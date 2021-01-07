import hashlib
import pickle
from functools import reduce
from typing import Dict, List

from django.core.cache import cache
from django.db.models import Q

from .models import (
    Cell,
    CellAndValues,
    Cluster,
    ClusterAndValues,
    Dataset,
    Gene,
    GeneAndValues,
    Organ,
    OrganAndValues,
    Protein,
    PVal,
    QuerySet,
    AtacQuant,
    CodexQuant,
    RnaQuant,
)
from .serializers import (
    CellSerializer,
    CellAndValuesSerializer,
    DatasetSerializer,
    GeneSerializer,
    GeneAndValuesSerializer,
    OrganSerializer,
    OrganAndValuesSerializer,
    ClusterSerializer,
    ClusterAndValuesSerializer,
    ProteinSerializer,
    QuerySetSerializer,
    QuerySetCountSerializer,
)


def get_zero_cells(gene: str, modality: str):
    gene = gene.split('<')[0]
    if modality == 'rna':
        non_zero_pks = cache.get('rna' + gene)
    elif modality == 'atac':
        non_zero_pks = cache.get('atac' + gene)

    zero_cells = Cell.objects.exclude(pk__in=non_zero_pks)

    return zero_cells



def get_max_value_items(query_set, limit, values_dict):
    identifiers = []

    if query_set.count() == 0:
        return query_set.filter(pk__in=[])

    limit = min(limit, query_set.count())

    for i in range(limit):

        k = list(values_dict.keys())
        v = list(values_dict.values())

        identifiers.append(k[v.index(max(v))])
        values_dict.pop(k[v.index(max(v))])

    if isinstance(query_set.first(), Cell):
        q = Q(cell_id__in=identifiers)

    elif isinstance(query_set.first(), Gene):
        q = Q(gene_symbol__in=identifiers)

    elif isinstance(query_set.first(), Organ):
        q = Q(grouping_name__in=identifiers)

    elif isinstance(query_set.first(), Cluster):
        id_split = [identifier.split("-") for identifier in identifiers]
        qs = [Q(dataset__uuid=ids[0]) & Q(grouping_name=ids[1]) for ids in id_split]
        q = reduce(q_or, qs)


    return query_set.filter(q)


def order_query_set(query_set, limit, values_dict):

    vals_dict = {}
    for item in query_set:
        if isinstance(item, Cell):
            identifier = item.cell_id
        elif isinstance(item, Gene):
            identifier = item.gene_symbol
        elif isinstance(item, Organ):
            identifier = item.grouping_name
        elif isinstance(item, Cluster):
            identifier = item.dataset.uuid + "-" + item.grouping_name

        if identifier in values_dict.keys():
            vals_dict[identifier] = values_dict[identifier]
        else:
            vals_dict[identifier] = 0.0

    return get_max_value_items(query_set, limit, vals_dict)


def genes_from_pvals(pval_set):
    ids = pval_set.distinct("p_gene").values_list("p_gene", flat=True)
    return Gene.objects.filter(pk__in=list(ids))


def organs_from_pvals(pval_set):
    ids = pval_set.values_list("p_organ", flat=True).distinct()
    print(ids)
    return Organ.objects.filter(pk__in=list(ids))


def clusters_from_pvals(pval_set):
    ids = pval_set.values_list("p_cluster", flat=True).distinct()
    print(ids)
    return Cluster.objects.filter(pk__in=list(ids))


def cells_from_quants(quant_set, var):
    print("Cells from quants called")

    print("query_set.count")
    print(quant_set.count())

    cell_ids = quant_set.distinct("q_cell_id").values_list("q_cell_id", flat=True)

    print("len(cell_ids)")
    print(len(cell_ids))
    if len(cell_ids) > 0:
        print(cell_ids[0])

    cells = Cell.objects.filter(cell_id__in=cell_ids)

    print(cells.count())

    if '<' in var:
        if isinstance(quant_set.first(), RnaQuant):
            modality = 'rna'
        elif isinstance(quant_set.first(), AtacQuant):
            modality = 'atac'
        else:
            modality = 'protein'
        if modality in ['rna', 'atac']:
            zero_cells = get_zero_cells(var, modality)
            cells = zero_cells | cells

    return cells


def split_and_strip(string: str) -> List[str]:
    set_split = string.split(",")
    set_strip = [element.strip() for element in set_split]
    return set_strip


