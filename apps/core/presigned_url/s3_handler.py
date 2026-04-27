import boto3
from django.conf import settings


class S3Handler:

    def __init__(self) -> None:
        self.s3 = boto3.client(
            "s3",
            config=settings.AWS_S3_CONFIG,
            region_name=settings.AWS_S3_REGION,
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.AWS_S3_BUCKET_NAME
        self.region = settings.AWS_S3_REGION

    # 업로드용 presigned url 생성 함수
    def presigned_url_for_upload(self, key: str, content_type: str, expire: int = 600) -> str:
        presigned_url = self.s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expire,
        )

        return presigned_url

    # DB의 img_url 생성 함수
    def img_url(self, key: str) -> str:
        img_url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

        return img_url


s3_handler: S3Handler | None = None


# lazy_init, singleton
def get_s3_handler() -> S3Handler:
    global s3_handler

    if s3_handler is None:
        s3_handler = S3Handler()
    return s3_handler
