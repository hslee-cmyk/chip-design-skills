# Phase 2 DoD 브리핑 드라이런 (공식 판정 아님)

대상 브리핑: `_drafts/phase2_dod_brief.md`(v2). 실행 판: gate `master` = `0f237862c007f6a53122f2bdfb3c87e6366ec133`(= 로컬 master, P10b 미병합). 실행일 2026-10-01.
환경: 임시 경로 `C:/g112`(브리핑의 `C:/g90` 대신 -- 드라이런 전용), 격리 복제본 `C:/g112/iso`(`--no-hardlinks --no-local`, origin 제거, longpaths), 게이트 캐시 = `git archive <rev> tools/gates`, Python 3.14.2, `APPDATA`·`HOME` export. 스크립트: `_drafts/p2dod_dryrun/`(e3_check.py, n63_check.py, e4a.sh, e4cd.sh). 원출력은 `C:/g112/out`에 있었고 끝에 C:/g112째로 지웠다(수치는 아래 표에 옮겨 둠).
**동시 부하 주의**: 실행하는 동안 다른 agent 4~5개(b33_kit redteam, g88 pytest, g113 E-INST, g114)가 함께 돌았다. 소요 시간은 부하가 걸린 상태에서 잰 값이다.

## 1. 항목별 결과

| 항목 | 실행한 명령(요지) | 결과 | 소요 | 문제 | 브리핑 수정 제안 |
|---|---|---|---|---|---|
| §2 H 산출 | `H=$(git -C $R log -1 --format=%H master -- .ai/verification/20260930-df23-registry-record.json)` | **H = 빈 문자열**(P10b 대기) | <1 s | **[높음] 조용히 진행됨**: `set -u`는 빈 값을 잡지 못한다. `git log --oneline $H..master` → `..master`(출력 0, 성공), `git checkout -q --detach $H` → 인자가 없어져 `checkout --detach` = **현재 HEAD(master)에 detach하고 성공한다**. P10b 기록 없이 돌리면 오류 없이 master를 'P10b 판'으로 재게 된다 | `test -n "$H" && git -C $R cat-file -e "$H:.ai/verification/20260930-df23-registry-record.json" \|\| { echo "H 없음"; exit 1; }`를 넣고, 변수는 전부 따옴표로 감싼다(`"$H"`). `master` 대신 `gate/master`를 쓰거나 `git -C $R rev-parse master gate/master`가 같은지 적게 한다 |
| §2 복제 | `git clone -q --no-hardlinks --no-local -c core.longpaths=true` + `remote remove origin` | OK, status 0줄 | 28 s | -- | -- |
| §2/§3 `REV` | `mkdir -p $G/cache_$REV && git archive $REV …` | OK(`REV=$H`를 직접 정해서) | 2 s | `REV`·`CACHE`를 정하는 줄이 없다(§4는 `CACHE=$G/cache_$H/...`만 씀). 7535799 판은 짧은 해시라 캐시 디렉터리 이름이 다르다(동작에는 문제 없음) | §3에 `REV=$H; CACHE=$G/cache_$REV/tools/gates`를 명시하고, §5 각 판마다 `REV=` 줄을 둔다 |
| §2 cwd | `cd` 금지 → cwd = 메인 저장소 | 이번 실행에서 측정 도구가 cwd에 쓴 것은 없음 | -- | **[중간]** cwd가 메인 저장소로 남아 cwd에 쓰는 도구는 모두 메인에 쓴다. 아래 '메인 쓰기 감시'와 함께 보면 오탐을 만든다 | 측정 명령을 `(cd $G && …)` 서브셸로 돌리는 것만 예외로 허용하거나, 처음에 `cd $G`를 한 번 하라고 적는다 |
| §2 메인 쓰기 감시 | `git -C $R status --porcelain --ignored`를 `main_before.txt`와 비교, `find … -newer stamp` | **status 달라짐**: 메인 루트에 `?? cfg_<hash>.json` 15개(18:07~18:3x). `find`(workspaces/skills/tools/.ai/verification)는 0개 | -- | **[높음] 다른 agent가 쓴 것이다**: 내용은 게이트 설정(`gate_path`·`reachability_roots`·`baseline_commit`), 첫 파일 18:07:51은 `_drafts/b33_kit/m4_records.py`(pid 3161, 18:07:26 시작) 직후이고, 이름 중 `cfg_2a2a7a0456`·`cfg_d473f65a94`는 P5·P5b 병합 커밋 해시다(b33 redteam 변형 실행으로 추정). 내 측정 시각과 겹치지 않는 파일도 있다. 이대로 두면 auditor는 (1) 브리핑대로 '같아야 함' FAIL을 내거나 (2) 출처를 증명하지 못한다. 그리고 `find` 범위가 저장소 루트를 덮지 않아 루트에 쓰는 것을 놓친다 | (a) 착수 조건 §0에 "메인 저장소를 cwd로 쓰는 다른 agent 없음"을 넣는다(b33_kit cfg 누출은 따로 백로그 처리 -- 아래 범위 밖 메모). (b) 불일치가 나올 때의 처리를 적는다: 늘어난 경로·mtime·내용을 결과에 적고, 측정 프로세스 시각과 비교해 출처를 판정한다. (c) `find $R -maxdepth 1 -newer stamp -type f`도 더한다 |
| E0 | `$PY -B …/reg_check.py --registry … --root $ISO` | exit 0, `reg_check: 발견 0` | 1.9 s | 결과에 적으라는 '§7 행 수·§1 D 값·처리 열 형식'을 재는 명령이 없다(도구는 '발견 0'만 출력). 직접 세어 보니 §7 표 행 25(sizing_recipe 9 + stick_diagram 15 + 기타 1) = §1 D 합 9+15+1 | 세는 명령을 지정한다(예: `awk` 또는 auditor 스크립트로 §7 `\| \`` 행 수, §1 D 열 합, `처리` 열 값 집합). 판별력(선택): H의 reg_check에 da03c0e 레지스트리를 주면 exit 1, 발견 22줄(`disposition` 1, `stale` …) -- 도구가 실제로 거부함을 보이는 한 줄을 넣을 만하다 |
| E0 옆 DF-23 | 같은 명령 + `--df23-inventory …/df23_inventory.json` | **exit 2** `unrecognized arguments` | <1 s | **P10b 대기**(옵션은 P10b code가 넣는다) | -- (P10b 병합 뒤 그대로 동작해야 함) |
| E1 수집 | `PT -k "dup_w_calc or dup_kcl_edges" --collect-only -q` | 130/886 수집, w_calc 106, kcl_edges 24, 두 모듈 밖 0 | 38 s | `--color=no`가 없어 요약 줄에 ANSI 코드가 들어간다(grep `^skills/…` 셈은 영향 없음) | E1·E5 명령에도 `--color=no`를 붙인다 |
| E1 실행 | `PT $ISO/…/contracts -k … -rA` | 130 passed, 756 deselected, 실패 0 | 43 s | `-rA` 노드 id가 cwd 기준 상대(`..\..\..\g112\iso\…`)로 찍힌다 -- 읽기 불편할 뿐 | -- |
| E1 V2 | 두 기록 `checks.V2.verdict` | dup-w-calc PASS(red-green), p9-kcl-edges PASS(equivalence) | <1 s | 브리핑 §6-5와 design §8은 P8을 red-green/equivalence로 다르게 부른다(design 표 P8 'equivalence', 판정 기록·브리핑 'red-green'). 판정에는 영향 없음 | 결과에 기록의 `evidence_type`을 그대로 적게 한다 |
| E2 | `$PY -B …/engine_dup_scan.py --root $ISO` | exit 0, 출력 1줄: `probe_mirror_gain_ranking.py:183 lut-private "exempt": true`(승인 `20260929-p4-scan-exempt`, `target_kind: decision`, target 일치 -- decision 기록 14개 중 이 target을 가진 것 1개) | 0.8 s | **[중간] 기준 문서와 브리핑이 다르다**: design 20 §10 E2 통과 기준 원문은 "exit 0, **발견 0**"이고 면제를 말하지 않는다(design 20에서 '면제'는 §5 V4 면제 문맥뿐). 브리핑은 '면제 아닌 발견 0'으로 읽는다. 브리핑 §1 규칙("기준을 해석으로 바꾸지 않는다")대로라면 auditor는 멈추거나 FAIL을 내야 한다 | 브리핑에 근거를 박아 둔다: 스캐너 계약(도구 docstring 8·18행 "면제되지 않은 발견 0 → exit 0", P4 spec card)과 승인 `20260929-p4-scan-exempt`. 또는 design E2 문구를 '면제되지 않은 발견 0(exit 0)'으로 맞추는 명확화 커밋을 DoD 전에 한다(기준 약화가 아니라 P4 때 승인된 면제를 반영하는 것인지 오케스트레이터가 판단) |
| E3 (H) | `e3_check.py $ISO $H out $H` (auditor 스크립트 역할을 내가 작성) | PASS: 1 cat-file 0 / 2 n_items 515 = totals, by_phase·by_role 일치 / 3 515/515 phase, 닫힌 집합 = N6.1에서 만든 {3,4,5,6a,6b,6c,7a,7b,7c,해당 없음} = `phase_source.closed_set` / 4 빈 function 0 / 5 '동작을 정함' DF-29 0, DF-30 27, DF-31 16, DF-32 1, DF-33 12, DF-34 18 / 6 `measured_at` 766b5c2 ↔ H `diff --quiet` exit 0, scope_files 8 = 기대 집합 | 1.8 s | (a) 5번 'DF 번호' 필드가 지정돼 있지 않다 -- 실제 필드는 `plan_mapping`이고 값이 `DF-31(회로별 보상 함수)`·`DF-30(신규 위치)`처럼 꼬리가 붙는다. 앞 일치(`^DF-(\d+)`)로 셌다. 정확 일치로 세면 DF-30 4·DF-31 6으로 달라진다. (b) `DF-29(신규 위치)` 항목 2개가 있으나 role '메시지뿐'이라 0에 들지 않는다. (c) 'DF-29 위치 def 0개'를 재는 명령이 없다 -- 계획 N5.2 DF-29 행의 다섯 이름(`_load_telescopic_topology_cached`·`_telescopic_class_ab_open_loop_response`·`_cmrr_telescopic_class_ab_cmfb`·`_psrr_telescopic_class_ab`·`_psrr_telescopic_class_ab_cmfb`)으로 `git grep -E 'def (…)\b'` 하니 H 0, 766b5c2 0, da03c0e 5 | 5번에 "필드 `plan_mapping`, 정규식 `^DF-(\d+)`(꼬리 포함), `role == '동작을 정함'`"을 명시하고, DF-29 def 검사 명령(위 다섯 이름, 범위 = scope_files)을 적는다 |
| E3 판별력 (766b5c2) | 같은 스크립트, rev 766b5c2, 6번 N/A | FAIL(기대대로): 1 성립, 3 phase 0/590, `measured_at` 없음. 덤으로 2(by_phase 없음)·4(빈 function 414) 실패, 5번 DF-29 42 | 1 s | -- | 기대 문장에 '2·4번도 실패'를 더해도 된다(필수 아님) |
| E5 | `PT $ISO/…/tests/unit -k new_topology -rA --color=no` | 9 passed, 877 deselected, **9건 전부 `tests/contracts/`**(test_d_delete_dead 1, test_d_delete_telescopic 8) -- 사전 점검 9건과 같다 | 44 s | **[낮음, 약화 가능성]** design E5 통과 기준의 "로드·파이프라인 동일"을 덮는 노드가 없다: 9건은 `ValueError` 거부 7 + 일반 경로 값 산출 2다. 수집 '1개 이상'만 보면 이 부분은 검사 없이 통과한다 | 결과에 9노드를 기준 문구 세 부분(로드·파이프라인 동일 / 삭제 키 ValueError / 일반 경로 값)에 나눠 매핑하게 하고, 비는 부분은 E4 E-LIB(라이브러리 회로에서 로드·파이프라인 동일)로 갈음한다고 근거를 적게 한다(합성 topology는 아님 -- 남으면 절차 메모) |
| E4(a) PT2 | `PT2 -q --color=no` (앞에 checkout -- workspaces; clean -fdxq) | exit 0, **871 passed, 15 xfailed**, XPASS 0 | **409 s**(pytest 389 s) | 브리핑 예상 '약 5분'보다 길다(동시 부하) | '약 7~11분'으로 고친다 |
| E4(a) PT2 dod | `PT2 --gmid-dod -q --color=no` | exit 0, **871 passed, 15 xfailed** | **696 s**(pytest 650 s) | 위와 같음. 각 실행 뒤 복제본에 `.pytest_cache/`가 생긴다(clean으로 지워짐) | 같음 |
| E4(b) 사본 | `cp` 3개 + `sha256sum` + `rev-parse $H:<path>` | 사본 sha256 e_lib `045f65c8…`, df35 `575fcb32…`, df36 `aa76989e…`; blob id `00fbb20f…`, `67df1684…`, `ef43c49f…`; 사본은 CRLF(autocrlf=true)라 blob 내용 sha256(`41b72d7d…`, `36d66763…`, `6cc48495…`)과 다르다 -- 브리핑이 예고한 대로 | <1 s | -- | -- |
| E1 판별력 (7535799) | 판 전환 → 캐시 7535799 → 같은 `--collect-only -q` | w_calc 106, **kcl_edges 0** -- 기대대로 | 69 s | -- | -- |
| E4(c) da03c0e | e_lib / e_inst_df35 base ×2 | E-LIB 9/9, ok 전부 true, exc 없음, hash `1d2e3bf6…7a8f`. E-INST 두 회로 `literal_counts_before` [2,1], `topology_ref_is_join_of_ASSETS_DIR` true, `fail_in_stdout` false, `engine_origin`·`sys_path_added`·`instance_path` 전부 `C:\g112\iso` 아래 | e_lib 8 s, crt **748 s**, fc 86 s | crt 하네스가 브리핑 예상(7~8분)보다 김(부하). 이 단계 직후 메인 status 비교에서 cfg 파일이 늘었으나 위 '메인 쓰기 감시' 행처럼 다른 agent 산출 | 시간 예상 수정, 메인 status 처리 규칙(위) |
| E4(d) H | e_lib / e_inst_df36 ×2 | E-LIB hash 같음(`1d2e3bf6…`), 9/9. crt `without_topology_ref_sha256` `185b675e…` = da03c0e, fc `0ca6746f…` = da03c0e. H `topology_ref_equals_expected_contract1` true, `path_string_hits` [], `topology_ref` = `skills/analog-gmid-design/assets/library/<회로>.topology.json` | e_lib 6 s, crt 456 s, fc 59 s | E-INST 뒤 복제본에 추적 파일 instance.json 2개 수정 + report.html 1개 생김 -- 다음 판 전환의 checkout/clean으로 정리됨(브리핑 절차대로면 문제 없음) | -- |
| §6-1 기록 전수 | n63_check.py(아래 전부 한 스크립트, git show/log만) | 32건(`_schema.json` 제외), V1~V10 전부 PASS/N/A | 59 s(스크립트 전체) | 브리핑 예상 33건 = 32 + P10b. **P10b 대기** | -- |
| §6-2 Phase 2 기록 | `git grep -l -E '^phase: 2$' $H -- docs/02-design/specs` | card 17장. 기록 있는 것 15, 없는 것 2: P3(c) `probe-promote-consistency`(정상) + **P10b `df23-registry-record`(P10b 대기)**. 기대 목록 밖 card 0 | (위에 포함) | 브리핑이 card 경로(`docs/02-design/specs`)를 적지 않았다 | grep 명령을 적는다 |
| §6-3 merge gate 형식 | 판정 기록 마지막 커밋의 trailer, `merge <id>` 병합 커밋, base/test/code 조상 여부 | 15건 전부 성립. test-only 4건(P1·P3a·P3b·P10) 병합 0·`code_commit` null, 나머지 11건 병합 커밋 1개씩 H의 조상. P10b 행 **P10b 대기** | -- | -- | -- |
| §6-4 카드 밖 엔진 변경 | `git log --no-merges da03c0e..$H -- 'skills/analog-gmid-design/assets/*.py' workspaces/run_harness.py '…/library/*.json'` | 28커밋, 전부 Role code/test + 16건 안의 Change-Id. card별: P2 4, P1·P3a·P3b·P10 1, 나머지 2 | -- | 브리핑 '2d58fd8 기준 27 + P10 test + P10b code·test' → 지금 28, P10b 뒤 30 예상 | 기대값을 '30(P10b code·test가 둘 다 assets 아래 .py를 바꿀 때)'으로 적는다 |
| §6-5 거부 입력 test | 기록의 `red`·`equivalence` | red-green 7건(P10b 대기 1) 모두 `red.test_ids`·`failure_hashes` 있음. equivalence 4건(P2·P5·P5b·P9) `equivalence.outputs_hash` 있음 | -- | **[중간, 확인 없이 통과]** 기록의 `equivalence`는 `{commands, outputs_hash}` **해시 하나뿐**이라 "outputs_hash와 base 쪽 같음"을 기록만으로는 잴 수 없다. 이대로면 '키가 있다'만 보고 통과한다 | 확인 근거를 바꾼다: 각 기록 `checks.V2.verdict` PASS와 `basis`의 base=병합본 문장(또는 `reproduced_numbers`)을 인용하게 하거나, 문구를 "outputs_hash 존재 + V2 PASS"로 낮추고 그렇다고 적는다 |
| §6 0.5 card | 같은 스크립트 | v3-history-clone, rejudge-cache 둘 다 V1·V10 PASS, 나머지 N/A | -- | -- | -- |
| §7-1 결정 D2 | 파일만 `$G/d2/…/tests/probes/`에 복사, H 판 `engine_dup_scan.py --root $G/d2` | 발견 1 `rail-set` 40행, exit 1. 메인 절대 경로 리터럴 33행 `ASSETS`, 38행 `INST` -- 브리핑 기대와 같음 | <1 s | -- | -- |
| §7-3 `phase="2"` 근거 | `git -C $ISO grep -n 'phase="2"' -- …/tests` | **1건 나온다**: `contracts/test_df23_inventory.py:354 _p10_item(phase="2")`(P10 test 픽스처, IC 표식 아님). gmid_ic 표식으로 좁히면 0 | <1 s | **[낮음]** 브리핑 명령 그대로면 '0이어야 할' 근거가 1건으로 나와 문장과 어긋난다 | 패턴을 `gmid_ic\([^)]*phase="2"`로 바꾼다. E4(a) 두 실행 xfailed 15 = 15라 관찰 문장 자체는 성립 |
| §7-4 추적 instance.json | `git show $H:<경로>`의 `topology_ref` | 두 회로 모두 메인 절대 경로(`C:\Users\HSLEE\…\library\<회로>.topology.json`) -- DF-36 이전 형식 | <1 s | -- | -- |
| 끝 | 복제본 reflog/status, 메인 HEAD | reflog: clone → H → 7535799 → da03c0e → H. 끝 status: instance.json 2 수정 + report.html 1(마지막 E-INST 산출, 판 전환이 없어 남음). 메인 HEAD 0f23786 불변, `find`(지정 경로) 0개, status 차이는 cfg_*.json 15개(다른 agent) | -- | 브리핑 §2는 '끝 status'를 적으라고만 하고 0줄을 요구하지 않는다 -- 마지막 E-INST 산출이 남는 것이 정상임을 적어 두면 혼동이 없다 | "끝 status는 E4(d) 산출 3줄이 정상"을 적는다 |

