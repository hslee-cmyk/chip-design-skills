---
template: design
version: 1.0 (adapted — non-web project)
---

# analog-topology-json-library Design Document

> Plan: `docs/01-plan/features/analog-topology-json-library.plan.md`

---

## Context Anchor (Plan에서 복사)

| Key | Value |
|-----|-------|
| **WHY** | topology netlist가 Python 코드 하드코딩이라 재현 불가능, agent마다 해석이 달라짐 |
| **WHO** | 이 skill을 사용해 아날로그 회로 sizing+layout 리포트를 작성하는 (fresh) agent 세션들 |
| **RISK** | 오케스트레이션 레이어 설계가 기존 30개 함수의 self-test 회귀를 깨뜨릴 위험 |
| **SUCCESS** | folded_cascode/two_stage_ota 이관 후 connectivity가 기존 하드코딩 버전과 100% 동일, 파이프라인이 정직한 결과(PASS/FAIL 그대로)를 산출 |
| **SCOPE** | 스키마 설계 + 오케스트레이션 레이어 + 2개 example 이관 + telescopic OTA 시연·전체 리포트 완성 |

> **2026-07-28 최종 확정(구현 중 실측으로 3차 수정됨)**: 이 문서는 구현 과정에서 스키마가
> 두 번 크게 바뀐 뒤의 **최종 상태**를 반영한다. 변경 이력은 §2/§4.5에 남겨두되, 지금
> 읽는 사람은 §1 아래부터 "확정된 최종안"으로 읽으면 된다.

---

## 1. 두 종류의 JSON — 역할 구분 (최종안)

**핵심 원칙(구현 중 발견 후 확정)**: matching 배치(interdigitation/common-centroid),
Euler trail, row 분할, floorplan은 전부 **finger 개수·finger_w가 정해져야만** 계산 가능하고,
그건 사이징 결과값이다 — topology 단계에는 존재하지 않는다. 그래서 topology library JSON은
**사이징과 완전히 무관한 정보만** 담고, layout에 관한 모든 것(finger 배분, stack 배정, row
분할, floorplan 좌표)은 사이징 이후 instance-output JSON 단계에서만 계산된다.

| | **topology library JSON** (`library/*.topology.json`) | **instance-output JSON** (설계 산출물) |
|---|---|---|
| 언제 만드는가 | topology를 처음 이 skill에 등록할 때 1회 | 특정 spec(fT/CL/gain 등)으로 사이징을 마칠 때마다 |
| 무엇을 담는가 | connectivity(name/kind/source/drain/gate), matching kind(`symmetry`), 위상보정 함수 참조(`compensation`) — **사이징과 무관한 것만** | 위 구조 + 실제 사이징된 W/L/ID/gm/n_fingers/finger_w/stack_id + 그 값으로 계산한 stick diagram/box-shape/floorplan/coverage 결과 |
| 누가 소비하는가 | `run_topology_pipeline()`(사이징 재실행 시 connectivity+matching kind를 그대로 재사용) | layout 실행 agent |
| 재사용성 | 같은 topology의 모든 향후 설계에서 재사용 | 그 설계 1건 전용 |

이 구분이 핵심이다 — **topology library JSON은 "이 회로가 무엇으로 이루어졌고 무엇끼리
매칭돼야 하는가"만 고정하고, instance-output JSON은 "이번 사이징에서 그게 실제로 어떤
숫자·배치가 됐는가"까지 고정한다.** (참고: `layout`이라는 "가이드" 필드를 topology JSON에
따로 두는 중간 설계를 시도했었으나, 그 가이드조차 실제로는 finger 개수에 의존하는 정보라
사이징 없이는 유효하지 않다는 게 실측으로 드러나 폐기했다 — §2 하단 변경 이력 참고.)

---

## 2. 3가지 스키마 설계안

### Option A — 최소 변경(느슨한 dict)

`Transistor` 필드를 그대로 flat dict 리스트로 직렬화하고, matching/floorplan 정보는
느슨한 `dict`(키 이름 고정 안 함)로 얹는다. 로더는 `json.load()` 결과를 바로
`Transistor(**d)`에 넣는다.

- 장점: 구현이 가장 빠름, 기존 `Transistor` dataclass와 1:1 대응이라 변환 로직이 거의 없음
- 단점: 대칭성/matching/floorplan 필드 이름이 파일마다 흔들릴 위험 — "agent가 다르게 해석할
  여지를 없앤다"는 이번 작업의 핵심 목표와 정면으로 배치된다

### Option B — 엄격한 JSON Schema 검증 스키마

