from django.urls import path

from apps.users.views.admin_account_view import AdminAccountListView

urlpatterns = [
    path("accounts", AdminAccountListView.as_view(), name="admin-account-list"),
]
