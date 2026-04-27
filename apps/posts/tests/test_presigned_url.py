from django.urls import reverse
from moto import mock_aws
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.utils.test_factories import create_test_user


class PresignedUrlViewTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_test_user("uploader")
        self.url = reverse("presigned_url")

    @mock_aws
    def test_generate_presigned_url_success(self) -> None:
        self.client.force_authenticate(user=self.user)
        payload = {"file_name": "cat.png"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("presigned_url", response.data)
        self.assertIn("img_url", response.data)
        self.assertIn("key", response.data)
        self.assertTrue(response.data["presigned_url"].startswith("https://"))
        self.assertTrue(response.data["img_url"].startswith("https://"))
        self.assertTrue(response.data["key"].startswith("uploads/images/posts/"))
        self.assertTrue(response.data["key"].endswith(".png"))

    def test_missing_file_name(self) -> None:
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("file_name", response.data["error_detail"])

    def test_invalid_extension(self) -> None:
        self.client.force_authenticate(user=self.user)
        payload = {"file_name": "malware.exe"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertEqual(response.data["error_detail"], "지원하지 않는 파일 형식입니다.")

    def test_no_extension(self) -> None:
        self.client.force_authenticate(user=self.user)
        payload = {"file_name": "noextfile"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_unauthenticated(self) -> None:
        payload = {"file_name": "cat.png"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
