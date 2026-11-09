---
id: 20260930-p3-gate-move-aware
phase: 0.5
evidence_type: red-green
gate_change: yes
approval: 20260930-p3-gate-move-aware
---
## 의도

design `30-module-split`(초안 v4) §5, card G1. 계획 N3.10 533행 "무변경 증명 = 이동 전후 함수별 `ast.dump`(docstring 제외) 해시 동일 + import 줄만 차이. **해시가 같은
함수는 V3 대상에서 뺀다**"가 게이트 도구에 구현돼 있지 않다. V3 `tools/gates/mutate_changed.py`는 같은 경로의 base 소스와만 비교하고(`changed_defs`, 88~100행; base 파일이
없으면 `None` → 전부 대상, 359·361·364행), V6 `source_lint.py`(`compare`, 212행)와 V7 `reachability.py`(`base_defs`/`new_defs`, 224~231행)도 같은 경로·(파일, qualname)
기준이다. 그래서 Phase 3 이동 card는 **바이트 그대로 옮긴 정의**를 새 정의로 보고 판정 불가가 된다 -- 엔진 4파일 전체 상한으로 V3 대상 def 473·변이 15,677,
V6 새 항목 861, V7 미도달 108(design v4 부록 A G1·G2). 합성 저장소에서 base V3·V6·V7 모두 exit 1(부록 A G5 `move-exact`).

