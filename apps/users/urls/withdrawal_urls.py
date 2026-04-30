from django.urls import path

from apps.users.views.withdrawal_view import (
    RestoreView,
    WithdrawalView,
)

urlpatterns = [
    # WithdrawalView는 UserInfoView를 상속하므로 GET/PATCH/DELETE 모두 처리
    # __init__.py에서 enrollment_url보다 먼저 include되어 'me' 경로 우선 매칭
    path("me", WithdrawalView.as_view(), name="withdrawal"),
    path("restore", RestoreView.as_view(), name="restore"),
]
