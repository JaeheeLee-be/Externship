from __future__ import annotations

import itertools
from typing import ClassVar

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

_counter = itertools.count(1)


def make_user(**kwargs: object) -> User:
    n = next(_counter)
    defaults: dict[str, object] = {
        "email": f"testuser{n}@test.com",
        "name": "홍길동",
        "nickname": f"유저{n}",
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


# ── 인증 / 권한 ───────────────────────────────────────────────────────────────


class AdminAccountDeleteAuthTest(APITestCase):
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
        res = self.client.delete(_url(self.target.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_401_error_message(self) -> None:
        """401 응답 본문에 한국어 에러 메시지가 정상 출력되는지 확인"""
        res = self.client.delete(_url(self.target.pk))
        self.assertIn("error_detail", res.data)
        self.assertEqual(res.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    def test_non_admin_returns_403(self) -> None:
        self.client.force_authenticate(user=self.normal_user)
        res = self.client.delete(_url(self.target.pk))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


# ── 404 ──────────────────────────────────────────────────────────────────────


class AdminAccountDeleteNotFoundTest(APITestCase):
    """존재하지 않는 account_id 요청 테스트"""

    admin: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(role=User.Role.ADMIN)

    def test_not_found_returns_404(self) -> None:
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(_url(99999))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", res.data)
        self.assertEqual(res.data["error_detail"], "사용자 정보를 찾을 수 없습니다.")


# ── 정상 삭제 (200 OK) ────────────────────────────────────────────────────────


class AdminAccountDeleteSuccessTest(APITestCase):
    """200 OK 응답 및 실제 삭제 여부 검증"""

    admin: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(role=User.Role.ADMIN)

    def test_delete_returns_200(self) -> None:
        target = make_user()
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(_url(target.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_response_contains_pk(self) -> None:
        """응답 메시지에 삭제된 pk가 포함되는지 확인"""
        target = make_user()
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(_url(target.pk))
        self.assertIn("detail", res.data)
        self.assertIn(str(target.pk), res.data["detail"])

    def test_delete_response_message(self) -> None:
        """응답 메시지 포맷 확인"""
        target = make_user()
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(_url(target.pk))
        self.assertEqual(res.data["detail"], f"유저 데이터가 삭제되었습니다. - pk: {target.pk}")

    def test_user_actually_deleted(self) -> None:
        """삭제 후 DB에서 해당 유저가 실제로 제거되었는지 확인"""
        target = make_user()
        pk = target.pk
        self.client.force_authenticate(user=self.admin)
        self.client.delete(_url(pk))
        self.assertFalse(User.objects.filter(pk=pk).exists())

    def test_deleted_user_returns_404_on_subsequent_request(self) -> None:
        """삭제된 유저에 재요청 시 404 반환"""
        target = make_user()
        self.client.force_authenticate(user=self.admin)
        self.client.delete(_url(target.pk))
        res = self.client.delete(_url(target.pk))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
