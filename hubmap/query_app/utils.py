from django.db.models import Q
from typing import List, Dict
from functools import reduce

from .models import (
    Cell,
    CellGrouping,
    Gene,
    Protein,
    Quant,
)

from .serializers import (
    CellSerializer,
    CellGroupingSerializer,
    GeneSerializer,
    ProteinSerializer,
)


def split_and_strip(string: str) -> List[str]:
    set_split = string.split(',')
    set_strip = [element.strip() for element in set_split]
    return set_strip


def process_query_parameters(query_params: Dict) -> Dict:
    if isinstance(query_params['input_set'], str):
        query_params['input_set'] = split_and_strip(query_params['input_set'])
    query_params['input_set'] = process_input_set(query_params['input_set'], query_params['input_type'])
    query_params['input_type'] = query_params['input_type'].lower()
    if query_params['input_type'] == 'organ':
        query_params['input_type'] = 'tissue_type'
    if 'limit' not in query_params.keys() or query_params['limit'] > 1000:
        query_params['limit'] = 1000

    return query_params


def process_input_set(input_set: List, input_type: str):
    """If the input set is output of a previous query, finds the relevant values from the serialized data"""
    type_dict = {'gene': 'gene_symbol', 'cell': 'cell_id', 'organ': 'group_id', 'protein': 'protein_id'}
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

    comparator_list = ['<=', '>=', '>', '<', '==', '!=']
    for comparator in comparator_list:
        if comparator in item:
            item_split = item.split(comparator)
            item_split.insert(1, comparator)
            return item_split
    print('No comparator found')
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
    if logical_operator == 'or':
        return reduce(q_or, qs)
    elif logical_operator == 'and':
        return reduce(q_and, qs)


def process_single_condition(split_condition: List[str], input_type: str) -> Q:
    """List[str], str -> Q
    Finds the keyword args for a quantitative query based on the results of
    calling split_at_comparator() on a string representation of that condition"""
    comparator = split_condition[1]

    assert comparator in ['>', '>=', '<=', '<', '==', '!=']
    value = float(split_condition[2].strip())

    if input_type == 'protein':
        protein_id = split_condition[0].strip()

        if comparator == '>':
            kwargs = {'protein_mean__' + protein_id + '__gt': value}
        elif comparator == '>=':
            kwargs = {'protein_mean__' + protein_id + '__gte': value}
        elif comparator == '<':
            kwargs = {'protein_mean__' + protein_id + '__lt': value}
        elif comparator == '<=':
            kwargs = {'protein_mean__' + protein_id + '__lte': value}
        elif comparator == '==':
            kwargs = {'protein_mean__' + protein_id + '__exact': value}
        elif comparator == '!=':
            kwargs = {'protein_mean__' + protein_id + '__exact': value}
            return ~Q(kwargs)

        return Q(**kwargs)

    if input_type in ['rna_gene', 'atac_gene']:
        gene_id = split_condition[0].strip()

        if comparator == '>':
            return Q(value__gt=value) & Q(gene_id__icontains=gene_id)
        elif comparator == '>=':
            return Q(value__gte=value) & Q(gene_id__icontains=gene_id)
        elif comparator == '<':
            return Q(value__lt=value) & Q(gene_id__icontains=gene_id)
        elif comparator == '<=':
            return Q(value__lte=value) & Q(gene_id__icontains=gene_id)
        elif comparator == '==':
            return Q(value__exact=value) & Q(gene_id__icontains=gene_id)
        elif comparator == '!=':
            return ~Q(value__exact=value) & Q(gene_id__icontains=gene_id)


