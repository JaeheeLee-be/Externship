from django.urls import path

from apps.exams.views.user_exam_submission_view import UserExamSubmissionGetView

urlpatterns = [
    path("submissions/<int:submission_id>", UserExamSubmissionGetView.as_view(), name="user-exam-submission-get"),
]
