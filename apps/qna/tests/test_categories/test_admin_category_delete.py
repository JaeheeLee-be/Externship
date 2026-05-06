from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.question_models import Question, QuestionCategory
from apps.qna.services.admin_category_services import DEFAULT_CATEGORY_NAME
from apps.users.models import User


class AdminCategoryDeleteAPITest(APITestCase):
    # ── 클래스 레벨 타입 어노테이션 ──────────────────────────────────────────
    admin_user: User
    general_user: User

    # 카테고리 트리
    large: QuestionCategory  # 대분류: "백엔드"
    middle: QuestionCategory  # 중분류: "웹 프레임워크"
    small: QuestionCategory  # 소분류: "Django"
    large2: QuestionCategory  # 독립 대분류 (삭제 후 default 확인용)
    default_category: QuestionCategory  # 일반질문

    # 질문
    question_in_small: Question
    question_in_middle: Question
    question_in_large: Question

    @classmethod
    def setUpTestData(cls) -> None:
        # 유저 생성
        cls.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="password123!",
            name="관리자",
            nickname="admin",
            phone_number="010-0000-0001",
            gender="MALE",
            birthday="1990-01-01",
            role="ADMIN",
            is_active=True,
        )
        cls.general_user = User.objects.create_user(
            email="user@test.com",
            password="password123!",
            name="일반유저",
            nickname="user",
            phone_number="010-0000-0002",
            gender="FEMALE",
            birthday="1995-05-05",
            role="STUDENT",
            is_active=True,
        )

        # 기본 카테고리 (일반질문)
        cls.default_category = QuestionCategory.objects.create(name=DEFAULT_CATEGORY_NAME, parent=None)

        # 카테고리 트리 생성
        cls.large = QuestionCategory.objects.create(name="백엔드", parent=None)
        cls.middle = QuestionCategory.objects.create(name="웹 프레임워크", parent=cls.large)
        cls.small = QuestionCategory.objects.create(name="Django", parent=cls.middle)
        cls.large2 = QuestionCategory.objects.create(name="프론트엔드", parent=None)

        # 질문 생성 — 각 카테고리에 1개씩
        cls.question_in_small = Question.objects.create(
            author=cls.general_user,
            category=cls.small,
            title="소분류 질문",
            content="소분류에 속한 질문입니다.",
        )
        cls.question_in_middle = Question.objects.create(
            author=cls.general_user,
            category=cls.middle,
            title="중분류 질문",
            content="중분류에 속한 질문입니다.",
        )
        cls.question_in_large = Question.objects.create(
            author=cls.general_user,
            category=cls.large,
            title="대분류 질문",
            content="대분류에 속한 질문입니다.",
        )

    def setUp(self) -> None:
        self.client = APIClient()

    def _authenticate_admin(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

    def _authenticate_general(self) -> None:
        self.client.force_authenticate(user=self.general_user)

    def _delete_url(self, category_id: int) -> str:
        return reverse("admin-category-delete", kwargs={"category_id": category_id})

    # ── 정상 케이스 ──────────────────────────────────────────────────────────

    def test_소분류_삭제_성공(self) -> None:
        """소분류 삭제 시 해당 카테고리의 질문이 일반질문으로 이관되어야 한다."""
        # small 카테고리는 setUpTestData에서 생성했으나, 이 테스트에서 삭제됩니다.
        # 다른 테스트에 영향을 주지 않도록 테스트 전용 소분류를 별도 생성합니다.
        small_temp = QuestionCategory.objects.create(name="FastAPI", parent=self.middle)
        q = Question.objects.create(
            author=self.general_user,
            category=small_temp,
            title="FastAPI 질문",
            content="temp",
        )

        self._authenticate_admin()
        response = self.client.delete(self._delete_url(small_temp.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["category_id"], small_temp.id)
        self.assertEqual(data["category_type"], "small")
        self.assertEqual(data["migrated_question_count"], 1)

        # 카테고리가 실제로 삭제됐는지 확인
        self.assertFalse(QuestionCategory.objects.filter(id=small_temp.id).exists())

        # 질문이 일반질문 카테고리로 이관됐는지 확인
        q.refresh_from_db()
        self.assertEqual(q.category_id, self.default_category.id)

    def test_중분류_삭제_시_소분류와_질문_모두_이관(self) -> None:
        """중분류 삭제 시 하위 소분류도 함께 삭제되고 질문이 이관되어야 한다."""
        # 독립적인 중분류 트리 구성
        middle_temp = QuestionCategory.objects.create(name="DB", parent=self.large2)
        small_temp = QuestionCategory.objects.create(name="PostgreSQL", parent=middle_temp)
        q_mid = Question.objects.create(
            author=self.general_user,
            category=middle_temp,
            title="중분류 직속 질문",
            content="temp",
        )
        q_small = Question.objects.create(
            author=self.general_user,
            category=small_temp,
            title="소분류 질문",
            content="temp",
        )

        self._authenticate_admin()
        response = self.client.delete(self._delete_url(middle_temp.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["category_id"], middle_temp.id)
        self.assertEqual(data["category_type"], "middle")
        self.assertEqual(data["migrated_question_count"], 2)

        # 중분류, 소분류 모두 삭제됐는지 확인
        self.assertFalse(QuestionCategory.objects.filter(id=middle_temp.id).exists())
        self.assertFalse(QuestionCategory.objects.filter(id=small_temp.id).exists())

        # 질문 이관 확인
        q_mid.refresh_from_db()
        q_small.refresh_from_db()
        self.assertEqual(q_mid.category_id, self.default_category.id)
        self.assertEqual(q_small.category_id, self.default_category.id)

    def test_대분류_삭제_시_하위_전체와_질문_모두_이관(self) -> None:
        """대분류 삭제 시 중분류·소분류 전체 삭제, 모든 질문이 이관되어야 한다."""
        # 독립적인 3depth 트리 구성
        large_temp = QuestionCategory.objects.create(name="데이터사이언스", parent=None)
        middle_temp = QuestionCategory.objects.create(name="ML", parent=large_temp)
        small_temp = QuestionCategory.objects.create(name="PyTorch", parent=middle_temp)
        q1 = Question.objects.create(author=self.general_user, category=large_temp, title="대분류 질문", content="temp")
        q2 = Question.objects.create(
            author=self.general_user, category=middle_temp, title="중분류 질문", content="temp"
        )
        q3 = Question.objects.create(author=self.general_user, category=small_temp, title="소분류 질문", content="temp")

        self._authenticate_admin()
        response = self.client.delete(self._delete_url(large_temp.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["category_type"], "large")
        self.assertEqual(data["migrated_question_count"], 3)

        for cat_id in [large_temp.id, middle_temp.id, small_temp.id]:
            self.assertFalse(QuestionCategory.objects.filter(id=cat_id).exists())

        for q in [q1, q2, q3]:
            q.refresh_from_db()
            self.assertEqual(q.category_id, self.default_category.id)

    def test_질문_없는_카테고리_삭제_성공(self) -> None:
        """질문이 없는 카테고리도 정상 삭제되어야 하고 migrated_question_count는 0이어야 한다."""
        empty_cat = QuestionCategory.objects.create(name="빈카테고리", parent=None)

        self._authenticate_admin()
        response = self.client.delete(self._delete_url(empty_cat.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["migrated_question_count"], 0)
        self.assertFalse(QuestionCategory.objects.filter(id=empty_cat.id).exists())

    def test_비로그인_401(self) -> None:
        """비로그인 요청은 401을 반환해야 한다."""
        response = self.client.delete(self._delete_url(self.small.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_권한없는_유저_403(self) -> None:
        """ADMIN이 아닌 유저의 삭제 요청은 403을 반환해야 한다."""
        self._authenticate_general()
        response = self.client.delete(self._delete_url(self.small.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.json())

    def test_존재하지_않는_카테고리_404(self) -> None:
        """존재하지 않는 category_id로 요청하면 404를 반환해야 한다."""
        self._authenticate_admin()
        response = self.client.delete(self._delete_url(99999999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error_detail"], "해당 카테고리를 찾을 수 없습니다.")

    def test_기본_카테고리_삭제_불가_409(self) -> None:
        """'일반질문' 기본 카테고리는 삭제할 수 없어야 한다."""
        self._authenticate_admin()
        response = self.client.delete(self._delete_url(self.default_category.id))
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.json()["error_detail"], "기본 카테고리는 삭제할 수 없습니다.")

    def test_응답_필드_확인(self) -> None:
        """성공 응답에 category_id, category_type, migrated_question_count 필드가 있어야 한다."""
        temp = QuestionCategory.objects.create(name="응답검증용", parent=None)

        self._authenticate_admin()
        response = self.client.delete(self._delete_url(temp.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("category_id", data)
        self.assertIn("category_type", data)
        self.assertIn("migrated_question_count", data)
        self.assertEqual(data["category_id"], temp.id)
