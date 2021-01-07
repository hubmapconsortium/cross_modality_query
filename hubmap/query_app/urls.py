from django.contrib import admin
from django.urls import path
from rest_framework.schemas import get_schema_view

from query_app import views

admin.autodiscover()
# first we define the serializers

urlpatterns = [
    path("", views.LandingFormView.as_view(), name="landing_page"),
    path("gene/", views.GeneViewSet.as_view({"post": "post"}), name="gene_query"),
    path("cell/", views.CellViewSet.as_view({"post": "post"}), name="cell_query"),
    path("organ/", views.OrganViewSet.as_view({"post": "post"}), name="organ_query"),
    path("protein/", views.ProteinViewSet.as_view({"get": "get"}), name="protein_query"),
    path("cluster/", views.ClusterViewSet.as_view({"post": "post"}), name="cluster_query"),
    path("dataset/", views.DatasetViewSet.as_view({"post": "post"}), name="dataset_query"),
    path("negation/", views.SetNegationViewSet.as_view({"post": "post"}), name="set_negation"),
    path("difference/", views.SetDifferenceViewSet.as_view({"post": "post"}), name="set_difference"),
    path("union/", views.SetUnionViewSet.as_view({"post": "post"}), name="set_union"),
    path("intersection/", views.SetIntersectionViewSet.as_view({"post": "post"}), name="set_intersection"),
    path("count/", views.SetCountViewSet.as_view({"post":"post"}), name="set_count"),
    path("cellevaluation/", views.CellListEvaluationViewSet.as_view({"post": "post"}), name="cell_list_evaluation"),
    path("geneevaluation/", views.GeneListEvaluationViewSet.as_view({"post": "post"}), name="gene_list_evaluation"),
    path("organevaluation/", views.OrganListEvaluationViewSet.as_view({"post": "post"}), name="organ_list_evaluation"),
    path("clusterevaluation/", views.ClusterListEvaluationViewSet.as_view({"post": "post"}), name="cluster_list_evaluation"),
    path("datasetevaluation/", views.DatasetListEvaluationViewSet.as_view({"post": "post"}),
         name="dataset_list_evaluation"),
    path("celldetailevaluation/", views.CellDetailEvaluationViewSet.as_view({"post": "post"}), name="celL_detail_evaluation"),
    path("genedetailevaluation/", views.GeneDetailEvaluationViewSet.as_view({"post": "post"}), name="gene_detail_evaluation"),
    path("organdetailevaluation/", views.OrganDetailEvaluationViewSet.as_view({"post": "post"}), name="organ_detail_evaluation"),
    path("clusterdetailevaluation/", views.ClusterDetailEvaluationViewSet.as_view({"post": "post"}), name="cluster_detail_evaluation"),
    path("geneform/", views.GeneQueryView.as_view(), name="gene_query_form"),
    path("cellform/", views.CellQueryView.as_view(), name="cell_query_form"),
    path("organform/", views.OrganQueryView.as_view(), name="organ_query_form"),
    path("clusterform/", views.ClusterQueryView.as_view(), name="cluster_query_form"),
    path("datasetform/", views.DatasetQueryView.as_view(), name="dataset_query_form"),
    path("intersectionform/", views.SetIntersectionFormView.as_view(), name="intersection_form"),
    path("unionform/", views.SetUnionFormView.as_view(), name="union_form"),
    path("negationform/", views.SetNegationFormView.as_view(), name="negation_form"),
    path("countform/", views.SetCountFormView.as_view(), name="count_form"),
    path("evaluationform/", views.EvaluationLandingFormView.as_view(), name="evaluation_form"),
    path("cellevaluationform/", views.CellSetEvaluationFormView.as_view(), name="cell_evaluation_form"),
    path("geneevaluationform/", views.GeneSetEvaluationFormView.as_view(), name="gene_evaluation_form"),
    path("organevaluationform/", views.OrganSetEvaluationFormView.as_view(), name="organ_evaluation_form"),
    path("clusterevaluationform/", views.ClusterSetEvaluationFormView.as_view(), name="cluster_evaluation_form"),
    path("celllistform/", views.CellSetListFormView.as_view(), name="cell_evaluation_form"),
    path("genelistform/", views.GeneSetListFormView.as_view(), name="gene_evaluation_form"),
    path("organlistform/", views.OrganSetListFormView.as_view(), name="organ_evaluation_form"),
    path("clusterlistform/", views.ClusterSetListFormView.as_view(), name="cluster_evaluation_form"),
    path("datasetlistform/", views.DatasetSetListFormView.as_view(), name="dataset_evaluation_form"),
    path("celllist/", views.CellListView.as_view(), name="cell_list"),
    path("genelist/", views.GeneListView.as_view(), name="gene_list"),
    path("clusterlist/", views.ClusterListView.as_view(), name="cluster_list"),
    path("organlist/", views.OrganListView.as_view(), name="organ_list"),
    path("celldetail/", views.CellDetailView.as_view(), name="cell_list"),
    path("genedetail/", views.GeneDetailView.as_view(), name="gene_list"),
    path("clusterdetail/", views.ClusterDetailView.as_view(), name="cluster_list"),
    path("organdetail/", views.OrganDetailView.as_view(), name="organ_list"),
    path("querysetlist/", views.QuerySetListView.as_view(), name="query_set_list"),
    path("intersectionlist/", views.QuerySetIntersectionListView.as_view(), name="query_set_intersection_list"),
    path("unionlist/", views.QuerySetUnionListView.as_view(), name="query_set_union_list"),
    path("negationlist/", views.QuerySetNegationListView.as_view(), name="query_set_negation_list"),
    path("querysetcountlist/", views.QuerySetCountListView.as_view(), name="query_set_count_list"),
    path(
        "openapi",
        get_schema_view(
            title="HuBMAP cell indexing",
            version="0.1-dev",
        ),
        name="openapi-schema",
    ),
]
