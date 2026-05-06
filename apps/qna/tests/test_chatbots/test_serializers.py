from django.test import TestCase

from apps.qna.serializers.chatbot_serializers import InitialAIAnswerSerializer, QNAChatbotRequestSerializer, \
    MessageSerializer, QNAChatbotResponseSerializer


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


class TestMessageSerializer(TestCase):
    def test_content_mapped_to_message(self) -> None:
        data = {"role": "user", "content": "hello"}
        serializer = MessageSerializer(data)
        self.assertEqual(serializer.data["role"], "user")
        self.assertEqual(serializer.data["message"], "hello")
        self.assertNotIn("content", serializer.data)


class TestQNAChatbotResponseSerializer(TestCase):
    def test_results_serialized(self) -> None:
        data = {"results": [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]}
        serializer = QNAChatbotResponseSerializer(data)
        self.assertEqual(len(serializer.data["results"]), 2)
        self.assertEqual(serializer.data["results"][0]["message"], "hello")