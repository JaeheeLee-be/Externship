from django.urls import path

from apps.exams.views.admin_exam_deployment_view import AdminExamDeploymentCreateView

urlpatterns = [path("deployments/", AdminExamDeploymentCreateView.as_view(), name="exam-deployment-create")]
