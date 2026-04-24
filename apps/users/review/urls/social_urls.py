from django.urls import path

from apps.users.views.social_views import SocialCallbackView, SocialLoginView

app_name = "users"

urlpatterns = [
    # GET /api/v1/accounts/social-login/<provider>/
    # 302 → 카카오·네이버 OAuth 인증 페이지
    path(
        "social-login/<str:provider>/",
        SocialLoginView.as_view(),
        name="social-login",
    ),
    # GET /api/v1/accounts/social-login/<provider>/callback/
    # 성공: 200 JSON {"is_new_user": bool, "access": str} + refresh HttpOnly 쿠키
    # 실패: 400 / 500 JSON {"detail": str}
    path(
        "social-login/<str:provider>/callback/",
        SocialCallbackView.as_view(),
        name="social-callback",
    ),
]
