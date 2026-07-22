# gm/ID 설계 방법론 (gm/ID Methodology)

> 출처: Paul G.A. Jespers, *The gm/ID Methodology, A Sizing Tool for Low-voltage Analog CMOS Circuits — The Semi-empirical and Compact Model Approaches*, Springer (Analog Circuits and Signal Processing Series), 2010. (본문 8개 章 + Annex 4개, 약 180페이지)
>
> gm/ID 방법론의 원조 논문: Silveira, Flandre, Jespers, "A gm/ID based methodology for the design of CMOS analog circuits...", IEEE JSSC 31(9):1314–1319, 1996.
>
> §1~§8은 Jespers 책 전체 요약(원문 대조 완료). **§9~§12는 Jespers 책 이후/외부 문헌으로 보강한 확장**
> (deep-submicron 한계, 3-stage OTA, distortion, RF) — 출처는 §8.1 매핑표 참조.

이 문서는 저전압 아날로그 CMOS 회로에서 **트랜지스터 sizing(전류 ID와 게이트 폭 W 결정)** 을 위한 gm/ID 설계 방법론의 기술적 백본이다. 전통적 square-law(제곱법칙) 모델이 무너지는 moderate/weak inversion 영역과 short-channel 소자에서, 시뮬레이션·측정 기반 lookup table / chart로 전 inversion 영역을 연속적으로 다루는 것이 핵심이다.

---

## 1. 개요 — 왜 gm/ID 인가

### 1.1 해결하려는 문제

IC 설계자는 gain-bandwidth product, 최소 전력, 최소 면적, 저전압, dynamic range, 비선형 왜곡 등 **여러 목표를 동시에** 만족하는 트랜지스터 치수를 정해야 한다. 핵심 질문:

- Op-Amp의 전력을 최소화하면서 면적 페널티 없이 gain-bandwidth 스펙을 맞추려면?
- Moderate inversion을 strong inversion보다 선호해야 하는가?
- Sizing은 예술인가, 경험+반복 시뮬레이션인가, 아니면 제약 다변수 최적화 문제인가?

gm/ID는 이 문제를 **하나의 기술 attribute(gm/ID)** 로 매개변수화하여, small-signal 양(gm)과 large-signal 양(ID)을 잇는 다리로 삼는다.

### 1.2 Square-law가 무너지는 지점

전통적 강반전 제곱법칙 모델:

```
ID = (β/2n)·(VG − Vth)²,   β = μ·C'ox·(W/L)
gm = √(2β·ID/n)
```

이 모델은 다음에서 실패한다:

| 영역/조건 | Square-law의 문제 |
|-----------|------------------|
| Weak inversion (VGS < Vth) | 전류가 **지수함수**(diffusion 지배). 제곱법칙 완전 부적합 |
| Moderate inversion | 강/약반전 사이 전이 영역. 어떤 단순 해석식도 없음. **저전력 아날로그의 최적 절충 영역** |
| Short-channel / deep-submicron | 이동도 열화(mobility degradation), 속도포화, VT roll-off, DIBL, CLM 등으로 제곱법칙과 Early 전압 상수 가정이 깨짐 |

square-law에서 gain은 `ADC = gm/(ID/VA)`로 ID가 작아질수록 커지지만, ID→0에서 gain→∞라는 물리적으로 틀린 결과가 나온다. 실제로는 전류가 줄면 트랜지스터가 moderate→weak inversion으로 들어가 제곱법칙이 무너진다.

### 1.3 gm/ID의 전 inversion 영역 연속성

`gm/ID`는 게이트 전압 대비 log(ID)의 기울기로 정의된다:

```
gm/ID = (1/ID)·(dID/dVG) = d[log(ID)]/dVG          ... (반로그 축 ID(VGS) 곡선의 기울기)
```

이 값은 weak→moderate→strong inversion을 **하나의 연속 곡선**으로 이어준다:

| Inversion 영역 | gm/ID (1/V) 대략치 | 특징 |
|----------------|-------------------|------|
| Weak (약반전) | 최대, ≈ 1/(n·UT) ≈ 25~38 | 지수전류, 효율 최고, 속도 낮음, 큰 W 필요 |
| Moderate (중반전) | 중간 (roll-off 급격) | **전력·면적 최적 절충** |
| Strong (강반전) | 작음, ID⁻⁰·⁵ 로 감소 | 제곱전류, 속도 최고, 효율 낮음 |

- 상온 UT = kT/q ≈ 26 mV, slope factor n ≈ 1.2~1.5.
- Weak inversion 최대값 이론치 = 1/(n·UT). n=1.2, UT=26mV → ≈ 32 V⁻¹. (공통게이트/bipolar 극한은 1/UT ≈ 38 V⁻¹)

### 1.4 두 가지 접근

| 접근 | 데이터 원천 | 장점 | 단점 |
|------|-------------|------|------|
| **Semi-empirical (반경험적)** | 실측 또는 BSIM/PSP 고급모델로 재구성한 대형 look-up table (ID, gm, gds, C 등) | 2차 효과 자동 포함, 모델 무관 | "맹목적(blindly)" 스윕 — 동작영역 직접 제어 어려움 |
| **Model-driven (모델기반)** | 파라미터 가변 E.K.V. compact model (n, VTo, ISuo, θ 다항식) | 해석식 → 동작영역(qF, gm/ID) 직접 지정 가능, 2차 효과 기여도 분리 | 파라미터 look-up table 필요 |

두 방법은 실질적으로 **동일한 결과**를 준다(moderate inversion에서 거의 일치). 방법론의 핵심은 아래 sizing 방정식의 **분모** — 임의의 기준 트랜지스터에서 얻은 gm/ID 비 — 이다.

---

## 2. 핵심 설계 변수와 관계식

### 2.1 Intrinsic Gain Stage (I.G.S.) — 기준 회로

책 전체의 기본 단위 회로. 포화된 common-source 트랜지스터 + 드레인의 정전류원 + 부하 커패시터 C.

Small-signal: 입력 개방, 출력 = `gm·vin` 전류원 ∥ 출력 컨덕턴스 gd ∥ C.

주파수 응답 (1차 시스템):

```
AAC(고주파) = −gm/(jωC)
ADC(저주파) = gm/gd = gm/(ID/VA)          (VA = Early 전압)
ωc = gd/C  (cutoff)
ωT = gm/C  (transition = gain-bandwidth product)   ... (핵심)
```

따라서 목표 fT가 주어지면 **gm은 자동 결정**:

```
gm = ωT·C = 2π·fT·C
```

남은 문제는 gm ↔ (ID, W/L) 연결 = large-signal 모델이 필요 → 여기서 gm/ID 등장.

### 2.2 핵심 sizing 방정식 (방법론의 심장)

기준 소자(폭 W*, 길이 L, 동일 VDS/VS)의 gm/ID 비를 알면:

```
ID = gm / (gm/ID)                         ... (1.17) 전류 결정
W  = W* · ID / ID*                        ... (1.18) 폭 결정 (전류-폭 비례)
```

- gm/ID는 **W에 무관**(폭이 border effect 무시할 만큼 크면). 그래서 단위 기준 소자의 gm/ID 곡선 하나로 모든 W를 sizing할 수 있다.
- ID와 gm을 **교환**하면 gain-bandwidth 대신 **slew-rate** 기준 sizing이 된다.
- gm→gd, gm/ID→gd/ID로 치환하면 출력 컨덕턴스 기준 sizing.

### 2.3 정규화 전류(inversion index)와 특성전류

E.K.V. 모델의 정규화 변수(전 영역 연속):

```
i  = ID / IS          (normalized drain current = inversion index)
IS = 2·n·UT²·C'ox·(W/L) = 2·n·UT²·β        (specific current, 특성전류)
q  = −Q'i/(2·n·UT·C'ox)  (정규화 이동전하밀도),   i = q² + q
q  = 0.5·(√(1+4i) − 1)
```

동작영역 판별 지표:

| 지표 | Weak | Moderate | Strong |
|------|------|----------|--------|
| i (inversion index) | ≪ 1 | ≈ 1 | ≫ 1 |
| qF (forward 정규화 전하) | < 0.1 | ≈ 1 (중앙) | > 10 |

- i=1 (q=1) → pinch-off 전압점. 이때 ID = 2·IS. Weak/strong 점근선이 log-log에서 i=1에서 교차.
- qF는 전압/전류가 아니지만 sizing 완료 후 사라지는 **동작영역 제어 파라미터**로 매우 유용(특히 moderate inversion 국한에 편리).

### 2.4 gm/ID 해석식 (E.K.V.)

