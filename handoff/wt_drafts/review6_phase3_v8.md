# 6차 독립 검토 -- Phase 3 `30-module-split` 초안 v7 → v8 델타 (승인 요청 전)

검토자: 독립 검토 agent(작성자·이전 검토자 아님). 저장소 읽기 전용, 상태 변경 git 없음.
측정: `C:/g125/repo`(`git clone --no-hardlinks`, `0f23786`)와 그 안의 합성 브랜치(스크래치 전용), 끝난 뒤 `C:/g125` 삭제. Python `C:/Python314/python.exe -B`, `APPDATA`·`HOME` export.
**루프 종료 규칙**: (a) v8 변경이 만든 결함, (b) 5차 검토 항목 중 실제로 풀리지 않은 것만 적는다. 닫힌 항목은 다시 열지 않는다.

검토 대상 판(sha256 앞 16자리, 검토 시점 재계산 = 승인 질문 '대상 판 해시'와 같음): design v8 `29ae10e99ff4b40d`, G1 `3a99df21414d6e99`, T0 `35f7e3e7850a2847`, D0a `1f9592d491303132`,
문서 개정 `c775320e6c2b7e1a`, `e_inst_p3.py` `7d26134ad00ec504`, 승인 질문 `b0e4a9061eff2093`, revision log `67aaf3f9cb32bc6a`.

## 판정

**막는 것 1건(승인 질문 분류), 고칠 것 3건 -- 고친 뒤 승인 요청 가능.** 모두 문장 수정이다. 판정 명령(§10 bash)에서 새로 생긴 약화 구멍은 없다.

* **N1**: E5 비교 판을 'Phase 2 DoD'에서 'B0(M1 base)'로 바꾼 것은 사용자가 Phase 2에서 **고르지 않은 대안**(card 판정 기록 사슬로 갈음)과 같은 모양이다. 그런데 승인 질문은 이것을 '원칙 기본값'(질문에 넣지 않은 것)으로 분류했다. '기준에 닿는 기본값'으로 옮기고 대안을 붙여야 한다.

---

## 1. 재측정 (믿지 않고 다시 잼)

| 항목 | 실행 | 결과 |
|---|---|---|
| B2 작성자 합성 | `p3v6_order_shim_sim.py … bottom7 pull` → `p3v8_e3b_synth.py`(경로 가드만 `g125`로 바꾼 사본) → `p3v8_sec10_selftest.sh`(v8·v7 문서에서 블록을 잘라 실행) | 브랜치 해시가 작성자 json과 같다(`sd_unread_reexported_n` 51, `v7_overdropped_reexports` 11개 동일). **v7 블록 @ b2head: `pre_existing=4` + `E3b PASS`(결함 재현). v8 블록: `pre_existing=1` + FAIL 세 줄**(`dyn_reader.py:3 <동적 이름>`, `parse_err.py:0 <PARSE-ERROR>`, `star_reader.py:1 *`). base(HEAD = B0)에서 `INVALID`, `syn/m9`에서 `PASS`(`moved_out=62 base_files_reading_moved_out=31 pre_existing=1`). **B2 해결** |
| B2 내 합성(9개 reader) | `0f23786` + `workspaces/yy/` 9파일(아래), H = SD의 `find_structural_symmetry_candidates` def를 새 파일로(재수출 없음) + `structural_symmetry_probe.py`만 갱신. v8 E3b 블록 그대로 | **잡음 6**: 여러 줄 `from stick_diagram import (\n load_topology,\n X,\n)`, 같은 모양 `as` 별칭, `importlib.import_module("stick_diagram").X`, `getattr(importlib.import_module('stick_diagram'), 'X')`, `__import__('stick_diagram').X`, 함수 안 `import stick_diagram as q; return q.X`. **놓침 3**: `m = sys.modules['stick_diagram']; m.X`, `get = lambda: importlib.import_module('stick_diagram'); get().X`, `from importlib import import_module as im; im('stick_diagram').X`. 셋 다 v7부터 있던 식의 한계라 v8 결함이 아니다(m-a) |
| F2 모의 정정(49줄·12파일) | 위 selftest의 `syn/f2drop` 시나리오 출력 집계 | **FAIL 49줄, 12파일, V1 밖 7**(`run_harness.py`, `structural_symmetry_probe.py`·`rerun_symmetry.py`·`stick.py`·`smoke_run_harness_session20.py`, `check_box_shape*.py` 2), V1 수집 test 5. design §2.2 목록과 같다. 재현 |
| S2(깨지는 판정 기록 스크립트) | 같은 selftest '제외 없음' 시나리오 | `.ai/verification/**` FAIL은 `e_lib_inst.py:35 save_instance_json`, `diff_dup.py:17 _import_analog_grammar`·`:32 _kcl_and_matching_edges` 3줄·2파일. `probe_stage_partition.py` 4줄. 6개 `e_lib.py` 0. 문서 수치와 같다 |
| S1 동등(스폿) | `0f23786`에서 `e_inst_df36.py`(B0 판 사본)와 `e_inst_p3.py`(sha `7d26134a…`)를 `folded_cascode`로 실행 | 두 출력의 다른 키 = `["engine_origin"]` 하나(p3 = df36 셋 + `topology_library`), `raw_sha256` 둘 다 `ef3cd996…`(부록 F3v8과 같음), stdout 사본 바이트 동일. 파일럿과 F1 모의는 다시 돌리지 않았다(약 15분 이상) |
| S3 사실 | `0f23786`의 `merge_gate.py`, 승인 기록, 계획, card 초안 | 532~549 = `rule10_phase` 맞음. 1008~1010 = `want = …`·`if phase_tok != [phase]`·실패 추가 맞음(`if strict_needed is not None:` 1007행 안). 승인 기록 27·28행 인용 맞음. 계획 1001행 인용 맞음. B34·B26-1·b26pre 초안 `phase: 2` 맞음. **단 N3·N4** |
| PT3·두 번 실행 | §10 머리 `PT3()`, E4·E5 bash, E4·E5 표 | `PT3`는 10 §10 `PT`에서 `--gmid-phase=3`만 바꿨다(인터프리터만 `$PY` 대신 같은 실행 파일 직접, `PYTHONPYCACHEPREFIX`가 있어 `-B` 유무는 영향 없음). E5 = `PT3` 전체 + `PT3 --gmid-dod` 전체, 표에 "둘 다 실패 0(수집 1개 이상)". E4는 파일 하나를 `PT3`로 한 번 돈다(같은 파일이 E5 두 실행에 들어 있어 빠지는 것 없음). T0 무동작 입력 `PT3`. **B1 해결** |
| 해시·m6 | `sha256sum` | 대상 판 6개가 승인 질문의 값과 같다 |

