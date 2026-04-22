from django.urls import include, path

app_name = "users"

urlpatterns = [
    # api/v1/accounts/verification/ 으로 시작하는 주소는 email_urls.py로 토스
    path("verification/", include("apps.users.urls.auth_email")),
]
