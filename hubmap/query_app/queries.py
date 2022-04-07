from time import perf_counter
from typing import Dict

from django.core.cache import cache

from .apps import uuid_dict
from .filters import (
    get_cell_filter,
    get_cell_type_filter,
    get_cluster_filter,
    get_dataset_filter,
    get_gene_filter,
    get_organ_filter,
    get_protein_filter,
)
from .models import Cell, CellType, Cluster, Dataset, Gene, Organ, Protein
from .utils import get_response_from_query_handle, make_pickle_and_hash
from .validation import (
    process_query_parameters,
    validate_cell_query_params,
    validate_cell_type_query_params,
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


def get_genes_list(query_params: Dict, input_set=None):
    if query_params["input_type"] is None:
        return Gene.objects.all()
    else:
        query_params = process_query_parameters(query_params, input_set)
        filter = get_gene_filter(query_params)

        query_set = Gene.objects.filter(filter)

        query_set = query_set.distinct("gene_symbol")

        query_handle = make_pickle_and_hash(query_set, "gene")
        return query_handle


# Put fork here depending on whether or not we're returning expression values
def get_cells_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_cell_filter(query_params)

    query_set = Cell.objects.filter(filter).distinct("cell_id")
    query_handle = make_pickle_and_hash(query_set, "cell")
    return query_handle


def get_organs_list(query_params: Dict, input_set=None):
    if query_params.get("input_type") is None:

        all_organs = Organ.objects.all().distinct("grouping_name")
        query_handle = make_pickle_and_hash(all_organs, "organ")

    else:
        query_params = process_query_parameters(query_params, input_set)
        filter = get_organ_filter(query_params)

        query_set = Organ.objects.filter(filter)
        ids = query_set.values_list("pk", flat=True)
        query_set = Organ.objects.filter(pk__in=list(ids))

        query_set = query_set.distinct("grouping_name")

        query_handle = make_pickle_and_hash(query_set, "organ")

    return query_handle


def get_clusters_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_cluster_filter(query_params)

    query_set = Cluster.objects.filter(filter)

    query_set = query_set.distinct("grouping_name")

    query_handle = make_pickle_and_hash(query_set, "cluster")
    return query_handle


def get_datasets_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_dataset_filter(query_params)

    if query_params["input_type"] in ["cell", "cluster", "dataset", "gene", "modality", "protein"]:
        query_set = (
            Dataset.objects.filter(filter)
            .filter(modality__modality_name__isnull=False)
            .distinct("uuid")
        )
        query_handle = make_pickle_and_hash(query_set, "dataset")
        return query_handle


def get_cell_types_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_cell_type_filter(query_params)

    if query_params["input_type"] in ["cell", "cell_type"]:
        query_set = CellType.objects.filter(filter)
        query_handle = make_pickle_and_hash(query_set, "cell_type")
        return query_handle


def get_proteins_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_protein_filter(query_params)
    proteins = Protein.objects.filter(filter).distinct("protein_id")
    query_handle = make_pickle_and_hash(proteins, "protein")
    return query_handle


def gene_query(self, request):
    if request.data == {}:
        all_genes = Gene.objects.all().distinct("gene_symbol")
        pickle_hash = make_pickle_and_hash(all_genes, "gene")

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_gene_query_params(query_params)
        pickle_hash = get_genes_list(query_params, input_set=request.POST.getlist("input_set"))

    return get_response_from_query_handle(pickle_hash, "gene")


def cell_query(self, request):
    if request.data == {}:
        all_cells = Cell.objects.all().distinct("cell_id")
        pickle_hash = make_pickle_and_hash(all_cells, "cell")

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_cell_query_params(query_params)
        if (
            query_params["input_type"] in {"dataset", "modality"}
            and len(query_params["input_set"]) == 1
            and query_params["input_set"][0] in uuid_dict
        ):
            print(f"Found handle in uuid dict")
            pickle_hash = uuid_dict[query_params["input_set"][0]]
        else:
            pickle_hash = get_cells_list(query_params, input_set=request.POST.getlist("input_set"))

    return get_response_from_query_handle(pickle_hash, "cell")


def organ_query(self, request):
    if request.data == {}:
        all_organs = Organ.objects.all().distinct("grouping_name")
        pickle_hash = make_pickle_and_hash(all_organs, "organ")

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_organ_query_params(query_params)
        pickle_hash = get_organs_list(query_params, input_set=request.POST.getlist("input_set"))

    return get_response_from_query_handle(pickle_hash, "organ")


def cluster_query(self, request):

    if request.data == {}:
        all_clusters = Cluster.objects.all().distinct("grouping_name")
        pickle_hash = make_pickle_and_hash(all_clusters, "cluster")

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_cluster_query_params(query_params)
        pickle_hash = get_clusters_list(query_params, input_set=request.POST.getlist("input_set"))

    return get_response_from_query_handle(pickle_hash, "cluster")


def dataset_query(self, request):
    if request.data == {}:
        all_datasets = Dataset.objects.all().distinct("uuid")
        pickle_hash = make_pickle_and_hash(all_datasets, "dataset")

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_dataset_query_params(query_params)
        pickle_hash = get_datasets_list(query_params, input_set=request.POST.getlist("input_set"))

    return get_response_from_query_handle(pickle_hash, "dataset")


def protein_query(self, request):
    if request.data == {}:
        all_proteins = Protein.objects.all().distinct("protein_id")
        pickle_hash = make_pickle_and_hash(all_proteins, "protein")

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_protein_query_params(query_params)
        pickle_hash = get_proteins_list(query_params, input_set=request.POST.getlist("input_set"))

    return get_response_from_query_handle(pickle_hash, "protein")


def cell_type_query(self, request):
    if request.data == {}:
        all_cell_types = CellType.objects.all().distinct("protein_id")
        pickle_hash = make_pickle_and_hash(all_cell_types, "protein")

    else:
        query_params = request.data.dict()
        query_params["input_set"] = request.POST.getlist("input_set")
        validate_cell_type_query_params(query_params)
        pickle_hash = get_cell_types_list(
            query_params, input_set=request.POST.getlist("input_set")
        )

    return get_response_from_query_handle(pickle_hash, "cell_type")
