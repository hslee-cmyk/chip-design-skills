# reference 검토 G3 -- SKILL.md · sky130-worked-example.md · spice-verification-workflow.md 대 새 엔진

- 작성 2026-10-07. 읽기 전용 검토(저장소·코드 수정 없음, git 조작 없음). 실측은 scratchpad 스크립트로 LUT npz 를 읽기만 했다.
- 정독한 reference(전 행): `skills/analog-gmid-design/SKILL.md`(453행), `references/sky130-worked-example.md`(530행), `references/spice-verification-workflow.md`(103행).
- 대조 대상: `_drafts/user_decisions.md` 2026-10-07 항목(UD), `_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md`(REQ, 끝 '확정 사항'), `ROADMAP.md`(R), `design_gb7_dc_canonical.md`(G7), `design_mod1_lut_mod5_mna.md`(M15), `design_mod6_search_front.md`(M6), `design_mod7_layout.md`(M7), `design_spec_format.md`(SF), `lut_regen_plan.md`(LRP), `tol_v_measurement.md`(TV), `lut_coverage_study.md`(LCS), `PENDING_USER_DECISIONS.md`(PUD), `spice_harness_report.md`(SH), 계획서 v6.0(P), `gmid_engine/lut/CONTRACT.md`(LC), `gmid_engine/layout/CONTRACT.md`, `tools/spice_oracle/README.md`(OR).
- 표기: **[실측]** = 이번 검토에서 npz/파일로 직접 확인. **[추측]** = 근거 없는 추론. 심각도 높음 = 합격 시험·정확도에 직접 영향.

## 0. 이번에 잰 사실 (sky130 예제 수치 재계산, `assets/sky130_nfet_pfet_lut_sample.npz`)

스크립트: scratchpad `chk.py`·`chk3.py`(VDS 로그선형 보간 + rightmost root, W = W_ref·ID/ID_ref(W_ref = 5 µm)).

| 항목 | reference 값 | 실측 | 판정 |
|---|---|---|---|
| LUT L 격자 | §2: 4점(0.15, 0.35, 0.5, 1.0 µm) | 12점(0.15~4.0 µm), corner tt, 27 °C | reference 낡음 |
| gm/ID 최댓값 | SKILL 189행·sky130 §4 64행: NMOS 29.93, PMOS 32.20 | NMOS 29.93(L=1 µm, **VS=0.8, VDS=0.075 V** -- 비포화·체바이어스 점), VS=0 최대 27.43. PMOS 전체 최대 **32.60**(L=2.5 µm), L=0.5 µm에서 32.20 | 상수가 낡았고, 그 점은 포화 설계에서 쓸 수 없는 조건 |
| §7.3/§4 Cgg·Cgd(L=0.35, VGS 0.75, VDS 0.9) | 11.600 fF / 1.198 fF | 11.6005 fF / 1.1982 fF | 일치 |
| §5 PMOS 점(VGS −0.75, VDS −0.9, L 0.5) | ID 2.5388e-8, gm 4.9889e-7 | 같음 | 일치 |
| §5 PMOS gm/ID=20, L 0.5 µm, VDS 0.9 V의 W | ≈24660 µm | §4 시험 스펙(fT 100 MHz, CL 1 pF → ID 31.4 µA)으로 **7191 µm**(gm/ID 19.65면 6295 µm) | 재현 안 됨(약 3.4배) |
| §8 IGS 표 W | 8.07 / 15.26 / 46.40 / 2071.27 µm | 8.07 / 15.26 / 46.40 / 2071.68 µm | 일치(gain 19.8 대 20.9 등 보간 차) |
| §8 IGS '준정적 True'(fT ≤ 0.1·f_nqs) | 4행 모두 True | 소자 f_T = gm/(2π·Cgg): 3.81 GHz / 2.14 GHz / **773 MHz** / **23.5 MHz** → 0.1·f_T ≥ 100 MHz는 1·2행만. **3·4행은 False** | reference 오류 |
| §6 NGCC W | 8141.2 / 617.8 / 8346.6 µm | 8141.17 / 617.78 / 8346.65 µm | 일치. 다만 1단 PMOS 소자 f_T = **1.69 MHz** < GB 10 MHz(이 점은 물리적으로 불가) -- reference는 'W 폭증'만 적음 |
| §9 전력·면적 최소 점 W | 47.044 / 3.020 µm | 47.035 / 3.020 µm | 일치 |

---

## 1. 발견 목록

