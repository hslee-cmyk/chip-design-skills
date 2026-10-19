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

### 2026-10-19 계획 v0.2 개정 방침

* 근거: v0.1 독립 검증 결과(판정 '수정 필요', 차단 5·중간 9·낮음 9). 요약은 `wt/_drafts/SESSION_HANDOFF_2026-10-16.md` '추가: graph-consumption 계획 v0.1 독립 검증 결과' 절(42-51행), 상세는 오케스트레이터 전달.
* 개정 전에 worktree에 master `5fea301`을 병합했다(병합 커밋 `aebe7e8`). 엔진·도구 코드는 v0.1 base와 같다(H2-5).
* 차단 B1은 새 결정이 아니라 기존 사용자 결정(B2·K-3, `user_decisions.md` 225·243행)과 design 41 §6.7-1a를 따르는 정정이다. v0.1은 as-built 쓰기 계획의 '같은 DC' 변(`input_tie`)을 KVL 정본 정의에 넣고, 그 동작을 상위 DEC-64 v1 문언으로 올리자고 했다(X-G2·U-G2). 이것은 B2('v1은 제약 없음, 쓰기 계획을 계획에 맞게 고친다')·K-3('input_tie 폐기')과 반대였다. v0.1 작성 때 design 41 §6.7-1a와 user_decisions 225·243행을 읽지 않은 것이 원인이다.
* 검증자 지적대로 승인된 headroom-chain 계획 v0.6의 Gs⁺ 정의도 같은 as-built tie 변을 포함한다(그 계획 N0.1 70행). 이 계획은 그 계획을 고치지 않고 정정 필요 사실을 N7.2에 적었다(S-7, 오케스트레이터·사용자 몫).
* 봉인 8(중간 (4))과 MNA 잔차(중간 (5))는 v0.1의 '재작성'·'잔차 기록'을 버리고 사용자 선택지로 바꿨다. 봉인 8은 봉인 2에 함의되고, MNA 상대 잔차는 후진 안정 LU에서 공허하다.
* B2·B3로 v0.1의 BD-3(결선 대조)·BD-4(공급 합 판정)를 철회하고, 독립 검증 경로를 오라클 forced·free로 다시 정의했다. 엔진 안에는 항등식이 아닌 보조 검사 둘(숲 구조 불변량, `node.terminals` 결선 점검)만 남겼다. `node.terminals`도 같은 핀에서 만들어진다는 사실(`E/graph/s1_structure.py:51, :55`)을 재측정으로 확인해, 그 점검은 독립 검증이 아니라 조립 오류 보조임을 계획에 적었다.
* '종속 사이클 필드'(v0.1 BD-1)는 봉인 8을 지우는 기본안에서 소비자가 없어져, 만들면 배선 원칙에 따라 만들지 않기로 바꿨다. 사이클 멤버가 필요한 곳은 트리 경로 정본(HC-1이 만듦)을 읽는다.
* K-3 구현 card는 상위·관련 계획 card 표에 id가 없다(grep 0). 이 계획은 id를 정하지 않고 '오케스트레이터가 부여'로 적었다.

### 2026-10-19 계획 v0.3 개정 방침

* 근거: v0.2 재검증 결과(판정 '수정 필요', 차단 0·중간 7·낮음 9, 오케스트레이터 전달). 반영 기록은 H3.
* v0.2는 봉인 8의 역할을 숲 불변량이 '대체'한다고 적었다. 재검증이 봉인 2가 같은 양을 소자별로 이미 잰다는 사실(`seal_vgs_match.py:25`, `seal_kvl_branch.py:29`)을 짚었고, 숲 불변량은 union-find 회계 검사로 봉인 8과 별개임을 바로잡았다. U-G9 선택지에서 '대체'를 뺐다.
* v0.2의 U-G13 (가)('`macro_failed`와 같은 경로')는 코드와 맞지 않았다. `use_macro`가 꺼진 뒤와 예산이 없을 때 실패가 통과하고, 사다리 아래 칸은 판정하지 않는다(F-G32). v0.3은 꺼지지 않는 별도 충돌 표지와 사다리 칸 단위 처리를 정의하고, 사다리 선택이 바뀌므로 X-G11로 올렸다. '0 이하 = 물리 동작점 아님'은 선언 방향이 고정된 뒤(결정 6)에만 성립하므로 GC-5 선행에 결정 6 card를 넣었다(BD-13).
* v0.2의 BD-10은 'HC-1이 트리 경로를 S0 결과(필드 또는 함수)로 만든다'고 했다. 재검증 지적대로 정본은 `node.dc_writer` 자체(부모 포인터)이고, 경로를 필드로 저장하면 사본이다. 경로는 순수 함수 하나로 한정했다. headroom-chain v0.7.1(브랜치 `plan/headroom-chain-k3` `ecceaed4`, 승인 대기)이 '경로 목록을 저장하지 않는다'(317행)이고 Gs⁺도 K-3 뒤 기준으로 이미 맞췄으므로, v0.2의 'headroom-chain 정정 필요'를 지웠다.
* 상위 V9(920행)가 `matching_offset`·`matching_ratio`를 검증 소비자로 지정한 것을 v0.2가 놓쳤다. 같은 이유로 상위 92행(G_vgs 용어)·LR5(553행)·design 41 589·917·1491·1533행도 관계 엣지 이름을 쓴다. 모두 N3.10 개정 항목으로 넣었다.
* 다른 card의 완료 조건 변경(U16 오라클 대조, 단위 8·U16·U17 ② 부채 항목 0)은 '브리핑'으로는 계획에 남지 않으므로 S-7 상위 개정 항목으로 바꿨다.
* U-G5(MNA)·U-G7(R4)은 결정 목록에서 내려 백로그 B-G1·B-G2로 옮겼다(재검증: 과잉). GC-4는 비웠고, GC-8은 R4 부채 항목의 card id로 남겼다.
* K-3 뒤 기준 측정은 모사하지 않고 K-3 병합 master에서 재도록 GC-0을 GC-0a·GC-0b로 나눴다(headroom-chain v0.7.1 448-451행과 같은 관행).

### 2026-10-19 계획 v0.4 개정 방침

* 근거: v0.3 재검증 결과(판정 '수정 필요(소폭)', 중간 2·낮음 4, 오케스트레이터 전달). 반영 기록은 H3.
* v0.3의 U-G13 (가)는 양 끝이 모두 실행 불가일 때 `final = bottom`이 칸 0이 되는 대체 경로와, 1회차 전류가 경계 함수로 가는 경로의 0 이하 처리를 정의하지 않아 fail-closed가 아니었다. v0.4는 (가) 안에 끝 처리(전류 충돌이면 칸 0도 빼고 빈 사다리, 층 0 상자 중심 출발, `_report` 빈 사다리 처리)와 1회차 처리(경계 함수 다섯 자리의 전류 충돌 비활성 사유·충돌 기록)를 넣었다. 재검증 지적은 경계 함수 셋(`matching_bounds`·`area_bounds`·`gain_l_bounds`)이었고, 코드 재측정에서 `noise_bounds`(333행)도 `currents1`을 받음을 확인해 다섯 자리로 적었다.
* v0.3은 결정 6을 '아직 구현되지 않은 card'로 보고 GC-5 선행에 넣었다. 결정 6은 U17 ①-d 병합 `c8d156e3`으로 이미 들어갔고(상위 U-62 닫힘, HEAD 조상 확인), headroom-chain v0.7.1 490행도 '이미 충족'으로 적는다. BD-13을 충족으로, GC-5 선행·K-j·R-G5·K-3 순서 조건 문언을 맞췄다.
* 낮음 4건은 계획 문언(N3.1-6 (c)(d), 완료 조건 3)과 design 항목(GD-7·GD-9), 후속 항목(N3.10 P-G2)으로만 넣었다.
* 재검증이 '302행 부근'으로 지목한 DEC-64 v1 고리 문언은 사용자 결정(DEC-64 v1 해석) 대기라 고치지 않고 N3.10 P-G1 대기 항목으로만 넣었다. v0.3·v0.4의 302행 부근에는 그 문언이 없어(N3.2 처리 표), 같은 전제를 담은 자리(54·316·324·343·464행)를 P-G1에 재측정해 적었다.