## 2. 기준 문서·승인 대조

- design 20 §10 머리 문장과 E4 행(gate 최신 커밋 fe638ab)이 브리핑 §1·§3·§4 E4(a)(b)·§5 E4(c)(d)와 맞는다: PT2 = `--gmid-phase=1`만 `=2`, `PT2` 전체 + `PT2 --gmid-dod` 전체, 사본 3개를 두 판에 같이 쓰고, `<out>`은 `<iso>` 밖, `-B -P`, da03c0e는 df35 base 모드, H는 df36, (a)(b)(c) 기준. design 10 §10 525행 `PT` 정의가 브리핑 `PT`와 같다.
- 승인 `20260930-phase2-e4-baseline`: `diff_base` 8790b24 = 2140da8^, `diff_head` 2140da8, `merge_gate.py diff-hash`(H 캐시)로 다시 계산 → `0d8ae146…8904` = `target`. 2140da8은 design과 `.ai/context.md`를 바꿨고 해시 범위는 design 한 파일.
- 승인 `20260930-phase2-e4-phase`(gate 판): `diff_base` b8d4c4d = fe638ab^, `diff_head` fe638ab, 다시 계산 → `611dbc39…d484` = `target`. 범위 설명(E4만 PT2, E0~E3·E5는 PT)이 브리핑 §1과 같다. 주의: `_drafts/approval_20260930-phase2-e4-phase.md`는 아직 `target: <… 정정 커밋 뒤 계산>` 자리표시가 남은 초안이다 -- gate 판은 채워져 있으니 auditor에게는 gate 판만 가리키면 된다.
- 어긋남: E2 '발견 0'과 '면제 아닌 발견 0'(위 표, 기준 문서 우선 규칙과 충돌). E3·E1에서 브리핑이 더하는 검사(모듈별 수집, 1~6번)는 design 문구보다 강한 쪽이라 문제 없음.

