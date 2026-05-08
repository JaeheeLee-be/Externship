from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    role: str
    content: str
    timestamp: str | None = None

    def api_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class GroqPayload:
    messages: list[Message]
    model: str
    stream: bool
    temperature: float

    def api(self) -> dict[str, Any]:
        return {
            "messages": [m.api_dict() for m in self.messages],
            "model": self.model,
            "stream": self.stream,
            "temperature": self.temperature,
        }


@dataclass
class InitialQNA:
    answer: str
    title: str
    category: str
    content: str
    question_id: int
    using_model: str
    created_at: str
