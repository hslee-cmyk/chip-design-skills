# 계획 v6.38.2 첫째 커밋 독립 검증 1 (2026-10-28)

- 피검: `wt/plan-v6382` 커밋 `233dc336`(부모 `1fefcab1`), 바뀐 파일 = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(+80/−12), `...history.md`(+1).
- 검증자: 독립 검증 agent(작성자 아님). 작성자 보고·커밋 메시지는 증거로 쓰지 않았다. 아래 근거는 모두 원문을 직접 읽은 것이다.
- 대조 원천: `wt/_drafts/user_decisions.md`(:300-316 2026-10-13, :366-373 2026-10-14, :1143-1145 O-162~O-164), `wt/_drafts/engine/STEP2_DESIGN_GAPS_DECISION_PACKAGE.md`(PKG), `wt/_drafts/evidence/2026-10-27/decision_propagation_audit.md`(감사), `h_judgment.md`, `cmp1_verify_alternatives.md`, `wt/_archive/README_cmp1_H_baseline.md`, 엔진 `wt/integ-it12` @ `ebad06c1`(읽기만), design 40·41·42(`wt/plan-v6382/docs/02-design/features/`).
- 파일 수정: 이 문서 하나만 썼다. git은 `git -C`·읽기 명령만 썼다(reset/checkout/stash 없음). 끝난 뒤 `git -C wt/plan-v6382 status --short` 빈 출력.
- 줄 번호: 계획 = 233dc336 판(DEC-104 = :303, DEC-105 = :304, LR6 = :684, LA-1 범위 15 = :1849, 완료 조건 9·10 = :1887·:1888, X-LA8 = :1928, TB-1 범위 3·4 = :2189·:2190, TB-1 병합 규칙 = :2192·:2196, N6.32~N6.34 = :2228~:2273, U-125~U-128 = :2450~:2453).

## 0. 요약

| 심각도 | 수 |
|---|---|
| 높음 | 0 |
| 중간 | 9 (D-1~D-8, D-10) |
| 경미 | 13 (D-9, D-11~D-22) |

사용자 확인 필요: 5건(§3). 13건 결정 반영 자체(뜻의 축소·확대)는 대부분 적합하고, 결함은 주로 **정의 공백·내부 모순·card 순서/병합 규칙·완료 게이트 입력 정의**에 있다.

## 1. 항목별 판정표

