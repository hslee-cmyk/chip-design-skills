---
name: analog-gmid-design
description: |
  gm/ID 방법론 기반 아날로그 CMOS 트랜지스터 sizing skill. topology+spec이 주어지면
  square-law 대신 gm/ID 기반 lookup table로 weak~strong inversion 전 영역에서 모든 소자
  (능동+수동)의 값을 확정한다. 논문/외부 예제는 검증용 테스트케이스일 뿐 재현이 목적이
  아니다 — 실무엔 정답이 없다고 전제한다. 다음에 사용: 트랜지스터 sizing(fT/gain/전력→ID,
  W/L), 동작점(gm/ID) 선택, 공정별 LUT 준비, 회로별 적용(IGS/cascode/mirror/Miller 2단/NGCC
  3단), 검증(준정적/slew-rate/matching/distortion), deep-submicron·RF 보정, sizing→layout
  (stick diagram/Euler trail) 피드백, bias/replica·보상소자(Cc/Rz) 사이징. 저전력 아날로그,
  OTA/Op-Amp 설계 요청 시 반드시 사용.
  트리거: gm/ID, gmid, transconductance efficiency, inversion coefficient, moderate/weak/
    strong inversion, OTA/Op-Amp sizing, current density, intrinsic gain, pole splitting,
    Miller compensation, cascode sizing, gm/gds, fT sizing, 3-stage OTA, NGCC, RHP zero,
    nulling resistor, distortion, HD2, HD3, VDsat, LNA sizing, stick diagram, Euler trail,
    finger 배치, common-centroid, bias generator, replica bias, CMFB sizing
---

# gm/ID Analog Design Skill

> 정본: `references/gm-id-methodology.md`(Jespers, *The gm/ID Methodology*, Springer 2010 전체 요약 —
> 방법론·수식·worked example 전부 여기 있다. 이 SKILL.md는 재서술하지 않고 절차/판단 지점만 안내한다).
> 함수를 언제 호출할지는 `references/function-selection-map.md`가 정본이다 — 이 문서도
> 함수 내부 로직을 재서술하지 않는다.

## 이 skill의 목적 (반드시 먼저 읽을 것)

**임의의 topology + spec이 주어지면, 그 topology를 구성하는 모든 소자(트랜지스터 + 수동소자)에
대해 spec을 만족하는 구체적 값을 확정하는 것**이 이 skill의 목적이다. 논문/worked example은
이 방법론이 맞게 작동하는지 검증하는 테스트 케이스일 뿐, 재현 자체가 목적이 아니다 — 실무
설계에는 대조할 논문이나 "정답"이 없다는 것을 항상 전제로 판단한다. 따라서:

- "이 값이 스펙 문서/논문에 안 나온다"는 **어떤 소자도 사이징을 건너뛸 근거가 되지 못한다**
  (§1.5).