### G3-01 [높음] 포화 판정의 VDsat 정의가 엔진과 SPICE 오라클에서 다르다
- reference: SKILL 230~231행 "준정적 확인…", 233행·371행(스냅된 W로 SPICE 재검증), sky130 §6 120~131행 "`2/(gm/ID)`가 VDsat을 과대추정 … 강제 변환은 안전하지 않다", §7.4 195~196행 "op-info 파라미터는 이름이 그럴듯해도 무조건 신뢰하지 말 것 -- 스칼라 DC 값(id/gm/gds)과 … 신뢰도가 다르다".
- 새 엔진: G7 142행 봉인 7 `VDS − VDsat ≥ −tol_V`, VDsat = `lut.vdsat`(DF-25, "LUT (ID, gds, VDS)에서 유도", G7 117행) -- 그런데 LC 246행 "`vdsat` … 규칙 미확정·소비자 없음 → 만들지 않음". 오라클 OR 합격 조건 2 `VDS − VDSAT ≥ sat_margin_V`, VDSAT = ngspice BSIM4 op-info `vdsat`(oracle_netlist.py 34행). SF 164행 `saturation_rule = vds_ge_vdsat`(여유 0, '확인' 대기).
- 문제 유형: 잘못(정의 불일치) + 빠짐(엔진 VDsat 미정).
- 내용: (1) 엔진은 VDsat보다 tol_V(셀 p50 수십~수백 mV, TV 2절)만큼 **낮은** VDS도 봉인 통과시키고, 오라클은 BSIM vdsat 이상을 요구한다. 엔진이 통과시킨 해가 SPICE에서 '비포화 FAIL'이 되는 경로가 구조적으로 열려 있다. (2) 두 VDsat의 정의가 다르다(엔진 = LUT 곡선 유도식 미정, SPICE = BSIM 내부량). reference §7은 op-info 중 id/gm/gds만 신뢰성을 확인했고 vdsat은 검증한 적이 없다. (3) sky130 §6이 경고한 `2/(gm/ID)` 다리가 VDsat 유도식에 다시 들어오면 약반전에서 과대(보수) 추정이 된다.
- 보강안(엔진 내부): `lut/vdsat.py`의 정의를 **오라클과 같은 양**으로 고정한다 -- LRP 5절이 권고한 `VDSAT` 열(op `@m[vdsat]`, 비용 0)을 U-27 재생성에 넣고(LRP D6), 엔진 VDsat = 그 열의 보간값으로 한다. 오라클은 지금처럼 BSIM vdsat을 읽는다(같은 모델·같은 정의). 봉인 7의 `−tol_V` 완화는 SPICE 판정(`vds_ge_vdsat`)보다 느슨하므로, 봉인 7을 `VDS − VDsat ≥ +tol_V(id_equivalent 셀값)`(엔진이 SPICE보다 보수적이 되는 방향)로 뒤집거나, 최소한 오라클 `saturation_rule`과 같은 부호로 맞춘다. 단일소자 검사로 `@m[vdsat]` 과 "gds 꺾임 기준 VDsat"(LUT VDS 축에서 gds/ID 기울기 변곡) 차이를 한 번 재서 vdsat op-info 신뢰성을 기록한다(sky130 §7 방식).
- 누가: 엔진 내부(정의). SF 164행 '확인'(여유 규칙 선택)은 사용자.

### G3-02 [높음] 드레인·소스 접합 용량(CJD)이 엔진 MNA에 없고 오라클은 확산을 선택 사항으로 둔다
- reference: SKILL 99행 "5. 기생 CJD를 C에 더해 3~4 **반복 수렴** (W가 커지면 CJD가 자라 ID가 재상승할 수 있음)", 237행 "기생 수렴: … 실제로 수렴했는가", sky130 §10 273행 "junction cap 파라미터(ad/as/pd/ps)는 그럴듯한 placeholder -- 실제 레이아웃 반영 안 됨", 275행 "Cdd는 … 최종 npz에는 아직 포함하지 않음".
- 새 엔진: M15 3.3 소자 스탬프 "용량: cgd(g–d), cgs(g–s), cgb(g–b), 선언 커패시터" -- cdb·csb 없음. M15 2.8 "접합 용량(cdb·csb)은 LUT에 없어 MOD5가 별도 열로 보고". LRP 5절 230행 "(선택) CDD … 현재는 MOD5가 별도 열로 처리할 예정", LRP D6 미결. OR `diffusion`은 선택(`ad_per_w_m`, `pd_extra_m`), 없으면 ad/as 생략. 오라클은 `m=n_fingers`로 finger마다 독립 확산(공유 없음, C3).
- 문제 유형: 빠짐.
- 내용: 출력 노드·캐스코드 노드·Miller 2단 1단 출력 같은 고임피던스 노드에서 Cdb는 Cgd·Cgg와 같은 크기다(LCS 표 M·sky130 §7.1: W=5 µm에서 Cdd 4.34 fF 대 Cgd 1.20 fF). 엔진 PM/GBW 예측이 SPICE보다 체계적으로 낙관적이 되고(오라클에 diffusion을 넣으면), diffusion을 빼면 둘 다 비현실적으로 일치한다. 또 `m=` 병렬은 다핑거 레이아웃의 확산 공유를 무시해 접합 용량을 과대평가한다(대략 내부 확산 절반 공유 [추측]).
- 보강안: (a) LRP D6에서 드레인·소스 여기 AC 열(CDD·CSS 또는 접합만 분리된 CDB·CSB)을 U-27 재생성에 포함(조합당 추가 비용은 AC 4회 시제품에 이미 들어 있음, LRP 1.4). (b) `lut/cap_query.caps()`가 cdb·csb를 내고 `metrics/mna_build`가 d–b·s–b에 스탬프. (c) 확산 기하는 레이아웃 산출(행 Euler trail의 공유/비공유 확산)에서 소자별 ad/as/pd/ps를 계산해 엔진 `ss`와 오라클 입력 둘 다에 같은 값으로 넣는다 -- LUT 생성 규칙(ad=as=W·0.5 µm, pd=ps=W+2 µm, LRP 5절)은 레이아웃 전 첫 사이징점의 기본으로만. (d) 오라클 `process.diffusion`을 합격 실행에서 필수로(없으면 BLOCKED).
- 누가: (a) 열 추가 = 사용자(LRP D6·D7 승인). (b)~(d) 엔진 내부.

