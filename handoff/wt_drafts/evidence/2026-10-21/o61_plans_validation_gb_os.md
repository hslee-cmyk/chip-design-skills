# O-61 계획 개정 독립 검증 -- gain-budget v6.22 · offset-strategy v0.7.1

- 검증자: 독립 plan validator(작성자 아님, 작성자 보고는 증거로 쓰지 않음). 2026-10-21. 모든 worktree는 읽기 전용(`git -C` diff/show/grep만, reset·checkout·stash·commit 없음).
- 대상
  - gb: `wt/gb-v622`, `plan/gb-v622`, **head `1027c6d8`**(1차 `ce46a2cd` P1~P6 + 2차 `1027c6d8` P7 DEC-23), base master `512b3c48`. 아래 줄 번호 = `1027c6d8`의 `gain-budget-gmid-sizing.plan.md`.
  - os: `wt/os-v071`, `plan/offset-strategy-v071` `703bb7ef`, base `512b3c48`. 줄 번호 = `703bb7ef`의 `offset-strategy.plan.md`.
- 기준: `_drafts/user_decisions.md` O-61(O-58·O-59), 분석 `evidence/2026-10-20/v622_batch_analysis.md`, design marker `wt/design-it12-window` `4b7f4d5a`(40:2091, 41:696·720·736·737·745·762·793, 42:229), offset design `wt/design-os-ss1` `50d33b8e`, 프로젝트 CLAUDE.md '★graph 단일 정본'.
- 주의: 계획의 한 줄은 문단 하나다. 줄 번호 뒤 따옴표 구절로 자리를 적었다.

## 요약

| 구분 | 내용 |
|---|---|
| blocker | **없음** |
| must-fix | M1 P3와 바뀌지 않은 문장 셋 충돌(1479·1487 (1)·1574). M2 P7(DEC-23 갈래)을 구현하는 card 범위·완료 조건이 없음(DE-1 1576·1590). M3 P5 대상 창 모호(커널 metric은 1479에서 `node.dc_window_cfg`를 읽음). M4 gb N6.1 OS-* 행(1157)에 새 선행 U17 ②·Q8이 없음(os 430이 gb N6.1을 유일한 순서 정본으로 둠) |
| nice-to-fix | N1 고립 포트의 창 문구. N2 계획 안 '옛 문언 ~ 대체' 경위 구절. N3 os 256·306·570·650 `S3Index` 선후 표기. N4 os design 개정 목록에 OSD 129 keep 표기 추가. N5 gb 1160 os 줄 번호 인용(병합 뒤 맞춤). N6 프로젝트 CLAUDE.md 규칙 5 문구(오케스트레이터 몫, 승인 뒤). N7 V_id* = −ΔV_out/A_dc 분모 갈래(사용자에게 올림) |
| 판정 | **수정 후 병합**(M1~M3은 gb 문장 단위 수정. M4는 같은 배치에 넣거나 병합 직후 맞춤 커밋에 넣어도 됨) |

## A. O-61 항목 반영 범위

