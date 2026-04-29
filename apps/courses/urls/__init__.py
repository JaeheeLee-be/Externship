from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("", include("apps.courses.urls.url_subject")),
]