def get_gene_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for gene objects based on the input set, input type, and logical operator
    Currently only services categorical queries where input type is tissue_type or dataset"""

    input_type = query_params['input_type']
    input_set = query_params['input_set']
    marker = query_params['marker']

    if input_type in ['tissue_type', 'cluster']:
        gene_ids = []
        q = Q(group_type__icontains=input_type)
        qs = [Q(group_id__icontains=element) for element in input_set]
        q2 = combine_qs(qs, 'or')
        q = q & q2

        if marker == 'True':
            for group in CellGrouping.objects.filter(q):
                gene_ids.extend(group.marker_genes.values_list('gene_symbol'))
        else:
            for group in CellGrouping.objects.filter(q):
                gene_ids.extend(group.genes.values_list('gene_symbol'))

        gene_ids = [gene_id[0] for gene_id in gene_ids]

        qs = [Q(gene_symbol__icontains=gene_id) for gene_id in gene_ids]
        q = combine_qs(qs, 'or')

        return q


def get_cell_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for cell objects based on the input set, input type, and logical operator
    Currently services quantitative queries where input is protein, atac_gene, or rna_gene
    and membership queries where input is tissue_type"""

    input_type = query_params['input_type']
    input_set = query_params['input_set']
    logical_operator = query_params['logical_operator']
    genomic_modality = query_params['genomic_modality']

    if input_type in ['protein', 'atac_gene', 'rna_gene']:

        if len(split_at_comparator(input_set[0])) == 0:
            print(len(split_at_comparator(input_set[0])))
            split_conditions = [[item, '>', '0'] for item in input_set]
        else:
            split_conditions = [split_at_comparator(item) for item in input_set]

        qs = [process_single_condition(condition, input_type) for condition in split_conditions]
        q = combine_qs(qs, logical_operator)

        if input_type == 'gene':

            q = q & Q(modality__icontains=genomic_modality)
            cell_ids = [item[0] for item in Quant.objects.filter(q).order_by('value').values_list('cell_id')]

            qs = [Q(cell_id__icontains=cell_id) for cell_id in cell_ids]
            q = combine_qs(qs, 'or')

        return q

    elif input_type in ['tissue_type', 'cluster']:

        q = Q(group_type__icontains=input_type)
        qs = [Q(group_id__icontains=element) for element in input_set]
        q2 = combine_qs(qs, 'or')  # These categories are mutually exclusive, so their intersection will be empty
        q = q & q2

        # Query groupings and then union their cells fields
        cell_ids = []
        for group in CellGrouping.objects.filter(q):
            cell_ids.extend(group.cells.values_list('cell_id'))

        cell_ids = [cell_id[0] for cell_id in cell_ids]

        qs = [Q(cell_id__icontains=cell_id) for cell_id in cell_ids]
        q = combine_qs(qs, 'or')

        return q


def get_group_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for group objects based on the input set, input type, and logical operator
    Currently services membership queries where input type is cells
    and categorical queries where input type is genes"""

    input_type = query_params['input_type']
    input_set = query_params['input_set']
    logical_operator = query_params['logical_operator']
    marker = query_params['marker']

    if input_type == 'cell':
        group_ids = []

        qs = [Q(cell_id__icontains=item) for item in input_set]
        q = combine_qs(qs, 'or')

        for cell in Cell.objects.filter(q):
            group_ids.extend(cell.groupings.values_list('group_id'))

        group_ids = [group_id[0] for group_id in group_ids]

        qs = [Q(group_id__icontains=group_id) for group_id in group_ids]
        q = combine_qs(qs, logical_operator)

        return q

    elif input_type in ['atac_gene', 'rna_gene']:
        # Query those genes and return their associated groupings
        group_ids = []

        qs = [Q(gene_symbol__icontains=item) for item in input_set]
        q = combine_qs(qs, 'or')

        if marker == 'True':
            for gene in Gene.objects.filter(q):
                group_ids.extend(gene.marker_groups.values_list('group_id'))

        else:
            for gene in Gene.objects.filter(q):
                group_ids.extend(gene.groups.values_list('group_id'))

        group_ids = [group_id[0] for group_id in group_ids]

        qs = [Q(group_id__icontains=group_id) for group_id in group_ids]
        q = combine_qs(qs, 'or')

        return q


def get_genes_list(query_params: Dict):
    if query_params['input_type'] is None:
        return Gene.objects.all()
    else:
        query_params = process_query_parameters(query_params)
        filter = get_gene_filter(query_params)
        return Gene.objects.filter(filter)


def get_cells_list(query_params: Dict):
    if query_params['input_type'] is None:
        return Cell.objects.all()
    else:
        query_params = process_query_parameters(query_params)
        filter = get_cell_filter(query_params)
        return Cell.objects.filter(filter)


def get_groupings_list(query_params: Dict):
    if query_params.get('input_type') is None:
        return CellGrouping.objects.filter(group_type__icontains='tissue_type')
    else:
        query_params = process_query_parameters(query_params)
        filter = get_group_filter(query_params)
        return CellGrouping.objects.filter(filter)

def get_proteins_list(query_params: Dict):
    if query_params.get('input_type') is None:
        return Protein.objects.all()

def gene_query(self, request):

    if request.method == 'GET':
        genes = Gene.objects.all()

    elif request.method == 'POST':
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
    response = GeneSerializer(genes, many=True, context=context).data
    return response


def cell_query(self, request):

    if request.method == 'GET':
        cells = Cell.objects.all()

    elif request.method == 'POST':
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
    response = CellSerializer(cells, many=True, context=context).data
    return response


def group_query(self, request):
    if request.method == 'GET':
        groups = CellGrouping.objects.filter(group_type__icontains='tissue_type')

    elif request.method == 'POST':
        query_params = request.data.dict()
        print(query_params)
        groups = get_groupings_list(query_params)

    self.queryset = groups
    # Set context
    context = {
        "request": request,
    }
#    print(groups)
#    print(CellGroupingSerializer(groups, many=True, context=context))
    # Get serializers lists
    response = CellGroupingSerializer(groups, many=True, context=context).data
    return response


def protein_query(self, request):

    if request.method == 'GET':
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
