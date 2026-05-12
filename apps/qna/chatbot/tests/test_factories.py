from django.test import TestCase

from apps.qna.chatbot import GroqPayloadFactory
from apps.qna.dtos import GroqPayload, InitialQNA, Message


class TestMessage(TestCase):

    def test_correct(self) -> None:
        msg = Message(role="test", content="test")
        self.assertEqual(msg.role, "test")
        self.assertEqual(msg.content, "test")

    def test_equality(self) -> None:
        self.assertEqual(
            Message(role="test", content="test"),
            Message(role="test", content="test"),
        )

    def test_inequality(self) -> None:
        self.assertNotEqual(
            Message(role="test1", content="test1"),
            Message(role="test2", content="test2"),
        )


class TestPayload(TestCase):
    def test_correct(self) -> None:
        messages = [Message(role="test", content="test")]
        payload = GroqPayload(messages=messages, model="test_model", stream=True, temperature=0.1)
        self.assertEqual(payload.messages, messages)
        self.assertEqual(payload.model, "test_model")
        self.assertTrue(payload.stream)
        self.assertEqual(payload.temperature, 0.1)


class TestCreateInitialPayload(TestCase):
    payload: GroqPayload

    @classmethod
    def setUpTestData(cls) -> None:
        cls.payload = GroqPayloadFactory.create_initial_payload(
            prompt="test_prompt",
            category="test_category",
            title="test_title",
            message="test_message",
        )

    def test_correct(self) -> None:
        self.assertIsInstance(self.payload, GroqPayload)
        self.assertIsInstance(self.payload.messages, list)
        self.assertEqual(self.payload.model, "openai/gpt-oss-120b")
        self.assertEqual(self.payload.stream, False)
        self.assertEqual(self.payload.temperature, 0.1)

    def test_messages(self) -> None:
        self.assertEqual(len(self.payload.messages), 2)
        self.assertEqual(self.payload.messages[0], Message(role="system", content="test_prompt"))
        self.assertEqual(self.payload.messages[1].role, "user")
        self.assertEqual(
            self.payload.messages[1].content,
            """
                <category>test_category</category>
                <client_question>
                    <title>test_title</title>
                    <message>test_message</message>
                </client_question>
            """,
        )


class TestCreatePayload(TestCase):
    payload: GroqPayload

    @classmethod
    def setUpTestData(cls) -> None:
        cls.payload = GroqPayloadFactory.create_payload(
            prompt="test_prompt",
            message="test_message",
        )

    def test_correct(self) -> None:
        self.assertIsInstance(self.payload, GroqPayload)
        self.assertIsInstance(self.payload.messages, list)
        self.assertEqual(self.payload.model, "openai/gpt-oss-120b")
        self.assertEqual(self.payload.stream, True)
        self.assertEqual(self.payload.temperature, 0.1)

    def test_messages(self) -> None:
        self.assertEqual(len(self.payload.messages), 2)
        self.assertEqual(self.payload.messages[0], Message(role="system", content="test_prompt"))
        self.assertEqual(self.payload.messages[1].role, "user")
        self.assertEqual(self.payload.messages[1].content, "<client_question>test_message</client_question>")

    def test_messages_with_history(self) -> None:
        history = [
            Message(role="user", content="hello"),
            Message(role="assistant", content="world"),
        ]
        p = GroqPayloadFactory.create_payload(prompt="test_prompt2", message="test_message2", history=history)
        self.assertEqual(len(p.messages), 4)
        self.assertEqual(p.messages[1], history[0])
        self.assertEqual(p.messages[2], history[1])
        self.assertEqual(p.messages[3].role, "user")
        self.assertEqual(p.messages[3].content, "<client_question>test_message2</client_question>")


class TestBuildHistoryForQnaPayload(TestCase):

    def setUp(self) -> None:
        self.initial = InitialQNA(
            category="test",
            title="test",
            content="test",
            answer="test",
            question_id=1,
            using_model="test",
            created_at="test",
        )

    def test_returns_only_initial_history_when_history_is_none(self) -> None:
        result = GroqPayloadFactory.build_history_for_qna_payload(self.initial, None)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].role, "user")
        self.assertEqual(result[1].role, "assistant")
        self.assertEqual(result[1].content, self.initial.answer)

    def test_appends_history_after_initial_history(self) -> None:
        history = [
            Message(role="user", content="추가 질문입니다."),
            Message(role="assistant", content="추가 답변입니다."),
        ]

        result = GroqPayloadFactory.build_history_for_qna_payload(self.initial, history)

        self.assertEqual(len(result), 4)
        self.assertEqual(result[2].content, "추가 질문입니다.")
        self.assertEqual(result[3].content, "추가 답변입니다.")
