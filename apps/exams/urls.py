from django.urls import path

from apps.exams.views.exam_deployment_view import (
    ExamDeploymentCheckCodeView,
    ExamDeploymentDetailView,
    ExamDeploymentListView,
    ExamDeploymentStatusView,
)

urlpatterns = [
    path("deployments/", ExamDeploymentListView.as_view(), name="deployment"),
    path("deployments/<int:deployment_id>/check-code/", ExamDeploymentCheckCodeView.as_view(), name="deployment-code"),
    path("deployments/<int:deployment_id>/", ExamDeploymentDetailView.as_view(), name="deployment-detail"),
    path("deployments/<int:deployment_id>/status/", ExamDeploymentStatusView.as_view(), name="deployment-status"),
]
