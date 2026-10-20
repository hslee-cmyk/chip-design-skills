"""MOD7 이름 정준 별칭 번역 데코레이터 (사용자 대원칙 '이름에 종속된 엔진 금지', U12 -- 사용자 지시 2026-10-09; 설계 40 v1.11.2 §2.4.8).

진입점: `canonical_names` -- 계산 블록 함수 데코레이터(`compute_block` 안쪽). 블록은 `reads` 에 graph `ly_canon`(`rows=True` 면 `ly_canon_rows`)을
선언해야 한다. 별칭표는 이 모듈이 만들지 않는다 -- `canon_block.canon_tables`(블록 `ly_canonical_naming`)가 구조 정준 위치(`graph.canonical_form`)로
한 번 만들어 graph 필드에 쓴 것을 투영에서 읽어 번역만 한다(별칭표를 만들 수 없을 때의 빈 `Canon` = 번역 없음).

소자·넷은 정준 위치 순서로 별칭을 받고 matching 그룹·행 그룹·수동소자는 내용 키로 별칭을 받는다(`_helpers_alias`). 이 별칭은 계산 블록 안의
이름 정렬·동률 처리가 구조 정준 순서를 따르게 하는 수단이다. `rows=True` 면 행 그룹·수동소자도 별칭을 받는다(블록이 `ly_row_groups`·`ly_passives`
를 읽을 때만 -- 안 읽는 블록의 캐시 키를 넓히지 않는다).
"""
import functools

from ._helpers_alias import AliasView
from ._ly_fields import F_CANON, F_CANON_ROWS, GRAPH, GRAPH_KEY


def canonical_names(rows=False):
    """계산 블록 함수 데코레이터 공장: 블록이 읽는 이름을 구조 정준 별칭으로 바꿔 건네고 쓴 결과를 이름으로 되돌린다(`_helpers_alias`).
    별칭표 = 투영의 `ly_canon`(`rows=True` 면 `ly_canon_rows`)."""
    field = F_CANON_ROWS if rows else F_CANON

    def decorate(fn):
        @functools.wraps(fn)
        def run(projection):
            canon = projection.value(GRAPH, GRAPH_KEY, field)
            result = fn(AliasView(projection, canon))
            return {key: {k: canon.real_order(v) for k, v in canon.to_name(columns).items()}
                    for key, columns in result.items()}

        return run

    return decorate
