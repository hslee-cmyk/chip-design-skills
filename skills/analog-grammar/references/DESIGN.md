# Analog Grammar — 설계개념

> Topology(netlist)가 주어졌을 때 device role을 배정하고 전체 기능을 분석하는
> 파이프라인. `circuit-topology-extraction`(추출)의 하류 단계이며 독립적으로 쓸 수 있다.

---

## 1. 먼저 답해야 할 질문 — AI가 원래 이걸 할 수 있나?

**할 수 있다. 그런데 그 능력을 그대로 쓰면 안 된다.**

Fig.2의 netlist를 그대로 주면 어떤 강력한 모델이든 "current-reuse telescopic
OTA, M1a/M1b는 PMOS 입력쌍, M2a/M2b는 cascode"라고 정확히 답한다.
문제는 그게 **분석이 아니라 회상**이라는 것이다. 익숙한 topology의 형태를
알아보고 교과서 답을 채워 넣는 것이며, 다음 세 곳에서 조용히 실패한다.

| 실패 지점 | 왜 |
|---|---|
| **변형된 topology** | 논문의 기여는 대개 canonical에서 한두 개 비틀린 부분인데, 그게 정확히 회상이 지워버리는 부분 |
| **틀린 netlist** | 추출이 잘못돼도 "그럴듯한 회로"로 읽어내 오류를 은폐한다 |
| **재현성** | 수천 편 파이프라인에서 같은 입력에 같은 출력이 안 나온다 |

세 번째가 특히 치명적이다. 데이터셋을 만드는 작업이면 결정론성이 없는 순간
"측정"이 불가능해진다.

### 경계선

| 판정 | 담당 | 근거 |
|---|---|---|
| Net 분류 | **코드** | DC 경로 전파 — 결정론적 |
| Device role 배정 | **코드** | net class가 주어지면 **완전** 결정론적 |
| Idiom 매칭 | **코드** | subgraph isomorphism |
| 계층 축약 / SFG / loop 검출 | **코드** | 그래프 연산 |
| 겹치는 매칭 중 "의도된 해석" | LLM 보조 | maximum-coverage 근사로 1차 처리 후 잔여만 |
| 라이브러리에 없는 새 idiom 명명 | **LLM** | 정의상 규칙이 없음 |
| 구조 시그니처 → 사람이 읽을 서술 | **LLM** | 문헌 명칭 매핑 |
| 검사 실패 원인 설명 | **LLM** | 진단·소통 |

**핵심: net 분류만 되면 role 배정과 idiom 매칭은 전부 결정론적으로 떨어진다.**
자동화 비율은 실측 기준 대략 85~90%가 코드, 나머지가 LLM.

### 구조적으로 판정 불가능한 단 하나

> **잘린 도면에서 INPUT과 BIAS는 구별되지 않는다.**
> 둘 다 "게이트에만 연결된 외부 넷"이라 그래프상 완전히 동일하다.

해결 수단은 셋뿐이다: (1) 이름 힌트, (2) 사용자 선언, (3) 전체 netlist를 병합해
바이어스 넷이 diode-connected 기준 소자까지 추적되는지 확인.

`analyze.py`는 기본적으로 (1)을 쓰고 **적용한 가정을 전부 ASSUMPTIONS 절에
출력**한다. `--inputs`로 선언하면 가정이 사실로 승격된다. 이 구분을 절대
흐리지 않는 것이 이 설계의 안전장치다.

---

## 2. 아날로그 조합 문법

아날로그 회로에는 실재하는 조합 문법이 있고, 이 문제는 본질적으로
**digital synthesis의 technology mapping과 같다** — cell library를 놓고
subgraph isomorphism으로 매칭하는 것.

```
L0 primitive  MOS, R, C, L, diode
L1 idiom      current mirror(simple/cascode/Wilson/low-voltage), differential pair,
              source follower, CS w/ active load, cascode, level shifter,
              Miller cap, class-AB output, switch, bootstrapped switch,
              chopper, latch, DEM, floating battery, current-reuse pair
              → 30~50개면 실무 회로의 대부분을 덮는다
L2 block      OTA(5T/telescopic/folded/two-stage), bandgap, LDO, S/H,
              integrator, VCO, PFD/CP, DAC unit cell
L3 system     ADC(SAR/ΔΣ/pipeline), PLL, PMIC
```

