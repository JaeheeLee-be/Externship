from django.urls import path

from apps.users.views.social_views import SocialCallbackView, SocialLoginView

urlpatterns = [
    path(
        "social-login/<str:provider>/",
        SocialLoginView.as_view(),
        name="social-login",
    ),
    path(
        "social-login/<str:provider>/callback/",
        SocialCallbackView.as_view(),
        name="social-callback",
    ),
]
