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
    request_dict = {
        key: request_dict[key] for key in request_dict if request_dict[key] is not None
    }
    response = c.post(request_url, request_dict)
    return response.json()["results"][0]["query_handle"]


def get_all(output_type: str):
    request_url = base_url + output_type + "/"
    request_dict = {}
    response = c.post(request_url, request_dict)
    return response.json()["results"][0]["query_handle"]


def set_count(set_key: str, set_type: str) -> str:
    request_url = base_url + "count/"
    request_dict = {"key": set_key, "set_type": set_type}
    response = c.post(request_url, request_dict)
    return response.json()["results"][0]["count"]


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
    response_json = c.post(request_url, request_dict).json()["results"]
    return response_json


def get_response_code(request_url, request_dict):
    response = c.post(request_url, request_dict)
    return response.status_code


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
    request_dict = {
        key: request_dict[key] for key in request_dict if request_dict[key] is not None
    }

    response_json = c.post(request_url, request_dict).json()["results"]
    return response_json  # Returns the key to be used in future computations


class CellTestCase(TestCase):
    fixtures = [
        "cell.json",
        "celltype.json",
        "cluster.json",
        "dataset.json",
        "gene.json",
        "modality.json",
        "organ.json",
        "protein.json",
    ]

    def test_all_cells(self):
        all_cells = get_all("cell")
        all_cells_count = set_count(all_cells, "cell")
        self.assertEqual(all_cells_count, 1230)

    def test_cells_from_cells(self):
        input_set = [
            "0576b972e074074b4c51a61c3d17a6e3-AATGGCTTCTCGACGG",
            "0576b972e074074b4c51a61c3d17a6e3-AGAAGTACACTGCACG",
        ]
        cells = hubmap_query(input_type="cell", output_type="cell", input_set=input_set)
        cells_count = set_count(cells, "cell")
        self.assertEqual(cells_count, 2)

    def test_cells_from_organs(self):
        input_set = ["Heart"]
        organ_cells = hubmap_query(input_type="organ", output_type="cell", input_set=input_set)
        organ_cells_count = set_count(organ_cells, "cell")
        self.assertEqual(organ_cells_count, 10)

    def test_cells_from_datasets(self):
        input_set = ["0576b972e074074b4c51a61c3d17a6e3"]
        dataset_cells = hubmap_query(input_type="dataset", output_type="cell", input_set=input_set)
        dataset_cells_count = set_count(dataset_cells, "cell")
        self.assertEqual(dataset_cells_count, 10)

    def test_cells_from_modalities(self):
        input_set = ["rna"]
        modality_cells = hubmap_query(
            input_type="modality", output_type="cell", input_set=input_set
        )
        modality_cells_count = set_count(modality_cells, "cell")
        self.assertEqual(modality_cells_count, 1100)

    def test_cells_from_organs(self):
        input_set = ["Heart"]
        organ_cells = hubmap_query(input_type="organ", output_type="cell", input_set=input_set)
        organ_cells_count = set_count(organ_cells, "cell")
        self.assertEqual(organ_cells_count, 50)

    def test_cells_from_datasets(self):
        input_set = ["0576b972e074074b4c51a61c3d17a6e3"]
        dataset_cells = hubmap_query(input_type="dataset", output_type="cell", input_set=input_set)
        dataset_cells_count = set_count(dataset_cells, "cell")
        self.assertEqual(dataset_cells_count, 10)

    def test_cells_from_cell_types(self):
        input_set = ["Mesangial Cell"]
        cell_type_cells = hubmap_query(
            input_type="cell_type", output_type="cell", input_set=input_set
        )
        cell_type_cells_count = set_count(cell_type_cells, "cell")
        self.assertEqual(cell_type_cells_count, 2)


class GeneTestCase(TestCase):
    fixtures = [
        "gene.json",
    ]

    def test_all_genes(self):
        all_genes = get_all("gene")
        all_genes_count = set_count(all_genes, "gene")
        self.assertEqual(all_genes_count, 11)

    def test_genes_from_genes(self):
        input_set = ["ABHD17A"]
        genes = hubmap_query(input_type="gene", output_type="gene", input_set=input_set)
        genes_count = set_count(genes, "gene")
        self.assertEqual(genes_count, 1)


