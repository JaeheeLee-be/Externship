from django.urls import include, path

from apps.users.views.auth_email_view import EmailSendView, EmailVerificationView


urlpatterns = [
    # 최종 경로: api/v1/accounts/verification/send-email
    path("accounts/verification/send-email", EmailSendView.as_view(), name="send-email"),
    # 최종 경로: api/v1/accounts/verification/verify-email
    path("accounts/verification/verify-email", EmailVerificationView.as_view(), name="verify-email"),
    # 최종 경로: api/v1/accounts/verification/send-email
]
