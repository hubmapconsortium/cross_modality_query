import hashlib
import pickle
from functools import reduce
from operator import or_

from django.db.models import Q

from .models import Cell, Cluster, Dataset, Gene, Organ, QuerySet


def set_intersection(query_set_1, query_set_2):
    return query_set_1 & query_set_2


def set_union(query_set_1, query_set_2):
    return query_set_1 | query_set_2


def make_pickle_and_hash(qs, set_type):
    qry = qs.query
    query_pickle = pickle.dumps(qry)
    print("Pickling done")
    query_pickle_hash = str(hashlib.sha256(query_pickle).hexdigest())
    if QuerySet.objects.filter(query_pickle_hash=query_pickle_hash).first() is None:
        query_set = QuerySet(
            query_pickle=query_pickle, query_pickle_hash=query_pickle_hash, set_type=set_type
        )
        query_set.save()
    return query_pickle_hash


def unpickle_query_set(query_pickle_hash, set_type):
    query_pickle = (
        QuerySet.objects.filter(query_pickle_hash__icontains=query_pickle_hash)
        .reverse()
        .first()
        .query_pickle
    )
    #    query_pickle = QuerySet.objects.get(query_pickle_hash=query_pickle_hash).query_pickle

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

    qs.query = pickle.loads(query_pickle)

    return qs
