import json
from unittest.mock import MagicMock

from apps.qna.models import Question, QuestionCategory
from apps.users.models import User

_test_user_counter = 0


def create_test_user(suffix: str) -> User:
    global _test_user_counter
    _test_user_counter += 1
    return User.objects.create_user(
        email=f"{suffix}@example.com",
        password="pw1234",
        name=f"{suffix} name",
        nickname=suffix[:10],
        phone_number=f"010{_test_user_counter:08d}",
    )


def create_test_category_and_question(
    author: str, top_name: str = "top", middle_name: str = "middle", bottom_name: str = "bottom"
) -> tuple[QuestionCategory, QuestionCategory, QuestionCategory, Question]:
    top = QuestionCategory.objects.create(name=top_name, parent=None)
    middle = QuestionCategory.objects.create(name=middle_name, parent=top)
    bottom = QuestionCategory.objects.create(name=bottom_name, parent=middle)
    question = Question.objects.create(
        author=create_test_user(author),
        category=bottom,
        title="title",
        content="content",
    )
    return top, middle, bottom, question


class MockedAIResponse:

    @staticmethod
    def make_lines() -> list[str]:
        return [
            MockedAIResponse.make_line("I"),
            MockedAIResponse.make_line(" "),
            MockedAIResponse.make_line("am"),
            MockedAIResponse.make_line(" "),
            MockedAIResponse.make_line("gumba"),
            "data: [DONE]",
        ]

    @staticmethod
    def make_line(content: str) -> str:
        return "data: " + json.dumps({"choices": [{"delta": {"content": content}}]})

    @staticmethod
    def make_iter_res(lines: list[str]) -> MagicMock:
        res = MagicMock()
        res.iter_lines.return_value = iter(lines)
        res.__enter__.return_value = res
        res.__exit__.return_value = False
        return res

    @staticmethod
    def make_res(content: str) -> MagicMock:
        res = MagicMock()
        res.json.return_value = {"choices": [{"message": {"content": content}}]}
        res.__enter__.return_value = res
        res.__exit__.return_value = False
        return res
