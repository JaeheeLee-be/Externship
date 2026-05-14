from django.urls import path

from apps.users.views.admin_account_view import AdminAccountListView
from apps.users.views.admin_detail_view import AdminAccountView
from apps.users.views.admin_permission_view import AdminPermissionView
from apps.users.views.admin_student_enrollment_reject_view import (
    AdminStudentEnrollmentRejectView,
)
from apps.users.views.admin_student_enrollment_view import (
    AdminEnrollmentRequestListView,
)
from apps.users.views.admin_student_list_view import AdminStudentListView
from apps.users.views.admin_withdrawal_view import (
    AdminWithdrawalDetailView,
    AdminWithdrawalListView,
)
from apps.users.views.enrollment_accept_view import AdminStudentEnrollmentAcceptView

urlpatterns = [
    path("accounts", AdminAccountListView.as_view(), name="admin-account-list"),
    path("accounts/<int:account_id>", AdminAccountView.as_view(), name="admin-account-detail"),
    path(
        "student-enrollments/accept", AdminStudentEnrollmentAcceptView.as_view(), name="admin-student-enrollment-accept"
    ),
    path(
        "student-enrollments/reject", AdminStudentEnrollmentRejectView.as_view(), name="admin-student-enrollment-reject"
    ),
    path("accounts/<int:account_id>/role", AdminPermissionView.as_view(), name="admin_permission"),
    path("withdrawals", AdminWithdrawalListView.as_view(), name="admin-withdrawal-list"),
    path("student-enrollments", AdminEnrollmentRequestListView.as_view(), name="student-enrollment-list"),
    path("withdrawals/<int:withdrawal_id>", AdminWithdrawalDetailView.as_view(), name="admin-withdrawal-detail"),
    path("students", AdminStudentListView.as_view(), name="admin-students-list"),
]
