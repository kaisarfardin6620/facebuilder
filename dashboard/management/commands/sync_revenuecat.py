from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from payments.services import verify_subscription_status

User = get_user_model()

class Command(BaseCommand):
    help = 'Checks RevenueCat status for ALL users and updates the Dashboard'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        count = users.count()
        
        self.stdout.write(f"Syncing {count} users with RevenueCat...")

        for user in users:
            self.stdout.write(f"Checking user: {user.phone_number}...")
            try:
                is_active = async_to_sync(verify_subscription_status)(user)
                status = "PREMIUM" if is_active else "FREE"
                self.stdout.write(self.style.SUCCESS(f" -> Updated: {status}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f" -> Failed: {e}"))

        self.stdout.write(self.style.SUCCESS("-----------------------------"))
        self.stdout.write(self.style.SUCCESS("Global Sync Complete! Check Dashboard now."))