from django.urls import path

from apps.qna.views.category_views import AdminCategoryCreateAPIView

urlpatterns = [
    # 어드민 카테고리
    path(
        "categories",
        AdminCategoryCreateAPIView.as_view(),
        name="admin-category-create",
    ),
]
