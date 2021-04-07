from typing import Dict, List, Set

from .utils import unpickle_query_set


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


def check_parameter_fields(query_params: Dict, required_fields: Set, permitted_fields: Set):
    param_fields = set(query_params.keys())
    missing_fields = list(required_fields - param_fields)
    missing_fields.sort()
    if len(missing_fields) > 0:
        raise ValueError(f"Missing parameters: {missing_fields}")
    extra_fields = list(param_fields - permitted_fields)
    extra_fields.sort()
    if len(extra_fields) > 0:
        raise ValueError(f"Invalid parameters: {extra_fields}")


def validate_gene_query_params(query_params):
    permitted_input_types = ["organ", "cluster", "gene"]
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
    permitted_input_types = ["cell", "cluster", "dataset"]
    input_type = query_params["input_type"]
    check_input_type(input_type, permitted_input_types)

    required_fields = {"input_type", "input_set"}
    permitted_fields = required_fields | {"input_set_token"}
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
    permitted_input_types = ["organ", "gene", "dataset", "cluster", "protein", "cell"]
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
        "limit" not in query_params.keys()
        or not query_params["limit"].isnumeric()
        or int(query_params["limit"]) > 100
    ):
        query_params["limit"] = 100
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


def validate_list_evaluation_args(query_params):

    required_fields = {"key", "set_type", "limit"}
    permitted_fields = required_fields | {"offset"}
    check_parameter_fields(query_params, required_fields, permitted_fields)


def validate_detail_evaluation_args(query_params):

    required_fields = {"key", "set_type", "limit"}
    permitted_fields = required_fields | {"offset", "sort_by", "values_included"}
    check_parameter_fields(query_params, required_fields, permitted_fields)


def validate_values_types(set_type, values_type):
    type_map = {
        "cell": ["gene", "protein"],
        "gene": ["organ", "cluster"],
        "cluster": ["gene"],
        "organ": ["gene"],
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
        or int(query_params["limit"]) > 100
    ):
        query_params["limit"] = 100
    else:
        query_params["limit"] = int(query_params["limit"])

    limit = query_params["limit"] + offset

    key = query_params["key"]

    return key, include_values, sort_by, limit, offset
