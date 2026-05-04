from django.db import transaction
from django.db.models import Count, F, OuterRef, Prefetch, QuerySet, Subquery

from apps.qna.exceptions import NotFoundException
from apps.qna.models.answer_models import Answer, AnswerComment
from apps.qna.exceptions import NotFoundException, PermissionDeniedException
from apps.qna.models.question_models import Question, QuestionCategory, QuestionImage
from apps.users.models import CohortStudents, User


class QuestionService:

    @staticmethod
    @transaction.atomic
    def create_question(
        *,
        author: User,
        title: str,
        content: str,
        category: QuestionCategory,
        img_urls: list[str],
    ) -> Question:
        question = Question.objects.create(
            author=author,
            title=title,
            content=content,
            category=category,
        )

        if img_urls:
            QuestionImage.objects.bulk_create(
                [QuestionImage(question=question, img_url=url) for url in img_urls]
            )

        return question

    @staticmethod
    def update_question(
        *,
        question: Question,
        title: str,
        content: str,
        category: QuestionCategory,
        img_urls: list[str],
    ) -> Question:
        """질문 수정"""
        question.title = title
        question.content = content
        question.category = category
        question.save(update_fields=["title", "content", "category", "updated_at"])

        # 기존 이미지 삭제 후 새로 추가
        question.questionimage_set.all().delete()
        if img_urls:
            QuestionImage.objects.bulk_create(
                [QuestionImage(question=question, img_url=url) for url in img_urls]
            )

        return question

    @staticmethod
    def update_question_by_user(
        *,
        user: User,
        question_id: int,
        title: str,
        content: str,
        category_id: int,
        img_urls: list[str],
    ) -> Question:
        """사용자가 질문 수정 (권한 체크 포함)"""
        # 질문 조회
        try:
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            raise NotFoundException("해당 질문을 찾을 수 없습니다.")

        # 권한 확인 (본인만 수정 가능)
        if question.author_id != user.id:
            raise PermissionDeniedException("본인이 작성한 질문만 수정할 수 있습니다.")

        # 카테고리 조회
        try:
            category = QuestionCategory.objects.get(id=category_id)
        except QuestionCategory.DoesNotExist:
            raise NotFoundException("존재하지 않는 카테고리입니다.")

        # 질문 수정
        return QuestionService.update_question(
            question=question,
            title=title,
            content=content,
            category=category,
            img_urls=img_urls,
        )

def _get_category_info(category: QuestionCategory) -> dict[str, object]:
    """카테고리 대/중/소 name 리스트와 depth 반환"""
    chain: list[str] = []
    current: QuestionCategory | None = category
    while current is not None:
        chain.append(current.name)
        current = current.parent

    names = list(reversed(chain))  # 대 → 중 → 소 순서

    return {
        "id": category.id,
        "depth": len(names),  # 대=0, 중=1, 소=2
        "names": names,
    }


class QuestionListService:

    @staticmethod
    def get_question_list(
        *,
        page: int,
        page_size: int,
        search_keyword: str | None = None,
        category_id: int | None = None,
        answer_status: str | None = None,
        sort: str = "latest",
    ) -> tuple[QuerySet[Question], int]:

        # 첫 번째 이미지 서브쿼리
        first_image_subquery = Subquery(
            QuestionImage.objects.filter(question=OuterRef("pk")).order_by("id").values("img_url")[:1]
        )

        qs = (
            Question.objects.select_related(
                "category__parent__parent",
                "author",
            )
            .prefetch_related(
                Prefetch(
                    "author__cohort_students",
                    queryset=CohortStudents.objects.select_related("cohort__course"),
                )
            )
            .annotate(
                answer_count=Count("answer", distinct=True),
                thumbnail_img_url=first_image_subquery,
            )
        )

        # 검색 필터
        if search_keyword:
            qs = qs.filter(title__icontains=search_keyword)

        # 카테고리 필터 (상위 카테고리 선택 시 하위 카테고리 포함)
        if category_id:
            category_ids = QuestionListService._get_descendant_category_ids(category_id)
            qs = qs.filter(category_id__in=category_ids)

        # 답변 상태 필터
        if answer_status == "answered":
            qs = qs.filter(answer_count__gt=0)
        elif answer_status == "unanswered":
            qs = qs.filter(answer_count=0)

        # 정렬
        order_map = {
            "latest": "-created_at",
            "oldest": "created_at",
            "views": "-view_count",
        }
        qs = qs.order_by(order_map.get(sort, "-created_at"))

        total_count = qs.count()
        offset = (page - 1) * page_size
        questions = qs[offset : offset + page_size]

        return questions, total_count

    @staticmethod
    def _get_descendant_category_ids(category_id: int) -> list[int]:
        """선택된 카테고리 + 모든 하위 카테고리 id 반환 (쿼리 1번)"""
        # 전체 카테고리를 한 번에 가져와서 메모리에서 트리 탐색
        all_categories = QuestionCategory.objects.values_list("id", "parent_id")

        ids = {category_id}
        changed = True
        while changed:
            changed = False
            for cat_id, parent_id in all_categories:
                if parent_id in ids and cat_id not in ids:
                    ids.add(cat_id)
                    changed = True

        return list(ids)

    @staticmethod
    def build_result(question: Question) -> dict[str, object]:
        author = question.author
        category = question.category

        # course_name, cohort_number 조회 (prefetch된 데이터 사용)
        cohort_student = author.cohort_students.first() if hasattr(author, "cohort_students") else None
        course_name = cohort_student.cohort.course.name if cohort_student and cohort_student.cohort else None
        cohort_number = cohort_student.cohort.number if cohort_student and cohort_student.cohort else None

        return {
            "id": question.id,
            "category": _get_category_info(category),
            "author": {
                "id": author.id,
                "nickname": author.nickname,
                "profile_img_url": getattr(author, "profile_img_url", None),
                "course_name": course_name,
                "cohort_number": cohort_number,
            },
            "title": question.title,
            "content_preview": question.content[:100],
            "answer_count": question.answer_count,  # type: ignore[attr-defined]
            "view_count": question.view_count,
            "created_at": question.created_at,
            "thumbnail_img_url": question.thumbnail_img_url,  # type: ignore[attr-defined]
        }


