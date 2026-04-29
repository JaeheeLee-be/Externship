from django.urls import include, path

app_name = "users"

urlpatterns = [
    path("accounts/", include("apps.users.urls.account_url")),
    path("", include("apps.users.urls.social_url")),
    path("", include("apps.users.urls.enrollment_url")),
    path("accounts/", include("apps.users.urls.profile_image_urls")),
]
