import json
import traceback
from typing import Callable

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .analysis import calc_stats
from .models import (
    Cell,
    CellAndValues,
    Cluster,
    ClusterAndValues,
    Dataset,
    DatasetAndValues,
    Gene,
    GeneAndValues,
    Organ,
    OrganAndValues,
    Protein,
    QuerySet,
    StatReport,
)
from .queries import (
    cell_query,
    cluster_query,
    dataset_query,
    gene_query,
    organ_query,
    protein_query,
)
from .serializers import (
    CellAndValuesSerializer,
    CellSerializer,
    ClusterAndValuesSerializer,
    ClusterSerializer,
    DatasetAndValuesSerializer,
    DatasetSerializer,
    GeneAndValuesSerializer,
    GeneSerializer,
    OrganAndValuesSerializer,
    OrganSerializer,
    ProteinSerializer,
    QuerySetCountSerializer,
    QuerySetSerializer,
    StatReportSerializer,
)
from .set_evaluators import (
    cell_evaluation_detail,
    cluster_evaluation_detail,
    dataset_evaluation_detail,
    evaluation_list,
    gene_evaluation_detail,
    organ_evaluation_detail,
    query_set_count,
)
from .set_operators import query_set_difference, query_set_intersection, query_set_union


class PaginationClass(PageNumberPagination):
    page_size = 100000
    max_page_size = 100000


def get_response(self, request, callable: Callable):
    try:
        response = callable(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response
    except Exception as e:
        tb = traceback.format_exc()
        json_error_response = json.dumps({"error": {"stack_trace": tb}, "message": str(e)})
        print(json_error_response)
        return HttpResponse(json_error_response)


class CellViewSet(viewsets.ModelViewSet):
    query_set = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass
    model = QuerySet

    def get(self, request, format=None):
        return get_response(self, request, cell_query)

    def post(self, request, format=None):
        return get_response(self, request, cell_query)


class OrganViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass
    model = QuerySet

    def get(self, request, format=None):
        return get_response(self, request, organ_query)

    def post(self, request, format=None):
        return get_response(self, request, organ_query)


class GeneViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass
    model = QuerySet

    def get(self, request, format=None):
        return get_response(self, request, gene_query)

    def post(self, request, format=None):
        return get_response(self, request, gene_query)


class ProteinViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass

    def get(self, request, format=None):
        return get_response(self, request, protein_query)

    def post(self, request, format=None):
        return get_response(self, request, protein_query)


class ClusterViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass
    model = QuerySet

    def get(self, request, format=None):
        return get_response(self, request, cluster_query)

    def post(self, request, format=None):
        return get_response(self, request, cluster_query)


class DatasetViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass
    model = QuerySet

    def get(self, request, format=None):
        return get_response(self, request, dataset_query)

    def post(self, request, format=None):
        return get_response(self, request, dataset_query)


class CellDetailEvaluationViewSet(viewsets.ModelViewSet):
    query_set = CellAndValues.objects.all()
    serializer_class = CellAndValuesSerializer
    pagination_class = PaginationClass
    model = CellAndValues

    def post(self, request, format=None):
        return get_response(self, request, cell_evaluation_detail)


class OrganDetailEvaluationViewSet(viewsets.ModelViewSet):
    queryset = OrganAndValues.objects.all()
    serializer_class = OrganAndValuesSerializer
    model = OrganAndValues
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, organ_evaluation_detail)


class GeneDetailEvaluationViewSet(viewsets.ModelViewSet):
    queryset = GeneAndValues.objects.all()
    serializer_class = GeneAndValuesSerializer
    pagination_class = PaginationClass
    model = GeneAndValues

    def post(self, request, format=None):
        return get_response(self, request, gene_evaluation_detail)


class ClusterDetailEvaluationViewSet(viewsets.ModelViewSet):
    queryset = ClusterAndValues.objects.all()
    serializer_class = ClusterAndValuesSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, cluster_evaluation_detail)


class DatasetDetailEvaluationViewSet(viewsets.ModelViewSet):
    queryset = DatasetAndValues.objects.all()
    serializer_class = DatasetAndValuesSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, dataset_evaluation_detail)


class CellListEvaluationViewSet(viewsets.ModelViewSet):
    query_set = Cell.objects.all()
    serializer_class = CellSerializer
    pagination_class = PaginationClass
    model = Cell

    def post(self, request, format=None):
        return get_response(self, request, evaluation_list)


class OrganListEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Organ.objects.all()
    serializer_class = OrganSerializer
    pagination_class = PaginationClass
    model = Organ

    def post(self, request, format=None):
        return get_response(self, request, evaluation_list)


class GeneListEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Gene.objects.all()
    serializer_class = GeneSerializer
    pagination_class = PaginationClass
    model = Gene

    def post(self, request, format=None):
        return get_response(self, request, evaluation_list)


class ClusterListEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, evaluation_list)


class DatasetListEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, evaluation_list)


class ProteinListEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Protein.objects.all()
    serializer_class = ProteinSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, evaluation_list)


class SetIntersectionViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, query_set_intersection)


class SetUnionViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, query_set_union)


class SetDifferenceViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, query_set_difference)


class SetCountViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetCountSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        print(request.method)
        return get_response(self, request, query_set_count)


class StatisticViewSet(viewsets.ModelViewSet):
    queryset = StatReport
    serializer_class = StatReportSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, calc_stats)
