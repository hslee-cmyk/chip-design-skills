# 독립 검토 -- FU card `20261002-p3-future-annotations` 초안

검토자: 독립 reviewer(작성자 아님). 대상: `_drafts/draft_p3_fu.spec.md`, `_drafts/fu_briefs.md`, `_drafts/p3kit_fu/`.
기준: design 30 초안 **v8.5**(`draft_phase3_design_v8.md` §6.5·D-29·§8 FU 행·§8.1), spec 양식 `docs/02-design/specs/_TEMPLATE.spec.md`(gate `master`).
재측정: gate `master` = 로컬 `master` = `dd60db6515b6fe80ab16349835c19aa75d4f292f`, 2026-10-02. 스크래치는 `C:/g190`만 썼다(`git clone --no-local` 복제본 `iso`·`base`·`fu`·`pp`,
게이트 사본 `cache` = `git archive gate/master tools/gates`). FU 모양 head는 **작성자 키트를 쓰지 않고 내가 따로 만들었다**(`mkfu.py`: 모듈 docstring의 `end_lineno` 뒤에 한 줄,
CRLF 작업 트리 → 인덱스 LF) = `351670bc`. 판정기도 모두 내가 따로 썼다(`co.py`·`ast1.py`·`jcmp.py`·`fut.py`). 저장소 쓰기 없음.

## 판정: **조건부 ready** -- B 0 · S 2 · minor 5

계약·판정 유형·수치는 재측정과 모두 맞는다. S 두 건(설계 v8.5와 어긋난 사실 문장, test 브랜치 없이 가는 착수 절차)을 고치면 순서 0 커밋을 해도 된다.

---

## 1. 재측정 결과(독립)

| 항목 | 초안 주장 | 재측정(`dd60db6` → `351670bc`) | 일치 |
|---|---|---|---|
| 넣는 자리 DR | docstring 2~27행, 첫 import 28행 `import html as _html` | `ast`: docstring 2–27, `body[1]` = Import 28행, 316줄, CRLF | ○ |
| 넣는 자리 ACF | docstring 1~37행, 첫 import 38행 `import sys` | docstring 1–37, Import 38행, 187줄 | ○ |
| diff 모양 | 2 files, 2 insertions, 인덱스 LF | `--stat` 2 files changed, 2 insertions(+), `cat -A`에 `^M` 없음 | ○ |
| 계약 1 AST `H = B[:1]+[I]+B[1:]` | 두 파일 참 | DR True·ACF True, `get_docstring` 같음 True | ○ |
| 계약 2 몸체 코드 객체 | 같음 DR 16(qualname 12)·ACF 5 = 21, 다름 0, `__annotate__` 다름 DR 5·ACF 4, 한쪽에만 있는 키 0 | 같음 DR 16·ACF 5, 다름 0, qualname 12·5, `__annotate__` 다름 5·4(같음 0), 한쪽에만 있는 키 [] | ○ |
| 계약 2 판정기 자기 점검 | 몸체에 문장 하나 → FAIL | `build_topology_device_table#0` 다름 1 → FAIL | ○ |
| 계약 3(a) PT3 | 1047 passed·15 xfailed, id 1062, 결과 차이 0 | 두 판 모두 1047 passed·15 xfailed(223 s / 224 s), id 1062 집합 같음, id별 결과 차이 0 | ○ |
| 계약 3(b) E-LIB | `hash` `1d2e3bf6…` 같음 | `e_lib.py` sha256 `045f65c8…`(P9 판정 기록 사본), base·head 모두 `1d2e3bf6acf762eb…` | ○ |
| 계약 3(c) E-INST | 22키 모두 같음, `raw_sha256` 파일럿 `2fc426d9…`·FC `ef3cd996…` | 아래 '부기' 참고(재측정 결과) | (부기) |
| 계약 4 V3 | PASS, 대상 DR·ACF, `mutants` 0, `survivors` [] | gate 판 `mutate_changed.py --gmid-phase=3 --gmid-strict=` → PASS, targets 2, mutants 0, survivors [] | ○ |
| V4 | `--interface-card`만 → ERROR exit 2, `--subject` 둘 → PASS `files` [] | 그대로(exit 2 / exit 0, `files` [], `findings` []) | ○ |
| V5·V6·V7 | PASS `diff_paths` []·`findings` []·`new_defs` [] | 그대로 | ○ |
| 계약 5 주석 읽기 | 추적 `.py` 5곳, 대상은 SD·SR 객체뿐, DR·ACF 0 | `git grep` 5곳(`test_dup_kcl_edges.py` 283·293, `test_dup_w_calc.py` 199·450, `probe_mirror_ratio_error.py` 85) -- DR·ACF 객체 0 | ○ |
| 계약 5 추가 확인 | -- | DR·ACF에 `class`·`@`(데코레이터)·`dataclass`·`NamedTuple`·`TypedDict`·`typing`·모듈 수준 주석 대입 **0**. 추적 `.py`(`.ai/` 밖)에 `pydantic`·`singledispatch`·`get_type_hints`·`annotationlib`·`__annotate__` **0**. DR·ACF `import *` 0, `__all__` 0, 모듈 속성 `annotations`를 읽는 곳 0. dataclass는 SR·SD에만 있다(이미 future 있는 파일) | ○ |
| DR·ACF를 이름으로 읽는 추적 `.py` | 21개(.ai 9·docs 2·A 2·tests 4·workspaces 4) | 21개, 같은 분포 | ○ |
| 계약 7 `reg_check.py` | exit 0 '발견 0' | head exit 0 '발견 0'; 레지스트리 217행 `design_report.py:32` 확인 | ○ |
| D0b 보호(배선) | FU 없이 `import_conflicts` `__future__` 갈림, FU 뒤 0 | 아래 §3 | ○(조건 붙음) |

