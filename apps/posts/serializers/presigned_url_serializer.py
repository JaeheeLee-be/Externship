from rest_framework import serializers

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

class PresignUrlRequestSerializer(serializers.Serializer):
    file_name = serializers.CharField(required=True)

    def validate_file_name(self, value: str) -> str:
        ext = value.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError("지원하지 않는 파일 형식입니다.")

        return value