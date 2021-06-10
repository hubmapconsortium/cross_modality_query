import hashlib
import json
import pickle
from typing import List

from django.db import connections
from django.db.utils import OperationalError

from .models import Cell, Cluster, Dataset, Gene, Organ, Protein, QuerySet


def set_intersection(query_set_1, query_set_2):
    return query_set_1 & query_set_2


def set_union(query_set_1, query_set_2):
    return query_set_1 | query_set_2


def make_pickle_and_hash(qs, set_type):
    qry = qs.query
    query_pickle = pickle.dumps(qry)
    query_handle = str(hashlib.sha256(query_pickle).hexdigest())
    if QuerySet.objects.filter(query_handle=query_handle).first() is None:
        query_set = QuerySet(
            query_pickle=query_pickle, query_handle=query_handle, set_type=set_type
        )
        query_set.save()
    return query_handle


def unpickle_query_set(query_handle, set_type):

    print(query_handle)

    query_object = QuerySet.objects.filter(query_handle=query_handle).first()
    if query_object is None:
        raise ValueError(f"Query handle {query_handle} is not valid")
    query_pickle = query_object.query_pickle

    #    query_pickle = QuerySet.objects.get(query_handle=query_handle).query_pickle

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

    return qs


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


def infer_values_type(values: List) -> str:

    print(values)

    values = [
        split_at_comparator(item)[0].strip()
        if len(split_at_comparator(item)) > 0
        else item.strip()
        for item in values
    ]

    print(values)

    values_up = [value.upper() for value in values]
    values = values + values_up

    print(values)

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