### 현재 구현된 L1 (11종)

| idiom | priority | 판정 근거 |
|---|---|---|
| `current-reuse-pair` | 9 | 상보형 차동쌍 2조가 동일 입력 게이트 공유 |
| `cascoded-gain-node` | 8 | HIGH_Z 노드에 상보형 cascode 드레인 대향 |
| `push-pull-output` | 6 | 상보 쌍이 출력 노드 공유, 게이트 분리=class-AB |
| `differential-pair` | 5 | 같은 tail(비레일), 서로 다른 게이트, 둘 다 AMPLIFYING |
| `floating-battery` | 5 | diode-connected 직렬쌍 |
| `current-mirror` | 4 | 게이트·소스 공통 + 하나는 diode-connected |
| `cascode-stack` | 4 | 동일 타입 직렬, 상단 role=CASCODE |
| `source-follower` | 3 | 드레인이 레일, 게이트가 신호 |
| `tail-current-source` | 2 | 차동쌍 tail 노드를 구동하는 전류원 |
| `active-load` | 2 | 게이트 BIAS, 소스 레일, 드레인이 HIGH_Z |
| `diode-connected` | 1 | G == D |

priority가 높을수록 더 **특수한** 패턴이며 겹침 해소에서 우선한다.
`current-reuse-pair`가 `differential-pair` 2개를 흡수하는 식이다.

**주의 — `current-mirror`는 gate뿐 아니라 source까지 같은 그룹으로 묶는다**
(`idioms.py`의 `grp[(d['G'], d['S'], d['type'])]`). gate만 같고 source가
다른 소자쌍(예: diode 체인의 직렬 멤버끼리)은 이 idiom에 잡히지 않는다 —
"진짜 VGS가 같은 미러인가"를 구조적으로 보장하기 위한 설계다.

### 왜 YAML DSL을 안 썼나

아날로그 idiom은 "role 조건 + 넷 클래스 조건 + 그래프 형태"의 조합이라
선언형으로 짜면 금세 표현력이 부족해진다. 반쪽짜리 DSL은 파이썬보다 읽기
어렵다. 대신 `@idiom(name, priority)` 데코레이터 하나로 등록하는 레지스트리를
썼다. 새 idiom 추가는 함수 하나다.

---

## 3. 6단계 파이프라인

각 단계마다 검증 가능한 invariant를 둔다.
UVM의 reference model + scoreboard를 단계별로 놓는 것과 같은 구조다.

```
[1] Net 분류                      netclass.classify_nets()
    1a 전원 레일 (이름)
    1b 사용자 선언 (최우선)
    1c 게이트 전용 외부 넷 → BIAS/INPUT/FEEDBACK/CLOCK   ★유일한 판정 불가 지점★
    1d 신호 정방향 전파
         g∈signal, D≠rail        → D 가 신호 (반전 gm)
         g∈signal, D=rail        → S 가 신호 (source follower)
         S∈signal, g=BIAS        → D 가 신호 (cascode current buffer)
    1e 출력 추정 (이름 힌트)
    1e2 남은 '게이트 구동 내부 넷' → 능동 드레인 구동이면 SIGNAL, diode면 BIAS
    1f 임피던스 등급
         드레인만 모인 노드      → HIGH_Z (이득 노드)
         소스가 붙은 노드        → LOW_Z
    ↓ invariant: 모든 넷이 정확히 하나의 클래스

[2] Device role 배정              netclass.assign_roles()
    판정 순서 (위가 더 특수)
      G == D                                   → DIODE_CONNECTED
      G class = CLOCK                          → SWITCH
      G class ∈ {SIGNAL,INPUT,OUTPUT}
          D = rail                             → SOURCE_FOLLOWER
          else                                 → AMPLIFYING
      G class = FEEDBACK                       → CONTROLLED_CURRENT_SOURCE
      G class = BIAS
          S = rail, D 가 HIGH_Z                → ACTIVE_LOAD
          S = rail, 그 외                      → CURRENT_SOURCE
          S = 내부 노드                        → CASCODE
    ↓ invariant: UNRESOLVED 0개

[3] Idiom 매칭                    idioms.match_all() / resolve_overlaps()
    전체 idiom 실행 후 maximum-coverage 근사로 겹침 해소
    (priority 내림차순 → 소자 수 내림차순 탐욕 선택, 단일 소자 idiom은 항상 유지)
    ↓ invariant: coverage ≥ 임계값. 낮으면 라이브러리 부족 또는 netlist 오류

[4] 계층 축약                     idioms.contract()
    매칭된 idiom을 port를 가진 supernode로 contract
    ↓ invariant: 미축약 소자가 설명 가능

[5] Signal flow graph             sfg.build_sfg()
    방향성 엣지
      gate → drain   반전 transconductance
      gate → source  비반전 (follower)
      source → drain current buffer (cascode)
    정방향 경로 열거 + cycle 검출로 feedback loop 식별
    ↓ invariant: 입력→출력 경로 ≥ 1

[6] 기능 가설                     sfg.structural_signature() / hypothesise()
    6a 구조 시그니처 — 여기까지가 코드의 책임          ★결정론적★
       이득단 수 / 차동 여부 / 출력 임피던스 / idiom 집합 /
       정방향 경로와 극성 / 루프와 극성 / role 맵
    6b 규칙 기반 서술 + LLM 잔여 과제 명시
    ↓ invariant: 본문 주장과 모순되지 않음
```

