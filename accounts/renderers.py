from rest_framework.renderers import JSONRenderer
from rest_framework.utils import encoders
from bson import ObjectId

class CustomJSONEncoder(encoders.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

class MongoJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that automatically handles MongoDB ObjectId serialization.
    """
    encoder_class = CustomJSONEncoder
