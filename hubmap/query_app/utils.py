from functools import reduce
from typing import Dict, List

from django.core.cache import cache
from django.db.models import Q

from .models import (
    Cell,
    CellAndValues,
    Cluster,
    Gene,
    GeneAndValues,
    Organ,
    OrganAndValues,
    Protein,
    PVal,
    AtacQuant,
    CodexQuant,
    RnaQuant,
)
from .serializers import (
    CellAndValuesSerializer,
    GeneAndValuesSerializer,
    OrganAndValuesSerializer,
    ProteinSerializer,
)


def get_zero_cells(gene: str, modality: str):
    gene = gene.split('<')[0]
    if modality == 'rna':
        non_zero_pks = cache.get('rna' + gene)
    elif modality == 'atac':
        non_zero_pks = cache.get('atac' + gene)

    zero_cells = Cell.objects.exclude(pk__in=non_zero_pks)

    return zero_cells

def get_non_zero_cells(gene: str, modality: str):
    gene = gene.split('<')[0]
    if modality == 'rna':
        non_zero_pks = cache.get('rna' + gene)
    elif modality == 'atac':
        non_zero_pks = cache.get('atac' + gene)

    non_zero_cells = Cell.objects.filter(pk__in=non_zero_pks)

    return non_zero_cells

def get_max_value_cells(cell_set, limit, values_dict, reverse_order):
    cell_ids = []

    if cell_set.count() == 0:
        return cell_set.filter(pk__in=[])

    limit = min(limit, cell_set.count())

    for i in range(limit):

        k = list(values_dict.keys())
        v = list(values_dict.values())

        if reverse_order:
            cell_ids.append(k[v.index(min(v))])
            values_dict.pop(k[v.index(min(v))])
        else:
            cell_ids.append(k[v.index(max(v))])
            values_dict.pop(k[v.index(max(v))])

    ids_dict = cache.get_many(cell_ids)
    pks = [ids_dict[id] for id in cell_ids]

    return cell_set.filter(pk__in=pks)


def order_cell_set(cell_set, gene, limit):

    reverse_order = "<" in gene
    if len(split_at_comparator(gene)) > 0:
        gene = split_at_comparator(gene)[0]

    dict_keys = [cell.cell_id + gene for cell in cell_set]

    cache_dict = cache.get_many(dict_keys)

    vals_dict = {}
    for cell in cell_set:
        if cell.cell_id + gene in cache_dict.keys():
            vals_dict[cell.cell_id] = cache_dict[cell.cell_id + gene]
        else:
            vals_dict[cell.cell_id] = 0.0

    return get_max_value_cells(cell_set, limit, vals_dict, reverse_order)


def genes_from_pvals(pval_set):
    ids = pval_set.distinct("p_gene").values_list("p_gene", flat=True)
    print(ids)
    return Gene.objects.filter(pk__in=list(ids))


def organs_from_pvals(pval_set):
    ids = pval_set.values_list("p_group", flat=True).distinct()
    print(ids)
    return Organ.objects.filter(pk__in=list(ids))


def clusters_from_pvals(pval_set):
    ids = pval_set.values_list("p_group", flat=True).distinct()
    print(ids)
    return Cluster.objects.filter(pk__in=list(ids))


def cells_from_quants(quant_set, var):
    print("Cells from quants called")

    values = quant_set.distinct("q_cell_id").values_list("q_cell_id", "q_gene_id", "value")
    print("Values gotten")
    ids = [triple[0] for triple in values]
    ids_dict = cache.get_many(ids)
    ids = [ids_dict[id] for id in ids]

    values_dict = {triple[0] + triple[1]: triple[2] for triple in values}
    cache.set_many(values_dict, 300)

    cells = Cell.objects.filter(pk__in=ids)

    print(cells.count())

    if '<' in var:
        if isinstance(quant_set.first(), RnaQuant):
            modality = 'rna'
        elif isinstance(quant_set.first(), AtacQuant):
            modality = 'atac'
        else:
            modality = 'protein'
        if modality in ['rna', 'atac']:
            zero_cells = get_zero_cells(var, modality)
            cells = zero_cells | cells

    return cells


