---
id: 20260930-v7-registry-edges
phase: 0.5
evidence_type: red-green
gate_change: yes
approval: 20260930-v7-registry-edges
---
## 의도

백로그 B33(`.ai/context.md` 15005행, 준비 자료 `_drafts/prep_b33_v7_edges.md`): 게이트 V7 도구 `tools/gates/reachability.py`의 정적 호출 그래프(`build_graph`)가
스펙이 요구하는 간선 둘을 만들지 않고, 반대로 스펙이 요구하지 않는 간선을 만든다.

1. **dict 레지스트리 간선 누락**(거짓 FAIL). 계획 용어표 '운영 경로'(121행)는 "문자열 레지스트리(`_METRICS_REGISTRY`, `_COMPENSATION_REGISTRY`, topology.json `"function"`)로
   도달하는 것 포함"이라 하고 design 05 §10 V7 행(321행)도 "문자열 레지스트리 포함"이라 한다. 그런데 그래프 노드는 def·`<module>`·`__main__`뿐이고 `<module>`에는
   같은 파일 `__main__`에서만 들어가므로, 레지스트리를 **읽는** 함수(`compute_metric`·`apply_theta_feed`·`_build_theta_evaluator._evaluate`)가 도달해도 이름
   `_METRICS_REGISTRY`가 def가 아니라서 값 함수로 가는 간선이 없다. 사전 실측(7535799, scratch 시제품 -- 판정 기록 수치 아님): 운영 루트에서 미도달인 소스 분류 def 494개 중
   115개, 그중 레지스트리 경유 74개(값 38 + 그 값이 부르는 함수 36).
2. **생성자 간선 누락**(거짓 FAIL). `Cls(...)`·`raise Cls`는 `Cls.__init__`(dataclass면 `__post_init__`) 호출이지만 클래스 이름은 어느 def와도 이어지지 않는다
   (`SemiEmpiricalGmIdLUT.__init__`·`InfeasibleSizingError.__init__`·`Transistor.__post_init__` 3개 미도달).
3. **비운영 파일로의 이름 폴백 누수**(거짓 PASS -- 이 card에서 새로 고정하는 결함). 이름·속성 폴백(`by_name`)에 파일 범위가 없어 엔진의 `x.size`·`_rel`·`run` 같은
   흔한 이름이 `tests/`·`tests/probes/`·`workspaces/*` 스크립트의 같은 이름 def로 간선을 만든다. 사전 실측: 운영 루트가 비운영 노드 64개에 닿고, 호출자가 test·probe·
   workspace 스크립트뿐인 `sizing_recipe.size_transistor`가 '도달'로 셈해진다(`_solve_vgs` → 속성 `.size` → `workspaces/current-reuse-telescopic-ota-report/resize.py::size`
   → `size_transistor`). 새 엔진 def가 test 전용인데 V7 PASS가 나는 면이 지금 모든 card에 열려 있다.

고칠 방향(규칙 3개, 사전 조사 §3):
* **R1 레지스트리 바인딩**: 모듈 최상위의 단순 이름 바인딩(`NAME = <식>`, `NAME: T = <식>`)마다 그래프에 바인딩 노드(`<파일>::=NAME`)를 두고 값 식이 참조하는 def로
  간선을 낸다. 도달 가능한 코드가 그 이름을 참조할 때만(같은 파일 이름, `from M import NAME`, 모듈 별칭 `M.NAME`, M에 바인딩이 없으면 -- 재수출 -- 같은 이름의 바인딩)
  바인딩 노드로 간선이 생긴다. **import 문장 자체는 간선이 아니다**(거절한 대안 R0 "import하면 모듈 최상위 전체 도달" -- 등록만 하고 아무도 읽지 않는 레지스트리를
  통과시키고, 3의 누수와 합쳐 면제 승인 대상 2개를 거짓 도달시킨다).
