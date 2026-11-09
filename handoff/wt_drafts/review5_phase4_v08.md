# 5차 독립 검토: `draft_phase4_design.md` v0.8 (Phase 4 `40-defect-fixes`) -- 승인 질문 전 검토

검토자: 독립 검토(작성자 아님, 1~4차 검토자 아님). 대상: `_drafts/draft_phase4_design.md`(v0.8, 17:14), `_drafts/phase4_approval_question.md`(17:16), `_drafts/phase4_revision_log.md`(v0.7 → v0.8 절, 281~331행), `_drafts/p4_scripts/p4v08_dag.py`·`p4v08_measure.sh`·`out/p4v08_*.out.txt`. 기준: `_drafts/review4_phase4_v07.md`.
교차 입력(읽기만): `draft_phase3_design_v7.md`(**현재 판 17:29:50, 183,204 바이트, sha256 `40f7447b…dd4f103ac34`** -- v0.8이 고정한 16:45:58 판 `87c63513…`과 다르다, 다른 agent가 개정 중), `user_decisions.md`(17:32), `pending_questions.md`(17:37), `b26_backfill_question.md`(17:36), `b26pre_revision_log.md`(17:43).
측정: gate `master` = **`0f23786`**(시작·끝 같음, `git -C R rev-parse --short HEAD`). `git -C R diff --stat a796468 0f23786` = `.ai/approvals/20261001-p10b-v3-equiv.md`·`docs/02-design/specs/20260930-df23-registry-record.spec.md` 2파일뿐 -- 엔진·tests·tools·계획·`00-common` 변경 0, v0.8의 `a796468` 사실은 그대로 성립한다. 저장소 쓰기 0, git 상태 변경 0(`git status --short` md5 `168fd530…` 시작·끝 같음). 스크래치 `C:/g108`만(HEAD `git archive` 복제본 `iso`, `tools/gates` 사본 `cache`, DAG 사본·변형, 측정 스크립트) -- 끝에 삭제.

---

## 0. 판정

**수정 후 승인 질문 가능(fixable) -- blocking 0, should-fix 4, minor 9.**

* 4차 검토 B1·S1~S9·m1~m6은 **전부 반영됐고 재측정 결과가 기록과 같다**(§1). E3 `--gmid-dod`·`-k` 오선택·노드 id 수집 수·`propagate_node_voltages` 시그니처·계획/`00-common` 인용 줄·DAG 결론을 다시 쟀다.
* 새로 찾은 should-fix:
  * **N-S1** 승인 질문의 시점(Phase 3 DoD 뒤)과 '#2·#3·#4·#17·#18을 D0b 전에 앞당길 수 있다'가 양립하지 않는다 -- 그 card들의 선행인 UD-0·UD-1·UD-15가 그 질문에 들어 있다(DAG 실측: 승인 시점 간선을 넣으면 R1·R8·R9 **순환**).
  * **N-S2** S6(`tol` 기본값 제거)이 같은 사슬의 형제 기본값 두 개(`reconcile_vsb_from_nodes`·`audit_vsb_consistency`의 `tol=1e-6`)와, `audit_vsb_consistency`의 `tol` 이름 가림(호출부 3863이 `**kw`로 전달 -- `tol`은 가려져 전달되지 않음)을 다루지 않았다.
  * **N-S3** S2(CC-9 앞당김)의 정정 대상에서 **계획 N9.1 1159행**(`50-failure-cache` 행이 "`00-common` CC-9(`normalized_margin`)"을 담는다)이 빠졌다. §9-22는 "계획 749행·IC9 행은 바꾸지 않는다"고만 적는다.
  * **N-S4** `p4v08_dag.py`가 v0.8 편집에서 **간선 3개를 주석 안으로 삼켰다**(`#6 → #10`, `#25 → #10`, `#17 → #18`). 복원해 다시 돌리면 결론은 같다(전 시나리오 비순환/대조 순환 그대로) -- 기록 산출물 결함이지 설계 결함은 아니다.
