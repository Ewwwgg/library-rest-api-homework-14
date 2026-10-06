from datetime import date

from django.core.management.base import BaseCommand

from library.models import Author, Book, Borrowing, Reader


class Command(BaseCommand):
    help = "Create sample authors, books, readers, and borrowings."

    def handle(self, *args, **options):
        author_data = [
            ("Mary Shelley", "English novelist known for Frankenstein.", date(1797, 8, 30)),
            ("Jules Verne", "French novelist and pioneer of science fiction.", date(1828, 2, 8)),
            ("Jane Austen", "English novelist known for social commentary.", date(1775, 12, 16)),
            ("H. G. Wells", "English writer known for science fiction.", date(1866, 9, 21)),
            ("Louisa May Alcott", "American novelist and poet.", date(1832, 11, 29)),
        ]
        authors = {}
        for name, bio, birth_date in author_data:
            author, _ = Author.objects.get_or_create(
                name=name,
                defaults={"bio": bio, "birth_date": birth_date},
            )
            authors[name] = author

        book_data = [
            ("Frankenstein", "Mary Shelley", "A scientist creates a living being.", "9780000000001"),
            ("The Last Man", "Mary Shelley", "A novel set in a future world.", "9780000000002"),
            ("Twenty Thousand Leagues Under the Seas", "Jules Verne", "An underwater adventure.", "9780000000003"),
            ("Journey to the Center of the Earth", "Jules Verne", "An expedition beneath the surface.", "9780000000004"),
            ("Pride and Prejudice", "Jane Austen", "A comedy of manners and courtship.", "9780000000005"),
            ("Sense and Sensibility", "Jane Austen", "Two sisters navigate love and society.", "9780000000006"),
            ("The Time Machine", "H. G. Wells", "A traveler journeys far into the future.", "9780000000007"),
            ("The War of the Worlds", "H. G. Wells", "An invasion from Mars.", "9780000000008"),
            ("Little Women", "Louisa May Alcott", "The lives of the March sisters.", "9780000000009"),
            ("Good Wives", "Louisa May Alcott", "The March sisters grow into adulthood.", "9780000000010"),
        ]
        books = []
        for index, (title, author_name, description, isbn) in enumerate(book_data):
            book, _ = Book.objects.get_or_create(
                isbn=isbn,
                defaults={
                    "title": title,
                    "author": authors[author_name],
                    "description": description,
                    "published_date": date(2020, 1, 1),
                    "pages": 200 + index * 20,
                    "available_copies": 0 if index % 3 == 0 else 2,
                },
            )
            books.append(book)

        readers = []
        for index in range(1, 6):
            reader, created = Reader.objects.get_or_create(username=f"sample_reader_{index}")
            if created:
                reader.set_unusable_password()
                reader.save(update_fields=("password",))
            readers.append(reader)

        for book, reader in zip(books[:5], readers):
            Borrowing.objects.get_or_create(book=book, reader=reader)

        self.stdout.write(
            self.style.SUCCESS(
                f"Library data ready: {Author.objects.count()} authors, "
                f"{Book.objects.count()} books, {Borrowing.objects.count()} borrowings."
            )
        )
