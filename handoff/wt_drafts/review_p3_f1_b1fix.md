# review_p3_f1_b1fix -- F1 card B1·S1·m1 반영 갱신 독립 검증 (2026-10-06)

대상: `_drafts/draft_p3_f1.spec.md`(대 `.pre-b1fix.bak`, 17 hunk -- 23·93~107·139~142·160~161·179~192·200~203·210·218~244·264·287~292·307~308·333~350행),
kit `p3kit_f12/f12_execstr.py`(새 파일), `f12_f1sim.py`·`f12_equiv.py`(대 `.pre-b1fix.bak`).
검증자는 작성자가 아니고 review_p3_f1_b34t를 쓴 검토자도 아니다. 수치는 모두 sandbox `C:/g360`에서 직접 쟀다. 실제 저장소는 읽기만 했다.

## 판정 요약

| 등급 | 건 | 요지 |
|---|---|---|
| B | 없음 | B1 반영은 실측으로 성립한다. gate 트리 전수에서 SD 삭제 집합을 읽는 실행 문자열은 **1자리**(`test_b34_grammar_explicit.py:123`)다. 작성자 도구와 무관하게 짠 내 스캐너도 같은 결과를 냈다. F2 9 failed는 43 passed로 바뀌었다. V5·f12_equiv·둘째 해시 수치가 바이트까지 재현된다. |
| **S** | S1 | **계약 1 (e) 실행 자리 정의와 fail-closed 문장이 서로 부딪힌다.** kit `f12_execstr`는 ③(매개변수 경유)로 닿은 `write` 자리에서 스크립트 모양 조건을 건너뛴다. 그 결과 D-9 밖 출력 문자열 14개가 '실행 문자열'로 잡히고, 그중 **6개는 파싱되지 않는다**(`review11_r4_rules.py:658·695·716`, `review5_probe_follower_structure.py:57·63·105` -- `emit(…)`/`w(…)` → `f.write(s + "\n")`). 그런데 계약 1 (e)는 "파싱이 안 되는 실행 문자열은 FAIL로 적고 **멈추고 묻는다**"고 정한다. 카드의 실측 '43'은 이 6개를 포함하면서도 파싱 실패를 언급하지 않는다. 문언 (s3)이 ③ 뒤에도 적용되는지 정해지지 않아, auditor가 어느 쪽으로 구현하느냐에 따라 F1 base에서 멈출 수도, 지나갈 수도 있다. (s2)도 인터프리터가 아닌 `-c`를 잡는다(`git clone -c core.longpaths=true` -- `tools/gates/mutate_changed.py:61`. D-9 안에서는 `pytest -c cache + "/pytest_gate.ini"`의 `"/pytest_gate.ini"`가 파싱되지 않는 '실행 문자열'이 된다). |
| minor | m1 | 실행 자리 규칙이 놓치는 모양이 있다(아래 1.3). 실제 트리에서 실제로 실행되면서 놓치는 문자열은 1자리다(`docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/measure_selftest.py:40` `[PY, "-c", SIM.format(…)]`). SD reader는 아니다. 다만 파싱되지 않는 템플릿이라 '내용 규칙' 안전망에도 보이지 않는다. |
| minor | m2 | adv C의 둘째 해시 `05b8eec4…`는 변경 원문이 카드에 없어 재현할 수 없다. 내 adv C(같은 `_sd` 튜플에서 모듈 둘의 순서만 바꿈)는 `335f48c9…`로 다른 값이지만, 판정 행은 같다(V5 = 정직한 판 `593483…`, 둘째 해시 ≠, 판정기 LISTED). adv C 편집 원문을 적어 둘 것. |

## 1. 실행 문자열 규칙 판정

### 1.1 독립 스캐너와 전수 결과

`C:/g360/myscan.py`(f12_execstr를 보지 않고 짰다)는 **흐름에 기대지 않는 내용 우선** 방식이다.
추적 blob 전부(`ls-tree` blob만, `cat-file --batch`)를 본다. `.py`에서는 모든 문자열 식을 모은다: `Constant` str(docstring 포함, 표시만 함), f-string `JoinedStr`(자리표시자를 복원), `+`로 이은 상수.
그중 엔진 모듈 이름이 나오는 것마다 파싱하고(실패하면 dedent, 그래도 실패하면 정규식), `stick_diagram`의 모든 별칭(`import … as`, `import_module`/`__import__` 대입)에서 읽는 속성·`getattr` 상수·`from stick_diagram import`를 센다. 대입받은 이름의 사용 자리 문맥도 함께 적는다.
`.py` 밖 파일은 `python … -c`/heredoc/`exec(`/`runpy` 줄에 `stick_diagram`이 함께 나오는지 본다.
별도로 `dropstr.py`는 모듈 이름이 없어도 삭제 집합 이름을 `.이름`/`import 이름` 모양으로 담은 여러 줄 문자열을 찾는다(globals 주입 같은 경우를 대비).

