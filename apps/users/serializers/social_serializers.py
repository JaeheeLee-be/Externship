from rest_framework import serializers

from apps.users.models import User


class SocialRegisterSerializer(serializers.ModelSerializer[User]):

    social_token = serializers.CharField(allow_blank=False)

    class Meta:
        model = User
        fields = ["social_token", "email", "name", "nickname", "phone_number", "birthday", "gender"]
