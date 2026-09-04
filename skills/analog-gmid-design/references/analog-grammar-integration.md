# analog-grammar 연동 설계 — matching 후보 오탐 필터

> 상태: **§6(Tier 1) 구현 완료, self-test(Test 30) 전체 PASS, 아직 미커밋.**
> `stick_diagram.py`에 `find_idiom_matches()`/`find_stack_edges()`/
> `find_stacked_matching_candidates()` 신설 + `find_matching_candidates()`에
> `idiom_matches` 파라미터 추가(하위호환, self-test로 확인). §7의 Tier 2
> (`find_diode_stacks()` 배선)는 실측으로 "적용 불가"로 결론 — 구현 안 함.
> `sizing_recipe.py`는 이번 배치에서 변경하지 않음(이 함수들을 실제 harness
> 호출부에 배선하는 건 아직 다음 단계).

## 0. 배경

`find_matching_candidates()`(`stick_diagram.py`)는 두 종류의 **문서화된** 구조적
오탐을 갖고 있다.

1. **current_mirror**: `(kind, gate)`로만 그룹핑한다 — source는 안 본다. 실사고: 2026-07-29
   `M57`/`M58`이 `current_mirror/pmos/Vbias_p`로 잘못 disposed됐다가 2026-08-03 diode-chain
   false-positive임을 발견해 정정(`analog-topology-json-library.do.md` 세션18 K/L절).
2. **diff_pair**: `(kind, source, w)`로 그룹핑하고 gate가 다른 것만 남긴다 — W가 없는
   topology-authoring 단계에서는 W 필터가 무력화된다. 실사고: `M11`/`MN`(둘 다
   `source=gnd`, 같은 `W=16`, 서로 다른 gate)이 diff_pair 후보로 오탐됨
   (`stick-diagram-euler-layout.md` §2.6, self-test Test 6이 이미 이 사례를 회귀
   대조로 갖고 있다).

세션18에서 "`find_matching_candidates()`의 `current_mirror`에 source-일치 조건을
추가할지"를 설계하려던 차에, 별도로 반입된 `analog-grammar` skill(`idioms.py`의
`m_mirror()`)이 정확히 이 조건(`(G, S, type)` 그룹핑 + diode-connected 레퍼런스 요구)을
이미 구현해 갖고 있다는 게 발견돼 — 재구현 대신 이 skill의 role 분류를 재사용하는
쪽으로 설계를 확정한다.

**이 문서 작성 중 재확인된 사실(설계를 바꾼 근거)**: `find_diode_stacks()`도 이미
이 프로젝트에 구현돼 있다(2026-07-30 정정, `stick_diagram.py:1369`) — 세션18이
"미배선"이라고 부른 건 "아직 없는 함수"가 아니라 "구현은 됐지만 self-test에서만
불리고 `find_hub_merge_candidates()`/`find_matching_candidates()`에 실제로 연결은
안 된 함수"였다. 이 함수는 **이미 M57/M58 사고를 계기로 재작성**됐고(자기 자신의
docstring이 이 사고를 직접 인용), `stack_id`가 이미 배정된 물리 스택 안에서 "gate가
자기 자신이든 이웃이든 어떤 소자의 drain을 가리키는가"를 그래프 워크로 찾는다 —
`analog-grammar`의 `DIODE_CONNECTED`(단순 `G==D` 자기참조)보다 **더 정밀**하다.
따라서 이번 설계는 **새 diode-stack 탐지기를 만들지 않는다** — 이미 있는
`find_diode_stacks()`를 그대로 쓴다.

## 1. 두 계층으로 문제를 다시 나눈다

이 프로젝트의 matching 관련 함수는 파이프라인상 서로 다른 두 시점에서 돈다.

| 계층 | 시점 | 함수 | `stack_id` 필요? |
|---|---|---|---|
| **Tier 1 — topology 저작 단계** | 사이징 전, W도 stack_id도 없음(`function-selection-map.md` §3 "사이징 전에도 diff_pair 후보를 낸다") | `find_matching_candidates()` | 아니오 — connectivity(gate/source/drain)만 있으면 됨 |
| **Tier 2 — layout 단계** | `split_into_stacks()` 이후, 물리 stack이 이미 확정 | `find_hub_merge_candidates()`, `find_diode_stacks()` | 예 |

`find_diode_stacks()`는 **stack_id가 있어야만** 동작한다(내부에서 `t.stack_id`로
그룹핑) — 그래서 Tier 1(아직 stack이 없는 시점)의 `find_matching_candidates()`에는
애초에 이 함수를 직접 넣을 수 없다. 반대로 `analog-grammar`의 `assign_roles()`는
gate/source/drain 연결성만 있으면 되므로(§2 참고) **Tier 1에 정확히 맞는 도구**다.
즉 두 도구는 경쟁하지 않고 서로 다른 단계를 메운다:

- **Tier 1 (이번 설계 범위)**: `find_matching_candidates()` + `analog-grammar` role →
  current_mirror/diff_pair 오탐 필터.
- **Tier 2 (이미 알려진 후속 과제, 이번 범위 아님)**: `find_diode_stacks()` →
  `find_hub_merge_candidates()` 배선. 자기 자신의 docstring이 이미 이 배선을
  제안하고 있지만(§7.3.2 콜아웃), **어떤 구체적 실패 사례를 막는지 아직 실측으로
  확인된 바 없다** — §2.6(위 사고1/2)와 달리 재현된 오탐 사례가 없으므로, 상상으로
  설계를 채우지 않고 실제 실패 사례가 나오면 그때 설계한다(§7 참고).

## 2. current_mirror 오탐(M57/M58)의 정확한 원인 재확인

세션18 기록(`M58.source=Vx, M58.drain=N58_57` / `M57.source=N58_57, M57.gate=M57.drain=
Vbias2`)과 "게이트가 자기 자신의 drain에 물린 M57은 self-diode, M58은 M57의 drain(=Vbias2)에
물려 같은 gate=Vbias2를 공유"라는 사실을 조합하면:

