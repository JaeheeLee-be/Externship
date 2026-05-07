from __future__ import annotations

from typing import ClassVar

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User


def create_user(
    email: str,
    nickname: str,
    phone_number: str,
    role: str = User.Role.USER,
    is_active: bool = True,
) -> User:
    return User.objects.create_user(
        email=email,
        password="Test1234!@",
        name="홍길동",
        nickname=nickname,
        phone_number=phone_number,
        role=role,
        is_active=is_active,
    )


class AdminAccountPatchTest(APITestCase):
    """PATCH 회원 정보 수정 API"""

    admin: ClassVar[User]
    target: ClassVar[User]
    other: ClassVar[User]
    normal_user: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = create_user("admin@oz.com", "관리자", "01000000000", role=User.Role.ADMIN)
        cls.target = create_user("user@oz.com", "수정대상", "01011111111")
        cls.other = create_user("other@oz.com", "다른유저", "01099999999")
        cls.normal_user = create_user("normal@oz.com", "일반유저", "01088888888")

    def _url(self, pk: int) -> str:
        return reverse("admin-account-update", kwargs={"account_id": pk})

    # ── 인증 / 권한 ──────────────────────────────────────────
    def test_unauthenticated_returns_401(self) -> None:
        res = self.client.patch(self._url(self.target.pk), {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_401_error_message(self) -> None:
        """401 응답 본문에 한국어 에러 메세지가 정상 출력되는지 확인"""
        res = self.client.patch(self._url(self.target.pk), {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", res.data)
        self.assertEqual(res.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    def test_non_admin_returns_403(self) -> None:
        self.client.force_authenticate(user=self.normal_user)
        res = self.client.patch(self._url(self.target.pk), {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ── 404 ──────────────────────────────────────────────────
    def test_not_found_returns_404(self) -> None:
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(self._url(99999), {"nickname": "새닉"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", res.data)
        self.assertEqual(res.data["error_detail"], "사용자 정보를 찾을 수 없습니다.")

    # ── 정상 수정 (200) ───────────────────────────────────────
    def test_patch_nickname_returns_200(self) -> None:
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(self._url(self.target.pk), {"nickname": "새닉네임"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["nickname"], "새닉네임")

    def test_patch_response_exact_fields(self) -> None:
        """응답 필드 명세와 정확히 일치"""
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(self._url(self.target.pk), {"name": "김철수"}, format="json")
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
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(self._url(self.target.pk), {"name": "이영희"}, format="json")
        self.assertIn("updated_at", res.data)

    # ── 400 검증 오류 ─────────────────────────────────────────
    def test_invalid_phone_format_returns_400(self) -> None:
        """phone_number 형식 오류 → 400 {"error_detail": {"phone_number": ["..."]}}
        validate_phone_number 가 serializers.ValidationError 를 raise 하므로
        is_valid() 가 False 를 반환하고 view 에서 req_serializer.errors 를 그대로 반환.
        명세: {"error_detail": {"phone_number": ["11자리 숫자로 구성된 포맷이어야 합니다."]}}
        """
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(
            self._url(self.target.pk),
            {"phone_number": "010-1234-5678"},  # 하이픈 포함 → 오류
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", res.data)
        self.assertIn("phone_number", res.data["error_detail"])
        self.assertIn("11자리 숫자로 구성된 포맷이어야 합니다.", res.data["error_detail"]["phone_number"])

    def test_phone_10_digits_returns_400(self) -> None:
        """10자리 phone_number → 400, phone_number 필드 오류 메시지 확인"""
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(
            self._url(self.target.pk),
            {"phone_number": "0101234567"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", res.data)
        self.assertIn("phone_number", res.data["error_detail"])

    def test_invalid_gender_returns_400(self) -> None:
        """잘못된 gender 값 → 400 {"error_detail": {"gender": ["..."]}}
        gender 는 DRF ChoiceField 기본 검증 실패 → serializers.ValidationError 발생.
        is_valid() 가 False 를 반환하고 view 에서 {"error_detail": req_serializer.errors} 로 응답.
        따라서 error_detail 은 {"gender": [...]} 형태의 dict 이다.
        """형태의 dict 이다.
        """
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(
            self._url(self.target.pk),
            {"gender": "X"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", res.data)
        self.assertIn("gender", res.data["error_detail"])

    # ── 409 중복 ──────────────────────────────────────────────
    def test_duplicate_phone_returns_409(self) -> None:
        """이미 사용 중인 phone_number → 409 {"error_detail": str}"""
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(
            self._url(self.target.pk),
            {"phone_number": self.other.phone_number},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error_detail", res.data)
        self.assertIsInstance(res.data["error_detail"], str)
        self.assertEqual(res.data["error_detail"], "휴대폰 번호 중복으로 인하여 요청 처리에 실패하였습니다.")
