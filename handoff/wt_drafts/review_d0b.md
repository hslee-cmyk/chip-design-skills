# D0b spec card 초안 독립 검토 -- `20260930-p3-registry-dest`

검토 2026-10-02, 독립 검토자(작성자 아님). 대상: `_drafts/draft_p3_d0b.spec.md`, `_drafts/d0b_briefs.md`, `_drafts/p3kit_d0b/`.
기준: design 30 `_drafts/draft_phase3_design_v8.md`(디스크 현재판 = **v8.4** 머리), 계획 N3.10(519~531행)·N3.12.3(675~685행)·N4.2 V2(838행),
`docs/02-design/specs/_TEMPLATE.spec.md` '작성 전 실측' 1~13, 승인 `20260923-u02-d-list`, 선례 판정 기록(V4).

재측정: 격리 복제본 `C:/g169/r`(`git clone --no-local`, origin 제거, 빈 hooksPath), gate `master` = `dd60db6`(`git -C <repo> rev-parse gate/master`).
키트와 같은 sha256 시제품(G1 `install_proto.py` 5790433c…·`g1_core.py` b3c4e391…, D0a `move_plan_proto.py` d2f3da97…)을 복제본에만 설치.
작업 끝에 `/c/g169` 삭제, 실제 저장소 `status`·`HEAD`·reflog가 시작 때와 같음을 확인. (절차 기록: 처음 clone 한 번이 MSYS 경로 변환 때문에 `C:/c/g169`에 생겼다 --
내가 만든 그 폴더만 바로 지우고 `C:/g169`로 다시 떴다. 다른 `/c/g*`는 건드리지 않았다.)

## 판정: **고친 뒤 재검토**(B 2 · S 5 · minor 5)

핵심 수치는 전부 재현된다. 그러나 (B1) oracle (d)-1 표의 두 행은 레지스트리에 행이 없어 만족할 수 없고, (B2) 초안이 design v8.4(FU card, `import_conflicts`)보다 앞선 판에 맞춰져 있다.
red 모양(S1)은 V2를 형식적으로는 통과시키지만 일부 test에서 red 증거를 비게 만든다.

---

## 1. 재측정 결과(주장별)

| 주장(spec/briefs) | 재측정(`dd60db6` + G1 시제품 + UD-0 N3.10 개정 (ga)) | 판정 |
|---|---|---|
| `upward` 34 · `cycles` 1(MOD 9개 SCC) · `unassigned` 18 · `conflicts` 0 · `reg_mismatch` 36 · `import_time_high` [] · MOD7 밖 0 · 배정 390 | 같은 값. 규칙 분포 A-4 234·A-5 63·A-1 55·A-2 37·A-3 1. 개정 없는 트리 `upward` 46·`reg_mismatch` 38. `analyze_plan` 요약(lens·rules·per_mod·upward_mod_pairs)이 키트 `out/an_amend.json`과 같다 | 재현 |
| `upward` 규칙 쌍 A-4→A-1 17, A-4→A-4 12, A-1→A-4 3, A-1→A-1 2 | 같음 | 재현 |
| A-1↔A-1 모순 `sizing_recipe.py:8060`·`:7683` | `:8060` `    stack_groups_geometry = resolve_stack_layout(`(`def _build_theta_evaluator` 7930행 안 -- N3.10 MOD6 토큰 → MOD8 토큰). `:7683` `        f"지금 넘긴 spec의 지문: {spec_fingerprint(spec)}")`(`def require_declared_spec_source` 7617행 안 -- MOD2 토큰 → MOD3 토큰; 거부 경로 f-string 안의 호출이지만 참조다). A-1→A-4의 `:5272` `metric_unit_scale(spec, name)`, `:399` `return _multilinear_interp_point_multi(...)`도 확인 | 재현(원문 일치) |
| A-4 승격 → `upward` 34 → 7 | 승격만 7(배정 42개 바뀜), A-K+A-6+승격 7(47개, 새 단위 12). `cycles`는 둘 다 1 그대로 | 재현 -- 단 S2 |
| D0a 빈칸 규칙(A-K, A-6) → `unassigned` 18 → 15 → 6 | 같음. 남는 6 = docstring 3(SR·SD·DR) + `signal_path_nodes` + `MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity` | 재현 |
| 재생성 멱등·`reg_mismatch` 36 → 0 | `regen_registry.py --write` + `보류(Phase 3)`→`(Phase 4)` 치환 커밋에서 `reg_mismatch` 0, (키 → `mod`) 사상 차이 0·키 차이 0, `rule` A-4 238·A-5 60·A-3 0. diff 409+/409− | 재현 |
| `reg_check` 0, 소비자 test 210 passed | 위 커밋(보류 치환 포함 -- 키트 `sim_regen.sh`는 치환을 안 했다)에서 `reg_check: 발견 0` exit 0, `test_reg_check.py`·`test_reg_check_df23.py`·`test_df23_inventory.py` 210 passed(`--gmid-phase=3 --gmid-strict=`). `보류(Phase 3)` 9 → 0, `보류(Phase 4)` 14 → 23 | 재현 |
| test 모양 시제품 base 5 failed·2 passed | base 5 failed·2 passed(통과 = `import_time_high`·MOD7), 재생성 커밋 2 failed·5 passed(`plan` exit·`upward`/`cycles`) | 재현 |
| `_metric_*` 26개 중 24개 A-4 → MOD4 | 26개 모두 A-4(MOD4 24·MOD3 1·MOD9 1) | 재현 |
| `plan` 1회 12~19초 | 14~18초 | 재현 |

