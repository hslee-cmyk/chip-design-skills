# FU 키트 점검 -- gate `master` `6df4bd7` (b26pre·backfill 병합 뒤, B26-1 spec card 커밋 직후)

작성 2026-10-07. 읽기 전용 점검(키트·초안·저장소 수정 없음). 대상: `_drafts/draft_p3_fu.spec.md`, `_drafts/fu_briefs.md`, `_drafts/fu_launch.sh`.
실제 저장소는 `git -C` 읽기만 했다. 측정은 스크래치 `C:/g438`에서만 했고(clone `-c core.autocrlf=false`, origin 제거, TMP/TEMP = `C:/g438/tmp`), 끝에 지웠다.
직전 점검 = `_drafts/t0_fu_at_2183.md`(gate `2183f2e`).

## 결론

**멈출 것 없음.** `2183f2e..6df4bd7`(11커밋)이 FU 판정 앵커를 하나도 깨지 않는다. 지금 고칠 drift는 문장 2건(필수 1, 관찰값 갱신 1)이고, 선택 갱신이 2건 있다.
B26-1(진행 중)·B33(gate_change: yes)이 병합되면 아래 (b) 목록을 다시 잰다 -- 그때도 계약·판정 유형은 바뀌지 않을 것으로 본다(DR·ACF가 쓰기 경로 밖).

## 1. `2183f2e..6df4bd7`에서 바뀐 범위

* 엔진: `sizing_recipe.py` +4/−5(`run_matching_safety_with_finger_growth` 안 11758~11878 -- backfill). **DR·ACF 0줄, SD 0줄, TL 0줄.**
* test: 새 `tests/contracts/test_b26pre_existing_paths.py`(593줄)·`test_b26_backfill_interdig.py`(206줄). unit·probes 변경 0, `test_ic5.py`·`test_df23_inventory.py`·`test_ts3_no_print_verdicts.py` 변경 0.
* `tools/`·`docs/01-plan`·`docs/02-design/features`·레지스트리·`docs/03-analysis/gain-budget-gmid-sizing-30-module-split/**`·`.ai/verification/20260930-df36-instance-relpath/**`·phase2-dod.md 변경 0
  (`git diff --stat 2183f2e 6df4bd7 -- …` = `.ai/approvals/20260930-b26-b40-reason-key.md` 새 파일 하나뿐 -- FU 무관).
  그래서 spec·브리프가 인용한 줄 번호(merge_gate 1137~1166, role_hooks 913·914·926·1066~1070, role_commit_gate 98~99, `lib/sb.py` 327~332, 계획 682·688·840·993, design 30 534, design 05 289,
  범위 정책 spec 249)는 `2183f2e` 점검 결과 그대로 성립한다.
* 새 spec card `20260930-b26-rail-accessor-set`(+interface card) -- 문서만.

## 2. (a) 지금 drift와 재확인 결과

### 2.1 재확인(성립)

| 확인 | `6df4bd7` 결과 |
|---|---|
| `fu_launch.sh conds` | **exit 3, `[중단]` 없음**: 1~7·10~13 = 0, 8 = 128(B26-1 판정 기록 없음), 9 = 128(B33 없음), 조건 4 규약 전체 = 0. measured rev 없음. 역할 브랜치 = B26-1의 `role/{audit,code,test}/20260930-b26-rail-accessor-set` 셋(S-6은 `pre` 몫 -- B26-1 정리 뒤 0이어야 함) |
| 조건 11 (DR·ACF = `dd60db6`) | 0 -- DR·ACF 바이트 같음. 머리(DR 27행 docstring 끝·28 `import html as _html`, ACF 37 `"""`·38 `import sys`) 그대로 |
| 조건 12 (future 줄 = SR·SD·TL) | 0 -- `:(glob)` 최상위 SR 35·SD 32·TL 24 그대로(backfill 수정은 11758행 아래) |
| A2(`p3kit_fu/fu_codeobj.py`, base `6df4bd7` → 두 줄 head, `--selfcheck`) | 같음 **DR 16(qualname 12)·ACF 5**, 다름 0, `__annotate__` **DR 5·ACF 4**, 자기 점검 FAIL(`build_topology_device_table` co_code·co_varnames·co_consts·co_flags), `pass` true; import 관찰 이름 차이 `annotations` 하나, `__annotations__` 문자열화 DR 5·ACF 4 함수; dump 21줄 base = head(sha256 `f94f7895…` -- B 관찰값과 같음, 재현 대상 아님). Python 3.14.2 |
| 계약 5(c) 주석 조회 | 5곳 그대로(dup_kcl_edges 283·293, dup_w_calc 199·450, probe_mirror_ratio_error 85) -- DR·ACF 객체 0. 새 test 2파일에 `inspect.signature`·`__annotations__` 등 0 |
| 계약 5(d) DR·ACF 이름 읽는 추적 `.py` | **23개, `2183f2e`와 목록 바이트 같음**(새 test 2파일은 DR·ACF 이름을 쓰지 않는다) -- `.annotations` 읽기 0 |
| 계약 7 `reg_check.py` | base·head `발견 0`(exit 0) |
| 레지스트리 217행 `design_report.py:32` | 그대로 |
| 승인 기록 `20260930-30-module-split-design` | 108행 FU id, 112행 D-29 원문 그대로(조건 1·2 = 0) |
| 계약 3(b)(c) 스크립트 | e_lib blob `00fbb20f1177fb9899c75374dd73e9077b087547` 그대로, `e_inst_p3.py` sha256 `7d26134a…` 그대로 |
| PT3 관찰 | b26bf 판정 기록(`22fd126`) V1: 병합본 `0bb2278` **1114 passed·15 xfailed**(base `863a037` 1109) -- 명령 = `--gmid-phase=3 --gmid-strict=`(PT3와 같음). `0bb2278..6df4bd7`은 문서 커밋뿐이라 `6df4bd7` PT3 = 1114·15, id 1129(passed+xfailed). V10 대상 아님(관계 A1) |

