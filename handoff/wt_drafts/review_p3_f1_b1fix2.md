# review_p3_f1_b1fix2 -- F1 card 계약 1 (e) 개정(b1fix2) 독립 검증 (2026-10-07)

대상: `_drafts/draft_p3_f1.spec.md`(sha256 `84e7945f…e18485`, 117113 B) 대 `.pre-b1fix2.bak`(hunk 4개 -- 95~124행 계약 1 (e), 282행 kit 설명, 364~366행 b1fix2 재측정, 370~373행 adv C 원문),
kit `p3kit_f12/f12_execstr.py`·`f12_equiv.py`·`f12_f1sim.py` 대 `.pre-b1fix2.bak`.
검증자는 작성자가 아니고 review_p3_f1_b1fix 작성자도 아니다. 모든 수치는 sandbox `C:/g385`에서 직접 쟀다. 실제 저장소는 읽기만 했다(clone `--no-local`, `core.autocrlf=false`).
**계약 1 (e) 스캐너는 카드 문언만 보고 새로 짰다**(`C:/g385/myexec.py`. f12_execstr를 import하지 않았고, 전수 결과를 낸 뒤에 kit을 읽어 비교했다).

## 판정 요약

| 등급 | 건 | 요지 |
|---|---|---|
| B | 없음 | 문언에서 짠 독립 스캐너가 카드 수치를 그대로 재현했다. F1 모의 base: 실행 문자열 **7**((s2) 3·(s3) 4·(s1) 0), D-9 밖 **3**(B34 123·150, `measure_selftest.py:21`), 파싱 실패 **0**, f-string 잎 **0**. (a)·(b)에 걸리는 것은 **B34:123 하나**(SD 삭제 집합 10이름)뿐이다. 규칙 밖은 **22자리**(D-9 밖 8자리·8파일)이고 모두 추적 파일 소스의 `exec(compile(…))`다. V5 11/7/`593483868d5d…`, 둘째 해시 `b585a5d4…`, f12_equiv 62/7/3·62/6/4·62/1/9, adv C 둘째 해시 `05b8eec4…`도 바이트까지 같다. |
| S | 없음 | 옛 S1(③ 경유 모양 조건, (s2) 인터프리터 무관)은 문언과 kit 모두에서 해소됐다. 파싱 실패가 0이라 fail-closed 조항이 F1 base에서 걸리지 않는다. |
| minor | m1 | kit `f12_execstr`는 '문언과 같은 식'이라고 적혀 있지만 문언과 다른 곳이 넷 있다(1.3). ③ 함수표가 이름 dict라 같은 이름의 def가 둘 이상이면 마지막 것만 남고, 속성 호출도 같은 함수로 본다. 그래서 적대 입력에서 **파싱 실패(멈춤) 하나와 2단 매개변수 경유 하나를 놓친다**. 메서드·keyword-only·lambda 경유는 '규칙 밖'으로 기록하지 않고 조용히 버린다. `file_reads`는 SD만 보고 ACF를 보지 않는다. 실제 트리 영향은 0이다(독립 스캐너와 실행 문자열 집합이 같음). kit은 판정 도구가 아니지만 카드 282행·주석의 '같은 식' 표현을 고치거나 kit을 고칠 것. |
| minor | m2 | '규칙 밖 40잎'은 잎을 세는 단위가 문언에 없어 재현이 구현에 따라 달라진다. 내 스캐너는 같은 이름의 대입마다 잎 하나로 세어 **50잎**이 나왔다. 자리 22(줄 단위)와 D-9 밖 8은 같다. 잎 단위를 정의하거나 카드에서 잎 수를 빼고 자리 수만 남길 것. |
| minor | m3 | ②는 '문자열 상수를 대입받은 이름'만 본다. `X = textwrap.dedent("""…""")`·`code = "…" % x`처럼 대입값이 감싼 식(w1~w3)이면 규칙 밖(기록만)이 된다. 내장 스크립트에 흔한 관용구다. 실제 트리에서는 D-9 안 `.ai/verification/20260930-v3-exempt-binding/scripts/p7_other_tools.py:25` 한 자리뿐이고 D-9 밖은 0이다. 권고: 대입값에도 w1~w3 풀기를 적용한다(순환 가드 필요 -- `src = src.replace(…)`). D-9 밖 수치는 바뀌지 않는다. |
| minor | m4 | 템플릿 자리표시자가 import 모듈 자리에 오면 (a)·(b)에서 빠진다. 예: `"import {mod} as m\nm.find_idiom_matches()".format(mod="stick_diagram")`. 이 경우 F2 뒤에 깨지는 삭제 집합 reader가 '기록만'으로 지나간다. design E3/E3b가 상수가 아닌 import를 보지 않는 것과 일관되므로 B는 아니다. 그래도 `format`의 해당 키워드 인자가 문자열 상수이면 그 값으로 채워 판정하는 편이 닫힌 쪽이다. 실제 트리 영향은 0이다(`measure_selftest` `{mod}`는 argv 템플릿이고 SD 읽기 0). |
| minor | m5 | gate master가 이제 `2db7622`다. `6c724de`와 비교하면 `tools/` 차이는 0이고, D-9 밖 추가 `.py`는 `contracts/test_b26pre_existing_paths.py` 하나다(실행 문자열 0). D-9 안에는 `.ai/verification/20260930-b26-pre-test-strengthen/scripts/*.py` 14개가 늘었다. 그래서 gate 전수는 **실행 7 → 8**이다(D-9 안 `tie_probe.py:13` (s2) 1 추가, SD 삭제 집합 읽기 0). D-9 밖 3, (a)(b) 1자리, 파싱 실패 0, 규칙 밖 22자리는 같다. 카드는 `6c724de` 수치라 틀린 것은 아니다. base를 갱신할 때 같이 적을 것. |