```
gm/ID = 1/(n·UT) · 1/(1+q) = 1/(n·UT) · 2/(√(1+4i)+1)
```

- Weak (i,q≪1): gm/ID → 1/(n·UT) = 최대, 거의 일정.
- Strong (i≫1): gm/ID ∝ 1/√i (√ID의 역수로 감소).

공통게이트(common-gate) gms/ID (부호 반대, n 소거):

```
gms/ID = 1/UT · 2/(√(1+4i)+1)      (weak 극한 → 1/UT ≈ 38 V⁻¹, bipolar와 동일)
```

### 2.5 Intrinsic gain(고유이득)과 gd/ID

```
|A| = gm/gd = (gm/ID)·(ID/gd) = (gm/ID)·VA
```

- Intrinsic gain = gm/ID 곡선 × Early 전압 VA 곡선의 곱.
- 큰 gm/ID(weak/moderate) + 큰 VA(strong+큰 VDS) 는 상충. 실측상 **moderate/weak inversion에서 최적** (gm/ID가 나쁜 Early 전압을 상쇄, gain 최대 ≈ 200 for 0.5µm; 100nm→15, 4µm→1000+).
- gd/ID(Early 전압의 역수)는 DIBL, de-saturation, CLM 기여로 분해된다(§5.6). **Early 전압이 모든 VGS에서 한 점으로 수렴한다는 통념은 실측상 거짓** — 오직 weak inversion에서만 VA가 게이트 전압에 무관.

### 2.6 fT 와 준정적(quasi-stationary) 한계

- ωT = gm/C 는 전체 부하 기준. 트랜지스터 자체 속도 한계는 `2π·f_nqs = gm/Cgg`(입력 커패시턴스 기준). 통상 **fT ≤ 0.1·f_nqs** 이어야 준정적 가정 성립(Tsividis).
- 고주파(예: 1 GHz) 설계에서는 이 한계 때문에 게이트 길이를 줄여야 하며, gain(나쁜 VA)과 절충해야 한다. → 예제상 160nm가 100nm(이득손실)와 500nm(f_nqs 부족) 사이 좋은 절충.

### 2.7 VDsat 근사식 (빠른 견적용)

```
VDsat ≈ 2/(gm/ID)
```
BSIM SPICE 데이터로 검증된 1차 견적 공식(Walker/Murmann 계열 강의자료). gm/ID를 이미 정했다면 VGS−Vth 여유(오버드라이브)를 룩업 없이 즉시 추정할 수 있어 **VDS 헤드룸 확인**(특히 cascode/저전압 설계에서 스택 가능 여부 빠른 판단)에 유용하다.

⚠️ **short-channel(L이 매우 작을 때)에서는 이 식이 VDsat을 과대추정**한다 — §9.3 참조. 100nm 이하에서는 참고용으로만 쓰고 최종은 반드시 LUT/시뮬레이션으로 확인한다.

---

## 3. Lookup Table / 설계 차트 생성 방법

### 3.1 시뮬레이션 스윕 방법론

Semi-empirical 데이터는 **단위 기준 소자(예: W=10µm 또는 W=L)** 에 대해 4차원 스윕으로 생성한다. 책의 데이터(IMEC 90nm/100nm 계열)는 다음 4D array 구조:

```
IDRAINn/p, GMn/p, GDSn/p, CGGn/p, ...  →  [ L , VGS , VDS , VS ] 4D array
```

책의 실제 격자(예시 규격):

| 축 | 범위 | 스텝 | 포인트 |
|----|------|------|--------|
| VGS (gate-to-source) | 0 ~ 1.2 V | 0.025 V | 49 |
| VDS (drain-to-source) | 0 ~ 1.2 V | 0.025 V | 49 |
| VS (source-to-substrate, back-bias) | 0 ~ 0.8 V | 0.1 V | 9 |
| L (gate length) | 0.10, 0.11, 0.12, 0.13, 0.14, 0.16, 0.50, 1.00, 4.00 µm | 불균등 | 9 |

→ array 크기 `[9 × 49 × 49 × 9]`. 각 소자 타입(N/P)별로 ID, gm, gmb, gds, Cgg, Cgs, Cgd, Cgb, Css를 저장.

주소 ↔ 전압 변환:
```
vgs = round(40·VGS + 1),   vds = round(40·VDS + 1),   vs = round(10·VS + 1)
```

### 3.2 SPICE 스윕 요약 (재현 레시피)

한 기술을 위한 gm/ID 차트를 만들려면:

1. 단위 소자(고정 W, 예 10µm; 또는 W=L "unary")를 DC 시뮬레이션.
2. **VGS를 전 영역(0~VDD) 스윕**, VDS·VS·L을 파라미터로 고정/스텝.
3. `.op` 출력에서 ID, gm(=∂ID/∂VGS), gds(=∂ID/∂VDS), gmb, 소신호 커패시턴스(Cgg 등)를 각 바이어스점에서 추출.
4. gm/ID는 `diff(log(ID))/diff(VGS)` (반로그 기울기)로 수치미분. (전치하면 gd/ID = `diff(log(ID))/diff(VDS)`.)
5. 결과를 (L, VGS, VDS, VS) 테이블로 저장 → 이후 sizing에서 interpolation(cubic)으로 소비.

### 3.3 도출되는 4대 설계 곡선 (gm/ID = 만능 x-축)

전통적 방법이 Vov(=VGS−Vth)를 x-축으로 쓰는 대신, **gm/ID를 만능 x-축**으로 사용하면 다음이 하나의 곡선족으로 정리된다:

| 곡선 | 의미 | 활용 |
|------|------|------|
| **gm/ID vs VGS** | 반로그 ID(VGS) 기울기 | 동작영역 위치 파악 |
| **ID/W (또는 IDu, i) vs gm/ID** | 전류밀도. i = ID/IS | gm/ID 선택 → W/L 결정 |
| **gm/gds (=gm/ID·VA) vs gm/ID** | intrinsic gain | 이득 확보 절충 |
| **fT (gm/Cgg) vs gm/ID** | 속도 | 대역폭 절충 |

이 4개가 gm/ID 방법론의 표준 "chart set"이다. 전류밀도(ID/W)와 gm/ID, fto, gain을 gm/ID 축 위에서 동시에 읽어 절충점을 고른다.

### 3.4 Compact model 파라미터 테이블 (model-driven용)

E.K.V. 파라미터는 3D/4D array (VGS 축 제거, 모델이 VGS를 내부 계산):

```
nN/P, VToN/P, ISuoN/P  →  [ VDS , VS , L ]  (49×9×9)
PolyN/P (θ 이동도열화 4차 다항식, 계수5), ThN/P  →  [ VDS , VS , L , (vgs/coef) ]
```

파라미터 추출 알고리즘(§4.5, §5.2, `IdentifN/P.m`): common-gate 구성에서 VS를 스윕하며 pinch-off 전압 VP가 일정하게 유지되는 ISu를 interpolation으로 탐색 → 여러 VG에서 반복 → VP vs VG 직선회귀로 `n`(기울기), `VTo`(절편) 획득. Short-channel에서도 **VS·VD 고정 시** 1% 이내로 실전류를 재현.

### 3.5 실전 LUT 조회 도구 — `lookup()` 3-모드 (Walker/Murmann 계열)

4D array를 직접 인덱싱하는 대신, 실무에서는 아래 3가지 모드를 지원하는 단일 `lookup(data, xVar, xVal, ...)` 스타일 함수 하나로 모든 조회를 처리한다:

1. **단순 조회**: 예) `lookup(GM, 'GM', 'VGS', 0.5, 'L', 0.5, 'VDS', 0.6)` — 격자점 보간으로 gm 하나를 반환.
2. **임의 비율 조회**: 두 배열을 나눈 비율을 그 자리에서 계산 — 예) `GM_ID = lookup(GM,...)/lookup(ID,...)` 대신 `lookup(GM_ID, 'GM_ID', ...)`처럼 비율 자체를 1급 조회 대상으로 취급.
3. **교차 조회(cross-lookup)**: 한 비율을 다른 비율에 대해 조회 — 예) "gm/ID=15일 때 fT는?" → `lookup(FT, 'GM_ID', 15, ...)`. Sizing에서 gm/ID를 축으로 놓고 fT·gain·ID/W를 동시에 읽는 것이 바로 이 모드.

실제 4D 보간 알고리즘(선형 vs cubic, weak inversion 지수구간 처리, monotonic 축 요구사항 등)은 재서술하지 않는다 — `lut-generation-checklist.md` §7을 그대로 따른다. `assets/sizing_recipe.py`의 `SemiEmpiricalGmIdLUT`가 이 3-모드 조회 중 (1)(3)에 해당하는 구현 예시다.