### 2.2 고칠 문장(정확한 편집안)

**E1 (필수 -- 줄 번호 drift, 원인 = rk 개정이 `fu_launch.sh` 235행에 `trap - ERR`을 넣음)** `_drafts/fu_briefs.md:88`
* 전: ``(`fu_launch.sh` `print_role_cmds` 340~342행과 같은 `git -C <repo> worktree add …` 꼴 -- `cd` 없이 저장소를 `-C`로 지정한다.)``
* 후: ``(`fu_launch.sh` `print_role_cmds` 341~343행과 같은 `git -C <repo> worktree add …` 꼴 -- `cd` 없이 저장소를 `-C`로 지정한다.)``
* (같은 파일의 다른 `fu_launch.sh` 줄 인용 -- 41행 'kit-cmds(212행)·조건 12(148행)', 46행 '`meas_rev`, 110~115행' -- 은 현재 판과 맞다.)

**E2 (관찰값 갱신 -- 판정 무관)** `_drafts/fu_briefs.md:129`
* 전: ``… gate `master` `2183f2e`(B34 병합 뒤) 1090 passed·15 xfailed·id 1105 -- 그 rev의 관찰일 뿐 …``
* 후: ``… gate `master` `2183f2e`(B34 병합 뒤) 1090 passed·15 xfailed·id 1105, `6df4bd7`(b26pre·backfill 병합 뒤) 1114 passed·15 xfailed·id 1129(b26bf 판정 기록 V1 병합본 값) -- 그 rev의 관찰일 뿐 …``