---

## 2. B(차단)

### B1. oracle (d)-1 표의 `RailDeclaration`·`rail_declaration` 두 행은 만족할 수 없다

spec oracle (d)-1: "test는 아래 표의 각 행이 **대상 행**이고 `이관 목적지` 칸이 기대 줄기와 같으며, 같은 단위의 `plan` `mod`도 같은지 단언한다". 대상 행 = 레지스트리 함수 표 안의 행이다(계약 6 (b)).
그런데 B26-1 초안 계약 11(`_drafts/draft_b26_1.spec.md` 183행)은 레지스트리 §2(개념 정본 표 -- 머리 `개념 | 정본(제안) | 중복 | 상태`, `이관 목적지` 열 없음)와 §6 문장만 고친다.
design §6.4 표도 "레지스트리에 행이 없는 최상위 정의 SD 24 → SD 26 … 함수 행 추가 없음"이라고 적는다. 그러면 D0b base에 두 단위의 함수 표 행이 없고, D0b 계약 1·'무동작 판정 입력'은
"바뀌는 것 = 대상 행 칸·`근거 규칙` 열·보류 9칸뿐"이라 code-author가 행을 더할 수도 없다. test-author가 표대로 쓰면 병합본에서도 FAIL하고, code-author는 dispute로 멈춘다.
**고칠 것**(하나를 고른다): (a) 레지스트리 행이 없는 표본은 `plan` `mod`만 단언(대상 행 단언 제외)한다고 표에 적는다 -- 이것이 가장 작다. (b) D0b code 커밋이 '도구 출력에 있고 행이 없는 새 정의'의 행을 더하게
계약 1·6·무동작 절을 넓힌다(칸 = 도구 출력이라 손으로 쓰는 값은 아니지만 책임 칸은 손 문장이 된다).

### B2. design v8.4와 어긋남 -- FU card와 `import_conflicts`가 빠졌다

design 디스크판 v8.4 §8 D0b 행: "**v8.4: `import_conflicts` 0 단언**(plan exit 0에 포함 -- `__future__` 기능 집합 갈림이 남으면 FAIL, §6.5)", base = "B34·B26-1·B33·G1·**FU**·D0a 병합 뒤 master",
§8.1 의존 표 "FU(v8.4) → D0b". D0a 초안도 v8.4로 exit 1 사유에 `import_conflicts`를 더했다(`draft_p3_d0a.spec.md` 94행, 9 (i) "D0b … exit 0 단언에는 `import_conflicts`가 들어간다").
D0b 초안은 'design v8.3' 기준이라:
* 의도·계약 3·계약 8·S-6·test 브리프 4번이 판정 목록을 "여섯"(`upward`·`cycles`·`unassigned`·`conflicts`·`reg_mismatch`·`import_time_high`)으로 닫고 `import_conflicts`가 없다. 멈춤 경로(계약 8)에도 `import_conflicts` → FU 확인/배정 변경 경로가 없다.
* base 사슬(의도 16행, S-2, 0.4)에 FU가 없다.
* '작성 전 실측'은 `import_conflicts`가 없는 D0a 시제품(d2f3da97 -- `grep -c import_conflicts` 0)으로 쟀다. 재측정 배정에서 MOD별 출처 파일을 보면 `topology_authoring`(SR·SD·**ACF**)·`gmid_sizing_engine`(SR·TL·**DR**)·`instance_report_builder`(SR·SD·**DR·ACF**) 세 MOD가 future 있는 파일(SR·SD·TL)과 없는 파일(DR·ACF)의 단위를 함께 받는다 -- FU 없이 v8.4 도구를 돌리면 `import_conflicts`가 적어도 3 MOD에서 비지 않는다(관찰). 즉 '지금 실측' 표의 "판정 목록" 줄이 하나 모자란다.
**고칠 것**: 목록을 일곱으로(계약 3·8·S-6·브리프·재현 수치에 `import_conflicts`), base 사슬에 FU, 계약 8에 '(e) `import_conflicts` 비지 않음 → FU 병합 확인, 아니면 배정 변경(D-11)'. `mod_imports`는 판정하지 않는다고 한 줄(M card 몫).

