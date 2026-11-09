# backfill 결함 card `20261001-b26-backfill-interdig-final-audit` -- 착수 키트(세 역할 브리프 + 착수 확인)

작성 2026-10-01. 기준: gate `master` `0f23786`(`a796468`과 `tools/`·`skills/`·`workspaces/` 차이 0 -- `git diff --quiet a796468 0f23786 -- tools skills workspaces` 같음).
사용자 결정: U-BF '결함으로 고침 (Recommended)'(2026-10-01 19:19 KST) -- 승인 기록 `20261001-b26-backfill-interdig-fix`(decision, 초안 `approval_20261001-b26-backfill-interdig-fix.md`).
순서: B34 → b26pre(`20260930-b26-pre-test-strengthen`) → **이 card** → B26-1.
저장소 쓰기·상태 변경 git 없음. 측정·모의는 scratch `C:/g128`(끝나고 삭제)에서만. 스크립트 `_drafts/b26bf_kit/`(결과 사본 `b26bf_kit/out/` -- setup·V3 대상/실행/병합·전체 회귀·library 계측·모의 출력).
대상 산출물: `draft_b26_backfill_audit.spec.md`(재검증·측정 반영판, 직전판 `.spec.v3.md`), `approval_20261001-b26-backfill-interdig-fix.md`(정정판, 직전판 `.v1.md`), 이 문서.

**착수 0단계(반드시, 다른 단계 전에 -- 읽기 전용)**: 이 키트는 B34·b26pre가 **아직 gate에 없는** 상태에서 모의 사슬(a796468 + B34 코드 + b26pre 시제품 test)로 쟀다. 착수 때는 두 card가 병합된 gate `master`에서 다음을 다시 돌리고 출력으로 판단한다.
```
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
git -C "$R" diff --stat 0f23786 gate/master -- skills/analog-gmid-design/assets/sizing_recipe.py      # (가) 비어 있어야(B34는 stick_diagram만, b26pre는 test만)
git -C "$R" show gate/master:skills/analog-gmid-design/assets/sizing_recipe.py | sed -n '11758,11759p;11769,11773p;11784,11794p;11798,11802p;11877,11881p'   # (나) 아래 0.1 표와 같은 글
git -C "$R" ls-tree --name-only gate/master -- skills/analog-gmid-design/assets/tests/contracts/ | grep -c 'test_b26pre_existing_paths.py\|test_b26_backfill_interdig.py'   # (다) 1(b26pre 파일만)
git -C "$R" ls-tree --name-only gate/master -- .ai/approvals/ | grep -c 20261001-b26-backfill-interdig-fix   # (라) 0(아직 안 올림)
```
(가)(나)가 맞으면 card 인용 줄·수정 후보 줄(11800·11879)은 그대로다. 어긋나면 card '의도'·'거부해야 할 입력'의 줄 번호를 다시 재고, `b26bf_kit/v3_targets.py`로 V3 대상을 다시 잰다(0.3).
(다)가 0이면 b26pre가 아직 병합되지 않은 것이다 -- 착수하지 않는다(순서 조건; 0.3의 V3 수치는 b26pre test가 base에 있다는 전제다).

---

## 0. 착수 확인 결과(오케스트레이터용)

### 0.1 spec card 재검증(gate `master` `0f23786`, archive 사본 `C:/g128/gm`)

| 확인 | 결과 | 조치 |
|---|---|---|
| 엔진 `a796468` → `0f23786` | `tools/`·`skills/`·`workspaces/` 차이 0 | 줄 번호 그대로 |
| 인용 줄(sizing_recipe.py) | def 머리 11712, docstring `interdig_ok` 11758~11759, backfill 주석 11769~11770·건너뜀 11772~11773, `_finalize` 앞 주석 11784~11786·정의 11787~11794, 루프 안 수리 11798·backfill **11800**·`if result.ok:` 11801·성공 분기 `_finalize` 11802, 루프 뒤 수리 11877·backfill **11879**·`_finalize` 11880 | 그대로 |
| 소비처 | `git grep interdig_ok -- '*.py'`: 엔진 자신 + `A/tests/unit/test_selftest_sizing_recipe.py:1480`(`is not None`)뿐. 비코드 히트(`.ai/context.md` 6, `.ai/verification/20260930-p9-kcl-edges/` AST 덤프 2)는 소비처 아님 | 소비처 문장에 `-- '*.py'` 범위를 적음 |
| 엔진 안 호출부 | `run_matching_safety_with_finger_growth(` 호출은 `optimize_full_circuit_budget` 9369 하나(`_lut_by_kind`가 있을 때), 결과는 9398에서 `pr["relaxed_pairs"]` → `pipeline_result` | 그대로 |
| `.ai/context.md` 1558~1561 | 세션17 '알려진 한계'(`interdig_ok=False` 실제 사례 self-test 미확인) 그대로 | -- |
| 이름 충돌 | `test_b26_backfill_interdig.py`·`b26bf` -- `A/` 0건 | -- |
| `A/tests/contracts`의 `interdig_ok`·`relaxed_pairs` | 0건 | -- |
| 계획서·설계·레지스트리 소비자 | `interdig_ok`·`run_matching_safety_with_finger_growth` 0건(레지스트리 159행 `_try_interdigitation_table_match`는 다른 함수) | -- |
| B26-1 접점 | B26-1 초안 '사이트 교체 -- SD 13줄 + SR 2줄'의 SR 2줄 = 이 def의 두 `repair_matching_safety` 호출(11798·11877) | 인계 문장 그대로 |
| 승인 기록 초안 | 질문 원문이 `user_decisions.md` 'U-BF 질문 원문'과 **달랐다**(초안 `쟽니다` 2곳 -- 원문 `잽니다`). 저장소 밖 `_drafts/…` 경로 3곳 | 0.2 |

