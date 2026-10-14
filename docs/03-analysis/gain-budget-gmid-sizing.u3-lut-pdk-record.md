# U3 LUT·PDK 확장 -- 특성화·검증 기록 (2026-10-08)

> 구현 단위 U3(설계 `40-engine` §11, 계획 v6.2 DEC-87·88·96). 코드 계약은 `skills/analog-gmid-design/gmid_engine/lut/CONTRACT.md` r7(9·10절)과 `core/CONTRACT.md` 9.4b·9.6·9.7.
> 이 문서는 **측정 기록**이다(재현 명령, 소요 시간, 표본, sha256). 판정 증거가 아니다 -- 판정은 auditor 격리 복제본에서 한다(WP-13).
> 모든 수치는 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_u3/`의 스크래치 스크립트(m_*.py, 저장소 밖)로 잰 값이고, 아래 '재현' 절의 명령으로 같은 입력을 다시 만들 수 있다.

## 1. 산출 데이터 (공유 `lut_data/sky130_lut_v2/`에 **새 버전 파일**로 추가, 기존 r2 파일은 고치지 않음)

| 파일 | 크기 | sha256 | 만든 명령 |
|---|---|---|---|
| `sky130_nfet_pfet_lut_v2_noise_r1.npz` | 48.6 MB | `f5ecfdf14958e03a2c99a9647e8df589a2d7040d1b7858761065eb2668ae32a1` | `sky130_lut_sweep.py noise --cap-npz <r2> --out <noise_r1> --work <폴더> --jobs 8` (깊이 3) |
| `sky130_nfet_pfet_lut_v2_mismatch_r1.npz` | 24.4 MB | `dfec7bbf9714861162de8da77ee8c65c7ac3c1f46a73b5f50b0aad730c93bf4e` | `sky130_lut_sweep.py mismatch --cap-npz <r2> --out <mismatch_r1> --work <폴더> --jobs 6` |
| (묶인 기준 LUT, 불변) `sky130_nfet_pfet_lut_v2_r2.npz` | -- | `938e95b9b101d45140720c0655ecebed96e62c664de7121dbf399f6b1aa1efe2` | `assets/lut_v2_location.json` 의 `cap_npz` |

- 생성기 `assets/sky130_lut_sweep.py`(작업 트리 CRLF 바이트 sha256 `0ea5ca366bc38b4f5552369fb6e374df32370d98dc7917078f7012d2b723cc69`, git blob(LF) `735220532101e8a5e7a864c448ad971effa5050eecdb97ead13575368cc35987`).
  `sky130_lut_rule_decl.json` 의 `lut_generator.sha256` 은 이 LF 값으로 바꿨다(DUT 줄은 그대로 90행).
- 두 파일 모두 meta 에 `cap_npz_sha256`(위 r2), 모델 파일 sha256, ngspice-46, 온도 27 °C, 조합 기록을 싣는다. `assets/lut_v2_location.json` 에 `files.noise`·`files.mismatch` 로 sha256 고정.

## 2. 특성화 실행 (소요 시간)

| 항목 | noise | mismatch |
|---|---|---|
| 조합 | 360 (nfet 180 + pfet 180 = L 18 × VS 10) | 360 |
| 조합당 작업 | ngspice 1 프로세스: VGS×VDS 2401점 × 주파수 9개(`noise`) | ngspice 4~5 프로세스(기준 1 + 변수 nfet 3·pfet 4) × op 2401점 |
| 병렬 | 8 | 6 |
| 벽시계 | **약 104 분** (20:01 → 21:45) | **약 79 분** (20:01 → 21:20) |
| 단독 실행(무부하) | 조합 1개 **17.5 s** (2401점 × 9 주파수) | (미실측; 4 병렬 부하에서 소형 시험 조합 약 45 s) |
| 재현성 | `base_repro_rel_max` = 0.0 (같은 생성기로 다시 잰 1 Hz·100 MHz 값이 기준 LUT `SVG2_1HZ`·`SVG2_HF` 와 비트 동일) | `ref_id_repro_rel_max` = 0.0 (기준 곡선 ID 가 기준 LUT ID 열과 비트 동일) |

기계 부하가 100 % 였다(다른 구현 단위의 test·특성화와 동시). 백그라운드 실행의 30 분 시간 제한에 두 실행 모두 한 번 중단돼 조합 단위 체크포인트(생성기 sha256 이 같을 때만 재사용)로 이어 돌렸다.
소형 시험(L 2점 × VS 2점): noise 120 s, mismatch 112 s.

## 3. 잡음 결과 (계약 9절)

- 주파수 점: 기준 LUT 의 1 Hz·100 MHz + 로그 이분 점 `[10, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7]` Hz (깊이 3 -- 이웃 비 10).
- B known 비율(on 점): nmos **90.1 %**, pmos **77.5 %**. `tol_a` 중앙/최대: nmos 0.135/3.95, pmos 0.297/4.17 (셀 882개 모두 정의).
- γ_eff = B·gm/(4kT)·K = A·W·L (VDS 0.9 V, VS 0): nfet L 0.25–1 µm gm/ID 10–11: γ 1.95–2.11, K 1.7e-22–3.1e-22 / gm/ID 15–17: γ 1.78–1.97 · pfet gm/ID 10–11: γ 1.01–1.06, K 0.7e-22–1.9e-22 / gm/ID 15: γ 0.78–0.85
  -- `_drafts/engine/noise_spec_proposal.md` §0.2(nfet 1.9–2.1, pfet 1.0–1.05·0.77–0.84, K nfet 1.7e-22–3.3e-22, pfet 0.5e-22–1.9e-22)와 일치.
- **설계(41 §7.2)와 다른 점**: B 를 읽는 점에 평탄(plateau) 조건을 더했고 허용오차를 점 단위로 엄격하게 했다. 근거 실측 -- L = 20 µm·약반전(gm/ID 25) 점에서 B_j 는 10 Hz~1e4 Hz 에서 6.82e-14 로 같고 1e6 Hz 에서 9.4e-15
  (86 % 낮음)인데 피드스루 식 (2π f Cgd/gm)² 는 6e-4 라 피드스루 조건만으로는 이 점들을 걸러내지 못한다. 효과: 10 % 넘게 어긋나는 점 비율 nmos 28 % → 10.5 %, pmos 37 % → 1.2 %, 대가로 known 비율 94.4 → 90.1 %(nmos)·81.7 → 77.5 %(pmos).
- ln B 면의 점별 LOO 오차(on 점): p50 0.002–0.8 %, p90 0.4–4.4 %, p99 7–22 % (계약 9.4).
- 입력 해상도 한계: ngspice 가 `inoise_spectrum` 을 7자리로 찍어 flicker 가 지배하는 낮은 주파수의 B_j 는 (S_lo·r_j/B)·1e-6 만큼 흔들린다(nfet L 0.5 µm gm/ID 10: 10 Hz 점 -4 %, 100 Hz +1.8 %).
- 조회: `noise_params` 약 100–160 µs/호출, `noise_planes` 1.7 s(배열을 품어 디스크 캐시 대상이 아님 -- `TableCache` 의 `unstorable` 규칙).

## 4. mismatch 결과 (계약 10절)

- 변수: nfet toxe·vth0·voff, pfet toxe·vth0·voff·nfactor (모델 카드 머리 `*_slope_spectre` 전수). 섭동 1σ = `.option scale` 1e-6 (core 선언 `mismatch_slope_geometry_unit_m`).
- NaN 칸 4.04 %(VDS = 0 열 + 섭동 곡선이 VGS 격자 끝 1.8 V 를 넘는 최상단 행), voff nfet 2.62 %·pfet 2.04 %. 조회는 가중치 0 이 아닌 모서리에 NaN 이 있으면 `lut_mismatch_undefined`.
- A_eff(쌍, mV·µm) = √2·σ_VGS·√(W·L), W = 5 µm, VDS 0.9 V, VS 0 -- 제안서 §0.3 표와 대조(`mismatch_sigma_vgs`):

| L (µm) | nfet gm/ID 5 / 10 / 15 / 20 | pfet gm/ID 5 / 10 / 15 / 20 | 제안서 nfet | 제안서 pfet |
|---|---|---|---|---|
| 0.18 | 7.39 / 9.18 / 10.33 / 11.30 | 12.52 / 12.01 / 11.98 / 12.39 | 7.3 / 8.6 / 10.0 / 11.2 | 12.5 / 12.0 / 12.0 / (12.4) |
| 0.5 | 5.79 / 6.13 / 7.73 / 9.12 | 11.84 / 11.37 / 11.25 / 11.36 | 5.8 / 6.0 / 7.1 / 8.6 | 11.9 / 11.4 / 11.3 / 11.4 |
| 1.0 | 6.05 / 6.51 / 7.58 / 8.96 | 9.39 / 9.05 / 8.98 / 9.16 | 6.1 / 6.3 / 7.5 / 8.9 | 9.5 / 9.1 / 9.0 / 9.2 |

  (제안서의 gm/ID 는 1 mV 간격 곡선의 목표 gm/ID 점이라 격자점 선택이 달라 최대 7 % 차이가 난다.)
- 조회: `mismatch_dvgs` 약 110–210 µs/호출, `tol_mismatch_table` 0.9~1.5 s.

## 5. ngspice 소자 쌍 Monte Carlo (단위·합성·기하 확인, `assets/sky130_pair_mc.py`)

방법: 소자 A·B 는 모델 카드 복사본(서브서킷·`.model`·`*_slope_spectre` 이름에 접미사)이라 변수·모델이 독립이다. 둘 다 다이오드 접속에 같은 강제 전류를 흘려 V(ga) − V(gb) = ΔVGS(같은 ID).
표본마다 `alterparam` + `reset` + `op`, 난수 numpy seed 20261008, 표본 1000/사례(A_β 회귀 gm/ID 4점 × 600), gm/ID ≈ 10. 도구 sha256(작업 트리 바이트) `90fe67afae74b0c2aa462c46ab07c23953d8d12b8137ec52ece4f96729bd66e7`, 실행 1212 s.

| 소자 | W µm | L µm | bin 블록 | gm/ID | 전류 A | A_VT MC | A_VT 기대 √2·slope | MC/기대 | native/meter | A_eff MC | MC/RSS | A_β MC (%·µm) | A_β 기대 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nfet | 5 | 0.5 | .24 | 9.9 | 4.50e-05 | 4.750 | 4.746 | 1.001 | 1.0000 | 6.122 | 1.025 | 0.452 | 0.487 |
| nfet | 5 | 1.0 | .23 | 9.9 | 2.27e-05 | 4.757 | 4.746 | 1.002 | 1.0000 | 6.487 | 1.033 | 0.470 | 0.487 |
| nfet | 5 | 0.18 | .26 | 10.0 | 1.30e-04 | 4.559 | 4.746 | 0.961 | 1.0000 | 8.049 | 0.962 | 0.370 | 0.487 |
| nfet | 2 | 1.0 | .41 | 10.1 | 8.89e-06 | 4.843 | 4.746 | 1.020 | 1.0000 | 5.939 | 1.012 | 0.434 | 0.487 |
| pfet | 5 | 0.5 | .24 | 10.2 | 1.08e-05 | 10.135 | 10.403 | 0.974 | 1.0000 | 10.996 | 0.975 | 0.843 | 0.911 |
| pfet | 5 | 1.0 | .23 | 10.1 | 5.68e-06 | 8.625 | 8.282 | 1.041 | 1.0000 | 9.307 | 1.030 | 0.553 | 0.628 |
| pfet | 5 | 0.18 | .26 | 10.0 | 2.66e-05 | 9.162 | 10.403 | 0.881 | 1.0000 | 11.461 | 1.000 | 0.892 | 0.911 |
| pfet | 2 | 1.0 | .41 | 9.9 | 2.26e-06 | 8.089 | 8.282 | 0.977 | 1.0000 | 8.643 | 0.971 | 0.601 | 0.628 |

- **단위 확인**: vth0 만 흔든 쌍 σ(ΔVGS)·√(W·L[µm²]) 가 √2·`vth0_slope` 와 같다(MC/기대 0.96–1.04, 통계 오차 1/√(2(N−1)) = 2.2 %; pfet L 0.18 µm 만 0.88 -- 짧은 채널에서 같은 ID 의 ΔVGS 는 ΔVT 와 다르다, LUT 감도가
  같은 효과를 이미 담는다). `.option scale=1.0u` + 숫자만 쓴 l·w(µm) + std 1.0 과 단위 글자 l·w(m) + std 1e-6 이 **비트 동일**한 σ 를 낸다(native/meter = 1.0000) -> l·w 는 µm², slope 길이 단위 µm.
- **감도 합성**: 변수를 모두 흔든 쌍 σ 대 변수별 +1σ 단독 ΔVGS 의 RSS×√2 비 0.96–1.03 (독립 변수 분산 합 가정 -- 단독 섭동 방식인 LUT 감도 열이 MC 와 일치).
- **기하·bin**: pfet L 0.5 µm 는 `vth0_slope1`(블록 .24, A_VT 10.1–10.4), L 1.0 µm 는 `vth0_slope`(블록 .23, 8.1–8.6) -- bin 에 따라 slope 비 1.26 만큼 바뀐다. A_eff 는 같은 bin 에서 W 를 5 → 2 µm 로 바꿔도 √(WL) 환산 후 같은 범위.
- A_β(toxe 만 흔든 σ(ΔVGS) = a + b/(gm/ID) 회귀의 b·√(WL)): 제안서 §0.3 의 같은 회귀 결과(nfet 0.45–0.52, pfet L ≥ 1 0.56–0.59, L ≤ 0.5 0.88–1.16)와 같은 범위이고 √2·`toxe_slope` 보다 3–24 % 작다
  (회귀가 제곱칙 β 모델이라 근사 -- L 0.18 µm 가 가장 크게 어긋난다).
- **LUT 합성 A_eff 와 MC 의 직접 대조**(같은 점: 다이오드 접속 VDS = VGS, 같은 전류밀도): nfet W5 L0.5 LUT 6.04 / MC 6.12 (비 1.014), L1 6.33/6.49 (1.025), L0.18 8.59/8.05 (0.938), W2 L1 6.35/5.94 (0.935);
  pfet W5 L0.5 11.37/11.00 (0.967), L1 9.06/9.31 (1.028), L0.18 12.02/11.46 (0.953), W2 L1 9.06/8.64 (0.955). 모든 사례에서 LUT 가 고른 `.model` 블록 = MC 블록.
  LUT 의 vth0 성분(mV·µm): nfet 4.74–4.82(기대 4.746), pfet L 0.5 10.41(10.40), L 1 8.37(8.28), L 0.18 9.71(10.40).

## 6. Pelgrom 계수 유도 (참고, 코드에 박지 않음)

쌍 A_VT = √2·`vth0_slope`, A_β = √2·`toxe_slope`(상대값 %·µm). 값은 PDK mismatch 파일(sha256 위 MC JSON `files_sha256`)에서 읽는다.

| | nfet_01v8 | pfet_01v8 L ≥ 0.5 µm | pfet_01v8 L < 0.5 µm |
|---|---|---|---|
| vth0_slope (V·µm) | 3.356e-3 | 5.856e-3 | 7.356e-3 (`vth0_slope1`) |
| A_VT = √2·slope (mV·µm) | 4.746 | 8.282 | 10.403 |
| toxe_slope (상대·µm) | 3.443e-3 | 4.443e-3 | 6.443e-3 (`toxe_slope1`) |
| A_β = √2·slope (%·µm) | 0.487 | 0.628 | 0.911 |

단위: 모델 카드 식이 `p_slope/sqrt(l·w·mult)` 이고 `models/all.spice` 의 `.option scale=1.0u` 아래 l·w 는 µm 수치 -> slope 의 길이 단위 µm, σ[V] = slope[V·µm]/√(W·L[µm²]). `legacy/sizing_recipe.py:3073` 은 pfet 에 5.856e-3 하나만 썼다(결함, 대조 기준선).

## 7. 그 밖의 측정

- **VS 축 Hermite 정확도**(ngspice 새 점, 칸 중앙, L 0.35 µm, 강반전 분지·VDS 12점, nmos 5292점·pmos 5281점): |Δln ID|/(gm/ID) p50/p99/max -- VS Hermite(r7) nmos 0.13/2.6/5.3 µV·pmos 0.30/5.1/9.0 µV,
  VS 선형(r6) nmos 174/763/910 µV·pmos 189/949/1073 µV (약 3 자릿수 개선). VS 축 LOO(환산 후, nmos 1000): 선형 p50/max 197/1294 µV -> Hermite 0.145/9.1 µV.
- **tol_V 영향**(w_key 1000): 셀 id_equivalent p50/p90/max [mV] 는 r6 와 r7 이 비트 동일(nmos 2.41/17.8/44.6, pmos 3.70/14.1/22.7 -- VDS·L 축이 지배); gm_id_inverse 셀 p50 nmos 81.2 → 76.4 mV, pmos 118.5 → 118.5 mV, p90·max 같음.
- **VS Hermite FC**: nmos 7,620,480 칸 중 위반 353(4.6e-5), pmos 4,572,288 칸 중 3,934(8.6e-4); VDS·VGS 축 위반 0.
- **`vgs_for_current_density` 대 옛 우회 `gm_id_for_target(current=)`**(무작위 3000점 × 2 kind): 둘 다 성공한 점의 VGS 차 최대 5.1e-15 V, 왕복 |Δln IDu| 최대 2.1e-14, 옛 우회만 실패한 점 31(분지 끝 마디 반올림), 새 함수만 실패한 점 0.
- **곡선 표 4종**: 300점/kind 모두 생성, 평균 마디 49(nmos)·48.8(pmos), `monotone` nmos 300/300·pmos 74/300(pfet 중반전 gm/ID 한 번 올라감 -- 소비자는 격자 전수로), 표 하나 0.8–4.7 ms.
- **기울기 열 단위 검사**: 실데이터 32개 슬라이스의 최대 |로그| GM 1.9e-4, GDS 8.0e-5 (경계 1; GMBS/ID 대 VS 도 2.9e-4 지만 toy 슬라이스 호환을 위해 검사하지 않는다).
- **저항 면적**(Q9): R□ = `rp1` 48.2 Ω/□ (`res_typical__cap_typical.spice` 21행), W_min = `poly.3` 0.33 µm (periphery.csv 403행), 본체 Ω당 면적 W_min²/R□ = (0.33e-6)²/48.2 = 2.2593e-15 m²/Ω (손계산 일치),
  머리 면적 2·W_min·(licon.1 + 2·licon.8a) = 2·0.33·(0.17 + 0.16) µm² = 0.2178 µm². 후보 종류는 `poly_generic`(res_generic_po) 하나 -- U3 측정 당시 정밀 poly 저항(res_high_po·res_xhigh_po) 모델 파일은 로컬 sparse checkout 에 없었다.
  (2026-10-14 정정: res_high_po 모델 파일 6개를 사용자 D-R 승인으로 `google/skywater-pdk-libs-sky130_fd_pr` 커밋 f62031a 에서 `C:/pdk/sky130_fd_pr/cells/res_high_po/` 에 받아
  held-out D 저항 값 계산에 썼다(master 6a22538). res_xhigh_po 는 여전히 없고, `sky130_pdk_decl.json` `resistor_types` 후보는 그대로 `poly_generic` 하나다.)
- **로드 시간**(32 슬라이스, 부하 중 비교): 마스터 26.0 s → U3 36.4 s (같은 부하; 단위 검사·VS FC 검사 추가분 포함, 무부하 U3 로드 11~15 s).

## 8. 재현

```
PY=C:/Python314/python.exe
cd skills/analog-gmid-design/assets
$PY -P sky130_lut_sweep.py noise    --cap-npz <lut_data>/sky130_nfet_pfet_lut_v2_r2.npz --out <noise_r1.npz>    --work <폴더> --jobs 8
$PY -P sky130_lut_sweep.py mismatch --cap-npz <lut_data>/sky130_nfet_pfet_lut_v2_r2.npz --out <mismatch_r1.npz> --work <폴더> --jobs 6
$PY -P sky130_pair_mc.py --work <폴더> --out <json> --n 1000 --n-beta 600 --jobs 4
```

## 9. 한계·열린 항목

- 잡음·mismatch 열은 기준 폭(5 µm)에서만 있다(다른 폭으로 옮기지 않는다 -- 호출부 환산, 계약 9.3·10.4). `mismatch_sigma_vgs` 의 W 환산은 √(W_ref/W)와 PDK bin slope 비만이고 좁은 폭 효과는 없다(W 2 µm 사례 LUT/MC 비 0.935–0.955).
- 잡음 주파수 점은 전 칸 같은 로그 이분 깊이(3)이고 설계의 칸별 적응 반복이 아니다. 깊이를 늘린 재측정은 `--depth` 로 가능(새 버전 파일).
- 정밀 poly 저항 후보 부재(위), 머리 면적 기하 해석은 사용자 ratify 대상.
- 소비처가 아직 없는 API: `noise_params`·`tol_noise_table`·`noise_planes` (U8), `mismatch_dvgs`·`mismatch_sigma_vgs`·`tol_mismatch_table` (U7·U13), 곡선 4종 (U9·U13), `sweep_memo` (U11·U16), `require_lut_data` (U5·U9).
  `vgs_for_current_density`(sizing)와 poly 저항 면적(`passive_area_decl` -> `metrics.area_search`)은 이 커밋에서 배선했다.
