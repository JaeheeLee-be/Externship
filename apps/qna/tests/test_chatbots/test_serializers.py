from django.test import TestCase

from apps.qna.dtos import LastQNAHistory, Message
from apps.qna.serializers.chatbot_serializers import (
    InitialAIAnswerSerializer,
    QNAChatbotListResponseSerializer,
    QNAChatbotRequestSerializer,
    QNAHistoryResponseSerializer,
)


class TestInitialAIAnswerSerializer(TestCase):
    def test_output_field_maps_from_answer(self) -> None:
        data = {
            "question_id": 1,
            "answer": "answer",
            "using_model": "model",
            "created_at": "2026-05-04",
        }
        serializer = InitialAIAnswerSerializer(data)
        self.assertEqual(serializer.data["question_id"], data["question_id"])
        self.assertEqual(serializer.data["output"], "answer")
        self.assertEqual(serializer.data["using_model"], data["using_model"])
        self.assertEqual(serializer.data["created_at"], data["created_at"])
        self.assertNotIn("answer", serializer.data)


class TestQNAChatbotRequestSerializer(TestCase):
    def test_valid_message(self) -> None:
        serializer = QNAChatbotRequestSerializer(data={"message": "hello"})
        self.assertTrue(serializer.is_valid())

    def test_empty_message_is_invalid(self) -> None:
        serializer = QNAChatbotRequestSerializer(data={"message": ""})
        self.assertFalse(serializer.is_valid())

    def test_message_over_max_length_is_invalid(self) -> None:
        serializer = QNAChatbotRequestSerializer(data={"message": "a" * 1001})
        self.assertFalse(serializer.is_valid())

    def test_whitespace_only_message_is_invalid(self) -> None:
        serializer = QNAChatbotRequestSerializer(data={"message": "   "})
        self.assertFalse(serializer.is_valid())

    def test_message_is_trimmed(self) -> None:
        serializer = QNAChatbotRequestSerializer(data={"message": "  hello  "})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["message"], "hello")


class TestQNAHistoryResponseSerializer(TestCase):

    def test_serializes_user_message(self) -> None:
        message = Message(role="user", content="질문입니다.")
        serializer = QNAHistoryResponseSerializer(message)
        self.assertEqual(serializer.data["role"], "user")
        self.assertEqual(serializer.data["message"], "질문입니다.")

    def test_serializes_assistant_message(self) -> None:
        message = Message(role="assistant", content="답변입니다.")
        serializer = QNAHistoryResponseSerializer(message)
        self.assertEqual(serializer.data["role"], "assistant")
        self.assertEqual(serializer.data["message"], "답변입니다.")

    def test_serializes_list_of_messages(self) -> None:
        messages = [
            Message(role="user", content="질문입니다."),
            Message(role="assistant", content="답변입니다."),
        ]
        serializer = QNAHistoryResponseSerializer(messages, many=True)
        self.assertEqual(len(serializer.data), 2)
        self.assertEqual(serializer.data[0]["role"], "user")
        self.assertEqual(serializer.data[1]["role"], "assistant")

    def test_invalid_role_raises_error(self) -> None:
        data = {"role": "admin", "content": "질문입니다."}
        serializer = QNAHistoryResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("role", serializer.errors)


class TestQNAChatbotListResponseSerializer(TestCase):
    def setUp(self) -> None:
        self.instance = LastQNAHistory(
            question_id=1,
            last_message="test",
            role="assistant",
            created_at="2026-05-07T14:30:05",
        )

    def test_serializer(self) -> None:
        serializer = QNAChatbotListResponseSerializer(self.instance)
        self.assertEqual(serializer.data["question_id"], 1)
        self.assertEqual(serializer.data["last_message"], "test")
        self.assertEqual(serializer.data["role"], "assistant")
        self.assertIn("created_at", serializer.data)

    def test_many_serialized(self) -> None:
        instances = [
            self.instance,
            LastQNAHistory(question_id=2, last_message="test", role="assistant", created_at="2026-04-23T14:30:06"),
        ]
        serializer = QNAChatbotListResponseSerializer(instances, many=True)
        self.assertEqual(len(serializer.data), 2)
        self.assertEqual(serializer.data[0]["question_id"], 1)
        self.assertEqual(serializer.data[1]["question_id"], 2)
