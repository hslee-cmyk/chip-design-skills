# 독립 검토 -- kit_line_shift.py / kit_line_shift.md (2026-10-06)

검토자는 도구를 쓰지 않았다. 도구·초안·저장소는 읽기만 했다. 실측은 `C:/g320`(TMP/TEMP 포함)의 합성 저장소에서 했고, 끝난 뒤 지웠다.

**판정: S** -- 줄 대응 핵심(`parse_hunks`+`LineMap`)은 맞다. 실제 사례의 patched 인용도 모두 텍스트가 일치한다. 다만 아래 두 가지가 문제다.
(S1) 이미 새 rev로 옮겨 적은 초안에 다시 돌리면 같은 이동을 한 번 더 제안한다(이중 이동). 이를 막는 장치가 없고, 저장된 `current/` 산출물에 실제로 이 오류가 8건(그중 2건은 high) 들어 있다.
(S2) 표지 바로 뒤에 오는 단위가 붙은 숫자(연도·개수·크기·%·파일 길이)와 `a → b` 쌍을 medium으로 패치한다. 문서가 주장하는 '보수적'과 맞지 않는다.

---

## 1. 줄 대응 정확성 (합성 저장소 + difflib 대조)

방법: 매 사례마다 git 저장소를 새로 만들어 old/new를 커밋한다. 이어 `git diff -U0`를 `kls.parse_hunks`와 `kls.LineMap`에 넣는다. 이것을 (a) 불변식 `map(n)=m ⇒ old[n]==new[m]`과 (b) `difflib.SequenceMatcher(autojunk=False)`의 matching block 대응, 두 가지와 대조했다.

| 사례 | 결과 |
|---|---|
| replace 같은 크기·늘림·줄임, 순수 삽입·삭제(중간), 파일 처음 삽입(`-0,0 +1,3`)·삭제(`-1,3 +0,0`), 끝 삽입·삭제, 첫 줄·끝 줄 교체, 1줄 뒤 삽입, 여러 덩어리 섞음 | 틀림 0, difflib 불일치 0 |
| 끝 줄 개행 없음(끝 줄 변경 / 개행 추가 / 뒤에 줄 추가) | 틀림 0. 끝 줄은 git이 바뀐 줄로 세므로 None(remeasure). 보수적이라 문제없음 |
| CRLF 엔진(삽입, 여러 덩어리) | 틀림 0, difflib 불일치 0 |
| 반복 줄(빈 줄·같은 줄 반복) | 틀림 0. difflib와 정렬이 29줄에서 다르지만 둘 다 유효한 정렬이다(텍스트 일치). 반복 줄 정렬의 선택 차이는 본래 피할 수 없다 |
| 무작위 300건(삽입/삭제/교체 1~6회, 반복 토큰 30%) | 틀림 0. 표시된 FAIL 7건은 모두 빈 old 파일로, 검사기가 `b"".split()`을 1줄로 센 오류다(도구 결함 아님) |
| 이름 바뀐 엔진(new 경로가 old에 없음) | `git show old:path` 실패 → SystemExit(rc 1, 메시지 있음). 조용한 오답은 아님. 이름 변경 추적은 하지 않는다(minor, 문서에 한 줄 필요) |
| **바이너리로 판정된 엔진**(`.gitattributes` `*.py -diff`, 또는 NUL 바이트 포함) | **틀림.** `Binary files differ`라 덩어리가 0개가 되고 항등 대응이 된다. 실제로는 +5 이동인데 `SR 1200 → 1200`, medium, delta 0으로 나온다. 보고서에서도 '이동 0'으로 사라진다(→ 결함 S3) |

실제 저장소에서 확인한 것: SR·SD에 attribute가 없고(`git check-attr -a`가 빈 결과), 전역 `diff.*` 설정도 없다. 그래서 S3는 지금 사례에는 영향이 없다.

## 2. 실제 사례 검증 (old 7243f28 → new 2183f2e)

