import datetime
import json
import hashlib
from bson import ObjectId
from flask import request
from flask_restplus import Api
from flask_restplus import Resource
from flask_restplus import reqparse
from ar_tunnel.utils.error_handling import ARChecks
from ar_tunnel.utils.error_handling import ARException
from ar_tunnel.utils.misc import info_map_to_info
from ar_tunnel.utils.misc import JSONEncoder
from ar_tunnel.models.artifact import ARTIFACT_TYPES
from ar_tunnel import api
from ar_tunnel import mongo
from flask_restplus import inputs


DEFAULT_PERSONAL_INFO_MAP = {
    "active": {
        "type": bool,
        "value": True,
        "validateFunction": None
    },
    "createdAt": {
        "type": datetime.datetime,
        "value": None,
        "validateFunction": None
    },
    "email": {
        "type": str,
        "value": None,
        "validateFunction": ARChecks.ensure_valid_email
    },
    "gender": {
        "type": str,
        "value": None,
        "validateFunction": None
    },
    "isTutorialDone": {
        "type": str,
        "value": None,
        "validateFunction": None
    },
    "level": {
        "type": int,
        "value": 1,
        "validateFunction": None
    },
    "nickname": {
        "type": str,
        "value": None,
        "validateFunction": None
    },
}
DEFAULT_PERSONAL_INFO = info_map_to_info(DEFAULT_PERSONAL_INFO_MAP)

DEFAULT_AWARDS_MAP = {
    "digQuantity": {
        "type": int,
        "value": 0,
        "validateFunction": None
    },
    "gatherQuantity": {
        "type": int,
        "value": 0,
        "validateFunction": None
    },  
    "searchQuantity": {
        "type": int,
        "value": 0,
        "validateFunction": None
    }
}
DEFAULT_AWARDS = info_map_to_info(DEFAULT_AWARDS_MAP)

DEFAULT_RECOLECTED_ITEMS_MAP = {
    "current_bottles": {
        "type": int,
        "value": 0,
        "validateFunction": None
    },
    "current_figurines": {
        "type": int,
        "value": 0,
        "validateFunction": None
    },
    "current_pitchers": {
        "type": int,
        "value": 0,
        "validateFunction": None
    },
    "current_plots": {
        "type": int,
        "value": 0,
        "validateFunction": None
    }
}
DEFAULT_RECOLECTED_ITEMS = info_map_to_info(DEFAULT_RECOLECTED_ITEMS_MAP)


arguments_post = reqparse.RequestParser()
arguments_post.add_argument('nickname', type=str, required=True)
arguments_post.add_argument('email', type=str, required=True)
arguments_post.add_argument('password', type=str, required=True)
arguments_post.add_argument('gender', choices=["male", "female"],
                            type=str, required=True)


class UserResource(Resource):
    @property
    def users(self):
        return mongo.db.users

    @property
    def users_artifacts(self):
        return mongo.db.users_artifacts


@api.route("/user/")
class Users(UserResource):
    def get(self):
        """
        Gets all the users.
        """
        filter_ = {
            "PersonalInfo.nickname": True,
            "PersonalInfo.email": True,
        }
        cursor = self.users.find({}, filter_)
        ret = []
        for obj in cursor:
            obj["_id"] = str(obj["_id"])
            ret.append(obj)
        return ret

    @api.expect(arguments_post, validate=True)
    def post(self):
        """
        Creates an user.
        :raises DuplicateKeyError if the artifact already exists.
        """
        nickname = request.args.get('nickname')
        email = request.args.get('email')
        password = request.args.get('password')
        gender = request.args.get('gender')

        ARChecks.ensure_valid_email(email)
        ARChecks.ensure_valid_password(password)
        ARChecks.User.ensure_valid_gender(gender)

        personal_info = DEFAULT_PERSONAL_INFO.copy()
        personal_info["createdAt"] = datetime.datetime.utcnow()
        personal_info["email"] = email
        personal_info["gender"] = gender
        personal_info["nickname"] = nickname
        personal_info["password"] =\
            hashlib.sha256(password.encode("utf-8")).hexdigest()
        awards = DEFAULT_AWARDS.copy()
        recolected_items = DEFAULT_RECOLECTED_ITEMS.copy()

        res = self.users.insert_one({
            "PersonalInfo": personal_info,
            "Awards": awards,
            "CollectedItems": {}
        })
        return {"_id": str(res.inserted_id)}


