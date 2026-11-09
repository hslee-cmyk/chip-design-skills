# design `20-dead-code-dup` 정정 제안 -- P9(`20260930-p9-kcl-edges`) 관련 (초안, 저장소 미반영)

대상 파일: `docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md` (base = gate `master` 070cf69, 231줄).
쓰는 주체: 오케스트레이터(쓰기 경로표 `docs/02-design/**`). 이 문서의 v1.1은 `20260923-20-dead-code-dup-design`(`target_kind: diff`)으로 승인됐다.
아래 1·2·4는 E1(DoD 판정 기준)을 바꾸므로 **정정 커밋 뒤 사용자 승인 기록 `20260930-p9-e1-correction`**(`target_kind: diff`, `diff_base` = 070cf69,
`diff_head` = 정정 커밋, `diff_path` = 이 design 문서)을 받은 다음에 P9 card를 gate에 올린다. 3·5는 사실 정정(같은 커밋에 함께 넣어 한 승인으로 덮는다).
표기: 인용은 base 원문 그대로(줄 번호 = base). 제안 문안의 `(2026-09-30 정정 …)` 괄호 형식은 §6.1·§8 P7·§10 E0의 기존 정정 표기를 따른다.

---

## 1. §10 E1 (218행) -- DoD 판정 기준 변경 (승인 필요)

현재(218행, 원문):

```
| E1 | DUP 차등 test PASS 후 옛 함수 삭제 | `PT <iso>/…/tests/unit -k "dup_"` 그리고 `git -C <iso> grep -n "kcl_series_union\|_multilinear_interp_point_multi"` | 차등 test PASS, 삭제한 이름의 참조 0 |
```

어긋나는 점(base 실측):
* (a) P9는 `kcl_series_union`을 지우지 않는다 -- 엣지가 아니라 KCL 그룹(연결 성분)을 돌려주는 함수이고 엔진 운영 호출자가 2곳이다(SR `_build_theta_evaluator` 8055, SD `_kcl_branch_map` 7310).
  지우는 것은 그 본문의 중복 엣지 정의다(§2.2-3 "중복 정의를 지운다"). 그대로 두면 E1 grep이 정의·호출·docstring 참조를 찾아 항상 FAIL이다.
* (b) `_multilinear_interp_point_multi`는 이 Phase의 대상이 아니다 -- §1이 DUP 대상을 "두 개다 -- `W 계산`, `KCL 엣지`"로 한정했고, 레지스트리 §2 '다선형 보간' 행의 상태 칸은 비어 있다
  ('행동 보존 통합 가능' 아님). §8에 이 이름을 다루는 card가 없다. 그대로 두면 E1은 어떤 card로도 충족되지 않는다(SR 206 정의, 399 호출 -- base 실측).
* (c) 경로 `tests/unit`: P8의 차등 test는 `A/tests/contracts/test_dup_w_calc.py`에 있고 P9도 `contracts/`에 둔다. `tests/unit -k "dup_"`은 둘 다 수집하지 않는다(`tests/unit`에 `dup_` 이름 test 0 -- base `ls A/tests/unit`).

제안(218행 교체):

```
| E1 | DUP 차등 test PASS 후 중복 정의 삭제 | `PT <iso>/…/tests/contracts -k "dup_w_calc or dup_kcl_edges"`(`-k "dup_"`는 P4의 `test_probe_dup_scan.py`까지 잡는다) 그리고 `.ai/verification/20260930-dup-w-calc.json`·`.ai/verification/20260930-p9-kcl-edges.json`의 `checks.V2` | 차등 test PASS(실패 0, 수집 1개 이상), 두 판정 기록의 V2 PASS(P8 = 식 함수 비트 동일·E-LIB·E-INST, P9 = DIFF-DUP·E-LIB·E-INST가 base = 병합본). (2026-09-30 정정, spec card `20260930-p9-kcl-edges`: 옛 기준 '`kcl_series_union`·`_multilinear_interp_point_multi` 참조 0'은 (1) P9가 지우는 것이 함수가 아니라 `kcl_series_union` 본문의 중복 엣지 정의이고 -- 함수는 KCL 그룹을 돌려주며 운영 호출자가 2곳 -- (2) 다선형 보간은 §1 DUP 대상이 아니며(레지스트리 §2 상태 칸 비어 있음) (3) 차등 test가 `tests/contracts/`에 있어 성립하지 않았다. 중복 정의 삭제의 기계 판정은 card별 계약이다: P8 = W 식 인라인 0(`20260930-dup-w-calc` 계약 2), P9 = `kcl_series_union` 본문의 `_RAIL_NETS` 참조·`.source`/`.drain` 접근 0과 정본 호출(`20260930-p9-kcl-edges` 계약 1)) |
```

## 2. §6.2 (132-137행) -- 대상·방향 정정 (E1과 한 승인)

현재(134-137행, 원문):

```
정본 `stick_diagram._kcl_and_matching_edges`. 중복 `kcl_series_union`(같은 엣지를 따로 구현, 57줄)과 `_metric_kcl_residual`의 엣지 생성부. 둘 다 엔진 운영 경로에 있다(각 2곳).

* 차등 test: library 회로 전부에서 두 함수가 만드는 엣지 집합이 같은지(집합 동일성, 순서 무관).
* 다르면 F3 -- 통합하지 않고 레지스트리 상태를 고친다.
```