---

## 4. 설계 절차 (Sizing Procedure)

### 4.1 Semi-empirical sizing 흐름 (I.G.S., 정전류 부하)

목표: 부하 C, 목표 fT를 만족하는 (ID, W). 전략 (Fig. 6.4):

```
[스펙] fT, C, L, VDS, VS 지정
   │
   ▼
1) 기준 gm/ID 행렬 생성:  gmID = d/dVGS[ log(IDu) ]   (테이블에서 수치미분)
2) 필요 gm 계산:          gm   = 2π·fT·C
3) 전류 스윕:             ID   = gm ./ gmID           (gm/ID 벡터로 나눔)
4) 폭 계산:               W    = L · ID ./ IDu         (전류-폭 비례)
5) 이득:                  A    = GM ./ GDS  (테이블에서 직접)
```

MATLAB 핵심(fig065.m 발췌, 일반화):
```matlab
gm   = 2*pi*fT*C;
ID   = gm ./ gmID;          % 각 gm/ID 후보에 대한 필요 전류
W    = L * ID ./ IDu;       % 대응 폭
```
결과: gm/ID(또는 ID) 축을 따라 (W, VGS, A)가 곡선으로 나온다. 저전류(weak) 쪽에서 W 급증 → **최소 구현 전류** 존재. Strong 쪽에서 VGS>0.5V면 이동도 열화로 예상보다 큰 W 필요.

### 4.2 기생 커패시턴스 반영 (일정 외부부하 sizing) — 반복 루프

폭 W가 커지면 드레인 접합 커패시턴스 CJD가 출력부하에 병렬로 더해진다. 외부부하를 일정하게 유지하려면 반복:

```
C = Co
repeat (수 회 수렴):
    gm = 2π·fT·C
    ID = gm/(gm/ID);  W = L·ID/IDu
    CJD = jctCap(L, W, ...)        # 폭으로부터 접합 커패시턴스
    C = Co + CJD
```
Weak inversion 깊숙이 가면 W가 너무 커져 CJD가 Co를 압도 → ID가 다시 **증가**로 반전. 최적점은 **moderate inversion 중앙**. (예제상 400µA, gain≈40, f_nqs > 10·fT 만족.)

**Transistor partitioning(다중 게이트 분할)**: 큰 W를 병렬 sub-소자로 나눠 공통 드레인 접합 공유 → 드레인 접합 커패시턴스 ~30% 감소(2분할 시), 게이트 직렬저항 감소(고주파 유리). 접합 커패시턴스는 면적/side-wall/gate-side 성분 합으로 계산.

### 4.3 Model-driven sizing 흐름 (동작영역 직접 지정)

Semi-empirical과 **동일 방정식**, 단 gm/ID를 n, VTo, ISuo, θ에서 해석적으로 계산. 최대 장점: **qF 벡터로 동작영역(moderate inversion)에 국한**하여 낭비 없이 sizing.

```matlab
qF  = logspace(-1.8, 0.8, 30);        % moderate inversion 포함 범위 지정
VP  = UT*(2*(qF-1) + log(qF));        % pinch-off (VS=0)
VGS = n*VP + VTo;
qR  = invq((VP-VDS)/UT);              % de-saturation 반영
i   = qF.^2 + qF - qR.^2 - qR;        % 정규화 전류
IDu = ISuo .* i;                      % 단위 전류
gmID1 = 1./(n*UT*(1+qF+qR));          % 이동도열화 무시 1차
% (2단계) 이동도 열화: ISu = ISuo·polyval(P,i);  gmIDD = gmID1·Z
% (3단계) 접합 커패시턴스: 반복 루프로 C 갱신
```
결과(Fig. 6.12): weak/strong 점근선을 잇는 곡선. Moderate inversion에서는 이동도 열화·기생 커패시턴스 영향이 작아 **n, VTo, ISuo 3개 파라미터만으로 sizing 충분**.

### 4.4 단순화 sizing 절차 (moderate inversion, Fig. 6.16)

포화·moderate inversion 가정 시 직결 계산:

```
1. qF 선택 (스칼라/벡터, moderate inversion)
2. gm/ID = 1/(n·UT·(1+qF))
3. ID = gm·(1/(gm/ID)) = gm·n·UT·(1+qF),  gm = 2π·fT·C
4. W  = ID / IDu,   IDu = ISuo·(qF²+qF)
5. (기생 CJD를 C에 더해 3~4 반복)
6. VGS = n·VP + VTo,  VP = UT·(2(qF−1)+log qF)
```

### 4.5 검증 단계

- **준정적 확인**: f_nqs = gm/(2π·Cgg) 계산, fT ≤ 0.1·f_nqs 인지.
- **이득 확인**: A = (gm/ID)·VA 또는 전달특성 기울기(§6.3.3, VDS 스윕하며 constant-ID 유지하는 VGS 추적 → 이득 = 전달곡선 기울기; noise 적고 왜곡 평가도 가능).
- **Slew-rate 확인**: slew-rate = ID/C = ωT/(gm/ID). 정현파 조건 `ω·V < ωT/(gm/ID)`. 큰 dynamic range 요구 시 fT를 상향해야 함.
- 최종은 **고급 시뮬레이터로 미세조정** — gm/ID는 최적 근방으로 안내하는 도구.

---

## 5. 핵심 트레이드오프 (효율 vs 속도 vs 이득)

### 5.1 트레이드오프 삼각형

gm/ID 방법론이 포착하는 중심 절충:

```
           효율 (Efficiency)
           gm/ID ↑, weak inversion
           작은 ID, 큰 W, 높은 gain
                  ▲
                 ╱ ╲
                ╱   ╲
     이득 ◄────╱─────╲────► 속도
   gm/gds       moderate    fT = gm/Cgg
   (intrinsic   inversion   strong inversion
    gain)       (최적절충)   gm/ID ↓, 작은 W
                            큰 ID, 낮은 gain
```

| 지표 | gm/ID 큰 쪽(weak) | gm/ID 작은 쪽(strong) |
|------|-------------------|----------------------|
| 전류 효율 (gm 대비 ID) | **높음** (전류 최소) | 낮음 (전류 큼) |
| 속도 fT = gm/Cgg | 낮음 (W 큼→Cgg 큼) | **높음** |
| Intrinsic gain gm/gds | 높음 (weak/moderate) | strong+큰VDS 필요, 실측상 낮음 |
| 게이트 폭 W | 매우 큼 (기생↑) | 작음 |
| 전력 | 최소 | 큼 |

### 5.2 왜 Moderate Inversion이 최적인가

- 전류: strong보다 작음 (전력↓).
- W/L: weak보다 작음 (기생 커패시턴스·면적 관리 가능).
- Gain: weak보다 약간만 낮음.
- 이동도 열화·기생 커패시턴스 영향이 작아 **파라미터 3개로 sizing 가능**.
- 과거에는 큰 W가 필요한 기생 문제로 회피되었으나, short-channel 소자 시대에 표준 선택이 됨.

경계: strong inversion은 gate voltage overdrive (VGS−Vth) > 0.2 V 부터(Laker). Weak inversion 시작은 ID가 IDmin 근처에서 W가 급증하는 지점.

### 5.3 Slew-rate 절충

```
slew-rate = ID/C = ωT/(gm/ID)
```
큰 gm/ID(효율)를 택하면 slew-rate가 낮아진다. Unity-gain 루프 등에서 dynamic range를 위해 fT를 큰 배수로 올려야 할 수 있음 — 효율과 속도의 또 다른 상충.

---

## 6. Worked Examples (일반화된 설계 레시피)

책의 예제를 **재현 가능한 레시피**로 일반화한다(구체 수치는 참고용).

### 6.1 Intrinsic Gain Stage (기본 1단)

**스펙 예**: C=1pF, fT=100MHz, L=0.5µm, VDS=0.25~1V, VS=0.
**레시피**: §4.1 그대로. gm=2π·fT·C=0.63mS. gm/ID 곡선 위에서 (W, VGS, A) 산출 → moderate inversion(gain≈40)에서 절충점 선택. 고주파(1GHz)면 L 단축(예 160nm)로 준정적 확보.

### 6.2 Cascode I.G.S. (공통게이트 + 공통소스)