Option A의 구조 + 별도 `library/schema/topology.schema.json`(JSON Schema)을 만들어
`jsonschema` 패키지로 매 로드 시 검증. 버전 필드(`schema_version`) 필수.

- 장점: 필드 이름/타입 불일치를 즉시 에러로 잡음 — 가장 엄격
- 단점: 이 프로젝트엔 `jsonschema` 외부 의존성이 없다(현재 stdlib만 사용) — 새 의존성 추가는
  범위 확대. 검증 로직 자체도 유지보수 대상이 됨

### Option C — Pragmatic: 고정 섹션 구조 + 기존 함수 인자명 재사용 (권장)

Option A처럼 외부 의존성 없이 stdlib `json`만 쓰되, **최상위 섹션을 4개로 고정**하고 각
섹션의 필드 이름을 기존 함수가 이미 받는 인자 이름과 동일하게 맞춘다(예:
`pack_floorplan_grouped(spine_groups, mirror_pairs, ...)`의 `spine_groups`/`mirror_pairs`를
JSON 필드명으로 그대로 사용) — 새 이름을 발명하지 않으므로 "이 필드가 정확히 뭘 의미하는지"
질문이 애초에 생기지 않는다. 검증은 `jsonschema` 없이 로더 함수 내부에서 필수 키 존재만
확인(가벼운 assert), 엄격한 타입 검증이 필요해지면 Option B로 나중에 승격 가능.

> **변경 이력(구현 중 실측으로 3차 수정)**:
> 1. 2026-07-28 1차: `pack_floorplan_grouped()`의 실제 2D 좌표는 사이징이 끝나야 계산
>    가능하므로, topology JSON엔 좌표 없는 "layout 가이드"만, 실제 좌표는 instance-output
>    JSON에만 두기로 함 (`layout`/`floorplan` 필드 분리).
> 2. 2026-07-28 2차: `topology_library.py`의 위상보정 함수(`miller_ota_topology` 등)를
>    이름으로 참조하는 `compensation` 필드 추가(allowlist 조회, eval 금지).
> 3. 2026-07-28 3차(**최종**, 사용자 지적): 1차의 "layout 가이드"조차 실측해보니 사이징과
>    무관하지 않았다 — matching 배치(interdigitation/common-centroid)를 만족시키는 row
>    분할은 실제 finger 개수를 알아야만 계산되고, box-shape 균등성도 마찬가지다.
>    `run_topology_pipeline()`을 구현하며 finger 개수만 저장해선 hierholzer()가 매번 다시
>    찾는 Euler trail이 달라져 interdigitation이 재현 안 됨을 확인 → 실제 배치 순서까지
>    저장해봤지만, 그러면 "topology"가 사실상 "특정 사이징 결과의 고정 스냅샷"이 되어
>    재사이징 시 무의미해진다는 근본 문제가 드러남 → **`layout` 필드를 topology JSON에서
>    완전히 제거**하기로 확정. topology JSON은 이제 connectivity + matching kind +
>    compensation 참조만 남고, layout에 관한 모든 것(n_fingers/finger_w/w/stack_id/row
>    분할/floorplan)은 instance-output JSON에서 사이징 이후에만 계산된다.

```jsonc
// library/folded_cascode.topology.json (최종 스키마 — 실제 파일, schema_version "2.0")
{
  "schema_version": "2.0",
  "topology_name": "folded_cascode",
  "source": "Maloberti PDF p.34-38 worked example",

  "compensation": null,
  // folded_cascode는 단일 스테이지라 topology_library.py의 다단 보상 함수(miller_ota_topology
  // 등)가 필요 없다 — null이 정상. 다단 topology(예: two_stage_ota)는 아래처럼 채운다:
  //   "compensation": {
  //     "function": "miller_ota_topology",   // topology_library.py 함수 이름 참조,
  //                                           // 함수 자체는 이관/재구현하지 않는다
  //     "parameters": ["GBW", "CL", "Z", "NDP"],
  //     "notes": "구조 일치 근거(예: '1단 diff pair+mirror, 2단 common-source' 확인) —
  //               이 필드는 '앞으로 재사이징할 때 어느 방정식을 쓰는가'를 가리키지,
  //               현재 netlist의 W값이 그 함수로 역산됐다는 뜻은 아니다"
  //   }

  "netlist": [
    // connectivity만 — name/kind/source/drain/gate. n_fingers/finger_w/w/stack_id는
    // 여기 없다(사이징 산출물이라 topology 단계엔 존재하지 않는다 — 위 변경 이력 3차 참고)
    {"name": "MP", "kind": "pmos", "source": "vdd", "drain": "tail", "gate": "bias1"},
    {"name": "M3", "kind": "pmos", "source": "vdd", "drain": "X", "gate": "bias2"}
    // ... 나머지 M4~M11, MN
  ],

  "symmetry": {
    // find_matching_candidates()/audit_row_split()이 이미 쓰는 kind 값 그대로 —
    // 이 판정은 connectivity(gate/source 공유)만으로 결정되므로 사이징과 무관하다
    "matching_pairs": [
      {"names": ["M3", "M4"], "kind": "current_mirror"},
      {"names": ["M1", "M2"], "kind": "diff_pair"},
      {"names": ["M5", "M6"], "kind": "branch_symmetric"},
      {"names": ["M7", "M8"], "kind": "branch_symmetric"},
      {"names": ["M9", "M10"], "kind": "current_mirror"}
    ]
  }
}
```

