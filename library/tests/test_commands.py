import pytest
from django.core.management import call_command

from library.models import Author, Book, Borrowing


@pytest.mark.django_db
def test_populate_library_command_is_idempotent():
    call_command("populate_library")
    call_command("populate_library")

    assert Author.objects.count() == 5
    assert Book.objects.count() == 10
    assert Borrowing.objects.count() == 5
