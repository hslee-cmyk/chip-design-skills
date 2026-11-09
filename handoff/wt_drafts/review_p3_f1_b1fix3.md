# review_p3_f1_b1fix3 -- F1 card b1fix3 개정 독립 검증 (2026-10-07)

검증자: 독립 verifier(작성자 아님. 앞선 review_p3_f1_b1fix.md·review_p3_f1_b1fix2.md 작성자와도 다름).
대상: `_drafts/draft_p3_f1.spec.md` (vs `.pre-b1fix3.bak`), kit `p3kit_f12/{f12_execstr,f12_equiv,f12_f1sim}.py` (vs `.pre-b1fix3.bak`), selftest `p3kit_f12/out/b1fix/selftest_execstr_b1fix3.py`.
샌드박스: `C:/g407` 하나(TMP/TEMP 그 아래, cd 없이 절대 경로, clone `-c core.autocrlf=false --no-local`), 작업 저장소는 읽기만 함. 끝에 삭제.

## 판정: **B 0 · S 0 · minor 4** -- 규칙 문언은 F2 card로 옮길 만큼 확정됐다(minor는 옮길 때 문장 몇 개를 보태면 되고, 잰 수치는 바뀌지 않는다)

## 1. 계약 1 (e)를 카드 문언만 보고 직접 구현해 전수 스캔 (kit은 import하지 않음)

- 구현: `C:/g407/me/aud_execstr.py`(카드 문언에서 바로 씀 -- (s1)·(s2) 옵션 구간·`-W`/`-X`·(s3) 모양 조건, ① 상수 / ② 대입문 값(`=`·`a=b=`·주석 대입·`+=`, 그 밖 증강 대입은 규칙 밖 잎)을 w1~w3·`+`로 다시 풂, 순환 가드 / ③ 보통 함수 위치 매개변수 → 이름 호출 인자(같은 이름 def 전부 합침, 메서드 제외), 템플릿 `__f12_fmt_<k>__` 채움과 import 모듈 자리의 상수 인자 채움(m4), 규칙 밖 자리 = (파일, 줄), f-string 멈춤. E3_AST·E3B `file_reads`는 design §10 코드 그대로 쓰고 ACF에도 적용).
- 사슬: `mk_chain_r1.sh C:/g407/f <repo> g1_kit/install_proto.py 6c724de` → exit 0. D-11 `3273d10`, G1 `b5c40b1`('installed 4'), M1~M9 `c143e10`(import_fail 전부 {}), M9 정정 **`fd75bd8` = F1 모의 base**, F1 모의 `b25bb7f`(`changed 72 notes 2 d17 files 8`), F2 모의 `e25dd15`, 삭제 집합 SD 49·ACF 2.
- 삭제 집합도 따로 계산함(SD = base SD 최상위 `from <새 N3.10 모듈> import`가 묶는 이름 중 SD 안 어디서도 Load하지 않는 것, ACF = B0에 없던 최상위 import 줄 중 Load하지 않는 것) → SD 49·ACF 2 `_as_set`·`_theta_evidence_for_pair`, 사슬 출력과 **같음**.

| rev | 추적 .py | 실행 문자열 (s1/s2/s3) | D-9 밖 | (a)(b) 자리 | 파싱 실패 | f-string 멈춤 | 규칙 밖 자리 / D-9 밖 (파일) |
|---|---|---|---|---|---|---|---|
| `fd75bd8` (F1 모의 base) | 376 | **16** (0/4/12) | **3** | **1** = `test_b34_grammar_explicit.py:123` (SD 10이름, e3 0, ACF 0) | **0** | 0 | **21 / 8 (8)** |
| `b25bb7f` (F1 모의) | 376 | 16 (0/4/12) | 3 | **0** | 0 | 0 | 21 / 8 (8) |
| `6c724de` (gate) | 368 | 16 (0/4/12) | 3 | 1 (B34:123) | 0 | 0 | 21 / 8 (8) |
| `863a037` (gate master) | 383 | **17** (0/5/12) | **3** | **1** (B34:123) | **0** | 0 | **21 / 8 (8)** |

