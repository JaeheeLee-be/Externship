from django.urls import path

from apps.qna.views.admin_category_views import AdminCategoryCreateAPIView
from apps.qna.views.admin_answer_view import AdminAnswerDeleteView

urlpatterns = [
    # 어드민 카테고리
    path(
        "categories",
        AdminCategoryCreateAPIView.as_view(),
        name="admin-category-create",
    ),
    path("answers/<int:answer_id>",AdminAnswerDeleteView.as_view(),name="admin-answer-delete"),
]
