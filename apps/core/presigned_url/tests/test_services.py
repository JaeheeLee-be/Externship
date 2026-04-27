from django.test import TestCase

from apps.core.presigned_url.services import PresignedUrlService


class TestServices(TestCase):
    def setUp(self):
        self.file_name = "test.jpg"
        self.path = "test/"
        self.key = PresignedUrlService._key(file_name=self.file_name, path=self.path)

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
        url = PresignedUrlService.create_upload_urls(file_name=self.file_name, content_type="image/jpeg", path=self.path)
        self.assertEqual(len(self.key), 50)
        self.assertIn(url["key"], url["img_url"])
        self.assertIn(url["img_url"], url["presigned_url"])