from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.answer_models import Answer
from apps.qna.models.question_models import Question, QuestionCategory
from apps.users.models import User

URL = "/api/v1/admin/qna/questions"


class AdminQuestionListAPIViewTest(APITestCase):
    """GET /api/v1/admin/qna/questions - 어드민 질의응답 목록 조회 API 테스트"""

    # ── 클래스 레벨 타입 어노테이션 ──────────────────────────────────
    admin_user: User
    student_user: User
    general_user: User
    large_category: QuestionCategory
    medium_category: QuestionCategory
    small_category: QuestionCategory
    small_category2: QuestionCategory
    question1: Question
    question2: Question
    question3: Question

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="password123!",
            name="관리자",
            nickname="ad_nick",
            phone_number="010-1111-1111",
            gender="male",
            birthday="1990-01-01",
            role="ADMIN",
            is_active=True,
        )
        cls.student_user = User.objects.create_user(
            email="student@test.com",
            password="password123!",
            name="수강생",
            nickname="st_nick",
            phone_number="010-2222-2222",
            gender="female",
            birthday="2000-01-01",
            role="STUDENT",
            is_active=True,
        )
        cls.general_user = User.objects.create_user(
            email="general@test.com",
            password="password123!",
            name="일반유저",
            nickname="ge_nick",
            phone_number="010-3333-3333",
            gender="male",
            birthday="1995-01-01",
            role="GENERAL",
            is_active=True,
        )

        cls.large_category = QuestionCategory.objects.create(name="백엔드", parent=None)
        cls.medium_category = QuestionCategory.objects.create(name="웹프레임워크", parent=cls.large_category)
        cls.small_category = QuestionCategory.objects.create(name="Django", parent=cls.medium_category)
        cls.small_category2 = QuestionCategory.objects.create(name="FastAPI", parent=cls.medium_category)

        cls.question1 = Question.objects.create(
            author=cls.student_user,
            category=cls.small_category,
            title="Django ORM 질문",
            content="Django ORM에서 select_related와 prefetch_related 차이가 궁금합니다.",
            view_count=10,
        )
        cls.question2 = Question.objects.create(
            author=cls.student_user,
            category=cls.small_category,
            title="Django 마이그레이션 질문",
            content="마이그레이션 충돌 해결 방법이 궁금합니다.",
            view_count=5,
        )
        cls.question3 = Question.objects.create(
            author=cls.student_user,
            category=cls.small_category2,
            title="FastAPI 의존성 주입 질문",
            content="FastAPI에서 Depends를 활용하는 방법이 궁금합니다.",
            view_count=20,
        )

        # question1에 답변 추가
        Answer.objects.create(
            author=cls.admin_user,
            question=cls.question1,
            content="답변입니다.",
        )

    def setUp(self) -> None:
        self.client = APIClient()

    def _force_login(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    # ── 성공 케이스 ─────────────────────────────────────────────────

    def test_어드민_목록_조회_성공_기본(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("page", response.data)
        self.assertIn("page_size", response.data)
        self.assertIn("total_count", response.data)
        self.assertIn("questions", response.data)

    def test_응답_필드_검증(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data["questions"][0]
        for field in [
            "question_id",
            "title",
            "category_path",
            "content_preview",
            "nickname",
            "view_count",
            "has_answer",
            "created_at",
            "updated_at",
        ]:
            self.assertIn(field, item)

    def test_category_path_문자열_형식(self) -> None:
        """category_path가 '대 > 중 > 소' 형태로 반환"""
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"category_id": self.small_category.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = next(q for q in response.data["questions"] if q["question_id"] == self.question1.id)
        self.assertEqual(item["category_path"], "백엔드 > 웹프레임워크 > Django")

    def test_has_answer_답변_있음(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"category_id": self.small_category.id})

        item = next(q for q in response.data["questions"] if q["question_id"] == self.question1.id)
        self.assertTrue(item["has_answer"])

    def test_has_answer_답변_없음(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"category_id": self.small_category.id})

        item = next(q for q in response.data["questions"] if q["question_id"] == self.question2.id)
        self.assertFalse(item["has_answer"])

    def test_content_preview_100자_잘림(self) -> None:
        long_content = "A" * 200
        question = Question.objects.create(
            author=self.student_user,
            category=self.small_category,
            title="긴 내용 질문",
            content=long_content,
        )
        self._force_login(self.admin_user)

        response = self.client.get(URL)

        item = next(q for q in response.data["questions"] if q["question_id"] == question.id)
        self.assertEqual(len(item["content_preview"]), 100)

    # ── 페이지네이션 ─────────────────────────────────────────────────

    def test_기본_page_size_20(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL)

        self.assertEqual(response.data["page_size"], 20)

    def test_page_size_적용(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"page": 1, "page_size": 2})

        self.assertEqual(len(response.data["questions"]), 2)

    def test_total_count_반환(self) -> None:
        self._force_login(self.admin_user)
        total = Question.objects.count()

        response = self.client.get(URL)

        self.assertEqual(response.data["total_count"], total)

    # ── 검색 필터 ────────────────────────────────────────────────────

    def test_search_keyword_제목_검색(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"search_keyword": "ORM"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [q["question_id"] for q in response.data["questions"]]
        self.assertIn(self.question1.id, ids)
        self.assertNotIn(self.question2.id, ids)
        self.assertNotIn(self.question3.id, ids)

    def test_search_keyword_결과_없으면_빈_리스트(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"search_keyword": "존재하지않는키워드xyz"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_count"], 0)
        self.assertEqual(response.data["questions"], [])

    # ── 카테고리 필터 ────────────────────────────────────────────────

    def test_category_id_소분류_필터(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"category_id": self.small_category.id})

        ids = [q["question_id"] for q in response.data["questions"]]
        self.assertIn(self.question1.id, ids)
        self.assertIn(self.question2.id, ids)
        self.assertNotIn(self.question3.id, ids)

    def test_category_id_중분류_필터_하위_포함(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"category_id": self.medium_category.id})

        ids = [q["question_id"] for q in response.data["questions"]]
        self.assertIn(self.question1.id, ids)
        self.assertIn(self.question2.id, ids)
        self.assertIn(self.question3.id, ids)

    # ── 답변 상태 필터 ───────────────────────────────────────────────

    def test_answer_status_Y_필터(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"answer_status": "Y"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [q["question_id"] for q in response.data["questions"]]
        self.assertIn(self.question1.id, ids)
        self.assertNotIn(self.question2.id, ids)

    def test_answer_status_N_필터(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"answer_status": "N"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for q in response.data["questions"]:
            self.assertFalse(q["has_answer"])

    def test_answer_status_잘못된_값_400(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"answer_status": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    # ── 정렬 ─────────────────────────────────────────────────────────

    def test_sort_latest_최신순(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"sort": "latest"})

        ids = [q["question_id"] for q in response.data["questions"]]
        self.assertEqual(ids[0], self.question3.id)

    def test_sort_oldest_오래된순(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"sort": "oldest"})

        ids = [q["question_id"] for q in response.data["questions"]]
        self.assertEqual(ids[0], self.question1.id)

    def test_sort_views_조회수순(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"sort": "views"})

        ids = [q["question_id"] for q in response.data["questions"]]
        self.assertEqual(ids[0], self.question3.id)

    def test_sort_잘못된_값_400(self) -> None:
        self._force_login(self.admin_user)

        response = self.client.get(URL, {"sort": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    # ── 인증/권한 에러 케이스 ────────────────────────────────────────

    def test_비로그인_401(self) -> None:
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_권한_403(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_general_권한_403(self) -> None:
        self._force_login(self.general_user)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
