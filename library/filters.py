import django_filters
from rest_framework import filters
from rest_framework.exceptions import ValidationError

from .models import Book, Borrowing


class BookFilter(django_filters.FilterSet):
    class Meta:
        model = Book
        fields = {
            "title": ["iexact", "icontains"],
            "author": ["exact"],
            "published_date": ["exact", "year", "year__gt", "year__lt"],
            "pages": ["exact", "lt", "lte", "gt", "gte", "range"],
            "available_copies": ["exact", "gt"],
        }


class BorrowingFilter(django_filters.FilterSet):
    class Meta:
        model = Borrowing
        fields = {
            "reader": ["exact"],
            "reader__username": ["icontains"],
            "book": ["exact"],
            "book__title": ["icontains"],
            "borrowed_date": ["exact", "year", "month", "year__gte"],
            "is_returned": ["exact"],
        }


class AvailableBooksFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(available_copies__gt=0)


class ActiveBorrowingsFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(is_returned=False)


class MinPagesFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        min_pages = request.query_params.get("min_pages")
        if min_pages is None:
            return queryset

        try:
            minimum = int(min_pages)
        except ValueError as exc:
            raise ValidationError({"min_pages": "Enter a whole number."}) from exc

        return queryset.filter(pages__gte=minimum)
