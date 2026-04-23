from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.users.models import SocialUsers, User
from apps.users.services.social_auth import SocialAuthService


# ── 공통 픽스처 ──────────────────────────────────────────────

def make_user(**kwargs: object) -> User:
    defaults: dict[str, object] = {
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
    return SocialUsers.objects.create(
        user=user,
        provider=provider,
        provider_id=provider_id,
    )


#  카카오 API 파싱

class KakaoGetUserInfoTest(TestCase):

    @patch("apps.users.services.kakao.requests.get")
    def test_parses_all_fields(self, mock_get: MagicMock) -> None:
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
        self.assertEqual(user_info.birthday, "1990-01-01")

    @patch("apps.users.services.kakao.requests.get")
    def test_birthday_none_when_missing(self, mock_get: MagicMock) -> None:
        """birthyear 또는 birthday 둘 중 하나라도 없으면 birthday=None"""
        from apps.users.services.kakao import KakaoOAuthService

        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "id": 999,
            "kakao_account": {
                "profile": {},
                "birthyear": "1990",
            },
        }

        user_info = KakaoOAuthService.get_user_info("fake_token")
        self.assertIsNone(user_info.birthday)


#  네이버 API 파싱

class NaverGetUserInfoTest(TestCase):

    @patch("apps.users.services.naver.requests.get")
    def test_parses_all_fields(self, mock_get: MagicMock) -> None:
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
        self.assertEqual(user_info.phone_number, "01012345678")  # 하이픈 제거 확인
        self.assertEqual(user_info.gender, "female")             # F → female 변환 확인
        self.assertEqual(user_info.birthday, "1992-03-15")       # YYYY-MM-DD 조합 확인

    @patch("apps.users.services.naver.requests.get")
    def test_gender_male_conversion(self, mock_get: MagicMock) -> None:
        """성별 M → male 변환 확인"""
        from apps.users.services.naver import NaverOAuthService

        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {"id": "n1", "gender": "M", "mobile": "", "birthyear": "", "birthday": ""}
        }

        user_info = NaverOAuthService.get_user_info("fake_token")
        self.assertEqual(user_info.gender, "male")

    @patch("apps.users.services.naver.requests.get")
    def test_birthday_none_when_missing(self, mock_get: MagicMock) -> None:
        """birthyear 또는 birthday 둘 중 하나라도 없으면 birthday=None"""
        from apps.users.services.naver import NaverOAuthService

        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "response": {
                "id": "n2",
                "birthyear": "1990",
            }
        }

        user_info = NaverOAuthService.get_user_info("fake_token")
        self.assertIsNone(user_info.birthday)


#  SocialAuthService (카카오 + 네이버 공통)

class KakaoLoginOrRegisterTest(TestCase):

    def test_existing_user_returns_jwt(self) -> None:
        """기존 카카오 유저 로그인 시 is_new_user=False + JWT 반환"""
        user = make_user()
        make_social_user(user, provider="kakao", provider_id="kakao_123")

        result = SocialAuthService.login_or_register(
            provider="kakao", provider_id="kakao_123",
            email="kakao@example.com", name="카카오유저",
            nickname="카카오닉네임", profile_img_url=None,
            phone_number="01099999999", gender="male", birthday="1990-01-01",
        )

        self.assertFalse(result["is_new_user"])
        self.assertIn("access", result)
        self.assertIn("refresh", result)

    def test_new_user_creates_user_and_social(self) -> None:
        """신규 카카오 유저: User + SocialUsers 생성 후 is_new_user=True + JWT 반환"""
        result = SocialAuthService.login_or_register(
            provider="kakao", provider_id="kakao_new_456",
            email="newkakao@example.com", name="신규유저",
            nickname="신규닉네임", profile_img_url=None,
            phone_number="01011112222", gender="female", birthday="1995-05-05",
        )

        self.assertTrue(result["is_new_user"])
        self.assertIn("access", result)

        user = User.objects.get(email="newkakao@example.com")
        self.assertEqual(user.name, "신규유저")
        self.assertTrue(
            SocialUsers.objects.filter(provider="kakao", provider_id="kakao_new_456").exists()
        )

    def test_existing_user_no_duplicate_created(self) -> None:
        """기존 카카오 유저 재로그인 시 중복 생성 안 됨"""
        user = make_user()
        make_social_user(user, provider="kakao", provider_id="kakao_123")

        SocialAuthService.login_or_register(
            provider="kakao", provider_id="kakao_123",
            email="kakao@example.com", name="카카오유저",
            nickname="카카오닉네임", profile_img_url=None,
            phone_number="01099999999", gender="male", birthday="1990-01-01",
        )

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(SocialUsers.objects.count(), 1)


class NaverLoginOrRegisterTest(TestCase):

    def test_existing_user_returns_jwt(self) -> None:
        """기존 네이버 유저 로그인 시 is_new_user=False + JWT 반환"""
        user = make_user(email="naver@example.com", nickname="navertest", phone_number="01088888888")
        make_social_user(user, provider="naver", provider_id="naver_123")

        result = SocialAuthService.login_or_register(
            provider="naver", provider_id="naver_123",
            email="naver@example.com", name="네이버유저",
            nickname="네이버닉네임", profile_img_url=None,
            phone_number="01088888888", gender="female", birthday="1992-03-15",
        )

        self.assertFalse(result["is_new_user"])
        self.assertIn("access", result)
        self.assertIn("refresh", result)

    def test_new_user_creates_user_and_social(self) -> None:
        """신규 네이버 유저: User + SocialUsers 생성 후 is_new_user=True + JWT 반환"""
        result = SocialAuthService.login_or_register(
            provider="naver", provider_id="naver_new_789",
            email="newnaver@example.com", name="신규네이버",
            nickname="신규네이버닉", profile_img_url=None,
            phone_number="01033334444", gender="male", birthday="2000-12-31",
        )

        self.assertTrue(result["is_new_user"])
        self.assertIn("access", result)

        user = User.objects.get(email="newnaver@example.com")
        self.assertEqual(user.name, "신규네이버")
        self.assertTrue(
            SocialUsers.objects.filter(provider="naver", provider_id="naver_new_789").exists()
        )

    def test_existing_user_no_duplicate_created(self) -> None:
        """기존 네이버 유저 재로그인 시 중복 생성 안 됨"""
        user = make_user(email="naver@example.com", nickname="navertest", phone_number="01088888888")
        make_social_user(user, provider="naver", provider_id="naver_123")

        SocialAuthService.login_or_register(
            provider="naver", provider_id="naver_123",
            email="naver@example.com", name="네이버유저",
            nickname="네이버닉네임", profile_img_url=None,
            phone_number="01088888888", gender="female", birthday="1992-03-15",
        )

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(SocialUsers.objects.count(), 1)
