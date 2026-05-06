from typing import Any

from rest_framework import serializers

from apps.qna.chatbot import Message


class InitialAIAnswerSerializer(serializers.Serializer[Any]):
    question_id = serializers.IntegerField()
    output = serializers.CharField(source="answer")
    using_model = serializers.CharField()
    created_at = serializers.CharField()


class QNAChatbotRequestSerializer(serializers.Serializer[str]):
    message = serializers.CharField(min_length=1, max_length=1000, trim_whitespace=True)


class MessageSerializer(serializers.Serializer[dict[str, str]]):
    role = serializers.CharField()
    message = serializers.CharField(source="content")


class QNAChatbotResponseSerializer(serializers.Serializer[dict[str, list[Message]]]):
    results = MessageSerializer(many=True)
