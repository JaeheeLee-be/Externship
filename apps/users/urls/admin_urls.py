from django.urls import path

from apps.users.views.admin_account_view import AdminAccountListView
from apps.users.views.admin_detail_view import AdminAccountDetailView
from apps.users.views.admin_update_view import AdminAccountUpdateView

urlpatterns = [
    path("accounts", AdminAccountListView.as_view(), name="admin-account-list"),
    path("accounts/<int:account_id>", AdminAccountDetailView.as_view(), name="admin-account-detail"),
    path("accounts/<int:account_id>/update", AdminAccountUpdateView.as_view(), name="admin-account-update"),
]
