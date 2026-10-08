"""S1 생성 (설계 design_mod3_s1_graph 5.2, design_mod3_structure_u2_u5 4.0, 확정 사항 1·2·5).

진입점: `build_s1(doc, supplies_v=None, previous=None, column_limit=None, *, structure=None) -> S1Graph`.

* `doc`: `authoring.load_topology` 결과 `TopologyDoc`(파일을 다시 읽지 않는다). `supplies_v`: {레일 넷: 전위} 또는
  None(`supplies_declaration` 이 검사·정규화). topology 의 `_` 주석 키는 읽지 않는다.
* `column_limit`: 기둥 열거 상한(0 이상 int) 또는 None(상한 없음) -- 열린 결정 O1 기본안. S1Key 에 넣지 않는다(spec·시간
  예산은 S1 키 밖). 열거 수가 넘으면 `s1_columns` 가 정지하고, 정지 결과는 캐시되지 않는다(예외).
* `previous`: 이전 S1Graph(같은 실행에서 이미 만든 것). 키(`S1Key`)가 같고 `previous` 의 기둥 수가 `column_limit` 이하(또는
  None)면 **그 객체를 그대로** 돌려준다(계산 0). 아니면 그 스냅샷 위에서 계산 블록을 부른다 -- 입력 버전이 같은 블록은
  재사용되고(예: supplies_v 만 바뀌면 `s1_bulk` 만 재계산, U2~U4 블록은 bulk·supplies 를 읽지 않아 전부 재사용), 바뀌지 않은
  레코드는 이전 스냅샷과 같은 객체다(구조 공유). `previous` 없이 같은 doc 으로 두 번 부르면 두 번 계산하고 블록 계수
  `recomputes_same_input` 이 올라간다 -- 같은 실행의 재사용은 호출자가 이전 S1 을 넘겨서 한다(graph 가 곧 캐시).
* `structure`: `load_structure_facts` 결과(`StructureFacts`) 또는 None. S1 이 소비하는 ratified 사실 -- `dc_role`(`s1_dc_roles` 규칙 4)과 `matching_pair`
  (`s1_matching_groups` 레코드 추가) -- 만 뽑아 두 블록에 넘기고, 그 지문을 S1 키(`facts_fp`)에 넣는다(같은 topology 라도 사실이 다르면 S1 이 다르다, 40 §3.2-3).
  `drive_kind`·`ac_ground_exception`·`loop_role`·`feedforward_cell`·`stage_members` 는 S1v 쪽 사실이다(`build_s1v`).
* 순서(고정): supplies 검사 -> 키 -> structure -> bulk -> dc_conduction -> gs_groups -> branches -> dc_roles -> rel_vgs
  -> rel_matching -> matching_groups -> gvgs -> columns -> rel_kcl.
"""
import json

from gmid_engine.authoring import TopologyDoc
from gmid_engine.core import GraphSnapshot, fp_of, sorted_items

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
from .s1_values import GRAPH_KEY, NO_FACTS_FP, S1_WRITERS, S1Key
from .s1v_values import CONCEPT_DC_ROLE, CONCEPT_MATCHING_PAIR
from .supplies import supplies_declaration


def _s1_facts(structure):
    """(dc_role 사실, matching_pair 사실) -- 불변 tuple. dc_role = (소자, 값, approval_id, 근거 넷), matching_pair = (멤버 이름 tuple, approval_id, 근거 넷)."""
    facts = () if structure is None else structure.facts
    dc = tuple((f.subject, f.value, f.approval_id, tuple(f.nets)) for f in facts if f.concept == CONCEPT_DC_ROLE)
    pairs = tuple((tuple(json.loads(f.subject)), f.approval_id, tuple(f.nets)) for f in facts if f.concept == CONCEPT_MATCHING_PAIR)
    return dc, pairs


def build_s1(doc, supplies_v=None, previous=None, column_limit=None, *, structure=None):
    if not isinstance(doc, TopologyDoc):
        raise TypeError("build_s1: doc 는 authoring.load_topology 가 만든 TopologyDoc 이어야 한다")
    if previous is not None and (not isinstance(previous, S1Graph) or previous.snapshot.writers != S1_WRITERS):
        raise TypeError("build_s1: previous 는 S1_WRITERS 권한표를 쓰는 S1Graph 여야 한다")
    if column_limit is not None and (isinstance(column_limit, bool) or not isinstance(column_limit, int)
                                     or column_limit < 0):
        raise TypeError("build_s1: column_limit 는 None 또는 0 이상 int 여야 한다")
    supplies = supplies_declaration(supplies_v, doc.rails)
    dc_facts, pair_facts = _s1_facts(structure)
    base = s1_key(doc, supplies)
    key = S1Key(base.topology_fp, base.rule_fp, base.supplies_v_fp, fp_of((dc_facts, pair_facts)) if dc_facts or pair_facts else NO_FACTS_FP)
    if previous is not None and previous.key == key and (
            column_limit is None or len(previous.value("graph", GRAPH_KEY, "columns")) <= column_limit):
        return previous
    snapshot = GraphSnapshot.empty(S1_WRITERS) if previous is None else previous.snapshot
    snapshot = s1_structure(snapshot, doc.devices, doc.passives, doc.sources, sorted_items(doc.rails), doc.ports)
    snapshot = s1_bulk(snapshot, supplies)
    snapshot = s1_dc_conduction(snapshot)
    snapshot = s1_gs_groups(snapshot)
    snapshot = s1_branches(snapshot)
    snapshot = s1_dc_roles(snapshot, dc_facts)
    snapshot = s1_rel_vgs(snapshot)
    snapshot = s1_rel_matching(snapshot)
    snapshot = s1_matching_groups(snapshot, pair_facts)
    snapshot = s1_gvgs(snapshot)
    snapshot = s1_columns(snapshot, column_limit)
    snapshot = s1_rel_kcl(snapshot)
    return S1Graph(key, snapshot)
