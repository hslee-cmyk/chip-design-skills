---
id: 20260930-p3-gate-move-aware
phase: 0.5
evidence_type: red-green
gate_change: yes
approval: 20260930-p3-gate-move-aware
---
## 의도

design `30-module-split`(초안 v2) §5, card G1. 계획 N3.10 533행 "무변경 증명 = 이동 전후 함수별 `ast.dump`(docstring 제외) 해시 동일 + import 줄만 차이. **해시가 같은
함수는 V3 대상에서 뺀다**"가 게이트 도구에 구현돼 있지 않다. V3 `tools/gates/mutate_changed.py`는 같은 경로의 base 소스와만 비교하고(`changed_defs`, 50~62행; base 파일이
없으면 `None` → 전부 대상, 321~326행), V6 `source_lint.py`(`compare`, 212행)와 V7 `reachability.py`(`base_defs`/`new_defs`, 224~231행)도 같은 경로·(파일, qualname)
기준이다. 그래서 Phase 3 이동 card는 **바이트 그대로 옮긴 정의**를 새 정의로 보고 판정 불가가 된다 -- 엔진 4파일 전체 상한으로 V3 대상 def 473·변이 15,677,
V6 새 항목 861, V7 미도달 108(design v2 부록 A G1·G2). 합성 저장소에서 base V6·V7 모두 exit 1(G3).

고칠 방향: **판정식은 그대로 두고 옮긴 정의의 비교 기준만 '같은 경로의 base'에서 '이동 원본'으로 바꾼다.** 옮긴 정의 = design v2 §3 MOVED:
(M-1) base의 소스 분류 파일 중 정확히 하나 p_b ≠ p_h가 같은 qualname q와 같은 `def_hash`를 가진다, (M-2) head에서 p_b는 q를 정의하지 않는다, (M-3) head에서 (q, 해시)가 p_h 한
곳에만 있다. 최상위 문장(import·def·class·`if __name__` 블록 제외)은 `ast.dump(include_attributes=False)` 해시로 같은 규칙. 이 규칙 때문에 복사·래퍼 shim·모호한 원본은
이동이 아니고 지금처럼 새 정의다 -- **판정 기준을 약화하지 않는다**(같은 경로 무변경 def를 보지 않는 지금 강도와 같다).

해시 정의는 하나: `_strip_doc`·`def_hash`를 `reachability.py`로 옮기고 `mutate_changed.py`는 그것을 import해 같은 이름으로 둔다(`mutate_changed`가 이미 `reachability`를
import하므로 반대 방향이면 순환). 기존 판정 기록 스크립트가 `mc.changed_defs(base_src, head_src)`·`mc.def_hash`를 부르므로(G4) 이름·시그니처·결과를 유지한다.

B28(`20260930-v3-history-clone`)과의 관계: B28은 V3의 **test 실행 환경**(285행 copytree → 격리 복제본, 328~342행 기준 실행 실패 → `ERROR`, 364행 정리)을, 이 card는
**대상 선택**(326행 앞 이동 제외)과 판정 JSON의 `moved`만 바꾼다. 이 card의 test worktree는 **B28 push 뒤 gate `master`**에서 만들고 '작성 전 실측'의 줄 번호는 그 base에서
다시 잰다. B28의 계약 1~7은 이 card의 무동작 입력이다.

재설치: 바뀌는 파일은 §4.4 캐시에서 실행되는 auditor 도구뿐이고 설치 사본(gate `hooks/pre-receive`·`gate-runner.py`, `.claude/hooks/role_*`)이 아니다 -- design 05 §13.4
재설치 절차 불필요(B28과 같은 판단). 새 도구 동작은 이 변경이 반영된 뒤의 base 캐시부터 쓰인다.

## 관찰 가능한 계약

1. **`reachability.moved_defs(base_files, head_files)`**: 입력은 `read_tree` 모양의 `{저장소 상대 경로: 소스}` 둘. 반환 `{"defs": {"<p_h>::<q>": "<p_b>::<q>"}, "statements":
   {"<p_h>::<module>:<줄>": "<p_b>::<module>:<줄>"}}`. 소스 분류(`_is_source`) 파일만 본다. M-1~M-3을 모두 만족하는 것만 담는다. 입력을 바꾸지 않는 순수 함수다.
2. **V3**: `moved_defs`의 `defs`에 든 정의는 변이 대상이 아니다. 나머지 대상 선택은 지금과 같다(`changed_defs`와 같은 결과). 판정 JSON에 `"moved": [{"from": …, "to": …}]`를 더한다.
3. **V6**: 옮긴 정의 단위의 '이전 항목 수'는 이동 원본 단위를 **원본 파일 맥락**에서 센 값이고, 옮긴 최상위 문장은 새 파일 `<module>` 단위의 이전 항목 수에 원본 맥락 값으로
   더해진다. 현재 항목 수는 **새 파일 맥락**에서 센다 -- 늘면 지금처럼 FAIL(예: 캐시 dict를 옮기고 `len()` 상한 검사를 원래 파일에 남기면 `unbounded_cache`). 판정 JSON에 `moved`.
