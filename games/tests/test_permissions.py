import pytest

from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory

from games.models import Publisher, Game
from games.permissions import IsOwnerOrReadOnly


@pytest.mark.django_db
def test_owner_permission():
    owner = User.objects.create_user("owner")

    publisher = Publisher.objects.create(
        name="EA",
        webhook_url="https://example.com",
        webhook_secret="secret",
        user=owner,
    )

    game = Game.objects.create(
        title="Game",
        publisher=publisher,
        price=50,
    )

    factory = APIRequestFactory()

    request = factory.put("/")

    request.user = owner

    permission = IsOwnerOrReadOnly()

    assert permission.has_object_permission(
        request,
        None,
        game,
    )


@pytest.mark.django_db
def test_safe_method_permission():
    owner = User.objects.create_user("owner")

    publisher = Publisher.objects.create(
        name="EA",
        webhook_url="https://example.com",
        webhook_secret="secret",
        user=owner,
    )

    game = Game.objects.create(
        title="Game",
        publisher=publisher,
        price=50,
    )

    factory = APIRequestFactory()

    request = factory.get("/")

    request.user = User.objects.create_user("other")

    permission = IsOwnerOrReadOnly()

    assert permission.has_object_permission(
        request,
        None,
        game,
    )