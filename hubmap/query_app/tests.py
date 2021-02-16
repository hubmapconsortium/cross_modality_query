from typing import List

from django.test import Client, TestCase

c = Client()

base_url = "/api/"


def hubmap_query(
    input_type: str,
    output_type: str,
    input_set: List[str],
    genomic_modality: str = None,
    p_value: float = None,
    set_key: str = None,
    logical_operator: str = None,
):
    request_url = base_url + output_type + "/"
    request_dict = {
        "input_type": input_type,
        "input_set": input_set,
        "genomic_modality": genomic_modality,
        "p_value": p_value,
        "logical_operator": logical_operator,
    }
    for key in request_dict:
        if request_dict[key] is None:
            request_dict.pop(key)
    return c.post(request_url, request_dict).json()["results"][0]["query_handle"]


def get_all(output_type: str):
    request_url = base_url + output_type + "/"
    return c.post(request_url).json()["results"][0]["query_handle"]


def set_count(set_key: str, set_type: str) -> str:
    request_url = base_url + "count/"
    request_dict = {"key": set_key, "set_type": set_type}
    return c.post(request_url, request_dict).json()["results"][0]["count"]


def set_intersection(set_key_one: str, set_key_two: str, set_type: str) -> str:
    request_url = base_url + "intersection/"
    request_dict = {"key_one": set_key_one, "key_two": set_key_two, "set_type": set_type}
    response_json = c.post(request_url, request_dict).json()["results"]
    return response_json[0]["query_handle"]  # Returns the key to be used in future computations


def set_union(set_key_one: str, set_key_two: str, set_type: str) -> str:
    request_url = base_url + "union/"
    request_dict = {"key_one": set_key_one, "key_two": set_key_two, "set_type": set_type}
    response_json = c.post(request_url, request_dict).json()["results"]
    return response_json[0]["query_handle"]  # Returns the key to be used in future computations


def set_difference(set_key_one: str, set_key_two: str, set_type: str) -> str:
    request_url = base_url + "difference/"
    request_dict = {"key_one": set_key_one, "key_two": set_key_two, "set_type": set_type}
    response_json = c.post(request_url, request_dict).json()["results"]
    return response_json[0]["query_handle"]  # Returns the key to be used in future computations


def set_list_evaluation(set_key: str, set_type: str, limit: int, offset=0):
    request_url = base_url + set_type + "evaluation/"
    request_dict = {"key": set_key, "set_type": set_type, "limit": limit, "offset": offset}
    response = c.post(request_url, request_dict).json()["results"]
    response_json = response.json()
    return response_json


# This function/API call returns a more detailed version of the set, containing data specified in include_values
# It may be slow.


def set_detail_evaluation(
    set_key: str,
    set_type: str,
    limit: int,
    values_included: List = [],
    sort_by: str = None,
    offset=0,
):
    request_url = base_url + set_type + "detailevaluation/"
    request_dict = {
        "key": set_key,
        "set_type": set_type,
        "limit": limit,
        "offset": offset,
        "values_included": values_included,
        "sort_by": sort_by,
    }
    response = c.post(request_url, request_dict).json()["results"]
    response_json = response.json()
    return response_json  # Returns the key to be used in future computations


class CellTestCase(TestCase):
    fixtures = [
        "/query_app/fixtures/dump.json",
    ]

    def test_all_cells(self):
        all_cells = get_all("cell")
        all_cells_count = set_count(all_cells, "cell")
        self.assertEqual(all_cells_count, 3000)

    def test_cells_from_genes(self):
        input_sets = {"atac": ["VIM > 0.015", "AASS > 0.11"], "rna": ["VIM > 10", "ABL1 > 0"]}
        params_dict = {"rna": {"and": 1, "or": 27}, "atac": {"and": 4, "or": 995}}
        for modality in params_dict:
            input_set = input_sets[modality]
            for log_op in modality:
                cells_from_genes = hubmap_query(
                    "gene", "cell", input_set, genomic_modality=modality, logical_operator=log_op
                )
                cells_from_genes_count = set_count(cells_from_genes, "cell")
                self.assertEqual(
                    cells_from_genes_count, params_dict["modality"]["logical_operator"]
                )

    def test_cells_from_proteins(self):
        input_set = ["Ki67 > 1000", "CD21 > 1500"]
        params_dict = {"and": 67, "or": 356}
        for log_op in params_dict:
            cells_from_proteins = hubmap_query(
                "protein", "cell", input_set, logical_operator=log_op
            )
            cells_from_protein_count = set_count(cells_from_proteins, "cell")
            self.assertEqual(cells_from_protein_count, params_dict["logical_operator"])

    def test_cells_from_cells(self):
        input_set = [
            "0576b972e074074b4c51a61c3d17a6e3-AAACGAATCCAACCGG",
            "0576b972e074074b4c51a61c3d17a6e3-AAACGCTCAACGACAG",
        ]
        cells_from_cells = hubmap_query("cell", "cell", input_set)
        cells_from_cells_count = set_count(cells_from_cells, "cell")
        self.assertEqual(cells_from_cells_count, 2)

    def test_cells_from_organs(self):
        input_set = ["Heart", "Lymph Node"]
        cells_from_organ = hubmap_query("organ", "cell", input_set)
        cells_from_organ_count = set_count(cells_from_organ, "cell")
        self.assertEqual(cells_from_organ_count, 3000)

    def test_cells_from_datasets(self):
        input_set = ["a83a0a7b03d26167344ccbd0df46331e", "d4493657cde29702c5ed73932da5317c"]
        cells_from_dataset = hubmap_query("dataset", "cell", input_set)
        cells_from_dataset_count = set_count(cells_from_dataset, "cell")
        self.assertEqual(cells_from_dataset_count, 2000)


