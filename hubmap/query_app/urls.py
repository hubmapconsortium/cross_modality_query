from django.contrib import admin
from django.urls import path
from rest_framework.schemas import get_schema_view

from query_app import views

from .browser_views import *

admin.autodiscover()
# first we define the serializers

urlpatterns = [
    path("", LandingFormView.as_view(), name="landing_page"),
    path("gene/", views.GeneViewSet.as_view({"post": "post"}), name="gene_query"),
    path("cell/", views.CellViewSet.as_view({"post": "post"}), name="cell_query"),
    path("organ/", views.OrganViewSet.as_view({"post": "post"}), name="organ_query"),
    path("protein/", views.ProteinViewSet.as_view({"post": "post"}), name="protein_query"),
    path("cluster/", views.ClusterViewSet.as_view({"post": "post"}), name="cluster_query"),
    path("dataset/", views.DatasetViewSet.as_view({"post": "post"}), name="dataset_query"),
    path(
        "difference/", views.SetDifferenceViewSet.as_view({"post": "post"}), name="set_difference"
    ),
    path("union/", views.SetUnionViewSet.as_view({"post": "post"}), name="set_union"),
    path(
        "intersection/",
        views.SetIntersectionViewSet.as_view({"post": "post"}),
        name="set_intersection",
    ),
    path("count/", views.SetCountViewSet.as_view({"post": "post"}), name="set_count"),
    path("mean/", views.StatisticViewSet.as_view({"post": "post"}), name="set_mean"),
    path("min/", views.StatisticViewSet.as_view({"post": "post"}), name="set_min"),
    path("max/", views.StatisticViewSet.as_view({"post": "post"}), name="set_max"),
    path("stddev/", views.StatisticViewSet.as_view({"post": "post"}), name="set_max"),
    path(
        "cellevaluation/",
        views.CellListEvaluationViewSet.as_view({"post": "post"}),
        name="cell_list_evaluation",
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
        name="celL_detail_evaluation",
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
        name="cluster_detail_evaluation",
    ),
    path("geneform/", GeneQueryView.as_view(), name="gene_query_form"),
    path("cellform/", CellQueryView.as_view(), name="cell_query_form"),
    path("organform/", OrganQueryView.as_view(), name="organ_query_form"),
    path("clusterform/", ClusterQueryView.as_view(), name="cluster_query_form"),
    path("datasetform/", DatasetQueryView.as_view(), name="dataset_query_form"),
    path("intersectionform/", SetIntersectionFormView.as_view(), name="intersection_form"),
    path("unionform/", SetUnionFormView.as_view(), name="union_form"),
    path("countform/", SetCountFormView.as_view(), name="count_form"),
    path("evaluationform/", EvaluationLandingFormView.as_view(), name="evaluation_form"),
    path("cellevaluationform/", CellSetEvaluationFormView.as_view(), name="cell_evaluation_form"),
    path("geneevaluationform/", GeneSetEvaluationFormView.as_view(), name="gene_evaluation_form"),
    path(
        "organevaluationform/", OrganSetEvaluationFormView.as_view(), name="organ_evaluation_form"
    ),
    path(
        "clusterevaluationform/",
        ClusterSetEvaluationFormView.as_view(),
        name="cluster_evaluation_form",
    ),
    path("celllistform/", CellSetListFormView.as_view(), name="cell_evaluation_form"),
    path("genelistform/", GeneSetListFormView.as_view(), name="gene_evaluation_form"),
    path("organlistform/", OrganSetListFormView.as_view(), name="organ_evaluation_form"),
    path("clusterlistform/", ClusterSetListFormView.as_view(), name="cluster_evaluation_form"),
    path("datasetlistform/", DatasetSetListFormView.as_view(), name="dataset_evaluation_form"),
    path("celllist/", CellListView.as_view(), name="cell_list"),
    path("genelist/", GeneListView.as_view(), name="gene_list"),
    path("clusterlist/", ClusterListView.as_view(), name="cluster_list"),
    path("organlist/", OrganListView.as_view(), name="organ_list"),
    path("celldetail/", CellDetailView.as_view(), name="cell_list"),
    path("genedetail/", GeneDetailView.as_view(), name="gene_list"),
    path("clusterdetail/", ClusterDetailView.as_view(), name="cluster_list"),
    path("organdetail/", OrganDetailView.as_view(), name="organ_list"),
    path("querysetlist/", QuerySetListView.as_view(), name="query_set_list"),
    path(
        "intersectionlist/",
        QuerySetIntersectionListView.as_view(),
        name="query_set_intersection_list",
    ),
    path("unionlist/", QuerySetUnionListView.as_view(), name="query_set_union_list"),
    path("querysetcountlist/", QuerySetCountListView.as_view(), name="query_set_count_list"),
    path(
        "openapi",
        get_schema_view(
            title="HuBMAP cell indexing",
            version="0.1-dev",
        ),
        name="openapi-schema",
    ),
]
