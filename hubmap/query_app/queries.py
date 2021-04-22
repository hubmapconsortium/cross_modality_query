from functools import reduce
from operator import and_, or_
from typing import Dict

from django.core.cache import cache

from .filters import (
    get_cell_filter,
    get_cluster_filter,
    get_dataset_filter,
    get_gene_filter,
    get_organ_filter,
    get_protein_filter,
)
from .models import (
    AtacQuant,
    Cell,
    Cluster,
    CodexQuant,
    Dataset,
    Gene,
    Organ,
    Protein,
    PVal,
    QuerySet,
    RnaQuant,
)
from .serializers import ProteinSerializer, QuerySetSerializer
from .utils import make_pickle_and_hash
from .validation import (
    process_query_parameters,
    split_at_comparator,
    validate_cell_query_params,
    validate_cluster_query_params,
    validate_dataset_query_params,
    validate_gene_query_params,
    validate_organ_query_params,
    validate_protein_query_params,
)


def get_zero_cells(gene: str, modality: str):
    gene = gene.split("<")[0]
    if modality == "rna":
        non_zero_pks = cache.get("rna" + gene)
    elif modality == "atac":
        non_zero_pks = cache.get("atac" + gene)

    zero_cells = Cell.objects.exclude(pk__in=non_zero_pks)

    return zero_cells


def genes_from_pvals(pval_set):
    ids = pval_set.distinct("p_gene").values_list("p_gene", flat=True)
    return Gene.objects.filter(pk__in=list(ids))


def organs_from_pvals(pval_set):
    ids = pval_set.values_list("p_organ", flat=True).distinct()
    return Organ.objects.filter(pk__in=list(ids))


def clusters_from_pvals(pval_set):
    ids = pval_set.values_list("p_cluster", flat=True).distinct()
    return Cluster.objects.filter(pk__in=list(ids))


def cells_from_quants(quant_set, var):

    cell_ids = quant_set.values_list("q_cell_id", flat=True)
    print("Cell ids gotten")

    if len(cell_ids) > 0:
        print(cell_ids[0])

    cells = Cell.objects.filter(cell_id__in=cell_ids)
    print("Cell set found")

    if "<" in var:
        if isinstance(quant_set.first(), RnaQuant):
            modality = "rna"
        elif isinstance(quant_set.first(), AtacQuant):
            modality = "atac"
        else:
            modality = "protein"
        if modality in ["rna", "atac"]:
            zero_cells = get_zero_cells(var, modality)
            cells = zero_cells | cells

    return cells


def get_quant_queryset(query_params: Dict, filter):
    if query_params["input_type"] == "protein":
        query_set = CodexQuant.objects.filter(filter)
    elif query_params["genomic_modality"] == "rna":
        query_set = RnaQuant.objects.filter(filter)
    elif query_params["genomic_modality"] == "atac":
        query_set = AtacQuant.objects.filter(filter)

    var_ids = [
        split_at_comparator(item)[0].strip() if len(split_at_comparator(item)) > 0 else item
        for item in query_params["input_set"]
    ]

    query_sets = [cells_from_quants(query_set.filter(q_var_id=var), var) for var in var_ids]

    print("Query sets gotten")

    if len(query_sets) == 0:
        query_set = Cell.objects.filter(pk__in=[])
    elif len(query_sets) == 1:
        query_set = query_sets[0]
    elif len(query_sets) > 1:
        if query_params["logical_operator"] == "and":
            query_set = reduce(and_, query_sets)
        elif query_params["logical_operator"] == "or":
            query_set = reduce(or_, query_sets)

    return query_set


def get_genes_list(query_params: Dict, input_set=None):
    if query_params["input_type"] is None:
        return Gene.objects.all()
    else:
        query_params = process_query_parameters(query_params, input_set)
        filter = get_gene_filter(query_params)

        if query_params["input_type"] in ["organ", "cluster"]:
            query_set = PVal.objects.filter(filter)
            ids = query_set.values_list("pk", flat=True)
            query_set = PVal.objects.filter(pk__in=list([ids]))

            grouping = "p_" + query_params["input_type"]
            groups = query_set.values(grouping).distinct()
            query_set_kwargs = [{grouping: group[grouping]} for group in groups]

            query_sets = [
                genes_from_pvals(query_set.filter(**kwargs)) for kwargs in query_set_kwargs
            ]
            if len(query_sets) == 0:
                query_set = Gene.objects.filter(pk__in=[])
            elif len(query_sets) == 1:
                query_set = query_sets[0]
            elif query_params["logical_operator"] == "and":
                query_set = reduce(and_, query_sets)
            elif query_params["logical_operator"] == "or":
                query_set = reduce(or_, query_sets)

        elif query_params["input_type"] == "gene":
            query_set = Gene.objects.filter(filter)

        query_set = query_set.distinct("gene_symbol")

        query_handle = make_pickle_and_hash(query_set, "gene")
        return QuerySet.objects.filter(query_handle=query_handle)


# Put fork here depending on whether or not we're returning expression values
def get_cells_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_cell_filter(query_params)
    print("Filter gotten")

    if query_params["input_type"] in ["gene", "protein"]:
        query_set = get_quant_queryset(query_params, filter)
    else:
        query_set = Cell.objects.filter(filter)

    query_set = query_set.distinct("cell_id")
    print("Query set found")

    query_handle = make_pickle_and_hash(query_set, "cell")
    return QuerySet.objects.filter(query_handle=query_handle)