```jsonc
// workspaces/<design>/<design_name>.instance.json (사이징+layout 결과 — layout agent에게 그대로 전달)
{
  "schema_version": "2.0",
  "topology_ref": "skills/analog-gmid-design/assets/library/folded_cascode.topology.json",

  "sizing": {
    // sizing_recipe.py의 SizingResult를 소자별로 직렬화(write_sizing_results()가 채움)
    "M3": {"gm": 45e-6, "gm_id": 15.0, "ID": 12e-6, "W": 30.0}
    // ...
  },

  "netlist": [
    // run_topology_pipeline()이 sizing_overrides로 채운 최종 Transistor 전체(asdict) —
    // n_fingers/finger_w/w/stack_id까지 전부 확정된 상태. 여기서부터가 실제 layout이다
    {"name": "MP", "kind": "pmos", "source": "vdd", "drain": "tail", "gate": "bias1",
     "n_fingers": 2, "finger_w": 10.0, "w": 20.0, "stack_id": "top"}
    // ...
  ],

  "floorplan": {
    // pack_floorplan_grouped()의 실제 반환값 그대로 — 손으로 재구성 금지(§1 표 5번 원칙)
    "placements": { "...": "FloorplanResult.placements" },
    "bbox": { "width": "...", "height": "..." },
    "aspect_ratio": "...",
    "packing_density": "..."
  },

  "box_shape": { "ok": "...", "row_widths": "...", "message": "..." },
  "audit_row_split": { "ok": "...", "checks": ["..."] },
  "coverage": { "ok": "...", "missing": [] }
}
```

- 장점: 새 의존성 없음, 필드명이 기존 함수 시그니처와 1:1이라 "이 필드로 뭘 하는가"가
  코드에서 바로 확인됨, topology JSON이 사이징과 완전히 독립적이라 재사이징해도 그대로 재사용
- 단점: Option B만큼 엄격한 자동 검증은 없음(로더의 가벼운 assert로 대체) — 실전에서
  문제가 되면 나중에 B로 승격 가능한 구조로 설계
- **알려진 한계(실측 확인, 2026-07-28)**: matching-safety(interdigitation/common-centroid)를
  만족시키는 **row 분할은 자동 탐색되지 않는다** — `run_topology_pipeline()`은 스택 전체를
  단일 물리 행으로 놓고 감사할 뿐이다. FAIL이면 호출자가 `search_stack_finger_w()`/
  `common_centroid_2row()`로 새 finger 배분을 찾아 `sizing_overrides`를 조정해 재호출해야
  한다 — §1.6/§1.7의 기존 피드백 루프와 동일한 패턴(자동 매직이 아니다).

### 비교 표

| | 복잡도 | 유지보수 | 회귀 위험 | "해석 여지 제거" 목표 부합도 |
|---|:---:|:---:|:---:|:---:|
| A. 최소 변경 | 낮음 | 낮음 | 낮음 | 낮음(필드명 미고정) |
| B. 엄격 스키마 | 높음(새 의존성) | 높음 | 중간(검증 로직 버그 가능) | 높음 |
| **C. Pragmatic(권장)** | 낮음 | 낮음 | 낮음 | **높음**(기존 함수 인자명 재사용으로 자연히 고정) |

---

## 3. 오케스트레이션 레이어 (최종 구현 — Option C 기준)

`stick_diagram.py`에 추가한 함수(기존 ~30개 계산 함수는 시그니처 무변경):

