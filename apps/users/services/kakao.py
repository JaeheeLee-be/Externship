# 카카오 API 통신
# 받아올 수 있는 항목: provider_id, nickname, profile_img_url, email, name, phone_number, gender, birthday


from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings


@dataclass
class KakaoUserInfo:
    provider_id: str
    nickname: Optional[str]
    profile_img_url: Optional[str]
    email: Optional[str]
    name: Optional[str]
    phone_number: Optional[str]
    gender: Optional[str]
    birthday: Optional[str]  # YYYY-MM-DD 형식


class KakaoOAuthService:
    """카카오 OAuth 2.0 서비스"""

    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"

    @classmethod
    def get_access_token(cls, code: str, redirect_uri: str) -> str:
        """인가 코드로 카카오 액세스 토큰 발급"""
        response = requests.post(
            cls.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_CLIENT_ID,
                "redirect_uri": redirect_uri or settings.KAKAO_REDIRECT_URI,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return str(data["access_token"])

    @classmethod
    def get_user_info(cls, access_token: str) -> KakaoUserInfo:
        """카카오 액세스 토큰으로 사용자 정보 조회"""
        response = requests.get(
            cls.USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        account = data.get("kakao_account", {})
        profile = account.get("profile", {})

        # birthyear(YYYY) + birthday(MMDD) → YYYY-MM-DD
        birthyear = account.get("birthyear")
        birthday_mmdd = account.get("birthday")
        if birthyear and birthday_mmdd:
            birthday = f"{birthyear}-{birthday_mmdd[:2]}-{birthday_mmdd[2:]}"
        else:
            birthday = None

        return KakaoUserInfo(
            provider_id=str(data["id"]),
            nickname=profile.get("nickname"),
            profile_img_url=profile.get("profile_image_url"),
            email=account.get("email"),
            name=account.get("name"),
            phone_number=account.get("phone_number"),
            gender=account.get("gender"),
            birthday=birthday,
        )

    @classmethod
    def get_user_info_by_code(cls, code: str, redirect_uri: str) -> KakaoUserInfo:
        """인가 코드로 사용자 정보 조회"""
        access_token = cls.get_access_token(code, redirect_uri)
        return cls.get_user_info(access_token)