from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.qna.serializers.chatbot_serializers import InitialAIAnswerSerializer

ai_answer_post_schema = extend_schema(
    tags=["Chatbot"],
    summary="AI 초기응답 생성",
    description="질문글을 기준으로 AI가 초기응답을 생성합니다.",
    responses={
        201: InitialAIAnswerSerializer,
        401: OpenApiResponse(description="로그인한 사용자만 요청할 수 있습니다."),
        404: OpenApiResponse(description="질문 데이터를 찾을 수 없습니다."),
        409: OpenApiResponse(description="이미 AI가 답변을 생성했습니다."),
        502: OpenApiResponse(description="외부 API 호출에 실패했습니다."),
        504: OpenApiResponse(description="외부 API 응답 시간이 초과되었습니다."),
    },
)

ai_answer_get_schema = extend_schema(
    tags=["Chatbot"],
    summary="AI 초기응답 조회",
    description="캐시에 저장된 초기응답을 불러옵니다.",
    responses={
        200: InitialAIAnswerSerializer,
        401: OpenApiResponse(description="로그인한 사용자만 요청할 수 있습니다."),
        404: OpenApiResponse(description="질문 데이터를 찾을 수 없습니다."),
        408: OpenApiResponse(description="응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."),
        409: OpenApiResponse(description="이미 AI가 답변을 생성했습니다."),
        502: OpenApiResponse(description="외부 API 호출에 실패했습니다."),
        504: OpenApiResponse(description="외부 API 응답 시간이 초과되었습니다."),
    },
)