- **gate**: M57=M58=`Vbias2` — **같다** → 옛 `(kind, gate)` 그룹핑이 왜 둘을 묶었는지 설명됨.
- **source**: M57=`N58_57`, M58=`Vx` — **다르다** → `(kind, gate, source)`로 그룹핑하면
  이 시점에 이미 서로 다른 그룹으로 갈라진다.
- **diode 멤버 요구만으로는 이 사고를 못 막는다**: M57 자신이 self-diode(`G==D`)이므로
  `role[M57]=="DIODE_CONNECTED"`는 참 — "그룹에 diode 멤버가 있는가"만 검사하면 이
  그룹은 여전히 통과한다. **이 사고를 실제로 막는 건 source를 그룹핑 키에 넣는 것
  하나뿐**이다.

즉 아래 2절의 두 조건(source 그룹핑 / diode 멤버 요구)은 **서로 다른 오탐 클래스를
막는다** — source 그룹핑은 M57/M58류(같은 gate, 다른 source)를, diode 멤버 요구는
"diode 레퍼런스가 아예 없는데 우연히 같은 gate를 공유하는 소자쌍"류(아직 이
프로젝트에서 실사고로 확인된 바는 없음, 방어적으로 추가)를 막는다. 둘 다 넣되,
어느 게 어떤 사고를 막는지는 self-test에서 각각 별도로 검증한다(§6).

## 3. Cross-skill import 메커니즘

`run_harness.py`가 이미 쓰는 패턴(`sys.path.insert()` + bare-name import, `.ai/
context.md` 확인됨)을 그대로 따르되, `stick_diagram.py` 자신은 라이브러리이므로
import-time에 sys.path를 건드리지 않는다 — 호출 시점에 **optional import**로 감싼다.

```python
def classify_device_roles(transistors: list, inputs=(), outputs=(),
                            feedbacks=(), biases=(), clocks=()) -> dict | None:
    """analog-grammar skill(netclass.py)을 이용해 gate/source/drain 연결성만으로
    device role을 배정한다. analog-grammar가 sys.path에 없으면(다른 skill이라 설치
    여부가 이 스크립트 실행 환경에 좌우됨) None을 반환한다 — 호출자는 None이면 이
    보강 기능 없이 기존 동작(role=None)으로 폴백해야 한다. 절대 예외를 삼키고 조용히
    "판정 없음"으로 넘어가지 않는다 — ImportError만 잡고 다른 예외는 그대로 던진다."""
    import sys, os
    _ag_path = os.path.join(os.path.dirname(__file__), "..", "..", "analog-grammar", "assets")
    _ag_path = os.path.normpath(_ag_path)
    if _ag_path not in sys.path:
        sys.path.insert(0, _ag_path)
    try:
        from netclass import classify_nets, assign_roles
    except ImportError:
        return None

    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return None
    cls, imp, _assume = classify_nets(devs, inputs, outputs, biases, feedbacks, clocks)
    return assign_roles(devs, cls, imp)
```

`analog-gmid-design/assets`에서 `../../analog-grammar/assets`로의 상대경로는 두
skill이 같은 저장소의 `skills/` 최상위에 나란히 있다는 전제(현재 실제 구조와 일치)에
의존한다 — 저장소 밖에서 `analog-gmid-design/assets`만 따로 복사해 쓰는 경우엔
자동으로 `None`이 되어 조용히 하위호환 경로로 빠진다(의도된 동작).

## 4. 어댑터: `Transistor` → analog-grammar `devs` dict

```python
def _to_analog_grammar_devs(transistors: list) -> list:
    """gate가 없는 소자는 제외한다 — analog-grammar의 net 분류는 모든 소자가 G/D/S
    셋 다 갖고 있다고 가정한다(terminals()가 'DGS'를 무조건 순회). 이 프로젝트의
    Transistor.gate는 원래 선택 필드(§2.6 matching 탐지 전용)라 None인 소자가 흔하다
    — 이런 소자는 애초에 이 함수가 강화하려는 current_mirror/diff_pair 판정 대상도
    아니므로 제외해도 손실이 없다."""
    return [{"name": t.name, "type": t.kind.upper(), "D": t.drain, "G": t.gate, "S": t.source}
            for t in transistors if t.gate is not None]
```

## 5. `classify_device_roles()`/`find_idiom_matches()`에 topology.json의 `ports`를
   힌트로 넘긴다

> `find_idiom_matches()`(§6.1)도 내부적으로 Stage 1(`classify_nets()`)을 그대로
> 거치므로, 이 절의 `inputs`/`outputs` 힌트는 두 함수 모두에 동일하게 적용된다 —
> 아래는 `classify_device_roles()` 예시지만 `find_idiom_matches()` 호출도 같은
> 인자를 그대로 받는다.

`analog-grammar` 자신이 "잘린 도면에서 INPUT/BIAS는 구조적으로 구별 불가 — 이름
힌트 또는 사용자 선언 필요"라고 명시한다(DESIGN.md §1). 이 프로젝트의
`topology.json`은 이미 `ports`(예: `current_reuse_telescopic_ota`의 `Vip`/`Vim`
`direction:"input"`, `Vom`/`Vop` `direction:"output"`)를 갖고 있으므로, 이름 힌트에
의존하지 않고 **선언을 그대로 승격**할 수 있다:

```python
ports = topo["ports"]  # load_topology()가 이미 파싱하는 그 dict
role = classify_device_roles(
    transistors,
    inputs=[n for n, p in ports.items() if p.get("direction") == "input"],
    outputs=[n for n, p in ports.items() if p.get("direction") == "output"],
)
```

`Vcmfb`류 내부 feedback net은 `ports`에 없는 경우가 흔하므로(1차 포트만 선언)
`analog-grammar`의 이름 힌트(`HINT_FB` 정규식이 `cmfb`를 이미 잡는다)로 폴백된다 —
이건 이 skill의 기존 동작 그대로이고, ASSUMPTIONS 절로 그 사실이 드러난다(원한다면
이 프로젝트 쪽에서 `feedbacks=`로 명시할 수도 있으나 이번 설계 범위는 아니다).

