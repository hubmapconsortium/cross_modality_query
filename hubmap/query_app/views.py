import json
import traceback
from typing import Callable

import django.core.serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .analysis import calculate_statistics, get_bounds
from .models import Cell, Cluster, Dataset, Gene, Organ, Protein, StatReport
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
    StatReportSerializer,
)
from .set_evaluators import evaluation_detail, evaluation_list, query_set_count
from .set_operators import query_set_difference, query_set_intersection, query_set_union
from .utils import get_app_status

JSONSerializer = django.core.serializers.get_serializer("json")


class PaginationClass(PageNumberPagination):
    page_size = 100000
    max_page_size = 100000


def get_generic_response(self, callable, request):
    try:
        return JsonResponse(callable(self, request), safe=False)
    except Exception as e:
        tb = traceback.format_exc()
        json_error_response = {"error": {"stack_trace": tb}, "message": str(e)}
        print(json_error_response)
        return JsonResponse(json_error_response)


def query(self, request):
    endpoints_dict = {
        "gene": gene_query,
        "organ": organ_query,
        "cell": cell_query,
        "dataset": dataset_query,
        "cluster": cluster_query,
        "protein": protein_query,
    }
    endpoint = request.path.split("/")[-2]
    callable = endpoints_dict[endpoint]
    return get_generic_response(self, callable, request)


def operation(self, request):
    endpoints_dict = {
        "union": query_set_union,
        "intersection": query_set_intersection,
        "difference": query_set_difference,
    }
    endpoint = request.path.split("/")[-2]
    callable = endpoints_dict[endpoint]
    return get_generic_response(self, callable, request)


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


class QueryViewSet(viewsets.GenericViewSet):
    pagination_class = PaginationClass
    serializer_class = JSONSerializer

    def post(self, request, format=None):
        return query(self, request)


class OperationViewSet(viewsets.GenericViewSet):
    pagination_class = PaginationClass
    serializer_class = JSONSerializer

    def post(self, request, format=None):
        return operation(self, request)


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


class SetCountViewSet(viewsets.ModelViewSet):
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_generic_response(self, query_set_count, request)


class StatisticViewSet(viewsets.ModelViewSet):
    queryset = StatReport.objects.all()
    serializer_class = StatReportSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_response(self, request, calculate_statistics)


class StatusViewSet(viewsets.GenericViewSet):
    pagination_class = PaginationClass
    serializer_class = JSONSerializer

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
    serializer_class = JSONSerializer

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
