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


class GroqFactory:
    @staticmethod
    def create_first_payload(
        prompt: str,
        category: str,
        title: str,
        message: str,
        model: str = "openai/gpt-oss-120b",
        stream: bool = False,
        temperature: float = 0.1,
    ) -> Payload:

        messages = [
            Message(role="system", content=prompt),
            Message(
                role="user",
                content=f"""
                <category>{category}</category>
                <client_question>
                    <title>{title}</title>
                    <message>{message}</message>
                </client_question>
            """,
            ),
        ]

        return Payload(
            messages=messages,
            model=model,
            stream=stream,
            temperature=temperature,
        )

    @staticmethod
    def create_payload(
        prompt: str,
        message: str,
        history: list[Message] | None = None,
        model: str = "openai/gpt-oss-120b",
        stream: bool = True,
        temperature: float = 0.1,
    ) -> Payload:

        messages = [
            Message(role="system", content=prompt),
            *(history or []),
            Message(
                role="user",
                content=f"<client_question>{message}</client_question>",
            ),
        ]

        return Payload(
            messages=messages,
            model=model,
            stream=stream,
            temperature=temperature,
        )
