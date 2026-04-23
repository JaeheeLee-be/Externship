from django.db import models


class AuthPurpose(models.TextChoices):
    SIGNUP = "signup"
    FIND_PASSWORD = "find_password"
    RECOVERY = "recovery"
