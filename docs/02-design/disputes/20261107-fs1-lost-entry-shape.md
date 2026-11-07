# dispute 20261107-fs1: O-3 `realize.lost` 항목 꼴 (test 작성자 -> 오케스트레이터)

- interface §6: "`realize.lost` 항목에 `"small_m"`: 그 점 실현 스냅샷(실패면 부분 스냅샷)의 `dc_finger`에서 m ≤ 2인 MOS 이름 정렬 목록, `dc_finger`가 없으면 None". 항목이 어떤 객체(튜플 `(point_id, reason, detail)` 안 detail 매핑인지, JSON 줄의 별도 키인지)인지는 정해져 있지 않다.
- 현 test (`search/test_realize_front.py::test_realize_r6c_..._small_m`): 항목 `(point_id, reason, detail)` 의 `detail` 을 `dict(detail)` 로 읽어 `"small_m"` 키 존재와 값 꼴(None 또는 정렬 이름 목록)을 단언한다. 키 존재만으로 줄이지 않았다.
- 요청: interface §6 에 `lost` 항목 꼴을 한 줄 정하거나(권고: 항목 detail 매핑의 `small_m` 키), JSON `runs.jsonl` 의 `realize.lost[i]` 키로 정한다. 정해지면 이 test 의 읽는 자리만 맞춘다.