---

## 3. S(중요)

### S1. red 모양: "모든 test가 먼저 `근거 규칙` 열 머리를 단언" -- red가 형식적으로만 성립한다(약화 성격)

계획 838행 V2는 "새·바뀐 test가 base에서 assertion FAIL"을 요구한다. 계약 11 (a)의 머리 단언은 그 요구를 **모든 test에 같은 한 조건으로** 채운다. 결과:
* `import_time_high`·MOD7·`upward`/`cycles`/`unassigned`/`conflicts` test는 실제 D0b base에서 **정의상 참**이다(S-6이 그것을 착수 조건으로 요구한다). 이 test들의 base red는 머리 단언 하나에서 나오고, 그 test 고유 단언이 무엇을 잡는지는 V2가 전혀 보이지 않는다.
* 고유 단언이 base에서 진짜 FAIL하는 test(칸 = 배정 줄기, (d)-1, `보류(Phase 3)` 0, `reg_mismatch`)도 머리 단언에서 먼저 멈춘다. 브리프 3.1이 "모든 test FAIL, 원인 = `근거 규칙` 열 머리 단언"을 red 판정으로 적어 두었으므로 auditor의 `failure_hashes`가 이 test들의 실제 단언을 한 번도 base에서 기록하지 않는다.
* 이것은 게이트 규칙을 어기지는 않지만 "red = test가 결함을 잡는다"의 내용을 비운다(메모리 원칙 '게이트는 실제로 거부한다를 먼저 확인'). 보완 장치인 V10 ⑥('거부해야 할 입력'을 병합본 사본에 하나씩 적용)는 입력별이지 test별이 아니고, 몇 입력(엔진 기본값 인자 조작, MOD7 토큰)은 만드는 법이 적혀 있지 않다.
**고칠 것**(기본안): (1) 머리 단언은 열 모양 test에만 둔다. (2) base에서 참인 단언은 혼자 test가 되지 않게 **한 test로 묶는다** -- `plan` 판정 test 하나가 exit·일곱 목록·MOD7을 차례로 단언(base에서 `reg_mismatch`로 진짜 FAIL). (3) V10 ⑥을 'test 함수마다 그 test 고유 단언으로 FAIL하는 거부 입력 ≥ 1'로 바꾸고 입력별 만드는 법(어느 파일 어느 줄을 어떻게)을 spec에 적는다. 이렇게 하면 V2 red가 각 test의 실제 단언에서 나온다.

### S2. 기본안 'A-4 승격'은 N3.10 책임 문장을 조용히 어긴다

재측정에서 승격(V_LIFT)은 `propose_device_roles_gap_fill`·`check_symmetry_dispositions`·`SymmetryDispositionsVerdict`(레지스트리 목적지 `topology_authoring` -- N3.10 MOD2 '구조 제안')를 **MOD7 `stick_diagram`**으로 올린다.
N3.10 MOD7 책임은 "레이아웃만(구조 유도 함수는 MOD2·MOD3로 나간다)"이다. 계약 5(MOD7 밖 단위의 MOD7 배정 0)는 이 셋이 SD 단위라 잡지 못한다. 그 밖에 SD 3단위 MOD7→MOD8, MOD4→MOD5 11, MOD2→MOD3 12 등 42개가 바뀐다.
spec D0b-1은 "승격이 새로 만든 1건(`load_topology` → `propose_device_roles_gap_fill` MOD7)"을 upward로만 적고 책임 위반은 적지 않는다. 또 승격은 계획 517행 "함수별 목적지는 레지스트리의 '이관 목적지' 열이 정본"을 '열 = 하한'으로 바꾸는 규칙이다 -- 사용자 승인 질문에 이 두 효과(정본 의미 변경, MOD7로 올라가는 구조 제안 함수 목록)를 원문으로 넣어야 한다.
참고(대안 탐색, 관찰): N3.10 MOD5에 글롭 토큰 `` `_metric_*` ``를 더해 A-1로 26개를 MOD5에 보내는 모의는 `upward` 34 그대로(다른 MOD4 함수가 `_metric_*`를 부른다), 승격과 합치면 6이었다 -- 글롭 하나로 (iii)을 닫을 수는 없다.