def process_query_parameters(query_params: Dict, input_set: List) -> Dict:
    query_params["input_type"] = query_params["input_type"].lower()

    if input_set is not None:
        query_params["input_set"] = input_set

    if isinstance(query_params["input_set"], str):
        query_params["input_set"] = split_and_strip(query_params["input_set"])
    query_params["input_set"] = process_input_set(
        query_params["input_set"], query_params["input_type"]
    )
    if 'input_set_key' in query_params.keys() and query_params['input_set_key'] != '':
        qs = unpickle_query_set(query_params["input_set_key"], query_params["input_type"])
        identifiers = {"cell":"cell_id", "gene":"gene_symbol", "organ":"grouping_name", "cluster":"grouping_name", "dataset":"uuid"}
        identifier = identifiers[query_params["input_type"]]
        query_params["input_set"].extend(qs.values_list(identifier, flat=True))

    if (
            "limit" not in query_params.keys()
            or not query_params["limit"].isnumeric()
            or int(query_params["limit"]) > 1000
    ):
        query_params["limit"] = 1000
    if (
            "p_value" not in query_params.keys()
            or query_params["p_value"] == ""
            or float(query_params["p_value"]) < 0.0
            or float(query_params["p_value"]) > 1.0
    ):
        query_params["p_value"] = 0.05
    else:
        query_params["p_value"] = float(query_params["p_value"])

    return query_params


def process_input_set(input_set: List, input_type: str):
    """If the input set is output of a previous query, finds the relevant values from the serialized data"""
    type_dict = {
        "gene": "gene_symbol",
        "cell": "cell_id",
        "organ": "grouping_name",
        "protein": "protein_id",
    }
    if type(input_set[0] == str):
        return input_set
    elif type(input_set[0] == dict):
        return [set_element[type_dict[input_type]] for set_element in input_set]
    else:
        return None


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


def q_and(q1: Q, q2: Q) -> Q:
    return q1 & q2


def q_or(q1: Q, q2: Q) -> Q:
    return q1 | q2


def combine_qs(qs: List[Q], logical_operator: str) -> Q:
    """List[Q] -> Q
    Combines a series of conditions into a single condition based on logical operator"""

    if len(qs) == 0:
        return Q(pk__in=[])
    if logical_operator == "or":
        return reduce(q_or, qs)
    elif logical_operator == "and":
        return reduce(q_and, qs)


def process_single_condition(split_condition: List[str], input_type: str) -> Q:
    """List[str], str -> Q
    Finds the keyword args for a quantitative query based on the results of
    calling split_at_comparator() on a string representation of that condition"""
    comparator = split_condition[1]

    assert comparator in [">", ">=", "<=", "<", "==", "!="]
    value = float(split_condition[2].strip())

    var_id = split_condition[0].strip()

    if input_type == "protein":
        protein_id = split_condition[0].strip()

        if comparator == ">":
            kwargs = {"protein_mean__" + protein_id + "__gt": value}
        elif comparator == ">=":
            kwargs = {"protein_mean__" + protein_id + "__gte": value}
        elif comparator == "<":
            kwargs = {"protein_mean__" + protein_id + "__lt": value}
        elif comparator == "<=":
            kwargs = {"protein_mean__" + protein_id + "__lte": value}
        elif comparator == "==":
            kwargs = {"protein_mean__" + protein_id + "__exact": value}
        elif comparator == "!=":
            kwargs = {"protein_mean__" + protein_id + "__exact": value}
            return ~Q(kwargs)

        return Q(**kwargs)

    if input_type == 'gene':
        q = Q(q_var_id__iexact=var_id)

        if comparator == '>':
            q = q & Q(value__gt=value)
        elif comparator == '>=':
            q = q & Q(value__gte=value)
        elif comparator == '<':
            q = q & (Q(value__lt=value))
        elif comparator == '<=':
            q = q & (Q(value__lte=value))
        elif comparator == '==':
            q = q & Q(value__exact=value)
        elif comparator == '!=':
            q = q & ~Q(value__exact=value)

    return q


