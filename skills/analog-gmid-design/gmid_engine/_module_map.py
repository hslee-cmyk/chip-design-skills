"""모듈 지도 매니페스트 -- 파일마다 책임·진입점·계획 ID·계산 블록, 패키지 순서와 패키지 안 층 순서 (설계 요건 1.2 (나) 2·3, 3.1).

진입점: `ModuleEntry`.

* `PACKAGE_ORDER`: 패키지 간 import 는 이 tuple 에서 앞(작은 위치) 쪽으로만 한다.
* `LAYERS`: 패키지마다 층의 tuple, 층 = 파일 이름 tuple. 패키지 안 import 는 앞 층 쪽으로만, 같은 층끼리 금지.
  층 번호는 tuple 위치다(숫자를 박지 않는다).
* `MODULES`: 엔진 파일(`__init__.py` 제외)마다 ModuleEntry 하나. 지도에 없는 파일·파일 없는 항목은 구조 test 가 FAIL.
"""
import dataclasses

PACKAGE_ORDER = (
    "core",
    "lut",
    "authoring",
    "graph",
    "sizing",
    "metrics",
    "search",
    "layout",
    "convergence",
    "report",
    "pipeline",
)


@dataclasses.dataclass(frozen=True)
class ModuleEntry:
    """`path`: gmid_engine 기준 상대 경로(`/` 구분). `kind`: "entry"(독립 진입점 1개), "data"(데이터 선언 모듈 --
    공개 정의가 전부 dataclass/NamedTuple/Enum/Exception 클래스, 한 개념으로 셈) 또는 "helper"(공용 helper, 규칙 B 예외).
    `entry_point`: 그 파일의 독립 진입점 이름(data·helper 는 None). `compute_block`: 그 파일의 계산 블록
    이름(없으면 None, 규칙 C -- 파일당 최대 1). `plan_ids`: 구현하는 계획·설계 ID."""

    path: str
    kind: str
    entry_point: object
    responsibility: str
    plan_ids: tuple
    compute_block: object = None


LAYERS = (
    (
        "core",
        (
            ("determinism.py", "fingerprint.py", "immutability.py", "margin.py", "writer_error.py"),
            ("bounded_lru.py", "failure_record.py", "field_value.py", "projection.py", "writer_table.py"),
            ("compute_block.py", "failure_errors.py", "graph_record.py"),
            ("failure_classes.py", "graph_snapshot.py"),
            ("canon_pointer.py", "exit_code.py"),
        ),
    ),
    (
        "authoring",
        (
            ("topology_model.py", "_terminal_nets.py"),
            ("_rejection.py", "_two_terminal.py", "dc_edges.py", "linked_files.py", "name_uniqueness.py",
             "topology_schema.py"),
            ("devices.py", "hidden_rails.py", "ideal_sources.py", "json_read.py", "passives.py", "ports.py",
             "rails.py"),
            ("topology_load.py",),
        ),
    ),
)

