from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)

from apps.qna.serializers.question_serializers import (
    QuestionCreateResponseSerializer,
    QuestionCreateSerializer,
)

# ── 질문 등록 ──────────────────────────────────────────────────────

question_create_schema = extend_schema(
    tags=["Qna"],
    summary="질문 등록",
    description="새로운 질문을 등록합니다. 소분류 카테고리만 선택 가능합니다.",
    request=QuestionCreateSerializer,
    responses={
        201: QuestionCreateResponseSerializer,
        400: OpenApiResponse(description="유효하지 않은 질문 등록 요청입니다."),
        401: OpenApiResponse(description="로그인한 수강생만 질문을 등록할 수 있습니다."),
        403: OpenApiResponse(description="질문 등록 권한이 없습니다."),
    },
)