어긋나는 점(base 실측): `_metric_kcl_residual`(SR 4267)에는 엣지 생성부가 없다 -- 소자 `ID`를 노드에 부호 붙여 더하고(4307·4309) 이상전원을 더해 레일(4293 인라인 튜플) 밖
노드의 |잔차| 최댓값을 돌려준다(float). 직접 호출 0, `_METRICS_REGISTRY["kcl_residual"]`(5098) 경유 1곳(파일럿 선언) -- "각 2곳"도 이 함수에는 맞지 않는다.
`kcl_series_union`의 57줄 중 엣지 정의는 3023-3026·3041-3048(12줄)이고 나머지는 union-find와 대표 고르기다.

제안(134-137행 교체):

```
정본 후보 `stick_diagram._kcl_and_matching_edges`(레일 판정을 넷 이름 상수 `_RAIL_NETS`로 한다 -- 확정은 B26, 계획 DF-19·DF-26 담당 Phase 4). 중복 = `kcl_series_union` 본문의 엣지 정의(넷별 단자 사용 목록·레일 제외·2단자 판정·매칭 쌍 사슬). `kcl_series_union` 자체는 엣지가 아니라 KCL 그룹(엣지의 연결 성분)을 돌려주는 다른 질문이고 엔진 운영 호출자가 2곳이라 지우지 않는다 -- 엣지 정의 자리에서 정본을 불러 union한다(이름·시그니처·반환 불변). (2026-09-30 정정, spec card `20260930-p9-kcl-edges`: 옛 문장은 `_metric_kcl_residual`의 엣지 생성부도 중복으로 적었으나 이 metric은 엣지를 만들지 않는다(노드별 부호 붙은 전류 합, float 반환 -- F3 성격, 다른 개념). 겹치는 것은 MOS 단자 전류 부호 규약(`_kcl_terminal_sign`)과 레일 이름 집합(B26)이고 이 Phase의 대상이 아니다.)

* 차등(DIFF-DUP): library 로드 가능한 회로 전부 × 두 입력(`current_forced` 매칭 쌍, `[]`)에서 `kcl_series_union`의 그룹과 정본의 엣지 목록이 base와 병합본에서 같다(auditor, 판정 유형 equivalence). 영구 test는 구성으로 정답이 정해진 합성 넷리스트로 그룹·엣지 집합을 판정한다(두 피검 함수를 서로의 기대값으로 쓰지 않는다 -- V4).
* 다르면 F3 -- 통합하지 않고 레지스트리 상태를 고친다.
```

## 3. §8 P9 행 (193행) -- 사실 정정

현재(193행, 원문):

```
| P9 | `dup-kcl-edges` | `kcl_series_union`·`_metric_kcl_residual` 엣지 → 정본 | equivalence | (c) DIFF-DUP + E-LIB·E-INST | 중복 제거 |
```

제안(193행 교체):

```
| P9 | `p9-kcl-edges` | `kcl_series_union` 본문의 엣지 정의 → 정본 후보 `_kcl_and_matching_edges` 호출(함수·시그니처 유지). `_metric_kcl_residual`은 대상 아님(엣지를 만들지 않음 -- 2026-09-30 정정, spec card `20260930-p9-kcl-edges`) | equivalence | (a) 합성 넷리스트 + (c) DIFF-DUP·E-LIB·E-INST | 중복 엣지 정의 제거, 레지스트리 §2 행 정정 |
```

(id 칸: 기존 행들은 spec card id의 slug를 쓰지 않고 초안 id를 적었다 -- 초안 id `dup-kcl-edges`를 유지하려면 id 칸만 원문대로 두면 된다. 오케스트레이터 선택, 판정 무관.)

## 4. §8 아래 문장 (196행) -- E1과 맞춤

현재(196행, 원문):

```
card 하나의 단위는 계획 N3.12.3(관찰 가능한 계약 하나)이다. P5·P6·P8·P9는 equivalence라 code·test 두 역할이 모두 움직인다.
```

어긋나는 점: P8은 red-green으로 확정됐다(spec card `20260930-dup-w-calc` 판정 유형 근거 -- 새 함수, ImportError red). 제안(196행 교체):

```
card 하나의 단위는 계획 N3.12.3(관찰 가능한 계약 하나)이다. P5·P6·P9는 equivalence, P7·P8은 red-green이라 code·test 두 역할이 모두 움직인다(2026-09-30 정정: P7·P8은 code 커밋과 새 함수 때문에 red-green -- spec card `20260930-registry-grade-fix`·`20260930-dup-w-calc`).
```

## 5. 계획서와의 관계 (정정 아님 -- 오케스트레이터 확인용 비고)

* 계획 N6.2 `2` 행(plan:1017) "DUP마다 옛 함수 대 정본 차등 test(실행 가능한 library 회로 입력 전수 출력 동일) PASS 후 옛 함수 삭제": P8·P9 모두 '옛 함수'를 통째로 지우지 않았다
  (P8은 인라인 식, P9는 함수 본문의 엣지 정의가 지워진 중복). 계획 N6.2는 판정 표 보호 목록(N4.1·N4.2·N6.1·N3.12.2)에 없으므로 문장 명확화('옛 함수' → '중복 정의')는 승인 기록 없이
  고칠 수 있다. 다만 같은 DoD 문장이라 1과 같은 승인 범위에 `diff_path`로 넣는 것이 안전하다(선택).
* 계획 MOD3(plan:523)은 `circuit_state_graph.py` 목적지에 `_kcl_and_matching_edges`를 둔다 -- P9 방향과 맞다. `kcl_series_union`은 그 목록에 없고 레지스트리 §6 472행의 목적지가 `circuit_state_graph`다(Phase 3에서 정할 일, P9 무관).