`git -C <repo> status --short` 출력 해시는 검토 전후로 같다(`168fd530…`).

---

## 2. Blocking

### N1. E5 비교 판 B0는 '기준에 닿는 기본값'인데 승인 질문은 '원칙 기본값'으로 분류했다 (S1 후속, v8 결함)

* **v7 문구는 승인된 적이 없다.** v7 E5 "E-LIB·E-INST 재측정이 Phase 2 DoD와 같은 해시"는 초안 문장이다. 계획 N6.3(1031행대)은 "동작 보존 Phase(1~3)는 실행 가능한 회로 전부에서 equivalence"라고만 적고 비교 판을 정하지 않는다. N6.2 Phase 3 DoD 행도 E-LIB·E-INST 비교 판을 적지 않는다. 그래서 **승인된 기준 문구를 바꾼 것은 아니다.**
* **승인된 선례는 반대쪽을 골랐다.** `.ai/approvals/20260930-phase2-e4-baseline.md` 질문 맥락: "기본안 = da03c0e와 Phase 2 마지막 병합본을 같은 경로에서 비교하고 `topology_ref`만 DF-36 계약값으로 판정, 대안 = card별 판정 기록 사슬로 갈음". 사용자 원문은 "둘다 기본안으로 진행해"였다. 그 결과 design 20 §10 E4는 "비교 기준을 Phase 1 DoD 대상 커밋 da03c0e의 같은 경로 실측으로 바꾸고, 의도적으로 바뀐 `topology_ref` 하나만 DF-36 계약값으로 따로 판정한다"가 됐다. 즉 직전 Phase DoD 판에서 시작하는 전체 창을 쓰고, 의도된 변경은 그 필드만 따로 판정한다.
* **v8 E5는 대안 쪽이다.** E5 표: "Phase 2 DoD 판과의 연결은 Phase 2 DoD 판정 기록과 B34·B26-1·그 사이 card의 판정 기록이 잇는다". Phase 2 DoD~B0 구간의 엔진 red-green card는 B34(`ImportError` 동작 변경), B26-1(`meta["rails"]`), 그리고 아래 N3의 backfill card(`interdig_ok`)다. 이 구간을 DoD 동작 보존 비교가 덮지 않는다. 승인 질문의 (가)안대로면 이 card들은 `phase: 3`인데 Phase 3 DoD의 비교 창 밖에 있다.
  v8이 든 근거 "원리상 성립하지 않았다"는 raw 해시를 그대로 같다고 볼 때만 맞다. 선례처럼 의도된 필드를 따로 판정하는 안(carve-out)은 검토하지 않았다.