- 기대값(16 / 863a037 17, D-9 밖 3, (a)(b) 1 = B34:123, 파싱 실패 0, 규칙 밖 21 / D-9 밖 8)과 **모두 같다**.
- **자리마다 kit 출력과 대조**(`C:/g407/me/cmp_sites.py` -- kit 출력은 샌드박스에서 kit을 다시 돌린 것): 네 rev 모두 실행 문자열 (경로, 줄, 자리 종류, e3 수, SD/ACF 삭제 이름) 집합이 같고, 규칙 밖 (경로, 줄) 집합이 같다(**차이 0**).
  - 더해진 9개를 확인함: (s2) `v3-exempt-binding/scripts/p7_other_tools.py:25`(`%` 템플릿), (s3) `v3-history-clone/scripts/c3_mixed.py` 48·49·50, `c3b_no_failing.py` 47·49, `c3c_failing_last.py` 48·49·50. import는 `pathlib`·`sys`·`rt_engine`(p7은 `json`·`merge_gate`·`reachability`·`subprocess`·`sys`·`weakening_diff`)이고 (a)·(b) 0이다. 카드 문장과 같다.
  - 863a037에서 더해진 것: `b26-pre-test-strengthen/scripts/tie_probe.py:13` (s2). import에 `stick_diagram`이 있지만 삭제 집합 읽기는 0이다. 카드와 같다.
  - `tools/gates/redteam/lib/rt.py` 규칙 밖 자리의 줄은 모의 사슬에서 751, gate에서 742다. G1 시제품이 rt.py에 9줄을 더했기 때문이다. `git diff 6c724de 863a037 -- tools`는 **0파일**로 확인함.
- 보조(내용 규칙): 파싱되고 import 문이 있는 문자열은 86개다. 그중 실행 문자열 14개를 빼면 72개로 kit `content_only` 72와 같다. 파싱되지 않는 import 모양 문자열은 6개로 같다.

## 2. 범위 확대 7 → 16 (m3 대입값 풀이) 판단: **받아들일 수 있고, 문언과 수치가 맞는다**

- 늘어난 9개는 모두 D-9 안이다(`.ai/verification`). 대상 계산은 D-9 밖 파일만 보므로 **F1 대상 집합은 그대로**다(D-9 밖 3, (a)(b) 1자리가 두 문언에서 같다). m3가 겨냥한 모양(`X = textwrap.dedent("""…""")`, `code = "…" % x`)은 놓치면 안 되는 실제 실행 경로다. 그것을 잡으려고 (s3) 합성 test 파일 쓰기까지 함께 닿게 되는 것은 '닫힌 쪽'의 정상 비용이다.
- 정당한 코드에서 F1을 멈추게 할 위험:
  - (s3)은 모양 조건 때문에 정의상 파싱 실패가 없다. 멈춤 조항은 (s1)·(s2)에만 걸린다. 그래서 이번 확대분(s3 8개)은 멈춤을 만들 수 없다. 실측 파싱 실패 0, f-string 0.
  - 남는 위험은 ②의 '파일 안 어느 스코프든'이다. 다른 함수에서 **같은 이름**에 파싱되지 않는 문자열이나 f-string을 대입하면 그 자리에서 거짓 멈춤이 난다. `def a(): code = "x = ("` / `def b(): code = "import os"; exec(code)` → 파싱 실패 2행이 잡히고, f-string이면 멈춤 표지가 붙는다. kit과 내 구현 모두 이렇게 재현된다. 다만 멈춤은 '묻기'라서 판정이 틀리지는 않고, 코퍼스(376·383파일)에서는 0이다. b1fix2에도 있던 성질이고 m3가 값 모양을 넓혀 조금 늘었을 뿐이다. **허용**한다(minor 4에 적음).
  - D-9 밖에서 (s3)로 엔진 이름을 import하는 합성 fixture 문자열이 대상이 되어 F1이 test 입력을 고치게 될 위험도 따져 봤다. 실측 0이다(`content_only_engine` 25문자열 중 실행 문자열은 없다).

