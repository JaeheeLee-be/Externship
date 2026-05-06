from django.db import transaction
from django.db.models import QuerySet

from apps.qna.exceptions import (
    CategoryNotFoundException,
    DefaultCategoryDeleteException,
)
from apps.qna.models.question_models import Question, QuestionCategory
from apps.qna.serializers.category_serializers import get_category_type

DEFAULT_CATEGORY_NAME = "일반질문"


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

    # 카테고리 삭제
    @staticmethod
    @transaction.atomic
    def delete_category(*, category_id: int) -> dict[str, object]:

        # 1) 삭제 대상 카테고리 조회
        try:
            target = QuestionCategory.objects.select_related("parent__parent").get(id=category_id)
        except QuestionCategory.DoesNotExist:
            raise CategoryNotFoundException()

        # 2) 기본 카테고리 보호
        if target.name == DEFAULT_CATEGORY_NAME and target.parent_id is None:
            raise DefaultCategoryDeleteException()

        category_type = get_category_type(target)

        # 3) 삭제할 카테고리 ID 수집 (target + 모든 하위)
        ids_to_delete: set[int] = {target.id}
        ids_to_delete |= CategoryService._collect_descendant_ids(target)

        # 4) "일반질문" 카테고리 조회 또는 생성
        default_category, _ = QuestionCategory.objects.get_or_create(
            name=DEFAULT_CATEGORY_NAME,
            parent=None,
        )

        # 5) 이관: 삭제 대상 카테고리에 속한 질문 → 일반질문으로 변경
        migrated_count = Question.objects.filter(category_id__in=ids_to_delete).update(category=default_category)

        # 6) 카테고리 삭제 (하위부터 역순으로 삭제해 FK 제약 위반 방지)
        QuestionCategory.objects.filter(id__in=ids_to_delete).delete()

        return {
            "category_id": category_id,
            "category_type": category_type,
            "migrated_question_count": migrated_count,
        }

    @staticmethod
    def _collect_descendant_ids(category: QuestionCategory) -> set[int]:
        descendant_ids: set[int] = set()
        current_parent_ids = {category.id}

        while current_parent_ids:
            children_ids = set(
                QuestionCategory.objects.filter(parent_id__in=current_parent_ids).values_list("id", flat=True)
            )
            descendant_ids |= children_ids
            current_parent_ids = children_ids

        return descendant_ids
