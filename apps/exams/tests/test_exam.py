from django.db import IntegrityError
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from apps.exams.models import Exam, ExamQuestion
from apps.posts.models import Course, Subject
from apps.users.models import User


class ExamBaseTestCase(APITestCase):
    user: User
    admin: User
    course: Course
    subject_html: Subject
    subject_python: Subject
    exam1: Exam
    exam2: Exam
    question1: ExamQuestion
    question2: ExamQuestion

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="test@test.com",
            password="test1234!",
            name="테스터",
            nickname="tester",
            phone_number="010-1234-5678",
            is_active=True,
            role="STUDENT",
        )
        cls.admin = User.objects.create_superuser(
            email="admin@test.com",
            password="test1234!",
            name="관리자",
            nickname="admin",
            phone_number="010-2222-5678",
            is_active=True,
            role="ADMIN",
        )
        cls.course = Course.objects.create(
            name="웹 개발",
            tag="WEB",
        )
        cls.subject_html = Subject.objects.create(
            course=cls.course,
            title="html",
            number_of_days=30,
            number_of_hours=60,
        )
        cls.subject_python = Subject.objects.create(
            course=cls.course,
            title="python",
            number_of_days=30,
            number_of_hours=60,
        )
        cls.exam1 = Exam.objects.create(
            subject=cls.subject_html,
            title="test_exam",
        )
        cls.exam2 = Exam.objects.create(
            subject=cls.subject_python,
            title="test_exam2",
        )
        cls.question1 = ExamQuestion.objects.create(
            exam=cls.exam1,
            question="test_question",
            type="single_choice",
            answer={"answer": "test_answer1"},
            point=1,
        )
        cls.question2 = ExamQuestion.objects.create(
            exam=cls.exam1,
            question="test_question2",
            type="multiple_choice",
            answer={"answer": ["test_answer1", "test_answer2"]},
            point=2,
        )


# 모델 테스트
class TestExamBaseModel(ExamBaseTestCase):
    def test_exam_title_unique_exception(self) -> None:
        with self.assertRaises(IntegrityError):
            Exam.objects.create(
                subject=self.subject_html,
                title="test_exam",
            )

    def test_exam_create(self) -> None:
        exam = Exam.objects.create(
            subject=self.subject_python,
            title="new_exam",
        )
        self.assertEqual(exam.title, "new_exam")
        self.assertCountEqual(Exam.objects.all(), [self.exam1, self.exam2, exam])
        self.assertEqual(Exam.objects.count(), 3)