class GeneTestCase(TestCase):
    fixtures = [
        "/query_app/fixtures/dump.json",
    ]

    def test_all_genes(self):
        all_genes = get_all("gene")
        all_genes_count = set_count(all_genes, "gene")
        self.assertEqual(all_genes_count, 1834)

    def test_genes_from_organs(self):
        input_sets = {"rna": ["Lymph Node"], "atac": "Heart"}
        params_dict = {"rna": 970, "atac": 987}
        for modality in params_dict:
            input_set = input_sets["modality"]
            genes_from_organs = hubmap_query(
                "organ", "gene", input_set, genomic_modality=modality, p_value=0.05
            )
            genes_from_organs_count = set_count(genes_from_organs, "gene")
            self.assertEqual(genes_from_organs_count, params_dict[modality])

    def test_genes_from_clusters(self):
        # @TODO: RNA clusters, values for both
        input_sets = {
            "rna": [],
            "atac": [
                "leiden-UMAP-d4493657cde29702c5ed73932da5317c-1",
                "leiden-UMAP-d4493657cde29702c5ed73932da5317c-10",
            ],
        }
        params_dict = {"rna": 0, "atac": 0}
        for modality in params_dict:
            input_set = input_sets[modality]
            genes_from_clusters = hubmap_query(
                "cluster", "gene", input_set, genomic_modality=modality, p_value=0.05
            )
            genes_from_clusters_count = set_count(genes_from_clusters, "gene")
            self.assertEqual(genes_from_clusters_count, params_dict[modality])

    def test_genes_from_genes(self):
        input_set = ["VIM", "AASS"]
        genes_from_genes = hubmap_query("gene", "gene", input_set)
        genes_from_genes_count = set_count(genes_from_genes, "gene")
        self.assertEqual(genes_from_genes_count, 2)


class OrganTestCase(TestCase):
    fixtures = [
        "/query_app/fixtures/dump.json",
    ]

    def test_all_organs(self):
        all_organs = get_all("organ")
        all_organs_count = set_count(all_organs, "organ")
        self.assertEqual(all_organs_count, 2)

    def test_organs_from_genes(self):
        input_set = ["VIM"]
        params_dict = {"rna": 1, "atac": 1}
        for modality in params_dict:
            organs_from_genes = hubmap_query(
                "gene", "organ", input_set, genomic_modality=modality, p_value=0.05
            )
            organs_from_genes_count = set_count(organs_from_genes, "organ")
            self.assertEqual(organs_from_genes_count, params_dict[modality])

    def test_organs_from_cells(self):
        input_set = [
            "0576b972e074074b4c51a61c3d17a6e3-AAACGAATCCAACCGG",
            "0576b972e074074b4c51a61c3d17a6e3-AAACGCTCAACGACAG",
        ]
        organs_from_cells = hubmap_query("cell", "organ", input_set)
        organs_from_cells_count = set_count(organs_from_cells, "organ")
        self.assertEqual(organs_from_cells_count, 1)

    def test_organs_from_organs(self):
        input_set = ["Heart", "Lymph Node"]
        organs_from_organs = hubmap_query("organ", "organ", input_set)
        organs_from_organs_count = set_count(organs_from_organs, "organ")
        self.assertEqual(organs_from_organs_count, 2)


