from django.urls import path, include

from apps.qna.views import answer_views

urlpatterns = [
    # 답변
    path(
        "qna/questions/<int:question_id>/answers",
        answer_views.AnswerView.as_view(),
        name="question_answers",
    ),

    path("admin/qna/", include("apps.qna.urls.admin_urls")),
]