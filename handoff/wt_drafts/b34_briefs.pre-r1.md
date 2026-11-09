# B34 card `20260930-b34-grammar-explicit` -- 착수 키트(세 역할 브리프 + 착수 확인)

작성 2026-10-01. 기준: gate `master` **`0f23786`**(P10b spec card 재시도 개정). 저장소 쓰기·상태 변경 git 없음(작업 전후 `git status --short` 36줄 동일). 모의는 격리 복제본 `C:/g123`(origin 제거, 빈 hooksPath, 끝나고 삭제)에서만.
대상 산출물: `draft_b34.final.spec.md`(재검증 반영판, 직전판 `.spec.v1.md`), `b34_commit_plan.md`(v2, 직전판 `.v1.md`), 스크립트·출력 `b34_kit/`.

**착수 0단계(반드시, 다른 단계 전에 -- 읽기 전용)**: 착수 시 gate `master`가 `0f23786`이 아니면 다음을 다시 돌리고 출력으로 판단한다.
```
git -C <R> diff --stat 0f23786 gate/master -- skills/analog-gmid-design/assets/stick_diagram.py skills/analog-gmid-design/assets/sizing_recipe.py install.py skills/analog-gmid-design/references/analog-grammar-integration.md tools/gates/
git -C <R> show gate/master:tools/gates/mutate_changed.py | grep -c not_targeted
```
판단: (가) 첫 명령에서 `tools/gates/`만 바뀌었으면(V3 card 34·35 병합 -- 예정된 변화) card 줄 번호 그대로, `b34_kit/measure_b34.py`·`probe_selection.py`로 V3 대상만 다시 잰다(범위 card 병합본이면 대상 10·`not_targeted` 45 기대).
(나) SD·SR·references가 바뀌었으면 `b34_kit/mk_head.py`의 base를 그 판으로 바꿔 `dump_lines.py`·`measure_b34.py`를 다시 돌리고 card '작성 전 실측' 00과 이 문서 0.1 표를 고친다. (다) 둘째 명령 ≥ 1이면 N2 규칙(V3 대상 10), 0이면 현행 규칙(55).

---

## 0. 착수 확인 결과(오케스트레이터용)

### 0.1 spec card 재검증(gate `master` `0f23786`)

| 확인 | 결과 | 조치 |
|---|---|---|
| `2d58fd8..0f23786` 차이 | SD·SR·`install.py`·references 문서·`tools/`·`test_selftest_stick_diagram.py` 0. 바뀐 것은 승인 기록 `20261001-p10b-v3-equiv`, P10 판정 기록, 계획·history, P10b spec·interface, `test_df23_inventory.py`·`test_phase2_stale_refs.py`. SD blob `ca46b5cd` 세 커밋 동일 | card 머리 문단에 'measured at `0f23786`' 한 줄 |
| SD 줄 인용 전부(사이트 1·2·3·11·11b, 인계 4~14·3955~3959, 남기는 것 14곳, docstring 17곳, 호출부 12곳, 3373·3381·3391, def 위치 3330·3834·8539) | 전부 같다(`b34_kit/out/sd_lines.txt`) | -- |
| SR 7952 `require_device_roles_reviewed` 호출 | 같다 | -- |
| SR `resolve_stack_layout` docstring '4번' | **6510~6512**(6509는 3번 끝 줄) | card 80행 6509~6512 → 6510~6512 |
| `install.py` 27~29 `SKILLS` | `analog-gmid-design` 있음, `analog-grammar` 없음 | -- |
| references 문서 폴백 줄 | 실제 부재 서술 = **95~98·106~107·118~119·186~188·197~198·440~443**. 옛 인용의 111·202는 `if not devs: return None`(gate 소자 없음 -- 남길 줄), 120~121은 빈 줄·절 머리 | card '작성 전 실측' 7 줄 범위 정정 + 패치 초안 `b34_kit/patch_b34_refs.py` |
| `test_selftest_stick_diagram.py` 2714~2717, 레지스트리 360, P9 spec 58·interface 60, `diff_dup.py` 17~20 | 같다 | -- |
| `_import_analog_grammar` 호출부 | SD 12곳 그대로. 다른 analog-grammar sys.path 주입: 엔진·test·workspaces 0(`.ai/verification/…/diff_dup.py`·`make_record.py` 설명 문자열만) | -- |
| `unavailable_reason` 읽는 코드 | 0(SD docstring 3516·3922만) | -- |
| 부재를 흉내 내는 기존 test | 0(`sys.modules`+`netclass`/`idioms` grep 0). `test_selftest_stick_diagram` Test 30·33·35~40 계열은 '있음' 전제 `is not None` -- 계약 7 방향 | -- |
| 새 이름 충돌 | `tests/contracts`에 `b34`·`grammar` 파일 0, `_b34_`·`test_b34_` 0 | -- |
| ts6 이력 의존 test 2개 | `test_ts6_probe_relocate.py` 652·668행 그대로 | -- |
| 승인 원소 | `_approved_ids` 36개(`2d58fd8` 27 + `20261001-p10b-v3-equiv` 9), 이 card 변이 id와 겹침 0 | card 'V3 계획'에 measured 문장 |
| B26-1 인계 | `draft_b26_1.spec.md` 52행 "사이트 10·14(B35)" -- 이 card 표와 같다 | -- |
| **V4 도구와 test 모양(새 발견)** | `test_lint.py` 실측: 계약 8을 지역 변수 `before`/`after` 직접 호출로 비교하면 (1) FAIL, 계약 1~3의 권고 `try` 모양에서 `assert`를 `except` 절 안에만 두면 (3) FAIL -- 어느 쪽이든 V4 FAIL → merge gate 거부. helper 모양·`pytest.raises` 모양은 PASS | **결정 0.6-6으로 대체**: 계약 8 = 새 프로세스 oracle, 계약 1~3 = `pytest.raises`(helper 모양 금지). 프로토타입 V4 PASS·red 27/27 `DID NOT RAISE`·변이 kill 동일(`b34_kit/proto_066/`) -- card 'test 모양' 끝 문단·계약 8·oracle·'작성 전 실측' 000, test-author 1.1~1.4 |

