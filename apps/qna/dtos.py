from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str
    timestamp: str | None = None


@dataclass
class GroqPayload:
    messages: list[Message]
    model: str
    stream: bool
    temperature: float


@dataclass
class InitialQNA:
    answer: str
    title: str
    category: str
    content: str
    question_id: int
    using_model: str
    created_at: str
