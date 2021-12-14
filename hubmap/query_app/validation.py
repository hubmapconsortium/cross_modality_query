from typing import Dict, List, Set

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.functions import Upper

from .models import Cell, Cluster, Dataset, Gene, Modality, Organ, Protein
from .utils import infer_values_type, split_at_comparator, unpickle_query_set


def check_input_type(input_type, permitted_input_types):
    permitted_input_types.sort()
    if input_type not in permitted_input_types:
        raise ValueError(f"{input_type} not in {permitted_input_types}")


def check_parameter_types_and_values(query_params):

    if not isinstance(query_params["input_set"], list):
        raise ValueError(f"Input must be of type list, not {type(query_params['input_set'])}")

    genomic_modalities = ["rna", "atac"]  # Used for quantitative gene->cell queries
    if "genomic_modality" in query_params.keys():
        if query_params["genomic_modality"] not in genomic_modalities:
            genomic_modalities.sort()
            raise ValueError(f"{query_params['genomic_modality']} not in {genomic_modalities}")

    if "p_value" in query_params.keys():
        p_value = query_params["p_value"]
        if p_value is None or float(p_value) < 0 or float(p_value) > 1:
            raise ValueError(f"p_value {p_value} should be in [0,1]")

    check_input_set(query_params["input_set"], query_params["input_type"])
    input_type = query_params["input_type"]
    input_set = query_params["input_set"]
    validate_input_terms(input_type, input_set)


def check_input_set(input_set, input_type):
    input_set = [
        split_at_comparator(item)[0].strip() if len(split_at_comparator(item)) > 0 else item
        for item in input_set
    ]
    items_not_found = []
    if input_type == "gene":
        items_not_found = [
            item
            for item in input_set
            if Gene.objects.filter(gene_symbol__iexact=item).first() is None
        ]
    if input_type == "protein":
        items_not_found = [
            item
            for item in input_set
            if Protein.objects.filter(protein_id__iexact=item).first() is None
        ]
    if input_type == "modality":
        items_not_found = [
            item
            for item in input_set
            if Modality.objects.filter(modality_name__iexact=item).first() is None
        ]
    if len(items_not_found) > 0:
        items_not_found_string = ", ".join(items_not_found)
        recommendations = []
        for item in items_not_found:
            recommendations += recommend_identifiers(item, input_type)
        recommendations_string = ", ".join(recommendations)
        raise ValueError(
            f"No {input_type}s found with names: {items_not_found_string}. Suggestions: {recommendations_string}"
        )


def recommend_identifiers(identifier: str, input_type: str):
    if input_type == "gene":
        identifier_upper = identifier.upper()
        annotated_genes = Gene.objects.annotate(
            similarity=TrigramSimilarity(Upper("gene_symbol"), identifier_upper)
        )
        similar_genes = annotated_genes.filter(similarity__gt=0.3).order_by("-similarity")[0:5]
        similar_ids = set(similar_genes.values_list("gene_symbol", flat=True))
    elif input_type == "protein":
        identifier_upper = identifier.upper()
        annotated_proteins = Protein.objects.annotate(
            similarity=TrigramSimilarity(Upper("protein_id"), identifier_upper)
        )
        similar_proteins = annotated_proteins.filter(similarity__gt=0.3).order_by("-similarity")[
            0:5
        ]
        similar_ids = set(similar_proteins.values_list("protein_id", flat=True))
    elif input_type == "modality":
        identifier_upper = identifier.upper()
        annotated_modalities = Modality.objects.annotate(
            similarity=TrigramSimilarity(Upper("modality_name"), identifier_upper)
        )
        similar_modalities = annotated_modalities.filter(similarity__gt=0.3).order_by(
            "-similarity"
        )[0:5]
        similar_ids = set(similar_modalities.values_list("modality_name", flat=True))
    return similar_ids


def check_parameter_fields(query_params: Dict, required_fields: Set, permitted_fields: Set):
    param_fields = set(query_params.keys())
    missing_fields = list(required_fields - param_fields)
    missing_fields.sort()
    if len(missing_fields) > 0:
        raise ValueError(f"Missing parameters: {missing_fields}")
    extra_fields = list(param_fields - permitted_fields)
    extra_fields = [item for item in extra_fields if item not in required_fields]
    extra_fields.sort()
    if len(extra_fields) > 0:
        raise ValueError(f"Invalid parameters: {extra_fields}")