def get_gene_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for gene objects based on the input set, input type, and logical operator
    Currently only services categorical queries where input type is tissue_type or dataset"""

    input_type = query_params["input_type"]
    input_set = query_params["input_set"]
    p_value = query_params["p_value"]
    genomic_modality = query_params["genomic_modality"]

    groupings_dict = {"organ": "p_organ__grouping_name__iexact", "cluster": "grouping_name__iexact"}

    if input_type in groupings_dict:

        # Assumes clusters are of the form uuid-clusternum
        if input_type == 'cluster':
            cluster_split = [item.split('-') for item in input_set]
            q_kwargs = [{groupings_dict[input_type]: element[1]} for element in cluster_split]
            qs1 = [Q(**kwargs) for kwargs in q_kwargs]
            q_kwargs = [{'dataset__uuid': element[0]} for element in cluster_split]
            qs2 = [Q(**kwargs) for kwargs in q_kwargs]
            qs = [qs1[i] & qs2[i] for i in range(len(qs1))]

            clusters = [Cluster.objects.filter(q).first() for q in qs if Cluster.objects.filter(q).first() is not None]
            q = Q(p_cluster_id__in=clusters)

        else:
            q_kwargs = [
                {groupings_dict[input_type]: element}
                for element in input_set
            ]
            qs = [Q(**kwargs) for kwargs in q_kwargs]

            q = combine_qs(qs, "or")

        q = q & Q(value__lte=p_value) & Q(modality__modality_name__icontains=genomic_modality)

        return q


def get_cell_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for cell objects based on the input set, input type, and logical operator
    Currently services quantitative queries where input is protein, atac_gene, or rna_gene
    and membership queries where input is tissue_type"""

    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    print("Get cell filter")
    print("Type input set")
    print(type(input_set))
    print("Input set")
    print(input_set)

    groupings_dict = {"organ": "grouping_name", "cluster": "grouping_name", "dataset":"uuid"}

    if input_type in ["protein", "gene"]:

        split_conditions = [[item, '>', '0'] if len(split_at_comparator(item)) == 0 else split_at_comparator(item) for
                            item in input_set]
        print(split_conditions)

        qs = [process_single_condition(condition, input_type) for condition in split_conditions]
        q = combine_qs(qs, "or")

        print(q)

        return q

    elif input_type in groupings_dict:

        # Query groupings and then union their cells fields
        cell_ids = []

        if input_type == "organ":
            for organ in Organ.objects.filter(grouping_name__in=input_set):
                cell_ids.extend([cell.cell_id for cell in organ.cells.all()])

        elif input_type == "cluster":
            for cluster in Cluster.objects.filter(grouping_name__in=input_set):
                cell_ids.extend([cell.cell_id for cell in cluster.cells.all()])

        elif input_type == 'dataset':
            print(Dataset.objects.filter(uuid__in=input_set).count())
            for dataset in Dataset.objects.filter(uuid__in=input_set):
                cell_ids.extend([cell.cell_id for cell in dataset.cells.all()])

        return Q(cell_id__in=cell_ids)