### G3-03 [높음] SPICE 합격 넷리스트가 어느 기하(sizing W 대 레이아웃 수렴 finger_w·nf)를 쓰는지 새 엔진 문서에 명시가 없다
- reference: SKILL 332~333행 "이 W로 freeze → SPICE 재검증(finger_w가 LUT 기준폭에서 벗어났다면 §8.3 방식으로 실측 재보정)", 371행 리포트 §6 "스냅된 W로 재검증한 SPICE 결과가 원 스펙을 만족하는지", 243행 "고급 시뮬레이터로 최종 미세조정".
- 새 엔진: R 1절 93행 "W 정본 … 레이아웃 어댑터는 W를 바꾸지 않는다"(철회된 옛 규칙이 표에 남음, R 319행 정정), R 53행 "레이아웃 … 합격 시험 밖, 보고용"(옛), M6 197행(front 점마다 `converge` 후 면적 재측정)은 SPICE 기하를 말하지 않음. OR `devices[]`는 `finger_w`·`n_fingers`·`W`를 받지만 어느 단계 값인지 정하지 않음. SH 3.1: 옛 엔진에서 layout W로 PM 79° → 18°.
- 문제 유형: 빠짐 + 충돌(R 표 안의 옛 규칙).
- 보강안: 합격 정의(T4·T5·마일스톤 1)에 "SPICE 넷리스트 기하 = MOD8 수렴 스냅샷의 (finger_w, n_fingers, 행 확산 기하)"를 한 줄로 고정하고, sizing 직후 기하(첫 사이징점)는 진단 실행으로만 둔다(오라클 `--tag sizing` / `--tag layout`). R 93·53행을 UD 레이아웃 규칙으로 정정. 결과 JSON에 SPICE에 넘긴 기하의 출처 스냅샷 지문을 기록.
- 누가: 사용자 확인 권장(합격 범위에 레이아웃을 넣는 결정 -- UD 8번은 'free 모드 + 스펙 + 포화'만 정함). 문서 정정은 엔진 내부.

### G3-04 [높음, 결정 재검토 제안] W 허용오차 상한 'tol_V × gm/ID'의 tol_V 지표가 결정·설계 문서에서 지정되지 않았다
- reference: sky130 §3 46~60행·§12.1 363~386행 -- W 정규화 오차는 ID를 그대로 W배 바꾼다(W_ref/L배 '버그' 사례), spice-verification §2 52~56행 "W = L·ID_target/IDu … 측정 전류가 ID_target과 일치".
- 새 엔진: UD "W 허용오차 = 상한 tol_V x (gm/ID)(소자별, tol_V는 계획 N3.6 LUT LOO 보간 오차)", R 331행, M7 156행 "상한 = tol_V·gm/ID"(LayoutInput `tol_v`, 지표 미지정), REQ 3.3 `"W_tol_rel_upper": "tol_V * gm_id"`. LC 171행만 "W 보존 = `id_equivalent`"로 배정.
- 문제 유형: 결정 재검토(문언 모호) / 충돌(LC 대 M7·REQ·R).
- 근거(실측 기록): gm/ID 역산 지표 tol_V(`gm_id_inverse`)는 보간 축 셀 p50 nmos 222 mV, pmos 224 mV(M6 121행). gm/ID 15에서 ΔW/W 상한 = 0.222 × 15 ≈ **330 %** -- '총 W 보존'이 사실상 무제한이 되어 레이아웃이 W를 몇 배 바꿔도 W_request가 나지 않는다(옛 엔진 10~35배 변경 결함과 같은 결과). `id_equivalent` 지표(p50 3.7 mV)면 ≈ 5.5 %로 물리 의미(ΔW/W = ΔID/ID = 같은 VGS에서 LUT가 구분 못 하는 전류 오차)와 일치한다.
- 보강안: 결정 문언을 "tol_V = `id_equivalent` 셀값(같은 VGS에서의 ln ID 보간 오차의 VGS 환산)"으로 명시하고, M7 `LayoutInput.tol_v`를 `(metric="id_equivalent", 셀 조회 함수)`로 타입화, test T11에 `gm_id_inverse` 값을 넣으면 거부되는 경우를 추가.
- 누가: 사용자(결정 문언 확정). 기본안은 LC 배정과 같다.

### G3-05 [중간] 합격 정의 문서들이 UD 8번(노드전압 = 기록만)과 충돌한다
- reference: spice-verification §1 20~22행 "각각 독립적으로 푼 뒤 그 결과를 사후 대조(차이가 작으면 … 검증 신호, 크면 설계 결함 신호)" -- 노드/게이트 전압 차는 **진단 신호**로 쓰라는 것.
- 새 엔진: R 102행 T4 "노드전압이 엔진 S2 `dc`와 tol_V 안" (판정), R 284행 마일스톤 완료 (b) 같은 문장, G7 255행 8.3 '판정 2(노드)', PUD AC-1 (iii)(v). UD 8번·OR 합격 정의·SF `node_compare_rule = record_only`는 기록만.
- 문제 유형: 충돌(새 엔진 문서끼리).
- 보강안: R T4·마일스톤 (b)·G7 8.3 판정 2를 "기록 + forced 경고"로 정정하고, 노드 대조는 진단 표(G3-14)로 옮긴다. PUD AC-1 (iii)(v)를 '해소됨(UD 8)'으로 표시.
- 누가: 엔진 내부(문서 정정).