## H2. 측정 근거

### H2-1 필드 분류 재측정(2026-10-16, base `52945ce`)

* 방법: 조사 스크립트(`wt/_scratch_deadfields/{decls,consumers,classify}.py`)를 scratchpad에 복사하고, 엔진 경로만 이 worktree로 바꿔 다시 돌렸다(엔진 import·실행 없음, AST만).
* `git diff --stat 9069e10 52945ce -- skills/analog-gmid-design/gmid_engine` 출력이 비어 있다. 조사 뒤 엔진 코드 변경은 없다.
* 결과:
  * 권한표: `S0_WRITERS` 117 + `LY_WRITERS` 14 = 131. 하위 표 S1 38, S1V 46, S2 78, metrics 15, search 16.
  * `@compute_block` 53개, READS·WRITES 미해석 0.
  * writer 블록 밖 정적 읽기 0인 필드: 44개. 이 중 동적 필드 접근을 손으로 확인한 19개는 실제 읽기가 있다(v0.1은 '18개'로 잘못 적었다. 아래 세 묶음의 합 7 + 6 + 6 = 19이고, 44 − 19 = 25와도 맞다).
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

### H2-5 v0.2 재측정(2026-10-19, master `5fea301`, 병합 커밋 `aebe7e8`)

* `git diff --stat 52945ce HEAD -- skills/analog-gmid-design/gmid_engine skills/analog-gmid-design/tools` 출력이 비어 있다. v0.1 인용 코드 줄은 그대로다.
* 상위 계획은 병합으로 6줄이 바뀌었다(hunk 1·8·446행 부근). v0.1이 인용한 줄(179·186·208·215·217·227·263·269·282·287·294·328·400·467·472·477·1153)을 다시 읽어 내용이 같음을 확인했다.
* `user_decisions.md` 줄: X-20 611, X-21 612, L-1 617, P-1 619, L-2 620, L-3 626, O-10 628, X-22 629, B2 225, K-3 243(파일 631행).
* 새로 읽은 사실(계획 F-G19~F-G30):

| 사실 | 확인한 줄 |
|---|---|
| as-built '같은 DC' 변(K-3 미구현) | `E/sizing/writer_plan.py:10-11, :104-105, :157-159, :213-214, :234` |
| K-3 구현 card id 없음 | `docs/01-plan/features/*.plan.md` grep `input_tie`·`K-3` card 표 0, design 41 §6.7-10 (P4) '구현은 별도 card' |
| `gvgs_self_edge` 유일 정지, 쓰기 계획은 비트리 → 종속 | `E/graph/gvgs_cycles.py:68-79`, `E/graph/s1_values.py:125`(사용처 grep 1), `E/sizing/writer_plan.py:164-167, :176-196` |
| 공급 합 = 같은 가지 전류의 레일 합 | `E/metrics/dc_metrics.py:73-90`, `E/metrics/supply.py:26-44, :70` |
| 기저 원소 필터, `node.terminals`도 같은 핀 | `E/sizing/current_basis.py:86-88`, `E/graph/s1_structure.py:51, :55` |
| 오라클 forced 고정원·넷별 KCL 판정 | `O/oracle_netlist.py:486-497`, `O/oracle_compare.py:365-367` |
| rule_hash 대상 파일, structure.json 2개 | `E/graph/s1v_values.py:14-21`, `E/graph/s1v_key.py:25, :29`, `git ls-files` |
| tail 정의 | `E/graph/l_classes.py:7-9` |
| S1 관계 사본(`rel_equal_vgs`·`rel_vds_eq_vgs`·`rel_l_class`·`rel_matching_ratio`) | `E/graph/rel_vgs.py:31-37`, `E/graph/rel_matching.py:35-40` |
| `size_and_seal_local` 엔진 호출자 0 | grep(tests 제외, 정의 파일 밖 호출 0), `E/sizing/size_and_seal_local.py:113` |
| MNA 풀이 = LU·`numpy.linalg.solve` | `E/metrics/mna_solve.py:6-9` |
| `stacked_vsb`·`same_as` S1 관계 엣지 없음 | `E/graph/s1_values.py:77-85`, `E/graph/coupling_values.py:17` |
| 동적 필드 접근 3곳 | `E/search/search_context.py:69-70`, `E/graph/structure_tables.py:33`, `E/layout/canonical_naming.py:96` |
| 수동소자 값 정본 | `E/sizing/dc_inputs.py:7, :36`(v0.1의 `:31`은 `input_dc_v` 줄이었다) |
| headroom-chain v0.6 Gs⁺ 정의의 tie 변 | `docs/01-plan/features/headroom-chain.plan.md` 10·70·72·227행 |
| 정상 출력 전용 10개 | `wt/_scratch_deadfields/deadfields_report.md` D 목록(180-196행), `E/pipeline/stage_b.py:117-118, :123` |

### H2-6 v0.3 재측정(2026-10-19, 같은 base)

| 사실 | 확인한 줄 |
|---|---|
| 봉인 2는 모든 MOS의 \|ln IDu_fwd − ln IDu\|/(gm/ID), 봉인 8은 같은 양의 멤버 합 | `E/sizing/seal_vgs_match.py:24-26`, `E/sizing/seal_kvl_branch.py:28-30` |
| `feasible` = 예산 안 and not (use_macro and macro_failed), 예산 None이면 within 참, use_macro 해제 | `E/search/start_intervals.py:362-367, :376-381` |
| 사다리 아래 칸은 판정 없이 추가 | `E/search/start_intervals.py:401-406` |
| `NodeWrite.known` = 읽는 아는 쪽 노드(부모 포인터), 쓰기 계획 BFS가 채움 | `E/sizing/s2_values.py:268-277`, `E/sizing/writer_plan.py:211-220` |
| headroom-chain v0.7.1: Gs⁺ K-3 뒤 기준, 성분마다 뿌리·오프셋 하나, 경로 목록 저장 안 함, K-3 뒤 측정은 병합 master에서 | `git show ecceaed4:docs/01-plan/features/headroom-chain.plan.md` 68-72·317·448-451행 |
| 상위 G_vgs 용어·LR5·V9 | 상위 계획 92·553·920행 |
| design 41 관계 엣지 이름 사용 | 589·917·1491·1533행 |
| `gvgs_cycles.py` 등록 자리 | `E/graph/s1_values.py:222-225`, `E/_module_map.py:98, :470`, `E/graph/__init__.py:29`, `E/graph/s1_build.py:35` |
| `applied_facts`·`declared`는 `structure_tables.py:33` 동적 루프로만 읽힘(`stage_a.py:100`의 `"applied_facts"`는 실패 보고 사전 키) | 해당 줄, grep |
| `cells.py` diode 비교는 속성 꼴 | `E/graph/cells.py:53, :117` |