## 6. `find_matching_candidates()` 확장 — role이 아니라 idiom Match를 직접 재사용
   (2026-08-06 재설계, 사용자 제안)

### 6.0 왜 role 필터 대신 Match를 직접 쓰는가

처음 설계(§6 구버전, 아래 6.4에 보존)는 `classify_device_roles()`(Stage 1~2만)의
`role`을 갖고 옛 그룹핑에 사후 필터를 얹는 방식이었다. 그런데 `analog-grammar`의
Stage 3(`idioms.match_all()`)는 **role보다 한 단계 더 응집된 정보**를 이미 갖고
있다 — `m_mirror()`/`m_diffpair()` 내부에서 이미 "그룹 안에 diode-connected 멤버가
있는가"(current-mirror), "둘 다 role=AMPLIFYING인가"(differential-pair)를 직접
검사해서 `Match` 객체를 낸다. 즉 **role 필터가 하려던 일을 idiom 함수가 이미
정확히 하고 있다** — role을 별도로 다시 필터링할 필요 없이 `Match.devices`를
그대로 후보로 채택하면 된다. 6.4의 role 필터 설계는 이걸로 대체되어 폐기한다.

### 6.1 새 어댑터 — `find_idiom_matches()` (Stage 1~3, `classify_device_roles()`와 별개)

```python
def find_idiom_matches(transistors: list, inputs=(), outputs=(), feedbacks=(),
                         biases=(), clocks=()) -> list | None:
    """analog-grammar skill(Stage 1 net 분류 + Stage 2 role 배정 + Stage 3 idiom 매칭)을
    한 번에 실행해 **겹침 해소 이전**의 원본 Match 리스트를 반환한다. 겹침 해소
    (resolve_overlaps())는 Stage 4(계층 축약/보고용 요약)를 위한 것이지 matching-pair
    후보 생성과는 무관하다 — 예를 들어 current-reuse-pair(priority 9)가 그 아래
    differential-pair 2개를 흡수해도, 실제 W/L 매칭이 필요한 단위는 여전히 원래의
    두 쌍(M1a/M1b, M4a/M4b)이지 4소자 뭉치가 아니다. analog-grammar가 sys.path에
    없으면 None(호출자는 find_matching_candidates(transistors, idiom_matches=None)으로
    폴백)."""
    import sys, os
    _ag_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..",
                                                "analog-grammar", "assets"))
    if _ag_path not in sys.path:
        sys.path.insert(0, _ag_path)
    try:
        from netclass import classify_nets, assign_roles
        from idioms import match_all
    except ImportError:
        return None

    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return None
    cls, imp, _assume = classify_nets(devs, inputs, outputs, biases, feedbacks, clocks)
    role = assign_roles(devs, cls, imp)
    return match_all(devs, cls, imp, role)
```

`classify_device_roles()`(§5)는 그대로 남긴다 — role만 필요한 다른 용도(§8의
오라클 교차검증)에는 여전히 Stage 1~2만으로 충분하고 더 가볍다. `find_idiom_
matches()`는 Tier 1 matching 후보 생성 전용의 별도 어댑터다(내부적으로 role도
계산하지만 반환하지 않는다 — 필요하면 `match_all()` 호출 전에 role을 별도로 뽑는
변형도 가능하나, 지금은 Tier 1에 필요한 것만 최소로 반환).

### 6.2 `find_matching_candidates()` 확장

```python
def find_matching_candidates(transistors: list, idiom_matches: list | None = None) -> dict:
    ...(기존 docstring에 아래 단락 추가)...
    idiom_matches가 주어지면(`find_idiom_matches()`의 반환값) current_mirror/diff_pair
    후보를 옛 net-only 그룹핑 대신 그 Match 리스트에서 직접 뽑는다 — `m_mirror()`가
    이미 "gate+source 공유 + diode-connected 레퍼런스 존재"를, `m_diffpair()`가 이미
    "source 공유 + gate 상이 + 둘 다 AMPLIFYING"을 검증했으므로 이 함수는 이름 변환만
    한다. idiom_matches=None(기본값)이면 기존 동작과 완전히 동일하다(바이트 단위,
    self-test로 확인).

    ⚠️ current-mirror Match 하나가 3개 이상의 소자(레퍼런스 1 + 미러 출력 N개)를
    가리킬 수 있다 — 옛 (kind,gate) 그룹핑과 마찬가지로 그룹 전체를 그대로 후보로
    낸다(2개로 쪼개지 않음).
    """
    if idiom_matches is not None:
        by_name = {t.name: t for t in transistors}
        current_mirror, diff_pair = {}, {}
        for m in idiom_matches:
            group = [by_name[n] for n in m.devices if n in by_name]
            if m.kind == "current-mirror" and len(group) >= 2:
                key = (group[0].kind, m.ports["bias"], m.ports["rail"])
                current_mirror[key] = group
            elif m.kind == "differential-pair" and len(group) == 2:
                key = (group[0].kind, m.ports["tail"])
                diff_pair[key] = group
        return {"current_mirror": current_mirror, "diff_pair": diff_pair}

    # idiom_matches=None -- 기존 동작 그대로(아래 원본 코드 무변경)
    by_gate = defaultdict(list)
    by_source = defaultdict(list)
    for t in transistors:
        if t.gate is not None:
            by_gate[(t.kind, t.gate)].append(t)
        by_source[(t.kind, t.source, t.w)].append(t)

    current_mirror = {k: v for k, v in by_gate.items() if len(v) >= 2}
    diff_pair = {}
    for (kind, source, w), group in by_source.items():
        if len(group) != 2:
            continue
        if group[0].gate is not None and group[1].gate is not None and group[0].gate != group[1].gate:
            diff_pair[(kind, source)] = group

    return {"current_mirror": current_mirror, "diff_pair": diff_pair}
```

