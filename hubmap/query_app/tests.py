from django.test import TestCase


class QueryTestCase(TestCase):
    fixtures = []

    def setUp(self):
        # Test definitions as before.
        pass

    def test_gene_queries(self):
        # leiden cluster
        # 2 organs and
        # 2 organs or
        pass

    def test_organ_queries(self):
        pass
        # 2 genes and
        # 2 genes or
        # cells

    def test_cell_queries(self):
        # 2 genes and
        # 2 genes or
        # 2 genes gt
        # 2 genes lt
        # 2 genes rna
        # 2 genes atac
        # 2 proteins and
        # 2 proteins or
        # 2 proteins gt
        # 2 proteins lt
        # 2 proteins rna
        # 2 proteins atac

        pass
