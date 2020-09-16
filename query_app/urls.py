from django.contrib import admin
from django.urls import path

from . import views

admin.autodiscover()
# first we define the serializers

urlpatterns = [
    path('genequery/', views.GeneViewSet.as_view({'post': 'post'}), name="gene_query"),
    path('cellquery/', views.CellViewSet.as_view({'post': 'post'}), name="cell_query"),
    path('organquery/', views.CellGroupingViewSet.as_view({'post': 'post'}), name="organ_query"),
    path('query/', views.LandingFormView.as_view(), name="landing_page"),
    path('genequeryform', views.GeneQueryView.as_view(), name="gene_query_form"),
    path('cellqueryform', views.CellQueryView.as_view(), name="cell_query_form"),
    path('organqueryform', views.OrganQueryView.as_view(), name="organ_query_form"),
]
