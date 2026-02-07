from bson.decimal128 import Decimal128
from bson import ObjectId
from datetime import datetime

def serialize_mongo_value(value):
    if isinstance(value, Decimal128):
        return float(value.to_decimal())
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value
