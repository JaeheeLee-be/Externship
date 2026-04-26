from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.exams.models.exam_model import Exam
from apps.exams.models.exam_question_model import ExamQuestion
from apps.posts.models.course import Course
from apps.posts.models.subject import Subject
from apps.users.models import User


class TestAdminExamQuestionCreateView(APITestCase):
    exam: Exam
    question: ExamQuestion
    client: APIClient
    admin_user: User
    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = User.objects.create_superuser(
            email="admin@test.com",
            name="admin",
            nickname="admin",
            phone_number="123456789",
            is_active=True,
            role=User.Role.ADMIN,
            password="test_password",
        )
        cls.user = User.objects.create_user(
            email="user@test.com",
            name="user",
            nickname="user",
            phone_number="01099299929",
            is_active=True,
            role=User.Role.USER,
            password="test_password",
        )
        cls.student = User.objects.create_user(
            email="student@test.com",
            name="student",
            nickname="stu",
            phone_number="01022020023",
            is_active=True,
            role=User.Role.STUDENT,
            password="test_student",
        )
        cls.course = Course.objects.create(name="test", tag="t")
        cls.subject = Subject.objects.create(
            course=cls.course,
            title="test",
            number_of_days=1,
            number_of_hours=1,
        )
        cls.exam = Exam.objects.create(
            title="test_title",
            subject=cls.subject,
        )
        cls.data = {
            "question": "test",
            "answer": {"answer": 1},
            "type": ExamQuestion.QuestionType.SHORT_ANSWER,
            "point": 5,
        }
        cls.question = ExamQuestion.objects.create(
            exam=cls.exam,
            question="tt",
            answer={"answer": 1},
            type=ExamQuestion.QuestionType.SHORT_ANSWER,
            point=1,
        )
        cls.fail_point_data = {"question": "test_2", "answer": {"answer": 2}, "type": "ox", "point": 10}
        cls.update_data = {
            "question": "mod_test",
            "answer": {"answer": 5},
            "type": ExamQuestion.QuestionType.SHORT_ANSWER,
            "point": 5,
        }
        cls.update_fail_point_data = {
            "question": "mod_test",
            "answer": {"answer": 5},
            "type": ExamQuestion.QuestionType.SHORT_ANSWER,
            "point": 9,
        }
        cls.create_url = reverse("exam-question-create", kwargs={"exam_id": cls.exam.id})
        cls.update_url = reverse(
            "exam-question-update", kwargs={"exam_id": cls.exam.id, "question_id": cls.question.id}
        )
        cls.error_400_create = "유효하지 않은 문제 생성 데이터 입니다."
        cls.error_401_create = "자격 인증 데이터가 제공되지 않았습니다."
        cls.error_403_create = "쪽지시험 문제 등록 권한이 없습니다."
        cls.error_404_create = "생성하려는 문제 정보를 찾을 수 없습니다."
        cls.error_409_create = "해당 쪽지시험에 등록 가능한 문제 수 또는 총 배점을 초과했습니다."
        cls.error_400_update = "유효하지 않은 문제 수정 데이터 입니다."
        cls.error_401_update = "자격 인증 데이터가 제공되지 않았습니다."
        cls.error_403_update = "쪽지시험 문제 수정 권한이 없습니다."
        cls.error_404_update = "수정하려는 문제 정보를 찾을 수 없습니다."
        cls.error_409_update = "시험 문제 수 제한 또는 총 배점을 초과하여 문제를 수정할 수 없습니다."

    def setUp(self) -> None:
        self.client = APIClient()

    def test_admin_create_question(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.create_url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExamQuestion.objects.filter(exam=self.exam).count(), 2)

    def test_user_create_question(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.create_url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("error_detail"), self.error_403_create)

    def test_student_create_question(self) -> None:
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.create_url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("error_detail"), self.error_403_create)

    def test_unauth_user_create_question(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.post(self.create_url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get("error_detail"), self.error_401_create)

    def test_admin_check_limit_point(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        ExamQuestion.objects.create(exam=self.exam, question="test", answer={"answer": 1}, type="ox", point=99)
        response = self.client.post(self.create_url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data.get("error_detail"), self.error_409_create)

    def test_admin_check_limit_question_len(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        for i in range(20):
            ExamQuestion.objects.create(
                exam=self.exam,
                question=f"test{i}",
                answer={"answer": 1},
                type=ExamQuestion.QuestionType.SHORT_ANSWER,
                point=1,
            )
        response = self.client.post(self.create_url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data.get("error_detail"), self.error_409_create)

    def test_admin_check_update_question(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(self.update_url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            ExamQuestion.objects.filter(id=self.question.id).first().question, self.update_data["question"]
        )

    def test_user_check_update_question(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.update_url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("error_detail"), self.error_403_create)

    def test_student_check_update_question(self) -> None:
        self.client.force_authenticate(user=self.student)
        response = self.client.put(self.update_url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("error_detail"), self.error_403_create)

    def test_unauth_student_check_update_question(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.put(self.update_url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get("error_detail"), self.error_401_create)

    def test_admin_check_update_limit_point(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        ExamQuestion.objects.create(
            exam=self.exam,
            question="te_2",
            answer={"answer": 1},
            type=ExamQuestion.QuestionType.SHORT_ANSWER,
            point=99,
        )
        response = self.client.put(self.update_url, self.update_fail_point_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data.get("error_detail"), self.error_409_create)
