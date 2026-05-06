from apps.users.models import User
from envs.admin_account_detail.utils.admin_exceptions import AccountNotFoundError


class AdminAccountDetailService:

    @staticmethod
    def get_account_detail(account_id: int) -> User:
        try:
            return (
                User.objects.select_related("withdrawal")
                .prefetch_related("cohort_students__cohort__course")
                .get(pk=account_id)
            )
        except User.DoesNotExist:
            raise AccountNotFoundError()
