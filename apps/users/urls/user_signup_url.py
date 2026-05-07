from django.urls import path

from apps.users.views.available_courses_view import AvailableCoursesView
from apps.users.views.check_nickname_view import CheckNicknameView
from apps.users.views.enrolled_courses_view import MyCoursesView
from apps.users.views.enrollment_view import EnrollmentView
from apps.users.views.user_info_view import UserInfoView
from apps.users.views.user_signup_view import SignupView

urlpatterns = [
    path("signup", SignupView.as_view(), name="signup"),
    path("enroll-student", EnrollmentView.as_view(), name="enroll-student"),
    path("me", UserInfoView.as_view(), name="me"),
    path("available-courses", AvailableCoursesView.as_view(), name="available-courses"),
    path("me/enrolled-courses", MyCoursesView.as_view(), name="enrolled-courses"),
    path("check-nickname", CheckNicknameView.as_view(), name="check-nickname"),
]