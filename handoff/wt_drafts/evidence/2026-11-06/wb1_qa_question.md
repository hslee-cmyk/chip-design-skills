# WB-1 QA 질문 문서 -- 비기준 폭 슬라이스의 tol_V bin L 방향 항 (A-63 Q-DC3 재검토)

작성: 오케스트레이터(2026-11-06). 재료 = 권고안 `wb1_qa_qb_recommendation.md`(v1 + v2, 작성 = 권고 agent), 분석 `wb1_resolution_slice_analysis.md`(독립 분석 agent), 결정 간 모순 점검 `wb1_qa_qb_contradiction_check.md`(v1 + 재점검 v2, 점검자 ≠ 권고 작성자). 이 문서는 재점검 v2의 고칠 방법 셋(R2-1 구현 꼴, R2-1 판정 자리 둘 표지, R2-3 W_min 지문 근거)을 반영한 최종 질문 문언이다.

## 1. 사실 (원 파일 확인)

- tol_V 셀 = (kind, w_key, L 점, VDS), 앵커 2개 bin 안 L의 tol_V = 양옆 셀 값과 그 bin의 중점 L 방향 값 중 최댓값(계획 P:682, design 40:1453 -- 사용자 확정 정의).
- 검증 중점 표는 kind마다 기준 폭(w_key 1000) 하나뿐이다. 다른 폭은 `lut/midpoint_checks.py:72`가 `width_differs`로 건너뛰고, `with_external(value, None)`(`lut/_helpers_loo.py:131-135`)이 L 항 없이 값을 낸다(오케스트레이터 직접 확인: midpoint_checks.py 60-80행).
- master는 모든 소자를 기준 폭 키로 판정해 이 공백이 드러나지 않았다. WB-1이 소자별 슬라이스로 바꾸면서(`sizing/seal_tolerances.py:31`) 판정에 들어왔다.
- 결과(two_stage_ota 손 봉인 점, 같은 θ): `dc_tol_v` M6 4.49e-3 V → 4.25e-6 V(1/1056), `power_resolution_w` 7.13e-6 → 6.69e-9 W(오케스트레이터가 덤프 `C:/Users/HSLEE/AppData/Local/Temp/la1s_wb1_diag9/dump_7c038c89.txt`에서 직접 확인). 봉인 1·2·3·8 문턱, SCC 수렴 tol, b_P, 정규화 제약 행이 모두 약 1/1000로 바뀐다 → 출발 점 gbw 행 c +0.0555 → −330, `converge` 거부(two_stage_ota 실경로 test 4건 red; master에서는 같은 test 7 passed, 오케스트레이터 실측).
- A-63 Q-DC3(D41:1751)의 원 근거: (가) 비용 -- 슬라이스별 중점 생성 비용·LUT 적재 순수성, (나) '중점 미검증 표지, 판정 불변'. (나)가 실측으로 틀렸다(판정이 ×1/1000으로 바뀜). (가)는 유지된다.
- 물리 실측(권고 agent): 폭을 바꿔도 L 보간 오차는 같은 자릿수(mV)다. ngspice 중점(L = 1.75 µm, bin (1.0, 2.0]): nmos 0.42 µm 1.513e-2 대 기준 1.596e-2 V(VDS별 0.95~1.44배), pmos 0.55 µm 8.61e-3 대 8.43e-3 V(0.98~1.09배). LUT만으로 앵커 3개 이상 bin LOO 폭별 비: 0.58~2.25배. 1/1000로 줄어드는 폭은 없다.

## 2. 질문 QA1 -- 비기준 폭 슬라이스 tol_V의 L 방향 항

| 안 | 내용 | 물리 정합 | 비용 | ⚠ |
|---|---|---|---|---|
| **A (권고)** | 슬라이스마다 앵커 2개 bin 중점을 생성해 P:682 정의를 그대로 채움 + 중점이 없는 칸은 fail-closed | 맞음(정의 그대로) | 데이터 생성 1회(DC 슬라이스 생성기 조합당 0.4~0.5 s 실측, 120조합 ≈ 1분; 기준 생성기면 직렬 ≈ 90분) + 엔진 card 하나 | 새 card 2개(LM-1d 데이터, LM-1e 엔진), ngspice 데이터 생성은 O-229 2·O-232 허용 목록 밖이라 이 질문으로 승인받음 |
| B | 기준 폭 중점 값을 비기준 슬라이스에 선언 차용 | 조건부(자릿수만 맞고 상한이 아님: 최대 1.44배(ngspice)·2.25배(LOO) 과소) | 작음 | ⚠ 정의 변경 + 과소 허용(O-240 '수치 자기 정합 허용'의 정의를 바꿈) |
| C | 중점이 없으면 셀 정의 불능(fail-closed)만 | fail-closed | 작음 | ⚠ 출발 점 층 0 55/60 소자·6/6 회로, 손 봉인 점 7/7이 E-0 실패 → 탐색 불능 |
| D | 현행 유지(표지만) | 틀림(정의 항 부재를 0으로, 없는 정밀도 주장) | 0 | ⚠ 원칙 1·2·10 위반 |