**`role` 파라미터는 이 설계에서 완전히 빠진다** — 아직 아무 코드도 커밋되지 않은
설계안이라 하위호환을 지킬 대상이 없다(§6.4 구버전은 폐기, 재도입하지 않음).

### 6.3 ⚠️ 새로 발견된 커버리지 갭 — "캐스코드 대칭쌍"이 사라진다(결정 필요)

이 재설계 도중 발견한, **구현 전 반드시 결정해야 하는 사항**이다.

`stick-diagram-euler-layout.md` §2.6 카탈로그는 캐스코드 대칭쌍(예: `M2a`/`M2b` —
같은 극성 + 같은 gate + **서로 다른** source/drain net)을 "✅ gate 공유 기준으로는
걸리지만, 캐스코드 역할이라는 의미까지는 자동 판별 못함"이라고 이미 정직하게
기록해뒀다 — 즉 **옛 `(kind, gate)`만 보는 그룹핑이 우연히 잡아주고 있었다.**

`M2a`/`M2b`의 실제 connectivity로 직접 확인: `M2a(G=Vbias2,S=n1)`/`M2b(G=Vbias2,
S=n3)` — gate는 같지만 **source가 다르다.** `m_mirror()`의 `(G,S,type)` 그룹핑은
source가 다르면 애초에 다른 그룹으로 갈라놓으므로, **이 재설계 이후 `M2a`/`M2b`는
current_mirror 후보로도, `analog-grammar`의 어떤 기존 idiom(`differential-pair`는
같은 source를 요구, `cascoded-gain-node`는 이 둘이 아니라 `M2a`+`M3a`처럼 출력
노드에서 만나는 수직쌍을 잡음)으로도 전혀 안 잡힌다.** §2 재확인과 동일한
원리(source 그룹핑이 M57/M58을 걸러낸 것)가 이번엔 의도치 않게 `M2a`/`M2b`류까지
같이 걸러낸 것이다.

**실제 손실 범위는 제한적이다**: `M2a`/`M2b`는 이미 `current_reuse_telescopic_ota.
topology.json`의 `symmetry.matching_pairs`에 **사람이 직접 선언해둔 상태**다
(`{"names":["M2a","M2b"],"matching_sensitivity":"ratio",...}`, branch_symmetric로
이미 재분류된 이력까지 있음) — 그러니 **이번 회로가 당장 깨지는 건 아니다.** 문제는
**다음 새 회로를 저작할 때** 이 자동탐지가 캐스코드 대칭쌍을 더 이상 후보로
제시하지 않게 된다는 것 — `function-selection-map.md` §10이 "topology JSON 저작
단계에서도 이 함수 그대로 쓸 것"이라고 명시한 그 용도가 이 카테고리에서는 약해진다.

**선택지 4(사용자 제안, 실측으로 확인 — 채택)**: "복합소자(composite)" 개념 —
세션16/17의 branch composite(`_branch_composite_pair()`, `kcl_series_union()`
기반, **레이아웃** crossover 짝짓기용)와 **정확히 같은 직렬 스택 개념을 반대
방향(매칭 후보 **발견**)으로 적용**한다. 이미 확정/발견된 매칭쌍 위에 직접 stacked된
소자쌍은, 그 자체의 gate/source 패턴이 아니라 **"이미 확정된 쌍 위에 대칭으로
얹혀 있다"는 구조적 근거**로 매칭 후보임을 추론한다.

`analog-grammar`의 `netclass.stack_edges(devs)`(role/net분류 불필요, 순수
connectivity — "X.source==Y.drain이면 Y 위에 X가 얹혀 있다")를 이 회로의 실제
`load_topology()` 결과에 직접 돌려 확인:
```
M1a 위에 직접 stacked: M2a (net N1a2a)     M4a 위에 직접 stacked: M3a (net N3a4a)
M1b 위에 직접 stacked: M2b (net N1b2b)     M4b 위에 직접 stacked: M3b (net N3b4b)
```
`{M1a,M1b}`(확정된 differential-pair)의 stack 위에 `{M2a,M2b}`가, `{M4a,M4b}`
위에 `{M3a,M3b}`가 정확히 대응한다 — **§2.6이 기록해둔 두 캐스코드 대칭쌍 사례
전부 이 메커니즘 하나로 재현된다.** M57/M58처럼 확정된 쌍 위에 얹혀 있지 않은
소자는 이 경로로 아예 끌려오지 않으므로 회귀 위험도 없다.

```python
def find_stacked_matching_candidates(transistors: list, base_pairs: list,
                                       stack_edges: list) -> dict:
    """이미 확정/발견된 매칭쌍(base_pairs: [(name_a, name_b), ...] -- diff_pair/
    current_mirror Match든, topology.json의 symmetry.matching_pairs든 호출자가
    아무거나 seed로 넘길 수 있다) 위에 직접 stacked된 소자쌍을 재귀적으로(2단 이상
    캐스코드 대비) 찾아 매칭 후보로 낸다. stack_edges: analog-grammar netclass.
    stack_edges(devs)의 반환값 [(lower, upper, node), ...] 그대로.

    반환: {(kind, lower_a, lower_b): [Transistor, Transistor], ...} -- 키의 마지막
    두 요소는 이 후보를 낳은 바로 아래 단(base) 소자 이름(추적/디버깅용)."""
    by_lower = {lo: up for lo, up, _node in stack_edges}
    kind_of = {t.name: t.kind for t in transistors}
    by_name = {t.name: t for t in transistors}
    out, frontier, seen = {}, list(base_pairs), set()
    while frontier:
        a, b = frontier.pop()
        if (a, b) in seen:
            continue
        seen.add((a, b))
        ua, ub = by_lower.get(a), by_lower.get(b)
        if ua is None or ub is None or kind_of.get(ua) != kind_of.get(ub):
            continue
        out[(kind_of[ua], a, b)] = [by_name[ua], by_name[ub]]
        frontier.append((ua, ub))
    return out
```

