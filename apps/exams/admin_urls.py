from django.urls import path

from apps.exams.views.admin_exam_deployment_view import AdminExamDeploymentCreateView
from apps.exams.views.admin_exam_view import ExamListCreateView
from apps.exams.views.exam_presigned_url_view import ExamPresignedUrlView

urlpatterns = [
    path("deployments/", AdminExamDeploymentCreateView.as_view(), name="exam-deployment-create"),
    path("presigned-url", ExamPresignedUrlView.as_view(), name="presigned-url"),
    path("", ExamListCreateView.as_view(), name="exam-list"),
]
