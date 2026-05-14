from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.question_models import QuestionCategory
from apps.users.models import User


# 유저 카테고리 목록 조회 API 테스트
class CategoryListAPITest(APITestCase):

    user: User
    url: str
    large: QuestionCategory
    middle: QuestionCategory
    small: QuestionCategory

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="testuser@example.com",
            password="test1234",
            role="STUDENT",
        )
        cls.url = "/api/v1/qna/categories"

        cls.large = QuestionCategory.objects.create(name="백엔드", parent=None)
        cls.middle = QuestionCategory.objects.create(name="프레임워크", parent=cls.large)
        cls.small = QuestionCategory.objects.create(name="Django", parent=cls.middle)

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    # 전체 카테고리 트리 조회 성공
    def test_get_category_tree_success(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("categories", response.data)

    # 응답이 트리 구조인지 확인
    def test_response_is_tree_structure(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        categories = response.data["categories"]
        self.assertEqual(len(categories), 1)

        large_item = categories[0]
        self.assertEqual(large_item["name"], "백엔드")
        self.assertEqual(large_item["category_type"], "large")
        self.assertEqual(len(large_item["children"]), 1)

        middle_item = large_item["children"][0]
        self.assertEqual(middle_item["name"], "프레임워크")
        self.assertEqual(middle_item["category_type"], "middle")
        self.assertEqual(len(middle_item["children"]), 1)

        small_item = middle_item["children"][0]
        self.assertEqual(small_item["name"], "Django")
        self.assertEqual(small_item["category_type"], "small")
        self.assertEqual(small_item["children"], [])

    # 대분류만 최상위로 노출되는지 확인
    def test_only_large_categories_at_top_level(self) -> None:
        QuestionCategory.objects.create(name="프론트엔드", parent=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        top_level_names = [c["name"] for c in response.data["categories"]]
        self.assertIn("백엔드", top_level_names)
        self.assertIn("프론트엔드", top_level_names)
        self.assertNotIn("프레임워크", top_level_names)
        self.assertNotIn("Django", top_level_names)

    # 응답 필드 확인
    def test_response_contains_required_fields(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        item = response.data["categories"][0]
        self.assertIn("id", item)
        self.assertIn("name", item)
        self.assertIn("category_type", item)
        self.assertIn("children", item)

    # 카테고리 없을 때 빈 리스트 반환
    def test_empty_category_list(self) -> None:
        QuestionCategory.objects.all().delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["categories"], [])

    # 비로그인도 카테고리 목록 조회 가능
    def test_unauthenticated_can_view_categories(self) -> None:
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