class OrganTestCase(TestCase):
    fixtures = [
        "cell.json",
        "celltype.json",
        "cluster.json",
        "dataset.json",
        "modality.json",
        "organ.json",
    ]

    def test_all_organs(self):
        all_organs = get_all("organ")
        all_organs_count = set_count(all_organs, "organ")
        self.assertEqual(all_organs_count, 10)

    def test_organs_from_cells(self):
        input_set = [
            "0576b972e074074b4c51a61c3d17a6e3-AATGGCTTCTCGACGG",
            "0576b972e074074b4c51a61c3d17a6e3-AGAAGTACACTGCACG",
        ]
        cell_organs = hubmap_query(input_type="cell", output_type="organ", input_set=input_set)
        cell_organs_count = set_count(cell_organs, "organ")
        self.assertEqual(cell_organs_count, 1)

    def test_organs_from_organs(self):
        input_set = ["Heart"]
        organs = hubmap_query(input_type="organ", output_type="organ", input_set=input_set)
        organs_count = set_count(organs, "organ")
        self.assertEqual(organs_count, 1)

    def test_organs_from_datasets(self):
        input_set = ["0576b972e074074b4c51a61c3d17a6e3"]
        organs = hubmap_query(input_type="dataset", output_type="organ", input_set=input_set)
        organs_count = set_count(organs, "organ")
        self.assertEqual(organs_count, 1)

    def test_organs_from_clusters(self):
        input_set = [
            "leiden-UMAP-0576b972e074074b4c51a61c3d17a6e3-7",
            "leiden-UMAP-0576b972e074074b4c51a61c3d17a6e3-5",
        ]
        organs = hubmap_query(input_type="cluster", output_type="organ", input_set=input_set)
        organs_count = set_count(organs, "organ")
        self.assertEqual(organs_count, 1)

    def test_organs_from_cell_types(self):
        input_set = ["Mesangial Cell"]
        cell_type_organs = hubmap_query(
            input_type="cell_type", output_type="organ", input_set=input_set
        )
        cell_type_organs_count = set_count(cell_type_organs, "organ")
        self.assertEqual(cell_type_organs_count, 1)


class DatasetTestCase(TestCase):
    fixtures = [
        "cell.json",
        "celltype.json",
        "cluster.json",
        "dataset.json",
        "modality.json",
        "organ.json",
    ]

    def test_all_datasets(self):
        all_datasets = get_all("dataset")
        all_datasets_count = set_count(all_datasets, "dataset")
        self.assertEqual(all_datasets_count, 170)

    def test_datasets_from_cells(self):
        input_set = [
            "0576b972e074074b4c51a61c3d17a6e3-AATGGCTTCTCGACGG",
            "0576b972e074074b4c51a61c3d17a6e3-AGAAGTACACTGCACG",
        ]
        cell_datasets = hubmap_query(input_type="cell", output_type="dataset", input_set=input_set)
        cell_datasets_count = set_count(cell_datasets, "organ")
        self.assertEqual(cell_datasets_count, 1)

    def test_datasets_from_datasets(self):
        input_set = ["0576b972e074074b4c51a61c3d17a6e3", "d4493657cde29702c5ed73932da5317c"]
        datasets_from_datasets = hubmap_query("dataset", "dataset", input_set)
        datasets_from_datasets_count = set_count(datasets_from_datasets, "dataset")
        self.assertEqual(datasets_from_datasets_count, 2)

    def test_datasets_from_clusters(self):
        input_set = [
            "leiden-UMAP-0576b972e074074b4c51a61c3d17a6e3-7",
            "leiden-UMAP-0576b972e074074b4c51a61c3d17a6e3-5",
        ]
        datasets_from_clusters = hubmap_query("cluster", "dataset", input_set)
        datasets_from_clusters_count = set_count(datasets_from_clusters, "dataset")
        self.assertEqual(datasets_from_clusters_count, 1)

    def test_datasets_from_modalities(self):
        input_set = ["codex"]
        modality_datasets = hubmap_query(
            input_type="modality", output_type="dataset", input_set=input_set
        )
        modality_datasets_count = set_count(modality_datasets, "cell")
        self.assertEqual(modality_datasets_count, 47)

    def test_datasets_from_organs(self):
        input_set = ["Heart"]
        organ_datasets = hubmap_query(
            input_type="organ", output_type="dataset", input_set=input_set
        )
        organ_datasets_count = set_count(organ_datasets, "cell")
        self.assertEqual(organ_datasets_count, 5)

    def test_datasets_from_cell_types(self):
        input_set = ["Mesangial Cell"]
        cell_type_datasets = hubmap_query(
            input_type="cell_type", output_type="dataset", input_set=input_set
        )
        cell_type_datasets_count = set_count(cell_type_datasets, "dataset")
        self.assertEqual(cell_type_datasets_count, 2)


