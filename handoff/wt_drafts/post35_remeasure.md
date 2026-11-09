# post-35 재측정 목록 -- card 35(`20260930-v3-changed-stmt-scope`) 병합 뒤 하류 키트 값 다시 재기

작성 2026-10-02(gate `master` `4a286f0` -- card 35는 문서·spec·승인 기록까지만 병합, 코드 전). 저장소·기존 `_drafts` 파일 쓰기 없음.
실행: `bash _drafts/post35_kit/remeasure.sh <병합된 gate rev>` (결과 `/c/g237/results/{results.jsonl,table.txt}`, 원자료 `/c/g237/out/`).

## 0. 왜 다시 재나

card 35가 병합되면 V3 도구(`tools/gates/mutate_changed.py`)가 해시가 바뀐 기존 def에서 **바뀐 문장과 그 주변만** 실행하고, 나머지는 `--out`에
`{"id","result":"not_targeted"}`로 적으며, 출력 JSON에 `not_targeted`(수)·`targets_by_def`가 붙는다(spec 계약 4·5).
하류 키트의 대상 수는 전부 **독립 프로토타입 `v3scope_kit/scope_proto.py`(N2w)**로 잰 값이고, 줄 번호·앵커는 35 전 도구(`36e170e`=`4a286f0` 판) 기준이다.
→ 병합된 **실제 도구**로 같은 head를 다시 돌려 값이 같은지 확인하고, 다르면 '적힌 곳'을 고친 뒤 그 card를 착수한다.

## 1. 측정 방법(remeasure.sh)

| 단계 | 내용 |
|---|---|
| 격리 | `--scratch`(기본 `/c/g237`, 없어야 함). 작업 트리 저장소를 `git -c core.autocrlf=false clone --no-hardlinks --no-local`, origin 제거, 빈 hooksPath, gate 원격 추적 참조는 저장소에서 fetch(읽기). TMP·TEMP·TMPDIR·pycache = scratch. `set -Eeuo pipefail`, 모든 git은 `git -C`. 끝에 실제 저장소 HEAD·status·reflog·refs 불변 단정(다르면 exit 1). |
| 도구 | `<rev>:tools/gates` archive(`tool_new`), 옛 값 기준 `--old-rev`(기본 `4a286f0`) archive(`tool_old`). `--sim35`(리허설 전용)이면 `tool_new`에 `p35_sim35.py`(scope_proto를 계약 4·5 자리에 얹은 모의)를 깐다. |
| V3 대상 수 | `p35_v3count.py`: 도구 `main`을 실제 경로로 돌리되 PYTHONPATH 앞에 가짜 `pytest`(exit 0) -- `v3scope_kit/probe_selection.py` 원리 재사용. 판정이 아니라 **선택 집합**만 본다(죽임 수는 안 잰다). 같은 변이 목록에 scope_proto N2w를 독립 적용해 대칭차도 낸다. |
| 모의 head | `p35_heads.py`: `b26_scripts/{sim_head,v3_scope_classify,v3_scope_widen,mk_b1,b26v4_head,b26v4_classify}.py`·`b26_reconcile/b26v4c.py`를 scratch로 복사(경로만 치환, setup_g109.py와 같은 방식)해 이전 측정과 같은 head를 만든다: B1(B34 코드), H4(B26-1 v4), C4B(backfill C4 base), HA(시나리오 A), H5(B26-1 v5 = C1·C2·C4), BF(backfill 후보 = REV에서 SR 11800·11879 삭제 -- backfill_launch.sh stage_v3count와 같은 식). |
| 정적 | `p35_static.py lines`(키트가 인용한 grep 식 그대로 줄 번호, V3 정상 출력 키 순서), `anchors`(install_proto.py의 `sub()` 앵커 수를 AST로), install_proto 실제 설치 시도(사본), 게이트 밖 `changed_defs`/`def_hash` 호출 `git grep`. 옛 값은 `--old-rev`에서 같은 식으로 다시 잰다. |
| 느린 것 | G1 redteam: 공격 32 base(`gen_attack32.py` + `run_all --only 32-moved-defs`), 시제품(`install_proto` + `--scope` + `G1_SCOPE=1`), 무동작 미리보기(기본 11 + `34-` + `35-`). g1_kit/run_*.sh는 결과를 `g1_kit/out`에 쓰므로 부르지 않고 같은 명령을 scratch 출력으로 낸다. `--skip-slow`로 건너뜀. |
| 기록 | 항목마다 `results/results.jsonl`에 한 줄 append(`status` = same·changed·needs35·deferred·error·skipped), 끝에 `table.txt`(옛 → 새). |

