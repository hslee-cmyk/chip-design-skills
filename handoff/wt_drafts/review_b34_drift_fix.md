# 독립 검토 -- B34-drift 수정(2026-10-06) 7개 파일

검토자: 독립 검증 agent(수정 작성자 아님). 저장소·_drafts 읽기 전용(이 파일만 씀). 모래상자 `/c/g326`(TMP·TEMP 그 아래, 끝나고 삭제).
기준: gate master `6c724de`(= `2183f2e` + b26pre spec·interface card 문서 2개뿐. 엔진·selftest·tools 바이트 같음 -- `git diff --stat 2183f2e 6c724de`).
대상: `backfill_launch.sh`, `draft_b26_backfill_audit.spec.md`, `b26_backfill_briefs.md`, `b26_1_launch.sh`, `draft_b26_1.spec.md`,
`b26_scripts/b26v4_head.py`, `post35_kit/p35_heads.py`(각 `*.pre-b34m.bak`과 대조).

## 판정: **minor** (B 0 · S 0 · minor 4)

---

## 1. 바뀐 줄 번호 -- `6c724de` 글 대조

**SR 전체 이동 규칙(실측)**: `git show <rev>:sizing_recipe.py`를 `0f23786`·`7243f28`·`dd60db6`·`cd64170`·`7535799` 각각과 `6c724de`를 줄 단위로 비교했다.
1~6509행은 같고, 6513행 이후 `옛 n == 새 n−1` 불일치 **0**(12016→12015줄)이다. 유일한 차이는 B34 `2eb7e55`의 `resolve_stack_layout` docstring hunk(`-6507,9 +6507,8`)다.
`dd60db6..2183f2e`에서 SR을 바꾼 커밋은 `2eb7e55` 하나뿐이고, blob은 `97a6c7b → 2a7a1a0`이다. selftest는 모든 rev에서 같다(1480·1481 `interdig_ok`).

모든 파일의 바뀐 줄을 토큰 단위로 대조했다(`numdiff`). SR 인용 숫자 변경은 **전부 Δ=−1**이었다. 예외는 의도된 경우뿐이다: briefs (나) sed 범위 재작성, 해시 교체(0→2183)(이 둘은 아래에서 따로 확인), b26_1의 SD 줄(b1→실제 Δ −2/−6/−25).
**`6c724de`에서 직접 읽어 확인한 인용 줄(전부 일치):**

| 인용 | 6c724de 글 |
|---|---|
| SR 11711 / 11714 | `def run_matching_safety_with_finger_growth(` / `gm_id_bounds: tuple = (2.0, 30.0), … max_rounds: int = 5,` |
| 11757~11758 | 반환 docstring `"relaxed_pairs": … "interdig_ok":bool\|None}` |
| 11768~11769 / 11771~11772 / 11777 | backfill 주석("다음 라운드에 … 3b 체크로 채운다") / `if entry["interdig_ok"] is not None:` `continue` / `break` |
| 11783~11785 / 11786~11793 / 11792 | `_finalize` 앞 주석("**모든** 반환 지점 … 최종 물리 구조와 항상 일치") / `def _finalize` … `return fixed_rows, fixed_ctx, fixed_audit` / `_backfill_interdig_ok(fixed_audit)` |
| 11795 / 11797 / **11799** / 11800 / 11801 | `result = None` / 루프 안 `current_rows, result = repair_matching_safety(` / **`        _backfill_interdig_ok(result)`** / `if result.ok:` / `_finalize` |
| 11802~11804 · 11828~11830 · 11836~11838 · 11862~11864 · 11880~11883 | 반환 다섯 자리(None · reason · `pair_not_found` · reason · `max_rounds_exceeded`) |
| 11810 · 11816 · 11832 · 11870~11871 (head = base−1) | `import re` · `m.group(1), m.group(2)` · `a, b = failing_3c[0]` · `for name, u in fix["revalidation"]…` / `cur_ctx = _dc_replace(` |
| 11876 / **11878** / 11879 | 루프 뒤 `repair_matching_safety(` / **`    _backfill_interdig_ok(result)`** / `_finalize` |
| 9368 / 9371 / 9397 | `match_fix = run_matching_safety_with_finger_growth(` / `gm_id_bounds=spec.get(…)` / `relaxed_pairs=match_fix["relaxed_pairs"])` |
| 6510~6511 | B34 docstring 2줄(`4. candidates가 None이면(도달 불가 -- … ImportError)`) |
| SR 7281·8002·8090·6880·6885·6919·6930·6947 | `_DEFAULT_RAIL_HI/LO` 판정 · `_rail_nets = frozenset(…)` · `rail_nets=_rail_nets` · `_rail_nets = topo.rail_nets` 등(cd64170 7282·8003·8091과 글 같음) |
| SD 사이트 13 = 1014·1570·1612·2090·2166·3130·3235·3967·4146·4282·4298·4345·4367 | 전부 `_RAIL_NETS` 또는 `{"vdd": "vdd", "gnd": "gnd"}`. 7535799의 같은 13개 문장(1014·1575·1617·2096·2172·3148·3253·3992·4171·4307·4323·4370·4392)과 1:1이고, 3042는 사라졌다 |
| SD 2394~2395 · 2404~2405 · 2414 · 2434~2435 | `if netclass is None: return None, None` · `if cls_before is None: return None` · `if candidates is None:` · `if relations is None: return None` |
| SD 4046~4048 · 3941~3945 · 2489 · 4062 | `_static_ref_roles = (… if _netclass_lcmf is not None else ())` · `if refined is None: return {… "unavailable_reason" …}` · `if _netclass_al is not None:` · `if _idioms_lcmf is not None:` |
| SD 3907~3908 · 2343~2344 | `(… is None 분기는 도달 불가 -- 삭제는 B26-1/B35/백로그)`. 같은 구절이 SD에 11곳 있다는 card 문장도 실측과 같다 |
| SD 2997~3042 `kcl_series_union` | 레일 판정 코드 0(vdd·gnd·rail은 docstring에만 3회) |
| 옛 모의 b1(재생성: 2d58fd8 archive + mk_b1, 9024→9016) | `SITE_SD_B1_MOCK` 13/13 일치, 새 `SITE_SD_B1`은 1/13 |

