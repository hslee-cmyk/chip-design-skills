---
id: 20261021-it2b-kernel-window
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
approval: 20261021-it2-o67-scope
---
> **재동결 (design 41 v1.12.10, 계획 v6.33, base 2a4ab829)** -- 2026-10-22, 사용자 결정 O-98·O-100·O-101·O-103·O-104. 정본 = design 41 v1.12.10 4.7-1a·4.7-2·4.7-3·4.7-3a·4.7-4·4.7-7 D·L12 (a)(e)·4.7-8 (8)·4.7-9, 계획 v6.33 N6.6 범위 1(1514행)·완료 조건 (9)·(12)(1524행). v1.12.8 → v1.12.10은 줄 추가 없음(`git diff -U0 0c048327 2a4ab829` hunk 실측 -- `41:n` 그대로). 엔진은 `0c048327` 이후 바뀌지 않음(같은 diff, `gmid_engine` 0파일) -- 아래 '작성 전 실측' 줄 그대로. 바뀐 것: S4 갈래 기록(**(S4-나) 확정**), 동작점 불일치 묶음 제거(EO-1로), `Window` 칸 다섯, helper 이동 IT-2d로, `_refine_ends`·`_root_windows` 삭제 IT-2b로, 분류표 대조 12 + 정지 3, 무동작 칸 → 동작 변경 (8), L12 (a)(e) test 기대, test 메모·code 메모.
>
> (옛 표시) **재동결 (design 41 v1.12.8, 계획 v6.31, base 0c048327)** -- 2026-10-22. 머리 블록은 `parse_spec_card`가 모르는 키를 거부하므로(`tools/gates/role_paths.py:695`) 표시를 이 줄에 둔다. 줄 인용 `41:n` = v1.12.8 줄(v1.12.3 대비 735행 이상 +1, 734행 이하 같음 -- `git diff -U0 468e6e73 0c048327` hunk 실측), 엔진 줄 = base `0c048327`(IT-1 + IT-2a 병합) 재측정. 바뀐 것: 줄 번호, '작성 전 실측' 칸, 측정 실패 문장(41:701 대조), V3 칸. 범위·계약은 그대로.

## 의도

- **절차(phase)**: 계획 DEC-86(285행)·N3.12 머리(687-689행, v6.33)로 역할 분리 gate·spec card 흐름·merge_gate가 꺼졌다. 판정 = N6.3(매 변경 뒤 새 test 전체 실행, 작성자 ≠ test 작성자 WP-13, 약화 보고, 변경당 커밋 1) + 독립 측정·검증 agent이고 merge_gate가 아니다. 머리 블록은 형식 호환용이다(공통 문서 '절차 상태').

card IT-2b -- 커널 창. 범위: design 41 4.7-1a(출력 구조 분류 `node.dc_output_structure`), 4.7-2(`Window` 칸 다섯·상태 어휘 -- 불일치 값 없음), 4.7-3 1~5(커널 창), 4.7-3a(창 경계 행 셋 `region_rows`, **(S4-나)**), 4.7-4 '공유하는 것'의 IT-2b 몫(**이동 없음** -- `block_columns._Circuit`에 `region_rows`·감도 반환을 더하고 `_solve`·`_FAILURES`는 그대로; helper `_helpers_dc_solve` 이동은 IT-2d -- 41:760 '이동 시점')·'옮기지 않는 것'의 `_refine_ends`·`_root_windows` 삭제(41:761)·커널 쪽 모듈 수준 `k_max`(41:762)·`saturation_window` 새 서명(4.7-3 2), 4.7-6 `fd_jacobian._steps`, 4.7-8 (8) 커널 y 끝(동작 변경). 계획 N6.6 범위 1(커널 쪽)·완료 조건 (0)(7)(9)(a)~(d)(12)(a 커널 쪽)·(b 상태). 앞 card = IT-2a. `_refine_ends` 삭제는 **이 card**(커널 호출을 없애는 변경 -- 41:761, v1.12.10; 대체 끝 풀이 함수는 IT-2d가 `window_refine.py`에 새로 쓴다).
- **S4 갈래 기록**(계획 v6.33 N6.6 범위 1 '갈래' -- "갈래는 IT-2b 착수 때 master의 EO-1 병합 여부로 한 번 정한다 -- IT-2 판정 card(IT-2b~IT-2d) 모두 같은 갈래이고, 기록 = IT-2 card 재동결"; 41:709): IT-2b 착수 때 **(S4-나)**로 정해졌다 -- EO-1 미병합, `E/authoring/spec_regions.py:16-17` `REGIONS = (REGION_TRIODE,)`(base `2a4ab829` 재측정). IT-2b·IT-2c·IT-2d 모두 이 갈래를 따른다. 따라서 EO-1은 IT-1 + IT-2 통합 병합 뒤에 병합한다(병합 순서 고정 -- 41:709, 계획 N6.1 EO-1 행). `off` 경계 행·V_on 호출·`off` toy·동작점 불일치 묶음은 card EO-1 몫(41:708, 4.7-9 EO-1 '늦게 병합 몫').

