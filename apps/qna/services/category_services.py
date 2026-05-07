from django.db.models import QuerySet

from apps.qna.models.question_models import QuestionCategory


class CategoryService:
    @staticmethod
    def get_category_tree() -> QuerySet[QuestionCategory]:
        """대분류만 조회 후 children을 prefetch로 2depth 한 번에 로딩"""
        return QuestionCategory.objects.filter(parent__isnull=True).prefetch_related(
            "children",
            "children__children",
        )