### H2-7 v0.4 재측정(2026-10-19, 같은 base, HEAD `d641ac9`)

| 사실 | 확인한 줄 |
|---|---|
| 양 끝 모두 실행 불가면 `final = bottom`, 면적 충돌만 기록, 그 `final`이 칸 0 | `E/search/start_intervals.py:377-389, :401` |
| t = 0이면 아래 칸 없음, 아래 칸은 `solve(lower, refine=False)` = `_placed` 고정점 마지막 상태 | `E/search/start_intervals.py:369-370, :402-405, :171-182` |
| `_report`가 `rungs[0]`을 무조건 읽음(빈 사다리면 IndexError) | `E/search/start_intervals.py:453` |
| 층 0은 빈 사다리를 `(None,)`으로 받아 상자 중심 출발 | `E/search/layer0_center.py:654-656, :126-135` |
| 1회차 `currents1` = 전류 또는 `first.refs`, 소비처 `gain_l_bounds`(elements)·`matching_bounds`·`area_bounds`·`noise_bounds` | `E/search/start_intervals.py:285-296, :327, :332-333` |
| ~~경계 함수의 전류 None 처리 = `WHY_NO_CURRENT` 비활성~~ **틀림, v0.5에서 정정(H2-8)**: `gain_l_bounds`·`area_bounds`는 그렇지 않다 | `E/search/iv_area.py:57-58, :83`, `E/search/iv_matching_l.py:117-118`, `E/search/iv_noise.py:77` |
| θ 자유 원소가 아닌 원소 값은 부호 거르기 없음 | `E/search/start_intervals.py:115-117` |
| 결정 6 병합: `c8d156e3`이 HEAD 조상(`git merge-base --is-ancestor c8d156e3 HEAD` 참), 상위 U-62 닫힘, `ds_self_swap_zero_current` 정지 | 상위 계획 1371행, `E/graph/s1_symmetry.py:14-20, :125-133`, headroom-chain v0.7.1 490행 |
| 계획 302행 부근 = N3.2 처리 표(v1 고리 문언 없음), v1 고리 전제 문언 자리 | 이 계획 54·316·324·343·464행 |

### H2-8 v0.5 재측정(2026-10-19, 같은 base, HEAD `7760541a`)

| 사실 | 확인한 줄 |
|---|---|
| `gain_l_bounds`는 비활성 경로 없음: 원소 없으면 `_row` None → 앵커 건너뜀 → 전부 빠지면 `found = anchors[-1]`, `SRC_GAIN_L` 충돌(목표 미달) + L 하한 = 최대 앵커. `start_intervals.py:117`이 0 이하 자유 원소를 빼므로 지금도 살아 있음 | `E/search/iv_gain_l.py:64-65, :115-119, :125-129` |
| `area_bounds`: 전류 None이면 W_min 하한을 기록 없이 건너뜀. `WHY_NO_CURRENT`는 예산 선언 때만(예산 없으면 81-82행 먼저 반환) | `E/search/iv_area.py:57-58, :66-69, :81-83` |
| `matching_bounds`·`noise_bounds`: 목표 선언 때만 가드 전체를 `WHY_NO_CURRENT`로 비활성 | `E/search/iv_matching_l.py:110-118`, `E/search/iv_noise.py:65-78` |
| 1회차 전류 소비처 = 네 함수, 여섯 호출 자리 | `E/search/start_intervals.py:292, :295, :296, :327, :332, :333` |
| 원소 값은 매크로 gm(t)의 아핀식(계수는 t 무관) | `E/search/start_intervals.py:95-96, :114-115` |
| 아래 끝 실행 불가면 이분 탐색 건너뜀, 이분 탐색은 단조 가정, 결과 상태 재확인 | `E/search/start_intervals.py:384-396`, 372행 주석(분해능) |
| 387-389행 면적 충돌은 `bottom.area`(None이면 차이 nan) | `E/search/start_intervals.py:387-389` |
| 조기 반환: `rungs` = (), `uncovered` = (), `area_fraction` = None | `E/search/start_intervals.py:263-264` |
| `uncovered`·`area_fraction` 엔진 reader 없음(writer·선언만) | grep(tests 제외): `s0_fields.py:8, :32`, `start_intervals.py:11-12, :245` |
| 출발 단계는 판정하지 않음 | `E/search/start_intervals.py:5` |
| P-G1 추가 자리(v0.4 줄): 53·160·574행 전제 담음, 175·365·426행은 경계 자리 | 이 계획 v0.4(`7760541a`) |

### H2-9 v0.6 재측정(2026-10-19, 같은 base, HEAD `80c1b14a`)

| 사실 | 확인한 줄 |
|---|---|
| gm/ID 선택: 실행 가능한 최대 t, t = 0이 '가장 느슨한 끝'(gm/ID 낮을수록 면적·매크로 실행 가능 쪽) | `E/search/start_intervals.py:23-26`(docstring 7번), `:382` 주석 |
| 최상 칸 `solve(1.0)`은 `refine` 기본값(참), 아래 칸은 `refine=False`, `solve`의 정제 = `use_macro and refine` | `E/search/start_intervals.py:369-370, :377, :404` |
| 면적 충돌 라벨 `estimate_at_gm_id_lo` = `bottom.area` | `E/search/start_intervals.py:388` |
| `matching_bounds`: 절대 정합 목표만 있고 가드가 없어도 전류 None이면 117-118행 반환, 사유는 `(SRC_OFFSET_GUARD, WHY_NO_CURRENT)` 하나 → `SRC_MATCH_L` 경계 소실 사유 없음 | `E/search/iv_matching_l.py:107-118` |
| 조기 반환은 LUT 곡선이 모든 L에서 미정의일 때(`_first_defined` None), 판정에 LUT 필요 | `E/search/start_intervals.py:185-188, :259-264` |

### H2-10 v0.7 재측정(2026-10-19, 같은 base, HEAD `91ea9616`)

| 사실 | 확인한 줄 |
|---|---|
| 매크로 목표 달성 불가 판정은 아래 끝 상태(`bottom.macro_failed`)로 하고, 참이면 `use_macro` 해제 + `macro_target_unattainable_at_gm_id_lo` 충돌(t = 0 뜻) | `E/search/start_intervals.py:378-383` |
| `use_macro`를 끈 뒤 `top`은 다시 풀지 않고 `feasible(top)`만 다시 봄 | `E/search/start_intervals.py:385-386` |
| gm/ID를 낮출수록 게이트 용량이 줄어 매크로(속도)가 풀린다(매크로 실패만으로 실행 불가가 흔함) | `E/search/start_intervals.py:24-26`(docstring 7번) |

## H3. 검증 반영 기록

### v0.1 독립 검증(2026-10-16) → v0.2

