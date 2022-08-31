from functools import reduce
from operator import and_, eq, ge, gt, le, lt, ne, or_
from typing import Dict, List

from django.core.cache import cache
from django.db.models import Case, Count, IntegerField, Q, Sum, When

from .apps import (
    atac_cell_df,
    atac_gene_df,
    atac_percentages,
    atac_pvals,
    codex_cell_df,
    codex_gene_df,
    codex_percentages,
    rna_cell_df,
    rna_gene_df,
    rna_percentages,
    rna_pvals,
    zarr_root,
)
from .models import Cell, Cluster, Dataset, Modality, Organ
from .utils import unpickle_query_set
from .validation import process_query_parameters, split_at_comparator

operators_dict = {">": gt, ">=": ge, "<": lt, "<=": le, "==": eq, "!=": ne}
modalities_to_pvals = {"rna": rna_pvals, "atac": atac_pvals}


def get_precomputed_datasets(modality, min_cell_percentage, input_set):
    if len(input_set) > 1:
        return None

    if modality == "rna":
        df = rna_percentages
    elif modality == "atac":
        df = atac_percentages
    elif modality == "codex":
        df = codex_percentages

    print(input_set)
    input_set_split = split_at_comparator(input_set[0])
    print(input_set_split)
    input_set_split = [item.strip() for item in input_set_split]
    print(input_set_split)
    var_id = input_set_split[0]
    cutoff = float(input_set_split[2])

    if var_id in df["var_id"].values and cutoff in df["cutoff"].values:
        try:
            df = df.loc[(var_id, cutoff, slice(None))]
            df = df[df["percentage"] >= float(min_cell_percentage)]
            return Q(uuid__in=list(df["dataset"].unique()))
        except:
            print((var_id, cutoff, slice(None)))

    return None


def get_cells_list(query_params: Dict, input_set=None):
    query_params = process_query_parameters(query_params, input_set)
    filter = get_cell_filter(query_params)

    query_set = Cell.objects.filter(filter)

    pks = query_set.values_list("pk", flat=True)
    query_set = Cell.objects.filter(pk__in=pks)
    query_set = query_set.distinct("cell_id")

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

    cell_dfs_dict = {"atac": atac_cell_df, "codex": codex_cell_df, "rna": rna_cell_df}

    value = float(split_condition[2].strip())

    var_id = split_condition[0].strip()

    if input_type == "protein":
        modality = "codex"
    elif genomic_modality == "rna":
        modality = "rna"
    elif genomic_modality == "atac":
        modality = "atac"

    cell_df = cell_dfs_dict[modality]

    try:
        operator = operators_dict[split_condition[1].strip()]
        num_array = zarr_root[f"/{modality}/{var_id}"][:]
        bool_array = operator(num_array, value)
        cell_ids = cell_df[bool_array].cell_id.to_list()
        return Q(cell_id__in=cell_ids)

    except Exception as e:
        raise ValueError(f"{var_id} not present in {modality} index")


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

    elif input_type == "modality":
        genes_list = []
        if "rna" in input_set:
            genes_list.extend(list(rna_gene_df.index))
        if "atac" in input_set:
            genes_list.extend(list(atac_gene_df.index))
        return Q(gene_symbol__in=genes_list)

    genomic_modality = query_params["genomic_modality"]

    if input_type in groupings_dict:

        if genomic_modality == "rna":
            df = rna_pvals
            df = df[df["grouping_name"].isin(input_set)]
            df = df[df["value"] <= p_value]
            gene_symbols = list(df["gene_id"].unique())

        elif genomic_modality == "atac":
            atac_pvals = modalities_to_pvals["atac"]
            atac_pvals = atac_pvals[atac_pvals.obs.grouping_type == input_type]
            bool_masks = [atac_pvals[[var], :].X <= p_value for var in input_set]
            bool_mask = reduce(or_, bool_masks)
            atac_pvals = atac_pvals[:, bool_mask]
            gene_symbols = list(atac_pvals.var.index)

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
        "cell_type": "grouping_name",
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

    entities_dict = {
        "cell": {"cell_id__in": input_set},
        "cell_type": {"cell_type__grouping_name__in": input_set},
        "dataset": {"dataset__uuid__in": input_set},
        "cluster": {"clusters__grouping_name__in": input_set},
    }

    if input_type in entities_dict:
        kwargs = entities_dict[input_type]
        cell_qs = Cell.objects.filter(**kwargs)
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
            df = df[df["gene_id"].isin(input_set)]
            df = df[df["value"] <= p_value]
            grouping_names = list(df["grouping_name"].unique())
        elif genomic_modality == "atac":
            atac_pvals = modalities_to_pvals["atac"]
            organ_pvals = atac_pvals[atac_pvals.obs.grouping_type == "organ"]
            bool_masks = [organ_pvals[:, [var]].X <= p_value for var in input_set]
            bool_mask = reduce(or_, bool_masks)
            organ_pvals = organ_pvals[bool_mask, :]
            grouping_names = list(organ_pvals.obs.index)

        return Q(grouping_name__in=grouping_names)


