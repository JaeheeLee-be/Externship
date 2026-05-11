from django.db.models import Count, OuterRef, QuerySet, Subquery

from apps.qna.models.question_models import Question, QuestionCategory, QuestionImage


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
