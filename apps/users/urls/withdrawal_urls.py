from django.urls import path

from apps.users.views.withdrawal_view import RestoreView, WithdrawalView

urlpatterns = [
    path("me", WithdrawalView.as_view(), name="withdrawal"),
    path("restore", RestoreView.as_view(), name="restore"),
]
