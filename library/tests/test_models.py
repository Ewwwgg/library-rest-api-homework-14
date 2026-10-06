import pytest
from model_bakery import baker

from library.models import Author, Book, Borrowing


pytestmark = [pytest.mark.django_db, pytest.mark.models]


class TestAuthorModel:
    def test_author_string_and_book_count(self, sample_author):
        assert str(sample_author) == "Тарас Шевченко"
        assert sample_author.book_count == 0

        baker.make(Book, author=sample_author, _quantity=4)

        assert sample_author.book_count == 4


class TestBookModel:
    def test_book_string_and_availability(self, sample_book, out_of_stock_book):
        assert str(sample_book) == "Кобзар"
        assert sample_book.is_available is True
        assert out_of_stock_book.is_available is False


class TestBorrowingModel:
    def test_borrowing_default_return_state_and_string(
        self, sample_book, sample_reader
    ):
        borrowing = baker.make(
            Borrowing,
            book=sample_book,
            reader=sample_reader,
        )

        assert borrowing.is_returned is False
        assert str(borrowing) == f"{sample_reader.username} borrowed {sample_book.title}"
        assert borrowing.days_borrowed >= 0

    def test_returned_borrowing_days_uses_return_date(self, sample_book, sample_reader):
        from datetime import date, timedelta

        borrowing = baker.make(
            Borrowing,
            book=sample_book,
            reader=sample_reader,
            is_returned=True,
            return_date=date.today(),
            borrowed_date=date.today() - timedelta(days=4),
        )

        assert borrowing.days_borrowed == 4