| 항목 | 판정 | 근거 |
|---|---|---|
| P1 keep = base writer ∪ 호출 블록, parent 검사 확장, 봉인 4 서로소 단언, `_CONTEXT_WRITERS` 이동 없음 | PASS | 422(N3.3 '스냅샷 파생 규칙'), 495(N3.6 표 4행), 1481(N6.6 범위 4, 착수 실측에 'parent 없는 평가 스냅샷 writer 목록·θ 무관'), 1487 (11)(a)(b). '`_CONTEXT_WRITERS`는 `context_fp` 전용, 자리를 옮기지 않음'은 422·1481에 있다. CLAUDE.md 규칙 5 맞춤은 history v6.22 행 끝에 '오케스트레이터 몫'으로 적혀 있다(N6) |
| P2 완료 조건 (2) = `saturation_window` 하나 + 호출 셋 | PASS | 1487 (2) '함수는 `saturation_window` 하나(끝 풀이는 `_refine_ends` 하나)이고 그 함수를 부르는 자리는 셋 -- `dc_columns`·봉인 뒤 측정 구성 블록·다듬은 창 블록'. 식 재구현 = 둘째 생산자라고 명시 |
| P3 KVL 정본 = `node.dc_window_cfg` 하나, `kvl` 칸 삭제, 다듬은 창은 그 포트를 쓰지 않음 | PASS(반영) / M1(정합) | 567 'KVL 고정 포트의 정본 칸', 1478 끝, 1487 (5)·(12)(c). **'원래 취지와 다름, 승인 O-61 P3'** 표시: 318·567에 있음 |
| P4 (a) 고립 포트 규칙 명시 | PASS | 1391(IT-1 범위 4) '규칙 문언 명시, 범위 확장 아님', 발동은 card 0 M-I1 |
| P4 (b) F 성분 미선언 포트 = (가) 정의 불능 + 사유, (나) 일반형 채택 안 함 | PASS | 1478 'F 성분에 속한 입력 DC 미선언 포트 ... 정의 불능 ... 일반형은 공동분석 대상이라 채택하지 않는다', red 1487 (12)(b) |
| P5 커널 미수렴 → 정의 불능, 동작 변경, red, card 0 발동률 | PASS(반영) / M3(모호) | 1478 '커널 창 되풀이 미수렴 ... **동작 변경**(N4 0번·N6.3), 승인 O-61 P5', 완료 조건 1487 (6) '동작 변경 ... card 0(IT-0)이 library 9회로에서 그 발동률 ... 이 기록이 있어야 완료', red (12)(a). 동작 변경 등록과 완료 조건이 모두 있다 |
| P6 출발 창 = DE-1 전 `node.dc_window_cfg` | PASS | 1478 '입력(출발 창) = ... DE-1 전에는 `node.dc_window_cfg`(+tol), DE-1 뒤에는 `node.dc_window_def`', READS 단언 1487 (12)(d) |
| P7(DEC-23 갈래, 2차 커밋) | PASS(내용) / M2(배선) | 223 '**A_dc 정의 불능 갈래** ... \|A_dc\| ≤ 판정 분해능(A_dc = 0 포함) → 정의 불능·사유, 판정 분해능 = N3.8 정의 자리 인용, 새 상수 없음, 동작 변경 -- 차동 "값 불변" 예외는 발동 회로뿐'. O-61은 P7을 oracle v0.6.12 몫으로 적었다. 그러나 O-58 DV-11은 'gain-budget DEC-23 먼저, oracle N3.9 인용'으로 정했다. 그래서 정의를 정본 자리에 두는 것은 O-61을 넘는 결정이 아니고 배치를 맞춘 것이다. 오케스트레이터는 사용자 보고에 '배치 = DEC-23'을 한 줄로 적을 것 |
| O-61 밖 결정 | PASS | O-61을 넘는 새 결정은 찾지 못했다. 덧붙은 세부(P3 '구조 분류로 읽을 칸 결정', P4 (a) 'card 0 M-I1 발동')는 분석 권고 문안 그대로다. P10은 '따로 올림, 반영 없음'(318) |
| os P9 (1) OS-2 착수 조건 = U17 ② + Q8 | PASS | 439-445 'OS-2 착수 조건' 문단. 과도기 `EvalResult` 칸·JSON 재계산 금지, (나) 전환은 그때 사용자 결정. N7.2 OS-2 행 선행 칸 469 |
| os P9 (2) design v0.7 개정(kernel 행 현행화) | PASS | 446-451 '고칠 것 넷'. 계획 결정을 새로 만들지 않고 v0.7 N3.3을 인용한다 |
| os P9 (3) 469행 표기 정정 | PASS | 483 '`sctx.cache`(XRUN-F1 card B·U17 ② 뒤에는 S3 메모리 색인의 평가 키 부분 -- F-5)'. F-5(151) 선후 문언과 같다 |

## B. design marker 대응

