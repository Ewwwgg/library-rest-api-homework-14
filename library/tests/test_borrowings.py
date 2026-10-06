from datetime import date

import pytest
from django.urls import reverse
from model_bakery import baker

from library.models import Borrowing


pytestmark = [pytest.mark.django_db, pytest.mark.borrowings]


class TestBorrowingAPI:
    def test_anonymous_reader_is_unauthorized(self, api_client):
        response = api_client.get(reverse("library:borrowing_list_create"))

        assert response.status_code == 401

    def test_reader_sees_only_own_borrowings(
        self, api_client, sample_reader, sample_book
    ):
        other_reader = baker.make("library.Reader", username="other_reader")
        baker.make(
            Borrowing, reader=sample_reader, book=sample_book, _quantity=2
        )
        baker.make(Borrowing, reader=other_reader, book=sample_book)
        api_client.force_authenticate(user=sample_reader)

        response = api_client.get(reverse("library:borrowing_list_create"))

        assert response.status_code == 200
        assert response.data["count"] == 2
        assert all(
            item["reader"]["id"] == sample_reader.pk
            for item in response.data["data"]
        )

    def test_reader_can_create_borrowing_for_self(
        self, auth_client, sample_reader, sample_book
    ):
        response = auth_client.post(
            reverse("library:borrowing_list_create"),
            {"book": sample_book.pk, "reader": sample_reader.pk},
            format="json",
        )

        assert response.status_code == 201, response.data
        borrowing = Borrowing.objects.get()
        assert borrowing.book == sample_book
        assert borrowing.reader == sample_reader

    def test_reader_can_create_borrowing_with_id_aliases(
        self, auth_client, sample_reader, sample_book
    ):
        response = auth_client.post(
            reverse("library:borrowing_list_create"),
            {"book_id": sample_book.pk, "reader_id": sample_reader.pk},
            format="json",
        )

        assert response.status_code == 201
        assert Borrowing.objects.filter(
            book=sample_book, reader=sample_reader
        ).exists()

    def test_reader_cannot_create_borrowing_for_another_reader(
        self, auth_client, sample_book, db
    ):
        other_reader = baker.make("library.Reader", username="other_reader")

        response = auth_client.post(
            reverse("library:borrowing_list_create"),
            {"book_id": sample_book.pk, "reader_id": other_reader.pk},
            format="json",
        )

        assert response.status_code == 400
        assert "reader_id" in response.data

    def test_active_borrowings_excludes_returned(
        self, auth_client, sample_reader, sample_book
    ):
        active = baker.make(
            Borrowing, reader=sample_reader, book=sample_book, is_returned=False
        )
        baker.make(
            Borrowing,
            reader=sample_reader,
            book=sample_book,
            is_returned=True,
            return_date=date.today(),
        )

        response = auth_client.get(reverse("library:active_borrowings"))

        assert response.status_code == 200
        assert [item["id"] for item in response.data["data"]] == [active.pk]

    def test_borrowing_filters_related_fields_and_return_state(
        self, auth_client, sample_reader, sample_book
    ):
        borrowing = baker.make(
            Borrowing,
            reader=sample_reader,
            book=sample_book,
            borrowed_date=date(2024, 5, 10),
        )

        response = auth_client.get(
            reverse("library:borrowing_list_create"),
            {
                "reader__username__icontains": sample_reader.username,
                "book__title__icontains": sample_book.title,
                "borrowed_date__year": 2024,
                "borrowed_date__month": 5,
                "borrowed_date__year__gte": 2024,
                "is_returned": "false",
            },
        )

        assert response.status_code == 200
        assert [item["id"] for item in response.data["data"]] == [borrowing.pk]

    def test_borrowing_filter_supports_reader_and_book_ids(
        self, auth_client, sample_reader, sample_book
    ):
        borrowing = baker.make(
            Borrowing, reader=sample_reader, book=sample_book
        )
        response = auth_client.get(
            reverse("library:borrowing_list_create"),
            {"reader": sample_reader.pk, "book": sample_book.pk},
        )

        assert response.status_code == 200
        assert [item["id"] for item in response.data["data"]] == [borrowing.pk]

    def test_borrowing_throttle(self, auth_client):
        url = reverse("library:borrowing_list_create")

        for _ in range(15):
            assert auth_client.get(url).status_code == 200

        assert auth_client.get(url).status_code == 429
