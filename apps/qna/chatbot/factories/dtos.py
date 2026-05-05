from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Payload:
    messages: list[Message]
    model: str
    stream: bool
    temperature: float

@dataclass
class QNAStreamResponse:
    message: str
