# gm/ID Lookup Table 생성 체크리스트 (공정별)

> 방법론 배경은 `gm-id-methodology.md` §3을 먼저 참조. 이 문서는 **실제로 스윕을 돌리기 위한**
> 체크리스트·스크립트 골격만 다룬다 — 재서술 없이 실행 관점만 추가.

---

## 1. 사전 결정 사항 (스윕 전에 고정)

| 항목 | 결정 | 비고 |
|---|---|---|
| 단위 소자 폭 W* | 예: 10µm 또는 W=L(unary) | gm/ID는 W 무관(border effect 무시 가능한 크기라면) — 하나의 W*로 전 sizing 커버 |
| Gate length 격자 | 공정이 지원하는 대표 L 몇 개(예: min, 2×min, 4×min, ... , max) | 원문 예시: 9개 L (0.10~4.00µm) |
| VGS 스윕 범위/스텝 | 0 ~ VDD, 0.025V 스텝 권장 | 스텝이 너무 크면 수치미분(gm/ID) 노이즈 발생 |
| VDS 스윕 범위/스텝 | 0 ~ VDD, 0.025V 스텝 권장 | saturation 판별에 필요 |
| VS(back-bias) 격자 | 0 ~ (허용 body bias), 0.1V 스텝 | body effect 무시 가능하면 1점만(VS=0)으로 축소 가능 — YAGNI |
| N/P 각각 별도 | 필수 | NMOS/PMOS 별도 테이블 |

## 2. SPICE/Spectre 스윕 스크립트 골격

```spice
* gm/ID sweep — unit device DC characterization
* 파라미터: L, VDS, VS 를 outer loop로, VGS를 inner sweep으로

.param L=0.5u VDS=0.6 VS=0

Xdut  d g s b  nmos_unit  W=10u L={L}
Vgs   g  0  DC 0
Vds   d  0  DC {VDS}
Vsb   b  0  DC {VS}
Vs    s  0  DC 0

.dc Vgs 0 {VDD} 0.025
* 각 (L, VDS, VS) 조합마다 반복 — outer sweep은 Spectre의 `sweep param` 또는
* 외부 스크립트(Python/MATLAB)로 다중 .dc 결과 파일을 생성 후 병합

.probe ID(Xdut) GM(Xdut) GDS(Xdut) CGG(Xdut) CGS(Xdut) CGD(Xdut) CGB(Xdut)
```

> Spectre 문법/연동은 `chip-verification` skill의 `references/spectre-integration.md` 참조
> (AMS 검증환경에 이 unit device 특성화 결과를 배치할 때).

## 3. 후처리 — gm/ID, gd/ID 수치 미분

시뮬레이터가 gm(`GM`)·gds(`GDS`)를 직접 주지 않으면(예: 순수 `.op` ID만 있는 경우) 반로그 기울기로
직접 계산한다:

```python
import numpy as np

def gm_over_id(vgs, id_):
    """gm/ID = d(log ID)/dVGS — 반로그 ID(VGS) 곡선의 기울기."""
    log_id = np.log(np.clip(id_, 1e-15, None))
    return np.gradient(log_id, vgs)

def gd_over_id(vds, id_at_fixed_vgs):
    """gd/ID = d(log ID)/dVDS — VDS 스윕 방향의 반로그 기울기 (Early 전압 역수)."""
    log_id = np.log(np.clip(id_at_fixed_vgs, 1e-15, None))
    return np.gradient(log_id, vds)
```

⚠️ VGS/VDS 스텝이 너무 크면 `np.gradient` 결과가 노이즈에 민감해진다 — 0.025V보다 크게 벌리지 않는다
(원문 §3.1 격자 참조).

## 4. 테이블 저장 형식 (4D 구조 권장)

```
IDn[L][VGS][VDS][VS], GMn[L][VGS][VDS][VS], GDSn[L][VGS][VDS][VS], CGGn[L][VGS][VDS][VS]
IDp[...], GMp[...], GDSp[...], CGGp[...]   # PMOS 동일 구조
```

주소 ↔ 전압 변환 규칙은 스윕 스텝에 맞춰 정의(예: 원문처럼 `vgs_idx = round(VGS/step + 1)`).
`.mat`/`.npz`/`.parquet` 등 재사용 가능한 배열 포맷으로 저장 — 이후 sizing 시 **cubic interpolation**으로
소비한다(스텝 사이 값은 보간, 재시뮬레이션 아님).

