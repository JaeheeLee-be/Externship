from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.answer_models import Answer
from apps.qna.models.question_models import Question, QuestionCategory, QuestionImage
from apps.users.models import CohortStudents, User


class AdminQuestionDetailAPIViewTest(APITestCase):
    """GET /api/v1/admin/qna/questions/{question_id} - 어드민 질문 상세 조회 API 테스트"""

    # 타입 어노테이션
    admin_user: User
    student_user: User
    general_user: User
    large_category: QuestionCategory
    medium_category: QuestionCategory
    small_category: QuestionCategory
    question: Question
    question_img1: QuestionImage
    question_img2: QuestionImage
    answer1: Answer
    answer2: Answer

    @classmethod
    def setUpTestData(cls) -> None:
        # 어드민 유저
        cls.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="password123!",
            name="어드민",
            nickname="관리자",
            phone_number="010-1111-1111",
            gender="male",
            birthday="1990-01-01",
            role="ADMIN",
            is_active=True,
        )

        # 학생 유저
        cls.student_user = User.objects.create_user(
            email="student@test.com",
            password="password123!",
            name="학생",
            nickname="학생1",
            phone_number="010-2222-2222",
            gender="female",
            birthday="2000-01-01",
            role="STUDENT",
            is_active=True,
        )

        # 일반 유저
        cls.general_user = User.objects.create_user(
            email="general@test.com",
            password="password123!",
            name="일반유저",
            nickname="일반인",
            phone_number="010-3333-3333",
            gender="male",
            birthday="1995-01-01",
            role="GENERAL",
            is_active=True,
        )

        # 카테고리 생성
        cls.large_category = QuestionCategory.objects.create(name="백엔드", parent=None)
        cls.medium_category = QuestionCategory.objects.create(name="Django", parent=cls.large_category)
        cls.small_category = QuestionCategory.objects.create(name="ORM", parent=cls.medium_category)

        # 질문 생성
        cls.question = Question.objects.create(
            author=cls.student_user,
            category=cls.small_category,
            title="Django ORM 역참조 질문",
            content="ForeignKey에서 related_name을 어떻게 사용하나요?",
            view_count=10,
        )

        # 질문 이미지
        cls.question_img1 = QuestionImage.objects.create(question=cls.question, img_url="https://example.com/img1.jpg")
        cls.question_img2 = QuestionImage.objects.create(question=cls.question, img_url="https://example.com/img2.jpg")

        # 답변 생성
        cls.answer1 = Answer.objects.create(
            author=cls.admin_user,
            question=cls.question,
            content="related_name을 사용하면 역참조가 가능합니다.",
            is_adopted=True,
        )

        cls.answer2 = Answer.objects.create(
            author=cls.student_user,
            question=cls.question,
            content="추가 답변입니다.",
            is_adopted=False,
        )

    def setUp(self) -> None:
        self.client = APIClient()

    # ── 정상 케이스 ──────────────────────────────────────────────────

    def test_어드민_질문_상세_조회_성공(self) -> None:
        """어드민 질문 상세 조회 성공"""
        self.client.force_authenticate(user=self.admin_user)
        url = f"/api/v1/admin/qna/questions/{self.question.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # 기본 정보
        self.assertEqual(data["question_id"], self.question.id)
        self.assertEqual(data["title"], "Django ORM 역참조 질문")
        self.assertEqual(data["content"], "ForeignKey에서 related_name을 어떻게 사용하나요?")
        self.assertEqual(data["view_count"], 10)

        # 이미지 (URL만)
        self.assertEqual(len(data["images"]), 2)
        self.assertIn("https://example.com/img1.jpg", data["images"])
        self.assertIn("https://example.com/img2.jpg", data["images"])

        # 작성자 정보
        self.assertEqual(data["author"]["nickname"], "학생1")
        self.assertIn("profile_img_url", data["author"])
        self.assertIn("course_generation", data["author"])

        # has_answer
        self.assertTrue(data["has_answer"])

        # created_at, updated_at 존재
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

        # 답변 정보
        self.assertEqual(len(data["answers"]), 2)
        self.assertEqual(data["answers"][0]["answer_id"], self.answer1.id)
        self.assertTrue(data["answers"][0]["is_adopted"])

        # 답변 작성자 정보
        answer_author = data["answers"][0]["author"]
        self.assertIn("profile_img_url", answer_author)
        self.assertIn("nickname", answer_author)
        self.assertIn("role_title", answer_author)
        self.assertIn("course_generation", answer_author)

    def test_답변_없는_질문_조회(self) -> None:
        """답변이 없는 질문 조회"""
        question_no_answer = Question.objects.create(
            author=self.student_user,
            category=self.small_category,
            title="답변 없는 질문",
            content="답변이 없습니다.",
        )

        self.client.force_authenticate(user=self.admin_user)
        url = f"/api/v1/admin/qna/questions/{question_no_answer.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertFalse(data["has_answer"])
        self.assertEqual(len(data["answers"]), 0)

    def test_이미지_없는_질문_조회(self) -> None:
        """이미지가 없는 질문 조회"""
        question_no_img = Question.objects.create(
            author=self.student_user,
            category=self.small_category,
            title="이미지 없는 질문",
            content="이미지가 없습니다.",
        )

        self.client.force_authenticate(user=self.admin_user)
        url = f"/api/v1/admin/qna/questions/{question_no_img.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data["images"]), 0)

    # ── 에러 케이스 ──────────────────────────────────────────────────

    def test_존재하지_않는_질문_404(self) -> None:
        """존재하지 않는 질문 조회 시 404"""
        self.client.force_authenticate(user=self.admin_user)
        url = "/api/v1/admin/qna/questions/99999"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error_detail"], "해당 질문을 찾을 수 없습니다.")

    def test_유효하지_않은_question_id_400(self) -> None:
        """유효하지 않은 question_id 400"""
        self.client.force_authenticate(user=self.admin_user)
        url = "/api/v1/admin/qna/questions/0"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error_detail"], "유효하지 않은 상세 조회 요청입니다.")

    # ── 권한 테스트 ──────────────────────────────────────────────────

    def test_비로그인_사용자_401(self) -> None:
        """비로그인 사용자 접근 불가"""
        url = f"/api/v1/admin/qna/questions/{self.question.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_STUDENT_권한_사용자_403(self) -> None:
        """STUDENT 권한 사용자 접근 불가"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/admin/qna/questions/{self.question.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_GENERAL_권한_사용자_403(self) -> None:
        """GENERAL 권한 사용자 접근 불가"""
        self.client.force_authenticate(user=self.general_user)
        url = f"/api/v1/admin/qna/questions/{self.question.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
