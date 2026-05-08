# apps/users/tests/test_check_nickname_view.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.users.models import User


class CheckNicknameViewTest(APITestCase):
    user: User
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("users:check-nickname")

        cls.user = User.objects.create_user(
            email="user@test.com",
            password="Test1234!",
            name="테스트",
            nickname="기존닉네임",
            phone_number="01011112222",
        )

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_available_nickname(self) -> None:
        """사용 가능한 닉네임 - 200"""
        response = self.client.post(
            self.url,
            data={"nickname": "새닉네임"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "사용 가능한 닉네임입니다."})

    def test_duplicate_nickname(self) -> None:
        """중복된 닉네임 - 409"""
        response = self.client.post(
            self.url,
            data={"nickname": "기존닉네임"},  # 이미 있는 닉네임
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error_detail", response.data)
        self.assertEqual(response.data["error_detail"], "중복된 닉네임이 존재합니다.")

    def test_missing_nickname(self) -> None:
        """닉네임 누락 - 400"""
        response = self.client.post(
            self.url,
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("nickname", response.data["error_detail"])

    def test_invalid_nickname_format(self) -> None:
        """닉네임 정규식 위반 - 400"""
        response = self.client.post(
            self.url,
            data={"nickname": "닉@#$"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_unauthenticated(self) -> None:
        """비로그인 시 401"""
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.url,
            data={"nickname": "새닉네임"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)
        self.assertEqual(
            response.data["error_detail"],
            "자격 인증 데이터가 제공되지 않았습니다.",
        )
