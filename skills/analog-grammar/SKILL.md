---
name: analog-grammar
description: |
  회로 netlist가 주어졌을 때 device role을 배정하고 topology의 기능을 구조적으로
  분석하는 skill. 다음 상황에서 사용:
  (1) netlist에서 각 소자의 역할 판정 — cascode, current source, active load,
      amplifying, source follower, switch, diode-connected
  (2) net 분류 — supply/ground/bias/signal/clock/feedback, 임피던스 등급
  (3) L1 idiom 인식 — differential pair, current mirror, cascode stack,
      push-pull output, floating battery, current-reuse pair
  (4) signal flow graph 구성, 이득단 수 판정, feedback loop 검출
  (5) topology 기능 가설 생성 및 논문 주장과의 대조
  (6) 다른 skill(analog-gmid-design)의 matching 후보 탐지 결과(current_mirror/
      diff_pair)가 진짜인지 구조적으로 재검증 — role 기반 오탐 필터
  트리거: device role, 소자 역할, topology 분석, 회로 기능 분석, netlist 분석,
  idiom 인식, signal flow, 이득단, cascode 판정, 회로 구조 파악, current mirror 진위,
  diode stack, floating battery, matching 오탐
---

# Analog Grammar — topology 기능 분석

netlist에서 device role과 회로 기능을 **구조적으로** 도출한다.

> 정본: `references/DESIGN.md`(설계 근거·경계선·6단계 파이프라인 전체·Fig.2/Fig.3
> 실증 사례). 이 SKILL.md는 재서술하지 않고 절차·판단 지점만 안내한다.

## 절대 규칙

### 1. LLM에게 "이 회로가 뭐냐"고 먼저 묻지 않는다

netlist를 보고 바로 "current-reuse telescopic OTA구나"라고 답하는 것은
**분석이 아니라 회상**이다. 익숙한 topology의 형태를 알아보고 교과서 답을
채워 넣는 것이며, 세 곳에서 조용히 실패한다.

- **변형된 topology** — 논문의 기여는 대개 canonical에서 한두 개 비틀린
  부분인데, 그게 정확히 회상이 지워버리는 부분이다
- **틀린 netlist** — 추출 오류가 있어도 "그럴듯한 회로"로 읽어내 은폐한다
- **재현성 없음** — 대량 파이프라인에서 측정이 불가능해진다

**반드시 `assets/analyze.py`를 먼저 돌리고, 그 시그니처를 해석하는 역할만 한다.**
[→DESIGN.md §1]

### 2. ASSUMPTIONS 절을 절대 생략하지 않는다

잘린 도면에서 **INPUT과 BIAS는 구조적으로 구별되지 않는다.** 둘 다
"게이트에만 연결된 외부 넷"이라 그래프상 동일하다. 스크립트는 이름 힌트로
추정하고 그 사실을 전부 출력한다. 사용자에게 보고할 때 이 가정을 반드시
같이 전달하고, 가능하면 `--inputs` / `--bias`로 선언하도록 유도한다. [→DESIGN.md §1]

### 3. UNRESOLVED와 낮은 coverage는 상류를 의심하는 신호다

이 단계에서 억지로 맞추지 않는다. Stage 2의 `UNRESOLVED` role이나 Stage 4의
낮은 coverage는 대개 **netlist 자체가 잘못됐다는 지표**다.
실제 사례: Fig.3의 `push-pull-output` 미검출은 상류 추출기가 수동소자를
지원하지 않아 소스 노드가 잘못 잡힌 결과였다. [→DESIGN.md §4]

## 워크플로

> Windows에서 콘솔이 cp949(기본 코드페이지)면 한글/em-dash 출력에서
> `UnicodeEncodeError`가 난다. `PYTHONUTF8=1 python assets/analyze.py ...`처럼
> 환경변수를 앞에 붙이거나 `set PYTHONUTF8=1`을 먼저 실행할 것(2026-08-06 반입 시
> 이 저장소 환경에서 실측 확인).

```bash
# 기본 (이름 힌트로 추정)
python3 assets/analyze.py netlist.json

# 가정을 사실로 승격 (권장)
python3 assets/analyze.py netlist.json \
    --inputs Vip,Vim --feedback Vcmfb --outputs Vom1,Vop1

# 후속 처리용 JSON
python3 assets/analyze.py netlist.json --inputs Vip,Vim --json result.json
```

입력 형식:
```json
{"devices":[{"name":"M1a","type":"PMOS","D":"n1","G":"Vip","S":"Vx"}, ...]}
```
`circuit-topology-extraction` skill의 `schematic_extract.py` 출력과 동일하다.

## 파이프라인 (6단계)

| Stage | 하는 일 | 파일 | 성격 |
|---|---|---|---|
| 1 | net 분류 + 임피던스 등급 | `assets/netclass.py` | 결정론적 (1c만 힌트 의존) |
| 2 | device role 배정 | `assets/netclass.py` | **완전** 결정론적 |
| 3 | L1 idiom 매칭 + 겹침 해소 | `assets/idioms.py` | 결정론적 |
| 4 | 계층 축약 (supernode) | `assets/idioms.py` | 결정론적 |
| 5 | signal flow graph + loop 검출 | `assets/sfg.py` | 결정론적 |
| 6a | 구조 시그니처 | `assets/sfg.py` | 결정론적 |
| 6b | 기능 서술 | `assets/sfg.py` + **LLM** | 규칙 + 판단 |

상세는 `references/DESIGN.md` §3.

## LLM이 담당하는 것 (Stage 6b 이후)

