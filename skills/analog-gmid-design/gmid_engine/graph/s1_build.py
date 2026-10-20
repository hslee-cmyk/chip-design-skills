"""S1 생성 (설계 design_mod3_s1_graph 5.2, design_mod3_structure_u2_u5 4.0, 확정 사항 1·2·5).

진입점: `build_s1(doc, supplies_v=None, previous=None, column_limit=None, *, structure=None, marks=NO_MARKS, donors, counters) -> S1Graph`.

* `donors`·`counters`: 필수 키워드(기본값 없음) -- 호출자가 `search.open_run()` 으로 만든 실행 하나의 블록 결과 색인·계수(설계 40 §2.4.5 '전달').
  13개 계산 블록에 그대로 넘긴다. 같은 실행의 같은 입력이면 계보와 무관하게 이식되어 다시 계산하지 않는다.

* `doc`: `authoring.load_topology` 결과 `TopologyDoc`(파일을 다시 읽지 않는다). `supplies_v`: {레일 넷: 전위} 또는
  None(`supplies_declaration` 이 검사·정규화). topology 의 `_` 주석 키는 읽지 않는다.
* `column_limit`: 기둥 열거 상한(0 이상 int) 또는 None(상한 없음) -- 열린 결정 O1 기본안. S1Key 에 넣지 않는다(spec·시간
  예산은 S1 키 밖). 열거 수가 넘으면 `s1_columns` 가 정지하고, 정지 결과는 캐시되지 않는다(예외).
* `previous`: 이전 S1Graph(같은 실행에서 이미 만든 것) 또는 S0 수준 스냅샷(실행마다 처음 만드는 빈 S0 수준 스냅샷 --
  권한표가 `S1_WRITERS` 를 덮는 `GraphSnapshot`, 설계 40 §2.4.1·§2.4.2·§2.4.3. 결과 S1Graph 는 그 권한표를 그대로 갖는다). 스냅샷이면 키 비교 없이 그 위에서 아래 순서의 블록을 모두 부른다 -- 같은 실행 안에서 이미 부른 블록은
  입력 버전 일치로 재사용되어 계산 0 이다(실행 사이 재사용은 없다 -- 실행마다 빈 스냅샷에서 시작한다). S1Graph 이고 키(`S1Key`)가 같고 `previous` 의 기둥 수가 `column_limit` 이하(또는
  None)면 **그 객체를 그대로** 돌려준다(계산 0). 아니면 그 스냅샷 위에서 계산 블록을 부른다 -- 입력 버전이 같은 블록은
  재사용되고(예: supplies_v 만 바뀌면 `s1_bulk` 만 재계산, U2~U4 블록은 bulk·supplies 를 읽지 않아 전부 재사용), 바뀌지 않은
  레코드는 이전 스냅샷과 같은 객체다(구조 공유). `previous` 없이 같은 doc 으로 두 번 부르면 같은 실행(같은 `donors`)에서는 두 번째가
  블록 결과 색인에서 이식되어(계수 graft) 계산 0 이다 -- 다른 실행(다른 `open_run()` 쌍)과는 아무것도 나누지 않는다.
* `structure`: `load_structure_facts` 결과(`StructureFacts`) 또는 None. S1 이 소비하는 ratified 사실 -- `dc_role`(`s1_dc_roles` 규칙 4)과 `matching_pair`
  (`s1_matching_groups` 레코드 추가) -- 만 뽑아 두 블록에 넘기고, 그 지문을 S1 키(`facts_fp`, `s1_key`)에 넣는다(같은 topology 라도 사실이 다르면 S1 이 다르다, 40 §3.2-3).
  `drive_kind`·`ac_ground_exception`·`loop_role`·`feedforward_cell`·`stage_members` 는 S1v 쪽 사실이다(`build_s1v`).
* `marks`: 대칭 블록(`s1_symmetry`)이 보존할 사람 선언 표시 `SymmetryMarks`(기본 `NO_MARKS` -- spec 없음). 지문은 S1 키(`marks_fp`)에 들어간다(40 §6-8 D-2: 궤도·구조 색·
  전류 부호를 S1 하나에서 정한다).
* 순서(고정): supplies 검사 -> 키 -> structure -> bulk -> dc_conduction -> gs_groups -> branches -> dc_roles -> rel_vgs
  -> rel_matching -> matching_groups -> gvgs -> columns -> rel_kcl -> symmetry(대칭 블록, d/s 자기 맞바꿈이면 정지).
"""
import json

