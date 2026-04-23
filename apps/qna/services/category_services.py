from apps.qna.models.question_models import QuestionCategory


class CategoryService:

    # 카테고리 생성
    @staticmethod
    def create_category(*, name: str, parent: QuestionCategory | None = None) -> QuestionCategory:
        return QuestionCategory.objects.create(
            name=name,
            parent=parent,
        )