from django.urls import path

from . import views


app_name = "library"

urlpatterns = [
    path(
        "register/",
        views.ReaderRegisterAPIView.as_view(),
        name="reader_register",
    ),
    path(
        "authors/",
        views.AuthorListCreateAPIView.as_view(),
        name="author_list_create",
    ),
    path(
        "authors/<int:author_id>/",
        views.AuthorDetailAPIView.as_view(),
        name="author_detail",
    ),
    path("books/", views.BookListCreateAPIView.as_view(), name="book_list_create"),
    path("books/<int:pk>/", views.BookDetailAPIView.as_view(), name="book_detail"),
    path(
        "borrowings/",
        views.BorrowingListCreateAPIView.as_view(),
        name="borrowing_list_create",
    ),
    path(
        "books/available/",
        views.AvailableBooksAPIView.as_view(),
        name="available_books",
    ),
    path(
        "borrowings/active/",
        views.ActiveBorrowingsAPIView.as_view(),
        name="active_borrowings",
    ),
]
