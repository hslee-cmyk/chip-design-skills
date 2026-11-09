# B28 사전 조사 -- V3 `mutate_changed.py`의 `.git` 없는 사본 결함 (정적 조사, 읽기 전용)

R = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, A = `R/skills/analog-gmid-design/assets`. 도구·test는 실행하지 않았다.
실행한 것은 Read/Grep, `git ls-files -s`, `git count-objects -vH`, `ls -d`(부모 `.git` 유무)뿐이다. **[추정]**이라고 적은 곳은 코드를 읽고 추론한 것이고 실행해 확인하지 않았다.

---

## 1. `mutate_changed.py` 흐름 (Read `R/tools/gates/mutate_changed.py`, 376줄)

| 줄 | 내용 |
|---|---|
| 276-277 | `git diff --name-only --no-renames --diff-filter=AM base head` → `rch._is_source(p)`인 `.py`만 targets(= `A/` 바로 아래 `.py`와 `workspaces/run_harness.py`. `tools/gates/**`는 대상이 아니다) |
| 278-281 | 호출 그래프는 **git의 `--head` 트리**(`rch.read_tree(root, ns.head, …)`)에서 만든다. test 노드 = `A/tests/`에서 `A/tests/tools/`를 뺀 곳의 `test*` 함수 |
| 282 | 승인된 변이 id(`rch._approved_ids(root, head)`) |
| **283-285** | `tmp = tempfile.mkdtemp(prefix="gmid-v3-")`; `work = tmp/copy`; **`shutil.copytree(root, work, ignore=shutil.ignore_patterns(".git"))`** -- root의 **작업 트리**를 복사(추적 안 되는 파일 포함, `.git` 제외) |
| 286-287 | `PYTHONPYCACHEPREFIX`용 빈 디렉터리 |
| 293-299 | 사본의 `A/tests/conftest.py`로 `--gmid-phase` 지원 여부 판정(`except OSError` → None) |
| 309-318 | `run_tests(inv)`: `$PY -P -m pytest -c <ini> --rootdir=work --confcutdir=work -x -q -p no:cacheprovider [--gmid-*] <인벤토리 test들>`, cwd=work. `TimeoutExpired` → 문자열 `"timeout"` |
| 321-323 | base에 그 파일이 있으면(`git cat-file -e`) `git show base:path`, 없으면 `base_src=None`(전부 새 def) |
| 326-327 | 바뀐 def마다 인벤토리 = 그래프에서 그 def에 도달하는 test |
| **328-331** | **기준 실행**: 인벤토리 튜플마다 한 번 `run_tests(inv) == 0`을 `baseline_ok`에 캐시. 주석: "기준에서 이미 실패하면 모든 변이가 죽은 것으로 보여 거짓 PASS가 된다 -- WP-02" |
| 332-336 | 승인된 변이 id → `exempt` |
| 337-339 | 인벤토리 없음 → `survived`, reason "인벤토리 없음(도달하는 test 없음)" |
| **340-342** | **B28 경로**: `not baseline_ok[inv]` → `survivors.append(mid)`, `{"result": "survived", "reason": "변이 없는 기준 실행에서 인벤토리 test가 통과하지 않음"}` -- 변이를 실행하지 않고 '생존'으로 센다 |
| 343-354 | 변이 실행: 사본의 대상 파일을 변이본으로 덮어쓰고 `run_tests(inv)` 뒤 head 원문으로 복원. exit 0 → survived, 그 밖(`"timeout"` 포함) → killed |
| 356-358 | `--out`에 변이마다 append |
| 359-361 | `except (OSError, RuntimeError, SyntaxError, ValueError, UnicodeDecodeError)` → `verdict: ERROR`, exit 2 |
| 362-364 | `finally: shutil.rmtree(tmp, ignore_errors=True)` |
| 365-367 | survivors 있으면 `FAIL` exit 1, 없으면 `PASS` exit 0 |

**성격**: 기준 실행 실패는 거짓 PASS가 아니라 **거짓 FAIL**(원인이 test 강도가 아니라 환경인데 '생존'으로 기록)이다. auditor가 매번 수동 스크립트로 대신 확인해야 한다(P8 dup-w-calc 실례, 아래 4).