| 지적 | 반영 자리 | 처리 |
|---|---|---|
| B1 KVL 정본에 tie 변, X-G2·U-G2가 B2·K-3과 반대 | N0.1 Gs⁺·KVL 관계, N2(B2·K-3·design 41 §6.7-1·-1a 행), N3.3-1·2·8, N3.11 K-a′·K-a″, N5 X-G2, N7.2 K-3·headroom-chain | tie 변 제외, X-G2·U-G2 철회, GC-2를 K-3 구현 card 뒤로(둘 다 `writer_plan.py`). VDS 변 부등식 사이클은 HC-1 소관으로 정의에 명시. 트리 경로 정본을 HC-1 제약 그래프와 하나로(N3.3-3, BD-10). headroom-chain v0.6 Gs⁺ 문언 정정 필요는 사실로만 기록 |
| B2 BD-4 공급 합 판정은 항등식 | F-G21, N3.5-1, N3.11 K-e, BD-4 | 삭제(철회) |
| B3 BD-3 결선 대조는 항등식 | F-G22·F-G23, N3.5-2·3, FR-G17·FR-G18, BD-3·BD-12, U-G10, N7.3-4 | 삭제(철회). 독립 경로 = 오라클 forced·free + U16 배선. 엔진 보조 = `node.terminals` 점검, 숲 불변량 |
| B3 X-G4 '함의' 문장 | N3.5-1, N3.11 K-d, N5 X-G4 | max(봉인 3) 대 합(봉인 2)이라 함의 아님, 상관된 더 엄격한 집계로 정정 |
| B4 `gvgs_self_edge` 정지 소실 | F-G20, FR-G16, N3.3-6, N3.11 K-h, GC-2 (1), BD-11, GD-10 | 삭제 전 S1 구조 쪽으로 이전(거부 먼저) |
| B5 rule_hash 재기록 | F-G24, N3.2 표, N3.7, U-G11, N7.3-11, R-G8 | 사용자 결정 항목. 지문 개선 백로그 포함 여부를 선택지로 |
| 중간 (1) 부채 목록 판정 | N0.1, N3.1-6 (c)(d), BD-9, N7.3-2 | 항목 키 집합 부분집합 + 기준선 지문 검증자 고정 |
| 중간 (2) L-1 도달 조건 | N0.1 실제 읽기, N3.1-1, F-G27, A-5 | 엔진 진입점 도달 필요 |
| 중간 (3) 동적 접근 처리 종류 | F-G30, N3.1-1·6, N3.2 표 | '정적 해석 형태로 바꾸기' 추가(GC-7) |
| 중간 (4) 봉인 8 | N3.3-4, U-G9, X-G10, N4-2, R-G4 | 재작성 대신 삭제(기본안)·구조 불변량 대체·재작성 선택지 |
| 중간 (5) MNA 잔차 공허 | F-G28, N3.5-5, FR-G11, U-G5, N3.11 K-f | 넣지 않음(기본안), 조건수는 선택지 |
| 중간 (6) GC-2~GC-4 범위 | N5 X-G9, U-G12, N7.1 착수 조건 | X 항목 + 착수 승인 |
| 중간 (7) GC-5 충돌 뒤 처리 | N3.6-3, U-G13, N4-5 | 선택지 정의(기본안 실행 불가) |
| 중간 (8) card id 규칙 | N0, N3.1-6 (e), N3.2 표 card·읽는 결정 칸 분리, GC-8 신설 | U-G4 → GC-7, U-G7 → GC-8 |
| 중간 (9) L-5 AST 한계 | N3.1-5, N3.11 A-3 | 자료 흐름 꼴 미탐지 명시 |
| 낮음: F-G9 `dc_inputs.py:31` | N3.2 표 `device.value` 행 | `:7, :36` |
| 낮음: H2-1 18 → 19 | H2-1 | 정정 |
| 낮음: 400행 H3 → H1 인용 | N5 끝 괄호 | H1로 |
| 낮음: 460행 '파일럿' | N7.2 offset-strategy 항목 | 이름 제거 |
| 낮음: `rel_l_class`도 `gs_groups` 사본 | F-G7, F-G26, N3.2 표, U-G3 | 소비 이동 뒤 삭제 대기 |
| 낮음: M-G1c·M-G2b 측정 불필요 | N6 끝 괄호, N3.3-5, N3.4-3 | 지움(정의로 같음, 코드 읽기로 답). M-G2c(항등)도 지움 |
| 낮음: G_vgs⁺ → Gs⁺(FR-9) | N0.1, 본문 전체 | 통일 |
| 낮음: design 41 §6.7-1 인용 | N2 표, N3.3-2 근거 3, N8 R6 | 추가 |
| 낮음: X-G7에 `stacked_vsb`·`same_as` 미구현 | F-G29, N2 S1 구조 행, N5 X-G7, N3.10 | 사실 추가 |
| 낮음: 정상 D 필드 10개 | F-G3, N3.1-2, GC-1 | 처음부터 출력 전용 목록 |

* 검증자 측정물은 그 agent scratchpad `df/rows.json`·`cls.txt`다(인계 문서 51행). 이 개정은 그 파일을 다시 읽지 않고, 지적 문장과 이 worktree 코드 재측정(H2-5)으로 반영했다.

### v0.2 재검증(2026-10-19) → v0.3

| 지적 | 반영 자리 | 처리 |
|---|---|---|
| M2 부채 목록 우회 | N0.1 부채 목록, N3.1-6 (d)(e), BD-9, N7.3-2, R-G2, GD-3 | 키 = (규칙, 최소 단위), 지문 대상에 규칙 코드·진입점·출력 모듈·허용 파일·L-5 등록표·L-4 칸 목록·L-2 목록, 항목 제거는 대상 코드 변경 검증자 확인 |
| M3 봉인 8 대체 주장 | F-G31, N2 DEC-88 행, N3.3-4, N3.5-3, N3.10 472행, N3.11 K-c, N5 X-G10, U-G9 | 472행의 일은 봉인 2가 이미 함, 숲 불변량은 별개 회계 검사, 선택지 = 삭제/유지(목록 교체) |
| M4 U-G13 (가)와 코드 불일치 | F-G32, N3.6-1·3, N3.8, N3.11 K-j, N5 X-G11, BD-13, U-G13, GC-5 선행, N7.3-6 | 꺼지지 않는 충돌 표지, 사다리 칸 단위 처리, 결정 6 뒤 성립 조건, X 항목 |
| M5 V9·용어집·LR5·design 41 관계 엣지 | F-G34, N2(92·553·920·589·917·1533행), N3.2 표, N3.10, X-G7, U-G3 | 상위·design 개정 항목, `matching_*` 삭제는 V9 개정 뒤 |
| M6 BD-10 | N0.1 트리 경로, F-G33, N3.3-3, BD-10, GD-2, N7.2, 완료 조건 3 | 정본 = `node.dc_writer`, 경로 = 순수 함수 하나, 필드 저장 금지, headroom-chain 개정 불필요 |
| M7 다른 card 완료 조건 | N3.10 card 표 행 3개, N3.5-2, N7.2, U-G6·U-G10 | 브리핑 → S-7 상위 개정 항목 |
| L1 headroom-chain v0.7.1 기준, 포트 표현, K-3 모사 측정 | Summary, N0.1 Gs⁺, N3.3-1 표, N6, N7.2, N8 R7 | v0.7.1 기준, '성분마다 뿌리·오프셋 하나, 나머지 포트는 MOS writer', GC-0a·GC-0b 분리(K-3 병합 master에서 잼), M-G1 원인 (iv) as-built tie 삭제 |
| L2 `declared`·`applied_facts` | F-G3, N3.1-1·2, N3.2 표 | 정상 8개만 초기 출력 전용, 2개는 GC-7까지 부채 |
| L3 M-G3 기준선 시점 | N6 머리·표, GC-1 | GC-0a 예비, GC-1에서 GD-1 뒤 재측정 |
| L4 L-5 기준선 완전성 | F-G13, N3.1-5, N7.3-1, A-3 | 7자리 거부 증거, 속성 꼴·변수 경유 꼴, 못 잡으면 멈춤 |
| L5 BD-11 근거·rule_hash·등록·K-h | F-G20, F-G35, N3.3-6·7, N3.11 K-h, BD-11, GD-10, U-G11, B-G3 | '같은 층·같은 시점', 정지 블록 rule_hash, 등록 4자리 삭제, 비대칭 물리 근거 없음(보존만) |
| L6 K-d 식 | N3.5-1, N3.11 K-d | ID(e^Δ − 1), 1차 근사 표기 |
| L7 X-G9에 GC-8 | N5 X-G9, U-G12, N7.1 | 추가 |
| L8 (L6과 같음) | -- | -- |
| L9 BD-5 W_min 소자 | N3.6-2, BD-5, GD-7 | design 항목 |
| 숲 불변량 성립 조건 | N3.5-3, GD-11 | design 항목으로 기록 |
| U-G5·U-G7 과잉 | N10.2 끝 괄호, N10.4 B-G1·B-G2, N1.2, FR-G11, N7.1(GC-4 비움) | 백로그로 내림 |