### 0.2 승인 기록 초안 정정(`approval_20261001-b26-backfill-interdig-fix.md`, 직전판 `.v1.md`)

* 질문 원문 인용의 `쟽니다` → `잽니다`(질문 본문 1곳 -- `user_decisions.md`와 바이트 단위 같음 확인 True). 선택지 설명의 같은 글자 1곳도 `잽니다`로 고쳤다.
  **주의(오케스트레이터 확인 필요)**: 선택지 설명 원문은 `user_decisions.md`에 없다(선택지 이름만 있다). 세션 기록의 AskUserQuestion 선택지 description과 대조해, 원문이 정말 `쟽니다`였다면 그 한 곳만 되돌린다(원문 인용은 고치지 않는다).
* 저장소 밖 경로(`_drafts/b26_backfill_question.md`, `_drafts/review_b26pre.md`, `_drafts/review2_b26pre.md`) 3곳 -- 커밋되는 기록이 가리킬 수 없는 경로라 "질문 준비 문서(저장소 밖 작업 초안)"와 "배경 사실은 spec card `20261001-b26-backfill-interdig-final-audit` '의도'"로 바꿨다. 결정 문장·범위 설명·재검토는 그대로.
* 형식: `---` 시작, LF, BOM 없음, HTML 주석 없음, `merge_gate.py parse-approval` 통과(0.5).

### 0.3 V3 측정(이 card -- 모의 사슬, `b26bf_kit/setup_v3.py`·`v3_targets.py`·`run_v3_tool.sh`·`v3_replica.py`)

모의 사슬(격리 복제본 `C:/g128/sim/r`, origin 없음, 빈 hooksPath):
`P0 = a796468` → `B1 = P0 + B34 코드`(stick_diagram 4 def, `mk_g106.py`와 같은 치환) → `BP = B1 + b26pre 시제품 test`(`proto_v2_test_b26pre.py` → `A/tests/contracts/test_b26pre_existing_paths.py`)
→ `H = BP + 수정 후보(11800·11879 두 줄 삭제) + 이 card 시제품 test`(`proto_bf_test.py` → `A/tests/contracts/test_b26_backfill_interdig.py`), `T = BP + 시제품 test만`.
V3 범위 = `BP..H`(이 card의 base = b26pre 병합본이라는 순서 전제).

변이 실행 = gate `master` 판 `mutate_changed.py`(archive 사본 `C:/g128/gate0`, 캐시와 같은 blob)의 `main`을 `--base BP --head H --gmid-phase=2 --gmid-strict=`로 실제로 돌렸다(`run_v3_tool.sh` -- 직렬이라 22 변이 뒤 중단).
나머지 75 변이는 같은 도구 함수(`changed_defs`·`mutants`·`_replace_def`·`inventory`·`test_nodeid`)와 같은 pytest 인자로 작업 사본 6개에서 병렬 실행(`v3_replica.py`). 겹친 3 변이의 결과는 도구와 같았다. 인벤토리 기준 실행 통과.

| 범위 규칙 | 바뀐 def | 대상 변이 | 죽음 | 생존 | 판정 |
|---|---|---|---|---|---|
| **현재 도구**(바뀐 def의 변이 전부) | `sizing_recipe.run_matching_safety_with_finger_growth` 하나(인벤토리 71 test) | 97 | 78 | **19** | FAIL(생존 19 -- 전부 이 card가 바꾸지 않은 문장) |
| **N2w**(범위 card `20260930-v3-changed-stmt-scope`, `_drafts/v3scope_kit/scope_proto.py` `select(…, "N2w")`) | 같음 | **4** | 4 | **0** | PASS |
| (참고) N2b(승인 당시 정의) | 같음 | 4 | 4 | 0 | -- |

N2w 대상 4(모두 죽음): `stmt_delete:body[9]`(for 루프 전체), `stmt_delete:body[9].body[1]`(`if result.ok:` 블록, head 11800), `stmt_delete:body[11]`(루프 뒤 `_finalize`, head 11878), `early_return:body[1]`.

현재 도구 생존 19(head 줄 = `H`의 sizing_recipe.py, base 줄은 11800 앞이면 같고 뒤면 +1, 11879 뒤면 +2):
| head 줄 | 변이 | 문장 | 메모 |
|---|---|---|---|
| 11715 | `const±` `args.defaults[0].elts[0·1]`, `args.defaults[2]`(6) | 기본 인자 `gm_id_bounds=(2.0, 30.0)`, `max_rounds=5` | 모든 호출이 이 인자를 명시(엔진 9372·test) -- 기본값 미사용 |
| 11772·11773 | `stmt_delete` `body[6].body[0].body[0]`·`…body[0].body[0]`(2) | backfill의 `if entry["interdig_ok"] is not None: continue` | **수정 뒤 생긴 등가 후보**: backfill이 반환마다 `_finalize`에서 한 번만 불리므로 건너뛰기 가드가 무의미해졌다 |
| 11778 | `stmt_delete` `body[6].body[0].body[2].body[0].body[1]` | backfill 안 `break` | 쌍마다 3b 체크가 하나뿐이면 등가 |
| 11796 | `stmt_delete:body[8]` | `result = None` | 등가(루프 안·뒤에서 반드시 대입) |
| 11801 | `stmt_delete:body[9].body[1].body[0]` | 성공 분기 `_finalize` | b26pre의 'N2d만' 등가 후보(base 11802)와 같은 문장 |
| 11810 | `stmt_delete:body[9].body[2]` | `import re` | 모듈에 `re`가 이미 있으면 등가 |
| 11816 | `const±` `…left.elts[0·1].args[0]`(3) | `m.group(1)`/`m.group(2)` 순번 | 3c 실패 쌍 파싱 -- 기존 test 공백 |
| 11832 | `const-:body[9].body[7].value.slice` | `a, b = failing_3c[0]` | 3c 실패 쌍이 하나뿐인 입력만 있음 -- 기존 test 공백 |
| 11849 | `cmp_flip:body[9].body[15].body[0].value.test.values[1].ops[0]` | `reason` 3항식의 `fix["growth"] is not None` | 기존 test 공백 |
| 11870·11871 | `stmt_delete` `body[9].body[18]`·`…body[0]`(2) | 핑거증가 뒤 `cur_ctx` 사이징 갱신 루프 | 기존 test 공백(반환 ctx를 보는 test 없음) |

