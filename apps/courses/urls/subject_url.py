from django.urls import path

from apps.courses.views.subject_view import SubjectCreateView, SubjectListView

urlpatterns = [
    path("admin/subjects/", SubjectCreateView.as_view(), name="subject_create"),
    path("courses/<int:course_id>/subjects/", SubjectListView.as_view(), name="subject_list"),
]
