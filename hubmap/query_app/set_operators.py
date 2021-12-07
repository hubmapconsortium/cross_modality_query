from .utils import (
    get_response_from_query_handle,
    make_pickle_and_hash,
    unpickle_query_set,
)


def query_set_intersection(self, request):
    if request.method == "POST":
        params = request.data.dict()
        pickle_hash = qs_intersect(params)
        set_type = params["set_type"]
        return get_response_from_query_handle(pickle_hash, set_type)


def query_set_union(self, request):
    if request.method == "POST":
        params = request.data.dict()
        pickle_hash = qs_union(params)
        set_type = params["set_type"]
        return get_response_from_query_handle(pickle_hash, set_type)


def query_set_difference(self, request):
    if request.method == "POST":
        params = request.data.dict()
        pickle_hash = qs_subtract(params)
        set_type = params["set_type"]
        return get_response_from_query_handle(pickle_hash, set_type)


def qs_intersect(params):
    pickle_hash_1 = params["key_one"]
    pickle_hash_2 = params["key_two"]
    set_type = params["set_type"]
    qs1 = unpickle_query_set(pickle_hash_1)[0]
    qs2 = unpickle_query_set(pickle_hash_2)[0]
    qs = qs1 & qs2
    pickle_hash = make_pickle_and_hash(qs, set_type)
    return pickle_hash


def qs_union(params):
    pickle_hash_1 = params["key_one"]
    pickle_hash_2 = params["key_two"]
    set_type = params["set_type"]
    qs1 = unpickle_query_set(pickle_hash_1)[0]
    qs2 = unpickle_query_set(pickle_hash_2)[0]
    qs = qs1 | qs2
    pickle_hash = make_pickle_and_hash(qs, set_type)
    return pickle_hash


def qs_subtract(params):
    pickle_hash_1 = params["key_one"]
    pickle_hash_2 = params["key_two"]
    set_type = params["set_type"]
    qs1 = unpickle_query_set(pickle_hash_1)[0]
    qs2 = unpickle_query_set(pickle_hash_2)[0]
    qs = qs1.difference(qs2)
    pickle_hash = make_pickle_and_hash(qs, set_type)
    return pickle_hash
