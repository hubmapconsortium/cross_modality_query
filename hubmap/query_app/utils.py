import hashlib
import json
import pickle
from collections import OrderedDict
from datetime import datetime

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpResponse
from pymongo import MongoClient

from .models import Cell, Cluster, Dataset, Gene, Organ, Protein

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
    db.log_events.createIndex({"created_at": 1}, {expireAfterSeconds: TOKEN_EXPIRATION_TIME})
    return


def set_intersection(query_set_1, query_set_2):
    return query_set_1 & query_set_2


def set_union(query_set_1, query_set_2):
    return query_set_1 | query_set_2


def make_pickle_and_hash(qs, set_type):
    client = MongoClient(MONGO_HOST_AND_PORT)
    collection = client[MONGO_DB_NAME][MONGO_COLLECTION_NAME]

    qry = qs.query
    query_pickle = pickle.dumps(qry)
    query_handle = str(hashlib.sha256(query_pickle).hexdigest())

    doc = {
        "query_handle": query_handle,
        "query_pickle": query_pickle,
        "set_type": set_type,
        "created_at": datetime.utcnow(),
    }
    collection.insert_one(doc)

    return query_handle


def unpickle_query_set(query_handle):
    client = MongoClient(MONGO_HOST_AND_PORT)
    collection = client[MONGO_DB_NAME][MONGO_COLLECTION_NAME]

    query_object = collection.find_one({"query_handle": query_handle})
    if query_object is None:
        raise ValueError(f"Query handle {query_handle} is not valid")
    query_pickle = query_object["query_pickle"]
    set_type = query_object["set_type"]

    if set_type == "cell":
        qs = Cell.objects.all()

    elif set_type == "gene":
        qs = Gene.objects.all()

    elif set_type == "cluster":
        qs = Cluster.objects.all()

    elif set_type == "organ":
        qs = Organ.objects.all()

    elif set_type == "dataset":
        qs = Dataset.objects.all()

    elif set_type == "protein":
        qs = Protein.objects.all()

    qs.query = pickle.loads(query_pickle)

    return qs, set_type


def get_database_status():
    db_conn = connections["default"]
    try:
        c = db_conn.cursor()
    except OperationalError:
        connected = False
    else:
        connected = True
    return connected


def get_app_status():
    json_file_path = "/opt/cross-modality-query/version.json"
    with open(json_file_path) as file:
        json_dict = json.load(file)
        json_dict["Postgres connection"] = get_database_status()
        return json.dumps(json_dict)


def get_response_from_query_handle(query_handle: str, set_type: str):
    query_dict = OrderedDict()
    query_dict["query_handle"] = query_handle
    query_dict["set_type"] = set_type
    response_dict = OrderedDict()
    response_dict["count"] = 1
    response_dict["next"] = None
    response_dict["previous"] = None
    response_dict["results"] = [query_dict]
    response_string = json.dumps(response_dict)
    return HttpResponse(response_string)


def get_response_with_count_from_query_handle(query_handle: str):
    query_dict = OrderedDict()
    query_dict["query_handle"] = query_handle
    query_set, set_type = unpickle_query_set(query_handle)
    query_dict["set_type"] = set_type
    query_dict["count"] = query_set.count
    response_dict = OrderedDict()
    response_dict["count"] = 1
    response_dict["next"] = None
    response_dict["previous"] = None
    response_dict["results"] = [query_dict]
    response_string = json.dumps(response_dict)
    return HttpResponse(response_string)
