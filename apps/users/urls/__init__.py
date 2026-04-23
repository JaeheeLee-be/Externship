from django.urls import path

from apps.users.views.social_views import (
    KakaoCallbackView,
    KakaoLoginView,
    NaverCallbackView,
    NaverLoginView,
)

app_name = "users"  # ← 이게 있어야 해요

urlpatterns = [
    path("social-login/kakao", KakaoLoginView.as_view(), name="kakao-login"),
    path("social-login/kakao/callback", KakaoCallbackView.as_view(), name="kakao-callback"),
    path("social-login/naver", NaverLoginView.as_view(), name="naver-login"),
    path("social-login/naver/callback", NaverCallbackView.as_view(), name="naver-callback"),
]
