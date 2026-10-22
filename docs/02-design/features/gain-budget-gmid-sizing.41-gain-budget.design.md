---
template: design
version: 1.12.9
plan_version: 6.32
---

# gain-budget-gmid-sizing -- 41-gain-budget Design Document

> **Summary**: gain-budget-first 흐름을 설계한다(계획 N1.1, FR-1·FR-2·FR-4·FR-8, DEC-03·05·43·57·59·63·65·71·73·77·81). 다루는 범위는 여섯 가지다.
> - connectivity에서 signal stage를 유도한다(SP1).
> - 블록 국소 소신호 모델로 stage gain을 정의하고, 평가마다 전회로 MNA와의 잔차를 기록한다.
> - LUT 격자 상한으로 탐색 전에 달성 가능성을 판정한다.
> - 층 0에서 블록 gain bin별 (전력, 면적) 비지배 점을 만들고, 조합 DP로 예산 조합 front와 `gain_budget_db`를 낸다. 이 결과를 외층 SLSQP와 잇는다.
> - 스펙에서 gm/ID·L·전류 출발 구간을 topology와 무관하게 유도한다.
> - 잡음 경로를 만든다. spec 제약, LUT 잡음 데이터, MNA adjoint 잡음 해석, 오라클 `.noise` 대조를 포함한다.
>
> **Date**: 2026-10-22 · **Status**: v1.12.9 **계획 v6.32 맞춤판 -- 승인 대기**(사용자 결정 O-96·O-97, 계획 master `559f4da2`)(넷째 커밋 = 재검증 `wt/_drafts/evidence/2026-10-22/design_v1129_recheck2.md` 95/100 S-Q1·N-Q1(L11 (e) 재연 선택 사례: 두 평가 모두 같은 컨텍스트에서 `size_and_seal` 직접 호출, 유효 조건 `replays` +1, 주입 = 블록 인스턴스 `fn` 교체 또는 실제 실패 θ·`InfeasibleSizingError` 하위)·R2(4.7-7 41:804 장애 주입 범위 괄호) 반영; N-Q2 -- 41:753·813과 40:2092가 셋째·넷째 커밋으로 더 길어짐, 같은 가독성 부채, 줄 수 유지 방침 그대로)(셋째 커밋 = 재검증 `wt/_drafts/evidence/2026-10-22/design_v1129_recheck.md` 93/100 S-R1('블록 이름 집합' 인식에 문자열 상수 집합·tuple과 매개변수 이름 집합 추가)·S-R2((나) 대조 평가 한 갈래, 계획보다 엄격 표시)·S-R3((가) 셋째 관측 = `donors.find_failure` None, 재연 경로 선택 사례 1건)·N-R1(호출로 감싼 피연산자 안 추적·양성 대조 2)·N-R2(`"*"` 리터럴) 반영, 둘째 커밋의 S-3 기각 사유 정정; N-R3 -- 41:753·40:2092 bullet이 더 길어져 가독성 부채가 커짐, 줄 수 유지 방침은 그대로)(둘째 커밋 = 독립 검증 `wt/_drafts/evidence/2026-10-22/design_v1129_validation.md` 90/100 S-2·S-3(수정 수용 -- 셀 연산만 정함; 검증자 안 대신 대체 정의를 택함 -- 계획 v6.32 N3.3 문언('base writer 집합과 블록 이름 집합이 함께')을 그대로 구현)·S-4·N-1·N-2와 design↔계획 gap G1·G2·G4 반영: 4.7-3c 문서 갱신 대상·AST 셀 연산·'부른 = 성공한' 대조, L11 (e) 개수 박은 문언 → 구성 상수·실측, (가)의 관측, `writers_in_scope(None, …)` `TypeError`, 4.7-7 interface 목록; N-5(긴 bullet)는 줄 수 유지 방침으로 알려진 가독성 부채). **v1.12.9 변경**(백로그 B69 해소 -- card IT-2e): 4.7-3c '실패 평가의 부분 스냅샷 파생'(사실 정정 = parent 경로 부분 스냅샷에 낡은 필드가 k..끝(실패 블록 자신과 커널 블록 실패 포함); 남기는 writer = base writer ∪ 실패 전에 부른 블록, 봉인 위반은 `dc_seal_report` 유지; 집합 함수 하나 `writers_in_scope(base, blocks) -> frozenset`(`E/sizing/seal_versions.py`)와 부르는 자리 셋(파생 keep·봉인 4 coverage 차집합 꼴·실패 부착), 앞 블록 얻는 방법, 재연 예외도 같음), 4.7-7 L11 (e)(계획 (11)(e) -- 사례 유효 조건 (가)(나)·변성 관계·AST red 변형 둘·계수 변화 0), 4.7-8 IT-2e 변경 종류, 4.7-9 판정 단위에 card IT-2e; 낡은 엔진 줄 인용 7곳 정정(내용 불변, `integ-it12` `56080584` 재측정 -- 4.7-1a `writer_plan.py:95`·`_TIE`(IT-1에서 삭제)·`:162-165`·`s2_values.py:143`, 4.7-3a `block_columns.py:223-224`, L10 (a) `writer_plan.py:117-118`·`seal.py:48`). 줄 추가 없음. **v1.12.8 상태(대체됨)**: v1.12.8 **정오판 -- 계획 v6.31 맞춤, 승인됨(사용자 O-95, 2026-10-22)**(셋째 커밋 = 재검증 `wt/_drafts/evidence/2026-10-22/plan_v631_design_v1128_recheck.md` 91/100 G-1·N-2·N-3). **v1.12.8 변경**(사용자 결정 O-94 -- IT-2a 구현 dispute 검증): 4.7-3c keep = base writer ∪ 봉인 4가 받는 호출 목록(커널 블록 ∪ 봉인 항목 블록 여덟, 봉인 항목 구성원 정본 = `E/sizing/seal.py` 모듈 상수 하나), `dc_seal_report`는 keep 밖 → graft(원래 취지와 다름(작음), 승인 O-94 (2)); `seal_dc` `base` 필수 키워드(O-94 (3)); 착수 실측 (i)에 DC 열세 블록 outcome 기대(reuse 12·graft 1); L11 (d) 추가. 둘째 커밋(검증 `wt/_drafts/evidence/2026-10-22/design41_v1128_validation.md` 88/100 S-1·S-2·R-1~R-3·N-2): 계획 v6.31(같은 정오, plan/o94) 인용, extras 블록 키 매핑(R-1), `seal_versions` base None 거부·건너뛰기 분기 삭제(R-2), 실패 부분 스냅샷 사실 한 구절·백로그(R-3 -- 그 '원래 취지와 다름(작음)'·백로그 B69는 v1.12.9에서 계획 v6.32 N3.3·O-96으로 해소), 착수 실측 (i) 항목 수(N-2); S-2(base 추가 test 호출 7곳)는 승인 기록 몫. 옛 문언 '커널 호출 블록 이름(`steps`·`later`)'은 계획 N3.3 '그 평가가 부르는 계산 블록'보다 좁았다(v1.12.7 design↔계획 gap 분석이 놓침). 줄 추가 없음. **v1.12.7 상태(대체됨)**: v1.12.7 **계획 v6.28(병합 `e87092b3`, 사용자 O-85·O-86·O-87) 맞춤판 -- 사용자 승인 O-90**. **v1.12.7 다섯째 커밋**(O-89 (3); 계획 정합 = v6.29 대기 -- READS 일곱 문언은 계획 v6.29(O-89 (1)) 병합 뒤 계획과 맞음): 41:734 (바)에 자체 BFS를 쓰는 이유 한 구절(`graph.dc_segments` 가지치기·`signal_reach` AC·`stage_bfs` AC 셀 비용·`composite_diode._walk` 직렬 가지). 줄 추가 없음. **v1.12.7 넷째 커밋**(오케스트레이터 확인 -- `device.kind` 유지): 41:734 (나) 이상 전류원 제외를 엔진 선례 술어 그대로 `element_class == ELEMENT_SOURCE and kind == CURRENT_SOURCE`(`ss_circuit.py:19·57`, 상수 `sizing/s2_values.py:22`)로 적음 -- 재사용 helper 없음(같은 술어가 세 자리에 인라인), READS 일곱 그대로, 계획 (10)(f) 'device.kind' 문언 충족. 줄 추가 없음. **v1.12.7 셋째 커밋**(사용자 결정 O-88 -- MOS 식별 정정): 41:734 (나) MOS 식별 = S1 정본 필드 `device.element_class == ELEMENT_MOS` READS(선례 `dc_metrics.py:40`·`achievability.py:108`); 둘째 커밋의 `device.pins` gate 단자 유무 추정(검증 MF-1 권고를 정본 필드 확인 없이 옮긴 것)은 정본 필드로 대체·철회, `device.pins`는 단자 넷 조회에만, g→d·g→s 단자 이름 = 공개 `MOS_TERMINAL_NAMES`(R-a); READS 여섯 → 일곱(`device.element_class` 추가); L10 (i) '지원 kind 상수 참조 0' 유지. 줄 추가 없음. **v1.12.7 둘째 커밋**(사용자 결정 O-87 (1), 검증 `wt/_drafts/evidence/2026-10-21/design41_v1127_validation.md` 88/100 MF-1·MF-2·N-1·N-3·N-4): (1) U-1 -- IT-2c 범위 확대 철회: 차동 출력 + 선언은 지금처럼 S-OS2 code, 차동 결합·`icm_config_feedback_outputs_split`은 S-OS2 일반형 card 몫(이름 예약), IT-2c 갈래 순서 = 지원 밖 → 단일 출력 경로 판정 → 구성 선택, L8 (d) 갈림 toy 삭제 (2) MF-1 -- MOS 식별 = `device.pins` gate 단자, L10 (i) 지원 kind 상수 참조 0(예외 없음) (3) MF-2 -- 서명 `_dc_feedback_reaches(view, output, cut_nets)`, 출발 = 그 출력 넷 하나 (4) N-4 -- 744 (2)의 옛 이름 괄호를 여기로: v1.12.6 이름 `icm_config_feedback_source_unsupported`는 v1.12.7에서 `icm_config_feedback_element_unsupported`로 바뀜(code에 들어간 적 없음). 줄 추가 없음. **v1.12.7 첫 커밋 변경**(사용자 결정 O-85 (1)~(3)·O-86 M1·N1~N4, 계획 v6.28 N3.8 '차동 출력'·'지원 밖 원소'·N6.6 완료 조건 (10)(a)(f)·IT-2c 착수 조건 (iv) 범위 -- 근거 `wt/_drafts/evidence/2026-10-21/design41_v1126_validation.md` MF-A·R1~R8): (1) 4.7-3b (1) 차동 출력 결합(두 출력 판정이 같을 때만, 갈리면 새 code `icm_config_feedback_outputs_split`)과 이 card의 갈래 순서(① 지원 밖 ② 갈림 ③ S-OS2 fail-closed) (2) 지원 밖 원소 = S1 `device.unsupported` READS(kind 목록 대조 삭제 -- 둘째 계산 제거), code 이름 `icm_config_feedback_element_unsupported`(계획이 정함, 옛 `icm_config_feedback_source_unsupported`) (3) L10 (a) 멈춤 S-FB1 해소 -- 계획 (10)(a) 새 문언((i) 함수 객체 참조 load·`tests/` 제외·네 자리만 (ii) 원 함수 `__code__`·양성 대조 (가)(나)·reuse 없는 실행 (iii) (e)) (4) L8 (d) 새 code 두 toy, L10 (i) READS (5) 40·42 같은 판. 줄 추가 없음 -- 줄 번호 v1.12.6 그대로. **v1.12.6 상태(대체됨)**: 계획 v6.27 맞춤판(멈춤 S-FB1은 v1.12.7에서 해소). **v1.12.6 변경**(사용자 결정 O-81~O-84, 계획 v6.27 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나'·N6.6 완료 조건 (8)(b1)~(b3)·(10)(e)(f)·IT-2c (iii) 범위 -- 근거 `wt/_drafts/evidence/2026-10-21/design41_v1125_validation.md` MF-1·N1~N9·`plan_o81_validation.md`): (1) 4.7-3b (1) no_dc 판정 = kind 판정에서 경로 판정(방향 의존 그래프 BFS, `icm_config.py` 비공개 `_dc_feedback_reaches`, S1 READS 다섯 추가, 측정 구성 선택 전, O(N), cache 없음), 판정 불능 code `icm_config_feedback_source_unsupported`, 정의 불능 갈래의 `IcmConfig` 칸·code 순서(N3) (2) 절단 넷 순수 함수 `feedback_cut_nets`(`_feedback_cuts.py`, 직접 호출 넷, `input_terminal_nets`·`_input_side` 삭제·래퍼 없음, 레지스트리 행) (3) L8 (b1)~(b3)·R2 toy(N4)·unmeasured 단언(N9), L10 (e) 저항·Rf∥Cf(MF-1), L10 (i) 판정 자리 하나·동작 동일성 test (4) 744 (2) code 목록 (5) 멈춤 S-FB1 -- 계획 (10)(a) 측정 꼴과 (10)(f) 충돌 (6) 40·42 같은 판(N6, O-84 40 §6-8 한 줄). 줄 추가 없음 -- 줄 번호 v1.12.5 그대로. **v1.12.5 상태(대체됨)**: 계획 v6.26 맞춤판. **v1.12.5 변경**(사용자 결정 O-79·O-80 R1·R2, 계획 v6.26 N3.8 'ICMR 측정 구성'·N6.6 IT-2c 착수 조건 범위만 -- 근거 `wt/_drafts/evidence/2026-10-21/plan_o78_validation.md` M1·재검증 R1~R3): (1) 4.7-3b (1) 갈래 추가 -- 단일 출력 + DC 성분 없는(용량만) 선언 되먹임 = `config` None + 정의 불능 `icm_config_feedback_no_dc`(이름만 design 몫; DC 성분 = `DC_CONDUCTING_PASSIVE_KINDS` 기존 정의, 단일 입력은 `as_is_single_input` 먼저 -- R2), S-3 망은 그 갈래에서 세우지 않음 (2) 744 (2) 정의 불능 code 목록에 그 code (3) L8 (b) -- 용량만 선언 단일 출력 toy = 정의 불능 기대, 선언 구성 창 test는 저항 선언 toy(`declared_feedback`)로; `config` 값 집합 그대로 (4) 줄 추가 없음 -- v1.12.4 줄 번호 그대로(L8 = 811, L10 = 812). **v1.12.4 상태(대체됨)**: 계획 v6.24(병합 `59ecc88e`, 사용자 O-70 (2)) 맞춤판. **v1.12.4 변경**(사용자 결정 O-66~O-71, IT-2 창 design 범위만 -- 슬루 시작 동작점(N3.8 577)·DEC-74 front 판정 기록·oracle은 설계하지 않음): (1) 4.7-3b (1) 반전 입력 식별의 판정 분해능 = 계획 N3.8 '판정 분해능의 정의 자리'(576) 인용, 정의 함수 하나 `_transfer_resolution`(δV_out = |z_u|ᵀ|r|, `icm_config.py` 비공개 -- 실현 가능성 근거·DE-1 이동 인계), 기록 = `IcmConfig.transfer` resolution 칸 = δA_num (2) 멈춤 S-OS2 -- 일반형은 계획 v6.24 N3.8 '차동 출력 회로의 측정 구성'(O-68 (2))이 정했고 후속 card 몫, IT-2c는 fail-closed로 시작(O-67 (5)) (3) 13회로 출력 구조 분류표 승인 = IT-1·IT-2 통합 병합 조건(O-66 (3), 충족 -- O-66 (1)) (4) 정의 불능 code 목록 보완, 깨지는 기존 test 넷 (5) IT-2c 착수 실측 (a)~(c)·card 넷 분할(O-69 (2)) 인용. **v1.12.3 상태(대체됨)**: 검증·gap 반영판 -- 계획 v6.23 맞춤. **v1.12.3 변경**(design 검증 MF-1~MF-4·N-1~N-3, gap 분석 `_drafts/evidence/2026-10-21/design_it12_v1122_plan_gap.md` N1~N3): MF-1 OS (e) 단단한 경로 = MOS 엣지(저항만 경로는 기존 `dc_resistor_cycle` 정지가 먼저) -- 4.7-1a·4.7-8a; MF-2(= gap N1) 멈춤 S-OS1 실행 중 fail-closed code `icm_config_output_root_w3`(N3.14 적용) -- 4.7-1a·4.7-3b (1)·L8 (d); MF-3 권한표 `DC_WRITES`·sizing CONTRACT 소유표 등록, 깨지는 기존 test 둘은 test 작성 주체 몫, OS (j) grep 꼴 -- 4.7-1a; MF-4 멈춤 S-OS2(차동 출력 + 되먹임 선언) fail-closed code -- 4.7-1a; N-1 분류 걷기에 `_TIE` 엣지 없음(계획 N6.5)·toy OS (k); N-2 동작 변경 목록 기준선 둘로 나눔·(6) 넓힘 -- 4.7-8; N-3 S-OS 발동 측정에 heldout 4회로 -- 4.7-8a; gap N2 고임피던스 W3 목표 출력의 다듬은 창 끝 풀이 = 목표값 자리에 x -- 4.7-3b·4.7-4 2·L8 (d); gap N3 단일 입력이면 (5)가 (3)보다 앞섬 -- 4.7-3b. **v1.12.2 상태(대체됨)**: 계획 v6.23 맞춤판. **v1.12.2 변경**(사용자 결정 O-63 (4)·O-64 (1)(2), IT-2 창 design 범위만 -- DE-1·P10/P11 기록·oracle은 설계하지 않음): (1) **41:751 멈춤 해소**(O-63 (4)) -- 측정 구성 `as_is_single_input`의 입력 포트는 `dc_window_refine`이 쓰지 않고 front·보고는 `node.dc_window_cfg`('추정' 선형 감도 끝)를 읽는다, 정밀 값은 oracle SPICE 다리, 엔진 전체 DC 끝 풀이 신설 없음(계획 N3.8 '선형 감도 끝만 정의되는 구성의 정본 칸' -- 4.7-3b·4.7-4 1·2·4.7-5) (2) **출력 구조 분류 = 계획 N3.8 '출력 구조 분류 -- 규칙 하나'**(O-64 (1)) -- S0 graph 필드 `node.dc_output_structure`(writer = 쓰기 계획 블록 `dc_writer_plan` 하나, θ 무관, 값 {`high_impedance`, `kvl_fixed`}; 4.7-1a 신설), v1.12.1의 `IcmConfig.output_structure` 칸(봉인 뒤·평가마다 계산)과 값 `w3_target` 삭제, `icm_config`·`dc_window_refine`·card DE-1은 READS만 (3) **출발 창 미수렴 포트**(O-64 (2)) -- 다듬은 창 계산 안 함(v1.12.1 '다듬는다'와 그 '원래 취지와 다를 수 있는 항목' 보고 대체), front 값 정의 불능 `input_window_unsettled`, 선언 제약이 걸리면 기존 미측정 경로로 최종 front에서 빠짐·원인 = 미수렴 code(4.7-4 1·2, 4.7-5, 4.7-7 L12 (a), 4.7-8a) (4) DE-1 인계 갱신(4.7-9) (5) 남은 멈춤 S-OS1(4.7-1a). **v1.12.1 상태(대체됨)**: 검증·gap 반영판 -- 계획 v6.22(`de301d2d`, O-62) 맞춤. **v1.12.1 변경**(독립 검증 B1·M1~M7·N1~N6, gap 분석 `_drafts/evidence/2026-10-21/design_it12_v112_plan_gap.md` G1~G3·I-1~I-3, 오케스트레이터 판정 = gap G1): **W1 규칙 철회** -- `icm_config`가 `as_is_single_input`에서도 `node.dc_window_cfg`를 쓴다(θ 프레임 창과 측정 구성 창은 측정 구성 축이 다른 양 -- 계획 N6.6 범위 1 '어느 쪽도 follower가 아니다'·N3.8 '단일 입력 회로는 회로 그대로가 구성이다'; 옛 W1은 두 정의를 한 필드로 합친 규칙 3 위반), 커널 metric·제약은 모든 구성에서 cfg, `node.dc_window` 값 독자 = 커널 탐색뿐(§4.7-2·§4.7-3b (5)·§4.7-5); G2 DE-1 뒤 선언 제약 = `node.dc_window_cfg`(§4.7-2); M1 `output_structure` = 출력 writer 사슬 뿌리 분류 셋(W4 → `high_impedance`, W3 목표 → `w3_target`, F → `kvl_fixed`), 분류 계산 자리 = `icm_config` 하나(§4.7-3b); M2 `kvl_fixed` 구조는 묶인 반전 입력 포함 입력 포트 전부 cfg 한 칸(§4.7-3b·§4.7-4 2); M3 41:751 근거 없는 문장 삭제, cfg 자기 측정 실패 꼴·출발 창 없는 포트·`unsettled` 출발 창 규칙(§4.7-2·§4.7-4 1); M4·M5·N1 40 §2.4.8 어휘·범위·열 수; M6·I-2 `IcmWindow.config`·`criterion` 사본 칸 삭제 → 포트별 출처 참조 `IcmWindow.sources`(§4.7-5); M7 `IcmConfig.undefined` → metric 경로(`metric_value` quantity 필터, §4.7-5); N2 '(가)' 정리; N3 상태·code 우선순위 definitional > numeric; N6·I-1·I-3·G3 → §4.7-9 DE-1 인계·후속 정정·계획 문언 알림. **멈춤 한 건**(S-7 계획 먼저, §4.7-4 1): `as_is_single_input`에서 다듬은 창 블록의 동작(옛 멈춤 '출발 창'은 W1 철회로 사라짐). 아래는 v1.12 머리: v1.12 **최종안 -- 계획 v6.22(`de301d2d`, 사용자 O-62 병합 승인 2026-10-21, `_drafts/user_decisions.md` O-62 행) 맞춤 완료; design 재검증·사용자 승인 대기**. **v6.22 맞춤(O-61 P1~P6, 계획 v6.22 대기 표시 6곳 해소)**: P1 keep 집합 = `ctx.base` writer ∪ 호출 블록·parent 일치 검사 확장·봉인 4 서로소 단언, `CONTEXT_WRITERS` 이동 항목 삭제(§4.7-3c); P2 창 끝 함수 `saturation_window` 하나·호출 블록 셋(§4.7-3b (4)·§4.7-7 M2·L10 (b)); P3 KVL 고정 포트 정본 칸 = `node.dc_window_cfg` 하나, `graph.icm_config` `kvl` 칸 삭제 → 구조 분류 칸 `output_structure`, 다듬은 창 블록은 그 포트를 쓰지 않음(§4.7-3b·§4.7-4·§4.7-5); P4 고립 입력 포트 = 뿌리 창 절차, F 성분 미선언 포트 = 정의 불능 + 사유(§4.7-3 3); P5 커널 창 미수렴 → `node.dc_window_cfg` 상태 칸으로 이어받아 커널 metric·커널 ICMR 제약 정의 불능(§4.7-3b·§4.7-5); P6 다듬은 창 출발 창 = DE-1 전 `node.dc_window_cfg`(§4.7-4 1). 계획 v6.23 몫(O-62 P10·P11)은 이 판에서 설계하지 않는다. **멈춤 한 건**(S-7 계획 먼저): 측정 구성 `as_is_single_input`의 다듬은 창 출발 창(§4.7-4 1). 아래는 이 판의 앞 초안 머리 문장(계획 v6.20·v6.21 맞춤): v1.12 **초안 -- 계획 v6.20(사용자 O-57 승인본) 맞춤 판**. **독립 검증(evidence/2026-10-20/it12_v112_validation.md) 정정 반영**: C1 다듬은 창 = 두 끝 전압 [min, max]·한 끝 결측이면 창 None(§4.7-2, R1), M1 동작점 불일치 = 커널 마지막 풀이에서 봉인 7·9와 같은 함수·기준, `input_status="op_mismatch"`·code `input_window_operating_point_mismatch`(definitional)(§4.7-3a 3), W1 `off`·`triode` 행 부호·첫 칸, W2 행 원소 5원소 꼴, W3 `saturation_window(…, roots, …) -> (dlo, dhi, slope)` 묶음 인터페이스·끝 풀이 `fixed_values[p]` = 선언값 + Δ, W4 재사용은 graph 규칙(S3 색인 graft)만·새 캐시 없음, parent는 as-built 커널 결과 그대로, 커널 밖 writer 필드의 parent 무효화 규칙 공백은 계획 먼저(§4.7-4 5, K3 단언), W5 `IcmWindow.config` 제거·출력 전용 필드 선언, W6·I1 줄 번호 master `2e707d5d` 재측정, I2 IT-1 삭제 자리 추가; **O-58 반영(2026-10-20, 계획 v6.21 -- 사용자 O-60 승인본 맞춤; Status = 초안, design 재검증 대기)**: S-1~S-3 = 봉인 뒤 블록 `icm_config`·ss 층 필드 `graph.ss_nodal`·세 자리 이전(§4.7-3b), S-4 두 갈래(§4.7-3a 2), T-1 인용(§4.7-3a), O-59 (2) 스냅샷 파생 규칙(§4.7-3c), K3 (b) 문언 'S3 색인 평가 키 부분(as-built `sctx.cache`)'(단일 정본 감사 F2), 40 §2.4.5·42 D-GR1 낡은 인용 정정(F4). 아래는 이 판의 첫 초안 머리 문장: 사용자 결정 O-49 P1~P6(옛 결정 대기 D1~D6)을 결정으로 반영(§4.7-2 기준 칸 `criterion`(P5), §4.7-3 2 감도 음수 포트 [min, max](P2), §4.7-3 3 선언 포트 묶음 훑기(P3, O-53 A-2), §4.7-4 READS에 `node.dc_v` 없음(P1)·(ii) 끝 포화 확인(P6)·층 0 front 후보 호출 자리 = card LA-1 범위 12(P4)), O-54 DC 범위 조건·O-55 U1·V5 창 경계 행(§4.7-3a), O-50 G4·O-52·O-53 A-1 ICMR 측정 구성(§4.7-3b -- 층 순서·소유 card 충돌로 **멈춘 항목 S-1~S-3**, `off` 경계의 EO-1 선행 순서 **S-4**(§4.7-3a 2), 계획 먼저), O-56 EO-1 범위 표시(§4.7-9). 이 판의 옛 초안 문장(계획 v6.19 기준, D1~D6 '결정 대기')은 git 이력(`f10436ea`). 아래는 그 초안의 머리 문장이다 -- card IT-1·IT-2 착수 전 design(옛 기준 계획 v6.19 N6.5·N6.6, S-7 '계획 먼저 → design'; 근거 사용자 결정 B2·K-3, O-13 (1)(2), O-15 (B), O-16 (2), O-19 (2), O-21, O-33 (3), O-34 (1)): §4.6 J-E 입력 DC 정책을 IT-1(W4 입력 뿌리 y 키 = 뿌리 넷, 입력 뿌리 최대 하나·둘 이상이면 정지)과 IT-2(커널 = 선형 감도 끝, 끝 풀이는 수락 반복·front)로 개정, §4.7 신설(입력 포트 창 정본 하나 -- 필드 셋 `node.dc_window`·`node.dc_window_def`(DE-1 예약)·`node.dc_window_def_refined`, 끝 풀이 fail-closed 사유, metric 읽기, card IT-1·IT-2 interface), §6.7-1 v1 문장·§6.7-1a 개정 후 문언(O-13 (1)·IT-Q1 (나), as-built 문단은 history)·§6.7-10 (P4)(P8) card 표시, §9 §6.7-1a test 위치(F-IT4)와 IT-2 test 행, §10 상태 행. 40 v1.12와 같은 변경. 옛 문장은 계획 history H2 'IT-1·IT-2 design' 행. 범위 밖(card DE-1·FX-1 몫)은 §4.7-9. 같은 판 보완(design 검증 '수정 필요'·gap 분석 중 계획 결정과 무관한 항목): helper 범위(`Circuit`·`solve`·`FAILURES`만, 끝 풀이는 `window_refine.py` 비공개), `DeviceCoord(role, relation, partner)`, 호출 배선(`refine_front_windows`·`accept`·`_point_record`·계수), `IcmPort`·`Undefined` 형식·예시, `ls_swing` 새 서명·합치는 규칙, F 성분 미선언 포트·고립 입력 포트, `Window.input_status`(미수렴 = 정의 불능), IT-0 결과 칸, 결정 대기 D1~D6 목록.
>
> v1.11 -- XRUN-F1(사용자 결정 2026-10-15 "권고대로 진행해" X-1·X-2, 40 v1.11과 같은 변경): §5.3.9 '찾기' `local` 반환(늘 보존이라 스냅샷)과 '보존 소유자'를 실행 수명 보존으로(40 §2.4.5), 40 대조 표 §2.4 행 문구. 옛 문장은 history.
>
> v1.10 -- 사용자 결정 2026-10-15 "나로 해"(실행 사이 재사용 제거, 40 v1.10과 같은 변경): mismatch·잡음 tol의 '디스크 캐시 대상' 문구에 LUT 파생표 디스크 캐시 결정(U-87 유지, 사용자 결정 2026-10-15 "U-87은 LUT는 관리복잡도가 없다는 네 판단근거에 따라 유지. 나머지는 기본안대로") 표시. 경위는 history.
>
> v1.9.4 -- 사용자 결정 2026-10-15 "1안·3안 진행하고 ③ 기준 변경도 승인해"(원문 `_drafts/user_decisions.md` 'NFR-4 BLAS 결정성')의 3안: §5.13 신설 -- 판정 경계 위에 일부러 놓는 점의 규칙(BP1 닫힌 식 배치 + 판정 쪽 √ε 여유, BP2 판정 c ≥ 0 그대로, BP3 자기 판정식 확인), 층 0 끌어올림 식, 같은 종류 자리 목록, 검토한 안((a)·(a2)·(b)·(c))과 측정, 남은 위험(풀이기 잡음이 가르는 탐색 경로 -- pushpull의 스레드 간 결정 차이는 이 규칙으로 없어지지 않는다), 끌어올림 식 가장자리와 Q-N9(사용자 결정 2026-10-15 "기본안대로 진행해"로 확정: s = max(0, ·)), `iv_matching_l.py:99` 해당 없음 확인. 같은 날 독립 검증 지적 반영(B-2·N1·N9·N10, 규칙 이름 B → BP, 41 §6의 'B3'와 겹침 회피). 1안·③은 40 §2.4.3·§2.4.13(40 v1.9.4와 같은 변경). 경위·측정 조건은 history.
>
> v1.9.1 -- U17 ①-b 착수 전 as-built 실측 정정(오케스트레이터 기본안 2026-10-13 U17 ①-b D1~D10, 사용자 결정 아님, 40 v1.9.1과 같은 정정): §6.1-9 `graph/start: rungs` = as-built `StartIntervals.ladder`, `placement`는 U17 ②(U15 `placer`와 함께, as-built MOD8 `Placement`와 다른 것), §6.7 KVL 기록은 U17 ②에서 `records`에 더함, §7.5 `noise_inputs`는 U17 ②(β·C_eff 계산과 함께). 경위는 history.
>
> v1.8.1 -- U17 ①-d 실측에 문구를 맞춘 정정(사용자 결정 변경 아님): §1.5-4 측정 의무 (2)·§9 표 '혼재 노드 구동 종류' 행의 folded M8 "해제" → "시작 셀 아님 유지"(base에서도 시작 셀 = M1, M2), 허용 변화 = Vg10 극점 노드 drive voltage → current 하나. 경위는 history.
>
> v1.8 -- §1.5-4 혼재 노드 C-1 보완 (가)(source 쪽 follower 먼저, 예상 집합에 folded_cascode Vg10 추가·sf N17·N20 유지, 측정 의무 3개)와 §9 표 해당 행(사용자 결정 2026-10-12 "1, 가로 해", 계획 v6.7). 경위는 history.
>
> v1.7 -- §4.5 DOF 등식 목록에서 `budget_ref` 제거(사용자 결정 2026-10-12 "다로 해", 계획 v6.6 DEC-55). v1.6 §5 (+ 사용자 결정 2026-10-12 L-3·L-11·L-12·graph 저장 반영, §4.2 층 0 정의역 상한 추가) 계획 복귀 개정(사용자 결정 2026-10-12 "A1~A6은 계획대로 되돌려", "L1~L13 모두 권고대로 해", 재검증 반영, L-14 결정 -- 사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): 층 0 국소 후보를 DEC-71 (4) 역산 우선으로 되돌리고(gm/ID·L 역산, VDS 배분, 국소 고정점), bin을 목표로, LR5 knee·동치류 격자, `comp_approx_gap` 정의를 넣었다. 나머지 절은 v1.5 그대로다.
>
> **v1.6(2026-10-12, 사용자 결정 "9번 권고대로"·"B는 권고대로"·"K-1~K-3도 권고대로")**: §6.7 KVL 고리 출발 제약(쓰기 계획의 v2 고리 등식·VDS-1 포화 부등식, 묶인 소자 구간 안 공동 선택 + 매크로·면적 재확인, 해 없으면 충돌 레코드, 층 0 역산·VDS 배분과의 관계, DEC-64 v1 을 계획대로 제약 없음으로 하는 커널 쓰기 계획 개정 §6.7-1a) 추가, §6.1 순서 7a·8, §6.6 충돌 종류, §7.5 β·C_eff 입력 배선(design 검증 뒤 사용자 승인 대상). 계획과의 차이는 §6.7-10(P5·P8은 K-1·K-3으로 닫힘, P7은 K-2 조건부 승인, P1 남음). P-1·P-9·P-15(§5.1·§5.3.11·§9), C-2(§7, 파일럿 kT/C 미선언)도 이 판에 반영했다.
>
> v1.5(2026-10-08). 사용자 결정 2026-10-08 "j해석은 네의견에 모두 동의해."(J 공동분석, 근거 `_drafts/engine/J_joint_analysis_2026-10-08.md`)를 반영했다.
> - §1.12 구조 규칙 6개 추가: 복합 diode D1, feedforward 셀, 중첩 Miller 보상 내부 루프, 루프 극성 = DC 사이클 극성, L 주인 `main_path_signal`, 뷰 한정 교류접지 예외
> - §1.13 회로별 실측·기대 표 추가
> - §1.2·§1.4·§1.6·§1.8·§1.9·§2·§4.3·§4.6(입력 DC 정책 SP-2 (c)·짧은 L bin 경고)·§5.1·§6.5·§8·§9 갱신
>
> v1.4는 사용자 결정 2026-10-08 "q3,q4는 네 제안대로 해"(Q3 offset·미러비, Q4 스윙·ICMR)를 반영했다: §6.4-2 mismatch 모델을 유효 계수 A_eff(LUT 감도 열, bin별 slope)로 대체, §6.4-2a offset 구조 가드, §6.2 스윙·ICMR 예산 분할, §4.6 헤드룸 달성가능성 보고. 근거 `_drafts/engine/matching_swing_spec_proposal.md`. v1.3은 사용자 결정 2026-10-08 "Q1~Q11 모두 네 의견대로 진행해"를 반영했다(R29 knee 추가 후보, Q2 Pelgrom 출처, Q5b 판정 보류 탐색, Q11 잡음 값과 metric). v1.2의 변경은 다음 셋이다.
> - 재검증 지적 N1~N9와 Low 항목 반영
> - 잡음 경로 추가(§7, 사용자 결정 2026-10-08)
> - v1.1에서 반영한 C1~C4·H1~H8·M1~M14·L1~L8 유지
>
> 색인과 표기는 [40-engine](gain-budget-gmid-sizing.40-engine.design.md)을 따른다(`E/`, OK/DEV/PART/MISS). as-built 기준은 master `004b7d2`다.

**as-built 요약**: 이 문서의 설계 항목은 모두 MISS다. 쓸 수 있는 재료는 다음이 전부다.
- LUT 곡선 표의 격자 최대 gm/gds: `CurveRow.gm_gds_max`(`E/lut/lut_types.py:384,396`)
- LUT 곡선 검사: `curve_report`, `DcSlice.hermite_fc`(`E/lut/lut_set.py:124-173`)
- 전회로 MNA: `E/metrics/mna_build.py:47`, `mna_solve.py:42`
- pencil 극점: `E/metrics/pencil_roots.py`
- 외층 ε-제약 front: `E/search/eps_sweep.py`, `pareto.py`
- 최소형 층 0: `E/search/layer0_center.py`(시작점 하나만 만든다)

---

## 0. 계산 순서 DAG (S0당 한 번, 순환 없음)

P N3.1의 'GB0~GB4는 S0 지문마다 한 번'에 맞춘 순서다. 앞 단계는 뒤 단계 결과를 읽지 않는다.

```
[단계 A -- 봉인 평가 없이, S0당 1회]
 A1 GB0 load            : spec, topology, S0
 A2 GB1 build_s1        : S1
 A3 GB2 build_s1v       : S1v (뷰·셀·stage·블록·극점 노드·루프)        §1
 A4 GB3 coupling_vars   : y 목록, 기둥↔블록 매핑                        40 §3.3
 A5 GB4a curve_checks   : LUT 칸 분류(역산 허용/격자 전용/거부)          §4.1
 A6 GB4b block_bounds   : A_i,max 표(LUT 격자 전수, 인증 또는 미상)      §4.2
 A7 GB4c verdict        : Σ A_i,max 판정, 구조 DOF, 인증된 면적 하한,    §4.3~4.6
                          헤드룸 창 상한(스윙·ICMR·버퍼)
 A8 start_intervals     : gm/ID·L·I 출발 구간, 7a KVL 고리 선택, 사다리(A3·A6, S0 쓰기 계획 `graph/kernel`, LUT를 읽는다) §6
 A9 block_bounds_l0     : 층 0 정의역 상한 A_i,max^L0(A6 국소 모델 + A8 S0 필드 `start.row`·`start.point`, 사용자 결정 L-12, '추정') §4.2
[단계 B -- 봉인 평가가 필요, S0당 1회, 평가 커널 컨텍스트 생성 뒤]
 B1 residual_probe      : 결합 잔차 분포 r̂ (표본 = dof_rank_sample_count) §2.4
 B2 dof_numeric         : 수치 rank (B1 표본 재사용)                     §4.5
 B3 layer0_budget       : 국소 front → 조합 DP → 조립(A6·A8·A9·B1을 읽는다) §5
[단계 C -- 탐색]
 C1 find_front(외층 ε-제약) → MOD8 → 오라클                              40 §3.6, §3.9, §4
```

순환을 끊는 규칙은 넷이다.
- 단계 A는 봉인된 값을 읽지 않는다.
- A7 판정은 r̂를 쓰지 않는다. A7의 면적 하한도 A8 출발값을 쓰지 않는다(§4.4).
- A8이 읽는 A_i,max가 미상이면, 그 블록의 이득 L 하한만 비활성으로 둔다(§6.4).
- 단계 B의 결과는 단계 A로 되돌아가지 않는다.

**미측정 값의 처리 규칙(하나로 통일)**: 모델 오차, r̂, 분해능처럼 아직 재지 않은 값은 '보류'로 둔다. 보류 값을 쓰는 결정은 거부·정지를 하지 않는다. 그 값을 거친 산출물(front, 순서, bin)에는 '추정'을 표시한다(DEC-72·77).

**예산은 두 종류이고 서로 섞지 않는다**(N1·N4):

- **계수 예산 N_S**(단계 A와 DP 상태 수에 씀)
  - 시간에 의존하지 않고 S0에서 계산한다. 같은 S0이면 결과가 늘 같다(결정론).
  - **기본값**: N_S = 이 회로에 쓰이는 kind들의 LUT 격자점 수 합 = Σ_kind |VGS|·|VDS|·|VS|·|L|·|W 슬라이스|. 근거는 "상한 계산 한 번이 LUT 전체를 한 번 훑는 양을 넘지 않는다"이다. LUT 파일에서 정해지므로 새 상수가 아니다.
  - **선언값**: spec human `structure_count_budget{value, source}`가 선언되면 기본값 대신 그 값을 쓴다. 이 값은 S0 지문에 들어간다.
  - **적용 대상**:
    - GB4 블록 격자 곱 Π(§4.2), 복합 블록 Π(§1.9): N_S를 넘으면 그 상한은 '미상'이다.
    - 사이클 열거(§1.8): N_S를 넘으면 정지한다.
    - 조합 DP 상태 수(§5.6): N_S를 넘으면 DEC-80 게이트로 bin 폭을 넓힌다.
- **시간 예산 N_T**(단계 B·C의 평가 커널 호출 수에 씀)
  - DEC-34 식으로 정한다(§5.8).
  - 단계 A는 커널을 부르지 않으므로 N_T를 쓰지 않는다.

---

## 1. FR-1 -- signal stage 유도 SP1 (GB2, MOD3)

**목적**: connectivity만으로 여기 뷰마다 셀, 구동 종류, stage, 블록, 극점 노드, 루프를 유도한다. declared와 다르면 `review_needed`로 올린다(DEC-43·44). 규칙 정본은 P N3.2 1~9와 용어집이다. 이 절은 그 규칙을 실행 순서와 알고리즘으로 정한다(WP-21 코드 부류).

**출력**: S1v의 필드 `views[]`이다. 각 뷰는 `{kind, excite, sense, ac_ground, signal_nets, forward_nets, cells{dev: CS|CG|CD|pass|diode_load|off}, drive_kind{net}, dist{net}, blocks[], pole_nodes[], loops[], cuts[]}`를 갖는다. 여기에 `rule_branch_coverage`와 `review_needed[]`가 붙는다.

**파일**(`E/graph/`, 계산 블록 하나 = 파일 하나):

| 파일 | 내용 |
|---|---|
| `views.py` | 뷰 수집 |
| `ac_ground_view.py` | 뷰별 교류접지 |
| `signal_reach.py` | 도달성·순방향 집합 |
| `cells.py` | 셀 분류 |
| `drive_kind.py` | 입력 노드 구동 종류 |
| `stage_bfs.py` | 0-1 BFS, stage 경계 |
| `blocks.py` | 블록 구성 |
| `pole_nodes.py` | 극점 노드 목록 |
| `loops.py`, `loop_classify.py`, `loop_cuts.py`, `polarity.py` | 루프 탐지·분류·끊는 점·극성 |
| `buffer_bundles.py`, `output_direction.py`, `composite_blocks.py` | 버퍼 묶음, 출력 방향, 복합 블록 |
| `declared_compare.py`, `rule_coverage.py` | declared 대조, 규칙 분기 발동표 |
| `s1v_build.py` | 진입점 |

### 1.1 뷰 수집

- **전달 뷰**: 선언된 metric의 `(ac_excite, sense)`마다 하나씩 만든다.
- **기본 전달 뷰**: metric 선언이 없으면 `ports` role에서 만든다. 두 입력 포트가 자기동형 궤도(40 §6)에서 서로 대응하면 기모드 여기 하나, 아니면 입력마다 단일 여기 하나다.
- **루프 뷰**: §1.8의 (3) 루프마다 하나씩 만든다.
- 전류 입력·트랜스임피던스 뷰는 DEC-59에 따라 정지한다.
- `(excite, sense)` 키는 as-built `E/authoring/spec_views.py:61,110`의 것을 그대로 쓴다.

### 1.2 뷰별 교류접지

정적 집합 (1) 레일과 (2) gate 전용 넷은 as-built가 이미 계산한다(`E/graph/ac_ground_static.py`).

**(4) 바이어스 종속 넷 술어**(P N3.2-1 (0)~(iii)): 넷 b에 대해 다음을 확인한다.
- 사슬 찾기: b를 제거한 신호 그래프에서 source→drain 역방향 BFS로 사슬을 찾는다. 교류접지와 b는 지나지 않는다.
- 판정: 그 뷰의 여기가 사슬의 출발 신호 노드를 움직이지 않으면 b는 교류접지다.
- 움직이는 경우: b는 교류접지가 아니고, 그 사슬이 만드는 폐경로를 (3) 루프로 등록한다.

이상 전압원 (3)은 as-built처럼 정지한다(발동 0, DEC-76). 실측 기대는 파일럿 2건, 나머지 8회로 무동작이다(J1).

**뷰 한정 예외**(J-C): 위 판정 뒤 ratified `ac_ground_exception` 사실이 지정한 뷰에서만 그 넷을 교류접지로 둔다(§1.12.6).

### 1.3 도달성과 순방향 집합

최소 고정점으로 신호 넷을 모은다. 여기 포트에서 시작해 다음 세 규칙을 반복한다. 교류접지 넷과 제거된 넷은 넣지 않는다.
- (a) 신호 넷을 gate로 받는 소자의 drain·source를 넣는다.
- (b) 신호 넷을 source로 받는 소자의 drain을 넣는다.
- (c) 신호 넷에 붙은 2단자 수동소자의 반대쪽 단자를 넣는다.

**순방향 집합 F**는 이 그래프에서 여기 포트로부터 도달하고 출력 포트로 역도달하는 넷의 집합이다.

### 1.4 셀 분류

1. **gate = drain**이면 `diode_load`다. 복합 diode 묶음(§1.12.1)의 MOS 멤버도 `diode_load`다.
2. **gate가 신호 넷**인 경우:
   - drain이 교류접지면 CD, source가 교류접지면 CS다.
   - 둘 다 아니면 source가 F 위의 다른 신호 셀 입력이나 출력 포트에 닿는지 본다. 닿으면 `review_needed`, 아니면 CS(degeneration)다.
   - 상대 셀도 모호하면 그 쌍을 함께 `review_needed`로 올린다.
3. **gate가 신호 경로 밖**인 경우:
   - 역병렬 pass 묶음 조건을 만족하면 pass다.
   - 아니고 source가 신호 넷이면 CG다.
   - 그 밖은 `off`다.
   - 소자가 셋 이상이거나 방향이 섞인 묶음은 `review_needed`다.

대조표 셀 수는 출력이 F에 드는 셀만 센다. 빠진 셀은 '순방향 밖 셀' 열에 적는다.

### 1.5 입력 노드 구동 종류

1. 신호가 drain으로 들어오면 전류 구동이다. source, 입력 포트, 앞 stage 출력으로 들어오면 전압 구동이다.
2. 저항으로만 들어오면 반대쪽 노드의 종류를 상속하고 '값 의존'으로 표시한다. 상속이 순환하면 `review_needed`다.
3. 전류 진입 노드는 신호가 나가는 쪽으로 가른다.
   - gate로만 나가면 전압 구동이다.
   - 채널로만 나가면 전류 구동이다.
   - 둘 다면 gate 쪽 셀의 출력이 F 위에 있을 때 전압 구동(stage 경계)이다. 그렇지 않으면 그 노드는 **tap**이다. tap은 채널 쪽만 순방향을 잇는 노드다. 구동 종류는 '전류 구동'으로 기록하고, gate로 갈라진 셀은 규칙 9 (a)(`기록만`, DEC-59 정지)로 둔다.
4. **혼재**(한 소자의 drain과 다른 소자의 source가 만나는 노드)는 두 단계로 가른다(C-1, 사용자 결정 2026-10-12 "7절 권고대로", 보완 (가) 사용자 결정 2026-10-12 "1, 가로 해". 회로·소자 이름을 쓰지 않는 구조 규칙).
   - **(i) source 쪽 소자를 먼저 본다**: 그 소자의 drain이 교류 접지(레일)이고 gate가 그 뷰의 신호 노드(순방향 신호 경로 위 넷, §1.3)이면 source follower(CD)다. 그 노드는 **전압 구동**이다.
   - **(ii) 아니면(CG/cascode) drain 쪽 소자를 본다**(기존 C-1): drain 쪽 소자의 gate가 그 뷰의 신호 노드이면 **전류 구동**이다. 그 소자가 신호 전류를 그 노드로 밀어 넣기 때문이다. 그 gate가 신호 노드가 아니면(교류접지이거나 신호가 닿지 않는 바이어스 넷) 전압 구동이다. 그 소자는 그 뷰에서 고정 전류원이다.
   - **대체하는 규칙**: 옛 규칙 4 'drain 쪽 소자의 DC 역할로 가른다(바이어스 전류원 → 전압 구동, 신호 소자 → `review_needed`, 못 가르면 J 대기)'를 통째로 바꾼다. DC 역할은 뷰와 무관한 S1 사실이라 AC 신호 진입을 가르지 못했다. 바뀐 규칙은 뷰마다 신호 노드 집합(§1.3)과 교류 접지(§1.2)만 읽는다.
   - **예상 집합**(판정이 바뀌는 노드): `sf_pushpull_output_opamp` N910·N1112·N1516 → 전류 구동, `folded_cascode` Vg10 → 전류 구동(미러 출력 M10 → cascode M8, 옛 판정 오판). 유지: `sf_pushpull_output_opamp` N17·N20 = 전압 구동((i) follower M18·M19). 나머지 회로는 무동작이다. 40 §3.2-3 사실 표의 sf `drive_kind` override는 필요 없다.
   - **측정 의무**(구현 DoD): (1) 9 library 회로 발동표(뷰마다 혼재 노드, 옛 판정, 새 판정, 근거 `follower` | `cascode`). (2) `folded_cascode` 전후 비교 = 기록 + 판정 하나: Vg10이 전류 구동이 되고 M8이 stage 시작 셀이 아님(§1.6 규칙)이 유지됨을 확인한다(base에서도 M8은 시작 셀이 아니었다 -- stage 시작 셀 = M1, M2. ①-d 실측). 그 밖의 블록·stage·극점 노드 변화는 기록하고, Vg10 극점 노드 drive(voltage → current) 변화 밖이면 멈추고 보고한다. ①-d 실측: 변화는 Vg10 극점 노드 drive voltage → current 하나, 블록·stage는 9회로 불변. (3) 비교 키 = (회로, `view_key`, 노드). 예상 집합의 노드는 **그 노드가 혼재로 판정되는 모든 뷰에서** 판정이 바뀌어야 한다. 일부 뷰에서만 바뀌거나 예상 밖 (회로, 뷰, 노드)가 바뀌면(그 밖의 회로 무동작, WP-05) 구현을 멈추고 보고한다(§9 표 '혼재 노드 구동 종류' 행).
5. pass 묶음을 지난 노드는 반대편 노드의 종류를 상속한다.

### 1.6 0-1 BFS와 stage 경계

**엣지 비용**:

| 엣지 | 비용 | 비고 |
|---|---|---|
| gate→drain | 1 | gate가 diode 단자면 0 |
| source→drain, gate→source | 0 | source가 전압 구동인 CG의 source→drain은 1 |
| 수동소자 | 0 | 열린 항목 ⑬ |

**stage 시작 셀**: 입력이 전압 구동인 CS, 그리고 source가 전압 구동인 CG다. 단 DC 역할이 바이어스 전류원인 셀은 stage를 시작하지 않는다(K8).

**diode 단자**: 위 표와 규칙 9 (c)의 'diode 단자'는 단순 diode와 복합 diode(§1.12.1) 소자의 gate 넷이다.

**적용 순서**(⑧): 규칙 9 (c)의 diode 미러 갈래를 stage 시작보다 먼저 적용한다. 미러 입력 노드는 블록 내부 노드이므로, 그 노드를 gate로 읽는 셀은 stage를 시작하지 않는다. 근거는 P N3.2-5와 J2 기본안이다.

### 1.7 블록, 출력노드, 임피던스 등급, 극점 노드

1. **블록 열기**: 시작 셀마다 블록을 연다. 캐스코드 사슬, 미러 연장, pass 묶음을 따라가 다음 시작 셀 입력이나 출력 포트에 닿은 노드가 출력노드다.
2. **병렬 합류**: P N3.7의 ①②③ 순서로 판정한다. 세 갈래 이상이면 입력 쌍마다 ①을 적용하고 union-find로 묶는다(⑪).
3. **차동 블록**(⑩·M5): 같은 stage 번호의 반쪽 블록 둘이 넷을 공유하면 하나로 합친다.
   - 블록 키: 출력노드 넷 이름의 정렬된 배열이다. 단일 출력 블록은 원소 1개, 차동 블록은 원소 2개다. 구분자로 이은 문자열을 쓰지 않는 이유는 넷 이름에 어떤 문자가 들어 있어도 키가 모호해지지 않게 하기 위해서다. JSON에서는 배열로 쓴다.
   - 여기: 두 입력 넷에 ±½를 건다.
   - 출력: 두 출력노드 전압 차다.
   - 노드 배타성은 합친 뒤에 검사한다.
4. **임피던스 등급**:
   - 낮음: source 단자나 diode가 붙은 노드. 출력 임피던스는 입력 신호를 0으로 놓고 보므로, gate가 교류접지이든 앞단이 구동하든(follower) source를 들여다보면 1/gm 차수다. pass 묶음 소자의 단자는 등급에 기여하지 않는다(pass 끝 노드는 반대편 종류를 상속, §1.6-5). Block.impedance와 극점 노드 등급은 이 한 규칙을 함께 쓴다(같은 뷰에서 등급이 둘이면 결함, U1 red test 1). 2026-10-08 정정: 옛 문구 "gate가 교류접지인 source 단자"는 follower 출력을 높음으로 만들어 물리와 어긋났다.
   - 높음: drain, gate, 커패시터 단자만 붙은 노드.
   - 값 의존: 낮음 단자 없이 저항이 붙은 노드.
   - 규칙 9 (c)는 블록 구성 뒤, 출력노드가 F 위에 있을 때만 본다.
5. **극점 노드 목록**: 교류접지가 아닌 모든 노드다. 노드마다 소속 블록, 등급, 종류를 붙인다.
6. **DEC-59 정지 집계**: 비축약 뷰에서 센다(⑨). 축약 뷰와 비축약 뷰의 결과가 같아야 한다.

### 1.8 루프

**탐지**: P N3.2-2 방향 그래프에서 단순 사이클을 전수 열거한다(Johnson, 정렬된 노드 순서). 세지 않는 것은 수동소자 왕복, pass 묶음 내부 왕복, 자기 엣지다.

**열거 상한**: 계수 예산 N_S다(§0). 시간과 무관하다. 넘으면 `StructureUnresolvedError(unsupported_rule_branch, reason=cycle_enumeration_over_budget)`로 정지한다(M14).

**분류**: (1.5) 바이어스 SCC → (1.6) 복합 diode 내부(§1.12.1) → (2) Miller → (3-a) → (3-b) → (4) 순서로 판정한다. 정의는 P N3.2-2를 따른다. (2)와 (3-b)를 함께 만족하면 두 분류를 모두 단다. (3-b)는 배타 조건 (가)·(나)를 적용하고, (나)는 복합 diode 묶음 밖의 루프에만 남는다. (2)·(3-b) 루프가 §1.12.3 조건을 만족하면 루프 뷰를 만들지 않는다(`compensation_internal`).

**끊는 점**: 루프 위에 gate 엣지가 있는 CS 셀의 gate다.
- 후보가 여럿이면 복귀 경로 다음 첫 gate를 고른다.
- 복귀 구간이 여럿이면, 이름 정렬로 첫 노드에서 시작한 사이클 표현의 가장 이른 구간을 쓴다.
- 후보가 없으면 `review_needed`다.

**극성**: §1.12.4(J-F). 사이클 극성은 커패시터를 지나지 않으면 셀 부호의 곱(CS −, 그 밖 +)이고, 지나면 `ac_only`(info)다. 루프 뷰 극성 = 그 뷰의 DC 사이클 극성이다.

**U-24 게이트와 CM 루프의 구조적 대응**(H5): 루프 뷰 ℓ의 사이클 노드 집합이 **선언된 차동 출력 포트쌍(role p/n)의 두 넷을 모두** 포함하면, ℓ을 '포트쌍 CM 루프 대응'으로 본다.
- 근거: 포트쌍에 같은 부호로 주입하면 두 출력 넷을 함께 지나는 모든 CM 되먹임 경로가 한 번에 열린다.
- 그 ℓ의 안정도 metric은 40 §5의 `pm_cm_ss_deg`다.
- U-24 정지 대신 사용자 결정(2026-10-08)을 따른다. 제약이 미선언이면 T_cm만 보고하고, T_cm(0) > 1이면 경고 `cm_loop_unconstrained`를 낸다.
- 그 밖의 루프 뷰는 안정도 제약이 미선언이면 GB2 출구에서 `StructureUnresolvedError(undeclared_loop_constraint)`로 정지한다.
- '선언'은 spec 루프 뷰 선언(`ViewDecl` kind loop의 끊는 넷)이 안정도 제약 행에 쓰인 것이다. 단계 A 진입점이 그 끊는 넷 목록을 `build_s1v(declared_loop_cuts=...)`로 넘긴다(40 §3.2-3 파이프라인 수정. `[u1-sp1]` `pipeline/stage_a.py`는 넘기지 않아 선언해도 정지가 풀리지 않는다).

### 1.9 버퍼 묶음, 출력 방향, 복합 블록

- **R(u)**(DEC-63): CD 병렬 합류(②)에서는 §1.7의 ①보다 먼저 판정한다.
- **출력 방향**(DEC-65): β/σ/κ와 push-pull·class-A 구분은 MOD3에서 구조로 판정한다. 값은 40 §3.8 `ls`가 낸다.
- **feedforward 분리**(§1.12.2, J-A): 복합 블록 판정 전에 FF 묶음을 주경로 블록 구성에서 뺀다. FF 합류는 복합 블록으로 묶지 않는다.
- **복합 블록**(DEC-81): ②의 합류 노드가 전류 구동이거나 블록 출력노드면 묶는다. 묶은 결과 DAG는 사슬이어야 한다.
  - 묶음 크기 Π가 N_S를 넘으면 `unsupported_rule_branch`다. Π는 §4.2의 축 정의로 센 격자 곱이다. 계획 DEC-81은 'DEC-34 예산 식의 평가 수'를 쓴다. N_S로 두는 것은 L-10과 같은 이유(결정론, NFR-4)의 **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로")(U-65, 계획 DEC-81 정정)이다(§5.12.3 D5).
  - 경로별 기여는 §2에서 계산한다(⑭).

### 1.10 declared 대조와 발동표

- **declared 대조**: declared stage(`compensation.stage_devices`, `gain_stages_sum.stages`, `vertical_stack_id`)는 `declared` 엣지로만 싣고 유도 결과와 대조한다. 불일치면 `review_needed`다. 유도 입력으로는 쓰지 않는다(U-50).
- **발동표**(R7, 축소 유지 승인 2026-10-08): `rule_branch_coverage.json` 파일은 만들지 않는다. 대신 다음은 유지한다.
  - `기록만` 분기를 탈 때의 `unsupported_rule_branch` 정지(exit 2).
  - J ratify 전에 걸리는 `review_needed` 정지(DEC-59 안전망).
  - 분기 발동 사실을 S1v `review_needed[]`와 결과 JSON에 기록하는 일.

### 1.11 6a 열린 항목 결정

| 항목 | 결정 |
|---|---|
| ① | as-built `gvgs_cycles` |
| ② | R(u)를 먼저 판정 |
| ③ | 구조로 못 가르는 DC 역할 그룹은 잠정 신호 소자로 두고, 블록에 `review_needed`를 붙여 GB4 앞에서 정지. 2026-10-08 J: 복합 diode(§1.12.1)로 구조가 풀리는 그룹은 규칙으로 가르고, 남는 그룹만 ratified `dc_role` 사실(40 §3.2-3)로 정한다 |
| ④ | diode source 진입은 전압 구동으로 보고, diode 자체는 `diode_load` |
| ⑤ | 40 §3.5 |
| ⑧ | §1.6 |
| ⑨·⑩·⑪ | §1.7 |
| ⑫ | as-built |
| ⑬ | §1.6 |
| ⑭ | §1.9 |
| ⑥ | 구현 출력으로 갱신 |
| ⑮ | 사용자(40 §9 Q7) |

**불변식**: 같은 입력이면 같은 S1v다. 이름을 전단사로 바꾸면 결과는 그 사상으로만 바뀐다. 축약 뷰와 비축약 뷰의 결과가 같다.

**실패**: `StructureUnresolvedError`.

**상태**: MISS. 부분 대리물은 `E/authoring/_feedback_cuts.py:11`, `E/metrics/loop_cut.py:60`, `[ng-cmfb-pm] E/authoring/cm_partition.py`, `E/graph/matching_groups.py:202`다. SP1 본체는 `[u1-sp1]`(eae0292, 미병합)에 있다.

### 1.12 J 공동분석 구조 규칙 (사용자 결정 2026-10-08 "j해석은 네의견에 모두 동의해.")

**근거**: `_drafts/engine/J_joint_analysis_2026-10-08.md`(SP1 9회로 실측, `[u1-sp1]` 7c757e8, `s1v_rule_fp` e6c195f2…1aef). 결정 전문은 `_drafts/user_decisions.md` 마지막 항목이다.

**이름 규칙**: 아래 1.12.1~1.12.5는 구조 규칙이다. 회로·소자·넷 이름을 쓰지 않는다(EP-1). 회로별 산출은 §1.13 실측 표와 40 §3.2-3 사실 표에만 적는다.

**배선 원칙**: 각 규칙은 '소비' 항목에 적은 기존 계산 경로를 대체한다. 소비처가 없는 규칙은 두지 않는다.

#### 1.12.1 복합 diode (D1) -- DC 역할·미러 인식·루프 분류의 공통 입력

**정의**(S1, connectivity만 쓴다). MOS X의 gate 넷을 g, drain 넷을 d라 하고 'DC 가지 걷기'를 한다.
- 출발: w = d.
- 단계마다:
  - w = g이면 성공이다.
  - 아니면 w가 다음 두 조건을 모두 만족해야 한다. (i) 레일·포트·이상원 단자 넷이 아니다. (ii) w에 붙은 **DC 전류 단자**가 정확히 둘이다(직렬 노드). DC 전류 단자는 MOS 채널 단자(d·s)와 2단자 저항 단자다. gate와 커패시터 단자는 세지 않는다.
  - 두 조건을 만족하면 방금 들어온 단자가 아닌 쪽 단자의 원소를 지나 그 반대쪽 넷으로 간다.
  - 만족하지 않거나 이미 지난 넷에 다시 오면 실패다.
- 지난 원소가 하나 이상이고 성공하면 X는 **복합 diode 소자**다. gate = drain인 단순 diode(지난 원소 0)는 기존 규칙 1 그대로다.
- 걸음 수는 원소 수를 넘지 않으므로 따로 상한을 두지 않는다.

**묶음**: 복합 diode 소자 X와 그 걷기가 지난 원소(MOS·저항, 지나간 단순 diode 포함)가 한 묶음이다. 걷기가 원소를 공유하는 묶음은 합친다(union-find).

**묶음 안 역할**: 다른 복합 diode 소자의 걷기에 들지 않는 복합 diode 소자가 **기준**(`diode_reference_composite`)이다. 나머지 복합 diode 소자는 **캐스코드 기준 멤버**(`diode_reference_composite_cascode`)다. 지나간 단순 diode와 저항은 묶음 멤버로만 기록한다.

**소비**(배선 세 곳 -- 같은 묶음 레코드를 읽는다):
1. **DC 역할**(`E/graph/dc_roles.py` 규칙 1 확장, S1).
   - 복합 diode 소자는 diode 기준 역할이다(evidence rule `1c`, 하위 구분 composite / composite_cascode).
   - 그러면 규칙 2의 gs 묶음이 '기준이 있는 묶음'이 되어, 같은 gate·source 묶음의 나머지 멤버는 바이어스 전류원으로 갈린다. 이것이 J-U3-c '구조로 못 가르는 그룹'을 구조로 푸는 경로다.
   - L 동치류 주인 규칙 2(`current_source_member`)는 diode 기준을 읽으므로 이 기준을 그대로 고른다.
2. **미러 인식**(`E/graph/drive_kind.py` `_mirror_inputs`, 규칙 9 (c)·⑧, S1v).
   - '미러 입력 넷' 판정의 'diode 연결 단자'를 '단순 diode 또는 복합 diode 소자의 gate 넷'으로 넓힌다.
   - 그 넷을 gate로 읽는 다른 순방향 셀이 있으면 그 넷은 미러 입력(블록 내부 노드)이다. 그 셀은 stage를 시작하지 않고, 블록은 미러 출력 쪽으로 이어진다.
   - §1.6 엣지 비용의 'gate가 diode 단자면 0'도 같은 넓힌 정의를 쓴다.
   - 셀 분류(§1.4-1): 복합 diode 묶음의 MOS 멤버는 `diode_load`로 분류한다. 묶음 전체가 진입 넷에 걸린 diode 부하 하나(1/gm_eff)이기 때문이다. 묶음 내부 넷은 블록 내부 노드이고 구동 종류 혼재 판정(§1.5-4) 대상이 아니다.
3. **루프 분류**(`E/graph/loop_classify.py`, §1.8).
   - 분류 순서에 **(1.6) 복합 diode 내부 루프**를 (1.5) 바이어스 SCC 바로 뒤, (2) Miller 앞에 둔다.
   - 판정: 사이클의 모든 원소(엣지의 MOS·수동소자)가 한 복합 diode 묶음 안에 있으면, DC 국소 루프로 기록하고(`composite_diode_internal`, info) 루프 뷰를 만들지 않는다.
   - 이 규칙이 계획 N3.2-2 (3-b) 배타 조건 (나)('수동소자 없는 2능동셀 루프 → `기록만`')와 '국소 되먹임 조건 발동 0' 보류를 닫는다. (나)는 복합 diode 묶음 **밖**의 2능동셀 루프에만 남는다.

**바뀌지 않는 것**:
- 단순 diode 규칙 1과 J1 술어(§1.2)는 그대로다.
- 복합 diode 기준 가지에 흐르는 전류가 차동쌍 공통 source 넷에서 빠지는 것(레플리카 전류 분할)은 KCL이 이미 다룬다. GB7 꼬리 전류 예산에서 유효 꼬리 전류 = Σ 꼬리 공급 − Σ 레플리카 가지 전류다(새 코드 없음, U1b test로 확인).

#### 1.12.2 feedforward 셀 (J-A)

전달 뷰마다 블록 구성(§1.7) 뒤, 복합 블록(§1.9) 앞에서 판정한다.

1. **주경로**
   - G_f: 그 뷰 순방향 넷 F 위의 능동 셀 엣지만으로 만든 그래프다(§1.6 비용, 수동소자 엣지 제외). SCC는 응축한다.
   - D_max(n): 뷰 입력에서 n까지의 **최대** 비용, 즉 지나는 stage 시작 수의 최댓값이다. §1.6의 0-1 BFS(최소 비용)와 다른 양이다.
   - slack(e = u→v) = D_max(v) − D_max(u) − cost(e) ≥ 0.
   - **주경로 셀**: 뷰 입력에서 감지 출력까지 slack 0 엣지만으로 이어진 경로 위에 있는 셀이다.
   - **주경로 블록**: 그 셀들로 다시 구성한 블록이다(아래 3).
2. **feedforward 묶음**
   - FF 진입 엣지: 주경로가 아닌 신호 셀 c가 주경로 넷 m으로 들어오는 엣지이고 slack > 0인 것.
   - **합류 노드 조건**: m은 주경로 **블록 출력노드**여야 한다. 이 조건이 측면 주입(K8, 블록 내부 노드로 들어옴)과 feedforward를 가른다.
   - FF 묶음: c에서 출발해 주경로 넷에 닿을 때까지 거꾸로 따라간 비주경로 신호 셀 전부다. 닿은 주경로 넷이 **탭** u다.
   - 함께 묶는 것: 묶음 내부 넷에 drain이 붙은 바이어스 전류원(`ff_bias`)과 diode 부하(`ff_load`).
   - **우회 조건**: u에서 m까지 주경로가 지나는 블록 출력노드 중 FF 묶음이 지나지 않는 것이 하나 이상 있어야 한다. 그 첫 블록이 **처음 우회한 블록** B_b다. 우회 조건을 만족하지 않으면 FF가 아니고, 기존 규칙(§1.7 병렬 합류)대로 처리한다.
   - 주경로 최장 경로가 둘 이상이고 셀 집합이 다르면 `review_needed`(`main_path_ambiguous`)다. 이 판정은 FF 후보 묶음이 있는 뷰에서만 한다(as-built U1b 2026-10-09: 무조건 판정하면 push-pull 병렬 버퍼 가지(파일럿·pushpull·sf)에서 오발동한다. FF가 없으면 주경로를 고를 이유가 없다).
3. **블록 분해**
   - FF 묶음의 셀을 빼고 §1.7을 다시 적용하면 주경로 블록 사슬이 된다.
   - m은 그 노드를 출력으로 갖는 주경로 블록에 둔다. FF 묶음은 그 블록의 **합류 입력**으로 붙인다.
   - FF 합류에는 복합 블록 조건(§1.9, DEC-81)을 적용하지 않는다. 경로 기여로 다룬다(아래 4).
   - 산출 필드: `feedforward_cells[{id, tap, merge, cells, bias_cells, load_cells, bypassed_blocks, sign}]`. sign은 경로 셀 부호의 곱이다.
4. **gain 귀속**
   - gain 예산(§5 bin·조합·`gain_budget_db`)은 주경로 블록에만 둔다. FF에는 예산 항목이 없다.
   - FF 기여는 §2 블록 국소 모델에서 **경로 기여**로 계산한다. merge 블록의 국소 해에 탭 전압을 추가 입력으로 넣는다.
   - 분해 합성값: A_decomp = Π_main A_i + Σ_ff A_in→tap · G_ff · Z_merge.
   - 잔차(§2.2)는 `gain_ss_db − 20·log10|A_decomp|`다.
   - `ss.ff_contrib{ff_id: {gain_db, sign}}`를 함께 쓴다.
5. **비율 제약 후보**(sizing 제약, 출처 기록)
   - FF 묶음마다 r_ff = G_ff / gm_in(B_b)를 정의한다.
   - G_ff: B_b 입력 넷 전압에서 merge 노드 단락 전류까지의 FF 경로 트랜스컨덕턴스. FF 안의 미러 비를 포함한다.
   - gm_in(B_b): B_b input 셀의 gm이다.
   - 관계 r_ff = 1이 영점 상쇄 조건 후보다. 출처: You, Embabi, Sánchez-Sinencio, IEEE JSSC 32(12), 1997; Leung & Mok, IEEE TCAS-I 48(9), 2001.
   - S1v는 `ff_ratio_candidates[{ff, bypassed_block, relation, source}]`를 내고, 단계 A 보고(`stage_a_report`)가 이를 출력한다.
   - metric `ff_gm_ratio`(단위 ratio, 40 §3.8-8 어휘에 추가)는 front 점마다 보고한다.
   - 제약 행은 spec이 값과 `source`를 선언할 때만 활성이다. 값은 사용자 몫이다.
   - 출발 구간(§6.5)은 FF 셀 전류 출발값을 r_ff = 1 관계에서 낸다. 이것은 출발값일 뿐이다(EP-7).
6. **달성가능성**(§4.2·§4.3)
   - A_i,max는 주경로 블록만 계산한다.
   - Σ 판정의 상한 = 20·log10(Π A_i,max + Σ_ff A_ff,max)이다. A_ff,max = (입력→탭 상한) × (FF 경로 격자 상한)이다.
   - 성분 하나라도 미상이면 상한은 미상이다(§4.2 규칙).

#### 1.12.3 중첩 Miller 내부 루프 = 보상 루프 (J-B)

**대상**: §1.8 (3) 판정으로 생기는 루프 뷰 후보 ℓ(끊는 점 c, 출처 전달 뷰 T).

**구조 조건**: 다음 (a)(b)를 모두 만족하면 ℓ은 `compensation_internal`이다.
- (a) ℓ의 모든 사이클이 (2) Miller 조건을 만족한다. 즉 사이클마다 커패시터를 포함한 수동소자만의 극대 구간이 있고, 그 구간이 T의 순방향 넷 둘을 잇는다.
- (b) ℓ의 사이클 위 능동 셀이 모두 T의 순방향 셀이다. 즉 루프가 개루프 증폭기 **내부**에 있다.

**처리**:
- 루프 뷰를 만들지 않는다. GB5가 보상 루프로 받는다.
- 안정도는 T의 전체 루프 제약 `pm_ss_deg`가 덮는다. 그 판정에는 개루프 RHP 극점 수 P = 0이 포함된다(결정 A 탐색 규칙, 오라클은 40 §4 Q10의 Nyquist Z = N + P와 `.pz`).
- T에 `pm_ss_deg` 제약이 선언되지 않았으면 기존 정지 `undeclared_loop_constraint`를 유지하고 사유 `compensation_internal_needs_overall_pm`을 붙인다.
- (3-b) 판정 자체는 바꾸지 않는다. 수동소자 엣지를 뺀 거리로 (3-b)를 다시 정하는 안(B3)은 9회로 실측에서 다른 회로를 깨므로 기각했다.

**조건 (b)가 막는 것**: 순방향 밖 능동 셀(예: 공통 모드 감지·주입 셀)이 낀 되먹임 루프는 (b)를 만족하지 않는다. 그런 루프는 루프 뷰로 남는다(40 §5).

#### 1.12.4 루프 극성 (J-F)

§1.8 '극성' 문단과 P N3.2-7의 '커패시터만 거쳐 저주파 경로가 없으면 `review_needed`'를 아래로 대체한다.
- **사이클 극성**
  - 커패시터를 지나지 않는 사이클(저항은 지나도 된다): 셀 부호의 곱(CS −1, 그 밖 +1, 저항 +1)이다. 이것이 **DC 사이클 극성**이다.
  - 커패시터를 지나는 사이클: 극성 `ac_only`로 기록한다(info `loop_polarity_ac_only`). 그 사이클의 수동소자는 GB5 보상 후보 목록에 올린다.
- **루프 뷰 극성** = 그 뷰에 속한 DC 사이클들의 극성이다.
  - 모두 같으면 그 값이다.
  - 서로 다르면 `review_needed`(`loop_polarity_conflict`)다.
  - DC 사이클이 하나도 없으면 `loop_polarity_undefined`(review_needed)를 유지한다. 1.12.3 뒤에는 발동 기대가 0이다.

#### 1.12.5 L 동치류 주인 (J-F)

DEC-17 순서(`E/graph/l_classes.py`)의 3번째에 규칙 하나를 넣는다.
1. tail
2. `current_source_member`: diode 기준(1.12.1의 복합 diode 포함)
3. **신규 `main_path_signal`**: 멤버 중 gain 제약 전달 뷰(없으면 첫 전달 뷰)의 **주경로 stage 시작 셀**(1.12.2)인 것. FF 묶음 멤버보다 우선한다. 여럿이면 가장 앞 stage 것이다.
   - 근거: FF 셀은 주경로 전류를 복사하는 쪽이다. 따라서 주경로 소자가 L 기준이 되는 것이 회로 원리에 맞다.
4. `name_order`: 남은 동률만 해당한다. `review_needed`(`l_owner_name_order`)로 올린다. **예외**(2026-10-09 오케스트레이터 결정): 동률 후보가 모두 같은 자기동형 궤도(U2 `automorphism_orbits`)에 들면 어느 쪽을 주인으로 골라도 구조상 같은 결과라 review를 올리지 않는다(정정 2026-10-09: nmcnr {M104, M105}는 단일 종단 미러 M108(diode)·M109(출력) 때문에 같은 궤도가 아니어서 이 예외에 들지 않는다 -- 독립 test·엔진 궤도 계산 확인).

**사실 `l_owner`가 이 순서를 덮어쓴다**(C-3, 사용자 결정 2026-10-12 "7절 권고대로"): `structure.json`에 그 동치류의 `l_owner` 사실(40 §3.2-3)이 있으면 1~4를 적용하지 않고 사실의 주인을 쓴다(override). 사실의 주인이 동치류 멤버가 아니면 `review_needed`(`structure_fact_mismatch`)다. 회로별 주인은 이 문서가 정하지 않는다. nmcnr {M104, M105}의 주인은 M105로 결정됐다(사용자 결정 2026-10-12 "C-3은 네 제안대로 해", 사실 파일로 적용, 40 §3.2-3).

#### 1.12.6 뷰 한정 교류접지 예외 (J-C)

§1.2 (4) 술어 결과 위에, ratified 사실 `ac_ground_exception{subject: 넷, value: 뷰 id}`가 있으면 **그 뷰에서만** 그 넷을 교류접지로 둔다(40 §3.2-3 override).
- 다른 뷰(CM 전달 뷰·전원 뷰 등)에서는 J1 판정이 그대로다.
- 구조 규칙이 아니라 회로 해석 사실이다. 근거: 레플리카가 전류원에 고정되어 신호 전류를 싣지 않으므로 1차 근사로 접지다. 잔여 효과는 오라클 CM 루프 측정이 잰다.
- 이 사실이 필요한지는 1.12.1을 적용한 뒤 실측으로 확인한다. 1.12.1은 레플리카 가지의 DC 역할과 루프 분류만 바꾸고, 루프 뷰에서 레플리카 구동 gate 넷이 움직이는 것은 바꾸지 않는다. 그래서 분석 패킷 C.4 기준으로는 그 뷰의 `cs_output_low_impedance` 정지가 이 사실 없이 남는다.

### 1.13 J 규칙 실측·기대 표 (규칙 아님 -- 회로 이름은 이 표와 40 §3.2-3에만)

'실측'은 분석 패킷의 9회로 측정값(`[u1-sp1]` 7c757e8)이다. '기대'는 패킷의 손유도와 부분 실측에서 나온 값이다. 기대값은 test 기준값이 아니다(EP-5). U1b가 9회로로 재고, 다르면 42 행에 차이를 보고한다(EP-8).

| 규칙 | 발동 회로·대상 | 무동작 | 근거 |
|---|---|---|---|
| 1.12.1 복합 diode | **실측**: sf_pushpull M5·M6·M7·M8·M13·M14(묶음 {M6, M5, R1a}, {M8, M7, R1b}, {M14, M13, R1c}, 기준 M6·M8·M14), 파일럿 M58·M63(묶음 {M58, M57}, {M63, M64}) | **실측**: 나머지 7회로 0 | 패킷 C.3·D.3 |
| 1.12.1 → DC 역할 | **기대**: sf M9·M17·M11·M16·M20 = 바이어스 전류원(미러 출력, AC는 K8). sf J-U3-c 3그룹 해소. ngcc {M8, M14}는 남는다(기준 없는 그룹 → 40 §3.2-3 `dc_role` 사실) | -- | 패킷 D.4·D.6, F.3 |
| 1.12.1 → 루프 분류 | **실측(U1b, 2026-10-09)**: sf `composite_diode_internal` **3개**({N1,N5}, {N2,N7}, {N12,N13}). 옛 기대 9개는 U1 그래프의 `record_only` 수였고, 묶음 내부 혼재 넷(N56·N78·N1314)은 1.12.1-2로 혼재 판정을 하지 않아 사이클이 생기지 않는다. 파일럿 레플리카 쪽은 신호 사이클 0 | -- | 패킷 D.3 |
| 1.12.2 feedforward | **기대**: ngcc FF1 = {M6B, M6A, M7}(bias M5, 탭 ND, merge Vout, B_b = 1단), FF2 = {M14}(탭 V1, merge Vout, B_b = 2단). 주경로 V1 → V2 → Vout. 복합 블록 0 | **기대**: 나머지 8회로 0(sf M17·M20은 merge가 블록 출력노드가 아니라서 K8) | 패킷 A.2·A.4(경로 부호 다섯 개가 모두 같은 위상) |
| 1.12.3 보상 내부 루프 | **기대**: ngcc `loop:M8:V1`, nmcnr `loop:M201:NodeM2` → 루프 뷰 0, `undeclared_loop_constraint` 해소(두 회로 모두 `pm_ss_deg` 선언 있음) | 파일럿 CM 루프는 (b) 불만족으로 루프 뷰 유지 | 패킷 B.2·B.4 |
| 1.12.4 극성 | **기대**: 파일럿 CM 루프 뷰 = −1(DC 사이클 4개), Cc–Rz 우회 사이클 2개 = `ac_only`. ngcc ×2·nmcnr ×4 미정의는 1.12.3으로 사라진다 | -- | 패킷 F.1 |
| 1.12.5 L 주인 | **기대**: ngcc {M8, M14} → M8(`main_path_signal`), sf 3동치류 → M6·M8·M14(`current_source_member`) | -- | 패킷 F.3·F.4 |
| 1.12.6 교류접지 예외 | 파일럿 Vbias2, 뷰 `loop:M37a:Voc`. 패킷 C.4 scratch 실측: 정지·혼재 3건 해소 | -- | 패킷 C.4·C.5 |
| sf 전체 | **기대**: 이득 블록 {Y} 하나 + 버퍼 블록 {vout}. `composite_dag_not_chain`·`record_only`·혼재 8건 해소. 남는 혼재는 `drive_kind` 사실로 메우지 않는다(v1.8: §1.5-4 C-1 보완 (가)가 sf 혼재 넷을 구조로 가르고, 예상 집합과 다르면 구현을 멈추고 보고, 40 §3.2-3) | -- | 패킷 D.4. DC 역할만 바꾼 scratch 실측에서는 DAG 1·record_only 9·혼재 3이 남았다. 그 원인인 미러 인식은 1.12.1-2가 바꾼다 |

---

## 2. FR-2 -- 블록 gain 모델과 MNA 잔차 (MOD5)

### 2.1 정의

**블록 국소 모델**(P N3.8):
- 미지수는 블록 노드 집합이다.
- 입력 넷에 단위 전압을 건다. 차동 블록은 ±½다(§1.7-3).
- 블록 밖 노드는 교류접지로 두거나, 다음 블록의 입력 어드미턴스로 고정한다.
- 스탬프 값은 봉인 스냅샷의 `ss`에서 가져온다.

**산출량**:
- 블록 gain = 20·log10|V(out)/V(in)| (ω → 0).
- Z_out = 입력을 교류접지로 두고 출력에 단위 전류를 넣었을 때의 출력 전압.
- 복합 블록의 경로별 기여 = 다른 경로 입력 소자의 gm을 0으로 둔 국소 해(부호 포함).
- feedforward 기여(§1.12.2-4): merge 블록 국소 해에 FF 묶음을 합류 입력으로 넣고, 탭 전압을 그 입력으로 준 해다. 주경로 블록 gain에는 넣지 않는다.

### 2.2 잔차

평가마다 다음을 S2 `ss`와 S3 evals 요약에 쓴다.
- `gain_residual_db = gain_ss_db(전회로) − Σ 블록 gain`. feedforward 묶음이 있는 뷰는 `gain_ss_db − 20·log10|A_decomp|`이고, A_decomp는 §1.12.2-4의 분해 합성값이다. 이때 `ss.ff_contrib`도 함께 쓴다
- `ss.block_gain{key: {gain_db, zout_ohm, contributions}}`
- `ss.rout_residual_ohm`(DEC-66)

블록을 가로지르는 되먹임 수동소자가 있으면 그 블록 gain은 '분해값'으로만 표시한다.

### 2.3 구현

- 블록 노드 부분집합에서 as-built 스탬프 함수(`mos_stamps`, `stamp_two_terminal`)로 (G_b, C_b)를 조립한다.
- ω → 0 극한은 `solve_dc_limit` 방식으로 푼다.
- 필드 캐시 키는 블록 키와 `ss` 입력 버전이다.
- 파일은 `E/metrics/block_model.py`, `block_residual.py`다.

### 2.4 결합 잔차 측정 (단계 B1)

- 표본: `dof_rank_sample_count`개의 준난수 θ다.
- 계산: 표본마다 평가 커널을 돌리고, 봉인을 통과한 점에서 잔차를 잰다.
- 산출: r̂ = 중앙값, r̂_spread = 최대 − 최소.
- 쓰임(40 §3.10.8 '결합 잔차의 쓰임', P N3.7):
  - (i) 진단 보고: 결과 JSON `diagnostics.residual_probe`.
  - (ii) 6c DoD 결합 잔차 표: 결과 JSON `residual_table[{block, metric, r_hat, r_spread, n_samples, seal_failures}]`.
  - (iii) 신뢰 한계: 잔차가 그 metric의 모델 오차 선언값(DEC-72)보다 크면, 그 블록 분해값을 할당 입력으로 쓸 때 `trust_limits[{block, metric, residual, model_error}]`를 함께 기록한다.
  - (iv) 층 0 조합 순서(§5.6).
  - 상한이 보장되지 않으므로 판정에는 쓰지 않는다(M2, DEC-74).

**상태**: MISS.

---

## 3. FR-3 연계

- 보상 `gm_req`(MNA 1-D 근)는 외층 판정에서 제약으로 쓴다(40 §3.5).
- 층 0 국소 고정점은 노드 C를 갱신하며 §6.5 매크로를 키워드 인자로 다시 풀어 블록 gm 요구와 보상 수동소자 시작값을 얻는다(§5.3.6).
- 조립점에서 `comp_approx_gap`을 기록한다(정의 §5.5).

---

## 4. FR-8 -- 탐색 전 달성 불가 판정 (GB4, MOD5)

**파일**: `E/metrics/achievability.py`(진입점), `curve_checks.py`, `block_gain_bound.py`, `dof_report.py`, `area_lower_bound.py`, `headroom_bound.py`(§4.6).

### 4.1 LUT 곡선 검사에서 해법으로 (P N3.7)

as-built `curve_report`와 `hermite_fc`의 칸 분류를 소비해, 칸마다 해법을 정한다.

| 칸 분류 | 해법 |
|---|---|
| 단조 | 역산 허용(`vgs_for_gm_id`, `vgs_for_current_density`) |
| 비단조 또는 Fritsch–Carlson 위반 | 그 칸은 격자 전수만 쓴다. 역산은 `lut_hermite_nonmonotone_cell`로 실패시킨다. 순방향 조회는 선형 폴백을 허용하되 사유를 기록한다(DEC-87) |
| 단위 불일치 | 로드 거부(`SchemaRejectedError`) |

산출은 `CurveCheck{kind, w_key, L, VDS, cell, method}`다. §5.3의 역산이 이것을 읽는다.

### 4.2 블록 gain 상한 A_i,max (P N3.7 격자 전수, C2)

**정의**: A_i,max = 블록 i 국소 모델 gain의 최댓값이다. 최댓값은 블록 결정 축의 격자 곱 전체에서 찾는다.

**축**: 등식으로 묶인 것(궤도, L 동치류, `equal_vgs`)은 축 하나로 센다.

| 축 | 격자 |
|---|---|
| 소자 그룹별 gm/ID | LUT gm/ID 격자 |
| L 동치류별 L | LUT L 점, 그리고 bin 안 L 구간의 내부 극값. 내부 극값이 양끝을 넘으면 그 점을 추가한다 |
| 기둥 VDS | W4 창 안의 LUT VDS 격자 |
| y (K1~K4) | 따로 새 격자를 만들지 않고 해당 LUT 축 격자를 쓴다. K1(부하 소자가 다른 블록의 미러·L 동치류에 속함): 그 소자의 gm/ID·L 축에 이미 포함. K2(공유 VGS): 노드 창 안의 LUT VGS 격자. K3(`stacked_vsb`): LUT VS 격자. K4(공유 노드 전압): W4 창 안의 LUT VDS 격자 |
| 블록 안 저항값 | 컨덕턴스 G = 1/R 기준 격자. 후보 G는 그 저항이 닿는 노드에 붙은 소자들의 LUT 격자 gds·W/w_m 값(축 격자에서 나오는 값)과, spec θ 범위 양끝의 1/R이다. 근거: 국소 모델에서 저항은 같은 노드의 소자 컨덕턴스와 더해지거나 직렬로만 영향을 주므로, 영향이 달라지는 지점은 그 컨덕턴스들과 비교되는 크기다. θ 범위 밖 후보는 버린다 |
| 미러 비 θ | 범위 양끝 + 내부 세분(아래 '비단조 축 처리') |
| 전류 배율 | 블록에 저항이 있을 때만 둔다(저항이 있으면 gain이 전류에 대해 0차 동차가 아니다). 격자는 전류 상자 [I_off, I_max] 위의 LUT ID 격자를 w_m으로 환산한 것. 같은 비단조 축 처리를 적용한다 |

**비단조 축 처리**(미러 비, 전류 배율, 저항, N5): 최대 행에서 그 축을 따라 양쪽 이웃 행의 gain을 본다.
- **이웃이 둘 다 작다**: 그 축에서 내부 최대다. 이웃 사이 구간을 이분해 세분하고, 이웃 간 gain 차가 b_GB4 이하가 되면 멈춘다. 상한은 K_max다.
- **최대 행이 축 끝점이고 그 방향으로 단조다**: 그대로 인증한다.
- **세분해도 이웃 차가 b_GB4 아래로 내려가지 않는다**: '미상'으로 둔다.

**계산**:
- 행마다 봉인 없이 블록 국소 모델을 풀어 gain을 구한다.
- 행 조건 (gm, ID, L, VDS, R, 비)과 함께 S0 지문 필드에 저장한다(행 단위 memo).
- 소자 파라미터는 LUT memo에서 한 번만 조회한다.

**예산 게이트**: 격자 곱 Π가 계수 예산 N_S(§0)를 넘으면(시간 무관, 결정론) 상한을 **'미상'**으로 두고 판정에 쓰지 않는다. 격자를 줄이지 않는 이유는, 줄인 격자의 최댓값은 상한이 아니기 때문이다. 이 처리는 P N3.7의 "LUT·구조만으로 상한을 계산할 수 없는 제약은 상한 미상"과 같다.

**분해능**: b_GB4,i = 최대 행과 그 격자 이웃 행들 사이 gain 차의 최댓값이다.

**GB5 재사용**: 보상 gm 요구로 다시 판정할 때는 이 표에서 gm 조건을 만족하는 행만 거른다. LUT 격자를 다시 돌지 않는다.

**버퍼 블록**: 같은 방법을 쓴다. 상한은 0 dB 이하다.

**층 0 정의역 상한 A_i,max^L0**(사용자 결정 2026-10-12 L-12 "GB4 블록 gain 상한 계산도 신호 소자 축만으로 축소", 재검증 Major-1 반영):
- **축 규칙**(§5.3.3 L-11의 자유 축과 같다):
  - 자유 축: S∪F 소자(§5.3.3)의 같은 VGS 묶음 VGS 축(= gm/ID 축), L 동치류 L 축 전부(L은 층 0에서 역산·LR5 격자로 움직인다, §5.3.5·§5.3.7), 전류·저항 축, 덮는 기둥의 W4 VDS 격자 축(VDS는 층 0에서 (c) 배분이 움직인다, §5.3.4. §4.2 표의 '기둥 VDS = W4 창 안의 LUT VDS 격자'와 같다).
  - 하나로 세기: matching 그룹(S1 `graph.matching_groups`의 derived `diff_pair`·`branch_symmetric`·`mirror`)과 자기동형 궤도로 묶인 소자의 VGS·VDS 축은 축 하나다(§4.2 '등식으로 묶인 것은 축 하나로 센다').
  - 고정: B 소자(§5.3.3)의 VGS 축과 모든 VS 축. 값은 S0 수준 필드 `start.row`(gm/ID·L)와 `start.point`(VDS, VSB)에서 읽는다(40 §2.4.8). VGS는 `vgs_for_gm_id`로 구하고 담는 LUT 격자 마디를 쓴다. 단계 B 기준점(봉인 평가)은 읽지 않는다(§0 DAG: A9는 단계 A).
- **계산**: §4.2와 같은 함수(격자 전수, 예산 게이트 N_S, 비단조 축 세분, 분해능 b)를 이 축에 적용한다. 단계 A9(A8 뒤)이고 결과는 S0 수준 필드다(40 §2.4.8 A9 행).
- **'추정' 표시**: 인증되어도 이 값은 B 소자를 출발값에 고정한 정의역 위의 최댓값이다. N3.7의 '봉인 가능 점을 모두 포함하는 상위집합 위의 상계'가 아니므로 늘 '추정'으로 표시한다(DEC-67).
- **쓰임**: 목표 bin 범위의 위 끝 후보로만 쓴다(§5.3.2: 위 끝 = max(A^L0 bin, 역산 실패 bin)). 첫 배분(§5.3.2, L-2)에는 쓰지 않는다. §4.3 exit 3과 §6.4-1 이득 L 하한은 축소 전 A_i,max만 읽는다(L-14).
- **실측(2026-10-12, as-built bd19cc6 코드 읽기 전용, `wt/_tmp_l0design/measure_v3.py`, 결과 `v3.jsonl`)**. N_S = 13,829,760(6회로 공통). 고정값은 as-built `start` 선택점(gm/ID·L)과 `CurveBook.points`(VDS, VSB, 40 §2.4.8에서 `start.point`가 된다)다.

| 회로 | 블록 | 축소 전 Π | A^L0 축 Π | 게이트 | A^L0 |
|---|---|---|---|---|---|
| common_gate_amplifier | vout | 1.9·10¹⁰ | 3.8·10⁷ | 초과 | 미상 |
| folded_cascode | out | 6.2·10⁵² | 7.8·10²⁹ | 초과 | 미상 |
| sf_pushpull_output_opamp | Y | 3.4·10⁸⁰ | 1.3·10⁴² | 초과 | 미상 |
| two_stage_ota | O1 / OUT | 1.7·10²² / 1.9·10⁹ | 3.0·10¹³ / 3.8·10⁷ | 초과 / 초과 | 미상 / 미상 |
| two_stage_ota_sf | O1 / OUT | 1.7·10²² / 1.9·10⁹ | 3.0·10¹³ / 3.8·10⁷ | 초과 / 초과 | 미상 / 미상 |

  - 재측정(실측(2026-10-12, as-built bd19cc6 코드 읽기 전용 + §6.7-1a 쓰기 계획 모사(같은 DC `input_tie` 엣지 제거), 'kvl 종속' 제외, `wt/_tmp_l0design/measure_v4.py`, 결과 `v4.jsonl`)): kvl 종속 VGS 축을 빼도 축 수가 같아 표 값이 그대로다.
  - 인증 수: 이득 블록 7개 중 **0개**. W4 VDS 축을 넣으면 가장 작은 블록(OUT, VGS 1 × VDS 2 × L 2)도 49²·18²·49 = 3.8·10⁷로 N_S를 넘는다. 그래서 지금 library에서 bin 위 끝은 모두 역산 실패 bin이 정한다(§5.3.2).
  - 직전 측정(VDS 고정, 단계 B 기준점 값)의 3개 인증과 그 값(48.8·54.5·52.8 dB)은 이 정의로 대체하며 쓰지 않는다. 그 값이 축소 전 `found_db`(61~68 dB)보다 낮았던 것이 '추정' 표시의 근거다.

### 4.3 gain 판정

다음 두 조건이 모두 맞으면 `InfeasibleTargetError`(exit 3)로 정지한다.
- 모든 블록 상한이 인증되었다.
- Σ_i (A_i,max + b_GB4,i) < G_target이다.

r̂와 모델 오차는 쓰지 않는다. 블록 하나라도 상한이 미상이면 판정하지 않고 보고만 한다.

**feedforward가 있는 뷰**(§1.12.2-6): 블록은 주경로 블록만이다. 비교식은 dB 합 대신 20·log10(Π A_i,max + Σ_ff A_ff,max) + b_GB4 < G_target이다. 이때 b_GB4는 주경로 블록 b의 합이다. FF 상한이 하나라도 미상이면 판정하지 않는다. FF 경로는 주경로와 같은 위상으로 더해질 때 이득을 키우므로 이 합이 상한이다.

산출은 `achievability{blocks[{key, A_max_db, b_db, status: certified|unknown, row_condition}], sum_db, target_db, verdict}`다.

### 4.4 면적 하한 (결정 11, 인증된 하한만, C1)

A_lb = Σ_k I_k,cert · L_min,k² / IDu_max,k + Σ_c C_c,min / ρ_MIM

| 항 | 뜻 |
|---|---|
| I_k,cert | 선언된 이상 전류원(`value_dc_amp`)과 KCL로 값이 고정된 가지 전류. 그 밖의 소자는 0 |
| L_min,k | LUT 최소 L 점(PDK 최소 L 이상) |
| IDu_max,k | LUT 최대 전류밀도 |
| C_c,min | 값이 선언되지 않은 보상 커패시터의 spec θ 하한, 선언값이 있으면 그 값. 측정 부하는 뺀다 |
| ρ_MIM | PDK 선언 `mim_cap_density_f_per_m2` |

- A_lb > A_budget + b_A이면 INFEASIBLE_TARGET(`area_budget_below_lower_bound`)로 정지한다.
- 출발값으로 계산한 면적 추정 A_est는 보고만 한다.

### 4.5 DOF

**구조 rank**(단계 A):
- 변수: 노드전압, 소자 gm_id(P N3.7 이름. 새 엔진 좌표는 쓰기 소자 ln IDu(DEC-88)이고 강반전 분지에서 gm_id와 일대일이라 rank가 같다. 종속 소자 gm_id는 관계가 정해 변수가 아니다), L 동치류 L, θ 전류, DC 경로 저항.
- 등식: diode, `equal_vgs`, `stacked_vsb`, `kvl_branch`, KCL. (`budget_ref`는 없다: 옛 `budget_reference_device`의 예산 관계는 기둥 KVL과 노드 변수 하나로 이미 들어 있다, 계획 DEC-55·사용자 결정 2026-10-12 "다로 해")
- 방법: 변수와 등식의 이분 매칭으로 rank를 구한다.
- 판정: 매칭되지 않는 등식이 있으면 `overconstrained`이고 INFEASIBLE_TARGET이다. 남는 변수가 있으면 `underdetermined` 목록을 낸다.
- 부등식(포화 여유, 벌크 역바이어스, 헤드룸 창 등)은 rank에 넣지 않고 경고로만 낸다(P N3.7 "부등식은 경고"): `dof_inequality_warning[{kind, devices}]`.

**수치 rank**(단계 B2):
- B1 표본에서 등식 잔차의 FD Jacobian을 만든다. 스텝은 LUT 격자 간격이다.
- `numpy.linalg.matrix_rank`(기본 허용오차)로 rank를 구한다.
- **표본 수 증거 규칙**(P N3.7 "선언값이 모자란다는 증거(같은 회로에서 표본을 늘렸더니 rank가 달라짐)가 나오면 그 회로에서 올리고 근거를 남긴다"): 선언 표본 n개의 rank와 앞 ⌈n/2⌉개의 rank를 함께 잰다. 둘이 다르면 표본이 모자랄 수 있다는 증거로 `dof_sample_evidence{n, rank_half, rank_full}`를 기록하고 보고 맨 앞에 둔다. 선언값 `dof_rank_sample_count`는 spec 선언이므로 엔진이 바꾸지 않는다. 올리는 것은 그 회로 spec 선언의 개정이고, 출처에 이 기록 id를 남긴다.
- 범위 안이다: 40 §8 R3은 사용자 결정 2026-10-08 "Q1~Q11 모두 네 의견대로 진행해" Q1(R2~R6 복원)로 복원되었다. 구현 시점은 계획 N1.2의 DEC-76 원칙(발동 회로가 생길 때)을 따른다.

산출은 `DofReport{status, structural_rank, numeric_ranks[], competing_pairs}`다.

### 4.6 헤드룸 달성가능성 (사용자 결정 2026-10-08 Q4 (6), 탐색 전 보고)

**왜 필요한가**: sky130 1.8 V에서는 pfet |VT|가 L bin에 따라 크게 뛴다(gm/ID 15에서 VSG 0.68 / 0.81 / 1.02 V at L 0.15 / 0.18 / 0.5 µm, 제안서 §0.4). 그래서 '게이트-소스로 쌓이는' 경로(입력 두 극성 공유 gate, follower 스택, PMOS 입력쌍)는 L bin 선택이 곧 DC 성립 여부다. 이 사실을 탐색이 수백 번 실패한 뒤가 아니라 탐색 전에, 유도와 함께 보고한다.

**대상(구조로 정한다, 이름 없음)**: S1의 레일-레일 경로 중 VGS 엣지를 하나 이상 지나는 DC 경로 전부. 각 경로에 대해 아래 세 창을 계산한다.
- 출력 창: 출력 노드에 닿는 경로들로 [V_lo, V_hi]의 최대 폭(`swing_out_v`의 상한).
- 입력 창: 입력 셀 gate에서 레일까지의 경로들로 [Vin,min, Vin,max] ∩ [rail_lo, rail_hi]의 최대 폭(`icmr_v`의 상한). 레일 밖 입력은 허용하지 않는다(사용자 결정 Q4 (4)).
- 버퍼 창: 버퍼 묶음(§1.9) 입력 노드가 DC로 성립하는 구간의 최대 폭.

**상한 계산(인증)**: 경로 폭 = ΔV_rail − Σ_VGS엣지 |VGS|_min − Σ_VDS엣지 (VDSAT_min + tol_VDsat). |VGS|_min·VDSAT_min은 그 소자 kind의 LUT 격자 전수(gm/ID, L bin, VS 축은 bulk 기본 규칙이 정하는 VSB 범위)에서의 최솟값이다. 서로 다른 소자를 독립으로 최소화하므로 실제 폭의 **상한**이다. 등식(`equal_vgs`, L 동치류)으로 묶인 소자는 한 축으로 센다(§4.2와 같은 규칙). 격자 곱이 N_S를 넘으면 '미상'이다.

**판정**(§4.3과 같은 규칙):
- 선언 제약(`swing_out_v >=`, `icmr_v >=`, `icm_margin_v >= 0`)의 대상 창이 **모두 인증**되었고 상한 + 분해능 < 목표면 `InfeasibleTargetError`(exit 3, 사유 `headroom_unattainable{metric, window, upper_bound, target, derivation}`)이다.
- 선언 제약이 없는 창(포화 전용 -- SPICE 합격 조건 '모든 MOS 포화'에만 걸리는 버퍼 창 등)과, 입력 DC가 SP-2 대기라 `icm_margin_v`를 판정할 수 없는 경우는 **보고만** 하고 정지하지 않는다.
- 산출 `headroom_achievability[{path, window_kind, upper_bound_v, binding_devices, best_row{gm_id, L_bin, VSB}, status: certified|unknown, verdict}]`. 각 행에 유도(경로 엣지 목록과 엣지별 최솟값의 출처 LUT 칸)를 함께 적는다.

**알려진 사례**(제안서 §2.4·§7·§8·§9 추정 -- W 5 µm 한 슬라이스·bulk = 레일 가정이다. **test 기대값이 아니다**, 기대값은 오라클 DC 스윕과 test 작성 주체가 만든다):

| 회로 | 경로 | 제안서 추정 |
|---|---|---|
| current_reuse(파일럿) 입력단 | 두 극성 입력이 같은 gate: VDSAT5 + VGS4 ≤ Vin ≤ VDD − VSDsat6 − VSG1 | 창이 pfet 최단 bin(L 0.15 µm)·nmos 약반전에서만 열린다(+0.14 V), L 0.18 −0.02 V, L 0.5 −0.15 V |
| nmcnr_amplifier 입력 | Vin,max = vdd − VSDsat101 − VSG102 | L ≥ 0.5 µm에서 −0.26 ~ −0.48 V → 입력 DC 0 V(agnd 관례, SP-2 대기)는 창 밖 |
| sf_pushpull_output_opamp 출력 버퍼 | Y ∈ [VGS19 + VDSAT20, VDD − VSDsat17 − VSG18] | L 0.15 +0.11 V, L 0.18 −0.12 V, L 0.5 −0.32 V. 선언 입력 DC 0.9 V도 Vin,min 0.83–0.99 V에 걸린다 |
| pushpull_follower_buffer | vin 창 = [VDSAT6 + VGS4, VDD − VSDsat5 − VSG3] | 위와 같은 식·같은 수치. Rout ≤ 1 kΩ 선언과 충돌 가능 |

**후속 처리**: bulk 기본 규칙(NMOS = 최저 레일, PMOS = 최고 레일)은 유지한다(사용자 결정 Q4 (6)). 입력 DC와 버퍼 구성은 아래 J-E 결정으로 닫혔다.

**입력 DC 정책(J-E, 사용자 결정 2026-10-08)**: 입력 DC는 회로가 아니라 사용 환경이 정하는 값이다. 회로가 정하는 것은 창이다.
- **SP-2 (c) 창 안 자유 변수**: 입력 DC가 `pending: SP-2`인 회로는 값을 지어내지 않는다.
  - 입력 공통모드를 W4 자유 변수 y_icm으로 둔다. y_icm은 입력 포트인 W4 뿌리(회로마다 최대 하나 -- 둘 이상이면 탐색 전 정지, §4.7-1)의 y 성분이고 **y 키는 그 뿌리 넷 이름**이다(card IT-1, 계획 N6.5 범위 2·4; 옛 묶음 키 `input_common_mode`는 없어진다). 범위는 입력 창 [Vin,min, Vin,max] ∩ [rail_lo, rail_hi]이고 경계는 tol을 포함한다(포화 판정 여유 +tol_VDsat). **경계의 층별 정밀도**(사용자 결정 O-33 (3), card IT-2): 평가 커널에서는 그 해에서 잰 선형 감도 끝(손계산, '추정' 표기)이고, 끝 풀이(창 끝 x 고정 Newton)로 다듬은 봉인 시점 값은 수락 반복·front에서만 낸다(§4.7-3·4).
  - `icm_margin_v`·`required_input_cm_v`·`icmr_v`는 입력 포트 창 필드를 읽기만 한다(§4.7-5, card IT-2 -- metric 쪽 자체 창 계산은 없다). 결과 JSON `required_input_cm_v{value, window}` 형식은 그대로다(IT-Q2, 사용자 결정 O-13 (2)).
  - '창 중앙값'을 숫자로 선언하지 않는다(EP-4).
  - agnd 0 V 관례는 이 정책의 회로에 적용하지 않는다.
- **선언 입력 DC 유지**: 입력 DC가 선언된 회로는 그 값을 쓰고, `icm_margin_v >= 0`을 제약으로 둔다(40 §9.2). 그 창도 입력 포트 창 필드에서 읽는다(§4.7-2 (c) -- 선언 포트는 F라 y 범위가 아니다).
  - 위 판정 규칙에 따라 창이 인증되었고 상한 밖이면 exit 3이다.
  - 출력 버퍼 창(follower 스택)은 선언 제약이 없어도 **탐색 전 실현가능성 보고**로 낸다. 이것은 기존 '보고만' 규칙과 같다. 이 보고는 단계 A 보고서에 별도 행 `buffer_window_report`로 출력한다.
- **짧은 L bin 경고**: 입력 창 상한이 인증된 상태에서, 그 창을 정하는 경로의 어느 kind가 **최단 L bin에서만** 양의 폭을 낼 때가 있다. 그때는 경고 `icmr_window_short_l_bin{kind, bin, upper_bound_by_bin}`를 낸다.
  - 이 경고는 탐색을 막지 않는다. 탐색 공간의 구조 정보로 보고에 싣는다.
  - 창이 모든 bin에서 비면 기존 판정 규칙(제약 있으면 exit 3)을 따른다.
  - 회로별 적용은 40 §9.2 표에 있다.

**파일**: `E/metrics/headroom_bound.py`(진입점 `achievability`가 부른다).

### 4.7 입력 포트 창 -- 정본 하나 (card IT-1·IT-2, 계획 N6.5·N6.6, v1.12)

**목적**: 입력 공통모드 창(J-E)을 계산하는 곳을 노드 풀이 블록 하나로 두고(DEC-83·FR-9, 원칙 감사 C1 '입력 CM 창 2곳'), metric은 그 필드를 읽기만 하게 한다. §4.6의 헤드룸 창 상한(`headroom_bound`, LUT 격자 최솟값 상한 = 탐색 전 달성가능성 경계)은 다른 개념이라 이 절의 대상이 아니다(계획 N6.6 소비자 표).

**4.7-0 as-built 사실**(master `9401e98f`, 2026-10-20 이 design 작성 때 코드를 다시 읽음. `E` = `skills/analog-gmid-design/gmid_engine`):

| # | 사실 | 근거 |
|---|---|---|
| A1 | 쓰기 계획: 입력 DC 미선언이면 F 밖 입력 포트를 (구조 색, 이름) 이웃 쌍마다 '같은 DC' 엣지로 잇고(순위 최상위 `_TIE`·`_KIND_TIE`), 트리 엣지면 `input_tie`(W2)로 쓴다. 포트가 있는 성분의 뿌리 y 키 = `INPUT_GROUP_KEY`(`"input_common_mode"`) | `E/sizing/writer_plan.py:76-77, :104-105, :157-159, :213-214, :228-234` |
| A2 | `input_roots()` = relation `free_window`이고 y 키가 `INPUT_GROUP_KEY`인 W4 뿌리. `members`는 `input_tie` 사슬을 따라 뿌리에 묶인다. `dc_columns` READS에 `node.port_direction`이 없다 | `E/sizing/block_columns.py:179-184, :220-223, :82-86` |
| A3 | `saturation_rows` = 전도 MOS마다 (d, s, 부호, VDS − VDsat − tol_VDsat), 선형 선언 소자 제외, VDSAT 열·tol 미정이면 None | `E/sizing/block_columns.py:225-244` |
| A4 | `input_windows` = 뿌리마다 `saturation_window` 창 ∩ 순서 창(`kvl_window`, 레일 범위 포함) | `E/sizing/block_columns.py:246-259` |
| A5 | `saturation_window`는 `_sensitivities`(s_n = dV_n/dx 선형 연립, VDS·VSB 결합 포함)로 창을 잰 뒤 감도를 버리고 (lo, hi)만 낸다. 연립 특이·정의역 밖이면 None | `E/sizing/input_window.py:26-45, :48-66` |
| A6 | `_solve_input_window`: y = 1/2 풀이 → 창 측정 → 창을 y 범위(`override`)로 두고 다시 풀며 경계가 tol 안에서 같아질 때까지(상한 `k_max`) → `_refine_ends`(창 끝 x 고정 Newton) → 마지막 풀이. 갈래: (a) y = 1/2가 풀리지 않거나 창을 못 재면 `_interior_solution`이 이분 수준 y 열(`_dyadic_ys`, 시도 상한 `k_max`)에서 풀리고 창을 잴 수 있는 점을 찾고(θ 키는 호출자가 준 `key` -- as-built `(y, INPUT_GROUP_KEY)`), 못 찾으면 요청 y·순서 창으로 푼다(종래 사상) (b) `tolerance`가 미정(`SealViolationError`)이면 창을 한 번만 적용하고 되풀이 수렴 판정 없이 푼다 (c) 되풀이가 `k_max` 안에 tol 안으로 같아지지 않으면 마지막으로 잰 창을 그대로 쓴다(수렴 표시 없음) | `E/sizing/block_columns.py:691-735`(a `:713-717`·`:640-660`, b `:719-723`, c `:724-733`) |
| A7 | `_refine_ends`의 끝 값이 풀린 x인 경우는 (i) `inside and close` (ii) 풀이 직후 `again is None` 둘뿐이고, (iii) 첫 반복 풀이 실패 (iv) 둘째 반복 이후 풀이 실패 (v) `k_max` 소진에서는 끝 = 풀지 않은 x다. 끝 풀이 해(`values`)는 버린다. 끝이 무한대면(제약 없음) 손대지 않고 멈춘다(`:672` -- 순서 창이 레일 범위로 시작하므로(`kvl_window` `:201`) 입력 뿌리 창 끝은 실제로는 늘 유한) | `E/sizing/block_columns.py:663-688` |
| A8 | `dc_columns`는 relation `free_window`인 모든 넷에 `node.dc_window` = `Window(lo, hi, constraints)`(순서 창 ∩ `override`)를 쓴다 -- 입력 포트가 아닌 넷·뿌리 아닌 입력 포트·선언 입력 포트는 해당 없음 | `E/sizing/block_columns.py:770-778`, `E/sizing/s2_values.py:355-361`, `E/sizing/CONTRACT.md:202`(master `2e707d5d`에서 다시 잼, 옛 `:196`) |
| A9 | metric 쪽 둘째 창: `ls_swing`이 입력 포트마다 경로 합 [lo, hi]의 교집합을 재고 `v_icm = volts[inputs[0]]`(첫 포트)로 margin을 낸다. 호출 `metrics_aux._swing` | `E/metrics/ls_swing.py:107-118`, `E/metrics/metrics_aux.py:214, :236, :256-264` |
| A10 | **계획 소비자 표 밖 소비자**: `fd_jacobian._steps`가 `node.dc_window`를 그 넷 writer의 y 키로 색인해 y FD 스텝(창 폭)을 정한다 -- 창이 W4 뿌리에만 있다는 전제 | `E/search/fd_jacobian.py:52-55, :65-68` |

**4.7-1 card IT-1 -- 쓰기 계획 개정**(계획 N6.5 범위 1~5, 결정 B2·K-3·O-13 (1)(2)):

1. **같은 DC 엣지 없음**: 입력 DC 미선언이어도 G_vgs에 '같은 DC' 엣지를 넣지 않는다. 엣지 순위 `_TIE`·`_KIND_TIE`, `TieBreak(input_tie_order)` 기록, `input_tie` 쓰기와 어휘(`REL_TIE`·`PATH_TIE`·`TIE_INPUT_ORDER`·`INPUT_GROUP_KEY`와 그 공개 export)를 지운다. 같은 변경에서 지우는 소비 자리(master `2e707d5d`에서 잼, 검증 I2): `E/sizing/scc_order.py` import `:21`·`:26`, `REL_TIE` 사슬 `:125`, `REL_TIE`·`INPUT_GROUP_KEY` 분기 `:137-140`, docstring `:7-8`; `E/sizing/CONTRACT.md` relation 어휘 `:232-233`, `TIE_INPUT_ORDER` `:238`, 쓰기 계획 문언 `:311`·`:318`·`:321`, 읽기 집합 `:351`, 식 `:420`, path_values `PATH_TIE` `:497`, 예시 `:635`, 입력 묶음 되풀이 문언 `:1014-1016`.
2. **뿌리와 y 키**: 뿌리 규칙은 그대로(F 없는 성분에 입력 포트가 있으면 그중 (구조 색, 이름) 최소, 같은 색 후보가 둘 이상이면 `TieBreak(w4_root)`). **y 키 = 뿌리 넷 이름**(입력 포트 뿌리도 다른 W4 뿌리와 같은 규칙). θ 성분 키는 `(y, <뿌리 넷>)`이고 결과 JSON 키 `y:input_common_mode`는 `y:<넷>`이 된다. 한 성분 안 뿌리가 아닌 입력 포트는 트리 경로(MOS VGS)로 쓰인다.
3. **종속**: 같은 DC 엣지로 생긴 종속은 0이다. 포트 경로가 둘 이상인 v1 고리는 ΔV를 소거한 KVL 하나가 남아 그 고리 멤버 하나가 `cycle_vgs` 종속이다(파일럿 VGS1a − VGS1b = VGS4a − VGS4b, M1b). 대칭이면 그 등식은 대칭 묶음과 중복이다. 불변식 '종속 수 = 순환수'는 같은 DC 엣지 없는 G_vgs(F 한 점) 기준이다.
4. **다중 입력 뿌리 -- 정지 안전망**(IT-Q1 (나), DEC-76): 입력 포트인 W4 뿌리가 둘 이상인 쓰기 계획은 `dc_writer_plan`이 `StructureUnresolvedError`(detail `reason` = `unsupported_rule_branch`, `rule_branch` = **`input_port_multiple_roots`**, `nets` = 그 뿌리 넷들(쓰기 순번 순))로 낸다. `dc_writer_plan`은 S0 블록이라 탐색 전 정지다. 상수 이름 `BRANCH_INPUT_MULTIPLE_ROOTS`(`E/sizing/s2_values.py`, `BRANCH_RESISTOR_CYCLE` 옆). 뿌리별 y 묶음(`domain.ties`)·뿌리별 포화 창은 **미구현(발동 0)** -- 계획 DEC-64 상태 칸·sizing CONTRACT 3절에 같은 표시, DEC-59 발동표에 이 분기 행(발동 회로 0). 코퍼스 발동 0은 계획 F-IT9(근사 모사)이고 card 0 M-I1이 엔진 쓰기 계획으로 다시 잰다.
5. **노드 풀이 블록 쪽**(같은 card): `members` = 자기 자신(사슬 없음), `input_roots()` = relation `free_window`이고 넷이 입력 포트인 W4 뿌리(`dc_columns` READS에 `("node", "port_direction")`을 더한다). **G_vgs 밖 고립 입력 포트**(MOS gate·source에도 저항에도 닿지 않아 쓰기 계획이 W4 y 키 = 넷으로 쓰는 넷, `writer_plan.py:236-238`)도 입력 포트인 W4 뿌리로 센다 -- 4의 '둘 이상이면 정지'에 들어간다(그 넷도 사용 환경이 DC를 정하는 입력이고, 세지 않으면 y가 둘인 회로가 정지 없이 지나간다; 코퍼스 발동은 IT-0 M-I1이 기록). `_solve_input_window`의 θ 키 = `(y, <입력 뿌리 넷>)`(뿌리는 4로 최대 하나 -- 같은 키를 `_interior_solution`에 넘긴다), `REL_TIE` 분기(writer 식·야코비안·path value) 삭제. `achievability`의 `tie:<넷>` 등식 삭제.

**test interface(IT-1, test 작성 주체 -- 소스 없이)**: 진입점 `dc_writer_plan(snapshot, target_nets, input_dc_declared, order_hints=NO_ORDER_HINTS)`(서명 불변). 출력 필드 `node.dc_writer`(`NodeWrite(tier, relation, element, known, y_key, order)`), `device.dc_coord`(`DeviceCoord(role, relation, partner)` -- `E/sizing/s2_values.py:281-287`), `graph.dc_tie_breaks`(`TieBreak(decision, candidates, chosen)`; decision `input_tie_order`는 없어지고 `writer_edge`·`w4_root`·`current_pivot`이 남는다). 어휘: `NodeWrite.relation` ∈ {`rail`, `declared_target`, `input_dc`, `vgs_gate`, `vgs_source`, `resistor_drop`, `free_window`}(`input_tie` 없음), `DeviceCoord.role` ∈ {`writer`, `dependent`}, `DeviceCoord.relation` ∈ {`tree`, `parallel_vgs`, `cycle_vgs`, `fixed_vgs`}. 세 필드의 형식은 그대로이고 값 어휘·y 키만 바뀐다(계획 N6.5 완료 조건 4 (c) -- 40 §2.4.8 '쓰기 계획 필드(IT-1)' 행). 단언 (a) 입력 DC 미선언 차동 입력 toy: relation `input_tie` 0, 입력 포트 W4 뿌리의 y 키 = 그 넷 이름, 기대 종속 목록(같은 DC 엣지로 생긴 종속 0, 포트 경로가 둘 이상인 v1 고리의 ΔV 소거 `cycle_vgs` 포함)은 toy 연결에서 손으로 유도한다 (b) 종속 수 = 같은 DC 엣지 없는 G_vgs(F 한 점)의 순환 수(손계산) (c) 입력 DC 선언 toy의 쓰기 계획 = 손계산 오라클(base에서도 green -- 무동작 성질) (d) 두 입력 포트가 서로 다른 G_vgs 성분인 toy → `StructureUnresolvedError`, `detail["rule_branch"] == "input_port_multiple_roots"`(base는 정지하지 않아 red). 위치 = `E/tests/sizing/test_writer_plan.py` 안 새 test 함수(이름은 test 주체가 `git grep`으로 겹침 확인, F-IT4 -- 구조 규칙 H).

**4.7-2 card IT-2 -- 필드 셋**(이름 정본 = 계획 N6.6 범위 1·N6.8 DE-1 (a)·N3.3 S2 행. 정밀도·기준이 다르면 이름이 다르다):

| 필드 | 뜻 | writer | 층·호출 자리 | 읽는 쪽 | 이 design 판에서 |
|---|---|---|---|---|---|
| `node.dc_window` | **탐색·판정 창**: 포화 판정 여유를 넣은 창(VDS − VDsat − tol_VDsat ≥ 0, `saturation_rows` 현행 식), 그 해에서 잰 **선형 감도 끝**(손계산, '추정'). 입력 포트가 아닌 W4 뿌리는 지금처럼 순서 창 | `dc_columns`(노드 풀이 블록) | 평가 커널(모든 평가, FD 열 포함) | 커널 탐색 `fd_jacobian` y 스텝(W4 뿌리만, 4.7-6) -- θ 프레임 창의 값 독자는 이것뿐이다(계획 N6.6 범위 1 '`node.dc_window`는 θ 프레임 창이라 커널 탐색만 읽는다', O-58 S-1). `icm_config`는 이 필드의 상태 칸만 읽는다(4.7-3b '커널 상태 이어받기') | IT-2가 쓰는 범위를 '모든 입력 포트와 W4 뿌리'로 넓힌다 |
| `node.dc_window_cfg` | **측정 구성 판정 창**(계획 N3.8 '창 필드', O-58 S-1): 측정 구성 ICMR(follower·선언 되먹임·KVL 고정)에서 +tol_VDsat로 잰 창. 값 꼴 = `node.dc_window`와 같은 `Window` 하나(아래 '값 형식'). **모든 측정 구성에서 쓴다**(`as_is_single_input` 포함 -- v1.12.1에서 옛 W1 규칙 '`as_is_single_input`이면 쓰지 않고 소비자가 `node.dc_window`를 읽음'을 철회: θ 프레임 창은 출력을 순서 창 비례(W4)·고정(W3)으로 두어 '출력은 회로가 정하는 대로 따름'(계획 N3.8 '단일 입력 회로는 회로 그대로가 구성이다', O-25 (2))과 측정 구성 축이 다른 양이다 -- 계획 N6.6 범위 1 '어느 쪽도 follower가 아니다'; 두 정의를 한 필드로 합치면 graph 단일 정본 규칙 3 위반). 구성이 None(정의 불능)이면 쓰지 않고 소비자는 `graph.icm_config.undefined`를 metric 정의 불능으로 옮긴다(4.7-5 '측정 구성 정의 불능의 경로') | 새 블록 `icm_config`(4.7-3b) | 평가 커널, 봉인 뒤(`E/metrics/ss_evaluate.py:101` 뒤) | 커널 ICMR 선언 제약·커널 metric(`metrics_aux`, 아래 5), `dc_window_refine` 출발 창(DE-1 전, O-61 P6), front·보고의 선형 감도 끝만 정의되는 구성(KVL 고정 출력 구조·`as_is_single_input`)의 포트 값(계획 N3.8 '선형 감도 끝만 정의되는 구성의 정본 칸' -- O-61 P3·O-63 (4)) | IT-2가 만든다(입력 포트마다; 상태 칸이 커널 미수렴·F 성분 미선언을 이어받음 -- O-61 P4·P5) |
| `node.dc_window_def` | **정의 창**: VDS ≥ VDSAT(tol 없음)·전도 끝(봉인 9 식, 훑기 점 값) | card DE-1 (a)의 블록 | 평가 커널 | DE-1 뒤 metric 값 | **예약 -- 이 card는 만들지 않는다**(DE-1 몫) |
| `node.dc_window_def_refined` | **다듬은 창**: 끝 풀이(창 끝 x 고정 Newton)로 다듬은 봉인 시점 창. DE-1 전에는 끝 풀이 기준이 지금 식(+tol_VDsat)이고 DE-1이 정의(tol 없음·전도 끝)로 바꾼다. 같은 이름에 다른 기준이 실리는 기간은 **기준 칸 `criterion`**으로 구별한다(사용자 결정 O-49 P5, 계획 X-IT12 -- 이 card의 값 = `"tol_judgement"`('+tol 판정 기준'), DE-1이 `"definition"`('정의 기준')으로 바꾼다) | 새 블록 `dc_window_refine`(4.7-4) | 수락 반복·front에서만(4.7-4 호출 자리) | front 판정·보고 metric(아래 5) | IT-2가 만든다(입력 포트 가운데 4.7-4 2 '쓰지 않는 포트'(F 성분 미선언 포트, 선형 감도 끝만 정의되는 구성(`kvl_fixed` 출력 구조·`as_is_single_input`)의 입력 포트, 출발 창 없는 포트, 출발 창 미수렴 포트)를 뺀 포트 -- v1.12.2) |

**DE-1 전 한정**(계획 N6.6 범위 1·2): metric 값 = 커널은 `node.dc_window_cfg`(측정 구성 판정 창 -- 모든 구성), front·보고는 `node.dc_window_def_refined`(선형 감도 끝만 정의되는 구성(KVL 고정·`as_is_single_input`)의 포트·F 성분 미선언 포트·출발 창 미수렴 포트는 그 칸에 항목이 없고 `node.dc_window_cfg`를 읽는다 -- 계획 N3.8 '선형 감도 끝만 정의되는 구성의 정본 칸', 사용자 결정 O-61 P3·P4·O-63 (4)·O-64 (2), 4.7-5 front). DE-1 병합 뒤 metric 값은 `node.dc_window_def`, 선언 제약 판정은 `node.dc_window_cfg`(측정 구성 판정 창)를 읽고 그 제약 행은 다른 이름을 갖는다(DE-1 design 몫; 계획 N6.6 범위 1 'DE-1 병합 뒤에는 metric 값 = `node.dc_window_def`, 선언 제약 = 측정 구성 판정 창'·DE-1 (ii′) -- v1.12.1 gap G2 정정, 옛 '`node.dc_window`'는 O-58 전 문언 잔재).

**값 형식**:
- `node.dc_window` = `Window(lo, hi, constraints, input_status=None, tol_v=None, status_detail=())`(`E/sizing/s2_values.py` `Window`에 기본값 있는 칸 셋을 더한다). `input_status` ∈ {None(입력 포트가 아닌 W4 뿌리 -- 지금 순서 창), `"measured"`(입력 포화 창을 재고 되풀이가 tol 안에서 수렴), `"unsettled"`(창은 잰 해에서 쟀으나 되풀이가 `k_max` 안에 수렴하지 않았거나(A6 c) tol 미정이라 수렴 판정을 못 함(A6 b)), `"unmeasured"`(창을 잴 수 없어 순서 창만 -- A6 a의 종래 사상, 뿌리 항목만), `"op_mismatch"`(선언 소자가 커널 마지막 풀이에서 선언 영역과 어긋남 -- 4.7-3a 3, 그 성분 모든 입력 포트, `lo`·`hi` = None), `"f_component_undeclared"`(F 성분에 속한 입력 DC 미선언 포트 -- 창이 정의되지 않음, 계획 N6.6 범위 1 (c), 사용자 결정 O-61 P4 (b) (가); 4.7-3 3, `lo`·`hi` = None)}. `node.dc_window_cfg`(4.7-3b)는 같은 `Window` 꼴이고 상태 칸 `input_status`로 커널 창의 `"unsettled"`·`"f_component_undeclared"`를 이어받는다(4.7-3b '커널 상태 이어받기' -- 계획 N6.6 범위 1 '상태를 나르는 칸 = 기존 창 필드의 상태 칸', O-61 P5). `icm_config` 자기 측정 실패(연립 특이·`saturation_window` None·행을 만들 수 없음)의 꼴 = `Window(None, None, 0, input_status="unmeasured")`. **상태 우선순위**(한 포트에 둘이 겹칠 때, v1.12.1 N3): definitional 상태(`"f_component_undeclared"`·`"op_mismatch"`)가 numeric 상태(`"unsettled"`·`"unmeasured"`)보다 앞선다(4.7-5 code 우선순위와 같은 규칙). `status_detail` = `"op_mismatch"`일 때만 `(("devices", 소자 이름 정렬 tuple),)`, 그 밖 `()` -- 소비자 `metrics_aux`(4.7-5 `IcmPort.missing` detail). `tol_v` = 그 창을 잰 풀이의 허용오차(`tolerance(소자 전부, 해)` = 그 해의 소자 tol_V 셀 최솟값, A6의 되풀이 판정에 쓰는 값) 또는 None(미정 -- A6 b). `constraints`는 뿌리면 지금 뜻(순서 제약 수), 뿌리 아닌 포트·선언 포트면 0(순서 창이 없다).
- `node.dc_window_def_refined` = `RefinedWindow(lo, hi, lo_end, hi_end, tol_v, criterion)`(새 frozen dataclass, `E/sizing/s2_values.py`). `criterion` = 끝 풀이 기준(O-49 P5): 상수 `CRITERION_TOL_JUDGEMENT = "tol_judgement"`(계획 '+tol 판정 기준' -- 끝 풀이의 창 측정이 `saturation_rows` 현행 식, 이 card가 쓰는 유일한 값)·`CRITERION_DEFINITION = "definition"`(계획 '정의 기준' -- card DE-1 (a)가 기준을 바꾸면서 쓴다, 이 card는 상수만 둔다; 정의는 계획 N3.8 '창 필드는 정의와 판정 여유로 나눈다'를 인용, 이 design은 옮겨 적지 않는다). 기본값 없음(쓰는 쪽이 늘 명시 -- 기준 없는 다듬은 창을 만들 수 없게). 소비자: 변화표 원인 칸·보고가 이 칸을 **직접**(필드 참조로) 읽는다(계획 N6.6 완료 조건 (7) (e) -- `IcmWindow`에 사본 칸 없음, v1.12.1 검증 M6·gap I-2; 4.7-5 `IcmWindow.sources`). `lo_end`·`hi_end` = `WindowEnd(x, v, reason)`(새 frozen dataclass) -- **x 쪽 끝**이다: `lo_end` = 훑는 x의 아래 끝, `hi_end` = 위 끝(포트 전압의 아래·위가 아니다 -- 감도 음수 포트는 x 아래 끝이 포트 위 끝이다). `x` = 그 끝에서 마지막으로 다룬 x(뿌리면 뿌리 전압, 선언 포트 묶음이면 묶음 이동량 Δ -- 4.7-3 3), `v` = **끝 풀이 해에서 이 포트의 전압**(성공한 해가 있을 때만, 아니면 None -- 이것이 계획 범위 1의 '끝 풀이 포트 전압 보관'이다), `reason` = None(풀린 끝) 또는 결측 사유. **포트 창 = 두 끝 전압의 [min, max]**(사용자 결정 O-49 P2 -- 커널 창 4.7-3 2와 같은 규칙): 두 끝이 모두 풀렸으면 `lo` = `max(min(lo_end.v, hi_end.v), rail_lo)`, `hi` = `min(max(lo_end.v, hi_end.v), rail_hi)`. **어느 한 끝이라도 결측이면 `lo` = `hi` = None**이다 -- 다듬은 창은 감도를 싣지 않아 결측 끝이 포트의 아래·위 어느 쪽인지 해만으로 정해지지 않으므로, 남은 한 끝을 한쪽 경계로 놓지 않는다(조용한 대체 금지, N3.14). 이때도 metric은 어차피 정의 불능이다(4.7-5 `input_window_end_missing`, detail `end` = 결측인 x 쪽 끝 `"lo"`/`"hi"`). `tol_v` = 끝 풀이 수렴 판정 tol(A6·A7의 `tol`).
- 예시 리터럴(test 작성용): `Window(0.31, 1.12, 2, input_status="measured", tol_v=1.2e-4)`, `RefinedWindow(lo=None, hi=None, lo_end=WindowEnd(x=0.30, v=0.30, reason=None), hi_end=WindowEnd(x=1.15, v=None, reason="window_end_solve_failed"), tol_v=1.2e-4, criterion="tol_judgement")`.
- **정확도 표기**(계획 N6.6 범위 1 '정확도(oracle 대조 오차)를 표기'): 커널 창은 손계산 '추정'이다. 그 정확도는 metric 쪽 `IcmWindow.model_error_ref`(4.7-5)에 적는다 -- 값 = card ME-1의 모델 오차 판정 기록 id, ME-1 전에는 None이고 보고에 '보류'(채울 card ME-1, 계획 N6.3 (i)·N6.19)로 적는다. 창 필드 자체에는 칸을 두지 않는다(모델 오차는 metric 단위 선언값, DEC-72).

**4.7-3 커널 창(IT-2 범위 1, O-33 (3))** -- `dc_columns`(노드 풀이 블록)가 같은 평가 안에서:
1. **뿌리**(입력 DC 미선언, 4.7-1로 최대 하나): A6 그대로 y = 1/2 풀이 → 창 측정 → y 범위로 다시 풀기 되풀이(상한 `k_max`)까지 한다. **`_refine_ends`는 커널에서 부르지 않는다.** 마지막 풀이의 `override` = 마지막으로 잰 선형 창. 뿌리의 `node.dc_window` = 순서 창 ∩ `override`(as-built와 같은 식), `input_status` = 되풀이가 tol 안에서 수렴했으면 `"measured"`, A6 b·c 경로면 `"unsettled"`. **A6 c(`k_max` 소진 뒤 마지막 창 사용)와 fail-closed**: 그 창은 실제 해에서 잰 값이지만 자기를 y 범위로 둔 해와 tol 안에서 맞지 않아, 그 창을 metric 값으로 내면 수렴하지 않은 값을 수렴한 값처럼 쓰는 조용한 대체다. 그래서 y 범위로는 그대로 쓰되(풀이는 진행 -- 탐색이 그 점을 평가할 수 있게) metric은 정의 불능(`input_window_unsettled`, 4.7-5)이다. A6 b(tol 미정)도 수렴을 판정할 수 없으므로 같다. 이 미수렴 상태는 그 평가점의 측정 구성 판정 창 `node.dc_window_cfg`가 상태 칸으로 이어받아(4.7-3b '커널 상태 이어받기') 커널 metric·커널 ICMR 선언 제약도 정의 불능이 된다(계획 N6.6 범위 1 '커널 창 되풀이 미수렴', 사용자 결정 O-61 P5 -- 동작 변경, 완료 조건 (6)·(12) (a)).
2. **뿌리 아닌 입력 포트 p**(같은 성분, 트리 경로로 쓰임): [lo_x, hi_x] = 위 1의 뿌리 `node.dc_window` 끝. 마지막 `override`를 잰 **같은 `input_windows` 호출**의 해(뿌리 전압 x_k, 포트 전압 V_p)와 감도 s_p = dV_p/dx로 옮긴다(한 해에서 잰 값끼리만 쓴다): 두 끝 전압 a_p = V_p + s_p·(lo_x − x_k), b_p = V_p + s_p·(hi_x − x_k)에서 **lo_p = min(a_p, b_p), hi_p = max(a_p, b_p)**(사용자 결정 O-49 P2 -- 감도 음수 포트는 뿌리 아래 끝이 포트 위 끝이 된다, 빈 창·음수 폭으로 내지 않는다), 그다음 ∩ [rail_lo, rail_hi]. 그래서 `saturation_window`는 감도를 버리지 않고 낸다: **`saturation_window(unknown, roots, values, gradient, rows, *, slope=None) -> (dlo, dhi, slope) | None`** -- `roots` = x로 함께 움직이는 넷의 tuple(그 행마다 s = 1; 커널 뿌리면 `(뿌리,)`, 선언 포트 묶음이면 묶음 전체 -- 4.7-3 3; 원소가 쌍 `(행 넷, 고정 넷)`이면 그 행 넷의 식을 s_고정넷 = 1로 바꾼다 -- 측정 구성 follower의 'W4 뿌리 행을 V_out = x로 바꾼 같은 연립', 4.7-3b (2)·(4)), `slope`(키워드 전용, {넷: dV/dx} 또는 None) = 주면 안의 감도 연립을 풀지 않고 그 감도로 끝만 낸다(KVL 고정 구조 -- 감도 정본 `kvl_sensitivity`, 4.7-3b (3)·(4); 그때 `unknown`·`gradient`는 읽지 않고 반환 slope = 받은 값). 창 끝 식(행 교집합)은 이 함수 하나에만 있다(계획 N6.6 완료 조건 (2), 사용자 결정 O-61 P2), 출발점 x₀ = 0 기준 **이동량** 창 [dlo, dhi](as-built의 `x0 = values[root]` 절대 창 대신 -- 커널 뿌리 창은 호출자가 `values[뿌리] + [dlo, dhi]`로 만든다), slope = {넷: dV/dx}. 포트 창은 호출자가 한 규칙으로 만든다: 두 끝 전압 V_p + s_p·dlo, V_p + s_p·dhi의 [min, max] ∩ 레일(위 a_p·b_p와 같은 식 -- lo_x − x_k = dlo). 행 원소 꼴은 4.7-3a 1·4.7-7. κ 경로 필드를 다시 계산하지 않고 별도 노드 풀이를 하지 않는다. s_p < 0 발동 회로는 card 0 M-I4가 기록한다(4.7-8a). 뿌리 아닌 포트의 `input_status`는 뿌리 항목과 같다.
3. **x를 따로 두는 입력 포트 -- 입력 DC 선언 포트(F)**: 절차 = `saturation_window`, `unknown` = 고정 아닌 넷 + 그 포트(그 포트 행은 writer 식 대신 s_x = 1), 다른 F 넷은 s = 0. y 범위가 아니므로 `override`에 넣지 않는다(계획 N6.6 범위 1 (c)). 근거: J-E '입력 DC는 사용 환경이 정하는 값이고 회로가 정하는 것은 창' -- 입력 포트의 창은 그 포트를 바깥에서 구동한다고 볼 때 포화가 유지되는 구동 값 범위다. 이 절차의 대상은 선언 포트뿐이다 -- 아래 두 경우는 이 절차를 쓰지 않는다:
   - **F 성분에 속한 입력 DC 미선언 포트**(그 성분이 레일·W3에 닿아 포트가 W4 뿌리가 아니고 트리 경로로 DC가 정해지는 입력 포트 -- 계획 F-IT9의 heldout r2r_opamp 꼴, library 발동은 IT-0 M-I1이 기록): 창은 **정의 불능**이고 사유를 기록한다(계획 N6.6 범위 1 (c), 사용자 결정 O-61 P4 (b) (가) -- fail-closed, DEC-76과 같은 처리). 그 포트 하나만 자기 x로 훑는 창은 P3 묶음 훑기·O-25 (2) 공통모드 정의와 충돌해 두지 않고, 측정 구성이 묶지 않은 모든 입력 포트를 같은 x로 함께 움직이는 일반형은 공동분석 대상이라 채택하지 않는다(같은 결정). 기록: `dc_columns`가 그 포트 항목을 `Window(None, None, 0, input_status="f_component_undeclared")`로 쓴다(4.7-2 '값 형식'; 감도 연립·끝 풀이 없음). 이 상태는 `node.dc_window_cfg`가 이어받고(4.7-3b '커널 상태 이어받기'), `dc_window_refine`은 그 포트를 쓰지 않으며(4.7-4 2), metric은 code **`input_window_f_component_undeclared`**(category `definitional` -- 창이 정의되지 않음, 4.7-5)로 정의 불능을 낸다. 분류 근거 = 쓰기 계획(그 포트의 writer relation이 `free_window`가 아니고 입력 DC 선언이 없음) -- 새 규칙·상수 없음.
   - **고립 입력 포트**(G_vgs 밖 -- 게이트·소스·저항 어디에도 닿지 않아 쓰기 계획이 W4 y 키 = 그 넷으로 쓰는 포트): 계획 N6.5 4(사용자 결정 O-61 P4 (a))대로 '입력 포트인 W4 뿌리'로 센다 -- 둘 이상이면 4.7-1 4의 정지, 하나뿐이면 그 창은 **위 1의 뿌리 창 절차 그대로**다(새 절차 없음; 그 넷에 닿는 소자가 없어 행이 그 넷의 감도를 쓰지 않으면 창 = 레일 교집합이 그 절차의 출력이다). `domain.ties` y 묶음·뿌리별 포화 창은 구현하지 않는다(상태 '미구현(발동 0)', 계획 N6.5 완료 조건 7).

   **x 하나의 묶음**(사용자 결정 O-49 P3, 계획 X-IT11 -- 옛 '포트마다 따로 x' 해석 대체): 위 선언 포트 가운데 측정 구성이 묶지 않은 포트(O-53 A-2 -- θ 프레임 창 `node.dc_window`는 측정 구성이 없어 이 묶음 = 선언 포트 전부; 측정 구성 창·다듬은 창의 묶음은 선언 포트 − `graph.icm_config` `tied_ports`, 4.7-3b)는 **모두 같은 x만큼 함께** 움직인다: `saturation_window(unknown, roots = 묶음 포트 tuple, …)`로 부른다 -- 묶음의 모든 포트 행이 s = 1, 공통 x 하나(선언 포트 사이 차 유지 -- 각 포트 전압 = 선언값 + Δ, x₀ = 0 기준 이동량 Δ). 반환은 이동량 창 [dlo, dhi] 하나와 slope이고, **포트별 창**은 호출자가 4.7-3 2와 같은 규칙(V_p + s_p·dlo, V_p + s_p·dhi의 [min, max] ∩ 레일; 묶음 포트는 s_p = 1이라 [선언값 + dlo, 선언값 + dhi])으로 만든다. 결과 창은 포트마다 그 포트 전압의 끝 [선언값 + Δlo, 선언값 + Δhi]이다(같은 x 이동량 Δ, 포트별 창 끝이 선언 차만큼 어긋난다). 선언 포트가 하나면 이 묶음은 그 포트 하나다(옛 절차와 같다). `input_status` = 잼 `"measured"`(되풀이가 없으므로 tol 미정만 `"unsettled"`).
4. **측정 실패**(`saturation_rows` None·연립 특이 -- A6 a '종래 사상' 경로): 뿌리 항목은 순서 창, `input_status="unmeasured"`. 뿌리 아닌 포트·x를 따로 두는 포트 항목은 쓰지 않는다. 이 창을 읽는 metric은 정의 불능(4.7-5) -- 순서 창을 입력 창 값으로 쓰는 조용한 대체를 metric에 들이지 않는다(N3.14). **DE-1과의 나눔**: IT-2는 여기까지(측정 실패 → 상태 표시와 metric 정의 불능)다. DE-1 범위 2 '선형 감도 연립 특이 fail-closed'의 나머지(일반화된 끝점 블록의 결측 사유 기록 칸, 출력 창·방향 전류까지 같은 규칙, 요청 y·순서 창 '종래 사상' 풀이 경로 자체의 처리)는 DE-1 몫이다.
5. 결과 `node.dc_window`의 `tol_v` = 그 창을 잰 해의 `tolerance` 값. 미정이면 None이고(A6 b) 그때 `input_status="unsettled"`, metric 분해능은 None이다(4.7-5 -- 분해능을 지어내지 않는다).

**4.7-3a 창 경계 행 = DC 범위 조건**(계획 N6.6 범위 1 '창 경계 조건', 완료 조건 (9); 사용자 결정 O-54·O-55 U1·V5; 정의 정본 = 계획 N3.8 '소자 조건 = DC 범위 조건' -- 여기서는 인용만): 커널 창(4.7-3)과 다듬은 창(4.7-4)의 경계 행을 같은 선형 감도 연립에서 소자의 선언 영역(`intended_region`)별로 낸다. 새 기계는 두지 않는다.
1. **행 셋**(`_helpers_dc_solve.Circuit.saturation_rows`를 `region_rows`로 넓힌다 -- 반환 행 목록, **행 원소 꼴 = 5원소 `(a, b, sign, slack, kind)`**: `a`·`b` = 여유가 기대는 전압 차의 두 넷(행 기울기 = `sign`·(s_a − s_b)), `slack` = 그 해에서의 여유(≥ 0이 안쪽), `kind` ∈ {`"sat"`, `"triode"`, `"off"`}; 여유의 x 미분이 `sign`·(s_a − s_b)가 되도록 `sign`을 둔다 -- `saturation_window`의 끝 정의(`rate = sign·(s_a − s_b)`, `slack + rate·Δ ≥ 0`, `E/sizing/input_window.py:57-65`)가 그대로 맞는 부호): (가) 선언 없음(포화) = **`(d, s, 부호, VDS − VDsat − tol_VDsat, "sat")`**(지금 행 그대로, 부호 = 소자 극성 부호) (나) `triode` 선언 = **`(d, s, −부호, VDsat − VDS − tol_VDsat, "triode")`**(여유가 VDS↑에 줄어 기울기 부호가 포화 행과 반대; 판정 여유의 정의 자리 = 계획 N3.8 '소자 조건'의 `triode` 경계 판정 여유(사용자 결정 O-58 T-1 -- 인용만, 정의 사본 없음); `tol_VDsat` = (가) 행과 같은 정본 `sat_threshold` 값(headroom-chain HC-S, 계획 O-33 (8)) -- 훑기 점이면 그 점 자신의 VDS·VSB 셀, 새 상수·둘째 진입점 없음) (다) `off` 선언 = **`(g, s, −부호, V_on − VGS, "off")`**(첫 칸 = gate; 여유 V_on − VGS는 VGS↑에 줄어 기울기 = −부호·(s_g − s_s); 판정 여유 없음; V_on = 그 점에서 봉인 9 전도 정의(I_off ≤ ε·ID)를 처음 만족하는 VGS -- 아래 2). 선형화에서 VDsat·V_on은 그 해의 값으로 고정한다(행 기울기에 넣지 않는다 -- 지금 포화 행과 같은 손계산 '추정'). 지금 `saturation_rows`는 선언 소자를 빼기만 한다(`E/sizing/block_columns.py:223-224`) -- 그 제외를 이 행 셋으로 바꾼다.
2. **V_on의 출처**: card EO-1의 공용 전도 판정 함수(사용자 결정 O-55 U2·V5 -- 'off 유지 경계 = VGS 감도 + 봉인 9 전도 VGS(LUT)', 같은 함수가 LUT I_off로 판정)를 부른다. 이 design은 그 함수를 새로 만들지 않고 이름·서명은 EO-1 design을 인용한다. **S-4(사용자 결정 O-58 S-4 -- 계획 N6.6 범위 1·완료 조건 (9), N6.20 범위 (4)·완료 조건 (8) (b))**: (다) 행과 `off` toy는 **IT-2·EO-1 가운데 늦게 병합되는 card**의 변경이다(O-56 (b)와 같은 규칙; 지금 spec 어휘는 `triode` 하나 `E/authoring/spec_regions.py:16-17`이라 `off` 어휘 없이 넣는 행은 죽은 코드). 갈래 둘:
   - **(S4-가) IT-2가 늦게 병합**(EO-1 공용 함수와 `off` 어휘가 master에 있음): 이 card가 (다) 행을 `region_rows`에 넣는다. V_on = 공용 전도 판정 함수 **곁**에 두는 역함수(EO-1 모듈 안 공개 함수 -- 이름·서명은 EO-1 design 인용, 이 design은 정하지 않는다; 정의 = 그 점의 VDS·VSB에서 봉인 9 전도 정의를 처음 만족하는 VGS, LUT I_off 열 위 1변수 근 -- 계획 N3.3 (a) LUT memo 대상)를 부르는 자리 하나(`region_rows`)를 더한다; 근 풀이 종료 분해능 = 그 점의 tol_V 셀(계획 N3.8 '훑기 점의 I_off 평가 점' -- `tol_v_table(kind, w_key)`의 그 점 VDS 열, 새 상수 없음). 그 호출 자리 하나가 EO-1 완료 조건 (8) (b) '공용 함수 호출 = 봉인 7·9 + 그 행' 단언에 더해진다. test = 4.7-7 L7 `off` 변형(이 card 판정).
   - **(S4-나) EO-1이 늦게 병합**: 이 card에는 (다) 행·V_on 호출·`off` toy가 **없다**. `region_rows`의 `kind` 값은 {`"sat"`, `"triode"`}뿐이고, 4.7-7 L7이 (1) `region_rows`의 `kind` 집합 = {`"sat"`, `"triode"`} (2) 이 card 소스에 공용 전도 판정 함수·V_on 역함수 호출 0(`git grep`)을 단언한다(부재 단언 -- 죽은 코드 없음의 증거). (다) 행과 `off` toy는 EO-1 design·test 몫이고 위 (S4-가)의 꼴(행 원소·V_on 자리·분해능)을 그대로 인용한다.
   - 어느 갈래인지는 오케스트레이터가 이 card 착수 때 master의 EO-1 병합 여부로 정해 card에 적는다(design은 둘 다 정한다). (다)에 tol을 더하지 않는다(상수 발명 금지).
3. **동작점 불일치**(O-53 B1·O-55 U1, 검증 M1 정정 -- 옛 '사유 없는 `unmeasured`' 대체): 선언된 `triode`·`off` 소자가 동작점에서 선언 영역과 어긋나면 창을 내지 않는다. 거부 자체는 봉인 게이트(계획 N3.6 표 7·9행, card EO-1 범위 4 (b))가 '선언 오류'로 낸다(노드 풀이 블록은 봉인 전이라 거부하지 않는다).
   - **판정 점 = 커널 마지막 풀이**(4.7-3 1의 마지막 `override` 풀이 해 -- 그 해가 평가 스냅샷이 되어 봉인이 같은 점을 본다; 입력 DC 미선언 뿌리도 이 점이 동작점이다). 다듬은 창(4.7-4)은 이 판정을 다시 하지 않는다(봉인 실패 점은 다듬지 않는다).
   - **판정 함수·기준 = 봉인 7·9와 같은 것**: `off` = card EO-1의 공용 전도 판정 함수(O-55 U2 -- 봉인 9가 바로 부르는 함수), `triode` = 봉인 7의 triode 대조와 같은 함수·기준(여유 = 계획 N3.8 '소자 조건'의 `triode` 경계 판정 여유, 사용자 결정 O-58 T-1; 봉인 7 대조도 같은 기준 -- 계획 N3.6 표 7행, 맡는 card EO-1 N6.20 범위 (4) (b); tol_VDsat = `sat_threshold` 값). 이 블록은 행 여유 부호로 따로 판정하지 않는다(정본 하나 -- tol 띠의 소자를 블록과 봉인이 다르게 보는 일이 없게).
   - **기록**: 불일치가 있으면 그 성분의 **모든** 입력 포트 항목(뿌리·뿌리 아닌 포트·x 포트 -- 4.7-3 4의 '뿌리 아닌 포트 항목은 쓰지 않는다'는 측정 실패에만 해당)을 순서 창 없이 `input_status="op_mismatch"`, `status_detail` = `(("devices", (소자 이름 정렬 tuple)),)`로 쓴다(4.7-2 `Window` 칸). metric은 이것을 정의 불능 code **`input_window_operating_point_mismatch`**(category `definitional` -- 선언과 동작점의 불일치로 창이 정의되지 않음, detail = 소자)로 낸다(4.7-5). 같은 점·같은 함수라 봉인이 늘 거부하므로 이 code가 metric 기록에 실리는 것은 블록과 봉인이 갈라진 경우뿐이다 -- 그때도 조용한 `unmeasured`가 아니라 사유가 남는다(N3.14·O-55 U1). 불일치 소자 열은 거부된 점의 스냅샷 필드로 남아 진단에 쓰인다.
   - 선언 없는 소자의 비포화는 봉인 7·9 거부(그대로, O-55 U1 '설계 실패').
4. **훑기 도중 이탈 = 범위 끝**(O-54): 위 행 셋의 첫 영(0) 교차가 창 끝이다 -- 측정 거부가 아니다. 지금 `saturation_window`의 끝 정의(행마다 a·Δx + 여유 ≥ 0의 교집합)가 그대로 이 뜻이다.
5. 다듬은 창(4.7-4)의 창 측정과 (ii) 끝 확인(4.7-4 2)도 같은 `region_rows`를 쓴다. headroom-chain HC-S(`sat_threshold`)가 같은 자리를 고치므로 순서는 **IT-1·IT-2 → HC-S**(그대로), `device.dc_sat_v`의 `off` 갈래는 O-56 (b)로 HC-S·EO-1 몫이다(이 card 아님).

**4.7-1a 출력 구조 분류 필드 `node.dc_output_structure`(v1.12.2, 사용자 결정 O-64 (1) -- 정의 정본 = 계획 N3.8 '출력 구조 분류 -- 규칙 하나', 인용만·정의 사본 없음; IT-1·IT-2 통합 병합에 든다)**:
- **writer = 쓰기 계획 블록 `dc_writer_plan` 하나**(상수 `DC_WRITER_PLAN_WRITER`, `E/sizing/writer_plan.py`; 계획 권고 자리 'S0 쓰기 계획 쪽'을 design이 확정). WRITES에 `("node", "dc_output_structure")`를 더한다(지금 WRITES `E/sizing/writer_plan.py:73`). **자리 근거**: (i) 그 블록은 S0 당 1회·θ 무관(`writer_plan.py:3`)이고 `PLAN_WRITERS`(`E/sizing/kernel_context.py:49`) 원소라 커널 컨텍스트 `ctx.base`의 base writer다 -- 4.7-3c 스냅샷 파생 규칙으로 모든 child 스냅샷에 그대로 남고, 봉인 뒤 블록·커널 밖 블록이 같은 입력 버전의 값을 읽는다(계획 N3.3 스냅샷 파생 규칙 5) (ii) 분류의 입력 -- 레일(`node.is_rail`), 출력·입력 포트(`node.port_direction`, `OUTPUT_DIRECTION` `E/authoring/ports.py:24`), W3 목표 넷(extras `target_nets`), 입력 DC 선언(extras `input_dc_declared`), G_vgs 엣지 목록(`_edges`, `writer_plan.py:95`) -- 이 모두 그 블록 안에 이미 있다; 다른 블록에 두면 G_vgs 엣지 목록을 다시 만들어야 해서 둘째 생산자가 된다. READS·extras는 바뀌지 않는다(블록 코드 해시만 바뀐다 -- `context_fp`에 든 `PLAN_WRITERS` 블록 입력 버전이 한 번 바뀜, 변화표에 적음). **등록**(v1.12.3 MF-3): 권한표 `DC_WRITES`의 `DC_WRITER_PLAN_WRITER` 행(`E/sizing/s2_values.py:143`)에 `("node", "dc_output_structure")`를 더한다(→ `S2_WRITERS`). `E/sizing/CONTRACT.md:14` 문단(`dc_writer_plan`이 쓰는 S0 필드)과 소유표(`:191` `node.dc_writer` 행 옆)에 새 행 `node.dc_output_structure | dc_writer_plan | 출력 포트 넷 | str`을 더한다. 이 변경으로 깨지는 기존 test 넷(v1.12.4 재측정) -- `E/tests/sizing/test_s2_values.py:70-75` `test_dc_table_has_33_fields`(`DC_TABLE` 행 수)·`:97-106` `test_s2_writers_is_s1_plus_dc_table_exactly`(S2 권한표 = S1 + `DC_TABLE` + `SS_TABLE`)·`:118-124` `test_dc_writes_constant_matches_table`(`DC_TABLE` 기대)·`:127-128` `test_block_name_and_writes_match_table`(블록 WRITES = 표) -- 의 기대 갱신은 **test 작성 주체 몫**이다. **같은 test에 걸리는 IT-2 새 writer 전부**(v1.12.4 검증 nice-fix -- 이 필드만이 아니다): `DC_WRITES`에 `dc_window_refine`(`node.dc_window_def_refined`, 4.7-4), `SS_WRITES`에 `ss_nodal`(`graph.ss_nodal`)·`icm_config`(`node.dc_window_cfg`·`graph.icm_config`)·`metrics_icm_front`(`graph.metrics_icm_front`)(4.7-3b·4.7-5) -- 영향 = `:70-75` `DC_TABLE` 행 수, `:97-106` S2 = S1 + `DC_TABLE` + `SS_TABLE` 등식, `SS_TABLE` 기대, `:118-124`·`:127-128` 표·블록 WRITES 대조; 모두 test 작성 주체 몫(IT-2 card별 test 커밋)(작성자 ≠ 검증자; code 작성자는 고치지 않고, 변경표에 test 작성 항목으로 적는다).
- **값**: 출력 포트 넷마다 `"high_impedance"` | `"kvl_fixed"`(상수 `OUTPUT_HIGH_IMPEDANCE`·`OUTPUT_KVL_FIXED`, `E/sizing/s2_values.py` -- `NodeWrite` 정의 옆); 출력 포트가 아닌 넷에는 쓰지 않는다. **값은 둘뿐이다** -- v1.12.1의 `w3_target`은 물리 구조 분류가 아니다(계획 규칙에서 W3 출력은 핀을 뺀 뒤 고임피던스 또는 KVL 고정으로 갈리고, 고임피던스 W3 출력의 '목표값을 x로 바꿈'은 follower 행 세우는 법이다). 출력이 W3 목표 노드인지는 `node.dc_writer`(tier W3)가 정본이고 소비자가 그것을 읽는다 -- 분류 필드에 표지를 두면 같은 사실의 둘째 칸이다(graph 단일 정본 규칙 3).
- **계산**(블록 안 지역 계산, 계획 규칙 그대로): F′ = 레일 ∪ (입력 DC 선언이면 입력 포트) -- **W3 목표 넷은 F′에 넣지 않는다**(출력 자신의 것과 성분 안 다른 W3 목표 노드의 것 모두 -- 계획 'W3 목표 핀을 모두 뺀 뒤', 'W3 목표는 sizing 기준점이지 물리 전원이 아니다'). 같은 블록이 쓰기 계획에 쓰는 G_vgs 엣지 목록(F를 한 점으로 묶기 전의 넷 사이 엣지)에서 출력 넷부터 너비 우선으로 성분을 걷는다: F′ 넷에 닿으면 `"kvl_fixed"`, 성분을 다 걸어도 닿지 않으면 `"high_impedance"`, 출력 넷이 G_vgs 엣지의 끝점이 아니면(G_vgs 밖) `"high_impedance"`. W3 목표 넷은 걷기를 멈추지 않는 보통 노드다. **걷는 엣지**(v1.12.3 N-1): IT-1 뒤 `_edges`의 MOS gate–source·저항 엣지이고 '같은 DC' 엣지(`_TIE`, IT-1 전 `writer_plan.py:104-105` -- IT-1에서 삭제됨)는 들지 않는다 -- 계획 N6.5(card IT-1, `input_tie` 폐기)가 그 엣지를 없애고 IT-1·IT-2가 한 통합 병합이라(O-19 (2)) 분류가 `_TIE`를 보는 기간이 없다. **저항만으로 이어진 W3–레일 경로**는 분류 전에 쓰기 계획의 기존 정지 `dc_resistor_cycle`(`writer_plan.py:162-165` -- 두 F 사이 비트리 저항)에서 멈춘다(분류 값 없음, 기존 동작 그대로). 회로·소자·넷 이름과 태그(`device_roles` 등)를 읽지 않는다(EP-1). 새 상수·새 규칙 없음.
- **소비자(READS만 -- 다른 블록 재계산 금지, 계획 같은 문단)**: `icm_config`(4.7-3b -- follower 행 (2)·KVL 고정 연립 (3) 갈래 선택), `dc_window_refine`(4.7-4 2 (b) -- 선형 감도 끝만 정의되는 구성 판정), card DE-1 (b) 출력 스윙의 고임피던스/KVL 고정 구분(DE-1 design 몫 -- 4.7-9 인계). `metrics_icm_front`는 읽지 않는다(포트별 출처 = 다듬은 창 항목 유무). 출력 구조를 내는 다른 자리(성분 걷기·핀 뺀 쓰기 계획 재구성) 0.
- **차동 출력**: 출력 포트마다 값이 있다. 측정 구성 쪽 소비는 v1.12.1과 같이 출력 하나(단일 출력)일 때만 이 값으로 갈래를 고르고, 차동 출력은 4.7-3b (1)의 구성 규칙(선언 없으면 `icm_config_differential_output_undeclared`)을 따른다 -- 이 판에서 바꾸지 않음. 선언이 있는 차동 출력은 아래 멈춤 S-OS2.
- **동작 변경**(4.7-8): v1.12.1 설계 대비 '단단한 경로 위 W3 출력'(O-64 경우 1)이 `w3_target` follower에서 KVL 고정 연립으로 바뀐다. library 발동은 card 0이 잰다(4.7-8a). **13회로 출력 구조 분류표 승인 = IT-1·IT-2 통합 병합 조건**(사용자 결정 O-66 (3), 계획 v6.24 N6.6 순서 -- **충족됨**(O-66 (1): 15출력 KVL 고정 7·고임피던스 8, 경우 1 = 0); 옛 v1.12.2 문언 'DE-1 착수 조건이고 IT-2 착수 조건 아님' 대체). 그 표가 IT-2의 분류 기준선이다 -- IT-2 변화표는 이 필드 값을 표와 대조해 적고, 불일치면 구조 규칙을 고치기 전에 멈추고 보고한다; 병합 전에 W3 목표 선언(CI-15)·F 선언·코퍼스가 바뀌면 표를 다시 재고 승인받은 뒤 병합한다(계획 같은 문단).
- **멈춤 S-OS1**(계획 먼저, S-7): 분류는 계획 규칙대로 정해지지만, `high_impedance`로 분류된 출력의 writer 사슬 뿌리가 출력이 아닌 W3 목표 노드인 경우(아래 OS (f) 꼴) θ 고정 연립에서 어느 고정을 풀어 'V_out = x' 행을 세우는지(그 W3 목표값을 x 미지수로 바꾸는지 등)는 계획 N3.8이 적지 않았다(계획은 '출력이 W3 목표 노드이면'만 적음). 구현 agent는 이 갈래의 창 계산(일반형)을 만들지 않는다. **실행 중 만나면 fail-closed**(v1.12.3 MF-2·gap N1 -- 계획 N3.14 공통 실패 규약의 적용, 계획 개정 불요): `icm_config`가 `config` = None, `IcmConfig.undefined`에 `definitional` code **`icm_config_output_root_w3`** 하나(detail `(("output", 출력 넷), ("root", 그 W3 넷))`)를 쓰고 `node.dc_window_cfg`를 쓰지 않는다 -- 세 metric은 4.7-5 M7 경로로 그 code로 정의 불능, 선언 ICMR 제약은 기존 unmeasured 경로(`ss_constraint_rows` → 최종 front 제외, 4.7-5 '미수렴 front 처리' (가)와 같은 경로). card 0이 library 9회로와 heldout 4회로에서 발동 수를 재고(4.7-8a), 발동이 있으면 일반형은 계획 개정이 먼저다(회로 해석 공동분석).
- **멈춤 S-OS2**(v1.12.3 MF-4; v1.12.4 -- 일반형은 계획 v6.24 N3.8 '차동 출력 회로의 측정 구성'(576행, 사용자 결정 O-68 (2): 차동 모드만 닫음 (in+ − in−) = −(Vop − Von), 입력 공통모드 = x, `kvl_sensitivity`에 닫힘 행 둘, margin 대상 = 입력 포트 둘)이 정했고 **후속 card 몫**이다 -- IT-2c는 fail-closed로 시작한다(사용자 결정 O-67 (5)); 이 판은 일반형을 설계하지 않는다): 되먹임 구성이 선언된 차동 출력. 구현 agent는 IT-2에서 이 갈래의 창 계산을 만들지 않고, 실행 중 만나면 `icm_config`가 `config` = None, `definitional` code **`icm_config_differential_output_structure`**(detail `(("outputs", 출력 넷 tuple),)`)를 `IcmConfig.undefined`에 쓴다(M7 경로, 선언 제약은 unmeasured 경로). card 0이 발동 수를 잰다(4.7-8a). 선언 없는 차동 출력의 `icm_config_differential_output_undeclared`도 O-68 (2) 일반형이 대체할 규칙이지만 IT-2에서는 그대로 fail-closed다(같은 후속 card). IT-2 병합 전 검증자가 이 차동 처리가 13회로 표 Q1(CMFB 감지 차동 출력 4개 KVL 고정, '추정', 정확값 oracle `.dc`)과 N3.8 '차동 출력 회로의 측정 구성'에 어긋나지 않음을 판정 기록에 적는다(계획 N6.6 'design 차동 처리 정합 확인', O-66 (1) Q1·O-68 (2) -- 어긋나면 멈추고 보고).
- **test(분류 toy -- 이름 없는 toy, 기대는 toy 연결에서 손으로 유도; test 파일 = 쓰기 계획 test `E/tests/sizing/test_writer_plan.py` 옆 새 파일 `E/tests/sizing/test_output_structure.py`, 규칙 H)**: OS (a) 출력 = 드레인만 닿는 노드(G_vgs 밖) → `high_impedance` (b) 출력이 F′ 없는 G_vgs 성분(W4 뿌리 성분 -- 출력에 MOS source writer가 있는 꼴 포함) → `high_impedance` (c) 부하 저항이 출력과 레일을 잇는 차동 입력 단일 출력 → `kvl_fixed` (d) W3 목표 출력, 핀을 뺀 성분에 F′ 없음 → `high_impedance`(v1.12.1 값 `w3_target`이 나오면 red) (e) **단단한 경로 위 W3 출력**(MOS 엣지로 레일에 닿는 W3 목표 출력 -- 출력–레일 diode 부하(gate = drain = 출력, source = 레일) 또는 gate = 레일·source = 출력인 소자; 두 끝이 F라 그 MOS는 `fixed_vgs` 종속(`writer_plan.py` 머리 6) -- v1.12.3 MF-1) → `kvl_fixed`(W3 출력을 일괄 고임피던스로 두면 red -- O-64 경우 1); 저항만으로 레일에 이어진 W3 출력은 분류 toy가 아니다 -- 기존 `dc_resistor_cycle` 정지가 먼저(기존 test) (f) **성분 안 다른 W3**: 출력 성분에 출력 아닌 W3 목표 노드만 있고 레일·선언 입력 DC가 없음 → `high_impedance`(그 W3를 F로 세면 `kvl_fixed` -- red) (g) 입력 DC 선언 회로에서 출력이 G_vgs로 입력 포트에 이어짐(입력 gate → source = 출력) → `kvl_fixed`, 같은 연결 입력 DC 미선언 → `high_impedance` (h) 넷·소자 이름 맞바꿈 toy에서 같은 값 (i) θ 무관: 서로 다른 θ 둘로 커널 평가한 스냅샷의 이 필드 `FieldValue.value_fp`·writer 블록 입력 버전이 같고 `dc_writer_plan` `computes` 증분 0(G-10) (j) 둘째 생산자 부재: `git grep`으로 이 필드의 `@compute_block` WRITES 자리 하나(`writer_plan.py`)와 권한표 행 하나(`s2_values.py` `DC_WRITES`의 `DC_WRITER_PLAN_WRITER` 행 -- v1.12.3 MF-3), `icm_config.py`·`window_refine.py`·`icm_front.py`에 G_vgs 성분 걷기·`_edges` 호출 0, `IcmConfig`에 `output_structure` 칸 없음 (k) **`_TIE` 부재**(v1.12.3 N-1): 입력 DC 미선언 두 입력 포트 가운데 하나만 출력 성분에 있고 다른 포트의 성분이 레일에 닿는 연결 → `high_impedance`(같은 DC 엣지로 두 성분을 이으면 `kvl_fixed` -- red).

**4.7-3b ICMR 측정 구성(사용자 결정 O-50 G4·O-52·O-53 A-1·A-2) -- 봉인 뒤 측정 구성 블록**(사용자 결정 O-58 S-1~S-3·O-59 (1), 계획 v6.21 N3.8 'ICMR 측정 구성'·'엔진 쪽 계산 자리'·'창 필드', N6.6 범위 1, 완료 조건 (8) (a)~(e)·(10) (a)~(e); 정의 정본 = 계획 N3.8 -- 인용만, 정의 사본 없음):
- **블록 `icm_config`**(새 `@compute_block`, writer 이름 `icm_config`(상수 `ICM_CONFIG_WRITER`), 파일 `E/metrics/icm_config.py`, 진입점 `icm_config_window`, test `E/tests/metrics/test_icm_config.py`(규칙 H)) = 계획 N3.8 '엔진 쪽 계산 자리'의 '봉인 뒤 블록 하나'. **자리**(W5): `E/metrics/ss_evaluate.py:101`(`ss_dev` 호출 -- 블록 정의 `E/metrics/ss_linearize.py:78`) 바로 뒤에 `ss_nodal` → `icm_config` 순으로 부른다(같은 `**keys` -- donors·counters). 호출 조건 = `metrics_aux` 호출 조건과 같음(`ss_evaluate.py:107` `if aux_requests or views` -- 그 조건 밖에서는 두 블록의 소비자가 돌지 않으므로 부르지 않는다). 등록 = `SS_WRITES`(`E/sizing/s2_values.py:173-179`)에 `(ICM_CONFIG_WRITER, (("node", "dc_window_cfg"), ("graph", "icm_config")))`. θ 프레임 창 `node.dc_window`(writer `dc_columns`, 소비자 `E/search/fd_jacobian.py:54-55`)는 바꾸지 않는다(O-58 S-1).
  - **READS** = `dc_columns`의 READS(`node.dc_v` 제외 -- 4.7-4 6과 같은 넷) + `("graph", "ss_nodal")`·`("node", "dc_window")`·`("device", "dc_op")`·`("device", "dc_tol_v")`(행 여유, 4.7-3a 1)·`("node", "dc_output_structure")`(출력 구조 -- 4.7-1a, READS만; v1.12.2)·`("node", "dc_writer")`(출력이 W3 목표 노드인지 -- `dc_columns` READS에 이미 있으면 그 원소 그대로) + S1 필드 `("device", "element_class")`·`("device", "kind")`·`("device", "pins")`·`("device", "dc_nets")`·`("device", "unsupported")`·`("node", "is_rail")`·`("node", "port_direction")`(writer `s1_structure`; DC 되먹임 판정 입력 -- v1.12.6, `device.unsupported`는 v1.12.7(계획 v6.28 완료 조건 (10)(f), O-85 (3)), `device.element_class`는 v1.12.7 셋째 커밋(O-88, MOS 식별); 이미 있는 원소는 그대로). extras = `dc_window_refine`과 같은 넷(θ 성분, `fixed_values`, `resistor_values`, LUT, 선형 선언 소자) + spec 되먹임 선언(`human.feedback.elements` 로드 결과, `E/authoring/spec_elements.py:118` -- 커널 컨텍스트에 그 값이 있는 자리는 착수 때 확인, 없으면 멈추고 보고).
  - **WRITES** = `("node", "dc_window_cfg")`(**측정 구성 판정 창** -- 계획 N3.8 '창 필드'의 새 필드 이름, 입력 포트마다, 값 꼴 = `node.dc_window`와 같은 `Window` 하나, +tol_VDsat; **모든 측정 구성에서 쓴다**(`as_is_single_input` 포함 -- 4.7-2, v1.12.1 W1 철회), 구성 None이면 쓰지 않음; 자기 측정 실패 꼴 = `Window(None, None, 0, input_status="unmeasured")`) · `("graph", "icm_config")`(값 `IcmConfig` -- 새 frozen dataclass, `E/metrics/aux_types.py`, 칸 = `config`·`inverting_port`·`tied_ports`·`transfer`·`undefined`: `config` ∈ {`"declared_feedback"`, `"follower_beta1"`, `"as_is_single_input"`} 또는 None, `inverting_port`: str 또는 None, `tied_ports`: tuple[str](구성이 출력에 묶은 입력 포트), `transfer`: tuple[(port, T_p, resolution)](resolution = δA_num(V/V) -- v1.12.4, 아래 '판정 분해능 정의 함수 하나'; 반전 입력 식별 근거 -- **출력 전용 칸**: 엔진 소비자 없음, 결과 JSON·변화표만 읽음, 계획 N6.6 완료 조건 (5) '출력 전용 선언'), **출력 구조 분류 칸 없음**(v1.12.2, 사용자 결정 O-64 (1) -- v1.12.1의 `output_structure` 칸(이 블록이 평가마다 출력 writer 사슬로 분류, 값 `high_impedance`·`w3_target`·`kvl_fixed`)을 삭제: 분류는 θ 무관 S0 필드 `node.dc_output_structure` 하나이고 writer는 `dc_writer_plan` 하나다 -- 4.7-1a; 이 블록은 READS로 읽기만 하고 다시 분류하지 않는다(둘째 생산자 금지)), `undefined`: tuple[`Undefined`]). **옛 `kvl` 칸(포트별 KVL 선형 감도 끝)은 두지 않는다**(사용자 결정 O-61 P3 -- **원래 취지와 다름, 승인 O-61 P3**; 같은 정의의 양 두 칸 금지, graph 단일 정본 규칙 3): KVL 고정 포트의 끝은 `node.dc_window_cfg` 한 칸에만 있다. **정의 창 `node.dc_window_def`**: writer 자리 = 이 블록(계획 N3.8 '창 필드' -- 권한표에 writer 배정), 값은 card DE-1 (a)가 이 블록에 정의 기준을 더할 때 쓴다 -- IT-2는 쓰지 않는다(생산자만 있고 소비자 없는 칸을 만들지 않는다; 계획 같은 문단 'DE-1 (a)가 그 블록에 정의 기준을 더함').
  - **소비자**(새 필드마다 ≥ 1 -- 계획 N6.6 완료 조건 (5)): `node.dc_window_cfg` → 커널 ICMR 선언 제약 판정·커널 `icm_margin_v`(4.7-5 커널 갈래의 창 출처를 `node.dc_window`에서 이 필드로 바꾼다 -- 계획 완료 조건 (1) '커널 `icm_margin_v`는 측정 구성 판정 창에서')·`dc_window_refine`의 출발 창(4.7-4 1, DE-1 전 -- 사용자 결정 O-61 P6)·`metrics_icm_front`의 KVL 고정 포트 값(4.7-5 front -- O-61 P3); `graph.icm_config` → `dc_window_refine`(4.7-4, READS 추가 -- 반전 입력 식별·`tied_ports`·`config`를 읽는다)·`metrics_aux`(구성 None 갈래 `undefined` -- 4.7-5 M7 경로)·`metrics_icm_front`(구성 None 갈래 -- 포트별 출처는 다듬은 창 항목 유무로 정한다, 4.7-5 front; v1.12.2에서 `output_structure` 읽기 삭제)·이 블록과 `dc_window_refine` 안의 P3 묶음(θ 프레임 `node.dc_window`는 측정 구성이 없어 묶음 = 선언 포트 전부). 보고 'β = 1 기본' 표기는 같은 스냅샷의 `graph.icm_config.config`를 직접 읽는다(`IcmWindow`에 사본 칸 없음 -- v1.12.1 M6).
  - **계산(한 연립 -- 계획 N3.8 '한 연립에서 함께 계산')**: (1) **반전 입력 식별**(O-53 A-1): 선언이 있으면 선언이 정한다. 없으면 `graph.ss_nodal`의 인수분해로 입력 포트 p마다 DC 전달 T_p(구동 = p에 1, 나머지 고정 0, `nodal_solve` -- 봉인점 컨덕턴스 계 = DC 극한 전달과 같은 계)를 재고 T_p < 0 후보가 하나이고 |T_p| > δA_num(계획 v6.24 N3.8 '판정 분해능의 정의 자리' 인용 -- 정의 함수 아래 '판정 분해능 정의 함수 하나', v1.12.4: 옛 문언 '`nodal_solve` 상대 잔차를 T_p에 전파한 폭'은 무차원 상대 잔차라 폐기 -- O-68 (1)·O-71)이면 그 포트. 후보 0개 → `icm_inverting_port_none`, 2개 이상 → `icm_inverting_port_ambiguous`, |T_p| ≤ 분해능 → `icm_inverting_port_unresolved`, 차동 출력·선언 없음 → `icm_config_differential_output_undeclared`(모두 category `definitional`, 4.7-5 `Undefined`). 4.7-1a 멈춤 S-OS1·S-OS2의 실행 중 code `icm_config_output_root_w3`·`icm_config_differential_output_structure`도 `definitional`이고 같은 경로(`config` None → M7)다(v1.12.3). 포트 role 이름은 읽지 않는다. 입력 하나 = `"as_is_single_input"` -- 그 구성의 창은 아래 (5). **선언 되먹임의 DC 되먹임 판정**(v1.12.6 -- 정의 정본 = 계획 v6.27 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나', 사용자 결정 O-81 (2)·O-82·O-83, 인용만; v1.12.5의 소자 kind 판정(`DC_CONDUCTING_PASSIVE_KINDS` 유무)을 대체): 선언 소자가 하나 이상이면 측정 구성 선택·T_p·어떤 풀이보다 먼저 이 판정을 한다(계획 N3.8 '순서'). **설계**(`icm_config.py` 비공개 함수 하나 `_dc_feedback_reaches(view, output, cut_nets) -> bool | None`(출력 넷 하나 -- v1.12.7 둘째 커밋, 검증 MF-2), 이름은 design -- 계획 완료 조건 (10)(f)): (가) 입력 = 블록 READS의 S1 필드 일곱 `device.element_class`·`device.kind`·`device.pins`·`device.dc_nets`·`device.unsupported`·`node.is_rail`·`node.port_direction`(writer `s1_structure`, `E/graph/s1_structure.py:56-57·63-65·69·73-75·79·82`) -- 투영 안 읽기라 입력 버전에 든다, `ctx.base` 직접 읽기 0 (나) 방향 의존 그래프(마디 = 넷): `device.dc_nets`가 있는 원소(= `dc_edges_unpruned`의 DC 전도 엣지 -- 용량은 `dc_nets` None이라 엣지 아님, 저항을 kind 이름으로 고르지 않음) 중 이상 전류원(`device.element_class == ELEMENT_SOURCE and device.kind == CURRENT_SOURCE` -- 증분 컨덕턴스 0이라 엣지 아님; 같은 술어 선례 `E/metrics/ss_circuit.py:57`, import `:19` `from gmid_engine.sizing import CURRENT_SOURCE`(정의 `E/sizing/s2_values.py:22`); 재사용 helper는 없고 같은 술어가 `ss_circuit.py:57`·`E/sizing/current_basis.py:90`·`E/sizing/kernel_context.py:80`에 각자 같은 상수로 쓰여 있어 이 함수도 같은 상수 `ELEMENT_SOURCE`·`CURRENT_SOURCE`로 쓴다 -- `CURRENT_SOURCE`는 kind 어휘라 `SUPPORTED_*_KINDS` 튜플이 아님; v1.12.7 넷째 커밋)을 뺀 원소는 `dc_nets` 두 넷 사이 양방향(MOS는 drain↔source), MOS(= S1 정본 필드 `device.element_class == ELEMENT_MOS`(`"mos"`, `E/graph/s1_values.py:22`; writer `s1_structure`, `E/graph/s1_structure.py:63·73`)인 원소를 READS로 읽음 -- 같은 용도의 선례 `E/metrics/dc_metrics.py:40` READS·`E/metrics/achievability.py:108`; kind 상수로 고르지 않음; v1.12.7 셋째 커밋, 사용자 결정 O-88)는 gate→drain·gate→source 한 방향 -- 단자 넷은 `device.pins`에서 공개 `MOS_TERMINAL_NAMES`(d, g, s 순)로 얻는다(`device.pins`는 단자 넷 조회에만; 구조 규칙 C -- `ELEMENT_MOS`·`MOS_TERMINAL_NAMES`는 `gmid_engine.graph` 공개 export, `E/graph/__init__.py:71·95·243·271`, metrics 쪽 import 선례 `E/metrics/dc_metrics.py:28`) (다) **지원 밖 원소**(v1.12.7 -- 계획 v6.28 N3.8 '지원 밖 원소', 사용자 결정 O-85 (3)): S1 `device.unsupported`(값 = 분기 이름, `E/graph/CONTRACT.md:154`)가 있는 원소가 하나라도 있으면 None(판정 불능 -- 이상 전압원은 그 하나). 그 필드를 READS로 읽을 뿐 kind 목록으로 다시 판정하지 않는다(v1.12.6의 `MOS_KINDS`·`SUPPORTED_*_KINDS` 대조는 둘째 계산이라 삭제). 엔진 운영 경로에서는 그 전에 S1 `s1_dc_conduction`이 같은 분기 이름으로 멈춰 도달하지 않는다(`E/graph/CONTRACT.md:394`) -- test는 합성 스냅샷으로 블록을 부른다 (라) 끝점 = 선언 절단 넷 = 선언 소자마다 아래 '절단 넷 순수 함수'(단자 넷 = 그 소자 `device.pins`의 두 넷, 입력 포트 넷 = `node.port_direction == "input"`인 넷)가 낸 길이 1 튜플의 넷 (마) 출발 = 인자 `output` 넷 하나(`node.port_direction == "output"`인 넷)에서 BFS; 경유 금지 = `node.is_rail` 넷과 절단 넷 아닌 입력 포트 넷(끝점은 예외) -- 절단 넷에 닿으면 True, 아니면 False (바) **자체 BFS를 쓰는 이유**(v1.12.7 다섯째 커밋, 사용자 결정 O-89 (3) -- 근거 adopted_fix_audit.md A3): 기존 helper는 이 그래프와 정의가 달라 쓰지 않는다 -- `graph.dc_segments`(`E/graph/dc_conduction.py:54`)는 단계 2에서 레일·포트 아닌 넷 중 DC 엣지가 저항 하나뿐인 넷을 가지치므로(`dc_conduction.py:12-14`, gate는 DC 엣지가 아님) gate만 붙은 내부 넷과 그 g→d 경로를 잃는다; `signal_reach`(`E/graph/signal_reach.py:39`)는 커패시터를 포함하는 AC 도달성(같은 파일 docstring 규칙 (c))이라 쓰면 DC/AC 분리가 깨진다; `stage_bfs`(`E/graph/stage_bfs.py:86`)는 AC 셀 비용 0-1 BFS이고 `composite_diode._walk`(`E/graph/composite_diode.py:60`)는 DC 전류 단자가 정확히 둘인 직렬 가지만 걷는다. 비용 = 평가마다 넷 수 N에 O(N) BFS 한 번, 새 cache·memo 없음(재사용은 graph reuse가 덮음), 결과는 `IcmConfig.config`·`undefined`로만 남는다(새 칸 없음); `config`·T_p를 읽지 않는다. **갈래**: 단일 출력에서 판정 False → `config` None, 정의 불능 `icm_config_feedback_no_dc`(code 이름 v1.12.5 그대로, `definitional`, 사유 기록 -- fail-closed; 4.7-1a 멈춤 code와 같은 경로 `config` None → M7, `node.dc_window_cfg` 항목 없음, 쓰기는 이 블록의 `graph.icm_config` 하나); 판정 None → `config` None, `icm_config_feedback_element_unsupported`(code 이름 = 계획 v6.28 N3.8, O-85 (3); `definitional`, 같은 경로); True → 아래 S-3 선언 구성(`declared_feedback`). **IT-2c 갈래 순서**(v1.12.7 둘째 커밋, 사용자 결정 O-87 (1) -- 계획 v6.28 (10)(f)·O-67 (5)): 차동 출력 + 비지 않은 선언 → 먼저 멈춤 S-OS2 code `icm_config_differential_output_structure`(지금처럼 fail-closed, 이 판정을 부르지 않음); 그 밖(단일 출력 + 비지 않은 선언) → ① 지원 밖 원소 → `icm_config_feedback_element_unsupported` ② 단일 출력 경로 판정 False → `icm_config_feedback_no_dc` ③ True → 측정 구성 선택(S-3 `declared_feedback`). **차동 출력의 결합은 S-OS2 일반형 card 몫**(정의 = 계획 v6.28 N3.8 '차동 출력', 사용자 결정 O-85 (1)·O-86 N3: 출력마다 이 함수를 `output` 인자로 한 번씩 부르고 두 판정이 같을 때만 그 판정, 갈리면 정의 불능 -- code 이름 `icm_config_feedback_outputs_split`은 그 card용으로 예약, IT-2c는 쓰지 않음; 갈림 toy는 그 card가 오라클 (x)(한 출력이 MOS d↔s로 레일에만 닿음)·(xi)(CMFB 저항 대조) 꼴을 쓴다 -- 검증 N-1; v1.12.7 첫 커밋의 IT-2c 범위 확대 철회, O-87 (1)). 두 정의 불능 갈래의 `IcmConfig` 나머지 칸(v1.12.6 검증 N3 -- 계획 N3.8 '선언이 있을 때 반전 입력 = 이 절단 넷'): `inverting_port` = 절단 넷의 입력 포트, `tied_ports` = ()(구성이 없어 묶은 포트 없음), `transfer` = 선언 갈래처럼 T_p를 재지 않음(빈 값). **code 순서**(검증 N3): 이 판정은 측정 구성 선택 전이라(계획 N3.8 '순서') False·None이면 S-OS1(`icm_config_output_root_w3`)·`icm_config_feedback_cut` 갈래까지 가지 않는다 -- `undefined`는 code 하나. 차동 출력 + 선언은 위 'IT-2c 갈래 순서'대로 S-OS2 code이고, S-OS2 card는 같은 함수를 부른다(둘째 구현 금지). 선언 소자 0개(빈 목록 = β=1 루프, `E/authoring/spec_elements.py:19-20`)는 이 판정을 하지 않는다(미선언·β=1 갈래). **입력이 하나이면 `as_is_single_input`이 이 판정·갈래보다 먼저다**(계획 O-80 R2 -- 아래 '(5)가 (3)보다 앞선다'와 같은 순서, 동작 변화 0). 해당 회로 0개(13회로, 계획 N3.8), 생기면 계획부터(S-7). **절단 넷 순수 함수**(v1.12.6 -- 계획 N3.8 '절단 넷 규칙은 순수 함수 하나', 사용자 결정 O-83 R-M1·R-N1): `E/authoring/_feedback_cuts.py`에 `feedback_cut_nets(terminals, input_nets) -> tuple[str, ...]`(소자 두 단자 넷 × 입력 포트 넷 집합 → 입력 포트 넷에 물린 단자 넷, 단자 순서·중복 유지; 길이 1 = 그 넷이 절단 넷, 0 = `feedback_element_not_on_input`, 2 = `feedback_cut_ambiguous` -- 옛 `input_terminal_nets` docstring 규칙 그대로), `gmid_engine.authoring`에서 공개 export(`DC_CONDUCTING_PASSIVE_KINDS`와 같은 꼴). 직접 호출 자리 넷: `spec_elements.py:104`·`spec_views.py:101`(topology에서 이름으로 소자를 찾아 단자 넷을 넘김 -- 이름이 없으면 옛 반환 None과 같은 갈래를 호출부가 낸다), `icm_config`(위 (라)), `noise_plan.py:48`(`ss.nodes[element.a]`·`ss.nodes[element.b]`, `ss.input_nets`; 길이 1이 아니면 옛 `_input_side`의 None과 같은 `CODE_CUT_AMBIGUOUS`). `def input_terminal_nets`(`_feedback_cuts.py:11`)·`def _input_side`(`noise_plan.py:28`)는 같은 변경에서 지우고 래퍼를 남기지 않는다(둘째 이름 금지). 함수 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`)에 같은 변경에서 행 둘(절단 넷 순수 함수, DC 되먹임 판정 개념 행). 동작 동일성 test = L10 (i). (2) **follower 행**(출력의 `node.dc_output_structure == "high_impedance"`(4.7-1a)이고 출력 또는 그 G_vgs 성분 뿌리가 W4): `_helpers_dc_solve.Circuit`의 θ 고정 선형 연립(4.7-3 1과 같은 행렬)에서 그 W4 뿌리 행을 V_out = x(s_out = 1)로 바꾼 같은 연립(우변 둘 -- 계획 N3.8 '엔진 θ 고정 손계산 근거'), 묶인 반전 입력은 x로 훑지 않는다(O-53 A-2 -- `tied_ports`). (3) **KVL 고정 출력 감도 연립**(출력의 `node.dc_output_structure == "kvl_fixed"` -- 4.7-1a, 계획 N3.8 '출력 구조 분류 -- 규칙 하나'(O-64 (1)이 옛 O-43 D3 문언 대체), 출력이 W3 목표 노드여도 같음; 정본 하나, 사용자 결정 O-58 S-2): 봉인점 DC 방정식(부하 포함 KCL) 1차 감도 = `graph.ss_nodal`의 G에 follower 행 V_out = x를 더한 계. 반전 입력 노드 전압 u를 미지수로 두고, 같은 인수분해로 두 해(x만 1인 구동 v_x, u만 1인 구동 v_u -- `nodal_solve` 두 번)를 낸 뒤 스칼라 하나로 닫는다(follower: u = V_out(v_x·x + v_u·u); 선언 저항 되먹임: 반전 입력 노드 KCL 행 G[inv,:]·v = 0) -- 새 인수분해·새 풀이기 없음(Schur 보완 1칸). DE-1 (b) KVL 고정 출력 스윙은 이 연립을 구동만 바꿔(차동 훑기, follower 행 없음) 재사용한다(사본 금지; 진입점은 같은 파일의 공개 함수 `kvl_sensitivity(nodal, drive, closure)` -- DE-1 design이 인용). (4) **영역 경계 행과 창 끝 = `saturation_window` 호출**(사용자 결정 O-61 P2 -- 계획 N6.6 완료 조건 (2) '창 끝을 내는 함수는 `saturation_window` 하나, 부르는 자리 셋'; 이 블록은 끝 식을 다시 쓰지 않는다): `region_rows`(4.7-3a)로 행을 세우고 `saturation_window`를 부른다 -- 고임피던스 follower((2))는 `roots`에 쌍 `(W4 뿌리, 출력)`을 넣어 그 뿌리 행을 s_out = 1로 바꾼 같은 연립을 `saturation_window` 안 감도 풀이가 푼다(4.7-3 2 서명의 `roots` 원소 꼴); KVL 고정((3))은 `kvl_sensitivity`가 낸 감도를 키워드 `slope`로 넘겨 `saturation_window`가 감도 연립을 다시 풀지 않고 끝만 낸다(감도 연립 정본 = `kvl_sensitivity` 하나, 끝 식 정본 = `saturation_window` 하나 -- 둘째 생산자 없음). 포트 창은 반환 (dlo, dhi, slope)에서 4.7-3 2의 호출자 규칙(P2 [min, max] ∩ 레일)으로 만들고, P3 묶음 = 선언 포트 − `tied_ports`. KVL 고정 구조는 커널·다듬은 창 모두 이 선형 감도 끝이다(계획 N3.8) -- 그 정본 칸은 아래 '선형 감도 끝만 정의되는 구성의 정본 칸'. 출력이 `high_impedance`이고 출력 자신이 W3 목표 노드(출력의 `node.dc_writer` tier W3 -- READS)이면 (2)와 같은 θ 고정 연립에서 `roots = (출력,)`(그 목표값을 x로 -- 계획 N3.8 규칙 하나 '출력이 W3 목표 노드이면 그 목표값을 x로 바꾼다'; W3 여부는 `node.dc_writer`가 정본이라 분류 필드에 `w3_target` 표지를 두지 않는다 -- 같은 사실 두 칸 금지). `high_impedance` 출력의 writer 사슬 뿌리가 출력 아닌 W3 목표 노드인 갈래는 **멈춤 S-OS1**(4.7-1a -- 일반형은 구현하지 않고 실행 중 fail-closed code `icm_config_output_root_w3`). (5) **`as_is_single_input`**(계획 N3.8 '단일 입력 회로는 회로 그대로가 구성이다'·O-25 (2) '출력은 회로가 정하는 대로 따름' -- v1.12.1, W1 철회): follower 행·닫음 없이 출력이 회로 자신의 DC 관계로 따르는 계 = `graph.ss_nodal`의 G 위 (3)과 같은 연립을 **구동만 입력 포트(x만 1)로 바꿔** `kvl_sensitivity`가 푼 감도(새 연립·새 풀이기 없음 -- (3)과 같은 정본, DE-1 (b)와 같은 재사용 꼴), 끝 = 그 감도를 `slope`로 넘긴 `saturation_window`. 결과는 `node.dc_window_cfg`에 쓴다(θ 프레임 `node.dc_window`와 다른 양 -- 4.7-2). 이 구성의 포트는 아래 '선형 감도 끝만 정의되는 구성의 정본 칸'을 따른다(사용자 결정 O-63 (4) -- 다듬은 창 블록은 쓰지 않음). **입력이 하나이면 (5)가 (3)보다 앞선다**(v1.12.3 gap N3 -- 계획 N3.8 '단일 입력 회로는 회로 그대로가 구성'; (3)은 반전 입력 u로 닫히는 연립이라 단일 입력에는 없다. 단일 입력 `kvl_fixed` 출력도 (5)로 잰다 -- 두 갈래 모두 `kvl_sensitivity` 재사용).
  - **판정 분해능 정의 함수 하나**(v1.12.4, 계획 v6.24 N3.8 '판정 분해능의 정의 자리'(576행) -- 정의 정본 = 계획, 인용만; 사용자 결정 O-71·O-68 (1)·O-67 (3)): 판정 = |A|·(V_rail,max − V_rail,min) ≤ δV_out이면 판정 불능, 엔진 δV_out = |z_u|ᵀ|r|(V). **함수** = `_transfer_resolution(system, volt, sense, injection=None) -> float | None`(δV_out, V) -- 파일 `E/metrics/icm_config.py` 안 비공개 함수 하나(IT-2에서 부르는 자리 = 이 블록의 T_p 판정 하나). 계산(블록 안 지역 계산, 새 필드·생산자·상수 없음 -- 계획 '같은 호출 안에서 다시 만든다'): (i) r = `coupling @ volt − inject[unknown]`(A) -- `nodal_factor`가 `coupling = g[unknown, :]`(전체 열, `E/metrics/_helpers_nodal.py:43`)을 돌려주고 `nodal_solve`가 `rhs = inject[unknown] − coupling @ volt`(고정 노드 항, `:65`)·`volt[unknown] = x`(`:67`)로 푸므로 `coupling @ volt`(풀린 전체 전압) − `inject[unknown]` = G_uu·x̂ − rhs와 같다 (ii) z = `nodal_adjoint(system.factor, len(system.nodes), sense)`(`:73-82`, z[unknown]만 값 -- V/A) (iii) δV_out = Σ |z[unknown]|·|r|. `volt`·`z`가 None(특이)이면 None. **구동** = 레일 폭: T_p 판정은 `nodal_solve(system.factor, size, {p: span})`(`:52-70`, 반환 (전압, 상대 잔차) -- 상대 잔차 스칼라는 쓰지 않음) **한 번**으로 V_out = sense·volt를 얻고 T_p = V_out / span, 판정 |V_out| ≤ δV_out(⇔ |T_p| ≤ δA_num = δV_out / span) -- 전달 풀이와 분해능이 같은 해를 쓰므로 풀이 추가 0, z는 출력(sense)마다 한 번 풀어 모든 포트에 쓴다. span = `node.dc_rail_v`(writer `dc_rails`, `E/sizing/s2_values.py:144`; 이 블록 READS = `dc_columns` READS에 이미 있음 `E/sizing/block_columns.py:83`)의 레일 값 최대 − 최소(선언 `supplies_v` 정본 -- `E/sizing/dc_inputs.py:5`, DEC-60). sense = 출력 노드 단위 벡터(`system.nodes` 색인), 차동 출력이면 e_p − e_n(계획 같은 문단 -- IT-2에서는 차동 출력이 멈춤 S-OS2·`icm_config_differential_output_undeclared`로 이 판정 전에 끝나므로 쓰이지 않음). **기록** = `IcmConfig.transfer`의 resolution 칸 = δA_num(V/V, 포트마다; 출력 전용 -- 계획 '기록 자리'). **fail-closed**: span = 0 또는 레일 값 없음 → `icm_inverting_port_unresolved`(detail `(("rail_span", span),)`), 특이(None) → 같은 code(detail `(("singular", True),)`) -- 새 code 없음, N3.14 적용. **자리 근거(실현 가능성)**: 계획이 지목한 기존 함수(`nodal_solve`·`nodal_adjoint`)는 `E/metrics/_helpers_nodal.py`에 있으나 그 파일은 `_` 모듈이라 구조 규칙 A 보충 (3)(`E/tests/structure/README.md:39` -- 공개 함수마다 같은 하위 패키지의 다른 파일 2개 이상이 import)을 받는다; IT-2의 호출 자리는 하나(`icm_config`)라 거기 공개 함수로 두면 규칙 A가 FAIL한다. 그래서 IT-2에서는 호출 자리 파일 안 비공개 함수 하나로 두고, **card DE-1 (c)가 DEC-23 A_dc 갈래에서 둘째 호출 자리를 더할 때 같은 변경에서 `_helpers_nodal.py`의 공개 함수로 옮긴다**(이동이지 둘째 정의가 아님 -- 정의 하나는 늘 하나; 4.7-9 DE-1 인계 (8)). **미확인**(계획 N6.6 'IT-2c 착수 실측', 사용자 결정 O-71): 대표 회로 값(`current_reuse_telescopic_ota` 봉인점 T_p·δA_num), 진짜 A = 0 대칭 사례의 갈래 발동, 오라클 실제 vntol·reltol -- 4.7-9 착수 실측 목록; 근거 실측 `_drafts/evidence/2026-10-21/dvout_feasibility.md` §3·§4는 이 design이 다시 재지 않았다(미확인).
  - **선형 감도 끝만 정의되는 구성의 정본 칸**(옛 이름 'KVL 고정 포트의 정본 칸'; 계획 N3.8 같은 이름, 사용자 결정 O-61 P3 -- **원래 취지와 다름, 승인 O-61 P3**: 옛 문언 '두 필드가 공유'를 대체, 취지 '정본 하나·재계산 0'은 그대로; **대상 일반형**, 사용자 결정 O-63 (4) -- KVL 고정 출력 구조((3))와 `as_is_single_input`((5))의 포트, 아래 'KVL 고정 포트'는 두 구성의 포트를 함께 가리킨다): (3)·(5)의 연립은 이 블록이 평가마다 한 번 풀고, 그 끝은 `node.dc_window_cfg` **한 칸에만** 쓴다(`graph.icm_config`에 `kvl` 칸 없음, `node.dc_window_def_refined`에 그 포트 항목 없음 -- 같은 정의의 양 두 칸 금지). 출력의 `node.dc_output_structure == "kvl_fixed"`이거나 `graph.icm_config.config == "as_is_single_input"`이면(이 판정 자리 = `dc_window_refine` 하나 -- 4.7-4 2 (b)) `dc_window_refine`은 그 평가의 **입력 포트 전부**를 쓰지 않고(끝 풀이 호출 0 -- 4.7-4 2 (b); 측정 구성이 출력에 묶은 반전 입력 u = V_out도 같은 연립의 해라 같은 칸이 정본이다 -- 계획 N6.6 범위 1 'KVL 고정 출력 구조는 커널·다듬은 창 모두 … 선형 감도 끝 -- 그 끝은 `node.dc_window_cfg` 한 칸에만 쓰고 다듬은 창 블록은 그 포트를 쓰지 않으며'는 구조 단위 문언; v1.12.1 검증 M2), front 판정·보고는 그 포트에서 `node.dc_window_cfg`('추정')를 읽는다(4.7-5 front). 정밀 값은 oracle SPICE 다리(`.dc` 훑기)가 재고, 엔진에 전체 DC 끝 풀이를 새로 만들지 않는다(O-63 (4), O-32 순풀이 금지). 이 구조에서 다듬은 창은 판정 창과 같은 정의·같은 정밀도(선형 감도 끝, '추정')·같은 기준(+tol, DE-1 전)의 양이라 따로 둘 칸이 없다(계획 같은 문단). DE-1 뒤 이 포트의 정의 기준 값은 이 블록이 쓰는 `node.dc_window_def` 한 칸이다(card DE-1 design 몫 -- 계획 같은 문단). 고임피던스 follower이면 `dc_window_refine`이 끝 x 고정 풀이에 그 W4 y를 V_out = x가 되게 정한 1변수 풀이를 더한다(계획 N3.8 '엔진 θ 고정 손계산 근거'). 출력 자신이 W3 목표 노드인 고임피던스 출력이면 끝 x 고정 풀이에서 그 목표값 자리(`fixed_values[출력]`)에 x를 넣어 푼다(계획 N3.8 규칙 하나 '그 목표값을 x로 바꾼다' -- 1변수 풀이 없음, v1.12.3 gap N2).
  - **커널 상태 이어받기**(계획 N6.6 범위 1 '커널 창 되풀이 미수렴', 사용자 결정 O-61 P5 -- 동작 변경, 승인 O-61 P5; F 성분 미선언 포트는 O-61 P4 (b)): 이 블록은 READS의 `node.dc_window`(커널 θ 프레임 창, writer `dc_columns`)에서 상태만 읽어 `node.dc_window_cfg`의 상태 칸 `input_status`에 싣는다(새 칸·새 필드 없음 -- '상태를 나르는 칸 = 기존 창 필드의 상태 칸'). (가) **미수렴**: 그 평가의 `node.dc_window` 입력 포트 항목 가운데 하나라도 `input_status == "unsettled"`이면(4.7-3 1 A6 b·c, 4.7-3 3 tol 미정) 그 평가점의 모든 `node.dc_window_cfg` 항목을 `input_status="unsettled"`로 쓴다 -- 측정 구성 창은 그 커널 해(미수렴 되풀이의 마지막 풀이)에서 잰 값이라 같은 점의 상태를 따른다(계획 '그 평가점의 측정 구성 판정 창도 미수렴 상태를 이어받으며'). `lo`·`hi`는 이 블록이 잰 값 그대로 두되(진단) metric은 그 상태로 정의 불능이다(4.7-5 `input_window_unsettled`). W4 y 범위는 `node.dc_window` 그대로 쓰인다(탐색 불변). (나) **F 성분 미선언 포트**: 그 포트 항목을 `Window(None, None, 0, input_status="f_component_undeclared")`로 쓴다(그 포트의 창을 재지 않는다 -- 4.7-3 3). (다) `"op_mismatch"` 점은 봉인 거부라 이 블록이 돌지 않는다(4.7-3a 3). 커널 뿌리 `"unmeasured"`(4.7-3 4 -- θ 프레임 측정 실패)는 이어받지 않는다: 이 블록은 자기 연립으로 재고, 자기 측정이 실패하면 `Window(None, None, 0, input_status="unmeasured")`를 쓴다(4.7-2). (라) **우선순위**(v1.12.1 N3): 한 포트에 (가)·(나)가 겹치면 definitional 상태(`"f_component_undeclared"`)가 numeric 상태(`"unsettled"`)보다 앞선다(4.7-2 '상태 우선순위'). 모든 구성(`as_is_single_input` 포함)에서 같다.
  - **S-3 선언 되먹임 DC 망**(사용자 결정 O-58 S-3): DC 망 = 선언 소자를 끊지 않은 봉인점 회로 = `ss.circuit` 그대로(선언 소자는 topology 수동소자 -- 저항은 G에 들어가고 용량은 `conductance_matrix`가 넣지 않는다, `E/metrics/_helpers_nodal.py:26-28`); 반전 입력 노드의 KCL은 (3)의 스칼라 닫음으로 더한다(follower 행 없음). 단일 출력에서 위 (1) DC 되먹임 판정이 없음(False)·판정 불능(None)이면 이 망을 세우지 않는다 -- `icm_config_feedback_no_dc`·`icm_config_feedback_element_unsupported` 갈래(v1.12.6·v1.12.7; v1.12.5 kind 판정 대체). 봉인점 해가 그 소자를 절단한 해이면 정의 불능 `icm_config_feedback_cut`(새 code, `definitional`, 사유 기록 -- fail-closed). 착수 실측(순서 0, 완료 조건 (10) (a)): spec 루프 절단(`E/authoring/spec_elements.py:19-22`)이 쓰기 계획·봉인점 망에 적용되지 않음을 잰다 -- 적용되면 **멈추고 보고**.
- **ss 층 필드 `graph.ss_nodal`**(사용자 결정 O-59 (1) -- 봉인점 컨덕턴스 계·인수분해 = ss 층 graph 필드 하나, writer 하나): 새 `@compute_block`, writer 이름 `ss_nodal`(상수 `SS_NODAL_WRITER`), 파일 `E/metrics/ss_nodal.py`, 진입점 `ss_nodal_system`, test `E/tests/metrics/test_ss_nodal.py`. READS = `metrics_aux`의 회로 조립 투영 열(`E/metrics/metrics_aux.py:95-105` -- 회로는 그 조립 함수를 import해 만든다, 사본 없음). WRITES `("graph", "ss_nodal")`, 값 `NodalSystem`(새 frozen dataclass, `E/metrics/aux_types.py`: `nodes`(정준 순서 tuple -- 크기 = `len(nodes)`, 따로 칸 없음), `fixed`(frozenset[int] = ac 접지 ∪ 입력 넷), `g`(읽기 전용 ndarray), `factor`(`nodal_factor` 튜플 -- `E/metrics/_helpers_nodal.py:36`)). 호출 자리·조건 = 위 `icm_config` '자리'(W5 -- `ss_evaluate.py:101` 뒤, `icm_config` 앞), 등록 = `SS_WRITES`(`E/sizing/s2_values.py:173-179`)에 `(SS_NODAL_WRITER, (("graph", "ss_nodal"),))`.
  - **READS 지문**(계획 v6.21 재검증 Info): 블록 입력 버전 = `fp_of((name, code_hash, projection.fp))`(`E/core/compute_block.py:129-132`), projection 지문은 읽은 필드의 `FieldValue.value_fp`(= `fp_of(value)`, 쓰기 때 한 번 -- `E/core/field_value.py:19`)에서 온다. ndarray·LU 튜플은 `fp_of` 정준 직렬화 규칙 밖(`E/core/fingerprint.py:80-83` `TypeError`)이므로 `NodalSystem.__canonical__` = `(nodes, tuple(sorted(fixed)), g.shape, g.dtype.str, g.tobytes())`(I1 -- 바이트 해석을 정하는 dtype 포함)로 둔다 -- 인수분해(`lu`·`piv`·`coupling`·`floating`)는 (g, fixed)와 writer 코드 해시의 결정적 함수라 지문에 넣지 않는다(같은 (g, fixed) → 같은 인수분해, 결정성 비트 동일 -- 계획 완료 조건 (6)). 그래서 READS 하는 블록(`icm_config`·`metrics_aux`)의 입력 버전은 G·고정 집합이 바뀔 때만 바뀐다. 불변성(W4): `g`와 `factor`의 모든 ndarray(`unknown`·`lu`·`piv`·`coupling`)는 `writeable=False`, `floating`은 tuple -- test 단언 L10 (f)(배열마다 `flags.writeable is False`, 제자리 쓰기 시도가 `ValueError`; **red 먼저** -- `writeable=False` 설정을 뺀 변형에서 단언이 실제로 FAIL함을 확인한 뒤 통과를 본다). `require_immutable`(`E/core/immutability.py`)이 이 값을 받는지도 같은 test가 쓰기 경로로 잰다.
  - **고정 집합 하나의 전제**: 세 자리의 `fixed` = `view_system`(`E/metrics/_helpers_view.py:23`)의 ac 접지 ∪ 입력 넷 ∪ 구동 쌍 넷. 착수 실측: library 9회로·toy에서 구동 쌍 넷 ⊆ ac 접지 ∪ 입력 넷(그러면 `fixed`가 뷰와 무관 -- 필드 하나). 아니면 **멈추고 보고**(뷰별 인수분해 여럿은 계획이 정하지 않았다).
  - **세 자리 이전(IT-2 범위, 같은 변경 -- 둘째·셋째 생산자 제거)**: `E/metrics/offset_analysis.py:69`·`E/metrics/offset_systematic.py:46`·`E/metrics/block_residual.py:73`의 `nodal_factor(conductance_matrix(ss.circuit, size), fixed)`를 `NodalSystem.factor` 읽기로 바꾸고(세 함수는 `metrics_aux` 블록 안에서 불린다 -- import 자리 `E/metrics/metrics_aux.py`), `metrics_aux` READS에 `("graph", "ss_nodal")`를 더한다. 전회로 조립 `conductance_matrix(ss.circuit` 자리 = `ss_nodal` 하나(완료 조건 (10) (c) `git grep`). `block_model.py:91, :112`·`ff_gm_ratio.py:55`의 조립은 블록 국소 부분회로·FF 회로(다른 계)라 대상 밖(I2 사실 확정: `block_model.py:91`·`:112` 인자 = `sub`, `ff_gm_ratio.py:55` 인자 = `ff_circuit`).
  - 재사용 = graph reuse·S3 graft(블록 호출 규약 `E/core/compute_block.py:138-170`)뿐, graph 밖 캐시·메모·값 사본 없음(NFR-2·DEC-83).
- **O-58 전 초안 중 채택한 것**: (1) 결과 표기 칸 -- `config` ∈ {`"declared_feedback"`, `"follower_beta1"`, `"as_is_single_input"`} 또는 None(정의 불능), 보고에 'β = 1 기본' 표기는 `"follower_beta1"`에서 낸다(생산자 = `graph.icm_config` -- 이 판에서 추가) (2) 정의 불능 code 셋(4.7-5 `Undefined`, category `definitional`): `icm_config_differential_output_undeclared`(차동 출력·선언 없음), `icm_inverting_port_none`(음수 후보 0개), `icm_inverting_port_ambiguous`(2개 이상), `icm_inverting_port_unresolved`(전달 크기 ≤ δA_num, 레일 폭 0, 특이 -- v1.12.4), 4.7-1a 멈춤의 실행 중 code `icm_config_output_root_w3`(S-OS1)·`icm_config_differential_output_structure`(S-OS2)(v1.12.3), `icm_config_feedback_no_dc`(단일 출력 + DC 되먹임 없는 선언 되먹임 -- v1.12.5, 계획 v6.26 N3.8·N6.6 IT-2c 착수 조건 (i), 사용자 결정 O-79·O-80 R1; v1.12.6 '없음' = 계획 v6.27 N3.8 경로 판정, O-81 (2)·O-82; 갈래 = 4.7-3b (1)), `icm_config_feedback_element_unsupported`(DC 되먹임 판정 불능 -- S1 `device.unsupported` 원소, v1.12.7 이름 = 계획 v6.28 O-85 (3)) (3) P3 묶음(4.7-3 3)은 구성이 묶은 반전 입력을 빼고 만든다(O-53 A-2).
- **옛 멈춤 기록**(O-58 결정 전 문언 -- 위 설계로 대체됨, history 이전 대상; O-58 결정: S-1 (라) 커널 창은 θ 프레임 유지, 측정 구성 ICMR 창은 봉인 뒤 블록 하나, S-2 그 블록 안 IT-2 정본 하나, S-3 선언 소자를 끊지 않은 봉인점 회로 -- 계획 v6.21 반영·사용자 O-60 승인):
  - **S-1 반전 입력 식별의 층 순서**: 계획은 엔진 식별을 '봉인점 컨덕턴스 계 `conductance_matrix(ss.circuit)`'로 정했다(O-53 A-1). 그 계는 `ss` 층(`E/metrics/_helpers_nodal.py:26`, 소비자는 모두 `E/metrics/*`)에서 생기고, 커널 창을 쓰는 노드 풀이 블록 `dc_columns`(S2 `dc`)는 그보다 먼저 돈다. follower 행(V_out = x)은 반전 입력을 알아야 세울 수 있으므로 같은 평가 안에서 순서가 맞지 않는다. 선택지: (가) 커널 창의 follower 구성 부분을 `ss` 뒤 별도 블록으로 옮김(O-16 (2) '노드 풀이 블록이 모든 입력 포트 창을 쓴다'와 다름) (나) 식별을 S2 θ 프레임 감도 연립의 부호로 함(O-53 A-1 '봉인점 컨덕턴스 계'와 다름; 고임피던스 출력은 θ 프레임에서 입력→출력 전달이 정해지지 않아 물리적으로도 다른 양) (다) S2 블록 안에서 같은 해로 컨덕턴스 계를 조립(ss 계산의 사본 -- 정본 하나 위반). 셋 모두 계획 문언을 바꾸므로 사용자 결정 사항이다.
  - **S-2 KVL 고정 출력의 감도 연립 소유 card**: 계획 N6.6 완료 조건 (8) (d)는 IT-2가 '봉인점 DC 방정식(부하 포함 KCL) 1차 감도 연립 + follower 행'을 내야 한다고 적고, N3.8은 '계산법(DC 끝점 풀이 하나)은 card DE-1이 정한다'·'KVL 고정 출력 스윙(DE-1 (b))과 같은 계산법'이라 적는다. IT-2는 DE-1보다 먼저 병합되므로(계획 N6.6 순서) 그 연립을 IT-2가 먼저 만들면 DE-1 (b)의 계산법을 IT-2 design이 정하게 된다. 또 그 연립은 소자 소신호 컨덕턴스(gm·gds -- `ss` 층 값)가 필요해 S-1과 같은 층 순서 문제를 갖는다. 소유 card(IT-2 / DE-1 / 둘 사이 공용 블록 선행 card)의 결정이 필요하다.
  - **S-3 선언 되먹임 구성의 DC 망**: spec `human.feedback.elements`(`E/authoring/spec_elements.py:118`) 소자를 θ 고정 노드 풀이에 넣는 방법(저항 되먹임이면 출력 W4 행이 KCL 행이 된다 -- S-2와 같은 연립)이 계획에 없다. S-2 결정을 따른다.
  - (옛 문언 '완료 조건 (8) test interface는 이 판에 없다'는 대체됨 -- 4.7-7 L8·L10.)

**4.7-3c graph 스냅샷 파생 규칙(IT-2 범위 4, 사용자 결정 O-59 (2) -- 원래 취지와 다름, 승인 O-59 (2); 정의 정본 = 계획 N3.3 '스냅샷 파생 규칙'·N3.6 표 4행 -- 인용만)**:
- **사실(master `b9af2d6f`, 2026-10-20 재측정)**: `run_kernel`은 parent가 있으면 `snapshot = parent.snapshot`에서 출발한다(`E/sizing/kernel_run.py:72-75` -- 그 앞 조건이 parent의 `PLAN_WRITERS` 버전 = base임을 확인). `_CONTEXT_WRITERS` = `S1_WRITERS` writer ∪ `PLAN_WRITERS`(`E/search/search_context.py:44`; `PLAN_WRITERS` 정의 `E/sizing/kernel_context.py:49`). `lift_s1`(`E/sizing/s2_lift.py:17-24`)은 S1 writer가 모두 돌았는지 확인하고 `source.widen(S2_WRITERS)`로 권한표만 넓힌다 -- 필드의 writer 귀속을 바꾸지 않는다(`FieldValue.writer`, `E/core/field_value.py:16`). 봉인 4 `seal_versions(snapshot, calls)`(`E/sizing/seal_versions.py:14-27`)는 `calls`의 블록만 본다.
- **파생 자리 하나**(keep 집합의 정의 -- 계획 N3.3 '스냅샷 파생 규칙', 사용자 결정 O-61 P1: 옛 문언 '`_CONTEXT_WRITERS`'를 대체, O-59 (2) 뜻 그대로·취지 변경 아님): `run_kernel`의 parent 분기를 `snapshot = parent.snapshot.derive_child(keep)`로 바꾼다. `keep` = **base writer**(그 평가의 커널 컨텍스트 스냅샷 `ctx.base`에 블록 버전이 있는 writer -- 정본 = `ctx.base.block_versions`의 키, `E/core/graph_snapshot.py:39`·`:46`; 그 매핑에서 읽는다, 사본 목록 없음) ∪ **봉인 4가 받는 호출 목록의 블록 이름**(v1.12.8 정오, 사용자 결정 O-94 (2) -- 계획 N3.3 '그 평가가 부르는 계산 블록'·N3.6 표 4행 '그 평가의 호출 블록'과 같은 집합; 옛 문언 '커널 호출 블록 이름(`steps`·`later`)'은 봉인 항목 블록을 빠뜨려 계획보다 좁았다): 커널 블록(`steps`·`later` 목록 -- `kernel_run.py:83-97`) ∪ 봉인 항목 블록 여덟(`dc_tolerances`·`dc_seal_node_conflict`·`dc_seal_vgs_match`·`dc_seal_kcl`·`dc_seal_bulk_reverse`·`dc_seal_saturation`·`dc_seal_kvl_branch`·`dc_seal_conduction` -- `E/sizing/seal.py` `seal_dc`의 항목 목록). 봉인 항목 블록의 구성원·순서는 `E/sizing/seal.py`의 모듈 상수 하나(블록 객체 tuple)가 정본이고 `seal_dc`의 호출 순서와 `run_kernel`의 keep이 모두 그 상수를 읽는다(이름 사본 목록 없음; extras는 `seal_dc` 안에서 블록 객체를 키로 하는 지역 매핑으로 찾는다 -- 순서는 상수, 키가 빠지거나 상수 밖 키가 있으면 예외(검증 R-1: 길이만 대조하면 순서 바뀜을 못 잡음); 실행 사이·평가 사이에 남지 않는 인자 구조라 cache가 아니다). keep 집합은 아래 집합 함수 `writers_in_scope`로 읽는다(v1.12.9 -- 계획 v6.32 N3.3 '집합의 정본 자리 = 함수 하나'). **실패 평가의 부분 스냅샷 파생**(card IT-2e, v1.12.9 -- 정의 정본 = 계획 v6.32 N3.3 '실패 평가의 부분 스냅샷'·N3.6 표 4행·U-93, 사용자 결정 O-96, 근거 `wt/_drafts/evidence/2026-10-22/b69_partial_snapshot_analysis.md`; v1.12.8의 '원래 취지와 다름(작음)·백로그 B69'는 **계획 v6.32 N3.3·O-96으로 해소** -- 성격은 U-93 '그때까지 계산한'·N3.3 "'없음'이 '낡은 값'보다 안전"의 취지 회복): (사실, `integ-it12` `56080584` 재측정 -- v1.12.8 문언 'k+1 뒤 봉인 항목'은 좁았다) 블록 호출은 `block_version(이름) == 입력 버전`이면 reuse하므로(`E/core/compute_block.py:143`) 블록 k에서 실패했다는 것은 k의 입력 버전이 parent와 다르다는 뜻이고, parent에서 파생한 스냅샷의 부분 스냅샷(`_call_block` `E/sizing/kernel_run.py:56-62`, `seal_dc` 봉인 항목 `E/sizing/seal.py:66-70`)에는 **k..끝(실패 블록 자신과 그 뒤 커널 블록·봉인 항목 블록 -- 커널 블록에서 실패한 경우 포함)**의 parent 필드가 남는다; 봉인 보고서 블록 실패(`seal.py:74-78`)·봉인 위반(`:87`)은 커널 블록과 봉인 항목 블록을 모두 부른 뒤라 낡은 필드가 없고, ss 단계(`E/metrics/ss_evaluate.py:113-115`)는 시작 스냅샷 = 봉인 스냅샷이고 ss writer가 파생 keep 밖이라 이미 규칙을 충족한다(code 변경 없음 -- 계획 N3.3). **규칙**: 부분 스냅샷 = 실패 시점 스냅샷을 **base writer ∪ 그 평가에서 실패 전에 부른 블록**(reuse·graft·compute 어느 쪽이든 부른 블록; 계획 문언 '실패 전에 성공한 블록'과 같은 집합 -- 첫 실패에서 예외로 멈추므로 앞에서 부른 블록은 모두 성공한 블록)으로 줄인 것(`derive_child` -- 구조 공유, 새 필드·cache·값 사본·writer·블록 호출 없음, reuse·graft·compute 계수 변화 0); 실패한 블록 자신과 그 뒤 블록의 필드는 넣지 않는다; 봉인 위반에서는 `dc_seal_report`도 이미 부른 블록이라 남는다(방금 쓴 보고서를 지우지 않는다). 그래서 부분 스냅샷의 writer 집합과 지문은 (평가 키, 실패 지점)만으로 정해지고 parent와 무관하다; parent 없는 평가는 스냅샷 writer가 이미 이 집합 안이라 바뀌지 않는다(지문 불변). **집합 함수 하나**(이름·자리 = design, 계획 N3.3): `writers_in_scope(base, blocks) -> frozenset` -- 자리 `E/sizing/seal_versions.py`(봉인 4 coverage 술어가 있는 모듈; 모듈 지도 sizing 층 1이라 `seal.py`(층 3)·`kernel_run.py`(층 4)가 앞 층으로 import -- 순환·같은 층 import 없음; `seal_versions`가 부르므로 구조 규칙 A의 독립 진입점이 아니어서 모듈 지도 kind·진입점 `seal_versions` 그대로, 그 항목 책임 문장·계획 ID에 N3.3 부분 스냅샷 집합을 더한다). 서명: `base` = 커널 컨텍스트 스냅샷 `ctx.base`(base writer 정본 = 그 `block_versions` 키; None이면 `TypeError` -- `seal_versions`와 같은 형태), `blocks` = 블록 객체(`ComputeBlock`) iterable(이름은 함수 안에서 `.name`으로 읽는다 -- 부르는 자리는 블록 이름 집합을 만들지 않는다), 반환 = base writer ∪ {블록 이름}의 `frozenset`. 'base writer ∪ 블록 이름' 합집합식과 coverage 차집합 꼴의 정의 자리는 이 함수 하나, 그 밖 재구현 0(L11 (e) AST 검사). **AST 검사가 세는 것**(검증 S-3, 계획 N3.3 측정 정의 안의 구현 세부 -- 정의를 넓히지 않는다): 세는 연산 = 합집합·차집합 -- 이항 `|`·`-`, 누적 대입 `|=`·`-=`, set 메서드 `.union`·`.difference`·`.update`·`.difference_update`; 교집합(`&`·`.intersection`)은 서로소 단언 꼴이라 세지 않는다; 한 식 트리(위 연산의 사슬)의 피연산자에 base writer 집합(출처 = 스냅샷 `block_versions` -- 함수 안 대입을 거쳐도, `set(x)`·`frozenset(x)`·`tuple(x)`처럼 호출로 감싼 피연산자 안까지 들어가 추적; 재검증 N-R1)과 블록 이름 집합이 **함께** 나타날 때만 센다; '블록 이름 집합' = 블록 객체의 `.name`으로 만든 집합(comprehension 등), 문자열 상수의 set·frozenset·tuple(예: `{"dc_currents", …}` -- 옛 `_CONTEXT_WRITERS` 같은 이름 사본 꼴), 함수 매개변수로 받은 이름 집합, 또는 그것들을 담은 변수(재검증 S-R1 -- 계획 '블록 이름 집합'은 만드는 방식을 한정하지 않는다; 교집합 제외는 그대로). **검사기 양성 대조**(N-R1): 변경 전 head(IT-2a 반영 `integ-it12` `56080584`)에서 세면 인라인 식 두 곳(`kernel_run.py:86`·`seal_versions.py:36`) = 2가 나와야 한다(0이면 검사기 결함 -- red). 레지스트리 확인: `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` §2에 같은 개념 행 없음, 엔진 `def ` grep에 같은 집합을 내는 함수 없음(지금은 `kernel_run.py:86-87` keep식과 `seal_versions.py:32-36` coverage식 두 곳의 인라인 식) -- 새 함수를 두고 두 인라인 식을 같은 변경에서 지우며 레지스트리 §2에 행을 더한다(code 커밋 몫). **부르는 자리 셋**: (i) `run_kernel` 파생 keep -- `parent.snapshot.derive_child(writers_in_scope(base, 커널 블록(steps·later_blocks) + SEAL_ITEM_BLOCKS))`(옛 `set(base_writers) | {…} | …` 대체) (ii) 봉인 4 coverage -- 위반 writer = 스냅샷 필드 writer − `writers_in_scope(base, calls의 블록)`(차집합 꼴; 옛 `used - base_writers - called` 대체) (iii) 실패 부착 -- 줄인 스냅샷 `snapshot.derive_child(writers_in_scope(base, 앞 블록))`을 `attach_partial`에 넘긴다: `_call_block`(커널 블록 실패 -- 앞 블록 = 그 평가의 커널 호출 순서에서 실패 블록 앞부분), `seal_dc` 봉인 항목 블록 실패(앞 블록 = 그 시점 `calls`의 블록 = 커널 블록 ∪ 이미 성공한 봉인 항목; 실패 블록은 성공 뒤에만 `calls`에 더해지므로 빠진다 -- `seal.py:71`), 봉인 보고서 블록 실패(`calls`의 블록 전부 -- 커널 블록 ∪ `SEAL_ITEM_BLOCKS`), 봉인 위반(`calls`의 블록 + `dc_seal_report`). **앞 블록을 얻는 방법**: `_call_block`에 인자 `before`(그 평가에서 이미 부른 블록 객체 tuple)를 더하고 `run_kernel`의 두 루프가 호출 목록 앞부분 slice로 넘긴다(첫 루프 = `steps[:i]`의 블록, 둘째 루프 = `steps`의 블록 + `later_blocks[:j]` -- 루프 인덱스, 새 누적 변수·저장 없음); `seal_dc`는 이미 있는 지역 `calls`(봉인 4 인자로 쌓는 호출 목록)를 쓴다. 서로소 단언(base writer ∩ 호출 블록)과 parent 일치 검사(`kernel_run.py:73-74`)는 이 함수 밖이다(base writer를 따로 읽는 것은 합집합·차집합이 아니라 측정 대상 아님 -- 계획 N3.3). **재연 예외**(같은 실행 실패 색인 재연 -- 블록 호출의 `from_record`, `E/core/compute_block.py:150-156`)도 같은 부착 자리에서 줄여서 붙는다(재연 예외는 `partial` None으로 시작하고 `attach_partial` 첫 부착 유지 규칙 그대로 -- 계산했을 때와 같은 앞 블록·같은 부분 스냅샷). `attach_partial`(core)은 바꾸지 않는다(base를 모른다). **같은 변경에서 고치는 문서 자리**(검증 S-2 -- 바뀐 뒤 parent 경로에서 거짓이 되는 부분 스냅샷 문언, `56080584` 재확인): `E/search/CONTRACT.md:458`(`EvalResult.partial` 문언 'DC 블록 실패 = 그 블록에 들어간 스냅샷'), `E/search/search_values.py:163-164`(`EvalResult.partial` docstring), `E/sizing/CONTRACT.md:117-119`(`run_kernel`·`seal_dc` 부분 스냅샷 부착 문단), `E/sizing/kernel_run.py:10-11`(머리 설명), `E/sizing/seal.py:69` 주석 -- '줄인 스냅샷'으로 고친다. 착수 사실(부착 자리, 커널 블록 구성 = 평가 커널 steps·later 구성원, 집합식 자리, 줄 번호)은 IT-2d 병합 head에서 다시 잰다(계획 N6.6 범위 5 -- 이 항목의 줄 번호는 `56080584` 값). 범위 밖(백로그, 계획 N3.3): 봉인 아닌 점의 `passive_values`·`metrics_dc` 후보 실패 처리(`E/search/kernel.py:142-147`). **`dc_seal_report`는 keep에 넣지 않는다** -- 봉인 4·5의 결과를 입력으로 봉인 4 뒤에 불리므로 봉인 4의 호출 목록에 들 수 없고, parent의 보고서 필드를 남기면 봉인 4 coverage가 그 필드를 `foreign_writers`로 거부한다(남기려면 coverage가 아직 부르지 않은 블록의 낡은 필드를 허용해야 해서 검사가 약해진다). 그래서 그 필드는 child에서 지워지고 다시 불릴 때 같은 입력 버전이면 S3 graft로 돌아온다(재계산 0) -- 계획 문언 '부르는 계산 블록'을 '봉인 4가 받는 호출 목록'으로 읽은 것이고 더 지우는 쪽(fail-closed)이다(**원래 취지와 다름(작음), 승인 O-94 (2)**). 근거(계획 같은 문단): 옛 `_CONTEXT_WRITERS`(`S1_WRITERS` ∪ `PLAN_WRITERS`)에는 `ctx.base`가 담는 S1v·S0 탐색·metrics S0 writer가 없어 parent 없는 평가가 봉인 4에서 거부되고 child가 그 필드를 잃는다. `ctx.base`는 평가 θ를 읽지 않는 블록만으로 평가 전에 만들어지므로 그 필드는 모든 평가에 유효하다(전제 -- 아래 봉인 4 서로소 단언이 지킨다). 새 메서드 `GraphSnapshot.derive_child(keep_writers)`(`E/core/graph_snapshot.py`): writer ∈ `keep_writers`인 필드와 그 writer의 `block_version`만 남기고 나머지 writer의 필드·`block_version`을 지운 새 스냅샷(권한표·구조 공유 그대로; eager, '없음'이 '낡은 값'보다 안전 -- fail-closed). 봉인 뒤 블록(`ss_linearize`·`ss_nodal`·`icm_config`·metric 블록)과 커널 밖 writer(`dc_window_refine`·`metrics_icm_front`)의 필드는 child에서 지워지고, 그 블록이 다시 불리면 같은 입력 버전의 값이 S3 색인 graft로 돌아온다(재계산 0, 새 캐시 없음 -- 계획 N3.3).
- **`_CONTEXT_WRITERS`는 옮기지 않는다**(사용자 결정 O-61 P1 -- 옛 초안의 '`CONTEXT_WRITERS` 정의 이동' 항목 삭제): `E/search/search_context.py:44`의 `_CONTEXT_WRITERS`는 평가 키 지문 `context_fp` 전용이고 이 규칙의 정본이 아니다(계획 N3.3). `run_kernel`은 search를 import하지 않는다 -- keep은 `ctx.base`(이미 `run_kernel`의 인자 `ctx`에 있음)에서 읽으므로 층 방향 문제가 없다.
- **parent 일치 검사 넓힘**(계획 N3.3·N6.6 범위 4): `kernel_run.py:73`의 검사 `any(parent.snapshot.block_version(w) != base.block_version(w) for w in PLAN_WRITERS)`를 **base writer 전부**(`base.block_versions`의 키)로 넓힌다 -- 같은 검사의 일반형, 어긋나면 지금처럼 `ValueError`(fail-closed). 그래서 `derive_child`가 남긴 base writer 필드는 늘 `ctx.base`와 같은 입력 버전이다.
- **봉인 4 단언 둘**(계획 N3.6 표 4행): `seal_versions(snapshot, calls, base)`(셋째 인자 = `ctx.base` 스냅샷 -- base writer는 그 `block_versions`에서 읽는다; 호출 자리 `seal_dc`는 `run_kernel`에서 `ctx.base`를 넘겨받는다 -- `seal_dc`의 `base`는 기본값 없는 필수 키워드(v1.12.8, 사용자 결정 O-94 (3): 기본값 None으로 (3)(4)를 건너뛰는 길은 봉인 4 우회 = 기준 약화; 선례 `donors`·`counters` 필수 키워드 B-T16; `seal_versions`도 base None을 받으면 건너뛰지 않고 `TypeError`로 거부하며(SEAL_FAIL이 아니라 호출 오류 -- 필수 키워드 누락과 같은 형태, 재검증 G-1) `if base is not None` 건너뛰기 분기는 삭제 -- 검증 R-2, 계획 v6.31 N3.6 4행)) 끝에 (3) **coverage** '스냅샷의 모든 필드의 `FieldValue.writer` ∈ base writer ∪ {`calls`의 블록 이름}'(v1.12.9: 그 집합은 `writers_in_scope(base, calls의 블록)`에서 읽고 위반 writer = 필드 writer − 그 집합 -- 위 '실패 평가의 부분 스냅샷 파생', 계획 v6.32 N3.6 4행) -- 위반 writer는 detail `("foreign_writers", 정렬 tuple)` (4) **서로소** 'base writer ∩ {`calls`의 블록 이름} = ∅' -- 위반 이름은 detail `("base_call_overlap", 정렬 tuple)`을 더한다. 어느 하나라도 위반이면 status `SEAL_FAIL`(fail-closed). 기존 (1)(2) 검사는 그대로.
- **착수 실측**(계획 N6.6 범위 4): (i) search tests 가운데 ss 블록 `reuse` 계수를 단언하는 test(`git grep`) -- 기대가 `graft`로 바뀌므로 변화표에 적고 test 작성자가 새 기대로 쓴다; 같은 θ parent 재평가의 DC 열세 블록 outcome은 커널 4·봉인 항목 8 = `reuse`, `dc_seal_report` 1 = `graft`(옛 기대 reuse 13 -- `E/tests/sizing/test_size_and_seal.py` `test_same_theta_with_parent_zero_compute`·`test_passive_theta_only_change_zero_dc_compute` -- 함수 둘, parametrize 포함 항목 넷, computes 0 유지; v1.12.8, 사용자 결정 O-94 (2)) (ii) S3 색인에서 ss 블록 등록이 빠지는 경로(실패 경로 등) -- 있으면 그 경로에서 graft가 아니라 compute가 되므로 변화표에 적는다 (iii) parent 없는 평가 스냅샷(= `ctx.base`)의 writer 목록과 그 writer 모두가 평가 θ를 읽지 않음(탐색 경로 `E/search/search_context.py` `base = dc_ctx.base.widen(S0_WRITERS)` 뒤 S0 블록 포함 -- 계획 N6.6 범위 4; θ를 읽는 writer가 있으면 서로소 전제가 깨지므로 **멈추고 보고**) (iv) `lift_s1`(호출 `E/sizing/kernel_context.py:81`, 정의 `E/sizing/s2_lift.py:17`)이 writer 귀속을 바꾸지 않음(확인됨, 위 사실).

**4.7-4 다듬은 창 블록 `dc_window_refine`(IT-2 범위 1, O-21·O-25 (3))**: 새 `@compute_block`, writer 이름 `dc_window_refine`(상수 `DC_WINDOW_REFINE_WRITER`), 파일 `E/sizing/window_refine.py`(진입점 `refine_input_windows`), test `E/tests/sizing/test_window_refine.py`(규칙 H). READS = `dc_columns`의 READS + `("node", "dc_window_cfg")`(출발 창, 아래 1 -- 사용자 결정 O-61 P6; `("node", "dc_window")`는 읽지 않는다, 계획 N6.6 완료 조건 (12) (d))·`("node", "port_direction")`·`("graph", "icm_config")`(W2 -- 반전 입력 식별·`tied_ports`·`config`, 4.7-3b)·`("node", "dc_output_structure")`(출력 구조, READS만 -- 4.7-1a, v1.12.2), extras = `dc_columns`와 같은 넷(θ 성분, `fixed_values`, `resistor_values`, LUT, 선형 선언 소자). WRITES `("node", "dc_window_def_refined")`(입력 포트마다). 등록: `DC_WRITES`(`E/sizing/s2_values.py:143-164`)에 `(DC_WINDOW_REFINE_WRITER, (("node", "dc_window_def_refined"),))`를 더해 `S2_WRITERS`(`:180-`) 권한표에 든다, `E/_module_map.py`에 `ModuleEntry("sizing/window_refine.py", "entry", "refine_input_windows", …)`·`ModuleEntry("sizing/_helpers_dc_solve.py", …)` 행.
- **공유하는 것(helper로 옮김)**: 두 블록(`dc_columns`·`dc_window_refine`)이 함께 쓰는 노드 풀이 기계만 같은 패키지의 공용 helper 모듈 **`E/sizing/_helpers_dc_solve.py`**(test `E/tests/sizing/test__helpers_dc_solve.py`)로 옮겨 공개 이름으로 둔다: 클래스 `Circuit`(as-built `_Circuit`, 메서드 `saturation_rows`·`input_windows`·`window`·`kvl_window` 등 포함), 함수 `solve`(as-built `_solve`)와 그것이 부르는 비공개 정의, 실패 묶음 상수 `FAILURES`(as-built `_FAILURES`). 근거: 구조 규칙 A 보충 (3)(`_` 모듈의 공개 함수는 같은 하위 패키지의 다른 파일 2개 이상이 import -- `Circuit`·`solve`는 `block_columns.py`·`window_refine.py` 둘이 쓴다), 규칙 B(다른 파일의 `_` 이름 import 금지, `_helpers_*` 모듈 import는 허용), 규칙 H. '코드 이동이고 식 불변'은 이 옮기는 범위(`Circuit`·`solve`·`FAILURES`)에만 해당한다 -- `Circuit.input_windows`는 4.7-3 2의 감도 반환 때문에 반환 형식이 바뀐다. (이름 `_helpers_columns`는 `E/lut/_helpers_columns.py`와 겹쳐 쓰지 않는다.)
- **옮기지 않는 것**: 끝 풀이는 helper로 옮기지 않는다 -- 한 파일(`window_refine.py`)만 쓰므로 규칙 A 보충 (3)을 못 넘는다. `window_refine.py` 안 비공개 함수로 아래 2·3대로 **새로 쓴다**(as-built `_refine_ends`의 되풀이 구조 (i)~(v)를 따르되 끝 해 보관과 fail-closed가 다르다). 커널 쪽 `_refine_ends` 호출은 없어지므로 `block_columns.py`의 `_refine_ends`는 같은 변경에서 지운다. `_solve_input_window`·`_interior_solution`·`_dyadic_ys`는 커널 전용이라 `block_columns.py`에 남는다.
- 모듈 수준 이름(장애 주입 지점, 4.7-7 R2): `window_refine.py`는 `from ._helpers_dc_solve import solve`·`from .k_max import k_max`로 모듈 수준에서 import한다(test가 `gmid_engine.sizing.window_refine.solve`·`.k_max`를 monkeypatch할 수 있게).
1. **출발 끝**(계획 N6.6 범위 1 '입력(출발 창) = 같은 측정 구성·같은 기준의 커널 창', 사용자 결정 O-61 P6 -- 옛 문언 '입력 = 정의 창'은 DE-1 전에 없는 필드를 가리켰다): DE-1 전 입력 = 측정 구성 판정 창 `node.dc_window_cfg`(+tol, 기준 칸 `"tol_judgement"`과 같은 기준), DE-1 뒤 = 정의 창 `node.dc_window_def`(READS 교체는 card DE-1 design 몫). θ 프레임 창 `node.dc_window`(측정 구성 없음)와 `node.dc_v`는 읽지 않는다(아래 6). **출발 창이 없는 포트**(그 포트의 `node.dc_window_cfg` `lo`·`hi`가 None -- `"f_component_undeclared"`, 자기 측정 실패 `"unmeasured"`)는 다듬지 않는다(입력이 없으면 출력이 없다 -- fail-closed; 아래 2 '쓰지 않는 포트' (c)); front는 그 포트에서 cfg 상태로 정의 불능을 낸다(4.7-5). **`"unsettled"` 출발 창**(커널 미수렴 이어받기 -- `lo`·`hi`는 진단용으로 있음)은 **다듬지 않는다**(계획 N6.6 범위 1 '출발 창이 미수렴인 포트의 다듬은 창은 계산하지 않고, 그 front 값은 같은 사유로 정의 불능이다', 사용자 결정 O-64 (2) -- v1.12.1의 '다듬는다'와 그 '원래 취지와 다를 수 있는 항목' 보고를 대체): 아래 2 '쓰지 않는 포트' (d), 끝 풀이 호출 0. front는 그 포트에서 cfg 상태 `"unsettled"`로 `input_window_unsettled`를 낸다(4.7-5 front·'미수렴 front 처리'). **측정 구성 `as_is_single_input`**(사용자 결정 O-63 (4) -- v1.12.1 멈춤 해소; 계획 N3.8 '선형 감도 끝만 정의되는 구성의 정본 칸'·N6.6 범위 1·2): 그 구성의 측정은 '출력이 회로 자신의 DC 관계로 따름'의 선형 감도 끝(4.7-3b (5) -- 봉인점 G 위 `kvl_sensitivity`)이고, 이 블록의 θ 고정 끝 풀이(전류 θ 고정)는 그것을 표현하지 못한다(고임피던스 출력의 W4 y를 정할 식이 없고 KVL 고정 출력에서도 출력 가지 전류를 바꿀 수 없다). 그래서 KVL 고정 구조와 같이 처리한다: 그 평가의 입력 포트 전부를 쓰지 않고(아래 2 (b), 끝 풀이 호출 0), front·보고는 그 포트의 `node.dc_window_cfg`('추정' 선형 감도 끝)를 읽으며(4.7-5), 정밀 값은 oracle SPICE 다리(`.dc` 훑기)가 잰다 -- 엔진에 전체 DC 끝 풀이를 새로 두지 않는다(O-32 순풀이 금지). 판정에 쓰는 graph 필드 = `graph.icm_config.config`(이 블록 READS) -- 새 규칙·상수 없음.
2. **끝 풀이**(아래 끝·위 끝 각각, A7과 같은 되풀이, 상한 `k_max`(레일 폭, tol)): 뿌리는 `override` = (x, x)(고임피던스 W3 목표 출력의 follower는 `fixed_values[출력]` = x -- 4.7-3b '정본 칸' 끝, v1.12.3 gap N2), 선언 포트 묶음(4.7-3 3 -- x = 묶음 이동량 Δ)은 묶음의 모든 포트 p에 `fixed_values[p]` = 선언값 + Δ로 바꿔(묶음 전체를 같은 Δ로 함께 옮긴 풀이 하나) 푼다. **쓰지 않는 포트**(끝 풀이 호출 0, `node.dc_window_def_refined` 항목 없음): (a) F 성분 미선언 포트(4.7-3 3 -- 창 정의 불능, 사용자 결정 O-61 P4 (b)) (b) **선형 감도 끝만 정의되는 구성의 평가** -- 출력의 `node.dc_output_structure == "kvl_fixed"`(4.7-1a)이거나 `graph.icm_config.config == "as_is_single_input"`(사용자 결정 O-63 (4))인 평가의 입력 포트 전부(묶인 반전 입력 포함 -- 정본 칸 `node.dc_window_cfg`, 4.7-3b, 사용자 결정 O-61 P3, v1.12.1 M2; 이 판정을 하는 자리는 이 블록 하나이고 front는 항목 유무만 본다) (c) 출발 창이 없는 포트(위 1) (d) 출발 창이 미수렴(`node.dc_window_cfg` `input_status == "unsettled"`)인 포트(위 1, 사용자 결정 O-64 (2) -- 미수렴은 평가점 단위로 이어받으므로(4.7-3b (가)) 그 평가의 입력 포트 전부). 네 경우 front 값의 출처는 4.7-5 front 규칙이 정한다. **끝 풀이 함수 하나**(v1.12.1 gap G3): as-built `_refine_ends`는 이 블록의 비공개 끝 풀이 함수로 **대체**된다('옮기지 않는 것' -- 같은 변경에서 `_refine_ends` 삭제). 끝 풀이를 하는 함수는 그 하나뿐이라 계획 범위 1 끝·완료 조건 (2) '끝 풀이는 `_refine_ends` 하나'의 취지(끝 풀이 함수 하나, 둘째 생산자 없음)는 그대로이고 이름만 다르다 -- 계획 문언 정리는 4.7-9 계획 문언 알림. 되풀이가 (i) `inside and close` 또는 (ii) 풀이 직후 창을 잴 수 없어 멈추면 **그 끝 = 방금 푼 x이고 그 해를 보관한다**: 뿌리(또는 x 포트) `WindowEnd(x, x, None)`, 같은 성분의 입력 포트 p마다 `WindowEnd(x, V_p(해), None)`. **(ii) 끝의 포화 확인**(사용자 결정 O-49 P6, fail-closed -- O-25 (3)): (ii)는 해는 있으나 그 해에서 창을 잴 수 없어 멈춘 끝이므로, 값으로 쓰기 전에 **그 해에서 4.7-3a 행 셋(`region_rows`)의 여유를 직접 계산**해 모든 행의 여유 ≥ 0이면 확인된 끝(`reason` None, 해 보관)이다. 행을 만들 수 없거나(VDSAT 열·tol 미정 -- `region_rows` None) 어느 행이라도 여유 < 0이면 그 끝은 `reason` = **`window_end_saturation_unconfirmed`**(상수 `REASON_WINDOW_END_UNCONFIRMED`), `v` = None이고 같은 성분의 모든 입력 포트가 그 사유를 받는다(아래 3과 같은 처리). 확인은 행 값 계산이라 감도 연립도 새 풀이도 하지 않는다(재계산 0).
3. **fail-closed**(계획 범위 1 (iii)~(v), 뿌리 창도 같음 -- O-25 (3)): (iii) 첫 반복 풀이 실패 (iv) 둘째 반복 이후 풀이 실패 → `reason` = **`window_end_solve_failed`**(상수 `REASON_WINDOW_END_SOLVE_FAILED`), (v) `k_max` 소진 → **`window_end_k_max_exhausted`**(상수 `REASON_WINDOW_END_K_MAX`). 그 끝의 `v` = None, `x` = 마지막으로 다룬(풀리지 않은) x(진단용, 값으로 쓰지 않는다). 대체값(기울기 외삽·이전 끝·다른 x의 해·0)을 쓰지 않는다. 같은 성분의 모든 입력 포트가 그 끝의 사유를 받는다. 실패 예외의 원래 사유(LUT 정의역 밖 등)는 `SccLog`와 같이 진단 칸으로 남기지 않고 사유 둘만 둔다(계획 '세부는 design' -- 판정에 쓰는 정보는 '그 끝이 풀리지 않았다'뿐이다).
4. `_sensitivities` 기울기 외삽을 다듬은 창에 쓰지 않는다(O-21). 넷별 뿌리 경로 κ를 다시 계산하지 않는다.
5. **호출 자리와 배선**(줄 번호는 master `2e707d5d`에서 다시 잼, 2026-10-20 -- 검증 W6):
   - 실행 함수 하나: 새 파일 `E/search/front_windows.py`, 진입점 `refine_front_windows(sctx, result) -> EvalResult`. 봉인 통과(`status` 봉인) 점의 `result.evaluation.snapshot` 위에 `dc_window_refine` → `metrics_icm_front`를 차례로 부르고(블록 호출 규약 그대로 -- extras는 그 점의 θ 성분과 커널 컨텍스트 S0 필드 `fixed_values`·`resistor_values`·LUT·선형 선언 소자, `metrics_icm_front`는 선언 입력 DC), 두 필드가 붙은 스냅샷을 담은 `EvalResult`를 `dataclasses.replace(result, evaluation=dataclasses.replace(result.evaluation, snapshot=새 스냅샷))`로 돌려준다. 봉인 실패·`outside_domain` 점은 그대로 돌려준다.
   - **재사용 = graph 규칙 하나, 새 캐시 없음**(검증 W4; 사용자 지적 2026-10-20 '캐시는 graph 정본' -- NFR-2·DEC-83): 두 필드는 graph 필드이고 그 값의 재사용 자리는 실행 수명 S3 색인(`S3Index(Donors)`, 키 = (writer, part, input_version)뿐 -- `E/search/CONTRACT.md:1112-1113`, `E/core/CONTRACT.md:296-298`) 하나다. 블록 호출(`E/core/compute_block.py:138-170`)은 (1) 스냅샷의 `block_version(이름)`이 지금 입력 버전과 같으면 reuse(`:143-145`) (2) 아니면 S3 색인 `donors.find(이름, part, 입력 버전)`이 있으면 graft(`:146-149`) (3) 없으면 compute 뒤 `donors.register`(`:169-170`)이다. 그래서 같은 θ(같은 커널 스냅샷 = 같은 투영 = 같은 입력 버전)에서 `refine_front_windows`를 두 번째 부르면 두 블록은 graft이고 `computes` 0이다(재계산 0, G-10). 커널 평가 캐시 `sctx.cache`(조회 `E/search/kernel.py:101`, 저장 `:112`·`:170`, `evaluate` `:94` -- as-built 그대로)에는 다듬은 결과를 넣지 않는다.
   - **parent와 커널 밖 writer 필드**: `evaluate`는 `size_and_seal(dc, …, parent=parent.evaluation)`(`kernel.py:123`·`:126`)을 부르고 `run_kernel`은 parent가 있으면 **parent 스냅샷에서 출발**한다(`E/sizing/kernel_run.py:72-75`). 커널 블록(`dc_currents`·`dc_lengths`·`dc_columns`·`dc_widths`, `kernel_run.py:83-97`)은 위 규칙대로 입력 버전이 바뀌면 다시 쓰지만, 커널이 부르지 않는 writer(`dc_window_refine`·`metrics_icm_front`)의 필드는 **아무도 다시 쓰지도 무효로 하지도 않고 그대로 실린다** -- 봉인 4(`E/sizing/seal_versions.py:14-27`)는 그 평가에서 부른 블록(`calls`)만 검사하므로 그 필드의 낡은 입력 버전을 잡지 않는다. 즉 **기존 graph 규칙만으로는 '다듬은 스냅샷이 parent가 되면 낡은 값이 실리지 않음'이 성립하지 않는다**(공백 -- 아래). 그래서 이 design은 다듬은 스냅샷이 parent·커널 캐시에 들어가는 길을 만들지 않는다: 수락 반복의 `state["parent"]`·`state["accepted"]`는 as-built처럼 커널 결과 `entry["res"]`이고(`slsqp_outer.py:155`·`:156` 불변 -- 옛 초안의 `entry["res"]` 교체 삭제), `refine_front_windows`의 반환은 parent·`sctx.cache`에 넣지 않는다. **공백 해소**(사용자 결정 O-59 (2), 계획 v6.21 N3.3 '스냅샷 파생 규칙'): parent → child 파생 때 커널 밖 writer 필드를 지우고 봉인 4가 writer coverage를 단언한다 -- 4.7-3c. 이 card는 그 규칙과 함께 K3 (a)(b)('길 없음')도 그대로 단언한다.
   - (a) 수락 반복: `E/search/slsqp_outer.py` `solve_eps`의 `accept`(`:153-156`) 안에서 `refine_front_windows(sctx, entry["res"])`를 부른다(계획 DEC-73 '수락 반복'의 정의 -- 두 블록이 compute되어 S3 색인에 등록된다; 반환값은 parent에 쓰지 않는다).
   - (b) front 점: `E/search/find_front.py` `find_front`가 `sweep_front` 결과(`out["front"]`·`out["pending_front"]`·`out["unmeasured_front"]`)의 점마다 `_point_record`(정의 `:51-61`, 호출 `:136-138`) 전에 `refine_front_windows`를 불러 그 반환으로 기록한다(이미 수락 반복이었으면 S3 색인 graft -- `computes` 0). `_point_record`가 쓰는 `snapshot_ref`(`sctx.archive.write_snapshot`, `E/search/archive.py:58`)·`snapshot_fp`가 두 필드를 담은 스냅샷을 가리킨다 -- front 점 보고 값의 운반자다. run 레코드의 키는 늘지 않는다(형식 불변). front 값을 읽는 쪽 = 그 스냅샷의 `graph.metrics_icm_front`(EO-1의 oracle 입력 생산자, U16 보고서).
   - **FD 열 평가·커널 평가에서는 부르지 않는다**(계획 N6.6 완료 조건 (0)): `kernel.evaluate`(`:94-`)·`fd_jacobian`은 `refine_front_windows`를 부르지 않는다.
   - **계수**: 끝 풀이의 `solve` 호출은 커널 평가가 아니다 -- `kernel_calls`·평가 예산 E_B·XRUN-F1 E_total(X-8, 커널 평가 수)에 넣지 않는다(SCC 반복처럼 블록 안 계산). 두 블록은 블록 계수(`perf.blocks`·`block_computes`, `RunCounters`)에 행이 생기고, 끝 풀이 수는 새 perf 칸 `window_end_solves`(실행 합)로 센다(WP-10 비용 보고).
   - **층 0 front 후보 점**(외층이 꺼진 점 -- 조립점·수리점 가운데 비지배 재필터를 통과한 점): 호출 자리는 **card LA-1 범위 12**가 더한다(사용자 결정 O-49 P4, DEC-73 (4) -- 그 점에서 한 번, 같은 점 두 번 호출 0). 이 card는 그 자리가 부를 진입점 `refine_front_windows(sctx, result)`를 외층 상태와 무관한 꼴로 둔다(수락 반복 여부를 인자로 받지 않는다 -- LA-1이 같은 함수를 부르게). 자리·계수 test는 LA-1 design 몫이다.
6. **READS에 `node.dc_v`·`node.dc_window` 없음**(사용자 결정 O-49 P1·O-61 P6 -- 계획 N6.6 범위 1 '`node.dc_window`(측정 구성 없음)와 `node.dc_v`는 읽지 않는다', 완료 조건 (7) (d)·(12) (d)): 끝 풀이는 끝 x마다 처음부터 풀고(`_solve`는 시작값을 받지 않는다, `E/sizing/block_columns.py:560-` 기둥 위치 비례 시작) 창 측정도 그 해에서 하므로 `node.dc_v`를 읽는 계산이 없다. 위 READS 목록이 정본이다(`dc_columns`의 READS가 `node.dc_v`를 담고 있으면 그 원소는 뺀다 -- 계획 완료 조건 (7) (d) 블록 READS 단언).

**4.7-5 metric 읽기(IT-2 범위 2·3, IT-Q2 (다) 정의, X-IT8 -- 판정이 (나)든 (다)든 계산 경로 하나)**:
- **정의 함수 하나**: `icm_window_metrics(ports, input_dc, config_undefined=()) -> IcmWindow`(새 순수 함수, 파일 `E/metrics/icm_window.py`, test `E/tests/metrics/test_icm_window.py`).
  - `ports` = **측정 구성이 묶지 않은 입력 포트**마다(v1.12.4 gap G4 -- 계획 v6.24 N6.6 범위 2·N3.8 576 `icm_margin_v` 정의 정본 '대상 = 측정 구성이 묶지 않은 입력 포트', 사용자 결정 O-67 (2) DV-18; 묶인 포트 = `graph.icm_config.tied_ports`(4.7-3b WRITES, `IcmConfig` 칸 `tied_ports: tuple[str]` -- 구성이 출력에 묶은 입력 포트, 예 follower의 반전 입력)는 빼고, 부르는 쪽(`metrics_aux`·`metrics_icm_front`)이 이미 READS인 그 칸에서 거른다 -- 새 칸·사본 없음) `IcmPort(net, v, lo, hi, tol_v, missing)`의 tuple. **세 metric의 포트 집합은 같다**: `icm_margin_v`(계획 정의 정본)·`required_input_cm_v`(값·창 = 최솟값을 낸 포트의 것 -- 계획 N6.6 범위 2, 같은 포트 집합에서 나와야 정의가 맞음)·`icmr_v`(포트 창 교집합의 폭 -- 계획은 포트 집합을 따로 적지 않음('as-built 뜻 유지'); 묶인 포트의 창은 출력에 묶인 종속 양이라 입력 공통모드 범위가 아니므로 같은 집합으로 둔다, 계획 문언과 충돌 없음 확인) -- 묶인 포트가 없으면(선언 되먹임 아닌 `as_is_single_input`·묶음 없는 구성) 입력 포트 전부. 순서 = (구조 색 `node.dc_colour`, 이름) -- 동률 깨기 순서. `IcmPort`는 새 frozen dataclass(`E/metrics/aux_types.py`): `net: str`, `v: float`(해의 그 포트 전압, `node.dc_v` -- 선언 포트는 선언값과 같다), `lo`·`hi`: float 또는 None, `tol_v`: float 또는 None, `missing`: `()` 또는 `((code, detail),)`(code ∈ {`input_window_unmeasured`, `input_window_unsettled`, `input_window_end_missing`, `input_window_operating_point_mismatch`, `input_window_f_component_undeclared`}, detail = (키, 값) 정렬 tuple). 창 필드에서 만드는 규칙(`Window` 꼴 창 -- 커널 갈래의 `node.dc_window_cfg`(모든 구성), front 갈래에서 다듬은 창 항목이 없는 포트가 읽는 `node.dc_window_cfg`): 항목 없음 또는 `input_status="unmeasured"` → `input_window_unmeasured`, `"unsettled"` → **`input_window_unsettled`**(커널 창 되풀이 미수렴·tol 미정 -- 사용자 결정 O-61 P5, 계획 N6.6 범위 1 '사유 이름은 design'; `node.dc_window_cfg`는 4.7-3b '커널 상태 이어받기'로 이 상태를 싣는다), `"op_mismatch"` → `input_window_operating_point_mismatch`(detail = `Window.status_detail`, 4.7-3a 3), `"f_component_undeclared"` → **`input_window_f_component_undeclared`**(사용자 결정 O-61 P4 (b), 4.7-3 3); `RefinedWindow` 꼴 창(front) -- 끝 `reason`이 None이 아니면 `input_window_end_missing`(detail `(("end", "lo"|"hi"), ("reason", WindowEnd.reason))`).
  - `input_dc` = `"declared"` | `"pending"`. 예시: `icm_window_metrics((IcmPort("vin_n", 0.90, 0.35, 1.20, 1.2e-4, ()), IcmPort("vin_p", 0.90, 0.33, 1.18, 1.2e-4, ())), "pending")` → `icm_margin_v` = 0.28(vin_p 위쪽), `icmr_v` = 1.18 − 0.35 = 0.83, `required_input_cm_v` = (0.90, 0.33, 1.18).
  - `icm_margin_v` = 포트별 margin_p = min(V_p − lo_p, hi_p − V_p)의 최솟값. 동률이면 `ports` 순서 첫 포트.
  - `required_input_cm_v` = 입력 DC 미선언이면 (V_p*, lo_p*, hi_p*)(p* = 최솟값을 낸 포트), 선언이면 None -- as-built 형식 그대로.
  - `icmr_v` = 포트 창 교집합 폭 = min_p hi_p − max_p lo_p(빈 교집합은 음수 폭 그대로, as-built 뜻). `window` = (max lo, min hi), `v_icm` = V_p*.
  - 분해능(새 상수 없음, 창 필드의 `tol_v`에서): `margin_resolution` = p* 창의 `tol_v`, `icmr_resolution` = 아래 끝을 정한 포트의 `tol_v` + 위 끝을 정한 포트의 `tol_v`(as-built '구속 하한 누적 + 구속 상한 누적'과 같은 꼴). `tol_v`가 None이면 None.
  - **정의 불능**(N3.14, 세 metric 모두 값 None): 입력 포트 없음 `no_input_port`(as-built 코드, category `definitional`), 어느 포트든 `missing`이 있으면 그 code(category `numeric` -- 단 `input_window_operating_point_mismatch`(선언과 동작점의 불일치로 창이 정의되지 않음, 4.7-3a 3)와 `input_window_f_component_undeclared`(F 성분 미선언 포트의 창이 정의되지 않음, 4.7-3 3)는 `definitional`; detail에 `("port", net)`을 더함). **커널 ICMR 선언 제약**은 이 metric 값을 읽으므로 같은 `Undefined`(예: `input_window_unsettled`)로 판정 불능이다(계획 N3.14 공통 실패 규약 -- 새 경로 없음; 사용자 결정 O-61 P5 '커널 ICMR 선언 제약은 정의 불능'). 기록 형식은 as-built `Undefined(quantity, code, category, detail)`(`E/metrics/mna_types.py:41-48`, category ∈ `UNDEFINED_CATEGORIES`)이고 세 metric 이름마다 한 원소. **원인이 여럿일 때**(v1.12.1 N3): 한 metric에 원소 하나 -- definitional code가 numeric code보다 앞서고, 같은 category 안에서는 `ports` 순서 첫 포트. **측정 구성 정의 불능의 경로**(v1.12.1 검증 M7): `metrics_aux`·`metrics_icm_front`는 `graph.icm_config.config`가 None이면 `ports`를 만들지 않고 `IcmConfig.undefined`를 `config_undefined`로 넘긴다; `icm_window_metrics`는 그 원소 u마다 `Undefined(q, u.code, u.category, u.detail)`를 q ∈ {`icmr_v`, `icm_margin_v`, `required_input_cm_v`}마다 만들어 `undefined`에 싣는다 -- q = `IcmWindow`·`SwingIcmr` 칸 이름 = metric 등록의 `entry.field`(`E/metrics/registry.py:61-62`)여야 한다: `metric_value`(`E/metrics/evaluate.py:14-27`)가 `u.quantity == entry.field`로 거르므로 다르면 원인이 `unrecorded_cause`로 바뀐다. `IcmConfig.undefined` 원소 자신의 quantity는 `"icm_config"`(구성 기록)이고, 이 사상은 metric 단위 원인 기록(결과 기록, graph 필드 아님)이라 값 사본이 아니다. 구성 None이 포트 `missing`보다 앞선다(포트를 만들지 않음). 예: `Undefined("icm_margin_v", "input_window_end_missing", "numeric", (("end", "hi"), ("port", "vin_p"), ("reason", "window_end_solve_failed")))`.
  - `IcmWindow`(새 frozen dataclass, `E/metrics/aux_types.py`) 칸 = `icmr_v`, `icm_margin_v`, `required_input_cm_v`, `window`, `v_icm`, `input_dc`, `icmr_resolution`, `margin_resolution`, `undefined`(tuple[`Undefined`]), `model_error_ref`(정확도 표기 -- card ME-1 판정 기록 id, ME-1 전 None = 보고에 '보류', 4.7-2), `sources`(front 값만 -- tuple[(net, (kind, field))], 그 포트 값을 낸 graph 필드의 **참조**; 커널 값은 `()` -- 모든 포트가 `node.dc_window_cfg`). **사본 칸 없음**(v1.12.1 검증 M6·gap I-2, graph 단일 정본 규칙 2·4): 옛 `criterion`·`config` 칸은 두지 않는다 -- 보고 'β = 1 기본'은 같은 스냅샷의 `graph.icm_config.config`(`"follower_beta1"`)를, 기준 표기는 `sources`가 가리키는 필드를 직접 읽는다(다듬은 포트 = `node.dc_window_def_refined`의 `criterion` 칸; cfg 포트 = 그 필드 정의의 기준 '+tol 판정'(계획 N3.8 '창 필드' -- 필드 정의에서 오는 것, 새 상수 없음); DE-1 뒤 `node.dc_window_def` 포트 = '정의 기준'). 측정 구성 정의 불능의 metric 경로는 위 '측정 구성 정의 불능의 경로'. `input_window_end_missing`의 detail `reason`은 4.7-4의 사유 셋(`window_end_solve_failed`·`window_end_k_max_exhausted`·`window_end_saturation_unconfirmed`) 가운데 하나다.
  - **출력 전용 필드 선언**(계획 N6.6 완료 조건 (5), 사용자 원칙 'graph 계산값 소비' -- 새 필드마다 엔진 소비자 ≥ 1 또는 출력 전용 선언): 이 card에서 엔진 안 소비자가 없는 아래 넷은 **출력 전용**이다 -- (1) `graph.metrics_icm_front`(front 점 스냅샷 보고 값; 엔진 소비자 = card EO-1 oracle 입력 생산자, EO-1 전 출력 전용) (2) `RefinedWindow.criterion`(변화표 원인 칸·보고가 필드 참조로 직접 읽음)·`IcmWindow.sources`(포트별 출처 필드 참조 -- 보고가 기준 칸을 찾는 길) (3) perf `window_end_solves`(WP-10 비용 보고) (4) `IcmWindow.model_error_ref`(card ME-1 전 늘 None, 보고 '보류'; ME-1이 생산·소비). 엔진 소비자가 있는 새 필드: `node.dc_window_def_refined` → `metrics_icm_front`, `Window.input_status`·`tol_v`·`status_detail` → `metrics_aux`(`IcmPort`). 출력 전용 선언은 EO-1·ME-1 병합 때 각 design이 소비자로 바꾼다.
- **커널**: `metrics_aux`가 입력 포트의 `node.dc_window_cfg`·`graph.icm_config`·`node.dc_colour`(READS에 더함; `node.dc_window`는 읽지 않는다 -- 계획 N6.6 범위 1 '커널 탐색만', v1.12.1 W1 철회)를 읽어 `graph.icm_config.tied_ports`의 포트를 뺀 입력 포트로 `IcmPort` 열을 만들고(v1.12.4 gap G4 -- 위 `ports`) `icm_window_metrics`를 부른다. 창 출처 = 모든 구성에서 `node.dc_window_cfg`, 구성 None이면 `config_undefined` 경로(위 M7).
  - `ls_swing` 새 서명 = **`ls_swing(devices, rails, node_v, outputs, diff_outputs=False) -> SwingIcmr`**: 출력 스윙만 낸다(입력 창 계산 `:107-118`, 인자 `inputs`·`input_dc_v`, `no_input_port` 정지와 입력 넷의 `node_v_missing` 검사, 그 문언 삭제 -- 계획 N6.6 범위 3). 반환 `SwingIcmr`의 입력 칸은 기본값(`icmr_v`·`icm_margin_v` = None, `window` = `()`, `v_icm`·`required_input_cm_v` = None, `input_dc` = `""`, 두 분해능 None)이고 `undefined`에는 스윙 사유만 든다.
  - **합치는 규칙**: `metrics_aux`가 `dataclasses.replace(swing, icmr_v=iw.icmr_v, icm_margin_v=iw.icm_margin_v, window=iw.window, v_icm=iw.v_icm, required_input_cm_v=iw.required_input_cm_v, input_dc=iw.input_dc, icmr_resolution=iw.icmr_resolution, margin_resolution=iw.margin_resolution, undefined=swing.undefined + iw.undefined)`로 한 `SwingIcmr`을 만든다(`iw` = `IcmWindow`). 그래서 `SwingIcmr` 형식·결과 JSON·`swing_icmr` 보고 행 키·분해능 칸 이름(`RESOLUTION_FIELDS`, `metrics_aux.py:58-62`)은 그대로다(형식 불변, IT-Q2).
  - `bounds`(모든 넷의 경로 합 구간, `ls_fields` 입력)는 card DE-1 전까지 그대로다. 단서: as-built 넷 집합은 `set(inputs)`를 더했으나 입력 포트는 MOS gate라 소자 단자 넷에 이미 들고, 소자에 닿지 않는 입력 포트만 `bounds`에서 빠진다(그 넷은 `ls_fields`가 읽지 않는다).
  - 등록: `E/_module_map.py`의 `metrics/ls_swing.py` 행 서명 갱신, `metrics/icm_window.py` 행 추가.
- **front·보고**: 새 `@compute_block` `metrics_icm_front`(상수 `METRICS_ICM_FRONT_WRITER`, 파일 `E/metrics/icm_front.py`, 진입점 `icm_front`, test `E/tests/metrics/test_icm_front.py`), READS `("node", "dc_window_def_refined")`·`("node", "dc_window_cfg")`·`("graph", "icm_config")`·`("node", "dc_v")`·`("node", "port_direction")`·`("node", "dc_colour")`, extras = 선언 입력 DC 또는 None. **포트별 출처**(계획 N6.6 범위 2 'KVL 고정·단일 입력 회로 그대로 구성의 포트는 N3.8 선형 감도 끝만 정의되는 구성의 정본 칸', 사용자 결정 O-61 P3·O-63 (4); 어느 칸을 읽을지는 graph에 이미 있는 분류로 정한다 -- 새 규칙·상수 없음): `node.dc_window_def_refined` 항목이 있는 포트는 그 칸; 항목이 없는 포트(4.7-4 2 '쓰지 않는 포트' (a)~(d))는 커널 갈래와 같은 출처 `node.dc_window_cfg`의 그 포트 항목을 읽고 위 '창 필드에서 만드는 규칙'으로 `IcmPort`를 만든다(선형 감도 끝만 정의되는 구성의 포트는 그 칸의 값('추정'), F 성분 미선언 포트는 `input_window_f_component_undeclared`, 출발 창 미수렴 포트는 `input_window_unsettled` -- 같은 사유로 정의 불능, 사용자 결정 O-64 (2)). 이 블록은 출력 구조·구성을 다시 판정하지 않는다(판정 자리 = `dc_window_refine` 하나). 포트별 출처는 `IcmWindow.sources`에 필드 참조로 남는다(사본 칸 없음 -- 위 `IcmWindow`). 구성 None이면 M7 경로. 포트 집합 = 커널 갈래와 같이 `graph.icm_config.tied_ports`(이 블록 READS `("graph", "icm_config")`)를 뺀 입력 포트(v1.12.4 gap G4 -- 위 `ports`). WRITES `("graph", "metrics_icm_front")` = {METRICS_KEY: `IcmWindow`}. 등록: `SS_WRITES`(`E/sizing/s2_values.py:173-179`)에 `(METRICS_ICM_FRONT_WRITER, (("graph", "metrics_icm_front"),))`(상수는 `METRICS_AUX_WRITER` 옆), `E/_module_map.py` 행. 호출 자리는 4.7-4 5와 같다(`refine_front_windows` 안 `dc_window_refine` 바로 뒤). front 점의 보고 값(그 점 스냅샷의 이 필드 -- EO-1 oracle 입력 생산자·U16 보고서가 읽는다, DEC-98 oracle 대조 값)은 이 필드에서 읽는다 -- run 레코드 키·형식은 그대로, 값 출처만 다르다. **제약 판정은 커널 값**이다(DEC-74; 'front 판정' = oracle 대조·보고 값, 계획 N6.6 범위 1 A-N3).
- **미수렴 front 처리**(v1.12.2, 사용자 결정 O-64 (2), 계획 N6.6 범위 1 '그 front 값의 처리' -- 새 경로·새 칸·새 상태 없음): 출발 창 미수렴 포트가 있는 점(4.7-4 2 (d))의 front 세 metric(`graph.metrics_icm_front`)은 `Undefined(_, "input_window_unsettled", "numeric", …)`로 정의 불능이다. (가) **선언 제약이 걸린 값**(선언 `icmr_v`·`icm_margin_v` 제약): 그 제약 판정은 커널 값(DEC-74)이고 같은 점 `node.dc_window_cfg`가 미수렴을 이어받아(4.7-3b '커널 상태 이어받기' (가)) 이미 정의 불능이다 -- 기존 `ss_constraint_rows`가 행 없이 `unmeasured`에 (metric, op, `"input_window_unsettled"`)를 싣고(`E/search/ss_constraints.py` 머리 '값 None(Undefined)'), 그 점은 최종 `front`(봉인 + 모든 ss 제약 측정 -- `E/search/eps_sweep.py:33-38` `_CLASSES`)에서 빠져 `unmeasured_front` 안 비지배 재필터(`_filter` → `nondominated`)를 거친다. 원인 = 그 unmeasured code(미수렴 사유) -- fail-closed. (나) **제약 없는 보고 값**: 그 점의 front 분류는 바뀌지 않고 `graph.metrics_icm_front`의 `undefined`에만 원인이 남는다(보고에서만 정의 불능). 두 갈래 모두 엔진 `ss_constraints` 기존 규칙과 같다(계획 같은 문단). card 0의 'front가 빈 회로 수'(4.7-8a)가 (가)의 발동을 잰다. DE-1 뒤 출발 창 = 정의 창 `node.dc_window_def`에도 같은 상태가 이어진다(DE-1 인계 -- 4.7-9).

**4.7-6 소비자 정리(계획 N6.6 소비자 표 + A10)**: `fd_jacobian._steps`는 `node.dc_window` 가운데 writer relation이 `free_window`인 넷(W4 뿌리)만 y 스텝에 쓴다(입력 포트 항목이 늘어도 y 키 색인이 바뀌지 않게). `E/sizing/CONTRACT.md` 소유표 행 `node.dc_window`(`:202`, master `2e707d5d`에서 다시 잼)의 범위 = '모든 입력 포트와 W4 뿌리'·형식 `Window`(칸 둘 추가), 새 행 `node.dc_window_def_refined`(writer `dc_window_refine`)·`graph.metrics_icm_front`(writer `metrics_icm_front`), 14.6절 문언. 그 밖 같은 변경에서 고치는 자리: `E/metrics/CONTRACT.md:1235`(`ls_swing` 서명 행), `:1286`(V_icm = 첫 포트·y_icm 문언), `:1334`(SP-2 대기 `icm_margin_v`), `E/metrics/aux_types.py:160-172`(`SwingIcmr` docstring의 V_icm 문언, `IcmPort`·`IcmWindow` 추가), `E/tests/metrics/test_aux_types.py:40`(`SwingIcmr(None, None, None)` -- 형식 불변이라 기대 그대로, 새 타입 test 추가는 test 주체), `E/sizing/s2_values.py` `DC_WRITES`·`SS_WRITES`(→ `S2_WRITERS`), `E/_module_map.py`(새 파일 네 개·`ls_swing`·`saturation_window` 서명 행). `headroom_bound`의 창은 대상이 아니다.

**4.7-7 test interface(IT-2, test 작성 주체 -- 소스 없이)**: 공개 진입점 `dc_columns`(서명 불변), `refine_input_windows`, `icm_front`, `refine_front_windows`(search), 순수 함수 `icm_window_metrics`·`saturation_window`(새 서명 `(unknown, roots, values, gradient, rows, *, slope=None) -> (dlo, dhi, slope) | None` -- 4.7-3 2; `roots` 원소 = 넷 또는 쌍 `(행 넷, 고정 넷)`, `slope`를 주면 감도 연립 없이 끝만)·`ls_swing`(새 서명)·`writers_in_scope(base, blocks) -> frozenset`(card IT-2e, `E/sizing/seal_versions.py` -- 4.7-3c, v1.12.9), 타입 `Window`·`RefinedWindow`·`WindowEnd`·`IcmPort`·`IcmWindow`. **`rows` 입력 꼴 변경**(검증 W2): as-built `saturation_window`는 4원소 행 `(d, s, sign, slack)`을 받았다(`E/sizing/input_window.py:57`); 새 꼴은 `region_rows`의 5원소 `(a, b, sign, slack, kind)`(4.7-3a 1)이고 `saturation_window`는 `kind`를 창 계산에 쓰지 않는다(끝 정의는 행마다 `slack + sign·(s_a − s_b)·Δ ≥ 0`의 교집합 그대로). 필드·형식은 4.7-2, 사유 이름은 4.7-4 3·4.7-5. 단언(계획 N6.6 완료 조건 (0)~(6)을 측정할 수 있는 꼴):
- K1 입력 DC 선언 toy: 입력 포트 `node.dc_window` 항목이 있고 `input_status == "measured"`(base는 항목 없음 -- red). 미선언 2입력 toy: 두 포트 항목 모두 있음(base는 뿌리만 -- red). 창을 잴 수 없는 toy(VDSAT 열 없는 LUT 축소 픽스처 등): 뿌리 `input_status == "unmeasured"`, 세 metric 정의 불능 `input_window_unmeasured`.
- K2 커널 선형 창 = 손계산 오라클(toy 연결의 선형 감도 손계산, '추정' 정확도 표기). 뿌리 아닌 포트 창 = 그 해의 V_p + s_p·(뿌리 끝 − x)(같은 감도).
- K3 커널 평가(FD 열 포함) 중 `dc_window_refine`·`metrics_icm_front` `computes` 0(`RunCounters`), perf `window_end_solves` 증분 0. **graph 규칙 기준 단언**(4.7-4 5, 검증 W4): 수락 반복이 일어난 toy 실행에서 (a) 수락 뒤 다음 커널 평가 결과의 스냅샷과 `state["parent"]`의 스냅샷에 writer가 `dc_window_refine`·`metrics_icm_front`인 필드가 없음(커널 밖 writer 필드가 parent로 들어가는 길 없음 -- 봉인 4가 그 필드를 잡지 않으므로 길 자체가 없어야 한다) (b) S3 색인 평가 키 부분(as-built `sctx.cache`)의 모든 값의 스냅샷에도 그 필드가 없음 (c) 같은 θ를 `refine_front_windows`로 두 번 부르면 둘째는 두 블록 `RunCounters` outcome이 `graft`(또는 `reuse`)이고 `computes` 증분 0, perf `window_end_solves` 증분 0 (d) 엔진 소스에 S3 색인 밖 새 결과 캐시 없음(`git grep` -- `front_cache` 0).
- R1 다듬은 창: 끝이 풀린 toy에서 `lo_end.reason is None`·`hi_end.reason is None`이고 `lo == max(min(lo_end.v, hi_end.v), rail_lo)`·`hi == min(max(lo_end.v, hi_end.v), rail_hi)`(감도 음수 포트는 `lo`가 `hi_end.v`에서 온다 -- P (a)와 같은 toy로 둘 다 확인), 한 끝 결측 toy(R2)에서 그 포트 `lo is None and hi is None`, 뿌리 아닌 포트의 `lo_end.x`는 뿌리 `lo_end.x`와 같고 `lo_end.v`는 그 x로 뿌리를 고정해 푼 해의 포트 전압(손계산 오라클과 같음).
- R2 red 변형 둘: 끝 풀이 실패 toy(끝 x에서 어느 writer의 LUT 정의역을 벗어나 풀이가 실패하는 연결) → 그 끝 `reason == "window_end_solve_failed"`, `v is None`, `metrics_icm_front`의 세 metric 정의 불능(`input_window_end_missing`); `k_max` 소진 toy → `reason == "window_end_k_max_exhausted"`, 같은 정의 불능. **red 사유**: base에는 `refine_input_windows`·`icm_front`·필드가 없어 import에서 실패한다(존재 부재 red -- 검증자는 실패 단언 목록에 'ImportError'로 적는다). 행동 red(외삽·이전 끝을 값으로 냄)는 as-built `_refine_ends`의 성질이고 base에서 직접 단언할 공개 진입점이 없다. **장애 주입 허용**: 자연 toy로 만들기 어려우면 monkeypatch를 쓸 수 있다 -- 주입 지점은 `gmid_engine.sizing.window_refine.solve`(x 고정 풀이에서 `FAILURES` 원소를 던지게)와 `gmid_engine.sizing.window_refine.k_max`(상한 1)로 한정한다(4.7-4 모듈 수준 이름). 그 밖 내부 이름 주입은 하지 않는다(이 R2·L9 (c)의 장애 주입 범위 -- L11 (e)의 블록 실패 주입(`ComputeBlock.__call__` 감쌈, 재연 선택 사례의 블록 인스턴스 `fn` 교체)은 L11 (e)가 정한다).
- M1 커널 `icm_margin_v`·`icmr_v`·`required_input_cm_v` = `icm_window_metrics`(`node.dc_window_cfg`)와 같은 값(모든 구성 -- `as_is_single_input` toy 포함, v1.12.1 W1 철회), front 값 = `icm_window_metrics`(`node.dc_window_def_refined`)와 같은 값(선형 감도 끝만 정의되는 구성(KVL 고정·`as_is_single_input`)의 포트와 미수렴 포트는 `node.dc_window_cfg`에서 -- L12 (a)(c)).
- W1 배선: 외층이 도는 toy 실행(`find_front`)에서 front 점마다 `snapshot_ref`가 가리키는 스냅샷에 `graph.metrics_icm_front`가 있고 그 값 = 같은 스냅샷 `node.dc_window_def_refined`로 부른 `icm_window_metrics` 값(front 점 보고 값 = `metrics_icm_front`); 수락 반복마다 `dc_window_refine` `computes` ≤ 1, 같은 θ front 점에서 추가 `computes` 0; `kernel_calls`가 두 블록 때문에 늘지 않음.
- M2 `git grep`(계획 N6.6 완료 조건 (2), 사용자 결정 O-61 P2): `ls_swing`에 입력 창 계산 0; 창 끝 식(행 교집합)을 가진 함수 = `input_window.saturation_window` 하나; 그 함수를 부르는 블록 = 셋 -- `dc_columns`(θ 프레임 창 `node.dc_window`)·`dc_window_refine`(`node.dc_window_def_refined`) 둘은 공용 helper `_helpers_dc_solve.Circuit.input_windows`를 거쳐, `icm_config`(`node.dc_window_cfg`)는 직접(4.7-3b (4)) -- 그 밖 호출·끝 식 재구현 0(`headroom_bound` 제외 -- LUT 격자 최솟값 상한, 다른 개념).
- M3 포트 창 재계산 0: 다듬은 포트 창이 `_sensitivities` 외삽·κ 경로 합·별도 노드 풀이를 하지 않음(`git grep` + G-10 + WP-10 중복 인자 계측).
- P(계획 완료 조건 (7), O-49): (a) 감도 음수 포트 toy -- 커널 창·다듬은 창 모두 포트 창 lo ≤ hi이고 = 두 끝 전압의 [min, max](손계산; base는 lo > hi -- red) (b) 입력 DC 둘 선언 toy -- 두 포트 창 끝의 차 = 선언 차(같은 x 이동, 포트별 따로 훑은 창이면 red) (c) (ii) 끝 toy(풀린 x의 해에서 어느 행 여유 < 0이거나 행을 못 만드는 연결; 자연 toy가 어려우면 4.7-7 R2와 같은 주입 지점 `window_refine.solve`만 사용) -- 그 끝 `reason == "window_end_saturation_unconfirmed"`, front 세 metric 정의 불능 (d) `dc_window_refine` 블록 READS에 `("node", "dc_v")` 없음 (e) `RefinedWindow.criterion == "tol_judgement"`, front `IcmWindow.sources`의 다듬은 포트 참조 = `("node", "dc_window_def_refined")`, `IcmWindow`에 `criterion`·`config` 칸 없음(사본 칸 부재 단언 -- v1.12.1 M6).
- D(계획 완료 조건 (9), O-54, 4.7-3a): `triode` 선언 소자가 훑기 중 포화로 가는 toy → 그 점이 창 끝(손계산 오라클: 행 `(d, s, −부호, VDsat − VDS − tol_VDsat)`의 영 교차; base는 선언 소자를 행에서 빼 놓침 -- red). `off` 선언 소자가 켜지는 toy는 4.7-3a 2 S-4 갈래를 따른다 -- (S4-가)이면 이 card test(창 끝 = V_on 영 교차), (S4-나)이면 부재 단언(`region_rows` `kind` 집합 = {`"sat"`, `"triode"`}, 공용 전도 판정 함수·V_on 역함수 호출 0). 동작점 불일치(4.7-3a 3): 선언 `triode` 소자가 커널 마지막 풀이에서 포화인 toy → 그 성분 모든 입력 포트 `input_status == "op_mismatch"`, `status_detail == (("devices", (그 소자,)),)`, 같은 점 봉인 거부(선언 오류); 그 `Window`들로 부른 `icm_window_metrics`의 세 metric이 `Undefined(_, "input_window_operating_point_mismatch", "definitional", …)`(base는 code 없음 -- red). `off` 소자 불일치 toy는 EO-1 공용 전도 판정 함수가 있는 base에서만 잰다(S-4와 같이 대기).
- L8(계획 완료 조건 (8), 4.7-3b): (a) 되먹임 미선언 차동 입력·단일 출력 toy(출력 = W4) -- `node.dc_window_cfg`·`node.dc_window_def_refined` 끝 = follower 연립 끝(손계산 오라클), `graph.icm_config.config` = `"follower_beta1"`(base는 순서 창 비례 끝 -- red); 같은 toy에서 커널·front 세 metric의 포트 집합 = 묶이지 않은 입력 포트뿐(`tied_ports`의 반전 입력을 포함해 `icm_margin_v`·`icmr_v`·`required_input_cm_v`를 내면 red -- v1.12.4 gap G4, 손계산 = 비반전 입력 창 하나로 낸 값) (b) 되먹임 선언 단일 출력 toy(입력 둘; v1.12.5·v1.12.6 -- 계획 v6.27 N6.6 완료 조건 (8)(b), 사용자 결정 O-79·O-80 R1·O-81·O-82; 판정 = 4.7-3b (1) DC 되먹임 판정): (b1) 용량만 선언(Cf 출력–in−) → `graph.icm_config.config is None`, `IcmConfig.undefined`에 `icm_config_feedback_no_dc`(`definitional`) 하나, `inverting_port` = in−, `tied_ports` = (), `node.dc_window_cfg` 항목 없음, 세 metric(`icm_margin_v`·`icmr_v`·`required_input_cm_v`)이 그 code로 정의 불능(M7), 선언 `icm_margin_v` 제약 점이 unmeasured(S-OS1 단언과 같은 꼴 -- 검증 N9)(창 값이 나오면 red) (b2) 저항 되먹임(R 출력–in−) → `config == "declared_feedback"`, 선언 구성 창 = `node.dc_window_cfg` 끝이 S-3 망(저항이 G에 든 봉인점 회로, 용량 열림)에 반전 입력 노드 KCL 닫음((3))을 더한 연립의 끝(손계산) (b3) **경로 판정 red 변형**: Cf(출력–in−) + Rb(in−–레일) → (b1)과 같은 정의 불능(소자 종류 판정이면 `declared_feedback` 창 -- red), R(in−–레일)만 선언 → 같은 정의 불능(같은 red), T망(R1 출력–X, R2 X–in−만 선언, R3 X–접지) → `declared_feedback`(선언 소자만 보는 판정이면 정의 불능 -- red); R2 우선 toy(입력 하나 + 용량만 선언) → `config == "as_is_single_input"`, `undefined`에 no_dc code 없음(검증 N4; spec 검사가 이 꼴을 받는지 미확인 -- 받지 않으면 test 작성 주체가 멈추고 보고); `config` 값 집합(744 (1))은 그대로 (c) 차동 출력·선언 없음 → `icm_config_differential_output_undeclared` (d) KVL 고정 출력 toy(RL 출력–레일) -- `node.dc_window_cfg` 끝 = `kvl_sensitivity` 감도로 `saturation_window`가 낸 끝(손계산), '추정' 표기, 출력의 `node.dc_output_structure == "kvl_fixed"`, 그 포트의 `node.dc_window_def_refined` 항목 없음(L12 (c)); 분류 자체의 toy는 4.7-1a OS (a)~(j), 이 card 창 쪽 -- 핀 뺀 성분에 F′ 없는 W3 목표 출력(OS (d)) → `node.dc_window_cfg` 끝 = 목표값을 x로 바꾼 θ 고정 연립 끝(손계산), `node.dc_window_def_refined` 끝 = `fixed_values[출력]` = x로 푼 끝 x 고정 풀이의 끝(손계산 -- v1.12.3 gap N2), 단단한 경로 위 W3 출력(OS (e)) → 끝 = `kvl_sensitivity` 감도로 낸 끝(손계산)이고 다듬은 창 항목 없음(목표값을 x로 바꾼 follower 끝이 나오면 red -- O-64 (1) 경우 1), `IcmConfig`에 `output_structure` 칸 없음(v1.12.2); OS (f) 꼴 toy(멈춤 S-OS1) → `graph.icm_config.config is None`, `IcmConfig.undefined`에 `icm_config_output_root_w3`(`definitional`) 하나, `node.dc_window_cfg` 항목 없음, 세 metric이 그 code로 정의 불능(M7), 선언 `icm_margin_v` 제약 점이 unmeasured(창 값이 나오면 red -- v1.12.3 MF-2); 되먹임 선언 차동 출력 toy(멈춤 S-OS2) → 같은 꼴로 `icm_config_differential_output_structure`(MF-4); v1.12.7(4.7-3b (1) 'IT-2c 갈래 순서'; 차동 갈림 toy는 S-OS2 card 몫 -- O-87 (1)): `device.unsupported` 원소 하나를 넣은 합성 스냅샷으로 블록을 부름 → `icm_config_feedback_element_unsupported`(운영 경로는 S1이 먼저 멈춤 -- 검증 R1) (e) 포트 role 이름 맞바꿈 toy에서 같은 `inverting_port`, 후보 0·2·분해능 이하 toy → 세 code, 입력 DC 둘 선언 + follower toy에서 `tied_ports`의 포트는 x 묶음 밖.
- L10(완료 조건 (10)): (a) 착수 실측 기록 -- **DC 망을 만드는 자리에 루프 절단이 적용되지 않음**(v1.12.7 -- 계획 v6.28 완료 조건 (10)(a) 새 문언, 사용자 결정 O-85 (2)·O-86 M1·N1·N4, IT-2c 착수 조건 (iv); v1.12.6 '멈춤 S-FB1'은 이 문언으로 해소): (i) 정적 -- 절단 넷 순수 함수 `feedback_cut_nets`의 **함수 객체 참조(load -- 호출·값으로 넘김·별칭 모두, import 경로와 무관, docstring·주석 제외)**를 엔진 소스(`tests/` 제외)에서 센다: (10)(f)의 넷 자리(`spec_elements`·`spec_views`·`icm_config`·`noise_plan`)에만 있고 `E/sizing` 전체·`ss_nodal`(`E/metrics/ss_nodal.py`)·`E/metrics/_helpers_nodal.py`에는 0. `gmid_engine.authoring` export로 이름 문자열 grep이 우연히 0이 되는 것은 증거로 쓰지 않는다(검증 R5) (ii) 동적 -- 그 함수의 호출 수를 그 함수의 `__code__`로 센다(이름 묶기와 무관 -- 검증 R4). 구간 = `dc_writer_plan`(`E/sizing/writer_plan.py:117-118`; `@compute_block`이 만든 `ComputeBlock` 인스턴스라 구간 기준 code = `dc_writer_plan.fn.__code__`, `E/core/compute_block.py:118·122`)·`run_kernel`(`E/sizing/kernel_run.py:65`)·`seal_dc`(`E/sizing/seal.py:48`)(둘은 평함수 -- `__code__` 그대로)의 실행 구간에서 0. 측정 입력 = 13회로 + L8 (b) 선언 되먹임 toy, graph reuse 없는 실행(새 입력 버전). 양성 대조 둘 다 필수: (가) 같은 실행에서 같은 계수기가 구간 밖 호출 ≥ 1을 잡음(예: spec 로드의 `spec_elements`, 봉인 뒤 `icm_config`) (나) 구간 안에서 그 함수를 부르게 한 red 변형에서 계수 > 0 (iii) 의미 판정 = 아래 (e) 손계산 일치(`icm_config`의 호출은 끝점 식별만 한다). 함수를 다른 모듈로 옮겨 정적 0을 맞추는 것은 측정 게이밍이라 기각(계획 (10)(a)) (b) `git grep` writer 하나씩 -- `node.dc_window` = `dc_columns`, `node.dc_window_cfg` = `icm_config`(완료 조건 (2)와의 정합 -- 사용자 결정 O-61 P2: 창 끝 함수 `saturation_window` 하나·부르는 블록 셋, M2) (c) `conductance_matrix(ss.circuit` 자리 = `ss_nodal` 하나, 같은 입력 버전에서 `ss_nodal` `computes` 증분 0(G-10)·WP-10 중복 인자 0, `icm_config`·`metrics_aux` READS에 `("graph", "ss_nodal")` (d) `kvl_sensitivity` 정의·호출 자리 하나(`git grep`), 다듬은 창이 KVL 구조에서 끝 풀이 호출 0, KVL 끝을 담는 칸 = `node.dc_window_cfg` 하나(`IcmConfig`에 `kvl` 칸 없음 -- 완료 조건 (5), O-61 P3) (e) 저항 되먹임 toy(R 출력–반전 입력)와 저항+용량 혼합 toy(Rf∥Cf, 출력–반전 입력)에서 DC 망 = 선언 소자를 끊지 않은 봉인점 회로(용량 제외·저항 포함)로 잰 창 = 손계산(v1.12.6 -- 계획 완료 조건 (10)(e), 사용자 결정 O-81 (1) MF-1; 용량만 선언 toy는 L8 (b1)) (f) `NodalSystem`의 `g`·`factor` 모든 ndarray `flags.writeable is False`·제자리 쓰기 `ValueError`(red 먼저 -- 4.7-3b W4) (g) `as_is_single_input` toy(단일 입력, 고임피던스 출력)에서 `node.dc_window_cfg` 항목 있음, 끝 = `graph.ss_nodal` 위 구동 = 입력 포트 감도(`kvl_sensitivity`, 닫음 없음)를 `slope`로 넘긴 `saturation_window` 끝(손계산), 커널 metric = `icm_window_metrics(node.dc_window_cfg)`, `metrics_aux` READS에 `("node", "dc_window")` 없음(base는 cfg 없음 -- red; v1.12.1 W1 철회); 같은 toy에서 `node.dc_window_def_refined`에 입력 포트 항목이 없고 끝 풀이 호출 0(perf `window_end_solves` 증분 0), front `icm_margin_v` = `icm_window_metrics`(그 포트의 `node.dc_window_cfg`) 값, `IcmWindow.sources`의 그 포트 참조 = `("node", "dc_window_cfg")`(다듬은 창 블록이 그 포트를 쓰면 red -- 사용자 결정 O-63 (4)). (h) 구성 None toy -- 세 metric `undefined` 원소의 quantity가 칸 이름(`icmr_v`·`icm_margin_v`·`required_input_cm_v`)이고 `metric_value`가 `unrecorded_cause`를 내지 않음(M7). (i) **DC 되먹임 판정 자리 하나**(v1.12.6 -- 계획 완료 조건 (10)(f), 사용자 결정 O-82·O-83 R-M1·R-N1; L10 (f)는 `NodalSystem` 단언이 쓰고 있어 새 기호): `git grep` -- 술어 `_dc_feedback_reaches` 정의 1곳(`icm_config.py`), 둘째 구현 0; `icm_config` READS에 일곱 `device.element_class`·`device.kind`·`device.pins`·`device.dc_nets`·`device.unsupported`·`node.is_rail`·`node.port_direction` 있음(블록 READS 단언), `icm_config.py`의 지원 kind 상수 참조 0(`MOS_KINDS`·`SUPPORTED_PASSIVE_KINDS`·`SUPPORTED_SOURCE_KINDS` 모두, 예외 없음 -- 계획 (10)(f); MOS는 `device.element_class == ELEMENT_MOS`로 식별(원소 분류 어휘라 지원 kind 상수 아님 -- O-88), 이상 전류원 제외 = `element_class == ELEMENT_SOURCE and kind == CURRENT_SOURCE`(`ss_circuit.py:57`과 같은 술어·같은 상수, `CURRENT_SOURCE`는 kind 어휘 -- 넷째 커밋), g→d·g→s 단자 이름은 `MOS_TERMINAL_NAMES`, `MOS_GATE` 직접 import 0, `device.unsupported` 둘째 계산 금지 -- v1.12.7 둘째·셋째 커밋, 검증 MF-1·O-88), 술어 서명에 출력 인자 `output`(MF-2), 새 graph 필드·cache·sctx 슬롯·`IcmConfig` 값 칸 0; 술어가 `config`·T_p를 읽지 않음; 절단 넷 순수 함수 `feedback_cut_nets` 정의 1곳(`_feedback_cuts.py`)·직접 호출 자리 넷(`spec_elements`·`spec_views`·`icm_config`·`noise_plan`), `def input_terminal_nets`·`def _input_side` 0, 함수 레지스트리 행 같은 변경; **동작 동일성 test**(계획 N6.6 IT-2c (iii)) -- 같은 입력에서 옛 두 함수와 순수 함수의 절단 넷이 같음(입력 넷 단자 0개·1개·2개 갈래). 옛 두 함수는 같은 변경에서 지워지므로 (가) 옛 함수의 공개 경로 test(`E/tests/authoring/test__feedback_cuts.py` -- 로더 code `feedback_element_not_on_input`·`feedback_cut_ambiguous`·`default_views` `cuts`; `E/tests/metrics/test_noise_plan.py:22` 절단 넷)를 바꾸지 않고 head에서 green (나) 같은 파일 `test__feedback_cuts.py`(모듈 1:1)에 순수 함수 0·1·2 갈래 직접 단언 -- 기대값은 옛 docstring 규칙(`_feedback_cuts.py:4-6`)과 손으로 읽은 단자에서 만든다(옛 함수 사본을 test에 두지 않음).
- L11(완료 조건 (11), 4.7-3c, 사용자 결정 O-61 P1): (a) parent에 `dc_window_refine` 필드를 실은 픽스처 → child 스냅샷 커밋에 그 필드 없음; base writer 필드(S1·S1v·계획·S0 탐색·metrics S0 -- `ctx.base.block_versions`에 있는 writer)는 child에 남음(지우면 red); parent 없는 평가(스냅샷 = `ctx.base`)가 봉인 4를 통과함(keep을 옛 `_CONTEXT_WRITERS`로 구현하면 red); base writer 버전이 `ctx.base`와 다른 parent는 `ValueError`로 거부 (b) 봉인 4 위반 픽스처 둘 -- base writer ∪ 호출 블록 밖 writer 필드 → `SEAL_FAIL`·detail `foreign_writers`, base writer ∩ 호출 블록 ≠ ∅ → `SEAL_FAIL`·detail `base_call_overlap`(둘 다 통과면 red -- 게이트가 실제로 거부함을 먼저 확인) (c) 같은 θ ss 재평가 → ss 블록 outcome `graft`, `computes` 증분 0 (d) (v1.12.8, 사용자 결정 O-94 (2)) 같은 θ parent 재평가 → 봉인 항목 블록 여덟은 child에 남아 outcome `reuse`(keep을 커널 블록만으로 구현하면 `graft` -- red), `dc_seal_report`는 `graft`(keep에 넣으면 봉인 4 `foreign_writers` -- red), `computes` 증분 0; `seal_versions(snapshot, calls, None)`·`seal_dc(…, base=None)`·`seal_dc`에서 `base` 생략 → `TypeError`(건너뛰어 pass면 red -- 계획 v6.31 (11)(d), 재검증 G-1) (e) (v1.12.9, 계획 v6.32 완료 조건 (11)(e), 사용자 결정 O-96 -- card IT-2e, 4.7-3c '실패 평가의 부분 스냅샷 파생') parent가 있는 평가에서 블록 k(커널 블록(steps·later 구성원) 각각 -- 구성은 IT-2d 병합 head 실측 -- 와 봉인 항목 블록 각각 -- 구성 = `SEAL_ITEM_BLOCKS` 상수를 걷는다; 후보 실패 주입, 주입 자리는 바꾸지 않음)가 실패하면 부분 스냅샷(`EvalResult.partial`)의 `block_versions` 키 = base writer ∪ k 앞 블록, 필드 writer ⊆ base writer ∪ k 앞 블록이고 k와 그 뒤 블록이 없음(parent 값이 남으면 red). **사례 유효 조건 둘**(어기면 그 사례는 무효이고 통과로 세지 않음): (가) 주입한 θ에서 블록 k가 reuse되지도 graft되지도 않고 실제로 실패한다(parent reuse·같은 실행 S3 색인 graft 모두 아님 -- 부분 스냅샷이 없거나 k가 실패 블록이 아니면 그 사례는 무효). **(가)의 관측**(검증 S-4·gap G4): parent 경로 사례에서 블록 k에 들어간 스냅샷으로 잰 `k.input_version(snapshot, *extras)` ≠ parent 스냅샷의 `block_version(k.name)`(reuse 아님), 그 실행 색인의 `donors.find(k.name, "*", 그 입력 버전)`이 None(graft 아님), 그 실행 색인의 `donors.find_failure(k.name, "*", 그 입력 버전)`이 None(재연 아님 -- 계획 '실제로 실패'의 해석, 계획보다 엄격한 쪽이라 원래 취지와 다르지 않음; 재검증 S-R3: 옛 '`replays` 증분 0'은 `__call__`을 감싸는 주입에서 늘 0이라 아무것도 거르지 않아 바꿈) -- part `"*"`는 엔진 비공개 상수 `_PART`(`E/core/compute_block.py:99`)라 test는 리터럴 `"*"`로 쓴다(N-R2) (나) 대조 평가 = **새 `open_run()` 쌍으로 `build_kernel_context`한 별도 커널 컨텍스트에서 `size_and_seal`을 직접 호출**(parent 없이 같은 θ·같은 주입; 재검증 S-R2 -- 한 갈래) -- 계획 (나)('`size_and_seal` 직접 호출 또는 별도 커널 컨텍스트')보다 엄격하다: 평가 키 캐시와 블록 결과 색인(graft·재연)을 모두 parent 경로와 공유하지 않아 대조가 parent 경로에 기대지 않게 하기 위함; 대조 결과가 parent 경로 결과와 같은 캐시 객체가 아님을 확인한다. **재연 경로 선택 사례 1건**(S-R3 -- 4.7-3c '재연 예외도 같은 부착 자리에서 줄여서 붙는다'를 판정): 같은 커널 컨텍스트(같은 실행 쌍)에서 두 평가 모두 `size_and_seal(ctx, θ, parent=…)`을 직접 부른다 -- 먼저 parent 없이 블록 k를 실패시켜 실패를 색인에 기록하고, 이어 parent 경로 평가로 블록 k를 재연(`from_record`)시킨 뒤, 부분 스냅샷 축소(`block_versions` 키 = base writer ∪ k 앞 블록)와 fp가 계산 경로 사례와 같은지 본다(search `evaluate`로 부르지 않는다 -- 평가 키 캐시가 parent를 키에 넣지 않아 둘째 평가가 첫 결과 객체를 받아 사례가 공허하게 통과한다; 재검증 S-Q1). **이 사례의 유효 조건**: 블록 k의 `replays` 증분 = +1(재연임 -- 어기면 그 사례는 무효, N-Q1). 실패 주입 = 블록 인스턴스 `fn` 교체 또는 실제로 실패하는 θ(실패가 색인에 등록돼야 하므로 블록 계산 경로에서 나야 한다 -- `__call__`을 감싸는 주입으로는 재연이 생기지 않는다), 주입 예외는 `InfeasibleSizingError` 하위 클래스(결정적 도메인 실패만 색인에 등록됨 -- `E/core/compute_block.py:160`); 위 (가)의 '재연 아님' 조건은 이 사례에 적용하지 않는다. **판정 = 변성 관계**(기대값은 축소가 no-op인 parent 없는 경로에서 나온다): 부분 스냅샷 fp = 대조 평가의 부분 스냅샷 fp이고 S3 evals 실패 줄 `snapshot_fp`도 그 fp; 봉인 위반 + parent 한 건에서 부분 스냅샷에 `dc_seal_report` 필드가 남고(지우면 red) fp가 같은 조건 (가)(나)의 대조 평가와 같음. `writers_in_scope(None, …)` → `TypeError`(건너뛰어 집합을 내면 red -- gap G2·검증 N-2). **재구현 0(AST 검사, 측정 정의 = 계획 N3.3, 세는 연산 = 4.7-3c 'AST 검사가 세는 것')**: 한 식 트리(합집합·차집합 연산 사슬)의 피연산자에 base writer 집합(출처 = 스냅샷 `block_versions` -- 변수 대입을 거쳐도 추적)과 블록 이름 집합이 함께 나타나는 식(coverage 연쇄 꼴 `(used − base) − called` 포함)의 정의 자리 = `writers_in_scope` 하나, 그 함수를 부르는 자리 = 파생 keep(`run_kernel`)·봉인 4 coverage(`seal_versions`)·실패 부착(`_call_block`·`seal_dc`), 그 밖 0(서로소 단언·parent 일치 검사의 base writer 단독 읽기는 대상 아님); 검사가 실제로 거부함을 보이는 red 변형 둘(넣으면 검사 FAIL -- 계획 N3.3의 (가)(나)): 정의 자리 밖에 연쇄 꼴 `(필드 writer − base writer) − 호출 블록 이름`을 쓴 식, `block_versions`에서 얻은 base writer 집합을 변수에 담았다가 그 변수와 블록 이름 집합을 합집합하는 식. parent 없는 기존 부분 스냅샷 test(`E/tests/search/test_kernel.py` B-T19·B-T20) 불변, reuse·graft·compute 계수 변화 0(G-10). 바뀐 실패 줄 수는 감사가 base↔head 같은 입력 실행의 evals 실패 줄 `snapshot_fp` 차이로 변화표에서 센다; NFR-4 덤프(`tests/integration/nfr4_run_dump.py`가 evals 줄을 걷는다) 기준선을 바꿔야 하면 그 갱신은 작성자가 아닌 주체가 변화표 근거로 한다.
- L12(완료 조건 (12), 사용자 결정 O-61 P3~P6): (a) 커널 되풀이 `k_max` 소진 toy·tol 미정 toy(4.7-3 1 A6 b·c) -- `node.dc_window` 뿌리 `input_status == "unsettled"`이고 W4 y 범위로 그대로 쓰임, 같은 평가 `node.dc_window_cfg` 항목 모두 `input_status == "unsettled"`, 커널 세 metric과 커널 ICMR 선언 제약이 `Undefined(_, "input_window_unsettled", "numeric", …)`(base는 마지막 창 값을 냄 -- red); **같은 미수렴 toy에서 다듬은 창 계산 안 함**(사용자 결정 O-64 (2), 계획 완료 조건 (12)(a)): `node.dc_window_def_refined`에 입력 포트 항목 없음·끝 풀이 호출 0·perf `window_end_solves` 증분 0(계산하면 red -- v1.12.1 설계는 다듬었다), front 세 metric `Undefined(_, "input_window_unsettled", "numeric", …)`; 선언 `icm_margin_v` 제약을 단 같은 toy의 외층 실행에서 그 점이 최종 `front`에 없고 `unmeasured_front` 쪽에 있으며 unmeasured 원인 = `"input_window_unsettled"`(최종 `front`에 남으면 red), 제약 없는 같은 toy에서 그 점의 front 분류는 미수렴 없는 대조 toy와 같은 규칙이고 원인은 `graph.metrics_icm_front.undefined`에만 있음 (b) F 성분 입력 DC 미선언 포트 toy -- 그 포트 `node.dc_window`·`node.dc_window_cfg` `input_status == "f_component_undeclared"`(`lo`·`hi` None), `node.dc_window_def_refined` 항목 없음, 세 metric `Undefined(_, "input_window_f_component_undeclared", "definitional", …)`(그 포트만 자기 x로 훑은 창이 나오면 red) (c) KVL 고정 출력 toy와 단일 입력 '회로 그대로' 구성 toy(사용자 결정 O-63 (4) -- 단일 입력 toy는 L10 (g)와 같은 연결) -- 각 끝이 `node.dc_window_cfg`에만 있고(`IcmConfig`에 `kvl` 칸 없음) `node.dc_window_def_refined`에 입력 포트 항목이 하나도 없으며(묶인 반전 입력 포함 -- M2) front·보고 `icm_margin_v` = `icm_window_metrics`(그 포트의 `node.dc_window_cfg`) 값 (d) `dc_window_refine` 블록 READS에 `("node", "dc_window_cfg")`가 있고 `("node", "dc_window")`가 없음(블록 READS 단언 -- 모든 구성; `as_is_single_input`에서 이 블록은 입력 포트를 쓰지 않는다 -- 4.7-4 1·2 (b), O-63 (4)).
- triode 경계 판정 여유는 계획 N3.8 '소자 조건'(O-58 T-1) 인용, tol_VDsat = `sat_threshold` 값.

**4.7-8 변경 종류·판정 다리**(계획 N6.3 (i)~(iv), O-34 (1)): IT-1·IT-2 모두 **동작 변경**(IT-1 = 입력 DC 미선언 회로의 쓰기 계획·θ y·결과, IT-2 = 입력 DC 선언 회로에 창이 생기고 metric 값의 출처가 바뀜. 무동작 입력 -- IT-1의 선언 2회로 쓰기 계획 -- 은 순수 리팩터링 필드별). 다리 넷: 정의 오라클 toy(4.7-1·4.7-7), 봉인 불변식, SPICE oracle 대조(**보류** -- 채울 card EO-1, 그 뒤 꺼짐 정의 판에 따라 OP-5), 검증자 변화표(9회로, IT-Q3 (가) -- IT-0 기록 대비). 결정성 비트 동일. 두 card는 각자 test·code 커밋을 갖고 **하나의 통합 병합**으로 들어간다(O-19 (2) -- IT-1만 병합된 기간 없음). 바뀌는 metric 동작(변화표 원인 칸에 쓴다): (1) 입력 창 출처가 경로 합 → 노드 풀이 창, margin이 첫 포트 → 포트별 최솟값 (2) 측정 실패·되풀이 미수렴 점의 세 metric이 정의 불능(as-built는 값을 냈다) (3) **입력 포트가 없는 회로의 `swing_out_v`**: as-built `ls_swing`은 `no_input_port`면 세 metric 모두 정의 불능으로 냈다(`ls_swing.py:87-88`) -- 이제 스윙은 출력만 보고 풀리고, 입력 두 metric만 `no_input_port`다. **기준선 둘**(v1.12.3 N-2): 검증자 변화표의 원인 칸은 as-built(IT-0 기록) 대비로 적는다. 아래 (4)~(7)은 as-built 대비 원인과, design 판 사이 차이(v1.12.1 design 대비 -- 구현 전이라 변화표가 아니라 design 기록)를 함께 적는다. (4) **단일 입력 '회로 그대로' 구성 포트의 front·보고 값 출처** = `node.dc_window_cfg`('추정' 선형 감도 끝 -- 사용자 결정 O-63 (4), 계획 완료 조건 (6)) -- as-built: `ls_swing` 경로 합 창; v1.12.1: 다듬은 창(멈춤) (5) **출발 창 미수렴 점**: front 값 정의 불능, 선언 제약이 걸리면 최종 front에서 빠짐(O-64 (2) -- 4.7-5 '미수렴 front 처리') -- as-built: 마지막 창 값; v1.12.1: 다듬은 창을 계산 (6) **출력 구조 분류로 고르는 측정 구성 창 갈래**(O-64 (1), 4.7-1a) -- as-built: 분류 없음(ICMR = 경로 합); v1.12.1 대비: 단단한 경로 위 W3 출력(MOS 경로)이 목표값 follower → KVL 고정 연립, 옛 D3 문언('출력 노드에 DC writer가 있으면 KVL 고정')을 출력 자신의 writer로 읽은 것 대비 분류가 바뀌는 출력 전부(v1.12.4 I-4 -- 계획 v6.24는 옛 D3를 writer 사슬 뿌리 기준으로 읽으면 규칙 하나와 같다고 정정했다, O-66 (2) 사실 정정·동작 변경 아님)(W4 성분 안 writer 있는 출력 등) -- 발동 회로·출력은 card 0 '출력 구조 분류 발동'(4.7-8a) (7) **멈춤 S-OS1·S-OS2 갈래**: 세 metric 정의 불능·선언 제약 front 제외(fail-closed -- as-built는 값을 냈다; v1.12.1은 갈래 미기술). 순서: 선행 XRUN-F1 card B, 뒤에 headroom-chain HC-S(`sat_threshold`가 `saturation_rows`를 고친다 -- **IT-1·IT-2 → HC-S**, headroom-chain v0.7.6), card DE-1, card ME-1(metric 코드를 바꾸는 card라 ME-1 모델 오차 측정은 IT-2 뒤, 계획 N6.19 선행). **card IT-2e 변경 종류**(v1.12.9, 계획 v6.32 완료 조건 (11)(e), O-34): 지문(evals 실패 줄 `snapshot_fp` -- parent가 있는 커널 블록·봉인 항목 블록 단계 실패 줄) = 동작 변경, 지문 밖 결과 = 순수 리팩터링(필드별, NFR-4), 결정성 비트 동일; 동작 변경 칸의 SPICE 다리는 계획 N6.3 '대상 없음' (ii) -- 부분 스냅샷을 판정·재사용 입력으로 읽는 엔진 소비자 0의 `git grep` 증거를 판정 기록에 남긴다; 다리 = L11 (e) 변성 관계 test, 봉인 불변식(봉인 4 coverage가 같은 집합 함수), 검증자 변화표(바뀐 실패 줄 수).

**4.7-8a card 0 IT-0 결과 칸**(검증자가 채운다 -- 이 design 판에서는 '미측정'. 판정 기록 `.ai/verification/<IT-0 id>/`):

| 칸 | 내용 | 값 |
|---|---|---|
| M-I4 IT-Q2 판정 | 포트 쌍마다 \|V_p − V_q\| ≤ max(노드 tol_V) 여부 → (나)/(다) -- 계산 경로는 판정과 무관하게 하나(X-IT8) | 미측정 |
| s_p 부호 | 회로·뿌리 아닌 포트마다 dV_p/dx 부호(음수면 O-49 P2 [min, max] 규칙 발동) | 미측정 |
| 커널 창 상태 발동 수 | 회로마다 평가 중 `input_status` = `unmeasured`·`unsettled` 비율 | 미측정 |
| 다중 입력 뿌리·고립 입력 포트·F 성분 미선언 포트 | 4.7-1 4·5, 4.7-3 3 (나) 발동 회로 | 미측정 |
| front가 빈 회로 수 | 미수렴 제외로 최종 `front` 점이 0이 되는 회로(사용자 결정 O-64 (2), 계획 완료 조건 (6) -- 4.7-5 '미수렴 front 처리' (가)) | 미측정 |
| 출력 구조 분류 발동 | library 9회로 + heldout 4회로(v1.12.3 N-3 -- 측정만, card 0 기록 칸 추가): 회로·출력마다 `node.dc_output_structure` 값, W3 출력 여부, 단단한 경로 위 W3 출력 수를 MOS 경로(OS (e) 꼴 -- `kvl_fixed`)와 저항만 경로(`dc_resistor_cycle` 정지 -- 분류 없음)로 나눠 셈(MF-1), 멈춤 S-OS1(출력 아닌 W3가 사슬 뿌리인 `high_impedance` 출력)·S-OS2(되먹임 선언 차동 출력) 발동 수 | 미측정 |

**4.7-9 범위 밖(card DE-1·FX-1 몫, 이 판에서 고치지 않음)과 보고 항목**:
- DE-1: 정의 창 `node.dc_window_def`(tol 없음·전도 끝 = 봉인 9 식, 훑기 점 I_off·ε)와 그 블록, 선언 제약 행의 다른 이름, ICMR 정의 O-25(출력은 회로대로 따름)·일반형 O-33 (7)(전달 뷰 여기 방향 훑기), 다듬은 창의 끝 풀이 기준 전환(+tol → 정의), 선형 감도 연립 특이의 fail-closed(커널 쪽 -- 이 판은 4.7-3 4로 metric 정의 불능까지만), 출력 스윙(고임피던스·KVL 고정 출력, 출력 창 별도 필드), 계통 offset ΔV_out = −G⁻¹·ΔI, 슬루 방향 최대 전류, `ls_swing` 자체 제약계·`ls_fields` β/σ/κ 삭제, 40 §3.8-3·§3.8-8 `swing_out_v`·`offset_sys_mv` 정의. **DE-1 인계(v1.12.1, v1.12.2 갱신)**: (1) 출력 스윙(DE-1 (b))의 고임피던스/KVL 고정 구분은 S0 필드 `node.dc_output_structure`(writer `dc_writer_plan` 하나, θ 무관 -- 4.7-1a, 사용자 결정 O-64 (1))를 READS로 읽는다(다시 분류 금지 -- 둘째 생산자); 13회로 출력 표(W3 여부·핀 뺀 성분의 F·D3 분류·O-23 분류, netlist 연결만)의 사용자 승인은 IT-1·IT-2 통합 병합 조건으로 앞당겨졌고 충족됐다(사용자 결정 O-66 (1)(3), 계획 v6.24 N6.6 순서 -- 그 표가 IT-2와 DE-1 (b)의 분류 기준선) (2) DE-1 뒤 cfg 포트(KVL 고정 등)의 front 값 출처 `node.dc_window_def`의 기준 표기는 `IcmWindow.sources` 참조로 그 필드 정의('정의 기준')에서 읽는다(gap I-1 -- 옛 `criterion` None 표기의 모호함은 사본 칸 삭제로 없어짐) (3) 선언 제약 판정 = `node.dc_window_cfg`(4.7-2 'DE-1 전 한정', gap G2) (4) **미수렴 상태의 이어짐**(사용자 결정 O-64 (2)): DE-1이 다듬은 창 출발 창을 정의 창 `node.dc_window_def`로 바꿀 때 그 칸도 커널 미수렴 상태를 이어받고, 4.7-4 2 (d)(출발 창 미수렴 포트 = 다듬지 않음)·4.7-5 '미수렴 front 처리'가 그대로 적용된다 (5) **선형 감도 끝만 정의되는 구성**(KVL 고정·`as_is_single_input`, O-63 (4))의 DE-1 뒤 정의 기준 값 = `icm_config`가 쓰는 `node.dc_window_def` 한 칸(계획 N3.8 -- 재계산 0) (6) **O-63 (1)**(DEC-23 'A_dc 정의 불능 갈래'가 'ΔW = 0 → 0'보다 먼저): IT-2는 A_dc·σ·V_id*를 계산하지 않는다(4.7-3b (1)의 T_p는 반전 입력 식별용 DC 전달이고 그것으로 나누는 양이 없다) -- 계통 offset(DE-1 (c))의 갈래 순서·판정 자리는 DE-1 design 몫이고 이 판은 설계하지 않는다 (7) 멈춤 S-OS1·S-OS2(4.7-1a)가 card 0에서 발동하면 출력 스윙의 같은 갈래도 계획 개정을 따른다(S-OS2 일반형은 계획 v6.24 N3.8 '차동 출력 회로의 측정 구성' -- 후속 card) (8) **판정 분해능 정의 함수의 이동**(v1.12.4): DE-1 (c)가 DEC-23 'A_dc 정의 불능 갈래'(O-63 (1) -- 갈래 먼저)에서 같은 정의를 쓸 때, `icm_config.py`의 비공개 `_transfer_resolution`을 `E/metrics/_helpers_nodal.py`의 공개 함수로 옮기고 두 자리(T_p 판정·A_dc 판정)가 import한다(정의 하나 -- 둘째 정의 금지; 구조 규칙 A 보충 (3)이 그때 충족). A_dc 생산자 둘(`offset_analysis.py:74`·`offset_systematic.py:50` -- O-71 백로그)의 정본 하나 정리도 DE-1 몫이다. 슬루 `.tran` 시작 동작점(N3.8 577, O-69 (1))·DEC-74 front 판정 기록(O-68 (3))은 IT-2 범위 밖이다.
- FX-1: §0 '단계 A는 봉인된 값을 읽지 않는다'의 출발 고정점 예외(X-FX1).
- **옛 결정 대기 D1~D6 = 사용자 결정 O-49 P1~P6으로 결정됨**(계획 v6.20 N6.6 소비자 표 '4.7-9 항목 D1~D6이 O-49 P1~P6과 같은 항목'): P1 → 4.7-4 6, P2 → 4.7-3 2, P3 → 4.7-3 3(X-IT11), P4 → 4.7-4 5 '층 0 front 후보 점'(card LA-1 범위 12), P5 → 4.7-2 표·값 형식 `criterion`(X-IT12), P6 → 4.7-4 2 '(ii) 끝의 포화 확인'.
- **옛 멈춘 항목 S-1~S-4·T-1**: 사용자 결정 O-58·O-59 (1)(2)와 계획 v6.21(사용자 O-60 승인)로 이 판에 설계됨 -- 4.7-3b(S-1~S-3)·4.7-3a 2(S-4 두 갈래)·4.7-3a 1 (나)·3(T-1)·4.7-3c(스냅샷 파생 규칙). **IT-2 착수 실측 멈춤 조건**(멈추고 보고): **IT-2c 착수 실측**(계획 v6.24 N6.6 순서, 사용자 결정 O-71 미확인 항목 -- 기록 뒤 착수, 결과가 계획 N3.8 정의와 어긋나면 멈추고 보고): (a) `current_reuse_telescopic_ota` 봉인점의 T_p와 δA_num 값 (b) 진짜 A = 0인 대칭 사례 하나(갈래 발동 확인) (c) 오라클이 선언한 실제 vntol·reltol(oracle N0 29행 입력). **잴 수 없는 착수 실측의 처리**(v1.12.4 검증 nice-fix -- **design 선택, 사용자 확인 대상**): (a)는 지금 `current_reuse_telescopic_ota`에 층 0 출발점이 없어(`layer0_start` 출발점 없음 -- `_drafts/evidence/2026-10-21/dvout_feasibility.md` 5행) 잴 수 없다. 착수 실측을 잴 수 없으면 IT-0/IT-2c 판정 기록에 '미측정 + 사유'로 적고 IT-2c code 착수 전에 사용자에게 보고한다 -- 조용히 진행하지 않고, 다른 회로·다른 점의 대체 측정을 만들어 넣지 않는다; 판정 단위 = card 넷 IT-2a 스냅샷 파생(4.7-3c)·IT-2b 커널 창(4.7-3·4.7-3a)·IT-2c 측정 구성(4.7-1a·4.7-3b)·IT-2d 다듬은 창·front(4.7-4·4.7-5)(사용자 결정 O-69 (2) -- design·완료 조건 불변, 같은 통합 브랜치, master 병합은 IT-1과 함께 한 번) + **card IT-2e 실패 평가의 부분 스냅샷 파생**(4.7-3c '실패 평가의 부분 스냅샷 파생'·L11 (e), v1.12.9 -- 계획 v6.32 N6.6 범위 5·순서, 사용자 결정 O-96: IT-2d 뒤, IT-1 + IT-2 master 병합 전에 같은 통합 브랜치에서 test·code 커밋; 착수 조건 = 계획 v6.32 승인 → design 40 §2.4.7·이 4.7-3c 개정 → design↔계획 gap → IT-2d 병합 head에서 착수 사실 재측정); 루프 절단 적용(4.7-3b S-3), 구동 쌍 넷 ⊄ ac 접지 ∪ 입력 넷, 커널 컨텍스트에 되먹임 선언 자리 없음(옛 '`require_immutable` 거부'는 L10 (f) test 단언으로, 옛 '`block_model`·`ff_gm_ratio` 인자'는 사실 확정으로 뺐다 -- W4·I2).
- **card EO-1 범위**(사용자 결정 O-55 U2·O-56 -- 이 design은 소비만 한다): 공용 전도 판정 함수 하나(봉인 7·9가 바로 부름), `search_domain`이 상자를 드는 kind 목록의 `off` 제외(`intended_region` 위 술어 하나), headroom-chain `device.dc_sat_v`의 `off` 갈래(HC-S·EO-1 중 늦게 병합되는 쪽). `off` 소자를 사이징·역산 경로에서 빼는 것(O-55 V5)도 EO-1 범위 4 (b)다. IT-2는 4.7-3a 2에서 그 함수를 부르기만 한다.
- **card DE-1 몫(O-50·O-54 관련)**: 정의 창의 tol 없는 경계(포화·triode·전도 끝), 훑기 점 I_off·ε, 기준 칸을 `"definition"`으로 바꾸기(O-49 P5), 출력 창 필드.
- **다른 계획·문서의 후속 정정**(각 문서가 자기 개정에서 고친다, 이 design은 목록만): helper 이동(4.7-4)으로 경로가 바뀐다 -- headroom-chain HC-S가 고칠 `block_columns.saturation_rows`(→ `_helpers_dc_solve.Circuit.saturation_rows`), gain-budget 계획 N6.8 DE-1 F-DE5의 `E/sizing/block_columns.py:246-257`(`input_windows` → `Circuit.input_windows`)·`:663-694`(`_refine_ends` → 삭제, 끝 풀이는 `window_refine.py` 비공개 함수), N6.6 F-I2-1·F-I2-4와 소비자 표의 `block_columns.py` 줄 번호(IT-2 착수 때 재측정). design 42 D-J5·D-ICM 행. gain-budget 계획 DE-1 (c)(N6.8)의 '`offset_systematic.py:46` 같은 factor 재사용' 인용 → IT-2 뒤 `graph.ss_nodal` READS(gap I-3). **계획 문언 알림(v1.12.1)의 처리**: ㉠ 범위 1 끝·완료 조건 (2)의 '`_refine_ends`' → '끝 풀이 함수 하나(이름은 design, as-built `_refine_ends`)' -- 계획 v6.23에서 반영됨 ㉡ N3.8 O-43 D3 문언 -- 계획 v6.23 '출력 구조 분류 -- 규칙 하나'(사용자 결정 O-64 (1))로 대체됨(4.7-1a가 그 규칙을 설계).

**상태**: 4.1은 PART(분류는 있고 매핑이 없다). 4.2~4.6은 MISS. 4.7은 MISS(J-E 창은 as-built `input_window`·`_solve_input_window`가 PART -- A1~A10).

---

## 5. FR-4 -- 층 0 gain 예산 조합 front와 `gain_budget_db` (MOD6)

> **v1.6 계획 복귀 개정 (사용자 결정 2026-10-12 A1~A6, "L1~L13 모두 권고대로 해" 반영, 재검증 반영). L-14는 결정됐다(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지").** 사용자 결정 "A1~A6은 계획대로 되돌려"에 따라 v1.5의 이탈(§5.3 축 표의 'LUT gm/ID 격자점'·'LUT L 점' 후보 축, 'gain bin은 출력이다(N6)', (b) bin 안 L 다듬기, §5.10 as-built 1·2·11)을 폐기하고 계획 v6.3대로 다시 쓴다. 조항 대응은 §5.11, 계획이 정하지 않았거나 서로 어긋나는 점은 §5.12다. 범위 밖(A7 혼합 회로 버퍼 rout 국소 제약, A8 차동쌍 완화, A9 9회로 축소 격자 대조, A10, 결정 9의 §6 KVL 고리 개정)은 접점만 적는다(§5.10-3).

정본은 DEC-71 (1)~(8), DEC-73, DEC-77, DEC-03, DEC-92 (2), LR3·LR5·DEC-16·DEC-19다.

**파일**(`E/search/`): `layer0_budget.py`, `gain_bins.py`, `local_candidates.py`, `local_front.py`, `combo_dp.py`, `assembly.py`, `budget_override.py`, `eval_budget.py`, 신규 `layer0_inverse.py`(§5.3.3~5.3.6), 신규 `l_targets.py`(§5.3.7).

### 5.1 활성 조건

**활성**: 다음 셋이 모두 맞을 때 층 0 gain 예산을 돌린다.
- gain 제약 `gain_ss_db >= G`가 있다.
- 그 전달 뷰에 이득 블록이 하나 이상 있다.
- `review_needed`가 없다.

**예산 대상**: 주경로 블록만이다(§1.12.2-4, J-A). feedforward 묶음은 bin·조합 DP·`gain_budget_db`에 항목이 없다. 조립점에서 FF 묶음 소자는 출발 구간(§6.5, r_ff = 1 관계)의 값을 쓰고, 그 기여는 §2 경로 기여로 계산해 조합 순서의 잔차에 넣는다.

**버퍼 블록의 국소 AC 제약**(DEC-71 (3) "그런 블록에는 선언된 출력 저항 상한(`rout_ss_ohm`)을 블록 국소 모델의 테브난 출력 저항에 건 것을 국소 AC 제약으로 대신 쓴다", 사용자 결정 2026-10-12 "P-1~P-15까지 권고대로 고쳐" P-15 "이득 블록과 섞인 회로의 버퍼 블록에도 rout 국소 제약"):
- 이득 블록이 없는 회로(버퍼만): 층 0을 rout 모드로 돌린다(as-built와 같다).
- 이득 블록과 섞인 회로: gain 모드 층 0 안에서 버퍼 블록도 국소 문제를 푼다. 국소 AC 제약은 국소 Z_out ≤ `rout_ss_ohm`이다. 버퍼 블록은 gain 예산을 받지 않으므로 gain bin이 없고 면적 bin만으로 front를 만든다(DEC-71 (6) '이득 블록이 없어 gain bin이 정의되지 않는 블록'). DP 단계로 들어가는 방식은 §5.6이다.
- `rout_ss_ohm` 선언이 없는 버퍼 블록: DEC-71 (3) "그 선언도 없으면 그 블록은 '층 0 무동작'으로 보고"대로 그 블록만 무동작으로 보고하고, 그 블록 소자는 §6 출발값에 둔다. 섞인 회로에서는 그 블록만 무동작으로 보고하고 나머지 층 0은 돈다(PQ3 결정, 사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지").
- 실측 대상: sf_pushpull_output_opamp(vout 버퍼), two_stage_ota_sf(vout 버퍼). 둘 다 `rout_ss_ohm <= 1000` 선언이 있다.

**gain 제약도 rout 제약도 없는 경우**(H2):
- 문제: 국소 문제에 AC 제약이 없어 해가 최소 크기로 자명해진다.
- **처리**(사용자 결정 2026-10-08 Q5b. DEC-71 (3)의 '사이징 대상에서 뺀다' 대신 적용):
  - 층 0을 끄고 '층 0 무동작'으로 보고한다.
  - 시작점은 출발 구간(§6)에서 만든다.
  - 탐색 결과는 **'성능 판정 보류'**로 표시해 보고한다. 회로를 사이징에서 빼지 않는다.
  - 현재 해당 회로: common_gate_amplifier, folded_cascode(40 §9 Q5 표). 잡음 가드 `noise_excess_th` 행만 있는 경우도 gain 예산은 동작하지 않는다.

### 5.2 bin

- **gain bin 폭**: w_g = max(b_gain, `model_error_gain_ss_db`)이다.
  - b_gain은 `MetricResult.resolution`이다. 단계 B의 첫 봉인 평가에서 잰다. 잴 수 없으면 기준점 행에서 블록 국소 모델의 격자 분해능(§4.2 b와 같은 정의) 최댓값을 쓰고 출처를 `bins.b_gain_source`에 적는다.
  - 모델 오차가 미측정이면 b_gain만 쓰고 결과를 '추정'으로 표시한다(§0, DEC-72).
- **면적 bin 폭**: DEC-80 (ii)를 따른다.
- **bin은 목표다**(P DEC-71 (3) "블록 이득은 등이득 contour에 해당하는 **gain bin으로 고정**해 bin마다 따로 푼다"):
  - bin b = [b·w_g, (b+1)·w_g)이고 그 목표 T_b = b·w_g(아래 끝)다.
  - 국소 AC 제약은 P DEC-71 (3) "블록 국소 소신호 모델(N3.8) 이득 ≥ 그 블록 예산"이다. 그래서 점 p는 국소 gain(p) ≥ T_b이면 bin b를 **충족**한다. 한 점이 아래 bin 여럿을 함께 충족한다(§5.4).
  - 폐기: v1.5 'bin 번호는 floor(gain / w_g)로 평가된 후보에서 정한다(gain bin은 출력이다, N6)'.

### 5.3 블록 국소 문제와 역산 우선 후보 (DEC-71 (3)(4), LR3·LR5)

#### 5.3.1 국소 문제 (DEC-71 (3))

| 항목 | 내용 | 계획 인용 |
|---|---|---|
| 범위 | 블록 소자를 덮는 기둥 집합. 바이어스 기둥도 같은 절차(gain 제약 없음, 면적 bin만) | "범위 = 그 블록의 소자를 덮는 **기둥 집합**이다" / (2) 바이어스 기둥 |
| 입력 | 블록 예산(§5.3.2), 기둥별 레일 전압차, 블록 전류(KCL·선언·슬루 하한), 소자 간 등식(매칭·공유 VGS·diode), 고정 입력(§5.3.10) | "입력 = 그 블록의 gain 예산(첫 회차는 블록 gain 상한(GB4)에 비례해 총 gain 제약을 나눈 시작 배분이고, 이후는 조립이 고른 조합의 값이다 -- 배분의 정본은 조립 단계다, DEC-73), 기둥별 레일 전압차, 블록 전류(KCL·선언·슬루 하한), 소자 간 등식" |
| 결정 | 소자별 gm/ID(θ 좌표는 ln IDu, DEC-88), L 동치류 L(bin 선택 + bin 안 연속, LR3), 기둥 내부 W4 자유 노드전압(VDS 배분) | "결정 = 소자별 gm_id·L·기둥 내부 노드전압(VDS 배분)" |
| DC 제약 | 국소 봉인(§5.3.9)이 검사 | "덮는 기둥마다 KVL ..., 분기 노드 KCL, 포화 여유, diode VGS = VDS, 벌크 역바이어스" |
| AC 제약 | 국소 gain ≥ T_b. 출력 임피던스도 기록 | "이득 ≥ 그 블록 예산(출력 임피던스도 함께 기록)" |
| 목적 | (전력, 면적) 2목적, gain bin마다 따로 | "목적 = (전력, 면적) 2목적 ... gain bin으로 고정해 bin마다 따로 푼다" |

#### 5.3.2 블록 예산과 목표 bin 집합

- **첫 회차 예산**(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-2): g_i^(1) = G · found_db_i / Σ_j found_db_j (dB). found_db = 축소 전 GB4의 격자 일부 좌표 상승 최댓값(§4.2, 하한 추정). found_db가 없는 블록은 층 0 기준점의 블록 분해 gain을 found_db 자리에 쓴다. 결과는 '추정'이다(DEC-67). 첫 목표 bin = g_i^(1)를 담는 bin. A_i,max·A^L0 비례는 쓰지 않는다.
- **bin마다 푼다**: 블록 i가 푸는 bin 범위는 GB4 표와 역산 결과에서 정한다(새 상수 없음).
  - 위 끝 = max(A^L0 bin, 역산 실패 bin). A^L0 bin은 A_i,max^L0(§4.2, '추정')가 인증일 때 A_i,max^L0 + b_GB4,i를 담는 bin이고, 미상이면 없다. 역산 실패 bin은 (b) L 역산(§5.3.5)이 역산 대상 동치류 전부·모든 L bin에서 근을 못 찾는 첫 bin이다(그 bin과 그 위는 같은 고정값에서 도달 불가). 둘 중 큰 쪽까지 푼다. A^L0가 실제 상계가 아니므로 역산이 더 위에서도 근을 찾으면 그 bin을 버리지 않는다.
  - 아래 끝: 다른 블록의 축소 전 A_j,max(§4.2, exit 3과 같은 상계)가 모두 인증이면 G − b_gain − Σ_{j≠i}(A_j,max + b_GB4,j)를 담는 bin부터다(그 아래 bin을 쓰는 조합은 G에 닿지 않는다). '추정'인 A^L0로는 아래 끝을 자르지 않는다. 미상이 있으면 역산이 모든 대상에서 L 창 하한(§5.3.7)으로 눌려 직전 bin과 같은 후보만 낼 때 멈춘다.
  - 순서: 첫 목표 bin → 위로 → 아래로. 예산이 끊겨도 시작 배분 근방이 먼저 덮인다.
- **이후 회차**(사용자 결정 2026-10-12 L-3 "2회차 이후 = 고른 조합의 미해결 (bin, 고정 입력 지문)만 재풀이, 조합 front 불변이면 정지, 상한 K_max(DEC-70 반복 자리 추가 포함)"):
  - 회차 r ≥ 2의 입력: 예산 = 회차 r−1에서 조립이 고른 조합들의 `allocated`(§5.5·§5.6), 고정 입력 = 그 조립점 값(§5.3.10).
  - 다시 푸는 것: 고른 조합에 든 블록마다 (목표 bin, 고정 입력 지문) 쌍 중 `solved(블록 키, bin, 고정 입력 지문)`(40 §2.4.5)이 거짓인 것만 푼다. 참인 쌍은 다시 풀지 않는다.
  - 그 뒤 국소 front(§5.4) → 조합 DP(§5.6) → 조립(§5.5)을 다시 돈다.
  - 멈춤: 조합 front(조합 집합과 조합마다 (전력, 면적) 칸·`allocated`)가 직전 회차와 같으면 멈춘다.
  - 상한: N3.6 K_max 규칙이다. 변화량은 §5.3.6과 같은 지표를 고정 입력 소자에 적용한 것(VGS 변화, |Δln ID|/(gm/ID), |∂VGS/∂L|·|ΔL|)이고, 구간폭도 §5.3.6과 같다. q 규칙으로 도달 불가가 확정되거나 K_max에 닿으면 마지막 회차의 조합 front를 쓰고 `layer0_rounds_nonconvergent`를 기록한다(정지 아님).
  - **반복 자리**: 이 회차 반복은 DEC-70이 세는 반복 자리의 **넷째**다(사용자 승인 2026-10-12 L-3). 셋째(층 0 국소 고정점, §5.3.6)와 별개다. 계획 문언 정정은 §5.12.3 D3이다.
  - 회차 기록(회차 번호, 다시 푼 쌍, 조합 front 지문, 변화량)은 층 0 단계 필드다(40 §2.4.8 회차 기록 행).
- **L-2를 쓰는 이유**(실측, §5.12.4 표): 단계 B를 지나는 6회로의 이득 블록 7개가 축소 전 표에서 모두 미상이고(`grid_product_over_budget`), A^L0(§4.2)도 7개 모두 미상이다. 그래서 GB4 상한 비례 배분은 어느 gain 모드 회로에서도 정의되지 않는다.

#### 5.3.3 (a) gm/ID 역산과 소자 종류 (DEC-71 (4)(a), 사용자 결정 L-11)

P: "(a) 필요 gm에서 `gm_id = gm / ID` 역산". 사용자 결정 2026-10-12 L-11: "ID 미정 소자: 필요 gm 정의된 신호 소자만 gm/ID 자유변수(ID = gm/(gm/ID)), 부하·미러·바이어스는 §6 구간·미러비·KCL 로 정하고 격자 곱에서 제외(reference 방법론 §4.1·§6.4·§6.7)".

**소자 종류**(구조 사실만 쓴다. 이름·상수 없음, IC4):

| 종류 | 구조 정의 | gm/ID | 전류 |
|---|---|---|---|
| 제외 | 쓰기 계획이 종속시킨 소자(`dc_coord.relation` = `cycle_vgs`·`fixed_vgs`, DEC-64 v2 고리 종속 멤버)와 같은 VGS 묶음 비뿌리(`parallel_vgs`) | 고리 등식·묶음 뿌리가 정한다(P DEC-64 "하나의 gm_id가 종속된다"). `kvl_dependent`·`parallel_member`로 기록만 | KCL |
| S: 필요 gm이 정의된 신호 소자 | gain 제약 전달 뷰의 주경로 이득 블록에서 S1v AC 역할이 `input`(시작 CS·CG, `Block.roles`)인 소자. 단 §6.5 매크로가 활성일 때만이다. 활성 조건은 §6.5와 같다: `gbw_target_hz`가 있으면 활성이고, `pm_target_deg`가 없으면 PM 하한 경로(`PM_FLOOR_DEG` = 45°, 기록 `pm_floor_pole_at_ugf`)로 푼다. 이 소자의 필요 gm이 매크로 블록 VCCS gm_i로 정의된다 | ID가 정해졌으면(`kcl`·`ideal_source_ref`) 역산 gm_id = gm_req/ID. ID가 θ 전류면 **자유 변수**(축)이고, 정의역은 §6 구간 [gm/ID_lo, gm/ID_hi] 안 LUT gm/ID 점이다 | 자유 변수면 ID = gm_req/(gm/ID)(방법론 §4.1 흐름 3, §6.4 "(gm/ID1, gm/ID2) 각 단을 제어", §6.7 Phase 1). 슬루 하한이 있으면 ID ≥ I_slew인 점만 남긴다 |
| B: 부하·미러·바이어스, FF | S도 F도 아닌 소자: AC 역할 `load`·`mirror`·`diode_load`·`tail_source`, 어느 블록에도 들지 않는 소자(바이어스 기둥, DEC-71 (2)), 그리고 FF 묶음 셀(§1.12.2, 주경로 예산 밖, §5.1) | **축이 아니다.** §6 출발값(헤드룸 하한 §6.2·matching §6.4-2a·속도 상한 §6.3이 정한 구간의 선택점, FF 셀은 §6.5 G_ff = r_ff·gm_in 출발값)을 쓰고, 외층 SLSQP가 다듬는다 | 미러 비·KCL로 전파한다(placer, §5.10-3) |
| F: 그 밖 신호 소자 | 필요 gm이 정의되지 않은 신호 셀: AC 역할 `cascode`·`pass`·`follower`, 그리고 매크로가 비활성인 회로의 `input`. **버퍼 블록(rout 제약, §5.1)의 출력 follower**는 예외다: 그 블록 출력노드에 source가 닿는 follower 셀은 필요 gm이 rout 제약으로 정의되므로 S로 본다(§5.12.5 E10) | DEC-71 (4) 격자 폴백(`no_gm_requirement`). 정의역은 §6 구간 안 LUT gm/ID 점이다. rout S follower: 한 출력노드에 그런 follower가 여럿이면 **공통 배율 하나** s로 푼다: 그 follower들의 gm을 현재 값 비율 그대로 s배 한 국소 모델 Z_out(s) = `rout_ss_ohm`의 1-D 근(나머지 값 고정). 정준 순서로 하나씩 풀지 않는다 -- §5.3.6 매크로가 블록 gm을 공동으로 푸는 것과 같은 이유(순차 1-D는 앞 소자에 몫을 몰아 순서에 따라 답이 갈린다)이고, 비율을 유지하므로 이름 순서와 무관하다(결정론). 그 뒤는 S 규칙 | KCL. rout S follower는 ID = gm_req/(gm/ID) |

- S 소자의 역산(ID 기지)이 실패하면 그 소자만 격자 폴백한다. 사유는 `gm_id_out_of_interval`(§6 구간 또는 LUT 범위 밖)과 `lut_hermite_nonmonotone_cell`(§4.1 격자 전용 칸)이다.
- 매크로 결과에 `macro_root_missing`·`macro_nonconvergent`·`macro_inactive`가 있으면 그 블록의 S 소자는 F로 간다(`no_gm_requirement`).
- VGS는 `lut.vgs_for_gm_id`(gm/ID 역산 지표 tol_V (i), N3.6)로 구한다.
- 폴백·자유 축의 열거 규칙은 §5.3.11이다.
- **축 하나로 세기**: matching 그룹(S1 `graph.matching_groups`의 derived `diff_pair`·`branch_symmetric`·`mirror`)이나 자기동형 궤도로 묶인 S·F 소자는 gm/ID 축 하나다(차동쌍 두 반쪽 = 축 하나). 같은 VGS 묶음(`parallel_vgs`)은 원래 한 축이다.
- **실측**(2026-10-12, §5.8 표): 9회로 블록 MOS 102개 중 ID가 KCL·선언으로 정해진 소자는 0개다. 그래서 S 소자는 모두 자유 변수 축이고, ID 기지 역산은 발동하지 않는다.

#### 5.3.4 (c) VDS 배분 (DEC-71 (4)(c))

P: "(c) VDS 배분 = 전 소자를 포화 여유 하한(VDsat, DF-25)으로 채운 뒤 남은 헤드룸을 LUT에서 계산한 `∂(gm/gds)/∂VDS`가 큰 소자부터 배분(역할 라벨·상수 금지, IC4·WP-03)".

- **변수**: 덮는 기둥의 W4 자유 노드전압만이다. W0~W3 writer 노드는 값이 정해져 있고, W1/W2 노드는 재배분하지 않는다(LR7).
- **1단계 채움**: 모든 MOS의 VDS를 하한 VDsat + tol_VDsat(봉인 7, VDsat = LUT `VDSAT` 열, DF-25·DEC-88)로 둔다. diode는 VDS = VGS다. 덮는 기둥의 독립 KVL(DEC-71 (5))마다 남는 헤드룸 H = ΔV_rail − Σ(하한) − Σ(저항 강하)를 계산한다. 어느 기둥이든 H < 0이면 그 후보는 `headroom_floor_unmet{column, H}`로 봉인 없이 버린다.
- **2단계 배분**: 한 걸음 = 그 소자 칸의 LUT VDS 격자 간격(데이터에서 정해지는 크기, 새 상수 아님). 매 걸음에서 `∂(gm/gds)/∂VDS`(그 소자 (gm/ID, L, VDS, VSB)에서 LUT 운영 보간(DEC-87)의 VDS 방향 미분)가 가장 큰 소자에 한 걸음을 준다. 그 소자가 지나는 모든 기둥에 한 걸음 이상의 H가 남아 있고, 움직이는 W4 노드가 창 안에 남을 때만 준다. 주고 나면 그 소자의 미분을 다시 계산한다. 줄 수 있는 소자가 없으면 멈춘다. 한 걸음보다 작은 나머지는, 지나는 모든 기둥에 그 나머지 이상의 H가 남은 소자 중 미분이 가장 큰 소자에 준다. 그런 소자가 없으면 나머지는 배분하지 않고 W4 창 안 여유로 둔다(§5.12.1 E3). 동률은 정준 순서(40 §6)로 가른다.
- **출력**: W4 자유 노드전압 θ 성분. 40 §3.7-5 "W4 초기값: 층 0이 배분한 기둥 VDS"가 이 값이다.
- 폐기: v1.5 as-built 2의 '(c) VDS 배분은 커널 DC 정본(W4 창·쓰기 계획)이 한다'.

#### 5.3.5 (b) L 역산 (DEC-71 (4)(b), LR3)

P: "(b) 목표 이득에서 필요한 gm/gds를 구해 bin마다 LUT 곡선(같은 bin 안 L 점 사이 선형 보간)에서 그 값을 내는 L을 역산하고 bin을 고른다(bin 경계를 넘는 L 보간 없음, LR3)".

- **대상**: 블록 안에서 확정할 수 있는 L 동치류 c(고정 입력 §5.3.10 제외).
- **식**(§5.12.1 E1): 다른 값(다른 동치류 L, gm/ID, VDS)을 현재 바퀴 값으로 두고 블록 국소 모델 gain(L_c) = T_b를 L_c에 대해 푼다. 이것이 '필요 gm/gds → L'의 일반형이다. 단일 소자 단에서는 방법론 §6.7 Phase 2 "Av_total 목표에서 역으로 필요한 VA(따라서 필요한 L)를 역산"과 같다.
- **bin마다**: L_c의 PDK 모델 bin(LR3 bin 지도) 중 feasible_L_window(§5.3.7) 안의 bin마다 따로 푼다. bin 안에서는 이웃 LUT L 점 사이 구간마다 끝값의 gain을 보고, T_b를 넘는 첫 구간을 bisection한다. 반복 상한은 N3.6 K_max이고 L 쪽 멈춤 폭은 PDK 제조 격자(DEC-80 (i)과 같은 선언)다. 결과는 gain ≥ T_b인 쪽 끝 L이다. bin 경계를 넘지 않고 LUT L 범위 밖으로 외삽하지 않는다.
- **bin 고르기**: 근이 있는 L bin마다 후보 하나씩을 낸다. 고르는 것은 국소 front(§5.4, (전력, 면적) 비지배)다(L-6).
- **실패 → 그 동치류만 격자 폴백**: `l_inverse_no_bracket`(창 안 어느 bin에서도 끝값이 T_b를 가르지 않음), `lut_axis_out_of_range`(DF-27). 폴백 격자는 그 동치류의 LR5 격자(§5.3.7)다.
- **국소 모델 평가**: L·VGS·VDS·VS는 격자 마디로 맞추지 않고 LUT 운영 보간(DEC-87, L은 bin 안 선형 LR3)으로 평가한다. 폐기: v1.5 as-built 1 '가장 가까운 LUT 격자 마디로 맞추고'.
- 폐기: v1.5 '(b) bin 안 L 다듬기'. 역산이 T_b를 맞추는 최소 L을 직접 내므로 따로 두지 않는다.

#### 5.3.6 (d) 층 0 국소 고정점과 보상 시작점 (DEC-71 (4)(d), DEC-70 (c), DEC-92 (2))

P DEC-71 (4)(d): "기생 용량 반영은 부하 C를 갱신하며 도는 **층 0 국소 고정점**이다 -- ... 수렴 판정·반복 상한·NONCONVERGENT 판정은 DC 순환 블록(N3.6)과 같은 규칙을 쓰고 새 상수를 두지 않는다." P DEC-92 (2): "극점·영점 근사식은 층 0 시작점 생성기로만 쓰고 근사 대 MNA 차를 `comp_approx_gap`으로 기록한다(판정에 쓰지 않음)."

후보 하나의 **한 바퀴**(LUT 계산과 매크로 풀이만 한다. 커널은 부르지 않는다):
1. 극점 노드 용량 C_n은 국소 조각의 W·L에서 봉인 스냅샷 `ss.node_c_farad`와 같은 정의(같은 함수)로 계산한다. 부하 요소 값과 보상 수동소자 값을 더한다.
   - 이 값은 봉인 전 AC 값이라 **'추정'**이다(P DEC-67 "봉인 전에 내는 AC 값은 '상한' ... 또는 '추정'(시작점)으로 표기").
   - 접합 용량의 확산 기하는 레이아웃 전이므로 LUT 생성 규칙의 확산 기하를 쓴다(P DEC-91 (2) "레이아웃 전 첫 사이징점은 LUT 생성 규칙의 확산 기하를 쓴다").
   - 첫 바퀴는 §6.5 매크로의 노드 용량이다.
2. 블록 gm 요구와 보상 시작점은 아래 **층 0 매크로 호출**로 구한다.
3. (a) gm/ID 역산(§5.3.3).
4. (c) VDS 배분(§5.3.4).
5. (b) L 역산(§5.3.5).
6. W = ID · L / IDu(LUT)를 구하고, 이 값으로 다음 바퀴의 C_n을 만든다.

같은 바퀴 안의 LUT 조회(VGS, VDsat, ∂(gm/gds)/∂VDS)는 직전 바퀴 값을 입력으로 쓴다(첫 바퀴는 층 0 기준점 값). (b)와 (c)의 결합도 이 고정점 안에서 풀린다. 새 반복 자리는 만들지 않는다. 이 고정점은 DEC-70 (c)가 정한 세 번째 자리(층 0 국소 고정점) 안에 있다.

**층 0 매크로 호출**(DEC-92 (2), §5.12.1 E2):
- **서명**: as-built `macro_solve(ctx, model, gm_id, lengths, refine=True)`에 키워드 전용 인자 셋을 더한다.

```python
def macro_solve(ctx, model, gm_id, lengths, refine=True, *, node_c=None, gm_bounds=None, gain_targets=None) -> MacroResult
```
  - `node_c`: {극점 노드: C [F]}. 주어진 노드는 소자 기여 용량(전류 비례 cgg + cdd/cgd 항) 대신 이 값을 쓰고, 수동소자는 그대로 더한다.
  - `gm_bounds`: {블록 키: (lo, hi) [S]}. 주어진 블록의 ln gm 변수 상자를 이 범위와 as-built 상자의 교집합으로 좁힌다. 변수에서 빼거나 고정하지 않는다.
  - `gain_targets`: {블록 키: g [dB]}. 주어진 블록의 출력 컨덕턴스를 G_i = gm_i / 10^{g/20}로 둔다(§6.5 망 구성의 g_i 규칙). 주지 않은 블록은 as-built A_intr를 쓴다.
- **풀이**: as-built 그대로다. 공동 SLSQP와 '단마다 그 단을 주극점으로 하는 실행 가능한 출발점' 다중 출발을 쓰고, 목적은 전원 전류 합 최소다(§6.5 as-built).
  - 다른 블록 gm을 고정한 순차 1-D 풀이는 쓰지 않는다. §6.5 as-built 기록 "gm_1 을 고정한 채 gm_k 를 줄이면 이득이 1 아래로 떨어져 (i)이 풀리지 않고, gm_1 을 함께 다시 맞추면 gm_1 상자 상한 모서리로 간다"의 퇴화를 피한다.
- **층 0이 넘기는 값**(블록 i, 목표 bin b의 후보 바퀴):
  - `node_c` = 1단계의 C_n.
  - `gain_targets` = {i: T_b, j ≠ i: 블록 j의 현재 예산(첫 회차 g_j^(1), 이후 조합 `allocated`)}.
  - `gm_bounds` = {j ≠ i: 블록 j의 현재 국소 front 점들이 가진 gm_j의 최솟값~최댓값}. 블록 j를 아직 풀지 않았으면 넣지 않고 as-built 상자를 쓴다.
  - 블록 i의 gm은 as-built 상자 그대로 변수다. engine 보상 커패시터도 as-built처럼 변수다.
  - 결과의 보상 수동소자 값은 층 0 시작점의 보상 수동소자 θ다(DEC-92 (1) "θ 연속 성분(외층 SLSQP 변수)"의 시작값).
- **gm_req,i**: `MacroResult.gm`의 블록 i 값이다. 결과 기록에 `macro_root_missing`·`macro_nonconvergent`·`macro_inactive`가 있으면 블록 i 입력 셀은 (a) 폴백(`no_gm_requirement`)으로 가고, 그 기록을 남긴다.
- **기본 호출 불변**: 세 인자가 모두 None이면 as-built와 비트 동일이어야 한다.
  - 결정 9 초안(u13-kvl-start 7d516cc §6.7-4 B3 "§6.5 매크로 모델(`current_model` + `macro_solve`, 확정 풀이와 같은 설정)")이 기본 호출을 쓴다. 그래서 이 조건이 두 개정의 호환 조건이다.
  - test(`tests/search/test_macro_poles.py`): 이상 VCCS 2·3극점 픽스처와 library 9회로 중 매크로가 활성인 회로에서, 기본 호출 `MacroResult`의 `fp_of`가 as-built bd19cc6에서 잰 기준 지문과 같아야 한다. 기준 지문은 구현 전에 test 작성 주체가 잰다.
- **비용**: 매크로 풀이는 커널을 부르지 않으므로 평가 수에 들지 않는다. 시간은 T_used에 든다(§5.8). 매크로 결과는 그 후보 국소 스냅샷의 층 0 필드다(40 §2.4.8 매크로 결과 행, 입력 버전 = `node_c`, `gm_bounds`, `gain_targets`, gm_id, lengths). 같은 입력 버전이면 계산 블록 규칙(40 §2.4.4 호출 규칙 1·2)대로 재사용하거나 이식한다. graph 밖 memo를 두지 않는다. 매크로가 부르는 LUT 조회(A_intr, cgg·cdd)는 LUT memo다(40 §2.4.6).

**수렴·상한·NONCONVERGENT**(N3.6 그대로, 같은 함수 `sizing.k_max`와 q 판정):
- 변화량 |Δ_k| [V]는 다음 넷 중 최댓값이다.
  - 소자 VGS 변화.
  - W4 노드전압 변화.
  - 소자 |Δln ID|/(gm/ID): ID 환산 지표 (ii)다. N3.6은 순환 블록 수렴에 이 지표를 쓴다.
  - 동치류 |∂VGS/∂L|·|ΔL|: 같은 ln IDu·VDS·VSB에서 L 변화를 VGS로 환산한 값이다(LUT bin 안 선형 보간의 L 방향 기울기, LR3). 이 항이 없으면 L만 움직이고 전압은 같은 바퀴를 수렴으로 잘못 센다(§5.12.1 E6).
- 수렴: |Δ_k| ≤ 그 칸들의 tol_V 최솟값.
- 상한: K_max = ceil(log2(구간폭/tol_V)). 구간폭은 바퀴 변수들의 창 폭 중 최댓값이고, 출처는 as-built 커널 순환 블록과 같다.
  - 노드 변수(W4): 노드 창 폭. `sizing.fixed_point.gauss_seidel`의 `width`이고, 호출부 `E/sizing/block_columns.py`가 `k_max(c.hi − c.lo, ...)`로 쓴다.
  - VGS: 레일 폭. `block_columns.py`의 1변수 노드 규칙 "상한 k_max(레일 폭, tol)"과 같다.
  - L 환산 항: VGS와 같은 창에 든다.
- q 규칙으로 도달 불가가 확정되거나 K_max에 닿으면, 그 후보는 NONCONVERGENT 실패 레코드(N3.14)로 남기고 봉인하지 않는다.

**보상 근사 기록**은 조립점에서 한다(§5.5 `comp_approx_gap`).

#### 5.3.7 L 초기 목표·knee·동치류 격자 (LR5, DEC-16)

P LR5: "초기 L 목표(역할은 라벨이 아니라 S1 유도 사실이다, IC4): 미러(`equal_vgs` 멤버) = kind별 knee(`measure_L_knee`, 동치류 멤버의 탐색 gm_id 가능역으로 한정한 곡선에서 계산 ...), 바이어스 레플리카(J1 교류접지 예외 목록 소자) = `feasible_L_window` 하한, 캐스코드(전류 구동 CG 셀)·그 밖 신호 경로 셀 = knee 목표를 거부하고 theta 탐색이 정한다 ... 모두 `feasible_L_window`로 clamp한다." P DEC-16: "초기 L은 공정 knee에서 시작하고 실현가능 창으로 clamp한다".

**동치류 종류**(S1 사실, 라벨 없음): 동치류의 종류는 L 주인(LR1·DEC-17, §1.12.5)의 종류다.
- 미러: 주인이 `equal_vgs` 멤버이고 신호 셀이 아니다 → 초기 목표 = knee.
- 레플리카: 주인이 J1 술어(§1.2 (4) 바이어스 종속 넷)가 교류접지로 둔 넷을 구동하는 소자다 → 초기 목표 = window 하한.
- 신호: 주인이 신호 셀(CS·CG·CD, 캐스코드 포함)이다 → knee 목표를 거부하고 (b) 역산이 정한다. 첫 바퀴 값은 §6 출발 L이다.
- 그 밖: §6 출발 L(DEC-71 (3) "첫 회차는 ... 출발 구간 값").

**knee(새 엔진 정의)**. 원천은 history v4.49 §7.10 '측정 2'와 레지스트리 `measure_L_knee` "L 격자 전수 스캔으로 한계 Δ(gm/gds)/Δ(W·L) 최대 구간 상단 L"이다. 옛 코드는 참고만 한다.
- 소자 d, 고정 (gm/ID, VDS, VSB)에서 LUT L 점 L_1 < … < L_n(bin 경계 점 포함, LR3)마다 e_j = gm/gds, a_j = L_j²/IDu를 구한다. VGS는 `vgs_for_gm_id`로 구한다. W·L = ID·L²/IDu이므로 ID는 argmax에 영향이 없다.
- 한계효율 η_j = (e_{j+1} − e_j)/(a_{j+1} − a_j). a_{j+1} ≤ a_j인 구간(IDu 비단조, §7.10 반례)과 §4.1 격자 전용 칸은 건너뛰고 `knee_interval_skipped{reason}`로 기록한다.
- knee = η가 가장 큰 구간의 위 끝 L(LUT L 점 = 앵커). 동률은 작은 L이다.
- gm/ID 범위: 동치류 멤버의 §6 출발 구간 [gm/ID_lo, gm/ID_hi] 안의 LUT gm/ID 점(P "탐색 gm_id 가능역으로 한정", I-A15: 격자 전체 중앙값을 쓰지 않는다).
- VDS·VSB: S0 수준 필드 `start.point`의 그 소자 값이다(40 §2.4.8).
- 축약(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-4 "knee 축약 = 합집합 앵커(중복 제거, 늘어난 앵커 수 기록)"): 가능역의 gm/ID 점·멤버마다 잰 knee 앵커의 합집합(중복 제거)을 쓴다. 늘어난 앵커 수를 `knee_anchor_union{class, n_anchors}`로 기록한다.
- knee는 LUT와 숫자 인자(kind, w_key, gm/ID 점, VDS, VSB, LUT L 격자)만의 순수 함수다. 그래서 LUT memo `memo.call(knee_fn, ...)`에 둔다(40 §2.4.6 순수성 규칙).

**feasible_L_window(새 엔진 정의)**. 원천은 history §10.11 "선언된 `W_bounds`와 그 소자의 실제 ID로 그리는 'W 한계 안에 들어오는 L 구간'"이다.
- 소자 d: {L ∈ LUT L 범위 : W(L) = ID_d · L / IDu(gm/ID_d, L, VDS_d, VSB_d) ≥ W_min} ∩ {W(L) ≤ W 상한, 선언이 있을 때}. W_min은 PDK `core` 선언이다. 새 엔진에는 W 상한 선언이 없으므로 면적 예산이 있을 때만 §6.4-5의 W ≤ A_budget/L을 쓴다.
- history §10.11의 선언 `W_bounds`는 옛 spec 필드이고 새 spec에는 없다. 이 정의는 그것을 위 두 경계(PDK W_min, 면적 예산 W 상한)로 **대체**한다(§5.12.1 E5).
- diode 멤버는 VDS = VGS(gm/ID, L)로 계산한다(history §10.11 diode 분기).
- 동치류의 창 = 멤버 창의 교집합이다. ID·gm/ID·VDS는 현재 바퀴 값이다.
- 창이 비면 `l_window_empty`이고, 그 동치류가 든 후보는 국소 실현 불가다(LR5 확장 조건 'W 한계').

**동치류 격자**(P LR5 "동치류마다 초기 격자 = {knee 앵커와 인접 앵커} ∪ {`feasible_L_window` 하한 앵커}"):
- G_c = {knee 앵커, 그 위·아래 이웃 LUT L 점} ∪ {window 하한을 담는 LUT L 점}. window 밖 점은 뺀다.
- 역산 시작 후보: (b) 결과 L_inv를 감싸는 같은 bin의 두 LUT L 점을 G_c에 더한다(P LR5 "층 0의 이득→VA→L 역산 결과 ... 그 L을 감싸는 같은 bin의 LUT L 점을 이 격자의 시작 후보로만 쓰고, 격자를 대체하거나 줄이지 않는다").
- **넓히기**(P LR5 "블록이 실현 불가(W 한계, 블록 gain 상한 < 목표)이거나 한 칸 넓힌 격자에서 두 목적 축에서 비지배로 개선되는 점이 생기고 그 개선이 축마다 max(그 축의 분해능, 모델 오차) 이상이면 그 동치류 격자를 인접 앵커 한 칸씩 넓히고, 개선이 없거나 LR3·LR6 경계에 닿으면 멈춘다"):
  - 시도: G_c 양쪽 이웃 앵커 한 칸을 그 bin 국소 front에서 전력이 가장 작은 점의 나머지 값에 얹어 평가한다.
  - 개선 판정(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-8 "비지배 개선 + 개선된 축마다 개선량 >= max(분해능, 모델 오차), 모델 오차 미측정이면 분해능 + '추정'"): 넓힌 앵커의 점이 그 bin 국소 front에 비지배로 들어가고, 개선된 축마다 개선량이 max(그 축 분해능, 모델 오차) 이상이면 개선이다. 모델 오차가 미측정이면 분해능만 쓰고 '추정'으로 표시한다.
  - 멈춤: 개선 없음, LUT L 범위·bin 지도 끝(LR3), §6.4-4 속도 상한·§6.4-2 matching 하한(LR6의 봉인 전 추정).

#### 5.3.8 후보 집합 (DEC-71 (4) "역산은 후보를 만드는 수단이고 격자를 대체하지 않는다")

P: "LR5 동치류 격자와 내층 DP는 그대로이며 역산 결과는 그 격자의 시작 후보이고, 검증·폴백·미세조정은 격자가 한다."

블록 i, 목표 bin b의 후보:
1. **역산 후보**: 역산 대상 동치류 c마다, 나머지 동치류를 초기 목표(§5.3.7)에 두고 c를 (b) 역산한 점. 근이 있는 L bin마다 하나씩이다(§5.3.5). (a)·(c)·(d)는 §5.3.6 고정점이 함께 푼다.
2. **검증 후보**: 1의 L_inv를 감싸는 두 LUT L 점. 나머지 값은 그 역산 후보와 같다.
3. **자유·폴백 후보**: S 자유 축과 F 폴백 축의 gm/ID 격자(§5.3.3), (b)가 폴백한 동치류의 LR5 격자 G_c. B 소자는 §6 출발값에 둔다. 열거는 §5.3.11이다.
4. **넓히기 후보**: §5.3.7 넓히기.

각 후보는 §5.3.6 고정점을 거친 뒤 국소 봉인 한 번(§5.3.9)으로 판정한다. 폐기: v1.5 §5.3 축 표('소자 그룹별 gm/ID = LUT gm/ID 격자점', 'L 동치류별 L = LUT L 점'을 모든 후보의 축으로 두는 곱).

#### 5.3.9 국소 봉인과 국소 결과 저장 (DEC-71 (5), 40 §2.4.4·§2.4.5·§2.4.8·§2.4.11)

신규 `E/sizing/size_and_seal_local.py`:

```python
def size_and_seal_local(ctx: KernelContext, theta_block: Mapping[str, float],
                        fixed: Mapping[str, float], columns: frozenset[str]) -> GraphSnapshot
```
- 계산 블록 ②~⑤를 `columns`에 속한 소자·노드에만 적용한다. 그 밖의 값은 `fixed`에서 읽는다. 블록은 분할 계산 블록이다(분할 key = 기둥 id 또는 `shared:<기둥>`, 40 §2.4.4).
- 봉인 1·2·6·7과 덮는 기둥의 독립 KVL·KCL만 검사한다.
- tol_I는 그 후보 자기 동작점의 `device.dc_gm` 필드 × tol_V다. 부모 스냅샷에 의존하지 않는다(40 §2.4.11, 사용자 결정 G-3').
- `theta_block`에는 §5.3.6 결과(ln IDu, L 동치류 L, W4 노드전압, θ 전류)가 들어간다.
- **반환값은 층 0 국소 층의 graph 스냅샷이다**(40 §2.4.1 층 0 국소 층).
  - 봉인 통과 여부와 실패 레코드는 그 스냅샷의 봉인 필드다.
  - 국소 전력·면적은 `graph/local: power_w, area_m2`, 국소 gain·rout 모드 Z_out은 국소 gain 필드다(40 §2.4.8 해당 행, writer = 국소 봉인 블록, 키 = 덮는 기둥 집합). 국소 AC는 봉인을 통과한 점에서만 계산한다.
  - graph 밖에 결과 사본(옛 `LocalSeal{gain_db, power_w, area_m2, snapshot_fragment}`)을 두지 않는다.
- **찾기**(40 §2.4.5 S3 메모리 색인):
  - `local(블록 키, 기둥, θ_block 지문, fixed 지문) -> 스냅샷 | None`: 같은 후보의 국소 스냅샷을 찾는다. 실행 안에서는 늘 보존되므로 스냅샷을 준다(40 §2.4.5 v1.11 -- 옛 '놓았으면 요약'은 대상 소멸). 찾으면 다시 봉인하지 않는다.
  - `solved(블록 키, bin, 고정 입력 지문) -> bool`: 그 (bin, 고정 입력 지문)을 이미 풀었는지. 회차 2 이상의 '미해결 쌍'(§5.3.2) 판정이 쓴다.
- **보존**(40 §2.4.5 v1.11 보존 규칙, 사용자 결정 X-2): 실행 수명이다. 국소 front 점의 국소 스냅샷(조립의 이식 원천, 회차 사이 재사용)과 조립점 스냅샷은 실행이 끝날 때까지 남는다. 옛 소유자 '층 0 단계(모든 회차)'·'외층 시작점 대기열'은 폐지(history).
- 폐기: v1.6 초안의 `sctx.local_seal_memo`(상한 있는 graph 밖 memo)와 `LocalSeal` 값 사본.

#### 5.3.10 고정 입력 (K1·K3·K8, 블록을 가로지르는 L 동치류)

P DEC-71 (3): "국소 확정 금지 소자 ... 의 gm_id·L은 국소 단계에서 **고정 입력**으로 쓴다 -- 첫 회차는 스펙에서 유도한 출발 구간 값(design 41 §6)이고 LR5 knee 앵커는 추가 후보로 넣으며(R29 수용, 사용자 2026-10-08), 이후 회차는 직전 조립점 값이며, 국소 AC 이득 계산의 부하 gds가 이 값에서 온다."
- 첫 회차: §6 출발값을 쓴다. **모든 고정 입력 동치류**에 knee 앵커(§5.3.7)와 LR5 종류 앵커(레플리카 종류면 window 하한 앵커)의 합집합을 **추가 후보**로 같은 bin에서 한 번씩 더 평가한다(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-9 "R29 를 좁히지 않음 -- 고정 입력 동치류 전부에 knee + LR5 종류 앵커(레플리카는 window 하한) 합집합"). 폐기: v1.5의 기록 `lr5_knee_anchor_unavailable`.
- 이후 회차: 직전 조립점 값.
- 고정 입력은 (a)·(b)의 역산 대상이 아니다.

#### 5.3.11 후보 열거와 종료

- 순서: 목표 bin 순서(§5.3.2) 안에서 역산 → 검증 → 자유·폴백 → 넓히기 순서다.
- 격자 곱 Π = Π_S(S 자유 축) × Π_F(F 폴백 축) × (L 폴백 동치류의 LR5 격자)를 쓴다. matching 그룹·궤도로 묶인 소자는 축 하나다(§5.3.3). B 소자는 축이 아니다(§5.3.3).
- **정지와 절단의 구분**(**결정**(사용자 결정 2026-10-12 "U-63은 (가)로", U-63), 사용자 결정 2026-10-12 P-1 "DEC-76 경로 열거 상한 초과 = 정지(unsupported_rule_branch), 좌표 훑기 축소 탐색 폐기"의 적용을 좁힌 것):
  - **정지**(`unsupported_rule_branch`, STRUCTURE_UNRESOLVED, 탐색 전)는 둘뿐이다. (a) DEC-71 (3) 경로 열거 수가 DEC-34 예산 상한을 넘을 때(DEC-76 안전망, 가지 단위 축소는 두지 않는다). (b) 후보 격자 곱 Π가 계수 예산 N_S(§0, L-10)를 넘을 때 -- `unsupported_rule_branch{rule: layer0_candidate_grid_over_budget, block, bin, Π, N_S}`. 둘 다 시간과 무관한 결정론 판정이고 단계 A·B 경계에서 한 번 한다.
  - **절단**(정지 아님): N_T,i(§5.8)는 평가 상한일 뿐이다. 후보는 축 index의 반분 단계 순(끝점 → 중점 → …)으로 평가하고, N_T,i나 블록 벽시계에 닿으면 멈춘다. 그때 `layer0_candidates_truncated{block, bin, Π, evaluated}`를 기록하고, 그 블록의 국소 front를 '추정'으로 표시한다(그 뒤 조합 front·`gain_budget_db`도 '추정').
  - 강결합 그룹 좌표 훑기(v1.6 초안)는 폐기한 채로 둔다.
  - 실측(§5.8 표): 후보 격자 곱 최대는 pushpull_follower_buffer vout Π_F = 52,675이고 N_S = 13,829,760보다 작다. 그래서 library 9회로 중 (b) 정지는 0이다. N_T,i에 따라 절단될 수 있는 블록은 pushpull vout 하나다(sf_pushpull vout은 35로 줄었다).
- 같은 θ는 다시 봉인하지 않는다. `local(...)`로 찾은 국소 스냅샷을 재사용한다(§5.3.9). 블록 몫 예산에는 적중도 한 번으로 센다.


### 5.4 블록 국소 front

- 블록마다 `{gain bin → (전력, 면적) 비지배 점}`을 만든다(DEC-71 (6)).
- bin b의 점 = 국소 봉인을 통과하고 국소 gain ≥ T_b인 점 전부다(§5.2). 그래서 높은 bin을 충족하는 점은 그보다 낮은 bin의 front에도 든다.
- **같은 점 접기**(P DEC-71 (6) "두 점의 블록 이득 차가 모델 오차 이하이고 면적 차가 면적 축 bin 폭 이하이며 전력 차가 목적값 분해능 이하이면 같은 점으로 접어 하나만 남긴다"): 칸에 넣기 전에 적용한다. 남기는 점은 칸 규칙과 같다. 모델 오차가 미측정이면 분해능만 쓰고 '추정'으로 표시한다(§0).
- (gain bin, 면적 bin) 칸 하나에는 전력이 가장 작은 점 하나만 남긴다. 전력이 같으면 포화 여유가 큰 점을 남긴다(P DEC-71 (3) "두 축 값이 같은 칸에 든 점끼리만 포화 여유 최솟값이 큰 점을 남긴다").
- 칸 수(gain bin 수 × 면적 bin 수)가 계수 예산 N_S를 넘으면 DEC-80 예산 게이트를 적용한다. bin 폭을 2배로 넓히고 그 배수를 기록한다. 더 넓혀도 칸 배치가 바뀔 수 없으면 멈추고 `resolution_gate_unmet`을 기록한다(as-built 유지).
- 바이어스 기둥(gain bin 없음)은 면적 bin만으로 센다(DEC-71 (6)).
- 목표 bin에 봉인을 통과한 점이 없으면 `local_infeasible{block, bin, reasons}`(N3.14)을 남긴다. 처리는 조립이 다른 조합을 고르는 것이다(DEC-71 (5)).

### 5.5 조립 (M6)

**미지수**: y(K1~K4)와 공유량이다. 공유량은 공유 노드 전압, 블록을 가로지르는 `equal_vgs`의 공통 VGS, 미러 비, `kvl_branch` 종속 gm/ID, 폴딩 노드 전류다.

**풀이**(사용자 결정 2026-10-12 #1, graph core **graft** 연산, 정의는 40 §2.4.4): 조합에 든 블록 국소 스냅샷들에서 입력 버전이 맞는 블록 필드를 조립 스냅샷으로 이식하고, 공유량 필드만 GB7 커널(writer plan 등식)로 다시 계산한 뒤 전역 봉인을 한다. 별도 솔버를 두지 않는다. 이식된 필드는 다시 계산하지 않는다(같은 입력 버전 재계산 0, 결정 (4) G-10).

**공유 VGS 선택**(DEC-10):
- 그룹 g를 공유하는 블록 수를 m_g라 하면, 각 블록의 국소 값 m_g개를 후보로 커널을 m_g번 돌린다.
- 봉인을 통과한 후보 중 전회로 `gain_ss_db`가 가장 큰 것을 고른다. gain 차가 b_gain 이하면 전력이 작은 쪽을 고른다(U-14 기본안). 전회로 `gain_ss_db`를 잴 수 없으면 블록 분해 보고 `full_gain_db`를 쓰고 출처를 기록한다.
- **그룹이 여럿이면**(M6): 정준 순서로 한 그룹씩 고른다(좌표별). 앞 그룹에서 고른 값은 뒤 그룹을 평가할 때 고정한다. 커널 호출 수는 Π m_g가 아니라 Σ m_g다.

**기록**: 국소 값과 전역 값의 차(ΔVGS, Δ노드전압, Δgm_id, Δ블록 gain)를 남긴다.

**`comp_approx_gap`**(DEC-92 (2), §3). 조립에 성공한 점마다 다음을 기록하고 판정에는 쓰지 않는다.
- `approx`: 그 조합의 블록 점들이 쓴 §6.5 매크로 망이다(블록마다 자기 점의 gm_req,i와 자기 출력노드 C_n, 보상 수동소자는 조립된 θ의 값). 여기서 pencil 극점·영점 목록 [Hz], UGF [Hz], PM [deg]을 구한다.
- `mna`: 조립점 봉인 스냅샷에서 구한다. (G, C) 일반화 고유값의 극점·영점 목록 [Hz](DEC-92 (4)), `ugf_ss_hz`, `pm_ss_deg`.
- `gap`: ugf = mna − approx [Hz], pm = mna − approx [deg]. 두 쪽 모두 같은 정의의 스칼라라 짝이 정해진다.
- 극점·영점 목록은 두 쪽을 그대로 싣고, 원소별 차는 기록하지 않는다(L-7).
- 위치: 조립 스냅샷의 `comp_approx_gap` 필드다(40 §2.4.8 해당 행). `Layer0Budget.assemblies[k]`는 그 필드를 읽는 보기다. front 점 기록은 그 필드를 참조한다.
- 극점·영점 목록은 원본을 보존한다(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-7 "comp_approx_gap = UGF·PM 스칼라 차만 기록, 극점 목록 원본 보존").

**시도 상한**: 조립 커널 호출 수는 조합 front 크기와 N_T,0(§5.8)의 남은 몫 중 작은 쪽이다. 조립이 실패하면 다음 조합으로 간다. 성공한 조립점은 모두 외층 시작점으로 넘긴다(as-built 유지).

### 5.6 조합 DP와 front

- **상태**: (블록 k, 누적 gain bin, 누적 면적 bin)이다. 값은 그 상태의 최소 전력 경로다.
- **누적 gain**: 고른 이득 블록 점의 목표 T_b 합(= `allocated`)에 버퍼 블록 몫을 더한 값이다. 섞인 회로(P-15)에서는 버퍼 블록이 면적 bin만 가진 DP 단계이고, 그 몫은 고른 버퍼 점의 실제 국소 gain을 gain bin 아래 끝으로 내린 값(보수)이다. 버퍼 국소 문제가 무동작인 블록(rout 미선언)은 기준점 블록 분해 gain을 상수항으로 쓴다(as-built와 같다). 점의 실제 국소 gain은 T_b 이상이므로 이 합은 보수적이다. 폐기: v1.5 as-built 7 '대표 경로의 정확한 gain 합'.
- **종료**: 누적 gain ≥ G − b_gain이다.
- **r̂의 쓰임**: 측정되어 있으면 '누적 gain + r̂'가 큰 순서로 조립에 넘긴다. 종료 조건에는 넣지 않는다.
- **출력**: 종료 상태 중 (전력, 면적) 비지배인 조합 front와, 조합마다 `gain_budget_db.allocated`를 낸다.
- **동률**(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" D1 "DP 단계 동률 = 최소 포화 여유 비, 조립·봉인 뒤 조합 front 동률 = 계획대로 활성 제약 여유 합"):
  - DP 단계(조립 전): 전력, 블록 MOS 최소 포화 여유 비 (VDS − VDSAT)/VDSAT, 이름 정렬 순. 국소 단계에는 전회로 활성 제약 여유가 없다.
  - 조립·봉인 뒤 조합 front: 전력, 활성 제약 여유 합(DEC-71 (6)), 이름 정렬 순. 여유는 조립 스냅샷의 `graph/metrics: constraint_rows`(40 §2.4.8)에서 읽는다.
- **상태 수 상한**: 계수 예산 N_S(§0)다. DP는 커널을 부르지 않으므로 평가 예산과 섞지 않는다(N4). 넘으면 DEC-80 게이트를 쓴다(면적 폭 먼저, 면적 bin이 하나면 gain 폭). 더 넓힐 축이 없으면 `state_count_over_budget`으로 끝난다(as-built 유지).

### 5.7 출력과 override

**front 점마다 내는 값**: `gain_budget_db.allocated`, `gain_budget_db.realized`(최종 봉인 스냅샷의 블록 gain), 두 값의 차, `gain_residual_db`, `comp_approx_gap`(§5.5).

**`gain_budget_db_override: [{block: [<출력노드 넷 이름>...], value_db, source}]`**(블록 키는 §1.7-3의 정렬 배열):
- 그 블록의 목표 bin을 value_db를 담는 bin 하나로 고정한다. §5.3.2 범위 규칙 대신 이 bin만 푼다.
- 블록 키가 없으면 `SchemaRejectedError(override_block_unknown)`이다.
- A_i,max가 인증되어 있고 value_db > A_i,max + b_GB4,i이면 INFEASIBLE_TARGET이다.
- A_i,max가 미상이면 받아들인다. 그 bin에 봉인을 통과한 후보가 없으면 `local_infeasible`을 보고한다(H3).
- `override_source`를 기록한다.

### 5.8 평가 예산 N_T (DEC-34 식, 단계 B·C 전용, M10·N4)

P DEC-34: "실측 시간으로 계산한다(식: N3.5). 이 식은 **예산 상한 계산 용도**이고".

**정의**: 커널 평가 횟수 예산(상한).

N_T = floor((B − T_used − T_reserve) / t_eval)

| 기호 | 뜻 |
|---|---|
| B | `wall_clock_budget_s` |
| T_used | 지금까지 쓴 시간. §5.3.6 고정점의 LUT 계산 시간도 여기에 든다 |
| t_eval | warm 평가 시간의 중앙값. 첫 평가가 끝나기 전에는 정의되지 않는다. 국소 봉인 시간도 같은 목록에 넣는다 |
| T_reserve | 외층 최소 비용 = 끝점 2개 × (as-built `slsqp_outer` maxiter 식 Σ⌈log2(폭/h)⌉) × t_eval. 선언 E_B가 있으면 N_T = E_B − (커널 + 국소 평가 수) − T_reserve이고, T_reserve는 기준점 FD 스텝으로 센다 |

외층 예약분은 T_reserve로 **한 번만** 뺀다. N_T는 그렇게 뺀 뒤의 층 0 몫이므로, N_T에서 다시 빼지 않는다(N4).

**t_eval 첫 측정**: as-built `layer0_center` 시작점 하나를 먼저 평가해 잰다. 그 뒤로 평가할 때마다 중앙값을 갱신하고 N_T를 다시 계산한다.

**평가 1회**: 국소 봉인 1회 또는 커널 1회다. §5.3.6 고정점 바퀴는 커널을 부르지 않으므로 평가 수에 들지 않는다(시간은 T_used에 든다).

**블록 후보 수(이 개정이 바꾸는 것)**:
- 목표 bin 하나: n_{i,b} = Π_S × Π_F × N_L + 넓히기 후보 수. N_L = Σ_c (n_Lbin,c × 3) + Π_{c ∈ L 폴백} |G_c|(L 격자 쪽 후보).
  - Π_S = S 자유 축 격자 곱, Π_F = F 폴백 축 격자 곱이다(없으면 1). B는 축이 아니다.
  - c = 역산 대상 동치류, n_Lbin,c = 근이 있는 L bin 수, 3 = 역산 1 + 감싸는 LUT L 점 2(§5.3.8)다.
- 블록 전체: n_i = Σ_b n_{i,b}. 실제 평가는 N_T,i가 상한이고, 닿으면 절단·'추정'이다. 정지는 Π > N_S일 때뿐이다(§5.3.11).
- 목표 bin 범위가 미상(§5.3.2)이면 n_i는 평가 전에 알 수 없다. 이때는 n_i 대신 N_T를 쓴다.

**실측**(2026-10-12, as-built bd19cc6 읽기 전용, 스크립트 `wt/_tmp_l0design/measure_l0.py`·`measure_axes.py`, 결과 `results.jsonl`·`axes.jsonl`):
- **ID 출처**: 9회로 블록 MOS 102개 중 ID가 KCL·선언으로 정해진 소자는 0개이고, 블록 밖 MOS 40개 중에서는 2개다. 그래서 (a)의 'ID가 정해진 경우' 역산은 발동하지 않고, S 소자는 자유 변수 축이 된다(§5.3.3).

| 회로 | 블록 MOS | 입력 셀 | ID 고정 / θ 전류 | kvl 종속(`cycle_vgs`) | 블록 밖 MOS(고정 / θ) |
|---|---|---|---|---|---|
| common_gate_amplifier | 2 | 1 | 0 / 2 | 0 | 0 / 1 |
| current_reuse_telescopic_ota(단계 A 정지) | 25 | 8 | 0 / 25 | 6 | 1 / 25 |
| folded_cascode | 11 | 2 | 0 / 11 | 1 | 0 / 2 |
| ngcc_3stage_ff(review_needed) | 11 | 4 | 0 / 11 | 1 | 0 / 5 |
| nmcnr_amplifier(review_needed) | 15 | 4 | 0 / 15 | 1 | 0 / 0 |
| pushpull_follower_buffer | 4 | 0 | 0 / 4 | 1 | 0 / 2 |
| sf_pushpull_output_opamp | 19 | 2 | 0 / 19 | 2 | 1 / 2 |
| two_stage_ota | 7 | 3 | 0 / 7 | 1 | 0 / 0 |
| two_stage_ota_sf | 8 | 3 | 0 / 8 | 1 | 0 / 1 |

- **L-11 적용 뒤 격자 크기**(층 0이 도는 6회로). 실측(2026-10-12, as-built bd19cc6 코드 읽기 전용 + §6.7-1a 쓰기 계획 모사(같은 DC `input_tie` 엣지 제거), 'kvl 종속' 제외, `wt/_tmp_l0design/measure_v4.py`, 결과 `v4.jsonl`). as-built `_jobs` gm/ID 축을 §5.3.3 종류로 나누고, matching 그룹으로 묶인 축은 하나로 셌다. 축 크기 = §6 구간 안 LUT gm/ID 점 수. X = kvl 종속(쓰기 계획 `cycle_vgs`·`fixed_vgs`)이라 축에서 빠진 것. 출력 follower의 E10(S)은 축 수를 바꾸지 않아 F 열에 그대로 둔다.

| 회로(GBW 목표) | 블록(모드) | S 자유 축 → Π_S | F 폴백 축 → Π_F | B 축(제외) | X(kvl 종속) | L 동치류 | as-built Π |
|---|---|---|---|---|---|---|---|
| common_gate_amplifier(없음) | vout(gain) | 없음 → 1 | 35(input, 매크로 비활성) → 35 | 43 | 없음 | 2 | 4.9·10⁵ |
| folded_cascode(없음) | out(gain) | 없음 → 1 | 36(input 쌍), 44(cascode 쌍) → 1,584 | 25, 25 | 없음 | 7 | 2.4·10¹⁹ |
| folded_cascode | bias:6 | 1 | 1 | 35, 34 | 없음 | 0 | 1,190 |
| pushpull_follower_buffer(없음) | vout(rout, 버퍼만) | 1 | 35, 35, 43 → **52,675** | 없음 | 43(M3) | 4 | 2.4·10¹¹ |
| sf_pushpull_output_opamp(60 MHz, PM 하한 경로) | Y(gain) | 16(M1; M2는 kvl 종속) → 16 | 1 | 36, 42, 42, 15 | M2 | 9 | 5.0·10²³ |
| sf_pushpull_output_opamp | vout(버퍼, P-15) / bias:6 | 1 / 1 | 35 → 35 / 1 | 없음 / 13 | 42(M21) / 없음 | 2 / 0 | 4.8·10⁵ / 13 |
| two_stage_ota(7 MHz, PM 목표 없음) | O1 / OUT(gain) | 15 / 44 | 1 / 1 | 18 / 없음 | 없음 | 3 / 1 | 2.4·10⁷ / 792 |
| two_stage_ota_sf(7 MHz, PM 목표 없음) | O1 / OUT(gain) | 14 / 30 | 1 / 1 | 14 / 없음 | 없음 | 3 / 1 | 1.6·10⁷ / 540 |
| two_stage_ota_sf | vout(버퍼, P-15) | 1 | 36(follower) | 없음 | 없음 | 1 | 648 |

- **함의**: gain 제약이 있는 3회로의 블록은 bin 하나당 Π_S = 14~44에 N_L(동치류 1~9개 × 근 있는 L bin × 3)을 곱한 수준이라 전수가 가능하다. 모든 블록의 Π가 N_S보다 작아 P-1 (b) 정지는 0이다. pushpull vout(52,675)은 N_T,i에 따라 절단·'추정'이 될 수 있다. gain 제약이 없는 회로(cga, folded)는 매크로가 비활성이라 S가 비고 input·cascode가 F로 남지만, gain 모드 층 0 자체가 꺼진다(§5.1).
- 단계 A·B를 넘지 못하는 3회로(current_reuse_telescopic_ota 정지, ngcc·nmcnr review_needed)는 층 0이 돌지 않는다(§5.1).

**층 0 안 배분**(배분 규칙은 v1.5와 같다. 새 배분 상수 없음):
- 블록 몫: N_T,i = max(1, N_T × min(n_i, N_T) / Σ_j min(n_j, N_T)).
  - N_T,i는 평가 상한일 뿐이다. 닿으면 정지하지 않고 절단한다(`layer0_candidates_truncated` 기록, 블록 front '추정', §5.3.11). 정지는 경로 열거 예산 초과와 Π > N_S뿐이다(결정 -- 사용자 결정 2026-10-12 "U-63은 (가)로").
- 조립 몫: N_T,0 = N_T − Σ_i (블록 i가 실제로 쓴 평가 수).
- 벽시계: 층 0은 외층 몫(T_reserve · t_eval)을 남긴 시각까지 돈다. 블록마다 남은 시간을 남은 몫 비로 나눈 시각에서 끊는다.
- 국소 봉인 호출은 `counters["layer0_local_calls"]`로 따로 센다. `kernel_calls == 고유 키` 불변식은 유지된다.

**외층 ε 점 수**(40 §3.6-5): 층 0이 끝난 시점의 시간으로 같은 식을 다시 계산한다(T_reserve 없이).

**LUT memo 상한의 층 0 항**(결정 -- 사용자 결정 2026-10-12 "U-60은 (가)로", U-60 = (가), 40 §2.4.6과 같은 문장, 검토 M6 선택지 (가)):
- U_L0,r = Σ_i K_max,i · (U_pass,i,r + U_macro,i,r). 블록 i의 **첫 후보**에서 한 번 세고, N_T,i를 곱하지 않는다. 퇴출은 허용하고 `perf`에 보고한다. 퇴출된 키를 다시 계산하면 FAIL이다(U-60 (가)).
  - U_pass,i,r = 블록 i 첫 후보의 고정점 한 바퀴(§5.3.6)가 영역 r에서 센 서로 다른 LUT 키 수다.
  - U_macro,i,r = 같은 바퀴의 매크로 호출(§5.3.6)이 센 서로 다른 LUT 키 수다.
  - K_max,i = 그 바퀴의 N3.6 반복 상한(§5.3.6)이다. 첫 후보가 수렴 전에 멈춘 경우에도 상한 K_max를 곱한다.
- 층 0이 꺼진 회로는 0이다. 계수 방식은 40 §2.4.6이 정본이다.

**기록**: `perf`에 N_T, t_eval, 블록 n_i·몫·사용 수, 고정점 바퀴 수 합, NONCONVERGENT 수, 폴백 수(사유별), 소진 여부를 쓴다. 계수 예산 N_S는 §0의 정의를 따른다.

### 5.9 외층 인계 (M7)

- 외층 SLSQP는 조립점에서 시작한다. 블록 gain은 제약에 넣지 않는다(DEC-05·74).
- **근방 반경**(40 §3.10.8 '근방 반경 확장 규칙'): 초기 r_j = max(|θ_j,local − θ_j,assembled|, h_j), h_j = 그 성분의 격자 분해능. 그 반경 안에 feasible이 없으면 반경을 2배로 넓힌다(DEC-80 예산 게이트와 같은 2배, 새 상수 아님). 멈춤: 반경이 전역 bounds에 닿거나, 확장에 쓴 평가 수가 DEC-34 예산 식의 남은 몫을 넘을 때. 층 0은 전역 bounds를 줄이지 않는다.
- ε 스윕의 첫 ε는 조합 점의 면적과 전력이다.
- r̂는 이미 평가한 받아들인 점에서 먼저 재고, 모자라면 Halton 시험을 표본 수 이하로 한다(`residual_probe(pool=, trials=)`). front 점의 `allocated`는 그 점의 풀이 사슬이 시작한 조립점의 조합에서 온다(`sweep_front` `roots`).

**불변식**: 층 0은 전역 bounds를 줄이지 않는다. 같은 입력이면 같은 조합 front다. 평가 계수는 `perf`에 남긴다.

**실패**: 모든 조합의 조립이 실패하면 §6 시작점으로 넘어간다. 그것도 실패하면 `SearchFailedError`다.

**상태**: `E/search/layer0_center.py`는 국소 기준점 생성, t_eval 첫 측정, 대체 시작점에만 쓰인다(U15).

### 5.10 as-built(U15) 대조와 구현 변경 목록

호출 경로(유지): `find_front` → `layer0_start`(기준점 = 국소 기준점·첫 t_eval·대체 시작점) → `layer0_budget` → 시작점(조립점 → §6 시작점 → S3 → x0, 없으면 `SearchFailedError`) → E_B 재유도(40 §3.6-5) → `sweep_front`.

**1. v1.5 §5.10 as-built 항목의 처리**

| v1.5 항목 | 처리 | 근거 |
|---|---|---|
| 1 국소 gain을 가장 가까운 LUT 격자 마디에서 | **폐기**. 운영 보간으로 평가한다(§5.3.5) | LR3, DEC-71 (4)(b) |
| 2 후보 θ = 축 선택(LUT gm/ID 마디·L 앵커) + placer, (c) 커널 위임, (d) 생략 | **폐기**. 역산 후보(§5.3.8), (c) §5.3.4, (d) §5.3.6 | DEC-71 (4)(a)~(d) |
| 3 b_gain 출처 | 유지(§5.2) | DEC-72 |
| 4 블록 범위(버퍼 상수항, 바이어스 의사 블록, GB3 기둥 매핑, 고정 입력, 강결합 그룹) | 바이어스 의사 블록·기둥 매핑·고정 입력은 유지. 버퍼 상수항은 섞인 회로에서 버퍼 DP 단계로 바뀐다(P-15, §5.6). 강결합 그룹 좌표 훑기는 폐기(P-1, §5.3.11) | DEC-71 (2)(3)(7), DEC-76 |
| 5 bin 격자 게이트·fail-closed | 유지(§5.4·§5.6) | DEC-80 |
| 6 평가 예산 | 몫 규칙·벽시계·계수 유지. '후보 수'의 정의만 n_i로 바꾼다(§5.8). 국소 봉인 memo는 폐기하고 S3 메모리 색인으로 바꾼다(§5.3.9) | DEC-34, 40 §2.4 |
| 7 DP 대표·종료 = 정확한 gain 합 | **변경**. 누적 = T_b 합(§5.6) | DEC-71 (3) 'gain ≥ 예산' |
| 8 rout 모드 | 버퍼만 있는 회로는 유지. 섞인 회로의 버퍼 블록에도 rout 국소 제약(P-15, §5.1) | DEC-71 (3) |
| 9 조립 전 조합 시도·`full_gain_db` 폴백 | 유지(§5.5) | DEC-71 (7), DEC-10 |
| 10 외층 인계 | 유지(§5.9) | DEC-71 (8) |
| 11 열린 항목 (b) 다듬기·knee 미정의·`comp_approx_gap` 없음 | **폐기**. (b)는 역산이 대신하고(§5.3.5), knee는 §5.3.7, `comp_approx_gap`은 §5.5 | LR5, DEC-16, DEC-92 (2) |

**2. 구현 변경 목록**(U15 코드 기준. 파일은 `E/search/` 아래, 따로 적은 것 제외)

| 대상 | 유지 / 변경 |
|---|---|
| `gain_bins.py`(`BinGrid`, 게이트) | 유지. 'bin b 충족 = gain ≥ T_b' 판정 함수를 더한다 |
| `local_front.py` | 변경: 점이 충족하는 모든 bin에 넣는다(§5.4). 칸 규칙은 유지 |
| `combo_dp.py` | 변경: 누적 gain = T_b 합 + 상수항(§5.6). 상태·동률·게이트는 유지 |
| `assembly.py` | 변경: 조립 = graph graft(40 §2.4) + 공유량 필드 재계산 + 전역 봉인. `comp_approx_gap` 기록을 더한다(§5.5) |
| `budget_override.py` | 유지. override = 목표 bin 고정(§5.7) |
| `local_candidates.py` | 변경: 후보 = §5.3.8 집합, 축 = S 자유·F 폴백만(B·FF 제외, matching 그룹·궤도 = 축 하나, §5.3.3). 평가 루프(계수, 벽시계, 반분 순서)는 그대로 쓰고, 좌표 훑기는 지우고 P-1 규칙(Π > N_S 정지, N_T,i 절단 + `layer0_candidates_truncated`·'추정', §5.3.11)으로 바꾸며, `local_seal_memo` 대신 S3 메모리 색인 `local(...)`·`solved(...)`(40 §2.4.5)를 쓴다. `lr5_knee_anchor_unavailable` 삭제 |
| `layer0_budget.py` | 변경: 첫 배분 g_i^(1)(L-2 found_db 비례, §5.3.2), 목표 bin 범위·순서(§5.3.2), n_i 몫(§5.8). `REC_KNEE_UNAVAILABLE` 삭제. 일감(`_jobs`)·기둥·고정 입력·예산·DP 루프는 유지 |
| `_helpers_place.theta_from_choice` | 변경: θ = §5.3.6 결과(ln IDu, 연속 L, W4 노드전압 θ, θ 전류) |
| `_helpers_rows.model_row` + `E/metrics` U9 `row_gains` | 변경: 축 값을 격자 index로 맞추지 않고 동작점 연속값으로 평가한다(L은 bin 안 선형, 나머지는 DEC-87 운영 보간). A_i,max 표(§4.2)는 격자 그대로 둔다 |
| 신규 `layer0_inverse.py` | (a) gm/ID 역산(`lut.vgs_for_gm_id`, §4.1 분류), (c) VDS 배분, (b) L 역산, (d) 국소 고정점(`sizing.k_max`·q 판정 재사용), 노드 C(`ss.node_c_farad`와 같은 함수) |
| 신규 `l_targets.py` | knee, feasible_L_window, 동치류 종류(주인 기준), LR5 격자·넓히기 |
| `E/sizing/size_and_seal_local.py` | 변경: 반환 = 국소 graph 스냅샷. 국소 전력·면적·gain은 블록 범위 metric 필드다. tol_I = 자기 dc 단계 gm 필드 × tol_V(§5.3.9) |
| 신규 A9 블록 `block_bounds_l0`(§4.2) | 추가: 층 0 정의역 상한 A_i,max^L0(축 규칙 §4.2, 단계 A9, S0 필드 `start.row`·`start.point`를 읽음, '추정', 40 §2.4.8 A9 행). 축소 전 표와 exit 3은 그대로 둔다 |
| §6.5 매크로(`macro_poles.macro_solve`) | 변경: 키워드 전용 인자 `node_c`·`gm_bounds`·`gain_targets`를 추가한다(§5.3.6). 공동 SLSQP·다중 출발은 그대로 둔다. 기본 호출은 as-built와 비트 동일이고 test가 `fp_of`로 확인한다. 결정 9 §6.7-4 B3의 기본 호출과 호환된다 |
| 커널 θ(40 §3.7-5) | W4 자유 노드전압 θ를 층 0 값으로 받는지 확인하고, 받지 않으면 writer 계획의 W4 초기값 입력을 더한다 |

**3. 범위 밖 항목과의 접점**
- **결정 9(§6.7 KVL 고리 출발 제약, 사용자 결정 2026-10-12 "K-1~K-3도 권고대로", 같은 문서 §6.7)**:
  - **공동 선택(7a) 결과가 들어오는 자리**:
    - (i) 고리 종속 멤버(`cycle_vgs`·`fixed_vgs`)의 gm/ID는 층 0이 고르지 않는다. W2 쓰기 계획이 정한다(§5.3.3 `kvl_dependent`).
    - (ii) 7a가 위치를 옮긴 writer 묶음의 선택점은 층 0 첫 회차의 출발값이다. 고정 입력 소자라면 §5.3.10 고정값이 된다. 블록 안 소자라면 §5.3.6 첫 바퀴 값이자 §5.3.11 자유·폴백 열거에서 그 축의 첫 점이 된다.
    - (iii) §6 구간은 (a) 역산과 폴백 격자의 정의역이다(§6.7 "구간은 그 역산의 정의역").
  - **placer**: 유지한다.
    - 역할은 θ 조립에서의 KCL·미러 전류 전파와 최소 폭 보정이다(§6 '같은 식').
    - 층 0이 정한 gm/ID·L·W4·θ 전류는 placer의 선택을 덮어쓴다. §6.7-6 "U15 `placer.place`(덮어쓴 묶음은 고정, 나머지만 변수)"와 같은 규칙이다.
    - placer는 층 0 안에서 7a를 다시 돌리지 않는다.
  - **`layer0_center._maxmin`·`_box_centre`**: 유지한다. 층 0 기준점(첫 t_eval 측정점, 대체 시작점, §5.9 상태)을 만드는 데에만 쓴다. §6.7-2의 저항 기하 중심은 `_box_centre`와 같은 값이다.
  - B1 "(a) 필요 gm -> gm/ID 역산, (c) VDS 배분(A1·A4 와 함께)"은 §5.3.3·§5.3.4와 같은 함수를 쓴다. §6.7-4 B3 매크로 재확인은 `macro_solve` 기본 호출이다(§5.3.6 불변 조건).
- **A7 → P-15(결정됨)**: 섞인 회로의 버퍼 블록에도 rout 국소 제약(§5.1, §5.6).
- **A8**: 차동쌍 완화. §5.3.3 입력 셀 gm_id 역산의 대상 집합이 바뀔 수 있다.
- **A9 → P-9(결정됨)**: N3.7 9회로 축소 격자 전수 대조는 §9 검증 항목이다. 층 0 결과를 바꾸지 않는다.
- **A10**: 접점 없음.

### 5.11 계획 조항 → 설계 절 대응표

| 계획 조항 | 요지 | 설계 절 |
|---|---|---|
| DEC-71 (3) 입력·첫 회차 배분 | GB4 비례 시작 배분(L-2: 축소 전 GB4 `found_db` 비례), 이후 조립 조합 | §5.3.1, §5.3.2 |
| DEC-71 (3) gain bin 고정 | bin마다 따로 푼다 | §5.2, §5.3.2 |
| DEC-71 (3) AC 제약 | 국소 gain ≥ 예산, 출력 임피던스 기록 | §5.2, §5.3.1, §5.4 |
| DEC-71 (3) 고정 입력 | 첫 회차 §6 + knee 추가 후보, 이후 조립점 | §5.3.10 |
| DEC-71 (4)(a) | gm_id = gm/ID 역산 | §5.3.3 |
| DEC-71 (4)(b), LR3 | 목표 gain → L 역산, bin 안 선형, bin 넘지 않음 | §5.3.5 |
| DEC-71 (4)(c), DF-25, IC4, WP-03 | VDsat 채움 → ∂(gm/gds)/∂VDS 큰 소자부터 | §5.3.4 |
| DEC-71 (4)(d), DEC-70 (c), N3.6 | 기생 C 국소 고정점, 같은 수렴 규칙 | §5.3.6 |
| DEC-71 (4) 폴백 | 그 소자만 격자, 사유 기록 | §5.3.3, §5.3.5, §5.3.8 |
| DEC-71 (4) "역산은 후보 수단" | 격자가 검증·폴백·미세조정 | §5.3.8, §5.3.11 |
| DEC-71 (5) | 국소 봉인 | §5.3.9, §5.4 |
| DEC-71 (6), DEC-77, DEC-80 | bin별 비지배 점, 칸, 게이트, DP | §5.4, §5.6 |
| DEC-71 (7), DEC-10 | 조립, 공유 VGS | §5.5 |
| DEC-71 (8), DEC-73 | 전역 정합·외층 인계 | §5.9 |
| LR5, DEC-16, DEC-19, I-A15 | knee, window, 동치류 격자, 넓히기, 역산 시작 후보 | §5.3.7 |
| DEC-92 (2)(4), N3.7 보상 규칙 | 근사식 = 층 0 시작점, `comp_approx_gap` | §5.3.6, §5.5 |
| DEC-34, N3.5 | 예산 상한 식 | §5.8 |
| DEC-72 | gain bin 폭 = 모델 오차, 미측정 '추정' | §5.2, §5.3.7 |
| 40 §3.7-5 | W4 초기값 = 층 0 VDS | §5.3.4 |
| 사용자 결정 L-3·L-11·L-12 (2026-10-12) | 회차 반복, 소자 종류 S/B/F, 층 0 정의역 상한 | §5.3.2, §5.3.3, §4.2 |
| 40 §2.4 graph 저장(사용자 결정 #1·#2·G-3') | §2.4.4 graft, §2.4.5 색인·보존(`local`·`solved`, v1.11 블록 결과 색인·실행 수명 보존 -- 옛 소유자 '층 0 단계(모든 회차)'·'외층 시작점 대기열' 폐지), §2.4.6 LUT memo, §2.4.8 필드 소유(매크로 결과·국소 gain·Z_out·`comp_approx_gap`·A9·회차 기록), §2.4.11 tol_I | §5.3.2, §5.3.6, §5.3.9, §5.5, §5.8, §4.2 |
| DEC-64 v2 | 고리 종속 멤버 gm/ID는 등식이 정함 | §5.3.3, §5.10-3 |
| DEC-67, DEC-91 (2) | 봉인 전 C_n '추정', 레이아웃 전 확산 기하 | §5.3.6 |
| DEC-71 (6) 같은 점 접기 | 접은 뒤 칸에 넣음 | §5.4 |

### 5.12 결정 기록 -- 설계가 더한 정의, 사용자 결정, 계획과 다른 점

#### 5.12.1 설계가 더한 정의 (사용자 결정 L-13으로 승인)

사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-13 "design 추가 정의 E1~E9 승인(E4 위·아래 끝 규칙의 A^L0 사용 부분과 E9 축 규칙은 검증 Major-1 수정 후, E8 은 FF 처리 Major-2 수정 후)". E4·E8·E9는 그 수정을 반영한 아래 문안이다.

| # | 정의 | 절 | 근거 |
|---|---|---|---|
| E1 | (b) L 역산의 일반형: 블록 국소 gain(L_c) = T_b를 L 동치류 c마다 **하나씩** 푼다. 나머지 동치류는 §5.3.7 초기 목표에, gm/ID·VDS는 현재 바퀴 값에 둔다. 근이 있는 L bin마다 후보를 하나 낸다 | §5.3.5, §5.3.8 | DEC-71 (4)(b), 방법론 §6.7 Phase 2 |
| E2 | 층 0 매크로 호출: 키워드 전용 인자 `node_c`·`gm_bounds`·`gain_targets`, 공동 풀이 유지, 기본 호출 비트 동일 | §5.3.6 | DEC-92 (2), §6.5 as-built 퇴화 기록 |
| E3 | VDS 배분 한 걸음 = LUT VDS 격자 간격. 나머지는 지나는 모든 기둥의 여유를 지킬 때만 준다 | §5.3.4 | DEC-71 (4)(c) |
| E4 | 목표 bin 범위: 위 끝 = max(A^L0 bin('추정'), 역산 실패 bin), 아래 끝 = 축소 전 A_max 인증일 때의 유도 또는 창 하한 clamp 반복 | §5.3.2 | DEC-71 (3) "bin마다 따로 푼다" |
| E5 | feasible_L_window의 W 경계 = PDK W_min, 면적 예산 W ≤ A_budget/L(옛 `W_bounds` 대체) | §5.3.7 | history §10.11 |
| E6 | 국소 고정점 변화량에 L 환산 항 \|∂VGS/∂L\|·\|ΔL\| | §5.3.6 | N3.6 지표 규칙 |
| E7 | knee 동률은 작은 L이다. 동치류 종류는 L 주인의 종류다 | §5.3.7 | LR1·DEC-17 |
| E8 | L-11 소자 종류의 구조 정의: S = 주경로 이득 블록 AC 역할 `input`(매크로 활성 = GBW 목표 있음, PM 없으면 PM 하한 경로), B = `load`·`mirror`·`diode_load`·`tail_source`·블록 밖 소자·**FF 셀**(§6.5 출발값 고정, 외층이 다듬음), F = `cascode`·`pass`·`follower`·매크로 비활성 회로의 `input`. matching 그룹·궤도로 묶인 S·F 소자는 축 하나 | §5.3.3 | 사용자 결정 L-11, 재검증 Major-2·Minor-3·Minor-4 |
| E9 | A^L0 축 규칙: (S∪F) gm/ID + L 전부 + 전류·저항 + 덮는 기둥 W4 VDS 격자, B VGS·VS는 S0 필드 `start.row`·`start.point`로 고정, 단계 A9, 늘 '추정' | §4.2 | 사용자 결정 L-12, 재검증 Major-1 |

#### 5.12.2 사용자 결정 기록 (L 번호 ↔ 이 문서 Q 번호)

| L | 옛 Q | 결정 원문(사용자 2026-10-12) | 설계 위치 |
|---|---|---|---|
| L-1 | Q1 | "계획 DEC-71 (4) "(I-A11)" 인용 오기 -> "N3.7 LUT 곡선 검사"로 계획 정정" | §5.3.3 폴백 사유, 계획 정정은 §5.12.3 D4 |
| L-2 | Q2 | "첫 회차 배분 = 축소 전 GB4 found_db 비례, 값 없는 블록만 기준점 블록 gain 보완, '추정' 표시(A^L0 비례는 쓰지 않음)" | §5.3.2 |
| L-3 | Q3 | (기승인) "2회차 이후 = 고른 조합의 미해결 (bin, 고정 입력 지문)만 재풀이, 조합 front 불변이면 정지, 상한 K_max(DEC-70 반복 자리 추가 포함)" | §5.3.2, D3 |
| L-4 | Q4 | "knee 축약 = 합집합 앵커(중복 제거, 늘어난 앵커 수 기록)" | §5.3.7 |
| L-5 | Q5 | "격자 폴백은 L-11 범위 밖(F 종류)에만, 정의역 §6 구간" | §5.3.3 |
| L-6 | Q6 | "L bin = 근이 있는 bin 마다 후보, 국소 front 가 고름" | §5.3.5 |
| L-7 | Q7 | "comp_approx_gap = UGF·PM 스칼라 차만 기록, 극점 목록 원본 보존(§6.5 옛 문장 정리)" | §5.5, §6.5 |
| L-8 | Q8 | "L 격자 넓히기 개선 = 비지배 개선 + 개선된 축마다 개선량 >= max(분해능, 모델 오차), 모델 오차 미측정이면 분해능 + '추정'" | §5.3.7 |
| L-9 | Q9 | "R29 를 좁히지 않음 -- 고정 입력 동치류 전부에 knee + LR5 종류 앵커(레플리카는 window 하한) 합집합" | §5.3.10 |
| L-10 | Q10 | "bin·DP 상태 상한 = 계수 예산 N_S 유지, 계획 DEC-71 (6)·DEC-80 문구 정정(NFR-4 결정론)" | §0, §5.4, §5.6, D2 |
| L-11 | -- | (기승인) "필요 gm 정의된 신호 소자만 gm/ID 자유변수(ID = gm/(gm/ID)), 부하·미러·바이어스는 §6 구간·미러비·KCL 로 정하고 격자 곱에서 제외" | §5.3.3 |
| L-12 | -- | (기승인) "GB4 블록 gain 상한 계산도 신호 소자 축만으로 축소 후 재측정" | §4.2 |
| L-13 | D1, E1~E9 | "design 추가 정의 E1~E9 승인 ..., D1 ... DP 단계 동률 = 최소 포화 여유 비, 조립·봉인 뒤 조합 front 동률 = 계획대로 활성 제약 여유 합; 계획 DEC-70 "세 곳뿐"·DEC-71 (4)(d) "세 번째" 정정(넷째 반복 자리)" | §5.12.1, §5.6, D1, D3 |
| L-14 | Q11 | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): 축소 상한은 층 0 전용(첫 배분 제외, bin 위 끝 보조), exit 3·§6.4-1은 축소 전 표 | §4.2, §5.3.2(이미 반영) |

**L-14 결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"). 근거: 축소 상한은 상위집합의 상계가 아니고(§4.2 '추정'), 직전 측정에서 축소 값(54.5 dB)이 축소 전 격자 일부 값(67.7 dB)보다 낮았다. exit 3에 쓰면 gain 57 dB 회로를 잘못 멈출 수 있다.

#### 5.12.3 계획과 다른 점·계획 문언 정정

| # | 내용 | 계획 원문 | 설계 | 처리 |
|---|---|---|---|---|
| D1 | 조합 동률의 둘째 기준 | DEC-71 (6) "전력이 작은 쪽, 동률이면 활성 제약 여유 합이 큰 쪽" | DP 단계 = 최소 포화 여유 비, 조립·봉인 뒤 조합 front = 활성 제약 여유 합(§5.6) | L-13 결정. DP 단계만 계획과 다르다 |
| D2 | bin·DP 상태 게이트 예산 | DEC-71 (6)·DEC-80의 "DEC-34 예산 식에서 계산한 평가 수" | 계수 예산 N_S(§0) | L-10 결정. 계획 DEC-71 (6)·DEC-80 문언 정정 |
| D3 | 층 0 회차 반복 = DEC-70 넷째 반복 자리 | DEC-70 "반복은 (a) ... (b) ... (c) 층 0 국소 고정점 ... 세 곳뿐이다", DEC-71 (4)(d) "DEC-70이 세는 반복 자리에 (c) 층 0 국소 고정점을 세 번째로 추가" | (d) 층 0 회차 반복(§5.3.2)을 넷째로 더한다 | L-3·L-13 결정. 계획 DEC-70 "세 곳뿐" → "네 곳뿐", DEC-71 (4)(d) "세 번째"에 '(d) 회차 반복은 넷째' 추가 정정 |
| D5 | DEC-81 복합 블록 묶음 크기 상한 | DEC-81 "묶음 크기가 DEC-34 예산 식의 평가 수를 넘으면 `unsupported_rule_branch`" | 계수 예산 N_S(§1.9) | **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로")(U-65, 계획 DEC-81 정정). L-10과 같은 이유(결정론) |
| D4 | 비단조 폴백 근거 인용 | DEC-71 (4) "LUT 비단조 구간(I-A11)" | N3.7 'LUT 곡선 검사'와 §4.1 | L-1 결정. 계획 인용 정정 |

#### 5.12.4 축소 전 A_i,max 인증 현황 (실측, L-2 근거)

(2026-10-12, as-built bd19cc6, 읽기 전용 스크립트 `wt/_tmp_l0design/measure_l0.py`, 결과 `results.jsonl`. A^L0는 §4.2 표)

| 회로 | 단계 A / B | gain 제약 | 이득 블록 | A_max 인증 / 미상 | 미상 사유(Π) | `found_db` |
|---|---|---|---|---|---|---|
| common_gate_amplifier | ok / ok | 없음 | 1 | 0 / 1 | `grid_product_over_budget`(1.9·10¹⁰) | 53.4 |
| folded_cascode | ok / ok | 없음 | 1 | 0 / 1 | 같음(6.2·10⁵²) | 119.3 |
| pushpull_follower_buffer | ok / ok | 없음 | 0(버퍼 1, 미상) | -- | -- | -- |
| sf_pushpull_output_opamp | ok / ok | 있음 | 1(+버퍼 1, 미상) | 0 / 1 | 같음(3.4·10⁸⁰) | 없음 |
| two_stage_ota | ok / ok | 있음 | 2 | 0 / 2 | 같음(1.7·10²², 1.9·10⁹) | 61.2, 67.7 |
| two_stage_ota_sf | ok / ok | 있음 | 2(+버퍼 1, 인증 −0.7 dB) | 0 / 2 | 같음 | 61.2, 67.7 |
| current_reuse_telescopic_ota | stopped / -- | 있음 | 3 | 단계 B 없음 | `unsupported_rule_branch`(cs_output_low_impedance, J-C) | -- |
| ngcc_3stage_ff | review_needed / -- | 없음 | 3 | 단계 B 없음 | -- | -- |
| nmcnr_amplifier | review_needed / -- | 없음 | 3 | 단계 B 없음 | -- | -- |

#### 5.12.5 P·K·C 결정 반영과 남은 질문 (2026-10-12)

**결정 반영**:

| 결정 | 원문 | 41 위치 |
|---|---|---|
| P-1 | "DEC-76 경로 열거 상한 초과 = 정지(unsupported_rule_branch), 좌표 훑기 축소 탐색 폐기" | §5.3.11, §5.8, §5.10, §9 |
| P-9 | "9회로 축소 격자 전수 대조 추가(N3.7, NFR-5)" | §9 |
| P-15 | "이득 블록과 섞인 회로의 버퍼 블록에도 rout 국소 제약(DEC-71 (3))" | §5.1, §5.3.3 F 행, §5.6, §5.8, §5.10 |
| K-1 | "KVL 고리 공동 선택 기준 승인 -- 위반 최소 -> 가장 낮은 위치 최대(max-min) -> 위치 합 최대, ..." | §6.7-4·10 |
| K-2 | "β·C_eff 근사 정의는 design 검증에서 지적이 없을 때 승인(지적이 있으면 다시 묻는다)" | §7.5, §6.7-10 |
| K-3 | "input_tie(U2 기본안 (a)) 폐기, 대칭 포트는 U2 자기동형 묶음(domain.ties)이 대신, 구현 순서는 결정 6(d/s 맞바꿈) 다음" | §6.7-1a·10 |
| C-2 | "(가) Cs1·Cs2 kT/C 선언하지 않음, 300 uV 는 OTA 소자 잡음 적분(폐루프 귀환 조건)으로 판정. 적분 대역은 논문에 명시 없음(spec 의 대역 정의 유지)" | §6.4-3, §7.1, §7.3, §7.5, §7.6, §9 |
| Q1(2026-10-08) R3 복원 | 40 §8 R3은 "Q1~Q11 모두 네 의견대로 진행해" Q1로 복원 | §4.5 |

**설계가 더한 정의(승인 대상)**:

| # | 정의 | 절 | 근거 |
|---|---|---|---|
| E10 | 버퍼 블록(rout 제약)에서 블록 출력노드에 source가 닿는 follower는 필요 gm이 rout 제약으로 정의되므로 S다. 한 출력노드의 여러 follower는 공통 배율 하나로 Z_out = `rout_ss_ohm`을 푼다(§5.3.3) | §5.3.3 | L-11 "필요 gm 정의된 신호 소자만 gm/ID 자유변수"를 rout 제약에 적용. P-15 |

**남은 질문**(계획이 정하지 않은 것):

| # | 쟁점 | 계획 원문 | 선택지 | 권고 |
|---|---|---|---|---|
| PQ1 | P-9 '축소 격자'의 정의 | N3.7 "전체회로 MNA를 목적·제약으로 쓰는 축소 격자 전수탐색(다른 모델)과 대조한다"(무엇을 어떻게 줄이는지는 없음) | (i) A^L0와 같은 축(§4.2: S∪F gm/ID, L 앵커, W4 VDS, 전류·저항, B는 §6 값)을 축마다 반분 단계 순으로 줄여 Π ≤ N_S가 되게 함 (ii) θ 성분 전부를 축마다 같은 점 수로 균등 추출 (iii) 회로별 선언(spec `verification.reduced_grid`) | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): (i). B 고정 가정은 이 대조로 검증되지 않음을 보고에 기록한다. 층 0과 다른 모델(전회로 MNA)이고 같은 정의역이라 대조의 뜻이 분명하다. 다만 B 고정은 층 0과 같은 가정이라, 그 가정 자체는 이 대조로 검증되지 않는다 |
| PQ2 | P-1 정지 범위(검토 M1) | DEC-76 "만들지 않은 폴백이 필요한 입력이 실제로 오면 ... 탐색 전 정지" | (i) Π > N_T,i 정지(직전 판) (ii) 정지는 경로 열거 초과와 Π > N_S뿐, N_T,i는 절단 + '추정'(§5.3.11) | **결정**(사용자 결정 2026-10-12 "U-63은 (가)로", U-63): (ii). 재측정(kvl 종속 제외·`input_tie` 제거)으로 최대 Π = 52,675(pushpull vout) < N_S라 library 정지 0, 절단 가능 블록은 pushpull vout 하나 |
| PQ3 | 섞인 회로에서 rout 미선언 버퍼 | DEC-71 (3) "그 선언도 없으면 그 블록은 '층 0 무동작'으로 보고하고, 그 회로는 층 0 없이 출발 구간 시작점으로 탐색" | (i) 그 블록만 무동작, 나머지 층 0은 돈다(설계) (ii) 회로 전체 층 0 끔(문언) | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): (i). 그 블록만 층 0 무동작 + 보고. 문언은 버퍼만 있는 회로를 두고 쓴 것이고, 이득 블록 예산은 그대로 정의된다. 현재 library 해당 회로 0 |
| PQ4 | E10 승인 | -- | 승인 / 출력 follower도 F | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): 승인. 한 출력노드에 follower가 둘 이상이면 공통 배율 하나로 Z_out = `rout_ss_ohm`을 푼다(E10, §5.3.3 -- §5.3.6 공동 풀이와 같은 변수 하나라 결정론) |
| PQ5 | §6.7 P1: KVL 등식을 단계 A8 출발 선택에도 거는 것 | DEC-71 (7)·N3.7 "조립 단계에서 푼다" | 유지(현 설계) / 조립에서만 | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): 유지(출발 단계 A8에도 KVL 등식, 조립 처리는 그대로). 조립의 처리는 바꾸지 않고 출발점 실현 가능성만 높인다 |
| L-14 | 축소 상한 쓰임 | §5.12.2 | -- | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): 축소 상한은 층 0 전용, exit 3·§6.4-1은 축소 전 표(설계 반영됨) |

### 5.13 판정 경계 위에 일부러 놓는 점 (NFR-4 3안, v1.9.4)

사용자 결정 2026-10-15 "1안·3안 진행하고 ③ 기준 변경도 승인해"의 3안이다. 층 0 전류 중심에서 드러났고, 엔진 안의 같은 종류 자리(아래 표) 전부에 적용한다. 근거 요구: 계획 NFR-4(같은 입력 → 같은 산출물)와 40 §2.4.13 (2)의 '다른 실행 환경에서 이산 판단 정확 일치'.

**용어**: **경계 배치점** = 엔진이 판정 행 c ≥ 0(`ConstraintRow.c`, 분해능 단위)의 c = 0 위에 일부러 놓는 값. 풀이기가 활성 제약을 c ≈ 0으로 몰아 생긴 점은 경계 배치점이 아니다(아래 '남은 위험').

**문제**: 경계 배치점의 경계 좌표를 풀이기 수렴값에서 읽으면, 그 점의 c 부호는 풀이기 허용오차 안의 잡음이 정한다. 그 잡음은 BLAS 경로에 따라 다르다. 그래서 같은 입력에서 이산 판단이 뒤집힌다. 사례는 `E/search/layer0_center.py:238-246` 끌어올림이다(cfe2e31 실측: 주석 238-239, `lift = u` 240, 시도 루프 241-246, 반환 247 -- 옛 문장 '238-245'를 정정). 이 끌어올림은 Chebyshev 풀이(`:235`)의 목적값 u로 움직이는 θ 전류를 모두 e^u 배 해서 '가장 낮은 MOS 전류 = 기준 전류(`StartRung.current_ref`, 폭 W_min의 전류)'를 겨냥한다. pushpull_follower_buffer에서 시작점의 `w_min:M1` 행 c는 스레드 1에서 +1.13e-10, 스레드 8·18에서 −2.30e-6이다. 그래서 `hard_ok`(`:683`)의 `np.all(c >= 0)`이 뒤집힌다(같은 판정이 최선점 키 `:407`과 외층 `best` `E/search/slsqp_outer.py:230`에도 있다). 같은 결함은 스레드가 같아도 c를 0 아래로 놓을 수 있다: folded_cascode의 시작점 `w_min:M8` 행 c는 스레드 1에서 −4.68e-10이고 `hard_ok` = False다. 측정 조건은 아래 표 밑과 history에 있다.

**규칙**:
- **BP1 닫힌 식 배치**: 경계 배치점의 경계 좌표는 풀이기 수렴값에서 읽지 않는다. 그 행의 선언량(PDK·LUT·기준값)과 고정 순서 산술의 닫힌 식으로 계산하고, 판정 쪽으로 부동소수 여유 √ε(상대)만큼 안쪽에 놓는다. 풀이기 해는 '어느 행을 경계에 놓을지'를 고르는 데만 쓴다. √ε는 엔진이 같은 목적으로 이미 선언한 값이다(`E/search/start_intervals.py:78` `_REL`: 'W = W_min 이 정확히 경계라 반올림이 아래로 떨어지지 않게 하는 여유'). 새 상수가 아니다. **쓰는 방식(J-6, 오케스트레이터 기본안 -- 사용자 결정 아님)**: `_REL`은 비공개 이름이라 다른 파일에서 import할 수 없다(규칙 B). 그래서 `layer0_center`는 정의식 `math.sqrt(sys.float_info.epsilon)`을 그 자리에서 쓴다 -- 같은 정의식을 그 자리에서 쓰는 선례가 이미 있다(`E/search/macro_poles.py:282`, `E/search/iv_matching_l.py:99`). 근거: 값의 출처는 정의(부동소수 기계 엡실론)이고 상수를 짓는 것이 아니다. `_REL`을 공개 이름으로 바꾸거나 core에 정본을 두는 것은 `start_intervals.py`·다른 두 자리를 함께 고치는 별개 정리라 이 card 범위 밖이다(최소 변경). 여유가 필요한 까닭: 닫힌 식으로 놓아도 판정 값은 다른 산술 경로(커널 W = ID·L/exp(ln IDu) 대 기준 W_min·IDu/L)의 반올림 차만큼 0 근처에 남는다(측정: +9.53e-14 분해능 단위). √ε 여유를 두면 c ≈ √ε·W_min/grid다(측정: +1.25e-6 분해능 단위). 이 값은 반올림 수준보다 약 10^7배 크고, 활성 판정 경계(c ≤ 1, `E/search/constraints.py:27-28`)보다 훨씬 작다.
- **BP2 판정은 그대로**: 경계 배치점의 판정은 c ≥ 0 그대로다. 허용 띠(c ≥ −분해능)를 두지 않는다.
- **BP3 자기 판정식 확인**: 배치하는 함수가 판정식을 직접 가지는 자리는, 배치한 뒤 같은 식으로 확인한다. 통과하지 못하면 판정 허용오차만큼 안쪽으로 물러나 다시 확인한다.

**층 0 끌어올림의 식(BP1)**: 풀이기 해 x(θ 전류의 ln)에서 MOS 행 m(θ 전류를 하나라도 읽는 원뿔 행)마다 두 값을 잰다. A_m(x) = Σ(움직이는 θ 전류 항)/기준 전류_m이고 F_m = Σ(고정 전류 항)/기준 전류_m이다. 움직이는 전류를 e^s 배 하면 q_m(s) = A_m·e^s + F_m이다. 끌어올림 배수는 e^s = max_{m: A_m > 0} (1 + √ε − F_m)/A_m이다. 그 행은 q = 1 + √ε에 놓이고, 나머지 A_m > 0 행은 그 이상이다. u(풀이기 목적값)는 이 식에 쓰지 않는다. 원뿔이 깨지면(고정 전류·음의 계수) 올리지 않는 것과 변수 상자 클램프(`:244`)는 as-built 그대로다. **적용 조건(J-9, 오케스트레이터 기본안 -- 사용자 결정 아님)**: as-built 조건(`:240` -- 출발 사다리 칸이 있고 그 `StartRung.current_ref`가 비어 있지 않을 때만 끌어올린다)을 그대로 둔다. 근거: 끌어올림의 목적은 '모든 MOS 전류 ≥ 기준 전류 = 폭 W_min의 전류'다. 사다리 칸이 없으면 기준 전류는 kind 전류 상자의 기하 중심(`:190-193`)이라 W_min과 무관하고, q ≥ 1 + √ε는 경계 배치점이 아니다(BP1 대상 아님). 조건을 바꾸면 사다리 없는 회로의 시작점이 새로 바뀌어 3안 범위 밖 동작 변경이 된다. 측정 시제품은 F_m = 0인 경우만 구현했다(s = −min_m ln q_m(x) + ln(1 + √ε)). F_m ≠ 0인 행이 최소가 되는 경우는 착수 때 test로 덮는다.

**끌어올림 식의 가장자리**:
- A_m > 0인 행이 하나도 없다(모든 원뿔 행이 움직이는 전류에 대해 감소하거나 무관): 끌어올릴 행이 없다. s = 0(올리지 않음)이다. as-built의 '원뿔이 깨지면 올리지 않는다'와 같은 결과다.
- A_m > 0인 모든 행에서 1 + √ε − F_m ≤ 0(고정 전류만으로 이미 q ≥ 1 + √ε): 식의 최댓값이 0 이하라 ln이 정의되지 않는다. s = 0이다(이미 경계에서 여유가 있다).
- 식의 값이 s < 0(Chebyshev 해의 최소 행이 이미 1 + √ε보다 위 -- 끌어올림이 전류를 낮추게 됨): as-built `lift`는 u ≥ 0으로 올리기만 한다(`:232` u 상자 하한 0). **s = max(0, 식의 값)이다** -- as-built처럼 올리기만 한다(Q-N9 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-85).

**같은 종류 자리**(2026-10-15 grep `w_min_m`·`_REL`·`float_info.epsilon`·`bracket_root(`·클램프, tests 제외):

| 자리 | 경계에 놓는 것 | 판정 | 규칙 |
|---|---|---|---|
| `E/search/layer0_center.py:238-246` 끌어올림 | 가장 낮은 MOS 전류 = 기준 전류 | `:407`·`:683`, `E/search/slsqp_outer.py:230`의 c ≥ 0 | **BP1 위반 → 위 식으로 고친다** |
| `E/search/start_intervals.py:126-128` `current_ref` = max(scale, W_min·IDu/L) | 전류 미정 소자의 자리값을 W = W_min에 | 판정 아님(BP1 식의 입력) | BP1 준수(선언량 닫힌 식) |
| `E/search/start_intervals.py:137-152` `_width_floor_gm_id` | W = W_min·(1 + √ε)인 gm/ID | 같은 함수의 `excess ≤ 0`, 아니면 곡선 마디로 물러남 | BP1(√ε 여유)·BP3 준수 |
| `E/search/start_intervals.py:390-395` 면적 예산 경계 t | 실행 가능 판정의 경계 t | `feasible(solve(t − tol))` 재확인 | BP3 준수 |
| `E/search/iv_area.py:72-78` `w_min_gm_id` 상한 | W = W_min인 gm/ID(출발 구간 끝점) | 끝점 넘음 판정 `E/search/start_intervals.py:407`(√ε 상대 비교) | 구간 끝점(배치 아님) |
| `E/search/iv_matching_l.py:99` 입력쌍 L 하한 | σ_ΔVGS = σ_share인 L(출발 구간 하한) | 커널 판정 행의 경계가 아니다 | **해당 없음(2026-10-15 확인)**: 하한은 실제로 출발 L이 된다(측정 3 current_reuse M4a·M4b `l_chosen` = `l_lo` = 3.221e-6, `E/search/start_intervals.py:307-310` 하한 최댓값을 `_snap`이 그대로 고름). 그러나 σ_share = σ_target/√2는 입력 셀의 몫이고(`E/search/iv_matching_l.py:8`, `:123`), 커널 판정은 전회로 MNA `offset_in_sigma_mv`가 모든 소자 기여를 합해 한다(같은 파일 docstring '출발값 전용(EP-7)'). 그래서 이 L은 커널 판정 행의 c = 0 위가 아니다 |
| `E/search/iv_matching_l.py:63`, `E/search/iv_noise.py:61` W 클램프 max(…, W_min) | 모델 입력 W | 판정 없음(mismatch·잡음 모델 입력) | 해당 없음 |
| `E/search/layer0_center.py:244`, `_halton_probe` 상자 클램프 | θ를 변수 상자 끝에 | 상자는 정의역(판정 행 아님) | 해당 없음 |
| `E/search/macro_poles.py:353-357` 채택 판정 | (풀이기 해) | abs(ln abs(H)) ≤ √tol 등 허용 띠 | 배치 아님 -- 남은 위험 |
| `E/search/layer0_center.py:374`, `E/search/slsqp_outer.py:195` | (풀이기가 활성 제약을 c ≈ 0으로) | `:407`·`:683`·`:230`의 c ≥ 0 | 배치 아님 -- 남은 위험 |

**검토한 안과 측정**: 엔진 사본(`wt/_nfr4_design_scratch/repo`, master 34932a9 복제)만 고쳤다. 단계 A → B → `build_search_context` → `find_front`를 `OPENBLAS_NUM_THREADS` 1·8·18로 실행했다. 실행마다 별도 프로세스·빈 S0·빈 표 캐시를 썼다. '엔진 결정 차이' = 측정 3 이산 키에서 풀이기 호출 기록(`slsqp[…]`)과 경로 계수(nit·iterations·`n_history`·sweeps·평가 수·커널 호출 수)를 뺀 키의 차이다(40 §2.4.13 (3) D 부류). pushpull_follower_buffer:

| 안 | 내용 | 엔진 결정 차이 1 대 8 / 1 대 18 / 8 대 18 | `hard_ok` 1·8·18 | 시작점 `w_min:M1` c 1·8·18 | 판단 |
|---|---|---|---|---|---|
| 현행 | e^u 끌어올림 | 125 / 125 / 0 | T·F·F | +1.13e-10 · −2.30e-6 · −2.30e-6 | 결함 재현 |
| (a) 닫힌 식, 여유 없음 | e^s = 1 / min_m q_m(x) | 1 / 1 / 0 | T·T·T | +9.53e-14(세 스레드 같은 비트) | 경계 부호는 고쳐진다. 그러나 c가 반올림 수준이다. 남은 차이가 1건인 것은 우연이다(아래) |
| **(a2) 닫힌 식 + √ε 여유(BP1)** | e^s = (1 + √ε) / min_m q_m(x) | 125 / 125 / 0 | T·T·T | +1.25e-6(세 스레드 같은 비트) | **채택**: 경계 부호가 고쳐지고 반올림에 견딘다. 남은 125건은 경계 배치와 다른 원인이다(아래) |
| (b) 판정 허용 띠 | `:407`·`:683`·`:230`을 c ≥ −1 | 124 / 124 / 0 | T·T·T | 현행과 같음 | 기각: W < W_min 점을 경성 통과로 센다. 40 §10.5 'spec 제약 행 c ≥ 0'과 충돌한다. 경계 좌표의 잡음은 그대로다 |
| (c) 한 분해능 칸 안쪽 | e^(u + ln(1 + grid/W_min)), 목표 W = W_min + 격자 1칸 | 136 / 136 / 0 | T·T·T | 스레드 1의 최소 행 = `current_cone:M6` 1.0, 8·18 = `w_min:M1` 0.99999767 | 기각: 목표 c = +1이 활성 판정 경계(c ≤ 1)에 놓여 그 부호가 다시 잡음으로 정해진다. u의 잡음도 그대로 남는다 |

- **pushpull의 남은 차이는 경계 배치가 아니다.** (a2)에서 `hard_ok`와 시작점 c는 세 스레드가 같다. 그래도 외층 ε 풀이 `EP:s1`이 스레드 8·18에서 `L:M1` FD 열 실패로 그 변수를 고정한다(`frozen:L:M1`). 재시작이 2회에서 6회로 늘고, 평가 18번부터 다른 점을 잰다. 시작점의 경계 밖 성분은 스레드마다 다르다(`current/M4` 상대 5.6e-4, `current/M5` 4.8e-5 -- Chebyshev 풀이 `:235` 해의 잡음). 그 차이가 외층 풀이 경로를 가른다. 이 갈림은 이 규칙 범위 밖의 '남은 위험' (2)다(아래).
- (a)의 남은 1건은 `eval[35]`의 `failure.margin`이 정의되었는가다(스레드 1 = 2.08, 8·18 = None). 이 1건만 남은 것은 우연이다. (a)와 (a2)는 시작점이 √ε(상대 1.5e-8)만큼 다를 뿐인데 스레드 1에서 엔진 결정이 123건 다르다. 즉 pushpull의 외층 경로는 시작점의 그 정도 차이에도 갈린다.
- 측정 3의 인과 가설('시작점 c 부호가 달라 외층 첫 QP가 다르고, FD 열 실패로 L:M1이 고정된다')은 (a2)로 반증됐다. c 부호가 같아도 같은 갈림이 생긴다.
- (a2)를 9회로 1·8·18에 적용했다. 엔진 결정 차이는 pushpull 말고 0이다(현행도 같다). 경로 계수 차이는 남는다(current_reuse 7, nmcnr 8, sf_pushpull 8, two_stage_ota 7, two_stage_ota_sf 2). `hard_ok`는 9회로 모두 세 스레드가 같다.
- (a2)가 바꾸는 결과(스레드 1, 현행 대비 엔진 결정 차이)는 두 회로다. folded 1(`hard_ok` False → True, 시작점 c −4.68e-10 → +1.25e-6), common_gate 2(ε 풀이 `EA:s1` best seq 34 → 23, stop `converged` → `slsqp_8`)다. 나머지 7회로는 0이라고 적었으나 틀렸다(v1.11 정정, nfr4c2 판정 0305b8c A-5): √ε 여유가 경계에서 끌어올린 층 0 점 전부를 움직여 nmcnr_amplifier·pushpull_follower_buffer·sf_pushpull_output_opamp도 바뀐다(front·hard_ok·stop 불변, nmcnr `block_recomputes_same_input` 64 → 80). 사용자 결정 2026-10-16 N-5로 수용했다. 변화 0은 two_stage_ota·two_stage_ota_sf·current_reuse_telescopic_ota·ngcc_3stage_ff 4회로다. S0 수준 결과(`search_base.fp`·`context_fp`)는 비교할 수 있는 7회로에서 모두 같다(common_gate의 현행 측정에는 S0 기록이 없다). → 층 0·탐색 결과 기준선은 다시 잰다(40 §2.4.13 (7)).

**남은 위험**(이 규칙 범위 밖): 풀이기가 정한 값의 잡음은 BP1로 없앨 수 없다. 닫힌 식이 없기 때문이다. 두 갈래가 있다. (1) 풀이기가 활성 제약을 c ≈ 0으로 몬 점의 부호 판정. (2) 풀이기 해의 경계 밖 성분이 다음 풀이의 경로를 가르는 것(위 pushpull). 같은 실행 환경에서는 1안 고정(40 §2.4.13 (1))으로 비트 재현된다. 다른 환경에서 갈리면 40 §2.4.13 (2)의 이산 비교가 FAIL로 드러낸다. pushpull은 지금 엔진으로는 다른 환경 비교에서 FAIL할 것으로 본다. 스레드 1 대 8이 그 대리 측정이다. 처리(Q-N7 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-83): 알려진 결함으로 기록하고(42 D-ND4) 이 card를 끝낸다. 원인(외층 FD 열 실패와 재시작 경로)은 후속 card NFR4-F1(40 §2.4.13 (8))로 조사한다. 2안은 다시 열지 않는다.

**as-built 변경**: `E/search/layer0_center.py:238-246`(위 식, 옛 `lift = u` 줄 240은 같은 변경에서 지운다. u는 `centre_u` 반환값으로만 남는다), 끌어올림 설명 문장 -- cfe2e31 실측으로 끌어올림 설명은 모듈 docstring 2번 항목(`:12-18`)에 **없고** 코드 주석 `:238-239`와 `E/search/CONTRACT.md:1063-1065`(U13.2 '전류 확정' 끝 문장 '해의 편차 u(ln)만큼 움직이는 θ 전류를 모두 올려')에 있다. 이 둘을 닫힌 식으로 고치고 docstring 2번 항목에 끌어올림 한 문장을 더한다(옛 문장 '모듈 docstring 2번 문단(끌어올림 설명)'을 정정). **test**(test 작성 주체, 소스 열람 없이 이 절만으로):
- `test_layer0_lift_closed_form`: toy 원뿔에서 끌어올린 뒤 최소 행 q가 1 + √ε와 같은지(부동소수 반올림 범위 안), 나머지 A_m > 0 행 q ≥ 1 + √ε인지 단언한다. F_m ≠ 0인 행이 최소인 toy를 포함한다. **반올림 범위(J-15, 오케스트레이터 기본안 -- 사용자 결정 아님)**: 상대 허용폭 γ_n = n·ε/(1 − n·ε)(표준 반올림 오차 상계, ε = `sys.float_info.epsilon`), n = test가 끌어올린 θ에서 q_m을 다시 계산하기까지 위 식이 거치는 부동소수 연산 수를 그 toy의 항 수로 센 값(s 계산: A_m·F_m 항마다 exp·곱·나눗셈과 합, 분자 1 + √ε − F_m, 나눗셈, ln / θᵢ = exp(xᵢ + s): 덧셈·exp / q_m 재계산: 항마다 곱·나눗셈과 합). 상수를 짓지 않는다 -- n은 식에서 세고 γ_n은 정의다. 셈 규칙(N-6): 덧셈·뺄셈·곱셈·나눗셈은 IEEE 754가 정확 반올림(상대 오차 ≤ ε/2)이고, `math.exp`·`math.log`는 정확 반올림이 보장되지 않으나 libm의 통상 오차 한도 1 ulp(상대 오차 ≤ ε)를 쓴다 -- 그래서 연산마다 상대 오차를 ε로 잡아 사칙연산·exp·ln을 **각 1회로** 센다(사칙연산은 그 절반이라 이 셈이 위쪽 상계다). `max`·`min`·클램프·비교는 반올림이 없어 세지 않는다. libm 1 ulp는 플랫폼 libm의 문서화된 한도이고 새 상수가 아니다. 이 한도를 넘는 libm이면 test가 실패로 드러낸다(넓히지 않는다). 단언: |min q − (1 + √ε)| ≤ γ_n·(1 + √ε).
- `test_layer0_lift_independent_of_solver_noise`: 같은 문제에서 풀이기 해 x만 허용오차 안에서 흔든 두 입력을 쓴다. 최소 행이 같으면 끌어올린 뒤 그 행의 `w_min` c가 둘 다 0보다 크다. **풀이기 해 주입(J-16, 오케스트레이터 기본안 -- 사용자 결정 아님. 선례: XRUN-F1 card A J-3·card 1 J-5의 모듈 속성 교체 계약)**: 모듈 속성 `gmid_engine.search.layer0_center.scipy_minimize`(as-built `from scipy.optimize import minimize as scipy_minimize`, 전류 중심 `:235`·최대-최소 `:374`가 모듈 전역 이름으로 부른다)를 교체 지점으로 고정한다 -- 이름·호출 방식(키워드 `jac`·`method`·`bounds`·`constraints`)·반환에서 `x`를 읽는 방식을 바꾸지 않는다. test는 `centre_start(sctx, rung)` 호출 동안만 이 속성을 진짜 풀이 결과의 x를 흔들어 돌려주는 감싸개로 바꾼다(`centre_start`는 전류 중심만 부르고 최대-최소는 부르지 않는다). 가장자리 test(아래 '끌어올림 식의 가장자리' 셋 -- R 빔, 분자 모두 ≤ 0, 식 값 < 0이면 s = 0)도 같은 지점으로 x를 정한다.
- `test_layer0_boundary_rows_positive_9circuits`(엔진 고정 상태, 스레드 수를 바꾸지 않음 -- 이 test에서는 스레드 비교를 하지 않는다. 고정 뒤에는 스레드 비교로 경계 배치 결함을 드러낼 수 없기 때문이다. 고정 자체가 듣는지는 40 §2.4.13 (7)의 `test_blas_thread_determinism`이 같은 환경 1차 검사로 계속 본다): 9회로 층 0 시작점에서 BP1로 경계에 놓인 행의 c가 0보다 크다. 그래서 `hard_ok`가 경계 배치 때문에 False가 되지 않는다. 현행 코드에서는 folded_cascode(`w_min:M8` c = −4.68e-10)에서 실패해야 한다(red 재현). 이 값은 34932a9 복제에서 잰 것이고 card 1(실행 사이 재사용 제거)·code_hash·library spec 병합 뒤인 card base cfe2e31에서는 재지 않았다(J-14): auditor가 test 동결 전에 cfe2e31에서 folded `w_min:M8` c < 0을 부호 단언으로 재현하고, 재현되지 않으면 멈추고 보고한다(다른 red 회로나 toy가 필요 -- 그때 이 절을 고친다). red는 import 오류가 아니라 비트·부호 단언이어야 한다. pushpull 탐색 결과의 다른 환경 일치는 이 card의 완료 조건이 아니다(남은 위험 (2), Q-N7 확정, 후속 card NFR4-F1).

---

## 6. 스펙에서 gm/ID·L·전류 출발 구간 (단계 A8)

**쓰임**: 출발값과 보고에만 쓴다(EP-7). 입력은 S1/S1v, spec, LUT 곡선, A6 상한표다.

**파일**: `E/search/start_intervals.py`, `iv_headroom.py`, `iv_speed.py`, `iv_gain_l.py`, `iv_matching_l.py`, `iv_noise.py`, `iv_area.py`, `iv_currents.py`, `macro_poles.py`, `dominant_node.py`.

**matching·헤드룸**(사용자 결정 2026-10-08 Q3·Q4): 절대 offset 제약이 있으면 matching L 하한(§6.4-2), offset 구조 가드가 있으면 부하 gm/ID 상한(§6.4-2a), 스윙·ICMR 제약이 있으면 헤드룸 예산 분할(§6.2)을 계산한다.

**잡음 경로**: 범위 안이다(사용자 결정 2026-10-08, §7). 1/f 제약이 있으면 1/f L 하한(§6.4-3)을, 열잡음 제약이 있으면 열잡음 gm 하한(§7.5)을 계산한다.

**LUT 곡선 API(신규)**: `ft_curve`, `intrinsic_gain_curve`, `vdsat_curve`, `idu_curve`.

### 6.1 계산 순서 (순환 없음, M8)

궤도마다 대표 소자로 계산하고, L 동치류는 구간의 교집합을 쓴다. 순서는 다음과 같다.

0. 주극점 노드를 구조로 정한다(§6.3). 이 단계는 매크로 모델을 쓰지 않는다(N3).
1. 헤드룸 gm/ID 하한(§6.2).
2. 이득 L 하한(§6.4-1). [gm/ID_lo, LUT 최대] 구간에서 intrinsic gain이 가장 큰 gm/ID를 쓴다.
3. 속도 L 상한(§6.4-4). gm/ID_lo를 쓴다.
4. matching·잡음·면적 L 경계(§6.4-2, -3, -5). 이 단계에 필요한 전류는 1차 전류 추정(§6.5 1회차)에서 가져온다.
5. L 선택(§6.4-6).
6. 그 L에서 속도 gm/ID 상한(§6.3).
7. gm/ID 선택: 구간 안의 최댓값.
7a. **KVL 고리 공동 선택**(§6.7, v1.6): 7의 선택을 소자별 독립 최댓값으로 끝내지 않는다. 쓰기 계획이 정한 v2 고리 등식(종속 소자의 VGS)과 고리가 정한 VDS 의 포화 부등식을 만족하는지 재고, 위반이 있으면 그 행에 묶인 소자들만 각자 구간 안(올림 포함)에서 다시 고른다(기준은 7과 같이 gm/ID 큰 쪽). 올린 점은 매크로·면적 실행 가능성을 다시 잰다. 해가 없으면 충돌 레코드(§6.6). 이 선택점은 층 0 역산 우선(DEC-71 (4), §5)의 첫 회차 고정 입력이고, 구간은 그 역산의 정의역이다.
8. 전류 확정(§6.5 2회차). 열잡음 gm 하한(§7.5)과 열잡음 C_eff 하한·1/f L 하한(§7.5, β·C_eff 입력)을 함께 적용한다. 8 에서 전류가 바뀌어 최소 폭 보정(§6.5 as-built)이 gm/ID 를 올리면 7a 를 다시 잰다(상한 = 소자 수, 7a 가 바꾼 것이 없으면 끝).

9. **출발 사다리**(as-built 0868ff5 `search/start_intervals.py`·`start_values.StartRung`, 층 0 `layer0_start`가 소비):
   - **t**: 구간 안 위치다. 소자마다 gm/ID = gm/ID_lo + t·(gm/ID_hi − gm/ID_lo)이고, t = 0은 하한 끝, t = 1은 상한 끝이다(7의 선택은 t = 1에서 시작한다).
   - **steps** = ⌈log2(span / floor)⌉(span > 0일 때, 아니면 0). span = max_소자 (gm/ID_hi − gm/ID_lo), floor = 그 소자들 LUT 곡선의 gm/ID 최솟값이다. 구간 폭을 LUT gm/ID 최솟값 단위까지 반으로 가르는 횟수이고, t 탐색 분해능 2^−steps와 같다.
   - **칸 0(선택점)**: 실행 가능(면적 ≤ 예산, 매크로 근 있음)한 최대 t*. t = 1이 실행 가능하면 t* = 1이고, 아니면 [0, 1]에서 `bracket_root`(허용오차 2^−steps)로 경계를 찾아 그보다 한 칸 아래를 쓴다. 칸 0은 매크로 확정 풀이(전원 전류 최소화 포함)의 전류를 쓴다. 7a(KVL 고리 공동 선택)는 칸 0에 적용한다.
   - **칸 k = 1..steps**(t* > 0일 때): t_k = t*/2^k. 매크로는 전원 전류 최소화 없이 실행 가능한 출발점(`refine=False`)만 풀고, 7a를 칸마다 다시 적용한다(§6.7-6).
   - **칸의 내용**(`StartRung`): t, θ(구간이 값을 정한 성분만: ln IDu, θ 전류, 보상 커패시터, L 동치류 L), L 칸 index, 기준 전류(매크로가 전류를 정하지 못한 소자의 자리값).
   - **저장**: 칸 목록은 S0 수준 필드 `graph/start: rungs`(as-built `StartIntervals.ladder` 그대로, U17 ①-b), 선택점 둘레 출발 θ 생성기의 입력(선택 gm/ID·L·칸·t)은 `graph/start: placement`다(40 §2.4.8). `placement`는 U17 ②에서 U15 `placer`와 함께 만들고, as-built MOD8 `Placement`(`E/convergence/convergence_values.py:47`)와 다른 것이다(40 v1.9.1 D4, 근거: 소비자 위치). 층 0 `layer0_start`는 칸 0부터 차례로 커널에 확인해 처음 받아들일 상태인 칸을 기준점으로 쓴다(§5.9 상태).

**4의 전류를 정하는 방법**: 4는 전류 I가 필요하다. 그 값은 §6.5 매크로 모델을 **1회차**로 돌려 얻는다. 1회차에서는 gm/ID를 gm/ID_lo로 두고 L을 2의 하한으로 둔다. 확정 전류는 8에서 다시 계산한다. 4→8 사이에는 되먹임이 없으므로(8의 결과가 4로 돌아가지 않는다) 순환이 생기지 않는다.

### 6.2 gm/ID 하한 -- 헤드룸

**기둥별 가용 폭**:

V_col = ΔV_rail − Σ VGS_min(diode) − Σ R·I_cert

- VGS_min은 LUT 최대 gm/ID에서의 VGS다.
- 인증 전류 I_cert가 없으면 R 강하는 0이다.

**스윙 구간 분할**: 스윙 [V_lo, V_hi] 제약이 있는 노드 n에서 기둥을 나눈다.
- 위쪽 예산 = V_rail,hi − V_hi.
- 아래쪽 예산 = V_lo − V_rail,lo.

**하한**: 다음 식을 `vdsat_curve`로 역산한 값이 gm/ID_k,lo다. 여러 기둥에 걸친 소자는 그중 최댓값을 쓴다.

VDSAT_k(gm/ID) ≤ V_part − Σ_{j≠k}(VDSAT_j,min + tol_VDsat,j)

VDSAT_j,min은 LUT 최대 gm/ID에서의 VDSAT를 L 점 전체에서 최소로 한 값이다.

**스윙·입력 범위 제약에서 V_lo·V_hi 정하기**(사용자 결정 2026-10-08 Q4, 정의는 40 §3.8-3):
- `swing_out_v >= s`: 출력 노드마다 요구 반폭 h = s/2(단일 출력) 또는 s/4(차동 출력, 출력마다). 출력 DC V_o가 spec에 선언되어 있으면 V_hi = V_o + h, V_lo = V_o − h. 선언이 없으면 위·아래 예산 합 = ΔV_rail − 2h로 두고, 둘의 나눔은 위·아래 부분 기둥의 최소 요구(Σ(VDSAT_j,min + tol_VDsat,j))에 대한 남는 여유의 최솟값이 가장 크도록 정한다(계산값, 상수 없음).
- `icmr_v >= w`: 입력 경로 기둥(입력 셀 gate에서 레일까지의 VGS·VDS 엣지 경로)의 가용 폭을 ΔV_rail − w로 두고 같은 식으로 역산한다.
- `icm_margin_v >= 0`이고 입력 DC V_icm이 선언된 회로: 입력 경로의 위쪽 예산 = V_rail,hi − V_icm, 아래쪽 예산 = V_icm − V_rail,lo.
- 경계의 여유는 사용자 SPICE 포화 규칙 VDS ≥ VDSAT에 LUT `tol_vdsat`를 더한 것뿐이다. 3σ 같은 통계 관례는 쓰지 않는다(사용자 결정 Q4 (4)).
- 이 구간이 비면(필요 폭 > 가용 폭) 41 §4.6 헤드룸 달성가능성 보고와 같은 사실이다. 출발 구간은 충돌 레코드로 남기고 자르지 않는다(§6.6).

### 6.3 gm/ID 상한 -- 속도

- **전제**: `gbw_target_hz`와 `pm_target_deg`가 있어야 한다. 없으면 비활성이다.
- **비주극점 조건**: f_np ≥ GBW / tan(90° − PM)(2극점 근사).
- **주극점 노드(구조로 결정, N3)**: gain 제약 전달 뷰에서 정한다.
  - Miller (2) 루프가 있으면, 그 수동소자 구간이 잇는 두 노드 중 앞 노드(BFS 거리가 작은 쪽)가 주극점 노드다. Miller 증배가 걸리는 노드이기 때문이다. 루프가 여럿이면 블록 순서상 가장 앞 블록의 출력노드인 것을 쓴다.
  - Miller 루프가 없으면 출력 포트 노드가 주극점 노드다. 부하가 걸리는 노드다.
  - 등급이 '높음'이 아닌 노드는 주극점 노드 후보에서 뺀다.
- **대상 노드**: 극점 노드에서 주극점 노드를 뺀 나머지 전부다.
- **조건**: 그 노드에 낮은 등급 단자를 주는 소자는 f_T(gm/ID, L) ≥ f_np를 만족해야 한다.
- **산출**: `ft_curve`를 역산해 gm/ID_k,hi를 얻는다.

### 6.4 L 구간

1. **이득 하한**:
   - 블록 목표 g_i = G·A_i,max / Σ A_max로 둔다.
   - 블록 국소 모델 gain ≥ g_i를 만족하는 최소 L을 찾는다. bin은 오름차순으로 훑고, bin 안에서는 bisection한다.
   - A_max가 미상이거나 gain 제약이 없으면 비활성이다(H3).
2. **matching 하한**(사용자 결정 2026-10-08 Q3 "q3,q4는 네 제안대로 해", 근거 `_drafts/engine/matching_swing_spec_proposal.md` §0·§2.3): **절대 offset 제약**(`offset_in_sigma_mv <= 값`, 현재 파일럿 3.3 mV)이 있는 회로에서만 활성이다. 구조 가드(`offset_excess`, §6.4-2a)만 있는 회로는 L 하한이 아니라 부하 gm/ID 상한으로 간다.
   - **mismatch 모델(옛 식 대체)**: 옛 식 A_min = (A_VT² + A_β²/(gm/ID)²)/σ² 는 `vth0` 한 항과 β 한 항만 본다. ngspice 감도 실측(제안서 §0.3)에서 `toxe`는 β보다 Vth로 더 크게 들어가고(BSIM4 k1ox 경로, n 2.2–4.1·p 2.3–6.5 mV·µm로 `vth0` 항과 같은 크기), nfet 약반전에서는 `voff` 항이 `vth0` 항을 넘는다. 옛 식은 nfet을 1.2–2.4배, pfet을 1.05–1.4배 과소평가한다. 그래서 **유효 계수 A_eff**로 바꾼다.
     - 단일 소자 게이트 환산 σ: σ_VGS(W, L, 점) = √(Σ_k (DVGS_k(L, 점) · slope_k(bin(W, L)) / slope_k(bin_ref))²) · √(W_ref·L_ref) / √(W·L).
     - k는 mismatch 블록의 `*_slope_spectre` 변수 **전수**다(`vth0`, `toxe`, `voff`, `nfactor` 등 카드가 쓰는 것, lint·wint는 slope 0이라 0 기여). 같은 ID에서의 ΔVGS로 정의하므로 β 경로(1/(gm/ID)에 비례)와 Vth 경로가 한 열에 함께 들어간다.
     - 쌍: σ_ΔVGS,pair = √2·σ_VGS(두 소자 독립). A_eff(L, gm/ID) = σ_ΔVGS,pair·√(W·L)이고 읽는 쪽에서 계산한다(열로 저장하지 않는다).
     - DVGS_k는 §6.4-2b의 LUT 감도 열에서 읽는다(상수 표를 박지 않는다).
   - **slope 출처**(사용자 결정 2026-10-08 Q2, 이번 Q3로 bin 규칙 보강): PDK `C:/pdk/sky130_fd_pr/cells/{nfet,pfet}_01v8/sky130_fd_pr__*_01v8__mismatch.corner.spice`를 파싱한다.
     - 모델 카드는 파라미터를 `p = p0 + p_slope·(slope_spectre)/√(l·w·mult)` 꼴로 흔든다(`toxe`는 toxe0을 곱한 상대값).
     - **bin마다 쓰는 slope 이름이 다르다.** 모델 카드(`*__tt.pm3.spice`) `.model` 블록마다 lmin/lmax/wmin/wmax와 그 블록이 쓰는 slope 이름(`vth0_slope` / `vth0_slope1`, `toxe_slope` / `toxe_slope1` 등)을 읽어 LBinMap과 같은 bin 지도에 붙인다. 예(제안서 §0.1 전수 집계): pfet L < 0.5 µm 36 bin은 `vth0_slope1` = 7.356e-3(L ≥ 0.5 µm의 5.856e-3 대비 +26 %), nfet L 4–8 µm·좁은 W 4 bin도 `vth0_slope1`. 옛 `legacy/sizing_recipe.py:3073`은 pfet에 5.856e-3 하나만 썼다(결함, 대조 기준선으로만 기록).
     - 참고 유도값(vth0 항만, 대조용): A_VT = √2·`vth0_slope` = nfet 4.75, pfet 8.28(L ≥ 0.5) / 10.40(L < 0.5) mV·µm. A_β = √2·`toxe_slope` = nfet 0.487, pfet 0.628 / 0.911 %·µm. LUT 감도 열의 `vth0` 성분은 이 값과 같아야 한다(U3 test (c)).
   - **단위 확인**: `models/all.spice` `.option scale=1.0u`라 l·w는 µm²다. 구현 첫 커밋에서 ngspice 소자 쌍 Monte Carlo(mismatch 블록 변수를 소자마다 gauss로, 오라클 측·엔진 비의존)로 σ(ΔVGS at 같은 ID)를 재고 A_eff 식과 비교한다. 그 비교를 test로 고정하고, 확인한 단위와 출처(파일 sha256·행)를 `core` PDK 선언에 기록한다.
   - **하한**: 출발 단계의 입력 셀 몫 σ_share = σ_target/√2(입력 셀 분산 = 나머지 분산, §6.4-2a 가드와 §7.5 잡음과 같은 등분 원칙 -- 새 상수가 아니라 '부하 기여 ≤ 입력쌍 기여'의 경계). 입력 셀 소자 면적 하한 A_min(L, gm/ID) = A_eff(L, gm/ID)² / σ_share², **L ≥ √(A_min·IDu/I)**. A_eff가 L에 의존하므로 §6.4-1처럼 bin을 오름차순으로 훑고 bin 안에서 bisection한다.
   - 판정은 이 하한이 아니라 봉인 스냅샷의 `offset_in_sigma_mv`(40 §3.8, MNA 전회로)가 한다(EP-7).
2a. **offset 구조 가드 → 부하 gm/ID 상한**(`offset_excess <= √2` 회로): 부하 소자 k의 입력 환산 분산 비 Σ_k (gm_k·σ_VGS,k)² / Σ_in (gm_in·σ_VGS,in)² ≤ 1이 되도록 부하 gm/ID를 상한으로 둔다. gm_k/gm_in은 §6.5 매크로 모델 전류 비로 쓴다(§7.5 잡음 가드와 같은 방법). §6.3 속도 상한·§7.5 잡음 상한과 교집합하고, 헤드룸 하한(§6.2)과 충돌하면 충돌 레코드로 남긴다.
2b. **LUT mismatch 감도 열**(U3): 생성기 `assets/sky130_lut_sweep.py`에 mismatch 모드를 더한다.
   - 방법(제안서 §0.3과 같음): pm3 카드 복사본에서 변수 k의 `*_slope_spectre`를 0 → 1(인스턴스 기하의 1σ)로 바꾼 섭동 곡선과 기준 곡선을 같은 include·DUT 줄로 돌리고, 기준 곡선의 칸 ID에서 두 곡선의 VGS 차를 DVGS_k로 둔다(W_ref·각 L·DC LUT 축 격자).
   - **저장**: 새 버전 파일 `..._mismatch_r1.npz`(sha256, 생성 메타: 모델 경로·sha, ngspice 버전, 온도, 섭동 변수 목록)에 둔다. **공유 `lut_data`의 기존 v2 r2 파일은 고치지 않는다.** `lut_v2_location.json`에 새 항목으로 더한다. 로더는 v2 칸과 같은 키로 합쳐 노출한다.
   - **tol**: 칸별 `tol_mismatch`를 LOO로 계산한다(DEC-87 방법, 디스크 캐시 대상 -- v1.10: 실행 사이 유지, U-87 원래 취지의 예외, 40 §2.4.12 Q9).
   - 감도 데이터가 없는데 offset 제약이 선언되면 `SchemaRejectedError(mismatch_lut_missing)`이다.
   - 한계 기록: 제안서 실측은 W 5 µm·|VDS| 0.9 V·VS 0 한 슬라이스였다. 생성기는 DC LUT 축(VDS·VS·W 슬라이스) 전체에서 잰다.
   - API(신규): `mismatch_dvgs(kind, w_key, L, VGS, VDS, VS) -> MismatchSens{dvgs: {param: V}, slope_ref: {param: value}}`.
3. **flicker 잡음 하한**(사용자 결정 2026-10-08, 파일럿 `noise_out_int_vrms` 제약에서 활성):
   - 출발 단계에서는 §7.5에 따라 (총 예산 − 스위치 kT/C 항)의 절반을 flicker 몫으로 보고, 이를 출력 적분 예산으로 둔다. 스위치 항은 `sampling_caps` 선언이 없으면 0이다(파일럿 = 0, C-2).
   - 입력 소자의 flicker 출력 적분은 Σ_in (K_k/(W_k·L_k))·∫ f^−EF_k·|폐루프 잡음 이득|² df이다. K는 §7.2의 A·W·L이고 W에 무관하다. 적분은 매크로 모델 폐루프 응답으로 계산한다.
   - 위 식에서 입력 소자 면적 하한 A_min = W·L이 나온다. W·L = I·L²/IDu에서 **L ≥ √(A_min·IDu/I)**이다(matching 하한과 같은 꼴).
4. **속도 상한**: f_T(gm/ID_lo, L) ≥ f_np에서 L의 최댓값.
5. **면적 상한**(결정 11):
   - L ≤ √(A_budget · IDu / I)
   - W ≤ A_budget / L
6. **선택**: L = max(1, 2, 3의 하한)이다(2a는 L이 아니라 gm/ID 상한이다). LUT L 점이나 bin 안 값으로 맞춘다(LR3). 구간 끝이 다른 bin에 있으면 bin마다 후보를 하나씩 둔다.

### 6.5 전류 출발값 -- S1v 매크로 모델 (H4)

DEC-92 (2)의 근사를 회로별 식이 아닌 일반 매크로 모델로 둔다.

**망 구성**:
- **노드**: gain 제약 전달 뷰의 극점 노드.
- **이득 블록 출력노드 컨덕턴스**: 블록마다 VCCS gm_i를 둔다. 출력노드 컨덕턴스는 G_i = gm_i / 10^{g_i/20}이다.
  - g_i가 없으면 A_i,max를 쓴다.
  - 둘 다 없으면 G_i = gm_i / A_intr,i로 둔다. A_intr,i는 블록 입력 소자의 LUT gm/gds(출발 gm/ID, L)이다. 캐스코드가 없다고 가정한 값이므로 보수적이다.
- **출력노드가 아닌 극점 노드**(캐스코드 source 노드 등, N9): 낮은 등급 단자를 주는 소자 c의 gm_c + gmb_c를 컨덕턴스로 둔다.
  - 이 값은 블록 gm에 비례하게 표현한다: gm_c = gm_i · ((gm/ID)_c / (gm/ID)_in) · r_c.
  - r_c는 KCL·미러 비로 정해진 전류 비다. 같은 가지에 있으면 1이다.
  - gmb/gm 비는 LUT에서 읽는다.
  - 높은 등급 노드는 붙은 drain 단자들의 gds 합을 쓴다. 이것도 같은 방식으로 gm_i에 비례한다.
- **노드 용량**: 부하 + 소자 cgg 추정(gm/(2π f_T)) + 보상 수동소자.
- **feedforward·복합 블록**: 경로마다 VCCS를 하나씩 둔다. feedforward 묶음(§1.12.2)의 VCCS 값은 G_ff = r_ff · gm_in(B_b)이고, r_ff = 1(영점 상쇄 조건 후보)이다. 그 묶음 소자의 전류 출발값은 이 G_ff와 FF 경로 미러 비로 전파한다. 이것은 출발값이며, 판정은 외층이 한다(EP-7).

**보상 수동소자 값 규칙(하나만 쓴다, N9)**:
- 선언값이 있으면 그 값을 쓴다.
- 선언값이 없으면 **PM ≥ `pm_target_deg`를 만족하는 최소값**을 쓴다.
- θ 범위의 기하 중점은 1-D 근 찾기의 **첫 구간 분할점**으로만 쓴다.

**풀이 순서와 실패 처리**:
1. 극점과 영점은 pencil 고유값으로 구한다(`pencil_roots`).
2. 한 바퀴는 다음 세 단계를 차례로 수행한다.
   - (i) gm_1: UGF = `gbw_target_hz`의 1-D 근(`bracket_root`). 이때 나머지 값은 현재 값으로 둔다.
   - (ii) k = 2..n 블록 순서로 gm_k: PM ≥ 목표인 최소값.
   - (iii) 보상 수동소자: 정준 순서로 PM ≥ 목표인 최소값.
3. 한 바퀴의 모든 값 변화가 각자의 1-D 근 허용오차 안에 들면 수렴이다. 상한은 K_max 바퀴이고, 닿으면 마지막 값을 쓰고 `macro_nonconvergent`를 기록한다(보고만, 정지 아님).
4. 어떤 1-D 근이 그 변수의 범위(전류 상자 × gm/ID, θ 범위)에서 괄호가 잡히지 않으면 다음과 같이 처리한다.
   - 그 변수는 현재 값을 유지한다.
   - `macro_root_missing{variable, condition}`을 기록하고 다음 변수로 넘어간다.
   - 모든 변수가 근 없이 끝나면 매크로 출발값을 버리고 상자 기하 중심을 쓴다.

**특수 경우**: 단일 블록이고 Miller 루프가 없는 회로에서는 gm_1 = 2π·GBW·C_out이 나온다. U-12 기본안과 같은 값이지만, `compensation: null` 태그가 아니라 구조에서 나온다.

**전류**:
- I = gm / (gm/ID).
- 나머지 소자는 미러 비와 KCL로 전파한다.
- 남는 θ 전류는 상자 기하 중심이다.

**기록**: `comp_approx_gap` = UGF·PM 스칼라의 (조립점 MNA − 매크로) 차이고, 극점·영점 목록은 두 쪽 원본을 보존한다(§5.5, 사용자 결정 L-7).

**구현 반영(as-built, 단위 U13, 2026-10-09)**:
- **풀이는 순차 바퀴가 아니라 공동 풀이 + 다중 출발**이다. 위 '풀이 순서'(gm_1 UGF -> gm_k PM 최소 -> C PM 최소)는 퇴화한다: gm_1 을 고정한 채 gm_k 를 줄이면 이득이 1 아래로 떨어져 (i)이 풀리지 않고, gm_1 을 함께 다시 맞추면
  gm_1 상자 상한 모서리로 간다; UGF 에서 잰 PM 은 모든 gm 을 같이 줄여도 변하지 않아(척도 불변) '최소 gm' 이 하한으로 간다. 대신 같은 제약 -- |H(jω_GBW)| = 1, PM(ω_GBW) ≥ 목표, 주극점을 뺀 극점 ≥ ω_GBW·tan(PM)(§6.3) --
  아래 전원 전류 합 최소를 SLSQP 로 한 번에 푼다. 이 문제는 비볼록이다(주극점이 어느 단에 놓이는지가 국소 최소를 가른다; 3극점 C = 1·2·3 pF 에서 주극점을 1 pF 단에 둔 국소 최소는 전역 최소의 1.7 배).
  그래서 단마다 그 단을 주극점으로 하는 실행 가능한 출발점(나머지 단 gm 을 2 배씩 올리고 그 단 gm 으로 UGF = GBW)에서 다중 출발하고, 구조로 정한 주극점 노드(`dominant_node`, §6.3)의 단을 먼저 시도한다. 만족해 중 전류가 가장 작은 해를 쓴다.
  구조 주극점 노드의 극점을 강제로 가장 낮게 두지는 않는다(큰 커패시터 단이 구조 주극점이 아닌 회로에서 전류가 더 큰 해가 된다 -- 독립 test 의 2극점 닫힌 식 oracle 이 자유로운 단 선택의 최소를 기대한다).
- **출력노드 컨덕턴스의 A_i 순서**: 이득 제약이 있고 모든 블록의 A_i,max 가 인증되면 블록 목표 g_i(§6.4-1), 아니면 입력 소자의 LUT 진성 이득 A_intr. 위 설계의 중간 단계 'g_i 가 없으면 A_i,max' 는 쓰지 않았다
  -- 이득 제약이 없는 회로에서 인증 상한(최적 격자 점의 값)을 블록의 실제 이득으로 가정할 근거가 없다.
- **PM 목표가 없으면** 매크로는 경계 PM_FLOOR_DEG = atan(1) = 45°(비주극점이 UGF 에 놓임)를 PM 하한으로 풀이 안에서만 쓰고 `pm_floor_pole_at_ugf` 로 기록한다. §6.3 속도 gm/ID·L 상한은 설계대로 PM 목표가 없으면 비활성이고 사유 `pm_target_missing` 을 보고한다.
- §6.2: 출력 DC 가 선언되지 않은 창은 남는 여유를 위·아래 부분 기둥의 같은 몫으로 나누고, 최소 폭 W ≥ W_min 은 확정된 전류에서 gm/ID 를 올려 맞춘다(전류가 입력 소자를 따르는 미러 부하는 gm 고정 하한이 어긋난다). §6.4-1 은 U9 블록 국소 모델(`BlockModel`·`ParamTables`)로
  목표 g_i 를 맞추는 최소 L 을 앵커 오름차순으로 찾고, 같은 bin 안에서는 앵커 사이 gain(dB)을 L 에 선형으로 보간한다(파라미터 표가 앵커 격자라 bin 안 L 에서 모델을 다시 풀 수 없다).

### 6.6 충돌과 보고

**충돌 레코드** `StartConflict{device|group, quantity, bounds[{source, value}], gap}`를 남기는 경우:
- 하한 > 상한
- 전류 > 상자 상한
- A_est > 예산(보고만)
- KVL 고리 행(§6.7)이 소자 구간 안 어떤 조합으로도(매크로·면적 실행 가능성과 함께) 모두 0 이상이 되지 않음(`quantity = "kvl"`, `bounds` = 남은 위반 행 (행 종류, 소자, 값 V), `gap` = 가장 나쁜 행 값의 크기). 양 끝 후보 대신 위반이 가장 작은 조합을 넘긴다(§6.7-5).
- 열잡음 C_eff 하한 > 선언 커패시터 값(§7.5, `quantity = "capacitance"`).

충돌이 있어도 자르지 않는다. 양 끝 후보를 '충돌' 표시와 함께 층 0으로 넘긴다.

**보고 표**: `start_intervals[{device, gm_id_lo/hi/chosen, L_lo/hi/chosen, bin, I_start, sources, inactive_reasons, conflicts}]`

**불변식**: 같은 입력이면 같은 표다. 이름 전단사는 행 이름만 바꾼다.

**상태**: MISS. as-built는 spec과 무관한 LUT 포락선 상자 중점을 쓴다(`E/search/search_domain.py:35-56`, `layer0_center.py:105-172`).

### 6.7 KVL 고리 출발 제약 (v1.6, 사용자 결정 2026-10-12 "9번 권고대로", "B는 권고대로")

**원리(바꾸지 않는 것)**: 입력단 gm 은 spec(§6.5 매크로 모델)에서 오고, gm/ID 는 [헤드룸 하한 §6.2, 속도 상한 §6.3] 구간 안에서 고르며, 전류 = gm/(gm/ID)다. 노드 전압을 먼저 배분하고 gm/ID 를 역산하지 않는다(reference `gm-id-methodology.md` §4.1·§6.4·§6.7, `sky130-worked-example.md` §6). 이 절은 구간을 그대로 두고, **구조가 묶은 소자는 독립으로 고르지 않는다**는 등식·부등식만 더한다.

**층 0 과의 관계(계획 DEC-71 (3)(4), 사용자 결정 B1 "계획을 따른다")**:
- §6 의 출력은 **구간(경계)**과 그 안의 출발 선택점이다. 계획 DEC-71 (4)의 역산 우선 -- (a) 필요 gm 에서 gm/ID = gm/ID 역산, (b) 목표 이득에서 L 역산, (c) VDS 배분(전 소자를 VDsat + tol 로 채운 뒤 남은 헤드룸을 LUT `∂(gm/gds)/∂VDS` 가 큰 소자부터) -- 은 **층 0(§5) 블록 국소 문제가 이 구간 안에서** 한다. §6 은 역산의 정의역(구간)과 첫 회차 고정 입력(DEC-71 (3) '첫 회차는 스펙에서 유도한 출발 구간 값')을 준다.
- VDS 배분은 층 0 의 몫이다(이 절은 VDS 를 배분하지 않는다). 이 절의 포화 행은 **고리가 정한 VDS**(W4 창이 아닌, 나무로 정해지는 VDS)만 검사한다 -- 층 0 의 배분 결과든 §6 선택점이든 같은 행으로 잴 수 있다(층 0 은 국소 봉인 항목 7·8 이 같은 사실을 판정한다).
- 층 0 쪽 받는 자리는 §5.10-3이다: 고리 종속 멤버는 층 0이 고르지 않고(§5.3.3 `kvl_dependent`), 7a가 옮긴 writer 묶음 선택점은 층 0 첫 회차의 고정 입력(§5.3.10) 또는 첫 바퀴 값(§5.3.6)이다. §6 구간은 (a) 역산·자유·폴백 축의 정의역이다.
- **단계**: 이 절 전체는 단계 A(A8 안의 7a)다. 봉인된 값을 읽지 않는다(§0). 결과는 S0 수준 필드다(아래 7).

**왜**: §6.1-7 은 소자마다 구간 최댓값을 따로 고른다. VGS 고리(DEC-64 v2)는 한 소자의 VGS 를 나머지 VGS 합·차로 정하고, VDS-1 고리는 한 소자의 VDS 를 VGS 합·차로 정한다. 따로 고른 최댓값(모두 약반전, VGS 최소)은 그 합·차를 무너뜨린다. 실측(as-built bd19cc6, 사다리 칸 0): 파일럿 M4a VDS = −0.03 V(VDS = VGS(M63) − VGS(M3a) 꼴), sf_pushpull M10 노드 근 없음, nmcnr M301 VDS ≈ 0(사다리 7칸 모두 실패, Halton 시험 점에서만 출발).

**1. 고리의 출처 -- 새 탐지기를 만들지 않는다**: 평가 커널의 쓰기 계획(`node.dc_writer` 나무 + `device.dc_coord`, GB7 `dc_writer_plan`, sizing CONTRACT 3절)을 읽는다. 쓰기 계획은 S1 G_vgs 고리(`graph.rel_kvl_branch`, DEC-64)를 레일·W3 선언 노드·입력 DC·저항 강하까지 넣어 컴파일한 것이고, 종속 소자는 DEC-95 (3) 우선순위로 이미 정해져 있다.
- 비나무 MOS 엣지 중 `cycle_vgs`·`fixed_vgs` = **고리 등식**(DEC-64 v2 `Σ±VGS = ΔV`): 그 소자의 VGS 는 나무 경로가 정한다. `parallel_vgs`(v0)는 같은 VGS 묶음(§6.1-6)이라 대상이 아니다.
- **v1(포트 차 고리)**(계획 DEC-64 v1, 사용자 결정 B2·O-13 (1)): 입력 포트끼리의 '같은 DC' 등식은 없다(아래 1a). 포트 경로가 둘 이상인 v1 고리는 ΔV를 소거한 KVL 하나가 남아 그 고리 멤버 하나가 `cycle_vgs` 종속이고(파일럿 VGS1a − VGS1b = VGS4a − VGS4b, M1b), 그 종속은 위 항목의 고리 등식과 같은 대상이다 -- 이 절의 행 생성 규칙은 바꾸지 않는다(계획 N6.5 '고치지 않는 것': §6.7 KVL 출발 제약은 U17 ② 몫이고 IT-1 뒤의 쓰기 계획을 읽는다). 대칭이면 그 등식은 대칭 묶음과 중복이다. (v1.12 정정: 옛 문장 'v1 고리는 이 절의 행을 만들지 않는다'는 O-13 (1)과 어긋나 고쳤다 -- 옛 문장은 계획 history H2 'IT-1·IT-2 design' 행.)
- drain·source 가 같은 나무 성분에 있는 diode 아닌 MOS = **VDS-1 부등식**(`gvgs_summary.vds_saturation` 과 같은 뜻): VDS = 나무 경로 합·차 ≥ VDSAT + tol_vdsat.

**1a. 커널 쪽 개정(DEC-64 v1 을 계획에 맞춤, 사용자 결정 B2·K-3·O-13, card IT-1 -- 계획 N6.5)**:
- 개정 전(as-built, master `9401e98f`): 입력 DC 미선언이면 F 밖 입력 포트를 이웃 쌍마다 '같은 DC' 엣지(`input_tie`)로 잇고 그 엣지가 Kruskal 순위 최상위라, 커널이 같은 DC 등식을 실제로 풀었다(§4.7-0 A1, 계획 X-IT1). 옛 문단 전문은 계획 history H2 'IT-1·IT-2 design' 행.
- 개정(정본 = §4.7-1 1~5): 입력 DC 미선언이어도 '같은 DC' 엣지를 G_vgs 에 넣지 않는다. F 밖 입력 포트는 각자 성분의 W4 뿌리 후보로 남고(항목 5 의 뿌리 규칙 그대로), **y 키 = 뿌리 넷**(`INPUT_GROUP_KEY` 없음). 한 성분 안 뿌리가 아닌 입력 포트는 트리 경로(MOS VGS)로 쓰인다. 입력 포트인 W4 뿌리가 둘 이상이면 `unsupported_rule_branch`(rule_branch `input_port_multiple_roots`)로 탐색 전 정지한다(IT-Q1 (나), DEC-76).
- 결과(O-13 (1)): 같은 DC 엣지로 생긴 종속은 0이다. 포트 경로가 둘 이상인 v1 고리는 ΔV를 소거한 KVL 하나가 남아 그 고리 멤버 하나가 `cycle_vgs` 종속이다(파일럿 VGS1a − VGS1b = VGS4a − VGS4b, M1b). 대칭이면 그 등식은 대칭 묶음과 중복이다. 종속 수 = 순환수 불변식은 '같은 DC 엣지 없는 G_vgs(F 한 점)' 기준이다. `input_tie` relation·`TIE_INPUT_ORDER` 기록과 그 어휘는 IT-1이 같은 변경에서 지운다.
- **K-3 축소(X-IT5, 원래 취지와 다름 -- 사용자 결정 O-13 (2) 승인)**: 옛 개정 문언의 '대칭 궤도가 같은 포트들의 y 는 U2 자기동형 묶음(`domain.ties`)이 하나의 변수로 묶는다'(서로 다른 성분 뿌리인 입력 포트의 경우)는 **미구현(발동 0)**이고 그 경우는 정지한다. 발동 회로가 library에 들어오면 그때 구현한다(계획 N6.5 범위 4).
- 영향 확인 대상(card 0 IT-0 M-I1~M-I7, 계획 N6.5 순서 0): 입력 DC 미선언 회로의 종속 소자 목록·W4 뿌리·y 키·θ y 수·층 0 시작점·봉인·결과 JSON 키·입력 포화 창(M-I4: 뿌리 아닌 포트와 뿌리의 전압 차, IT-Q2 판정)·DOF·순환수 = 종속 수(library 9회로). 입력 DC 가 선언된 회로는 입력 포트가 F(W2 `input_dc`)라 이 개정과 무관하다 -- 그때 두 포트를 지나는 고리는 v1 이 아니라 F 경유 v2 와 같은 처리(ΔV = 선언 차)다(계획 DEC-64 v1 'ΔV 는 입력 DC 선언이 있으면 그 차'). 무동작 확인 = library 선언 2회로 쓰기 계획 필드별 동일(M-I7, NFR-4).

**2. 노드 전위(출발 모델)**: 계획 순번대로 쓴다. 고정 = 레일·W3·입력 DC(절대값). MOS writer 는 커널과 같은 역산 `vgs_for_current_density`(ln IDu, L, VDS, VSB). 저항 = 선언값 또는 θ 저항 상자 기하 중심 × KCL 기저 전류. 기하 중심은 순수 함수 하나 `theta_box_centre(domain, component)`(S0 수준 정의역 필드만 읽음)로 두고, 이 절과 `layer0_center._box_centre`가 같은 함수를 부른다(식 중복 없음, 단계 B 의존 없음). W4 창 넷 = 그 넷을 뿌리로 한 **상대 전위**(같은 뿌리끼리의 차만 쓴다 -- y 와 무관). VDS·VSB 는 두 단자 전위가 같은 뿌리로 알려지면 그 차(VSB 는 절대 전위일 때만), 아니면 그 소자의 곡선 동작점(§6.1-6). 1변수 노드(diode gate·소스 추종 source)는 커널처럼 `bracket_root`(창 = 레일 범위, 상대면 아는 쪽 ± 레일 폭). drain 이 뒤 순번에서 쓰이는 writer 가 있으므로 전위 변화가 행 분해능 이하가 될 때까지 바퀴를 되풀이한다(상한 = 넷 수). 봉인 평가를 쓰지 않는다(§0 단계 A 규칙).

**3. 행**(값 ≥ 0 이 만족, 단위 V, 분해능 = 그 소자들의 LUT `tol_vdsat` 최솟값):
- `loop_lo`·`loop_hi`(v2 고리만): 종속 소자 m 의 고리 VGS_m 이 m 의 출발 구간 안 -- VGS_m − VGS(gm/ID_hi,m) ≥ 0, VGS(gm/ID_lo,m) − VGS_m ≥ 0(`vgs_for_gm_id`, 그 점 VDS·VSB). gm/ID_lo,m 은 구간 하한과 최소 폭 하한(§6.5 as-built) 중 큰 값. 종속 소자의 gm/ID 는 고르지 않고 등식이 정한다(DEC-64 '하나의 gm_id 가 종속된다').
- `saturation`: VDS − VDSAT − tol_vdsat ≥ 0(§6.2 와 같은 포화 규칙). VDSAT 는 gate 전위도 알면 그 VGS 점의 LUT 열, 아니면 출발 gm/ID 의 곡선 값. 선형 선언 소자는 제외(봉인 7 제외와 같다).
- `writer_root`: 1변수 노드의 창 안 근이 없거나 writer 역산이 정의되지 않음 -- 값 = −(끝점 |h| 최솟값, 없으면 레일 폭). 커널 `no_root_in_window` 와 같은 사실이다.
행마다 **의존 묶음**(행의 넷을 쓴 나무 경로의 writer 와 자기 소자의 같은 VGS 묶음 뿌리)을 S0 에서 구조로 한 번 정한다.

**4. 공동 선택(7a)** -- 결정론, 상한 있음:
- 선택점(§6.1-7, 최소 폭 보정 뒤)에서 모든 행이 0 이상이면 아무것도 바꾸지 않는다(대부분 회로가 이 경우여야 한다 -- 측정으로 확인).
- 아니면 변수 = 위반 행의 의존 묶음에 든 **writer VGS 묶음**들. 묶음 j 의 gm/ID 는 **자기 구간 [바닥_j, 상한_j] 어디로든** 움직일 수 있다(올림 허용, 사용자 결정 B3; 바닥 = max(구간 하한, 최소 폭 하한)). 정규화 위치 x_j = (g_j − 바닥_j)/(상한_j − 바닥_j) ∈ [0, 1], 출발 = 선택점 위치 x⁰_j. 제약 = 변수에 닿는 모든 행 ≥ 0.
- 목적(기준 = gm/ID 큰 쪽, §6.1-7 과 같다): (i) 위반 최소화(min v, 행 + v ≥ 0, v ≥ 0)로 실행 가능 여부를 정하고, (ii) 가장 낮은 위치 min_j x_j 를 최대화(max-min), (iii) 그 값을 하한으로 고정하고 Σ x_j 최대화. 세 단계 모두 SLSQP, 변수 순서 = 구조 색 순(이름 전단사 불변), FD 스텝 = 사다리 분해능 2^−steps(§6.1-9 의 steps), maxiter = 변수 수 × steps(layer0 `_maxmin` 과 같은 규칙), ftol = 2^−steps. 결과 점에서 행을 다시 잰다(풀이 결과를 믿지 않는다).
- **매크로·면적 재확인(B3)**: 위치를 올린 묶음이 있으면 그 점에서 §6.5 매크로 모델(`current_model` + `macro_solve` **기본 호출** -- 키워드 인자 `node_c`·`gm_bounds`·`gain_targets` 없음, §5.3.6 '기본 호출 불변', 확정 풀이와 같은 설정)과 면적 추정(§6.4-5)을 다시 푼다 -- §6.1-7 의 실행 가능 판정과 같은 식(면적 ≤ 예산, 매크로 근 있음). 실행 불가면 올린 묶음들의 위치 상한을 선택점 위치 x⁰_j 쪽으로 반씩 좁혀(x 상한 = x⁰_j + (상한 − x⁰_j)/2^k) (i)~(iii)을 다시 푼다. k 는 0 부터 steps 까지(상한 steps + 1 회), k = steps 에서 올림이 사실상 없어진다. 매크로 결과가 바뀌면 전류가 바뀌므로 최소 폭 보정(§6.5 as-built)과 행 재측정을 거친다(§6.1-8 의 반복 상한 = 소자 수 안).
- 채택 점에서 종속 소자의 출발 gm/ID 는 고리가 정한 값으로 바꾼다(보고·면적 추정 일관).

**5. 해가 없으면(fail-closed)**: 위반 최소화 결과에서도 행 < 0 이 남거나, 4 의 좁힘을 다 써도 매크로·면적과 행을 함께 만족하는 점이 없으면 `StartConflict(quantity="kvl")`(§6.6)를 남은 행마다 남기고 위반 최소 조합(매크로·면적이 실행 가능한 쪽 우선)을 출발점으로 넘긴다. 다른 경계를 조용히 넓히거나 행을 빼지 않는다.

**6. 적용 위치(배선)**: `start_intervals` 블록의 선택점(사다리 칸 0)과 사다리 아래 칸 각각(칸의 t 위치가 출발, 구간 전체가 정의역). U15 `placer.place`는 덮어쓴 묶음을 고정하고 나머지만 바꾼다(§5.10-3). §6.1-7 의 t 괄호 탐색 안에서는 부르지 않는다(t 를 정한 뒤 한 번). 호출 경로: 단계 A `start_intervals`(7a 포함) -> S0 수준 필드 `start.row`·`start.point`·`graph/start` -> 단계 B `layer0_start` / `layer0_budget` -> `find_front`. 단계 B는 이 필드를 읽기만 한다.

**7. 인터페이스**(S0 수준 필드, 40 §2.4.2·§2.4.8. 묶음 객체 `StartContext`·`StartIntervals`는 없앤다, 40 §2.4.7):
- KVL 모델(쓰기 계획·고정 전위·종속 소자·의존 묶음)은 S0 수준 필드 `graph/start: kvl_model`이다(writer = `start_intervals` 블록, S0당 1회). 쓰기 계획 자체는 sizing 쓰기 계획 블록의 S0 수준 필드를 읽는다.
- 선택점의 행 표 `[{kind, device, value_v, deps}]`는 `graph/start: kvl_rows`, 기록 `kvl_adjusted{groups, min_position}`·`kvl_macro_recheck{k}`·`kvl_unsatisfied{rows}`는 `graph/start: records`(KVL 기록은 U17 ②에서 더한다. U17 ①-b의 `records` = as-built 매크로 모델 기록 -- 40 v1.9.1 D3), 충돌은 `graph/start: conflicts`다. 채택된 소자 gm/ID·L은 `device: start.row`, (VDS, VSB)는 `device: start.point`다.
- `StartConflict.quantity` 어휘에 `"kvl"` 추가. 출처 어휘 `SRC_KVL_LOOP`·`SRC_KVL_SATURATION`.
- 새 파일 `E/search/iv_kvl.py`(진입점 `kvl_model`, 행 평가), `E/search/iv_kvl_choice.py`(진입점 `kvl_choice`, 4·5).
- 재사용: 행 평가는 같은 x 벡터를 한 선택 호출 안에서만 묶는다. 이것은 호출 지역 변수이고 호출 밖으로 나가지 않는다(40 §2.4.10 G-8 허용, 상한 = 그 호출의 평가 상한 maxiter·(변수 수 + 2)). LUT 조회는 LUT memo `memo.call`(40 §2.4.6)이다.

**8. 비활성**: 레일 전위 미선언(`rail_potentials_undeclared`) -- 절대 전위 행 없음(상대 행은 남는다). 저항 전류·값이 없는 넷은 '정해지지 않음'으로 그 넷을 쓰는 행이 생기지 않고 사유 `kvl_node_undetermined{net}` 을 보고한다.

**9. 불변식**: 같은 입력이면 같은 행·같은 선택. 이름 전단사는 행 이름만 바꾼다. 위반이 없는 회로의 출발 θ 는 v1.5 와 비트 동일(1a 커널 개정이 바꾸는 입력 DC 미선언 회로는 개정된 쓰기 계획 기준으로 같은 말).

**10. 계획과의 관계**:
- (P1, 남음) 계획 DEC-71 (7)·N3.7 층 0 은 `kvl_branch` 등식을 **조립 단계**에서 푼다(정밀 경로는 내층 DP 의 W2 블록). 이 절은 같은 등식을 단계 A8 출발 선택에도 건다(사용자 결정 9). 조립의 처리는 바꾸지 않는다.
- (P2, 닫힘 -- B1) 역산 우선(DEC-71 (4)(a))은 층 0 의 몫이고 §6 은 그 정의역(구간)을 준다(위 '층 0 과의 관계').
- (P3, 닫힘 -- B1) VDS 배분(DEC-71 (4)(c))은 층 0 의 몫이고 이 절은 고리가 정한 VDS 만 검사한다.
- (P4, 닫힘 -- B2) DEC-64 v1 은 제약 없음(같은 DC 등식 없음, ΔV 소거 KVL은 남음 -- O-13 (1)). 커널 쓰기 계획을 1a 로 맞춘다(구현 = card IT-1, 계획 N6.5).
- (P5, 닫힘 -- K-1) 공동 선택 기준(위반 최소 -> max-min 위치 -> 위치 합 최대)과 매크로·면적 재확인의 좁힘 규칙(반씩, 상한 steps + 1 회)을 승인했다(사용자 결정 2026-10-12 "K-1~K-3도 권고대로" K-1 "KVL 고리 공동 선택 기준 승인 -- 위반 최소 -> 가장 낮은 위치 최대(max-min) -> 위치 합 최대, ... 그래도 없으면 StartConflict(kvl) 기록 + 위반 최소 조합 전달").
- (P6, 닫힘 -- B3) '낮춤만'·'매크로·면적 재확인 생략' 가정을 없앴다(4 의 재확인).
- (P7, 조건부 닫힘 -- K-2) §7.5 β·C_eff 정의는 "design 검증에서 지적이 없을 때 승인(지적이 있으면 다시 묻는다)"(K-2). design 검증 지적이 나오면 다시 묻는다.
- (P8, 닫힘 -- K-3) 1a 의 `input_tie` 폐기를 승인했다: "입력 DC 미선언 시 입력 포트를 같은 DC 로 묶던 input_tie(U2 기본안 (a)) 폐기, 대칭 포트는 U2 자기동형 묶음(domain.ties)이 대신, 구현 순서는 결정 6(d/s 맞바꿈) 다음"(K-3). U2 기본안 (a)를 대체한다. 구현 = card IT-1(계획 N6.5). '대칭 포트는 `domain.ties`가 대신'(서로 다른 성분 뿌리인 입력 포트)은 미구현(발동 0)·정지로 축소(X-IT5, 사용자 결정 O-13 (2) 승인, 1a).
- (P1, 닫힘) 위 첫 항목. PQ5 결정(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지")으로 닫혔다.

---

## 7. 잡음 경로 (사용자 결정 2026-10-08: "노이즈 spec을 추가해서 코드를 만들어야지.")

잡음 경로를 범위 안에 넣는다. 회로별 값은 사용자 결정 2026-10-08 Q11을 따른다(§7.1). 이 결정에 따라 P N1.2의 잡음 항목과 DEC-96 (3)의 '잡음·왜곡 미검증'은 잡음에 한해 바뀐다(계획서 DEC-96 정정 필요, 사용자 지시). 설계는 topology와 무관하다. 잡음원은 소자마다 붙고, 출력까지의 전달은 MNA adjoint로 계산하며, 회로별 식은 두지 않는다.

### 7.1 spec -- 잡음 제약 metric (닫힌 어휘)

metric 이름은 주파수를 숫자로 고르지 않도록 '평탄값'과 'corner'로 정의한다(근거: `_drafts/engine/noise_spec_proposal.md` §1).

| metric | 정의 | 단위 | 쓰임 |
|---|---|---|---|
| `noise_th_in_v2hz` | 입력 환산 **열잡음 평탄값**. 소자별 열잡음 성분을 전달 뷰의 MNA로 입력에 환산해 더한 값 | V²/Hz | 보고(모든 회로) |
| `noise_fc_in_hz` | 입력 환산 **1/f corner**. 입력 환산 flicker 성분이 열잡음 평탄값과 같아지는 주파수 | Hz | 보고(모든 회로) |
| `noise_excess_th` | `noise_th_in_v2hz` ÷ 입력 소자만의 열잡음 하한(같은 LUT γ). 입력 소자는 S1v에서 gain 제약 전달 뷰의 첫 이득 블록 input 셀로 구조적으로 정한다 | 무차원 | 구조 가드 제약 |
| `noise_out_int_vrms` | **폐루프** 출력 적분 잡음(rms). 선언된 되먹임 β로 루프를 닫은 테스트벤치(§7.3 폐루프 모드)에서 [f_lo, f_hi]를 적분한다 | V | 파일럿 제약 |

**회로별 선언**(사용자 결정 2026-10-08 Q11):

| 회로 | 잡음 선언 |
|---|---|
| current_reuse_telescopic_ota(파일럿) | `noise_out_int_vrms <= 450e-6`(V). 감지 = 차동 출력 v(Vop)−v(Vom)(view 미적음, 기본 포트 뷰), 대역 = 이 절의 적분 대역. 출처: `user_spec`(사용자 결정 2026-10-14 Q-S3, 근거 `_pilot_current_reuse/noise_basis.md` §4(c) C1: SPICE 438.5 µV @ 282 µW) |
| two_stage_ota, two_stage_ota_sf, folded_cascode, ngcc_3stage_ff, nmcnr_amplifier, sf_pushpull_output_opamp, common_gate_amplifier | `noise_excess_th <= 2`(가드: 부하 잡음 ≤ 입력 잡음, `user_spec`). 그리고 `noise_th_in_v2hz`·`noise_fc_in_hz` 보고 |
| pushpull_follower_buffer | 제약 없음, 보고만(이득 ~1 버퍼라 잡음 스펙이 의미가 없음) |

**파일럿 적분 범위**:
- 하한 f_lo = LUT가 실측한 가장 낮은 잡음 주파수 점이다(외삽하지 않는다. 현재 1 Hz).
- 상한 f_hi는 유도한다. 폐루프 최고 극점보다 위에서 로그 격자로 올라가며, 꼬리 상계 PSD(f)·f(1극 이상 감쇠에서 성립)가 분해능²(이 metric의 resolution²) 이하가 되는 첫 주파수에서 멈춘다. 상한은 K_max번 두 배 확장이다.

**공통 규칙**:
- 제약 형식은 `{metric, op: "<=", value, source}`이다. `source`는 필수다.
- MOD5 레지스트리에 `MetricSignature`로 등록한다(`domain: ss`, `view_kind: transfer`).
- 단위 어휘 `v2_per_hz`, `hz`(기존), `ratio`, `v`를 `core/units`에 넣는다.
- 레지스트리 밖의 잡음 이름은 `metric_unknown`으로 거부한다.
- 옛 topology `sizing_roles.metrics.noise_v_rthz`(주파수가 없어 판정할 수 없음)는 새 로더가 읽지 않는다.
- 왜곡은 여전히 범위 밖이다.

### 7.2 LUT -- 소자 잡음 데이터 (PDK BSIM4 잡음 모델에서 특성화)

**모델 사실**(`noise_spec_proposal.md` §0, sky130 모델 카드를 bin 전수로 확인한 값):
- `fnoimod = 1`(unified flicker: NOIA/NOIB/NOIC, EF). 그래서 KF·AF는 쓰지 않는다(카드 값 kf = 0).
- `tnoimod = 1`(holistic thermal). γ는 모델 파라미터가 아니라 바이어스 함수다.
- `ef`: nfet 0.84, pfet 1.0.
- 따라서 γ·K를 상수로 가정하지 않는다. **LUT에서 칸마다 읽는다.**
- EF는 상수를 박지 않고 PDK 모델 카드에서 파싱해 `core` PDK 선언(출처: 파일·sha256·행)에 둔다.

**이미 있는 열**: LUT v2 r2(`lut_v2_location.json`이 sha256으로 고정)에 `SVG2_1HZ`, `SVG2_HF`가 있다. 게이트 환산 V²/Hz이고 각각 1 Hz, 100 MHz 값이다.

**추가 특성화**(사용자 결정 Q11: 저주파 점 추가):
- 100 MHz 점은 fT가 충분하지 않은 칸(긴 L, 약반전)에서 Cgd 피드스루 때문에 게이트 환산값이 작게 나온다. 그래서 중간 주파수 점을 더 잰다.
- 점 위치를 상수로 박지 않는다. 기존 두 점 사이를 로그로 이분해 점을 추가한다. 각 칸에서 아래 '열잡음 평탄값 B 추정' 조건을 만족하는 점이 하나 이상 생길 때까지 반복하고, 상한은 K_max다.
- 측정은 ngspice `.noise`로 한다. 단일 소자 DUT 줄과 include는 생성기와 같다.
- 축 격자는 DC LUT의 (L, VGS, VDS, VS)와 W 슬라이스를 그대로 쓴다.

**분해 규칙**: S_vg(f) = A/f^EF + B로 둔다.
- A = S_vg(1 Hz) − B.
- B(열잡음 평탄값)는 특성화 점 j마다 추정 B_j = (S_j − S_lo·r_j)/(1 − r_j)(r_j = (f_j/f_lo)^−EF)를 구하고, 아래 **두 조건을 모두 만족하는 가장 높은 주파수 점**의 B_j를 쓴다(사용자 결정 2026-10-12 "C-4는 (다)로" (1)).
  - (1) **피드스루**: (2π·f_j·|Cgd|/gm)² ≤ tol_point. Cgd와 gm은 같은 LUT 칸에서 읽으므로 새 상수가 없다.
  - (2) **평탄(plateau)**: j가 가장 낮은 이분 점이 아니면 |B_j − B_{j−1}| ≤ tol_point·|B_{j−1}| + (두 추정의 부동소수 반올림 허용분). 열잡음 평탄값은 주파수와 무관해야 하므로 이웃 점의 B 추정이 일치해야 한다.
  - tol_point = min(그 점의 ln S_vg(f_lo) 면 leave-one-out 오차, 그 셀 tol_a). LOO가 정의되지 않는 점(격자 가장자리)은 tol_a다. B의 주파수를 고르는 데 B의 tol을 쓰면 순환이라 flicker 면의 tol을 쓴다.
  - 근거(2026-10-08 r1 실측): L = 20 µm·약반전(gm/ID 25)에서 입력 환산 잡음이 피드스루 식의 예측보다 훨씬 낮은 주파수에서 1차 저역 통과로 떨어진다. (1)만 쓰면 B를 86 % 낮게 읽고, (2)를 더하면 6 % 낮게 읽는다(1e5 Hz 점). as-built `E/lut/noise_planes.py`가 이 규칙이다(설계와 구현 일치).
- 조건을 만족하는 점이 없으면 그 칸의 B는 '미상'(`no_feedthrough_free_point`)이다. 그 칸을 쓰는 잡음 metric의 resolution을 무한대로 두고 판정을 보류한다.

**칸별 적응 재측정**(사용자 결정 C-4 (2)(3), 구현 단위로 등록):
- 대상: 현 데이터로 B를 확정하지 못한 칸 -- 미상 칸, 피드스루·평탄 판정이 엇갈리는 칸, 계단형 칸.
- 방법: 칸마다 이웃 두 주파수 점 사이를 로그 이분해 새 점을 잰다(ngspice `.noise`, 생성기와 같은 DUT 줄). 위 두 조건을 만족하는 점이 생기면 그 칸은 멈춘다. 상한은 K_max(N3.6 식, 구간 = 로그 주파수 폭)다.
- 저장: 새 버전 noise 파일(`..._noise_r2.npz`, sha256·생성 메타). 기존 r1은 고치지 않는다.
- 시점: graph 재작성 ①~③(40 §11 U17) 다음, U16(9회로 E2E·오라클 대조) 전. 재측정 전 B 오차는 SPICE 오라클 잡음 대조가 잡는다(fail-closed).

**파생량**(읽는 쪽에서 계산하고 열로 저장하지 않는다):
- γ_eff = B·gm / (4kT)
- K = A·W·L(V²·m²): §6.4-3의 1/f L 하한에 쓴다.

**저장**:
- 추가 주파수 점은 **새 버전 파일** `..._noise_r1.npz`에 둔다. sha256과 생성 메타(모델 경로·sha, ngspice 버전, 온도, 코너, 주파수 점)를 함께 기록한다.
- 기존 v2 r2 파일은 고치지 않는다. `lut_v2_location.json`에 새 항목으로 더한다.
- 로더는 v2의 `SVG2_*`와 새 파일의 점을 합쳐 노출한다.
- 잡음 데이터가 없는데 잡음 제약이 선언되면 `SchemaRejectedError(noise_lut_missing)`이다.

**tol**: 칸별 `tol_noise`를 LOO로 계산한다(DEC-87 방법). 디스크 캐시 대상이다(v1.10: 실행 사이 유지, U-87 원래 취지의 예외, 40 §2.4.12 Q9).

**API**(신규): `noise_params(kind, w_key, L, VGS, VDS, VS) -> NoiseParams{A, B, ef, b_status}`. 옛 `SID_1F`는 단위가 잘못되어 있으므로 읽지 않는다.

### 7.3 metrics -- 봉인 스냅샷 잡음 해석 (MOD5)

**잡음원**:
- MOS: gate–source 사이에 게이트 환산 전압 잡음원을 하나 둔다. 값은 S_vg(f) = A/f^EF + B다. 이것을 드레인 전류 잡음 gm²·S_vg로 바꿔 drain–source에 스탬프하는데, 두 방식은 같은 양이다.
- 저항: 4kT/R.
- 값은 봉인 스냅샷 `ss`의 동작점에서 LUT로 읽고 W 배율을 적용한다.
- **포함 범위**(사용자 결정 Q11: CMFB·바이어스 포함): 회로의 모든 MOS와 저항이다. 스위치 kT/C 항은 spec이 `noise_testbench.sampling_caps[]`를 선언한 회로에만 더한다. **파일럿은 선언하지 않는다**(사용자 결정 2026-10-12 "C-2를 네가 확인해" C-2: 논문 Table I 300 µV는 Cadence 폐루프 테스트벤치(C1 = C2 = 500 fF 용량 귀환, CL = 1 pF)의 `.noise` 적분 출력 잡음이고, 기여 상위가 모두 OTA MOS이며 스위치가 없다 -- 판정 = OTA 소자 잡음 적분, 폐루프 귀환 조건).

**폐루프 모드**(`noise_out_int_vrms`, 파일럿):
- 선언된 되먹임 요소(feedback {Cf1, Cf2}, spec)로 루프를 닫는다. Cs는 입력 부하로 남긴다(CI-10 결정). 이 상태에서 출력 잡음 PSD를 구한다. 파일럿은 C-2대로 이 폐루프 조건의 OTA 소자 잡음 적분이 판정량이다.
- **스위치**(선언한 회로만, 현재 library 선언 0 -- 파일럿은 C-2로 선언하지 않음): 스위치 on-저항의 열잡음이 샘플링 커패시터에 남기는 값은 R과 무관하게 kT/C다. 그래서 spec 테스트벤치 선언 `noise_testbench.sampling_caps[]`(as-built 모양 `[{element, source}]` -- 요소는 topology 커패시터, 출력까지의 전달 이득은 엔진이 MNA로 계산하므로 선언하지 않는다)마다 kT/C_s × (그 커패시터에서 출력까지의 저주파 전달 이득)²를 출력 적분에 더한다.
- 이 항을 따로 기록해, 엔진(소자 잡음)과 오라클(스위치 포함 실제 SC 테스트벤치)의 구성 차이가 드러나게 한다.

**전달**: as-built MNA(같은 (G, C) 조립)의 adjoint를 쓴다.
- 출력 감지 노드에서 단위 전류를 주입해 adjoint 해를 한 번 구한다. 그러면 모든 잡음원의 전달 함수 Z_k(jω)를 한 번에 얻는다.
- ω마다 풀이 1회이며, 조립은 다시 하지 않는다(WP-23).

**입력 환산**: S_in(f) = Σ_k |Z_k|²·S_k(f) / |H(jω)|². H는 선언된 전달 뷰의 전달함수(gain metric과 같은 뷰)다.

**산출**:
- `noise_th_in_v2hz` = Σ_k |Z_k/H|²·gm_k²·B_k이다(열잡음 성분만).
- `noise_fc_in_hz`는 입력 환산 flicker 합 Σ|Z_k/H|²·gm_k²·A_k/f^EF_k가 열잡음 평탄값과 같아지는 f다. 1-D 근(`bracket_root`)으로 구한다.
- `noise_excess_th` = `noise_th_in_v2hz` / (input 셀 소자만의 같은 합)이다.
- `noise_out_int_vrms` = √(∫_{f_lo}^{f_hi} S_out df + 스위치 항)이다(스위치 항은 `sampling_caps` 선언이 없으면 0, 파일럿 = 0). 적분은 로그 격자 사다리꼴로 하고, 오차가 분해능 이하가 될 때까지 이분 세분한다(상한 K_max).
- 소자별 기여 표 `noise_contrib[{device|element, thermal, flicker, share}]`를 낸다.

**분해능**: metrics §9와 같은 방식이다. LUT 잡음 열의 tol_noise와 소신호 파라미터 tol이 adjoint 감도를 거쳐 전파된 값을 `MetricResult.resolution`으로 둔다.

**파일**: `E/metrics/noise_sources.py`, `E/metrics/noise_analysis.py`.

### 7.4 search -- 제약 행

다른 ss 제약과 같은 형식이다. 판정 단위는 c = (value − metric)/resolution이고, 풀이 척도는 40 §7.2를 따른다. 외층 전회로 판정 위치(DEC-74)도 그대로다.

### 7.5 출발 구간 -- 잡음

**`noise_excess_th ≤ 2` 가드**:
- 부하 소자 k의 열잡음 비는 (γ_k·gm_k)/(γ_in·gm_in)이다. 이 비의 합이 1 이하가 되도록 부하 gm/ID를 상한으로 둔다(강반전 쪽).
- 매크로 모델(§6.5)의 전류 비로 gm_k/gm_in = ((gm/ID)_k / (gm/ID)_in)·r_k이다. 여기에 LUT γ를 넣어 부하 gm/ID 상한을 역산하고, 그 결과를 §6.3 속도 상한과 교집합한다.
- 헤드룸 하한(§6.2)과 충돌하면 충돌 레코드로 남긴다.

**파일럿 `noise_out_int_vrms`**:
- 폐루프 열잡음 적분은 매크로 근사로 v²_th ≈ N_in·γ_avg·kT/(β·C_eff)·(1 + 부하 비)이다(`noise_spec_proposal.md` §2.2와 같은 꼴, C_eff는 §6.5의 보상 소자).
  - **N_in의 구조 유도**(K-2 **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")): N_in = Σ_in γ_k·gm_k / (γ_avg·G_half). 합은 입력 셀 소자(S1v gain 제약 전달 뷰 첫 이득 블록에서 AC 역할 `input`인 MOS, `noise_excess_th`의 입력 소자와 같은 집합)에 대해서이고, G_half = gate가 한쪽 입력 포트에 닿는 입력 소자의 gm 합이다. γ_avg = 입력 소자 γ의 gm 가중 평균. 예: 차동쌍 2, current-reuse 2, 단일 입력 1. 유도(단일 출력): 입력 소자 k의 입력 환산 열잡음 4kTγ_k·gm_k / G_half²를 더하면 4kT·Σγ_k·gm_k / G_half²이고, 폐루프 잡음 대역 β·G_half/(4·C_eff)(1극)와 출력 환산 1/β²를 곱하면 N_in·γ_avg·kT/(β·C_eff)다. 옛 정의('입력 셀 소자 수')는 입력 소자들이 같은 gm·γ이고 한쪽 포트에 하나씩일 때의 특수형이다. 나머지 β·C_eff·kT/C·1/f 식은 검증 확인대로 승인됐다(같은 결정).
  - 출력 형태: 차동 출력(출력 포트 쌍 Vop − Vom)은 반쪽마다 C_eff·β가 같다는 가정에서 같은 식이다. 이 가정이 깨지는 회로(반쪽의 귀환 C가 다름)의 계수는 K-2 재확인 대상이다(**결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로")(U-70): N_in 구조 유도, 대칭 귀환 Cf1 = Cf2 식, 선언 귀환이 비대칭이면 그 계수를 '추정'으로 표시). gm이 소거되므로, 이 항은 보상 커패시터의 하한으로 작용한다. 하한 = 예산 중 열잡음 몫이 남도록 하는 최소 C_eff다.
- 예산은 나누지 않는다. 총 예산에서 kT/C 스위치 항(선언이 없으면 0, 파일럿 = 0, C-2)을 뺀 나머지를 열잡음과 flicker가 함께 쓴다.
- 출발 단계에서는 둘을 같은 몫으로 시작하고, 판정은 §7.3 전회로 계산이 한다.
- flicker 몫은 §6.4-3 1/f L 하한(입력 소자 W·L)으로 간다.

**1/f L 하한**: §6.4-3.

**β·C_eff 입력 배선(v1.6, 사용자 결정 2026-10-12 "K-1~K-3도 권고대로" K-2 "design 검증에서 지적이 없을 때 승인(지적이 있으면 다시 묻는다)", U13 열린 항목 `feedback_factor_beta_unavailable`·`c_eff_not_a_start_bound` 해소)**: (β, C_eff 노드, 샘플링 커패시터) 묶음은 S0 수준 필드 `graph/start: noise_inputs`다(writer = `start_intervals` 블록, S0당 1회, 40 §2.4.8). U17 ②에서 β·C_eff 계산과 함께 만든다(40 v1.9.1 D3, 근거: 소비자 위치). 새 상수 없음.
- **β**: spec `feedback.elements`(되먹임 소자) 각각의 입력 포트 쪽 단자 넷(authoring `_feedback_cuts`·metrics `noise_plan` 과 같은 절단 규칙)에서, β = ΣC_fb / (ΣC_fb + 그 넷에 닿는 다른 커패시터 값 합 + 그 넷에 gate 가 닿는 입력 소자의 cgg 추정 gm/(2π f_T)). 커패시터 값 = 선언값, engine θ 면 §6.5 매크로 출발값(`cap_values`), 둘 다 없으면 θ 상자 기하 중심(층 0 과 같은 값). 되먹임 소자가 커패시터가 아니거나 절단 넷이 정확히 하나가 아니면 비활성(`noise_feedback_cut_ambiguous`·`noise_feedback_element_unknown`, `noise_plan` 과 같은 사유 이름), `feedback` 이 결정 대기면 `noise_feedback_undeclared`. 입력쌍 차동 회로는 절단 넷마다 β 를 구하고 같지 않으면 작은 쪽(보수)을 쓰고, 그 계수를 '추정'으로 표시한다(비대칭 귀환, U-70 결정 "GQ2, N1, N3, K2 권고대로").
- **C_eff**: 구조 주극점 노드(§6.3 `dominant_node`)의 매크로 모델 노드 용량(§6.5 망 구성: 부하 + 소자 cgg 추정 + 보상 수동소자)에, 그 노드가 되먹임 소자의 출력 쪽 단자면 (1 − β)·ΣC_fb 를 더한 값. 주극점 노드가 정해지지 않으면 비활성(`dominant_node_undefined`).
- **열잡음 C_eff 하한**: v²_th,budget = (V_budget² − Σ_s kT/C_s·(C_s/ΣC_fb)²)/2(스위치 kT/C 항 -- 저주파 폐루프 전달 C_s/ΣC_fb, 남는 몫을 열잡음·flicker 가 같은 몫으로 시작, 위 '예산은 나누지 않는다'), 하한 C_eff,min = N_in·γ_avg·kT·(1 + 부하 비)/(β·v²_th,budget)(N_in은 위 구조 유도). γ_avg = 입력 소자 LUT γ_eff = B·gm/(4kT)(§7.2) 평균, 부하 비 = 위 가드와 같은 Σ(γ_k gm_k)/(γ_in gm_in)(출발점). kT 는 U8 `noise_integral` 과 같은 출처. 주극점 노드의 engine θ 커패시터가 있으면 그 출발값을 하한까지 올린다(값 경계 출처 `SRC_NOISE_THERMAL_C`); 모두 선언값이면 검사만 하고 모자라면 `StartConflict(quantity="capacitance")`. v²_th,budget ≤ 0 이면 `StartConflict`(스위치 항이 예산을 다 씀).
- **1/f L 하한(§6.4-3)**: 출력 flicker 몫 v²_fl,budget(같은 몫) ≥ Σ_in (K_k/(W_k·L_k))·(1/β)²·∫_{f_lo}^{f_cl} f^−EF_k df, f_lo = LUT 최저 잡음 주파수(U8 과 같다), f_cl = β·`gbw_target_hz`(폐루프 대역; 없으면 비활성 `gbw_target_missing`). 입력 소자는 같은 몫(대칭)으로 나눠 A_min = W·L, L ≥ √(A_min·IDu/I).
- 출발값 전용(EP-7), 판정은 §7.3 전회로 `noise_out_int_vrms`.

### 7.6 오라클 -- ngspice `.noise` 대조

- 오라클은 엔진을 import하지 않는다.
- **개루프 metric**(`noise_th_in_v2hz`, `noise_fc_in_hz`, `noise_excess_th`): 같은 free 모드 동작점 테스트벤치에서 `.noise v(sense) <입력원> dec ...`로 잰다. excess는 입력 소자별 기여(`.noise` 소자별 출력)로 계산한다.
- **폐루프 metric**(파일럿 `noise_out_int_vrms`, C-2): 논문 Table I과 같은 조건 -- 용량 귀환 폐루프(선언 feedback Cf1·Cf2, Cs 입력 부하, 부하 CL), CMFB·바이어스 포함, **스위치 없음** -- 의 `.noise` 출력 PSD를 적분한다. 적분 범위는 엔진과 같은 [f_lo, f_hi] 유도 규칙을 따른다(논문에 대역 명시 없음, spec의 대역 정의 유지. 오라클이 독립적으로 계산한다). 샘플링 kT/C는 재지 않는다(`sampling_caps` 선언 회로가 생기면 과도 기반으로 따로 잰다).
- **비교 허용오차**: 다른 metric과 같다. resolution과 `model_error_noise_*`(DEC-72)를 쓰고, 미측정이면 '판정 보류'다.
- **합격**: T5에 잡음 제약을 넣는다. `ORACLE_MEASURES`에 네 metric을 더한다.

### 7.7 상태

7.1~7.6 모두 MISS다. as-built 잡음 관련 코드는 `noise_1f_density`(옛 엔진)가 전부이고, 새 엔진에는 해당 코드가 없다.

---

## 8. 신규 공개 API

```python
def build_s1v(s1: S1, spec: SizingSpec, *, count_budget: int) -> S1v                                   # E/graph/s1v_build.py
def block_local_gain(snap: GraphSnapshot, s1v: S1v, view_key: str, block_key: tuple[str, ...]) -> BlockGain  # E/metrics/block_model.py
def achievability(s0: GraphSnapshot, lut: LutSet, spec: SizingSpec, pdk: PdkDecl, *, count_budget: int) -> GraphSnapshot  # graph/ach 필드를 쓴다(40 §2.4.8), raise InfeasibleTargetError
def start_intervals(s0: GraphSnapshot, lut: LutSet, spec: SizingSpec, pdk: PdkDecl) -> GraphSnapshot  # E/search/start_intervals.py, graph/start·device start.* 필드(40 §2.4.8)
def layer0_budget(ctx: SearchContext, s0: GraphSnapshot, *, count_budget: int) -> BudgetFront   # S0 수준 필드(graph/ach·graph/start·start.*·A9)를 읽는다(40 §2.4.2). 평가 예산·계수는 ctx 실행 계수, r̂는 S3 색인
def block_bounds_l0(s0: GraphSnapshot) -> GraphSnapshot                                           # 신규 A9(§4.2), graph/ach: block_bounds_l0 필드를 쓴다(40 §2.4.8)
# E/search/layer0_inverse.py (§5.3.3~5.3.6): 모듈 진입점 하나(파일당 진입점 하나 규칙)
def layer0_candidate(ctx: SearchContext, s0: GraphSnapshot, job: BlockJob, target_db: float, fixed_fp: str, choice: tuple) -> GraphSnapshot | FailureRecord  # (a)(c)(b)(d) 고정점 -> 국소 봉인 스냅샷
# E/search/l_targets.py (§5.3.7)
def l_targets(s0: GraphSnapshot, owner: str) -> LTargets   # {kind: mirror|replica|signal|other, knee_anchors, window, grid}, knee 는 LUT memo(40 §2.4.6)
def size_and_seal_local(ctx: KernelContext, theta_block, fixed, columns: frozenset[str]) -> GraphSnapshot  # E/sizing/size_and_seal_local.py (국소 스냅샷, 40 §2.4)
def macro_solve(ctx, model, gm_id, lengths, refine=True, *, node_c=None, gm_bounds=None, gain_targets=None) -> MacroResult  # E/search/macro_poles.py (§5.3.6)
def count_budget(lut: LutSet, kinds: frozenset[str], spec: SizingSpec) -> int                           # E/search/count_budget.py  (N_S, §0)
class EvalBudget:                                                                                       # E/search/eval_budget.py  (N_T, §5.8)
    def remaining(self) -> int: ...
def noise_params(kind, w_key, L, VGS, VDS, VS) -> NoiseParams                                            # E/lut/noise_query.py
def noise_analysis(snap: GraphSnapshot, view_key: str, spec_item) -> NoiseResult                         # E/metrics/noise_analysis.py
def mismatch_dvgs(kind, w_key, L, VGS, VDS, VS) -> MismatchSens                                          # E/lut/mismatch_query.py  (§6.4-2b)
def headroom_bound(s1: S1, s1v: S1v, lut: LutSet, spec: SizingSpec, pdk: PdkDecl, *, count_budget: int) -> HeadroomAchievability  # E/metrics/headroom_bound.py (§4.6)
# J 공동분석(§1.12) -- 단위 U1b
def composite_diodes(projection) -> tuple[CompositeDiode, ...]                                        # E/graph/composite_diode.py  {members, reference, cascode_members, walk[]}
def feedforward_cells(model, view, blocks, cells, stage) -> FeedforwardResult                          # E/graph/feedforward_cells.py {main_path, cells[FeedforwardCell], ratio_candidates, findings}
def loop_roles(view_loops, transfer_views, declared_pm_views) -> tuple[LoopRole, ...]                  # E/graph/loop_roles.py  {loop_id, role: loop_view|compensation_internal|composite_diode_internal|bias_scc}
```

`build_s1v`의 as-built 서명(`[u1-sp1]`)은 `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), previous=None, stop_on_unsupported=True)`이다. U1b는 서명을 바꾸지 않는다. 단계 A가 `declared_loop_cuts`와 `structure`를 실제로 넘기도록 호출부를 고친다(40 §3.2-3).

---

## 9. 검증 -- 오라클, test, DoD 명령

오라클 종류(P N0.4): (a) 손계산·불변식, (b) 다른 방법의 참조구현, (c) SPICE, (d) 사용자 선언.

| 항목 | 오라클 | test(신규) | 핵심 단언 |
|---|---|---|---|
| SP1 | (a) 이름 없는 2~4소자 toy, (d) ratified 대조표 | `tests/graph/test_cells.py`, `test_drive_kind.py`, `test_stage_bfs.py`, `test_blocks.py` | 5T: 차동 블록 1, 미러 입력은 내부 노드. 2단: 블록 2. 캐스코드는 같은 stage. 이름 전단사 불변 |
| 루프 | (a) toy, (d) J11 | `test_loops.py`, `test_loop_classify.py` | Miller = (2). CMFB = 포트쌍 대응. 열거 상한 초과 시 정지 |
| 블록 gain·잔차 | (a) CS·캐스코드 손계산, (b) 단일 블록 회로에서 MNA와 비교 | `tests/metrics/test_block_model.py` | 단일 블록 잔차 ≤ 수치 분해능 |
| GB4 | (b) 작은 toy에서 격자 직접 전수, (a) 불가능한 gain 픽스처 | `test_block_gain_bound.py`, `test_achievability.py` | exit 3. 상한 미상이면 판정 없음. 저항이 있으면 전류 축 포함 |
| 면적 하한 | (a) | `test_area_lower_bound.py` | 인증되지 않은 전류 = 0 |
| DOF(IC6) | (a) 사고19 픽스처 | `tests/metrics/test_ic6_dof.py` | over/under 판정 |
| 층 0 | (a) 2블록 toy에서 전수 조합과 비교 | `tests/search/test_combo_dp.py`, `test_layer0_budget.py` | DP front = 전수 front. `gain_budget_db` 출력. override 반영 |
| 층 0 역산(§5.3) | (a) 이름 없는 CS·캐스코드 toy 손계산(목표 gain → L, gm 요구 → gm/ID), 이상 소자 2단 VDS 배분 손계산, (b) 같은 bin 격자 전수 | `tests/search/test_layer0_inverse.py`, `test_l_targets.py` | 역산 L의 국소 gain ≥ T_b이고 한 제조 격자 아래 L은 < T_b. bin 경계 넘는 L 없음. 소자 종류(S 자유·B 제외·F 폴백·kvl 종속, §5.3.3)와 폴백 사유(`no_gm_requirement`·`l_inverse_no_bracket`·`lut_hermite_nonmonotone_cell`). 회차 2 이상 = 미해결 쌍만 재풀이·front 불변 정지(§5.3.2). 국소 결과 = 스냅샷, 조립 = graft(같은 입력 버전 재계산 0). 축소 상한(§4.2) ≠ exit 3 입력. VDS 배분 = 미분 큰 소자부터, 하한 위반 0. 고정점 수렴·NONCONVERGENT(비수축 픽스처). knee = 한계효율 최대 구간 위 끝(손계산 표), 면적 비단조 구간 건너뜀. 이름 전단사 불변 |
| 출발 구간 | (a) 손계산 | `tests/search/test_start_intervals.py` | 필요조건 성질 |
| 매크로 모델 | (a) 이상 VCCS 2·3극점, 캐스코드 노드 포함 | `tests/search/test_macro_poles.py` | UGF·PM 근, 근 없음 기록, 바퀴 수렴. **기본 호출 비트 동일**: 키워드 인자 셋이 None이면 `MacroResult`의 `fp_of`가 bd19cc6 기준 지문과 같다(이상 VCCS 픽스처 + library 매크로 활성 회로). 키워드 인자 호출은 `gm_bounds` 밖으로 나가지 않고 `gain_targets` 블록의 G_i = gm_i/10^{g/20} |
| **축소 격자 전수 대조**(P N3.7 검증, 사용자 결정 2026-10-12 "P-1~P-15까지 권고대로 고쳐" P-9 "9회로 축소 격자 전수 대조 추가(N3.7, NFR-5)") | (b) 다른 모델: 전체회로 MNA를 목적·제약으로 쓰는 축소 격자 전수탐색(P N3.7 "사이징 대상 회로 전부에서 전체회로 MNA를 목적·제약으로 쓰는 축소 격자 전수탐색(다른 모델)과 대조한다") | `tests/integration/test_reduced_grid_crosscheck.py`(slow, 9회로) | 대조량 둘(DEC-77): (i) 축마다(전력·면적) 최적값 차, (ii) 같은 면적 상한 ε에서의 최소 전력 차(= front 점 대조). 각각 ≤ max(그 축의 격자 분해능(면적은 DEC-80), 모델 오차(DEC-72)), NFR-5와 같은 기준. 모델 오차 미측정이면 '판정 보류'. 단계 A·B에서 정지하는 회로(current_reuse·ngcc·nmcnr, P-1 정지 회로)는 그 정지를 기록하고 대조 대상에서 뺀 사실을 보고한다. 축소 격자의 정의는 계획에 없다(§5.12.5 PQ1) |
| 혼재 노드 구동 종류(§1.5-4, C-1 + 보완 (가)) | (a) 이름 없는 toy 셋(source 쪽 소자 drain 레일·gate 신호 노드 / drain 쪽 gate가 신호 노드 / 바이어스 넷), (d) 9회로 발동표 | `tests/graph/test_drive_kind.py`(toy), `tests/integration/test_drive_kind_mixed_9circuits.py` | toy: 첫째 전압 구동(근거 `follower`), 둘째 전류 구동(근거 `cascode`), 셋째 전압 구동. 9회로 발동표(옛/새/근거, 키 (회로, `view_key`, 노드)): 바뀐 키 = sf N910·N1112·N1516 + folded_cascode Vg10이 혼재로 판정되는 모든 뷰(모두 전류 구동)뿐, sf N17·N20 전압 구동 유지, 나머지 회로 무동작. folded_cascode: M8이 stage 시작 셀이 아님(base와 같이 유지, 시작 셀 = M1, M2)을 단언, 그 밖 블록·stage·극점 노드 변화는 기록(Vg10 극점 노드 drive voltage → current 밖이면 실패) |
| `l_owner` 사실(§1.12.5, C-3) | (a) toy 동치류 + 사실 | `tests/graph/test_l_classes.py` | 사실이 있으면 1~4 규칙과 무관하게 사실의 주인, 멤버가 아니면 `structure_fact_mismatch` |
| P-1 정지(§5.3.11 (a)(b)) | (a) 경로 열거 수가 예산 상한을 넘는 toy, Π > N_S toy(N_S 선언값 작게) | `tests/search/test_layer0_budget.py` | 둘 다 `unsupported_rule_branch`로 탐색 전 정지(결정론: 시간 설정을 바꿔도 같은 판정). 좌표 훑기 코드 경로 없음(구조 test) |
| P-1 절단(§5.3.11) | (a) N_S ≥ Π > N_T,i toy(N_T 선언 E_B 작게) | `tests/search/test_layer0_budget.py` | 정지하지 않고 반분 단계 순으로 N_T,i개 평가 후 `layer0_candidates_truncated{block, bin, Π, evaluated}` 기록, 그 블록 front·조합 front '추정' |
| §6.7 KVL 행 | (a) 이름 없는 toy: v2 고리(종속 소자 VGS 구간 밖·안), VDS-1 고리(포화 위반·만족), 1변수 노드 근 없음 | `tests/search/test_iv_kvl.py` | `loop_lo`·`loop_hi`·`saturation`·`writer_root` 행 값과 부호, 의존 묶음, 비활성 사유(`rail_potentials_undeclared`, `kvl_node_undetermined`) |
| §6.7 공동 선택 | (a) 위반 toy, 위반 없는 library 회로 | `tests/search/test_iv_kvl_choice.py` | 7a (i) 위반 최소 → (ii) max-min → (iii) 위치 합. 올린 묶음이 있으면 매크로·면적 재확인과 반씩 좁힘(상한 steps + 1). 해 없으면 `StartConflict(kvl)` + 위반 최소 조합(fail-closed). 위반 없는 회로의 출발 θ가 v1.5와 비트 동일 |
| §6.7-1a 쓰기 계획(card IT-1, §4.7-1) | (a) 입력 DC 미선언 차동 입력 toy, 입력 DC 선언 toy, 두 입력 포트가 서로 다른 G_vgs 성분인 toy -- 기대 writer·종속 분류는 toy 연결에서 손으로 유도(손계산 오라클) | `tests/sizing/test_writer_plan.py` 안 새 test 함수(v1.12: 옛 경로 `test_writer_plan_no_input_tie.py`는 구조 규칙 H 위반이라 바꿈 -- 계획 F-IT4·X-IT3, 함수 이름은 test 주체가 `git grep`으로 겹침 확인) | **red 먼저**(검증자가 격리 복제본 base에서 실패 기록): relation `input_tie` 0, 같은 DC 엣지로 생긴 종속 0 + 종속 수 = 같은 DC 엣지 없는 G_vgs 순환 수(포트 경로가 둘 이상인 v1 고리의 ΔV 소거 `cycle_vgs`는 기대값에 포함), 입력 포트 W4 뿌리 y 키 = 뿌리 넷, 선언 toy 쓰기 계획 = 오라클(base에서도 green), 다중 입력 뿌리 toy = `unsupported_rule_branch`·`input_port_multiple_roots`(base는 정지하지 않음 -- red) |
| §4.7 입력 포트 창(card IT-2) | (a) 입력 DC 선언 toy·미선언 2입력 toy 손계산(선형 감도), 끝 풀이 손계산, red 변형 둘(끝 풀이 실패·`k_max` 소진) | `tests/sizing/test_block_columns.py`·`test_input_window.py`(커널 창·`saturation_window` 새 반환), `tests/sizing/test_window_refine.py`(다듬은 창), `tests/metrics/test_icm_window.py`·`test_icm_front.py`(metric), `tests/metrics/test_ls_swing.py`(입력 칸 삭제 반영) | §4.7-7 K1~K3·R1·R2·M1~M3. `test_input_window.py:300`의 '선언 입력 DC 는 창 사상이 없다' 기대는 '창 있음'으로 바뀐다(계획 N6.6 소비자 표) |
| P-15 섞인 회로 버퍼(§5.1) | (a) 이름 없는 CS + follower toy(rout 선언·미선언) | `tests/search/test_layer0_budget.py` | 버퍼가 면적 bin DP 단계로 들어가고 국소 Z_out ≤ rout인 점만 남음. 미선언이면 그 블록만 무동작 기록, 상수항 사용 |
| 층 0 정의역 상한 A^L0(§4.2) | (a) 축소 축 2~3개 toy 전수 손계산 | `tests/graph/test_structure_tables.py`(S0 표에 `block_bounds_l0` 행·'추정' 표시·축 목록이 실림), `tests/metrics/test_block_bounds_l0.py` | 고정 축 값 = `start.row`·`start.point` 격자 마디, 단계 B 값을 읽지 않음, matching 그룹 축 하나, Π > N_S면 미상, exit 3이 이 값을 읽지 않음 |
| 계수 예산 결정론 | (a) 같은 S0 두 번 | `tests/search/test_count_budget.py` | N_S가 시간과 무관하다. 사이클·Π 결과가 실행 간 같다 |
| 비단조 축 처리 | (a) 비율에 대해 내부 최대가 있는 toy | `test_block_gain_bound.py` | 세분 후 인증, 실패 시 미상 |
| 잡음 LUT | (c) 단일 소자 ngspice `.noise` 칸 중앙 대조 | `tests/lut/test_noise_query.py` | 칸 중앙 오차 ≤ tol_noise |
| 잡음 해석 | (a) 저항 분압·CS 한 단 손계산(4kTR, 4kTγgm), (c) ngspice `.noise` | `tests/metrics/test_noise_analysis.py` | 입력 환산 밀도·적분이 resolution 안. `sampling_caps` 미선언(파일럿, C-2)이면 스위치 항 0 |
| 잡음 출발 구간 | (a) 손계산 | `tests/search/test_start_intervals.py` | 열잡음 gm 하한, 1/f L 하한 |
| mismatch 감도 LUT | (c) 단일 소자 ngspice 섭동(칸 중앙), (c) 소자 쌍 Monte Carlo | `tests/lut/test_mismatch_query.py` | 칸 중앙 오차 ≤ tol_mismatch. `vth0` 성분 = √2·slope 유도값(bin별 slope1 포함). MC σ와 A_eff 식이 MC 표본 분해능 안 |
| matching L 하한·offset 가드 | (a) 손계산 | `tests/search/test_start_intervals.py` | 절대 offset 회로에서만 L 하한 활성, 가드 회로는 부하 gm/ID 상한 |
| 헤드룸 달성가능성 | (a) 이름 없는 follower 스택·두 극성 입력 toy 손계산, (b) 소형 toy 격자 직접 전수 | `tests/metrics/test_headroom_bound.py` | 상한 ≥ 격자 직접 전수 최대 폭. 선언 제약이 인증 불가면 exit 3, 제약 없는 창은 보고만. 최단 L bin에서만 열리는 toy → `icmr_window_short_l_bin` 경고(정지 아님). SP-2 (c) 회로는 y_icm 범위 = 창 |
| 복합 diode(§1.12.1) | (a) 이름 없는 toy: 저항 자기바이어스 캐스코드 기준(MOS 2 + R), 레플리카(MOS 2, 전류원 고정), 단순 diode(무동작), 직렬 노드에 세 번째 전류 단자가 붙은 변형(무동작). (d) 9회로 | `tests/graph/test_composite_diode.py` | 발동 집합·기준/캐스코드 구분. 9회로 발동 = §1.13 실측 집합, 나머지 7회로 0. 같은 gs 묶음 나머지가 바이어스 전류원. 미러 입력 넷 확장. 묶음 내부 사이클은 `composite_diode_internal`, 루프 뷰 0. 이름 전단사 불변 |
| feedforward(§1.12.2) | (a) 이름 없는 3단 toy + 1단 우회 CS + 2단 우회 미러 가지, 우회 없는 병렬 합류 toy(무동작), 블록 내부 노드로 들어오는 바이어스 셀 toy(K8, 무동작). (b) 분해 합성값 A_decomp와 전회로 MNA 비교 | `tests/graph/test_feedforward_cells.py`, `tests/metrics/test_block_model.py` | FF 묶음·탭·merge·B_b. 주경로 블록 사슬. 복합 블록 0. A_decomp 잔차 ≤ 수치 분해능. `ff_ratio_candidates` 보고 |
| 보상 내부 루프(§1.12.3) | (a) 이름 없는 중첩 Miller 3단 toy(`pm_ss_deg` 선언 있음/없음), 순방향 밖 셀이 낀 되먹임 toy | `tests/graph/test_loop_roles.py` | 선언 있으면 루프 뷰 0. 없으면 `undeclared_loop_constraint`(사유 `compensation_internal_needs_overall_pm`). 순방향 밖 셀 루프는 루프 뷰 유지 |
| 루프 극성·L 주인(§1.12.4·5) | (a) DC 사이클 + Cc 사이클 toy, 부호가 다른 DC 사이클 두 개 toy. 주경로 셀과 FF 셀이 같은 L 동치류인 toy | `tests/graph/test_loop_classify.py`, `tests/graph/test_l_classes.py` | 뷰 극성 = DC 사이클 극성. Cc 사이클 `ac_only`. 충돌이면 `loop_polarity_conflict`. 주인 = 주경로 stage 시작 셀(`main_path_signal`). name_order면 review |
| structure 사실 소비(40 §3.2-3) | (a) 사실 픽스처: confirm 일치/불일치/고아, override, stale(rule_hash 다름), 알 수 없는 concept | `tests/graph/test_structure_load.py`, `tests/pipeline/test_stage_a.py` | 일치 → ratified, 불일치 → `structure_fact_mismatch`, 고아 → `structure_fact_orphan`, stale → `structure_fact_stale`, 알 수 없는 concept → `SchemaRejectedError`(**거부 확인**). 단계 A가 spec 루프 선언의 끊는 넷을 `declared_loop_cuts`로 넘긴다(넘기지 않으면 실패하는 red test 먼저) |

**DoD 명령**(`$PY` = `C:\Python314\python.exe`):

```
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q   # slow 포함 판정은 --run-slow
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration/test_structure_tables.py -q  # 9회로 S1v·A_max·Π·인증 비율 표
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration/test_layer0_pilot.py -q      # front 점마다 allocated·realized·잔차
```

`test_structure_tables.py`는 `runs/<run_id>/structure_tables/`에 다음을 쓰고, 9회로 전부 표가 있는지 단언한다(N7).
- 9회로 S1v 표와 분기 발동 기록. 전용 coverage 파일은 만들지 않는다(R7).
- 블록별 GB4 표(블록 키, 격자 곱 Π, N_S, 인증/미상, A_max, b_GB4)
- 회로별 인증 비율(인증 블록 수 / 블록 수)

---

## 10. 상태 요약

| 절 | 항목 | OK | DEV | PART | MISS |
|---|---|---|---|---|---|
| §1 SP1 | 10 | 0 | 0 | 1(1.2 정적 교류접지) | 9 |
| §1.12 J 규칙 | 6 | 0 | 0 | 0 | 6 |
| §2 블록 모델·잔차 | 3 | 0 | 0 | 0 | 3 |
| §4 GB4 | 6 | 0 | 0 | 1(4.1 곡선 분류) | 5 |
| §4.7 입력 포트 창(IT-1·IT-2, v1.12) | 3 | 0 | 1(4.7-1 쓰기 계획: 같은 DC 엣지를 커널이 푼다) | 1(4.7-3 커널 창: `input_window`·`_solve_input_window` as-built, 뿌리만·커널에서 끝 풀이) | 1(4.7-4·4.7-5 다듬은 창 블록·metric 읽기) |
| §5 층 0 | 9 | 0 | 0 | 0 | 9 |
| §6 출발 구간 | 6 | 0 | 0 | 0 | 6 |
| §7 잡음 | 6 | 0 | 0 | 0 | 6 |
