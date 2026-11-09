# Phase 2 DoD 사전 실행(prerun) -- 공식 판정 아님

작성 2026-10-01 21:3x~22:4x KST. 목적: 공식 DoD 전에 예상 측정 판 H의 모래상자 사본 H'에서 브리핑 `phase2_dod_brief.md` v4의 E0~E5와 N6.3을 미리 돌려, 공식 실행에서 FAIL이나 INVALID가 될 곳을 찾는다.
모래상자 `C:/g145`(끝나고 지웠다). 메인 저장소와 role worktree에는 읽기만 했다. 메인 status는 실행 전후 같았다(`real main status same`).

## 0. H' 구성

| 단계 | 내용 | 결과 |
|---|---|---|
| 모래상자 | `post_p10b_dryrun_setup.sh /c/g145 54ef51ca8ad3800279369754b07583bb1cdfc120 --fake-record`: 메인 master `0f23786`을 복제하고 P10b 재시도 3차 병합 `54ef51c`(test `572d767` · code `b7b1e00`)까지 ff한 뒤 합성 audit 커밋 `254f4fa`를 만든다(gate 경로 치환 + 자리표시 `.ai/verification/20260930-df23-registry-record.json`). 이어서 bare 가짜 gate를 만든다 | 33 s, OK |
| 합성 audit가 필요한 이유 | 브리핑 가드 (1)에는 제목 `audit: 20260930-df23-registry-record`이고 판정 기록을 바꾸는 커밋이 필요하다. 실제 P10b 판정 기록은 아직 없다(`role/audit` 머리 = `54ef51c` merge) | -- |
| runbook `local` | `post_p10b_runbook.sh --repo /c/g145/r --state /c/g145/state.txt --render-tmp /c/g145/render --wt /c/g145/wt local`. pre → c1 `831a7b7` → d `21fbcfc` → appr `91f7576` → card `2be1219` → e2 `471bb8d` → e2appr `8ccac18` → ubf `7a1fd2f` → final | **150 s, rc 0. 단정에 걸린 것 없음**: 세 패치 `적용:`, md blob `711a5910…`·`2a3e67a5…` 일치, plan hash `7167e028…596d` 불변, E2 target `ddacfe22…ed64`(7b 사전 시험과 같은 값), EL3 hook 통과 |
| push(가짜 gate) | `git -C /c/g145/r push gate master:master` → `254f4fa..7a1fd2f`, accept-log 1줄 | 32 s, OK |
| `after-push` | OK | <5 s |
| **H'** | `7a1fd2f6517717f8574c463485ce8ec976668467` | -- |

이번 실행으로 P10b 재시도 3차가 바꾸는 파일(레지스트리 · `reg_check.py` · 새 test `test_reg_check_df23.py`)과 runbook 대상(design 20 · 양식 · history · library · context) 사이에 충돌이 없다는 것도 다시 확인했다(pre 기준 blob 단정 통과).

## 1. 가드(브리핑 §2) -- 가드 (4)만 끄고 나머지는 그대로

| 가드 | 결과 |
|---|---|
| H = ls-remote = gate/master | `7a1fd2f…` |
| (1) P10b audit 커밋 P | `254f4fa`(합성) 1개, 판정 기록을 바꾸고 H의 조상. "마지막으로 바꾼 커밋 != P" 경고는 나오지 않았다 |
| (2) E2 정정 커밋 E | `471bb8d`, Change-Id 1개, design 20만 바꾼다 |
| (3) 승인 기록 커밋 AC | `8ccac18`. 머리 id·diff·diff_head = E·diff_base = E^·diff_path 하나, target `ddacfe22022dd0b5d5f8bf2cc8c1e80b45c22844fa1624e8968a4fbd676aed64` = H 판 게이트 캐시 재계산값 |
| (4) md 일치 card | **공식 실행이면 여기서 멈춘다**. spec card는 있지만 `.ai/verification/20261001-topology-md-sync.json`이 없다(test 커밋이 아직 없다). 이번에는 끄고 진행했다 |
| H 판 E2 행 | 정정 문구(`patch_e2_wording.py` NEW)와 바이트가 같은 1줄, 옛 칸 0줄 |
| 가드 전체 + 복제 | 51 s(복제 32 s) |

## 2. 항목별 결과(H')

