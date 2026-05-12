from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

from apps.qna.serializers.admin_question_serializers import (
    AdminQuestionDeleteResponseSerializer,
)

# ── 어드민 질문 삭제 ──────────────────────────────────────────────────

admin_question_delete_schema = extend_schema(
    tags=["Admin - Qna"],
    summary="어드민 질의응답 삭제",
    description="관리자가 질의응답을 삭제합니다. 연관된 답변과 댓글도 함께 삭제됩니다.",
    parameters=[
        OpenApiParameter(
            name="question_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="질문 ID",
            required=True,
        ),
    ],
    responses={
        200: AdminQuestionDeleteResponseSerializer,
        400: OpenApiResponse(description="유효하지 않은 삭제 요청입니다."),
        401: OpenApiResponse(description="로그인이 필요합니다."),
        403: OpenApiResponse(description="질의응답 삭제 권한이 없습니다."),
        404: OpenApiResponse(description="삭제할 질문을 찾을 수 없습니다."),
    },
)
