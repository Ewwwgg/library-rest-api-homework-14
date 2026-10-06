from django.urls import path

from . import views


app_name = "library"

urlpatterns = [
    path("authors/", views.author_list, name="author_list"),
    path("authors/<int:pk>/", views.author_detail, name="author_detail"),
    path("books/", views.book_list, name="book_list"),
    path("books/<int:pk>/", views.book_detail, name="book_detail"),
    path("borrowings/", views.borrowing_list, name="borrowing_list"),
    path("books/available/", views.available_books, name="available_books"),
]