- 공통: card base·경로 접두·사용자 결정 원문·병합 관계·착수 조건·절차 상태·graph 단일 정본 계약 G1~G7 정의·정의 불능 code·판정 분해능·S-OS1/S-OS2·작성 전 실측 1~13·승인 기록 초안은 `docs/02-design/specs/20261021-it2-common.md`(옛 IT-2 단일 card 본문, 내용 불변)에 있다. 이 card는 그 가운데 아래 범위만 판정한다.
- 나눔 근거: 사용자 결정 O-69 (2)(2026-10-21) -- IT-2를 IT-2a(스냅샷 파생)·IT-2b(커널 창)·IT-2c(측정 구성)·IT-2d(다듬은 창·front) 넷으로, IT-1 code 위 같은 통합 브랜치, master 병합은 IT-1과 함께 한 번(O-19 (2)). 순서 IT-1 → IT-2a → IT-2b → IT-2c → IT-2d. 나눔은 판정 단위만 바꾸고 design·완료 조건은 그대로다.
- 이 card는 **동작 변경**(design 41 4.7-8). `E/` = `skills/analog-gmid-design/gmid_engine/`, `41:n` = design 41 v1.12.8 줄(base `0c048327` -- 재동결 2026-10-22; 옛 v1.12.3 줄 735행 이상 +1). 공통 문서 '재동결(IT-2b)' 참조.

## 관찰 가능한 계약