**조용히 넘기는 곳·광범위 except 점검**
- 광범위 `except Exception`은 없다. 359행은 좁은 튜플이다.
- 대신 **튜플 밖 예외**(KeyError·AttributeError·IndexError 등)는 잡히지 않아 traceback으로 끝나고 파이썬 기본 exit 1 -- **FAIL(exit 1)과 같은 코드이고 JSON 줄이 없다** [추정: 파이썬 기본 동작, 실행 확인 안 함].
- 340-342: 기준 실행 실패 → 원인(실패 test id·출력)을 버리고 '생존'. `run_tests`가 `capture_output=True`로 출력을 받지만 반환값은 returncode뿐이다.
- 317-318: 기준 실행이 시간 초과면 `"timeout" == 0` 거짓 → 역시 '생존'.
- 241-242 `inventory_gmid_keys`: 읽기 실패 test 파일을 `continue`(엄격 키가 줄어든다).
- 53-57: base 소스 SyntaxError → 전부 바뀐 def로 본다(보수 쪽).
- 321-323: `cat-file -e`가 git 이상으로 실패해도 '새 파일'로 본다(보수 쪽, 조용함).
- 364: `rmtree(ignore_errors=True)`. `.git`을 사본에 넣는 수정이면 Windows에서 읽기 전용 pack 파일 때문에 삭제가 실패해 `%TEMP%`에 조용히 남을 수 있다 [추정].
- 암묵 전제: 그래프·targets는 git `--head` 트리에서, test 실행은 root **작업 트리 복사본**에서 -- root 체크아웃이 head와 다르면 어긋난다(auditor 사용 방식에서는 root = head 병합본이라 지금은 일치).
- `-x`: 인벤토리 test 하나만 실패해도 인벤토리 전체의 기준 실행이 실패한다.

---

## 2. `.git` 없는 사본에서 실패하는 test 전수

명령: `Grep "subprocess|\"git\"|'git'|git show|rev-parse|cat-file|ls-tree|_git\(" A/tests --glob *.py`, `Grep "\bgit\b|\.git\b" A --glob *.py`, `Grep "gmid-gate-cache|git-common-dir|GIT_DIR|\.git[\"'/\\]" A`

| 파일 | git 호출 | 읽는 것 | pytest 수집 | V3 영향 |
|---|---|---|---|---|
| `A/tests/contracts/test_ts6_probe_relocate.py` 237-245 `base_blob_text()` | `subprocess.run(["git","-C",_REPO_ROOT,"show",f"{_BASE_COMMIT}:{rel}"])`, `_BASE_COMMIT = 939f926fe97b…`(96행), `_REPO_ROOT = __file__.parents[1].parent.parents[2]` | base 커밋 939f926의 옛 probe 32개 blob과 `A/tests/derive_achievable_bounds.py` blob | 예 | **실패하는 test 둘**: `test_base_blob_reader_reads_the_base_tree`(652-656), `test_moved_tool_matches_base_except_path_lines`(668-673). 사본에서 `fatal: not a git repository`(P8 auditor 재현) |
| `A/tests/probes/probe_b22_headroom_attribution.py` 79-87 | `git -C <A>/../../.. show HEAD:<library>/current_reuse_telescopic_ota.topology.json` | HEAD의 topology blob | **아니오**(`probes/`, 이름 `probe_*`) | 없음 |
| `A/tests/tooling/test_extract_selftest.py` | `subprocess.run([sys.executable, …extract_selftest.py])`만. `git` 글자는 주석(blob id 독립 계산 62·204행) | -- | 예 | git 불필요(`tools/migrate/`에도 subprocess·git 없음 -- Grep 0건) |
| `A/tests/contracts/test_restore_plan_functions.py` | 없음(4-5행 docstring: "이 test는 git 이력을 읽지 않고") | -- | 예 | 없음 |

`.git`·`gmid-gate-cache`를 직접 읽는 test는 0건(bkit `worktree-warning.flag` 두 개만 걸림 -- 데이터 파일).

