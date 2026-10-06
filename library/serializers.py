from rest_framework import serializers

from .models import Author, Book, Borrowing, Reader


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ("id", "name", "bio", "birth_date", "photo")


class BookSerializer(serializers.ModelSerializer):
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "description",
            "isbn",
            "published_date",
            "pages",
            "cover",
            "available_copies",
            "is_available",
        )

    def validate_pages(self, value):
        if value <= 0:
            raise serializers.ValidationError("Pages must be greater than zero.")
        return value

    def validate_isbn(self, value):
        if len(value) != 13:
            raise serializers.ValidationError("ISBN must contain exactly 13 characters.")
        return value


class BookDetailSerializer(BookSerializer):
    author = AuthorSerializer(read_only=True)
    total_borrowings = serializers.SerializerMethodField()

    class Meta(BookSerializer.Meta):
        fields = BookSerializer.Meta.fields + ("total_borrowings",)

    def get_total_borrowings(self, obj):
        return obj.borrowings.count()


class BorrowedBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "isbn")


class BorrowingReaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reader
        fields = ("id", "username")


class BorrowingSerializer(serializers.ModelSerializer):
    book = BorrowedBookSerializer(read_only=True)
    reader = BorrowingReaderSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        source="book", queryset=Book.objects.all(), write_only=True
    )
    reader_id = serializers.PrimaryKeyRelatedField(
        source="reader", queryset=Reader.objects.all(), write_only=True
    )
    book_title = serializers.CharField(source="book.title", read_only=True)
    reader_name = serializers.CharField(source="reader.username", read_only=True)
    days_borrowed = serializers.SerializerMethodField()

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "book",
            "reader",
            "book_id",
            "reader_id",
            "book_title",
            "reader_name",
            "borrowed_date",
            "return_date",
            "is_returned",
            "days_borrowed",
        )

    def get_days_borrowed(self, obj):
        return obj.days_borrowed