* **R2 생성자**: 도달 가능한 코드의 호출 위치 `Cls(...)`(`Cls`·`from M import Cls`·`M.Cls`) 또는 `raise Cls` → 그 클래스의 `__init__`·`__new__`·`__post_init__`,
  클래스에 없는 dunder는 기반 클래스(클래스 정의의 bases 이름으로 해석, 재귀)의 것. 호출이 아닌 클래스 이름 참조(`isinstance`·`except`·주석)는 생성자로 가지 않는다
  (결정 필요 항목 Q1 -- 권고안).
* **R3 운영 범위**: V7 `main`의 도달 계산은 소스 분류 파일(`_is_source`) 노드만 따라간다. `build_graph`는 R3를 모른다.

**R1·R2를 어디에 두나 -- `build_graph`(V3와 공유)에 둔다.** 준비 자료 §4.2가 적은 부작용을 받아들이는 판단과 근거:
* 스펙: design 05 §10 V3 ③ "인벤토리 = 정적 호출 그래프(V7과 같은 그래프)"와 계획 N4.2 V3 "정적 호출 그래프에서 그 함수에 도달하는 test만"이 **같은 그래프**를
  요구한다. V7에만 두면 두 그래프가 갈라져 스펙 문구 개정(승인)이 필요하고, V3는 지금의 결함을 그대로 가진다.
* V3 쪽 효과는 **거짓 FAIL 제거**다: 지금 레지스트리 값(`_metric_*`·`_feed_*` 등)은 인벤토리가 0이라 그 def를 바꾸는 card는 모든 변이가 '인벤토리 없음 → 생존' → V3 FAIL이다
  (사전 실측 7535799: 인벤토리 0인 소스 def 82 → 14, `_metric_sum_current` 0 → 166, `SemiEmpiricalGmIdLUT.__init__` 0 → 335). 합성 저장소 시제품에서 레지스트리 값 변이
  7개가 base 도구 FAIL(생존 5) → 새 그래프 PASS(7 killed).
* 약화가 아니다: 인벤토리는 **실행할 test의 집합**일 뿐이고 변이를 죽이는 증거는 그 test의 실제 실패다. 인벤토리가 커져도 옛 인벤토리 test는 그대로 포함된다(새 그래프는
  옛 그래프 간선의 상위집합 -- 계약 9). R3는 V3에 두지 않는다(V3는 test 노드에서 출발한다).
* 비용(사전 실측 7535799, test 함수 454개): (소스 def, 도달 test) 쌍 33,991 → 79,809(2.35배), 소스 def별 인벤토리 중앙값 61 → 148, 전 test 도달 계산 0.30 → 1.14초,
  `build_graph` 5.18 → 5.19초. 변이 실행 비용은 인벤토리 test 실행 시간에 비례해 늘어난다 -- auditor가 판정 기록 1건에서 잰다(계약 12).
* 새 위험 두 가지를 계약으로 드러낸다: (i) 새로 인벤토리에 들어온 test가 격리 복제본 기준 실행에서 실패하면 V3가 `ERROR`(B28 규칙, 조용한 생존 아님) (ii) 변이 실행 상한
  `--timeout`(기본 600초) 초과는 '죽인 변이'로 세지므로, 인벤토리가 커져 기준 실행 시간이 상한에 가까워지면 느려진 변이가 거짓으로 죽는다 -- auditor가 측정 건의
  최대 기준 실행 시간을 상한과 함께 기록한다(계약 12). 상한 조정은 이 card 범위 밖(필요하면 별도 card).

`mutate_changed.py`는 코드 변경이 없다(`rch.build_graph`를 그대로 부른다, HEAD 317행). 설치 사본이 없어 재설치 불필요(§13.4 -- `reachability.py`·`mutate_changed.py`는
§4.4 캐시에서 실행, 설치 사본은 gate `pre-receive`·`gate-runner.py`뿐이고 둘 다 V7을 import하지 않는다) -- 새 도구는 이 변경이 반영된 뒤의 base 캐시부터 쓰인다.
design 05 §10 V7 행은 그래프 규칙을 명시하는 **명확화**가 필요하다(판정 문구 개정 = 이 card 승인 기록 범위, 계약 13).

## 관찰 가능한 계약

