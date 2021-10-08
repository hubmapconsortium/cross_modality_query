from functools import reduce
from operator import and_, or_
from typing import Dict, List

from django.core.cache import cache
from django.db.models import Case, Count, IntegerField, Q, Sum, When

from .apps import (
    atac_adata,
    atac_percentages,
    atac_pvals,
    codex_adata,
    codex_percentages,
    rna_adata,
    rna_percentages,
    rna_pvals,
)
from .models import (
    AtacQuant,
    Cell,
    Cluster,
    CodexQuant,
    Dataset,
    Modality,
    Organ,
    RnaQuant,
)
from .utils import unpickle_query_set
from .validation import process_query_parameters, split_at_comparator


def get_precomputed_datasets(modality, min_cell_percentage, input_set):
    print(f"Len input set: {len(input_set)}")
    if len(input_set) > 1:
        return None

    if modality == "rna":
        df = rna_percentages
    elif modality == "atac":
        df = atac_percentages
    elif modality == "codex":
        df = codex_percentages

    input_set_split = split_at_comparator(input_set[0])
    input_set_split = [item.strip() for item in input_set_split]
    var_id = input_set_split[0]
    cutoff = float(input_set_split[2])

    if var_id in list(df["var_id"].unique()) and float(cutoff) in list(df["cutoff"].unique()):
        print(len(df.index))
        df = df[df["var_id"] == var_id]
        print(len(df.index))
        df = df[df["cutoff"] == cutoff]
        print(len(df.index))
        df = df[df["percentage"] >= float(min_cell_percentage)]
        print(len(df.index))
        print(df["dataset"].unique())
        return Q(uuid__in=list(df["dataset"].unique()))

    return None


def cells_from_quants(quant_set, var):

    cell_ids = quant_set.values_list("q_cell_id", flat=True)

    cell_pks = Cell.objects.filter(cell_id__in=cell_ids).values_list("pk", flat=True)

    return Cell.objects.filter(pk__in=cell_pks)


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

    query_sets = [
        cells_from_quants(query_set.filter(q_var_id__iexact=var), var) for var in var_ids
    ]

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

    query_set = query_set.distinct("cell_id")
    query_set = Cell.objects.filter(pk__in=list(query_set.values_list("pk", flat=True)))

    return query_set


def get_cells_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_cell_filter(query_params)
    print("Filter gotten")

    query_set = Cell.objects.filter(filter)

    print("Query set found")

    return query_set


def combine_qs(qs: List[Q], logical_operator: str) -> Q:
    """List[Q] -> Q
    Combines a series of conditions into a single condition based on logical operator"""

    if len(qs) == 0:
        return Q(pk__in=[])
    if logical_operator == "or":
        return reduce(or_, qs)
    elif logical_operator == "and":
        return reduce(and_, qs)


def process_single_condition(
    split_condition: List[str], input_type: str, genomic_modality=None
) -> Q:
    """List[str], str -> Q
    Finds the keyword args for a quantitative query based on the results of
    calling split_at_comparator() on a string representation of that condition"""

    value = float(split_condition[2].strip())

    var_id = split_condition[0].strip()

    if input_type == "protein":
        adata = codex_adata
    elif genomic_modality == "rna":
        adata = rna_adata
    elif genomic_modality == "atac":
        adata = atac_adata

    adata = adata[:, [var_id]]
    bool_series = adata.X >= value
    adata = adata[bool_series, :]
    cell_ids = list(adata.obs.index)

    return Q(cell_id__in=cell_ids)


def get_gene_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for gene objects based on the input set, input type, and logical operator
    Currently only services categorical queries where input type is tissue_type or dataset"""

    input_type = query_params["input_type"]
    input_set = query_params["input_set"]
    p_value = query_params["p_value"]

    groupings_dict = {
        "organ": "p_organ__grouping_name__iexact",
        "cluster": "grouping_name__iexact",
    }

    if input_type == "gene":
        return Q(gene_symbol__in=input_set)

    genomic_modality = query_params["genomic_modality"]

    if input_type in groupings_dict:

        if genomic_modality == "rna":
            df = rna_pvals
        elif genomic_modality == "atac":
            df = atac_pvals

        print(input_set)
        print(len(df.index))
        df = df[df["grouping_name"].isin(input_set)]
        print(len(df.index))
        df = df[df["value"] <= p_value]
        print(len(df.index))

        gene_symbols = list(df["gene_id"].unique())

        return Q(gene_symbol__in=gene_symbols)


def get_cell_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for cell objects based on the input set, input type, and logical operator
    Currently services quantitative queries where input is protein, atac_gene, or rna_gene
    and membership queries where input is tissue_type"""

    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    groupings_dict = {
        "organ": "grouping_name",
        "cluster": "grouping_name",
        "dataset": "uuid",
        "modality": "modality_name",
    }

    if input_type == "cell":
        return Q(cell_id__in=input_set)

    if input_type in ["gene", "protein"]:
        if input_type == "protein":
            genomic_modality = None
        else:
            genomic_modality = query_params["genomic_modality"]

        split_conditions = [
            [item, ">", "0"] if len(split_at_comparator(item)) == 0 else split_at_comparator(item)
            for item in input_set
        ]

        split_conditions = [[item.strip() for condition in split_conditions for item in condition]]

        qs = [
            process_single_condition(condition, input_type, genomic_modality)
            for condition in split_conditions
        ]
        q = combine_qs(qs, "or")

        return q

    elif input_type in groupings_dict:

        if input_type == "cluster":
            cluster_pks = Cluster.objects.filter(grouping_name__in=input_set).values_list(
                "pk", flat=True
            )
            filter_kwargs = {"clusters__in": cluster_pks}
        else:
            filter_kwargs = {f"{input_type}__{groupings_dict[input_type]}__in": input_set}

        return Q(**filter_kwargs)


