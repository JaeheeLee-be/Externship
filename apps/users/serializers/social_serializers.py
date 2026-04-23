"""
API 명세서를 보면 Request body가 없고, 302 리다이렉트 + HttpOnly 쿠키 방식이다.
"""

# 소셜 로그인 Serializer
# KakaoRegisterSerializer : 카카오 회원가입 완료 시 프론트가 POST로 보내는 데이터 검증

from typing import Any

from rest_framework import serializers


class KakaoRegisterSerializer(serializers.Serializer[Any]):
    """카카오 소셜 회원가입 완료 요청 검증"""

    social_token = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField()
    phone_number = serializers.CharField()
    birthday = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=["male", "female"],
        required=False,
        allow_null=True,
    )
