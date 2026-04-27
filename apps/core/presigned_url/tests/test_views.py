from typing import Any

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.core.presigned_url.views import PresignedUrlView


class TestPresignedUrlSubclass(TestCase):

    # 서브클래스에서 path를 정의하지 않았을 때 에러가 나는지
    def test_path_required(self) -> None:
        with self.assertRaises(TypeError) as e:

            class NoPathView(PresignedUrlView):
                pass

        self.assertEqual(str(e.exception), "NoPathView에 path 클래스 변수를 정의해야 합니다")

    # 서브클래스에서 path를 str 외의 타입으로 정의했을 때 에러가 나는지
    def test_path_type(self) -> None:
        with self.assertRaises(TypeError) as e:

            class InvalidPathView(PresignedUrlView):
                path = 123  # type: ignore[assignment]

        self.assertEqual(str(e.exception), "InvalidPathView: path는 str이어야 합니다.")

    # 서브클래스에서 expire를 int 외의 타입으로 정의했을 때 에러가 나는지
    def test_expire_type(self) -> None:
        with self.assertRaises(TypeError) as e:

            class InvalidExpireView(PresignedUrlView):
                path = "test/"
                expire = "600"  # type: ignore[assignment]

        self.assertEqual(str(e.exception), "InvalidExpireView: expire는 int여야 합니다.")


class TestPresignedUrlView(TestCase):
    view: Any
    factory: APIRequestFactory

    @classmethod
    def setUpTestData(cls) -> None:
        class PresignedUrlSubclass(PresignedUrlView):
            path = "test/"

        cls.view = PresignedUrlSubclass.as_view()
        cls.factory = APIRequestFactory()

    def setUp(self) -> None: ...

    # 올바른 request인 경우 성공하는지
    def test_success(self) -> None:
        request = self.factory.put(
            path="test/",
            data={"file_name": "test.jpg"},
            format="json",
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("presigned_url", response.data)
        self.assertIn("img_url", response.data)
        self.assertIn("key", response.data)
        self.assertEqual(set(response.data.keys()), {"presigned_url", "img_url", "key"})

    # request의 file_name이 올바르지 않은 경우 에러를 내는지
    def test_invalid_request(self) -> None:
        request = self.factory.put(
            path="test/",
            data={"file_name": "test.test"},
            format="json",
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error_detail": "지원하지 않는 파일 형식입니다."})