| 함수 | 역할 |
|---|---|
| `load_topology(json_path) -> tuple[list[Transistor], dict]` | `netlist`(connectivity만)를 `Transistor` 리스트로(n_fingers=1 기본값, finger_w/w/stack_id=None), `symmetry`/`compensation`을 `meta` dict로 반환. **`layout` 필드는 없다**(§1/§2 최종 확정) |
| `run_topology_pipeline(topology_json_path, sizing_overrides, floorplan_hints=None) -> dict` | `load_topology()` → `sizing_overrides`(소자별 n_fingers/finger_w/w/stack_id — **필수**, 사이징+finger 배분 이후에만 의미 있음)로 덮어쓰기 → `split_into_stacks()`로 스택(=기본 물리 행) 구성 → §1.6/§1.7 순서 그대로 `check_box_shape()` → `audit_row_split()`(matching kind는 `symmetry`에서) → `pack_floorplan_grouped()`(`floorplan_hints` 없으면 스택마다 1:1 그룹 기본값) → `check_stick_diagram_coverage()`. 반환: `{"transistors": [...], "box_shape": ..., "audit_row_split": ..., "floorplan": ..., "coverage": ...}`. **⚠️ matching-safety 위한 row 분할은 자동 탐색하지 않는다** — FAIL이면 호출자가 `search_stack_finger_w()`/`common_centroid_2row()`로 새 배분을 찾아 재호출(§2 "알려진 한계" 참고). `run_full_circuit_audit()`는 `dispositions` 판단이 필요해 의도적으로 미포함 — 필요하면 호출자가 별도 호출 |
| `save_instance_json(path, topology_json_path, sizing_results, pipeline_result)` | 위 결과를 instance-output JSON 스키마(`sizing`+`netlist`+`floorplan`+`box_shape`+`audit_row_split`+`coverage`)로 파일에 씀 |

`sizing_recipe.py`에 추가한 함수(기존 `size_transistor`/`optimize_multistage` 등은 무변경):

| 함수 | 역할 |
|---|---|
| `load_sizing_targets(json_path) -> dict` | instance-output JSON(또는 별도 sizing-spec JSON)에서 `design_spec`(gm/ID sizing 목표값: fT/CL/gain_target 등)을 읽음. 키가 없으면 파일 전체를 반환(단순 스펙 JSON도 지원) |
| `write_sizing_results(json_path, results: dict[str, SizingResult])` | `size_transistor()`/`optimize_multistage()` 결과를 instance-output JSON의 `sizing` 섹션에 병합해 씀(파일 없으면 새로 생성, 다른 섹션은 건드리지 않음) |
| `run_sizing_pipeline(topology_json_path, design_spec: dict)` | topology JSON의 `compensation`을 읽어 `function` 이름을 `_COMPENSATION_REGISTRY`(명시적 allowlist)로 조회 → `design_spec`으로 호출. **반환 타입이 갈린다**: `compensation` 있으면 `topology_library.py`의 세 함수가 공통으로 반환하는 `topology_fn(prev_cggs) -> list[gm_i]` **클로저**를 그대로 반환(`optimize_multistage()`에 넘길 것) / `compensation`이 `null`이면 `design_spec` **dict**를 그대로 반환(`size_transistor()`를 직접 쓸 것) |

이 레이어는 **I/O만 담당** — 계산 로직은 한 줄도 새로 만들지 않는다(기존 self-test가 곧
이 레이어가 호출하는 함수들의 회귀 방어선이므로 그대로 유효). `audit_row_split()`은 이번
작업 중 `precomputed_sequences` 파라미터를 추가했다가(위 §2 변경 이력 3차의 row_splits
시도) 그 스키마 자체가 폐기되며 다시 원래 시그니처로 되돌렸다 — 최종적으로 기존 30개 함수
중 **단 하나도 시그니처가 바뀌지 않았다**.

---

## 4. 마이그레이션 절차 (실행 완료 — 배치 1~3)

1. `folded_cascode_example()`/`two_stage_ota_example()`의 connectivity(name/kind/source/
   drain/gate)만 JSON `netlist`로 추림(수작업 재입력 금지 — 실제로는 `Transistor` 필드를
   그대로 옮기되 n_fingers/finger_w/w/stack_id는 제외)
2. `symmetry.matching_pairs`는 이번 세션에서 이미 실측 확정된 kind 판정 결과
   (`find_matching_candidates()`/`audit_row_split()`가 쓰는 것과 같은 기준)를 그대로 채움
3. `load_topology()`로 되읽어 `Transistor`의 connectivity 필드(name/kind/source/drain/gate)가
   원본과 동일한지 diff — **실제로 두 topology 모두 diff=0 확인됨**
