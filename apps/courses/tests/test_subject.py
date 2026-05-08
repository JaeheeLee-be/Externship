from __future__ import annotations

import itertools
from typing import Any

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.courses.models import Subject
from apps.posts.models import Course
from apps.users.models import User

_counter = itertools.count(1)


def make_user(**kwargs: Any) -> User:
    n = next(_counter)
    defaults: dict[str, Any] = {
        "email": f"testuser{n}@test.com",
        "nickname": f"유저{n}",
        "name": "이름",
        "phone_number": f"010{n:08d}",
        "role": "USER",
        "is_active": True,
    }
    defaults.update(kwargs)
    user = User(**defaults)
    user.set_unusable_password()
    user.save()
    return user


class SubjectTestBase(APITestCase):
    admin: User
    normal_user: User
    course: Course

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(role="ADMIN")
        cls.normal_user = make_user(role="USER")
        cls.course = Course.objects.create(name="테스트 과정", tag="TS0")

    def setUp(self) -> None:
        self.client = APIClient()


class SubjectListViewTest(SubjectTestBase):
    subject1: Subject
    subject2: Subject
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.subject1 = Subject.objects.create(
            course=cls.course,
            title="변수와 자료형",
            number_of_days=3,
            number_of_hours=6,
        )
        cls.subject2 = Subject.objects.create(
            course=cls.course,
            title="함수와 모듈",
            number_of_days=2,
            number_of_hours=4,
        )
        cls.url = f"/api/v1/courses/{cls.course.id}/subjects/"

    def test_list_subjects_success(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["id"], self.subject1.id)
        self.assertEqual(response.data[1]["id"], self.subject2.id)

    def test_list_subjects_empty(self) -> None:
        empty_course = Course.objects.create(name="빈 과정", tag="MT1")
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f"/api/v1/courses/{empty_course.id}/subjects/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_subjects_status_field(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["status"], "ACTIVATED")

    def test_list_subjects_unauthenticated(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_subjects_non_admin_forbidden(self) -> None:
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubjectCreateViewTest(SubjectTestBase):
    url = "/api/v1/admin/subjects/"

    def test_create_subject_success(self) -> None:
        self.client.force_authenticate(user=self.admin)
        payload = {
            "course_id": self.course.id,
            "title": "ORM 기초",
            "number_of_days": 5,
            "number_of_hours": 10,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "ORM 기초")
        self.assertEqual(response.data["course_id"], self.course.id)

    def test_create_subject_with_thumbnail(self) -> None:
        self.client.force_authenticate(user=self.admin)
        payload = {
            "course_id": self.course.id,
            "title": "뷰 기초",
            "number_of_days": 3,
            "number_of_hours": 6,
            "thumbnail_img_url": "https://example.com/thumb.jpg",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["thumbnail_img_url"], "https://example.com/thumb.jpg")

    def test_create_subject_missing_required_field(self) -> None:
        self.client.force_authenticate(user=self.admin)
        payload = {"course_id": self.course.id, "title": "제목만 있음"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_subject_course_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin)
        payload = {
            "course_id": 99999,
            "title": "없는 과정",
            "number_of_days": 1,
            "number_of_hours": 2,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_subject_duplicate_title_conflict(self) -> None:
        Subject.objects.create(course=self.course, title="중복 제목", number_of_days=1, number_of_hours=2)
        self.client.force_authenticate(user=self.admin)
        payload = {
            "course_id": self.course.id,
            "title": "중복 제목",
            "number_of_days": 2,
            "number_of_hours": 4,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_create_subject_unauthenticated(self) -> None:
        payload = {
            "course_id": self.course.id,
            "title": "비로그인",
            "number_of_days": 1,
            "number_of_hours": 2,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_subject_non_admin_forbidden(self) -> None:
        self.client.force_authenticate(user=self.normal_user)
        payload = {
            "course_id": self.course.id,
            "title": "권한 없음",
            "number_of_days": 1,
            "number_of_hours": 2,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubjectDetailViewGetTest(SubjectTestBase):
    subject: Subject
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.subject = Subject.objects.create(
            course=cls.course,
            title="컴포넌트",
            number_of_days=4,
            number_of_hours=8,
            thumbnail_img_url="https://example.com/react.jpg",
        )
        cls.url = f"/api/v1/admin/subjects/{cls.subject.id}/"

    def test_get_subject_detail_success(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.subject.id)
        self.assertEqual(response.data["title"], "컴포넌트")
        self.assertEqual(response.data["number_of_days"], 4)
        self.assertEqual(response.data["number_of_hours"], 8)
        self.assertEqual(response.data["course"]["id"], self.course.id)
        self.assertEqual(response.data["course"]["name"], "테스트 과정")
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

    def test_get_subject_detail_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/v1/admin/subjects/99999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_subject_detail_unauthenticated(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_subject_detail_non_admin_forbidden(self) -> None:
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubjectDetailViewPatchTest(SubjectTestBase):
    other_course: Course

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.other_course = Course.objects.create(name="노드JS", tag="ND1")

    def setUp(self) -> None:
        super().setUp()
        self.subject = Subject.objects.create(
            course=self.course,
            title="타입 기초",
            number_of_days=3,
            number_of_hours=6,
        )
        self.url = f"/api/v1/admin/subjects/{self.subject.id}/"

    def test_patch_subject_title_success(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(self.url, {"title": "수정된 제목"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subject.refresh_from_db()
        self.assertEqual(self.subject.title, "수정된 제목")

    def test_patch_subject_course_success(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(self.url, {"course_id": self.other_course.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subject.refresh_from_db()
        self.assertEqual(self.subject.course_id, self.other_course.id)

    def test_patch_subject_status_deactivated(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(self.url, {"status": False}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subject.refresh_from_db()
        self.assertFalse(self.subject.status)

    def test_patch_subject_duplicate_title_conflict(self) -> None:
        Subject.objects.create(course=self.course, title="이미 있는 제목", number_of_days=1, number_of_hours=2)
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(self.url, {"title": "이미 있는 제목"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_patch_subject_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch("/api/v1/admin/subjects/99999/", {"title": "없는 과목"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_subject_unauthenticated(self) -> None:
        response = self.client.patch(self.url, {"title": "비로그인"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_subject_non_admin_forbidden(self) -> None:
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.patch(self.url, {"title": "권한 없음"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubjectDetailViewDeleteTest(SubjectTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.subject = Subject.objects.create(
            course=self.course,
            title="정렬 알고리즘",
            number_of_days=2,
            number_of_hours=4,
        )
        self.url = f"/api/v1/admin/subjects/{self.subject.id}/"

    def test_delete_subject_success(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Subject.objects.filter(id=self.subject.id).exists())

    def test_delete_subject_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete("/api/v1/admin/subjects/99999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_subject_unauthenticated(self) -> None:
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Subject.objects.filter(id=self.subject.id).exists())

    def test_delete_subject_non_admin_forbidden(self) -> None:
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Subject.objects.filter(id=self.subject.id).exists())
