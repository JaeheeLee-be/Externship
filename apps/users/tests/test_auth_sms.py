from typing import Any
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.users.utils.purpose_enum import SmsPurpose


class SmsAuthViewTests(IsolatedRedisTestClient):

    def setUp(self) -> None:
        super().setUp()
        self.send_url = reverse("users:send-sms")
        self.verify_url = reverse("users:verify-sms")
        self.valid_phone = "01012345678"
        self.valid_purpose = "signup"
        self.valid_code = "123456"

    @patch("apps.users.views.auth_sms_view.SmsVerificationService.send_verification_sms")
    def test_sms_send_view_success(self, mock_send_sms: Any) -> None:
        mock_send_sms.return_value = None  # Service 로직은 성공했다고 가정(Mock)

        data = {"phone_number": self.valid_phone, "purpose": self.valid_purpose}

        response = self.client.post(self.send_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "회원가입을 위한 휴대폰 인증 코드가 전송되었습니다")

        mock_send_sms.assert_called_once_with(self.valid_phone, SmsPurpose(self.valid_purpose))

    def test_sms_send_view_invalid_data(self) -> None:
        data = {"purpose": self.valid_purpose}

        response = self.client.post(self.send_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    @patch("apps.users.views.auth_sms_view.SmsVerificationService.send_verification_sms")
    def test_sms_send_view_service_error(self, mock_send_sms: Any) -> None:
        mock_send_sms.side_effect = ValidationError("SMS 발송 실패")

        data = {"phone_number": self.valid_phone, "purpose": self.valid_purpose}

        response = self.client.post(self.send_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    @patch("apps.users.views.auth_sms_view.SmsVerificationService.verify_sms_code")
    def test_sms_verify_view_success(self, mock_verify_code: Any) -> None:
        mock_sms_token = "mocked_token_string_123"
        mock_verify_code.return_value = mock_sms_token

        data = {"phone_number": self.valid_phone, "code": self.valid_code, "purpose": self.valid_purpose}

        response = self.client.post(self.verify_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "회원가입을 위한 휴대폰 인증에 성공했습니다.")
        self.assertEqual(response.data["sms_token"], mock_sms_token)
        mock_verify_code.assert_called_once_with(self.valid_phone, self.valid_code, SmsPurpose(self.valid_purpose))

    @patch("apps.users.views.auth_sms_view.SmsVerificationService.verify_sms_code")
    def test_sms_verify_view_service_error(self, mock_verify_code: Any) -> None:
        mock_verify_code.side_effect = ValidationError("인증 코드가 일치하지 않습니다.")

        data = {"phone_number": self.valid_phone, "code": "000000", "purpose": self.valid_purpose}

        response = self.client.post(self.verify_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
