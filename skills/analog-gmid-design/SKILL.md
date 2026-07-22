---
name: analog-gmid-design
description: |
  gm/ID 방법론 기반 아날로그 CMOS 트랜지스터 sizing skill. 전통적 square-law(제곱법칙) 대신
  시뮬레이션/모델 기반 lookup table·차트로 weak/moderate/strong inversion 전 영역에서 ID·W를
  연속적으로 결정. Short-channel/deep-submicron 소자에서도 유효.
  다음 상황에서 사용:
  (1) 트랜지스터 sizing - 목표 fT(gain-bandwidth)·gain·전력에서 ID, W/L 결정
  (2) 동작점 선택 - gm/ID(또는 qF)로 weak/moderate/strong inversion 절충
  (3) Lookup Table 준비 - 공정별 gm/ID 차트를 만드는 SPICE/Spectre 스윕 절차
  (4) 회로별 적용 - Intrinsic Gain Stage, cascode, current mirror, Miller OTA(2단)·3-stage OTA(NGCC) sizing
  (5) 검증 - 준정적(quasi-static) 조건, slew-rate, matching/noise, distortion(HD2/HD3) 확인
  (6) Deep-submicron(L≲130nm) 보정 - gm/ID의 VDS·L 의존성, RF 블록(매칭/NF) 확장
  아날로그 CMOS 트랜지스터 sizing, 저전력/저전압 아날로그 설계, OTA/Op-Amp 설계 요청이 보이면
  반드시 이 스킬을 사용.
  트리거: gm/ID, gmid, transconductance efficiency, inversion coefficient, moderate inversion,
    weak inversion, strong inversion, OTA sizing, Op-Amp sizing, 트랜지스터 사이징, 아날로그 회로 설계,
    current density, ID/W, intrinsic gain, pole splitting, Miller compensation, cascode sizing,
    lookup table 설계, gm/gds, fT sizing, slew-rate 설계, 3-stage OTA, NGCC, nested Miller,
    RHP zero removal, nulling resistor, distortion, HD2, HD3, IIP3, VDsat, deep-submicron gm/ID,
    LNA sizing, RF gm/ID
---

# gm/ID Analog Design Skill

> 정본: `references/gm-id-methodology.md`(Jespers, *The gm/ID Methodology*, Springer 2010 전체 요약 —
> 방법론·수식·worked example 전부 여기 있다. 이 SKILL.md는 재서술하지 않고 절차/판단 지점만 안내한다).

## 핵심 원칙

square-law는 weak/moderate inversion과 short-channel 소자에서 무너진다. gm/ID 방법론은
**gm/ID를 만능 x축**으로 삼아 weak→moderate→strong inversion을 하나의 연속 곡선으로 다룬다.

**gm/ID 방법론 핵심 원칙:**

1. fT(또는 slew-rate) 스펙이 **gm을 고정**한다 — `gm = 2π·fT·C` [→references §2.1]
2. gm/ID(또는 qF)는 **자유 변수** — 여기서 효율/속도/이득 절충을 선택한다 [→§5]
3. ID, W는 gm/ID 선택 이후 **차트/LUT에서 읽는다** — 직접 계산하지 않는다 [→§2.2, §4]
4. **Moderate inversion이 기본 출발점** — 대부분의 저전력 아날로그 설계에서 최적 절충 [→§5.2]

---

## 1. 설계 절차 (6단계)

```
[스펙: fT(또는 slew-rate), 부하 C, target gain, phase margin]
        │
        ▼
1. gm = 2π·fT·C                          (fT 스펙 → gm 고정, 협상 불가)
        │
        ▼
2. 동작점 선택: gm/ID (또는 qF)
      weak↑   = 효율/gain↑, 속도↓, W↑ (기생 커패시턴스 위험)
      strong↓ = 속도↑, 효율/gain↓, W↓
      → **moderate inversion(qF≈0.1~1)에서 시작** [→§5]
        │
        ▼
3. ID = gm / (gm/ID)                     (LUT 보간 또는 E.K.V. 해석식)
        │
        ▼
4. W  = L · ID / IDu                     (전류-폭 비례, IDu = ISuo·i)
        │
        ▼
5. 기생 CJD를 C에 더해 3~4 **반복 수렴** (W가 커지면 CJD가 자라 ID가 재상승할 수 있음 [→§4.2])
        │
        ▼
6. 검증: f_nqs(준정적), A=(gm/ID)·VA(이득), slew-rate, matching/noise [→§4.5, §7]
        │
        ▼
   고급 시뮬레이터(SPICE/Spectre)로 미세조정 — gm/ID는 최적 "근방"으로 안내하는 도구
```

상세 방정식·유도·MATLAB 발췌는 재서술하지 않는다 — `references/gm-id-methodology.md` §2/§4를 그대로 따른다.

