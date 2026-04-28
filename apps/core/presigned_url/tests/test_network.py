from unittest.mock import patch

from botocore.exceptions import HTTPClientError
from django.test import TestCase
from freezegun import freeze_time
from moto import mock_aws

from apps.core.presigned_url.s3_handler import get_s3_handler
from apps.core.presigned_url.services import PresignedUrlService


class TestPresignedUrlNetwork(TestCase):
    """
    테스트 요약:

        - @mock_aws가 정상적으로 모킹을 하는지 테스트.
        - s3.create_upload_urls()가 실제 aws 서버 호출 없이 동작하는 메서드인지 테스트
    """

    def setUp(self) -> None:
        self.s3_handler = get_s3_handler()

    @mock_aws
    def test_mock(self) -> None:
        """
        s3가 테스트 케이스 외부에서 생성된 인스턴스임에도
        @mock_aws가 aws 서버와의 실제 접촉을 잘 차단하는지 테스트

        결과:
            @mock_aws 없었을 때:
                'Buckets': [{'Name': 'oz-externship', ...}]

            @mock_aws 적용했을 때:
                'Buckets': []

        결론: aws와의 접촉을 잘 차단함.
        """

        bucket_list = self.s3_handler.s3.list_buckets()
        self.assertEqual(bucket_list["Buckets"], [])

    @patch("socket.socket", None)
    def test_patch(self) -> None:
        """
        @patch가 네트워크 연결을 잘 차단하는지 테스트

        결과: s3.s3.list_buckets() 실행 도중 HTTPClientError 발생

        결론: 네트워크 차단 잘 작동함
        """

        with self.assertRaises(HTTPClientError):
            self.s3_handler.s3.list_buckets()

    @patch("socket.socket", None)
    def test_s3_create_upload_urls(self) -> None:
        """
        s3.create_upload_urls가 aws에 접촉하는 함수인지 아닌지를 테스트

        결과: list_buckets()는 네트워크가 끊겼을 때 에러가 났지만,
            create_upload_urls()는 에러가 나지 않고 잘 작동함

        결론: s3.create_upload_urls는 로컬 계산만 하는 함수임.
        """

        urls_dict = PresignedUrlService.create_upload_urls("test.jpg", "image/jpeg", "test/")
        self.assertTrue(urls_dict["presigned_url"].startswith("https://"))
        self.assertTrue(urls_dict["img_url"].startswith("https://"))

    # 모킹된 presigned_url과 그렇지 않은 presigned_url이 동일한지
    @freeze_time("2026-04-27 11:11:11")
    def test_mocked_presigned_url(self) -> None:

        @mock_aws
        def mocking() -> str:
            return self.s3_handler.presigned_url_for_upload(key="path/uuid_test.jpg", content_type="image/jpeg")

        presigned_url = self.s3_handler.presigned_url_for_upload(key="path/uuid_test.jpg", content_type="image/jpeg")
        mocked_presigned_url = mocking()

        self.assertEqual(presigned_url, mocked_presigned_url)