### v0.3 재검증(2026-10-19) → v0.4

| 지적 | 반영 자리 | 처리 |
|---|---|---|
| N1 (1) U-G13 (가) 끝 처리 없음(`final = bottom` 칸 0 대체, `_report` IndexError) | F-G32, N3.6-3 (가) '끝 처리', N5 X-G11, U-G13, GC-5, N7.3-6, GD-7 | 전류 충돌이면 칸 0도 뺌 → 빈 사다리, θ 성분 `uncovered`, 층 0 상자 중심 출발, `_report` 빈 사다리 처리, 면적만 실행 불가인 아래 끝은 보존. 틀린 d/s 선언에서 실제 발생 명시 |
| N1 (2) 1회차 전류 0 이하 처리 없음 | F-G32, N3.6-3 (가) '1회차', U-G13, GC-5, N7.3-6, GD-7 | 자리값 없이 빼고, 경계 함수 다섯 자리(`noise_bounds` 포함, 재측정)에서 `WHY_NO_CURRENT`와 구분되는 전류 충돌 사유로 비활성 + `StartConflict` 기록. 소비처 없는 표지는 FR-G12·완료 조건 6 위반으로 명시 |
| N2 결정 6 이미 병합 | N2 K-3 행, F-G36, N3.6-3 성립 조건, N3.11 K-j, GC-5, N7.2(K-3·결정 6 항목), R-G5, BD-13, U-G13 | BD-13 충족(`c8d156e3`), GC-5 선행에서 뺌, K-3 순서 조건 충족 |
| L-a 규칙 L 지문 파일 | N3.1-6 (d), GD-9, GC-1, N7.2 LT-1 | 규칙 L 코드는 별도 파일, 지문은 그 파일만(helper 의존 포함) |
| L-b 기준선 측정 독립성 | N3.1-6 (c), N6 M-G3, GC-1 | 검증자 독립 측정 스크립트, 규칙 L 코드와 차이 나면 기록 후 멈춤 |
| L-c 아래 칸 표지 출처 | GD-7 | `_placed` 고정점 마지막 상태에서 읽음, 새 계산 없음 |
| L-d 트리 경로 함수 단일성 | N7.3-3, N3.10 P-G2 | 검증자 확인 항목. headroom-chain 완료 조건 문언은 후속 권고로만 |
| (지시) DEC-64 v1 고리 문언 | N3.10 P-G1 | 사용자 결정 대기 항목만 추가, 문언은 고치지 않음 |

### v0.4 재검증(2026-10-19) → v0.5

| 지적 | 반영 자리 | 처리 |
|---|---|---|
| M1 경계 함수 None 처리 사실 틀림 | F-G32 '1회차 전류의 소비처', H2-7 행 정정 표시, H2-8, N3.6-3 '1회차', GD-7, GC-5 | 함수별 사실로 정정(`gain_l_bounds` 목표 미달 오기록·최대 앵커 L 하한, `area_bounds` 무기록 건너뜀, 가드 둘은 목표 선언 때만). 고칠 자리를 GD-7·GC-5 범위에 명시 |
| M2 혼합 경우 미정의 | N3.6-3 't 의존'·'선택점 고르기'(가-1~가-3)·'빈 사다리', N5 X-G11, U-G13, GC-5, N7.3-6 | 선택지 셋 나열, 권고 (가-1) 사다리 격자 탐색(근거: 단조 가정 없음, 분해능 = 사다리 칸 폭, 사다리 계산 재사용), 결정은 사용자. 원소 값이 gm(t) 아핀이라 충돌이 t에 따라 바뀜을 명시. 빈 사다리 범위를 '선택 후보 모두 충돌'로 |
| L1 '다섯 자리' 대 여섯 호출 | F-G32, N3.6-3, U-G13, GC-5, N7.3-6, GD-7 | '네 함수, 여섯 호출 자리'로 통일, 완료 조건 6은 여섯 자리마다 |
| L2 원인과 다른 면적 충돌 | N3.6-3 '원인과 다른 면적 충돌 기록', U-G13, GC-5, N7.3-6 | 전류 충돌 상태면 면적 충돌을 기록하지 않음, 면적 충돌은 충돌 없는 상태의 예산 초과만 |
| L3 빈 사다리 출력 정렬 | GD-7, GC-5 | 빈 사다리 출력 형식(`uncovered` = 칸 0 성분 전부, `area_est_m2`·`area_fraction` = None), `start_intervals.py:264` 조기 반환을 같은 `uncovered` 규칙으로 맞추고 사유로 구분(기본안, 두 필드 엔진 reader 없음) |
| L4 (다) 대신 상자 중심 계속의 근거 | N3.6-3, U-G13 | 출발 단계는 판정하지 않음(EP-7), 틀린 선언 거부는 봉인 7 한 곳, 모든 후보 충돌 = 틀린 선언은 증명 안 됨 |
| P-G1 자리 보완 | N3.10 P-G1 | 53·160·574행(v0.4) 추가, 175·365·426행은 경계 자리로 대상 아님 메모. 줄 번호를 v0.4 기준으로 표시, 표 행을 한 줄로 |

### v0.5 재검증(2026-10-19) → v0.6

| 지적 | 반영 자리 | 처리 |
|---|---|---|
| N1 (가-1) (ii) '충돌 없는 최대 t'는 혼합 경우에 늘 t = 1 | N3.6-3 (가-1), X-G11, U-G13, GD-7 | '충돌 없는 최소 t'로(지금 아래 끝 대체 = 가장 느슨한 끝, docstring 7번·382행). 면적 충돌 라벨 `estimate_at_gm_id_lo`가 t ≠ 0에서 틀리므로 기록 형식을 GD-7 항목에 |
| L-a 적용 조건 통일 | N3.6-3 제목·본문 (a)~(c)·빈 사다리, 기본안 문장, X-G11, U-G13, GC-5, N7.3-6 | '아래 끝이 전류 충돌(최상 칸 무관)'로 통일, 최상·아래 모두 충돌·중간만 충돌 없음 경우 포함, 완료 조건 6에 세 픽스처 |
| L-b `SRC_MATCH_L` 사유 누락 | F-G32, N3.6-3 '1회차', GD-7, GC-5 | 사실 문장 정정(절대 정합만 있을 때 L 경계 소실 사유 없음), 고칠 내용에 `SRC_MATCH_L` 전류 충돌 사유 추가 |
| L-c 조기 반환 정렬과 비트 동일 충돌, 재사용 문언 | N4-4, N6 M-G8 신설(GC-5 착수, 기대 0), N7.3-6 예외, N3.6-3 (가-1) 재사용 | 예외 명시 + 측정 항목. 재사용은 격자 겹침·정제 설정(`refine`·`use_macro`) 동일일 때만으로 정정 |