* **질문 위치**: 승인 질문 UD-0 본문에는 "동작 보존(E-LIB·E-INST)은 Phase 3 이동 직전 판과 비교합니다"라는 한 문장만 있다. D-28 전체는 '질문에 넣지 않은 것(원칙 기본값)'에 들어 있다. '기준에 닿는 기본값' (a)·(b)에는 없다.
* **고칠 것(문장)**: UD-0 '기준에 닿는 기본값'에 (c)를 더한다. 내용: "동작 보존 비교 판 = B0(M1 base). Phase 2 DoD~B0 구간(B34·B26-1·backfill)은 각 card 판정 기록이 잇는다 -- Phase 2 승인 `20260930-phase2-e4-baseline`의 대안 쪽". 대안도 적는다: "Phase 2 DoD 대상 커밋 대 마지막 병합본, 의도된 변경(B26-1 `meta["rails"]` 등)만 그 card 계약값으로 따로 판정 -- 선례 기본안 쪽". 수정 요청 선택지 예시에 (c)를 넣고, '질문에 넣지 않은 것'의 D-28 문장에서 비교 판 부분을 뺀다. design D-28 (e)의 "원리상 성립하지 않았다"도 "raw 해시 그대로는 성립하지 않는다(선례식 따로 판정 안은 대안)"로 좁힌다. 어느 쪽을 기본안으로 둘지는 오케스트레이터 몫이고, 이 검토는 결정하지 않는다.

---

## 3. Should-fix (모두 v8에서 새로 쓴 문장)

| # | 위치 | 발견(근거) | 고칠 것 |
|---|---|---|---|
| N2 | design §10 E2 표 행(1006행) | v8은 E2 앞에 `git diff --quiet "$B0" HEAD -- tools/gates tools/migrate \|\| echo "E2 INVALID: …"`를 더했다(D-27 사후 강제, S6). 그러나 E2 **통과 기준 행**에는 `INVALID`도 `tools`도 없다(`grep -c` 0). §10 머리 규칙은 "표에는 ID와 통과 기준만 둔다"이다. 그래서 표를 그대로 적용하면 이 줄이 출력돼도 E2 PASS가 된다. D-27·§9.1이 '강제 수단'으로 든 확인이 판정에서 빠진다(fail-open) | E2 행 ① 앞에 "`E2 INVALID` 줄 없음(B0..HEAD `tools/gates`·`tools/migrate` 무변경 -- D-27)"을 더한다 |
| N3 | 승인 질문 A2-③ 사실 (3)·(가), design §11-11·§9.2 A2-③ 행 | **card 목록이 빠졌다.** `_drafts/draft_b26_backfill_audit.spec.md`(id `20261001-b26-backfill-interdig-final-audit`, `phase: 2`, red-green, `sizing_recipe.py` 엔진 변경, 19:00 작성 -- v8 승인 질문 19:39보다 앞)도 Phase 2 DoD 뒤에 병합된다(`b26pre_revision_log.md` m5 순서 'B34 → b26pre → 이 card → B26-1'). `pending_questions.md` Q-B34-PHASE 보탬도 "B34·B26-1·b26pre·backfill card"라고 적는다. 그런데 질문은 "card 초안 셋"이고, (가)는 "세 card 초안의 `phase`를 3으로"라고 쓴다. 이대로 답을 받으면 backfill card만 `phase: 2`로 남는다. design 확정 순서(§8.1 머리)에도 이 card가 없다. D0b 전에 병합되므로 §6.4 재측정이 흡수해 판정식은 같다 | 사실 (3)과 (가)를 네 card로 고친다(backfill은 승인 ③의 대상이 아니므로 "계획 1001행으로 같은 값"이라고 한 줄 덧붙인다). §8.1 확정 순서의 "B26-1(앞선 test 보강 card 포함)"에 backfill card(U-BF 승인 시)를 더한다. N1의 구간 card 목록에도 넣는다 |
| N4 | 승인 질문 A2-③ 사실 (4), design §11-11 | **"어느 값으로도 통과"는 맞지만 영향 문장이 빠졌다.** `0f23786` `merge_gate.py` 1042~1043행: `if c["phase"] == card["phase"]: keys \|= set(c["activated_ic_case"])`(같은 Phase card의 엄격 집합). 1210~1213행: old conftest에 `--gmid-phase`가 있으면 `strict_set`을 계산해 `v1_command_check(…, phase=card["phase"])`에 넘긴다. 그래서 phase 값이 이 card들의 V1 `--gmid-phase=`·`--gmid-strict=` 값을 바꾼다. Q-B34-PHASE 보탬(Phase 4 6차 검토 m-2)이 이미 이것을 기록했다. 질문은 1008~1010만 인용해 '판정에 영향 없음'으로 읽힌다 | (4)에 한 문장을 더한다: "다만 값에 따라 이 card들의 V1 명령 `--gmid-phase`·`--gmid-strict`(같은 Phase card의 엄격 집합, 1042·1213행)가 정해진다 -- 거부 위험은 없고 판정 기록의 V1 옵션이 그 값을 따른다". §11-11도 같은 문장으로 고친다 |

