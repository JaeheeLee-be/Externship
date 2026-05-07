from __future__ import annotations

import itertools
from datetime import date, timedelta
from typing import ClassVar

from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from apps.users.models import User, Withdrawal
from apps.users.services.admin_detail_service import AdminAccountDetailService
from apps.users.utils.admin_exceptions import AccountNotFoundError

# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

_counter = itertools.count(1)


def make_user(**kwargs: object) -> User:
    n = next(_counter)
    defaults: dict[str, object] = {
        "email": f"testuser{n}@test.com",
        "nickname": f"유저{n}",
        "name": "홍길동",
        "phone_number": f"010{n:08d}",
        "role": User.Role.USER,
        "is_active": True,
    }
    defaults.update(kwargs)
    user = User(**defaults)
    user.set_unusable_password()
    user.save()
    return user


def _url(account_id: int) -> str:
    return reverse("admin-account-detail", kwargs={"account_id": account_id})


# ── 서비스 단위 테스트 ─────────────────────────────────────────────────────────


class AdminAccountDetailServiceTest(APITestCase):
    """AdminAccountDetailService 단위 테스트 (HTTP 없이 직접 호출)"""

    def test_returns_correct_user(self) -> None:
        """존재하는 pk → 해당 User 객체 반환"""
        user = make_user()
        result = AdminAccountDetailService.get_account_detail(user.pk)
        self.assertEqual(result.pk, user.pk)

    def test_nonexistent_pk_raises_account_not_found_error(self) -> None:
        """존재하지 않는 pk → AccountNotFoundError 발생"""
        with self.assertRaises(AccountNotFoundError):
            AdminAccountDetailService.get_account_detail(99999)


# ── 인증 / 권한 ───────────────────────────────────────────────────────────────


class AdminAccountDetailAuthTest(APITestCase):
    """인증 및 권한 검증 테스트"""

    admin: ClassVar[User]
    target: ClassVar[User]
    normal_user: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(role=User.Role.ADMIN)
        cls.target = make_user()
        cls.normal_user = make_user()

    def test_unauthenticated_returns_401(self) -> None:
        res = self.client.get(_url(self.target.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(res.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    def test_non_admin_returns_403(self) -> None:
        self.client.force_authenticate(user=self.normal_user)
        res = self.client.get(_url(self.target.pk))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res.data["error_detail"], "권한이 없습니다.")


# ── 404 ──────────────────────────────────────────────────────────────────────


class AdminAccountDetailNotFoundTest(APITestCase):
    """존재하지 않는 account_id 요청 테스트"""

    admin: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(role=User.Role.ADMIN)

    def test_not_found_returns_404(self) -> None:
        self.client.force_authenticate(user=self.admin)
        res = self.client.get(_url(99999))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(res.data["error_detail"], "사용자 정보를 찾을 수 없습니다.")


# ── 응답 구조 (200 OK) ────────────────────────────────────────────────────────


class AdminAccountDetailResponseTest(APITestCase):
    """200 OK 응답의 필드 구조 및 값 검증"""

    admin: ClassVar[User]
    target: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(role=User.Role.ADMIN)
        cls.target = make_user()

    def _get(self, pk: int | None = None) -> Response:
        self.client.force_authenticate(user=self.admin)
        return self.client.get(_url(pk or self.target.pk))

    def test_returns_200_with_exact_fields(self) -> None:
        """명세 필드와 정확히 일치 (누락·추가 필드 없음)"""
        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = {
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "status",
            "role",
            "profile_img_url",
            "assigned_courses",
            "created_at",
        }
        self.assertEqual(set(res.data.keys()), expected)

    def test_role_is_lowercase(self) -> None:
        """role 필드는 소문자로 직렬화되어야 한다"""
        res = self._get()
        self.assertEqual(res.data["role"], self.target.role.lower())

    def test_assigned_courses_empty_when_no_enrollment(self) -> None:
        """코호트에 배정되지 않은 유저 → assigned_courses == []"""
        res = self._get()
        self.assertEqual(res.data["assigned_courses"], [])


# ── status 필드 분기 ──────────────────────────────────────────────────────────


class AdminAccountDetailStatusFieldTest(APITestCase):
    """AdminAccountDetailSerializer.get_status 분기 검증"""

    admin: ClassVar[User]
    active_user: ClassVar[User]
    inactive_user: ClassVar[User]
    withdrew_user: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(role=User.Role.ADMIN)
        cls.active_user = make_user(is_active=True)
        cls.inactive_user = make_user(is_active=False)
        cls.withdrew_user = make_user(is_active=True)
        Withdrawal.objects.create(
            user=cls.withdrew_user,
            reason=Withdrawal.Reason.GRADUATION,
            due_date=date.today() + timedelta(days=30),
        )

    def _get(self, pk: int) -> Response:
        self.client.force_authenticate(user=self.admin)
        return self.client.get(_url(pk))

    def test_status_active(self) -> None:
        """is_active=True, withdrawal 없음 → 'active'"""
        res = self._get(self.active_user.pk)
        self.assertEqual(res.data["status"], "active")

    def test_status_inactive(self) -> None:
        """is_active=False, withdrawal 없음 → 'inactive'"""
        res = self._get(self.inactive_user.pk)
        self.assertEqual(res.data["status"], "inactive")

    def test_status_withdrew(self) -> None:
        """Withdrawal 레코드 존재 → 'withdrew'"""
        res = self._get(self.withdrew_user.pk)
        self.assertEqual(res.data["status"], "withdrew")
