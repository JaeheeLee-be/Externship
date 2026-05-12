from django.urls import path

from apps.courses.views.course_cohorts_view import (
    CohortAvgScoreView,
    CohortCreateView,
    CohortDetailView,
    CohortStudentListView,
    CourseCohortListView,
)

urlpatterns = [
    path("admin/cohorts", CohortCreateView.as_view(), name="cohort_create"),
    path("courses/<int:course_id>/cohorts", CourseCohortListView.as_view(), name="course_cohort_list"),
    path("admin/cohorts/<int:cohort_id>", CohortDetailView.as_view(), name="cohort_detail"),
    path(
        "admin/courses/<int:course_id>/cohorts/avg-scores",
        CohortAvgScoreView.as_view(),
        name="cohort_avg_scores",
    ),
    path(
        "admin/cohorts/<int:cohort_id>/students",
        CohortStudentListView.as_view(),
        name="cohort_students",
    ),
]
