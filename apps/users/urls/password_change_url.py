from django.urls import path

from apps.users.views.password_change_view import PasswordChangeView

urlpatterns = [
    path("change-password", PasswordChangeView.as_view(), name="change-password"),
]