def split_and_strip(string: str) -> List[str]:
    set_split = string.split(",")
    set_strip = [element.strip() for element in set_split]
    return set_strip


def process_query_parameters(query_params: Dict) -> Dict:
    if isinstance(query_params["input_set"], str):
        query_params["input_set"] = split_and_strip(query_params["input_set"])
    query_params["input_set"] = process_input_set(
        query_params["input_set"], query_params["input_type"]
    )
    query_params["input_type"] = query_params["input_type"].lower()
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


def q_and(q1: Q, q2: Q) -> Q:
    return q1 & q2


def q_or(q1: Q, q2: Q) -> Q:
    return q1 | q2


def combine_qs(qs: List[Q], logical_operator: str) -> Q:
    """List[Q] -> Q
    Combines a series of conditions into a single condition based on logical operator"""

    if len(qs) == 0:
        return Q(pk__in=[])
    if logical_operator == "or":
        return reduce(q_or, qs)
    elif logical_operator == "and":
        return reduce(q_and, qs)


def process_single_condition(split_condition: List[str], input_type: str) -> Q:
    """List[str], str -> Q
    Finds the keyword args for a quantitative query based on the results of
    calling split_at_comparator() on a string representation of that condition"""
    comparator = split_condition[1]

    assert comparator in [">", ">=", "<=", "<", "==", "!="]
    value = float(split_condition[2].strip())

    var_id = split_condition[0].strip()
    q = Q(q_var_id__iexact=var_id)

    if comparator == '>':
        q = q & Q(value__gt=value)
    elif comparator == '>=':
        q = q & Q(value__gte=value)
    elif comparator == '<':
        q = q & (Q(value__lt=value))
    elif comparator == '<=':
        q = q & (Q(value__lte=value))
    elif comparator == '==':
        q = q & Q(value__exact=value)
    elif comparator == '!=':
        q = q & ~Q(value__exact=value)

    return q


def get_gene_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for gene objects based on the input set, input type, and logical operator
    Currently only services categorical queries where input type is tissue_type or dataset"""

    input_type = query_params["input_type"]
    input_set = query_params["input_set"]
    p_value = query_params["p_value"]
    genomic_modality = query_params["genomic_modality"]

    groupings_dict = {"organ": "grouping_name", "cluster": "grouping_name", "dataset": "uuid"}

    if input_type in groupings_dict:
        q_kwargs = [
            {"p_group__" + groupings_dict[input_type] + "__iexact": element}
            for element in input_set
        ]

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
    genomic_modality = query_params["genomic_modality"]

    groupings_dict = {"organ": "grouping_name", "cluster": "grouping_name"}

    if input_type in ["protein", "gene"]:

        split_conditions = [[item, '>', '0'] if len(split_at_comparator(item)) == 0 else split_at_comparator(item) for item in input_set]

        qs = [process_single_condition(condition, input_type) for condition in split_conditions]
        q = combine_qs(qs, "or")

        return q

    elif input_type in groupings_dict:

        q_kwargs = [{groupings_dict[input_type] + "__iexact": element} for element in input_set]
        qs = [Q(**kwargs) for kwargs in q_kwargs]
        q = combine_qs(qs, "or")

        # Query groupings and then union their cells fields
        cell_ids = []

        if input_type == "organ":
            for organ in Organ.objects.filter(q):
                cell_ids.extend([cell.cell_id for cell in organ.cells.all()])

        elif input_type == "cluster":
            for cluster in Cluster.objects.filter(q):
                cell_ids.extend([cell.cell_id for cell in cluster.cells.all()])

        qs = [Q(cell_id__icontains=cell_id) for cell_id in cell_ids]
        q = combine_qs(qs, "or")

        return q


def get_organ_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for group objects based on the input set, input type, and logical operator
    Currently services membership queries where input type is cells
    and categorical queries where input type is genes"""

    input_type = query_params["input_type"]
    input_set = query_params["input_set"]
    logical_operator = query_params["logical_operator"]

    if input_type == "cell":

        qs = [Q(cell_id__iexact=item) for item in input_set]
        q = combine_qs(qs, "or")

        organ_names = [
            cell.organ.grouping_name
            for cell in Cell.objects.filter(q)
            if cell is not None and cell.organ is not None
        ]

        qs = [
            Q(grouping_name__icontains=organ_name)
            for organ_name in organ_names
            if organ_name is not None
        ]
        q = combine_qs(qs, logical_operator)

        return q

    elif input_type == "gene":
        # Query those genes and return their associated groupings
        p_value = query_params["p_value"]

        qs = [Q(p_gene__gene_symbol__iexact=item) for item in input_set]
        q = combine_qs(qs, "or")
        q = q & Q(value__lte=p_value)

        return q


