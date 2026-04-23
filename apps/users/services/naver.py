# 네이버 API 통신
# 필수 항목 : 이메일, 닉네임, 이름, 휴대폰 번호, 생년월일, 성별, 프로필 사진

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
    """네이버 OAuth 2.0 서비스"""

    TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
    USER_INFO_URL = "https://openapi.naver.com/v1/nid/me"

    @classmethod
    def get_access_token(cls, code: str, state: str) -> str:
        """인가 코드로 네이버 액세스 토큰 발급"""
        response = requests.post(
            cls.TOKEN_URL,
            params={
                "grant_type": "authorization_code",
                "client_id": settings.NAVER_CLIENT_ID,
                "client_secret": settings.NAVER_CLIENT_SECRET,
                "redirect_uri": settings.NAVER_REDIRECT_URI,
                "code": code,
                "state": state,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return str(data["access_token"])

    @classmethod
    def get_user_info(cls, access_token: str) -> NaverUserInfo:
        """네이버 액세스 토큰으로 사용자 정보 조회"""
        response = requests.get(
            cls.USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        user_data = data.get("response", {})

        # 전화번호 : "010-1234-5678" → "01012345678"로 변환
        raw_phone = user_data.get("mobile", "")
        phone_number = raw_phone.replace("-", "") if raw_phone else None

        # 성별 : "M" → "male" / "F" → "female" 로 변환
        gender_map = {"M": "male", "F": "female"}
        gender = gender_map.get(user_data.get("gender", ""))

        # 생년월일 : birthyear="2000", birthday="12-31" → "2000-12-31"
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
        """인가 코드로 네이버 사용자 정보 조회"""
        access_token = cls.get_access_token(code, state)
        return cls.get_user_info(access_token)