| 트리 | 스캔 | SD 삭제 집합 49(사슬 출력 `stick_diagram.py dropped 49`)를 읽는 비 docstring 문자열(D-9 밖) |
|---|---|---|
| gate `6c724de`(368 `.py`) | myscan · dropstr · f12_execstr | **1 = `tests/contracts/test_b34_grammar_explicit.py:123` `_B34_FRESH_SCRIPT`(10이름)**. 셋이 같다. 나머지는 docstring 2(`probe_stage_partition.py:2`·`tools/gates/test_lint.py:159`)와 D-9 안 2파일(`v4diag_b34.py`·`p9-kcl-edges/make_record.py`)이다. |
| F1 모의 base `878c93c`(376) | myscan · f12_execstr | 같은 1자리 |
| F1 모의 `3cbfa0f`(B1 반영) | myscan | **0** |
| adv E `3ba3ce8` | myscan | 1(125행 `find_idiom_matches`) -- 계약 5 (b) 내장 판이 잡는다 |

`.py` 밖 239줄(39파일)은 모두 로그(`.bkit/audit`·redteam jsonl)·`.ai/verification` 기록·설계/계획 md다. 실행되는 스크립트(.sh/.bat 등)는 0이다.
결론: 카드의 "D-9 밖 1 = `test_b34_grammar_explicit.py:123`", "gate 368파일 전수도 같은 1자리"는 맞다.
흐름 규칙이 무엇을 놓치든, 삭제 집합 이름을 코드 모양으로 담은 문자열 자체가 그 하나뿐이다.

### 1.2 S1 상세 -- 과잉 포함과 fail-closed의 충돌

f12_execstr `exec_strings`에서 ③으로 닿은 자리의 kind는 `"param:<함수>"`다. 그런데 스크립트 모양 거름은 `if "write" in kind`일 때만 걸린다.
그래서 `def emit(s=""): … f.write(s + "\n")`처럼 매개변수가 `write`로 가는 함수의 호출 인자는 **로그 문구도** 실행 문자열이 된다.
F1 base `878c93c`의 43개 = param 27 · `-c` 14 · write 2이고, 카드 수치와 같다. D-9 밖은 17개다.

- 14개 = `emit`/`w` 경유 출력 문구(`review11_r4_gb2.py` 5, `review11_r4_rules.py` 4, `review5_probe_follower_structure.py` 5). 그중 **파싱 실패 6**이다. 예: 658행 `emit("  !! no default transfer view (no input port)")`.
- 1개 = `mutate_changed.py:61` `git clone … -c core.longpaths=true`. (s2)가 프로그램을 가리지 않아서 잡혔다.
- 진짜 실행 문자열은 2개다(B34 123·150).

계약 1 (e) (s3)은 "write의 첫 인자이면서 스크립트 모양인 문자열"이라고 하므로, 문언대로라면 ③ 뒤에도 모양 조건이 걸린다고 읽을 수 있다. 하지만 ③은 "매개변수를 실행 자리로 넘기면"이라고만 한다. 매개변수 단계에서는 모양을 알 수 없으므로 두 가지 구현이 모두 문언에 맞는다.
kit처럼 구현하면 F1 base에서 파싱 실패 6이 나와 "멈추고 묻는다"가 발동한다. 카드 '작성 전 실측'은 이 6개를 보고하지 않는다.
요청:
(1) "(s3)의 모양 조건은 ③으로 닿은 상수에도 적용한다"를 문언에 넣는다. (s2)는 리스트 첫 원소가 인터프리터(`sys.executable` 또는 상수 `python*`)인 경우로 좁히거나, 아니면 명시적으로 닫힌 쪽으로 두되 파싱 실패 처리를 (s1)·(s2) 인터프리터 자리에만 건다.
(2) kit를 고치고 다시 센다. 내 예상은 D-9 밖 2개이고, 파싱 실패는 0이다.
(3) 카드 104행 '43'의 구성을 고친 정의로 다시 적는다.

### 1.3 m1 -- 놓치는 모양(일반성)

