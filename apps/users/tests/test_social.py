from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import SocialUsers, User
from apps.users.services.kakao import KakaoOAuthService, KakaoUserInfo
from apps.users.services.naver import NaverOAuthService, NaverUserInfo
from apps.users.services.social_auth import SocialAuthService
from apps.users.utils.social_exceptions import (
    EmailAlreadyRegisteredError,
    EmailNotProvidedError,
    InternalServerError,
    MissingAuthCodeError,
    OAuthCallbackError,
    SocialAuthError,
    UnsupportedProviderError,
)

# ── 헬퍼 ──────────────────────────────────────────────────────────────────────


def make_user(**kwargs: Any) -> User:
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


def _parse_redirect(response: Any) -> dict[str, str]:
    """302 응답의 Location 헤더에서 쿼리 파라미터를 파싱해 반환"""
    location = response["Location"]
    qs = parse_qs(urlparse(location).query)
    return {k: v[0] for k, v in qs.items()}


# ── social_exceptions: __init__ 커버 ──────────────────────────────────────────


class SocialExceptionsInitTest(TestCase):
    """각 예외의 __init__ 를 직접 실행해 미커버 라인 해소"""

    def test_unsupported_provider_error(self) -> None:
        e = UnsupportedProviderError()
        self.assertIn("지원하지 않는", str(e))

    def test_oauth_callback_error(self) -> None:
        e = OAuthCallbackError("access_denied")
        self.assertEqual(str(e), "access_denied")

    def test_missing_auth_code_error(self) -> None:
        e = MissingAuthCodeError()
        self.assertIn("인가 코드", str(e))

    def test_email_not_provided_error(self) -> None:
        e = EmailNotProvidedError()
        self.assertIn("이메일", str(e))

    def test_email_already_registered_error(self) -> None:
        e = EmailAlreadyRegisteredError()
        self.assertIn("일반 이메일", str(e))

    def test_internal_server_error(self) -> None:
        e = InternalServerError()
        self.assertIn("서버 오류", str(e))


# ── social_views.py: 302 리다이렉트 기준으로 재작성 ──────────────────────────