| 항목 | 결과 | 소요 | 공식 실행 예측 |
|---|---|---|---|
| E0 | exit 0, `reg_check: 발견 0`. §7 행 25 = §1 D 합 25. 처리 열은 `보류(Phase 3)` 9 · `보류(Phase 4)` 14 · `보류(Phase 6a)` 2 | 3 s | PASS |
| E0 옆 DF-23 기록 | `--df23-inventory …/df23_inventory.json` → **exit 0, 발견 0**. 0f23786에서는 exit 2였다(P10b 반영 확인) | 2 s | 기록 줄 정상 |
| E1 | 수집 130/1023: w_calc 106, kcl_edges 24, 두 모듈 밖 0. 실행 130 passed, 실패 0. V2: dup-w-calc PASS(기록 red-green), p9-kcl-edges PASS(기록 equivalence) | 42 s / 66 s | PASS |
| **E2(새 문구)** | exit 0, 출력 1줄 = `probes/probe_mirror_gain_ranking.py:183 lut-private "exempt": true`. `"exempt": false` 0줄. (c) 근거 승인: `.ai/approvals/20260929-p4-scan-exempt.md`(`target_kind: decision`, `target: skills/analog-gmid-design/assets/tests/probes/probe_mirror_gain_ranking.py::lut-private`). H 트리의 decision 기록 15개 중 이 path::rule을 가진 것은 이 1개. 면제 줄 수 1 = 문구의 "현재 … 1건" | 2 s | **PASS**. (a)(b)(c) 모두 성립하고 절차 메모에 적을 차이도 없다 |
| E3 | 1 cat-file 0 / 2 items 515 = totals, by_phase · by_role 일치 / 3 515/515 phase, 닫힌 집합 {3,4,5,6a,6b,6c,7a,7b,7c,해당 없음} = `phase_source.closed_set` / 4 빈 function 0 / 5 '동작을 정함' DF-29 0 · 30 27 · 31 16 · 32 1 · 33 12 · 34 18 / 6 `measured_at` 766b5c2 ↔ H diff --quiet 0, scope_files 8 일치. DF-29 위치 def: H 0건, da03c0e 5건 | 3 s | PASS. P10b가 df23_inventory · 엔진을 바꾸지 않아 6번이 그대로 성립한다 |
| E5 | 9 passed / 1014 deselected, 9건 모두 contracts(test_d_delete_dead 1, test_d_delete_telescopic 8). 덮음: (ii) 7, (iii) 2, (i) 0 | 118 s | PASS. (i) 빈 부분은 절차 메모 대상 |
| **E4(a) PT2** | exit 0, **1008 passed, 15 xfailed**, XPASS 0 | 438 s(pytest 408 s) | PASS. 1008 = 871 + **137(P10b `test_reg_check_df23.py`)** -- 예상대로 들어갔다. md 일치 card test가 들어오면 그만큼 더 는다 |
| **E4(a) PT2 --gmid-dod** | exit 0, **1008 passed, 15 xfailed** | 443 s(pytest 415 s) | PASS. 두 실행의 xfailed 15가 같다 → 관찰 3 성립 |
| E4(b) 사본 | sha256: e_lib `045f65c8…`, df35 `575fcb32…`, df36 `aa76989e…`. blob: `00fbb20f…`, `67df1684…`, `ef43c49f…`(드라이런과 같음) | <1 s | 정상 |
| E1 판별력 @7535799 | kcl_edges **0**, w_calc 106 | 100 s(캐시 포함) | 기대대로 |
| E3 판별력 @766b5c2 | FAIL(기대대로): 2 by_phase 불일치, 3 phase 0/590, 4 빈 function 414, `measured_at` 없음. 5 DF-29 42 | 1 s | 기대대로 |
| **E4(c) da03c0e** | E-LIB 9/9, 모두 ok · exc 없음, hash `1d2e3bf6acf762ebea14aa526405bfe63db9632cfab68672b93948c2be3b7a8f`. E-INST(df35 base): 두 회로 모두 `literal_counts_before` [2,1], `topology_ref_is_join_of_ASSETS_DIR` true, `fail_in_stdout` false, `engine_origin` · `instance_path`가 `C:\g145\dod\iso` 아래 | 5 s / crt 462 s / fc 65 s | 정상 |
| **E4(d) H'** | E-LIB 9/9, hash **`1d2e3bf6…7a8f` = da03c0e**. crt `without_topology_ref_sha256` **`185b675e9dd363a535d2942c651cddee4cb1a0ee98b703f0c7abef99f50e51ca` = da03c0e**, fc **`0ca6746f1cb3d364f26f5ec6b37e931c7fbc3488b610b4e57f377a6067cda754` = da03c0e**. 두 회로 모두 `topology_ref_equals_expected_contract1` true, `path_string_hits` [] | 5 s / crt 465 s / fc 59 s | **PASS**(승인 20260930-phase2-e4-baseline 기준 (a)(b)(c) 모두 성립. 값은 0f23786 드라이런과 같다) |
| 메인 쓰기 감시 | 모래상자 '메인'(`/c/g145/r`)은 매 검사에서 status가 같고, stamp 이후 파일 0(지정 경로 · 루트). 실제 메인 저장소 status도 실행 전후 같다 | -- | 공식 실행에서는 그 시점 다른 agent의 cwd를 확인해야 한다(브리핑 §0) |
| 복제본 끝 상태 | reflog: clone → H → 7535799 → da03c0e → H. status는 E4(d) 산출 3줄(instance.json 2 M + report.html 1 ??) | -- | 브리핑이 말한 "정상" 모양 |