### 0.2 Q-B34-PHASE -- `phase` 값이 2냐 3이냐로 B34에서 바뀌는 것(정하지 않는다)

**게이트가 card `phase`를 쓰는 곳(`0f23786` `tools/gates/merge_gate.py` 실측)** -- 어디에서도 '지금 진행 중인 Phase'와 대조하지 않는다.

| 위치 | 하는 일 | phase 2 | phase 3 |
|---|---|---|---|
| 532~549 `rule10_phase`(1193·1311 호출 -- `receive` 판정 기록 로드, `check-record`) | card phase가 계획 N6.1 `phase_order`에 있는지, `N/A` 판정이 그 V의 도입 Phase(N4.2)보다 앞인지, `N/A` basis가 `도입 <Phase>: ` 형식인지, V4 PASS basis의 `oracle 대조: ` 줄 | 통과. V1~V7(도입 1·2)은 N/A 불가 → PASS 필수, V8(도입 4)·V9(도입 6b) N/A 가능 | **같다**(V7 도입 2 < 3 → PASS 필수, V8·V9 N/A 가능, V10 도입 0.5 → PASS 필수). 모의: 병합된 phase 2 기록 `20260930-dup-w-calc`가 phase 2·3 둘 다 `rule10` 통과 |
| 1031~1052 `strict_set`(1042 `c["phase"] == card["phase"]`) | V1 엄격 집합 = 같은 phase로 병합된 card들의 `activated_ic_case` ∪ 이 card 것 | 판정 기록이 있는 phase 2 card 15장 전부 `activated_ic_case` 빈 목록 → 빈 집합 | phase 3 병합 card 0장 → 빈 집합. **같다**(`--gmid-strict=` 빈 값) |
| 1209~1213 → `v1_command_check` 1008~1012 | V1 명령에 `--gmid-phase=<card phase>`가 정확히 하나 | `--gmid-phase=2` | `--gmid-phase=3` -- **이 토큰만 다르다**(모의: phase 2 명령을 phase 3 card로 검사하면 "V1 `--gmid-phase=3`가 없다") |
| (`mutate_changed.py` `--gmid-phase`, conftest) | `gmid_ic` 표식 Phase와 비교해 xfail·엄격 | 저장소 `gmid_ic` 표식 Phase = 1(6)·4(2)·6a(4)·6b(4)·6c(7). 2·3 표식 0 | **같은 수집·xfail**(`test_phase2_stale_refs` 모의 `--gmid-phase=2`·`3` 둘 다 18 passed) |

`role_paths`는 `phase`를 머리 키로 읽기만 한다(`SPEC_KEYS_SINGLE`). **결론: 게이트 거부 위험은 어느 값에도 없고, 계약·oracle·V3 대상·V 활성 집합은 같다.** 갈리는 것은 기록 분류와 문서뿐이다.

| 항목 | (가) `phase: 3`, Phase 2 DoD 뒤·Phase 3 M card 전(질문 기본안) | (나) `phase: 2` 유지 + Phase 2 DoD **앞으로** 당김 | 지금 초안 그대로(`phase: 2`, DoD 뒤) -- 어느 답도 아님 |
|---|---|---|---|
| spec card 머리 | `phase: 3` + `approval:` 줄 하나 더(새 decision 기록) | 그대로 | 그대로 |
| 승인 기록 | 새 decision 기록(③ 'Phase 2 진행 중' → 'Phase 2 DoD 뒤·Phase 3 M card 전', B26-1·b26pre 함께). 옛 기록 불변 | 순서 결정 변경 기록(`user_decisions.md`), 승인 기록 ③ 문장과는 맞는다 | ③ 문장과 순서 결정이 계속 어긋남 |
| 판정 기록 분류 | Phase 3 기록 목록(`^phase: 3$`)에 든다 -- Phase 3 DoD N6.3 2번 표에 'A2 앞당김 red-green card'(B34·B26-1, b26pre test-only)로 따로 한 줄 필요(N6.1 Phase 3 판정 유형은 equivalence) | Phase 2 기록 목록에 든다 | Phase 2 기록인데 Phase 2 DoD(H = P10b 판정 기록 커밋) 뒤라 **어느 DoD에도 안 잡힌다** |
| Phase 2 DoD 브리프(`phase2_dod_brief.md` §6) | 변화 없음(16건·`phase: 2` card 17장 그대로) | 2번 16 → 17건(+B26-1 18, b26pre 19), 3번 병합 12 → 13(+B26-1 14), 4번 카드 밖 엔진 변경 기대 수 +2(B34 test·code)(+B26-1), 5번 red-green 8 → 9(+B26-1 10). E4는 `da03c0e` 대 B34 포함 판 -- analog-grammar 있음이라 E-LIB·E-INST 같음(계약 7) | 브리프 그대로지만 DoD 뒤에 `phase: 2` 기록이 늘어 'Phase 2 마지막 card 병합본' 정의가 어긋남 |
| Phase 3 착수 조건 적용 | design 30 v8 D-23은 phase 3 card 병합에 'Phase 2 DoD PASS'를 건다(순서상 자동 성립). **'design 30 사용자 승인(DEC-51)·U-03'까지 B34에 거는지는 문서에 없다** -- 새 decision 기록에 "A2 card는 design 30 승인·U-03을 기다리지 않는다"를 적지 않으면 B34가 Phase 3 승인 뒤로 밀릴 수 있다 | 해당 없음 | 해당 없음 |
| V3 규칙 | N2(34·35 뒤, 대상 10) | 34·35보다 **앞**이면 현행 규칙(대상 55) -- card는 두 규칙 모두 통과하게 설계(55/55) | N2 |
| auditor 명령 | `--gmid-phase=3`(V1·V3·red 수집 전부) | `--gmid-phase=2` | `--gmid-phase=2` |
| 브리프 수정 | 이 문서의 `<P>` = 3 | `<P>` = 2, 순서 문단 | -- |