from gmid_engine.authoring import TopologyDoc
from gmid_engine.core import GraphSnapshot, sorted_items

from .branches import s1_branches
from .bulk_default import s1_bulk
from .columns import s1_columns
from .dc_conduction import s1_dc_conduction
from .dc_roles import s1_dc_roles
from .gs_groups import s1_gs_groups
from .gvgs_cycles import s1_gvgs
from .matching_groups import s1_matching_groups
from .rel_kcl import s1_rel_kcl
from .rel_matching import s1_rel_matching
from .rel_vgs import s1_rel_vgs
from .s1_key import s1_key
from .s1_model import S1Graph
from .s1_structure import s1_structure
from .s1_symmetry import s1_symmetry
from .s1_values import GRAPH_KEY, NO_MARKS, S1_WRITERS, SymmetryMarks
from .s1v_values import CONCEPT_DC_ROLE, CONCEPT_MATCHING_PAIR
from .supplies import supplies_declaration


def _s1_facts(structure):
    """(dc_role 사실, matching_pair 사실) -- 불변 tuple. dc_role = (소자, 값, approval_id, 근거 넷), matching_pair = (멤버 이름 tuple, approval_id, 근거 넷)."""
    facts = () if structure is None else structure.facts
    dc = tuple((f.subject, f.value, f.approval_id, tuple(f.nets)) for f in facts if f.concept == CONCEPT_DC_ROLE)
    pairs = tuple((tuple(json.loads(f.subject)), f.approval_id, tuple(f.nets)) for f in facts if f.concept == CONCEPT_MATCHING_PAIR)
    return dc, pairs


def build_s1(doc, supplies_v=None, previous=None, column_limit=None, *, structure=None, marks=NO_MARKS, donors, counters):
    if not isinstance(doc, TopologyDoc):
        raise TypeError("build_s1: doc 는 authoring.load_topology 가 만든 TopologyDoc 이어야 한다")
    base_snapshot = previous.snapshot if isinstance(previous, S1Graph) else previous
    if previous is not None and (not isinstance(base_snapshot, GraphSnapshot) or not base_snapshot.writers.covers(S1_WRITERS)):
        raise TypeError("build_s1: previous 는 권한표가 S1_WRITERS 를 덮는 S1Graph 또는 GraphSnapshot 이어야 한다")
    if column_limit is not None and (isinstance(column_limit, bool) or not isinstance(column_limit, int)
                                     or column_limit < 0):
        raise TypeError("build_s1: column_limit 는 None 또는 0 이상 int 여야 한다")
    if not isinstance(marks, SymmetryMarks):
        raise TypeError("build_s1: marks 는 SymmetryMarks 여야 한다")
    supplies = supplies_declaration(supplies_v, doc.rails)
    dc_facts, pair_facts = _s1_facts(structure)
    key = s1_key(doc, supplies, (dc_facts, pair_facts), marks)
    if isinstance(previous, S1Graph) and previous.key == key and (
            column_limit is None or len(previous.value("graph", GRAPH_KEY, "columns")) <= column_limit):
        return previous
    snapshot = GraphSnapshot.empty(S1_WRITERS) if previous is None else base_snapshot
    snapshot = s1_structure(snapshot, doc.devices, doc.passives, doc.sources, sorted_items(doc.rails), doc.ports, donors=donors, counters=counters)
    snapshot = s1_bulk(snapshot, supplies, donors=donors, counters=counters)
    snapshot = s1_dc_conduction(snapshot, donors=donors, counters=counters)
    snapshot = s1_gs_groups(snapshot, donors=donors, counters=counters)
    snapshot = s1_branches(snapshot, donors=donors, counters=counters)
    snapshot = s1_dc_roles(snapshot, dc_facts, donors=donors, counters=counters)
    snapshot = s1_rel_vgs(snapshot, donors=donors, counters=counters)
    snapshot = s1_rel_matching(snapshot, donors=donors, counters=counters)
    snapshot = s1_matching_groups(snapshot, pair_facts, donors=donors, counters=counters)
    snapshot = s1_gvgs(snapshot, donors=donors, counters=counters)
    snapshot = s1_columns(snapshot, column_limit, donors=donors, counters=counters)
    snapshot = s1_rel_kcl(snapshot, donors=donors, counters=counters)
    snapshot = s1_symmetry(snapshot, supplies, marks, donors=donors, counters=counters)
    return S1Graph(key, snapshot)
