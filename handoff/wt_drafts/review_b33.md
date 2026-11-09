# 독립 검토 -- `_drafts/draft_b33.spec.md` (20260930-v7-registry-edges)

검토자: 독립 reviewer(작성자 아님). 저장소 읽기 전용(HEAD 7535799), scratch `C:/g55`(끝나고 삭제).
측정 도구: HEAD `tools/gates/reachability.py` 사본(`rch_base.py`) + 초안 문장대로 R1·R2·R3를 구현한 reviewer 시제품 `ext.py`
(작성자 시제품 `C:/g42`는 열지 않았다 -- 초안 **문장**에서 독립적으로 구현). 변형 플래그로 아래 결함·수정안을 각각 켜고 껐다.
아래 수치는 검토용 실측이고 판정 기록 수치가 아니다.

---

## 0. 요약

| 등급 | 건수 | 핵심 |
|---|---|---|
| **blocking** | 3 | B1 R2가 기존 `super().__init__` 속성 폴백을 깨워 **모든 새 `__init__`이 도달**(실저장소에서 계약 4가 거짓) · B2 R1 재수출 폴백이 외부 모듈 속성(`math.pi`)에도 걸림 · B3 17단계가 해석 형식을 고정하지 못함(느슨한 구현이 17단계 전부 통과하면서 속성·문자열 동명 바인딩으로 거짓 PASS) |
| **should-fix** | 6 | S1 바인딩 값 안 문자열 상수(str 규칙)가 V3 인벤토리 증가의 대부분이고 V7 거짓 PASS 면 · S2 함수 지역 변수 가림 · S3 재수출 폴백이 같은 이름 바인딩 전체로 · S4 계약 12 측정 대상(dup-w-calc)이 부적절, timeout-kill 관찰 없음 · S5 계약 9 문구(바인딩 노드는 '키로만'이 아님)와 수정 시 단조성 조정 · S6 redteam 번호 충돌 |
| **minor** | 5 | red 단계 수 9 vs 10 · 바인딩 값 안 생성자 호출 범위 미명시 · 하네스 최상위 코드가 `__main__` 루트로 도달한다는 작성 주의 · Q1 (a)의 거짓 FAIL 모양 기록 · 측정 시간 수치 |

사실 재측정: 초안의 줄 번호·수치는 전부 재현됐다(§4). 무동작 27건·31쌍 재판정은 §4.3.

---

## 1. blocking

### B1. R2가 기존 `__init__` 속성 폴백을 활성화 -- 실저장소에서 아무도 만들지 않는 클래스의 `__init__`도 '도달'

* 근거: HEAD `sizing_recipe.py:6451-6452` `InfeasibleSizingError.__init__` 본문이 `super().__init__(message)`. 기존 `_refs`는 이를 `("attr", "__init__")`로 만들고
  `resolve`는 `by_name["__init__"]` -- 그래프의 **모든** `__init__`으로 간선을 낸다. 옛 그래프에서는 `InfeasibleSizingError.__init__` 자체가 미도달이라 이 간선이 잠들어
  있었다(준비 자료 §3 R2 반례 4 "HEAD 운영 경로에 0건이라 지금은 무해"는 **옛 그래프 기준** 판단). R2가 `raise InfeasibleSizingError(...)`로 이 노드를 도달시키는 순간 폴백이 깨어난다.
* 실측(reviewer 시제품, HEAD 트리에 `class _RvNeverBuilt: def __init__...`를 `sizing_recipe.py` 끝에 붙인 메모리 사본, 운영 루트, R3 적용):
  - base 도구: `_RvNeverBuilt.__init__` 미도달.
  - 초안 규칙(R1+R2+R3): **도달**. 사슬 `run_harness::run → optimize_full_circuit_budget → _build_theta_evaluator._evaluate → InfeasibleSizingError.__init__ → (attr __init__) → _RvNeverBuilt.__init__`.
  - 합성 단계 `adv-super-init-leak`(base에 `RtErr(ValueError).__init__`이 `super().__init__(m)`, 도달하는 `rt_check`가 `raise RtErr(...)`; head가 인스턴스화 0인 `RtNever.__init__`만 추가):
    base exit 1, 초안 규칙 **exit 0**(거짓 PASS).