* SR·SD blob은 `c851e54`와 `2183f2e`에서 같다(`git diff --stat` 빈 결과). 따라서 저장된 산출물(new=c851e54)도 2183f2e 기준으로 검증된다.
* 모의 base `b1`을 다시 만들었다(2d58fd8 SD에 build_b34 사이트 5개 적용, 9024→9016줄). 도구 보고서의 b1 덩어리 18개와 **정확히 같다**.
* 세 산출물(`validation_snapshot/`, `current/`, 검토자가 현재 초안으로 새로 돌린 결과) 모두에서 엔진이 붙은 레코드 전부를 확인했다. base n행 글 == new m행 글, 그리고 difflib 대응 == 도구 대응이다.

| 산출물 | high patched | medium patched | 텍스트 일치 | difflib 일치 |
|---|---|---|---|---|
| validation_snapshot | 91 | 94 | 전부 | 전부 |
| current | 91 | 94 | 전부 | 전부 |
| 재실행(현재 초안) | 86 | 90 | 전부 | 전부 |

* high의 의미도 한 줄씩 봤다. `validation_snapshot`의 high 91건은 snippet·리터럴·def가 base 줄과 맞고, 초안의 의도(인용 대상)와도 맞는다. `draft_b26_backfill_audit.spec.md:19` 11769~11770 → 11768~11769는 오케스트레이터가 손으로 고친 값과도 같다.
* **`current/`에는 틀린 제안이 8건 있다**(→ S1). `draft_b26_backfill_audit.spec.md`는 18:03에 이미 2183f2e 줄 번호로 고쳐진 상태였다(13행 "gate `master` `2183f2e` 줄 번호"). 그런데 18:12 실행이 이 파일에 base `old`를 배정했다. 그 결과:
  * 15행 `11783~11785` → `11782~11784` (medium ×2)
  * **19행 `11768~11769` → `11767~11768` (high ×2: `snippet-ok`, `def-ok(_backfill_interdig_ok)`)**. 새 11767행은 `def _backfill_interdig_ok(audit_result):`이고, 인용의 의도는 그 아래 주석 두 줄이다.
  * 105행 `11783~11785, 11768~11769` → 전부 −1 (medium ×4)

  → `current/kit_line_shift.patch`의 이 파일 hunk는 적용하면 안 된다.
* 현재 초안으로 다시 돌리면 이중 이동이 더 나온다. `b26_scripts/b26v4_head.py`는 18:22에 `SITE_SD_B1`이 2183f2e 값으로 바뀌었는데, `@b1`로 돌리면 medium 12건(1570→1569, 4367→4361 …)이 이중 이동이다.
* 오탐 점검: 재실행 patched 176건에는 단위 접미(줄·개·년·%…), `→` 쌍, `b1/` 경로 인용이 0건이다. 실제 초안에 U+2028·`\x0c`·`\x85`·CR도 없다.

## 3. 인용 인식 -- 적대적 초안 (SR·SD 3000줄, 40행 뒤 5줄 삽입, base old)