arguments_put = reqparse.RequestParser()
for arg in DEFAULT_PERSONAL_INFO_MAP:
    if arg == "createdAt":
        continue
    arguments_put.add_argument(arg, type=DEFAULT_PERSONAL_INFO_MAP[arg]["type"],
                               required=False)

arguments_get = reqparse.RequestParser()
arguments_get.add_argument("fields", action='split')


@api.route("/user/<id>/personalInfo")
class UserPersonalInfo(UserResource):

    @api.expect(arguments_put, validate=True)
    def put(self, id):
        """
        Updates the user's personal information.
        """
        data = {}
        for arg in arguments_put.args:
            value = request.args.get(arg.name)
            if value is not None and arg.name in DEFAULT_AWARDS_MAP:
                type_ = DEFAULT_PERSONAL_INFO_MAP[arg.name]["type"]
                validate_func =\
                    DEFAULT_PERSONAL_INFO_MAP[arg.name]["validateFunction"]
                value = type_(value)
                if validate_func is not None:
                    validate_func(value)
                data["PersonalInfo.%s" % arg.name] = value
        self.users.update({"_id": ObjectId(id)},
                          {"$set": data})

    @api.expect(arguments_get, validate=True)
    def get(self, id):
        """
        Gets the user's personal information.
        """
        filter_ = {"PersonalInfo": True}
        fields = arguments_get.parse_args()["fields"]
        if fields is not None:
            for field in DEFAULT_PERSONAL_INFO_MAP:
                if field in fields:
                    filter_["PersonalInfo.%s" % field] = True
        obj = self.users.find_one({"_id": ObjectId(id)}, filter_)
        obj["_id"] = str(obj["_id"])

        if "createdAt" in obj["PersonalInfo"]:
            obj["PersonalInfo"]["createdAt"] =\
                str(obj["PersonalInfo"]["createdAt"])
        if "password" in obj["PersonalInfo"]:
            del obj["PersonalInfo"]["password"]
        return obj


arguments_user_awards_put = reqparse.RequestParser()
for arg in DEFAULT_AWARDS_MAP:
    arguments_user_awards_put.add_argument(
        arg, type=DEFAULT_AWARDS_MAP[arg]["type"], required=False)
arguments_user_awards_put.add_argument("_increase", type=inputs.boolean,
    required=False,
    help="If 'true', then increments rest of fields by the given values")


@api.route("/user/<id>/awards")
class UserAwards(UserResource):
    @api.expect(arguments_user_awards_put, validate=True)
    def put(self, id):
        """
        Updates the user's awards.
        """
        data = {}
        for arg in arguments_user_awards_put.args:
            value = request.args.get(arg.name)
            if value is not None and arg.name in DEFAULT_AWARDS_MAP:
                type_ = DEFAULT_AWARDS_MAP[arg.name]["type"]
                validate_func =\
                    DEFAULT_AWARDS_MAP[arg.name]["validateFunction"]
                value = type_(value)
                if validate_func is not None:
                    validate_func(value)
                data["Awards.%s" % arg.name] = value

        increase = bool(arguments_user_awards_put.parse_args()["_increase"])
        op = "$set" if not increase else "$inc"
        self.users.update({"_id": ObjectId(id)}, {op: data})

    @api.expect(arguments_get, validate=True)
    def get(self, id):
        """
        Gets the user's awards.
        """
        filter_ = {"Awards": True}
        fields = arguments_get.parse_args()["fields"]
        if fields is not None:
            for field in DEFAULT_AWARDS_MAP:
                if field in fields:
                    filter_["Awards.%s" % field] = True
        obj = self.users.find_one({"_id": ObjectId(id)}, filter_)
        obj["_id"] = str(obj["_id"])
        return obj


arguments_user_collected_items_get = reqparse.RequestParser()
arguments_user_collected_items_get.add_argument("types", type=inputs.boolean,
                                                required=False)

arguments_user_collected_items_put = reqparse.RequestParser()
arguments_user_collected_items_put.add_argument("artifact_id", type=str,
                                                required=False)
arguments_user_collected_items_put.add_argument("value", type=int,
                                                required=True)
arguments_user_collected_items_put.add_argument("_increase",
                                                type=inputs.boolean,
                                                required=False)