**설계상 가장 중요한 결정**: Stage 6을 6a(시그니처)와 6b(서술)로 쪼갠 것.
시그니처가 근거이고 서술은 표현일 뿐이므로, 서술이 틀려도 시그니처로
되짚을 수 있다. LLM은 6b에만 개입한다.

---

## 4. 실증 — Fig.2 (current-reuse telescopic) 자동 분석 결과

입력은 11소자 netlist뿐이다. **도메인 지식 입력 0.**

```
STAGE 2 — device roles
  M6   PMOS  CURRENT_SOURCE              M1a  PMOS  AMPLIFYING
  M7   PMOS  CONTROLLED_CURRENT_SOURCE   M2a  PMOS  CASCODE
  M5   NMOS  CURRENT_SOURCE              M3a  NMOS  CASCODE
                                         M4a  NMOS  AMPLIFYING

STAGE 3 — idiom matching
  [9] current-reuse-pair    M1a+M1b+M4a+M4b   inp=Vip inm=Vim tail_hi=Vx tail_lo=Vy
  [8] cascoded-gain-node    M2a+M3a           node=Vom1
  [8] cascoded-gain-node    M2b+M3b           node=Vop1
  [2] tail-current-source   M7  gate=Vcmfb    (CMFB 제어)
  coverage = 1.00

STAGE 5 — signal flow
  gain nodes : ['Vom1','Vop1']   gain stages : 1   output Z : HIGH_Z
  Vip -> n1 -> Vom1  (반전)      <- PMOS 경로
  Vip -> n2 -> Vom1  (반전)      <- NMOS 경로, 같은 출력 노드로 합류

STAGE 6 — functional hypothesis
  - fully differential
  - current-reuse 입력단 (gm_eff = gmn + gmp)
  - cascode 이득 노드 (telescopic 또는 folded)
  - CM 또는 전역 귀환 존재 (Vcmfb)
  - 단일 이득단 / transconductance 출력 (OTA 계열)
```

주목할 것:

1. **논문의 실제 기여인 current-reuse가 구조만으로 자동 검출됐다.**
   canonical telescopic과 겉모습이 비슷해서, "아는 회로"로 회상했으면
   바로 이 차이가 지워졌을 지점이다.
2. **SFG에 그 메커니즘이 그대로 나타난다** — `Vip→n1→Vom1`(PMOS)과
   `Vip→n2→Vom1`(NMOS)이 같은 출력 노드로 합류하는 두 병렬 gm 경로.
3. **CMFB가 role 수준에서 구별됐다** — M6는 `CURRENT_SOURCE`,
   M7은 `CONTROLLED_CURRENT_SOURCE`. 논문 본문의 "M6는 tail 전류원, M7은
   피드백 트랜지스터"와 일치한다.

