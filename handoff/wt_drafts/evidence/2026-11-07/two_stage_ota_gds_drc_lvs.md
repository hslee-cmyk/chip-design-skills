# two_stage_ota -- 손 레이아웃 → GDS → KLayout DRC·LVS (2026-11-07)

앞 문서 `two_stage_ota_hand_design_layout.md`의 손설계 최종점(run6/final_5)과 행 손가락 열(`two_stage_ota_design_for_layout.json`)을 실제 GDS로 만들고 sky130 KLayout 덱으로 검증했다. 엔진·계획·topology 수정 0, 커밋 0.

## 0. 돌린 것

| 항목 | 경로 |
|---|---|
| PDK 규칙 선언(층 번호·치수 값 + 출처 줄) | `C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/layout/sky130_layout_rules.json` (값 출처 `C:/pdk/skywater-pdk/docs/rules/periphery/periphery.csv` 줄 번호, 층은 `sky130A_mr.drc:146-205`) |
| GDS 생성 스크립트(KLayout Python) | `.../layout/gen_gds.py` -- 숫자 0, 모든 치수는 규칙 선언의 역할 이름 |
| 실행 묶음(생성·DRC·LVS) | `.../layout/run_flow.ps1 <tag> gen|drc|lvs` |
| LVS 회로(CDL) | `.../layout/two_stage_ota.cdl` |
| 레이아웃 뒤 SPICE | `.../layout/post_layout_spice.py`, 결과 `.../layout/postlayout/post_layout_spice.json` |
| 도구 | KLayout 0.30.12, 덱 efabless/sky130_klayout_pdk `dace5183` (`C:\pdk\sky130_klayout_pdk.PROVENANCE.txt`) |

실행 메모: `klayout_app.exe`는 GUI 서브시스템 실행 파일이라 PowerShell 호출 연산자(`&`)는 끝나기 전에 돌아온다 -- `Start-Process -Wait`로 기다려야 결과가 맞다(`run_flow.ps1`의 `KL` 함수).

## 1. GDS

- 경로: `C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/layout/two_stage_ota.gds`, 43,496 B, sha256 `F81792754F5840211620E5FC4C1956B929E46E9110384D7A9FD4272B7F3EA85B`.
- 결정성: 같은 입력으로 3회 생성 → sha256 3/3 같음(GDS 타임스탬프 끔 `gds2_write_timestamps = False`).
- 외곽 25.74 × 10.155 µm = 261.4 µm². 행(확산) N 22.09 µm(w_s 0.58) · P 19.43 µm(w_s 1.26), 두 행 가운데 정렬(같은 대칭 축).
- 구조(아래→위): p-tap 띠 | N 행 gate li 단 3개(bias·vin_n·vin_p) | N 확산 | N S/D met2 버스 5개(OUT·gnd·CS·D3·O1) | P 행 gate li 단 2개(O1·D3) | P 확산 | P S/D met2 버스 4개 | n-tap 띠. nwell은 P 행과 n-tap을 덮는다.
- 행 밖으로 나가는 넷 8개(D3·O1·OUT·bias·gnd·vdd·vin_n·vin_p)는 왼쪽 met1 세로 riser 하나씩, 버스는 자기 riser까지 연장해 via/mcon으로 연결. 다른 넷끼리의 교차는 언제나 다른 층(li·met1·met2) -- 금속 3층 불필요.
- 손가락 배치는 손 레이아웃 그대로(Euler 경로 1개/행, 끊김 0, ABBA, 축 대칭). 확산 공유: N 행 노드 열 OUT·gnd·…·gnd | CS | D3·CS·… | O1·CS·… | … (생성 스크립트가 손가락 열에서 Euler 걸음으로 S/D 방향을 정함 -- 끊기면 정지).
- 넣지 않은 것(판단): Cc(MIM 674 µm², MOS 외곽의 2.6배)·Rz -- 자리(종횡비·met3/met4 MIM 층)를 정하는 일이라 이번 범위 밖으로 남김. dummy 손가락·가드링 없음. 배선 RC 추출 없음.

## 2. DRC (sky130A_mr.drc, feol + beol)

| 반복 | 위반 | 규칙 | 원인 | 수정 |
|---|---|---|---|---|
| it1 | 8 | `m2.5` (via 인접 두 변 met2 감싸기 0.085) | riser 쪽 버스 끝에서 via가 met2 끝에서 0.055만 들어감 | 버스를 via 진행 방향으로 `m2_encl_via_adj`만큼 연장(`gen_gds.py` 주석) |
| it2 | **0** | -- | -- | -- |