`stack_edges`는 이 함수 시그니처에서 순수 인자로 받는다(analog-grammar import를
이 함수 자신은 하지 않음) — 호출자가 §6.1의 `find_idiom_matches()`를 이미
호출했다면 같은 어댑터에서 `netclass.stack_edges(devs)`도 한 번 더 뽑아 넘기면
된다(추가 sys.path 조작 불필요, 이미 로드된 모듈 재사용).

`base_pairs`는 `find_matching_candidates()`의 `diff_pair`/`current_mirror` 결과
에서 뽑거나, `symmetry.matching_pairs`(이미 사람이 확정한 것)에서 뽑을 수도 있다
— 후자를 쓰면 "아직 미확정인 자동탐지 후보"가 아니라 "이미 확정된 사실"에서만
전파하므로 더 보수적이다. 이번 회로(`current_reuse_telescopic_ota`)는 결과가
같다(diff_pair 자동탐지와 matching_pairs 선언이 이미 일치) — 두 소스가 갈리는
회로가 생기면 그때 어느 쪽을 기본으로 할지 재논의.

### 6.4 (폐기) role 필터 기반 구버전 설계 — §6.0의 이유로 대체됨, 기록용으로만 보존

<details>
이전 설계는 `classify_device_roles()`의 role만으로 옛 net-그룹핑에 사후 필터를
얹었다: current_mirror는 `(kind,gate,source)`로 재그룹핑 후 DIODE_CONNECTED 멤버
요구, diff_pair는 두 멤버 다 AMPLIFYING 요구. §6.0에서 설명한 대로 이건 `idioms.
match_all()`이 내부적으로 이미 하는 검사를 이 프로젝트 쪽에서 다시 구현한 것이라
중복이었다 — Match를 직접 쓰는 §6.1~6.2로 대체한다.
</details>

## 7. 이번 설계에 포함하지 않는 것 (후속 과제로 명시)

- **`find_diode_stacks()` → `find_hub_merge_candidates()` 배선 — 확인 결과 적용
  불가로 결론(§1 최초 가설과 다름, 실측으로 정정)**: `find_diode_stacks()`가 찾는
  diode-stack의 "내부 연결 net"은 정의상 한쪽 소자의 drain 하나 + 다른 소자의
  source 하나만 닿아 있다. `find_hub_merge_candidates()`는 source끼리/drain끼리
  **역할을 나눠** 그룹핑하므로, 이런 net은 각 역할별로 항상 크기 1이라 애초에
  2개 이상 후보 조건을 절대 못 채운다(`current_reuse_telescopic_ota`의 diode-stack
  전부 — `N11a11b`/`N58_57`/`N64_63`/`N20a20b` 등 — 를 실제로 뽑아 확인, 예외
  없음). 즉 두 함수를 이어붙여도 원래 기대했던 필터가 구조적으로 작동하지 않는다
  — 이 방향은 폐기.
- **실제로 관찰된 hub_merge 혼합 현상(예: `Vx`={M1a,M1b,M58}, `Vy`={M4a,M4b,M63},
  `Vom1`={M2a,M18a})은 diode-stack의 내부 net이 아니라 diode-stack 소자의
  바깥쪽(tail) 연결점이 메인 신호경로와 우연히 겹친 것**이라, `find_diode_stacks()`
  가 추적하는 정보(누가 누구의 drain을 gate로 참조하는가)와 무관하다. 이 혼합
  자체는 `device_roles[name]["vertical_stack_id"]`(§8 참고, 이미 topology.json에
  있는 필드 — VDD~GND 직렬 전압강하 체인 단위)로 전부 설명된다(관찰된 사례 전부
  `stack_ids`가 `{None, "biasgen_*"}`처럼 서로 다른 vertical_stack_id를 섞고
  있었다). **단, 이것도 "오탐"이라고 증명된 건 아니다** — `find_hub_merge_
  candidates()` 자신이 "matching과 무관한 후보도 정상적으로 낸다"고 이미 선언하고
  있어서, 이 혼합이 실제로 잘못된 판단으로 이어진 사고 이력은 아직 없다. 그래서
  이번 설계엔 넣지 않는다 — `vertical_stack_id` 경계를 hub_merge 후보에 주석으로
  붙이는 정도의 낮은 리스크 확장은 실제 필요(예: 리포트에서 사람이 헷갈렸다는
  사례)가 생기면 별도로 설계.
- **`solve_diode_stack_current()` 배선 여부**: 세션18 K절에서 이미 "이 저장소 4개
  회로 중 실제로 필요한 곳이 없다"고 확인됨 — 이번 설계와 무관, 별도 결정 필요.
- **`find_hub_merge_candidates()` 자체에 role 파라미터 추가**: 이 함수는 애초에
  "matching과 무관하게 같은 diffusion에 물릴 수 있는 후보"를 찾는 게 목적이라
  (`find_matching_candidates()`와 반대 성격 — matching이 **아닌** 것도 후보로
  잡는 게 정상 동작), role 필터를 넣으면 함수의 존재 이유와 충돌할 수 있다. 넣을
  근거가 생기면 별도로 논의.
- **`device_roles`(topology.json)를 analog-grammar role로 자동 갱신**: §8에서
  교차검증(오라클) 계층으로만 쓰고, 자동 덮어쓰기는 하지 않는다(이유는 §8).

## 8. Role 어휘 매핑 — analog-grammar ↔ 이 프로젝트 `device_roles`

**성격 규정 먼저**: `topology.json`의 `device_roles`(`L_role`/`gm_id_role`/
`headroom_role`/`vertical_stack_id`)는 **사이징 전략 결정**(어느 정도 VDS 헤드룸을
줄지, 어떤 L을 고를지, gm/ID를 매칭시킬지)이고 사람/AI가 설계 판단으로 채운다.
`analog-grammar`의 role(`DIODE_CONNECTED`/`CURRENT_SOURCE`/`CASCODE`/`AMPLIFYING`/...)
은 **connectivity에서 결정론적으로 도출되는 구조적 사실**이다. 성격이 다르므로
**analog-grammar role이 `device_roles`를 대체하거나 자동으로 덮어쓰지 않는다** —
`circuit-topology-extraction`의 원칙("오라클 없는 netlist는 신뢰하지 않는다")과
같은 정신으로, **읽기 전용 교차검증 계층**으로만 쓴다: 두 값이 불일치하면 그
소자를 사람/AI가 재검토할 대상으로 flag한다(자동 수정 없음).

