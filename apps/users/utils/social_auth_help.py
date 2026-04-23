from django.conf import settings
from django.http import HttpResponseBase


def set_refresh_cookie(response: HttpResponseBase, refresh_token: str) -> None:
    """
    refresh 토큰을 HttpOnly 쿠키에 설정.
    httponly=True → JS 접근 불가 (XSS 방어).
    """
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=60 * 60 * 24 * 3,  # 3일
    )


def get_frontend_url(path: str, **query_params: str) -> str:
    """프론트엔드 URL 생성"""
    base = getattr(settings, "FRONTEND_URL", "").rstrip("/")
    url = f"{base}{path}"
    if query_params:
        qs = "&".join(f"{k}={v}" for k, v in query_params.items())
        url = f"{url}?{qs}"
    return url