class ClusterTestCase(TestCase):
    fixtures = [
        "cell.json",
        "celltype.json",
        "cluster.json",
        "dataset.json",
        "modality.json",
        "organ.json",
    ]

    def test_all_clusters(self):
        all_clusters = get_all("cluster")
        all_clusters_count = set_count(all_clusters, "cluster")
        self.assertEqual(all_clusters_count, 1795)

    def test_clusters_from_cells(self):
        input_set = ["0576b972e074074b4c51a61c3d17a6e3-AATGGCTTCTCGACGG"]
        clusters_from_cells = hubmap_query("cell", "cluster", input_set)
        clusters_from_cells = set_count(clusters_from_cells, "cluster")
        self.assertEqual(clusters_from_cells, 2)

    def test_clusters_from_datasets(self):
        input_set = ["d4493657cde29702c5ed73932da5317c"]
        clusters_from_datasets = hubmap_query("dataset", "cluster", input_set)
        clusters_from_datasets_count = set_count(clusters_from_datasets, "cluster")
        self.assertEqual(clusters_from_datasets_count, 9)

    def test_clusters_from_clusters(self):
        input_set = [
            "leiden-UMAP-d4493657cde29702c5ed73932da5317c-1",
            "leiden-UMAP-d4493657cde29702c5ed73932da5317c-8",
        ]
        clusters_from_clusters = hubmap_query("cluster", "cluster", input_set)
        clusters_from_clusters_count = set_count(clusters_from_clusters, "cluster")
        self.assertEqual(clusters_from_clusters_count, 2)


class CellTypeTestCase(TestCase):
    fixtures = [
        "cell.json",
        "celltype.json",
        "cluster.json",
        "dataset.json",
        "modality.json",
        "organ.json",
    ]

    def test_all_cell_types(self):
        all_cell_types = get_all("celltype")
        all_cell_types_count = set_count(all_cell_types, "cell_type")
        self.assertEqual(all_cell_types_count, 40)

    def test_cell_types_from_cell_types(self):
        input_set = ["Mesangial Cell"]
        cell_type_cell_types = hubmap_query(
            input_type="celltype", output_type="celltype", input_set=input_set
        )
        cell_type_cell_types_count = set_count(cell_type_cell_types, "cell_type")
        self.assertEqual(cell_type_cell_types_count, 1)

    def test_cell_types_from_cells(self):
        input_set = ["0576b972e074074b4c51a61c3d17a6e3-AATGGCTTCTCGACGG"]
        cell_types_from_cells = hubmap_query("cell", "celltype", input_set)
        cell_types_from_cells = set_count(cell_types_from_cells, "cell_type")
        self.assertEqual(cell_types_from_cells, 1)

    def test_cell_types_from_datasets(self):
        input_set = ["0576b972e074074b4c51a61c3d17a6e3"]
        cell_types_from_datasets = hubmap_query("dataset", "celltype", input_set)
        cell_types_from_datasets_count = set_count(cell_types_from_datasets, "cell_type")
        self.assertEqual(cell_types_from_datasets_count, 1)

    def test_cell_types_from_organs(self):
        input_set = ["Kidney"]
        organ_cell_types = hubmap_query(
            input_type="organ", output_type="celltype", input_set=input_set
        )
        organ_cell_types_count = set_count(organ_cell_types, "cell_type")
        self.assertEqual(organ_cell_types_count, 5)


