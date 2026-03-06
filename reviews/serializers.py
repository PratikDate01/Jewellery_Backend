from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Review
        fields = ('id', 'user', 'user_email', 'product', 'rating', 'comment', 'image', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'user_email', 'created_at', 'updated_at')