## 5. 검증 체크리스트 (LUT 자체의 건전성)

- [ ] gm/ID의 weak inversion 점근값이 `1/(n·UT)`(상온 n≈1.2~1.5, UT≈26mV → 약 25~32 V⁻¹) 근처인가?
- [ ] gm/ID vs VGS 곡선이 단조 감소(monotonic decreasing)인가? (노이즈로 인한 비단조 구간은 스텝을
      줄이거나 스무딩)
- [ ] ID/W vs gm/ID(전류밀도) 곡선이 strong inversion에서 `∝ (gm/ID)²`(제곱법칙과 정합)로 근사되는가?
- [ ] gm/gds(intrinsic gain) vs gm/ID 곡선이 예상 범위인가(공정별로 다르나, 최신 나노공정일수록 최대
      이득이 낮아짐 — §2.5 참조)?
- [ ] N/P 두 테이블 모두 동일 격자·동일 후처리 절차로 생성됐는가?

## 6. Model-driven 경로(E.K.V. 파라미터 추출)를 쓸 경우

전체 4D LUT 대신 E.K.V. 파라미터(n, VTo, ISuo, 이동도열화 다항식)만 추출해도 moderate inversion
설계는 충분하다(`gm-id-methodology.md` §3.4/§6 참조). 파라미터 추출은 공통게이트 구성에서 VS를
스윕하며 pinch-off 전압이 일정하게 유지되는 지점을 찾는 절차 — 전체 4D 스윕보다 데이터량이 훨씬
작다. 신규 공정에서 **처음엔 이 경로로 빠르게 시작**하고, 정밀도가 더 필요해지면 semi-empirical
전체 LUT로 확장하는 것을 권장(YAGNI — 처음부터 4D 전체를 만들 필요는 없다).

## 7. 실전 보간 알고리즘 (LUT를 만든 뒤 실제로 어떻게 조회하는가)

> 출처: Youssef/Murmann/Omran, "Precomputed Lookup Tables — Challenges and Solutions", IEEE Access 2020.
> §1~§6은 LUT를 **만드는** 절차였다 — 이 절은 만든 LUT를 **정확하고 빠르게 조회하는** 절차다.
> `assets/sizing_recipe.py`의 `SemiEmpiricalGmIdLUT`가 이 절의 구현 예시.

### 7.1 핵심 원리 — 수치미분 대신 저장된 도함수를 재사용한다

LUT는 ID와 함께 gm(=∂ID/∂VGS), gds(=∂ID/∂VDS), gmb(=∂ID/∂VSB)를 **이미 저장**하고 있다. 이 값들은
근사가 아니라 SPICE가 계산한 정확한 도함수다. 그러므로 VGS 축 보간을 "새로 미분"하지 않고, 이미
있는 gm을 **cubic-Hermite 보간의 기울기 입력**으로 그대로 재사용한다:

```
두 격자점 VGS_k, VGS_{k+1} 사이를 보간할 때
  P(x) = 2-knot cubic Hermite(y_k, y_{k+1}, slope_k=gm_k, slope_{k+1}=gm_{k+1})
```
이렇게 하면 **50mV처럼 성긴 VGS 격자에서도 오차 <0.01%** — 격자를 무리하게 촘촘히 할 필요가 없다.

### 7.2 축별 보간 방법 요약

| 축 | 방법 | 이유 |
|---|---|---|
| VGS | cubic-Hermite (저장된 gm을 기울기로 사용) | 유일하게 도함수가 LUT에 있는 축 |
| VDS, VS | 선형(`scipy.interpolate.RegularGridInterpolator`) | 도함수(gds/gmb)는 gm만큼 정확도 이득이 크지 않고 구현 단순 |
| L | 선형, **불균등 격자 그대로** | L은 도함수 개념이 없음. `RegularGridInterpolator`는 불균등 monotonic 격자를 그대로 지원 |
| ID(전류) | **ln(ID) 축에서 보간** | weak inversion에서 ID가 지수함수라 선형 보간 시 오차 3~4자릿수 발생 — 반드시 로그 공간에서 보간 |