class ProteinTestCase(TestCase):
    fixtures = [
        "protein.json",
    ]

    def test_all_proteins(self):
        all_proteins = get_all("protein")
        all_proteins_count = set_count(all_proteins, "protein")
        self.assertEqual(all_proteins_count, 65)

    def test_proteins_from_proteins(self):
        input_set = ["CD107a", "CD11c"]
        proteins_from_proteins = hubmap_query("protein", "protein", input_set)
        proteins_from_proteins_count = set_count(proteins_from_proteins, "protein")
        self.assertEqual(proteins_from_proteins_count, 2)


class OperationsTestCase(TestCase):
    fixtures = [
        "cell.json",
        "celltype.json",
        "cluster.json",
        "dataset.json",
        "gene.json",
        "modality.json",
        "organ.json",
        "protein.json",
    ]

    def test_union(self):
        input_set = ["d4493657cde29702c5ed73932da5317c"]
        cells_from_dataset = hubmap_query("dataset", "cell", input_set)
        input_set = ["Spleen"]
        cells_from_organ = hubmap_query("organ", "cell", input_set)
        intersection_cells = set_union(cells_from_dataset, cells_from_organ, "cell")
        intersection_cells_count = set_count(intersection_cells, "cell")
        self.assertEqual(intersection_cells_count, 180)


class ListEvaluationTestCase(TestCase):
    fixtures = [
        "cell.json",
        "celltype.json",
        "cluster.json",
        "dataset.json",
        "gene.json",
        "modality.json",
        "organ.json",
        "protein.json",
    ]

    def test_cells(self):
        all_cells = get_all("cell")
        evaluated_cell = set_list_evaluation(all_cells, "cell", 1)[0]
        evaluated_cell_fields = list(evaluated_cell.keys())
        self.assertEqual(
            evaluated_cell_fields,
            ["cell_id", "modality", "dataset", "organ", "cell_type", "clusters"],
        )

    def test_genes(self):
        all_genes = get_all("gene")
        evaluated_gene = set_list_evaluation(all_genes, "gene", 1)[0]
        evaluated_gene_fields = list(evaluated_gene.keys())
        self.assertEqual(evaluated_gene_fields, ["gene_symbol", "go_terms", "summary"])

    def test_organs(self):
        all_organs = get_all("organ")
        evaluated_organ = set_list_evaluation(all_organs, "organ", 1)[0]
        evaluated_organ_fields = list(evaluated_organ.keys())
        self.assertEqual(evaluated_organ_fields, ["grouping_name"])

    def test_clusters(self):
        all_clusters = get_all("cluster")
        evaluated_cluster = set_list_evaluation(all_clusters, "cluster", 1)[0]
        evaluated_cluster_fields = list(evaluated_cluster.keys())
        self.assertEqual(
            evaluated_cluster_fields,
            [
                "cluster_method",
                "cluster_data",
                "grouping_name",
                "dataset",
            ],
        )

    def test_datasets(self):
        all_datasets = get_all("dataset")
        evaluated_dataset = set_list_evaluation(all_datasets, "dataset", 1)[0]
        evaluated_dataset_fields = list(evaluated_dataset.keys())
        self.assertEqual(evaluated_dataset_fields, ["uuid", "annotation_metadata"])

    def test_proteins(self):
        all_proteins = get_all("protein")
        evaluated_protein = set_list_evaluation(all_proteins, "protein", 1)[0]
        evaluated_protein_fields = list(evaluated_protein.keys())
        self.assertEqual(evaluated_protein_fields, ["protein_id", "go_terms", "summary"])

    def test_cell_type(self):
        all_cell_types = get_all("celltype")
        evaluated_cell_type = set_list_evaluation(all_cell_types, "cell_type", 1)[0]
        evaluated_cell_type_fields = list(evaluated_cell_type.keys())
        self.assertEqual(evaluated_cell_type_fields, ["grouping_name"])


