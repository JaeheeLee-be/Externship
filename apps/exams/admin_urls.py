from django.urls import path

from apps.exams.views.admin_exam_deployment_view import (
    AdminExamDeploymentCreateView,
    AdminExamDeploymentListView,
)
from apps.exams.views.admin_exam_view import ExamListCreateView

urlpatterns = [
    path("deployments/", AdminExamDeploymentCreateView.as_view(), name="exam-deployment"),
    path("deployments/list/", AdminExamDeploymentListView.as_view(), name="exam-deployment-list"),
    path("", ExamListCreateView.as_view(), name="exam-list"),
]
