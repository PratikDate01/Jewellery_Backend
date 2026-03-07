from rest_framework import serializers
from .models import Category
from accounts.fields import ObjectIdField
from accounts.serializers import BaseMongoSerializer

class CategorySerializer(BaseMongoSerializer):
    id = ObjectIdField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = Category
        fields = '__all__'
