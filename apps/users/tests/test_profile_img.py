from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.utils.test_factories import create_test_user
from apps.users.models import User


class ProfileImageViewTest(APITestCase):
    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = create_test_user("profileimg")

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("users:profile-image")
        self.img_url = "https://oz-externship.s3.amazonaws.com/uploads/images/profiles/uuid.png"

    def test_success(self) -> None:
        """[성공] 200 + DB 반영 확인"""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.url, {"profile_img_url": self.img_url}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile_img_url, self.img_url)

    def test_null_url_clears_profile_image(self) -> None:
        """[성공] null 허용 — 미등록 상태"""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.url, {"profile_img_url": None}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.profile_img_url)

    def test_missing_field_returns_400(self) -> None:
        """[실패] profile_img_url 없음"""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_unauthenticated_returns_401(self) -> None:
        """[실패] Authorization 헤더 없음"""
        response = self.client.patch(self.url, {"profile_img_url": self.img_url}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
