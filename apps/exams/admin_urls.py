from django.urls import path

from apps.exams.views.admin_exam_deployment_view import AdminExamDeploymentCreateView
from apps.exams.views.admin_exam_view import ExamListCreateView

urlpatterns = [
    path("deployments/", AdminExamDeploymentCreateView.as_view(), name="exam-deployment-create"),
    path("", ExamListCreateView.as_view(), name="exam-list"),
]