| marker | 계획 답 | 판정 |
|---|---|---|
| 40:2091·41:736·41:737·42:229 keep 집합, `CONTEXT_WRITERS` 이동 | 422·1481: keep = `ctx.base` `block_versions`의 writer ∪ 호출 블록, 이동 없음 | PASS. design 41:737('sizing으로 이동')은 지워야 한다는 뜻이 분명하다 |
| 41:696 F 성분 미선언 포트·고립 포트의 창 | 1478 정의 불능(F 성분), 1391 고립 포트 = W4 뿌리 | PARTIAL → N1. F 성분 쪽은 분명하다. 고립 포트 쪽은 '뿌리로 센다'만 있고 '그 포트 창 = 뿌리 창 절차'는 추론에 맡겨져 있다 |
| 41:720 KVL 칸 셋 | 567·1478: `node.dc_window_cfg` 한 칸, `kvl` 칸 없음, 다듬은 창 블록 미기록 | PASS(답 자체는 분명함). 다만 M1이 남아 있으면 design 작성자가 1479·1574와 충돌하는 문장을 함께 읽게 된다 |
| 41:745 출발 창 | 1478 P6 | PASS |
| 41:762 커널 `unsettled` → 정의 불능 사상 | 1478 P5('사유 이름은 design') | PARTIAL → M3 |
| 41:793 완료 조건 (2)와 writer 둘 | 1487 (2) | PASS |

## C. graph 단일 정본(별도 검사)

diff와 주변 문장을 직접 훑었다. 새 cache·memo·dict, `sctx.*` 슬롯, `EvalResult` 값 칸, 값 사본, 둘째 생산자, 같은 정의의 두 필드를 찾았다.

| 점검 | 판정 | 근거 |
|---|---|---|
| keep 집합 = `ctx.base.block_versions` 읽기인가 | PASS | master `E/core/graph_snapshot.py:39,46,58-60,149-151`: `block_versions`는 스냅샷의 기존 불변 매핑(writer → 마지막 쓰기 입력 버전)이다. `block_version(w)`는 읽기다. 계획은 '사본 목록 금지'를 명시한다(422·495·1481). 새로 저장되는 목록은 없다 |
| parent 검사 확장 | PASS | 같은 검사(`kernel_run.py:73`)의 일반형이다. 새 상태는 없다 |
| P3 | PASS(개선) | `graph.icm_config.kvl` 사본을 없애고 규칙 3을 명시한다(567). 읽을 칸은 기존 구조 분류로 정한다. 새 규칙·상수는 없다 |
| P2 | PASS | 식 재구현 = 둘째 생산자라고 적고 `git grep` 완료 조건을 둔다 |
| P5 | PASS | 상태는 기존 창 필드의 상태로 나르고(design `input_status`) 새 칸은 없다. 사유는 metric missing 기록이다 |
| P7 | PASS | 정의 자리 하나(DEC-23). 판정 분해능은 N3.8 정의 자리를 인용한다. 새 상수는 없다 |
| os 439-445 | PASS(개선) | 과도기 `EvalResult` 칸과 JSON 재계산(둘째 생산자)을 명시적으로 금지한다 |
| 코드 인용(master `512b3c48`) | PASS | `E/sizing/kernel_run.py:73` = `PLAN_WRITERS`만 비교하는 parent 검사(맞음). `:71` `snapshot = base`(history 인용, 맞음). `E/sizing/block_columns.py:719-723` = tol 미정 `SealViolationError` 분기, 창 한 번 적용(맞음). `:724-733` = `k_max` 루프, 소진 시 수렴 표지 없음(맞음. 734 `_refine_ends` 뒤에도 표지 없음). `E/search/search_context.py:44` `_CONTEXT_WRITERS`, 주석 :43 'context_fp'(맞음). `:171` `widen(S0_WRITERS)`(history 인용, 맞음). 40 design `:549` '제약 행 = `graph/metrics: constraint_rows`, U17 ② 이월', `:681` Q8 '정하기 전에는 `constraint_rows`를 쓰지 않는다'(os 인용 맞음). OSD `50d33b8e` v0.2.6·`plan_version: 0.6.2`·115 `v = k·σ + \|V_sys\|`(맞음) |

## D. 내부 정합·교차 계획

**M1 (P3와 바뀌지 않은 문장의 충돌, must-fix)**: P3 뒤에는 KVL 고정 포트의 front·보고 값이 `node.dc_window_cfg`(DE-1 뒤 `node.dc_window_def`)에서 나온다. 그런데 아래 세 문장은 한정 없이 '다듬은 창'을 읽는다고 적고 있다.
- 1479 N6.6 범위 2 '읽기': "front 판정·보고는 다듬은 창 필드를 읽는다"
- 1487 완료 조건 (1): "front·보고 `icm_margin_v`는 다듬은 창 필드에서 나온 값과 같음". 같은 줄 (12)(c)는 KVL toy에서 `node.dc_window_cfg`와 같다고 적는다. test 작성자가 두 단언을 동시에 쓰면 충돌한다.
- 1574 DE-1 (iii): "`node.dc_window_def_refined` ... front 판정·보고가 읽는다". DE-1 뒤 KVL 포트의 값은 P3에 따라 `node.dc_window_def`다.