**gm/ID 역조회**(목표 gm/ID로부터 VGS를 찾는 것): 매 조회마다 축 뒤집기+재보간하지 말고, LUT 생성
직후 **`VGS vs ln(gm/ID)` 역LUT를 한 번만 오프라인으로 만들어 캐싱**한다 — 논문 측정상 조회 시점에
축을 뒤집는 방식은 4자릿수 이상 느리다.

### 7.3 흔한 함정 (체크리스트)

- [ ] **일반 cubic spline(non-Hermite)을 쓰지 않았는가?** — shape-preserving이 아니라 단조 증가
      데이터에서도 비단조 출력이 나올 수 있다(gm/ID 역조회에서 특히 위험). Hermite/pchip 계열만 사용.
- [ ] **gm/gds를 `diff()` 수치미분으로 뽑지 않았는가?** — DC sweep 스텝이 조금만 성겨도 노이즈가
      끼고, 그 노이즈가 Hermite 기울기로 그대로 전파된다. 가능하면 **AC/Y-parameter 시뮬레이션**에서
      `gm=Re(Y21−Y12)`, `gds=Re(Y22+Y12)`로 직접 뽑아 미분 자체를 생략한다.
- [ ] **격자 경계(끝점)에서 한쪽 도함수만 쓰고 있지 않은가?** — 실제 관심 구간보다 여유를 두고
      스윕 범위를 넓혀서, 조회 지점이 항상 격자 "내부"에 오도록 한다.
- [ ] **gm/ID·IC 축이 균등 간격인가?** — 4자릿수 넘게 걸치는 축이므로 균등 간격은 낭비/저해상도를
      동시에 유발한다. 원 논문 IC 격자 예: 0.01~0.1(step 0.01), 0.2~1.0(step 0.1), 2~9(step 1),
      10~100(step 5) — 구간별 스텝을 다르게.
- [ ] **VDS 같은 "고정해둔" 차원이 실제 회로의 동작 범위를 커버하는가?** — 특성화 때 VDS=VDD/2로
      고정해두고 실제 회로가 다른 VDS로 동작하면 gds 오차가 그대로 이득 오차(예: 15%)로 전이된다.
- [ ] **기준 소자 W/L이 충분히 큰가?** — W/L이 너무 작으면(예 1) narrow-width 효과로 Vth가 밀려
      보인다. 기준 소자는 W/L ≥ 20(권장 100)로 스윕한다.

**실전 추가 함정** (`sky130-worked-example.md`에서 실제로 겪은 것 — 오픈소스 PDK 최초 적용 시 흔함):
- [ ] **L/W에 단위 접미사(`u` 등)를 붙였는가?** — `l=0.5`는 0.5"미터"로 해석돼 모든 bin 범위를
      벗어나 "could not find a valid modelname" 에러가 난다(단위 실수인지 바로 안 보임).
- [ ] **모델 파일이 참조하는 부속 파라미터 파일을 다 include했는가?** — BSIM 모델카드 하나(예
      `__tt.pm3.spice`)가 다른 파일(예 `__mismatch.corner.spice`, 공정에 따라
      `models/parameters/*.spice`)에 정의된 `.param`을 참조하는 경우가 흔하다. 한 소자 타입(예
      NMOS)에서 통과했다고 다른 타입(PMOS)도 같은 include 세트로 충분하다고 가정하지 말 것 — 공정
      효과(WPE/LOD 등)가 소자 타입별로 다른 부속 파일을 요구할 수 있다.
- [ ] **PMOS를 NMOS와 같은 부호로 스윕하고 있지 않은가?** — 소스 접지 기준 PMOS는 VGS·VDS가
      음수여야 도통한다. LUT에는 크기(절대값)로 저장해 NMOS와 같은 조회 인터페이스를 유지한다.
- [ ] **"이상치"를 보면 바로 격자를 촘촘히 하기 전에, 그 지점을 SPICE로 직접 재확인했는가?** —
      보간 오차가 아니라 정확한 값인데 gm/ID 선택이 나빴을 뿐인 경우가 있다(sky130 PMOS
      gm/ID=20 사례 — 격자를 아무리 세분화해도 결과는 안 바뀐다). 격자 밀도를 올리기 전에 원인부터
      가른다.
