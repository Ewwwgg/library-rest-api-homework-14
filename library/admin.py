from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Author, Book, Borrowing, Reader


@admin.register(Reader)
class ReaderAdmin(UserAdmin):
    list_display = ("username", "email", "phone", "registration_date", "is_staff")
    search_fields = ("username", "email", "phone")
    fieldsets = UserAdmin.fieldsets + (
        ("Library details", {"fields": ("phone", "address", "registration_date")}),
    )
    readonly_fields = ("registration_date",)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "birth_date", "book_count")
    search_fields = ("name",)
    list_filter = ("birth_date",)
    readonly_fields = ("book_count",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn", "available_copies")
    search_fields = ("title", "isbn", "author__name")
    list_filter = ("author", "published_date")


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ("book", "reader", "borrowed_date", "return_date", "is_returned")
    search_fields = ("book__title", "reader__username")
    list_filter = ("is_returned", "borrowed_date")