4. **V7**: `moved_defs`의 `defs`에 든 정의는 `new_defs`가 아니다. 판정 JSON에 `moved`.
5. **이동이 아닌 것**(지금과 같은 판정): (a) 옮기며 토큰 하나라도 바뀐 정의(해시 다름) (b) 복사 -- p_b가 q를 계속 정의 (c) 래퍼 shim -- p_b에 같은 이름의 다른 def (d) 모호한 원본 --
   base에서 같은 (q, 해시)가 두 파일 (e) head에서 같은 (q, 해시)가 두 새 위치. 이것들은 V3 대상·V6 새 항목·V7 새 def다.
6. **정의 하나·호환**: `reachability.def_hash`가 유일한 정의이고 `mutate_changed.def_hash is reachability.def_hash`. `mutate_changed.changed_defs(base_src, head_src)`의 시그니처와
   반환(같은 입력에서 같은 (qualname, 노드 해시) 목록)이 base와 같다.
7. **topology 무관**: 바뀐 게이트 소스에 `library/`·`.topology.json`·회로·넷·소자 이름 리터럴이 없고, 모든 판정이 회로 없는 합성 저장소에서 성립한다.
8. **재계산 없음**(NFR-2): 세 도구의 `main`은 실행당 `moved_defs`를 한 번 부르고 base 트리를 한 번 읽는다(V3는 지금처럼 대상 파일마다 `git show`로 base 소스를 다시 읽지
   않고 그 한 번 읽은 트리를 쓴다). auditor가 합성 저장소 실행에서 `cProfile` 호출 수(`moved_defs` 1, `read_tree`의 base 호출 1)로 확인한다.
9. **무동작**: 기존 redteam V3·V6·V7 케이스(`v3_survivor`, `v7_unwired`, `attacks/09-v6-broad-except`, `26-gate-output-utf8`, `27f-v6-reconfigure-except`, `28-v3-gmid-options`,
   B28의 `31-v3-git-history`)와 `run_all.py --phase 0.5 --mode direct`·`--cases 0.5` 전 케이스의 판정이 base와 같다.
10. **새 redteam 케이스** `tools/gates/redteam/attacks/<다음 번호>-moved-defs/`(B28 병합 뒤 `ls attacks`로 번호 확인, 지금 마지막 30 + B28 31 → 32): `lib/rt.py vcase` 합성
    저장소 단계
    * `move-exact`: 인벤토리 test가 없는 def(광범위 except·리터럴 포함, 운영 루트 미도달)를 바이트 그대로 새 파일로 옮기고 원래 파일은 `from <새 모듈> import <이름>`만 --
      V3·V6·V7 각각 exit 0, 출력 `moved`에 그 정의(base 도구: V3 exit 1 '인벤토리 없음' 생존, V6 exit 1, V7 exit 1 -- red).
    * `move-edited`·`copy`·`wrapper`·`ambiguous`·`two-targets`: 계약 5 (a)~(e) -- 해당 도구 exit 1(base 도구도 exit 1).
    * `cache-split`: 캐시 dict만 옮기고 `len()` 검사는 원래 파일 -- V6 exit 1(base도 1). `cache-together`: 캐시와 검사 함수를 함께 옮김 -- V6 exit 0(base exit 1 -- red).
11. 문서(오케스트레이터 문서 커밋): design 05 §10 V3 행 ①("diff가 닿은 `def` 중 … 해시가 base와 다른 것")·V6 행·V7 행에 "옮긴 정의(design 30 §3 MOVED)는 이동 원본과
    비교"를 더하고, 계획 N3.10 533행 끝에 "V6·V7의 '새'도 같은 규칙(옮긴 정의는 이동 원본과 비교)" 한 문장을 더한다. 도구 모듈 docstring도 같은 뜻(code-author).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `reachability` | `moved_defs` | `def moved_defs(base_files: dict, head_files: dict) -> dict` |
| `reachability` | `def_hash` | `def def_hash(fn) -> str` |

## 판정 유형 근거

red-green: 계약 10의 `move-exact`·`cache-together` 단계가 base 도구에서 exit 1이라 red(G3 실측: base V6·V7 exit 1), 병합본 도구에서 exit 0. design 05 §18 "⑤ 뒤 게이트 변경은
spec card로 한다(red-green, oracle (a))". 게이트 코드(`tools/gates/`, redteam 제외)를 바꾸므로 `gate_change: yes`와 승인 기록이 필요하다.