## 3. m1 동등성 사례와 m4 상수 인자 채움

- selftest의 ADV 13·REG 17 판정식을 **내 구현**에 어댑터로 그대로 적용함(`C:/g407/me/run_cases.py`): **30/30 PASS**. 포함한 경우는 메서드 가림(K.run이 ③을 덮지 않음, 파싱 실패 멈춤), 2단 매개변수(wrap2→run), `run(code=…)` 키워드(s2), 메서드·kw-only·lambda 기록, f-string 멈춤, ACF `file_reads`, `X = dedent(…)`, `code = "…" % x`, m4 `format`·`%`·from-import 상수 채움, 순환 가드 2종, 상수가 아닌 인자는 동적 import로 남음, 채운 판 파싱 실패 → 멈춤, 자리 단위, 같은 이름 보통 함수의 합이다.
- 내가 만든 적대 입력 33경우를 kit과 내 구현에 함께 돌림(`C:/g407/me/extra_cases.py`): **31 같음, 2 다름**.
  - 다름 1: `"C:/Python314/Python.exe"`(대문자). kit은 대소문자를 무시해 인터프리터로 보고, 문언("`python`으로 시작")대로 짠 내 구현은 보지 않는다 → minor 1. 코퍼스 영향은 0이다(두 구현의 전수 결과가 같다).
  - 다름 2: 같은 상수가 템플릿 경로와 템플릿이 아닌 경로로 둘 다 닿는 경우. 문언은 '템플릿으로만 닿은' 상수만 템플릿으로 본다. 그러니 원문 판만 파싱해 파싱 실패로 멈추는 kit이 문언에 맞는다. 내 구현은 채운 판도 더 판정했을 뿐이고, 둘 다 멈춤이다. 결함 아님.
  - 같은 결과로 확인한 경계: `-W`가 `-c`를 값으로 먹음, `-`·`-m`에서 끝남, `*opts`는 구간을 끝내지 않음, `%=`는 규칙 밖, `a = b =`, 튜플 대상·for 대상·다른 파일에서 가져온 이름은 규칙 밖, `{m!r}`·`%r`은 동적, `{0}`/`{}` 위치 채움, `format_map`·`%` dict·튜플 채움, ②·③ 경유 f-string 멈춤, `or` 인터프리터, `from sys import executable as E`, partial 기록, `compile(source=…)` 키워드는 규칙 밖, docstring은 제외.

## 4. 재확인 수치 (샌드박스 사슬 `fd75bd8`→`b25bb7f`, gate `6c724de` tools)

- V5(`weakening_diff`): **FAIL 11 · diff_paths 7 · `593483868d5d0a6011b9c921bcb9396e279cdef34669f5bf6f879bc9b08b9907`**. 둘째 해시(`merge_gate diff-hash`, 6파일): **`b585a5d480b24f55a3f31f32b8f78ffcd312d342525baac22619ab30426e457a`**. 둘 다 같음.
- `f12_equiv`(b1fix3): approved 7 → **62/7/3**(PASS/LISTED/FAIL. FAIL 3은 `test_selftest_{design_report,sizing_recipe,topology_library}.py` ast_same·from_same). approved 5 → 62/6/4, 없음 → 62/1/9. `d17_expect_vs_f1sim_diff` None. B34 `<str#0>` PASS·`<str#1>` SAME. 카드와 같다.
- B34 pytest: F1 `b25bb7f` **43 passed**, F2 `e25dd15` 43 passed.
- `parse_spec_card`(gate `863a037` `role_paths`): id `20261002-p3-callers-update`, phase 3, evidence_type equivalence, gate_change no, approval [`20260930-30-module-split-design`, `20261002-p3-f1-workspaces-write-path`] → 파싱됨. 카드 현재 판은 sha256 `81dd4fd25aabc2dc59e149ca96d4a7ea1717739b15ea93a98e5bf96111acd854`(122995 bytes)이다. remeasure 로그의 `3c96828…`(119807 bytes)는 이번 b1fix3 문언 추가 전 판이었다.

