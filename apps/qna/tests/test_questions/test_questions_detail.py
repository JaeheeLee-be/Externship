from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.answer_models import Answer, AnswerComment
from apps.qna.models.question_models import Question, QuestionCategory, QuestionImage
from apps.users.models import User


class QuestionDetailAPIViewTest(APITestCase):
    """GET /api/v1/qna/questions/{question_id} - 질문 상세 조회 API 테스트"""

    # ── 클래스 레벨 타입 어노테이션 ──────────────────────────────────
    student_user: User
    admin_user: User
    general_user: User
    large_category: QuestionCategory
    medium_category: QuestionCategory
    small_category: QuestionCategory
    question: Question
    question_img1: QuestionImage
    question_img2: QuestionImage
    answer1: Answer
    answer2: Answer
    comment1: AnswerComment
    comment2: AnswerComment

    @classmethod
    def setUpTestData(cls) -> None:
        # 학생 유저 생성
        cls.student_user = User.objects.create_user(
            email="student@test.com",
            password="password123!",
            name="학생",
            nickname="학생1",
            phone_number="010-1111-1111",
            gender="male",
            birthday="2000-01-01",
            role="STUDENT",
            is_active=True,
        )

        # 어드민 유저 생성
        cls.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="password123!",
            name="어드민",
            nickname="관리자",
            phone_number="010-2222-2222",
            gender="female",
            birthday="1990-01-01",
            role="ADMIN",
            is_active=True,
        )

        # 일반 유저 생성
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

        # 카테고리 생성 (대 > 중 > 소)
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

        # 질문 이미지 생성
        cls.question_img1 = QuestionImage.objects.create(
            question=cls.question, img_url="http://example.com/question_img1.jpg"
        )
        cls.question_img2 = QuestionImage.objects.create(
            question=cls.question, img_url="http://example.com/question_img2.jpg"
        )

        # 답변 생성 (채택된 답변)
        cls.answer1 = Answer.objects.create(
            author=cls.admin_user,
            question=cls.question,
            content="related_name을 사용하면 역참조가 가능합니다.",
            is_adopted=True,
        )

        # 답변 생성 (채택 안된 답변)
        cls.answer2 = Answer.objects.create(
            author=cls.student_user,
            question=cls.question,
            content="추가 답변입니다.",
            is_adopted=False,
        )

        # 댓글 생성
        cls.comment1 = AnswerComment.objects.create(
            author=cls.student_user,
            answer=cls.answer1,
            content="답변 감사합니다!",
        )

        cls.comment2 = AnswerComment.objects.create(
            author=cls.admin_user,
            answer=cls.answer1,
            content="추가 설명입니다.",
        )

    def setUp(self) -> None:
        self.client = APIClient()

    # ── 정상 케이스 ──────────────────────────────────────────────────

    def test_질문_상세_조회_성공(self) -> None:
        """질문 상세 조회 성공"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # 기본 정보 검증
        self.assertEqual(data["id"], self.question.id)
        self.assertEqual(data["title"], "Django ORM 역참조 질문")
        self.assertEqual(data["content"], "ForeignKey에서 related_name을 어떻게 사용하나요?")
        self.assertEqual(data["view_count"], 11)  # 조회수 1 증가

        # 카테고리 정보 검증
        self.assertEqual(data["category"]["id"], self.small_category.id)
        self.assertEqual(data["category"]["depth"], 3)
        self.assertEqual(data["category"]["names"], ["백엔드", "Django", "ORM"])

        # 작성자 정보 검증
        self.assertEqual(data["author"]["id"], self.student_user.id)
        self.assertEqual(data["author"]["nickname"], "학생1")

        # 이미지 검증
        self.assertEqual(len(data["images"]), 2)
        img_urls = [img["img_url"] for img in data["images"]]
        self.assertIn("http://example.com/question_img1.jpg", img_urls)
        self.assertIn("http://example.com/question_img2.jpg", img_urls)

        # 답변 검증
        self.assertEqual(len(data["answers"]), 2)

    def test_조회수_증가_확인(self) -> None:
        """질문 조회 시 조회수가 1 증가하는지 확인"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        initial_view_count = self.question.view_count

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["view_count"], initial_view_count + 1)

        # DB에서 직접 확인
        self.question.refresh_from_db()
        self.assertEqual(self.question.view_count, initial_view_count + 1)

    def test_답변_정렬_순서_채택순_작성일순(self) -> None:
        """채택된 답변이 먼저 나오고, 그 다음은 작성일시 순"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # 첫 번째 답변은 채택된 답변
        self.assertTrue(data["answers"][0]["is_adopted"])
        self.assertEqual(data["answers"][0]["id"], self.answer1.id)

        # 두 번째 답변은 채택되지 않은 답변
        self.assertFalse(data["answers"][1]["is_adopted"])
        self.assertEqual(data["answers"][1]["id"], self.answer2.id)

    def test_댓글_정보_포함_확인(self) -> None:
        """답변에 댓글 정보가 포함되는지 확인"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # 첫 번째 답변의 댓글 검증
        comments = data["answers"][0]["comments"]
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0]["content"], "답변 감사합니다!")
        self.assertEqual(comments[0]["author"]["nickname"], "학생1")

    def test_이미지가_없는_질문_조회(self) -> None:
        """이미지가 없는 질문도 정상 조회"""
        question_no_img = Question.objects.create(
            author=self.student_user,
            category=self.small_category,
            title="이미지 없는 질문",
            content="이미지가 없습니다.",
        )

        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{question_no_img.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data["images"]), 0)

    def test_답변이_없는_질문_조회(self) -> None:
        """답변이 없는 질문도 정상 조회"""
        question_no_answer = Question.objects.create(
            author=self.student_user,
            category=self.small_category,
            title="답변 없는 질문",
            content="답변이 없습니다.",
        )

        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{question_no_answer.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data["answers"]), 0)

    # ── 에러 케이스 ──────────────────────────────────────────────────

    def test_존재하지_않는_질문_조회_404(self) -> None:
        """존재하지 않는 질문 조회 시 404 에러"""
        self.client.force_authenticate(user=self.student_user)
        url = "/api/v1/qna/questions/99999"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error_detail"], "해당 질문을 찾을 수 없습니다.")

    def test_유효하지_않은_질문ID_400(self) -> None:
        """유효하지 않은 질문 ID로 조회 시 400 에러"""
        self.client.force_authenticate(user=self.student_user)
        url = "/api/v1/qna/questions/0"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error_detail"], "유효하지 않은 질문 상세 조회 요청입니다.")

    # ── 권한 테스트 ──────────────────────────────────────────────────

    def test_비로그인_사용자_접근_불가_401(self) -> None:
        """로그인하지 않은 사용자는 접근 불가"""
        url = f"/api/v1/qna/questions/{self.question.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_GENERAL_권한_사용자_접근_불가_403(self) -> None:
        """GENERAL 권한 사용자는 접근 불가"""
        self.client.force_authenticate(user=self.general_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ADMIN_권한_사용자_접근_가능(self) -> None:
        """ADMIN 권한 사용자는 접근 가능"""
        self.client.force_authenticate(user=self.admin_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
