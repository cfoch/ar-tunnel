from bson import ObjectId
from flask import request
from flask_restplus import Resource
from flask_restplus import reqparse
from flask_restplus import inputs

from ar_tunnel import api
from ar_tunnel import mongo

ARTIFACT_TYPES = ["botella", "figurina", "olla", "jarron"]
DEFAULT_PERSONAL_INFO_MAP = {
    "type": {
        "type": str,
        "value": True,
        # TODO?
        "validateFunction": None
    },
    "path": {
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
put_arguments.add_argument('path', type=str, required=False)
put_arguments.add_argument('latitude', type=float, required=True)
put_arguments.add_argument('longitude', type=float, required=True)


@api.route("/artifact/")
class Artifacts(ArtifactResource):
    def get(self):
        """
        Gets all the artifacts.
        """
        objs = self.artifacts.find()
        ret = []
        for obj in objs:
            obj["_id"] = str(obj["_id"])
            ret.append(obj)
        print(ret)
        return ret

    @api.expect(put_arguments, validate=True)
    def post(self):
        """
        Creates an artifact.
        :raises DuplicateKeyError if the artifact already exists.
        """
        fields = put_arguments.parse_args()
        res = self.artifacts.insert_one(fields)
        return {"_id": str(res.inserted_id)}


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