수정안: 세 자리에 "(KVL 고정 포트는 N3.8 'KVL 고정 포트의 정본 칸' -- DE-1 전 `node.dc_window_cfg`, 뒤 `node.dc_window_def`)"를 붙인다. 580 metric 표 행의 '끝 풀이(Newton)로 다듬은 정의 창'에도 같은 한정을 붙이면 좋다(nice).

**M3 (P5 대상 창 모호, must-fix)**: 1478 P5는 커널 되풀이 창(`node.dc_window`)이 미수렴이면 "그 창을 읽는 metric(`icm_margin_v`·`required_input_cm_v`·`icmr_v`)과 커널 ICMR 선언 제약"이 정의 불능이라고 적는다. 그런데 1479는 커널 metric·제약이 측정 구성 판정 창 `node.dc_window_cfg`를 읽는다고 적는다(O-58 S-1). 문자 그대로 읽으면 `node.dc_window`를 직접 읽는 metric은 없다(소비자는 탐색 `fd_jacobian`뿐이다). 그러면 P5가 발동할 대상이 없다. design 41:762는 커널 `input_status`를 metric missing으로 사상한다. 수정안: "그 평가점의 측정 구성 판정 창(`node.dc_window_cfg`)도 미수렴 상태를 이어받고, 그 창을 읽는 커널 metric·ICMR 제약은 정의 불능"처럼 상태가 전파되는 필드를 한 구절로 적는다. 상태를 나르는 칸 이름은 design이 정한다.

**M2 (P7 배선, must-fix -- '만들면 배선')**: DEC-23(223)에 갈래가 생겼다. 그러나 σ 입력 환산을 구현하는 card DE-1의 범위 (c)(1576 'σ 입력 환산도 이 card')와 완료 조건(1590 '차동 입력 toy에서 `offset_in_sigma_mv` 비트 동일')에는 이 갈래가 없다. 그대로 두면 정의만 있고 구현 card가 없다. 또 1590의 '차동 비트 동일'은 P7 예외(발동 회로)와 문언이 충돌한다. 수정안: 1576 범위 (c)에 "\|A_dc\| ≤ 판정 분해능 → 정의 불능(DEC-23 갈래)"을 넣는다. 1590에는 red "\|A_dc\| ≤ 분해능 toy(차동·단일 각 하나) → `unavailable`·사유(base는 값을 냄)"와 "비트 동일은 갈래 미발동 회로에서"를 더한다. DEC-23 엔진 소비자 `offset_analysis.py:76` `gain_zero`(A = 0 특수형)를 이 갈래로 대체한다는 문장도 같이 넣는다(옛 검사 삭제).

**M4 (gb N6.1 OS-* 행, must-fix·병합 비차단)**: os 430은 "엔진 card 순서의 유일한 정본은 gain-budget N6.1"이라고 적는다. gb 1157 OS-* 행은 '선후 정본은 그 계획(v0.7 `5f99a49a`)'이라며 위임하면서도, '이 계획과의 선후는:'에서 gb 쪽 선행(EO-1·OP-3·OP-5)을 열거한다. v0.7.1이 더한 U17 ②는 **gb card**이므로 이 열거에 빠지면 순서 정본이 불완전하다. 반면 gb 행이 os 계획에 위임하므로 os v0.7.1 자체의 정합성은 깨지지 않는다. 그래서 **blocker는 아니다**. 수정안: gb 1157 행에 "U17 ②(`constraint_rows` 필드·writer) + 40 §2.4.12 Q8 결정(사용자) -- os v0.7.1 O-61 P9"를 더하고, 인용판을 v0.7.1로 바꾼다. 두 계획을 같이 병합하므로 gb v6.22에 한 구절로 넣는 것이 가장 싸다. 병합 직후 해시 맞춤 커밋(O-60 I1 꼴)에 넣어도 된다. 덧붙여, os 430 '그 전까지 이 절의 선후는 이 계획 card 사이의 선후'와 새 N7.1 문단의 다른 계획 card(U17 ②) 선행이 문언상 어긋난다. gb 행이 들어오면 함께 해소된다.

