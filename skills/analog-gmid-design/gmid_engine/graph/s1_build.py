"""S1 생성 (설계 design_mod3_s1_graph 5.2, 확정 사항 1·2·5).

진입점: `build_s1(doc, supplies_v=None, previous=None) -> S1Graph`.

* `doc`: `authoring.load_topology` 결과 `TopologyDoc`(파일을 다시 읽지 않는다). `supplies_v`: {레일 넷: 전위} 또는
  None(`supplies_declaration` 이 검사·정규화). topology 의 `_` 주석 키는 읽지 않는다.
* `previous`: 이전 S1Graph(같은 실행에서 이미 만든 것). 키(`S1Key`)가 같으면 **그 객체를 그대로** 돌려준다(계산 0).
  다르면 그 스냅샷 위에서 계산 블록을 부른다 -- 입력 버전이 같은 블록은 재사용되고(예: supplies_v 만 바뀌면
  구조 블록은 재사용, bulk 블록만 재계산), 바뀌지 않은 레코드는 이전 스냅샷과 같은 객체다(구조 공유).
  `previous` 없이 같은 doc 으로 두 번 부르면 두 번 계산하고 블록 계수 `recomputes_same_input` 이 올라간다 --
  같은 실행의 재사용은 호출자가 이전 S1 을 넘겨서 한다(graph 가 곧 캐시, graph 밖 memo 없음).
* 순서: supplies 검사 -> 키 -> `s1_structure`(노드·원소·인덱스·교류접지·is_diode·unsupported) -> `s1_bulk`.
"""
from gmid_engine.authoring import TopologyDoc
from gmid_engine.core import GraphSnapshot, sorted_items

from .bulk_default import s1_bulk
from .s1_key import s1_key
from .s1_model import S1Graph
from .s1_structure import s1_structure
from .s1_values import S1_WRITERS
from .supplies import supplies_declaration


def build_s1(doc, supplies_v=None, previous=None):
    if not isinstance(doc, TopologyDoc):
        raise TypeError("build_s1: doc 는 authoring.load_topology 가 만든 TopologyDoc 이어야 한다")
    if previous is not None and (not isinstance(previous, S1Graph) or previous.snapshot.writers != S1_WRITERS):
        raise TypeError("build_s1: previous 는 S1_WRITERS 권한표를 쓰는 S1Graph 여야 한다")
    supplies = supplies_declaration(supplies_v, doc.rails)
    key = s1_key(doc, supplies)
    if previous is not None and previous.key == key:
        return previous
    snapshot = GraphSnapshot.empty(S1_WRITERS) if previous is None else previous.snapshot
    snapshot = s1_structure(snapshot, doc.devices, doc.passives, doc.sources, sorted_items(doc.rails), doc.ports)
    snapshot = s1_bulk(snapshot, supplies)
    return S1Graph(key, snapshot)