class TestExamBaseAPI(ExamBaseTestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    # 쪽지시험 목록 조회: 권한
    def test_get_exam_list_as_admin(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("exam-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["title"], "test_exam2")
        self.assertEqual(response.data["results"][0]["subject_name"], "python")

    def test_get_exam_list_as_user(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("exam-list"))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_detail"], "쪽지시험 목록 조회 권한이 없습니다.")

    def test_get_exam_list_unauthorized(self) -> None:
        response = self.client.get(reverse("exam-list"))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    # 쪽지시험 목록 조회: 필터
    def test_get_exam_list_with_subject(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("exam-list"), {"subject_id": self.subject_html.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject_name"], "html")

    def test_get_exam_list_with_subject_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("exam-list"), {"subject_id": self.subject_python.id + 9999})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    # 쪽지시험 목록 조회: 검색
    def test_get_exam_list_with_search_title(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam-list"), {"search_keyword": "exam"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["title"], "test_exam2")
        self.assertEqual(response.data["results"][0]["subject_name"], "python")

    def test_get_exam_list_with_search_subject(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam-list"), {"search_keyword": "html"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject_name"], "html")

    def test_get_exam_list_with_search_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam-list"), {"search_keyword": "not_found"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    # 쪽지시험 목록 조회: sort
    def test_get_exam_list_with_sort(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam-list"), {"sort": "created_at"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject_name"], "html")

    # 쪽지시험 목록 조회: order
    def test_get_exam_list_with_order(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam-list"), {"order": "desc"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["title"], "test_exam2")
        self.assertEqual(response.data["results"][0]["subject_name"], "python")

    # 쪽지시험 목록 조회: sort + order
    def test_get_exam_list_with_sort_and_order(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam-list"), {"sort": "subject__title", "order": "asc"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject_name"], "html")

    # 쪽지시험 생성: 권한
    def test_exam_create_as_admin(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("exam-list"),
            {
                "subject_id": self.subject_python.id,
                "title": "new_exam",
                "thumbnail_image_url": "https://example.com/image.jpg",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "new_exam")
        self.assertEqual(response.data["subject_id"], self.subject_python.id)
        self.assertEqual(Exam.objects.count(), 3)

    def test_exam_create_as_user(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("exam-list"),
            {
                "subject_id": self.subject_python.id,
                "title": "new_exam",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_detail"], "쪽지시험 생성 권한이 없습니다.")
        self.assertEqual(Exam.objects.count(), 2)

    def test_exam_create_unauthorized(self) -> None:
        response = self.client.post(
            reverse("exam-list"),
            {
                "subject_id": self.subject_python.id,
                "title": "new_exam",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")
        self.assertEqual(Exam.objects.count(), 2)

    # 쪽지시험 생성: 없는 subject 생성
    def test_exam_create_not_found_subject(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("exam-list"),
            {
                "subject_id": self.subject_html.id + 9999,
                "title": "new_exam",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "해당 과목 정보를 찾을 수 없습니다.")
        self.assertEqual(Exam.objects.count(), 2)

    # 쪽지시험 생성: 동일한 이름의 시험 생성
    def test_exam_create_title_unique_exception(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("exam-list"),
            {
                "subject_id": self.subject_python.id,
                "title": "test_exam",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error_detail"], "동일한 이름의 시험이 이미 존재합니다.")
        self.assertEqual(Exam.objects.count(), 2)

    # 쪽지시험 생성: 유효하지 않은 요청
    def test_exam_create_invalid_thumbnail_extension(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("exam-list"),
            {
                "subject_id": self.subject_python.id,
                "title": "new_exam",
                "thumbnail_image_url": "https://example.com/image.abcd",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error_detail"], "유효하지 않은 시험 생성 요청입니다.")
        self.assertEqual(Exam.objects.count(), 2)

    def test_exam_create_title_max_length(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("exam-list"),
            {
                "subject_id": self.subject_python.id,
                "title": "new_exam" * 20,
                "thumbnail_image_url": "https://example.com/image.abcd",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Exam.objects.count(), 2)


class TestExamDetail(ExamBaseTestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    # 디테일 조회: 권한 테스트
    def test_detail_get_as_admin(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam-detail", kwargs={"exam_id": self.exam1.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "test_exam")
        self.assertEqual(response.data["subject"]["title"], "html")
        self.assertEqual(response.data["questions"][0]["type"], "single_choice")
        self.assertEqual(response.data["questions"][0]["question"], "test_question")

    def test_detail_get_as_user(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("exam-detail", kwargs={"exam_id": self.exam1.id}))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_detail"], "쪽지시험 상세 조회 권한이 없습니다.")

    def test_detail_get_unauthorized(self) -> None:
        response = self.client.get(reverse("exam-detail", kwargs={"exam_id": self.exam1.id}))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    # 디테일 조회: not found
    def test_detail_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam-detail", kwargs={"exam_id": self.exam1.id + 9999}))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "해당 쪽지시험 정보를 찾을 수 없습니다.")

    # 디테일 수정: 권한
    def test_detail_put_as_admin(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            reverse("exam-detail", kwargs={"exam_id": self.exam1.id}),
            {
                "title": "updated_exam",
                "subject_id": self.subject_python.id,
                "thumbnail_image_url": "https://example.com/image.jpg",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "updated_exam")
        self.assertEqual(response.data["subject_id"], self.subject_python.id)
        self.assertEqual(response.data["thumbnail_image_url"], "https://example.com/image.jpg")
        self.assertEqual(Exam.objects.count(), 2)

    def test_detail_put_as_user(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            reverse("exam-detail", kwargs={"exam_id": self.exam1.id}),
            {
                "title": "updated_exam",
                "subject_id": self.subject_python.id,
                "thumbnail_image_url": "https://example.com/image.jpg",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_detail"], "쪽지시험 수정 권한이 없습니다.")

    def test_detail_put_unauthorized(self) -> None:
        response = self.client.put(
            reverse("exam-detail", kwargs={"exam_id": self.exam1.id}),
            {
                "title": "updated_exam",
                "subject_id": self.subject_python.id,
                "thumbnail_image_url": "https://example.com/image.jpg",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    # 디테일 수정: 수정 타이틀 제외 수정 가능
    def test_detail_put_title_exclude(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            reverse("exam-detail", kwargs={"exam_id": self.exam1.id}),
            {
                "title": "test_exam",
                "subject_id": self.subject_python.id,
                "thumbnail_image_url": "https://example.com/image.jpg",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "test_exam")
        self.assertEqual(response.data["subject_id"], self.subject_python.id)

    # 디테일 수정: 예외
    def test_detail_put_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            reverse("exam-detail", kwargs={"exam_id": self.exam1.id + 9999}),
            {
                "title": "updated_exam",
                "subject_id": self.subject_python.id,
                "thumbnail_image_url": "https://example.com/image.jpg",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "해당 쪽지시험 정보를 찾을 수 없습니다.")
        self.assertEqual(Exam.objects.count(), 2)

    def test_detail_put_title_unique_exception(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            reverse("exam-detail", kwargs={"exam_id": self.exam1.id}),
            {
                "title": "test_exam2",
                "subject_id": self.subject_python.id,
                "thumbnail_image_url": "https://example.com/image.jpg",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error_detail"], "동일한 이름의 시험이 이미 존재합니다.")
        self.assertEqual(Exam.objects.count(), 2)

    def test_detail_put_subject_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            reverse("exam-detail", kwargs={"exam_id": self.exam1.id}),
            {
                "title": "updated_exam",
                "subject_id": self.subject_html.id + 9999,
                "thumbnail_image_url": "https://example.com/image.jpg",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "해당 과목 정보를 찾을 수 없습니다.")
        self.assertEqual(Exam.objects.count(), 2)

    def test_detail_put_invalid_thumbnail_extension(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            reverse("exam-detail", kwargs={"exam_id": self.exam1.id}),
            {
                "title": "updated_exam",
                "subject_id": self.subject_python.id,
                "thumbnail_image_url": "https://example.com/image.abcd",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error_detail"], "유효하지 않은 요청 데이터입니다.")
        self.assertEqual(Exam.objects.count(), 2)

    def test_detail_put_title_max_langth(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            reverse("exam-detail", kwargs={"exam_id": self.exam1.id}),
            {
                "title": "updated_exam" * 20,
                "subject_id": self.subject_python.id,
                "thumbnail_image_url": "https://example.com/image.jpg",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Exam.objects.count(), 2)
