from django.urls import path

from apps.core.presigned_url.views import PresignedUrlView
from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.views.admin_exam_deployment_view import AdminExamDeploymentView
from apps.exams.views.admin_exam_view import ExamListCreateView


class ExamImageUploadView(PresignedUrlView):
    path = "uploads/exams/thumbnails"
    permission_classes = [IsRoleAdminUser]


urlpatterns = [
    path("deployments/", AdminExamDeploymentView.as_view(), name="exam-deployment"),
    path("presigned-url/", ExamImageUploadView.as_view(), name="presigned-url"),
    path("", ExamListCreateView.as_view(), name="exam-list"),
]