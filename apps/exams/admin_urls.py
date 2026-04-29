from django.urls import path

from apps.core.presigned_url.views import PresignedUrlView
from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.views.admin_exam_deployment_view import AdminExamDeploymentView
from apps.exams.views.admin_exam_view import (
    ExamDetailView,
    ExamListCreateView,
)


class ExamImageUploadView(PresignedUrlView):
    path = "uploads/exams/thumbnails"
    permission_classes = [IsRoleAdminUser]


urlpatterns = [
    path("deployments/", AdminExamDeploymentView.as_view(), name="exam-deployment"),
    path("presigned-url/", ExamImageUploadView.as_view(), name="presigned-url"),
    path("<int:exam_id>/", ExamDetailView.as_view(), name="exam-detail"),
    path("", ExamListCreateView.as_view(), name="exam-list"),
]