**해석**: 이 card는 B34 뒤라 범위 card(N2w) 병합 뒤에 돈다(B34 card '판정 규칙': P10 → P10b → Phase 2 DoD → V3 binding → V3 scope → B34). 그 규칙으로 대상 4·생존 0 -- 면제·추가 test 불필요.
만약 범위 card 전에 착수하면(순서가 바뀌면) 현재 도구로 생존 19가 이 card의 V3 FAIL이 된다 -- 착수하지 말고 오케스트레이터가 순서를 다시 본다(이 card가 만든 생존은 11772·11773 둘뿐이고 그 둘도 N2w 대상이 아니다).
B26-1 인계: 수정 뒤 head에서 11800·11879 문장이 사라졌다(B26-1의 V3 생존 몫 2개 소멸, 예상대로). B26-1 모의 head·대상 수는 이 card 병합본에서 다시 잰다.

### 0.4 library 영향(DEC-40 입력 -- `b26bf_kit/lib_measure.py`·`run_lib.sh`)

이 def의 엔진 안 호출부는 `optimize_full_circuit_budget`(9369) 하나다. E-LIB 정의(`load_topology`·`run_topology_pipeline`, stick_diagram)는 이 def에 닿지 않는다(정적). 그래서 harness 실행(`run_harness.run`)마다 이 def를 감싸
(반환을 읽기만) 호출별 `relaxed_pairs` 항목의 반환 `interdig_ok`와 같은 반환 audit의 3b를 대조했다. 사본: base = `BP` 트리(a796468 + B34 + b26pre 시제품), fix = `H` 트리(+ 수정 후보). PYTHONHASHSEED 0.

| 회로(library 9) | harness SPECS | base: 호출 / 완화 항목 / 불일치(= 수정이 바꾸는 항목) | fix: 같은 셋 | `instance.json` sha256(키 정렬 JSON) base = fix | 비고 |
|---|---|---|---|---|---|
| `current_reuse_telescopic_ota`(파일럿) | 있음 | 1 / 2 / **0** | 1 / 2 / 0 | 같음 `1b9a4d4c…` | 완화 2쌍: `M4a/M4b` interdig_ok True(3b True), `M3a/M3b` **False(3b False)** -- 실제 회로의 첫 `interdig_ok=False` 관찰(`.ai/context.md` 1558 '알려진 한계'의 사례). 사유 `growth_not_applicable`. 핵심 반환 해시(`core_sha`, interdig_ok 제외) base = fix |
| `folded_cascode` | 있음 | 1 / 0 / 0 | 1 / 0 / 0 | 같음 `e690b95d…` | 완화 없음(무발동) |
| `two_stage_ota` | 있음 | 0 / -- / -- | 0 | 산출 없음(두 사본 같음) | harness가 `optimize_full_circuit_budget` 안 `ValueError`('stage1_out' 그룹 VDS 합 KVL 불일치)로 이 def 전에 멈춤 -- `a796468`(B34 없음)에서도 같음, 이 card와 무관 |
| `nmcnr_amplifier` | 있음 | 0 / -- / -- | 0 | 산출 없음(두 사본 같음) | `ValueError`(모든 theta 격자점 infeasible, 'stage2_diode_ref' 예산) -- `a796468`에서도 같음, 이 card와 무관 |
| 나머지 5(`common_gate_amplifier`·`ngcc_3stage_ff`·`pushpull_follower_buffer`·`sf_pushpull_output_opamp`·`two_stage_ota_sf`) | 없음 | 호출 경로 없음 | -- | -- | `load_topology` 9/9 ok(두 사본), 계측 중 호출 0 |

**결론(DEC-40 입력)**: library에서 수정 후보가 `interdig_ok`를 바꾸는 항목 **0**(완화가 생기는 유일한 회로인 파일럿에서도 정리 전후 3b가 같다). `instance.json`에는 `interdig_ok` 키가 없고 두 사본 해시가 같다.
→ 재생성할 기준선 없음. 기존 test 전체에서도 어긋나는 호출 0(독립 검토 계측)이라, 값이 바뀌는 곳은 이 card의 합성 입력뿐이다. 실행 시간: 파일럿 ~430초, folded ~50초(두 사본 병렬).

### 0.5 red-green·전체 회귀(B34 위 -- 그동안 B34 없는 사본에서만 잼)