모두 V7 CLI(`reachability.py --root --base --head --config`, JSON 한 줄·exit)로 합성 저장소에서 관찰한다(계약 10·12는 V3 CLI, 11·14는 auditor). 합성 저장소 공통 base:
`skills/analog-gmid-design/assets/rt_engine.py`(`rt_gain`)와 `workspaces/run_harness.py::run`(`rt_gain` 호출) -- `gate_config.json` 루트 `workspaces/run_harness.py::run`이
실제로 있다(기존 `v7_unwired`는 루트 파일이 없어 무엇이든 미도달이라 green 단계를 만들 수 없다).

1. **R1 도달**: 새 def가 모듈 최상위 바인딩의 값(dict 값)으로만 등록되고, 루트에서 도달하는 코드가 그 바인딩 이름을 참조하면 도달한다 -- 참조 형태 넷 모두:
   같은 파일 이름(`_REG[k]`), `from rt_engine import _REG_I`, 모듈 별칭 `rt_engine._REG_M`, 재수출(`rt_engine.py`의 `from rt_reg import _REG_R`를 하네스가
   `from rt_engine import _REG_R`로 읽음). exit 0, `unreached` 빈 목록.
2. **R1 미도달**: 아무도 참조하지 않는 바인딩의 값은 도달하지 않는다(하네스가 그 모듈을 import해도 -- R0 배제). 도달하지 않는 def만 참조하는 바인딩의 값도 도달하지
   않는다. exit 1, 그 def들이 `unreached_without_approval`.
3. **R2 도달**: 루트에서 도달하는 코드의 `Cls(...)` → `Cls.__init__`, `raise Cls`(호출 없이) → `Cls.__init__`, 자기 `__init__`이 없는 `Sub(...)` → 기반 클래스
   `Base.__init__`, `@dataclass` 클래스 호출 → `__post_init__`. exit 0.
4. **R2 미도달**: 클래스가 `isinstance(x, Cls)`·`except Cls:`·변수 주석에만 나오면 `Cls.__init__`은 도달하지 않는다. exit 1(Q1이 대안 (b)로 결정되면 이 계약은
   "이름 참조 전부가 생성자로 간다"로 바뀌고 해당 단계 기대가 exit 0이 된다 -- 결정 필요 항목).
5. **R3 누수 차단(이름)**: 엔진 `rt_area`가 속성 `a.rt_sz`를 쓰고, 새 엔진 def `rt_g`를 부르는 것이 `skills/analog-gmid-design/assets/tests/probes/p_rt.py::rt_sz`
   뿐이면 `rt_g`는 미도달이다. exit 1, `unreached_without_approval` = [`rt_engine.py::rt_g`].
6. **R3 누수 차단(test 파일 상수)**: 하네스가 이름 폴백으로 test 파일의 `_rt_rel`을 부르고, 그 test 파일의 최상위 바인딩 `_RT_NAMES = ("rt_h",)`가 새 엔진 def
   `rt_h`의 이름과 같아도 `rt_h`는 미도달이다(test 파일 노드를 따라가지 않는다). exit 1.
7. **바인딩 노드는 def가 아니다**: 새 def 없이 모듈 최상위 바인딩만 추가(`_RT_UNUSED = {"k": 1}`, 참조 없음) → exit 0, `new_defs` 빈 목록. 판정 JSON의 `new_defs`·
   `unreached`에 `::=` 노드가 나오지 않는다.
8. **면제·출력 형식 불변**: 계약 2의 미도달 def를 `target_kind: decision` 승인 기록(head 트리 `.ai/approvals/`, `target` = 그 def id)으로 면제하면 exit 0,
   `unreached`에는 남고 `unreached_without_approval`은 빈 목록. JSON 키(`tool`·`verdict`·`roots`·`roots_without_file`·`new_defs`·`unreached`·
   `unreached_without_approval`)와 exit 규칙(0 PASS / 1 FAIL / 2 실행 오류)은 그대로. 루트가 직접 부르는 새 def(대조군)는 exit 0.