MODULES = (
    ModuleEntry("core/determinism.py", "entry", "sorted_items",
                "정렬된 tuple 순회 도우미", ("NFR-4", "IC2")),
    ModuleEntry("core/fingerprint.py", "entry", "fp_of",
                "정준 직렬화(float.hex·키 정렬)와 sha256 내용 지문", ("NFR-2", "SC-d")),
    ModuleEntry("core/immutability.py", "entry", "require_immutable",
                "graph 값·블록 인자·memo 키의 불변 검사", ("SC-a", "SC-b", "IC10", "DF-13")),
    ModuleEntry("core/margin.py", "entry", "normalized_margin",
                "실패 margin 정규화(위반 크기 / 허용오차)", ("N3.14", "IC9")),
    ModuleEntry("core/writer_error.py", "entry", "WriterPermissionError",
                "writer 권한 위반 예외", ("N3.4", "SC-a")),
    ModuleEntry("core/bounded_lru.py", "entry", "BoundedLRU",
                "graph 밖 순수 함수(LUT 조회) 전용 상한 LRU memo와 계수", ("NFR-2", "WP-10", "DF-07", "DF-13")),
    ModuleEntry("core/failure_record.py", "entry", "FailureRecord",
                "실패 레코드 {class, devices, margin, detail}", ("N3.14",)),
    ModuleEntry("core/field_value.py", "entry", "FieldValue",
                "graph 필드 값과 writer·입력 버전·쓰기 횟수", ("SC-b", "N3.3")),
    ModuleEntry("core/projection.py", "entry", "Projection",
                "계산 블록 입력 투영(선언 열 + 추가 인자)과 그 지문", ("SC-e", "NFR-2")),
    ModuleEntry("core/writer_table.py", "entry", "WriterTable",
                "(kind, field) 마다 writer 하나인 권한표", ("N3.4", "SC-a")),
    ModuleEntry("core/compute_block.py", "entry", "compute_block",
                "계산 블록 데코레이터: 투영 입력, 입력 버전 같으면 재사용, graph setter 로만 기록, 계수",
                ("NFR-2", "SC-a", "SC-b", "SC-d", "SC-e")),
    ModuleEntry("core/failure_errors.py", "data", None,
                "N3.14 예외 클래스 모음(데이터 선언 모듈)", ("N3.14",)),
    ModuleEntry("core/failure_classes.py", "data", None,
                "N3.14 분류표·후보 실패 클래스·예상 밖 exit code(데이터 선언 모듈)", ("N3.14",)),
    ModuleEntry("core/exit_code.py", "entry", "exit_code_for",
                "예외 -> N3.14 exit code", ("N3.14",)),
    ModuleEntry("core/graph_record.py", "entry", "GraphRecord",
                "graph 레코드(노드·소자·엣지·graph) 불변 필드 묶음", ("N3.3",)),
    ModuleEntry("core/graph_snapshot.py", "entry", "GraphSnapshot",
                "불변 graph 스냅샷: 구조 공유 갱신, writer 권한, block 입력 버전", ("N3.3", "N3.4", "SC-a", "SC-b")),
    ModuleEntry("core/canon_pointer.py", "entry", "CanonPointer",
                "현재 정본 = 채택 스냅샷 포인터", ("N3.3",)),
    ModuleEntry("authoring/topology_model.py", "data", None,
                "topology 로드 결과 불변 형식(SchemaHit·선언 투영·DcEdge·TopologyDoc, 데이터 선언 모듈)",
                ("MOD2", "IC4", "NFR-2")),
    ModuleEntry("authoring/_terminal_nets.py", "helper", None,
                "단자 넷 집합(MOS d/g/s/bulk, 2단자 원소 terminals)", ("MOD2",)),
    ModuleEntry("authoring/_rejection.py", "helper", None,
                "로드 게이트 위반 묶음 -> SchemaRejectedError 한 형식", ("MOD2", "C00-6.2")),
    ModuleEntry("authoring/_two_terminal.py", "helper", None,
                "2단자 원소(수동소자·이상원) 목록 읽기·검사", ("MOD2", "J9")),
    ModuleEntry("authoring/dc_edges.py", "entry", "dc_edges_unpruned",
                "DC 전도 엣지 유일 정의(가지치기 전)", ("DEC-70",)),
    ModuleEntry("authoring/linked_files.py", "entry", "check_linked_files",
                "linked_topology_files 비어 있지 않으면 거부", ("DEC-76",)),
    ModuleEntry("authoring/name_uniqueness.py", "entry", "check_name_uniqueness",
                "소자·수동소자·이상원 이름 유일성(IC3)", ("IC3",)),
    ModuleEntry("authoring/topology_schema.py", "entry", "check_topology_schema",
                "최상위 키 화이트리스트·schema_version·topology_name", ("MOD2", "IC4")),
    ModuleEntry("authoring/devices.py", "entry", "device_declaration",
                "netlist MOS 소자 선언 접근자(원소 키·형식)", ("MOD2",)),
    ModuleEntry("authoring/hidden_rails.py", "entry", "check_hidden_rails",
                "레일 선언 넷 존재 + 숨은 레일 (iii)", ("DEC-60",)),
    ModuleEntry("authoring/ideal_sources.py", "entry", "source_declaration",
                "ideal_sources 선언 접근자", ("MOD2", "DEC-76")),
    ModuleEntry("authoring/json_read.py", "entry", "load_json_checked",
                "엄격 JSON 읽기(BOM·UTF-8·중복 키·유한 수)", ("C00-6.2",)),
    ModuleEntry("authoring/passives.py", "entry", "passive_declaration",
                "passive_elements 선언 접근자(키 필수 -- CI-12 기본안)", ("J9", "CI-12", "DEC-59")),
    ModuleEntry("authoring/ports.py", "entry", "port_declaration",
                "ports 선언 접근자(방향·역할·넷 존재·레일 아님·입출력 각 1 이상)", ("U-08",)),
    ModuleEntry("authoring/rails.py", "entry", "rail_declaration",
                "supply_nets 레일 선언 접근자(B26-1 이식)", ("DEC-60", "B26-1")),
    ModuleEntry("authoring/topology_load.py", "entry", "load_topology",
                "모든 로드 게이트 실행·위반 일괄 거부·TopologyDoc 생성", ("MOD2", "C00-6.2")),
)
