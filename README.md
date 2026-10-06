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

The API is available under `/api/`. List endpoints return a `count` and `data` object. Author and book endpoints support creating items with `POST`; detail endpoints support `PUT`, `PATCH`, and `DELETE`. Borrowing endpoints require an authenticated user; borrowings can be created with `POST` using `book_id` and `reader_id`. Books and borrowings support `django-filter` query parameters. The available books and active borrowings endpoints also enforce their respective stock/return-state filters. Books support `?min_pages=200`; invalid values return HTTP 400.

| Endpoint | Description |
| --- | --- |
| `/api/authors/` | List and create authors |
| `/api/authors/<author_id>/` | Retrieve, update, or delete an author |
| `/api/books/` | List and create books |
| `/api/books/<id>/` | Retrieve, update, or delete a book; details include its author and borrowing count |
| `/api/books/available/` | Books with copies in stock, with book filters |
| `/api/borrowings/` | List and create borrowings, with borrowing filters |
| `/api/borrowings/active/` | Active borrowings, with borrowing filters |

### Filtering examples

```text
/api/books/?title__icontains=kobzar
/api/books/?published_date__year=1840
/api/books/?pages__range=100,300
/api/books/?available_copies__gt=0
/api/books/?min_pages=200
/api/borrowings/?reader__username__icontains=john
/api/borrowings/?book__title__icontains=kobzar
/api/borrowings/?borrowed_date__year=2024
/api/borrowings/?is_returned=false
/api/borrowings/active/
```

Book filters include case-insensitive title matching, author ID, publication date/year, page-count comparisons/ranges, and available-copy counts. Borrowing filters include reader/book IDs and related names, borrowing date/year/month, and returned state.

Uploaded images are served from `/media/` while `DEBUG` is enabled. Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS` through environment variables before deploying.
