from datetime import datetime

from celery import shared_task
from django.conf import settings

from .models import (
    CellAndValues,
    ClusterAndValues,
    GeneAndValues,
    OrganAndValues,
    QuerySet,
)


@shared_task
def delete_expired_querysets():
    querysets = QuerySet.objects.filter(
        created__lt=datetime.now() - settings.QUERY_TOKEN_EXPIRATION
    )
    querysets.delete()


@shared_task
def delete_expired_and_values():
    cells_and_values = CellAndValues.objects.filter(
        created__lt=datetime.now() - settings.QUERY_TOKEN_EXPIRATION
    )
    cells_and_values.delete()

    genes_and_values = GeneAndValues.objects.filter(
        created__lt=datetime.now() - settings.QUERY_TOKEN_EXPIRATION
    )
    genes_and_values.delete()

    organs_and_values = OrganAndValues.objects.filter(
        created__lt=datetime.now() - settings.QUERY_TOKEN_EXPIRATION
    )
    organs_and_values.delete()

    clusters_and_values = ClusterAndValues.objects.filter(
        created__lt=datetime.now() - settings.QUERY_TOKEN_EXPIRATION
    )
    clusters_and_values.delete()