**스펙 예**: C=1pF, fT=100MHz(또는 1GHz), 두 트랜지스터 Q1(공통소스)·Q2(공통게이트) 모두 moderate inversion.
**레시피** (§7.2.1, 5단계):
```
1. qF 범위 지정 (예 0.1~2, 전력·크기 절충)
2. 정규화 전류·gm/ID 평가 (이동도 열화 초기 무시)
3. gm/ID 방법론으로 ID, W1/L 산출 (gm1 = 2π·fT·C)
4. Q2 폭 = Q1 폭으로 두고, IDu2=IDu1/ISuo2 → qF2 → 두 트랜지스터 VGS·VG 계산
5. 파일 재실행: 출력 접합 커패시턴스 + 이동도 열화 반영 (반복)
```
- Q1이 gm(=전류) 설정, Q2가 출력 임피던스를 A2배 증폭 → 총 이득 = A1·A2 (예 100MHz/500nm: 81 dB).
- **두 번째 pole**: Q1-Q2 공통노드 기생(접합+Q2 intrinsic source 커패시턴스, **strong inversion 근사로** ≈½ 게이트 커패시턴스). 비지배 pole이 fT 너머여야 안정 → phase margin 확인.

### 6.3 Current Mirror (전류거울)

Miller Op-Amp 1단의 부하로 등장(§8.2.3). 거울은 pole-zero **doublet**을 도입: 다이오드 접속 Q3a의 gm3와 기생 게이트/접합 커패시턴스가 시정수 형성.
```
gm1 보정계수 = (gm3 + jω·C3/2)/(gm3 + jω·C3)   → pole·zero 한 octave 간격 doublet
```
- Doublet 주파수가 fT의 ~3배 이상이면 phase margin에 무해.
- **주의**: 1/f noise 저감 위해 Q3 게이트 면적(길이)을 키우면 C3 증가로 doublet이 fT 근처로 내려와 **ringing 유발**. Q3 길이는 과도 확대 금지.

### 6.4 Miller Op-Amp (2단 OTA) — 방법론의 정점

**구조**: P채널 차동쌍(1단, 1/f noise 유리) + N채널 공통소스(2단, 진짜 I.G.S.) + 전류거울 + Miller 보상 커패시터 Cm.

**Pole splitting (핵심 원리)**:
```
ωT   = gm1/Cm                              (전체 gain-bandwidth)
ω1   = gd1/(A2·Cm) = (gd1/Cm)·(gd2/gm2)    (지배 pole, 저주파로 밀림)
ω2   = gd2/(C2+Cm)                          (2단 cutoff)
ωNDP = (gm2/Cm)·Cm²/[Cm(C1+C2)+C1C2]       (비지배 pole)
ωZ   = gm2/Cm                              (RHP zero)
```
Cm이 노드1 pole을 저주파로, 노드2 pole을 fT 너머로 갈라 **1차 시스템(무조건 안정)** 화. RHP zero는 Cm이 Q2를 우회하며 발생 → phase margin 악화. 안정 조건: RHP zero·비지배 pole을 ωT 오른쪽에 둠 (2단 gain-bandwidth > ωT).

**Sizing — 2D sizing space (§8.3)**:

스펙(반드시 만족) vs attribute(최적화 대상) 이분법:
- **스펙**: gain-bandwidth(ωT), 안정성(phase margin).
- **Attribute**: 전력, 면적.
- **Sizing space**: 2축 = (qF1, qF2) 또는 (gm/ID1, gm/ID2), 각 단을 제어. 각 점이 **동일 스펙을 만족하는 서로 다른 Op-Amp**.

레시피:
```
1. Z = ωZ/ωT (통상 10), NDP = ωNDP/ωT (통상 4) 지정  → phase margin 60~70°
2. gm1 = ωT·Cm,   gm2 = Z·gm1
3. Cm 초기추정(예 0.5·C) → gm/ID로 각 트랜지스터 ID·W 산출
   → 기생 C1,C2 추정 → Cm 재계산(식 8.15, 아래) → 수렴까지 반복(수 회)
4. 2D 공간에서 등전력(타원)·등면적(쌍곡선)·등이득(점선) contour 겹쳐 절충점 선택
5. 부가 제약: VGS3b = VGS2 (offset 방지), W4 고정(면적 제어)
```
식 8.15 (Cm 재계산, C1·C2는 노드1/노드2 기생 커패시턴스):
```
Cm = (NDP/Z) · [ C1+C2 + sqrt((C1+C2)² + 4·C1·C2·Z/NDP) ]
```
- 등전류 contour ∩ 등면적 contour → 동일 전력·면적 두 구현. 면적 contour를 밀어 접점 → 주어진 전류의 최소 면적. 여러 전류 반복 → 전력-최소면적 관계.
- 예제 결과(20MHz/1.2V/3pF): gain 82dB, IDC≈105µA, 면적 200~250µm², Cm≈1.41pF, PM≈70°. 모든 핵심 트랜지스터 moderate inversion.
- **RHP zero 제거**: Cm에 직렬 저항 R=1/gm2 → zero를 무한대로. 더 큰 R은 zero를 LHP로(pole-zero 상쇄), gain-bandwidth ~2배 가능.
- **Slew-rate 기준 sizing**: slew-rate 지정 시 1단 전류가 부하·slew로 고정 → 나머지 동일 절차.

### 6.5 기초 예제 — CS 단/차동쌍 pole-zero sizing (Walker/Murmann 계열, SPICE 검증)

Jespers의 I.G.S./cascode 예제보다 더 기초적인, "gm/ID sizing → pole/zero 계산 → SPICE 대조"의 최소 골격:

**스펙**: gain=4, RL=1kΩ, CL=50fF, Rs=10kΩ, ITAIL=600µA (차동쌍, 180nm).
**절차** (원문 MATLAB 스크립트 그대로 — 여기서는 **ITAIL이 스펙으로 고정**되어 있어 gm/ID는
자유 선택이 아니라 gm과 ITAIL/2로부터 **역산**되는 값임에 주의, 다른 worked example(§6.1 등)의
"gm/ID를 먼저 선택"하는 순서와는 다르다):
```
1. gm = gain/RL = 4/1kΩ = 4mS                          (gain-RL 스펙에서 고정)
2. gm/ID = gm/(ITAIL/2)                                 (ITAIL 스펙에서 역산 — 선택 아님)
3. LUT 조회: GM_CGG(→fT), CGD_CGG, CDD_CGG (모두 gm/ID 축으로) → Cgg=gm/wT, Cgd, Cdd, Cgs 도출
4. 커플링된 2-pole (Miller 항 포함, RL·Rs 양쪽 노드 결합):
   b1 = Rs·[Cgs + Cgd·(1+gain)] + RL·(CL+Cgd)
   b2 = Rs·RL·(Cgs·CL + Cgs·Cgd + CL·Cgd)
   fp1 = 1/(2π·b1),   fp2 = (1/2π)·(b1/b2)
5. W = (ITAIL/2) / ID_W(gm/ID)                          (LUT의 ID/W 조회)
6. hand-calc vs Spectre 대조
```
**검증 결과**(원문 수치, 그대로 재현): gm 4mS(hand) vs 4.05mS(sim), Cgg 37.8fF vs 37.49fF, Cgd 9.0fF
vs 8.97fF, Cdd 22.6fF vs 24.63fF — 소자 파라미터는 대부분 <10% 오차. Pole은 **fp1=200MHz(hand)
vs 215MHz(sim, 오차 ~7%)**, **fp2=5.8GHz(hand) vs 4.8GHz(sim, 오차 ~20%)** — 저자 본인 결론:
"typical discrepancies are no more than 10-20%, due to VDS dependencies, finite output resistance
등" — **gm/ID 1차 계산은 10~20% 오차 범위**이며 이것이 "출발점이지 최종값이 아니다"(§4.5)라는
원칙의 정량적 근거.

### 6.6 역사적 검증 예제 — Silveira/Flandre/Jespers 1996 cascode SOI OTA

gm/ID 방법론의 **원조 논문**(1996) 자체의 worked example. 11개 트랜지스터 cascode SOI OTA, Itot=2mA, CL=10pF, VDD=3V — synthesis 결과를 HSPICE·실측과 대조.

**정량적 근거 — 왜 gm/ID가 strong/weak 단순 접근보다 나은가** (원 논문 Table III 계열 비교):

| Sizing 방법 | fT 오차 | Gain 오차 | 비고 |
|---|---|---|---|
| Strong inversion(제곱법칙)만 사용 | **+50%** 과대추정 | **+7dB** 과대추정 | square-law가 실제보다 낙관적 |
| Weak inversion(지수모델)만 사용 | **+15%** 과대추정 | — | 면적도 **+25%** 과대추정(불필요하게 큰 W) |
| **gm/ID(전 영역 연속)** | HSPICE·실측 대비 **<5%** | <5% | gain/fT/PM/slew-rate/swing 전부 |