4. `run_topology_pipeline(path, sizing_overrides)`에 원본 example의 n_fingers/finger_w/w/
   stack_id를 `sizing_overrides`로 그대로 넣어 실행 — box_shape/audit_row_split/floorplan/
   coverage가 계산됨. **audit_row_split은 두 topology 모두 branch_symmetric/diff_pair 쌍에서
   FAIL이 나온다 — 이는 버그가 아니라 정직한 결과다**(단일 행 후보로만 감사하고 row 분할은
   자동 탐색하지 않으므로, §2 "알려진 한계" 참고). 이 세션 초반에 손으로 찾은 2-row
   swap-분배 값과 비교하려면 별도 저장된 `folded_cascode_split.json` 등과 대조할 것(이번
   배치의 정식 산출물은 아님)
5. `stick_diagram.py`/`sizing_recipe.py` self-test 전체 재실행, exit 0 확인 — **완료**
6. 문서 반영: `function-selection-map.md`(새 함수), `SKILL.md`(§1.5/§1.6/§1.7에 "library/
   JSON을 정본으로 우선 사용" 문구 추가), `consistency-map.md`(변경 이력) — 배치 4에서 진행

---

## 4.5 새 topology를 논문/스펙 문서에서 처음부터 JSON으로 만드는 절차 (신설 — 사용자 지적 반영)

> **4번(마이그레이션)은 이미 Python 코드로 존재하는 두 example을 옮기는 절차다 — 아직 코드가
> 없는 새 논문/스펙을 다루는 절차가 아니다.** 이게 없으면 새 topology마다 agent가 JSON
> 필드를 또 임의로 해석하게 되어, 이번 작업의 핵심 목표("agent가 문서를 해석해 다르게 만들
> 여지 제거")가 원점으로 돌아간다. 아래 절차는 기존 `folded_cascode_example()`의 docstring이
> 이미 실천하고 있던 "원문에서 직접 읽어냄, 짐작 금지" 원칙(`design-report-spec.md` PRE-FLIGHT
> 사고4 — "논문 원문을 안 읽고 일반적인 구조를 상상해서 채움")을 JSON 작성 단계에 그대로
> 적용한 것이다.

### 절차 (2026-07-28 최종 스키마 반영 — `layout` 관련 단계 삭제)

1. **`library/_TEMPLATE.topology.json` 스캐폴드에서 시작한다**(배치 1에서 생성) — 3개 섹션
   (`netlist`/`symmetry`/`compensation`)의 빈 구조 + 각 필드가 무엇을 요구하는지 인라인
   주석으로 명시. 빈 종이에서 시작하지 않는다 — 필드를 빠뜨리거나 새 이름을 발명할 여지를
   스캐폴드가 미리 막는다. **`layout` 섹션은 없다** — 사이징 이전엔 존재할 수 없는 정보이므로
   topology JSON 자체에 자리를 만들지 않는다(§1/§2 최종 확정 참고).
2. **`netlist`**: 논문의 실제 스키매틱/핀 연결을 직접 읽어 소자별 connectivity(name/kind/
   source/drain/gate)만 채운다 — n_fingers/finger_w/w/stack_id는 넣지 않는다(사이징
   산출물). "일반적으로 이런 구조는 보통 이렇다"는 상상 금지(PRE-FLIGHT 사고4와 동일 원칙).
   회로도가 이미지/PDF라면 소자별 연결을 표로 먼저 옮겨 적은 뒤 JSON으로 옮긴다.
3. **`symmetry`**: 손으로 판단하지 않는다 — 2번에서 만든 `netlist`로 `load_topology()`를
   실행해 `Transistor` 리스트를 얻은 뒤, **`find_matching_candidates()`를 실제로 호출**해
   나온 후보를 `design-report-spec.md` §1.5의 5가지 패턴((a)우연한 net 공유 (b)diode→mirror
   체인 (c)바이어스 소비 (d)피드백 공유 (e)진짜 매칭쌍)으로 걸러 진짜 매칭쌍만 채운다. 이
   판정은 connectivity만으로 결정되므로 사이징 없이도 완결된다. `current_mirror`/`diff_pair`
   둘 다 이 함수 하나로 후보가 나온다(2026-07-28 함수 수정 완료 — 아래 참고).

   **⚠️ 2026-07-28 배치 5 실측 발견 + 즉시 수정**: `find_matching_candidates()`의
   `diff_pair` 경로가 내부적으로 `w`(소자 W) **일치를 필수**로 요구해서, topology 단계엔
   W가 아예 없으므로 처음엔 diff_pair 후보가 **항상 빈 결과**로 나왔다. 사용자가 이 함수의
   존재 이유(구조적으로 가능성 있는 후보를 미리 좁혀 AI가 모든 소자쌍을 수동으로 훑지
   않게 하는 것 — 함수 이름 자체가 "후보 탐지"이지 "확정"이 아님)를 지적 — W를 **필수**가
   아니라 **선택적 추가 필터**로 바꿨다: W가 둘 다 있으면(사이징 후, 대형 회로 오탐 방지용)
   지금처럼 W까지 일치해야 후보로 잡고, W가 없으면(사이징 전) 구조적 신호(같은 kind+source,
   다른 gate, 정확히 2개)만으로 후보를 낸다. 이 수정으로 `current_reuse_telescopic_ota`
   재시험 시 M1a/M1b, M4a/M4b, M37a/M37b가 즉시 diff_pair 후보로 나왔고(수동으로 채웠던 것과
   정확히 일치), 덤으로 bias-gen의 의심스러운 M31/M32 후보(실제로 Euler 결함이 있던 그
   sub-block)까지 자동으로 표면화했다 — gap-findings.md §3/§8 참고, 기존 self-test 전체
   회귀 없음 확인.

   **⚠️⚠️ 3-1(필수, 생략 금지, 2026-07-28 신설)**: `symmetry.matching_pairs`를 다 채웠다고
   끝난 게 아니다 — `find_matching_candidates()`가 찾은 후보 중 **조용히 빠뜨린 게
   없는지** 반드시 `check_symmetry_dispositions(transistors, matching_pairs, dispositions)`
   로 확인하고 `ok=True`를 받은 뒤에만 topology JSON을 저장한다. `find_matching_candidates()`
   는 "후보"만 낼 뿐 확정이 아니므로(함수 이름 그대로), 후보 각각을 (a) `matching_pairs`에
   채택하거나 (b) `symmetry.dispositions`(`[{"tag":..., "kind":..., "key":..., "category":...,
   "reason":...}]`, `design-report-spec.md` §1.5 5가지 패턴 중 하나를 category로)에 명시적
   기각 사유를 남기거나 둘 중 하나를 **반드시** 해야 한다 — 이게 `run_full_circuit_audit()`
   3번 체크("every candidate has a recorded disposition")와 정확히 같은 원리를
   topology-authoring 단계에 적용한 것이다. **후보 그룹이 3개 이상의 소자를 묶으면
   `matching_pairs` 항목 하나로 전부 기록한다** — pairwise로 쪼개면(예: 3-leg 미러를
   2개의 2-소자 항목으로) 부분집합 검사가 실패해 여전히 UNDISPOSED로 남는다(실측 확인,
   `current_reuse_telescopic_ota` 시연에서 M27/M28/M29를 처음에 pairwise로 나눠 기록했다가
   이 게이트에 걸려서 발견함).

   **⚠️⚠️⚠️ 3-2(필수, 2026-07-28 추가 발견)**: `check_symmetry_dispositions()`는 후보
   누락 확인 **전에** net 이름 대소문자 자기모순도 스캔한다(`run_full_circuit_audit()` 2번
   체크와 동일 로직) — `Vbias1`/`vbias1`처럼 같은 물리 net을 다르게 표기하면 그 자체로
   `ok=False`가 된다. 이건 §4.6의 `linked_topology_files`(여러 파일로 쪼개는 기능)를 만든
   직후 사용자가 "예전에 겪었던 대소문자 문제(사고9)가 이번에도 반영됐냐"고 확인해서 발견한
   빈틈이었다 — 지금까지 예제 3개는 우연히 표기가 일관돼서 이 문제가 드러나지 않았을
   뿐, 검사 자체가 없었다. 대소문자가 꼬이면 **자동으로 소문자 통일해 조용히 고치지
   않는다** — 후보 탐지 자체가 신뢰 불가한 상태이므로, 사람/AI가 원본 net 이름 중 어느
   쪽이 오타인지 직접 확인해 고친 뒤 재실행해야 한다.
4. **`compensation`**: 회로의 **구조**(단 수, 각 단의 역할 — diff pair+mirror 부하 1단,
   common-source 2단 등)가 `topology_library.py`의 기존 함수(`miller_ota_topology`/
   `nmcnr_3stage_topology`/`ngcc_3stage_topology`)가 모델링하는 구조와 일치하면 그 함수
   이름을 참조한다. **이 판단은 "이 예제의 현재 W값이 그 함수로 역산됐는가"가 아니라 "이
   회로가 그 함수가 다루는 구조인가"이다** — 지금 netlist에 이미 W가 있든 없든(topology
   단계엔 W가 없으므로 항상 없음), 구조 분석만으로 결정 가능하다(2026-07-28 실제 정정
   사례: 처음에 "역산 검증 안 됨"을 이유로 `null`로 뒀다가, 구조가 명백히 일치함을
   재확인하고 참조로 바꿨다). 구조가 안 맞으면 `compensation: null` — 새 함수 유도는
   `topology-fn-derivation-guide.md` 절차를 따르되 이 파일 작성 범위 밖이다.
   **(2026-07-30 신설, 필수)** `compensation`이 `null`일 땐 반드시 `_compensation_status`도
   같이 채운다 — `null`이 "이 회로는 애초에 보상이 필요 없다"(단일 스테이지 등,
   `not_applicable`)는 뜻인지 "보상이 필요한데 기존 함수 중 안 맞아 새 `topology_fn`
   유도·등록이 아직 안 됐다"(`pending_topology_fn`)는 뜻인지 이 필드 없이는 구분이 안
   된다 — 후자를 표시 없이 그냥 `null`로만 두면, 나중에 그 topology를 사이징할 때 보상
   구현이 빠진 걸 놓치기 쉽다. `compensation`이 함수를 참조하면 `_compensation_status:
   "resolved"`.
5. **검증**: 작성한 JSON을 `load_topology()`로 로드하고, 임의의 `sizing_overrides`
   (n_fingers/finger_w/w/stack_id)를 채워 `run_topology_pipeline()`을 실제 실행해
   Euler-validity/box-shape/`audit_row_split`이 계산되는지 확인한다 — **이 실행 자체가 새
   topology JSON의 1차 검증 게이트다**. `audit_row_split` FAIL은 정상일 수 있다(row 분할
   미시도 상태이므로) — `load_topology()` 단계에서 에러 없이 로드되고 connectivity가
   맞는지가 이 단계의 핵심 확인 사항이다.
6. 완성된 JSON은 `library/<topology_name>.topology.json`으로 저장하고, 어떤 논문/스펙의
   어느 그림/페이지에서 추출했는지를 `source` 필드에 반드시 남긴다(기존
   `folded_cascode_example()` docstring의 "p.34-38에서 직접 확인" 관행을 JSON 필드로 승격).
   **소자 수가 많아 파일 하나가 너무 커지면(권장: 이 skill이 다뤄온 규모(수십 개)에서는
   보통 필요 없다) 여러 topology JSON으로 쪼갤 수 있다** — 그때는 각 파일의
   `linked_topology_files`에 자기 자신을 뺀 나머지 형제 파일 전부를 나열한다(§4.6 참고).

## 4.6 회로를 여러 topology JSON으로 쪼갤 때 — `linked_topology_files` (2026-07-28 신설, 사고8 재발 방지)

> **실제 사고 재발 위험**: PRE-FLIGHT 사고8(design-report-spec.md §1.5)은 "bias-gen과
> Class-AB를 각각 따로 `find_matching_candidates()`에 돌려서, 두 sub-block에 걸친 진짜
> current-mirror 관계(같은 gate net 공유)를 놓쳤다"는 사고였다. 지금까지의 예제(folded_
> cascode/two_stage_ota/current_reuse_telescopic_ota)는 전부 **회로 하나 = topology JSON
> 파일 하나**였기 때문에 이 사고가 구조적으로 재발할 수 없었다 — `load_topology()`가
> 항상 그 회로의 전체 netlist를 한 번에 반환하니까. 하지만 이건 "우연히 안전했던" 것이지
> 강제된 게 아니었다 — 만약 소자 수가 아주 많은 회로를 여러 topology JSON으로 쪼개고 각
> 파일을 독립적으로 다루기 시작하면, 파일 경계가 곧 sub-block 경계가 되어 사고8이 그대로
> 재발할 수 있다.