def validate_gene_query_params(query_params):
    permitted_input_types = ["organ", "cluster", "gene", "modality"]
    input_type = query_params["input_type"]

    check_input_type(input_type, permitted_input_types)

    required_fields = {"input_type", "input_set"}
    permitted_fields = required_fields | {"p_value", "genomic_modality", "input_set_token"}
    if input_type in ["cluster", "organ"]:
        if len(query_params["input_set"]) > 1:
            permitted_fields.add("logical_operator")

    check_parameter_fields(query_params, required_fields, permitted_fields)

    check_parameter_types_and_values(query_params)


def validate_organ_query_params(query_params):
    permitted_input_types = ["cell", "gene", "organ"]
    input_type = query_params["input_type"]
    check_input_type(input_type, permitted_input_types)

    required_fields = {"input_type", "input_set"}
    permitted_fields = required_fields | {"input_set_token"}

    if input_type == "gene":
        permitted_fields.add("p_value")
        permitted_fields.add("genomic_modality")
        if len(query_params["input_set"]) > 1:
            permitted_fields.add("logical_operator")

    check_parameter_fields(query_params, required_fields, permitted_fields)

    check_parameter_types_and_values(query_params)


def validate_cluster_query_params(query_params):
    permitted_input_types = ["cell", "gene", "dataset", "cluster"]
    input_type = query_params["input_type"]
    check_input_type(input_type, permitted_input_types)

    required_fields = {"input_type", "input_set"}
    permitted_fields = required_fields | {"input_set_token"}

    if input_type == "gene":
        permitted_fields.add("p_value")
        permitted_fields.add("genomic_modality")
        if len(query_params["input_set"]) > 1:
            permitted_fields.add("logical_operator")

    check_parameter_fields(query_params, required_fields, permitted_fields)

    check_parameter_types_and_values(query_params)


def validate_dataset_query_params(query_params):
    permitted_input_types = ["cell", "cluster", "dataset", "gene", "modality", "protein"]
    input_type = query_params["input_type"]
    check_input_type(input_type, permitted_input_types)

    required_fields = {"input_type", "input_set"}
    permitted_fields = required_fields | {"input_set_token"}
    if input_type in ["gene", "protein"]:
        permitted_fields.add("min_cell_percentage")
        if input_type == "gene":
            required_fields.add("genomic_modality")
        print(required_fields)
    check_parameter_fields(query_params, required_fields, permitted_fields)

    check_parameter_types_and_values(query_params)


def validate_protein_query_params(query_params):
    permitted_input_types = ["protein"]
    input_type = query_params["input_type"]
    check_input_type(input_type, permitted_input_types)

    required_fields = {"input_type", "input_set"}
    permitted_fields = required_fields | {"input_set_token"}
    check_parameter_fields(query_params, required_fields, permitted_fields)

    check_parameter_types_and_values(query_params)


def validate_cell_query_params(query_params):
    permitted_input_types = ["organ", "gene", "dataset", "cluster", "protein", "cell", "modality"]
    input_type = query_params["input_type"]
    check_input_type(input_type, permitted_input_types)

    required_fields = {"input_type", "input_set"}

    if input_type == "gene":
        required_fields.add("genomic_modality")
        if len(query_params["input_set"]) > 1:
            required_fields.add("logical_operator")

    permitted_fields = required_fields | {"input_set_token"}
    check_parameter_fields(query_params, required_fields, permitted_fields)

    check_parameter_types_and_values(query_params)


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
    if "input_set_key" in query_params.keys() and query_params["input_set_key"] != "":
        qs = unpickle_query_set(query_params["input_set_key"], query_params["input_type"])
        identifiers = {
            "cell": "cell_id",
            "gene": "gene_symbol",
            "organ": "grouping_name",
            "cluster": "grouping_name",
            "dataset": "uuid",
        }
        identifier = identifiers[query_params["input_type"]]
        query_params["input_set"].extend(qs.values_list(identifier, flat=True))

    if (
        "p_value" not in query_params.keys()
        or query_params["p_value"] == ""
        or float(query_params["p_value"]) < 0.0
        or float(query_params["p_value"]) > 1.0
    ):
        query_params["p_value"] = 0.00
    else:
        query_params["p_value"] = float(query_params["p_value"])

    if "genomic_modality" not in query_params.keys():
        query_params["genomic_modality"] = None

    if "logical_operator" not in query_params.keys():
        query_params["logical_operator"] = "or"

    if "min_cell_percentage" not in query_params.keys():
        query_params["min_cell_percentage"] = 10.0

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


