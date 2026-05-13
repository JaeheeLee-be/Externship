from typing import Any

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory

import apps.core.presigned_url.s3_handler as s3_module
from apps.core.utils.s3 import PresignedUrlView

FAKE_S3 = dict(
    AWS_S3_REGION="ap-northeast-2",
    AWS_S3_ACCESS_KEY_ID="test-key",
    AWS_S3_SECRET_ACCESS_KEY="test-secret",
    AWS_S3_BUCKET_NAME="test-bucket",
)


@override_settings(**FAKE_S3)
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

    def setUp(self) -> None:
        s3_module.s3_handler = None

    def tearDown(self) -> None:
        s3_module.s3_handler = None

    def test_success(self) -> None:
        request = self.factory.put(
            path="test/",
            data={"file_name": "test.jpg"},
            format="json",
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {"presigned_url", "img_url", "key"})
