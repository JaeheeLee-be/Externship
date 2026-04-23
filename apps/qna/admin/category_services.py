from apps.qna.models.question_models import QuestionCategory


class AdminCategoryService:

    # 카테고리 댑스
    @staticmethod
    def get_category_depth(category: QuestionCategory) -> int:
        depth = 1
        current = category.parent
        while current:
            depth += 1
            current = current.parent
        return depth

    #댑스 타입으로 변환
    @staticmethod
    def get_category_type(category: QuestionCategory) -> str | None:
        mapping = {
            1: "large",
            2: "middle",
            3: "small",
        }
        return mapping.get(AdminCategoryService.get_category_depth(category))

    #리스트 조회
    @staticmethod
    def get_category_list(
        *,
        category_type: str | None = None,
        keyword: str | None = None,
    ) -> list[QuestionCategory]:
        queryset = (
            QuestionCategory._default_manager
            .select_related("parent")
            .prefetch_related("children")
            .order_by("id")
        )

        categories = list(queryset)

        if category_type:
            categories = [
                category
                for category in categories
                if AdminCategoryService.get_category_type(category) == category_type
            ]

        if keyword:
            normalized_keyword = keyword.strip().lower()
            categories = [
                category
                for category in categories
                if normalized_keyword in category.name.lower()
            ]

        return categories