| 초안 줄 | 결과 | 판정 |
|---|---|---|
| `SR 130줄을 고쳤다` | 130→135 medium **패치** | 오탐 |
| `SR 2026년 10월 6일` / `SR 2026/10/06` / `SR 2026` / `SR 1200 2026년` / `SR 1200 / 2026` | 2026→2031 medium **패치** | 오탐 |
| `SD 512 MB` | 512→517 **패치** | 오탐 |
| `SR 100% 통과` | 100→105 **패치** | 오탐 |
| `SR 300 tests passed`, `SR: 300 passed` | 300→305 **패치** | 오탐 |
| `SR 1200·133개` | 133→138 **패치** | 오탐 |
| `sizing_recipe.py 3000줄 중 1200` | 3000(파일 길이)→3005 **패치** | 오탐 |
| `SR 1200 → 1205(이미 옮긴 값)` | 두 수 모두 +5 **패치**(1205 → 1210) | 오탐(의미 파괴) |
| `* \`sr_line_1200\` 근처, sizing_recipe.py:1205`(이미 new 번호) | 1205→1210 medium **패치**. 줄 안 snippet이 base 줄과 다른데도 표 행이 아니면 내리지 않는다 | 오탐(S1과 같은 원인) |
| `` `C:/g83/b1/skills/a/stick_diagram.py:1200` ``(기본 base old) | 경로 안 `b1`이 엔진 표지에 먹혀 base 표지가 사라진다 → medium **패치** | 오탐(minor) |
| `SR 9024→9016줄`, `SR 12345` | low(파일 길이 밖), 패치 밖 | 정상 |
| `SR 2026-10-06`, `SR v1.2.300`, `SR 0x1234`, `SR 3.14159`, `SR 1,200줄`, `SR 1234567` | 인식 안 함 | 정상 |
| `SR 래치 1200`, `SR latch 1200`, `\| SR \| 1200 \| 1300 \|`, `PR #1234, SR` | untied/ambiguous, 패치 밖 | 정상 |
| `SR 1200 (a1b2c3d)` | anchored, 패치 밖 | 정상 |
| `SD 1567(b34 1563)`, `SR 1200(B34 사본 1195)` | 둘 다 ambiguous, 패치 밖 | 정상 |
| `sizing_recipe.py:1200, test_sizing_recipe.py:1300` | 1300 무시 | 정상 |
| `SR 1200-1210` | 1200은 **보고서에도 없이** 빠지고, 1210만 untied | minor(누락이 보이지 않음) |
| `SR 01200` | `1205`로 바꿔 앞의 0을 잃는다 | minor |
| 리터럴 `{500: b'common = 1'}`가 SR·SD base 500행 모두와 같음 | `--engine` 순서에서 앞에 오는 엔진으로 정한다(SD 먼저 → 507, SR 먼저 → 503). 둘 다 **high** | minor(실사례 영향 없음: SR 11800/11879는 SD 길이 밖) |
| CRLF 엔진의 리터럴 `{1200: b'sr_line_1200 = 1200'}` | `literal-mismatch`(low). `Source.lines`에 `\r`이 남는다 | minor |
| CRLF 초안 | patch `git apply --check` 통과 | 정상 |
| 초안에 U+2028 / `\x0c` | `splitlines()`가 더 쪼개 줄 번호가 L3·L6으로 틀린다(실제 2·4). patch에 `\ No newline` 표지가 잘못 끼어 `git apply --check`가 실패한다 | minor(실제 초안엔 없음, apply가 막는다) |

## 4. 결함과 수정 제안 (도구는 고치지 않았다)

**S1 이중 이동 / 낡은 base 배정 -- 막는 장치 없음, `current/`에 실제 오답 8건(high 2)**
* 재현: 위 `already` 줄. 실제로는 `draft_b26_backfill_audit.spec.md` 15·19·105행(`current/`), `b26v4_head.py` 15행(재실행).
* 원인 (1) anchored 판정이 줄 단위라서, 절 머리말("`2183f2e` 줄 번호")이 아래 줄에 전파되지 않는다.
* 원인 (2) `snippet-ok`가 식별자 하나(`` `_backfill_interdig_ok` ``)의 부분 문자열 일치만으로 high를 준다.
* 원인 (3) `def-ok`는 같은 def 안에서 k줄 어긋난 것을 가리지 못한다.
* 원인 (4) snippet 불일치는 표 행일 때만 내린다.
* 수정 1: 레코드마다 `new[n]`(번호를 그대로 둔 경우)과 `new[map(n)]`를 비교한다. 줄의 snippet이나 리터럴이 `new[n]`과는 맞고 `base[n]`과는 맞지 않으면 `already-new?`로 표시하고 패치에서 뺀다.
* 수정 2: snippet-ok는 snippet이 식별자 하나뿐이면 증거로 치지 않는다. 또는 그 snippet이 base n±3 범위에서 n에만 맞을 때만 인정한다.
* 수정 3: snippet 불일치는 표 행이 아니어도 medium을 ambiguous로 내린다.
* 수정 4: 초안 안 `<hash> 줄`·`줄 번호는 <rev>`·`<rev> 줄 번호` 문장을 찾아 그 절(다음 머리말까지)에 anchored를 전파한다.
* 수정 5(문서): '이미 옮긴 초안에는 다시 돌리지 말 것. 다시 돌리려면 옮기기 전 사본(.bak)을 drafts-root로 줄 것'을 주의 절에 쓴다. `current/`의 해당 hunk 폐기도 명시한다.

