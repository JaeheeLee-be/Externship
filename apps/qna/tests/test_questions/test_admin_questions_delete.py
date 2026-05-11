from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.answer_models import Answer, AnswerComment
from apps.qna.models.question_models import Question, QuestionCategory, QuestionImage
from apps.users.models import User


class AdminQuestionDeleteAPIViewTest(APITestCase):
    """DELETE /api/v1/admin/qna/questions/{question_id} - 어드민 질문 삭제 API 테스트"""

    # 타입 어노테이션
    admin_user: User
    student_user: User
    general_user: User
    large_category: QuestionCategory
    medium_category: QuestionCategory
    small_category: QuestionCategory
    question: Question
    question_img1: QuestionImage
    answer1: Answer
    answer2: Answer
    comment1: AnswerComment
    comment2: AnswerComment
    comment3: AnswerComment

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
            title="Django ORM 질문",
            content="ORM 관련 질문입니다.",
        )

        # 질문 이미지
        cls.question_img1 = QuestionImage.objects.create(question=cls.question, img_url="https://example.com/img1.jpg")

        # 답변 생성
        cls.answer1 = Answer.objects.create(
            author=cls.admin_user,
            question=cls.question,
            content="첫 번째 답변입니다.",
            is_adopted=True,
        )

        cls.answer2 = Answer.objects.create(
            author=cls.student_user,
            question=cls.question,
            content="두 번째 답변입니다.",
            is_adopted=False,
        )

        # 댓글 생성
        cls.comment1 = AnswerComment.objects.create(
            author=cls.student_user,
            answer=cls.answer1,
            content="첫 번째 답변의 댓글 1",
        )

        cls.comment2 = AnswerComment.objects.create(
            author=cls.admin_user,
            answer=cls.answer1,
            content="첫 번째 답변의 댓글 2",
        )

        cls.comment3 = AnswerComment.objects.create(
            author=cls.student_user,
            answer=cls.answer2,
            content="두 번째 답변의 댓글 1",
        )

    def setUp(self) -> None:
        self.client = APIClient()

    # ── 정상 케이스 ──────────────────────────────────────────────────

    def test_어드민_질문_삭제_성공(self) -> None:
        """어드민 질문 삭제 성공"""
        self.client.force_authenticate(user=self.admin_user)
        url = f"/api/v1/admin/qna/questions/{self.question.id}"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # 응답 확인
        self.assertEqual(data["question_id"], self.question.id)
        self.assertEqual(data["deleted_answer_count"], 2)
        self.assertEqual(data["deleted_comment_count"], 3)

        # 실제 삭제 확인
        self.assertFalse(Question.objects.filter(id=self.question.id).exists())
        self.assertFalse(Answer.objects.filter(question_id=self.question.id).exists())
        self.assertFalse(QuestionImage.objects.filter(question_id=self.question.id).exists())
        self.assertFalse(AnswerComment.objects.filter(answer__question_id=self.question.id).exists())

    def test_답변_없는_질문_삭제(self) -> None:
        """답변이 없는 질문 삭제"""
        question_no_answer = Question.objects.create(
            author=self.student_user,
            category=self.small_category,
            title="답변 없는 질문",
            content="답변이 없습니다.",
        )

        self.client.force_authenticate(user=self.admin_user)
        url = f"/api/v1/admin/qna/questions/{question_no_answer.id}"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["deleted_answer_count"], 0)
        self.assertEqual(data["deleted_comment_count"], 0)
        self.assertFalse(Question.objects.filter(id=question_no_answer.id).exists())

    def test_댓글_없는_질문_삭제(self) -> None:
        """댓글이 없는 질문 삭제"""
        question_no_comment = Question.objects.create(
            author=self.student_user,
            category=self.small_category,
            title="댓글 없는 질문",
            content="댓글이 없습니다.",
        )

        answer_no_comment = Answer.objects.create(
            author=self.admin_user,
            question=question_no_comment,
            content="댓글 없는 답변",
        )

        self.client.force_authenticate(user=self.admin_user)
        url = f"/api/v1/admin/qna/questions/{question_no_comment.id}"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data["deleted_answer_count"], 1)
        self.assertEqual(data["deleted_comment_count"], 0)

    # ── 에러 케이스 ──────────────────────────────────────────────────

    def test_존재하지_않는_질문_삭제_404(self) -> None:
        """존재하지 않는 질문 삭제 시 404"""
        self.client.force_authenticate(user=self.admin_user)
        url = "/api/v1/admin/qna/questions/99999"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error_detail"], "삭제할 질문을 찾을 수 없습니다.")

    def test_유효하지_않은_question_id_400(self) -> None:
        """유효하지 않은 question_id 400"""
        self.client.force_authenticate(user=self.admin_user)
        url = "/api/v1/admin/qna/questions/0"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error_detail"], "유효하지 않은 삭제 요청입니다.")

    # ── 권한 테스트 ──────────────────────────────────────────────────

    def test_비로그인_사용자_401(self) -> None:
        """비로그인 사용자 접근 불가"""
        url = f"/api/v1/admin/qna/questions/{self.question.id}"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 삭제되지 않았는지 확인
        self.assertTrue(Question.objects.filter(id=self.question.id).exists())

    def test_STUDENT_권한_사용자_403(self) -> None:
        """STUDENT 권한 사용자 접근 불가"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/admin/qna/questions/{self.question.id}"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 삭제되지 않았는지 확인
        self.assertTrue(Question.objects.filter(id=self.question.id).exists())

    def test_GENERAL_권한_사용자_403(self) -> None:
        """GENERAL 권한 사용자 접근 불가"""
        self.client.force_authenticate(user=self.general_user)
        url = f"/api/v1/admin/qna/questions/{self.question.id}"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 삭제되지 않았는지 확인
        self.assertTrue(Question.objects.filter(id=self.question.id).exists())

    def test_CASCADE_삭제_확인(self) -> None:
        """질문 삭제 시 연관 데이터 모두 삭제되는지 확인"""
        # 삭제 전 개수 확인
        question_id = self.question.id
        self.assertEqual(Answer.objects.filter(question_id=question_id).count(), 2)
        self.assertEqual(QuestionImage.objects.filter(question_id=question_id).count(), 1)
        self.assertEqual(
            AnswerComment.objects.filter(answer__question_id=question_id).count(),
            3,
        )

        self.client.force_authenticate(user=self.admin_user)
        url = f"/api/v1/admin/qna/questions/{question_id}"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # CASCADE로 모두 삭제되었는지 확인
        self.assertEqual(Question.objects.filter(id=question_id).count(), 0)
        self.assertEqual(Answer.objects.filter(question_id=question_id).count(), 0)
        self.assertEqual(QuestionImage.objects.filter(question_id=question_id).count(), 0)
        self.assertEqual(
            AnswerComment.objects.filter(answer__question_id=question_id).count(),
            0,
        )
