### N6.10 card NL-1 -- 노달 ω → 0 극한 식 정본 하나(사용자 결정 O-26 (5))

**근거**: 사용자 결정 O-26(2026-10-19 "모두 권고대로", `_drafts/user_decisions.md` O-26 행) (5) "C3 -- 노달 helper가 dc_limit 극한 식(용량 전용 노드 전하 보존)을 공유, 정본 하나".

**사실**(base `b2c72a01`): `E/metrics/dc_limit.py:1-14` `solve_dc_limit`은 용량 전용 노드를 전하 보존 식으로 바꾼 정확한 극한이다. `E/metrics/_helpers_nodal.py:5-8`은 같은 극한을 '전도 경로가 있는 노드만' 풀고 컨덕턴스가 안 닿은 노드를 전압 0(`floating`)으로 둔다 -- 같은 개념(소신호 DC 극한)의 두 정의다. `_helpers_nodal` 소비자: `E/metrics/offset_analysis.py:11`, `E/metrics/block_residual.py:8`, `block_model`, `ff_gm_ratio`(모듈 머리 `:1`).

**범위**: `_helpers_nodal`의 풀이가 `dc_limit`의 극한 식(용량 전용 노드 = 전하 보존)을 공유한다 -- 정의 하나. 소비자 결과가 바뀌는 곳(용량 전용 노드가 감지·구동 경로에 있는 회로)은 변화표로 낸다. `offset_systematic`의 나눗셈은 DE-1이 지우므로 그 소비자는 이 card 범위가 아니다.

**순서**: DE-1과 독립(파일 겹침 `metrics_aux.py`·`offset_*`는 착수 때 확인). **완료 조건**: (1) 극한 식 구현 자리 하나(`git grep`) (2) 용량 전용 노드 toy 손계산과 일치, 기존 test 기대값 변화는 원인 설명 (3) 13회로 변화표 (4) N6.3 공통 (5) **변경 종류: 동작 변경**(O-34 (1) -- 소비자 값이 바뀌는 회로) / 용량 전용 노드가 없는 회로는 순수 리팩터링 필드별. 바뀌는 값(`offset_analysis`·`block_residual`·`ff_gm_ratio` 등)의 oracle 다리는 N6.3 '판정 다리 보류·대상 없음' 규칙(보고 전용·`spice_unverifiable`이면 대상 없음 + 판정 소비자 0 grep). 결정성 비트 동일.

