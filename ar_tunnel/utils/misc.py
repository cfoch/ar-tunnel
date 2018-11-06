import json
from bson import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def info_map_to_info(info_map):
    return {key:info_map[key]["value"] for key in info_map}
