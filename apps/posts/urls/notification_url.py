from django.urls import URLPattern, path

from apps.posts.views.notification_view import NotificationView

urlpatterns: list[URLPattern] = [
    path("notifications/", NotificationView.as_view(), name="post_notifications"),
]
