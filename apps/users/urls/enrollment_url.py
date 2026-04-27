from django.urls import path

from apps.users.views.enrollment_view import EnrollmentView

app_name = "users"

urlpatterns = [
    path("enroll-student", EnrollmentView.as_view(), name="enroll-student"),
]
