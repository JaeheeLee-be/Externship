from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("", include("apps.posts.urls.post_crud_url")),
    path("", include("apps.posts.urls.post_comment_url")),
    path("", include("apps.posts.urls.post_like_url")),
    path("", include("apps.posts.urls.post_category_urls")),
    path("", include("apps.posts.urls.post_presigned_url_urls")),
    path("", include("apps.posts.urls.notification_url")),
]
