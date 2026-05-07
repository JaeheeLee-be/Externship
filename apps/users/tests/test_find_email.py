import uuid

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.users.models import User
from apps.users.utils.purpose_enum import SmsPurpose


class FindEmailAPITestCase(IsolatedRedisTestClient):
    # 테스트에 사용할 유저 정보
    user: User
    name: str = "테스터"
    masked_email: str = "t**t@c***ng.com"

    @classmethod
    def setUpTestData(cls) -> None:
        """테스트 전체에서 공통으로 사용할 유저 생성"""
        cls.user = User.objects.create_user(
            email="test@coding.com",
            password="testfinde12!@",
            name=cls.name,
            nickname="tester",
            phone_number="010-9999-8888",
        )

    def setUp(self) -> None:
        super().setUp()
        # 테스트에 사용할 API URL 및 토큰 설정
        self.url: str = reverse("users:find_email")
        self.sms_token: str = f"token_{uuid.uuid4().hex}"
        self.cache_key: str = f"sms_verify_token_{self.sms_token}"

        # 기본 유효 페이로드
        self.valid_payload = {
            "sms_token": self.sms_token,
            "name": self.name,
        }

    def set_cache_data(self, purpose: str = SmsPurpose.FIND_EMAIL.value) -> None:
        """Redis 캐시에 인증 데이터를 주입하는 헬퍼 메서드"""
        cache.set(self.cache_key, {"phone_number": self.user.phone_number, "purpose": purpose}, timeout=300)

    def test_find_email_success(self) -> None:
        """정상적인 토큰으로 이메일 확인 성공 (200) 테스트"""
        self.set_cache_data()

        response = self.client.post(self.url, self.valid_payload, format="json")

        # 상태 코드 및 메시지 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.masked_email)
        # 사용된 Redis 토큰 삭제 확인
        self.assertIsNone(cache.get(self.cache_key))

    def test_find_email_with_invalid_token_returns_400(self) -> None:
        """존재하지 않거나 만료된 토큰 사용 시 400 반환 테스트"""
        # 캐시 설정 없이 요청
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"][0], "유효하지 않거나 만료된 인증 토큰입니다.")

    def test_find_email_with_wrong_purpose_returns_400(self) -> None:
        """이메일 찾기용이 아닌 다른 용도의 토큰(예: 회원가입용) 사용 시 400 반환"""
        # SIGNUP 용도
        self.set_cache_data(purpose=SmsPurpose.SIGNUP.value)

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"][0], "유효하지 않거나 만료된 인증 토큰입니다.")

    def test_find_email_missing_fields_returns_400(self) -> None:
        """필수 필드 누락 시 400 반환 테스트"""
        data = {"sms_token": self.sms_token}  # 이름 필드 누락

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
