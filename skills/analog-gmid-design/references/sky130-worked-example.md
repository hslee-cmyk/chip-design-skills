# sky130 실전 LUT 예제 — toy가 아닌 진짜 실리콘 데이터

> `references/gm-id-methodology.md`·`lut-generation-checklist.md`는 방법론과 절차를 다룬다.
> 이 문서는 그 절차를 **실제로 오픈소스 PDK + ngspice로 끝까지 실행해본 결과**를 기록한다 —
> `assets/sky130_lut_sweep.py`(재현 스크립트) + `assets/sky130_nfet_pfet_lut_sample.npz`(실행 결과
> 샘플)가 짝이다.

## 1. 환경

- **ngspice-46**(Windows 네이티브 빌드, SourceForge, BSD 계열 라이선스) — OSS CAD Suite엔 아날로그
  SPICE 툴이 없어(디지털/FPGA 전용 배포판) 별도 설치. 프로젝트 `CLAUDE.md`에 PATH 등록됨.
- **sky130_fd_pr**(SkyWater 오픈소스 PDK, Apache-2.0, NDA 없음) — `google/skywater-pdk-libs-sky130_fd_pr`
  리포지토리에서 `models` + `cells/nfet_01v8` + `cells/pfet_01v8`만 sparse-checkout(전체 110MB 중
  28MB만).

## 2. 스윕 격자

| 축 | 값 |
|---|---|
| L | 0.15, 0.35, 0.5, 1.0 µm (4개, sky130 01v8 최소 채널 0.15µm 포함) |
| VGS | 0~1.8V, 49점 (Jespers 책 스타일 포인트 수, 1.8V 소자에 맞춰 step=0.0375V) |
| VDS | 0~1.8V, 49점 |
| VS(body bias) | 0, 0.2, 0.4, 0.6, 0.8 V (5점) |
| 기준 소자 폭 | W=5µm 고정 |

NMOS/PMOS 각각 L×VS = 4×5 = 20회 ngspice 배치 실행, 총 40회. **각 실행 내부에서 VGS×VDS
49×49=2401개 바이어스점을 순회하며, 점마다 `.op`(id/gm/gds) + AC 2회(Y11→Cgg, Y12→Cgd)를
수행**(§7 참조 — 처음엔 단순 `.dc` 스윕 + op-info로 Cgg/Cgd까지 뽑으려 했으나 그 방식이 부정확한
것으로 판명되어 이 방식으로 교체). 전체 40회 완주에 약 55분.

## 3. 실전에서 막혔던 지점 (checklist에 없던 실전 함정)

- **L/W 단위 접미사 누락**: `l=0.5`라고 쓰면 0.5"미터"로 해석돼 어떤 bin에도 안 걸려
  "could not find a valid modelname" 에러. `l=0.5u`로 써야 함.
- **nfet_01v8은 `__tt.pm3.spice`만으로는 안 됨**: 그 파일이 참조하는 `..._toxe_slope` 등
  mismatch 파라미터가 별도 파일 `__mismatch.corner.spice`에 있음 — 두 파일을 같이 include.
- **pfet_01v8은 한 겹 더 필요**: 위 두 파일에 더해 `models/parameters/lod.spice`(LOD/WPE 파라미터
  `..._wlod_diff` 등)까지 include해야 함. NMOS는 이게 없어도 통과해서, PMOS만 갑자기 "Undefined
  parameter"가 나면 이게 원인일 확률이 높다.
- **PMOS 부호**: VGS/VDS를 음수로 인가해야 정상 동작(소스 접지 기준 pmos는 VGS<Vth<0에서 도통).
  LUT에는 크기(절대값)로 저장해 NMOS와 동일한 인터페이스를 유지.
- 이상 내용은 `assets/sky130_lut_sweep.py` 상단 docstring에도 반복해 적어뒀다(재사용 시 다시
  겪지 않도록).

## 4. 검증 결과

- gm/ID 최대값: NMOS 29.93 S/A, PMOS 32.20 S/A — 이론치(1/(nUT), n≈1.3 가정 시 ≈29.6)와 일치.
- 두 소자 모두 VGS에 대해 gm/ID **단조감소** 확인(정상적인 물리적 거동).
- `SemiEmpiricalGmIdLUT`(sizing_recipe.py)에 그대로 로드해 sizing 테스트(fT=100MHz, CL=1pF,
  L=0.5µm, VDS=0.9V) 실행 — NMOS/PMOS 모두 gm/ID 8·14에서 정상적인 ID/W/gain 산출.
- Cgg/Cgd(AC/Y-parameter 기반, §7)를 커밋된 `assets/`에서 다시 로드해 재계산해도 독립적으로
  손으로 계산한 단일점 검증값과 **소수점까지 일치**(Cgg=11.600fF, Cgd=1.198fF @ L=0.35µm,
  VGS=0.75V, VDS=0.9V).

## 5. 중요 사례 — "이상치"가 아니라 방법론이 의도한 신호였던 경우

> ⚠️ **W 값 정정(§12에서 발견한 `W_ref` 버그 수정 반영)**: 이 절의 W는 원래 2466µm으로
> 기록됐었다. `SemiEmpiricalGmIdLUT`가 W=5µm 기준폭으로 스윕한 real 데이터를 다루면서
> `gm_id_to_id_density()`가 그 raw 전류를 `W_ref` 보정 없이 반환하던 버그 때문에 W가
> (W_ref/L)=(5/0.5)=10배 작게 나왔었다 — 이 버그는 ID/gm/gain 등 비율에는 영향이 없고 W에만
> 영향을 준다(§12.1 참고). 아래는 수정된 값(**W≈24660µm**)이다 — 결론(PMOS 저이동도로 인한
> W 폭증이라는 물성 자체)은 그대로 유효하며 오히려 더 극적으로 확인된다.

