from django.db.models import Q
from typing import List, Dict
from functools import reduce

from .models import (
    Cell,
    CellAndValues,
    Gene,
    Organ,
    Protein,
    PVal,
    Quant,
)

from .serializers import (
    CellSerializer,
    CellAndValuesSerializer,
    DatasetSerializer,
    GeneSerializer,
    ModalitySerializer,
    OrganSerializer,
    ProteinSerializer,
    GenePValSerializer,
    OrganPValSerializer,
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
    if 'limit' not in query_params.keys() or int(query_params['limit']) > 1000:
        query_params['limit'] = 1000
    if 'p_value' not in query_params.keys() or query_params['p_value'] == '' or float(
            query_params['p_value']) < 0.0 or float(
            query_params['p_value']) > 1.0:
        query_params['p_value'] = 0.05
    else:
        query_params['p_value'] = float(query_params['p_value'])

    return query_params


def process_input_set(input_set: List, input_type: str):
    """If the input set is output of a previous query, finds the relevant values from the serialized data"""
    type_dict = {'gene': 'gene_symbol', 'cell': 'cell_id', 'organ': 'organ_name', 'protein': 'protein_id'}
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

    if input_type == 'gene':
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
    p_value = query_params['p_value']

    if input_type == 'organ':
        qs = [Q(organ_name__icontains=element) for element in input_set]
        q = combine_qs(qs, 'or')
        q = q & Q(value__lte=p_value)

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

    if input_type in ['protein', 'gene']:

        if len(split_at_comparator(input_set[0])) == 0:
            print(len(split_at_comparator(input_set[0])))
            split_conditions = [[item, '>', '0'] for item in input_set]
        else:
            split_conditions = [split_at_comparator(item) for item in input_set]

        qs = [process_single_condition(condition, input_type) for condition in split_conditions]
        q = combine_qs(qs, logical_operator)

        if input_type == 'gene':
            q = q & Q(modality__modality_name__icontains=genomic_modality)

        return q

    elif input_type == 'organ':

        qs = [Q(organ_name__icontains=element) for element in input_set]
        q = combine_qs(qs, 'or')  # These categories are mutually exclusive, so their intersection will be empty

        # Query groupings and then union their cells fields
        cell_ids = []

        for organ in Organ.objects.filter(q):
            cell_ids.extend([cell.cell_id for cell in organ.cells.all()])

        qs = [Q(cell_id__icontains=cell_id) for cell_id in cell_ids]
        q = combine_qs(qs, 'or')

        return q


def get_organ_filter(query_params: Dict) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for group objects based on the input set, input type, and logical operator
    Currently services membership queries where input type is cells
    and categorical queries where input type is genes"""

    input_type = query_params['input_type']
    input_set = query_params['input_set']
    logical_operator = query_params['logical_operator']

    if input_type == 'cell':

        qs = [Q(cell_id__icontains=item) for item in input_set]
        q = combine_qs(qs, 'or')

        organ_names = [cell.organ.organ_name for cell in Cell.objects.filter(q) if
                       cell is not None and cell.organ is not None]

        qs = [Q(organ_name__icontains=organ_name) for organ_name in organ_names if organ_name is not None]
        q = combine_qs(qs, logical_operator)

        return q

    elif input_type == 'gene':
        # Query those genes and return their associated groupings
        p_value = query_params['p_value']

        qs = [Q(gene_id__icontains=item) for item in input_set]
        q = combine_qs(qs, 'or')
        q = q & Q(value__lte=p_value)

        return q


# Put fork here depending on whether or not we're returning pvals

def get_genes_list(query_params: Dict):
    if query_params['input_type'] is None:
        return Gene.objects.all()
    else:
        query_params = process_query_parameters(query_params)
        limit = int(query_params['limit'])
        filter = get_gene_filter(query_params)

        if query_params['input_type'] == 'organ':
            ids = PVal.objects.filter(filter).order_by('value')[:limit].values_list('pk', flat=True)
            return PVal.objects.filter(pk__in=list(ids))
        else:
            ids = Gene.objects.filter(filter)[:limit].values_list('pk', flat=True)
            return Gene.objects.filter(pk__in=list(ids))


# Put fork here depending on whether or not we're returning expression values
def get_cells_list(query_params: Dict):
    if query_params['input_type'] is None:
        return Cell.objects.all()
    else:
        query_params = process_query_parameters(query_params)
        limit = int(query_params['limit'])
        filter = get_cell_filter(query_params)
        if query_params['input_type'] == 'gene':
            ids = Quant.objects.filter(filter).order_by('-value')[:limit].values_list('pk', flat=True)
            quants = Quant.objects.filter(pk__in=list(ids))
            cells_and_values = make_cell_and_values(quants)

            return cells_and_values
        else:
            ids = Cell.objects.filter(filter)[:limit].values_list('pk', flat=True)
            return Cell.objects.filter(pk__in=list(ids))


# Put fork here depending on whether or not we're returning pvals
def get_organs_list(query_params: Dict):
    if query_params.get('input_type') is None:
        return Organ.objects.all()
    else:
        query_params = process_query_parameters(query_params)
        filter = get_organ_filter(query_params)
        limit = int(query_params['limit'])
        if query_params['input_type'] == 'gene':
            ids = PVal.objects.filter(filter).order_by('value')[:limit].values_list('pk', flat=True)
            return PVal.objects.filter(pk__in=list(ids))
        else:
            ids = Organ.objects.filter(filter)[:limit].values_list('pk', flat=True)
            return Organ.objects.filter(pk__in=list(ids))


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
    if query_params['input_type'] == 'organ':
        response = GenePValSerializer(genes, many=True, context=context).data
    else:
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
    if query_params['input_type'] == 'gene':
        cells_and_values = make_cell_and_values(cells)
        response = CellAndValuesSerializer(cells_and_values, many=True, context=context).data
    else:
        response = CellSerializer(cells, many=True, context=context).data

    return response


def organ_query(self, request):
    if request.method == 'GET':
        organs = Organ.objects.all()

    elif request.method == 'POST':
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
    if query_params['input_type'] == 'gene':
        response = OrganPValSerializer(organs, many=True, context=context).data
    else:
        response = OrganSerializer(organs, many=True, context=context).data

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


def make_cell_and_values(quant_query_set):
    """Takes a query set of quant objects and returns a query set of cell_and_values
    This function will almost definitely have problems with concurrency"""

    CellAndValues.objects.all().delete()

    cell_ids = quant_query_set.distinct('cell_id').values_list('cell_id', flat=True)
    for cell_id in cell_ids:
        gene_ids_and_values = quant_query_set.filter(cell_id__icontains=cell_id).values_list('gene_id', 'value')
        values = {giv[0]: float(giv[1]) for giv in gene_ids_and_values}
        cell = Cell.objects.filter(cell_id__icontains=cell_id).first()
        kwargs = {'cell_id':cell.cell_id, 'dataset':cell.dataset, 'modality':cell.modality,
                       'organ':cell.organ, 'values':values}
        cav = CellAndValues(**kwargs)
        cav.save()

    return CellAndValues.objects.all()