부기 -- E-INST: 같은 체크아웃 경로 `C:/g190/iso`에서 base → head 차례로 실행(`e_inst_p3.py` sha256 `7d26134a…`). 결과는 §6에 적는다.

---

## 2. 판정 유형: equivalence + test 커밋 0 -- **타당**

**규칙 문장(gate `master` 계획서)**
* 680행(N3.12.3 순서 3): "equivalence면 base에서 통과 확인" -- test 커밋이 없으면 T = B이고, base 전체 PT3 통과(재측정 1047/15)로 성립한다.
* 686행: equivalence = "test 커밋이 그대로이고 base와 병합본 모두 통과(… Phase 3은 AST 해시 동일)" -- test 커밋 0은 '그대로'의 자명한 경우다.
* 838행(V2): "test 커밋 불변 + base·병합본 모두 PASS + 유형별 동등 증명(… Phase 3 AST 해시)".
  FU의 유형별 증명은 계약 1(모듈 `body` 전체가 `B[:1]+[I]+B[1:]` -- 모든 함수 AST가 같다는 뜻)과 계약 2(코드 객체)다. 계약 1은 838행 'Phase 3 AST 해시 동일'보다 강하다(m3 참고).
* design 05 §10-4(289행, gate `master`): "equivalence | 같음, 단 ①의 `Role: test`가 0개면 M^1 = `old`" -- test 커밋 0개를 **명문으로 허용**한다.

**게이트(gate `master` `tools/gates/merge_gate.py`) -- 받는다**
* 1137~1166행: `ev in ("red-green", "equivalence")`이면 `chain = _first_parent_chain(M1, old, …)`; M1 = old이면 `chain` = []이고(921~932행: `while x != stop`가 바로 끝남),
  test 커밋이 없을 때 거부하는 줄은 **`if ev == "red-green" and not chain`** 하나뿐이다. equivalence는 빈 사슬을 통과한다.
  `T = M1 = old`, 판정 기록 `test_commit` = T(1196행), `base_commit`은 old의 조상이면 된다(1202행).
* redteam 공격 **20(e)**(`tools/gates/redteam/attacks/20e-normal-equivalence/run.sh`): `flow-step start` → `code --equivalence` → `merge` → `audit --et equivalence` → EL4 -- **test 커밋 없이 가는 equivalence 정상 흐름을 '오거부 0' 대조로 이미 증명**한다(`lib/sb.py` `flow_start`는 test worktree·브랜치만 만들고 커밋하지 않는다).
* 실제 card 선례는 없다: gate `master`의 equivalence 판정 기록 5건(`ts1-legacy-move`·`d-delete-dead`·`d-delete-telescopic`·`probe-relocate`·`p9-kcl-edges`)은 모두 test 커밋이 있다(T ≠ B).
  FU가 첫 실제 사례다 -- 게이트 코드·redteam은 받지만, 실제 운영 절차(EL hook)에서는 S2의 조건이 붙는다.

