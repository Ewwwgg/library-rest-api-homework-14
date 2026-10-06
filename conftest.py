import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from model_bakery import baker
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_reader(db):
    return get_user_model().objects.create_user(
        username="reader_taras",
        email="taras@example.com",
        password="ReaderPassword123!",
        phone="+380501112233",
    )


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_superuser(
        username="librarian_admin",
        email="admin@library.com",
        password="AdminPassword123!",
    )


@pytest.fixture
def auth_client(sample_reader):
    client = APIClient()
    client.force_authenticate(user=sample_reader)
    return client


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def sample_author(db):
    return baker.make("library.Author", name="Тарас Шевченко")


@pytest.fixture
def sample_book(db, sample_author):
    return baker.make(
        "library.Book",
        title="Кобзар",
        author=sample_author,
        pages=280,
        available_copies=3,
    )


@pytest.fixture
def out_of_stock_book(db, sample_author):
    return baker.make(
        "library.Book",
        title="Рідкісний манускрипт",
        author=sample_author,
        pages=500,
        available_copies=0,
    )
