from django.db.models import Q

from .models import (
    Cell,
    Cell_Grouping,
    Gene,
#    Protein,
    RNA_Quant,
    ATAC_Quant,
)

from .serializers import (
    CellSerializer,
    Cell_GroupingSerializer,
    GeneSerializer,
#    ProteinSerializer,
)

def split_at_comparator(item:str)->List:
    comparator_list = ['<=', '>=', '>', '<', '==', '!=']
    for comparator in comparator_list:
        if comparator in item:
            item_split = item.split(comparator)
            item_split[1] = comparator_dict[item_split[1]]
            return item_split
    print('No comparator found')
    return None

def process_single_condition(split_condition:List, input_type:str)->Q:

    comparator = split_condition[1]
    value = int(split_condition[2])

    if input_type == 'protein':
        protein_id = split_condition[0]

        if comparator == '>':
            kwargs = ['protein_mean__' + protein_id + '__gt': value]
        elif comparator == '>=':
            kwargs = ['protein_mean__' + protein_id + '__gte': value]
        elif comparator == '<':
            kwargs = ['protein_mean__' + protein_id + '__lt': value]
        elif comparator == '<=':
            kwargs = ['protein_mean__' + protein_id + '__lte': value]
        elif comparator == '==':
            kwargs = ['protein_mean__' + protein_id + '__exact': value]
        elif comparator == '!=':
            kwargs = ['protein_mean__' + protein_id + '__exact': value]
            return (~Q(kwargs))

        return Q(kwargs)

    if input_type in ['rna_gene', 'atac_gene']:
        gene_id = split_condition[0]

        if comparator == '>':
            return Q(value__gt=value & Q(gene_id__icontains=gene_id)
        elif comparator == '>=':
            return Q(value__gte=value) & Q(gene_id__icontains=gene_id)
        elif comparator == '<':
            return Q(value__lt=value) & Q(gene_id__icontains=gene_id)
        elif comparator == '<=':
            return Q(value__lte=value) & Q(gene_id__icontains=gene_id)
        elif comparator == '==':
            return Q(value__exact=value) & Q(gene_id__icontains=gene_id)
        elif comparator == '!=':
            return (~Q(value__exact=value) & Q(gene_id__icontains=gene_id))

def get_gene_filter(input_type, input_set, logical_operator):
    if input_type in ['tissue_type', 'cluster']:
        #Query groupings first and then union their marker genes
        pass

def get_cell_filter(input_type, input_set, logical_operator):
    if input_type == 'protein':

        if split_at_comparator(input_set[0]) is None:
            split_conditions = [[item, '>', '0'] for item in input_set]
        else:
            split_conditions = [split_at_comparator(item) for item in input_set]

        q = process_single_condition(split_conditions[0], input_type)
        for condition in split_conditions[1:]:
            q = q & process_single_condition(condition)

        return q

    elif input_type in ['atac_gene', 'rna_gene']:
        #Query quants first and then use those cell_ids to get cells

    elif input_type in ['tissue_type', 'cluster']:
        #Query groupings and then union their cells fields

def get_group_filter(input_type, input_set, logical_operator):
    if input_type == 'cell':
        pass
    elif input_type in ['atac_gene', 'rna_gene']:
        #Query those genes and return their associated groupings
        pass

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
    groups = get_groups_list(input_type, input_set, logical_operator)
    self.queryset = group
    # Set context
    context = {
        "request": request,
    }
    print(groups)
    print(Cell_GroupingSerializer(groups, many=True, context=context))
    # Get serializers lists
    response = Cell_GroupingSerializer(groups, many=True, context=context).data
    return response
