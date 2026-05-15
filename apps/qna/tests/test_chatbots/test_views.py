from typing import Any, Iterator, cast
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.http import StreamingHttpResponse
from django.urls import reverse

from apps.core.utils.isolated_cache_testcase import (
    FixedPrefixRedisTestClient,
    IsolatedRedisTestClient,
)
from apps.core.utils.test_factories import MockedAIResponse as Res
from apps.core.utils.test_factories import (
    create_test_category_and_question,
    create_test_user,
)
from apps.qna.chatbot.exceptions import GroqAPIError, GroqTimeoutError
from apps.qna.dtos import InitialQNA
from apps.qna.models import Question
from apps.qna.redis import CacheRepository
from apps.qna.redis.keys import CS_KEY, INITIAL_KEY, QNA_KEY, SESSION_KEY
from apps.qna.services.chatbot_initial_qna import InitialService
from apps.users.models import User


class TestInitialAiAnswerAPIView(IsolatedRedisTestClient):
    question: Question
    user: User
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        _, _, _, cls.question = create_test_category_and_question("gumba")
        cls.user = cls.question.author
        cls.url = reverse("ai_answer", kwargs={"question_id": cls.question.id})

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_res("i am gumba")

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_get_initial_answer_success(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        InitialService.save_initial_answer(self.question.id)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["output"], "i am gumba")
        self.assertEqual(len(response.data), 4)

    def test_get_initial_answer_unauthenticated(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_get_initial_answer_not_found(self) -> None:
        url = reverse("ai_answer", kwargs={"question_id": 9999})
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_initial_answer_success(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["output"], "i am gumba")
        self.assertEqual(len(response.data), 4)

    def test_post_initial_answer_unauthenticated(self) -> None:
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_initial_answer_conflict(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 409)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_internal_server_error(self, mock: MagicMock) -> None:
        mock.side_effect = Exception("서버 오류")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 500)


class TestQNAChatbotAPIViewGetMethod(IsolatedRedisTestClient):
    question: Question
    user: User
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        _, _, _, cls.question = create_test_category_and_question("gumba")
        cls.user = cls.question.author
        cls.url = reverse("qna_chatbot", kwargs={"question_id": cls.question.id})

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_res("i am gumba")
        self.initial = InitialQNA(
            category="top > middle > bottom",
            title="title",
            content="content",
            answer="i am gumba",
            question_id=self.question.id,
            using_model="model",
            created_at="2026-05-04",
        )
        CacheRepository.save_initial(
            key=f"qna_initial:{self.question.id}",
            value=self.initial.__dict__,
            ttl=60,
        )
        CacheRepository.set_session(SESSION_KEY.format(user_id=self.user.id), self.question.id, ttl=60)

    def test_get_unauthenticated(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_get_returns_200_with_history(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)

    def test_get_returns_404_when_no_initial(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/questions/9999/chatbot")
        self.assertEqual(response.status_code, 404)


class TestQNAChatbotAPIViewPostMethod(IsolatedRedisTestClient):
    """
    QNAChatbotAPIView.post 테스트.
    뷰는 내부에서 make_qna_context로 세션/initial/history 검증 후
    response_qna_chat(initial, history, key, message)에 전달함.
    """

    question: Question
    user: User
    url: str
    lines: list[str]

    @classmethod
    def setUpTestData(cls) -> None:
        _, _, _, cls.question = create_test_category_and_question("gumba")
        cls.user = cls.question.author
        cls.url = reverse("qna_chatbot", kwargs={"question_id": cls.question.id})
        cls.lines = Res.make_lines()

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_iter_res(self.lines)

        self.initial = InitialQNA(
            category="top > middle > bottom",
            title="title",
            content="content",
            answer="i am gumba",
            question_id=self.question.id,
            using_model="model",
            created_at="2026-05-04",
        )
        CacheRepository.save_initial(
            key=INITIAL_KEY.format(question_id=self.question.id),
            value=self.initial.__dict__,
            ttl=60,
        )
        CacheRepository.set_session(SESSION_KEY.format(user_id=self.user.id), self.question.id, ttl=60)

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_post_unauthenticated(self) -> None:
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 401)

    def test_post_returns_400_when_message_empty(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": ""})
        self.assertEqual(response.status_code, 400)

    def test_post_returns_400_when_message_missing(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)

    def test_post_returns_400_when_message_too_long(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "a" * 1001})
        self.assertEqual(response.status_code, 400)

    def test_post_returns_403_when_no_session(self) -> None:
        CacheRepository.delete(SESSION_KEY.format(user_id=self.user.id))
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 403)

    def test_post_returns_403_when_session_mismatch(self) -> None:
        # 세션에 다른 question_id가 들어있는 경우
        CacheRepository.set_session(
            key=SESSION_KEY.format(user_id=self.user.id),
            value=99999,
            ttl=60,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 403)

    def test_post_returns_404_when_no_initial(self) -> None:
        CacheRepository.delete(INITIAL_KEY.format(question_id=self.question.id))
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 404)

    def test_post_returns_429_when_history_full(self) -> None:
        CacheRepository.save_history(
            key=QNA_KEY.format(user_id=self.user.id, question_id=self.question.id),
            history=[{"role": "user", "content": f"msg{i}"} for i in range(10)],
            ttl=60,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 429)

    # ---------- 정상 동작 ----------

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_returns_streaming_response(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Content-Type"), "text/event-stream")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_streaming_body(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        assert isinstance(response, StreamingHttpResponse)
        assert isinstance(response.streaming_content, Iterator)
        content = b"".join(response.streaming_content).decode()
        self.assertIn("data:", content)
        self.assertIn("[DONE]", content)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_saves_history_after_streaming(self, mock: MagicMock) -> None:
        """스트리밍이 끝나면 히스토리가 캐시에 저장되어야 함."""
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        assert isinstance(response, StreamingHttpResponse)
        # 스트림 소비
        b"".join(cast(Iterator[bytes], response.streaming_content))

        history = CacheRepository.get_history(QNA_KEY.format(user_id=self.user.id, question_id=self.question.id))
        assert history is not None
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[0].content, "hello")
        self.assertEqual(history[1].role, "assistant")


