from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

# core 앱에 정의된 공통 테스트 클라이언트를 임포트합니다.
from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient


class EmailVerificationAPITests(IsolatedRedisTestClient):
    def setUp(self) -> None:
        super().setUp()
        self.email = "test_user@ozcoding.com"
        self.purpose = "signup"

        self.send_url = reverse("users:send-email")
        self.verify_url = reverse("users:verify-email")

    def test_send_email_success(self) -> None:
        """이메일 발송 성공 테스트"""
        data = {"email": self.email, "purpose": self.purpose}

        response = self.client.post(self.send_url, data)

        # 1. HTTP 200 응답 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "이메일 인증코드가 전송되었습니다")

        # 2. 메일이 가상 우체통(outbox)에 1통 잘 들어갔는지 확인
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.email])

        # 3. Redis 캐시에 코드가 잘 저장되었는지 확인
        cache_key = f"email_code_{self.email}"
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertIn("code", cached_data)
        self.assertEqual(cached_data["purpose"], self.purpose)

    def test_send_email_invalid_email(self) -> None:
        """잘못된 이메일 형식 발송 실패 테스트"""
        data = {"email": "invalid_email_format", "purpose": self.purpose}

        response = self.client.post(self.send_url, data)

        # 400 에러 확인 및 아까 수정한 status 반환 로직이 잘 작동하는지 확인
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["error_detail"])
        self.assertEqual(len(mail.outbox), 0)

    def test_verify_email_success(self) -> None:
        """인증 코드 검증 성공 테스트"""
        valid_code = "aB3dE5"

        # 1. 테스트를 위해 캐시에 미리 인증 코드를 강제로 세팅
        cache_key = f"email_code_{self.email}"
        cache.set(cache_key, {"code": valid_code, "purpose": self.purpose}, timeout=300)

        data = {"email": self.email, "code": valid_code}

        response = self.client.post(self.verify_url, data)

        # 2. 200 성공 및 토큰 발급 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "이메일 인증이 성공했습니다")
        self.assertIn("email_token", response.data)

        # 3. 검증 완료 후 기존 인증번호 캐시가 삭제되었는지 확인
        self.assertIsNone(cache.get(cache_key))

        # 4. 검증 완료 증명 토큰이 캐시에 저장되었는지 확인
        email_token = response.data["email_token"]
        token_key = f"purpose_{self.purpose}_verify_token_{email_token}"
        self.assertEqual(cache.get(token_key), self.email)

    def test_verify_email_invalid_code(self) -> None:
        """틀린 인증 코드 입력 시 실패 테스트"""
        valid_code = "aB3dE5"

        # 1. 캐시에 정상 코드를 세팅
        cache_key = f"email_code_{self.email}"
        cache.set(cache_key, {"code": valid_code, "purpose": self.purpose}, timeout=300)

        data = {"email": self.email, "code": "WRONG1"}  # 틀린 코드 전송

        response = self.client.post(self.verify_url, data)

        # 2. 400 에러 및 메시지 확인
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data["error_detail"])

        # 3. 실패했으므로 재시도를 위해 캐시가 삭제되지 않고 남아있어야 함
        self.assertIsNotNone(cache.get(cache_key))

    def test_verify_email_expired_code(self) -> None:
        """인증 시간이 만료된(캐시에 없는) 경우 실패 테스트"""
        #  캐시에 아무것도 세팅하지 않음으로써 '만료된 상황'
        data = {"email": self.email, "code": "123456"}

        response = self.client.post(self.verify_url, data)

        # 400 에러 및 적절한 에러 메시지가 나오는지 확인
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 에러 메시지에 '만료'나 '요청' 등의 키워드가 포함되어 있는지 확인 (실제 뷰 로직에 맞춰 수정하세요)
        self.assertIn("code", response.data["error_detail"])

    def test_send_email_invalid_purpose(self) -> None:
        """유효하지 않은 purpose 값 발송 실패 테스트"""
        # 'hack'이라는 허용되지 않은 purpose 전송
        data = {"email": self.email, "purpose": "hack"}

        response = self.client.post(self.send_url, data)

        # 400 에러와 함께 purpose 필드에 대한 에러가 났는지 확인
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("purpose", response.data["error_detail"])
        self.assertEqual(len(mail.outbox), 0)  # 메일 발송 안됨