**해결**: 파일을 쪼개는 것 자체는 막지 않되(소자 수가 정말 많으면 파일 하나로 관리하기
어려울 수 있다), 각 topology JSON 파일에 `linked_topology_files`(같은 폴더 기준 상대경로
리스트, **자기 자신을 뺀 나머지 형제 파일 전부**)를 두고, `load_topology()`가 이 목록을
**자동으로 따라가 전부 병합**해서 반환하도록 만들었다 — 어느 형제 파일을 진입점으로 읽든
항상 회로 전체가 보인다. `find_matching_candidates()`/`check_symmetry_dispositions()`는
이 병합된 전체 목록에 대해서만 실행되므로, 파일이 몇 개로 쪼개져 있든 stage 경계를 넘는
매칭 관계를 놓칠 수 없다.

- 형식: `[{"names": [...], ...}]`이 아니라 단순 문자열 리스트 — `["biasgen.topology.json",
  "cmfb.topology.json"]` 처럼 파일명만 나열한다.
- **방사형 구조만 지원한다** — 그룹 안의 모든 파일이 서로를 전부 나열해야 하고(A가 B/C를,
  B가 A/C를, C가 A/B를), 체인 구조(A→B→C만, B/C는 서로 모름)는 지원하지 않는다.
  `load_topology()`는 재귀적으로 형제의 형제까지 따라가지 않는다.
