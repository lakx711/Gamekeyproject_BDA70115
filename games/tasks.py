import hmac
import hashlib
import json

import requests

from celery import shared_task

from .models import Publisher, WebhookDeliveryLog


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_expiry_webhook_async(
    self,
    publisher_id,
    game_key_str,
    game_title,
    expired_at_iso,
    attempt=0
):
    publisher = None
    payload = {}

    try:
        publisher = Publisher.objects.get(id=publisher_id)

        payload = {
            "event": "game_key.expired",
            "game_key": game_key_str,
            "game_title": game_title,
            "expired_at": expired_at_iso,
            "attempt": attempt,
        }

        secret = publisher.webhook_secret.encode("utf-8")
        body = json.dumps(payload, sort_keys=True).encode("utf-8")

        signature = hmac.new(
            secret,
            body,
            hashlib.sha256
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Signature": f"sha256={signature}",
        }

        response = requests.post(
            publisher.webhook_url,
            json=payload,
            headers=headers,
            timeout=5,
        )

        WebhookDeliveryLog.objects.create(
            game_key=game_key_str,
            publisher=publisher,
            payload=payload,
            response_status=response.status_code,
            attempt=attempt,
            success=response.status_code < 400,
        )

        if response.status_code >= 400:
            raise Exception(
                f"HTTP {response.status_code} from publisher endpoint"
            )

    except Exception as exc:

        if publisher:
            WebhookDeliveryLog.objects.create(
                game_key=game_key_str,
                publisher=publisher,
                payload=payload,
                error_message=str(exc),
                attempt=attempt,
                success=False,
            )

        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** attempt)
        )