* S6 질문(‘pass 수 ≤ 소자 수 + 1’이 루프 구조로 증명되는가): **증명된다**(§3, 루프 본문 실측). 근거 없는 새 상수는 없다. 구조 실측으로 library 9회로 pass 수 ≤ 3(제거가 무동작일 근거, [미측정] 항목 보강).
* Phase 3 v7 D-27과의 정합: 문장은 일치(§4). 단 v7이 v0.8 고정 판 뒤에 다시 바뀌었다(정보 -- 승인 질문 머리의 '확정본과 다시 대조' 조건이 이미 덮는다).

---

## 1. 4차 지적 재측정

| 4차 | v0.8 반영 | 재측정(이 검토) | 판정 |
|---|---|---|---|
| **B1** E3 `--gmid-dod` | E3 = `PT --gmid-dod -rA …/test_ic11.py`, E11 = 두 실행 | `p4v08_measure.sh`를 `C:/g108`에서 HEAD `0f23786` 복제본으로 재실행: 옵션 없음 = `3 xfailed`(rail2 XFAIL 'IC11 -- 담당 Phase 4 -- 만료: 4 DoD'), `--gmid-dod` = `1 failed, 2 xfailed`(rail2 FAILED `test_ic11.py:16`, rail3·reject XFAIL 6a). `out/p4v08_ic11.out.txt`와 같음. 추가: `PT` 형식(tests 전체 경로 + 파일)으로 수집하면 `886 tests collected`, `test_ic11.py::` 3개(중복 수집 없음) -- §6 머리 '실행 범위 = 전체 suite, 판정은 지정 test 결과'가 성립한다 | 해소 |
| **S1** `-k` | E4·E5·E10 = node id 목록 + '수집 수 = 목록 수' | `-k legacy`(contracts) = `1/606`, `test_ts3_no_print_verdicts.py::test_target_set_includes_legacy_scripts`; `-k lut_axis`(tests) = `no tests collected (886 deselected)`; 전체 `886`. 기록과 같음(4차의 '1/886'은 tests 전체 기준 -- 둘 다 맞다) | 해소 |
| **S2** margin | CC-9를 #23으로, `00-common` 7곳 문안 | 계획 749·827·396·428·439·441행 원문, `00-common` 109·263·265·266·540·559·607·618행 원문을 HEAD에서 확인 -- 인용 일치. 단 **계획 N9.1 1159행 누락 → N-S3**, 승인 질문의 '§3.2 표 109행'은 §3.3(m-1) | 반영(보완 필요) |
| **S3** #53 (i) | (i-1)·(i-2)·(i-3) 간선 | DAG 재실행: S2a·S2b·S2c 비순환, C5·C6·C7 순환 -- 기록과 같음(복원 간선 넣어도 같음, N-S4) | 해소. §3.3 같은 글머리 앞부분에 v0.7 문장 잔존(m-2) |
| **S4** Phase 3 v7·D-27 | 기본 F2 뒤, 앞당기면 D0b 전에만 | v7 현재 판 571·577·597·676행과 문장 일치. 단 **앞당김 경로가 승인 질문 시점과 모순 → N-S1** | 반영(보완 필요) |
| **S5** #55 oracle | (a) 합성·`SchemaRejectedError`·red (c) 무동작 | §5.10 #55 칸 확인. vsb = abs(V(source) − V(bulk))는 계획 DEC-61(255행) 원문과 같음 | 해소 |
| **S6** 기본 인자 | `tol` 기본값 제거·호출부 tol_V, `max_passes` 제거 | 시그니처 3727~3729·호출부 3831·3863·7294·7449 확인. **형제 기본값·이름 가림 → N-S2**. 증명은 §3 | 반영(보완 필요) |
| **S7** E-INST 해시 | #13 계약, §7.4, #14 = 실행 기록 JSON | 확인. #13 계약 '(4회로 모두 빈 목록)'은 발동 > 0 지점이 계측으로 남는 경우와 어긋날 수 있음(m-5) | 해소(문구 보완) |
| **S8** 문서 밖 규칙 | G1~G7 본문, oracle (d) 출처 | #26 줄 번호 HEAD 재확인(267·270·275~276·108·73·75 일치). 단 칸의 재측정 grep 명령이 HEAD에서 **아무것도 찾지 못한다**(m-3) | 해소(명령 수정) |
| **S9** P-34 | 혼합 사유 계수, `SearchFailedError.detail` | `00-common` 122·233행 `FailureRecord.detail` 있음 -- 실을 자리 있음 | 해소 |
| m1~m6 | 반영 | m2만 반쪽(§10.7 첫 문장에 철회한 근거 잔존 -- m-4) | 해소(m2 잔여) |

