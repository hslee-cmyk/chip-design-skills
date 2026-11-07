---
id: 20261107-fs1-s0-baseline
spec_card: docs/02-design/specs/20261107-fs1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/integration/test_s0_layer_9circuits.py::test_stage_reports_unchanged_from_base[folded_cascode]
test_id: skills/analog-gmid-design/gmid_engine/tests/integration/test_s0_layer_9circuits.py::test_stage_reports_unchanged_from_base[ngcc_3stage_ff]
test_id: skills/analog-gmid-design/gmid_engine/tests/integration/test_s0_layer_9circuits.py::test_s0_field_values_unchanged_from_base[folded_cascode]
---
## 문제의 test

2회로 연기(`--run-slow -k "folded_cascode or ngcc_3stage_ff"`, `integration/test_s0_layer_9circuits.py`) 중 '기준선과 같음' 단언 3개. 기준선 = `tests/integration/fixtures/u17_1b_s0_baseline.json`(U17 ①-b 때 base 코드로 잰 값; 이 card 는 기준선을 갱신하지 않았다).

실패 사유(실측):
* `base 와 다른 보고서 키: ['stage_b.achievability.curves', 'stage_b.achievability.gain']` (folded_cascode, ngcc_3stage_ff 둘 다).
* `base 와 다른 S0 필드 값: ['device M10 start.row', 'device M3 start.row', 'device M4 start.row', 'device M7 start.row', 'device M8 start.row', 'device M9 start.row', 'device MP start.row', ...]` (folded_cascode).

## 근거(oracle 또는 사용자 원문)

이 값들은 FS-1 의 **의도된 동작 변경**이다(spec 머리 '변경 종류 = 동작 변경(O-34 (1))', 재작성 범위 W5·W7·W9):
* W5 / DEC-108 (1): W 가 없는 단계의 포락 표(GB4 `ParamTables._envelope` → `achievability` 곡선·이득 보고)가 `reachable_slices`(기준 폭 슬라이스의 W bin 위 끝 이하 + 기준 폭 슬라이스에 L 이 든 bin 이 있을 때만) 대신 `widths(lut, kind)`(최소 finger 폭 이상 전 슬라이스)를 읽는다 → 포락에 드는 슬라이스 집합이 달라 `stage_b.achievability.curves/gain` 값이 달라진다.
* W7·W9 / DEC-108 (3): 출발 단계의 offset 가드 slope bin 폭이 옛 소자별 선택 함수의 폭에서 소자 칸 키 × 격자(6단계)로 바뀌고 4단계 L 하한은 기준 폭 슬라이스 폭으로 바뀐다 → `start.row` 의 경계·출처가 달라진다.
같은 실행에서 G-10 계수 test(`test_g10_no_recompute_9circuits.py`, 같은 2회로)는 통과한다(블록 재계산 0, 기준 변경 0).

## 요청

기준선 `u17_1b_s0_baseline.json` 의 위 키·필드를 판정자가 FS-1 코드로 다시 잰 값으로 갱신하거나, 이 '기준선과 같음' 단언의 대상에서 FS-1 이 정의를 바꾼 키(`stage_b.achievability.curves/gain`, `device */start.row`)를 뺀다. 기준 변경은 code 몫이 아니다(N6.3) -- 코드를 기준선에 맞추면 W5/W7/W9 를 되돌려야 한다.