`analyze.py`가 마지막에 명시하는 4가지에만 개입한다.

1. **시그니처에 해당하는 문헌상의 정확한 topology 명칭**
   구조 시그니처는 코드가 만든다. 그걸 "folded cascode"인지 "telescopic"인지
   문헌 용어로 옮기는 것이 LLM 역할이다. 근거(시그니처)를 반드시 함께 인용한다.
2. **라이브러리에 없는 신규 idiom의 명명 및 등록 제안**
   coverage가 낮고 미축약 소자가 구조적으로 뭉쳐 있으면 새 idiom 후보다.
   `@idiom(name, priority)` 함수 초안을 제안한다.
3. **겹쳐 탈락한 매칭 중 '의도된 해석' 판단**
   maximum-coverage 근사가 항상 옳지는 않다. 탈락 목록을 보고 재해석을 제안한다.
4. **미축약 소자가 왜 남았는지 설명**

## 새 idiom 추가

`assets/idioms.py`에 함수 하나:

```python
@idiom('my-idiom', priority=5)
def m_my_idiom(devs, cls, imp, role):
    out = []
    # devs: [{'name','type','D','G','S'}]
    # cls:  net -> SUPPLY|GROUND|INPUT|OUTPUT|SIGNAL|BIAS|FEEDBACK|CLOCK|INTERNAL
    # imp:  net -> HIGH_Z|LOW_Z|RAIL
    # role: device -> DIODE_CONNECTED|CURRENT_SOURCE|CASCODE|AMPLIFYING|...
    return out  # [Match(kind, devices, ports, note, priority)]
```

priority는 **더 특수한 패턴일수록 높게**. 겹침 해소에서 우선한다.
(예: `current-reuse-pair`(9)가 `differential-pair`(5) 2개를 흡수)

**추가할 때마다 `assets/examples/`의 기존 예제로 회귀 테스트를 돌린다**
(`assets/run_example.sh`).

## 보고 형식

사용자에게 보고할 때 반드시 포함:

1. **ASSUMPTIONS** — 어떤 추정을 썼는지. 생략 금지.
2. device role 표 (name / type / role / D / G / S)
3. 검출된 idiom과 coverage
4. gain stages, 정방향 경로와 극성, feedback loop
5. 기능 가설 — **[확정: 구조에서 결정론적으로 도출]** 과
   **[추정: LLM 해석]** 을 명확히 분리
6. UNRESOLVED / 낮은 coverage가 있으면 상류 netlist 재검토 권고

## 알려진 한계

- **수동소자(R/C/L) 미지원** — Miller 보상, RC 필터, SC 회로 미인식
- **folded vs telescopic 미구별** — 이득 노드 형태만 판정, 전류 가지 분기 미분석
- **switched-capacitor** — SWITCH role은 있으나 clock phase별 그래프 분리 미구현
- **L2 block 미인식** — Stage 4 출력을 다시 Stage 3에 넣는 재귀는 미구현
- **입력 스키마가 `Transistor` dataclass가 아니라 평면 dict** — `analog-gmid-design`의
  `stick_diagram.Transistor`를 이 skill의 `{"name","type","D","G","S"}` 형식으로
  변환하는 어댑터가 필요하다(해당 skill의 `references/analog-grammar-integration.md`
  참고, 이 skill 자체는 변환 코드를 갖지 않는다 — 호출하는 쪽의 책임).

## 참조 파일

- `references/DESIGN.md` — **정본.** 설계 근거(AI가 이미 할 수 있는 일을 그대로
  쓰면 안 되는 이유), 아날로그 조합 문법(L0~L3 계층), 6단계 파이프라인 상세,
  Fig.2/Fig.3 실증 결과, 로컬 완성 과제, 이 프로젝트로 반입된 경위.
- `references/consistency-map.md` — 원칙별 SKILL.md 섹션↔`DESIGN.md` 반영 위치 맵.
  SKILL.md 수정 시 `skill-validation-prompt.md` 절차로 재검증한다.
- `assets/netclass.py` — Stage 1(net 분류) + Stage 2(device role 배정).
- `assets/idioms.py` — Stage 3(L1 idiom 매칭) + Stage 4(계층 축약). `REGISTRY`에
  `@idiom` 데코레이터로 등록된 11개 idiom 함수.
- `assets/sfg.py` — Stage 5(signal flow graph) + Stage 6(구조 시그니처/기능 가설).
- `assets/analyze.py` — 6단계 파이프라인을 순서대로 실행하는 CLI 러너. 사람이 읽을
  텍스트 리포트 + `--json`으로 후속 처리용 구조화 출력을 낸다.
- `assets/examples/fig2_telescopic.json` / `fig3_classab.json` — 회귀 테스트용 예제.
  Fig.2는 `analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json`과
  **같은 회로**다(DESIGN.md §4 참고) — 두 skill의 결과를 대조하는 용도로도 쓸 수 있다.
- `assets/run_example.sh` — 두 예제를 순서대로 재현하는 스크립트.

## Cross-Skill 참조

- 논문 PDF의 회로도에서 이 skill이 받는 netlist 입력을 직접 추출 →
  `circuit-topology-extraction` skill(별도 반입 예정, 아직 이 저장소에 없음).
- gm/ID 사이징 harness가 이 skill의 role/idiom 판정 함수(특히 `current-mirror`의
  gate+source 그룹핑)를 matching 후보 오탐 필터로 재사용하는 연동 설계 →
  `analog-gmid-design` skill의 `references/analog-grammar-integration.md`.
