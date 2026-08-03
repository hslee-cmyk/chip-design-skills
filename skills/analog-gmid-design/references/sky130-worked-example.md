# sky130 실전 LUT 예제 — toy가 아닌 진짜 실리콘 데이터

> `references/gm-id-methodology.md`·`lut-generation-checklist.md`는 방법론과 절차를 다룬다.
> 이 문서는 그 절차를 **실제로 오픈소스 PDK + SPICE 시뮬레이터로 끝까지 실행해본 결과**를 기록한다 —
> `assets/sky130_lut_sweep.py`(재현 스크립트) + `assets/sky130_nfet_pfet_lut_sample.npz`(실행 결과
> 샘플)가 짝이다.

## 1. 환경

- **SPICE 시뮬레이터**(이 세션 실행 환경: ngspice-46, Windows 네이티브 빌드, BSD 계열 라이선스 —
  방법론 자체는 특정 시뮬레이터에 종속되지 않으며 Spectre/HSPICE 등 다른 SPICE 시뮬레이터로도
  동일하게 재현 가능하다). OSS CAD Suite엔 아날로그 SPICE 툴이 없어(디지털/FPGA 전용 배포판)
  별도 설치. 프로젝트 `CLAUDE.md`에 PATH 등록됨.
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

NMOS/PMOS 각각 L×VS = 4×5 = 20회 SPICE 배치 실행, 총 40회. **각 실행 내부에서 VGS×VDS
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
- **`gm_id_to_id_density()`가 반환하는 `IDu`를 SPICE로 "직접" 검증하려 할 때 흔한 함정**(100-channel
  neural recording IC 예제 검증 중 실제로 40분을 낭비하며 발견): `IDu`는
  **"W=L(단위 소자) 기준" 전류밀도**이지 "LUT의 실측 기준폭(W_ref=5µm)에서의 전류"가 **아니다**.
  "이 gm/ID·L·VDS에서 LUT가 맞는지 SPICE로 확인해보자"며 `W=W_ref=5µm`짜리 소자를 SPICE에 직접
  인스턴스화해서 나온 전류를 `IDu`와 곧바로 비교하면, 정확히 `W_ref/L`배만큼 차이가 나는 게
  **정상**인데(L=1µm이면 5배, L=0.5µm이면 10배 — §5의 "10배 버그"와 겉보기엔 비슷하지만
  원인은 다르다: 그건 실제 코드 버그였고, 이건 애초에 다른 두 정규화를 비교한 **검증 방법론
  실수**다) 이걸 "LUT가 SPICE 대비 N배 틀렸다"는 진짜 버그로 오인하기 쉽다. 실제로 이 세션에서
  그렇게 오인해 멀쩡한 LUT를 스테일(stale) 데이터로 의심하고 처음부터 전체 재스윕(~40분)까지
  실행했었다 — 재스윕 후에도 "오차"가 똑같이 나와서야 비교 방식 자체가 잘못됐음을 발견했다.
  **올바른 검증 방법**: `IDu`를 직접 SPICE와 비교하지 말고, 이 skill이 실제로 쓰는 방식 그대로
  `W = L·ID_target/IDu`로 사이징한 뒤, **그 W로** SPICE에 인스턴스화해서 `ID_target`이 나오는지
  확인할 것(이렇게 하면 정규화가 스스로 상쇄되어 일치해야 정상 — 실제로 재확인 시 101% 일치).
  즉 "LUT 예측치 vs SPICE 실측치"를 비교할 땐 **반드시 이 skill의 사이징 공식을 거친 뒤의 값**으로
  비교할 것 — LUT의 중간 산출물(IDu 등)을 그 자체로 SPICE와 직접 비교하지 말 것.

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
보간 버그로 의심했으나, **정확히 같은 지점을 SPICE 시뮬레이터로 직접 재시뮬레이션**(VGS=-0.75V, VDS=-0.9V
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

**Cgg는 op-info로도 그럭저럭 쓸 만하지만, Cgd/Cdd는 op-info로 뽑으면 안 된다** — SPICE
시뮬레이터의 BSIM4 op-info(`@device[cgd]`/`@device[cdd]` 계열)는 신뢰할 수 없다(비대칭 트랜스-커패시턴스 행렬의 어느
성분을 보고하는지가 모호한 것으로 추정). AC로 뽑은 값은 10MHz~1GHz 대에서 크기가 주파수에
선형 비례해 순수 용량성임을 확인했다(정의가 명확한 물리량).

### 7.2 대응 — 전체 그리드를 AC 기반으로 재스윕

`assets/sky130_lut_sweep.py`를 전면 재작성해 **모든 바이어스점에서 Cgg/Cgd를 AC/Y-parameter로
직접 추출**하도록 바꿨다(id/gm/gds는 기존 op-info 유지 — 이들은 모호하지 않은 스칼라 값이라 신뢰
가능). 격자당(4L×5VS×2소자=40조합) 하나의 SPICE 프로세스 안에서 2401개 바이어스점을 컨트롤
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
아직 범위 밖 — `gm-id-methodology.md` §6.4/§10의 "등전력·등면적 contour"를 이런 그리드서치로
확장하는 건 자연스러운 다음 단계다.

## 10. 알려진 한계 (다음에 확장할 것)

- L 4개·기준폭 W=5µm 고정 — 실사용엔 더 조밀한 L 격자, 여러 기준폭 교차검증 권장(§3.1.2 실측
  논문 기준 W 의존성 존재).
- junction cap 파라미터(ad/as/pd/ps)는 그럴듯한 placeholder — 실제 레이아웃 반영 안 됨.
- corner는 tt(typical)만 — ff/ss 등 다른 corner는 미실행.
- Cdd는 AC(Y22)로도 검증했지만 최종 npz에는 아직 포함하지 않음(Cgg/Cgd만 필요한 예제 위주로
  검증) — 필요시 §7.2 방식 그대로 Y22 추출을 추가하면 된다.
- 이 문서의 npz는 **검증된 데모 샘플**이지 양산 sizing에 쓸 만큼 조밀한 격자는 아니다(정직한 한계).

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

### 12.3 SPICE 검증 — 노치는 없다(2026-07-31, 이전 조사에서 쓴 잘못된 보상망 배선을
발견하고 삭제 후 재작성)

