from django.urls import path
from drf_spectacular.utils import extend_schema

from apps.core.presigned_url.views import PresignedUrlView
from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.views.admin_exam_deployment_view import (
    AdminExamDeploymentDetailView,
    AdminExamDeploymentView,
)
from apps.exams.views.admin_exam_question_view import (
    AdminQuestionCreateView,
    AdminQuestionUpdateDeleteView,
)
from apps.exams.views.admin_exam_view import ExamDetailView, ExamListCreateView


@extend_schema(tags=["admin-exams"])
class ExamImageUploadView(PresignedUrlView):
    path = "uploads/exams/thumbnails"
    permission_classes = [IsRoleAdminUser]


urlpatterns = [
    path("deployments/", AdminExamDeploymentView.as_view(), name="exam-deployment"),
    path("deployments/<str:deployment_id>/", AdminExamDeploymentDetailView.as_view(), name="exam-deployment-detail"),
    path("presigned-url/", ExamImageUploadView.as_view(), name="presigned-url"),
    path("<int:exam_id>/questions/", AdminQuestionCreateView.as_view(), name="exam-question-create"),
    path("questions/<int:question_id>/", AdminQuestionUpdateDeleteView.as_view(), name="exam-question-update-delete"),
    path("<int:exam_id>/", ExamDetailView.as_view(), name="exam-detail"),
    path("", ExamListCreateView.as_view(), name="exam-list"),
]