# Put fork here depending on whether or not we're returning pvals


def get_genes_list(query_params: Dict):
    if query_params["input_type"] is None:
        return Gene.objects.all()
    else:
        query_params = process_query_parameters(query_params)
        limit = int(query_params["limit"])
        filter = get_gene_filter(query_params)
        print(filter)

        if query_params["input_type"] == "organ":
            query_set = PVal.objects.filter(filter).order_by("value")[:limit]
            ids = query_set.values_list("pk", flat=True)
            query_set = PVal.objects.filter(pk__in=list([ids]))

            genes_and_values = make_gene_and_values(query_set, query_params)
            return genes_and_values

def cache_values(query_set, gene_ids, modality):
    cell_ids = query_set.values_list('cell_id', flat=True)
    filter = Q(q_var_id__in=gene_ids) & Q(q_cell_id__in=cell_ids)
    if modality == 'rna':
        query_set = RnaQuant.objects.filter(filter)
    elif modality == 'atac':
        query_set = AtacQuant.objects.filter(filter)

    values = query_set.values_list('q_cell_id', 'q_var_id', 'value')
    print('Values gotten')

    values_dict = {triple[0] + triple[1]: triple[2] for triple in values}

    cache.set_many(values_dict, 300)

def get_quant_queryset(query_params:Dict, filter):

    zeroes = [item[2] == 0 for item in query_params['input_set']]

    if False:
        #            if all(zeroes):
        query_sets = [get_zero_cells(gene[0], genomic_modality) for gene in query_params['input_set']]

    else:

        if query_params['input_type'] == 'protein':
            query_set = CodexQuant.objects.filter(filter)
        elif query_params['genomic_modality'] == 'rna':
            query_set = RnaQuant.objects.filter(filter)
        elif query_params['genomic_modality'] == 'rna':
            query_set = AtacQuant.objects.filter(filter)

        var_ids = [split_at_comparator(item)[0] if len(split_at_comparator(item)) > 0 else item for item in
                   query_params['input_set']]

        query_sets = [cells_from_quants(query_set.filter(q_var_id=var), var) for var in
                      var_ids]

    if query_params['logical_operator'] == 'and':
        query_set = reduce(set_intersection, query_sets)
    elif query_params['logical_operator'] == 'or':
        query_set = reduce(set_union, query_sets)
        if len(var_ids) > 1:
            cache_values(query_set, var_ids, genomic_modality)

    query_set = order_cell_set(query_set, var_ids[0], limit)

    return query_set

# Put fork here depending on whether or not we're returning expression values
def get_cells_list(query_params: Dict):
    if query_params["input_type"] is None:
        return Cell.objects.all()
    else:
        query_params = process_query_parameters(query_params)
        limit = int(query_params["limit"])
        filter = get_cell_filter(query_params)
        print("Filter made")

        if query_params['input_type'] in ['gene', 'protein']:
            query_set = get_quant_queryset(query_params, filter)

        else:
            query_set = Cell.objects.filter(filter)[:limit]
            ids = query_set.values_list("pk", flat=True)
            query_set = Cell.objects.filter(pk__in=list(ids))

        print("Quant queryset gotten")
        cells_and_values = make_cell_and_values(query_set, query_params)

        return cells_and_values