| # | 검사 항목 | 판정 | 근거(파일:행) |
|---|---|---|---|
| 1-1 | Q1-2 (ii) found_db 비례 g_i | 적합 | 원문 user_decisions:313 = 계획 :304 DEC-105 (1). '인증 무관 활성·gain 미선언 비활성' 일치 |
| 1-2 | Q6-1 (A) W-bin 슬라이스 | 결함(중간) D-4·D-5·D-6, 경미 D-21 | 원문 :310 'W→슬라이스→W 고정점 bin 수 상한' 일치. 단 전류 없는 단계·ss 열·D1 상호작용 공백 |
| 1-3 | Q1-1 N9 매크로 망 | 적합 | PKG:13, D41:1610 문언 있음 → DEC-104 R3 :303 '(design 41 §6.5 N9)를 포함' |
| 1-4 | Q2-2 P = 0 | 적합(경미 D-14) | PKG:232 '같은 2배 사다리' ↔ 계획 '§6.5 출발점 생성 규칙의 다음 후보'(as-built `macro_poles.py:316-326` step = ln 2) |
| 1-5 | Q3-1·Q3-2·Q-N9 `mirror_vds`(U-126) | 사용자 확인 필요 + 결함(중간) D-1·D-2·D-3, 경미 D-19 | 원문 :308 '§6.7 목표 행, 위반 최소, 해 없으면 StartConflict'. 계획 :304 (4)·X-LA8 :1928·U-126 :2451 |
| 1-6 | Q4-1·Q4-2·Q-N2 D 가드 | 적합(경미 D-22) | PKG:346·:349·:489 = 계획 (5)(a)(b)(c), TB-1 범위 3 :2189 |
| 1-7 | Q5-1 (가) U-125 기본안 '대체됨' | 사용자 확인 필요(근거는 성립) | (i) O-122 = DEC-90 (2)·R10 '엔진 슬루 판정 없음'(:303) 성립 (ii) R10 대상 = SR 선언 셀(:303) 성립 (iii) DC 부분: 접힘 노드 KCL I_free = I_in + I_c, I_c ≥ W_min 하한 전류 > 0 → I_free > I_in 함축, 성립(정확히는 'W_min 하한 행 + 전도(봉인 9)') (iv) 남는 몫 = 대신호 비차단 = spec 없는 요구 → R1(:303 '요구는 spec 양') 충돌. 감사 A-12 '대체 의도 사용자 확인 대상'과 같음 |
| 1-8 | Q5-1 재측정·Q-N6/7/10·Q-R1 | 적합(경미 D-16) | 계획 LA-1 완료 조건 9 (f) :1887 |
| 1-9 | Q-N2 B 면적 → gm/ID 하한 | 적합 | PKG:487 = 계획 (6)·LR6 :684. 식 IDu(g, L) ≤ I·L²/A_min 확인(W = I·L/IDu ⇒ W·L = I·L²/IDu) |
| 1-10 | Q-N3 CMFB DC 평형 | 적합(경미 D-13) | PKG:501 = 계획 (7) |
| 1-11 | Q-N11 B 분해능 | 적합(순서 결함 D-10) | PKG:595·:598 = 계획 (8)·RS-1 |
| 1-12 | N12 counted_rails | 적합(경미 D-15) | 원문 :373 = 계획 (9)·SF-1 범위 8 |
| 1-13 | N13 θ 상자 | 적합(경미 D-20) | 원문 :368 = 계획 (10)·SF-1 범위 9 |
| 2-1 | CPG-1 완료 조건 대 O-164 | 결함(중간) D-8, 사용자 확인 D-9 | O-164 :1145 '같은 library 9회로(+folded O-140 사본)…H0r 이상'. 계획 :2271 |
| 2-2 | 기준선 수 H0r 4 | 적합 | `h_judgment.md` §1 표(:57-65) H0r = common_gate, two_stage_ota, folded*(저장소 spec), pushpull = 4; README:7 같음; O-140 사본 전 변형 0(:43) |
| 2-3 | 미달 시 D 경로 | 적합 | O-164 '못 넘으면 D' = 계획 :2271 |
| 3-1 | fail-closed 규칙 대 iv_gain_l.py:125-127 | 적합(경미 D-18) | as-built :125 `if found is None:`, :126 `found = anchors[-1] if previous is None else previous[1]`, :127 margin `target − (0.0 if previous is None …)` -- 계획 서술 '가장 긴 앵커로 닫고 0 dB 가정' 일치. 의미('비활성 + 사유')는 `cmp1_verify_alternatives.md`:91·:104와 일치 |
| 3-2 | GC-5 공유 서술 | 적합(경미 D-11) | graph-consumption.plan.md:459 '`gain_l_bounds`: 전류 충돌로 빠진 블록은 … 최대 앵커 L 하한을 만들지 않는다(지금 `iv_gain_l.py:125-127`)… 전류 충돌 사유로 비활성' -- 충돌 없음. 단 graph-consumption 쪽 역참조 0(`grep DEC-105` 0) |
| 4-1 | g_i^(1) 필드 | 적합 | writer 하나(design), 소비자 = 출발 구간 이득 L 하한·층 0 첫 회차(둘 다 LA-1) -- 같은 양 둘째 생산자 금지(규칙 1·3) |
| 4-2 | `mirror_vds` 인스턴스 S0 필드 | 결함(중간) D-7 | writer 하나 OK, 소비자 = LA-1만인데 병합 규칙이 'HC-1·LA-1 중 먼저'(TB-1 :2192·:2196) |
| 4-3 | 새 cache·sctx 슬롯·사본 | 적합 | 새 칸 0. WB-1 슬라이스 키 = `LutAccess` 폭 키 성분 → LUT memo 승인 예외(N3.3·U-87) 범위 안 |
| 4-4 | W-bin 지도 자리 | 경미 D-21 | 'S0 수준 값'의 writer/자리 미명시. as-built `lut/lut_set.py:16-18, :88-100`이 이미 wmin/wmax W 행 파싱(LBinMap) |
| 5-1 | 만들면 배선 | 결함(중간) D-7 | 위 4-2 |
| 5-2 | DC/AC 분리 | 적합 | mirror_vds·CM 평형 = DC 출발, 판정 = 봉인·`pm_cm_ss_deg`; RS-1 = AC metric 분해능 |
| 5-3 | θ 기저 O-127 | 적합(경미 D-13) | DEC-104 (0)에 CM 평형 종속 문장 추가 -- 근본원칙 문언 변경인데 history는 '가리킴만'이라 적음 |
| 5-4 | EP-7 | 적합 | g_i^(1)·mirror_vds 출발값 전용 명시 |
| 5-5 | O-153 옛 코드 삭제 | 적합 | WB-1 범위 2, LA-1 범위 15 (a) |
| 5-6 | 상수 발명 | 적합 | E² − 1 = 1(PKG:489 §6.4-2 등분), 2배 사다리 = as-built, N13 '10번' = 사용자 선언 |
| 5-7 | 회로·소자 이름 | 적합 | 규칙 문언에 회로 조건 없음. 회로 이름은 I-H4·I-H5 조사 항목, U-127·U-128 data 후보, CPG-1 기준선 기록에만 |
| 6-1 | 계획 안 낡은 문언 | 경미 D-12(LY2 :999), D-17 | LR6·LA-1 범위 1·DEC-91 (2) 갱신 확인. LY2 '고른 finger_w가 LUT 기준폭(`w_ref_m`)과 다르면'은 WB-1 뒤 낡음 |
| 6-2 | 다른 계획 충돌 | 결함(경미) D-11 | offset-strategy.plan.md:212('하한은 mismatch 임계값' 인용)·:304·:619('L 하한') 그대로 |
| 7-1 | card 순서 | 결함(중간) D-10, 경미 D-17 | WB-1 LA-0 앞 OK; RS-1 '선후 고정 없음'이 감사 B-9 'LA-1 b_gain 선행' 권고·WB-1 같은 논리와 어긋남 |
| 7-2 | 열린 결정이 막는 자리 | 결함(경미) D-17 | U-125는 '확인 전까지 목록 그대로'(비차단) 명시. U-126은 LA-1 범위 15 (c) '확인 결과를 따름'뿐 -- LA-1 design 착수 조건에 없음 |
| 8 | 계획/이력 분리 | 적합 | 경위는 history H1 행. WB-1·RS-1 '사실' 절은 기존 card(SF-1 범위 6 등)와 같은 꼴 |
| 9 | design 넘김 목록 | 결함(경미) D-12 | 목록 항목은 모두 실제 충돌 문장(D41:1569·:1581·:1583·:1623-1633·:1640·:964·:1671 확인). 빠진 것 §2 D-12 |
| 10 | '원래 취지와 다름' 표지 | 결함(경미) D-9·D-19·D-20, D-1 관련 | mirror_vds·U-125·O-163·O-164 표지 있음. CPG-1 O-140 사본 기록만·RS-1/SF-1 미병합 허용·N13 library 사본 삭제·'신호 경로' 술어 계획 확정에 표지 없음 |

