# 독립 검토 -- backfill 결함 card 키트 (`20261001-b26-backfill-interdig-final-audit`)

검토자: 독립 reviewer(작성자 아님). 2026-10-01. 저장소 읽기 전용, scratch `C:/g140`(끝나고 삭제), 측정은 자체 복제본 `C:/g140/r`(origin 제거, 빈 hooksPath).
대상: `draft_b26_backfill_audit.spec.md`, `approval_20261001-b26-backfill-interdig-fix.md`, `b26_backfill_briefs.md`, `b26bf_kit/`(scripts + out/).
gate `master` = `0f23786`(로컬 `gate/master` 같음). `a796468`과 `skills tools workspaces` 차이 0 확인.

## 판정

**PASS(착수 가능 -- 조건부)**. B(차단) 0, S(수정 권고) 2, minor 4.
핵심 주장 5개(승인 원문, 계약·부분 수정 거부, library 무변화, V3 수치, V4 모양)를 자체 복제본에서 독립적으로 다시 재서 모두 키트와 같았다.

## 1. 승인 기록 원문 대조(세션 jsonl, AskUserQuestion header "U-BF")

자체 스크립트로 jsonl에서 header `U-BF`인 tool_use 1건(`toolu_01UB8MYiKoGaacm4JJEA3HBd`, 2026-10-01T10:17:21Z = 19:17 KST)과 그 tool_result(10:19:30Z = 19:19 KST)를 뽑아 승인 초안과 바이트 단위로 비교했다.

| 항목 | 결과 |
|---|---|
| 답 `결함으로 고침 (Recommended)` = 선택지 0의 label, `> ` 인용 줄과 같음 | True |
| tool_result content에 `="결함으로 고침 (Recommended)"`가 들어 있음 | True |
| 질문 문장 전체가 `"…"` 인용으로 초안에 그대로 있음 | True |
| 선택지 3개 `"label" -- "description"` 그대로 | 3/3 True |
| 오타 `쟽니다` | jsonl: 질문 1 + 선택지 0 설명 1. 초안: 2. **보존됨** |
| 시각 19:17 / 19:19 KST | 맞음 |
| `merge_gate.py parse-approval`(gate master 판) | 통과: `target_kind decision`, `target_list ["U-BF-BACKFILL-INTERDIG"]`, `diff_path []`. LF, BOM 없음, HTML 주석 없음 |

## 2. 계약 1: 두 경로에서 반환 interdig_ok == 반환 audit 3b, 잘못된 수정 거부

test는 브리프 1절만 보고 자체 작성했다(`_drafts` 시제품은 쓰지 않음). 베이스는 a796468 + B34 head(`b34_kit/mk_head.py`를 내 복제본 경로로 바꿔 적용)이고, 변이마다 같은 test 파일을 넣었다. 실행: `test_b26_backfill_interdig.py` + `test_selftest_sizing_recipe.py`, PYTHONHASHSEED 0·1. 두 seed 결과가 같았다.

| 엔진 | loop_inside (m=2) | after_loop (m=1) | L4e (`test_s016…`) | 실패 문장 |
|---|---|---|---|---|
| base | FAIL | FAIL | pass | `assert False is True`(3b `seg1_seg1: 인접` ok=True) |
| fix(11800·11879 삭제) | pass | pass | pass | 68 passed·2 xfailed |
| 11800만 삭제 | pass | **FAIL** | pass | `False is True` |
| 11879만 삭제 | **FAIL** | pass | pass | `False is True` |
| 11793(`_finalize` 안)까지 셋 다 삭제 | FAIL | FAIL | **FAIL** | `None is True` / L4e `is not None` |

card '거부해야 할 입력'의 세 줄은 그대로 맞다. 계약 2(바뀌지 않는 것)도 base와 fix에서 m=1·2·3·5, metrics `{}`와 `{"A0_dB":40}` 8개 조합으로 대조했다. rows 키(`seg1_seg0`, `seg1_seg1`), 체크 이름과 ok, unresolved_pair·reason, growth_rounds 길이가 전부 같았다. 다른 것은 `interdig_ok`(False→True) 하나였다.

## 3. library 주장(a796468 + B34 head ± fix, PYTHONHASHSEED 0)

자체 감싸기 계측 `libm.py`로 `run_harness.run`을 4개 SPECS 회로에 돌렸다. 반환만 읽었다.

