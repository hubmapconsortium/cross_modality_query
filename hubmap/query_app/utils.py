import hashlib
import json
import pickle
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import List

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpResponse
from pymongo import MongoClient

from .models import Cell, Cluster, Dataset, Gene, Organ, Protein


def set_intersection(query_set_1, query_set_2):
    return query_set_1 & query_set_2


def set_union(query_set_1, query_set_2):
    return query_set_1 | query_set_2


def make_pickle_and_hash(qs, set_type):
    client = MongoClient(settings.MONGO_HOST_AND_PORT)
    collection = client[settings.MONGO_DB_NAME][settings.MONGO_COLLECTION_NAME]

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
    client = MongoClient(settings.MONGO_HOST_AND_PORT)
    collection = client[settings.MONGO_DB_NAME][settings.MONGO_COLLECTION_NAME]

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
    paths = [
        Path("/opt/cross-modality-query/version.json"),
        Path("/opt/project/hubmap/version.json"),
        Path("/code/version.json"),
    ]
    for path in paths:
        try:
            with open(path) as f:
                json_dict = json.load(f)
                json_dict["postgres_connection"] = get_database_status()
                return json.dumps(json_dict)
        except FileNotFoundError:
            pass

    message_pieces = ["Couldn't find version.json. Tried:"]
    message_pieces.extend(f"\t{path}" for path in paths)
    raise FileNotFoundError("".join(message_pieces))


def infer_values_type(values: List) -> str:

    values = [
        split_at_comparator(item)[0].strip()
        if len(split_at_comparator(item)) > 0
        else item.strip()
        for item in values
    ]

    values_up = [value.upper() for value in values]
    values = values + values_up

    """Assumes a non-empty list of one one type of entity, and no identifier collisions across entity types"""
    if Gene.objects.filter(gene_symbol__in=values).count() > 0:
        return "gene"
    if Protein.objects.filter(protein_id__in=values).count() > 0:
        return "protein"
    if Cluster.objects.filter(grouping_name__in=values).count() > 0:
        return "cluster"
    if Organ.objects.filter(grouping_name__in=values).count() > 0:
        return "organ"
    values.sort()
    raise ValueError(
        f"Value type could not be inferred. None of {values} recognized as gene, protein, cluster, or organ"
    )


def split_at_comparator(item: str) -> List:
    """str->List
    Splits a string representation of a quantitative comparison into its parts
    i.e. 'eg_protein>=50' -> ['eg_protein', '>=', '50']
    If there is no comparator in the string, returns an empty list"""

    comparator_list = ["<=", ">=", ">", "<", "==", "!="]
    for comparator in comparator_list:
        if comparator in item:
            item_split = item.split(comparator)
            item_split.insert(1, comparator)
            return item_split
    return []


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
    query_dict["count"] = query_set.count()
    response_dict = OrderedDict()
    response_dict["count"] = 1
    response_dict["next"] = None
    response_dict["previous"] = None
    response_dict["results"] = [query_dict]
    response_string = json.dumps(response_dict)
    return HttpResponse(response_string)