## 2. 결함 목록과 수정안

### D-1 (중간) U-126 근거의 내부 모순 -- StartConflict는 기록이다
- 사실: as-built `StartConflict`는 충돌 **레코드**다(`E/search/start_values.py:67-73`, `graph/start: conflicts` 필드 `start_intervals.py:11, :244`) -- 정지가 아니다. 계획 DEC-104 (0)(:303)도 '출발 단계 `StartConflict`'를 fail-closed의 기록 꼴로 쓴다. DEC-105 (1)(:304)은 R-1′ 행이 아닌 **이득 L 하한 미달**에 `StartConflict`를 그대로 쓴다.
- 그런데 DEC-105 (4)·X-LA8·U-126은 `mirror_vds`의 '해 없으면 StartConflict'를 "출발 fail-closed는 R-1′ 행에만(O-158 (A′) ②)"이라는 이유로 '기록'으로 바꿨다고 한다. 같은 판 안에서 (1)은 비-R-1′ 행에 StartConflict를 쓰고 (4)는 못 쓴다고 한다 -- 모순이고, '(나) 해 없음을 StartConflict 대신 기록으로' 차이는 실체가 없다(둘 다 기록).
- 또 U-126 대안 (가) 설명 "S 좌표에는 효과 없음 -- nmcnr 사례는 g가 S 소자"는 불완전하다: 조건은 VGS_g = VGS_d(PKG:281)라 d(diode, B 소자)의 밀도를 R6/R7이 옮겨도 맞춰진다(PKG:287 'g의 gm/ID·L이 d 쪽으로 끌린다'는 옛 §6.7 기준 서술).
- 수정안(원칙 근거): U-126을 다시 쓴다 -- 원문 '해 없으면 StartConflict'는 유지(P6 기존 사용자 결정 문언은 P0~P5가 요구할 때만 바꾼다, DEC-104 (1); 여기서 요구하는 상위 원칙 없음). 남는 '원래 취지와 다름'은 (가) S 출발값 선택으로의 확장 하나뿐이고, 대안 (가)의 효과 서술을 'B(d) 쪽 밀도는 R6/R7로 움직일 수 있음, S(g)는 못 움직임'으로 고친다(권고 전 실현 가능성 실측 원칙).

