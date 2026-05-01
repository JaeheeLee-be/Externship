from rest_framework import serializers

from apps.qna.models import Question


# 질문글 -> 챗봇
class QNABotFirstRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["category", "title", "content"]
        read_only_fields = ["category", "title", "content"]


# 챗봇 채팅방: 유저 -> 챗봇
class QNABotRequestSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=True, max_length=500)


# 질문글, 챗봇 채팅방: 챗봇 -> 유저
class QNABotResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()


# 챗봇 채팅방: 질의응답 한 쌍 -> redis
class QNABotHistoryPairSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=True, max_length=500)
    answer = serializers.CharField()


# redis -> 챗봇
class QNABotAllHistorySerializer(serializers.Serializer):
    history = QNABotHistoryPairSerializer(many=True)