---

## 2. 동작점(gm/ID) 선택 판단 기준

| 조건 | 권장 동작점 | 근거 |
|---|---|---|
| 전력 최소화가 최우선, 속도 여유 있음 | Weak~Moderate (qF < 0.5) | gm/ID 최대 → 전류 효율 최고 [→§1.3] |
| Gain-bandwidth·면적 균형 (일반 Op-Amp 1단) | **Moderate inversion (qF ≈ 0.1~1)** | 효율·기생·이동도열화 절충이 가장 좋음, 파라미터 3개(n/VTo/ISuo)만으로 sizing 충분 [→§5.2] |
| 고주파(수백 MHz~GHz), 속도가 최우선 | Strong inversion, 짧은 L | fT↑ 필요, 단 이득·이동도열화 손해 — L 단축과 이득 손실을 절충 [→§2.6] |
| 정전류원/전류거울/차동쌍 (matching 민감) | Moderate~Strong (qF 크게) | Weak inversion은 mismatch 민감도가 높음(VTo 편차 지배적) [→§7.1] |
| 1/f noise 저감 필요(입력단) | 큰 게이트 면적, 단 기생 커패시턴스(doublet) 주의 | 면적↑=noise↓ vs doublet 주파수 하락(ringing 위험) 상충 [→§6.3, §7.2] |

⚠️ **weak inversion로 갈수록 W가 급증**해 기생 커패시턴스가 외부 부하를 압도할 수 있다 — 반드시
§1 스텝 5의 반복 수렴으로 최적점(보통 moderate inversion 중앙)을 재확인한다.

---

## 3. Lookup Table 준비 (공정별)

새 공정에 이 방법론을 적용하려면 gm/ID 차트/LUT가 먼저 필요하다. 스윕 방법론 요약은
`references/gm-id-methodology.md` §3, 실제 SPICE/Spectre 스윕 스크립트 골격은
`references/lut-generation-checklist.md` 참조. Spectre 연동이 필요하면 `chip-verification`
skill의 `spectre-integration.md`와 함께 사용한다.

**최소 요구 데이터** (LUT 또는 E.K.V. 파라미터 세트 중 하나):
- Semi-empirical: (L, VGS, VDS, VS) 4D 격자에서 ID, gm, gds, Cgg(+Cgs/Cgd/Cgb) — `references/gm-id-methodology.md` §3.1
- Model-driven(E.K.V.): n, VTo, ISuo + 이동도열화 다항식(θ) — 같은 문서 §3.4

---

## 4. 회로별 적용 가이드

| 회로 | 참조 | 핵심 판단 지점 |
|---|---|---|
| Intrinsic Gain Stage(1단 기본) | `references/gm-id-methodology.md` §6.1, §6.5 | fT→gm→(W,VGS,A) 단일 곡선 산출, moderate inversion 절충점 선택 |
| Cascode(공통게이트+공통소스) | 같은 문서 §6.2 | Q1이 gm(전류) 설정, Q2가 출력 임피던스 증폭, 2번째 pole(공통노드 기생) 확인 |
| Current Mirror | 같은 문서 §6.3 | 다이오드 접속 소자가 만드는 pole-zero doublet 위치 확인(fT의 3배 이상 유지) |
| Miller Op-Amp(2단 OTA) | 같은 문서 §6.4, §6.7 | pole splitting, RHP zero, **2D sizing space**(qF1, qF2)에서 등전력/등면적 contour로 절충, 이득식 기반 L 역산(§6.7) |
| **3-stage OTA(NGCC/NMC)** | 같은 문서 §10 | 2단으로 이득·전력 스펙을 못 맞출 때. NGCC 닫힌형태 sizing(k, ω1/ω2/ω3, Cm1/Cm2), RHP-zero 완전제거(NMCNR, §10.4) |
| Distortion/Linearity 스펙이 있는 단 | 같은 문서 §11 | HD2/HD3을 gm/ID의 5번째 설계곡선으로 취급 — 왜곡 스펙에서 gm/ID를 역산 |
| RF 블록(LNA 등) | 같은 문서 §12 | baseband sizing 위에 매칭망·NF·richer noise 층이 추가됨(코어 방법론은 동일) |

각 회로의 구체 sizing 방정식·MATLAB 발췌·수치 예제는 위 문서에서 재서술 없이 그대로 참조한다.

⚠️ **Deep-submicron(L≲130nm)이면 §9(Deep-submicron 한계)를 먼저 읽는다** — gm/ID가 VDS·L에도
의존하게 되어 위 표의 기본 절차에 VDS를 4번째 sizing 축으로 추가해야 할 수 있다.

---

## 5. 검증 체크리스트 (Definition of Done)

