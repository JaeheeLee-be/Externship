from apps.core.utils.s3_urls import s3
from apps.posts.exceptions import InvalidFileExtensionError


def generate_presigned_url(file_name: str) -> dict[str, str]:
    try:
        presigned_url, img_url = s3.create_upload_urls(
            file_name=file_name,
            path="uploads/images/posts/",
        )
    except ValueError:
        raise InvalidFileExtensionError("지원하지 않는 파일 형식입니다")

    key = img_url.split(".amazonaws.com/")[-1]
    return {
        "presigned_url": presigned_url,
        "img_url": img_url,
        "key": key,
    }
