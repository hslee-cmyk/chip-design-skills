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
| (같은 판 후속 커밋) 2번 근거 정정 | GC-8 (2) θ 없는 소비자 | 처음 근거(`current_basis.py:14` 정지)는 `mos_zero_current_structural`만 덮어 불완전했다. headroom-chain v0.7.5(`43cf75c9`) 341행과 같은 규칙·근거로 맞췄다: 자기 맞바꿈은 graph가 정지(`s1_symmetry.py:16-18`), 대칭·KCL이 0으로 정하는 다른 구조적 0 가지는 search `zeros`로 θ에서 빠짐(`search/CONTRACT.md:590-591`) → 구조적 0 전류로 확정된 MOS가 있으면 그것만 빼고, 없으면 제외 없음 |
| (재검증 `a13af8a2` → 같은 판 후속 커밋) #4 다른 이름 개념 | GC-8 (4) | headroom-chain v0.7.5가 '신호 고정 VGS 변'을 철회. 개념은 둘(VDS 변 격자 하한 비용, VGS 변 격자 하한 비용). `ls_swing` VGS 등식 변은 소속 기준 공동분석 백로그, as-built 보존 |
| #5 Gs⁺ VGS 변 필드 | GC-8 (1)(3), N3.3-3, GC-2, GD-2 | headroom-chain 완료 조건 12가 넘긴 `headroom_bound._edges` VGS 절반의 Gs⁺ VGS 변 필드 읽기를 GC-8에 넣었다. 쓰기 계획 블록 출력 두 필드(뿌리 경로, Gs⁺ VGS 변)를 HC-1이 만들고 못 하면 GC-2 |
| #2 구조적 0 전류 MOS 집합 정본 | GC-8 (2), GD-2 | `zeros`(`current_symmetry.py:110-131`, `search_domain.py:166`)는 `graph/kernel: search_domain` 칸 `SearchDomain.zeros`(`search_values.py:92`, writer `search_domain.py:172-175`)에 이미 있으므로 그 필드가 정본, `order_terms`·`headroom_bound`가 읽는다. 층 순서가 맞지 않으면 앞 층 S0 필드로(기본안, headroom-chain과 같은 문언) |
| #2 후속(headroom-chain `b35af834` 확인) | GC-8 (2), GD-2 | `search_domain` 필드 writer는 search 층(6), 소비자 `order_terms`(sizing 4)·`headroom_bound`(metrics 5)는 아래 층이라 데이터 흐름 역전(`structure_checks.py:24-30`, `s0_fields.py:20, :27`, `search_domain.py:166, :173` 재확인). 기본안을 '구조적 0 전류 MOS 집합을 sizing 층 이하 S0 graph 필드 하나로 올리고(`dc_current_basis` 쪽), `search_domain`도 그 필드를 읽음, 처음 읽는 card(GC-8 또는 먼저 병합되는 card)가 만든다'로 바꿨다 |
| (재검증 `7ed2e298` → 같은 판 후속 커밋) 문언 3곳 | GC-8 (2), GD-2 | (1) 올리는 것은 `zeros`만이 아니라 전류 대칭 결과 전체(`ties`·`negated`·`zeros`, `current_symmetry.py:75-131` 한 번의 기약 행사다리꼴), `search_domain`은 읽기만, writer 입력에 spec `search.untie_orbits`(`current_symmetry.py:15, :40-51`). (2) 만드는 card = HC-1(`iv_headroom`이 θ 없는 구조적 전도 소비자라 처음 읽음), 못 하면 GC-8 -- GD-2 card 칸도 맞춤. (3) θ 없는 소비자에 `iv_headroom` 추가(`iv_headroom.py:152-175`가 `start_intervals.py:99-119`보다 앞), headroom-chain 인용을 `b35af834` 341-344행으로 재측정 |
| (diff 확인 `c57b9f5d` '승인 가능' 뒤 낮음 2건) | 머리 19행·Status, GC-8, N7.2, N8 R7 | headroom-chain 인용 기준판을 v0.7.5 최종 `c0d96517`(341-344행 재확인)로, 판 표기 `43cf75c9`·`b35af834` → `c0d96517`. Status 'v0.10 -- 독립 검증 승인 가능, 사용자 승인 대기' |
| #3 구조적 전도 문장 동일화 | GC-8 (2) | headroom-chain 341행 문장 형태로 맞추고 `current_basis.py:13-14` 근거를 같은 문장 안에 넣었다 |
| #6 headroom-chain 판 | 머리 19행, N7.2, N2 O-15 행, N3.2 R4 행, GC-8, N8 R7, U-G12, B-G2 | v0.7.5 `43cf75c9` |

### 사용자 결정 O-26·O-27·O-32·O-33 → v0.11(2026-10-19, 브랜치 `plan/graph-consumption-v011`, base master `b2c72a01`)

원문: `wt/_drafts/user_decisions.md` 645(O-26)·646(O-27)·652(O-32)·653(O-33)행. O-33은 오케스트레이터 알림대로 끝 행에서 다시 읽어 대조했다(가정으로 쓴 부분 없음). gain-budget v6.18(브랜치 `plan/gb-v618` `816d9dc1`, 승인 전 -- 처음 `d888d9a9`에서 읽고 후속 커밋에서 이 판으로 갱신)의 card DE-1·LI-1과 그 계획의 '관련 계획 후속 정정' 표(graph-consumption 행)를 읽었다.