- [ ] **준정적 확인**: `f_nqs = gm/(2π·Cgg)` 계산, `fT ≤ 0.1·f_nqs` 성립하는가?
- [ ] **이득 확인**: `A = (gm/ID)·VA` 목표 스펙 만족하는가? (Early 전압 VA는 weak inversion에서만
      게이트전압 무관 — "VA가 항상 한 점으로 수렴한다"는 가정 금지 [→references §2.5])
- [ ] **Slew-rate 확인**: `slew-rate = ID/C = ωT/(gm/ID)` — 정현파 조건 만족하는가?
- [ ] **Matching**: 정전류원/전류거울/차동쌍이 충분히 strong 방향인가(weak inversion mismatch 민감)?
- [ ] **Noise**: 1/f 저감을 위한 면적 확대가 doublet 주파수를 fT 근처로 끌어내리지 않았는가?
- [ ] **기생 수렴**: §1 스텝 5의 반복이 실제로 수렴했는가(W 급증 후 재상승 패턴 확인)?
- [ ] **Distortion**(왜곡 스펙이 있으면): HD2/HD3를 gm/ID의 함수로 확인했는가 [→references §11]?
- [ ] **Deep-submicron**(L≲130nm이면): VDS를 4번째 sizing 축으로 다뤘는가, VA(VDS) 의존성을 무시하지
      않았는가 [→references §9]?
- [ ] 고급 시뮬레이터(SPICE/Spectre)로 최종 미세조정했는가 — gm/ID sizing은 출발점이지 최종값이 아니다.

---

## 참조 파일

- `references/gm-id-methodology.md` — 방법론 전체(핵심 변수·관계식·LUT 생성·설계 절차·트레이드오프·
  worked example·noise/matching·§9 deep-submicron 한계·§10 3-stage OTA·§11 distortion·§12 RF).
  **정본** — 이 SKILL.md의 모든 수식·절차 근거.
- `references/lut-generation-checklist.md` — 공정별 gm/ID 차트 생성용 SPICE/Spectre 스윕 체크리스트 +
  §7 실전 보간 알고리즘(4D LUT를 실제로 정확·빠르게 조회하는 법, 함정 목록, foundry 특성화 절차).
- `assets/sizing_recipe.py` — §1 6단계 sizing 방정식 구현. `SemiEmpiricalGmIdLUT`(numpy 기반 4D LUT
  보간 구현)와 `build_toy_lut()`(E.K.V. 해석식 합성 LUT)로 **그대로 실행 가능** — 자신의 공정
  스윕 데이터가 있으면 `build_toy_lut()` 대신 실측 4D 배열로 `SemiEmpiricalGmIdLUT(...)`를 만들면
  된다. `python sizing_recipe.py`로 바로 확인 가능. **`find_optimal_sizing()`**: "이 gm/ID를 고르면
  결과가 어떻게 되나"를 넘어 "스펙(gain/면적/준정적 제약)을 만족하며 전력 또는 면적이 최소인 sizing을
  찾아라"는 요청에 대응 — 단일 소자, (L,VDS,gm/ID) 격자 전체를 스윕하는 이산 그리드서치다.
  **`optimize_multistage()` + `topology_fn` 콜백**: 다단 회로로 확장 — 토폴로지별 위상보상
  방정식만 작은 콜백으로 교체하면 되는 **제네릭** 엔진이라, 새 토폴로지 추가 시 엔진을 다시 짤
  필요가 없다. 단, gm_i가 스펙만으로 유일하게 안 정해지는 토폴로지(NMCNR의 3차 극점 배치 kg 등)는
  topology_fn 안에서 남은 자유도를 근사해야 한다(회로 이론 자체의 한계 — 아키텍처 한계 아님).
  연속 최적화·진짜 2D sizing space 접점 탐색은 아직 범위 밖.
