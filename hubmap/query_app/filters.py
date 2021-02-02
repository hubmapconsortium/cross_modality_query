from functools import reduce
from operator import and_, or_
from typing import Dict, List

from django.db.models import Q

from .models import Cell, Cluster, Dataset, Organ
from .validation import split_at_comparator


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

        q = q & Q(value__lte=p_value) & Q(modality__modality_name__icontains=genomic_modality)

        return q


def get_cell_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for cell objects based on the input set, input type, and logical operator
    Currently services quantitative queries where input is protein, atac_gene, or rna_gene
    and membership queries where input is tissue_type"""

    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    groupings_dict = {"organ": "grouping_name", "cluster": "grouping_name", "dataset": "uuid"}

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

        # Query groupings and then union their cells fields
        cell_ids = []

        if input_type == "organ":
            for organ in Organ.objects.filter(grouping_name__in=input_set):
                cell_ids.extend([cell.cell_id for cell in organ.cells.all()])

        elif input_type == "cluster":
            for cluster in Cluster.objects.filter(grouping_name__in=input_set):
                cell_ids.extend([cell.cell_id for cell in cluster.cells.all()])

        elif input_type == "dataset":
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

        q = (
            Q(p_gene__gene_symbol__in=input_set)
            & Q(modality__modality_name=genomic_modality)
            & Q(value__lte=p_value)
        )
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

        q = (
            Q(p_gene__gene_symbol__in=input_set)
            & Q(value__lte=p_value)
            & Q(modality__modality_name=genomic_modality)
        )
        cluster_pks = Cluster.objects.all().values_list("pk", flat=True)
        q = q & Q(p_cluster__in=cluster_pks)

        return q

    elif input_type == "cell":

        cell_qs = Cell.objects.filter(cell_id__in=input_set)

        cluster_pks = cell_qs.distinct("dataset").values_list("cluster", flat=True)

        q = Q(pk__in=cluster_pks)

        return q

    elif input_type == "dataset":

        print(Dataset.objects.filter(uuid__in=input_set).count())

        cluster_ids = []

        for dataset in Dataset.objects.filter(uuid__in=input_set):
            cluster_ids.extend([cluster.grouping_name for cluster in dataset.clusters.all()])

        return Q(grouping_name__in=cluster_ids)


def get_dataset_filter(query_params: dict):
    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    if input_type == "dataset":
        return Q(uuid__in=input_set)

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
