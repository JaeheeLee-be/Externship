from datetime import datetime

from .dtos import InitialQNA


class CacheFactory:
    @staticmethod
    def create_initial_cache(
        category: str,
        title: str,
        content: str,
        answer: str,
        question_id: int,
        using_model: str,
    ) -> InitialQNA:

        created_at = str(datetime.now())
        return InitialQNA(
            category=category,
            title=title,
            content=content,
            answer=answer,
            question_id=question_id,
            using_model=using_model,
            created_at=created_at,
        )
