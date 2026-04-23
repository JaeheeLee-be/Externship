from apps.qna.models.question_models import QuestionCategories


class CategoryService:

    # 카테고리 생성
    @staticmethod
    def create_category(*, name: str, parent: QuestionCategories | None = None) -> QuestionCategories:
        return QuestionCategories.objects.create(
            name=name,
            parent=parent,
        )