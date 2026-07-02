import pytest

from django.contrib.auth.models import User

from games.models import Publisher, Game
from games.serializers import GameSerializer, PublisherSerializer


@pytest.mark.django_db
def test_game_serializer():
    user = User.objects.create_user("pub")

    publisher = Publisher.objects.create(
        name="EA",
        webhook_url="https://example.com",
        webhook_secret="secret",
        user=user,
    )

    game = Game.objects.create(
        title="FIFA",
        publisher=publisher,
        price=59.99,
    )

    serializer = GameSerializer(game)

    assert serializer.data["title"] == "FIFA"


@pytest.mark.django_db
def test_publisher_serializer():
    user = User.objects.create_user("pub2")

    publisher = Publisher.objects.create(
        name="Ubisoft",
        webhook_url="https://example.com",
        webhook_secret="hidden",
        user=user,
    )

    serializer = PublisherSerializer(publisher)

    assert "webhook_secret" not in serializer.data