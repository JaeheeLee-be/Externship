from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str
    timestamp: str | None = None


@dataclass
class Payload:
    messages: list[Message]
    model: str
    stream: bool
    temperature: float
