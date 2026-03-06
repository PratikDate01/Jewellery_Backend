from rest_framework import serializers
from .models import Review
from accounts.fields import ObjectIdField

class ReviewSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Review
        fields = ('id', 'user', 'user_email', 'product', 'rating', 'comment', 'image', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'user_email', 'created_at', 'updated_at')
