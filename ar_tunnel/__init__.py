from flask import Flask
from flask_pymongo import PyMongo
from flask_restplus import Api

def init_db(mongo):
    mongo.db.users.create_index("PersonalInfo.email", unique=True)
    mongo.db.users.create_index("PersonalInfo.nickname", unique=True)
    mongo.db.users_artifacts.create_index([("user_id", 1), ("artifact_id", 1)],
                                          unique=True)
    mongo.db.artifacts.create_index("name", unique=True)

app = Flask(__name__)
api = Api(
    app,
    version='0.1',
    title='ArqueoPUCP DB API',
    description='API para obtener y actualizar datos de jugadores.'
)
mongo = PyMongo()