| analog-grammar role | 구조적 판정 근거 | `device_roles`의 개연적 대응 | 매핑 성격 |
|---|---|---|---|
| `DIODE_CONNECTED` | `G == D` | 대응 필드 없음(순수 구조 사실) | 신규 정보 — §6의 current_mirror 레퍼런스 판정에 직접 사용 |
| `CASCODE` | gate=BIAS, source=내부 노드 | `headroom_role == "cascode"` | 교차검증 — 예: `M11a`/`M11b`(headroom_role="cascode"). ⚠️ `M10`은 예시에서 제외(2026-08-08 세션25 — `M10`은 role=`CURRENT_SOURCE`(레일에 직접 닿음)인데 `headroom_role`만 `cascode`로 선언돼 있어 선언 오류로 의심됨, `.ai/context.md` 세션25 참고, 아직 미확정) |
| `FLOATING_CURRENT_SOURCE` | 서로 다른 kind가 비-레일 노드 2개 사이를 anti-parallel로 마주봄(Monticelli class-AB) | 대응 필드 없음(headroom_role에 아직 이 카테고리가 없음, `M9b`/`M18b`의 `headroom_role=="mirror"` 선언도 이 발견 이전 값이라 재검토 대상) | 신규(2026-08-08 세션25 신설) — `CASCODE`에서 분리됐던 role, 실측: `M9a`/`M9b`, `M18a`/`M18b` |
| `CURRENT_SOURCE` | gate=BIAS, source=rail, drain≠HIGH_Z | `headroom_role == "tail"` 또는 `L_role == "bias_replica"`와 부분 겹침 | 교차검증(느슨함 — 1:1 대응 보장 안 됨) |
| `ACTIVE_LOAD` | gate=BIAS, source=rail, drain=HIGH_Z | `headroom_role == "mirror"`류 일부 | 교차검증(느슨함 — mirror가 전부 active_load는 아님) |
| `AMPLIFYING` | gate=SIGNAL/INPUT/OUTPUT, drain≠rail | 명시적 대응 필드 없음(diff_pair 입력쌍이 여기 해당) | §6의 diff_pair 필터에 직접 사용 |
| `SOURCE_FOLLOWER` | gate=신호, drain=rail | 대응 없음 | 신규(이 4개 회로엔 현재 사례 없음) |
| `CONTROLLED_CURRENT_SOURCE` | gate=FEEDBACK | 대응 없음(CMFB 소자, 예: M7) — `L_role=="bias_replica"`와 개연성 | 신규 참고정보 |
| `SWITCH` | gate=CLOCK | 대응 없음 | 미사용(SC 회로 확장 시) |
| `UNRESOLVED` | 위 어디에도 안 걸림 | — | 오탐/추출오류 신호 — DESIGN.md 원칙 3과 동일 |

`vertical_stack_id`/`gm_id_role`은 이 프로젝트 고유의 사이징 전략 정보라
analog-grammar가 도출할 수 없다 — 매핑 대상이 아니다.

## 9. self-test 계획 (구현 시, `idiom_matches` 기반으로 갱신)

모두 `stick_diagram.py` self-test에 추가. 새 assertion을 채우기 전에 실제 함수를
호출해 반환값을 먼저 확인한다(`.ai/context.md` "상상으로 채우지 말고" 원칙).

1. **하위호환**: `idiom_matches=None`으로 기존 self-test(Test 6 등) 전체를 재실행 —
   `find_matching_candidates()` 반환값이 이 문서 편집 전과 바이트 단위로 동일한지
   `PYTHONHASHSEED=0` 고정 diff로 확인.
2. **M57/M58류 재현**(current_mirror, gate+source 그룹핑 검증): 세션18 기록의
   connectivity(`M57`: source=N58_57, gate=drain=Vbias2 / `M58`: source=Vx,
   drain=N58_57, gate=Vbias2)를 그대로 fixture로 구성 — `idiom_matches=None`이면
   `(pmos, "Vbias2")` 그룹에 M57/M58이 같이 잡히는지(오탐 재현) 먼저 확인하고,
   `find_idiom_matches()`로 실제 Match를 뽑아 넘기면 `m_mirror()`가 이 둘을 애초에
   하나의 `current-mirror` Match로 안 묶는지(gate는 같지만 source가 달라서) 확인.
3. **M11/MN류 재현**(diff_pair, AMPLIFYING 요구 검증): 기존 Test 6의 `folded_cascode_
   example()` fixture 재사용 — `idiom_matches=None`이면 옛 동작 그대로, `find_idiom_
   matches()` 결과를 넘기면 M11/MN이 `differential-pair` Match에 아예 안 잡히는지
   확인(둘 다 role=DIODE_CONNECTED라 `m_diffpair()`의 AMP 요구를 애초에 통과 못함).
4. **analog-grammar 부재 시 폴백**: `sys.path`에서 `analog-grammar/assets`를 일부러
   빼고 `find_idiom_matches()`가 `None`을 반환하는지, 그 `None`을 그대로
   `find_matching_candidates(transistors, idiom_matches=None)`에 넘겼을 때 기존
   동작과 동일한지 확인.