- 특정 논문·사례는 검증 근거나 각주로만 인용한다 — 판단 규칙 자체를 논문 특정 문구("~라고
  안 한다")로 서술하지 않는다.

## 핵심 원칙

square-law는 weak/moderate inversion과 short-channel 소자에서 무너진다. gm/ID 방법론은
**gm/ID를 만능 x축**으로 삼아 weak→moderate→strong inversion을 하나의 연속 곡선으로 다룬다.

**gm/ID 방법론 핵심 원칙:**

1. fT(또는 slew-rate) 스펙이 **gm을 고정**한다 — `gm = 2π·fT·C` [→references §2.1]
2. gm/ID(또는 qF)는 **자유 변수** — 여기서 효율/속도/이득 절충을 선택한다 [→§5]
3. ID, W는 gm/ID 선택 이후 **차트/LUT에서 읽는다** — 직접 계산하지 않는다 [→§2.2, §4]
4. **Moderate inversion이 기본 출발점** — 대부분의 저전력 아날로그 설계에서 최적 절충 [→§5.2]

**함수 우선순위 대원칙(반드시 지킬 것)** — 이 skill의 모든 작업은 다음 순서로만 수행한다:

1. **harness(오케스트레이션) 함수를 먼저 시도한다** — `run_sizing_pipeline()`/`optimize_multistage()`/
   `run_full_circuit_audit()`/`audit_row_split()`/`run_topology_pipeline()`. 이 함수들은 여러
   원소 함수를 정해진 순서로 묶어 실행하는 워크플로우 자체다 — `function-selection-map.md`
   맨 위 "harness 목록"에서 상황에 맞는 게 있는지 먼저 확인한다.
2. **harness가 이 세부 작업을 담당하지 않을 때만** 원소 함수를 직접 호출한다 — `function-
   selection-map.md`의 나머지 표에서 이미 구현된 함수를 찾아 그대로 쓴다.
3. **①·② 어디에도 없을 때만** AI가 새 코드/로직을 작성해 그 작업을 수행한다 — 이때도 §1.5
   (가정 금지)와 이 표의 나머지 원칙은 그대로 적용된다.

**하지 말 것**: harness나 원소 함수가 이미 있는데 그걸 거치지 않고 즉석 스크립트/손 계산으로
같은 일을 다시 구현. **왜**: 이미 검증된 경로(그래프 이론 증명, 실측 스윕, self-test)를
우회하면 이 세션 내내 반복된 실패 패턴(아래 표 1번, `known-incidents.md`)이 그대로 재현된다.

**절대 원칙 (하지 말 것 — 전부 실제 사고에서 나옴, 전체 경위는 `references/known-incidents.md`):**

| # | 하지 말 것 | 대신 할 것 |
|---|---|---|
| 1 | 함수가 있는데 결과를 손으로 근사·요약·재구성 | 그 함수를 실제로 호출해 나온 값을 그대로 사용(`function-selection-map.md`에서 어느 함수인지 확인) |
| 2 | 외부 논문/자료의 topology를 일반 지식으로 상상해서 채움 | 원문 도면을 직접 읽고(이미지 렌더링 등) 소자별 넷리스트 표로 먼저 옮겨 적은 뒤 그 표만 근거로 진행 |
| 3 | 리포트 시각화 코드를 새로 작성하거나 텍스트로 대체 | `assets/report_template.html`의 렌더링 함수를 코드 그대로 복사해 재사용 |
| 4 | 소자에 대한 명시적 목표치가 없다고 사이징을 스킵("범위 밖"으로 처리) | §1.5의 절차로 로컬 타겟을 유도해 반드시 값을 확정 |
| 5 | **이 skill의 함수 집합을 수정·확장하고서, spec→instance.json 전 구간이 여전히 harness만으로·재현 가능하게·최선의 결과로 완주되는지 재검사하지 않고 완료 보고**(2026-07-31, 배치 7-6 발견 계기 — 다른 4개와 달리 특정 사고가 아니라 "매 수정마다 반복해야 하는 게이트"라는 게 원칙 자체) | §5 마지막 항목("skill 최종 게이트")의 절차 그대로 매번 재실행 — 1회성 설계 검증이 아니라 이 skill 자신의 무결성에 대한 상시 게이트임을 명심할 것 |
| 6 | 순수 수식 함수의 self-test라는 이유로, 실제 `library/*.topology.json`에 존재하는 소자 이름을 그 회로에서의 kind/connectivity를 확인하지 않고 논문/기억만으로 역할 배정해서 씀(2026-07-31, `telescopic_class_ab` CMRR 계기 -- Phase 2에서 삭제) | 그 이름을 값에 채워 넣기 전에 `load_topology(그 실제 파일)`로 kind/connectivity(같은 노드 공유 등)를 먼저 assert — "수식 검증"과 "역할 배정 검증"을 별도 블록으로 분리 |

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
실제로 어느 함수를 호출할지는 `references/function-selection-map.md` §1을 확인한다.

---

## 1.5 모든 소자는 확정된 값을 가져야 한다 — "out of scope" 금지

주어진 topology 안의 **어떤 소자도 "사이징 안 함/범위 제외"로 결과를 끝내지 않는다.** 모든
소자는 (a) 구체적 W/L 또는 R/C 값과 (b) 그 값이 왜 spec을 만족하는지의 근거를 가진 채로
끝나야 한다 — 그래야 다음 단계(layout)가 그 값을 바로 쓸 수 있다. 이 규칙은 트랜지스터뿐
아니라 **수동 보상소자(Cc, Rz 등)에도 동일하게 적용**된다.

### 목표치가 명시적으로 안 주어진 트랜지스터 서브블록 (바이어스 생성/레플리카 네트워크 등)

이런 서브블록(CMFB 네트워크, bias generator 등)은 스펙 문서가 gm/ID나 gm 수치를 직접 주지
않는 경우가 흔하다. 그래도 다음 절차로 로컬 타겟을 스스로 유도한다:

1. 이 서브블록이 전체 회로에서 하는 **기능적 역할**을 명시한다(예: "이미 사이징된 브랜치 X의
   동작점을 복제해 다른 소자의 게이트에 공급").
2. 그 역할이 요구하는 제약을 스펙으로 번역한다(예: "레퍼런스 소자와 같은 gm/ID로 브랜치 X의
   동작점을 추종해야 한다", "전류 정확도 Y% 이내", "헤드룸 마진 Z 이상").
3. 그 제약을 gm/ID·미러비·전류 목표로 바꿔 **§1과 동일한 6단계 절차**로 사이징한다. 대표
   패턴 — replica-bias/전류거울 네트워크: 이미 사이징된 메인 경로 소자를 레퍼런스로 삼아,
   같은 gm/ID(트래킹이 목적이면 기본 선택) 또는 의도적으로 다른 gm/ID(그 근거를 명시)를
   고르고, 미러비(면적·전력 트레이드오프로 설계자가 정하는 자유변수)를 정해 사이징한다.
4. 이 추론으로도 정말 로컬 스펙이 안 나오면(드문 경우), "범위 제외"가 아니라 **"이 값을
   확정하려면 다음 정보가 필요하다"**고 구체적 질문으로 명시한다.

### 수동 보상소자(Cc, Rz, pole/zero 관련 R/C)

신호 경로 소자의 gm/ID 사이징이 끝나면, **그 결과 gm 값을 그대로 넣어 보상소자 값을 계산하는
것까지가 같은 설계 흐름의 마지막 단계**다 — 별도 영역이 아니다. `gm-id-methodology.md`
§6.4/§6.7/§10에 이미 있는 표준 공식(예: 널링저항 R≈1/gm2)을 실제로 적용한다. 어느 topology에
어느 공식을 쓸지는 `references/function-selection-map.md` §2를 확인하고, 그 표에 없는
조합이면 `topology-fn-derivation-guide.md`의 패턴대로 새로 유도해 `topology_library.py`에
추가한다 — "이 값을 계산하는 전용 함수가 아직 없다"는 것도 스킵 근거가 되지 못한다.

### 순수 비-gm/ID 영역과의 구분

Pole-zero placement로 결정되는 R/C 자체는 위처럼 gm/ID 사이징의 연장선에서 확정한다. 이
skill이 다루지 않는 것은 **트랜지스터 gm/ID와 무관한 완전히 다른 설계 영역**(정확한 ESD/
guard-ring 폭, foundry DRC 규칙 등 PDK 매뉴얼 영역)뿐이다 — 이런 항목만 별도로 명시하고,
"트랜지스터인데 스킵"하는 일은 없어야 한다.

### topology library JSON이 있으면 그것부터 확인

이 회로의 topology가 `assets/library/*.topology.json`에 이미 있으면(예: folded_cascode,
two_stage_ota), connectivity/matching kind/위상보정 함수 참조를 그 파일에서 로드해 재사용한다
— 매번 스키매틱을 다시 해석하지 않는다. `function-selection-map.md` §10 참고
(`load_topology()`/`run_topology_pipeline()`). 새 topology라면 `library/_TEMPLATE.topology.json`
에서 시작해 같은 §10 절차를 따른다.

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

### 2.1 gm/ID 사이징이 물리적으로 막힐 때의 판단 기준

nA 이하 초저전류 회로를 사이징하다 보면 "이 gm/ID로는 W가 말이 안 되게 나온다"는 상황을
만난다. 재시행착오 없이 바로 판단하기 위한 세 가지 기준:

1. **정방향 sizing이 비현실적 W를 낼 때는 방향을 뒤집는다** — W를 매칭/공정 최소선 기준의
   현실적 값으로 먼저 고정하고, 그 W와 목표 ID에서 결과 gm/ID를 역산한다(함수는
   `function-selection-map.md` §1 참고).
2. **선형 전류거울 스케일링이 막히면(비율이 극단적) 지수적/직렬 분할 기법으로 전환**한다 —
   서로 다른 W/L비를 가진 소자를 직렬로 강제 동일 전류를 흘려 생기는 ΔVGS를 다음 단 게이트에
   되먹여 지수적으로 줄인다. **이 메커니즘의 실제 ΔVGS는 이상적 EKV 공식과 실측이 크게
   벌어질 수 있으므로 반드시 SPICE로 직접 확인**하고 공식값을 그대로 쓰지 않는다.
3. **gm/ID 목표가 LUT 특성화 상한을 넘으면 그 지점부터는 모델이 답을 줄 수 있는 범위 밖이다.**
   이 skill의 sky130 LUT 실측 상한은 NMOS 29.93 / PMOS 32.20 S/A(`sky130-worked-example.md`
   §4) — 새 공정/LUT에서는 재확인할 것. 상한을 살짝 넘는 목표가 나오면 1번 기준대로 W를
   현실적 값으로 고정하고 gm/ID를 결과로 받아들인다.

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
| Miller Op-Amp(2단 OTA) | 같은 문서 §6.4, §6.7 | pole splitting, RHP zero, **2D sizing space**(qF1, qF2)에서 등전력/등면적 contour로 절충, 이득식 기반 L 역산(§6.7). 보상소자(Cc/Rz) 실값 산출은 §1.5 참고 |
| **3-stage OTA(NGCC/NMC)** | 같은 문서 §10 | 2단으로 이득·전력 스펙을 못 맞출 때. NGCC 닫힌형태 sizing(k, ω1/ω2/ω3, Cm1/Cm2), RHP-zero 완전제거(NMCNR, §10.4) |
| Distortion/Linearity 스펙이 있는 단 | 같은 문서 §11 | HD2/HD3을 gm/ID의 5번째 설계곡선으로 취급 — 왜곡 스펙에서 gm/ID를 역산 |
| RF 블록(LNA 등) | 같은 문서 §12 | baseband sizing 위에 매칭망·NF·richer noise 층이 추가됨(코어 방법론은 동일) |
| Bias generator / replica-bias / CMFB 네트워크 | §1.5 | 명시적 목표치가 없어도 기능적 역할로부터 로컬 타겟 유도 — "범위 밖" 처리 금지 |

각 회로의 구체 sizing 방정식·MATLAB 발췌·수치 예제는 위 문서에서 재서술 없이 그대로 참조한다.
실제 호출 함수는 `references/function-selection-map.md` §2 참고.

⚠️ **Deep-submicron(L≲130nm)이면 §9(Deep-submicron 한계)를 먼저 읽는다** — gm/ID가 VDS·L에도
의존하게 되어 위 표의 기본 절차에 VDS를 4번째 sizing 축으로 추가해야 할 수 있다.

---

## 5. 검증 체크리스트 (Definition of Done)

- [ ] **준정적 확인**: `f_nqs = gm/(2π·Cgg)` 계산, `fT ≤ 0.1·f_nqs` 성립하는가?
- [ ] **이득 확인**: `A = (gm/ID)·VA` 목표 스펙 만족하는가? (Early 전압 VA는 weak inversion에서만
      게이트전압 무관 — "VA가 항상 한 점으로 수렴한다"는 가정 금지 [→references §2.5])
- [ ] **Slew-rate 확인**: `slew-rate = ID/C = ωT/(gm/ID)` — 정현파 조건 만족하는가?
- [ ] **Matching**: 정전류원/전류거울/차동쌍이 충분히 strong 방향인가(weak inversion mismatch 민감)?
      "이게 current mirror인가"는 항상 게이트 net 공유 여부로 판단한다(`function-selection-map.md` §3).
- [ ] **Noise**: 1/f 저감을 위한 면적 확대가 doublet 주파수를 fT 근처로 끌어내리지 않았는가?
- [ ] **기생 수렴**: §1 스텝 5의 반복이 실제로 수렴했는가(W 급증 후 재상승 패턴 확인)?
- [ ] **Distortion**(왜곡 스펙이 있으면): HD2/HD3를 gm/ID의 함수로 확인했는가 [→references §11]?
- [ ] **Deep-submicron**(L≲130nm이면): VDS를 4번째 sizing 축으로 다뤘는가, VA(VDS) 의존성을 무시하지
      않았는가 [→references §9]?
- [ ] **모든 소자(능동+수동)가 확정된 값을 가졌는가**(§1.5) — "범위 밖"으로 남긴 트랜지스터나
      보상소자가 있다면 그건 §1.5 위반이다.
- [ ] 고급 시뮬레이터(SPICE/Spectre)로 최종 미세조정했는가 — gm/ID sizing은 출발점이지 최종값이 아니다.
- [ ] **여러 소자가 얽힌 폐루프(2단 이상 OTA, CMFB 등) SPICE 검증 시, 소자별로 분해해서
      풀었는가**(전체를 한 번에 자기일관되게 풀려고 시도하지 않았는가) — 절차는
      `references/spice-verification-workflow.md` §1.
- [ ] **LUT를 SPICE와 직접 대조할 때, IDu를 SPICE 전류와 곧바로 비교하지 않고 올바른 절차를
      따랐는가** — 절차는 `references/spice-verification-workflow.md` §2.
- [ ] **리포트 §5(완성된 stick diagram)의 데이터가 `build_stick_diagram()`의 실제 반환값
      그대로인가**(손으로 축약·재구성하지 않았는가 — §6 참고).
- [ ] **`run_full_circuit_audit()`(sizing 시작 전 선언한 `expected_counts` 매니페스트 +
      정본 connectivity dict 1벌 + `dispositions` 판정 전부를 인자로) 를 호출해 `AuditResult.
      ok == True`를 확인했는가** — 소자 수 대조(§3↔§5 커버리지 + 소스 대비 총 개수), net 이름
      대소문자 정규화, 전체 목록 기준 `current_mirror`/`diff_pair`/hub-merge 후보 전수 판정,
      sub-block별 box-shape를 이 **한 번의 호출**로 전부 확인한다. **하지 말 것**: sub-block별로
      나눠 국부 재확인, 고친 항목만 재확인 — 무언가 고쳤다면 전체를 처음부터 다시 실행한다
      (근거는 `design-report-spec.md` §1.6).
- [ ] **`check_stick_diagram_coverage(sized_device_names, stick_diagram_devices)`를
      `run_full_circuit_audit()`와 별도로 호출해 `.ok == True`를 확인했는가** —
      `run_full_circuit_audit()`는 자신에게 전달된 `devices` dict **안에서만** 커버리지를
      보므로, sub-block 하나가 그 dict 자체에서 통째로 빠지면(예: 사이징은 했지만 stick
      diagram 호출을 아예 안 함) 잡지 못한다. **하지 말 것**: `sized_device_names`를
      `run_full_circuit_audit()`에 넘긴 것과 같은 dict에서 재사용(같은 누락이 반복됨) —
      §3 sizing 표에서 독립적으로 뽑을 것. **하지 말 것**: 두 게이트를 import만 하고 실제
      호출부 없이 완료 보고 — 보고 전 `grep -n "run_full_circuit_audit(\|
      check_stick_diagram_coverage("`으로 호출부 존재를 직접 확인할 것.

- [ ] **⭐ [skill 최종 게이트 — 이 항목만 다른 항목들과 성격이 다르다: 매 설계 1회가
      아니라, 이 skill의 harness 함수 집합이 수정되거나 확장될 때마다(새 함수 추가,
      기존 함수 시그니처 변경, 새 topology_fn 등록 등) 반드시 재검사한다. 절대 원칙
      5번(위)이 이 항목을 가리킨다]** **spec → instance.json 전체 workflow가 harness
      함수(및 그 함수가 호출하는 원소 함수)만으로 완주되고, 그 결과가 재현 가능하며,
      주어진 spec하에서 최선임이 보장되는가?** 세 가지를 전부 확인해야 통과다:
  - **(a) harness-only 구성**: 이 경로의 어느 단계도 "harness/원소 함수에 없어서 AI가
        즉석 코드/로직을 새로 만들어 채운" 지점이 없는가? 하나라도 있으면 "함수 우선순위
        대원칙"(위) 위반이다 — 그 자리를 임시로 손으로 메우고 넘어가지 말고, 새 harness/
        원소 함수로 승격해 이 skill에 정식 등록할 것.
  - **(b) 재현성**: 같은 topology.json + design_spec을 다시 넣고 처음부터 다시 실행했을
        때, 완전히 동일한 결과(sizing/floorplan/instance.json)가 나오는가? 재현이 안
        되면 어딘가 비결정적 선택(순서 의존, 시드 없는 난수, 사람의 그때그때 판단 등)이
        경로에 숨어있다는 뜻 — 그 지점을 찾아 결정론적 규칙(또는 명시적 정책 파라미터)으로
        바꿀 것.
  - **(c) 최적성**: 그 결과가 주어진 spec(`objective`/`constraints`)하에서 최선임이
        보장되는가? D유형 탐색(`optimize_full_circuit_budget()`류)이 실제로 objective를
        최소/최대화하는 θ*에 수렴했는지 확인하고, 탐색 없이 임의로 고른 첫 feasible
        후보로 멈추지 않았는지 확인할 것.
  - **검증 절차**: `docs/04-report/*.do.md`의 최종 시나리오 감사 절(예:
        `analog-topology-json-library.do.md` §10)과 같은 방식 — spec 하나를 실제로
        골라 topology.json부터 instance.json까지 **실제 함수 호출로**(이상적으로는 진짜
        실행, 최소한 실제 함수 시그니처 대조 기반 단계별 추적) 끝까지 따라가며 위 (a)(b)(c)를
        확인한다. 이 절차가 실제로 gap을 찾아낸 전례가 있다(2026-07-31, raw W→
        n_fingers/finger_w/stack_id 자동배정 함수 부재 — 절대 원칙 5번의 계기).

---

## 6. Layout 단계: Stick Diagram/Euler Trail ↔ Sizing 피드백 루프

> 정본: `references/stick-diagram-euler-layout.md`. §5 검증을 통과한 sizing이라도 물리
> layout(finger 수·stack 배치·상호연결)으로 옮기는 순간 또 다른 제약이 드러난다 — 이 절은
> 그 제약을 다시 sizing으로 되먹이는 워크플로우다. §1~§5(회로 sizing)가 끝나야 시작되는
> **후속 단계**이지, §1~§5를 대체하지 않는다.

```
[§1~§5 sizing 완료] → [stack 분할 + Euler trail 판정 = stick diagram 배치]
        │                                   │
        │                          check_euler_condition() PASS(홀수차수 노드 0/2개)?
        │                                   │
        │                                  YES
        │                                   ▼
        │              ⚠️ 여기서 바로 SPICE로 가지 말 것 — box-shape 게이트가 남아있다
        │                                   ▼
        │              [check_box_shape() 게이트 — 반드시 SPICE 이전에 실행]
        │                                   │
        │                  FAIL → search_stack_finger_w()/search_shared_finger_w()로
        │                         finger_w·행 구성 재탐색(§8), 그래도 안 되면 §8.5 계산
        │                                   │
        │                                   ▼
        │              [§5 검증 체크리스트 재실행 — finger_w가 바뀌었으므로 필수]
        │
     check_box_shape() PASS
        │
        ▼
   ⚠️ 비율 PASS ≠ PDK가 그 finger_w를 실제로 만들 수 있다는 보장(§8.4) — SPICE 인스턴스화 확인
        │
        ▼
   [matching-symmetry 확인 — check_mirror_symmetry(), Euler trail 존재와는 별개(§2.5.3)]
        │
        ▼
   [stage-경계 병합 확인 — find_hub_merge_candidates(), stack_id 배정 전에 실행(§4.1)]
        │
        ▼
   이 W로 freeze → SPICE 재검증(finger_w가 LUT 기준폭에서 벗어났다면 §8.3 방식으로
   실측 재보정) → 물리 layout(finger 배치+interconnect) 진행
```

이 흐름의 각 게이트가 왜 순서대로 필수인지, 어긴 사고 경위는 `references/known-incidents.md`
와 `stick-diagram-euler-layout.md` §8/§10에 있다 — 여기서 재서술하지 않는다. 실제 호출 함수는
`references/function-selection-map.md` §3~§6에서 상황별로 찾는다. topology가 `library/*.
topology.json`으로 등록돼 있으면 `run_topology_pipeline(topology_json_path, sizing_overrides)`
가 이 흐름(box-shape/matching-safety/floorplan/coverage)을 한 번에 실행한다 — 단, row 분할은
자동 탐색하지 않으므로 `audit_row_split` FAIL 시 `search_stack_finger_w()`/
`common_centroid_layout()`로 재조정하는 건 여전히 직접 해야 한다(§10 참고).

**요지**: 되먹임되는 "결과"는 gm/ID 재계산값이 아니라 stick diagram으로 실제 배치해본 뒤에야
드러나는 layout 판정이다. 이 판정이 문제를 지적하면 비-critical branch의 W를 조정하고,
**조정된 W는 반드시 §5 체크리스트로 재검증**한 뒤에만 확정한다. 재검증을 통과해 **freeze**된
이후에만 실제 finger 배치·metal 상호연결 단계로 넘어간다.

Worked example(Folded Cascode 등): `stick-diagram-euler-layout.md` §6. 이 절의 산출물은
회로에 종속되지 않는 일반 코드 `assets/stick_diagram.py`로 실제로 계산한다.

---

## 7. 최종 산출물 — 설계 리포트(HTML) 규격

> 정본: `references/design-report-spec.md`. §1~§6(sizing + layout 피드백 루프)이 끝나면
> **반드시** 아래 8개 섹션을 모두 담은 HTML 문서 하나를 산출물로 생성한다 — 사람이 브라우저로
> 읽을 수 있고, 동시에 다른 agent가 파일을 그대로 `Read`해서 이해할 수 있어야 한다.

⚠️ **HTML을 쓰기 시작하기 전에 `design-report-spec.md`의 PRE-FLIGHT 절을 반드시 먼저 읽는다**
— 검증을 다 했다는 것과 그 검증의 실제 근거(데이터도, 시각화 코드도)를 리포트에 그대로
옮겼다는 것은 별개다.

| # | 섹션 | 생성 소스 |
|---|---|---|
| 1 | 주어진 topology(스키매틱, 원문 이미지 캡처 금지 — 직접 그린 원본만) | `report_template.html`의 `renderSchematic()` 코드 그대로 재사용 |
| 2 | 주어진 설계 spec | 사용자/논문 원문 그대로 |
| 3 | 결정된 gm/ID parameter(**§1.5에 따라 모든 소자 포함, 능동+수동**) | §1 6단계 출력 |
| 4 | stick diagram을 위한 결정사항(matching 탐지, stage-merge, Case A/B, box-shape 탐색) | `stick_diagram.py` 결정 추적 |
| 5 | 완성된 stick diagram(실제 Euler trail) — **§3에서 사이징된 소자 전부가 등장해야 함** | `build_stick_diagram()`(데이터) + `report_template.html`의 `renderStack()`(시각화, 코드 그대로 재사용) + `check_stick_diagram_coverage()`(§3↔§5 소자 집합 대조, PASS 확인 필수) |
| 6 | 스냅된 W로 재검증한 SPICE 결과가 원 스펙을 만족하는지 | SPICE 재시뮬레이션 + §5 체크리스트 재적용 |
| 7 | Layout 실행 agent를 위한 가이드 — 이 회로의 실제 소자/net 이름으로 성능-critical 요소를 지목 | `design-report-spec.md` §2 체크리스트 |
| 8 | **물리 floorplan(필수)** — 전체 회로(모든 sub-block 포함)를 실제 2D packing한 결과(bbox/aspect/packing_density), 빈 공간 없는 실제 배치임을 시각적으로 확인 가능해야 함. "나중에/선택적으로"로 미루지 말 것 | `pack_floorplan_grouped()`(§8) + `run_full_circuit_audit()`(ALL PASS 확인) — topology가 `library/*.topology.json`으로 등록돼 있으면 `run_topology_pipeline()`이 이 계산까지 담당(`function-selection-map.md` §10) |

8개 섹션 중 하나라도 빠지면(특히 §1.5를 어기고 일부 소자를 "범위 밖"으로 남긴 경우) 산출물
미완성으로 간주한다. 자세한 체크리스트는 `design-report-spec.md` §2. 완료 보고 전 §5의
`run_full_circuit_audit()`/`check_stick_diagram_coverage()` 게이트가 **실제로 호출**됐는지
재확인할 것 — import만 하고 호출부가 없는 것도 실패다(§5 참고).

**형식**: 시각 렌더링(사람용) + 같은 파일 안 `<script>` JS 객체 리터럴(agent용, 렌더링이 이
객체에서 파생되므로 두 층이 어긋날 수 없음) 이중 구조. 템플릿: `assets/report_template.html`.

⚠️ **이 skill의 모든 산출물은 완료 보고 전에 반드시 시각 검증한다** — Artifact 배포는 시각
검증을 가능하게 하는 수단이지 그 자체가 목적이 아니다. 문법적으로 유효한 데이터 구조라도 실제
렌더링에서 겹침/overflow/배선 끊김이 생길 수 있다. 검증 없이 "생성 완료"라고 보고하지 말 것
(자세한 절차는 `design-report-spec.md` §4).

---

## 참조 파일

- **`references/function-selection-map.md`** — **"이 상황엔 이 함수" 정본.** §0에 harness
  (오케스트레이션) 함수 5개 목록, §1~§10에 세 스크립트(`sizing_recipe.py`/`stick_diagram.py`/
  `topology_library.py`)의 나머지 함수를 상황별로 매핑한다. 함수 로직을 재서술하지 않는다 —
  어느 함수를 호출해야 하는지만 안내한다. **판단이 안 서면 먼저 §0(harness)부터 확인할 것.**
- `references/known-incidents.md` — SKILL.md 절대 원칙 각각의 전체 사고 경위(무엇이 왜
  틀렸는지, 어떻게 발견됐는지).
- `references/consistency-map.md` — 원칙별 SKILL.md 섹션↔reference 반영 위치 맵, 이 skill
  고유 마커 규약(`[→§X]`는 SKILL.md가 아니라 `gm-id-methodology.md`를 가리킴). SKILL.md 수정
  시 `../skill-validation-prompt.md` 절차로 재검증하고 이 맵의 변경 이력에 기록한다.
- `references/design-report-spec.md` — §7 정본. 8개 섹션 정의, PRE-FLIGHT 체크리스트, 시각
  검증 절차.
- `assets/report_template.html` — §7 규격을 구현한 완전한 템플릿. 새 리포트는 이 파일을 복사해
  데이터만 교체한다 — 렌더링 함수를 다시 쓰지 않는다.
- `references/gm-id-methodology.md` — 방법론 전체(핵심 변수·관계식·LUT 생성·설계 절차·
  트레이드오프·worked example·noise/matching·§9 deep-submicron 한계·§10 3-stage OTA·§11
  distortion·§12 RF·보상소자 표준식). **정본** — 이 SKILL.md의 모든 수식·절차 근거.
- `references/lut-generation-checklist.md` — 공정별 gm/ID 차트 생성용 SPICE/Spectre 스윕
  체크리스트 + 실전 보간 알고리즘.
- `references/spice-verification-workflow.md` — §5의 "폐루프 SPICE 수렴 워크플로우"와
  "LUT↔SPICE 교차검증 절차" 정본.
- `assets/sizing_recipe.py` — §1 6단계 sizing 방정식 구현. 함수별 사용 상황은
  `function-selection-map.md` §1.
- `assets/topology_library.py` — 반복 사용되는 토폴로지의 `topology_fn`/보상소자 함수 모음.
  함수별 사용 상황·검증 상태는 `function-selection-map.md` §2. 새 토폴로지 추가 전 반드시
  `references/topology-fn-derivation-guide.md` §1을 먼저 읽는다.
- `references/topology-fn-derivation-guide.md` — 새 `topology_fn`(및 보상소자 함수)을
  추가하기 전에 먼저 읽을 문서. 논문의 위상보상 방정식을 "스펙 → gm_i" 닫힌해로 역산하는
  일반 절차와, 기존 토폴로지들의 실제 유도 과정을 기록한다.
- `references/topology-behavior-diagnosis-workflow.md` — SPICE 결과가 설계식/원문 예측과
  질적으로 다를 때(노치·예상 밖 극점/영점 등) 따를 일반 진단 절차(8단계).
- `references/stick-diagram-euler-layout.md` — §6의 정본. Stick diagram, Euler trail
  그래프화, stack 분할, sizing↔layout 피드백 루프, cell shape(box) 판단 기준, 병합/대칭성
  검증까지 전부 포함.
- `assets/stick_diagram.py` — §6의 회로-무관 구현. 함수별 사용 상황은
  `function-selection-map.md` §3~§6.
- `assets/library/*.topology.json` — 이미 등록된 topology의 connectivity+matching+위상보정
  참조 정본. 재사이징해도 재사용 가능 — 새로 만들지 말고 먼저 확인할 것.
  로드/파이프라인 함수는 `function-selection-map.md` §10, 새 topology 작성 절차는
  `docs/02-design/features/analog-topology-json-library.design.md` §4.5.
- `references/topology-extraction-checklist.md` — **스펙/회로도 이미지에서 topology.json
  자체를 처음 만들 때** 따를 절차(위 항목의 "이미 있는 topology를 사이징"과는 다른 문제).
  실제 오독 사고 5건(Fig.4 오인, Vop 12개 누락, 극성 오류 등, `current_reuse_telescopic_ota`
  작성 중 발생) 기반 — Stage 0(원문 완전성)~Stage 3(선택적 인간 확인) 체크리스트. **topology.json을
  새로 만들거나 connectivity를 고칠 때마다 `assets/topology_to_markdown.py <json경로>`를
  실행해 net별/소자별 connectivity 표를 `<name>.topology.md`로 저장하고 세션에도 출력해
  사람이 재확인하는 게 필수 절차다**(§5) — 이미지/PDF 판독만으로는 dense한 회로도의
  connectivity를 신뢰성 있게 재현 못 한다는 게 실측으로 재확인됨(2026-08-03).
- `references/sky130-worked-example.md` + `assets/sky130_lut_sweep.py` +
  `assets/sky130_nfet_pfet_lut_sample.npz` — 실리콘 검증 사례(SkyWater sky130 + SPICE 시뮬레이터).
  LUT 실측 gm/ID 상한(§4), LUT↔SPICE 정규화 함정(§3) 포함.

## Cross-Skill 참조

- Sizing 결과를 behavioral 모델로 미리 검증(수렴성·연속성) → `verilog-a` skill
- AMS 검증환경(듀얼탑, Spectre 연동)에 이 sizing 결과를 실제 회로로 배치 → `chip-verification` skill
- `find_matching_candidates()`의 current_mirror/diff_pair 오탐(§2.6, 실사고: M57/M58 —
  gate만 보고 source를 안 봐서 diode 체인을 진짜 매칭쌍으로 오판; M11/MN — 우연히 같은
  source+W를 가진 무관한 소자가 diff_pair로 오판)을 device role 기반으로 재검증 →
  `analog-grammar` skill(netlist에서 gate/source/drain 연결성만으로 role을 결정론적으로
  도출). `find_idiom_matches()`/`find_stack_edges()`/`find_stacked_matching_candidates()`
  로 연동 구현 완료(2026-08-06, opt-in — 안 쓰면 기존 동작 그대로). 설계 근거·역할
  매핑표: `references/analog-grammar-integration.md`
