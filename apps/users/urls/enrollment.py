from django.urls import path

from apps.users.views.enrollment import EnrollmentView

urlpatterns = [
    path("enroll-student", EnrollmentView.as_view(), name="enroll-student"),
]
