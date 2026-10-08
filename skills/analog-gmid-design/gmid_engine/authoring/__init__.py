"""MOD2 authoring -- topology·회로 사이징 spec 로드·스키마·선언 게이트(계획 N3.10 topology_authoring.py, 설계 design_mod3_s1_graph 2.1).

다른 패키지와 test 는 이 `__all__` 만 쓴다. 계약: `CONTRACT.md`.
"""
from .bias_inputs import bias_input_declaration
from .dc_edges import DC_CONDUCTING_PASSIVE_KINDS, dc_edges_unpruned
from .devices import device_declaration
from .hidden_rails import check_hidden_rails
from .ideal_sources import source_declaration
from .json_read import CheckedJson, load_json_checked
from .linked_files import check_linked_files
from .name_uniqueness import check_name_uniqueness
from .passives import passive_declaration
from .cm_partition import CmPartition, cm_partition
from .ports import (
    INPUT_DIRECTION,
    OUTPUT_DIRECTION,
    ROLE_DIFFERENTIAL_INPUT_N,
    ROLE_DIFFERENTIAL_INPUT_P,
    ROLE_DIFFERENTIAL_OUTPUT_N,
    ROLE_DIFFERENTIAL_OUTPUT_P,
    ROLE_SINGLE_ENDED_INPUT,
    port_declaration,
)
from .rails import rail_declaration
from .source_manifest import check_source_manifest
from .spec_constraints import constraint_declaration
from .spec_count_budget import count_budget_declaration
from .spec_driving import driving_declaration
from .spec_elements import element_value_declaration
from .spec_gain_override import gain_override_declaration
from .spec_input_dc import input_dc_declaration
from .spec_load import load_sizing_spec
from .spec_meta import meta_cross_check
from .spec_model import (
    SECTION_GROUPS,
    VIEW_MODE_CM_OUTPUT,
    VIEW_MODE_LOOP,
    VIEW_MODE_NONE,
    VIEW_MODE_PENDING,
    VIEW_MODE_PORT,
    VIEW_MODE_RATIO,
    VIEW_MODE_SENSE,
    VIEW_MODE_TRANSFER,
    VIEW_MODES,
    ConstraintDecl,
    CountBudgetDecl,
    DrivingDecl,
    ElementValue,
    ExciteSense,
    GainOverrideDecl,
    InputDc,
    ObjectiveBudget,
    PendingMark,
    RegionDecl,
    RuleChoice,
    SenseDecl,
    SettingValue,
    SettlingDecl,
    SizingSpecDoc,
    SpecSource,
    TargetDecl,
    ThetaBound,
    ViewDecl,
)
from .spec_views import (
    BETA_DECLARED,
    BETA_UNITY,
    SENSE_DIFFERENTIAL,
    SENSE_MODES,
    SENSE_SINGLE_ENDED,
    DefaultViews,
    default_views,
)
from .spec_node_targets import node_target_declaration
from .spec_refs import resolve_spec_references
from .spec_regions import REGION_TRIODE, intended_region_declaration
from .spec_schema import SPEC_SCHEMA_VERSION, check_spec_schema
from .spec_settings import THETA_BOUNDS, settings_declaration
from .spec_theta_bounds import theta_bound_declaration
from .spec_sources import source_declaration_checks
from .spec_supplies import supplies_declaration
from .spec_targets import compensation_target_declaration
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
    "BETA_DECLARED",
    "BETA_UNITY",
    "CheckedJson",
    "ConstraintDecl",
    "CountBudgetDecl",
    "DC_CONDUCTING_PASSIVE_KINDS",
    "DcEdge",
    "DefaultViews",
    "DeviceDecl",
    "DrivingDecl",
    "ElementValue",
    "ExciteSense",
    "GainOverrideDecl",
    "IGNORED_TAG_KEYS",
    "INPUT_DIRECTION",
    "InputDc",
    "OUTPUT_DIRECTION",
    "ObjectiveBudget",
    "PassiveDecl",
    "PendingMark",
    "PortDecl",
    "REGION_TRIODE",
    "RailDeclaration",
    "RegionDecl",
    "RuleChoice",
    "SCHEMA_VERSION",
    "SECTION_GROUPS",
    "SPEC_SCHEMA_VERSION",
    "SENSE_DIFFERENTIAL",
    "SENSE_MODES",
    "SENSE_SINGLE_ENDED",
    "SchemaHit",
    "SenseDecl",
    "SettingValue",
    "SettlingDecl",
    "SizingSpecDoc",
    "SourceDecl",
    "SpecSource",
    "THETA_BOUNDS",
    "TWO_TERMINAL_NAMES",
    "TargetDecl",
    "ThetaBound",
    "TopologyDoc",
    "VIEW_MODES",
    "VIEW_MODE_CM_OUTPUT",
    "VIEW_MODE_LOOP",
    "VIEW_MODE_NONE",
    "VIEW_MODE_PENDING",
    "VIEW_MODE_PORT",
    "VIEW_MODE_RATIO",
    "VIEW_MODE_SENSE",
    "VIEW_MODE_TRANSFER",
    "ViewDecl",
    "CmPartition",
    "cm_partition",
    "ROLE_DIFFERENTIAL_INPUT_N",
    "ROLE_DIFFERENTIAL_INPUT_P",
    "ROLE_DIFFERENTIAL_OUTPUT_N",
    "ROLE_DIFFERENTIAL_OUTPUT_P",
    "ROLE_SINGLE_ENDED_INPUT",
    "check_hidden_rails",
    "check_linked_files",
    "check_name_uniqueness",
    "check_source_manifest",
    "check_spec_schema",
    "check_topology_schema",
    "bias_input_declaration",
    "compensation_target_declaration",
    "constraint_declaration",
    "count_budget_declaration",
    "dc_edges_unpruned",
    "default_views",
    "device_declaration",
    "driving_declaration",
    "element_value_declaration",
    "gain_override_declaration",
    "input_dc_declaration",
    "intended_region_declaration",
    "load_json_checked",
    "load_sizing_spec",
    "load_topology",
    "meta_cross_check",
    "node_target_declaration",
    "passive_declaration",
    "port_declaration",
    "rail_declaration",
    "resolve_spec_references",
    "settings_declaration",
    "source_declaration",
    "source_declaration_checks",
    "supplies_declaration",
    "theta_bound_declaration",
)