PMOS에서 gm/ID=20(L=0.5µm, VDS=0.9V)을 고르면 **W가 약 24660µm(24.66mm)으로 튐**. 처음엔 LUT
보간 버그로 의심했으나, **정확히 같은 지점을 ngspice로 직접 재시뮬레이션**(VGS=-0.75V, VDS=-0.9V
단일 `.op`)한 결과:

```
ID = 2.5388e-08 A   (LUT 저장값과 정확히 일치)
gm = 4.9889e-07 S   (LUT 저장값과 정확히 일치)
Vth = 0.982V, Vdsat = 45mV
```

— **LUT 값 자체가 정확했다.** W가 커진 이유는 진짜 물성: PMOS는 이동도가 낮아 같은 gm/ID(같은
반전 정도)에서도 전류밀도가 NMOS보다 훨씬 낮다. 이 결과는 격자를 아무리 촘촘히 해도 바뀌지 않는다
(보간 오차가 아니라 정확한 값이므로).

**결론**: `gm-id-methodology.md` §5.2/§9가 경고하는 "나쁜 gm/ID 선택은 W를 비현실적으로 키운다"는
원칙이 toy LUT(§2.7 예제)에 이어 **진짜 실리콘 데이터로도 재현됐다.** 이 지점에서 올바른 설계
대응은 격자 조정이 아니라 gm/ID를 더 작게(strong inversion 쪽) 잡거나 L을 조정하는 것 —
방법론이 정확히 의도한 대로 "나쁜 동작점 선택"을 드러낸 사례다.

## 6. NGCC 3-stage OTA 재현 교차검증 — square-law↔gm/ID 강제변환의 위험

> ⚠️ **W 값 정정**(§12 `W_ref` 버그, L=0.5µm이므로 배율=W_ref/L=5/0.5=10): 아래 W는 수정된 값이다.

`gm-id-methodology.md` §10.2(Lee et al. NGCC 3-stage OTA)를 이 real LUT로 재현해봤다. 이 논문은
square-law 기반이라(§10.2 경고 참조), 논문의 VDSAT=80mV 스펙을 §2.7 다리(`VDsat≈2/(gm/ID)`)로
gm/ID=25 S/A로 변환한 뒤, 논문과 같은 L=0.5µm에서 sky130 real LUT로 sizing했다.

```
gm/ID=25.0 S/A (VDsat=80mV → §2.7 다리),  L=0.5µm, VDS=0.9V

stage1(PMOS,gm1): ID=4.20µA(논문 4.2µA 일치)   W= 8141.2µm  [논문 square-law: W=10.0µm]
stage2(NMOS,gm2): ID=7.44µA(논문 7.4µA 일치)   W=  617.8µm  [논문 square-law: W=4.0µm]
stage3(NMOS,gm3): ID=100.52µA(논문 100µA 일치) W= 8346.6µm  [논문 square-law: W=52.5µm]
```

ID는 (LUT와 무관한 순수 산술이라) 정확히 일치하지만, **W는 real LUT 쪽이 논문 square-law보다
150~800배 크다**(정정 전에는 20~80배로 기록됐었다 — §12의 W_ref 버그로 실제보다 10배 작게
보고됐던 것).

**원인 — 버그가 아니라 §2.7 다리 자체의 한계**: gm/ID=25는 이 LUT의 최대치(~30)에 가까운 꽤 깊은
weak inversion이다(sky130 real 데이터로 확인: 이 지점 VGS≈0.65V 근방, 기준소자 전류가 nA대로
매우 작음) — 필요 전류(수십~수백 µA)를 채우려니 W가 커질 수밖에 없다. 이건 **§9.3에 이미 문서화된
현상의 뒤집힌 표현**이다: "`2/(gm/ID)`가 VDsat을 과대추정한다"는 건, 거꾸로 "VDsat에서 역산한
gm/ID가 실제보다 weak-inversion 쪽으로 더 치우친다"는 뜻이고, 그 결과 필요 이상으로 큰 W가
나온다.

**결론**: **square-law 스펙(VDSAT)을 §2.7 근사식으로 gm/ID에 강제로 끼워 맞추는 건 안전하지
않다.** 진짜 gm/ID 설계는 VDSAT을 거꾸로 계산해서 gm/ID를 유도하는 게 아니라, **처음부터 gm/ID를
스펙·아키텍처 판단으로 직접 선택**해야 한다(§1의 6단계 절차가 원래 이 순서). §5의 "toy LUT라
데이터가 가짜라서 숫자가 안 맞았다"보다 한 단계 더 깊은 교훈 — **real 데이터로도 방법론을 잘못
적용(square-law↔gm/ID 강제 변환)하면 여전히 틀린다**는 것을 확인했다.

## 7. Walker CS/차동쌍 재현과 op-info Cgd/Cdd 오류 발견 — 전체 재스윕으로 이어진 사례

