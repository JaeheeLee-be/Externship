from apps.qna.models.answer_models import Answer
from rest_framework.exceptions import NotFound

class AdminAnswerDeleteService:
    """
    관리자만 가능 -> 답변 삭제에 대한 service 로직
    """
    def get_object(self,answer_id:int):
        try:
            return Answer.objects.get(pk=answer_id)
        except Answer.DoesNotExist:
            raise NotFound("삭제할 답변을 찾을 수 없습니다.")

    def delete(self,answer_id:int)->dict:
        answer = self.get_object(answer_id)
        deleted_comment_count = answer.answercomment_set.count()
        answer.delete()
        return {"answer_id":answer_id,"deleted_comment_count":deleted_comment_count}
