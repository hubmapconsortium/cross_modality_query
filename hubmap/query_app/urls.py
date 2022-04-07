from django.contrib import admin
from django.urls import path
from rest_framework.schemas import get_schema_view

from query_app import views

admin.autodiscover()
# first we define the serializers

urlpatterns = [
    path(
        "",
        get_schema_view(
            title="HuBMAP cell indexing",
            version="0.1-dev",
        ),
        name="openapi-schema",
    ),
    path("gene/", views.QueryViewSet.as_view(), name="gene_query"),
    path("cell/", views.QueryViewSet.as_view(), name="cell_query"),
    path("organ/", views.QueryViewSet.as_view(), name="organ_query"),
    path("protein/", views.QueryViewSet.as_view(), name="protein_query"),
    path("cluster/", views.QueryViewSet.as_view(), name="cluster_query"),
    path("dataset/", views.QueryViewSet.as_view(), name="dataset_query"),
    path("celltype/", views.QueryViewSet.as_view(), name="cell_type_query"),
    path("difference/", views.OperationViewSet.as_view(), name="set_difference"),
    path("union/", views.OperationViewSet.as_view(), name="set_union"),
    path(
        "intersection/",
        views.OperationViewSet.as_view(),
        name="set_intersection",
    ),
    path("count/", views.SetCountViewSet.as_view(), name="set_count"),
    path("mean/", views.StatisticViewSet.as_view(), name="set_mean"),
    path("min/", views.StatisticViewSet.as_view(), name="set_min"),
    path("max/", views.StatisticViewSet.as_view(), name="set_max"),
    path("stddev/", views.StatisticViewSet.as_view(), name="set_max"),
    path(
        "cellevaluation/",
        views.CellListEvaluationViewSet.as_view({"post": "post"}),
        name="cell_list_evaluation",
    ),
    path(
        "celltypeevaluation/",
        views.CellTypeListEvaluationViewSet.as_view({"post": "post"}),
        name="cell_type_list_evaluation",
    ),
    path(
        "geneevaluation/",
        views.GeneListEvaluationViewSet.as_view({"post": "post"}),
        name="gene_list_evaluation",
    ),
    path(
        "organevaluation/",
        views.OrganListEvaluationViewSet.as_view({"post": "post"}),
        name="organ_list_evaluation",
    ),
    path(
        "clusterevaluation/",
        views.ClusterListEvaluationViewSet.as_view({"post": "post"}),
        name="cluster_list_evaluation",
    ),
    path(
        "datasetevaluation/",
        views.DatasetListEvaluationViewSet.as_view({"post": "post"}),
        name="dataset_list_evaluation",
    ),
    path(
        "proteinevaluation/",
        views.ProteinListEvaluationViewSet.as_view({"post": "post"}),
        name="protein_list_evaluation",
    ),
    path(
        "celldetailevaluation/",
        views.CellDetailEvaluationViewSet.as_view({"post": "post"}),
        name="cell_detail_evaluation",
    ),
    path(
        "celltypedetailevaluation/",
        views.CellTypeDetailEvaluationViewSet.as_view({"post": "post"}),
        name="cell_type_detail_evaluation",
    ),
    path(
        "genedetailevaluation/",
        views.GeneDetailEvaluationViewSet.as_view({"post": "post"}),
        name="gene_detail_evaluation",
    ),
    path(
        "organdetailevaluation/",
        views.OrganDetailEvaluationViewSet.as_view({"post": "post"}),
        name="organ_detail_evaluation",
    ),
    path(
        "clusterdetailevaluation/",
        views.ClusterDetailEvaluationViewSet.as_view({"post": "post"}),
        name="cluster_detail_evaluation",
    ),
    path(
        "datasetdetailevaluation/",
        views.DatasetDetailEvaluationViewSet.as_view({"post": "post"}),
        name="dataset_detail_evaluation",
    ),
    path(
        "proteindetailevaluation/",
        views.ProteinListEvaluationViewSet.as_view({"post": "post"}),
        name="protein_detail_evaluation",
    ),
    path(
        "bounds/",
        views.ValueBoundsViewSet.as_view(),
        name="max_value",
    ),
    path("status/", views.StatusViewSet.as_view(), name="app_status"),
    path(
        "openapi/",
        get_schema_view(
            title="HuBMAP cell indexing",
            version="0.1-dev",
        ),
        name="openapi-schema",
    ),
]