`gm-id-methodology.md` §6.5(Walker CS/차동쌍 pole-zero)를 이 real LUT로 처음부터 재현했다. NGCC(§6)와
달리 이 예제는 **진짜 gm/ID LUT 조회가 필요**하다(square-law가 아님) — 다만 Cgg뿐 아니라 Cgd도
필요해서, 처음엔 기존 방식(nested `.dc` + op-info `@device[cgd]`)으로 Cgd/Cdd를 추가로 뽑았다.

### 7.1 발견 — op-info Cgd/Cdd가 틀렸다

Walker 절차대로 계산하니 fp1이 예상(200MHz대)보다 5배 높게(1115MHz) 나왔다. 원인을 추적하려고
**같은 지점을 AC/Y-parameter로 직접 재확인**(Y11=i_gate/v_gate|v_drain=0 → Cgg, Y12=i_gate/v_drain|
v_gate=0 → Cgd — 게이트 전류만 보므로 gm 오염이 없다)했더니:

| 파라미터 | op-info | AC(Y-parameter) | 배율 |
|---|---|---|---|
| Cgg | 9.136fF | 11.601fF | 1.27배 (양호) |
| Cgd | 0.033fF | 1.198fF | **36배** |
| Cdd | −0.014fF(부호도 틀림) | 4.34fF | **~300배** |

**Cgg는 op-info로도 그럭저럭 쓸 만하지만, Cgd/Cdd는 op-info로 뽑으면 안 된다** — ngspice
BSIM4의 `@device[cgd]`/`@device[cdd]`는 신뢰할 수 없다(비대칭 트랜스-커패시턴스 행렬의 어느
성분을 보고하는지가 모호한 것으로 추정). AC로 뽑은 값은 10MHz~1GHz 대에서 크기가 주파수에
선형 비례해 순수 용량성임을 확인했다(정의가 명확한 물리량).

### 7.2 대응 — 전체 그리드를 AC 기반으로 재스윕

`assets/sky130_lut_sweep.py`를 전면 재작성해 **모든 바이어스점에서 Cgg/Cgd를 AC/Y-parameter로
직접 추출**하도록 바꿨다(id/gm/gds는 기존 op-info 유지 — 이들은 모호하지 않은 스칼라 값이라 신뢰
가능). 격자당(4L×5VS×2소자=40조합) 하나의 ngspice 프로세스 안에서 2401개 바이어스점을 컨트롤
스크립트 `while` 루프로 순회하며 매 점마다 `.op`+AC 2회를 수행 — 총 55분. 조합마다 즉시 체크포인트
저장(재실행 시 이미 끝난 조합은 건너뜀 — 실제로 첫 시도가 세션 타임아웃으로 중간에 죽어서 이
재시작 로직이 실전에서 바로 쓰였다).

### 7.3 Walker 예제 최종 재현 결과 (AC로 고친 real LUT 사용)

> ⚠️ **W/Cgg/Cgd/fp1/fp2 전부 정정**(§12 `W_ref` 버그): 아래 `Cgg=11.599fF, Cgd=1.198fF`는
> **W=5µm 기준소자 자체의 raw 값**이라 이 숫자 자체는 원래도 맞았다 — 문제는 이 raw 값을
> **목표 폭(W)의 실제 소자 것인 양 그대로 fp1/fp2 계산에 썼다는 것**이다. 목표 폭이
> W=3.32µm(버그로 실제보다 5/0.35≈14.3배 작게 계산됨)이면 raw Cgg/Cgd를 그대로 쓰는 게 우연히
> "거의" 맞았겠지만, 올바른 목표 폭은 W=47.39µm이므로 실제 Cgg/Cgd도 그만큼(약 9.5배, 정확히는
> `버그 W/L`배) 커야 한다. 이 스케일링을 반영해 다시 계산했다.

```
gm/ID=13.333 S/A (ITAIL 스펙에서 역산),  L=0.35µm, VDS=0.9V
W=47.393µm  (정정 전: 3.32µm)

기준소자(W=5µm) raw: Cgg=11.599fF  Cgd=1.198fF  — 이 값 자체는 원래부터 정확했다.
실제 목표폭(W=47.393µm) 절대값: Cgg=109.944fF  Cgd=11.357fF  Cgs=98.587fF

fp1=98.54MHz   fp2=3.885GHz

(Walker 원본 180nm: fp1=200MHz(계산)/215MHz(실측), fp2=5.8GHz(계산)/4.8GHz(실측), W=18.6µm)
```
fp1/fp2/W 전부 원본 180nm 논문과 다르다(공정·L·바이어스가 다르니 당연) — 정정 전 문서는 fp2가
"우연히 5.78 vs 5.8GHz로 근접한다"고 적었었는데, 그건 W_ref 버그로 실제보다 작은 Cgg/Cgd를 썼기
때문에 나온 **우연의 일치였을 뿐**이다(버그 수정 후 fp2=3.885GHz로, 더는 근접하지 않는다). 핵심
교훈은 그대로 유효하다 — **AC/Y-parameter로 올바르게 뽑은 Cgg/Cgd**를(§7.1/7.2), 이번엔 **목표
폭까지 올바르게 스케일링해서** 쓴 결과다.

### 7.4 교훈