### G3-06 [중간] 오라클에 단독 소자(LUT↔SPICE) 모드가 없다
- reference: spice-verification §2 52~57행 절차(사이징 W로 인스턴스화 → ID_target 일치 확인), SKILL 247~248행 DoD 항목, sky130 §3 56~60행.
- 새 엔진: R K3 완료 조건 "단일 소자 SPICE 오라클 ID 오차가 W_ref finger에서 LUT 보간 오차 안", R oracles (iii). 옛 하네스에는 `*.iso.cir`가 있었으나(SH 2단계) `tools/spice_oracle`에는 없다 [실측: `iso`/단독 grep 0건].
- 문제 유형: 빠짐.
- 내용: forced 모드의 소자 ID 차는 회로 DC 오차와 LUT 충실도 오차가 섞인다. reference §1의 '분해' 정신은 둘을 떼는 것이다. 단독 모드가 없으면 K3 완료 조건을 판정할 장치가 없다.
- 보강안: `oracle_netlist.py --bias iso` 추가: 소자마다 단독 인스턴스(`w=finger_w m=n_fingers`, 같은 확산 규칙), 단자를 엔진 예측 VGS·VDS·VSB에 고정, 측정 ID·gm·gds를 `ID_target`·예측과 비교, 허용오차 = 그 소자 슬라이스 셀의 `id_equivalent × gm/ID`(G3-07과 같은 계산). 결과는 기록 + K3 test 판정.
- 누가: 엔진 내부(오라클 계약 C 항목 추가).

### G3-07 [중간] forced 모드 경고 허용오차가 스칼라 하나라 UD 8번 'LUT 계산 허용오차'를 표현하지 못한다
- reference: spice-verification §2 59~62행(멀쩡한 LUT를 오판하지 않으려면 비교 기준이 올바른 정규화를 거쳐야 함), sky130 §12.1 384~386행(비율량과 절대량의 영향 범위가 다름).
- 새 엔진: UD "경고는 forced 모드에서 소자 차이 > LUT 계산 허용오차일 때만", OR `judge.tolerances.ID_rel`·`gm_rel`(스칼라, 기본값 없음), OR C7.
- 문제 유형: 잘못(형식이 결정을 담지 못함).
- 보강안: 스키마 `predictions.devices[].tol{ID_rel, gm_rel}`(소자별, 엔진이 셀 tol에서 계산해 쓴 값) 추가, 오라클은 그것을 우선 사용하고 스칼라는 폴백 금지(없으면 `N/A`). ID_rel = id_equivalent·gm/ID, gm_rel은 같은 셀에서 ln GM LOO로(LC 5절 확장).
- 누가: 엔진 내부.

### G3-08 [중간] 레이아웃 finger_w 변경 뒤 DC 재봉인의 발동 조건이 모호하고, 'diode는 재보정 불필요' 규칙이 부분적으로 틀렸다
- reference: SKILL 332~333행 "finger_w가 LUT 기준폭에서 벗어났다면 §8.3 방식으로 실측 재보정", 344~347행 "조정된 W는 반드시 §5 체크리스트로 재검증한 뒤에만 확정"(§8.3 본문은 stick-diagram 문서, R 323행 인용 "diode 연결 소자는 보정 불필요").
- 새 엔진: M7 189행 MOD8 반복 k의 (3) "finger_w가 LUT `w_ref_m`와 다른 소자는 그 폭 슬라이스로 재평가(diode 연결 소자 제외)" -- 이 단계는 **W_request 루프 반복 안**에만 있다. 수렴 조건(W_requests 비어 있음)이 첫 반복에서 바로 성립하면 재평가가 한 번도 안 돈다. REQ 3.3 `self_biased_diode: true // 재보정 불필요`.
- 문제 유형: 빠짐(발동 조건) + reference 오류(diode 규칙).
- 근거: LCS 표 A·B -- 같은 gm/ID의 ID/W가 폭에 따라 −28 %~+170 %. diode 소자는 ID는 자기 바이어스로 유지되지만 **VGS = 노드전압**이 폭 슬라이스에 따라 바뀐다. 그 노드를 게이트로 받는 미러 출력·캐스코드의 VDS 창(봉인 7)이 바뀐다. "ID가 맞으니 보정 불필요"는 노드전압을 보지 않은 판단이다.
- 보강안: MOD8 진입 조건을 "W_requests 비어 있음"이 아니라 "레이아웃이 고른 (kind, finger_w) 키가 사이징 스냅샷의 폭 키와 하나라도 다름 또는 W_requests 존재"로 바꾼다. 재평가 = 바뀐 폭 키를 읽는 S2 필드만 무효화하고 봉인 1~8 전부 재실행(필드=캐시라 비용은 바뀐 소자 분만). diode 예외는 "ID 재보정 불필요, 노드전압·봉인 재실행은 필요"로 문언 정정(REQ 3.3 주석, R 323행). stick-diagram §8.3 reference도 같은 정정 권고.
- 누가: 엔진 내부. reference 문언 정정은 사용자 승인.

### G3-09 [중간] 준정적(NQS) 검사가 새 엔진에 없고, reference 예제의 준정적 판정 열은 틀렸다
- reference: SKILL 102행 "6. 검증: f_nqs(준정적)", 230행 "`f_nqs = gm/(2π·Cgg)` 계산, `fT ≤ 0.1·f_nqs` 성립하는가?", sky130 §8 211~219행(4행 모두 True, "모든 (VDS, gm/ID) 조합에서 준정적 조건 성립").
- 새 엔진: P·REQ·M15·M6에 nqs/준정적 항목 0건 [실측 grep]. MNA·ngspice BSIM4(기본 NQS 모델 꺼짐)는 둘 다 준정적 모델이라 이 오차를 서로 확인하지 못한다.
- 문제 유형: 빠짐 + reference 오류(0절 표: 3·4행 False, 소자 f_T 773 MHz·23.5 MHz < 1 GHz). NGCC 1단 PMOS f_T 1.69 MHz < GB 10 MHz(sky130 §6)도 무검출.
- 대원칙 충돌: reference의 '0.1' 비율은 상수(WP-03).
- 보강안: `metrics/nqs.py`(레지스트리 변형군): 신호 경로 소자마다 `f_T,dev = gm/(2π·cgg)`(봉인 `ss`에서, 추가 조회 0)와 `ugf_ss_hz`의 비를 기록 metric `nqs_ratio_min`으로. 판정 임계는 spec 선언(출처 필수)일 때만 제약, 없으면 보고만(상수 금지와 양립). reference §8 표·문장 정정(3·4행 False).
- 누가: metric 추가는 엔진 내부, 임계값을 제약으로 둘지는 사용자(스펙).