**왜 sizing_recipe def의 인벤토리에 ts6 test가 드는가** [정적 추론, 실행 안 함]: `reachability._refs`는 `subprocess.run`을 `("modattr", ("subprocess","run"))`로 읽고, `resolve`는 `by_mod.get(("subprocess","run"))`가 비면 `by_name.get("run")`으로 넘어간다(`R/tools/gates/reachability.py` 144-145행). `workspaces/run_harness.py:421`에 `def run(circuit_key)`가 있으므로 `base_blob_text` → `run_harness.py::run` → 엔진 대부분으로 간선이 생긴다. 그래서 `run_harness::run`이 닿는 sizing_recipe def(dup-w-calc의 `_build_theta_evaluator._evaluate` 등)의 인벤토리에 ts6 test가 끼고, `-x`로 기준 실행 전체가 실패한다. restore-plan-functions(V3 PASS, 32/32 killed)는 대상 def(`lut_conditions_from_npz`, `derived_spec`)의 인벤토리에 ts6 test가 없었던 것으로 보인다 [추정]. 이 과대 근사는 설계가 의도한 것(reachability docstring "과대 근사 -- 도달 판정이 거짓 FAIL을 내지 않는 쪽")이라 B28 범위 밖이다 -- 다만 git을 읽는 test가 하나만 있어도 대상 def 다수의 인벤토리에 번지는 이유다.

**잠복 위험**: `%TEMP%`의 부모에 저장소가 생기면 `git -C <사본>`이 **다른 저장소**를 읽는다. 지금은 없다: `ls -d /c/Users/HSLEE/.git /c/Users/HSLEE/Documents/.git /c/Users/HSLEE/AppData/.git /c/Users/HSLEE/AppData/Local/.git` → 넷 다 없음(`TEMP=C:\Users\HSLEE\AppData\Local\Temp`). bkit flag 파일 `A/library/.bkit/runtime/worktree-warning.flag`에 `"gitCommonDir": "C:\\Users\\HSLEE\\.git"`가 적혀 있지만 현재는 없는 경로다(오래된 기록).

---

## 3. 고칠 방향 비교

설계 문장(Read `R/docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md`):
- §3.2: "**gate는 push된 코드를 실행하지 않는다**(N3.12.0). 풀어 쓰는 것은 `old` 판 게이트 코드뿐이고, push된 트리는 데이터로만 읽는다" -- **gate(EL4 pre-receive)** 에 대한 규칙이다. §9.2-6 "gate는 증거를 다시 실행하지 않는다(§3.2)". V3는 gate가 아니라 auditor가 격리 복제본에서 돌리는 도구이고 head test 실행이 본래 역할이다(§10 머리: "모두 **격리 복제본**(§12-7)에서 돈다").
- §10 V3 행 ④: "변이마다 임시 복사본에서 그 test만". 계획 N4.2 V3(plan 839행): "변이는 worktree 밖 임시 복사본에서 수행하고 worktree는 바꾸지 않는다".
- §10 머리·§17: "exit 0 PASS / 1 FAIL / 2 실행 오류(auditor는 FAIL로 적는다)".
- §12-7: "`git clone --no-hardlinks --no-local <audit worktree 경로> <TEMP>/<id>-iso` → `git -C <TEMP>/<id>-iso remote remove origin`(복제본의 `origin`이 작업 저장소를 가리킨다 -- review30 R-09 실측)". auditor 실제 명령은 `git -c core.longpaths=true clone -q --no-hardlinks --no-local …` + `config core.longpaths true`(`.ai/verification/20260922-v3-gmid-options.json` auditor_run.commands).

