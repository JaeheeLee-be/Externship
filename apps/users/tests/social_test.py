from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import SocialUsers, User
from apps.users.services.kakao import KakaoUserInfo
from apps.users.services.naver import NaverUserInfo
from apps.users.services.social_auth import SocialAuthService
from apps.users.utils.social_exceptions import (
    EmailAlreadyRegisteredError,
    EmailNotProvidedError,
    SocialAuthError,
    UnsupportedProviderError,
)

# ── 픽스처 헬퍼 ──────────────────────────────────────────────────────


def make_user(**kwargs: Any) -> User:
    """테스트용 User 생성 헬퍼 (unusable password)"""
    defaults: dict[str, Any] = {
        "email": "test@example.com",
        "name": "테스트유저",
        "nickname": "테스트닉",
        "phone_number": "01012345678",
    }
    defaults.update(kwargs)
    user = User(**defaults)
    user.set_unusable_password()
    user.save()
    return user


# ── 뷰 테스트 ─────────────────────────────────────────────────────────
# SocialAuthService를 mock하여 HTTP 요청/응답 동작만 검증한다.
# DB 데이터 없음 → setUpTestData 불필요, APIClient만 setUp에서 생성.


class SocialLoginViewTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    @patch("apps.users.views.social_views.SocialAuthService.get_auth_url")
    def test_kakao_redirects_to_auth_url(self, mock_get_auth_url: MagicMock) -> None:
        """카카오 로그인 요청 시 카카오 인증 페이지로 302 리다이렉트"""
        mock_get_auth_url.return_value = "https://kauth.kakao.com/oauth/authorize?client_id=test"

        response = self.client.get(reverse("users:social-login", kwargs={"provider": "kakao"}))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("kauth.kakao.com", response["Location"])
        mock_get_auth_url.assert_called_once_with("kakao")

    @patch("apps.users.views.social_views.SocialAuthService.get_auth_url")
    def test_naver_redirects_to_auth_url(self, mock_get_auth_url: MagicMock) -> None:
        """네이버 로그인 요청 시 네이버 인증 페이지로 302 리다이렉트"""
        mock_get_auth_url.return_value = "https://nid.naver.com/oauth2.0/authorize?client_id=test"

        response = self.client.get(reverse("users:social-login", kwargs={"provider": "naver"}))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("nid.naver.com", response["Location"])
        mock_get_auth_url.assert_called_once_with("naver")

    @patch("apps.users.views.social_views.SocialAuthService.get_auth_url")
    def test_invalid_provider_returns_400(self, mock_get_auth_url: MagicMock) -> None:
        """지원하지 않는 provider 요청 시 400 반환"""
        mock_get_auth_url.side_effect = UnsupportedProviderError()

        response: Any = self.client.get(reverse("users:social-login", kwargs={"provider": "google"}))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)