### G3-10 [중간] 슬루·정착은 SPICE로 검증되지 않는데 오늘 정착 목표가 채택됐다
- reference: SKILL 233행 "Slew-rate 확인: `slew-rate = ID/C = ωT/(gm/ID)`", 81행 스펙 목록(fT 또는 slew-rate).
- 새 엔진: UD 3 "파일럿 정착 목표 논문 값 t_lln 30 ns·t_settle 40 ns 채택", SF F11 "과도 metric이 레지스트리에 없어 보상 목표로만 쓰이고 합격 판정 대상이 아님", OR 측정 = .op/.ac만(.tran 없음). 엔진은 DEC-70 슬루 제약(`ls`)을 가짐.
- 문제 유형: 빠짐(검증 쪽) / 결정 재검토(채택된 정착 목표가 합격에서 판정되지 않음).
- 보강안: 오라클에 `.tran` 측정 하나(입력 계단, 선언 β 루프 구성에서 t_settle·슬루율) 추가, `measure ∈ {slew_rate_vps, t_settle_s}` 스키마 확장. 엔진 `ls` 슬루 예측과의 차를 모델 오차 파일에 기록. 합격 판정에 넣을지는 사용자.
- 누가: 사용자(합격 범위). 구현은 엔진 내부.

### G3-11 [중간] matching: 미스매치 제약이 판정 밖이라 면적 최소화에 반대 압력이 없고, reference의 차동쌍 권고는 틀렸다
- reference: SKILL 169행 "정전류원/전류거울/차동쌍(matching 민감) | Moderate~Strong (qF 크게) | Weak inversion은 mismatch 민감도가 높음(VTo 편차 지배적)", 234행 DoD "Matching: … 충분히 strong 방향인가".
- 새 엔진: SF 181·204행 `mismatch_sigma_mv <= 5.0` = `pending_spice`(judged=false), P U-17·DEC-21(5.0 mV는 시스템 입력), R 47행 `estimate_mismatch_sigma` 식 복사, DEC-23 입력환산 오프셋. 면적은 목적 축(DEC-79).
- 문제 유형: reference 오류 + 빠짐.
- 내용: (1) 전류 미스매치 σ(ΔI/I) ≈ (gm/ID)·σVT는 gm/ID가 클수록 나빠지므로 미러·전류원에는 reference 권고가 맞다. 입력환산 오프셋 σVos² ≈ σVT² + (ID/gm)²·(σβ/β)²는 gm/ID가 클수록 **줄어든다** -- 차동쌍을 같은 줄에 둔 것은 틀렸다. (2) 미스매치가 판정되지 않으면 면적 최소 front 끝점이 매칭 소자 W·L을 최소로 밀어 Pelgrom σ ∝ 1/√(WL)이 커져도 막지 않는다.
- 보강안: (a) MOD5 오프셋 metric을 Pelgrom 두 항(A_VT, A_β)과 소자별 gm/ID 가중으로 계산하고, 계수는 PDK 미스매치 파일(sky130 §3 37~38행이 이미 include하는 `__mismatch.corner.spice`의 slope 파라미터)에서 읽는다(상수 금지와 양립). (b) 그 계수를 SPICE Monte Carlo 소수 표본으로 1회 대조해 '7a 재도출'(U-17)을 실제로 수행. (c) SKILL 169행을 미러/전류원 대 차동쌍으로 나눠 정정.
- 누가: (a)(b) 엔진 내부, 미스매치를 판정 제약으로 올릴지·값은 사용자(U-17).

### G3-12 [중간] GB4 블록 국소 상한이 실제 상한인지 검증하는 장치가 없다
- reference: spice-verification §3 79~88행 -- leading-order·국소 근사가 "M10/M19(저컨덕턴스 바이어스 싱크)를 모델링하지 않아" 최대 49 dB·부호 반대 오차, "소자가 하나만 추가되면 다시 실패할 수 있다", 100~103행 일반 원칙(수치 MNA를 기본).
- 새 엔진: M15 3.5 GB4 `achievability.py` = 블록 국소 모델 + 격자 최대 gm/gds 상한표, INFEASIBLE 판정 전용. 엔진 정밀 경로(DEC-73)는 범위 밖(R D18).
- 문제 유형: 빠짐(검증) -- 국소 모델이 블록 노드에 물린 저컨덕턴스 소자를 빠뜨리면 상한이 실제보다 **낮아져** 가능한 설계를 INFEASIBLE로 잘라낸다.
- 보강안: 불변식 test `test_gb4_bound_dominates_mna`: 9회로 탐색 중 봉인 통과 스냅샷마다 블록 이득(전회로 MNA에서 블록 경계 노드 비)이 GB4 상한 이하인지 검사, 위반 1건이면 FAIL. 국소 모델의 소자 집합 = 블록 노드에 단자가 닿는 S1 소자 전부(이름·역할로 거르지 않음)로 계약에 명시.
- 누가: 엔진 내부.

