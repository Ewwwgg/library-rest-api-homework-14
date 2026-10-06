from rest_framework import generics
from rest_framework.response import Response

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


class BookDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.select_related("author").prefetch_related("borrowings")
    serializer_class = BookDetailSerializer


class BorrowingListCreateAPIView(CountDataListMixin, generics.ListCreateAPIView):
    queryset = Borrowing.objects.select_related("book", "reader").all()
    serializer_class = BorrowingSerializer


class AvailableBookListAPIView(CountDataListMixin, generics.ListAPIView):
    queryset = Book.objects.select_related("author").filter(available_copies__gt=0)
    serializer_class = BookSerializer
