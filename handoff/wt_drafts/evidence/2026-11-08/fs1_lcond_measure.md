verdict: 진행 가능

# FS-1 code 재개 착수 조건 (2) -- L 조건 착수 실측 (계획 v6.39.5 N6.43)

- 측정자: 앞 판정(`fs1_disputes_verdict.md`)과 같은 독립 판정자. 읽기·측정만 했고 엔진·test·card 변경 0이다.
- 기준 코드: code worktree `wt/20261107-fs1-code` HEAD = `7c239beefcb7a914d58d5bc8eede7d2336f1d5b9`(브랜치 role/code/20261107-fs1).
- 도구: 앞 판정 스크립트를 그대로 썼다. 새 도구 0이다.
  - `m_s1.py`: 단계 A → B → 탐색 컨텍스트. 출력 칸만 늘렸다(소자별 출발 L = `start.row.l_chosen`, 칸 구조·키, kind별 기준 폭 키·후보, 기준 폭 출발 조회 시험).
  - `m_partner.py`: 새 짝 정의 갈래를 더했다(오프라인).
- 파일: `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/fs1_judge/`
  - 측정 원자료 `m_s1L.jsonl`(회로마다 append)
  - 집계 `partnerL.jsonl`
  - 회로별 stdout `m_s1L_<회로>.stdout`
- 연결은 topology JSON `netlist` 원문만 썼다(태그 미사용). bulk 미선언은 DEC-61 kind별 레일 기본으로 두었다.

## 적용한 정의(오케스트레이터 지시 = 계획 v6.39.5)

- 짝 = KVL 짝 ∪ 대칭 짝이고, 둘 다 있으면 KVL 짝을 쓴다.
- KVL 짝 = gate·source·bulk·kind가 같고 **출발 L이 같은**(부동소수 `==`) 쓰기 소자다. 칸 소속은 보지 않는다.
- 대칭 짝 = 그 멤버가 든 diff_pair·branch_symmetric 묶음(status derived·ratified)의 다른 쓰기 멤버다.
- 짝이 없는 비쓰기 단일 멤버 칸은 기준 폭 슬라이스(`cap_map[kind].w_key`)로 출발한다. 조건은 둘이다.
  - 그 키가 `widths(lut, kind)` 안에 있다.
  - 출발점에서 그 슬라이스 조회(`op_point`)가 정의된다. 이 조회가 출발 L의 L 축·bin 안 여부를 함께 판정한다.
  - 둘 중 하나라도 안 서면 출발 불능 `reference_slice_undefined`이다.
- 다멤버 칸에 짝 없는 멤버가 있으면 출발 불능 `no_member_density`이다.

## 1. 출발 불능 칸 n/N (단계 B 통과 library 7개 회로 전수)

| 회로 | 칸 N | 짝으로 정의 | 기준 폭 출발 | 출발 불능 (사유별) |
|---|---|---|---|---|
| common_gate_amplifier | 3 | 3 | 0 | 0 |
| current_reuse_telescopic_ota | 40 | 35 | 5 | 0 |
| folded_cascode | 7 | 7 | 0 | 0 |
| nmcnr_amplifier | 10 | 10 | 0 | 0 |
| pushpull_follower_buffer | 6 | 5 | 1 | 0 |
| sf_pushpull_output_opamp | 12 | 11 | 1 | 0 |
| two_stage_ota | 4 | 4 | 0 | 0 |
| **합** | **82** | **75** | **7** | **0/82** (no_member_density 0, reference_slice_undefined 0) |

- 단계 B를 통과하지 못한 회로(cnr_ota·erfc_ota·r2r_opamp = stopped, ngcc_3stage_ff·rfc_ota = review_needed)는 탐색 컨텍스트가 없어 대상 밖이다. 앞 판정 `m_s1.jsonl`과 같다.

## 2. 기준 폭으로 출발한 칸: 7/82