### v0.6 재검증(2026-10-19) → v0.7

| 지적 | 반영 자리 | 처리 |
|---|---|---|
| N1′ (ii) 점의 매크로 실패 미처리 | N3.6-3 (가-1) '(ii) 점의 실행 불가 원인 기록과 `use_macro`', '원인과 다른 면적 충돌 기록', X-G11, U-G13, GD-7, N7.3-6 | `use_macro` 해제 판정을 전류 충돌 아래 끝에서 (ii) 점(충돌 없는 가장 느슨한 점)으로 옮김(기존 380-383과 같은 성격). 해제 뒤 격자 상태를 다시 풀지 않고 면적만으로 (i) 재적용(기존 385행과 같음). 실행 불가 원인마다 t를 담아 기록. 픽스처(매크로만·면적만·둘 다·충돌 아래 끝 `macro_failed` 무시) 추가 |
| L-a′ (c)·빈 사다리 조건 문언 | N3.6-3 (c), '빈 사다리' 항목 | '선택 후보(격자 점과 t = 0)가 모두 전류 충돌'로 통일 |
| L-c′ M-G8이 LUT 없는 card 0 표에 있음 | N6 표에서 행 삭제, N4-4에 정의(산출·주체·LUT 필요) | GC-5 착수 측정으로 이동, N6 표 순서 M-G6 → M-G7 복원 |

### 사용자 결정 O-13(2026-10-19) → v0.8

원문: 사용자 "1~5까지 권고대로"(`wt/_drafts/user_decisions.md` 632행). 이 계획에 걸리는 것은 (1)과 (4)다.

| 결정 | 반영 자리 | 처리 |
|---|---|---|
| (1) DEC-64 v1 해석 (가) | N0.1 Gs⁺·KVL 관계(53·54행), N2 O-13 행 신설·DEC-64 행(161행), N3.2 `gvgs_summary` 행(289행), N3.3-1 표(317행)·N3.3-2(325행)·N3.3-8(344행), N3.5-3 성립 조건(366행), N3.10 DEC-64 개정 행(453행), N3.11 K-a′(490행), N7.2 headroom-chain Gs⁺ 문장(600행), N3.10 P-G1 '결정됨' | 같은 DC 등식 없음, 포트 경로 둘 이상이면 ΔV 소거 KVL 하나(`cycle_vgs`) 남음, 대칭이면 묶음과 중복. Gs⁺ 정의('나머지 포트는 MOS writer')와 맞음을 확인(트리 경로 밖 포트 경로의 비트리 MOS 변이 그 KVL을 닫음) -- 정의 문언 보강. 숲 회계 불변량이 이 고리를 포함해 성립함을 한 줄. 줄 번호는 v0.8 기준 |
| (1)의 정정 목록 밖 | N2 DEC-64 행, N3.10 DEC-64 개정 행 | 처음에는 상위 계획 DEC-64 263행 v1 문언을 오케스트레이터 확인 항목으로 표시했다. 오케스트레이터 전달로 상위 계획 card IT-1 반영 커밋 `3fd202b`(브랜치 `plan/gb-k3-card`, v6.16)에서 이미 O-13 (1) 문언으로 정정된 것을 `git show 3fd202b:…gain-budget-gmid-sizing.plan.md` 263행으로 확인하고, 두 자리를 '3fd202b에서 정정됨(병합 전)'으로 바꿨다(같은 판 v0.8 후속 커밋) |
| (4) U-G 전부 권고대로 | N10.2 머리·각 행 '결정됨(O-13)', N5 X-G 상태 칸 '승인(O-13, …)', N3.6-3 (가-1) '결정됨'·(가-2)·(가-3) '선택 안 됨, 기록'·빈 사다리 조건에서 (가-3) 갈래 삭제, N3.10 봉인 8 행 | U-G1 (가), U-G3 항목별(card 0 대조 일치 항목), U-G4 (가), U-G6 미룸, U-G8 넣기, U-G9 (가), U-G10 넘기기, U-G11 (가), U-G12 승인(GC-8은 B-G2 뒤 재질문), U-G13 (가) + (가-1), X-G11 승인 |
| 재검증 L-1((가-2) 관련) | -- | (가-2) 미선택으로 소멸 |
| 재검증 L-2(t_p 격자 기준 근사) | GD-7 | 기록 문구에 '격자 기준' 명시 한 줄 |
| (v0.8 diff 확인 '승인 가능' 뒤 정정) K-3 구현 card id | F-G19, N3.10 card 표 행, N7.2 K-3 항목, R-G6 | 'card id 없음/미부여'를 상위 card IT-1(N6.5, `plan/gb-k3-card` `3fd202b`, red test는 `E/tests/sizing/test_writer_plan.py` 안 새 test 함수 -- 상위 X-IT3·F-IT4)로. `3fd202b`의 상위 계획 1270·1309·1340행으로 확인 |
| (같은 정정, 비차단 낮음) 남는 KVL의 종속 분류 | N0.1 Gs⁺, N3.2 `gvgs_summary` 행, N3.3-1 표·N3.3-2·N3.3-8, N3.5-3, N3.11 K-a′ | 일반 문장의 '`cycle_vgs` 종속'을 '비트리 MOS 종속(보통 `cycle_vgs`, 경우에 따라 `parallel_vgs`·`fixed_vgs`, `E/sizing/writer_plan.py:191-196`)'으로. 파일럿 예시(M1b `cycle_vgs`)는 그대로. 지적은 53·317행이었고 같은 일반 문장 다섯 자리도 맞췄다. 줄 번호는 재측정(분류 191-196행) |
| (같은 정정, 비차단 낮음) 상위 정정 표시 | N2 DEC-64 행, N3.10 DEC-64 개정 행 | '(병합 전)' → '(diff 확인·병합 전)' |

### 사용자 결정 O-14(2026-10-19) → v0.9

원문: 사용자 "1은 (가′), 2 승인, 3 기본안, 4 권고대로"(`wt/_drafts/user_decisions.md` 633행). 이 계획에 걸리는 것은 (1)과 (2)다.

* **원래 취지와 다름 아님**: v0.3~v0.8은 '경로를 필드로 저장하면 `node.dc_writer`의 사본'이라는 논리로 순수 함수 하나만 두었다. 그러면 소비자 셋이 각자 같은 경로를 다시 계산하게 되어, 상위 원칙(graph 단일 정본 -- 계산값은 필드로 한 번, 재사용 -- NFR-2·WP-10)에서 벗어나 있었다. O-14 (1)은 그 원칙으로 돌아간 것이다. 쓰기 계획 블록의 자기 출력 필드는 writer가 하나라 사본이 아니다(DEC-83 충족).

