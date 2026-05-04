from rest_framework import serializers


class InitialAIAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    output = serializers.CharField(source="answer")
    using_model = serializers.CharField()
    created_at = serializers.CharField()