| 회로 | 소자 | kind | 기준 키(× 격자 1e-8) | 후보 안 | 출발 L | 출발점 조회 |
|---|---|---|---|---|---|---|
| current_reuse_telescopic_ota | M23a | nmos | 1000 (10 µm) | 예 | 1.5e-7 | defined |
| 〃 | M14a | nmos | 1000 | 예 | 1.5e-7 | defined |
| 〃 | M20b | pmos | 1000 | 예 | 1.5e-7 | defined |
| 〃 | M11b | pmos | 1000 | 예 | 1.5e-7 | defined |
| 〃 | M40 | pmos | 1000 | 예 | 1.5e-7 | defined |
| pushpull_follower_buffer | M2 | pmos | 1000 | 예 | 1.5e-7 | defined |
| sf_pushpull_output_opamp | M21 | pmos | 1000 | 예 | 1.5e-7 | defined |

- 일곱 개는 앞 판정의 출발 불능 칸과 같은 소자다. 모두 고리 등식 종속(`cycle_vgs`) 단일 멤버 칸이다.
- 후보 목록(nmos 18개, pmos 12개)에 키 1000이 있다. pmos 후보에는 84·110·…·1000·1400이 있다.

## 3. L 조건 때문에 KVL 짝을 잃은 경우: 0/30

- 비쓰기 소자는 모두 43개다(0 + 22 + 5 + 4 + 1 + 8 + 3).
- 그 가운데 gate·source·bulk·kind가 같은 쓰기 후보가 있는 것은 30개다. 회로별로 current_reuse 15, sf_pushpull 6, folded 4, nmcnr 3, two_stage 2개다.
- 이 30개 중 L이 달라 짝을 잃은 경우는 0개다. 30개 모두 KVL 짝을 유지한다(`partnerL.jsonl`의 `lost_by_L`은 모든 회로에서 빈 목록).
- 나머지 13개는 처음부터 KVL 후보가 없다. 6개는 대칭 짝으로 짝을 얻는다: M1b·M4b(current_reuse), M1(folded), M102(nmcnr), M2(sf), M1(two_stage). 7개는 짝이 없어 기준 폭으로 출발한다(§2).
- **folded_cascode (M3, M4) ↔ MP**: 출발 L은 M3 = 1.5e-7, M4 = 1.5e-7, MP = 1.5e-7로 같다. 그래서 KVL 짝 = MP(`partner: M3 → ("kvl", "MP")`, `M4 → ("kvl", "MP")`)이고, 미러 칸 (M3, M4)는 출발이 정의된다.
- 같은 회로의 나머지 짝은 M10 → M9, M11 → MN(KVL), M1 → M2(대칭)다.
- 칸 밖 KVL 짝 13개(current_reuse 11개, folded 2개 -- 앞 판정 §2.4)도 모두 L이 같아 유지된다. current_reuse에서 M18_bg·M66과 짝들의 L은 1.5e-7이다.

## 4. 판정 r-1: 대칭 짝 쌍의 출발 L 같음: 15/15

| 회로 | 묶음 (role: members → 출발 L) |
|---|---|
| current_reuse_telescopic_ota | diff_pair M37a·M37b 1.5e-7, diff_pair M4a·M4b 3.221e-6, diff_pair M1a·M1b 2.5e-6, branch_symmetric M3a·M3b 1.5e-7, M2a·M2b 1.5e-7 |
| folded_cascode | diff_pair M1·M2, branch_symmetric M7·M8, M5·M6 (모두 1.5e-7) |
| nmcnr_amplifier | diff_pair M102·M103, branch_symmetric M106·M107 (1.5e-7) |
| sf_pushpull_output_opamp | diff_pair M1·M2, branch_symmetric M13·M15, M10·M5, M12·M7 (1.5e-7) |
| two_stage_ota | diff_pair M1·M2 (1.5e-7) |

