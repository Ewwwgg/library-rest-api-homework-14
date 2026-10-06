# Library REST API

Django REST Framework project for managing library authors, books, readers, and borrowings.

## Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py populate_library
python manage.py runserver
```

The API is available under `/api/`. List endpoints return a `count` and `data` object.

| Endpoint | Description |
| --- | --- |
| `/api/authors/` | List authors |
| `/api/authors/<id>/` | Author details |
| `/api/books/` | List books |
| `/api/books/<id>/` | Book details, including its author and borrowing count |
| `/api/books/available/` | Books with copies in stock |
| `/api/borrowings/` | List borrowings |

Uploaded images are served from `/media/` while `DEBUG` is enabled. Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS` through environment variables before deploying.
