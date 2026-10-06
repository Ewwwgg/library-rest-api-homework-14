from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Author, Book, Borrowing, Reader


class ReaderRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
        help_text="Choose a strong password with at least 8 characters.",
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="Enter the password again to confirm it.",
    )

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "email",
            "phone",
            "address",
            "password",
            "password_confirm",
        )
        extra_kwargs = {
            "email": {"required": True},
            "phone": {"required": False},
            "address": {"required": False},
        }

    def validate_email(self, value):
        if get_user_model().objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email address is already registered."
            )
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "The passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return get_user_model().objects.create_user(
            password=password,
            **validated_data,
        )


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

    def get_total_borrowings(self, obj: Book) -> int:
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

    def get_days_borrowed(self, obj: Borrowing) -> int:
        return obj.days_borrowed
