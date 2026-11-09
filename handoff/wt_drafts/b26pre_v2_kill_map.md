# b26pre card v2가 죽이는 B26-1 생존 변이 -- 대응표

작성 2026-10-01. 대상: `_drafts/b26_1_survivor_question.md` Q1('계획된 계약으로도 죽지 않는 V3 대상 변이 24개'), `_drafts/b26_1_revision_log_v4.md` §3(N2w 생존 27 = `_metric_kcl_residual` 3 + 남는 24).
이 문서는 그 두 파일을 고치지 않는다(다른 agent가 대조 중). B26-1 질문을 줄일 때 쓰는 대응만 적는다.
측정: `_drafts/draft_b26pre.spec.md` v2 시제품(17 test), gate `a796468` 사본과 +B34 사본, base 문장 단위(`_drafts/b26pre_v2_scripts/kill_v2.py`, scratch C:/g106 -- 삭제).
gate `master`는 그 뒤 `0f23786`으로 움직였으나 `skills` 변경이 없어(`git diff --quiet a796468 0f23786 -- skills`) 줄 번호·수치는 그대로다. card v3의 계약 10 약한 단언('Mx1·Mx2 중 정확히 하나')도 씨앗 6문장을 6/6 죽인다(`0f23786` 사본 재측정, 아래 §3).

## 1. Q1의 N2w 생존 24개 -- 문장별 대응

head 줄은 v4 모의 head(`b26pre_scripts/out/survivors.txt`), base 줄은 a796468.

| Q1 묶음 | head 줄 | base 줄 | 문장 | b26pre v2 판정 | Q1에서 |
|---|---|---|---|---|---|
| LUT 없는 repair(4) | 9411 (`_evaluate_row_split`·바깥 def 두 변이) | SR 9404 | `repaired_rows, repaired_audit = repair_matching_safety(...)` | 죽음(계약 1) | 빠짐 |
| 〃 | 9413 (두 변이) | SR 9406 | `pr = dict(pr, repaired_rows=..., repaired_audit=...)` | 죽음(계약 1) | 빠짐 |
| euler-blocked fixup(3) | 11704 | SR 11696 | `split = find_min_crossover_layout_with_branch_composite(...)` | 죽음(계약 2) | 빠짐 |
| 〃 | 11706 | SR 11698 | `by_name = {...}` | 죽음(계약 2) | 빠짐 |
| 〃 | 11708 | SR 11700 | `for seg_idx, seg in enumerate(split["segments"]):` | 죽음(계약 2) | 빠짐 |
| finger growth(6) | 11809 | SR 11800 | `_backfill_interdig_ok(result)`(루프 안) | **생존 -- 등가 아님, 결함 의심** | U-BF로 이동 |
| 〃 | 11810 | SR 11801 | `if result.ok:` | 죽음(계약 3(c)) | 빠짐 |
| 〃 | 11886 | SR 11877 | 루프 뒤 `repair_matching_safety(...)` | 죽음(계약 3(a)) | 빠짐 |
| 〃 | 11888 | SR 11879 | `_backfill_interdig_ok(result)`(루프 뒤) | **생존 -- 등가 아님, 결함 의심** | U-BF로 이동 |
| 〃 | 11889 | SR 11880 | 루프 뒤 `_finalize(...)` | 죽음(계약 3(b)) | 빠짐 |
| 〃 | 11890 | SR 11881 | 루프 뒤 `return {...}` | 죽음(계약 3(a)(b)) | 빠짐 |
| E7 `run_full_circuit_audit`(2) | -- | SD 6892 | `for … in mc["current_mirror"].items():` | 죽음(계약 4) | 빠짐 |
| 〃 | -- | SD 6894 | `for … in mc["diff_pair"].items():` | 죽음(계약 4) | 빠짐 |
| E7 `resolve_stack_layout`(1) | 6578 | SR 6573 | `if refined is not None and refined.get(...)` | 죽음(계약 5) | 빠짐 |
| E7 `propose_vertical_stack_id_gap_fill` 포트(1) | -- | SD 3282 | `if inputs or outputs or feedbacks or biases or clocks:` | 죽음(계약 6) | 빠짐 |
| E7 `case_collisions`(1) | -- | SD 4529 | `if disp.case_collisions:` | 죽음(계약 7) | 빠짐 |
| trace 루프 범위(2) | -- | -- | `find_differential_pair_candidates`의 `range(i + 1, …)`(const+·arith) | **이 card 범위 밖**(E6·E7 def가 아님, 측정 안 함) | 남음 |
| 등가(4) | -- | -- | `_propose_L_roles` 중복 가드 2, `open_terminals[0]` const−, `range` const− | 이 card 범위 밖(B26-1 code-author 동작 불변 정리 몫) | 남음 |