9. **간선 단조성**: `build_graph`가 돌려주는 노드 집합은 def·`<module>`·`__main__`뿐이고(바인딩 노드는 간선 사전의 키로만), 옛 그래프의 모든 간선은 새 그래프에도 있다
   (R1·R2는 간선을 더하기만 한다. `<module>` 노드의 간선도 그대로). 따라서 V7에서 도달이 줄어드는 것은 R3 때문뿐이다 -- auditor가 HEAD 트리에서 두 그래프의 간선
   포함 관계를 잰다.
10. **V3 같은 그래프**: V3 합성 저장소 -- 새 `_metric_rt_x`(2배)가 `_RT_METRICS = {"x": _metric_rt_x}`로만 등록되고 새 `rt_compute(kind, v)`가 그것을 읽으며, test가
    `rt_compute("x", 3.0) == 6.0`을 단언한다 -- 에서 `mutate_changed.py`가 exit 0 `"verdict": "PASS"`(모든 변이 killed). `mutate_changed.py` 코드는 바뀌지 않는다.
11. **topology 무관·재계산 없음**: 게이트 소스에 회로·넷·소자 이름, `library/`·`.topology.json` 리터럴이 없고 `gate_config.json` 말고 JSON을 읽지 않는다. `build_graph`는 파일당
    `ast.parse` 1회이고 바인딩·클래스 색인을 같은 순회에서 만든다. 생성자 해석(기반 클래스 재귀)은 클래스당 한 번 계산해 재사용한다 -- auditor가 코드로 확인하고 HEAD
    트리의 `build_graph` 실행 시간을 base 도구와 함께 보고 수치로 적는다(임계값 없음).
12. **V3 비용 기록**(auditor 판정 기록의 보고 수치, 기준 약화 아님): 최근 판정 기록 1건(권장 `20260930-dup-w-calc`, V3 base·head는 그 기록 근거에서 읽는다)의 V3를 base 도구와
    병합본 도구로 같은 격리 복제본에서 돌려 verdict·mutants·killed·survivors·전체 실행 시간·인벤토리 크기(대상 def별)·최대 기준 실행 시간과 `--timeout`을 적는다. 병합본
    도구의 verdict가 base 도구보다 나쁘면(PASS → FAIL/ERROR) 원인을 적는다(새 인벤토리 test의 기준 실행 실패면 그 test id).
13. **문서**: design 05 §10 V7 행(321행)과 같은 절 거부 증명 줄(338행)을 아래 '문구 변경'대로 고친다(이 card의 문서 커밋). `reachability.py` 모듈 docstring의 그래프
    설명(10~13행)도 같은 뜻으로(code-author).
14. **무동작**: 기존 redteam 전체(`run_all.py --phase 0.5 --mode direct`)와 `--cases 0.5`의 케이스 판정이 base와 같다(새 케이스 32 제외 -- V7 `v7_unwired`, V3
    `v3_survivor`·`28-v3-gmid-options`·`31-v3-git-history` 포함). 과거 판정 기록 중 V7 근거에 `reachability.py … --base X --head Y`가 있는 기록 전부(작성 시점 27건·
    31쌍)의 각 쌍에서 base 도구와 병합본 도구의 `verdict`와 `unreached_without_approval`이 같다(`--config`는 head 트리의 것, 없으면 병합본의 것).

### 문구 변경(design 05 §10)

321행 옛 문구:
> | `reachability.py`(V7) | 배선 | 새 `def`가 `gate_config.json`의 `reachability_roots`에서 정적 호출 그래프(문자열 레지스트리 포함)로 도달하는지 |

새 문구:
> | `reachability.py`(V7) | 배선 | 새 `def`가 `gate_config.json`의 `reachability_roots`에서 정적 호출 그래프(문자열 레지스트리 포함)로 도달하는지. 그래프 간선 = 이름·속성 참조(기존), 모듈 최상위 이름 바인딩(dict 레지스트리 등)은 도달하는 코드가 그 이름을 참조할 때만(같은 파일·`from M import`·`M.NAME`, 재수출이면 같은 이름의 바인딩) 값 식이 참조하는 def로, 클래스 호출 `Cls(...)`·`raise Cls`는 그 클래스(없으면 기반 클래스)의 `__init__`·`__new__`·`__post_init__`로. import 문장 자체는 간선이 아니다. 도달 계산은 소스 분류 파일(`_is_source`, §4.3 소스의 `.py`) 노드 안에서만 따라간다 -- test·probe·workspace 스크립트의 def를 거친 도달은 세지 않는다. V3 인벤토리는 같은 그래프를 test 노드에서 출발해 쓴다(범위 제한 없음) |

