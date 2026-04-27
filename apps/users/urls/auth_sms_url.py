from django.urls import include, path

from apps.users.views.auth_sms_view import SmsSendView, SmsVerificationView

urlpatterns = [
    # 최종 경로: api/v1/accounts/verification/send-sms
    path("verification/send-sms", SmsSendView.as_view(), name="send-sms"),
    # 최종 경로: api/v1/accounts/verification/verify-sms
    path("verification/verify-sms", SmsVerificationView.as_view(), name="verify-sms"),
]
