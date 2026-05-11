from django.urls import path

from apps.users.views.find_email_view import FindEmailView

urlpatterns = [
    path("find-email", FindEmailView.as_view(), name="find_email"),
]
