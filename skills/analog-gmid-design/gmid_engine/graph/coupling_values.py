"""GB3 결합 변수 y 와 기둥↔블록 매핑표의 값 형식·어휘 -- 데이터 선언 모듈 (설계 40 §3.3, 계획 DEC-71 (2)(7), 41 §5.5).

공개 정의는 frozen dataclass·예외 이유 상수·어휘 상수뿐이다(규칙 A 데이터 선언 모듈). 모든 값은 tuple·frozen dataclass 라 `fp_of` 로 지문한다.

* `BlockRef(view, key)` -- 블록 하나를 가리키는 값: 뷰 id 와 블록 키(출력노드 이름 정렬 tuple). 같은 키의 블록도 뷰가 다르면 다른 블록이다.
* `ColumnBlockRow(column, block, device, shared, basis)` -- 매핑표 한 행(DEC-71 (2)): S1 기둥 id, 블록(바이어스 기둥이면 None), 소자, 공유 소자 표시, 귀속 근거.
  `column` 이 None 이면 어느 기둥에도 들지 않지만(DC 엣지가 없는 커패시터 등) 블록 멤버인 소자의 행이다.
* `CouplingVar(kind, members, blocks, domain, init_rule, nets)` -- 결합 변수 y 한 개(40 §3.3). `kind` ∈ COUPLING_KINDS, `members` = 관련 소자,
  `blocks` = 블록 경계를 실제로 가로지른 뷰들의 블록 `BlockRef` 정렬 tuple, `domain` = S1 영역 어휘(dc·geom), `init_rule` = 조립(41 §5.5)이 y 초기값을 정하는 규칙 이름, `nets` = 관련 넷.
결과는 묶음 객체 없이 S0 수준 필드 `graph/coupling: vars·column_block_map(행 tuple)·bias_columns` 로 쓴다(설계 40 §2.4.8 v1.9.1 D8).
"""
import dataclasses

# ---- 결합 종류 (40 §3.3, 계획 N3.7 결합 표). K5·K6 은 y 가 아니라(GB5·GB8 몫) 여기서 만들지 않는다.
KIND_K1 = "K1"      # 부하 소자가 다른 블록의 미러·L 동치류에 속함
KIND_K2 = "K2"      # 블록을 가로지르는 equal_vgs
KIND_K3 = "K3"      # 블록 경계를 넘는 stacked_vsb (한 소자의 source 가 다른 블록 소자의 drain 인 비레일 넷)
KIND_K4 = "K4"      # 둘 이상 블록의 소자가 한 기둥을 지나는 가지의 노드전압
KIND_K7 = "K7"      # 둘 이상의 뷰가 쓰는 소자
KIND_K8 = "K8"      # 측면 주입
COUPLING_KINDS = (KIND_K1, KIND_K2, KIND_K3, KIND_K4, KIND_K7, KIND_K8)
# ---- init_rule: 조립(41 §5.5)이 y 초기값을 정하는 방법의 이름 (값을 정하는 계산은 U15 몫이고 여기서는 이름만 붙인다)
INIT_CLASS_OWNER = "class_owner_value"          # 동치류 주인·기준 소자의 값을 고정 입력으로 쓰고 조립이 확정(DEC-71 (3)(7))
INIT_COMMON_VGS = "common_vgs_candidates"       # 공유 블록마다 국소 VGS 를 후보로 커널을 돌려 고른다(DEC-10)
INIT_STACK_KVL = "stack_node_kvl"               # 적층 노드전압을 기둥 KVL 로 정한다
INIT_SHARED_NODE = "shared_node_kvl_kcl"        # 공유 가지의 노드전압을 기둥 KVL·분기 노드 KCL 로 정한다
INIT_VIEW_SPLIT = "view_shared_split"           # 뷰가 공유하는 소자의 전류 분할·값
INIT_SIDE_INJECTION = "side_injection_current"  # 측면 주입 셀의 바이어스 전류
# ---- 매핑표 귀속 근거
BASIS_BLOCK_MEMBER = "block_member"             # 소자가 그 블록의 멤버다
BASIS_COLUMN_MATE = "column_mate"               # 블록 멤버가 아니지만 같은 기둥에 그 블록 소자가 있다 -> 그 블록 국소 문제 범위에 넣고 공유 소자로 표시(DEC-71 (2))
BASIS_BIAS_COLUMN = "bias_column"               # 기둥의 모든 소자가 블록 밖 -> 바이어스 기둥으로 등록
# ---- 바이어스 기둥 의사 블록 키 접두 (설계 40 §3.3 as-built)
BIAS_PREFIX = "bias:"
# ---- 정지 이유 (core StructureUnresolvedError detail reason)
REASON_COLUMN_UNASSIGNED = "column_unassigned"


@dataclasses.dataclass(frozen=True, order=True)
class BlockRef:
    """블록 참조: `view` = 뷰 id, `key` = 블록 키(출력노드 이름 정렬 tuple).

    의사 블록(바이어스 기둥): `key` 가 `(BIAS_PREFIX + <기둥 id>,)` 한 원소 tuple 이다. `view` 는 그 의사 블록이 놓인 뷰 id 다
    (판정이 뷰 단위라 모든 뷰에 같은 기둥 의사 블록이 하나씩 있다). repr 에 `bias:<기둥 id>` 가 든다."""

    view: str
    key: tuple


@dataclasses.dataclass(frozen=True)
class ColumnBlockRow:
    """매핑표 한 행. `column` = S1 기둥 id 또는 None(기둥에 들지 않은 블록 멤버), `block` = BlockRef 또는 None(바이어스 기둥), `device` = 소자 이름,
    `shared` = 공유 소자 표시(둘 이상 기둥에 걸침 · 한 뷰에서 둘 이상 블록에 속함 · 블록 멤버가 아니라 기둥 이웃으로 귀속됨), `basis` ∈ {block_member, column_mate, bias_column}."""

    column: object
    block: object
    device: str
    shared: bool
    basis: str


@dataclasses.dataclass(frozen=True)
class CouplingVar:
    """결합 변수 y 한 개. `kind` ∈ COUPLING_KINDS, `members` = 소자 이름 tuple, `blocks` = BlockRef 정렬 tuple, `domain` ∈ {dc, geom}, `init_rule` = INIT_*, `nets` = 관련 넷 정렬 tuple."""

    kind: str
    members: tuple
    blocks: tuple
    domain: str
    init_rule: str
    nets: tuple = ()