338행 끝 옛 문구: `V7 → \`redteam/v7_unwired\`.` → 새 문구: `V7 → \`redteam/v7_unwired\`·공격 32(\`attacks/32-v7-registry-edges\`).`
(계획 121행 '운영 경로'와 N4.2 V7 행 843행은 바꾸지 않는다 -- 이 card는 게이트를 그 문구에 맞춘다.)

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

(엔진 신규 심볼 없음. `reachability.build_graph(files)`의 반환 모양 `(노드 집합, 간선 사전)`은 그대로이고 간선 사전에 `<파일>::=<이름>` 키가 더해진다. 게이트 안의 보조 함수
이름은 code-author가 정한다 -- `main`·`build_graph`가 부른다.)

## 판정 유형 근거

red-green: 새 redteam 케이스 `attacks/32-v7-registry-edges`의 red 단계 9개(아래 표 'base 도구' 열이 기대와 다른 것)가 base 도구에서 기대와 다르고 병합본 도구에서 같다.
사전 실측(7535799 도구 = base 도구, scratch 시제품 = 새 규칙): 단계 16개 전부 표의 두 열과 같게 나왔다. design 05 §18: ⑤ 뒤 게이트 변경은 spec card(red-green, oracle (a)).

## oracle 종류와 출처

(a) 구성: redteam `lib/rt.py`의 `vcase`(`build_vrepo` -- base 커밋 → head 커밋의 실제 이력, `--config`는 시험 대상의 `gate_config.json`)로 만드는 합성 저장소.
기대 exit·`unreached`·`new_defs`는 이 card 계약 문장에서 정한다(피검 도구 출력으로 만들지 않는다). 형식은 공격 31(`attacks/31-v3-git-history/`)과 같다 -- `expect.json`
(`layer`는 단계별 `tool`), `run.sh`(`rt vcase v.json`), `v.json`. 면제 승인 기록은 head 파일(`.ai/approvals/<id>.md`, `target_kind: decision`)로 넣는다(`approve_after_head`는
diff 승인 전용이라 쓰지 않는다). 레이어 V3 단계는 공격 31처럼 `subjects`를 둘지 test-author가 `rt.py` 동작으로 정한다.

`attacks/32-v7-registry-edges` 단계(공통 base = 계약 머리의 두 파일):