## 2. 항목(옛 값 · 옛 값을 낸 명령 · 적힌 곳 · 기대 방향)

기호: 대상/not_targeted. '기대'는 35가 계약대로 병합됐을 때. 결과 표의 status `same` = 새 값이 기대(옛 값, G1-KEYS는 옛 키 + 두 키)와 같음, `changed` = 다름(→ '적힌 곳'을 고치거나 원인 확인),
`needs35` = 도구에 `targets_by_def`가 없어(35 전) V3 실행을 건너뜀 -- 35 전 도구는 대상 밖 없이 변이 수천 개를 다 돌려 잴 값이 없다.

| id | 옛 값 | 옛 값을 낸 명령 | 적힌 곳(파일 + 앵커) | 기대 방향 |
|---|---|---|---|---|
| TOOL35-marker | 0 | `git show gate/master:tools/gates/mutate_changed.py \| grep -c targets_by_def` | `b34_launch.sh:209`, `b26pre_launch.sh:244`, `backfill_launch.sh:255`(착수 조건 '35 병합'), `b34_commit_plan.md:74` | 0 → **1 이상**(0이면 세 launch가 멈춤 -- 정상) |
| V3-P9 (대조) | 12/16(전체 28) | `v3scope_kit/measure_b26.py` p9_real `6bf510b..93b18db`, scope_proto N2w | 35 spec '작성 전 실측' 1 표 P9 행, `v3_scope_briefs.md` §0.2 표 | **같음**(실제 커밋 쌍 -- 다르면 도구가 계약 1과 다르게 구현됐다는 신호, auditor에게) |
| V3-BF | 4/93(전체 97) | `backfill_launch.sh stage_v3count`(병합 도구·실제 pytest로 `targets_by_def[...run_matching_safety_with_finger_growth].targeted`) -- 옛 값은 시제품 N2w(`b26_backfill_briefs.md` §0.3) | `backfill_launch.sh:81` `V3_WANT=4`, `draft_b26_backfill_audit.spec.md:180` '대상 4·not_targeted 93', `b26_backfill_briefs.md:71·136` | 같음(4가 아니면 backfill launch가 멈춘다 -- card 'V3'·briefs 0.3 표를 고친다) |
| V3-B34 | 10/45(전체 55) | `b34_kit/measure_b34.py`(REV..B34 모의, scope_proto N2w), 현행 규칙 55는 `probe_selection.py` | `b34_briefs.md:14·250` '대상 10(not_targeted 45)', `draft_b34.final.spec.md` 'V3 계획' 표·318~320행, `b34_commit_plan.md` | 같음 |
| V3-B34-ids | 10/10 | `measure_b34.py` spec10 목록 | `draft_b34.final.spec.md` 'V3 계획' 표 10 id | 도구 대상 = 그 10 id |
| V3-B26v4 | 301/2,141(전체 2,442) | `v3scope_kit/measure_b26.py` b26_v4(B1..H4) | `draft_b26_1.spec.md` 'V3 계획' 1, `v3_scope_briefs.md` §0.2, 35 spec '작성 전 실측' 1 | 같음 |
| V3-B26A | 299/2,141(전체 2,440) | `b26_reconcile` 시나리오 A(C4 base에 v4 head) | `draft_b26_1.spec.md:362·386`, `b26_reconcile/out/plan_summary.txt` | 같음 |
| V3-B26v5 | 299/2,136(전체 2,435) | `36e170e` 재측정(C:/g210 measure_b26 사본 + v5 head) | `draft_b26_1.spec.md` 'V3 계획' 1('착수 base 대상 299'), `v3_scope_briefs.md` §0.2 끝·사용자 보고 한 줄, `approval_20260930-v3-changed-stmt-scope.md` 재측정 문단 | 같음. 실제 착수 수는 B26-1 1차 auditor가 병합본 base에서 다시 잰다(card 'V3 계획' 5) |
| B26PRE-20 | 주표 20 전부 N2w 대상 | b26_reconcile 통합 측정(v4 head) | `draft_b26pre.spec.md:13~14`·표 1(335~357행), `b26pre_launch.sh:74` 커밋 제목 '주표 20 중 18 죽임' | 20/20 대상. **'18 죽임' 실측: 18/20 죽음**(실제 도구 `changed_defs`·`_Scope.targets`·`mutants`·`_replace_def` 변이 + 시제품 19 test, seed 1), 생존 2 = SR 11800·11879(backfill 몫), 죽인 test 이름까지 card 표 1과 같음 -- `b26pre_backfill_post35_dryrun.md` §2 (card 35 병합본 a17b8bd 사전 실행 2026-10-02 — 공식 병합 뒤 재확인). 판정 수치는 여전히 b26pre 순서 7 auditor 몫 |
| EQ4-b26a | 등가 4 전부 대상 | `plan_summary.txt` REMAIN 4 | `draft_b26_1.spec.md:386~397`, `b26_1_carry.sh:89` `V3_RE` | 4/4 대상 |
| EQ4-b26v5 | range `const-` 대상, `[0]` `const-` 없음 | 계약 15 C1·C2(`b26v4c.cleanup`) | 같음 | range 대상·`[0]` 없음. **'4 → 1 생존'은 deferred**(B26-1 1차 `attempt1_v3.json`에서만) |
| CARRY5-* | 계약 5 가정 | `b26_1_carry.sh` check heredoc 안 '# 범위 card 35(' 주석 ~ `assert v["killed"]` 줄(m1~m4 단정 포함 20줄, `== [mid]` 줄만 뺌)을 그대로 뽑아 모든 V3 실행 출력에 실행 | `b26_1_carry.sh` check 단계 | ok(`--out` 대상 레코드 수 = `mutants`, `not_targeted` 레코드 수 = 출력 `not_targeted`, id 중복 0). **실제 1차 출력 전체 단정은 deferred**(B26-1 1차 auditor 뒤 `b26_1_carry.sh check`) |
| V3-B26U3 | 299/2,136, 생존 1 | (새 실행) H5T = H5 + `_metric_kcl_residual` 직접 호출 test 1개(card 'V3 계획' 4 모양 -- 인벤토리 0 생존 제거), 가짜 pytest = U3 변이 `range(i + 0, len(chains))`만 생존·나머지 죽음·기준 실행(diff 없음) 통과 | `draft_b26_1.spec.md` 'V3 계획' 1·3·4 | 299/2,136, 생존 = U3 하나 |
| **CARRY-FULL-b26u3**(오케스트레이터 추가) | m1~m4 모양은 spec·모의 도구(`p35_sim35.py`)로만 정함 | `b26_1_kit_selftest/out_check_test.sh`의 피검과 같은 것 = `b26_1_carry.sh` check 단계 heredoc(`local v3; v3=$("$PY" -B - "$WT_A/$AUD/attempt1_v3.json" …) <<'EOF'` ~ `EOF`)을 그대로 뽑아 V3-B26U3의 **실제 도구** 판정 JSON·`--out`·head SD·`V3_RE`(carry 스크립트 줄에서)·SD로 실행 | `b26_1_carry.sh` check 단계(review_kits_4a2 m1~m4: result 닫힌 집합, int 전용, `not_targeted`·`targets_by_def` 필수, `not_targeted` 레코드 키 정확히 `["id","result"]`, `targets_by_def` 키 `<경로>::<qualname>`, Σtargeted = mutants·Σnot_targeted = not_targeted) | **PASS**. FAIL이면 carry 쪽 정정 대상(어느 단정인지 note에 마지막 오류 줄). 실측: 실제 도구(a17b8bd) U3 실행(H5T)에서 전체 heredoc **PASS**(m1~m4 포함, 생존 1 = U3, 묶기 해시 일치), v5 실제 출력(가짜 pytest, 생존 299)에서도 m1~m4 블록 **PASS**(전체 heredoc은 '생존 U3 1개' 단정에서 기대대로 FAIL) -- `b26pre_backfill_post35_dryrun.md` §4 (card 35 병합본 a17b8bd 사전 실행 2026-10-02 — 공식 병합 뒤 재확인) |
| LINES-G1\|… | `4a286f0` 줄(예: `changed_defs` 호출 413, `mutants(` 루프 423, 출력 465, `make_clone` 371) | `grep -n`(g1_briefs §0.7 ③ 식) | `draft_p3_g1.spec.md` '작성 전 실측' 1(`0f23786` 줄 표기), `g1_briefs.md` §0.1 26~27행 | `mutate_changed.py` 줄만 밀림(35가 `main`을 고침), reachability·source_lint·rt.py·run_all 98행은 같음 |
| G1-KEYS | `tool, verdict, targets, mutants, killed, survivors, survivor_bindings, exempt_ignored` | main 마지막 `json.dumps` 키(AST) | `g1_briefs.md` §0.7 ③, 35 spec 계약 5 | 옛 키 + `not_targeted`, `targets_by_def`(G1 키 `defs`·`moved`·`move_rejected`와 겹침 0) |
| LINES-B33\|… | `0f23786`: `rch.reach` 215, `build_graph(head_files)` 317, `_is_source` 315, `TimeoutExpired` 354~356, `killed` 387~392 / `4a286f0`: 263·365·363·404~405·449 | `grep -n`(B33 spec '작성 전 실측' 1·2 식) | `draft_b33.final.spec.md` 292~301행, 63·67행 | `mutate_changed.py` 줄 밀림(값만 갱신), `reachability.py` 줄은 같음 |
| G1-ANCH-* | 14앵커 전부 1 | `p35_static.py anchors`(install_proto.py `sub()` 앵커) | `g1_kit/install_proto.py`, `g1_briefs.md` 113~114행 | `rch *`·`sl *`·`rt observe` 1 유지. **`mc loop`·`mc mutants`·`mc print`는 0이 될 수 있다** → 시제품 재앵커(측정 전용) |
| G1-INSTALL | `installed 4` | `python -B install_proto.py <트리 사본>` | `g1_briefs.md` 113행 | 앵커가 깨지면 `앵커 mc …: 0개` -- 재앵커 뒤 다시 |
| G1-OOG | `4a286f0`: 9줄·8 스크립트 | `git grep -n -E '(mc\|mutate_changed)\.(changed_defs\|def_hash)\(' <rev> -- . ':!*.jsonl' ':!tools/gates'` | `draft_p3_g1.spec.md:278~279·310`, `g1_briefs.md:29·178·316·382` | 같거나 늘어남(35 판정 기록 scripts가 더할 수 있다 -- 늘면 G1 '작성 전 실측' 5·auditor m2 목록에 더한다) |
| G1-A32B-* | 93단계 전부 FAIL(base 도구, 단계 exit 분포는 `g1_kit/out/a32_base_4a286f0.jsonl`) | `gen_attack32.py b` + `run_all --only 32-moved-defs` | `g1_briefs.md` §0.7 ⑥('93 단계 exit가 표 왼쪽 열과 같음') | 단계별 exit 같음(35가 대상 선택만 바꾸고, 공격 32 V3 단계는 새 def·옮긴 def 위주) -- 다른 단계가 있으면 card 표 왼쪽 열 재검토 |
| G1-A32P-* | 93/93 PASS(`a32_proto_4a286f0`) | `install_proto` + `gen_attack32 --scope` + `G1_SCOPE=1` | `g1_briefs.md` §0.4 | 시제품 재앵커 전에는 잴 수 없음(install 실패로 기록) |
| G1-NOOP-* | `noop_base_4a286f0`: 8 PASS·4 FAIL(28·31·34·v3_survivor는 그 실행 환경에서 V3 exit 2) | `run_all` 기본 11 + `34-` | `g1_briefs.md` §0.7 ⑥ | 케이스 판정 같음 + `35-` 새 케이스 PASS. 옛 FAIL 4가 여기서 PASS로 바뀌면 환경 차이(옛 실행의 exit 2)이지 35 효과가 아니다 -- 노트에 단계별 exit 차이를 남긴다 |
| SIMHEAD-engine | -- | `git diff --quiet <old> <rev> -- 'skills/analog-gmid-design/assets/*.py'` | (전제) | 0 차이(35는 도구만 고침). 차이가 있으면 모의 head 빌더(줄 앵커)가 그 rev에 안 맞을 수 있다 |

