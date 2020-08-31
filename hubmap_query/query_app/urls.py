from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

admin.autodiscover()
# first we define the serializers

urlpatterns = [
    path('catquery/', views.CategoricalQuery.as_view(), name="categorical_query"),
    path('quantquery/', views.QuantitativeQuery.as_view(), name="quantitative_query"),
    path('genes/', views.GeneListView.as_view(), name="genes"),
]
