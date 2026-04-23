from rest_framework import serializers

from apps.users.models import User


class SocialRegisterSerializer(serializers.ModelSerializer[User]):
    """
    소셜 회원가입 완료 요청 검증 (카카오 / 네이버 공통)
    """

    social_token = serializers.CharField(allow_blank=False)

    class Meta:
        model = User
        fields = ["social_token", "email", "name", "nickname", "phone_number", "birthday", "gender"]
