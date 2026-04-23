from django.urls import path

from apps.users.views.restore_view import RestoreRequestView, RestoreView
from apps.users.views.withdrawal_view import WithdrawalView

urlpatterns = [
    path("me", WithdrawalView.as_view(), name="withdrawal"),
    path("recover/request", RestoreRequestView.as_view(), name="restore-request"),
    path("recover", RestoreView.as_view(), name="restore"),
]
