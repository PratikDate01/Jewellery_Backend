from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class Command(BaseCommand):
    help = 'Debug authentication issue'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email address')
        parser.add_argument('--password', type=str, default='Pratik@2006', help='Password to test')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("AUTHENTICATION DEBUG")
        self.stdout.write("="*70 + "\n")
        
        try:
            user = User.objects.get(email=email)
            
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"Name: {user.name}")
            self.stdout.write(f"Is Active: {user.is_active}")
            self.stdout.write(f"Is Staff: {user.is_staff}")
            self.stdout.write(f"\nPassword Hash:")
            self.stdout.write(f"{user.password}\n")
            
            self.stdout.write("Test 1: Direct check_password() method")
            self.stdout.write("-" * 50)
            result1 = user.check_password(password)
            self.stdout.write(f"Result: {result1}")
            self.stdout.write(f"Type: {type(result1)}\n")
            
            self.stdout.write("Test 2: Django authenticate() backend")
            self.stdout.write("-" * 50)
            result2 = authenticate(request=None, username=email, password=password)
            self.stdout.write(f"Result: {result2}")
            if result2:
                self.stdout.write(f"Authenticated as: {result2.email}")
            self.stdout.write()
            
            self.stdout.write("Test 3: Test with wrong password")
            self.stdout.write("-" * 50)
            result3 = user.check_password("wrongpassword")
            self.stdout.write(f"check_password('wrongpassword'): {result3}")
            self.stdout.write()
            
            self.stdout.write("Test 4: EmailBackend test")
            self.stdout.write("-" * 50)
            from accounts.backends import EmailBackend
            backend = EmailBackend()
            result4 = backend.authenticate(request=None, username=email, password=password)
            self.stdout.write(f"EmailBackend.authenticate(): {result4}")
            if result4:
                self.stdout.write(f"Authenticated as: {result4.email}")
            self.stdout.write()
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User not found: {email}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            import traceback
            traceback.print_exc()
        
        self.stdout.write("\n" + "="*70 + "\n")
