from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
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
    UnsupportedProviderError,
)


def _qs(response: Any) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlparse(response["Location"]).query).items()}


# ── 예외 ──────────────────────────────────────────────────────────────────────


class SocialExceptionsTest(TestCase):
    def test_unsupported_provider_error(self) -> None:
        self.assertIn("지원하지 않는", str(UnsupportedProviderError()))

    def test_oauth_callback_error(self) -> None:
        self.assertEqual(str(OAuthCallbackError("access_denied")), "access_denied")

    def test_missing_auth_code_error(self) -> None:
        self.assertIn("인가 코드", str(MissingAuthCodeError()))

    def test_email_not_provided_error(self) -> None:
        self.assertIn("이메일", str(EmailNotProvidedError()))

    def test_email_already_registered_error(self) -> None:
        self.assertIn("일반 이메일", str(EmailAlreadyRegisteredError()))

    def test_internal_server_error(self) -> None:
        self.assertIn("서버 오류", str(InternalServerError()))


# ── SocialCallbackView ────────────────────────────────────────────────────────


@override_settings(FRONTEND_REDIRECT_URI="http://localhost:3000")
class SocialCallbackViewTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.kakao_url = reverse("users:social-callback", kwargs={"provider": "kakao"})
        self.naver_url = reverse("users:social-callback", kwargs={"provider": "naver"})
        self.success_result = {"is_new_user": False, "access": "acc", "refresh": "ref"}

    def test_error_param_redirects_with_is_success_false(self) -> None:
        response = self.client.get(self.kakao_url, {"error": "access_denied"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(_qs(response)["is_success"], "false")

    def test_missing_code_redirects_with_is_success_false(self) -> None:
        response = self.client.get(self.kakao_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(_qs(response)["is_success"], "false")

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_social_auth_error_redirects_with_is_success_false(self, mock: MagicMock) -> None:
        mock.side_effect = EmailAlreadyRegisteredError()
        response = self.client.get(self.kakao_url, {"code": "some_code"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(_qs(response)["is_success"], "false")

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_unexpected_exception_redirects_with_server_error(self, mock: MagicMock) -> None:
        mock.side_effect = RuntimeError("DB 연결 실패")
        response = self.client.get(self.kakao_url, {"code": "some_code"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(_qs(response)["is_success"], "false")
        self.assertEqual(_qs(response)["error"], "server_error")

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_existing_user_redirects_with_is_new_user_false(self, mock: MagicMock) -> None:
        mock.return_value = self.success_result
        response = self.client.get(self.kakao_url, {"code": "valid_code"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(_qs(response)["is_success"], "true")
        self.assertEqual(_qs(response)["is_new_user"], "false")

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_new_user_redirects_with_is_new_user_true(self, mock: MagicMock) -> None:
        mock.return_value = {**self.success_result, "is_new_user": True}
        response = self.client.get(self.kakao_url, {"code": "valid_code"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(_qs(response)["is_new_user"], "true")

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_refresh_token_cookie_set_on_success(self, mock: MagicMock) -> None:
        mock.return_value = self.success_result
        response = self.client.get(self.kakao_url, {"code": "valid_code"})
        self.assertIn("refresh_token", response.cookies)
        self.assertTrue(response.cookies["refresh_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["secure"])  # secure 주석처리됨

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_naver_callback_passes_state_param(self, mock: MagicMock) -> None:
        mock.return_value = self.success_result
        self.client.get(self.naver_url, {"code": "naver_code", "state": "some_state"})
        mock.assert_called_once_with(provider="naver", code="naver_code", state="some_state", error=None)

    @patch("apps.users.views.social_views.SocialAuthService.process_user")
    def test_redirect_url_points_to_frontend(self, mock: MagicMock) -> None:
        mock.return_value = self.success_result
        response = self.client.get(self.kakao_url, {"code": "valid_code"})
        self.assertIn("localhost:3000/social-callback", response["Location"])


class SocialAuthServiceTest(TestCase):
    def test_error_param_raises_oauth_callback_error(self) -> None:
        with self.assertRaises(OAuthCallbackError):
            SocialAuthService.process_user(provider="kakao", code="code", error="access_denied")

    def test_missing_code_raises_missing_auth_code_error(self) -> None:
        with self.assertRaises(MissingAuthCodeError):
            SocialAuthService.process_user(provider="kakao", code="")

    def test_unsupported_provider_raises_error(self) -> None:
        with self.assertRaises(UnsupportedProviderError):
            SocialAuthService._get_user_info("google", "code")

    @patch("apps.users.services.social_auth.cache")
    @patch("apps.users.services.social_auth.NaverOAuthService.get_user_info_by_code")
    def test_naver_calls_naver_service(self, mock: MagicMock, mock_cache: MagicMock) -> None:
        mock_cache.get.return_value = "naver"
        mock.return_value = NaverUserInfo(
            provider_id="naver_1",
            email="naver@example.com",
            name="네이버",
            nickname="닉",
            profile_img_url=None,
            phone_number="01011112222",
            gender="M",
            birthday="1990-01-01",
        )
        result = SocialAuthService.process_user(provider="naver", code="code", state="state")
        self.assertTrue(result["is_new_user"])
        mock.assert_called_once_with("code", "state")


class ExistingSocialUserTest(TestCase):
    user: User
    social_user: SocialUsers
    kakao_info: KakaoUserInfo

    @classmethod
    def setUpTestData(cls) -> None:
        cls.kakao_info = KakaoUserInfo(
            provider_id="kakao_001",
            email="exist@example.com",
            name="기존유저",
            nickname="기존닉",
            phone_number="01033334444",
            profile_img_url=None,
            gender="M",
            birthday="1991-05-05",
        )
        cls.user = User(email="exist@example.com", name="기존유저", nickname="기존닉", phone_number="01033334444")
        cls.user.set_unusable_password()
        cls.user.save()
        cls.social_user = SocialUsers.objects.create(user=cls.user, provider="kakao", provider_id="kakao_001")

    @patch("apps.users.services.social_auth.KakaoOAuthService.get_user_info_by_code")
    def test_existing_social_user_returns_is_new_user_false(self, mock: MagicMock) -> None:
        mock.return_value = self.kakao_info
        result = SocialAuthService.process_user(provider="kakao", code="code")
        self.assertFalse(result["is_new_user"])
        self.assertEqual(User.objects.count(), 1)


class NewSocialUserTest(TestCase):
    kakao_info: KakaoUserInfo
    kakao_info_no_email: KakaoUserInfo

    @classmethod
    def setUpTestData(cls) -> None:
        cls.kakao_info = KakaoUserInfo(
            provider_id="kakao_new_001",
            email="new@example.com",
            name="신규유저",
            nickname="신규닉",
            phone_number="01055556666",
            profile_img_url=None,
            gender="F",
            birthday="1995-03-10",
        )
        cls.kakao_info_no_email = KakaoUserInfo(
            provider_id="kakao_new_002",
            email=None,
            name="이메일없음",
            nickname="닉",
            phone_number=None,
            profile_img_url=None,
            gender=None,
            birthday=None,
        )

    @patch("apps.users.services.social_auth.KakaoOAuthService.get_user_info_by_code")
    def test_new_user_created_with_social_users_linked(self, mock: MagicMock) -> None:
        mock.return_value = self.kakao_info
        result = SocialAuthService.process_user(provider="kakao", code="code")
        self.assertTrue(result["is_new_user"])
        created_user = User.objects.get(email="new@example.com")
        self.assertTrue(SocialUsers.objects.filter(user=created_user, provider_id=self.kakao_info.provider_id).exists())

    @patch("apps.users.services.social_auth.KakaoOAuthService.get_user_info_by_code")
    def test_no_email_raises_email_not_provided_error(self, mock: MagicMock) -> None:
        mock.return_value = self.kakao_info_no_email
        with self.assertRaises(EmailNotProvidedError):
            SocialAuthService.process_user(provider="kakao", code="code")

    @patch("apps.users.services.social_auth.SocialUsers.objects.create")
    @patch("apps.users.services.social_auth.KakaoOAuthService.get_user_info_by_code")
    def test_social_users_create_failure_rolls_back_user(self, mock_info: MagicMock, mock_create: MagicMock) -> None:
        mock_info.return_value = self.kakao_info
        mock_create.side_effect = Exception("DB 오류")
        with self.assertRaises(Exception):
            SocialAuthService.process_user(provider="kakao", code="code")
        self.assertFalse(User.objects.filter(email="new@example.com").exists())


class EmailConflictTest(TestCase):
    user: User
    kakao_info: KakaoUserInfo

    @classmethod
    def setUpTestData(cls) -> None:
        cls.kakao_info = KakaoUserInfo(
            provider_id="kakao_conflict_001",
            email="conflict@example.com",
            name="충돌유저",
            nickname="충돌닉",
            phone_number="01077778888",
            profile_img_url=None,
            gender="M",
            birthday="1988-12-25",
        )
        cls.user = User(email="conflict@example.com", name="충돌유저", nickname="충돌닉", phone_number="01077778888")
        cls.user.set_unusable_password()
        cls.user.save()

    @patch("apps.users.services.social_auth.KakaoOAuthService.get_user_info_by_code")
    def test_email_conflict_raises_error(self, mock: MagicMock) -> None:
        mock.return_value = self.kakao_info
        with self.assertRaises(EmailAlreadyRegisteredError):
            SocialAuthService.process_user(provider="kakao", code="code")


class KakaoOAuthServiceTest(TestCase):
    def setUp(self) -> None:
        self.code = "test_code"
        self.redirect_uri = "http://localhost/cb"

    @override_settings(KAKAO_CLIENT_ID="test_id", KAKAO_REDIRECT_URI="http://localhost/cb")
    def test_get_auth_url(self) -> None:
        url = KakaoOAuthService.get_auth_url("dummy_state")
        self.assertIn("test_id", url)
        self.assertIn("kauth.kakao.com", url)

    @patch("apps.users.services.kakao.requests.post")
    def test_get_access_token_success(self, mock: MagicMock) -> None:
        mock.return_value.json.return_value = {"access_token": "kakao_token"}
        self.assertEqual(KakaoOAuthService.get_access_token(self.code, self.redirect_uri), "kakao_token")

    @patch("apps.users.services.kakao.requests.post")
    def test_get_access_token_no_token_raises(self, mock: MagicMock) -> None:
        mock.return_value.json.return_value = {}
        with self.assertRaises(ValueError):
            KakaoOAuthService.get_access_token(self.code, self.redirect_uri)

    @patch("apps.users.services.kakao.requests.post")
    def test_get_access_token_error_field_raises(self, mock: MagicMock) -> None:
        mock.return_value.json.return_value = {"error": "invalid_grant"}
        with self.assertRaises(ValueError):
            KakaoOAuthService.get_access_token(self.code, self.redirect_uri)

    @patch("apps.users.services.kakao.requests.get")
    def test_get_user_info_parses_full_response(self, mock: MagicMock) -> None:
        mock.return_value.json.return_value = {
            "id": 12345,
            "kakao_account": {
                "email": "kakao@test.com",
                "name": "카카오",
                "phone_number": "+82 10-1234-5678",
                "gender": "male",
                "birthyear": "1990",
                "birthday": "0505",
                "profile": {"nickname": "닉", "profile_image_url": "https://img.jpg"},
            },
        }
        info = KakaoOAuthService.get_user_info("token")
        self.assertEqual(info.email, "kakao@test.com")
        self.assertEqual(info.gender, "M")
        self.assertEqual(info.birthday, "1990-05-05")
        self.assertEqual(info.phone_number, "01012345678")

    @patch("apps.users.services.kakao.requests.get")
    def test_get_user_info_missing_optional_fields(self, mock: MagicMock) -> None:
        mock.return_value.json.return_value = {"id": 99, "kakao_account": {"profile": {}}}
        info = KakaoOAuthService.get_user_info("token")
        self.assertIsNone(info.email)
        self.assertIsNone(info.gender)

    def test_normalize_phone_plus82(self) -> None:
        self.assertEqual(KakaoOAuthService._normalize_phone("+82 10-1234-5678"), "01012345678")

    def test_normalize_phone_local(self) -> None:
        self.assertEqual(KakaoOAuthService._normalize_phone("010-1234-5678"), "01012345678")


class NaverOAuthServiceTest(TestCase):
    def setUp(self) -> None:
        self.code = "test_code"
        self.state = "test_state"

    @override_settings(NAVER_CLIENT_ID="naver_id", NAVER_REDIRECT_URI="http://localhost/naver")
    def test_get_auth_url(self) -> None:
        url = NaverOAuthService.get_auth_url(state=self.state)
        self.assertIn("naver_id", url)
        self.assertIn("nid.naver.com", url)

    @patch("apps.users.services.naver.requests.post")
    def test_get_access_token_success(self, mock: MagicMock) -> None:
        mock.return_value.json.return_value = {"access_token": "naver_token"}
        self.assertEqual(NaverOAuthService.get_access_token(self.code, self.state), "naver_token")

    @patch("apps.users.services.naver.requests.post")
    def test_get_access_token_no_token_raises(self, mock: MagicMock) -> None:
        mock.return_value.json.return_value = {}
        with self.assertRaises(ValueError):
            NaverOAuthService.get_access_token(self.code, self.state)

    @patch("apps.users.services.naver.requests.post")
    def test_get_access_token_error_field_raises(self, mock: MagicMock) -> None:
        mock.return_value.json.return_value = {"error": "invalid_grant"}
        with self.assertRaises(ValueError):
            NaverOAuthService.get_access_token(self.code, self.state)

    @patch("apps.users.services.naver.requests.get")
    def test_get_user_info_parses_full_response(self, mock: MagicMock) -> None:
        mock.return_value.json.return_value = {
            "response": {
                "id": "naver_abc",
                "email": "naver@test.com",
                "name": "네이버",
                "nickname": "닉",
                "profile_image": "https://img.jpg",
                "mobile": "010-9876-5432",
                "gender": "F",
                "birthyear": "1995",
                "birthday": "07-20",
            }
        }
        info = NaverOAuthService.get_user_info("token")
        self.assertEqual(info.email, "naver@test.com")
        self.assertEqual(info.gender, "F")
        self.assertEqual(info.birthday, "1995-07-20")
        self.assertEqual(info.phone_number, "01098765432")

    @patch("apps.users.services.naver.requests.get")
    def test_get_user_info_missing_optional_fields(self, mock: MagicMock) -> None:
        mock.return_value.json.return_value = {
            "response": {"id": "naver_xyz", "email": "min@test.com", "name": "최소", "nickname": "닉"}
        }
        info = NaverOAuthService.get_user_info("token")
        self.assertIsNone(info.phone_number)
        self.assertIsNone(info.birthday)