- [ ] **Cgd/Cdd를 SPICE 시뮬레이터의 op-info(예: `@device[cgd]`/`@device[cdd]` 계열 출력)로
      뽑지 않았는가?** — §7.1의
      "gm/gds를 diff()로 뽑지 말라"는 경고가 Cgd/Cdd에는 **더 심각하게** 적용된다: sky130 실측
      결과 op-info Cgd는 AC(Y-parameter)로 뽑은 값 대비 **36배**, Cdd는 부호까지 틀리고
      **~300배** 차이가 났다(Cgg는 27% 차이로 상대적으로 양호). Cgd/Cdd는 반드시 Y12/Y22(게이트
      또는 드레인을 AC 여기, 반대쪽을 AC 접지)로 뽑는다 — 실제 재현 사례는
      `sky130-worked-example.md` §7.

### 7.4 Foundry 특성화 절차 (신규 공정에 처음 적용할 때)

1. 기준소자 I0 결정: unity W/L, 큰 L(≥2µm), 포화 VDS(>0.5V)에서 VGS 미세 스윕 → weak inversion
   점근선(수평, gm/ID 최대)과 strong inversion 점근선(기울기 −1/2)의 교차점에서 I0 추출.
2. I0가 VDS(>~0.5V)·L(≥2µm)에 대해 평형(flat)인지 확인 — 코너별로 하나의 I0 확정.
3. (더 빠른 대안) AC/S-parameter 시뮬레이션으로 gm/gds/ID를 한 번에 추출 — 수동 미분 생략.
4. 최소 유효 W/L 결정: W/L 스윕하며 Vth 안정 구간(narrow-width 효과 없는 구간) 확인.
5. 코너×소자타입별 전체 스윕: L(공정별 대표값)×VDS(triode 경계~VDD−헤드룸)×VGS(IC 목표범위 커버)
   — 기준 W/L에서 ID/gm/gds 기록.
6. 후처리: IC = ID/(I0·W/L), gm/ID, gds/ID vs IC로 정리.
7. 시뮬레이션된 촘촘한 곡선을 설계자용 비균등 IC 벡터로 다운샘플·보간해 캐싱(§7.3 격자 권장 참조).
8. 코너 반복 — 단, gm/ID vs IC의 **형태 자체는 코너 불변**이므로(코너별 I0만 적용), 예산이 빠듯하면
   nominal I0 하나로 전 코너를 근사(오차 ~1-2%)하는 것도 실용적 선택.

### 7.5 LUT 조회 도구 아키텍처 참고 (대규모로 갈 때)

공정별 설정(공정 상수·유도량 수식)과 실측 데이터(원시 스윕 배열)를 **분리된 두 계층**으로 관리하면
확장이 쉽다: 트랜지스터 파라미터 조회(LUT 엔진)와 회로별 FOM 수식(설계자가 직접 채워 넣는 텍스트,
gain/GBW/SR 등)을 분리해두면 새 토폴로지를 추가해도 LUT 엔진은 안 건드려도 된다. Aging처럼 새로운
축(시간)을 추가해야 할 때도 같은 4D+α 구조를 그대로 확장할 수 있다 — 처음부터 이 정도 아키텍처가
필요하진 않지만(YAGNI), 여러 회로/토폴로지를 같은 LUT로 재사용할 계획이라면 이 분리를 염두에 둔다.

### 7.6 실전 사례 — sky130 + SPICE 시뮬레이터로 실제로 끝까지 해본 결과

이 §7 전체를 오픈소스 PDK(SkyWater sky130)와 SPICE 시뮬레이터로 실제 실행해본 기록·재현 스크립트·검증
결과는 `sky130-worked-example.md` + `assets/sky130_lut_sweep.py` +
`assets/sky130_nfet_pfet_lut_sample.npz` 참조 — toy 합성 데이터가 아닌 진짜 실리콘 4D LUT 사례.

## 8. 필수 필드 계약 (신규 공정 적용 전 완전성 체크, 2026-07-31)

