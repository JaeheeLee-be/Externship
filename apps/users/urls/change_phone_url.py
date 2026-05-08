from django.urls import path

from apps.users.views.change_phone_view import ChangePhoneView

urlpatterns = [
    path("change-phone", ChangePhoneView.as_view(), name="change-phone"),
]
