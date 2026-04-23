from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import SocialUsers, User
from apps.users.services.kakao import KakaoUserInfo
from apps.users.services.naver import NaverUserInfo
from apps.users.services.social_auth import SocialAuthService


# ── 공통 픽스처 ──────────────────────────────────────────────

def make_user(**kwargs) -> User:
    """테스트용 User 생성"""
    defaults = {
        "email": "test@example.com",
        "name": "테스트유저",
        "nickname": "test",
        "phone_number": "01012345678",
        "is_active": True,
    }
    defaults.update(kwargs)
    user = User(**defaults)
    user.set_unusable_password()
    user.save()
    return user


def make_social_user(user: User, provider: str, provider_id: str) -> SocialUsers:
    """테스트용 소셜유저 생성"""
    return SocialUsers.objects.create(
        user=user,
        provider=provider,
        provider_id=provider_id,
    )


def make_kakao_user_info(**kwargs) -> KakaoUserInfo:
    """테스트용 KakaoUserInfo 생성"""
    defaults = {
        "provider_id": "kakao_123",
        "nickname": "카카오닉네임",
        "profile_img_url": None,
        "email": "kakao@example.com",
        "name": "카카오유저",
        "phone_number": "01099999999",
        "gender": "male",
        "birthday": "1990-01-01",
    }
    defaults.update(kwargs)
    return KakaoUserInfo(**defaults)


def make_naver_user_info(**kwargs) -> NaverUserInfo:
    """테스트용 NaverUserInfo 생성"""
    defaults = {
        "provider_id": "naver_123",
        "nickname": "네이버닉네임",
        "profile_img_url": None,
        "email": "naver@example.com",
        "name": "네이버유저",
        "phone_number": "01088888888",
        "gender": "female",
        "birthday": "1992-03-15",
    }
    defaults.update(kwargs)
    return NaverUserInfo(**defaults)


# ════════════════════════════════════════
#  카카오
# ════════════════════════════════════════

# ── KakaoLoginView ────────────────────────────────────────────

class KakaoLoginViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_login_redirects_to_kakao_auth(self):
        """카카오 로그인 요청 시 카카오 인증 페이지로 302 리다이렉트"""
        response = self.client.get(reverse("users:kakao-login"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("https://kauth.kakao.com/oauth/authorize", response["Location"])


# ── KakaoCallbackView ─────────────────────────────────────────

class KakaoCallbackViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("users:kakao-callback")

    def test_error_param_redirects_to_fail(self):
        """카카오가 error 파라미터 내려줄 때 실패 페이지로 리다이렉트"""
        response = self.client.get(self.url, {"error": "access_denied"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("social-login/fail", response["Location"])

    def test_missing_code_redirects_to_fail(self):
        """code 없이 요청 시 실패 페이지로 리다이렉트"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("social-login/fail", response["Location"])

    @patch("apps.users.views.social_views.KakaoOAuthService.get_user_info_by_code")
    @patch("apps.users.views.social_views.SocialAuthService.login_or_register")
    def test_existing_user_redirects_to_success(self, mock_login, mock_kakao):
        """기존 유저: JWT 발급 후 success 페이지로 리다이렉트"""
        mock_kakao.return_value = make_kakao_user_info()
        mock_login.return_value = {
            "is_new_user": False,
            "access": "access_token_value",
            "refresh": "refresh_token_value",
        }

        response = self.client.get(self.url, {"code": "valid_code"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("social-login/success", response["Location"])
        self.assertEqual(response["X-Access-Token"], "access_token_value")

    @patch("apps.users.views.social_views.KakaoOAuthService.get_user_info_by_code")
    @patch("apps.users.views.social_views.SocialAuthService.login_or_register")
    def test_new_user_redirects_to_success(self, mock_login, mock_kakao):
        """신규 유저: 추가 입력 없이 바로 회원가입 후 success 페이지로 리다이렉트"""
        mock_kakao.return_value = make_kakao_user_info(
            provider_id="kakao_new_user",
            nickname="신규유저",
        )
        mock_login.return_value = {
            "is_new_user": True,
            "access": "new_access_token",
            "refresh": "new_refresh_token",
        }

        response = self.client.get(self.url, {"code": "valid_code"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("social-login/success", response["Location"])
        self.assertEqual(response["X-Access-Token"], "new_access_token")
        self.assertNotIn("signup/kakao", response["Location"])  # 예전 흐름으로 가면 안 됨

    @patch("apps.users.views.social_views.KakaoOAuthService.get_user_info_by_code")
    def test_kakao_api_error_redirects_to_fail(self, mock_kakao):
        """카카오 API 오류 시 실패 페이지로 리다이렉트"""
        import requests as req
        mock_kakao.side_effect = req.RequestException("카카오 서버 오류")

        response = self.client.get(self.url, {"code": "bad_code"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("social-login/fail", response["Location"])


# ── KakaoOAuthService.get_user_info ──────────────────────────

class KakaoGetUserInfoTest(TestCase):

    @patch("apps.users.services.kakao.requests.get")
    def test_parses_all_fields(self, mock_get):
        """카카오 API 응답에서 모든 필드를 올바르게 파싱"""
        from apps.users.services.kakao import KakaoOAuthService

        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "id": 123456,
            "kakao_account": {
                "profile": {
                    "nickname": "카카오닉네임",
                    "profile_image_url": "https://img.kakao.com/profile.jpg",
                },
                "email": "kakao@example.com",
                "name": "홍길동",
                "phone_number": "+82 10-1234-5678",
                "gender": "male",
                "birthyear": "1990",
                "birthday": "0101",
            },
        }

        user_info = KakaoOAuthService.get_user_info("fake_access_token")

        self.assertEqual(user_info.provider_id, "123456")
        self.assertEqual(user_info.nickname, "카카오닉네임")
        self.assertEqual(user_info.email, "kakao@example.com")
        self.assertEqual(user_info.name, "홍길동")
        self.assertEqual(user_info.phone_number, "+82 10-1234-5678")
        self.assertEqual(user_info.gender, "male")
        self.assertEqual(user_info.birthday, "1990-01-01")  # YYYY-MM-DD 조합 확인

    @patch("apps.users.services.kakao.requests.get")
    def test_birthday_none_when_missing(self, mock_get):
        """birthyear 또는 birthday 둘 중 하나라도 없으면 birthday=None"""
        from apps.users.services.kakao import KakaoOAuthService

        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "id": 999,
            "kakao_account": {
                "profile": {},
                "birthyear": "1990",
                # birthday 없음
            },
        }

        user_info = KakaoOAuthService.get_user_info("fake_token")
        self.assertIsNone(user_info.birthday)


# ── SocialAuthService - 카카오 ────────────────────────────────

class KakaoLoginOrRegisterTest(TestCase):

    def test_existing_user_returns_jwt(self):
        """기존 카카오 유저 로그인 시 is_new_user=False + JWT 반환"""
        user = make_user()
        make_social_user(user, provider="kakao", provider_id="kakao_123")

        result = SocialAuthService.login_or_register(
            provider="kakao",
            provider_id="kakao_123",
            email="kakao@example.com",
            name="카카오유저",
            nickname="카카오닉네임",
            profile_img_url=None,
            phone_number="01099999999",
            gender="male",
            birthday="1990-01-01",
        )

        self.assertFalse(result["is_new_user"])
        self.assertIn("access", result)
        self.assertIn("refresh", result)

    def test_new_user_creates_user_and_social(self):
        """신규 카카오 유저: User + SocialUsers 생성 후 is_new_user=True + JWT 반환"""
        result = SocialAuthService.login_or_register(
            provider="kakao",
            provider_id="kakao_new_456",
            email="newkakao@example.com",
            name="신규유저",
            nickname="신규닉네임",
            profile_img_url=None,
            phone_number="01011112222",
            gender="female",
            birthday="1995-05-05",
        )

        self.assertTrue(result["is_new_user"])
        self.assertIn("access", result)

        user = User.objects.get(email="newkakao@example.com")
        self.assertEqual(user.name, "신규유저")
        self.assertTrue(
            SocialUsers.objects.filter(provider="kakao", provider_id="kakao_new_456").exists()
        )

    def test_existing_user_no_duplicate_created(self):
        """기존 카카오 유저 재로그인 시 중복 생성 안 됨"""
        user = make_user()
        make_social_user(user, provider="kakao", provider_id="kakao_123")

        SocialAuthService.login_or_register(
            provider="kakao",
            provider_id="kakao_123",
            email="kakao@example.com",
            name="카카오유저",
            nickname="카카오닉네임",
            profile_img_url=None,
            phone_number="01099999999",
            gender="male",
            birthday="1990-01-01",
        )

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(SocialUsers.objects.count(), 1)


# ════════════════════════════════════════
#  네이버
# ════════════════════════════════════════

# ── NaverLoginView ────────────────────────────────────────────

class NaverLoginViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_login_redirects_to_naver_auth(self):
        """네이버 로그인 요청 시 네이버 인증 페이지로 302 리다이렉트 (state 포함)"""
        response = self.client.get(reverse("users:naver-login"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("https://nid.naver.com/oauth2.0/authorize", response["Location"])
        self.assertIn("state=", response["Location"])  # CSRF 방지 state 포함 확인


# ── NaverCallbackView ─────────────────────────────────────────

class NaverCallbackViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("users:naver-callback")

    def test_error_param_redirects_to_fail(self):
        """네이버가 error 파라미터 내려줄 때 실패 페이지로 리다이렉트"""
        response = self.client.get(self.url, {"error": "access_denied", "state": "somestate"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("social-login/fail", response["Location"])

    def test_missing_code_redirects_to_fail(self):
        """code 없이 요청 시 실패 페이지로 리다이렉트"""
        response = self.client.get(self.url, {"state": "somestate"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("social-login/fail", response["Location"])

    def test_missing_state_redirects_to_fail(self):
        """state 없이 요청 시 실패 페이지로 리다이렉트"""
        response = self.client.get(self.url, {"code": "valid_code"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("social-login/fail", response["Location"])

    @patch("apps.users.views.social_views.NaverOAuthService.get_user_info_by_code")
    @patch("apps.users.views.social_views.SocialAuthService.login_or_register")
    def test_existing_user_redirects_to_success(self, mock_login, mock_naver):
        """기존 유저: JWT 발급 후 success 페이지로 리다이렉트"""
        mock_naver.return_value = make_naver_user_info()
        mock_login.return_value = {
            "is_new_user": False,
            "access": "naver_access_token",
            "refresh": "naver_refresh_token",
        }

        response = self.client.get(self.url, {"code": "valid_code", "state": "somestate"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("social-login/success", response["Location"])
        self.assertEqual(response["X-Access-Token"], "naver_access_token")

    @patch("apps.users.views.social_views.NaverOAuthService.get_user_info_by_code")
    @patch("apps.users.views.social_views.SocialAuthService.login_or_register")
    def test_new_user_redirects_to_success(self, mock_login, mock_naver):
        """신규 유저: 바로 회원가입 후 success 페이지로 리다이렉트"""
        mock_naver.return_value = make_naver_user_info(
            provider_id="naver_new_user",
            nickname="신규네이버유저",
        )
        mock_login.return_value = {
            "is_new_user": True,
            "access": "new_naver_access_token",
            "refresh": "new_naver_refresh_token",
        }

        response = self.client.get(self.url, {"code": "valid_code", "state": "somestate"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("social-login/success", response["Location"])
        self.assertEqual(response["X-Access-Token"], "new_naver_access_token")

    @patch("apps.users.views.social_views.NaverOAuthService.get_user_info_by_code")
    def test_naver_api_error_redirects_to_fail(self, mock_naver):
        """네이버 API 오류 시 실패 페이지로 리다이렉트"""
        import requests as req
        mock_naver.side_effect = req.RequestException("네이버 서버 오류")

        response = self.client.get(self.url, {"code": "bad_code", "state": "somestate"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("social-login/fail", response["Location"])


# ── NaverOAuthService.get_user_info ──────────────────────────

class NaverGetUserInfoTest(TestCase):

    @patch("apps.users.services.naver.requests.get")
    def test_parses_all_fields(self, mock_get):
        """네이버 API 응답에서 모든 필드를 올바르게 파싱"""
        from apps.users.services.naver import NaverOAuthService

        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {
                "id": "naver_abc",
                "email": "naver@example.com",
                "name": "김네이버",
                "nickname": "네이버닉",
                "profile_image": "https://img.naver.com/profile.jpg",
                "mobile": "010-1234-5678",
                "gender": "F",
                "birthyear": "1992",
                "birthday": "03-15",
            }
        }

        user_info = NaverOAuthService.get_user_info("fake_access_token")

        self.assertEqual(user_info.provider_id, "naver_abc")
        self.assertEqual(user_info.email, "naver@example.com")
        self.assertEqual(user_info.name, "김네이버")
        self.assertEqual(user_info.phone_number, "01012345678")   # 하이픈 제거 확인
        self.assertEqual(user_info.gender, "female")              # F → female 변환 확인
        self.assertEqual(user_info.birthday, "1992-03-15")        # YYYY-MM-DD 조합 확인

    @patch("apps.users.services.naver.requests.get")
    def test_gender_male_conversion(self, mock_get):
        """성별 M → male 변환 확인"""
        from apps.users.services.naver import NaverOAuthService

        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {"id": "n1", "gender": "M", "mobile": "", "birthyear": "", "birthday": ""}
        }

        user_info = NaverOAuthService.get_user_info("fake_token")
        self.assertEqual(user_info.gender, "male")

    @patch("apps.users.services.naver.requests.get")
    def test_birthday_none_when_missing(self, mock_get):
        """birthyear 또는 birthday 둘 중 하나라도 없으면 birthday=None"""
        from apps.users.services.naver import NaverOAuthService

        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {
                "id": "n2",
                "birthyear": "1990",
                # birthday 없음
            }
        }

        user_info = NaverOAuthService.get_user_info("fake_token")
        self.assertIsNone(user_info.birthday)


# ── SocialAuthService - 네이버 ────────────────────────────────

class NaverLoginOrRegisterTest(TestCase):

    def test_existing_user_returns_jwt(self):
        """기존 네이버 유저 로그인 시 is_new_user=False + JWT 반환"""
        user = make_user(email="naver@example.com", nickname="navertest", phone_number="01088888888")
        make_social_user(user, provider="naver", provider_id="naver_123")

        result = SocialAuthService.login_or_register(
            provider="naver",
            provider_id="naver_123",
            email="naver@example.com",
            name="네이버유저",
            nickname="네이버닉네임",
            profile_img_url=None,
            phone_number="01088888888",
            gender="female",
            birthday="1992-03-15",
        )

        self.assertFalse(result["is_new_user"])
        self.assertIn("access", result)
        self.assertIn("refresh", result)

    def test_new_user_creates_user_and_social(self):
        """신규 네이버 유저: User + SocialUsers 생성 후 is_new_user=True + JWT 반환"""
        result = SocialAuthService.login_or_register(
            provider="naver",
            provider_id="naver_new_789",
            email="newnaver@example.com",
            name="신규네이버",
            nickname="신규네이버닉",
            profile_img_url=None,
            phone_number="01033334444",
            gender="male",
            birthday="2000-12-31",
        )

        self.assertTrue(result["is_new_user"])
        self.assertIn("access", result)

        user = User.objects.get(email="newnaver@example.com")
        self.assertEqual(user.name, "신규네이버")
        self.assertTrue(
            SocialUsers.objects.filter(provider="naver", provider_id="naver_new_789").exists()
        )

    def test_existing_user_no_duplicate_created(self):
        """기존 네이버 유저 재로그인 시 중복 생성 안 됨"""
        user = make_user(email="naver@example.com", nickname="navertest", phone_number="01088888888")
        make_social_user(user, provider="naver", provider_id="naver_123")

        SocialAuthService.login_or_register(
            provider="naver",
            provider_id="naver_123",
            email="naver@example.com",
            name="네이버유저",
            nickname="네이버닉네임",
            profile_img_url=None,
            phone_number="01088888888",
            gender="female",
            birthday="1992-03-15",
        )

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(SocialUsers.objects.count(), 1)