## 1. 계약 1 (e) 독립 구현과 전수 결과

### 1.1 구현(문언 → 코드)
- 실행 자리: (s1)은 `Name` 호출 `exec`·`eval`·`compile`의 `args[0]`이다. (s2)는 첫 원소가 인터프리터인 List·Tuple이다. 인터프리터 = `sys.executable`, `from sys import executable` 이름, 마지막 경로 성분이 `python*`인 상수, 그것을 대입받은 이름(고정점, `or` 한쪽 포함). 옵션 구간 규칙은 이렇다. `-c`이면 다음 원소가 자리다. `-m`이면 끝난다. `-W`·`-X`는 다음 원소를 먹는다. `-`로 시작하는 다른 상수는 계속한다. `-`나 비옵션 상수에서 끝난다. 비상수와 `*`는 계속한다. (s3)은 `.write_text`·`.write`의 `args[0]`이고, 닿은 상수에 모양 조건(parse, 실패하면 dedent, 트리에 import 있음)을 건다.
- 닿음: `+`는 양쪽, w1 `%`는 왼쪽(템플릿), w2는 `format`·`format_map`(템플릿)과 `replace`·`strip`·`lstrip`·`rstrip`의 수신자, w3는 `dedent`·`textwrap.dedent`·`str`의 첫 인자다. 잎에서는 다음처럼 처리한다. ① 상수. ② 상수를 대입받은 이름(어느 스코프든). ③ 둘러싼 def의 위치 매개변수이면 그 이름을 부르는 모든 `Name` 호출의 같은 위치·같은 키워드 인자를 같은 자리 종류·템플릿 여부로 다시 넣는다(고정점). 메서드·kw-only·lambda는 규칙 밖으로 기록한다. f-string은 (s1)·(s2)에서 멈춤이다. 나머지는 규칙 밖으로 기록한다.
- 템플릿은 자리표시자를 `__f12_fmt_<k>__`로 채운다(`{{`·`}}`·`%%`는 글자 하나). 그 내장 트리에 design §10 `E3_AST` walk와 `E3B_AST file_reads`(design 원문을 옮김. ACF에도 같은 식)를 적용한다. 삭제 집합은 사슬 출력 SD 49 + ACF 2이다.

### 1.2 전수 결과(독립 스캐너)