class DatasetTestCase(TestCase):
    fixtures = [
        "/query_app/fixtures/dump.json",
    ]

    def test_all_datasets(self):
        all_datasets = get_all("dataset")
        all_datasets_count = set_count(all_datasets, "dataset")
        self.assertEqual(all_datasets_count, 3)

    def test_datasets_from_cells(self):
        input_set = [
            "0576b972e074074b4c51a61c3d17a6e3-AAACGAATCCAACCGG",
            "0576b972e074074b4c51a61c3d17a6e3-AAACGCTCAACGACAG",
        ]
        datasets_from_cells = hubmap_query("cell", "dataset", input_set)
        datasets_from_cells_count = set_count(datasets_from_cells, "dataset")
        self.assertEqual(datasets_from_cells_count, 1)

    def test_datasets_from_datasets(self):
        input_set = ["a83a0a7b03d26167344ccbd0df46331e", "d4493657cde29702c5ed73932da5317c"]
        datasets_from_datasets = hubmap_query("dataset", "dataset", input_set)
        datasets_from_datasets_count = set_count(datasets_from_datasets, "dataset")
        self.assertEqual(datasets_from_datasets_count, 2)

    def test_datasets_from_clusters(self):
        input_set = [
            "leiden-UMAP-d4493657cde29702c5ed73932da5317c-1",
            "leiden-UMAP-d4493657cde29702c5ed73932da5317c-10",
        ]
        datasets_from_clusters = hubmap_query("cluster", "dataset", input_set)
        datasets_from_clusters_count = set_count(datasets_from_clusters, "dataset")
        self.assertEqual(datasets_from_clusters_count, 1)


class ClusterTestCase(TestCase):
    fixtures = [
        "/query_app/fixtures/dump.json",
    ]

    def test_all_clusters(self):
        all_clusters = get_all("cluster")
        all_clusters_count = set_count(all_clusters, "cluster")
        self.assertEqual(all_clusters_count, 1059)

    def test_clusters_from_genes(self):
        input_set = ["VIM"]
        params_dict = {"rna": 0, "atac": 0}
        for modality in params_dict:
            clusters_from_genes = hubmap_query(
                "gene", "cluster", input_set, genomic_modality=modality, p_value=0.05
            )
            clusters_from_genes_count = set_count(clusters_from_genes, "cluster")
            self.assertEqual(clusters_from_genes_count, params_dict[modality])

    def test_clusters_from_datasets(self):
        input_set = ["a83a0a7b03d26167344ccbd0df46331e", "d4493657cde29702c5ed73932da5317c"]
        clusters_from_datasets = hubmap_query("dataset", "cluster", input_set)
        clusters_from_datasets_count = set_count(clusters_from_datasets, "cluster")
        self.assertEqual(clusters_from_datasets_count, 52)

    def test_clusters_from_clusters(self):
        input_set = [
            "leiden-UMAP-d4493657cde29702c5ed73932da5317c-1",
            "leiden-UMAP-d4493657cde29702c5ed73932da5317c-10",
        ]
        clusters_from_clusters = hubmap_query("cluster", "cluster", input_set)
        clusters_from_clusters_count = set_count(clusters_from_clusters, "cluster")
        self.assertEqual(clusters_from_clusters_count, 2)


class ProteinTestCase(TestCase):
    fixtures = [
        "/query_app/fixtures/dump.json",
    ]

    def test_all_proteins(self):
        all_proteins = get_all("protein")
        all_proteins_count = set_count(all_proteins, "protein")
        self.assertEqual(all_proteins_count, 10)

    def test_proteins_from_proteins(self):
        input_set = [""]
        proteins_from_proteins = hubmap_query("protein", "protein", input_set)
        proteins_from_proteins_count = set_count(proteins_from_proteins, "protein")
        self.assertEqual(proteins_from_proteins_count, 2)


class OperationsTestCase(TestCase):
    fixtures = [
        "/query_app/fixtures/dump.json",
    ]

    def test_intersection(self):
        input_set = ["a83a0a7b03d26167344ccbd0df46331e"]
        cells_from_dataset = hubmap_query("dataset", "cell", input_set)
        input_set = ["Heart"]
        cells_from_organ = hubmap_query("organ", "cell", input_set)
        intersection_cells = set_intersection(cells_from_dataset, cells_from_organ, "cell")
        intersection_cells_count = set_count(intersection_cells, "cell")
        self.assertEqual(intersection_cells_count, 2000)

    def test_union(self):
        input_set = ["Ki67 > 1000", "CD21 > 1500"]
        cells_from_proteins = hubmap_query("protein", "cell", input_set, logical_operator="and")
        input_set = ["Heart"]
        cells_from_organ = hubmap_query("organ", "cell", input_set)
        union_cells = set_union(cells_from_proteins, cells_from_organ, "cell")
        union_cells_count = set_count(union_cells, "cell")
        self.assertEqual(union_cells_count, 1067)

    def test_difference(self):
        input_set = ["Ki67 > 1000", "CD21 > 1500"]
        cells_from_proteins = hubmap_query("protein", "cell", input_set, logical_operator="and")
        input_set = ["Lymph Node"]
        cells_from_organ = hubmap_query("organ", "cell", input_set)
        difference_cells = set_difference(cells_from_organ, cells_from_proteins, "cell")
        difference_cells_count = set_count(difference_cells, "cell")
        self.assertEqual(difference_cells_count, 1933)


