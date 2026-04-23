from django.urls import include, path

from apps.qna.views import answer_views

urlpatterns = [
    # 답변
    path(
        "qna/questions/<int:question_id>/answers",
        answer_views.AnswerView.as_view(),
        name="question_answers",
    ),
]
