from apps.users.models import User


class PasswordChangeService:
    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> None:
        if not user.check_password(old_password):
            raise ValueError("현재 비밀번호가 일치하지 않습니다.")
        user.set_password(new_password)
        user.save(update_fields=["password"])
