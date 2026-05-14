from typing import Any

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.question_models import Question, QuestionCategory, QuestionImage
from apps.users.models import User

URL = "/api/v1/qna/questions"


class QuestionListAPIViewTest(APITestCase):
    """GET /api/v1/qna/questions - 질문 목록 조회 API 테스트"""

    # ── 클래스 레벨 타입 어노테이션 ──────────────────────────────────
    student_user: User
    other_student: User
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
        cls.student_user = User.objects.create_user(
            email="student@test.com",
            password="password123!",
            name="수강생",
            nickname="st_nick",
            phone_number="010-1111-1111",
            gender="male",
            birthday="2000-01-01",
            role="STUDENT",
            is_active=True,
        )
        cls.other_student = User.objects.create_user(
            email="other@test.com",
            password="password123!",
            name="다른수강생",
            nickname="ot_nick",
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

        # 카테고리 대/중/소 구성
        cls.large_category = QuestionCategory.objects.create(name="백엔드", parent=None)
        cls.medium_category = QuestionCategory.objects.create(name="웹프레임워크", parent=cls.large_category)
        cls.small_category = QuestionCategory.objects.create(name="Django", parent=cls.medium_category)
        cls.small_category2 = QuestionCategory.objects.create(name="FastAPI", parent=cls.medium_category)

        # 질문 픽스처
        cls.question1 = Question.objects.create(
            author=cls.student_user,
            category=cls.small_category,
            title="Django ORM 질문",
            content="Django ORM에서 select_related와 prefetch_related 차이가 궁금합니다.",
            view_count=10,
        )
        cls.question2 = Question.objects.create(
            author=cls.other_student,
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

        # question1에만 이미지 추가
        QuestionImage.objects.create(
            question=cls.question1,
            img_url="https://bucket.s3.amazonaws.com/img1.png",
        )

    def setUp(self) -> None:
        self.client = APIClient()

    # ── 헬퍼 ────────────────────────────────────────────────────────

    def _force_login(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    def _get_result_ids(self, response_data: dict[str, Any]) -> list[int]:
        return [item["id"] for item in response_data["results"]]

    # ── 성공 케이스 ─────────────────────────────────────────────────

    def test_목록_조회_성공_기본(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

    def test_목록_조회_응답_필드_검증(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data["results"][0]
        # 필수 필드 존재 여부 확인
        for field in [
            "id",
            "category",
            "author",
            "title",
            "content_preview",
            "answer_count",
            "view_count",
            "created_at",
            "thumbnail_img_url",
        ]:
            self.assertIn(field, item)

        # category 필드 구조 확인
        for field in ["id", "depth", "names"]:
            self.assertIn(field, item["category"])

        # author 필드 구조 확인
        for field in ["id", "nickname", "profile_img_url"]:
            self.assertIn(field, item["author"])

    def test_카테고리_depth_소분류는_3(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # question1은 소분류(Django)에 속함
        result = next(r for r in response.data["results"] if r["id"] == self.question1.id)
        self.assertEqual(result["category"]["depth"], 3)
        self.assertEqual(result["category"]["names"], ["백엔드", "웹프레임워크", "Django"])

    def test_thumbnail_img_url_이미지_있는_질문(self) -> None:
        """이미지가 있는 질문은 첫 번째 이미지 URL 반환"""
        self._force_login(self.student_user)

        response = self.client.get(URL)

        result = next(r for r in response.data["results"] if r["id"] == self.question1.id)
        self.assertEqual(result["thumbnail_img_url"], "https://bucket.s3.amazonaws.com/img1.png")

    def test_thumbnail_img_url_이미지_없는_질문은_null(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL)

        result = next(r for r in response.data["results"] if r["id"] == self.question2.id)
        self.assertIsNone(result["thumbnail_img_url"])

    def test_content_preview_100자_초과시_잘림(self) -> None:
        long_content = "A" * 200
        question = Question.objects.create(
            author=self.student_user,
            category=self.small_category,
            title="긴 내용 질문",
            content=long_content,
        )
        self._force_login(self.student_user)

        response = self.client.get(URL)

        result = next(r for r in response.data["results"] if r["id"] == question.id)
        self.assertEqual(len(result["content_preview"]), 100)

    # ── 페이지네이션 ─────────────────────────────────────────────────

    def test_페이지네이션_page_size_적용(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"page": 1, "page_size": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_페이지네이션_next_url_존재(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"page": 1, "page_size": 2})

        self.assertIsNotNone(response.data["next"])

    def test_페이지네이션_마지막_페이지_next_없음(self) -> None:
        self._force_login(self.student_user)
        total = Question.objects.count()

        response = self.client.get(URL, {"page": 1, "page_size": total})

        self.assertIsNone(response.data["next"])

    def test_페이지네이션_첫_페이지_previous_없음(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"page": 1, "page_size": 2})

        self.assertIsNone(response.data["previous"])

    def test_count_전체_질문_수_반환(self) -> None:
        self._force_login(self.student_user)
        total = Question.objects.count()

        response = self.client.get(URL)

        self.assertEqual(response.data["count"], total)

    # ── 검색 필터 ────────────────────────────────────────────────────

    def test_search_keyword_제목_검색(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"search_keyword": "ORM"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self._get_result_ids(response.data)
        self.assertIn(self.question1.id, ids)
        self.assertNotIn(self.question2.id, ids)
        self.assertNotIn(self.question3.id, ids)

    def test_search_keyword_결과_없으면_빈_리스트(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"search_keyword": "존재하지않는키워드xyz"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    # ── 카테고리 필터 ────────────────────────────────────────────────

    def test_category_id_소분류_필터(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"category_id": self.small_category.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self._get_result_ids(response.data)
        self.assertIn(self.question1.id, ids)
        self.assertIn(self.question2.id, ids)
        self.assertNotIn(self.question3.id, ids)  # small_category2 소속

    def test_category_id_중분류_필터_하위_모두_포함(self) -> None:
        """중분류 선택 시 하위 소분류 질문 모두 포함"""
        self._force_login(self.student_user)

        response = self.client.get(URL, {"category_id": self.medium_category.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self._get_result_ids(response.data)
        # small_category, small_category2 둘 다 medium_category 하위
        self.assertIn(self.question1.id, ids)
        self.assertIn(self.question2.id, ids)
        self.assertIn(self.question3.id, ids)

    def test_존재하지_않는_category_id_404(self) -> None:
        """존재하지 않는 category_id는 404"""
        self._force_login(self.student_user)

        response = self.client.get(URL, {"category_id": 99999999})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", response.data)
        self.assertEqual(response.data["error_detail"], "조회 가능한 질문이 존재하지 않습니다.")

    # ── 답변 상태 필터 ───────────────────────────────────────────────

    def test_answer_status_answered_필터(self) -> None:
        # question1에 답변 달기 (Answer 모델 직접 생성)
        from django.apps import apps

        from apps.qna.models.question_models import Question as Q

        Answer = apps.get_model("qna", "Answer")
        Answer.objects.create(
            author=self.other_student,
            question=self.question1,
            content="답변입니다.",
        )
        self._force_login(self.student_user)

        response = self.client.get(URL, {"answer_status": "answered"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self._get_result_ids(response.data)
        self.assertIn(self.question1.id, ids)
        self.assertNotIn(self.question2.id, ids)

    def test_answer_status_unanswered_필터(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"answer_status": "unanswered"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertEqual(item["answer_count"], 0)

    def test_answer_status_잘못된_값_400(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"answer_status": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    # ── 정렬 ─────────────────────────────────────────────────────────

    def test_sort_latest_최신순(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"sort": "latest"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self._get_result_ids(response.data)
        # question3이 가장 나중에 생성됐으므로 첫 번째
        self.assertEqual(ids[0], self.question3.id)

    def test_sort_oldest_오래된순(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"sort": "oldest"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self._get_result_ids(response.data)
        # question1이 가장 먼저 생성됐으므로 첫 번째
        self.assertEqual(ids[0], self.question1.id)

    def test_sort_views_조회수순(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"sort": "views"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self._get_result_ids(response.data)
        # view_count: question3=20, question1=10, question2=5
        self.assertEqual(ids[0], self.question3.id)

    def test_sort_잘못된_값_400(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"sort": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    # ── 인증/권한 에러 케이스 ────────────────────────────────────────

    def test_비로그인_목록_조회_200(self) -> None:
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_general_권한_목록_조회_200(self) -> None:
        self._force_login(self.general_user)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── Query Param 유효성 ───────────────────────────────────────────

    def test_page_문자열_400(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"page": "abc"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_category_id_문자열_400(self) -> None:
        self._force_login(self.student_user)

        response = self.client.get(URL, {"category_id": "abc"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
