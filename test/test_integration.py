import json
import os
import sys

import networkx as nx
import pytest

import pandas as pd
import pyarrow.parquet as pq

from biocypher._ontology import Ontology


def get_parquet_content_as_rows(file_path):
    table = pq.read_table(file_path)
    return [tuple(row.values()) for row in table.to_pylist()]


@pytest.mark.parametrize("length", [4], scope="function")
def test_write_node_data_from_gen(core, _get_nodes):
    nodes = _get_nodes

    def node_gen(nodes):
        yield from nodes

    passed = core.write_nodes(node_gen(nodes))
    assert passed

    path = core._output_directory

    protein_data_file = os.path.join(path, "Protein-part000.parquet")
    micro_rna_data_file = os.path.join(path, "MicroRNA-part000.parquet")
    protein_data = get_parquet_content_as_rows(protein_data_file)
    micro_rna_data = get_parquet_content_as_rows(micro_rna_data_file)

    assert passed
    assert protein_data[0][:-1] == ("p1", "StringProperty1", 4.0, 9606, ["gene1", "gene2"], "p1", "uniprot")
    assert "BiologicalEntity" in protein_data[0][-1]
    assert micro_rna_data[0][:-1] == ("m1", "StringProperty1", 9606, "m1", "mirbase")
    assert "ChemicalEntity" in micro_rna_data[0][-1]


def test_show_ontology_structure_kwargs(core):
    treevis = core.show_ontology_structure(full=True)

    assert treevis is not None


def test_ontology_without_schema_config(core_no_schema):
    assert core_no_schema

    core_no_schema._head_ontology = {
        "url": "test/ontologies/sem.file",  # any file suffix
        "root_node": "Core",
        "format": "rdf",
    }
    core_no_schema._ontology_mapping = None

    core_no_schema._get_ontology()

    assert isinstance(core_no_schema._ontology, Ontology)
    assert isinstance(core_no_schema._ontology._nx_graph, nx.DiGraph)


@pytest.mark.parametrize("length", [4], scope="function")
def test_write_schema_info_as_node(core, _get_nodes):
    core.write_nodes(_get_nodes)

    schema = core.write_schema_info(as_node=True)

    header_path = os.path.join(core._output_directory, "Schema_info-header.csv")
    assert os.path.exists(header_path)
    schema_path = os.path.join(core._output_directory, "Schema_info-part000.parquet")
    assert os.path.exists(schema_path)

    with open(header_path) as f:
        schema_header = f.read()

    assert "schema_info" in schema_header

    # read schema_path with pandas
    schema_df = pd.read_parquet(schema_path)

    # get the second column of the first row and decode from json dumps format
    string = schema_df.iloc[0, 1]
    schema_part = json.loads(string)

    assert schema_part == schema

    # test import call
    if sys.platform.startswith("win"):
        import_call_filename = "neo4j-admin-import-call.ps1"
    else:
        import_call_filename = "neo4j-admin-import-call.sh"
    import_call_path = os.path.join(core._output_directory, import_call_filename)
    assert os.path.exists(import_call_path)
    with open(import_call_path) as f:
        import_call = f.read()

    assert "Schema_info" in import_call