| 트리 | `.py` | 실행 | (s1)/(s2)/(s3) | D-9 밖 | 파싱 실패 | f-string | (a)(b) 걸림 | 규칙 밖 자리(줄) / D-9 밖 |
|---|---|---|---|---|---|---|---|---|
| F1 모의 base `e368c60`(= M9 정정) | 376 | **7** | 0/3/4 | **3** = B34 123·150, `measure_selftest.py:21` | **0** | 0 | **B34:123 1자리**((b) 10이름, (a) 0) | **22** / **8**(8파일) |
| F1 모의 `edfdf04` | 376 | 7 | 0/3/4 | 3(B34 125·154, measure 21) | 0 | 0 | **0** | 22 / 8 |
| gate `6c724de` | 368 | 7 | 0/3/4 | 3 | 0 | 0 | B34:123 1자리 | 22 / 8 |
| gate `2db7622`(현재 master) | 383 | **8** | 0/4/4 | 3 | 0 | 0 | B34:123 1자리 | 22 / 8 |

- B34 123·150은 둘 다 ③ 경유다(`_b34_fresh_process` 162행 `[sys.executable, "-B", "-c", script, …]` ← 301행·271행 호출). `measure_selftest.py:21` `SIM`은 40행 `[PY, "-c", SIM.format(…)]`로 닿는 템플릿이고, 채운 판의 import는 `ast`·`sys`·동적 `__f12_fmt_1__` 1자리다. 카드 문장과 같다.
- (s3) 4개는 모두 D-9 안이다(`install_probe.py:9`·`probe_selection.py:26`·`c1_head.py:44`·`c4_clonefail.py:44`).
- 규칙 밖 D-9 밖 8자리는 `hooks/role_{guard,diff_guard_bash,diff_guard_stop,session_start}.py:48`·`.githooks/gmid_gate.py:49`·`tools/gates/githooks/gmid_gate.py:49`·`tools/gates/redteam/lib/rt.py:742`·`30-module-split/scripts/e_inst_p3.py:27`이다. 소스는 각각 `git cat-file blob …:tools/gates/role_paths.py`, `open(run_harness.py)`, `sb.repo_read('show', …)`·`read_text`이고 **모두 추적 `.py` 파일의 내용**이다. 그 파일 자체가 이미 E3·E3b 대상이라 문자열 규칙이 따로 볼 것이 없다.
- 내용 안전망(파싱되고 import 있음, 또는 줄 머리 import 모양)에서 E3에 걸리는 D-9 밖 문자열은 21개·7파일이다. 카드와 같다.
- kit(`f12_execstr` b1fix2, `--drop` 51이름) 대조: base 7·gate `2db7622` 8, 파일·줄·자리 종류·템플릿·삭제 집합 읽기가 모두 내 결과와 같다. 규칙 밖은 kit 40잎·22줄이고 나는 50잎·22줄이다(m2).
- (s2)에서 버린 `-c` 리스트(D-9 밖) 5개는 모두 맞게 버렸다. `mutate_changed.py:61` `git clone -c`, `:655` `[ns.python, "-P", "-m", "pytest", "-c", ini]`(`-m` 뒤), `rt.py:905`·`role_hooks.py:301` `["-m","pytest","-c",…]` 조각, `rt.py:267` `[bash, "-c", cmd]`이다.

### 1.3 적대 입력(`C:/g385/adv/r/adv.py` 32경우 -- 내 구현 = 문언 기대, kit 비교)

