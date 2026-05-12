from django.urls import path

from apps.users.views.find_password_view import FindPasswordView

urlpatterns = [
    path("find_password", FindPasswordView.as_view(), name="find_password"),
]
