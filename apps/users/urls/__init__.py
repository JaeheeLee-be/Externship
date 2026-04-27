from django.urls import include, path

app_name = "users"

urlpatterns = [
    path("", include("apps.users.urls.auth_email_url")),
    path("", include("apps.users.urls.social_url")),
    path("", include("apps.users.urls.enrollment_url")),
    path("", include("apps.users.urls.profile_image_urls")),
path("", include("apps.users.urls.auth_sms_url")),
]