`b26pre H4`(실제 B34 위, 아래 4절 p35_heads가 만든 head) SR 11808·11887 = `_backfill_interdig_ok(result)`. card 167행 주석과 같다.

## 2. 계약 절 -- 숫자만 바뀌었나

절 단위 비교(숫자를 `#`로 정규화)를 했다.
* backfill card '관찰 가능한 계약': 정규화 뒤 차이 **1줄**. 반환 자리 머리말의 `(gate \`0f23786\` A/sizing_recipe.py,` → `(gate \`2183f2e\` A/sizing_recipe.py 줄 -- \`0f23786\`보다 −1,`이다. 측정 rev 표지만 바꾸고 주석을 하나 더했다. 계약 문장·판정·기대값은 바뀌지 않았다.
* B26-1 card '관찰 가능한 계약': 정규화 뒤 차이 **1줄**((e) 사이트 줄 출처 괄호 `(b1 줄)` → `(B34 병합본 \`2183f2e\` 줄 -- 옛 모의 … 숫자만 고침, 2026-10-06)`). 마찬가지로 줄 출처 주석이다.
* 두 card 모두 다른 계약 문장은 숫자만 달라졌다. backfill card의 '판정 유형 근거'·'거부해야 할 입력'·'재현할 수치'도 숫자만 달라졌다. '의도'·oracle·library·phase·B26-1 인계·'작성 전 실측'은 설명 문장이 늘었다. 이 절들은 계약이 아니다.
* **두 문장 식별**: 계약 끝 구현 후보 "루프 안·루프 뒤의 사전 backfill 호출(11799·11878) 두 줄"은 `6c724de`에서 각각 루프 안·루프 뒤 `repair_matching_safety` 바로 다음 `_backfill_interdig_ok(result)`다. 정리 함수 안 호출(11792)과는 다르다. 수정 전 11800·11879가 가리키던 두 문장과 **같은 두 문장**이다(전수 −1 대응).
* parse_spec_card(`git archive 6c724de tools/gates`)의 수정 전후 결과는 같다:
  backfill `('3','red-green','no',[20261001-b26-backfill-interdig-fix, 20261001-b26-phase3-cards],[],11)`. phase는 plan 순서 안에 있고, 승인 2건 모두 6c724de에 있다.
  B26-1(id `20260930-b26-rail-accessor-set`) `('3','red-green','no',[20260930-b26-before-phase3, 20261001-b26-phase3-cards, 20260930-b26-b40-reason-key],[],12)`. b40 기록만 gate에 없는데, launch P 단계가 올리는 것이라 수정 전과 같다.

## 3. engine_since -- fail-closed 합성 시험

