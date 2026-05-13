from django.test import TestCase, override_settings

import apps.core.presigned_url.s3_handler as s3_module
from apps.core.presigned_url.services import PresignedUrlService

FAKE_S3 = dict(
    AWS_S3_REGION="ap-northeast-2",
    AWS_S3_ACCESS_KEY_ID="test-key",
    AWS_S3_SECRET_ACCESS_KEY="test-secret",
    AWS_S3_BUCKET_NAME="test-bucket",
)


@override_settings(**FAKE_S3)
class TestServices(TestCase):
    def setUp(self) -> None:
        s3_module.s3_handler = None
        self.file_name = "test.jpg"
        self.path = "test/"
        self.key = PresignedUrlService._key(file_name=self.file_name, path=self.path)

    def tearDown(self) -> None:
        s3_module.s3_handler = None

    # path 마지막에 슬래시가 있어도 key가 의도한대로 생성되는지
    def test_key_path_with_slash(self) -> None:
        self.assertNotIn("//", self.key)
        self.assertTrue(self.key.startswith("test/"))
        self.assertTrue(self.key.endswith(".jpg"))

    # path 마지막에 슬래시가 없어도 key가 의도한대로 생성되는지
    def test_key_path_without_slash(self) -> None:
        key = PresignedUrlService._key(file_name=self.file_name, path="test")
        self.assertNotIn("//", key)
        self.assertTrue(key.startswith("test/"))
        self.assertTrue(key.endswith(".jpg"))

    # create_upload_urls()가 잘 작동하는지
    def test_create_upload_urls(self) -> None:
        url = PresignedUrlService.create_upload_urls(
            file_name=self.file_name, content_type="image/jpeg", path=self.path
        )
        self.assertEqual(len(self.key), 50)
        self.assertIn(url["key"], url["img_url"])
        self.assertIn(url["img_url"], url["presigned_url"])
