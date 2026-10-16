---
title: graph-consumption -- 계획 이력
plan: graph-consumption.plan.md
date: 2026-10-16
---

# graph-consumption 계획 이력

계획 본문은 [graph-consumption.plan.md](graph-consumption.plan.md)다. 이 문서에는 경위, 측정 근거, 버전 이력만 둔다.

## H1. 결정 경위

### 2026-10-16 조사 두 건

* **필드 소비자 조사**(정적, `wt/_scratch_deadfields/deadfields_report.md`, 당시 HEAD `9069e10`): 권한표 필드 131개를 엔진 소비자·test만·아무도 안 읽음·보고 전용으로 나눴다(A 91, B 24, C 2, D 14). 하위 칸 0 계수(292), 정본 우회 재계산 의심 R1~R9, 구조 규칙 L 초안(L-1~L-5)을 냈다.
* **KVL·KCL 관계 조사**(읽기 전용, `wt/_scratch_kvlkcl/kvlkcl_findings.md`, master `baa7883`): 엔진이 KVL(노드전압 정식화 + 쓰기 계획 숲)과 KCL(유리수 전류 기저)을 실제로 푼다는 것, 그런데 graph S1 관계 필드를 읽지 않고 따로 다시 만든다는 것을 확인했다. 결과 검증 쪽의 빈 곳(봉인 8 목록, 봉인 3 결선, 공급 합·MNA 잔차 미판정)과 출발 전류 자리값 문제를 적었다.
* **KCL 계수**(`wt/_scratch_kcl/kcl_count.jsonl`): 회로별 기저 자유·고정 원소, 혼합 행, 연결 통계. heldout 한 회로는 기저 단계에서 `mos_zero_current_structural`로 멈춘다.

### 2026-10-16 사용자 결정 O-10과 원문 지시

* O-10 "v0.6.5 승인, 나머지 세 가지는 권고대로"(`user_decisions.md` 628행): (2) 이 계획 착수(규칙 L, 부채 목록, 필드별 처리, R3 공동분석), (4) KCL 조사 결과 처리(새 전류 사슬 없음, 출발 음수 자리값 → 충돌 기록, 구간 결합·저항 방향 표현 백로그).
* 사용자 원문(오케스트레이터 전달, 계획 N1.1 인용): 계산식을 쓰기 전 graph 확인, 엔진이 KVL·KCL에 따라 계산하는지 확인. 같은 날 역할 agent 두 개에 절차를 넣었다(커밋 `3ddb27c`).
* P-1(619행): 물리 정합 최우선, 가장 일반적인 형태부터.

### 2026-10-16 계획 v0.1 작성 방침

* 형식은 같은 폴더의 headroom-chain·oracle-portability 계획을 따랐다(N 절, 원래 취지와 다름 표, 결정 표 기본안 + 근거, card 단계, 완료 조건).
* 엔진 사실은 worktree `wt/graph-consumption-plan`(base `52945ce`)에서 직접 읽어 `파일:줄`로 적었다. 조사 메모 문장을 옮기지 않고, 수치는 다시 쟀다(H2).
* 조사 메모의 G1~G8 항목은 계획에서 다음 자리로 옮겼다: G1(봉인 8 목록과 쓰기 계획 사이클 정의 차이) → N3.3·M-G1, G2(봉인 3 비독립) → N3.5-1·2·X-G4, G3(포화 사후 판정) → headroom-chain 범위(N3.5-6), G4(출발 전류 KCL 미경유) → N3.6·X-G8, G8(공급 합·MNA 잔차) → N3.5-3·4. port_diff·rel_matching_offset 미사용은 N3.2 표.
* 규칙 L의 하위 번호가 사용자 결정 L-1~L-3(옛 엔진 삭제)과 겹쳐서, 계획에서는 항상 '규칙 L-n'으로 적기로 했다(N0).
* 범위 초안의 (4) 'coupling 3필드 → 층 0, residual_probe·dof_numeric → 단계 B, layout_outputs'는 소비자 자체가 아직 없는 엔진 기능이라 배선 대기로 바꿨다(X-G5, U-G6).
* 봉인 8이 봉인 2에 함의된다는 사실은 처음에 X-G3로 올리려 했으나, 상위 계획 472행이 이미 '봉인 1·2가 통과하면 자동 성립하므로 … 게이트'라고 적고 있어 취지 차이가 아니라고 보고 번호를 비웠다.
* 상위 DEC-64가 '루프 소속은 S1 관계 엣지 `kvl_branch`로 기록'과 J12-c 측정 기대를 명시한 것을 읽고, KVL 정본 이동을 X-G1로 올렸다.

## H2. 측정 근거

### H2-1 필드 분류 재측정(2026-10-16, base `52945ce`)

