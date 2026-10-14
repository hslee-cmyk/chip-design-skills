"""구조 표 출력 -- `structure.json`(엔진 유도 결과) 내용 (설계 40 §10.4 '9회로 구조 표', 계획 N3.3·N9.1 `6a-structure-stage`).

진입점: `structure_tables(source) -> dict`  (`source` = S1v 필드 `graph/s1v` 가 있는 스냅샷 또는 S1Graph, 설계 40 §2.4.8 v1.9.1 D1).

S1v 필드(`views`·`l_classes`·`findings`·`declared`·`applied_facts`)를 JSON 으로 쓸 수 있는 평범한 값(dict·list·str·int·float·bool·None)으로 바꾼다 -- 뷰마다 셀·구동 종류·stage 시작·블록(키는 출력노드 배열)·극점 노드·
출력 방향·루프(분류·끊는 점·극성)·축약/비축약 셀 판독 차이·기록, 그리고 L 동치류(주인)·declared 대조·적용한 ratified 사실. dataclass 필드는 선언 순서
그대로 키가 되고 tuple·frozenset 은 list(frozenset 은 정렬)가 된다. ratified 사실 파일(`library/<name>.structure.json`)과 형식이 다른 **유도 결과 보고**다
(그 파일은 ratified 사실만 담고 이 결과는 매 실행 재생성한다 -- N3.3).
"""
import dataclasses

from gmid_engine.core import sorted_items

from .s1_values import S1V_KEY

SCHEMA_VERSION = "1"


def _plain(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: _plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, frozenset):
        return [_plain(item) for item in sorted_items(value)]
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    return value


def structure_tables(source):
    out = {"schema_version": SCHEMA_VERSION}
    for name in ("views", "l_classes", "findings", "declared", "applied_facts"):
        out[name] = _plain(source.value("graph", S1V_KEY, name))
    return out