이 절은 원래 "3단 캐스케이드 조립 → 노치 발견 → kg 스윕 → 원인 규명"이라는 긴 조사였는데,
**그 조사 전체가 Cm1/Rm/Cm2를 "Cm1은 V1↔Vout 직결, Rm+Cm2가 직렬로 V2↔Vout"이라는 잘못된
배선으로 조립한 것**이었음이 드러나 전부 삭제하고 다시 썼다. 실제 논문(Leung/Mok/Ki, 1999)
Fig.3을 사용자와 함께 확대 이미지로 node-by-node 재확인한 결과, 진짜 구조는 **Cm1과 Cm2가
하나의 공통 노드(NodeCM)에서 만나고, 그 뒤에 Rm 하나를 Cm1/Cm2가 공유**한다 — 논문 abstract의
"using only ONE null resistor"와 정확히 일치(예전 배선은 이 문장과도 안 맞았다). 당시엔 원문
이미지 없이 기억으로 배선을 재구성하다가 이 오류가 생겼다.

**1) 4-노드 KCL 재유도**: V1(스테이지1 출력)/V2(스테이지2 출력)/NodeCM/Vout 네 노드로 KCL을
세워(`sympy.solve()`) 정확한 전달함수를 구했다(분자 2차/분모 3차). `topology_library.py`의
`nmcnr_predict_notch()`가 이 4-노드 모델로 구현돼 있다.

**2) 대표 동작점(gm1=7.1267mS, gm2=0.6283mS, gm3=1.2566mS, R1=3465Ω, R2=90188Ω,
R3=19269Ω, CL=10pF, kg=0.5)을 정정된 식에 대입**:

```
DC 이득 90.60dB, DC 위상 -0.41°(2-반전+1-비반전 net 비반전, 이론과 일치)
교차 1번뿐(GBW≈25.7MHz대, PM≈44.8°) — 노치 없음
```