5. **캐스코드 대칭쌍 재현**(`find_stacked_matching_candidates()`, §6.3 선택지 4):
   `current_reuse_telescopic_ota` 실제 connectivity로 `find_idiom_matches()`가 낸
   `differential-pair`(M1a/M1b, M4a/M4b)를 `base_pairs`로, `netclass.stack_edges()`
   결과를 그대로 넘겨 `{M2a,M2b}`/`{M3a,M3b}`가 정확히 재현되는지 확인(이 문서
   작성 중 이미 스크래치 스크립트로 확인한 값과 일치해야 함). 확정된 쌍 위에
   얹혀 있지 않은 소자(M57/M58 등)가 섞여 들어오지 않는지도 회귀 대조.
6. **Fig.2 회로 대조**(선택, 참고용): `current_reuse_telescopic_ota.topology.json`의
   실제 connectivity로 `find_idiom_matches()`를 돌려, `analog-grammar/assets/
   examples/fig2_telescopic.json`(같은 회로)의 이미 알려진 idiom 매칭 결과
   (DESIGN.md §4 — `current-reuse-pair`/`cascoded-gain-node`/`tail-current-source`)와
   일치하는지 확인.

## 10.5. (2026-08-18 추가) §6 이후 신설된 재사용 유틸리티 카탈로그 -- 새 코드 작성 전 필독

이 문서가 §6 구현 시점(2026-08-06) 이후 갱신 안 된 사이, `idioms.py`에 REGISTRY 밖
유틸리티 함수가 여러 개 더 생겼다(세션34/35/오늘). **이 문서가 그동안 이 함수들을
카탈로그화하지 않아서, 이 함수들을 몰라 Transistor connectivity 위에 같은 로직을
손으로 다시 짜는 사고가 실제로 있었다**(`stick_diagram.py`의 `audit_theta_root_
direction()` — 캐스코드 root/follower 방향 판정을 자체 source/drain BFS로 3번
다시 짜다가, `idioms.propagate_reference_role_through_cascode()`가 이미 그 역할을
한다는 걸 뒤늦게 발견해 재사용으로 전환). 앞으로 이 문서를 읽는 AI/사람은 **새
그래프 탐색/역할 전파 코드를 짜기 전에 아래 표부터 확인할 것**.

| 함수 | 위치 | 반환/용도 |
|---|---|---|
| `m_cascode(devs, cls, imp, role)` | `idioms.py` | `cascode-stack` Match 리스트. 같은 kind 직렬(`up.S==lo.D`) + PMOS/NMOS 경계 cross-kind(`up.D==lo.D`, 2026-08-18 신설) 둘 다 인식. `ports['lo']`/`ports['up']`에 항상 명시. |
| `_cascode_lo_up_pairs(devs, matches)` | `idioms.py` | `cascode-stack` Match들을 `[(lo_name, up_name), ...]`로 정리(명시된 `lo`/`up` 우선, 없으면 `mid` 기반 추론으로 하위호환). |
| `propagate_reference_role_through_cascode(matches, seed_names, devs)` | `idioms.py` | seed 소자 집합을 캐스코드 체인 위로 고정점 반복 전파. **"두 소자 중 어느 쪽이 전류를 먼저 정하는 root/lo인가" 판단에 직접 쓸 것** -- `audit_theta_root_direction()`(`stick_diagram.py`)의 실제 사용 예: `root_dev`를 seed로 전파해 `reference`/`terms`의 소자가 그 안에 있으면(=root보다 위에 얹힌 캐스코드) 방향이 거꾸로라고 판정. |
| `find_cascoded_active_load_legs(devs, matches, imp, cls=None)` | `idioms.py` | current-mirror 다리 위에 캐스코드가 쌓여 진짜 이득노드(HIGH_Z)가 그 위로 옮겨간 경우까지 active-load 판정 확장. `propose_device_roles_gap_fill()`(`stick_diagram.py`)의 gain role 6번째 소스. |
| `m_tail(devs, cls, imp, role)` | `idioms.py` | tail-current-source 판정. `(CURR_SRC, CTRL_SRC)` 둘 다 인정 -- `m_diffpair()`도 2026-08-18부터 이와 일관되게 `CTRL_SRC`(CMFB FEEDBACK게이트 차동쌍)를 인정하도록 확장됨. |
| `netclass.stack_edges(devs)` | `netclass.py` | role/net분류 불필요, 순수 connectivity로 "X.source==Y.drain이면 Y가 X 위에 얹혀있다" 전부. `find_stacked_matching_candidates()`(§6.3)의 재료. |
| `propose_fold_group_gap_fill()`/`apply_fold_group_gap_fill()` | `stick_diagram.py` | (analog-grammar 유틸은 아니지만 같은 카테고리) `device_roles.*.fold_group`/`vertical_stack_id` 제안+실제 파일 반영 -- 2026-08-18 신설. |
| `audit_theta_root_direction()` | `stick_diagram.py` | `sizing_roles.theta`의 `"A"`/`"A_signed"` feed 방향이 캐스코드 체인과 모순되는지 검사(제안 아님, lint) -- 2026-08-18 신설, 위 `propagate_reference_role_through_cascode()`를 재사용. |

**2026-08-18 `idioms.py` 확장 2건**(위 표의 `m_cascode()`/`m_diffpair()` 관련, 새 회로
저작 시 알아둘 것):
1. `m_cascode()`가 이제 PMOS/NMOS 경계(drain-drain 접합, 다이오드/미러가 캐스코드에
   전류를 공급하는 구조)도 인식한다 -- 단, `up.source`가 레일이면 제외(complementary
   push-pull 출력단 오탐 방지, 실측 발견: `current_reuse_telescopic_ota`의 `M15`/`M16`).
2. `m_diffpair()`가 `role==AMPLIFYING`뿐 아니라 `CONTROLLED_CURRENT_SOURCE`(FEEDBACK
   게이트, CMFB 비교기 차동쌍)도 인정한다 -- 실측 발견: `M37a`/`M37b`.

## 10. 구현 확정 시 문서 갱신 목록

- `function-selection-map.md` §3 줄65: "게이트 공유 여부로 판단" → "게이트+소스
  공유(및 diode-connected 레퍼런스 존재)로 판단, `analog-grammar`의 idiom 매칭이
  있으면 그걸 직접 재사용"으로 갱신. `find_stacked_matching_candidates()`(복합소자
  기반 캐스코드 대칭쌍 탐지)도 새 표 행으로 추가.
