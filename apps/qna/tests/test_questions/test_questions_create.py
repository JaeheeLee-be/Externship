from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.question_models import Question, QuestionCategory, QuestionImage
from apps.users.models import User

URL = "/api/v1/qna/questions"


class QuestionCreateAPIViewTest(APITestCase):
    """POST /api/v1/qna/questions - 질문 등록 API 테스트"""

    # ── 클래스 레벨 타입 어노테이션 ──────────────────────────────────
    student_user: User
    admin_user: User
    general_user: User
    large_category: QuestionCategory
    small_category: QuestionCategory

    @classmethod
    def setUpTestData(cls) -> None:
        # 읽기 전용 DB 데이터 - 클래스당 1번만 INSERT
        cls.student_user = User.objects.create_user(
            email="student@test.com",
            password="password123!",
            name="수강생",
            nickname="student_nick",
            phone_number="010-1111-1111",
            gender="male",
            birthday="2000-01-01",
            role="STUDENT",
            is_active=True,
        )
        cls.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="password123!",
            name="관리자",
            nickname="admin_nick",
            phone_number="010-2222-2222",
            gender="female",
            birthday="1990-01-01",
            role="ADMIN",
            is_active=True,
        )
        cls.general_user = User.objects.create_user(
            email="general@test.com",
            password="password123!",
            name="일반유저",
            nickname="general_nick",
            phone_number="010-3333-3333",
            gender="male",
            birthday="1995-01-01",
            role="GENERAL",
            is_active=True,
        )

        # 카테고리 픽스처 (대분류만 있는 것, 소분류까지 있는 것)
        cls.large_category = QuestionCategory.objects.create(
            name="백엔드",
            parent=None,
        )
        medium_category = QuestionCategory.objects.create(
            name="웹프레임워크",
            parent=cls.large_category,
        )
        cls.small_category = QuestionCategory.objects.create(
            name="Django",
            parent=medium_category,
        )

    def setUp(self) -> None:
        # APIClient는 상태를 가지므로 매 테스트마다 새로 생성
        self.client = APIClient()

    # ── 헬퍼 ────────────────────────────────────────────────────────

    def _force_login(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    def _make_payload(self, **overrides: object) -> dict:
        base: dict = {
            "title": "Django ForeignKey 역참조는 어떻게 하나요?",
            "content": "related_name 지정 후 역참조하는 방법이 궁금합니다.",
            "category_id": self.small_category.id,  # ID 하드코딩 금지 → 실제 객체 참조
            "img_urls": [],
        }
        base.update(overrides)
        return base

    # ── 성공 케이스 ─────────────────────────────────────────────────

    def test_student_질문_등록_성공_이미지_없음(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload()

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "질문이 성공적으로 등록되었습니다.")
        self.assertIn("question_id", response.data)

        question = Question.objects.get(id=response.data["question_id"])
        self.assertEqual(question.title, payload["title"])
        self.assertEqual(question.content, payload["content"])
        self.assertEqual(question.category_id, self.small_category.id)
        self.assertEqual(question.author_id, self.student_user.id)
        self.assertEqual(question.view_count, 0)
        self.assertFalse(QuestionImage.objects.filter(question=question).exists())

    def test_student_질문_등록_성공_이미지_포함(self) -> None:
        self._force_login(self.student_user)
        img_urls = [
            "https://my-bucket.s3.ap-northeast-2.amazonaws.com/questions/img1.png",
            "https://my-bucket.s3.ap-northeast-2.amazonaws.com/questions/img2.png",
        ]
        payload = self._make_payload(img_urls=img_urls)

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        question = Question.objects.get(id=response.data["question_id"])
        images = QuestionImage.objects.filter(question=question).order_by("id")
        self.assertEqual(images.count(), 2)

        # ID 하드코딩 금지 → 실제 객체 ID 참조
        actual_urls = list(images.values_list("img_url", flat=True))
        self.assertEqual(actual_urls, img_urls)

    def test_admin_질문_등록_성공(self) -> None:
        """ADMIN 권한도 질문 등록 가능"""
        self._force_login(self.admin_user)
        payload = self._make_payload()

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        question = Question.objects.get(id=response.data["question_id"])
        self.assertEqual(question.author_id, self.admin_user.id)

    def test_대분류_카테고리로_질문_등록_성공(self) -> None:
        """소분류가 아닌 대분류 category_id로도 등록 가능"""
        self._force_login(self.student_user)
        payload = self._make_payload(category_id=self.large_category.id)

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        question = Question.objects.get(id=response.data["question_id"])
        self.assertEqual(question.category_id, self.large_category.id)

    # ── 인증/권한 에러 케이스 ────────────────────────────────────────

    def test_비로그인_질문_등록_401(self) -> None:
        payload = self._make_payload()

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_general_권한_질문_등록_403(self) -> None:
        """GENERAL 유저는 질문 등록 불가"""
        self._force_login(self.general_user)
        payload = self._make_payload()

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── 유효성 검사 에러 케이스 ──────────────────────────────────────

    def test_title_누락_400(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload()
        del payload["title"]

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_content_누락_400(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload()
        del payload["content"]

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_category_id_누락_400(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload()
        del payload["category_id"]

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_존재하지_않는_category_id_400(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload(category_id=99999999)

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_title_최대길이_초과_400(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload(title="A" * 51)  # max_length=50 초과

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_title_빈문자열_400(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload(title="")

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_content_빈문자열_400(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload(content="")

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_img_urls_유효하지_않은_URL_형식_400(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload(img_urls=["not-a-valid-url"])

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_img_urls_생략시_기본값_빈리스트(self) -> None:
        """img_urls 필드 자체를 보내지 않아도 등록 성공"""
        self._force_login(self.student_user)
        payload = self._make_payload()
        del payload["img_urls"]

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        question = Question.objects.get(id=response.data["question_id"])
        self.assertFalse(QuestionImage.objects.filter(question=question).exists())

    # ── DB 저장 정합성 ───────────────────────────────────────────────

    def test_질문_등록_후_DB_레코드_정확히_1개_생성(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload()
        before_count = Question.objects.count()

        self.client.post(URL, data=payload, format="json")

        self.assertEqual(Question.objects.count(), before_count + 1)

    def test_이미지_2개_등록_후_QuestionImage_레코드_정확히_2개(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload(
            img_urls=[
                "https://bucket.s3.amazonaws.com/img1.png",
                "https://bucket.s3.amazonaws.com/img2.png",
            ]
        )
        before_count = QuestionImage.objects.count()

        response = self.client.post(URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuestionImage.objects.count(), before_count + 2)

    def test_응답_question_id로_실제_Question_조회_가능(self) -> None:
        self._force_login(self.student_user)
        payload = self._make_payload()

        response = self.client.post(URL, data=payload, format="json")

        question_id = response.data["question_id"]
        # ID 하드코딩 금지 → 응답으로 받은 ID 그대로 조회
        self.assertTrue(Question.objects.filter(id=question_id).exists())
