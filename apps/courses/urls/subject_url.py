from django.urls import path

from apps.courses.views.subject_view import SubjectCreateView, SubjectDetailView, SubjectListView

urlpatterns = [
    path("admin/subjects/<int:subject_id>/", SubjectDetailView.as_view(), name="subject_detail"),
    path("courses/<int:course_id>/subjects/", SubjectListView.as_view(), name="subject_list"),
    path("admin/subjects/", SubjectCreateView.as_view(), name="subject_create"),
]
