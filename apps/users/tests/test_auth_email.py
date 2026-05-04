from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient


class EmailVerificationAPITests(IsolatedRedisTestClient):
    def setUp(self) -> None:
        super().setUp()
        self.email = "test_user@ozcoding.com"
        self.valid_code = "aB3dE5"

        self.send_url = reverse("users:send-email")
        self.verify_url = reverse("users:verify-email")

    def test_send_email_success(self) -> None:
        """[성공] 정상적인 이메일 및 용도로 인증 코드 발송"""
        purpose = "signup"
        data = {"email": self.email, "purpose": purpose}

        response = self.client.post(self.send_url, data)

        # 1. HTTP 200 응답 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "이메일 인증 코드가 전송되었습니다")

        # 2. 메일이 가상 우체통(outbox)에 1통 잘 들어갔는지 확인
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.email])

        # 3. Redis 캐시에 코드가 잘 저장되었는지 확인
        cache_key = f"email_code_{self.email}"
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertIn("code", cached_data)
        self.assertEqual(cached_data["purpose"], purpose)

    def test_send_email_invalid_email(self) -> None:
        """[실패] 잘못된 이메일 형식 발송 테스트"""
        data = {"email": "invalid_email_format", "purpose": "signup"}

        response = self.client.post(self.send_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["error_detail"])
        self.assertEqual(len(mail.outbox), 0)

    def test_send_email_invalid_purpose(self) -> None:
        """[실패] 유효하지 않은 purpose 값 발송 테스트"""
        # 'hack'이라는 허용되지 않은 purpose 전송
        data = {"email": self.email, "purpose": "hack"}

        response = self.client.post(self.send_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("purpose", response.data["error_detail"])
        self.assertEqual(len(mail.outbox), 0)

    def test_verify_email_signup_success(self) -> None:
        """[성공] 회원가입 용도"""
        purpose = "signup"
        cache_key = f"email_code_{self.email}"
        cache.set(cache_key, {"code": self.valid_code, "purpose": purpose}, timeout=300)

        data = {"email": self.email, "code": self.valid_code, "purpose": purpose}
        response = self.client.post(self.verify_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "이메일 인증에 성공하였습니다")
        self.assertIn("email_token", response.data)

        # 토큰 발급 및 기존 캐시 삭제 확인
        verify_token = response.data["email_token"]
        token_key = f"email_verify_token_{verify_token}"

        cached_data = cache.get(token_key)
        self.assertIsNotNone(cached_data)  # 캐시가 존재하는지 확인
        self.assertEqual(cached_data["email"], self.email)  # 이메일이 맞는지 확인
        self.assertEqual(cached_data["purpose"], purpose)  # 용도도 맞게 들어갔는지 확인

    def test_verify_email_find_password_success(self) -> None:
        """[성공] 비밀번호 찾기 용도"""
        purpose = "find_password"
        cache_key = f"email_code_{self.email}"
        cache.set(cache_key, {"code": self.valid_code, "purpose": purpose}, timeout=300)

        data = {"email": self.email, "code": self.valid_code, "purpose": purpose}
        response = self.client.post(self.verify_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "이메일 인증에 성공하였습니다")

    def test_verify_email_recovery_success(self) -> None:
        """[성공] 계정 복구 용도"""
        purpose = "recovery"
        cache_key = f"email_code_{self.email}"
        cache.set(cache_key, {"code": self.valid_code, "purpose": purpose}, timeout=300)

        data = {"email": self.email, "code": self.valid_code, "purpose": purpose}
        response = self.client.post(self.verify_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "이메일 인증에 성공하였습니다")

    def test_verify_email_invalid_code(self) -> None:
        """[실패] 틀린 인증 코드 입력 시 실패 테스트"""
        purpose = "signup"
        cache_key = f"email_code_{self.email}"
        cache.set(cache_key, {"code": self.valid_code, "purpose": purpose}, timeout=300)

        data = {"email": self.email, "code": "WRONG1", "purpose": purpose}
        response = self.client.post(self.verify_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("인증코드가 만료되거나 일치하지 않습니다.", response.data["error_detail"])

        # 실패했으므로 재시도를 위해 캐시가 삭제되지 않고 남아있어야 함
        self.assertIsNotNone(cache.get(cache_key))

    def test_verify_email_expired_code(self) -> None:
        """[실패] 인증 시간이 만료된(캐시에 없는) 경우 실패 테스트"""
        # 캐시에 아무것도 세팅하지 않음으로써 '만료된 상황' 가정
        data = {"email": self.email, "code": self.valid_code, "purpose": "signup"}
        response = self.client.post(self.verify_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("인증코드가 만료되거나 발급되지 않았습니다.", response.data["error_detail"])