* 결과: Q1을 (a)로 정해도 실저장소에서 계약 4("isinstance·except·주석에만 나오는 클래스의 `__init__`은 미도달")는 **성립하지 않는다**. 합성 단계 `ctor-isinstance-only`는 `super()`가 없는
  저장소라 통과하므로 게이트 redteam이 이 약화를 못 본다. Phase 3에서 새 클래스가 생기면 V7이 전부 통과시킨다.
* 수정안(HEAD 비용 0 실측): 속성 참조 중 dunder(`__x__`) 이름은 `by_name` 전역 폴백을 쓰지 않는다. `super().X`는 R2의 기반 클래스 해석으로 그 클래스 bases의 `X`에만
  간선(선택). 실측: dunder 폴백 제거 시 HEAD 미도달 39 그대로(합집합·두 벌 모두), V3 인벤토리 0 증가 없음, 쌍 79,809 → 79,737.
* 계약·redteam: 계약 4에 "기존 도달 코드에 `super().__init__()`이 있어도"를 넣고, 거부 단계 `ctor-super-leak`(위 `adv-super-init-leak` 구성, 기대 exit 1, base 도구 exit 1)을 추가.
  이 수정은 옛 간선(속성 `__init__` → 모든 `__init__`)을 지우므로 계약 9의 단조성 문장도 고쳐야 한다(S5).

### B2. R1 재수출 폴백이 그래프 밖 모듈의 속성에도 걸린다

* 초안 R1: "`M.NAME`, M에 바인딩이 없으면 -- 재수출 -- 같은 이름의 바인딩". 문장 그대로면 M이 numpy·math·os 같은 **그래프 밖 모듈**이어도 폴백한다
  (기존 def 규칙 `by_mod or by_name`을 그대로 본뜬 모양).
* 실측 `adv-external-modattr`: 엔진에 새 `_f_p`와 고아 바인딩 `pi = {"p": _f_p}`, 하네스 `run`이 `math.pi * rt_gain(x)` → base exit 1, 초안 규칙 **exit 0**(거짓 PASS).
  `np.inf`·`os.path`·`sys.path`·`math.e` 같은 흔한 속성이 같은 이름의 엔진 바인딩 값을 '배선'한다.
* 수정안: 재수출 폴백은 M이 그래프 안의 모듈일 때만, 그리고 **같은 이름 바인딩 전체가 아니라 M 파일의 `from X import NAME`을 따라간다**(최대 깊이 제한). 실측: 이 규칙(`chase`)으로
  HEAD 39 그대로, 초안 단계 `registry-reexport` exit 0 그대로, `adv-external-modattr`·`adv-crossmodule-same-binding-name`(S3) exit 1.
* 계약·redteam: 계약 1의 재수출 형식을 "M 파일의 `from X import NAME`을 따라 X의 바인딩"으로 고치고, 거부 단계 `registry-external-attr`(위 구성) 추가.

### B3. 17단계가 바인딩 해석 형식을 고정하지 못한다 -- 가장 자연스러운 구현이 전부 통과하면서 약화

* 초안은 참조 형태 네 가지(같은 파일 이름, `from M import`, `M.NAME`, 재수출)를 **양성**으로만 시험한다. 바인딩을 기존 `local`·`by_name`·`by_mod` 색인에 그냥 넣는 구현(`resolve`를 안 고치고
  색인만 늘리는, code-author가 가장 먼저 떠올릴 모양)은 `str`·`attr`·맨 이름 폴백까지 바인딩으로 보낸다.
* 실측(그 구현 = 시제품 `loose`): 초안 V7 단계 15개(승인 단계 제외) 전부 기대와 같음. 그러나
  - `adv-attr-same-name`: 엔진 고아 바인딩 `cache = {"a": _f_a}`, `run`이 비모듈 속성 `x.cache` → **exit 0**(거짓 PASS)
  - `adv-str-same-name`: 고아 `_STRREG = {...}`, `run`이 문자열 `'_STRREG'`(dict 키)만 씀 → **exit 0**
  - HEAD 운영 루트가 닿는 비운영 노드 141 → 654(R3가 V7에서는 가리지만 V3 인벤토리는 그대로 부푼다).