고칠 방향: **판정식은 그대로 두고, 옮긴 단위의 비교 기준만 '같은 경로의 base'에서 '이동 원본'으로 바꾼다.** '옮긴 단위'는 design v4 §3 MOVED(M-0·M-0h·M-1~M-4)가 정하고,
이 card의 계약 1~3이 그 정의를 도구 계약으로 옮긴 것이다. 단위는 셋이다: 최상위 **함수**(`def_hash`), 최상위 **클래스 골격**(메서드 몸체를 이름 표지로 바꾼 ClassDef 해시 --
머리·데코레이터·클래스 수준 문장 포함), 최상위 **문장**(import·def·class·`if __name__` 블록 밖의 문장, `ast.dump` 해시). 메서드는 감싼 클래스 골격이 옮겨졌을 때만 옮긴 것이다.
이 규칙이 거부하는 것(부록 A G5·G5', 합성 단계 재실행 -- 1·2차 검토 반례 포함): 복사·래퍼 shim·모호 원본·두 목적지(초안 v2 M-1~M-3), **덮어쓰기**(M-0 -- 1차 B1),
**목적 파일의 조건부 재정의·재바인딩**(M-0h -- 2차 B1: `if FLAG: def f`, `f = (lambda …)(f)`, `f += …`, `except … as f`, star import), **자유 이름 재바인딩**·`__file__`·import 디렉터리
변경·`global` 쓰기 대상·`__future__` 차이(M-4 -- 1차 B2, 2차 S1·S3), **클래스 머리·필드 변경을 끼운 메서드 이동**(골격 단위 -- 1차 B3), **qualname이 겹치는 def**(property
getter/setter -- 2차 B1: 옮긴 def 목록에 넣지 않는다). 실제 엔진 4파일을 같은 디렉터리의 새 파일로 통째 옮긴 모의에서 거짓 거부 0(단위 402/402, def 473/473 인정, M-0h 위반 0 --
부록 A G6'), 판정 기록 2건(`df36`·`dup-w-calc`) base·head에서 옮긴 단위 0(G7).

해시 정의는 하나: `_strip_doc`·`def_hash`를 `reachability.py`로 옮기고 `mutate_changed.py`는 그것을 import해 같은 이름으로 둔다(`mutate_changed`가 이미 `reachability`를
import하므로 반대 방향이면 순환). 기존 판정 기록 스크립트가 `mc.changed_defs(base_src, head_src)`·`mc.def_hash`를 부르므로(스크립트 3개, 부록 A G4) 이름·시그니처·결과를 유지한다.
'모듈 전역에서 읽는 이름'과 '이름의 바인딩 출처'도 이 card가 `reachability.SourceIndex`에 한 번 정의하고(`global_names`·`binding_origin` -- 파일당 한 번 파싱), D0a(`move_plan.py`)가 그것을 재사용한다.

B28(`20260930-v3-history-clone`)과의 관계: B28은 **병합됐다**(code `dee338d` → 병합 `2b41e79`, 판정 기록 `8790b24`; 지금 gate `master` = `7535799`). B28은 V3의 **test 실행 환경**
(copytree → `make_clone` 격리 복제본 53·323행, 기준 실행 실패 → `ERROR` 398행, 임시 정리 `_rmtree_force` 406행)을 바꿨고, 이 card는 **대상 선택**(364행 `changed_defs` 호출 앞 이동 제외)과
판정 JSON 필드 추가만 바꾼다. 출력 키(`tool`·`verdict`·`targets`·`mutants`·`killed`·`survivors`, 407행; ERROR는 `error`·`baseline_failed`)는 B28 병합본에서도 같다. 이 card의 test worktree는
지금 gate `master`에서 만든다. B28의 계약 1~7은 이 card의 무동작 입력이다.

재설치: 바뀌는 파일은 §4.4 캐시에서 실행되는 auditor 도구뿐이고 설치 사본(gate `hooks/pre-receive`·`gate-runner.py`, `.claude/hooks/role_*`)이 아니다 -- design 05 §13.4
재설치 절차 불필요(B28과 같은 판단). 새 도구 동작은 이 변경이 반영된 뒤의 base 캐시부터 쓰인다.

## 관찰 가능한 계약

A = `skills/analog-gmid-design/assets`. '소스 파일' = `reachability._is_source`가 참인 경로(`A/*.py`, `workspaces/run_harness.py`).

0. **소스 색인** `reachability.SourceIndex(files)`: `files` = `{저장소 상대 경로: 소스}`(소스 파일이 아닌 경로는 무시). 파일마다 `ast.parse` 1회, `symtable` 1회(처음 필요할 때)만 하고
   아래 1~2의 결과를 파일 단위로 기억한다(같은 색인에서 같은 질의를 다시 파싱하지 않는다). `units(path)` = 최상위 단위 목록 `[(종류, 키, 해시, 바인딩 이름 집합)]`
   (종류 `def`·`class`·`stmt`, 해시는 3의 정의, 바인딩 이름은 1의 정의).
1. **이름의 바인딩 출처** `SourceIndex.binding_origin(path, name)`.
   **바인딩**(2차 검토 S2): 모듈 `path`의 **모듈 공간**(최상위와 최상위 `if`/`try`/`with`/`for`/`while`/`match` 몸체 -- def·class·lambda·컴프리헨션 몸체 제외)에서 이름이 `Store`·`Del` 문맥으로
   나오는 모든 곳(대입·주석 대입·증강 대입·walrus -- 컴프리헨션 안 walrus 포함·`for`/`with` 대상·`del`), import·`from … import`(블록 안 포함), def·class, `except … as n`, `match` 포획
   (`MatchAs`·`MatchStar`·`MatchMapping` rest), `type` 별칭. 판정 순서:
   * `__file__` → `("file-dir", <path의 디렉터리>)`. `__name__`·`__spec__`·`__loader__`·`__package__`·`__path__`·`__cached__`·`__builtins__`·`__dict__`·`__doc__`·`__annotations__` →
     `("module-identity", path)`.
   * `path`가 색인에 없으면 → 내장 이름이면 `("builtin", name)`, 아니면 `("unbound", name)`.
   * 모듈에 `from … import *`가 **하나라도** 있으면(위치·바인딩 유무와 무관) → `("star", path, name)`(2차 검토 S1 (c) -- 명시 바인딩 **뒤의** star가 이름을 가리는 경우).
   * 모듈 어디서든(함수 안 포함) `global name` 선언이 있으면 → `("global-dynamic", path, name)`(S1 (a) -- 실행 중에 다시 묶이는 이름. 경로를 붙여 옮기면 항상 다르다. 경로를
     `unbound` 전체에 붙이지 않는 이유: 문장 단위 전역 읽기가 컴프리헨션 변수를 넣던 v3 정의에서 SR 24단위가 거짓 거부됐다 -- 2차 검토 실측).
   * 바인딩이 둘 이상 → `("multi", path, name)`. 하나이고 def·class·대입·대상 모양 → `("def", path, name)`.
   * `from M import n [as name]`(level 0)이고 `path`와 같은 디렉터리의 `<M 마지막 성분>.py`가 색인에 있으면 → 그 파일에서 `n`의 출처(재귀, 깊이 20 넘으면 `("cycle", path, name)`),
     없으면 `("ext", <path의 디렉터리>, "<점 접두><M>", n)`. `import M [as name]` → `("module", <같은 디렉터리 파일>)` 또는 `("ext-module", <path의 디렉터리>, M)`
     (S1 (b) -- `sys.path[0]`이 가져오는 파일의 디렉터리라 같은 import 줄도 디렉터리가 다르면 다른 모듈일 수 있다).
   * 바인딩이 없으면: `globals`·`eval`·`exec` → `("module-identity", path)`, 내장 이름 → `("builtin", name)`, 그 밖 → `("unbound", name)`.
2. **모듈 전역에서 읽는 이름** `SourceIndex.global_names(path)` → `{단위 키: frozenset(이름)}`. 단위 키 = 최상위 함수·클래스 이름, 최상위 문장은 `"<stmt:" + 해시 앞 12자 + ">"`.
   함수·클래스 단위 = `symtable`로 그 단위와 그 안의 모든 하위 유효 범위(중첩 def·lambda·컴프리헨션·메서드·중첩 클래스)에서 `is_global()`이고 참조되거나 대입되는 이름
   ∪ 모듈 공간에서 평가되는 데코레이터·기본값·기반 클래스·키워드 인자의 `Name` ∪ 단위 안 모든 주석(평가형과 **문자열형**; 문자열은 `ast.parse(mode="eval")`, 실패하면
   식별자 토큰)의 이름. **문장 단위**도 같은 유효 범위 규칙(2차 검토 S2): 문장 안 `Name`(Load) 중 lambda 인자·컴프리헨션 대상(첫 `iter`는 바깥 유효 범위)·문장 안 중첩 def의 지역이
   아닌 것 ∪ 주석의 이름(Python 3.12+ `symtable`은 인라인 컴프리헨션 변수를 모듈 표의 지역으로 넣으므로 -- 3.14 실측 `X = [t*K for t in range(3)]`에서 `t`가 모듈 표에 있다 -- 문장
   단위는 AST 유효 범위로 센다). 지역 이름이 모듈 최상위 이름과 같아도 지역이면 넣지 않는다.
3. **옮긴 단위** `reachability.moved_defs(base, head)`: 두 인자는 `read_tree` 모양의 사전이거나 이미 만든 `SourceIndex`(사전이면 안에서 색인을 만든다). B = base 색인, H = head 색인.
   단위 해시: 함수 = `def_hash`, 클래스 = **골격 해시**(ClassDef 사본에서 클래스 안의 모든 def -- 메서드와 중첩 클래스의 메서드 -- 를 `<method 이름>` 표지 문장으로 바꾼 뒤 `def_hash`;
   머리·데코레이터·기반·키워드·클래스 수준 문장·메서드 이름과 순서가 들어가고 메서드 몸체는 빠진다), 문장 = 그 문장의 `def_hash`(`ast.dump(include_attributes=False)`).
   head 소스 파일 p_h의 최상위 단위 u(종류 k, 키 q -- 문장은 키 없이 해시로만 식별, 해시 h)가 **옮긴 단위**인 것 ⇔ 다음이 모두 참:
   * (M-1) base 소스 파일 중 (k, q, h) 단위를 가진 파일이 정확히 하나 p_b이고 p_b ≠ p_h, 그 파일 안에서도 한 번(base p_h가 같은 (k, q, h)를 가지면 무변경이지 이동이 아니다).
     한 파일 안에 같은 문장 해시·같은 q가 둘이면 모호 = 이동 아님.
   * (M-0) u가 바인딩하는 이름 n마다 `B.binding_origin(p_h, n)`이 `unbound`·`builtin`이거나 `("def", p_b, n)`이다 -- **p_h가 base에서 이미 다른 것을 그 이름으로 가리켰으면 이동
     아님**(덮어쓰기).
   * (M-0h) u가 바인딩하는 이름 n마다 `H.binding_origin(p_h, n)` = `("def", p_h, n)`이다 -- **목적 파일에서도 u가 그 이름의 유일한 바인딩**(2차 검토 B1 (1)의 M-0'). 목적 파일의
     조건부 재정의(`if FLAG: def f`)·def 없는 재바인딩(`f = (lambda g: …)(f)`, `f += …`, `del f`, `except … as f`)·star import·`global f`가 있으면 `multi`·`star`·`global-dynamic`이 되어 이동 아님.
   * (M-2) head p_b에 같은 (k, q)(문장은 같은 h)의 단위가 없고, u가 바인딩하는 이름 n마다 `H.binding_origin(p_b, n)`이 `unbound`·`builtin`이거나 `("def", p_h, n)`이다(원본 자리에
     남는 것은 p_h를 가리키는 재수출뿐).
   * (M-3) head 소스 파일 전체에서 (k, q, h) 단위가 p_h 한 곳에만 있다.
   * (M-4) p_b와 p_h의 `from __future__ import` 기능 집합이 같고(2차 검토 S3 -- `annotations`가 빠지면 주석이 문자열 → 평가값으로 바뀐다), `H.global_names(p_h)[u]`의 이름 v마다
     `B.binding_origin(p_b, v)` = `H.binding_origin(p_h, v)`이거나, head 출처가 `("def", p', v')`이고 (p', v')가 **이 호출에서 옮긴 단위로 인정된** 것이 바인딩하는 이름이며 그 원본 출처
     (`("def", 원본 파일, v')`)가 base 출처와 같다. M-4는 고정점으로 판정한다(함께 옮긴 것이 거부되면 그것에 기대던 것도 다시 판정).
   * 클래스 단위의 메서드(와 그 안 중첩 def)는 클래스 골격이 옮긴 단위이고 **자기 `def_hash`가 base p_b의 같은 qualname과 같을 때만** 옮긴 def다. 함수 단위 안의 중첩 def는 함수와 함께
     옮긴 def다(해시가 몸체를 덮는다). 최상위 블록(`if`/`try`) 안의 def는 옮긴 def가 아니다(보수적).
   * **qualname 중복 제외**(2차 검토 B1 (2)): `iter_defs` 기준으로 p_b 또는 p_h에서 qualname이 둘 이상인 def(`@property def x` + `@x.setter def x`, 조건부 재정의)는 옮긴 def에 넣지 않는다
     (단위 자체는 옮긴 단위일 수 있다 -- 그 안의 겹치는 def만 V3·V7 대상에 남는다).
   반환 `{"units": {"<p_h>::<q>": "<p_b>::<q>"}, "defs": {"<p_h>::<qualname>": "<p_b>::<qualname>"}, "def_hashes": {"<p_h>::<qualname>": "<def_hash>"}, "rejected": {"<p_h>::<q>": {"rule":
   "M-0|M-0h|M-1|M-2|M-3|M-4", "detail": [문자열…]}}}`. `defs`의 키 모양은 `iter_defs` qualname(V3·V7의 노드 id와 같다), `def_hashes`는 그 def의 head `def_hash`. `rejected`에는 (k, q, h)가
   같은 원본이 base에 **있지만** 규칙 하나에 걸린 후보만 들어간다. 순수 함수(입력 불변).
4. **V3**: 변이 대상에서 빼는 def는 `(경로, qualname, def_hash)`가 `moved_defs`의 `defs` 키·`def_hashes` 값과 **모두** 맞는 것뿐이다(2차 검토 B1 (3) -- 키만 같고 해시가 다른 def는 대상).
   나머지 대상 선택은 지금과 같다(같은 입력에서 `changed_defs`와 같은 결과, base 파일 읽기 방식도 그대로). 판정 JSON에 세 키를 더한다: `"defs"`(변이 대상이 된 def의
   `"<경로>::<qualname>"` 목록, 대상 선택 순서), `"moved"`(`[{"from": …, "to": …}]`, `defs` 사전 그대로), `"move_rejected"`(`rejected` 그대로). 기존 키(`tool`·`verdict`·`targets`·`mutants`·
   `killed`·`survivors`, B28의 ERROR `baseline_failed`)는 이름·뜻을 바꾸지 않는다.
5. **V6**: 옮긴 def 단위의 '이전 항목 수'는 원본 단위를 **원본 파일 맥락**(원본 파일 전체 텍스트 -- `len(` 검사·`# derive:` 태그 포함)에서 센 값이다. 새 파일 `<module>` 단위의 이전
   항목 수 = (base 같은 경로 `<module>` 값) + (그 파일로 옮긴 문장 단위 각각을 **원본 파일 맥락**에서 센 항목 중 그 문장의 줄 범위에 든 것의 수). 현재 항목 수는 지금처럼 **새 파일
   맥락**에서 센다 -- 늘면 FAIL. 판정 JSON에 `moved`·`move_rejected`.
6. **V7**: `new_defs`에서 빼는 def는 계약 4와 같은 `(경로, qualname, def_hash)` 대조로 정한다. 판정 JSON에 `moved`·`move_rejected`.
7. **이동이 아닌 것**(지금과 같은 판정, 부록 A G5·G5' 단계 이름): (a) 옮기며 토큰 하나라도 바뀐 정의(`move-edited`) (b) 복사 -- 원본 자리에 남음(`copy`, M-2) (c) 래퍼 shim(`wrapper`, M-2)
   (d) 모호한 원본(`ambiguous`, M-1) (e) 두 목적지(`two-targets`, M-3) (f) **덮어쓰기** -- 목적 파일이 base에서 같은 이름을 정의(`overwrite`) 또는 다른 모듈에서 import(`overwrite-import`)
   (M-0) (g) 두 파일 def 교환(`swap`, M-0) (h) **자유 이름 재바인딩** -- 옮긴 def가 읽는 이름을 목적 파일이 다른 정의에 묶음(`rebind`, M-4) (i) `__file__`을 읽는 def를 다른
   디렉터리 소스 파일로(`file-dir-change-noshim`, M-4) (j) 클래스 머리(`class-header-changed`)·클래스 수준 문장(`class-field-changed`)을 바꾸며 옮김(골격 해시 다름 → 메서드도 대상)
   (k) **목적 파일의 조건부 재정의**(`dest-conditional-redef`, M-0h) (l) **목적 파일의 def 없는 재바인딩**(`dest-lambda-rebind`·`augassign-rebind`·`except-as-rebind`, M-0h)
   (m) **옮긴 클래스의 property getter 본문 변경**(`property-getter-changed` -- 골격은 같아 클래스는 옮긴 단위지만 겹치는 qualname이라 `P.x`는 옮긴 def가 아님)
   (n) **star import가 함께 옮긴 이름을 가림**(`star-shadow`, M-0h) (o) **`global`로 쓰이는 이름을 읽는 def만 옮김**(`global-reader`, M-4) (p) **같은 import 줄이지만 디렉터리가 다른
   소스 파일로**(`ext-dir-change`, M-4) (q) **목적 파일에 `from __future__ import annotations` 누락**(`future-dropped`, M-4).
8. **정의 하나·호환**: `reachability.def_hash`가 유일한 정의이고 `mutate_changed.def_hash is reachability.def_hash`. `mutate_changed.changed_defs(base_src, head_src)`의 시그니처와 반환이
   base와 같다. `move_plan.py`(D0a)가 쓸 `SourceIndex`(`units`·`global_names`·`binding_origin`)는 `moved_defs`가 쓰는 바로 그 클래스다.
9. **topology 무관**: 바뀐 게이트 소스에 `library/`·`.topology.json`·회로·넷·소자 이름 리터럴이 없고, 모든 판정이 회로 없는 합성 저장소에서 성립한다.
10. **재계산 없음**(NFR-2): 한 도구 실행에서 `moved_defs` 호출 1, `read_tree` 호출은 V3 ≤ 2(head 그래프 + base 소스), V6 ≤ 2(base·head 소스), V7 = 2(지금과 같음). `moved_defs`
    입력은 소스 파일만(`SOURCE_GLOBS`로 읽거나 이미 읽은 사전을 `_is_source`로 걸러서). `moved_defs` 안에서 파일마다 `ast.parse` 1회·`symtable` 1회. auditor는 합성 저장소 실행을
    `cProfile`로 돌려 함수별 호출 수(`ncalls`)로 확인한다(인자 구별은 필요 없다).
11. **무동작**: 기존 redteam V3·V6·V7 케이스(`v3_survivor`, `v7_unwired`, `attacks/09-v6-broad-except`, `26-gate-output-utf8`, `27f-v6-reconfigure-except`, `28-v3-gmid-options`,
    `31-v3-git-history`)와 `run_all.py --phase 0.5 --mode direct`·`--cases 0.5` 전 케이스의 판정(exit·verdict)이 base와 같다. 새 키는 추가만이라 기존 기대의 필드 대조는 그대로 성립한다.
12. **새 redteam 케이스** `tools/gates/redteam/attacks/32-moved-defs/`(번호 배정 design v4 D-18: G1 = 32, B33 = 33 -- 마지막 `31-v3-git-history`): `lib/rt.py vcase` 합성
    저장소. 모든 단계의 공통 픽스처 성질: 옮기는 def는 **인벤토리 test 없음**(`tests/` 없음), **운영 루트 미도달**(루트 = `workspaces/run_harness.py::run2`, 옮기는 def를 부르지 않음),
    몸체에 **리터럴 3.7과 `except Exception`**(V6 magic_number·broad_except의 원천 -- `property-getter-changed`·`star-shadow`·`future-dropped`는 구성 칸에 적은 대로). 기대 exit(base 도구 → 병합본 도구):

    | 단계 | 구성(base → head) | V3 | V6 | V7 | `moved` / `move_rejected` |
    |---|---|---|---|---|---|
    | `move-exact` | `a.py::f` → `b.py::f` 바이트 그대로, `a.py`는 `from b import f`만 | 1 → **0** | 1 → **0** | 1 → **0** | `b.py::f ← a.py::f` / 없음 |
    | `absorb-own-import` | base `b.py`가 `from a import f`, head `b.py`에 f 정의(같은 본문), `a.py`는 `from b import f` | 1 → **0** | 1 → **0** | 1 → **0** | `b.py::f` / 없음 |
    | `move-together` | `helper`·`g`(helper를 부름)를 함께 `b.py`로 | 1 → **0** | 1 → **0** | 1 → **0** | 둘 다 / 없음 |
    | `move-chain` | base에서 helper는 이미 `m1.py`(원본 `a.py`는 재수출), g를 `m2.py`로(`from m1 import helper`) | 1 → **0** | 1 → **0** | 1 → **0** | `m2.py::g` / 없음 |
    | `local-shadow` | g의 지역 이름 `helper`가 원본 최상위 `helper = 7`과 같음, 목적 파일엔 최상위 helper 없음 | 1 → **0** | 1 → **0** | 1 → **0** | `b.py::g` / 없음 |
    | `class-exact` | 클래스 `C(Base)`(클래스 필드 3.5, 메서드 m)와 `Base`를 바이트 그대로 | 1 → **0** | 1 → **0** | 1 → **0** | `b.py::C.m` / 없음 |
    | `cache-together` | `_X_CACHE = {}`와 `len(_X_CACHE)` 검사 함수 g를 함께(리터럴 3.5가 g 안) | 1 → **0** | 1 → **0** | 1 → **0** | `b.py::g` / 없음 |
    | `move-edited` | 옮기며 3.7 → 3.8 | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / 없음 |
    | `copy` | 원본 남김 | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-2 |
    | `wrapper` | 원본 자리에 `def f(x): return _bf(x)` | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-2 |
    | `ambiguous` | base `a.py`·`c.py`에 같은 f | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-1 |
    | `two-targets` | head `b.py`·`d.py`에 같은 f | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-3(b), M-2(d) |
    | `overwrite` | base `b.py::f`(다른 본문, 리터럴·except 없음) → head `b.py::f` = `a.py::f` 본문 | 1 → 1 | 1 → 1 | 0 → 0 | 없음 / M-0 |
    | `overwrite-import` | base `b.py`가 `from c import f`(다른 본문) | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-0 |
    | `swap` | `a.py::f`·`b.py::f` 본문 교환 | 1 → 1 | 1 → 1 | 0 → 0 | 없음 / M-0(둘 다) |
    | `rebind` | g를 옮기며 목적 파일이 `from c import helper`(원본 helper와 다른 정의) | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-4 |
    | `file-dir-change-noshim` | `__file__`을 읽는 def를 `workspaces/run_harness.py`로(원본 자리 재수출 없음) | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-4 |
    | `class-header-changed` | 옮기며 `class C(Base)` → `class C(Other)` | 1 → 1 | 1 → 1 | 1 → 1 | `C.m` 없음 / 없음 |
    | `class-field-changed` | 옮기며 클래스 필드 3.5 → 4.5 | 1 → 1 | 1 → 1 | 1 → 1 | `C.m` 없음 / 없음 |
    | `cache-split` | `_X_CACHE = {}`만 옮기고 `len()` 검사 함수는 원래 파일 | 0 → 0 | 1 → 1 | 0 → 0 | 없음(문장 단위만 인정) / 없음 |
    | `dest-conditional-redef` | f를 `b.py`로 옮기고(원본 자리 재수출 없음 -- 호출자 갱신 모양) `b.py` 끝에 `FLAG = True` + `if FLAG: def f(x): return -x` | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-0h(`b.py::f`) |
    | `dest-lambda-rebind` | 같은 이동 + `b.py` 끝에 `f = (lambda g: (lambda x: -g(x)))(f)` | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-0h |
    | `augassign-rebind` | `move-exact` + `b.py` 끝에 `f += 0` | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-0h |
    | `except-as-rebind` | `move-exact` + `b.py` 끝에 `try: pass` / `except Exception as f: pass` | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-0h |
    | `property-getter-changed` | 클래스 `P`(`@property x` getter `return self._x * 3.7` + `@x.setter`, except 없음)를 옮기며 getter만 3.7 → 4.7 | 1 → 1 | 0 → 0 | 1 → 1 | `P.x` 없음(qualname 중복 제외) / 없음 |
    | `star-shadow` | `helper()→2`·`g(x): return helper() * x`(리터럴·except 없음)를 함께 `b.py`로, `b.py` 끝에 `from c import *`(`c.helper()→5`) | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-0h(helper·g 둘 다 -- star 모듈의 모든 이름 출처가 `star`) |
    | `global-reader` | `setx(v): global X; X = v`는 남기고 `g(y): … X / 3.7 …`만 `b.py`로 | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-4 |
    | `ext-dir-change` | `A/a.py`의 `from wsutil import h`를 쓰는 g를 `workspaces/run_harness.py`로(같은 import 줄, `workspaces/wsutil.py`는 소스 아님, 원본 자리 재수출 없음) | 1 → 1 | 1 → 1 | 1 → 1 | 없음 / M-4 |
    | `future-dropped` | `from __future__ import annotations`가 있는 `a.py`의 `@dataclasses.dataclass class Rec: a: float = 2.5`를 future 없는 `b.py`로 | 0 → 0 | 0 → 0 | 0 → 0 | 없음 / M-4(`__future__`) |

    red = `move-exact`·`absorb-own-import`·`move-together`·`move-chain`·`local-shadow`·`class-exact`·`cache-together`(base 도구 exit 1). 나머지 22단계는 거부 단계(base = 병합본). V6의 exit를
    만드는 원천은 리터럴·광범위 except이고, `cache-split`만 `unbounded_cache`다(`cache-together`의 base red는 캐시가 아니라 g 안의 리터럴 3.5에서 나온다 -- `source_lint`의 `len(` 검사는
    파일 전체 텍스트를 본다, 129행). `future-dropped`는 exit로는 base와 병합본을 구별하지 못하므로(메서드 없는 dataclass -- V3·V6·V7이 원래 보지 않는다) **관찰로만** 판정한다.
    **관찰 방식**(2차 검토 m7): `v.json` 단계에 `"observe": "moved"`를 두면 `lib/rt.py`의 `vcase`가 도구 JSON에서 `{"moved": [<to> …](정렬), "move_rejected": {<키>: <rule>}}`을 뽑아
    `observed`로 기록하고, `expect.observed_equals`(`run_all.py` 98행의 기존 대조)로 기대와 비교한다. 모든 거부 단계와 red 단계가 이 관찰을 쓴다(규칙 이름까지 대조). `rt.py`의 이 선택 관찰
    추가는 test-author 몫(B28의 `tool_tmpdir`·`root_state` 선례, 599~621행). `move-edited`·`class-*`·`property-getter-changed`는 해시가 같은 원본 단위가 없거나 단위는 옮겨졌으므로
    `move_rejected`에 들지 않는다.
13. 문서(오케스트레이터, **이 spec card와 같은 커밋 -- 승인 전**): design 05 §10 V3 행 ①·V6 행·V7 행에 "옮긴 단위(design 30 §3 MOVED)는 이동 원본과 비교"를 더하고, 계획 N3.10 533행
    끝에 "V6·V7의 '새'도 같은 규칙(옮긴 단위는 이동 원본과 비교, 옮긴 단위의 정의는 design 30 §3)" 한 문장을 더한다. 승인 기록(`target_kind: diff`)의 `diff_path`는 이 spec card·
    design 05·계획서 세 경로를 덮는다(B28 승인 기록 선례: spec card와 design 05 두 경로). 도구 모듈 docstring도 같은 뜻(code-author).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `reachability` | `moved_defs` | `def moved_defs(base, head) -> dict` (`base`·`head` = `dict` 또는 `SourceIndex`) |
| `reachability` | `SourceIndex` | `class SourceIndex: def __init__(self, files: dict)` |
| `reachability` | `SourceIndex.units` | `def units(self, path: str) -> list` |
| `reachability` | `SourceIndex.global_names` | `def global_names(self, path: str) -> dict` |
| `reachability` | `SourceIndex.binding_origin` | `def binding_origin(self, path: str, name: str) -> tuple` |
| `reachability` | `def_hash` | `def def_hash(fn) -> str` |

## 판정 유형 근거

red-green: 계약 12의 red 단계 7개가 base 도구에서 exit 1(부록 A G5에서 base 도구를 실제로 실행해 확인 -- v4 재측정 `p3v4_g1_results.json`에서도 같음), 병합본 도구에서 exit 0.
design 05 §18 "⑤ 뒤 게이트 변경은 spec card로 한다(red-green, oracle (a))". 게이트 코드(`tools/gates/`, redteam 제외)를 바꾸므로 `gate_change: yes`와 승인 기록이 필요하다.

## oracle 종류와 출처

(a) 구성: 합성 저장소(redteam `lib/rt.py`의 `build_vrepo`·`vcase` -- base 커밋 → head 커밋의 실제 이력)에 계약 12 단계를 손으로 만든다. 기대 exit·`moved`·`move_rejected` 규칙
이름은 이 card 계약 문장이 정한다(피검 도구 출력으로 만들지 않는다). `moved_defs`·`binding_origin`·`global_names`의 단위 판정도 합성 `{경로: 소스}` 사전으로.

## 거부해야 할 입력

계약 7 (a)~(q)와 `cache-split`: 이동으로 보지 않고 지금처럼 판정. 판정기 자기 점검: `moved_defs`가 소스 파일 밖(`A/tests/**`, `tools/**`, `A/<하위 디렉터리>/**`)의 단위를 담으면 안 된다.
`binding_origin`이 알 수 없는 바인딩 모양을 만나면 이동 쪽으로 판정하지 않는다(`multi`·`star`·`global-dynamic`·`cycle`은 경로를 담으므로 원본·목적이 다르면 M-4에서 항상 불일치,
목적 파일에서는 M-0h가 거부). 알려진 보수 비용: 바이트 그대로 옮긴 property 클래스의 `P.x`도 qualname 중복이라 V3·V7 대상에 남는다(`p3v4_g1_results.json` `P-property-exact`:
V3/V7 1) -- 엔진 4파일 qualname 중복 0이라 Phase 3 노출 0.

## library 회로 적용 여부

해당 없음(게이트 도구). Phase 3 M card 판정의 V3·V6·V7 `moved` 목록이 실제 적용이다(design v4 §8 M행·§10 E2).

## 무동작 판정 입력(무발동 값)

계약 11: 기존 redteam 전체와 `--cases 0.5`. 이동이 없는 base·head 쌍에서 `moved`·`move_rejected`가 비고 판정이 base 도구와 같다 -- auditor가 최근 판정 기록 2건
(`20260930-df36-instance-relpath` 070cf69→ed98d35, `20260930-dup-w-calc` b7d1798→a9de49c)의 base·`code_commit`으로 확인(초안 측정: 둘 다 빈 결과, 부록 A G7 -- v4 규칙으로도 같음).

## 재현할 수치

없음(보고 수치는 auditor 판정 기록에서만 인용한다).

## 결정 필요 항목

게이트 변경 승인(design v4 §9.2 UD-5) -- 승인 기록 `20260930-p3-gate-move-aware`(날짜는 승인일로). UD-5에는 **이동 인식 방식의 비용 선택**(전역 규칙 = 이 card / 승인 기록에
선언된 이동만 인정)이 함께 걸려 있다 -- 권고는 전역 규칙(design v4 §9.2, 근거는 v4 재측정 수치). 계획 N3.10 533행 문장 추가와 design 05 §10 개정도 같은 승인이 덮는다(계약 13).

## 작성 전 실측

(기준 gate `master` `7535799` -- B28 병합 `2b41e79` 뒤. 그 사이 `tools/gates`가 바뀌면 1·2를 다시 잰다)
1. 사실: `grep -n 'diff", "--name-only\|make_clone\|cat-file\|changed_defs\|rmtree\|json.dumps\|def def_hash\|def _strip_doc\|base_src' tools/gates/mutate_changed.py` →
   `make_clone` 53(정의)·323(호출), `_rmtree_force` 61·406, `_strip_doc` 74, `def_hash` 84, `changed_defs` 88~100, diff 314, cat-file 359, `base_src` 361, `changed_defs` 호출 364,
   출력 398·402(ERROR)·407(PASS/FAIL). `copytree` 없음(B28이 `make_clone`으로 바꿈). 출력 키 `tool, verdict, targets, mutants, killed, survivors`(ERROR `tool, verdict, error` + `baseline_failed`).
   `grep -n "base_defs\|new_defs = " tools/gates/reachability.py` → 224·227·230·231. `grep -n "^def compare\|findings += compare\|module_text" tools/gates/source_lint.py` → 212·268·102·129.
   `grep -n 'add_parser("vcase")\|tool_tmpdir\|root_state\|observe' tools/gates/redteam/lib/rt.py` → vcase 1351, 선택 관찰 599~621(`v4_first`·`tool_tmpdir`·`root_state`),
   `run_all.py:98` `observed_equals` 대조.
   반례·모의: `$PY -B wt/_drafts/p3v4_g1_measure.py` → `p3v4_g1_results.json`(v3 27단계 + 2차 검토 새 반례 24단계, 단계마다 HEAD 게이트 도구 실제 실행, v3·v4 규칙 나란히, D0a `check`
   발견 모의, 실제 엔진 통째 이동, 판정 기록 2건).
2. 이름 충돌: `ls tools/gates/redteam/attacks` → 마지막 `31-v3-git-history` → **32**(B33 준비 `wt/_drafts/prep_b33_v7_edges.md` 278행은 "G1 32 예정이면 그 다음" → B33 = 33, design v4 D-18).
   `run_all.py:55` 발견 규칙 = `attacks/*/expect.json`. `git grep -n -E "moved_defs|SourceIndex|global_names|binding_origin|move_rejected|global-dynamic" -- tools docs/01-plan docs/02-design` → 0건.
3. 원칙: 약화 금지 -- 계약 3·7·12(거부 단계 22개), topology 무관 -- 계약 9, 재계산 없음 -- 계약 10, 정의 하나 -- 계약 8, 만들면 배선 -- 계약 4~6(세 `main`이 부른다)·D0a가
   `SourceIndex`를 부른다.
4. 쓰기 경로: `tools/gates/{reachability,mutate_changed,source_lint}.py` = code-author(게이트 변경, 승인 기록 필요), `tools/gates/redteam/**`(`attacks/32-moved-defs/`, `lib/rt.py`의 `observe: "moved"`)
   = test-author(게이트 변경), design 05 §10·계획 N3.10 533행 = 오케스트레이터(이 spec card와 같은 커밋).
5. 계획서 소비자: 바꾸는 이름 없음(추가만). 게이트 밖 호출: `git grep -n "def_hash\|changed_defs" -- . ':!*.jsonl'` → `.ai/verification/20260930-df36-instance-relpath/scripts/mut_def.py:67`,
   `probe_t2_vs_1st_survivor.py:16`, `.ai/verification/20260930-dup-w-calc/scripts/v3_baseline_probe.py:17` -- 계약 8로 호환.
6. 미배선: 새 def `moved_defs`는 세 도구 `main`이, `SourceIndex`는 `moved_defs`와 D0a가 부른다. V7 검사 범위(`A/*.py`·`run_harness.py`) 밖이라 면제 승인 불필요.
7. 기존 계약 test: `git grep -l -E "mutate_changed|reachability|source_lint" -- skills/analog-gmid-design/assets/tests` → 0건. 기존 redteam V3·V6·V7 케이스는 계약 11로 불변 판정.
8. 엔진 사실(단위 규칙의 전제, `p3v4_g1_results.json` `engine_facts`·2차 검토 부록 A): 엔진 4파일에 star import 0, `global` 문 0, `__name__`·`globals()`·`sys.modules` 읽기 0, `__file__` 2곳
   (`stick_diagram.py:1050`·`:8973` -- 같은 디렉터리 MOD 파일로 옮기면 `file-dir` 출처가 같아 인정), 최상위 이름 중복 바인딩(`multi`) 0, `iter_defs` qualname 중복 0,
   `from __future__ import annotations` SR 35·SD 32·TL 24행(DR 없음 -- 새 MOD 파일은 원본의 future 줄을 가져야 M-4 통과), 클래스 41(메서드 없는 클래스 36, dataclass 36, 예외 3).
