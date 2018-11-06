import uuid
import datetime
from flask import Flask
from flask import request
from flask_pymongo import PyMongo
from flask_restplus import Api, Resource, fields, reqparse

from pymongo.errors import DuplicateKeyError
from werkzeug.exceptions import BadRequest




from IPython import embed

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/testdb"

api = Api(
    app,
    version='0.1',
    title='ArqueoPUCP DB API',
    description='API para obtener y actualizar datos de jugadores.'
)

mongo = PyMongo(app)






@api.errorhandler(DuplicateKeyError)
def error_mongo_duplicate_key(error):
    """Returns a duplicate key error"""
    return {"message": "Duplicate key error"}


arguments = reqparse.RequestParser()
arguments.add_argument('latitude', type=float, required=True)
arguments.add_argument('longitude', type=float, required=True)


@api.route("/artifact/<id>")
class Artifact(Resource):
    @api.expect(arguments, validate=True)
    def put(self, id):
        """
        Creates an artifact.
        :raises DuplicateKeyError if the artifact already exists.
        """
        latitude = float(request.args.get('latitude'))
        longitude = float(request.args.get('longitude'))

        self.artifacts.insert_one({
            "_id": id,
            "latitude": latitude,
            "longitude": longitude
        })

    def get(self, id):
        """
        Gets an artifact.
        """
        return self.artifacts.find_one({"_id": id})

    def delete(self, id):
        """
        Deletes an artifact.
        """
        self.artifacts.delete_one({"_id": id})

    @property
    def artifacts(self):
        return mongo.db.artifacts



class ARException:
    class User:
        class InvalidGender(Exception):
            pass

    class InvalidEmail(Exception):
        pass

    class InvalidPassword(Exception):
        pass


from validate_email import validate_email


class ARChecks:
    class User:
        @staticmethod
        def ensure_valid_gender(gender):
            raise ARException.User.InvalidGender

    @staticmethod
    def ensure_valid_email(email):
        raise ARException.InvalidEmail

    @staticmethod
    def ensure_valid_password(password):
        raise ARException.InvalidPassword


@api.errorhandler(ARException.User.InvalidGender)
def error_user_invalid_gender(error):
    return {"message": "Gender should be 'male' or 'female'."}


@api.errorhandler(ARException.InvalidEmail)
def error_invalid_email(error):
    return {"message": "E-mail format is invalid."}

@api.errorhandler(ARException.InvalidPassword)
def error_invalid_password(error):
    return {"message": "Password is not a sha-256 encrypted string."}


arguments_put = reqparse.RequestParser()
arguments_put.add_argument('nickname', type=str, required=True)
arguments_put.add_argument('email', type=str, required=True)
arguments_put.add_argument('password', type=str, required=True)
arguments_put.add_argument('gender', type=str, required=True)


@api.route("/user/create/<id>")
class User(Resource):

    DEFAULT_PERSONAL_INFO = {
        "active": True,
        "createdAt": None,
        "email": None,
        "gender": None,
        "isTutorialDone": False,
        "level": 1,
        "nickname": None
    }

    DEFAULT_AWARDS = {
        "digQuantity": 0,
        "gatherQuantity": 0,
        "searchQuantity": 0
    }

    DEFAULT_RECOLECTED_ITEMS = {
        "current_bottles": 0,
        "current_figurines": 0,
        "current_pitchers": 0,
        "current_plots": 0,
    }

    @api.expect(arguments, validate=True)
    def put(self, id):
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

        personal_info = User.DEFAULT_PERSONAL_INFO.copy()
        personal_info["createdAt"] = datetime.datetime.utcnow()
        personal_info["email"] = email
        personal_info["gender"] = gender
        personal_info["nickname"] = nickname
        awards = User.DEFAULT_AWARDS.copy()
        recolected_items = User.DEFAULT_RECOLECTED_ITEMS.copy()

        return self.artifacts.insert_one({
            "PersonalInfo": personal_info,
            "Awards": awards,
            "RecolectedItems": recolected_items
        })

    @property
    def users(self):
        return mongo.db.users


if __name__ == '__main__':
    app.run(debug=True)