@api.route("/user/<id>/collectedItems/")
class UserCollectedItems(UserResource):
    @api.expect(arguments_user_collected_items_get, validate=True)
    def get(self, id):
        """Gets the user's collected items."""
        ARChecks.User.ensure_existent_user(mongo.db.users, id)

        parser = arguments_user_collected_items_get.parse_args()
        types = parser["types"]

        obj = {"_id": id, "CollectedItems": []}
        if not types:
            cursor = self._get_artifact_types(id)
        else:
            cursor = self._count_by_artifact_type(id)

        if cursor.alive:
            obj = cursor.next()
        return json.loads(JSONEncoder().encode(obj))


    @api.expect(arguments_user_collected_items_put, validate=True)
    def put(self, id):
        parser = arguments_user_collected_items_put.parse_args()
        artifact_id = parser["artifact_id"]
        value = parser["value"]
        increase = bool(parser["_increase"])

        ARChecks.Artifact.ensure_existent_artifact(mongo.db.artifacts,
                                                   artifact_id)
        ARChecks.User.ensure_existent_user(mongo.db.users, id)

        if not increase and value == 0:
            self.users_artifacts.remove({"user_id": ObjectId(id),
                                         "artifact_id": ObjectId(artifact_id)})
        else:
            op = "$set" if not increase else "$inc"
            self.users_artifacts.update(
                {"user_id": ObjectId(id), "artifact_id": ObjectId(artifact_id)},
                {op: {"value": value}},
                upsert=True
            )

    def _get_artifact_types(self, id):
        cursor = self.users_artifacts.aggregate([
            {"$match": {"user_id": ObjectId(id)}},
            {
                "$lookup": {
                    "from": "artifacts",
                    "localField": "artifact_id",
                    "foreignField": "_id",
                    "as": "artifact"
                }
            },
            {"$unwind": "$artifact"},
            {
                "$addFields": {
                    "item": {"_id": "$artifact_id", "value": "$value"}
                }
            },
            {
                "$group": {
                    "_id": "$_id.user_id",
                    "CollectedItems": { "$push": "$item" }
                }
            }
        ])
        return cursor


    def _count_by_artifact_type(self, id):
        cursor = self.users_artifacts.aggregate([
            {"$match": {"user_id": ObjectId(id)}},
            {
                "$lookup": {
                    "from": "artifacts",
                    "localField": "artifact_id",
                    "foreignField": "_id",
                    "as": "artifacts"
                }
            },
            {"$unwind": "$artifacts"},
            {
                "$group": {
                    "_id": {
                        "user_id": "$user_id",
                        "artifact_type": "$artifacts.type"
                    },
                    "artifacts": { "$mergeObjects": "$artifacts" },
                    "total": { "$sum": "$value" }
                }
            },
            {
                "$addFields": {
                    "CollectedItems": {
                        "type": "$_id.artifact_type",
                        "total": "$total"
                    }
                }
            },
            {
                "$group": {
                    "_id": "$_id.user_id",
                    "CollectedItems": { "$push": "$CollectedItems" }
                }
            }
        ])
        return cursor


@api.route("/user/<id>")
class User(UserResource):
    def delete(self, id):
        """Deletes an user from the database."""
        self.users.delete_one({"_id": ObjectId(id)})
        self.users_artifacts.remove({"_id": ObjectId(id)})


arguments_user_login_post = reqparse.RequestParser()
arguments_user_login_post.add_argument("nickname", type=str, location='form',
                                       required=True)
arguments_user_login_post.add_argument("password", type=str, location='form',
                                       required=True)


@api.route("/user/login")
class UserLogin(UserResource):
    @api.expect(arguments_user_login_post, validate=True)
    def post(self):
        """
        Given an user and password tells if they matches in the database.

        Returns: The id of the user.
        """
        parser = arguments_user_login_post.parse_args()
        # TODO
        # Check nickname and password are not null.
        nickname = parser["nickname"]
        password =\
            hashlib.sha256(parser["password"].encode("utf-8")).hexdigest()

        project = {"_id": True}
        data = {
            "PersonalInfo.nickname": nickname,
            "PersonalInfo.password": password
        }
        obj = self.users.find_one(data, project)
        if obj is None:
            data = {
                "PersonalInfo.email": nickname,
                "PersonalInfo.password": password
            }
            obj = self.users.find_one(data, project)
        if obj is None:
            return {"message": "Invalid"}
        # TODO
        # This should return actually a token.
        obj["_id"] = str(obj["_id"])
        return obj