이 예제는 이 프로젝트가 `analog-gmid-design/library/current_reuse_telescopic_
ota.topology.json`에서 실제로 사이징하고 있는 **바로 그 회로**다 — `assets/
examples/fig2_telescopic.json`으로 그대로 보존돼 있으며, 두 결과(이 skill의
Stage 2 role 배정 vs 그 topology.json의 `device_roles`)를 서로 대조하는
용도로도 쓸 수 있다(`analog-gmid-design/references/analog-grammar-integration.md`
참고).

### Fig.3 (Class-AB) — 부분 성공, 그리고 그것이 유용한 이유

`floating-battery`(class-AB의 magic battery) 2조를 정확히 검출했다.
그러나 `push-pull-output`은 매칭되지 않는다. 원인은 이 단계가 아니라
**상류 추출기가 수동소자(Cc, Rz)를 지원하지 않아 M16의 소스가 GND 대신
내부 노드 n5로 잘못 잡혀 있기 때문**이다.

→ **Stage 3의 coverage 저하가 상류 netlist 오류의 지표로 작동한다.**
이것이 단계별 invariant를 두는 이유다.

---

## 5. 로컬에서 완성해야 할 것

| # | 항목 | 난이도 | 비고 |
|---|---|---|---|
| 1 | 수동소자(R/C/L) 지원 | 중 | 상류 추출기 + `Miller-compensation` idiom |
| 2 | folded vs telescopic 구별 | 중 | Stage 5에서 전류 가지 분기 검출 필요 |
| 3 | L1 라이브러리 30~50종으로 확장 | 소 (반복) | idiom 함수 하나씩 |
| 4 | switched-capacitor: clock phase별 그래프 분리 | 상 | SWITCH role은 이미 있음 |
| 5 | Stage 6b LLM 프롬프트 정형화 | 소 | 시그니처 JSON → 서술 |
| 6 | golden set 기반 role/idiom 정확도 측정 | 중 | 이게 없으면 개선 여부 판정 불가 |
| 7 | L2 block 인식 (축약 그래프 위 2차 매칭) | 중 | Stage 4 출력을 다시 Stage 3에 |

특히 **7번이 이 설계의 자연스러운 확장**이다. Stage 4가 supernode 그래프를
내놓으므로, 같은 매칭 엔진을 한 번 더 돌리면 L2 블록(OTA, bandgap 등)이
나온다. 재귀 구조로 만들면 코드 추가 없이 계층이 올라간다.

---

## 6. 사용 원칙

1. **LLM에게 "이 회로가 뭐냐"고 먼저 묻지 않는다.** 반드시 `analyze.py`를
   먼저 돌리고, LLM은 그 시그니처를 해석하는 역할만 한다.
2. **ASSUMPTIONS 절이 비어 있지 않으면 그 아래는 전부 조건부다.**
   `--inputs` 등으로 선언해 가정을 줄인다.
3. **UNRESOLVED role이나 낮은 coverage는 상류 netlist를 의심한다.**
   이 단계에서 억지로 맞추지 않는다.
4. **새 idiom을 추가할 때마다 기존 예제로 회귀 테스트를 돌린다.**
   (추출 단계에서 이걸 안 해서 조용히 깨진 적이 있다)

---

## 7. 이 프로젝트로 반입된 경위 (2026-08-06)

이 skill은 원래 독립적으로 만들어진 "아날로그 기능분석기.zip" 패키지를
`chip-design-skills` 저장소의 skill 관리 컨벤션(SKILL.md +
`skill-validation-prompt.md` + `references/`, 다른 5개 skill과 동일 구조)에
맞춰 반입한 것이다. 반입 당시 이미 `analog-gmid-design`(gm/ID 사이징) skill이
`stick_diagram.py`의 `find_matching_candidates()`(현재 gate만 보고 current_mirror
판정)에서 실제 오탐 사고(M57/M58이 한때 진짜 매칭쌍으로 잘못 disposed됨,
`analog-topology-json-library` 세션18 기록)를 겪은 뒤였고, 이 skill의
`idioms.m_mirror()`가 gate+source+type을 함께 보는 더 엄격한 판정을 이미
갖고 있다는 게 반입을 결정한 핵심 근거였다. harness와의 실제 연동 설계는
`analog-gmid-design/references/analog-grammar-integration.md`에 있다 — 이
문서(DESIGN.md)는 이 skill 자체의 설계만 다루고, 다른 skill과의 연동은
다루지 않는다.
