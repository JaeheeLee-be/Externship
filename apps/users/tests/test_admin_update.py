from __future__ import annotations

import itertools
from typing import ClassVar

from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from apps.users.models import User

# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

_counter = itertools.count(1)


def make_user(**kwargs: object) -> User:
    n = next(_counter)
    defaults: dict[str, object] = {
        "email": f"testuser{n}@test.com",
        "password": "Test1234!@",
        "name": "홍길동",
        "nickname": f"유저{n}",
        "phone_number": f"010{n:08d}",
        "role": User.Role.USER,
        "is_active": True,
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def _url(account_id: int) -> str:
    return reverse("admin-account-update", kwargs={"account_id": account_id})


# ── 인증 / 권한 ───────────────────────────────────────────────────────────────


class AdminAccountUpdateAuthTest(APITestCase):
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
        res = self.client.patch(_url(self.target.pk), {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_401_error_message(self) -> None:
        """401 응답 본문에 한국어 에러 메시지가 정상 출력되는지 확인"""
        res = self.client.patch(_url(self.target.pk), {}, format="json")
        self.assertIn("error_detail", res.data)
        self.assertEqual(res.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    def test_non_admin_returns_403(self) -> None:
        self.client.force_authenticate(user=self.normal_user)
        res = self.client.patch(_url(self.target.pk), {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


# ── 404 ──────────────────────────────────────────────────────────────────────


class AdminAccountUpdateNotFoundTest(APITestCase):
    """존재하지 않는 account_id 요청 테스트"""

    admin: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(role=User.Role.ADMIN)

    def test_not_found_returns_404(self) -> None:
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(_url(99999), {"nickname": "새닉"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", res.data)
        self.assertEqual(res.data["error_detail"], "사용자 정보를 찾을 수 없습니다.")


# ── 정상 수정 (200 OK) ────────────────────────────────────────────────────────


class AdminAccountUpdateSuccessTest(APITestCase):
    """200 OK 응답의 필드 구조 및 값 검증"""

    admin: ClassVar[User]
    target: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(role=User.Role.ADMIN)
        cls.target = make_user()

    def _patch(self, payload: dict, pk: int | None = None) -> Response:
        self.client.force_authenticate(user=self.admin)
        return self.client.patch(_url(pk or self.target.pk), payload, format="json")

    def test_patch_nickname_returns_200(self) -> None:
        res = self._patch({"nickname": "새닉네임"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["nickname"], "새닉네임")

    def test_patch_response_exact_fields(self) -> None:
        """명세 필드와 정확히 일치 (누락·추가 필드 없음)"""
        res = self._patch({"name": "김철수"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = {
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "profile_img_url",
            "updated_at",
        }
        self.assertEqual(set(res.data.keys()), expected)

    def test_patch_updated_at_in_response(self) -> None:
        """응답에 updated_at 포함 여부"""
        res = self._patch({"name": "이영희"})
        self.assertIn("updated_at", res.data)


# ── 400 검증 오류 ─────────────────────────────────────────────────────────────


class AdminAccountUpdateValidationTest(APITestCase):
    """잘못된 입력값에 대한 400 Bad Request 검증"""

    admin: ClassVar[User]
    target: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(role=User.Role.ADMIN)
        cls.target = make_user()

    def _patch(self, payload: dict) -> Response:
        self.client.force_authenticate(user=self.admin)
        return self.client.patch(_url(self.target.pk), payload, format="json")

    def test_invalid_phone_format_returns_400(self) -> None:
        """하이픈 포함 전화번호 → 400, phone_number 필드 오류 메시지 확인"""
        res = self._patch({"phone_number": "010-1234-5678"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", res.data)
        self.assertIn("phone_number", res.data["error_detail"])
        self.assertIn("11자리 숫자로 구성된 포맷이어야 합니다.", res.data["error_detail"]["phone_number"])

    def test_phone_10_digits_returns_400(self) -> None:
        """10자리 phone_number → 400, phone_number 필드 오류 메시지 확인"""
        res = self._patch({"phone_number": "0101234567"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", res.data)
        self.assertIn("phone_number", res.data["error_detail"])

    def test_invalid_gender_returns_400(self) -> None:
        """유효하지 않은 gender 값 → 400, gender 필드 오류 메시지 확인"""
        res = self._patch({"gender": "X"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", res.data)
        self.assertIn("gender", res.data["error_detail"])


# ── 409 중복 ──────────────────────────────────────────────────────────────────


class AdminAccountUpdateConflictTest(APITestCase):
    """중복 데이터로 인한 409 Conflict 검증"""

    admin: ClassVar[User]
    target: ClassVar[User]
    other: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(role=User.Role.ADMIN)
        cls.target = make_user()
        cls.other = make_user()

    def test_duplicate_phone_returns_409(self) -> None:
        """이미 사용 중인 phone_number → 409 {"error_detail": str}"""
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(
            _url(self.target.pk),
            {"phone_number": self.other.phone_number},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error_detail", res.data)
        self.assertIsInstance(res.data["error_detail"], str)
        self.assertEqual(res.data["error_detail"], "휴대폰 번호 중복으로 인하여 요청 처리에 실패하였습니다.")