| 모양 | 규칙 결과 | 실제 트리 |
|---|---|---|
| 자리의 식이 호출로 감싸임(`SIM.format(…)`·`textwrap.dedent(S)`·`S % x`·`str(S)`) | 놓침(leaves가 `Call`/`BinOp(Mod)`에서 멈춤) | **`measure_selftest.py:40`** `[PY, "-c", SIM.format(assets=…, mod=mod)]` -- 실제로 실행된다. `import {mod} as _m`는 argv 템플릿이라 SD reader는 아니다. 파싱되지 않아 content-only 안전망(`parse` 필요)에도 안 보인다 |
| f-string `JoinedStr`가 자리에 옴 | 놓침(상수가 아님) | 0 |
| 이름이 상수가 아닌 식에서 대입받음(`X = dedent("""…""")`, `X = A + B`, `X += "…"`) | 놓침 | 0 |
| 문자열 명령(`subprocess.run("python -c …", shell=True)`·`os.system`) | 놓침((s2)는 리스트 표시만) | 0 |
| `exec(code, {"sd": stick_diagram})` 처럼 globals로 모듈 주입 | 문자열은 잡히지만 내장 파일 안에 import가 없어 (b) `file_reads`가 못 봄. 바깥 파일의 dict 값 자리는 계약 3 (바) 탈출 ④로 잡힘 | 0 |
| 템플릿을 `write_text(T.format(…))`로 쓰고 경로로 실행(runpy·subprocess 파일) | 놓침((s3)는 상수·이름만) | 0 |
| 다른 파일의 상수를 import해 넘김 | 놓침('같은 파일 안') -- 문언의 content-only 목록 + 멈춤 조항이 부분적으로 보완한다(파싱되는 것만) | 0 |
| 메서드 호출(`obj.f(s)` -- 매개변수 0번이 `self`), keyword-only 매개변수, `partial`/`lambda` | 놓침(위치 어긋남) | 0 |
| `importlib`/`runpy`로 추적 `.py` 파일 실행 | 해당 없음(그 파일 자체가 E3·E3b 대상) | -- |

현재 판정 수치에는 영향이 없다. 권고: leaves를 `Call(attr ∈ {format, replace, strip}, func=dedent)`의 수신자·첫 인자, `JoinedStr`의 상수 부분, `BinOp(Mod)`의 왼쪽까지 넓힌다. content-only 안전망은 파싱 실패 문자열도 `\bimport\b` 정규식으로 목록에 올린다(그러면 SIM이 보인다).

## 2. 재측정(내 사슬)

사슬: `bash p3kit_f12/mk_chain_r1.sh C:/g360/f <chip-design-skills> g1_kit/install_proto.py 6c724de` → exit 0.
D-11 'already present' 빈 커밋 `8ce75eb`, G1 `bab1527`('installed 4'), M1~M9 `db18be7`(`import_fail` 전부 {}), M9 정정 `878c93c` = F1 모의 base, F1 모의 `3cbfa0f`(현재 재작성기 = B1 반영, `changed 72 notes 2 d17 files 8`), F2 모의 `8e4ef26`.

| 주장 | 실측 | 결과 |
|---|---|---|
| V5(gate `6c724de` `weakening_diff.py`, base → F1) FAIL 11 · `diff_paths` 7 · `diff_hash 593483868d5d…` | FAIL **11**(conftest 1 + B34 `<module>` 1 + 리터럴 9) · paths **7** · `593483868d5d0a6011b9c921bcb9396e279cdef34669f5bf6f879bc9b08b9907` | 일치(바이트) |
| B34 파일 pytest(gate ini, `--gmid-phase=3`) F1 43 passed · F2 43 passed | `3cbfa0f` 43 passed · `8e4ef26` **43 passed** | 일치 |
| 옛 판 F2 9 failed | `8e4ef26`에 `_B34_FRESH_SCRIPT`만 base 원문으로 되돌린 트리 → **9 failed · 34 passed**, `AttributeError: … 'find_idiom_matches'` | 일치 |
| f12_equiv 7단위 62/7/3 | 72파일 PASS 62 · LISTED 7 · FAIL 3(selftest 3 `ast_same`·`from_same`), B34 LISTED: `<str#0>` PASS · `<str#1>` SAME, `d17_expect_vs_f1sim_diff` [] | 일치 |
| 5단위 62/6/4 | 62 · 6 · 4(+ B34 `listed_changes_approved`) | 일치 |
| 목록 없음 62/1/9 | 62 · 1 · 9 | 일치 |
| 계약 5 (b) 내장 판 base 1 → F1 0 | myscan 기준 1(123행, 10이름) → 0 | 일치 |
| content 규칙만 걸리는 21문자열·7파일 | f12_execstr content_only 중 E3 걸림 21 · 7파일(gate·F1 base 같음) | 일치 |

## 3. S1 (a) -- 승인 기록 둘 · 둘째 해시(gate `6c724de` 읽기 전용 확인)

