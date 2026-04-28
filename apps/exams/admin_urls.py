from django.urls import path

from apps.core.presigned_url.views import PresignedUrlView
from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.views.admin_exam_deployment_view import (
    AdminExamDeploymentCreateView,
    AdminExamDeploymentListView,
)
from apps.exams.views.admin_exam_view import ExamDetailView, ExamListCreateView


class ExamImageUploadView(PresignedUrlView):
    path = "uploads/exams/thumbnails"
    permission_classes = [IsRoleAdminUser]


urlpatterns = [
    path("deployments/", AdminExamDeploymentCreateView.as_view(), name="exam-deployment-create"),
    path("deployments/list/", AdminExamDeploymentListView.as_view(), name="exam-deployment-list"),
    path("presigned-url", ExamImageUploadView.as_view(), name="presigned-url"),
    path("", ExamListCreateView.as_view(), name="exam-list"),
    path("<int:exam_id>", ExamDetailView.as_view(), name="exam-detail"),
]

