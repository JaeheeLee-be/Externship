from django.db import models


class AuthPurpose(models.TextChoices):
    SIGNUP = "signup", "회원가입"
    FIND_PASSWORD = "find_password", "비밀번호 찾기"
    RECOVERY = "recovery", "계정복구"


class SmsPurpose(models.TextChoices):
    SIGNUP = "signup", "회원가입"
    FIND_EMAIL = "find_email", "이메일 찾기"
    PHONE_CHANGE = "phone_change", "휴대폰 변경"