- 전류거울 소자는 **의도적으로 strong inversion**에 배치(matching/noise), 이득 관련 소자는 weak/moderate — 한 OTA 안에서도 **소자별로 다른 동작점**을 쓰는 것이 정상.

### 6.7 Miller OTA sizing — 2-phase 알고리즘 (Cortes & Bampi, §6.4 심화)

§6.4의 2D sizing space(qF1,qF2) 절충을 **숫자 스펙에서 거꾸로 W/L을 뽑아내는 순서형 절차**로 구체화:

```
Phase 1 (W/L, 전류 배분):
  - 각 트랜지스터 역할별 gm/ID 선택: 전류거울=strong inversion(matching),
    차동쌍=GBW로 결정, 나머지=moderate inversion
  - gm/ID 곡선에서 ID/(W/L) 조회 → 전류 예산으로 W/L 산출

Phase 2 (L, 이득 역산):
  - 단별 이득 Av,i = (gm/ID)_i · (그 단의 두 Early전압 VA 병렬조합)
  - Av_total = Av1·Av2 (목표 스펙)
  - noise-critical 차동쌍의 L을 먼저 임의 지정 → 그 VA를 gm/ID vs VA 곡선에서 조회
  - Av_total 목표에서 **역으로 필요한 VA(따라서 필요한 L)를 나머지 트랜지스터에 대해 역산**
```
**수치 예**: VA3=10.2V가 필요하면 gm/ID vs VA 곡선에서 L3=0.6µm로 역산. 이 "이득식 → L 역산" 스텝이 §6.4의 2D contour 탐색을 대체하는 닫힌 형태(closed-form) 지름길이다.

---

## 7. Noise 및 Matching 고려사항

### 7.1 Matching / Mismatch

- **Weak inversion은 mismatch 민감도가 높다**(Fig. A3.4): 동일 VG에서 weak(VG=0.2V)일 때 drain current spread가 strong(VG=0.6V)보다 훨씬 큼. 도핑 N(σ=2%)·산화막 tox(σ=0.5%) mismatch 히스토그램에서 weak가 넓게 퍼짐.
- Mismatch를 **E.K.V. 파라미터(n, VTo, ISuo) 편차**로 환산 가능(§A3.5). 예(N σ=1%): 3σ(n)≈0.0018%, 3σ(VTo)≈5.6mV, 3σ(ISu)≈1.16nA. → VTo mismatch가 지배적.
- 실전 함의: 정전류원·전류거울·차동쌍은 mismatch 억제 위해 **moderate~strong inversion**(큰 qF)이 유리. 예제상 거울/전류원 Q4는 qF를 차동쌍 Q1보다 크게(민감도↓).

### 7.2 Noise

- **1/f noise**는 게이트 면적에 반비례 → 큰 W·L이 저감. Miller Op-Amp에서 입력단을 P채널로 택한 이유(P채널 1/f 특성 우수).
- 단, noise 저감 위한 면적 확대는 **기생 커패시턴스(doublet)** 와 상충(§6.3): Q3 길이 확대 → ringing. Noise-속도 절충.
- Thermal noise는 gm에 직접 연동 → 입력환산 noise ∝ 1/gm. gm이 fT로 고정되면 noise도 결정. (책은 1/f·mismatch 중심; thermal은 gm/ID→gm 연결로 간접 다룸.)
- Temperature: gm/ID 최대값은 온도에 강하게 의존 (weak inversion subthreshold slope 변화). 250K/300K/350K에서 max(gm/ID) ≈ 39.7 / 32.7 / 27.6 V⁻¹ (≈1/(n·UT)).

**Subthreshold(weak inversion) 소신호·noise 보충식** (Perrott, MIT 강의자료 계열 — E.K.V.와 별개의 직관적 근사):
```
gm  ≈ (1/n)·(ID/UT)
gmb ≈ ((n-1)/n)·(ID/UT)
ro  ≈ 1/(λ·ID)
```
Thermal noise 계수가 strong/weak inversion에서 **형태가 다르다**:
```
strong inversion:  i²nd/Δf = 4kT·γ·gdso        (γ≈2/3 롱채널, 채널길이 짧을수록 증가)
weak inversion:    i²nd/Δf = 2kT·n·gm           (γ가 아니라 slope factor n이 계수)
```
1/f 항은 원문 슬라이드 기준 strong/weak 양쪽 모두 `Kf/f · gm²/(WLC'ox²)`로 **완전히 동일한 식**(계수 차이조차 없음, gm이 동작영역에 따라 이미 값이 다르므로 결과만 달라짐) — 위에서 "계수만 다르다"고 한 건 thermal noise 항 얘기다. Noise 예산을 strong inversion 공식(4kTγgdso)으로만 잡으면 weak/moderate inversion 소자에서 **틀린 계수**를 쓰게 되므로, 동작영역에 맞는 thermal 식을 선택할 것.

### 7.3 Intrinsic Capacitance (E.K.V.)

원문 Annex 4 (A4.1/A4.2), 저자 제공 이미지로 확인 완료 — 근사 아님, 정확한 형태:
```
Cgsi = Cox · (qF/3) · (2qF + 4qR + 3) / (qF+qR+1)²         (A4.1)
Cgdi = Cox · (qR/3) · (2qR + 4qF + 3) / (qF+qR+1)²         (A4.2)
```
- overlap 커패시턴스(Cgsov ≈ 0.4 fF/µm, 게이트 길이 무관)를 별도 추가.
- Cgs 모델은 포화 시 실측과 잘 맞음; Cgd 모델은 포화 시 부정확(overlap+접합 의존).

---

## 8. 참고: 챕터 구조 매핑

| 章 | 제목 | 핵심 내용 | skill 관련도 |
|----|------|-----------|-------------|
| **1** | Sizing the Intrinsic Gain Stage | I.G.S. 정의, ωT=gm/C, square-law/weak/moderate sizing, **gm/ID 방법론 소개(식 1.17/1.18/1.19)** | ★★★ 방법론 근간 |
| **2** | The Charge Sheet Model Revisited | C.S.M. 물리(drift/diffusion), gm/ID 수치도출, 공통게이트 gms/ID | ★ 배경 물리 |
| **3** | Graphical Interpretation of the C.S.M. | ID 그래픽 표현, VT 곡선, MOS diode/follower/inverter/전송게이트 | ★ 직관 |
| **4** | Compact Modeling | **E.K.V. 모델**(n, IS, VTo), q·i 정규화, gm/ID 해석식(4.34/4.35), I.G.S. sizing(4.39), 이동도 열화 | ★★★ model-driven 근간 |
| **5** | The Real Transistor | 파라미터 가변 E.K.V.로 short-channel 재현, 파라미터 추출, **gm/ID·gd/ID 실측 재구성**, DIBL/CLM 분해 | ★★★ 실소자 |
| **6** | The Real Intrinsic Gain Stage | **Semi-empirical & model-driven sizing 전체 흐름**, 기생 커패시턴스 반복, partitioning, 단순화 절차(Fig.6.16), slew-rate | ★★★ 설계 절차 핵심 |
| **7** | The Common-Gate Configuration | 공통게이트 gms/ID, **cascode sizing(5단계)**, 이득·pole 평가 | ★★★ cascode |
| **8** | Sizing the Miller Op. Amp. | pole splitting, RHP zero, current mirror doublet, **2D sizing space + contour 최적화**, 저전압/고주파 예제 | ★★★ OTA 정점 |
| **A1** | extras.springer.com 데이터 사용법 | **4D/3D global variable 구조**, 주소↔전압 변환, gm/ID 추출 예제 | ★★★ 테이블 규격 |
| **A2** | MATLAB Toolbox | pMat/surfpot/IDsh/Identif3/invq/ComS/jctCap/Gss 함수 | ★ 구현 |
| **A3** | Temperature and Mismatch | 온도·mismatch → 전류·gm/ID·E.K.V. 파라미터 영향 | ★★ noise/matching |
| **A4** | E.K.V. Intrinsic Capacitance Model | Cgsi/Cgdi 식, overlap 분리 | ★★ 커패시턴스 |

### 8.1 추가 참고문헌 매핑 (Jespers 책 외부, §9~§12 근거)

