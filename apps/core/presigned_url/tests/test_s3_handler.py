import apps.core.presigned_url.s3_handler as s3_module
from django.test import TestCase, override_settings

from apps.core.presigned_url.s3_handler import get_s3_handler

FAKE_S3 = dict(
    AWS_S3_REGION="ap-northeast-2",
    AWS_S3_ACCESS_KEY_ID="test-key",
    AWS_S3_SECRET_ACCESS_KEY="test-secret",
    AWS_S3_BUCKET_NAME="test-bucket",
)


@override_settings(**FAKE_S3)
class TestS3Handler(TestCase):
    def setUp(self) -> None:
        s3_module.s3_handler = None
        self.s3_handler = get_s3_handler()
        self.key = "t" * 154 + ".jpg"  # 이론상 key 최대 길이
        self.content_type = "image/jpeg"

    def tearDown(self) -> None:
        s3_module.s3_handler = None

    # img_url이 잘 생성되는지
    def test_img_url(self) -> None:
        img_url = self.s3_handler.img_url(self.key)
        self.assertEqual(
            img_url, f"https://{self.s3_handler.bucket}.s3.{self.s3_handler.region}.amazonaws.com/{self.key}"
        )

    # img_url이 255자 이내인지.
    def test_img_url_length(self) -> None:
        img_url = self.s3_handler.img_url(self.key)
        self.assertLessEqual(len(img_url), 255)

    # presigned_url이 잘 생성되는지
    def test_presigned_url_for_upload(self) -> None:
        presigned_url = self.s3_handler.presigned_url_for_upload(self.key, self.content_type)
        self.assertEqual(presigned_url.count("?"), 1)
        self.assertTrue(presigned_url.startswith("https://"))
        self.assertIn(self.key, presigned_url)
        self.assertIn("X-Amz-Signature", presigned_url)
        self.assertIn("X-Amz-Credential", presigned_url)
        self.assertIn("X-Amz-Algorithm", presigned_url)
        self.assertIn("X-Amz-Expires=600", presigned_url)

    # get_s3_handler()로 생성한 객체가 동일한 객체인지
    def test_singleton(self) -> None:
        s3_handler = get_s3_handler()
        self.assertIs(self.s3_handler, s3_handler)