A의 구현 꼴(재점검 v2 R2-1 반영): `with_external`은 그대로 두고, 표 구성 단계에서 bin 상태가 `missing_external`(앵커 2개 bin인데 그 폭 중점이 없음, 상태는 `lut/_helpers_loo.py:82`가 이미 냄)인 앵커 행만 None으로 만든다. 앵커 3개 이상(computed)·1개(single_point) bin은 지금처럼 셀 값을 낸다 -- 그래서 기준 폭만 쓰는 경로의 거짓 거부가 없다. None 셀은 기존 판정 자리 둘로 간다: 봉인 항목 = P:663 봉인 10행(tol_V 셀 정의 불능 = E-0 정의 불능, O-210 RR-7) → `seal_undefined`; SCC 순환 수렴 = `block_dc` `tol_v_undefined` 실패 레코드(O-240 '순환 수렴'). 둘 다 fail-closed이고 design에 두 갈래를 적는다. 새 사유 이름 0. 중점이 없는 toy LUT의 영향은 LM-1e card에 적는다.

순서: W_min 하네스 정정(A-129, 커밋 `3397b834` 됨) → LM-1d 데이터 생성 → LM-1e 엔진(적재·가드, ngspice 0) → WB-1 병합. LM-1e 고칠 자리(점검자 grep): `lut_set` 중점 표 적재·`MidpointTable` 키, `midpoint_checks:72`, `tolerance`·`vdsat_tolerance` 표 구성, 위치·지문 파일, WB-1 card spec :39·:73·:253·:276, interface :311, 소비자 `lut/CONTRACT.md`·`search/find_front.py`·`tests/lut/test_midpoint_checks.py`·`tests/search/test_find_front_notes_bins.py`, A-110 낡은 구절 무효 표지.

조건부 표지: 'LM-1 뒤 잔차 수 % 이하는 분해능 아래로 들어간다'(권고 V2-1.2)는 tol_I가 노드 전류의 약 13 %인 사실에 기대며, 이는 열린 결정 Q-T0(P:1224, LA-1 측정 시점) 그 자체라 조건부다.

## 3. 함께 알리는 것(질문 아님)

- **W_min**(A-129, 위임): test 하네스가 `LutSpec.min_finger_w_m`을 LUT manifest 최소 폭(0.36 µm)으로 채워 PDK 선언(difftap, 0.42 µm)보다 좁은 손가락이 뽑혔다(층 0 7/60 소자). 하네스 19곳을 PDK 선언으로 바꿨다(`3397b834`). 재점검 v2 R2-3: LUT 지문(`lut/fingerprint.py:18-36`)에 `min_finger_w_m`이 없으므로, W_min에 기대는 파생값의 memo·U-87 캐시 키에 W_min이 들어가는지 확인을 LM-1e 완료 조건에 둔다.
- **QB 슬라이스 선택 규칙(O-173 상정 C1·P:305 '잔차 최소')**: 7/13 회로 실측에서 네 후보(현행·넓은 우선·같은 W bin 안 잔차 최소·연결 묶음 공유) 모두 모순이 남아 지금은 권고 없음. 현행 결과는 µV tol과 엉켜 비교가 공정하지 않다. QA·W_min 뒤 같은 스크립트로 다시 재고, LM-1e 뒤·WB-1 병합 전에 권고 없는 선택지로 묻는다(기준선을 두 번 잡지 않는 순서, 재점검 v2 R2-2 (b)). 현행 R0로 병합해도 물리 관문 완화는 아니다(점검자 판정) -- 다만 정합 묶음 3/23만 같은 W bin인 것은 '알려진 설계 품질 결함, 질문 대기'로 기록하고 통과로 세지 않는다.
- WB-1 병합은 QA 답 전까지 보류한다. two_stage_ota 출발 점 재조정은 QA 결함을 가리므로 보류한다.

## 4. 질문 문언

**QA1**: "WB-1에서 소자별 폭 슬라이스를 쓰자 기준 폭이 아닌 슬라이스의 tol_V에서 bin L 방향 항이 빠져 판정 분해능이 약 1/1000이 됐습니다(원 결정 A-63 Q-DC3의 '판정 불변' 전제가 실측으로 틀림). 어떻게 할까요?" -- 선택지 A(권고: 슬라이스별 중점 데이터 생성 card LM-1d(ngspice 1회) + 엔진 card LM-1e(빈 칸 fail-closed), 그 뒤 WB-1 병합), B(기준 폭 값 차용 ⚠ 최대 2.25배 과소), C(빈 칸 fail-closed만 ⚠ 탐색 불능), D(현행 ⚠ 정의 위반).