- `parse_approval_header`: `diff_path`만 여러 줄을 허용하고, 그 밖 키가 중복되면 `GateError("승인 기록 키 중복")`를 낸다. 실제로 `target` 두 줄 기록을 만들어 `merge_gate.py parse-approval`에 넣으면 "승인 기록 키 중복: target"이 나온다. 기록 ⓐ(diff_path 1)와 ⓑ(diff_path 6줄, `target_kind: diff`, 40자 base·head)는 둘 다 파싱된다.
- 로더 규칙 9(`merge_gate.py` 1218~1224행): `checks.V5.basis`에 있는 64자리 16진마다, head 트리 승인 기록 중 `target_kind == "diff"`이면서 `target`이 그 값인 기록이 있어야 한다. 기록의 존재만 강제하고 재계산은 하지 않는다. 카드 문장과 같다.
- `diff-hash` 하위 명령은 `--repo --base --head paths…` → `compute_diff_hash`다. 계산은 정렬한 경로마다 `"%s\t%s\t%s\n" % (경로, base blob, head blob)`(없으면 `-`)를 이은 sha256이고, `forbid_same`이라 바뀌지 않은 경로는 오류다. 카드가 적은 형식과 **정확히 같다**. weakening_diff `diff_hash`도 같은 식이다.
- 둘째 해시: gate 명령의 출력 `b585a5d480b24f55a3f31f32b8f78ffcd312d342525baac22619ab30426e457a`는 내가 `rev-parse`로 따로 낸 값과 같다. 카드와도 같다.
- 적대 표 재현(F1 모의 위 한 커밋씩, 승인 7단위, `--only` 그 파일):

| adv | V5 `diff_hash` | 둘째 해시 | 판정기 | 카드 |
|---|---|---|---|---|
| 정직 `3cbfa0f` | `593483868d5d` | `b585a5d480b2` | LISTED | 같음 |
| A `0056328`(c1: 206행 진입점 교체 + 210행 `assert [] == []`) | `1d660102daaf` ≠ | `7b326638f102` ≠ | LISTED(못 잡음) | 해시까지 같음 |
| C `f7be7d2`(`_sd` 튜플 모듈 순서) | **`593483868d5d` = 정직** | `335f48c9ba3a` ≠ | LISTED(못 잡음) | 행 같음, 해시는 편집이 달라 다름(m2) |
| D `b3aeec5`(내장 144행 oracle 바꿔치기) | `f3d938bfbf24` ≠ | `84cf76a71388` ≠ | **FAIL** `str#0:ast_same`·`str#0:attr_same` | 해시까지 같음 |
| E `3ba3ce8`(내장 138행 `stick_diagram.` 경유) | `606f5bc62393` ≠ | `1c897c430fd8` ≠ | **FAIL** `str#0:def_module` + 내장 reader 1 | 해시까지 같음 |

adv C를 기계로 잡는 것은 둘째 해시 하나뿐이다. 카드 주장과 같다.
참고(판정 아님): ⓑ도 `target_kind: diff`라서 weakening_diff `approved_hashes`에 함께 들어간다. 그 경로·blob 집합과 우연히 같은 V5 diff가 있어야만 효력이 생기므로 실해는 없다.
남는 것: ⓑ의 재계산과 'diff 줄 = 인용 원문' 대조는 auditor 몫이다. gate는 basis에 해시가 있는지만 본다. 카드가 이것을 정직하게 밝히고 있다.

## 4. m1(옛 검토) 단위 사유 -- 정확

F1 base `test_b34_grammar_explicit.py` AST 실측:
- `_b34_exc_problems`(65) = dunder 73(도우미 def).
- c1(169)·c2_idioms(220)·c2_netclass(228)·selfcheck(354) = 도우미 호출, dunder 없음.
- c5_import(269) = dunder 271, 도우미 호출 없음.
- c8(299) = dunder 301, **도우미 호출 없음**.

판정기 `listed_changed_units` = c1·c8이다. 카드 184~187·218행의 단위별 사유와 "c1은 dunder 자리가 아니다"는 맞다.

## 5. parse_spec_card(gate `6c724de`)

`role_paths.parse_spec_card(text, "20261002-p3-callers-update")` → `id` 일치, `phase "3"`, `evidence_type equivalence`, `gate_change no`, `approval` 2개, 예외 없음.
`git diff --stat 2183f2e 6c724de`는 docs spec·interface 2파일뿐이고 `tools/` 변경은 0이다.

## 6. 정리

- sandbox: `C:/g360`(clone `--no-local -c core.autocrlf=false`, origin 제거, TMP/TEMP `C:/g360/tmp`, cd 없음). 끝에 삭제했다.
- 판정: **B 0 · S 1 · minor 2**. S1(③ 경유 write 자리의 모양 조건, (s2) 인터프리터 한정 ↔ 파싱 실패 멈춤 조항)을 문언과 kit에서 고치고 '43'을 다시 센 뒤 확정할 것. B1·옛 S1·옛 m1 반영은 실측으로 성립한다.
