from django.urls import path

from apps.users.views.available_courses_view import AvailableCoursesView
from apps.users.views.enrollment_view import EnrollmentView
from apps.users.views.user_info_view import UserInfoView

urlpatterns = [
    path("enroll-student", EnrollmentView.as_view(), name="enroll-student"),
    path("me", UserInfoView.as_view(), name="me"),
    path("available-courses", AvailableCoursesView.as_view(), name="available-courses"),
]
