from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.users.models import User
from apps.users.services.user_login_service import UserLoginService


class AuthAPITestCase(IsolatedRedisTestClient):
    # 테스트에 사용할 테스트 유저
    user: User
    user_password: str = "TestPassword123!"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="testuser@ozcoding.com",
            password=cls.user_password,
            name="테스트지형",
            nickname="test_jh",
            phone_number="010-1234-5678",
        )

    def setUp(self) -> None:
        super().setUp()

        # 테스트에 사용할 API URL.
        self.login_url: str = reverse("users:login")
        self.logout_url: str = reverse("users:logout")
        self.refresh_url: str = reverse("users:token_refresh")

    def test_login_success(self) -> None:
        data: dict[str, str] = {"email": "testuser@ozcoding.com", "password": self.user_password}

        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 응답 바디에 access_token이 있는지 확인
        self.assertIn("access_token", response.data)
        # 쿠키에 refresh_token이 있는지 확인
        self.assertIn("refresh_token", response.cookies)

    def test_login_with_wrong_password_returns_403(self) -> None:
        data = {"email": "testuser@ozcoding.com", "password": "WrongPassword!"}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error_detail"],
            "입력한 이메일 또는 비밀번호가 잘못되었습니다.",
        )

    def test_login_inactive_user(self) -> None:
        """비활성화 된계정 로그인 시 403과 에러 메시지 반환"""
        self.user.is_active = False
        self.user.save()

        data = {"email": "testuser@ozcoding.com", "password": self.user_password}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "비활성된 계정입니다.")

    def test_login_withdrawn_user(self) -> None:
        """탈퇴 신청 계정 로그인 시 403과 expire_at 반환."""
        from apps.users.models import Withdrawal  # 모델 경로/필드명에 맞춰 조정

        due = date.today() + timedelta(days=30)
        Withdrawal.objects.create(user=self.user, due_date=due)

        data = {"email": "testuser@ozcoding.com", "password": self.user_password}
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error_detail"]["detail"],
            "탈퇴 신청한 계정입니다.",
        )
        self.assertEqual(
            response.data["error_detail"]["expire_at"],
            due.strftime("%Y-%m-%d"),
        )

    def test_logout_success(self) -> None:
        """로그아웃 시 토큰이 Redis 블랙리스트에 등록되는지 테스트"""
        # 토큰의 유효성만 확인하 access_token 받지만 사용 x
        _, refresh_token = UserLoginService.generate_token_pair(self.user)

        # 클라이언트 쿠키에 해당 토큰을 세팅
        self.client.cookies["refresh_token"] = refresh_token

        # 로그아웃 요청
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        #  토큰이 블랙리스트에 올랐는지 검증
        self.assertTrue(UserLoginService.is_blacklisted(refresh_token))
        #  쿠키가 삭제되었는지 확인
        self.assertEqual(response.cookies["refresh_token"].value, "")

    def test_token_refresh_success(self) -> None:
        """유효한 리프레시 토큰으로 재발급을 요청할 때 성공하는지 테스트"""
        _, refresh_token = UserLoginService.generate_token_pair(self.user)

        # 쿠키에 refresh token 담아서 요청
        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 응답 확인 access token 확인
        self.assertIn("access_token", response.data)
        # 기존 토큰은 재사용을 막기 위해 블랙리스트 등록
        self.assertTrue(UserLoginService.is_blacklisted(refresh_token))

    def test_blacklisted_token_rejected(self) -> None:
        """이미 블랙리스트에 등록된 토큰으로 재발급 시도 시 403 에러과 에러 메시지 반환."""
        _, refresh_token = UserLoginService.generate_token_pair(self.user)

        # 토큰을 블랙리스트에 추가
        UserLoginService.add_to_blacklist(refresh_token)

        # 차단된 토큰으로 재발급을 시도 (쿠키에 담아서 요청)
        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post(self.refresh_url)

        # 403 상태 코드 반환 확인
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(response.data["error_detail"], "로그인 세션이 만료되었습니다.")

    def test_malformed_token_rejected(self) -> None:
        """변조된 토큰으로 재발급 시도 시 403과 에러 메시지 반환."""
        self.client.cookies["refresh_token"] = "this.is.not.a.valid.jwt"
        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error_detail"],
            "로그인 세션이 만료되었습니다.",
        )
