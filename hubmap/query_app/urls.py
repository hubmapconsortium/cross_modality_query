from django.contrib import admin
from django.urls import path
from rest_framework.schemas import get_schema_view

from query_app import views

admin.autodiscover()
# first we define the serializers

urlpatterns = [
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
        name="protein_detail_evaluation",
    ),
    path(
        "cellvaluesevaluation/",
        views.CellValuesViewSet.as_view({"post": "post"}),
        name="cell_values_evaluation",
    ),
    path(
        "bounds/",
        views.ValueBoundsViewSet.as_view({"post": "post"}),
        name="max_value",
    ),
    path("status/", views.StatusViewSet.as_view({"get": "get"}), name="app_status"),
    path(
        "openapi/",
        get_schema_view(
            title="HuBMAP cell indexing",
            version="0.1-dev",
        ),
        name="openapi-schema",
    ),
    path(
        "/add-delete/delete/",
        views.DeleteModalityDataView.as_view({"post": "post"}),
        name="delete_modality_data_view",
    ),
    path(
        "/add-delete/insert/",
        views.CreateModelView.as_view({"post": "post"}),
        name="create_model_view",
    ),
    path(
        "/add-delete/setuprelationships/",
        views.SetUpClusterRelationshipsView.as_view({"post": "post"}),
        name="set_up_relationships_view",
    ),
    path(
        "/add-delete/precomputepercentages/",
        views.PrecomputePercentagesView.as_view({"post": "post"}),
        name="precompute_percentages_view",
    ),
]