**옛 문언 잔존 검색**(head 전체, Python 검색): `_CONTEXT_WRITERS`는 남은 곳(318·422·1481·1487)이 모두 '옛 문언 대체' 또는 '`context_fp` 전용' 문맥이다. 규칙 문언으로는 남지 않았다. '두 필드가 공유'·'입력 = 정의 창'·'`block_columns` 하나'는 대체 표기 안에만 있다. `kvl` 칸은 '두지 않는다' 문맥에만 있다. `icm_config` 명칭은 0건이다(design 이름이라 맞다).

**인용 해시·줄**: gb 1160 'os v0.7(`5f99a49a`) 430-434행'은 해시를 고정한 인용이라 지금은 맞다. 다만 v0.7.1에서는 Status가 1줄에서 3줄로 늘어 'OS-2와 LA-1의 선후'가 432-436행이 된다(N5, 병합 뒤 맞춤). os Status의 '상위 정본 현행판 = gb v6.21 `61ee9eab`'는 master 기준으로 맞다. gb v6.22가 병합되면 맞춤 대상이다.

**V_id* 질문(오케스트레이터 문의) -- 사용자에게 올릴 가치가 있다(N7, 비차단)**: DEC-23(223)·N3.8(266·273·582)·DE-1(1576·1591)의 V_id* = −ΔV_out / A_dc는 σ와 **같은 A_dc**로 나눈다. 물리적으로도 같은 문제다. \|A_dc\| ≤ 분해능이고 ΔW ≠ 0이면 V_id*는 수치적으로 정해지지 않은 큰 값이 된다. 그 값은 \|V_id*\| ≤ spec 위반으로 front에서 빠진다. 결과는 fail-closed에 가깝지만, 보고 값은 무의미하고 제외 원인은 'offset 위반'으로 잘못 귀속된다. 같은 A_dc에 대해 반전 입력 식별(O-53 A-1, 567)과 σ(P7)는 '분해능 이하 = 정의 불능'이고 V_id*만 갈래가 없다. 이는 P-1(가장 일반적인 물리 규칙) 기준으로 정합 결함이다. O-61은 σ만 승인했으므로 이 계획에 넣으면 승인 범위를 넘는다. 따라서 **이번 개정에는 넣지 않는 것이 맞다**. 다만 다음 결정 묶음에 "A_dc로 나누는 모든 양(σ 입력 환산·V_id*) = 같은 갈래; ΔW = 0 → 0(통과) 규칙은 유지"를 원칙 기본안으로 올릴 것을 권고한다. 근거 자리는 DEC-23 223 'V_id* = −ΔV_out / A_dc'와 새 'A_dc 정의 불능 갈래'다.

## E. history

| 점검 | 판정 | 근거 |
|---|---|---|
| gb 옛 문장 이전 | PASS | history v6.22 H1 행이 P1~P6의 옛 문장(N3.3·봉인 4·N3.6 4행·범위 4·(11)(a)(b)·(2)·N3.8 '두 필드 공유'·'입력 = 정의 창')을 원문으로 싣는다. 둘째 커밋 행은 옛 DEC-23 두 문장을 싣는다 |
| gb 버전 행 | PASS | Version History '6.22' 행이 있다. 둘째 커밋은 H1 행만 더했다. 버전 표 6.22 행에 P7을 한 단어 더하면 좋다(nice) |
| os 이전·버전 행 | PASS | '2026-10-21 O-61 P9 → v0.7.1' 절에 v0.7 Status 원문(머리 부분, 뒤는 '규칙 근거 문단과 같음'), 바뀐 문장 표, 버전 행 0.7.1이 있다 |
| 계획 안 경위 서술 | PARTIAL → N2 | gb 422·567·1478·1487에 '옛 문언 '…'을 대체' 같은 정정 구절이 있다. 기존 계획의 관례(DEC-23 'DV-11 -- 옛 문언 '차동 이득으로'를 대체')와 같고 짧다. 그러나 '계획은 규칙만, 이력은 history' 원칙으로는 history로 옮길 대상이다. 예: 422 '그 집합에는 … child가 그 필드를 잃는다'(결함 경위). os Status(11)의 '바뀐 것 셋'은 Status 요약으로 허용 범위다 |

