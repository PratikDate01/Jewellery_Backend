from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.backends import ModelBackend
from accounts.backends import EmailBackend
from accounts.fields import ObjectIdField
from accounts.base_serializers import BaseMongoSerializer
from bson import ObjectId

User = get_user_model()

class UserSerializer(BaseMongoSerializer):
    id = ObjectIdField(source='pk', read_only=True)
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'role', 'phone', 'address', 'profile_image', 'date_joined')
        read_only_fields = ('id', 'email', 'role', 'date_joined')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False)

    class Meta:
        model = User
        fields = ('email', 'name', 'password', 'password_confirm', 'phone', 'role')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_role(self, value):
        if value == 'ADMIN':
            raise serializers.ValidationError("Cannot register as an Admin. Admins must be created via management commands.")
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        role = validated_data.get('role', 'CUSTOMER')
        
        return User.objects.create_user(
            email=validated_data['email'],
            name=validated_data.get('name', ''),
            password=validated_data['password'],
            phone=validated_data.get('phone', ''),
            role=role
        )

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        backend = EmailBackend()
        user = backend.authenticate(request=None, email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        data['user'] = user
        return data

class TokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()

class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
