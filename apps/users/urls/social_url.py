from django.urls import path

from apps.users.views.social_views import SocialCallbackView, SocialLoginView



urlpatterns = [
    # 302 → 카카오·네이버 OAuth 인증 페이지
    path(
        "social-login/<str:provider>/",
        SocialLoginView.as_view(),
        name="social-login",
    ),
    # 성공: 302 → {FRONTEND_URL}/social-callback?provider=<provider>&is_success=true&access_token=<JWT>
    #       Set-Cookie: refresh_token=<JWT>; HttpOnly; Secure; SameSite=Lax
    # 실패: 302 → {FRONTEND_URL}/social-callback?provider=<provider>&is_success=false
    path(
        "social-login/<str:provider>/callback/",
        SocialCallbackView.as_view(),
        name="social-callback",
    ),
]