* 방법: 조사 스크립트(`wt/_scratch_deadfields/{decls,consumers,classify}.py`)를 scratchpad에 복사하고, 엔진 경로만 이 worktree로 바꿔 다시 돌렸다(엔진 import·실행 없음, AST만).
* `git diff --stat 9069e10 52945ce -- skills/analog-gmid-design/gmid_engine` 출력이 비어 있다. 조사 뒤 엔진 코드 변경은 없다.
* 결과:
  * 권한표: `S0_WRITERS` 117 + `LY_WRITERS` 14 = 131. 하위 표 S1 38, S1V 46, S2 78, metrics 15, search 16.
  * `@compute_block` 53개, READS·WRITES 미해석 0.
  * writer 블록 밖 정적 읽기 0인 필드: 44개. 이 중 동적 필드 접근을 손으로 확인한 18개는 실제 읽기가 있다.
    * 봉인 보고 `ITEM_FIELDS` 루프: `dc_seal_1·2·3·6·7·8·9`(7)
    * 단계 B 보고 `_REPORT_FIELDS`: `area_bound`·`buffer_window_report`·`count_budget`·`dof`·`headroom_rows`·`warnings`(6, 보고 전용)
    * `SearchContext` `_field` 속성: `constraint_classes`·`junction_source`·`metric_structure`·`mismatch_source`·`model_error`·`noise_input_cells`(6)
  * 남는 25개에, 정적 판정이 읽기로 잘못 센 `device.value` 1개를 더하면 26개다. 잘못 센 자리는 `E/search/constraint_classes.py:31, :41`의 선언 객체 속성 `decl.value`다(필드 접근이 아님).
  * 26개 = 조사 메모의 B 24 + C 2와 같은 목록이다.
  * 보고 전용 4개 문제(`ly_rows` reader `layout/outputs.py:49`만, coupling 3필드 reader `pipeline/stage_a.py`만)도 행 자료로 다시 확인했다.

### H2-2 하위 칸 재측정

* `attrs.py`·`attrs2.py` 재실행: frozen dataclass 337개, 칸 2047개, 엔진 읽기 0인 칸 292개. 조사 메모와 같다.
* 이 292는 엔진 전체 dataclass 기준이다(예: `_module_map` 항목 형식 포함). graph 필드 값 형식으로 한정한 수는 card 0 M-G3c에서 잰다.

### H2-3 코드 사실 재확인(읽기)

| 사실 | 확인한 줄 |
|---|---|
| 출발 구간 θ 자유 원소 0 이하 → 미정, MOS 0 이하 → None, 소자별 자리값 | `E/search/start_intervals.py:117, :119, :128-129` |
| 봉인 3 결선 = `basis.ends`, MOS 전류 = `idu_forward`·W/L | `E/sizing/seal_kcl.py:37-46` |
| W = ID·L/exp(ln IDu), 요청 W 예외 | `E/sizing/block_widths.py:47` |
| 봉인 8 목록 = S1 `rel_kvl_branch` | `E/sizing/seal_kvl_branch.py:18, :28` |
| 쓰기 계획 F·변·분류 | `E/sizing/writer_plan.py:8-23, :146-196` |
| 쓰기 계획 (kind, gate, source) 키 재유도 | `E/sizing/writer_plan.py:186` |
| S1 G_vgs 정의(F = 레일만, 평행 변 하나) | `E/graph/gvgs_cycles.py:7-23, :56-118` |
| 기저 원소 = `dc_nets`가 있는 원소, 방향 `_ends` | `E/sizing/current_basis.py:48-54, :84-88` |
| `rel_kcl_group` = 가지 segment 2개 이상 | `E/graph/rel_kcl.py:28-32` |
| 공급 합 계산·운반만 | `E/metrics/supply.py:70`, `E/metrics/dc_metrics.py:130`, `E/search/objectives.py:28` |
| MNA 잔차 검사 없음 | `E/metrics/mna_solve.py`(grep `residual` 0) |
| diode·묶음 재계산 자리 | `E/metrics/block_gain_model.py:166, :170`, `E/metrics/ls_swing.py:46`, `E/graph/cells.py:53, :117`, `E/graph/net_model.py:75`, `E/graph/node_impedance.py:22` |
| VGS = 0 누설 세 곳, `oracle_input` 생성 엔진 코드 없음 | `E/sizing/seal_conduction.py:8, :27-31`, `E/search/cell_floor.py:53`, `E/search/current_box.py:1-33`, grep `oracle_input` |
| 단계 B 필드 배선 = U17 ② | design 40 531-532행, `E/search/s0_fields.py:9` |
| coupling 3필드 지정 소비자 = 층 0 조립 | `E/pipeline/stage_a.py:12-15` |

### H2-4 S1 관계 필드 계수(조사 원자료, 재측정 안 함)

* `wt/_scratch_kvlkcl/s1_counts.jsonl`(2회로, `build_s1`만): 파일럿 `rel_kvl_branch` 4(모두 레일 경유), `rel_kcl_group` 18, `gvgs_summary.vds_saturation` 22. folded_cascode `rel_kvl_branch` 0, `rel_kcl_group` 3.
* 이 값은 계획 본문에 넣지 않았다. 13회로 값은 card 0 M-G1·M-G2가 잰다.

## H3. 검증 반영 기록

(아직 없음)

## Version History

| 판 | 날짜 | 변경 |
|---|---|---|
| 0.1 | 2026-10-16 | 초안. 사용자 O-10 (2)·(4), P-1, 사용자 원문(KK-1) 반영. 재측정 H2 |