### S3. 계약 6 (c) `근거 규칙` 형식 `A-0`~`A-5`가 spec 자신의 기본안(A-K·A-6)과 모순

D0b-2 기본안은 D0a에 규칙 A-K와 A-6을 더한다. 그대로 채택되면 재생성 열에 `A-K`·`A-6`이 쓰이고 계약 6 (c) test가 병합본에서 FAIL한다. 형식 집합을 'D0a 계약 2가 정의한 규칙 ID 집합'으로(이름 열거 대신 정의 참조 -- '정의 하나') 바꾸거나 D0b-2 결정 뒤 고정한다. 거부 입력 `A-9`도 그 집합 밖 값으로.

### S4. design 문구와의 어긋남을 'design 개정'이 아니라 card 결정으로 처리 -- v8.4 안에서 닫을 것

design §8 D0b 행은 (i) "레지스트리 목적지 열 **전 행** = MOD 이름 하나", (ii) oracle "규칙 손적용 **합성 입력**"을 적는다. spec은 D0b-3(비대상 행 칸 불변)·D0b-4(합성 입력 → 실제 단위 표본, D0a test로)·D0b-5(`근거 규칙` 열 뜻)로 바꾼다.
(ii)는 '사실 정정'이 아니라 oracle 종류 변경이다. design이 지금 v8.4로 고쳐지는 중이고 아직 승인 전이므로, 이 셋을 v8.4 본문(§8 D0b 행)에 넣어 UD-0 승인 범위로 닫는 것이 맞다(card가 승인될 design과 다른 기준을 갖지 않게). 이유 문장(합성 입력 test는 D0a 병합 뒤 base에서도 통과 → V2 red 불가)은 타당하다.

### S5. (d)-1 표본이 사실상 A-1만 덮는다 -- 동어반복 방지 몫이 가장 위험한 규칙에 없다

11행 중 9행이 A-1(N3.10 토큰), 1행 A-2, 1행 A-1/A-5. 기대값 출처는 문서(N3.10·개정 문안)라 도구와 **독립**인 것은 맞다(선택 기준만 도구 출력을 봤다). 그러나 배정 390 중 A-4 234·A-5 63(76%)이 손적용 표본 0이다.
spec 자신이 찾은 `〃` 번짐 결함(§3 '기타 모듈' 표 `save_html_report` 〃 → 다른 파일 행의 `gmid_sizing_engine`)이 바로 '도구와 열이 함께 틀리는' 종류인데 표본에 없다. 규칙마다 손적용 행을 하나 이상 더할 것을 권한다:
A-4 일반 칸 1, A-4 별칭(`optimizer` → `theta_search`, N3.10 토큰 아닌 행) 1, A-4 `〃` 1(번짐 결함을 고치기로 하면 그 기대값), A-5 1(행 없는 상수·레지스트리 dict), A-3 1(두 MOD 셀 -- 지금 A-3 배정은 1개뿐).
또 표 위 문장 "계층 충돌(`upward`)에 걸리지 않은 단위만 골랐다"는 사실과 다르다 -- 재측정에서 `compute_metric`(`_make_shared_current_scorer`·`_refine_shared_current_joint_scan…`이 부름), `optimize_full_circuit_budget`(`achievable_metric_bound`), `render_html_report`(`save_html_report`)가 upward 간선의 **대상**이다(원천이 A-4라 승격이면 표본은 그대로지만, 해소가 대상을 내리면 바뀐다). "원천으로 걸리지 않은"으로 고치고 해소 뒤 재확인을 적는다.

---

## 4. minor

