from django.core.management.base import BaseCommand
from django.utils import timezone

from games.models import GameKey
from games.webhooks import send_expiry_webhook


class Command(BaseCommand):
    help = "Mark expired keys and notify publishers synchronously."

    def handle(self, *args, **options):

        expired_keys = (
            GameKey.objects
            .select_related("game__publisher")
            .filter(
                expires_at__lte=timezone.now(),
                status="active"
            )
        )

        count = expired_keys.update(status="expired")

        for key in (
            GameKey.objects
            .filter(status="expired")
            .select_related("game__publisher")
        ):
            send_expiry_webhook(
                key.game.publisher,
                key.key_string,
                key.game.title,
                key.expires_at
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {count} keys (sync webhooks sent)."
            )
        )