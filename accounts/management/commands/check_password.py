from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Check if user password is hashed correctly'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email address')
        parser.add_argument('--password', type=str, help='Password to test')

    def handle(self, *args, **options):
        email = options['email']
        password = options.get('password') or 'Pratik@2006'
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("PASSWORD DIAGNOSTIC REPORT")
        self.stdout.write("="*70)
        
        try:
            user = User.objects.get(email=email)
            
            self.stdout.write(f"\nEmail: {user.email}")
            self.stdout.write(f"Name: {user.name}")
            self.stdout.write(f"Role: {user.role}")
            
            self.stdout.write(f"\nPassword Hash (first 80 chars):")
            self.stdout.write(f"{user.password[:80]}...\n")
            
            if not user.password:
                self.stdout.write(self.style.ERROR("[ERROR] Password is EMPTY/NULL"))
            elif user.password.startswith("pbkdf2_sha256"):
                self.stdout.write(self.style.SUCCESS("[OK] Password is HASHED (pbkdf2_sha256)"))
                
                password_clean = password.strip('"\'')
                test = user.check_password(password_clean)
                
                self.stdout.write(f"\nPassword: {password}")
                self.stdout.write(f"Password (cleaned): {password_clean}")
                self.stdout.write(f"check_password() result: {test}\n")
                
                if not test:
                    self.stdout.write(self.style.WARNING("[WARNING] Password verification FAILED!"))
                    self.stdout.write("\nPossible causes:")
                    self.stdout.write("1. Wrong password - user was created with different password")
                    self.stdout.write("2. Password was manually set without hashing")
                    self.stdout.write("3. Database corruption")
                    self.stdout.write("4. Different hash algorithm issue")
                else:
                    self.stdout.write(self.style.SUCCESS("[SUCCESS] Password is correct!"))
            elif user.password.startswith("argon2"):
                self.stdout.write(self.style.SUCCESS("[OK] Password is HASHED (argon2)"))
                test = user.check_password(password)
                self.stdout.write(f"\nPassword check: {test}")
            elif user.password.startswith("bcrypt"):
                self.stdout.write(self.style.SUCCESS("[OK] Password is HASHED (bcrypt)"))
                test = user.check_password(password)
                self.stdout.write(f"\nPassword check: {test}")
            else:
                self.stdout.write(self.style.ERROR("[ERROR] PASSWORD IS STORED AS RAW TEXT!"))
                self.stdout.write(f"Raw value: {user.password}")
                
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
