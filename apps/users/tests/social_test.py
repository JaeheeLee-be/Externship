# from typing import Any
# from unittest.mock import patch
#
# from django.test import TestCase
# from django.urls import reverse
# from rest_framework.test import APIClient
#
# from apps.users.services.kakao import KakaoUserInfo
# from apps.users.services.naver import NaverUserInfo
#
# # ── 공통 픽스처 ──────────────────────────────────────────────
#
#
# def make_kakao_user_info(**kwargs: Any) -> KakaoUserInfo:
#     defaults: dict[str, Any] = {
#         "provider_id": "kakao_123",
#         "nickname": "카카오닉네임",
#         "profile_img_url": None,
#         "email": "kakao@example.com",
#         "name": "카카오유저",
#         "phone_number": "01099999999",
#         "gender": "M",
#         "birthday": "1990-01-01",
#     }
#     defaults.update(kwargs)
#     return KakaoUserInfo(**defaults)
#
#
# def make_naver_user_info(**kwargs: Any) -> NaverUserInfo:
#     defaults: dict[str, Any] = {
#         "provider_id": "naver_123",
#         "nickname": "네이버닉네임",
#         "profile_img_url": None,
#         "email": "naver@example.com",
#         "name": "네이버유저",
#         "phone_number": "01088888888",
#         "gender": "F",
#         "birthday": "1992-03-15",
#     }
#     defaults.update(kwargs)
#     return NaverUserInfo(**defaults)
#
#
# #  카카오
#
#
# class KakaoLoginViewTest(TestCase):
#     def setUp(self) -> None:
#         self.client = APIClient()
#
#     def test_login_redirects_to_kakao_auth(self) -> None:
#         """카카오 로그인 요청 시 카카오 인증 페이지로 302 리다이렉트"""
#         response = self.client.get(reverse("users:social-login", kwargs={"provider": "kakao"}))
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("https://kauth.kakao.com/oauth/authorize", response["Location"])
#
#
# class KakaoCallbackViewTest(TestCase):
#     def setUp(self) -> None:
#         self.client = APIClient()
#         self.url = reverse("users:social-callback", kwargs={"provider": "kakao"})
#
#     def test_error_param_redirects_to_fail(self) -> None:
#         """카카오가 error 파라미터 내려줄 때 실패 페이지로 리다이렉트"""
#         response = self.client.get(self.url, {"error": "access_denied"})
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("is_success=false", response["Location"])
#
#     def test_missing_code_redirects_to_fail(self) -> None:
#         """code 없이 요청 시 실패 페이지로 리다이렉트"""
#         response = self.client.get(self.url)
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("is_success=false", response["Location"])
#
#     @patch("apps.users.services.social_login_service.SocialLoginService.login")
#     def test_existing_user_redirects_to_success(self, mock_login: object) -> None:
#         """기존 유저: JWT 발급 후 success 페이지로 리다이렉트"""
#         mock_login.return_value = {  # type: ignore[attr-defined]
#             "is_new_user": False,
#             "access": "access_token_value",
#             "refresh": "refresh_token_value",
#         }
#
#         response = self.client.get(self.url, {"code": "valid_code"})
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("is_success=true", response["Location"])
#         self.assertIn("access_token=access_token_value", response["Location"])
#
#     @patch("apps.users.services.social_login_service.SocialLoginService.login")
#     def test_new_user_redirects_to_success(self, mock_login: object) -> None:
#         """신규 유저: 바로 회원가입 후 success 페이지로 리다이렉트"""
#         mock_login.return_value = {  # type: ignore[attr-defined]
#             "is_new_user": True,
#             "access": "new_access_token",
#             "refresh": "new_refresh_token",
#         }
#
#         response = self.client.get(self.url, {"code": "valid_code"})
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("is_success=true", response["Location"])
#         self.assertIn("access_token=new_access_token", response["Location"])
#
#     @patch("apps.users.services.social_login_service.SocialLoginService.login")
#     def test_kakao_api_error_redirects_to_fail(self, mock_login: object) -> None:
#         """카카오 API 오류 시 실패 페이지로 리다이렉트"""
#         from apps.users.services.social_auth import SocialAuthError
#
#         mock_login.side_effect = SocialAuthError("카카오 서버 오류")  # type: ignore[attr-defined]
#
#         response = self.client.get(self.url, {"code": "bad_code"})
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("is_success=false", response["Location"])
#
#
# #  네이버
#
#
# class NaverLoginViewTest(TestCase):
#     def setUp(self) -> None:
#         self.client = APIClient()
#
#     def test_login_redirects_to_naver_auth(self) -> None:
#         """네이버 로그인 요청 시 네이버 인증 페이지로 302 리다이렉트 (state 포함)"""
#         response = self.client.get(reverse("users:social-login", kwargs={"provider": "naver"}))
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("https://nid.naver.com/oauth2.0/authorize", response["Location"])
#         self.assertIn("state=", response["Location"])
#
#
# class NaverCallbackViewTest(TestCase):
#     def setUp(self) -> None:
#         self.client = APIClient()
#         self.url = reverse("users:social-callback", kwargs={"provider": "naver"})
#
#     def _set_naver_state(self, state: str) -> None:
#         """세션에 naver oauth state 주입"""
#         session = self.client.session
#         session["naver_oauth_state"] = state
#         session.save()
#
#     def test_error_param_redirects_to_fail(self) -> None:
#         """네이버가 error 파라미터 내려줄 때 실패 페이지로 리다이렉트"""
#         response = self.client.get(self.url, {"error": "access_denied", "state": "somestate"})
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("is_success=false", response["Location"])
#
#     def test_missing_code_redirects_to_fail(self) -> None:
#         """code 없이 요청 시 실패 페이지로 리다이렉트"""
#         response = self.client.get(self.url, {"state": "somestate"})
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("is_success=false", response["Location"])
#
#     def test_missing_state_redirects_to_fail(self) -> None:
#         """state 없이 요청 시 실패 페이지로 리다이렉트"""
#         response = self.client.get(self.url, {"code": "valid_code"})
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("is_success=false", response["Location"])
#
#     @patch("apps.users.services.social_login_service.SocialLoginService.login")
#     def test_existing_user_redirects_to_success(self, mock_login: object) -> None:
#         """기존 유저: JWT 발급 후 success 페이지로 리다이렉트"""
#         self._set_naver_state("somestate")
#         mock_login.return_value = {  # type: ignore[attr-defined]
#             "is_new_user": False,
#             "access": "naver_access_token",
#             "refresh": "naver_refresh_token",
#         }
#
#         response = self.client.get(self.url, {"code": "valid_code", "state": "somestate"})
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("is_success=true", response["Location"])
#         self.assertIn("access_token=naver_access_token", response["Location"])
#
#     @patch("apps.users.services.social_login_service.SocialLoginService.login")
#     def test_new_user_redirects_to_success(self, mock_login: object) -> None:
#         """신규 유저: 바로 회원가입 후 success 페이지로 리다이렉트"""
#         self._set_naver_state("somestate")
#         mock_login.return_value = {  # type: ignore[attr-defined]
#             "is_new_user": True,
#             "access": "new_naver_access_token",
#             "refresh": "new_naver_refresh_token",
#         }
#
#         response = self.client.get(self.url, {"code": "valid_code", "state": "somestate"})
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("is_success=true", response["Location"])
#         self.assertIn("access_token=new_naver_access_token", response["Location"])
#
#     @patch("apps.users.services.social_login_service.SocialLoginService.login")
#     def test_naver_api_error_redirects_to_fail(self, mock_login: object) -> None:
#         """네이버 API 오류 시 실패 페이지로 리다이렉트"""
#         from apps.users.services.social_auth import SocialAuthError
#
#         self._set_naver_state("somestate")
#         mock_login.side_effect = SocialAuthError("네이버 서버 오류")  # type: ignore[attr-defined]
#
#         response = self.client.get(self.url, {"code": "bad_code", "state": "somestate"})
#
#         self.assertEqual(response.status_code, 302)
#         self.assertIn("is_success=false", response["Location"])
