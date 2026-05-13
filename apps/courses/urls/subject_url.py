from django.urls import path

from apps.courses.views.subject_view import (
    SubjectCreateView,
    SubjectDetailView,
    SubjectListView,
    SubjectPresignedUrlView,
)

urlpatterns = [
    path("courses/<int:course_id>/subjects", SubjectListView.as_view(), name="subject_list"),
    path("admin/subjects", SubjectCreateView.as_view(), name="subject_create"),
    path("admin/subjects/<int:subject_id>", SubjectDetailView.as_view(), name="subject_detail"),
    path("subjects/presigned-url", SubjectPresignedUrlView.as_view(), name="subject_presigned_url"),
]
