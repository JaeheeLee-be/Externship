from .dtos import Message, Payload


class GroqFactory:
    @staticmethod
    def create_initial_payload(
        prompt: str,
        category: str,
        title: str,
        message: str,
        model: str = "openai/gpt-oss-120b",
        stream: bool = False,
        temperature: float = 0.1,
    ) -> Payload:
        """
        챗봇 초기응답용 페이로드 생성 함수입니다.
        XML 태그로 클라이언트의 질문과 그 외 텍스트를 구분합니다.
        <title>과 <message> 태그는 클라이언트의 질문으로 취급됩니다.
        <client_question> 태그는 프롬프트 인젝션 방지 및 관련 없는 주제를 필터링하는 데 활용됩니다.
        """

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
        """
        챗봇 채팅창용 페이로드 생성 함수입니다.
        초기응답을 포함한 대화 히스토리를 포함하며,
        XML 태그로 클라이언트의 질문과 그 외 텍스트를 구분합니다.
        <client_question> 태그는 프롬프트 인젝션 방지 및 관련 없는 주제를 필터링하는 데 활용됩니다.
        """

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
