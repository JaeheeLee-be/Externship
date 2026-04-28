"""
사용법:

from apps.core.utils.s3 import PresignedUrlView

class ExampleView(PresignedUrlView):
    permission_classes: list[type[Any]]
    path: str
    expire: int

1. permission_classes: 알맞게 정의하세요. 기본값은 []입니다.
2. path: 이 속성은 반드시 정의해야 합니다. 파일명을 제외한 저장경로를 쓰면 됩니다.
    ex) 저장경로가 upload/uuid.jpg라면 upload/를 쓰세요.
    마지막 슬래시는 있어도 없어도 상관 없음.
3. expire: 기본값은 600, 즉 10분입니다.

- PresignedUrlView는 presigned_url, img_url, key를 응답합니다.
- PUT과 POST 메서드를 모두 지원하며, 하나만 허용하려면 사용하지 않을 메서드를 오버라이드 하세요.
- 400에러만을 발생시키니, 401과 403 에러는 서브클래스에서 직접 정의해야 합니다.
- DB에 img_url을 저장하고 싶다면, 그건 나도 모릅니다. 조교님이나 코치님한테 물어보세요.
"""

from apps.core.presigned_url.views import PresignedUrlView

__all__ = ["PresignedUrlView"]