---

## 2. should-fix

### N-S1. '#2·#3·#4·#17·#18 D0b 전 앞당김'과 승인 질문 시점이 양립하지 않는다

**근거**
* 승인 질문 머리: "올리는 시점: **Phase 4 착수 시**(Phase 3 DoD PASS 뒤)". 1차 질문 = UD-0·UD-6·UD-1·UD-15.
* design §5 선행 열: #2 = "UD-0, DEC-40 V5 승인", #3 = "UD-0", #4 = "UD-0", #17 = "#1, #45, UD-1, (UD-15 결과)", #18 = "#17, …". 곧 #2~#4·#17·#18은 그 질문의 답 없이는 착수할 수 없다.
* 그런데 §3.1 항목 7·§3.2·#2~#4·#17·#18 `P3?` 칸·승인 질문 UD-0 본문("앞당길 때는 D0b 전에만 합니다")은 D0b 전 앞당김을 선택지로 둔다.
* 실측(`C:/g108/dag/p4v08_ud0.py` = 복원 간선 사본 + `P3DoD → UD-0·UD-1·UD-15`, `UD-0 → #2·#3·#4`): S0·S1 비순환, **R1·R8·R9 순환**(`TIMING+ R1 … False`, `R8 … False`, `R9 … False`). `p4v08_dag.py`에는 UD-0 노드가 없고 UD-1·UD-15가 뿌리라 이 모순이 안 보였다.

**고칠 것**(둘 중 하나를 문서에 확정)
* (가) 앞당김 경로를 지운다: #2~#4·#17·#18 = F2 뒤(Phase 4) 단일 경로, UD-0 본문의 "앞당길 때는 D0b 전에만" 삭제. §9-9의 N6.1 정정이 유일 경로가 된다.
* (나) 앞당김을 남긴다면 "그 card의 승인(UD-0의 해당 부분, UD-1·UD-15)을 **D0b 전에 별도 질문**으로 받는다"를 조건에 적고, 그 질문 문안을 따로 둔다(이 1차 질문으로는 성립하지 않음). DAG에 승인 노드와 시점 간선을 넣어 R1·R8·R9를 다시 돈다.

### N-S2. S6이 같은 사슬의 형제 기본값과 `tol` 이름 가림을 다루지 않는다

**근거(HEAD `0f23786` SR 실측)**
* `def reconcile_vsb_from_nodes(ctx, by_name, vdd, tol: float = 1e-6)`(3808) -- 본문 3843 `abs(old - exp) > tol`이면 vsb 덮어씀. 호출부 8658 `reconcile_vsb_from_nodes(ctx, by_name, _vsb_vdd)`(tol 미지정).
* `def audit_vsb_consistency(by_name, sized, vdd, tol: float = 1e-6, **kw)`(3850~3851) -- 본문 3863 `propagate_node_voltages(by_name, sized, vdd, **kw)`, 3875 `abs(d) > tol`. 호출부 8892 `audit_vsb_consistency(by_name, ctx.sized, _vsb_vdd)`(tol 미지정).
* 곧 HEAD에서 `tol=1e-6`은 세 함수(노드 충돌·vsb 덮어쓰기·vsb 감사 게이트)에 같은 근거 없는 값으로 있다. v0.8 #23은 첫째만 없앤다. 그리고 #23이 `propagate_node_voltages`의 기본값을 없애면 3863 호출은 `**kw`에 `tol`이 없어 **TypeError**가 된다. 호출자가 `audit_vsb_consistency(…, tol=tol_V)`를 넘겨도 그 값은 `audit`의 자기 `tol`(vsb 비교)로 들어가고 `**kw`로 전달되지 않는다(이름 가림). design #23 칸 "호출부 4곳(… 3863 …)이 tol_V를 넘긴다"는 이 구조에서 시그니처 변경 없이는 성립하지 않는다.

