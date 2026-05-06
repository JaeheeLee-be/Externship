from django.urls import path

from apps.users.views.admin_account_view import AdminAccountListView
from apps.users.views.admin_detail_view import AdminAccountDetailView

urlpatterns = [
    path("accounts", AdminAccountListView.as_view(), name="admin-account-list"),

    path("accounts/<int:account_id>", AdminAccountDetailView.as_view(), name="admin-account-detail"),


]
