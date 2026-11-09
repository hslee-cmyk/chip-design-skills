# Phase 2 완료 판정(DoD) -- auditor 브리핑 (v2, P10b 판정 기록 push 직후 그대로 보낸다)

받는 agent: `gmid-verification-auditor`. 이 작업은 card가 아니다(spec card·판정 기록 .json·커밋 없음). Phase 1 선례(`docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/phase1-dod.md`, 781f405)처럼
auditor가 독립으로 재고 **결과 파일만** 쓴다. 오케스트레이터가 그 파일을 다시 계산하지 않고 `phase2-dod.md`로 옮겨 커밋한다.

## 0. 착수 조건 (보내기 전에 오케스트레이터가 확인)

- gate `master`에 P9(`20260930-p9-kcl-edges`)·P10(`20260930-p10-df23-inventory`)·P10b(`20260930-df23-registry-record`) 판정 기록이 있다.
- 기준 정정 두 건이 gate에 있다: design 20 §10 E4 정정 2140da8 + 승인 `20260930-phase2-e4-baseline`, E4 PT phase 정정 fe638ab + 승인 `20260930-phase2-e4-phase`.
- B28 `20260930-v3-history-clone` 판정 기록이 있다(V3 도구 변경이 DoD 전에 끝나 있음 -- 이미 있음, 2b41e79 병합).
- `C:/g90`이 없다(이 작업 전용으로 예약). 다른 살아 있는 agent가 `C:/g90`을 쓰지 않는다.

## 1. 기준 문서 (판정 기준은 이 문서들이고, 이 브리핑은 실행 절차만 정한다)