이상화 소신호 netlist(VCCS+ro, sky130 PDK와 무관한 순수 검증용)로 ngspice AC 해석까지
교차검증: DC이득 90.599dB·DC위상 -0.4067°·PM 44.87°로 sympy 해석해와 정확히 일치(오차
수치오차 수준).

**3) 실제 sky130 트랜지스터로도 재확인**: 3개 스테이지를 실제 sky130 NMOS(각각 이상적 전류원
부하 + AC 결합으로 독립 DC 동작점 유지)로 조립하고 정정된 Cm1/Cm2/Rm(같은 공식, 실측 gm으로
재계산)을 붙여 AC 스윕 — **여기서도 교차 1번, 노치 없음**을 확인했다(DC 위상은 실제
트랜지스터 3개 전부가 물리적으로 반전(common-source) 구조라 net 반전(-180° 근방)이 나오는데,
원문의 "-Av1,+Av2,-Av3"[스테이지2만 비반전]를 정확히 재현하려면 스테이지2를 실제 M201-M204
구조로 만들어야 한다 — 이번엔 계산 편의상 3개 다 단순 CS로 단순화했다. 180°를 보정하면
이상화 모델과 위상이 일치한다. 이 부호 차이는 **크로싱 횟수(노치 유무)엔 영향이 없다** —
전역 위상 오프셋은 |H(jw)| 크기를 바꾸지 않는다).

**결론**: 이전 조사가 보고했던 노치·kg 스윕 결과는 **전부 잘못된 배선에서 나온 것이었다.**
올바른 배선으로는 (적어도 위 동작점에서는) 노치가 나타나지 않는다 — NMCNR의 원래 설계식
(Eq 10/11)이 예측 못 하는 이상 현상 자체가 없었을 가능성이 높다. 실제 kg 스윕/최적 설계점
탐색은 이 정정된 토폴로지로 처음부터 다시 해야 한다(이 세션 스코프 밖 — 후속 배치로 이월).

---

## 13. 2026-07-29 논문 재확인 — current-reuse telescopic OTA topology.json 오류 3건 발견·수정

> **왜 이 섹션이 필요한가**: `library/current_reuse_telescopic_ota.topology.json`(§11에서 만든
> topology library JSON 체계로 이 회로를 등록한 것)의 2026-07-28 버전이 실제로는 논문 본문/
> 부록 스키매틱을 충분히 정밀하게 재확인하지 않은 채 만들어졌다 — 이번에 사용자와 함께 **논문
> PDF를 처음부터 끝까지(부록 포함) 다시 읽고, 회로도를 이미지로 직접 재판독**해서 오류 3건을
> 찾아 고쳤다. 다음에 이 topology.json을 다시 손볼 일이 생기면(예: 배치 7-3 gm2 Eq.6 재유도),
> **이 표를 먼저 참고하고 같은 재확인 작업을 반복하지 말 것** — 아래는 이미 검증 완료된 매핑이다.

### 13.1 발견된 오류 3건

| # | 오류 | 근본 원인 | 근거 |
|---|---|---|---|
| 1 | bias-gen 소자 9개(M27,M28,M29,M33,M34,M31,M32,M30,M35)가 전부 가상의 소자였음 | 논문 III.C절("Biasing Circuit")의 "the other side of Vx and Vy is marked in **Figure 3**"는 오탈자(Figure 2가 맞음) — Fig.4는 실제 회로가 아니라 Fig.2 아키텍처(Vbias1/Vbias2 자리를 Vip/Vim으로 바꾼 변형)를 설명하기 위한 참고 다이어그램이다. 실제 bias-gen은 Appendix **Fig.8**(완전히 다른 Cadence 인스턴스 이름) | 사용자가 논문 재열람하며 직접 지적(2026-07-29 대화) |
| 2 | Class-AB 2단의 Vop측(좌측) 12개 소자가 통째로 누락 | Fig.1(전체 스키매틱)엔 Vom측(Fig.3에 그려짐)과 별개로 Vop측 미러(M22/M20a/M20b/M17/M18a/M18b/M21/M19/M24b/M23a, Fig.3엔 안 그려짐)가 실제로 존재. 2026-07-28 버전은 M13/M25/M26 3개 placeholder만 넣고 M26의 gate까지 Vom측 M16과 잘못 공유시킴 | Fig.1 전체 스키매틱 재판독 + Appendix **Fig.7**(2단 size/DC 동작점)로 Vop/Vom 양쪽 교차검증 |
| 3 | M9a(및 Vop측 대응 M18a)의 극성이 nmos로 잘못 기재 | Monticelli floating current source는 PMOS+NMOS **상보쌍**인데 둘 다 nmos로 들어가 있었음 | Appendix **Fig.7** DC 동작점의 id 부호로 확인(M46 id=-338.8n=PMOS, M45 id=857.2n=NMOS) |

