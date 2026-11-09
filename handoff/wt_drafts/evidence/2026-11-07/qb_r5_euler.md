# QB R5 측정 -- Euler 경로 손가락 기준 (사용자 제안, 2026-11-07)

작성 2026-11-07, 측정 agent(문서·분석). **권고 없음** -- 사실·비교·물리 판정만 적는다.
사용자 원문: "오일러패쓰가 기준이 될 수 있을 것 같은데? 같은 스테이지에 있는 kind가 같은 소자들을 하나의 오일러패쓰로 묶을 수 있는 핑거수가 기준이 될 것 같아." 추가 지시(오케스트레이터 전달): "전류미러비는 가장 우선 되어야 하고." + 정정 M-1·M-2·M-3(`qb_question_contradiction_check.md`).
대상 엔진 = master `faf69218`(v3와 같은 엔진). 원칙 8 용도 제한: 엔진 인용은 (1) 엔진 밖 사실(LUT·PDK 값) (2) 재작성 범위로만 쓴다.
O-229 아래: 엔진 수정 0, 커밋 0, pytest 0, ngspice 0.

## 0. 돌린 것

- 측정 worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261107-qb-r5`(`git -C …/chip-design-skills worktree add --detach … master` = faf69218). 측정 뒤 추적 파일 변경 0 확인 후 `worktree remove`(§9).
- 스크립트(새로 씀, `C:/Users/HSLEE/AppData/Local/Temp/la1s_qb5/scripts/`):
  - `qb5_probe.py` -- 회로마다 R0 탐색 평가 1회로 정본 필드(`graph.matching_groups`·`matching_dispositions`·S1 `bulk`·`dc_coord`)·도달 슬라이스 키를 확인. 출력 `out/qb5_probe.txt`.
  - `qb5_r5.py` -- 점마다 R0·R1·R3(v3 정의 그대로 복사) + R5 네 변형(body 조건 없음/있음 × w_s 둘째 기준 (가)/(나))을 탐색 평가 → 실현 평가(`evaluate(..., realized=RealizedFinger(...))`, v3 `qb2_rules_realize.py`와 같은 호출). 출력 `out/qb5_r5.txt`.
  - `qb5_summary.py` -- 요약. 출력 `out/qb5_summary.txt`.
  - 실행기 `la1s_qb5/run_seq.py`(v3 `la1s_qb3/run_seq.py` 복사, worktree 경로만 바꿈): 회로마다 별도 프로세스로 하나씩, 착수 전 여유 < 3.7 GB면 10 s sleep 대기, 실행 중 < 1 GB면 그 자식 PID만 정지. 기록 `out/*.runlog`.
- 명령: `OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8 C:/Python314/python.exe -P run_seq.py scripts/<script> out/<out> <회로,…>`(회로 7개 = v3와 같음), 요약은 `C:/Python314/python.exe -P scripts/qb5_summary.py out/qb5_r5.txt out/qb5_summary.txt`.
- 점: v3와 같다(회로마다 층 0 출발 θ `Pipe.theta0`, two_stage_ota는 손 봉인 점 HS 추가). 7회로 모두 층 0 출발점이 있어 ALT 점은 쓰지 않았다.
- **규칙 위반 1건(자기 기록)**: 준비 중 한 Bash 줄에서 `la1s_qb3/patch_copies.py --help`와 `python -P -`(stdin = /dev/null)를 실수로 실행했다. `patch_copies.py`는 이미 표지된 복사본을 건너뛰는 1회 패치라 아무 파일도 바꾸지 않았다(`la1s_qb3/scripts/*` mtime 07:05·07:07 그대로 확인). `python -P -`는 빈 stdin으로 곧 끝났고 떠돌이 프로세스는 없었다(프로세스 목록 확인). 그 줄은 TaskStop으로 멈췄다.

## 1. R5 정의 (측정용 가정 -- 확정 아님)

| 항목 | 측정용 가정 | 출처·근거 |
|---|---|---|
| stage | **엔진 정본 S1v `graph.views`** 전달 뷰 블록의 `stage`(DEC-57·FR-1 유도 결과). 하네스(generality `Pipe`)는 S1만 만들어 평가 스냅샷에 S1v가 없으므로, 같은 프로세스에서 단계 A `run_stage_a`(build_s1 + build_s1v, structure.json 사실 포함)를 불러 그 결과를 읽었다. 뷰 = gain 제약 전달 뷰(`s1v_fields._constrained_keys(..., gain_ss_db)` 키가 같은 뷰), 없으면 첫 전달 뷰(`l_classes._main_path_starts`와 같은 규칙). 소자가 그 뷰 블록 여럿에 들면 최솟값(`writer_plan._stages`와 같은 읽기). 블록에 없는 소자 = stage None(그 kind의 None 묶음 -- **측정용 가정**) | `gmid_engine/pipeline/stage_a.py:206`, `graph/s1v_values.py` `Block.stage`, `graph/l_classes.py:49`, `sizing/writer_plan.py:118` |
| 묶음 G | (stage, kind) -- 변형 'b'는 (stage, kind, body). body = S1 `device.bulk`의 `.net`(DEC-61 kind별 기본 레일 포함 -- `convergence/layout_input.py`와 같은 읽기) | 사용자 원문 + LR8 물리 행 |
| 미러 묶음 | **정본** `graph.matching_groups` 중 `kind == mirror`(writer `s1_matching_groups`). 측정 스크립트는 묶음을 새로 만들지 않는다(M-1). 연결 직접 묶음(v3 정의)은 대조용으로만 따로 셈 | DEC-93 (1), U-06, `graph/matching_groups.py` |
| 확산 그래프 | 꼭짓점 = S·D 넷, 손가락 하나 = 그 소자 S–D 변 하나(m 손가락 = 평행 변 m개). S = D인 소자는 차수에 넣지 않음. 연결이 아닌 묶음은 연결 성분마다 경로 하나 | 지시 |
| 공유 w_s 후보 | 묶음 소자 전부에서 W(k)가 정의되는 도달 슬라이스 키의 교집합. 한 소자라도 W(k) 정의 불능인 키는 뺀다. 교집합이 비면 **정지 기록**(폴백 없음, M-2) | 원칙 10 |
| m 후보 | 키마다 {f, f+1}, f = max(1, ⌊W/(k·g)⌋) -- W에 가장 가까운 아래·위 정수(두 홀짝이 다 들어간다). 미러 비를 위해 m을 더 키우는 것은 키(w_s)를 좁히는 것으로만 일어난다 | 측정용 가정 |
| 사전식 목적 | (1) 미러 비 오차 max \|(m_i k_i)/(m_j k_j) / (I_i/I_j) − 1\|(I = θ 점 `dc_op` 전류, 지시의 정의 -- 같은 w_s면 m_i/m_j 대 I_i/I_j) (2) Euler -- 필요한 경로 수 Σ max(1, 홀수 꼭짓점/2) 최소(성분마다 홀수 0·2면 성립) (3) **(가)** 묶음 W 오차 max \|m k g/W − 1\|(동률 합) / **(나)** 넓은 키 먼저, 그다음 W 오차 | 지시(사전식 1·2·3) |
| 묶음 사이 미러 | 미러 멤버가 다른 묶음에 걸치면(예: stage 1 tail과 stage 2 전류원) 묶음 이름순으로 한 바퀴 돌며 이미 정한 쪽 값으로 재고, 상태가 바뀌지 않을 때까지 다시 돈다(재방문 = 순환 기록) | **측정용 가정**(정의 필요 §8) |
| W 표 | 종속 소자 W(k)는 노드 점의 함수다. 첫 표 = R0 탐색 평가 노드 점에서 잰 W(k)(쓰기 소자는 키와 무관한 상수 ID·L/exp(θ ln IDu)). 고른 (k, m)으로 강제 평가(pass B)한 뒤 그 평가 노드 점에서 W(k)를 다시 재어, 표가 같으면 끝(tables_same), 다르면 새 표로 다시 고른다. 같은 선택이 다시 나오면 끝(converged/cycle 기록) | 측정용 가정 |
| 강제 방법 | `pick_writer`·`pick_dependent`를 감싸 그 소자의 후보를 고른 키 하나로 제한한 엔진 선택을 부른 뒤 m만 바꾼다. 그 키에서 W가 정의되지 않으면 엔진이 `slice_missing`으로 그 평가를 실패시킨다(폴백 없음) | `sizing/block_dc.py:343~368` |
| Euler 판정 | 손 차수 세기(스크립트 `trails`)를 모든 묶음에 하고, 엔진 MOD7 함수 `layout/euler_graph.build_graph` + `layout/euler_condition.check_euler_condition`을 연결 성분마다 불러 대조: (i) 실제 m(Σm ≤ 4000인 묶음 -- 측정 도구 상한, 규칙 상수 아님) (ii) m을 홀짝이 같은 1·2로 줄인 그래프(판정 조건 = 차수 홀짝 + 연결이라 같은 판정) | 지시 |

R0·R1·R3는 v3 정의 그대로다(R3는 v3 연결 묶음·이름순 첫 쓰기 소자·광범위 except 폴백을 **v3 재현용으로만** 복사 -- 폴백 횟수는 `R3FALLBACK`으로 셈). 비교표의 정합·미러 지표는 R0·R1·R3·R5 모두 **정본 묶음**으로 다시 셌다.

## 2. 측정 범위와 정적 사실

- 회로 7/13(v3와 같은 7), 점 8개(층 0 7 + two_stage_ota HS), 소자 76(층 0 69 + HS 7). 층 0 점은 v3와 같은 전류 하한 근처 퇴화 점이고 대표점은 HS 하나다.
- **R0·R1·R3 재현**: v3 값과 같다(R0 max |r| 4.6e-3·p50 4.1e-4·HS m [13,13,13,26,63,267,299]·HS gbw −0.0691/−0.0724, R1 HS +0.0491/+0.1366·nmcnr 실현 실패, R3 HS −0.0014/−0.0252). R3 폴백(`R3FALLBACK`)은 8점 모두 0건.
- **stage(정본 S1v)**: 7회로 모두 전달 뷰가 하나(`transfer:0`, default_port). gain 제약 뷰 키가 잡힌 회로 4(ngcc·nmcnr·two_stage·two_stage_sf), 못 잡힌 회로 3(common_gate·folded·pushpull -- gain 제약에 view 필드 없음 → 첫 전달 뷰). 뷰가 하나라 '어느 뷰' 선택은 이 7회로에서 결과를 바꾸지 않는다. 단계 A 상태: ngcc `review_needed`, 나머지 `ok`.
- **블록에 없는 소자(stage None)**: 11/76 -- common_gate M1, folded MN·MP, ngcc M14·M5·M6A·M6B·M7, pushpull M5·M6, two_stage_ota_sf M9(HS 0). 바이어스 사슬 소자들이다.
- **body**: 76/76 소자의 S1 `bulk` origin = `default_rule`(DEC-61 kind별 레일). 그래서 body 조건을 걸어도 묶음이 바뀌지 않는다 -- **R5b(body 있음) = R5(body 없음)**, 모든 지표 동일(§3 표에는 R5만 적음).
- **정본 matching 묶음**: 단계 A(structure.json 사실 포함) 결과와 하네스 S1 결과가 7회로 모두 같다(7회로 합 mirror 15·diff_pair 5·branch_symmetric 3 묶음, common_gate·pushpull은 0; HS 점까지 넣은 8점 합 mirror 17·전체 26). disposition `bias_distribution` 1건(folded M3/M4 -- 같은 소자 쌍이 mirror로도 있음).
- **정본 묶음 대 v3 연결 묶음 차(R0 점 기준, 8점 합)**: 둘 다 22, 정본만 4(folded M3/M4 mirror, folded M5/M6·M7/M8 branch_symmetric, nmcnr M106/M107 branch_symmetric), 연결만 1(folded (M3, M4, MP) -- 정본은 MP를 미러에서 뺌). M-3의 두 쌍(nmcnr M102/M103 θ 비 0.0115, ngcc M1/M2 θ 비 0.5)은 정본에서 `diff_pair`라 미러 열에 들지 않는다.

## 3. 결과

### 3.1 비교표 (v3 열 + 정본 묶음 다시 셈 + R5 전용) -- 76소자·8점

'실현 비 오차' 정의 = v3와 같다: 실현 평가 전류 비 / θ 전류 비 − 1(묶음 첫 멤버 기준). v3 '같은 전류 쌍'·'비 다른 미러'는 연결 묶음(미러 꼴 + 차동 꼴) 전체를 θ 비 = 1 여부로 나눈 것이었다. 여기서는 **정본** 묶음으로 다시 센다: '같은 전류(정본 전체)' = 정본 묶음 전부 중 θ 비 = 1, '미러 비 오차(정본 mirror)' = 정본 kind mirror만(θ 비 = 1과 ≠ 1 둘 다 -- 괄호 안은 θ 비 ≠ 1 부분). '지시 정의' = (m_i k_i)/(m_j k_j) / (I_i/I_j) − 1(R5 목적 (1)과 같은 식, 노드 이동·IDu 비 없음).

| 지표 | R0 | R1 | R3 | R5(가) | R5(나) |
|---|---|---|---|---|---|
| 정합 묶음 같은 W bin -- 정본 mirror / 정본 전체 | 2/17 / 6/26 | 17/17 / 26/26 | 17/17 / 26/26 | 12/17 / 21/26 | 14/17 / 23/26 |
| 같은 전류 실현 비 오차 max(정본 전체, n) | 0.48 %(18) | 11.5 %(15) | 11.4 %(15) | 1.7 %(11) | 18.1 %(15) |
| **미러 비 오차(정본 mirror) max, (θ 비 ≠ 1 부분)** | 0.48 % (0.15 %) | 11.5 % (4.2 %) | 11.4 % (1.3 %) | **67 %** (67 %; two_stage_ota L0 M5/M7) | **47 %** (47 %; folded L0 M11/MN) |
| 미러 비 오차 HS: M5/M7(θ 비 2.108) / M3/M4 | −0.04 % / −0.11 % | −3.8 % / 0.00 % | +0.61 % / −0.11 % | **−6.7 %** / −0.12 % | −1.4 % / +0.02 % |
| 지시 정의 미러 오차 max(정본 mirror) | 2359 %(L0 키 다름·퇴화 IDu) | 25 % | 25 % | 4.3 % | 4.3 % |
| 잔차 max / p50 / p90 / p99 | 4.6e-3 / 4.1e-4 / 1.9e-3 / 4.2e-3 | 0.250 / 3.8e-3 / 6.6e-2 / 0.128 | 0.117 / 4.1e-4 / 7.1e-3 / 0.106 | **2.16** / 2.7e-3 / 0.303 / 2.15 | 0.835 / 2.7e-3 / 7.1e-2 / 0.355 |
| HS 잔차 max | 5.7e-4 | 2.6e-2 | 9.6e-3 | 0.103(M7) | 2.6e-2 |
| HS m 목록 / 최대 m | [13,13,13,26,63,267,299] / 299 | [8,8,8,8,16,30,33] / 33 | [13,13,13,13,26,51,299] / 299 | [12,13,13,13,25,210,299] / 299 | [8,8,13,13,16,33,56] / 56 |
| m ≤ 3 소자 | 0/76 | 12/76 | 1/76 | 0/76 | 9/76 |
| 봉인 7 깨짐(실현) | 0/76 | 0/76 | 0/76 | 0/76 | 0/76 |
| 실현 탈락 | 0/8 | 1/8(nmcnr Newton) | 1/8(nmcnr Newton) | **2/8**(ngcc·nmcnr `newton_line_search`) | 1/8(nmcnr `newton_iteration_cap`) |
| 최대 여유 감소(실현 − 탐색) | −18.3 mV(nmcnr M101) | −150 mV(common_gate M3) | 0 | −24.7 mV(two_stage L0 M2) | −150 mV(common_gate M3) |
| W_min 아래 손가락 | 0/76 | 0/76 | 0/76 | 0/76 | 0/76 |
| HS gbw 행 c 탐색 / 실현 | −0.0691 / −0.0724 | +0.0491 / +0.1366 | −0.0014 / −0.0252 | −0.0085 / **−0.1832** | +0.0517 / +0.1434 |
| servo 입력 차 이동 ΔV_id(0이 아닌 것) | nmcnr +47.9 mV | folded −37 µV, ngcc −276 µV | 0 | folded −34 µV, two_stage L0 −19.5 mV, HS +5.0 mV, sf −6.1 mV | folded +23.9 mV |
| **R5 전용** | | | | | |
| 묶음 수 / 크기 분포 | -- | -- | -- | 38 / 1×18, 2×11, 3×4, 4×3, 5×1, 7×1 | 같음 |
| Euler 경로 성립 묶음 | -- | -- | -- | 38/38(연결이 아닌 묶음 1: two_stage_ota_sf stage 2 nmos M7·M8 -- 성분 2, 경로 2) | 38/38 |
| 미러–Euler 충돌 묶음 | -- | -- | -- | 0/38 | 0/38 |
| 미러 쌍이 서로 다른 Euler 묶음에 듦 | -- | -- | -- | **12/23** 쌍(body 조건 있어도 12/23) | 같음 |
| 홀짝·미러 때문에 m ≠ 반올림 m(W 표가 자기 정합인 점만) | -- | -- | -- | 3/24(max \|r\| 1.2 %, nmcnr M106) | 12/63(max \|r\| 17.7 %, ngcc M7 m 4 대 3) |
| 같은 점에서 W 표가 바뀌어 m이 어긋난 소자(순환 점) | -- | -- | -- | 21/52(max \|r\| 216 %, ngcc M0·M12) | 4/13(max \|r\| 84 %, folded M11) |
| W 표 되풀이 결과(점 8) | -- | -- | -- | tables_same 2, converged 1, **cycle 5** | tables_same 6, converged 1, cycle 1 |
| 쓰기 소자 둘 이상인 묶음 | -- | -- | -- | 10/38 | 10/38 |
| 공유 키 정의 불능(W(k) 없는 소자)·교집합 빔 | -- | -- | -- | 0/38 · 0/38 | 0/38 · 0/38 |
| 행 하나로 묶인 소자(묶음 ≥ 2, 성분 1, Euler 성립) | -- | -- | -- | 56/76 | 56/76 |
| 같은 (점, kind, body, w_f)에 다른 소자가 있는 소자 | 44/76 | 75/76 | 70/76 | 66/76 | 68/76 |

표 주:
1. R5의 큰 잔차·미러 오차는 대부분 **W 표 되풀이가 순환한 점**에서 나온다(§3.1 'W 표 되풀이' 행): 고른 (k, m)으로 평가하면 종속 소자의 노드 점이 움직여 그 소자의 W(k)가 바뀌고(층 0 퇴화 점에서 수 배), 다음 선택이 이전 선택으로 돌아간다. 마지막 평가의 m은 이전 W 표로 고른 값이라 실제 W와 어긋난다. 자기 정합 점만 보면 m ≠ 반올림 m은 R5(가) 3/24, R5(나) 12/63이다.
2. HS R5(가): stage 1 nmos 묶음(M1·M2·M5)이 키 600, stage 2 nmos(M7)가 키 148로 갈렸다. 미러 M5/M7(정본 mirror, θ 비 2.108)이 서로 다른 Euler 묶음에 들어 지시 정의 오차(키 비 포함)를 줄이려 키·m이 정해졌고(M5 m 25, M7 m 210), 그 결과 같은 묶음의 차동쌍 M1/M2가 Euler 홀짝 때문에 m 12/13으로 갈렸다(고정 노드 비 오차 9.4 %, 실현 비 오차 −0.16 %). 실현 미러 오차는 −6.7 %다 -- 지시 정의(m·k 비 대 I 비)는 두 슬라이스의 IDu 차를 보지 않으므로, 지시 정의 오차 1.7 %가 실현 오차 6.7 %로 나타났다(§6 P-5).
3. R5(나)는 넓은 키를 먼저 고르므로 R1과 비슷한 꼴(키 1000, m 작음)이 되고 m ≤ 3 소자 9/76, 입력 고정 구성 common_gate M3 −150 mV(R1과 같은 값)가 그대로 나온다.
4. Euler 판정 대조: 손 차수 세기와 엔진 `check_euler_condition`(성분마다)이 152/152(38묶음 × 4변형, m을 홀짝 같은 1·2로 줄인 그래프) 일치, 실제 m으로 그린 그래프(Σm ≤ 4000인 92건)도 92/92 일치.

### 3.2 Euler 손 차수 세기 표본 (엔진 판정과 대조)

| # | 점·변형·묶음 | 소자(S–D, m) | 차수 | 홀수 꼭짓점 | 손 판정 | 엔진 |
|---|---|---|---|---|---|---|
| 1 | two_stage_ota HS R5(가) (stage 1, nmos) | M1 D3–CS 12, M2 O1–CS 13, M5 CS–gnd 25 | D3 12, O1 13, CS 50, gnd 25 | O1, gnd | 경로 | path (O1, gnd) |
| 2 | two_stage_ota HS R5(나) (stage 1, nmos) | M1 8, M2 8, M5 16 | D3 8, O1 8, CS 32, gnd 16 | 없음 | 회로 | circuit |
| 3 | two_stage_ota HS R5(가) (stage 1, pmos) | M3 D3–vdd 13, M4 O1–vdd 13 | D3 13, O1 13, vdd 26 | D3, O1 | 경로 | path (D3, O1) |
| 4 | ngcc L0 R5(나) (stage 2, nmos) | M11 V2–gnd 4, M8 NP–gnd 4 | V2 4, NP 4, gnd 8 | 없음 | 회로 | circuit |
| 5 | pushpull L0 R5(나) (stage 0, nmos) | M1 vdd–vout 3, M4 vdd–B 1 | vdd 4, vout 3, B 1 | B, vout | 경로 | path (B, vout) |
| 6 | folded L0 R5(가) (stage 1, pmos) | M3 X–vdd 167699, M4 Y–vdd 167699, M5 Vg7–Y 62835, M6 out–X 62835 | X 230534, Y 230534, vdd 335398, Vg7 62835, out 62835 | Vg7, out | 경로 | path (Vg7, out) |

### 3.3 LR8 충돌 -- 지금 규칙의 w_f가 물리 행 구성과 어긋나는 소자

물리 행 그룹 = (kind, body)(LR8 '물리 행은 (kind, body 넷)으로 먼저 나뉜다', MOD7 `RowGroup`). 한 행 그룹 안 w_f가 둘 이상이면 같은 확산 띠에 둘 수 없다(LR8 '같은 물리 행 안 finger 폭 같음'). '다수 밖' = 그 행 그룹에서 가장 많은 w_f가 아닌 소자 수(행을 하나로 두려면 w_f를 바꿔야 하는 최소 소자 수).

| 규칙 | (kind, body) 행 그룹 기준: 다수 밖 소자 / w_f 둘 이상인 행 그룹에 든 소자 / 그런 행 그룹 수 | (stage, kind, body) 기준 같은 셈 |
|---|---|---|
| R0 | **34/76** / 73/76 / 14/16 | 24/76 / 52/76 / 17/38 |
| R1 | 0/76 / 0/76 / 0/16 | 0 / 0 / 0 |
| R3 | **16/76** / 38/76 / 7/16 | 9/76 / 20/76 / 6/38 |
| R5(가) | 16/76 / 55/76 / 10/16 | 0(정의상) |
| R5(나) | 14/76 / 49/76 / 9/16 | 0(정의상) |

R5는 stage 안 묶음에서만 w_f를 맞추므로 (kind, body) 행 그룹 기준으로는 stage 사이 w_f가 갈린다(14~16/76).


## 4. 측정 중 바뀐 정의 (원래 지시와 다른 점 -- 따로 표지)

| 순서 | 지시(오케스트레이터 전달) | 이 측정에 반영한 것 |
|---|---|---|
| 1 | R5 원 정의: 묶음 = stage ∩ kind, m 선택 = W 오차 최소, w_s 둘째 기준 (가)·(나) | §1 |
| 2 | 사용자 "전류미러비는 가장 우선 되어야 하고." → 사전식 (1) 미러 비 (2) Euler (3) W 오차 | §1 사전식 목적, 미러–Euler 충돌 n/N(§3.1) |
| 3 | 정정 M-1·M-2·M-3: 미러 묶음은 정본 `matching_groups`, 광범위 except 폴백 금지, 이름 정렬 대표 금지, 미러 열은 정본 미러만 | §1(정본 READS, 정지 기록), §2(정본 대 연결 묶음 차), §3.1(미러 열 정본만) |
| 4 | 사용자 "오일러 묶음은 핑거수 결정근거로 graph에 기록… 레이아웃은 이것을 기초로 묶음을 풀거나 재사용" | §5.1~5.3 |
| 5 | 사용자 "이 묶음은 기하학적인 묶음으로 성능묶음과는 관계없어." → Euler 묶음 = 기하 묶음, 미러 비는 정본 성능 묶음에서 | §5.1 축 표기, M-1 비해당 판정, 미러 쌍이 다른 Euler 묶음 12/23 |
| 6 | 사용자 R6 제안(사이징 = W·w_s, m은 레이아웃) | §7 |

측정 스크립트는 1~3을 반영해 한 번 돌렸고(4·5는 문서 판정만 바뀜, 측정 정의 변화 없음 -- 측정의 Euler 묶음은 처음부터 matching에서 유도하지 않았다), 6은 folded부터 같은 실행에서 R6 변형을 더했고 common_gate는 따로 다시 돌렸다(§9).

## 5. graph 단일 정본 점검 (원칙 7, 상위 CLAUDE.md '★graph 단일 정본' 1~7)

엔진 인용은 재작성 범위(지울·바꿀 자리) 용도뿐이다(원칙 8). 사용자 지시(오케스트레이터 전달): "오일러 묶음은 핑거수 결정근거로 graph에 기록했으면 좋겠어. 나중에 레이아웃 단계에서는 이것을 기초로 묶음을 풀거나 재사용하도록 해." 아래 5.1~5.3은 그 방향의 **필드 설계안 점검**(재작성 범위 인용, 새 코드 0)이고 확정이 아니다. 5.4는 원래의 점검표다.

### 5.1 두 양 (a) 묶음 소속 / (b) 점마다 손가락 결정

| | (a) 묶음 소속(Euler 묶음 멤버십) | (b) 점마다 손가락 결정 |
|---|---|---|
| 값 | 묶음 id → 멤버(소자), 묶음 키 = (stage, kind[, body]) + 연결 성분(공유 S/D 넷으로 정해짐). **기하 묶음**(확산 공유·행 배치)이라 성능 묶음 `matching_groups`에서 유도하지 않는다(사용자 정정 2026-11-07 "이 묶음은 기하학적인 묶음으로 성능묶음과는 관계없어.") | 묶음마다 공유 w_s(슬라이스 키) / 소자마다 m / 묶음 Euler 판정(성립 여부, 성분마다 홀수 꼭짓점, 필요한 경로 수) / 홀짝 조정 기록(반올림 m에서 벗어난 소자와 그 W 오차) / 미러-Euler 충돌 기록 |
| θ 의존 | 없음 -- 입력이 S1(kind·`bulk`·`pins`·`matching_groups`)과 S1v(`graph.views` 블록 `stage`)뿐 | 있음 -- W(k)가 θ·노드 점의 함수 |
| 사이징 전에 쓸 수 있나 | **있다**. 입력 필드가 모두 단계 A(S1 → S1v) 산물이다 | 아니다(평가마다) |
| writer 후보·층 순서 | S0 수준 블록 하나(이름은 design). 층 순서 = `build_s1v`(stage 유도) **뒤**, 출발 단계(`search/iv_matching_l.py:66` 등)·DC 블록(`sizing/block_dc.py` `dc_solve`) **앞**. `s1_matching_groups`는 S1 단계라 stage를 모른다 -- (a)를 그 블록에 넣으면 층 역전(S1이 S1v를 읽음)이 된다 | `dc_solve` 하나(지금 `device.dc_finger`의 writer). 묶음 결합 선택을 한 블록 호출 안에서 하면 writer 하나가 유지된다 |
| 기존 필드와 같은 정의인가 (graph 규칙 3) | **다른 정의 → 새 필드**. 비교 대상과 축: `graph.matching_groups`(**성능** 묶음 -- 정합·미러 비 판정, 축 = '기하(확산 공유·행 배치) 대 성능(정합·미러 비)') / MOD7 `RowGroup`(물리 행 그룹 = (kind, body), stage 축 없음, `convergence/layout_input.py:79`가 매번 유도 -- 필드 아님) / S1v 블록(stage 단위 이득 블록, kind 축 없음). (a)의 축 = 손가락 결정 근거로서의 확산 묶음 단위(stage ∩ kind[∩ body]) | 소자별 (m, w_f) = `dc_finger` **같은 정의 → 합침**(지금 `FingerGeom(m, w_f_m, residual)` 그대로, 둘째 필드 금지). 묶음 단위 값(공유 키·Euler 판정·경로 수·충돌·홀짝 조정 기록) = **다른 축 → 새 필드**(묶음 단위 graph 필드, 소자 행이 아님; writer = `dc_solve`, `DeviceOp.W`·`dc_finger`와 같이 쓰는 꼴 -- DEC-105 (2) '필드 둘·계산 자리 하나' 선례). 소비자 = 레이아웃(5.2)·보고. 소비자 0이면 출력 전용 선언 필요(원칙 9) |

**점검자 M-1이 R5 Euler 묶음에 해당하는가**: 해당하지 않는다. M-1은 '연결로 만든 미러 꼴·차동 꼴 묶음 = 정본 matching 분류(DEC-93·U-06, `graph.matching_groups`)의 둘째 정의'라는 지적이다. R5 Euler 묶음은 정합 의도를 판정하지 않고 '한 확산 띠에 놓을 소자 집합'을 정한다 -- 입력(stage·kind·body·S/D 넷)도, 쓰임(손가락 홀짝·공유 폭의 근거)도 성능 판정과 다르고, 같은 소자 쌍이 한쪽에만 들 수 있다(예: 미러 M5/M7은 정본 mirror지만 stage가 달라 Euler 묶음이 갈린다 -- 정본 미러 쌍 12/23이 서로 다른 Euler 묶음에 든다, §3.1). 정의가 다르므로 graph 규칙 3의 '다른 정의 = 다른 필드'다. **단 M-1의 꼴은 R5의 미러 비 우선 쪽에 남는다**: 미러 비는 성능 조건이라 미러 판정을 정본 `matching_groups`(DEC-105 (4) 미러 술어)에서 읽어야 하고, 이 측정은 그렇게 했다. 그리고 Euler 묶음 유도가 MOD7 행 유도와 같은 정의인지는 별개 질문이다(아래 5.2 -- 같으면 그쪽이 둘째 생산자).

### 5.2 레이아웃 소비(MOD7 -- 묶음을 재사용하거나 푸는 꼴)

| 자리(재작성 범위) | 지금 | (a)·(b)를 READS하는 꼴로 바뀔 때 | 둘째 생산자 점검 |
|---|---|---|---|
| 행 그룹 유도 `convergence/layout_input.py:79`(`RowGroup` = (kind, body)마다 하나) | 레이아웃 입력 어댑터가 스냅샷에서 (kind, body)로 행 그룹을 스스로 만든다 | (a) 묶음을 시작 행 그룹으로 읽는다(재사용). 물리 행 = (kind, body) 먼저(LR8)이므로 (a)에 body 축이 없으면 (kind, body) 분할만 레이아웃이 더한다 | (a)에 body 축을 넣으면 같은 (kind, body) 유도가 (a)와 어댑터 두 곳 -- 둘 중 하나를 지운다 |
| 폭 후보·확정 `layout/finger_candidates.py:21~33`, `layout/finger_geometry.py`(행 그룹마다 가장 많은 소자에 맞는 폭 키 → `device.ly_finger`, writer `ly_finger_geometry`) | 레이아웃이 W_need에서 finger_w·nf를 **다시 고른다**(⌊⌋·⌈⌉, 허용오차 ok 플래그) | 재사용 갈래: (b)의 공유 w_s·m을 그대로 받는다(다시 고르지 않음 -- LY2 '같은 선택 함수 하나'와 맞음). 푸는 갈래(LY3 W_request·LY9 행 접기·재구성·hub 병합): 레이아웃이 (b)에서 출발해 바꾼 결과를 자기 필드(`ly_finger`·`ly_rows`)에 쓴다 | 재사용 갈래에서 레이아웃이 같은 입력으로 같은 선택을 다시 하면 둘째 생산자다 -- `finger_candidates`의 nf 재선택은 재사용 갈래에서 지워야 한다. 푸는 갈래의 `ly_finger`는 '물리 행에 실제로 둔 손가락'이라 (b)('사이징 점의 손가락 결정 근거')와 축이 다르다(입력 = 레이아웃 판정·면적·matching 패턴) -- 다른 정의로 남을 수 있다 |
| 행 구성 `layout/rows.py:131~145` `_initial_rows`(폭 키별 Euler 행 → `row_euler`), `:148` `_merge_hubs`(stage를 넘는 같은 (kind, body, 폭 키) 병합), LY9 접기·재구성 | 행을 행 그룹·폭 키에서 스스로 짓는다 | (a)·(b)의 Euler 묶음을 초기 행으로 읽는다. hub 병합(stage를 넘음)·접기·재구성은 '푸는' 연산이고 결과는 `ly_rows`(writer `compose_rows`) | 초기 행을 레이아웃이 따로 유도하면 (a)와 같은 정의의 둘째 생산자 -- 초기 행 유도를 지운다. `ly_rows` 자체는 물리 행(최종 배치)이라 다른 축 |
| 레이아웃 Euler 판정 `layout/row_euler.py`, `layout/euler_condition.py`(MOD7 복사 함수) | 행마다 Euler·crossover를 판정 | 사이징 (b)의 Euler 판정과 **같은 함수**를 불러야 한다(같은 판정 정의를 두 함수로 두지 않음). 이 측정은 그 함수를 측정 도구로 불렀다(§3.1 표 주 4, §3.2) | 같은 행에 같은 함수를 다시 부르면 값 재계산(G-10 꼴) -- 재사용 갈래는 (b)를 READS |

### 5.3 DEC-105 (2) '선택 함수 = 소자 하나의 순수 함수' 충돌이 어떻게 바뀌나

- 지금 문언: 선택 함수 = (kind, L, 슬라이스별 W_s) → (m, w_f, 키), DC 블록과 출발 단계(`iv_matching_l.py:66`, 소자 하나·상수 W)가 같이 부른다.
- (a)를 정본 필드로 두면: 함수 입력이 '소자 하나 + (a) 묶음 참조 + 묶음 멤버의 W_s 표'가 된다. 묶음 정보가 필드 참조로 들어오므로 '숨은 상태 없는 순수 함수'는 유지할 수 있다. 그러나 **'소자 하나의 함수'는 성립하지 않는다** -- 결과가 다른 멤버의 W_s 표에 기댄다(묶음의 함수). 문언 개정 대상: '소자 하나' → '묶음 하나(멤버 = (a) 필드)'.
- 출발 단계: `_sigma_vgs`는 소자 하나·상수 W로 손가락 폭을 정해 mismatch slope bin을 고른다. 묶음 함수가 되면 출발 단계도 (a)를 READS하고 멤버 전부의 출발 W를 가져야 한다(재작성 범위 `iv_matching_l.py:59~67`). 출발 W가 멤버마다 있는지(종속 소자의 출발 W)는 design 몫이다 -- 없으면 출발 단계는 묶음 선택을 부를 수 없다(정의 필요 §8).
- DC 블록: 쓰기 소자를 노드 풀이 전에 상수 W로 고르는 순서(`block_dc.py:879~884`)는 묶음 함수와 맞지 않는다 -- 묶음에 종속 소자가 섞이면(측정 38묶음 중 다소자 묶음 대부분 -- §3.1 'W 표 되풀이' 행에서 순환 R5(가) 5/8점) 쓰기 소자 키가 종속 소자의 노드 점 W(s)에 기댄다. 되풀이 규칙(종료·순환)을 정해야 한다(G-b).

### 5.4 점검표

| # | 질문 | 사실 | 판정 |
|---|---|---|---|
| G-a | 묶음은 사이징 전에 유도되는 정적 양인가 | 묶음 키 = stage(S1v `graph.views` 블록 `stage`, writer `build_s1v` -- 단계 A) × kind(S1) × body(S1 `bulk`). 셋 다 θ와 무관한 S0 수준 필드라 사이징 전에 정해진다. Euler 묶음은 기하 묶음이라 성능 묶음 `graph.matching_groups`에서 유도하지 않는다(5.1). 미러 비 우선이 읽는 미러 묶음은 S1 `graph.matching_groups`(writer `s1_matching_groups`) -- (b) 선택의 입력 | **맞음**(정적). 단 하네스·커널 평가 경로(generality `Pipe`)에는 S1v가 없다 -- 지금 DC 블록이 `graph.views`를 READS로 선언하지만(`sizing/block_dc.py:95`) 그 경로에서는 비어 있다. 정적 정본 자리는 있으나 평가 스냅샷에 실려 오는지는 호출 경로마다 다르다 |
| G-b | 슬라이스 선택 필드의 writer가 하나로 남는가 | `device.dc_finger` writer = `dc_solve` 하나(`sizing/block_dc.py:1~5`). R5는 묶음 단위 결합 선택이라 한 블록 호출 안에서 묶음 전체를 고르면 writer는 하나로 남는다. 그러나 dc_solve 순서는 (1) 쓰기 소자를 상수 W로 먼저 고르고 (2) 그 키로 노드를 풀고 (3) 종속 소자를 노드 점 W(s)로 고른다(`block_dc.py:873~890`, `_rounds` 607~625). R5 묶음에는 쓰기·종속 소자가 섞이고, 종속 소자 W(s)는 노드 점 함수, 노드 점은 쓰기 소자 키의 함수다 -- 같은 블록 안 되풀이가 필요하고, 측정에서는 그 되풀이가 고정점에 닿지 않았다: 순환 R5(가) 5/8점, R5(나) 1/8점(§3.1 'W 표 되풀이' 행) | **조건부** -- writer 하나는 유지 가능, 되풀이의 종료·순환 규칙(지금 Rʳ 키 벡터 재방문 = fail-closed와 같은 꼴을 쓰기 소자까지 넓힐지)이 계획에 없다 |
| G-c | 출발 단계 선택 함수 공용(DEC-105 (2))과 맞는가 | DEC-105 (2): '손가락·슬라이스 선택은 순수 함수 하나(kind·L과 슬라이스별 W_s → (m, w_f, 슬라이스 키)), DC 블록과 출발 단계가 같이 부른다'. 출발 단계 호출 자리 `search/iv_matching_l.py:66`(`_sigma_vgs` -- 소자 하나·상수 W 한 번, 묶음·다른 소자 W 없음). R5 선택은 묶음 멤버 전부의 W(k) 표·미러 묶음·Euler 그래프가 입력이라 서명이 바뀐다 | **모순**(M-2와 같은 꼴) -- 재작성 범위: `lut/finger_slice.py` `finger_slice` 서명(소자 하나 → 묶음), `block_dc.py:343~368` `pick_writer`·`pick_dependent`·`873~890` 순서, `iv_matching_l.py:66`(출발 단계가 묶음 정보 = S1v `graph.views`·S1 `bulk`·`matching_groups`를 READS로 읽고 멤버 전부의 출발 W를 가져야 함 -- 출발 블록이 그 필드를 읽을 수 있는지는 design 몫, 지금 `_sigma_vgs`는 소자 하나 단위) |
| G-d | 레이아웃 층 행 구성(MOD7)과 같은 정의의 양이 둘이 되는가 | MOD7: 행 그룹 = (kind, body) 하나(`convergence/layout_input.py:79` `RowGroup`), 행 그룹마다 finger_w를 레이아웃이 **다시 고른다**(`layout/finger_candidates.py:21~33` nf = ⌊W_need/fw⌋·⌈⌉, `layout/finger_geometry.py` 가장 많은 소자에 맞는 폭 키 → `device.ly_finger`, writer `ly_finger_geometry`), 행 = 폭 키별 Euler 행(`layout/rows.py:131~145` `_initial_rows` → `row_euler`), stage를 넘는 hub 병합(같은 (kind, body, 폭 키), `rows.py:148`). R5를 사이징 층에 두면 '같은 물리 행 = 공유 w_f + Euler 홀짝 m'이 `dc_finger`에도 생긴다 | **위반 위험**(graph 규칙 1·3): 같은 정의(행별 공유 손가락 폭·행 Euler 손가락 수)를 `dc_finger`(사이징)와 `ly_finger`·`ly_rows`(레이아웃)가 각각 만든다. 둘을 남기려면 축 차이를 적어야 하는데 실제 차이는 (i) stage 축 -- R5 묶음은 stage를 나누고 MOD7 행 그룹은 나누지 않으며 stage를 넘어 병합한다 (ii) 판정 축 -- MOD7은 `w_tolerance` ok 플래그, `dc_finger`는 잔차 최소. 하나로 하려면 레이아웃이 `dc_finger`를 READS하고 다시 고르지 않거나(LY2 '같은 선택 함수 하나'의 as-built 어긋남 = 재작성 범위), 사이징이 레이아웃 행 정의를 READS해야 한다. 정본 자리는 계획에 없다 -- **멈춤 사유 후보(S-7, 규칙 6)**: 채택 전 계획부터 정해야 한다 |
| G-e | 미러·정합 묶음 둘째 생산자가 있는가 | 이 측정의 R5 미러 우선 대상 = 정본 `graph.matching_groups` kind mirror(읽기만). v3 연결 묶음은 대조용 표(§2)에만 쓴다 | **맞음**(R5 측정 정의 안). R3(v3 정의)는 연결 직접 묶음이라 둘째 정의 -- M-1 그대로 |
| G-f | 새 cache·memo·sctx 슬롯·값 사본 | 측정 스크립트 안의 W 표(REC)는 측정 도구 상태다. R5를 엔진에 넣으면 묶음 선택의 W(k) 표는 블록 안 지역 값(필드 아님) -- 블록 안 local memo 예외(O-15 (E))에 해당하는지 design 몫 | **불확실**(design 미검토) |
| G-g | 같은 정의 = 필드 하나(묶음 정의) | R5 묶음 (stage ∩ kind ∩ body)과 MOD7 행 그룹 (kind ∩ body), 레이아웃 matching 그룹(DEC-93)은 서로 다른 정의다. 새 집합을 만들면 A-139·새 집합 점검(원리 하나로 대체 가능한가) 대상 | **불확실** -- stage 축이 물리 결정자인지가 정해지지 않았다(§6 P-3) |

## 6. 물리 판정 (물리 결정자 / 식·원문 / 실측 / 판정)

원문 위치(로컬):
- Maloberti, *Layout of Analog CMOS IC Part 2* -- `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library/sources/two_stage_ota+folded_cascode__maloberti_2004/source.pdf`(쪽 = 슬라이드 아래 번호, 텍스트 `paper.md`). references/stick-diagram-euler-layout.md가 인용하는 `vendor/analog/Layout02.pdf`와 같은 원문(그 vendor 폴더는 저장소에 없음).
- Jespers & Murmann 2017, 부록 2·3 -- `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/references/gmid_sources/jespers_murmann_2017/extracted/lookup-table-generation-and-usage.pdf`, `…/layout-dependence.pdf`(쪽 = 서적 쪽 번호).
- 찾은 범위: Jespers 2010(`…/gmid_sources/jespers_2010/gmid_methodology_jespers_2010.pdf`)은 이번에 열지 않았다. Jespers & Murmann 2017 부록 3에는 Euler 경로·확산 공유 서술이 없다(확인 범위 = 부록 3 전문 pp.315~321 텍스트 검색 'finger·junction·diffusion·shared').

| # | 질문 | 물리 결정자 | 식·원문 | 실측(이 측정) | 판정 |
|---|---|---|---|---|---|
| P-1 | 한 확산 띠로 묶으면 접합 용량이 준다 | 이웃 손가락이 같은 S/D 넷을 공유하면 그 확산 하나를 두 손가락이 나눠 쓴다 → 소자당 Cdb·Csb 면적·둘레 감소 | Maloberti p.10 C_DB = C_SB ∝ (W + 2l_diff)(L_D + 2l_diff) 꼴, p.11 'Use of multiple fingers'(W를 2·3 손가락으로 나누면 C_DB′ = C_DB/2, 2/3 C_DB…) -- 같은 소자 안 손가락 사이 공유. 다른 소자 사이 공유는 p.25 stacked layout·p.27 Euler 조건(stick-diagram 참조 §3 'PDF p.27') | **이 측정으로는 잴 수 없다**: 엔진 레이아웃 전 접합 비례 r = 그 평가의 `DeviceOp.W`/w_ref(계획 v6.38.29 JC-1 -- 소자마다 총 W 비례, 이웃 공유 없음), 레이아웃 뒤 r = `ly.diffusion` 면적 비. 사이징 층 평가(이 측정의 탐색·실현 평가)에는 공유 효과가 들어가지 않는다. 오라클 넷리스트 ad/as/pd/ps도 (w_f, m) 소자 단위(DEC-105 (2)) | **조건부** -- 방향은 원문과 맞음. 크기는 MOD7 `ly.diffusion`·oracle 몫(이 측정 범위 밖) |
| P-2 | 같은 행(stack) 안 finger 폭이 같아야 한다 | 한 확산 띠는 한 높이(W_f)로 그린다. 정합 소자 interdigitation은 같은 단위 손가락 반복 | Maloberti p.25 'Same width of the fingers in the same stack, possibly different length', p.13 'Two matched transistors … split them in an equal part of fingers … interdigitate'; 계획 LR8 '같은 물리 행 안 finger 폭 같음' | §3.4 LR8 표 | **맞음**(R5는 정의상 묶음 안 w_f 하나 -- 공유 키) |
| P-3 | 묶음 경계 = stage인가 | 확산 공유를 가능하게 하는 것은 (kind, well/body, 공유 넷, 같은 w_f)다. stage(전압 이득 단계)는 확산 연속의 물리 조건이 아니다 | Maloberti p.25 'Identify the transistors that can be placed on the same stack'(stage 언급 없음), p.38 'Group transistors in stacks … transistors of the same type in the same region'; MOD7은 stage를 넘는 hub 병합을 둔다(`layout/rows.py:148`, 계획 Q8 (viii)) | §3.3 묶음 표, 묶음 사이 미러 수 | **불확실** -- stage 경계는 물리 결정자가 아니라 묶는 단위의 선택(잡음 결합·배치 편의 등 다른 근거가 있는지는 원문에서 못 찾음) |
| P-4 | Euler 경로가 되는 홀짝 m을 고르면 W가 어긋난다 | 홀짝을 바꾸려면 반올림 m에서 ±1 -- 상대 W 오차 ≤ 1/m. m이 작을수록 크다 | 정수 손가락: Jespers & Murmann 2017 p.316~317(기준 레이아웃 W = 10 µm = 5 × 2 µm, nf = max(round(W/2 µm), 1) 식 (C.3.1), 'the finger width must vary') | §3.2 '홀짝 조정 소자' 열 | **조건부** -- 크기는 m 분포에 따른다(§3.2) |
| P-5 | 미러 비 우선 | 미러 전류 비 = 같은 VGS에서 (m_i w_s)/(m_j w_s) × IDu 비(VDS 차) | 미러 비 = 손가락 수 비(Maloberti p.13 정합 손가락 분할). VDS 차에 따른 IDu 비는 엔진 W에 이미 들어 있다(W = I·L/IDu) | §3.1 미러 열: 지시 정의(m 비 대 I 비)와 v3 정의(실현 전류 비 / θ 전류 비)를 함께 적음 | **조건부** -- 지시 정의는 IDu 비(VDS 차)를 빼고 재므로, 지시 정의로 0인 선택도 실현 전류 비 오차는 IDu 비만큼 남는다(§3.1) |
| P-6 | 슬라이스(w_f)가 바뀌면 gm/ID·용량 열이 바뀐다 | LUT 슬라이스 = 그 폭의 SPICE 스윕(Q-P8 ①②), 손가락 폭 의존 LDE | Jespers & Murmann 2017 p.318~319: W > 2 µm에서 gm/ID·gm/Cgg 오차 ≤ ~1.5 %, 최소 폭에서 gm/Cgg 40 %; p.305 CDD = 진성 + stray + 접합 성분 | §3.2 HS gbw 행 | **조건부** -- R5가 좁은 공유 키를 고르면 v3 R0와 같은 꼴(좁은 슬라이스)의 영향이 생긴다 |

## 7. R6 -- 사이징은 W와 공유 w_s만, 손가락 수 m은 레이아웃에서 (사용자 제안, 측정용 가정)

사용자 원문(오케스트레이터 전달): "레이아웃은 이 필드를 참조만 하고 필요에 따라 다시 구성할 수 있어. 핑거 수 결정을 위해서 레이아웃 단계의 일부가 여기에서 수행되어야 하는 것 같아. 이 단계에서는 W만 정하고 핑거수는 나중에 정할 수 있으면 좋겠는데?"

R6 측정용 가정: 사이징 = 소자 W(연속, θ에서) + Euler 기하 묶음마다 공유 w_s(= 슬라이스 키 = 모델 bin). m은 정하지 않는다. 레이아웃 = 묶음 필드 READS(필요하면 재구성) + m 결정(미러 비 → Euler → W 오차) + 실현 재평가(LY7·O-237)가 정수화 잔차를 흡수.
측정 방법: R5(가)·(나)가 고른 공유 키를 그대로 두고 m = W/(k·g)(연속, 그 평가 노드 점의 W 표)로 강제한 탐색 평가 = 'R6 사이징 평가'(라벨 R6ga·R6na). 그 탐색 스냅샷을 R5의 탐색·실현 평가와 비교한다(같은 키라 차이는 m이 사이징 평가에 들어가는 자리에서만 생긴다).

### 7.1 전제 확인 -- 같은 w_s에서 사이징 평가가 W에만 기대는가 (엔진 평가식 읽기, 원칙 8 용도 (2))

| 양 | 평가식(자리) | m 의존 | 판정 |
|---|---|---|---|
| DC(노드 전압·전류·VGS) | `dc_solve` 탐색 평가: 소자 점 = 슬라이스 키의 순방향 IDu(VGS, VDS, VSB) × W/L, W = I·L/IDu(연속 `free_width`, `sizing/block_dc.py` `_outputs`) -- `dc_finger.m`은 잔차 기록에만 쓰인다 | 없음(키만) | **맞음** |
| gm·gds·gmb | `ss_linearize`: gm = `dc_gm`, gds = `gds_per_w`·W, gmb = `gmb`·W/w_m(`metrics/ss_linearize.py:14`) | 없음 | **맞음** |
| 진성 용량(CGG·CGD·CGS·CGB) | `caps(memo, kind, …, op.W)`(그 키 열, W 비례) | 없음 | **맞음** |
| mismatch σ | `metrics_aux.py:172` 행 = (kind, 기준 키, L, W, VGS, VDS, VSB, 슬라이스 폭 w_m) -- W와 슬라이스 폭만 | 없음 | **맞음** |
| 잡음 | `metrics/noise_devices.py:6·37`: 기준 폭 `w_m` 값 × 배율 w_m/W(S_vg는 같은 전류밀도에서 폭에 반비례), 전류 잡음 = gm²·S_vg(`noise_sources.py`) | 없음 | **맞음** |
| **접합 cdb·csb** | `ss_linearize._linearize` → `junction.pre_layout_geometry(w_f, m)` = `DiffusionGeometry.from_lut_rule(decl, w_f, m)`(`metrics/junction_cap.py:111`): 손가락 하나 ad = ad_per_w·w_f, **pd = w_f + pd_extra**, 소자 = m배 → 총 Cj = Cj,area·ad_per_w·W + Cj,sw·(W + **m·pd_extra**)(as·ps 같은 꼴) | **있음** -- 둘레의 손가락당 상수 항이 m에 비례 | **틀림(전제 불성립)**: 레이아웃 전 접합 용량이 정수 m(손가락 수)을 읽는다. 계획 v6.38.29 JC-1 문언 'r = 그 평가의 `DeviceOp.W`/w_ref'(W만)와 as-built가 다르다 -- as-built는 (w_f, m) 손가락 기하다(재작성 범위 표지, JC-1 card 미병합 여부는 이 측정이 확인하지 않음) |
| 실현 평가 | `RealizedFinger` → W′ = m·w_s(`block_dc.py` `_realized_picks`), O-237 재풀이 | m이 입력 | 정의상 m 필요 |

R6 측정에서는 접합 기하의 m에 연속값 W/w_s를 넣었다(= 'W만의 꼴', 손가락 수가 정수가 아님). 이 값의 물리 뜻은 '손가락당 둘레 상수 항을 W/w_s개 센다'이고 정수 m과 다르다 -- §7.2가 그 차를 잰다.

### 7.2 R6 사이징 평가 대 R5 (같은 공유 키, 8점)

| 지표 | R6(가) | R6(나) | 대응 R5(가) / R5(나) |
|---|---|---|---|
| 탐색 평가 노드 전압 차 max \|ΔV\| (R6 − R5, 같은 키) | **0.0**(8/8점) | **0.0**(8/8점) | -- |
| 탐색 평가 제약 행 c 차(R6 − R5) | HS: pm −0.0079, parasitic_pm −0.026, gbw −1.8e-5, ugf +1.2e-3(행 단위). gain 행·DC 행(w_min·seal6·inversion_floor·area) 차 0. 부호 바뀐 행 0/8점 | HS: pm +0.0016, parasitic_pm +0.0052, gbw +5e-6. 부호 바뀐 행 0/8점 | -- |
| 탐색 HS gbw 행 c | −0.0085 | +0.0518 | −0.0085 / +0.0517 |
| 그 탐색 점의 실현 평가(m = W/w_s 연속 → W′ = W) | HS gbw −0.0106, 실현 탈락 0/8, 봉인 7 깨짐 0/76 | HS +0.0486, 탈락 0/8, 깨짐 0/76 | R5 정수 m 실현: HS −0.1832 / +0.1434, 탈락 2/8 / 1/8 |
| 미러 비 오차(정본 mirror, 실현) | max 0.029 %(고정 노드 0) | max 0.030 % | 67 % / 47 % |
| 잔차 | 0(정의상, ≤ 3e-15) | 0 | -- |

- 사이징 평가 차는 접합 둘레 항(m·pd_extra)에서만 나온다(7.1). 노드 전압·DC 행이 R5와 같아 **DC는 m 무관**을 실측으로 확인했다. 소신호 행 차는 HS에서 PM 행 단위 ≤ 0.026으로 작고 부호를 바꾸지 않았다(8/8점).
- '레이아웃 m 정수화 뒤 재평가가 R5와 같은 점으로 가는가': 실현 평가 입력은 (θ, 소자별 m·w_s) + 기준 스냅샷의 측정 구성·입력 값·피벗 판정이다. R6 탐색과 R5 탐색은 θ·키·노드 전압이 같으므로(ΔV = 0) 기준 스냅샷의 그 셋이 같고, 레이아웃이 R5와 같은 정수 m을 고르면 재평가는 **구성상 R5 실현 평가와 같은 점**이다(R6 기준으로 정수 m 재평가를 따로 돌리지는 않음 -- 입력 동일성 논증, 실측은 ΔV = 0까지). 다른 m을 고르면 다른 실현 점이다.
- R6 실현(연속 m)과 R5 실현(정수 m)의 차가 곧 '정수화가 만드는 변화'다: HS gbw 행 R6(가) −0.0106 → R5(가) −0.1832, R6(나) +0.0486 → R5(나) +0.1434. 실현 탈락 R6 0/8 → R5 2/8·1/8.

### 7.3 계획 문언 충돌·재작성 범위 (원칙 8 용도 (2))

| 자리 | 지금 문언·as-built | R6에서 바뀌는 것 |
|---|---|---|
| DEC-105 (2) '레이아웃 전 손가락 규칙'(P:305) | 실현 기하 (m, w_f) = graph 필드 하나, writer = `DeviceOp.W`를 쓰는 DC 블록, 소비자 = oracle 넷리스트 생산자(EO-1)·DE-1 성분 (3)·WB-1 범위 2b 손가락 분할 의존 양 | 사이징은 w_s(키)만 정하고 m을 쓰지 않는다 -- `dc_finger.m`의 writer가 사이징에서 사라지고 레이아웃으로 간다. 그 필드를 읽는 사이징 쪽 소비자를 바꿔야 한다(아래 목록) |
| O-173 Q-P8 (A) 자기 정합 선택 = 슬라이스 고정 | 선택식 \|m·w_s/W(s) − 1\| 최소(m과 w_s를 함께 고름) | 사이징 선택 기준에서 m이 빠진다 -- 공유 w_s를 고르는 기준이 새로 필요(R5의 사전식 기준은 m을 쓰므로 그대로 옮길 수 없다, 정의 필요 §8) |
| O-237 실현 재풀이(W′·바이어스 고정 KCL + 재봉인)의 위치 | 사이징 front 점 실현 평가(`search/realize_front.py`)와 레이아웃 뒤(LY7) 둘 다 같은 꼴 | 사이징에는 정수 m이 없으므로 사이징 실현 평가는 W′ = W(연속)라 재풀이할 것이 없다(R6 실측: 실현 ≈ 탐색). 정수화 잔차의 재풀이는 레이아웃 뒤 LY7 하나로 모인다 |
| LY7·MOD8 루프 | LY7: 실현 기하로 한 번 재평가 후 freeze, MOD8 진입 = '폭 키가 사이징 스냅샷과 다름' 또는 'W_request 있음' | 레이아웃이 묶음을 다시 구성해 w_s가 바뀌면 = MOD8 진입 조건 '폭 키 다름' -- 그 점은 재평가가 필요하다(기록). 정수화만 하면 키는 같고 LY7 재평가 한 번 |
| `device.dc_finger` writer·소비자 | writer = `dc_solve`. 엔진 소비자(grep): `metrics/ss_linearize.py:41·106`(레이아웃 전 접합 기하 = (w_f, m)), `search/realize_front.py:53`·`sizing/block_dc.py` `_realized_picks`(실현 평가 입력 m·w_s), `metrics/metrics_aux.py:172`(w_f만 -- 주석상 dc_finger.w_f_m과 같은 값을 슬라이스 표에서 읽음), `convergence/realized_geometry.py:9`(요청 대기 소자의 접합 기하) | m을 읽는 사이징 쪽 소비자 = ss_linearize 접합 기하, 실현 평가(realize_front·`_realized_picks`), realized_geometry. R6이면 이 셋이 m 없이 정의되어야 한다(접합 = W만의 꼴, 실현 = W′ = W) |
| JC-1 r '그 평가가 쓴 W'(계획 v6.38.29) | 계획: 레이아웃 전 r = `DeviceOp.W`/w_ref(W만). as-built: (w_f, m) 손가락 기하(7.1) | R6 전제(사이징 평가가 W·w_s만)는 계획 문언 쪽과 맞고 as-built와는 다르다 -- as-built 접합 자리는 재작성 범위 |

### 7.4 물리 판정 (R6)

| # | 질문 | 물리 결정자 | 식·원문 | 실측 | 판정 |
|---|---|---|---|---|---|
| R6-1 | 사이징 평가 = w_s 슬라이스 × W가 정의상 맞는가 | SPICE는 손가락 폭 w_f로 bin을 고르고 m은 병렬 배율이다(Q-P8 ①, DEC-105 (2) '오라클 소자 w = finger_w, m = n_fingers') | 폭 정규화 LUT 값(IDu·gm/ID·gds/W·C/W)은 같은 w_f에서 m과 무관 | 노드 ΔV 0, DC 행 차 0(8/8점) | **맞음**(진성 양) |
| R6-2 | 접합 용량도 W만으로 정해지는가 | 접합 둘레 = 손가락마다 (w_f + 끝 확산 길이) -- 손가락 수에 비례하는 상수 항이 있다. 확산 공유(Euler 행)면 그 항이 더 준다 | Maloberti p.10~11(C_DB·C_SB 면적·둘레, 손가락 분할로 C_DB′ 감소); as-built `from_lut_rule` pd = w_f + pd_extra | 연속 m 대입 시 HS PM 행 차 ≤ 0.026 | **조건부** -- W만의 꼴은 '손가락당 둘레 항을 W/w_s개 센다'는 근사다. 정확한 값은 정수 m과 확산 공유(레이아웃) 뒤에만 정해진다 |
| R6-3 | E-0 관문에서 사이징이 정수 m 없이 못 판정하는 항목 | (i) W_min: 손가락 폭 w_s ≥ W_min은 w_s만으로 판정된다 (ii) 손가락 수 ≥ 1: W ≥ w_s여야 정수 m ≥ 1이 W에 가깝다 -- W < w_s이면 m = 1이 W를 넘는다(R1의 m = 1 갈래와 같은 물리) (iii) 확산 기하·실현 가능 W: 정수 m 뒤에만 | 계획 E-0(원칙 1·6) | 측정 점에서 W < w_s 소자: R6(가)·(나) 연속 m < 1 소자 0/76(m ≤ 3: 0/76, 1/76) | **조건부** -- (i)은 사이징에서 판정 가능, (ii)는 'W ≥ w_s' 조건으로 사이징에서 판정 가능하나 그 조건이 지금 선택 규칙에 없다, (iii)은 레이아웃 뒤 LY7로 미뤄진다 |
| R6-4 | m을 늦추면 정합 비가 보존되는가 | 미러 비 = (m_i w_s,i IDu_i)/(m_j w_s,j IDu_j) | -- | 연속 m 실현 미러 오차 ≤ 0.03 %, 정수 m(R5) 47~67 %(층 0 퇴화 점 포함) | **조건부** -- 사이징 단계에서는 정의상 보존, 정수화 비 오차는 레이아웃 m 선택과 LY7 재평가의 몫이 된다 |

## 8. 남은 불확실 -- 사용자가 정해야 할 정의 포함

### 8.1 정의가 필요한 것 (측정은 측정용 가정으로 했다)

| # | 정의 | 측정용 가정 | 측정이 보인 것 |
|---|---|---|---|
| D-1 | **stage 뷰** | gain 제약 전달 뷰, 없으면 첫 전달 뷰(엔진 `l_classes` 규칙) | 7회로 모두 전달 뷰 1개라 선택이 결과를 바꾸지 않음. 뷰가 여럿인 회로(CMFB 등)에서는 미측정 |
| D-2 | **블록에 없는 소자(stage None)의 묶음** | kind별 'None' 묶음 하나 | 11/76 소자(바이어스 사슬). 이 묶음이 stage 묶음과 확산을 나눌지(MOD7 hub 병합처럼 stage를 넘을지) 미정 |
| D-3 | **body 조건** | 있음/없음 둘 다 | 76/76 bulk = 기본 레일이라 차 0. 선언 bulk가 있는 회로는 미측정 |
| D-4 | **w_s 둘째 기준** (가) W 오차 / (나) 넓은 w_s | 둘 다 | (가): HS 실현 gbw −0.1832, 실현 탈락 2/8, 순환 5/8점. (나): HS +0.1434, m ≤ 3 9/76, common_gate M3 −150 mV, 순환 1/8점 |
| D-5 | **미러 비 정의** | 지시 정의 (m_i k_i)/(m_j k_j) 대 I_i/I_j | 키가 다른 미러(서로 다른 Euler 묶음 -- 12/23 쌍)에서 지시 정의는 슬라이스 IDu 차를 보지 않아, 지시 정의 1.7 %가 실현 6.7 %(HS M5/M7)가 됐다. 실현 전류 비 정의(= (m_i k_i/W_i(k_i)) / (m_j k_j/W_j(k_j)))를 쓸지 정의 필요 |
| D-6 | **미러 쌍이 서로 다른 Euler 묶음에 들 때** | 묶음 이름순 교대 갱신 | 12/23 쌍. 이름순 갱신은 원칙 12(이름 불변성) 위험이 있다 -- 순서 규칙 정의 필요 |
| D-7 | **경로 불성립 때 처리** | 기록만 | 이 측정에서 불성립 0/38(m 후보 {f, f+1}이 두 홀짝을 다 줌). 불성립이 나면 정지인지, 경로 여러 개(확산 끊김)를 허용하는지 정의 필요. 연결이 아닌 묶음(1건, sf M7·M8)은 '성분마다 경로 하나'로 셌다 |
| D-8 | **W 표 되풀이(쓰기·종속 소자 혼합 묶음)의 종료** | 상태 재방문 = 끝(converged/cycle 기록), 마지막 평가 사용 | 순환 R5(가) 5/8점, R5(나) 1/8점. 순환 점에서 m이 실제 W와 크게 어긋남(잔차 max 2.16). fail-closed(지금 Rʳ 키 순환 = `slice_cycle` 정지와 같은 꼴)로 둘지 정의 필요 -- 그러면 R5(가)는 5/8점이 정지 |
| D-9 | **쓰기 소자 둘 이상인 묶음** | 대표를 고르지 않음(묶음 전체 공동 선택) | 10/38 묶음. 쓰기 소자의 W는 키와 무관한 상수, 종속 소자 W는 키·노드 점 함수라 두 종류를 같은 W 오차로 볼지 정의 필요 |
| D-10 | **공유 키에서 W(k) 정의 불능** | 그 키 제외, 교집합 비면 정지 | 0/38(이 측정 점에서 일어나지 않음) |
| D-11 | **R6 공유 w_s 선택 기준** | R5가 고른 키를 그대로 씀 | m이 없으면 R5의 W 오차·미러 m 비 기준을 쓸 수 없다 -- 사이징에서 w_s를 무엇으로 고를지 정의 필요 |
| D-12 | **R6 레이아웃 전 접합 꼴** | 연속 m = W/w_s | 정수 m 대비 HS PM 행 ≤ 0.026 차. 계획 JC-1 'r = W/w_ref'와 as-built (w_f, m) 중 어느 쪽인지 |

### 8.2 측정의 한계

1. 대표점은 HS 1점, 나머지 7점은 전류 하한 퇴화 점(69/76). 큰 수치(잔차 2.16, 미러 67 %)는 퇴화 점의 W 표 순환에서 나온다.
2. 6/13 회로 미측정(v3와 같은 사유).
3. 확산 공유의 접합 용량 이득(P-1)은 사이징 평가에 없어 잴 수 없다 -- MOD7 `ly.diffusion`·oracle 몫.
4. 모든 실현 효과의 SPICE 대조 없음(E-1 oracle 몫, ngspice 0).
5. '정수 m 재평가가 R5와 같은 점'은 입력 동일성 논증이고, R6 기준 스냅샷으로 정수 m 재평가를 따로 돌리지 않았다.
6. 결정 간 모순 점검(⑩)은 이 문서 작성자가 채울 수 없다.

## 9. 정리

- 측정 worktree: `git -C …/wt/20261107-qb-r5 status --porcelain` = 변경 0(추적·비추적 모두), HEAD faf69218 그대로 → `git -C …/chip-design-skills worktree remove …/wt/20261107-qb-r5` 완료(`worktree list`에 없음 확인). 엔진 수정 0, 커밋 0.
- 출력 파일: `C:/Users/HSLEE/AppData/Local/Temp/la1s_qb5/out/qb5_r5.txt`(7회로, common_gate는 R6 없는 첫 실행), `out/qb5_r5_cg.txt`(common_gate R6 포함 재실행), `out/qb5_r5_all.txt`(합본 = `scripts/qb5_merge.py`), `out/qb5_summary.txt`(요약), `out/qb5_probe.txt`, 실행 기록 `out/*.runlog`(메모리 대기: folded 착수 전 약 58분 대기, two_stage_ota_sf 착수 전 약 14분 대기, 실행 중 1 GB 미만 정지 0회).

