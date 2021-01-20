from .serializers import QuerySetSerializer
from .models import Cell, Cluster, Dataset, Gene, Organ, QuerySet
from .utils import unpickle_query_set, make_pickle_and_hash


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


def query_set_negation(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        qs = qs_negate(query_params)

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
    qs = QuerySet.objects.filter(query_pickle_hash=pickle_hash)
    return qs


def qs_union(params):
    pickle_hash_1 = params["key_one"]
    pickle_hash_2 = params["key_two"]
    set_type = params["set_type"]
    qs1 = unpickle_query_set(pickle_hash_1, set_type)
    qs2 = unpickle_query_set(pickle_hash_2, set_type)
    qs = qs1 | qs2
    pickle_hash = make_pickle_and_hash(qs, set_type)
    qs = QuerySet.objects.filter(query_pickle_hash=pickle_hash)
    return qs


def qs_negate(params):
    pickle_hash = params["key"]
    set_type = QuerySet.objects.filter(query_pickle_hash__icontains=pickle_hash).reverse().first().set_type

    if set_type == "cell":
        qs1 = Cell.objects.all()

    elif set_type == "gene":
        qs1 = Gene.objects.all()

    elif set_type == "cluster":
        qs1 = Cluster.objects.all()

    elif set_type == "organ":
        qs1 = Organ.objects.all()

    qs2 = unpickle_query_set(pickle_hash, set_type)
    qs = qs1.difference(qs2)
    pickle_hash = make_pickle_and_hash(qs, set_type)
    qs = QuerySet.objects.filter(query_pickle_hash=pickle_hash)
    return qs


def qs_subtract(params):
    pickle_hash_1 = params["key_one"]
    pickle_hash_2 = params["key_two"]
    set_type = params["set_type"]
    qs1 = unpickle_query_set(pickle_hash_1, set_type)
    qs2 = unpickle_query_set(pickle_hash_2, set_type)
    qs = qs1.difference(qs2)
    pickle_hash = make_pickle_and_hash(qs, set_type)
    qs = QuerySet.objects.filter(query_pickle_hash=pickle_hash)
    return qs