- `dc_writer_plan` WRITES에 `("node", "dc_output_structure")`(값 `"high_impedance"`|`"kvl_fixed"`, 출력 포트 넷만), `DC_WRITES` `DC_WRITER_PLAN_WRITER` 행 등록(MF-3), sizing CONTRACT `:14`·소유표 새 행. 계산 = 41:721(IT-1 뒤 `_edges`, `_TIE` 없음, W3 목표 넷은 F′ 아님, `dc_resistor_cycle` 정지 먼저). θ 무관(S0).
- `dc_columns`가 `node.dc_window`를 모든 입력 포트 + W4 뿌리에 쓴다: 뿌리 = A6 되풀이(커널에서 `_refine_ends` 부르지 않음), 뿌리 아닌 포트 = 같은 `input_windows` 호출의 해·감도로 두 끝 전압 [min, max] ∩ 레일, 선언 포트 묶음 = 같은 x 이동량 Δ(묶음 = 선언 포트 전부 -- θ 프레임은 측정 구성 없음), F 성분 미선언 포트 = `Window(None, None, 0, input_status="f_component_undeclared")`, 고립 입력 포트 = 뿌리 절차, 측정 실패 = 뿌리 `unmeasured`(뿌리 아닌 포트·x를 따로 두는 포트 항목 없음 -- 41:701), `tol_v` = 그 해 `tolerance`, A6 b·c = `unsettled`(y 범위는 그대로 씀). `Window` 칸 = `lo`·`hi`·`constraints`·`input_status`·`tol_v` 다섯(41:688). 동작점 불일치 묶음(불일치 상태 값 `"op_mismatch"`·소자 열 칸 `status_detail`·metric code `input_window_operating_point_mismatch`·같은 점 봉인 거부·불일치 toy)은 (S4-나)라 이 card에 **없다** -- 정의도 없다(만들면 배선; 41:688·709·711-714, 계획 v6.33 N6.6 범위 1 '동작점 불일치 묶음'·'갈래'). (S4-나) 기간의 동작(사용자 결정 O-100 수락 -- 원래 취지와 다름(작음, 발동 0)): 동작점에서 여유가 음수인 선언 `triode` 행도 선언 없는 행과 같은 끝 식에 그대로 들어간다(특별 처리 0 -- 41:715).
- `region_rows`(`block_columns._Circuit`의 메서드 -- IT-2d 이동 전, 41:705) 5원소 행 (가) sat (나) triode, (S4-나): `kind` ⊆ {`"sat"`, `"triode"`}, 전도·문턱 계산 0(41:708 -- 측정은 판정 단언 D (c)).
- `_refine_ends`와 그것만 부르는 `_root_windows`를 `block_columns.py`에서 지운다(41:761). `_solve_input_window`·`_interior_solution`·`_dyadic_ys`는 남는다. `block_columns.py`는 `from .k_max import k_max`를 모듈 수준에 유지한다(L12 (a) 주입 지점 -- 41:762).
- `saturation_window(unknown, roots, values, gradient, rows, *, slope=None) -> (dlo, dhi, slope) | None`: 이동량 창, `roots` 원소 = 넷 또는 쌍 `(행 넷, 고정 넷)`, `slope`를 주면 감도 연립 없이 끝만(반환 slope = 받은 값), 끝 식 = 행마다 `slack + sign·(s_a − s_b)·Δ ≥ 0` 교집합(`kind` 안 씀).
- `fd_jacobian._steps`는 writer relation `free_window`(W4 뿌리)만 y 스텝에 씀.
- 판정 단언: OS (a)~(k)(41:727), K1·K2(41:800-801), P (a)(b) 커널 쪽(41:809), D = 계획 완료 조건 (9) (a)~(d)((S4-나) -- 41:810), L12 (a) 커널 쪽(41:814 앞부분 -- `k_max` 소진 toy 주입 지점·tol 미정 toy 도달 조건 포함), L12 (b) `dc_window` 상태(41:814), L12 (e) 커널 y 끝점 기대(41:814, 4.7-8 (8)).
- **D (S4-나) = 계획 (9) (a)~(d)**(41:810): (a) `triode` 선언 소자가 동작점에서 triode이고(전제 단언) 훑기 중 포화로 가는 toy → 그 행 `(d, s, −부호, VDsat − VDS − tol_VDsat)`의 영 교차 = 커널 창 끝(손계산; 다듬은 창 쪽은 IT-2d) (b) `region_rows` 행 `kind` 집합 = {`"sat"`, `"triode"`} (c) 행 여유는 `tol_VDsat` 정본 값과 그 해의 VDS·VDsat만 읽고 경계 행 계산은 전도·문턱 계산을 하지 않음 -- 측정은 **정적 AST만(docstring·주석 제외)**: `region_rows`와 그것이 부르는 IT-2 모듈 함수의 소스에 (i) VGS 인자가 상수 0인 `op_point` 호출 0 (ii) `device.dc_off_current`·`device.dc_conduction_floor` 읽기 0 (iii) EO-1 모듈 import 0; 새 계수기·monkeypatch 없음 (d) 불일치 상태 값·소자 열 칸·그 metric code 정의 포함 0 -- 측정 = (c)와 같은 꼴의 **정적 AST**(비test 엔진 소스, docstring·주석 제외): 식별자(이름·속성·인자·키워드·dataclass 필드·대입 대상)와 문자열 상수에 검색 대상 이름 다섯 `"op_mismatch"`·`status_detail`·`input_window_operating_point_mismatch`·`INPUT_STATUS_OP_MISMATCH`·`CODE_INPUT_WINDOW_OPERATING_POINT_MISMATCH` 0(41:810; 41:688 'S-4 갈래 몫의 꼴').

graph 단일 정본 검사(이 card 범위): G1(`node.dc_output_structure` writer = `dc_writer_plan` 자리 하나·권한표 행 하나 -- OS (j); G_vgs 걷기·`_edges` 호출은 `writer_plan.py`에만; 창 끝 식은 `saturation_window`에만), G2(새 cache·사본 0), G3(출력 구조는 S0 필드 하나, `w3_target` 표지 없음 -- W3 여부는 `node.dc_writer`), G6(`node.dc_output_structure` 소비자는 IT-2c·IT-2d가 배선 -- 이 card 단독 시점에는 **출력 전용 상태**를 감사가 기록하고 IT-2c 병합본에서 소비자 ≥ 1 확인; `node.dc_window` 새 칸 둘(`input_status`·`tol_v`)의 소비자도 IT-2c(`icm_config` 상태 칸)·IT-2d(`metrics_aux`)), G7(`dc_writer_plan` θ 무관 `computes` 증분 0 -- OS (i)).

