from typing import Any

from rest_framework import serializers

from apps.qna.dtos import Message


class InitialAIAnswerSerializer(serializers.Serializer[Any]):
    question_id = serializers.IntegerField()
    output = serializers.CharField(source="answer")
    using_model = serializers.CharField()
    created_at = serializers.CharField()


class QNAChatbotRequestSerializer(serializers.Serializer[Any]):
    message = serializers.CharField(min_length=1, max_length=1000, trim_whitespace=True)


ROLE = (
    ("user", "user"),
    ("assistant", "assistant"),
)


class QNAHistoryResponseSerializer(serializers.Serializer[Any]):
    role = serializers.ChoiceField(choices=ROLE)
    message = serializers.CharField(source="content")


class QNAChatbotListResponseSerializer(serializers.Serializer[Any]):
    question_id = serializers.IntegerField()
    last_message = serializers.CharField()
    role = serializers.ChoiceField(choices=ROLE)
    created_at = serializers.CharField()
