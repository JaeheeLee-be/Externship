from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("", include("apps.posts.urls.post_crud_urls")),
    path("", include("apps.posts.urls.presigned_url_urls")),
]
