---
title: offset-trim -- 계획 이력
plan: offset-trim.plan.md
date: 2026-10-15
---

# offset-trim 계획 이력

> 계획서(`offset-trim.plan.md`)에 넣지 않는 **경위·제안 원문 요지·원문 검토 기록·버전 이력**을 둔다. 현행 규칙·정의·게이트·완료조건은 계획서가 정본이다.

## H1. 결정 경위

### 2026-10-15 착수 결정 T-1~T-4

- 원문: `wt/_drafts/user_decisions.md` '## offset trim 착수 결정 (2026-10-15 사용자 "권고대로 해")'.
- 앞선 제안(오케스트레이터가 사용자에게 한 보고 요지, 계획 초안의 출발점):
  - 주입 노드 = 입력 셀(S1v gain 뷰 첫 이득 블록 input 셀) drain 쪽 차동 노드 쌍 후보 가운데, 기존 수반 offset 해석(σ_in = √Σ(Z_i·gm_i·σ_VGS,i)²/A_dm)으로 단위 전류당 보정 t_n = z[n]/A_dm 이 크고 headroom 여유가 있는 쌍.
  - 범위 I_range ≥ k·σ_in/|t_n|, LSB I_LSB ≤ V_res/|t_n|, N = ⌈log2(2·I_range/I_LSB)⌉, 단위 소자 W·L은 DAC mismatch DNL < LSB/2(Pelgrom, mismatch LUT).
  - 구조 역할 trim_dac(신호 경로 제외, 바이어스·잡음·커패시턴스 기여는 남김), θ 변수 I_LSB 또는 I_T·단위 gm/ID·L, 제약 trim_range ≥ k·σ_in, metric trim_lsb·trim_dnl·trim_power·trim_area, 코드 양 끝 DC 동작점 검사.
  - offset spec 의미 전환(σ_in ≤ spec → 잔여 offset, iv_matching_l 완화), drift·1/f는 유지. CMOS는 offset trim이 drift를 trim하지 않음(TI SBOA590 §1.2). 상보 입력쌍은 trim 각각. 단일 입력 회로는 spec에 offset 항목이 있을 때만.
- 계획 초안 반영: 위 제안 가운데 사용자 결정 T-1~T-4로 확정된 것만 계획서 '확정'으로 두고, 나머지(설계식 형태, θ 변수 선택, iv_matching_l 완화 범위, 주입 노드 순위 기준 등)는 계획서 N7 '사용자 결정 필요'로 모았다.

## H2. 원문 검토 기록 (2026-10-15)

검토한 원문 7편(앞선 2편 Srinivasan 2007·Kay 2024 + 이번 5편). 보관 위치 `skills/analog-gmid-design/assets/technique/sources/`, 목록은 그 폴더 README.

| 원문 | 계획 근거로 쓴 것 | 쓰지 않은 것(이유) |
|---|---|---|
| Mohamed 2013 (SIECPC) | 한 입력 단자에 DC 전압을 더하는 방식의 존재와 비용: 신호 경로 안 두 단 level shifter(식 (7) 버퍼 이득 < 1, 대역 제한), ΔV_GS가 I_Trim의 제곱근 함수(식 (4)) -- 기본안(전류 주입)과의 비교 근거 | 표 I의 W·L, I_optimum 5.41 µA, 200 µV 등 수치(원문 값 인용 금지). '온도 무관' 주장(식 (4)는 ΔV_TH 항을 남겨 V_TH 온도계수가 같을 때만 성립) |
| von Staudt 2011 (IMS3TW) | trim 범위가 미보정 분포를 덮어야 한다는 조건(R = 2^n·LSB), 이진 가중 주 전이 DNL σ_U·√(2^n−1) 대 thermometer σ_U(Table I), 양의 DNL이 trim 뒤 분포 꼬리를 만든다는 것, 범위 손실과 bit 추가의 교환 | '±5σ_V' 범위 관례·5 % 단위 σ·Table II/III 수치(상수 발명 금지 -- 범위 배수는 사용자 spec k). 자기 trim·비교기 잡음 모델(이번 범위는 sizing, trim 알고리즘 밖) |
| Zhou·Kay 2017 (TI SBOT037A) | e-Trim = 패키지 뒤 내부 보정 전류원 조정(p.1), Fig.2 입력쌍 쪽 trim 소자, Table 1 drift·1/f 제거는 chopper만 | 제품 수치(OPA2191 등) |
| Bertotti 2012 (ARS) | 차동 출력 전류 steering 단위 셀(Fig.3, Iout+/Iout−, 전류원을 끄지 않음 -- T-3 'I_A+I_B 일정'과 같은 구조), 최악 INL·DNL 분산식 (2)(3)(분할 m비트), 단위 전류 상대 σ의 Pelgrom 식 (4)(강반전)·(5)(약반전), 공통중심 배치 | 10 µA·40 nA·1.904 %·m ≤ 5 등 수치, 배치 그림의 계수 |
| Lu 2007 (ICICDT) | 1단 출력(R1) 노드에 보조 transconductor 전류를 넣는 구조(Fig.2·3), 주입 소자를 더할 때 부하 전류 균형을 맞추는 크기 관계(식 (10)) -- 코드 중간점 계통 offset 검사의 근거, 주입 오차가 G_m,aux/G_m1에 비례(식 (9)) -- 주입 소자 gm을 작게 둘 근거 | 클럭·저장 커패시터 동적 기법 자체(trim 범위 밖), 1.898 mV 등 수치 |
| Srinivasan 2007 (JSSC, 앞서 보관) | 'current-mode DAC로 증폭기 부하 전류를 조정해 offset 보상'(§I, p.1) -- 주입 노드 = 부하 쪽 근거 | floating-gate 프로그래밍 |
| Kay 2024 (TI SBOA590, 앞서 보관) | CMOS drift는 offset에 비례하지 않아 한 온도 offset trim이 drift를 trim하지 않는다(§1.2, **PDF p.7** Figure 1-8 문단; 오케스트레이터 보고의 '§1.2'는 맞고 쪽은 p.7), CMOS 입력 모델의 trim 저항(Figure 1-6, p.6) | 제품 표 수치 |

## H3. 측정 근거

- 엔진 현황 사실 문장의 파일:줄은 2026-10-15 base `cfe2e31` 기준 읽기 확인(계획서 N3.0 표). 엔진 코드 변경 없음.

## Version History

| 버전 | 날짜 | 변경 |
|---|---|---|
| 0.1 | 2026-10-15 | 초안: 계획서·history 신설, 원문 5편 보관(누적 7편). 사용자 승인 전 |