## 3. 브리핑 고칠 것 (중요도 순)

1. **[높음]** §2 H 빈 값 가드(`test -n "$H"` + cat-file), 변수 따옴표, `master`↔`gate/master` 확인. 지금 그대로면 P10b 없이 master를 조용히 잰다.
2. **[높음]** 메인 쓰기 감시 오탐: 다른 agent(b33_kit 계열로 추정)가 메인 저장소 루트에 `cfg_<hash>.json`을 계속 쓴다. 착수 조건에 '메인을 cwd로 쓰는 agent 없음'을 넣고, 불일치가 나올 때 출처를 판정하는 규칙과 루트(`-maxdepth 1`) `find`를 더한다.
3. **[중간]** E2 기준 문구 충돌: design '발견 0' 대 면제 1건. 근거(스캐너 계약 + `20260929-p4-scan-exempt`)를 브리핑에 박거나 design을 명확화한다.
4. **[중간]** §6-5 equivalence 'base 쪽 같음'은 기록 구조로는 잴 수 없다 -- V2 basis 인용으로 바꾼다.
5. **[중간]** E3 5번 필드·매칭 규칙(`plan_mapping`, `^DF-(\d+)`, role)과 DF-29 def 검사 명령을 명시한다.
6. **[낮음]** E0 집계 명령, E5 기준 세 부분 매핑, §7-3 grep 패턴(`gmid_ic(...phase="2")`), §6-2 card 경로, §6-4 기대 30, `REV`/`CACHE` 정의, `--color=no`, 끝 status 3줄이 정상이라는 문장.
7. **[낮음]** 시간 예산: PT2 7분 / PT2 dod 11.6분 / E-INST crt 판당 7.6~12.5분(부하). 전체 벽시계 약 55분(직렬, 부하 있음). 판을 바꾸지 않는 읽기 전용 항목(E2·E3·§6·§7)은 PT2 실행 중에 돌려도 된다(이번에 그렇게 했고 복제본 status에 영향 없음).

