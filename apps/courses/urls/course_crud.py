from django.urls import path

from apps.courses.views.course_crud import (
    AdminCourseCreateView,
    AdminCourseDetailView,
    CourseListView,
)

urlpatterns = [
    path("course/", CourseListView.as_view(), name="course-list"),
    path("admin/courses/", AdminCourseCreateView.as_view(), name="admin-course-create"),
    path("admin/courses/<int:course_id>/", AdminCourseDetailView.as_view(), name="admin-course-detail"),
]