- 측정 명령·통과 기준: design `docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md` §10 E0~E5(2140da8·fe638ab 정정본). 조건: 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` N6.2 Phase 2 행(1017행)과 N6.3(1028행~).
- 승인: `.ai/approvals/20260930-phase2-e4-baseline.md`, `.ai/approvals/20260930-phase2-e4-phase.md`(범위: **E4만** `PT2`. E0~E3·E5는 design 10 §10 `PT` 그대로 -- `--gmid-phase=1`).
- 이 브리핑과 기준 문서가 어긋나면 기준 문서를 따르고 어긋남을 결과 파일 '절차 메모'에 적는다. 기준을 해석으로 바꾸지 않는다(필요하면 멈추고 보고).

## 2. 경로·가드 (필수)

```bash
set -euo pipefail
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills      # 메인 저장소: 읽기 전용, git -C로만, 상태 바꾸는 git 금지
G=C:/g90                                                       # 유일한 임시 경로. 이 밖에 쓰는 것은 결과 파일(아래 OUTF) 하나뿐
ISO=$G/iso ; S=$G/scripts ; O=$G/out ; PY=C:/Python314/python.exe
OUTF=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/phase2_dod_result.md
H=$(git -C $R log -1 --format=%H master -- .ai/verification/20260930-df23-registry-record.json)   # 대상 커밋 = P10b 판정 기록 커밋
git -C $R log --oneline $H..master        # 출력이 있으면 결과 파일에 적는다(측정 대상은 H로 고정)
mkdir -p $S $O $G/snap $G/pyc
git -C $R status --porcelain --ignored > $G/snap/main_before.txt ; touch $G/snap/stamp
git clone -q --no-hardlinks --no-local -c core.longpaths=true "$R" $ISO
git -C $ISO remote remove origin
git -C $ISO checkout -q --detach $H
```

- 모든 git은 `git -C $ISO`(메인은 읽기 명령만 `git -C $R`). `cd` 금지.
- 판을 바꿀 때마다: `git -C $ISO checkout -- workspaces ; git -C $ISO clean -fdxq` 후 `git -C $ISO checkout -q --detach <rev>`, 그리고 `git -C $ISO status --porcelain --ignored` 0줄 확인.
- 메인 저장소 쓰기 감시: E-INST 실행 뒤마다와 맨 끝에 `git -C $R status --porcelain --ignored`를 `main_before.txt`와 비교(같아야 함), 맨 끝에 `find`로 `$R/workspaces $R/skills $R/tools $R/.ai/verification` 아래 `-newer $G/snap/stamp` 파일 0개 확인.
- 오래 걸리는 실행(PT2 각 약 5분, 파일럿 E-INST 판당 약 7~8분)은 `run_in_background`로 돌리고 출력은 `$O/*.txt`·`*.json`에 쓴다(stdout에만 의존 금지).
- **결과 파일 `$OUTF`는 항목 하나가 끝날 때마다 추가로 쓴다**(중간에 끊겨도 남게). 원출력은 `$O`에 둔다. **커밋하지 않는다**(메인·복제본 모두). `C:/g90`은 지우지 않는다 -- 오케스트레이터가 옮겨 적은 뒤 지운다.
- 끝나면 복제본 `git -C $ISO reflog` 이동 목록과 `status`, 메인 HEAD·status 불변을 결과 파일에 적는다.

## 3. 공통 정의

```bash
# 게이트 캐시(대상 커밋마다 따로): <rev>의 tools/gates
mkdir -p $G/cache_$REV && git -C $ISO archive $REV tools/gates | tar -x -C $G/cache_$REV      # CACHE=$G/cache_$REV/tools/gates
# PT  (design 10 §10 정의 그대로 -- E0~E3·E5용)
PT()  { PYTHONPATH=$CACHE PYTHONPYCACHEPREFIX=$(mktemp -d -p $G/pyc) $PY -P -m pytest -c $CACHE/pytest_gate.ini --rootdir=$ISO --confcutdir=$ISO $ISO/skills/analog-gmid-design/assets/tests --gmid-phase=1 "$@"; }
# PT2 (E4 전용 -- PT에서 --gmid-phase=1만 =2로, 승인 20260930-phase2-e4-phase)
PT2() { PYTHONPATH=$CACHE PYTHONPYCACHEPREFIX=$(mktemp -d -p $G/pyc) $PY -P -m pytest -c $CACHE/pytest_gate.ini --rootdir=$ISO --confcutdir=$ISO $ISO/skills/analog-gmid-design/assets/tests --gmid-phase=2 "$@"; }
```
정의에 없는 옵션(`-p no:cacheprovider`, `--gmid-strict=` 등)은 더하지 않는다. `-rA`·`--collect-only -q`·`-q`·`--color=no`만 출력 형식용으로 더한다.
주의(Phase 1 관찰 B13과 같은 현상): `PT`가 이미 `.../assets/tests`를 인자로 가지므로 뒤에 붙이는 하위 경로는 수집을 좁히지 않는다(합집합). 선택은 `-k`가 한다.

## 4. 측정 (H 판, `CACHE=$G/cache_$H/tools/gates`)

**E0** -- `$PY -B $ISO/skills/analog-gmid-design/assets/tests/tools/reg_check.py --registry $ISO/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root $ISO`
→ exit 0, 출력 `reg_check: 발견 0`. §7 행 수·§1 집계 D 값·`처리` 열 형식을 결과에 적는다. (인자 추가 없이 -- 이것이 E0.)

**E0 옆 기록(판정 기준 아님 -- 계획 DF-23 행 '2(전수 목록·레지스트리 기록)'의 증거, P10b spec card 결정 메모)**: 같은 명령에 `--df23-inventory $ISO/docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json`을 더해 exit·출력을 적는다(기대 exit 0, 발견 0). N6.3 절 옆에 'DF-23 레지스트리 기록' 한 줄로 보고한다.

**E1** -- 수집 수는 모듈별로 센다(합계로 판정하지 않는다).
```bash
PT -k "dup_w_calc or dup_kcl_edges" --collect-only -q > $O/e1_collect_H.txt
grep -c '^skills/analog-gmid-design/assets/tests/contracts/test_dup_w_calc.py::'   $O/e1_collect_H.txt   # >= 1
grep -c '^skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py::' $O/e1_collect_H.txt   # >= 1
PT $ISO/skills/analog-gmid-design/assets/tests/contracts -k "dup_w_calc or dup_kcl_edges" -rA > $O/e1_run_H.txt   # 실패·오류 0
```
수집된 노드 중 두 모듈 밖의 것이 있으면 모듈별로 적는다. 그리고 `$ISO/.ai/verification/20260930-dup-w-calc.json`·`20260930-p9-kcl-edges.json`의 `checks.V2.verdict` == `PASS`(둘 다)와 `basis` 요지.

**E2** -- `$PY -B $ISO/skills/analog-gmid-design/assets/tests/tools/engine_dup_scan.py --root $ISO > $O/e2_H.txt` → exit 0. 발견 줄 전부(JSON)와, 그중 `"exempt": true`인 것마다 면제 근거 승인 id(`.ai/approvals/*.md` 중 `target_kind: decision`이고 `target`에 `<path>::<rule>`이 든 기록 -- 사전 점검 기준 1건, `20260929-p4-scan-exempt`). 면제 아닌 발견 0.

**E3** -- design 문구(cat-file + 항목 수 대조)에 더해 '항목마다 담당 Phase'를 기계로 본다. auditor 자신의 스크립트 `$S/e3_check.py <iso> <rev> <out.json>`(작성자 산출물 미사용, 목록은 `git -C $ISO show <rev>:<경로>`로 읽음)으로:
1. `git -C $ISO cat-file -e <rev>:docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json` exit 0.
2. `len(items) == totals.n_items`, `totals.by_phase`·`by_role`이 items에서 다시 센 값과 같음.
3. 모든 항목이 `phase`를 갖고 값이 닫힌 집합 {`3`,`4`,`5`,`6a`,`6b`,`6c`,`7a`,`7b`,`7c`,`해당 없음`}의 원소 -- 이 집합은 계획 N6.1 순서표(989행~)에서 Phase 2 뒤 Phase 이름 + `해당 없음`으로 auditor가 직접 만들고, 목록의 `phase_source.closed_set`과 같은지도 적는다.
4. 모든 항목 `function`이 빈 문자열이 아님.
5. N6.2 "DF-29~DF-34의 위치가 목록에 들어 있고": DF-29~DF-34 번호별 '동작을 정함' 항목 개수를 센다. DF-30~DF-34는 각각 ≥1이어야 한다. DF-29는 0이 정상이다 -- DF-29 위치의 함수는 P5b(`20260923-d-delete-telescopic`)가 전부 지웠다(P10 spec card 의도 절 "N6.2 문장은 base 엔진에 남아 있는 위치에 대한 문장으로 읽는다", P10 판정 기록 재현 수치 DF-29 0). DF-29가 0일 때는 P5b 판정 기록과 base 엔진에 DF-29 위치 def가 0개임을 근거로 적는다(0이면서 위치 def가 남아 있으면 FAIL).
6. `measured_at` 커밋과 H의 엔진이 같음: `git -C $ISO diff --quiet <measured_at> $H -- <목록 scope_files 8개>` exit 0, 그리고 `scope_files`가 H의 `skills/analog-gmid-design/assets/*.py`(최상위) 7개 + `workspaces/run_harness.py`와 같은 집합.
H 판에서 1~6 전부 성립해야 PASS.

**E5** -- `PT $ISO/skills/analog-gmid-design/assets/tests/unit -k new_topology -rA > $O/e5_H.txt` → 실패 0, 수집 1개 이상. 수집된 노드 id 전부를 적는다. new_topology test는 `tests/contracts/`(`test_d_delete_dead.py`·`test_d_delete_telescopic.py`)에 있고 `unit`이 아니다 -- `PT`가 `tests` 전체를 이미 수집하므로 잡힌다(위 주의). 결과 표에 "수집 n건, 전부 contracts" 한 줄로 적는다(사전 점검 9건).

**E4(a) PT2 두 실행** -- `PT2 -q --color=no > $O/e4_pt2.txt` 그리고 `PT2 --gmid-dod -q --color=no > $O/e4_pt2_dod.txt`. 두 실행 모두 실패·오류 0. passed·xfailed·XPASS 수와 소요 시간을 적는다(수집 수는 Phase 1과 비교하지 않는다 -- design E4 기준). 각 실행 앞에 `git -C $ISO checkout -- workspaces ; git -C $ISO clean -fdxq`.

**E4(b) 스크립트 사본 (판을 바꾸기 전에, H 판에서)**
```bash
cp $ISO/.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py         $S/
cp $ISO/.ai/verification/20260930-df35-harness-paths/scripts/e_inst_df35.py      $S/
cp $ISO/.ai/verification/20260930-df36-instance-relpath/scripts/e_inst_df36.py   $S/
sha256sum $S/e_lib.py $S/e_inst_df35.py $S/e_inst_df36.py
git -C $ISO rev-parse $H:.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py $H:.ai/verification/20260930-df35-harness-paths/scripts/e_inst_df35.py $H:.ai/verification/20260930-df36-instance-relpath/scripts/e_inst_df36.py
```
사본 sha256과 blob id 둘 다 적는다(체크아웃 줄 끝 변환 때문에 사본 sha256은 blob 내용 sha256과 다를 수 있다 -- 요건은 두 판에 **같은 사본**을 쓰는 것). 세 스크립트는 da03c0e 판에 **없다**. `<out>`은 반드시 `$O`(복제본 밖 -- `clean -fdx`가 복제본 안 산출을 지운다). 실행은 항상 `$PY -B -P <사본> …`.

## 5. 판별력 대조와 다른 판 (H 측정이 끝난 뒤 이 순서로)

**E1 판별력 -- P9 직전 커밋 `7535799`**(P9 판정 기록의 `base_commit`): 판을 7535799로 바꾸고 `CACHE=$G/cache_7535799/tools/gates`로 E1과 같은 `--collect-only -q`를 돌린다 → `test_dup_kcl_edges.py::` **0건**(파일 없음), `test_dup_w_calc.py::` ≥1. H에서 E1의 dup_kcl_edges 수집이 P9로 생겼음을 보인다.

**E3 판별력 -- `C` = 766b5c2**(P10 문서 커밋 0fa6ca2 직전 = 목록 재측정 전): 판을 바꾸지 않고 `$S/e3_check.py`를 rev 766b5c2로 돌린다(6번 엔진 대조는 '해당 없음'으로 적는다) → 기대 **FAIL**: 1번(cat-file)은 성립하지만 3번에서 `phase` 가진 항목 0/590, `measured_at` 없음. design 문구의 cat-file만으로는 판별하지 못함을 같이 적는다.

**E4(c) 기준 판 da03c0e** (판 바꾸기 → status 0줄):
```bash
$PY -B -P $S/e_lib.py $ISO $O/elib_da03c0e.json
$PY -B -P $S/e_inst_df35.py $ISO current_reuse_telescopic_ota base $O/einst_da03c0e_current_reuse_telescopic_ota.json
$PY -B -P $S/e_inst_df35.py $ISO folded_cascode base $O/einst_da03c0e_folded_cascode.json
```
base 모드 출력의 `literal_counts_before` = [2, 1](ASSETS 2·WORKSPACES 1 치환), `engine_origin`·`sys_path_added`·`instance_path`가 전부 `$ISO` 아래, `fail_in_stdout` false인지 적는다. 이 단계 직후 메인 저장소 status 비교(da03c0e 하네스는 메인 절대 경로 리터럴을 가진다 -- 치환이 메인 쓰기를 막는지가 여기서 확인된다).

**E4(d) 병합본 판 H로 복귀** (판 바꾸기 → status 0줄):
```bash
$PY -B -P $S/e_lib.py $ISO $O/elib_H.json
$PY -B -P $S/e_inst_df36.py $ISO current_reuse_telescopic_ota $O/einst_H_current_reuse_telescopic_ota.json
$PY -B -P $S/e_inst_df36.py $ISO folded_cascode $O/einst_H_folded_cascode.json
```
E4 통과 기준(design E4 행 그대로): 두 판 모두 library 9/9 로드(`_TEMPLATE` 제외, 회로별 `ok` 전부 true·`exc` 없음), `elib` `hash`가 두 판에서 같음. E-INST 두 회로 모두 (a) `without_topology_ref_sha256` 두 판 같음 (b) H 판 `topology_ref_equals_expected_contract1` true, `path_string_hits` = [] (c) da03c0e 판 `topology_ref_is_join_of_ASSETS_DIR` true. 그리고 (a)의 PT2 두 실행 실패 0. 해시 전체 값을 표로 적는다.

## 6. N6.3 공통 조건 (H 트리)

1. **판정 기록 전수**(Phase 1 선례: 트리 전수): `$ISO/.ai/verification/*.json`(`_schema.json` 제외) 전부 `checks.V1`~`V10`이 `PASS` 또는 `N/A`. 건수를 적는다(2d58fd8 기준 31건 + P10·P10b = 33건 예상 -- 실측 값으로).
2. **Phase 2 판정 기록 16건** -- `^phase: 2$`인 spec card(H 기준 17장) 중 판정 기록이 있는 것. 표(id, evidence_type, V1~V10, audit 커밋, merge 커밋)를 실측으로 채운다:
   P1 `20260923-probe-dead-delete`, P2 `20260923-probe-relocate`, P3(a) `20260923-probe-promote-clean`, P3(b) `20260923-probe-promote-differential`, P4 `20260929-probe-engine-dup`, P5 `20260923-d-delete-dead`, P5b `20260923-d-delete-telescopic`, P6 `20260930-d-move-tests`, P7 `20260930-registry-grade-fix`, P8 `20260930-dup-w-calc`, P9 `20260930-p9-kcl-edges`, P10 `20260930-p10-df23-inventory`, P10b `20260930-df23-registry-record`, §8 밖 `20260930-restore-plan-functions`·`20260930-df35-harness-paths`·`20260930-df36-instance-relpath`.
   기록 없는 `phase: 2` card는 P3(c) `20260923-probe-promote-consistency` 하나여야 한다(사용자 결정 2026-09-29 "보류, P5로 진행", 백로그 B21 Phase 4; design §8 P3 행 "또는 `probe_physical_consistency` 제외 6개"가 허용). 다른 것이 나오면 FAIL로 보고.
   **Phase 2 목록 밖**: `20260930-v3-history-clone`(B28)·`20260929-rejudge-cache`는 spec card `phase: 0.5`(게이트 변경)라 Phase 2 기록 목록에 넣지 않는다. 1번 전수에는 들어간다 -- 표 아래 "Phase 2 기간에 병합된 0.5 card" 한 줄로 V 판정을 따로 적는다.
3. **merge gate(EL4) 형식**: 16건마다 판정 기록 파일을 마지막으로 바꾼 커밋(`git -C $ISO log -1 --format=%H $H -- .ai/verification/<id>.json`)이 `Role: audit`·`Change-Id: <id>` trailer를 갖고 H의 조상. `evidence_type`이 test-only가 아닌 12건은 제목 `merge <id>` 병합 커밋이 H의 조상(test-only 4건 P1·P3a·P3b·P10은 병합 없음·`code_commit` null이 정상). 기록의 `base_commit`·`test_commit`·`code_commit`(있으면)이 H의 조상.
4. **카드 밖 엔진 변경 0**: `git -C $ISO log --no-merges --format=%H da03c0e..$H -- 'skills/analog-gmid-design/assets/*.py' workspaces/run_harness.py 'skills/analog-gmid-design/assets/library/*.json'`(git 기본 pathspec이라 `*`가 하위 디렉터리도 맞춘다 -- tests 아래 .py 포함, 더 넓게 보는 쪽) 전부가 `Role: code` 또는 `Role: test` trailer와, 위 16건 중 하나인 `Change-Id`를 가진 커밋. 커밋 수와 card별 개수를 적는다(2d58fd8 기준 27개, 그 뒤 P10 test·P10b code·test가 더해짐).
5. **동작 변경 card의 거부 입력 test**: Phase 2는 동작 보존 Phase다. red-green 8건(P4·P6·P7·P8·restore·DF-35·DF-36·P10b)은 기록의 `red`(base에서 새 test FAIL)를, equivalence 4건(P2·P5·P5b·P9)은 `equivalence.outputs_hash`와 base 쪽 같음을, 삭제 키 `ValueError`는 E5 노드로 확인했다고 한 줄씩 적는다.

## 7. 남긴 관찰 (판정에 걸지 않는다 -- 실측으로 확인한 것만 적는다)

1. **결정 D2 (a)** (사용자 2026-09-30 "둘다 기본안으로 진행해", 기준 변경 아님 -- 승인 기록 불필요): `skills/analog-gmid-design/assets/tests/probe_physical_consistency.py`는 P3(c) 보류분(B21, Phase 4)으로 `tests/probes/` 밖(tests 루트)에 남아 E2 스캐너 범위(`PROBES_REL` = `…/tests/probes`) 밖이다. 확인: 이 파일만 `$G/d2/skills/analog-gmid-design/assets/tests/probes/`에 복사하고 `$PY -B <H 판 engine_dup_scan.py> --root $G/d2` → 기대 발견 1건 `rail-set`(40행 `RAIL_HI, RAIL_LO = …`), exit 1. 그리고 메인 체크아웃 절대 경로 리터럴 2개(33행 `ASSETS`, 38행 `INST`).
   기록 문장: "P3c 보류(B21, Phase 4) -- `tests/probe_physical_consistency.py`는 tests 루트에 남아 E2 스캐너 범위 밖이며, 스캐너 기준 rail-set 재구현 1건(40행)과 메인 절대 경로 리터럴 2개(33·38행)를 가진다. E2는 design 문구(`tests/probes/**`)대로 판정했다(결정 D2 (a))." 줄 번호·건수는 H에서 잰 값으로.
2. **E5 명령 경로**: new_topology 노드가 전부 `tests/contracts/`(위 E5). Phase 1 관찰 B13과 같은 현상, 판정 영향 없음.
3. **`--gmid-dod`의 엄격 대상**: E4(a) 두 실행의 xfailed 수가 같으면 "Phase 2 표식 IC 케이스 0 -- `--gmid-dod`가 Phase 2에서 엄격 대상을 더하지 않음"을 적는다(근거: `git -C $ISO grep -n 'phase="2"' -- skills/analog-gmid-design/assets/tests` 결과).
4. **추적 산출물 `workspaces/*/…instance.json`**(DF-36 뒤 재생성 안 됨 -- 드라이런 관찰 ④): `git -C $ISO show $H:<경로>`로 두 회로 추적 instance.json의 `topology_ref` 값을 보고, 메인 절대 경로면 "추적 산출물이 DF-36 이전 형식, E4는 새로 생성한 파일로 판정해 영향 없음"으로 적는다. 판정 대상 아님.
- **적지 않는 것**: B47(`library/folded_cascode.topology.md` 낡음)은 da03c0e..H에서 그 파일·`folded_cascode.topology.json`이 바뀌지 않았고(2d58fd8 기준 실측 0커밋) E0~E5 어느 항목도 재지 않으므로 Phase 2 DoD 범위 밖이다(Phase 4 design 백로그 소관). 그 밖의 범위 밖 발견은 결과 파일 끝 '범위 밖 메모'에 한 줄씩만.

## 8. 결과 파일 `$OUTF` 형식 (phase1-dod.md 머리를 따른다)

```
# Phase 2 완료 조건(DoD) 측정 결과 (auditor 원본 -- 오케스트레이터가 phase2-dod.md로 옮김)
대상: gate `master` = `<H 전체 해시>`(P10b 판정 기록 커밋). H..master 사이 커밋: <없음|목록>. 측정 주체 = gmid-verification-auditor(독립 측정, <날짜>).
기준: design 20 §10(2140da8·fe638ab 정정본), 계획 N6.2 Phase 2 행·N6.3, 승인 20260930-phase2-e4-baseline·20260930-phase2-e4-phase.
환경: 격리 복제본(--no-hardlinks --no-local, origin 제거, core.longpaths=true) C:/g90/iso, Python <버전>/pytest <버전>, 게이트 캐시 = git archive <rev> tools/gates. 메인 저장소 쓰기 0(status 전/중/후 동일, stamp 이후 파일 0).
## 판정  (| ID | 조건(N6.2) | 판정 | 측정 결과 |  -- E0, E1, E2, E3, E4, E5 순)
## 판별력 대조  (E1@7535799, E3@766b5c2)
## N6.3 공통 조건  (1~5, Phase 2 기록 16건 표, 0.5 card 줄, DF-23 레지스트리 기록 줄)
## 남긴 관찰(PASS, 차단 아님)
## 절차 메모  (브리핑과 기준 문서의 어긋남, 스크립트 sha256·blob id, 소요 시간, 복제본 reflog/status)
```
FAIL이 나오면 고치려 하지 말고 그 항목의 원출력 경로와 함께 결과 파일에 적고, 나머지를 끝까지 잰 뒤 보고한다. 판정 기록·spec card·승인·문서를 만들거나 바꾸지 않는다.

## 9. 오케스트레이터 (auditor 보고 뒤)

`$OUTF`를 다시 계산하지 않고 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md`로 옮겨(머리: 대상 커밋·측정 주체·환경, E0~E5 표, 판별력 대조, N6.3, 남긴 관찰) 문서 커밋 → `.ai/context.md` Python 바이너리 append(`git diff --numstat` 삭제 0줄 확인) → push 결과 확인 뒤 `C:/g90` 삭제. 이 커밋이 Phase 3 design 착수 조건("Phase 2 DoD PASS")의 인용 대상이다.