| 결정 | 반영 자리 | 처리 |
|---|---|---|
| (1) (가′) 트리 경로 = 쓰기 계획 블록 자기 출력 S0 필드 | Summary 3, N0.1 트리 경로, FR-G8, NFR-G3, N2 FR-9 행·O-14 행 신설, N3.3-2·N3.3-3(전면 개정), N3.3-4 (나) 문장, N3.9, N3.10 DEC-64 행·`E/sizing/CONTRACT.md` 행·headroom-chain 문단·P-G2, N5 X-G1, N6 M-G1, GC-2, N7.2 headroom-chain 항목, N7.3-3, R-G9, BD-10, U-G1, GD-2, GD-8 | '저장하면 사본' 논리 철회, writer = 쓰기 계획 블록, 소비자 셋(규칙 L-1 대상), 만드는 card = IT-1 뒤 먼저 병합되는 소비자 card(기본안 HC-1, 아니면 GC-2 첫 단계), 완료 조건 3을 '필드 하나·블록 밖 재구성 0'으로 |
| (1) WP-10 계측 | NFR-G4, N7.3-9, R-G9 | cProfile + 블록 밖 함수 포함 같은 인자 반복 호출 0(상위 WP-10 315행, master `f2852c36` 판), 검증자 판정 |
| (2) 상위 IT-1 병합 | F-G19, N2 DEC-64 행, N3.10 DEC-64·card 표 행, N7.2 K-3 항목, R-G6 | 'diff 확인·병합 전' → 'master `f2852c36` 병합됨'(card 정의만, 구현은 아직) |
| headroom-chain 쪽 개정 | N3.3-3 끝, N3.10 headroom-chain 문단, N7.2 | v0.7.1 317행 '경로 목록 저장 안 함'·완료 조건 WP-10은 그 계획 소관으로 표시만 |

### 사용자 결정 O-15(2026-10-19) → v0.10

원문: 사용자 "A~E 권고대로, oracle 승인"(`wt/_drafts/user_decisions.md` 634행). 근거는 원칙 감사 메모(오케스트레이터 scratchpad `principle_audit/notes.md`)다. 메모의 file:line은 이 worktree에서 다시 읽었다. 재측정 차이: VGS = 0 첫 마디 판정은 `derived_fns.py:43`(메모는 :47), 한 단계 `.known` 읽기는 `layer0_center.py:485`(메모는 :487)이고, 두 단계 이상 따라가는 tie 사슬은 `block_columns.py:181-184`·`scc_order.py:122-127`이다(`achievability.py:315-317`은 tie 관계 한 단계 읽기).

| 결정 | 반영 자리 | 처리 |
|---|---|---|
| (A) U-G4 범위 보완 | F-G14, N3.1-5 L-5 등록표, N3.2 `dc_conduction_floor` 행, GC-7, U-G4 행, BD-8, GD-12, N7.3-13 | 네 번째 자리 `derived_fns.py:36-47` `_conduction_ok`(`edge_costs`) 추가, 정본 = LUT memo 파생 `conduction_mask(kind, w_key)`(VGS = 0 마디 찾기 한 곳), `cell_floor`·`edge_costs`가 읽음, `sctx.cell_floors` 제거, `dc_conduction_floor` 출력 전용. 같은 캐시를 쓰는 `_peak_floor`의 자리는 GD-12 |
| (E) 범위 확장 | F-G37~F-G39, N1.2 범위 행, NFR-G4, N5 X-G12 신설, GC-9 신설, GC-5 범위, N7.2 XRUN-F1, N7.3-3·N7.3-13, FR-G15·N4-1·N7.3-7(GC-9 무동작), N7.3-2, GD-13 | 기저 float 변환 1회, 정확 MOS 전류 공용 함수, `current_cone` 소비자 기저 읽기(사본 삭제는 U-G3 절차), `_vds_floor` → `lut.derived`(GC-9). 완료 조건 3을 '두 단계 이상 따라가는 경로 재구성'으로 좁힘, 블록 안 local memo 허용·`bracket_root` 뒤 같은 점 재풀이 금지(GC-5). X-G12 '승인(O-15 (E))' |
| (C) 차분 제약 그래프 | N3.2 R4 행, GC-8, N10.4 B-G2, X-G9, U-G12, N7.3-2 | B-G2는 O-15 (C)로 흡수(닫힘). R4 처리는 headroom-chain card 소관. GC-8은 그 card id가 생길 때까지 부채 항목 자리표 |
| 머리 | Status, N2 O-15 행 | 'v0.10 -- O-15 반영, 재검증 전' |
| (오케스트레이터 답, 같은 판 후속 커밋) `_peak_floor` 자리 | GD-12, GC-7 | `_peak_floor`(`cell_floor.py:36-50`)도 LUT만의 순수 함수라 같은 원칙(O-15 (A))으로 LUT memo 파생 함수로 확정. design은 이름·키만 정한다 |
| (같은 답) GC-8 자리표 | -- | 그대로 둔다. headroom-chain v0.7.4가 R4를 맡을 card id를 정하면 오케스트레이터가 알리고, 그때 부채 항목 card id를 바꾼다 |
| (같은 판 후속 커밋) headroom-chain v0.7.4(`wt/headroom-k3-plan` `752659ee`)의 R4 분담 | GC-8 행, N3.2 R4 행, N1.2 범위 표 두 칸, N2 O-15 행, N5 X-G9 상태, N7.3-2, U-G12, N10.4 B-G2 | 그 계획 N3.4(소비자별 처리 표, 배선 분담 기본안)·F-23·완료 조건 12를 직접 읽었다. GC-8은 자리표가 아니라 실제 card다: `ls_swing`·`headroom_bound`·`order_terms` 배선 + 정책 통일(선언 triode = on_mask VDS 하한, 비전도 변 제외) + 사본 삭제, 선행 HC-1, 결과가 바뀔 수 있어 무동작 card가 아님(변화표). `iv_headroom`은 HC-1. 다른 이름 개념 셋은 그 계획 표가 정본. `order_terms`는 원래 R4 범위 밖이었다가 O-15 (C)로 들어왔다고 표시. B-G2는 'O-15 (C)·O-16 (3)으로 닫힘, 정의 차이 판단은 headroom-chain N3.4 표'. U-G12의 GC-8 재질문은 '재질문 대상 소멸 -- O-15 (C) 승인 범위'. 확인: O-15 (C)가 네 곳의 정본 읽기를, O-16 (3)이 '같은 개념은 하나로'를 승인했으므로 GC-8의 내용은 사용자 결정 범위 안이다. 소비자별 card 분담(HC-1 대 GC-8)은 headroom-chain의 기본안이다. ls_swing 39·53행, headroom_bound 58·75행, block_columns 172-177행을 재확인했다 |

### v0.10 독립 검증(`429a84eb`, '수정 필요') → v0.10 후속 커밋

기본안은 근본원칙(같은 개념은 하나, 다른 양은 다른 이름)으로 정했고, 계획에 '오케스트레이터 기본안'으로 표시했다.

