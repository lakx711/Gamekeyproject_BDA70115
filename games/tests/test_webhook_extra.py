from unittest.mock import patch

from django.contrib.auth.models import User

from games.models import Publisher
from games.webhooks import send_expiry_webhook

from datetime import datetime


@patch("games.webhooks.requests.post")
def test_webhook_success(mock_post):

    publisher = Publisher(
        id=1,
        name="EA",
        webhook_url="https://example.com",
        webhook_secret="secret",
        user=User(),
    )

    mock_post.return_value.raise_for_status.return_value = None

    send_expiry_webhook(
        publisher,
        "ABC123",
        "FIFA",
        datetime.now(),
    )

    assert mock_post.called