from django.core.management.base import BaseCommand
from django.utils import timezone

from games.models import GameKey


class Command(BaseCommand):
    help = "Mark active keys whose expiry has passed as expired."

    def handle(self, *args, **options):

        expired_keys = GameKey.objects.filter(
            expires_at__lte=timezone.now(),
            status="active"
        )

        count = expired_keys.update(status="expired")

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {count} keys."
            )
        )