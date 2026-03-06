from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Create admin users from ADMIN_EMAILS with default password'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='Admin@123',
            help='Password for admin users (default: Admin@123)'
        )

    def handle(self, *args, **options):
        password = options['password']
        admin_emails = getattr(settings, 'ADMIN_EMAILS', [])

        if not admin_emails:
            self.stdout.write(self.style.WARNING("No ADMIN_EMAILS configured in settings"))
            return

        self.stdout.write(f"Creating/updating admin users with password: {password}\n")

        for email in admin_emails:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'name': email.split('@')[0].title(),
                    'is_active': True,
                }
            )

            user.set_password(password)
            user.role = 'ADMIN'
            user.is_staff = True
            user.is_superuser = True
            user.save()

            status = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] {status}: {email} (role: {user.role})"
                )
            )

        self.stdout.write(self.style.SUCCESS("\n[OK] All admin users created/updated successfully"))