**합계**: Q1 24개 중 b26pre v2가 **16개를 죽인다**(LUT 없는 repair 4, euler fixup 3, finger growth 4, E7 5).
남는 8개 = backfill 2(U-BF 질문으로 이동 -- 고치면 문장이 사라짐) + trace 범위 2 + 등가 4.
(SR 9404·9406은 변이 id로 각 2개라 'LUT 없는 repair 4'는 base 문장으로 2개다.)

## 2. Q1 문안이 줄일 수 있는 것

* Q1 배경의 '20개는 test로 죽일 수 있는 기존 test 공백' → b26pre card(test-only)가 16개를 죽임이 실측됐다. 남는 '죽일 수 있는' 것은 trace 범위 2개뿐이다.
* finger growth 6개 중 2개(backfill)는 '기존 test 공백'이 아니라 **기존 동작이 문서화된 의도와 어긋나는 것**이었다. 그래서 '앞선 test-only card로 지금 동작을 고정'이라는 Q1 선택지 1의 설명이 이 2개에는 맞지 않는다.
  → 별도 질문 `_drafts/b26_backfill_question.md`(U-BF)와 red-green card 초안 `_drafts/draft_b26_backfill_audit.spec.md`.
* Q1 선택지 1의 test-only card 크기 추정('약 10~14 test, 300~500줄, 픽스처 4~5종')은 b26pre 실측 17 test(1 파일)로 바꿀 수 있다.

## 3. N2w 규칙 밖(N2d만) 대상 -- 참고

b26pre v2가 죽이는 나머지는 B26-1 card 규칙(N2w)에서 V3 대상이 아닌 'N2d만' 문장이다: SR 11803·11828·11835·11836·11837, SD 3285(삭제·뒤집기)·3286·4530, 씨앗 6개(SD 2100·2101·2176·2177·3985·3986).
수치를 섞지 않는다: b26pre 표 1의 변이 id 34개 = **N2w 18**(§1의 Q1 E6 13·E7 5 -- 16 죽음, 남는 2 = backfill) + **N2d만 16**(15 죽음, 남는 1 = SR 11802). B26-1 V3(N2w)와 맞추는 것은 앞 수치뿐이다.
* 씨앗 6개를 죽이는 계약 10은 card v3에서 'Mx1·Mx2 중 정확히 하나가 My와 짝'으로 약해졌다(동점 이름순 주석에 기대지 않음). `0f23786` 사본 재측정: base PASS, 씨앗 6/6 죽음, 동점 순서 역전 변이(SD 2761)에서도 통과.
* 씨앗 6개는 v1이 '등가 후보'로 올렸으나 합성 입력으로 구별된다(독립 검토). v2 계약 10이 6/6을 죽인다. N2w 규칙에서는 애초에 대상이 아니므로 B26-1 Q1의 24개에는 들어 있지 않았다.
* SR 11802(성공 분기 `_finalize` 삭제)는 유일한 등가 후보로 남는다(증명 스케치는 b26pre card '생존 3문장의 판정'). 역시 'N2d만'이라 N2w 규칙의 B26-1 V3에서는 면제가 필요 없다.
  B26-1 V3를 N2d로 재기로 하는 경우에만 A1-a 등가 면제 1건이 필요하다.
* 따라서 B26-1 V3를 card 규칙(N2w)으로 재면, E6·E7 def에서 B26-1 앞 card들(b26pre + backfill 결함 card)을 거친 뒤 남는 생존은 **0**이다(backfill 결함을 고치는 경우). 고치지 않으면 2(SR 11800·11879).
* 이 '0'은 예상이다. 순서는 B34 → b26pre → backfill 결함 card → B26-1이고, **backfill card 병합 뒤 B26-1의 모의 head·V3 대상 수('301')·Q1 문안을 그 병합본에서 다시 잰다**(E6 finger growth 6 → 4, head 11809·11888 행 삭제, 같은 블록 뒤 문장의 AST 경로 순번이 당겨진다).
* backfill 수정 후보의 `A/tests` 전체 회귀는 B34 없는 사본에서만 쟀다. B34 위 전체 회귀는 그 card auditor 몫이다(backfill card '재현할 수치').

## 4. 측정 수치(이 문서의 근거)

* 기준: 시제품 17 test, a796468 사본·+B34 사본 × PYTHONHASHSEED 0·1·7·123 = 8회 모두 17 passed.
* 변이: base 32문장(stmt_delete 31 + SD 3285 cmp_flip) → 두 사본 모두 죽음 29, 생존 3(SR 11800·11802·11879). 죽인 test 이름까지 두 사본이 같다.
* backfill 수정 후보(SR 11800·11879 삭제) 사본: `A/tests` 전체 888 passed·15 xfailed·2 failed(`.git` 필요 test, 사본 한계), base 사본은 같은 2개 + red 시제품 2개 실패.