### G3-13 [중간] SKILL.md가 회로별 위상보상 함수(topology_library)를 지시한다 -- 오늘 대원칙 3과 충돌(reference 낡음)
- reference: SKILL 141~143행 "어느 topology에 어느 공식을 쓸지는 … 그 표에 없는 조합이면 … 새로 유도해 `topology_library.py`에 추가한다", 154~157행 "connectivity/matching kind/위상보정 함수 참조를 그 파일에서 로드", 214~215행(Miller·NGCC·NMCNR 회로별 sizing), 412~420행(topology_fn 참조). sky130 §11 279~355행 전체가 회로별 `topology_fn` 전제.
- 새 엔진: UD 대원칙 3 "회로별 분기·회로별 함수(옛 compensation.function: miller_ota_topology/nmcnr_3stage_topology 등) 금지", SF 397행 GB5 일반 규칙으로 대체, M15 146행.
- 문제 유형: 충돌 / reference 낡음.
- 보강안: SKILL §1.5 '수동 보상소자'·§4 표·참조 파일 목록을 "GB5 일반 규칙(S1v 극점 노드 + `compensation_targets`)이 정본, `topology_library.py`는 옛 엔진 대조 오라클"로 개정. 단 reference가 확보한 닫힌형 결과(NGCC Table 4: gm1 0.105 mS·gm2 0.186 mS·gm3 2.5 mS, NMCNR 4-노드 KCL 해, sky130 §11 323·§12.3 413~419행)는 **GB5 일반 규칙의 손계산 오라클 test**로 승격(ROADMAP oracles (ii)).
- 누가: SKILL 개정은 사용자 승인. 오라클 test 승격은 엔진 내부.

### G3-14 [낮음] free 모드 FAIL의 원인 분류(경계조건 대 구조 한계)를 오라클이 자동으로 내지 않는다
- reference: spice-verification §1 23~36행 "경계조건(전압 배분) 문제라면 재조정 … 구조적 문제라면 회로의 실제 한계(발견)로 보고 … 구분하는 것", 20~22행 공유 바이어스 노드 사후 대조.
- 새 엔진: OR는 free/forced를 각각 판정·기록, R Z1~Z9 "원인 → 해당 단위 수정"(수동). G7 233행 `test_shared_gate_single_voltage`(엔진 쪽)만.
- 문제 유형: 빠짐(진단).
- 보강안: `oracle_compare`에 `diagnosis` 칸: (a) forced KCL 잔차 ≤ 소자 tol_I 합 + free FAIL → '엔진 DC 정합, free 수렴/고임피던스 노드 문제'(경계조건 쪽), (b) forced 잔차 큼 → '엔진 DC 비정합'(G7 결함), (c) forced에서 게이트 공유 넷 소자들의 등가 ΔVGS(= ΔID/gm) 최대 차를 넷별로 기록(reference 4단계 신호를 이분탐색 없이 얻음).
- 누가: 엔진 내부.

### G3-15 [낮음] PVT 코너·온도가 TT 27 °C 하나다
- reference: sky130 §10 274행 "corner는 tt(typical)만 -- ff/ss 등 다른 corner는 미실행".
- 새 엔진: P 164행 "LUT는 TT·기록된 온도 한 조건", OR C2(npz corner·temp를 그대로).
- 문제 유형: 빠짐(범위 밖으로 확정됨).
- 보강안: 합격 판정은 TT 유지, 오라클이 같은 넷리스트를 ss/ff·온도 끝점으로 재실행해 '기록만' 표(엔진 LUT 재생성 없이 가능 -- 모델 include의 `{corner}`만 바꿈)를 내는 옵션. 판정에 넣을지는 사용자.
- 누가: 사용자.

### G3-16 [낮음] 잡음·왜곡이 SKILL DoD에 있으나 계획 범위 밖이다
- reference: SKILL 236행 Noise, 238행 Distortion, 170행 1/f.
- 새 엔진: P 163행(잡음은 7b 이후 제약, 저잡음 요구 회로는 적용 조건 밖), LRP D5(SID_1F 단위 V/√Hz 오기).
- 문제 유형: 충돌(reference DoD 대 계획 범위).
- 보강안: 9회로 spec 로더가 잡음·왜곡 metric 선언을 만나면 `unsupported_metric`으로 정지(조용히 무시 금지), 결과 JSON에 '잡음·왜곡 미검증'을 명시. SKILL DoD에 '새 엔진 범위 밖' 주석.
- 누가: 사용자(9회로 중 잡음 스펙 유무 확인).

### G3-17 [낮음] SKILL·sky130의 gm/ID 상한 상수는 낡았고 조건이 틀렸다
- reference: SKILL 187~190행 "sky130 LUT 실측 상한은 NMOS 29.93 / PMOS 32.20 S/A", sky130 §4 64행.
- 실측: 0절 표 -- NMOS 29.93은 VS 0.8 V·VDS 0.075 V(비포화) 점, VS 0에서는 27.43. PMOS는 지금 LUT 전체 최대 32.60.
- 새 엔진: LC `curve_report`가 (kind, L, VDS, VS)마다 계산(상수 없음) -- 새 엔진은 이미 맞다.
- 보강안: SKILL 2.1-3 문장을 "상한은 `curve_report`가 조회 조건마다 계산한다(상수 아님)"로 개정.
- 누가: reference 개정은 사용자 승인. 엔진 변경 없음.