def get_organs_list(query_params: Dict, input_set=None):
    if query_params.get("input_type") is None:
        all_clusters = Cluster.objects.all().distinct("grouping_name")
        query_handle = make_pickle_and_hash(all_clusters, "cluster")
        return QuerySet.objects.filter(query_handle=query_handle)
    else:
        query_params = process_query_parameters(query_params, input_set)
        filter = get_organ_filter(query_params)

        if query_params["input_type"] == "gene":
            query_set = PVal.objects.filter(filter)
            genes = query_set.values("p_gene").distinct()
            query_sets = [
                organs_from_pvals(query_set.filter(p_gene=gene["p_gene"])) for gene in genes
            ]
            if len(query_sets) == 0:
                query_set = Organ.objects.filter(pk__in=[])
            elif len(query_sets) == 1:
                query_set = query_sets[0]
            elif query_params["logical_operator"] == "and":
                query_set = reduce(and_, query_sets)
            elif query_params["logical_operator"] == "or":
                query_set = reduce(or_, query_sets)

        else:
            query_set = Organ.objects.filter(filter)
            ids = query_set.values_list("pk", flat=True)
            query_set = Organ.objects.filter(pk__in=list(ids))

        query_set = query_set.distinct("grouping_name")

        query_handle = make_pickle_and_hash(query_set, "organ")
        return QuerySet.objects.filter(query_handle=query_handle)


def get_clusters_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_cluster_filter(query_params)

    if query_params["input_type"] == "gene":
        query_set = PVal.objects.filter(filter).order_by("value")
        genes = query_set.values("p_gene").distinct()

        query_sets = [
            clusters_from_pvals(query_set.filter(p_gene=gene["p_gene"])) for gene in genes
        ]
        if len(query_sets) == 0:
            query_set = Cluster.objects.filter(pk__in=[])
        elif len(query_sets) == 1:
            query_set = query_sets[0]
        elif query_params["logical_operator"] == "and":
            query_set = reduce(and_, query_sets)
        elif query_params["logical_operator"] == "or":
            query_set = reduce(or_, query_sets)

    elif query_params["input_type"] in ["cluster", "dataset"]:
        query_set = Cluster.objects.filter(filter)

    query_set = query_set.distinct("grouping_name")

    query_handle = make_pickle_and_hash(query_set, "cluster")
    return QuerySet.objects.filter(query_handle=query_handle)


def get_datasets_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_dataset_filter(query_params)

    if query_params["input_type"] in ["cell", "cluster", "dataset", "gene", "protein"]:
        query_set = Dataset.objects.filter(filter).distinct("uuid")
        query_handle = make_pickle_and_hash(query_set, "dataset")
        return QuerySet.objects.filter(query_handle=query_handle)


def get_proteins_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_protein_filter(query_params)
    proteins = Protein.objects.filter(filter).distinct("protein_id")
    query_handle = make_pickle_and_hash(proteins, "protein")
    return QuerySet.objects.filter(query_handle=query_handle)


def gene_query(self, request):
    if request.data == {}:
        all_genes = Gene.objects.all().distinct("gene_symbol")
        pickle_hash = make_pickle_and_hash(all_genes, "gene")
        query_set = QuerySet.objects.filter(query_handle=pickle_hash)

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_gene_query_params(query_params)
        query_set = get_genes_list(query_params, input_set=request.POST.getlist("input_set"))

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }

    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response


def cell_query(self, request):
    if request.data == {}:
        all_cells = Cell.objects.all().distinct("cell_id")
        pickle_hash = make_pickle_and_hash(all_cells, "cell")
        query_set = QuerySet.objects.filter(query_handle=pickle_hash)

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_cell_query_params(query_params)
        print("Parameters validated")
        query_set = get_cells_list(query_params, input_set=request.POST.getlist("input_set"))

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }

    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response


def organ_query(self, request):
    if request.data == {}:
        all_organs = Organ.objects.all().distinct("grouping_name")
        pickle_hash = make_pickle_and_hash(all_organs, "organ")
        query_set = QuerySet.objects.filter(query_handle=pickle_hash)

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_organ_query_params(query_params)
        query_set = get_organs_list(query_params, input_set=request.POST.getlist("input_set"))

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

    if request.data == {}:
        all_clusters = Cluster.objects.all().distinct("grouping_name")
        pickle_hash = make_pickle_and_hash(all_clusters, "cluster")
        query_set = QuerySet.objects.filter(query_handle=pickle_hash)

    else:
        query_params = request.data.dict()
        print(query_params.keys())
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_cluster_query_params(query_params)
        query_set = get_clusters_list(query_params, input_set=request.POST.getlist("input_set"))

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }

    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response


def dataset_query(self, request):
    if request.data == {}:
        all_datasets = Dataset.objects.all().distinct("uuid")
        pickle_hash = make_pickle_and_hash(all_datasets, "dataset")
        query_set = QuerySet.objects.filter(query_handle=pickle_hash)

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_dataset_query_params(query_params)
        query_set = get_datasets_list(query_params, input_set=request.POST.getlist("input_set"))

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }

    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response


def protein_query(self, request):
    if request.data == {}:
        all_proteins = Protein.objects.all().distinct("protein_id")
        pickle_hash = make_pickle_and_hash(all_proteins, "protein")
        query_set = QuerySet.objects.filter(query_handle=pickle_hash)

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_protein_query_params(query_params)
        query_set = get_proteins_list(query_params, input_set=request.POST.getlist("input_set"))

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }
    response = QuerySetSerializer(query_set, many=True, context=context).data
    return response
