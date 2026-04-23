
from django.urls import path

from apps.qna.views import answer_views



from apps.qna.views.category_views import AdminCategoryCreateAPIView

urlpatterns = [
    # 답변
    path(
        "qna/questions/<int:question_id>/answers",
        answer_views.AnswerView.as_view(),
        name="question_answers",
    ),


]