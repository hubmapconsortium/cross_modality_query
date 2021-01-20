from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .models import (
    Cell,
    CellAndValues,
    Cluster,
    ClusterAndValues,
    Dataset,
    Gene,
    GeneAndValues,
    Organ,
    OrganAndValues,
    QuerySet,
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
    DatasetSerializer,
    GeneAndValuesSerializer,
    GeneSerializer,
    OrganAndValuesSerializer,
    OrganSerializer,
    QuerySetCountSerializer,
    QuerySetSerializer,
)
from .set_evaluators import (
    cell_evaluation_detail,
    cluster_evaluation_detail,
    evaluation_list,
    gene_evaluation_detail,
    organ_evaluation_detail,
    query_set_count,
)
from .set_operators import (
    query_set_difference,
    query_set_intersection,
    query_set_negation,
    query_set_union,
)


class PaginationClass(PageNumberPagination):
    page_size = 10
    max_page_size = 10


class CellViewSet(viewsets.ModelViewSet):
    query_set = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass
    model = QuerySet

    def post(self, request, format=None):
        response = cell_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response

    def get(self, request, format=None):
        response = cell_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class OrganViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass
    model = QuerySet

    def post(self, request, format=None):
        response = organ_query(self, request)
        #        return Response(response)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response

    def get(self, request, format=None):
        response = organ_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class GeneViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass
    model = QuerySet

    def post(self, request, format=None):
        response = gene_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response

    def get(self, request, format=None):
        response = gene_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class ProteinViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass

    def get(self, request, format=None):
        response = protein_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class ClusterViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass
    model = QuerySet

    def get(self, request, format=None):
        response = cluster_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response

    def post(self, request, format=None):
        response = cluster_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class DatasetViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass
    model = QuerySet

    def get(self, request, format=None):
        response = dataset_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response

    def post(self, request, format=None):
        response = dataset_query(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class CellDetailEvaluationViewSet(viewsets.ModelViewSet):
    query_set = CellAndValues.objects.all()
    serializer_class = CellAndValuesSerializer
    pagination_class = PaginationClass
    model = CellAndValues

    def post(self, request, format=None):
        response = cell_evaluation_detail(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class OrganDetailEvaluationViewSet(viewsets.ModelViewSet):
    queryset = OrganAndValues.objects.all()
    serializer_class = OrganAndValuesSerializer
    model = OrganAndValues
    pagination_class = PaginationClass

    def post(self, request, format=None):
        response = organ_evaluation_detail(self, request)
        #        return Response(response)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class GeneDetailEvaluationViewSet(viewsets.ModelViewSet):
    queryset = GeneAndValues.objects.all()
    serializer_class = GeneAndValuesSerializer
    pagination_class = PaginationClass
    model = GeneAndValues

    def post(self, request, format=None):
        response = gene_evaluation_detail(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class ClusterDetailEvaluationViewSet(viewsets.ModelViewSet):
    queryset = ClusterAndValues.objects.all()
    serializer_class = ClusterAndValuesSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        response = cluster_evaluation_detail(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class CellListEvaluationViewSet(viewsets.ModelViewSet):
    query_set = Cell.objects.all()
    serializer_class = CellSerializer
    pagination_class = PaginationClass
    model = Cell

    def post(self, request, format=None):
        response = evaluation_list(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class OrganListEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Organ.objects.all()
    serializer_class = OrganSerializer
    pagination_class = PaginationClass
    model = Organ

    def post(self, request, format=None):
        response = evaluation_list(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class GeneListEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Gene.objects.all()
    serializer_class = GeneSerializer
    pagination_class = PaginationClass
    model = Gene

    def post(self, request, format=None):
        response = evaluation_list(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class ClusterListEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        response = evaluation_list(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class DatasetListEvaluationViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        response = evaluation_list(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class SetIntersectionViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        response = query_set_intersection(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class SetUnionViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        response = query_set_union(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class SetNegationViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        response = query_set_negation(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class SetDifferenceViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        response = query_set_difference(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response


class SetCountViewSet(viewsets.ModelViewSet):
    queryset = QuerySet.objects.all()
    serializer_class = QuerySetCountSerializer
    pagination_class = PaginationClass

    def post(self, request, format=None):
        response = query_set_count(self, request)
        paginated_queryset = self.paginate_queryset(response)
        paginated_response = self.get_paginated_response(paginated_queryset)
        return paginated_response