자동화하지 않은(=deferred) 것: b26pre '18 죽임', B26-1 '등가 4 → 1 생존', carry 단정의 실제 1차 출력 대조 -- 모두 실제 test 실행이 필요한 판정이라 각 card의 auditor 몫이다(이 스크립트는 대상 집합·출력 모양만).

## 3. 리허설(2026-10-02, gate `master` `4a286f0` + `--sim35`, scratch `/c/g237` -- 끝나고 삭제)

모의 도구 = `p35_sim35.py`(이전 키트의 독립 프로토타입 `v3scope_kit/scope_proto.py` select(N2w)를 `mutate_changed.main`의 계약 4·5 자리(묶기 card가 남긴 425행 주석 자리)에 얹음,
`--out` not_targeted 레코드·`not_targeted`·`targets_by_def` 출력. 한계: `deleted_statements`·`def_header_changed` = null, 계약 9(데코레이터) 없음). 실제 병합본이 오면 `--sim35` 없이 돌린다.

실행 3번:
1. `remeasure.sh --skip-slow 4a286f0`(모의 없음 = 35 전 실제 도구): TOOL35 0 → **needs35**, V3 7개 **needs35**(건너뜀), 정적 항목 전부 same(옛 = 새 rev), G1-KEYS changed(35 키 없음) -- 57항목, 저장소 불변. '35 전이면 표시하고 끝까지 간다' 경로 확인.
2. `remeasure.sh --sim35 4a286f0`(전체): V3·정적·공격 32 base·시제품까지 끝, 무동작 미리보기 중 **백그라운드 상한 2시간에 걸려 끊김**(다른 agent 부하로 `23-v4-boundary` 한 케이스가 40분 -- 옛 22분).
3. 끊긴 무동작 미리보기만 같은 명령(스크립트의 `run_all … --only`·`p35_items.py slow noop`)으로 이어 돌리고 `table`·저장소 상태 확인을 손으로 마저 함.
→ **실제 병합 뒤에는** `--skip-slow` 한 번(약 45분) + 느린 것 따로, 또는 전체를 상한 없는 셸에서 돌린다(전체 약 2.5~3시간, 부하에 따라).