| 논문 | 이 문서의 어느 절에 반영됐나 | 한 줄 요약 |
|---|---|---|
| Silveira/Flandre/Jespers 1996 (원조 논문) | §6.6 | gm/ID vs strong/weak 단순 접근 정량 비교(Table III류), 11-Tr cascode SOI OTA 검증 |
| Walker, "Chapter 5 gm-id-based design" (Murmann 계열 강의) | §2.7, §3.5, §6.5 | VDsat≈2/(gm/ID), `lookup()` 3-모드, CS/차동쌍 pole-zero 기초 예제 |
| Perrott, "Subthreshold Operation and gm/Id design" | §7.2 | subthreshold gm/gmb/ro 근사식, strong/weak noise 계수 차이 |
| Pollissard-Quatremère et al. 2013 (modified gm/ID) | §9.1~9.3, §9.5 | 60nm급 gm/ID의 VDS·L 의존성, 4-파라미터 확장, VDsat 추정법 비교 |
| Paul/Dana/Pandit 2013 (ultra-low-power gm/ID OTA) | §9.4 | 45nm VA(VDS) 의존, 바이어스 반복으로 이득 확보(면적 불변) |
| Youssef/Murmann/Omran 2020, IEEE Access (Precomputed LUT) | `lut-generation-checklist.md` §7 | 4D 보간 알고리즘(analytic-derivative Hermite), 함정 목록 |
| 실증적 foundry-specific 방법론 논문 | `lut-generation-checklist.md` §7.3 | 실제 공정 특성화 절차(I0 추출→격자 스윕→보간) |
| GMID-tool 논문 (Design & Verification of Analog CMOS Circuits) | `lut-generation-checklist.md` §7.4 | LUT 조회 도구 아키텍처(.ini/시뮬레이션 파일 분리, MX.Y 표기) |
| Cortes & Bampi (Miller OTA gm/ID+Early-V) | §6.7 | 2D sizing space를 순서형 2-phase 절차로 구체화, 이득식 L 역산 |
| Lee et al. (NGCC 3-stage 설계 가이드) | §10.1~10.2 | NGCC 닫힌형태 sizing 절차(k, ω1/ω2/ω3, Cm1/Cm2) |
| Seth & Murmann (5차 시스템 최적화) | §10.3 | 극-영점 간격 PVT 안전조건, 시간영역 settling 직접 검증 |
| Leung/Mok/Ki (3단 RHP-zero 완전 제거) | §10.4 | NMCNR 구조(Rm=1/gm3, 내부 Cm에만), 닫힌형태 Cm1/Cm2/GBW/PM |
| Garimella & Furth (보상 기법 개관) | §10.5 | Miller 정리 기반 RHP-zero 제거 기법 6종 지형도 |
| Jespers & Murmann 2015 (distortion via gm/ID) | §11 | HD2/HD3를 gm/ID의 5번째 표준 설계곡선으로 정리 |
| Fiorelli, PhD thesis (All-Inversion RF gm/ID) | §12 | RF 확장(다중 커패시턴스, 인덕터 LUT, richer noise, 매칭 탐색) |

검토 후 **낮은 가치로 판정되어 반영 제외**한 논문(중복/입문 수준, 이미 §4/§6.1에 있는 내용 재탕): "A Gm-Id Based Methodology for Designing Common Source Amplifier"(Pinjare et al.), "amplifier design using gm-id"(과제 자료). 폴더 내 나머지(PSRR/CMRR 테스트 방법론, 신경 인터페이스·생체전위 응용, 뱅갭 레퍼런스, LTSpice 튜토리얼, mixer/LNA 세부 회로, 일반 opamp 교과서)는 gm/ID sizing 방법론 자체의 범위를 벗어나 이번 보강에서 제외 — 필요 시 별도 스킬/섹션으로 다룰 것.

### 핵심 방정식 색인

| 식 | 내용 | 위치 |
|----|------|------|
| `ωT = gm/C` | gain-bandwidth = transition freq | §2.1, (1.6) |
| `gm = 2π·fT·C` | 목표 fT → gm | §2.1, (1.7) |
| `ID = gm/(gm/ID)` | 전류 sizing | §2.2, (1.17) |
| `W = W*·ID/ID*` | 폭 sizing | §2.2, (1.18) |
| `gm/ID = d[log ID]/dVG` | gm/ID 정의(반로그 기울기) | §1.3, (1.19) |
| `i = q²+q`, `IS=2nUT²C'ox(W/L)` | 정규화 전류·특성전류 | §2.3, (4.17–4.19) |
| `gm/ID = 1/(nUT)·1/(1+q)` | E.K.V. gm/ID | §2.4, (4.34) |
| `W/L = n·ωT²C²/(2K)·1/(ID−IDmin)`, `K=μC'ox` | I.G.S. sizing (E.K.V., IDmin 경유) | §4.7, (4.39) |
| `|A| = (gm/ID)·VA` | intrinsic gain | §2.5, (6.1) |
| `slew-rate = ωT/(gm/ID)` | slew-rate | §5.3, (6.10) |
| `ωT=gm1/Cm`, `ωZ=gm2/Cm` | Miller Op-Amp | §6.4, (8.8/8.11) |
| `VDsat ≈ 2/(gm/ID)` | 오버드라이브 빠른 견적(short-channel 과대추정 주의) | §2.7 |
| `HD3 ≈ (1/24)(1/nUT)²·1/(1+2q)³·vgs,pk²` | CS 3차 왜곡 | §12.1 |
| `Cm1=(gm1/gm3)·k·CL`, `Cm2=(gm2/gm3)·[k²/(1+2k)]·CL` | 3-stage NGCC OTA | §10.2 |
| `Rm=1/gm3` (NMCNR, 내부 Cm2에만 직렬) | 3단 RHP-zero 완전 제거 | §11.1 |

---

## 9. Deep-submicron 한계 (short-channel gm/ID 붕괴)

> 출처: Pollissard-Quatremère et al. 2013(modified gm/ID), Paul/Dana/Pandit 2013(ultra-low-power 45nm OTA). Jespers 책은 90~100nm대 IMEC 공정을 다루므로 이 절이 그보다 짧은 채널에서 추가로 필요한 보정이다.

### 9.1 핵심 붕괴 지점: gm/ID가 더 이상 "동작영역만의 함수"가 아니다

책 전체의 핵심 가정 — "gm/ID는 inversion level(qF/i)에만 의존, VDS·L은 별개 축" — 은 **60nm급에서 깨진다**. gd/ID vs gm/ID 곡선이 VDS·L에 강하게 의존하게 되어, §2.5의 "일정 VA로 근사" 가정을 쓰면 **최대 10배 오차**가 날 수 있다.

**대응**: sizing 변수 집합을 Jespers의 3-파라미터 `{gm/ID, L, ID}`에서 **4-파라미터 `{gm/ID, VDS, L, ID}`로 확장** — VDS를 더 이상 "나중에 확인"이 아니라 sizing 초기 입력으로 명시적으로 고정/추적해야 한다.

### 9.2 slope factor n도 더 이상 상수가 아니다

§1.3의 "n≈1.2~1.5(상수)" 가정도 짧은 채널에서는 VDS·L에 의존하는 `gms/ID`(공통게이트) 관계로부터 역산해야 정확하다 — 고정값으로 두면 gm/ID↔전류 변환에 체계적 오차가 쌓인다.

### 9.3 VDsat 추정식 비교 (100nm 이하)

4가지 VDsat 추정 방법(BSIM 직접추출 / GVO=VGS−Vth 나누기 n / `2/(gm/ID)`(§2.7) / EKV 해석식)을 비교하면, **`2/(gm/ID)`와 EKV 둘 다 short-channel에서 VDsat을 과대추정**한다 — 짧은 L에서는 BSIM 추출값이나 LUT 직접 조회를 우선한다.

### 9.4 Early 전압 VA는 VDS의 강한 함수(45nm)

CLM+DIBL이 겹쳐 **VA가 VDS 상승에 따라 오히려 감소**하는 구간이 생긴다(saturation 안에서도). 이 때문에 "L을 늘려 이득을 확보"하는 대신 **같은 L에서 바이어스(VDS) 점을 반복 조정**해 스펙을 맞추는 것이 더 효율적일 수 있다.

**수치 예**(45nm 2단 Miller OTA, Av>60dB/UGB>45kHz/PM>55°/P<350nW 스펙): 고전적 방법(L=100nm 고정, VA 상수 가정)은 41.4dB로 스펙 미달(더 큰 L 필요해 보임). VDS를 축으로 놓고 2회 반복하자 **같은 L=100nm에서 61.4dB 달성** — **면적을 늘리지 않고 바이어스 점만 옮겨** 스펙을 만족.