**E3 (선택 -- 지금 틀리지 않음, 판 표기만)** `_drafts/draft_p3_fu.spec.md:164`
* 전: ``gate `master` `2183f2e`(B34 병합 뒤) 23개(``
* 후: ``gate `master` `2183f2e`(B34 병합 뒤)·`6df4bd7`(b26pre·backfill 병합 뒤, 같은 목록) 23개(``
* 어차피 착수 0단계에서 measured rev로 다시 잰다(아래 (b) 6) -- 지금 넣지 않아도 된다.

**E4 (선택)** `_drafts/fu_briefs.md:11` 끝 ``DR·ACF·Python만 보는 값(A2)은 gate `4a286f0`에서 다시 재 같았다(스크래치 `C:/g253`).`` 뒤에
``` `2183f2e`(`C:/g311`)·`6df4bd7`(`C:/g438`)에서도 같다(`_drafts/t0_fu_at_2183.md`·`_drafts/fu_at_6df4bd7.md`).``` 를 붙인다.

### 2.3 실행 환경 주의(키트 drift 아님)

Bash 도구 기본 셸(`/usr/bin/bash` = msys 5.2.37, PATH 앞쪽이 `/c/msys64/usr/bin`)로 `bash fu_launch.sh conds`를 돌리면 **exit 1 `[중단] 착수 조건 번호가 1~13이 아니다`**가 난다 --
`mktemp`가 `/tmp/tmp.*`를 주고 `cut`(msys64 판)이 다른 `/tmp` 루트를 봐 빈 출력(`test '' = '1 2 … 13 '`, `bash -x` 실측). 같은 스크립트를
`env TMP=C:/g438/tmp TEMP=C:/g438/tmp TMPDIR=/c/g438/tmp /c/msys64/usr/bin/bash fu_launch.sh conds`(CLAUDE.md 셸)로 돌리면 정상(exit 3). 착수 때는 msys64 bash 한 벌로 돌린다.
(키트 수정 제안 아님 -- 같은 `mktemp` 꼴을 쓰는 다른 launch 스크립트도 같은 조건이면 같은 증상이 날 수 있다.)

## 3. (b) B26-1 병합 뒤 예상 drift와 재측정 목록

B26-1 spec(`6df4bd7`) 쓰기 경로 = SD·SR(code-author), 레지스트리(계약 11, code-author), `A/tests/**`(test-author). **DR·ACF는 쓰기 경로 밖**이고 spec·interface card(심볼 표 전부 SD·SR 것)에 DR·ACF 이름 0.
DR·ACF가 SD에서 쓰는 것은 `load_topology`·`_audit_result_json`뿐이고 `load_topology`는 B26-1에서 시그니처가 **안 바뀌는** 뿌리(spec 119행). DR는 meta에서 `device_roles`·`symmetry`만 읽고 meta 전체를 직렬화하지 않는다
(그래서 `meta["rails"]`가 DR를 깨지 않는다). SD는 이미 `from dataclasses import … dataclass`를 가져오므로(39행) `RailDeclaration`이 import 줄을 더할 이유가 없다 -- SD 32행 future 줄 위치는 그대로일 것.
계획 정정은 이미 `8356c1e`(≤ `dd60db6`)에 들어갔다 -- B26-1이 계획을 더 고치지 않는다.

| # | 대상(FU가 기대는 것) | B26-1 예상 | 재측정 명령/방법 | 어긋나면 |
|---|---|---|---|---|
| 1 | 조건 8 | 0이 됨(2차 시도 병합 뒤 판정 기록) | `fu_launch.sh conds` | -- |
| 2 | 조건 11 DR·ACF = `dd60db6` | 그대로(쓰기 경로 밖) | `conds` 11 | 0이 아니면 A2·DR/ACF 머리·계약 2 기대 수를 그 판에서 `fu_codeobj.py`로 다시 재 spec '재현할 수치' A2·작성 전 실측 1 고침(`pre`도 멈춤) |
| 3 | 조건 12 future 파일 = SR·SD·TL | 그대로(새 최상위 모듈 없음 -- `RailDeclaration`은 SD 안) | `conds` 12 + `git grep -n` 줄 번호(SR 35·SD 32·TL 24 -- spec 161행, G1·D0a 문장) | 줄 번호만 바뀌면 spec 161행 문장만 |
| 4 | S-6 역할 브랜치 0 | 지금 B26-1 `role/*` 셋 있음, 두 번 시도라 1차 정리 뒤 2차에 다시 생김 | `conds` 끝 '역할 브랜치' 줄 / `pre` | B26-1 최종 정리 전 FU `pre` 불가(정상) |
| 5 | 계약 5(c) 주석 조회 5곳·줄 번호 | **바뀜**: B26-1 계약 12가 `test_dup_kcl_edges.py` 281~298 시그니처 test 두 개(현 283·293 `inspect.signature`)를 고치고, 새 `test_b26_rail_accessor.py`가 `inspect.signature(stick_diagram.…)`(계약 4 기본값 -- spec 124·125행) 3곳 이상 더함. 대상은 SD 객체뿐일 것 | `git grep -nE "get_type_hints\|__annotations__\|annotationlib\|get_annotations\|inspect\.signature" <B> -- '*.py'` | 곳 수·줄 번호를 spec 60행(계약 5 '실측: (c) 5곳 -- 계약 test 2파일·probe 1파일')·163행(작성 전 실측 1)에 새 값으로. DR·ACF 객체가 대상이면 멈춤(계약 5 결론 재검토) |
| 6 | 계약 5(d) DR·ACF 이름 읽는 추적 `.py` 23개 | 늘 수 있음: B26-1 판정 기록 `scripts/`가 E-INST 사본(`e_inst_*.py`, DR 이름 포함)을 넣으면 +1 이상(B34 선례 +1). b26pre·backfill은 +0이었음 | `git grep -lE "design_report\|audit_current_forced" <B> -- '*.py'` 개수·영역별, 그 파일들에서 `.annotations` 읽기 0 | spec 163~165행 수·영역 분해 고침(결론 무변경) |
| 7 | 레지스트리 217행 `design_report.py:32` | 줄 번호가 밀릴 수 있음: 계약 11이 §2 40·43·45행과 행 문구를 고침(행 추가 시 217 → 217+k) | `git grep -nE "(design_report\|audit_current_forced)\.py:[0-9]+" <B> -- docs/01-plan docs/02-design <REG>` | spec 152·173행, 브리프 162행 '레지스트리 217행' 고침. 칸 내용(`:32`)은 그대로일 것. `reg_check.py` base·head exit 0 재확인(계약 7) |
| 8 | PT3 관찰 수 | 늘어남(새 계약 test 파일 + selftest 픽스처 `supply_nets` 조정 17곳 -- spec 529~530행) | b26-rail 판정 기록 V1 병합본 수 | 브리프 129행 관찰 문장(V10 무관) |
| 9 | E-LIB `hash` | **바뀜**(meta에 `rails`; `_TEMPLATE` 예외 종류 AttributeError → ValueError -- B26-1 spec 304행) | FU 판정 때 base에서 | B 관찰만 낡음(spec 124행이 이미 예고) -- 고칠 것 없음 |
| 10 | E-INST `raw_sha256` 파일럿 `2fc426d9…`·`folded_cascode` `ef3cd996…` | 그대로 예상(B26-1 계약 8 'E-INST instance.json 해시 동일') | B26-1 판정 기록 계약 8 증거 | 달라도 V10은 관계 A1 -- B 관찰 문장만 |
| 11 | A2 코드 객체 값 | 그대로(DR·ACF·Python에만 묶임; import 관찰은 SD를 import하지만 `load_topology` 시그니처 불변) | `fu_codeobj.py <base> <두 줄 head> out --selfcheck` + `dump` 두 판 | 2번과 같은 처리 |
| 12 | 계약 4 V3·V4·V6·V7 기대 | B26-1은 `gate_change: no` -- 도구 불변 | -- | -- |
| 13 | DR·ACF 참조 계약 test(`test_ic5.py:48`, `test_df23_inventory.py:56`, `test_ts3_no_print_verdicts.py:30`) | 그대로 예상(B26-1은 `test_ic5` `_TARGET_NAME_RES`·영역 표에 안 걸리게 이름을 고름 -- spec 507행) | `git grep -n "design_report\|audit_current_forced" <B> -- A/tests/contracts` | spec 175~176행 줄 번호 |
| 14 | 승인 id 집합(`pre`의 `_approved_ids`) | 늘어남(B26-1 두 번 시도의 V5 운반 승인 4·5 등) | `pre`가 실행 중 base·head 비교 | 영향 없음 |

**B26-1 밖이지만 FU 전에 들어오는 B33(`20260930-v7-registry-edges`, `gate_change: yes`, phase 0.5)**: draft(`_drafts/draft_b33.final.spec.md`)가 `tools/gates/reachability.py`(5회)·`merge_gate.py`·`integrity.py`와
design 05(§10·§18, 승인 `diff_path` = 05-role-separation design)를 가리킨다. 그래서 B33 병합 뒤 다음을 다시 잰다:
* spec 77행·브리프 1절의 `merge_gate.py` 1137~1166(equivalence test 사슬 거부 줄), design 05 §10-4 **289행**(M^1 = `old`), role_hooks 913·914·926·1066~1070, role_commit_gate 98~99, `lib/sb.py` 327~332 -- 줄 번호.
* 계약 4 V7 기대(`new_defs` [])와 '작성 전 실측' 6·8의 V4~V7 출력 모양 -- B33 판 `reachability.py`로 base 모의 실행.
* 게이트 캐시 판이 바뀌므로 V3 모의(`targets` DR·ACF, `mutants` 0, `not_targeted` 0, `targets_by_def` {})도 다시.

## 4. 측정 기록

* `fu_launch.sh conds`(실제 저장소, 읽기 전용): `env TMP=C:/g438/tmp TEMP=C:/g438/tmp TMPDIR=/c/g438/tmp /c/msys64/usr/bin/bash …/fu_launch.sh conds` → exit 3(위 2.1). 이 스크립트가 원래 쓰는 `_drafts/fu_launch_state.txt.tmpd`(이미 있던 폴더) 말고 쓴 것 없음.
* A2: `C:/g438/base`·`head` = `6df4bd7` 복제 두 벌(autocrlf=false, origin 제거), head는 DR `import html as _html` 앞·ACF `import sys` 앞에 future 줄 하나씩(작업 트리만, `git diff --stat` 2 files 2 insertions). `fu_codeobj.py` `--selfcheck`·`dump`, `reg_check.py` 두 판.
* `C:/g438` 삭제 완료.
