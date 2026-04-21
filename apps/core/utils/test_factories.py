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
