import json
from bson import ObjectId
from flask import request
from ar_tunnel.utils.misc import JSONEncoder
from flask_restplus import Resource
from flask_restplus import reqparse
from flask_restplus import inputs

from ar_tunnel import api
from ar_tunnel import mongo

ARTIFACT_TYPES = ["botella", "figurina", "olla", "cantaro"]
DEFAULT_PERSONAL_INFO_MAP = {
    "type": {
        "type": str,
        "value": True,
        # TODO?
        "validateFunction": None
    },
    "name": {
        "type": str,
        "value": True,
        "validateFunction": None
    },
    "latitude": {
        "type": float,
        "value": True,
        "validateFunction": None
    },
    "longitude": {
        "type": float,
        "value": True,
        "validateFunction": None
    }
}


class ArtifactResource(Resource):
    @property
    def artifacts(self):
        return mongo.db.artifacts


put_arguments = reqparse.RequestParser()
put_arguments.add_argument('type',
                           choices=ARTIFACT_TYPES,
                           required=True)
put_arguments.add_argument('name', type=str, required=True)
put_arguments.add_argument('latitude', type=float, required=True)
put_arguments.add_argument('longitude', type=float, required=True)

get_arguments = reqparse.RequestParser()
get_arguments.add_argument('group_by_type',
                           type=inputs.boolean,
                           required=False)
get_arguments.add_argument('user', type=str, required=False)

@api.route("/artifact/")
class Artifacts(ArtifactResource):
    @api.expect(get_arguments, validate=True)
    def get(self):
        """
        Gets all the artifacts.
        """
        fields = get_arguments.parse_args()
        group_by_type = fields["group_by_type"]
        user = fields["user"]

        if user is None or group_by_type is None:
            objs = self.artifacts.find()
            ret = []
            for obj in objs:
                obj["_id"] = str(obj["_id"])
                ret.append(obj)
            return ret
        elif group_by_type and user is not None:
            cursor = self._group_by_type(user)
            ret = {}
            for item in cursor:
                type_ = item["_id"]["type"]
                ret[type_] = []
                for artifact in item["artifacts"]:
                    artifact["collected"] = len(artifact["items"]) == 1
                    del artifact["items"]
                    ret[type_].append(artifact)
            return json.loads(JSONEncoder().encode(ret))
        return {"message": "Not supported"}

    @api.expect(put_arguments, validate=True)
    def post(self):
        """
        Creates an artifact.
        :raises DuplicateKeyError if the artifact already exists.
        """
        fields = put_arguments.parse_args()
        res = self.artifacts.insert_one(fields)
        return {"_id": str(res.inserted_id)}

    def _group_by_type(self, user_id):
        cursor = self.artifacts.aggregate([
            {
                "$lookup": {
                    "from": "users_artifacts",
                    "localField": "_id",
                    "foreignField": "artifact_id",
                    "as": "items"
                },
            },
            {
                "$project": {
                    "items.user_id": 1,
                    "type": 1,
                    "name": 1,
                    "latitude": 1,
                    "longitude": 1
                }
            },
            {
                "$project": {
                    "items": {
                        "$filter": {
                            "input": "$items",
                            "as": "item",
                            "cond": {
                                "$eq": ["$$item.user_id", ObjectId(user_id)]
                            }
                        }
                    },
                    "type": 1, "name": 1, "latitude": 1, "longitude": 1
                }
            },
            {
                "$group": {
                    "_id": {"type": "$type" },
                    "artifacts": { "$push": "$$ROOT"}
                }
            }
        ])
        return cursor


arguments_get = reqparse.RequestParser()
arguments_get.add_argument("fields", action='split')


@api.route("/artifact/<id>")
class Artifact(ArtifactResource):
    @api.expect(arguments_get, validate=True)
    def get(self, id):
        """
        Gets an artifact.
        """
        filter_ = {}
        fields = arguments_get.parse_args()["fields"]
        if fields is not None:
            for field in DEFAULT_PERSONAL_INFO_MAP:
                if field in fields:
                    filter_[field] = True
        if filter_:
            obj = self.artifacts.find_one({"_id": ObjectId(id)}, filter_)
        else:
            obj = self.artifacts.find_one({"_id": ObjectId(id)})
        obj["_id"] = str(obj["_id"])
        return obj

    def delete(self, id):
        """
        Deletes an artifact.
        """
        print("DELETE")
        self.artifacts.delete_one({"_id": ObjectId(id)})
        mongo.db.users_artifacts.remove({"artifact_id": ObjectId(id)})