> **이 절의 성격**: §1~§7은 "LUT를 어떻게 만드는가"(방법론)였다. 이 절은 다르다 —
> **이 skill이 실제로 요구하는 정보의 전체 목록(정본 스펙)**이다. 이 skill 개발이
> 끝난 뒤 어떤 신규 공정에 이 skill을 쓰려고 할 때, 그 공정용 LUT/PDK 참조가 이미
> 없다면 새로 만들어야 하는데, 그 결과물이 아래 항목을 **전부** 채워야 이 skill의
> 모든 기능(사이징뿐 아니라 노이즈/mismatch/CMRR·PSRR 추정까지)이 그 공정에서
> 동작한다. "이번에 만든 배치가 새로 요구하게 됐다"는 이력이 아니라, **skill이 실제로
> 필요로 하는 것의 현재 정본**이다 — skill 기능이 늘어 LUT나 PDK 참조에 대한 요구가
> 늘면 이 목록도 그만큼 갱신해 항상 "현재 skill을 다 쓰는 데 필요한 전체 목록"으로
> 유지한다(과거 어느 시점 스냅샷이 아님).
>
> **두 가지 서로 다른 출처를 구분한다** — 수집 방법이 완전히 다르기 때문에 하나로
> 뭉뚱그리면 안 된다:

### 8.1 스윕 LUT (직접 시뮬레이션으로 생성 — `sky130_lut_sweep.py`류 스크립트 필요)

| 필드 | 축/구조 | 어느 기능이 요구하는가 | 상태(sky130) |
|---|---|---|---|
| `L`/`VGS`/`VDS`/`VS` | 격자(축) | 전체 사이징 기반 | ✅ 있음 |
| `ID_n`/`GM_n`/`GDS_n`/`CGG_n` | [L][VGS][VDS][VS] | `size_transistor()`/`SemiEmpiricalGmIdLUT` 전체 | ✅ 있음 |
| `ID_p`/`GM_p`/`GDS_p`/`CGG_p` | 〃 (PMOS) | 〃 | ✅ 있음 |
| `SID_1F` (1/f 노이즈 밀도) | [L][VGS][VDS][VS], N/P 각각 | `noise_1f_density()`(배치 7-3g) | ⏳ 배치 7-3g 구현 대기 — 없으면 노이즈 추정 기능이 그 공정에서 동작 불가 |

### 8.2 PDK 참조 상수 (스윕이 아니라 그 공정의 model/mismatch 파일에서 **읽기만** 하면 됨)

| 필드 | 전형적 위치(sky130 기준 예시) | 어느 기능이 요구하는가 | 상태(sky130) |
|---|---|---|---|
| `vth0_slope`(+ 있으면 `vth0_slope1`/`voff_slope`/`toxe_slope` 등 추가항) | `*__mismatch.corner.spice`의 `.param` | `estimate_mismatch_sigma()`(배치 7-3h) | ✅ 있음(vth0_slope 확인, 추가항도 존재 — §7.9 질문 10(a) 참고) |
| `NOIA`/`EF`/`AF`(BSIM4 flicker noise 파라미터) | `*__tt.pm3.spice` 등 코너별 모델카드 | 위 §8.1의 `SID_1F` 스윕 자체가 이 파라미터에 의존(ngspice `.noise` 해석이 모델카드의 이 값을 사용) | ✅ 있음 |
| 디자인룰 최소폭(W_min)/최소길이(L_min) | 공식 design-rule 문서(DRC 매뉴얼) — **로컬 PDK spice 파일엔 없음이 확인됨**(BSIM 모델-빈 경계와 혼동 주의) | `search_gm_id_for_role()`의 `W_bounds` 하한(배치 7-3e) | ⚠️ **미확보** — sky130 자신도 아직 1차 출처로 확정 못함(§7.9 질문 7(a), do.md 참고). 공식 문서 확보가 필요한 항목의 실제 사례 |

### 8.3 신규 공정 적용 전 최종 게이트

새 공정에 이 skill을 적용하기 전, 위 8.1/8.2 표의 모든 행이 "있음"으로 확인돼야 한다.
하나라도 없으면 그 필드에 의존하는 기능만 국소적으로 비활성화(예: `SID_1F`가 없으면
노이즈 추정만 스킵하고 사이징/mismatch/CMRR·PSRR은 정상 동작)하거나, 먼저 그 필드를
확보(스윕 재실행 또는 PDK 문서 확보)한 뒤 진행한다 — 있는 걸로 억지로 대체하지 않는다
(§1.5).