| 지적 | 반영 자리 | 처리 |
|---|---|---|
| 1 O-16 (3) 예외 누락 | F-G14, N7.3-13 | 봉인 9 소자별 I_off 동작점 보간(`seal_conduction.py:26-31` `_off_current`)은 검증 경로(판정 권한)라 단일화 예외로 명시 |
| 2 GC-8 '비전도 제외'를 θ 없는 소비자에 그대로 못 씀 | GC-8 (2) | 전도 집합은 소비자가 알 수 있는 정보로 평가한다(기본안). θ 있는 소비자(`ls_swing`, R-1′)는 θ 전도로 제외하고, θ 없는 소비자(`headroom_bound`, `order_terms`)는 구조적 전도를 쓴다. `dc_current_basis`가 구조적 0 전류 MOS를 정지시키므로(`current_basis.py:14`) 제외 없음. 근거를 병기했고, headroom-chain 334·335행과 같은 문언이다 |
| 3 완료 조건 13 대 GD-12 `current_box` 불일치 | N7.3-13, GD-12 | `current_box` I_off 값(θ 전류 상자 하한)은 다른 개념이라 완료 조건 단일화 대상에서 뺐다. VGS = 0 마디 찾기는 `conduction_mask` 모듈 한 함수로 모으고 `current_box`도 그것을 부른다. GD-12 열린 질문을 닫았다 |
| 4 `_vds_floor` 이동 순서 | F-G38, GC-9, X-G12, N1.2, N7.2, N7.3-13, GD-13 | 선언 triode 항으로 HC-1(search)이 먼저 쓰므로 이동을 headroom-chain HC-S로 옮겼다(기본안). GC-9 범위에서 빼고 선행에 HC-S를 넣었다 |
| 5 gm/ID 정점 마디 중복 | GD-12, N7.3-13 | 정점 마디는 LUT memo 파생 함수 한 곳에서 계산한다(기본안). 재측정 결과 `cell_floor.py:45-46`(지적은 44-45), `derived_fns.py:39-41`(지적은 40-41) |
| 6 옛 문구 | 머리 관련 계획(19행), N7.2 headroom-chain 항목, N8 R7, U-G12 권고 칸, history 0.10 행, GC-8 선행(HC-S → HC-1 → GC-8), GC-8 (4) | v0.7.4 개정 중 표기, 재질문 소멸 표기, 'GC-8 실제 card', `edge_costs.vds_min_v` 소비자 셋(`start_intervals.py:280`, `_helpers_curves.py:111`, `derived_fns.py:106`)을 'VDS 변 격자 하한 비용' 이름 부여 대상에 포함 |
| (유지) 트리 경로 필드를 만드는 card | -- | HC-1 기본안 유지 |

## Version History

| 판 | 날짜 | 변경 |
|---|---|---|
| 0.1 | 2026-10-16 | 초안. 사용자 O-10 (2)·(4), P-1, 사용자 원문(KK-1) 반영. 재측정 H2 |
| 0.2 | 2026-10-19 | v0.1 독립 검증 반영(H3). KVL 정본에서 tie 변 제외(B2·K-3 따름), X-G2·U-G2·BD-3·BD-4 철회, 독립 검증 = 오라클 forced·free(U16 배선), 엔진 보조 검사 둘, `gvgs_self_edge` 정지 이전, 봉인 8·MNA·rule_hash·충돌 뒤 처리·범위 확장을 사용자 결정으로(U-G9~U-G13), 부채 목록 집합 판정, 규칙 L-1 도달 조건, 트리 경로 정본 하나(HC-1), GC-8 신설. 재측정 H2-5 |
| 0.3 | 2026-10-19 | v0.2 재검증 반영(H3). 봉인 8 '대체' 주장 정정, 출발 충돌 표지·사다리 칸 처리·결정 6 선행(X-G11·BD-13), 트리 경로 정본 = `node.dc_writer`(경로 필드 금지), V9·용어집·LR5·design 41 관계 엣지 개정 항목, 다른 card 완료 조건을 상위 개정 항목으로, 부채 목록 지문 대상 확대·최소 단위 키·제거 조건, GC-0a·GC-0b 분리, U-G5·U-G7 → 백로그 B-G1·B-G2, B-G3 추가. 재측정 H2-6 |
| 0.4 | 2026-10-19 | v0.3 재검증 반영(H3). U-G13 (가)에 끝 처리(모든 칸 전류 충돌 → 빈 사다리·상자 중심 출발·`_report` 빈 사다리 처리)와 1회차 전류 충돌 처리(경계 함수 다섯 자리) 정의, F-G32 행 근거 추가. 결정 6 이미 병합(`c8d156e3`, F-G36) → BD-13 충족, GC-5 선행·K-j·R-G5·K-3 순서 조건 정정. GD-7(아래 칸 표지 출처)·GD-9(규칙 L 별도 파일·지문), 기준선 독립 측정, 트리 경로 함수 단일성 검증자 확인, N3.10 대기·후속 항목 P-G1(DEC-64 v1 고리 문언, 사용자 결정 대기)·P-G2. 재측정 H2-7 |
| 0.5 | 2026-10-19 | v0.4 재검증 반영(H3). 경계 함수 None 처리 사실 정정(F-G32, H2-7 정정 표시), 네 함수·여섯 호출 자리별 처리와 고칠 자리(GD-7·GC-5), 혼합 경우 선택지 (가-1)~(가-3)과 권고 (가-1), 충돌의 t 의존, 빈 사다리 범위·원인과 다른 면적 충돌 제거·출력 형식(조기 반환 정렬), (다) 대신 상자 중심 계속의 근거, P-G1 자리 보완. 재측정 H2-8 |
| 0.6 | 2026-10-19 | v0.5 재검증 반영(H3). (가-1) 실행 불가 대체를 충돌 없는 최소 t로, 면적 충돌 기록 형식 GD-7, 적용 조건 '아래 끝이 전류 충돌(최상 칸 무관)' 통일, `SRC_MATCH_L` 사유 누락 사실·처리, 조기 반환 정렬 예외와 M-G8, 재사용 조건 정정. 재측정 H2-9 |
| 0.7 | 2026-10-19 | v0.6 재검증 반영(H3). (가-1) (ii) 점의 매크로 실패 처리(`use_macro` 해제 판정 위치 이동, 면적만으로 재선택, 원인별 t 포함 기록), (c)·빈 사다리 조건 통일, M-G8을 N6 표에서 N4-4로 이동. 재측정 H2-10 |
| 0.8 | 2026-10-19 | 사용자 결정 O-13 반영(H3). DEC-64 v1 해석 (가)로 P-G1 자리 정정(같은 DC 등식 없음, 포트 경로 둘 이상이면 ΔV 소거 KVL 하나 남음, 대칭이면 묶음과 중복), Gs⁺ 정의 보강·숲 불변량 성립 한 줄, U-G 전부 결정됨·X-G 승인 표시, (가-2)·(가-3) 기록화, GD-7 격자 기준 명시 |
| 0.9 | 2026-10-19 | 사용자 결정 O-14 반영(H3). 트리 경로를 쓰기 계획 블록 자기 출력 S0 필드로(소비자 셋, '저장하면 사본' 논리 철회, 만드는 card 기본안 HC-1/GC-2), WP-10 계측 완료 조건·NFR-G4, 상위 IT-1 병합됨 표시. 원래 취지와 다름 아님(원칙으로 복귀) |
| 0.10 | 2026-10-19 | 사용자 결정 O-15 반영(H3). (A) 전도 술어 정본 `conduction_mask`(네 번째 자리 `edge_costs`, `sctx.cell_floors` 제거), (E) 원칙 감사 범위 확장 GC-9·X-G12(기저 float 1회, 정확 MOS 전류 함수 하나, `current_cone` 기저 읽기, 완료 조건 3 좁힘, 블록 안 local memo·같은 점 재풀이 금지 -- `_vds_floor` 이동은 후속 커밋에서 headroom-chain HC-S로 옮김), (C)·O-16 (3)으로 B-G2 닫힘·**GC-8 실제 card**(`ls_swing`·`headroom_bound`·`order_terms` 배선, headroom-chain v0.7.4 분담), 후속 커밋에서 독립 검증 '수정 필요' 6건 반영 |
