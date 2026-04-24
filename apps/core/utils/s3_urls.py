import uuid
from pathlib import Path

import boto3
from django.conf import settings

s3 = boto3.client(
    "s3",
    region_name=settings.AWS_S3_REGION,
    aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
)


"""
file_name: 확장자를 포함한 파일명을 그대로 넣어주세요
path: 저장경로에서 파일명을 뺀 값. 저장경로가 uploads/images/questions/uuid.png라면
    uploads/images/questions/를 넣어주세요. 마지막 슬래시는 있어도 없어도 상관 없음
expire: 넣거나 말거나
add_name: 파일명을 uuid_cat.png처럼 만들고 싶다면, add_name에 cat을 넣어주면 됩니다
"""


def create_upload_urls(file_name: str, path: str, expire: int = 600, *, add_name: str) -> tuple[str, str]:
    # 파일명에서 확장자 분리
    suffix = Path(file_name).suffix

    # rstrip("/"): path 마지막에 슬래시가 있으면 제거. 없으면 내비둠
    key = path.rstrip("/") + "/" + image_uuid(add_name) + suffix

    # boto3로 presigned_url 만드는 함수
    presigned_url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": key},
        ExpiresIn=expire,
    )

    # DB의 img_url
    img_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}"

    return presigned_url, img_url


# uuid 뒤에 추가 이름을 붙일 때 사용
def image_uuid(add_name: str | None) -> str:
    add = f"_{add_name}" if add_name else ""
    return str(uuid.uuid4()) + add
