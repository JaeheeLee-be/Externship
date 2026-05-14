# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OZ Coding School Externship 8기 Backend — Django REST API with PostgreSQL, Redis, WebSocket (Channels), and JWT authentication.

## Commands

### Dependency Management
```bash
poetry install          # Install dependencies
poetry add <package>    # Add dependency
```

### Running the Server
```bash
# Local development (requires .local.env configured)
python manage.py runserver

# Docker (recommended)
docker-compose -f docker-compose.local.yml up
```

### Database
```bash
python manage.py makemigrations
python manage.py migrate
```

### Tests
```bash
# Run all tests
poetry run python manage.py test

# Run tests in parallel
poetry run python manage.py test --parallel 3

# Run tests for a specific app
poetry run python manage.py test apps.posts

# Run with coverage
poetry run coverage run --parallel-mode --concurrency=multiprocessing manage.py test --parallel 3
poetry run coverage combine
poetry run coverage report -m
```

The custom `test` management command (in `apps/core/management/commands/test.py`) flushes Redis before and after runs for test isolation.

### Linting & Formatting
```bash
poetry run isort .              # Sort imports
poetry run black .              # Format code
poetry run mypy .               # Type check

# CI check mode (no changes)
poetry run isort . --check --diff
poetry run black . --check
```

Line length is 120 (Black). isort uses the `black` profile. Mypy runs in strict mode.

## Architecture

### Settings
Environment-based settings inheritance:
- `config/settings/base.py` — shared configuration
- `config/settings/local.py` — DEBUG=True, debug-toolbar
- `config/settings/dev.py` — staging with Sentry
- `config/settings/prod.py` — production

Set via `DJANGO_SETTINGS_MODULE` env var. Local env vars live in `envs/.local.env`.

### App Structure

Each app follows a layered MVCS pattern:

```
apps/<name>/
├── models/        # ORM models (each in separate file, exported from __init__.py)
├── serializers/   # DRF serializers for request/response validation
├── services/      # Business logic and optimized queries
├── views/         # APIView subclasses (thin, delegate to services)
├── urls/          # URL routing
├── migrations/
└── tests/
```

Apps:
- `apps/core` — `TimeStampModel` abstract base (adds `created_at`/`updated_at`), custom permissions, Redis test isolation utility
- `apps/users` — Custom email-based `User` model (roles: USER, ADMIN, STUDENT), OAuth (Kakao/Naver), enrollment requests
- `apps/qna` — Questions, Answers, hierarchical categories, images, comments
- `apps/posts` — Posts with categories, comments (`PostComment`), and user mention tags (`PostCommentTag`)

### URL Hierarchy
```
config/urls.py
└── api/v1/ → apps/<app>/urls/__init__.py → apps/<app>/urls/<feature>.py
```

Example: `api/v1/posts/<post_id>/comments/`

### Key Patterns

**Models:** All models extend `TimeStampModel`. Foreign keys to User use `settings.AUTH_USER_MODEL`.

**Services:** Contain all query logic, including `select_related`/`prefetch_related` optimizations. Views call service functions; views do not query directly.

**Serializers:** Use `SerializerMethodField` for computed fields. Nested serializers (e.g., `CommentAuthorSerializer`) are defined inline for read-only data.

**Views:** Use `APIView` with explicit `get`/`post`/`patch`/`delete` methods. Decorated with `@extend_schema` (drf-spectacular) for OpenAPI docs. Default permission: `IsAuthenticatedOrReadOnly`.

### Authentication
JWT via `djangorestframework-simplejwt`. Bearer tokens. Access: 1 day (local), 60 min (prod). Refresh: 7 days.

### API Documentation
Swagger UI: `/api/schema/swagger-ui/`
ReDoc: `/api/schema/redoc/`

### Infrastructure
- PostgreSQL 14 (primary DB)
- Redis (caching + Django Channels layer)
- AWS S3 (media/image storage)
- Twilio (SMS verification)
- Sentry (error tracking, dev & prod)
- Gunicorn + Nginx (production Docker)

## CI/CD

GitHub Actions (`.github/workflows/checks.yml`) runs on PRs to `main`/`develop`:
1. **CI job:** isort check → black check → mypy
2. **Test job:** migrate → coverage run (80% minimum)

Services: PostgreSQL 14 + Redis. Python 3.12, Poetry cached.