def validate_list_evaluation_args(query_params):

    required_fields = {"key", "set_type", "limit"}
    permitted_fields = required_fields | {"offset"}
    check_parameter_fields(query_params, required_fields, permitted_fields)


def validate_detail_evaluation_args(query_params):

    required_fields = {"key", "set_type", "limit"}
    permitted_fields = required_fields | {"offset", "sort_by", "values_included"}
    check_parameter_fields(query_params, required_fields, permitted_fields)
    if "values_included" in query_params and len(query_params["values_included"]) > 0:
        values_type = infer_values_type(query_params["values_included"])
        check_input_set(query_params["values_included"], values_type)


def validate_values_types(set_type, values_type):
    type_map = {
        "cell": ["gene", "protein"],
        "gene": ["organ", "cluster"],
        "cluster": ["gene"],
        "organ": ["gene"],
        "dataset": ["gene", "protein"],
    }
    allowed_types = type_map[set_type]
    allowed_types.sort()

    if values_type not in allowed_types:
        raise ValueError(f'For "{set_type}", only {allowed_types} allowed, not "{values_type}"')


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
            include_values = query_params["values_included"]
    else:
        include_values = []

    if sort_by is not None and sort_by not in include_values:
        include_values.append(sort_by)

    if (
        "offset" not in query_params.keys()
        or not query_params["offset"].isdigit()
        or int(query_params["offset"]) < 0
    ):
        offset = 0
    else:
        offset = int(query_params["offset"])

    if (
        "limit" not in query_params.keys()
        or not query_params["limit"].isdigit()
        or int(query_params["limit"]) > 100000
    ):
        query_params["limit"] = 100000
    else:
        query_params["limit"] = int(query_params["limit"])

    limit = query_params["limit"] + offset

    key = query_params["key"]

    return key, include_values, sort_by, limit, offset


def validate_statistic_args(query_params):
    required_fields = {"key", "set_type", "var_id", "stat_type"}
    permitted_fields = required_fields
    check_parameter_fields(query_params, required_fields, permitted_fields)

    permitted_set_types = ["cell"]
    permitted_set_types.sort()
    set_type = query_params["set_type"]
    if set_type not in permitted_set_types:
        raise ValueError(f"{set_type} not supported, only {permitted_set_types}")

    permitted_stat_types = ["mean", "min", "max", "stddev"]
    permitted_stat_types.sort()
    stat_type = query_params["stat_type"]
    if stat_type not in permitted_stat_types:
        raise ValueError(f"{stat_type} not supported, only {permitted_stat_types}")

    return (
        query_params["key"],
        query_params["set_type"],
        query_params["var_id"],
        query_params["stat_type"],
    )


def validate_bounds_args(query_params: Dict):
    required_fields = {"modality"}
    permitted_fields = required_fields | {"var_id"}
    check_parameter_fields(query_params, required_fields, permitted_fields)

    modality = query_params["modality"]
    permitted_modalities = ["rna", "atac", "codex"]
    permitted_modalities.sort()
    if modality not in permitted_modalities:
        raise ValueError(f"{modality} not supported, only {permitted_modalities}")

    if "var_id" in query_params:
        if (
            modality == "codex"
            and Protein.objects.filter(protein_id=query_params["var_id"]).first() is None
        ):
            raise ValueError(f"{query_params['var_id']} is not in protein index")
        if (
            modality in ["atac", "rna"]
            and Gene.objects.filter(gene_symbol=query_params["var_id"]).first() is None
        ):
            raise ValueError(f"{query_params['var_id']} is not in gene index")


def validate_input_terms(input_type: str, input_set: List[str]):

    input_set = [
        split_at_comparator(item)[0].strip()
        if len(split_at_comparator(item)) > 0
        else item.strip()
        for item in input_set
    ]

    input_type_model_mapping = {
        "gene": (Gene, "gene_symbol"),
        "protein": (Protein, "protein_id"),
        "organ": (Organ, "grouping_name"),
        "cluster": (Cluster, "grouping_name"),
        "cell": (Cell, "cell_id"),
        "dataset": (Dataset, "uuid"),
        "modality": (Modality, "modality_name"),
    }

    model, kwarg_piece = input_type_model_mapping[input_type]
    identifiers_not_found = [
        item for item in input_set if not model.objects.filter(**{f"{kwarg_piece}__iexact": item})
    ]

    if len(identifiers_not_found) > 0:
        identifiers_string = ", ".join(identifiers_not_found)
        raise ValueError(f"No {input_type} found with identifiers: {identifiers_string}")
