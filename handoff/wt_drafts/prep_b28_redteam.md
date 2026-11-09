# B28 redteam·게이트 변경 사전 실측 (읽기 전용 + C:/g16 스크래치)

R = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`(base 070cf69), RT = `R/tools/gates/redteam`. 저장소 파일은 하나도 바꾸지 않았다.
실험은 전부 `C:/g16` 아래에서 했다(scratch 복제본·합성 저장소·도구 시제품). 끝에 `C:/g16`는 지웠다.
부수 산출물: 스크래치 복제본 안에서 `run_all.py`를 돌려 `%TEMP%/gmid-redteam/20260930-19{1404,1541,1709,1743}-direct/` 4개가 남았다(하네스의 기존 동작, C:/g16 밖이라 지우지 않음).

---

## 1. `rt.py` 합성 저장소 구조와 V3 호출

**이력**: `build_vrepo`(RT/lib/rt.py 523-571)가 만드는 합성 저장소는 **실제 git 이력이 있다**.
- 523-527: `WORK/v/<step>`에 `sb.init_repo`(sb.py 183-198: `git init -b master` + user·`core.autocrlf=false`·`commit.gpgsign=false`·`core.hooksPath=<root>/.githooks`·`core.quotepath=false`).
- 530-539: `base` 파일 쓰고, `subjects`가 있으면 spec card(`docs/02-design/specs/<cid>.spec.md`, cid 기본 `20260921-rt-v`)와 `.gitkeep-rt`도 → `git add -A` → 커밋 "base"(Role: user) → `base = rev-parse HEAD`.
- 540-548: `subjects`가 있으면 `interface_card.py` 실행 → 커밋 "interface card"(Role: doc) → **`base`를 이 커밋으로 다시 잡는다**.
- 549-557: `head` 파일(값 `null`이면 `git rm`) → 커밋 "head"(Role: user, allow_empty) → `head = rev-parse HEAD`.
- 558-570: `approve_after_head`가 있으면 승인 기록 커밋을 더하고 `head`를 그 커밋으로 옮긴다(V5 대조군 전용).
- 따라서 **root의 HEAD = 도구에 넘기는 `--head`가 항상 성립**하고, `approve_after_head`가 없으면 **`HEAD~1` = 도구에 넘기는 `--base`**(subjects 있음: interface card 커밋, 없음: 첫 커밋). 두 경우 모두 `HEAD~1`에 base 파일(`rt_engine.py`)이 있다.

**base/head 전달**: `a_vcase`(574-600) → `iface.vtool_command(PY, gate_path("V3"), posix(root), base, head, card)`(iface.py 88-102) = `[PY, <시험 대상 저장소>/tools/gates/mutate_changed.py, --root <합성>, --base <sha>, --head <sha>, --pytest-ini <시험 대상 gates>/pytest_gate.ini]` + 단계의 `args`(subst_str 치환). 실행은 `sb.run_py`(sb.py 227-228, `clean_env`로 GIT_* 빈 값 제거, **timeout 600초**).
- `gate_path`는 `RT_REPO`(run_all이 `--repo` 또는 redteam이 든 저장소) 기준 -- base 판 T 복제본에서 돌리면 base 도구, 병합본에서 돌리면 새 도구가 불린다(red-green 구조 그대로 성립).

**v.json 형식**(선례 RT/attacks/28-v3-gmid-options/v.json, RT/v3_survivor/v.json): `{"cases":[{"step","tool":"V3","kind"(선택, 기본 attack),"subjects":[...],"base":{경로: {"text": ...}},"head":{...},"args":[...](선택),"expect":{"exit","layer","message_contains","basis",...}}]}`.
- 파일 명세(`_file_content` 491-509): 문자열(=subst_str 치환) / `{"git": "<rev>:<path>"}`(시험 대상 저장소 blob) / `{"section": ...}` / `{"text": ...}` + 선택 `replace`. **`text`는 치환하지 않는다**(문자열 형식만 `@{VAR}` 치환).
- 단계 기대는 각 `record`에 `expect`로 박히고 run_all이 `steps_from_records: true`로 레코드의 expect를 쓴다(run_all.py 157-166).
- `expect.json`(케이스 머리): `layer`, `exit`(참고값), `modes:["direct"]`, `phase:"0.5"`, `basis`, `title`, `steps_from_records: true`. run.sh는 `set -e; rt() { "$PY" -B "$RT" "$@"; }; rt vcase v.json` 세 줄(28과 동일).

**합성 test가 조상 blob을 읽을 수 있나 / rev 표현**:
- rt가 합성 저장소의 base/head sha를 치환 변수로 주지 않는다(`S.vars`에 없음, head 커밋 전에 파일을 써서 원리상 head sha도 못 넣는다). → **`HEAD~1` 사용이 유일하게 안정적**(위 구조로 base = HEAD~1 보장, approve_after_head 쓰지 말 것). `git rev-list --max-parents=0 HEAD`(루트 커밋)도 가능.
- 저장소 루트: test 파일이 `skills/analog-gmid-design/assets/tests/test_*.py`면 `Path(__file__).resolve().parents[4]`.
- base 도구에서의 거동: 사본 `%TEMP%/gmid-v3-*/copy`의 부모에 저장소가 없으므로(prep_b28 §2) `git -C <사본>`이 `not a git repository`로 실패 → 기준 실행 실패. oracle을 튼튼하게 하려면 returncode만이 아니라 **blob 내용**(`b"def rt_gain" in stdout`)도 단언할 것(부모 디렉터리에 우연히 저장소가 생겨도 red가 유지된다).
- 수집: `run_all.py` 51-55 `attacks/*`(expect.json 있는 것) + `v3_survivor`·`v7_unwired`; `--only`는 디렉터리 이름 부분 문자열(216-217). `--only v3` → `28-v3-gmid-options`, `v3_survivor`, 새 `31-v3-git-history` 셋.

**실측(C:/g16, 합성 저장소 두 개를 rt 형태 그대로 -- base 커밋 `rt_gain`, head 커밋 `rt_scale`=3x + test)**:

| 단계 | head test | base 도구(070cf69) | 시제품(clone + ERROR) |
|---|---|---|---|
| git-history-kill | `git -C parents[4] show HEAD~1:skills/analog-gmid-design/assets/rt_engine.py` returncode 0 + `b"def rt_gain"` + `rt_scale(2.0)==6.0` | **exit 1** FAIL, mutants 5·killed 0, `--out` reason 전부 "변이 없는 기준 실행에서 인벤토리 test가 통과하지 않음" | **exit 0** PASS, mutants 5·killed 5 (12.3초) |
| baseline-fail-error | `rt_scale(2.0)==7.0` | **exit 1** FAIL, killed 0 | **exit 2** `"verdict": "ERROR"` |

→ card 계약 5 (a)(b)의 red·green이 실제로 갈린다. 인벤토리가 비지 않음(시제품에서 5개 죽음)도 확인 -- `subprocess.run`의 `run` 이름 해석(prep_b28 §2)은 합성 저장소에 `def run`이 없어 무해.
- 계약 2(root 불변): 시제품 실행 전후 합성 root의 `for-each-ref`·`status --porcelain`·`worktree list` 동일.

**계약 1의 "--head 체크아웃" 관찰 한계**: `build_vrepo`에서는 root HEAD = `--head`이고 root 작업 트리 = head 트리라, 옛 도구(작업 트리 복사)와 "`--head` 체크아웃"을 redteam이 구별할 수 없다. 구별하려면 (i) head test가 `git log -1 --format=%s` == `"head"`(build_vrepo의 head 커밋 메시지)와 `git remote` 출력 빈 것(origin 제거)을 단언 -- origin 제거는 이것으로 관찰됨, head 체크아웃은 여전히 구별 안 됨 -- 또는 (ii) rt.py에 "빌드 뒤 root를 base로 checkout" 같은 단계 옵션을 test-author가 추가(`tools/gates/redteam/**`는 test-author 경로)해야 한다. 추가하지 않으면 계약 1의 체크아웃 부분은 auditor의 코드 확인으로만 판정된다 -- card에 어느 쪽인지 적을 것.

## 2. exit 2 / ERROR 기대 표기

- run_all `eval_step`(run_all.py 71-102): `exit`은 정수·리스트·`"nonzero"`·`"any"`; `message_contains`는 stdout+stderr 부분 문자열; 기본 `message_not_contains = ["Traceback (most recent call last)"]`.
- 표기: `"expect": {"exit": 2, "layer": "V3", "message_contains": ["\"verdict\": \"ERROR\""], "basis": ...}`. 도구가 `json.dumps(..., ensure_ascii=False)` 기본 구분자라 출력에 `"verdict": "ERROR"`가 그대로 나온다(시제품 출력 확인). 28의 PASS 단계가 같은 방식(`"\"verdict\": \"PASS\""`).
- **vcase(V 도구) 단계에서 exit 2를 기대하는 선례는 없다**: `rt vcase`를 쓰는 attacks 06·07·08·09·17·28·29, cases 5개, v3_survivor·v7_unwired의 모든 단계 기대가 0 또는 1(전수 스크립트로 확인). exit 2 기대 선례는 hook 공격(01·02·04·10 등)과 **공격 26 `v3-bad-revisions-{cp949,unset}`**(ENC 층, mutate_changed를 잘못된 rev로 불러 exit 2 + UTF-8 JSON 한 줄 -- RT/attacks/26-gate-output-utf8/expect.json 718·737행 부근, run.sh 48-49). 형식은 28 단계에 `exit: 2`만 바꿔 쓰면 된다.
- 새 ERROR 출력은 공격 26의 계약(stdout 한 줄 JSON, UTF-8, 한글 보존 -- spec card 20260921-gate-output-utf8)을 따라야 한다. 공격 26은 git diff 단계(clone 전)에서 끝나므로 이번 변경의 영향을 받지 않는다(시제품으로 재생 PASS 42/42).

## 3. mutate_changed.py 호출처와 "작업 트리 사본" 의존

**호출처**:
- 코드: `tools/gates/redteam/lib/iface.py:22,98`(V3 명령), `attacks/26-gate-output-utf8/run.sh:48-49`(잘못된 rev, clone 전 종료), `attacks/27f-v6-reconfigure-except/run.sh:22`(AST로 reconfigure 주변 광범위 except 0 확인 -- 새 코드도 광범위 except 금지). `merge_gate.py`·gate/*·githooks/*·hooks/*는 **mutate_changed를 부르지 않는다**(grep 0).
- auditor: `.ai/verification/*/scripts/tools_m*.sh` 등(dup-w-calc·df35·restore-plan·registry-grade-fix·d-move-tests) -- 모두 `$PY <캐시>/mutate_changed.py --root $R --base $B --head $M ...`, `$R` = §12-7 격리 복제본(= M 체크아웃). 즉 지금까지의 실사용은 root 작업 트리 = `--head` 트리였다.

**작업 트리(미커밋·무시 파일) 의존 여부**:
- 설계상 V3는 격리 복제본(git clone, 추적 파일만)에서 돈다(05 §10 머리 "모두 격리 복제본(§12-7)에서 돈다") → 미커밋 파일을 기대하는 경로 없음.
- 추적 안 되는 파일을 test가 읽는 곳: prep_b28 §2의 git 조회 외에, .gitignore 대상 `tests/*.result.txt`·`*.sizing_cache.json`·`*.theta_star.json`·`*.unwired_theta.json`·`*.window_dump.txt`는 probe 산출물(`probes/`는 수집 안 됨)이고 auditor V1도 추적 파일만 있는 복제본에서 통과하므로 의존 없음. 가정이 깨지면 새 도구에서는 기준 실행 실패 → ERROR로 드러난다(조용한 생존 아님).
- 실측: 메인 작업 트리를 copytree하면 **231MB·8.9초**(무시·미추적 파일 포함), `--no-hardlinks --no-local` clone은 **6.5~6.7초 + checkout 1.0~1.7초, 54MB**(.git 34MB). 사본이 더 작고 빠르다.
- 실측: 실제 저장소에서 `contracts/test_ts6_probe_relocate.py::test_base_blob_reader_reads_the_base_tree`·`::test_moved_tool_matches_base_except_path_lines`를 `-c pytest_gate.ini --gmid-phase=2 --gmid-strict=`로 -- **clone 사본(070cf69)에서 2 passed, copytree 사본에서 2 failed**("base 939f926의 …를 읽지 못했다"). `939f926`은 HEAD의 조상(`merge-base --is-ancestor` 확인). B28 원인과 해결이 실제 저장소에서 재현된다.

**문서 문장(갱신 후보)**:
| 위치 | 현재 문장 | 필요 |
|---|---|---|
| 05 design 317행 §10 V3 행 ④ | "변이마다 임시 복사본에서 그 test만" | "임시 복사본 = `--root`의 격리 복제본(`clone --no-hardlinks --no-local`, origin 제거, `--head` 체크아웃)" + "변이 전 기준 실행 실패 인벤토리가 있으면 exit 2(판정 불가)" 추가 |
| 05 design 313·550행(§10 머리, §17) | "exit … 2 실행 오류(auditor는 FAIL로 적는다)" | 변경 불필요. **draft 의도 2항 "exit 2, §17 입력 오류"는 틀림** -- §17에서 V3~V7의 2는 "실행 오류"("입력 오류"는 merge_gate·integrity 행) |
| 계획 839행 N4.2 V3 | "변이는 worktree 밖 임시 복사본에서 수행하고 worktree는 바꾸지 않는다" | 충돌 없음(clone도 임시 복사본). 기준 실행 실패 = 판정 불가를 넣을지 선택 |
| `mutate_changed.py` 3·10·13행 docstring | "④ 변이마다 worktree 밖 임시 복사본" | code-author가 함께 갱신 |
| 00-common design | V3·mutate·복사본 언급 0건 | 없음 |
| 10-test-separation 66·117·427·428·432·493·515 | C11 이력 | 손대지 않음 |
| auditor agent md 41행 | 도구 이름만 | 없음 |

## 4. 설치 사본 / 재설치

- §13.4(05 design 464-466) 설치 사본 = gate `hooks/pre-receive`·`gate-runner.py`, `.claude/hooks/role_*`(+ `.githooks`). `integrity.py` 32-33 `GATE_FILES`도 pre-receive·gate-runner.py 둘뿐. `tools/gates/gate/`에는 `gate-runner.py`·`pre-receive`만 있고 mutate 참조 0.
- `mutate_changed.py`는 §4.4 캐시(`role_paths.ensure_cache` 631-662: gate master 트리의 게이트 코드 blob을 `<git-common-dir>/gmid-gate-cache/<커밋>/`에 풀고 blob 대조, 다르면 재추출)에서 실행 → **재설치 불필요**. 반영 뒤 base 캐시부터 새 도구(이 변경 자신의 V3는 base 판 도구, targets 0).

## 5. 스크래치 실험 결과 요약과 구현 주의점

- clone 비용(3회): 6.45 / 6.61 / 6.69초(+ checkout 1.0~1.7초). 현 copytree(8.9초)보다 빠르다. V3 1회당 1번.
- **Windows 정리 결함 확정**: clone 사본을 `shutil.rmtree(ignore_errors=True)`(현 364행)로 지우면 `.git/objects/pack/pack-*.{idx,pack,rev}` 읽기 전용 3개가 **조용히 남는다**(약 33MB/회, %TEMP%에 누적). 느슨한 객체도 읽기 전용이다(합성 저장소 rmtree에서 PermissionError 재현). `shutil.rmtree(tmp, onexc=<chmod S_IWRITE 후 재시도>)`로 완전 삭제 확인 -- card 계약에 "임시 복제본이 남지 않는다" 또는 정리 실패를 드러내는 문장을 넣을 것(prep_b28 §7 선택 5를 필수로 승격 권장).
- **예외 튜플**: clone·checkout 실패를 `subprocess.run(check=True)`로 처리하면 `CalledProcessError`가 359행 튜플(OSError·RuntimeError·SyntaxError·ValueError·UnicodeDecodeError) 밖이라 traceback + exit 1(FAIL과 같은 코드)이 된다. 시제품처럼 returncode 검사 후 `RuntimeError`(또는 `rch._git` 재사용 -- reachability.py 24-28이 RuntimeError를 던진다)로 올려야 exit 2 ERROR.
- 시제품(스크래치, 저장소 아님): clone `--no-checkout` → `config core.longpaths true` → `remote remove origin` → `checkout -q --detach <head>`, 기준 실패 변이는 `result: "baseline_failed"`로 따로 모아 `survived`에 넣지 않고 최종 `verdict: ERROR`/exit 2, rmtree onexc. 이 시제품을 스크래치 clone의 `tools/gates/`에 넣고 redteam 재생: `--only v3` → `28-v3-gmid-options` PASS·`v3_survivor` PASS(6단계 PASS, base 도구와 같음), `--only 26-gate-output-utf8` PASS(42단계), `--only 27f` PASS(16단계). → 계약 4 무동작이 시제품 수준에서 성립.
- 참고(범위 판단용): 도구의 test 실행 env는 `os.environ` 그대로라 호출자가 `GIT_DIR`·`GIT_WORK_TREE`를 설정한 상태면 test의 `git -C`가 엉뚱한 저장소를 읽을 수 있다. redteam은 `clean_env`, auditor는 bash에서 직접 실행이라 현재 사용에선 무관 -- 넣을지 여부만 결정.
- 실제 저장소 base/head 쌍에 현 도구 전체 실행은 **생략**(P8 dup-w-calc는 변이 2060개, 5분 초과 예상). 대신 원인 test 두 개를 clone/copytree 사본에서 직접 돌려 재현(§3).

## card 초안(draft_b28.spec.md)에 반영할 것

1. 의도 2항: "exit 2, §17 입력 오류" → "§17 실행 오류".
2. 계약 5 (a)의 rev 표현은 `HEAD~1`(rt가 base sha 치환을 주지 않음, build_vrepo 구조상 HEAD~1 = `--base`) + blob 내용 단언. `approve_after_head` 사용 금지.
3. 계약 1 "`--head` 체크아웃"은 현 rt로 redteam 관찰 불가 -- rt.py 단계 옵션 추가(test-author) 또는 auditor 코드 확인으로 판정한다고 명시. origin 제거는 head test의 `git remote` 빈 출력으로 관찰 가능.
4. 정리 계약 추가: 임시 복제본이 %TEMP%에 남지 않는다(읽기 전용 pack -- 실측).
5. 구현 제약 한 줄: git 실패는 RuntimeError로 올려 exit 2(튜플 밖 예외 금지), 광범위 except 금지(공격 27f).
6. '작성 전 실측' 1: 줄 번호 285·312·331·339·340-342·359·364 모두 base 070cf69에서 일치 확인(328-331 중 캐시 줄은 331).
