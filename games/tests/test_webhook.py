import pytest

from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import timezone

from games.models import (
    Publisher,
    Game,
    GameKey,
    WebhookDeliveryLog,
)


# -------------------------
# Fixtures
# -------------------------

@pytest.fixture
def publisher_user(db):
    user = User.objects.create_user(
        username="pub_user",
        password="pass123"
    )

    publisher = Publisher.objects.create(
        name="Test Publisher",
        webhook_url="https://example.com/webhook",
        webhook_secret="supersecret",
        user=user,
    )

    return publisher


@pytest.fixture
def expired_game_key(db, publisher_user):
    game = Game.objects.create(
        title="Epic Game",
        publisher=publisher_user,
        price="29.99",
    )

    return GameKey.objects.create(
        key_string="TEST-KEY-0001",
        game=game,
        status="active",
        expires_at=timezone.now() - timedelta(hours=1),
        owner=publisher_user.user,
    )


# -------------------------
# Test 1
# -------------------------

@pytest.mark.django_db
@patch("games.tasks.send_expiry_webhook_async.delay")
def test_management_command_dispatches_tasks(
    mock_delay,
    expired_game_key
):
    call_command("check_expired_keys")

    assert mock_delay.called

    kwargs = mock_delay.call_args.kwargs

    assert kwargs["game_key_str"] == "TEST-KEY-0001"


# -------------------------
# Test 2
# -------------------------

@pytest.mark.django_db
@patch("games.tasks.requests.post")
def test_webhook_task_logs_success(
    mock_post,
    publisher_user,
    expired_game_key,
):
    from games.tasks import send_expiry_webhook_async

    response = MagicMock()
    response.status_code = 200

    mock_post.return_value = response

    send_expiry_webhook_async.apply(
        kwargs=dict(
            publisher_id=publisher_user.id,
            game_key_str="TEST-KEY-0001",
            game_title="Epic Game",
            expired_at_iso=expired_game_key.expires_at.isoformat(),
            attempt=0,
        )
    )

    log = WebhookDeliveryLog.objects.get(
        game_key="TEST-KEY-0001"
    )

    assert log.success is True
    assert log.response_status == 200


# -------------------------
# Test 3
# -------------------------

@pytest.mark.django_db
@patch("games.tasks.requests.post")
def test_webhook_task_logs_failure(
    mock_post,
    publisher_user,
    expired_game_key,
):
    from games.tasks import send_expiry_webhook_async

    mock_post.side_effect = Exception(
        "Connection refused"
    )

    send_expiry_webhook_async.apply(
        kwargs=dict(
            publisher_id=publisher_user.id,
            game_key_str="TEST-KEY-0001",
            game_title="Epic Game",
            expired_at_iso=expired_game_key.expires_at.isoformat(),
            attempt=0,
        )
    )

    log = WebhookDeliveryLog.objects.filter(
        game_key="TEST-KEY-0001",
        success=False,
    ).first()

    assert log is not None
    assert "Connection refused" in log.error_message