## F. os 작성자의 근처 위반 후보 세 건

| 후보 | 판정 | 근거·처리 |
|---|---|---|
| 481(옛 468) W-1 진단 모드 '결과에 그 표지를 싣는다' | backlog(v0.7.1 범위 밖) | 진단 표지는 계산값이 아니라 실행 설정이다. 그런데 단계 B 보고서가 이미 `diagnostic` 칸(`stage_b.py:129`)을 갖는다. 결과 객체에 다시 실으면 같은 뜻의 두 번째 칸(규칙 3·4)이 될 수 있다. OS-2 design에서 '단계 B 보고서 참조로 노출'로 정하도록 backlog에 올린다. S-9 승인 문언이라 v0.7.1(P9 표기 정정만)이 고칠 몫이 아니다 |
| 483-484 노출 목록의 `sctx.cache` | backlog | 새 cache를 만드는 문장이 아니라 기존 평가 캐시(`search_context.py:58` `self.cache = {}`)를 읽기 전용 참조로 노출하는 목록이다. 다만 노출 대상은 F-5 선후대로 S3 색인 평가 키 부분이 되어야 한다. 노출 목록 전수는 design이 하네스를 읽어 만든다고 적혀 있다(482). design 개정 때 '`sctx.*` 슬롯을 새 소비자로 고정하지 않음'을 점검 항목으로 둔다 |
| 306·570(그리고 256·650) `S3Index` 선후 표기 | nice-to-fix / backlog(N3) | `S3Index`는 master에 실재한다(`search/s3_index.py`, `_module_map.py:872`). 이 자리들은 'card B 뒤'만 적고 F-5의 'card B·U17 ② 뒤'와 다르다. 570은 결정된 DS-1(S-14) 기록이라 고치면 결정 문언을 바꾸게 된다. 다음 os 개정의 표기 일괄 정정으로 미룬다. 규칙 위반은 아니다 |

## G. 삭제 줄 대조

- gb: 삭제·대체된 구절(422 'S0 입력 writer(…)', 495 `_CONTEXT_WRITERS`, 567 '이때 … 두 필드가 공유한다', 1478 '입력 = 정의 창', 1481 '`PLAN_WRITERS` 정의 위치', 1487 (2)·(11)(a)(b), 223 갈래 삽입)은 모두 history v6.22 두 행의 옛 문장 원문과 짝이 맞는다. 의도하지 않은 소실은 찾지 못했다. PASS.
- os: 삭제는 Status 한 줄(11)뿐이다. 내용은 새 '규칙 근거(v0.7, 바뀌지 않음)' 문단과 history 원문 머리로 보존됐다. 469·483 구절 대체는 history 표에 원문이 있다. PASS.

## nice-to-fix 상세

- N1: 1391에 "그 포트의 창은 뿌리 창 절차(`saturation_window` + 끝 풀이) 그대로"를 한 구절 더한다(41:696 marker의 고립 포트 몫).
- N2: 계획 안 '옛 문언 대체' 경위 구절을 history로 옮긴다. 기존 관례와 같으므로 일괄 정리 backlog로 둬도 된다.
- N3: os 256·306·570·650의 'card B 뒤'를 'card B·U17 ② 뒤'로 정정한다(F-5 기준, 다음 개정).
- N4: os 446-451 design 개정 목록에 "5. OSD 129 스냅샷 파생 keep 표기 = gb v6.22 base writer ∪ 호출 블록"을 더한다(분석 P1 '반영 대상').
- N5: gb 1160 os 줄 번호와 해시를 v0.7.1로 맞춘다(병합 뒤 맞춤).
- N6: 프로젝트 CLAUDE.md 규칙 5('`_CONTEXT_WRITERS` ∪ 부르는 블록')는 P1 승인 뒤 문구를 맞춘다(O-61 P1 원문, 오케스트레이터 몫). 그 전까지 브리핑과 규칙 문구가 서로 다르다는 점을 작성 agent 브리핑에 적는다.
- N7: V_id* 분모 갈래를 사용자 결정으로 올린다(D절).
