from django.core.management.base import BaseCommand
from django.utils import timezone

from games.models import GameKey
from games.tasks import send_expiry_webhook_async


class Command(BaseCommand):
    help = "Mark expired keys and dispatch async webhook notifications."

    def handle(self, *args, **options):

        expired_keys = (
            GameKey.objects
            .select_related("game__publisher")
            .filter(
                expires_at__lte=timezone.now(),
                status="active"
            )
        )

        keys_to_notify = list(expired_keys)

        count = expired_keys.update(status="expired")

        for key in keys_to_notify:
            send_expiry_webhook_async.delay(
                publisher_id=key.game.publisher.id,
                game_key_str=key.key_string,
                game_title=key.game.title,
                expired_at_iso=key.expires_at.isoformat(),
                attempt=0,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {count} keys. Webhook tasks dispatched to Celery."
            )
        )