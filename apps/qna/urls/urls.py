from django.urls import path

from apps.qna.views import answer_views, chatbot_views
from apps.qna.views.category_views import CategoryListAPIView
from apps.qna.views.question_views import QuestionAPIView, QuestionDetailAPIView

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
    # 질문
    path("questions", QuestionAPIView.as_view(), name="questions"),
    path("questions/<int:question_id>", QuestionDetailAPIView.as_view(), name="question_detail"),
    # 챗봇
    path("questions/<int:question_id>/ai-answer", chatbot_views.InitialAiAnswerAPIView.as_view(), name="ai_answer"),
    path("questions/<int:question_id>/chatbot", chatbot_views.QNAChatbotAPIView.as_view(), name="qna_chatbot"),
    path("ai-answer/sessions", chatbot_views.QNAChatbotListAPIView.as_view(), name="qna_chatbot_list"),
    path("chatbot/completions", chatbot_views.CSChatbotAPIView.as_view(), name="cs_chatbot"),
]
