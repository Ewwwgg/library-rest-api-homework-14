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

The API is available under `/api/`. List endpoints return a `count` and `data` object. Author and book endpoints support creating items with `POST`; detail endpoints support `PUT`, `PATCH`, and `DELETE`. Borrowings can be created with `POST` using `book_id` and `reader_id`.

| Endpoint | Description |
| --- | --- |
| `/api/authors/` | List and create authors |
| `/api/authors/<author_id>/` | Retrieve, update, or delete an author |
| `/api/books/` | List and create books |
| `/api/books/<id>/` | Retrieve, update, or delete a book; details include its author and borrowing count |
| `/api/books/available/` | Books with copies in stock |
| `/api/borrowings/` | List and create borrowings |

Uploaded images are served from `/media/` while `DEBUG` is enabled. Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS` through environment variables before deploying.
