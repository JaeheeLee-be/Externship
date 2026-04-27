from rest_framework import serializers



class AdminAnswerDeleteSerializer(serializers.Serializer):
    """
    DELETE api/v1/admin/qna/answers/{answer_id}
    admin 답변 삭제 API 응답 serializer
    """
    answer_id = serializers.IntegerField()
    deleted_comment_count = serializers.IntegerField()
