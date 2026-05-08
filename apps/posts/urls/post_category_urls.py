from django.urls import path

from apps.posts.views.post_category_view import PostCategoryListView

urlpatterns = [path("categories", PostCategoryListView.as_view(), name="post_category_list")]