## 4. P10b 대기 항목 (P10b 병합 뒤 다시 볼 것)

- §2 `H` 산출(지금 빈 값), E0 옆 `--df23-inventory`(지금 exit 2), §6-1 33건, §6-2 P10b 행(지금 기록 없음), §6-3 P10b merge·trailer, §6-4 커밋 30개, §6-5 P10b `red`.
- 드라이런 결과 P10b와 무관한 측정(E0·E1·E2·E3·E4·E5, 판별력 두 건)은 지금 판에서 전부 브리핑 기대대로 성립했다(PASS 성격) -- P10b가 엔진·test를 바꾸므로 공식 판정에서는 H 판에서 다시 잰다.

## 5. 범위 밖 메모

- 메인 저장소 루트에 `cfg_*.json` 15개(18:07~18:3x, 게이트 설정 내용)가 생겼다. 내 측정 프로세스 산출이 아니다(첫 파일이 측정 시작 전이고, 이름이 P5·P5b 병합 해시). `_drafts/b33_kit`(m4_records.py / run_redteam_variants.py, cwd = 메인) 쪽 누출로 보인다 -- 해당 agent 확인과 정리가 필요하다(나는 지우지 않았다).
- design 20 §8은 P6를 equivalence로, P8을 equivalence로 적지만 판정 기록은 둘 다 red-green이다(§8 아래 문단이 P7·P8을 red-green으로 정정했으나 표 P8 칸과 P6은 그대로) -- 문서 정합 백로그 후보.