**red-green과 비교 -- 초안 판단에 동의**
* 'future 줄이 있다' 단언은 base에서 AssertionError라 형식상 red가 되지만, 680·686·838행의 "동작을 바꾸는 변경 = red-green"과 맞지 않는다(운영 동작 불변 -- 계약 2·3 재측정).
  red-green으로 두면 '동작이 바뀌었다'고 기록하게 되고, 그 영구 test는 F2(DR shim 삭제)에서 지우거나 고쳐야 한다(V5 승인) -- 쓸데없는 결함.
* P9 인용은 정확하다(P9 spec '판정 유형 근거': "base에서 어긋나는 구조 판정은 auditor AST 측정으로 옮기고 영구 test는 base·병합본 모두 PASS하는 동작 계약만").
  다만 P9는 test 커밋이 **있는** equivalence였다 -- '구조 판정은 auditor 측정'의 선례이지 'test 커밋 0'의 선례는 아니다. 초안은 test 커밋 0의 근거를 05 §10-4 289행에서 따로 대므로 논리는 맞다(m4: 문장으로 구분해 두면 좋다).

---

## 3. 보호가 D0b `import_conflicts` 단언으로 실제로 생기는가 -- **생긴다(조건 셋)**

독립 근사 측정: D0a `plan` 시제품(`p3kit_d0a/move_plan_proto.py`)을 G1 시제품(`g1_kit/install_proto.py`)을 깐 `C:/g190/pp`에서 design §10 `MP_ARGS`로 base·head에 돌리고,
배정(`assignment`)의 MOD마다 원본 파일 `__future__` 기능 집합이 갈리는지를 내가 쓴 `fut.py`로 셌다(시제품에는 `import_conflicts`가 없어서 D0a 계약 2 (iv)를 손으로 계산했다).
* base(`dd60db6`, 문서 개정 미적용): 갈리는 MOD **3**(`topology_authoring` ← ACF ∅ / SR·SD annotations, `instance_report_builder` ← ACF·DR ∅ / SR·SD, `gmid_sizing_engine` ← DR ∅ / SR·TL). `_kv_table`은 아직 MOD4(A-4).
* head(FU): **0**.
* `plan` 출력 전체(`assignment`·`upward`·`cycles`·`unassigned`·`conflicts`·`reg_mismatch`·`import_time_high`·`order`·`reexports`)가 base = head -- DR·ACF 주석은 내장 타입뿐이라
  D0a 계약 2의 '`__future__`가 없으면 주석 이름도 참조' 규칙이 배정을 바꾸지 않는다(FU는 `__future__` 갈림 말고는 이관표에 영향 0 -- 초안에 없던 확인, m5).

조건: (1) 보호는 **D0b 병합부터**다(FU 병합~D0b 사이는 D0b 착수 0단계 `git grep` -- 사람 절차, 초안이 '잃는 것'으로 적음). (2) D0a가 계약 2 (iv)(`name` = `__future__`)를 실제로 구현해야 한다 --
D0a spec 108~109행에 있고 D0b redteam R-A5(FU 줄 삭제 → `import_conflicts` 비지 않음)가 그것을 판정한다. (3) 보호 범위는 DR·ACF 단위가 아직 원본에 있는 동안(M9까지)이다 -- 그 뒤에는 지킬 것이 없어 충분하다.

---

## 4. 발견

### B (차단) -- 없음

### S1. 사실 문장이 design v8.5와 어긋난다(MOD 셋 → 둘, v8.4 → v8.5)
* 초안 머리·의도 10행 "design `30-module-split`(초안 **v8.4**)", 14·17·25행 "MOD2·MOD4·MOD9 … 3건", 브리프 3행·S-1·S-4·§4 "v8.4".
* design **v8.5** §6.5(534행): "문서 개정 §9 (h)(N3.10 MOD9 `_kv_table` 토큰)로 `_kv_table`이 MOD9로 가서 **갈리는 MOD는 둘(MOD2 `_as_set` 1·MOD9 8단위)** -- FU 없이 `import_conflicts` `__future__` = MOD2·MOD9, FU 뒤 0(부록 A F5v85)".
  승인 질문 문안(`phase3_approval_question.md`)도 v8.5다. 근거로 쓴 'D0b spec 실측 3(3 / 0)'은 v8.5 이전 관찰이다(D0b spec 69·173·233행도 같은 묵은 값 -- D0b card 몫).
