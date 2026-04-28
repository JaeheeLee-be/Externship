from rest_framework import serializers

from apps.users.models import User


class UserInfoSerializer(serializers.ModelSerializer[User]):
    # 수강생인 경우 보여줄 추가 필드
    cohort_id = serializers.IntegerField(
        source="cohort_students.first.cohort.id",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "profile_img_url",
            "cohort_id",
            "created_at",
        ]
        read_only_fields = fields
