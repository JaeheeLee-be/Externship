from django.db import transaction
from django.db.models import Count, OuterRef, Prefetch, QuerySet, Subquery

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
            QuestionImage.objects.bulk_create([QuestionImage(question=question, img_url=url) for url in img_urls])

        return question


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
