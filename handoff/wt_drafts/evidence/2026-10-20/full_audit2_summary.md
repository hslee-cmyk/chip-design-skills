# 2차 전체 정합 검증 결과 요약 (2026-10-20, 감사 A 원칙별·1차 닫힘 + 감사 B 층·계획 교차)

대상: gain-budget v6.19 `81fc49a7`(gb), oracle v0.6.9 `63a69d17`(op), headroom-chain v0.7.6 `7706d6a9`(hc), graph-consumption v0.11 `aabc5d90`(gc). 줄 번호는 이 판 기준. 감사 사본: scratchpad `full_audit2_A/`, `full_audit2_B/`. 사용자 결정 O-45(U1~U3).

## 사용자 결정 (O-45)
- U1 (B-H1·A-N4) EO-1 완료 (1)이 G-18 확장 칸(OP-5·HC-O 담당) 요구 → EO-1 = OP-3 스키마 칸까지, 확장 칸은 OP-5·HC-O 병합 때 생산자 갱신(U-6).
- U2 (B-M1) oracle 합격 판정 '꺼짐' 둘(gb DEC-90 (1) 289행·N3.6 (ii) 495행·T4 1190·1205행 ε=1 대 op 401행 OP-5 봉인 9 식) → 봉인 9 식 통일, DEC-90 개정(원래 취지와 다름 승인), op X 행 추가, hc 371행 인용 교체.
- U3 (B-M5·A-N6) 계통 offset 판정 실현 W는 단위 9 뒤에만 → 단위 9 전 sizing W(T4-pre 기하), 뒤 실현 W 재판정, 위반 점 fail-closed front 제외·재필터·기록.

## 원칙 기본안 (gb 중심)
- A-N1 [중대] 계통 offset 계산법 0(DE-1 (c) 1551·범위 3 1554·완료 1 1564행이 DC 극한 A_dm 나눗셈을 '범주 오류'로 삭제; 575행은 같은 계를 σ에 씀; offset_systematic.py:6, offset_analysis.py) → DE-1 (c)·범위 3 = 'front 판정 W 봉인점 DC 방정식 1차 감도(출력 오차 ÷ DC 극한 전달), 1차 표기(O-43 D1 (a))', 삭제는 커널 호출만, 완료 1 grep은 ls_swing 한정, DEC-67 'AC MNA 이득 나눗셈' 예시를 '0이 아닌 주파수 .ac 이득'으로, DEC-23 223행 문언도 1차 DC 감도로(B-L5). 고친 문언 사용자에게 보고.
- A-N2·B-N1·N2·M3·M8 창 필드: metric 값 = `node.dc_window_def`, 선언 제약 = +tol 창(별도 행 이름), IT-2(1455·1456·1463행) 'DE-1 전 한정' 표시·'필드 둘' 머리 정정·변경 종류(동작 변경), DE-1 범위에 `_def_refined` 끝 풀이 기준을 정의(tol 없음, 전도 끝)로 전환 + red test, red (ii) 전도 끝 toy 성립 조건(θ 고정 선형 감도에서 전도 끝은 I_off 증가로만 -- 전류 조향 꺼짐은 표현 불가) 명시, A-N11 red (i) 'VDS 여유가 tol_VDsat만큼 다른 점'.
- A-N3 'front 판정'(IT-2·DE-1) = DEC-98 oracle 대조·보고(합격·불합격 아님), DEC-74와 정합.
- B-H2·A-N4 EO-1 입력 출처 = 봉인 스냅샷·spec 선언·LUT 파생표 참조(사본 없음); tol_V 열은 `tol_v_table(kind,w_key)` L 고정 VDS 열(동작점 스칼라 `device.dc_tol_v`와 구분, seal_tolerances.py:29).
- A-N5·B-L6 훑기 점 ε의 gm/ID·tol_V도 그 점 값(tol_V = 그 점 VDS의 LUT 셀) -- gb N3.8 553행 정의 소유자에, DE-1 (a) 인용; op는 인용.
- B-M2·A-N12 ME-1 선행에 metric 코드를 바꾸는 card(DE-1·NL-1·UB-1·IT-2), 모델 오차 측정 주체 = ME-1 하나(DE-1 완료 4 위임).
- B-M4 '사다리·상자 중심·Halton = 무동작 회로 + 층 0 조립 실패 경로(LA-Q2 (b))'(LA-1 범위 6 1689·DEC-73 (3)(b) 272·hc 154).
- B-M6 LA-1의 FX-1 선행 근거 = 파일 겹침(1735 vs 1595).
- B-M7 R-1′ 거르기는 그 점 자신의 (VDS, VSB)로 항 평가(LA-1 1694, hc 238·240·257).
- B-M3·B-L8 HC-1 SPICE 다리가 HC-O에 걸림 명시(hc), HC-1 다리 분류 재확인(정의역 게이트 거부가 통과·거부를 바꿀 수 있음).
- A-N7·B-N3·L3 슬루 문언 'DC 끝점 전류 ÷ C'·'DC 끝점 해·끝 풀이 fail-closed'(90·264·266·416·547·571행) → 기저 θ 전류 합 '추정'.
- A-N8 표기 체계: '손계산(정확도 SPICE 검증)'(상위)과 '1차'·'추정'(하위) 관계 한 줄(gb 264, hc 339).
- A-N9 EO-1·VB-1 착수 조건에 design 단계(design 41 U17 ② 분할, design 40 §3.8-8).
- A-N10·B-L7·L11 다리 상태 어휘(N6.3 두 상태만, 'SPICE 다리 없음' 정리), 변경 종류 누락(IT-1·IT-2·PR-1·LA-2·ME-1·PW-1b), EO-1 '병합 선행' 대 '완료(SPICE 다리) 선행' 의미 통일.
- A-N13 HC-S 다리 (b) '정지 없이 탐색' 실행 수단 = 검증자 하네스(엔진 안 우회 스위치 금지).
- A-N14·B-N4·L4 '외층 커널 평가' 15곳 → '평가 커널'.
- A-F11 잔여 413행 matching_offset dc→ss(graph/CONTRACT.md:244 dc_to_ss) 고칠 card.
- B-L1 hc 155행 '커널 max-min 수리 단계' → `_repair`.
- B 3절 LA-1 순서 절 선행 목록(1735)에 HC-1·GC-9·EO-1, FX-1 1599 'U17 ②와 착수 때 선후' 낡음.
- B-L9·A-N15 낡은 줄 인용(gb 289·1190 '(479행)', gc 491, op 472).
- B-L10 power_dc_w도 counted_rails 부분 선언 시 OP-11과 갈림(dc_metrics.py:110) → 백로그 (i).
- 오케스트레이터 추가: AI 손분석 설계(DEC-98 독립 대조군)의 oracle 입력 생산 주체 -- EO-1과 같은 G-18 스키마로 넣는 경로를 명시.
- 미확인(감사): OP-11과 엔진 power 부호 규약, op 합격 판정 '동작점 gm/ID' 출처(엔진 값 대 SPICE op), XRUN-F1 card B·C의 O-44 동작 변경 card 해당 여부, op X-26 해소 표시, ME-1 gain 모델 오차의 LA-1 새 front 점 재사용 범위(DEC-72).