(이 표는 `_drafts/phase3_approval_question.md` A2-③과 같은 사실 위에 B34 몫만 더한 것이다. 답을 받으면 Q-B34-PHASE와 A2-③을 함께 닫는다 -- 오케스트레이터 몫.)

### 0.3 사용자 선행 작업(`install.py`) -- **B34 착수 조건 아님**

* **사실**: `0f23786` `install.py` 27~29행 `SKILLS`에 `analog-grammar`가 없다. 사용자 전역 설치 `~/.claude/skills`에는 지금 `analog-gmid-design`·`analog-grammar` **둘 다 없다**(SKILLS에 있는 `analog-gmid-design`도 아직 설치되지 않음).
* **card가 그것을 어떻게 재나**: test는 저장소 트리(`skills/analog-grammar/assets` 있음)에서 돈다. '없음'은 `monkeypatch.setitem(sys.modules, "netclass"/"idioms", None)`로 흉내 낸다(계약 1~3·5·8). '있음 = 동작 불변'은 계약 7(auditor E-LIB 9/9·E-INST·14 진입점 × 9회로 base 대조)과 계약 8(복구)이 잰다.
  auditor 격리 복제본도 저장소 트리라 같다. 그래서 사용자 편집 없이 착수·판정·병합이 된다.
* **설치 모양 실측**(`b34_kit/install_probe.py`, `skills/<이름>`만 있는 디렉터리 -- `~/.claude/skills`와 같은 상대 위치 `../../analog-grammar/assets`):

| 판 | analog-grammar 없음 | 있음 |
|---|---|---|
| base `0f23786` | 9/9 예외 없이 반환, 그런데 meta 9/9가 '있음'과 다름(`_device_roles_gap_fill_review_needed` 0·28·4·5·12·1·1·9·2 → 전부 0) -- **조용히 틀림** | 9/9 |
| 모의 head(B34 코드) | 9/9 `ImportError`: `analog-grammar skill을 import할 수 없다(탐색 경로 …\skills\analog-grammar\assets)`, `__cause__` `ModuleNotFoundError` | 9/9, meta가 base와 9/9 같음 |

* **사용자가 할 일(시점 = B34 병합 뒤, 다음 `python install.py` 실행 전)**: ① 오케스트레이터가 승인 기록 `.ai/approvals/<id>.md`를 쓴다(`target_kind: staged_diff`, `target` = HEAD→staged install.py 변경의 `merge_gate.compute_diff_hash`, `diff_base: <HEAD>`, `diff_path: install.py`, 사용자 원문)
  ② 사용자가 `install.py` 29행을 `"solution-capture", "analog-gmid-design", "analog-grammar"]`로 고쳐 stage하고 승인 기록과 **한 커밋**으로 `git commit --trailer "Role: user"`(선례 `d72475a`) ③ gate push ④ `python install.py --only skills` → `~/.claude/skills/analog-grammar/assets/netclass.py` 확인.
  모의(`sim_b34.py`): 승인 기록 있으면 가짜 gate 통과, 없으면 `[EL4 거부] target_kind: staged_diff 승인 기록 필요(target = …) -- Role: user 커밋`.

### 0.4 V3 규모(`b34_kit/out/measure_b34.txt`, `probe_cur_all.txt`)

독립 모의 head(`mk_head.py` -- card 표에서 새로 작성, 메시지 = f-string 하나, 정수 상수 없음) = `0f23786` + 사이트 1·2·3·11·11b:

| def | 현행 규칙(def 전체) | N2b / N2w(넓힌 T6) | 인벤토리 |
|---|---|---|---|
| `_import_analog_grammar` | 12 | 3 / 3 | 159 |
| `find_idiom_matches` | 8 | 2 / 2 | 15 |
| `find_stack_edges` | 6 | 2 / 2 | 66 |
| `audit_theta_root_direction` | 29 | 3 / 3 | 4 |
| 합 | **55** | **10 / 10** | |

* 지금 gate 도구(`0f23786` `mutate_changed.py`, 범위 card 미병합)를 가짜 pytest로 돌린 선택 probe: 레코드 55, 대상 55, `not_targeted` 0, 순서 일치 -- 현행 규칙 = 55.
* N2(범위 card 계약 1의 독립 프로토타입 `v3scope_kit/scope_proto.py`) 10개 = card 'V3 계획' 표 10개(id 문자열 일치), 이전 키트 `ids_b34_narrow.json`과 55·10·10 모두 일치.
* 계약 4·6만 죽이는 6개(`const±:body[3].body[0].value.args[0]`, `stmt_delete:body[3]`, `audit_theta_root_direction:stmt_delete:body[3]`·`…body[3].body[0]`·`…body[6].body[5].orelse[0]`)는 55 안·N2 밖.
* 시간(이전 키트, junit 시간 기준): N2 10개 하한 0.8분·상한 0.27 h. 현행 55개는 `_import_analog_grammar` 12개 × 인벤토리 159 test가 지배(상한 미측정, 도구는 `-x`로 첫 실패에서 멈춤).

### 0.5 문서 시퀀스 모의(`b34_kit/sim_b34.py` → `out/sim_b34.txt`, NG 0)

