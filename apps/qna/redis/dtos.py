from dataclasses import dataclass


@dataclass
class InitialQNA:
    answer: str
    title: str
    category: str
    content: str
    question_id: int
    using_model: str
    created_at: str
