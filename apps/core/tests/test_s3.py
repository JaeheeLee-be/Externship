from typing import Any

from django.test import TestCase
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory

from apps.core.utils.s3 import PresignedUrlView


class TestS3(TestCase):
    view: Any
    factory: APIRequestFactory

    @classmethod
    def setUpTestData(cls) -> None:
        class PresignedUrlSubclass(PresignedUrlView):
            permission_classes = [AllowAny]
            path = "test/"

        cls.view = PresignedUrlSubclass.as_view()
        cls.factory = APIRequestFactory()

    def test_success(self) -> None:
        request = self.factory.put(
            path="test/",
            data={"file_name": "test.jpg"},
            format="json",
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {"presigned_url", "img_url", "key"})