---

## 4. Minor (차단 아님)

| # | 내용 |
|---|---|
| m-a | (v7부터 있던 E3b 식의 한계 -- 루프 규칙상 참고) 내 합성에서 `sys.modules['stick_diagram']` 대입 별칭, lambda가 돌려주는 모듈, 이름을 바꾼 `import_module`(`im(…)`) 세 모양을 E3b가 놓쳤다. D-24에는 같은 '이름 바꾼 호출' 한계가 E3 몫으로만 적혀 있다. D-26 한계 목록에 이 세 모양을 한 줄 더한다. `0f23786` 노출: 추적 `.py`에서 `sys.modules[…stick_diagram…]`·`import_module as`·`from importlib import import_module` 0건 |
| m-b | `e_inst_p3.py`의 출처 확인은 `__file__` 디렉터리가 `…/skills/analog-gmid-design/assets`로 끝나는 모듈만 본다. 그런 경로가 아닌 곳(예: 캐시 디렉터리 사본)에서 로드된 엔진 모듈은 그냥 지나간다. df36은 이름 셋을 경로와 상관없이 확인했다. 또 확인 시점이 `mod.run()` 전이라 run 안에서 처음 import되는 MOD는 보지 않는다(df36도 run 전 확인이지만 대상이 import 시점 모듈 셋이었다). 실제 위험은 낮다. 그래도 D-28의 "한 곳만 다르다·동등"에 이 범위 차이를 한 줄 적거나, 확인을 run 뒤로 한 번 더 둔다 |
| m-c | revision log S1 행의 "`draft_b26_1.spec.md` 91행"(`rails`)은 지금 판에서 58행이다(b26_1 초안이 20:01에 다시 바뀌었다). design 본문은 줄 번호를 쓰지 않아 영향 없음 |

---

## 5. 5차 검토 항목 상태

| 5차 # | 상태(이번 확인) |
|---|---|
| B1 | 해결(§1 PT3 행) |
| B2 | 해결(작성자 합성 재현 + 내 합성 6/9 탐지, 놓친 3은 v7부터 있던 한계 m-a) |
| S1 | 측정 명령은 해결(F1 뒤 df36 `KeyError`는 근사 모의로 보였고, F1 전 동등은 스폿으로 확인). **비교 판 변경의 질문 분류는 N1** |
| S2 | 해결(2파일·3줄 재현) |
| S3 | 항목을 나눈 것은 해결. **사실 목록 N3·N4** |
| S4·S5 | 해결(diff 확인, 추적 안 된 경로는 메인 저장소 `git status`의 `??` 줄과 같음) |
| S6 | 범위 확대는 해결. **강제 줄이 통과 기준에 없음 N2** |
| m1~m7 | 반영 확인(m1 해시 일치, m3 export, m5 '둘 예정', m6 `0f23786` 문장, m7 D-24) |

## 6. 정리

N1(승인 질문 UD-0에 (c) 추가), N2(E2 행 한 줄), N3·N4(A2-③ 사실 문장)를 고치면 승인 질문을 올릴 수 있다. 판정 명령의 새 약화 구멍은 N2 하나이고 표 문장으로 닫힌다. E3b·PT3·E5 bash는 재실행에서 기대대로 동작했다.
재현 자료: `C:/g125`(삭제함). 브랜치는 작성자 스크립트 사본(경로 가드 `g125`)으로 만든 `syn/*`, 내 합성 base `295331c`·head `1316a6d`(`workspaces/yy/` 9파일 + def 이동)다.