- `assets/topology_library.py` — 실무에서 반복 사용되는 강건한 토폴로지의 `topology_fn` 모음
  (계속 늘려가는 라이브러리 구조). 매번 새 토폴로지용 함수를 직접 짜지 않고 여기서 골라 쓴다.
  - `miller_ota_topology()` — 2단 Miller OTA(§6.4/§10.2). 원문 수식과 완전 대조 검증됨. 실측
    sky130 LUT로 gm1/gm2 재현 확인(`sky130-worked-example.md` §11).
  - `nmcnr_3stage_topology()` — 3단 NMCNR/RHP-zero 완전제거 구조(§10.4, Leung/Mok/Ki, IEEE 1999).
    Eq 6~11 전체를 원문 페이지 이미지로 직접 대조 검증. `kg`(=gm2/gm3)는 원문 자체가 추가
    결정식 없이 남긴 자유도임을 원문에서 확인(재구성 실패가 아니라 확정된 사실) — 기본값
    (0.5)은 임의값이니 실사용 전 SPICE로 재확인 필요.
    ⚠️ **이 함수의 Eq 10/11이 예측하는 GBW/PM이 실제로 맞는다는 보장이 없다** — 그 식은
    "우세극이 나머지 극점과 충분히 떨어져 있다"는 근사인데, 스테이지2 고유이득이 어떤 문턱을
    넘으면 이 근사가 무너져 개루프 응답에 노치(0dB 재교차)가 생긴다(sky130-worked-example.md
    §12.4~§12.7 전체가 이 발견의 실측 기록). **사이징 후 반드시 `nmcnr_predict_notch()`로
    재검증할 것** — 근사 없이 정확한 3-노드 전달함수로 GBW/PM/노치 여부를 직접 계산해준다
    (다시 유도할 필요 없음). 보상소자 실값(Cm1/Rm/Cm2)이 필요하면 `nmcnr_compensation_elements()`.
  - `ngcc_3stage_topology()` — 3단 NGCC(§10.2, Lee et al.). gm1/gm2/gm3 전부 원문 Eq 8.a/8.b로
    완전 결정됨(원문 페이지를 이미지로 렌더링해 직접 판독, Table 4 수치와 삼중 교차검증 —
    처음엔 텍스트 추출이 뒤섞여 "OCR 손상으로 재현 불가"라고 오판했다가 정정한 사례). 유일하게
    남는 입력은 `mu_ratio`(=μn/μp, 해당 공정의 이동도 비) — 이건 설계 자유도가 아니라 **공정
    파라미터**라 기본값(원 논문 0.18µm 예제 역산값)을 자기 공정 값으로 교체해서 쓰면 된다.
  - 각 함수 docstring에 "원문 대비 검증 상태"(완전 검증 vs 근사/자유도 고정)를 명시해뒀다 —
    사용 전 반드시 확인할 것.
- `references/topology-fn-derivation-guide.md` — **새 topology_fn을 추가하기 전에 먼저 읽을
  문서**. 논문의 위상보상 방정식을 어떻게 "스펙 -> gm_i" 닫힌해로 역산하는지 일반 절차(§1)와,
  이미 만든 3개 토폴로지(Miller/NMCNR/NGCC)의 실제 유도 과정(어느 식을 어느 식에 대입해 무엇이
  소거됐는지, 어떤 자유도가 왜 남았는지)을 기록한다. `topology_library.py`의 docstring은 결론
  (검증 상태)만 담고, 그 결론에 이르는 추론은 여기 있다 — 코드 주석을 다시 역산하지 말 것.
- `references/topology-behavior-diagnosis-workflow.md` — **SPICE 결과가 설계식/원문 예측과
  질적으로 다를 때**(단순 10~20% 오차가 아니라 노치·예상 밖 극점/영점처럼 구조적으로 다른 경우)
  따를 일반 진단 절차. sizing과 위상보상 설계식을 분리해 결백 확인 → 제거법으로 최소 원인 좁힘 →
  이상화(VCCS+ro) 모델로 실소자 기생 여부 구분 → 정확한 노드방정식 직접 유도(근사식 대신) →
  처음 의심한 변수가 진범인지 공변 변수 분리로 재확인 → 실측 SPICE 재검증 → 측정 방법론 자체도
  교차검증 → 트레이드오프까지 정직하게 보고, 8단계로 구성된다. NMCNR 노치 조사
  (`sky130-worked-example.md` §12.7)가 이 절차의 완전한 worked example이다.
- `references/sky130-worked-example.md` + `assets/sky130_lut_sweep.py` +
  `assets/sky130_nfet_pfet_lut_sample.npz` — **toy가 아닌 진짜 실리콘 데이터** 실전 사례. 오픈소스
  PDK(SkyWater sky130) + ngspice로 Cgg/Cgd까지 **AC/Y-parameter 기반**(op-info 대비 최대 300배
  정확도 차이 발견 후 전체 재스윕)으로 뽑은 4D LUT를 `SemiEmpiricalGmIdLUT`에 로드하고 §6.5(Walker
  CS/차동쌍) sizing까지 검증했다. 실전 include 함정(mismatch 파라미터, PMOS의 lod.spice, L/W 단위
  접미사, op-info Cgd/Cdd 불신뢰) 및 "이상치처럼 보이지만 실제로는 나쁜 gm/ID 선택을 드러낸 것뿐이었던"
  검증 사례 포함.

## Cross-Skill 참조

- Sizing 결과를 behavioral 모델로 미리 검증(수렴성·연속성) → `verilog-a` skill
- AMS 검증환경(듀얼탑, Spectre 연동)에 이 sizing 결과를 실제 회로로 배치 → `chip-verification` skill