@override_settings(FRONTEND_REDIRECT_URI="http://localhost:3000")
class SocialCallbackViewRedirectTest(TestCase):
    """
    현재 SocialCallbackView.get 동작 기준 (302 리다이렉트)
    기존 test_social.py 의 SocialCallbackViewTest 를 이 클래스로 교체해야 함.
    """

    kakao_url: str
    naver_url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.kakao_url = reverse("users:social-callback", kwargs={"provider": "kakao"})
        cls.naver_url = reverse("users:social-callback", kwargs={"provider": "naver"})

    def setUp(self) -> None:
        self.client = APIClient()

    # ── 실패 케이스 ──

    def test_error_param_redirects_with_is_success_false(self) -> None:
        """OAuth error 파라미터 → 302 + is_success=false"""
        response = self.client.get(self.kakao_url, {"error": "access_denied"})

        self.assertEqual(response.status_code, 302)
        params = _parse_redirect(response)
        self.assertEqual(params["is_success"], "false")
        self.assertEqual(params["provider"], "kakao")

    def test_missing_code_redirects_with_is_success_false(self) -> None:
        """code 없이 요청 → 302 + is_success=false"""
        response = self.client.get(self.kakao_url)

        self.assertEqual(response.status_code, 302)
        params = _parse_redirect(response)
        self.assertEqual(params["is_success"], "false")

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_social_auth_error_redirects_with_is_success_false(self, mock_process: MagicMock) -> None:
        """SocialAuthError 발생 → 302 + is_success=false"""
        mock_process.side_effect = EmailAlreadyRegisteredError()

        response = self.client.get(self.kakao_url, {"code": "some_code"})

        self.assertEqual(response.status_code, 302)
        params = _parse_redirect(response)
        self.assertEqual(params["is_success"], "false")
        self.assertEqual(params["provider"], "kakao")

    # ── 성공 케이스 ──

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_existing_user_redirects_with_is_success_true(self, mock_process: MagicMock) -> None:
        """기존 유저 → 302 + is_success=true + is_new_user=false"""
        mock_process.return_value = {
            "is_new_user": False,
            "access": "access_token_value",
            "refresh": "refresh_token_value",
        }

        response = self.client.get(self.kakao_url, {"code": "valid_code"})

        self.assertEqual(response.status_code, 302)
        params = _parse_redirect(response)
        self.assertEqual(params["is_success"], "true")
        self.assertEqual(params["is_new_user"], "false")
        self.assertEqual(params["provider"], "kakao")

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_new_user_redirects_with_is_new_user_true(self, mock_process: MagicMock) -> None:
        """신규 유저 → 302 + is_success=true + is_new_user=true"""
        mock_process.return_value = {
            "is_new_user": True,
            "access": "new_access",
            "refresh": "new_refresh",
        }

        response = self.client.get(self.kakao_url, {"code": "valid_code"})

        self.assertEqual(response.status_code, 302)
        params = _parse_redirect(response)
        self.assertEqual(params["is_success"], "true")
        self.assertEqual(params["is_new_user"], "true")

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_refresh_token_cookie_set_on_success(self, mock_process: MagicMock) -> None:
        """성공 시 refresh_token HttpOnly 쿠키 설정"""
        mock_process.return_value = {
            "is_new_user": False,
            "access": "access_token_value",
            "refresh": "refresh_token_value",
        }

        response = self.client.get(self.kakao_url, {"code": "valid_code"})

        self.assertIn("refresh_token", response.cookies)
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_naver_callback_passes_state_param(self, mock_process: MagicMock) -> None:
        """네이버 콜백 - state 파라미터가 service로 전달된다"""
        mock_process.return_value = {
            "is_new_user": False,
            "access": "naver_access",
            "refresh": "naver_refresh",
        }

        self.client.get(self.naver_url, {"code": "naver_code", "state": "some_state"})

        mock_process.assert_called_once_with(
            provider="naver",
            code="naver_code",
            state="some_state",
            error=None,
        )

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_redirect_url_points_to_frontend(self, mock_process: MagicMock) -> None:
        """리다이렉트 URL이 FRONTEND_REDIRECT_URI 기준으로 생성된다"""
        mock_process.return_value = {
            "is_new_user": False,
            "access": "access",
            "refresh": "refresh",
        }

        response = self.client.get(self.kakao_url, {"code": "valid_code"})

        self.assertIn("localhost:3000", response["Location"])
        self.assertIn("/social-callback", response["Location"])


# ── social_auth.py: 미커버 라인 보완 ─────────────────────────────────────────


class SocialAuthServiceProcessUserEdgeCasesTest(TestCase):
    """process_user 의 error / missing code 분기 (lines 60-63)"""

    def test_error_param_raises_oauth_callback_error(self) -> None:
        with self.assertRaises(OAuthCallbackError):
            SocialAuthService.process_user(provider="kakao", code="some_code", error="access_denied")

    def test_missing_code_raises_missing_auth_code_error(self) -> None:
        with self.assertRaises(MissingAuthCodeError):
            SocialAuthService.process_user(provider="kakao", code="")


class SocialAuthServiceGetUserInfoNaverTest(TestCase):
    """_get_user_info naver 분기 (lines 85-90)"""

    @patch("apps.users.services.social_auth.NaverOAuthService.get_user_info_by_code")
    def test_naver_calls_naver_service(self, mock_naver: MagicMock) -> None:
        mock_naver.return_value = NaverUserInfo(
            provider_id="naver_1",
            email="naver@example.com",
            name="네이버",
            nickname="닉",
            profile_img_url=None,
            phone_number="01011112222",
            gender="M",
            birthday="1990-01-01",
        )
        # process_user 까지 실행하면 _login_and_register 도 같이 커버
        result = SocialAuthService.process_user(provider="naver", code="code", state="state")
        self.assertTrue(result["is_new_user"])
        mock_naver.assert_called_once_with("code", "state")

    def test_unsupported_provider_in_get_user_info_raises(self) -> None:
        with self.assertRaises(UnsupportedProviderError):
            SocialAuthService._get_user_info("google", "code")


