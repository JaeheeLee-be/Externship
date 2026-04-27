from django.test import TestCase
from rest_framework.exceptions import APIException

from apps.core.presigned_url.serializers import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)


class TestPresignedUrlRequestSerializer(TestCase):

    # 확장자가 없는 파일이 들어온 경우 에러가 발생하는지
    def test_blank_suffix(self) -> None:
        data = {"file_name": "test_file"}

        with self.assertRaises(APIException) as e:
            serializer = PresignedUrlRequestSerializer(data=data)
            serializer.is_valid(raise_exception=True)
        self.assertEqual(e.exception.detail["error_detail"], "지원하지 않는 파일 형식입니다.")  # type: ignore

    # 화이트리스트에 없는 확장자가 들어온 경우 예외처리가 되는지
    def test_invalid_suffix(self) -> None:
        data = {"file_name": "test_file.test"}

        with self.assertRaises(APIException) as e:
            serializer = PresignedUrlRequestSerializer(data=data)
            serializer.is_valid(raise_exception=True)
        self.assertEqual(e.exception.detail["error_detail"], "지원하지 않는 파일 형식입니다.")  # type: ignore

    # file_name의 길이 제한 테스트
    def test_max_length(self) -> None:
        data = {"file_name": f"{"test"*25}.jpg"}
        with self.assertRaises(APIException) as e:
            serializer = PresignedUrlRequestSerializer(data=data)
            serializer.is_valid(raise_exception=True)

    # 대문자 확장자를 넣어도 소문자로 변환이 되는지
    def test_suffix_lowercase(self) -> None:
        data = {"file_name": "test_file.JPG"}

        serializer = PresignedUrlRequestSerializer(data=data)
        serializer.is_valid()
        self.assertEqual(serializer.validated_data["file_name"], "test_file.jpg")

    # 화이트리스트에 등록된 확장자가 들어온 경우 의도한 값을 반환을 하는지
    def test_valid_suffix(self) -> None:
        data = {"file_name": "test_file.jpg"}

        serializer = PresignedUrlRequestSerializer(data=data)
        serializer.is_valid()
        self.assertEqual(serializer.validated_data, data)


class TestPresignedUrlResponseSerializer(TestCase):

    def setUp(self) -> None:
        self.instance = {
            "presigned_url": "https://test/uuid.jpg?Sign",
            "img_url": "https://test/uuid.jpg",
            "key": "test/uuid.jpg",
        }

    # valid한 인스턴스를 넣었을 때 의도한 값이 나오는지
    def test_valid_instance(self) -> None:
        serializer = PresignedUrlResponseSerializer(instance=self.instance)
        self.assertEqual(serializer.data, self.instance)
