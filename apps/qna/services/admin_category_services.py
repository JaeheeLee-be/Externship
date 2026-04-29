from django.db.models import QuerySet

from apps.qna.models.question_models import QuestionCategory


class CategoryService:

    # 카테고리 생성
    @staticmethod
    def create_category(*, name: str, parent: QuestionCategory | None = None) -> QuestionCategory:
        return QuestionCategory.objects.create(
            name=name,
            parent=parent,
        )

    # 카테고리 조회
    @staticmethod
    def get_category_list(
        *,
        page: int,
        page_size: int,
        search_keyword: str | None = None,
        category_type: str | None = None,
    ) -> tuple[QuerySet[QuestionCategory], int]:
        qs = QuestionCategory.objects.select_related("parent__parent").prefetch_related("children")

        if search_keyword:
            qs = qs.filter(name__icontains=search_keyword)

        if category_type == "large":
            qs = qs.filter(parent__isnull=True)
        elif category_type == "middle":
            qs = qs.filter(parent__isnull=False, parent__parent__isnull=True)
        elif category_type == "small":
            qs = qs.filter(parent__parent__isnull=False)

        total_count = qs.count()
        offset = (page - 1) * page_size
        categories = qs.order_by("id")[offset : offset + page_size]

        return categories, total_count
