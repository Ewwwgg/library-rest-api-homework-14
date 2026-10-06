from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Author, Book, Borrowing
from .serializers import (
    AuthorSerializer,
    BookDetailSerializer,
    BookSerializer,
    BorrowingSerializer,
)


@api_view(["GET"])
def author_list(request):
    authors = Author.objects.all()
    serializer = AuthorSerializer(authors, many=True)
    return Response({"count": authors.count(), "data": serializer.data})


@api_view(["GET"])
def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    return Response(AuthorSerializer(author).data)


@api_view(["GET"])
def book_list(request):
    books = Book.objects.select_related("author").all()
    serializer = BookSerializer(books, many=True)
    return Response({"count": books.count(), "data": serializer.data})


@api_view(["GET"])
def book_detail(request, pk):
    book = get_object_or_404(
        Book.objects.select_related("author").prefetch_related("borrowings"), pk=pk
    )
    return Response(BookDetailSerializer(book).data)


@api_view(["GET"])
def borrowing_list(request):
    borrowings = Borrowing.objects.select_related("book", "reader").all()
    serializer = BorrowingSerializer(borrowings, many=True)
    return Response({"count": borrowings.count(), "data": serializer.data})


@api_view(["GET"])
def available_books(request):
    books = Book.objects.select_related("author").filter(available_copies__gt=0)
    serializer = BookSerializer(books, many=True)
    return Response({"count": books.count(), "data": serializer.data}, status=status.HTTP_200_OK)