- `symmetry`(matching_pairs+dispositions)와 `netlist`는 병합되지만, `compensation`은
  진입점 파일(호출자가 실제로 연 파일)의 것만 쓴다 — 여러 파일에 중복 기록하지 않는다.
- self-test(Test 21.6, 합성 2-파일 예제)로 "형제 파일을 자동으로 합치는지", "cross-file
  matching 후보를 실제로 찾아내는지" 회귀 확인 완료. 현재 3개 example(folded_cascode/
  two_stage_ota/current_reuse_telescopic_ota)은 전부 단일 파일이라 `linked_topology_files`
  가 빈 배열이다 — 실제로 쪼갤 필요가 생기기 전까지는 이 필드를 채우지 않는 게 기본이다.

### 이번 작업 범위와의 관계 (2026-07-28 수정 — 시연 포함으로 범위 확대, 사용자 확인)

`_TEMPLATE.topology.json` 스캐폴드 + 문서 반영에 더해, **이 절차를 telescopic OTA 논문에
실제로 적용해 시연**하는 것도 이번 범위에 포함한다(Do 문서 배치 5). 이유: folded_cascode/
two_stage_ota 이관(4번 절차)만으로는 "이미 Python으로 존재하는 구조를 JSON으로 옮길 수
있는가"만 검증되고, "새 논문에서 처음부터 JSON을 authoring할 수 있는가"는 검증되지 않는다 —
스키마 자체가 그 두 example에서 역설계됐으므로, 그 두 example로 스키마를 검증하는 것은
순환 검증이다. telescopic OTA는 Class-AB/bias-gen/CMFB처럼 두 example에 없는 구조를 갖고
있어(또한 이미 이번 세션에서 한 번 읽혀 사이징 데이터가 있어) 더 강한 독립 검증이 된다.