* m1. V4 선례: `20260922-sections-major-merge`는 그 card가 **고친** 도구를 `--module-dir . --subject tools.migrate.extract_selftest:main`으로 줬다. D0b는 바꾸지 않는 도구를 subject로 준다 -- 더 가까운 선례는 `20260922-ts7-ic-xfail`(card가 바꾸지 않는 `merge_gate`를 `--module-dir tools/gates --subject …`)·`20260923-v4-decision-exempt`다. 선례 인용을 바꾸고 'interface card 두 표가 빈 DESIGN-GAP 우회'라고 명시. 측정(키트 `out/vt/v_test_lint_subject.json`: PASS, 7개 모두 NO-SUBJECT)은 맞다. V4가 실질을 갖는 곳은 basis의 oracle 대조 문장뿐임을 브리프 3.2에 적을 것.
* m2. 계약 11 (b)는 도구를 `--rev HEAD`(커밋 객체)로 돌리고 레지스트리는 작업 트리 파일로 읽는다. 작업 트리가 HEAD와 다르면(code-author 자기 확인 중 미커밋 편집) 두 입력이 갈린다. 'test는 깨끗한 체크아웃에서만 의미가 있다' 한 줄, 또는 레지스트리도 `git show HEAD:`로 읽게.
* m3. `§7 보류(Phase 3)` → `보류(Phase 4)`(계약 7, D-10)는 **새 기준 변경이 아니라고 본다**: U-02 승인 1항 "보류(Phase 3 모듈 이동·Phase 4 배선)"과 design 20 18행 "보류(배선은 Phase 4, 모듈 이동은 Phase 3)"이 이미 두 몫을 승인했고, 보류 **집합**은 그대로(design 20 REG 판정식 = 보류 집합 일치, `reg_check` 0 확인)이며, D-10은 UD-0이 덮는 D 목록에 있다. 다만 U-02 '재검토'는 "승인표를 바꾸는 것은 사용자 승인 사항"이라고 적고, 승인 질문 문안(`phase3_approval_question.md` 88행)은 D-10을 '코드 배치·판정 절차'로만 묶는다 -- UD-0 문장에 "U-02 승인표의 처리 칸 9개를 Phase 3 → Phase 4로(이동 몫은 이관 목적지 열이 넘겨받음)" 한 줄을 넣으면 승인 범위가 원문으로 드러난다. 그리고 D0b 병합 시점에는 아직 옮기지 않았으므로, 'Phase 3 이동 의무는 열 + `plan`/`check`가 진다'는 문장을 계약 7에 둘 것.
* m4. 키트 `run_plan.sh`·`sim_regen.sh`·`run_proto_test.sh`·`sim_chain_vtools.sh`가 `C:/g162/*` 경로 가드와 `C:/g162/tmp/move_plan_proto.py` 기본값을 박아 둬서 브리프 '착수 0단계'("인자로 받으므로 실제 파일 경로를 넘긴다")대로 재사용할 수 없다(이번 재측정도 명령을 풀어 썼다). 스크래치 루트를 인자로.
* m5. 키트 `sim_regen.sh`는 `보류` 치환 없이 재생성만 해서 실측 6의 '210 passed·`reg_check` 0'이 계약 7을 함께 적용한 트리의 값이 아니다. 이번 재측정에서 치환까지 한 트리에서도 같은 값이 나왔으므로 사실 문장에 '보류 치환 포함 트리에서도'를 더하면 된다.

---

## 5. 질문별 답(요청 항목)

1. **재측정 핵심 수치**: 34 / 1 / 18, A-1↔A-1 두 곳(`:8060`·`:7683` 원문 위 인용), 승격 34 → 7, 빈칸 규칙 18 → 6, 재생성 멱등(사상 차이 0)·`reg_check` 0 -- **모두 재현**. 단 이 측정은 `import_conflicts` 없는 시제품이라 판정 목록 하나가 빠진 값이다(B2).
2. **red 모양이 약화인가**: 게이트 규칙 위반은 아니지만 **red 증거를 비우는 모양**이다(S1). base에서 참인 단언을 혼자 test로 두지 말고 진짜 red 단언과 묶고, V10 ⑥을 test별 거부 입력으로 바꾸면 해소.
3. **oracle 11행 독립성**: 값의 출처(N3.10·개정 문안·D-19 답)는 도구와 독립이다. 그러나 2행은 레지스트리 행이 없어 성립 불가(B1), 나머지는 A-1 편중이라 동어반복 위험이 큰 A-4/A-5/`〃`를 못 덮는다(S5).
4. **V4 `--subject move_plan:main`**: 방식은 선례가 많다(ts7·v4-decision-exempt 등) -- 인용 선례만 고칠 것(m1).
5. **`보류(Phase 3)` 9 → `보류(Phase 4)`가 기준 변경인가**: 따로 승인할 기준 변경은 아니다(U-02 1항·design 20이 두 몫을 이미 승인, 집합 불변, D-10 ∈ UD-0). UD-0 문장에 원문 한 줄로 드러내는 것만 권한다(m3).
