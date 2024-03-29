import json
import traceback
from time import perf_counter
from typing import Callable

import django.core.serializers
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.views import View
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from .analysis import calculate_statistics, get_bounds
from .models import Cell, CellType, Cluster, Dataset, Gene, Organ, Protein
from .queries import (
    cell_query,
    cell_type_query,
    cluster_query,
    dataset_query,
    gene_query,
    organ_query,
    protein_query,
)
from .serializers import (
    CellAndValuesSerializer,
    CellSerializer,
    CellTypeSerializer,
    ClusterAndValuesSerializer,
    ClusterSerializer,
    DatasetAndValuesSerializer,
    DatasetSerializer,
    GeneAndValuesSerializer,
    GeneSerializer,
    OrganAndValuesSerializer,
    OrganSerializer,
    ProteinSerializer,
)
from .set_evaluators import evaluation_detail, evaluation_list, query_set_count
from .set_operators import query_set_difference, query_set_intersection, query_set_union
from .utils import get_app_status

JSONSerializer = django.core.serializers.get_serializer("json")


class PaginationClass(PageNumberPagination):
    page_size = settings.MAX_PAGE_SIZE
    max_page_size = settings.MAX_PAGE_SIZE


def get_generic_response(self, callable, request):
    try:
        return JsonResponse(callable(self, request), safe=False)
    except ValueError as e:
        tb = traceback.format_exc()
        json_error_response = {"error": {"stack_trace": tb}, "message": str(e)}
        response = JsonResponse(json_error_response)
        response.status_code = 400
        return response
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
        "celltype": cell_type_query,
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
        if isinstance(response, str):
            return HttpResponse(response)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response
    except ValueError as e:
        tb = traceback.format_exc()
        json_error_response = {"error": {"stack_trace": tb}, "message": str(e)}
        response = JsonResponse(json_error_response)
        response.status_code = 400
        return response
    except Exception as e:
        tb = traceback.format_exc()
        json_error_response = json.dumps({"error": {"stack_trace": tb}, "message": str(e)})
        print(json_error_response)
        return HttpResponse(json_error_response)


class QueryViewSet(APIView):
    pagination_class = PaginationClass
    serializer_class = JSONSerializer

    def post(self, request, format=None):
        return query(self, request)


class OperationViewSet(APIView):
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
        response = get_response(self, request, evaluation_detail)
        print("Got response")
        print(response)
        return response


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


class CellTypeListEvaluationViewSet(viewsets.ModelViewSet):
    query_set = CellType.objects.all()
    serializer_class = CellTypeSerializer
    pagination_class = PaginationClass
    model = CellType

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


class SetCountViewSet(APIView):
    pagination_class = PaginationClass

    def post(self, request, format=None):
        return get_generic_response(self, query_set_count, request)


class StatisticViewSet(APIView):
    pagination_class = PaginationClass
    serializer_class = JSONSerializer

    def post(self, request, format=None):
        return get_generic_response(self, calculate_statistics, request)


class StatusViewSet(APIView):
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


class ValueBoundsViewSet(APIView):
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
