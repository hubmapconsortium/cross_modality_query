from django.apps import AppConfig
from django.conf import settings
from pymongo import MongoClient

MONGO_USERNAME = "root"
MONGO_PASSWORD = settings.MONGO_PASSWORD
MONGO_HOSTNAME = "18.207.164.186"
MONGO_PORT = "27017"
MONGO_HOST_AND_PORT = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOSTNAME}:{MONGO_PORT}/"
MONGO_DB_NAME = "token_store"
MONGO_COLLECTION_NAME = "pickles_and_hashes"
TOKEN_EXPIRATION_TIME = 14400  # 4 hours in seconds


def set_up_mongo():
    client = MongoClient(MONGO_HOST_AND_PORT)
    db = client[MONGO_DB_NAME]
    db.log_events.createIndex({"created_at": 1}, {"expireAfterSeconds": TOKEN_EXPIRATION_TIME})
    return


class QueryAppConfig(AppConfig):
    name = "query_app"