실제 `backfill_launch.sh` 212~226행(ALLOW_SR_IDS + 함수)을 그대로 떼어 냈다. 이것을 `/c/g326/zz_es` 복제본(`-c core.autocrlf=false`, origin 제거, 빈 hooksPath)에서
`set -Eeuo pipefail; shopt -s inherit_errexit` 아래 새 bash로 실행했다. H0는 `2183f2e` + b26pre test 자리표시다. 승인 기록은 실제 초안 파일과 cmp로 비교했다.

| 경우 | 기대 | 결과 |
|---|---|---|
| A M=2183f2e, SR 커밋 0 | 통과 | rc 0("변경 커밋 0개") |
| B M=7243f28 / B2 M=dd60db6 → B34 `2eb7e55` | 통과 | rc 0(`2eb7e55 … Change-Id 20260930-b34-grammar-explicit(허용)`) |
| C 트레일러 없는 SR 커밋(M=2183f2e, M=7243f28 둘 다) | 멈춤 | rc 1(`Change-Id ''`) |
| D 다른 Change-Id(backfill id) SR 커밋 | 멈춤 | rc 1 |
| E 다른 Change-Id로 selftest 변경 | 멈춤 | rc 1 |
| F B34 id + 다른 id 두 트레일러 | 멈춤 | rc 1(줄바꿈 낀 cid는 일치 안 함) |
| G 접두 id `20260930-b34-grammar` | 멈춤 | rc 1(공백 경계 일치) |
| J M가 H의 조상 아님 | 멈춤 | rc 1(merge-base) |
| K b26pre test 없음 | 멈춤 | rc 1 |
| H B34 Change-Id를 **재사용**한 SR 커밋 | (한계) | rc 0 -- 통과 |
| I SR을 **merge 커밋에서만** 바꿈(evil merge) | (한계) | rc 0 -- `--no-merges`라 안 보임 |

→ 비 B34 커밋은 멈추고 B34 커밋은 통과한다. 이 요구는 성립한다(**fail-closed**). 한계 H·I는 minor 1에서 다룬다.

## 4. 실행 재측정(`/c/g326`, `post35_kit/remeasure.sh --skip-slow 6c724de`, 실제 저장소 읽기 전용)

* p35_heads setup: "REV 6c724de…에 실제 B34(2eb7e55)가 있다 -- mk_b1 건너뜀". 그래서 B1 = P0. BF 커밋 "SR 11799 11878 deleted", numstat `0 2`.
* **V3-BF 4/93**(targets_by_def `run_matching_safety_with_finger_growth: [4, 93]`, proto 대칭차 0). 대상 id 4개는 briefs N2w 4개와 같다.
* **V3-B26v4 301/2141**(out 2442), **V3-B26A 299/2141**(2440), **V3-B26v5 299/2136**(2435). 전부 이전 값과 같고 proto 대칭차 0이다. V3-P9 12/16도 같다.
* V3-B34 0/0은 예상한 값이다(실제 B34가 REV에 있어 B1 = P0. 수정 대상 밖).

## 5. kit_line_shift.py 직접 실행(--old 7243f28 --new 2183f2e)

base: `b1`=재생성 모의 SD, `p0`=SD:cd64170. 문서 사례와 같은 --draft 배정으로 돌렸다.
* 수정 전(`.pre-b34m.bak` 사본): 기록 195(high 8·medium 31·ambiguous 155·remeasure 1), 패치 30.
  기록마다 현재 초안과 맞춰 보았다(`reconcile`): high·medium 중 이동 대상은 **전부 현재 초안에 새 값으로 반영**됐다. 예외 2건은 `p35_heads.py` 커밋 메시지로, `%s` 서식으로 바뀌어 숫자가 사라졌다.
  KEPT-OLD 25건은 모두 의도된 것이다. backfill card 186행(dd60db6 측정 기록, card가 "그대로 둔다"고 명시), B26-1 card 65·66·75·77·499·542행(7535799/cd64170 기준 범위 밖·측정 기록 줄, card measured `7535799` 그대로)이 여기에 든다.
  B26-1 44·46·47행(b1 기반 ambiguous/remeasure)은 도구가 값을 못 냈다. 현재 값 3941~3945·2489·4062는 1절에서 직접 확인했다.
* 현재 초안: 패치 2. 둘 다 `p35_heads.py:139` `else` 가지의 11800·11879다. 이것은 **B34 전 REV 가지라 옛 줄이 맞다(도구 오탐)**. remeasure 1건(B26-1:28 SD 3042 = P9가 없앤 줄, 서술 맞음). already-new 105.
→ 도구 제안과 실제 수정 사이에 놓친 이동은 없다.

