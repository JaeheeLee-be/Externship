from apps.users.models import User


def update_profile_image(user: User, profile_img_url: str | None) -> None:
    user.profile_img_url = profile_img_url
    user.save(update_fields=["profile_img_url"])
