from datetime import date

import pytest
from django.urls import reverse
from model_bakery import baker

from library.models import Book


pytestmark = [pytest.mark.django_db, pytest.mark.books]


def book_payload(author, **overrides):
    payload = {
        "title": "Test title",
        "author": author.pk,
        "description": "A test description.",
        "isbn": "9789661000011",
        "published_date": "2020-01-01",
        "pages": 200,
        "available_copies": 2,
    }
    payload.update(overrides)
    return payload


class TestBookAPI:
    def test_anonymous_can_list_books(self, api_client, sample_book):
        response = api_client.get(reverse("library:book_list_create"))

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["data"][0]["id"] == sample_book.id

    def test_only_admin_can_create_books(self, api_client, auth_client, admin_client, sample_author):
        url = reverse("library:book_list_create")
        payload = book_payload(sample_author)

        api_client.force_authenticate(user=None)
        assert api_client.post(url, payload).status_code == 401
        assert auth_client.post(url, payload).status_code == 403
        response = admin_client.post(url, payload)

        assert response.status_code == 201
        assert Book.objects.filter(isbn=payload["isbn"]).exists()

    @pytest.mark.parametrize(
        ("pages", "available_copies"),
        [(0, 5), (-10, 2)],
    )
    def test_admin_create_rejects_invalid_book_data(
        self, admin_client, sample_author, pages, available_copies
    ):
        response = admin_client.post(
            reverse("library:book_list_create"),
            book_payload(
                sample_author,
                isbn="9789661000044",
                pages=pages,
                available_copies=available_copies,
            ),
        )

        assert response.status_code == 400
        assert "pages" in response.data

    def test_reader_cannot_update_or_delete_book(
        self, auth_client, sample_book
    ):
        url = reverse("library:book_detail", args=[sample_book.pk])

        assert auth_client.patch(url, {"title": "Changed"}).status_code == 403
        assert auth_client.delete(url).status_code == 403

    def test_admin_can_update_and_delete_book(self, admin_client, sample_book):
        url = reverse("library:book_detail", args=[sample_book.pk])
        assert admin_client.patch(url, {"title": "Updated"}).status_code == 200
        sample_book.refresh_from_db()
        assert sample_book.title == "Updated"
        assert admin_client.delete(url).status_code == 204

    def test_detail_contains_author_and_borrowing_count(
        self, api_client, sample_book, sample_reader
    ):
        baker.make(
            "library.Borrowing",
            book=sample_book,
            reader=sample_reader,
            _quantity=2,
        )

        response = api_client.get(
            reverse("library:book_detail", args=[sample_book.pk])
        )

        assert response.status_code == 200
        assert response.data["author"]["name"] == sample_book.author.name
        assert response.data["total_borrowings"] == 2

    def test_available_books_only_includes_books_in_stock(
        self, api_client, sample_book, out_of_stock_book
    ):
        response = api_client.get(reverse("library:available_books"))

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert [item["id"] for item in response.data["data"]] == [sample_book.pk]

    @pytest.mark.parametrize(
        ("query", "expected"),
        [
            ("title__iexact=KOBZAR", True),
            ("title__icontains=kob", True),
            ("author={author}", True),
            ("published_date=1840-01-01", True),
            ("published_date__year=1840", True),
            ("published_date__year__gt=1840", False),
            ("published_date__year__lt=1841", True),
            ("pages=280", True),
            ("pages__lt=300", True),
            ("pages__lte=280", True),
            ("pages__gt=200", True),
            ("pages__gte=280", True),
            ("pages__range=200,300", True),
            ("available_copies=3", True),
            ("available_copies__gt=0", True),
            ("min_pages=281", False),
        ],
    )
    def test_book_filter_query_lookups(
        self, api_client, sample_book, query, expected
    ):
        sample_book.title = "Kobzar"
        sample_book.published_date = date(1840, 1, 1)
        sample_book.save(update_fields=["title", "published_date"])
        query = query.format(author=sample_book.author_id)
        response = api_client.get(f"{reverse('library:book_list_create')}?{query}")

        assert response.status_code == 200
        assert (sample_book.pk in [item["id"] for item in response.data["data"]]) is expected

    def test_min_pages_rejects_invalid_value(self, api_client, sample_book):
        response = api_client.get(
            reverse("library:book_list_create"), {"min_pages": "many"}
        )

        assert response.status_code == 400
        assert "min_pages" in response.data

    def test_serializer_requires_positive_pages_and_13_character_isbn(
        self, admin_client, sample_author
    ):
        response = admin_client.post(
            reverse("library:book_list_create"),
            book_payload(sample_author, pages=0, isbn="123"),
        )

        assert response.status_code == 400
        assert "pages" in response.data
        assert "isbn" in response.data