| 회로 | base: 호출 / 완화 항목 (interdig_ok, 최종 3b) | fix | instance.json(정렬 JSON sha) |
|---|---|---|---|
| current_reuse_telescopic_ota | 1 / M4a·M4b (True, [True]), M3a·M3b (False, [False]). 사유 `growth_not_applicable` | 같음. core 해시 `702199b7…` 같음 | 1b9a4d4c… = 같음(키트와 같은 값). `interdig_ok` 키 없음 |
| folded_cascode | 1 / 0 | 같음 | e690b95d… = 같음 |
| two_stage_ota | 0. harness ValueError(stage1_out KVL) | 같음 | 산출 없음 |
| nmcnr_amplifier | 0. ValueError(stage2_diode_ref 예산) | 같음 | 산출 없음 |

정적 확인: 이 def의 엔진 안 호출부는 `sizing_recipe.py:9369` 하나뿐이다(`optimize_full_circuit_budget`). 나머지 5회로는 SPECS에 없다.
결론: 9회로에서 값 변화 0. 파일럿의 2개 완화 쌍은 base에서 이미 최종 3b와 같다. 키트 주장과 일치한다.

## 4. V3(gate master 판 `mutate_changed` 함수 + `v3scope_kit/scope_proto.py` N2w, base = BP(B1 + b26pre 시제품 test), head = BP + fix + 내 test)

자체 병렬 replica(작업 사본 8개)로 측정했다. 기준 실행 rc 0, 인벤토리 71.

* 대상: 97, N2w 4. **N2w 4개 모두 죽음**: `stmt_delete:body[9]`(11797), `body[9].body[1]`(11800), `body[11]`(11878), `early_return:body[1]`(11762).
* 현재 도구 규칙(def의 변이 전부)으로는 **78 죽음 / 19 생존**. 생존 id 집합이 키트 `v3merged_bf.json`의 `survived`와 정확히 같다. 줄 분류(11715 기본값 6, 11772·11773 가드 2, 11778 break, 11796, 11801, 11810, 11816 ×3, 11832, 11849, 11870·11871)도 브리프 0.3 표와 같다.
* 순서 요건: gate master에는 아직 범위 card(`20260930-v3-changed-stmt-scope`), B34, b26pre가 어느 것도 없다(`ls-tree` grep 0). 그래서 지금의 gate 도구로 판정하면 V3 FAIL(생존 19)이다. **이 card는 범위 card 병합 뒤에만 착수할 수 있다**는 card의 문장은 옳다. 다만 아래 S1을 본다.

## 5. oracle (d)와 V4

* oracle (d)는 승인 기록 id이고, 결정 문장이 계약 1의 관계 단언과 일치한다. 기대값을 리터럴로 박지 않는다. 입력 (a) 구성은 홀수 차수 넷 4개와 gm/ID 11.9~12.1이다. 타당하다.
* interface card(gate 판 `interface_card.py`, 이 card 사본): 관찰 가능한 계약 4행, 신규 0행. 키트와 같다.
* V4(gate master `git archive tools/gates`의 `test_lint.py`, `--base BP --head T`):
  * 내 test(판정 도우미 `assert_b26bf_consistent` + test 본문의 reason 단언): PASS, (2) NO-SUBJECT 4건.
  * 도우미 이름이 `assert`로 시작하지 않고 test 본문에 reason 단언이 있으면: PASS, NO-SUBJECT 2건(브리프 수치와 같음).
  * 도우미 이름이 `assert`로 시작하지 않고 test 본문에 단언도 없으면: **(4) FAIL** 2건. 브리프 1.4 경고가 맞다.
  * 대조: `interdig_ok is True`를 리터럴로 박은 변형도 V4 **PASS**다. 관계 단언인지 리터럴 단언인지는 기계로 가려지지 않고, auditor가 `oracle 대조:` 줄과 단언 모양을 읽어야만 걸린다. 브리프 3.2 V4 행이 이 일을 auditor 몫으로 적은 것은 맞다(minor m3).
* V2 사전 수치를 재측정했다(git 복제본, seed 1, 전체 `A/tests`):
  * T(BP + test): **2 failed(새 test 2개)·888 passed·15 xfailed**
  * HB(+ fix): **890 passed·15 xfailed**
  * 브리프 0.5와 같다.

## 지적

### S1 -- 착수 0단계에 'V3 범위 card 병합' 확인이 없다
* 문제: card와 브리프 0.3은 범위 card 전에 착수하면 V3 FAIL(생존 19)이라고 적었다. 그런데 0단계 (가)~(라)와 0.7은 B34·b26pre의 `audit:` 커밋만 본다. 범위 card는 'B34 card의 판정 규칙 순서'를 통해 간접으로만 걸려 있다. N2w 수치는 시제품 `scope_proto.py` 기준이기도 하다.
* 권고: 0단계에 (마)를 추가한다. 예: `git -C "$R" ls-tree -r --name-only gate/master -- .ai/verification/ | grep -c 20260930-v3-changed-stmt-scope`는 ≥1이어야 한다. 병합된 `mutate_changed.py`로 대상 수를 다시 재고(0.3), 4가 아니면 멈춘다.

