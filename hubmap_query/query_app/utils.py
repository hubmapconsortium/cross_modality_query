from django.db.models import Q

from .models import (
    Cell,
    Cell_Grouping,
    Gene,
    Protein,
    RNA_Quant,
    ATAC_Quant,
)

from .serializers import (
    CellSerializer,
    Cell_GroupingSerializer,
    GeneSerializer,
    ProteinSerializer,
    ATAC_QuantSerializer,
    RNA_QuantSerializer,
)

def get_serializer_class(model):
    model = model.get_subclass_object()
    if isinstance(model, Cell):
        return CellSerializer
    elif isinstance(model, Cell_Grouping):
        return Cell_GroupingSerializer
    elif isinstance(model, Gene):
        return GeneSerializer
    elif isinstance(model, Protein):
        return ProteinSerializer
    elif isinstance(model, RNA_Quant):
        return RNA_QuantSerializer
    elif isinstance(model, ATAC_Quant):
        return ATAC_QuantSerializer

def split_at_comparator(item:str)->List:
    comparator_list = ['<=', '>=', '>', '<', '==', '!=']
    for comparator in comparator_list:
        if comparator in item:
            item_split = item.split(comparator)
            item_split[1] = comparator_dict[item_split[1]]
            return item_split
    print('No comparator found')
    return None

def process_single_condition(split_condition:List, input_type:str)->:

    comparator = split_condition[1]
    value = int(split_condition[2])

    if input_type == 'protein':
        pass

    if input_type in ['rna_gene', 'atac_gene']:
        id = split_condition[0]

        if comparator == '>':
            return Q(value__gt=int) & Q(gene_id__icontains=id)
        elif comparator == '>=':
            return Q(value__gte=int) & Q(gene_id__icontains=id)
        elif comparator == '<':
            return Q(value__lt=int) & Q(gene_id__icontains=id)
        elif comparator == '<=':
            return Q(value__lte=int) & Q(gene_id__icontains=id)
        elif comparator == '==':
            return Q(value__exact=int) & Q(gene_id__icontains=id)
        elif comparator == '!=':
            return (~Q(value__exact=int)) & Q(gene_id__icontains=id)

def get_quantitative_condition(input_set:List, input_type:str, logical_operator:str)->Q:

    split_conditions = [split_at_comparator(item) for item in input_set]

    q = process_single_condition(split_conditions[0], input_type)
    for condition in split_conditions[1:]:
        q = q & process_single_condition(condition)

    return q


def get_categorical_condition(input_set:List, input_type:str, logical_operator:str)->Q:

    grouping_types = Cell_Grouping.objects.distinct('grouping_type')
    g_types_list = [gtype for gtype in grouping_types]

    if input_type in grouping_types:
        if output_type in ['gene', 'marker_gene']:
            pass

    elif input_type in ['gene', 'marker_gene']:
        if output_type in grouping_types:
            pass

def categorical_query(input_type: str, input_set:List, logical_operator:str, output_type:str):

    values_list = [element[0] for element in input_set]
    condition = get_categorical_condition(values_list, input_type, logical_operator)

    if output_type in grouping_types:
        results = Cell_Grouping.objects.filter(condition)

    elif output_type in ['gene', 'marker_gene']:
        results = Gene.objects.filter(condition)

    return results

def quantitative_query(input_type: str, input_set:List, logical_operator:str, output_type:str):

    values_list = [element[0] for element in input_set]

    if output_type == 'cell':
        condition = get_quantitative_condition(values_list, input_type, logical_operator)
        if input_type == 'protein':
            results = Cell.objects.filter(condition)
        elif input_type == 'rna_gene':
            results = RNA_Quant.objects.filter(condition)
        elif input_type == 'atac_gene':
            results = ATAC_Quant.objects.filter(condition)
        return results
