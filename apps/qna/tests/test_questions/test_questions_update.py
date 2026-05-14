from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.question_models import Question, QuestionCategory, QuestionImage
from apps.users.models import User


class QuestionUpdateAPIViewTest(APITestCase):
    """PUT /api/v1/qna/questions/{question_id} - 질문 수정 API 테스트"""

    # ── 클래스 레벨 타입 어노테이션 ──────────────────────────────────
    student_user: User
    other_student: User
    general_user: User
    large_category: QuestionCategory
    medium_category: QuestionCategory
    small_category: QuestionCategory
    small_category2: QuestionCategory
    question: Question
    other_question: Question
    question_img1: QuestionImage

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

        # 다른 학생 유저
        cls.other_student = User.objects.create_user(
            email="other@test.com",
            password="password123!",
            name="다른학생",
            nickname="학생2",
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

        # 카테고리 생성 (대 > 중 > 소)
        cls.large_category = QuestionCategory.objects.create(name="백엔드", parent=None)
        cls.medium_category = QuestionCategory.objects.create(name="Django", parent=cls.large_category)
        cls.small_category = QuestionCategory.objects.create(name="ORM", parent=cls.medium_category)
        cls.small_category2 = QuestionCategory.objects.create(name="View", parent=cls.medium_category)

        # 질문 생성 (본인 작성)
        cls.question = Question.objects.create(
            author=cls.student_user,
            category=cls.small_category,
            title="Django ORM 질문",
            content="ORM 사용법이 궁금합니다.",
        )

        # 질문 이미지
        cls.question_img1 = QuestionImage.objects.create(
            question=cls.question, img_url="http://example.com/old_img.jpg"
        )

        # 다른 사람이 작성한 질문
        cls.other_question = Question.objects.create(
            author=cls.other_student,
            category=cls.small_category,
            title="다른 사람 질문",
            content="다른 사람이 작성한 질문입니다.",
        )

    def setUp(self) -> None:
        self.client = APIClient()

    # ── 정상 케이스 ──────────────────────────────────────────────────

    def test_질문_수정_성공(self) -> None:
        """본인이 작성한 질문 수정 성공"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        data = {
            "title": "Django ORM 역참조 질문 (수정)",
            "content": "related_name을 어떻게 사용하나요?",
            "category_id": self.small_category2.id,  # 카테고리 변경
            "img_urls": ["http://example.com/new_img1.jpg", "http://example.com/new_img2.jpg"],
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(response_data["question_id"], self.question.id)
        self.assertIn("updated_at", response_data)

        # DB 확인
        self.question.refresh_from_db()
        self.assertEqual(self.question.title, "Django ORM 역참조 질문 (수정)")
        self.assertEqual(self.question.content, "related_name을 어떻게 사용하나요?")
        self.assertEqual(self.question.category_id, self.small_category2.id)

        # 이미지 확인
        images = list(self.question.questionimage_set.values_list("img_url", flat=True))
        self.assertEqual(len(images), 2)
        self.assertIn("http://example.com/new_img1.jpg", images)
        self.assertIn("http://example.com/new_img2.jpg", images)

    def test_이미지_없이_수정(self) -> None:
        """이미지 없이 질문 수정"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        data = {
            "title": "수정된 제목",
            "content": "수정된 내용",
            "category_id": self.small_category.id,
            "img_urls": [],  # 이미지 없음
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 기존 이미지 삭제 확인
        self.question.refresh_from_db()
        self.assertEqual(self.question.questionimage_set.count(), 0)

    def test_카테고리만_변경(self) -> None:
        """카테고리만 변경"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        data = {
            "title": self.question.title,
            "content": self.question.content,
            "category_id": self.small_category2.id,  # 카테고리만 변경
            "img_urls": [],
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.question.refresh_from_db()
        self.assertEqual(self.question.category_id, self.small_category2.id)

    # ── 에러 케이스 ──────────────────────────────────────────────────

    def test_존재하지_않는_질문_수정_404(self) -> None:
        """존재하지 않는 질문 수정 시 404"""
        self.client.force_authenticate(user=self.student_user)
        url = "/api/v1/qna/questions/99999"

        data = {
            "title": "수정",
            "content": "수정",
            "category_id": self.small_category.id,
            "img_urls": [],
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error_detail"], "해당 질문을 찾을 수 없습니다.")

    def test_다른_사람_질문_수정_403(self) -> None:
        """다른 사람이 작성한 질문 수정 시 403"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.other_question.id}"

        data = {
            "title": "수정 시도",
            "content": "수정 시도",
            "category_id": self.small_category.id,
            "img_urls": [],
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["error_detail"], "본인이 작성한 질문만 수정할 수 있습니다.")

    def test_존재하지_않는_카테고리_400(self) -> None:
        """존재하지 않는 카테고리로 수정 시 400"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        data = {
            "title": "수정",
            "content": "수정",
            "category_id": 99999,  # 존재하지 않는 카테고리
            "img_urls": [],
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error_detail"], "존재하지 않는 카테고리입니다.")

    def test_대분류_카테고리_선택_400(self) -> None:
        """대분류 카테고리 선택 시 400 (소분류만 가능)"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        data = {
            "title": "수정",
            "content": "수정",
            "category_id": self.large_category.id,  # 대분류
            "img_urls": [],
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error_detail"], "소분류 카테고리만 선택할 수 있습니다.")

    def test_중분류_카테고리_선택_400(self) -> None:
        """중분류 카테고리 선택 시 400 (소분류만 가능)"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        data = {
            "title": "수정",
            "content": "수정",
            "category_id": self.medium_category.id,  # 중분류
            "img_urls": [],
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error_detail"], "소분류 카테고리만 선택할 수 있습니다.")

    def test_필수_필드_누락_400(self) -> None:
        """필수 필드 누락 시 400"""
        self.client.force_authenticate(user=self.student_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        data = {
            "title": "수정",
            # content 누락
            "category_id": self.small_category.id,
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_유효하지_않은_question_id_400(self) -> None:
        """유효하지 않은 question_id로 수정 시 400"""
        self.client.force_authenticate(user=self.student_user)
        url = "/api/v1/qna/questions/0"

        data = {
            "title": "수정",
            "content": "수정",
            "category_id": self.small_category.id,
            "img_urls": [],
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error_detail"], "유효하지 않은 질문 수정 요청입니다.")

    # ── 권한 테스트 ──────────────────────────────────────────────────

    def test_비로그인_사용자_수정_불가_401(self) -> None:
        """로그인하지 않은 사용자는 수정 불가"""
        url = f"/api/v1/qna/questions/{self.question.id}"

        data = {
            "title": "수정",
            "content": "수정",
            "category_id": self.small_category.id,
            "img_urls": [],
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_GENERAL_권한_사용자_수정_불가_403(self) -> None:
        """GENERAL 권한 사용자는 수정 불가"""
        self.client.force_authenticate(user=self.general_user)
        url = f"/api/v1/qna/questions/{self.question.id}"

        data = {
            "title": "수정",
            "content": "수정",
            "category_id": self.small_category.id,
            "img_urls": [],
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