### D-2 (중간) `mirror_vds` 층 0 적용 여부 모순
- DEC-104 R6(:303): R6 블록은 "출발 단계 스냅샷과 층 0 후보 스냅샷에서 같은 블록으로 불린다". DEC-105 (4)는 등식 순위를 R7 B 선택·R5′ (2) 선택(= R6 블록 안)에 넣으면서 "층 0 탐색·외층은 이 등식에 묶이지 않는다"고 한다. 층 0 후보 스냅샷의 R6/R7 호출에서 순위를 쓰는지 정해지지 않았다. 원문(PKG:287)은 '외층은 자유'만 적었다.
- 수정안: "층 0 후보 스냅샷의 R6/R7 B·W4·V_R 선택도 같은 순위를 쓴다(같은 블록·같은 규칙 하나 -- graph 규칙 1), 층 0이 고르는 독립 좌표와 외층만 자유"처럼 한 문장으로 정하거나, 반대로 정하면 그 근거와 표지를 단다.

### D-3 (중간) S 출발값 선택에 K-1 단계가 정의돼 있지 않음
- DEC-105 (4)는 "S 좌표(gm/ID·L, R4 독립)는 출발 구간 안 출발값 선택 … 각 선택의 K-1 (i) 위반 최소 단계"라 쓰지만, DEC-104는 K-1을 R5′ 재개방·R7 B 선택에만 정의한다(:303). R4는 S의 L = 이득 요구 bin 안 역산(LR3), ID = max(gm_req/(gm/ID), R8 하한)라 `mirror_vds`와 R4 역산 L의 우선순위가 없다.
- 수정안: (가) U-126 기본안을 B·W4·V_R 선택에 한정(원문 형태에 가장 가까움)하거나 (나) S 출발값 선택 절차를 계획에 정의하고 R4(이득 역산 L, gm_req)가 이 등식보다 우선임을 명시한다. 어느 쪽이든 U-126 질문에 이 선택을 넣는다.

### D-4 (중간) 전류가 정해지기 전 단계의 W-bin 선택이 정의되지 않음
- DEC-105 (2)(:304)는 "출발 구간·층 0·평가 커널·외층·**GB4 국소 입력**도 소자 W가 속한 W-bin 슬라이스"를 읽고, 고정점은 "커널 W 계산 블록 안"이라 한다. GB4 블록 gain 상한(:607 'gm_id 격자 × L × VDS' 위 상계)은 전류를 모르므로 W가 없다. 출발 구간도 매크로 전류 확정 전 단계(§6.2 헤드룸 gm/ID 하한 등)는 W가 없다. 그 단계가 어느 슬라이스를 읽는지 공백이고, GB4에서 한 슬라이스만 쓰면 A_i,max '상위집합 위의 상계'(:607) 보장이 깨질 수 있다.
- 수정안: GB4 = 그 kind의 모든 W-bin 슬라이스 위 최대(상계 유지, 새 상수 없음) 또는 기준 폭 유지 + '추정' 기록을 계획에 정하고, 출발 구간은 전류 확정 뒤 커널과 같은 고정점 함수 하나를 부른다(둘째 고정점 금지)를 적는다.