* 영향: 계약·판정은 그대로(갈림이 0이 아니라는 사실만 쓰인다). 그러나 '사실 문장은 쓰는 자리에서 재측정' 규칙과 승인 대상 판(v8.5)에 어긋난다.
* 고칠 것: 'design 30 v8.5', '(UD-0 문서 개정 적용 뒤) MOD2·MOD9 두 곳, 적용 전 판은 MOD2·MOD4·MOD9 셋 -- 부록 A F5v85', '9단위' 그대로. 브리프의 v8.4 표기도 같이.

### S2. test 브랜치 없이 가는 절차는 EL hook에 막힌다(브리프 §1·§2)
* 브리프 §1 "test worktree를 만들지 않는다(만들었다면 커밋 없이 지운다)", §2 "부모 = B".
* gate `master` `tools/gates/role_hooks.py` `_judge_worktree`(913행): `role/code/<id>`·`role/audit/<id>` worktree add는 base가 **문자열 `role/test/<id>`**일 때만 허용(`want_base`), 그 밖은 925행 `_deny`.
  `role_commit_gate.py` `_judge_merge`(98행): audit worktree 병합은 "HEAD가 `role/test/<id>` 끝"이어야 한다. `role_hooks.py` 1066행: code·audit 범위를 `refs/heads/role/test/<id>..HEAD`로 정하고 없으면 실패.
  계획 680행 순서 3도 audit worktree를 `role/test/<id>`에서 만든다.
* redteam 20(e)는 test worktree·브랜치를 gate/master에 **만들고 커밋만 하지 않는다**.
* 고칠 것: "test-author는 띄우지 않는다. 오케스트레이터는 `git worktree add <W>/<id>-test -b role/test/<id> gate/master`로 브랜치를 만들고(커밋 0 -- T = B), code·audit worktree는 `role/test/<id>`에서 만든다.
  브랜치는 병합·push 확인 뒤 정리 때까지 지우지 않는다." §2 `부모 = B`는 "`role/test/<id>`(= B)"로.

### minor
* **m1** 코드 객체 수 표기: design D-29·§6.5·승인 질문 119행은 "**17개**(DR 12·ACF 5)", 초안은 "**21**(DR 16, qualname 12)". 둘 다 맞는 측정(qualname 수 대 객체 수 -- `<genexpr>` 여럿)이지만
  auditor·사용자가 보는 수가 갈린다. 초안 계약 2 '기대 수'에 "design·승인 질문의 17 = qualname 기준(DR 12 + ACF 5)과 같은 측정"을 한 줄 더할 것.
* **m2** 승인 줄 id `20260930-30-module-split-design`: design §9.2 UD-0·승인 질문 19행·D0a·D0b·T0 초안·결정 패키지와 같다 -- **일치**. 날짜 접두가 기록일(≥10-02)과 달라도 된다
  (게이트 `rule6_dates_approvals`는 실제 날짜인지만 본다; 선례 `20260930-b26-before-phase3`는 10-01 커밋 `2d58fd8`에 기록). Phase 2 선례 `20260923-20-dead-code-dup-design`과 같은 모양.
  다만 승인 질문 ④ 본문(32행)은 '준비 card 하나'만 적고 card id를 쓰지 않는다 -- 양식 '작성 전 실측' 9와 착수 조건 S-1은 기록 범위 설명에 id(`p3-future-annotations`)를 요구하므로, 기록을 쓸 때 범위 설명에 id·D-29 원문을 넣는 것을 S-1에 '기록 작성 때'로 못 박을 것.
