from typing import Any

from rest_framework import serializers


class InitialAIAnswerSerializer(serializers.Serializer[Any]):
    question_id = serializers.IntegerField()
    output = serializers.CharField(source="answer")
    using_model = serializers.CharField()
    created_at = serializers.CharField()

class QNAChatbotRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, trim_whitespace=True)