## 3. N6.3(H')

| # | 결과 | 공식 실행 예측 |
|---|---|---|
| 1 기록 전수 | 33건. 32건은 V1~V10이 모두 PASS 또는 N/A. **P10b 1건은 합성 자리표시라 checks가 없다** | 실제 P10b 기록(V 모두 PASS/N/A)과 md 일치 기록이 들어오면 34건. 모래상자 한정 FAIL이다 |
| 2 Phase 2 card | `phase: 2` card 18장. 기록이 있는 것 16, 없는 것 2: P3(c)(정상) + **`20261001-topology-md-sync`**. 기대 밖 card 0 | md 일치 판정 기록이 없으면 **공식 FAIL**("기록 없는 card는 P3(c) 하나"). 가드 (4)가 먼저 멈추므로 실제로는 INVALID(착수 불가)로 나온다 |
| 3 merge gate 형식 | 16행 모두 성립. 판정 기록 커밋이 Role: audit · Change-Id를 갖고, 비 test-only 12건(P10b 포함 -- `merge 20260930-df23-registry-record` = `54ef51c`)의 병합 커밋이 H의 조상, test-only 4건은 병합 없음 · code null | P10b 행은 실제 기록의 base/test/code 조상 여부를 다시 봐야 한다(합성 기록에는 값이 없어 공허하게 참이다) |
| 4 카드 밖 엔진 변경 | **30커밋**, 모두 Role code/test + 목록 안 Change-Id. P2 4, P1 · P3a · P3b · P10 1, P10b 2, 나머지 2 | md 일치 test 커밋(`tests/contracts/test_topology_md_sync.py`, pathspec `assets/*.py`에 맞음)이 들어오면 **31**(브리핑 기대와 같음). 문서 커밋 c1 · D · E2는 목록에 나오지 않았다 |
| 5 증거 | red-green 7건(P4 · P6 · P7 · P8 · restore · DF-35 · DF-36)은 `red.test_ids` · `failure_hashes`가 있고 V2 PASS. P10b는 합성이라 확인 불가. equivalence 4건(P2 · P5 · P5b · P9)은 V2 PASS이고 basis에 base = 병합본 문장이 있다(P5 "기존 test 집합 양쪽 PASS: base 382건 … 병합본에서 같은 382 id가 실패 0", P5b "기존 test 양쪽 PASS: base 433건 … 430 id가 병합본에서 실패 0", P2 · P9는 커밋 모양 · 재사용 근거 문장) | P10b 실제 기록의 red 필드를 확인해야 한다 |
| 0.5 card | v3-history-clone · rejudge-cache 모두 V1 · V10 PASS, 나머지 N/A | 같음 |

## 4. 남긴 관찰(§7)

