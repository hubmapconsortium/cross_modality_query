from typing import Dict, List, Set

from .utils import unpickle_query_set


def check_input_type(input_type, permitted_input_types):
    if input_type not in permitted_input_types:
        raise ValueError(f"{input_type} not in {permitted_input_types}")


def check_parameter_fields(query_params: Dict, required_fields: Set, permitted_fields: Set):
    param_fields = set(query_params.keys())
    missing_fields = required_fields - param_fields
    if len(missing_fields) > 0:
        raise ValueError(f"Missing parameters: {missing_fields}")
    extra_fields = param_fields - permitted_fields
    if len(extra_fields) > 0:
        raise ValueError(f"Invalid parameters: {extra_fields}")


def validate_gene_query_params(query_params):
    required_fields = {"input_type", "input_set", "genomic_modality", "logical_operator"}
    permitted_fields = {
        "input_type",
        "input_set",
        "genomic_modality",
        "logical_operator",
        "p_value",
        "input_set_token",
    }

    check_parameter_fields(query_params, required_fields, permitted_fields)

    permitted_input_types = ["organ", "cluster"]
    input_type = query_params["input_type"]

    check_input_type(input_type, permitted_input_types)


def validate_organ_query_params(query_params):
    permitted_input_types = ["cell", "gene"]
    input_type = query_params["input_type"]
    check_input_type(input_type, permitted_input_types)

    if input_type == "gene":
        required_fields = {"input_type", "input_set", "genomic_modality", "logical_operator"}
        permitted_fields = {
            "input_type",
            "input_set",
            "genomic_modality",
            "logical_operator",
            "p_value",
            "input_set_token",
        }
        check_parameter_fields(query_params, required_fields, permitted_fields)

    elif input_type == "cell":
        required_fields = {"input_type", "input_set"}
        permitted_fields = {"input_type", "input_set", "input_set_token"}
        check_parameter_fields(query_params, required_fields, permitted_fields)


def validate_cluster_query_params(query_params):
    permitted_input_types = ["cell", "gene", "dataset"]
    input_type = query_params["input_type"]
    check_input_type(input_type, permitted_input_types)

    if input_type == "gene":
        required_fields = {"input_type", "input_set", "genomic_modality", "logical_operator"}
        permitted_fields = {
            "input_type",
            "input_set",
            "genomic_modality",
            "logical_operator",
            "p_value",
            "input_set_token",
        }
        check_parameter_fields(query_params, required_fields, permitted_fields)

    elif input_type == "cell":
        required_fields = {"input_type", "input_set"}
        permitted_fields = {"input_type", "input_set", "input_set_token"}
        check_parameter_fields(query_params, required_fields, permitted_fields)


def validate_dataset_query_params(query_params):
    permitted_input_types = ["cell", "cluster"]
    input_type = query_params["input_type"]
    check_input_type(input_type, permitted_input_types)

    required_fields = {"input_type", "input_set"}
    permitted_fields = {"input_type", "input_set", "input_set_token"}
    check_parameter_fields(query_params, required_fields, permitted_fields)


def validate_cell_query_params(query_params):
    permitted_input_types = ["organ", "gene", "dataset", "cluster", "protein"]
    input_type = query_params["input_type"]
    check_input_type(input_type, permitted_input_types)

    if input_type == "gene":
        required_fields = {"input_type", "input_set", "genomic_modality", "logical_operator"}
        permitted_fields = {
            "input_type",
            "input_set",
            "genomic_modality",
            "logical_operator",
            "input_set_token",
        }
        check_parameter_fields(query_params, required_fields, permitted_fields)

    elif input_type == "organ":
        required_fields = {"input_type", "input_set"}
        permitted_fields = {"input_type", "input_set", "input_set_token"}
        check_parameter_fields(query_params, required_fields, permitted_fields)

    elif input_type == "dataset":
        required_fields = {"input_type", "input_set"}
        permitted_fields = {"input_type", "input_set", "input_set_token"}
        check_parameter_fields(query_params, required_fields, permitted_fields)

    elif input_type == "cluster":
        required_fields = {"input_type", "input_set"}
        permitted_fields = {"input_type", "input_set", "input_set_token"}
        check_parameter_fields(query_params, required_fields, permitted_fields)


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

    if (
        "offset" not in query_params.keys()
        or not query_params["offset"].isdigit()
        or int(query_params["offset"]) < 0
    ):
        query_params["offset"] = 0
    else:
        query_params["offset"] = int(query_params["offset"])

    if (
        "limit" not in query_params.keys()
        or not query_params["limit"].isdigit()
        or int(query_params["limit"]) > 1000
    ):
        query_params["limit"] = 1000
    else:
        query_params["limit"] = int(query_params["limit"])

    query_params["limit"] = query_params["limit"] + query_params["offset"]

    query_params["sort_by"] = sort_by
    query_params["include_values"] = include_values

    return query_params
