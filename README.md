# DevFolio: Portfolio + Blog API

Django REST Framework backend for my personal portfolio and blog. A single owner (superuser) manages all content through a JWT-protected API; visitors can read, like, comment (moderated) and send contact messages.

**Frontend repo:** https://github.com/HexEnigma/hamim-shahriar-portfolio-frontend
**Live API:** _add only after it is deployed and verified_
**Postman collection:** [`postman_collection.json`](./postman_collection.json) (regenerate with `python scripts/make_postman.py`)

## Tech stack
Python 3.10+, Django 5.1, Django REST Framework, djangorestframework-simplejwt (with token blacklist), django-filter, django-cors-headers, Pillow, python-decouple. SQLite for development, PostgreSQL supported through the `DB_*` variables.

## Features
- Single owner: no registration, no signup endpoint (`/api/auth/register/` returns 404).
- JWT login, refresh with rotation, logout with blacklist, change password.
- Portfolio data: profile (singleton), skills, experience, education, projects.
- Blog: drafts, publishing, categories, tags, likes (visitor UUID), threaded comments with moderation, related posts.
- Contact inbox, dashboard statistics (ORM aggregation), filtering, search, ordering, pagination.
- Scoped throttling, request logging middleware, signals, strict validation, absolute media URLs.

## Setup
```bash
git clone https://github.com/HexEnigma/hamim-shahriar-portfolio-backend.git
cd hamim-shahriar-portfolio-backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # then set SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Run the tests with `python manage.py test -v 2`.

## Environment variables
| Variable | Purpose | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key | long random string |
| `DEBUG` | Debug mode (False in production) | `True` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `127.0.0.1,localhost` |
| `CORS_ALLOWED_ORIGINS` | Frontend origins (whitelist only) | `http://localhost:5173` |
| `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Database | SQLite by default |
| `OWNER_NOTIFY_EMAIL` | Recipient of new-comment notices (console backend) | `owner@example.com` |
| `VIEW_COOLDOWN_SECONDS` | Per-visitor view-count cooldown | `1800` |
| `NUM_PROXIES` | Proxies in front of the app (for client IP) | `0` |
| `SECURE_SSL_REDIRECT` | HTTPS redirect when `DEBUG=False` | `True` |

## Endpoints
| Method | Path | Access |
|---|---|---|
| POST | `/api/auth/login/` | Public |
| POST | `/api/auth/refresh/` | Public |
| POST | `/api/auth/logout/` | Owner |
| GET | `/api/auth/me/` | Owner |
| POST | `/api/auth/change-password/` | Owner |
| GET / PATCH | `/api/profile/` | Public read / Owner write |
| GET / POST | `/api/skills/` | Public read / Owner write |
| PATCH / DELETE | `/api/skills/<id>/` | Owner |
| GET / POST | `/api/experiences/`, `/api/education/` | Public read / Owner write |
| PATCH / DELETE | `/api/experiences/<id>/`, `/api/education/<id>/` | Owner |
| GET / POST | `/api/projects/` | Public read / Owner write |
| GET / PATCH / DELETE | `/api/projects/<slug>/` | Public read / Owner write |
| GET / POST | `/api/posts/` | Public (published only) / Owner write |
| GET / PATCH / DELETE | `/api/posts/<slug>/` | Public (published only) / Owner write |
| POST | `/api/posts/<slug>/like/` | Public (`X-Visitor-Id` required) |
| GET / POST | `/api/posts/<slug>/comments/` | Public (approved only; new comments need approval) |
| GET | `/api/comments/` | Owner (moderation list) |
| PATCH / DELETE | `/api/comments/<id>/` | Owner |
| GET / POST | `/api/categories/`, `/api/tags/` | Public read / Owner write |
| PATCH / DELETE | `/api/categories/<id>/`, `/api/tags/<id>/` | Owner |
| POST | `/api/contact/` | Public (throttled) |
| GET | `/api/contact/` | Owner |
| PATCH / DELETE | `/api/contact/<id>/` | Owner |
| GET | `/api/dashboard/stats/` | Owner |

## Models
`User` (built-in, the owner) · `Profile` (singleton) · `Skill` · `Experience` · `Education` · `Project` —M2M→ `Skill` · `Category` ←FK(PROTECT)— `Post` —M2M→ `Tag` · `Post` ←FK— `PostLike` (unique per post + visitor) · `Post` ←FK— `Comment` ←self FK (one reply level) · `ContactMessage`.

## Permission class
`core.permissions.IsOwnerOrReadOnly` allows safe methods for everyone and any write only when `request.user.is_authenticated and request.user.is_superuser`. Private endpoints (moderation list, inbox, dashboard, me) use `IsOwner`. The frontend never makes the decision, and the API rejects visitors with 401 and non-owner users with 403.

## View counter strategy
`GET /api/posts/<slug>/` increments `views_count` at most once per visitor per cooldown window. The visitor is identified by the `X-Visitor-Id` header (falling back to the client IP). A cache key `post-view:<post>:<hash>` is created with `cache.add()` (atomic, expires after `VIEW_COOLDOWN_SECONDS`). Only when the key is newly created does a single `UPDATE … SET views_count = views_count + 1` (an `F()` expression) run. React 18 StrictMode's double requests and page refreshes therefore never double count, and the owner's views are not counted. With multiple server processes use a shared cache (Redis or a database cache).

## Throttle rates
| Scope | Rate |
|---|---|
| Anonymous reads | 300/min per IP (see deviation) |
| Anonymous writes | 20/min per IP |
| Comment creation | 5/hour per IP |
| Contact form | 3/hour per IP |
| Like toggle | 30/min per IP |
| Login | 10/min per IP |

**Deviation from the brief:** the brief's "anonymous 20/min global" would block a single-page app (the home page alone makes about 6 requests), so reads and writes are limited separately as shown. The owner is exempt from the IP-scoped limits.

## Notes
- `Post.content` is **Markdown**; the frontend renders it without raw HTML.
- `PostLike` uses a `UniqueConstraint` on (post, visitor_id) (the modern equivalent of `unique_together`).
- Login issues tokens to any active user so the permission class can be tested with a non-owner token; only superusers can write.