**고칠 것**
* #23 범위에 `audit_vsb_consistency`·`reconcile_vsb_from_nodes`의 처리를 적는다: (1) 노드 충돌 tol_V를 받는 인자 이름을 vsb 비교 허용오차와 분리(예: `node_tol`)하거나 `audit`이 받은 값을 명시 전달, (2) 두 함수의 vsb 비교 `tol=1e-6`도 근거 없는 기본값이므로 제거하고 근거(vsb는 노드전압 차이므로 tol_V 계열인지, 아니면 '같은 식으로 다시 계산한 값의 일치'라 비트 동일인지)를 원칙 기본안으로 정한다. 이 card에서 하지 않으면 담당 card를 지정한다(§1.4).
* §2 F 표 또는 부록 A G3에 두 줄(3808·3850~3851)과 호출부(8658·8892)를 사실로 더한다.

### N-S3. CC-9 앞당김의 정정 대상에 계획 N9.1 1159행이 빠졌다

**근거**: 계획 1159행 원문 "| `50-failure-cache` | `00-common` CC-9(`normalized_margin`), 실패 캐시 키·저장, margin 정규화식, …". §9-22는 `00-common` 7곳만 고치고 "계획 749행·IC9 행은 바꾸지 않는다"고 적는다. CC-9가 #23(`40-defect-fixes`)으로 오면 N9.1이 그 design에 '반드시 담을 것'으로 CC-9를 `50-failure-cache`에 남긴 채가 된다(1158행 `40-defect-fixes` 행에는 없음). 계획 1002행(N6.1 Phase 5 행 '… margin 반환')은 실패 캐시의 margin 반환으로 읽혀 그대로 둘 수 있으나 그 판단을 한 줄로 남긴다. 둘 다 `plan_tables_hash` 입력 아님(입력은 N4.1·N4.2·N6.1 `Phase` 열·N3.12.2 -- 계획 698행 EL3) -- 승인 종류는 문안 diff.
**고칠 것**: §9-22 '같이 고칠 문구'에 계획 1159행(CC-9를 `40-defect-fixes` 행으로) 추가, 승인 질문 UD-0 '승인 기록 diff' 목록에 계획 1159행 추가. 1002행은 '변경 없음(실패 캐시 margin 반환)'을 적는다.

### N-S4. `p4v08_dag.py`가 간선 3개를 주석으로 삼켰다