def get_organ_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for group objects based on the input set, input type, and logical operator
    Currently services membership queries where input type is cells
    and categorical queries where input type is genes"""

    input_type = query_params["input_type"]
    input_set = query_params["input_set"]
    logical_operator = query_params["logical_operator"]

    if input_type == "cell":

        cell_qs = Cell.objects.filter(cell_id__in=input_set)

        organ_pks = cell_qs.distinct('organ').values_list('organ', flat=True)

        q = Q(pk__in=organ_pks)

        return q

    elif input_type == "gene":
        # Query those genes and return their associated groupings
        p_value = query_params["p_value"]

        qs = [Q(p_gene__gene_symbol__iexact=item) for item in input_set]
        q = combine_qs(qs, "or")
        q = q & Q(value__lte=p_value)
        organ_pks = Organ.objects.all().values_list("pk", flat=True)
        q = q & Q(p_organ__in=organ_pks)

        return q


def get_cluster_filter(query_params: dict):
    input_type = query_params['input_type']
    input_set = query_params['input_set']

    if input_type == "gene":
        # Query those genes and return their associated groupings
        p_value = query_params["p_value"]

        qs = [Q(p_gene__gene_symbol__iexact=item) for item in input_set]
        q = combine_qs(qs, "or")
        q = q & Q(value__lte=p_value)
        cluster_pks = Cluster.objects.all().values_list("pk", flat=True)
        q = q & Q(p_cluster__in=cluster_pks)

        return q

    elif input_type == "cell":

        cell_qs = Cell.objects.filter(cell_id__in=input_set)

        cluster_pks = cell_qs.distinct('dataset').values_list('cluster', flat=True)

        q = Q(pk__in=cluster_pks)

        return q



def get_dataset_filter(query_params: dict):
    input_type = query_params['input_type']
    input_set = query_params['input_set']

    if input_type == 'cell':
        cell_qs = Cell.objects.filter(cell_id__in=input_set)

        dataset_pks = cell_qs.distinct('dataset').values_list('dataset', flat=True)

        q = Q(pk__in=dataset_pks)

        return q


def get_quant_queryset(query_params: Dict, filter):
    if query_params['input_type'] == 'protein':
        query_set = CodexQuant.objects.filter(filter)
    elif query_params['genomic_modality'] == 'rna':
        query_set = RnaQuant.objects.filter(filter)
    elif query_params['genomic_modality'] == 'rna':
        query_set = AtacQuant.objects.filter(filter)

    var_ids = [split_at_comparator(item)[0].strip() if len(split_at_comparator(item)) > 0 else item for item in
               query_params['input_set']]

    query_sets = [cells_from_quants(query_set.filter(q_var_id=var), var) for var in
                  var_ids]

    if len(query_sets) == 0:
        query_set = Cell.objects.filter(pk__in=[])
    else:
        if query_params['logical_operator'] == 'and':
            query_set = reduce(set_intersection, query_sets)
        elif query_params['logical_operator'] == 'or':
            query_set = reduce(set_union, query_sets)

    return query_set


def get_genes_list(query_params: Dict, input_set=None):
    if query_params["input_type"] is None:
        return Gene.objects.all()
    else:
        query_params = process_query_parameters(query_params, input_set)
        filter = get_gene_filter(query_params)
        print(filter)

        if query_params["input_type"] in ["organ", "cluster"]:
            query_set = PVal.objects.filter(filter)
            ids = query_set.values_list("pk", flat=True)
            query_set = PVal.objects.filter(pk__in=list([ids]))

            grouping = "p_" + query_params["input_type"]
            groups = query_set.values(grouping).distinct()
            query_set_kwargs = [{grouping:group[grouping]} for group in groups]

            query_sets = [
                genes_from_pvals(query_set.filter(**kwargs)) for kwargs in query_set_kwargs
            ]
            if len(query_sets) == 0:
                query_set = Gene.objects.filter(pk__in=[])
            else:
                query_set = reduce(set_intersection, query_sets)

        query_pickle_hash = make_pickle_and_hash(query_set, "gene")
        return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)


# Put fork here depending on whether or not we're returning expression values
def get_cells_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_cell_filter(query_params)

    if query_params['input_type'] in ['gene']:
        query_set = get_quant_queryset(query_params, filter)
    else:
        query_set = Cell.objects.filter(filter)

    query_pickle_hash = make_pickle_and_hash(query_set, "cell")
    return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)


# Put fork here depending on whether or not we're returning pvals
def get_organs_list(query_params: Dict, input_set=None):
    if query_params.get("input_type") is None:
        all_clusters = Cluster.objects.all()
        query_pickle_hash = make_pickle_and_hash(all_clusters, "cluster")
        return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)
    else:
        query_params = process_query_parameters(query_params, input_set)
        filter = get_organ_filter(query_params)
        print(filter)
        limit = int(query_params["limit"])

        if query_params["input_type"] == "gene":
            query_set = PVal.objects.filter(filter)
            print(query_set.count())
            genes = query_set.values("p_gene").distinct()
            query_sets = [
                organs_from_pvals(query_set.filter(p_gene=gene["p_gene"])) for gene in genes
            ]
            if len(query_sets) == 0:
                query_set = Organ.objects.filter(pk__in=[])
            else:
                query_set = reduce(set_intersection, query_sets)

        else:
            query_set = Organ.objects.filter(filter)[:limit]
            ids = query_set.values_list("pk", flat=True)
            query_set = Organ.objects.filter(pk__in=list(ids))

        query_pickle_hash = make_pickle_and_hash(query_set, "organ")
        return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)


def get_clusters_list(query_params: Dict, input_set=None):

    query_params = process_query_parameters(query_params, input_set)
    filter = get_cluster_filter(query_params)

    if query_params["input_type"] == "gene":
        query_set = PVal.objects.filter(filter).order_by("value")
        print(query_set.count())
        genes = query_set.values("p_gene").distinct()

        query_sets = [
            clusters_from_pvals(query_set.filter(p_gene=gene["p_gene"])) for gene in genes
        ]
        if len(query_sets) == 0:
            query_set = Cluster.objects.filter(pk__in=[])
        else:
            query_set = reduce(set_intersection, query_sets)

        query_pickle_hash = make_pickle_and_hash(query_set, "cluster")
        return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)

def get_datasets_list(query_params: Dict, input_set=None):

    query_params = process_query_parameters(query_params)
    filter = get_dataset_filter(query_params)

    if query_params["input_type"] == "cell":
        query_set = Dataset.objects.filter(filter)
        query_pickle_hash = make_pickle_and_hash(query_set, "cluster")
        return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)


def get_proteins_list(query_params: Dict):
    if query_params.get("input_type") is None:
        all_proteins = Protein.objects.all()
        query_pickle_hash = make_pickle_and_hash(all_proteins, "cluster")
        return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)


def gene_query(self, request):

    print(request.method)

    if request.method == "GET":
        all_genes = Gene.objects.all()
        pickle_hash = make_pickle_and_hash(all_genes, "gene")
        query_set = QuerySet.objects.filter(query_pickle_hash=pickle_hash)

    if request.method == "POST":
        query_params = request.data.dict()
        query_set = get_genes_list(query_params, input_set=request.POST.getlist("input_set"))

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }
    #    print(genes)
    #    print(GeneSerializer(genes, many=True, context=context))
    # Get serializers lists

    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response


def cell_query(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        print(query_params)
        query_set = get_cells_list(query_params, input_set=request.POST.getlist("input_set"))

    if request.method == "GET":
        all_genes = Cell.objects.all()
        pickle_hash = make_pickle_and_hash(all_genes, "cell")
        query_set = QuerySet.objects.filter(query_pickle_hash=pickle_hash)

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }
    #    print(cells)
    #    print(CellSerializer(cells, many=True, context=context))
    # Get serializers lists
    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response


def organ_query(self, request):

    if request.method == "POST":
        query_params = request.data.dict()
        print(query_params)
        query_set = get_organs_list(query_params, input_set=request.POST.getlist("input_set"))

    if request.method == "GET":
        all_genes = Organ.objects.all()
        pickle_hash = make_pickle_and_hash(all_genes, "organ")
        query_set = QuerySet.objects.filter(query_pickle_hash=pickle_hash)

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }
    #    print(groups)
    #    print(CellGroupingSerializer(groups, many=True, context=context))
    # Get serializers lists

    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response


def cluster_query(self, request):

    if request.method == "POST":
        query_params = request.data.dict()
        print(query_params)
        query_set = get_clusters_list(query_params, input_set=request.POST.getlist("input_set"))

    if request.method == "GET":
        all_genes = Cluster.objects.all()
        pickle_hash = make_pickle_and_hash(all_genes, "cluster")
        query_set = QuerySet.objects.filter(query_pickle_hash=pickle_hash)

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }
    #    print(groups)
    #    print(CellGroupingSerializer(groups, many=True, context=context))
    # Get serializers lists

    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response

def dataset_query(self, request):

    if request.method == "POST":
        query_params = request.data.dict()
        print(query_params)
        query_set = get_datasets_list(query_params, input_set=request.POST.getlist("input_set"))

    if request.method == "GET":
        all_genes = Dataset.objects.all()
        pickle_hash = make_pickle_and_hash(all_genes, "dataset")
        query_set = QuerySet.objects.filter(query_pickle_hash=pickle_hash)

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }
    #    print(groups)
    #    print(CellGroupingSerializer(groups, many=True, context=context))
    # Get serializers lists

    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response


def protein_query(self, request):
    if request.method == "GET":
        proteins = Protein.objects.all()
        self.queryset = proteins
        # Set context
        context = {
            "request": request,
        }
        #        print(proteins)
        #        print(ProteinSerializer(proteins, many=True, context=context))
        # Get serializers lists
        response = ProteinSerializer(proteins, many=True, context=context).data
        return response


def set_intersection(query_set_1, query_set_2):
    return query_set_1 & query_set_2


def set_union(query_set_1, query_set_2):
    return query_set_1 | query_set_2

def process_evaluation_args(query_params):
    if "sort_by" in query_params.keys() and query_params["sort_by"] != "":
        sort_by = query_params["sort_by"]  # Must be empty or an element of include values
    else:
        sort_by = None

    if "values_included" in query_params.keys():
        if isinstance(query_params["values_included"], str):
            include_values = query_params["values_included"].split(",")
            include_values = [value.strip() for value in include_values]
    else:
        include_values = []

    if "limit" not in query_params.keys() or not query_params["limit"].isdigit() or int(query_params["limit"]) > 1000:
        query_params["limit"] = 1000
    else:
        query_params["limit"] = int(query_params["limit"])

    query_params["sort_by"] = sort_by
    query_params["include_values"] = include_values

    return query_params

def make_cell_and_values(query_params):

    query_params = process_evaluation_args(query_params)

    pickle_hash = query_params["key"]
    include_values = query_params["include_values"]  # A list of genes, proteins, organs, etc. for which to include values, optional

    limit = query_params["limit"]  # The maximum number of results to return
    values_type = query_params["values_type"]
    qs = QuerySet.objects.get(query_pickle_hash__icontains=pickle_hash)
    set_type = qs.set_type
    query_set = unpickle_query_set(pickle_hash, set_type)
    sort_by = query_params["sort_by"]


    CellAndValues.objects.all().delete()

    print("Making cells and values")


    if query_params["sort_by"] is None:
        query_set = query_set[:limit]

    else:
        sort_by_values = get_values(query_set, "cell", [sort_by], values_type)
        sort_by_dict = {}
        for key in sort_by_values:
            if "sort_by" in sort_by_values[key].keys():
                sort_by_dict[key] = sort_by_values[key][sort_by]
            else:
                sort_by_dict[key] = 0.0

        query_set = order_query_set(query_set, limit, sort_by_dict)

    values_dict = {} if len(include_values) == 0 else get_values(query_set, "cell", include_values, values_type)

    for cell in query_set:

        values = {} if cell.cell_id not in values_dict else values_dict[cell.cell_id]

        kwargs = {

            "cell_id": cell.cell_id,

            "dataset": cell.dataset,

            "modality": cell.modality,

            "organ": cell.organ,

            "values": values,

        }

        cav = CellAndValues(**kwargs)

        cav.save()

        kwargs = {'cell_id': cell.cell_id, 'dataset': cell.dataset, 'modality': cell.modality,
                  'organ': cell.organ, 'values': values}

        cav = CellAndValues(**kwargs)
        cav.save()

    print('Values gotten')

    qs = CellAndValues.objects.all()

    return qs


def make_gene_and_values(query_params):
    query_params = process_evaluation_args(query_params)

    pickle_hash = query_params["key"]
    include_values = query_params[
        "include_values"]  # A list of genes, proteins, organs, etc. for which to include values, optional
    sort_by = query_params["sort_by"]  # Must be empty or an element of include values
    limit = query_params["limit"]  # The maximum number of results to return
    values_type = query_params["values_type"]
    qs = QuerySet.objects.get(query_pickle_hash__icontains=pickle_hash)
    set_type = qs.set_type
    query_set = unpickle_query_set(pickle_hash, set_type)

    GeneAndValues.objects.all().delete()
    # Filter on timestamp

    if sort_by is None:
        query_set = query_set[:limit]

    else:
        sort_by_values = get_values(query_set, "gene", [sort_by], values_type)
        sort_by_dict = {}
        for key in sort_by_values:
            if sort_by in sort_by_values[key].keys():
                sort_by_dict[key] = sort_by_values[key][sort_by]
            else:
                sort_by_dict[key] = 0.0

        query_set = order_query_set(query_set, limit, sort_by_dict)


    values_dict = {} if len(include_values) == 0 else get_values(query_set, "gene", include_values, values_type)

    for gene in query_set:

        values = {} if gene.gene_symbol not in values_dict else values_dict[gene.gene_symbol]
        kwargs = {'gene_symbol': gene.gene_symbol, 'values': values}

        gav = GeneAndValues(**kwargs)
        gav.save()

    # Filter on query hash
    return GeneAndValues.objects.all()


def make_organ_and_values(query_params):
    OrganAndValues.objects.all().delete()

    query_params = process_evaluation_args(query_params)

    pickle_hash = query_params["key"]
    include_values = query_params[
        "include_values"]  # A list of genes, proteins, organs, etc. for which to include values, optional
    sort_by = query_params["sort_by"]  # Must be empty or an element of include values
    limit = query_params["limit"]  # The maximum number of results to return
    values_type = query_params["values_type"]
    qs = QuerySet.objects.get(query_pickle_hash__icontains=pickle_hash)
    set_type = qs.set_type
    query_set = unpickle_query_set(pickle_hash, set_type)

    if sort_by is None:
        query_set = query_set[:limit]

    else:
        sort_by_values = get_values(query_set, "organ", [sort_by], values_type)
        sort_by_dict = {}
        for key in sort_by_values:
            if sort_by in sort_by_values[key].keys():
                sort_by_dict[key] = sort_by_values[key][sort_by]
            else:
                sort_by_dict[key] = 0.0

        query_set = order_query_set(query_set, limit, sort_by_dict)

    print('Executing')
    print(include_values)
    values_dict = {} if len(include_values) == 0 else get_values(query_set, "organ", include_values, values_type)
    for organ in query_set:
        values = {} if organ.grouping_name not in values_dict else values_dict[organ.grouping_name]

        kwargs = {"grouping_name": organ.grouping_name, "values": values}
        oav = OrganAndValues(**kwargs)
        oav.save()

    # Filter on query hash
    return OrganAndValues.objects.all()


def make_cluster_and_values(query_params):
    query_params = process_evaluation_args(query_params)

    pickle_hash = query_params["key"]
    include_values = query_params[
        "include_values"]  # A list of genes, proteins, organs, etc. for which to include values, optional
    sort_by = query_params["sort_by"]  # Must be empty or an element of include values
    values_type = query_params["values_type"]
    limit = query_params["limit"]  # The maximum number of results to return
    qs = QuerySet.objects.get(query_pickle_hash__icontains=pickle_hash)
    set_type = qs.set_type
    query_set = unpickle_query_set(pickle_hash, set_type)

    ClusterAndValues.objects.all().delete()

    if sort_by is None:
        query_set = query_set[:limit]

    else:
        sort_by_values = get_values(query_set, "cluster", [sort_by], values_type)
        sort_by_dict = {}
        for key in sort_by_values:
            if sort_by in sort_by_values[key].keys():
                sort_by_dict[key] = sort_by_values[key][sort_by]
            else:
                sort_by_dict[key] = 0.0

        query_set = order_query_set(query_set, limit, sort_by_dict)

    values_dict = {} if len(include_values) == 0 else get_values(query_set, "cluster", include_values, values_type)
    for cluster in query_set[:limit]:
        values = {} if cluster.grouping_name not in values_dict else values_dict[cluster.grouping_name]

        kwargs = {"grouping_name": cluster.grouping_name, "dataset":cluster.dataset, "values": values}
        clav = ClusterAndValues(**kwargs)
        clav.save()

    # Filter on query hash
    return ClusterAndValues.objects.all()


def make_pickle_and_hash(qs, set_type):
    qry = qs.query
    query_pickle = pickle.dumps(qry)
    print("Pickling done")
    query_pickle_hash = str(hashlib.sha256(query_pickle).hexdigest())
    if QuerySet.objects.filter(query_pickle_hash=query_pickle_hash).first() is None:
        query_set = QuerySet(query_pickle=query_pickle, query_pickle_hash=query_pickle_hash, set_type=set_type)
        query_set.save()
    return query_pickle_hash


def unpickle_query_set(query_pickle_hash, set_type):
    query_pickle = QuerySet.objects.filter(query_pickle_hash__icontains=query_pickle_hash).reverse().first().query_pickle
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

def get_qs_count(query_params):
    pickle_hash = query_params["key"]
    set_type = query_params["set_type"]

    qs = unpickle_query_set(pickle_hash, set_type)
    query_set = QuerySet.objects.get(query_pickle_hash=pickle_hash)
    query_set.count = qs.count()
    query_set.save()

    qs_count = QuerySet.objects.filter(query_pickle_hash=pickle_hash)
    return qs_count

def query_set_count(self, request):
    if request.method == "POST":
        query_params = request.data.dict()

    qs_count = get_qs_count(query_params)

    self.queryset = qs_count
    # Set context
    context = {
        "request": request,
    }
    #    print(groups)
    #    print(CellGroupingSerializer(groups, many=True, context=context))
    # Get serializers lists

    response = QuerySetCountSerializer(qs_count, many=True, context=context).data

    return response


def get_values(query_set, set_type, values, values_type):
    print("Values param")
    print(values)

    values_dict = {}

    if set_type == "cell":
        # values must be genes
        if values_type == 'gene':
            pks = query_set.values_list('pk', flat=True)
            query_set = Cell.objects.filter(pk__in=pks)
            atac_cells = query_set.filter(modality__modality_name='atac').values_list('cell_id', flat=True)
            rna_cells = query_set.filter(modality__modality_name='rna').values_list('cell_id', flat=True)
            print("rna_cells")
            print((len(rna_cells)))
            atac_quants = AtacQuant.objects.filter(q_cell_id__in=atac_cells).filter(q_var_id__in=values)
            rna_quants = RnaQuant.objects.filter(q_cell_id__in=rna_cells).filter(q_var_id__in=values)
            print("rna quants")
            print(len(rna_quants))
            for cell in atac_cells:
                cell_values = atac_quants.filter(q_cell_id=cell).values_list('q_var_id', 'value')
                print(len(cell_values))
                values_dict[cell] = {cv[0]: cv[1] for cv in cell_values}
            for cell in rna_cells:
                cell_values = rna_quants.filter(q_cell_id=cell).values_list('q_var_id', 'value')
                values_dict[cell] = {cv[0]: cv[1] for cv in cell_values}

        elif values_type == 'protein':
            for cell in query_set:
                values_dict[cell.cell_id] = {protein: cell.protein_mean[protein] for protein in values}

        return values_dict

    elif set_type == 'gene':
        # values must be organs or clusters
        gene_ids = query_set.values_list('gene_symbol', flat=True)

        if values_type == 'organ':
            organs = Organ.objects.filter(grouping_name__in=values).values_list('pk', flat=True)
            pvals = PVal.objects.filter(p_organ__in=organs).filter(p_gene__gene_symbol__in=gene_ids)
            for gene in query_set:
                gene_pvals = pvals.filter(p_gene__gene_symbol=gene.gene_symbol).values_list('p_organ__grouping_name', 'value')
                values_dict[gene.gene_symbol] = {gp[0]: gp[1] for gp in gene_pvals}

        elif values_type == 'cluster':
            cluster_split = [(value.split('-')[0], value.split('-')[1]) for value in values]
            qs = [Q(dataset__uuid=cs[0]) & Q(grouping_name=cs[1]) for cs in cluster_split]
            q = reduce(q_or, qs)
            clusters = Cluster.objects.filter(q).values_list('pk', flat=True)
            pvals = PVal.objects.filter(p_cluster__in=clusters).filter(p_gene__gene_symbol__in=gene_ids)
            for gene in query_set:
                gene_pvals = pvals.filter(p_gene__gene_symbol=gene.gene_symbol).values_list('p_cluster__grouping_name', 'value')
                values_dict[gene.gene_symbol] = {gp[0]: gp[1] for gp in gene_pvals}

        return values_dict


    elif set_type == 'organ':
        # values must be genes
        print("Organs")
        print(query_set.values_list('pk', flat=True))
        print("Genes")
        print(values)
        pvals = PVal.objects.filter(p_organ__in=query_set.values_list('pk', flat=True)).filter(p_gene__gene_symbol__in=values)
        for organ in query_set:
            organ_pvals = pvals.filter(p_organ=organ).values_list('p_gene__gene_symbol', 'value')
            values_dict[organ.grouping_name] = {op[0]: op[1] for op in organ_pvals}
        return values_dict

    elif set_type == 'cluster':
        # values must be genes
        pvals = PVal.objects.filter(p_cluster__in=query_set.values_list('pk', flat=True)).filter(p_gene__gene_symbol__in=values)
        for cluster in query_set:
            cluster_pvals = pvals.filter(p_cluster=cluster).values_list('p_gene__gene_symbol', 'value')
            values_dict[cluster.grouping_name] = {cp[0]: cp[1] for cp in cluster_pvals}
        return values_dict


def cell_evaluation_detail(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        evaluated_set = make_cell_and_values(query_params)
        self.queryset = evaluated_set
        # Set context
        context = {
            "request": request,
        }
        #    print(groups)
        #    print(CellGroupingSerializer(groups, many=True, context=context))
        # Get serializers lists

        response = CellAndValuesSerializer(evaluated_set, many=True, context=context).data

        return response

def gene_evaluation_detail(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        evaluated_set = make_gene_and_values(query_params)
        self.queryset = evaluated_set
        # Set context
        context = {
            "request": request,
        }
        #    print(groups)
        #    print(CellGroupingSerializer(groups, many=True, context=context))
        # Get serializers lists

        response = GeneAndValuesSerializer(evaluated_set, many=True, context=context).data

        return response


def organ_evaluation_detail(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        evaluated_set = make_organ_and_values(query_params)
        self.queryset = evaluated_set
        # Set context
        context = {
            "request": request,
        }
        #    print(groups)
        #    print(CellGroupingSerializer(groups, many=True, context=context))
        # Get serializers lists

        response = OrganAndValuesSerializer(evaluated_set, many=True, context=context).data

        return response

def cluster_evaluation_detail(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        evaluated_set = make_cluster_and_values(query_params)
        self.queryset = evaluated_set
        # Set context
        context = {
            "request": request,
        }
        #    print(groups)
        #    print(CellGroupingSerializer(groups, many=True, context=context))
        # Get serializers lists

        response = ClusterAndValuesSerializer(evaluated_set, many=True, context=context).data

        return response

def evaluate_qs(query_params):
    pickle_hash = query_params["key"]
    set_type = query_params["set_type"]
    evaluated_set = unpickle_query_set(query_pickle_hash=pickle_hash, set_type=set_type)
    limit = int(query_params["limit"])
    evaluated_set = evaluated_set[:limit]
    return evaluated_set

def evaluation_list(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        set_type = query_params["set_type"]
        eval_qs = evaluate_qs(query_params)
        self.queryset = eval_qs
        # Set context
        context = {
            "request": request,
        }
        #    print(groups)
        #    print(CellGroupingSerializer(groups, many=True, context=context))
        # Get serializers lists

        if set_type == "cell":
            response = CellSerializer(eval_qs, many=True, context=context).data
        if set_type == "gene":
            response = GeneSerializer(eval_qs, many=True, context=context).data
        if set_type == "cluster":
            response = ClusterSerializer(eval_qs, many=True, context=context).data
        if set_type == "organ":
            response = OrganSerializer(eval_qs, many=True, context=context).data
        if set_type == "dataset":
            response = DatasetSerializer(eval_qs, many=True, context=context).data

        return response