from rest_framework import serializers
from bson import ObjectId

class ObjectIdField(serializers.Field):
    """
    Serializer field for MongoDB ObjectId.
    """
    def to_representation(self, value):
        if not value:
            return None
        return str(value)

    def to_internal_value(self, data):
        if not data:
            return None
        try:
            return ObjectId(str(data))
        except Exception:
            raise serializers.ValidationError(f"Invalid ObjectId: {data}")
