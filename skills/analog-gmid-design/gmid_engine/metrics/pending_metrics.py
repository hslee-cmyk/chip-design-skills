"""계산 대기 metric 서명 표 -- 서명만 있고 계산은 아직 없는 닫힌 어휘 (설계 40 §3.8-8, 41 §7.1, 단위 U5).

공개 정의 0(상수 표, 구조 규칙 A 통과). `catalog.metric_catalog()` 가 이 표를 레지스트리 서명과 합쳐 spec 로더에 주입한다
-- 그래서 spec 이 이 이름의 제약을 선언할 수 있다(로더는 `metric_unknown` 으로 거르지 않는다).

**계산 대기 표시**: 이 이름은 `metric_registry()` 에 **없다**(결과 형식·필드가 없다). 따라서 평가 경로는 이 이름을 측정하지 못하며
조용히 통과시키지 않는다 -- `search.search_context` 가 판정 제약 중 카탈로그에는 있고 레지스트리에는 없는 이름을
`constraint_notes` 에 verdict `unmeasured`·사유 `metric_computation_pending` 으로 기록한다(보고에 드러난다). 주의: 이 기록은 점마다
front 를 거르는 행이 아니다(레지스트리 밖 제약의 기존 처리와 같다) -- 계산이 들어오기 전에는 이 제약이 합격을 막지도 허락하지도 않는다고
읽어야 한다. 계산을 구현하는 단위(offset·스윙 = U7)는 그 metric 의 행을 이 표에서 지우고 `registry._ROWS` 에 계산 필드와 함께 옮긴다(서명은 같아야 한다).

[U7] offset_in_sigma_mv·offset_excess·offset_sys_mv·mirror_ratio_sigma_pct·swing_out_v·icmr_v·icm_margin_v·ff_gm_ratio 8행은 계산이 들어와 `registry._ROWS` 로 옮겼다(서명 동일) --
잡음 4행(U8)도 옮겨져 이 표는 비었다(계산 대기 이름 없음). 아래 뜻풀이는 옮긴 행의 정의 출처 기록으로 남긴다.

행 = (metric 이름, 단위, 영역, view_kind, objective_axis). 이름 정의·쓰임은 설계 40 §3.8-8 표(offset·미러비·스윙·ICMR)와 41 §7.1 표(잡음).
* offset_in_sigma_mv / offset_excess / offset_sys_mv: `dc` 영역 [IT-2d relabel, 옛 ss], `transfer` 뷰(gain 제약 전달 뷰의 A_dm 으로 나눈다).
* mirror_ratio_sigma_pct: `dc` 영역 [IT-2d relabel], matching 그룹별 보고 metric -- 뷰를 받지 않는다(설계 표의 `ratio` 는 '전류비'이지 `ratio` 뷰({num, den})가 아니다).
* swing_out_v / icmr_v / icm_margin_v: DC 양이라 `dc` 영역(O-112, IT-2d; 옛 `ls`), 뷰 없음(출력·입력 포트는 topology ports 에서 읽는다). offset·미러비도 `dc` 로 relabel.
* ff_gm_ratio: ss 영역, `transfer` 뷰(40 §3.8-8 표 'ratio / ss / transfer'). feedforward 묶음마다 r_ff = G_ff / gm_in(B_b)(41 §1.12.2-5), 묶음 없는 회로는 값 없음 -- 계산은 U7.
* [U8] noise_* 4개는 계산이 들어와 `registry._ROWS` 로 옮겨졌다(서명 그대로: ss 영역, `transfer` 뷰 -- 41 §7.1 '공통 규칙'. `noise_out_int_vrms` 의 폐루프 β 는 spec feedback 에서 유도한다, 뷰에 적지 않는다).
"""

PENDING_METRIC_ROWS = ()