def get_cell_type_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for group objects based on the input set, input type, and logical operator
    Currently services membership queries where input type is cells
    and categorical queries where input type is genes"""

    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    if input_type == "cell_type":
        return Q(grouping_name__in=input_set)

    entities_dict = {
        "cell": {"cell_id__in": input_set},
        "dataset": {"dataset__uuid__in": input_set},
        "organ": {"organ__grouping_name__in": input_set},
    }

    if input_type in entities_dict:
        kwargs = entities_dict[input_type]
        cell_qs = Cell.objects.filter(**kwargs)
        cell_type_pks = cell_qs.distinct("cell_type").values_list("cell_type", flat=True)

        q = Q(pk__in=cell_type_pks)

        return q


def get_cluster_filter(query_params: dict):
    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    entities_dict = {
        "cell": {"cell_id__in": input_set},
        "organ": {"organ__grouping_name__in": input_set},
    }

    if input_type == "cluster":
        return Q(grouping_name__in=input_set)

    if input_type == "gene":

        genomic_modality = query_params["genomic_modality"]
        # Query those genes and return their associated groupings
        p_value = query_params["p_value"]

        if genomic_modality == "rna":
            df = rna_pvals
            df = df[df["gene_id"].isin(input_set)]
            df = df[df["value"] <= p_value]
            grouping_names = list(df["grouping_name"].unique())

        elif genomic_modality == "atac":
            atac_pvals = modalities_to_pvals["atac"]
            cluster_pvals = atac_pvals[atac_pvals.obs.grouping_type == "cluster"]
            bool_masks = [cluster_pvals[:, [var]].X <= p_value for var in input_set]
            bool_mask = reduce(or_, bool_masks)
            cluster_pvals = cluster_pvals[bool_mask, :]
            grouping_names = list(cluster_pvals.obs.index)

        return Q(grouping_name__in=grouping_names)

    elif input_type == "dataset":
        return Q(dataset__uuid__in=input_set)

    elif input_type in entities_dict:
        kwargs = entities_dict[input_type]
        cell_qs = Cell.objects.filter(**kwargs)
        cell_pks = cell_qs.values_list("pk", flat=True)
        cluster_pks = Cluster.objects.filter(cells__pk__in=cell_pks).values_list("pk", flat=True)
        #        cluster_pks = {cluster.id for cell in cell_qs for cluster in cell.clusters.all()}
        q = Q(pk__in=cluster_pks)
        return q


def get_dataset_filter(query_params: dict):
    input_type = query_params["input_type"]
    input_set = query_params["input_set"]

    if input_type == "dataset":
        return Q(uuid__in=input_set)

    elif input_type == "modality":
        return Q(modality__modality_name__in=input_set)

    entities_dict = {
        "cell": {"cell_id__in": input_set},
        "cell_type": {"cell_type__grouping_name__in": input_set},
        "organ": {"organ__grouping_name__in": input_set},
        "cluster": {"clusters__grouping_name__in": input_set},
    }
    if input_type in entities_dict:
        kwargs = entities_dict[input_type]
        cell_qs = Cell.objects.filter(**kwargs)
        dataset_pks = cell_qs.distinct("dataset").values_list("dataset", flat=True)
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
            return precomputed_datasets

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
