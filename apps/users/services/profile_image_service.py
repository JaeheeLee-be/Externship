from pathlib import Path

from apps.core.presigned_url.constants import ALLOWED_SUFFIX
from apps.core.presigned_url.services import PresignedUrlService
from apps.users.models import User

PROFILE_IMAGE_S3_PATH = "uploads/images/profiles"


def generate_profile_presigned_url(file_name: str) -> dict[str, str]:

    content_type = ALLOWED_SUFFIX[Path(file_name).suffix.lower()]
    return PresignedUrlService.create_upload_urls(
        file_name=file_name,
        content_type=content_type,
        path=PROFILE_IMAGE_S3_PATH,
    )


def update_profile_image(user: User, profile_img_url: str | None) -> None:

    user.profile_img_url = profile_img_url
    user.save(update_fields=["profile_img_url"])
