from rest_framework import serializers

from apps.qna.models import Question


class InitialAIAnswerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    output = serializers.CharField()
    using_model = serializers.CharField()
    created_at = serializers.DateTimeField()
