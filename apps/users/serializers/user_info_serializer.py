from rest_framework import serializers

from apps.users.models import User


class UserInfoSerializer(serializers.ModelSerializer[User]):
    # 수강생인 경우 보여줄 추가 필드
    cohort_id = serializers.SerializerMethodField()

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

    def get_cohort_id(self, obj: User) -> int | None:
        cohort_student = obj.cohort_students.first()
        # 유저 레코드가 없는 경우 or 레코드는 있는데 cohort FK가 NULL인 경우
        if cohort_student is None or cohort_student.cohort is None:
            return None
        return cohort_student.cohort.id


# class UserInfoUpdateSerializer(serializers.ModelSerializer[User]):
#     cohort_id = serializers.IntegerField(
#         source="cohort_students.first.cohort.id",
#         read_only=True,
#         allow_null=True,
#     )
#
#     class Meta:
#         model = User
#         fields = [
#             "id",
#             "email",
#             "nickname",
#             "name",
#             "phone_number",
#             "birthday",
#             "gender",
#             "profile_img_url",
#             "cohort_id",
#             "created_at",
#         ]
#         read_only_fields = fields
