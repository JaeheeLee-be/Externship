from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.question_models import QuestionCategory
from apps.users.models import User


# 어드민 카테고리 생성 API 테스트
class AdminCategoryCreateAPITest(APITestCase):

    user: User
    url: str

    # 테스트 클래스에서 한 번만 실행됨 (DB 생성 1회)
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="testadmin@example.com",
            password="test1234",
            role="ADMIN",
        )
        cls.url = "/api/v1/admin/qna/categories/"

    # 테스트마다 실행됨 (상태 객체 초기화)
    def setUp(self) -> None:
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    # 대분류 카테고리 생성 성공 테스트
    def test_create_large_category_success(self) -> None:
        payload = {
            "category_type": "large",
            "name": "백엔드",
            "parent_id": None,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuestionCategory.objects.count(), 1)

        category = QuestionCategory.objects.first()
        self.assertIsNotNone(category)
        assert category is not None

        self.assertEqual(category.name, "백엔드")
        self.assertIsNone(category.parent)

        self.assertEqual(response.data["category_id"], category.id)
        self.assertEqual(response.data["name"], "백엔드")
        self.assertEqual(response.data["category_type"], "large")
        self.assertIsNone(response.data["parent_id"])
        self.assertIn("created_at", response.data)

    # 중분류 생성 성공 테스트
    # - 부모는 반드시 대분류여야 함
    def test_create_middle_category_success(self) -> None:

        parent = QuestionCategory.objects.create(name="백엔드", parent=None)

        payload = {
            "category_type": "middle",
            "name": "프레임워크",
            "parent_id": parent.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuestionCategory.objects.count(), 2)

        category = QuestionCategory.objects.get(name="프레임워크")
        self.assertEqual(category.parent, parent)

        self.assertEqual(response.data["category_type"], "middle")
        self.assertEqual(response.data["parent_id"], parent.id)

    # 소분류 생성 성공 테스트
    # - 부모는 반드시 중분류여야 함
    def test_create_small_category_success(self) -> None:

        large = QuestionCategory.objects.create(name="백엔드", parent=None)
        middle = QuestionCategory.objects.create(name="프레임워크", parent=large)

        payload = {
            "category_type": "small",
            "name": "Django",
            "parent_id": middle.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        category = QuestionCategory.objects.get(name="Django")
        self.assertEqual(category.parent, middle)

        self.assertEqual(response.data["category_type"], "small")
        self.assertEqual(response.data["parent_id"], middle.id)

    # 이름이 공백이면 실패
    def test_fail_when_name_is_blank(self) -> None:
        payload = {
            "category_type": "large",
            "name": "",
            "parent_id": None,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error_detail"],
            "카테고리 종류와 이름은 필수 입력값입니다.",
        )

    # 중분류에 부모 없을때
    def test_fail_when_middle_has_no_parent(self) -> None:
        payload = {
            "category_type": "middle",
            "name": "프레임워크",
            "parent_id": None,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["error_detail"],
            "부모 카테고리를 찾을 수 없습니다.",
        )

    # 존재 하지 않는 parent_id
    def test_fail_when_parent_not_found(self) -> None:
        payload = {
            "category_type": "middle",
            "name": "프레임워크",
            "parent_id": 99999,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["error_detail"],
            "부모 카테고리를 찾을 수 없습니다.",
        )

    # 소분류인데 부모가 대분류일 경우
    def test_fail_when_small_parent_depth_invalid(self) -> None:
        large = QuestionCategory.objects.create(name="백엔드", parent=None)

        payload = {
            "category_type": "small",
            "name": "Django",
            "parent_id": large.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error_detail"],
            "소분류의 부모는 중분류여야 합니다.",
        )

    # 중복된 카테고리
    def test_fail_when_duplicate_name(self) -> None:
        parent = QuestionCategory.objects.create(name="백엔드", parent=None)
        QuestionCategory.objects.create(name="프레임워크", parent=parent)

        payload = {
            "category_type": "middle",
            "name": "프레임워크",
            "parent_id": parent.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["error_detail"],
            "동일한 이름의 카테고리가 이미 존재합니다.",
        )

    # 로그인 안됐을때 요청
    def test_fail_when_not_authenticated(self) -> None:

        self.client.force_authenticate(user=None)

        payload = {
            "category_type": "large",
            "name": "백엔드",
            "parent_id": None,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    # 대분류가 부모를 가질때
    def test_fail_when_large_has_parent(self) -> None:
        parent = QuestionCategory.objects.create(name="백엔드", parent=None)

        payload = {
            "category_type": "large",
            "name": "프론트엔드",
            "parent_id": parent.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error_detail"],
            "대분류는 parent_id를 가질 수 없습니다.",
        )

    # 중분류의 부모가 대분류가 아닐때
    def test_fail_when_middle_parent_depth_invalid(self) -> None:
        large = QuestionCategory.objects.create(name="백엔드", parent=None)
        middle = QuestionCategory.objects.create(name="프레임워크", parent=large)

        payload = {
            "category_type": "middle",
            "name": "Django",
            "parent_id": middle.id,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error_detail"],
            "중분류의 부모는 대분류여야 합니다.",
        )

    # 이름이 비어있을때
    def test_fail_when_name_is_only_spaces(self) -> None:
        payload = {
            "category_type": "large",
            "name": "   ",
            "parent_id": None,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error_detail"],
            "카테고리 종류와 이름은 필수 입력값입니다.",
        )
