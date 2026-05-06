from django.urls import path

from apps.users.views.admin_withdrawal_view import AdminWithdrawalListView

urlpatterns = [
    path("withdrawals", AdminWithdrawalListView.as_view(), name="admin-withdrawal-list"),
]