* **m3** 838행 'Phase 3 AST 해시 동일'을 이 card에서 무엇이 대신하는지 '판정 유형 근거'에 한 문장: 계약 1(모듈 `body` 전체 동일 + 머리 한 줄) ⇒ 모든 def의 `ast.dump` 같음. V2 basis가 그 문장을 그대로 쓸 수 있다.
* **m4** P9 인용은 '구조 판정은 auditor 측정'의 선례이고 'test 커밋 0'의 선례는 아니다(P9 T ≠ B). test 커밋 0의 근거는 05 §10-4 289행 + merge_gate 1137~1166 + redteam 20(e)라고 나눠 적으면 오해가 없다.
  실제 card로서는 첫 사례라는 사실도 적어 둘 것(gate `master` equivalence 기록 5건 모두 T ≠ B).
* **m5** 계약 5/6 보강 후보(선택): 'FU는 `plan` 배정에 영향 0'(위 §3 -- base·head `plan` 출력 같음)을 '작성 전 실측'에 한 줄. D0a 계약 2가 주석 이름을 future 유무로 다르게 세므로 리뷰어가 물을 자리다.
* V4 `--subject` 우회: 결과(`files` [])는 subject와 무관하다(test diff 0). 선례 ts7은 test-only라 test 파일이 있었다 -- 우회 자체는 맞고, basis에 "test diff 0이라 lint 대상 0 -- subject는 ERROR 회피용"을 적으면 된다(지적 아님).
* card id `20261002-…`: 실제 날짜, slug는 design §8 그대로, D0b 브리프 68행도 slug로 가리킨다 -- 문제 없음.

### 확인했고 문제 없는 것
양식 절 11개·머리 키(id·phase·evidence_type·gate_change·approval) 양식과 같음. 거부 입력 3종(docstring 앞 → docstring 소실, import 뒤 → SyntaxError, 기능 둘 → AST 불일치) 논리 맞음.
범위 계약(계약 1)은 'Change-Id 커밋들의 diff'로 한정(양식 10). 계약 3(c) 같은 경로 base → head 순서 명시. 오라클 출처(base 실행·PEP 236/563) 맞음. 시제품을 판정 도구로 쓰지 않는다는 분리 명시.

---

## 5. 측정 명령(요약, 스크래치 `C:/g190`)
* 복제·FU head: `git clone -q --no-local <repo> C:/g190/iso` → `checkout --detach dd60db6` → `mkfu.py`(ast docstring `end_lineno` 뒤 한 줄) → commit `351670bc`; `base`·`fu` 복제본.
* 계약 1: `ast1.py`(`ast.dump(include_attributes=False)` 비교). 계약 2: `co.py`(qualname#등장 순번, 필드 10개, `co_flags & ~annotations.compiler_flag`, `__annotate__` 따로) + 자기 점검 `co_self.py`.
* PT3: `PYTHONPATH=<cache> python -P -m pytest -c <cache>/pytest_gate.ini --rootdir <tree> --confcutdir <tree> <tree>/…/tests --gmid-phase=3 -q -p no:cacheprovider --junitxml …` 두 판, `jcmp.py`.
* E-LIB·E-INST: `el.sh`(같은 `iso` 경로, base → head, `checkout --detach` + `clean -qfdx`).
* 게이트: `gates.sh`(gate 판 `mutate_changed`·`source_lint`·`reachability`·`weakening_diff`·`test_lint` 두 형태). `reg_check.py` head.
* 배선 근사: `install_proto.py C:/g190/pp` + `move_plan_proto.py plan --rev <base|head>` + `fut.py`.

## 6. E-INST 재측정 결과
같은 경로 `C:/g190/iso`, base → head, `e_inst_p3.py` `7d26134a…`, 모두 exit 0:
* 파일럿 `current_reuse_telescopic_ota`: 출력 JSON 22키, base == head(다른 키 0), `raw_sha256` `2fc426d9ef3a9623…`, `without_topology_ref_sha256` `185b675e…`; stdout은 `elapsed=<n>s`를 가리면 같음. 263 s / 286 s.
* `folded_cascode`: 22키, base == head, `raw_sha256` `ef3cd9963d0a80ac…`, `without_topology_ref_sha256` `0ca6746f…`; 가린 stdout 같음. 37 s / 42 s.
→ 초안 '재현할 수치'와 같다. 그래서 §1 표의 계약 3(c) 행도 ○다.

정리: 스크래치 `C:/g190`만 지웠다. 실제 저장소 `status`(처음과 같은 `.bkit` 2파일 M)와 HEAD `dd60db6`은 그대로다.