### 3.1 결과(83항목: same 64 · changed 18 · needs35 1)

| 묶음 | 결과 |
|---|---|
| V3 대상 수(모의 도구, 가짜 pytest) | P9 12/16, BF 4/93, B34 10/45(+ spec 10 id 일치), B26 v4 301/2,141, 시나리오 A 299/2,141, v5 299/2,136, U3 299/2,136 -- **전부 옛 값과 같음**, 도구 대상 id와 proto 독립 계산 대칭차 0, `--out` 순서 = 생성 순서 |
| b26pre·등가 | B26PRE-20 20/20 대상, EQ4 시나리오 A 4/4 대상, v5 range `const-` 대상·`[0]` `const-` 없음 |
| carry | CARRY5(m1~m4 블록) 7실행 전부 ok. **CARRY-FULL PASS**: H5T 실행의 생존 1 = `stick_diagram:find_differential_pair_candidates:const-:body[8].body[3].body[1].body[0].iter.args[0].right`, heredoc 전체(묶기 해시 재계산·경로 노드 `range(i + 1, …)`의 1 포함) 통과 -- **단 모의 도구 출력이다. 실제 35 출력에서 다시 돈다** |
| 줄 번호(changed = 기대대로 `mutate_changed.py`만) | G1: `changed_defs` 호출 413 → 417, `mutants(` 루프 423 → (모의가 `enumerate(mutants(…))`로 바꿔 grep 식 불일치 -- 실제 35의 모양에 따라 식을 고칠 것), `json.dumps` 432·454·456·460·465 → 437·447·469·471·475·480, `_rmtree_force` 464 → 479. B33: `TimeoutExpired` 404 → 407, `"timeout"` 405 → 408, `killed += 1` 449 → 464(`rch.reach` 263·`build_graph(head_files)` 365·`_is_source` 363은 같음). reachability·source_lint·rt.py·run_all 98행 같음 |
| 출력 키 | G1-KEYS = 옛 8키 + `not_targeted`, `targets_by_def`(G1 키와 겹침 0) |
| install_proto | 앵커 14 중 `mc mutants`·`mc print` 0 → `install_proto` 실패(`앵커 mc mutants: 0개`), G1-A32P는 잴 수 없음(changed). `mc loop`·`mc read_tree`는 모의에서는 1 -- 실제 35가 그 줄을 건드리면 더 깨진다 |
| 게이트 밖 호출 | 12줄·9파일 → 같음(이 grep은 docstring·문서 줄을 빼지 않아 card의 '9줄·8 스크립트'보다 많다 -- 옛·새를 같은 식으로 비교) |
| 공격 32 base | 93단계 FAIL, 단계 exit 분포 {0: 10, 1: 83} -- `a32_base_4a286f0`과 단계별 exit 같음 |
| 무동작 미리보기 | 8케이스 같음. **28·31·34·v3_survivor는 옛 기준선 FAIL(V3 exit 2) → 새 PASS** -- 35 효과가 아니라 옛 기준선(`g1_kit/out/noop_base_4a286f0.*`, `C:/g225`) 실행 환경 문제로 보인다(이 스크립트는 HOME·APPDATA·TMP를 scratch로 맞춤). G1 키트 기준선을 다시 떠야 한다. 34(6단계)는 모의 35 도구에서 PASS(계약 7 '34 결과 불변'과 맞음). `35-`는 needs35 |
| 저장소 | 실제 저장소 HEAD `4a286f0`·status·reflog 345 앞뒤 같음. refs는 실행 중 오케스트레이터의 `role/*/20260930-v3-changed-stmt-scope` 생성·이동으로 바뀜(이 스크립트는 refs를 쓰지 않음 -- 보고만 하도록 고침) |

### 3.2 실제 병합 뒤 할 일

1. `bash _drafts/post35_kit/remeasure.sh <gate master>`(`--sim35` 없이). `TOOL35-marker`가 needs35면 35가 아직 안 들어간 판이다.
2. `changed` 항목마다 '적힌 곳'을 고친다. 특히 V3 수가 다르면 그 card(BF·B34·B26-1·b26pre)의 'V3' 문장과 launch 상수(`V3_WANT` 등), CARRY-FULL FAIL이면 `b26_1_carry.sh` heredoc(오케스트레이터 지시), install_proto 앵커는 G1 키트 시제품(`g1_kit/install_proto.py`)을 재앵커한 뒤 G1-A32P를 다시.
3. deferred(b26pre 18 죽임, B26-1 등가 4 → 1, carry 실제 1차 출력)는 각 card auditor 순서에서.