class SocialAuthServiceLoginAndRegisterTest(TestCase):
    """_login_and_register 의 모든 분기 커버"""

    kakao_info: KakaoUserInfo

    @classmethod
    def setUpTestData(cls) -> None:
        cls.kakao_info = KakaoUserInfo(
            provider_id="kakao_999",
            email="kakao_cover@example.com",
            name="커버유저",
            nickname="커버닉",
            phone_number="01033334444",
            profile_img_url=None,
            gender="M",
            birthday="1991-05-05",
        )

    @patch("apps.users.services.social_auth.KakaoOAuthService.get_user_info_by_code")
    def test_existing_social_user_returns_is_new_user_false(self, mock_info: MagicMock) -> None:
        """기존 SocialUsers → is_new_user=False (lines 103-110)"""
        mock_info.return_value = self.kakao_info
        user = make_user(email="kakao_cover@example.com", nickname="기존닉", phone_number="01055556666")
        SocialUsers.objects.create(user=user, provider="kakao", provider_id="kakao_999")

        result = SocialAuthService.process_user(provider="kakao", code="code")

        self.assertFalse(result["is_new_user"])
        self.assertIn("refresh", result)

    @patch("apps.users.services.social_auth.KakaoOAuthService.get_user_info_by_code")
    def test_new_user_created_and_social_user_linked(self, mock_info: MagicMock) -> None:
        """신규 유저 → User + SocialUsers 생성, is_new_user=True (lines 123-147)"""
        mock_info.return_value = self.kakao_info

        result = SocialAuthService.process_user(provider="kakao", code="code")

        self.assertTrue(result["is_new_user"])
        self.assertTrue(User.objects.filter(email="kakao_cover@example.com").exists())
        self.assertTrue(SocialUsers.objects.filter(provider="kakao", provider_id="kakao_999").exists())


# ── kakao.py: 미커버 라인 보완 ────────────────────────────────────────────────


class KakaoOAuthServiceTest(TestCase):

    @override_settings(KAKAO_CLIENT_ID="test_client_id", KAKAO_REDIRECT_URI="http://localhost/callback")
    def test_get_auth_url_contains_client_id(self) -> None:
        """get_auth_url (line 38)"""
        url = KakaoOAuthService.get_auth_url()
        self.assertIn("test_client_id", url)
        self.assertIn("kauth.kakao.com", url)

    @patch("apps.users.services.kakao.requests.post")
    def test_get_access_token_success(self, mock_post: MagicMock) -> None:
        """get_access_token 정상 (lines 48-69)"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "kakao_access_123"}
        mock_post.return_value = mock_resp

        token = KakaoOAuthService.get_access_token("code", "http://localhost/cb")

        self.assertEqual(token, "kakao_access_123")

    @patch("apps.users.services.kakao.requests.post")
    def test_get_access_token_missing_token_raises(self, mock_post: MagicMock) -> None:
        """access_token 없는 응답 → ValueError"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_post.return_value = mock_resp

        with self.assertRaises(ValueError):
            KakaoOAuthService.get_access_token("code", "http://localhost/cb")

    @patch("apps.users.services.kakao.requests.post")
    def test_get_access_token_error_in_response_raises(self, mock_post: MagicMock) -> None:
        """응답에 error 필드 → ValueError"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": "invalid_grant", "error_description": "bad code"}
        mock_post.return_value = mock_resp

        with self.assertRaises(ValueError):
            KakaoOAuthService.get_access_token("code", "http://localhost/cb")

    @patch("apps.users.services.kakao.requests.get")
    def test_get_user_info_parses_response(self, mock_get: MagicMock) -> None:
        """get_user_info 전체 파싱 (lines 74-100)"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "id": 12345,
            "kakao_account": {
                "email": "kakao@test.com",
                "name": "카카오",
                "phone_number": "+82 10-1234-5678",
                "gender": "male",
                "birthyear": "1990",
                "birthday": "0505",
                "profile": {
                    "nickname": "카카오닉",
                    "profile_image_url": "https://img.kakao.com/profile.jpg",
                },
            },
        }
        mock_get.return_value = mock_resp

        info = KakaoOAuthService.get_user_info("some_token")

        self.assertEqual(info.provider_id, "12345")
        self.assertEqual(info.email, "kakao@test.com")
        self.assertEqual(info.gender, "M")
        self.assertEqual(info.birthday, "1990-05-05")
        self.assertEqual(info.phone_number, "01012345678")

    def test_normalize_phone_with_plus82(self) -> None:
        """전화번호 정규화 (lines 120-123)"""
        result = KakaoOAuthService._normalize_phone("+82 10-1234-5678")
        self.assertEqual(result, "01012345678")

    def test_normalize_phone_without_plus82(self) -> None:
        result = KakaoOAuthService._normalize_phone("010-1234-5678")
        self.assertEqual(result, "01012345678")


