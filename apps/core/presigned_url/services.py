import uuid

from .s3_handler import get_s3_handler


class PresignedUrlService:

    # presigned url, img_url을 반환하는 함수
    @classmethod
    def create_upload_urls(cls, file_name: str, content_type: str, path: str, expire: int = 600) -> dict[str, str]:

        s3_handler = get_s3_handler()

        key = cls._key(file_name, path)
        presigned_url = s3_handler.presigned_url_for_upload(key, content_type, expire)
        img_url = s3_handler.img_url(key)

        return {"presigned_url": presigned_url, "img_url": img_url, "key": key}

    # key: 파일명을 포함한 저장경로. ex) uploads/images/questions/uuid.png
    @classmethod
    def _key(cls, file_name: str, path: str) -> str:
        uuid_name = cls._image_uuid()
        key = f"{path.rstrip("/")}/{uuid_name}_{file_name}"

        return key

    # uuid 파일명 생성 함수
    @staticmethod
    def _image_uuid() -> str:
        return str(uuid.uuid4())