`lut-generation-checklist.md` §7.3의 기존 경고("gm/gds를 diff() 수치미분으로 뽑지 말고 AC로
뽑아라")가 **커패시턴스(특히 Cgd/Cdd)에도 그대로, 오히려 더 심각하게 적용된다**는 걸 실측
배율(36배, 300배)까지 갖고 확인한 사례. "op-info 파라미터는 이름이 그럴듯해도 무조건 신뢰하지
말 것" — 스칼라 DC 값(id/gm/gds)과 트랜스-커패시턴스 행렬 성분(cgd/cdd)은 신뢰도가 다르다.

## 8. Intrinsic Gain Stage 재현 (Jespers §6.1) — 세 예제 종합

`gm-id-methodology.md` §6.1(I.G.S., 방법론의 가장 기초 예제)도 이 real LUT로 재현했다. Cgd가
필요 없는(Cgg만 있으면 되는) 가장 단순한 예제라 §7에서 AC로 고친 데이터를 그대로 검증하기 좋다.

**스펙**: C=1pF, fT=100MHz, L=0.5µm(격자와 정확히 일치), VDS=0.25~1V 스윕, VS=0.

> ⚠️ **W 정정**(§12 `W_ref` 버그, L=0.5µm 고정이므로 배율=5/0.5=10 균일 적용): 아래 W는 수정된
> 값이다(ID/gain/준정적 여부는 W에 안 의존하는 양이라 원래도 정확했다).

```
gm = 2*pi*fT*C = 0.628mS (스펙으로 고정)

VDS   gm/ID   ID(µA)   W(µm)      gain   준정적(fT≤0.1·f_nqs)
0.25   10.0    62.83     8.07      19.8      True
0.25   15.0    41.89    15.26      44.3      True   <- 원문 "moderate inversion, gain≈40"과 근접
0.50   20.0    31.42    46.40     105.8      True
1.00   25.0    25.13  2071.27     130.9      True   <- W 폭증
```

- gm/ID=15, VDS=0.25V에서 gain≈44.3 — 원문이 찾은 절충점(gain≈40)과 근접(공정이 다른데도).
- 모든 (VDS, gm/ID) 조합에서 준정적 조건 성립 — L=0.5µm이 100MHz엔 충분히 빠르다는 원문 결론과 일치.
- gm/ID=25(이 LUT의 NMOS 최대치 ~29.93에 근접)에서 **또 W가 폭증**(2071µm, 정정 전엔 207µm으로
  기록됐었다 — §12 `W_ref` 버그, L=0.5µm이라 배율 10).

**세 예제 종합**: 애초 후보였던 3개 worked example(§6.1 I.G.S., §6.5 Walker CS/차동쌍, §10.2 NGCC
3-stage)을 전부 이 real sky130 LUT로 재현했다. 세 예제 모두 **독립적으로** gm/ID를 이 LUT의
최대치(~30 S/A) 근처로 밀어붙이면 W가 비현실적으로 커지는 현상을 재현했다(§5의 PMOS gm/ID=20,
§6의 NGCC gm/ID=25, 여기의 gm/ID=25) — 우연이 아니라 **gm/ID 방법론이 실리콘 데이터에서
반복적으로 검증하는 물리적 사실**(weak inversion 깊이 갈수록 전류밀도가 급감)임을 세 번째로
확인한 셈이다.

## 9. 그리드서치 최적화 — "최적 sizing 자동 탐색" 실증

지금까지(§5~§8)는 gm/ID 후보를 몇 개 손으로 골라 결과를 비교하는 방식이었다. `sizing_recipe.py`의
`find_optimal_sizing()`은 이걸 자동화한다 — (L, VDS, gm/ID) 격자 전체를 스윕해 제약조건을
만족하는 점 중 **전력(ID) 또는 면적(W) 최소**인 걸 찾는다.

**스펙**: fT=100MHz, C=1pF, NMOS 전 L·VDS 격자, gm/ID=2.0~28.5(0.5 step), gain≥80,
준정적 여유 10%.

> ⚠️ **정정**(§12 `W_ref` 버그): 전력 최소(power-min)는 ID를 최소화하는데 ID는 W_ref 버그와
> 무관한 양이라 **선택되는 점 자체는 바뀌지 않는다**(W만 재계산). 하지만 면적 최소(area-min)는
> W 자체를 비교해서 고르는데, L마다 보정 배율(5µm/L)이 달라서(L=0.15µm은 33배, L=1.0µm은 5배)
> **버그가 있던 상태에서 "최소"로 골랐던 점이 진짜 최소가 아닐 수 있다** — 실제로 재검색하니
> **L=0.35µm이 아니라 L=0.50µm이 진짜 면적 최소점**이었다(아래는 코드로 재검색한 결과).

```
9469개 후보 평가, 2273개 실행가능(gain>=80, 준정적 만족)

전력 최소: L=0.35µm VDS=0.67V gm/ID=21.0  ID=29.92µA  W=47.044µm  gain=80.8   (점은 동일, W만 정정)
면적 최소: L=0.50µm VDS=1.80V gm/ID= 3.5  ID=179.52µA  W=3.020µm  gain=88.2  (점 자체가 바뀜)
```

같은 gain≥80 제약 아래서도 목적함수만 바꾸면 **완전히 다른 두 sizing**이 나온다 — 전력 최소는
gm/ID=21(weak 쪽, 전류는 작지만 폭이 넓음), 면적 최소는 gm/ID=3.5(strong 쪽, 폭은 작지만 전류가
큼). `gm-id-methodology.md` §5.1 트레이드오프 삼각형을 숫자로, 자동 탐색으로 확인한 것이다.

**부수적으로 발견한 버그**: 이 최적화기를 만들다가 `converge_with_parasitics()`의
`result.gain = gm_id * lut.gm_gds_ratio(...)`가 잘못됐다는 걸 발견했다 — `gm_gds_ratio()`가
이미 완전한 gain(gm/gds)을 반환하는데 `gm_id`를 한 번 더 곱하고 있었다(예: gm/ID=20에서 실제
gain=49.4인데 987.2로 출력). `find_optimal_sizing()` 자체는 `gm_gds_ratio()`를 직접 호출해
이 버그의 영향을 받지 않았고(그래서 개발 중 이 차이를 알아챌 수 있었다), sizing(ID/W) 계산 경로와
이 문서 §7·§8의 Walker/NGCC/I.G.S. 재현 수치들도 별도 경로로 계산돼 영향받지 않았음을 확인했다.
`converge_with_parasitics()`는 수정 완료(현재 커밋에 반영됨).

**한계**: 이산 격자 탐색이라 격자점 사이의 진짜 연속 최적점은 못 찾는다(§7.2 보간으로 gm/ID 자체는
연속이지만 L/VDS는 격자값만 시도). 다단 회로(Miller OTA/NGCC)의 2D sizing space 접점 탐색은
아직 범위 밖 — §6.4/§10의 "등전력·등면적 contour"를 이런 그리드서치로 확장하는 건 자연스러운
다음 단계다.

## 11. topology_library.py — 토폴로지 라이브러리로 분리 + 실측 LUT로 이식 검증

§9의 `optimize_multistage(topology_fn, ...)`는 제네릭 엔진이지만, `miller_ota_topology()`가
`sizing_recipe.py` 안에 같이 있으면 "토폴로지 하나 늘 때마다 이 핵심 파일이 계속 커진다"는
문제가 그대로 남는다. 그래서 `topology_fn` 팩토리들을 `assets/topology_library.py`로 분리하고,
이번에 검증했던 나머지 두 토폴로지(§10.2 NGCC, §10.4 NMCNR)도 같이 추가했다.

**이식 등가성 검증**: `miller_ota_topology`를 새 위치(`topology_library.py`)에서 import해
§9와 완전히 동일한 스펙(GBW=20MHz, CL=3pF, Z=10, NDP=4, 실측 sky130 PMOS/NMOS LUT,
gain_min=[20,20], w_max=[200µm,200µm])으로 재실행한 결과:

```
converged=True iters=4
gm1=0.3047mS gm2=3.0471mS
  stage1(PMOS): L=0.35um VDS=0.53V gm/ID=19.5 ID=15.63uA W=199.795um gain=55.2
  stage2(NMOS): L=0.35um VDS=0.30V gm/ID=24.0 ID=126.96uA W=191.581um gain=57.4
```

파일을 옮기기 전 원래 위치(`sizing_recipe.py` 안)에서 얻은 수치와 **완전히 동일**하다 — 순수
리팩터링이었고 동작 변화가 없었음을 확인.

> ⚠️ **정정**(§12 `W_ref` 버그): 위 "이식 등가성"(리팩터링 전후가 똑같은 숫자를 낸다) 자체는
> 여전히 유효하다(양쪽 다 같은 버그를 갖고 있어서 서로는 정확히 일치했다). 하지만 **절대 수치
> 자체가 W_ref 버그의 영향을 받았다** — `w_max=200µm` 제약이 버그 있는 W(실제보다 5/L배 작게
> 계산됨)로는 "거의 걸리기 직전"이었는데, 올바른 W로는 그 제약을 훨씬 일찍 넘어서 버려서 그리드
> 서치가 **완전히 다른 동작점**을 골랐다. 수정된 코드로 재검색한 결과:
> ```
> converged=True iters=4
> gm1=0.3680mS gm2=3.6801mS
>   stage1(PMOS): L=0.50um VDS=0.11V gm/ID=17.0 ID=21.65uA W=187.336um gain=20.4
>   stage2(NMOS): L=0.15um VDS=1.24V gm/ID=20.5 ID=179.52uA W=199.844um gain=30.2
> ```
> L 자체가 스테이지1은 0.35→0.50µm, 스테이지2는 0.35→0.15µm로 바뀌었고 gm/ID도 더 strong
> inversion 쪽으로(19.5→17.0, 24.0→20.5) 이동했다 — `w_max` 제약이 실제로 바인딩되는 상황에서는
> §9의 면적-최소 케이스처럼 **버그가 있으면 최적점 자체가 달라질 수 있다**는 걸 다시 한번 보여준다.

**새로 추가한 두 토폴로지의 스모크 테스트** (`python topology_library.py`):

```
# Miller 2단 OTA (GBW=20MHz, CL=3pF, Z=10, NDP=4) — prev_cggs=None(초기 반복) 기준
  gm1=0.3901mS  gm2=3.9005mS
# NMCNR 3단 (GBW=5MHz, CL=10pF, PM_target=70deg, kg=0.5)
  gm1=7.1267mS  gm2=0.6283mS  gm3=1.2566mS
# NGCC 3단 (Lee et al. Table 4 예제: k=4, GB=10MHz, CL=10pF, alpha=0.3) — 전체 재현
  gm1=0.1056mS  gm2=0.1866mS  gm3=2.5133mS  (원문 Table 4: gm1=0.105mS gm2=0.186mS gm3=2.5mS)
```

(Miller OTA의 위 수치는 `prev_cggs=None`인 첫 반복 값이라 §9/위 등가성 검증의 수렴값과는
다르다 — 반복이 수렴해야 실제 sizing에 쓸 gm이 나온다는 것을 보여주는 참고용 스냅샷이다.)

**NGCC 관련 정정**: 처음에는 "gm1/gm2 유일해에 필요한 원문 비용함수 최적화(Eq 8.a/8.b)가 이
세션에서 OCR 손상으로 재현 안 됨"이라 기록하고 `gm2/gm1` 비율을 근사 자유도로 노출했었다. 이건
**틀린 판단이었다** — 실제로는 PDF 텍스트 추출이 수식 분수/위첨자를 뒤섞었을 뿐이고, 해당
페이지(원문 p.23)를 300dpi 이미지로 렌더링해서 직접 읽으니 Eq 8.a/8.b가 완전히 판독됐다. 이
식들로 `mu_n/mu_p≈3.9775`(원 논문 0.18µm 공정 예제 역산값)를 넣으면 Table 4의 `gm1=0.105mS,
gm2=0.186mS`가 정확히 재현되고, Eq 7 선형 제약도 동시에 만족한다(삼중 교차검증). 유도 전체
과정은 `topology-fn-derivation-guide.md` §4 참고 — `ngcc_3stage_topology()`는 이제 근사가
아니라 `mu_ratio`(공정의 이동도 비, 설계 자유도 아님)만 요구하는 **완전 결정** 함수다.

**NMCNR도 원문 이미지로 재확인**: 원문(Ka Nang Leung, Philip K. T. Mok, Wing-Hung Ki, "Right-Half-
Plane Zero Removal Technique for Low-Voltage Low-Power Nested Miller Compensation CMOS Amplifier",
IEEE 1999) p.601을 이미지로 렌더링해 Eq (6)~(11)을 전부 직접 판독했다 — 기존에 유도했던
Cm1/Cm2/GBW/PM 식이 원문과 **정확히 일치**함을 확인. 그리고 `kg`(=gm2/gm3)에 대해서도 확정:
원문은 "Cm1/Cm2를 Eq(8)/(9)로 잡으면 3차 Butterworth 극점 배치가 된다"고 설명할 뿐, `kg` 자체를
정하는 별도 방정식이나 수치 예제는 원문 어디에도 없다. 즉 이건 NGCC처럼 "재구성 실패"가 아니라
**"원문 자체가 kg를 자유도로 남겼다"는 확정된 사실**이다.

**정직한 한계**:
- NMCNR의 `kg`(=gm2/gm3)는 원문이 확정한 진짜 자유도다(위 재확인 참고) — 기본값 0.5는 임의값일
  뿐 일반해가 아니다. 실사용 전 SPICE로 PM/GBW를 재확인할 것. (NGCC는 위 정정으로 이 범주에서
  빠졌다 — `mu_ratio`는 설계 자유도가 아니라 공정 파라미터라 SPICE 재확인이 필요한 "자유도"가
  아니다.)
- 두 토폴로지(NMCNR, NGCC) 모두 real sky130 LUT로 `optimize_multistage()`를 끝까지 돌려
  sizing(L/VDS/W)까지 실증하지는 않았다(Miller OTA만 실증됨) — gm 산출 로직만 검증한 상태다.
- `topology_fn`이 `prev_cggs`를 쓰는지(Miller OTA) 안 쓰는지(NMCNR, NGCC)는 토폴로지 고유의
  성질일 뿐, `optimize_multistage()` 엔진은 두 경우 모두 동일하게 동작한다(수정 불필요) — 이
  라이브러리 구조가 실제로 "새 토폴로지 = 새 topology_fn 몇 줄"임을 보여주는 두 번째 증거다.

## 12. NMCNR을 실제 회로로 조립해 GBW/PM SPICE 검증 — `SemiEmpiricalGmIdLUT`의 실제 버그 발견

§11에서 "kg 기본값은 SPICE로 재확인 필요"라고 적어뒀던 그 재확인을 실제로 했다 — NMCNR 3단을
`optimize_multistage()`로 사이징한 뒤, 실제 sky130 소자로 3단 캐스케이드 + 위상보상망(Cm1, Rm+Cm2,
CL)을 SPICE에 직접 조립해 AC 시뮬레이션으로 GBW/PM을 측정했다.

### 12.1 사이징 도중 발견한 진짜 버그 — `gm_id_to_id_density()`가 W를 (W_ref/L)배만큼 작게 계산

스펙(GBW=5MHz, CL=10pF, PM_target=70°, kg=0.5)으로 3단을 사이징해 SPICE 넷리스트에 넣었더니
**DC 동작점이 완전히 발산**했다(드레인 노드가 VDD=1.8V를 넘어 6V대로 치솟음). 원인을 추적한 결과:

- `size_transistor()`/`find_optimal_sizing()`가 쓰는 공식 `W = L*ID/IDu`는 IDu가 **"W/L=1 기준
  전류"**일 때만 성립한다(`build_toy_lut()`는 실제로 W\*=L 관례로 데이터를 합성해서 문제없다).
- 하지만 `SemiEmpiricalGmIdLUT`(sky130 실측 데이터, **고정 기준폭 W=5µm**에서 스윕)의
  `gm_id_to_id_density()`는 그 5µm 기준폭에서 잰 raw 전류값을 **아무 변환 없이 그대로** 반환하고
  있었다 — L=0.15µm 소자라면 필요한 "W/L=1 기준 전류"보다 5/0.15=**33배** 큰 값을 잘못 쓴 셈이라,
  계산된 W가 실제 필요한 값의 1/33밖에 안 됐다.
- **SPICE로 직접 검증**: 같은 VGS/VDS에서 단일 기준소자(W=5µm)의 실제 전류를 재보고, N개를
  병렬로 연결했을 때 전류가 정확히 N배가 되는지 확인해 배율(L/W_ref)을 독립적으로 확인했다.

**수정**: `SemiEmpiricalGmIdLUT.__init__`에 `W_ref` 파라미터를 추가(기본값 `None`=toy LUT의
W\*=L 관례 그대로 유지, 숫자를 주면 `raw_ID * L/W_ref`로 환산), `gm_id_to_id_density()`를
고치고, 다음 단 게이트 커패시턴스 feedback(`optimize_multistage`의 `prev_cggs`)에 쓰던
`_query(CGG,...)`도 같은 문제(기준폭 Cgg를 목표폭 Cgg인 것처럼 잘못 씀)가 있어 새 메서드
`cgg_absolute(gm_id, L, vds, vs, W_target)`로 교체했다. `build_toy_lut()` 경로(`W_ref=None`)는
회귀 없이 그대로 동작함을 재확인.

⚠️ **영향 범위**: 이 버그는 `SemiEmpiricalGmIdLUT`를 sky130 npz 데이터로 만들 때 `W_ref`를
지정하지 않은 **모든 계산**에 있었다 — §5~§9, §11의 모든 W 수치가 대상이다(gm/ID/ID/gain/VGS/fT
**비율**은 W에 안 곱해지는 양이라 영향 없음). 이 문서의 나머지 절들도 순차적으로 재계산해 고친다.

### 12.2 수정된 코드로 재사이징 — 물리적으로 타당한 결과

`objective="power", gain_min=10, w_max=200µm`(Miller OTA §11과 동일 관례)로 재사이징:

```
stage1: L=0.150um VDS=0.975V gm/ID=19.00 ID=375.092uA W=199.722um gain=24.69
stage2: L=0.350um VDS=0.300V gm/ID=23.00 ID= 27.318uA W=196.469um gain=56.67
stage3: L=0.150um VDS=0.900V gm/ID=22.00 ID= 57.120uA W=199.961um gain=24.21
```

### 12.3 SPICE 조립 — 3단 캐스케이드 + Cm1/Rm+Cm2/CL

각 스테이지를 LUT 기준소자(w=5µm, nf=1)와 동일 지오메트리의 **병렬 유닛 소자 N개**로 실현했다
(N1=40, N2=39, N3=40 — `nf` 파라미터로 폭을 키우면 이 PDK의 모델 비닝(wmax=100µm)을 벗어나
"could not find a valid modelname"가 나서, 실제 레이아웃처럼 병렬 유닛 소자로 구현). 스테이지
사이는 AC 결합(1µF 커패시터 + 1GΩ 바이어스 저항)으로 각 단의 DC 동작점을 독립적으로 유지하면서
신호만 통과시켰다. Cm1=4(gm1/gm3)CL=226.86pF, Cm2=[2/(1-kg)](gm2/gm3)CL=20.0pF, Rm=1/gm3=795.8Ω
(전부 목표 gm1/gm2/gm3로 계산 — 실제 SPICE gm1/gm2/gm3가 목표 대비 <0.3% 오차로 일치함을 `.op`로
확인해 이 값들이 유효함을 검증했다).

### 12.4 결과 — GBW/PM이 설계식과 다르고, 노치(notch)가 있다

```
DC gain = 90.8dB,  DC phase ≈ -179.6° (3단 반전 캐스케이드라 정상)

1차 0dB 교차: GBW≈1.66MHz  PM≈62.0°   (설계 목표: GBW=5MHz, PM=70°)
2차 0dB 교차: f≈103MHz     PM≈-102°   (교차 재발생 — 조건부 안정성 신호)

교차 사이(~2MHz 부근)에 깊은 노치: 이득이 -21dB까지 떨어졌다가 다시 +8~11dB로 회복
```

**GBW는 목표의 1/3, PM은 목표보다 8° 낮지만 여전히 >60°**(NMCNR의 기본 주장 자체는 유지) —
하지만 **2차 0dB 교차와 노치는 설계식(Eq 10/11)이 전혀 예측하지 못하는 현상**이다.

### 12.5 원인 진단

- **Rm/gm3 불일치는 아니다**: 실제 SPICE stage3의 gm3(=1.2567mS)가 목표(1.2566mS)와 <0.01%
  일치 — Rm=1/gm3 널링이 거의 완벽하게 성립한다. RHP-zero 잔류가 원인이 아니다.
- **이상화된 3소자 모델(Eq 6/7)도 정확한 단일 우세극이 아니다**: 목표 gm1/gm2/gm3/Cm1/Cm2로
  직접 Eq 6을 계산해보면(우세극 p-3dB=wGBW/ADC로 올바르게 정규화) 300kHz~10MHz 구간에서 이득이
  14~17dB 근방에서 거의 평평해지는(완만한 하강) 구간이 나온다 — **LHP zero(zLHP=gm3/Cm1≈882kHz)가
  우세극 롤오프를 부분적으로 상쇄**하는, 원문 Eq 11이 의도한 바로 그 메커니즘이다.
- **하지만 실측 SPICE는 이 평평한 구간이 아니라 실제 -21dB짜리 깊은 노치**를 보인다 — 이상화
  모델보다 더 나쁜 거동이다. 이 차이의 정확한 물리적 근원(스테이지 간 로딩, LUT 보간 오차로 인한
  개별 스테이지 gain 값의 작은 편차 등)은 이번 세션에서 완전히 규명하지 못했다 — **정직한 한계**로
  남긴다.
- **kg=0.5는 원문이 확정한 자유도**(§11 참고)이고, 이 특정 선택이 극-영점을 서로 가깝게 몰아
  (crowding) 실제 회로가 이상화된 설계식보다 훨씬 민감하게 반응하도록 만든 것으로 보인다.

### 12.6 kg 스윕(0.1~0.9) — 노치는 kg로 안 없어진다

stage1/stage3는 kg와 무관(gm1, gm3는 topology_fn에서 kg 없이 고정)하므로 그대로 두고, stage2와
Cm2만 kg에 맞춰 다시 사이징·재조립해 kg=0.1~0.9(9점) 전부 SPICE AC로 확인했다:

| kg | DC gain | 1차 교차 GBW | 1차 교차 PM | 2차 교차 f | 2차 교차 PM |
|---|---|---|---|---|---|
| 0.1 | 91.1dB | 1.98MHz | **69.7°** | 103.1MHz | -101.4° |
| 0.2 | 91.0dB | 1.97MHz | 67.7° | 103.8MHz | -102.0° |
| 0.3 | 90.0dB | 1.88MHz | 65.6° | 102.6MHz | -102.2° |
| 0.4 | 91.0dB | 1.78MHz | 64.4° | 103.4MHz | -102.2° |
| 0.5 | 90.8dB | 1.66MHz | 62.0° | 102.7MHz | -102.3° |
| 0.6 | 79.3dB | 1.51MHz | 42.4° | 104.4MHz | -102.5° |
| 0.7 | 90.6dB | 1.35MHz | 54.4° | 103.1MHz | -102.3° |
| 0.8 | 77.4dB | 1.11MHz | 26.7° | 104.7MHz | -102.6° |
| 0.9 | 80.7dB | 0.81MHz | 19.7° | 104.6MHz | -102.6° |

**결론 — 이 GBW/PM_target 스펙에서는 kg로 노치를 없앨 수 없다**:

- **2차 0dB 교차(노치)가 kg=0.1~0.9 전 구간에서 사라지지 않는다** — 9점 전부 교차가 2번씩
  나온다. kg 조정만으로는 이 문제를 해결 못 한다.
- **kg가 작을수록 1차 교차의 PM이 좋아진다**(단조 경향) — kg=0.1에서 PM≈69.7°로 설계 목표
  (70°)에 가장 근접.
- **2차 교차(~103MHz, PM≈-102°)는 kg와 거의 무관하게 고정돼 있다** — Cm2/stage2가 kg에 따라
  크게 바뀌는데도(Cm2가 2.2pF~180pF까지 82배 변함) 2차 교차 위치·PM은 거의 안 변한다. 이건 이
  노치의 원인이 **NMCNR 보상망(Cm1/Cm2/Rm) 자체가 아니라, 실제 트랜지스터의 고차 기생 효과**
  (원문의 단순화된 2-pole+1-zero 모델이 담지 못하는 부분)일 가능성을 시사한다 — §12.5의 "정확한
  물리적 근원 미규명"이 여전히 정직한 한계로 남는다.

**결론**: `nmcnr_3stage_topology()`의 기본값(kg=0.5)으로 얻은 gm 목표를 실제 sky130 소자로
사이징·조립한 결과, **설계식이 예측하는 GBW/PM과 실측 SPICE 결과가 상당히 다르다**(GBW 3배
낮음, 2차 0dB 교차로 인한 조건부 안정성 신호) — `topology-fn-derivation-guide.md`/`SKILL.md`가
이미 "kg는 원문 확정 자유도, 실사용 전 SPICE 재확인 필요"라고 경고한 바로 그 상황이 실제로
일어난 것을 확인했다. kg를 실제로 스윕해보니(§12.6) **1차 교차 PM은 kg를 낮출수록 개선되지만
(kg=0.1에서 설계 목표에 근접), 2차 교차/노치 자체는 이 범위에서 없어지지 않는다** — NMCNR을
이 스펙대로 실제로 쓰려면 노치의 물리적 근원(실소자 고주파 기생 추정)을 별도로 규명해야 하며,
이건 이 세션의 범위 밖으로 남겨둔다.

## 10. 알려진 한계 (다음에 확장할 것)

- L 4개·기준폭 W=5µm 고정 — 실사용엔 더 조밀한 L 격자, 여러 기준폭 교차검증 권장(§3.1.2 실측
  논문 기준 W 의존성 존재).
- junction cap 파라미터(ad/as/pd/ps)는 그럴듯한 placeholder — 실제 레이아웃 반영 안 됨.
- corner는 tt(typical)만 — ff/ss 등 다른 corner는 미실행.
- Cdd는 AC(Y22)로도 검증했지만 최종 npz에는 아직 포함하지 않음(Cgg/Cgd만 필요한 예제 위주로
  검증) — 필요시 §7.2 방식 그대로 Y22 추출을 추가하면 된다.
- 이 문서의 npz는 **검증된 데모 샘플**이지 양산 sizing에 쓸 만큼 조밀한 격자는 아니다(정직한 한계).