### S2 -- 브리프 0.1 마지막 행과 0.2 첫 항목이 현재 승인 초안과 모순된다(낡은 서술)
* 문제: 0.1 행은 `user_decisions.md`의 원문을 `잽니다`라고 적고, 0.2는 초안을 `잽니다`로 고쳤다고 적는다. 그러나 현재 승인 초안은 `쟽니다` 2곳이고, 이것이 jsonl 원문과 바이트 단위로 같다(§1). `user_decisions.md` 60행 정정도 jsonl 원문이 `쟽니다`라고 한다.
* 위험: 0.7-1을 따르는 오케스트레이터가 0.2를 믿고 `잽니다`로 '정정'할 수 있다.
* 권고: 0.1·0.2를 "jsonl 대조 결과 원문은 `쟽니다`(질문 1, 선택지 0 설명 1), 초안은 원문대로 되돌림 완료"로 고친다. 0.7-1은 '완료'로 표시한다.

### minor
* **m1 -- '모든 반환 경로'는 test가 아니라 구조로 보장된다.**
  * 계약 1의 이름은 '모든 반환 경로'인데 test는 relaxed_to_layout와 max_rounds_exceeded 두 경로만 고정한다. 파일럿이 실제로 지나는 `growth_not_applicable`과 success·pair_not_found 반환은 고정하지 않는다.
  * 자체 반례 엔진: 11879만 지우고 11800은 남긴 채, relaxed_to_layout 반환 자리에서만 interdig_ok를 None으로 되돌린 뒤 재backfill한다. 이 엔진은 새 test 2개와 selftest를 모두 통과한다(68 passed).
  * 이 엔진이 다른 경로에서 틀린 값을 내는 입력이 실재하는지는 만들지 않았다. 그래서 B가 아니다.
  * 권고: card '구현 방식'에 '정리 함수 안 호출만 남기는 방식(모든 반환이 `_finalize`를 거침)' 쪽으로 구조 근거를 한 줄 적는다. 또는 계약 문구를 '두 경로(test) + 나머지는 `_finalize` 경유로 구조 보장'으로 정확히 적는다.
* **m2 -- 키트 출력과 스크립트가 맞지 않는다.**
  * `b26bf_kit/out/lib_*_elib.json`에는 `"pipeline": "TypeError: run_topology_pipeline() missing … 'sizing_overrides'"` 필드가 있다. 현재 `lib_measure.py`의 elib 모드는 그 필드를 만들지 않는다.
  * 출력은 이전 판 스크립트에서 나온 것이다. 결론은 정적 사실(호출부 9369 하나)과 einst 계측으로 서 있어 영향은 없다.
  * 권고: 출처 문장을 정정하거나 elib를 다시 돌린다.
* **m3 -- V4는 리터럴 단언을 막지 못한다.** §5에서 본 대로 리터럴 단언도 V4 PASS다. 관계 단언 요구는 auditor 판독에만 걸려 있다. 브리프 3.2 V4 행이 이미 그렇게 적었으니 표시만 한다.
* **m4 -- 범위 서술과 재생성 해시 메모.**
  * card는 이 def가 `run_harness.run`만으로 닿는다고 적었다. 실제로는 `achievable_metric_bound`(sizing_recipe 7797)와 tests/probes·workspaces 스크립트도 `optimize_full_circuit_budget`을 거쳐 이 def에 닿을 수 있다. library 기준선 결론은 바뀌지 않는다.
  * 재생성 instance.json의 raw 해시(`7dc9f2e2…`, `8cd006a5…`)는 a796468에 커밋된 파일(`586a2912…`, `d4ce00d7…`)과 다르다. base와 fix 모두 같게 다르므로 이 card와 무관하지만, auditor E-INST 비교는 커밋 파일이 아니라 base 재생성과 해야 한다.

## 재현(자체 스크립트, scratch에서 실행 후 삭제)
* `ext.py`/`cmp.py`: jsonl 추출, 바이트 비교
* `mk_head.py`(b34_kit 사본, 경로만 변경) → B1
* `mk_variants.py`: base, fix, only11800, only11879, all3 → `run_variants.sh`
* `c2.py`: 계약 2
* `libm.py`/`run_lib.sh`: library
* `mk_v3.py` + `v3rep.py`: V3
* `v4var.py`: V4 변형
* `fs.sh`: 전체 회귀
* `mk_sitepatch.py`: m1 반례