* test-author는 소스를 못 보므로 interface card의 계약 문장이 유일한 근거다 -- 음성 형식이 계약에 없으면 시험할 수 없다.
* 수정안: 계약 1에 **"바인딩 노드로 가는 간선은 이 네 형식뿐이다: 비모듈 속성 `x.NAME`, 문자열 상수 `"NAME"`, import 없는 다른 파일의 맨 이름은 바인딩으로 가지 않는다"**를 넣고,
  거부 단계 `registry-attr-collision`·`registry-str-collision`(위 두 구성, 기대 exit 1, base 도구 exit 1)을 추가. R2도 같은 문장 하나("`x.Cls(...)`(x가 모듈 별칭이 아님)·
  import 없는 다른 파일 클래스 이름은 생성자로 가지 않는다").

---

## 2. should-fix

### S1. 바인딩 값 안 문자열 상수가 str 규칙으로 def에 간선 -- V3 비용 증가의 대부분이자 V7 거짓 PASS 면

* R1은 바인딩 값에 기존 `_refs`를 그대로 쓴다(준비 자료 §3 R1 "기존 `_refs` 그대로") → 값 안의 식별자 모양 문자열이 같은 이름 def로 간선(str 규칙, 파일 범위 없음).
  옛 그래프에서는 모듈 최상위가 미도달이라 잠들어 있던 간선이다.
* V7 실측 `adv-str-in-source-binding`: 엔진 `_DOC_NAMES = ("rt_h2",)`를 도달 코드가 `x in _DOC_NAMES`로만 읽고 `rt_h2`는 호출 0 → base exit 1, 초안 **exit 0**. 준비 자료 §1.4가
  누수 증거로 든 바로 그 모양(`_RESTORED_NAMES`)이 소스 파일에 오면 R3가 막지 못한다(계약 6은 test 파일만 시험).
* V3 실측(HEAD, test 454): 쌍 base 33,991 / 초안 79,809 / **바인딩 값 str 제외 44,565**. 즉 초안 증가분 45,818쌍 중 35,244쌍(77%)이 test 파일 바인딩의 이름 문자열 튜플을
  test가 읽어서 생긴 것이다(그 test는 엔진 def를 부르지 않고 이름만 적는다 -- 변이를 죽일 수 없는 인벤토리라 순수 비용). 대표: `SemiEmpiricalGmIdLUT.__init__` 335 → 252,
  `_metric_sum_current` 166 → 87.
* 비용(실측): HEAD V7 미도달 39 그대로(두 벌 모두). V3 인벤토리 0인 소스 def 14 → 19, 늘어난 5개(`audit_current_forced` 4개, `check_mirror_symmetry`)는 **base에서도 0**이라 base 대비 회귀 없음.
* 수정안: R1 바인딩 값에서는 str 참조를 간선으로 쓰지 않는다(이름·속성·생성자 참조만). 계약 1에 명시 + 거부 단계 `registry-name-strings`(위 구성). 함수 몸체의 기존 str 규칙은 그대로
  (계약 9 단조성 유지).
  거절할 경우에도 계약 6을 소스 파일 버전으로 하나 더 두어 이 동작을 '알려진 한계'로 고정해야 한다(지금은 문서에도 없다).

### S2. 함수 지역 변수가 같은 이름 모듈 바인딩으로 해석된다

* 준비 자료 §3 R1 반례 5에만 있고 초안에는 없다. 실측 `adv-local-shadow`: `rt_gain`이 지역 `_TABLE = {}`을 읽고 모듈의 고아 `_TABLE = {"t": _f_t}`는 아무도 안 읽음 →
  base exit 1, 초안 **exit 0**.
* 수정 비용 실측: 함수의 인자·Store 이름(`global`/`nonlocal` 선언 제외)을 바인딩 해석에서 빼면 HEAD 39 그대로, HEAD 소스 파일에 이 충돌이 있는 def 0개(지금 무해, 앞으로의 면).
* 수정안: 규칙으로 넣거나(권고 -- 함수당 AST 한 번, 계약 11 '재계산 없음'과 양립), 넣지 않으면 의도 절에 알려진 한계로 적고 거부 단계 대신 known_limit 단계(기대 exit 0)로 고정.

### S3. 재수출 폴백이 같은 이름 바인딩 **전체**로 간다

* 실측 `adv-crossmodule-same-binding-name`: `rt_engine`이 `from rt_reg import _REG_Y` 재수출, 하네스가 `from rt_engine import _REG_Y`; 다른 소스 `rt_other.py`의 고아 `_REG_Y = {"y": _f_y2}`
  → 초안 규칙에서 `_f_y2`가 도달(exit 0). Phase 3에서 레지스트리를 옮기며 옛·새 모듈에 같은 이름이 잠시 공존하면 정확히 이 모양이다.
* 수정: B2의 `chase`(M의 import 문을 따라감)가 같이 해결한다(실측 exit 1, HEAD 39 그대로).

### S4. 계약 12(V3 비용 기록)의 측정 대상과 관찰 항목

* 권장 대상 `20260930-dup-w-calc`의 V3는 도구 실행이 **변이 2,060개 전부 기준 실행 실패**(B28 이전 .git 없는 사본 결함)였고 PASS는 대체 확인으로 냈다
  (`.ai/verification/20260930-dup-w-calc.json` checks.V3). 병합본(B28 반영) 도구로는 처음으로 2,060개를 실제로 돌리게 되고, 대상이 `_build_theta_evaluator._evaluate` 같은 큰 def라
  두 도구 × 수 시간~수십 시간(`draft_v3_decision_question.md`: B26-1 2,472개 3.4 h~122 h)이며 기록에 적힌 생존 10개 때문에 두 도구 모두 FAIL일 공산이 크다 -- "verdict가 나빠지면
  원인 기록"이 비교 근거가 되지 못한다.
* 대안(판정 가능·저비용):
  1. 실제 도구 PASS였던 작은 기록 `20260930-restore-plan-functions`(mutants 32, killed 32) 1건을 두 도구로 실행.
  2. **정적 인벤토리 비교**(test 실행 없음): 과거 V3 대상 def 전부 + 착수 예정 card(B26-1·B34 draft의 대상 def)의 인벤토리 크기 base/병합본.
  3. 그중 인벤토리가 가장 큰 대상 1개의 **기준 실행만** 두 그래프로 1회씩(시간 = timeout 여유).
* timeout-kill 관찰 추가: `run_tests`의 `TimeoutExpired` → `"timeout"` → `code != 0` → killed(`mutate_changed.py` 354-356·387-392). 변이 결과 jsonl의 `"exit": "timeout"` 건수를
  두 도구 각각 기록하게 한다(관찰 가능, `--out`). 병합본에서만 timeout-kill이 생기면 원인 기록. timeout을 별도 결과로 분리하는 게이트 변경은 백로그(이 card 범위 밖이라는 초안 판단에 동의).
* S1 수정이 받아들여지면 V3 증가는 2.35배 → 1.31배(쌍 44,493, 아래 모든 수정 합산 실측)로 줄어 이 위험 자체가 작아진다.

### S5. 계약 9 문구

* "바인딩 노드는 간선 사전의 **키로만**" -- 바인딩 노드는 간선의 **값(목적지)**에도 들어가고 `reach` 결과에 들어간다(V3 `inventory`는 목적지 비교라 무해, V7 `new_defs`는 `nodes`에서
  만들어 무해). "노드 집합 `nodes`에는 들어가지 않고 간선 사전의 키·값에만"으로.
* B1 수정을 채택하면 옛 간선(속성 dunder → 모든 `__init__`)이 사라지므로 "옛 그래프의 모든 간선은 새 그래프에도 있다"를 "속성 dunder 폴백 간선을 빼고"로 바꾸고, 그 제거로 도달이
  줄어든 def가 HEAD에서 0개임을 auditor가 잰다(실측 0).

### S6. redteam 번호 -- 네 초안이 32·33을 서로 다르게 쓴다

| 초안 | 지금 쓰는 번호 |
|---|---|
| `draft_phase3_design_v4.md` D-18(209-210·406행) | G1 = `32-moved-defs`, B33 = `33-v7-graph-edges`, "병합 순서와 무관하게 미리 나눔" |
| `draft_p3_g1.spec.md`(112·220행) | `32-moved-defs` (D-18 따름) |
| `draft_b33.spec.md`(102·115·125·189-191행, 계약 14) | `32-v7-registry-edges`, "먼저 병합하는 card가 32" -- **D-18과 충돌** |
| `draft_v3_exempt_binding.spec.md`(54·129행) | `32-v3-exempt-binding` |
| `draft_v3_scope_policy.spec.md`(63·65행) | `33-v3-changed-scope` |

제안(D-18 원칙 그대로 -- 미리 나누고 병합 순서와 무관, 단일 출처는 design v4 D-18 표):

| 번호 | 디렉터리 | card |
|---|---|---|
| 32 | `32-moved-defs` | G1 `20260930-p3-gate-move-aware` (변경 없음) |
| 33 | `33-v7-registry-edges` | B33 (D-18의 이름 `33-v7-graph-edges`를 이 이름으로 정정 -- 초안이 쓰는 이름) |
| 34 | `34-v3-exempt-binding` | `20260930-v3-exempt-binding` |
| 35 | `35-v3-changed-scope` | `20260930-v3-changed-stmt-scope` |

* 이유: G1·D-18이 이미 32·33을 확정해 두 문서만 고치면 되고(B33 1건 + V3 두 건), V3 두 card는 아직 사용자 결정(질문 대기) 중이라 번호를 뒤로 미는 비용이 가장 작다. 번호 사이가
  비어도 `run_all.py:55`(`attacks/*/expect.json` glob)는 문제없다.
* 각 card '작성 전 실측'은 "`ls attacks`에 자기 번호가 없음"만 확인하고, 무동작 목록은 "그 시점 `attacks/` 전체"로 쓴다(B33 계약 14가 이미 '기존 redteam 전체'라 그대로 맞다).
* B33 고칠 곳: 102행(design 05 338행 새 문구) `공격 33(attacks/33-v7-registry-edges)`, 115·125행 경로, 계약 14 "(새 케이스 33 제외", 189-191행 '순서' 단락을 "번호는 D-18 고정, 순서 권고만"으로.
* 상호작용 주의: B33은 V3 인벤토리를 바꾸므로 34·35가 먼저 병합되면 그 V3 합성 기대가 B33 계약 14에서 다시 판정되고, B33이 먼저면 34·35 test worktree는 B33 그래프 위에서 만든다.

---

## 3. minor

1. '판정 유형 근거' "red 단계 9개(... base 도구 열이 기대와 다른 것)" -- 표에서 그런 행은 V7 9개 + `v3-registry-inventory` 1개 = **10개**. "V7 9 + V3 1"로.
2. R2가 바인딩 값 안의 생성자 호출(`_THETA_FEED_REGISTRY`의 `FeedHandler(...)` 같은)에도 걸리는지 문장에 없다. 실측(`fp-registry-in-binding-ctor`)상 자연 구현은 건다 -- "바인딩 노드의 값 식도
   R2의 '도달 가능한 코드'에 든다"로 명시.
3. 합성 저장소 루트에 `run_harness.py::__main__`도 들어가(설정 두 벌 합집합 + `__main__` 노드는 항상 생김) 하네스 **모듈 최상위**가 도달한다. test-author가 하네스 최상위에서
   바인딩을 읽으면 거부 단계가 의도와 다르게 통과한다 -- oracle 절에 "하네스 최상위에는 import만" 한 줄.
4. Q1 (a)의 거짓 FAIL 모양(`{"k": Cls}` 후 `_REG[k]()`, `defaultdict(Cls)`)은 실측대로 미도달(`fp-class-as-value` exit 1). 최상위 `REG["k"] = f`·`globals()` 컴프리헨션 레지스트리도
   미도달(`fp-mutated-later`·`fp-dictcomp-globals`). 모두 거짓 FAIL 쪽이라 약화는 아니다 -- 의도 절 '알려진 한계'에 한 줄로(HEAD 0건은 준비 자료 §3 R1 반례 6).
5. `build_graph` 시간: reviewer 실측 base 4.66 s / 초안 5.09 s / 수정 합산 약 4.0~5.6 s(측정 잡음 범위). 임계값 없는 보고 수치라는 계약 11과 맞다.

Q1 판단: (a) 권고에 동의한다. 단 B1을 고치지 않으면 (a)와 (b)의 차이가 실저장소에서 사라진다(어느 쪽이든 모든 `__init__` 도달).

---

## 4. 사실 재측정

### 4.1 줄 번호·grep (HEAD 7535799)

| 초안 문장 | 재측정 |
|---|---|
| `_refs` 69, `build_graph` 97, `reach` 160, `_is_source` 175, `seen = reach` 223, `new_defs` 230 | 일치 |
| `mutate_changed.py` 215 `rch.reach`, 315 `_is_source`, 317 `rch.build_graph` | 일치 |
| docstring 그래프 설명 10~13행 | 일치 |
| design 05 317(V3 ③)·321(V7)·338(거부 증명), 계획 121·843 | 일치(문구 동일) |
| `git grep "::=" -- tools/gates` 0건, `library/·topology.json` 0건, `build_graph` 소비자 `mutate_changed.py`뿐 | 일치 |
| 마지막 attack `31-v3-git-history` | 일치 |
| rt.py: V7 `--config`는 시험 대상 `gate_config.json`(`iface.vtool_command` 100-101행), `approve_after_head`는 diff 전용(rt.py 560-569) | 일치 |

### 4.2 수치 (운영 루트 = 합집합 4개, 소스 def 494)

| 항목 | 초안 | reviewer 재측정 |
|---|---|---|
| 미도달 base 도구 | 115 (R3만 116) | 115 / 116 |
| 미도달 R1+R2+R3 | 39 (두 벌 39) | 39 / before 39 / after 39 |
| 비운영 노드 누수(base) | 64 | 64 |
| V3 쌍 | 33,991 → 79,809 | 33,991 → 79,809 |
| 인벤토리 0 | 82 → 14 | 82 → 14 |
| `_metric_sum_current` / `SemiEmpiricalGmIdLUT.__init__` 인벤토리 | 0→166 / 0→335 | 일치 |
| 수정 합산(B1 dunder·B2/S3 chase·S2 지역·S1 str 제외) | -- | 미도달 39(차이 집합 공집합, 세 루트 벌 모두), V3 쌍 44,493, 인벤토리 0 = 19(늘어난 5개는 base에서도 0) |

### 4.3 과거 판정 기록 V7 쌍 재판정(계약 14 미리보기)

정규식 `reachability.py … --base X --head Y`: 기록 **27건·31쌍**(초안과 같음). 각 쌍에서 base 도구 / 초안 규칙 / 수정 합산 규칙의 `unreached_without_approval`과 `unreached`를 비교.

결과: **31쌍 모두 세 도구의 `unreached_without_approval`이 같다(전부 빈 목록 → 판정 PASS 불변)**, `unreached`도 같다. `--config`는 31쌍 모두 head 트리의 것.
new_defs가 있는 쌍은 `ic3-completeness`(2)·`df36-instance-relpath`(1)·`dup-w-calc`(1)·`restore-plan-functions`(2, 미도달 `lut_conditions_from_npz`·`derived_spec` 세 도구 모두 미도달,
면제 승인으로 PASS)뿐 -- 초안 문장과 같다.
보충(minor): 31쌍 중 4쌍(`d-delete-dead`·`d-delete-telescopic`·`probe-dead-delete`·`probe-engine-dup`)은 한 기록 안에서 같은 커밋 쌍을 짧은/긴 해시로 두 번 적은 것이라 **서로 다른 쌍은 27**이다.
계약 14의 "27건·31쌍"은 정규식 일치 수로는 맞지만 auditor가 쌍 수를 대조할 때 혼동하지 않게 "31 일치(서로 다른 커밋 쌍 27)"로 적기를 권한다.
또 이 무동작 표본은 new_defs가 거의 없어(6개) R1·R2·R3와 B1~S3 수정 어느 것도 구별하지 못한다 -- 거부 동작 증명은 redteam 단계가 맡는다는 초안 판단에 동의.

### 4.4 합성 단계 시뮬레이션(메모리 안 그래프, V7 `main`과 같은 new_defs·면제 전 미도달 판정)

| 단계 | 기대 | base | 초안 규칙 | 느슨한 구현 | 수정 합산 |
|---|---|---|---|---|---|
| 초안 V7 15단계(승인 단계 제외) | 표대로 | 표의 base 열과 전부 일치 | 전부 기대 | 전부 기대 | 전부 기대 |
| `adv-attr-same-name` | 1 | 1 | 1 | **0** | 1 |
| `adv-str-same-name` | 1 | 1 | 1 | **0** | 1 |
| `adv-external-modattr` | 1 | 1 | **0** | **0** | 1 |
| `adv-super-init-leak` | 1 | 1 | **0** | **0** | 1 |
| `adv-local-shadow` | 1 | 1 | **0** | **0** | 1 |
| `adv-str-in-source-binding` | 1 | 1 | **0** | **0** | 1 |
| `adv-crossmodule-same-binding-name` | 1 | 1 | **0** | **0** | 1 |
| `adv-test-only-reader`(레지스트리를 test만 읽음) | 1 | 1 | 1 | 1 | 1 |
| `registry-dead-reader`(초안) | 1 | 1 | 1 | 1 | 1 |
| `fp-*` 4개(실행상 쓰이는 거짓 FAIL 모양) | 0 | 1 | 1(3개)/0(바인딩 값 생성자) | 같음 | 같음 |

요청된 적대 구성 대응: 죽은 함수만 읽는 레지스트리(초안 단계 있음, 통과) · test 파일만 읽는 레지스트리(R3로 거부, 통과) · isinstance/except만(합성은 통과, 실저장소는 B1로 실패) ·
`Cls`를 값으로 팩토리에 넘김(거짓 FAIL 쪽, minor 4) · `from x import REG` 재수출(S3·B2) · dict 컴프리헨션(참조식이면 도달, `globals()`면 거짓 FAIL) · 나중에 `REG["k"] = f`(거짓 FAIL 쪽).

---

## 5. 계약별 판정 가능성(test-author는 CLI만)

| 계약 | 판정 주체 | 판정 가능? | 비고 |
|---|---|---|---|
| 1·2·3·5·6·7·8 | test-author(V7 CLI JSON) | 예 | B3 수정 후 음성 형식 단계 추가 필요 |
| 4 | test-author | Q1 결정 뒤 예 | B1 반영 시 `ctor-super-leak` 추가 |
| 10 | test-author(V3 CLI) | 예 | 공격 31처럼 `subjects` 필요(rt.py가 CARD 레이어 요구) |
| 9·11 | auditor(코드·import) | 예 | S5 문구 수정 |
| 12 | auditor | 조건부 | S4 -- 대상·관찰 항목 고정 필요(지금 '권장'이라 대상이 정해지지 않음) |
| 13 | 오케스트레이터 문서 커밋 + code-author docstring | 예 | S6 번호 반영 |
| 14 | auditor | 예 | 27건·31쌍 재현 |

쓰기 경로: `reachability.py`(code-author, 승인 기록), `attacks/33-*`(test-author), design 05 §10(오케스트레이터) -- 초안과 같고 문제없음. `mutate_changed.py` 무변경도 맞다
(B1·S1 수정도 전부 `build_graph`/`_refs` 쪽이라 V3 코드는 그대로).

---

## 6. 권고 처리 순서

1. B1·B2·B3 반영(계약 1·3·4 문장 + 거부 단계 4개: `ctor-super-leak`, `registry-external-attr`, `registry-attr-collision`, `registry-str-collision`).
2. S1은 사용자 승인 범위 설명에 "바인딩 값의 문자열은 간선 아님"을 넣어 결정(권고 채택 -- HEAD V7 비용 0, V3 증가 2.35배 → 1.31배). S2·S3는 B2 수정과 같이.
3. S4 계약 12 재작성, S5 계약 9 문구, S6 번호(33) 반영 후 재검토.