| 단계 | head 변경(요지) | base 도구 | 기대(새 도구) | 역할 |
|---|---|---|---|---|
| `registry-wired` | 새 `_f_b`, `_REG = {"b": _f_b}`, 새 `rt_pick(k)`가 `_REG[k]` 읽음, `run`이 `rt_pick` 호출 | exit 1 | exit 0 | red (계약 1) |
| `registry-imported` | 새 `_f_i`, `_REG_I = {"i": _f_i}`, 하네스 `from rt_engine import _REG_I` 후 `run`이 읽음 | exit 1 | exit 0 | red (계약 1) |
| `registry-modattr` | 새 `_f_m`, `_REG_M`, 하네스 `import rt_engine`, `run`이 `rt_engine._REG_M["m"]` | exit 1 | exit 0 | red (계약 1) |
| `registry-reexport` | 새 `rt_reg.py`(`_f_r`, `_REG_R`), `rt_engine.py`가 `from rt_reg import _REG_R`, 하네스가 `from rt_engine import _REG_R`로 읽음 | exit 1 | exit 0 | red (계약 1, Phase 3 재수출 대비) |
| `registry-orphan` | 새 `_f_c`, `_ORPHAN = {"c": _f_c}`, 참조 없음(하네스는 `rt_engine`을 import) | exit 1 | exit 1 | 거부 (계약 2, R0 배제) |
| `registry-dead-reader` | 새 `_f_d`, `_DEADREG`, 새 `_dead_reader`만 읽음(호출 0) | exit 1 | exit 1 | 거부 (계약 2) |
| `ctor-wired` | 새 `class RtBox: __init__`, `run`이 `RtBox(1.0)` | exit 1 | exit 0 | red (계약 3) |
| `ctor-raise` | 새 `class RtError(Exception): __init__`, 새 `rt_check`가 `raise RtError`(호출 없이), `run`이 `rt_check` | exit 1 | exit 0 | red (계약 3) |
| `ctor-inherited` | 새 `RtBase.__init__`, `class RtSub(RtBase): pass`, `run`이 `RtSub(1.0)` | exit 1 | exit 0 | red (계약 3) |
| `ctor-dataclass-post-init` | 새 `@dataclass class RtDev` + `__post_init__`, `run`이 `RtDev(-1.0)` | exit 1 | exit 0 | red (계약 3) |
| `ctor-isinstance-only` | 새 `RtOnly.__init__`, `run`은 `isinstance(v, RtOnly)`·`except RtOnly:`·주석 `v: RtOnly`만 | exit 1 | exit 1 | 거부 (계약 4, Q1) |
| `leak-test-name` | 엔진 새 `rt_area(a)`가 `a.rt_sz`, 새 `rt_g`는 `A/tests/probes/p_rt.py::rt_sz`만 호출, `run`이 `rt_area` | **exit 0** | exit 1 | red(거짓 PASS) (계약 5) |
| `leak-test-string` | 새 `rt_h`(호출 0), `A/tests/contracts/test_rt_names.py`에 `_RT_NAMES = ("rt_h",)`와 그것을 읽는 `_rt_rel`, `run`이 `_rt_rel("a")`(이름 폴백) | exit 1 | exit 1 | 거부 (계약 6 -- R1만 있고 R3가 없으면 exit 0이 되는 구성) |
| `approved-still-exempt` | `registry-orphan` + head `.ai/approvals/20260930-rt-v7-exempt.md`(`target_kind: decision`, `target: …/rt_engine.py::_f_c`) | exit 0 | exit 0 | 면제 불변 (계약 8) |
| `direct-call-control` | 새 `rt_twice`, `run`이 직접 호출 | exit 0 | exit 0 | 대조군 (계약 8) |
| `binding-not-a-def` | 새 def 없이 `_RT_UNUSED = {"k": 1}`만 | exit 0 | exit 0, `"new_defs": []` | 대조군 (계약 7) |
| `v3-registry-inventory` (tool V3) | 계약 10의 구성 | exit 1(생존 5, 인벤토리 없음) | exit 0 `"verdict": "PASS"` | red (계약 10) |

기대 표기: 미도달 def는 `message_contains`에 `"unreached_without_approval": ["skills/analog-gmid-design/assets/rt_engine.py::<qualname>"]` 모양으로(목록 전체가 한 def일 때)
적는다. 단계 이름·파일 이름의 `rt_` 접두는 기존 합성 케이스와 같다.

## 거부해야 할 입력

`registry-orphan`·`registry-dead-reader`(참조 없는 레지스트리 등록), `ctor-isinstance-only`(인스턴스를 만들지 않는 클래스 참조), `leak-test-name`(test·probe 파일 def만 부르는 새
엔진 def -- 지금 게이트가 통과시키는 입력), `leak-test-string`(test 파일 최상위 문자열로 엔진 def 이름을 적은 것) → 모두 exit 1. 기존 `v7_unwired` attack → exit 1 그대로.

## library 회로 적용 여부

해당 없음(게이트 도구). 게이트는 topology.json·library를 읽지 않는다(계약 11) -- topology.json `"function"` 문자열은 `_COMPENSATION_REGISTRY`의 키로만 코드에 닿으므로
R1이 덮는다(준비 자료 §1.3).

## 무동작 판정 입력(무발동 값)

