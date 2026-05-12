from apps.users.models import User
from apps.users.utils.admin_exceptions import AccountNotFoundError


class AdminAccountDeleteService:

    @staticmethod
    def delete_account(account_id: int) -> int:
        try:
            user = User.objects.get(pk=account_id)
        except User.DoesNotExist:
            raise AccountNotFoundError()

        pk = user.pk
        user.delete()
        return pk