1. D2: `probe_physical_consistency.py`를 `probes/` 아래로 복사해 스캔 → 1건 `rail-set` 40행, exit 1. 절대 경로 리터럴은 33행 `ASSETS`, 38행 `INST`.
2. E5 노드는 모두 contracts에 있다.
3. `gmid_ic(...phase="2")` 0건, xfailed 15 = 15.
4. 추적 instance.json 두 개의 `topology_ref`가 메인 절대 경로다(DF-36 이전 형식).

## 5. 공식 실행에서 FAIL 또는 INVALID가 될 것(예측)

1. **[차단 -- 착수 조건]** md 일치 card `20261001-topology-md-sync` 판정 기록이 gate에 없으면 가드 (4)에서 멈춘다(INVALID). 끄고 돌리면 N6.3-2에서 FAIL이다. runbook §6(test → audit → 정리)을 DoD 전에 끝내야 한다.
2. **[해소 -- 실행 중 확인]** 측정하는 동안 실제 P10b 판정 기록 `afcf36c`가 gate에 들어왔다(메인 reflog 22:20 ff). 끝에 읽기만 해서 확인한 내용: 제목이 `audit: 20260930-df23-registry-record`로 시작하고(가드 (1) 형식 충족), trailer `Role: audit` · `Change-Id: 20260930-df23-registry-record`, red-green, V1~V7 · V10 PASS · V8 · V9 N/A, base `0f23786` · test `572d767` · code `b7b1e00`가 모두 afcf36c의 조상, `red.test_ids` · `failure_hashes` 각 1개. 기록 제목의 "1008 passed · 15 xfailed"도 이번 PT2와 같다. 따라서 N6.3-1 · 3 · 5의 P10b 행은 PASS로 예측한다(34건 = 32 + P10b + md 일치).
3. 그 밖에 E0 · E1 · **E2(새 문구 PASS, 면제 1건 = 승인 20260929-p4-scan-exempt)** · E3 · **E4(PT2 · PT2 --gmid-dod 모두 1008 passed/15 xfailed, P10b 137개 포함; E-LIB · E-INST 값 모두 da03c0e와 같음)** · E5 · 판별력 3건 · 관찰 4건은 H'에서 모두 기대대로 성립했다. md 일치 test 커밋이 더해지면 PT2 수와 N6.3-4 커밋 수(31)만 바뀌고, 그 test가 엔진 · library json을 바꾸지 않으면 E-LIB · E-INST 해시는 그대로일 것으로 예측한다.
4. 공식 실행 시간 추정(이번 실측, 다른 agent 부하 있음): 가드 + 복제 약 1분, E1 + E5 약 4분, PT2 7.3분, PT2 dod 7.4분, E1 판별력 1.7분, E4(c) 8.9분, E4(d) 8.8분. **직렬 벽시계 약 40분**(드라이런 55분보다 짧다).

## 6. 절차 메모

- runbook과 가드를 모래상자 경로로만 바꿔 실행했다. 가드 스크립트는 브리핑 §2 코드를 그대로 쓰고 R · G · OUTF만 바꿨으며 (4)는 보고만 하도록 했다. 결과 파일은 이 문서 하나다(`phase2_dod_result.md`는 쓰지 않았다).
- 측정 스크립트는 드라이런 `_drafts/p2dod_dryrun/`의 `e3_check.py`를 그대로 썼다. `n63_check.py`는 v4에 맞게 사본을 고쳐 썼다: 기대 목록에 md 일치 card를 더해 17건으로 하고, checks가 없는 기록에도 멈추지 않게 했다. 공식 실행에서는 auditor가 자기 스크립트를 쓴다(브리핑 규정).
- E1 수집 총수가 886 → 1023으로 바뀌었다(+137 = P10b test). E1 · E5 판정에는 영향이 없다.
- `C:/g145`는 끝에 지웠다. 메인 저장소에는 쓰지 않았다(status 줄은 전후 같다). 다만 실행 중에 **오케스트레이터가** 메인을 옮겼다: `merge gate/master`(afcf36c, 22:20) 뒤 runbook 로컬 커밋 7개 `58024de`…`19eb475`(22:23~22:26)를 만들었고, 끝날 때 메인 HEAD는 `19eb475`, gate/master는 `afcf36c`(아직 push 전)였다. 실제 runbook 커밋 제목과 순서는 모래상자 H'와 같다. 실제 H는 sha만 다르고 같은 모양이 된다(md 일치 판정 기록이 더해지는 것만 다르다).
