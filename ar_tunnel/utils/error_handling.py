from bson import ObjectId
from validate_email import validate_email
from pymongo.errors import DuplicateKeyError
from ar_tunnel import api


class ARException:
    class User:
        class DoesNotExist(Exception):
            def __init__(self, user_id):
                super().__init__()
                self.user_id = user_id

        class InvalidGender(Exception):
            pass

    class Artifact:
        class DoesNotExist(Exception):
            def __init__(self, artifact_id):
                super().__init__()
                self.artifact_id = artifact_id

    class InvalidEmail(Exception):
        pass

    class InvalidPassword(Exception):
        pass


class ARChecks:
    class User:
        @staticmethod
        def ensure_valid_gender(gender):
            if gender in ["male", "female"]:
                return
            raise ARException.User.InvalidGender

        @staticmethod
        def ensure_existent_user(users, user_id):
            cursor = users.find({"_id": ObjectId(str(user_id))})
            valid = cursor.count() > 0
            if valid:
                return
            raise ARException.User.DoesNotExist(user_id)

    class Artifact:
        @staticmethod
        def ensure_existent_artifact(artifacts, artifact_id):
            cursor = artifacts.find({"_id": ObjectId(str(artifact_id))})
            valid = cursor.count() > 0
            if valid:
                return
            raise ARException.Artifact.DoesNotExist(artifact_id)

    @staticmethod
    def ensure_valid_email(email):
        if validate_email(email):
            return
        raise ARException.InvalidEmail

    @staticmethod
    def ensure_valid_password(password):
        # TODO
        # Implement
        if False:
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


# Models-related errors.
@api.errorhandler(ARException.Artifact.DoesNotExist)
def error_non_existent_artifact(error):
    return {"message": "Artifact with id '%s' does not exist." %
            error.artifact_id}

@api.errorhandler(ARException.User.DoesNotExist)
def error_non_existent_user(error):
    return {"message": "User with id '%s' does not exist." % error.user_id}


# MongoDB-related errors.

@api.errorhandler(DuplicateKeyError)
def error_mongo_duplicate_key(error):
    """Returns a duplicate key error"""
    return {"message": "Duplicate key error"}
