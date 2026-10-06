import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


pytestmark = [pytest.mark.django_db, pytest.mark.auth]


class TestAuthAPI:
    def test_reader_registration_hashes_password_and_returns_tokens(self, api_client):
        password = "SecureLibraryPassword!123"
        response = api_client.post(
            reverse("library:reader_register"),
            {
                "username": "lesia_ukrainka",
                "email": "lesia@example.com",
                "phone": "+380509998877",
                "password": password,
                "password_confirm": password,
            },
            format="json",
        )

        assert response.status_code == 201
        assert "password" not in response.data
        assert "password_confirm" not in response.data
        reader = get_user_model().objects.get(username="lesia_ukrainka")
        assert reader.check_password(password)
        assert response.data["access"]
        assert response.data["refresh"]

    def test_registration_rejects_password_mismatch_and_weak_password(
        self, api_client
    ):
        base_url = reverse("library:reader_register")
        mismatch = api_client.post(
            base_url,
            {
                "username": "mismatch_user",
                "email": "mismatch@example.com",
                "password": "SecureLibraryPassword!123",
                "password_confirm": "OtherPassword456!",
            },
            format="json",
        )
        weak = api_client.post(
            base_url,
            {
                "username": "weak_user",
                "email": "weak@example.com",
                "password": "123",
                "password_confirm": "123",
            },
            format="json",
        )

        assert mismatch.status_code == 400
        assert "password_confirm" in mismatch.data
        assert weak.status_code == 400
        assert "password" in weak.data

    def test_registration_requires_case_insensitive_unique_email(
        self, api_client, sample_reader
    ):
        response = api_client.post(
            reverse("library:reader_register"),
            {
                "username": "another_reader",
                "email": sample_reader.email.upper(),
                "password": "SecureLibraryPassword!123",
                "password_confirm": "SecureLibraryPassword!123",
            },
            format="json",
        )

        assert response.status_code == 400
        assert "email" in response.data

    def test_reader_can_obtain_and_refresh_jwt(self, api_client, sample_reader):
        token_response = api_client.post(
            reverse("token_obtain_pair"),
            {
                "username": "reader_taras",
                "password": "ReaderPassword123!",
            },
            format="json",
        )

        assert token_response.status_code == 200
        refresh_response = api_client.post(
            reverse("token_refresh"),
            {"refresh": token_response.data["refresh"]},
            format="json",
        )
        assert refresh_response.status_code == 200
        assert refresh_response.data["access"]

    def test_registration_throttle_returns_429_on_sixth_request(self, api_client):
        url = reverse("library:reader_register")

        for index in range(5):
            response = api_client.post(
                url,
                {
                    "username": f"rate_reader_{index}",
                    "email": f"rate_reader_{index}@example.com",
                    "password": "SecureLibraryPassword!123",
                    "password_confirm": "SecureLibraryPassword!123",
                },
                format="json",
            )
            assert response.status_code == 201

        response = api_client.post(
            url,
            {
                "username": "rate_reader_last",
                "email": "rate_reader_last@example.com",
                "password": "SecureLibraryPassword!123",
                "password_confirm": "SecureLibraryPassword!123",
            },
            format="json",
        )

        assert response.status_code == 429

    def test_homepage_and_api_docs_render(self, api_client):
        response = api_client.get(reverse("home"))

        assert response.status_code == 200
        assert b"Library API Developer Portal" in response.content
        assert api_client.get(reverse("swagger-ui")).status_code == 200
        assert api_client.get(reverse("redoc")).status_code == 200