### 9.5 실무 함의

- L이 130nm 이하인 설계에서는 §2.2/§4의 기본 절차에 VDS를 4번째 축으로 추가해 LUT를 조회한다(3D `[L,VGS,VDS]` slice가 아니라 VDS도 sizing 루프의 명시적 변수).
- 이득 스펙 미달 시 **L을 늘리기 전에 VDS(바이어스) 반복부터** 시도 — 면적 페널티 없이 해결될 수 있다.
- PVT 코너 검증 시 gm/ID↔VA 관계 자체가 코너마다 다르게 흔들릴 수 있음을 인지(§9.1 근거).

---

## 10. 3-stage OTA (NGCC) Sizing

> 출처: Jae-Seung Lee et al., "A Design Guide of 3-stage CMOS OP amp with Nested Gm-C Frequency
> Compensation" (JSTS 2007) — 원문 Table 1~4 직접 대조 완료(아래 §10.2 수치 검증 참조).
> Jespers §6.4/이 문서 §6.4·§6.7은 **2-stage** Miller만 다룬다 — 3단이 필요한 고이득/저전압
> 스펙에서는 이 절을 쓴다.
>
> ⚠️ **원 논문은 gm/ID가 아니라 square-law 기반이다** — ω1/ω2/ω3/Cm1/Cm2 등 주파수보상 수식은
> gm_i를 추상량으로 다루므로 모델과 무관하지만, gm_i→(ID_i, W/L_i) 변환(아래 절차 5·7)은 원문에서
> 순수 제곱법칙(`W/L=2ID/(μCoxVDSAT²)`)을 쓴다. 이 스킬에서는 그 자리에 gm/ID LUT 조회를 대입하는
> 것이 자연스러운 확장이지만, 그건 원 논문의 내용이 아니라 이 스킬의 각색임을 명시해둔다.

### 10.1 왜 NGCC(Nested Gm-C Compensation)인가

3단 보상 토폴로지 중 NMC(Nested Miller)·MNMC·RNMC 대비, **NGCC는 feedforward 조건(gmf,i = gm,i, i=1,2)이 만족되면 RHP zero가 아예 생기지 않는다** — 3단에서 가장 골치 아픈 문제(RHP zero로 인한 위상 손실)를 구조적으로 없앤다.

### 10.2 닫힌 형태(closed-form) sizing 절차

**입력 스펙**: GB(gain-bandwidth), k=ω3/ω1(k>1, 통상 4), PM(목표 위상마진), CL, ICMR(입력 공통모드 범위), α=(Cm1+Cm2)/CL.

```
1. ω1 = 2π·GB                             (지배극, GB 스펙 그대로)
2. ω3 = k·ω1                              (안정성 조건, k>1)
3. ω2 = ω1·(1+2k)/k                       (63.4° 위상마진 조건)
4. gm3 = ω3·CL                            (출력단 gm3는 CL만으로 결정)
5. gm1, gm2: 원문은 **면적 비용함수 H = W1/L1 + W2/L2**(square-law로 전개하면
   gmi²/(2μiC'ox·IDi) 형태)를 최소화 — 제약조건 Cm1+Cm2 = α·CL 과 함께 (gm1,gm2)
   평면에서 H=상수는 타원, 제약식은 직선 → 접점이 최적해(Lagrange 승수법으로 닫힌형태로
   풀림). 닫힌해(원문 Eq 8.a/8.b, μn/μp=해당 공정 NMOS/PMOS 이동도 비):
   gm1 = [α(1+2k)² / (k·((μn/μp)k² + (1+2k)²))]·gm3
   gm2 = [α(1+2k)      / (k² + (μp/μn)(1+2k)²)]·gm3
6. Cm1 = (gm1/gm3)·k·CL
   Cm2 = (gm2/gm3)·[k²/(1+2k)]·CL
7. ICMR → 트랜지스터별 VDSAT → IDi = 0.5·gmi·VDSATi → (W/L)i = 2·IDi/(μCox·VDSATi²)
8. feedforward 조건: gmf,i = gm,i (i=1,2) — RHP zero 상쇄 필수조건
```

**수치 검증**(원문 Table 4, k=4·GB=10MHz·CL=10pF·α=0.3 예제 — 계산 결과가 논문과 정확히 일치):
ω2=2π×22.5MHz(위 식 3 그대로 계산: 10MHz×(1+8)/4=22.5MHz ✓), gm3=2π×40MHz×10pF≈2.5mS ✓,
gm1=0.105mS·gm2=0.186mS(원문 8a/8b 수치해) → Cm1=(0.105/2.5)×4×10pF=**1.68pF** ✓,
Cm2=(0.186/2.5)×(16/9)×10pF=**1.32pF** ✓ — 원문 Table 4와 소수점까지 일치.

### 10.3 대안: 5차 시스템 최적화 (Seth & Murmann 계열, nested-Miller+feedforward-cap)

k=4 같은 hand-recipe 대신, settling time·noise·전력을 동시에 트레이드오프하는 **제약 비선형 최적화**로 접근하는 방식도 있다(8개 정규화 pole-zero 변수 ωd/ζ/kp1/kp2/kz1..kz4). 이 접근이 주는 실무 규칙:

- **극-영점 간격을 항상 2배 이상 벌린다**: `kp1/|kzi| > 2`, `|kzi|/kp2 > 2`, `|kzi| < 0.5` — 공칭(nominal) 조건에서만 빠른 settling을 내는 극-영점 근접 배치는 **PVT 변동에 취약**하므로 지양.
- Settling spec은 위상마진 대리(proxy)가 아니라 `|εd(t)| < 0.1% (t>2.5ns)` 같은 **직접적인 시간영역 조건**으로 검증하는 것이 더 정확.
- 널링저항 열잡음 `v²nm/Δf = 4kT/gm3`도 다른 단의 noise PSD와 함께 반드시 합산.

### 10.4 3-stage RHP-zero 완전 제거 (NMCNR)

> 출처: Ka Nang Leung, Philip K. T. Mok, Wing-Hung Ki, "Right-Half-Plane Zero Removal Technique
> for Low-Voltage Low-Power Nested Miller Compensation CMOS Amplifier" (IEEE, 1999) — 원문 p.601
> Eq (6)~(11) 직접 이미지 대조 검증 완료.

Nested Miller(비-NGCC) 3단에서, **안쪽 Miller cap(Cm2)에만** 널링저항 Rm을 걸고 바깥쪽(Cm1)은 그대로 두는 배치("Structure 4")가 저항 매칭 없이 RHP zero를 완전히 없앤다:

```
Rm = 1/gm3                                (3단째 gm — 2단째 아님에 주의)
→ zero 다항식의 s² 항이 완전히 사라짐 → 남는 건 LHP zero(zLHP=gm3/Cm1)뿐 → PM에 오히려 도움
Cm1 = 4·(gm1/gm3)·CL                      (Eq 8)
Cm2 = [2/(1−kg)]·(gm2/gm3)·CL,   kg=gm2/gm3  (Eq 9)
GBW = gm1/Cm1 = (1/4)·(gm3/CL)            (Eq 10)
PM  = 60° + arctan(zLHP/GBW)  > 60°       (Eq 11)
```
실측 이득: 대역폭/slew-rate/settling ~30% 개선, PM +3°, PSRR− ≥49dB 개선 — Cm 값 자체가 작아져 **면적도 줄어든다**(전력 페널티 없음).

⚠️ `kg`는 원문 어디에도 추가 결정식이나 수치 예제가 없다 — Eq (8)/(9)로 Cm1/Cm2를 잡으면 "3차
Butterworth 극점 배치"가 된다는 설명은 있지만, 그건 이미 정해진 Cm1/Cm2의 결과에 대한 설명이지
`kg` 자체를 정하는 식이 아니다. 즉 `kg`는 원문이 의도적으로 남긴 설계 자유도다(GBW·PM 헤드라인
식 어디에도 나타나지 않음) — `topology_library.py`의 `nmcnr_3stage_topology()`에서 호출자가
직접 정하게 해뒀다.

### 10.5 RHP-zero 제거 기법 전체 지형도

기존 §6.4·§6.7의 "Cm에 직렬저항 R=1/gm2"는 **Miller 정리(Zin=Zc/(1+Av))에서 나온 여러 기법 중 하나**일 뿐이다. 순수 저항 대신 능동소자로 바꾼 변형들을 정리하면:

| # | 기법 | 영점 위치(근사) | 비고 |
|---|------|-----------------|------|
| 1 | Nulling resistor | `−1/(Rm·Cm)` (Rm=1/gmY 최적) | 가장 기본, 저항 정밀도 필요 |
| 2 | Ahuja/cascode 보상 | `−gmCG/Cc` | 기존 cascode 소자 재사용 — 추가 전류 无 |
| 3 | Current-mirror 기반 inverting buffer | `−gmBU/Cc` | 이미 있는 unity-gain mirror 재사용(RNMC LDO 등) |
| 4 | 저항보강 current buffer | `−1/(Rc·Cc)` (Rc≫1/gmCB) | #2/#3에 Rc 추가 — 영점을 gm 의존성에서 분리 |
| 5 | 내부노드 passive LHP zero | `−1/(Ri·Ci)` | 온칩 소형 R·C, 외부 ESR-zero와 동일 원리 |
| 6 | Source-degeneration | `−1/(Rs·Cs)` | 차동쌍 source에 Rs–Cs, 고-PSRR LDO 등에 사용 |

선택 기준: 회로에 이미 cascode/전류거울이 있으면 #2/#3(추가 바이어스 전류 無)을 우선 검토하고, 정밀한 영점 위치 제어가 필요하면 #4로 gm 의존성을 없앤다.

---

## 11. Distortion / Linearity (gm/ID 기반)

> 출처: Jespers & Murmann, "Calculation of MOSFET Distortion Using gm/ID" (IEEE, 2015). §3.3의 4대 설계 곡선(gm/ID vs VGS, ID/W vs gm/ID, gain vs gm/ID, fT vs gm/ID)에 **5번째 표준 곡선(HD vs gm/ID)**을 추가하는 확장.

### 11.1 CS 단 왜곡

기본 E.K.V. 관계(i=q²+q, gm/ID=1/(nUT)·1/(1+q))로부터:
```
HD2 ≈ (1/4)·(1/nUT)·1/(1+2q)·vgs,pk
HD3 ≈ (1/24)·(1/nUT)²·1/(1+2q)³·vgs,pk²
```
**n과 q(=gm/ID)에만 의존** — IS나 VT는 등장하지 않는다. 즉 왜곡도 gm/ID 축 하나로 정리된다.

### 11.2 차동쌍

대칭성으로 2차항(HD2) 소거, 3차항만 남음:
```
HD3 ≈ (1/24)·(1/nUT)²·(1+3q)/[2(1+2q)³]·vid,pk²
```
CS 단 대비 weak inversion에서 **6dB 개선**, strong inversion에서는 **2.5dB 개선**에 그침 — 차동화의 왜곡 저감 효과는 동작영역에 따라 크게 다르다.

### 11.3 설계-by-왜곡스펙 절차

```
1. 목표 HD3·신호진폭(vgs,pk 또는 vid,pk) 지정
2. 위 HD3 식을 q(=gm/ID)에 대해 역산
3. gm/ID를 얻으면 이후는 표준 sizing 절차(§2.2/§4)와 동일 — ID/W는 평소처럼 차트에서 조회
```
즉 "HD3 vs gm/ID"를 §3.3의 4대 곡선과 나란히 두면, **선형성 스펙도 gm/ID sizing 루프 안에서 그대로 처리**된다 — 별도 왜곡 시뮬레이션 반복이 필요 없어진다(1차 견적 단계에서는).

### 11.4 gds 비선형성(DIBL) 기반 HD2 상쇄

DIBL로 인한 출력 컨덕턴스 비선형성(gd1, gd2, x11 — VDS에 대한 dVT/dVDS, d·log(IS)/dVDS로 SPICE에서 추출)을 이용해, **HD2를 0으로 만드는 부하저항 R 값을 닫힌 형태로 도출** 가능 — 원문 예제(gm/ID=15S/A, gm=6.3mS, L=60nm, VDS=0.6V)에서 R=2.32kΩ일 때 null 발생, SPICE와 -90~-40dB 범위 전체에서 잘 일치(단, HD2<-80dB급 저왜곡을 노리려면 R 공차를 엄격히 관리해야 함 — R 민감도가 큼). 저왜곡이 최우선 스펙인 CS 단에서 부하 설계 시 참고.

---

## 12. RF 확장 (매칭/NF/수동소자 공동설계)

> 출처: Fiorelli, PhD thesis(All-Inversion-Region gm/ID for RF Blocks). §1~§11은 baseband/저주파 아날로그를 다룬다 — **RF 블록(LNA 등)은 같은 gm/ID 코어 방법론 위에 3가지 층이 추가로 필요**하다. 전체를 재서술하지 않고 baseband sizing과 다른 지점만 요약한다.

### 12.1 커패시턴스 모델이 lumped Cgg 하나로 부족

`fT = gm/[2π(Cgs+Cgd+Cgb)]` 계산에 개별 intrinsic 성분(§7.3의 Cgsi/Cgdi 확장판)뿐 아니라 **extrinsic 성분**(overlap `Cgse=Cgde=W·C″o`, gate-bulk `Cgbe=2L·C″ob`, 접합 `Cbse/Cbde`)까지 필요 — layout 의존적이라 baseband의 "Cgg 하나"로는 부족하다.

### 12.2 수동소자(인덕터)도 LUT 대상이다

트랜지스터와 **동일한 방식**으로 인덕터도 특성화한다: 공정에서 구현 가능한 각 인덕턴스 L_ind마다 최소 series 저항 Rs,ind·최대 parallel 저항 Rp,ind를 주파수별로 테이블화(§2.3.1) — LNA sizing 시 gm/ID LUT에서 트랜지스터를 고르듯 이 인덕터 LUT에서 소자를 고른다.

### 12.3 Noise 모델이 훨씬 richer

White noise `i²w,d = 4kBTγ·gd0`, induced gate noise 계수 δ, 그리고 `α≡gm/gd0`(gd0=VDS=0에서의 gds) —
이 **세 파라미터(α, γ, δ)가 서로 독립적으로** gm/ID의 함수로 변한다(원문 §2.2.4). 통상값은
γ=2/3, δ=2γ, α≈0.6이지만 short-channel·moderate/weak inversion에서는 이 값들이 크게 벗어난다
— γ/α 비율은 비교적 안정적이라 이 비율만 상수로 근사하는 것도 방법. Gate noise-drain noise
상관계수 `|c|≈0.4`(Van der Ziel/Lee)도 확인됨. Flicker corner frequency(fc,1/f³)는 DC 특성이 아니라
**실제 동작주파수 대비 오프셋에서 능동적으로 검증해야 하는 설계 제약**이다 — 원문 VCO 설계
예제(f0=2.4GHz)에서도 "fc,1/f³ > Δf이면 설계 재시도"가 매 반복의 명시적 체크 항목이다.

### 12.4 sizing 루프에 매칭망 탐색이 추가됨

(ID, gm/ID) 후보쌍을 스윕하면서, 각 후보마다 인덕터 LUT에서 **Gout를 최소화하는 소자 → 그 중 NF를 최소화하는 소자**를 고르는 2단 탐색이 baseband 루프 위에 추가된다(§4의 "3~4 반복 수렴"과 같은 자리에 매칭망 선택 루프가 끼어든다고 생각하면 된다).

**실무 판단**: RF 블록이 아니면 이 절은 무시하고 §1~§11만으로 충분하다. RF 블록이라면 baseband 결과를 **입력 매칭·NF 재검증**(§4.5 검증 단계에 추가) 없이 그대로 쓰지 말 것.

---

## 부록: 방법론 요약 (1-page cheat)

```
[스펙: fT(또는 slew), C, gain, phase margin]
        │
        ▼
1. gm = 2π·fT·C                          (fT 스펙 → gm 고정)
2. 동작영역 선택: gm/ID (또는 qF)
      weak↑ = 효율/gain↑, 속도↓, W↑
      strong↓ = 속도↑, 효율/gain↓, W↓
      → moderate inversion(qF≈0.1~1) 이 통상 최적
3. ID = gm / (gm/ID)                     (테이블 or E.K.V. 해석식)
4. W  = L · ID / IDu                     (전류-폭 비례, IDu=ISuo·i)
5. 기생 CJD를 C에 더해 3~4 반복 수렴
6. 검증: f_nqs(준정적), A=(gm/ID)·VA(이득), slew-rate, matching/noise
7. 고급 시뮬레이터로 미세조정
```

**한 줄 요약**: fT가 gm을 고정하고, gm/ID(동작영역)를 자유변수로 선택해 전류·폭·이득·속도·전력의 절충을 하나의 차트에서 읽어 sizing한다. 전 inversion 영역 연속, short-channel 대응, moderate inversion 최적.
