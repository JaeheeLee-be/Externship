from drf_spectacular.utils import extend_schema,OpenApiResponse
from apps.qna.serializers.answer_serializers import AnswerAcceptResponseSerializer,AnswerResponseSerializer,AnswerRequestSerializer

answer_accept_schema = extend_schema(
    tags=["Qna"],
    summary="답변 채택",
    description="질문 작성자가 답변을 채택합니다",
    responses={
        200: AnswerAcceptResponseSerializer,
        401: OpenApiResponse(description="로그인한 사용자만 채택할 수 있습니다."),
        403: OpenApiResponse(description="본인의 질문에 대한 답변만 채택할 수 있습니다."),
        404: OpenApiResponse(description="해당 갑변을 찾을 수 없습니다."),
    }
)

answer_create_schema = extend_schema(
    tags=["Qna"],
    summary="답변 등록",
    description="질문에 대한 답변을 등록합니다.",
    request = AnswerRequestSerializer,
    responses = {
        201:AnswerResponseSerializer,
        400: OpenApiResponse(description="잘못된 요청 입니다."),
        401: OpenApiResponse(description="로그인한 사용자만 채택할 수 있습니다."),
        403: OpenApiResponse(description="관리자가 아닙니다."),
        404: OpenApiResponse(description="찾을 수 없는 질문 입니다."),
    }
)