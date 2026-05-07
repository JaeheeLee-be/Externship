from django.urls import include, path

from apps.qna.views import answer_views
from apps.qna.views.category_views import CategoryListAPIView

urlpatterns = [
    # 답변
    path(
        "questions/<int:question_id>/answers",
        answer_views.AnswerView.as_view(),
        name="question_answers",
    ),
    path(
        "answers/<int:answer_id>/accept",
        answer_views.AnswerAcceptView.as_view(),
        name="answer_accept",
    ),
    path(
        "answers/presigned-url",
        answer_views.AnswerPresignedUrlView.as_view(),
        name="answer_presigned_url",
    ),
    path(
        "answers/<int:answer_id>",
        answer_views.AnswerDetail.as_view(),
        name="answers_detail",
    ),
    path(
        "answers/<int:answer_id>/comments",
        answer_views.AnswerCommentView.as_view(),
        name="answer_comments",
    ),
    # 카테고리
    path("categories", CategoryListAPIView.as_view(), name="category-list"),
]
