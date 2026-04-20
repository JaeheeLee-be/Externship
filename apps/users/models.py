from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

from apps.core.models import TimeStampModel


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, name, nickname, phone_number, gender, birthday, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수항목입니다.")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            nickname=nickname,
            phone_number=phone_number,
            gender=gender,
            birthday=birthday,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, name, nickname, phone_number, gender, birthday, **extra_fields):
        user = self.create_user(email, password, name, nickname, phone_number, gender, birthday, **extra_fields)
        user.role = User.Role.ADMIN
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, TimeStampModel):
    class Gender(models.TextChoices):
        MALE = 'male', '남성'
        FEMALE = 'female', '여성'

    class Role(models.TextChoices):
        GENERAL = 'general', '일반수강생'
        ADMIN = 'admin', '관리자'

    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(null=False, unique=True)
    name = models.CharField(max_length=30, null=False)
    nickname = models.CharField(max_length=10, null=False, unique=True)
    phone_number = models.CharField(max_length=20, null=False, unique=True)
    gender = models.CharField(max_length=6, null=True)
    birthday = models.DateField(null=True)
    profile_img_url = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(null=True, default=False)
    role = models.CharField(choices=Role.choices, default=Role.GENERAL)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'nickname', 'phone_number']

    objects = CustomUserManager()

    class Meta:
        db_table = "user"


class SocialUsers(TimeStampModel):
    class Provider(models.TextChoices):
        KAKAO = 'kakao', '카카오'
        NAVER = 'naver', '네이버'

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="social_users")
    provider = models.CharField(max_length=10, choices=Provider.choices)
    provider_id = models.CharField(max_length=10)

    class Meta:
        db_table = "social_users"


class Withdrawal(TimeStampModel):
    class Reason(models.TextChoices):
        INCONVENIENT = 'inconvenient', '서비스 불편'
        PERSONAL = 'personal', '개인 사유'
        OTHER = 'other', '기타'

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    reason = models.CharField(max_length=20, choices=Reason.choices)
    reason_detail = models.TextField()
    due_date = models.DateField()

    class Meta:
        db_table = "withdrawal"


class StudentEnrollmentRequests(TimeStampModel):
    class Status(models.TextChoices):
        END = 'end', '종료됨'
        ONGOING = 'ongoing', '진행중'
        PENDING = 'pending', '대기중'

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollment_requests', null=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, null=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "student_enrollment_requests"


class CohortStudents(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cohort_students', null=False)

    class Meta:
        db_table = "cohort_students"


class OperationManagers(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='operation_managers', null=False)

    class Meta:
        db_table = "operation_managers"


class LearningCoachs(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_coachs', null=False)

    class Meta:
        db_table = "learning_coachs"


class TrainigAssistants(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_assistants', null=False)

    class Meta:
        db_table = "training_assistants"