### D-5 (중간) DEC-91 (2) 'DC·`ss` LUT 슬라이스'와 DEC-105 (2) 'DC 슬라이스' 불일치
- 계획 DEC-91 (2)(:290): "DC·`ss` LUT 슬라이스는 소자 W가 속한 … W-bin의 슬라이스다". DEC-105 (2)는 "LUT DC 슬라이스". 잡음·mismatch 열은 기준 폭(5 µm)에만 있다(`docs/03-analysis/gain-budget-gmid-sizing.u3-lut-pdk-record.md` §9), 용량 표는 채택 기준 폭(`CapTable.w_ref_m`, `pre_layout_widths.py:1-3`). DEC-105 (2)의 '그 bin에 슬라이스가 없으면 fail-closed'를 `ss` 열에 문자대로 걸면 모든 점이 실패한다. `cmp1_verify_alternatives.md`:112도 'AC·잡음은 기준 폭 환산이 남음(기록 필요)'을 적었다.
- 수정안: "W-bin 슬라이스 = DC 슬라이스 열(ID·gm·gds·VDSAT·tol 등), 용량·잡음·mismatch 열은 기존 기준 폭 환산(lut 계약 9.3·10.4) 유지·남는 차를 기록"으로 두 자리를 맞춘다. bin 안 슬라이스가 둘 이상인 경우·'bin 아래 끝 + 격자 한 칸' 슬라이스 추가(LR3 대칭, `cmp1_verify_alternatives.md`:112 권고)는 WB-1 design 항목으로 명시한다.

### D-6 (중간) WB-1과 D1(W_min bin 경계 1 ulp) 상호작용 미등록
- as-built `E/lut/_helpers_bins.py:6-14`는 경계 비교를 1 ulp로 하고(PKG §8.1 D1: 왕복 오차 수십 ulp, 10만 점 중 37.6~39.9 %가 bin 밖), `mismatch_sigma.py:26`이 `bin_index(w_rows, W)`를 쓴다. W_min(0.42 µm)은 W-bin 경계다(PKG:410). WB-1이 같은 `bin_index`로 DC 슬라이스를 고르면 D1 결함이 슬라이스 선택과 'bin에 슬라이스 없음 = fail-closed'로 번진다. 감사 A-13은 D1이 card·backlog 없음이라 적었고 v6.38.2도 등록하지 않았다.
- 수정안: WB-1 범위에 D1 정정(경계 비교를 제조 격자 기준으로 -- `manufacturing_grid_m`, 새 상수 없음)을 넣거나 WB-1 선행 결함 card로 등록한다.

### D-7 (중간) TB-1 범위 4 필드가 소비자 0으로 master에 들어갈 수 있음
- TB-1 :2190·:2192는 범위 4에 'O-149 규칙(첫 소비자와 같은 통합 병합)이 그대로 적용'이라 쓰는데, TB-1의 O-149 규칙은 "HC-1·LA-1 가운데 먼저 master에 들어가는 쪽"(:2192, :2196, :1236)이다. HC-1이 먼저면 범위 4 필드(소비자 = LA-1 출발 구간 블록·R6 블록만)는 소비자 0으로 master에 남는다(만들면 배선 위반, graph 계산값 소비 원칙). 범위 3의 합 행 정정(소비자 R6 = LA-1)도 같다.
- 수정안: "범위 4 필드와 범위 3 합 행·정정은 LA-1 통합 병합으로만"(또는 범위 4를 LA-1 범위로 옮김)을 적는다.

### D-8 (중간) CPG-1 입력('기준선 판정 때의 제약 값')이 C′ 시점에 실현 가능한지 정해지지 않음
- CPG-1 범위 1(:2266)은 "spec = 기준선 판정이 읽은 제약 값(`ebad06c1`) … 형식 이관만 허용하고 값은 같게"라 한다. 그러나 (a) LA-1 범위 14(:1848)가 common_gate에 C_L 1 pF를 **topology**에 더한다(connectivity 변경) -- 기준선(`h_judgment.md`:49 common_gate spec 'noise·면적만')의 회로와 다르고, topology는 규칙에 없다 (b) SF-1·DE-1이 `swing_out_v` 제약·metric(nmcnr·current_reuse), `linear_s`, `driving_spec`을 지운다(SF-1 범위 5·6, :2171-2172) -- 옛 spec은 C′ 엔진 로더가 받지 않을 수 있고 '형식 이관'으로 옮길 자리가 없는 항목이 있다(판정 도구는 swing을 잰다, `h_judgment.md`:24).
- 수정안(사용자 확인과 함께): 엔진 입력 = 기준선 topology + 기준선 spec의 형식 이관본, 엔진 쪽 항목이 사라진 제약은 엔진 입력에서 빼고 판정 도구가 기준선 정의로만 판정, 이 처리 목록을 판정 기록에 적는다(같은 입력 비교 원칙, 기준 약화 금지).

