import json
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase

from apps.core.utils.test_factories import MockedAIResponse as Res
from apps.qna.chatbot.clients.groq import call_groq, call_groq_once
from apps.qna.chatbot.exceptions import GroqAPIError, GroqTimeoutError

"""실제 groq api 요청을 보내는 테스트입니다."""
# class TestRealCall(TestCase):
#
#     @classmethod
#     def setUpTestData(cls):
#         from django.conf import settings
#         from apps.qna.chatbot import GroqPayloadFactory
#         from apps.qna.chatbot import QNA_PROMPT
#         from apps.qna.chatbot import GROQ_MODEL
#         from apps.qna.chatbot.questions.questions import questions
#         cls.key = settings.GROQ_API_KEY
#         cls.payloads = [
#             GroqPayloadFactory.create_payload(
#                 prompt=QNA_PROMPT,
#                 message=question,
#                 model=GROQ_MODEL["gpt_120"]
#             ) for question in questions["off_topic1"]
#         ]
#
#     def test_call_groq(self):
#         for i, payload in enumerate(self.payloads):
#                 print(i+1, "==" * 20)
#                 for chunk in call_groq(payload.api(), self.key):
#                     print(chunk, flush=True, end="")
#                 print()

# class TestRealCallOnce(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         from django.conf import settings
#         from apps.qna.chatbot import GroqPayloadFactory
#         from apps.qna.chatbot import QNA_PROMPT
#         from apps.qna.chatbot import GROQ_MODEL
#         from apps.qna.chatbot.questions.questions import questions
#         cls.key = settings.GROQ_API_KEY
#         cls.payloads = [
#             GroqPayloadFactory.create_initial_payload(
#                 prompt=QNA_PROMPT,
#                 category="python",
#                 title="파이썬이 뭐야",
#                 message=question,
#                 model=GROQ_MODEL["gpt_120"]
#             ) for question in questions["off_topic1"]
#         ]
#
#     def test_call_groq_once(self):
#         for i, payload in enumerate(self.payloads):
#             print(i+1, "=="*20)
#             print(call_groq_once(payload.api(), self.key), flush=True)
#             print()


class TestCallGroq(TestCase):
    lines: list[str]
    payload: dict[str, str]
    key: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.lines = Res.make_lines()
        cls.payload = {"test": "test"}
        cls.key = "groq_api_key"

    def setUp(self) -> None:
        self.res = Res.make_iter_res(self.lines)

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_correct(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        text = ""
        for chunk in call_groq(self.payload, self.key):
            text += chunk
        self.assertEqual(text, "I am gumba")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_skips_empty_line(self, mock: MagicMock) -> None:
        lines = ["", Res.make_line("hello"), "data: [DONE]"]
        mock.return_value = Res.make_iter_res(lines)
        text = ""
        for chunk in call_groq(self.payload, self.key):
            text += chunk
        self.assertEqual(text, "hello")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_stop_at_done(self, mock: MagicMock) -> None:
        lines = [Res.make_line("hello"), "data: [DONE]", Res.make_line("world")]
        mock.return_value = Res.make_iter_res(lines)
        text = ""
        for chunk in call_groq(self.payload, self.key):
            text += chunk
        self.assertEqual(text, "hello")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_skips_invalid_json(self, mock: MagicMock) -> None:
        lines = ["data: not-json", Res.make_line("valid")]
        mock.return_value = Res.make_iter_res(lines)
        text = ""
        for chunk in call_groq(self.payload, self.key):
            text += chunk
        self.assertEqual(text, "valid")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_skips_with_invalid_key(self, mock: MagicMock) -> None:
        invalid_key = json.dumps({"invalid_key": "invalid"})
        lines = [f"data: {invalid_key}", Res.make_line("test")]
        mock.return_value = Res.make_iter_res(lines)
        text = ""
        for chunk in call_groq(self.payload, self.key):
            text += chunk
        self.assertEqual(text, "test")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_skips_with_invalid_index(self, mock: MagicMock) -> None:
        invalid_index = json.dumps({"choices": []})
        lines = [f"data: {invalid_index}", Res.make_line("test")]
        mock.return_value = Res.make_iter_res(lines)
        text = ""
        for chunk in call_groq(self.payload, self.key):
            text += chunk
        self.assertEqual(text, "test")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_http_error_raise_groq_api_error(self, mock: MagicMock) -> None:
        mock.side_effect = requests.HTTPError()
        with self.assertRaises(GroqAPIError):
            list(call_groq(self.payload, self.key))

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_connection_error_raise_groq_api_error(self, mock: MagicMock) -> None:
        self.res.raise_for_status.side_effect = requests.HTTPError()
        mock.return_value = self.res
        with self.assertRaises(GroqAPIError):
            list(call_groq(self.payload, self.key))

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_timeout_error_raise_groq_timeout_error(self, mock: MagicMock) -> None:
        mock.side_effect = requests.Timeout()
        with self.assertRaises(GroqTimeoutError):
            list(call_groq(self.payload, self.key))


class TestCallGroqOnce(TestCase):

    def setUp(self) -> None:
        self.key = "key"
        self.payload = {"payload": "payload"}
        self.res = Res.make_res("i am gumba")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_correct(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        self.assertEqual("i am gumba", call_groq_once(self.payload, self.key))
