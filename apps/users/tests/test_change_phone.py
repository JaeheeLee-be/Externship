import uuid
from typing import Optional

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.users.models import User
from apps.users.utils.purpose_enum import SmsPurpose


class ChangePhoneAPITestCase(IsolatedRedisTestClient):
    # 테스트에 사용할 유저 정보
    user: User
    other_user: User
    current_phone: str = "01011112222"
    new_phone: str = "01033334444"
    other_phone: str = "01055556666"

    @classmethod
    def setUpTestData(cls) -> None:
        """테스트 전체에서 공통으로 사용할 유저 생성"""
        cls.user = User.objects.create_user(
            email="test@coding.com",
            password="testPhone12!@",
            name="테스터",
            nickname="tester",
            phone_number=cls.current_phone,
        )
        # 중복 확인 테스트용 다른 유저
        cls.other_user = User.objects.create_user(
            email="other@coding.com",
            password="otherPhone12!@",
            name="다른유저",
            nickname="other",
            phone_number=cls.other_phone,
        )

    def setUp(self) -> None:
        super().setUp()
        # 테스트에 사용할 API URL 및 토큰 설정
        self.url: str = reverse("users:change-phone")
        self.sms_token: str = f"token_{uuid.uuid4().hex}"
        self.cache_key: str = f"sms_verify_token_{self.sms_token}"
        # 기본 유효 페이로드
        self.valid_payload = {"phone_verify_token": self.sms_token}
        # 인증된 유저로 클라이언트 설정
        self.client.force_authenticate(user=self.user)

    def set_cache_data(
        self,
        phone_number: Optional[str] = None,
        purpose: str = SmsPurpose.PHONE_CHANGE.value,
    ) -> None:
        """Redis 캐시에 인증 데이터를 주입"""
        cache.set(
            self.cache_key,
            {"phone_number": phone_number or self.new_phone, "purpose": purpose},
            timeout=300,
        )

    def test_change_phone_success(self) -> None:
        """정상적인 토큰으로 휴대폰 번호 변경 성공 (200) 테스트"""
        self.set_cache_data()
        response = self.client.patch(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "휴대폰 번호 변경에 성공하였습니다.")
        self.assertEqual(response.data["phone_number"], self.new_phone)
        # DB 반영 확인
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, self.new_phone)
        # 사용된 Redis 토큰 삭제 확인
        self.assertIsNone(cache.get(self.cache_key))

    def test_change_phone_with_invalid_token_returns_400(self) -> None:
        """존재하지 않거나 만료된 토큰 사용 시 400 반환 테스트"""
        # 캐시 설정 없이 요청
        response = self.client.patch(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"][0], "유효하지 않거나 만료된 인증 토큰입니다.")

    def test_change_phone_with_wrong_purpose_returns_400(self) -> None:
        """번호 변경용이 아닌 다른 용도의 토큰 사용 시 400 반환 테스트"""
        self.set_cache_data(purpose=SmsPurpose.SIGNUP.value)
        response = self.client.patch(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"][0], "유효하지 않거나 만료된 인증 토큰입니다.")

    def test_change_phone_with_same_number_returns_400(self) -> None:
        """현재 번호와 동일한 번호로 변경 시 400 반환 테스트"""
        self.set_cache_data(phone_number=self.current_phone)
        response = self.client.patch(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"][0], "현재 휴대폰 번호와 동일합니다.")

    def test_change_phone_with_duplicated_number_returns_409(self) -> None:
        """다른 유저가 사용 중인 번호로 변경 시 409 반환 테스트"""
        self.set_cache_data(phone_number=self.other_phone)
        response = self.client.patch(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["error_detail"], "이미 등록된 휴대폰 번호입니다.")

    def test_change_phone_missing_token_returns_400(self) -> None:
        """필수 필드 누락 시 400 반환 테스트"""
        response = self.client.patch(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_change_phone_unauthenticated_returns_401(self) -> None:
        """비로그인 요청 시 401 반환 테스트"""
        self.client.force_authenticate(user=None)
        self.set_cache_data()
        response = self.client.patch(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
