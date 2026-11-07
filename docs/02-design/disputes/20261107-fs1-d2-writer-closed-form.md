---
id: 20261107-fs1-d2-writer-closed-form
spec_card: docs/02-design/specs/20261107-fs1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_block_dc.py::test_dc_solve_cell_members_share_slice_and_w_is_closed_form
---
## 문제의 test

`test_dc_solve_cell_members_share_slice_and_w_is_closed_form` (interface §4 D-2). 마지막 단언이 모든 MOS 에 대해 `abs(op.W - _w_closed(op)) <= 1e-9 * _w_closed(op)` 를 요구한다
(`_w_closed(op)` = `op.current * op.L / exp(r4_ln_idu(op.kind, op.vgs, op.vds, op.vsb))`, 노드 풀이가 낸 동작점 (vgs, vds, vsb) 에서 잰 r4 닫힌 식).

## 근거(oracle 또는 사용자 원문)

* interface §4.2: `DeviceOp.W` = I·L/IDu(…)(**기존 식**). 기존 식에서 쓰기 소자의 IDu 는 θ 좌표 `exp(θ ln IDu)`(DEC-88)이고 노드 동작점의 순방향 IDu 가 아니다(`block_dc` 머리 설명, 코드 변경 전·후 같다).
* 실측(code worktree, FS-1 구현 뒤, 같은 toy `mirror_setup` + 정합 칸 키 200 / 나머지 100):

  | 소자 | role | `op.W` | `_w_closed(op)` | 상대 차 |
  |---|---|---|---|---|
  | M1 | writer(다이오드 노드) | 1.2e-06 | 1.2000009820868058e-06 | 8.18e-07 |
  | M2 | dependent | 4.000003252226456e-06 | 4.000003252226449e-06 | 1.7e-15 |
  | M3 | writer | 1.821101507070498e-06 | 1.821101507070498e-06 | 0.0 |

  M1 의 `op.vgs` = 0.5999999465094559(θ 가 겨냥한 0.6 에서 5.35e-8 V 아래). 다이오드 노드는 1변수 괄호 근(`solve_self`)이 수렴 허용오차 안에서 멈춘 값이고, 닫힌 식은 그 노드 전압에서 IDu 를 다시 잰다
  (gm/ID 15.2 × 5.35e-8 V = 8.1e-7). 즉 차이는 노드 풀이 수렴 허용오차×gm/ID 이고 슬라이스 선택(FS-1)과 무관하다.
* 옛 WB-1 test(`f42a13f8`)는 같은 단언을 **종속 소자 M2 에만** 걸었다(`want_w2 = ... r4_ln_idu("nmos", o["M2"].vgs, ...)`). 새 test 는 이 단언을 `o.items()` 전체로 넓혔는데, 쓰기 소자 M1(다이오드 노드)에서는
  어떤 구현이든(W 가 θ 좌표 식인 한) 1e-9 를 만족할 수 없다. 쓰기 소자 W 를 노드 동작점 IDu 로 바꾸라는 요구는 interface 어디에도 없다(DEC-88 'W = ID·L/exp(θ ln IDu)' 와 모순).

## 요청

D-2 단언을 (a) 종속 소자(M2)에만 `_w_closed` 1e-9 비교를 걸고 쓰기 소자(M1, M3)는 `op.W == op.current * op.L / math.exp(op.ln_idu)`(좌표 식 그대로) 로 보거나, (b) 쓰기 소자에는 노드 수렴 허용오차×gm/ID 를 허용오차로 쓰도록 고친다.
기대값을 구현에 맞추려는 요청이 아니다: 단언의 대상(쓰기 소자 W 의 정의)이 interface §4.2 와 어긋난다는 지적이다.
