import pytest
from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from games.models import Publisher, Game, GameKey


@pytest.mark.django_db
def test_register_user():
    client = APIClient()

    response = client.post(
        "/api/register/",
        {
            "username": "john",
            "password": "pass12345"
        },
        format="json"
    )

    assert response.status_code == 201
    assert "token" in response.data


@pytest.mark.django_db
def test_register_without_password():
    client = APIClient()

    response = client.post(
        "/api/register/",
        {
            "username": "john"
        },
        format="json"
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_order():
    buyer = User.objects.create_user(
        username="buyer",
        password="1234"
    )

    token = Token.objects.create(user=buyer)

    publisher_user = User.objects.create_user(
        username="publisher",
        password="1234"
    )

    publisher = Publisher.objects.create(
        name="EA",
        webhook_url="https://example.com",
        webhook_secret="secret",
        user=publisher_user,
    )

    game = Game.objects.create(
        title="FIFA",
        publisher=publisher,
        price=49.99,
    )

    GameKey.objects.create(
        key_string="ABC123",
        game=game,
        status="active",
        expires_at=timezone.now() + timedelta(days=30),
    )

    client = APIClient()

    client.credentials(
        HTTP_AUTHORIZATION=f"Token {token.key}"
    )

    response = client.post(
        "/api/orders/",
        {
            "game_id": game.id
        },
        format="json"
    )

    assert response.status_code == 201
    assert response.data["key"] == "ABC123"

    key = GameKey.objects.get(key_string="ABC123")

    assert key.owner == buyer