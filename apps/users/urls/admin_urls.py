from django.urls import path

from apps.users.views.admin_account_view import AdminAccountListView
from apps.users.views.admin_detail_view import AdminAccountDetailView
from apps.users.views.enrollment_accept_view import AdminStudentEnrollmentAcceptView
from apps.users.views.admin_permission_view import AdminPermissionView
from apps.users.views.admin_update_view import AdminAccountUpdateView
from apps.users.views.enrollment_accept_view import AdminStudentEnrollmentAcceptView

urlpatterns = [
    path("accounts", AdminAccountListView.as_view(), name="admin-account-list"),
    path("accounts/<int:account_id>", AdminAccountDetailView.as_view(), name="admin-account-detail"),
    path("accounts/<int:account_id>", AdminAccountUpdateView.as_view(), name="admin-account-update"),
    path("student-enrollments/accept", AdminStudentEnrollmentAcceptView.as_view(), name="admin-student-enrollment-accept"),
    path("accounts/<int:account_id>/role", AdminPermissionView.as_view(), name="admin_permission"),

]
