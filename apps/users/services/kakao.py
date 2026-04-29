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

    AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"

    _GENDER_MAP = {"male": "M", "female": "F"}

    @classmethod
    def get_auth_url(cls) -> str:

        return (
            f"{cls.AUTH_URL}"
            f"?client_id={settings.KAKAO_CLIENT_ID}"
            f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
            "&response_type=code"
        )

    @classmethod
    def get_access_token(cls, code: str, redirect_uri: str) -> str:

        response = requests.post(
            cls.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_CLIENT_ID,
                "redirect_uri": redirect_uri,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise ValueError(f"카카오 토큰 발급 오류: {data.get('error_description', data['error'])}")

        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("카카오 응답에 access_token이 없습니다.")

        return str(access_token)

    @classmethod
    def get_user_info(cls, access_token: str) -> KakaoUserInfo:

        response = requests.get(
            cls.USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        account = data.get("kakao_account", {})
        profile = account.get("profile", {})

        birthyear = account.get("birthyear")
        birthday_mmdd = account.get("birthday")
        if birthyear and birthday_mmdd and len(birthday_mmdd) == 4:
            birthday = f"{birthyear}-{birthday_mmdd[:2]}-{birthday_mmdd[2:]}"
        else:
            birthday = None

        raw_gender = account.get("gender")
        gender = cls._GENDER_MAP.get(raw_gender) if raw_gender else None

        raw_phone = account.get("phone_number", "")
        phone_number = cls._normalize_phone(raw_phone) if raw_phone else None

        return KakaoUserInfo(
            provider_id=str(data["id"]),
            nickname=profile.get("nickname"),
            profile_img_url=profile.get("profile_image_url"),
            email=account.get("email"),
            name=account.get("name"),
            phone_number=phone_number,
            gender=gender,
            birthday=birthday,
        )

    @classmethod
    def get_user_info_by_code(cls, code: str, redirect_uri: str) -> KakaoUserInfo:

        access_token = cls.get_access_token(code, redirect_uri)
        return cls.get_user_info(access_token)

    @staticmethod
    def _normalize_phone(raw: str) -> str:

        phone = raw.rstrip()
        if phone.startswith("+82"):
            phone = "0" + phone[3:].strip()
        return phone.replace("-", "").replace(" ", "")
