from django.db import models


class AuthPurpose(models.TextChoices):
    SIGNUP = "signup", "회원가입"
    FIND_PASSWORD = "find_password", "비밀번호 찾기"
    RECOVERY = "recovery", "계정복구"
