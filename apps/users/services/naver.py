from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings


@dataclass
class NaverUserInfo:
    provider_id: str
    email: Optional[str]
    name: Optional[str]
    nickname: Optional[str]
    profile_img_url: Optional[str]
    phone_number: Optional[str]
    gender: Optional[str]
    birthday: Optional[str]  # YYYY-MM-DD 형식


class NaverOAuthService:

    AUTH_URL = "https://nid.naver.com/oauth2.0/authorize"
    TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
    USER_INFO_URL = "https://openapi.naver.com/v1/nid/me"

    @classmethod
    def get_auth_url(cls, state: str | None = None) -> str:

        return (
            f"{cls.AUTH_URL}"
            f"?client_id={settings.NAVER_CLIENT_ID}"
            f"&redirect_uri={settings.NAVER_REDIRECT_URI}"
            "&response_type=code"
            f"&state={state}"
        )

    @classmethod
    def get_access_token(cls, code: str, state: str) -> str:

        response = requests.post(
            cls.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.NAVER_CLIENT_ID,
                "client_secret": settings.NAVER_CLIENT_SECRET,
                "redirect_uri": settings.NAVER_REDIRECT_URI,
                "code": code,
                "state": state,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise ValueError(f"네이버 토큰 발급 오루: {data.get('error_description', data['error'])}")

        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("네이버 응답에 access_token이 없습니다.")

        return str(access_token)

    @classmethod
    def get_user_info(cls, access_token: str) -> NaverUserInfo:
        response = requests.get(
            cls.USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        user_data = data.get("response", {})

        raw_phone = user_data.get("mobile", "")
        phone_number = raw_phone.replace("-", "") if raw_phone else None

        gender = user_data.get("gender") or None

        birthyear = user_data.get("birthyear", "")
        birthday_mmdd = user_data.get("birthday", "")
        if birthyear and birthday_mmdd:
            birthday = f"{birthyear}-{birthday_mmdd}"
        else:
            birthday = None

        return NaverUserInfo(
            provider_id=str(user_data["id"]),
            email=user_data.get("email"),
            name=user_data.get("name"),
            nickname=user_data.get("nickname"),
            profile_img_url=user_data.get("profile_image"),
            phone_number=phone_number,
            gender=gender,
            birthday=birthday,
        )

    @classmethod
    def get_user_info_by_code(cls, code: str, state: str) -> NaverUserInfo:

        access_token = cls.get_access_token(code, state)
        return cls.get_user_info(access_token)
