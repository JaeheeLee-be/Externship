from django.db.models import Count, OuterRef, QuerySet, Subquery, Prefetch

from apps.qna.exceptions import NotFoundException
from apps.qna.models import Answer
from apps.qna.models.question_models import Question, QuestionCategory
from apps.users.models import CohortStudents


def _get_category_path(category: QuestionCategory) -> str:
    """카테고리 대/중/소를 ' > ' 로 연결한 문자열 반환"""
    chain: list[str] = []
    current: QuestionCategory | None = category
    while current is not None:
        chain.append(current.name)
        current = current.parent
    return " > ".join(reversed(chain))


class AdminQuestionListService:

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

        qs = Question.objects.select_related(
            "category__parent__parent",
            "author",
        ).annotate(
            answer_count=Count("answer", distinct=True),
        )

        if search_keyword:
            qs = qs.filter(title__icontains=search_keyword)

        if category_id:
            category_ids = AdminQuestionListService._get_descendant_category_ids(category_id)
            qs = qs.filter(category_id__in=category_ids)

        if answer_status == "Y":
            qs = qs.filter(answer_count__gt=0)
        elif answer_status == "N":
            qs = qs.filter(answer_count=0)

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
        all_categories = QuestionCategory.objects.values_list("id", "parent_id")
        ids: set[int] = {category_id}
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
        category = question.category
        author = question.author

        return {
            "question_id": question.id,
            "title": question.title,
            "category_path": _get_category_path(category),
            "content_preview": question.content[:100],
            "nickname": author.nickname,
            "view_count": question.view_count,
            "has_answer": question.answer_count > 0,  # type: ignore[attr-defined]
            "created_at": question.created_at,
            "updated_at": question.updated_at,
        }


class AdminQuestionDeleteService:
    """어드민 질문 삭제 서비스"""

    @staticmethod
    def delete_admin_question(question_id: int) -> dict[str, object]:
        """어드민 질문 삭제 (답변, 댓글 포함)"""
        try:
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            raise NotFoundException("삭제할 질문을 찾을 수 없습니다.")

        # 삭제 전 카운트 계산
        deleted_answer_count = 0
        deleted_comment_count = 0

        # 각 답변의 댓글 수 계산 및 합산
        for answer in question.answer_set.all():
            deleted_comment_count += answer.answercomment_set.count()
            deleted_answer_count += 1

        # 질문 삭제 (cascade로 답변, 댓글, 이미지 모두 삭제됨)
        question.delete()

        return {
            "question_id": question_id,
            "deleted_answer_count": deleted_answer_count,
            "deleted_comment_count": deleted_comment_count,
        }

class AdminQuestionDetailService:
    """어드민 질문 상세 조회 서비스"""

    @staticmethod
    def get_admin_question_detail(question_id: int) -> dict[str, object]:
        """어드민 질문 상세 조회"""
        try:
            # cohort_students prefetch (User 모델용)
            cohort_students_prefetch = Prefetch(
                "cohort_students",
                queryset=CohortStudents.objects.select_related("cohort__course"),
            )

            # 질문 작성자의 cohort_students prefetch
            author_prefetch = Prefetch(
                "author",
                queryset=User.objects.prefetch_related(cohort_students_prefetch),
            )

            # 답변 prefetch
            answers_prefetch = Prefetch(
                "answer_set",
                queryset=Answer.objects.select_related("author")
                .prefetch_related(
                    Prefetch(
                        "author__cohort_students",
                        queryset=CohortStudents.objects.select_related("cohort__course"),
                    )
                )
                .order_by("-is_adopted", "created_at"),
            )

            # has_answer 계산 (답변 존재 여부)
            has_answer_subquery = Answer.objects.filter(question=OuterRef("pk"))

            question = (
                Question.objects.prefetch_related(
                    "questionimage_set",
                    author_prefetch,
                    answers_prefetch,
                )
                .annotate(has_answer=Exists(has_answer_subquery))
                .get(pk=question_id)
            )
        except Question.DoesNotExist:
            raise NotFoundException("해당 질문을 찾을 수 없습니다.")

        # 응답 데이터 구성
        return AdminQuestionDetailService._build_response(question)

    @staticmethod
    def _build_response(question: Question) -> dict[str, object]:
        """어드민 질문 상세 응답 데이터 구성"""
        author = question.author

        # 이미지 URL만 리스트로
        images = [img.img_url for img in question.questionimage_set.all()]

        # 작성자 course_generation
        cohort_student = author.cohort_students.first() if hasattr(author, "cohort_students") else None
        author_course_generation = None
        if cohort_student and cohort_student.cohort:
            course_name = cohort_student.cohort.course.name
            cohort_number = cohort_student.cohort.number
            author_course_generation = f"{course_name} {cohort_number}기" if course_name and cohort_number else None

        # 답변 목록
        answers = []
        for answer in question.answer_set.all():
            answer_author = answer.author

            # 답변 작성자 정보
            answer_cohort_student = (
                answer_author.cohort_students.first() if hasattr(answer_author, "cohort_students") else None
            )

            answer_course_generation = None
            answer_role_title = None

            if answer_cohort_student and answer_cohort_student.cohort:
                course_name = answer_cohort_student.cohort.course.name
                cohort_number = answer_cohort_student.cohort.number
                answer_course_generation = f"{course_name} {cohort_number}기" if course_name and cohort_number else None

                # role_title 결정 (예시 로직 - 실제로는 User 모델의 role 기반)
                # TODO: role에 따라 role_title 설정 로직 필요
                if answer_author.role == "ADMIN":
                    answer_role_title = f"{course_name} {cohort_number}기 관리자"
                # 추가 role에 따른 title 설정 가능

            answers.append(
                {
                    "answer_id": answer.id,
                    "author": {
                        "profile_img_url": getattr(answer_author, "profile_img_url", None),
                        "nickname": answer_author.nickname,
                        "role_title": answer_role_title,
                        "course_generation": answer_course_generation,
                    },
                    "content": answer.content,
                    "is_adopted": answer.is_adopted,
                    "created_at": answer.created_at,
                    "updated_at": answer.updated_at,
                }
            )

        return {
            "question_id": question.id,
            "title": question.title,
            "content": question.content,
            "images": images,
            "author": {
                "profile_img_url": getattr(author, "profile_img_url", None),
                "nickname": author.nickname,
                "course_generation": author_course_generation,
            },
            "view_count": question.view_count,
            "has_answer": question.has_answer,  # type: ignore[attr-defined]
            "created_at": question.created_at,
            "updated_at": question.updated_at,
            "answers": answers,
        }