최종 남은 위반 0(181 규칙 범주). 이 덱(`_mr`)이 검사하지 않는 규칙(밀도·안테나 등)은 이 결과로 통과를 말할 수 없다.

## 3. LVS (sky130.lvs, 기본 옵션 = netlist simplify)

- 회로: `two_stage_ota.cdl` -- 손설계 7소자(W = m·w_s, 손가락은 LVS가 병렬로 합침), body nmos = gnd, pmos = vdd, Cc·Rz 제외(레이아웃에 없음).
- 결과(it2): **"Congratulations! Netlists match."** (rc 0). 핀 = 라벨 6개(vdd·gnd·vin_n·vin_p·OUT·bias), 내부 넷 CS·D3·O1은 추출 이름 `$7·$9·$8`로 위상 대응.

## 4. 추출 넷리스트 대 손 레이아웃 기하

| 소자 | m | W 추출 [µm] | L | AD=AS 추출 [µm²] | 손 ad / as [µm²] | PD=PS 추출 [µm] | 손 pd / ps [µm] |
|---|---|---|---|---|---|---|---|
| M1 | 8 | 4.64 | 0.5 | 0.6496 | 0.6496 / 0.6496 | 6.88 | 2.24 / 2.24 |
| M2 | 8 | 4.64 | 0.5 | 0.6496 | 0.6496 / 0.6496 | 6.88 | 2.24 / 2.24 |
| M5 | 2 | 1.16 | 0.5 | 0.1624 | 0.1624 / 0.1624 | 1.72 | 0.56 / 0.56 |
| M7 | 10 | 5.80 | 0.5 | 0.8845 | 0.9744 / 0.8120 | 9.43 | 4.52 / 2.80 |
| M3 | 4 | 5.04 | 0.7 | 0.7056 | 0.7056 / 0.7056 | 6.16 | 1.12 / 1.12 |
| M4 | 4 | 5.04 | 0.7 | 0.7056 | 0.7056 / 0.7056 | 6.16 | 1.12 / 1.12 |
| M6 | 18 | 22.68 | 0.35 | 3.3327 | 3.528 / 3.175 | 29.23 | 8.12 / 5.04 |

- W·L: 7/7 일치.
- 면적: 합 일치. 추출은 소자 안에서 AS = AD로 평균(M7·M6의 끝 확산 비대칭이 평균으로 사라짐).
- 둘레: **정의가 다르다** -- 추출 PS/PD는 gate 쪽 변(W)을 포함한 확산 둘레, 손 기하는 gate 변을 뺀 둘레(공유 확산은 반씩). sky130 모델은 `permod = 1.0`(`C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice:47`, pfet `:69`) -- BSIM4에서 perMod = 1은 PS/PD가 gate 변을 포함한다는 뜻이라, 추출 쪽이 모델 정의와 맞고 손 기하 쪽이 모델에 덜 들어간다(판정: 조건부 -- BSIM4 문서 쪽 대조는 안 함, 모델 파라미터 줄만 확인). ngspice 경고는 두 경우 모두 0.

## 5. 레이아웃 뒤 SPICE 재대조 (같은 시험대: bias = 이상 전압원, final_5)

손가락마다 w_s·L은 그대로, ad/as/pd/ps만 추출 합 ÷ m으로 바꿈(배선 RC 없음).

| 양 | 레이아웃 전(손 기하) | 레이아웃 뒤(추출 기하) | 차 |
|---|---|---|---|
| gain [dB] | 71.7895 | 71.7895 | 0 |
| GBW [MHz] | 6.99999 | 6.99981 | −0.003 % |
| PM [deg] | 71.14 | 71.13 | −0.01° |
| 전원 전류 [µA] | 42.18 | 42.18 | 0 |

접합 기하 차이는 이 회로의 GBW·PM을 거의 움직이지 않는다. 배선 기생(버스 길이 ~22 µm, riser)은 재지 않았다 -- 이 표는 '레이아웃 뒤'의 소자 기하 몫만이다.

## 6. 드러난 것