| 결정·지시 | 반영 자리 | 처리 |
|---|---|---|
| (1) GC-8에서 `ls_swing` 제외(O-26 (1)) | GC-8 행, N3.2 R4 행, N2 O-15 행, N10.4 B-G2, F-G13 | 배선은 `headroom_bound`·`order_terms`만. GC-8이 DE-1보다 먼저 병합돼도 `ls_swing`은 배선하지 않음. θ 있는 소비자는 R-1′만. `ls_swing._constraints`·VGS 등식 변은 DE-1 소관. F-G13의 `ls_swing.py:46` diode 자리는 DE-1 삭제 범위(39-50행)라 DE-1이 먼저면 부채 항목도 사라진다고 표시 |
| (2) layout 동작점 사본 부채 항목(O-27) | N3.2 새 행, GC-1, N7.3-2, N3.1-5 L-5 개념, BD-8 | `LayoutInput` 동작점(`convergence/layout_input.py:72`)과 card B의 `ly_point`를 card LI-1로 등록. 사본을 '지금도 위반'으로 잡을 규칙이 없어 L-5 등록표에 '동작점 사본' 개념을 더했다(오케스트레이터 기본안). `ly_point`는 base에 없어 card B 병합 뒤 기준선에 넣는다 |
| (3) 출력 함수 판정 기준 + GD-1 독립 검증 | N3.1-2, GD-1, GC-1 | 기준 = 엔진 reader 0 그리고 결과 JSON·보고 경로에만 도달(함수 단위). 검증자가 독립 스크립트로 GD-1 목록을 재측정, 다르면 GC-1 멈춤 |
| (4) 선언 triode(O-33 (9)) | GC-8 (2), F-G38, GC-9 | DC 범위 정의에서는 포화 조건 제외, R-1′ on_mask VDS 하한은 'LUT 정의역'(다른 개념·다른 이름). '선언 triode = LUT on_mask VDS 하한' 문장을 정정 |
| (5) 전류 대칭 결과 필드 소유 | GC-8 (2) | headroom-chain 344행(`b7f457e9`) 문장 형태로: 만드는 card는 HC-1(`iv_headroom`이 처음 읽음), HC-1이 못 하면 GC-8, writer는 만든 card의 블록 하나 |
| (6) cProfile 기준선(WP-10, O-33 (1)) | N7.1 공통 착수 조건, N7.3-9 | 엔진 card마다 그 base에서 검증자가 13회로 cProfile·블록별 계산 수·블록 밖 함수 포함 같은 인자 반복 호출 계수를 잰다. 완료 조건 9는 이 기준선과 비교 |
| O-32 | N2 O-26~O-33 행 | 이 계획에 직접 걸리는 문언이 없어 결정 행에만 기록 |
| (v0.11 검증 `9e3ed4e2` '수정 필요' → 같은 판 후속 커밋) (1) L-5 '동작점 사본' 탐지 정의 [막음] | N3.1-5 | 출처 = graph `device.dc_op` 값(`DeviceOp`)을 데이터 흐름으로 추적(변수 경유·`float()`/`int()` 포함), 대상 = 엔진 값 형식(L-4와 같은 frozen dataclass 집합, 집합 코드는 규칙 L 전용 파일 한 곳) 생성자 인자 또는 graph 필드 쓰기, 정적으로 못 풀면 위반. 알려진 자리: `layout_input.py:72`·`ly_point` = LI-1, `metrics_aux.py:125` = HC-S. 확인 결과 HC-S 행(headroom-chain `952d9761` 509행)은 `sat_v`·`sat_tol_v`만 적고 `op.vgs`(`SatDevice.vgs_v`)는 없다 -- 그 칸의 유일한 소비자 `ls_swing.py:47`은 DE-1이 지운다. 오케스트레이터 확인 항목으로 표시. 새 자리가 나오면 card id 배정 전 GC-1 멈춤 |
| (2) GC-8을 headroom-chain v0.7.6에 맞춤 | GC-8 (2)(4), 머리 19행, N7.2, N8 R7 | `headroom_bound` = 정의 값(VDS ≥ VDSAT) 상한 인증, 비용에 tol 제외, 선언 triode = 비용 0 방향 변(VDS ≥ 0), LUT 정의역 하한 항은 쓰지 않음, `STATUS_UNKNOWN` 예산 처리는 design 넘김(대체값 금지). 'VDS 변 격자 하한 비용' 정의 변화(tol 제외). 인용 판을 `plan/headroom-v076` `952d9761`(336·342-345·509행)로 |
| (3) 용어 통일 | Status, N2, F-G38, GC-8, GC-9 | 'LUT 정의역 하한 항' |
| (재확인 `9ca1e00f`, 같은 판 후속 커밋) L-5 '동작점 사본' 정의를 기계적으로 닫음 [막음] | N3.1-5, N3.2 LI-1 행 | 사본 = 칸 값(또는 `DeviceOp` 객체)을 그대로(같은 값 또는 `float()`·`int()`만) 영속 자리(graph 필드 쓰기, S3 기록, 결과 JSON·보고 객체, 모듈·클래스·인스턴스 속성)에 담기. 계산용 임시 묶음·산술 결과는 사본 아님. 값 형식 집합 기준은 철회. 추적 = 호출 그래프 인자 전파(함수 경계 넘음), L-1과 같은 도달 조건, 못 풀면 위반. 출력 함수 면제(N3.1-2 기준과 같음). 자리 분류(직접 확인): `size_and_seal_local.py:128` = dc_op writer 아님, 엔진 호출자 0이라 도달 밖(GD-1이 진입점에 넣으면 GC-1 멈춤), `dc_metrics.py:113` `GateArea` = 같은 호출 안 `area_search`(`area.py:12-30`)만 읽고 버려지는 계산 입력, `front_query.py:26-31` = 사용자 조회 `node_across_front`의 보고 객체라 출력 함수 면제. 기준선 절차: 분류에 없는 자리는 card id 배정 전 GC-1 멈춤 |
| (재확인 `7899cd6d` '수정 필요', 같은 판 후속 커밋) (1) `SatDevice` 재분류 | N3.1-5, N3.10 DE-1 행, N7.3-2 | `_swing`(`metrics_aux.py:256-262`) → `ls_swing` → `SwingIcmr`(`ls_swing.py:119`)에 `op` 칸이 없어 계산 입력. 부채 항목에서 뺐다(첫 분류 'DE-1 항목' 철회). `vgs_v` 칸 삭제의 상위 개정 항목은 근거를 'DE-1이 지우는 코드에만 쓰이는 칸(L-4)'으로 |
| (2) 추적 범위 | N3.1-5 | 인자·**반환값·객체 칸(필드 단위)** 전파. LI-1 경로 `layout_input.py:61-72` → `place_layout.py:38-39` → `layout/run.py:98` `snapshot.write`가 이것으로 잡힘(코드 재확인 -- 지적의 'place_layout' 경로 그대로) |
| (3) 영속 자리 (iv)·escape | N3.1-5 | (iv) = 호출보다 오래 사는 객체의 속성(모듈 전역, 실행 컨텍스트·캐시 객체). 반환으로 나간 임시 묶음은 받은 쪽에서 계속 추적, 산술로 끊기면 종료 |
| (4) 예시 정정 | N3.1-5 | `SsDevice`는 graph 필드 `ss_dev` 값(영속)이고, 사본 아닌 이유는 칸이 산술 결과(`ss_linearize.py:70-75`) |
| (5) `size_and_seal_local` | N3.1-5, N3.2 새 행, N3.10 v6.19 행, N5 X-G13, N7.3-2, GD-14, B-G4 | '배선 대기' 부채 항목, card id = gain-budget v6.19 층 0 card(이름 확정 뒤 갱신), `snapshot_fragment`의 `dc_op` 참조 전환은 상위 개정 항목, 원래 취지와 다름(배선 대기 기간). 규칙 L에 호출자 0 함수 탐지가 없어 L-1 확장 GD-14, 넣지 않으면 B-G4(부채 판정 (b)와 충돌하므로 그때는 항목 대신 백로그) |
| (6) O-34 반영 | Goal 5, N1.2, FR-G15, NFR-G7, N2 O-34 행, N3.3-5, N3.7, N4-0 신설·N4-1·N4-4, GC-8·GC-9 행, GC-V, N7.3-3·6·7·13, U-G12 | '비트 동일'·'무동작' 완료 조건을 변경 종류 표시로: 결정성(모든 card), 순수 리팩터링 GC-2·GC-3·GC-6(필드별), 동작 변경 GC-5·GC-7·GC-8·GC-9(오라클 toy·봉인·SPICE·변화표), 측정·문서·test card는 엔진 변경 0. GC-7·GC-9를 동작 변경으로 둔 이유 병기. `uncovered` 제외의 별도 예외 승인 문구는 동작 변경 기준으로 대체 |
| (재확인 `f4be659f`, 같은 판 후속 커밋) GC-9·GC-7 변경 종류 | N4-0 표·근거 문장, N4-1, FR-G15, GC-7·GC-9 행, N7.3-7·13 | GC-9를 순수 리팩터링으로 되돌림(원래 취지가 동작 보존 단일화, 합산 순서 차이는 연속 값 분해능이 받음, 동작 변경 표시는 기준 약화라 사용자 승인 필요). GC-7은 부분별: `conduction_mask` 통일 = 동작 변경, 출력 전용 선언·`gs_groups` 읽기·`sctx.cell_floors` 제거 등 = 순수 리팩터링(headroom-chain HC-S와 같은 방식) |
| (마지막 diff 확인 중-2·낮음-3, 같은 판 후속 커밋) | F-G14(207), N3.2 `dc_off_current` 행(309), N5 X-G5(573), N7.2 oracle 항목(658), U-G4 행(749), N4-0 동작 변경 행, 완료 조건 6, gain-budget 인용 전부 | O-46 (2)로 oracle 합격 판정이 `off_current_A` 스칼라를 쓰지 않으므로 `dc_off_current` 소비자는 EO-1~OP-5 사이(옛 ε = 1 판정)만, OP-5 병합 때 출력 전용 선언(X-G6 (가)와 같은 처리, 기본안 -- 삭제는 사용자 승인이라 택하지 않음). 3차 감사 N5 '꺼짐 정의 판'(EO-1 뒤 OP-5 전 옛 식 판정 다리 = 보류(채울 card = OP-5), OP-5 뒤 봉인 9 식으로 재판정)을 gain-budget N6.3 인용으로. gain-budget 인용 `f7b2d5b0` → `6ab294c9`(직접 show), 줄 재측정(N6.3 1230→1232, 봉인 8 행 486→488, 커널 489→491, N6.1 1145→1147, FX-1 1132→1134, LA-1 1137→1139) |
| (3차 정합 감사 N9, 같은 판 후속 커밋) | N2 O-43 행(150), N7.2 LA-1 항목(647), 완료 조건 6(669) | 상자 중심·Halton·사다리·빈 사다리가 남는 출발 경로를 '층 0 무동작 회로'에서 '층 0 무동작 회로 + 층 0 조립 실패 경로(LA-Q2 (b))'로 -- gain-budget v6.19 `f7b2d5b0` LA-1 범위 6·DEC-73 (3)(b), headroom-chain `a2ae9df6`과 같은 문언. 150행은 O-43 결정 인용이라 원문은 두고 괄호로 덧붙임 |
| (gain-budget v6.19 `f7b2d5b0` N6.3 (iv), 같은 판 후속 커밋) | N4-0 동작 변경 행, GC-5·GC-7·GC-8 행, N7.3-6, 인용 전부 | '병합은 막지 않음' 표기를 N6.3 1230행 (iv) 인용으로 바꿈: (가) 보류 다리를 채울 card id(EO-1)가 판정 기록에 있을 때만 병합, 병합해도 미완료 (나) 없으면 병합 금지·사용자 보고. 다리 상태 어휘를 '보류'(채울 card id와 함께)·'대상 없음'((ii) 증거와 함께) 둘로 -- gain-budget 문언에 '채움'이 없어 지난 커밋의 '채움'을 지우고 '채워진 다리는 판정 결과(통과·거부)로 적는다'로. 인용 `81fc49a7` → `f7b2d5b0`, 줄 재측정(N6.3 1228→1230, 봉인 8 행 485→486, 커널 488→489, N6.1 1144→1145, FX-1 1131→1132, LA-1 1136→1137) |
| (2차 전체 정합 검증 `full_audit2_summary.md`, 같은 판 후속 커밋) | N3.10 봉인 8 행, N4-0 동작 변경 행, GC-5·GC-7·GC-8 행, N7.3-6 | (1) 봉인 8 행 인용을 'master 472행, v6.19 `81fc49a7` 485행'으로, 'v6.19에서 진행 중'을 '이미 반영됨(488행 커널 = 봉인 전 항목, 봉인 9 표 포함)'으로. (2) EO-1을 gain-budget 정본 뜻으로 통일: 완료 판정 선행이고 병합은 막지 않음(EO-1 전 병합이면 SPICE 다리 '보류'로 미완료, N6.3 (i)). (3) 다리 상태 표기를 확인: GC-5·GC-7·GC-8에 N6.3 밖 상태어(미측정·생략·면제 등) 0, 표기는 '채움·보류·대상 없음' 셋으로 한정한다고 N4-0에 적음 |
| (gain-budget v6.19 `81fc49a7` O-44 (1) card EO-1, 같은 판 후속 커밋) | N4-0 동작 변경 행, GC-5·GC-7·GC-8 행 선행, N7.3-6, N7.2 순서 항목, N3.2 LI-1 행, N3.10 DE-1 행, GC-8 | SPICE 다리가 있는 동작 변경 card 전수(N4-0 표: GC-5, GC-8, GC-7의 `conduction_mask` 통일 부분)의 선행에 gain-budget card EO-1(N6.20)을 넣었다. 순수 리팩터링 card(GC-2·GC-3·GC-6·GC-9, GC-7 나머지)는 SPICE 다리가 없어 해당 없음. 인용 `d64e11b9` → `81fc49a7`, 줄 번호 재측정(N6.3 1226→1228, N6.1 1142→1144, FX-1 1129→1131, LA-1 1134→1136) |
| (gain-budget v6.19 정본 `d64e11b9` 이름 맞춤, 같은 판 후속 커밋 `0cdc525b`) | N4-0 동작 변경 행, N7.3-6, N7.2 순서 항목, GC-5 선행, N3.2 LI-1 행, N3.10 DE-1 행, GC-8, N3.6-2, N10.4 | N6.3 1226행 '판정 다리 보류·대상 없음' 규칙 (i)~(iii)을 줄 인용, GC-5 SPICE 다리 = 시작점 ngspice 판정((iii)). N6.1 1142행 순서 GC-9 → GC-5 → FX-1·GC-9 → LA-1로 확정, 이 계획 card 내부 의존과 충돌 없음(GC-5 선행에 GC-9 추가). 인용 `503a31fe`(`plan/gb-v618`) → `d64e11b9`(`plan/gb-v619`). 새 백로그 번호를 B-G4 → B-G5(옛 B-G4는 O-36으로 지운 번호 -- 바로 아래 행의 'B-G4(새 번호 재사용)'는 이 커밋으로 B-G5가 됐다) |
| (전체 정합 검증·사용자 결정 O-43, 같은 판 후속 커밋) | N2 O-43 행, N7.2 새 항목 둘, N4-0 동작 변경 행, N7.3-6, N3.6-2, N10.4 B-G4(새 번호 재사용), N3.2 R4 행, N3.10 봉인 8 행, 인용 판 | D2: LA-1 대응 항목, GC-5 빈 사다리·상자 중심 출발은 층 0 무동작 회로 출발 경로에서 유지. B-M4: 순서는 gain-budget N6.1 정본, 동작 변경 card끼리는 같은 출발 기록에서 원인 분리 불가라 따로 병합. A-F4: SPICE 다리 보류·대상 없음은 gain-budget N6.3 규칙 인용. A-F12: 출발 자리값 기하평균은 근거 없음 -- '추정' 표기·백로그 B-G4(옛 B-G4는 O-36으로 지워져 번호 재사용). B-L8: R4 '네 곳'을 'ls_swing은 DE-1이 지워 세 곳'으로. A-F13·B-L5: headroom-chain 인용 `952d9761` → `aa6e064c`(336→338, 342-344→344-346, 345→347), gain-budget `816d9dc1`(v6.18) → v6.19 `503a31fe`(승인 전 표기 유지). B-M5: 봉인 8 삭제 행에 '봉인 집합 표기(1~8, 표에 9 없음)는 gain-budget '커널 = 봉인 전 항목' 개정이 맡고 같은 상위 개정 묶음에서' 명시(`seal.py:41` 봉인 9 확인) |
| (diff 확인 '승인 가능' 뒤 비차단 1건, 같은 판 후속 커밋) GD-14 기준선 | GD-14, N6 M-G9 신설, GC-0a | GD-14 판정은 AST 호출 그래프로(이름 grep 금지). 이름 grep 사전 조사에서 'entry' 339개 중 `size_and_seal_local` 밖 후보 셋(`pin_blas_threads`, `CanonPointer`, `resolve_lut_location`)이 나와, GC-0a에 'L-1 확장 대상 사전 측정(AST)' M-G9를 넣었다. 셋은 지금 분류하지 않고 M-G9 결과로 처리(배선·삭제는 사용자 승인). gain-budget v6.18 '승인 전' 표기는 그대로 |
| (사용자 결정 O-36, 같은 판 후속 커밋) X-G13·GD-14 | Status, N2 O-36 행, N3.1-5, N3.2 `size_and_seal_local` 행, N3.10 v6.19 행, N5 X-G13, N7.3-2, GD-14, N10.4(B-G4 삭제) | X-G13 'O-36 (1) 승인, 기한 = LA-1 병합', card 이름 LA-1로 확정('이름이 정해지면' 문구 정리). GD-14 넣기로 결정 -- B-G4 대체 경로 문구와 B-G4 행을 지우고, 부채 목록 판정 (b)는 L-1 확장으로 성립한다고 정리 |
| (오케스트레이터 답, 같은 판 후속 커밋) `metrics_aux.py:125` card id | N3.1-5, N3.10 새 행, N7.3-2 | 확인 항목 닫음: `op.vgs` 사본(`SatDevice.vgs_v`, `aux_types.py:102`)의 card id = DE-1(유일한 소비자 `ls_swing.py:47`을 DE-1이 지움). `sat_v`·`sat_tol_v`는 사본이 아니고 HC-S가 `device.dc_sat_v` 읽기로 바꿈. gain-budget v6.18 `816d9dc1` DE-1 소비자 표 F-DE7을 확인했더니 이 칸 삭제가 없어(`aux_types.py:139-172, :251-260`만) N3.10 상위 개정 항목으로 기록 |
| (4) 상위 v6.18 참조 | 이 표 머리 | `816d9dc1` |

