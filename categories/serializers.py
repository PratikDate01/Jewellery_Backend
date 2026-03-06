from rest_framework import serializers
from .models import Category
from accounts.fields import ObjectIdField

class CategorySerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    class Meta:
        model = Category
        fields = '__all__'
