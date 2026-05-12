import uuid

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.users.models import User
from apps.users.utils.purpose_enum import AuthPurpose


class PasswordResetAPITestCase(IsolatedRedisTestClient):
    # 테스트에 사용할 유저 정보
    user: User
    user_password: str = "oldassword12!@"
    new_password: str = "newpassword12!@"

    @classmethod
    def setUpTestData(cls) -> None:
        """테스트 전체에서 공통으로 사용할 유저 생성"""
        cls.user = User.objects.create_user(
            email="test@coding.com",
            password=cls.user_password,
            name="재설정테스터",
            nickname="tester",
            phone_number="010-9999-8888",
        )

    def setUp(self) -> None:
        super().setUp()
        # 테스트에 사용할 API URL 및 토큰 설정
        self.url: str = reverse("users:find_password")
        self.email_token: str = f"token_{uuid.uuid4().hex}"
        self.cache_key: str = f"email_verify_token_{self.email_token}"

        # 기본 유효 페이로드
        self.valid_payload = {
            "email_token": self.email_token,
            "new_password": self.new_password,
        }

    def set_cache_data(self, purpose: str = AuthPurpose.FIND_PASSWORD.value) -> None:
        """Redis 캐시에 인증 데이터를 주입하는 헬퍼 메서드"""
        cache.set(self.cache_key, {"email": self.user.email, "purpose": purpose}, timeout=300)

    def test_password_reset_success(self) -> None:
        """정상적인 토큰으로 비밀번호 재설정 성공 (200) 테스트"""
        self.set_cache_data()

        response = self.client.post(self.url, self.valid_payload, format="json")

        # 상태 코드 및 메시지 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "비밀번호 변경 성공.")

        # 실제 DB 반영 여부 확인
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))

        # 사용된 Redis 토큰 삭제 확인
        self.assertIsNone(cache.get(self.cache_key))

    def test_password_reset_with_invalid_token_returns_400(self) -> None:
        """존재하지 않거나 만료된 토큰 사용 시 400 반환 테스트"""
        # 캐시 설정 없이 요청
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"][0], "유효하지 않거나 만료된 인증 토큰입니다.")

    def test_password_reset_with_wrong_purpose_returns_400(self) -> None:
        """비밀번호 재설정용이 아닌 다른 용도의 토큰(예: 회원가입용) 사용 시 400 반환"""
        # SIGNUP 용도
        self.set_cache_data(purpose=AuthPurpose.SIGNUP.value)

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"][0], "유효하지 않거나 만료된 인증 토큰입니다.")

    def test_password_reset_missing_fields_returns_400(self) -> None:
        """필수 필드 누락 시 400 반환 테스트"""
        data = {"email_token": self.email_token}  # 비밀번호 필드 누락

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_password_reset_same_as_old_returns_400(self) -> None:
        """기존 비밀번호와 동일한 비밀번호로 재설정 시도 시 400 반환"""
        self.set_cache_data()

        payload = {"email_token": self.email_token, "new_password": self.user_password}  # 기존과 동일한 값

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"][0], "기존 비밀번호와 동일한 비밀번호로 변경할 수 없습니다.")
