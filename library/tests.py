from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.test import APIClient

from .models import Author, Book, Borrowing
from .serializers import BookSerializer


class LibraryAPITests(TestCase):
    def setUp(self):
        cache.clear()
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

    def create_book(self, *, title, isbn, pages, published_date, available_copies=1):
        return Book.objects.create(
            title=title,
            author=self.author,
            description="A book created for filtering tests.",
            isbn=isbn,
            published_date=published_date,
            pages=pages,
            available_copies=available_copies,
        )

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

    def test_available_books_backend_enforces_stock_and_supports_filters(self):
        self.create_book(
            title="Out of stock",
            isbn="1234567890124",
            pages=250,
            published_date=date(2024, 1, 1),
            available_copies=0,
        )

        response = self.client.get(
            reverse("library:available_books"),
            {"pages__gte": 200},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_book_filter_supports_text_author_date_page_and_stock_lookups(self):
        matched_book = self.create_book(
            title="The Kobzar",
            isbn="1234567890124",
            pages=250,
            published_date=date(1840, 1, 1),
            available_copies=3,
        )
        other_book = self.create_book(
            title="Another Book",
            isbn="1234567890125",
            pages=90,
            published_date=date(1850, 1, 1),
        )
        endpoint = reverse("library:book_list_create")
        reader = get_user_model().objects.create_user(username="book_filter_reader")
        self.client.force_authenticate(user=reader)

        cases = (
            ({"title__iexact": "THE KOBZAR"}, [matched_book.pk]),
            ({"title__icontains": "kob"}, [matched_book.pk]),
            (
                {"author": self.author.pk},
                [self.book.pk, matched_book.pk, other_book.pk],
            ),
            ({"published_date": "1840-01-01"}, [matched_book.pk]),
            ({"published_date__year": 1840}, [matched_book.pk]),
            ({"published_date__year__gt": 1840}, [self.book.pk, other_book.pk]),
            ({"published_date__year__lt": 1840}, []),
            ({"pages": 250}, [matched_book.pk]),
            ({"pages__lt": 200}, [self.book.pk, other_book.pk]),
            ({"pages__lte": 100}, [self.book.pk, other_book.pk]),
            ({"pages__gt": 200}, [matched_book.pk]),
            ({"pages__gte": 250}, [matched_book.pk]),
            ({"pages__range": "200,300"}, [matched_book.pk]),
            ({"available_copies": 3}, [matched_book.pk]),
            ({"available_copies__gt": 1}, [matched_book.pk]),
        )

        for params, expected_ids in cases:
            with self.subTest(params=params):
                response = self.client.get(endpoint, params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    sorted(item["id"] for item in response.data["data"]),
                    sorted(expected_ids),
                )

    def test_min_pages_backend_filters_books_and_rejects_invalid_value(self):
        long_book = self.create_book(
            title="Long Book",
            isbn="1234567890124",
            pages=300,
            published_date=date(2024, 1, 1),
        )
        endpoint = reverse("library:book_list_create")

        response = self.client.get(endpoint, {"min_pages": "200"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data["data"]], [long_book.pk])

        invalid_response = self.client.get(endpoint, {"min_pages": "many"})
        self.assertEqual(invalid_response.status_code, 400)
        self.assertIn("min_pages", invalid_response.data)

    def test_borrowing_list_includes_nested_names_and_days(self):
        borrowing = Borrowing.objects.create(book=self.book, reader=self.reader)
        borrowing.borrowed_date = date.today() - timedelta(days=3)
        borrowing.save(update_fields=("borrowed_date",))
        self.client.force_authenticate(user=self.reader)

        response = self.client.get(reverse("library:borrowing_list_create"))

        self.assertEqual(response.status_code, 200)
        result = response.data["data"][0]
        self.assertEqual(result["book_title"], self.book.title)
        self.assertEqual(result["reader_name"], self.reader.username)
        self.assertEqual(result["days_borrowed"], 3)
        self.assertEqual(result["book"]["isbn"], self.book.isbn)

    def test_borrowing_list_create_endpoint_creates_borrowing(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.post(
            reverse("library:borrowing_list_create"),
            {"book_id": self.book.pk, "reader_id": self.reader.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Borrowing.objects.filter(book=self.book, reader=self.reader).exists()
        )

    def test_borrowing_filters_related_fields_dates_and_returned_state(self):
        active = Borrowing.objects.create(book=self.book, reader=self.reader)
        active.borrowed_date = date(2024, 5, 10)
        active.save(update_fields=("borrowed_date",))
        returned_reader = get_user_model().objects.create_user(username="john_reader")
        returned = Borrowing.objects.create(
            book=self.book,
            reader=returned_reader,
            is_returned=True,
            return_date=date(2024, 5, 15),
        )
        returned.borrowed_date = date(2024, 5, 12)
        returned.save(update_fields=("borrowed_date",))
        other_book = self.create_book(
            title="Different Title",
            isbn="1234567890124",
            pages=100,
            published_date=date(2024, 1, 1),
        )
        other = Borrowing.objects.create(book=other_book, reader=self.reader)
        other.borrowed_date = date(2025, 6, 1)
        other.save(update_fields=("borrowed_date",))
        endpoint = reverse("library:borrowing_list_create")
        cases = (
            ({"reader": self.reader.pk}, [active.pk, other.pk]),
            ({"reader__username__icontains": "JOHN"}, [returned.pk]),
            ({"book": self.book.pk}, [active.pk, returned.pk]),
            ({"book__title__icontains": "available"}, [active.pk, returned.pk]),
            ({"borrowed_date": "2024-05-10"}, [active.pk]),
            ({"borrowed_date__year": 2024}, [active.pk, returned.pk]),
            ({"borrowed_date__month": 5}, [active.pk, returned.pk]),
            ({"borrowed_date__year__gte": 2025}, [other.pk]),
            ({"is_returned": "false"}, [active.pk, other.pk]),
            ({"is_returned": "true"}, [returned.pk]),
        )
        self.client.force_authenticate(user=self.reader)

        for params, expected_ids in cases:
            with self.subTest(params=params):
                response = self.client.get(endpoint, params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    sorted(item["id"] for item in response.data["data"]),
                    sorted(expected_ids),
                )

    def test_active_borrowings_backend_enforces_active_state_and_filters(self):
        active = Borrowing.objects.create(book=self.book, reader=self.reader)
        active.borrowed_date = date(2024, 5, 10)
        active.save(update_fields=("borrowed_date",))
        Borrowing.objects.create(
            book=self.book,
            reader=self.reader,
            is_returned=True,
            return_date=date.today(),
        )
        self.client.force_authenticate(user=self.reader)

        response = self.client.get(
            reverse("library:active_borrowings"),
            {"is_returned": "true"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_borrowing_endpoints_require_authentication(self):
        response = self.client.get(reverse("library:borrowing_list_create"))

        self.assertEqual(response.status_code, 401)

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


class RegistrationAndPortalTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.registration_url = reverse("library:reader_register")
        self.registration_data = {
            "username": "reader_api",
            "email": "reader@example.com",
            "password": "StrongLibraryPassword!902",
            "password_confirm": "StrongLibraryPassword!902",
        }

    def test_registration_hashes_password_and_returns_jwt_tokens(self):
        response = self.client.post(
            self.registration_url,
            self.registration_data,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        reader = get_user_model().objects.get(username="reader_api")
        self.assertTrue(reader.check_password(self.registration_data["password"]))
        self.assertNotEqual(reader.password, self.registration_data["password"])
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_confirm", response.data)
        self.assertTrue(response.data["access"])
        self.assertTrue(response.data["refresh"])

    def test_registered_reader_can_obtain_jwt_and_access_protected_endpoint(self):
        registration_response = self.client.post(
            self.registration_url,
            self.registration_data,
            format="json",
        )
        self.assertEqual(registration_response.status_code, 201)

        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": self.registration_data["username"],
                "password": self.registration_data["password"],
            },
            format="json",
        )

        self.assertEqual(token_response.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )
        borrowing_response = self.client.get(
            reverse("library:borrowing_list_create")
        )
        self.assertEqual(borrowing_response.status_code, 200)

    def test_registration_rejects_mismatched_and_weak_passwords(self):
        mismatched_data = {
            **self.registration_data,
            "password_confirm": "DifferentLibraryPassword!902",
        }
        mismatch_response = self.client.post(
            self.registration_url, mismatched_data, format="json"
        )
        weak_data = {
            **self.registration_data,
            "email": "weak@example.com",
            "password": "123",
            "password_confirm": "123",
        }
        weak_response = self.client.post(
            self.registration_url, weak_data, format="json"
        )

        self.assertEqual(mismatch_response.status_code, 400)
        self.assertIn("password_confirm", mismatch_response.data)
        self.assertEqual(weak_response.status_code, 400)
        self.assertIn("password", weak_response.data)
        self.assertFalse(
            get_user_model().objects.filter(username="reader_api").exists()
        )

    def test_registration_requires_unique_email_case_insensitively(self):
        get_user_model().objects.create_user(
            username="existing_reader",
            email="reader@example.com",
            password="AnExistingSecurePassword!902",
        )

        response = self.client.post(
            self.registration_url,
            self.registration_data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)

    def test_homepage_and_documentation_portal_routes_render(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("Library API Developer Portal", response.content.decode())
        self.assertEqual(self.client.get(reverse("swagger-ui")).status_code, 200)
        self.assertEqual(self.client.get(reverse("redoc")).status_code, 200)


class ThrottlingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_registration_throttle_blocks_sixth_attempt(self):
        url = reverse("library:reader_register")
        for index in range(5):
            response = self.client.post(
                url,
                {
                    "username": f"throttled_reader_{index}",
                    "email": f"throttled_{index}@example.com",
                    "password": "StrongLibraryPassword!902",
                    "password_confirm": "StrongLibraryPassword!902",
                },
                format="json",
            )
            self.assertEqual(response.status_code, 201)

        limited_response = self.client.post(
            url,
            {
                "username": "throttled_reader_last",
                "email": "throttled_last@example.com",
                "password": "StrongLibraryPassword!902",
                "password_confirm": "StrongLibraryPassword!902",
            },
            format="json",
        )

        self.assertEqual(limited_response.status_code, 429)

    def test_borrowing_throttle_blocks_sixteenth_request(self):
        reader = get_user_model().objects.create_user(username="rate_limited_reader")
        self.client.force_authenticate(user=reader)
        url = reverse("library:borrowing_list_create")

        for _ in range(15):
            self.assertEqual(self.client.get(url).status_code, 200)

        self.assertEqual(self.client.get(url).status_code, 429)

    def test_burst_throttle_blocks_third_catalog_request(self):
        reader = get_user_model().objects.create_user(username="burst_reader")
        self.client.force_authenticate(user=reader)
        url = reverse("library:book_list_create")

        with patch.dict(
            SimpleRateThrottle.THROTTLE_RATES,
            {"user": "100/minute", "burst": "2/minute"},
        ):
            self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual(self.client.get(url).status_code, 429)

    def test_sustained_throttle_blocks_third_catalog_request(self):
        reader = get_user_model().objects.create_user(username="sustained_reader")
        self.client.force_authenticate(user=reader)
        url = reverse("library:book_list_create")

        with patch.dict(
            SimpleRateThrottle.THROTTLE_RATES,
            {"user": "100/minute", "burst": "100/minute", "sustained": "2/hour"},
        ):
            self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual(self.client.get(url).status_code, 429)