def get_organ_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for group objects based on the input set, input type, and logical operator
    Currently services membership queries where input type is cells
    and categorical queries where input type is genes"""

    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    if input_type == "organ":
        return Q(grouping_name__in=input_set)

    if input_type == "cell":

        cell_qs = Cell.objects.filter(cell_id__in=input_set)

        organ_pks = cell_qs.distinct("organ").values_list("organ", flat=True)

        q = Q(pk__in=organ_pks)

        return q

    elif input_type == "gene":
        # Query those genes and return their associated groupings
        genomic_modality = query_params["genomic_modality"]
        # Query those genes and return their associated groupings
        p_value = query_params["p_value"]

        if genomic_modality == "rna":
            df = rna_pvals
        elif genomic_modality == "atac":
            df = atac_pvals

        print(input_set)
        print(len(df.index))
        df = df[df["gene_id"].isin(input_set)]
        print(len(df.index))
        df = df[df["value"] <= p_value]
        print(len(df.index))

        grouping_names = list(df["grouping_name"].unique())

        print(len(grouping_names))

        return Q(grouping_name__in=grouping_names)


def get_cluster_filter(query_params: dict):
    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    if input_type == "cluster":
        return Q(grouping_name__in=input_set)

    if input_type == "gene":

        genomic_modality = query_params["genomic_modality"]
        # Query those genes and return their associated groupings
        p_value = query_params["p_value"]

        if genomic_modality == "rna":
            df = rna_pvals
        elif genomic_modality == "atac":
            df = atac_pvals

        df = df[df["gene_id"].isin(input_set)]
        df = df[df["value"] <= p_value]

        grouping_names = list(df["grouping_name"].unique())

        return Q(grouping_name__in=grouping_names)

    elif input_type == "cell":

        cell_qs = Cell.objects.filter(cell_id__in=input_set)

        cluster_pks = {cluster.id for cell in cell_qs for cluster in cell.clusters.all()}

        q = Q(pk__in=cluster_pks)

        return q

    elif input_type == "dataset":

        cluster_ids = []

        for dataset in Dataset.objects.filter(uuid__in=input_set):
            cluster_ids.extend([cluster.grouping_name for cluster in dataset.clusters.all()])

        return Q(grouping_name__in=cluster_ids)


def get_percentage_and_cache(params_tuple):
    uuid = params_tuple[0]
    var_cells = params_tuple[1]
    include_values = params_tuple[2]
    query_handle = cache.get(f"{uuid}_cells_set")
    dataset_cells = unpickle_query_set(query_handle, "dataset")
    dataset_count = cache.get(f"{uuid}_cells_count")
    print(uuid)
    print("Dataset cells found")
    dataset_and_var_cells = dataset_cells.intersection(var_cells)
    print("Intersection taken")
    percentage = dataset_and_var_cells.count() / dataset_count
    cache.set(f"{uuid}-{include_values}", percentage)


def get_dataset_filter(query_params: dict):
    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    if input_type == "dataset":
        return Q(uuid__in=input_set)

    elif input_type == "modality":
        return Q(modality__modality_name__in=input_set)

    if input_type == "cell":
        cell_qs = Cell.objects.filter(cell_id__in=input_set)

        dataset_pks = cell_qs.distinct("dataset").values_list("dataset", flat=True)

        q = Q(pk__in=dataset_pks)

        return q

    if input_type == "cluster":
        cluster_qs = Cluster.objects.filter(grouping_name__in=input_set)

        dataset_pks = cluster_qs.distinct("dataset").values_list("dataset", flat=True)

        q = Q(pk__in=dataset_pks)

        return q

    if input_type in ["gene", "protein"]:

        min_cell_percentage = query_params["min_cell_percentage"]

        if input_type == "gene":
            modality = query_params["genomic_modality"]
        elif input_type == "protein":
            modality = "codex"
        precomputed_datasets = get_precomputed_datasets(modality, min_cell_percentage, input_set)
        if precomputed_datasets:
            print("Precomputed datasets found")
            return precomputed_datasets

        print("Precomputed datasets not found")
        var_cell_pks = list(get_cells_list(query_params).values_list("pk", flat=True))
        var_cells = (
            Cell.objects.filter(pk__in=var_cell_pks)
            .only("pk", "dataset")
            .select_related("dataset")
        )
        dataset_pks = var_cells.distinct("dataset").values_list("dataset", flat=True)

        aggregate_kwargs = {
            str(dataset_pk): Sum(
                Case(When(dataset=dataset_pk, then=1), output_field=IntegerField())
            )
            for dataset_pk in dataset_pks
        }
        counts = var_cells.aggregate(**aggregate_kwargs)
        dataset_counts = {
            dataset_pk: Cell.objects.filter(dataset=dataset_pk).distinct("cell_id").count()
            for dataset_pk in dataset_pks
        }

        filtered_datasets = [
            pk
            for pk in dataset_pks
            if counts[str(pk)] / dataset_counts[pk] * 100 >= float(min_cell_percentage)
        ]

        return Q(pk__in=filtered_datasets)


def get_protein_filter(query_params: dict):
    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    if input_type == "protein":
        return Q(protein_id__in=input_set)
