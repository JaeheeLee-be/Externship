from django.urls import path

from apps.users.views.restore_view import RestoreRequestView, RestoreView
from apps.users.views.withdrawal_view import WithdrawalView

urlpatterns = [
    path("me", WithdrawalView.as_view(), name="withdrawal"),
    path("restore/request", RestoreRequestView.as_view(), name="restore-request"),
    path("restore", RestoreView.as_view(), name="restore"),
]