# Put fork here depending on whether or not we're returning pvals
def get_organs_list(query_params: Dict):
    if query_params.get("input_type") is None:
        return Organ.objects.all().distinct("grouping_name")
    else:
        query_params = process_query_parameters(query_params)
        filter = get_organ_filter(query_params)
        limit = int(query_params["limit"])

        if query_params["input_type"] == "gene":
            query_set = PVal.objects.filter(filter).order_by("value")
        else:
            query_set = Organ.objects.filter(filter)[:limit]
            ids = query_set.values_list("pk", flat=True)
            query_set = Organ.objects.filter(pk__in=list(ids))

        organs_and_values = make_organ_and_values(query_set, query_params)
        return organs_and_values


def get_proteins_list(query_params: Dict):
    if query_params.get("input_type") is None:
        return Protein.objects.all()


def gene_query(self, request):
    if request.method == "GET":
        genes = Gene.objects.all()

    elif request.method == "POST":
        query_params = request.data.dict()
        genes = get_genes_list(query_params)

    self.queryset = genes
    # Set context
    context = {
        "request": request,
    }
    #    print(genes)
    #    print(GeneSerializer(genes, many=True, context=context))
    # Get serializers lists

    response = GeneAndValuesSerializer(genes, many=True, context=context).data

    return response


def cell_query(self, request):
    if request.method == "GET":
        cells = Cell.objects.all()

    elif request.method == "POST":
        query_params = request.data.dict()
        print(query_params)
        cells = get_cells_list(query_params)

    self.queryset = cells
    # Set context
    context = {
        "request": request,
    }
    #    print(cells)
    #    print(CellSerializer(cells, many=True, context=context))
    # Get serializers lists
    response = CellAndValuesSerializer(cells, many=True, context=context).data

    return response


def organ_query(self, request):
    if request.method == "GET":
        organs = Organ.objects.all().distinct("grouping_name")

    elif request.method == "POST":
        query_params = request.data.dict()
        print(query_params)
        organs = get_organs_list(query_params)

    self.queryset = organs
    # Set context
    context = {
        "request": request,
    }
    #    print(groups)
    #    print(CellGroupingSerializer(groups, many=True, context=context))
    # Get serializers lists

    response = OrganAndValuesSerializer(organs, many=True, context=context).data

    return response


def protein_query(self, request):
    if request.method == "GET":
        proteins = Protein.objects.all()
        self.queryset = proteins
        # Set context
        context = {
            "request": request,
        }
        #        print(proteins)
        #        print(ProteinSerializer(proteins, many=True, context=context))
        # Get serializers lists
        response = ProteinSerializer(proteins, many=True, context=context).data
        return response


def set_intersection(query_set_1, query_set_2):
    return query_set_1 & query_set_2


def set_union(query_set_1, query_set_2):
    return query_set_1 | query_set_2