| 경우 | 문언 기대 | 독립 구현 | kit |
|---|---|---|---|
| `[exe, "-W", "-c", S]`(`-W`가 `-c`를 먹음) | 아님 | 아님 | 아님 |
| `[exe, "-W", "ignore", "-c", S]` / `"-X","utf8"` / `"-I"` 튜플 | 실행 | 실행 | 실행 |
| `[exe, "-m", "pytest", "-c", S]` / `[exe, "-", "-c", S]` | 아님 | 아님 | 아님 |
| `[exe, *extra, "-c", S]` | 실행(닫힌 쪽) | 실행 | 실행 |
| `PY = os.environ.get(..) or sys.executable` | 실행 | 실행 | 실행 |
| `"C:/Python314/python.exe"` 상수 | 실행 | 실행 | 실행 |
| `exec(str(S))`, `exec(S.replace(..).strip())`, `exec(S % 3)` | 실행(`%`는 템플릿) | 실행, E3 걸림 | 실행 |
| `T.format(mod="stick_diagram")`의 `import {mod}` / `from {pkg} import` | 동적 import, (a)(b) 아님, 기록 | 같음 | 같음(m4) |
| `def emit(s): f.write(s+"\n")` + `emit("hello (")` | 아님(모양 조건) | 아님 | 아님 |
| 같은 emit + `emit("import stick_diagram\nstick_diagram.find_idiom_matches()")` | 실행, (b) 걸림 | 걸림 | 걸림 |
| `def run(code): [exe,"-c",code]` + `run("x = (")` | 실행, **파싱 실패 → 멈춤** | 멈춤 | **놓침**(같은 파일의 메서드 `K.run(self, code)`가 이름 dict를 덮어 위치가 1로 어긋남) |
| `wrap2(c): return run(c)` + `wrap2("import design_report")` | 실행(2단 ③) | 실행 | **놓침**(같은 원인) |
| `run(code="import sizing_recipe")` | 실행((s2)) | 실행 | 실행, 다만 자리 종류를 (s1)로 적음(메서드 쪽 매칭) |
| f-string `[exe, "-c", f"import {m}"]` | 멈춤 | 멈춤 | unresolved에 기록(`JoinedStr`), 멈춤 표지 없음 |
| 메서드 `K().run("…")`, kw-only `kwo(code=…)`, `lambda c: exec(c)` | 규칙 밖 기록 | 기록 | **기록 없음**(조용히 버림) |
| `X = dedent("""…""")`; `exec(X)` / `X29 = S`; `exec(X29)` | 규칙 밖 기록 | 기록 | 기록(m3) |
| `exec("import audit_current_forced as a; a._theta_evidence_for_pair")` | (b) 걸림(ACF 삭제 집합) | 걸림 | **안 걸림**(`file_reads`가 SD 고정) |
| `shutil.which("python3")`, `["/usr/bin/env","python3","-c",S]`, `[exe,"-c"]+[S]`, `cmd[2]=S` | 문언 밖(기록도 없음) | 같음 | 같음 |

마지막 행의 모양들은 문언이 보지 않고 규칙 밖 기록에도 나오지 않는다. 실제 트리에는 0이다(D-9 밖 `-c` 리스트 전수가 위 5개뿐). 내용 안전망은 그 상수가 파싱되고 import가 있으면 보인다. 판정 영향은 없으므로 등급을 매기지 않는다.

## 2. '규칙 밖 → 기록만, f-string → 멈춤' 설계 판단

**수용한다(fail-closed로 충분)**. 근거는 넷이다.
1. 작성자 주장대로 F1 base에는 D-9 밖 규칙 밖 자리가 **8개 실재**한다(위 1.2 목록). 규칙 밖을 모두 멈춤으로 하면 F1은 이 8자리에서 멈춘다.
2. 8자리는 모두 **추적 `.py` 파일의 내용**을 실행한다(role_paths.py·run_harness.py·redteam probe). 실행되는 코드는 그 파일 자체로서 이미 E3·E3b·계약 1 (a)(b)의 파일 단위 대상이다. 멈춤은 안전을 더하지 않고 사람 판단만 8번 부른다.
3. 문언이 정적으로 내용을 알 수 없는 잎 가운데 '상수로 쓰인 코드'가 숨을 수 있는 모양은 f-string(멈춤으로 닫힘)과 감싼 대입(m3), 동적 import 템플릿(m4)이다. 이 가운데 실제 트리 D-9 밖에 있는 것은 0이다. 이 모양들은 내용 안전망(파싱 + import → 기록, 그중 '흐름이 식 밖으로 보이면 멈추고 묻는다')에도 함께 보인다.
4. 대안인 '규칙 밖 잎 중 출처가 파일 읽기가 아닌 것만 멈춤'은 출처 판정 자체가 새 규칙을 필요로 한다. 지금 규모에서는 기록 + 안전망이 비용 대비 낫다.