| 후보 | 내용 | 설계 충돌 | 장점 | 단점·주의 |
|---|---|---|---|---|
| (a) `git clone` | 사본을 `git -c core.longpaths=true clone -q --no-hardlinks --no-local <root> <tmp>/copy` → `checkout -q --detach <head>` → `remote remove origin` | 없음. §12-7 격리 복제본과 같은 명령 형태이고, "임시 복사본"(N4.2)이며 root를 바꾸지 않는다. §3.2는 gate 규칙이라 해당 없음 | 원인 제거: ts6 test가 `git show 939f926:…`를 읽을 수 있다(939f926은 head의 조상이라 clone에 있다). 실행 트리 = `--head` 트리가 되어 그래프(git head 트리)와 일치(현재 암묵 전제 제거). 부모 디렉터리 저장소 오인 위험도 사라진다 | clone 비용: `git count-objects -vH` → size 15.28 MiB + size-pack 33.03 MiB(약 48 MiB), 도구 실행당 1회. 어느 ref에서도 닿지 않는 커밋을 읽는 test는 여전히 실패. Windows에서 `.git` 읽기 전용 pack 때문에 `rmtree(ignore_errors=True)`가 조용히 남길 수 있다 [추정] -- 정리 실패 처리 필요 |
| (a') `git worktree add` | root 저장소에 linked worktree | **충돌 소지**: root의 `.git/worktrees/`에 기록이 생긴다(N4.2 "worktree는 바꾸지 않는다"의 취지, §12-7 격리). worktree의 `.git` 파일이 root gitdir를 가리켜 head test가 root 저장소에 git 쓰기를 할 수 있다 | -- | 채택 비권장 |
| (a'') `.git`까지 copytree | ignore 제거 | root가 linked worktree면 `.git`은 파일이고 원 gitdir를 공유 -- 위와 같은 격리 문제. root의 remote 설정도 따라온다 | 간단 | 비권장 |
| (b) ERROR 명시 | `.git` 제외는 두고, 기준 실행 실패 인벤토리가 있으면 `verdict: ERROR`, exit 2 + 실패 test id·출력 끝을 JSON에 | 없음. §10·§17 exit 2 = 실행 오류, auditor는 FAIL로 적는다 -- 통과가 되지 않으므로 기준 약화 아님. 329-331행 주석(WP-02)의 목적(기준 실패를 '죽음'으로 세지 않음) 유지 | '생존'과 '판정 불가'를 구분. 원인이 기록에 남는다 | **B28 원인을 고치지 않는다**: dup-w-calc 같은 경우 여전히 변이 0개 실행 → auditor 수동 대체가 계속 필요. 판정 결과(auditor 기록 FAIL)는 실질적으로 같다 |
| (c) 둘 다 | (a) + (b) | 없음 | 원인 제거 + 남는 환경 차이(ref에 없는 커밋, 순서 의존, 시간 초과)도 '판정 불가'로 드러난다 | 계약·redteam 단계가 늘어난다 |

**추천: (c)**. (a)만 하면 다른 환경 차이로 기준 실행이 실패할 때 여전히 조용한 '생존'이 되고, (b)만 하면 B28 실례(P8)가 그대로 재현된다. 둘 다 V3 판정식(연산자·인벤토리·생존=FAIL)은 바꾸지 않는다. "막는 규칙을 넓히지 않는다"(선례 card 의도 문장)와 맞는다.
(b)의 세부 결정 기본안(원칙에서): 기준 실패 인벤토리가 하나라도 있으면 전체 verdict = ERROR(판정 불가가 섞인 판정을 PASS/FAIL로 요약하지 않는다), 다른 인벤토리의 실제 생존 변이도 JSON에 그대로 싣는다. 기준 실패 인벤토리의 변이는 `survived`가 아닌 별도 result(가칭 `baseline_failed`)로 `--out`에 기록.

범위 밖(별도 백로그 후보, 이번 card에 넣지 않음): 359행 튜플 밖 예외의 exit 1 충돌, `reachability`의 `subprocess.run` → `run_harness.run` 과대 근사, 인벤토리 과대에 따른 V3 실행 비용.

---

## 4. 기존 test·공격 재생·판정 기록에서의 V3

명령: `ls R/tools/gates/redteam/{attacks,cases}`, `Grep "mutate|V3|v3"` redteam, Read 해당 파일.

- `redteam/v3_survivor/`(expect exit 1, modes direct, phase 0.5): `v.json` 두 단계 -- `attack`(0 입력만 보는 test → 변이 생존, exit 1), `control`(`rt_scale(2.0)==6.0` → 전부 죽음, exit 0). §10 "거부 증명: V3 → `redteam/v3_survivor`".
- `redteam/attacks/28-v3-gmid-options/`(선례 C11): 네 단계 `opts-kill`·`pre-c6-no-opts`·`pre-c6-with-opts`·`strict-outside-inventory`, 전부 expect exit 0 + `message_contains ["\"verdict\": \"PASS\""]`, 단계별 `args`로 `--gmid-*` 전달.
- 실행 기구: `lib/rt.py` `a_vcase`(574-600)가 `build_vrepo`(523-571)로 `$WORK/v/<step>`에 합성 저장소(base 커밋 → interface card 커밋 → head 커밋, 전부 `git add -A` 커밋)를 만들고 `iface.vtool_command`(`lib/iface.py` 88-102: V3는 `--pytest-ini <gates>/pytest_gate.ini` 자동 추가)로 **시험 대상 저장소의** `tools/gates/mutate_changed.py`를 부른다. `run_all.py` 55-56행: `attacks/*/expect.json` + `v3_survivor`·`v7_unwired` 자동 수집, `--only`는 디렉터리 이름 부분 문자열.
- 판정 기록의 V3 사용:
  - `20260922-v3-gmid-options.json`(게이트 변경 선례): V1 = redteam 전체 재생(`run_all.py --phase 0.5 --mode direct`, 병합본 PASS 49·SKIPPED 7 / base 판 T는 공격 28의 red 3단계 FAIL), V2 red = redteam 단계 3개(`tools/gates/redteam/attacks/28-v3-gmid-options::<step>`)의 failure_hashes, **V3 = PASS "변이 대상 0개(도구 규칙)"** -- 게이트 도구는 `_is_source` 밖이라 targets 빈 목록.
  - `20260930-dup-w-calc.json` V3(P8): 도구 출력 FAIL, mutants 2060, killed 0, 전부 reason '변이 없는 기준 실행에서…'. 원인 재현 스크립트 `.ai/verification/20260930-dup-w-calc/scripts/v3_baseline_probe.py`, 대체 확인 `scripts/mut_sites.py`(git 있는 격리 복제본에서 변이마다 V1 명령 + `-x`). 기록 verdict는 PASS(대체 확인 근거), handoff "V3 도구의 .git 없는 사본 결함".
  - `20260930-restore-plan-functions.json` V3 PASS(32/32 killed), `20260930-d-move-tests.json`·`20260930-registry-grade-fix.json` V3 PASS(mutants 0, 대상 def가 `A/tests/tools/`) -- 이 셋은 B28에 걸리지 않았다.
  - auditor 실행 형태: `bash C:/g1x/scripts/tools_m*.sh v3` → `$PY <캐시 gmid-gate-cache/<base>>/mutate_changed.py --root <격리 복제본> --base <B> --head <M> --pytest-ini <캐시>/pytest_gate.ini --gmid-phase=2 --gmid-strict= --out …`(base 판 캐시에서 실행).

---

## 5. 게이트 변경 절차 요구사항

- **승인 기록이 base에 먼저**: `R/tools/gates/merge_gate.py` 720-740 `gate_change_ok(base_view, change_id)` -- base 트리의 spec card가 `gate_change: yes`이고 `approval:`의 모든 id가 `.ai/approvals/<id>.md`로 base에 있고 `parse_approval_header`로 파싱돼야 참. `role_paths.py` 395-398: 조건 `게이트 변경` 행(`tools/gates/*.py` code-author, `tools/gates/redteam/**` test-author -- plan 605·619행)이 이 값으로 허용된다. 따라서 §12-0에서 spec card + 승인 기록을 gate master에 올린 **뒤** worktree를 만든다.
- 선례 승인 기록 `R/.ai/approvals/20260922-v3-gmid-options.md`: `target_kind: diff`, `target` = spec card diff 해시, `diff_base`/`diff_head`, `diff_path: docs/02-design/specs/<id>.spec.md`, scope, "## 사용자 원문 > 승인", 범위 설명(덮는 것: `mutate_changed.py` 수정 + `redteam/**` 케이스, 덮지 않는 것).
- 선례 spec card `R/docs/02-design/specs/20260922-v3-gmid-options.spec.md`: 머리 `phase: 1`, `evidence_type: red-green`, `gate_change: yes`, `approval: <id>`. 판정 유형 근거 = base 도구로 redteam 합성 저장소 FAIL, 병합본 PASS. oracle (a) 합성 저장소(conftest 같은 판정 환경 이름은 커밋하지 않고 `rt.py`가 실행 중 생성). 신규 시그니처 표 비움.
- **재설치 불필요**: §13.4 설치 사본 목록은 gate `hooks/pre-receive`·`gate-runner.py`, `.claude/hooks/role_*`(+`.githooks`)뿐이다. `mutate_changed.py`는 §4.4 캐시(`<git-common-dir>/gmid-gate-cache/<gate master id>/`, blob 대조 후 자동 재추출)에서 실행된다. 선례 card 의도 문장: "`mutate_changed.py`는 설치 사본이 없어(gate `pre-receive`·`.claude/hooks`·`.githooks` 어느 것도 아님) 반영 뒤 §13.4 재설치는 필요 없다". 10-test-separation design 432행도 같은 내용.
- 효과 시점: 새 도구는 **이 변경이 gate master에 반영된 뒤의 base 캐시**부터 쓰인다. 이 변경 자신의 V3는 base 판 도구로 돌고 targets 0(게이트 도구)이라 무관.
- 템플릿 `_TEMPLATE.spec.md` 35-45행 '작성 전 실측' 7항목을 채워야 한다(아래 6 참조).
- 문서 동반(오케스트레이터 `Role: doc`): 05 design §10 V3 행 ④("임시 복사본")와 §17에 기준 실행 실패 = exit 2를 반영할지, 계획 N4.2 V3 행(839행) 문구 -- (a)는 "임시 복사본"의 한 형태라 문구와 충돌은 없다. 10-test-separation 66·117·493·515행은 C11 이력이라 손대지 않는다.

---

## 6. 새 test·redteam 케이스 이름 후보와 glob 충돌

명령: `Grep "glob\(|iterdir\(|rglob\(" {A/tests/**/*.py, tools/gates/**/*.py}`, `ls attacks`.

- 이번 변경은 `A/tests/`에 파일을 더하지 않는다(게이트 변경 test = redteam). `A/tests` 안 glob(`test_d_delete_dead`·`test_d_move_tests`·`test_ts3_no_print_verdicts`의 `_TESTS_DIR.rglob("*.py")`, `_ASSETS_DIR.glob("*.py")` 등)은 `tools/gates/**`를 보지 않는다 → 충돌 없음. `A/tests`에서 `tools/gates`를 참조하는 곳은 `conftest.py`(merge_gate import, sys.path 끝)와 `test_ic_markers_match_plan.py`(`_GATES_DIR`)뿐이고 `mutate_changed`는 참조하지 않는다.
- redteam 수집: `run_all.py` 55행 `attacks/*`(expect.json 있는 것), 58행 `cases/*`, `lib/rt.py` 364행 `Path(ns.cases).glob("*.json")`(공격 15 전용).
- 기존 번호: 01~30(마지막 `30-rejudge-cache`). 번호는 유일 키가 아니다(`17-*` 6개, `20e-*` 3개).
- **후보: `attacks/31-v3-git-history/`**(`run.sh`·`expect.json`·`v.json`, 선례 28과 같은 3파일). `--only 31` → 이 케이스만(다른 이름에 "31" 없음). `--only v3` → `28-v3-gmid-options`·`v3_survivor`·새 케이스(의도대로 V3 묶음). `--only git` → 새 케이스만. 대안 이름 `31-v3-baseline-error`도 충돌 없음.
- 단계 이름 후보(v.json `step`, `WORK/v/<step>` 디렉터리가 되므로 기존 단계 이름과 겹치면 안 됨 -- 기존: `attack`, `control`, `opts-kill`, `pre-c6-no-opts`, `pre-c6-with-opts`, `strict-outside-inventory` 등): `git-history-kill`, `baseline-fail-error`, `git-history-control`.

---

## 7. spec card 계약 초안 (결정 전 제안)

머리: `phase: <현 Phase>`, `evidence_type: red-green`, `gate_change: yes`, `approval: <id>`.

1. **이력 있는 시험 사본**: V3 도구가 기준 실행·변이 실행에 쓰는 사본은 `--root`에서 `git clone --no-hardlinks --no-local`로 만든 독립 복제본이고, `--head` 커밋이 체크아웃되어 있으며 `origin` 원격이 없다(§12-7과 같은 형태). 사본 안에서 `git -C <사본 루트>`로 head의 조상 커밋 blob을 읽을 수 있다.
2. **root 불변**: 도구 실행 전후 `--root`의 refs·작업 트리 상태·`git worktree list`가 같다(N4.2 "worktree는 바꾸지 않는다").
3. **기준 실행 실패 = 판정 불가**: 변이 전 기준 실행이 통과하지 않은 인벤토리가 하나라도 있으면 판정 JSON은 `"verdict": "ERROR"`, exit 2이고, 그 인벤토리의 대상 def와 실패를 식별할 정보(실패 test id 또는 pytest 출력 끝)를 담는다. 그 인벤토리의 변이는 '생존'으로 세지 않는다(--out에 별도 result).
4. **무동작(오거부 0)**: 기준 실행이 통과하는 저장소의 판정은 기존과 같다 -- `redteam/v3_survivor` attack exit 1·control exit 0, 공격 28 네 단계 PASS 불변. '인벤토리 없음' 변이는 기존대로 생존(FAIL).
5. (선택) **정리**: 임시 복제본 삭제 실패를 조용히 넘기지 않는다(읽기 전용 pack 처리 또는 실패 시 stderr/JSON에 경로 기록).

oracle (a) 구성 합성 저장소(redteam `31-v3-git-history`, `rt.py` `build_vrepo` 재사용):
- `git-history-kill`: head test가 `subprocess.run(["git","-C",<__file__.parents[4]>,"cat-file","-e","HEAD~1:skills/analog-gmid-design/assets/rt_engine.py"])` returncode 0을 단언하고 `rt_scale(2.0)==6.0` -- 기대 exit 0, `"verdict": "PASS"`. red: base 도구는 사본에 `.git`이 없어 기준 실패 → 전부 생존, exit 1.
- `baseline-fail-error`: head test가 구성상 항상 실패(`rt_scale(2.0)==7.0`) -- 기대 exit 2, `"verdict": "ERROR"`. red: base 도구는 exit 1(생존).
- 대조: 기존 `v3_survivor`·공격 28 재생 결과 불변(V1 = redteam 전체 재생, 선례와 같이).

재현할 수치: 없음(선택: 반영 뒤 dup-w-calc 병합본 `243e6ed`에 새 도구를 돌려 mutants 2060이 실제 실행되는지 -- 결정 필요 항목으로 둘지 사용자 판단 [추정: 실행 시간이 길 수 있다]).

## 8. 추천 방향 요약

- **(c) = (a) git clone 사본 + (b) 기준 실행 실패 ERROR**. 설계 충돌 없음: §3.2는 gate(EL4)가 push된 코드를 실행하지 않는다는 규칙이고 V3는 auditor 격리 복제본에서 head test를 실행하는 도구다(§10 머리). clone 명령은 §12-7 격리 복제본 선례(`--no-hardlinks --no-local` + `remote remove origin` + `core.longpaths`)를 그대로 따른다. `git worktree add`와 `.git` 포함 copytree는 root 저장소와 gitdir를 공유/변경하므로 비권장.
- 절차: spec card(`gate_change: yes`) + `target_kind: diff` 승인 기록을 먼저 gate master에 → test-author가 `redteam/attacks/31-v3-git-history/` → code-author가 `mutate_changed.py` → auditor V1 = redteam 전체 재생(red = base 판 T 복제본에서 새 두 단계 FAIL), V3 = targets 0. 재설치 불필요.
- 범위 밖으로 남길 것: 359행 튜플 밖 예외의 exit 1 충돌, `subprocess.run` → `run_harness.run` 그래프 과대 근사(인벤토리 비용).