def make_cell_and_values(query_set, request_dict):
    """Takes a query set of quant objects and returns a query set of cell_and_values
    This function will almost definitely have problems with concurrency"""

    CellAndValues.objects.all().delete()

    print("Making cells and values")

    print(query_set.count())

    genomic_modality = request_dict['genomic_modality']

    for cell in query_set:

        if request_dict['input_type'] in ['gene', 'protein']:

            var_ids = [split_at_comparator(item)[0].strip() if len(split_at_comparator(item)) > 0 else item.strip() for item in request_dict['input_set']]
            cell_ids = query_set.values_list('cell_id', flat=True)
            id_pairs = [cell_id + gene_id for cell_id in cell_ids for gene_id in var_ids]
            values_dict = cache.get_many(id_pairs)

            print('Values loaded from cache')
            if len(values_dict) > 0:
                values = {
                    var_id: values_dict[
                        cell.cell_id + var_id] if cell.cell_id + var_id in values_dict.keys() else 0.0
                    for var_id in var_ids}
            else:
                if request_dict['input_type'] == 'protein':
                    values = {
                        var_id: CodexQuant.objects.filter(q_var_id=var_id).filter(
                            q_cell_id=cell.cell_id).first().value if CodexQuant.objects.filter(q_var_id=var_id).filter(
                            q_cell_id=cell.cell_id).first() is not None else 0.0
                        for var_id in var_ids}

                elif genomic_modality == 'rna':
                    values = {
                        var_id: RnaQuant.objects.filter(q_var_id=var_id).filter(
                            q_cell_id=cell.cell_id).first().value if RnaQuant.objects.filter(q_var_id=var_id).filter(
                            q_cell_id=cell.cell_id).first() is not None else 0.0
                        for var_id in var_ids}

                elif genomic_modality == 'atac':
                    values = {
                        var_id: AtacQuant.objects.filter(q_var_id=var_id).filter(
                            q_cell_id=cell.cell_id).first().value if AtacQuant.objects.filter(q_var_id=var_id).filter(
                            q_cell_id=cell.cell_id).first() is not None else 0.0
                        for var_id in var_ids}

        else:
            values = {}

        kwargs = {'cell_id': cell.cell_id, 'dataset': cell.dataset, 'modality': cell.modality,
                  'organ': cell.organ, 'values': values}

        cav = CellAndValues(**kwargs)
        cav.save()

    print('Values gotten')

    qs = CellAndValues.objects.all()

    return qs


def make_gene_and_values(query_set, request_dict):
    GeneAndValues.objects.all().delete()
    # Filter on timestamp

    limit = int(request_dict["limit"])

    if request_dict["logical_operator"] == "and" and len(request_dict["input_set"]) > 1:
        # Get or more sets and intersect them
        groups = query_set.values("p_group").distinct()
        query_sets = [
            genes_from_pvals(query_set.filter(p_group=group["p_group"])) for group in groups
        ]
        query_set = reduce(set_intersection, query_sets)

    for gene in query_set[:limit]:
        if isinstance(gene, PVal):
            gene = gene.p_gene
        print(gene)
        values = {}

        if request_dict['input_type'] in ['organ', 'cluster', 'dataset']:
            for group_id in request_dict['input_set']:
                pval = PVal.objects.filter(p_group__grouping_name=group_id).filter(
                    p_gene=gene).first()
                if pval is not None:
                    values[group_id] = pval.value

        kwargs = {'gene_symbol': gene.gene_symbol, 'values': values}

        gav = GeneAndValues(**kwargs)
        gav.save()

    # Filter on query hash
    return GeneAndValues.objects.all()


def make_organ_and_values(query_set, request_dict):
    OrganAndValues.objects.all().delete()

    limit = int(request_dict["limit"])

    if request_dict["input_type"] == "gene":
        if request_dict["logical_operator"] == "and" and len(request_dict["input_set"]) > 1:
            genes = query_set.values("p_gene").distinct()
            query_sets = [
                organs_from_pvals(query_set.filter(p_gene=gene["p_gene"])) for gene in genes
            ]
            query_set = reduce(set_intersection, query_sets)

    for organ in query_set[:limit]:

        if isinstance(organ, PVal):
            organ = organ.p_group

        values = {}
        if request_dict["input_type"] == "gene":
            for gene_id in request_dict["input_set"]:
                gene_id = gene_id.strip()

                pval = (
                    PVal.objects.filter(p_group=organ)
                    .filter(p_gene__gene_symbol__iexact=gene_id)
                    .first()
                )
                if pval is not None:
                    values[gene_id] = pval.value

        kwargs = {"grouping_name": organ.grouping_name, "values": values}
        oav = OrganAndValues(**kwargs)
        oav.save()

    # Filter on query hash
    return OrganAndValues.objects.all()