### 13.2 Fig.6 appendix ↔ topology.json 1단(stage-1) 매핑 — 확정(HIGH confidence)

Cadence가 appendix 스키매틱에 자동으로 붙인 로컬 인스턴스 이름(M0,M1,...,M9)은 **논문 Fig.1/2의
M1a,M2a 같은 이름과 완전히 무관**하다 — 아래는 Vip/Vim/Vom1/Vop1/Vcmfb 라벨이 정확히 겹치는 것으로
행(row) 위치 기준 매칭한 결과(사용자가 5행 게이트 연결을 직접 확인해줌: M3→Vip, M5→Vim).

| topology.json 이름 | gate | Fig.6 appendix 로컬 이름 | 확인 근거 |
|---|---|---|---|
| M6 | Vbias1 | M8 | 1행 좌측 |
| M7 | Vcmfb | M43 | 1행 우측, gate="Vcmfb" 라벨 일치 |
| M1a | Vip | M0 | 2행 좌측, gate="Vip" 라벨 일치 |
| M1b | Vim | M7(로컬) | 2행 우측, gate="Vim" 라벨 일치 |
| M2a | Vbias2 | M2(로컬) | 3행 좌측, gate="Vbias_p1"(=Vbias2), "Vom1" 라벨 일치 |
| M2b | Vbias2 | M6(로컬) | 3행 우측, "Vop1" 라벨 일치 |
| M3a | Vbias3 | M1(로컬) | 4행 좌측, gate="Vbias_n1"(=Vbias3) |
| M3b | Vbias3 | M4(로컬) | 4행 우측 |
| M4a | Vip | M3(로컬) | 5행 좌측, gate=Vip **사용자 확인** |
| M4b | Vim | M5(로컬) | 5행 우측, gate=Vim **사용자 확인** |
| M5 | Vbias4 | M9(로컬) | 맨 아래 tail |

### 13.3 로컬 net 이름 ↔ main 회로 net 이름 매핑

appendix 스키매틱(Fig.6/7/8)은 자기만의 로컬 bias net 이름을 쓴다 — main 회로(Fig.1/2, topology.json)의
Vbias1~4와는 다음처럼 대응된다(Fig.6/7/8 교차 등장으로 확인):

| appendix 로컬 이름 | main 회로 이름 | 확인 근거 |
|---|---|---|
| Vbias_p2 | Vbias1 | Fig.6/7/8에 공통으로 top PMOS(M6/M8/M13류) 게이트로 등장 |
| Vbias_p1 | Vbias2 | Fig.6에서 M2a/M2b류(캐스코드) 게이트로 등장 |
| Vbias_n1 | Vbias3 | Fig.6에서 M3a/M3b류 게이트로 등장, Fig.8에서 동일 이름으로 생성됨 |
| Vbias_n2 | Vbias4 | Fig.6/7/8 공통, tail류 게이트 |
| Vbias_p | Vbias2 | Fig.8의 M57/M58 브랜치 출력 — §13.5에서 배선 확정 후 확인 |

### 13.4 Fig.8 bias-gen 실제 소자 — 전체 확정(소자명·사이즈·DC 동작점·배선 전부)

