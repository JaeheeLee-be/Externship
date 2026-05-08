from django.test import TestCase

from apps.qna.serializers.chatbot_serializers import InitialAIAnswerSerializer


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