계약 14: 기존 redteam 전체와 `--cases 0.5`, 과거 판정 기록의 V7 base·head 쌍 전부. 사전 미리보기(7535799 도구와 scratch 시제품, 준비 자료 §6 방식 재측정): 27건·31쌍에서
`verdict`·`unreached_without_approval` 모두 같음(전부 PASS, `--config`는 31쌍 모두 head 트리의 것). new_defs가 있던 쌍은 `20260922-ic3-completeness`(2)·
`20260930-df36-instance-relpath`(1)·`20260930-dup-w-calc`(1)·`20260930-restore-plan-functions`(2, 미도달 `lut_conditions_from_npz`·`derived_spec` 둘 다 양쪽에서 미도달이고 면제
승인으로 PASS)뿐 -- 새 규칙의 거부 동작 증명은 공격 32가 맡는다. auditor는 이 수치를 인용하지 않고 다시 잰다.

## 재현할 수치

없음(판정 경계가 아니라 그래프 규칙). 보고 수치(auditor, 판정 기록 `notes`): HEAD 트리 운영 루트 기준 미도달 소스 def 수(base 도구 / 병합본 도구, 합집합 루트와 두 벌 각각),
면제 승인 `20260930-restore-unwired-until-6a`의 두 id(`sizing_recipe.py::lut_conditions_from_npz`, `workspaces/run_harness.py::derived_spec`)가 병합본 도구에서도 미도달인지
(미도달이어야 면제가 계속 필요하다 -- 도달로 바뀌면 누수 여부를 경로로 확인), 계약 11·12의 시간·인벤토리 수치.

## 결정 필요 항목

**Q1 (사용자) R2 생성자 간선의 범위**
* (a) **호출 위치만**(권고): `Cls(...)`·`raise Cls`만 생성자로 간다. `isinstance`·`except`·주석은 인스턴스를 만들지 않으므로 간선 없음 -- 계약 4 거부 단계가 거짓 PASS를 막는다.
  대가: 클래스를 값으로 넘겨 다른 곳에서 인스턴스화하는 모양(`defaultdict(Cls)`, `{"k": Cls}` 등록, `field(default_factory=Cls)`)은 생성자가 미도달로 남아 거짓 FAIL이
  된다 -- 그때는 V7 면제 승인(`target_kind: decision`)으로 처리한다. 사전 실측: HEAD 엔진에 이 모양으로만 생성되는 클래스 0개((a)와 (b)의 HEAD 미도달 수가 39 = 39).
* (b) 이름 참조 전부: 클래스 이름이 도달 코드에 나오기만 하면 생성자로 간다(함수를 콜백으로 넘기는 것을 간선으로 보는 기존 def 규칙과 대칭). 팩토리 모양의 거짓 FAIL은 없지만
  `isinstance`·`except`만 쓰는 클래스의 생성자가 '도달'이 된다(거짓 PASS). (b)면 계약 4와 `ctor-isinstance-only` 기대가 exit 0으로 바뀌고, 대신 `ctor-factory`
  (`{"k": RtFac}` 등록 후 다른 곳에서 호출) green 단계를 둔다.
* 권고 이유: V7의 목적은 "만든 것이 실제로 쓰이는가"이고 거짓 PASS가 거짓 FAIL보다 비싸다(거짓 FAIL은 승인으로 드러나고, 거짓 PASS는 보이지 않는다). HEAD 차이 0이라
  (a)의 비용은 지금 없다.

**게이트 변경 승인(사용자)**: 승인 기록 `20260930-v7-registry-edges` -- 범위 = `tools/gates/reachability.py` 변경(R1·R2·R3), V3가 같은 그래프를 쓰는 데서 오는 인벤토리 변화
수용(계약 10·12), design 05 §10 V7 행·338행 문구 변경(위 '문구 변경'), Q1 선택. R1·R2를 `build_graph`에 두는 판단은 스펙('같은 그래프')에서 정해진다(의도 절) -- 사용자
결정 항목이 아니라 승인 범위의 설명이다.

순서: 이 card와 G1(`20260930-p3-gate-move-aware`)은 같은 파일(`reachability.py`)을 바꾸고 둘 다 redteam 번호 32를 예정했다. 판정 효과는 독립(G1 = 무엇이 새 def인가,
B33 = 무엇이 도달하는가)이므로 **먼저 병합하는 card가 32**, 나중 card는 `ls attacks`로 다음 번호를 쓰고 무동작 목록에 앞 card의 케이스를 더한다. 권고 순서는 B33 → G1
(준비 자료 §5: R3가 막는 거짓 PASS가 지금 모든 card의 V7에 걸려 있고, Phase 3 이동이 같은 이름 def를 늘려 누수 면이 커진다).