class ListEvaluationTestCase(TestCase):
    fixtures = [
        "/query_app/fixtures/dump.json",
    ]

    def test_cells(self):
        all_cells = get_all("cell")
        evaluated_cell = set_list_evaluation(all_cells, "cell", 1)
        evaluated_cell_fields = list(evaluated_cell.keys())
        self.assertEqual(
            evaluated_cell_fields, ["cell_id", "modality", "dataset", "organ", "clusters"]
        )

    def test_genes(self):
        all_genes = get_all("gene")
        evaluated_gene = set_list_evaluation(all_genes, "gene", 1)
        evaluated_gene_fields = list(evaluated_gene.keys())
        self.assertEqual(evaluated_gene_fields, ["gene_symbol", "go_terms"])

    def test_organs(self):
        all_organs = get_all("organ")
        evaluated_organ = set_list_evaluation(all_organs, "organ", 1)
        evaluated_organ_fields = list(evaluated_organ.keys())
        self.assertEqual(evaluated_organ_fields, ["grouping_name"])

    def test_clusters(self):
        all_clusters = get_all("cluster")
        evaluated_cluster = set_list_evaluation(all_clusters, "cluster", 1)
        evaluated_cluster_fields = list(evaluated_cluster.keys())
        self.assertEqual(
            evaluated_cluster_fields,
            [
                "cluster_method",
                "cluster_data",
                "dataset",
                "grouping_name",
            ],
        )
        pass

    def test_datasets(self):
        all_datasets = get_all("dataset")
        evaluated_dataset = set_list_evaluation(all_datasets, "dataset", 1)
        evaluated_dataset_fields = list(evaluated_dataset.keys())
        self.assertEqual(evaluated_dataset_fields, ["uuid"])
        pass

    def test_proteins(self):
        all_proteins = get_all("protein")
        evaluated_protein = set_list_evaluation(all_proteins, "protein", 1)
        evaluated_protein_fields = list(evaluated_protein.keys())
        self.assertEqual(evaluated_protein_fields, ["protein_id", "go_terms"])
        pass


class DetailEvaluationTestCase(TestCase):
    fixtures = [
        "/query_app/fixtures/dump.json",
    ]

    def test_cells(self):
        all_cells = get_all("cell")
        evaluated_cell = set_detail_evaluation(all_cells, "cell", 1)
        evaluated_cell_fields = list(evaluated_cell.keys())
        self.assertEqual(
            evaluated_cell_fields,
            ["cell_id", "modality", "dataset", "organ", "clusters", "values"],
        )

    def test_genes(self):
        all_genes = get_all("gene")
        evaluated_gene = set_detail_evaluation(all_genes, "gene", 1)
        evaluated_gene_fields = list(evaluated_gene.keys())
        self.assertEqual(evaluated_gene_fields, ["gene_symbol", "go_terms", "values"])

    def test_organs(self):
        all_organs = get_all("organ")
        evaluated_organ = set_detail_evaluation(all_organs, "organ", 1)
        evaluated_organ_fields = list(evaluated_organ.keys())
        self.assertEqual(evaluated_organ_fields, ["grouping_name", "values"])

    def test_clusters(self):
        all_clusters = get_all("cluster")
        evaluated_cluster = set_detail_evaluation(all_clusters, "cluster", 1)
        evaluated_cluster_fields = list(evaluated_cluster.keys())
        self.assertEqual(
            evaluated_cluster_fields,
            ["cluster_method", "cluster_data", "dataset", "grouping_name", "values"],
        )
        pass

    def test_datasets(self):
        all_datasets = get_all("dataset")
        evaluated_dataset = set_detail_evaluation(all_datasets, "dataset", 1)
        evaluated_dataset_fields = list(evaluated_dataset.keys())
        self.assertEqual(evaluated_dataset_fields, ["uuid"])
        pass

    def test_proteins(self):
        all_proteins = get_all("protein")
        evaluated_protein = set_detail_evaluation(all_proteins, "protein", 1)
        evaluated_protein_fields = list(evaluated_protein.keys())
        self.assertEqual(evaluated_protein_fields, ["protein_id", "go_terms"])
        pass
