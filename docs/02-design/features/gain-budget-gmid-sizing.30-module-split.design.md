# gain-budget-gmid-sizing -- Phase 3 `30-module-split` design

> **v8.5 -- 사용자 승인 2026-10-02**(UD-0 "승인 (Recommended)"·D-19 "(가) MOD2 (Recommended)"·UD-1 "(가) 깨지게 둠 (Recommended)", 승인 기록 `20260930-30-module-split-design`). 정식 경로(계획 N9.1) = 이 파일. 승인본 = 초안 `_drafts/draft_phase3_design_v8.md`(sha256 `a4350dc05ff86179…`) -- 저장소에 넣으며 이 줄(초안 표지)만 바꿨다.
> **v8.5(2026-10-02)**: 8차 검토 `review8_phase3_v84.md`('ready to ask') 경미 m1~m4와 D0b-8 반영 -- 문서 개정 §9 (h) N3.10 MOD9에 `_kv_table` 토큰(레지스트리 칸 `〃` 번짐으로 MOD4가 되던 HTML 표 도우미를 책임대로 MOD9, UD-0이 덮음), 독립 재구현 모의에서 일곱 목록·MOD7 밖 모두 0·`_kv_table` = MOD9 A-1(부록 A F5v85); §9.2 UD-0 행 '기준에 닿는 기본값'에 D-31(m1); §6.5 갈리는 MOD 둘; D0a 계약 2 모호 두 곳을 실측과 같은 읽기로 확정(m4 -- 승격의 R(u) 최댓값은 N3.10 MOD 번호만, A-6은 승격·상한 공허). 질문 (d) 32개 분해(m2)·④ 9단위(m3). 기준 gate `master` `dd60db6` 그대로. 사본 `draft_phase3_design_v8.v8.4.md`, 대응표 `phase3_revision_log.md` '초안 v8.4 → v8.5'.
> **v8.4(2026-10-01)**: 승인 질문 전 마무리 -- (1) **`__future__` 혼합**(G1 착수 키트 0.2): `design_report.py`·`audit_current_forced.py`(future 없음)의 9단위를 future 있는 MOD 파일로 옮기면 G1 M-4가 거부한다 -- 세 처리안을 원칙과 실측으로 비교해 **준비 card FU**(D0b 전에 두 파일에 `from __future__ import annotations` 한 줄)를 기본값으로 정함(§6.5, D-29; 함수 몸체 코드 객체 17개 동일·전체 test 1047 passed 15 xfailed 동일·V3 변이 0·V6 발견 0·V7 PASS·E-LIB·E-INST 해시 동일·모의 M card 거부 0, 부록 A F2v84·F3v84). 승인된 기준을 바꾸지 않으므로 UD-0 안의 설계 결정이고 card 수만 16 → 17(질문 본문에 사실로). (2) **D0a import 머리 생성**(이름마다 import 한 번 -- `plan` `mod_imports`·`import_conflicts`, `check` `import-dup`, D-30, §6.3·§8 D0a·M행). (3) G1 spec card v9 반영: `SourceIndex.tree(path)`(D0a 착수 조건 해소), 머리 수치 변이 15,650·V6 859·게이트 밖 호출 스크립트 4·redteam 31단계(§4 F5·§5.1·§5.2·§8 G1행). (4) T0 V5 승인 범위에 '리터럴 변경 3 + 비교 완화 1'(§9.2). (5) 기준 gate `master` **`dd60db6`**로 다시 확인 -- `0f23786..5f643a9`(P10b 병합·md 일치 card 등)과 `5f643a9..dd60db6`(Phase 2 완료 판정 기록 `2eefda1` -- 대상 H = `5f643a9` = **P2D**, PASS; 백로그; V3 면제 묶기(34) 문서·spec·승인 -- 계획서 839행 한 줄) 모두 엔진·`tools/`·N3.10·레지스트리 목적지 열 무변경, 문서 개정 '현재' 블록 일치(부록 A F1v84). 실측(F2v84~F4v84)은 `5f643a9` = P2D 판에서 했다. (6) **D0b 착수 키트·D0b 검토(`review_d0b.md`) 반영 -- 이관표 계층**: UD-0 개정을 적용한 모의 트리에서 `plan`이 `upward` 34·`cycles` 1·`unassigned` 18 -- 배정 규칙 보강(모듈 docstring 제외·A-K·승격(MOD7 상한)·A-6·A-7·단조 고정점, §6.2 D-31 -- 승격은 '레지스트리 열 = 정본'을 '칸 = 하한'으로 읽으므로 질문에 사실로)과 N3.10 A-1 충돌 보정 8건(토큰 11개, 문서 개정 §1 갱신·§9, D-11)로 0·0·0(부록 A F4v84, 시제품 관찰), `_metric_*` 문장 정정, §8 D0b 행을 대상 행·실제 단위 표본·`근거 규칙` 형식·판정 목록 일곱(`import_conflicts`)·FU base 사슬·멈춤 경로로 닫음, D-10에 U-02 1항 원문. 스크래치 `C:/g164`, 사본 `draft_phase3_design_v8.v8.3.md`, 대응표 `phase3_revision_log.md` '초안 v8.3 → v8.4' 절, 정정 요약 부록 L.
> **v8.3(2026-10-01)**: 7차 검토 `review7_phase3_v82.md`와 B26 묶음 답 반영 -- §10 E5 판정 python의 `rails` 계약값 판정을 **정확 일치**로(`hv == {"__dc__": "RailDeclaration", "nets": want}` -- 계약 밖 필드가 끼면 FAIL, S1), 계약값 `supply_nets`를 HEAD가 아니라 **비교 시작 판(P2D) library**에서 `git show`로 읽음(판정 python 인자에 `$P2D`, m1), 승인 질문 UD-0 (c) 기본안에 비용 문장과 '계약 모양 시제품으로 실측'(m2). **A2-③은 결정됨**(사용자 답 2026-10-01 B26 묶음 [card phase] "phase 3 + 정정 기록 (Recommended)", decision 기록 `20261001-b26-phase3-cards`) -- 승인 질문에서 빼고(질문 4개, S2) §9.2 A2-③ 행·§11-11·§6.4·D-28 (e)·E5 행을 결정 사실로 고침, 네 card(B34·b26pre·backfill·B26-1)가 Phase 3 DoD N6.3 목록(`^phase: 3$` spec card)에 든다는 문장(§8.1·§9.1·D-23), §6.4에 B40 반환 키 삭제(U4)와 B26-1 등가 면제의 모듈 접두 처리(U3). 재측정 = `a796468`, 스크래치 `C:/g149`, 스크립트 `_drafts/p3_scripts/p3v83_*`, 실측 부록 A F4v83. 사본 `draft_phase3_design_v8.v8.2.md`, 대응표 `phase3_revision_log.md` '초안 v8.2 → v8.3' 절, 정정 요약 부록 K.
> **v8.2(2026-10-01)**: 오케스트레이터 결정(원칙: 같은 상황의 사용자 선택을 따른다 -- 승인 `20260930-phase2-e4-baseline`, 사용자 "둘다 기본안으로 진행해") -- **UD-0 (c) E5 비교 판의 기본안을 선례 모양으로 바꿈**: Phase 2 DoD 대상 커밋 `P2D`와 Phase 3 마지막 병합본을 같은 경로에서 비교하고, 사이 card가 의도적으로 바꾼 필드만 그 card 계약값으로 따로 판정, 나머지는 해시 같음. B0 비교는 대안. 빼는 필드 목록을 card 초안 계약에서 유도하고 실측(E-INST instance.json 키 없음 -- backfill `interdig_ok`는 `pipeline_result`까지만 가고 instance.json·report에 닿지 않는다; E-LIB `load_topology` `meta["rails"]` 하나), E-LIB용 `e_lib_p3.py`(`e_lib.py` + meta 키 빼기 인자 한 곳)를 design 커밋에 더함(D-28 (e)·§10 E5 블록·행·§9.2 UD-0·승인 질문 UD-0 (c)). 측정 = `a796468`(엔진은 `0f23786`과 같다), 스크래치 `C:/g135`, 스크립트 `_drafts/p3_scripts/p3v82_*`·`e_lib_p3_proposed/`. 사본 `draft_phase3_design_v8.1.md`, 실측 부록 A F1v82~F3v82, 대응표 `phase3_revision_log.md` '초안 v8.1 → v8.2' 절, 정정 요약 부록 J.
> **v8.1(2026-10-01)**: 6차 검토 `review6_phase3_v8.md` 반영 -- E5 비교 판 B0를 **'기준에 닿는 기본값' (c)**로 옮기고 선례 `20260930-phase2-e4-baseline`의 기본안 모양(Phase 2 DoD 대상 커밋과 비교 + 의도된 변경 필드만 card 계약값으로 따로 판정)을 대안으로 적음(N1 -- D-28 (e)·§10 E5·§9.2 UD-0),
> E2 통과 기준에 `E2 INVALID` 줄 없음(N2), 확정 순서·A2-③에 backfill 결함 card `20261001-b26-backfill-interdig-final-audit`(B34 → b26pre → backfill → B26-1, N3), §11-11에 card `phase`가 V1 `--gmid-phase`·`--gmid-strict`를 정한다는 문장(N4),
> D-26 한계에 E3b가 놓치는 세 모양(m-a), D-28에 `e_inst_p3.py` 출처 확인 범위(m-b). 사본 `draft_phase3_design_v8.0.md`, 대응표는 `phase3_revision_log.md` '초안 v8 → v8.1' 절.
> **v8(2026-10-01)**: 5차 검토 `review5_phase3_v7.md` 반영 -- **`PT3`**(§10 머리: `PT`에서 `--gmid-phase=1`만 `--gmid-phase=3`, E4·E5 = `PT3` 전체 + `PT3 --gmid-dod` 전체, T0 oracle도 `--gmid-phase=3` -- B1,
> 선례 승인 `20260930-phase2-e4-phase`), **E3b 표지 이름 면제 제거**(star·동적 이름·파싱 오류는 base에 있어도 FAIL -- B2, 합성 커밋에서 v7 PASS / v8 FAIL 실측),
> **F1 뒤 E-INST 측정 스크립트** `e_inst_p3.py`(design 커밋에 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/`로 함께 넣고, F1 전 트리에서 `e_inst_df36.py`와의 동등을 E5가 먼저 잰다 -- S1),
> D-9·UD-0 (a)의 판정 기록 스크립트 깨짐 수를 실측으로(S2), A2 ③ 'Phase 2 진행 중' 충돌은 결정하지 않고 승인 질문의 별도 항목으로(S3), D-25를 E-INST 회로 집합으로 좁힘(S4),
> UD-1 경로(S5), D-27 동결 범위에 `tools/gates/**`·`tools/migrate/**`·레지스트리 목적지 열과 E6 사후 강제(S6), minor m1~m7. 측정 = gate `master` `0f23786`(`a796468` 대비 바뀐 것은 승인 기록 `20261001-p10b-v3-equiv`와 P10b spec card 2파일 -- 엔진·`tools/`·계획·레지스트리 무변경),
> 스크래치 `C:/g113`, 스크립트 `_drafts/p3_scripts/p3v8_*`. 대응표는 `phase3_revision_log.md` '초안 v7 → v8' 절, 정정 요약은 부록 H.
> **v7(2026-10-01)**: 4차 검토 `review4_phase3_v6.md` 반영 -- **E3b**(F2가 `stick_diagram` 임시 재수출을 지운 뒤 추적 파일이 SD에서 읽는 이름이 모두 해석되는지, N1)와 F1·F2 문장(이름 단위),
> E3·IMPORT-ANY fail-closed(S1·S2), M10 V3 생존 실측과 '작성 전 실측' 항목(S3), 엔진 card 동결 규칙과 B26-2~B26-4·B35 위치(S4, D-27), D-22 전제의 D0b 계약 단언(S5), minor m1~m6,
> 그리고 **확정 순서**: P10b → Phase 2 DoD → 면제 묶기(34) → 범위 정책(35) → B34 → B26-1(앞선 test 보강 card 포함) → B33(33) → Phase 3.
> (v8 정정 -- 5차 검토 S3: 사용자 지시 원문 "P10b 끝나면 push하고 Phase 2 완료 판정 진행해"는 P10b → Phase 2 DoD만 정한다. 그 뒤 34 → 35 → B34 → B26-1은 오케스트레이터가 제안하고 사용자가
> "응, 그렇게 진행해"로 답한 순서이고(`_drafts/pending_questions.md` Q-B34-PHASE 기록), test 보강 card와 B33의 자리는 오케스트레이터 배열이다. v7의 '사용자 지시' 귀속은 이 범위로 좁힌다.)
> B34·B26-1은 Phase 2 DoD **뒤**에 병합하는 앞당긴 card(A2)이고 Phase 2 DoD의 N6.3 판정 기록 목록에 들지 않는다(§8.1·§9.1). 측정 = gate `master` `a796468`, 스크래치 `C:/g95b`,
> 스크립트 `_drafts/p3_scripts/p3v7_*`. 대응표는 `phase3_revision_log.md` '초안 v6 → v7' 절, 정정 요약은 부록 G.
> **v6(2026-10-01)**: 3차 검토 `review3_phase3_v5.md` 반영 -- D0a `order`·`shim` 문언(B1·B2, M1~M9 모의로 확인), DoD 명령을 bash 블록으로·E3 거부 확인(B3), UD-0 문서 개정 문안 `_drafts/p3_doc_amendments.md`와
> N3.10 개정 시점(B4), 옛 문장·수치(S1~S8), 모의에서 새로 드러난 M9 중간 상태 순환 import(§2.2 D-22). 측정 = gate `master` `7535799`, 스크래치 `C:/g73`, 스크립트 `_drafts/p3_scripts/`.
> 작성 중 master가 `a796468`(P9·P10 병합, 계획 A2 정정 `8356c1e`)로 나아갔다 -- 그 판에서 다시 확인: 문서 개정 '현재' 블록 10개 일치, E3 AST 수치 동일, `tools/gates` 무변경, 엔진은 `stick_diagram.py`만
> (P9, −11줄 -- SD 줄 인용은 원래 재측정 대상).
> 대응표는 `phase3_revision_log.md` '초안 v5 → v6' 절, 정정 요약은 부록 F.
> 측정 시점 = gate `master` `7535799`(2026-09-30, **B28 병합 `2b41e79`·판정 기록 `8790b24` 뒤**). 엔진·계획서·design 00/05/10/20의 인용 줄은 v3 측정 시점 `cd64170` 이후 불변
> (`git diff --stat cd64170 HEAD`는 tools·P9 spec·design 20 E4뿐) -- 줄 번호가 바뀐 것은 `tools/gates/mutate_changed.py`(B28)와 redteam뿐이다. 측정은 읽기 전용, 스크래치 `C:/g51`(끝나면 삭제).
> v5는 v4 뒤 확정된 결정·card를 반영한다(2026-10-01, HEAD는 여전히 `7535799`): 사용자 결정 **A2**(B26-1·B34를 Phase 3 전에 병합, 승인 기록 `20260930-b26-before-phase3`),
> **A1-a·A1-b**(V3 면제 묶기 `20260930-v3-exempt-binding`, V3 범위 정책 N2 + 넓힌 T6 `20260930-v3-changed-stmt-scope`), B33(`20260930-v7-registry-edges`)가 G1보다 먼저 병합된다는 순서와
> redteam 번호(G1 32, B33 33, 면제 묶기 34, 범위 정책 35). 그 card들이 바꿀 사실은 **초안에서 추정해 '§9.1 재측정 조건'으로 표시**했다(병합 전이라 잴 수 없다 -- 추정치를 판정 근거로 쓰지 않는다).
> 측정 명령·결과는 부록 A, v1→v2 정정은 부록 B, v2→v3 정정은 부록 C, v3→v4 정정은 부록 D, v4→v5 정정은 부록 E(발견별 대응은 `phase3_revision_log.md`).
> **재측정 조건(Phase 3 시작 때 -- 상세는 §9.1)**: (1) P9·P10·**B34·B26-1**(엔진 변경 card, v7: Phase 2 DoD 뒤·B33 전에 병합)이 병합되면 엔진 줄 인용(`sizing_recipe.py:2391·2530·7697`, `stick_diagram.py:1050·8973`,
> `run_harness.py:422·427·446`)과 부록 A M6·M9~M15·M18·M22·M24·G6'·S6·S7·S11·S13·m6·m7을 그 병합본에서 다시 잰다(2차 검토 S8, §6.4). (2) B33·면제 묶기·범위 정책(게이트 card)이 병합되면
> §5.1·G1 card '작성 전 실측'의 `tools/gates` 줄 번호·출력 키와 부록 A G2·G5'(base 열)를 그 병합본에서 다시 잰다(§5.5).

버전 v0.8(초안). 정본 인용 규칙은 계획 N9.4 -- 이 문서는 계획서·`00-common`·`05-role-separation`·`20-dead-code-dup`의 정의를 재서술하지 않고 절 번호로 인용한다.
읽은 계획 절(N9.1 표 `30-module-split` 행): N3.10, N6.1·N6.2 Phase 3, U-03. 추가로 읽은 절: N3.11(test 배치), N3.12.2(역할 경로), N3.12.3(card 단위·판정 유형), N4.2 V2·V3·V6·V7, N8,
WP-01·WP-03·WP-11·WP-14, NFR-2.

실측 원자료: `p3_measure.py`·`p3_assign.py`·`p3_refs.py`(초안 v1), `p3v2_g1_measure.py`(v2), `p3v3_g1_measure.py` → `p3v3_g1_results.json`(v3), `p3v3_facts.py` → `p3v3_facts.json`
(v3: N3.10 열·토큰, 중첩 참조, 인벤토리, 전수 스캔 이름, V3 출력 키), **`p3v4_g1_measure.py` → `p3v4_g1_results.json`**(v4: v3 규칙과 v4 규칙을 같은 입력에서 나란히 -- v3 26단계 +
2차 검토 새 반례 25단계, 각 단계 합성 저장소에서 HEAD 게이트 도구 3개 실제 실행, D0a `check` 발견 모의, 실제 엔진 통째 이동 거짓 거부, 판정 기록 무동작),
**`p3_scripts/p3v6_order_shim_sim.py` → `p3v6_order_shim_sim.*.json`**(v6: 근사 이관표로 M1~M9를 실제 파일로 적용한 트리에서 `order`·`shim` 옛/새 문언과 모듈별 단독 import),
`p3_scripts/p3v6_e3_check.sh`(v6: E3 명령 실행), `p3_scripts/p3v6_m10_inventory_time.py` → `p3v6_m10_inventory_time.json`(v6: M10 V3 비용 입력),
**v7**: `p3_scripts/p3v7_e3b_synth.py`(합성 커밋), `p3v7_sec10_selftest.sh` → `p3v7_sec10_selftest.out.txt`(§10 E3·E3b·`import_any`를 이 문서에서 잘라 실행),
`p3v7_m10_mutants.py` → `p3v7_m10_mutants.*.json`(M10 변이를 실제로 하나씩 실행), `p3v7_import_time_reads.py` → `p3v7_import_time_reads.json`(D-22 전제).
**v8**: `p3_scripts/p3v8_e3b_synth.py`(합성 커밋: 5차 검토 B2의 B0'·H, 모의 M9·F2·하네스 F1), `p3v8_sec10_selftest.sh` → `p3v8_sec10_selftest.out.txt`(§10 E3·E3b를 v8·v7 문서에서 잘라 실행),
`p3v8_einst_equiv.sh` → `p3v8_einst_equiv.out.txt`(`e_inst_p3.py` 제안 사본 `p3_scripts/e_inst_p3_proposed/e_inst_p3.py`와 `e_inst_df36.py`의 F1 전 동등, F1 모의 트리에서 E-INST·E-LIB).
참조 구현은 design 문장이 판정 가능한지 확인하는 초안 측정이다 -- G1 구현이나 test 기대값의 근거가 아니다(작성자≠검증자).
정식 문서로 올릴 때 원자료는 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/`에 둔다(20-dead-code-dup 선례).

---

## 1. 범위 (N9.2-1)

계획 N6.1 Phase 3 행(1000행)이 정본이다: "10모듈 이동(N3.10), shim, 추적 파일 호출부 갱신 후 `sizing_recipe.py` 삭제 | equivalence | U-03". 이 Phase가 구현하는 것:

1. **게이트의 이동 인식**(G1): 계획 N3.10 533행 "해시가 같은 함수는 V3 대상에서 뺀다"가 도구에 없다(§5). 이동 card가 판정 가능하려면 먼저 필요하다. G1은 먼저 병합되는 게이트 card
   셋(B33 V7 그래프 간선, V3 면제 묶기, V3 범위 정책)과 합성된다(§5.5).
2. **계약 test 위치 독립화**(T0): 정의가 **특정 파일에 있다고 가정하는** 계약 test 3개가 첫 이동 card에서 깨지거나 공허해진다(§7.1).
3. **이관표**(D0a·D0b): 레지스트리 '이관 목적지' 열을 N3.10 10모듈 이름으로 재생성하고, 계층 규칙(import는 작은 번호로만, 순환 0)을 **옮기기 전에** 계산으로 만족시키는 단위→모듈 배정(§6).
4. **이동**(M1~M9, 모듈 하나당 card 하나 -- 계획 N3.12.3 674행)과 **MOD10 진입점**(M10).
5. **test 재배치**(T1): `unit/test_selftest_<모듈>.py` 4개 → `unit/test_mod*.py`(계획 N3.11 test 배치 541~543행, `10-test-separation` 187·413행).
6. **호출부 갱신과 shim 삭제**(F1·F2), 모듈 속성을 덮어써 계측하는 probe의 처리(§7.2 D군, D-17). v7: shim 3파일뿐 아니라 `stick_diagram`의 임시 재수출을 지운 뒤에도
   추적 파일이 SD에서 읽는 이름이 전부 해석되는지를 DoD가 잰다(E3b, D-26 -- 4차 검토 N1).
7. `00-common` §17 표가 넘긴 `optimize_full_circuit_budget` 목적지 불일치(MOD6 대 MOD8) 해소(§6 A-3, D-3).

범위 밖(명시): 함수 분할·추출(CC-7 θ 탐색부 추출은 Phase 4, `00-common` §10.1 435행), 이름 리터럴 교체(DF-23 → Phase 4/7a), D 함수 배선(Phase 4), 레지스트리 §2 '정본 후보'의 정본 확정(B26, Phase 4), 광범위 except 정리(DF-37, Phase 4), V7 그래프 한계·Phase 3 밖의 같은 경로 import 재바인딩·클래스 수준 문장의 **게이트** 사각(§5.4 관찰 -- 백로그 후보; Phase 3 이동 card 안에서는 `move_plan check`의 `rebind`·`changed`가 닫는다).

---

## 2. 인터페이스 (N9.2-2)

A = `skills/analog-gmid-design/assets`.

### 2.1 파일 배치

| 경로 | 내용 | card |
|---|---|---|
| `A/gmid_lut.py` … `A/gmid_design_pipeline.py` | N3.10 MOD1~MOD10. **평면 배치**(하위 디렉터리 없음, D-1) | M1~M10 |
| `A/stick_diagram.py` | MOD7로 남고 줄어든다(구조 유도 함수가 MOD2·MOD3로 나간다, N3.10 527행) | M2·M3·M9 |
| `A/sizing_recipe.py` | 이관 중 **잔여 정의 + 명시 재수출 목록**(도구 생성, `_` 접두 포함, `import *` 금지 -- 534행) → F2에서 삭제 | M1~F2 |
| `A/topology_library.py`·`A/design_report.py` | N3.10 표에 없는 파일. 내용이 MOD4·MOD9로 나간 뒤 같은 방식의 재수출 shim → F2에서 삭제(D-2) | M4·M9·F2 |
| `A/audit_current_forced.py` | 도구로 남는다(`__main__` 감사 실행 경로, 레지스트리 248행 `render_report` 유지). `audit_topology`는 이관표 규칙 A-4대로(D-8) | M9 |
| `tools/migrate/move_plan.py` | 이관표·계층 사전 검사·재수출 목록·이동 대조 도구(code-author). CLI 정본 = D0a spec card 계약 1. test는 `A/tests/tooling/test_move_plan.py`(test-author) -- 계획 N3.11 549행 `tooling/`, `extract_selftest.py` 선례(D-7) | D0a |
| `tools/gates/reachability.py`·`mutate_changed.py`·`source_lint.py` | 이동 인식(`SourceIndex`·`moved_defs`, §5) -- 게이트 변경 | G1 |

### 2.2 shim 규칙

* 재수출은 `from <MODn> import a, b, _c` 형태만(명시 목록, 도구 생성 -- `move_plan plan`의 `reexports`). **def 래퍼를 두지 않는다** -- 래퍼는 동작 코드라 이동이 아니다(§3 MOVED M-2가
  이동으로 보지 않는다, 부록 A G5 `wrapper`).
* `stick_diagram.py`에서 나간 이름의 재수출은 **임시**이고 F2에서 지운다(한 이름에 import 경로 하나, WP-14). F2가 지우는 것은 **SD 자신이 읽지 않는 이름**의 재수출뿐이다 --
  SD에 남는 레이아웃 단위가 `global_names`로 읽는 이름(MOD2·MOD3로 간 `Transistor` 등)의 import는 SD의 의존이라 남긴다(3차 검토 m3).
  **v7(4차 검토 N1, D-26)**: 지울 수 있는 조건은 계획 534행 shim 문장과 같다 -- 그 이름을 SD에서 읽는 추적 파일(D-9 제외 집합 밖)을 F1이 전부 목적 모듈로 바꾼 뒤다. 판정은 **E3b**(§10):
  F2 병합본에서 추적 `.py`가 `stick_diagram`에서 읽는 이름(`from stick_diagram import N`, SD 모듈 별칭·`importlib.import_module("stick_diagram")`·그것을 돌려주는 함수 호출의 속성
  `.N`, `getattr`류의 상수 이름)이 모두 head SD 최상위에 바인딩돼 있어야 한다. 이유: SD 밖으로 가는 이름을 SD에서 읽는 곳 중 V1이 수집하지 않는 파일이 있다. **v8 재측정(5차 검토 뒤 발견한 v7 측정 결함 정정, 부록 A F1v8)**:
  `0f23786`, 근사 배정 모의 M9 트리에서 SD가 **어느 유효 범위에서도** 읽지 않는 재수출(51개)만 지운 합성 커밋 -- E3b FAIL 49줄·12파일: V1 밖 7개(`workspaces/run_harness.py`,
  `workspaces/current-reuse-telescopic-ota-report/` 아래 `structural_symmetry_probe.py`·`rerun_symmetry.py`·`stick.py`·`smoke_run_harness_session20.py`, `workspaces/two-stage-ota-report/check_box_shape*.py` 2개)와
  V1 수집 test 5개(`test_df36_instance_relpath.py`·`test_dup_kcl_edges.py`·`test_ic3.py`·`test_selftest_design_report.py`·`test_selftest_stick_diagram.py`). v7의 'FAIL 88줄'(`spice/*.py` 11개·
  `topology_to_markdown.py`·`audit_current_forced.py` 등 포함)은 모의 F2가 SD 모듈 최상위 symtable의 `is_referenced()`만 보고 **함수 몸체에서만 읽는 이름**(`load_topology`·`Transistor`·
  `kcl_series_union` 등 재수출 11개)까지 지운 과대 삭제였다 -- 실제 F2는 그 import를 남긴다(위 m3 문장). 판정 명령(E3b)은 그대로이고 모의 입력만 틀렸다.
  F1이 하나를 빠뜨리면 F2 뒤 V1 밖 파일은 조용히 깨지고 GONE-SHIM·E3·IMPORT-ANY는 그것을 보지 않는다.
* **재수출 줄의 위치**: split 파일의 재수출 줄은 그 파일의 import 머리 바로 뒤에 둔다(남은 모듈 수준 문장이 import 시점에 그 이름을 읽기 전에 묶인다 -- 모의에서 끝에 두면 M8에서
  `NameError`, `p3v6_order_shim_sim` 첫 판).
* **SD의 위쪽 임시 재수출과 순환(D-22, v6 모의에서 새로 드러남)**: N3.10이 MOD9로 보내는 SD 단위(`save_instance_json` 계열 -- 모의 배정 `save_instance_json`·
  `run_full_circuit_audit_from_topology`·`_audit_result_json`·`_box_shape_json`·`_topology_ref_relpath`)는 추적 test·하네스가 F1까지 `from stick_diagram import …`로 읽으므로
  (`test_df36_instance_relpath.py:87·237·274·288`, `test_selftest_design_report.py:25`, `run_harness.py:42` 등) M9부터 F2까지 SD가 MOD9에서 그 이름을 재수출한다. 그런데 MOD9는 SD의
  레이아웃 이름(`run_full_circuit_audit`·`AuditResult`·`check_instance_completeness` 등)을, MOD8은 SD를 import한다 -- **SD(7) → MOD9 위쪽 import와 순환 SD ↔ MOD9(↔ MOD8)**가 생긴다.
  모의(`p3v6_order_shim_sim.pull_top.json`): import 줄을 모두 파일 머리에 두면 M9 병합본에서 `instance_report_builder`·`design_report`를 **먼저** import한 새 프로세스가
  `ImportError: cannot import name '_audit_result_json' from 'instance_report_builder'`(부분 초기화). V1이 우연히 SR을 먼저 import하면 드러나지 않다가 F1(test가 MOD9를 직접 import)에서
  터진다. 규칙(함수 안 지연 import로 우회하지 않는다 -- F3):
  (1) SD의 MOD 8·9 재수출 줄은 SD **끝**에 둔다. (2) MOD8·MOD9 파일은 번호 7 이상 모듈(SD·MOD8)의 import 줄을 **파일 끝**(모든 단위 뒤)에 두고, 번호 7 미만 MOD의 import는 머리에 둔다
  (모듈 수준 문장이 import 시점에 읽는 이름은 7 미만 MOD에서 온다 -- 모의에서 MOD9의 import를 전부 끝에 두면 레지스트리 dict 문장이 `NameError`, `p3v6_order_shim_sim.bottomall.json`).
  (3) M card마다 IMPORT-ANY(§3)로 확인한다. 모의(`…pull_bottom7.json`): 이 배치로 M1~M9 모든 card에서 모듈마다 단독 import 성공(v7: `a796468`에서 재실행해 같은 결과).
  **(2)의 전제(v7, 4차 검토 S5)**: 이 배치는 "MOD8·MOD9가 import 시점에 읽는 이름(모듈 수준 문장, 데코레이터·기본값·기반·키워드, 클래스 몸체, `__future__` 없는 파일의 주석)의
  출처가 번호 7 미만 MOD"일 때만 성립한다. 지금은 사실이다(`a796468` 실측, 부록 A F4v7: SR·DR·TL·`audit_current_forced`에서 SD 이름의 import 시점 읽기 0, 모의 M9 트리의 MOD8·MOD9에서
  출처가 SD·MOD8인 import 시점 읽기 0). 그러나 규칙이 보장하지 않으므로(D0b의 실제 배정이나 B26-1의 `rails: RailDeclaration` 같은 주석이 깰 수 있다) **D0b 계약 test가 단언한다**(§8 D0b행):
  위반이면 위치 규칙으로 풀 수 없다(머리 배치 = 순환, 끝 배치 = `NameError`, 지연 import = 금지) -- D0b가 멈추고 배정을 바꾼다(N3.10 밖이면 D-11 승인).
  (4) 위쪽 import는 M9~F1 동안 `import_layering`이 `큰 번호로의 import`·순환으로 보고한다(모의 M9 트리 실측) -- LAYER는 DoD(F2 뒤) 판정이고(§3), F2가 SD의 위쪽 재수출을 지우면 사라진다.
  F2는 끝에 둔 import 줄을 머리로 올려도 된다(import 줄만 차이).
* 모듈 수준 캐시(`sizing_recipe.py:2391 _KNEE_L_CACHE`, `:2530 _FEASIBLE_L_WINDOW_CACHE`, `:7697 _ACHIEVABLE_BOUND_CACHE` -- 셋 다 주석 대입 `: dict = {}`, 사용 함수는 각각 하나
  `knee_L_for_kind`·`feasible_L_window`·`achievable_metric_bound`; `topology_library.py:248` `@functools.lru_cache(maxsize=256)` 1곳 -- 254행은 주석)는 **읽고 쓰는 함수와 같은 모듈로**
  옮긴다(판정 CACHE-ID, NFR-2). 판정 도구는 `move_plan check`의 `cache` 발견이다. V6 `unbounded_cache`는 `ast.Assign`만 보므로 이 셋(주석 대입)을 보지 않는다 -- 그래서 CACHE-ID를
  게이트가 아니라 D0a 도구로 잰다. `global` 문 0개라 재수출 이름은 같은 객체를 가리킨다(부록 A M18; SHIM 판정 참고).

### 2.3 MOD10 진입점

* 정본 시그니처 `00-common` §10.1 431행: `run_gmid_design_pipeline(spec, *, search, output_dir, instrument=None, activations_out=None)`. **Phase 3(M10)는 `spec`·`topology_path`·`search`·`output_dir`까지만** 만든다 -- 하네스 `run()`(`workspaces/run_harness.py:422`)의 파이프라인 몸통을 옮기는 데 탐색 설정과 출력 경로가 필요하다. `instrument`·`activations_out`은 CC-7·CC-8(Phase 4).
* **정본 시그니처의 빈칸(실측)**: 하네스는 topology 경로를 spec이 아니라 `SPECS[circuit]["topology_file"]`에서 만들어(`run_harness.py:427`) `optimize_full_circuit_budget(topo, spec, …)`(446행)에 따로 넘긴다. 431행 시그니처로는 진입점이 topology를 찾을 수 없다 → 키워드 인자 `topology_path`를 더한다(D-5).
* M10은 이동이 아니라 **추출**(새 def + 하네스 `run()` 몸체 변경)이라 V3 대상이다. 지금 인벤토리(부록 A S12): `run_harness.py::run`에 도달하는 test 60개는 전부 `build_graph`의 이름 과대 근사
  (`subprocess.run`류 속성 호출 → 같은 이름의 모든 def)로 이어진 것(`tooling/test_extract_selftest.py` 24, `unit/test_selftest_sizing_recipe.py` 22 …)이고 하네스를 실제로 실행하지
  않는다 -- 변이를 죽이지 못한다. 그래서 **M10은 red-green**(새 test가 진입점을 library 회로로 불러 E-INST 해시를 대조, base에는 진입점이 없어 red)이다(§8).
* **M10 V3 비용(v6, 3차 검토 S3)**: M10은 Phase 3에서 V3 변이가 생기는 거의 유일한 card다(나머지는 G1 이동 제외로 `defs` = `[]`). 대상 = 새 진입점 본문 전체 + `run()`의 바뀐 문장(범위 정책 N2).
  HEAD `run`(422~529행) 변이 71개(3차 검토 실측) → **추정 약 70**. V3는 변이마다 인벤토리 test를 `-x`로 돌리므로(`mutate_changed.py:350`) 변이 비용 ≈ 첫 실패까지의 test 시간이다.
  * 회로(v8 정정 -- 5차 검토 S4): E-INST test는 **instance.json을 만드는 회로(= E-INST 회로 집합, `20-dead-code-dup` §3: 파일럿·`folded_cascode`) 중 한 판이 가장 짧은 것**으로
    부른다 = **`folded_cascode`**. 판정 기록 실측 E-INST 한 판: `folded_cascode` 13~19초, `current_reuse_telescopic_ota` 98~137초
    (`.ai/verification/20260930-dup-w-calc/einst_time.txt`·`20260930-restore-plan-functions/einst_time.txt`), 파일럿 판당 7~8분(`dryrun_phase2_e4.md`). `two_stage_ota`·`nmcnr_amplifier`는
    v7 측정(`p3v7_m10_trace.*.json`)에서 `optimize_full_circuit_budget`이 `ValueError`로 끝나 instance.json을 만들지 않는다(`inst_sha: null`, `fail_in_stdout: true`, 31.4·33.9초) --
    E-INST 회로가 아니므로 '가장 짧은 회로' 후보가 아니고, 아래 (ii)의 실패 경로 보조 회로로만 쓴다.
  * 추정(근거: 위 실측 + `p3v6_m10_inventory_time.json` -- `7535799` 복제본에서 `run` 인벤토리 60 test id(파일 8개)를 V3와 같은 pytest 설정으로 한 번 실행: 71 passed·3 xfailed,
    **143초**): `folded_cascode`면 변이를 E-INST test가 죽일 때 약 70 × (기동 + 약 20초) ≈ **30~40분**, 하나도 못 죽이는 최악이면 70 × (20초 + 143초) ≈ **3.2시간**.
    파일럿이면 70 × 8분 ≈ 9시간 이상(최악 약 12시간)이고 B28 `--timeout` 600초에 가까워 느린 변이가 '죽음'으로 셀 위험이 있다(3차 검토 S3) -- 회로 선택이 비용의 대부분을 정한다.
    (`-x`라 수집 순서상 E-INST test가 이름 과대 근사 test보다 앞이면 죽는 변이는 그 test에서 멈춘다 -- 배치는 test-author 몫이고 판정에 영향 없음, 비용만.)
  * M10 '작성 전 실측'(card 작성 때): (1) 병합본 base에서 M10 대상 def의 변이 수(`mutate_changed`의 변이 생성만 -- `run` 몸체를 옮긴 초안에서) (2) E-INST 회로 두 개와 실패 경로 보조 회로 하나의 한 판 시간 (3) 인벤토리
    한 번 실행 시간 → 추정치 = 변이 수 × (기동 + 회로 시간) + 생존 추정 × 인벤토리 시간을 card에 적는다(판정 근거 아님, 실행 계획용).
  * **v7 정정 -- 위 추정은 '변이를 E-INST test가 죽인다'는 가정이었고 틀렸다(4차 검토 S3).** 지금 `run()`(`a796468`)의 변이 71개(stmt_delete 58·cmp_flip 9·except_body_delete 3·
    early_return 1)를 `folded_cascode`로 **하나씩 실제 실행**했다(부록 A F6v7, `p3v7_m10_summary.json` -- M10은 이 문장들을 진입점으로 옮기므로 생존 모양이 같다). 기준 실행은 결정적이다
    (두 번 실행해 instance.json·stdout·report 해시 같음). test 모양별 생존:

    | test가 대조하는 것 | 생존 | 그중 `print` 문장 | 그중 `folded_cascode`가 지나가지 않는 줄 | 어느 회로도 지나가지 않는 줄 |
    |---|---|---|---|---|
    | instance.json 해시만(E-INST 정의 그대로 -- v6 계획) | **50** / 71 | 18 | 24 | 13 |
    | + stdout의 `[FAIL]` 유무 | 46 | 18 | 23 | 12 |
    | + stdout 전체 해시 | **24** | 9 | 18 | 7 |
    | + report.html 해시 | 24(`folded_cascode`는 report를 만들지 않는다) | 9 | 18 | 7 |

    회로별 도달(같은 스크립트 `trace`, 부록 A F6v7): `folded_cascode`는 감사 `except ValueError` [SKIP]·note 분기·report 생략 경로, `current_reuse_telescopic_ota`(파일럿)는 감사 성공·report 저장 경로
    (이 측정에서 616초 -- 다른 측정과 겹침, 기록 98~137초), `two_stage_ota`·`nmcnr_amplifier`는 `optimize_full_circuit_budget`이 `ValueError`(모든 θ infeasible)로 `except Exception` +
    `diagnose_sizing_roles_gap` 진단 경로(31~34초, instance.json 없음 -- E-INST 회로가 아니다). 어느 회로도 지나가지 않는 줄: 알 수 없는 키의 `raise`(424), `pr is None`(451·511),
    `layout_retry_rounds` 출력(454), 감사 FAIL note(500). **stdout까지 대조해도 남는 24개**: 진입 전 준비 문장(`circuit_key` 검사·`raise`·`report_out`·두 `spec.setdefault` -- 423·424·431·438·442,
    setdefault 둘은 `folded_cascode`에서 결과가 같아 출력 대조로 죽지 않는다), `pr is None`·재시도 출력(451·453·454·511), 감사 성공 출력(473~475), 감사 FAIL note(499·500), report 저장(505~507),
    `except Exception`·진단 분기(512·524~528), 비교 뒤집기 1개.
    **그래서 '작성 전 실측'에 더할 것(M10 card가 정한다 -- 판정 기준 불변, 생존은 V3 FAIL이고 면제는 사용자 승인)**:
    (i) **옮길 문장 범위**: 회로 키 검사·경로 계산·`spec` 생성·`setdefault` 두 줄은 `run()`에 남기고 진입점은 `spec`·`topology_path`·`search`·`output_dir`를 받아 `try` 몸체부터 옮긴다
    (`run()`은 바뀐 def라 범위 정책 N2로 바뀐 문장·T5·T6만 대상 -- 남긴 준비 문장 13개 변이는 대상 밖). `print`는 진입점에 그대로 둔다(옮기며 출력 위치를 바꾸면 이동이 아니라 재구성이다).
    (ii) **test 모양**: 진입점 test는 instance.json 해시에 더해 **stdout 전체**(`folded_cascode`는 결정적 -- 실측. v8 관찰: 파일럿 stdout은 SLSQP 진행 줄에 경과 시간 `elapsed=<초>s`를 찍어 바이트로는 결정적이지 않다 -- 부록 A F3v8. 파일럿을 쓰지 않는 이 test에는 영향 없음)와 report.html(만드는 회로에서) 해시를 base 하네스와 대조한다. 회로는 `folded_cascode`(D-25) +
    실패 경로 회로 하나(`two_stage_ota` 또는 `nmcnr_amplifier`, 31~34초 -- `except`·진단 분기 6개). (iii) **분기 계약**: 어느 회로도 지나가지 않거나 파일럿만 지나가는 분기(`pr is None`·재시도 출력·
    감사 성공/FAIL note·report 저장, 약 13개)는 진입점이 이름으로 읽는 `optimize_full_circuit_budget`·`run_full_circuit_audit_from_topology`·`save_html_report`를 test가 진입점 모듈 속성으로
    바꿔(합성 반환값) 그 분기의 stdout·호출 인자를 대조하는 계약으로 죽인다(회로 실행 없음, 초 단위). 파일럿은 쓰지 않는다(판당 98~137초, 변이마다 곱해진다).
    (iv) **비용 다시 추정**: 대상 ≈ 진입점 본문 변이 약 58 + `run()` 바뀐 문장 몇 개. (ii)(iii)대로면 생존 0을 목표로 변이당 첫 실패까지 ≈ 분기 계약 몇 초 또는 `folded_cascode` 한 판(기록 13~19초) →
    **약 20~40분**. v6 계획(E-INST 해시만)이면 생존 약 50 × (회로 + 인벤토리 143초) + 죽는 21 × 회로 ≈ **2.5시간 이상이고 V3 FAIL**이다 -- 생존 하나마다 약 2.5~3분이 더해진다.
    (v) D-25는 **새 진입점 test의 회로**만 정한다. M10 equivalence 몫의 E-INST 회로 집합은 `20-dead-code-dup` §3 정의(파일럿·`folded_cascode`) 그대로다.

### 2.4 새 함수·도구의 원칙(모든 card에 계약으로 들어간다)

* **topology 무관**: G1·D0a 도구는 코드 구조만 읽는다 -- `library/`·`*.topology.json`을 읽지 않고 회로·넷·소자 이름 리터럴이 없다. 합성 저장소(회로 없음)에서 동작함이 그 증거다.
* **만들면 배선**: `moved_defs`는 V3·V6·V7 세 도구의 `main`이 부르고, `SourceIndex`는 `moved_defs`와 `move_plan.py`가 부른다(G1). `move_plan.py`는 (i) D0b 계약 test가 매 card V1에서
  `plan`을 부르고 (ii) M card마다 판정 `equivalence.commands`에 `check`가 들어가며 (iii) DoD E2·E4·E6이 부른다. `plan`은 규칙 A-0 때문에 **Phase 어느 시점에서도** 같은 배정을 내므로
  (i)이 Phase 중간에 끊기지 않는다(검토 B4).
* **재계산 없음**(NFR-2): base·head 트리의 색인(`SourceIndex`)은 도구 실행당 커밋마다 한 번 만든다(파일마다 `ast.parse`·`symtable` 1회). `move_plan.py`는 한 번의 실행으로 배정·계층·
  재수출·순서·열 대조를 같이 낸다.
* **정의 하나**: 이동 판정의 해시 정의는 `def_hash` 하나다(G1이 `reachability`로 옮기고 `mutate_changed`는 import -- 이름·시그니처 유지). 면제 묶기 card의 **묶기 해시**(docstring·데코레이터
  포함 def 원본의 `ast.dump` sha256)는 용도(면제 대조)가 다른 별개 정의다 -- G1은 그것을 읽거나 바꾸지 않고, 이동 판정에 쓰지 않는다(§5.5.3). '모듈 전역에서 읽는 이름'·'이름의 바인딩 출처'도
  `reachability.SourceIndex` 하나다. `move_plan.py`는 계층 표를 `import_layering.mod_table`, 대표 대상 열을 `role_paths.read_section_table`, 참조·이동·해시를 G1 이름으로 읽는다.
* **작성자≠검증자**: 도구의 test는 test-author가 interface card만 보고 합성 입력(oracle (a))으로 쓴다. 판정 수치는 auditor 판정 기록에서만 인용한다. 이동 card의 판정 도구(`move_plan.py`)는
  **`tools/migrate/move_plan.py`를 마지막으로 바꾼 판정 기록의 `code_commit`**(지금은 D0a)에서 꺼낸 사본을 쓴다(M card code-author가 같은 card에서 바꿀 수 없다 -- §8, 1차 검토 S9·2차 검토 m6).

---

## 3. 판정식 (N9.2-3)

숫자를 박지 않는다(WP-03). 모두 `영역: 없음(스키마)`. E-LIB·E-INST는 `20-dead-code-dup` §3 정의를 그대로 쓴다(재서술하지 않는다). '판정 도구' 열이 비지 않는 것만 판정식이다(만들면 배선).

**단위**: 소스 파일(`reachability._is_source`: `A/*.py`, `workspaces/run_harness.py`)의 최상위 **함수**(해시 `def_hash`), 최상위 **클래스 골격**(ClassDef에서 안의 모든 def를 이름 표지로
바꾼 사본의 `def_hash` -- 머리·데코레이터·클래스 수준 문장·메서드 이름과 순서 포함, 메서드 몸체 제외), 최상위 **문장**(import·def·class·`if __name__` 블록 밖, 문장 `ast.dump` 해시 --
문장은 해시로만 식별). **바인딩** = 모듈 공간(def·class·lambda·컴프리헨션 몸체 밖)에서 이름이 `Store`/`Del` 문맥이거나 import·def·class·`except … as`·`match` 포획·`type` 별칭으로
묶이는 모든 곳(증강 대입·walrus·`del` 포함 -- 2차 검토 S2). **바인딩 출처** `binding_origin(p, n)` = 모듈 p 최상위에서 n이 가리키는 정의를 `from … import` 사슬을 따라가 얻은
`("def", 파일, 이름)`(또는 `ext`·`ext-module`(**가져오는 파일의 디렉터리 포함**)·`module`·`builtin`·`unbound`·`multi`·`star`(**모듈에 star import가 하나라도 있으면 모든 이름**)·
`global-dynamic`(**모듈 어디서든 `global` 선언된 이름**, 경로 포함)·`cycle`·`file-dir`(`__file__`)·`module-identity`(`__name__` 등·`globals`/`eval`/`exec`) -- 2차 검토 S1).
**전역 읽기** `global_names(u)` = u와 그 안 모든 유효 범위에서 Python 유효 범위 규칙상 모듈 전역으로 해석되는 이름(문장 단위도 같은 규칙 -- lambda 인자·컴프리헨션 대상은 지역) ∪
데코레이터·기본값·기반·키워드의 이름 ∪ 주석(문자열 주석 포함)의 이름. 정확한 문언은 G1 spec card 계약 0~3.

| ID | 판정 | 식 | 판정 도구 |
|---|---|---|---|
| E-LIB / E-INST | 동작 보존 | `20-dead-code-dup` §3 | 그 정의의 측정 명령. **v8(5차 검토 S1, D-28)**: E-INST는 Phase 3 모든 card·DoD에서 같은 해시 정의를 재는 `e_inst_p3.py`(design 커밋이 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/`에 넣는다 -- F1 뒤 `e_inst_df36.py`는 `sys.modules["sizing_recipe"]` `KeyError`), E-LIB는 M card에서 `e_lib.py` 사본 그대로, DoD E5에서 `e_lib_p3.py`(v8.2 -- `e_lib.py`에 meta 키를 빼는 인자 하나를 더한 사본, D-28·§10 E5) |
| MOVED | 이동 인식(G1) | head 단위 u = (p_h, 키 q, 해시 h)가 **옮긴 단위** ⇔ (M-1) base에서 (종류, q, h)를 가진 소스 파일이 정확히 하나 p_b ≠ p_h(파일 안에서도 하나) (M-0) u가 바인딩하는 이름마다 base p_h의 바인딩 출처가 없거나 `("def", p_b, 이름)`(**덮어쓰기 거부**) (M-0h) u가 바인딩하는 이름마다 **head** p_h의 바인딩 출처 = `("def", p_h, 이름)` -- 목적 파일에서도 u가 그 이름의 유일한 바인딩(`multi`·`star`·`global-dynamic`이면 거부: **목적 파일의 조건부 재정의·재바인딩 거부**, 2차 검토 B1 (1)의 M-0') (M-2) head p_b에 같은 단위가 없고 p_b에 남은 그 이름의 출처는 없거나 `("def", p_h, 이름)`(재수출뿐) (M-3) head에서 (종류, q, h)가 p_h 한 곳 (M-4) p_b와 p_h의 `__future__` 기능 집합이 같고(2차 검토 S3), `global_names(u)`의 이름마다 base p_b의 출처 = head p_h의 출처, 또는 head 출처가 함께 옮긴 단위이고 그 원본 출처가 base 출처(**재바인딩·`__file__`·import 디렉터리 변경·star 가림·`global` 쓰기 대상 거부**, 고정점). 메서드는 클래스 골격이 옮겨지고 자기 해시가 원본과 같을 때만 옮긴 def(**클래스 머리·필드 변경 거부**). **옮긴 def**(V3·V7 제외 목록)에는 p_b 또는 p_h에서 qualname이 둘 이상인 def를 넣지 않고(property getter/setter 등, 2차 검토 B1 (2)), V3·V7은 (경로, qualname, `def_hash`)가 모두 같을 때만 뺀다(B1 (3)) | `reachability.moved_defs`(V3·V6·V7이 부름) |
| MOVE-AST | 이동 동일성(533·1018행) | card k의 병합본에서 (a) 이 base→head에서 MOVED가 낸 **모든** 옮긴 단위 집합 = 이관표가 card k에 배정한 **최상위 단위**(함수·클래스·문장) 집합이고 목적지가 전부 card k의 MOD 파일(2차 검토 S4) (b) 옮긴 단위가 아닌데 해시가 바뀌었거나 새로 생긴 단위 0(클래스 골격·문장 포함 -- V3가 보지 않는 클래스 필드 기본값 변경도 여기서 잡힌다) + 옮긴 클래스 안 def의 해시가 원본과 다른 것 0(2차 검토 S6) (c) 사라진 단위 0 (d) MOVED가 거부한 후보 0 (e) 옮긴 단위·제자리 단위 모두 전역 읽기 출처가 base와 같음(옮긴 단위 사상 적용 -- import 줄 교체 거부, 2차 검토 S5) (f) 목적 파일 `__future__` ⊇ 원본(S3) (g) 옮긴 문장 단위의 원본 상대 순서 보존(m2) | `move_plan check`(`move-set`·`changed`·`lost`·`move-rejected`·`rebind`·`future`·`stmt-order`) + card마다 V3 JSON `defs` = `[]`(§8 M행, §10 E2) |
| MOVE-TOTAL | 정의 보존 | Phase 전 base와 Phase 후 병합본 사이에서 MOVE-AST (b)(c)(d)를 전 단위로: 바뀐·새·사라진 단위는 M10이 선언한 것(`run_harness.py::run`, `gmid_design_pipeline.py::run_gmid_design_pipeline`)뿐 | `move_plan check --card ALL --allow-changed …`(E6) |
| PLAN-LAYER | 이동 전 계층 사전 검사 | 이관표 σ에서, 단위 u의 참조 R(u)(`global_names`의 이름 중 출처가 split·MOD 파일의 정의인 것 + 그 파일 모듈 별칭 속성, 중첩 def·메서드 포함 -- 문자열·해석 못 한 이름 제외) u→v 중 σ(u) < σ(v)인 것 0, 모듈 순환 0 | `move_plan plan`(`upward`·`cycles`) |
| LAYER | 계층 | Phase 3 마지막 병합본(F2 뒤)에서 `import_layering.py --root <iso>` exit 0. M9~F1 중간 상태의 SD → MOD9 임시 재수출(§2.2 D-22)은 이 판정의 대상 시점이 아니다 -- 중간 상태는 ORDER·IMPORT-ANY가 맡는다 | 그 도구(E1) |
| ORDER | 중간 상태 | card k 병합본에서 `--card` 파일(MOD k)의 import 문(모듈 수준, 함수 안 포함 -- 엔진 4파일에 함수 안 엔진 import 0)이 가리키는 트리 파일 f마다: f가 **N3.10 파일이면 그 번호 < k**(f가 `--split`에 있어도 N3.10 번호로 판정 -- `stick_diagram.py` = MOD7), f가 **N3.10 밖의 `--split` 파일이면 위반**(잔여 shim·도구 import 금지), 그 밖의 트리 파일(N3.10·split 밖, 예 `analog_grammar` 쪽 모듈)은 판정 밖(`import_layering`과 같은 범위). 3차 검토 B1: v5 문언("`--split` 파일이거나 …")은 MOD8·MOD9가 MOD7 레이아웃 이름을 읽으려고 `stick_diagram`을 import하는 것(`sizing_recipe.py:5302`·`design_report.py:32`가 지금 하는 import)을 위반으로 잡아 M8·M9가 통과할 수 없었다 -- 모의 `p3v6_order_shim_sim`: 옛 문언 M8·M9 발견, 새 문언 M1~M9 발견 0 | `move_plan check`(`order`) |
| SHIM | 재수출 정확성 | head에 있는 `--split` 파일마다 (a) **중간 상태**: base에 없던(문장 `ast.dump` 다중집합 차) head 최상위 문장은 전부 `from <MOD 줄기> import …` 재수출 줄이다(남은 단위의 변경·삭제는 `changed`·`lost`가 맡는다) (b) **완전 shim**(N3.10·`--keep` 밖 split 파일이고 head에 그 파일의 단위가 0개 -- 배정된 단위가 전부 옮겨진 card): 최상위 문장이 docstring, 재수출 줄, (선택) `from __future__ import …` 줄뿐 (c) 두 경우 모두 재수출 이름 집합 = (base 재수출) ∪ (이 card가 그 파일에서 옮긴 이름), 이름마다 shim의 바인딩 출처 = MOD의 바인딩 출처(출처가 같으면 import가 같은 객체를 묶는다 -- `getattr(shim, s) is getattr(MOD, s)`의 정적 형태. 실행 중 속성 덮어쓰기는 §7.2 D군), base에 있던 `if __name__ == "__main__"` 블록 불변(2차 검토 m3). `--card ALL`(E6, base = M1 base, head = F2 뒤)에서는 (c)의 **이름 집합** 대조를 하지 않는다 -- F1이 남는 파일(`audit_current_forced.py`)의 import를 MOD로 바꾸고 F2가 SD의 임시 재수출을 지운 뒤라 이름 집합은 card 단위 정의와 다르다. (a)와 출처 동일성은 그대로. 3차 검토 B2: v5 문언("docstring과 `from <MOD> import …` 밖 문장이 있으면")은 잔여 정의가 있는 중간 card마다 SR·TL·DR을 위반으로 잡고(모의 M1 SR 214건 등) 최종 shim의 `from __future__` 줄도 잡았다 -- 모의: 옛 문언 M1~M9 모두 발견, 새 문언 (a)(b) M1~M9 발견 0, 완전 shim은 TL이 M4, SR·DR이 M8 또는 M9(배정에 따라) | `move_plan check`(`shim`) |
| IMPORT-ANY | 중간 상태 import 가능(v6, D-22) | card 병합본에서 그 트리에 있는 N3.10 파일과 `--split` 파일 각각을 **새 파이썬 프로세스에서 맨 처음으로** import하면 성공한다(어느 모듈을 먼저 import해도 순환 import의 부분 초기화가 드러나지 않는다). **v7(4차 검토 S2)**: 모듈 목록 계산이 실패하거나 비면 INVALID, 실제로 import를 시도한 수 = 그 트리의 기대 수(`import_layering` `present` ∪ 트리에 있는 `--split` 파일)여야 한다 -- 둘이 다르거나 0이면 INVALID | §10의 `import_any` 명령(M card `equivalence.commands`, E5 앞) |
| CACHE-ID | 캐시 단일성(NFR-2) | 모듈 최상위 캐시(이름에 `cache`, 값이 빈 dict -- 대입·주석 대입)를 전역 읽기로 쓰는 단위가 모두 캐시와 같은 파일 | `move_plan check`(`cache`) |
| LOC-FREE | 위치 독립(T0) | 계약 test의 판정이 '정의 파일'을 이름으로 가정하지 않는다 -- 같은 test가 base 트리와 **정의 하나를 다른 파일로 옮긴 합성 트리**에서 같은 결과 | T0 계약 6·7(auditor 합성 트리 실행) |
| GONE-SHIM | shim 삭제 | 마지막 card 병합본에서 `sizing_recipe.py`·`topology_library.py`·`design_report.py` 없음, 추적 `.py`의 해당 import(줄 머리와 문자열 import 모두) 0(제외 집합 D-9 밖). 도구 오류(git 실패·`git show` 실패·파이썬 비정상 종료)는 FAIL(v7 -- 4차 검토 S1) | §10 E3 |
| SD-NAMES | SD 임시 재수출 삭제 뒤 이름 해석(v7, D-26 -- 4차 검토 N1) | 마지막 card 병합본에서 D-9 제외 집합 밖 추적 `.py`가 `stick_diagram`에서 읽는 이름 N(`from stick_diagram import N`, 그리고 **SD 모듈 식**의 속성 `.N`과 `getattr`·`hasattr`·`setattr`·`delattr(SD 모듈 식, "N")` -- SD 모듈 식 = `import stick_diagram [as a]`의 이름, `importlib.import_module("stick_diagram")`·`_import`·`__import__` 호출, 그것을 대입받은 이름, 그것을 돌려주는 함수의 호출)마다 head `stick_diagram.py` 최상위 바인딩(정의·import)이나 모듈 기본 속성(`__file__` 등)이 있다. base에서 이미 풀리지 않던 (파일, 이름)은 뺀다(`a796468`·`0f23786` 1건 -- §11-10). star import·동적 이름·파싱 오류는 풀리지 않는 이름으로 FAIL이고 **base에 이미 있어도 빼지 않는다**(v8 -- 5차 검토 B2: v7 식은 표지 이름이 base SD에서 풀리지 않는다는 이유로 면제했다), 도구 오류는 FAIL. **거부 확인**: base(M1 판정 기록 `base_commit`)의 SD 정의 중 head SD에 정의가 없는 이름(= Phase 3가 SD 밖으로 옮긴 이름)이 1개 이상이고, base에서 그 이름을 SD에서 읽는 추적 파일이 1개 이상이어야 한다(아니면 INVALID) | §10 E3b |
| REG-DEST | 레지스트리 = 실제 위치(1018행) | 레지스트리 함수 행의 목적지 셀이 MOD 파일 이름 하나이고, 그 단위의 배정 MOD(= 이동 뒤에는 규칙 A-0의 현재 파일)와 같다 | `move_plan plan`(`reg_mismatch`, A-0) |
| LAYOUT-FLAT | 평면 배치 | MOD1~MOD10 파일이 전부 `A/` 바로 아래 | E0(`import_layering` `present`) |
| ENTRY | MOD10 | `run_gmid_design_pipeline`이 있고 `workspaces`를 import하지 않으며 하네스 `run()`이 그것을 부른다 | M10 spec card(red-green) |

---

## 4. 실패 경로 (N9.2-4)

Phase 4 전이라 N3.14 실패 클래스가 없다(`20-dead-code-dup` §4와 같은 상황).

| ID | 경우 | 결과 | 처리 |
|---|---|---|---|
| F1 | PLAN-LAYER FAIL | 이동하지 않는다 | §6 규칙으로 배정을 고친다. 규칙으로 안 풀리면 N3.10 표 개정(이 design 승인 범위 -- §9 D-11) |
| F2 | MOVE-AST FAIL(옮기며 본문·클래스 머리·필드가 바뀜) | V2 FAIL(G1 뒤에는 V3 대상도 생긴다) | card 되돌림. 본문 수정이 필요한 이동은 Phase 3가 아니다 |
| F3 | 중간 상태 순환 import(v6: M9~F1의 SD ↔ MOD9 -- §2.2 D-22) | V1 수집 오류, 또는 V1이 우연히 다른 모듈을 먼저 import해 숨기고 F1에서 드러남 | 순서·import 줄 위치를 고친다(§2.2 D-22 규칙), IMPORT-ANY로 card마다 확인. 함수 안 지연 import로 우회하지 않는다(우회 = skip, 메모리 원칙). **v7(4차 검토 S5)**: MOD8·MOD9가 import 시점에 출처 번호 7 이상 모듈의 이름을 읽는 배정이면 위치로 풀 수 없다 -- D0b 계약 test의 단언(§8 D0b행)이 이관표 단계에서 먼저 거부하고, 배정을 바꾼다(N3.10 밖 개정이면 D-11 승인) |
| F4 | E-LIB·E-INST 차이 | V2 FAIL | 모듈 수준 상태 분리를 먼저 의심(CACHE-ID) |
| F5 | G1 병합 전 이동 card | 판정 불가(V3 변이 약 1.6만 개(15,650), V6 새 항목 859, V7 미도달 약 108 -- v8.4: G1 착수 키트가 `0f23786`에서 다시 잰 값(P9 전 `cd64170` 값은 15,677·861); B33 병합 뒤에는 약 39로 줄 것으로 추정(B33 시제품, 소스 전체 기준), 그래도 0이 아니다 -- §5.1·§5.5.4) | G1 병합 전에는 M card를 시작하지 않는다(§8) |
| F6 | 계약 test가 첫 이동에서 깨지거나 공허해짐 | equivalence 불성립 | T0 병합 전에는 M card를 시작하지 않는다 |
| F7 | MOVED 거부(`move-rejected` M-0/M-0h/M-4) | 옮긴 단위가 아니라 V3 대상·`changed` | 배정을 따라 **함께 옮길 것을 함께** 옮기거나(재바인딩 대상이 이 card 배정이면) 새 MOD가 원본과 같은 출처에서 import하게 import 줄만 고친다(`from __future__ import annotations` 포함). 몸체를 고치지 않는다 |
| F8 | 모듈 속성 덮어쓰기 probe가 이동 뒤 계측을 잃음(§7.2 D군) | probe 결과가 조용히 비거나 달라짐(V1이 probe를 수집하지 않아 FAIL로 드러나지 않는다) | D-17대로 F1에서 덮어쓰기 대상을 호출자 모듈로 옮긴다 |
| F9 | (v7) F1이 SD에서 옮긴 이름을 읽는 추적 파일을 빠뜨린 채 F2가 SD 재수출을 지움(4차 검토 N1) | V1 밖 파일은 조용히 `ImportError`·`AttributeError`, DoD **E3b FAIL**(그 파일·줄·이름) | F2를 되돌리거나 빠진 파일을 F1 범위로 고친 뒤 F2를 다시 판정한다. 그 재수출을 남기는 것은 WP-14 위반이라 처리가 아니다 |

---

## 5. 게이트의 이동 인식 (G1)

### 5.1 실측: 지금 게이트는 옮긴 정의를 새 정의로 본다

| 도구 | '새/바뀐 def'를 정하는 곳(`7535799`, B28 병합 뒤) | 옮긴 정의에 대한 결과 |
|---|---|---|
| V3 `mutate_changed.py` | `changed_defs(base_src, head_src)`(88~100행, `_strip_doc` 74·`def_hash` 84)이 **같은 경로**의 base 소스와만 비교. `main`이 `git cat-file -e <base>:<path>`(359행)로 base 파일이 없으면 `base_src = None`(361행) → 그 파일의 def 전부가 대상(`changed_defs` 호출 364행). diff는 `--no-renames --diff-filter=AM`(314행). test 실행 환경은 B28의 `make_clone`(53행 정의, 323행 호출 -- 옛 `copytree` 없음), 정리 `_rmtree_force`(406행), 출력 398·402(ERROR)·407(PASS/FAIL) | 엔진 4파일을 새 파일로 옮기면 대상 def 473개·변이 15,650개·V6 새 항목 859(v8.4: G1 착수 키트 `0f23786` 재측정 -- 부록 A G1의 15,677·861은 P9 전 `cd64170` 값, P9가 SD를 고쳐 −27·−2). 인벤토리 없는 def는 변이 전부 '생존' |
| V6 `source_lint.py` | `compare(path, base_src, head_src, kd)`(212행)가 같은 경로 base와 단위별 항목 수 비교, base 없으면 전부 '새 항목' | 새 파일로 옮기면 새 항목: magic_number 500·continue 347·broad_except 8·id_call 6(부록 A G1) |
| V7 `reachability.py` | `base_defs` = base의 (파일, qualname) 집합(224~229행), `new_defs` = head 노드 중 그 집합에 없는 것(230~231행) | 지금 운영 루트로 도달하지 못하는 엔진 def 109개(승인 면제 1) -- 옮기면 전부 '새 def 미도달'로 FAIL(부록 A G2) |

**v5 주의(재측정 대상)**: 위 줄 번호는 `7535799`의 값이다. G1 전에 병합되는 게이트 card 셋이 이 세 파일을 바꾼다 -- 면제 묶기·범위 정책은 `mutate_changed.py`의 `main`(면제 대조 375행 근처, 대상 선택
364행 근처, 출력 407행), B33은 `reachability.py`의 `build_graph`(97행~)와 `main`의 도달 계산(223·230행 근처, R3 소스 범위). V7 '미도달 109'는 B33 뒤 줄어든다(B33 시제품: 소스 전체 기준 미도달
115 → 39 -- `draft_b33.spec.md` '작성 전 실측' 1, 판정 기록 수치 아님). 옮긴 def를 새 def로 보는 결함 자체는 B33과 무관하게 남는다(B33은 '무엇이 도달하는가', G1은 '무엇이 새 def인가'). G1 card는
이 줄 번호와 수치를 그 병합본에서 다시 잰다(G1 card '작성 전 실측' 1).

합성 저장소 red 실측(부록 A G5 `move-exact`): def 하나를 바이트 그대로 새 파일로 옮기고 원래 파일은 재수출만 남긴 커밋에서 base V3·V6·V7 모두 exit 1.

**계획 원문**(N3.10 533행): "무변경 증명 = 이동 전후 함수별 `ast.dump`(docstring 제외) 해시 동일 + import 줄만 차이. **해시가 같은 함수는 V3 대상에서 뺀다.**" -- V3 행(N4.2 839행)도 "대상 = diff가 닿은 def 중 AST 해시가 바뀐 것"이고 경로를 말하지 않는다. V6(842행)·V7(843행)은 이동을 말하지 않는다.

### 5.2 고칠 방향

* **판정식은 그대로, 비교 기준만 옮긴다**: 옮긴 단위(§3 MOVED)는 비교 기준이 '같은 경로의 base'에서 '이동 원본'으로 바뀐다.
  * V3: 옮긴 def는 대상이 아니다 -- (경로, qualname, `def_hash`)가 모두 맞을 때만 뺀다(2차 검토 B1 (3)). 옮기며 한 토큰이라도 바뀐 def, 거부된 후보(M-0·M-0h·M-1~M-4)의 def,
    qualname이 겹치는 def(B1 (2))는 지금처럼 대상. 대상이 된 def 안의 변이 선택은 범위 정책 card(N2)의 규칙 그대로이고, 새 경로에서 base 같은 경로에 같은 qualname이 없으면 '새 def'(본문 전체)다
    -- 이동 원본과 문장 단위로 맞추지 않는다(D-20, §5.5.2).
  * V6: 옮긴 def 단위의 '이전 항목 수'는 원본 단위를 원본 파일 맥락에서 센 값. 옮긴 문장은 새 파일 `<module>` 단위의 이전 항목 수에 원본 맥락 값(그 문장 줄 범위)으로 더해진다.
    **새 파일 맥락에서 항목이 늘면 FAIL**(부록 A G5 `cache-split`: 캐시 dict만 옮기고 `len()` 검사를 원래 파일에 남기면 `unbounded_cache` -- 옮긴 문장이라도 걸린다).
  * V7: 옮긴 def는 '새 def'가 아니다(V3와 같은 (경로, qualname, `def_hash`) 대조).
* **약화하지 않는다 -- 반례 재실행**(부록 A G5·G5', base 도구는 **HEAD `7535799`의 실제 도구**를 단계마다 합성 git 저장소에서 실행, v3·v4 규칙은 같은 입력에서 참조 구현 모의).
  초안 v2 규칙(M-1~M-3)이 통과시키던 1차 검토 반례 3종은 v3에서, v3 규칙(M-0~M-4)이 통과시키던 **2차 검토 반례 7종**은 v4에서 모두 거부된다. v3 규칙으로 잰 26단계 결과는 초안 v3 측정
  (`p3v3_g1_results.json` `counterexamples` 26개)과 26/26 같고(`p3v4_g1_results.json` `v3_regression`, 회귀 없음), v4 규칙은 그 26단계의 exit를 하나도 바꾸지 않는다(v6 정정: v5까지 '27'은 오기 -- 3차 검토 S6).

  | 단계 | 무엇을 막나 | 규칙 | base V3/V6/V7 | v3 규칙 | v4 규칙 |
  |---|---|---|---|---|---|
  | `overwrite` | 목적 파일의 같은 이름 정의(다른 본문)를 옮긴 본문으로 덮음 -- 호출자 동작이 바뀜(1차 B1) | M-0 | 1/1/0 | 1/1/0 | 1/1/0 |
  | `overwrite-import` | 목적 파일이 base에서 같은 이름을 다른 모듈에서 import | M-0 | 1/1/1 | 1/1/1 | 1/1/1 |
  | `swap` | 두 파일 def 교환 | M-0 | 1/1/0 | 1/1/0 | 1/1/0 |
  | `rebind` | 옮긴 def가 읽는 `helper`를 목적 파일이 다른 정의에 묶음(1차 B2) | M-4 | 1/1/1 | 1/1/1 | 1/1/1 |
  | `file-dir-change-noshim` | `__file__`을 읽는 def를 다른 디렉터리 소스 파일로 | M-4 | 1/1/1 | 1/1/1 | 1/1/1 |
  | `class-header-changed` / `class-field-changed` | 클래스 기반·필드를 바꾸며 메서드 이동(1차 B3) | 골격 해시 | 1/1/1 | 1/1/1 | 1/1/1 |
  | `copy`·`wrapper`·`ambiguous`·`two-targets`·`move-edited` | 초안 v2부터 거부 | M-2·M-2·M-1·M-3·해시 | 1/1/1 | 1/1/1 | 1/1/1 |
  | `N1` 목적 파일 조건부 재정의(원본 재수출 없음) | `if FLAG: def f(x): return -x`가 옮긴 f 뒤에서 이름을 가로챔(2차 B1) | M-0h | 1/1/1 | **0/0/0** | 1/1/1 |
  | `N2` 목적 파일 def 없는 재바인딩 | `f = (lambda g: …)(f)` | M-0h | 1/1/1 | **0/0/0** | 1/1/1 |
  | `S2` 증강 대입·`except … as` 재바인딩 | 계약 문언이 def·class·대입·`for`/`with`만이면 뚫림(2차 S2) | M-0h | 1/1/1 | 1/1/1·**0/1/0** | 1/1/1 |
  | `P` 옮긴 클래스의 property getter 변경 | 골격 같음, `P.x` 키가 setter 해시로 제외돼 getter 변경이 V3에서 빠짐(2차 B1) | qualname 중복 제외 | 1/0/1 | **0/0/0** | 1/0/1 |
  | `N3b` star import가 함께 옮긴 helper를 가림 | 명시 바인딩 뒤의 `from c import *`(2차 S1 (c)) | M-0h | 1/1/1 | **0/0/0** | 1/1/1 |
  | `N4` `global`로 쓰이는 X를 읽는 g만 이동 | base·head 모두 `unbound`라 같다고 봄(2차 S1 (a)) | M-4 | 1/1/1 | **0/0/0** | 1/1/1 |
  | `N13` 같은 import 줄, 다른 디렉터리 | `A/`의 `from wsutil import h` → `workspaces/`(2차 S1 (b)) | M-4 | 1/1/1 | **0/0/0** | 1/1/1 |
  | `N5` 목적 파일에 `from __future__ import annotations` 누락 | 주석 문자열 → 평가값(2차 S3) | M-4 | 0/0/0 | 0/0/0(인정) | 0/0/0(**거부**, 관찰) |

  인정 9단계(red → green): `move-exact`, `absorb-own-import`(목적 파일이 base에서 원본을 import하던 경우), `move-with-helper-import`(새 파일이 원본 모듈에서 helper를 import -- 출처가 같아
  G1은 인정, Phase 3에서는 원본이 N3.10 밖 split 파일이면 `move_plan check` `order`가 거부 -- v6 ORDER), `move-together`, `move-chain`(앞 card에서 옮긴 이름을 새 MOD가 그 MOD에서 import),
  `local-shadow`(지역 이름이 원본 최상위 이름과 같음 -- 유효 범위 규칙으로 전역 아님), `file-same-dir`, `class-exact`, `cache-together` -- 모두 base 1/1/1 → v3·v4 0/0/0. 추가 인정
  `N5ok`(future 줄을 가진 목적 파일)·`N6ok`(문장 순서 보존)도 v4에서 인정. **알려진 보수 비용**: `P-property-exact`(바이트 그대로 옮긴 property 클래스)는 qualname 중복 제외 때문에
  v4에서 V3/V7 1(base와 같음) -- 엔진 4파일 qualname 중복 0이라 Phase 3 노출 0.
* **2차 검토 새 반례 22건 전부 거부**(부록 A G5' `adversarial_summary`): G1이 19건(주체 def가 V3·V7 대상으로 남거나 `move_rejected`), `move_plan check` 발견만으로 3건 --
  `same-path-rebind`·`S5-inplace-rebind-in-move-card`(제자리 단위의 import 교체 → `rebind`), `N6`(옮긴 문장 순서 교환 → `stmt-order`). G1이 잡은 19건 중 N5·N7·P·N1 등은 `check`도 함께
  잡는다(`future`·`changed` def 단위·`changed`/`lost`). 2차 검토 §3 표의 N8a·N8b·N9a·N9b·N10·N11·N12는 v3에서도 거부였고 v4에서도 거부.
* **거짓 거부 측정**(부록 A G6'): 실제 엔진 4파일 각각을 같은 디렉터리 새 파일로 통째 옮기고 원래 파일은 명시 재수출만 남긴 모의에서 **v4 규칙으로** 옮긴 단위 402/402(SR 218·SD 169·TL 8·DR 7),
  옮긴 def 473/473, 거부 0(M-0h 위반 0, qualname 중복 제외 0), `move_plan check` 발견 모의 0(`changed`·`lost`·def 단위 `changed`·`stmt-order`·`future`·`rebind` 모두 0 -- 트리 전체 단위의
  `rebind` 대조 포함). `stick_diagram`의 `__file__` 사용 2곳(1050·8973행)도 같은 디렉터리라 인정. 참조 구현 한 호출 7.9~15.6초(전체 소스 두 벌 색인 -- v3 측정 5.8~9.2초와 같은 규모,
  기계 부하 차), `check` 모의 1.3~2.4초.
* **관찰 가능**: 세 도구의 판정 JSON에 `moved`(`[{"from", "to"}]`)와 `move_rejected`를 더하고, V3에는 변이 대상 def 목록 `defs`를 더한다(§10 E2가 `targets`가 아니라 이것을 잰다 -- 검토 B5).
  먼저 병합된 card가 더한 키(범위 정책 `not_targeted`·`targets_by_def`, 면제 묶기 `exempt_ignored`·`survivor_bindings`, B28 `baseline_failed`)는 이름·뜻을 그대로 둔다(§5.5).
* **기존 이름·시그니처 유지**: `mutate_changed.changed_defs(base_src, head_src)`·`def_hash(fn)`은 기존 판정 기록 스크립트 4개가 부른다(부록 A G4의 3개 + P9 판정 기록 `v3_list.py:9` -- v8.4, G1 착수 키트 `0f23786` 재측정). 해시 정의는 `reachability`로 옮기고
  `mutate_changed`는 그것을 import해 같은 이름으로 둔다(`mutate_changed`가 `reachability`를 import하므로 반대 방향이면 순환 -- 정의 하나).
* **비용 선택(UD-5)**: 이 절의 방식은 **전역 이동 인식 규칙**이다. 대안은 '승인 기록에 선언된 이동 목록(from→to)만 인정'이다. 비교와 권고는 §9.2 UD-5.

### 5.3 B28(`20260930-v3-history-clone`)과의 합성 -- B28 병합 완료

B28은 병합됐다(code `dee338d` → 병합 `2b41e79`, 판정 기록 `8790b24` -- 지금 gate `master` = `7535799`). B28은 `mutate_changed.main`의 **test 실행 환경**(copytree → `make_clone`
격리 복제본(53·323행), 기준 실행 실패 → `ERROR`(398행, `baseline_failed`), 임시 디렉터리 정리 `_rmtree_force`(406행))을 바꿨다. G1은 **대상 선택**(`changed_defs` 호출 364행 앞 이동
제외)과 판정 JSON 필드 추가만 바꾼다. 출력 키는 병합본에서도 `tool, verdict, targets, mutants, killed, survivors`(PASS/FAIL 407행, ERROR는 `tool, verdict, error` + `baseline_failed`)
-- **E2 기준은 영향 없음**(2차 검토 S8 재측정). `lib/rt.py`에 B28이 `vcase` 선택 관찰(`tool_tmpdir`·`root_state`, 599~621행)을 더했다. 합성 규칙:

1. G1의 test worktree는 **B33·면제 묶기·범위 정책이 병합된 뒤의 gate `master`**에서 만든다(05 §12 순서 1, §5.5.1). G1 spec card의 '작성 전 실측' 줄 번호는 `7535799`에서 잰 값이다 --
   그 세 card가 `tools/gates`를 바꾸므로 G1 착수 때 반드시 다시 잰다.
2. G1의 무동작 입력에 B28의 redteam `attacks/31-v3-git-history/` 세 단계를 넣는다(결과 불변).
3. G1은 B28의 계약(격리 복제본·`ERROR`·임시 디렉터리 무누수)을 건드리지 않는다. G1이 새로 여는 git 호출은 base 트리 읽기(`ls-tree`·`show`)뿐이다.
4. §10 E2는 G1이 더하는 `defs`·`moved`와 공통 키 `mutants`를 읽는다 -- 출력 키가 다시 바뀌면 E2 명령을 다시 잰다(의존 명시).
5. **redteam 번호 배정**(D-18, v5 개정): 마지막 번호 `31-v3-git-history`(B28). 오케스트레이터 배정 = **G1 `32-moved-defs`, B33 `33-…`, 면제 묶기 `34-…`, 범위 정책 `35-…`**
   (디렉터리 이름 꼬리는 각 card의 것: B33 `33-v7-registry-edges`, 면제 묶기 `34-v3-exempt-binding`, 범위 정책 `35-v3-changed-scope`). 병합 순서(33·34·35가 32보다 먼저 들어간다)와
   무관하게 번호를 미리 나눈다. v4의 `33-v7-graph-edges`는 B33 card가 정한 꼬리 `v7-registry-edges`로 바꿨다. 세 card 초안은 이미 이 번호를 적는다(v6 확인, 2026-10-01 개정판:
   `draft_b33.spec.md` 131·144·160행 `33-v7-registry-edges`, `draft_v3_exempt_binding.spec.md` 82행 `34-v3-exempt-binding`, `draft_v3_scope_policy.spec.md` 89행 `35-v3-changed-scope`,
   `redteam_numbering.md`). G1 card '작성 전 실측' 2는 `ls attacks`에 33·34·35가 있고 32가 비었는지 확인한다.

### 5.4 관찰(범위 밖, 백로그 후보)

* V7 그래프는 클래스 인스턴스화에서 `__init__`로, 모듈 최상위 레지스트리 dict에서 값 함수로 가는 간선이 없어 `SemiEmpiricalGmIdLUT.__init__`·`_feed_*` 같은 def를 미도달로 센다(부록 A G2).
  **v5: B33(`20260930-v7-registry-edges`)이 G1 전에 병합되어 닫는다**(R1 레지스트리 바인딩·R2 생성자·R3 소스 범위). G1과의 합성은 §5.5.4.
* **같은 경로 import 재바인딩**: `a.py`의 `from c import helper`를 `from d import helper`로 바꾸면 V3·V6·V7 모두 exit 0이다(부록 A G5 `same-path-rebind(observation)` -- def가 바뀌지 않았으므로).
  G1의 M-4는 **옮긴** def에 대해 이 사각을 막지만 같은 경로 변경에는 관여하지 않는다(약화도 강화도 아님). **Phase 3 이동 card 안에서는** `move_plan check`의 `rebind`(head의 모든 단위의
  전역 읽기 출처 = base 출처, 옮긴 단위 사상 적용 -- 2차 검토 S5)가 닫는다(부록 A G5' `same-path-rebind`·`S5-inplace-rebind-in-move-card` → `rebind` 발견). Phase 3 밖 card의 같은 경로
  import 교체는 여전히 게이트 사각이다(백로그 후보).
* **클래스 수준 문장**: V6 `_units`는 클래스 몸체의 리터럴을 어느 단위에도 넣지 않고 V3는 def만 보므로 dataclass 필드 기본값 변경은 세 도구 모두 보지 않는다(부록 A G5
  `record-class-default-changed` base·v3 모두 0/0/0). 이동 card에서는 `move_plan check`의 `changed`(클래스 골격 해시)가 잡는다.
* **옮긴 클래스 안 메서드 본문 변경**: 골격 해시는 메서드 몸체를 빼므로 클래스 단위는 '옮김'이다. V3는 그 메서드를 대상으로 잡지만(해시가 원본과 달라 옮긴 def가 아님) 인벤토리 test가
  변이를 죽이면 V3 PASS다 -- 그래서 M card 판정은 **card마다** V3 JSON `defs` = `[]`을 요구하고(§8 M행), `check` `changed`가 옮긴 클래스 안 def 해시까지 본다(2차 검토 S6).

### 5.5 먼저 병합되는 게이트 card와의 합성(v5)

#### 5.5.1 순서와 base

사용자 결정 A1-a·A1-b(`_drafts/user_decisions.md`, 2026-10-01)와 B33 card의 권고 순서로 G1 앞에 게이트 card 셋이 병합된다. 셋 다 `tools/gates`를 바꾸고 G1도 같은 파일을 바꾸므로 **나중에
병합하는 G1이 합성 문장을 가진다**(범위 정책 card '결정 필요 항목'이 정한 규칙 -- "나중에 병합하는 card가 문장을 고친다").

| card | 바꾸는 파일·동작 | G1과의 관계 |
|---|---|---|
| B33 `20260930-v7-registry-edges`(redteam 33) | `reachability.py` `build_graph`(R1 레지스트리 바인딩·R2 생성자 간선)와 `main`의 도달 계산(R3 소스 범위). V3 인벤토리도 같은 그래프 | 판정 효과 독립(B33 = 무엇이 도달하는가, G1 = 무엇이 새 def인가). 같은 파일 -- §5.5.4 |
| 면제 묶기 `20260930-v3-exempt-binding`(redteam 34) | `mutate_changed.py` `main`의 면제 대조(원소 `<변이 id>@<묶기 해시>`), 출력 `exempt_ignored`·`survivor_bindings`, `--out`에 exempt 기록 | 옮긴 def의 면제 -- §5.5.3 |
| 범위 정책 `20260930-v3-changed-stmt-scope`(redteam 35) | `mutate_changed.py` 대상 선택(해시가 바뀐 기존 def는 바뀐 문장·감싸는 제어문·삭제 지점·넓힌 T6·바뀐 매개변수·`early_return`, 새 def는 전체), 출력 `not_targeted`·`targets_by_def`, 데코레이터 변이 적용 | 옮긴 def 제외와 N2 -- §5.5.2 |

G1 base = 이 셋이 병합된 gate `master`. 셋 사이의 순서는 G1에 영향이 없다(면제 묶기는 A1-a대로 B26-1 전, 범위 정책은 B26-1의 V3 비용 근거라 B26-1 전, B33은 G1 전 어느 때든).

#### 5.5.2 V3 대상: 옮긴 def 제외와 N2

* **먼저 제외, 그다음 N2**: G1의 옮긴 def((경로, qualname, `def_hash`) 일치 -- §3 MOVED)는 V3 대상 def가 아니다. 변이를 만들지 않으므로 `not_targeted`에도 `targets_by_def`에도 들지 않는다
  (실행하지 않은 변이가 아니라 대상 def가 아니다). 범위 정책 계약 3의 G1 읽기("옮긴 def는 대상 아님")와 같다.
* **나머지 def**에는 범위 정책 계약 1이 그대로 적용된다: base **같은 경로**에 같은 qualname이 있고 해시가 다르면 문장 단위 대상(T1~T6, 넓힌 T6 포함), 없으면 새 def 본문 전체.
* **D-20 -- 옮기며 바뀐 def·거부된 이동 후보는 새 경로의 '새 def'(본문 전체)다.** 이동 원본과 문장 단위로 맞추지 않는다. 근거: (1) 범위 정책 승인(A1-b, 약화 승인)이 덮는 것은 '같은 경로의 해시가
  바뀐 기존 def'뿐이다 -- 원본을 경로 밖에서 찾아 문장 단위로 좁히는 것은 승인 범위 밖의 추가 약화다. (2) Phase 3에서는 옮기며 본문을 바꾸는 것 자체가 F2(card 되돌림)이고 M card는
  `defs` = `[]`을 요구하므로 좁힐 이유가 없다. (3) 거부 후보(M-0·M-0h·M-4 등)는 '이동으로 인정할 수 없다'는 판정이므로 원본과 맞추는 것은 그 판정을 무르는 것이다.
* 범위 정책 계약 2(해시가 바뀐 기존 def마다 대상 ≥ 1)는 옮긴 def에 걸리지 않는다 -- 옮긴 def는 '해시가 바뀐 기존 def'가 아니다(이동 원본과 해시가 같다).
* G1 redteam 31단계(v8.4: G1 착수 키트 v9가 `class-method-edited`(거부)·`stmt-literal-moved`(red)를 더함 -- 옛 29단계)의 V3 exit는 범위 정책 뒤에도 바뀌지 않을 것으로 본다: 합성 저장소에 test가 없어 대상 변이가 하나라도 있으면 전부 생존(exit 1)이고, 대상이 0인 경우는 '옮긴 def만 있음'뿐이다
  (새 def는 본문 전체, 해시가 바뀐 기존 def는 `early_return` 항상). G1 card '작성 전 실측'에서 병합본 도구로 base 열을 다시 잰다.

#### 5.5.3 면제 묶기와 옮긴 def

* 변이 id = `<모듈>:<qualname>:<연산자>:<경로>`이고 `<모듈>` = 파일 줄기(`reachability.module_name` 47행, `mutate_changed.py` 362·374행 -- 부록 A E2). 그래서 **def를 옮기면 그 def 변이 id의 모듈
  부분이 바뀐다**. 묶기 해시(docstring 포함 def 원본)는 바이트 그대로 옮기면 같다.
* 옮긴 def(G1 인정): V3 대상이 아니어서 변이 id가 만들어지지 않는다 → 면제 대조 자체가 없다. 옛 경로 id의 원소는 '이번 실행의 변이 id'와 같지 않아 `exempt_ignored`에도 실리지 않는다(면제 묶기 계약 3).
* 거부된 이동 후보(본문은 같지만 M-0h·M-4 등으로 대상): 새 모듈 이름의 id로 변이된다. 옛 모듈 이름 id의 원소는 **적용되지 않는다**(fail-closed, 누수 아님). 면제가 필요하면 `<새 모듈>:…@<묶기 해시>`로
  다시 승인한다(묶기 해시는 바이트가 같으면 옛 승인 값과 같다). Phase 3에서는 거부 후보가 곧 F7(배정을 고치거나 import 줄만 고친다)이라 면제로 넘기는 경로가 아니다.
* 이동 뒤 card가 옮긴 def를 바꾸면 묶기 해시가 바뀌어 어떤 옛 원소도 맞지 않는다 -- 모듈 부분과 무관하게 면제 묶기 card 계약 2의 동작.
* 결론: G1은 면제 대조를 바꾸지 않는다(**D-21**). 이동 때문에 면제가 다른 문장으로 새는 경로는 없다(id가 바뀌면 적용 안 됨, 해시가 바뀌면 적용 안 됨). 지금 HEAD의 V3 모양 원소 14개
  (`20260922-ic3-v3-exempt`: `load_topology` 10·`save_instance_json` 4)는 해시가 없어 면제 묶기 병합 뒤 이미 적용되지 않는다.

#### 5.5.4 B33(V7 그래프)과 G1

* G1의 V7 변경은 `new_defs`에서 옮긴 def를 빼는 것뿐이고 `build_graph`·도달 계산을 바꾸지 않는다 -- B33의 R1~R3와 그 card의 그래프 계약(계약 9 간선 관계 -- 검토 `review_b33.md` B1·S5대로 dunder 속성 폴백 제거(R2')에 맞춰 이미 개정됨, 정본은 B33 card)이 G1 뒤에도 그대로다. G1 card의 무동작 입력에
  B33 redteam `33-v7-registry-edges` 전 단계를 넣는다.
* B33 바인딩 노드(`<파일>::=<이름>`)는 def가 아니다(B33 계약 7) -- G1 `moved_defs`의 `defs`·V7 `new_defs` 제외 대상에 나오지 않는다. 옮긴 **문장** 단위(레지스트리 dict 대입)는 새 파일의 바인딩
  노드가 되고, 소비자가 shim(`from <MOD> import _REG`)을 거쳐 읽어도 B33 R1의 재수출 해석이 값 함수로 잇는다(B33 단계 `registry-reexport`. B33 초안의 최종 문언(34행 (iv))이 "M에 그 이름의 바인딩이 없으면 **M 파일의 `from X import NAME`을 따라 X의 바인딩**(재수출, 순환은 방문 집합)"이다 -- 검토 `review_b33.md` S3·B2가 권한 chase 판으로 이미 고쳐졌고, Phase 3 중간 상태에서 옛·새 모듈에 같은 이름이 잠시 공존하는 모양이 그 반례였다. dunder 속성 폴백 제거(R2')와 계약 9 개정도 B33 초안에 반영됐다 -- v6 사실 갱신).
  그래서 Phase 3 중간 상태에서 레지스트리 값 함수가 미도달로 바뀌지 않는다 -- 옮긴 def는 어차피 V7 대상이 아니고, 이 성질은 이동과 같은 card에서 생긴 **새** def(예: M10 진입점)의 도달 판정에 쓰인다.
* B33 R3(도달은 `_is_source` 노드 안에서만)와 G1 `moved_defs` 입력(소스 파일만, `_is_source`)은 같은 소스 분류를 쓴다 -- 새 MOD 파일(`A/*.py`)은 둘 모두에서 소스다.
* B33은 V3 인벤토리를 키운다(사전 실측 (소스 def, 도달 test) 쌍 33,991 → **44,493** -- B33 초안 58·257행 개정값, 79,809는 초안 v1 규칙 값). G1은 인벤토리를 바꾸지 않는다. M card의 V3는 `defs` = `[]`이라 인벤토리 비용이 없다.
* §4 F5·§5.1의 'V7 미도달 약 108'은 B33 뒤 값으로 G1 card에서 다시 잰다(시제품 추정 약 39).

---

## 6. 이관표 생성 규칙 (N9.1 '레지스트리 목적지 열에서 생성')

### 6.1 왜 열을 그대로 읽을 수 없는가(실측, cd64170)

* 레지스트리 함수 행 379개의 목적지 셀 분류: `gmid_sizing_engine` 114, `stick_diagram` 87, `circuit_state_graph` 61, `topology_authoring` 32, `sizing_layout_convergence` 14, `instance_report_builder` 7, `gmid_design_pipeline` 2, **MOD 이름이 없는 셀 62**(`optimizer`, `〃`, `삭제 후보`, `test util`, `LUT 생성 도구 유지` 등). **MOD1 `gmid_lut`·MOD5 `circuit_metrics`·MOD6 `theta_search`로 가는 행 0**(부록 A M9).
* 레지스트리 머리: "작성 2026-09-14, 기준 커밋 78b58c6. 계획서 §13(v4.44)의 부속 문서" -- 목적지 열은 10모듈 표 이전 판의 이름을 쓴다.
* N3.10 표 '대표 대상'과 열이 다른 행: `GmIdLUT`·`SemiEmpiricalGmIdLUT`·`_multilinear_interp`(표 MOD1, 열 `gmid_sizing_engine`), `load_topology`(표 MOD2), `compute_metric`·`build_ac_network`·`_full_circuit_response`·`estimate_mismatch_sigma`(표 MOD5), `search_stage_budget_L_warm_start`·`presolve_warm_start`·`_optimize_theta_slsqp`·`repair_infeasible_baseline`(표 MOD6, 열 `optimizer`) 등(부록 A M10).
* 둘 이상 모듈로 **쪼개라**고 적은 셀 16행(부록 A M11). 이동 전용 규칙으로는 함수를 쪼갤 수 없다.
* 레지스트리에 행이 없는 최상위 정의: `sizing_recipe` 3, `stick_diagram` 24(DF-36의 `_topology_ref_relpath` 포함). 초안 배정 뒤 미배정 최상위 이름 34(대입 포함)(부록 A M12·M13).
* 초안 배정으로 **큰 번호로 향하는 참조 64개**(MOD2→MOD3 17, MOD3→MOD4 14, MOD3→MOD7 9, MOD4→MOD5 8, MOD2→MOD7 6, …, 가장 많은 원천 `_hr_resolve_vertical_group` 9)(부록 A M14). 이 계수는 `ast.Name` 참조만 센 것이다 -- PLAN-LAYER 정식 계수는 D0a 도구가 낸다.
* 참조를 최상위 몸체에서만 세면 모자란다: 중첩 def·메서드 안에서만 다른 최상위 이름을 참조하는 최상위 단위가 SR 17·SD 4(예 `SemiEmpiricalGmIdLUT` → `_multilinear_interp`)(부록 A S6). 그래서 R(u)는 G1 `global_names`(모든 하위 유효 범위)로 센다.

### 6.2 규칙(우선순위 높은 것이 이긴다. 도구가 단위마다 근거 규칙 ID를 남긴다. 정확한 문언은 D0a spec card 계약 2·3)

* **A-0 현재 위치**: N3.10 표 파일 중 그 트리에 있고 분할 대상(`--split`)이 **아닌** 파일의 단위는 그 파일. 이동 뒤에도 `plan`이 같은 배정을 내게 하는 규칙이다(Phase 중 D0b 계약 test·
  REG-DEST·E4 -- 검토 B4). 분할 대상 파일이 없는 트리(F2 뒤)는 오류가 아니라 `absent_split`으로 보고한다.
* **A-1 계획 명시**: N3.10 표 '대표 대상' 열의 백틱 토큰 -- 식별자(글롭 `*` 허용)는 그 이름, `<파일>.py`는 그 파일 전체, `<모듈>.<이름>`은 이름, 그 밖(`∂ID/∂VSB`, `workspaces/`)과 산문은 무시
  (부록 A S5: 식별자 41·파일 1·점 이름 1·무시 2, MOD7은 산문뿐). 열은 `role_paths.read_section_table`로 읽는다(`mod_table`은 ID·파일 열만 -- 게이트 코드 무변경). 계획 532행(`canonical_spec`/`SPECS`는 하네스에 남음) 포함.
* **A-2 레코드 클래스 하강**: 레코드 = `@dataclass`(이름·속성·호출), 내장 예외 또는 다른 레코드를 기반으로 하는 클래스, 메서드 없는 클래스. 그것을 참조하는 단위(문자열 주석 포함, 레코드 자신 제외)
  중 **가장 낮은 번호**로. 엔진 클래스 41 중 dataclass 36, 예외 3, 메서드 없는 클래스 36(부록 A G6 `classes`).
* **A-3 계층 강제**: 목적지 셀이 MOD를 둘 이상 적은 16행은 쪼개지 않고 max(셀의 가장 작은 MOD, 피참조의 최대 MOD)로 통째(쪼개기는 그 셀이 적은 담당 Phase). A-1과 충돌하면 N3.10 표를
  고친다(D-11). 계산으로 드러난 충돌: `load_topology`(표 MOD2)가 구조 자동채움을 부른다(부록 A M15) → MOD3. `validate_theta_declaration_order`(표 MOD2)가 `_build_shared_current_joint_plan`·
  `_shared_current_groups_from_compensation`을 부른다 → 그 둘의 MOD 이상 = **MOD3**(v6 확정: 두 함수의 레지스트리 목적지 셀이 `circuit_state_graph S1`·`circuit_state_graph S1 / 유도
  DAG`라 A-4로 MOD3 -- 레지스트리 129·131행; 모의 `p3v6_order_shim_sim` 근사 배정에서도 그 둘이 이 함수의 MOD 2 초과 참조의 전부). `optimize_full_circuit_budget`(표 MOD6 '탐색부')는 `stick_diagram` 레이아웃 함수 8개와
  `run_topology_pipeline_with_finger_fixup`(MOD8)을 부른다 → Phase 3 위치 MOD8(D-3), 탐색부 추출 뒤 MOD6(CC-7, `00-common` 435행과 일치).
  이 세 건과 D-19가 UD-0이 덮는 N3.10 개정 문안이다(`_drafts/p3_doc_amendments.md` §1).
  **A-1 충돌(v8.4 -- D0b 착수 키트 실측, 부록 A F4v84, G1·D0a 시제품 관찰)**: 위 세 건을 적용한 트리에서도 `plan`은 `upward` 34·`cycles` 1을 냈고, 아래 v8.4 규칙(docstring 제외·A-K·승격·A-6·A-7)을 더하면
  `upward` 7로 줄지만 남는 7건은 **모두 원천이 A-1 토큰**이라 규칙으로 풀 수 없다(N3.10 표 안의 모순 2건 `sizing_recipe.py:8060` `_build_theta_evaluator`(MOD6) → `resolve_stack_layout`(MOD8)·`:7683`
  `require_declared_spec_source`(MOD2) → `spec_fingerprint`(MOD3), 토큰 → 레지스트리 칸 3건 `:5272`·`:399`·`_METRICS_REGISTRY` → `_metric_nulling_resistor_ohm`, 승격이 끌어올린 2건 `apply_theta_feed` →
  feed 레지스트리·`load_topology` → `propose_device_roles_gap_fill`). 지금 계산되므로 UD-0 개정 문안에 넣었다(§1 (a)~(d) 갱신 + §9 -- 보정 8건·토큰 11개: MOD6의 `_build_theta_evaluator`·`search_stage_budget_L_warm_start`·
  `presolve_warm_start`·`_optimize_theta_slsqp` → MOD8(Phase 3 위치 -- D-3과 같은 모양, 넷을 함께 옮겨야 닫힌다: 하나 `upward` 4·셋 1·넷 0), `require_declared_spec_source` MOD2 → MOD3, `apply_theta_feed` MOD4 → MOD5,
  `metric_unit_scale` → MOD2, `_multilinear_interp_point_multi` → MOD1, `_metric_nulling_resistor_ohm` → MOD4, `find_hub_merge_candidates`·`signal_path_nodes` → MOD3). 원칙: 부르는 쪽이 올라간다(A-3·D-3),
  트리 안 참조가 없는 도우미는 부르는 쪽 MOD 책임에 맞으면 내려간다. 결과(개정 + v8.4 규칙): `upward` 0·`cycles` 0·`unassigned` 0·`conflicts` 0·`import_time_high` []·MOD7 파일 밖 MOD7 배정 0,
  열 재생성 뒤 `reg_mismatch` 0·멱등. 수치는 시제품 관찰이다 -- D0b가 자기 base(B34·B26-1 등 병합 뒤)에서 다시 계산하고, D0b가 B26-1·B34 병합본에서 **이 밖의** 충돌(`conflicts`·`upward`를 규칙으로 못 푼 것)을
  계산하면 그 N3.10 표 diff는 **따로** 사용자 승인(`target_kind: diff`)을 받는다(D-11, 3차 검토 B4 (가)) -- UD-0은 그 결과를 미리 위임받지 않는다.
  A-1이 '대표 대상'의 **백틱 식별자**를 그 행 MOD로 보내므로 개정은 토큰을 옮긴다 -- 특히 지금 MOD6 행의 `` `optimize_full_circuit_budget` 탐색부 ``는 A-1로 함수 전체를 MOD6에 보낸다
  (v6 모의 근사 배정에서도 A-1 MOD6) → MOD6 행에서 백틱을 빼고 MOD8 행에 넣는다. 설명 문장의 함수 이름은 백틱 없이 쓴다(두 행에 걸리면 `conflicts`). 사본 적용 실측: 두 행 이상에 걸린 토큰 0,
  표 파싱·`import_layering` 정상(`p3_scripts/p3v6_amend_check.json`).
* **A-4 레지스트리 열**: 셀의 식별자 토큰 중 MOD 파일 줄기와 별칭 키를 MOD로 바꾼 것이 하나면 그 MOD **에서 승격**(v8.4, D-31: max(칸 MOD, 부르는 단위들의 배정 MOD 최댓값) -- A-3과 같은 식. v8.5 확정(8차 검토 m4): 최댓값은 N3.10 MOD 번호만 센다 -- `--keep` 도구 번호는 넣지 않고 그 참조는 `upward`로 남는다; A-6은 결과 자체가 R(u) 최댓값이라 승격·상한이 공허 -- D0a 계약 2). 옛 이름: `optimizer` → MOD6(책임 '실패 캐시, 시작점, 전역 샘플, S3', 526행), `〃` → 위 행.
  (v8.4 정정 -- D0b 착수 키트 실측: 초안 v2의 "`_metric_*`·metric 레지스트리 → MOD5"를 뺀 뒤 적은 "`_metric_*` 함수는 그 레지스트리가 참조자라 A-5로 MOD5에 간다"는 틀렸다 -- `_metric_*` 26개는 모두 레지스트리 칸이 있어
  A-4다(MOD4 24·MOD3 1·MOD9 1). 그중 MOD5 함수(`compute_metric`·`build_ac_network`·`_full_circuit_response`·`estimate_mismatch_sigma`)를 부르는 것은 승격으로 MOD5가 되고, MOD9로 읽힌 칸 하나(`_metric_nulling_resistor_ohm`)는
  N3.10 토큰으로 MOD4에 둔다(§9 (f)).)
  **승격 상한**: 승격 결과가 MOD7(N3.10 책임 "레이아웃만(구조 유도 함수는 MOD2·MOD3로 나간다)" -- 표에서 유일하게 배타적인 책임 문장)이고 칸 MOD가 MOD7이 아니면 올리지 않는다 -- 그 참조는 `upward`로 남아
  N3.10 개정(D-11)을 부른다. 상한이 없으면 구조 제안 함수 3개(`propose_device_roles_gap_fill`·`check_symmetry_dispositions`·`SymmetryDispositionsVerdict`, 레지스트리 칸 `topology_authoring`)가
  레지스트리 칸 MOD7인 `find_hub_merge_candidates`를 부른다는 이유로 MOD7로 올라간다(D0b 검토 S2 재측정) -- 이 design은 그 피참조를 N3.10 토큰으로 MOD3에 두어 닫는다(§9 개정 뒤 상한 있음/없음 결과 같음).
  **승격과 '열이 정본'(계획 517행)**: 승격은 MOD 하나짜리 칸을 '그 MOD 이상'(하한)으로 읽는다 -- 517행 같은 줄의 "import는 번호가 작은 모듈 쪽으로만"과 칸이 충돌하는 단위(시제품 관찰: 승격으로 칸과 달라지는 단위 32,
  MOD2 → MOD3 12·MOD4 → MOD5 11·MOD6 → MOD8 4 등)에서 계층 규칙을 앞세운다. D0b가 열을 도구 출력으로 다시 쓰므로(`reg_mismatch` 0) 그 뒤 열은 다시 이관표와 같다. 이 의미 변경은 승인 질문 UD-0 본문에 사실로 적는다.
* **A-K `--keep` 파일 잔여(v8.4)**: `--keep` 파일 단위 중 A-1~A-4로 정해지지 않은 것은 그 파일에 남는다(D-8의 규칙화 -- 없으면 `render_report`·`sys.path.insert` 문장이 `unassigned`). A-5보다 먼저.
* **A-5 소비자 따라**: 행이 없는 정의와 최상위 문장은 **그것을 참조하는 단위 중 가장 낮은 MOD**로(상수·레지스트리 dict는 소비자를, 레지스트리 값 함수는 레지스트리를 따른다), v8.4: 그리고 승격. 참조자가 없으면 A-6.
* **A-6 참조 따라(v8.4)**: 참조자가 없는 단위는 부르는 단위들의 배정 MOD 최댓값(계층상 둘 수 있는 가장 낮은 자리 -- §7 D 목록 `보류(Phase 4)`·예시 함수 8개, 시제품 관찰).
* **A-7 고립 단위(v8.4)**: 그래도 정해지지 않고(트리 안 참조·참조자 없음, 서로만 참조 포함) N3.10 파일(지금 `stick_diagram.py`)에 있으면 그 MOD에 남는다(`MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity`·
  `SharedFingerWCandidate`). N3.10 밖 split 파일이면 `unassigned`로 **도구가 FAIL**한다(조용한 기본값 금지) -- N3.10 개정으로 닫는다(`signal_path_nodes` → MOD3, §1 (b)).
* **모듈 docstring(v8.4)**: 배정 대상이 아니다(제자리 -- SHIM (b)가 docstring을 허용한다). 넣으면 참조·참조자가 없어 `unassigned`이고 SD·ACF는 F2 뒤에도 남아 D0b test·E4가 영원히 FAIL한다(D0b 키트 관찰 4개).
* **고정점(v8.4)**: A-3·A-4 단위를 칸 MOD에 먼저 앉히고 반복은 배정을 올리기만 한다(단조 -- 앉히지 않으면 A-5 단위가 아직 배정되지 않은 낮은 참조자를 못 보고 높게 잡혀 그것을 읽는 A-4 단위를 끌어올렸다:
  `_DEFAULT_METRIC_STAGE_BUDGET_GM_ID` → `_feed_metric_stage_budget` MOD4 → MOD6, 반복 순서에 따라 결과가 갈림). 규칙 ID 집합 = {A-0, A-1, A-2, A-3, A-4, A-K, A-5, A-6, A-7}(정본 D0a 계약 2).
* **결과 조건**: 규칙 적용 뒤 PLAN-LAYER exit 0(`upward`·`cycles`·`unassigned`·`conflicts`·`import_time_high`·`import_conflicts` 모두 빈 목록)이어야 레지스트리 열을 갱신한다(D0b). 갱신 뒤 `plan`의 `reg_mismatch` 0 = REG-DEST.

### 6.3 도구 `tools/migrate/move_plan.py`(D0a)

CLI·출력·exit의 **정본은 D0a spec card 계약 1~4**이고 이 절은 요약이다(검토 B6 -- 두 문서가 따로 적지 않는다).

| 명령 | 요지 |
|---|---|
| `plan --root R [--rev C] --plan P --registry G --split F… [--keep F…] [--aliases JSON]` | 단위 → MOD 배정(근거 규칙), `upward`·`cycles`(PLAN-LAYER), `unassigned`, `conflicts`, `reexports`, `order`, `absent_split`, `reg_mismatch`(REG-DEST), `import_time_high`(v7), **`mod_imports`(MOD 파일 import 머리 -- 이름마다 import 한 번)·`import_conflicts`(같은 이름의 출처 갈림·`__future__` 기능 집합 갈림)**(v8.4, D-30). 경로 인자는 `--rev` 커밋에서 읽는다 |
| `check --root R --base B --head H --card <MOD 파일>\|ALL --plan P --registry G --split F… [--keep F…] [--aliases JSON] [--allow-changed ID…]` | `move-set`·`move-rejected`·`changed`·`lost`(MOVE-AST), `rebind`·`future`·`stmt-order`, **`import-dup`(MOD 파일이 이름 하나를 import 둘 이상으로 묶음, v8.4)**, `order`(ORDER), `shim`(SHIM), `cache`(CACHE-ID). 배정은 base 커밋에서 계산 |

게이트 모듈은 `--root`의 `tools/gates`에서 import한다 -- 다른 커밋에서 꺼낸 사본으로 실행할 수 있다(§8 M card, §10).

실제 저장소 인자(§10과 M card가 쓴다). **bash 배열**로 두고 `"${MP_ARGS[@]}"`로 넘긴다 -- 문자열 변수 `$MP_ARGS` 전개는 따옴표를 다시 해석하지 않아 `--aliases`의 JSON이 공백에서
쪼개지고 D0a 계약 1대로 exit 2가 된다(2차 검토 B2: `printf '[%s]\n' $MP_ARGS` → `['{"optimizer":]`, `["theta_search.py"}']`). `--aliases`의 CLI 모양(JSON)은 D0a 정본 그대로 둔다.

```bash
MP_ARGS=(--plan docs/01-plan/features/gain-budget-gmid-sizing.plan.md
         --registry docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
         --split sizing_recipe.py stick_diagram.py topology_library.py design_report.py audit_current_forced.py
         --keep audit_current_forced.py
         --aliases '{"optimizer": "theta_search.py"}')
printf '[%s]\n' "${MP_ARGS[@]}" | tail -1   # 확인: [{"optimizer": "theta_search.py"}] 한 줄
```

### 6.4 B26-1·B34(A2 -- Phase 3 전 병합)가 바꾸는 단위와 배정(v5)

사용자 결정 A2(승인 기록 `20260930-b26-before-phase3`, decision): B26-1(`20260930-b26-rail-accessor-set`)과 B34(`20260930-b34-grammar-explicit`)는 **Phase 3 M card보다 먼저** 병합되는
앞당긴 card다. **v7 정정(오케스트레이터 확정 순서, 사용자 지시)**: 둘은 **Phase 2 DoD 뒤**에 병합한다 -- P10b → Phase 2 DoD → 면제 묶기(34) → 범위 정책(35) → B34 → B26-1(앞선 test 보강 card
`20260930-b26-pre-test-strengthen` 포함) → B33(33) → Phase 3. v6의 "Phase 2 진행 중(순서 P9 → B34 → B26-1)에 병합"은 틀렸다. 둘은 design 20 §8 범위 밖(A2로 앞당긴 Phase 4 몫, 계획
1001행)이라 Phase 2 DoD의 N6.3 판정 기록 목록에 들지 않는다(v8.3: 네 card(B34·b26pre·backfill·B26-1) 초안은 `phase: 3`이고, 승인 기록 A2 ③의 "Phase 2 진행 중에 병합" 문구는 decision 기록 `20261001-b26-phase3-cards`(사용자 답 2026-10-01)가 'Phase 2 DoD 뒤·Phase 3 M card 전(card `phase: 3`)'으로 바로잡았다 -- 그래서 네 card는 **Phase 3 DoD**의 N6.3 목록에 든다, §9.1·§11-11). 그 기록의 '재검토' 절: 둘 중 병합되지 않은 card가 있는 채 M card가
`stick_diagram`·`sizing_recipe`를 나누기 시작하면 그 card의 앞당김은 효력을 잃고 편집 범위를 새 모듈 기준으로 다시 잰다 -- 그래서 §9.1 착수 조건에 'M1 전 두 card 병합'을 둔다.

두 card 초안(`_drafts/draft_b26_1.spec.md`, `draft_b34.spec.md`)에서 **추정한** Phase 3 영향(병합 전이라 잴 수 없다 -- 전부 'Phase 3 시작 때 재측정', D0b가 실제 값으로 확정):

| 항목 | v4 값(`7535799`) | B26-1·B34 뒤 추정 | 근거(초안) |
|---|---|---|---|
| SD 최상위 정의 | Class 28·Func 132 | Class 29·Func 133(`RailDeclaration` frozen dataclass, `rail_declaration`) | B26-1 '신규 시그니처'. 지우는 def 0(B26-1 '작성 전 실측' 마지막, B34 범위 2·3) |
| 엔진 단위·def(G6' 통째 이동 모의) | 단위 402(SD 169)·def 473(SD 181) | 단위 404(SD 171)·def 474(SD 182) | 위 두 정의. `RailDeclaration`은 메서드 없는 dataclass(def 0) |
| 엔진 클래스(A-2 입력) | 41(dataclass 36·메서드 없음 36·예외 3) | 42(dataclass 37·메서드 없음 37·예외 3) | 같음 |
| 레지스트리에 행이 없는 최상위 정의(M12) | SD 24 | SD 26 | B26-1 계약 11은 §2(개념 정본)·§6 문장만 고친다 -- 함수 행 추가 없음 |
| 바뀌는 def | -- | B34: `_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`. B26-1: 판정·통과 사이트 SD 18·SR 2(`true_current_mirror_groups`·`resolve_stack_layout`)에 키워드 전용 `rails: RailDeclaration`, `load_topology`·`l_sharing_classes`·`_metric_kcl_residual` 등 본문, `propose_device_roles_gap_fill`의 `refined is None` 분기 반환에서 `unavailable_reason` 키 삭제(B40 -- v8.3, 사용자 답 U4·승인 `20260930-b26-b40-reason-key`; 새 def·이동 단위 변화 없음), 동작 불변 정리 C1·C2(`_propose_L_roles` 중복 None 가드, `open_terminals[0]` -- U3; 최상위 정의 수 불변) | B34 사이트 표, B26-1 계약 4·5·6·13·15 |
| SD 줄 이동 | `__file__` 1050·8973, future 32행 | B34 코드만으로 1073 이후 4줄 당김(B26-1 초안 '순서' 절) + B34 docstring 수정분 + B26-1 접근자·클래스 추가분. 1050(`_import_analog_grammar` 안 `_ag_path`)은 B34가 그 def를 바꾸므로 근처에서 다시 잰다 | B26-1 의도 '순서' |
| SR 캐시 줄 | 2391·2530·7697 | B26-1이 SR 2191~2230·4200대·6470대·8000대 본문을 바꿔 몇 줄 밀릴 수 있다 | B26-1 계약 4·6 |
| `run_harness.py:422·427·446`, `topology_library.py:248` | -- | 바뀌지 않을 것으로 봄(두 card 모두 편집 목록에 없음) -- 확인만 | 두 card '바꾸는 것' 표 |
| 계약 test(§7.1) | contracts 3개가 엔진 모듈 import(M22) | `tests/contracts/test_b34_grammar_explicit.py`(B군 -- `stick_diagram.<이름>(…)` 직접 호출), `tests/contracts/test_b26_rail_accessor.py`(**A군 후보** -- 계수 래퍼가 `stick_diagram.rail_declaration` 모듈 속성을 바꿈, B군 -- `sizing_recipe._metric_kcl_residual` 이름 호출) | §7.1 v5 행, T0 계약 10 |

**B26-1 등가 면제와 M card 이동(v8.3 -- 사용자 답 U3, 기록 `20261001-b26-v3-equiv-range`)**: B26-1은 `find_differential_pair_candidates`의 `range(i + 1, …)` const− 변이 1개를 '변이 id@def 원본 해시'로 면제한다. 변이 id는 `<모듈>:<qualname>:<연산자>:<AST 경로>`라(`draft_v3_exempt_binding.spec.md` 14행) 모듈 접두 `stick_diagram:`을 지니고, 묶기 규칙상 def 해시가 바뀌면 자동 무효다. M card가 그 def를 다른 MOD로 옮기면 id가 더는 맞지 않는다 -- **그래도 옮길 것이 없다**: (1) 면제는 B26-1 card 자신의 V3 판정(그 card의 base→head, def는 아직 `stick_diagram`)에서 쓰이고 끝난다 -- B26-1은 확정 순서상 M1 전에 병합된다(§8.1) (2) M card에서 그 def는 G1 이동 인식으로 '옮긴 정의'라 변이 대상이 아니다(E2 ① `mutants` = 0, `defs` = `[]`) (3) DoD E2가 V3를 다시 도는 것은 M1~M6·M8·M9 판정 기록뿐이고(§10 `$S/cards.txt`), 네 card의 판정 기록은 Phase 3 DoD 목록에 들어도 다시 판정하지 않는다(§9.1). 그 def를 **바꾸는** 뒤 card(Phase 4 이후)는 V3 대상이 되고 def 해시가 달라져 면제가 어차피 무효이므로, 모듈과 상관없이 새 면제 승인이 필요하다. M card 안에서 그 def에 V3를 재는 card가 생기면(이동 인식 밖 -- E2 ①이 FAIL) 그것은 이동이 아니라 변경이라 재승인 대상이다.

**배정(D-19 -- 사용자에게 따로 묻는다, v6)**: `rail_declaration`은 topology 선언 `supply_nets`의 형식을 검사하고 `ValueError`로 거부하는 접근자다.
* **규칙만 적용하면**: 행이 없는 정의라 A-5(소비자 따라)로 **MOD3**(유일한 운영 호출자 `load_topology`가 A-3로 MOD3 -- B26-1 계약 3·4: SR은 `meta["rails"]`로만 받고 접근자를 부르지 않는다).
  계획 표 개정이 필요 없다.
* **(가) 기본안 -- MOD2**: N3.10 MOD2 '대표 대상'에 `rail_declaration`을 더해 A-1로 MOD2. 근거는 하나로 좁힌다(3차 검토 S4): MOD2 책임 "스키마·단위·참조·선언 순서 **게이트**" -- 선언 형식을
  검사해 거부하는 함수(`validate_metric_units`·`validate_no_legacy_vs_key`·`require_declared_spec_source`)와 같은 성격이고, 다음 card B37a(미승인)의 같은 성격 접근자(`port_declaration`)도 같은 곳에
  둘 예정이다(v8 -- 5차 검토 m5). 계층: `load_topology`(MOD3) → `rail_declaration`(MOD2)은 작은 번호 쪽이라 허용. **한계(중립 기록)**: 같은 MOD2 '게이트' 행의 `validate_theta_declaration_order`는 규칙(A-3)으로
  MOD3에 가므로(§6.2) 선언 게이트가 어느 쪽이든 MOD2·MOD3에 나뉜다. 그리고 MOD2 책임의 '로딩' 대표인 `load_topology`도 MOD3로 간다 -- '로딩 옆'은 근거가 아니다.
* **(나) 규칙대로 -- MOD3**: 유일한 호출자 `load_topology` 옆. 계획 표 개정이 없다. MOD2의 선언 게이트 셋과는 떨어진다.
* 두 경우 모두 같은 것: `RailDeclaration`은 A-2(레코드 하강)로 참조 단위 중 가장 낮은 번호 = **MOD2**(`rails: RailDeclaration` 주석을 단 MOD2 구조 제안 함수 -- `refine_differential_and_mirror_relations`·
  `propose_device_roles_gap_fill` 등, 레지스트리 목적지 `topology_authoring`). (v5의 "MOD2 주석이 MOD3를 가리키는 위쪽 참조가 생기지 않는다"는 `RailDeclaration`의 배정 이유이고 D-19와 무관 -- 3차 검토 S4로 근거에서 뺐다.)
  T0 계약 10(B26-1 계수 test)은 두 경우 모두 M3(`load_topology` 이동)에서 필요하다.
* **B37a 접근자(`port_declaration`·`PortDeclaration`)**: B37a는 Phase 3 뒤 card라 이 design의 이관표 단위가 아니다. B37a 초안이 적은 위치("`rail_declaration` 옆", "접근자는 `ports`를 읽는 MOD2 쪽")는
  D-19 (가)면 MOD2(`topology_authoring.py`), (나)면 "`rail_declaration` 옆"이 MOD3가 되어 초안의 두 문장이 갈린다 -- B37a card 커밋 때 오케스트레이터가 D-19 결정대로 모듈 이름을 적는다.
* `_import_analog_grammar`(B34가 바꾸는 def): 레지스트리 행이 있으면 A-4, 없으면 A-5로 가장 낮은 소비자(구조 제안·유도 함수 -- MOD2 또는 MOD3)로 간다. `__file__`을 읽지만 MOD 파일이 `A/` 평면이라
  `file-dir` 출처가 같아 G1 M-4가 인정한다(§5.2 `file-same-dir`). B34 계약 3의 탐색 경로 `os.path.dirname(stick_diagram.__file__)`도 `stick_diagram.py`가 MOD7로 남고 같은 디렉터리라 그대로 성립한다.
  B34 범위 1 "지연 import 유지 -- 레이아웃 전용 모듈이 analog-grammar 없이 import"는 이동이 바이트 그대로라 보존된다(E-LIB와 별도로 M card가 확인할 필요 없음 -- 모듈 최상위 문장이 바뀌지 않는다).
  B34 초안 212행은 "M2(어댑터와 소비 함수를 MOD2로 이동)"라고 단정한다 -- 실제 목적지(MOD2 또는 MOD3)와 card는 D0b 이관표가 정한다는 문장을 B34 쪽 인계에 남긴다(3차 검토 m6, 이 design은 B34 초안을 고치지 않는다).

**D0b 재측정 조건**(v7 -- 확정 순서 기준): D0b의 이관표·`reg_mismatch`·PLAN-LAYER 수치는 **D0b 자신의 base**에서 처음 계산한다 -- 그 base는 B34·B26-1(test 보강 card 포함)·B33·G1·D0a가
모두 병합된 master다(§8.1). 그 전에 D0a 합성 test 밖에서 실제 저장소로 돌린 `plan` 출력(D0a 계약 8 (a) 포함)은 참고 관찰일 뿐 이관표가 아니다. D0b 착수 때 위 표의 추정 행을 전부 실측으로 바꾸고,
다르면 이 절을 사실 문장 갱신으로 고친다(규칙은 줄 번호·개수에 기대지 않는다). D0b 병합 뒤에는 F2까지 엔진 파일·`tools/gates/**`·`tools/migrate/**`·레지스트리 목적지 열을 바꾸는 Phase 3 밖 card를 병합하지 않는다(D-27, §9.1) --
그런 card가 병합되면 D0b 이관표·레지스트리 열이 낡으므로 D0b를 다시 계산한다.

**B35 인계 사이트와의 관계(v7, 4차 검토 S4)**: B34·B26-1이 백로그 B35로 넘긴 사이트 5~8·10·14(B34 final 사이트 표 -- 5 `suggest_vertical_stack_composites`, 6 `find_verified_differential_and_mirror_relations`,
7 `_propose_vertical_stack_ids`, 8 `_propose_headroom_roles`, 10 `refine_differential_and_mirror_relations`, 14 `propose_device_roles_gap_fill`)는 모두 SD 단위이고 레지스트리 목적지가
`topology_authoring`(MOD2)이다(`a796468` 레지스트리 430~438행 -- 실제 MOD는 D0b가 정한다, MOD2 또는 MOD3). B35는 위 확정 순서에 없으므로 **F2 뒤**에 착수하고, 그 사이트를 Phase 3 뒤의
새 모듈(MOD2·MOD3)에서 바꾼다. B35 card 작성 때 오케스트레이터가 사이트의 파일 이름을 D0b 이관표대로 옮긴다(B34 final 249행 인계 목록).

### 6.5 `__future__` 혼합 단위와 준비 card FU(v8.4 -- D-29, G1 착수 키트 0.2)

**사실(`5f643a9` = `0f23786` 엔진)**: split 파일 중 `sizing_recipe.py`(35행)·`stick_diagram.py`(32행)·`topology_library.py`(24행)에는 `from __future__ import annotations`가 있고
`design_report.py`(DR)·`audit_current_forced.py`(ACF)에는 없다. G1 M-4는 원본·목적 파일의 `__future__` 기능 집합이 **같아야** 옮긴 단위로 인정한다(2차 검토 S3 -- 주석이 평가값에서 문자열로 바뀌는 이동을
'바이트 그대로'로 보지 않는다), `move_plan check`의 `future`도 목적 ⊇ 원본을 본다. 한 MOD가 두 종류 파일의 단위를 함께 받으면 어느 한쪽은 반드시 거부된다. G1 착수 키트 모의 M card(`0f23786`, 근사 배정,
import 줄 dedup 뒤): MOD2 `_as_set`(ACF), MOD4 `_kv_table`(DR), MOD9 7단위(DR `build_topology_device_table`·`assemble_report_data`·`render_html_report`·`save_html_report`·문장 `_CSS`, ACF `_theta_evidence_for_pair`·
`audit_topology`) -- 9단위(키트 집계 def 10·변이 236), dedup 뒤 남는 거부의 유일한 원인. 세 MOD 모두 future 있는 파일에서도 단위를 받는다(MOD2 ← SD·TL, MOD4 ← SR·TL, MOD9 ← SD `save_instance_json` 등 -- D0b 검토 B2 재측정도 같다).
**v8.5**: 문서 개정 §9 (h)(N3.10 MOD9 `_kv_table` 토큰, D0b-8)로 `_kv_table`이 MOD9로 가서 갈리는 MOD는 **둘**(MOD2 `_as_set` 1·MOD9 8단위)이다 -- 9단위·FU 필요성은 그대로(부록 A F5v85: FU 없이 `import_conflicts` `__future__` = MOD2·MOD9, FU 뒤 0).

**세 처리안과 원칙 판단**:
| 안 | 내용 | 판단 |
|---|---|---|
| (가) | 그 단위들은 해당 M card에서 V3 판정을 받는다 | **기각** -- M card 기준(§8 M행·§10 E2 ①: V3 `defs` = `[]`·`mutants` = 0·`move_rejected` = `{}`)을 그 card만 풀어야 한다(이동 card에 판정할 변경이 섞임 = 기준 약화). 그리고 변이는 몸체를 바꾸는데 실제 차이는 몸체가 아니라 주석 표현이라 236개 변이가 재는 것이 차이와 무관하다(아래 실측: 몸체 코드 객체 동일). 생존이 나오면 면제 승인까지 부른다 |
| (나) | 이동 전 별도 card로 DR·ACF에 `from __future__ import annotations` 한 줄 | **기본값(D-29, card FU)** -- 바뀌는 것은 파일 머리 한 줄, 판정은 그 card의 equivalence로 따로 하고, 그 뒤 M card는 원래 기준(`defs` = `[]`) 그대로 바이트 이동이 된다(card당 한 책임) |
| (다) | 이관표에서 DR·ACF 단위를 future 없는 MOD에 모은다 | **불가** -- MOD2·MOD4·MOD9 모두 두 종류를 받으므로 future 없는 MOD를 따로 만들거나 목적 MOD의 future를 빼야 한다. 앞은 N3.10 책임 개정(사용자 승인, D-11 -- MOD9 '대표 대상'에 `design_report.render_html_report`가 이미 있다), 뒤는 SR·SD·TL 단위가 대신 거부된다(훨씬 많다) |

**(나)가 동작을 바꾸지 않는다는 근거(실측, 부록 A F2v84 -- `5f643a9` 복제본과 두 줄만 더한 복제본)**:
* 원칙: `from __future__ import annotations`는 주석의 저장 형태만 바꾼다(PEP 563 -- 문자열). 실행 환경 Python 3.14.2는 future 없이도 주석을 정의 시점에 평가하지 않는다(PEP 649 지연 평가) -- 두 경우 모두
  주석은 `__annotations__`·`inspect.signature`·`typing.get_type_hints`로 꺼낼 때만 드러나고(값 객체 대 문자열), 모듈에 이름 `annotations`(`__future__._Feature`) 하나가 더해진다.
* 그 차이를 읽는 곳: 추적 `.py` 전체 `git grep -E "get_type_hints|__annotations__|annotationlib|get_annotations|inspect\.signature"` -- 대상은 `stick_diagram`(P9 `test_dup_kcl_edges.py`)·`sizing_recipe`
  (`test_dup_w_calc.py`·`probe_mirror_ratio_error.py`)뿐이고 DR·ACF 객체는 0. `tools/gates/interface_card.py`의 시그니처는 AST(`ast.unparse`)라 영향 없음. DR·ACF 모듈 속성 `annotations`를 읽는 곳 0.
* 코드 객체: 두 파일을 future 없이/있게 컴파일해 qualname으로 짝지은 함수 몸체 코드 객체 17개(DR 12·ACF 5 -- 중첩 `_find`·`_union`·`_section`·`<genexpr>` 포함)의 `co_code`·상수·이름·지역 변수·플래그(future 비트 제외)가
  전부 같다. 다른 것은 주석 평가 함수 `__annotate__`(DR 5·ACF 4)뿐이다. 함수 `__annotations__`는 DR 5·ACF 4 함수에서 값 대 문자열로 다르다(위 '읽는 곳' 0).
* 전체 test(`pytest_gate.ini`, `--gmid-phase=2 --gmid-strict=`): 두 판 모두 1047 passed·15 xfailed, test id 1062개의 결과가 하나도 다르지 않다. E-LIB 해시(`e_lib.py`)와 E-INST(`e_inst_p3.py`, 파일럿·`folded_cascode`)의
  출력 22키가 같은 체크아웃 경로에서 모두 같다. 게이트 도구(base 판): V3 PASS 대상 2파일·변이 0, V6 PASS 발견 0, V7 PASS `new_defs` [].
* 이동 모의(G1 착수 키트 `m9_classify.py`, `5f643a9` + 두 줄, 근사 배정): 모의 M1~M9 거부 원인 `__future__` 0, import 줄 dedup(D-30)까지 하면 **M1~M9 거부 0**(키트 `0f23786` 판은 dedup 뒤 M2 1·M4 1·M9 7).

**왜 사용자 질문이 아닌가**: 승인된 기준(계획 533행 '이동 전후 함수별 `ast.dump` 해시 동일 + import 줄만 차이', G1 M-4, M card 기준)을 하나도 바꾸지 않는다 -- FU는 이동 card가 아니고 함수 해시를 바꾸지 않는 import 줄
하나이며, 이동 card는 원래 기준 그대로다. design card 목록(§8)에 준비 card가 하나 더해질 뿐이라 UD-0 범위다(승인 질문 UD-0 본문에 card 수 17과 이 한 줄을 사실로 적는다).
**배선(만들면 쓴다)**: D0a `plan`의 `import_conflicts`가 한 MOD로 가는 단위들의 `__future__` 기능 집합이 갈리면 비지 않고(D0a 계약 2, D-30), D0b 계약 test의 `plan` exit 0 단언이 그것을 FAIL로 잡는다 --
FU가 D0b 전에 병합되지 않으면 D0b가 멈춘다(§8.1 의존 'FU → D0b').

---

## 7. 계약 test와 호출부

### 7.1 위치에 묶인 계약 test(실측 cd64170, 부록 A M24)

`A/tests/contracts/`에서 엔진 파일·모듈 이름을 **실제 트리 판정에** 쓰는 곳(합성 소스 문자열 안의 `import sizing_recipe`는 입력이라 제외):

| 군 | 깨지는 시점 | test(줄) | 처리 |
|---|---|---|---|
| **A. 정의가 특정 파일에 있다고 가정** | 그 정의를 옮기는 첫 M card | `test_ic5.py:47-69`(`_DOMAIN_TABLE` 키 = (파일 이름, 함수) 21개), `test_dup_w_calc.py:442`(`size_transistor` 정의를 `sizing_recipe.py`에서 찾음 → M4에서 FAIL), `test_ts6_dead_probes.py:221-222`(`_L_ROLE_MULTIPLIERS` 바인딩 검사 범위가 `sizing_recipe.py` 한 파일 -- 옮긴 뒤 **조용히 공허**), `:261-262`(`audit_vsb_consistency`의 운영 호출자를 `sizing_recipe.py`에서만 찾음) | **T0**(M1 전) |
| **B. 모듈 이름으로 import·파일 존재 앵커** | shim 삭제(F2) 또는 호출부 갱신(F1) | `test_d_delete_dead.py:74·98-101·201·286·295`, `test_d_delete_telescopic.py:108-117·155·233`, `test_d_move_tests.py:69·73`, `test_dup_w_calc.py:56·72-75`, `test_df35_harness_paths.py:206`, `test_ts6_probe_relocate.py:528`, `test_ts6_dead_probes.py:229`, `test_restore_plan_functions.py:54·113-140`, `test_ic3.py:107·271`, `test_df36_instance_relpath.py:76·87·237·274·288`, **(v7, P9가 더함 -- 4차 검토 m3)** `test_dup_kcl_edges.py:35`(`importlib.import_module("stick_diagram")`을 돌려주는 `_sd()`) + 그 반환의 속성 `_kcl_and_matching_edges`(274·293)·`kcl_series_union`(265·283)(둘 다 레지스트리 목적지 `circuit_state_graph` = MOD3, `a796468`) | **F1** |
| **C. test 파일 이름 목록** | T1 | `test_ts3_no_print_verdicts.py:29-30` `_LEGACY_SCRIPTS` | **T1** |
| **A(v5, B26-1 병합 뒤 생김)** | M3(D-19: `rail_declaration`은 M2에서 MOD2로 가도 SD 재수출을 `load_topology`가 SD 전역으로 읽어 계수가 유지되고, `load_topology`가 M3에서 MOD3로 가면 깨진다) | `test_b26_rail_accessor.py`(B26-1 계약 3 계수 test -- `stick_diagram.rail_declaration` **모듈 속성**을 래퍼로 바꿔 호출 수를 센다. 호출자 `load_topology`가 자기 모듈 전역에서 이름을 읽으므로, 둘 중 하나라도 다른 파일로 가면 shim 속성 교체가 호출을 가로채지 못해 0회 → FAIL) | **T0**(계약 10, B26-1 병합 뒤 실측) |
| **B(v5, B26-1·B34 병합 뒤 생김)** | F1 | `test_b34_grammar_explicit.py`(`stick_diagram.<이름>(…)` 직접 호출 -- V3 인벤토리 조건이라 F1도 `<MOD>.<이름>(…)` 속성 호출 모양을 유지), `test_b26_rail_accessor.py`(`sizing_recipe._metric_kcl_residual` 이름 호출) | **F1** |

A군만 T0에 둔다(최소 수정). v5 A군 행은 V1이 수집하는 계약 test라 §7.2 D군(V1 밖 probe -- 조용히 빈다)과 달리 첫 이동 card에서 **FAIL**로 드러나 equivalence를 깬다(F6) -- 그래서 F1이 아니라
T0다(D-12 그대로: 위치 가정은 T0, 모듈 이름 import는 F1). B군은 shim이 살아 있는 동안 통과하고, 계획 534행이 '추적 파일 호출부 갱신'을 shim 삭제 조건으로 적었으므로 F1이 import를 목적 모듈로 바꾼다. 스캔 범위가
이미 `A/*.py` 전체인 판정(`_engine_files()` glob, GONE 검사)은 새 MOD 파일을 자동으로 포함하므로 고치지 않는다. T0는 `test_ts6_dead_probes.py`의 모듈 상수 `_SIZING_RECIPE`(소비자가
바꾸는 두 test뿐)도 지운다(부록 A S13 -- 초안 v2의 "229행이 계속 쓴다"는 틀렸다).

**T0의 해석 규칙 R-DEF**: 이름 n의 정의 파일 = `A/*.py`(하위 디렉터리 제외)와 `workspaces/run_harness.py` 중 최상위(메서드는 `Class.method`)에서 n을 def·class·대입으로 **바인딩**하는
파일(AST, import로 받은 이름은 정의가 아니다 -- shim 재수출은 정의가 아님). 정의 파일이 정확히 하나가 아니면 FAIL(0 = 공허, 2 이상 = 모호·사본). 이 규칙은 **판정 범위를 넓힌다**.
T0의 새 줄이 피해야 할 전수 스캔 토큰 목록은 T0 spec card 계약 9(부록 A m6).

### 7.2 추적 호출부(F1 대상, 실측 cd64170, 부록 A M22)

**v6 정정(3차 검토 B3 재측정 중 발견)**: 아래 86개는 줄 머리 정규식 계수이고, AST(import 문장 전부)로 세면 **92개**다(`7535799`) -- `import numpy as np, sizing_recipe as sr` 모양 6파일
(`A/tests/probe_physical_consistency.py`, `A/tests/probes/probe_L_search_window.py`·`probe_diode_min_vgs.py`·`probe_metric_tiers.py`·`probe_runtime_budget.py`·`probe_stack_headroom_feasibility.py`)을
정규식이 놓친다. F1 대상 목록은 AST로 뽑는다. **v7 정정(4차 검토 N1·D-26)**: SR·TL·DR은 **모듈 단위**(E3의 AST 식 -- 그 모듈을 import하는 곳 전부), `stick_diagram`은 **이름 단위**로 고른다 --
SD에서 읽는 이름(E3b의 식) 중 **F2 뒤 SD에 바인딩이 남지 않는 이름**(D0b 이관표가 SD 밖으로 보내고, SD 자신이 읽지 않아 F2가 재수출을 지우는 이름)을 읽는 곳만 F1 대상이다. SD에 남는 이름
(레이아웃 단위, SD가 스스로 읽어 import가 남는 `Transistor` 등)의 `stick_diagram` import는 F1이 고치지 않는다(v6의 "모듈 집합에 `stick_diagram` 포함"은 그것까지 대상으로 잡았다). F1이 고른 목록이
맞았는지는 F2 뒤 E3b가 판정한다(F9). 원래 계수(정규식):
엔진 4모듈을 줄 머리 `import`/`from`으로 가져오는 추적 `.py` 86개: `A/` 루트 4, `A/tests/unit` 10, `A/tests/probes` 27, `A/tests/contracts` 3, `A/tests/tools` 2, `A/tests/conftest.py` 1(conftest 변경은 V5 무조건 승인 대상), `workspaces/run_harness.py` 1, `workspaces/current-reuse-telescopic-ota-report/**` 27, `workspaces/two-stage-ota-report/**` 4, `.ai/verification/**/scripts` 6, `docs/03-analysis/**` 1. **문자열 import** 문자열 일치 10줄·6파일(`importlib.import_module("sizing_recipe")`·`_import("sizing_recipe")`, 부록 A m7) 중 **9줄·5파일이 import 호출**(전부 B군 계약 test: `test_d_delete_dead.py:101`, `test_d_delete_telescopic.py:111`, `test_dup_w_calc.py:75`, `test_restore_plan_functions.py:113·120·127·134·140`, `test_ts6_dead_probes.py:229`)이고 1줄은 **docstring 문장**(`test_d_move_tests.py:37` "판정하지 않은 것: `importlib.import_module("sizing_recipe")` 뒤 …" -- import가 아니다, 3차 검토 S7). F1 범위 = 호출 9곳. E3은 문자열 일치가 아니라 AST의 import 호출로 재므로(§10 E3, D-24) 그 docstring은 F1이 고치지 않아도 E3에 걸리지 않는다. 추적 안 된 `workspaces/**/*.py` 1개(`workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py` -- `sizing_recipe`와 `stick_diagram.save_instance_json`을 import, 9·10행 -- UD-1. v8: 경로를 전체로, 5차 검토 S5 -- `git status --porcelain --untracked-files=all -- '*.py'`로 추적 안 된 `.py`는 이것과 `.claude/hooks/*` 4개뿐, `0f23786`).

**D군 -- 모듈 속성 덮어쓰기**(부록 A S11): 엔진 모듈 속성에 대입해 계측·차단하는 추적 파일 8개(대입 **14줄** -- probe 12 + workspaces 2, `p3v3_facts.json` `S11_attr_overrides`; v3 '12줄'은 오기, 2차 검토 m1): probe 6개(`probe_b22_headroom_attribution.py:104·116`,
`probe_diode_gmid_readiness.py:63`, `probe_diode_pass_skips.py:94`, `probe_diode_window_corner.py:100·108`, `probe_matching_pair_divergence.py:124`, `probe_vds_assignment_paths.py:47·53·62·73·79`)와
`workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_cmfb.py:24`·`diagnose_cmrr_psrr.py:20`. unit·contracts·conftest·엔진·하네스에는 0. S11 패턴은 **대입문**만 센다 --
`setattr(`·`monkeypatch.setattr(` 형태는 HEAD `7535799`에서 `git grep -n setattr -- '*.py'` 0건이라 v4 결론은 그대로다(부록 A E3). B26-1이 그 형태를 contracts에 처음 들인다(위 §7.1 v5 A군 행 --
V1 수집 test라 T0). Phase 3 시작 때 S11을 대입문과 `setattr` 두 형태로 다시 잰다. 분할 뒤 호출자는 **자기 모듈 전역**에서
이름을 읽으므로 shim이나 정의 모듈의 속성을 바꿔도 다른 모듈의 호출자는 가로채지 못한다 -- probe는 V1이 수집하지 않아 계측이 **조용히** 빈다(F8). 처리 = **D-17**(F1에서 덮어쓰기 대상을 `binding_origin`으로 찾은 **호출자 모듈 전부**로 바꾸고, F1 oracle의 'import 줄 외 동일'에 이 대입 줄만
예외로 둔다 -- probe 기능을 보존하므로 삭제·범위 축소가 아니다. 초안 v3의 UD-7을 2차 검토 §5 권고대로 UD-0에 흡수, 대안 '동작 안 하는 probe로 표시'는 사용자가 원할 때만).

---

## 8. 역할별 산출물 -- spec card 목록 (N9.2-5)

card 단위는 N3.12.3(674행: 이동은 모듈 하나가 한 건). 판정 유형은 **커밋 모양이 정한다**(code 커밋이 없으면 test-only, 있으면 red-green 또는 equivalence -- `20-dead-code-dup` §8 P2·P7 정정).

| # | id(초안) | 대상 | 판정 유형 | oracle | 원칙 제약 |
|---|---|---|---|---|---|
| **G1** | `p3-gate-move-aware` | `tools/gates/reachability.py`(`SourceIndex`·`moved_defs`·해시 정의), `mutate_changed.py`(V3 대상 선택·`defs`·`moved`), `source_lint.py`(V6 비교 기준), redteam 새 케이스, design 05 §10 V3·V6·V7 행·계획 533행 문구(spec card와 같은 커밋) | red-green, `gate_change: yes`, phase 0.5(05 §18) | (a) 합성 저장소 31단계(red 8, 거부 23 -- 2차 검토 새 부류 9단계 포함; v8.4: G1 착수 키트 v9가 `class-method-edited`(거부)·`stmt-literal-moved`(red)를 더함), redteam `attacks/32-moved-defs/`(D-18), 규칙 이름은 `observe: "moved"` 관찰로 대조 | 약화 금지(M-0·M-0h·M-1~M-4·골격·qualname 중복 제외·(경로, qualname, 해시) 대조), `moved`·`move_rejected`·`defs` 출력, 해시·이름 해석 정의 하나, 실행당 색인 1회, 공개 `SourceIndex.tree(path)`(색인의 같은 파싱 객체 -- D0a가 부른다, G1 v9). base = **B33·면제 묶기·범위 정책 병합 뒤** master(§5.5): 대상이 된 def 안 변이 선택은 범위 정책 그대로, 옮기며 바뀐 def·거부 후보는 새 def(D-20), 면제 대조 불변(D-21), `build_graph` 불변. 무동작에 redteam 33·34·35 |
| **T0** | `p3-tests-location-free` | §7.1 A군 3파일을 R-DEF로, `_SIZING_RECIPE` 삭제, **v5: B26-1 계수 test의 래퍼 대상을 R-DEF 정의 파일 + 그 이름을 import로 바인딩하는 엔진 파일 전부로**(B26-1 병합 뒤) | **test-only** + V5 승인 | (c) base 트리 결과 동일 + (a) 합성 이동 트리에서도 PASS(옛 test는 FAIL) | 판정 범위를 좁히지 않는다, 정의 파일 유일성, 전수 스캔 토큰 회피 |
| **D0a** | `p3-move-plan-tool` | 새 `tools/migrate/move_plan.py`(`plan`·`check` -- `move-set`(모든 옮긴 단위)·`changed`(옮긴 클래스 안 def 포함)·`rebind`·`future`·`stmt-order`·`order`(N3.10 번호 판정, v6)·`shim`(중간 상태·완전 shim 구분, main 블록 포함, v6)·**`import-dup`**(v8.4); `plan`의 **`mod_imports`(MOD 파일 import 머리 생성 -- 이름마다 import 한 번)·`import_conflicts`**(같은 이름의 출처 갈림·`__future__` 기능 집합 갈림, v8.4 -- D-30)) | red-green | (a) 합성 저장소(이동 card를 차례로 적용한 커밋들·shim 삭제 커밋 포함, v6: split이자 N3.10인 작은 번호 파일을 import하는 card·잔여 정의가 남는 부분 이동 card 단계 포함; v8.4: `mod-imports-dedup`·`mod-imports-conflict`·`future-mixed` 단계) | CLI 정본(셸은 bash 배열), A-0으로 Phase 전 구간 동작, G1 뒤 base. 모듈 AST는 G1 `SourceIndex.tree`로만(다시 파싱 없음 -- D0a 계약 6). **v8.4 규칙(§6.2, D-31)**: 모듈 docstring 배정 제외, A-K(`--keep` 잔여), A-4·A-2·A-5·A-6 승격(MOD7 상한), A-6(참조자 없음 → 참조 최댓값), A-7(고립 → N3.10 파일 MOD), 단조 고정점 -- 합성 단계 `doc-excluded`·`keep-residual`·`lift-a4`·`lift-cap-mod7`·`a6-ref-follow`·`a7-isolated`·`monotone-seed` |
| **FU** | `p3-future-annotations` | (v8.4, §6.5 D-29) `design_report.py`·`audit_current_forced.py` 머리(docstring 뒤 첫 import 앞)에 `from __future__ import annotations` 한 줄씩 -- 그 밖 변경 0 | equivalence(test 커밋 0) | (c) V3 대상 def 0·변이 0(def 해시 불변), V6 발견 0, V7 `new_defs` 0, E-LIB·E-INST 해시 = base, 그리고 두 파일의 함수 몸체 코드 객체(중첩·`<genexpr>` 포함, 주석 평가 함수 `__annotate__` 제외)가 base와 같음(실측 부록 A F2v84) | D0b 전 병합(D0b 계약 test의 `plan` `import_conflicts`가 `__future__` 갈림을 FAIL로 잡는다 -- 만들면 배선). 몸체·다른 줄을 고치지 않는다 |
| **D0b** | `p3-registry-dest` | 레지스트리 함수 표의 **대상 행**(함수 칸의 단위가 `plan` `assignment`에 있는 행) 목적지 칸 = 배정 MOD 파일 줄기 하나 + 표마다 `근거 규칙` 열(v8.4 -- D0b 키트 결정 D0b-3·5를 design에서 닫음: 도구 출력이 없는 **비대상 행**(하네스 `canonical_spec`·`SPECS`·`run`, LUT 도구·`topology_to_markdown.py` 행 등 -- 키트 관찰 35)은 칸 불변·`근거 규칙` `-`. `근거 규칙` 값 = 재생성 시점 규칙(이력) -- 재생성 뒤 `plan`의 `rule`은 열이 A-4 입력이 되어 바뀔 수 있으므로 test는 값이 D0a 계약 2의 규칙 ID 집합 안인지만 본다), §7 `보류(Phase 3)` 9행 처리 열 = `보류(Phase 4)`(D-10 -- U-02 승인 1항 원문 "보류(Phase 3 모듈 이동·Phase 4 배선)"의 이동 몫은 이 열 + `plan`·`check`가 넘겨받는다; 보류 **집합**은 그대로), 새 계약 test `contracts/test_p3_registry_dest.py`(`move_plan plan` exit 0 + **판정 목록 일곱 = `upward`·`cycles`·`unassigned`·`conflicts`·`reg_mismatch`·`import_time_high`·`import_conflicts` 모두 빈 목록**(v8.4: 일곱째 `import_conflicts` -- D-30, §6.5 FU) + **split 파일 중 `stick_diagram.py` 밖 단위의 MOD7 배정 0**(v6, 3차 검토 m4). `import_time_high`(v7)는 D-22 (2)의 전제 "MOD8·MOD9로 배정된 단위와 그 모듈 문장이 import 시점에 읽는 이름의 출처가 번호 7 미만 MOD"(§2.2, 4차 검토 S5). 키 정의는 D0a 계약 2. **`mod_imports`는 D0b가 판정하지 않는다**(M card 몫 -- §8 M행)) | red-green(base 열에서 `reg_mismatch`로 FAIL -- base에서 참인 단언(`import_time_high`·MOD7 등)은 혼자 test가 되지 않게 진짜 red 단언과 한 test로 묶는다, D0b 검토 S1) | (d) 도구 출력 = 열. 동어반복 방지로 oracle을 둘로 나눈다(v8.4 -- D0b-4를 design에서 닫음): **실제 단위 표본 (d)-1**(N3.10 표·UD-0 문서 개정 문안에서 손으로 정한 기대 MOD -- 규칙 A-1·A-2·A-3·A-4(일반 칸·별칭 `optimizer`·`〃`)·A-5·A-K·A-6·A-7마다 한 행 이상; 레지스트리 행이 없는 표본은 `plan` `mod`만 단언) + 실제 트리 drift guard(검토 §2 (3) V4). 규칙 손적용 **합성 입력**은 D0a test 몫이다 -- D0a 병합 뒤 base에서도 통과하므로 D0b의 V2 red가 될 수 없다 | 손으로 쓰지 않는다(도구 출력). N3.10 표는 UD-0 문안(`p3_doc_amendments.md` §1·§9 -- v8.4: 3건 + D-19 + A-1 충돌 보정 8건(토큰 11개))이 design 커밋에서 이미 바뀌어 있다. **그 밖의** N3.10 개정이 계산으로 필요하면 D0b는 멈추고 그 diff를 따로 승인받는다(D-11, v6). 멈춤 경로(판정 목록별): `conflicts`·A-1이 원천인 `upward` → N3.10 토큰(D-11), 규칙 공백(`unassigned`) → design §6.2 규칙 개정(D0a 후속 card), `import_time_high` → 배정 변경(위치 규칙으로 풀 수 없다 -- F3), **`import_conflicts` → `__future__`면 FU 병합 확인, 이름 출처면 배정 변경(N3.10 밖이면 D-11)**(v8.4), MOD7 밖 → N3.10 또는 M7 card. **D0b 자신의 base(B34 → b26pre → backfill → B26-1 → B33 → G1 → FU → D0a 병합 뒤 master -- FU는 B33 뒤 D0b 전 아무 때나, §8.1)에서 처음 계산**(§6.4 재측정 조건, v7; FU v8.4). D0b 병합부터 F2까지 엔진 파일·`tools/gates`·`tools/migrate`·레지스트리 목적지 열을 바꾸는 다른 card 병합 금지(D-27, v8 범위) |
| **M1**~**M6**, **M8**, **M9** | `p3-move-mod<n>-<이름>` | 이관표 MODn 배정 전부(파일:줄은 D0b 뒤 도구 출력) | equivalence(test 커밋 0 가능 -- 05 §9.2 289행) | (c) MOVE-AST + E-LIB·E-INST + SHIM + CACHE-ID + ORDER(`check` 발견 0 -- `rebind`·`future`·`stmt-order`·옮긴 클래스 안 def `changed` 포함) + **IMPORT-ANY**(§10 `import_any`, v6 -- M9의 SD ↔ MOD9 순환 대비, §2.2 D-22) + **card마다 V3 JSON `defs` = `[]`·`move_rejected` = `{}`·`not_targeted` = 0·`targets_by_def` = `{}`**(범위 정책 키 -- 옮긴 def는 대상 def가 아니므로 둘 다 비어야 한다, §5.5.2)(옮긴 클래스의 메서드 본문 변경은 인벤토리 test가 변이를 죽이면 V3 PASS라 `defs`로만 드러난다 -- 2차 검토 S6; DoD E2까지 미루지 않는다) | G1·T0·D0b 뒤. **`tools/**` 변경 0**(`git diff --name-only <base> <head> -- tools` 빈 출력). 판정 도구는 `tools/migrate/move_plan.py`를 **마지막으로 바꾼 판정 기록의 `code_commit`**에서 꺼낸 사본(`git show <그 code_commit>:tools/migrate/move_plan.py` -- 지금은 D0a; 1차 검토 S9·2차 검토 m6) -- code-author가 판정 도구를 같은 card에서 바꿀 수 없게. 목적 MOD 파일은 원본의 `from __future__` 줄을 가진다(F7). **MOD 파일의 import 머리 = 그 card base에서 돌린 `plan`의 `mod_imports[<MOD 파일>]` 그대로**(이름마다 import 한 번 -- 원본 파일들의 import 줄을 모아 붙이지 않는다, D-30; 어긋나면 `check` `import-dup`·`move-rejected`, v8.4). 재수출 줄 위치와 M8·M9의 import 줄 위치는 §2.2(D-22) |
| **M7** | -- | `stick_diagram.py`에 레이아웃만 남았는지 -- 이동 없음 | M2·M3·M9에 흡수(빈 card 금지) | -- | -- |
| **M10** | `p3-mod10-entry` | 새 `gmid_design_pipeline.run_gmid_design_pipeline(spec, *, topology_path, search, output_dir)`, 하네스 `run()`이 부른다 | **red-green**(새 test가 library 회로로 진입점을 불러 E-INST 해시 대조 -- base에 진입점 없음) | (c) E-INST·E-LIB + (a) ENTRY | 만들면 배선: 하네스 즉시 호출, `after_phase3` 루트. 지금 인벤토리는 이름 과대 근사뿐(§2.3). **진입점 test 회로 = instance.json을 만드는 회로(E-INST 회로 집합) 중 한 판이 가장 짧은 것 = `folded_cascode`**(기록 13~19초; v8 -- 5차 검토 S4: `two_stage_ota`·`nmcnr_amplifier`는 instance.json을 만들지 않아 후보가 아니고 실패 경로 보조 회로로만 쓴다). '작성 전 실측'에 변이 수·회로별 한 판 시간·인벤토리 한 번 실행 시간과 V3 비용 추정. **v7(4차 검토 S3)**: E-INST 해시만 대조하면 지금 `run()` 변이 71개 중 50개가 산다(실측 §2.3) -- '작성 전 실측'에 (i) 옮길 문장 범위(준비 문장은 `run()`에 남김) (ii) stdout·report 해시 대조 + 실패 경로 회로 하나 (iii) 회로가 지나가지 않는 분기의 합성 반환값 계약 (iv) 비용(목표 생존 0, 약 20~40분)을 적는다 |
| **T1** | `p3-test-relocate` | `unit/test_selftest_*.py` 4개 → `unit/test_mod*.py`, C군, 새 C9 매핑 | test-only + V5 승인 | (c) 수집 test id 집합 = 매핑 | `10-test-separation` 413행 |
| **F1** | `p3-callers-update` | §7.2 추적 호출부 import(줄 머리, 문자열 import **호출 9곳**)를 목적 모듈로(D-9 제외 집합 밖), B군 계약 test, D군 덮어쓰기 대상(D-17). **v7: 범위는 이름 단위**(§7.2 -- SR·TL·DR은 모듈 단위, `stick_diagram`은 SD에 바인딩이 남지 않는 이름을 읽는 곳만; 4차 검토 N1) | equivalence | (c) 호출부 AST가 import 줄(과 D-17이 허용한 D군 대입 줄) 외 동일 + E-INST + IMPORT-ANY. '작성 전 실측'에 F1 목록 = (E3 AST 식의 SR·TL·DR importer) ∪ (F1 base에서 E3b 식으로 모은 SD 이름 reader 중 F2 뒤 SD에 남지 않는 이름을 읽는 곳 -- D0b 이관표와 §2.2 F2 규칙으로 계산) | test 쪽 문자열 변경은 V5 승인 |
| **F2** | `p3-shim-delete` | shim 3파일 삭제, `stick_diagram` 임시 재수출 제거(SD 자신이 읽지 않는 이름만 -- §2.2), REG-DEST | red-green | (a) GONE-SHIM + LAYER(SD의 MOD9 위쪽 재수출이 사라져 `import_layering` exit 0) + **SD-NAMES(§10 E3b, v7 -- 4차 검토 N1: 지운 재수출을 읽는 추적 파일 0)** | WP-14 |

**card 수 17**(G1, T0, FU, D0a, D0b 5 + M1~M6·M8·M9 8 + M10 1 + T1·F1·F2 3 -- M7 흡수; v5 '15'는 오기, 3차 검토 m1; v8.4: FU 추가로 16 → 17, §6.5).

### 8.1 순서와 병렬 준비

**확정 순서(v7; v8 귀속 정정 -- 5차 검토 S3)**: 사용자 지시 원문 "P10b 끝나면 push하고 Phase 2 완료 판정 진행해"는 P10b → Phase 2 DoD만 정한다. 34 → 35 → B34 → B26-1은 오케스트레이터가 제안하고 사용자가 "응, 그렇게 진행해"로 답한 순서(`_drafts/pending_questions.md` Q-B34-PHASE), test 보강 card·B33의 자리와 Phase 3 안 순서는 오케스트레이터 배열이다. **v8.1(6차 검토 N3)**: B34와 B26-1 사이에 card 둘이 들어간다 -- 앞선 test 보강 card(b26pre, `20260930-b26-pre-test-strengthen`)와 backfill 결함 card(`20261001-b26-backfill-interdig-final-audit`, red-green, `sizing_recipe.py` 엔진 변경, U-BF 답 '결함으로 고침' -- 승인 기록 `20261001-b26-backfill-interdig-fix`). 순서는 backfill card 초안의 'B34 → b26pre → 이 card → B26-1'(`b26pre_revision_log.md` m5)이다. 넷 모두 D0b 전에 병합되므로 §6.4·§9.1 재측정 (1)이 흡수하고 판정식은 같다. 병합 기준, 'A → B' = A 병합 뒤 B 병합. v6의 '필수/편의' 구분(3차 검토 S2 (iii)·m5)은
이 확정으로 대체된다 -- 아래는 한 줄 순서이고, 근거 열은 그 순서가 지키는 의존(없으면 '확정 순서')이다:

```
P10b → [Phase 2 DoD PASS] → 면제 묶기(34) → 범위 정책(35) → B34 → b26pre(20260930-b26-pre-test-strengthen)
     → backfill(20261001-b26-backfill-interdig-final-audit) → B26-1 → B33(33)
     → Phase 3: T0, FU, G1(32) → D0a → D0b → M1 → M2 → … → M6 → M8 → M9 → M10 → T1 → F1 → F2
```

| 앞 | 뒤 | 근거 |
|---|---|---|
| P10b | Phase 2 DoD | Phase 2 마지막 card(P9·P10은 `a796468`에 병합됨). Phase 2 DoD의 N6.3 판정 기록 목록은 design 20 §8 card뿐이다 -- **B34·B26-1은 들지 않는다**(A2로 앞당긴 Phase 4 몫, §6.4). v8.3: 네 card(B34·b26pre·backfill·B26-1)는 `phase: 3`(기록 `20261001-b26-phase3-cards`)이라 Phase 3 DoD의 `^phase: 3$` 목록에 든다(§9.1) |
| Phase 2 DoD PASS | 면제 묶기(34) | 확정 순서. A1-a(면제 묶기 초안 11행 "P9·P10·P10b 뒤")도 만족한다 |
| 면제 묶기(34) | 범위 정책(35) | 범위 정책 초안 11행 |
| 범위 정책(35) | B34 | 확정 순서 |
| B34 | b26pre(`20260930-b26-pre-test-strengthen`) | b26pre 초안 순서(B26-1 V3 대상의 기존 동작 고정 -- B34 병합본에서 잰다) |
| b26pre | backfill(`20261001-b26-backfill-interdig-final-audit`) | backfill card 초안 순서 'B34 → b26pre → 이 card → B26-1'(v8.1, 6차 검토 N3) |
| 면제 묶기(34)·범위 정책(35)·B34·b26pre·backfill | B26-1 | A1-a·A1-b(B26-1의 V3 비용 근거), B26-1 초안 "B34 → B26-1"(A2). b26pre·backfill이 B26-1 V3 대상의 기존 동작을 고정하거나 바꾼다(backfill card의 B26-1 인계: 그 병합본에서 B26-1 V3 재측정) |
| B26-1 | B33(33) | 확정 순서 |
| B33(33)·면제 묶기(34)·범위 정책(35) | G1(32) | §5.5.1 -- G1 base, 합성 문장의 주인 |
| B26-1 | T0 | T0 계약 10이 B26-1의 계수 test를 고친다 |
| G1 | D0a | D0a가 G1의 `SourceIndex`·`moved_defs`를 부른다(정의 하나). 오케스트레이터 지시문의 괄호 "T0·D0a·D0b → G1(32)"는 이 의존과 어긋난다 -- D0a는 G1 없이 import가 실패하므로 G1 → D0a로 둔다(§11-12, 확인 요청) |
| B34·b26pre·backfill·B26-1·B33·D0a | D0b | §6.4 -- 이관표를 D0b 자신의 base에서 처음 계산 |
| FU(v8.4) | D0b | §6.5 -- D0b 계약 test의 `plan` exit 0에 `import_conflicts`가 들어가 `__future__` 기능 집합이 갈린 배정이 남으면 FAIL. FU는 다른 card와 의존이 없다(엔진 두 파일 머리 한 줄씩 -- B33 뒤 아무 때나, D-27 동결 전) |
| Phase 2 DoD PASS | T0·FU·D0a·D0b(phase 3 card) | 계획 991행 "이전 Phase DoD PASS"(D-23). 확정 순서상 B26-1·B33 뒤라 자동으로 성립한다 |
| Phase 2 DoD PASS | B34·b26pre·backfill·B26-1(phase 3 card -- v8.3) | 계획 991행 "이전 Phase DoD PASS"(D-23). 확정 순서 그대로라 자동으로 성립한다. design 30 승인·U-03은 기다리지 않는다(기록 `20261001-b26-phase3-cards` 범위 설명) |
| G1·T0·D0b | M1 | F5·F6, §9.1 |
| M1 → M2 → … → M6 → M8 → M9 | M10 → T1 → F1 → F2 | ORDER(번호순), F1이 shim 삭제 조건(534행) |
| D0b 병합 | F2 병합까지 | **동결(D-27, v7 -- 4차 검토 S4; v8 범위 확대 -- 5차 검토 S6)**: 이 구간에는 엔진 파일(`A/*.py`, `workspaces/run_harness.py`), `tools/gates/**`·`tools/migrate/**`, 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`)의 '이관 목적지' 열을 바꾸는 Phase 3 밖 card를 병합하지 않는다 |

* **phase 3 card의 병합 시점(D-23)**: T0·FU·D0a·D0b는 spec card `phase: 3`이고 계획 991행 공통 착수 조건 "이전 Phase DoD PASS"가 이 card들에도 걸린다(기본값 = Phase 순서 그대로). v8.3: B34·b26pre·backfill·B26-1도 `phase: 3`이다(사용자 답 2026-10-01, 기록 `20261001-b26-phase3-cards`) -- "이전 Phase DoD PASS"는 확정 순서(Phase 2 DoD 뒤)로 자동 성립하고, design 30 승인·U-03은 그 기록이 기다리지 않는다고 정했다. 게이트는 이 순서를
  강제하지 않으므로(`merge_gate.rule10_phase` 실측, 3차 검토) 오케스트레이터가 지킨다. G1은 `phase: 0.5` 게이트 변경(05 §18)이라 Phase 2 DoD와 독립이지만 확정 순서상 B33 뒤다.
  test·code worktree는 각 card의 앞 card가 병합된 뒤 만든다. 그 전에 할 수 있는 것은 **준비**(spec card 초안·작성 전 실측·interface card 초안)뿐이다.
* **지금 병렬로 준비 가능(spec card 초안·작성 전 실측)**: G1, T0, D0a, FU(v8.4). 실행 순서는 G1 → D0a, T0·FU는 G1과 독립(FU는 D0b 전).
* **B26-2~B26-4·B35의 자리(v7 -- 4차 검토 S4, D-27)**: 계획 769·929·936행은 B26-2(극성)·B26-3(MNA 고정 노드)·B26-4(이름 상수 삭제·lint)를 "Phase 3 착수 전에 해도 된다"고 적는다. 위 확정
  순서에는 없으므로 **기본값 = F2 뒤**(Phase 3 뒤 새 모듈에서 바꾼다). 오케스트레이터가 어느 것을 Phase 3 전에 넣으려면 **D0b 전**(B33 뒤·G1 앞 또는 G1 뒤·D0b 앞)에 병합해야 하고, 그러면
  §9.1 재측정 (1)에 그 card가 들어간다. B35(B34·B26-1 인계 사이트 5~8·10·14 -- §6.4)는 착수 조건(B36 게이트 변경 card·`plan_tables` 승인·B26-2)상 Phase 3 전에 올 수 없어 **F2 뒤**다.
* M 순서가 번호순인 이유: 작은 번호부터 만들면 매 card 병합본에서 새 파일이 잔여 shim을 import할 일이 없다(ORDER). M 작성 전 실측은 D0b 이관표 한 벌에서 결정적으로 나온다.

---

## 9. 착수 조건과 사용자 결정 (N9.2-7)

### 9.1 착수 조건

* 공통(N6.1 991행): 이 문서의 사용자 승인(DEC-51), **Phase 2 DoD PASS**. v6 작성 중 gate `master`가 `7535799` → `a796468`로 나아갔다(P9 병합·판정 기록 `766b5c2`, P10 판정 기록 `62ae24f`,
  계획 A2 정정 `8356c1e`, P10b spec card `a796468`). **v7 정정(확정 순서, §8.1)**: `a796468` 기준 Phase 2에 남은 것 = Phase 2 card **P10b** 병합과 design 20 §10 **DoD E0~E5**(P3c 보류 B21은 D2
  기본안대로 관찰 기록)뿐이다. **B34·B26-1은 Phase 2 DoD 뒤**에 병합하는 앞당긴 card(A2)이고 Phase 2 DoD의 N6.3 판정 기록 목록에 들지 않는다(design 20 §8 범위 밖 -- v6이 "Phase 2에 남은 것"에
  둘을 넣은 것은 틀렸다). **v8.3**: 네 card(B34·b26pre·backfill·B26-1)는 spec card `phase: 3`(사용자 답 2026-10-01, 기록 `20261001-b26-phase3-cards`)이라 **Phase 3 DoD의 N6.3 판정 기록 목록**에 든다 -- Phase 2 DoD가 `git grep -l -E '^phase: 2$' <H> -- docs/02-design/specs`로 모은 것과 같은 방식(`^phase: 3$`)이면 네 card가 잡힌다. Phase 3 DoD는 그 판정 기록을 각 card 병합 때 기록 그대로 센다(다시 판정하지 않는다 -- E2가 V3를 다시 도는 것은 M card뿐이고, E5는 P2D 대 마지막 병합본 비교라 네 card의 의도된 변경은 D-28 (e) 목록으로 이미 들어 있다). 몫은 A2로 앞당긴 Phase 4 몫이라 계획 1001행대로 Phase 4 행 범위에서 빠지지 않는다. 게이트 card(`phase: 0.5`) 면제 묶기·범위 정책·B33은 Phase 2 DoD 항목이 아니라 G1의 선행이고, 확정 순서상 Phase 2 DoD 뒤다. 이 조건은 M card뿐 아니라
  T0·FU·D0a·D0b(`phase: 3`)의 **병합**에도 건다(D-23).
* U-03(N7.2 1078행): 승인 기록 없음(부록 A M27).
* 게이트 선행: B28 병합(**완료** -- `2b41e79`, 판정 기록 `8790b24`), **B33·면제 묶기·범위 정책 병합(G1 전, §5.5.1)**, G1 병합.
* **엔진 선행(A2, v5)**: B34·B26-1(앞선 test 보강 card와 backfill 결함 card 포함 -- v8.1) 병합(M1 전, 확정 순서상 Phase 2 DoD 뒤·B33 전). 승인 기록 `20260930-b26-before-phase3` '재검토': 둘 중 하나라도 병합되지 않은 채 M card를
  시작하면 그 card의 앞당김이 효력을 잃는다 -- 그래서 M1의 착수 조건이다. T0는 B26-1 병합 뒤(§8.1).
* **동결(v7, D-27 -- 4차 검토 S4; v8 범위 확대 -- 5차 검토 S6)**: **D0b 병합부터 F2 병합까지** 엔진 파일(`A/*.py`, `workspaces/run_harness.py`), `tools/gates/**`·`tools/migrate/**`, 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`)의 '이관 목적지' 열을 바꾸는 Phase 3 밖 card는 병합하지 않는다. 이유: 엔진 파일 -- D0b 뒤에 병합되면
  이관표(레지스트리 열)·§6.4 수치가 낡고, M card 사이에 병합되면 A2 '재검토'와 같은 편집 범위 문제(나누는 중인 파일을 다른 card가 바꿈)가 생긴다. `tools/gates/**` -- DoD E2는 마지막 병합본의
  게이트로 card마다 V3를 다시 돌리므로(§10 `GC`) 사이에 게이트가 바뀌면 card 판정 때와 다른 게이트로 재판정한다(예: B35의 착수 조건인 게이트 변경 card B36은 확정 순서에 없다). `tools/migrate/**` -- M card 판정 도구는
  `move_plan.py`를 마지막으로 바꾼 판정 기록의 `code_commit` 사본이라(D-16) 다른 card가 바꾸면 사본 출처가 바뀐다. 레지스트리 목적지 열 -- D0b 계약 test(`reg_mismatch`)가 이후 모든 card V1에서 깨진다
  (크게 깨지므로 약화는 아니지만 Phase 3가 멈춘다). **강제 수단**: 게이트는 병합 순서를 강제하지 않으므로 오케스트레이터 병합 순서 규칙이고, DoD가 사후에 잰다 -- E6 MOVE-TOTAL(base = M1 판정 기록
  `base_commit`)이 M1~F2 사이의 엔진 단위 변경을, §10 E2 앞의 `git diff --quiet "$B0" HEAD -- tools/gates tools/migrate`가 같은 구간의 도구 변경을, E4 `reg_mismatch`가 목적지 열 drift를 잡는다.
  **D0b 병합~M1 base 구간은 DoD가 덮지 않는다**(M1 base가 그 뒤라서) -- 그 구간은 M1 card의 `check`(`assigned` = D0b 레지스트리)와 오케스트레이터 순서 규칙에만 기댄다. 꼭 필요하면 그 card를 병합한 뒤 **D0b를 다시
  계산**하고(레지스트리 열 재생성 card), N3.10 밖 개정이 나오면 D-11대로 따로 승인받는다. B26-2~B26-4(계획상 Phase 3 전 가능)는 확정 순서에 없으므로 기본값 F2 뒤이고, Phase 3 전에 넣으려면 D0b 전에
  병합해 아래 재측정 (1)에 포함한다. B35(사이트 5~8·10·14)는 착수 조건상 F2 뒤다(§8.1, §6.4).
* 재측정(2차 검토 S8, v7 확정 순서 기준 -- Phase 3 시작 때): (1) B34·B26-1(test 보강 card와 backfill 결함 card 포함 -- v8.1, 6차 검토 N3)과, D0b 전에 병합된 그 밖의 엔진 card(예: B26-2~B26-4를 앞당기면 그것)의 병합본에서 머리의 재측정
  조건 (1)의 엔진 줄 인용·부록 A 행과 §6.4 표의 추정 행 전부, §7.1 v5 행(B26-1·B34 계약 test의 실제 줄), §7.2 S11(대입문 + `setattr`), §7.2 F1 범위의 SD 이름 reader 목록(E3b 식).
  (2) B33·면제 묶기·범위 정책 병합본에서 §5.1 줄 번호·V7 미도달 수, G1 card '작성 전 실측' 1·2, 부록 A G2·G5' base 열, §10 E2의 출력 키.
  (3) D0b는 자기 base(B34·B26-1·B33·G1·FU·D0a 병합 뒤 master)에서 이관표를 처음 계산한다(§6.4). 인용 줄·개수가 바뀌면 이 design의 개정이 아니라 사실 문장 갱신이다 -- 규칙·판정식은 줄 번호에 기대지 않는다.
* 문서 개정 커밋 시점(검토 S4): 게이트 변경 card(G1)는 spec card와 그것이 개정하는 design 05·계획서 문구를 **같은 커밋(승인 전)**에 넣고, 승인 기록(`target_kind: diff`)의 `diff_path`가
  세 경로를 덮는다(B28 승인 `20260930-v3-history-clone`의 `diff_path` 두 줄 선례). 이 design의 UD-0 문서 개정도 design 커밋과 함께 승인 대상 diff에 든다(선례
  `20260922-10-test-separation-design`의 `diff_path`가 계획서·00·05·10을 함께 덮는다). **그 문안은 `_drafts/p3_doc_amendments.md`**(지금 줄 번호와 원문 인용, 새 문안 -- 3차 검토 B4)이고
  오케스트레이터가 design 커밋에 그대로 넣는다. N3.10·N3.12.3은 `plan_tables_hash` 입력이 아니므로(`merge_gate.py:107-176`: N4.1·N4.2·N6.1·N3.12.2만) `plan_tables` 승인은 필요 없다(3차 검토 실측).
* **N3.10 개정 시점(v6, 3차 검토 B4)**: UD-0이 덮는 N3.10 개정은 **지금 계산 가능한 3건 + D-19**(`p3_doc_amendments.md` §1)이고 design 커밋 때 바뀐다. D0b가 자기 base(B26-1·B34 병합 뒤)에서 그 밖의
  충돌을 계산하면 D0b는 레지스트리 열을 쓰기 전에 멈추고, 오케스트레이터가 그 N3.10 diff를 **따로** 사용자 승인(`target_kind: diff`)으로 받은 뒤 D0b를 잇는다(D-11). UD-0은 그 계산 결과를 위임받지 않는다.

### 9.2 사용자 결정(진짜 사용자 몫만 -- 질문 4개(v8: A2-③ 추가, v8.3: A2-③은 2026-10-01 답으로 결정되어 뺌), 문안은 `_drafts/phase3_approval_question.md`)

초안 v3의 5개(UD-0·1·5·6·7)에서 2차 검토 §5 권고대로 줄였다: **UD-7 → D-17**(기본안이 probe 기능을 보존하므로 삭제·범위 축소가 아니다 -- 원칙으로 확정, UD-0이 덮는다),
**UD-6 → '뒤에 올 승인'**(T0 V5 승인은 test 커밋 뒤 diff 해시로만 받을 수 있어 착수 전 결정이 될 수 없다 -- T1·F1의 V5 승인과 같은 기준).
v6(3차 검토 §7): UD-0 안에 묻혀 있던 **기준에 닿는 기본값 둘(D-9, D-17)**과 **D0b의 N3.10 추가 개정을 위임하지 않는다는 것**을 질문 문안에 드러내고, D-19는 따로 묻는다.

| ID | 결정 | 기본안(원칙에서) | 왜 사용자 몫인가 |
|---|---|---|---|
| **UD-0** | 이 design 승인(DEC-51). §9.3 기본값(D-1~D-31)과 문서 개정 문안(`p3_doc_amendments.md`: 계획 N3.10 표 3건 -- `load_topology`·`validate_theta_declaration_order` → MOD3, `optimize_full_circuit_budget` Phase 3 위치 MOD8 -- 과 D-19, **v8.4: A-1 충돌 보정 8건(토큰 11개)**(§6.2 -- §1 갱신·§9, 그중 MOD6의 θ 평가·시작점·SLSQP 넷은 Phase 3 동안 MOD8, `apply_theta_feed` MOD5), **v8.5: 책임 보정 1건** `_kv_table` → MOD9(문서 개정 §9 (h), D0b-8 -- 레지스트리 칸 `〃` 번짐), **v8.4 사실로 드러낼 것**: 준비 card FU로 card 17(D-29), §7 보류 처리 칸 9개 Phase 3 → Phase 4(D-10, U-02 1항 원문), 534행 shim 문장(D-2·D-9), N3.12.3 test-only 열거에 "Phase 3 T0·T1", `00-common` §3.2 103행·§10.1 431행(D-5), `10-test-separation` §5.6 영역 표 '파일' 열을 설명으로(T0))을 함께 덮는다. **기준에 닿는 기본값**(질문에 드러냄): **D-9**(534행 "추적 파일 전부 갱신"의 예외 -- 판정 기록 증거 스크립트 `.ai/verification/**`와 기준 커밋 원자료 `probe_stage_partition.py`는 갱신하지 않는다. v7 정정(4차 검토 m2, `a796468` 실측): SR·TL·DR import(E3 AST)가 걸리는 파일은 `probe_stage_partition.py` 1개뿐이고 `.ai/verification/**`는 0이다. `.ai/verification/**`의 `import stick_diagram as sd` 8파일 중 F2 뒤 깨지는 것은 근사 배정 기준 **2개**(`e_lib_inst.py` -- `save_instance_json`, `diff_dup.py` -- `_import_analog_grammar`·`_kcl_and_matching_edges`; 정확한 수는 D0b 뒤 -- v8, 5차 검토 S2 실측) -- E3b도 같은 제외 집합을 쓴다), **D-17**(F1 oracle 'import 줄 외 동일'에 D군 probe 대입 14줄 예외), **D-28 E5 비교 판**(v8.2 -- **기본안 = 선례 `20260930-phase2-e4-baseline` 기본안 모양**: Phase 2 DoD 대상 커밋 P2D와 Phase 3 마지막 병합본을 같은 경로에서 비교하고, 사이 card가 의도적으로 바꾼 필드(E-LIB `load_topology` `meta["rails"]` 하나, E-INST 없음 -- D-28 (e))만 빼서 그 card 계약값으로 따로 판정, 나머지 해시 같음; **대안 = B0(M1 base)와 비교** + Phase 2 DoD 판과는 card 판정 기록 사슬. v8.1까지는 반대였다 -- 6차 검토 N1이 드러낸 선례 불일치를 선례 쪽으로 풀었다), **D-31**(v8.4, v8.5에서 이 묶음으로 옮김 -- 8차 검토 m1: 배정 규칙 승격이 계획 517행 '레지스트리 열 = 정본'을 '칸 MOD = 하한'으로 읽는다; 시제품 관찰 32단위가 칸과 달라지고 D0b가 열을 도구 출력으로 다시 써서 열 = 이관표 회복, MOD7로는 올리지 않음; 대안 = 열 정본 + 충돌 함수 32개를 N3.10 토큰으로 -- 승인 질문 (d)). 새 측정 스크립트 `e_lib_p3.py`도 이 승인이 덮는다(문서 개정 §8). **D0b가 계산할 N3.10 추가 개정은 위임하지 않는다**(나오면 따로 묻는다 -- §9.1). N3.10 533행 문장은 UD-0이 아니라 G1 승인(UD-5)이 덮는다. v7: DoD에 E3b(SD 재수출 삭제 뒤 추적 호출부 확인, D-26)가 더해졌다 -- 기준을 더하는 쪽 | §9.3 | 계획서 표·판정 문구 개정은 승인 대상(0.5 공격 16), 기준 예외(D-9·D-17)와 판정 기준인 비교 판·빼는 필드 목록(D-28)·레지스트리 열의 정본성(D-31)은 사용자 몫 |
| **D-19** | `rail_declaration`(B26-1)을 둘 모듈 | (가) MOD2(N3.10 MOD2 '대표 대상'에 추가) -- §6.4 | 계획서 표 개정을 부르는 배치 선택이고 두 안이 원칙상 모두 성립한다(§6.4 중립 기록) |
| **UD-1** | **U-03**: 추적 안 된 `workspaces` 스크립트가 shim 삭제로 깨지는 것을 허용 | 계획 기본안 그대로 -- 추적 파일은 전부 F1에서 갱신, 추적 안 된 1개(`workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py` -- `sizing_recipe`의 `SemiEmpiricalGmIdLUT`·`optimize_full_circuit_budget`와 `stick_diagram.save_instance_json`을 import, 9·10행)는 F2 뒤 두 import가 모두 깨진 채 둔다. 대안: (나) 지금 저장소에 추가(추적)하고 F1에서 함께 갱신 (다) 삭제(사용자 작업) -- 3차 검토 S8 | 계획이 사용자 결정으로 지정(N7.2) |
| **UD-5** | **G1 게이트 변경 승인** + **이동 인식 방식의 비용 선택** | **(가) 전역 규칙**(G1 spec card 그대로) | 판정 기준(게이트) 변경은 사용자 승인(05 §18). 두 방식 모두 '약화 금지'를 만족하므로 비용 선택은 사용자 몫(1차 검토 §3-2) |
| **A2-③** | (v8, 5차 검토 S3; v8.1 -- 6차 검토 N3; **v8.3 결정됨**) B34·B26-1과 그 사이 card 둘(앞선 test 보강 card `20260930-b26-pre-test-strengthen`, backfill 결함 card `20261001-b26-backfill-interdig-final-audit`) -- 네 card의 병합 Phase | **결정됨**(2026-10-01, 사용자 답 B26 묶음 [card phase] "phase 3 + 정정 기록 (Recommended)", decision 기록 `20261001-b26-phase3-cards`): 네 card `phase: 3`, 순서 B34 → b26pre → backfill → B26-1 그대로 Phase 2 DoD 뒤·Phase 3 M card 전 병합. 승인 기록 `20260930-b26-before-phase3` ③의 'Phase 2 진행 중' 문구는 그 새 기록이 바로잡는다(옛 기록은 고치지 않음). design 30 승인·U-03을 기다리지 않는다. 판정 기록 V1은 `--gmid-phase=3`(§11-11). 네 card는 Phase 3 DoD N6.3 목록에 든다(§9.1) | 이 승인 질문에서 묻지 않는다(이미 답함). `_drafts/pending_questions.md` Q-B34-PHASE는 닫음(2026-10-01) |

**UD-5 비용 비교**(권고 (가)). 근거 수치는 v4 재측정(`p3v4_g1_results.json`, HEAD `7535799`의 실제 게이트 도구 + 참조 구현 모의)이다:

| | (가) 전역 이동 인식 규칙 | (나) 승인 기록에 선언된 이동만 인정 |
|---|---|---|
| 막는 것 | M-0·M-0h·M-1~M-4·골격·qualname 중복 제외가 거부하는 부류. 합성 단계 51개 중 거부 단계 전부 거부 -- 1차 검토 반례(거부 13단계)와 2차 검토 새 반례 22건(G1 19 + `move_plan check` 3). 규칙 밖의 새 부류가 나오면 규칙을 고쳐야 한다(v3 → v4가 그 예: 2차 검토가 v3 규칙을 통과한 7부류를 찾았고 M-0h·qualname 중복 제외·해시 대조·출처 정밀화(S1)·`__future__` 대조를 더해 닫았다) | 선언 밖 이동은 전부 '새 정의'. **선언 안에서는 (가)와 같은 규칙이 필요**하다 -- 2차 검토의 N1·P·N3b·N4·N13·N5는 모두 선언된 from→to 안에서 일어나므로 선언만으로는 막지 못한다 |
| 비용 | 게이트 변경 1회(G1). card마다 추가 승인 없음 | 게이트 변경 1회 + M card 8개마다 승인 기록 1건(+ 선언 형식·대조 코드) |
| 이중 대조 | Phase 3 안에서는 이미 `move_plan check`의 `move-set`이 **이 base→head의 모든** 옮긴 단위를 **이관표(D0b 승인 결과)**와 대조한다(2차 검토 S4 반영) -- 선언이 이관표로 존재한다 | 이관표와 승인 선언이 같은 내용을 두 번 적는다 |
| Phase 3 밖 | 규칙대로인 이동은 어느 card에서든 인정 -- 실제 엔진 4파일 통째 이동 모의에서 거짓 거부 0(단위 402/402, def 473/473, M-0h 위반 0) | 선언 없는 이동은 불인정(보수적) |

권고 근거(v4 수치로 다시 씀): (나)가 (가)보다 더 막는 것은 '규칙을 통과하는 이동이 Phase 3 밖에서 계획 없이 일어나는 것'뿐이다. 그 이동은 v4 규칙상 (i) 단위 해시가 원본과 같고
(M-1·골격), (ii) 목적 파일에서 유일하게 바인딩되며 덮어쓰지 않고(M-0·M-0h), (iii) 원본 자리에 재수출만 남고(M-2), (iv) 전역 읽기 출처·`__future__`가 원본과 같다(M-4) -- 2차 검토가 v3에서
찾은 약화 7부류(N1·N2·P·N3b·N4·N13·S2 `except as`)는 v4 규칙에서 전부 base 도구와 같은 exit로 돌아왔고(§5.2 표), v3 26단계의 exit는 하나도 바뀌지 않았으며, 실제 엔진 통째 이동의 거짓 거부는
0이다. 규칙이 모든 부류를 증명하지는 않는다(측정 한계: 합성 반례 + 엔진 통째 이동) -- 그래서 Phase 3 안에서는 `move_plan check`(이관표 대조·`rebind`·`future`·`stmt-order`·def 단위
`changed`)가 두 번째 선을 이루고, M card마다 V3 `defs` = `[]`을 요구한다(§8). (나)의 선언은 그 두 번째 선과 같은 정보를 한 번 더 적을 뿐 선언 안의 약화(N1·P 등)는 막지 못한다 --
추가 승인 8건은 원칙('결정은 원칙으로 기본안부터')에 비해 이득이 없다.

뒤에 올 같은 성격의 승인(지금 결정할 것 아님 -- 각 card의 test 커밋 뒤 diff 해시로 받는다): **T0 V5 승인**(판정 범위 확대 + 유일성 검사 추가, 기대값 불변, 죽은 상수 삭제 -- 초안 v3 UD-6; **v8.4: T0 착수 키트 시제품 기준 V5 도구 발견 4 = 리터럴 변경 3 + 비교 완화 1** -- 비교 완화는 유일성 단언 `len(...) == 1`이 새 비교 연산자로 잡힌 것(판정을 더하는 단언이지만 도구 분류상 '비교 완화')이라 T0 승인 기록 범위 설명에 그 1건을 이름으로 적는다. 실제 수·해시는 test 커밋에서 다시 잰다, `draft_p3_t0.spec.md` 113~117행),
T1·F1의 V5 승인(test 파일 이동·import 문자열).

### 9.3 원칙 유도 기본값(UD-0으로 확정 -- 따로 묻지 않는다)

| ID | 기본값 | 근거 |
|---|---|---|
| D-1 | 평면 배치. B11(`extract_selftest.py:645` 비재귀 glob)은 LAYOUT-FLAT로 해당 없음 | N3.10 표 파일 이름이 경로 없는 이름 |
| D-2 | `topology_library.py`·`design_report.py`도 재수출 shim 경유 뒤 F2 삭제, `stick_diagram` 재수출은 임시 | 파일당 한 책임, WP-14 |
| D-3 | `optimize_full_circuit_budget` → Phase 3 위치 MOD8(통째) | A-3 계산, `00-common` 435행 |
| D-4 | 쪼개라고 적힌 16행은 통째로(A-3), 쪼개기는 원래 담당 Phase | 533행 이동 전용 |
| D-5 | M10 시그니처 `(spec, *, topology_path, search, output_dir)`, 나머지 인자는 CC-7·CC-8. `00-common` 431행에 `topology_path` 추가, 103행 담당 정정 | `run_harness.py:427·446` |
| D-6 | `canonical_spec`/`SPECS`/`_spec_*`는 하네스에 남김(레지스트리 392~395행 목적지 정정) | 계획 532행 |
| D-7 | `move_plan.py`는 `tools/migrate/`(code-author), test는 `A/tests/tooling/`(test-author) | 계획 N3.11 549행 |
| D-8 | `audit_current_forced.py`는 도구로 남기고 `audit_topology`는 A-4대로 | 레지스트리 248·389행 |
| D-9 | GONE-SHIM·SD-NAMES 제외 집합 = `.ai/verification/**`(판정 기록 증거 스크립트 -- 기록된 base 커밋에서 재실행되는 증거) + `docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition.py`(기준 커밋 78b58c6 실측 원자료). **v7 정정(4차 검토 m2, `a796468`)**: v6의 "판정 기록 스크립트 6개"는 4모듈 줄 머리 정규식 계수였다 -- E3(SR·TL·DR, AST)로 걸리는 `.ai/verification/**` 파일은 **0**이고 제외 집합 안 적중은 `probe_stage_partition.py` 1개뿐이다. `.ai/verification/**`는 `import stick_diagram as sd` **8파일**이 SD 경유 이름으로만 깨질 수 있다(E3b의 제외 대상). **v8 실측(5차 검토 S2, 부록 A F1v8 -- 근사 배정 모의 F2라 근사, 정확한 수는 D0b 배정 뒤)**: 8파일 중 F2 뒤 SD에 남지 않는 이름을 읽어 깨지는 것은 **2개** -- `.ai/verification/20260930-df36-instance-relpath/scripts/e_lib_inst.py`(`save_instance_json` → MOD9)와 `.ai/verification/20260930-p9-kcl-edges/scripts/diff_dup.py`(`_import_analog_grammar`·`_kcl_and_matching_edges`). 나머지 6개 `e_lib.py`는 `__file__`·`load_topology`·`run_topology_pipeline`만 읽고 둘 다 SD에 남아 깨지지 않는다(모의 F2·F1 트리에서 실제 실행해 해시도 같음, 부록 A F3v8). `probe_stage_partition.py`는 SR import에 더해 SD 경유 4이름(`_RAIL_NETS` 등)도 깨진다. **기준에 닿는 기본값**: 계획 534행 "추적 파일 전부 갱신"의 예외라 534행 개정 문안(`p3_doc_amendments.md` §2)에 넣고 승인 질문에 드러낸다(v6) | 기록 불변 |
| D-10 | 레지스트리 §7 `보류(Phase 3)` 9행은 **옮기고 D 유지**, 처리 열 `보류(Phase 4)` | U-02 승인 `20260923-u02-d-list` 1항 원문 "보류(Phase 3 모듈 이동·Phase 4 배선)" -- 두 몫이 이미 승인됐고 이동 몫은 D0b 뒤 이관 목적지 열 + `plan`·`check`가 넘겨받는다(보류 집합 불변 -- design 20 REG 판정식). U-02 '재검토'가 "승인표를 바꾸는 것은 사용자 승인 사항"이라 적으므로 처리 칸 9개 변경을 승인 질문 UD-0 문장에 원문 인용으로 드러낸다(v8.4, D0b 검토 m3) |
| D-11 | N3.10 표 개정: UD-0은 지금 계산 가능한 3건(A-3 -- `load_topology`·`validate_theta_declaration_order` → MOD3, `optimize_full_circuit_budget` Phase 3 위치 MOD8)과 D-19, **v8.4: A-1 충돌 보정 8건(토큰 11개)**(§6.2 'A-1 충돌' -- `p3_doc_amendments.md` §1 갱신·§9), **v8.5: 책임 보정 1건**(§9 (h) MOD9 `_kv_table` -- 계층 위반은 없으나 레지스트리 칸 `〃` 번짐으로 MOD4 책임과 맞지 않던 HTML 표 도우미, D0b 키트 D0b-8)만 덮는다(문안 `p3_doc_amendments.md` §1). D0b가 자기 base(B26-1·B34 병합 뒤)에서 그 밖의 개정이 필요하다고 계산하면 그 diff를 따로 사용자 승인(`target_kind: diff`) -- 위임하지 않는다(v6). v7: D0b의 `import_time_high` 발견을 배정 변경으로 풀 때도 같다 | §6.2, 3차 검토 B4 권고 (가)(메모리 원칙: 승인은 diff로) |
| D-12 | T0 = A군 3파일만, B군은 F1 | 최소 수정 |
| D-13 | G1은 B28 병합 뒤 base, 해시·이름 해석 정의는 `reachability` 하나 | §5.3, 정의 하나 |
| D-14 | references 문서의 모듈 위치 안내는 F2에서 grep 목록만 보고, 갱신은 B22 별도 card | B22가 이미 그 card |
| D-15 | M10은 red-green | §2.3 인벤토리 실측(이름 과대 근사뿐) |
| D-16 | M card는 `tools/**` 변경 0, 판정 도구는 `move_plan.py`를 마지막으로 바꾼 판정 기록의 `code_commit` 사본(지금은 D0a) | 작성자≠검증자(1차 검토 S9, 2차 검토 m6) |
| D-17 | §7.2 D군 probe·진단 스크립트(8파일, 대입 14줄): F1에서 덮어쓰기 대상을 `binding_origin`으로 찾은 호출자 모듈 전부로 바꾸고, F1 oracle에 그 대입 줄만 예외. 대안('Phase 3 뒤 동작하지 않는 probe'로 표시)은 사용자가 원할 때만. **기준에 닿는 기본값**(F1 oracle의 예외) -- 승인 질문에 드러낸다(v6) | probe 기능 보존 -- 삭제·범위 축소가 아니므로 원칙('결정은 원칙으로 기본안부터')상 기본안으로 정한다(2차 검토 §5, 초안 v3 UD-7 흡수). 다만 oracle 예외라 질문 문안에 명시(3차 검토 §7) |
| D-18 | redteam 번호(v5): G1 `32-moved-defs`, B33 `33-v7-registry-edges`, 면제 묶기 `34-v3-exempt-binding`, 범위 정책 `35-v3-changed-scope`(오케스트레이터 배정, 병합 순서 무관) | 네 게이트 card의 번호 충돌 방지(§5.3-5) |
| D-19 | **따로 묻는다(§9.2, v6)**. 기본안 (가): `rail_declaration`(B26-1)은 N3.10 MOD2 '대표 대상'에 더해 A-1로 MOD2. 대안 (나): 규칙대로 A-5로 MOD3(표 개정 없음). `RailDeclaration`은 어느 쪽이든 A-2로 MOD2. B37a 접근자는 결정을 따른다 | (가) MOD2 책임 '스키마·선언 게이트'(선언 형식 거부 함수와 같은 성격), B37a(미승인) `port_declaration`을 둘 예정인 곳과 한 곳 -- 근거를 이것으로 좁혔다(3차 검토 S4). 한계: `validate_theta_declaration_order`는 A-3로 MOD3라 선언 게이트는 어느 쪽이든 나뉜다(§6.4) |
| D-20 | 옮기며 바뀐 def·거부된 이동 후보의 V3 대상 = 새 경로의 새 def(본문 전체). 이동 원본과 문장 단위로 맞추지 않는다 | 범위 정책 약화 승인(A1-b)은 같은 경로의 기존 def만 덮는다, Phase 3는 옮기며 바꾸지 않는다(F2)(§5.5.2) |
| D-21 | G1은 V3 면제 대조(면제 묶기 card)를 바꾸지 않는다. 옮긴 def는 대상이 아니라 대조 없음, 거부 후보는 새 모듈 id라 옛 원소 미적용(fail-closed) | 변이 id 모듈 = 파일 줄기, 묶기 해시 = def 원본(§5.5.3) |
| D-22 | (v6) 재수출·import 줄 위치: split 파일 재수출은 import 머리 뒤, SD의 MOD 8·9 재수출은 SD 끝, MOD8·MOD9의 번호 7 이상 모듈 import는 파일 끝. M card·F1에 IMPORT-ANY(모듈마다 단독 첫 import 성공) 추가. M9~F1의 SD → MOD9 위쪽 import는 F2가 없앤다(LAYER는 F2 뒤 판정). **v7(4차 검토 S5)**: 이 배치의 전제(MOD8·MOD9의 import 시점 읽기 출처 < 7)를 D0b 계약 test가 `import_time_high` 0으로 단언한다. IMPORT-ANY는 시도 수 대조·목록 실패 INVALID(S2) | 모의 `p3v6_order_shim_sim`(§2.2): 머리 배치는 M9에서 순환 `ImportError`, 이 배치는 M1~M9 모두 성공(`a796468` 재실행 같음). 함수 안 지연 import 우회 금지(F3). 판정을 더하는 쪽(강화)이다 |
| D-23 | (v6) T0·D0a·D0b(`phase: 3`, v8.4: FU도)도 Phase 2 DoD PASS 뒤에 병합한다. 그 전에는 준비(초안·실측)만. v7: 확정 순서(§8.1)상 B26-1·B33 뒤라 이 조건은 자동으로 성립한다. v8.3: B34·b26pre·backfill·B26-1도 `phase: 3`(기록 `20261001-b26-phase3-cards`) -- 같은 조건이 걸리고 확정 순서상 자동 성립, design 30 승인은 기다리지 않는다(그 기록). Phase 3 DoD `^phase: 3$` 목록에 네 card가 더해진다(§9.1) | 계획 991행 "이전 Phase DoD PASS", Phase 순서 기본값(3차 검토 S2 (ii)). G1은 `phase: 0.5`라 해당 없음 |
| D-24 | (v6) E3 문자열 import는 텍스트 일치가 아니라 AST의 import 호출(`import_module`·`_import`·`__import__`의 첫 인자 문자열 상수)로 잰다. docstring·주석 언급은 import가 아니다. **한계(v7, 4차 검토 m5)**: 이름을 바꾼 호출(`from importlib import import_module as im; im("sizing_recipe")`), 하위 프로세스 문자열(`subprocess.run([…, "-c", "import sizing_recipe"])`), 변수 인자(`import_module(name)`), 문자열 조립(`"sizing_" + "recipe"`)은 잡지 못한다 -- `a796468` 추적 `.py` 실측(부록 A F5v7): 별칭 0, 하위 프로세스 문자열 0(문자열 안 `import sizing_recipe`는 전부 계약 test의 합성 소스 입력), 변수 인자 `import_module`은
`stick_diagram.py:1056`(analog-grammar 모듈)과 `test_restore_plan_functions.py:59`(`_import` 도우미 -- 호출부는 상수 인자라 E3가 `_import("sizing_recipe")`로 잡는다) 둘뿐이다. E3b(D-26)도 같은 한계를 갖고,
동적 이름(`getattr(sd, name)` -- 지금 0건)은 FAIL로 센다. **v8 한계 추가(5차 검토 m7)**: 경로로 로드한 엔진 모듈(`importlib.util.spec_from_file_location`·`runpy.run_path`로 엔진 파일을 직접 실행)도 잡지 못한다 -- `0f23786` 추적 `.py` 실측(부록 A F4v8): 그 호출이 엔진 4파일(SR·SD·TL·DR)을 로드하는 곳 0(로드 대상은 `run_harness.py` -- `test_df35_harness_paths.py:163`·`test_selftest_stick_diagram.py:488`, review 스크립트끼리 `review9_bias_dependent_net_scan.py`, `w_sites.py`, `runpy`로 자기 자신) | 3차 검토 S7: 텍스트 일치는 `test_d_move_tests.py:37` docstring을 잡아 거짓 FAIL. 호출 9곳은 그대로 잡힌다(§10 E3 실측) |
| D-25 | (v6, v8 정정) M10 진입점 test 회로 = **instance.json을 만드는 회로(= `20-dead-code-dup` §3 E-INST 회로 집합: 파일럿·`folded_cascode`) 중 E-INST 한 판이 가장 짧은 것 = `folded_cascode`**. instance.json을 만들지 않는 실패 경로 회로(`two_stage_ota`·`nmcnr_amplifier` -- v7 측정 `inst_sha: null`)는 후보가 아니고 §2.3 (ii)의 보조 회로로만 쓴다(5차 검토 S4: v7 문언 '네 library 회로 중 가장 짧은 것'은 문언대로면 instance.json을 만들지 않는 31~34초 회로를 뽑는다) | V3 비용(§2.3 -- 파일럿이면 9시간 이상, `--timeout` 위험), 판정 기준 불변. **v7 정정(4차 검토 S3)**: D-25는 새 진입점 test의 회로만 정한다(M10 equivalence의 E-INST 회로 집합은 `20-dead-code-dup` §3 그대로). 회로 하나·해시 대조만으로는 생존이 남는다(실측 50/71) -- 추가 test 모양은 §2.3 (i)~(iii) |
| D-26 | (v7, 4차 검토 N1) DoD에 **E3b**(SD-NAMES)를 더한다: F2 뒤 D-9 제외 집합 밖 추적 `.py`가 `stick_diagram`에서 읽는 이름이 모두 head SD에서 해석된다. 거부 확인 = base에서 'SD 밖으로 나간 이름'을 SD에서 읽는 추적 파일 > 0. F2 oracle에 E3b, F1 범위는 이름 단위(§7.2). 도구 오류·파싱 오류·star·동적 이름은 FAIL(**v8: base에 이미 있어도 FAIL** -- 5차 검토 B2, `pre_existing`은 실제 이름만). **한계(v8, 5차 검토 m2)**: E3b는 SD 최상위 바인딩을 `symtable`로 따로 센다(§2.4 '정의 하나'의 `reachability.SourceIndex`가 아니다 -- DoD는 G1 병합 뒤라 SourceIndex를 쓸 수 있지만, DoD 명령이 G1 코드의 동작에 기대지 않도록 독립 식으로 둔다). `symtable`은 `try/except ImportError` 안·`if TYPE_CHECKING:` 안의 바인딩도 '있음'으로 센다 -- SD에 그런 조건부 바인딩으로 남은 이름은 E3b가 해석된다고 본다. `0f23786` SD 실측: 최상위 `try`·`if` 문 0개(조건부 바인딩 없음). D-22 배치 규칙상 F2가 남기는 SD import도 무조건 import 줄이라 지금은 이 한계에 걸리는 이름이 없다. **한계(v8.1, 6차 검토 m-a -- v7부터 있던 식의 한계)**: E3b는 `stick_diagram` 모듈 객체를 이렇게 얻는 reader를 놓친다 -- (1) `sys.modules` 대입 별칭(`m = sys.modules['stick_diagram']; m.X`) (2) lambda가 돌려주는 모듈(`get = lambda: importlib.import_module('stick_diagram'); get().X`) (3) 이름을 바꾼 `import_module`(`from importlib import import_module as im; im('stick_diagram').X` -- D-24의 E3 한계와 같은 모양). 검토자 합성(9 reader)에서 6 탐지·이 3 놓침. `0f23786` 추적 `.py` 노출: `sys.modules[…stick_diagram…]`·`import_module as`·`from importlib import import_module` 0건 | 계획 534행 '추적 파일 갱신 후 삭제'가 SD 재수출 경로에서는 판정되지 않았다 -- V1 밖 SD 이름 reader가 많다(§2.2, 부록 A F1v7). 판정을 더하는 쪽(강화) |
| D-27 | (v7, 4차 검토 S4; v8 범위 확대 -- 5차 검토 S6) **동결**: D0b 병합부터 F2 병합까지 엔진 파일(`A/*.py`, `workspaces/run_harness.py`), `tools/gates/**`·`tools/migrate/**`, 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`)의 '이관 목적지' 열을 바꾸는 Phase 3 밖 card는 병합하지 않는다(엔진·목적지 열이면 병합 뒤 D0b 재계산, N3.10 밖 개정은 D-11). 사후 강제 = DoD E6(M1~F2 엔진 단위)·E2 앞 `tools` diff 확인·E4 `reg_mismatch`; D0b~M1 base 구간은 덮지 않는다(§9.1). B26-2~B26-4는 확정 순서에 없으므로 F2 뒤(앞당기려면 D0b 전, §9.1 재측정 (1)에 포함), B35는 착수 조건상 F2 뒤 | 이관표·레지스트리 열이 D0b 한 벌에 묶인다(§6.4). A2 '재검토'와 같은 편집 범위 문제를 M card 사이에서 막는다. DoD E2가 card 판정 때와 같은 게이트·`move_plan` 사본으로 재판정한다(§10 `GC`·`MPC`) |
| D-28 | (v8, 5차 검토 S1) **Phase 3 E-INST 측정 스크립트 = `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`**(이 design 커밋에 함께 넣는다 -- 문안 `_drafts/p3_scripts/e_inst_p3_proposed/e_inst_p3.py`). `e_inst_df36.py`와 엔진 출처 확인 한 곳만 다르다(고정 모듈 이름 셋의 `sys.modules` 항목 대신, 실행 뒤 `skills/analog-gmid-design/assets` 디렉터리에서 로드된 모듈 전부가 `<root>` 안이고 하나 이상). M1~M10·F1·F2 card의 equivalence E-INST와 DoD E5가 모두 이 한 사본을 쓴다(정의 하나). 동등은 DoD E5 (i)이 P2D(F1 전 판)에서 먼저 잰다(다르면 INVALID). **E-LIB(v8.2)**: M card equivalence는 `e_lib.py` 사본 그대로(card base와 병합본이 모두 B26-1 뒤라 뺄 키가 없다), DoD E5는 같은 design 커밋에 넣는 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_lib_p3.py`(문안 `_drafts/p3_scripts/e_lib_p3_proposed/e_lib_p3.py`) -- `e_lib.py`와 한 곳만 다르다(인자로 받은 meta 키를 `load` 값 정규화 전에 빼고 그 값을 `circuits.<회로>.masked`에 따로 싣는다; 키를 주지 않으면 `hash`와 나머지 출력이 `e_lib.py`와 같다 -- 동등은 E5 (i)이 P2D에서 먼저 잰다, 실측 부록 A F2v82). E5 비교 판 = **P2D**(Phase 2 DoD 측정 기록 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md`의 '대상' 커밋) -- **v8.2: UD-0 (c)의 기본안을 선례 모양으로 옮겼다**(아래 (e)), B0 비교는 대안. **출처 확인 범위(v8.1, 6차 검토 m-b)**: '한 곳만 다르다'의 그 한 곳은 df36보다 좁은 면이 있다 -- (1) `e_inst_p3.py`는 `__file__` 디렉터리가 `skills/analog-gmid-design/assets`로 끝나는 모듈만 보므로, 그런 경로가 아닌 곳(예: 캐시 디렉터리 사본)에서 로드된 엔진 모듈은 확인 없이 지나간다(df36은 이름 셋을 경로와 상관없이 확인했다) (2) 확인 시점이 `mod.run()` 전이라 run 안에서 처음 import되는 MOD는 보지 않는다(df36도 run 전 확인이지만 대상이 하네스 import 시점의 모듈 셋이었다). 판정 자체는 (ii)의 해시 대조가 하고 이 확인은 출처 보조라 실제 위험은 낮다. 확인을 run 뒤로 한 번 더 두는 보강은 스크립트 sha256과 동등 실측(부록 A F3v8)을 다시 재야 하므로 이 판에서는 범위 차이를 적는 것으로 둔다 | (a) F1이 하네스 import를 N3.10 모듈로 바꾸면 `e_inst_df36.py` 33~35행이 `KeyError: 'sizing_recipe'`(근사 F1 모의 실측, 부록 A F3v8) (b) df36은 D-9 제외 집합(판정 기록 증거)이라 고치지 않는다 (c) **위치**: 판정에 쓰는 측정 스크립트를 Phase 3 code 커밋보다 먼저, 사용자 승인 대상 diff(design 커밋)에 고정해 code-author가 판정 도구에 맞춰 쓸 수 없게 한다(작성자≠검증자, D-16과 같은 이유). `.ai/verification/**`은 판정 기록 증거 자리이고 아직 판정 기록이 없다. 이 design의 원자료 자리(머리 문장 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/`)와 같다. auditor는 사본 sha256를 판정 기록에 적는다 (d) **동등 근거**: `0f23786`에서 두 회로 모두 출력 JSON이 `engine_origin` 키 하나만 다르고(p3가 df36의 세 항목 + `topology_library`) stdout 사본이 같다(경과 시간 가림); 근사 F1 모의 트리에서 df36은 `KeyError`, p3는 instance.json `raw_sha256`·`without_topology_ref_sha256`가 base와 같다(부록 A F3v8) (e) **비교 판 P2D(v8.2, 선례 모양)**: P2D와 Phase 3 마지막 병합본 사이 card가 의도적으로 바꾸는 E-LIB·E-INST 필드를 그 card 초안의 계약에서 유도해, 그 필드만 빼고 계약값으로 따로 판정하고 나머지는 해시 같음을 요구한다(선례 `20260930-phase2-e4-baseline` 기본안 -- da03c0e와 Phase 2 마지막 병합본을 같은 경로에서 비교하고 `topology_ref`만 DF-36 계약값으로 판정; 사용자 "둘다 기본안으로 진행해"). 사이 card 중 면제 묶기(34)·범위 정책(35)·B33·G1·T0·D0a·D0b는 게이트·도구·test·레지스트리라 E-LIB·E-INST 입력이 아니고, Phase 3 card 자신은 동작을 바꾸지 않는 것이 E5의 판정 대상이다. **의도된 변경 목록**: ① B34(`draft_b34.final.spec.md` 계약 7): analog-grammar가 있으면 E-LIB 9/9·E-INST가 base와 같다 -- 빼는 필드 없음 ② b26pre: test-only, 엔진 무변경 -- 없음 ③ backfill(`draft_b26_backfill_audit.spec.md` 계약 1·2, 'library 회로 적용 여부'): 바뀌는 값은 `run_matching_safety_with_finger_growth` 반환 `relaxed_pairs[i]["interdig_ok"]`뿐이고 그 값은 `optimize_full_circuit_budget`의 `pipeline_result["relaxed_pairs"]`까지만 간다 -- `save_instance_json`(SD 8973)은 고정 키(`schema_version`·`topology_ref`·`sizing`·`netlist`·`floorplan`·`box_shape`·`audit_row_split`·`coverage`, 선택 `scope_note`)만 쓰고 report는 그 instance.json에서 만든다(`run_harness.py` 505행), E-LIB 함수(`load_topology`·`run_topology_pipeline`)는 이 def에 닿지 않는다. 실측(부록 A F1v82, `a796468`, SPECS 4회로): 파일럿은 `relaxed_pairs` 2쌍(`M4a/M4b` `interdig_ok` True, `M3a/M3b` False)이 `save_instance_json`에 넘어가지만 instance.json·report.html·stdout에서 `relaxed`·`interdig_ok` 문자열 0(있는 `interdigitation`은 audit 3b 체크 이름), `folded_cascode`는 `relaxed_pairs` 빈 목록, `two_stage_ota`·`nmcnr_amplifier`는 이 def 전에 멈춘다 -- 빼는 필드 없음 ④ B26-1(`draft_b26_1.spec.md` 계약 2·8): `load_topology` `meta`에 새 키 `"rails"` -- E-LIB `load` 값에서 그 키만 빼고(`e_lib_p3.py` 인자 `rails`) 계약값 `RailDeclaration(nets = 그 회로 topology의 supply_nets)`(계약 1)로 따로 판정한다; `meta`의 다른 키·`transistors`, `run_topology_pipeline` 반환(`transistors`·`box_shape`·`audit_row_split`·`floorplan`·`coverage` -- meta를 담지 않는다), instance.json은 같아야 한다(계약 8). 실측(부록 A F2v82·F3v82, `a796468` + 계약 1·2 모양 시제품): 원래 `e_lib.py` 해시는 9회로 모두 `load`만 달라(V1·V2 같음) raw 비교는 성립하지 않고, `rails`를 뺀 해시는 base와 같고 계약 판정 PASS, E-INST 두 회로 해시 base와 같음 ⑤ **FU(v8.4, §6.5 D-29)**: DR·ACF 머리에 `from __future__ import annotations` 한 줄 -- 실측(부록 A F2v84, `5f643a9`): `e_lib.py` 해시 같음, `e_inst_p3.py` 파일럿·`folded_cascode` 출력 22키 모두 같음 -- 빼는 필드 없음(그래서 §10 E5 상수는 바뀌지 않는다). **결론: E-INST 빼는 키 = 없음, E-LIB 빼는 키 = `meta["rails"]` 하나** -- §10 E5 판정 python의 `EXCL_INST`·`MASK_META` 상수가 이 목록이다. 사이 card의 계약이 바뀌면(재작성·새 엔진 card) 이 목록과 상수를 고치는 design 개정(승인 대상 diff)이 필요하다 -- 목록은 판정 기준이라 auditor가 늘리지 않는다. **계약값 판정(v8.3, 7차 검토 S1·m1)**: HEAD `masked.rails`는 `{"__dc__": "RailDeclaration", "nets": <P2D library의 그 회로 `supply_nets` 정렬 집합>}`와 **정확히 같아야** 한다 -- 계약 1은 필드 `nets` 하나짜리 값 전체이므로 계약 밖 필드(예: 극성)가 끼면 FAIL이고(B26-2가 극성 필드를 더하는 것은 F2 뒤 기본값이라 이 창 밖 -- 앞당기면 이 목록·상수를 고치는 design 개정), 계약값은 비교 시작 판의 선언이다(P2D와 HEAD 사이에 library `supply_nets`가 바뀌면 FAIL -- HEAD에서 읽으면 같은 값이 양쪽에 들어가 걸리지 않는다). **A2-③ 답(v8.3 결정)**: 사용자 답 'phase 3 + 정정 기록'(기록 `20261001-b26-phase3-cards`)으로 네 card는 P2D 뒤에 오므로 기본안에서 P2D `masked.rails`는 `<ABSENT>`이다. 판정 python이 'P2D = HEAD와 같은 값'도 받는 것은 대안 (c-2)(B0 판에는 이미 `rails`가 있다) 때문이고, (나) 분기는 없어졌다. **대안(c-2) = B0 비교**: 같은 블록의 `P2D=`에 B0(M1 판정 기록 `base_commit`)를 넣는다 -- B0에 이미 `rails`가 있어 빼는 필드와 계약값 판정은 두 판에서 같은 값을 보고, Phase 2 DoD 판과의 연결은 B34·b26pre·backfill·B26-1 판정 기록이 잇는다. v8.1까지 기본안이던 이 모양은 선례에서 고르지 않은 대안('card별 판정 기록 사슬로 갈음')과 같다. §10 E5 행 |
| D-29 | (v8.4, G1 착수 키트 0.2) **`__future__` 혼합은 준비 card FU로 푼다**: D0b 전에 `design_report.py`·`audit_current_forced.py` 머리에 `from __future__ import annotations` 한 줄씩(equivalence). (가) M card V3 판정·(다) 배정 변경은 기각(§6.5 표) | 동작 불변 실측(§6.5 -- 몸체 코드 객체 17개 동일, 전체 test·E-LIB·E-INST 동일, V3 변이 0), M card 기준 불변, card당 한 책임. 승인된 기준을 바꾸지 않아 UD-0 범위(card 수 16 → 17은 질문 본문에 사실로) |
| D-30 | (v8.4, G1 착수 키트 0.2 'multi') **MOD 파일 import 머리 = `plan` `mod_imports`(이름마다 import 한 번)**, 갈리면 `import_conflicts`(D0b 계약 test가 FAIL로 잡음), M card `check` `import-dup` | 원본 import 줄을 모아 붙이면 같은 이름이 두 번 묶여 G1 `binding_origin` = `multi` → M-4 거부·연쇄 거부(모의 raw M1 2·M2 6·M3 29·M6 4·M9 16 → dedup 0, 부록 A F3v84). 정의 하나(G1 `binding_origin`에서 생성), 만들면 배선(D0b·M card) |
| D-31 | (v8.4, D0b 착수 키트 D0b-1·2) **배정 규칙 보강**: 모듈 docstring 제외, A-K, 승격(A-2·A-4·A-5·A-6, MOD7 상한), A-6, A-7, 단조 고정점(§6.2). **기준에 닿는다** -- 승격은 계획 517행 "레지스트리 '이관 목적지' 열이 정본"을 '칸 MOD는 하한'으로 읽는다(같은 줄의 "import는 작은 번호 쪽으로만"을 앞세움; 시제품 관찰 32단위가 칸과 달라짐, D0b가 열을 도구 출력으로 다시 써서 열 = 이관표 회복) -- 승인 질문 UD-0 본문에 사실로 적는다 | 지금 규칙은 `upward` 34·`cycles` 1·`unassigned` 18(D0b 키트) -- 규칙 보강 + A-1 충돌 보정 8건(토큰 11개, D-11)으로 0·0·0(부록 A F4v84). 대안(32단위를 N3.10 토큰으로 하나씩): 계획서에 단위 이름이 쌓이고 그 토큰 역시 칸을 덮어쓴다(A-1 > A-4) -- 정본성 변경은 어느 쪽이든 생기므로 규칙 하나로(정의 하나) |

---

## 10. DoD 측정 명령 (N9.2-6)

auditor가 Phase 3 마지막 card 병합본의 격리 복제본 `<iso>`에서 **bash**로 실행한다. **`PT3`** = `10-test-separation` §10 `PT` 정의에서 `--gmid-phase=1`만 `--gmid-phase=3`으로 바꾼 것이다
(v8 -- 5차 검토 B1: v7은 `PT`를 그대로 써서 Phase 1 DoD용 `--gmid-phase=1`로 돌았다. `tests/conftest.py`는 표식 Phase가 현재 Phase보다 뒤인 케이스를 `xfail(strict=False)`로 바꾸고,
`--gmid-dod` 없이는 현재 Phase 케이스도 `--gmid-strict` 밖이면 xfail이라 phase 2·3 표식 케이스가 실패해도 지나간다. 선례: Phase 2 DoD의 같은 결함을 승인 `20260930-phase2-e4-phase`가
`PT2` 실행 + `PT2 --gmid-dod` 실행으로 고쳤다 -- 이 design은 같은 모양을 처음부터 쓴다. 기준을 더하는 쪽이다). Phase 3 DoD의 pytest 실행은 전부 `PT3`이고, 전체 실행은 `PT3`와 `PT3 --gmid-dod` 두 번이다(E4·E5).
**v6(3차 검토 B3)**: 명령은 아래 bash 블록이 정본이다 -- 표 칸 안 명령은 정규식 `|`가 `\|`로 적혀 원문 그대로 실행하면 `git grep -E`에서 문자 `|`가 되어 **아무것도 찾지 못했다**
(실측 `7535799`: 줄 머리 식 원문 0파일 대 `|` 57파일, 문자열 식 원문 0 대 6파일). 표에는 ID와 통과 기준만 둔다. E3에는 **거부 확인**(같은 식이 Phase 3 전 base에서 빈 결과가 아님)을 둔다.

```bash
# ---- 공통 (값은 auditor가 판정 기록에서 채운다) ----
ISO=<iso>; S=<auditor 스크래치>; PY="C:/Python314/python.exe -B"
export APPDATA="C:/Users/HSLEE/AppData/Roaming" HOME="C:/Users/HSLEE"   # v8(5차 검토 m3): 하위 bash에서 APPDATA가 비면 사용자 site의 numpy를 못 찾아 import_any가 거짓 FAIL
GC="$ISO/tools/gates"     # 05 §4.4: 판정은 gate master 판 게이트 코드. M card는 tools/** 변경 0(D-16)이고 D0b~F2에는 Phase 3 밖 card도 tools/gates·tools/migrate를
                          # 바꾸지 않는다(D-27, v8 -- 5차 검토 S6) -- 그래서 마지막 병합본의 tools/gates = 각 card 판정 때의 판. 아래 E2 앞에서 그 전제를 확인한다
                          # (05 §4.4 캐시 <git-common-dir>/gmid-gate-cache/<그 커밋>/를 쓰면 GC를 그 안의 tools/gates로)
PT3() {   # 10 §10 PT에서 --gmid-phase=1만 =3으로(v8 -- 5차 검토 B1). <cache> = 05 §4.4 캐시.
          # 첫 인자가 $ISO 아래 경로면 그것이 test 경로(10 §10 D4의 `PT <파일>` 용법), 아니면 tests 전체. 나머지 인자는 pytest 옵션
  local t="$ISO/skills/analog-gmid-design/assets/tests"
  case "${1:-}" in "$ISO"/*) t="$1"; shift;; esac
  PYTHONPATH="<cache>" PYTHONPYCACHEPREFIX="$(mktemp -d)" C:/Python314/python.exe -P -m pytest -c "<cache>/pytest_gate.ini" --rootdir="$ISO" --confcutdir="$ISO"     "$t" --gmid-phase=3 "$@"
}
MPC=<tools/migrate/move_plan.py를 마지막으로 바꾼 판정 기록의 code_commit>     # 지금은 D0a(2차 검토 m6)
git -C "$ISO" show "$MPC:tools/migrate/move_plan.py" > "$S/move_plan.py"
MP_ARGS=(--plan docs/01-plan/features/gain-budget-gmid-sizing.plan.md
         --registry docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
         --split sizing_recipe.py stick_diagram.py topology_library.py design_report.py audit_current_forced.py
         --keep audit_current_forced.py
         --aliases '{"optimizer": "theta_search.py"}')                         # §6.3 그대로
B0=<M1 판정 기록 base_commit>                                                   # Phase 3 이동 전 base(D0b 병합 뒤)
# $S/cards.txt: 한 줄에 "<base_commit> <code_commit> <MOD 파일> <V1의 --gmid-strict= 값>" -- M1~M6·M8·M9 판정 기록에서

# ---- E0·E1 ----
$PY "$GC/import_layering.py" --root "$ISO" > "$S/layer.json"; echo "E0/E1 exit=$?"

# ---- E2: 이동 card마다 V3 재실행 + check ----
git -C "$ISO" diff --quiet "$B0" HEAD -- tools/gates tools/migrate   || echo "E2 INVALID: M1 base 뒤 tools/gates·tools/migrate 변경(D-27 위반) -- GC가 card 판정 때의 게이트가 아니다"   # v8(5차 검토 S6)
while read -r b h m strict; do
  $PY "$GC/mutate_changed.py" --root "$ISO" --base "$b" --head "$h" --pytest-ini "$GC/pytest_gate.ini" \
      --python C:/Python314/python.exe --gmid-phase=3 --gmid-strict="$strict" > "$S/v3_$m.json"; echo "E2 V3 $m exit=$?"
  $PY "$S/move_plan.py" check --root "$ISO" --base "$b" --head "$h" --card "$m" "${MP_ARGS[@]}" > "$S/chk_$m.json"; echo "E2 check $m exit=$?"
done < "$S/cards.txt"

# ---- E3: shim 삭제(v7: fail-closed -- 4차 검토 S1) ----
for f in sizing_recipe topology_library design_report; do            # 세 shim 파일 부재(4차 검토 m4 -- E4 absent_split과 같은 사실을 여기서도 직접 본다)
  git -C "$ISO" cat-file -e "HEAD:skills/analog-gmid-design/assets/$f.py" 2>/dev/null && echo "E3 FAIL: $f.py 있음"
done
EXCL='^(\.ai/verification/|docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition\.py$)'   # D-9
E3_AST=$(cat <<'PYEOF'
import ast, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
iso, rev = sys.argv[1], sys.argv[2]
mods = {"sizing_recipe", "topology_library", "design_report"}
G = ["git", "-c", "core.quotepath=off", "-C", iso]
r = subprocess.run(G + ["grep", "-z", "-l", "-E", "sizing_recipe|topology_library|design_report", rev, "--", "*.py"],
                   capture_output=True)
if r.returncode not in (0, 1):
    sys.exit("git grep failed: " + r.stderr.decode("utf-8", "replace"))
bad = 0
for ent in r.stdout.decode("utf-8").split("\0"):
    if not ent:
        continue
    if not ent.startswith(rev + ":"):
        sys.exit("unexpected git grep entry: " + ent)
    p = ent[len(rev) + 1:]
    s = subprocess.run(G + ["show", rev + ":" + p], capture_output=True)
    if s.returncode != 0:
        print("ERROR " + p); bad += 1
        continue
    try:
        tree = ast.parse(s.stdout)
    except SyntaxError:
        print("PARSE-ERROR " + p)
        continue
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] in mods for a in n.names):
            print("stmt %s:%d" % (p, n.lineno))
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module and n.module.split(".")[0] in mods:
            print("stmt %s:%d" % (p, n.lineno))
        elif isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Constant) \
                and isinstance(n.args[0].value, str):
            f = n.func
            fn = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if fn in ("import_module", "_import", "__import__") and n.args[0].value.split(".")[0] in mods:
                print("call %s:%d" % (p, n.lineno))
sys.exit(3 if bad else 0)
PYEOF
)
e3_run() {   # $1 = rev, $2 = 출력 파일. 파이썬이 0이 아니게 끝나면(git 실패·ERROR 줄) 도구 오류 = FAIL
  $PY -c "$E3_AST" "$ISO" "$1" | tr -d '\r' > "$2"; local rc=${PIPESTATUS[0]}
  [ "$rc" -eq 0 ] || echo "E3 FAIL(도구 오류 rc=$rc rev=$1)"
  return "$rc"
}
# 거부 확인(먼저): 같은 식이 Phase 3 전 base에서 import 문장과 import 호출을 둘 다 찾아야 명령이 살아 있다
e3_run "$B0" "$S/e3_b0.txt" && { [ "$(grep -c '^stmt ' "$S/e3_b0.txt")" -gt 0 ] && [ "$(grep -c '^call ' "$S/e3_b0.txt")" -gt 0 ] \
  || echo "E3 INVALID: base에서 빈 결과(명령 고장)"; }
# 판정: 마지막 병합본에서 제외 집합 밖 파일 0 (PARSE-ERROR 줄도 밖으로 센다 -- fail-closed)
e3_run HEAD "$S/e3_head.txt" && { OUT=$(sed 's/^[A-Za-z-]* //; s/:[0-9]*$//' "$S/e3_head.txt" | sort -u | grep -v -E "$EXCL")
  [ -z "$OUT" ] && echo "E3 PASS" || { echo "E3 FAIL:"; echo "$OUT"; }; }

# ---- E3b: stick_diagram에서 읽는 이름이 head SD에서 해석된다(v7 -- 4차 검토 N1) ----
E3B_AST=$(cat <<'PYEOF'
import ast, re, subprocess, symtable, sys
sys.stdout.reconfigure(encoding="utf-8")
iso, b0, head, excl = sys.argv[1:5]
SD = "skills/analog-gmid-design/assets/stick_diagram.py"
IMPL = {"__file__", "__name__", "__doc__", "__dict__", "__spec__", "__loader__", "__package__", "__builtins__", "__cached__"}
IMPF = ("import_module", "_import", "__import__")
ATTRF = ("getattr", "hasattr", "setattr", "delattr")
G = ["git", "-c", "core.quotepath=off", "-C", iso]
errs = []

def show(rev, p):
    s = subprocess.run(G + ["show", rev + ":" + p], capture_output=True)
    if s.returncode != 0:
        errs.append("ERROR show %s:%s" % (rev, p))
        return None
    return s.stdout

def sd_names(rev):   # SD 최상위 바인딩: (정의 = def·class·대입, 가져옴 = import)
    src = show(rev, SD)
    if src is None:
        return set(), set()
    defs, imps = set(), set()
    for s in symtable.symtable(src.decode("utf-8"), SD, "exec").get_symbols():
        if s.is_imported():
            imps.add(s.get_name())
        elif s.is_assigned() or s.is_namespace():
            defs.add(s.get_name())
    if "__getattr__" in defs | imps:
        errs.append("ERROR SD에 모듈 __getattr__ (%s) -- 이름 해석을 정적으로 판정할 수 없다" % rev)
    return defs, imps

def file_reads(tree):   # SD 모듈 식(별칭·import_module 결과·그것을 돌려주는 함수 호출)에서 읽는 이름
    al, fn_sd = set(), set()
    def is_sd(e):
        if isinstance(e, ast.Name):
            return e.id in al
        if isinstance(e, ast.Call):
            f = e.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if nm in IMPF and e.args and isinstance(e.args[0], ast.Constant) and e.args[0].value == "stick_diagram":
                return True
            return isinstance(f, ast.Name) and f.id in fn_sd
        return False
    ch = True
    while ch:
        ch = False
        for n in ast.walk(tree):
            new = set()
            if isinstance(n, ast.Import):
                new = {a.asname or a.name for a in n.names if a.name == "stick_diagram"}
            elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.NamedExpr)) and n.value is not None and is_sd(n.value):
                tg = n.targets if isinstance(n, ast.Assign) else [n.target]
                new = {t.id for t in tg if isinstance(t, ast.Name)}
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name not in fn_sd and any(
                    isinstance(r, ast.Return) and r.value is not None and is_sd(r.value) for r in ast.walk(n)):
                fn_sd.add(n.name); ch = True
            if new - al:
                al |= new; ch = True
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module == "stick_diagram":
            out |= {(n.lineno, a.name) for a in n.names}          # "*"는 해석 불가 이름으로 FAIL
        elif isinstance(n, ast.Attribute) and is_sd(n.value):
            out.add((n.lineno, n.attr))
        elif isinstance(n, ast.Call) and n.args and is_sd(n.args[0]) and (
                (n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", "")) in ATTRF):
            a = n.args[1] if len(n.args) > 1 else None
            out.add((n.lineno, a.value if isinstance(a, ast.Constant) and isinstance(a.value, str) else "<동적 이름>"))
    return out

def reads(rev):   # {경로: {(줄, 이름)}} -- 제외 집합(D-9)과 SD 자신 밖의 추적 .py
    r = subprocess.run(G + ["grep", "-z", "-l", "-F", "stick_diagram", rev, "--", "*.py"], capture_output=True)
    if r.returncode not in (0, 1):
        errs.append("ERROR git grep %s rc=%d" % (rev, r.returncode))
        return {}
    res = {}
    for ent in r.stdout.decode("utf-8").split("\0"):
        if not ent:
            continue
        if not ent.startswith(rev + ":"):
            errs.append("ERROR git grep 항목 " + ent)
            continue
        p = ent[len(rev) + 1:]
        if p == SD or re.search(excl, p):
            continue
        src = show(rev, p)
        if src is None:
            continue
        try:
            res[p] = file_reads(ast.parse(src))
        except SyntaxError:
            res[p] = {(0, "<PARSE-ERROR>")}
    return res

hd, hi = sd_names(head)
bd, bi = sd_names(b0)
hr, br = reads(head), reads(b0)
MARK = lambda n: n == "*" or n.startswith("<")   # 표지 이름: star import·"<동적 이름>"·"<PARSE-ERROR>"(v8 -- 5차 검토 B2)
pre = {(p, n) for p, s in br.items() for _, n in s
       if not MARK(n) and n not in bd | bi | IMPL}  # base에서 이미 안 풀리던 실제 이름만. 표지는 base에 있어도 면제하지 않는다(head에서 FAIL)
moved_out = bd - hd                                                                    # base SD 정의 중 head SD에 정의가 없는 이름
live = sorted(p for p, s in br.items() if any(n in moved_out for _, n in s))
print("E3b LIVE moved_out=%d base_files_reading_moved_out=%d pre_existing=%d" % (len(moved_out), len(live), len(pre)))
fails = sorted("%s:%d %s" % (p, ln, n) for p, s in hr.items() for ln, n in s
               if n not in hd | hi | IMPL and (p, n) not in pre)
for e in errs:
    print(e)
for f in fails:
    print("E3b FAIL " + f)
if not moved_out or not live:
    print("E3b INVALID: base에서 SD 밖으로 나간 이름을 읽는 추적 파일 0(명령 고장 또는 base 오지정)")
elif not errs and not fails:
    print("E3b PASS")
sys.exit(3 if errs else 0)
PYEOF
)
$PY -c "$E3B_AST" "$ISO" "$B0" HEAD "$EXCL" | tr -d '\r' > "$S/e3b.txt"; rc=${PIPESTATUS[0]}
cat "$S/e3b.txt"; [ "$rc" -eq 0 ] || echo "E3b FAIL(도구 오류 rc=$rc)"

# ---- E4 ----
PT3 "$ISO/skills/analog-gmid-design/assets/tests/contracts/test_p3_registry_dest.py"; echo "E4 test exit=$?"   # v8: PT → PT3(5차 검토 B1)
$PY "$S/move_plan.py" plan --root "$ISO" "${MP_ARGS[@]}" > "$S/plan_final.json"; echo "E4 plan exit=$?"

# ---- IMPORT-ANY(E5 앞, M card·F1에서도 같은 함수 -- v7: 목록 계산 실패·빈 목록 = INVALID, 시도 수 대조, 4차 검토 S2) ----
import_any() {   # $1 = 체크아웃된 트리 루트. N3.10 파일과 --split 파일 중 있는 것을 각각 새 프로세스에서 맨 처음 import
  local A="$1/skills/analog-gmid-design/assets" m mods split exp n_try=0 n_fail=0
  mods=$($PY -c 'import sys; sys.path.insert(0, sys.argv[1]); import import_layering as il; print(" ".join(il.mod_table(open(sys.argv[2], encoding="utf-8").read())))' \
         "$GC" "$1/docs/01-plan/features/gain-budget-gmid-sizing.plan.md") || { echo "IMPORT-ANY INVALID: 모듈 목록 계산 실패"; return 2; }
  mods=$(printf '%s' "$mods" | tr -d '\r')
  split=$(printf '%s\n' "${MP_ARGS[@]}" | sed -n '/^--split$/,/^--keep$/p' | grep '\.py$' | sed 's/\.py$//')
  [ -n "$mods" ] && [ -n "$split" ] || { echo "IMPORT-ANY INVALID: 모듈 목록이 비었다"; return 2; }
  # 기대 수(독립 계산): import_layering의 present(N3.10 중 있는 파일) ∪ 트리에 있는 --split 파일
  local pres; pres=$($PY "$GC/import_layering.py" --root "$1" | $PY -c 'import json,sys; print("\n".join(json.load(sys.stdin)["present"]))') \
    || { echo "IMPORT-ANY INVALID: import_layering present 계산 실패"; return 2; }
  exp=$( { printf '%s\n' "$pres"; for m in $split; do [ -f "$A/$m.py" ] && echo "$m"; done; } | tr -d '\r' | sort -u | grep -c .)
  for m in $(printf '%s\n' $mods $split | sort -u); do
    [ -f "$A/$m.py" ] || continue
    n_try=$((n_try + 1))
    ( cd "$A" && $PY -c "import $m" ) > /dev/null 2>&1 || { echo "IMPORT-ANY FAIL: $m"; n_fail=$((n_fail + 1)); }
  done
  echo "IMPORT-ANY tried=$n_try expected=$exp failed=$n_fail"
  [ "$n_try" -gt 0 ] && [ "$n_try" -eq "$exp" ] || { echo "IMPORT-ANY INVALID: 시도 수 $n_try ≠ 기대 수 $exp"; return 2; }
  [ "$n_fail" -eq 0 ]
}
import_any "$ISO"

# ---- E5: 동작 보존(v8.2 -- UD-0 (c) 기본안 = 선례 모양, D-28) ----
PT3;              echo "E5 PT3 exit=$?"          # 전체(수집 1개 이상, 실패 0)
PT3 --gmid-dod;   echo "E5 PT3-dod exit=$?"      # 전체, DoD 모드(실패 0)
# E-LIB·E-INST: P2D(Phase 2 DoD 측정 기록 docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md의 '대상' 커밋)와 이 병합본(HEAD)을 같은 <iso>에서 차례로 떠 같은 사본으로 잰다
# (design 20 §10 E4 절차 선례, 승인 20260930-phase2-e4-baseline). 사이 card가 의도적으로 바꾼 필드(D-28 (e) 목록 = 아래 판정 python의 EXCL_INST·MASK_META)만 빼고 그 card 계약값으로 따로 판정한다.
# 대안(c-2)을 고르면 P2D 자리에 B0(M1 판정 기록 base_commit)를 넣는다 -- 나머지 명령·판정 python 그대로.
# 스크립트는 판을 바꾸기 전에 <iso> 밖 X로 복사하고(sha256 기록) 두 판에 같은 사본을 쓴다. 출력 O도 <iso> 밖(clean -fdx가 지운다).
P2D=<phase2-dod.md '대상' 커밋>; H=$(git -C "$ISO" rev-parse HEAD); X=<iso 밖 임시 경로>; O=<iso 밖 출력 경로>
git -C "$ISO" show "$H:docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py" > "$X/e_inst_p3.py"
git -C "$ISO" show "$H:docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_lib_p3.py"  > "$X/e_lib_p3.py"
git -C "$ISO" show "$P2D:.ai/verification/20260930-df36-instance-relpath/scripts/e_inst_df36.py"     > "$X/e_inst_df36.py"
git -C "$ISO" show "$P2D:.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py"          > "$X/e_lib.py"
sha256sum "$X"/e_inst_p3.py "$X"/e_lib_p3.py "$X"/e_inst_df36.py "$X"/e_lib.py > "$O/scripts.sha256"
fresh() { git -C "$ISO" checkout -q --detach "$1" && git -C "$ISO" checkout -q -- . && git -C "$ISO" clean -q -fdx; }
for c in current_reuse_telescopic_ota folded_cascode; do                      # E-INST 회로 집합(20 §3)
  fresh "$P2D"; $PY -P "$X/e_inst_df36.py" "$ISO" "$c" "$O/p2d_df36_$c.json"; echo "E5 p2d df36 $c exit=$?"   # 동등 확인용(F1 전 판)
  fresh "$P2D"; $PY -P "$X/e_inst_p3.py"   "$ISO" "$c" "$O/p2d_p3_$c.json";   echo "E5 p2d p3 $c exit=$?"
  fresh "$H";   $PY -P "$X/e_inst_p3.py"   "$ISO" "$c" "$O/h_p3_$c.json";     echo "E5 head p3 $c exit=$?"
done
fresh "$P2D"
$PY -P "$X/e_lib.py"    "$ISO" "$O/p2d_elib.json";              echo "E5 p2d elib exit=$?"          # 동등 확인용
$PY -P "$X/e_lib_p3.py" "$ISO" "$O/p2d_elibp3_nomask.json";     echo "E5 p2d elibp3 nomask exit=$?" # 동등 확인용(빼는 키 없음)
$PY -P "$X/e_lib_p3.py" "$ISO" "$O/p2d_elibp3.json" rails;      echo "E5 p2d elibp3 exit=$?"        # rails = MASK_META(D-28 (e))
fresh "$H"
$PY -P "$X/e_lib_p3.py" "$ISO" "$O/h_elibp3.json" rails;        echo "E5 head elibp3 exit=$?"
$PY - "$O" "$ISO" "$P2D" <<'PYEOF'
import hashlib, json, os, re, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
O, ISO, P2D = sys.argv[1], sys.argv[2], sys.argv[3]   # O = 출력 경로(<iso> 밖), ISO = <iso>(git), P2D = 비교 시작 판 -- 계약값의 supply_nets를 P2D library에서 git show로 읽는다(v8.3, 7차 검토 m1)
ld = lambda n: json.load(open(os.path.join(O, n), encoding="utf-8")) if os.path.exists(os.path.join(O, n)) else None
# stdout 사본 비교는 SLSQP 진행 줄의 경과 시간 `elapsed=<초>s`만 가린다(파일럿 stdout은 경과 시간을 찍는다 -- v8 실측, 부록 A F3v8)
fh = lambda n: hashlib.sha256(re.sub(rb"elapsed=[0-9.]+s", b"elapsed=<T>s", open(os.path.join(O, n), "rb").read())).hexdigest() if os.path.exists(os.path.join(O, n)) else None
# 의도된 변경 목록(v8.2, D-28 (e) -- 사이 card 계약에서 유도, 실측 부록 A F1v82~F3v82):
#   E-INST instance.json 최상위 키: 없음(B34 계약 7·B26-1 계약 8 = instance.json 같음, b26pre = test-only,
#     backfill의 relaxed_pairs[i]["interdig_ok"]는 pipeline_result에만 있고 save_instance_json이 쓰지 않는다)
#   E-LIB: load_topology meta 키 "rails"(B26-1 계약 2·8) -- 해시에서 빼고(e_lib_p3.py 인자) 계약값 RailDeclaration(nets = 그 회로 supply_nets)로 따로 판정
EXCL_INST = ()
MASK_META = ("rails",)
bad = []
for c in ("current_reuse_telescopic_ota", "folded_cascode"):
    d, p, h = ld("p2d_df36_%s.json" % c), ld("p2d_p3_%s.json" % c), ld("h_p3_%s.json" % c)
    if d is None or p is None:
        print("E5 INVALID: P2D E-INST 출력 없음 %s" % c); bad.append(c); continue
    # 동등 확인(먼저): F1 전 판(P2D)에서 e_inst_p3 = e_inst_df36 (engine_origin 키 하나만 다르고 df36의 항목을 포함, stdout 사본 같음)
    diff = sorted(k for k in set(d) | set(p) if d.get(k) != p.get(k))
    sub = all(p["engine_origin"].get(k) == v for k, v in d["engine_origin"].items())
    if diff != ["engine_origin"] or not sub or fh("p2d_df36_%s.json.stdout.txt" % c) != fh("p2d_p3_%s.json.stdout.txt" % c):
        print("E5 INVALID: e_inst_p3 ≠ e_inst_df36 on P2D %s (다른 키 %s, 포함 %s)" % (c, diff, sub)); bad.append(c); continue
    strip = lambda r: {k: v for k, v in r["field_sha256"].items() if k not in EXCL_INST}
    ok = (h is not None and h["exists"] and not h["fail_in_stdout"] and h["path_string_hits"] == []
          and h["topology_ref_equals_expected_contract1"] and p["topology_ref_equals_expected_contract1"]
          and strip(h) == strip(p) and (EXCL_INST or (h["raw_sha256"] == p["raw_sha256"]
                                                      and h["without_topology_ref_sha256"] == p["without_topology_ref_sha256"])))
    print("E5 E-INST %s %s" % (c, "같음" if ok else "다름/실패")); ok or bad.append(c)
e0, q0, m0, m1 = ld("p2d_elib.json"), ld("p2d_elibp3_nomask.json"), ld("p2d_elibp3.json"), ld("h_elibp3.json")
# 동등 확인(먼저): P2D에서 e_lib_p3(MASK 없음) = e_lib.py (더한 키 masked_meta_keys·circuits.*.masked 밖 전부 같음)
dropk = lambda r: {**{k: v for k, v in r.items() if k not in ("masked_meta_keys", "circuits")},
                   "circuits": {n: {k: v for k, v in cv.items() if k != "masked"} for n, cv in r["circuits"].items()}}
if e0 is None or q0 is None or dropk(q0) != e0:
    print("E5 INVALID: e_lib_p3(MASK 없음) ≠ e_lib on P2D"); bad.append("E-LIB-equiv")
else:
    lib_ok = (m0 is not None and m1 is not None and m0["masked_meta_keys"] == m1["masked_meta_keys"] == sorted(MASK_META)
              and m0["hash"] == m1["hash"] and set(m0["circuits"]) == set(m1["circuits"])
              and all(v["ok"].get("load") for v in m1["circuits"].values()))
    print("E5 E-LIB(rails 뺀 해시) %s (%d 회로)" % ("같음" if lib_ok else "다름/실패", len(m1["circuits"]) if m1 else 0)); lib_ok or bad.append("E-LIB")
    for n in sorted(m1["circuits"]) if m1 else []:   # 뺀 키의 계약값(B26-1 계약 1·2·8): HEAD = RailDeclaration(nets = P2D library의 그 회로 supply_nets) 정확 일치, P2D = 없음(기본안) 또는 같은 값(대안 c-2 B0)
        g = subprocess.run(["git", "-C", ISO, "show", "%s:skills/analog-gmid-design/assets/library/%s.topology.json" % (P2D, n)], capture_output=True)
        nets = json.loads(g.stdout.decode("utf-8")).get("supply_nets") if g.returncode == 0 else None
        want = {"__set__": sorted(nets, key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False))} if isinstance(nets, list) else None
        hv, bv = m1["circuits"][n]["masked"].get("rails"), (m0["circuits"].get(n) or {}).get("masked", {}).get("rails")
        cok = (want is not None and hv == {"__dc__": "RailDeclaration", "nets": want}   # 정확 일치 -- 계약 밖 필드가 끼면 FAIL(v8.3, 7차 검토 S1)
               and (bv == "<ABSENT>" or bv == hv))
        if not cok:
            print("E5 E-LIB rails 계약 FAIL %s (HEAD %s, P2D %s, 기대 nets(P2D library) %s)" % (n, hv, bv, nets)); bad.append("rails:" + n)
print("E5 E-LIB/E-INST PASS" if not bad else "E5 E-LIB/E-INST FAIL " + ",".join(bad))
PYEOF

# ---- E6: 정의 보존(MOVE-TOTAL) ----
$PY "$S/move_plan.py" check --root "$ISO" --base "$B0" --head HEAD --card ALL "${MP_ARGS[@]}" \
    --allow-changed workspaces/run_harness.py::run skills/analog-gmid-design/assets/gmid_design_pipeline.py::run_gmid_design_pipeline \
    > "$S/chk_all.json"; echo "E6 exit=$?"
```

| ID | N6.2 `3` 조건 | 통과 기준 |
|---|---|---|
| E0 | MOD1~MOD10 존재 | `layer.json`의 `present`가 N3.10 표 10행 전부(표는 도구가 계획서에서 읽는다) |
| E1 | import 계층 위반 0 | 같은 실행 exit 0, `findings` 0(F2가 SD의 MOD9 임시 재수출을 지운 뒤 -- §2.2 D-22) |
| E2 | 이동 커밋마다 AST 해시 동일 | **`E2 INVALID` 줄 없음**(B0..HEAD `tools/gates`·`tools/migrate` 무변경 -- D-27 사후 강제, v8.1 6차 검토 N2: 이 줄이 나오면 E2는 PASS가 아니라 INVALID). 그리고 card마다 ① V3 exit 0, JSON `defs` = `[]`, `mutants` = 0, `move_rejected` = `{}`, `not_targeted` = 0, `targets_by_def` = `{}`(범위 정책 키)(M card 판정에서 card마다 이미 요구한 것의 재확인 -- §8 M행). `exempt_ignored`·`survivor_bindings`(면제 묶기 키)는 기준이 아니다(변이 0이면 비어 있다) ② check exit 0, `findings`의 모든 목록 비어 있음(`move-set`·`move-rejected`·`changed`·`lost`·`rebind`·`future`·`stmt-order`·`order`·`shim`·`cache`) ③ **일관성 점검(증거로 세지 않는다)**: ①의 `moved`(`to`→`from`) = ②의 `moved_defs`, ②의 `moved_units` 목적지 집합 = ②의 `assigned` -- ①과 ②는 같은 `$GC`의 같은 `moved_defs`를 부르므로 동어반복이다(2차 검토 m5). `targets`(파일 목록)는 기준이 아니다(1차 검토 B5). 출력 키가 바뀌면 이 행을 다시 잰다(§5.3-4). `--gmid-phase=3`·`--gmid-strict=`는 `10-test-separation` §6.10(428행 "auditor는 V1 명령과 같은 값을 준다")대로 그 card의 V1 값(3차 검토 m2) |
| E3 | `sizing_recipe.py` 삭제 | 첫 루프 출력 없음(**세 shim 파일 모두 없음** -- v7, 4차 검토 m4: v6은 `sizing_recipe.py`만 보고 TL·DR 부재는 E4 `absent_split`에 맡겼다. 같은 사실을 여기서도 직접 본다), `E3 INVALID`·`E3 FAIL(도구 오류 …)` 출력 없음, `E3 PASS`. **v7 fail-closed(4차 검토 S1)**: `git -c core.quotepath=off … grep -z -l`로 경로를 받고, `git show` 실패는 `ERROR <경로>` 줄 + 파이썬 종료 코드 3, 셸이 종료 코드를 받아 0이 아니면 `E3 FAIL(도구 오류)`. 실측(부록 A F2v7): v6 블록은 비ASCII 경로 importer 하나만 남은 합성 커밋에서 `git show` exit 128 traceback 뒤 **`E3 PASS`**, v7 블록은 같은 커밋에서 `E3 FAIL: workspaces/k/probe_전압.py`. **실측(`7535799`를 base 대용으로, `p3_scripts/p3v6_e3_check.out.txt`)**: import 문장 69줄·63파일, import 호출 9줄·5파일(§7.2), 제외 집합 안 1파일(`probe_stage_partition.py`) -- 거부 확인이 성립한다. **AST로 바꾼 이유(D-24)**: 줄 머리 정규식은 `import numpy as np, sizing_recipe as sr` 모양 6파일(`tests/probe_physical_consistency.py`, `tests/probes/probe_L_search_window.py`·`probe_diode_min_vgs.py`·`probe_metric_tiers.py`·`probe_runtime_budget.py`·`probe_stack_headroom_feasibility.py`)을 놓친다(정규식 57 대 AST 63파일) -- 그대로 두면 F1이 그 6파일을 빠뜨려도 E3이 통과하고, probe는 V1이 수집하지 않아 shim 삭제 뒤 조용히 깨진다. 텍스트 일치는 `test_d_move_tests.py:37` docstring을 잡아 거짓 FAIL(3차 검토 S7) |
| E3b | SD 임시 재수출 삭제 뒤 이름 해석(SD-NAMES, v7 -- D-26) | `E3b LIVE moved_out=<m> base_files_reading_moved_out=<f> pre_existing=<p>` 줄에서 m > 0·f > 0, `E3b INVALID`·`E3b FAIL`·`ERROR`·`E3b FAIL(도구 오류 …)` 출력 없음, `E3b PASS`. `pre_existing`(base에서 이미 풀리지 않던 (파일, 이름) -- **표지 이름 `*`·`<…>`는 넣지 않는다**, v8 -- 5차 검토 B2)은 판정에서 빼고 수를 기록한다(`a796468`·`0f23786` 1 -- §11-10). **실측(부록 A F1v7·F2v7, `a796468` 복제본의 합성 커밋, 근사 배정 모의 M9 트리)**: 분할 전 base(HEAD = base)에서 `INVALID`(m = 0 -- 거부 확인이 '이동 없음'을 잡는다), 모의 M9 병합본(SD가 나간 이름 전부 재수출)에서 `LIVE moved_out=62 base_files_reading_moved_out=31` + `PASS`, 재수출 하나(`find_structural_symmetry_candidates`)를 지운 커밋에서 `FAIL structural_symmetry_probe.py:10` 한 줄, SD가 스스로 읽지 않는 재수출을 모두 지운 커밋(F1 없는 F2)에서 V1 밖 파일을 포함한 FAIL(v7 측정 88줄은 모의 과대 삭제 -- v8 재측정 49줄·12파일, 부록 A F1v8), 비ASCII 경로 reader를 더한 커밋에서 그 경로도 FAIL, 존재하지 않는 B0에서 `ERROR` + `E3b FAIL(도구 오류 rc=3)`. **v8(5차 검토 B2, 부록 A F2v8)**: B0' = `0f23786` + star import reader·`getattr(sd, 변수)` reader·파싱 오류 파일, H = B0' + SD의 `find_structural_symmetry_candidates` def를 새 파일로(재수출 없음) + `structural_symmetry_probe.py`만 갱신 -- v7 블록 `LIVE moved_out=1 … pre_existing=4` + **`E3b PASS`**(결함 재현), v8 블록 `pre_existing=1` + `E3b FAIL` 세 줄(`star_reader.py:1 *`, `dyn_reader.py:3 <동적 이름>`, `parse_err.py:0 <PARSE-ERROR>`). 같은 v8 블록이 base(HEAD = B0)에서 `INVALID`, 모의 M9에서 `PASS`(`moved_out=62 base_files_reading_moved_out=31 pre_existing=1`) |
| E4 | 레지스트리 목적지 = 실제 위치 | test PASS(`PT3` -- v8, 5차 검토 B1), 도구 exit 0, `reg_mismatch`·`unassigned`·`upward`·`cycles`·`conflicts` 0, `absent_split` = `[sizing_recipe.py, topology_library.py, design_report.py]`, `stick_diagram.py`·`audit_current_forced.py` 밖 단위의 `rule` 전부 `A-0` |
| E5 | 동작 보존(N6.3) | `import_any` 출력이 `IMPORT-ANY tried=<n> expected=<n> failed=0` 한 줄뿐(n > 0, `FAIL`·`INVALID` 줄 없음, 함수 종료 코드 0 -- v7, 4차 검토 S2). **v8(5차 검토 B1)**: `PT3` 전체와 `PT3 --gmid-dod` 전체 두 실행 모두 실패 0(수집 1개 이상). **v8.2(UD-0 (c) 기본안 = 선례 모양, D-28)**: §10 E5 블록 출력에 `E5 INVALID` 줄이 없고 `E5 E-LIB/E-INST PASS` -- (i) **동등 확인(먼저, P2D = F1 전 판)**: `e_inst_p3.py`와 `e_inst_df36.py`의 출력 JSON이 `engine_origin` 키 하나만 다르고(p3가 df36 항목을 모두 포함) stdout 사본이 같다(`elapsed=<초>s`만 가림); `e_lib_p3.py`(인자 없음) 출력이 더한 두 키(`masked_meta_keys`·`circuits.*.masked`) 밖에서 `e_lib.py` 출력과 같다 -- 아니면 INVALID (ii) E-INST(파일럿·`folded_cascode`): HEAD의 `e_inst_p3.py` 출력이 P2D의 같은 스크립트 출력과 최상위 키별 `field_sha256`(빼는 키 `EXCL_INST` = 없음)·`raw_sha256`·`without_topology_ref_sha256`이 같고, `exists`, `[FAIL]` 없음, 두 판 `topology_ref_equals_expected_contract1`, 경로 문자열 잎 0 (iii) E-LIB: `e_lib_p3.py … rails`(`MASK_META`) 결과 `hash`가 P2D와 HEAD에서 같고 회로 집합이 같고 HEAD에서 회로마다 `load` 성공 (iv) **빼낸 필드의 계약값(B26-1 계약 1·2·8)**: 회로마다 HEAD `masked.rails`가 `{"__dc__": "RailDeclaration", "nets": <그 회로 **P2D** library topology `supply_nets`의 정렬 집합>}`와 **정확히 같고**(다른 필드가 있으면 FAIL -- v8.3, 7차 검토 S1; 계약값은 비교 시작 판의 선언이라 `git -C "$ISO" show "$P2D:…/library/<회로>.topology.json"`에서 읽는다 -- 7차 검토 m1) P2D `masked.rails`는 `<ABSENT>`(기본안 -- 네 card가 P2D 뒤, 기록 `20261001-b26-phase3-cards`) 또는 HEAD와 같다(대안 (c-2) B0 판) -- 아니면 `E5 E-LIB rails 계약 FAIL <회로>`. **비교 판 = P2D**: 선례 승인 `20260930-phase2-e4-baseline`(design 20 §10 E4 2026-09-30 정정, 사용자 "둘다 기본안으로 진행해")의 기본안 모양 -- 직전 Phase DoD 대상 커밋과 마지막 병합본을 같은 경로에서 비교하고 의도적으로 바뀐 필드만 계약값으로 따로 판정한다. 빼는 필드 목록의 유도·실측은 D-28 (e)·부록 A F1v82~F3v82. **대안(c-2)을 고르면** 블록의 `P2D=`에 B0(M1 판정 기록 `base_commit`)를 넣는다(그 밖의 명령·판정 python 그대로). 실측(부록 A F3v82 -- `a796468` 판을 P2D 대용, 계약 1·2 모양 B26-1 시제품을 HEAD 대용, 이 행의 판정 python을 design에서 그대로 뽑아 실행): 시제품 = `E5 E-LIB/E-INST PASS`, nets를 틀리게 만든 시제품 = `E5 E-LIB rails 계약 FAIL` 9줄 + `FAIL`, `rails`와 함께 meta 키를 하나 더 바꾼 시제품 = `E5 E-LIB(rails 뺀 해시) 다름/실패` + `FAIL`, P2D `e_lib.py` 해시를 바꾼 고장 입력 = `E5 INVALID: e_lib_p3(MASK 없음) ≠ e_lib on P2D`. v8.3 재측정(부록 A F4v83 -- 고친 판정 python을 design에서 그대로 뽑아 같은 다섯 시나리오 + 둘): 위 넷은 같은 결과, `RailDeclaration`에 계약 밖 필드를 더한 시제품(p4)과 HEAD library `supply_nets`에 넷을 더한 시제품(p5)이 `E5 E-LIB rails 계약 FAIL` + `FAIL`(v8.2 판정 python은 둘 다 `PASS` -- 같은 입력으로 재현). E-LIB 사본이 F2 뒤에도 도는 이유: `e_lib.py`가 SD에서 읽는 이름은 `__file__`·`load_topology`·`run_topology_pipeline`뿐이고(E3b `file_reads` 실측) `run_topology_pipeline`은 SD(MOD7)에 남아 `load_topology`를 읽으므로 SD가 그 import를 지닌다 -- 근사 F2 모의(부록 A F1v8)에서 E3b 식이 6개 `e_lib.py`에 FAIL 0, 실제 실행은 부록 A F3v8. 실측(부록 A F3v7): 모의 M9 `top` 트리 `FAIL design_report`·`instance_report_builder` + `tried=13 expected=13 failed=2`, `bottom7` 트리 `failed=0`, 고장 `GC`(없는 경로)에서 `IMPORT-ANY INVALID`(v6 블록은 같은 입력에서 `design_report`만 보고하고 종료 코드 0), 잘못된 트리 루트에서 `INVALID` |
| E6 | 정의 보존(MOVE-TOTAL) | exit 0(모든 발견 목록 비어 있음). `shim`: shim 3파일은 F2 뒤 없어 해당 없음, 남는 split 파일(SD·`audit_current_forced.py`)은 (a)와 출처 동일성만(`--card ALL`은 이름 집합 대조 없음 -- §3 SHIM). base를 'Phase 3 첫 card base'가 아니라 **M1 판정 기록 `base_commit`**(D0b 병합 뒤)로 둔다 -- G1·T0·D0a·D0b 뒤라 `check`의 `assigned`가 D0b 레지스트리로 계산된다(2차 검토 m4) |

부록 A M22·M24의 재현 명령도 같은 이유로 `\|`를 `|`로 읽어야 한다(측정 기록이라 판정 영향 없음 -- 표 칸이라 그렇게 적혔다).

---

## 11. 열린 질문 (N9.2-8)

없다. §9.2의 UD는 착수 전 사용자 결정 대기 항목이다. 이 초안이 드러낸 **계획·문서 개정 요청**(UD-0에 포함, 2·6·8 제외 -- 문안은 `_drafts/p3_doc_amendments.md`):

1. 레지스트리 목적지 열이 N3.10 이전 판 이름을 쓴다(§6.1) -- 517행 "레지스트리 열이 정본"은 D0b 재생성 뒤에 성립한다(문서 개정 불필요 -- D0b가 열을 고친다).
2. N3.10 533행의 이동 제외가 V3에만 적혀 있다 -- V6·V7도 같은 규칙이어야 이동 card가 판정 가능하다(§5.1). '옮긴 단위'의 정의는 이 design §3(G1 spec card 계약 0~3)을 인용한다(**G1 승인(UD-5)이 덮는다** -- G1 계약 13, UD-0 아님).
3. N3.12.3 test-only 열거에 Phase 3 T0·T1이 없다(`p3_doc_amendments.md` §3).
4. 534행 '추적 파일 전부 갱신'과 판정 기록 불변(D-9)의 충돌(§2 -- D-2의 TL·DR shim도 같은 문장에).
5. `00-common` §3.2 103행과 §10.1 431행의 MOD10 인자 담당, 431행 시그니처에 topology 경로 인자가 없음(D-5, §4).
5b. (v6) N3.10 표 3건(`load_topology`·`validate_theta_declaration_order` → MOD3, `optimize_full_circuit_budget` Phase 3 위치 MOD8)과 `10-test-separation` §5.6 '파일' 열(§1·§5).
6. 백로그 후보(§5.4): Phase 3 밖 card의 같은 경로 import 재바인딩(Phase 3 안은 `check` `rebind`), 클래스 수준 문장이 V3·V6에 보이지 않음. (V7 그래프의 `__init__`·레지스트리 값 간선은 B33이
   G1 전에 닫는다 -- v5.)
7. (v5) N3.10 MOD2 '대표 대상'에 `rail_declaration` 추가(D-19, §6.4) -- v6: D-19 질문의 답이 (가)일 때만(문안 `p3_doc_amendments.md` §1 (d)).
8. 다른 초안에 넘기는 정정(이 design이 고치지 않는다): (v5) redteam 번호 33·34·35는 **세 card 초안에 이미 반영됨**(v6 확인), 범위 정책 card '결정 필요 항목'의 G1 순서 문장(G1이 나중 --
   G1 card 계약 4가 합성 문장을 가진다), B37a의 접근자 모듈(D-19 결정을 따른다). (v6) B34 초안 212행 "M2(MOD2로 이동)" 단정 → 'D0b 이관표가 정한다'(§6.4, 3차 검토 m6).
9. (v6) 백로그 후보: 정규식으로 센 저장소 import 목록(부록 A M22 등)은 `import a, sizing_recipe` 모양을 놓친다 -- Phase 3 밖의 같은 모양 계수(예: 20-dead-code-dup·B22 스캔)도 AST로 다시 셀지 검토.
10. (v7) 백로그 후보(Phase 3 범위 밖 -- E3b 측정 중 발견): `workspaces/current-reuse-telescopic-ota-report/stick.py:9~13`이 `from stick_diagram import (…, block_from_row_widths, …)`를 하는데
    `a796468`의 SD에 `block_from_row_widths` 바인딩이 없다 -- 이미 깨진 추적 스크립트다(그 이름은 SD에서 지워진 뒤 갱신되지 않았다). E3b는 base에서 이미 풀리지 않던 (파일, 이름)을 판정에서 빼고
    `pre_existing` 수로만 남긴다(Phase 3가 만든 깨짐이 아니다). 처리(스크립트 갱신·삭제·보존)는 사용자 몫인 workspaces 정리라 백로그로 넘긴다.
11. (v7; v8 -- 5차 검토 S3; **v8.3 해소됨**) 사용자 승인 기록 문장과의 충돌: 승인 기록 `20260930-b26-before-phase3` 27·28행 ③은 B26-1·B34를 "Phase 2 진행 중에 병합하는 것(card `phase: 2`)"이라 적었는데,
    확정 순서는 둘(과 그 사이 b26pre·backfill -- 넷)을 Phase 2 DoD **뒤**에 둔다. **해소(2026-10-01)**: 사용자 답 B26 묶음 [card phase] "phase 3 + 정정 기록 (Recommended)" -- decision 기록 `20261001-b26-phase3-cards`가 ③의 병합 시점 문구를
    'Phase 2 DoD 뒤·Phase 3 M card 전(card `phase: 3`)'으로 바로잡고(옛 기록은 고치지 않음), 네 card 초안 머리는 `phase: 3`·`approval: 20261001-b26-phase3-cards`다. 계획 1001행("먼저 병합하는 card의 spec card `phase` 값은 병합 시점의 진행 Phase다")과 맞다.
    그 기록은 design 30 승인·U-03을 기다리지 않는다고 적었다. 그래서 이 항목은 승인 질문에서 빠졌고(v8.3, 7차 검토 S2), `_drafts/pending_questions.md` Q-B34-PHASE는 닫혔다.
    게이트 사실(`0f23786` 실측, 결정 근거로 남김): `merge_gate.rule10_phase`(532~549행)는 card `phase`를 진행 Phase와 대조하지 않는다. V1 명령 대조(1008~1010행)는 `--gmid-phase=`가 card `phase`와 같은지 본다 -- 그래서 **네 card 판정 기록의 V1은 `--gmid-phase=3`**이다.
    `strict_set`(1042행 `if c["phase"] == card["phase"]: keys |= set(c["activated_ic_case"])`)은 같은 Phase card의 엄격 집합인데, 네 card는 `activated_ic_case`가 없고 그 앞에 병합된 phase 3 card도 없어 자기 strict 집합은 빈 집합이며 뒤 phase 3 card의 집합도 바꾸지 않는다.
    이 design은 넷을 'Phase 3 M card 전에 병합되는 앞당긴 card'로 다루고, Phase 3 DoD N6.3 목록(`^phase: 3$`)에 든다(§9.1).
12. (v7) 확인 요청(오케스트레이터): 확정 순서 지시의 괄호 "Phase 3(T0·D0a·D0b → G1(32) → M1…)"는 D0a가 G1의 `reachability.SourceIndex`·`moved_defs`를 import하는 의존(D0a 계약 5)과
    어긋난다. 이 design은 G1 → D0a → D0b로 둔다(§8.1). D0a를 G1 전에 병합하려면 D0a 계약 5(정의 하나)를 바꿔야 하고 그것은 이 design 범위 밖이다.

---

## 부록 A. 측정 명령과 결과 (모두 읽기 전용; v3 행은 gate `master` `cd64170`, v4 행(G5'·G6'·H'·B2·S8·F)은 `7535799`)

`R` = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, `D` = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts`, `$PY` = `C:/Python314/python.exe -B`. v1·v2 스크립트는 초안 v2 부록 A대로.
v3 스크립트는 `D/p3v3_g1_measure.py`(합성 저장소는 `C:/g29` 아래에 만들고 단계마다 지움)와 `D/p3v3_facts.py`. v4 스크립트는 `D/p3v4_g1_measure.py`(합성 저장소는 `C:/g51` 아래, 단계마다 지움,
케이스마다 `p3v4_g1_results.partial.jsonl`에 누적 기록) → `D/p3v4_g1_results.json`.

| # | 명령 | 결과 |
|---|---|---|
| M0 | `ls R/docs/02-design/features/ \| grep gain` | 00·05·10·20 네 개(30 없음) |
| M1 | `sed -n 985,1020p R/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` | 1000행 Phase 3 행, 1018행 DoD |
| M2 | `git -C R log --oneline 070cf69..cd64170` | 8커밋 -- 엔진 변경은 `ed98d35`(DF-36)뿐 |
| M6 | `wc -l R/skills/analog-gmid-design/assets/*.py`; `$PY p3_measure.py` `toplevel_counts` | SR 12015줄(Class 13·Func 174·Assign 30), SD 9035줄(Class 28·Func 132·Assign 8), TL 7, DR 5+1 |
| M9~M15 | 초안 v2 부록 A와 같음(독립 검토가 cd64170에서 재실행해 일치) | §6.1 |
| M18 | `grep -n "^\s*global "`; `grep -n lru_cache R/…/topology_library.py`; `sed -n '2391p;2530p;7697p' R/…/sizing_recipe.py`; 캐시 사용 함수 AST 스캔(이 절 명령과 같은 세션의 `$PY -c`) | `global` 0 / `lru_cache` 데코레이터 1곳(248행, 254행은 주석 -- **v2 '2곳' 정정**) / 주석 대입 캐시 3개, 사용 함수 각 1(`knee_L_for_kind`·`feasible_L_window`·`achievable_metric_bound`) |
| M19~M20 | 초안 v2와 같음 | §5.1, `import_layering`은 표 밖 파일 import를 보지 않는다 |
| M22 | `git -C R grep -l -E "^[[:space:]]*(import\|from)[[:space:]]+(sizing_recipe\|stick_diagram\|design_report\|topology_library)\b" cd64170 -- '*.py'` | §7.2(86개) |
| M23 | `git -C R status --porcelain -- workspaces` | 추적 안 된 `.py` 1개 |
| M24 | `git -C R grep -c -E "(sizing_recipe\|stick_diagram\|topology_library\|design_report\|audit_current_forced)\.py" -- A/tests ':!A/tests/probes'` + 파일별 문맥 | §7.1 A·B·C 군 |
| M25 | `grep -n "tools/gates\|CLASS_GLOBS\|GATE_CODE_PREFIX" R/tools/gates/role_paths.py` | `tools/**` = tool, `GATE_CODE_PREFIX = "tools/gates/"`(23행) |
| M27 | `ls R/.ai/approvals \| grep -i -E "u03\|u-03\|30-module\|phase3\|p3-"` | 0건 |
| G1 | `$PY D/p3v2_g1_measure.py`(초안 v2) | 대상 def 473, 변이 15,677, V6 새 항목 861(부록 v2 G1 그대로) |
| G2 | 같은 실행 | 엔진 def 473 중 미도달 109(면제 1 → 108) |
| G4 | `git -C R grep -n "def_hash\|changed_defs" -- . ':!*.jsonl'` | 게이트 밖 호출 **3곳**(스크립트 3개: `mut_def.py:67`, `probe_t2_vs_1st_survivor.py:16`, `v3_baseline_probe.py:17` -- **v2 '4곳' 정정**) |
| G5 | `$PY D/p3v3_g1_measure.py` → `p3v3_g1_results.json` `counterexamples`(26단계 -- v6 정정, v5까지 '27'은 오기: 각 단계 합성 git 저장소에서 base `mutate_changed.py`·`source_lint.py`·`reachability.py`를 실제 실행, v3 규칙은 같은 파일의 참조 구현으로 모의) | §5.2 표와 G1 spec card 계약 12 표. 인정 9단계 base 1/1/1 → v3 0/0/0, 거부 단계 base = v3, `overwrite`·`swap` V7 0/0, `cache-split` 0/1/0, `record-class-*` 0/0/0, `same-path-rebind(observation)` 0/0/0 |
| G6 | 같은 실행 `real_rename_same_dir`·`classes`·`multi_bound_names` | 엔진 4파일 통째 이동 모의: 단위 218/218·169/169·8/8·7/7, def 272/272·181/181·12/12·8/8, 거부 0, 호출당 5.8~9.2초. 클래스 SR 13(dataclass 8·예외 3·메서드 없음 10·클래스 수준 문장 8), SD 28(dataclass 28·메서드 없음 26). 최상위 중복 바인딩 0 |
| G7 | 같은 실행 `noop` | 판정 기록 `df36`(070cf69→ed98d35)·`dup-w-calc`(b7d1798→a9de49c): `units`·`defs`·`rejected` 모두 빈 결과 |
| V3 | `$PY D/p3v3_facts.py` `B5_v3_output_keys`; `git -C R show role/code/20260930-v3-history-clone:tools/gates/mutate_changed.py \| grep -n 'json.dumps({"tool"\|changed_defs(\|cat-file'` | HEAD 출력 키 `tool, verdict, targets, mutants, killed, survivors`(ERROR `tool, verdict, error`), B28 판 같음 + ERROR `baseline_failed`. B28 판 줄: cat-file 359, `changed_defs` 364, 출력 398·402·407. `targets` = `diff --name-only`의 소스 `.py` 경로 목록(277행) |
| V4 | `$PY -c` 스키마 조회 `.ai/verification/_schema.json` `$defs.check` | 판정 기록의 `checks.V3` = `{verdict, basis}`(자유 문장) -- E2가 기록이 아니라 도구 재실행 JSON을 읽는 이유 |
| S5 | `$PY D/p3v3_facts.py` `n310_header`·`n310_rep_tokens`·`mod_table` | 머리 `ID, 파일, 책임, 대표 대상`. 토큰: 식별자 41(MOD1 5·MOD2 5·MOD3 9·MOD4 7·MOD5 5·MOD6 6·MOD8 3·MOD9 1), `<파일>.py` 1(MOD4), 점 이름 1(MOD9), 무시 2(MOD1 `∂ID/∂VSB`, MOD10 `workspaces/`), MOD7 0 |
| S6 | 같은 실행 `S6_nested_refs` | 중첩 def·메서드 안에서만 다른 최상위 이름 참조: SR 17, SD 4 |
| S7 | 같은 실행 `future_annotations` | `from __future__ import annotations` SR 35행, SD 32행(**TL 24행 누락 -- v4 F행에서 정정**, 2차 검토 S3) |
| S11 | 같은 실행 `S11_attr_overrides`(`git grep -n -E "^\s*(sr\|sd\|sizing_recipe\|stick_diagram\|topology_library\|design_report\|tl\|dr)\.[A-Za-z_]+\s*=[^=]" -- '*.py'`) | **14줄** 8파일(probe 12 + workspaces 2, §7.2 D군 -- v3 '12줄'은 오기, 2차 검토 m1) |
| S12 | 같은 실행 `S12_run_inventory` + 파일별 집계·`run`의 직접 호출자 | 60 test(`test_extract_selftest.py` 24, `test_selftest_sizing_recipe.py` 22, `test_probe_parasitic_pm_all_circuits.py` 5, …), 직접 호출자 12 = `_run_combo`·`_run`·`base_blob_text`·spice `run` 등 이름 과대 근사 |
| S13 | `git -C R grep -n _SIZING_RECIPE -- .` | `test_ts6_dead_probes.py` 60·221·222·261·262뿐 |
| m6 | 같은 실행 `m6_scan_names` | T0 spec card 계약 9 목록 |
| m7 | 같은 실행 `m7_string_imports` | 10곳(모두 `A/tests/contracts`) |
| G5' | `$PY D/p3v4_g1_measure.py` → `p3v4_g1_results.json` `counterexamples`(51단계 = v3 26 + 2차 검토 새 반례 25 -- v6 정정: N1·N1b·N1c·P·P-exact·N2·N3·N3b·N4·N5·N5ok·N6·N6ok·N7·N8a·N8b·N9a·N9b·N10·N11·N12·N13·S2 2개·S5; 단계마다 합성 git 저장소에서 HEAD `7535799`의 `mutate_changed.py`·`source_lint.py`·`reachability.py` 실제 실행, v3·v4 규칙 참조 구현 나란히, v4는 D0a `check` 발견 모의까지) | `v3_regression` 26/26 참(v3 규칙 결과 = 초안 v3 측정), `v3_steps_v4_changed` 빈 사전(v4가 v3 26단계 exit를 바꾸지 않음). `adversarial_summary` 22건 전부 `rejected` 참(G1 19, `check`만 3: `same-path-rebind`·`N6`·`S5`). v3 규칙이 base보다 약했던 것 N1·N2·P·N3b·N4·N13·S2 `except as`(+ `check` 몫 N6·S5) → v4 exit = base. 보수 비용 `P-property-exact` v4 V3/V7 1 |
| G6' | 같은 실행 `real_rename_same_dir`(v4)·`engine_facts` | 단위 218/218·169/169·8/8·7/7, def 272/272·181/181·12/12·8/8, 거부 0, M-0h 위반 0, qualname 중복 제외 0, `check` 모의 발견 0(`rebind`는 트리 전체 단위 대조). `moved_defs` 한 호출 7.9~15.6초, `check` 모의 1.3~2.4초. 엔진 4파일 star 0·`global` 0·`multi` 0·qualname 중복 0, future `annotations` SR 35·SD 32·TL 24(DR 없음) |
| G7' | 같은 실행 `noop`(v4 규칙) | `df36`·`dup-w-calc` 모두 빈 결과(v3과 같음) |
| B2 | `MP_ARGS="--split a.py b.py --aliases '{\"optimizer\": \"theta_search.py\"}'"; printf '[%s]\n' $MP_ARGS` 대 §6.3 배열 `printf '[%s]\n' "${MP_ARGS[@]}"`, `$PY -c "import sys,json; json.loads(sys.argv[-1])" "${MP_ARGS[@]}"` | 문자열: `['{"optimizer":]`, `["theta_search.py"}']`(파손). 배열: 마지막 원소 `{"optimizer": "theta_search.py"}`, JSON 파싱 성공, 인자 14개 |
| S8 | `grep -n 'diff", "--name-only\|make_clone\|cat-file\|changed_defs\|rmtree\|json.dumps\|def def_hash\|def _strip_doc\|base_src' R/tools/gates/mutate_changed.py`; `grep -n 'add_parser("vcase")\|tool_tmpdir\|root_state\|observe' R/tools/gates/redteam/lib/rt.py`; `ls R/tools/gates/redteam/attacks \| tail -1`; `git -C R diff --stat cd64170 HEAD -- A/*.py workspaces/run_harness.py docs/01-plan` | `make_clone` 53·323, `_rmtree_force` 61·406, `_strip_doc` 74, `def_hash` 84, `changed_defs` 88~100·364, diff 314, cat-file 359, `base_src` 361, 출력 398·402·407; vcase 1351, 관찰 599~621, `run_all.py:98` `observed_equals`; 마지막 `31-v3-git-history`; 엔진·계획서 변경 0 |
| F | `grep -n "__future__\|import \*\|^\s*global " R/A/*.py R/workspaces/run_harness.py`; `$PY -c` symtable 실측 `X = [t*K for t in range(3)]` | future SR 35·SD 32·TL 24, star 0, global 0; 3.14 `symtable` 모듈 표에 인라인 컴프리헨션 변수 `t`가 지역·대입으로 들어감(문장 단위 전역 읽기를 AST 유효 범위로 세는 근거) |
| B33 | `grep -n "attacks/<다음 번호>" D/prep_b33_v7_edges.md`; `ls D/draft_b33.spec.md` | 278행 "G1 32 예정이면 그 다음", B33 spec card 초안 없음 → D-18(G1 32, B33 33) |
| H | `git -C R rev-parse --short HEAD`, `git -C R rev-parse --short gate/master`, `git -C R log --oneline -1 role/code/20260930-v3-history-clone` | v3: `cd64170`, `cd64170`, `dee338d`(B28 code, 미병합). **v4(H')**: `7535799`, `7535799`, B28 병합 `2b41e79`·판정 기록 `8790b24` |
| P | `PYTHONPATH=R/tools/gates $PY -c "role_paths.parse_spec_card(...)"` 세 초안 | G1·T0·D0a 머리 파싱 성공(절 11개씩) -- v4 세 card도 같은 명령으로 재확인(부록 D), v5 세 card도 재확인(부록 E) |
| E1 | `git -C R rev-parse --short HEAD`(v5, 2026-10-01) | `7535799` -- v4 측정 시점과 같다(B26-1·B34·B33·면제 묶기·범위 정책 모두 미병합 초안) |
| E2 | `grep -n "mid\|modname" R/tools/gates/mutate_changed.py`; `grep -n "def module_name" -A2 R/tools/gates/reachability.py` | `modname = rch.module_name(path)` 362, `mid = "%s:%s:%s:%s" % (modname, q, opname, npath)` 374, 면제 대조 375; `module_name` = `os.path.splitext(os.path.basename(path))[0]`(47행) -- 변이 id 모듈 = 파일 줄기(§5.5.3) |
| E3 | `git -C R grep -n setattr HEAD -- '*.py'`; `git -C R grep -n "monkeypatch\." HEAD -- skills/analog-gmid-design/assets/tests` | `setattr` 0건, `monkeypatch.`는 `test_df36_instance_relpath.py`의 `chdir` 4건뿐 -- 엔진 모듈 속성 교체 0(§7.2) |
| E4 | `grep -n "^def load_topology\|^def find_matching_candidates\|^def _import_analog_grammar\|^def true_current_mirror_groups\|^def resolve_stack_layout" R/A/*.py`; `sed -n 515,531p R/docs/01-plan/…plan.md` | `load_topology` SD 8550, `_import_analog_grammar` SD 1045, `find_matching_candidates` SD 945, `true_current_mirror_groups` SR 2191, `resolve_stack_layout` SR 6470; N3.10 MOD2 책임 "topology·spec 로딩, 스키마·단위·참조·선언 순서 게이트, 구조 제안"(D-19 근거) |
| E5 | 초안 읽기(측정 아님): `D/draft_b26_1.spec.md` 의도·계약 1~4·11·'신규 시그니처', `D/draft_b34.spec.md` 범위·사이트 표, `D/draft_b33.spec.md` 계약 7·9·'작성 전 실측' 1, `D/draft_v3_exempt_binding.spec.md` 용어·계약 2·3, `D/draft_v3_scope_policy.spec.md` 계약 1~3·'결정 필요 항목', `D/approval_20260930-b26-before-phase3.md`, `D/user_decisions.md` A1·A2 | §5.5·§6.4 추정 행의 출처. 병합 뒤 실측으로 바꾼다 |
| F1v6 | `$PY D/p3_scripts/p3v6_order_shim_sim.py C:/g73/repo <out>.json C:/g73/sim_<변형> <배치> <보정>`(v6, `7535799` 복제본, 결과 `D/p3_scripts/p3v6_order_shim_sim.{top,bottom,bottomall,bottom7,pull_top,pull_bottom7}.json`) | 근사 이관표(규칙 A-1~A-5 단순 구현: 단위 403, 규칙 미배정 13, 위쪽 참조 49 -- **D0b 이관표가 아니다**)를 모의 보정(`raise`: 참조 단위를 올림 89단위 변경 / `pull`: A-1 아닌 피참조를 끌어내림 79단위 변경)해 위쪽 참조 0으로 만든 뒤 M1~M9를 실제 파일로 적용(본문 바이트 그대로, import 줄만 생성). **모든 변형에서**: `order` 옛 문언 M8·M9 발견(`stick_diagram.py`), 새 문언 M1~M9 발견 0. `shim` 옛 문언 M1~M9 모두 발견(SR 214→…→1 = 최종 `__future__` 줄, TL·DR), 새 문언 (a)(b) M1~M9 발견 0. 완전 shim: TL M4, SR M8(pull)·M9(raise), DR M9. 모듈별 단독 첫 import: 재수출을 split 파일 끝에 두면 M8 `NameError`(첫 판), `pull_top`(import 줄 모두 머리) M9에서 `instance_report_builder`·`design_report` 먼저 import 시 `ImportError … '_audit_result_json'`(SD ↔ MOD9 순환), `pull_bottom7`(D-22 배치) M1~M9 전부 성공, `bottomall`(MOD9 import 전부 끝)은 MOD9 레지스트리 문장 `NameError`. M9 트리 `import_layering`: FAIL(`MOD7 stick_diagram → MOD9`, 순환) -- M8 트리는 PASS. SD에서 MOD9로 가는 단위(모의 배정): `save_instance_json`·`run_full_circuit_audit_from_topology`·`_audit_result_json`·`_box_shape_json`·`_topology_ref_relpath`. SD 밖 split 단위의 규칙 MOD7 배정 0. `validate_theta_declaration_order`의 MOD 2 초과 참조 = `_build_shared_current_joint_plan`·`_shared_current_groups_from_compensation`(둘 다 A-4 MOD3) |
| F2v6 | `bash D/p3_scripts/p3v6_e3_check.sh C:/g73/repo HEAD` → `p3v6_e3_check.out.txt`; 원문(백슬래시 파이프) 식과 파이프 식의 `git grep -l -E` 파일 수 | 원문(백슬래시 파이프) 줄 머리 0·문자열 0, 파이프로 고친 식 줄 머리 57·문자열 10줄 6파일. AST: import 문장 69줄·63파일(정규식 57 + `import numpy as np, sizing_recipe as sr` 6파일), import 호출 9줄·5파일(`test_d_move_tests.py:37` docstring 제외), 제외 집합 안 1(`probe_stage_partition.py`). 엔진 4모듈(SD 포함) 추적 import 파일: 정규식 86, AST 92(같은 6파일) |
| F3v6 | `bash D/p3_scripts/p3v6_sec10_selftest.sh <이 문서> C:/g73/repo HEAD <모의 M9 트리>` → `p3v6_sec10_selftest.out.txt`(§10 bash 블록의 E3·`import_any`를 이 문서에서 잘라 그대로 실행) | E3: HEAD(분할 전)에서 `INVALID` 없음·`FAIL`(파일 있음 + 목록) -- 거부 동작. `import_any`: HEAD 실패 0, `pull_bottom7` M9 트리 실패 0, `pull_top` M9 트리 `instance_report_builder`·`design_report` 실패 -- 순환을 잡는다 |
| F4v6 | `$PY D/p3_scripts/p3v6_m10_inventory_time.py C:/g73/repo <out>` → `p3v6_m10_inventory_time.json`; `.ai/verification/20260930-{dup-w-calc,restore-plan-functions}/einst_time.txt` 읽기 | `run` 인벤토리 60 test id(파일 8: `tooling/test_extract_selftest.py` 24, `unit/test_selftest_sizing_recipe.py` 22, …) 한 번 실행 143.4초(71 passed·3 xfailed, exit 0). E-INST 한 판: `folded_cascode` 13.1~19.5초, `current_reuse_telescopic_ota` 97.8~137.2초 |
| F5v6 | `$PY -c` `p3v3_g1_results.json`·`p3v4_g1_results.json` 키 계수 | v3 `counterexamples` 26, v4 51, `v3_regression` 26/26 참, v4 새 키 25, `adversarial_summary` 22 |
| F6v6 | `grep -n "^\(from\|import\) " A/{sizing_recipe,stick_diagram,topology_library,design_report,audit_current_forced}.py`; `git grep -n "_audit_result_json\|save_instance_json\|run_full_circuit_audit_from_topology" -- '*.py'` | 엔진 사이 import는 모두 모듈 머리 줄(SR 1411 TL·5302 SD, DR 32 SD, ACF 43 SD) -- 함수 안 엔진 import 0. MOD9로 갈 SD 이름을 SD에서 import하는 추적 파일: `run_harness.py:42`, `test_df36_instance_relpath.py:87·237·274·288`, `test_selftest_design_report.py:25`, `test_selftest_stick_diagram.py`, `workspaces/two-stage-ota-report/check_box_shape*.py`, `smoke_run_harness_session20.py:28` |
| F7v6 | `$PY D/p3_scripts/p3v6_amend_check.py C:/g73/repo D/p3_doc_amendments.md C:/g73/amend <out>` → `p3v6_amend_check.json` | 개정 문안의 '현재' 블록 10개 = 실제 줄. D-19 두 안 모두 N3.10 표 4열·10행, `mod_table` 10, 두 행에 걸린 백틱 식별자 0, 세 함수가 기대 행에만, `import_layering` exit 0, 10 §5.6 표 21행 |
| F1v7 | (v7, `a796468`, 스크래치 `C:/g95b`) `$PY D/p3_scripts/p3v6_order_shim_sim.py C:/g95b/repo <out> C:/g95b/sim_<변형> {bottom7,top} pull` → `$PY D/p3_scripts/p3v7_e3b_synth.py C:/g95b/repo C:/g95b/sim_bottom7/state_M9 <out>` → `p3v7_e3b_synth.json` | 모의 재실행: `order` 옛 문언 M8·M9 발견·새 문언 0, `shim` 옛 문언 M1~M9·새 문언 0, `bottom7` import 실패 0, `top` M9 `design_report`·`instance_report_builder` `ImportError … '_audit_result_json'` -- v6 측정(`7535799`)과 같다. 합성 커밋(복제본 전용, 실제 저장소 쓰기 없음): `syn/m9`(모의 M9 병합본, SD 재수출 줄 5), `syn/f2drop`(SD가 스스로 읽지 않는 재수출 이름 62개 삭제 = F1 없는 F2), `syn/dropone`(`find_structural_symmetry_candidates` 하나 삭제), `syn/e3bnonascii`(+ `workspaces/k/sd_전압.py`), `syn/e3clean`(shim 3파일과 E3 importer 68개 삭제), `syn/e3nonascii`(+ `workspaces/k/probe_전압.py`). 모의 SD의 '읽지 않는 재수출'은 symtable 참조 기준이라 `__future__` 주석 안 이름(`Transistor` 등)도 넣는다 -- 실제 F2(§2.2 `global_names` 기준)보다 넓다 |
| F2v7 | `bash D/p3_scripts/p3v7_sec10_selftest.sh D/draft_phase3_design_v7.md D/draft_phase3_design_v6.md C:/g95b/repo <synth.json> C:/g95b/tree_top C:/g95b/tree_bottom7 <out>` → `p3v7_sec10_selftest.out.txt`(§10 E3·E3b·`import_any`를 이 문서와 v6 문서에서 잘라 그대로 실행) | **E3b**: base(HEAD = base) `LIVE moved_out=0` + `INVALID`; `syn/m9` `LIVE moved_out=62 base_files_reading_moved_out=31 pre_existing=1` + `PASS`; `syn/dropone` `FAIL structural_symmetry_probe.py:10 find_structural_symmetry_candidates` 한 줄; `syn/f2drop` FAIL 88줄(test 밖 -- V1이 수집하지 않는 파일: `spice/*.py` 11, `structural_symmetry_probe.py`, `rerun_symmetry.py`, `probe_l3_groups.py`, `probe_crossover_pairing_alternatives.py`, `probe_d1_verify.py`, `probe_group_split_reassembly.py`, `stick.py`, `smoke_run_harness_session20.py`, `A/topology_to_markdown.py`, `check_box_shape*.py` 2, 그리고 하네스·도구 `run_harness.py:42`·`audit_current_forced.py:43`; V1 수집 test: `test_df36_instance_relpath.py`, `test_dup_kcl_edges.py`, `test_ic3.py`, `test_selftest_design_report.py`, `test_selftest_stick_diagram.py`); `syn/e3bnonascii` 두 파일 FAIL(비ASCII 경로 그대로); 존재하지 않는 B0 → `ERROR show …`·`ERROR git grep … rc=128` + `E3b FAIL(도구 오류 rc=3)`. **E3**: `syn/e3clean` `PASS`; `syn/e3nonascii` v7 `FAIL: workspaces/k/probe_전압.py`, v6 블록은 `git show` exit 128 traceback 뒤 `E3 PASS`(4차 검토 S1 재현); 존재하지 않는 B0 → `E3 FAIL(도구 오류 rc=1 …)` |
| F3v7 | 같은 실행의 `import_any` 부분(트리 = 모의 M9 상태 디렉터리를 `skills/analog-gmid-design/assets`에 둔 루트 + 계획서 사본) | v7: `top` `FAIL design_report`·`instance_report_builder`, `tried=13 expected=13 failed=2`, 종료 코드 1; `bottom7` `tried=13 expected=13 failed=0`; base 트리 `tried=5 expected=5`; 고장 `GC`(없는 경로) → `IMPORT-ANY INVALID: 모듈 목록 계산 실패`(종료 2); 잘못된 트리 루트 → 같은 INVALID. v6 블록: 고장 `GC`에서 `design_report`만 보고하고 종료 코드 0(MOD9 실패가 사라짐 -- 4차 검토 S2 재현) |
| F4v7 | `$PY D/p3_scripts/p3v7_import_time_reads.py C:/g95b/repo_m10 a796468 C:/g95b/sim_bottom7/state_M9 <out>` → `p3v7_import_time_reads.json` | SR·DR·TL·ACF가 SD에서 받는 이름(25·2·0·1)의 import 시점 읽기 0. 모의 M9 MOD8(`sizing_layout_convergence.py`, SD에서 12)·MOD9(`instance_report_builder.py`, SD·MOD8에서 3)의 import 시점 읽기 0 -- D-22 전제가 지금 성립(D0b가 `import_time_high`로 확인) |
| F5v7 | `git -C R grep -n -E 'import_module as\|"-c".*import (sizing_recipe\|…)\|import_module\([^"'"'"')]\|getattr\((sd\|stick_diagram\|_sd\(\)), [^"'"'"']' a796468 -- '*.py'`; `.ai/verification/**` SD·SR import 계수; `git diff --stat 7535799 a796468 -- tools/gates skills/analog-gmid-design/assets` | D-24 한계 모양: 별칭 0, `-c` 문자열 0(문자열 속 `import sizing_recipe`는 계약 test 합성 입력뿐), 변수 인자 `import_module` 2(`stick_diagram.py:1056` analog-grammar, `test_restore_plan_functions.py:59` `_import` 도우미), `getattr(sd, 변수)` 0. `.ai/verification/**`: SR·TL·DR import 문장 0, `import stick_diagram as sd` 8파일(m2). `tools/gates` 무변경, assets는 SD(P9)와 새 계약 test 3개(`test_df23_inventory.py` -- 기록 JSON만 읽음, `test_dup_kcl_edges.py` -- §7.1 B군, `test_phase2_stale_refs.py` -- references md) |
| F6v7 | `$PY -P D/p3_scripts/p3v7_m10_mutants.py all C:/g95b/repo_m10 folded_cascode C:/g95b/m10_fc <out>`, 같은 스크립트 `trace`로 나머지 세 회로 → `p3v7_m10_mutants.folded_cascode.json`·`p3v7_m10_trace.*.json` | §2.3 표(M10 생존 실측) |
| F7v7 | `$PY D/p3_scripts/p3v6_amend_check.py C:/g95b/repo_m10 D/p3_doc_amendments.md C:/g95b/amend <out>` → `p3v7_amend_check.a796468.json`; `merge_gate.plan_tables_hash`(개정 전·두 안) | v7 문안(§2 새 문장 하나 추가) 적용 결과가 `p3v6_amend_check.a796468.json`과 키 정렬 동일, `plan_tables_hash` 셋 다 `7167e028…` |
| F1v8 | `$PY D/p3_scripts/p3v6_order_shim_sim.py C:/g113/repo <out> C:/g113/sim bottom7 pull`(`0f23786`) → `$PY D/p3_scripts/p3v8_e3b_synth.py C:/g113/repo C:/g113/sim/state_M9 <out>` → `p3v8_e3b_synth.json`; `bash D/p3_scripts/p3v8_sec10_selftest.sh D/draft_phase3_design_v8.md D/draft_phase3_design_v7.md C:/g113/repo <synth.json> <out>` → `p3v8_sec10_selftest.out.txt` | 모의 M1~M9: `order`·`shim` 새 문언 발견 0, 모듈별 단독 import 실패 0(v6·v7과 같음). **모의 F2 정정**: SD가 어느 유효 범위에서도 읽지 않는 재수출 51개만 지움(v7 `p3v7_e3b_synth.py`는 모듈 최상위 symtable `is_referenced()`만 봐서 함수 몸체에서만 읽는 재수출 11개 -- `load_topology`·`Transistor`·`kcl_series_union`·`find_stack_edges` 등 -- 까지 지웠다, `v7_overdropped_reexports`). v8 블록 E3b @ `syn/f2drop`: `LIVE moved_out=62 base_files_reading_moved_out=31 pre_existing=1` + FAIL **49줄·12파일**(§2.2 목록). 같은 블록의 제외 집합을 비운 측정 사본: `.ai/verification/**` FAIL은 `df36…/e_lib_inst.py:35 save_instance_json`, `p9-kcl-edges/scripts/diff_dup.py:17 _import_analog_grammar`·`:32 _kcl_and_matching_edges` 3줄·2파일뿐(6개 `e_lib.py` 0), `probe_stage_partition.py` 4줄(D-9, 5차 검토 S2). v8 블록 @ base(HEAD = B0) `INVALID`, @ `syn/m9` `PASS`(`moved_out=62 … pre_existing=1`). 첫 실행(`p3v8_sec10_selftest.run1_overdrop.out.txt`)은 v7과 같은 과대 삭제 모의로 돌아 S2 측정이 `e_lib.py` 6개를 거짓으로 FAIL로 셌다 -- 정정 뒤 재실행이 위 값 |
| F2v8 | 같은 실행의 `syn/b2base`(`0f23786` + `workspaces/zz/star_reader.py`(`from stick_diagram import *`)·`dyn_reader.py`(`getattr(sd, name)`)·`parse_err.py`(구문 오류)) → `syn/b2head`(SD의 `find_structural_symmetry_candidates` def를 `A/zz_moved_sym.py`로, 재수출 없음, `structural_symmetry_probe.py:10`만 새 모듈로) | **v7 블록**: `E3b LIVE moved_out=1 base_files_reading_moved_out=1 pre_existing=4` + `E3b PASS`(5차 검토 B2 재현 -- 세 reader는 실행하면 `NameError`·`AttributeError`·`SyntaxError`). **v8 블록**: `pre_existing=1` + `E3b FAIL workspaces/zz/dyn_reader.py:3 <동적 이름>`·`parse_err.py:0 <PARSE-ERROR>`·`star_reader.py:1 *`, `PASS` 없음 |
| F3v8 | `bash D/p3_scripts/p3v8_einst_equiv.sh C:/g113/repo2 <synth.json> D/p3_scripts/e_inst_p3_proposed/e_inst_p3.py C:/g113/einst <out> [rest]` → `p3v8_einst_equiv.out.txt`(사본 sha256: df36 `6cc48495…`, p3 `7d26134a…`, e_lib `41b72d7d…`) | **`0f23786`(F1 전)**: 두 회로 모두 `e_inst_p3`와 `e_inst_df36` 출력 JSON의 다른 키 = `engine_origin` 하나(df36 `design_report`·`sizing_recipe`·`stick_diagram`, p3는 거기에 `topology_library`), stdout 사본 같음(`folded_cascode`는 바이트 그대로, 파일럿은 SLSQP 줄의 `elapsed=<초>s`만 달라 그것을 가리면 같음). `raw_sha256` `folded_cascode` `ef3cd996…`, 파일럿 `2fc426d9…`. **`syn/f1h`(근사 F2 + 하네스 import만 MOD로 -- `SemiEmpiricalGmIdLUT`→`gmid_lut`, `optimize_full_circuit_budget`·`diagnose_sizing_roles_gap`→`sizing_layout_convergence`, `dense_candidates`·`layout_grid_L_candidates`→`theta_search`, 나머지 4개→`instance_report_builder`)**: `e_inst_df36` 두 회로 모두 `KeyError: 'sizing_recipe'`(rc 1, 3~4초), `e_inst_p3` 두 회로 모두 rc 0·`raw_sha256`·`without_topology_ref_sha256`·stdout(가림)이 `0f23786`과 같음, `engine_origin` = MOD 9개(`sizing_recipe` 없음). **E-LIB** `e_lib.py` 사본: `0f23786`·`syn/f2drop`·`syn/f1h` 셋 다 `hash` `1d2e3bf6…`, 9회로 load·V1·V2 성공. 시간(경합 상태): `folded_cascode` 54~92초, 파일럿 434~779초 |
| F4v8 | `git -C C:/g113/repo2 grep -n -E 'spec_from_file_location\|run_path\(' 0f23786 -- '*.py'`; `git diff --name-only a796468 0f23786`; SD 최상위 `try`·`if` 문 AST 계수; `git status --porcelain --untracked-files=all -- '*.py'`(메인 저장소, 읽기) | 경로 로드 대상은 `run_harness.py`(`test_df35_harness_paths.py:163`·`test_selftest_stick_diagram.py:488`)·`review9_bias_dependent_net_scan.py`·`w_sites.py`·`runpy` 자기 실행뿐 -- 엔진 4파일 0(m7). `a796468`→`0f23786` 변경 2파일(승인 기록·P10b spec card, m6). SD 최상위 `try`·`if` 0(m2). 추적 안 된 `.py` = `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py` + `.claude/hooks/*` 4(S5). 게이트 phase 대조: `merge_gate.py` 532~549(`rule10_phase`)·1008~1010(V1 `--gmid-phase`) 읽기(S3) |
| F5v8 | `$PY D/p3_scripts/p3v6_amend_check.py C:/g113/repo2 D/p3_doc_amendments.md C:/g113/amend <out>` → `p3v8_amend_check.0f23786.json` | `p3v7_amend_check.a796468.json`과 키 정렬 동일(블록 21, '현재' 10개 일치, 두 안 표 4열·10행·`import_layering` exit 0) |
| F1v82 | `bash D/p3_scripts/p3v82_out/run_reach.sh`(`$PY -B -P D/p3_scripts/p3v82_relaxed_reach.py C:/g135/iso_r <회로> <out>`, `a796468`, SPECS 4회로) → `p3v82_out/<회로>.json` | 파일럿: `run_matching_safety_with_finger_growth` 1회, `relaxed_pairs` = `M4a/M4b` `interdig_ok` True·`M3a/M3b` False, 같은 값이 `save_instance_json`의 `pipeline_result["relaxed_pairs"]`로 넘어감; instance.json(92,573 B)·report.html(77,728 B)·stdout에서 `relaxed` 0·`interdig_ok` 0(`interdig` 48·30회는 전부 `interdigitation` -- audit 3b 체크 이름), instance.json 최상위 키 = `schema_version`·`topology_ref`·`sizing`·`netlist`·`floorplan`·`box_shape`·`audit_row_split`·`coverage`. `folded_cascode`: 호출 1, `relaxed_pairs` 빈 목록, instance.json `relaxed` 0. `two_stage_ota`·`nmcnr_amplifier`: 이 def 전에 하네스가 `ValueError`(KVL 합 불일치)로 멈춤, instance.json 없음(backfill card 초안 'library 회로 적용 여부'와 같음). 결론: backfill이 바꾸는 값은 E-INST·보고 산출물에 닿지 않는다(D-28 (e) ③) |
| F2v82 | `bash D/p3_scripts/p3v82_out/run_elib.sh`(`a796468` 복제본 `C:/g135/el_base`, 사본 sha256: `e_lib.py` `41b72d7d…`, `e_lib_p3.py` `c6b82fc7…`) → `p3v82_out/summary.txt` | `e_lib.py` `hash` `1d2e3bf6…` = `e_lib_p3.py`(인자 없음) = `e_lib_p3.py rails`; 두 `e_lib_p3` 출력에서 `masked_meta_keys`·`circuits.*.masked`를 빼면 `e_lib.py` 출력과 같음(동등), `rails` 실행의 `masked.rails` 9회로 모두 `<ABSENT>` |
| F3v82 | 같은 실행의 시제품 `C:/g135/el_p1`(`a796468` + SD 끝에 `RailDeclaration(nets: frozenset)`·`rail_declaration(topology)`, `load_topology`가 `meta["rails"] = rail_declaration(data)` -- B26-1 계약 1·2 모양), `el_p2`(nets에서 마지막 넷을 뺌), `el_p3`(p1 + `meta["_g135_unexpected"] = 1`); E-INST는 `el_base`의 `e_inst_df36`·`e_inst_p3`와 `el_p1`의 `e_inst_p3`; `bash D/p3_scripts/p3v82_judge_scenarios.sh D/draft_phase3_design_v8.md C:/g135/out_e C:/g135/js C:/g135/el_p1` → `p3v82_judge_scenarios.out.txt`(§10 E5 판정 python을 design에서 그대로 뽑아 실행 -- sha256 `37fecfea…` = `p3v82_e5_judge.py`) | 원래 `e_lib.py` `hash`: p1 `c1213331…`·p2 `e01c7b52…`·p3 `ab5be683…`(base `1d2e3bf6…`와 모두 다름, 9회로 모두 `per_hash.load`만 다르고 V1·V2 같음 -- `run_topology_pipeline` 반환은 meta를 담지 않는다). `e_lib_p3 rails`: p1·p2 `1d2e3bf6…`(base와 같음), p3 `58e3a1e8…`. E-INST: 파일럿 `raw_sha256` `2fc426d9…`·`folded_cascode` `ef3cd996…`가 base df36·base p3·p1 p3 셋에서 같음(`rails`는 instance.json에 닿지 않는다; 값은 F3v8 `0f23786`과도 같음). 판정: p1 `E5 E-LIB/E-INST PASS`; p2 `E5 E-LIB rails 계약 FAIL` 9줄 + `FAIL`; p3 `E5 E-LIB(rails 뺀 해시) 다름/실패` + `FAIL E-LIB`; 고장 입력(P2D `e_lib.py` `hash` 한 글자 변경) `E5 INVALID: e_lib_p3(MASK 없음) ≠ e_lib on P2D` + `FAIL`. 측정 시간(CPU 경합): E-LIB 4~6초, E-INST `folded_cascode` 53~62초·파일럿 269~388초 |
| F4v83 | `a796468` 복제본 `C:/g149/el_base`와 시제품 `C:/g149/el_p1`~`el_p5`(`p3_scripts/p3v83_mkproto.py`, 실행 명령 `p3v83_out/run_elib.sh`·`run_einst.sh`, 로그 `p3v83_out/log_*.txt`: p1 = SD 끝에 frozen `RailDeclaration(nets: frozenset)`·`rail_declaration(topology)`, `load_topology`가 `meta["rails"] = rail_declaration(data)`; p2 = nets에서 마지막 넷을 뺌; p3 = p1 + `meta["_g149_unexpected"] = 1`; p4 = p1 + `RailDeclaration`에 계약 밖 필드 `polarity: str = 'junk-g149'`(7차 검토 S1); p5 = p1 + `two_stage_ota` library `supply_nets`에 `agnd`(7차 검토 m1)), 사본 sha256 `e_lib.py` `41b72d7d…`·`e_lib_p3.py` `c6b82fc7…`·`e_inst_df36.py` `6cc48495…`·`e_inst_p3.py` `7d26134a…`; E-INST는 `el_base`의 df36·p3와 `el_p1`의 p3; `bash D/p3_scripts/p3v83_judge_scenarios.sh D/draft_phase3_design_v8.md D/draft_phase3_design_v8.v8.2.md C:/g149/out_e C:/g149/js C:/g149/el_base a796468 C:/g149/el_` → `p3_scripts/p3v83_judge_scenarios.out.txt`(v8.3 판정 python을 design에서 그대로 뽑아 실행 -- sha256 `ae6422d6…`; 대조로 v8.2 사본의 판정 python `37fecfea…`도 같은 입력에) | 원래 `e_lib.py` `hash`: base `1d2e3bf6…`, p1 `c1213331…`·p2 `e01c7b52…`(F3v82와 같음), p3 `e044f286…`, p4 `1ee707d2…`, p5 `9812155e…`(7차 검토 재현과 같음). `e_lib_p3 rails`: base·p1·p2·p4·p5 `1d2e3bf6…`, p3 `36d01e94…`. E-INST raw: 파일럿 `2fc426d9…`·`folded_cascode` `ef3cd996…`가 base df36·base p3·p1 p3에서 같음(F3v82와 같음). v8.3 판정: p1 `E5 E-LIB/E-INST PASS`; p2 `E5 E-LIB rails 계약 FAIL` 9줄 + `FAIL`; p3 `E5 E-LIB(rails 뺀 해시) 다름/실패` + `FAIL E-LIB`; **p4 `E5 E-LIB rails 계약 FAIL` 9줄 + `FAIL`(v8.2 판정 = `PASS`)**; **p5 `E5 E-LIB rails 계약 FAIL two_stage_ota` + `FAIL rails:two_stage_ota`(v8.2 판정 = `PASS`)**; 고장 입력(P2D `e_lib.py` `hash` 한 글자) `E5 INVALID: e_lib_p3(MASK 없음) ≠ e_lib on P2D` + `FAIL`; 없는 P2D 커밋(`git show` 실패) 9회로 모두 `rails 계약 FAIL`(기대 nets `None`, fail-closed). 측정 시간: E-LIB 4~6초, E-INST `folded_cascode` 55~59초·파일럿 417~480초 |
| F1v84 | (v8.4, 스크래치 `C:/g164`) `git -C R rev-parse gate/master` → `5f643a9`(작업 시작), 끝에 `dd60db6`(`git diff --name-only 5f643a9 dd60db6` = 승인 기록·spec·interface card(V3 면제 묶기)·`.ai/context.md`·계획서(839행 한 줄)·design 05·10 각 한 줄·`phase2-dod.md` -- `git diff --quiet 5f643a9 dd60db6 -- skills tools workspaces <레지스트리>` 0, `dd60db6`에서 문서 개정 v8.4 블록 재적용 결과 = `5f643a9` 판); `git diff --name-only 0f23786 5f643a9`; 새 추적 `.py`의 엔진 모듈 이름 grep; `git ls-files --others --exclude-standard -- '*.py'`; `$PY D/p3_scripts/p3v6_amend_check.py C:/g164/repo D/p3_doc_amendments.md(v8.3 판) …` | 바뀐 파일 = 승인 기록 3·`.ai/context.md`·history·design 20(§10 E2 문구·§11-1)·spec·interface card(md 일치)·`_TEMPLATE`·레지스트리(§8 덧붙임 522행 뒤 -- 목적지 열 무변경)·library `topology.md` 2·test 2(`test_reg_check_df23.py`·`test_topology_md_sync.py`)·`tests/tools/reg_check.py`·판정 기록. 엔진 `A/*.py`·`tools/`·계획서 본문 0. 새 test·판정 기록 `.py`의 엔진 모듈 import 0(`reg_check`만). 추적 안 된 `.py` 5개 그대로(U-03 1 + hooks 4). 문서 개정 '현재' 10개 일치, 결과 JSON = `0f23786` 판(키 정렬 동일) |
| F2v84 | (v8.4) 복제본 `C:/g164/repo`(= `5f643a9`)와 `C:/g164/fut`(+ DR 28행 앞·ACF 38행 앞에 `from __future__ import annotations`, 커밋 `03bfbe0`): 전체 test `python -P -m pytest -c tools/gates/pytest_gate.ini … --gmid-phase=2 --gmid-strict= --junitxml`; 컴파일 대조 스크립트(두 파일을 future 없이/있게 `compile`, qualname별 코드 객체의 `co_code`·상수·이름·지역·플래그(future 비트 제외) 비교, import 뒤 `__annotations__`·모듈 이름 비교); base 판 `mutate_changed.py`·`source_lint.py`·`reachability.py`(base `5f643a9` → head `03bfbe0`); 같은 체크아웃 경로 `C:/g164/iso`에서 두 판 차례로 `e_lib.py`·`e_inst_p3.py`(파일럿·`folded_cascode`); `git grep -E "get_type_hints\|__annotations__\|annotationlib\|get_annotations\|inspect\.signature"` | 두 판 1047 passed·15 xfailed(271~275초), test id 1062 결과 차이 0. 몸체 코드 객체 같음 DR 12·ACF 5, 다름 = `__annotate__`만(DR 5·ACF 4), `__annotations__` 값 대 문자열 DR 5·ACF 4 함수, 모듈 이름 차이 `annotations` 하나. V3 PASS 대상 2파일·변이 0, V6 PASS 발견 0, V7 PASS `new_defs` []. E-LIB `hash` `1d2e3bf6…` 같음, E-INST 두 회로 출력 22키 모두 같음. 주석 조회 대상은 SD·SR 함수뿐(DR·ACF 0) |
| F3v84 | (v8.4) `C:/g164/fb`(= `03bfbe0`)·`C:/g164/fp`(+ `g1_kit/install_proto.py`, `g1_core.py` `b3c4e391…`) → `$PY D/p3_scripts/p3v6_order_shim_sim.py C:/g164/fb <out> C:/g164/simw` → `$PY D/g1_kit/m9_classify.py C:/g164/fb C:/g164/fp C:/g164/simw <out>` | 모의 M card 거부 raw M1 2·M2 6·M3 29·M4 0·M5 0·M6 4·M8 0·M9 16(원인 multi·연쇄만 -- `__future__` 0), dedup(이름마다 import 한 번) **M1~M9 전부 0**. 대조: G1 착수 키트 `0f23786`(future 없음) dedup 뒤 M2 1·M4 1·M9 7(전부 `__future__`) |
| F4v84 | (v8.4, D0b 착수 키트 재현·확장) `C:/g164/d0b` = `5f643a9` + `p3kit_d0b/apply_n310_amend.py`(UD-0 (a)~(d) (가))(커밋 `7b92d14`) + G1 시제품(`install_proto.py`) + D0a 시제품 `p3kit_d0a/move_plan_proto.py`(`d2f3da97…`)를 `p3kit_d0b/mk_variant.py`로 변형한 사본에 규칙 스위치를 더함(스크래치 전용: 모듈 docstring 제외, A-2·A-5 승격, A-3·A-4 칸 값 먼저 앉히기(단조), A-7, MOD7 상한 -- 패치 내용은 `phase3_revision_log.md` 'v8.3 → v8.4'); N3.10 토큰 보정은 같은 복제본 계획서에 커밋별로 적용, 레지스트리는 매번 `7b92d14` 판으로 되돌림; `p3kit_d0b/analyze_plan.py`; 재생성 `p3kit_d0b/regen_registry.py --write` | 규칙 그대로: `upward` 34·`cycles` 1·`unassigned` 18(키트 재현). A-K+A-6+A-4 승격: 7·1·6(키트 재현). + docstring 제외·A-2/A-5 승격·단조: `upward` 7(원천 모두 A-1: `_METRICS_REGISTRY`→`_metric_nulling_resistor_ohm`, `SemiEmpiricalGmIdLUT`→`_multilinear_interp_point_multi`, `_build_theta_evaluator`→`resolve_stack_layout`, `apply_theta_feed`→feed 레지스트리, `require_declared_spec_source`→`spec_fingerprint`, `validate_metric_units`→`metric_unit_scale`, `load_topology`→`propose_device_roles_gap_fill`)·`unassigned` 3. 문서 개정 §1·§9 보정 8건(토큰 11개) + A-7(+ 상한): `upward` 0·`cycles` 0·`unassigned` 0·`conflicts` 0·`import_time_high` []·MOD7 밖 0·배정 403·`reg_mismatch` 78(상한 있음/없음 같음); MOD6 넷 중 하나만 옮김 4·셋 1; `find_hub_merge_candidates` 토큰 없이(상한) 2. 재생성 커밋에서 `plan` exit 0·`reg_mismatch` 0·사상 차이 0. 개정 뒤 칸과 달라지는 A-4 단위 32. 단조 앉히기 없이 돌리면 반복 순서에 따라 `_feed_metric_stage_budget` MOD4 → MOD6(관찰). 문서 개정 v8.4를 깨끗한 계획서에 적용: '현재' 13개 일치, 8행 토큰 집합 = 위 보정 표, 두 행 이상 토큰 0, `import_layering` exit 0, 표 4열·10행 |
| F5v85 | (v8.5, 스크래치 `C:/g185`) `C:/g185/d0b` = `dd60db6` 복제본(`git clone --no-local`, origin 제거, 빈 hooksPath) + 작업 트리 G1 시제품(`g1_kit/install_proto.py`, `g1_core.py` `b3c4e391…`). 브랜치 `amd84fu`(문서 개정 v8.4 §1 (a)(가)~(d)+§9 (e)~(g) + FU 두 줄), `amd85fu`(+ §9 (h)), `amd85nofu`(+ (h), FU 없음), `regen85`(`amd85fu` + `p3kit_d0b/regen_registry.py --write`). D0a 시제품 `move_plan_proto.py`(`d2f3da97…`)에 **D0a 계약 2 v8.4 문언만 보고** 규칙을 얹은 사본(스크래치 `mk85.py`: docstring 제외·A-3/A-4 칸 선착석·단조 올림·A-2/A-4/A-5 승격(R(u) 최댓값은 N3.10 번호만)·MOD7 상한·A-K·A-6·A-7·`import_conflicts` (i)(iii)(iv)), 개정 블록은 `p3_doc_amendments.md`에서 '현재' 정확 일치 단언 뒤 교체(`apply85.py`), `p3kit_d0b/analyze_plan.py`, design §6.3 `MP_ARGS` | `amd84fu`: `upward` 0·`cycles` 0·`unassigned` 0·`conflicts` 0·`import_time_high` 0·`import_conflicts` 0·MOD7 밖 0·배정 403·`reg_mismatch` 78, 규칙 분포 A-4 230·A-5 64·A-1 59·A-2 38·A-6 7·A-7 2·A-K 2·A-3 1 = F4v84·8차 검토 재현과 같음; `_kv_table` = MOD4(A-4). `amd85fu`: 일곱 목록 중 `reg_mismatch` 밖 여섯 모두 0·MOD7 밖 0·배정 403, **`_kv_table` = MOD9(`instance_report_builder`, A-1)** -- 다른 단위 사상 차이 0, `reg_mismatch` 79(`_kv_table` 칸 `gmid_sizing_engine` 1건 더함 -- 재생성이 고친다). `amd85nofu`: `import_conflicts` = `__future__` MOD2·MOD9 둘(v8.4는 MOD4까지 셋). `regen85`: exit 0·`reg_mismatch` 0·`import_conflicts` 0·사상 차이 0(멱등). m4 변형(같은 트리): 승격에 `--keep` 번호 포함(`V_KEEPINC`)·상한 끔(`V_NOCAP`) 모두 사상·규칙 차이 0. 칸과 달라지는 A-4 단위 32 그대로(MOD2→MOD3 12: `propose_device_roles_gap_fill`·`propose_theta_kcl_gap_fill`·`propose_vertical_stack_id_gap_fill`·`_propose_L_roles`·`_propose_gm_id_roles`·`_propose_vertical_stack_ids`·`check_symmetry_dispositions`·`refine_differential_and_mirror_relations`·`find_verified_differential_and_mirror_relations`·`audit_vertical_stack_id_vs_kcl`·`suggest_vertical_stack_composites`·`resolve_constraint_references`; MOD4→MOD5 11·MOD6→MOD8 4·MOD3→MOD4 3·MOD4→MOD9 1(`save_html_report`)·MOD2→MOD8 1(`diagnose_sizing_roles_gap`)). 메인 저장소 `git status` 전후 같음 |

측정 한계: M14는 초안 배정 기준·`ast.Name` 참조만. G1은 '파일 전체가 새 파일'인 상한. G5·G6의 v3 결과는 **참조 구현 모의**다(게이트 도구 자체는 바뀌지 않았다) -- G1 card의 red-green이 실제
판정이다. G6은 '같은 디렉터리 통째 이동'이라 실제 card의 부분 이동과 다르다(부분 이동의 거짓 거부는 M-4 고정점에서 '함께 옮겨야 할 것을 안 옮긴' 경우뿐이고 그것은 PLAN-LAYER·
`move-set`이 먼저 잡는다).
v4 추가 한계: G5'·G6'의 v4 결과와 D0a `check` 발견도 **참조 구현 모의**다(`move-set`·`order`·`shim`·`cache`는 이관표·MOD 표가 필요해 모의하지 않았다). '반례 전부 거부'는
합성 반례 51단계 + 엔진 통째 이동에 대한 측정이지 규칙의 완전성 증명이 아니다 -- 그래서 Phase 3 안에서는 `check`와 card별 V3 `defs` = `[]`이 두 번째 선이다(§9.2 UD-5).
v6 추가 한계: F1v6의 이관표는 규칙의 **근사 구현 + 모의 보정**이라 D0b 결과와 다르다(배정 수·완전 shim card는 D0b가 정한다). 이 모의가 보이는 것은 '규칙을 지키는 배정이면 새 `order`·`shim` 문언과 D-22 배치로 M1~M9가 통과할 수 있다'와 'SD → MOD9 임시 재수출이 순환을 만든다'(구조 사실: N3.10이 `save_instance_json` 계열을 MOD9로 보내고 test가 그 이름을 SD에서 읽는다)이다. B26-1·B34 병합 전 트리다.
v8 추가 한계: F1v8·F3v8의 F2·F1 모의는 근사 배정 + 하네스 한 파일의 import 교체뿐이다 -- 깨지는 판정 기록 스크립트 수(2)와 E3b FAIL 목록은 D0b 배정에서 달라질 수 있다(판정 근거 아님). F3v8은 `e_inst_p3`가 F1 뒤에도 돌고 F1 전에는 df36과 같은 값을 낸다는 것을 보일 뿐, Phase 3 동작 보존의 증거가 아니다(그것은 DoD E5). v7 F1v7·F2v7의 'F2 FAIL 88줄'과 그 파일 목록은 과대 삭제 모의의 결과라 v8에서 대체했다(F1v8).
v8.3 추가 한계: F4v83의 p4·p5도 계약 모양 시제품이다(B26-1 실물이 아님). 보이는 것은 '고친 판정 python이 계약 밖 필드와 P2D 대비 library `supply_nets` 변경을 거부한다'이고, v8.2 판정 python이 같은 입력을 받아들였다는 대조다. E-INST 입력은 v8.2와 같은 실측 모양(P2D 대용 `a796468` df36·p3, HEAD 대용 p1 p3)을 `C:/g149`에서 다시 떴다.
v8.2 추가 한계: F3v82의 HEAD 대용은 B26-1 계약 1·2만 흉내 낸 시제품이다(B26-1 실제 병합본이 아니다 -- SR 소비처·접근자 거부 규칙 없음). 보이는 것은 '판정 python이 계약 모양의 `rails` 추가를 받고, nets가 틀리거나 다른 meta가 바뀌면 거부하며, 동등 확인이 고장 입력을 INVALID로 낸다'이다. 실제 P2D·HEAD 값은 DoD E5가 잰다. F1v82는 `a796468` 엔진(backfill 수정 전)에서 값이 '저장 함수까지 가고 파일에는 없다'를 보인 것이고, backfill 뒤에도 `save_instance_json`의 키 집합이 같다는 것은 그 card 초안(엔진 수정 = backfill 호출 줄 삭제뿐)에서 온 추론이다 -- 어긋나면 E5 (ii)가 FAIL로 드러낸다.
v7 추가 한계: F1v7~F3v7의 합성 커밋은 **근사 배정 모의 트리**에서 만든 것이라 E3b의 FAIL 목록·`moved_out` 수는 D0b 배정과 다르다(판정 근거가 아니다 -- 명령이 거부와 수용을 모두 하는지,
도구 오류를 FAIL로 내는지를 보인다). F6v7의 M10 변이는 지금 `run()`의 변이이고 M10 진입점은 아직 없다 -- 옮길 문장이 같으므로 생존 모양의 추정 근거로만 쓴다. 측정 시간은 다른 측정과 겹친
상태(CPU 경합)라 판정 기록의 E-INST 시간(`folded_cascode` 13~19초)보다 길다.

## 부록 B. 초안 v1(`draft_phase3_design.md`, 070cf69) 대비 정정

초안 v2 부록 B 그대로(12항목: A군 3파일, D-9, D-10, UD-4 흡수, 도구 하나, PLAN-LAYER 정밀 해석, M-1~M-3, B28 편집 지점, card 15, E0, D-5 근거, 줄 수).

## 부록 C. 초안 v2 대비 정정(검토 `review_phase3_drafts.md` 반영 -- 발견별 대응표는 `phase3_revision_log.md`)

| # | v2 | v3 |
|---|---|---|
| 1 | MOVED = M-1~M-3 | M-0(덮어쓰기)·M-4(전역 출처, `__file__`)·클래스 골격 단위·문장 해시 식별 추가(B1·B2·B3·S3·m8). 반례 26단계 재실행(G5, v6 정정), 실제 엔진 거짓 거부 0(G6) |
| 2 | D0a `plan`의 Phase 중·후 동작 미정 | A-0 현재 위치, `absent_split`, `reg_mismatch`(REG-DEST) -- D0b test·E4가 Phase 전 구간에서 성립(B4) |
| 3 | E2 = V3 `targets`의 def 0 | V3 재실행 JSON `defs` = []·`mutants` = 0·`move_rejected` 비어 있음 + `check` 발견 0 + `moved` 대조(B5) |
| 4 | design·D0a CLI 불일치 | D0a 계약 1이 정본, design은 요약·`MP_ARGS`(B6·m3) |
| 5 | 판정식 CACHE-ID·SHIM·MOVE-TOTAL 도구 없음 | `check`의 `cache`·`shim`(정적 출처 동일성), E6 `--card ALL`(S10) |
| 6 | M10 equivalence, 판정 결정 미룸 | 인벤토리 실측(이름 과대 근사뿐) → red-green(S12, D-15) |
| 7 | probe 속성 덮어쓰기 미기재 | §7.2 D군 8파일, F8, UD-7(S11) |
| 8 | M card 판정 도구 = 병합본 `tools/migrate` | D0a 병합 커밋 사본, M card `tools/**` 변경 0(S9, D-16) |
| 9 | 문서 개정 커밋 시점 불명 | spec card와 같은 커밋(승인 전), `diff_path` 세 경로(S4) |
| 10 | `lru_cache` 2곳, 게이트 밖 호출 4곳 | 1곳(248행), 3곳(m1·m2) |
| 11 | E3 줄 머리 import만 | 문자열 import 패턴 추가(m7) |
| 12 | UD-5 게이트 승인만 | 전역 규칙 대 선언 이동의 비용 비교와 권고 추가 |

## 부록 D. 초안 v3 대비 정정(2차 검토 `review2_phase3_v3.md` 반영 -- 발견별 대응표는 `phase3_revision_log.md` '초안 v3 → v4' 절)

| # | v3 | v4 |
|---|---|---|
| 1 | MOVED = M-0~M-4, V3·V7 제외 = `<경로>::<qualname>` 키 | **M-0h**(목적 파일에서도 유일 바인딩), p_b·p_h qualname 중복 def 제외, V3·V7 제외 대조 = (경로, qualname, `def_hash`)(B1). 새 부류 9단계를 G1 redteam에 추가(29단계) |
| 2 | `MP_ARGS="…"` 문자열, 명령 `$MP_ARGS` | 배열 `MP_ARGS=(…)`, 명령 `"${MP_ARGS[@]}"`(B2, 부록 A B2 실측). D0a 계약 1에 셸 사용 문장 |
| 3 | `binding_origin`: `unbound` 경로 없음, `ext` 디렉터리 없음, star는 바인딩 없을 때만 | `global` 선언 이름 = `global-dynamic`(경로), `ext`·`ext-module`에 가져오는 파일 디렉터리, star import가 있으면 모든 이름 `star`(S1 (a)(b)(c)) |
| 4 | 바인딩 = def·class·대입·`for`/`with` 대상, 문장 단위 전역 읽기 = 모든 `Name`(Load) | 모듈 공간 `Store`/`Del` 전부 + import·`except as`·`match` 포획·`type`, 문장 단위도 유효 범위 규칙(S2) |
| 5 | `__future__` 차이 미검사 | M-4가 기능 집합 대조, `check` `future` 발견, 엔진 사실에 TL 24행(S3) |
| 6 | `move-set` = `--card` 목적지 옮긴 단위만 | 이 base→head의 **모든** 옮긴 단위 = 배정, 목적지 전부 `--card`(S4) |
| 7 | 같은 경로 import 교체가 Phase 3 안에서도 사각 | `check` `rebind`(모든 head 단위 출처 = base 출처)(S5) |
| 8 | 옮긴 클래스 메서드 본문 변경은 E2까지 안 드러남 | M card마다 V3 `defs` = `[]`, `check` `changed`가 옮긴 클래스 안 def까지(S6) |
| 9 | D0a 계약 8(b) `assignment` 동일(문자 그대로 거짓) | (단위 키 → `mod`) 사상 동일(파일 부분·`rule` 제외), 문장 단위 키 정의(S7) |
| 10 | B28 병합 전 사실(`cd64170`, 줄 50~62·321·326, `copytree`, redteam "B28이 31") | `7535799` 재측정(88~100·359·361·364·407, `make_clone`), B28 병합 완료, redteam G1 = 32·B33 = 33(D-18), P9·P10 뒤 재측정 조건(S8) |
| 11 | D군 "대입 12줄", 문장 순서·main 블록 미검사, E6 base "첫 card base", E2 ③ 증거, 사본 출처 두 문언, 규칙 이름 관찰 방식 없음 | 14줄(m1), `check` `stmt-order`(m2)·`shim` main 블록(m3), E6 base = M1 판정 기록 `base_commit`(m4), ③ = 일관성 점검(m5), 사본 = `move_plan.py`를 마지막으로 바꾼 판정 기록 `code_commit`(m6), redteam `observe: "moved"`(m7) |
| 12 | 사용자 결정 5개(UD-0·1·5·6·7) | 3개(UD-0·1·5): UD-7 → D-17, UD-6 → 뒤에 올 승인. UD-5 권고 근거를 v4 수치로 다시 씀(2차 검토 §5) |

## 부록 E. 초안 v4 대비 정정(v4 뒤 확정된 결정·card 반영 -- 대응표는 `phase3_revision_log.md` '초안 v4 → v5' 절)

| # | v4 | v5 |
|---|---|---|
| 1 | B26-1·B34와 Phase 3의 관계 없음, 재측정 조건 = P9·P10 뒤 | A2(승인 기록 `20260930-b26-before-phase3`): B34 → B26-1을 M1 전 착수 조건으로(§9.1, '재검토' 절 인용). 두 card가 바꾸는 사실을 초안에서 추정해 §6.4 표로 두고 'Phase 3 시작 때 재측정'. **D0b는 두 card 병합 뒤 master에서 이관표를 처음 계산**(§6.4·§8 D0b행·§9.1) |
| 2 | `rail_declaration`·`RailDeclaration` 배정 미정(단위가 없었다) | D-19: N3.10 MOD2 '대표 대상'에 `rail_declaration`(A-1, UD-0 문서 개정), `RailDeclaration`은 A-2로 MOD2. 규칙만이면 A-5로 MOD3가 되어 MOD2 책임(스키마·선언 게이트)과 어긋남. B37a 접근자도 MOD2(§6.4) |
| 3 | §7.1 A군 3파일, §7.2 "contracts에 속성 덮어쓰기 0"(대입문만 셈) | B26-1 계수 test(`stick_diagram.rail_declaration` 모듈 속성 교체)를 A군(T0 계약 10)으로, B34·B26-1 test의 모듈 이름 호출을 B군(F1)으로. HEAD `setattr` 0건 실측(E3), S11을 `setattr` 형태까지 재측정 |
| 4 | G1 base = B28 병합본 `7535799`, 다른 게이트 card와의 합성 없음 | §5.5: B33·면제 묶기·범위 정책이 G1 전에 병합, G1이 나중 card로서 합성 문장을 가진다. V3 = 옮긴 def 먼저 제외 → 나머지에 N2(§5.5.2), 옮기며 바뀐 def·거부 후보 = 새 def 본문 전체(D-20), 면제 대조 불변(D-21, 변이 id 모듈 = 파일 줄기 실측 E2), B33 그래프 불변·바인딩 노드·재수출 규칙(§5.5.4) |
| 5 | §5.4 V7 `__init__`·레지스트리 간선 = 백로그 | B33이 G1 전에 닫음. F5·§5.1의 V7 미도달 108은 B33 뒤 재측정(시제품 추정 약 39) |
| 6 | redteam 번호 G1 32·B33 `33-v7-graph-edges` | G1 32·B33 `33-v7-registry-edges`·면제 묶기 `34-v3-exempt-binding`·범위 정책 `35-v3-changed-scope`(D-18 개정). 세 card 초안의 번호 정정은 그 card 몫(§11-8) |
| 7 | M card·E2 V3 기준 `defs` = `[]`·`mutants` = 0·`move_rejected` = `{}` | + `not_targeted` = 0·`targets_by_def` = `{}`(범위 정책 키). 면제 묶기 키는 기준 아님 |
| 8 | §8.1 순서도 G1·T0·D0a만 | Phase 2 쪽 선행(P9 → P10 → P10b → 면제 묶기 → 범위 정책 → B34 → B26-1)과 B33 → G1을 그림에 넣음. T0는 B26-1 뒤 |
| 9 | §10 `CARDS` 정의 줄 중복 | 한 줄로(편집 잔재 정리) |

## 부록 F. 초안 v5 대비 정정(3차 검토 `review3_phase3_v5.md` 반영 -- 대응표는 `phase3_revision_log.md` '초안 v5 → v6' 절)

| # | v5 | v6 |
|---|---|---|
| 1 | ORDER = "`--split` 파일이거나 번호가 같거나 큰 MOD"(M8·M9가 `stick_diagram` import로 통과 불가 -- B1) | N3.10 파일은 split이어도 N3.10 번호로 판정(SD = 7), N3.10 밖 split 파일만 금지. 모의 M1~M9 발견 0(F1v6). D0a 합성 단계 추가 |
| 2 | SHIM = "docstring과 `from <MOD> import` 밖 문장 0"(중간 card마다 발견, `__future__` 줄도 -- B2) | (a) 중간 상태: base에 없던 문장은 재수출 줄뿐 (b) 완전 shim(단위 0개)만 docstring·재수출·`__future__` (c) 이름 집합·출처 동일성(ALL은 이름 집합 빼고). 모의 M1~M9 발견 0. D0a 무동작 문장과 모순 해소 |
| 3 | §10 명령이 표 칸 안(`\|`로 공허 PASS -- B3) | bash 블록이 정본, E3 거부 확인(base에서 비지 않음), E3 = AST(import 문장 + import 호출) -- 정규식이 놓친 6파일·docstring 거짓 FAIL 해소(D-24), `<캐시>` 정의·`--gmid-phase=3` |
| 4 | UD-0 문서 개정 문안 없음, N3.10 개정 시점 모순(B4) | 문안 `_drafts/p3_doc_amendments.md`(7문서), UD-0 = 3건 + D-19만, D0b 추가 개정은 따로 승인(D-11), `validate_theta_declaration_order` → MOD3 확정 |
| 5 | (없음) | **D-22**: M9~F1의 SD ↔ MOD9 순환(모의에서 새로 드러남) -- 재수출·import 줄 위치 규칙, IMPORT-ANY 판정, LAYER는 F2 뒤 |
| 6 | 옛 문장: 세 card 번호 32·32·33, B33 chase '권고', 인벤토리 79,809, Phase 2 남은 것 "P9, P10, DoD E0~E5", G1 base 문장, 'design v4' 인용(S1·S2·S5) | 33·34·35 이미 반영, B33 34행 최종 문언, 44,493, §8.1 표와 같은 목록, base = 세 게이트 card 병합 뒤, 'design 30' |
| 7 | phase 3 card(T0·D0a·D0b) 병합 시점 미정(S2) | D-23: Phase 2 DoD PASS 뒤(계획 991행), 그 전은 준비만. §8.1 필수/편의 순서 분리 |
| 8 | M10 V3 비용·회로 미정(S3) | §2.3: 가장 싼 회로(기록상 `folded_cascode` 13~19초), 인벤토리 143초 실측, 추정 30~40분(최악 3.2시간), D-25, M10 '작성 전 실측' 항목 |
| 9 | D-19 근거에 무관한 문장(S4) | 근거를 '선언 게이트 + B37a 같은 곳'으로 좁히고 한계 기록, 중립 두 안으로 따로 질문 |
| 10 | "27단계", "51 = 27 + 24"(S6) | 26단계, 51 = 26 + 25 |
| 11 | 문자열 import 10곳 "전부 B군"(S7) | 호출 9곳 + docstring 1, F1 범위 = 9 |
| 12 | UD-1 대안 없음(S8) | (나) 추적 추가 후 F1 갱신 (다) 삭제 |
| 13 | card 수 15(m1), `<캐시>` 미정의(m2), F2 SD 재수출 규칙 없음(m3), SD 밖 MOD7 배정(m4), §8.1 순서 고정(m5), B34 212행 단정(m6) | 16, `GC`, SD 자신이 읽지 않는 이름만 지움, D0b 단언, 필수/편의 분리, D0b가 정한다는 인계 |
| 14 | 추적 import 파일 86(정규식) | AST 92(같은 6파일) -- F1 목록은 AST로 |
| 15 | UD-0 질문에 D-9·D-17·위임 미표시(검토 §7) | 질문 문안 `_drafts/phase3_approval_question.md`에 드러냄 |

## 부록 G. 초안 v6 대비 정정(4차 검토 `review4_phase3_v6.md`와 오케스트레이터 확정 순서 반영 -- 대응표는 `phase3_revision_log.md` '초안 v6 → v7' 절)

| # | v6 | v7 |
|---|---|---|
| 1 | F2가 SD 임시 재수출을 지운 뒤 깨지는 추적 파일을 DoD가 보지 않음(N1) | **E3b**(SD-NAMES, D-26): 추적 `.py`가 SD에서 읽는 이름(`from` import, 모듈 별칭·`import_module` 결과·그것을 돌려주는 함수의 속성, `getattr`류)이 head SD에서 모두 해석, 거부 확인 = base에서 SD 밖으로 나간 이름의 reader > 0. F2 oracle에 넣고 F1 범위를 이름 단위로(§7.2), F9. 합성 커밋에서 거부·수용·도구 오류 실증(F2v7) |
| 2 | E3가 도구 오류 때 PASS(S1) | `core.quotepath=off`·`-z`, `git show` 실패 = `ERROR` + 종료 코드 3, 셸이 종료 코드를 받아 `E3 FAIL(도구 오류)`. 비ASCII 경로 합성 커밋에서 v6 PASS / v7 FAIL |
| 3 | `import_any`가 목록 실패 때 일부만 봄(S2) | 목록 계산 실패·빈 목록 = INVALID, `tried` = `expected`(`import_layering` `present` ∪ 트리의 split 파일) 아니면 INVALID, 판정 기준에 그 줄. 고장 `GC`에서 v6 부분 보고 / v7 INVALID |
| 4 | M10 V3 추정이 '변이를 E-INST test가 죽인다'는 가정(S3) | 지금 `run()` 변이 71개를 `folded_cascode`로 실제 실행해 test 모양별 생존을 잼(§2.3), 회로별 도달 줄, '작성 전 실측'에 옮길 문장·추가 계약·비용, D-25 문장 정정(새 test의 회로만 정한다) |
| 5 | D0b~F2 사이 다른 엔진 card 규칙 없음, B26-2~4·B35 미기재(S4) | D-27 엔진 card 동결, B26-2~4 기본 F2 뒤(앞당기면 D0b 전), B35 F2 뒤(§6.4·§8.1·§9.1) |
| 6 | D-22 전제가 규칙으로 보장되지 않음(S5) | D0a `plan` 출력 `import_time_high`(계약 2) + D0b 계약 test 단언 + F3 처리 칸. 지금 0(F4v7) |
| 7 | 옛 base 문장(m1), D-9 "스크립트 6개"(m2), `test_dup_kcl_edges.py` 누락(m3), E3 첫 줄 SR만(m4), D-24 한계 없음(m5), 승인 질문(m6) | `a796468` 재확인 문장(승인 질문·G1·T0·D0a), `.ai/verification/**` E3 적중 0·SD 8파일, §7.1 B군 행, 세 파일 부재 확인, 한계 문장 + `a796468` 0건 실측, UD-0 ②·④ 문장 |
| 8 | §8.1 필수/편의 순서, §9.1 "Phase 2에 남은 것 = P10b·B34·B26-1" | **확정 순서**(오케스트레이터 결정·사용자 지시): P10b → Phase 2 DoD → 34 → 35 → B34 → B26-1(test 보강 card 포함) → B33 → Phase 3. B34·B26-1은 Phase 2 DoD 뒤의 앞당긴 card이고 Phase 2 DoD N6.3 목록에 들지 않음. D0b 재측정 = D0b 자신의 base. G1 → D0a 의존 유지(§11-12 확인 요청), 두 card `phase` 값·A2 기록 문장 인계(§11-11) |
| 9 | (없음) | 이미 깨진 `stick.py:12 block_from_row_widths`(§11-10, E3b `pre_existing`) |

## 부록 H. 초안 v7 대비 정정(5차 검토 `review5_phase3_v7.md` 반영 -- 대응표는 `phase3_revision_log.md` '초안 v7 → v8' 절)

| # | v7 | v8 |
|---|---|---|
| 1 | §10 `PT` = 10 §10 정의 그대로(`--gmid-phase=1`), E4·E5·T0 oracle이 그것으로 돎(B1) | `PT3`(`--gmid-phase=3`) 함수 정의, E4 test·E5 전체 실행 = `PT3` + `PT3 --gmid-dod`(둘 다 실패 0), T0 무동작 입력 `PT3`. 선례 승인 `20260930-phase2-e4-phase` |
| 2 | E3b `pre_existing`이 표지 이름(`*`·`<동적 이름>`·`<PARSE-ERROR>`)까지 면제(B2 -- 합성 커밋에서 `PASS`) | `MARK` 표지는 `pre`에서 뺀다 -- base에 있어도 head에서 FAIL. 합성 커밋에서 v7 PASS / v8 FAIL 세 줄, 정상 M9 모의 PASS·base INVALID 유지(부록 A F2v8·F1v8) |
| 3 | E5 'E-LIB·E-INST 재측정이 Phase 2 DoD와 같은 해시', F1 뒤 측정 명령 없음(S1) | D-28: `e_inst_p3.py`(design 커밋에 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/`로 고정), E5 블록(동등 확인을 B0에서 먼저 → E-INST·E-LIB B0 대 HEAD). 비교 판을 Phase 2 DoD에서 B0로(B26-1 `meta["rails"]` 같은 사이 card의 의도된 변경을 세지 않게). 실측: F1 전 동등, 근사 F1 뒤 df36 `KeyError`·p3 같은 해시, E-LIB 근사 F2·F1 뒤 같은 해시(F3v8) |
| 4 | UD-0 (a) "판정 기록 스크립트 8개가 … 읽는 이름"이 깨진다(재지 않음, S2) | 8개 중 2개(`e_lib_inst.py`, `diff_dup.py`)만 깨짐 -- 근사 배정 모의 F2에서 E3b 식 실측(F1v8). 승인 질문·D-9·§9.2·문서 개정 §2 사실 문장 |
| 5 | §6.4·§11-11이 A2 ③ 충돌을 '오케스트레이터가 정리'로 인계, 머리·§8.1이 확정 순서 전체를 '사용자 지시'로 귀속(S3) | 승인 질문 별도 항목 A2-③(사실 5개, 기본안 card `phase: 3` + M card 전 유지 + 새 decision 기록, 대안 Phase 2 DoD 앞 `phase: 2`), §9.2 행 추가, Q-B34-PHASE 연결, 게이트 phase 대조 없음 실측. 귀속을 원문 범위로 좁힘 |
| 6 | D-25 '네 library 회로 중 가장 짧은 것' + §2.3 '두 회로 기록 없음'(S4) | E-INST 회로 집합(instance.json을 만드는 회로) 중 가장 짧은 것 = `folded_cascode`, 실패 경로 두 회로는 보조 회로로만. 옛 '기록 없음' 문장 삭제 |
| 7 | UD-1 경로 `workspaces/smoke_run_harness_session18_save.py`(S5) | `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py`(§7.2·§9.2·승인 질문) |
| 8 | D-27 동결 = 엔진 파일만, `GC` 주석이 다른 card의 `tools/gates` 변경을 가정하지 않음(S6) | 동결에 `tools/gates/**`·`tools/migrate/**`·레지스트리 목적지 열, 사후 강제 = E6(M1~F2 엔진)·E2 앞 `git diff --quiet "$B0" HEAD -- tools/gates tools/migrate`(INVALID)·E4 `reg_mismatch`; D0b~M1 구간은 덮지 않음을 명시 |
| 9 | minor | m1 승인 질문에 대상 판 해시, m2 E3b `symtable` 한계(SD 조건부 최상위 바인딩 0 실측), m3 §10 공통에 `export APPDATA`·`HOME`, m4 '뒤에 올 승인'에 M10 V3 생존 면제, m5 B37a '둘 예정', m6 기준 `0f23786`(엔진·tools·계획·레지스트리 무변경), m7 D-24 한계에 경로 로드(엔진 4파일 0) |
| 10 | (v7 측정 결함 -- v8 작성 중 발견) §2.2·E3b 행·부록 A F1v7·F2v7의 'F2 FAIL 88줄'·reader 목록 | 모의 F2가 SD 함수 몸체에서만 읽는 재수출 11개까지 지운 과대 삭제였다(모듈 최상위 symtable만 봄). 모든 유효 범위 참조 + 주석 이름으로 고쳐 다시 잼: 49줄·12파일(§2.2). 판정 명령은 바뀌지 않음 |
| 11 | (관찰) §2.3 (ii) 'stdout 전체 결정적' | `folded_cascode`는 결정적, 파일럿 stdout은 SLSQP `elapsed=<초>s`가 달라 바이트로는 결정적이지 않음 -- E5 동등 확인은 그 숫자만 가린다 |

## 부록 I. 초안 v8 대비 정정(6차 검토 `review6_phase3_v8.md` 반영 -- 대응표는 `phase3_revision_log.md` '초안 v8 → v8.1' 절)

| # | v8 | v8.1 |
|---|---|---|
| 1 | E5 비교 판 B0를 D-28(원칙 기본값)에 두고 "원리상 성립하지 않았다"(N1) | UD-0 '기준에 닿는 기본값' (c)로 옮김(§9.2 UD-0 행, 승인 질문). 기본안 B0 + card 판정 기록 사슬, 대안 = 선례 `20260930-phase2-e4-baseline` 기본안 모양(Phase 2 DoD 대상 커밋과 비교, 의도적으로 바뀐 필드만 계약값으로 따로 판정). 선례와 일치하는 쪽은 대안. D-28 (e)·§10 E5 문장을 'raw 해시 그대로는 성립하지 않는다'로 좁힘 |
| 2 | §10 E2 통과 기준에 `E2 INVALID` 없음 -- D-27 사후 강제가 판정에서 빠짐(N2) | E2 행 맨 앞에 "`E2 INVALID` 줄 없음(B0..HEAD `tools/gates`·`tools/migrate` 무변경 -- D-27)" |
| 3 | A2-③·§8.1 확정 순서에 backfill 결함 card 없음(N3) | 네 card(B34·b26pre·backfill `20261001-b26-backfill-interdig-final-audit`·B26-1), 순서 B34 → b26pre → backfill → B26-1(§8.1 코드 블록·표, §9.1 엔진 선행·재측정 (1), §9.2 A2-③ 행, §11-11, 승인 질문) |
| 4 | §11-11·승인 질문 (4)가 1008~1010행만 인용(N4) | card `phase`가 V1 `--gmid-phase`·`--gmid-strict`를 정한다(`merge_gate.py` 1042행 `strict_set`, 1210~1213행 `v1_command_check(..., phase=card["phase"])` -- gate `master` `0f23786` 재확인), 거부 위험 없음 |
| 5 | minor | m-a D-26 한계에 E3b가 놓치는 세 모양(`sys.modules` 별칭·lambda가 돌려주는 모듈·이름 바꾼 `import_module`, `0f23786` 노출 0건 재확인), m-b D-28에 `e_inst_p3.py` 출처 확인 범위 차이(경로 꼬리 조건·run 전 시점, 스크립트는 바꾸지 않음), m-c revision log의 B26-1 초안 줄 번호 |

## 부록 J. 초안 v8.1 대비 정정(오케스트레이터 결정 -- 대응표는 `phase3_revision_log.md` '초안 v8.1 → v8.2' 절)

| # | v8.1 | v8.2 |
|---|---|---|
| 1 | UD-0 (c) 기본안 = B0 비교(선례에서 고르지 않은 대안 모양), 대안 = 선례 모양(측정 명령 없음) | 기본안 = 선례 `20260930-phase2-e4-baseline` 모양(P2D = Phase 2 DoD 대상 커밋과 비교, 사이 card가 의도적으로 바꾼 필드만 그 card 계약값으로 따로 판정, 나머지 해시 같음), 대안 = B0 비교(같은 블록에서 `P2D=`만 B0로). 원칙: 같은 상황의 사용자 선택("둘다 기본안으로 진행해")을 따른다 |
| 2 | 빼는 필드 미정('B26-1 `meta["rails"]` 등', backfill `interdig_ok` 도달 미측정) | card 초안 계약에서 유도 + 실측: E-INST 없음(B34 계약 7, b26pre test-only, backfill `interdig_ok`는 instance.json·report에 0 -- F1v82, B26-1 계약 8), E-LIB `meta["rails"]` 하나(B26-1 계약 2·8, 계약값 `RailDeclaration(nets = supply_nets)`) -- D-28 (e), 판정 python `EXCL_INST`·`MASK_META` |
| 3 | E-LIB 측정 = `e_lib.py` 사본(키를 뺄 수 없음) | DoD E5용 `e_lib_p3.py`(`e_lib.py` + meta 키 빼기 인자 한 곳, design 커밋에 함께 -- 문서 개정 §8). 인자 없으면 `e_lib.py`와 같음(F2v82), E5 (i)이 P2D에서 먼저 잰다. M card는 `e_lib.py` 그대로 |
| 4 | §10 E5 블록 = B0 대 HEAD | P2D 대 HEAD, E-INST 키별 `field_sha256`·raw·without_topology_ref, E-LIB `rails` 뺀 해시 + 회로별 `rails` 계약값 판정(A2-③ (나)면 P2D에도 같은 값 허용). 판정 python을 design에서 뽑아 시제품 4입력에 실행(F3v82: PASS·계약 FAIL·해시 FAIL·INVALID) |
| 5 | §9.2 UD-0·승인 질문 UD-0 (c) | 기본안(Recommended)·대안 교체, 선례 인용, 새 스크립트 문서 개정 목록에 추가, '수정 요청' 예시 (c)를 B0로 |

## 부록 K. 초안 v8.2 대비 정정(7차 검토 `review7_phase3_v82.md`와 B26 묶음 답 반영 -- 대응표는 `phase3_revision_log.md` '초안 v8.2 → v8.3' 절)

| # | v8.2 | v8.3 |
|---|---|---|
| 1 | §10 E5 판정 python `rails` 계약 판정이 `__dc__`와 `nets` 성분만 봄(계약 밖 필드가 끼어도 PASS -- S1) | `hv == {"__dc__": "RailDeclaration", "nets": want}` 정확 일치. E5 행 (iv)·D-28 (e) 문장. F4v83 p4: v8.2 PASS → v8.3 FAIL |
| 2 | 계약값 `supply_nets`를 HEAD library에서 읽음(P2D~HEAD 사이 선언 변경이 안 보임 -- m1) | `git -C "$ISO" show "$P2D:…/library/<회로>.topology.json"`(판정 python 인자에 `$P2D`). F4v83 p5: v8.2 PASS → v8.3 FAIL, 없는 P2D는 fail-closed |
| 3 | 승인 질문 UD-0 (c) 기본안에 비용 문장 없음, '실측으로 확인'(m2) | 기본안 비용(빼는 필드 목록이 design 상수 -- 사이 card 계약이 바뀌면 design 개정 승인), '계약 모양 시제품으로 실측' |
| 4 | A2-③ 미결(승인 질문 다섯 번째 항목, §9.2 행·§11-11·§6.4 인계, D-28 (e) (나) 분기 -- S2) | **결정됨**(사용자 답 2026-10-01 B26 묶음 [card phase] "phase 3 + 정정 기록 (Recommended)", decision 기록 `20261001-b26-phase3-cards`): 승인 질문 네 항목, §9.2 A2-③ 행·§11-11 = 결정 사실(V1 `--gmid-phase=3`, strict 집합 빈 집합), §6.4 인계 문장 정정, D-28 (e) (나) 분기 삭제(`bv == hv` 허용은 대안 (c-2) B0 몫으로 남김) |
| 5 | 네 card가 어느 DoD 목록에 드는지 없음 | 네 card `phase: 3` → Phase 3 DoD N6.3 목록(`^phase: 3$`)에 든다, 기록 그대로 세고 다시 판정하지 않는다(§9.1), §8.1 표 행·D-23(design 30 승인은 기다리지 않음 -- 그 기록) |
| 6 | §6.4 '바뀌는 def'에 B40·C1·C2 없음, U3 면제와 M card 이동 관계 없음 | B40 반환 키 삭제(U4)·정리 C1·C2(U3) 추가. 면제 id의 모듈 접두 `stick_diagram:`은 M card 이동을 따라가지 않지만 옮길 필요 없음 -- B26-1 V3에서 쓰이고 끝나며(M1 전 병합), M card에서 그 def는 변이 대상이 아니고(E2 ① `mutants` = 0), DoD E2는 M card만 다시 돈다. 그 def를 바꾸는 뒤 card는 해시가 달라져 어차피 새 승인 |


## 부록 L. 초안 v8.3 대비 정정(승인 질문 전 마무리 -- G1·T0·D0a·D0b 착수 키트, D0b 검토, B26 후속 -- 대응표는 `phase3_revision_log.md` '초안 v8.3 → v8.4' 절)

| # | v8.3 | v8.4 |
|---|---|---|
| 1 | `__future__` 혼합(DR·ACF 9단위가 future 있는 MOD로 가면 G1 M-4 거부) 처리 없음 | §6.5·D-29: 준비 card FU(D0b 전, DR·ACF 머리 한 줄) 기본값, (가) M card V3·(다) 배정 변경 기각. 동작 불변 실측(F2v84), 모의 거부 0(F3v84). card 16 → 17(§8 표·§8.1·D-23) |
| 2 | MOD 파일 import 줄 생성 규칙 없음(모의가 같은 이름을 두 번 묶어 `multi` 거부) | D-30: D0a `plan` `mod_imports`(이름마다 import 한 번)·`import_conflicts`, `check` `import-dup`; §6.3·§8 D0a·M행 |
| 3 | G1 머리 수치 15,677·861·스크립트 3·29단계 | 15,650·859·4·31단계(G1 착수 키트 v9, §4 F5·§5.1·§5.2·§5.5.2·§8 G1행), G1 공개 `SourceIndex.tree`(D0a 착수 조건 해소) |
| 4 | T0 V5 승인 범위에 비교 완화 언급 없음 | §9.2 '뒤에 올 승인': 리터럴 변경 3 + 비교 완화 1(`len(...) == 1`) |
| 5 | 배정 규칙 A-0~A-5, N3.10 개정 3건 + D-19 | §6.2·D-31: docstring 제외·A-K·승격(MOD7 상한)·A-6·A-7·단조 고정점, '열 = 정본' → '칸 = 하한'은 질문에 사실로; A-1 충돌 보정 8건(토큰 11개)을 UD-0 개정에(D-11, 문서 개정 §1·§9). `_metric_*` A-5 문장 정정. 모의 `upward` 34 → 0·`cycles` 1 → 0·`unassigned` 18 → 0(F4v84) |
| 6 | §8 D0b 행: "전 행", "규칙 손적용 합성 입력", 판정 목록 이름 없음 | 대상 행/비대상 행, 실제 단위 표본 (d)-1(규칙마다 한 행 이상, 행 없는 표본은 `plan` `mod`만), 합성 입력은 D0a test, `근거 규칙` = 재생성 시점 규칙(형식 = D0a 규칙 ID 집합), 판정 목록 일곱(`import_conflicts`), `mod_imports`는 판정 밖, base 사슬에 FU, 멈춤 경로 목록별 |
| 7 | D-10 근거 '1항'만 | U-02 1항 원문 "보류(Phase 3 모듈 이동·Phase 4 배선)" 인용, 질문 UD-0에 처리 칸 9개 변경을 드러냄 |
| 8 | 기준 gate `master` `0f23786` | `dd60db6`(F1v84 -- `5f643a9` = P2D(Phase 2 완료 판정 `2eefda1`)까지·그 뒤 V3 면제 묶기 문서 모두 엔진·`tools/`·N3.10·레지스트리 목적지 열 무변경, 문서 개정 '현재' 일치) |


## 부록 M. 초안 v8.4 대비 정정(8차 검토 `review8_phase3_v84.md` 경미 m1~m4 + D0b 착수 키트 D0b-8 -- 대응표는 `phase3_revision_log.md` '초안 v8.4 → v8.5' 절)

| # | v8.4 | v8.5 |
|---|---|---|
| 1 | `_kv_table`(DR HTML 표 도우미)이 레지스트리 칸 `〃` 번짐으로 MOD4(A-4) -- 계층 위반 없음, 책임 불일치(D0b-8, 백로그 후보) | 문서 개정 §9 (h) N3.10 MOD9 토큰(UD-0이 덮음, D-11 행). 모의(F5v85): `_kv_table` = MOD9 A-1, 다른 단위 차이 0, 일곱 목록·MOD7 밖 0, 재생성 멱등. §6.5 갈리는 MOD 셋 → 둘 |
| 2 | §9.2 UD-0 행: D-31을 'v8.4 사실로 드러낼 것'에 둠(m1) | '기준에 닿는 기본값' 묶음(D-9·D-17·D-28·**D-31**)과 끝 열 '사용자 몫'에 D-31 |
| 3 | D0a 계약 2 승격의 R(u) 최댓값에 `--keep` 번호가 드는지, A-6 '같은 상한' 모호(m4) | D0a 계약 2·§6.2 A-4: N3.10 MOD 번호만, A-6은 승격·상한 공허, A-3 상한 없음 -- 실측과 같은 읽기(반대 읽기도 지금 트리에서 같음, F5v85) |
| 4 | 질문 (d) 32개 내역 없음(m2), ④ '9개 함수'(m3) | (d)에 내역(구조 제안 함수 12개 → MOD3 등), ④ '9단위(함수 8 + `_CSS`)'·주석 문자열화 읽는 곳 0, ④ 근거에서 E-LIB 뺌(m5 -- `e_lib.py`는 DR·ACF와 무관) |
