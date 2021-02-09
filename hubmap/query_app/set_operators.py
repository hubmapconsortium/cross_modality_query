from .models import QuerySet
from .serializers import QuerySetSerializer
from .utils import make_pickle_and_hash, unpickle_query_set


def query_set_intersection(self, request):
    if request.method == "POST":
        params = request.data.dict()
        qs = qs_intersect(params)

    self.queryset = qs
    # Set context
    context = {
        "request": request,
    }
    #    print(groups)
    #    print(CellGroupingSerializer(groups, many=True, context=context))
    # Get serializers lists

    response = QuerySetSerializer(qs, many=True, context=context).data

    return response


def query_set_union(self, request):
    if request.method == "POST":
        params = request.data.dict()
        qs = qs_union(params)

    self.queryset = qs
    # Set context
    context = {
        "request": request,
    }
    #    print(groups)
    #    print(CellGroupingSerializer(groups, many=True, context=context))
    # Get serializers lists

    response = QuerySetSerializer(qs, many=True, context=context).data

    return response


def query_set_difference(self, request):
    if request.method == "POST":
        params = request.data.dict()
        qs = qs_subtract(params)

    self.queryset = qs
    # Set context
    context = {
        "request": request,
    }
    #    print(groups)
    #    print(CellGroupingSerializer(groups, many=True, context=context))
    # Get serializers lists

    response = QuerySetSerializer(qs, many=True, context=context).data

    return response


def qs_intersect(params):
    pickle_hash_1 = params["key_one"]
    pickle_hash_2 = params["key_two"]
    set_type = params["set_type"]
    qs1 = unpickle_query_set(pickle_hash_1, set_type)
    qs2 = unpickle_query_set(pickle_hash_2, set_type)
    qs = qs1 & qs2
    pickle_hash = make_pickle_and_hash(qs, set_type)
    qs = QuerySet.objects.filter(query_handle=pickle_hash)
    return qs


def qs_union(params):
    pickle_hash_1 = params["key_one"]
    pickle_hash_2 = params["key_two"]
    set_type = params["set_type"]
    qs1 = unpickle_query_set(pickle_hash_1, set_type)
    qs2 = unpickle_query_set(pickle_hash_2, set_type)
    qs = qs1 | qs2
    pickle_hash = make_pickle_and_hash(qs, set_type)
    qs = QuerySet.objects.filter(query_handle=pickle_hash)
    return qs


def qs_subtract(params):
    pickle_hash_1 = params["key_one"]
    pickle_hash_2 = params["key_two"]
    set_type = params["set_type"]
    qs1 = unpickle_query_set(pickle_hash_1, set_type)
    qs2 = unpickle_query_set(pickle_hash_2, set_type)
    qs = qs1.difference(qs2)
    pickle_hash = make_pickle_and_hash(qs, set_type)
    qs = QuerySet.objects.filter(query_handle=pickle_hash)
    return qs