**(2026-07-28 재수정, 사용자 확인 — 범위 재확대)** 처음엔 "topology JSON 하나를 작성하고
검증"까지만 범위로 뒀으나, 사용자가 "전체 리포트도 범위 안에 둬"라고 명시적으로 확대를
요청했다 — 이제 `current-reuse-telescopic-ota-report` 워크스페이스의 원래 미완성 문제
(PRE-FLIGHT 27번: floorplan 통째로 누락, CMFB/bias-gen/Class-AB stick diagram 22개 소자
누락)를 이 새 도구로 실제로 끝까지 완주하는 것까지 이번 범위에 포함한다(Do 문서 배치 6).
이렇게 하면 "스키마가 새 topology를 표현할 수 있는가"(배치 5)뿐 아니라 "이 도구 체계로 실제
완결된 산출물을 낼 수 있는가"(배치 6)까지 한 세션에서 검증된다 — 원래 사고의 재발 방지가
문서상의 가드레일(§1 표 8번, `check_stick_diagram_coverage()`)뿐 아니라 실제 완성된 산출물로
증명된다.

---

## 5. 승인 사항 (Checkpoint 3 — 전부 확정 완료)

1. **스키마 옵션**: Option C(Pragmatic) 채택 — ✅ 승인 완료, 이후 §1/§2에서 최종 3차 수정
   (`layout` 필드 완전 제거)까지 사용자 확인 완료
2. ~~`layout_groups`의 이름 규칙~~ — **해당 없음으로 정리됨**: `layout`/`groups` 필드
   자체가 topology JSON에서 제거됐다. `stack_id`는 이제 사이징 이후 `sizing_overrides`를
   통해 인스턴스 단계에서 부여되며, 기존 example의 관행("top"/"mid"/"bot")을 그대로 따른다
   — 별도 결정 불필요
3. **instance-output JSON의 위치**: `workspaces/<design>/` 채택(기존 관례 유지) — ✅ 승인 완료