조건: auditor 판정 기록에 규칙 밖 자리 목록(줄 단위)을 남기고, 출처가 '추적 파일 읽기'인지 사람이 한 줄로 확인하게 할 것. 이것이 잎 수보다 유용하다(m2와 함께). m3를 반영하면 '감싼 대입'도 규칙 안으로 들어와 기록만으로 지나갈 여지가 더 줄어든다.

## 3. 재측정(내 사슬)

사슬: `bash p3kit_f12/mk_chain_r1.sh C:/g385/f <chip-design-skills> g1_kit/install_proto.py 6c724de` → exit 0. 단계는 이렇다. D-11 빈 커밋 `0ee4987`, G1 `d5d41ad`('installed 4'), M1~M9 `1c64063`(`import_fail` 전부 {}), M9 정정 `e368c60` = F1 모의 base, F1 모의 `edfdf04`(`changed 72 notes 2 d17 files 8`), F2 모의 `98049c3`, 삭제 집합 SD 49·ACF 2.

| 주장 | 실측 | 결과 |
|---|---|---|
| V5(gate `weakening_diff.py` -- `2db7622` 판, `tools/` 차이 0) base → F1: FAIL 11·`diff_paths` 7·`593483868d5d…` | FAIL **11**(conftest 1 + B34 `<module>` 1 + 리터럴 9)·**7**·`593483868d5d0a6011b9c921bcb9396e279cdef34669f5bf6f879bc9b08b9907` | 일치 |
| 둘째 해시(6파일, `merge_gate.py diff-hash`) `b585a5d4…` | `b585a5d480b24f55a3f31f32b8f78ffcd312d342525baac22619ab30426e457a` | 일치 |
| f12_equiv 7단위 62/7/3 · 5단위 62/6/4 · 없이 62/1/9 · `d17_expect_vs_f1sim_diff` [] | 72파일 **62/7/3**(FAIL = selftest 3 `ast_same`·`from_same`) · **62/6/4**(+B34 `listed_changes_approved`) · **62/1/9** · `[]`. B34 `<str#0>`(123) PASS · `<str#1>`(150) SAME | 일치 |
| adv C 패치(sha256 `0d4dea28…743a` -- 실측 같음), head blob `042c5f6` | `git apply` 성공, blob `042c5f623dbd…`. V5 FAIL 11·7·**`593483868d5d…` = 정직한 판**, 둘째 해시 **`05b8eec4500b6f888b6c2997e925021ba8da46dd6105fbe2eb9f98220a3575d3`**, 판정기 두 파일 LISTED | 일치(옛 m2 해소) |
| B34 파일 pytest(gate ini, `--gmid-phase=3`) F1 43 · F2 43 | `edfdf04` 43 passed · `98049c3` 43 passed | 일치 |
| 계약 5 (b) 내장 판 base 1 → F1 0 | 독립 스캐너 base B34:123(10이름) → F1 0 | 일치 |

kit 차이(`.pre-b1fix2.bak` 대비): `f12_f1sim`은 템플릿·파싱 실패 문자열을 재작성하지 않고 notes(멈춤)로 보낸다. `f12_equiv`는 `exec_strings_ex`와 템플릿 채운 판(`exec_str_text`)으로 내장 파일을 비교한다. F1 모의의 notes·changed 수는 그대로다(2·72). 문언과 맞는 변경이다.

## 4. parse_spec_card(gate `2db7622`)

`tools/gates/role_paths.parse_spec_card(text, "20261002-p3-callers-update")` → `id` 일치, `phase "3"`, `evidence_type equivalence`, `gate_change no`, approval 2, 예외 없음.
`git diff 6c724de 2db7622 -- tools`는 비어 있다. D-9 밖 변경은 `docs/02-design/specs/20260930-b26-pre-test-strengthen.spec.md`(M)와 `skills/analog-gmid-design/assets/tests/contracts/test_b26pre_existing_paths.py`(A)뿐이다(나머지 117은 `.ai/verification/**`).

## 5. 정리

sandbox `C:/g385`(사슬 `f/r`·worktree 2·gate clone·adv repo·스캐너)는 끝에 삭제했다. 실제 저장소 쓰기는 없다.
