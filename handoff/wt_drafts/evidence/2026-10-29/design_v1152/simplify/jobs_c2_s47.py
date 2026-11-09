# 2차 단순화 커밋 2 -- 41 §4.7 재작성(4.7-V 대체 표 정본, 대체 표지 옛 본문·폐지 기록·옛 멈춤·후속 정정 목록 → design 이력)
S = "C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/v1152/"
cfg = open(S + "l698cfg.txt", encoding="utf-8").read()
OLD_AX = "**축**(graph 규칙 3, gap G2): cfg `tol_v`는 커널 판정 tol(`Window.tol_v` -- 그 해의 소자 tol_V 셀 최솟값, 4.7-3 5)과 같은 정의(점만 봉인점)이고, 봉인 1의 노드 tol(Q-N3 -- 노드에 닿는 MOS tol_V 최솟값)과는 다른 축이다(소자 전부 대 그 노드에 닿는 소자)."
NEW_AX = "**축**(graph 규칙 3, gap G2): cfg `tol_v`(봉인점 소자 전부의 tol_V 최솟값)는 봉인 1의 노드 tol(Q-N3 -- 노드에 닿는 MOS tol_V 최솟값)과 다른 축이다(소자 전부 대 그 노드에 닿는 소자)."
assert cfg.count(OLD_AX) == 1
cfg = cfg.replace(OLD_AX, NEW_AX).rstrip()

