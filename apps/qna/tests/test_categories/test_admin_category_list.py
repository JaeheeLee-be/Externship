from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.question_models import QuestionCategory
from apps.users.models import User


# 어드민 카테고리 목록 조회 API 테스트
class AdminCategoryListAPITest(APITestCase):

    user: User
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="testadmin@example.com",
            password="test1234",
        )
        cls.url = "/api/v1/admin/qna/categories/"

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    # 전체 카테고리 목록 조회 성공
    def test_get_admin_category_list_success(self) -> None:
        large = QuestionCategory._default_manager.create(name="백엔드", parent=None)
        middle = QuestionCategory._default_manager.create(name="프레임워크", parent=large)
        QuestionCategory._default_manager.create(name="Django", parent=middle)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    # category_type 필터 조회 성공
    def test_filter_admin_category_list_by_category_type(self) -> None:
        large = QuestionCategory._default_manager.create(name="백엔드", parent=None)
        middle = QuestionCategory._default_manager.create(name="프레임워크", parent=large)
        QuestionCategory._default_manager.create(name="Django", parent=middle)

        response = self.client.get(self.url, {"category_type": "large"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["category_type"], "large")
        self.assertEqual(response.data[0]["name"], "백엔드")

    # keyword 검색 조회 성공
    def test_filter_admin_category_list_by_keyword(self) -> None:
        large = QuestionCategory._default_manager.create(name="백엔드", parent=None)
        QuestionCategory._default_manager.create(name="프론트엔드", parent=None)
        QuestionCategory._default_manager.create(name="백엔드심화", parent=large)

        response = self.client.get(self.url, {"keyword": "백엔드"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    # 부모 / 자식 카테고리명 포함 여부 확인
    def test_admin_category_list_includes_parent_and_children(self) -> None:
        large = QuestionCategory._default_manager.create(name="백엔드", parent=None)
        middle = QuestionCategory._default_manager.create(name="프레임워크", parent=large)
        QuestionCategory._default_manager.create(name="Django", parent=middle)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        large_item = next(item for item in response.data if item["name"] == "백엔드")
        middle_item = next(item for item in response.data if item["name"] == "프레임워크")
        small_item = next(item for item in response.data if item["name"] == "Django")

        self.assertIsNone(large_item["parent_name"])
        self.assertIn("프레임워크", large_item["child_names"])

        self.assertEqual(middle_item["parent_name"], "백엔드")
        self.assertIn("Django", middle_item["child_names"])

        self.assertEqual(small_item["parent_name"], "프레임워크")
        self.assertEqual(small_item["child_names"], [])

    # 로그인 안 된 경우 실패
    def test_fail_when_not_authenticated(self) -> None:
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )