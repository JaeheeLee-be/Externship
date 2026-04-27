from apps.core.utils.s3_urls import s3


def generate_presigned_url(file_name: str) -> dict:
    presigned_url, img_url = s3.create_upload_urls(
        file_name=file_name,
        path="uploads/images/posts/",
    )
    key = img_url.split(".amazonaws.com/")[-1]
    return {
        "presigned_url": presigned_url,
        "img_url": img_url,
        "key": key,
    }
