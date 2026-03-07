from rest_framework import serializers
from .models import Category
from accounts.fields import ObjectIdField

class CategorySerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = Category
        fields = '__all__'

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if 'parent' in ret and ret['parent']:
            ret['parent'] = str(ret['parent'])
        return ret
