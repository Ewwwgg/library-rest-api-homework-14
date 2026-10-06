from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Author, Book, Borrowing
from .serializers import BookSerializer


class LibraryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = Author.objects.create(name="Test Author", bio="A test biography.")
        self.book = Book.objects.create(
            title="Available Book",
            author=self.author,
            description="A test book.",
            isbn="1234567890123",
            published_date=date(2024, 1, 1),
            pages=100,
            available_copies=1,
        )
        self.reader = get_user_model().objects.create_user(username="reader")

    def test_author_list_uses_count_and_data_envelope(self):
        response = self.client.get(reverse("library:author_list_create"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["data"][0]["name"], self.author.name)

    def test_author_detail_returns_requested_author(self):
        response = self.client.get(reverse("library:author_detail", args=[self.author.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.author.pk)

    def test_author_list_create_endpoint_creates_author(self):
        response = self.client.post(
            reverse("library:author_list_create"),
            {"name": "New Author", "bio": "A new biography."},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Author.objects.filter(name="New Author").exists())

    def test_author_list_renders_browsable_api(self):
        response = self.client.get(
            reverse("library:author_list_create"),
            HTTP_ACCEPT="text/html",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])

    def test_author_detail_supports_update_and_delete(self):
        url = reverse("library:author_detail", kwargs={"author_id": self.author.pk})
        update_response = self.client.patch(
            url, {"name": "Updated Author"}, format="json"
        )

        self.assertEqual(update_response.status_code, 200)
        self.author.refresh_from_db()
        self.assertEqual(self.author.name, "Updated Author")

        delete_response = self.client.delete(url)

        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(Author.objects.filter(pk=self.author.pk).exists())

    def test_book_list_uses_count_and_data_envelope(self):
        response = self.client.get(reverse("library:book_list_create"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["data"][0]["title"], self.book.title)

    def test_book_list_create_endpoint_creates_book(self):
        response = self.client.post(
            reverse("library:book_list_create"),
            {
                "title": "New Book",
                "author": self.author.pk,
                "description": "A newly created book.",
                "isbn": "9876543210123",
                "published_date": "2024-02-01",
                "pages": 150,
                "available_copies": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Book.objects.filter(isbn="9876543210123").exists())

    def test_book_detail_supports_update_and_delete(self):
        url = reverse("library:book_detail", args=[self.book.pk])
        update_response = self.client.patch(
            url, {"title": "Updated Book"}, format="json"
        )

        self.assertEqual(update_response.status_code, 200)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "Updated Book")

        delete_response = self.client.delete(url)

        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())

    def test_book_detail_includes_author_and_borrowing_count(self):
        Borrowing.objects.create(book=self.book, reader=self.reader)

        response = self.client.get(reverse("library:book_detail", args=[self.book.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["author"]["name"], self.author.name)
        self.assertEqual(response.data["total_borrowings"], 1)

    def test_available_books_excludes_out_of_stock(self):
        self.book.available_copies = 0
        self.book.save(update_fields=("available_copies",))

        response = self.client.get(reverse("library:available_books"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"count": 0, "data": []})

    def test_available_books_lists_books_with_copies(self):
        response = self.client.get(reverse("library:available_books"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertTrue(response.data["data"][0]["is_available"])

    def test_borrowing_list_includes_nested_names_and_days(self):
        borrowing = Borrowing.objects.create(book=self.book, reader=self.reader)
        borrowing.borrowed_date = date.today() - timedelta(days=3)
        borrowing.save(update_fields=("borrowed_date",))

        response = self.client.get(reverse("library:borrowing_list_create"))

        self.assertEqual(response.status_code, 200)
        result = response.data["data"][0]
        self.assertEqual(result["book_title"], self.book.title)
        self.assertEqual(result["reader_name"], self.reader.username)
        self.assertEqual(result["days_borrowed"], 3)
        self.assertEqual(result["book"]["isbn"], self.book.isbn)

    def test_borrowing_list_create_endpoint_creates_borrowing(self):
        response = self.client.post(
            reverse("library:borrowing_list_create"),
            {"book_id": self.book.pk, "reader_id": self.reader.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Borrowing.objects.filter(book=self.book, reader=self.reader).exists()
        )

    def test_book_serializer_rejects_nonpositive_pages_and_invalid_isbn_length(self):
        serializer = BookSerializer(
            data={
                "title": "Invalid Book",
                "author": self.author.pk,
                "description": "Invalid values.",
                "isbn": "123",
                "published_date": "2024-01-01",
                "pages": 0,
                "available_copies": 1,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("pages", serializer.errors)
        self.assertIn("isbn", serializer.errors)