### D-9 (경미 -- 사용자 확인) CPG-1 셈 범위가 O-164 원문과 다름, 표지 없음
- O-164(:1145): "같은 library 9회로(+folded O-140 사본) … 통과 회로가 H0r 이상". 계획 완료 조건(:2271): 셈 = library 9회로(기준선 spec)만, O-140 사본은 '기준선 0 대비 기록'. 기준선이 O-140 사본에서 0이라 계획 쪽이 더 엄하다(O-140 사본만 통과하면 O-164 원문으로는 셈에 들고 계획으로는 안 든다). 또 RS-1·SF-1 범위 8·9 미병합에서도 게이트를 돌 수 있게 했다(:2273 '병합 여부도 적는다') -- O-164 'C′ = … 13건'과 다른 해석.
- 수정안: 두 해석을 '원래 취지와 다름(사용자 확인 대기)'으로 표시하고 승인 질문에 올린다.

### D-10 (중간) RS-1 순서가 감사 권고·WB-1 논리와 어긋남
- RS-1 범위(:2252)는 소비자에 'LA-1 gain bin 폭'(b_gain → w_g, DEC-72)을 적으면서 순서(:2256)는 "LA-1과 선후 고정 없음". 감사 B-9(:195)는 'LA-1 gain bin 폭 b_gain 선행'을 권고했고, WB-1은 같은 이유(LA-0 기준선 위에서 LA-1 변화표 원인이 갈려야 함)로 LA-0 앞에 뒀다(:2244). RS-1이 LA-0 측정과 LA-1 병합 사이에 들어가면 LA-0 기준선이 낡는다.
- 수정안: RS-1을 LA-0 앞(권고 -- 감사 B-9) 또는 LA-1 뒤로 고정하고 근거를 적는다.

### D-11 (경미) 다른 계획 동기화 누락
- offset-strategy.plan.md:212("규칙 정본은 gain-budget N3.9 LR6('하한은 mismatch 임계값' …)"), :304·:619(G-S2 'L 하한')은 LR6 개정과 충돌한다. 계획 LR6(:684)은 '그 계획 후속 정정'이라고만 하고 추적 자리(U·card·후속 정정 표 행)가 없다. graph-consumption GC-5(:459)에는 DEC-105 (1) '먼저 병합되는 card가 분기를 만든다' 역참조가 없다(`grep DEC-105` 0).
- 수정안: 같은 판에서 offset-strategy 인용 정정(또는 후속 정정 표 행), graph-consumption GC-5 범위에 한 줄 역참조.

### D-12 (경미) design 넘김 목록 누락(§9 확인 결과)
- 목록 항목은 모두 실제 충돌 문장이다. 빠진 것: D41 :1044('§6.4-2 matching 하한(LR6의 봉인 전 추정)' -- L 격자 넓히기 멈춤), :1495('절대 offset 제약이 있으면 matching L 하한'), :1570(§6.4-2 머리), :1594('matching 하한과 같은 꼴'), :1599(§6.4-6 'L = max(1, 2, 3의 하한)' -- matching 포함), :1859(§7.5 잡음 가드 '부하 gm/ID 상한' -- 합 행·Q-N2 D), :1958(test 표 '절대 offset 회로에서만 L 하한 활성'), :1513·:1705·:1947(§6.7 7a·`StartConflict(kvl)` -- `mirror_vds`), D40 §3.10.1 :1340-1343('sizing 쪽 폭 슬라이스를 소자당 하나로' -- WB-1과 겹치는 기존 design, 재사용 대상), D42 D-P2 :292(소자별 폭 슬라이스 DEV 항목), 엔진 계약: sizing 계약 'kind당 폭 슬라이스 하나'(`kernel_keys.py:5-6` 인용)·lut CONTRACT 1.4(`w_ref_m`). 계획 안: LY2 :999 '고른 finger_w가 LUT 기준폭(`w_ref_m`)과 다르면'.

### D-13 (경미) history의 'DEC-104 가리킴만(규칙 문언 무변경)' 서술 부정확
- DEC-104 (0)에 "CM 되먹임 루프의 DC 평형 등식도 θ 전류 축의 종속을 만든다", R3에 "N9 포함·매크로 출발점 P = 0"이라는 규칙 내용이 들어갔다(:303). 근본원칙(DEC-104) 문언 변경이므로(내용은 2026-10-13·14 사용자 결정에 근거) 승인 질문에 '근본원칙 문언 추가'로 따로 적어야 한다(근본원칙 적용 전 승인 규칙).