| 측정 | 결과 |
|---|---|
| red(`T` = BP + 시제품 test, base 엔진, archive 사본·seed 0·1) | 2 failed -- 둘 다 `AssertionError: assert False is True`, `where True = AuditCheck(name='3b. interdigitation[Ma/Mb] [참고용 -- 이 kind는 필수 아님]', ok=True, detail='seg1_seg1: 인접').ok` |
| green(`H`, seed 0·1) | 2 passed |
| `A/tests` 전체, `T` git 복제본(seed 1) | 2 failed(위 red 2개뿐)·888 passed·15 xfailed, 435초 |
| `A/tests` 전체, `H` git 복제본(seed 1) | **890 passed·15 xfailed·실패 0**, 433초 (`.git`이 있는 복제본이라 `test_ts6_probe_relocate` 2개도 통과 -- 예전 archive 사본의 '2 failed'는 환경 한계였음) |
| V4(base 판 `test_lint.py`, 모의 interface card, `BP..T`) | PASS, 판정 (2) `NO-SUBJECT` 2건 -- 1.4 |

이 수치로 card '재현할 수치'의 'auditor 몫(미측정)' -- B34 위 전체 회귀 -- 를 사전 측정으로 채웠다(판정은 여전히 auditor가 착수 base에서 다시 잰다).

### 0.6 모의 결과(`b26bf_kit/sim_launch_bf.sh` -- `C:/g128/sim2/r` = gate `master` `0f23786` 복제, bare 가짜 gate `C:/g128/sim2/gate.git`)

| 단계 | 결과 |
|---|---|
| 0 모래상자 | `C:/g128/sim3/r` = `0f23786`(origin 없음, 빈 hooksPath), 가짜 gate = bare 복제(hook 없음 -- EL4는 `merge_gate.py receive`를 직접). 게이트 캐시 `…/.git/gmid-gate-cache/0f237862…`(`role_paths.tree_blobs`→`extract_blobs`→`dir_matches`, 22파일, `interface_card.py`가 gate master blob과 바이트 동일) |
| D 승인 기록 | 초안 그대로 복사, LF·BOM 없음·HTML 주석 없음, `merge_gate.py parse-approval` 통과(`target_kind decision`, `target_list ["U-BF-BACKFILL-INTERDIG"]`, `diff_path []`) → `Role: doc` 커밋(경로 = 기록 하나) |
| B spec+interface | 초안 복사 → **게이트 캐시의** `interface_card.py <절대 spec> --root <R> --out <절대 interface>` exit 0, 관찰 가능한 계약 **4행**(0.7-2), 신규 시그니처 0행 → `Role: doc` 커밋 |
| P 파싱 | `parse_spec_card`: phase 2·red-green·gate_change no·approval `[20261001-b26-backfill-interdig-fix]`·절 11. phase 2 ∈ `phase_order`. HEAD 트리에서 기록 머리 파싱·`load_approvals`에 있음. `reachability._approved_ids` 36 → 37(+`U-BF-BACKFILL-INTERDIG` 하나 -- 변이·test id 모양이 아니라 V3·V4·V7 면제에 닿지 않음). `gate_change_ok(HEAD)` False(gate_change no라 쓰이지 않음) |
| E EL4 | `merge_gate.py receive --git-dir <gate.git> --old 0f23786 --new <B>`(D·B 두 커밋) → **exit 0**. 대조: 트레일러 없는 커밋 하나를 더한 것 → **exit 1** "[EL4 거부] …: 트레일러 Role: code/test/audit/doc/user가 정확히 하나가 아니다([])"(게이트가 실제로 거부함) |

(모의 커밋 해시는 모래상자 것이다. EL3(커밋 hook)는 모의하지 않았다 -- 빈 hooksPath, 선례와 같은 범위. 실제 착수는 B34·b26pre 병합 뒤 gate master라 base가 다르다 -- 0단계로 확인.)

### 0.7 착수 직전에 다시 볼 것

0. **착수 0단계 명령**(이 문서 머리). B34·b26pre `audit:` 커밋이 gate `master`에 있고 `git -C "$R" branch --list 'role/*'`가 비어 있어야 한다(역할 브랜치가 있으면 문서 커밋 push가 EL1 거부).
1. **승인 기록 원문 대조**(0.2 주의): 선택지 설명의 `잽니다`/`쟽니다`를 세션 기록과 맞춘다.
2. **interface card**: 게이트 캐시(`<git-common-dir>/gmid-gate-cache/<gate master 전체 sha>/interface_card.py`)로 만든다. 모의 결과는 '관찰 가능한 계약' 4행(`run_matching_safety_with_finger_growth`·`size_transistor`·`GmIdLUT.gm_gds_ratio`·`SemiEmpiricalGmIdLUT.gm_gds_ratio`), 신규 시그니처 0행. 행 수가 다르면 card 백틱 토큰과 엔진 def 이름이 바뀐 것이다 -- 확인하고 멈춘다.
3. 셸: hook(`role_guard.py`)은 `(cd … && …)`·`cd` 뒤 상대 경로 쓰기 대상·변수 든 `rm`·**저장소 `.git` 안을 가리키는 인자**를 거부한다. 이번 작업에서 `ls <R>/.git/gmid-gate-cache/`(Bash·PowerShell 둘 다)가 `[EL1 거부] 저장소 내부를 가리키는 인자`로 거부됐다 -- 0.8의 `$CACHE/…` 호출이 거부되면 `sim_launch_bf.sh`처럼 스크립트 파일 안에서 부른다(`bash <스크립트>`).
4. 모의 커밋은 `--trailer "Role: doc"`만 썼다(문서 커밋 선례). 역할 커밋은 `--trailer "Role: …" --trailer "Change-Id: 20261001-b26-backfill-interdig-final-audit"`.