class DetailEvaluationTestCase(TestCase):
    fixtures = [
        "cell.json",
        "celltype.json",
        "cluster.json",
        "dataset.json",
        "gene.json",
        "modality.json",
        "organ.json",
        "protein.json",
    ]

    def test_cells(self):
        all_cells = get_all("cell")
        evaluated_cell = set_detail_evaluation(all_cells, "cell", 1)[0]
        evaluated_cell_fields = list(evaluated_cell.keys())
        self.assertEqual(
            evaluated_cell_fields,
            ["cell_id", "modality", "dataset", "organ", "cell_type", "clusters", "values"],
        )

    def test_genes(self):
        all_genes = get_all("gene")
        evaluated_gene = set_detail_evaluation(all_genes, "gene", 1)[0]
        evaluated_gene_fields = list(evaluated_gene.keys())
        self.assertEqual(evaluated_gene_fields, ["gene_symbol", "go_terms", "summary", "values"])

    def test_organs(self):
        all_organs = get_all("organ")
        evaluated_organ = set_detail_evaluation(all_organs, "organ", 1)[0]
        evaluated_organ_fields = list(evaluated_organ.keys())
        self.assertEqual(evaluated_organ_fields, ["grouping_name", "values"])

    def test_clusters(self):
        all_clusters = get_all("cluster")
        evaluated_cluster = set_detail_evaluation(all_clusters, "cluster", 1)[0]
        evaluated_cluster_fields = list(evaluated_cluster.keys())
        self.assertEqual(
            evaluated_cluster_fields,
            ["cluster_method", "cluster_data", "grouping_name", "dataset", "values"],
        )

    def test_datasets(self):
        all_datasets = get_all("dataset")
        evaluated_dataset = set_detail_evaluation(all_datasets, "dataset", 1)[0]
        evaluated_dataset_fields = list(evaluated_dataset.keys())
        self.assertEqual(evaluated_dataset_fields, ["uuid", "annotation_metadata", "values"])

    def test_proteins(self):
        all_proteins = get_all("protein")
        evaluated_protein = set_detail_evaluation(all_proteins, "protein", 1)[0]
        evaluated_protein_fields = list(evaluated_protein.keys())
        self.assertEqual(evaluated_protein_fields, ["protein_id", "go_terms", "summary"])

    def test_cell_type(self):
        all_cell_types = get_all("celltype")
        evaluated_cell_type = set_detail_evaluation(all_cell_types, "celltype", 1)[0]
        evaluated_cell_type_fields = list(evaluated_cell_type.keys())
        self.assertEqual(evaluated_cell_type_fields, ["grouping_name"])


class ErrorTestCase(TestCase):
    def test_invalid_input_types(self):
        request_url = base_url + "protein/"
        request_dict = {"input_type": "organ", "input_set": []}
        response_code = get_response_code(request_url, request_dict)
        self.assertEqual(response_code, 400)

    def test_invalid_genomic_modalities(self):
        request_url = base_url + "dataset/"
        request_dict = {
            "input_type": "gene",
            "input_set": ["VIM > 1"],
            "genomic_modality": "fake",
            "min_cell_percentage": 10.0,
        }
        response_code = get_response_code(request_url, request_dict)
        self.assertEqual(response_code, 400)

    def test_invalid_gene_modality_pairing(self):
        request_url = base_url + "dataset/"
        request_dict = {
            "input_type": "gene",
            "input_set": ["BEST1 > 1"],
            "genomic_modality": "rna",
            "min_cell_percentage": 10.0,
        }
        response_code = get_response_code(request_url, request_dict)
        self.assertEqual(response_code, 400)

    def test_invalid_parameters(self):
        request_url = base_url + "dataset/"
        request_dict = {
            "input_type": "gene",
            "input_set": ["BEST1 > 1"],
            "genomic_modality": "rna",
            "min_cell_percentage": 10.0,
            "extra_param": "fake",
        }
        response_code = get_response_code(request_url, request_dict)
        self.assertEqual(response_code, 400)

    def test_missing_parameters(self):
        request_url = base_url + "dataset/"
        request_dict = {
            "input_type": "gene",
            "input_set": ["BEST1 > 1"],
            "min_cell_percentage": 10.0,
        }
        response_code = get_response_code(request_url, request_dict)
        self.assertEqual(response_code, 400)