### D-14 (경미) Q2-2 '다음 후보' 문언 모호
- PKG:232 "뒤 블록 gm을 같은 2배 사다리로 더 올린다". 계획 "그 출발점을 버리고 design 41 §6.5 출발점 생성 규칙의 다음 후보로". '다음 블록 k'로도 읽힌다. 수정안: "같은 2배 사다리(as-built `feasible_start` step)의 다음 칸, 사다리 끝이면 다음 블록 k".

### D-15 (경미) N12 '목적 축이 같은 선언을 읽음'의 처리
- 원문(:373) "제약과 DEC-78 목적 축이 같은 선언을 읽음(단일 정본)". 계획 (9)는 "DEC-78 정의는 바꾸지 않는다"이고, 계획 :1987은 as-built `power_dc_w` = counted_rails와 무관한 모든 레일 Σ V·I라 적는다. 접지(0 V) 레일만 빠지면 값이 같지만, 0 V 아닌 레일이 선언에서 빠지면 다르다. 원문 (2) held-out 판정 값(D ≤ 92 µA, B 합 ≤ 10.4 µA·'등록 시 원문 정의 일치 실측 확인', A·C 보고만)을 실을 card도 지정되지 않았다('별도 data 커밋'). 수정안: 목적 축이 선언을 읽는 방식(또는 '0 V 레일만 빼는 선언일 때 같음' 조건)을 계획에 적고 held-out data 커밋 소유 card를 정한다.

### D-16 (경미) Q-S1 (라) 확인 미등록
- 원문(:367) "Q-S1 (라) ② 반영 뒤 엔진이 sf 동시 실현 불가(front 빔)를 내는지 먼저 확인". 감사 B-10 '판정 불가, LA-1 뒤 재측정'. LA-1 완료 조건 9 (f)에 없다. 수정안: (f) 표에 한 줄.

### D-17 (경미) 순서 문자열·열린 결정 막는 자리
- LA-1 선행 문장(:1892)의 순서 "IT-1 + IT-2 → UB-1 + NL-1·HC-S·EO-1 → LA-0 → LA-1"에 WB-1이 없다(목록 끝에만 추가). U-126이 LA-1 범위 15 (c)·design 착수를 막는지 LA-1 착수 조건·U-126 '시점' 칸(:2451 '사용자 확인')에 없다. 수정안: 순서에 'WB-1'을 넣고 U-126 시점 = 'LA-1 design 착수 전'.

### D-18 (경미) 이득 L 하한 미달 처리의 동작 변경 미표시
- as-built :126은 미달일 때 **마지막으로 평가된** 앵커(`previous[1]`)를 쓴다. 계획은 '평가된 최선 앵커'(LR4: L 증가가 늘 이득 증가는 아님). 동작 변경이므로 LA-1 변화표 원인 항목으로 적는다.

### D-19 (경미) '신호 경로' 술어를 계획이 정함
- Q3-2 원문(:308) "'신호 경로' 조건을 구조로 더하는 방식은 design에서 정의". 계획(:304 (4), TB-1 :2190)이 'R10 바이어스 고정 넷 술어의 부정'으로 정했다(회로 해석 성격, 공동분석 규칙). 또 부정 문언이 "어느 여기 뷰에서든 신호 넷"이라 R10 술어(:303 '모든 여기 뷰·되먹임 경로')의 '되먹임 경로'가 빠졌다. 수정안: '오케스트레이터 원칙 기본안(사용자 확인)' 표지, 문언에 되먹임 경로 포함.

### D-20 (경미) N13 범위 확장 표지 없음
- 원문(:368)은 held-out B CBAT 상자 규칙. 계획 SF-1 범위 9는 library 회로별 `theta_bounds` 사본 삭제(data 커밋)까지 넣었다. graph 규칙 1에 맞는 기본안이지만 결정 밖 확장이므로 '오케스트레이터 원칙 기본안' 표시.

### D-21 (경미) W-bin 지도 '새 파싱'처럼 적힘
- as-built `lut/lut_set.py:16-18, :88-100`이 이미 `.model` 블록 wmin/wmax로 W 행을 파싱하고 `bin_index`로 슬라이스 W bin을 정한다. WB-1 범위 1은 'LR3와 같은 파서'라고만 적었다. 수정안: 기존 `_bin_blocks`·`bin_index` 재사용(둘째 파서 금지)과 자리(LUT 적재 메타 -- graph 필드 아님)를 명시.