### 0.8 명령 시퀀스(오케스트레이터, MSYS bash -- 0.7 통과 뒤)

```bash
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
DR=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt
PY=C:/Python314/python.exe
ID=20261001-b26-backfill-interdig-final-audit
AID=20261001-b26-backfill-interdig-fix
git -C "$R" fetch gate
test "$(git -C "$R" rev-parse --abbrev-ref HEAD)" = master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
test -z "$(git -C "$R" branch --list 'role/*')"
test -z "$(git -C "$R" status --porcelain -- docs/ .ai/approvals/)"
GM=$(git -C "$R" rev-parse gate/master)
CACHE=$(git -C "$R" rev-parse --path-format=absolute --git-common-dir)/gmid-gate-cache/$GM
# D. 승인 기록(decision) -- spec card보다 먼저
cp "$DR/approval_$AID.md" "$R/.ai/approvals/$AID.md"
$PY -B "$CACHE/merge_gate.py" parse-approval "$R/.ai/approvals/$AID.md"
git -C "$R" add -- ".ai/approvals/$AID.md"
git -C "$R" commit --trailer "Role: doc" -m "docs: 승인 기록 $AID(U-BF 결정 -- relaxed_pairs interdig_ok를 반환 audit(euler 정리 뒤)의 3b로 채우도록 수정, target_kind decision; card $ID 착수 조건)"
# B. spec card + interface card(게이트 캐시의 interface_card.py, 절대 경로)
cp "$DR/draft_b26_backfill_audit.spec.md" "$R/docs/02-design/specs/$ID.spec.md"
$PY -B "$CACHE/interface_card.py" "$R/docs/02-design/specs/$ID.spec.md" --root "$R" --out "$R/docs/02-design/specs/$ID.interface.md"
git -C "$R" add -- "docs/02-design/specs/$ID.spec.md" "docs/02-design/specs/$ID.interface.md"
git -C "$R" commit --trailer "Role: doc" -m "docs: spec card $ID(run_matching_safety_with_finger_growth relaxed_pairs interdig_ok = 반환 audit 3b, red-green, approval $AID) + interface card"
# 확인(push 전): parse_spec_card -> phase 2, red-green, gate_change no, approval [$AID] (sim_launch_bf.sh P 단계와 같은 코드)
# push -- 단독 실행, 전체 출력 확인(병렬·tail 금지)
git -C "$R" push gate master:master
git -C "$R" fetch gate
git -C "$R" merge --ff-only gate/master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
# 순서 1: test worktree
git -C "$R" worktree add "$W/$ID-test" -b "role/test/$ID" gate/master
```
이어서 §12 순서 2(test-author, 1절) → 3(auditor freeze·base, 3.1) → 4(code worktree, 부모 = T) → 5(code-author, 2절) → 6(병합) → 7(auditor 판정, 3.2·3.3) → 8(push) → 정리 → **B26-1 재측정 인계**(card '결정 필요 항목' 마지막 묶음).

---

## 1. test-author 브리프(gmid-test-author, §12 순서 2)