| 소자 | 종류 | L/W | id/vgs/vds |
|---|---|---|---|
| M18(bias-gen, topology.json엔 `M18_bg`로 개명 — Class-AB의 M18a/M18b와 이름 충돌 방지) | pch | 360n/3u | -1.2µ/-502.4m/-502.4m(diode) |
| M60 | pch | 360n/3u | -1.395µ/-502.4m/-1.33 |
| M61 | pch | 360n/3u | -1.273µ/-502.4m/-801.1m |
| M64 | nch | 1.26µ/2u | 1.273µ/581.7m/581.7m |
| M63 | nch | 1.26µ/330n | 1.273µ/699.1m/117.5m |
| M58 | pch | 1.44µ/750n | -1.534µ/-748.3m/-189.3m |
| M57 | pch | 1.44µ/6u | -1.534µ/-550m/-558m |
| M66 | nch | 360n/2u | 1.395µ/470.2m/470.2m(diode) |
| M68 | nch | 360n/2u | 1.534µ/470.2m/791.4m |

### 13.5 2026-07-30 후속 세션 — 남은 LOW confidence 항목 전부 사용자와 재검증해 해소

13.4의 M63/M58/M57/M68은 처음엔 "정확한 배선 미확정(LOW)"으로 남겨뒀었다. 이후 대화에서 사용자가
직접 확대 이미지를 보며 하나씩 확인해줘서 전부 HIGH confidence로 승격했다:

| 항목 | 처음 추측(틀림) | 실제(사용자 확인) |
|---|---|---|
| M58/M57의 "vdd" 라벨 | 각자 독립적으로 VDD에 소스 연결 | **PMOS의 well/body bias 태그일 뿐** — 실제로는 M61이 공급하는 직렬 stacked diode |
| M58/M57 게이트 | M58=자기 자신 diode, M57=gate**Vip**(replica로 오독) | **둘 다 게이트가 M57의 drain(=Vbias_p)으로 함께 묶임** — M58도 M57도 "자기 자신"이 아니라 스택 맨 아래에 diode-connected |
| M68의 연결 대상 | 미확정 | **M57의 drain과 같은 노드(Vbias_p)** — VDD→M61→M58→M57→M68→GND로 전류 루프 완성 |
| M64/M63 | M64만 diode, M63은 gate=Vbias4 추정 | **M64/M63도 M58/M57과 같은 stacked-diode 패턴**(둘 다 게이트가 M63의 drain=Vbias3로 묶임), M60→M64→M63→gnd |
| M9a(Vom측)/M18a(Vop측) 게이트 | 대칭 가정으로 Vom1/Vop1(크로스커플링) 추정 | **M9a 게이트=M11b의 drain(=Vg15), M18a 게이트=M20b의 drain(=Vg25)** — 즉 자기 자신이 아니라 같은 diode 체인의 다른 다이오드 노드에 diode-connected |
| M13/M8/M22/M17의 역할 | M13/M17이 M8/M22와 병렬로 같은 노드를 공유한다는 paralleled-source 가정 | **확인됨** — 넷 다 게이트가 Vbias1에 병렬로 연결된 동일 구조 |

**교훈**: 저해상도 이미지에서 "vdd 라벨이 두 번 보인다"→"두 소자가 각자 독립적으로 소스 연결"이라고
해석한 게 틀렸다 — PMOS는 body/well을 항상 VDD(N-well 공정)에 묶어야 해서 그 태그가 소스 연결과
별개로 소자마다 반복해서 나타난다는 걸 놓쳤다. **두 소자의 id가 정확히 같다(-1.534µ)는 건 사실
직렬 스택이라는 강한 신호였는데**, 그 신호와 "독립 vdd 라벨"이라는(잘못된) 관찰이 충돌했을 때
후자를 더 믿었던 게 오독의 원인이었다 — 수치적 신호(동일 전류)가 시각적 라벨 해석보다 신뢰도가
높을 수 있다는 걸 유념할 것.

**참고(reference)**: 이 표 전체의 실측 근거는 `library/current_reuse_telescopic_ota.topology.json`의
`_correction_log`/`_correction_log_2`/`_confidence_note` 필드에도 요약돼 있다 — JSON을 다시 열 때는
그쪽을, 회로적 맥락과 근거를 다시 확인할 때는 이 §13을 참고할 것. `docs/03-analysis/
analog-topology-json-library.gap-findings.md` §4(compensation 판단)도 이번에 "Fig.3는 오탈자, 실제
참고 다이어그램은 Fig.4"라는 재해석으로 갱신 필요(아직 미반영 — 배치 7 이후 세션에서 확인).
