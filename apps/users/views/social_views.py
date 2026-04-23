# 소셜 로그인 뷰 (카카오 / 네이버)
# access 토큰 → Response Body
# refresh 토큰 → HttpOnly 쿠키

from __future__ import annotations

import secrets

import requests
from django.conf import settings
from django.http import HttpResponseBase, HttpResponseRedirect
from django.shortcuts import redirect
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.users.services.kakao import KakaoOAuthService
from apps.users.services.naver import NaverOAuthService
from apps.users.services.social_auth import SocialAuthService



# ────공통──────────────────────────────────────────────────────

def _set_refresh_cookie(response: HttpResponseBase, refresh_token: str) -> None:
    """refresh 토큰을 HttpOnly 쿠키에 설정"""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,        # JS에서 접근 불가
        secure=True,          # HTTPS에서만 전송
        samesite="Lax",
        max_age=60 * 60 * 24 * 7,  # 7일
    )


def _get_frontend_url(path: str) -> str:
    """프론트엔드 URL 생성"""
    base = getattr(settings, "FRONTEND_URL", "").rstrip("/")
    return f"{base}{path}"



# ────카카오──────────────────────────────────────────────────────

@extend_schema(tags=["소셜 로그인"])
class KakaoLoginView(APIView):
    """카카오 OAuth 인증 페이지로 302 리다이렉트"""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="카카오 소셜 로그인",
        responses={302: None},
    )
    def get(self, request: Request) -> HttpResponseRedirect:
        kakao_auth_url = (
            "https://kauth.kakao.com/oauth/authorize"
            f"?client_id={settings.KAKAO_CLIENT_ID}"
            f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
            "&response_type=code"
        )
        return redirect(kakao_auth_url)


@extend_schema(tags=["소셜 로그인"])
class KakaoCallbackView(APIView):
    """
    카카오 인가 코드 콜백 처리
    - 기존 유저 / 신규 유저 모두 바로 회원가입 후 JWT 발급
    - access(Body) + refresh(쿠키) + 프론트 리다이렉트
    - 오류 → 프론트 실패 페이지로 리다이렉트
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="카카오 소셜 로그인 콜백",
        parameters=[
            OpenApiParameter(name="code", description="카카오 인가 코드", required=True, type=str),
            OpenApiParameter(name="error", description="카카오 오류 코드 (실패 시)", required=False, type=str),
        ],
        responses={302: None},
    )
    def get(self, request: Request) -> HttpResponseRedirect:
        code = request.query_params.get("code")
        error = request.query_params.get("error")

        # 카카오에서 오류가 내려오거나 code가 없는 경우
        if error or not code:
            return redirect(_get_frontend_url("/social-login/fail"))

        try:
            # 카카오 유저 정보 조회
            user_info = KakaoOAuthService.get_user_info_by_code(code, settings.KAKAO_REDIRECT_URI or "")

            # 로그인 or 바로 회원가입
            result = SocialAuthService.login_or_register(
                provider="kakao",
                provider_id=user_info.provider_id,
                email=user_info.email,
                name=user_info.name,
                nickname=user_info.nickname,
                profile_img_url=user_info.profile_img_url,
                phone_number=user_info.phone_number,
                gender=user_info.gender,
                birthday=user_info.birthday,
            )

        except requests.RequestException:
            return redirect(_get_frontend_url("/social-login/fail"))

        # access → 헤더, refresh → HttpOnly 쿠키 후 리다이렉트
        response = redirect(_get_frontend_url("/social-login/success"))
        response["X-Access-Token"] = result["access"]
        _set_refresh_cookie(response, result["refresh"])
        return response


# ────네이버──────────────────────────────────────────────────────

@extend_schema(tags=["소셜 로그인"])
class NaverLoginView(APIView):
    """네이버 OAuth 인증 페이지로 302 리다이렉트 (state 포함)"""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="네이버 소셜 로그인",
        responses={302: None},
    )
    def get(self, request: Request) -> HttpResponseRedirect:
        state = secrets.token_urlsafe(16)  # CSRF 방지용 랜덤 문자열

        naver_auth_url = (
            "https://nid.naver.com/oauth2.0/authorize"
            f"?client_id={settings.NAVER_CLIENT_ID}"
            f"&redirect_uri={settings.NAVER_REDIRECT_URI}"
            "&response_type=code"
            f"&state={state}"
        )
        return redirect(naver_auth_url)


@extend_schema(tags=["소셜 로그인"])
class NaverCallbackView(APIView):
    """
    네이버 인가 코드 콜백 처리
    - 기존 유저 / 신규 유저 모두 바로 회원가입 후 JWT 발급
    - access(Body) + refresh(쿠키) + 프론트 리다이렉트
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="네이버 소셜 로그인 콜백",
        parameters=[
            OpenApiParameter(name="code", description="네이버 인가 코드", required=True, type=str),
            OpenApiParameter(name="state", description="CSRF 방지 state 값", required=True, type=str),
            OpenApiParameter(name="error", description="네이버 오류 코드 (실패 시)", required=False, type=str),
        ],
        responses={302: None},
    )
    def get(self, request: Request) -> HttpResponseRedirect:
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")

        # 오류 또는 필수값 누락
        if error or not code or not state:
            return redirect(_get_frontend_url("/social-login/fail"))

        try:
            # 네이버 유저 정보 조회
            user_info = NaverOAuthService.get_user_info_by_code(code, state)

            # 로그인 or 바로 회원가입
            result = SocialAuthService.login_or_register(
                provider = "naver",
                provider_id = user_info.provider_id,
                email = user_info.email,
                name = user_info.name,
                nickname = user_info.nickname,
                profile_img_url = user_info.profile_img_url,
                phone_number = user_info.phone_number,
                gender = user_info.gender,
                birthday = user_info.birthday,
            )

        except requests.RequestException:
            return redirect(_get_frontend_url("/social-login/fail"))

        # access → 헤더, refresh → HttpOnly 쿠키 후 리다이렉트
        response = redirect(_get_frontend_url("/social-login/success"))
        response["X-Access-Token"] = result["access"]
        _set_refresh_cookie(response, result["refresh"])
        return response