class QuestionDetailService:
    """질문 상세 조회 서비스"""

    @staticmethod
    def get_question_detail(question_id: int) -> dict[str, object]:
        """질문 상세 조회 및 조회수 증가"""
        try:
            from apps.users.models import CohortStudents

            # 댓글 prefetch
            answer_comments_prefetch = Prefetch(
                "answercomment_set",
                queryset=AnswerComment.objects.select_related("author").prefetch_related(
                    Prefetch(
                        "author__cohort_students",
                        queryset=CohortStudents.objects.select_related("cohort__course"),
                    )
                ),
            )

            question = (
                Question.objects.select_related(
                    "author",
                    "category__parent__parent",
                )
                .prefetch_related(
                    "questionimage_set",
                    Prefetch(
                        "answer_set",
                        queryset=Answer.objects.select_related("author")
                        .prefetch_related(answer_comments_prefetch)
                        .order_by("-is_adopted", "created_at"),
                    ),
                )
                .get(pk=question_id)
            )
        except Question.DoesNotExist:
            raise NotFoundException("해당 질문을 찾을 수 없습니다.")

        # 조회수 증가
        Question.objects.filter(pk=question_id).update(view_count=F("view_count") + 1)
        question.refresh_from_db()

        # 응답 데이터 구성
        return QuestionDetailService._build_response(question)

    @staticmethod
    def _build_response(question: Question) -> dict[str, object]:
        """질문 상세 응답 데이터 구성"""
        author = question.author
        category = question.category

        # 이미지 목록
        images = [{"id": img.id, "img_url": img.img_url} for img in question.questionimage_set.all()]

        # 답변 목록
        answers = []
        for answer in question.answer_set.all():
            answer_author = answer.author

            # 댓글 목록
            comments = []
            for comment in answer.answercomment_set.all():
                comment_author = comment.author

                # course_name, cohort_number 조회 (prefetch된 데이터 사용)
                cohort_student = comment_author.cohort_students.first()
                course_name = cohort_student.cohort.course.name if cohort_student and cohort_student.cohort else None
                cohort_number = cohort_student.cohort.number if cohort_student and cohort_student.cohort else None

                comments.append(
                    {
                        "id": comment.id,
                        "content": comment.content,
                        "created_at": comment.created_at,
                        "author": {
                            "id": comment_author.id,
                            "nickname": comment_author.nickname,
                            "profile_img_url": getattr(comment_author, "profile_img_url", None),
                            "course_name": course_name,
                            "cohort_number": cohort_number,
                        },
                    }
                )

            answers.append(
                {
                    "id": answer.id,
                    "content": answer.content,
                    "created_at": answer.created_at,
                    "is_adopted": answer.is_adopted,
                    "author": {
                        "id": answer_author.id,
                        "nickname": answer_author.nickname,
                        "profile_img_url": getattr(answer_author, "profile_img_url", None),
                    },
                    "comments": comments,
                }
            )

        return {
            "id": question.id,
            "title": question.title,
            "content": question.content,
            "category": _get_category_info(category),
            "images": images,
            "view_count": question.view_count,
            "created_at": question.created_at,
            "author": {
                "id": author.id,
                "nickname": author.nickname,
                "profile_img_url": getattr(author, "profile_img_url", None),
            },
            "answers": answers,
        }