### D-22 (경미) R7 (가) 선언 범위 고리 B의 합 행
- R7 (가)(:303)는 선언 범위 고리 B를 나머지 경계로 정하고 K-1은 재개방 때만 쓴다. DEC-105 (5)(a)는 합 행을 'K-1 공동 선택에서' 읽는다 -- (가) 경로에서 합 행을 어디서 거는지 공백. 수정안: (가)의 '가드 구간과의 교집합'에 합 행 포함 여부를 한 줄로.

## 3. 사용자 확인 필요 목록

1. **U-126 `mirror_vds`**(D-1·D-2·D-3 정리 뒤 다시 묻기): 원문 'StartConflict'는 기록이라 유지 가능 -- 남는 차이는 S 출발값 선택으로의 확장과 층 0 적용 여부. 대안 효과 서술을 고친 뒤 질문.
2. **U-125 Q5-1 (가)** 기본안 '대체됨': 근거 (i)~(iii)는 원문에서 성립(위 1-7). 받으면 승인 결정 하나를 거둠(원래 취지와 다름).
3. **CPG-1 셈 범위**(D-9): O-140 사본을 셈에서 빼고 기록만, RS-1·SF-1 8·9 미병합 허용 -- O-164 원문 해석 확인.
4. **CPG-1 입력**(D-8): 기준선 topology(common_gate C_L 없음)·삭제된 제약 처리.
5. **N12 목적 축**(D-15): 전력 축이 `counted_rails`를 읽는지.

(U-127·U-128은 계획에 질문으로 이미 올라 있음 -- 값은 사용자만 확정, 이 검증은 형식만 확인: 적합.)

## 4. 재현 명령

```bash
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6382; R=/c/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12
E=$R/skills/analog-gmid-design/gmid_engine; P=$W/docs/01-plan/features/gain-budget-gmid-sizing.plan.md
set -e
git -C $W show --stat 233dc336
sed -n '1143,1145p' /c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md           # O-162~O-164
sed -n '300,316p;366,373p' /c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md    # Q·Q-N·N12·N13 원문
sed -n '120,130p' $E/search/iv_gain_l.py                    # D-18, 3-1 (:125-127 닫힘, previous = 마지막 평가 앵커)
sed -n '44,52p' $E/search/iv_context.py                     # 인증 조건 :50-51
sed -n '67,73p' $E/search/start_values.py; grep -n 'conflicts' $E/search/start_intervals.py | head   # D-1 StartConflict = 기록
sed -n '316,326p' $E/search/macro_poles.py                  # D-14 2배 사다리
sed -n '1,22p' $E/sizing/pre_layout_widths.py; sed -n '1,8p' $E/convergence/kernel_keys.py
sed -n '1,20p' $E/lut/_helpers_bins.py; sed -n '12,18p;88,100p' $E/lut/lut_set.py; sed -n '20,30p' $E/lut/mismatch_sigma.py  # D-6, D-21
grep -n '잡음·mismatch 열은 기준 폭' /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/docs/03-analysis/gain-budget-gmid-sizing.u3-lut-pdk-record.md   # D-5
grep -n 'L 하한\|mismatch 임계' $W/docs/01-plan/features/offset-strategy.plan.md            # D-11
grep -c 'DEC-105' $W/docs/01-plan/features/graph-consumption.plan.md                        # D-11 (0)
sed -n '459p' $W/docs/01-plan/features/graph-consumption.plan.md                            # 3-2 GC-5
grep -n 'A_max가 미상\|L ≥ √\|L = max(1, 2, 3\|부하 gm/ID 상한\|StartConflict(kvl)\|matching 하한' $W/docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md   # D-12
grep -n '소자당 하나\|kind당 폭 슬라이스' $W/docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md; grep -n 'D-P2' $W/docs/02-design/features/gain-budget-gmid-sizing.42-gap-checklist.design.md
sed -n '29,67p' /c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-27/h_judgment.md   # 2-2 H0r 4
cat /c/Users/HSLEE/Documents/Todoc/fpga/wt/_archive/README_cmp1_H_baseline.md
sed -n '227,236p;281,294p;342,353p;476,490p;586,598p' /c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/STEP2_DESIGN_GAPS_DECISION_PACKAGE.md
git -C $W status --short
```