### G3-18 [낮음] sky130 예제의 격자·시간·함정 목록이 낡았다
- reference: sky130 §2 22행 L 4점, 28~31행 "40회 … 약 55분", §3 33~60행 함정 목록.
- 실측·근거: L 12점(0절), LRP 1.3 "옛 생성기 291 s/조합(점마다 plot 누적), `destroy all`로 3.5 s, 결과 비트 동일", LRP 1.3 stderr 혼입 파싱 결함, SH 2단계 "ngspice는 모델 bin을 `nf`로 나누지 않은 총 W로 고른다(W=10u nf=2가 12 % 작고, 총 W>100 µm면 모델 못 찾음)", SH 3.1 VSB > 0.8 V 외삽 ID −35~−97 %, oracle_compare 24행 BSIM `vbs` 부호.
- 문제 유형: reference 낡음(빠진 함정).
- 보강안: sky130 §3에 위 5개 함정을 추가(특히 `nf` 대신 `m`, `destroy all`, VS 축 상한), §2 표를 현재 npz와 LRP 계획으로 갱신.
- 누가: 사용자 승인(reference 개정).

### G3-19 [낮음] sky130 §5의 W≈24660 µm는 재현되지 않는다
- reference: sky130 §5 74~81행 "W≈24660µm … 정정 전 2466µm".
- 실측: 같은 점에서 §4 시험 스펙(fT 100 MHz, CL 1 pF)이면 W = 7191 µm(gm/ID 20) / 6295 µm(19.65). 어떤 ID를 썼는지 문서에 없다 [추측: 다른 gm 가정 또는 배율 정정을 잘못 적용].
- 보강안: 그 절에 사용한 ID(또는 gm)를 적고 재계산 값으로 정정. 결론(PMOS 저이동도로 W 폭증)은 유지.
- 누가: 사용자 승인(reference 개정).

### G3-20 [낮음] spice-verification·sky130의 경로·행 번호·그림 번호가 낡거나 서로 모순된다
- reference: spice-verification 90~94행 "`_mna_solve_smallsignal()`(`assets/sizing_recipe.py:2395` …) `_full_circuit_devices()`/`_full_circuit_response()` 같은 파일 :2815/:2850" -- 현재 `legacy/sizing_recipe.py` 4674·4935·4970행(M15 3.1). sky130 §13.1 454행 "Figure 3는 오탈자(Figure 2가 맞음)" 대 529~530행 "Fig.3는 오탈자, 실제 참고 다이어그램은 Fig.4" -- 같은 문서 안에서 다르다. 530행 "아직 미반영 -- 배치 7 이후 세션에서 확인" 미결 TODO.
- 보강안: 경로를 `legacy/`와 함수 이름 기준으로(행 번호 제거), §13 그림 번호 한 가지로 정리, TODO는 해소 여부 기록.
- 누가: 사용자 승인(reference 개정).

### G3-21 [낮음] 옛 이득 이중 곱 버그의 재발 방지 test가 계약에 없다
- reference: sky130 §9 256~262행 "`result.gain = gm_id * lut.gm_gds_ratio(...)` … 이미 완전한 gain(gm/gds)을 반환하는데 gm_id를 한 번 더 곱하고 있었다(gm/ID=20에서 49.4 대신 987.2)".
- 새 엔진: LC `op_point.gm_gds = exp(lnGM − lnGDS)`. 이득은 MNA(M15 3.4).
- 보강안: `tests/metrics/test_gain.py`에 단일 CS + 이상 전류원 부하의 `gain_ss_db` = 20·log10(op_point.gm_gds) 손계산 대조(이중 곱이면 gm/ID배 어긋나 red).
- 누가: 엔진 내부.

### G3-22 [낮음] M15 2.7의 tol_V 정의(L 축 LOO)가 UD 11과 어긋난다(계약은 이미 정정)
- reference: (간접) sky130 §9 264~265행 "L/VDS는 격자값만 시도"(L 이산), spice-verification §2(비교는 엔진이 실제로 쓰는 경로로).
- 새 엔진: UD 11 "L 도 LUT 앵커 이산값만(L 보간 금지), tol_V 는 남은 보간 축(VGS·VDS·VS) 기준 셀별", LC 9·165행 r2 정정 완료, M15 2.7(L 축 LOO)·TV(L 축 LOO 측정)는 옛 정의. LRP 8절도 지적.
- 문제 유형: 충돌(design 문서 낡음).
- 보강안: M15 2.7·O1과 TV 머리에 'LC 5절 r2로 대체됨' 표시. 엔진이 하지 않는 연산(L 보간)의 오차를 허용오차로 쓰지 않는다는 원칙(reference §2 정신)을 계약 머리에 한 줄.
- 누가: 엔진 내부.

### G3-23 [낮음] SKILL 최종 게이트 (c) 최적성의 증거가 결과 JSON에 없다
- reference: SKILL 283~286행 "(c) 최적성: … D유형 탐색이 실제로 objective를 최소/최대화하는 θ*에 수렴했는지 확인하고, 탐색 없이 임의로 고른 첫 feasible 후보로 멈추지 않았는지".
- 새 엔진: M6 SLSQP 국소 해 + ε-제약 + L-b 이산 탐색, 모델 오차 측정 전 front는 '추정'(M6 193행). 수렴 증거 기록 형식은 없음.
- 보강안: front 점마다 `optimality{slsqp_status, kkt_residual, active_constraints, n_starts, start_spread, lb_rounds}`를 S3·결과 JSON에 기록하고, 시작점 1개뿐인 점은 '국소 최적(다중 시작 없음)'으로 표시.
- 누가: 엔진 내부.