## 6. minor

1. **engine_since가 내용 기준에서 Change-Id 기준으로 약해졌다**(backfill_launch.sh 212~221). 옛 `git diff --quiet M H -- SR SELFT`는 H(B34 id 재사용)·I(evil merge)도 잡았다. 새 루프는 둘 다 통과시킨다.
   그런데 card measured가 이제 `2183f2e`(B34 뒤)라서 실제 실행에서는 허용 목록이 쓰이지 않는다(A 경우, 커밋 0). **권고**: 옛 `diff --quiet`로 되돌린다. 이쪽이 더 강하고, M=2183f2e에서 그대로 통과한다. 되돌리지 않는다면 `rev-list`에서 `--no-merges`를 빼고 merge 커밋도 Change-Id 검사에 넣는다. v3count의 exp 단정이 두 줄 글은 다시 보지만, 다른 인용 줄(11757~11880)은 보지 않는다.
2. **`SITE_SD_B1_MOCK`은 정의만 있고 쓰는 곳이 0이다**(b26v4_head.py:16, 배선 원칙). 게다가 `SITE_SD_B1`이 실제 B34 줄로 바뀌어서 p35_heads의 B34 전 REV 가지(mk_b1 경로)는 `_check_sites` AssertionError로 반드시 멈춘다(모의 b1에서 1/13). b26_reconcile/v3scope_kit의 옛 모의 b1 소비처도 같다.
   조용히 틀리지는 않는다(fail-loud). 하지만 p35_heads의 `rev_has_b34` else 가지와 `else` exp(11800·11879)는 사실상 도달 불가 코드다. **권고**: `rev_has_b34`로 `SITE_SD_B1`/`_MOCK`을 고르게 배선하거나, MOCK과 else 가지를 지우고 "B34 뒤 REV만"이라고 단정한다. b26v4_head.py 3~4행 docstring("base = b1 … + B34 코드 변경, mk_b1")도 이제 맞지 않는다.
3. **계약 절에 숫자 아닌 주석 2곳**(2절): 측정 rev 표지 괄호를 더했다. 의미는 그대로지만 "숫자만"이라는 규칙을 문자 그대로 지키지는 않았다. 고칠 필요는 없고 기록만 한다.
4. **수정 전부터 있던 1줄 어긋남(이번 수정이 만든 것 아님)**: briefs 0.3 생존 표 `11848 cmp_flip …body[15].body[0]… fix["growth"] is not None` 행의 head 줄. `reason = …` 문장은 base 11850 = head **11849**이고, head 11848은 `if not fix["applied"]:`다. 수정 전 표(11849 → 옛 head 11850)도 1 어긋나 있었고 이번 −1이 그 어긋남을 그대로 옮겼다.

## 7. 확인했고 문제 없음

* `b26_1_launch.sh:85` ALLOW_SR에 B34 id를 더했다. 이것이 필요하다: B26-1 measured가 `7535799`라 `2eb7e55`가 SR 범위에 들어온다. 함수 구조는 backfill과 같고 fail-closed다.
* card measured 앵커 2개(dd60db6 → 2183f2e)는 조상 관계가 맞다(lc_meas_short 규약). `2183f2e..6c724de` SR·selftest 커밋 0이다.
* card '작성 전 실측' 2183f2e 문단의 사실 문장(blob, 커밋 1개, interdig_ok 소비처 SR 10·selftest 2, targets_by_def 3)은 실측과 같다.
* `backfill_launch.sh` v3count에 `core.autocrlf false`를 더한 것은 격리 규칙에 맞는다.

모래상자: `/c/g326`(remeasure·zz_es·zz_kls·zz_tools), 끝나고 삭제했다.
remeasure.sh는 위 V3 항목(P9·BF·B34·B26v4·B26A·B26v5)을 기록한 뒤 b26u3(CARRY-FULL)·정적 항목 도중 백그라운드 30분 한도로 멈췄다. 그 두 항목은 이 검토 범위 밖이다.
그래서 스크립트 끝의 불변 단정이 돌지 않았다. 대신 같은 방식으로 직접 확인했다. 실제 저장소는 HEAD `6c724de`, status md5 `76eea762…`, reflog 356으로 시작 때 기록(`repo_state.before`)과 같고, refs 목록도 같다.
