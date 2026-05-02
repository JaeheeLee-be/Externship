from django.test import TestCase

from apps.qna.chatbot.factories.payload import GroqFactory, Message, Payload


class TestMessage(TestCase):

    def test_corecct(self):
        msg = Message(role="test", content="test")
        self.assertEqual(msg.role, "test")
        self.assertEqual(msg.content, "test")

    def test_equality(self):
        self.assertEqual(
            Message(role="test", content="test"),
            Message(role="test", content="test"),
        )

    def test_inequality(self):
        self.assertNotEqual(
            Message(role="test1", content="test1"),
            Message(role="test2", content="test2"),
        )


class TestPayload(TestCase):
    def test_correct(self):
        messages = [Message(role="test", content="test")]
        payload = Payload(messages=messages, model="test_model", stream=True, temperature=0.1)
        self.assertEqual(payload.messages, messages)
        self.assertEqual(payload.model, "test_model")
        self.assertTrue(payload.stream)
        self.assertEqual(payload.temperature, 0.1)


class TestCreateFirstPayload(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.payload = GroqFactory.create_first_payload(
            prompt="test_prompt",
            category="test_category",
            title="test_title",
            message="test_message",
        )

    def test_correct(self):
        self.assertIsInstance(self.payload, Payload)
        self.assertIsInstance(self.payload.messages, list)
        self.assertEqual(self.payload.model, "openai/gpt-oss-120b")
        self.assertEqual(self.payload.stream, False)
        self.assertEqual(self.payload.temperature, 0.1)

    def test_messages(self):
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
    @classmethod
    def setUpTestData(cls):
        cls.payload = GroqFactory.create_payload(
            prompt="test_prompt",
            message="test_message",
        )

    def test_correct(self):
        self.assertIsInstance(self.payload, Payload)
        self.assertIsInstance(self.payload.messages, list)
        self.assertEqual(self.payload.model, "openai/gpt-oss-120b")
        self.assertEqual(self.payload.stream, True)
        self.assertEqual(self.payload.temperature, 0.1)

    def test_messages(self):
        self.assertEqual(len(self.payload.messages), 2)
        self.assertEqual(self.payload.messages[0], Message(role="system", content="test_prompt"))
        self.assertEqual(self.payload.messages[1].role, "user")
        self.assertEqual(self.payload.messages[1].content, "<client_question>test_message</client_question>")

    def test_messages_with_history(self):
        history = [
            Message(role="user", content="hello"),
            Message(role="assistant", content="world"),
        ]
        p = GroqFactory.create_payload(prompt="test_prompt2", message="test_message2", history=history)
        self.assertEqual(len(p.messages), 4)
        self.assertEqual(p.messages[1], history[0])
        self.assertEqual(p.messages[2], history[1])
        self.assertEqual(p.messages[3].role, "user")
        self.assertEqual(p.messages[3].content, "<client_question>test_message2</client_question>")
