import json
import traceback
from typing import Callable

from django.core import serializers
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .analysis import calculate_statistics, get_bounds
from .models import Cell, Cluster, Dataset, Gene, Organ, Protein, QuerySet, StatReport
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
from .set_evaluators import evaluation_detail, evaluation_list, query_set_count
from .set_operators import query_set_difference, query_set_intersection, query_set_union
from .utils import get_app_status, unpickle_query_set

JSONSerializer = serializers.get_serializer("json")
json_serializer = JSONSerializer()


class PaginationClass(PageNumberPagination):
    page_size = 100000
    max_page_size = 100000


def get_response(self, request, callable: Callable):
    try:
        response = callable(self, request)
        print(type(response))
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
    query_set = Cell.objects.all()
    serializer_class = CellAndValuesSerializer
    pagination_class = PaginationClass
    model = Cell

    def post(self, request, format=None):
        return get_response(self, request, evaluation_detail)


class OrganDetailEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Organ.objects.all()
    serializer_class = OrganAndValuesSerializer
    model = Organ
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, evaluation_detail)


class GeneDetailEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Gene.objects.all()
    serializer_class = GeneAndValuesSerializer
    pagination_class = PaginationClass
    model = Gene

    def post(self, request, format=None):
        return get_response(self, request, evaluation_detail)


class ClusterDetailEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Cluster.objects.all()
    serializer_class = ClusterAndValuesSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, evaluation_detail)


class DatasetDetailEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetAndValuesSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, evaluation_detail)


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
        return get_response(self, request, query_set_count)


class StatisticViewSet(viewsets.ModelViewSet):
    queryset = StatReport.objects.all()
    serializer_class = StatReportSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, calculate_statistics)


class StatusViewSet(viewsets.GenericViewSet):
    pagination_class = PaginationClass
    serializer_class = json_serializer

    def get(self, request, format=None):
        try:
            return HttpResponse(get_app_status())
        except Exception as e:
            tb = traceback.format_exc()
            json_error_response = json.dumps({"error": {"stack_trace": tb}, "message": str(e)})
            print(json_error_response)
            return HttpResponse(json_error_response)


class ValueBoundsViewSet(viewsets.GenericViewSet):
    pagination_class = PaginationClass
    serializer_class = json_serializer

    def post(self, request, format=None):
        try:
            bounds_dict = get_bounds(self, request)
            response = JsonResponse(bounds_dict)
            return response
        except Exception as e:
            tb = traceback.format_exc()
            json_error_response = json.dumps({"error": {"stack_trace": tb}, "message": str(e)})
            print(json_error_response)
            return HttpResponse(json_error_response)