H = "design 이력 "
JOBS = [
 dict(id="H41-01", file="41", title="§4.7-V 머리 표지 문언", mode="sub",
      old="이 절 4.7-1~4.7-7 가운데 아래 자리는 이 표가 정본이고 본문 옛 문언은 기록이다 -- 본문 각 자리에 '(v1.15.2 대체 -- 4.7-V)' 표지)",
      new="이 절 4.7-1~4.7-7 가운데 아래 자리는 이 표가 정본이고 본문 해당 자리는 이 표를 가리킨다 -- 옛 문언 = " + H + "H41-02~H41-08, `gain-budget-gmid-sizing.design.history.md`)"),
 dict(id="H41-02", file="41", title="§4.7-1 4 다중 입력 뿌리 정지(옛 문언, 4.7-V 1행으로 대체)", mode="lines",
      start="4. (v1.15.2 대체 -- 4.7-V: DEC-106 입력 점", end=None,
      new="4. **다중 입력**: 4.7-V 1행이 정본(DEC-106 입력 점, 그 밖 다중 입력 = 탐색 전 정지 `input_cm_undefined`; 옛 `input_port_multiple_roots` 문언 = " + H + "H41-02)."),
 dict(id="H41-03", file="41", title="§4.7-2 `node.dc_window` 행(옛 문언, 4.7-V 2행으로 대체)", mode="lines",
      start="| `node.dc_window` | **(v1.15.2 대체", end=None,
      new="| `node.dc_window` | **θ y 범위 = KVL 순서 창**(4.7-V 2행 -- θ 변수 W4 뿌리 y의 범위, 설계점 질문이라 θ 고정, DEC-103; 상태 칸 없음). **항목 = W4 뿌리만**(입력 점 뿌리 포함 -- O-109 D1·DEC-106) | `dc_columns`(노드 풀이 블록) | 평가 커널(모든 평가, FD 열 포함) | 커널 탐색 `fd_jacobian` y 스텝(W4 뿌리만, 4.7-6) -- 값 독자는 이것뿐이다(계획 N6.6 범위 1, O-58 S-1); `icm_config`는 이 필드를 읽지 않는다(D2) | IT-2b가 넓힌 범위('모든 입력 포트와 W4 뿌리')를 IT-2c가 W4 뿌리로 되돌린다: 뿌리 아닌 입력 포트·입력 DC 선언 포트·F 성분 미선언 포트 항목 삭제(D1, 4.7-3 2·3) |"),
 dict(id="H41-04", file="41", title="§4.7-2 값 형식 첫 항목(옛 커널 상태 칸 문언 포함 원문)", mode="lines",
      start="- (v1.15.2 대체 -- 4.7-V: `node.dc_window`의", end=None,
      new="- `node.dc_window` = `Window(lo, hi, constraints)`(상태 칸 없음 -- 4.7-V 2행; `constraints` = 순서 제약 수). " + cfg + " (옛 커널 상태 어휘·`tol_v` 문언 = " + H + "H41-04.)"),
 dict(id="H41-05", file="41", title="§4.7-2 예시 리터럴(옛 커널 뿌리 예시)", mode="lines",
      start="- 예시 리터럴(test 작성용; v1.15.2", end=None,
      new="- 예시 리터럴(test 작성용): 커널 뿌리 `Window(0.31, 1.12, 2)`, cfg 포트 `Window(0.33, 1.18, 0, input_status=\"measured\", tol_v=1.2e-4)`."),
 dict(id="H41-06", file="41", title="§4.7-3 1 뿌리 A6 되풀이·판정 tol·A6 b 도달 조건(옛 문언, 4.7-V 2행으로 대체)", mode="lines",
      start="1. (v1.15.2 대체 -- 4.7-V: 뿌리 창 = 순서 창", end=None,
      new="1. **뿌리**(입력 DC 미선언, 4.7-1로 최대 하나 -- 입력 점 포함): `node.dc_window` = KVL 순서 창(4.7-V 2행; 되풀이·`k_max`·`_interior_solution`·상태 칸 없음). metric은 측정 구성 판정 창 `node.dc_window_cfg`(4.7-3b)를 읽고 그 블록은 `node.dc_window`를 읽지 않는다(사용자 결정 O-109 D2 -- 설계점 질문의 결과가 섭동 질문 metric을 정의 불능으로 만들지 않는다, DEC-103). 포화 밖 점은 봉인 7이 거부한다. (옛 A6 되풀이·판정 tol·A6 b 도달 조건 = " + H + "H41-06.)"),
 dict(id="H41-07", file="41", title="§4.7-3 4 커널 측정 실패(옛 문언)", mode="lines",
      start="4. (v1.15.2 대체 -- 4.7-V) **측정 실패**", end=None,
      new="4. **측정 실패**: 커널 입력 창 측정이 없으므로(4.7-V 2행) 커널 쪽 대상 없음. 측정 구성 판정 창의 자기 측정 실패는 4.7-3b가 `\"unmeasured\"`로 쓰고 metric 정의 불능(N3.14). DE-1 범위 2 '선형 감도 연립 특이 fail-closed'의 나머지(일반화된 끝점 블록의 결측 사유 기록 칸, 출력 창·방향 전류까지 같은 규칙)는 DE-1 몫이다."),
 dict(id="H41-08", file="41", title="§4.7-3 5 커널 `tol_v`(옛 문언)", mode="lines",
      start="5. (v1.15.2 대체 -- 4.7-V: 칸 삭제)", end=None,
      new="5. (삭제 -- `node.dc_window`의 `tol_v` 칸 없음, 4.7-V 2행; metric 분해능은 측정 구성 판정 창의 `tol_v` -- 4.7-2·4.7-5; 옛 문언 = " + H + "H41-08.)"),
 dict(id="H41-09", file="41", title="§4.7-1a 출력 구조 분류 필드 -- 폐지 기록 전문(머리·취소선 본문 S-OS1·S-OS2·test)", mode="lines",
      start="**4.7-1a 출력 구조 분류 필드", end="**4.7-3b ICMR 측정 구성",
      new="**4.7-1a 출력 구조 분류 필드 `node.dc_output_structure` -- 폐지**(계획 v6.34 N3.8 '출력 구조 분류 -- 엔진 필드 없음', 사용자 결정 O-109 D4 -- **원래 취지와 다름, 승인 O-109**; 멈춤 S-OS1·S-OS2와 그 code는 O-109·O-115로 소멸): 측정 구성 감도(4.7-3b)와 출력 스윙(DE-1 (b), O-109 C3)이 두 출력 꼴에서 같은 KCL 계라 구조별 갈래가 없다. **IT-2c 변경에서 지우는 것**(재작성 범위): `E/sizing/writer_plan.py`의 WRITES `(\"node\", \"dc_output_structure\")`·`_output_structure` 함수·그 호출과 그것만 쓰는 F′ 지역 값(`fixed_prime`)·머리 설명; `E/sizing/s2_values.py`의 `OUTPUT_HIGH_IMPEDANCE`·`OUTPUT_KVL_FIXED`와 `DC_WRITES` `DC_WRITER_PLAN_WRITER` 행의 그 원소; `E/sizing/CONTRACT.md`의 그 문단·소유표 행; `E/_module_map.py` 책임 문장의 그 구절; 그 필드를 단언하는 test(기대 갱신은 test 작성 주체 몫). 13회로 분류표(O-66 (1))는 회로 해석 기록이고 엔진 기준선이 아니다. 정지 회로 처리는 쓰기 계획의 기존 정지 그대로다. 옛 설계 기록(v1.12.2~v1.12.11 취소선 본문·줄 위치) = " + H + "H41-09.\n"),
 dict(id="H41-10", file="41", title="§4.7-3b 옛 멈춤 기록 S-1~S-3(O-58 결정 전 문언)", mode="lines",
      start="- **옛 멈춤 기록**(O-58", end="**4.7-3c graph 스냅샷",
      new="- 옛 멈춤 S-1~S-3(O-58 결정 전 문언, servo O-115로 대상 소멸) = " + H + "H41-10.\n"),
 dict(id="H41-11", file="41", title="§4.7-4 모듈 수준 이름(옛 커널 `k_max` import 문언)", mode="lines",
      start="- 모듈 수준 이름(장애 주입 지점)", end=None,
      new="- 모듈 수준 이름(장애 주입 지점): `window_refine.py` 주입 지점은 없다(파일 없음 -- v1.13.0). 커널 `k_max` import·주입 지점은 커널 되풀이와 함께 범위 3a에서 삭제(4.7-V 2행)."),
 dict(id="H41-12", file="41", title="§4.7-4 5 호출 자리와 배선(옛 삭제 항목 줄별 문언)", mode="lines",
      start="5. **(삭제 -- v1.13.0, O-109 C1) 호출 자리와 배선**", end="6. **(삭제 -- v1.13.0)**",
      new="5. **(삭제 -- v1.13.0, O-109 C1) 호출 자리와 배선**: 다듬은 창 실행 배선(`refine_front_windows`, 수락 반복 `accept`·`find_front` 배선, FD 열·커널 평가 제외 조건, perf 칸 `window_end_solves`, 층 0 front 후보 점 호출 자리 -- card LA-1 범위 12)은 만들지 않는다 -- `E/search/slsqp_outer.py`·`E/search/find_front.py` 변경 없음. front·보고 값(층 0 front 후보 점 포함) = 그 점 커널 평가 스냅샷의 `metrics_aux` 입력 CM 세 metric(= `node.dc_window_cfg`에서 낸 값, 추가 호출 0); 운반자 = `_point_record`의 `snapshot_ref`·`snapshot_fp`(EO-1의 oracle 입력 생산자·U16 보고서가 읽는 자리; run 레코드 형식 불변). 측정 구성 블록·`ss_nodal`의 재사용은 graph reuse·S3 graft뿐(4.7-3b, NFR-2·DEC-83 -- 새 캐시 없음); parent → child 파생 규칙(4.7-3c)은 그대로이고 봉인 뒤 블록 필드는 child에서 지워진다. 새 블록 `ss_nodal`·`icm_config`는 블록 계수(`perf.blocks`·`block_computes`, `RunCounters`)에 행이 생긴다(WP-10 비용 보고). 옛 줄별 문언 = " + H + "H41-12."),
 dict(id="H41-13", file="41", title="§4.7-9 옛 결정 대기 D1~D6", mode="lines",
      start="- **옛 결정 대기 D1~D6", end=None,
      new="- O-49 P2 → 4.7-3 2 포트 창 규칙, P3 → 4.7-3 3 묶음(X-IT11) -- 둘 다 측정 구성 판정 창; P1·P4·P5·P6은 대상 소멸(O-109). 옛 D1~D6 경위 = " + H + "H41-13."),
 dict(id="H41-14", file="41", title="§4.7-9 옛 멈춘 항목 S-1~S-4·T-1 머리 문장", mode="sub",
      old="- **옛 멈춘 항목 S-1~S-4·T-1**: 사용자 결정 O-58·O-59 (1)(2)와 계획 v6.21(사용자 O-60 승인)로 이 판에 설계됨 -- 4.7-3b(S-1~S-3)·4.7-3a 2(S-4 두 갈래)·4.7-3a 1 (나)·3(T-1)·4.7-3c(스냅샷 파생 규칙). ",
      new="- (옛 멈춘 항목 S-1~S-4·T-1은 O-58·O-59로 설계됨 -- " + H + "H41-14.) "),
 dict(id="H41-15", file="41", title="§4.7-9 다른 계획·문서의 후속 정정 목록", mode="lines",
      start="- **다른 계획·문서의 후속 정정**", end=None,
      new="- 다른 계획·문서의 후속 정정 목록(helper 이동에 따른 경로·줄 번호 변경 -- 각 문서가 자기 개정에서 고침) = " + H + "H41-15."),
]
