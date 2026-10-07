"""MOD2 authoring -- topology 로드·스키마·선언 게이트(계획 N3.10 topology_authoring.py, 설계 design_mod3_s1_graph 2.1).

다른 패키지와 test 는 이 `__all__` 만 쓴다. 계약: `CONTRACT.md`.
"""
from .dc_edges import DC_CONDUCTING_PASSIVE_KINDS, dc_edges_unpruned
from .devices import device_declaration
from .hidden_rails import check_hidden_rails
from .ideal_sources import source_declaration
from .json_read import CheckedJson, load_json_checked
from .linked_files import check_linked_files
from .name_uniqueness import check_name_uniqueness
from .passives import passive_declaration
from .ports import INPUT_DIRECTION, port_declaration
from .rails import rail_declaration
from .topology_load import load_topology
from .topology_model import (
    TWO_TERMINAL_NAMES,
    DcEdge,
    DeviceDecl,
    PassiveDecl,
    PortDecl,
    RailDeclaration,
    SchemaHit,
    SourceDecl,
    TopologyDoc,
)
from .topology_schema import IGNORED_TAG_KEYS, SCHEMA_VERSION, check_topology_schema

__all__ = (
    "CheckedJson",
    "DC_CONDUCTING_PASSIVE_KINDS",
    "DcEdge",
    "DeviceDecl",
    "IGNORED_TAG_KEYS",
    "INPUT_DIRECTION",
    "PassiveDecl",
    "PortDecl",
    "RailDeclaration",
    "SCHEMA_VERSION",
    "SchemaHit",
    "SourceDecl",
    "TWO_TERMINAL_NAMES",
    "TopologyDoc",
    "check_hidden_rails",
    "check_linked_files",
    "check_name_uniqueness",
    "check_topology_schema",
    "dc_edges_unpruned",
    "device_declaration",
    "load_json_checked",
    "load_topology",
    "passive_declaration",
    "port_declaration",
    "rail_declaration",
    "source_declaration",
)
