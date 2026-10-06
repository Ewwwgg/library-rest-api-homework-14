from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import (
    ActiveBorrowingsFilterBackend,
    AvailableBooksFilterBackend,
    BookFilter,
    BorrowingFilter,
    MinPagesFilterBackend,
)
from .models import Author, Book, Borrowing
from .serializers import (
    AuthorSerializer,
    BookDetailSerializer,
    BookSerializer,
    BorrowingSerializer,
)


class CountDataListMixin:
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"count": queryset.count(), "data": serializer.data})


class AuthorListCreateAPIView(CountDataListMixin, generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class AuthorDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    lookup_url_kwarg = "author_id"


class BookListCreateAPIView(CountDataListMixin, generics.ListCreateAPIView):
    queryset = Book.objects.select_related("author").all()
    serializer_class = BookSerializer
    filterset_class = BookFilter
    filter_backends = [DjangoFilterBackend, MinPagesFilterBackend]


class BookDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.select_related("author").prefetch_related("borrowings")
    serializer_class = BookDetailSerializer


class BorrowingListCreateAPIView(CountDataListMixin, generics.ListCreateAPIView):
    queryset = Borrowing.objects.select_related("book", "reader").all()
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = BorrowingFilter


class AvailableBooksAPIView(CountDataListMixin, generics.ListAPIView):
    queryset = Book.objects.select_related("author").order_by("pk")
    serializer_class = BookSerializer
    filterset_class = BookFilter
    filter_backends = [DjangoFilterBackend, AvailableBooksFilterBackend]


class ActiveBorrowingsAPIView(CountDataListMixin, generics.ListAPIView):
    queryset = Borrowing.objects.select_related("book", "reader").order_by(
        "-borrowed_date"
    )
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = BorrowingFilter
    filter_backends = [DjangoFilterBackend, ActiveBorrowingsFilterBackend]