```
역할: gmid-test-author. change id = 20261001-b26-backfill-interdig-final-audit (엔진 동작 변경, red-green, phase 2).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-test (브랜치 role/test/20261001-b26-backfill-interdig-final-audit). 모든 명령은 절대 경로(git -C, cd 금지).
쓰기 경로: skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py 하나(계획 N3.12.2 gmid-test-author 행 `A/tests/**`, tests/tools/** 제외).
입력: interface card docs/02-design/specs/20261001-b26-backfill-interdig-final-audit.interface.md(관찰 가능한 계약 4행 -- 피검은 run_matching_safety_with_finger_growth 하나,
      size_transistor·gm_gds_ratio 둘은 입력을 만드는 데만 쓴다), spec card의 '관찰 가능한 계약' 계약 1과 '이름' 목록, 'oracle 종류와 출처', '거부해야 할 입력'.
      oracle (d) = 승인 기록 .ai/approvals/20261001-b26-backfill-interdig-fix.md(읽어도 된다).
열람 금지: skills/analog-gmid-design/assets/*.py(엔진 소스 -- 특히 sizing_recipe.py), _drafts/** (오케스트레이터 시제품·측정 -- 기대값의 출처가 될 수 없다).
커밋: git -C <worktree> commit --trailer "Role: test" --trailer "Change-Id: 20261001-b26-backfill-interdig-final-audit" -m "test: …"
```

### 1.1 산출물(계약 1 그대로)

새 파일 하나: `A/tests/contracts/test_b26_backfill_interdig.py`. test 함수 이름은 `test_b26bf_`, 모듈 수준 도우미는 `_b26bf_`(또는 판정 도우미면 `assert`로 시작 -- 1.4)로 시작.

**합성 입력(구성 -- oracle (a) 입력)**: 행 하나 `{"seg1": [Ma, Mb, Mp]}`.
* `Ma = Transistor("Ma", "nmos", source="n2", drain="n1", gate="ga", n_fingers=1, finger_w=W0, stack_id="seg1")`
* `Mb = Transistor("Mb", "nmos", source="n4", drain="n2", gate="gb", n_fingers=1, finger_w=W0, stack_id="seg1")`
* `Mp = Transistor("Mp", "nmos", source="n2", drain="n5", gate="gp", n_fingers=1, finger_w=W0, stack_id="seg1")`
  -- 넷 `n2` 차수 3, `n1`·`n4`·`n5` 차수 1(홀수 차수 넷 4개 → euler-blocked). Mp가 Ma·Mb 사이에 끼어 '정리 전 행'과 '정리 뒤 행'의 3b가 다르게 된다.
* `W0`·사이징 항목 `S`: `r = size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=toy_lut, vds=0.6)`, `W0 = r.W`,
  `S = {"ID": r.ID, "W": W0, "L": 0.5e-6, "gm": r.gm, "gm_id": 12.0, "gds": r.gm / toy_lut.gm_gds_ratio(12.0, 0.5e-6, 0.6, 0.0), "kind": "nmos", "vds": 0.6, "vsb": 0.0}`.
* `ctx = SizingContext(sized={이름: dict(S) for 세 소자}, topology_path=<tmp_path의 합성 topology>)`. 합성 topology는 `tmp_path`에 쓰고 `supply_nets: ["vdd", "gnd"]`를 선언한다
  (`netlist` = 세 소자의 name·kind·source·drain·gate, `symmetry` = `{"matching_pairs": [], "dispositions": []}`, `schema_version: "2.0"`).
* 호출: `run_matching_safety_with_finger_growth({"seg1": 행}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, ctx, {"nmos": toy_lut}, {}, [], gm_id_bounds=(11.9, 12.1), max_rounds=m)`
  -- 앞 7개 위치 인자, 뒤 둘 키워드. 좁은 gm/ID 범위(사이징 값 12.0 둘레)로 핑거증가가 막혀 완화(`relaxed_pairs`)가 생긴다.
* 픽스처 `toy_lut`·`tmp_path`는 conftest·pytest 것을 쓴다.

**두 test(별개 함수 -- 한쪽 경로만 고친 엔진을 각각 잡는다)**:
| test | m | 경로 | 단언 |
|---|---|---|---|
| 루프 안 | 2 | 완화 뒤 다음 라운드에서 3c 실패가 완화 쌍뿐 → `relaxed_to_layout` 반환 | `res["unresolved_reason"] == "relaxed_to_layout"` 그리고 `CONSISTENT(res)` |
| 루프 뒤 | 1 | 첫 라운드에 완화하고 루프가 끝남 → 루프 뒤 반환 | `res["unresolved_reason"] == "max_rounds_exceeded"` 그리고 `CONSISTENT(res)` |

`CONSISTENT(res)`(계약 1): `[e["pair"] for e in res["relaxed_pairs"]] == [("Ma", "Mb")]`, 그리고 항목 `e`(쌍 `(a, b)`)마다 `res["audit"].checks` 중 이름이 `"3b."`로 시작하고 `f"[{a}/{b}]"`를 담은 체크가 **정확히 1개**이며 `e["interdig_ok"] is <그 체크>.ok`.

### 1.2 oracle 주석

각 test(또는 판정 도우미)에 `oracle 대조: 20261001-b26-backfill-interdig-fix (d) 사용자 결정 -- relaxed_pairs[i]["interdig_ok"]는 반환 audit(euler 정리 뒤 최종 물리 구조)의 3b 판정`.
기대값을 `True`/`False` 리터럴로 박지 않는다(관계 단언 -- 같은 반환 안 두 필드의 일치가 결정된 계약이다). 최종 rows 모양(`{Ma, Mb}` 행 등)도 단언하지 않는다(rows 불변은 계약 2, auditor 몫).

### 1.3 자기 점검(커밋 전, 판정 근거 아님)

* `C:/Python314/python.exe -P -m pytest <worktree>/skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py --rootdir=<worktree> -q --gmid-phase=2 --gmid-strict=`(bash면 `export APPDATA=C:/Users/HSLEE/AppData/Roaming`)
  → base 엔진에서 **2 failed, 둘 다 `AssertionError`이고 실패 문장이 `interdig_ok is …ok` 단언**이어야 한다(`unresolved_reason` 단언이나 쌍 목록·체크 개수 단언에서 실패하면 입력 구성이 틀렸다 -- 멈추고 보고).
* PYTHONHASHSEED 두 값(예 0·1)에서 같은 결과.
* `A/tests` 전체 한 번: 새 파일 두 test 외 실패 0.

### 1.4 V4 메모

* 피검 호출 한 번의 반환 안 두 필드를 비교하는 관계 단언이다. 키트 실측(base 판 `test_lint.py`, 같은 interface card): 피검 호출을 도우미(`_b26bf_run`) 안에 두고 test가 단언하는 모양은 `PASS`(판정 (2) `NO-SUBJECT`), test 함수 안에서 직접 호출하고 단언하는 모양도 `PASS`(판정 (2) `UNJUDGED`). 어느 쪽이든 (1) FAIL은 나지 않았다.
* 판정을 도우미에 몰아넣으면 test 함수 자신에 단언이 없어 (4) FAIL이 될 수 있다 -- test 함수 본문에 `unresolved_reason` 단언을 두거나, 도우미 이름을 `assert`로 시작하게 한다.

---

## 2. code-author 브리프(gmid-code-author, §12 순서 5)

```
역할: gmid-code-author. change id = 20261001-b26-backfill-interdig-final-audit (red-green, phase 2).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-code (브랜치 role/code/20261001-b26-backfill-interdig-final-audit, 부모 = test 커밋 T). 절대 경로만, cd 금지.
쓰기 경로: skills/analog-gmid-design/assets/sizing_recipe.py 하나. test·문서·레지스트리는 쓰지 않는다(새 def·삭제 def 없음 -- 레지스트리 갱신 없음).
입력: spec card·interface card·T의 test. test가 틀렸다고 보면 고치지 말고 dispute(<worktree>/docs/02-design/disputes/20261001-b26-backfill-interdig-final-audit.md)를 쓰고 같은 트레일러로 커밋한 뒤 멈춘다.
커밋: git -C <worktree> commit --trailer "Role: code" --trailer "Change-Id: 20261001-b26-backfill-interdig-final-audit" -m "…"
```

### 2.1 바꿀 것(최소 수정 -- 구조 변경 없음)

`run_matching_safety_with_finger_growth` 안에서:
1. 루프 안 `current_rows, result = repair_matching_safety(…)` **바로 다음 줄** `_backfill_interdig_ok(result)`(gate `0f23786` 11800)를 지운다.
2. 루프 뒤 `current_rows, result = repair_matching_safety(…)` **바로 다음 줄** `_backfill_interdig_ok(result)`(11879)를 지운다.
3. 정리 함수 `_finalize` 안의 `_backfill_interdig_ok(fixed_audit)`(11793)는 **남긴다**(모든 반환 경로가 `_finalize`를 거치므로 항목은 반드시 최종 audit으로 채워진다).
4. 거짓 서술 정리(코드 동작 아님, V 판정 밖): `_backfill_interdig_ok` 안 주석(11769~11770 "다음 라운드에 새로 계산된 audit_result가 나오면 그 3b 체크로 채운다")과 반환 docstring의 `"interdig_ok":bool|None`(11759) 설명을
   "반환 직전 `_finalize`가 계산한 최종 audit(euler 정리 뒤)의 3b 체크로 채운다"는 뜻으로 고친다. 주석·docstring 외 다른 줄은 바꾸지 않는다.

**하지 말 것**: `_backfill_interdig_ok`의 `if entry["interdig_ok"] is not None: continue`(11772~11773) 건드리기, `_finalize` 구조·반환 dict 키·완화 정책(3c 요구, `audit.ok`) 변경, 새 함수·새 인자, 광범위 `except`(V6), 숫자 리터럴 추가(V6).
(사전 측정: 위 1·2만 지운 엔진에서 계약 1 두 test green, `A/tests` 전체 회귀 없음 -- 0.5. 한쪽만 지우면 반대쪽 test가 실패한다 -- card '거부해야 할 입력'.)

### 2.2 자기 확인(판정 근거 아님)

* 새 test 두 개 PASS, `test_selftest_sizing_recipe.py`(L4e `interdig_ok is not None`)·`test_selftest_stick_diagram.py`·b26pre test 파일 PASS, `A/tests` 전체 실패 0.
* `git -C <worktree> diff T -- skills/analog-gmid-design/assets/sizing_recipe.py`: 삭제 2줄 + 주석·docstring 줄만.

---

## 3. auditor 브리프(gmid-verification-auditor, §12 순서 3·7)

```
역할: gmid-verification-auditor. change id = 20261001-b26-backfill-interdig-final-audit, evidence_type red-green, phase 2, approval 20261001-b26-backfill-interdig-fix(decision).
audit worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-audit (브랜치 role/audit/20261001-b26-backfill-interdig-final-audit).
모든 측정은 격리 복제본에서(§12-7): git clone --no-hardlinks --no-local -c core.longpaths=true --no-checkout <audit worktree> <scratch>/iso → git -C <scratch>/iso remote remove origin → checkout.
scratch는 새 C:/g<n> 하나만(다른 C:/g* 건드리지 말 것), 끝나면 그 폴더만 삭제. 셸 가드: set -euo pipefail, git -C <절대 경로>만, cd 금지. 끝나면 실제 저장소 git status·reflog 불변 확인.
게이트 코드는 base 판(= 승인 기록·spec card 커밋 뒤 gate master)을 git cat-file로 추출한 사본(캐시와 바이트 동일 확인), PYTHONPATH 앞, $PY -P.
작성자(test·code) 보고는 증거로 받지 않는다. 판정 기록 .ai/verification/20261001-b26-backfill-interdig-final-audit.json + scripts·out, Role: audit 커밋. V5 basis에 64자리 16진 금지.
```

### 3.1 순서 3(freeze·base 확인 → `base_check.json`)

* T 해시 고정. `git diff --name-only <base> <T>` = `skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py` 하나.
* **red**: T 복제본(base 엔진)에서 새 test 2개가 **둘 다 `AssertionError`로, `interdig_ok is <3b 체크>.ok` 단언에서** 실패하는지(키트 실측: `assert False is True`, 3b 체크 `3b. interdigitation[Ma/Mb] [참고용 -- 이 kind는 필수 아님]` ok=True, detail `seg1_seg1: 인접`).
  `unresolved_reason` 단언에서 실패하면 red 이유가 계약과 다르다 → test 결함으로 보고. PYTHONHASHSEED 두 값.
* **판별력**(card '거부해야 할 입력'): base 사본에 (i) 11800만 지운 엔진 → 루프 뒤 test만 실패, (ii) 11879만 지운 엔진 → 루프 안 test만 실패, (iii) `_finalize` 안 11793까지 지운 엔진 → 두 test와 L4e 실패. 셋 중 하나라도 test가 못 잡으면 test 결함.
* base 기준값: V2 회귀용 `A/tests` 전체(base = 착수 gate master), E-INST 두 회로(3.3), 계약 2 대조용 호출 결과(3.3).

### 3.2 순서 7(병합본 판정)

| V | 판정 | 근거·측정 |
|---|---|---|
| V1 | PASS 기대 | pytest 전체(base 판 `pytest_gate.ini`, `-k`·`--deselect`·`-x` 없음, `--gmid-phase=2 --gmid-strict=<base 판 merge_gate.strict_set>`). 키트 사전 수치(B34 위 모의 H, seed 1): 0.5 표 |
| V2 | PASS 기대 | red = 새 test 2개(base, `AssertionError`), green = 병합본 PASS. 새 test 외 base→병합본 판정이 바뀐 기존 test 0(계약 3, 특히 L4e) |
| V3 | 0.3 표 대로 | 착수 시점 V3 범위 규칙으로(범위 card `20260930-v3-changed-stmt-scope` 병합 여부를 기록). 대상 def = `run_matching_safety_with_finger_growth` 하나. 생존이 있으면 0.3 표의 분류와 대조 -- 등가 생존은 사용자 승인 기록(A1-a 형식) 없이 면제하지 않는다 |
| V4 | PASS 기대 | base 판 `test_lint.py --interface-card <interface card> --base <base> --head <T>`. `oracle 대조:` 줄 = 두 test의 기대(관계)가 승인 기록 `20261001-b26-backfill-interdig-fix` 결정 문장에서 왔는지, 피검 출력을 리터럴로 박지 않았는지 |
| V5 | PASS 기대 | base 판 `weakening_diff.py`(base→T, base→병합본): 기존 test·기준선 변경 0(새 파일 하나). → 3.4 DEC-40 |
| V6 | PASS 기대 | base 판 `source_lint.py`: 새 except·skip·숫자 리터럴 0(삭제 2줄 + 주석·docstring) |
| V7 | PASS(새 def 없음) | base 판 `reachability.py`: 새 def 0, `_backfill_interdig_ok`는 `_finalize` 안 호출로 계속 도달 |
| V8 | N/A(도입 4) | -- |
| V9 | N/A(도입 6b) | -- |
| V10 | PASS 기대 | card '재현할 수치'를 명령과 함께 재실행(`bf_repro` 상당 재현 -- auditor 독립 스크립트로) |

### 3.3 계약 2·library 대조(auditor 독립 스크립트)

* **계약 2(바뀌지 않는 것)**: 같은 합성 입력(m = 1·2·3·5, metrics 있음·없음)에서 base·병합본의 `rows`(행 키, 소자 이름·`n_fingers`·`stack_id`), `audit` 체크 이름·`ok`, `unresolved_pair`·`unresolved_reason`·`growth_rounds` 길이가 같고, 다른 것은 `relaxed_pairs[i]["interdig_ok"]`뿐.
* **library(E-LIB·E-INST)**: 이 def의 엔진 안 호출부는 `optimize_full_circuit_budget` 하나라 `load_topology`·`run_topology_pipeline`(E-LIB 9회로)은 닿지 않는다. 값이 바뀔 수 있는 곳은 harness 실행(`run_harness.run`)이다.
  E-INST 두 회로(`current_reuse_telescopic_ota`·`folded_cascode`)를 base·병합본에서 돌려 (a) `instance.json` 해시 같음 (b) 이 def 호출마다 `relaxed_pairs` 항목의 `interdig_ok` 전후 값을 기록(감싸기 계측 -- 반환을 읽기만). 키트 사전 수치는 0.4 표.
  달라지는 회로·쌍이 나오면 회로·쌍·전후 값을 판정 기록에 적는다(승인 기록 '재검토').

### 3.4 DEC-40 확인(기준 약화)

* 이 card는 기존 기대값·기준선을 바꾸지 않는다: 기존 test 변경 0(L4e `is not None` 그대로), 저장소에 `interdig_ok`를 담은 기준선 파일 0(`git grep interdig_ok`의 비코드 히트는 `.ai/context.md` 기록과 과거 판정 기록 AST 덤프뿐 -- test가 읽지 않는다), `instance.json`에 `interdig_ok` 키 없음(0.4).
* 관찰 가능한 반환값 변경 자체는 기준 약화가 아니라 사용자 결정(decision 승인 `20261001-b26-backfill-interdig-fix`)이 덮는다. 판정 기록 `approvals` = `["20261001-b26-backfill-interdig-fix"]`.
* library에서 값이 바뀌는 회로가 0이면(키트 사전 측정 0.4) 재생성할 기준선이 없다 -- DEC-40 승인 불필요를 근거(0.4 수치·V5 출력)와 함께 적는다. 0이 아니고 그 값이 어떤 기준선·보고 산출물에 들어가면 멈추고 오케스트레이터에 보고(DEC-40 승인 필요).

---

## 4. 순서 요약(오케스트레이터)

B34 병합·정리 → b26pre 병합·정리 → `role/*` 0개 → **착수 0단계**(머리) → 0.7 확인 → 0.8 D(승인 기록)·B(spec+interface) → push 단독·전체 출력 확인 →
§12 순서 1(test worktree) → test-author(1절) → 순서 3 auditor(3.1) → 순서 4 code worktree(부모 T) → code-author(2절) → 순서 6 병합 → 순서 7 auditor(3.2~3.4) → 순서 8 push → 정리 →
**B26-1 인계**: 이 card 병합본에서 B26-1 모의 head·V3 대상 수('301')·Q1 문안 재측정(E6 finger growth 행 6 → 4, AST 경로 순번 당겨짐 -- card '결정 필요 항목').