**근거**: `p4v07_dag.py` 46·50행 `add("#25", "#6", "#22"); add("#10", "#6", "#25")`, `add("#17", …); add("#18", "#17")`. `p4v08_dag.py` 40·44행은 `add("#25", "#6", "#22", "#23")  # v0.8 S2: …; add("#10", "#6", "#25")`, `add("#17", …, "P3DoD")  # v0.8 S4: …; add("#18", "#17")` -- 뒤쪽 `add` 호출이 주석 안이다. 그래서 #10은 선행 없는 뿌리, #18은 #17과 무관해졌다(design 표: #10 선행 "#6, **#25**", #18 선행 "#17").
**재실행**: 원본 사본 출력은 `out/p4v08_dag.out.txt`와 `diff` 0(`SAME_AS_RECORDED`). 두 줄을 복원한 사본(`p4v08_fixed.py`)도 S0~S8·R1·R8·R9 비순환, C1~C7 순환으로 결론 같다(정렬 실패 목록에 #10·#18이 새로 보일 뿐).
**고칠 것**: 두 줄을 별도 문장으로 복원하고 다시 돌려 출력·부록 A G1을 갱신. N-S1 (나)를 택하면 승인 노드·시점 간선도 함께.

---

## 3. S6 유도 검증 -- 'pass 수 ≤ 소자 수 + 1'

* HEAD SR 3760~3786(본문 실측): `for passes in range(1, max_passes + 1)`, pass 안에서 `for name in sorted(unresolved)`. `progressed = True`가 되는 세 갈래(소스만 앎·드레인만 앎·둘 다 앎) **모두** 같은 줄에서 `unresolved.discard(name)`를 한다(`name`은 그 pass 시작 때 `unresolved`의 원소). `vds`가 없으면 `continue`(진전 없음). pass 끝에 `if not progressed: break`.
* 따라서 진전 있는 pass는 미해결 소자를 1개 이상 지운다 → 진전 있는 pass ≤ N(소자 수). 그다음 pass는 진전이 없어 끝난다(미해결이 비어도 빈 순회 → 진전 없음 → break). **passes ≤ N + 1**, `max_passes` 없이도 종료가 보장된다. design #23 문장은 맞다. 계획 441행 `K_max`는 bisection·고정점 반복의 상한이라 이 위상 전파에 해당 없다는 판단도 맞다.
* 새 상수 없음: 상한은 별도 상수로 둘 필요가 없다(루프가 스스로 멈춤). 단 승인 질문 UD-0 문구 "반복 상한은 알고리즘에서 나오는 값(소자 수 + 1)으로 **바뀝니다**"는 design의 '`max_passes` 제거'와 어긋나 새 상한 인자가 생기는 것처럼 읽힌다(m-6).
* [미측정] 보강(정보): 구조 실측(`C:/g108/passes.py` -- library 9회로, 모든 소자에 `vds`를 준 `sized`, 레일 = `supply_nets`의 vdd/gnd·vss, `max_passes=10**6`) 결과 passes = 2~3(current_reuse 51소자 3, folded 13소자 3), unresolved 0. 실제 실행은 일부 소자에 `vds`가 없을 수 있어 상한 증명은 아니지만, 50에 닿을 가능성은 낮다는 근거다. #23 작성 전 실측(정본 실행 `passes` 최댓값)은 그대로 둔다.
* `tol_V` 대응 '두 경로 소자 tol_V 중 작은 쪽'(§9-25): 계획에 없는 규칙을 원칙(거부가 기본인 봉인 검사 = 엄격한 쪽)으로 정하고 계획 정정 요청으로 올렸다 -- 새 상수 아님. 다만 '`plan_tables_hash` 입력인지는 #23 작성 전 실측이 확인'은 지금 답할 수 있다: N3.6은 입력 목록(계획 698행: N4.1 담당 Phase·강제 test, N4.2 도입, N6.1 Phase 열, N3.12.2)에 없다 → 문안 정정(m-7).

---

## 4. Phase 3 v7 D-27 정합 (읽기만)

* v7 현재 판(17:29:50) 571행(§8.1 표 'D0b 병합 | F2 병합까지 | 엔진 card 동결'), 577행('B26-2~B26-4·B35의 자리 … 기본값 = F2 뒤 … **D0b 전**(B33 뒤·G1 앞 또는 G1 뒤·D0b 앞)'), 597행(§9.1), 676행(D-27)과 v0.8 §3.1 항목 7·§3.2 마지막 문단의 문장이 같다. #19(B26-4)는 v0.8이 '#21 조상 때문에 Phase 3 전 불가'로 두어 v7 '앞당기려면 D0b 전'과 충돌하지 않는다(더 좁음).
* D-19·D-22·D-25·D-26 행(666·669·674·675행)은 v0.8 §3.1 1~6 서술과 같다.
* 정보: v0.8과 승인 질문이 고정한 v7 판(16:45:58, `87c63513…`)은 지금 판이 아니다. 승인 질문 머리의 '확정본과 다시 대조' 조건이 이미 이 경우를 덮으므로 결함은 아니다. 대조 때 N-S1의 결론(앞당김 경로 유지 여부)을 v7 577행 문장과 함께 맞춘다.

---

## 5. 승인 질문 점검 (진짜 사용자 몫·정확한 사실)

* 사실 재확인: UD-1 "지금 library 9회로는 아래 규칙만으로 모두 판정" -- 실측(`C:/g108/polar.py`, `supply_nets`마다 pmos source만 = 위, nmos source만 = 아래, 둘 다 아님 = 중간): 9/9 판정, 거부 0(vdd = 위, gnd·vss = 아래, pushpull·sf_pushpull `agnd` = 중간). 맞음. 'card 계약 49 + 조건부 5', '#13 키 추가로 4회로 해시 한 번 변경', '#43·#25 margin `null`', '`--gmid-dod` 없이는 망가진 rail2가 예상된 실패' -- design·실측과 일치.
* 진짜 사용자 몫: UD-0(design 승인 -- DEC-51), UD-6(U-09, 회로 해석 포함), UD-1·UD-15(스키마 선택 -- topology 필드는 사용자 몫), 2차 U-04·U-05·U-26 (a)(계획 N7.2 '확정 전에는 구현하지 않는다') -- 모두 사용자 몫이다. 원칙 기본안(P-1~P-34)은 UD-0에 묶어 따로 묻지 않는다 -- 원칙에 맞다.
* 고칠 것은 N-S1(UD-0 본문의 앞당김 문장), N-S3(승인 기록 diff 목록), m-1(§ 번호), m-6(반복 상한 문구), m-8(대기 목록 갱신), m-9(U-26 nmcnr 문구).

---

## 6. minor

* **m-1** 승인 질문 머리 "`00-common` 문구 diff(§3.2 표 109행 …)": 109행은 §3.3 '이 문서 자신의 분류' 아래다(`awk` 절 추적). → '§3.3 표 109행'. design 머리 G4는 265행까지 8줄, §9-22·개정 기록·승인 질문은 7곳 -- 265행(IC9 문장)은 고치지 않는다는 뜻이면 G4에 '265행은 읽기만'을 적는다.
* **m-2** §3.3 '#53 ← UD-17a·b·c' 글머리 앞부분 "(i) … #23과 독립이라 권고 #53 → #23 유지"는 v0.7 문장이다. 같은 글머리 뒤쪽 (i-1)·(i-2)는 '권고 없음'이므로 "(i-3)이면"으로 좁힌다.
* **m-3** #26 칸 재측정 명령 `grep -n 'VS{iVS}\|SID_1F\|xdut\|VS_GRID\|OUTPUT_DIR' <A>/sky130_lut_sweep.py`는 HEAD에서 **출력 0줄, rc=1**(같은 파일에 `SID_1F` 등 32줄이 있는데도). `-F -e 'VS{iVS}' -e SID_1F -e xdut -e VS_GRID -e OUTPUT_DIR`로 바꾼다. 줄 번호 자체(267·270·275~276·108·73·75·146~150·172~179·329~333)는 HEAD와 맞다.
* **m-4** §10.7 기반 클래스 근거 첫 문장에 "I-C11 known-limitation xfail(`raises=ValueError`)과 … 관계를 깨지 않는다"가 남아 있고, 같은 칸 뒤에서 그 근거를 뺀다고 적는다 -- 첫 문장에서 지운다.
* **m-5** #13 oracle (c) "바뀌는 것은 `instance.json` 최상위 키 `fallback_events`(4회로 모두 빈 목록) 하나뿐": #13 범위의 §10.1-4 발동 규칙상 '발동 > 0 → 계측·원인 card 지정' 지점이 정본 실행에서 발동하면 #13 병합본 목록은 비지 않는다. → "키 하나뿐(값은 그 시점 계측 발동 목록 -- 빈 목록은 E1(DoD) 조건)"으로 고친다.
* **m-6** 승인 질문 UD-0 "반복 상한은 알고리즘에서 나오는 값(소자 수 + 1)으로 바뀝니다" → "반복 상한 인자(50)는 없앱니다 -- 루프가 진전 없는 pass에서 멈추므로 pass 수는 소자 수 + 1을 넘지 않습니다"(§3).
* **m-7** §9-25 "`plan_tables_hash` 입력인지는 #23 작성 전 실측이 확인" → 지금 확정 가능(N3.6은 입력 아님, 계획 698행). 문안 정정으로 적는다.
* **m-8** 승인 질문 '이미 따로 대기 중'이 v0.8 뒤 기록과 어긋난다: `b26pre_revision_log.md`(17:43) S5 행은 B26pre U1을 '원칙 기본안(결정 아님)'으로 바꿨고, 새 사용자 질문 `b26_backfill_question.md` U-BF(`interdig_ok` backfill, 17:36)와 `pending_questions.md` Q-B34-PHASE(B34·B26-1 card `phase: 2` → `3` 여부, 17:37)가 생겼다. Q-B34-PHASE의 답에 따라 v0.8의 '두 card 머리 `phase: 2`'(§3.1·§3.2·§9-19) 문장이 바뀐다. 승인 질문을 올리기 전 대기 목록을 다시 뽑고, Q-B34-PHASE 결과를 §3.2·§9-19에 반영한다.
* **m-9** 2차 질문 U-26 (a): 계획 1101행은 nmcnr을 이미 **확정**(`{vdd: 0.9, vss: −0.9}`)으로 적는다. 사용자 확인 대상은 세 회로 값과 nmcnr의 MG1~DF-24 사이 **중간값** `{vdd: 1.8, vss: 0.0}`뿐임을 문안에 밝힌다(확정값을 다시 묻는 것처럼 읽히지 않게).
* 정보(결함 아님): §10.6-0 margin 비교의 '분모(tol_V)가 두 평가에서 같음 -- 다르면 FAIL'은 tol_V가 VDS의 함수라 #22 뒤 절대 프레임에서 VDS가 비트 단위로만 달라도 앵커 경계에서 갈릴 수 있다. #21 interface card에서 '같은 (kind, L 앵커, VDS 앵커)이면 같은 분모'처럼 앵커 단위로 적으면 가짜 red를 막는다. #14 θ*의 실행 기록 JSON은 계획 368행 S3 실행 기록(θ*, start별 결과 -- Phase 5 `runs.jsonl`)과 같은 개념이므로, Phase 5가 그 파일을 대체할지 읽을지(DEC-68 저장 위치 하나)를 §1.4 '다른 Phase'에 한 줄 남긴다. #26 oracle 'CGS+CGD+CGB ≈ CGG'의 '≈'는 허용오차가 정의되지 않았다(v0.8 이전부터 -- card가 근거 있는 허용오차를 정하거나 비교를 기록으로).

---

## 7. 작성자 ≠ 검증자

* 보고 수치는 이 검토에서 독립 복제본으로 다시 쟀다(§1 표). 작성자 산출물(`out/p4v08_*.out.txt`)과 일치하는 것은 IC11·수집 수·DAG 결론이고, 어긋난 것은 DAG 스크립트 간선(N-S4)과 #26 grep 명령(m-3)이다.
* design 안의 판정 기준: oracle 기대값을 피검 함수로 만드는 곳은 #21 IC11 판정기뿐이고 V4 면제 승인(§7.3)으로 명시돼 있다. 같은 커밋에서 코드와 기준을 바꾸는 계획은 없다(E-INST·D-25 해시 변경은 기대 차이표 + DEC-40 건별).

## 8. 증거 명령(요지)

```
R=…/chip-design-skills; set -e
git -C $R rev-parse --short HEAD                          # 0f23786
git -C $R diff --stat a796468 0f23786                     # 2 files (approvals, spec card)
bash _drafts/p4_scripts/p4v08_measure.sh $R C:/g108       # §1 B1·S1 (IC11 두 실행, -k 수집, 전체 886)
PT4 <tests> --collect-only -q <tests>/contracts/test_ic11.py   # 886, test_ic11 3개(중복 없음)
python -B C:/g108/dag/p4v08_dag.py                        # 기록과 diff 0
python -B C:/g108/dag/p4v08_fixed.py                      # #10·#18 간선 복원 -- 결론 같음 (N-S4)
python -B C:/g108/dag/p4v08_ud0.py                        # + 승인 시점 간선: R1·R8·R9 순환 (N-S1)
sed -n 3727,3786p;3808p;3850,3880p;8655,8660p;8890,8893p <iso>/…/sizing_recipe.py   # §3, N-S2
sed -n '396p;428p;439p;441p;698p;749p;827p;1002p;1101p;1158p;1159p' <iso>/docs/01-plan/…plan.md   # N-S3, m-7, m-9
sed -n '109p;263p;265p;266p;540p;559p;607p;618p' <iso>/docs/02-design/…00-common.design.md
python -B C:/g108/passes.py ; python -B C:/g108/polar.py  # §3 정보, §5 UD-1 사실
grep -n 'VS{iVS}\|SID_1F\|xdut\|VS_GRID\|OUTPUT_DIR' <iso>/…/sky130_lut_sweep.py   # 0줄, rc=1 (m-3)
```

## 산출물·정리

* 쓴 파일: 이 파일뿐. 저장소·worktree 쓰기 0, git 상태 변경 0(HEAD `0f23786`, `status --short` 시작·끝 같음). 다른 `_drafts` 파일 수정 0.
* 스크래치 `C:/g108`(HEAD 복제본 `iso`, `cache`, `pyc`, DAG 사본·변형 3개, `passes.py`·`polar.py`, 측정 출력)은 검토 끝에 삭제했다.
