from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Reader(AbstractUser):
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    registration_date = models.DateField(auto_now_add=True)


class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField()
    birth_date = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to="authors/", null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def book_count(self):
        return self.books.count()


class Book(models.Model):
    title = models.CharField(max_length=300)
    author = models.ForeignKey(Author, related_name="books", on_delete=models.CASCADE)
    description = models.TextField()
    isbn = models.CharField(max_length=13, unique=True)
    published_date = models.DateField()
    pages = models.PositiveIntegerField()
    cover = models.ImageField(upload_to="books/", null=True, blank=True)
    available_copies = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        return self.available_copies > 0


class Borrowing(models.Model):
    book = models.ForeignKey(Book, related_name="borrowings", on_delete=models.CASCADE)
    reader = models.ForeignKey(Reader, related_name="borrowings", on_delete=models.CASCADE)
    borrowed_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.reader.username} borrowed {self.book.title}"

    @property
    def days_borrowed(self):
        end_date = self.return_date if self.is_returned and self.return_date else timezone.localdate()
        return (end_date - self.borrowed_date).days