### G3-24 [낮음] SKILL §7 보고서 8절과 MOD9 산출의 대응이 정해지지 않았다
- reference: SKILL 364~373행 8개 섹션(특히 §6 "스냅된 W로 재검증한 SPICE 결과", §8 물리 floorplan 필수), 383~386행 시각 검증.
- 새 엔진: REQ 3.1 `report`(result_json·front_table·instance_adapter·html), 섹션 정의 없음.
- 보강안: MOD9 design에 8섹션 ↔ graph 필드 대응표(§3 = S2 dc·ss, §5 = MOD7 행 Euler, §6 = G3-03 기하의 오라클 compare.json, §8 = floorplan) 추가. `legacy/report_template.html` 렌더 함수 재사용 여부는 대원칙 '기능별 파일'과 함께 결정.
- 누가: 엔진 내부(범위 축소 시 사용자).

---

## 2. 새 엔진이 reference와 이미 맞는 것 (확인만)

- 수치 MNA 기본(spice-verification §3) -- M15 3.3 조립 1회·ω별 풀이, gmb 스탬프 추가, VCCS 등가회로 ngspice 오라클(R oracles (iv), M1 완료 조건) = reference 96~98행 '독립 시뮬레이터 교차검증'과 같다.
- W 정규화(spice-verification §2, sky130 §12.1) -- LC `IDu = ID·L/w_m`(슬라이스 폭 메타), 용량 기준폭 `w_ref_m` 기록·추론 근거 provenance. 하네스 박힌 `_W_REF` 미사용.
- 폭 의존(sky130 §10 271행 "여러 기준폭 교차검증 권장") -- E5 폭 슬라이스, 폭 사이 보간 금지.
- op-info 용량 불신(sky130 §7) -- LUT 용량은 AC Y-parameter(LRP 5절, 부호 보존), 오라클은 용량을 op-info로 읽지 않는다.
- square-law 다리 금지(sky130 §6) -- SF가 회로 전용 키·논문 값 무단 채택을 거부. 다만 논문 스펙에 VDSAT 수치가 오면 `2/(gm/ID)`로 바꾸지 말고 G3-01의 LUT VDsat 제약으로 받아야 한다(ngcc spec 작성 때 확인).
- 비현실 W 처리(SKILL 2.1-1) -- `gm_id_for_target(W=…)` 역산 + MOD8 W 고정 재풀이.
- 대칭 trail(SKILL §6 `check_mirror_symmetry`) -- M7 `mirror_trail.py` 복사.

## 3. 대원칙과 충돌하는 reference 권고

| reference | 권고 | 충돌 원칙 | 처리 제안 |
|---|---|---|---|
| SKILL 99행 | 기생 반복 "3~4회" | 상수 금지 | 반복 상한은 N3.6 K_max 식(이미 새 엔진 방식) |
| SKILL 230행 | `fT ≤ 0.1·f_nqs` | 상수 금지 | G3-09: 기록 metric + spec 선언 임계 |
| SKILL 141~157·214행, sky130 §11 | 회로별 topology_fn·보상 함수 | topology 종속 금지(대원칙 3) | G3-13: 일반 규칙 + 닫힌형 결과는 오라클 test로 |
| SKILL 166~170행 | inversion 영역 권고표(qF 0.1~1 등) | 상수 금지(시작점·bounds에 쓰면) | 시작점은 층 0 역산(M6 6.1), 표는 설명용으로만 |
| SKILL 52~63행 | harness 함수 우선(옛 `run_sizing_pipeline` 등) | 옛 엔진은 참고·대조 기준선(UD) | 새 엔진 진입점 `run_gmid_design_pipeline`으로 SKILL 개정 필요(G3-13과 같은 개정 묶음) |
| spice-verification §1 2~3단계 | 소자마다 게이트 이분탐색 | 반복 계산 금지(직접 충돌은 아님) | G3-14: forced 모드 등가 ΔVGS = ΔID/gm로 이분탐색 없이 같은 신호 |

---

## 4. 요약표

| 심각도 | 개수 | ID |
|---|---|---|
| 높음 | 4 | G3-01, G3-02, G3-03, G3-04 |
| 중간 | 9 | G3-05 ~ G3-13 |
| 낮음 | 11 | G3-14 ~ G3-24 |
| 합계 | 24 | 유형: 빠짐 11, 잘못 2, 충돌 5, reference 오류·낡음 7(일부 중복 분류), 결정 재검토 2 |

## 5. 상위 5개 권고

1. **G3-01 포화 정의 통일**: 엔진 VDsat = LUT `VDSAT` 열(BSIM op, U-27 재생성에 추가) = 오라클과 같은 양. 봉인 7의 `−tol_V` 완화를 SPICE 판정보다 보수적인 방향으로 뒤집는다. 그렇지 않으면 엔진 통과 해가 SPICE에서 비포화 FAIL이 될 수 있다.
2. **G3-02 접합 용량 반영**: LUT에 CDD/CDB·CSB 열(LRP D6), MNA d–b·s–b 스탬프, 확산 기하는 레이아웃 산출에서 엔진·오라클에 같은 값. 오라클 `diffusion`은 합격 실행에서 필수.
3. **G3-03 합격 SPICE 기하 = MOD8 수렴 레이아웃 기하**로 명시(옛 PM 79°→18° 사례). R 표의 철회된 'W 정본' 문장 정정.
4. **G3-04 W 허용오차의 tol_V 지표를 `id_equivalent`로 명시**(사용자 확인). `gm_id_inverse`면 상한이 수백 %가 되어 W 보존 규칙이 무력해진다.
5. **G3-06·G3-08 검증 분해 장치**: 오라클 단독 소자(`--bias iso`) 모드로 LUT 충실도를 회로 DC와 분리하고, 레이아웃이 폭 키를 바꾸면 W_request 없어도 봉인 1~8을 재실행(diode도 노드전압은 재계산).