# ── naver.py: 미커버 라인 보완 ────────────────────────────────────────────────


class NaverOAuthServiceTest(TestCase):

    @override_settings(NAVER_CLIENT_ID="naver_id", NAVER_REDIRECT_URI="http://localhost/naver")
    def test_get_auth_url_contains_client_id(self) -> None:
        """get_auth_url (line 35)"""
        url = NaverOAuthService.get_auth_url(state="random_state")
        self.assertIn("naver_id", url)
        self.assertIn("nid.naver.com", url)

    @patch("apps.users.services.naver.requests.post")
    def test_get_access_token_success(self, mock_post: MagicMock) -> None:
        """get_access_token 정상 (lines 46-69)"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "naver_access_999"}
        mock_post.return_value = mock_resp

        token = NaverOAuthService.get_access_token("code", "state")

        self.assertEqual(token, "naver_access_999")

    @patch("apps.users.services.naver.requests.post")
    def test_get_access_token_missing_token_raises(self, mock_post: MagicMock) -> None:
        """access_token 없는 응답 → ValueError"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_post.return_value = mock_resp

        with self.assertRaises(ValueError):
            NaverOAuthService.get_access_token("code", "state")

    @patch("apps.users.services.naver.requests.post")
    def test_get_access_token_error_in_response_raises(self, mock_post: MagicMock) -> None:
        """응답에 error 필드 → ValueError"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": "invalid_grant"}
        mock_post.return_value = mock_resp

        with self.assertRaises(ValueError):
            NaverOAuthService.get_access_token("code", "state")

    @patch("apps.users.services.naver.requests.get")
    def test_get_user_info_parses_response(self, mock_get: MagicMock) -> None:
        """get_user_info 전체 파싱 (lines 73-97)"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "response": {
                "id": "naver_abc",
                "email": "naver@test.com",
                "name": "네이버",
                "nickname": "네이버닉",
                "profile_image": "https://img.naver.com/profile.jpg",
                "mobile": "010-9876-5432",
                "gender": "F",
                "birthyear": "1995",
                "birthday": "07-20",
            }
        }
        mock_get.return_value = mock_resp

        info = NaverOAuthService.get_user_info("some_token")

        self.assertEqual(info.provider_id, "naver_abc")
        self.assertEqual(info.email, "naver@test.com")
        self.assertEqual(info.gender, "F")
        self.assertEqual(info.birthday, "1995-07-20")
        self.assertEqual(info.phone_number, "01098765432")

    @patch("apps.users.services.naver.requests.get")
    def test_get_user_info_missing_optional_fields(self, mock_get: MagicMock) -> None:
        """선택 필드 없는 응답도 정상 처리"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "response": {
                "id": "naver_xyz",
                "email": "min@test.com",
                "name": "최소유저",
                "nickname": "닉",
            }
        }
        mock_get.return_value = mock_resp

        info = NaverOAuthService.get_user_info("token")

        self.assertIsNone(info.phone_number)
        self.assertIsNone(info.birthday)
