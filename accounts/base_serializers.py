from rest_framework import serializers
from bson import ObjectId

class BaseMongoSerializer(serializers.ModelSerializer):
    """
    Base serializer that ensures all ObjectId fields are converted to strings in the response.
    """
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return self._convert_objectid(ret)

    def _convert_objectid(self, data):
        if isinstance(data, ObjectId):
            return str(data)
        if isinstance(data, list):
            return [self._convert_objectid(item) for item in data]
        if isinstance(data, dict):
            return {key: self._convert_objectid(value) for key, value in data.items()}
        return data
