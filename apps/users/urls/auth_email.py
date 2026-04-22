from django.urls import path

from apps.users.views.auth_email import EmailSendView, EmailVerificationView

urlpatterns = [
    # 최종 경로: api/v1/accounts/verification/send-email/
    path("verification/send-email/", EmailSendView.as_view(), name="send-email"),
    # 최종 경로: api/v1/accounts/verification/verify-email/
    path("verification/verify-email/", EmailVerificationView.as_view(), name="verify-email"),
]
