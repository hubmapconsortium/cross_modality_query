import hashlib
import pickle

from .models import Cell, Cluster, Dataset, Gene, Organ, QuerySet


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

    qs.query = pickle.loads(query_pickle)

    return qs