class SocialCallbackViewTest(TestCase):
    # URL은 불변값이므로 클래스당 1번만 계산
    kakao_url: str
    naver_url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.kakao_url = reverse("users:social-callback", kwargs={"provider": "kakao"})
        cls.naver_url = reverse("users:social-callback", kwargs={"provider": "naver"})

    def setUp(self) -> None:
        # APIClient는 상태(인증 헤더·쿠키)를 가지므로 테스트마다 새로 생성
        self.client = APIClient()

    def test_error_param_returns_400(self) -> None:
        """OAuth error 파라미터가 있을 때 400 반환"""
        response: Any = self.client.get(self.kakao_url, {"error": "access_denied"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "access_denied")

    def test_missing_code_returns_400(self) -> None:
        """code 없이 요청 시 400 반환"""
        response: Any = self.client.get(self.kakao_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_existing_user_returns_200_with_tokens(self, mock_process_user: MagicMock) -> None:
        """기존 소셜 유저 로그인 시 200 + JWT 반환"""
        mock_process_user.return_value = {
            "is_new_user": False,
            "access": "access_token_value",
            "refresh": "refresh_token_value",
        }

        response: Any = self.client.get(self.kakao_url, {"code": "valid_code"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_new_user"])
        self.assertEqual(response.data["access"], "access_token_value")

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_new_user_returns_200_with_is_new_user_true(self, mock_process_user: MagicMock) -> None:
        """신규 유저 회원가입 시 200 + is_new_user=True 반환"""
        mock_process_user.return_value = {
            "is_new_user": True,
            "access": "new_access_token",
            "refresh": "new_refresh_token",
        }

        response: Any = self.client.get(self.kakao_url, {"code": "valid_code"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_new_user"])
        self.assertEqual(response.data["access"], "new_access_token")

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_social_auth_error_returns_400(self, mock_process_user: MagicMock) -> None:
        """SocialAuthError 발생 시 400 + detail 반환"""
        mock_process_user.side_effect = EmailAlreadyRegisteredError()

        response: Any = self.client.get(self.kakao_url, {"code": "some_code"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "일반 이메일로 회원 가입한 유저 입니다")

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_unexpected_error_returns_500(self, mock_process_user: MagicMock) -> None:
        """예상치 못한 예외 발생 시 500 반환"""
        mock_process_user.side_effect = RuntimeError("DB 연결 실패")

        response: Any = self.client.get(self.kakao_url, {"code": "some_code"})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("detail", response.data)

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_refresh_token_cookie_is_set(self, mock_process_user: MagicMock) -> None:
        """성공 응답 시 refresh_token HttpOnly 쿠키가 설정된다"""
        mock_process_user.return_value = {
            "is_new_user": False,
            "access": "access_token_value",
            "refresh": "refresh_token_value",
        }

        response = self.client.get(self.kakao_url, {"code": "valid_code"})

        self.assertIn("refresh_token", response.cookies)
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_naver_callback_passes_state_param(self, mock_process_user: MagicMock) -> None:
        """네이버 콜백에서 state 파라미터가 service로 전달된다"""
        mock_process_user.return_value = {
            "is_new_user": False,
            "access": "naver_access",
            "refresh": "naver_refresh",
        }

        self.client.get(self.naver_url, {"code": "naver_code", "state": "some_state"})

        mock_process_user.assert_called_once_with(
            provider="naver",
            code="naver_code",
            state="some_state",
        )


# ── 서비스 테스트 ─────────────────────────────────────────────────────
# 외부 OAuth API(카카오/네이버)만 mock하고 DB 로직은 실제로 실행한다.
# 사전 DB 상태가 다른 케이스끼리 클래스를 분리하여 setUpTestData를 활용한다.


class SocialAuthServiceGetAuthUrlTest(TestCase):
    # DB 데이터 없음 → setUpTestData 불필요

    @patch("apps.users.services.social_auth.KakaoOAuthService.get_auth_url")
    def test_kakao_returns_auth_url(self, mock_kakao: MagicMock) -> None:
        """kakao provider → KakaoOAuthService.get_auth_url 호출"""
        mock_kakao.return_value = "https://kauth.kakao.com/oauth/authorize"

        url = SocialAuthService.get_auth_url("kakao")

        self.assertEqual(url, "https://kauth.kakao.com/oauth/authorize")
        mock_kakao.assert_called_once()

    @patch("apps.users.services.social_auth.NaverOAuthService.get_auth_url")
    def test_naver_returns_auth_url(self, mock_naver: MagicMock) -> None:
        """naver provider → NaverOAuthService.get_auth_url 호출"""
        mock_naver.return_value = "https://nid.naver.com/oauth2.0/authorize"

        url = SocialAuthService.get_auth_url("naver")

        self.assertEqual(url, "https://nid.naver.com/oauth2.0/authorize")
        mock_naver.assert_called_once()

    def test_invalid_provider_raises_social_auth_error(self) -> None:
        """지원하지 않는 provider → SocialAuthError 발생"""
        with self.assertRaises(UnsupportedProviderError):
            SocialAuthService.get_auth_url("google")


class ExistingSocialUserLoginTest(TestCase):
    """기존 소셜 유저 로그인 — User + SocialUsers + KakaoUserInfo를 클래스당 1번만 생성"""

    user: User
    social_user: SocialUsers
    kakao_info: KakaoUserInfo

    @classmethod
    def setUpTestData(cls) -> None:
        cls.kakao_info = KakaoUserInfo(
            provider_id="kakao_123",
            email="kakao@example.com",
            name="카카오유저",
            nickname="카카오닉네임",
            phone_number="01099999999",
            profile_img_url=None,
            gender="M",
            birthday="1990-01-01",
        )
        cls.user = make_user(
            email="kakao@example.com",
            nickname="기존유저닉",
            phone_number="01011111111",
        )
        cls.social_user = SocialUsers.objects.create(
            user=cls.user,
            provider="kakao",
            provider_id="kakao_123",
        )

    @patch("apps.users.services.social_auth.KakaoOAuthService.get_user_info_by_code")
    def test_existing_social_user_login(self, mock_get_user_info: MagicMock) -> None:
        """기존 소셜 유저 → is_new_user=False, 새 User 생성 없음"""
        mock_get_user_info.return_value = self.kakao_info

        result = SocialAuthService.process_user(provider="kakao", code="valid_code")

        self.assertFalse(result["is_new_user"])
        self.assertIn("access", result)
        self.assertIn("refresh", result)
        # setUpTestData에서 만든 1명만 존재해야 함 (새 유저 생성 없음)
        self.assertEqual(User.objects.count(), 1)


class EmailOnlyUserConflictTest(TestCase):
    """일반 이메일 가입 유저가 소셜 로그인 시도하는 케이스"""

    user: User
    kakao_info: KakaoUserInfo

    @classmethod
    def setUpTestData(cls) -> None:
        cls.kakao_info = KakaoUserInfo(
            provider_id="kakao_123",
            email="kakao@example.com",
            name="카카오유저",
            nickname="카카오닉네임",
            phone_number="01099999999",
            profile_img_url=None,
            gender="M",
            birthday="1990-01-01",
        )
        # SocialUsers 없이 User만 생성 (일반 이메일 가입 유저)
        cls.user = make_user(
            email="kakao@example.com",
            nickname="일반유저닉",
            phone_number="01022222222",
        )

    @patch("apps.users.services.social_auth.KakaoOAuthService.get_user_info_by_code")
    def test_email_only_user_raises_error(self, mock_get_user_info: MagicMock) -> None:
        """동일 이메일 일반 가입 유저 → SocialAuthError('일반 이메일로 회원 가입한 유저 입니다')"""
        mock_get_user_info.return_value = self.kakao_info

        with self.assertRaises(EmailAlreadyRegisteredError) as ctx:
            SocialAuthService.process_user(provider="kakao", code="valid_code")

        self.assertEqual(str(ctx.exception), "일반 이메일로 회원 가입한 유저 입니다")


class NewSocialUserRegistrationTest(TestCase):
    """신규 소셜 유저 회원가입 — 사전 DB 데이터 없음"""

    kakao_info: KakaoUserInfo
    kakao_info_no_email: KakaoUserInfo
    naver_info: NaverUserInfo

    @classmethod
    def setUpTestData(cls) -> None:
        cls.kakao_info = KakaoUserInfo(
            provider_id="kakao_123",
            email="kakao@example.com",
            name="카카오유저",
            nickname="카카오닉네임",
            phone_number="01099999999",
            profile_img_url=None,
            gender="M",
            birthday="1990-01-01",
        )
        cls.kakao_info_no_email = KakaoUserInfo(
            provider_id="kakao_123",
            email=None,
            name="카카오유저",
            nickname="카카오닉네임",
            phone_number="01099999999",
            profile_img_url=None,
            gender="M",
            birthday="1990-01-01",
        )
        cls.naver_info = NaverUserInfo(
            provider_id="naver_123",
            email="naver@example.com",
            name="네이버유저",
            nickname="네이버닉네임",
            profile_img_url=None,
            phone_number="01088888888",
            gender="F",
            birthday="1992-03-15",
        )

    @patch("apps.users.services.social_auth.KakaoOAuthService.get_user_info_by_code")
    def test_no_email_raises_error(self, mock_get_user_info: MagicMock) -> None:
        """이메일 없는 소셜 유저 → SocialAuthError('이메일 정보를 가져올 수 없습니다.')"""
        mock_get_user_info.return_value = self.kakao_info_no_email

        with self.assertRaises(EmailNotProvidedError) as ctx:
            SocialAuthService.process_user(provider="kakao", code="valid_code")

        self.assertEqual(str(ctx.exception), "이메일 정보를 가져올 수 없습니다.")

    @patch("apps.users.services.social_auth.KakaoOAuthService.get_user_info_by_code")
    def test_new_kakao_user_created_successfully(self, mock_get_user_info: MagicMock) -> None:
        """카카오 신규 유저 → User + SocialUsers 생성, is_new_user=True"""
        mock_get_user_info.return_value = self.kakao_info

        result = SocialAuthService.process_user(provider="kakao", code="valid_code")

        self.assertTrue(result["is_new_user"])
        self.assertIn("access", result)
        self.assertIn("refresh", result)

        created_user = User.objects.get(email="kakao@example.com")
        self.assertFalse