- `stick-diagram-euler-layout.md` §2.6 카탈로그 표: M11/MN 오탐이 `idiom_matches`
  경로로 해소 가능해졌음을 추가(옵트인임을 명시). **캐스코드 대칭쌍 행의 "✅ gate
  공유 기준으로는 걸리지만..."을 "✅ `find_stacked_matching_candidates()`로 이미
  확정된 쌍 위의 stack 관계에서 재귀적으로 탐지(gate 공유 여부와 무관)"로 갱신**
  — 옛 방식(gate 우연 일치)보다 근거가 원인론적으로 바뀌었음을 명시.
- `analog-gmid-design/SKILL.md` "Cross-Skill 참조"에 `analog-grammar` 항목 추가.
- `analog-grammar/SKILL.md`의 "Cross-Skill 참조"는 이미 이 문서를 가리키고 있음
  (반입 시 미리 추가함) — 구현 완료 후 "설계안" → "구현 완료, 커밋 `<hash>`"로 갱신.
- 이 문서 자체의 최상단 상태 줄("설계안, 미구현")을 구현 완료 후 갱신.

## 11. netclass.py 자체의 실측 발견 버그 2건 + 개념 정정 1건 (2026-08 세션23)

§0~§10은 "이 프로젝트가 analog-grammar를 어떻게 소비하는가"를 다룬다. 이 절은 그 소비
과정에서 실제로 드러난, **analog-grammar 라이브러리(`netclass.py`) 자신의 버그**다 —
소비 측(`stick_diagram.py`)이 아니라 원본 라이브러리의 결함이라 별도로 기록한다.

### 11.1 rail 대소문자 불일치 — 이 프로젝트의 모든 role 분류가 rail을 인식 못 하고 있었다

`netclass.py`의 `RAILS_POS`/`RAILS_NEG`가 `{VDD, GND}` **대문자**만 인식하는데, 이
프로젝트의 모든 `topology.json`은 `vdd`/`gnd` **소문자**를 쓴다. 즉 analog-grammar
반입 이후 이 프로젝트에서 실행된 모든 role 분류가 **처음부터 rail을 하나도 인식하지
못한 채** 진행되고 있었다 — 예: `M6`(진짜 tail current-source, source=vdd)이
`CURRENT_SOURCE`가 아니라 `CASCODE`로 오분류.

**해결**: `RAILS_POS`/`RAILS_NEG`/`RAILS`를 대소문자 무관 비교(`.upper()` 정규화)를
지원하는 `_CaseInsensitiveNetSet(frozenset)`으로 교체 — 원본 라이브러리 코드를 직접
수정(이 프로젝트 쪽 wrapper로 국소 우회하지 않음. "wrapper로 해결한 거냐"는 사용자의
재확인 질문에 대해 원본 수정으로 확정한 경위 포함).

**교훈**: cross-skill로 반입한 라이브러리를 "이미 검증된 도구"로 무비판적으로 신뢰하지
말 것 — 이 프로젝트의 명명 관례(소문자 rail)가 그 라이브러리의 암묵적 가정(대문자
rail)과 다를 수 있고, 이런 불일치는 크래시가 아니라 **조용한 오분류**로만 나타나
발견이 늦어진다.

### 11.2 전류미러가 구동하는 bias net이 SIGNAL로 오분류 — "diode로만 구동" 판정 규칙의 구조적 사각

`netclass.py`의 BIAS net 판정 규칙("diode-connected 소자로만 구동되면 BIAS")은 **전류미러가
만드는 bias net**을 원천적으로 못 잡는다 — 전류미러는 정의상 `gate != drain`(미러 출력)이므로
"diode로만 구동"이라는 전제 자체가 성립하지 않는다. 실측: `Vbias1`(진짜 diode 레퍼런스가
구동) → `M60` 미러 출력 → `Vbias4`(전류미러로만 구동, diode 아님) 체인에서 `Vbias4`가
BIAS 대신 SIGNAL로 오분류.

**해결**: 드라이버 소자의 게이트 클래스를 **재귀적(고정점 반복)**으로 확인하도록 규칙
확장 — "diode-only" 이분법 대신 "이 net을 구동하는 소자 전부의 게이트가 이미 BIAS로
분류돼 있으면, 이 net도 BIAS로 전파한다".

**부수 효과(중요)**: 이 수정으로 `M7`/`M36a`가 `M6`/`M18_bg`와 **구조적으로 구별 불가능**
해졌다 — §11.3 참고.

### 11.3 "오탐(false positive)" 용어 정정 — ratio냐 1:1이냐는 mirror 여부와 무관

세션18부터 "`M36a`+`M7` current-mirror 오탐"으로 반복 인용되던 결론을, 사용자가 "전류가
ratio되는가 정확히 같아야 하는가만 다르지 VGS가 같으면 mirror가 맞는 것 아니냐"고
재검토를 요청했다. §11.1/§11.2의 두 버그를 고친 뒤 재검증하니, `M7`(role
`CURRENT_SOURCE`)/`M36a`(role `DIODE_CONNECTED`)가 진짜 bias mirror(`M6`/`M18_bg`)와
구조적으로 구별할 신호가 **전혀 없다**는 게 확인됐다.

**개념 정정**: "ratio냐 1:1이냐"는 W 크기(사이징) 문제일 뿐, mirror 관계 자체를 무효화하지
않는다. 이런 사례는 "오탐"(구조 탐지 알고리즘의 실수)이 아니라 "`matching_pairs` 미선언"
(사람/AI가 아직 안 내린 **설계 판단**)이라고 불러야 정확하다 — 두 표현은 책임 소재가
다르다: 전자는 "탐지 로직을 고쳐야 한다"는 뜻이고, 후자는 "이 회로에서 실제로 매칭이
필요한지는 설계자가 결정할 문제"라는 뜻이다.
