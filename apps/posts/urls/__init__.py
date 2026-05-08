from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("", include("apps.posts.urls.post_crud")),
    path("", include("apps.posts.urls.comment_url")),
    path("", include("apps.posts.urls.like")),
    path("", include("apps.posts.urls.categories_url")),
]