class TestQNAChatbotListAPIView(FixedPrefixRedisTestClient):
    user: User
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = create_test_user("gumba")
        cls.url = reverse("qna_chatbot_list")

    def setUp(self) -> None:
        super().setUp()
        self.value: list[dict[str, Any]] = [
            {"role": "user", "content": "질문입니다.", "created_at": None},
            {"role": "assistant", "content": "답변입니다.", "created_at": "2026-04-23T14:30:05"},
        ]
        CacheRepository.save_history(f"qna_chat:{self.user.id}:42", self.value, ttl=1800)
        CacheRepository.save_history(f"qna_chat:{self.user.id}:55", self.value, ttl=1800)

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_get_unauthenticated(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_get_returns_200(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_returns_correct_fields(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        item = response.data["results"][0]
        self.assertIn("question_id", item)
        self.assertIn("last_message", item)
        self.assertIn("role", item)
        self.assertIn("created_at", item)

    def test_get_returns_empty_when_no_history(self) -> None:
        cache.clear()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])


class TestCSChatbotAPIViewGetMethod(FixedPrefixRedisTestClient):
    user: User
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = create_test_user("gumba")
        cls.url = reverse("cs_chatbot")

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_res("i am gumba")

    def test_get_returns_empty_list_when_no_history(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])

    def test_get_returns_history(self) -> None:
        CacheRepository.save_history(
            key=CS_KEY.format(user_id=self.user.id),
            history=[{"role": "user", "content": "안녕하세요"}],
            ttl=60,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["role"], "user")
        self.assertEqual(response.data["results"][0]["message"], "안녕하세요")


class TestCSChatbotAPIViewPostMethod(IsolatedRedisTestClient):
    """
    CSChatbotAPIView.post 테스트.
    뷰는 response_cs_chat(user_id, message)를 호출해 첫 청크를 미리 소비하여
    Groq 연결 단계의 예외를 502/504로 변환하고, 나머지는 스트리밍으로 흘림.
    """

    user: User
    url: str
    lines: list[str]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = create_test_user("gumba")
        cls.url = reverse("cs_chatbot")
        cls.lines = Res.make_lines()

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_iter_res(self.lines)

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_post_unauthenticated(self) -> None:
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 401)

    def test_post_returns_400_when_message_empty(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": ""})
        self.assertEqual(response.status_code, 400)

    def test_post_returns_400_when_message_missing(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)

    def test_post_returns_400_when_message_too_long(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "a" * 1001})
        self.assertEqual(response.status_code, 400)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_returns_504_when_groq_timeout(self, mock: MagicMock) -> None:
        mock.side_effect = GroqTimeoutError
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 504)
        self.assertIn("error_detail", response.data)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_returns_502_when_groq_api_error(self, mock: MagicMock) -> None:
        mock.side_effect = GroqAPIError
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 502)
        self.assertIn("error_detail", response.data)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_groq_error_does_not_save_history(self, mock: MagicMock) -> None:
        """Groq 연결 단계에서 실패하면 히스토리가 저장되어선 안 됨."""
        mock.side_effect = GroqAPIError
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url, {"message": "hello"})
        history = CacheRepository.get_history(CS_KEY.format(user_id=self.user.id))
        self.assertIsNone(history)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_returns_streaming_response(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Content-Type"), "text/event-stream")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_streaming_body(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        assert isinstance(response, StreamingHttpResponse)
        assert isinstance(response.streaming_content, Iterator)
        content = b"".join(response.streaming_content).decode()
        self.assertIn("data:", content)
        self.assertIn("[DONE]", content)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_streaming_body_contains_first_chunk(self, mock: MagicMock) -> None:
        """첫 청크가 누락되지 않고 스트림 맨 앞에 포함되어야 함."""
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        assert isinstance(response, StreamingHttpResponse)
        content = b"".join(cast(Iterator[bytes], response.streaming_content)).decode()
        # make_lines()의 첫 토큰은 "I"
        self.assertIn('"message": "I"', content)
        # 마지막 토큰까지 포함
        self.assertIn('"message": "gumba"', content)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_saves_history_after_streaming(self, mock: MagicMock) -> None:
        """스트리밍이 끝나면 user/assistant 메시지가 캐시에 저장되어야 함."""
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        assert isinstance(response, StreamingHttpResponse)
        b"".join(cast(Iterator[bytes], response.streaming_content))

        history = CacheRepository.get_history(CS_KEY.format(user_id=self.user.id))
        assert history is not None
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[0].content, "hello")
        self.assertEqual(history[1].role, "assistant")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_post_appends_to_existing_history(self, mock: MagicMock) -> None:
        """기존 히스토리가 있을 때 새 대화가 누적되어야 함."""
        mock.return_value = self.res
        CacheRepository.save_history(
            key=CS_KEY.format(user_id=self.user.id),
            history=[
                {"role": "user", "content": "이전 질문"},
                {"role": "assistant", "content": "이전 답변"},
            ],
            ttl=60,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "새 질문"})
        assert isinstance(response, StreamingHttpResponse)
        b"".join(cast(Iterator[bytes], response.streaming_content))

        history = CacheRepository.get_history(CS_KEY.format(user_id=self.user.id))
        assert history is not None
        self.assertEqual(len(history), 4)
        self.assertEqual(history[2].role, "user")
        self.assertEqual(history[2].content, "새 질문")
