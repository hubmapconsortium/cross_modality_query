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

    cell_ids = quant_set.distinct("q_cell_id").values_list("q_cell_id", flat=True)

    if len(cell_ids) > 0:
        print(cell_ids[0])

    cells = Cell.objects.filter(cell_id__in=cell_ids)

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

    if len(query_sets) == 0:
        query_set = Cell.objects.filter(pk__in=[])
    else:
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
            else:
                query_set = reduce(or_, query_sets)

        elif query_params["input_type"] == "gene":
            query_set = Gene.objects.filter(filter)

        query_pickle_hash = make_pickle_and_hash(query_set, "gene")
        return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)


# Put fork here depending on whether or not we're returning expression values
def get_cells_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_cell_filter(query_params)

    if query_params["input_type"] in ["gene"]:
        query_set = get_quant_queryset(query_params, filter)
    else:
        query_set = Cell.objects.filter(filter)

    query_pickle_hash = make_pickle_and_hash(query_set, "cell")
    return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)


def get_organs_list(query_params: Dict, input_set=None):
    if query_params.get("input_type") is None:
        all_clusters = Cluster.objects.all()
        query_pickle_hash = make_pickle_and_hash(all_clusters, "cluster")
        return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)
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
            else:
                query_set = reduce(or_, query_sets)

        else:
            query_set = Organ.objects.filter(filter)
            ids = query_set.values_list("pk", flat=True)
            query_set = Organ.objects.filter(pk__in=list(ids))

        query_pickle_hash = make_pickle_and_hash(query_set, "organ")
        return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)


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
        else:
            query_set = reduce(or_, query_sets)

    elif query_params["input_type"] == "cluster":
        query_set = Cluster.objects.filter(filter)

    query_pickle_hash = make_pickle_and_hash(query_set, "cluster")
    return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)


def get_datasets_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_dataset_filter(query_params)

    if query_params["input_type"] in ["cell", "cluster", "dataset"]:
        query_set = Dataset.objects.filter(filter)
        query_pickle_hash = make_pickle_and_hash(query_set, "dataset")
        return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)


def get_proteins_list(query_params: Dict):
    if query_params.get("input_type") is None:
        all_proteins = Protein.objects.all()
        query_pickle_hash = make_pickle_and_hash(all_proteins, "cluster")
        return QuerySet.objects.filter(query_pickle_hash=query_pickle_hash)


def gene_query(self, request):

    if request.method == "GET":
        all_genes = Gene.objects.all()
        pickle_hash = make_pickle_and_hash(all_genes, "gene")
        query_set = QuerySet.objects.filter(query_pickle_hash=pickle_hash)

    if request.method == "POST":
        query_params = request.data.dict()
        validate_dataset_query_params(query_params)
        query_set = get_genes_list(query_params, input_set=request.POST.getlist("input_set"))

    self.queryset = query_set
    # Set context
    context = {
        "request": request,
    }

    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response


def cell_query(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        validate_cell_query_params(query_params)
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

    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response


def organ_query(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        validate_organ_query_params(query_params)
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
        validate_cluster_query_params(query_params)
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

    response = QuerySetSerializer(query_set, many=True, context=context).data

    return response


def dataset_query(self, request):
    if request.method == "POST":
        query_params = request.data.dict()
        validate_dataset_query_params(query_params)
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
        response = ProteinSerializer(proteins, many=True, context=context).data
        return response
