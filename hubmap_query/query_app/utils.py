from django.db.models import Q
from typing import List
from functools import reduce

from .models import (
    Cell,
    Cell_Grouping,
    Gene,
    # Protein,
    RNA_Quant,
    ATAC_Quant,
)

from .serializers import (
    CellSerializer,
    Cell_GroupingSerializer,
    GeneSerializer,
    #    ProteinSerializer,
)


def split_at_comparator(item: str) -> List:
    """str->List
    Splits a string representation of a quantitative comparison into its parts
    i.e. 'eg_protein>=50' -> ['eg_protein', '>=', '50']
    If there is no comparator in the string, returns an empty list"""

    comparator_list = ['<=', '>=', '>', '<', '==', '!=']
    for comparator in comparator_list:
        if comparator in item:
            item_split = item.split(comparator)
            item_split[1] = comparator
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
    value = int(split_condition[2])

    if input_type == 'protein':
        protein_id = split_condition[0]

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

        return Q(kwargs)

    if input_type in ['rna_gene', 'atac_gene']:
        gene_id = split_condition[0]

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


def get_gene_filter(input_type: str, input_set: List[str], logical_operator: str) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for gene objects based on the input set, input type, and logical operator
    Currently only services categorical queries where input type is tissue_type or dataset"""
    if input_type in ['tissue_type', 'cluster']:
        gene_ids = []
        q = Q(group_type__icontains=input_type)
        qs = [Q(group_id__icontains=element) for element in input_set]
        q2 = combine_qs(qs, 'or')
        q = q & q2

        for group in Cell_Grouping.objects.filter(q):
            gene_ids.extend(group.genes.values_list('gene_id'))

        qs = [Q(gene_id__icontains=gene_id) for gene_id in gene_ids]
        q = combine_qs(qs, 'or')

        return q


def get_cell_filter(input_type: str, input_set: List[str], logical_operator: str) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for cell objects based on the input set, input type, and logical operator
    Currently services quantitative queries where input is protein, atac_gene, or rna_gene
    and membership queries where input is tissue_type"""
    if input_type in ['protein', 'atac_gene', 'rna_gene']:

        if len(split_at_comparator(input_set[0])) == 0:
            split_conditions = [[item, '>', '0'] for item in input_set]
        else:
            split_conditions = [split_at_comparator(item) for item in input_set]

        qs = [process_single_condition(condition, input_type) for condition in split_conditions]
        q = combine_qs(qs, logical_operator)

        if input_type in ['atac_gene', 'rna_gene']:

            if input_type == 'atac_gene':
                cell_ids = ATAC_Quant.objects.filter(q).values_list('cell_id')
            elif input_type == 'rna_gene':
                cell_ids = RNA_Quant.objects.filter(q).values_list('cell_id')

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
        for group in Cell_Grouping.objects.filter(q):
            cell_ids.extend(group.cells.values_list('cell_id'))

        qs = [Q(cell_id__icontains=cell_id) for cell_id in cell_ids]
        q = combine_qs(qs, 'or')

        return q


def get_group_filter(input_type: str, input_set: List[str], logical_operator: str) -> Q:
    """str, List[str], str -> Q
    Finds the filter for a query for group objects based on the input set, input type, and logical operator
    Currently services membership queries where input type is cells
    and categorical queries where input type is genes"""
    if input_type == 'cell':
        group_ids = []

        qs = [Q(cell_id__icontains=item) for item in input_set]
        q = combine_qs(qs, 'or')

        for cell in Cell.objects.filter(q):
            group_ids.extend(cell.grouping.values_list('group_id'))

        qs = [Q(group_id__icontains=group_id) for group_id in group_ids]
        q = combine_qs(qs, logical_operator)

        return q

    elif input_type in ['atac_gene', 'rna_gene']:
        # Query those genes and return their associated groupings
        group_ids = []

        qs = [Q(gene_id__icontains=item) for item in input_set]
        q = combine_qs(qs, 'or')

        for gene in Gene.objects.filter(q):
            group_ids.extend(gene.grouping.values_list('group_id'))

        qs = [Q(group_id__icontains=group_id) for group_id in group_ids]
        q = combine_qs(qs, 'or')

        return q


def get_genes_list(input_type, input_set, logical_operator):
    if input_type is None:
        return Gene.objects.all()
    else:
        filter = get_gene_filter(input_type, input_set, logical_operator)
        return Gene.objects.filter(filter)


def get_cells_list(input_type, input_set, logical_operator):
    if input_type is None:
        return Cell.objects.all()
    else:
        filter = get_cell_filter(input_type, input_set, logical_operator)
        return Cell.objects.filter(filter)


def get_groupings_list(input_type, input_set, logical_operator):
    if input_type is None:
        return Cell_Grouping.objects.all()
    else:
        filter = get_group_filter(input_type, input_set, logical_operator)
        return Cell_Grouping.objects.filter(filter)


def gene_query(self, request):
    input_type = self.request.query_params.get('input_type', None)
    input_set = self.request.query_params.get('input_set', None)
    logical_operator = self.request.query_params.get('logical_operator', None)
    genes = get_genes_list(input_type, input_set, logical_operator)
    self.queryset = genes
    # Set context
    context = {
        "request": request,
    }
    print(genes)
    print(GeneSerializer(genes, many=True, context=context))
    # Get serializers lists
    response = GeneSerializer(genes, many=True, context=context).data
    return response


def cell_query(self, request):
    input_type = self.request.query_params.get('input_type', None)
    input_set = self.request.query_params.get('input_set', None)
    logical_operator = self.request.query_params.get('logical_operator', None)
    cells = get_cells_list(input_type, input_set, logical_operator)
    self.queryset = cells
    # Set context
    context = {
        "request": request,
    }
    print(cells)
    print(CellSerializer(cells, many=True, context=context))
    # Get serializers lists
    response = CellSerializer(cells, many=True, context=context).data
    return response


def group_query(self, request):
    input_type = self.request.query_params.get('input_type', None)
    input_set = self.request.query_params.get('input_set', None)
    logical_operator = self.request.query_params.get('logical_operator', None)
    groups = get_groupings_list(input_type, input_set, logical_operator)
    self.queryset = groups
    # Set context
    context = {
        "request": request,
    }
    print(groups)
    print(Cell_GroupingSerializer(groups, many=True, context=context))
    # Get serializers lists
    response = Cell_GroupingSerializer(groups, many=True, context=context).data
    return response
