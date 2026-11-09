# M-4 측정 -- 노드 풀이 되먹임 집합(Rʳ) 정적 계수와 소자 안 고정점 회차 (design v1.15.2 검증 M-4·재판정 P5)

- 2026-10-29, design 작성자. 엔진 = `wt/integ-it12` `b12792ab` import·읽기만(무수정, 끝에 `git status` 빈 출력). 판정 기록 아님.
- 재현: 이 폴더에서 `C:/Python314/python.exe m4_measure.py <회로 ...>` (결과 `m4_measure.out.jsonl` append, 요약 `run.log`). 흐름 = G-10 test와 같음(선언 E_B 40, 600 s). `timeout`으로 감싸지 말 것(사용자 site-packages 못 잡음).
- 방법은 `m4_measure.py` 머리 주석. 선택 규칙 = design 40 §3.7-A 5 재현(bin 소속은 as-built 1 ulp 비교 -- D1 정정 전).

## (i) Rʳ ≠ ∅ 회로(정적, 범위 3a 뒤 남는 읽기 = 순환 SCC 수렴 허용오차 소자 가운데 종속 소자)

| 회로 | 종속 소자 수 | 순환 SCC 허용오차 소자 중 종속 소자(Rʳ 후보) |
|---|---|---|
| common_gate_amplifier | 0 | 없음 |
| current_reuse_telescopic_ota | 21 | 없음 |
| folded_cascode | 4 | 없음 |
| ngcc_3stage_ff | 7 | 없음 |
| nmcnr_amplifier | 3 | 없음 |
| pushpull_follower_buffer | 1 | 없음 |
| sf_pushpull_output_opamp | 8 | 없음 |
| two_stage_ota | 2 | 없음 |
| two_stage_ota_sf | 3 | 없음 |

**9/9 회로에서 Rʳ = ∅**: 순환 SCC는 모두 VGS writer 식(θ 쓰기 소자)으로 닫혀 허용오차 소자에 종속 소자가 없다. 그래서 library에서는 DC 블록의 노드 풀이가 평가마다 한 번이다(노드 재풀이 0). 구현 뒤에만 잴 수 있는 것은 Rʳ ≠ ∅ 회로가 생겼을 때의 노드 재풀이 수뿐이다.

## (ii) 소자 안 고정점 회차(봉인점 노드 고정 + 슬라이스 직접 조회)

봉인점 = front, 없으면 sealed cache(균등 최대 5점). 소자-점 단위.

| 회로 | 소자-점 수 | 1회차 수렴 | 2회차 수렴(슬라이스 바뀜) | `finger_below_min` | `slice_cycle` | 최대 회차 |
|---|---|---|---|---|---|---|
| common_gate_amplifier | 0(종속 소자 0) | -- | -- | -- | -- | -- |
| current_reuse_telescopic_ota | 측정 불능(이 예산에서 봉인점 0) | | | | | |
| folded_cascode | 20 | 12 | 3 | 2 | 3 | 2 |
| ngcc_3stage_ff | 측정 불능(단계 B review_needed -- 탐색 미도달) | | | | | |
| nmcnr_amplifier | 15 | 15 | 0 | 0 | 0 | 1 |
| pushpull_follower_buffer | 5 | 5 | 0 | 0 | 0 | 1 |
| sf_pushpull_output_opamp | 측정 불능(봉인점 0) | | | | | |
| two_stage_ota | 10 | 8 | 0 | 2(4회차에) | 0 | 4 |
| two_stage_ota_sf | 15 | 10 | 0 | 4(2·4회차에) | 1(4회차) | 4 |

**발견(계획 v6.38.4 P5 재료 -- design은 계획 규칙을 그대로 두고 보고만)**:
1. **순환(`slice_cycle`)이 실제로 생긴다 -- 기제 둘**: (가) bin 경계를 넘는 m 전환(folded M3·M4 3건, 아래) (나) 같은 W-bin 안 가까운 슬라이스 왕복(two_stage_ota_sf M4 1건 -- 같은 모델 bin이라 매개변수는 같고 슬라이스 W 차이만 있음). (가): folded_cascode M3·M4(2/5 봉인점)는 기준 폭 슬라이스로 낸 W ≈ 5.5~5.8 µm가 w_hi를 넘어 m = 2(w_f ≈ 2.8 µm)로 가고, 그 좁은 슬라이스의 전류 밀도로 다시 낸 W ≈ 4.6~4.8 µm가 w_hi 아래라 m = 1(w_f ≈ 4.7 µm)로 돌아와 기준 슬라이스로 간다 -- **m이 W에 의존하고 W가 슬라이스(m이 고른 손가락 폭)에 의존하는 고리에 고정점이 없다**(같은 총 폭을 손가락 하나/둘로 실현하면 전류 밀도가 달라 둘 다 자기 일관이 아님). two_stage_ota_sf M4(점 48)는 1.0 → 0.42 → 0.55 → 0.42 µm로 돈다(0.42·0.55 µm는 같은 pmos W-bin (0.42, 0.55] 안의 두 슬라이스). 계획 DEC-105 (2)의 규칙대로면 이 점들은 봉인 실패(fail-closed)가 된다 -- 지금 봉인되는 점이 바뀌는 **동작 변경**이고, 물리적으로는 두 실현이 모두 제조 가능한데 규칙이 고르지 못하는 경우라 'fail-closed가 맞는 물리'인지는 계획 판단 몫.
2. **`finger_below_min`이 봉인점에서 생긴다**: folded M10(2/5점 -- 기준 슬라이스로 이미 W ≈ 0.38 µm < W_min 0.42), two_stage_ota M4·two_stage_ota_sf M4(좁은 슬라이스로 옮겨가며 W가 W_min 아래로 내려감 -- 좁은 bin의 전류 밀도가 커서). 지금 봉인되는 점이 거부된다.
3. Rʳ = ∅ 이므로 Q-DC1의 '노드 풀이 재계산' 손실은 library에서 0이고, 회차 비용은 소자 안 고정점(LUT 점 조회 몇 번)뿐이다.

한계: 봉인점은 as-built(기준 폭 슬라이스) 탐색이 낸 점이라, 새 블록이 돌면 탐색 궤적 자체가 달라진다; 선택 규칙 재현은 엔진 밖 스크립트(격자 반올림 = manifest 제조 격자, bin = 슬라이스 meta `w_bin`).

## 정정 기록

- 2026-10-29(검증 2 m-7 -- `wt/_drafts/evidence/2026-10-29/design_v1152_validation2/slice_keys.out`): 슬라이스 키는 5 nm 격자 단위다(키 84 = 0.42 µm, 110 = 0.55 µm, 200 = 1.0 µm, 600 = 3 µm, 1000 = 5 µm). 첫 판 README의 'two_stage_ota_sf M4는 0.84·1.0·2.0 µm 슬라이스 사이를 돈다'는 키를 10 nm로 읽은 오기라 위 본문을 정정했고, 순환 기제를 둘로 나눠 적었다. 원자료(`m4_measure.out.jsonl`·`run.log`)는 바꾸지 않았다.
