import uuid

from .s3_handler import s3_handler

class PresignedUrlService:

    # presigned url, img_url을 반환하는 함수
    def create_upload_urls(
        self, file_name: str, path: str, content_type: str, expire: int = 600) -> dict:

        key = self._key(file_name, path)
        presigned_url = s3_handler.presigned_url_for_upload(key, content_type, expire)
        img_url = s3_handler.img_url(key)

        return {"presigned_url": presigned_url, "img_url": img_url, "key": key}

    # key: 파일명을 포함한 저장경로. ex) uploads/images/questions/uuid.png
    def _key(self, file_name: str, path: str) -> str:
        uuid_name = self._image_uuid()
        key = f"{path.rstrip("/")}/{uuid_name}_{file_name}"

        return key

    # uuid 파일명 생성 함수
    @staticmethod
    def _image_uuid() -> str:
        return str(uuid.uuid4())