## oracle 종류와 출처

(a) 구성: 합성 저장소(redteam `lib/rt.py`의 `build_vrepo`·`vcase` -- base 커밋 → head 커밋의 실제 이력)에 이동·복사·래퍼·모호 원본·캐시 분리를 손으로 만든다. 기대 exit와
`moved` 내용은 이 card 계약 문장이 정한다(피검 도구 출력으로 만들지 않는다). `moved_defs`의 단위 판정도 합성 `{경로: 소스}` 사전으로.

## 거부해야 할 입력

계약 5 (a)~(e)와 `cache-split`: 이동으로 보지 않고 지금처럼 FAIL. 판정기 자기 점검: `moved_defs`가 소스 분류 밖 파일(`A/tests/**`, `tools/**`)의 정의를 담으면 안 된다.

## library 회로 적용 여부

해당 없음(게이트 도구). Phase 3 M card 판정 기록의 V3·V6·V7 `moved` 목록이 실제 적용이다.

## 무동작 판정 입력(무발동 값)

계약 9: 기존 redteam 전체와 `--cases 0.5`. 이동이 없는 base·head 쌍(지금까지의 모든 판정 기록 base·head)에서 `moved`가 비고 판정이 base 도구와 같다 -- auditor가 최근 판정 기록
2건(`20260930-df36-instance-relpath`, `20260930-dup-w-calc`)의 base·head로 확인.

## 재현할 수치

없음(보고 수치는 auditor 판정 기록에서만 인용한다).

## 결정 필요 항목

게이트 변경 승인(design v2 §9.2 UD-5) -- 승인 기록 `20260930-p3-gate-move-aware`(날짜는 승인일로). 계획 N3.10 533행 문장 추가도 같은 승인이 덮는다.

## 작성 전 실측

(기준 gate `master` `cd64170` -- **B28 병합 뒤 base에서 1·7을 다시 잰다**)
1. 사실: `grep -n 'diff", "--name-only\|copytree\|cat-file\|"show", "%s:%s" % (ns.base\|for q, fn in changed_defs\|rmtree' tools/gates/mutate_changed.py` → 276(diff `--no-renames
   --diff-filter=AM`)·285(copytree)·321(cat-file)·323(show)·326(`changed_defs` 호출)·364(rmtree). `sed -n 46,62p` → `def_hash` 46~47, `changed_defs` 50~62(같은 경로 base만).
   `grep -n "base_defs\|new_defs = " tools/gates/reachability.py` → 224·227·230·231. `grep -n "^def compare\|findings += compare" tools/gates/source_lint.py` → 212·268.
   design v2 부록 A G1(대상 473·변이 15,677·V6 861)·G2(미도달 109, 면제 1)·G3(base V6·V7 exit 1) -- `$PY -B wt/_drafts/p3v2_g1_measure.py` → `p3v2_g1_results.json`.
2. 이름 충돌: `ls tools/gates/redteam/attacks` → 마지막 `30-rejudge-cache`(B28이 31을 쓴다) → 32. `run_all.py:55` 발견 규칙 = `attacks/*/expect.json`이라 이름 충돌만 피하면 된다.
   `git grep -n -E "moved_defs|def_hash|changed_defs" -- docs/01-plan docs/02-design` → 0건(새 이름 `moved_defs` 충돌 없음).
3. 원칙: 약화 금지 -- 계약 5·10(거부 단계), topology 무관 -- 계약 7, 재계산 없음 -- 계약 8, 정의 하나 -- 계약 6, 만들면 배선 -- 계약 2~4(`moved_defs`를 세 `main`이 부른다).
4. 쓰기 경로: `tools/gates/{reachability,mutate_changed,source_lint}.py` = code-author(게이트 변경, 승인 기록 필요), `tools/gates/redteam/**` = test-author, design 05 §10·계획
   N3.10 533행 = 오케스트레이터 문서 커밋.
5. 계획서 소비자: 바꾸는 이름 없음(추가만). 게이트 밖 호출: `git grep -n "def_hash\|changed_defs" -- . ':!*.jsonl'` → `.ai/verification/20260930-df36-instance-relpath/scripts/mut_def.py:67`,
   `probe_t2_vs_1st_survivor.py:16`, `.ai/verification/20260930-dup-w-calc/scripts/v3_baseline_probe.py:17` -- 계약 6으로 호환.
6. 미배선: 새 def `moved_defs`는 세 도구 `main`이 부른다. V7 검사 범위(`A/*.py`·`run_harness.py`) 밖이라 면제 승인 불필요.
7. 기존 계약 test: `git grep -l -E "mutate_changed|reachability|source_lint" -- skills/analog-gmid-design/assets/tests` → 0건. 기존 redteam V3·V6·V7 케이스는 계약 9로 불변 판정.
