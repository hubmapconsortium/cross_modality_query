from functools import reduce
from operator import and_, or_
from typing import Dict, List

from django.core.cache import cache
from django.db.models import Case, Count, IntegerField, Q, Sum, When

from .models import (
    AtacQuant,
    Cell,
    Cluster,
    CodexQuant,
    Dataset,
    Gene,
    Modality,
    Organ,
    PrecomputedPercentage,
    Protein,
    RnaQuant,
)
from .utils import min_percentages, modality_ranges_dict, unpickle_query_set
from .validation import process_query_parameters, split_at_comparator


def check_for_precomputed_value(query_params):
    input_type = query_params["input_type"]
    modality = query_params["genomic_modality"] if input_type == "gene" else "codex"

    min_cell_percent = query_params["min_cell_percentage"]
    input_set = query_params["input_set"]

    cutoff = split_at_comparator(input_set[0])[2]
    exponents = list(
        range(modality_ranges_dict[modality][0], modality_ranges_dict[modality][1] + 1)
    )
    cutoffs = [10 ** exponent for exponent in exponents]

    if len(input_set) > 1 or min_cell_percent not in min_percentages or cutoff not in cutoffs:
        return False

    return True


def get_pre_computed_value(query_params):
    input_type = query_params["input_type"]
    modality = query_params["genomic_modality"] if input_type == "gene" else "codex"

    min_cell_percent = query_params["min_cell_percentage"]
    input_set = query_params["input_set"]

    cutoff = split_at_comparator(input_set[0])[2]
    var_id = split_at_comparator(input_set[0])[0]

    pks = (
        PrecomputedPercentage.objects.filter(modality__modality_name__iexact=modality)
        .filter(var_id__iexact=var_id)
        .filter(cutoff=cutoff)
        .filter(percentage__gte=min_cell_percent)
        .values_list("dataset", flat=True)
    )

    return Q(pk__in=pks)


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

    if query_params["input_type"] in ["gene", "protein"]:
        query_set = get_quant_queryset(query_params, filter)
    else:
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


def process_single_condition(split_condition: List[str], input_type: str) -> Q:
    """List[str], str -> Q
    Finds the keyword args for a quantitative query based on the results of
    calling split_at_comparator() on a string representation of that condition"""
    comparator = split_condition[1]

    assert comparator in [">", ">=", "<=", "<", "==", "!="]
    value = float(split_condition[2].strip())

    var_id = split_condition[0].strip()

    q = Q(q_var_id__iexact=var_id)

    if comparator == ">":
        q = q & Q(value__gt=value)
    elif comparator == ">=":
        q = q & Q(value__gte=value)
    elif comparator == "<":
        q = q & (Q(value__lt=value))
    elif comparator == "<=":
        q = q & (Q(value__lte=value))
    elif comparator == "==":
        q = q & Q(value__exact=value)
    elif comparator == "!=":
        q = q & ~Q(value__exact=value)

    #    if input_type == "protein":
    #        q = q & Q(statistic__iexact="mean")

    print(q)

    return q


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

        # Assumes clusters are of the form uuid-clusternum
        if input_type == "cluster":

            clusters = Cluster.objects.filter(grouping_name__in=input_set)
            q = Q(p_cluster_id__in=clusters)

        else:
            q_kwargs = [{groupings_dict[input_type]: element} for element in input_set]
            qs = [Q(**kwargs) for kwargs in q_kwargs]

            q = combine_qs(qs, "or")

        q = q & Q(value__lte=p_value)

        if genomic_modality:
            q = q & Q(modality__modality_name=genomic_modality)

        return q


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

    if input_type in ["protein", "gene"]:

        split_conditions = [
            [item, ">", "0"] if len(split_at_comparator(item)) == 0 else split_at_comparator(item)
            for item in input_set
        ]

        qs = [process_single_condition(condition, input_type) for condition in split_conditions]
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
        p_value = query_params["p_value"]
        genomic_modality = query_params["genomic_modality"]
        q = Q(p_gene__gene_symbol__in=input_set) & Q(value__lte=p_value)
        if genomic_modality:
            q = q & Q(modality__modality_name=genomic_modality)

        organ_pks = Organ.objects.all().values_list("pk", flat=True)
        q = q & Q(p_organ__in=organ_pks)

        return q


def get_cluster_filter(query_params: dict):
    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    if input_type == "cluster":
        return Q(grouping_name__in=input_set)

    if input_type == "gene":

        genomic_modality = query_params["genomic_modality"]
        # Query those genes and return their associated groupings
        p_value = query_params["p_value"]

        q = Q(p_gene__gene_symbol__in=input_set) & Q(value__lte=p_value)

        if genomic_modality:
            q = q & Q(modality__modality_name=genomic_modality)

        cluster_pks = Cluster.objects.all().values_list("pk", flat=True)
        q = q & Q(p_cluster__in=cluster_pks)

        return q

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
    dataset_cells = Cell.objects.filter(dataset__uuid=uuid)
    dataset_count = cache.get(f"{uuid}_cells_count")
    if not dataset_count:
        dataset_count = dataset_cells.count()
    dataset_and_var_cells = dataset_cells.intersection(var_cells)
    percentage = dataset_and_var_cells.count() / dataset_count
    if len(include_values) == 1:
        split = split_at_comparator(include_values[0])
        if len(split) > 1:
            var_id = split[0]
            cutoff = split[2]
            key = f"{uuid}-{var_id}-{cutoff}"
            cache.set(key, percentage)
    return percentage


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

        if check_for_precomputed_value(query_params):
            return get_pre_computed_value(query_params)

        var_cell_pks = list(get_cells_list(query_params).values_list("pk", flat=True))
        var_cells = (
            Cell.objects.filter(pk__in=var_cell_pks)
            .only("pk", "dataset")
            .select_related("dataset")
        )
        min_cell_percentage = query_params["min_cell_percentage"]
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