### 사용자 결정 O-49~O-55 → v0.12(2026-10-20, 브랜치 `plan/graph-consumption-v012`, base master `9401e98f`)

근거: `wt/_drafts/evidence/2026-10-20/full_audit4_summary.md` 16행 'graph-consumption v0.12' 항목, `wt/_drafts/user_decisions.md` O-49~O-55 행. 상위 정본 인용 판: gain-budget v6.20 `7fe555b1`(`plan/gb-v620`, 독립 검증 전), oracle-portability v0.6.10 `7f2a5e12`(`plan/oracle-v0610`, 독립 검증 전), headroom-chain v0.7.7 `f303115c`(`plan/headroom-v077`, 독립 검증 전) -- 첫 커밋은 `0a7868b5`·`84cc5410`을 인용, 둘째 커밋에서 최종 머리로.

| 감사 항목 | 바뀐 자리 | 처리 |
|---|---|---|
| `dc_off_current` 출력 전용 선언 시점(옛 309·573·658행 'OP-5 병합 때') | N3.2 표 `dc_off_current` 행, N5 X-G5, N7.2 oracle 항목, N10.2 U-G4 | 'OP-5 통합 병합의 엔진 커밋'으로 확정. 근거 = oracle v0.6.10 OP-5 행('엔진 쪽 `device.dc_off_current` 필드는 graph-consumption 계획이 출력 전용 선언으로 처리')과 gain-budget v6.20 EO-1 범위 (1)(확장 칸 갱신 = OP-5 통합 병합의 엔진 쪽 EO-1 생산자 갱신 커밋), O-55 U2. 같은 커밋이어야 하는 이유(앞이면 실제 소비자가 있는데 출력 전용, 뒤면 L-1 위반)와 변경 종류(선언 부분 = 순수 리팩터링) 표시 |
| 공용 전도 판정 함수 정본 등록과 `conduction_mask` 관계 | N3.0 F-G14(계획 항목 표시), N10.2 U-G4, N7.3-13 예외 항목, N10.1 BD-8 | 다른 개념·다른 이름으로 정함 -- 근거는 기존 결정 인용(U-G4 (가)의 R3 정의역 구분, O-16 (3) 검증 경로 단일화 예외): 판정 함수 = 소자 동작점 + 선언 영역 → 판정, `conduction_mask` = (kind, w_key) 격자 칸 술어. 서로 부르지 않음, 공통은 전도 정의 문장(DEC-90 (1)·봉인 9 식)뿐이고 격자 술어가 그 문장과 같은지는 GD-12 측정. 새 사용자 결정 없이 정해 멈추지 않음 |
| `off` 선언 소자 사이징·역산 경로 제외(O-55 V5)의 탐색 소비자 영향 | N3.2a 아래 문단 1~5, N3.10 새 행 | `current_box`·`edge_costs`·`conduction_mask`는 kind 단위라 영향 없음(코드 `E/search/current_box.py:20` 재확인), `cell_floor`는 θ 스키마 변수 집합을 그대로 읽고 자체 거르기 금지(L-5). `search_domain` kind 목록 출처는 GC-0a 측정 항목(정하지 않음). 상위 v6.20 문언('LUT·gm/ID 경로')이 O-55 V5 한정을 아직 안 담아 N3.10 상위 개정 항목으로 등록 |
| 새·바뀐 필드 소비(기준 칸, 방향별 슬루 행, 봉인 9 판정 행, 부호 있는 V_id*) | N3.2a 표(신설) | 필드마다 만드는 card·정본 지정 소비자·확인 자리·변경 종류(O-34). 기준 칸은 reader 또는 L-4 출력 전용 등록 중 하나를 IT-2 design이 정함(둘 다 아니면 병합 금지). 봉인 9 판정 행은 새 graph 필드가 아니며, 새 필드로 만들면 reader(OP-5 통합 병합 엔진 커밋)와 같은 커밋에서만. V_id* 크기 사본 칸 금지 |
| Status·N2 | 머리, N2 O-49~O-55 행 | 'v0.12 -- O-49~O-55 후속 정정, 독립 검증 전' |
| (오케스트레이터 마무리 맞춤, 같은 판 둘째 커밋) | 인용 전부, 머리 관련 계획, N3.2a 1·5·표 셋째 행, N3.10 새 행 | 상위 인용을 최종 머리로(첫 커밋의 gain-budget `0a7868b5` → `7fe555b1`, oracle `84cc5410` → `7f2a5e12`, headroom-chain v0.7.6 `aa6e064c` → v0.7.7 `f303115c`, git show로 직접 재확인; gain-budget 계통 offset (c) 1568 → 1571행). gain-budget `7fe555b1` 496·1888행이 off 제외를 '사이징·역산 경로 한정'으로 이미 정정해 N3.10 행 '해소'. `search_domain` kind 목록 = 사이징 경로 소자(선언 없음·triode)의 kind, off 선언 소자만 가진 kind 제외(O-55 V5 귀결, 원칙 기본안) -- GC-0a가 그런 kind 존재를 재고 있으면 EO-1 범위에서 처리('미정' 정리). 판정 행 이름을 gain-budget 1673행대로 '봉인 7·9 판정 행'. 기준 칸 소비 방식은 IT-2 design 몫 유지 |

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
| 0.10 승인 | 2026-10-19 | 사용자 결정 O-21 "모두 승인, 권고대로"(`wt/_drafts/user_decisions.md` 640행)로 v0.10(`9090593a`) 승인. Status만 갱신 |
| 0.11 | 2026-10-19 | 사용자 결정 O-26·O-27·O-32·O-33 후속 정정(H3): GC-8에서 `ls_swing` 제외, layout 동작점 사본 부채 항목(LI-1, L-5 '동작점 사본' 개념), 출력 함수 판정 기준·GD-1 독립 검증, 선언 triode 'LUT 정의역' 구분, 전류 대칭 결과 필드 소유 문언, 착수 조건 cProfile 기준선 |
| 0.12 | 2026-10-20 | 사용자 결정 O-49~O-55 후속 정정(H3 'O-49~O-55 → v0.12'): `dc_off_current` 출력 전용 선언 = OP-5 통합 병합의 엔진 커밋, 공용 전도 판정 함수 정본 등록(`conduction_mask`와 다른 개념), `off` 선언 소자의 탐색 소비자 영향, 새·바뀐 필드 소비 확인 표 N3.2a, 상위 v6.20 문언 정정 항목. 독립 검증 전 |
| 0.12 최종 diff 확인 | 2026-10-20 | 독립 최종 diff 확인(`wt/_drafts/evidence/2026-10-20/final_diff_check_summary.md` F2·F3·F7) 반영: (F2) headroom 기준 판 `f303115c` → `cca153ad`(머리 Status·관련 계획), HC-S `device.dc_sat_v` 소비 자리에 headroom N3.4 331행 `off` 선언 행 규칙 인용(소비자 = 정의 불능); (F3) `search_domain` kind 목록 소유 = gain-budget EO-1 범위, gc는 거르지 않고 GC-0a는 존재 여부만 측정; (F7) 봉인 9 (i) 문언 '거부'(gain-budget `ac188dd4` 496행 인용). 독립 검증 전 |
| 0.12 (병합 뒤 인용 맞춤) | 2026-10-20 | 사용자 O-57 병합 뒤 상대 계획 인용 해시를 병합된 최종 머리로(Status·관련 계획, 208·310·346·347·354·503·670행): gain-budget `7fe555b1`·`ac188dd4` → `f2579b2f`, oracle `7f2a5e12` → `64687b21`, headroom-chain `cca153ad` → `64c115ba`. gain-budget 줄 번호를 `f2579b2f`에서 다시 대조(그 판 N2 O-56 행 추가로 318행 뒤 +1): 496행 → 497행, 1571행 → 1572행, 1888행 → 1889행. headroom 331행은 같은 문장 확인. 내용 변경 없음 |
| 0.13 | 2026-10-20 | 사용자 결정 O-58 S-1·O-59 (1)~(4) 후속 정정(근거 `wt/_drafts/evidence/2026-10-20/o59_plans_revalidation.md` §6 '다른 계획 후속 정정 행'·`o58_plans_validation.md`; 상위 gain-budget v6.21 `plan/gb-v621`, oracle v0.6.11 `plan/oracle-v0611`, 해시는 병합 뒤 맞춤 -- O-60 병합 뒤 gain-budget `54a3a328`·oracle `83530559`): (1) N3.2a에 새 graph 필드 둘 -- 측정 구성 판정 창(writer = IT-2 봉인 뒤 블록, 소비자 = 커널 ICMR 선언 제약·커널 metric), ss 층 봉인점 컨덕턴스 계·인수분해 필드(가칭 `nodal_factor`, writer 하나, READS = 봉인 뒤 블록·`offset_analysis`·`offset_systematic`·`block_residual`, 세 자리 이전 = IT-2) (2) V_id* 행에 DEC-23 이동의 기준점 V_id,0 인용(O-59 (4) DV-13) (3) N3.9에 스냅샷 파생 규칙(O-59 (2)) 인용과 '실제 읽기'의 평가 경로 조건 (4) oracle 확정 기록(`status = final`, O-59 (3) DV-12) -- 이 계획 본문에 오라클 범위 값을 읽는 문언이 없어(grep '오라클'·'oracle'+범위·ICMR·스윙·슬루, 'G-19'·'확정 기록' 0건) 고칠 자리 없음 |
| 0.13 (재확인 G1) | 2026-10-20 | 마지막 재확인(`wt/_drafts/evidence/2026-10-20/o59_final_recheck.md`) G1 반영: N3.9 '스냅샷 파생 규칙과 필드 수명' bullet이 상위 정정 전 writer 집합(`PLAN_WRITERS`)을 풀어 옮긴 사본이라 규칙 본문(남는 필드·eager 제거·봉인 4 단언·graft 집계·reader 경로 확인 문장)을 지우고 gain-budget N3.3 '스냅샷 파생 규칙' 인용 한 구절과 이 계획 몫 문장('실제 읽기'는 그 평가 스냅샷에 남는 필드에만 성립)만 남김. writer 집합은 gb 정본에만 |
| 0.13 (재확인 G1 보완) | 2026-10-20 | G1 반영 때 같이 지워진 이 계획 소유 검사를 사본 없이 다시 넣음: N3.9 '스냅샷 파생 규칙과 필드 수명'에 "소비 확인(N3.2a)에서 reader가 읽는 필드의 writer가 그 평가 스냅샷에 남는 writer 집합(gain-budget N3.3 '스냅샷 파생 규칙' 정의)에 드는지 함께 본다 -- 들지 않으면 봉인 4 거부 대상" (writer 집합은 gb 정의 인용, 풀어 적지 않음) |
| 0.14 | 2026-10-24 | 상위 gain-budget v6.38 사용자 결정 O-126("안 B (권고)", `wt/_drafts/user_decisions.md` O-126 행; 근거 `wt/_drafts/evidence/2026-10-24/u114_la1_prereq.md` §3 P9 -- GC-9는 순수 리팩터링이고 `current_cone` 소비 자리는 LA-1이 남기는 무동작·조립 실패 출발 경로에 있어 LA-1과 파일 겹침만) 후속 정정, 검증 대기: '순서의 정본과 동작 변경 card 병합 원칙' 문단(v0.13 669행)의 `layer0_center.py`·`fd_jacobian.py` 순서를 '선후 고정 없음(같은 통합 병합 금지, 나중 card가 rebase, GC-9 비교는 병합 직전 master)'으로. `start_intervals.py`·`iv_currents.py`의 GC-9 → GC-5 → FX-1 순서는 그대로. 바꾼 옛 문장: «`layer0_center.py`·`fd_jacobian.py`는 **GC-9 → LA-1**(LA-1이 `dc_current_basis` 정본 위에서 층 0 경로를 다시 쓴다).» |
| 0.14 (둘째 커밋) | 2026-10-26 | 상위 gain-budget v6.38 셋째 커밋 DEC-104 R6(상위 사용자 결정 O-128 Q2 -- 근거 `wt/_drafts/evidence/2026-10-26/theta_basis_principle_audit.md` §7 W-5 대체) 후속 정정, 검증 대기: N3.6-3 '모든 후보가 충돌일 때 상자 중심 탐색' 근거 끝에 '상자 중심은 θ 독립 성분에만, 고리 종속 성분은 상위 고리 종속 블록이 파생' 한 문장. 옛 문장 변경 없음(덧붙임만) |
| 0.14.1 | 2026-10-26 | 상위 gain-budget v6.38.1(상위 사용자 결정 O-151 DK1, 근거 `wt/_drafts/evidence/2026-10-26/design_v115_plan_defects.md` §1) 후속 정정, 검증 대기: N3.2a `start.row` 출력 필드 행에 '출발 행·사다리 = θ 독립 성분만, 고리 종속 값 = 상위 R6 블록 출력 필드 하나(소비자 = 커널 평가 입력 조립)'를 더함. 바꾼 옛 문장: (1) start.row 행(DK1): «\| 출력 전용 선언 대기. 출력 함수 = U16 결과 JSON 진단 칸 \| U16 \| U-G6 \|» |
| 0.14.2 | 2026-10-28 | 상위 gain-budget v6.38.2(사용자 결정 O-164 -- 이득 L 하한 fail-closed, DEC-105 (1)) 역참조, 검증 대기: N3.6 '1회차 전류의 0 이하 처리'의 `gain_l_bounds` 항목에 '평가 앵커 0 → 정의 불능 분기와 같은 분기 하나, 먼저 병합되는 card가 만들고 나중 card는 사유만 더함(사본 금지)' 한 문장(상위 검증 1 D-11). 규칙 변경 없음 |
| 0.14.3 | 2026-10-28 | 상위 gain-budget v6.38.2 열째 커밋(상위 사용자 결정 O-165 -- 근본원칙 O-153 확장, 적용 문언 사용자 확인 대기; 근거 `wt/_drafts/evidence/2026-10-28/o165_rewrite_audit.md` R4) 후속 정정, 검증 대기: `gain_l_bounds`의 정의 불능·사유 분기를 상위 card LA-1 범위 15 (a) 하나가 소유(함수 전체 재작성), GC-5 범위를 세 함수·다섯 호출 자리로 줄임(N3.6 '1회차 전류의 0 이하 처리', 완료 조건 6, GC-5 card 행, GD-7). 이 card는 1회차 충돌 표지만 쓰고 그 함수는 표지를 사유로 옮김 -- 병합 순서 규칙 없음. 바꾼 옛 문장: (1) N3.6 «GC-5는 함수마다 다음을 고친다.» (2) `gain_l_bounds` 항목 «원소가 전류 충돌로 빠진 블록은 '이득 목표 미달'(`SRC_GAIN_L`) 충돌과 최대 앵커 L 하한을 만들지 않는다(지금 `iv_gain_l.py:125-127`). 그 블록 경계를 전류 충돌 사유로 비활성 기록한다. … 두 card 가운데 먼저 병합되는 쪽이 분기를 만들고 나중 card는 사유만 더한다(사본 금지).» (3) GC-5 행 «네 함수·여섯 호출 자리 처리(`gain_l_bounds`의 '이득 목표 미달' 오기록,» (4) 완료 조건 6 «**네 함수, 여섯 호출 자리**(`gain_l_bounds` 292행, …) … 여섯 자리마다 보인다(`gain_l_bounds`는 '이득 목표 미달' 충돌·최대 앵커 L 하한이 없어야 한다).» (5) GD-7 «네 함수·여섯 호출 자리의 …), 고칠 자리(`iv_gain_l.py:64-65, :117-119, :125-127`의 원소 없음 → '이득 목표 미달' 경로,». 0.14.2의 '먼저 병합되는 쪽' 문장은 이 행으로 철회 |
| 0.14.3 (둘째 커밋) | 2026-10-28 | 상위 gain-budget v6.38.2 열한째 커밋(상위 독립 검증 10 `wt/_drafts/evidence/2026-10-28/plan_v6382_validation10.md` V10-2·V10-11) 후속 정정, 검증 대기: `gain_l_bounds`의 원소 없음 사유를 그 함수의 자기 판정 '1회차 원소 미정'으로 두고 원인은 이 card 충돌 기록이 있으면 참조로 덧붙임 -- 표지를 '옮긴다'고 적어 GC-5·LA-1 순서에 숨은 의존이 생겼던 것을 없앰(순서 규칙 없음, O-126 (c) 그대로); 표지 소비처 문장을 '다섯 자리 = GC-5, 1자리 = 상위 LA-1'로. 바꾼 옛 문장: (1) «원소가 1회차 입력에 없을 때의 사유는 이 card가 세우는 1회차 충돌 표지를 그 함수가 그대로 옮긴다(분기 하나 -- 이 card는 표지를 쓰고, 그 함수를 고치지 않는다).» (2) «그래서 표지의 소비처는 이 여섯 호출 자리의 비활성 사유와 충돌 기록이다. 표지만 세우고 이 경로에서 읽지 않으면 …» (3) 완료 조건 6 «그 함수가 읽는 1회차 충돌 표지» (4) GD-7 «`gain_l_bounds`가 옮기는 표지 사유도 같은 이름» |
| 0.14.3 (셋째 커밋) | 2026-10-28 | 상위 gain-budget v6.38.2 열두째 커밋(상위 독립 검증 11 `wt/_drafts/evidence/2026-10-28/plan_v6382_validation11.md` V11-1·V11-5) 후속 정정, 검증 대기: `gain_l_bounds`의 '충돌 기록이 있으면 참조 덧붙임' 분기 삭제 -- 그 함수는 이 card 기록을 읽지 않고 원인 추적은 같은 원소 키로만(이 card 기록의 이름·형식(GD-7)에 대한 상위 card 의존 0, 순서 규칙 없음); 머리 version 0.14.3. 바꾼 옛 문장: (1) N3.6 «원인(전류 충돌)은 이 card의 충돌 기록이 가진다 -- 그 기록이 있으면 그 함수가 기록 참조(상위 graph 규칙 4)를 덧붙인다(분기 하나, 이 card와 LA-1의 선후와 무관; …).» (2) «그래서 표지의 소비처는 여섯 호출 자리의 … `gain_l_bounds` 1자리는 상위 LA-1 범위 15 (a)(기록 참조, v0.14.3).» (3) 완료 조건 6 «그 함수가 참조하는 1회차 충돌 기록이 서 있음만 보인다» (4) GD-7 «`gain_l_bounds`가 참조하는 충돌 기록도 같은 이름» (5) 머리 «version: 0.14.2» |
| 0.14.3 (승인) | 2026-10-28 | 상위 gain-budget v6.38.2 승인(상위 사용자 결정 O-166(2026-10-28 "기본안 일괄 승인 (권고)"·O-165 추가 문언 "1번은 권고대로"·U-129 "측정 부하로, topology는 내가 추가 (권고)"·U-128 "형태 승인, 값은 card 착수 전 표로 (권고)", `_drafts/user_decisions.md` O-166 행; 승인 범위 `wt/_drafts/evidence/2026-10-28/plan_v6382_approval_items.md` 기본안)): Status '검증 대기' → '승인됨(O-166)'. 규칙 변경 없음 |
| 0.14.4 | 2026-10-28 | 상위 gain-budget v6.38.3 첫째 커밋(상위 사용자 결정 O-168 -- 입력 공통모드 변수 하나, 상위 DEC-106; 실측 `wt/_drafts/evidence/2026-10-28/o168_input_cm_facts.md`) 후속 정정, 검증 대기: Gs⁺ 행 대체 표지, K-3·O-13 행 표지, N3 '미선언 입력 포트' 표 행·'tie 변 제외의 근거'(근거 대체, 결론 '같은 DC 변 없음' 유지)·8. v1 포트 차 루프·K-a′ 행 표지. |
| 0.14.4 (둘째 커밋) | 2026-10-28 | 상위 gain-budget v6.38.3 둘째 커밋(상위 독립 검증 1 `wt/_drafts/evidence/2026-10-28/plan_v6383_validation1.md` M-1·M-2·L-2·L-4) 후속 정정, 검증 대기: version 필드 0.14.4, 대체 표지의 범위 = 선언된 차동 입력쌍(그 밖 정의 불능 정지), 구현 = 상위 IT-1 v6.38.3 범위 재작성(card IT-3 철회), 병합 때 표지·옛 문언을 history로 옮기는 조건. |
| 0.14.4 (셋째 커밋) | 2026-10-28 | 상위 gain-budget v6.38.3 여섯째 커밋(상위 독립 검증 5 `wt/_drafts/evidence/2026-10-28/plan_v6383_validation5.md` V5-M4·L-5) 후속, 검증 대기: GC-5 범위 칸에 상위 N6.35 E-08(실행 불가 칸 = StartConflict·충돌 소자 기록, 칸 0 대체 금지) 인용. E-19(g = s 한 규칙)는 동작 변경이라 순수 리팩터링 card GC-2가 아니라 상위 IT-1 v6.38.3 범위 재작성 범위 5가 소유(GC-2 범위 변경 없음 -- 넷째 커밋에서 정정). |
| 0.14.4 (넷째 커밋) | 2026-10-28 | 상위 gain-budget v6.38.3 일곱째 커밋(상위 독립 검증 6 `wt/_drafts/evidence/2026-10-28/plan_v6383_validation6.md` V6-M1·상위 결정 재검토 `wt/_drafts/evidence/2026-10-28/decision_rereview.md` #2) 후속 정정, 검증 대기: (1) g = s 규칙 -- GC-2 범위 6·FR-G16·F-G20·K-h·BD-11·GD-10·완료 조건 3·B-G3를 '상위 IT-1 v6.38.3 범위 재작성 범위 5(N6.35 E-19) 결과 그대로 옮김'으로 대체 표지(분류 = S1, 신호 경로 정지 = S1v), B-G3 닫힘 -- **원래 취지와 다름**(옛 '이 계획은 base 동작 보존만, 일반화는 백로그 B-G3'; 셋째 커밋의 'GC-2 범위 변경 없음'은 상·하위 두 규칙을 남겨 검증 6 V6-M1이 지적) (2) 빈 사다리 -- N3.6-3·X-G11 근거·GC-5 범위·완료 조건 6·U-G13의 '상자 중심에서 출발/계속'을 '그 S0 출발 불능 기록(StartConflict·사유, 판정 아님)'으로 대체 표지(상위 N6.35 E-32) -- **원래 취지와 다름**(O-13 (가) 좁힘). library 실측 g = s 소자 0(검증 6) -- 동작 변화 예상 0. |
| 0.14.4 (다섯째 커밋) | 2026-10-28 | 상위 gain-budget v6.38.3 여덟째 커밋(상위 독립 검증 7 `wt/_drafts/evidence/2026-10-28/plan_v6383_validation7.md` L-1) 후속 정정, 검증 대기: X-G11 행·N7.2 LA-1 행의 옛 '빈 사다리 → 상자 중심 출발' 문언에 상위 N6.35 E-32(출발 불능) 대체 표지 -- **원래 취지와 다름**(넷째 커밋과 같은 결정). |
| 0.14.4 (여섯째 커밋) | 2026-10-28 | 상위 gain-budget v6.38.3 아홉째 커밋(상위 독립 검증 8 `wt/_drafts/evidence/2026-10-28/plan_v6383_validation8.md` V8-M2·L-2) 후속 정정, 검증 대기: (ii) 점 `use_macro` 해제를 PM 미달·미수렴 원인으로 좁힘 -- \|H\| = 1 근 없음(`target_not_reached_at_upper_limit`)이면 출발점 그대로를 실행 가능으로 바꾸지 않고 그 후보 매크로 출발 불능(상위 N6.35 E-31), 모든 후보 출발 불능이면 S0 출발 불능(E-32) 기록 writer = GC-5; X-G11·완료 6·U-G13·GC-5 행 대체 표지, N3.6-3 '상자 중심의 범위' 옛 문언 표지와 근거(B80·B81 → 상위 N6.35 머리 원칙·EP-7) 정정 -- **원래 취지와 다름**(O-13 (가-1) `use_macro` 해제 범위 좁힘). library 실측 근 없음 0회로 -- 발동 0, nmcnr(PM 미달) 해제 경로 그대로. |
| 0.14.4 (일곱째 커밋) | 2026-10-28 | 상위 gain-budget v6.38.3 열째 커밋(상위 독립 검증 9 `wt/_drafts/evidence/2026-10-28/plan_v6383_validation9.md` V9-M1·V9-M2·L-4) 후속 정정, 검증 대기: GC-5 `use_macro` 해제 + '면적만으로 (i) 재적용' 경로 삭제 -- 상위 세 층 규칙(근 없음 → 후보 매크로 출발 불능, 목표 미달 → 정의된 값 출발 + 후보별 기록)이 같은 상황을 덮으므로 둘째 경로(O-165 (a) 비교: 삭제 = 실행 가능 정의 하나·분기 0 / 고침 = 해제 전·후 두 정의 -- 삭제 기본안); 후보 실행 가능 = 면적 ∧ 매크로 출발 불능 아님, 매크로 출발 불능 기록 writer = 상위 LA-1 (g)(이 card는 읽음), S0 출발 불능 writer = GC-5; (ii) 점 정의·X-G11·완료 조건 6(혼합 원인 픽스처)·U-G13·F-G32 대체 표지 -- **원래 취지와 다름**(O-13 (가-1) 해제 정의 삭제). 실측(상위 `wt/_drafts/evidence/2026-10-28/v9chk/`): 후보 단위 최상 칸 근 없음 3회로·PM 미달 후보 4회로, 해제가 일어나는 회로 nmcnr 1(근 없음 후보 없음) -- 선택 변화 0 예상(추론). |
| 0.14.4 (여덟째 커밋) | 2026-10-28 | 상위 gain-budget v6.38.3 열한째 커밋(상위 사용자 대원칙 O-169, 상위 독립 검증 10 `wt/_drafts/evidence/2026-10-28/plan_v6383_validation10.md` V10-M1·O169-1·L-6) 후속 정정, 검증 대기: N3.6-3 칸 0 선택을 모든 경우 한 규칙으로 재작성 -- 후보 = 격자 t_k(최상 탐침 포함)와 아래 끝 탐침, 분류 = 전류 충돌 / 매크로 출발 불능(근 없음) / 면적으로만 실행 불가 / 실행 가능(목표 미달 포함, 후보별 기록), (i) 실행 가능 최대 격자 점 + 구간 이분 (ii) 면적으로만 실행 불가 최소 t (iii) S0 출발 불능(상위 E-32) -- 근 없는 점을 칸 0으로 뽑는 경로 없음; 옛 '(가-1)은 아래 끝 충돌일 때만'과 '지금 흐름 그대로'(이분 탐색 + 아래 끝 대체) 두 경로 삭제(비교: 한 규칙 = 경로·후보 정의 하나 / 두 경로 유지 ⚠ O-169 근거 '지금 흐름·동작 보존'뿐 / 격자만 ⚠ 칸 0 거칠어짐); (ii)·매크로 충돌 구절·(iii)·'면적만 실행 불가인 아래 끝'·X-G11·완료 6 머리(해제 픽스처 → 한 규칙·혼합 원인 픽스처)·U-G13·GD-7·NFR-G4 대체 표지 -- **원래 취지와 다름**(사용자 결정 O-13 (4)). 정정: 여섯째 행의 '근 없음 0회로 -- 발동 0'은 최종 선택점 기준 수치이고 후보 단위로는 최상 칸 근 없음 3회로·PM 미달 후보 4회로다(일곱째 행; 이력 행 append 관례에 따라 여섯째 행에 덧붙였던 정정 구절은 이 행으로 옮김 -- 검증 10 L-6). library 실측(상위 `wt/_drafts/evidence/2026-10-28/v10chk/`): 칸 0이 근 없음인 회로 0 -- 한 규칙 (iii) 발동 0, 칸 0 값 변화 0 예상(추론). |