## 5. selftest 실행

- `selftest_execstr_b1fix3.py <새 kit> <.pre-b1fix3.bak>`를 샌드박스 사본으로 돌림(출력 json이 _drafts에 써지지 않게) → **rc 0**: 새 kit ADV 13 + REG 17 = **30/30 PASS**, 옛 kit ADV **13/13 FAIL**(모두 진짜 False이고 어댑터 예외는 0). 옛 kit REG는 3개 FAIL(m4 채운 판 파싱 실패·자리 단위·같은 이름 def 합)로 b1fix3에서 새로 생긴 동작이다. 판정식은 옛 kit을 실제로 거부한다.
- `ACF file_reads` ADV는 어댑터가 옛 kit의 `acf_drop_reads`를 `[]`로 고정해 실패하는 구조다. 옛 `file_reads`가 SD 고정이라 정당하지만, 옛 kit 실행이 아니라 어댑터 사실로 실패한다는 점은 적어 둔다.

## minor (F2 card로 옮길 때 보탤 문장 -- 모두 수치 불변)

1. **인터프리터 상수의 대소문자**: 문언은 "마지막 경로 성분이 `python`으로 시작"인데 kit은 대소문자를 무시한다(`Python.exe`). 닫힌 쪽인 '대소문자 무시'를 문언에 적을 것. 코퍼스 영향 0.
2. **따라가지 않는 경로가 조용히 빠짐**: ③ 매개변수의 **기본값**(`def run(c="import design_report")` + `run()`)과 (s3) 메서드 매개변수 경유(`self.fh.write(t)`)는 실행 문자열도 아니고 규칙 밖 기록에도 안 나온다(kit·내 구현 모두 같음, 문언과도 맞음). 두 경우 모두 내용 규칙 기록(파싱되고 import가 있는 문자열)에는 잡혀 auditor의 '흐름이 식 밖이면 멈춤' 조항으로 막히므로 구멍은 아니다. 다만 "기본값은 따라가지 않는다 -- 내용 규칙 기록으로만 보인다"는 한 줄을 (e) 끝의 '이 식이 보지 않는 것' 목록에 보탤 것.
3. **`.v<j>` 짝짓기 순서 미정의**: 카드 230행은 "j번째 판끼리"라고만 한다. 판 순서(예: 채움 경로 호출 자리의 소스 순서)를 정의하지 않아 F1이 호출 순서를 바꾸면 거짓 FAIL이 날 수 있다. 또 kit은 판 수가 다를 때 `exec_str_parse`라는 이름으로 실패를 적어 '파싱 실패'와 구별되지 않는다. 지금 코퍼스에는 판이 둘 이상인 문자열이 0이라 수치 영향은 없다.
4. **② '어느 스코프든'의 거짓 멈춤**(2절): 받아들인 닫힌 쪽 비용이지만, 문언에 "이름 충돌로 생긴 파싱 실패·f-string 멈춤도 멈춤이다(auditor는 그 자리를 보고 묻는다)"를 한 줄 적어 두면 F2 auditor가 다르게 읽을 여지가 없다.

## 결론

계약 1 (e) b1fix3 문언은 독립 구현으로 재현된다. F1 모의 base·F1 모의·gate 6c724de·gate master 863a037 네 트리 전수에서 kit과 자리마다 같고 카드 수치와도 같다. m1~m4 반영은 selftest(새 30/30, 옛 ADV 13/13 실패)와 독립 구현 30/30, 추가 적대 33경우(문언과 다른 kit 동작은 대소문자 1건)로 확인됐다. 7→16 확대는 D-9 안에서만 일어나 대상 집합을 바꾸지 않고 멈춤도 만들지 않는다. **규칙 문언은 F2 card로 옮길 만큼 확정됐다.** minor 1~3은 옮길 때 문장으로 보태면 된다.

샌드박스 `C:/g407` 삭제함(아래 끝 확인).