1. **배선이 면적을 지배한다.** 손 외곽 추정 112 µm²(행 + tap + 간격만)에 대해 실제 GDS는 261 µm²(2.3배). 늘어난 몫: gate li 단(행마다 넷 수 × 0.34 µm), S/D met2 버스(행마다 넷 수 × 0.40 µm), 왼쪽 riser 8개(3.3 µm 폭). 확산 면적 비 14 %. 사이징 단계의 '가벼운 기하'(J2)에 넣을 면적은 행만이 아니라 **행마다 gate 넷 수·S/D 넷 수**에 비례하는 띠를 포함해야 판정 축 면적이 맞다 -- 이 두 수는 손가락 열(Euler 걸음)에서 정해지는 정적 양이라 닫힌 식으로 들어간다.
2. **확산 둘레 정의 불일치**(§4) -- 엔진·손 기하의 pd/ps 정의가 모델 perMod와 같은지 확인해야 할 정의 동일성 항목(원칙 2: 수치 아님, 정의).
3. **레이아웃 뒤 소자 기하 효과는 작다**(§5, 이 회로 이 점). 큰 차이가 날 곳은 배선 기생과 Cc 자리(MIM이 외곽보다 큼)다.
4. GDS 생성기는 손가락 열 + 규칙 선언만으로 DRC 0·LVS 일치를 한 번 수정으로 냈다 -- 행 구성·버스·riser 꼴은 규칙화가 된다.

## 7. 분류 추가분 (앞 문서 분류표에 덧붙일 것)

**코드로 일반화 (규칙으로 선다, 회로 이름 0)**
- 행 손가락 열 → Euler 걸음으로 S/D 방향·노드 넷 열(끊기면 정지). 손가락 열이 정해지면 결정적.
- gate 단 배치(행마다 gate 넷 수만큼 li 단, 단 피치 = max(li 폭+간격, licon 폭+간격)), S/D 버스(넷마다 met2 한 줄, 피치 = via 감싼 met2 + 간격), 행 밖 넷 riser(met1) -- 교차는 층으로 분리.
- tap 띠(p-tap·n-tap), nwell 감싸기, 주입층 감싸기, npc, 최소 면적 보정.
- 규칙 값은 PDK 선언 한 곳(`sky130_layout_rules.json` 꼴, 역할 이름 + 출처 줄) -- O-197 꼴.
- 판정 축 면적의 닫힌 식: 행 길이 + (gate 넷 수 × 단 피치) + (S/D 넷 수 × 버스 피치) + riser 수 × riser 피치 + tap·간격.
- DRC·LVS 실행과 결과 집계(규칙별 위반 수, 일치 여부), 추출 넷리스트 → 소자 기하(ad/as/pd/ps) → 실현 재평가 입력.

**AI가 맡으면 좋은 것 (스크립트 + 의도 문서로 재현)**
- DRC 위반의 원인 판독과 생성 규칙 수정(이번 `m2.5`처럼 규칙 해석이 필요한 수리). 반복이 몇 번이면 끝나는지는 규칙화가 안 된다.
- 배선 위상 결정: 어떤 넷을 어느 층·어느 쪽(위/아래)으로 뺄지, riser 순서, 넷 길이 균형(차동 경로 대칭), 민감 넷 차폐 -- 이번에는 가장 단순한 꼴(전부 왼쪽 riser)을 골랐고 대칭 배선은 아니다.
- Cc(MIM)·Rz 자리와 종횡비, dummy·가드링, 행 접기.
- 추출 둘레 정의처럼 '도구 간 정의 차'를 찾아내는 일.

**사용자 결정**
- Cc를 MOS 블록 위(met3/met4 MIM, 겹침 허용) 또는 옆에 둘지, 목표 종횡비.
- 배선 RC 추출까지 레이아웃 뒤 판정에 넣을지(지금 도구로는 KLayout 기생 추출 덱 확인 필요).
- 손 기하·엔진의 pd/ps 정의를 모델 perMod(= gate 변 포함)에 맞출지(정의 동일성 -- 원칙 2).
- 덱 `_mr`가 검사하지 않는 규칙(밀도·안테나)을 어디서 볼지.

## 8. 남은 불확실

1. 배선 기생 미추출 -- §5는 소자 기하 몫만.
2. BSIM4 perMod 의미는 모델 파라미터 줄로만 확인(문서 쪽 대조 안 함).
3. dummy 없음 -- 행 끝 소자(M7·M6 바깥 손가락)의 LOD·WPE 차이는 이 GDS로 보지 않았다(LVS 덱의 LOD 파라미터 sa/sb 추출 안 함).
4. riser 배선은 대칭이 아니다(전부 왼쪽) -- 차동 경로 길이 차가 있다(재지 않음).
5. 이 결과는 한 회로 한 점이다.

## 9. 규칙 준수

- heredoc·`python -` 계열·`python -c` 대입·`sed -i` 0회. 엔진·계획·topology 수정 0, 커밋 0.
