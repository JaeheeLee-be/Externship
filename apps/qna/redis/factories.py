from datetime import datetime
from typing import Any

from apps.qna.dtos import InitialQNA, LastQNAHistory


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

        created_at = datetime.now().isoformat()
        return InitialQNA(
            category=category,
            title=title,
            content=content,
            answer=answer,
            question_id=question_id,
            using_model=using_model,
            created_at=created_at,
        )

    @staticmethod
    def create_last_qna(key: str, value: Any) -> LastQNAHistory:
        return LastQNAHistory(
            question_id=int(key.split(":")[-1]),
            last_message=value[-1]["content"],
            role=value[-1]["role"],
            created_at=value[-1]["created_at"],
        )
