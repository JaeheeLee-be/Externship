from django.test import TestCase

from apps.core.presigned_url.s3_handler import get_s3_handler


class TestS3Handler(TestCase):
    def setUp(self) -> None:
        self.s3_handler = get_s3_handler()
        self.key = "t"*154 + ".jpg"  # 이론상 key 최대 길이
        self.content_type = "image/jpeg"

    # img_url이 잘 생성되는지
    def test_img_url(self) -> None:
        img_url = self.s3_handler.img_url(self.key)
        self.assertEqual(img_url, f"https://{self.s3_handler.bucket}.s3.{self.s3_handler.region}.amazonaws.com/{self.key}")

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