## 작성 전 실측

(2026-09-30, 저장소 HEAD 7535799, scratch `C:/g42` -- 시제품 `ext.py`는 HEAD `reachability.py` 사본 + R1·R2 스위치, 결과 파일은 삭제)
1. 사실 문장 재측정: `grep -n "def _refs\|def build_graph\|def reach\|def _is_source\|seen = reach\|new_defs = " tools/gates/reachability.py` → `_refs` 69, `build_graph` 97,
   `reach` 160, `_is_source` 175, `seen = reach` 223, `new_defs` 230행. `git show HEAD:tools/gates/mutate_changed.py | grep -n "build_graph\|rch.reach"` → 215행
   `inventory()`의 `rch.reach`, 317행 `rch.build_graph(head_files)`(준비 자료의 177·279행은 B28 병합 전 줄 번호 -- 옛 값). 시제품 재측정(HEAD 도구 = 준비 자료 값과 같음):
   미도달 115(합집합)·115/121(두 벌), R1+R2+R3 39(두 벌 모두), 비운영 노드 누수 64, 남은 39 = 준비 자료 (d) 38 + `size_transistor`. V3 인벤토리 33,991 → 79,809,
   인벤토리 0 82 → 14. 합성 단계 16개(V7)·1개(V3) base 도구 exit가 위 표와 같음.
2. 이름 충돌: `ls tools/gates/redteam/attacks` → 마지막 `31-v3-git-history` → 32(G1 초안도 32 예정 -- 결정 필요 항목 '순서'). `git grep -n "_is_source\|::=" -- tools/gates` →
   `_is_source`는 `reachability.py` 175·230행, `mutate_changed.py` 315행뿐, `::=` 0건(바인딩 노드 id가 기존 노드와 겹치지 않는다 -- `=`는 식별자 문자가 아니다).
   `run_all.py:55` 발견 규칙 = `attacks/*/expect.json`.
3. 원칙의 계약화: 회로 무관 -- 계약 11(`git grep -n "library/\|topology.json\|\.topology" -- tools/gates/reachability.py` → 0건, 변경 뒤에도 0건이어야 한다). 재계산 없음 --
   계약 11. 거짓 PASS 금지 -- 계약 2·4·5·6. 약화 없음 -- 계약 9·14.
4. 쓰기 경로: `tools/gates/reachability.py` = code-author(게이트 변경, 승인 기록), `tools/gates/redteam/attacks/32-*` = test-author, design 05 §10 문구 = 오케스트레이터 문서
   커밋. `mutate_changed.py`는 바꾸지 않는다.
5. 계획서 소비자: 지우거나 옮기는 이름 없음(`build_graph` 반환 모양 유지). `git grep -n "build_graph" -- tools hooks` → `mutate_changed.py` 317행(과 docstring 9행)뿐,
   `git grep -n "reachability" -- tools/gates/gate tools/gates/merge_gate.py tools/gates/integrity.py hooks .githooks` → 0건(설치 사본·merge gate가 V7을 부르지 않는다 -- 재설치 불필요).
   계획 121행·843행, design 05 317행(V3 ③ '같은 그래프')은 그대로 맞다.
6. 미배선: 게이트 안의 새 보조 함수는 `build_graph`·`main`이 부른다. 엔진 def 신설 없음.
7. 기존 test: `git grep -l "reachability\|mutate_changed" -- skills/analog-gmid-design/assets/tests` → 0건. redteam `v7_unwired`(exit 1)·`v3_survivor`·공격 28·31은 계약 14로
   불변 판정. 과거 판정 기록 V7 쌍: `.ai/verification/2026*.json` 중 정규식 `reachability\.py … --base X --head Y`가 맞는 기록 27건·31쌍(B28 기록 `20260930-v3-history-clone`은
   V7 N/A라 쌍 없음).