| 단계 | P2(초안 그대로) | P3(`phase: 3` + 모의 decision 기록) |
|---|---|---|
| §4.0 확인 | role/* 0(복제본), approvals 기록 있음, 줄 번호 유효, `not_targeted` 0(=범위 card 미병합 -- 착수 조건 미충족 판 표시) | 같음 |
| decision 기록 | -- | `parse_approval_header` 통과, `Role: doc` 커밋 |
| spec+interface | `parse_spec_card` (2, red-green, no, [b26-before-phase3], 절 12), interface 14행 전부 `stick_diagram` | (3, …, [b26-before-phase3, 모의 id], 12), interface 같음 |
| references 패치 | `--check` pending 5·무쓰기 → 적용(numstat 17/16, `if not devs` 줄 불변) → 재실행 already-applied, blob LF, `test_phase2_stale_refs` 18 passed | 같음(`--gmid-phase=3`) |
| 가짜 gate push | 통과, accept-log `<P0> <A>`, gate master = A | 같음 |
| 대조 | 트레일러 없는 커밋 → `[EL4 거부] 트레일러 … 정확히 하나가 아니다` | 같음 |
| 사용자 install.py | 승인 기록 없음 → 거부, staged_diff 승인 기록 + `Role: user` → 통과 | -- |

가짜 gate는 `gate-runner.py`의 무결성 대조(`integrity.py --scope gate` -- 설치된 hook·workspace 대조)만 뺐다. EL1(이 세션 hook)·EL3(`.githooks`)은 복제본에 없어 모의하지 않았다.

### 0.6 착수 직전에 다시 볼 것

1. **Q-B34-PHASE 답**(0.2) -- 답 전에는 spec card를 커밋하지 않는다. (가)면 decision 기록 문안에 'design 30 승인·U-03 비적용'을 넣을지 함께 정한다.
2. 착수 0단계 명령(머리). 두 V3 card 병합·정리, `role/*` 0개(지금 P10b 역할 브랜치 3개).
3. 커밋 계획 §4는 전부 절대 경로다(`(cd … && …)`·`cd` 뒤 상대 경로 쓰기·변수가 든 `rm`은 이 세션 hook이 거부 -- 이번 작업에서 실제로 거부됨).
4. references 패치 문안(`patch_b34_refs.py`의 새 문안 5개)은 초안이다 -- 커밋 전 `git diff`로 읽는다.
5. B26-1 card가 B34보다 먼저 SD를 바꾸는 순서 변경이 생기면 0단계 (나).
6. **계약 8과 V4 (1)**: card에 넣은 helper 스냅샷 모양은 도구 (1)이 보지 못하는 모양이다(계약 자체가 '같은 호출의 상태 변화 전후 동일성'이라 기대값 복사가 아니라는 판단은 auditor basis가 진다).
   이것을 받아들이지 않으려면 대안은 기대값을 '부재를 한 번도 거치지 않은 새 프로세스'의 값(subprocess JSON)으로 바꾸는 계약 8 정정이다(실측 V4 PASS, 상태 누수 판정은 더 엄격 -- 단 `Match` 정규화 결과를 JSON으로 넘겨야 한다). 착수 전에 둘 중 하나로 확정.
   **→ 확정(아래 '오케스트레이터 결정 0.6-6'): 새 프로세스 oracle. spec card(`draft_b34.final.spec.md`, 직전판 `.spec.v2.md`)와 1절 반영, 프로토타입 증명 `b34_kit/proto_066/`.**

---

## 1. test-author 브리프(gmid-test-author, §12 순서 2)

```
역할: gmid-test-author. change id = 20260930-b34-grammar-explicit (엔진 동작 변경, red-green, phase <P>).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b34-grammar-explicit-test (브랜치 role/test/20260930-b34-grammar-explicit). 모든 명령은 절대 경로로(git -C, cd 금지).
쓰기 경로: skills/analog-gmid-design/assets/tests/** 만. 새 파일 하나: skills/analog-gmid-design/assets/tests/contracts/test_b34_grammar_explicit.py.
입력: interface card docs/02-design/specs/20260930-b34-grammar-explicit.interface.md(기존 함수 14개, 전부 stick_diagram),
      spec card의 '관찰 가능한 계약'(머리 문단 + 계약 1~8 + 정규화), 'oracle 종류와 출처', '거부해야 할 입력'.
열람 금지: skills/analog-gmid-design/assets/*.py(엔진 소스). analog-grammar 소스도 읽지 않는다. 기존 test는 읽어도 된다(예: test_ic3.py 3절 overrides 구성, test_s120_section).
커밋: git -C <worktree> commit --trailer "Role: test" --trailer "Change-Id: 20260930-b34-grammar-explicit" -m "test: …"
```

### 1.1 판정할 것(계약 번호 그대로)

| 계약 | test가 하는 일 | 기대(oracle) |
|---|---|---|
| 1 | 두 모듈 부재(`monkeypatch.setitem(sys.modules, "netclass", None)`·`"idioms"`)에서 진입점 14개를 9회로(`A/library/*.topology.json` 중 `_`로 시작하지 않는 것)에 부른다. `load_topology(p)`·`run_topology_pipeline(p, overrides)`(소자마다 `{"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": "stack_<이름>"}`), transistor 목록 함수 12개(인자는 계약 1 그대로). 진입점마다 `with pytest.raises(ImportError) as ei:` 한 블록 | 전부 `ImportError`(하위형 포함), 반환 없음 -- (a) 구성 |
| 2 | `idioms`만 부재 → `load_topology` 9개, `netclass`만 부재 → `find_stack_edges` 9개 | `ImportError` |
| 3 | 계약 1·2의 예외 | `analog-grammar` 문자열, 탐색 경로(정규화 `norm(x) = os.path.normcase(os.path.realpath(x))`, 통과 조건 (i) 또는 (ii) 그대로 -- `E`는 test 파일 위치에서 구한 저장소 루트로), `exc.__cause__`가 `ImportError` |
| 4 | analog-grammar 있음. 탐색 경로를 뺀 `sys.path`(monkeypatch.setattr)에서 `find_stack_edges(ts)` 한 번 → `norm(sys.path[0]) == E`, 한 번 더 → `norm(x) == E`인 항목 정확히 1개 | (c) 기존 동작 |
| 5 | 있음. `fx`(gate 없는 두 소자)에 `find_idiom_matches`·`find_stack_edges`·`find_differential_and_mirror_forks`·`refine_differential_and_mirror_relations` → `None`, `audit_theta_root_direction(fx, None) == []`. 그리고 **새 프로세스**(`subprocess`, `sys.executable`)에서 `sys.modules`에 두 이름 `None`을 둔 뒤 `import stick_diagram` 성공 | (c) |
| 6 | 있음. `audit_theta_root_direction(fx, {θ A})== []`, `audit_theta_root_direction(gx, {θ A_signed, terms: []}) == []`(입력은 계약 6 그대로) | (a) 구성 |
| 8 | 한 test 함수 안에서(회로 9개 parametrize): ① 기대값 = `subprocess.run([sys.executable, "-B", "-c", <스크립트 문자열>, <stick_diagram 폴더>, <contracts 폴더>, p])` -- 새 인터프리터가 같은 `p`로 `load_topology(p)` → 진입점 14개(계약 1 인자)를 불러 정규화 JSON을 출력, `assert rc == 0, err` 뒤 `json.loads` ② 같은 `p`로 `ts`를 얻고 부재(`with monkeypatch.context()`) 안에서 진입점 여러 개를 `contextlib.suppress(ImportError)`로 부름(base 반환·head 오류 둘 다 허용, 다른 예외는 실패) ③ 복원 뒤 test 본문에서 14개를 **직접** 불러 정규화한 dict `got` ④ `assert got == expected` | (c) **새 프로세스 값**(같은 입력, 부재를 거치지 않은 별도 인터프리터) -- 오케스트레이터 결정 0.6-6 |

계약 7(base 대조)은 auditor 몫 -- test에 넣지 않는다.

### 1.2 모양 규칙(V3 인벤토리 조건 -- 어기면 auditor가 순서 3에서 돌려보낸다)

* 진입점 14개는 test 함수 **본문**에서 `stick_diagram.<이름>(…)`으로 직접 부른다. `parametrize` 이름 문자열·모듈 상수 목록 + `getattr`로만 부르지 않는다(회로 9개 반복은 parametrize 가능).
* 새 파일의 모든 def 이름: test 함수 `test_b34_…`, helper·중첩 함수·fixture `_b34_…`(예: `_b34_normalize`, `_b34_exc_problems`). `snap`·`run`·`check`·`norm` 같은 흔한 이름 금지(그래프가 이름으로 다른 파일과 이어 인벤토리를 suite 전체로 부풀린다 -- 실측 159·15·66·4 → 237·236·234·234).
* 입력(`ts`·소자 이름)은 부재를 만들기 **전에** `load_topology(p)`로 얻는다. 부재는 test 함수 본문 안에서만 만든다(세션·모듈 fixture 금지).
* 부재 상태에서는 `stick_diagram` 진입점만 부른다 -- `sizing_recipe` 함수는 하나도 부르지 않는다(topology 캐시가 부재를 가린다).
* **판정 문장 모양(오케스트레이터 결정 0.6-6 -- 이 규칙만 쓴다. 근거: `0f23786` `test_lint.py` 실측 `b34_kit/out/v4probe_*.txt`, 프로토타입 `b34_kit/proto_066/`)**:
  - 계약 1~3: **`with pytest.raises(ImportError) as ei:`** 안에 `stick_diagram.<진입점>(…)` 한 줄, 메시지·경로·`__cause__` `assert`는 `with` 뒤(if·try 밖)에. `try`/`except` 모양과 예외를 돌려주는 helper 모양은 쓰지 않는다(`assert`를 `except` 절 안에만 두면 (3) FAIL).
    계약 3 점검을 helper(`_b34_exc_problems(exc)` → 위반 절 목록)로 묶어 `assert _b34_exc_problems(ei.value) == []`로 써도 된다(피검 호출이 아니라 예외 객체 판정이라 (2) NO-SUBJECT가 정상).
  - 계약 8: 기대값은 **새 프로세스 값**만(위 1.1 표). 같은 프로세스의 부재 전 값을 기대값으로 쓰지 않는다 -- `before`/`after` 지역 변수는 (1) FAIL, 진입점 호출을 `_b34_snapshot`류 helper에 감춰 양쪽을 비교하는 모양은 도구가 판정 문장에서 피검 호출을 못 봐(0·0) 통과할 뿐이므로 금지(게이트를 피하지 않고 통과한다).
    판정 문장 왼쪽 `got`의 각 값은 test 본문의 `stick_diagram.<진입점>(…)` 직접 호출(정규화로 감싸는 것은 됨), 오른쪽은 subprocess JSON. 새 프로세스 쪽 진입점 호출은 `-c`에 넘기는 **문자열 안**에 둔다(그래프 간선이 아니어서 인벤토리를 부풀리지 않는다 -- 프로토타입 k = 4·2·3·2).
    새 프로세스는 정규화 함수를 test 모듈에서 import해 써도 된다(`sys.path`에 contracts 폴더를 넣고 `from test_b34_grammar_explicit import _b34_normalize`). 환경은 `PYTHONHASHSEED` 고정·`PYTHONDONTWRITEBYTECODE=1`.
  - 프로토타입 실측(V4 `--interface-card … --base S --head K`): verdict PASS, 계약 8 판정 문장 (2) UNJUDGED(왼쪽 피검 호출 14·오른쪽 0, (1) 발견 없음), 나머지 NO-SUBJECT, FAIL 0.
* 정규화(계약 7·8): spec card '정규화' 그대로(`Match`류 → 튜플, set → 정렬 리스트(키 `repr` 또는 `json.dumps(sort_keys=True)`), dict 재귀, 문자열·해시로 바꿀 때는 dict 키도 정렬).
  계약 8은 JSON으로 넘기므로 JSON 왕복에서 값이 같아야 한다: 튜플 → 리스트, 실수 → `repr` 문자열(`nan` 대비), 문자열 아닌 dict 키 → 정렬한 `[키, 값]` 리스트, dataclass·객체 → 형 이름 + 필드 dict.

### 1.3 판정기 자기 점검(같은 파일, 같은 판정 함수에 합성 입력)

* 조용히 반환하는 가짜 진입점(`lambda *a: None`, `lambda *a: {"unavailable_reason": "x"}`)을 `with pytest.raises(ImportError):`에 넣으면 `pytest.fail.Exception`이 나야 한다(바깥 `pytest.raises(pytest.fail.Exception)`로 확인).
* 메시지에 `analog-grammar`가 없는 `ImportError`, 탐색 경로가 없는 `ImportError`, `__cause__`가 없는 `ImportError` → 계약 3 판정 함수가 거부.
  주의(프로토타입 실측): 탐색 경로 자체에 `analog-grammar`가 들어 있다. '이름 없음' 합성 오류는 경로도 없는 메시지(예 `"cannot import netclass"`)로 만든다 -- 경로를 넣으면 이름 절이 자동 충족돼 자기 점검이 잘못 실패한다.
* 계약 8 비교 함수: 같은 값 두 번 → 같음(정규화 없이 `Match` 리스트를 `==`로 비교하는 판정을 쓰지 않았음), 다른 값 → 다름, `json.loads(json.dumps(정규화 값)) == 정규화 값`(`nan`·set·튜플 포함 합성 값).
  (모양 선례: `test_d_delete_telescopic`의 거부 점검.)

### 1.4 자기 확인(커밋 전, 판정 근거 아님)

```
PYTHONDONTWRITEBYTECODE=1 C:/Python314/python.exe -B -P -m pytest -c <worktree>/tools/gates/pytest_gate.ini --rootdir=<worktree> --confcutdir=<worktree> -q -p no:cacheprovider --gmid-phase=<P> --gmid-strict= <worktree>/skills/analog-gmid-design/assets/tests/contracts/test_b34_grammar_explicit.py
```
base(지금 엔진)에서: 계약 1·2·3 test는 **FAIL**(`Failed: DID NOT RAISE <class 'ImportError'>` -- 프로토타입 27/27) -- 다른 예외로 실패하면 안 된다. 계약 4·5·6·8과 자기 점검은 **PASS**(계약 8은 부재 구간 `ImportError` 허용이라 base 조용한 반환에서도 통과).
기대값은 계약 문장·구성에서만 만든다(피검 함수를 불러 기대값을 만들지 않는다 -- 계약 8은 spec card가 정한 새 프로세스 값이고, 같은 프로세스에서 피검을 부른 값이 아니다).

---

## 2. code-author 브리프(gmid-code-author, §12 순서 5)

```
역할: gmid-code-author. change id = 20260930-b34-grammar-explicit (엔진 동작 변경, red-green).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b34-grammar-explicit-code (브랜치 role/code/20260930-b34-grammar-explicit, 부모 = test 커밋 T). 절대 경로만, cd 금지.
쓰기 경로: skills/analog-gmid-design/assets/stick_diagram.py, skills/analog-gmid-design/assets/sizing_recipe.py(docstring만). test·references·install.py·analog-grammar는 쓰지 않는다.
입력: spec card '의도'·사이트 표·docstring 목록, interface card. test가 틀렸다고 보면 고치지 말고 dispute(<worktree>/docs/02-design/disputes/20260930-b34-grammar-explicit.md)를 쓰고 같은 트레일러로 커밋한 뒤 멈춘다.
커밋: git -C <worktree> commit --trailer "Role: code" --trailer "Change-Id: 20260930-b34-grammar-explicit" -m "…"
```

### 2.1 바꿀 것(줄은 `2d58fd8`=`0f23786` 기준)

1. **사이트 1** `_import_analog_grammar` 1057~1058: `except ImportError:` → `except ImportError as e:`, 본문 = **한 문장** `raise ImportError(<'analog-grammar'와 _ag_path를 담은 문자열 식 하나>) from e`.
   **모양 고정**(V3 변이 수 55의 전제): f-string 하나 등 문자열 식 하나, 정수 상수 추가 없음, 모듈·이름마다 raise 반복 없음, 새 지역 변수·도움 함수 없음. `sys.path` 주입(1049~1054: 경로 계산, `if _ag_path not in sys.path: sys.path.insert(0, _ag_path)`)은 그대로.
   모의 예(측정에 쓴 것): `raise ImportError(f"analog-grammar skill을 import할 수 없다(탐색 경로 {_ag_path})") from e`. docstring 1046~1048을 "없으면 `ImportError`(skill 이름·탐색 경로, 원래 예외는 `__cause__`)"로.
2. **사이트 2** `find_idiom_matches` 1073~1074, **사이트 3** `find_stack_edges` 1089~1090: `if netclass is None: return None` 삭제.
3. **사이트 11** `audit_theta_root_direction` 3370~3371 `if netclass_mod is None or idioms_mod is None: return []` 삭제, **사이트 11b** 3376~3377 `if matches is None: return []` 삭제.
4. **docstring·주석만**(AST 해시 불변): SD 1025~1031 주석 블록, 1304, 1384, 1533, 1676, 1891~1892, 2070, 2152, 2241, 2349, 3074, 3271, 3356, 3363~3364, 3515~3516, 3921~3922; SR `resolve_stack_layout` docstring **6510~6512**(4번).
   부재 서술 → '`ImportError`', 도달 불가 분기가 남는 함수는 "`… is None` 분기는 도달 불가 -- 삭제는 B26-1/B35/백로그" 한 구절, gate 소자 없음 서술은 남긴다.
   3363~3364는 IC5 '검사하지 않는 것:' 절 안 -- 절 머리와 `영역: dc, ac_struct` 줄은 그대로 두고 analog-grammar 문장만 뺀다(`test_ic5`).
5. 레지스트리 360행은 필수 아님(이름 불변).

### 2.2 하지 말 것

* 사이트 4~10·10b·12~14와 3955~3959의 코드는 건드리지 않는다(인계 -- B26-1·B35·백로그). gate 소자 없음 분기(`if not devs`, 남기는 것 목록)도 그대로.
* 광범위 `except` 추가 금지(V6). 모듈 최상위 import 추가 금지(지연 import 유지 -- 계약 5).
* `skills/analog-grammar/**`·`install.py` 쓰기 금지(B36·사용자 경로).

### 2.3 자기 확인(판정 근거 아님)

* 1.4의 명령 → 새 test 전부 PASS. `test_ic5`·`test_s120_section`·`test_selftest_stick_diagram` 전체 PASS.
* `git -C <worktree> diff --stat <T>` = SD·SR 두 파일. SD 코드 변경 def는 4개(docstring은 해시 밖).

---

## 3. auditor 브리프(gmid-verification-auditor, §12 순서 3·7)

```
역할: gmid-verification-auditor. change id = 20260930-b34-grammar-explicit, evidence_type red-green, 엔진 변경(phase <P>).
audit worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b34-grammar-explicit-audit (브랜치 role/audit/20260930-b34-grammar-explicit).
모든 측정은 격리 복제본에서(§12-7): git clone --no-hardlinks --no-local <audit worktree> <scratch>/iso → git -C <scratch>/iso remote remove origin.
scratch는 새 C:/g<n> 하나만(다른 C:/g* 건드리지 말 것), 끝나면 그 폴더만 삭제. 셸 가드: set -euo pipefail, git -C <절대 경로>만, cd 금지. 끝나면 실제 저장소 git status·reflog 불변 확인.
게이트 코드는 base 판(= spec card 커밋 뒤 gate master)을 git ls-tree + cat-file로 추출한 사본(선례 .ai/verification/20260930-df36-instance-relpath/scripts/extract_gate.py).
작성자(test·code) 보고는 증거로 받지 않는다. 판정 기록 .ai/verification/20260930-b34-grammar-explicit.json + scripts/·out/, Role: audit 커밋.
판정 기록 approvals = ["20260930-b26-before-phase3"] (phase 답이 (가)면 새 decision 기록 id 추가).
```

### 3.1 순서 3(freeze·base 확인 → `base_check.json`)

* T(test 커밋) 해시 고정. `git diff --name-only <base> <T>` = `…/tests/contracts/test_b34_grammar_explicit.py` 하나.
* **red**: base 엔진 + T test로 새 test 파일 실행(`--gmid-phase=<P> --gmid-strict=`, `-p merge_gate`·`GMID_RED_CAPTURE`). 계약 1·2·3 test만 FAIL이고 원인이 `Failed`(DID NOT RAISE/조용히 반환)·`AssertionError`인지, 다른 예외(`ImportError` 외 오류·수집 오류)가 0인지.
  계약 4·5·6·8·자기 점검은 PASS. `failure_hashes` = base 판 `merge_gate.red_failure_hash(<test id>, <예외형>)`.
* **인벤토리 확인(V3 전 필수)**: T 트리 그래프에서 4 def 인벤토리 = 159·15·66·4 + k(k ≤ 새 test 함수 수, 본문 직접 호출로 닿는 수 -- 프로토타입 계약 1·2·8 test 4개로 k = 4·2·3·2). 넘으면(예 237·236·234·234) 이름 규칙 위반 → test-author에게 돌려보낸다.
* **계약 8 모양 확인(결정 0.6-6)**: 계약 8 기대값이 subprocess(새 인터프리터) 값인지, 판정 문장 왼쪽에 진입점 직접 호출이 있는지(도구 내부 `_call_keys` 왼쪽 > 0·오른쪽 0 -- 재현 `b34_kit/proto_066/v4diag.py`). helper 스냅샷·같은 프로세스 부재 전 값이면 돌려보낸다.
* 판별력: base에서 계약 1 판정 함수가 14 진입점 × 9회로 = 126 전부를 '조용히 반환'으로 잡는지(실측 126/126 반환, 다른 예외 0), 계약 2(`idioms`만 108/126 반환 중 `load_topology` 9, `netclass`만 126).

### 3.2 순서 7(병합본 판정)

| V | 판정 | 근거·측정 |
|---|---|---|
| V1 | PASS | pytest 전체(`V1:` 명령 하나, base 판 `pytest_gate.ini`, `-k`·`--deselect`·`-x` 없음, **`--gmid-phase=<P> --gmid-strict=`**, 엄격 집합은 base 판 `merge_gate.strict_set`로 재서 기록 -- `0f23786` 기준 빈 집합). `v1_command_check` 위반 0 |
| V2 | PASS | red-green 사슬 base → T(Role: test) → K(Role: code, SD·SR) → 병합 M. 3.1 red 집합이 M에서 green, 나머지 test 무변화 |
| V3 | PASS | base 판 `mutate_changed.py --root <m> --base <base> --head <M> --gmid-phase=<P> --gmid-strict=`. 범위 card 병합본이면 대상 **10**(`not_targeted` 45), 아니면 **55**. 기대: 전부 killed, 면제 0(승인 원소와 겹침 0). 10개 id·죽이는 계약은 card 'V3 계획' 표. `except_body_delete`는 B34 test만 죽인다 |
| V4 | PASS | base 판 `test_lint.py --root <m> --interface-card <m>/docs/02-design/specs/20260930-b34-grammar-explicit.interface.md --base <base> --head <M>`(subject = interface card 14 진입점). basis에 `oracle 대조: ` 줄 -- 계약 1~3 (a) 구성(`pytest.raises`), 4·5 (c), 6 (a), 8 (c) 새 프로세스 값. 계약 8 판정 문장은 도구가 본다(프로토타입: (2) UNJUDGED, 왼쪽 피검 호출 14·오른쪽 0, (1) 발견 없음) -- UNJUDGED는 읽어서 대조: 오른쪽이 subprocess JSON뿐인지(같은 프로세스 값·helper 스냅샷이 섞이지 않았는지), 새 프로세스 입력이 같은 `p`·같은 인자인지, `assert rc == 0`이 있는지, 부재 구간이 복원 앞에 있는지. helper 스냅샷 모양(양쪽 피검 호출 0·0)이면 결정 0.6-6 위반으로 순서 3에서 돌려보낸다 |
| V5 | PASS | base 판 `weakening_diff.py`(base→T, base→M) -- 기존 test 변경 0 |
| V6 | PASS | base 판 `source_lint.py` -- 새 `except`는 `ImportError` 한정 재던짐, 광범위 except 0 |
| V7 | PASS | base 판 `reachability.py` -- 새 def 0·지운 def 0 |
| V8 | N/A | `도입 4: 폴백 발동 0 검사는 Phase 4부터(N4.2 v_intro[V8] = 4)` |
| V9 | N/A | `도입 6b: 물리 불변식 검사는 Phase 6b부터(N4.2 v_intro[V9] = 6b)` |
| V10 | PASS | '재현할 수치: 없음' → `reproduced_numbers` 빈 배열. 계약 7 측정은 아래 |

**계약 7(auditor 판정)**: analog-grammar 있음에서 base 대 M -- E-LIB 9/9(`load_topology`, `run_topology_pipeline` V1·V2), E-INST 두 회로(`current_reuse_telescopic_ota`, `folded_cascode` -- 선례 스크립트 `e_lib.py`·`e_inst_df36.py`·`einst.sh`), 진입점 14 × 9회로 반환 == (정규화 뒤, 또는 두 실행 같은 `PYTHONHASHSEED`).
카드 실측 기대: 126/126 같음. `refine_…` 반환의 `vertical_stack_id_candidates["groups"]` 키 순서는 seed마다 달라 문자열 비교면 키 정렬 필수.

**관찰(판정에 걸지 않음)**: `b34_kit/install_probe.py`를 M으로 돌려 설치 모양 사본에서 '없음 → 9/9 ImportError, 있음 → base와 meta 9/9 같음'을 한 줄로 적는다(사용자 `install.py` 작업 근거).

---

## 4. 순서 요약(오케스트레이터)

(V3 card 34·35 병합·정리, `role/*` 0) → **Q-B34-PHASE 답** → 착수 0단계 명령 → 커밋 계획 §4.0 → (가)면 §4.1 decision 기록 → §4.2 spec+interface(절대 경로) → §4.3 references 패치·`test_phase2_stale_refs` → §4.4 push 단독·전체 출력 확인 →
§12 순서 1(test worktree) → test-author(1절) → 순서 3 auditor freeze·인벤토리 확인(3.1) → 순서 4 code worktree → code-author(2절) → 순서 6 병합 → 순서 7 auditor(3.2) → 순서 8 push → 정리 →
병합 보고에 사용자 `install.py` 작업 한 건(0.3) → B26-1.


## 오케스트레이터 결정 (2026-10-01, 0.6-6)

- 계약 8 기대값은 **새 프로세스에서 얻은 값**(subprocess로 같은 입력을 별도 인터프리터에서 실행해 얻은 값)을 쓴다. helper(`_b34_snapshot`)로 감싸 test_lint 규칙 (1)을 피하는 모양은 쓰지 않는다 -- 도구가 보지 못하는 모양으로 판정 문장을 숨기는 것은 판정 약화와 같은 효과(원칙: 게이트를 피하지 않고 통과한다, 우회는 타당성 검토 후에만). 계약 1~3은 `pytest.raises` 모양.
- 착수 전 spec card 계약 8 문장과 test-author 브리프를 이 결정대로 고친다.
- **반영 완료(2026-10-01)**: spec card `draft_b34.final.spec.md`('test 모양' 끝 문단, 판정 유형 근거, 계약 8, 정규화 머리, oracle 계약 8, 거부해야 할 입력, V3 표 2행, '작성 전 실측' 000; 직전판 `.spec.v2.md`), 이 문서 0.1·0.6-6·1.1·1.2·1.3·1.4·3.1·3.2 V4.
  증명(`b34_kit/proto_066/`, 격리 복제본 `C:/g136` -- 삭제함): V4 verdict PASS(계약 8 판정 문장 (2) UNJUDGED, 피검 호출 왼쪽 14·오른쪽 0), red 27/27 `DID NOT RAISE`, 계약 8 test가 죽이는 N2 변이 7개 = helper 모양과 같은 7개(파일 전체 10/10), 인벤토리 +4·2·3·2, `parse_spec_card` (2, red-green, no, [b26-before-phase3], 절 12), interface card 기존 함수 14개 불변.