- 대칭 묶음 L은 S1v L 동치류 주인 하나에서 정해진다(출발 단계 `_owner_groups`). 그래서 같은 값이 나오고, 이번 실측에서도 깨진 쌍이 없다.

## 5. 판정 r-2용(출력 전용): 기준 폭 출발 칸의 동작점 조회 위험

- 시험한 점: 그 소자의 출발 L, VGS = 출발 곡선(`curve_bundle_of`, 그 소자 출발 동작점 `start.point` VDS·VSB)에서 gm/ID = `start.row.gm_id_lo`인 점, 기준 키 슬라이스 `op_point`.
- 결과: 7/7이 defined(축 밖·bin 불가 0)다.
- 한계(근사):
  - 코드 `_wf_cells.defined`는 1회차 g_lo0을 쓴다. 측정에는 그 근사로 행의 `gm_id_lo`를 썼다.
  - 평가 단계 동작점(고리 등식 VGS·실제 VDS)에서 기준 슬라이스가 정의되는지는 이 시험으로 보장되지 않는다. 그 경우는 평가 실패(fail-closed)로 드러난다.
  - 평가 동작점 기준 조회 가능 여부는 LA-1 측정 시점에 front 결과로 센다.

## 판정 (계획 N6.43 착수 조건 (2))

- folded_cascode 미러 칸 (M3, M4)는 출발이 정의된다(KVL 짝 MP, L 같음).
- 단계 B 통과 회로의 출발 불능 칸은 0/82다.
- 그래서 멈춤 조건에 해당하지 않는다. **진행 가능**이다.

## 해석상 주의 (판정 근거는 아님 -- LA-1 재점검 입력)

1. 이 library에서 L 조건은 **실질 부하가 없다**. 출발 L이 거의 모두 L 최소 1.5e-7에 몰려 있고(예외: current_reuse M1a·M1b 2.5e-6, M4a·M4b 3.22e-6 -- 각각 대칭 쌍 안에서만 같음), 0/30은 이 분포의 결과다. L 하한이 활성인 회로(절대 offset 제약 등)가 들어오면 L 조건으로 짝을 잃는 경우가 생길 수 있다. 그때는 착수 조건 (2)의 셈을 다시 해야 한다.
2. L 같음은 부동소수 `==`로 판정했다. 같은 L 동치류·같은 앵커에서 나온 값이라 지금은 정확히 같다. 서로 다른 계산 경로에서 나온 L을 비교하게 되면 '같은 칸 index/같은 앵커'처럼 정의 수준의 비교가 맞다. design에서 정한다.
3. '짝으로 정의' 75칸은 새 짝 정의에서 모든 비쓰기 멤버가 짝을 가진다는 뜻이다. 칸 키 선택((i)/(ii)/(iii))은 code가 실제로 낸 값이 모두 non-None인 칸이다. 새 정의로 바뀌는 짝 소자는 0이다(L 조건 손실 0, 칸 밖 짝은 코드가 이미 같은 짝을 씀). 그래서 그 키가 바뀌지 않는다고 본다. 새 정의 code가 나오면 같은 스크립트로 다시 확인한다.

## 실행 기록

- 측정은 하나씩 돌렸다.
  - 첫 실행(pushpull·two_stage): 착수 때 여유가 **3.18 GB로 기준 3.7 GB 미만**이었다(다른 agent의 pytest 2 GB 동시 실행). → **절차 위반 1건**이다. 실행 중 최저 1.82 GB로 1 GB 정지선까지 가지 않았다. 이 실행은 timeout으로 two_stage 앞에서 끝났다.
  - 그 뒤 회로별 실행 6회는 각 착수 전 여유 4.3~5.7 GB를 확인하고 시작했다(3.79 GB 미만이면 건너뛰는 검사를 넣음).
- 끝난 뒤 판정자 python 프로세스는 0개다. 남은 PID 34300은 다른 agent의 `pytest search/test_kernel.py`다.
- 금지 명령: 이번 측정에서 0건이다.
