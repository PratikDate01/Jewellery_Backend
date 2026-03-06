from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Reset a user password safely'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email address')
        parser.add_argument('password', type=str, help='New password')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("PASSWORD RESET")
        self.stdout.write("="*70)
        
        try:
            user = User.objects.get(email=email)
            
            self.stdout.write(f"\nResetting password for: {user.email}")
            self.stdout.write(f"Name: {user.name}")
            self.stdout.write(f"Role: {user.role}")
            
            user.set_password(password)
            user.save()
            
            self.stdout.write(self.style.SUCCESS("\n[SUCCESS] Password has been reset!"))
            
            verification = user.check_password(password)
            self.stdout.write(f"Verification test: {verification}")
            
            if verification:
                self.stdout.write(self.style.SUCCESS("[OK] New password is working correctly!"))
            else:
                self.stdout.write(self.style.ERROR("[ERROR] Password verification failed after reset!"))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"[ERROR] User not found: {email}"))
            self.stdout.write("\nAvailable users:")
            for u in User.objects.all():
                self.stdout.write(f"  - {u.email}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[ERROR] {e}"))
            import traceback
            traceback.print_exc()
        
        self.stdout.write("\n" + "="*70 + "\n")
