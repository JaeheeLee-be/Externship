from typing import Any

from rest_framework import serializers
from rest_framework.fields import CharField

from apps.users.serializers.purpose_enum import SmsPurpose



class PhoneNumberBaseSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=20,
        error_messages={"required": "이 필드는 필수 항목입니다."},
    )

    def validate_phone_number(self, value):
        # '-'  제거
        clean_value = value.replace('-', '')
        if not clean_value.isdigit():
            raise serializers.ValidationError("전화번호는 숫자여야 합니다.")
        return clean_value


class SmsSendSerializer(PhoneNumberBaseSerializer):

    purpose = serializers.ChoiceField(
        choices=SmsPurpose.choices,
        error_messages={"required": "이 필드는 필수 항목입니다."},
    )

class SmsVerifySerializer(PhoneNumberBaseSerializer):
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        error_messages={"required": "이 필드는 필수 항목입니다."},
    )

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("인증코드는 숫자만 입력되어야 합니다")
        return value