정의 불능 code·S-OS1/S-OS2·판정 분해능 문언은 공통 문서 해당 절이 정본이다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.sizing.s2_values` | `Window` | `Window(lo, hi, constraints, input_status=None, tol_v=None)`(칸 다섯 -- `status_detail` 없음, 41:688) |
| `gmid_engine.sizing.s2_values` | `OUTPUT_HIGH_IMPEDANCE` | 상수 `"high_impedance"` |
| `gmid_engine.sizing.s2_values` | `OUTPUT_KVL_FIXED` | 상수 `"kvl_fixed"` |
| `gmid_engine.sizing.input_window` | `saturation_window` | `def saturation_window(unknown, roots, values, gradient, rows, *, slope=None) -> tuple | None` |

(`gmid_engine.sizing._helpers_dc_solve` 신규 모듈 행(`Circuit`·`solve`·`FAILURES`)은 IT-2d로 옮겼다 -- 41:760 '이동 시점'. IT-2b에서 `Circuit`·`solve`·`FAILURES`·`region_rows`는 `block_columns` 안 비공개 이름(`_Circuit`·`_solve`·`_FAILURES`, `_Circuit.region_rows`)이라 공개 시그니처가 아니다.)

## 판정 유형 근거

red-green. 새 이름은 존재 부재 red(`ImportError`·`AttributeError` -- 00-common §8.1, '신규 시그니처' 표 대조), 행동 red는 시그니처 불변 진입점이 맡는다(새 키워드 직접 호출 `TypeError`는 red로 세지 않는다). 결정성 비트 동일은 감사의 equivalence 측정(같은 head 두 번).

## oracle 종류와 출처

(손) 이름 없는 toy 연결의 손계산(design 41 4.7-7), (식) design 식 그대로, (비교) 같은 스냅샷 필드로 부른 같은 순수 함수의 두 경로 같음, (독립) `RunCounters`·perf 증분·`git grep`. 피검 함수로 기대값을 만들지 않는다. SPICE 다리는 **보류**(card EO-1, 41:817).

## library 회로 적용 여부

적용(동작 변경). 감사가 9회로 변화표(원인 칸 = card 0 IT-0 기록 대비, 41:817 (1)~(8) -- (8) 커널 y 끝은 v1.12.10)·결정성·G-10 9회로 0을 잰다. 회로·소자·넷 이름 코드 0(EP-1).

- **출력 구조 분류표 대조**(감사 몫 -- 41:724, 계획 v6.31 N6.6 순서 1519행, 사용자 결정 O-66 (1)(3)): 정본 "그 표가 IT-2의 분류 기준선이다 -- IT-2 변화표는 이 필드 값을 표와 대조해 적고, 불일치면 구조 규칙을 고치기 전에 멈추고 보고한다; 병합 전에 W3 목표 선언(CI-15)·F 선언·코퍼스가 바뀌면 표를 다시 재고 승인받은 뒤 병합한다". 단언(대조 범위 -- 41:724 v1.12.10, O-66 (1) 승인 범위): 13회로(library 9 + heldout 4) 출력 15개 가운데 엔진 값이 있는 **12출력**은 `node.dc_output_structure` 값(`"kvl_fixed"`/`"high_impedance"`)이 승인된 표의 '새 분류' 칸(**KVL**/**HZ**)과 같음을 변화표에 출력별로 적고, 쓰기 계획이 정지하는 **3출력**(cnr_ota VOP·VON -- `dc_resistor_cycle`, 넷 VCR·VDD_1V8; erfc_ota out -- `mos_zero_current_structural`)은 값 대조 대신 **정지 사유가 표 §0과 같은지**(규칙 갈래·넷 -- 표 §0 13행: cnr_ota `StructureUnresolvedError` `dc_resistor_cycle`(x40 VCR–VDD_1V8), erfc_ota `mos_zero_current_structural`(M19·M20·M21))를 적는다. 사유가 다르거나 다른 출력에서 정지가 새로 나면 불일치다. 승인된 표 = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-21/de1_output_structure_13.md` §2 '표 -- 출력 15개(13회로)' 37-57행(표 본문 41-57행, 회로별 근거 §3 67행~, 표 작성 때 spec 선언 §1 17-33행); 승인 원문 = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md:687` O-66 (1) '13회로 출력 구조 분류표 승인 -- 15출력 KVL 고정 7·고임피던스 8'. 두 파일은 저장소 밖(`wt/_drafts`, git 추적 없음)이다. 감사 쪽 멈춤: 불일치 출력이 하나라도 있으면 판정을 내지 않고 멈추고 보고한다(구조 규칙을 고치기 전에); 병합 전에 W3 목표 선언(CI-15)·F 선언·코퍼스가 표 작성 때(§1)와 달라졌으면 표를 다시 재고 사용자 승인을 받은 뒤 병합한다.
- **동작 변경 (8) 커널 W4 입력 뿌리 y 끝**(41:817 4.7-8 (8), 사용자 결정 O-103 -- 원래 취지와 다름(작음)): 커널 y 범위 끝은 A6 선형 끝이다. 함께 바뀌는 값(비트 동일 아님) = 뿌리 `lo`·`hi`(다듬지 않은 끝), 그것을 읽는 θ y → V 사상, `fd_jacobian` y 스텝 값 -- 감사는 이것을 무동작이 아니라 변화표 원인 칸 (8)로 적는다(옛 '무동작 판정 입력'에서 옮김). θ y = 0·1 끝점은 봉인 7이 거부할 수 있다(끝점 test 기대 = L12 (e)).

## 거부해야 할 입력

- `saturation_window`에 4원소 옛 행 꼴을 넣는 호출은 엔진에 0(새 꼴 5원소만).
- 다중 입력 뿌리 정지는 IT-1 몫(이 card는 그 정지를 전제로 뿌리 하나).

## 무동작 판정 입력(무발동 값)

없음. 옛 문언 '뿌리 `lo`·`hi`와 `fd_jacobian` y 스텝 9회로 비트 동일'은 지웠다 -- 뿌리 `lo`·`hi`, θ y 사상, `fd_jacobian` y 스텝은 동작 변경 칸 4.7-8 (8)로 옮겼다(위 'library 회로 적용 여부', 41:817 '함께 바뀌는 값 … card 무동작 판정 입력에서 뺀다').

## 재현할 수치

없음(toy 손계산은 test 주체 소유).

## 결정 필요 항목

없음(U-1은 O-69 (2)로 결정). 착수 조건(공통 문서): IT-1 code 커밋, card 0 IT-0 기록. C-5는 해소됨(design 41 v1.12.4 735행 `_transfer_resolution`, 사용자 결정 O-72 (1)) -- IT-2c code 착수에는 대신 IT-2c 착수 실측 (a)~(c) 기록(공통 문서 'IT-2c 착수 실측')이 필요하다. 그 밖 design에 없는 판단은 멈추고 보고.

## code 작성자 멈춤 조건

- S4 갈래 = **(S4-나) 확정**(위 '의도' 갈래 기록). 동작점 불일치 묶음의 이름(위 D (d) 다섯)을 정의하거나 `region_rows`에서 전도·문턱 계산을 하려면 멈추고 보고(EO-1 몫).
- 4.7-1a 분류에서 계획에 없는 출력 갈래를 만나면 멈춤(S-OS1/S-OS2 fail-closed는 IT-2c).
- **분류표 불일치**(41:724 "불일치면 구조 규칙을 고치기 전에 멈추고 보고한다; 병합 전에 W3 목표 선언(CI-15)·F 선언·코퍼스가 바뀌면 표를 다시 재고 승인받은 뒤 병합한다"): 13회로 실행에서 값이 있는 12출력의 `node.dc_output_structure`가 승인된 표(위 'library 회로 적용 여부'의 경로)의 '새 분류'와 다르거나, 정지 3출력(cnr_ota VOP·VON `dc_resistor_cycle`, erfc_ota out `mos_zero_current_structural`)의 정지 사유가 표 §0과 다르거나, 다른 출력에서 정지가 새로 나면 분류 규칙·G_vgs 걷기를 고치지 말고 멈추고 보고한다(41:724). W3 목표 선언(CI-15)·F 선언·코퍼스가 표 작성 때와 달라진 것을 알게 되면 같은 식으로 멈추고 보고한다(표 재측정·재승인은 오케스트레이터·사용자 몫).
- helper 이동 금지: IT-2b에서 `_helpers_dc_solve.py`를 만들지 않는다(사용자 하나인 `_` 모듈은 구조 규칙 A 보충 (3) 위반 -- 41:760). `_Circuit`·`_solve`·`_FAILURES`·`_Circuit.region_rows`는 `block_columns.py` 안에 둔다.
- **code 정리 권장**(메모 -- 판정 단언 아님): `_windows`의 `kernel.measured.slope.get(net, 0.0)`(`85847b49` `block_columns.py:276`)을 `slope[net]`으로 바꾼다 -- 감도가 없는 포트를 0으로 조용히 대체하지 않고 `KeyError`로 드러낸다(fail-closed, N3.14).
- 공통 멈춤: design에 없는 것을 정해야 하면 멈추고 보고(as-built 결정 금지), 정본 자리가 없으면 만들지 않는다(CLAUDE.md graph 단일 정본 규칙 6, 공통 문서 C-7). 범위 밖 하위 card의 일을 당겨오지 않는다.

## test 작성 주체 몫(code 주체는 고치지 않는다)

- `E/tests/sizing/test_s2_values.py`: `:70-75` `test_dc_table_has_33_fields`(33 → 34, 이 card에서 `dc_output_structure` 한 행; IT-2d가 35로), `:118-124` `test_dc_writes_constant_matches_table`(`DC_TABLE`에 `("node", "dc_output_structure")` → `dc_writer_plan`), `:127-128` `test_block_name_and_writes_match_table`(블록 WRITES = 표), `:97-106` `test_s2_writers_is_s1_plus_dc_table_exactly`(DC_TABLE 확대분) -- 표 확대, 약화 아님.
- `E/tests/sizing/test_input_window.py`(옛 `saturation_window` 서명 호출).
- 새 test: `tests/sizing/test_output_structure.py`. 커널 창과 D·`region_rows` 단언은 기존 `dc_columns` test 파일(`E/tests/sizing/test_block_columns.py` -- `E/tests/sizing/test_size_and_seal.py:332·340`이 그 파일의 `_mirror_ctx`·`_mirror_theta`를 import한다). **`tests/sizing/test__helpers_dc_solve.py`는 IT-2b에서 만들지 않는다**(규칙 H 고아 방지 -- 대응 모듈 `_helpers_dc_solve.py`가 IT-2d에 생김, 41:760): 그 파일에 두려던 IT-2b 단언(T-D `triode` 행 영 교차·`kind` 집합·AST 부재 검사)은 `test_block_columns.py`로 옮기고, `Circuit`·`solve`·`FAILURES` 공개 이름 test는 IT-2d로 넘긴다.
- **T-D에서 동작점 불일치 단언 제거**: `op_mismatch` 상태·`status_detail`·같은 점 봉인 거부·`input_window_operating_point_mismatch` 단언은 IT-2b test에 두지 않고 card EO-1 test(완료 조건 N6.20 (8)(e))로 옮겨 간다. IT-2b의 D는 계획 (9) (a)~(d)뿐이다.
- **L12 (a) 커널 쪽 toy**(41:814): `k_max` 소진 toy는 주입 지점 `gmid_engine.sizing.block_columns.k_max`(상한 1)만 쓰고, 전제 단언으로 `_solve_input_window`의 소진 분기 도달을 보인다(요청 y ≠ 1/2, y = 1/2 풀이 성공, 첫 회 창과 둘째 측정 창의 차 > tol -- 손계산; 자기참조 노드 없는 toy). tol 미정 toy(A6 b)는 41:694 'A6 b 도달 조건'으로 만든다 -- 슬라이스에 VDSAT 열 없음(열 출처 = 기준 LUT), 기준 LUT VDSAT 셀 정의, 슬라이스 id_equivalent 셀 미정, 비순환 쓰기 계획(`graph.dc_scc_order`로 전제 단언); 픽스처는 sizing conftest에 새로 만든다; `run_blocks(…, upto="columns")` 스냅샷에서 본다. **만들 수 없으면 test 작성 주체가 멈추고 보고한다.**
- **L12 (e) 커널 y 끝점 기대**(41:814, 4.7-8 (8), 사용자 결정 O-103): 대상 test 둘 = `E/tests/sizing/test_input_window.py`의 `test_off_mid_window_maps_y_and_ends_saturated`(y = 0·1)·`test_mid_window_ends_have_nonnegative_saturation_slack`. 내부 y(0 < y < 1)는 기존 단언(봉인 7 pass, 독립 여유 ≥ −1e-12) 그대로. 끝점 y는 '봉인됨(그러면 기존 단언 그대로)' 또는 '봉인 7 거부 + 엔진 봉인 7 기록 `slack_v`와 독립 oracle 여유(`_oracle_slacks`)가 **모두** |·| ≤ `node.dc_window.tol_v`(그 점 뿌리 항목)'. `tol_v`가 None이면 그 사례는 무효이고 통과로 세지 않는다.
- **test 메모**: P (b) 입력 DC 둘 선언 toy의 선언 차는 0이다(입력 DC는 스칼라 선언 -- 두 포트 같은 값). `assert_voltages` 키 단언은 둘로 나눈다. P (a) 감도 음수 포트 toy는 이미 있다(`fd7c636f`, `role/test/it2b`).
- (재측정 `0c048327`) 위 `test_s2_values.py` 줄·이름·33은 그대로다(`468e6e73..0c048327` 이 파일 변경 = IT-1 test 커밋의 `:153-154` `dc_columns` READS 기대(`node.port_direction`)와 `:179-200` `test_vocabulary_constants` 어휘뿐 -- 네 test 몸은 그대로, IT-2a는 이 파일을 고치지 않았다; `DC_TABLE` 키 33·`SS_TABLE` 키 7 -- AST 계수). 새 test 파일 이름 둘은 `E/tests/**`에 0건(충돌 없음), `test_it2b_` 접두 0건.

## 작성 전 실측

공통 문서 '작성 전 실측' 1~13을 따른다. 이 card 사실(재측정 base `0c048327` = IT-1 + IT-2a, 2026-10-22; 괄호 안 = 옛 `468e6e73` 줄): `E/sizing/writer_plan.py:71`(`WRITES` 4필드, `dc_output_structure` 없음; 옛 :73)·`:95`(`_edges`)·`:117-118`(`@compute_block` `dc_writer_plan`), `E/sizing/s2_values.py:140`(`DC_WRITES`; 옛 :143)·`:143`(`DC_WRITER_PLAN_WRITER` 행; 옛 :146)·`:353`(`class Window` -- 칸 `lo`·`hi`·`constraints` 셋; 옛 :356), `E/sizing/block_columns.py:142`(`_Circuit`; 옛 :143)·`:218`(`saturation_rows`; 옛 :225)·`:239`(`input_windows`; 옛 :246)·`:549`(`_solve`; 옛 :560)·`:617`(`_FAILURES`; 옛 :628)·`:652`(`_refine_ends`; 옛 :663)·`:680`(`_solve_input_window`; 옛 :691), `E/sizing/input_window.py:26`(`_sensitivities`)·`:48`(`saturation_window(unknown, root, values, gradient, rows)` -- 옛 서명 그대로), `E/search/fd_jacobian.py:54-55`(`win.hi - win.lo`, writer relation 거름 없음), `E/authoring/spec_regions.py:16-17`(`REGIONS = (REGION_TRIODE,)` -- EO-1 미병합 → **(S4-나)**). `dc_output_structure`·`OUTPUT_HIGH_IMPEDANCE`·`_helpers_dc_solve`·`region_rows`·`input_status` 엔진 비test `.py` 0건. `E/sizing/CONTRACT.md:14`(`dc_writer_plan` S0 문단)·`:191`(`node.dc_writer` 행)·`:202`(`node.dc_window` 행 -- 범위 'W4 뿌리 노드') 그대로. IT-1 뒤 `_TIE`·`input_tie`·`INPUT_GROUP_KEY`·`REL_TIE` 엔진 비test 0건(41:721 전제 충족). V3 규모(8): **해당 없음(DEC-86)** -- 선례 IT-1·IT-2a 판정 기록 V3 = `N/A`('merge_gate·mutate_changed 미사용, N6.3 절차', `.ai/verification/20261021-it1-input-tie-removal.json`·`20261021-it2a-snapshot-derive.json`). 이 card에서 채우지 않은 이유: (i) `mutate_changed.py`는 `--base`·`--head` 커밋 사이 바뀐 `def`를 변이하므로 IT-2b code 커밋 전에는 잴 대상이 없다 (ii) 인벤토리 test 노드를 `TESTS_PREFIX = "skills/analog-gmid-design/assets/tests/"`(`tools/gates/mutate_changed.py:38`·`:622`)로 거르므로 `E/tests/**` test는 인벤토리에 들지 않는다.