**S2 단위가 붙은 수·연도·`→` 쌍을 medium으로 패치**
* 재현: §3 표의 '오탐' 줄들.
* 수정 1: `NUM_RE` 뒤에 단위 부정 lookahead를 둔다. 예: `(?!\s*(?:줄|개|년|월|일|%|건|회|곳|명|MB|KB|GB|tests?|passed|failed))`. 단 `행`은 인용이므로 둔다. `줄`은 'N줄짜리'와 'N줄(=행)'이 모호하니 ambiguous로 보낸다.
* 수정 2: 4자리 19xx/20xx 뒤에 `년` 또는 `/`가 오면 버린다.
* 수정 3: `SEP_CHARS`에서 `→`를 빼거나, `a → b`가 둘 다 묶이면 둘 다 ambiguous(`arrow-pair`)로 둔다.
* 수정 4: 표지와 숫자 사이 구분자가 `:` 하나뿐이고 뒤에 영단어가 오면 untied로 둔다.

**S3 바이너리·textconv 판정 시 조용한 항등 대응** (지금 저장소엔 영향 없음)
* 재현: new rev에 `.gitattributes` `*.py -diff`를 두거나, 엔진에 `\x00`을 넣는다. 그러면 `SR 1200`이 1200 그대로, medium으로 나온다(실제는 1205).
* 수정 1: `git diff`와 `git diff --no-index` 둘 다에 `--text --no-textconv`(필요하면 `--no-renames`)를 넣는다.
* 수정 2: `sum(d-b for hunks) == len(new_lines) - len(base_lines)`를 단언하고, 어긋나면 SystemExit로 멈춘다(덩어리를 빠뜨리는 모든 경우를 막는다).

**minor**
* m1 CRLF 엔진에서 리터럴 대조가 실패한다. `Source.lines`를 `text.split("\n")`에서 `[l.rstrip("\r") for l in …]`로 바꾼다.
* m2 리터럴이 두 엔진 base와 다 맞으면 `hit_eng[0]`을 고른다. `len(hit_eng) > 1`이면 ambiguous로 둔다.
* m3 경로 접두 `b1/`·`g83/b1/`이 엔진 표지 토큰에 흡수되어 base 표지가 사라진다. 엔진 표지의 경로 부분에 --base 이름이나 foreign 낱말이 path segment로 있으면 `mentioned`에 넣는다.
* m4 `a-b` 하이픈 범위의 시작 수가 `(?!-\d)` 때문에 보고서에서도 사라진다. 버리지 말고 untied로라도 남긴다.
* m5 초안을 `splitlines()`로 나누면 U+2028·`\x0c`·`\x85` 등에서 줄 번호가 git이나 편집기와 어긋난다. `split("\n")`(keepends는 수동)으로 바꾼다.
* m6 `n > len(src.lines)`가 끝 개행 뒤의 빈 원소 때문에 1 크다(파일 길이+1 인용을 범위 안으로 본다).
* m7 `literal-verified(base)+new`의 `+new`는 git 대응상 늘 참이라 정보가 없다(문서에서 high 근거로 쓰지 말 것).
* m8 `SR 01200`처럼 앞에 0이 붙은 수는 원래 자리수를 지키게 한다.
* m9 이름이 바뀐 엔진은 지원하지 않는다는 점을 문서에 적는다(지금은 git show 실패로 멈춘다).

## 5. 결론

* 줄 대응(덩어리 해석)은 삽입·삭제·교체·0줄 old 덩어리·파일 처음과 끝·여러 덩어리·CRLF 전부에서 맞다.
* 실제 사례의 patched 레코드는 세 산출물 모두 텍스트가 100% 일치하고, difflib 대응과도 100% 같다.
* `validation_snapshot/`의 high는 의도까지 맞다.
* **`current/kit_line_shift.patch`의 `draft_b26_backfill_audit.spec.md` hunk(8건)는 이중 이동이라 버려야 한다.** 현재 초안에 다시 돌리면 `b26v4_head.py`에서도 12건이 이중 이동된다.
* 보수성은 S2 때문에 문서 주장보다 약하다. 실제 초안에서는 오탐 0건을 측정했다.
