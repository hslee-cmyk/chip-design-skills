# 백로그 재감사 -- 계획 문서 전체 (2026-10-29, 계획 v6.38.4 열넷째 커밋)

사용자 지시(2026-10-29): "백로그에 있는 항목을 지금 규칙들과 원칙들로 다시 검증해서 불필요한 것들은 지우고 반드시 필요한 사항들은 바로 카드분배를 통해서 해결해."

판정 기준: 삭제 (a) 이미 닫힘 / (b) 재작성·대체로 대상 소멸 / (c) 원칙상 불필요 / (d) 물리 전제 틀림. 필요한 항목은 card 문언에 배정, 사용자 몫은 질문 후보(N5.3). 닫힌 행은 원문을 보존해 history H2로 옮겼다. 원칙: graph 단일 정본 1~7, O-153·O-165·O-169, DC/AC 분리, θ 기저 KVL(O-127), O-171 물리 검증.

반영 자리: worktree `wt/plan-v6384` 브랜치 plan/v6384 -- gain-budget 계획·history와 하위 계획 다섯(oracle-portability·graph-consumption·headroom-chain·offset-strategy·offset-trim)과 각 history.

## 0. 종합 집계 (계획 검증 4 전 -- 정정본은 §0.1)

| 묶음 | 대상 | 전체 | 삭제 | 필요 → card 배정 | 사용자 몫(질문) | 기타 |
|---|---|---|---|---|---|---|
| A | GB N5.2 DF-01~DF-37 | 37 | 35 (a 30, b 2, b·c 3) | 2 (DF-37 → LT-1 범위 (10), DF-18 → N6.2 단위 6 완료 조건) | 0 (DF-37 안 하위 질문 Q-A1 1) | -- |
| B | GB N5.3 I-* 열린 이슈 | 31행 | 27 (a 22, a·b 2, b 3) | 3 + 부속 1 (I-A13 → LI-1, I-A16 → SF-1 범위 9, I-H1 (i) → 새 card DR-1, IC11 → SD-1 완료 조건) | 4 (Q-1~Q-4) | 불확실 2 |
| C | GB 본문 미룬 항목 + N7.2 열린 U | 45 | 27 (a 16, 규칙 이관 3, b 4, c 3, d 1) | 5 (P9-M1 B4·B12 → IT-1 기본안, B13 → SF-1 범위 6 (e), GB-1834 → B4와 합침, supply_current → SF-1 범위 8, GB-2324 → 단위 9, U-122 → LA-0·HC-S) | 3 (Q-C1 AP-1, U-47, U-75) | 기존 card 소유 유지 4, 범위 밖 4, 불확실 2 |
| D | 하위 계획 다섯 | 57 | 27 | 22 (기존 card 확장·문언; 새 card 0) | 5 | 불확실 3 |
| **합계** | | **170** | **116** | **32 + 부속 1** | **12 (+ Q-A1 하위 1)** | 불확실 7 |

삭제 사유별(A~C): (a) 68 · (a)·(b) 2 · (b) 9 · (b)·(c) 3 · (c) 3 · 규칙 이관(열린 결정 아님) 3 · (d) 1 = 89. D 27행의 사유는 D 절 표(대부분 (a) 하위 계획 판 반영으로 닫힘, 일부 (b)).

card별 배정(상위 반영 포함): IT-1 범위 6·7(B4·B12 -- 기본안, ⚠ 대안: DT-1 또는 백로그 유지), SF-1(범위 6 (e) B13·범위 8 supply_current·범위 9 I-A16), LT-1 범위 (10)(DF-37), LI-1(I-A13), DR-1(새 card -- 원래 취지와 다름), SD-1(IC11), LA-0(U-122 측정), HC-S(U-122·`sat_threshold`), 단위 6 완료 조건(DF-18), 단위 9(GB-2324), WB-1 범위 3(HC-B1·`sat_threshold` 정의역·OP-B9 착수 실측), LA-1 범위 15(GC-B8 U17 ② 잔여), EO-1 완료 조건(OP-B3·N3.5-2), TB-1 착수 실측(GC-B7), OS-2(`constraint_rows`·PS-7 -- BL-OS-B9), GC-5(GC-B4 -- 승인 필요), oracle OP-3·OP-4·OP-5·OP-8·OP-0 design, TR-0T design(OT-B3·B6·B10). 문서만: DEC-96 (3) 온도 예외, E-20·E-21 소유 칸, U-107·O-119 후속 정정 표.

승인 대기(Status 목록에 추가): BL-DF37, BL-DR1, BL-NB1, BL-GC-B4, BL-OS-B9, P9-M1a, N5.3 Q-1~Q-4·Q-A1·Q-C1~Q-C5.

**원래 취지와 다름**: DR-1 새 card, IT-1 card 성격 확장(입력 공통모드 card에 S1·S1v 재계산 정리), SF-1 범위 6 (e) 확장, NB-1 삭제(O-76 (1) 미래 card), LT-1 범위 (10) 예외 계층 변경, N5.3 Q-1(U-67 (나) 일부 보류 권고), GC-5 '동작 보존' 문언 변경(GC-B4), `constraint_rows` writer를 옛 'OS-2 착수 선행 U17 ②'에서 OS-2 제작으로(OS-B9).

⚠ P9-M1 대안: (A) 기본안 IT-1 범위 확장 -- 층 순서상 S1·S1v를 처음 다시 쓰는 card라 둘째 생산자가 가장 빨리 사라짐; (B) DT-1 확장(분석가 권고); (C) 백로그 유지 -- 같은 입력 재계산이 graph 규칙 1·3 위반 상태로 남으므로 원칙과 충돌(⚠). 옛 '(다) 백로그(N6.17 꼴)' 참조는 N6.17이 그런 꼴을 정의하지 않아 잘못된 참조였고, 553행 문단을 교체해 지웠다.

불확실: G-18 유지 판단, SD-1 IC11 배정 근거(재감사 원문 'SD-1이 nmcnr를 원문 ±1 V로 옮김'은 SD-T1과 다름 -- 배정만 반영), U-76(CPG-1이 A' 판정을 대신하지 않음 → N6.2 A' 절로 표기), N3.12 폐기 절 이관 보류, U16 다섯 행 소유(GC-B9, GC-0a 실측 뒤), OP-B9 bin별 p0, OP-B14 생성기 판 출처.

## 0.1 계획 검증 4 정정 (2026-10-29, 계획 v6.38.4 열다섯째 커밋)

검증 4(`wt/_drafts/evidence/2026-10-29/plan_v6384_validation4.md`, 75/100, 잘못 지운 항목 0 -- 표본 25/25)를 오케스트레이터가 재판정했고, 그 결과를 전부 받았다. 위 §0 표는 검증 4 전 집계이고, 아래가 정정본이다.

| 항목 | 옛 판정(§0·A~D) | 정정 | 반영 자리 |
|---|---|---|---|
| `sctx.cache`(A 범위 밖 관찰) | 범위 밖, 배정 card 없음 | **필요 → 배정**: LA-1 범위 15 (iv)에 S3 색인 평가 키 부분(design 40 398-402)을 도입하고 `sctx.cache`·`computed_keys`를 삭제한다. 제작은 LA-1·OS-2 가운데 먼저 병합되는 card가 맡는다(조건부 제작 꼴, 새 순서 규칙 0) | GB LA-1 범위 15 (iv)·완료 11, N6.1 offset 행, OS PS-7·OS-2 행 |
| `sctx.cell_floors`(A 범위 밖 관찰) | 배정 card 없음 | **오판 정정**: 이미 graph-consumption GC-7 완료 조건 13이 소유한다(재감사가 GB만 봄) | GB LA-1 범위 15 (iv) 인용 |
| DF-18 | 필요 → N6.2 단위 6 완료 조건 | **재배정 → card OS-2**(`run_plan`이 엔진 사슬 진입점 정본, S-9 W-1). 엔진에 없는 `pipeline/entry.py` 참조는 지웠다 | GB 단위 6·N5.4·MOD10 행, OS-2 행·W-1 |
| GC-B9(D 불확실) | 불확실 | **확정 (나)**: `ly_rows`·`ly_dispositions`·R6 → LI-1 범위 (9). `start.*`·`graph/start`·`dc_scc_log`·`dc_tie_breaks` → GC-7(진입점 도달이면 출력 전용 선언, 아니면 O-153 삭제) | GC N3.2 표 card 칸, GB LI-1 (9) |
| IC11(B 부속) | SD-1 완료 조건(2레일), 3레일은 단위 10 | **재배정 → card SF-1 완료 (5)**: 엔진 card이고 2·3레일 모두 맡는다. 범위 = 절대 전위로 선언된 값 전부(레일·입력 DC·바이어스·V_ref 등)를 같은 Δ만큼 옮긴다. SD-1에는 data 기록만 남는다 | GB SF-1 완료 (5), SD-1 (6), 단위 10 |
| Q-2 (b) 저항 기생 C | 사용자 질문 | **원칙으로 정한 기본안 = 넣음 → SF-1 범위 9**. 물리: 분포 RC의 Y 파라미터를 양 끝 C/2로 근사하고, 값은 셀 모델 crpf·crpfsw에서 온다. 정확도는 분할 사다리 대 RS-1 분해능으로 판정한다 | GB SF-1 범위 9·완료 (d)(e), N5.3 Q-2 (a)만 |
| Q-A1(DF-37 하위) | 사용자 질문 | **원칙으로 정한 기본안 (가) → LA-1 범위 15 (g)** | GB LA-1 범위 15 (g)·완료 11 (b) |
| B12(P9-M1) | IT-1 범위 6 (a) | **재배정 → DT-1**(순수 리팩터링). B4는 IT-1 범위 6 (b) 그대로 | GB N3.3·IT-1 범위 6·DT-1 범위·완료 (8) |
| DR-1 | 새 card | 새 card는 유지한다. 근거 문장을 정정하고, 착수 조건 = Q-C4(U-75 heldout 선정), 범위 조건 = DC 원소가 값 선언·θ 저항·게이트뿐 | GB N6.36, N6.1 DR-1 행 |
| oracle `supply_current_A`(C GB-2062 (i)) | GB SF-1 범위 8에만 있음 | oracle-portability OP-11 판정 기준을 '정의를 바꾼 칸'으로 받음(정의 하나) | OP 477·513, GB 304·691·2189 |
| U-23 | 삭제 (d) | **삭제 (c)**: L 혼합 행의 물리 결과는 LY4·LI-1 (6)이 소유한다 | GB N5.3 Q-C2·U-23 |
| I-B12 불확실 잔여 | 삭제 (b), 소유 없음 | 삭제는 유지한다. 잔여 검사 = LI-1 완료 (10)(PYTHONHASHSEED 두 값 비트 동일) | GB LI-1 완료 (10) |
| DS-U9(D 질문) | 사용자 질문 | **원칙으로 정한 기본안**(NFR-4: 유도 실행은 결정성 요구 밖 표기 유지). 변경만 묻는다 | OS N10 DS-U9, GB U-47 |
| OP-B14 | 불확실, 앞당김 권고 | 소유 = OP-3 착수 조건, 앞당김 안 함 | OP N9 |

**정정 뒤 집계**:

| 구분 | 수 |
|---|---|
| 전체 | 170 |
| 삭제 | 116 |
| 삭제 사유 (A~C 89건) | (a) 68, (a)·(b) 2, (b) 9, (b)·(c) 3, (c) 4, 규칙 이관 3, (d) 0 |
| 배정 | 36 + 부속 1(옛 32 + 1에 `sctx.cache`·Q-2 (b)·I-B12 잔여·GC-B9 확정을 더함; 재배정 4건 DF-18·B12·IC11·Q-A1 포함) |
| 사용자 몫 | 11(옛 12에서 DS-U9를 원칙 기본안으로 뺌; Q-A1 하위 0) |
| 불확실 | 6(GC-B9 확정) |

**card별 배정(정정본)**:
- IT-1 범위 6 (b): B4
- DT-1 범위·완료 (8): B12
- SF-1: 범위 6 (e) B13, 범위 8 `supply_current`, 범위 9 I-A16·기생 C, 완료 (5) IC11
- LT-1 범위 (10): DF-37
- LI-1: (6) I-A13, (9) GC-B9 layout·R6, 완료 (10) I-B12 잔여
- DR-1: I-H1 (i), 새 card
- LA-0 (5)·HC-S: U-122
- LA-1 범위 15: (iv) `sctx.cache`, (g) Q-A1, U17 ② 잔여 셋(GC-B8)
- OS-2: DF-18, `constraint_rows`, PS-7
- GC-7: GC-B9 나머지 행
- 단위 9: GB-2324
- WB-1 범위 3: HC-B1·OP-B9
- EO-1·TB-1 착수 실측: 하위 계획 몫
- oracle OP-3·OP-4·OP-5·OP-8·OP-11·OP-0 design, TR-0T design

아래 A~D는 묶음별 분석 원문(판정 표·근거·문언 초안)이다.

---

# 백로그 재감사 A -- N5.2 DF-01~DF-37 + N5.4 DF 인용 (2026-10-29)

- 대상 계획 P = `wt/plan-v6384/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` @ `9c45b431` (N5.2 = 1146~1188행, N5.4 = 1228~1230행)
- 엔진 E = `wt/integ-it12/skills/analog-gmid-design/gmid_engine/` @ `b12792ab` (읽기만)
- D40 = `wt/plan-v6384/docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` (§10.3a DF 재발 금지 표 = 1943~1983행)
- 구조 규칙 = `E/tests/structure/structure_checks.py`(README 규칙표), 실행 test = `E/tests/structure/test_structure_rules.py:17-129`(규칙 A~G·I·K·M·복사)
- 판정 기호: 삭제-a(다른 결정·규칙·엔진 test로 닫힘) / 삭제-b(재작성으로 대상 소멸 + 재발 막는 규칙 인용) / 삭제-c(원칙상 불필요) / 삭제-d(물리 전제 틀림) / 필요 / 사용자 몫. 실측 = 이 문서 작성 중 grep·파일 확인. '불확실' = 확인 못 함.

## 0. 공통 사실(행마다 반복하지 않음)

1. **D40 §10.3a가 적은 계약 test 이름 23개(`test_df01_…`~`test_df36_…`)는 엔진에 0개다**(실측: `find E -iname "*df[0-9]*"` 결과 0, `grep -rn "test_df" E/tests` 0). §10.3a 머리(1945행)는 "test 파일 이름은 test 작성 주체가 확정하며, 확정하면 이 표를 갱신한다"인데 갱신되지 않았다. 아래 표는 같은 계약을 **다른 이름으로** 실제 강제하는 test·규칙을 찾아 인용한다. → 처리: DF 행을 지우면 D40 §10.3a 표도 같은 개정에서 '실제 test node id 대응표'로 바꾸거나 지운다(계획 먼저 -- S-7, 그다음 design).
2. N5.1(1144행) "새 엔진 `gmid_engine`은 아직 없다"는 낡았다(엔진 실재). 담당 범위 밖이지만 N5.2 머리와 같은 절이라 함께 고칠 대상으로 기록.
3. DF '위치'·'수정 Phase' 열은 옛 엔진(legacy) 기록이고 옛 엔진은 card LT-1(N6.4, DEC-99)이 지운다 -- 그 열 자체는 LT-1 뒤 대상이 없다.
4. 구조 규칙 범위(실측, README 규칙표): D 숫자 리터럴(0·±1·산술 2 허용), E 회로·넷·소자·레일 이름 **정확 일치** 리터럴 금지, F `except:`/`Exception`/`BaseException` 금지(`pipeline/entry.py` 1곳 예외), G 모듈 수준 가변 캐시·`lru_cache`·`global` 금지, I 태그 키 조회·식별 표현의 문자열 분기(`==`·`in`·`startswith`·`find`·`re.match` 등) 금지. **G-8 확장 lint(D40 §2.4.10, U17 ③)는 미구현**(실측: `structure_checks.py`에 `memo.call`·'G 확장' 0, `grep -rln "2\.4\.10" E` 0).
5. 예외 계층(실측 `E/core/failure_errors.py:33`): `class InfeasibleSizingError(ValueError)` -- N3.14 후보 실패 클래스 전부가 `ValueError` 하위다. 근거 문언은 00-common §7(`00-common.design.md:237` "`InfeasibleSizingError(ValueError)` # 기존 클래스(Phase 3에서 MOD4로 이동)") = 옛 엔진 호환. `SchemaRejectedError`만 `Exception` 직접 하위(P N3.14 953행).

## 1. 판정 표

| ID | 출처 줄 | 내용(요약) | 판정 | 근거(인용 줄·엔진 파일:행·실측) | 처리 | 원칙 점검 |
|---|---|---|---|---|---|---|
| DF-01 | P:1152 | vsb 재계산 뒤 W·gm·gds가 옛 vsb 값(버전 혼재), `setdefault("vsb", ref_vds)` | 삭제-a | 봉인 4 버전 혼재 거부 `E/sizing/seal_versions.py:19-37`(stale·foreign·overlap → SEAL_FAIL), test `E/tests/sizing/test_seal_versions.py:30 test_input_changed_after_compute_is_violation`·`:90`; IC10 `E/tests/sizing/test_kernel_run.py:325`; vsb는 노드전압·bulk에서 매번 유도 `E/sizing/block_columns.py:202-206`(`terminal_voltages(..., values[self.bulk[m]])`); `setdefault("vsb"` 0건(실측) | 닫는 문장: "봉인 4(버전 혼재 거부, DEC-83 graph 버전)와 IC10이 강제 -- E `sizing/seal_versions.py`, test `test_seal_versions.py:30`" → 행 삭제, history H2로 | graph 정본: 버전은 graph `block_versions` 하나 ✓ |
| DF-02 | P:1153 | 노드전압 경로 충돌을 엔진이 읽지 않음 | 삭제-a | 봉인 1(노드 충돌) test `E/tests/sizing/test_seal_node_conflict.py:48 test_fail_on_mos_node`·`:91`; P N6.2 단위 4 완료 조건(1330행 "같은 노드 두 writer를 봉인이 거부") | 행 삭제(근거 = 봉인 1 + 단위 4 완료 조건) | SC-a 단일 writer ✓ |
| DF-03 | P:1154 | 게이트가 `ValueError`를 던져 탐색 전체 정지 | 삭제-a | N3.14(941~958행) 후보 실패 = 실패 레코드·탐색 계속; `E/search/kernel.py:127,140` `except CANDIDATE_FAILURE_CLASSES` → `STATUS_FAILED`; test `E/tests/search/test_kernel.py:133 test_candidate_failure_recorded_and_cached`; `E/core/failure_classes.py:7,76` | 행 삭제. N5.4의 DF-03 인용도 삭제(아래 §2) | fail-closed: 실패를 통과로 세지 않음 ✓ |
| DF-04 | P:1155 | 소자명 부분문자열 탐색("M1"⊂"M11a") | 삭제-a | 구조 규칙 I(b) `name_branch` -- 식별 표현의 `startswith/endswith/find/index/__contains__`·`in` 리터럴 비교 금지(README 규칙표 I), 규칙 E; 대상 함수 `repair_infeasible_baseline`는 E에 없음(실측) | 행 삭제(근거 = 규칙 I(b)·E, DEC-28 행 228 '구현됨(DF-04)'도 DF 인용 제거) | 회로 이름 조건 금지 ✓ |
| DF-05 | P:1156 | 미러비 오차를 그룹 첫 두 소자만 봄 | 삭제-a | `E/metrics/mirror_ratio.py:46-48`(기준 diode 있으면 (기준, 나머지) 쌍, 없으면 `itertools.combinations` 전쌍), test `E/tests/metrics/test_mirror_ratio.py:27,39` | 행 삭제 | 상수 발명 없음(`PAIR = 1 + 1`) ✓ |
| DF-06 | P:1157 | 광범위 except가 필드 원천을 버림 | 삭제-a | 구조 규칙 F(`E/tests/structure/test_structure_rules.py:46`), 엔진 `except Exception` 0(실측) | 행 삭제(DF-37 처리와 함께 -- 아래) | fail-closed ✓ |
| DF-07 | P:1158 | 캐시 상한에서 캐싱 중단 | 삭제-a | `E/core/bounded_lru.py:6`(상한 = LRU 퇴출), test `E/tests/core/test_bounded_lru.py:128 test_caching_continues_after_capacity_reached`; U-60(P:2514) | 행 삭제 | 허용 cache = LUT memo(승인 예외 U-87 계열) ✓ |
| DF-08 | P:1159 | spec 지문 불일치를 노트만 남기고 유도 임계값 계속 사용 | 삭제-a | `E/authoring/spec_meta.py:32-34` `topology_fp_mismatch` 거부, 참조 파일 지문 불일치 = `ref_file_rejected` `E/authoring/spec_refs.py:9-13`; test `E/tests/authoring/test_spec_meta.py:37` | 행 삭제 | fail-closed ✓ |
| DF-09 | P:1160 | 면적 예산 블렌딩 식이 α 상쇄 | 삭제-b | 블렌딩 식 없음 -- 면적 예산 = spec 선언 `area_search_m2 <= 값`(`E/search/search_values.py:80-89`), 초과는 `StartConflict` 기록 `E/search/iv_area.py:81-94`; test `E/tests/search/test_iv_area.py:43`. 재발 막는 규칙 = DEC-79(P:278 면적 축 정의)·규칙 D(계수 리터럴 금지) | 행 삭제 | 상수 발명 금지 ✓ |
| DF-10 | P:1161 | 이분 역산 단조성 미검사 | 삭제-a | `E/lut/id_inverse.py:2-6`(DF-10 대체 명시), FC·단조 검사 DEC-87(P:286); test `E/tests/lut/test_curve_check.py:26,33,106`, `test__helpers_gmid_axis.py:33` | 행 삭제. P:1924 표의 'DF-10' 인용은 'DEC-87 FC·단조 검사'로 | 물리 정합(단조 구간 밖 근 없음) ✓ |
| DF-11 | P:1162 | 적층 diode LUT 실패 시 `idu_up = 1.0` 대입 | 삭제-a | LUT 실패 → `SealViolationError(lut_query_failed)` `E/tests/sizing/test__helpers_lut.py:53-58`, `test_block_columns.py:254-272`. 대입값 계열(0·1 자리값)의 일반 규칙 = N6.35 머리 '출발 정의 불능 공통 규칙'(DEC-105 행 304 인용)·E-14·E-17 | 행 삭제. 주의: 규칙 D는 0·±1을 허용하므로 '대입 1.0/0.0'을 lint가 못 잡는다 -- 재발 방지는 N6.35 공통 규칙과 리뷰 몫(새 lint 권고 안 함: 0·1 정상 사용과 구분 불가) | 상수 발명 금지 ✓ |
| DF-12 | P:1163 | 입력환산 offset이 gm 없는 소자를 조용히 뺌 | 삭제-a | `E/metrics/offset_analysis.py:6-25`(모든 MOS 합, σ 없으면 `sigma_missing` 정의 불가), test `E/tests/metrics/test_offset_analysis.py:167` | 행 삭제 | fail-closed ✓ |
| DF-13 | P:1164 | `id(lut)` 키 캐시와 상한 없는 캐시 | 삭제-a(부분 불확실) | 모듈 수준 캐시 = 규칙 G; 키 정준화 `E/core/canonical_key.py:1`, `bounded_lru.py:8`("`id()` 키 없음"); 모듈 수준 `id()` 키 0(실측). 남은 사실: (i) 블록 안 local memo가 `(id(계), ω)` 키를 씀 `E/metrics/ss_metrics.py:435`·`resolution.py:20,37-41` -- 계 객체를 `responses`가 블록 끝까지 쥐므로 id 재사용 충돌 없음(수명 안), 승인 예외 'O-15 (E) 블록 안 local memo'(CLAUDE.md 규칙 2) 범위. (ii) 실행 수명 인스턴스 dict `E/search/search_context.py:58 self.cache`, `:69 self.cell_floors`(주석 "[r8] … U17 ③에서 LUT memo 함수로") -- 상한·정본 여부는 이 감사 범위(DF) 밖, 불확실 | 행 삭제. 범위 밖 관찰 2건은 graph 정본 감사 쪽으로 넘김: `sctx.cell_floors`(U17 ③ 미완, G-8 lint 미구현 §0-4) -- 배정 card 없음(P에서 `cell_floors` grep 0) | graph 규칙 2: `sctx.*` 슬롯 금지 -- (ii)는 as-built 슬롯이라 ⚠ 별도 점검 필요 |
| DF-14 | P:1165 | `except Exception`이 호출 실패를 폴백으로 | 삭제-a | 규칙 F, 엔진 `except Exception` 0(실측) | 행 삭제(DF-37과 같은 처리) | fail-closed ✓ |
| DF-15 | P:1166 | Rz 캐시 키가 소자명뿐, ctx 공유 dict | 삭제-a | 수동소자 값 = 입력 버전 있는 graph 필드 `device.passive_value`; test `E/tests/metrics/test_passive_values.py:99,222`(DF-15 계약 명시) | 행 삭제 | graph 정본 필드 하나 ✓ |
| DF-16 | P:1167 | 전력 `sum_current` 직렬 기둥 중복 계상 | 삭제-a | DEC-78(P:277) 정의 그대로 구현 `E/metrics/supply.py:1-14`(선언 레일 Σ V·I, 소자 전류 합 안 씀), test `E/tests/metrics/test_supply.py:27,42,61` | 행 삭제. 비고의 '7b 착수 조건'·'4개 회로 전후 비교표'는 옛 엔진 대비라 P-14(옛 엔진 대조 범위 밖, N6.3 1392행)로 소멸. N5.4 DF-16 인용 삭제 | DEC-78 writer 하나 ✓ |
| DF-17 | P:1168 | 기준선에 FAIL 출력 박제 | 삭제-a | N6.3(1376행 '전체 0 failed'·1379행 '기대값은 오라클에서만'·1380행 `broken_tests`/`criteria_weakened` 필드). 대상(옛 stick_diagram self-test)은 LT-1이 삭제 | 행 삭제 | 작성자≠검증자 ✓ |
| DF-18 | P:1169 | 실패해도 exit 0, θ*는 출력만 | **필요** | N3.14 exit code 표(943~955행)·T1(1345행)은 정의돼 있으나 **최상위 진입점이 없다**: `run_gmid_design_pipeline`·`pipeline/entry.py`·CLI·`sys.exit` 0건(실측 `grep -rn "run_gmid_design_pipeline\|sys.exit\|__main__" E` → docstring 언급 `convergence/converge.py:5` 1건뿐). 단계 A·B는 보고서에 `exit_code` 칸만 낸다 `E/pipeline/stage_a.py:105,251`, `stage_b.py:22`. `exit_code_for` 자체는 test 있음 `E/tests/core/test_exit_code.py:26-41`. θ* 결과 JSON 기록: 불확실(진입점 없음) | 배정 card 없음 -- 진입점은 N6.1 단위 6(1249행 'MOD10 진입점·exit code')·D40 §11 U16 몫이고 N6.1 card 표(1258~1293행)에 MOD10 card가 없다. **권고(단순한 쪽)**: 새 card 대신 N6.2 단위 6 완료 조건(1332행)에 문언 추가 -- 초안: "`run_gmid_design_pipeline`(MOD10)은 N3.14 분류 예외를 `exit_code_for`로 프로세스 종료 코드에 싣고(비0), 탐색 단계까지 간 실행은 결과 JSON에 θ*·실패 레코드를 쓴다. 판정: 분류마다 합성 실패 픽스처 → 종료 코드 = 표 값, 결과 JSON 파일 존재·θ* 칸(DF-18 재발 금지)". 완료 측정 = 그 test green + 규칙 F 예외 1곳(`pipeline/entry.py`)이 그 진입점. MOD10을 만드는 변경이 card가 되면 N6.3 '결정 뒤 card 행'(1391행) 규칙으로 card 행 생성 | fail-closed(실패를 0으로 끝내지 않음) ✓, 만들면 배선: exit code 표는 진입점이 생겨야 배선됨 ⚠ |
| DF-19 | P:1170 | 레일 넷 집합이 모듈마다 다름 | 삭제-a | 레일 = `supply_nets` 선언(DEC-60 P:259), `E/tests/authoring/test_rails.py:31 test_names_do_not_decide_rails`, `E/tests/graph/test_bulk_default.py:103 test_rail_names_renamed_same_result`·`:116`; 규칙 E 이름 집합에 `supply_nets` 포함(README E). 비고의 B26-1~4·B35·B36·analog-grammar 사이트는 LT-1(DEC-99, P:298) 뒤 대상 소멸(DF-19 비고 스스로 명시) | 행 삭제. 소비자 정리: P:981(N3.16 레일 넷 행 'B26(DF-19·DF-26 …)') | 회로 이름 조건 금지 ✓ |
| DF-20 | P:1171 | 근거 없는 폴백 상수(vds 0.6/0.2, margin 0.05, `min_vds_by_role`) | 삭제-a | 규칙 D(숫자 리터럴, `# derive:` 태그 없으면 FAIL); `min_vds_by_role` 대상 하네스는 legacy(LT-1 삭제); 역할 라벨은 규칙 I. 0·1 자리값 계열은 N6.35 공통 규칙(DF-11 행과 같음) | 행 삭제 | 상수 발명 금지 ✓ |
| DF-21 | P:1172 | 실행 불가 probe 3개 | 삭제-b·c | 새 엔진에 probe 폴더·`probe_*` 함수 없음(실측: `E/metrics/probe_loop.py`는 metric 루프 프로브라 다른 개념). legacy test 보존·정리 성격(사용자 원칙 '목표 = 엔진') | 행 삭제 | -- |
| DF-22 | P:1173 | 지문 불일치 노트 리스트를 읽는 코드 없음 | 삭제-a | DF-08과 같음(노트가 아니라 거부) | 행 삭제 | fail-closed ✓ |
| DF-23 | P:1174 | 이름 리터럴이 동작을 정하는지 확인 필요 | 삭제-a | 규칙 E(소자·넷·회로·레일·파일 이름 정확 일치 금지) + 규칙 I(태그 키 조회·이름 분기 금지) + 일반성 test(무작위 이름 전단사 변환 `E/tests/generality/test_generator_sanity.py:82`, `test_metamorphic_*.py`) | 행 삭제 | WP-05·DEC-62 ✓ |
| DF-24 | P:1175 | vsb 유도가 bulk = 0 V/`vdd` 가정 | 삭제-a | bulk 넷 전압에서 유도 `E/sizing/block_columns.py:202-206`; 원점 이동 불변 test `E/tests/graph/test_bulk_default.py:131 test_origin_shift_invariant`·`:141 test_origin_shift_pm09_vs_0_18`; 전력 `E/tests/metrics/test_supply.py:42`. 남은 IC11 전 회로 test(`test_rail_origin_shift_invariance`, P:1066)는 N6.2 단위 10 완료 조건(1336행) 몫 -- DF가 아니라 IC11이 정본 | 행 삭제(IC11 행이 계속 소유) | IC11 ✓ |
| DF-25 | P:1176 | 포화 하한 `2/(gm/ID)` 근사 | 삭제-a | LUT v2 VDSAT 열(`assets/lut_v2_location.json:3` "GMBS·VDSAT 포함"), 봉인 7 VDSAT 사용 `E/sizing/seal_saturation.py`, `2/(gm/ID)` 식 0건(실측 grep); test `E/tests/lut/test_vdsat_query.py`·`test_vdsat_tolerance.py` | 행 삭제. P:1244 단위 1 행의 'DF-25' 인용은 'DEC-88 VDSAT 열'로 | 물리 정합 ✓ |
| DF-26 | P:1177 | 레일 판정 넷 이름 하드코딩, `agnd` 중간 레일 미인식 | 삭제-a | DF-19와 같음 + 중간 레일 test `E/tests/graph/test_bulk_default.py:196 test_multi_domain_pushpull_nmos_source_to_agnd`·`:223`·`:256` | 행 삭제 | ✓ |
| DF-27 | P:1178 | LUT VS 축 0~0.8 V, 축 밖 처리 규칙 없음 | 삭제-a | LUT v2 VS 0~1.8 V(`assets/lut_v2_location.json:3`), 축 밖 거부 `E/lut/axis_guard.py:17`(`lut_axis_out_of_range`), test `E/tests/lut/test_axis_guard.py:26,41`; LR3(P:715) | 행 삭제. P:1244·1925의 'DF-27' 인용은 'LR3 축 밖 거부'로 | fail-closed(클램프·외삽 없음) ✓ |
| DF-28 | P:1179 | LUT에 CGS·CGB 열 없음 | 삭제-a | `E/lut/cap_query.py:10-12`(열 있으면 `lut_cgs_cgb`, 없으면 `cgg_minus_cgd_at_gs` 모델 표지 -- 결과 `approximations`에 실림 `E/metrics/ss_linearize.py:21`); 열은 선택(lut/CONTRACT.md 120행). 엔진이 근사 사용을 결과에 기록 | 행 삭제. N5.4의 DF-28 문장은 규칙으로 남기되 ID 대신 'Caps.model = `cgg_minus_cgd_at_gs`인 metric'으로 바꿈(§2) | 조용한 근사 금지 ✓ |
| DF-29 | P:1180 | metric이 파일럿 topology 경로·넷 이름 리터럴 사용 | 삭제-a | 규칙 E(파일 이름·단자 넷 포함), 회로 전용 metric 대체 `E/metrics/ratio.py:2` | 행 삭제 | DEC-62 ✓ |
| DF-30 | P:1181 | metric 레지스트리 회로 이름 키 | 삭제-a | `E/metrics/registry.py:1`(DF-30 대체 명시), metric 이름 리터럴 전수에 회로 접두 키 0(실측: `gain_ss_db`·`rout_ss_ohm` 등). 한계: 규칙 E는 **정확 일치**라 `nmcnr_gain_db` 같은 접두 키는 lint가 못 잡는다 -- 위험 낮음(DEC-53 서명 어휘·일반성 test), 새 lint 권고 안 함 | 행 삭제 | ✓(한계 기록) |
| DF-31 | P:1182 | 보상 레지스트리가 회로별 함수 4개 | 삭제-a | GB5 보상 규칙 DEC-92(P:291)·DEC-70, 규칙 E; 엔진에 회로별 보상 함수 없음(`_COMPENSATION_REGISTRY` 0건 실측) | 행 삭제 | DEC-62 ✓ |
| DF-32 | P:1183 | 헤드룸이 `headroom_role` 라벨로 갈림 | 삭제-a | 규칙 I `FORBIDDEN_LOOKUP_KEYS`에 `headroom_role` 포함(README 규칙표 I), IC4(P:1059), 태그 자체는 LT-1 순서 6이 삭제 | 행 삭제 | analog-grammar 태그 금지 ✓ |
| DF-33 | P:1184 | 실행 spec에 소자 이름 override(`stack_groups_override`, `row_split`) | 삭제-a | spec 로더 = 스키마 밖 키 거부(N3.14 SCHEMA_REJECTED 953행, DEC-75 화이트리스트 P:274); `stack_groups_override`·`row_split` 엔진 0건(실측); 대상 하네스는 legacy | 행 삭제 | ✓ |
| DF-34 | P:1185 | 회로마다 spec 파이썬 함수 | 삭제-b | 대상(`run_harness.py`)은 legacy(LT-1 삭제); 새 엔진은 `*.sizing_spec.json` 데이터(N3.15), PDK 상수 = PDK 선언 하나(N6.1 단위 0, U-30), 9회로 실행 test `E/tests/integration/test_stage_a_library.py`·`test_spec_library_load.py`; 재발 방지 = DEC-62(P:261)·규칙 E | 행 삭제 | DEC-62 ✓ |
| DF-35 | P:1186 | 하네스가 메인 체크아웃 절대 경로를 박음 | 삭제-b·c | 엔진 소스에 드라이브·저장소 절대 경로·`sys.path.insert` 0건(실측), 경로는 `__file__` 유도 `E/lut/table_cache.py:98,220`; 대상 하네스는 legacy. 계획 안 재발 방지 규칙은 없음(D40 `test_df35_…`도 미구현) -- 판정 측정 무결성 인프라라 '엔진을 막을 때만'(사용자 원칙) 기준으로 지금 필요 아님. 참고: LUT 데이터 위치 기본값은 저장소 밖 절대 경로이고 env로 덮음(`assets/lut_v2_location.json:5-6`) -- 데이터 자리라 이 DF 대상 아님 | 행 삭제. 검증 격리는 작업 절차(검증 agent 격리 경로 규칙)로 | 인프라는 엔진을 막을 때만 ✓ |
| DF-36 | P:1187 | instance.json `topology_ref` 절대 경로 | 삭제-b·c | 대상 `stick_diagram.save_instance_json`은 legacy; 새 엔진 보고서에 경로 칸 없음(단계 A·B 보고 = 회로 이름, 실측 grep: 경로 문자열은 `SchemaHit` 오류 메시지 `E/authoring/spec_load.py:163,171`뿐). 피해 꼴은 가짜 FAIL(조용한 오판 아님) | 행 삭제 | ✓ |
| DF-37 | P:1188 | 광범위 except가 N3.14 클래스를 삼킴(옛: `except …ValueError…` 76·`except Exception` 13·`except InfeasibleSizingError` 18) | **필요** | (1) `except Exception` = 규칙 F로 막힘, 기반 클래스 포획 0(실측 -- 탐색은 `CANDIDATE_FAILURE_CLASSES`만, `E/search/kernel.py:127`). (2) **규칙 F가 `except ValueError`를 보지 않는데 `InfeasibleSizingError(ValueError)`(`E/core/failure_errors.py:33`)라 `except ValueError`는 N3.14 클래스 전부를 삼킨다** -- 옛 DF-37의 주된 꼴(76건)이 바로 이것. 현재 엔진의 `ValueError` 포획 10곳(`graph/structure_load.py:70,140`, `layout/patterns_common_centroid.py:135`, `metrics/records.py:53`, `pipeline/stage_a.py:232`, `lut/mismatch_set.py:59`, `lut/noise_set.py:49`, `lut/table_cache.py:258`, `metrics/probe_loop.py:34`, `metrics/_helpers_probe.py:82`)은 감싼 호출이 일반 `ValueError`만 내서 **지금 실제 삼킴은 0**(실측: 각 try 본문 확인 -- 예 `stage_a.py:232`는 `search/count_budget.py:21` 일반 ValueError) -- 그러나 재발을 막는 장치가 없다. (3) `SchemaRejectedError`를 잡는 비진입 자리 2곳: `E/lut/derived_fns.py:54`(→ 0.0, 이미 N6.35 E-14·LA-1 범위 15 (g) 소유), `E/search/_helpers_guard.py:42 Tolerant`(→ None, 예외 감사 E5-25가 B '정당한 안전망'으로 분류) -- N3.14 SCHEMA_REJECTED '탐색 중이라도 삼키지 않는다'(953행)와 문언 충돌 | **권고안 (A) 근본 수정**: `InfeasibleSizingError`의 기반을 `ValueError` → `Exception`(SchemaRejectedError와 같은 꼴). 근거: ValueError 하위는 옛 엔진 호환 문언(00-common:237 '기존 클래스')뿐이고 옛 엔진은 LT-1이 지운다(O-153·O-169: as-built는 근거 아님); 그러면 `except ValueError`가 구조적으로 N3.14 클래스를 못 삼켜 lint 예외 목록이 필요 없다. 바뀌는 것: 클래스 1줄, 기반 단언 test 3곳(`E/tests/core/test_failure_errors.py:27,33`, `E/tests/lut/test__helpers_fail.py:32` -- 기대값 변경이라 test 주체·`criteria_weakened` 아님(정의 변경) 기록), 00-common §7:237, P N3.14 표 머리 문언 "`InfeasibleSizingError`(`Exception` 직접 하위) 하위". 엔진 안 `ValueError` 포획이 N3.14 클래스를 기대하는 자리 0(위 10곳 실측), `pytest.raises(ValueError)` 202곳 중 N3.14 클래스를 기대하는 것이 있으면 깨진다 -- **불확실(착수 실측 필요)**. **대안 (B)**: 규칙 F 확장 -- `except` 형이 `ValueError`(또는 그 상위)를 포함하면 위반, 예외 = 같은 try에 앞선 `except InfeasibleSizingError: raise` 처리기. 10곳 수정 + lint 픽스처. 비교: 물리 무관 / 손계산 무관 / design 단순성 (A) 우세(규칙 1개 소멸 방향) / 실측 변경량 (A) 1줄+3 test vs (B) 10곳+lint. **배정**: card LT-1(N6.4) 확장이 단순 -- 옛 엔진 호환 사유의 제거라 그 card 주제와 같고, LT-1 완료 조건 6(엔진 결과 동일, 함수 해시 목록 고정)이 '동작 불변'을 그대로 판정한다. 넣을 문언(N6.4 범위 표 새 행): "(10) 예외 기반 정리(DF-37 재발 금지): `E/core/failure_errors.py` `InfeasibleSizingError` 기반을 `Exception`으로, 기반 단언 test 3곳·00-common §7·계획 N3.14 문언 동시 개정. 순서 5(legacy 삭제) 뒤 별도 커밋." 완료 측정: (i) `issubclass(InfeasibleSizingError, ValueError)` False test (ii) 전체 test 0 failed, 깨진 test는 `broken_tests` 목록 (iii) 완료 조건 6 엔진 결과 동일 (iv) 엔진 `except ValueError` 처리기 try 본문 재실측 표. (3)의 `Tolerant` SchemaRejected 포획은 → 사용자 몫(아래 Q-A1). 순서 충돌: LT-1 착수 조건(OP-1a·L-3) 불변, 다른 card와 파일 겹침 = `core/failure_errors.py`는 다른 card 범위에 없음(P에서 `failure_errors` grep -- 불확실, 착수 때 재확인) | fail-closed ✓, ⚠ (3) `Tolerant`가 SCHEMA_REJECTED를 None으로 바꿈 = N3.14 문언과 충돌(원칙 충돌로 올림) |

## 2. N5.4(P:1230) DF 인용 문장

| 대상 | 판정 | 근거 | 처리(문언 초안) |
|---|---|---|---|
| "옛 엔진 결과를 인용할 때: I-B21 …, DF-16 …, DF-03 …, DF-18 …" | 삭제-b·c | 옛 엔진 결과 인용·대조는 범위 밖(P-14, N6.3 1392행 '단위별 옛 엔진 대조 기록과 마일스톤은 범위 밖'), 옛 엔진은 LT-1로 작업 트리에서 사라짐. DF-16·DF-03은 위에서 닫힘. DF-18은 '필요'지만 그것은 새 엔진 진입점 계약이지 보고 문구가 아니다 | 문장 첫 절 삭제. I-B21(P:1212)은 N5.3 열린 이슈라 이 감사 범위 밖 -- 남길지 B 감사 몫 |
| "CGS·CGB 근사 스탬프를 쓴 metric(DF-28)" | 필요(문언만) | 보고 규칙 자체는 유효(조용한 근사 금지), DF-28 행이 지워지면 ID가 dangling | "용량 모델이 `cgg_minus_cgd_at_gs`(CGS·CGB 열 없음, `E/lut/cap_query.py`)인 metric"으로 교체. 배정 = 이 계획 개정 커밋(문서) |

## 3. 지울 때 함께 고칠 소비자(실측 grep, P 안 N5.2 밖 DF 인용 줄)

P: 11(Status), 75(용어 DF-nn 행 -- 'N5.2' 정의 유지 여부), 209~287 사이 DEC 행들의 DF 인용(228 `구현됨(DF-04)`, 236 DEC-37 폐기 행 등), 515, 672, 678, 715, 981, 1066, 1192, 1230, 1244, 1408, 1886, 1924, 1925, 2481, 2633~2644(N9.1 폐기 design 행 -- 이력이라 고치지 않음). design: 40(43곳, §10.3a 표 포함), 41(4), 42(1), 00-common(13 -- §7:270 'DF-37이 정본' 포함). 폐기 design(10·20·30)·history는 이력이라 고치지 않는다(LT-1 '고치지 않는 것' 규칙과 같은 원칙).

## 4. 사용자 몫 질문 후보

- **Q-A1**(DF-37 (3)): `E/search/_helpers_guard.py:42 Tolerant`가 LUT의 `SchemaRejectedError`('감도 열 미정의, 모델 bin 밖 폭')를 None으로 바꿔 offset·noise 가드 출발 구간을 끈다. 예외 감사(2026-10-28 E5-25)는 B(정당)로 분류했지만 N3.14 953행 'SCHEMA_REJECTED는 탐색 중이라도 삼키지 않는다'와 문언이 충돌한다. 물리 결정자: 'bin 밖 폭'은 스키마 위반이 아니라 LUT 정의역 밖(조회 실패) 사실 -- 분류 자체가 SEAL_VIOLATION(`lut_query_failed`)이어야 하는지가 핵심. 선택지 (가) LUT 정의역 실패를 SchemaRejected가 아닌 정의역 실패 분류로 바꾸고 `Tolerant`는 그것만 잡음(N3.14 문언 유지) (나) N3.14에 '출발 구간 보조 경계의 LUT 정의역 거부는 비활성 사유로 기록' 예외 행 추가. 오케스트레이터 권고 후보 = (가)(예외 행을 늘리지 않음, fail-closed 분류 정합) -- 단 LUT가 어떤 사유에 SchemaRejected를 내는지 전수 실측 뒤 확정(불확실).
- DF-18 진입점(MOD10)을 card로 만들지, 단위 6 완료 조건 문언으로만 둘지 -- 오케스트레이터 판단 범위(사용자 몫 아님)이나 card 목록에 MOD10 행이 없다는 사실은 보고.

## 5. 집계

- 전체 37행. **삭제 35 / 필요 2 / 사용자 몫 0(행 단위; DF-37 안 하위 질문 Q-A1 1건)**.
- 삭제 사유별: a = 30(DF-01~08, 10~20, 22~33 중 b·c 행 제외 -- DF-01,02,03,04,05,06,07,08,10,11,12,13,14,15,16,17,19,20,22,23,24,25,26,27,28,29,30,31,32,33), b = 2(DF-09, DF-34), b·c = 3(DF-21, DF-35, DF-36), c 단독 0, d 0.
- 필요 배정: **DF-37 → card LT-1 확장**(범위 (10) 예외 기반 정리, 권고안 (A); 대안 (B) 규칙 F 확장), **DF-18 → N6.2 단위 6 완료 조건 문언**(MOD10 진입점, 현재 card 없음 -- 진입점 변경이 card가 될 때 N6.3 '결정 뒤 card 행'으로 승계).
- 문서 후속: N5.4 문장 2곳(첫 절 삭제, DF-28 문언 교체), N5.1 낡은 문장, D40 §10.3a 표(가짜 test 이름 23개) → 실제 test 대응표 또는 삭제, §3 소비자 줄.
- 범위 밖 관찰(넘김): `sctx.cache`·`sctx.cell_floors`(`E/search/search_context.py:58,69`) 실행 수명 dict 슬롯과 G-8 확장 lint 미구현(D40 §2.4.10, U17 ③) -- graph 정본 규칙 2 대상, 배정 card 없음(P에서 `cell_floors` 0건).


---

# 백로그 재감사 B -- 계획 N5.3 열린 이슈 표(I-A5~I-H5)

- 대상: `wt/plan-v6384/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` @ `9c45b431`, N5.3(1190~1226행)과 그 ID를 인용하는 계획 안 다른 줄(grep)
- 엔진 사실: `wt/integ-it12/skills/analog-gmid-design/gmid_engine/` @ `b12792ab`(아래 `E/` = 이 폴더, `A/` = `wt/integ-it12/skills/analog-gmid-design/assets/`). 읽기만 했다.
- 기준: 사용자 지시 2026-10-29(불필요 → 삭제, 필요 → 바로 card 배정), graph 단일 정본(writer 하나, 새 cache·memo·sctx·사본 금지), 상수 발명 금지, 회로 이름 조건 금지, O-171(물리 판정 근거), O-153·O-165·O-169(재작성), '인프라는 엔진을 막을 때만', '목표 = 엔진, test는 버려도 됨'
- 판정 기호: 삭제(a) 다른 결정·card·규칙으로 닫힘 / 삭제(b) 재작성으로 대상 코드 소멸 / 삭제(c) 원칙상 불필요 / 삭제(d) 물리상 틀린 전제 / 필요 / 질문
- 원칙 점검 약어: G = graph 단일 정본, K = 상수 발명 없음, N = 회로 이름 조건 없음, P = O-171 물리 근거, R = O-153/165/169 재작성 정합, F = fail-closed, W = 만들면 배선

## 1. 행별 판정

| ID | 출처 줄 | 내용(요약) | 판정 | 근거(인용 줄·엔진 파일:행·실측) | 처리 | 원칙 점검 |
|---|---|---|---|---|---|---|
| I-A5 | 1196 (인용 164) | LUT 생성 메타 읽기(`lut_conditions_from_npz`)가 운영 경로에서 안 불림 | 삭제(a) | 새 엔진이 S0 지문 조립에 배선: `E/lut/provenance.py:7-8`(옛 함수 본문 복사 `_lut_conditions_from_npz` :39, "여기서 S0 지문 조립에 배선한다"), 슬라이스 간 corner·temp_c 대조 `E/lut/lut_set.py:338·397`. 합격 조건은 DEC-96 (3)(164행 'TT 27 °C 한 조건') | 삭제 근거 문장: "I-A5 닫힘 -- `E/lut/provenance.py`가 측정 조건을 S0 지문에 싣고 `lut_set` 이 슬라이스 간 대조(DEC-96 (3))". 164행 '(I-A5 범위 부분 해소)' → '(LUT 측정 조건은 `lut/provenance` 가 S0 지문에 싣는다)' | G·W 충족(소비자 = 지문·대조), K 0 |
| I-A6 | 1197 (인용 680·2483·2641) | ICMR·출력 스윙 metric과 제약 슬롯 없음 | 삭제(a) | 정의 = N3.8(680·694행), 이름·형식 = DEC-96 (2)·U-29(2483), `swing_out_v` 삭제 = O-154 Q3(373행). 엔진에 metric 있음: `E/metrics/achievability.py:73`, `E/metrics/aux_types.py:160-166`, `E/metrics/registry.py`. 남은 일(값 출처를 선형 감도 끝으로, `swing_out_v` 엔진 삭제)은 card DE-1 범위 3·4(1766·1767행)와 SF-1·SB-1 통합 병합(1273·1278행)이 소유 | 삭제 근거: "I-A6 닫힘 -- 정의 N3.8, 구현 잔여는 card DE-1 범위 3·4·SF-1(`swing_out_v` 제약 삭제 data)". 680행 머리 '(DC 동작 범위, I-A6 -- …' → 'I-A6' 삭제; 2483행 U-29 '(I-A6)' → '(N3.8 스윙·입력 범위)' | G: `swing_out_v` 가 엔진에 남아 있음(`E/core/units.py:8`, `aux_types.py:166`)은 DE-1 삭제 범위 -- 둘째 생산자 아님 |
| I-A7 | 1198 | 일반 순환 블록 수렴 판정 | 삭제(a) | 구현됨: `E/sizing/scc_newton.py:1-16`(SCC 감쇠 Newton, tol·K_max 계산, 상수 없음), 호출 `E/sizing/block_columns.py:640`, 순서 `E/sizing/scc_order.py`(`kernel_context.py:87`). 규칙 = N3.6·DEC-32(232행) | 삭제 근거: "I-A7 닫힘 -- `sizing/scc_newton`·`scc_order`(N3.6, DEC-32)". 곁 발견: 232행 DEC-32 상태 칸 '미구현'은 낡음 → '구현됨(`sizing/scc_newton`)'(이 범위 밖 -- 결정 표 감사 쪽에 넘김) | K: 감쇠 비 '반'·정지 = tol·K_max(docstring :15) -- 발명 상수 없음 |
| I-A10 | 1199 (인용 225) | `parasitic_pm_ss_deg ≥ pm_target_deg` 제약이 선측정 없이 걸림, folded는 `omega_c` 미노출 | 삭제(a)+(b) | 새 엔진은 회로 무관 전달 뷰 하나로 잼: `E/metrics/registry.py:42`(`parasitic_pm_ss_deg` = LoopAnalysis `phase_margin_deg`), `E/metrics/ss_metrics.py:14`(β = 1 `pm_ss_deg` 와 같은 `analyze_loop`), 회로별 `omega_c` 경로 없음(옛 `_metric_folded_cascode_pm_deg` 계열 소멸, DF-30). 선측정 = SPICE oracle 대응 `E/metrics/verified_by.py:40`(`pm_deg`) → 모델 오차 측정은 card ME-1(N6.19)이 소유 | 삭제 근거: "I-A10 닫힘 -- 전달 뷰 일반 metric(`metrics/registry`), 선측정 = ME-1 모델 오차". 225행 DEC-25 상태 칸 '사이징 대상 회로 선측정 미완 I-A10' → '사이징 대상 회로 모델 오차 = card ME-1' | N: 회로 이름 키 0(registry docstring :7) |
| I-A11 | 1203 (인용 270은 '오기' 기록) | 크로스오버 주파수: 선언식 36.6 MHz 대 전체 응답 30.50 MHz 차이 원인 미확인 | 삭제(b) | '선언식' 경로가 새 엔진에 없음 -- UGF는 전회로 MNA 교차 하나: `E/metrics/crossing.py:1`, `E/metrics/registry.py:40`. 엔진 대 SPICE 차는 ME-1(DEC-72)이 잼. 재발 방지 규칙 = DEC-05(206행 'gain 판정 = 전체회로 MNA 하나')·N3.8 GBW·PM 정의 | 삭제 근거: "I-A11 대상 소멸 -- 옛 선언식 경로 없음, UGF = 전회로 MNA(`metrics/crossing`), 대 SPICE 차는 ME-1". 270행 '옛 인용 I-A11 오기' 문구는 기록이라 그대로 | P: 원인 미확인 상태를 정의로 쓰지 않음 -- 둘째 정의 0 |
| I-A12 | 1200 (인용 279·1230) | `finger_pitch_overhead_m` = 0.0(sky130 poly pitch 미확보) → 행 폭 과소 | 삭제(a) | PDK 선언에서 규칙 식으로 계산: `A/sky130_pdk_decl.json:108-112`(`max(poly.2, licon.1 + 2·licon.11)`), 소비 `E/layout/contract_input.py:43·129`, `E/layout/rows.py:76`, `E/layout/pattern_select.py:137`. **실측**(`read_pdk_decl`, 2026-10-29): `finger_pitch_overhead_m = 2.8e-07` m(0 아님), `min_finger_w_m = 4.2e-07` | 삭제 근거: "I-A12 닫힘 -- PDK 선언 규칙 식(U-30, DEC-80 (i)), 실측 0.28 µm". 279행 DEC-80 '`finger_pitch_overhead_m`이 0인 동안(I-A12) …' 문장 삭제, 1230행 N5.4 '면적 축의 레이아웃 격자 분해능이 … = 0(I-A12) 때문에 과소평가임과' 구절 삭제 | K: 값 = 규칙 번호 식(박은 숫자 아님), G: 선언 한 곳 |
| I-A13 | 1201 (인용 11·2521) | dummy·LDE(LOD/WPE/PSE) 미반영, L 혼합 interdigitation 행 대칭 검사 없음 -- U-67 (나) 확정 | **필요**((1) 대칭 검사) + **질문**((2) LOD) | 결정 = U-67(2521행), design 40 정의 행 1307(LY4 L 혼합 행 대칭)·1308(`ly.lod`)·1536(오라클 LOD 입력). **새 엔진 실측**: (1) L 혼합은 기록만 -- `E/layout/pattern_select.py:27`·`:238-257`(`GroupLayout.l_mismatch`, "거부 사유 아님"), 거울 대칭 판정·`review_needed` 없음 → U-67 (1) 미구현 (2) `ly.lod` 생산자 0(`git grep` `lod` -- `E/` 0건, `tools/spice_oracle/legacy_adapter.py:168` 옛 어댑터 뿐) → U-67 (2) 미구현. WPE·PSE 제외·dummy 면적 포함은 결정대로(할 일 없음) | (1) **배정 = card LI-1(N6.12) 범위 확장** -- LI-1이 이미 `pattern_select`·`rows` READS를 고치는 card라 파일·블록이 같다(새 card보다 단순). 넣을 문언 초안(범위 (6)): "**L 혼합 interdigitation 행 대칭**(U-67 (1), design 40 1307행): `ly_pattern_select` 블록이 행 finger 패턴에서 소자마다 finger 위치의 행 중심 거울상이 같은 소자 finger인지 판정하고, 어긋나면 그 matching 그룹을 `review_needed`(사유 이름 design)에 올린다 -- 기존 `l_mismatch` 기록 칸을 이 판정의 입력으로 쓰고 둘째 판정 자리 없음, 새 상수 0(LY4 common-centroid 정의)." 완료 조건 추가: "(8) L 혼합 비대칭 toy → `review_needed` 항목(base는 기록만 -- red), 대칭 toy → 항목 없음, library 9회로 발동 수 변화표". 변경 종류 = 동작 변경(review 항목 추가). (2) 질문 후보 Q-1(아래 §2) | G: 판정 writer = `ly_pattern_select` 하나, 새 필드 0(기존 `review_needed` 칸). K 0, N 0, F: 비대칭이면 review(통과로 세지 않음). W: (2) `ly.lod` 는 소비자(oracle 넷리스트)와 같은 변경이 아니면 만들지 않는다 |
| I-A15 | 1202 (인용 717) | `measure_L_knee`가 격자 전체 중앙값에서 knee를 잼 | 삭제(b) | 옛 함수 소멸 -- 새 엔진에 knee 측정 코드 0(`git grep knee` → `E/search/find_front.py:12·35-37` '최소형 밖, 열린 항목' 표기뿐). 재발 방지 규칙은 이미 LR5(717행 '동치류 멤버의 탐색 gm_id 가능역으로 한정한 곡선에서 계산')에 있음 | 삭제 근거: "I-A15 대상 소멸 -- 옛 `measure_L_knee` 없음, 규칙 = LR5". 717행 '현 구현은 I-A15' 구절 삭제 | R: 옛 as-built 결함을 규칙 근거로 쓰지 않음 |
| I-A16 | 1204 | PDK 선언 note '`res_high_po` 셀 모델 파일 로컬 없음'은 사실과 다름 → 엔진 면적 선언(generic poly 48.2 Ω/□)·기생 용량 재검토 | **필요**(면적 선언) + **질문**(머리 기하 ratify·기생 C) | 사실 확인: `C:/pdk/sky130_fd_pr/cells/res_high_po/` 에 model 6개(`…res_high_po{,_0p35,_0p69,_1p41,_2p85,_5p73}.model.spice`, PDK 커밋 `f62031a`). note 문구 `A/sky130_pdk_decl.json:89`. 엔진 선택 규칙은 이미 있음: `E/core/pdk_decl.py:551-566`(`resistor_types` 후보 가운데 Ω당 면적 W_min²/R□ 최소를 `poly_res_*` 로), 소비 `E/search/area_decl.py:10-11·44-45`; 후보는 지금 `poly_generic` 하나(`A/sky130_pdk_decl.json` `resistor_types`). 물리(O-171): 실측 근거 `p4r_cm_sense.md` §3.3 -- high_po_0p35 rsheet 1112.41 Ω/µm → Ω당 면적 0.35/1112.41 = 3.15e-4 µm²/Ω 대 generic 0.33²/48.2 = 2.26e-3 µm²/Ω(7.2배), 1 MΩ당 C ≈ 125 fF. **선례**: heldout `cnr_ota` 저항 값은 이미 res_high_po 셀 모델 식으로 계산(`A/heldout/cnr_ota.sizing_spec.json:124·141`, 사용자 결정 2026-10-14 D-R) -- 같은 PDK 셀을 값에는 쓰고 면적에는 안 쓰는 불일치. 기생 C: 저항 스탬프는 1/R만(`E/metrics/stamp_two_terminal.py:13-15`) | **배정 = card SF-1 범위 9(N6.28, 행 담당 칸 그대로) 확장, data + PDK 선언 한 변경**. 문언 초안(범위 9 끝에 덧붙임): "**저항 종류 후보 선언 정정**(N5.3 I-A16 이관): `assets/sky130_pdk_decl.json` `poly_res_params` note의 '로컬 없음'을 고치고 `resistor_types.candidates`에 `res_high_po` 후보(시트 저항 = 셀 모델 rsheet·고정 폭에서 계산, 최소 폭 = 셀 폭, 머리 면적 = 규칙 번호 식 -- 식·원본 sha256은 선언, 숫자 박기 금지)를 더한다. 선택은 기존 규칙(`core/pdk_decl` Ω당 면적 최소) 그대로 -- 새 선택 규칙 0." 완료 조건 추가: "(a) 선언 읽기 test -- 두 후보 중 Ω당 면적 최소가 high_po로 선택됨(base는 generic -- red) (b) 저항 있는 library 회로의 `area_search_m2`·front 변화표(동작 변경, 원인 = 저항 종류) (c) cnr_ota spec 값 식과 같은 셀·같은 sha256(출처 하나)". 순서: SF-1 그대로(DE-1 앞) -- 충돌 없음 | G: 선언 한 곳·선택 규칙 하나(새 cache 0). K: 시트 저항·머리 면적은 모델·규칙 식에서 계산. N 0. P: 위 실측. R: 기존 규칙 재사용, 덧대기 없음. 기생 C는 MNA 스탬프 변경이라 이 확장에 넣지 않음 → Q-2 |
| I-B3 | 1205 | 블록 사이징 함수 시그니처(내층 DP 입력) | 삭제(a) | DEC-73: 내층 DP = 정밀 경로, '미구현 -- 선언 칸 없음', 기본 경로 = 층 0 손계산(270행 끝 'v6.19 정리(DEC-73)'). 블록 국소 모델 정본 = card UB-1(N6.15). 블록 계산 자리 실재: `E/sizing/size_and_seal_local.py`, `E/metrics/block_model.py` | 삭제 근거: "I-B3 닫힘 -- DEC-73 기본 경로에 내층 DP 없음, 블록 국소 모델 = UB-1" | R: 옛 Phase 7b 시그니처를 규칙으로 남기지 않음 |
| I-B5, I-B6 | 1206 | DOF 진단 없음(VDS·KVL 축, 부등식 오계수) | 삭제(a) | 구조 DOF 구현: `E/metrics/dof_report.py:1-12`(이분 매칭 rank, 등식만 셈 -- 부등식은 변수·등식 집합에 넣지 않음), 배선 `E/metrics/achievability.py:22·315`(overconstrained 정지). 곁 사실: 수치 rank(41 §4.5 B2)는 `numeric_ranks = ()`로 비어 있음(`dof_report.py:9`, `achievability_types.py:176`) -- N6.1 단위 7 '구조 DOF·수치 rank' 문언과 차이 | 삭제 근거: "I-B5·I-B6 닫힘 -- `metrics/dof_report`(GB4 A7) + `achievability` 정지". 수치 rank 빈 칸은 이 행 범위 밖 관찰 -- 실패는 Newton 특이·`singular_dc` 로 이미 fail-closed라 엔진을 막지 않음, 따로 card 권고하지 않음(불확실: 수치 rank가 막는 사고 실례 미확인) | F 충족(overconstrained 정지) |
| I-B8 | 1207 | KCL 잔차 제약 없음 | 삭제(a) | 봉인 3 구현: `E/sizing/seal_kcl.py:1-8`(노드전압에서 원소 전류 재계산, tol_I = tol_V × gm 최댓값 -- N3.6 식), 호출 `E/sizing/seal.py`·`s2_values.py` | 삭제 근거: "I-B8 닫힘 -- 봉인 3 `sizing/seal_kcl`" | K: tol_I 식 유도(상수 0) |
| I-B11 | 1208 | IC 강제 test 0개 | 삭제(a) + 부속 **필요**(IC11) | 정본 = N4.1 표(1050~1067행 -- 클래스·test 이름·담당)와 TS7(769행); 이 행은 사본. 실측(`find tests -name 'test_ic*'` 0, 이름 대신 내용으로 대조): IC2 섞기·IC4 태그 제거 = `E/tests/generality/test_metamorphic_sizing.py:168`(`test_shuffle_and_tag_noise_same_snapshot`)·`test_metamorphic_metrics.py:98`, 해시 시드 = `E/tests/convergence/test_converge.py:235`; IC7 정지 = `unsupported_rule_branch` toy(`tests/graph/*` 26 파일); **IC11 레일 원점 이동 불변 test 없음**(`origin_shift` 계 grep → `tests/graph/test_bulk_default.py` 하나, 엔진 전체 metamorphic 없음). IC11은 3레일(agnd) 회로가 library에 있어(`pushpull_follower_buffer`·`sf_pushpull`·`nmcnr` SD-T1) 물리 일반성 검사 -- 'legacy test 보존' 아님. IC5(게이트 docstring 사각 표기)는 인프라 문서 lint라 엔진을 막지 않음 | 행 삭제 근거: "I-B11 = N4.1 사본 -- 정본은 N4.1·TS7". 부속 배정 = **card SD-1(N6.21) 완료 조건 추가**(SD-1이 nmcnr를 원문 ±1 V로 옮기는 data card라 원점 이동이 그 card의 실제 변화): "IC11 원점 이동 불변 -- 레일 둘인 library 회로 하나를 (vdd, gnd) = (1.8, 0) 대 (0.9, −0.9)로 돌려 소자 VGS·VDS·VSB·gm/ID·W·dc/ss metric이 tol_V(그 밖은 감도 전파값) 안에서 같음; 단 `power_dc_w` 는 DEC-78 정의상 기준 전위 V_0 = 넷리스트 0 V에 의존하므로(277·2253행 P7) 비교에서 빼고 그 사실을 test에 적음." 곁 권고: N4.1 '담당 Phase' 열의 옛 Phase 표기 재정리는 N4.1 담당 감사 몫(이 범위 밖) | P: IC11은 DF-24·DF-26(레일 0 V 가정) 재발 검출 -- 물리 정합. W: test 대상 = 운영 엔진 경로. 전력 예외는 정의(P7)에서 유도, 발명 아님 |
| I-B12 | 1209 | `set` 순회 잔존(옛 sizing_recipe 1·stick_diagram 5) | 삭제(b) | 옛 파일 소멸. 새 엔진 AST 실측(`for … in set(…)`·집합 리터럴 순회): 3곳 -- `E/graph/feedforward_cells.py:102·155`(바로 `sorted` 로 감쌈 -- 결정론), `E/layout/mirror_trail.py:112`(시작 노드 두 후보 set 순회 -- 복사 정의라 본문 수정 금지 `_copy_manifest.py:133`; `.ok` 는 순서 무관, `node_path` 는 `E/layout/canonical_rows.py:1-9`가 넷 이름 정렬로 다시 유도). 결정론 규칙 = NFR-4·IC2, 해시 시드 독립 실경로 test `test_converge.py:235` | 삭제 근거: "I-B12 대상 소멸 -- 새 엔진 set 순회 3곳은 정렬 또는 `canonical_rows` 재유도로 결정론(NFR-4)". 불확실 1: `mirror_symmetric_trail`(`mirror_trail.py:235-236`) 결과 `node_sequence` 가 `canonical_rows` 를 반드시 거치는지는 호출 사슬 끝까지 확인 못 함 -- 해시 시드 test가 common_gate 하나뿐이라 matching 행 회로에서 미검증 | F: 결정론 깨짐이면 비트 비교 test가 잡음(1회로) |
| I-B13 | 1210 | gm_id·vds 확정 출처 태그가 일부 경로에만 | 삭제(a) | SC-a가 구조로 강제: `E/core/writer_table.py:1-6`(graph (kind, field)마다 writer 하나, 다른 writer 쓰기 = `WriterPermissionError`) -- 출처 = 그 필드의 writer 블록, 태그 필요 없음 | 삭제 근거: "I-B13 닫힘 -- SC-a writer 권한표(`core/writer_table`)가 필드 출처를 정함" | G 그 자체 |
| I-B14 | 1211 (인용 208) | 사이징 경로가 `value_dc_amp` 미소비 | 삭제(a) | DEC-08 구현: `E/sizing/current_basis.py:7`('값이 선언된 이상 전류원은 고정값(DEC-08)'), spec 키 `E/authoring/spec_elements.py:41`(`current_source` → `value_dc_amp`), 옛 키 `value_amp` 거부 `E/authoring/_spec_fields.py:32` | 삭제 근거: "I-B14 닫힘 -- `sizing/current_basis` 고정 전류". 208행 DEC-08 상태 칸 '부분(…사이징 경로 미배선, I-B14)' → '구현됨(`sizing/current_basis`)' | G: 선언 → 기저 한 자리 |
| I-B21 | 1212 (인용 206·1230) | 선언 gain 제약이 미러 부하를 못 봄(옛 `gain_stages_sum`) | 삭제(a) | DEC-05 구현: `E/metrics/registry.py:39`(`gain_ss_db` = 전달 뷰 LoopAnalysis -- 전회로 MNA), 분해 잔차 기록 `E/metrics/block_residual.py:3-9`(`gain_residual_db` = 전회로 − 분해 합성). `gain_stages_sum` 0건 | 삭제 근거: "I-B21 닫힘 -- `gain_ss_db` 전회로 MNA(DEC-05), 블록 잔차 `metrics/block_residual`". 206행 DEC-05 상태 칸 '미구현(현 제약은 `gain_stages_sum`, I-B21)' → '구현됨'. 1230행 N5.4 '옛 엔진 결과를 인용할 때: I-B21(…)'은 옛 엔진 인용 규칙이라 'I-B21' 대신 '옛 `gain_stages_sum` 제약(미러 부하 못 봄)'으로 풀어 씀 | G: gain 판정 정본 하나, 분해 값은 할당용(DEC-05) |
| I-B22 | 1213 | 입력환산 offset -- 다중 diff pair·비대칭·단일 입력 처리 | 삭제(a) | 일반형 구현: `E/metrics/offset_analysis.py:6-9`(**모든 MOS** σ_VGS를 수반 해석 한 번으로 출력까지 보내 RSS -- 다중 쌍·CMFB 오차증폭기 포함, matching 그룹 표지는 해석용 :13). 단일 입력 = 여기 방향 A_dc 환산은 card DE-1 (c)(1762·1777행) 소유 | 삭제 근거: "I-B22 닫힘 -- 모든 MOS 수반 RSS(`metrics/offset_analysis`), 단일 입력 A_dc 환산 = DE-1 (c)" | P: 쌍 ΔVth = 독립 소자 σ 두 개의 차라 소자별 σ RSS와 같은 분산(Pelgrom) -- 정합 |
| I-G1 | 1214 | 단일단 회로의 gm 출처 | 삭제(a) | U-12 확정(2466행 -- 구조로 판정, 판정은 DEC-92 GBW MNA). 태그 무시: `E/authoring/topology_schema.py:22`(`compensation` = IGNORED_TAG_KEYS), GBW 목표 출발값 `E/search/iv_speed.py:5` | 삭제 근거: "I-G1 닫힘 -- U-12(구조 판정·DEC-92)" | N: 태그·이름 무관 |
| I-G2 | 1215 | 3단 보상 stage 수 종속 일반화, nmcnr passive 누락(J9) | 삭제(a) | 회로별 보상 함수 없음 -- 보상 = DEC-70·DEC-92 일반 규칙(N6.1 단위 7), 극점 노드 `E/graph/pole_nodes.py:7`. 선언 실측: nmcnr `passive_elements` 5·`ports` 있음, two_stage 3(library topology 읽기, 2026-10-29); U-08 선언 완료(2462행) | 삭제 근거: "I-G2 닫힘 -- DEC-70/92 일반 보상 규칙, J9 선언 완료(U-08, library 실측)" | N: stage 수·회로 이름 분기 0 |
| I-G4 | 1216 | class-AB 정지전류 `ID_source` 타입(J3) | 삭제(a) | 정지전류 = θ 전류 기저 성분(DEC-70 전류 변수 정의, `E/sizing/current_basis.py:1-14` -- 원소 단위 KCL 해 공간의 자유 열), `kvl_branch` 등식 = `E/sizing/seal_kvl_branch.py`. 'ID_source 타입'이라는 별도 선언 필요 없음 | 삭제 근거: "I-G4 닫힘 -- 정지전류 = θ 전류 기저(DEC-70, `sizing/current_basis`)". J3 회로 해석 잔여가 있으면 N7.1 J3 행 몫(이 행 아님) | G: 전류 정본 = `dc_current_basis` 한 필드 |
| I-G5 | 1217 | 폴딩 노드 역할(J5 -- 축약 뷰가 출력노드를 잃는 경우) | 삭제(a) | 축약·비축약 둘 다 구함: `E/graph/view_analysis.py:12-16`(비축약 뷰에서 루프 탐지, 두 뷰 셀 판독 차 = `unreduced_diff`), DC 역할 `E/graph/dc_roles.py` | 삭제 근거: "I-G5 닫힘 -- `graph/view_analysis` 축약/비축약 대조(41 §1 불변식)" | F: 차이는 `unreduced_diff` 로 보고 |
| I-G6 | 1218 | stage 분할 구현 | 삭제(a) | 구현: `E/graph/stage_bfs.py:1-12`(0-1 BFS stage 시작 셀, N3.2-4·5) | 삭제 근거: "I-G6 닫힘 -- `graph/stage_bfs`" | -- |
| I-C6 | 1219 | 읽히지 않는 스키마 필드(`closed_loop_accuracy_db`, `stage_gm_ref`, `vdd_kvl`) | 삭제(a) | v5 닫힌 어휘: `E/authoring/spec_schema.py:5-8·22-33`, 밖 키 = `unknown_key` 거부 `E/authoring/_spec_fields.py:102`. 세 이름 엔진 grep 0 | 삭제 근거: "I-C6 닫힘 -- v5 spec 닫힌 어휘, 미지 키 거부" | F 충족 |
| I-C10 | 1220 (인용 2474) | `stack_headroom_slack_v` 담당·제약 여부 | 삭제(a) | U-20 확정(2474행 -- metric 삭제, 봉인 1·5로 흡수), 엔진 grep 0 | 삭제 근거: "I-C10 닫힘 -- U-20". 2474행 '(I-C10)' 표지만 제거 | -- |
| I-C11 | 1221 (인용 2638) | two_stage stage1_out 분리·nmcnr stage2_diode_ref 이월 | 삭제(a)+(b) | U-09 '해당 없음 -- 옛 엔진 국소 패치'(2463행, DEC-82) | 삭제 근거: "I-C11 대상 소멸 -- U-09". 2638행은 폐기 문서 목록이라 그대로 | R |
| I-H1 | 1222 (인용 399) | heldout 2회로 엔진 미실행 -- `cnr_ota` `dc_resistor_cycle`, `erfc_ota` `mos_zero_current_structural` | **필요**(엔진 일반성 -- (i) 저항 분압) + **질문**((ii) erfc 영역 선언) | 회로 해석인지 엔진 결함인지 연결로 판정: (i) `cnr_ota` 저항 x40 VDD_1V8–VCR, x39 VCR–net7, x3 net7–VSS(`A/heldout/cnr_ota.topology.json` passive_elements, 레일 = VDD_1V8·VSS) -- **레일 사이 고정값 저항 분압 사슬**이다. 물리: VCR·net7 전압 = Ohm + KCL 선형 해(게이트 부하 DC 전류 0) -- 정의역·해 유일(각 저항 넷이 고정 전압 노드에 저항 경로로 닿음). 엔진은 "저항을 종속시키는 규칙이 없음"으로 정지(`E/sizing/writer_plan.py:29-30`) → **엔진 규칙 공백**(회로 해석 아님). (ii) `erfc_ota` M19·M20(드레인 n_m5g·n_m6g = 커패시터 CBAT1_L/R와 게이트만), M21(드레인 n_m8g = CBAT2만) → DC 전류 구조적 0. 원문(Wu 2025 p.7 §3.2, `A/heldout/erfc_ota.spec_source.md:17`) "M19~M21 deep triode" -- 스위치(VDS = 0)다. 엔진은 `intended_region` 과 무관하게 정지(`E/sizing/current_basis.py:129-133`, `triode` 참조 0); spec `intended_region` = `{"pending": "CI-18"}`(`erfc_ota.sizing_spec.json:198-200`). 두 회로 모두 CPG-1(library 9회로) 게이트 밖이라 지금 card를 막지 않음 | (i) **새 card 권고**(기존 card 중 `writer_plan` W 티어 규칙을 소유하는 card 없음 -- LA-1은 범위가 이미 크고 IT-1은 입력 CM 변수 하나; 새 작은 card가 단순). 문언 초안: "card DR-1(이름 design) -- **고정값 저항 망 노드 writer**: S0 쓰기 계획에서 비트리 저항 엣지가 값 선언(또는 θ) 저항뿐이고 그 저항 넷들이 고정 전압 노드(레일·W 티어 기록 노드)에 저항 경로로 닿으면, 그 넷 전압을 같은 DC 블록이 노달 선형 해(Ohm + KCL, 게이트 전류 0) 하나로 쓴다(writer 하나 -- `dc_resistor_cycle` 정지 갈래를 대체, 닿지 않는 저항 섬은 정지 유지 -- fail-closed); 저항 전류는 `dc_current_basis` 의 저항 열을 이 해로 닫는다(새 필드 0 또는 1, 이름 design)." 착수 조건: 계획 개정(N3.4 W 티어 행 -- S-7) → design. 순서: IT-1 + IT-2 통합 병합 뒤(`writer_plan` 파일 겹침), CPG-1과 무관. 완료 조건: 분압 toy(base `dc_resistor_cycle` -- red) 노드전압 = 손계산 분압 tol_V 안, 저항 섬 toy 정지 유지, cnr_ota 단계 A가 다음 정지 사유까지 진행(사유 기록), library 9회로 발동 0·값 불변. (ii) 질문 후보 Q-4 | G: writer 하나, 새 cache 0. K: 해 = 선형 방정식(상수 0). N: 회로 이름 0(구조 조건). P: Ohm·KCL. F: 닿지 않는 섬 정지 유지. R: 정지 갈래를 규칙으로 대체(덧대기 아님) |
| I-H2 | 1223 (인용 11·223·394·680·2559) | A_dc 생산자 둘(`offset_analysis.py:74`, `offset_systematic.py:50`) | 삭제(a) | card DE-1 (c)가 완전 소유: 1762행('σ 입력 환산도 이 card … 정본 하나', '갈래 구현은 하나 … `offset_analysis.py:76`과 `offset_systematic.py:51-52`'), 완료 조건 1777행('갈래 하나: `git grep` …'). 엔진에 두 자리 현존 확인(`E/metrics/offset_analysis.py:74`·`offset_systematic.py:50` `a_dm = float(sense @ volt)`) -- DE-1 대상 그대로 | 삭제 근거: "I-H2 → card DE-1 (c) 소유(1762·1777행)". 인용 정리: 223행 'I-H2 정본을 READS' → 'DE-1 (c) A_dc 정본을 READS', 680행 'DE-1 (c)가 I-H2(A_dc 생산자 둘) 해소 때' → 'DE-1 (c)가 A_dc 생산자 둘을 합칠 때', 394행·11행은 결정·이력 기록이라 그대로 | G: 둘째 생산자 제거가 card 완료 조건 -- 정합 |
| I-H3 | 1224 (인용 11·345·680·1669·2386) | 측정 구성 창 전도 행(R0) 과보수, eps 문턱 단위 | 삭제(a) | eps 문턱 = N6.35 E-22(2386행, card IT-2c 범위 6). 과보수 = 사용자 결정 O-118 2번이 수용(345행 'ngcc 과보수 −146 ~ −376 mV 수용'), 안전 쪽(fail-closed -- 680행 '원칙 점검' 문단). 개선안은 만들지도 재지도 않았고 계획 개정 먼저(행 본문) | 삭제 근거: "I-H3 닫힘 -- 문턱 = N6.35 E-22, 과보수 = O-118 2번 수용(안전 쪽). 다시 열 조건: CMP-1·CPG-1 판정 기록에서 ICMR 제약이 SPICE 통과인데 엔진 FAIL인 회로가 생길 때(그때 계획 개정)". 680행 '백로그 I-H3(N5.3)' → '(O-118 2번 수용, 재개 조건은 위)', 1669행 '기록만(I-H3)' → '기록만(O-118 2번)' | F: 과보수 = 거짓 PASS 없음. P: 원인 축(전류 결정 방식) 기록 유지 |
| I-H4 | 1225 (인용 11·383) | ngcc_3stage_ff 단계 A `review_needed` `dc_role_unresolved_group M14,M8` | **질문** | 연결 실측(`A/library/ngcc_3stage_ff.topology.json`): M8 nmos (d NP, g V1, s gnd), M14 nmos (d Vout, g V1, s gnd), V1 = 첫 단 출력(M2·M4 드레인), Cm1 V1–Vout. 엔진 규칙: gs 묶음에 diode 기준이 없고 게이트 넷이 모든 뷰 교류접지가 아니면 멤버 전부 signal + `review_needed`(`E/graph/dc_roles.py:21-22`, J-U3-c). 물리 유도: V1은 신호 노드(교류접지 아님)라 두 소자는 V1이 구동하는 트랜스컨덕터(M8 = 둘째 단 CS, M14 = 출력 feedforward CS -- 원문 NGCC의 gmf) -- 역할 = signal, 두 전류 비 = W/L 비(θ), V1 DC = 첫 단 KCL. **엔진 결함 아님**(설계된 정지, 사실 승인 대기) -- 회로 해석 몫. 선례: `A/library/nmcnr_amplifier.structure.json` facts(`l_owner`, ratified) | 질문 후보 Q-3(§2). 행 처리: 승인 뒤 `ngcc_3stage_ff.structure.json` 사실 data 커밋(O-164 별도 항목 그대로) -- 행은 그 커밋으로 닫힘 | N: 사실은 structure.json data(코드에 이름 0). P: 위 유도 |
| I-H5 | 1226 (인용 11·383·1917) | sf_pushpull·current_reuse DC 봉인 실패 | 삭제(a) | 소유 card 실재: LA-0 실패 분류 표(1942·1947행 (b)), LA-1 범위 15 (f) CM 되먹임 DC 평형(1917행 -- 'current_reuse 봉인 실패 원인 후보 -- N5.3 I-H5'), LA-1 완료 조건 9 (e) sf 봉인 재현(1955행 -- 못 하면 계획으로 돌아옴). 실패 사실 `h_judgment.md:436-437` | 삭제 근거: "I-H5 → LA-0 분류·LA-1 범위 15 (f)·완료 조건 9 (e) 소유". 1917행 '-- N5.3 I-H5' → '-- `h_judgment.md` §5 Q3' | F: 재현 실패면 계획 복귀 조건 있음 |

## 2. 질문 후보(사용자 몫만)

| # | 행 | 물음 | 권고(근거·확신도) | ⚠ 원칙 |
|---|---|---|---|---|
| Q-1 | I-A13 (2) | U-67 (2) LOD(오라클 sa/sb/sd, 엔진·LUT 불변)를 지금 card로 만들지 | **보류 + 재개 조건** 권고: 엔진 판정을 바꾸지 않고 오라클 충실도만 올리는 항목이라 '엔진을 막을 때만'에 해당하지 않음. 만들면 엔진 `ly.lod` 생산자 + EO-1 생산자 칸 + oracle 넷리스트가 한 통합 병합이어야 함(만들면 배선). 재개 조건 = ME-1 기록에서 matching 관련 metric(`offset_in_sigma_mv` 등) 모델 오차가 그 축 분해능보다 클 때. 확신도 중간 | 사용자 결정(U-67 '나')을 일부 미루는 것이라 '원래 취지와 다름' -- 승인 필요 |
| Q-2 | I-A16 | (a) `res_high_po` 머리 면적 기하 식 ratify(레이아웃 기하 해석 = 사용자 ratify 대상, `A/sky130_pdk_decl.json:5` note) (b) 저항 분포 기생 C를 MNA에 넣을지 | (a) 규칙 번호 식 초안을 SF-1 design에서 내고 승인만. (b) **넣음** 권고(물리: 1 MΩ당 ≈ 125 fF가 CMFB PM을 5.9°까지 낮춤 -- `p4r_cm_sense.md` §3.3; 값은 고른 저항 종류의 셀 모델 crpf·crpfsw에서 계산, 발명 상수 0) -- 단 MNA 스탬프 변경이라 SF-1 범위 9가 아닌 별도 card(계획 개정 먼저, S-7). 확신도 중간(분포 RC를 양 끝 C/2로 근사하는 정확도 미측정) | (b)를 안 넣으면 PM 판정이 물리보다 낙관 -- fail-open 위험 |
| Q-3 | I-H4 | ngcc M8·M14 `dc_role` = 둘 다 signal(V1이 구동하는 CS 트랜스컨덕터, 전류 비 = θ) 사실 승인 | **(가) 사실 승인** 권고(연결 유도 위 §1, 원문 NGCC FF 단 -- 확신도 높음). 대안 (나) dc_roles 규칙 2 일반화('게이트 넷이 어느 뷰에서도 교류접지가 아니면 review 없이 signal')는 더 일반적이지만 J-U3-c 설계 결정 변경이고 반례 전수(바이어스 넷이 뷰마다 움직이는 경우) 미측정 -- 실측 뒤 별도 판단 | (가)는 회로 하나 data -- 일반화 원칙상 (나)를 실측 후보로 남김 |
| Q-4 | I-H1 (ii) | erfc_ota CI-18 `intended_region` 에 M19~M21 = `triode`(원문 p.7 §3.2 deep triode) 선언 승인 + 엔진 규칙 '`triode` 선언·구조적 0 전류 MOS = VDS 0 연결(노드 묶음)'을 DR-1 card에 넣을지 | **둘 다 예** 권고(원문 근거 있음, 확신도 높음; 엔진 쪽은 선언 없는 0 전류 MOS 정지 유지 -- fail-closed). heldout은 CPG-1 밖이라 순서는 CPG-1 뒤 | 선언 없이 엔진이 영역을 추정하면 안 됨(선언 필수 유지) |

## 3. 계획 안 인용 정리 목록(행 삭제와 같은 커밋)

164(I-A5) · 206(DEC-05 상태, I-B21) · 208(DEC-08 상태, I-B14) · 223(I-H2 → DE-1 (c)) · 225(DEC-25 상태, I-A10) · 279(DEC-80, I-A12) · 680(I-A6 머리·I-H2·I-H3) · 717(LR5, I-A15) · 1230(N5.4, I-A12·I-B21) · 1669(I-H3) · 1917(I-H5) · 2474(U-20, I-C10) · 2483(U-29, I-A6). 결정·이력 행(11 Status, 270 '오기' 기록, 345 O-118, 383 O-164, 394 O-71, 399 O-66, 2386 E-22 출처 칸, 2521 U-67, 2638·2641 폐기 문서 목록)은 기록이라 고치지 않는다 -- 단 383행 'N5.3 I-H4·I-H5'와 399행 'N5.3 I-H1'이 가리킬 자리가 사라지므로 '(N5.3 이관 -- 백로그 재감사 2026-10-29)' 한 마디를 덧붙이는 것을 권고. N5.3 머리 문장(1192행)은 표가 I-A13·I-A16·I-H1·I-H4 넷만 남으면 그대로 유효.

## 4. 곁 발견(이 범위 밖, 담당 감사에 넘김)

- 232행 DEC-32 상태 칸 '미구현'은 낡음(`E/sizing/scc_newton.py` 구현).
- 수치 rank(41 §4.5 B2) 빈 칸(`E/metrics/dof_report.py:9`) -- N6.1 단위 7 문언과 차이. 엔진을 막는 실례 미확인(불확실).
- `E/layout/mirror_trail.py:145` `_MAX_MIRROR_TRAIL_COMBO_PAIRS = 12` -- 복사 정의 안 근거 없는 상한(N6.35 예외 표 대상인지 확인 필요, 불확실).
- N4.1 IC 표 '담당 Phase' 열이 옛 Phase 표기.

## 5. 집계

| 판정 | 행 수 | ID |
|---|---|---|
| 삭제(a) 닫힘 | 22 | I-A5, I-A6, I-A7, I-A12, I-B3, I-B5·I-B6, I-B8, I-B11(행; 부속 IC11은 필요), I-B13, I-B14, I-B21, I-B22, I-G1, I-G2, I-G4, I-G5, I-G6, I-C6, I-C10, I-H2, I-H3, I-H5 |
| 삭제(a)+(b) | 2 | I-A10, I-C11 |
| 삭제(b) 대상 소멸 | 3 | I-A11, I-A15, I-B12 |
| 삭제(c)·(d) | 0 | -- |
| 필요(card 배정) | 3 행 + 부속 1 | I-A13 (1) → LI-1 범위 확장, I-A16 → SF-1 범위 9 확장, I-H1 (i) → 새 card DR-1(계획 개정 먼저), I-B11 부속 IC11 → SD-1 완료 조건 |
| 질문 | 4 | Q-1(I-A13 LOD 보류), Q-2(I-A16 머리 기하·저항 기생 C), Q-3(I-H4 ngcc dc_role 사실), Q-4(I-H1 erfc CI-18·triode 0전류 규칙) |

행 31개(ID 32개, I-B5·I-B6 한 행): 삭제 27행, 남는 행 4개(I-A13·I-A16·I-H1은 card 배정 뒤 삭제, I-H4는 Q-3 승인·data 커밋 뒤 삭제). 불확실 2건(I-B12 `mirror_symmetric_trail` 정준화 경로, 곁 발견 수치 rank 영향).


---

# 백로그 재감사 C -- gain-budget 계획 본문 미룬 항목·N7.2 열린 U·P9-M1(B4·B12·B13)

* 대상: `wt/plan-v6384/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` @ `9c45b431`(2672행). 줄 번호는 이 커밋 기준.
* 엔진 사실: `wt/integ-it12` @ `b12792ab`(계획 N3.3 배정표가 인용하는 커밋과 같음), `E` = `skills/analog-gmid-design/gmid_engine`. 읽기만 함.
* 범위 밖: N5.2·N5.3 표(다른 분석가 몫). N5.3 I-H3·I-H5를 본문이 인용하는 자리는 인용만 적었다.
* 사용자 지시(2026-10-29): "백로그에 있는 항목을 지금 규칙들과 원칙들로 다시 검증해서 불필요한 것들은 지우고 반드시 필요한 사항들은 바로 카드분배를 통해서 해결해."
* 판정 꼴: **삭제** (a) 이미 닫힘 / (b) 재작성(O-153·O-165·O-169)으로 대상이 사라짐 / (c) 원칙상 불필요 / (d) 전제가 물리상 틀림 · **필요** → card 배정과 문언 초안 · **사용자 몫** → 질문 후보 · **불확실**.
* 원칙 점검 약어: G = graph 단일 정본(규칙 1~6), K = 상수 발명 금지, N = 회로 이름 조건 금지, P = O-171(물리·회로이론 검증 첨부), R = O-153·O-165·O-169(재작성·덧대기 금지·소비자 없는 칸 삭제).

---

## 1. P9-M1 -- B4·B12·B13 '배정할 card가 없는 사안'(553행)

### 1.1 실측(층 순서와 IT-1 범위가 닿는 자리)

| # | 사실 | 근거(엔진 `b12792ab`) |
|---|---|---|
| F1 | `coupling_vars`는 단계 A4의 GB3 블록이다: READS = `S1_READS` + `graph/s1v: views·l_classes`, WRITES = `graph/coupling`. 층 순서 S1 → S1v(`build_s1v`) → `coupling_vars`라서, S1v 필드를 READS하게 바꿔도 층 역전이 없다 | `E/graph/coupling_vars.py:3`, `:171-183`, `E/pipeline/stage_a.py:12, :157` |
| F2 | `net_model(s1)` 호출 자리는 둘이다: S1v writer `s1v_fields`(`E/graph/s1v_fields.py:253`)와 `coupling_vars`(`:179`). 파생 술어는 `diode_nodes`·`composite_mos`·`composite_bundles`·`composite_internal`이고, 나머지(`by_gate`·`by_drain`·`mos_by_name` 등)는 투영이다(G2 접근자) | `E/graph/net_model.py:32-80` |
| F3 | **`graph/coupling`의 엔진 소비자는 0이다.** 읽는 곳은 단계 A 보고서(`E/pipeline/stage_a_report.py`)뿐이다. 계획상 소비자는 N6.1 단위 8의 'GB3 결합변수 y'(층 0·card LA-1)이다 | `git grep COUPLING_KEY`: `graph/*`·`pipeline/stage_a*.py`만 |
| F4 | **IT-1은 `coupling_vars`에 닿지 않는다.** 쓰기 계획(`writer_plan`)은 `coupling_vars`의 READS에 없으므로, IT-1 범위 1의 y 키 변경은 `coupling_vars` 값을 바꾸지 않는다. 553행이 '착수 실측'으로 남긴 질문의 답은 '아니다'이다. 통합 브랜치(merge-base 이후 엔진 diff)는 `graph/*`·`kernel_context.py`를 하나도 고치지 않았다. IT-1 재작성 범위 5 (a)가 S1 `gvgs_cycles.py`(S1 규칙 파일, `S1_RULE_FILES`)를 고치고, 5 (b)가 S1v 술어 블록을 새로 만든다 | `git diff --stat $(merge-base) HEAD`, 계획 1620행, `E/graph/s1_values.py:222-225` |
| F5 | B12 -- 정규화 레일 전위는 지금 세 자리가 각자 만든다. ① `build_s1`이 `supplies_declaration`으로 정규화한 뒤 `s1_bulk`·`s1_symmetry`에 extras로 넘긴다(필드가 아님, `E/graph/s1_build.py:71, :78, :89`) ② `build_kernel_context`가 `inputs.supplies_v`로 다시 정규화하고 S1 키 지문과 대조한 뒤(`E/sizing/kernel_context.py:60-63`) W0 블록 `dc_rails`에 extras로 넘긴다. `dc_rails`는 그 값을 `node.dc_rail_v`에 쓴다(`E/sizing/w0_rails.py:17-22`) ③ 로더 `authoring/spec_supplies.py:23-58`이 같은 넷 소속·유한성·누락 레일 검사로 정규화 tuple을 만든다. `graph/supplies.py:24-44`와 같은 이름·거의 같은 본문이다. 그 밖에 `spec.supplies_v`를 다시 읽는 자리도 있다: `E/metrics/achievability.py:266`, `E/search/iv_context.py:88`. **`node.dc_rail_v`(W0)와 B12 정본 'S1 필드'를 둘 다 두면 정의가 같은 필드 둘이다(G3)** | 파일 읽기 |
| F6 | B13 -- 배정표가 적은 둘째 생산자(`stage_b.py:151·153-156`·`search_context.py:164-168`) 밖에 생산자가 둘 더 있다. `E/metrics/achievability.py:115`(`UNTIE_ORBITS` 재파생)와 `E/search/iv_context.py:93`(`THETA_BOUNDS` 재파생). `dc_inputs_from_spec(spec)`도 두 번 불린다(`E/pipeline/stage_a.py:213` -- `symmetry_marks` 입력, `E/pipeline/stage_b.py:151`) | `git grep THETA_BOUNDS\|UNTIE_ORBITS\|dc_inputs_from_spec(` |

### 1.2 '(다) 백로그(N6.17 꼴)' 참조 확인(553행)

**오참조(꼴 불일치)다.** N6.17 백로그 (i)(2062행)는 **발동 0인 잠복 항목**이다. `counted_rails`가 둘 이상 선언될 때까지 정의가 갈리지 않는다. 반면 B4·B12·B13은 **지금 발동 중인 둘째 생산자**다. 매 실행 같은 입력에서 값을 다시 만든다. 두 꼴이 다르므로 'N6.17 꼴 백로그'는 근거가 되지 않는다. 계획 안의 맞는 선례는 N6.35(예외마다 소유 card 배정, 'card 아님'은 사용자 결정 대기 E-28 하나)와 N3.3 배정표 자체(B마다 기존 재작성 card)다. 그래서 (다) 백로그안은 ⚠ 대안으로만 남긴다. 사유는 둘이다. N6.3 기준선 래칫(1378행)에 B로 남고, 지시 "반드시 필요한 사항들은 바로 카드분배"와도 충돌한다.

### 1.3 배정 판정과 대안 비교(O-165 (a): 새 병합 순서 규칙 = 덧대기 신호, O-34 변경 종류 분리)

| 사안 | 안 | 성격 일치 | 새 순서 규칙 | critical path(LA-1 → CPG-1) | 변경 종류(O-34) | 판정 |
|---|---|---|---|---|---|---|
| B4 | (가) **IT-1 범위 재작성에 범위 6 추가**(오케스트레이터 재판정 기본안) | ⚠ IT-1 = 입력 공통모드·쓰기 계획 card(F4: `coupling_vars` 미접촉), S1v 술어 블록(범위 5 (b))과 층만 같음 | 0 | ⚠ IT 통합 병합이 LA-1·SF-1·SD-1·NU-1·TN-1·GV-1의 직접 선행이라 그만큼 늦어짐 | 동작 변경 card 안 순수 리팩터링 커밋(커밋 단위 변화표로 분리 가능) | 가능 -- ⚠ 성격 확장 |
| B4 | (나) **card DT-1 범위 확장**(분석가 권고) | DT-1 = S1 DC 사실 필드 정본화(교류접지 술어 → DC 이름 필드 하나, 소비자가 READS), **순수 리팩터링**. DT-1 범위가 이미 `coupling_vars` DC 쪽 재검토를 백로그로 적고(1834행) `net_model.py:48`을 소비자로 다룬다 | 0(DT-1 선행 '--', 1281행) | 영향 0(독립 card) | 같음(순수 리팩터링, `rule_hash`·S1 지문 변화 기록 절차가 이미 있음 -- DT-1 완료 (2)(3)) | **권고** |
| B4 | (다) GV-1 범위 5 | S1v writer `s1v_fields` 정본 READS 통일(같은 writer) | 0(IT 뒤) | 영향 0 | ⚠ GV-1은 동작 변경 card | 차선 |
| B4 | (라) 백로그(553행 기본안) | -- | 0 | 0 | -- | ⚠ 대안(래칫에 남음, 1.2) |
| B12 | (가) IT-1 범위 6(기본안) | IT-1 범위 5 (a)가 S1 규칙 파일을 고쳐 S1 지문이 이미 바뀐다는 점만 같음. 커널 문맥(`kernel_context.py`)·W0 `dc_rails`는 IT-1 범위 밖 | 0 | ⚠ (가)와 같음 | 순수 리팩터링 | 가능 -- ⚠ 성격 확장 |
| B12 | (나) **DT-1 범위 확장**(분석가 권고) | 같은 '레일 = DC로 고정된 넷' 사실군(DT-1 범위의 분류 (1) rail), 순수 리팩터링, S1 규칙 파일(`supplies.py`·`bulk_default.py`·`s1_build.py`) 지문 변화 절차 같음 | 0 | 영향 0 | 같음 | **권고** |
| B12 | (다) WB-1 범위 3 | DC 블록 재작성. 레일 값은 그 블록의 입력이라 자리가 다름(S1 vs 계획 층) | 0 | ⚠ WB-1도 LA-0 선행 | 동작 변경 card | 택하지 않음 |
| B13 | **SF-1 범위 6 (e) 추가**(오케스트레이터 재판정 = 분석가 동의) | spec 로더 단독 소유 card가 범위 6에서 B9~B11을 'S0 블록 필드 + 로더는 형식 거부만'(G1)으로 이미 넓혔다. B13은 같은 'spec 선언 파생값'이고, 범위 8(B14 `constraint_classes`)·범위 9(θ 수동소자 상자, `theta_bounds`)와 같은 파생 자리다 | 0 | 영향 0(SF-1은 IT 뒤·DE-1 앞, 기존) | SF-1 안 순수 리팩터링 커밋 | **필요 → SF-1** |

**분석가 권고 근거(B4·B12 → DT-1)**: 원칙 점검 기준은 '권고는 원칙과 일치', '검증자 수정안은 원칙 점검 후 내 권고로'다. 이 기준으로 오케스트레이터 재판정(IT-1)과 다르게 권고한다. **원래 취지와 다름 표시 대상**은 다음과 같다. (1) DT-1의 성격이 '이름 바꾸기 경미 card'에서 'S1·S1v DC 사실 필드 정본화'로 넓어진다 -- ⚠ card 성격 변화, 승인 필요. (2) IT-1안은 critical path 위에 순수 리팩터링 두 건을 더 얹는다. DT-1안은 독립 card라 순서 영향이 0이다. 결론은 둘 다 새 card 0·새 순서 규칙 0이고, 갈리는 축은 critical path와 변경 종류 분리뿐이다.

**만들면 배선(F3) ⚠**: B4는 소비자 0인 필드(`graph/coupling`)의 생산자를 정리하는 일이다. 엔진 소비자는 LA-1(N6.1 단위 8 'GB3 결합변수 y')이 배선할 때 생긴다. 그러므로 B4 정리는 '같은 실행 재계산 0'(NFR-2)의 몫일 뿐 소비 배선이 아니다. LA-1 design이 GB3 y를 쓰지 않기로 하면 B4 대신 `coupling_vars` 자체를 삭제 대상으로 올려야 한다(O-169 -- 소비자 없는 계산). 이 조건은 LA-1 design 착수 확인 항목으로 둔다.

### 1.4 문언 초안

#### (A) 기본안(오케스트레이터 재판정) -- N6.5 'IT-1 범위 재작성'(1606행 절) 범위 끝에 추가

> 6. **S1·S1v 같은 입력 재계산 정리**(N3.3 '같은 입력 재계산 배정' B4·B12 -- v6.38.4 P9-M1; **card 성격 확장 -- 원래 취지와 다름**: IT-1은 입력 공통모드·쓰기 계획 card였다. 근거 = 범위 5가 이미 S1 규칙 파일(`E/graph/gvgs_cycles.py`, `S1_RULE_FILES`)과 S1v 술어 블록을 고쳐 S1 규칙 지문·S1v writer가 이 card에서 바뀐다. 커밋 단위로 DEC-106·E-19와 분리한다):
> (a) **B12 정규화 레일 전위** -- 정본 = S1 필드 하나다. `node.dc_rail_v`의 writer를 S1 블록 하나로 옮기고(supplies 선언을 정규화하는 S1 블록 -- S1 키가 `supplies_v_fp`를 담으므로 같은 키면 같은 값), 필드 이름은 유지한다(소비자 무변경; W0 블록과 S1 필드를 따로 두면 정의가 같은 필드 둘 -- graph 규칙 3). 같은 변경에서 지운다: `E/sizing/kernel_context.py:60-63`(재정규화·지문 대조 -- 같은 값 한 자리라 불일치가 구조상 없음, 우회 아님), `E/sizing/w0_rails.py`(`dc_rails`·`DC_RAILS_WRITER`, `PLAN_WRITERS`에서 제거), `s1_bulk`·`s1_symmetry`(S1·커널 문맥 두 호출)의 `supplies` extras(필드 READS로), `DcInputs.supplies_v`(소비자 0이 되면 -- O-169). `E/metrics/achievability.py:266`·`E/search/iv_context.py:88`의 `spec.supplies_v` 재읽기는 필드 READS로 바꾸되, 각 파일을 재작성하는 card(GV-1 범위 1·LA-1 범위 15)와는 파일 겹침만 있다(나중 병합 쪽이 맞춤 -- 새 순서 규칙 0). 로더 `E/authoring/spec_supplies.py`의 넷 소속 검사(`graph/supplies.py`와 같은 계산)를 S1 블록 안 거부로 옮기는 일은 G1이다. 이것은 spec 로더 단독 소유 card SF-1 범위 6 몫이므로 이 범위는 S1 쪽만 맡는다.
> (b) **B4 S1v 파생 술어** -- `net_model`의 파생 술어(`diode_nodes`·`composite_mos`·`composite_bundles`·`composite_internal`)를 S1v 필드로 둔다(writer `s1v_fields` 하나; 투영 부분은 접근자 -- G2). `E/graph/coupling_vars.py:179`의 둘째 `net_model(s1)`을 지우고 `coupling_vars` READS에 그 필드를 더한다. 범위 1의 y 키 변경은 `coupling_vars`에 닿지 않는다(READS에 쓰기 계획 필드 없음 -- 실측 2026-10-29).
> **완료 조건 추가**: (i) `supplies_declaration` 정규화 호출 자리 = S1 블록 하나(`git grep`), `dc_rails` grep 0 (ii) `net_model(` 호출 = `s1v_fields` 하나 (iii) 순수 리팩터링 필드별 비교 -- 9회로 `node.dc_rail_v`·`graph/coupling`·`device.bulk` 값 같음(이산 정확, NFR-4). 변화표 원인 칸 'P9 B4·B12'는 DEC-106·E-19와 따로 둔다 (iv) S1 규칙 지문·S0 키 변화 기록(DT-1 완료 (3) 꼴) (v) N6.3 래칫 -- B4·B12 해소, 새 B 0.

#### (B) 분석가 권고안 -- N6.11 card DT-1 범위 끝에 추가(위 (A)의 (a)(b)와 같은 본문, 머리만 다름)

> **범위 추가(v6.38.4 P9-M1 -- N3.3 B4·B12; card 성격 확장 -- 원래 취지와 다름: 이름 바꾸기 card를 'S1·S1v DC 사실 필드 정본화'로 넓힘, 같은 S1 규칙 지문 변화 절차·순수 리팩터링)**: (a) B12 …(A)(a)와 같음… (b) B4 …(A)(b)와 같음 -- 이 항목으로 1834행 백로그('`coupling_vars` DC 쪽 소비 시 재검토')를 닫는다(그 백로그 문장 삭제; DC 쪽 소비자 배선 = LA-1 단위 8 GB3 y, LA-1 design 착수 확인 항목: GB3 y를 쓰지 않으면 `coupling_vars` 삭제 -- O-169).
> **완료 조건 추가**: (A)의 (i)~(v)와 같다. 변경 종류는 순수 리팩터링 그대로이고 DT-1 완료 (1)~(7)과 같은 판정 기준이다.
> **순서**: 독립이다(DT-1 행 1281 그대로). `kernel_context.py`·`w0_rails.py`가 WB-1 범위 3(DC 블록 재작성)과 파일 겹침이 있는지는 착수 때 grep한다. 겹치면 나중 병합 쪽이 rebase한다(새 순서 규칙 0).

#### (C) N6.28 SF-1 범위 6 끝에 (e) 추가(B13)

> (e) **spec → DC·탐색 입력 파생(N3.3 B13 -- v6.38.4 P9-M1, 범위 6 확장 -- 원래 취지와 다름, 같은 '로더 단독 소유 → 파생값은 S0 블록 필드' 꼴)**: 파생(`theta_bounds` 상자 선언 추출 `spec_bounds`, `untie_orbits` 이름 목록 `untie`, `symmetry_marks(dc_inputs_from_spec(spec))`)을 S0 필드로 둔다. writer는 S0 블록 하나다(블록·이름은 design; 범위 8 제약 분류 블록과 합칠지도 design). 단계 A·단계 B·탐색 문맥·GB4는 그 필드를 READS한다. `DcInputs` 투영 부분은 접근자다(G2·G6). 지울 둘째 생산자: `E/pipeline/stage_a.py:213`, `E/pipeline/stage_b.py:151, :154-156`, `E/search/search_context.py:164-166`, `E/metrics/achievability.py:115`, `E/search/iv_context.py:93`. 범위 9가 `theta_bounds` 상자 규칙을 바꾸면 같은 필드의 writer 본문이 바뀐다(새 자리 0). `iv_context.py`는 LA-1 범위 15와 파일 겹침만이고, 나중 병합 쪽이 맞춘다(N6.1 관행 -- 새 순서 규칙 0). 완료 조건 추가: 파생 호출 자리 = S0 블록 하나(`git grep THETA_BOUNDS|UNTIE_ORBITS` 엔진 소비 = 그 블록 하나), 순수 리팩터링 필드별 비교(9회로 `search_domain` 결과 같음), N6.3 래칫 B13 해소.

#### (D) N3.3 553행 문단 교체 초안

> **배정할 card가 없던 사안 -- 배정 확정**(v6.38.4 P9-M1, 사용자 지시 2026-10-29 '백로그 재검증 → card 분배'): B4·B12 → card DT-1 범위 추가(분석가 권고 -- 대안 IT-1 범위 재작성 범위 6 ⚠ critical path) / B13 → card SF-1 범위 6 (e). 옛 (다) 'N6.17 꼴 백로그'는 꼴이 맞지 않아 지운다. N6.17 (i)은 발동 0 잠복 항목이고 B4·B12·B13은 발동 중인 둘째 생산자다. 배정표 B4·B12·B13 행의 '배정 card' 칸과 지울 둘째 생산자 목록에 F5·F6 추가분(`authoring/spec_supplies.py` 넷 소속 검사 -- SF-1 범위 6, `metrics/achievability.py:115·266`, `search/iv_context.py:88·93`)을 더한다.

---

## 2. 본문에서 미룬 항목(N5.2·N5.3·N7.2 밖)

| ID | 출처 줄 | 내용 | 판정 | 근거 | 처리(문언 초안 포함) | 원칙 점검 |
|---|---|---|---|---|---|---|
| P9-M1 | 553 | B4·B12·B13 배정 card 없음 | **필요** | 1절 | 1.4 (B)·(C)·(D) | G 1·3·4·6 직접 해당, R(덧대기 아님 -- 기존 card 범위), K·N 해당 없음, P = 원칙 정합(G0~G7, 물리 결정자 대상 아님) |
| GB-1834 | 1834 | DT-1 '`coupling_vars` DC 쪽 소비 시 재검토 -- 백로그' | **필요 → DT-1(B4와 합침)** | F1~F3: `coupling_vars`는 S1·S1v만 읽고, 그 DC 쪽 소비자는 LA-1(단위 8 GB3 y)이다 | 1.4 (B) '1834행 백로그 문장 삭제' + LA-1 design 착수 확인 항목(GB3 y 미사용이면 `coupling_vars` 삭제) | G, R(O-169 소비자 0 계산 삭제 조건), 만들면 배선 |
| GB-2062(i) / GB-691 / GB-2253 | 2062, 691, 2253 | `supply_current_dc` ↔ oracle `supply_current_A`: `counted_rails` 둘 이상이면 정의 정정 필요, 그때까지 발동 0 | **필요(조건부 문언을 무조건으로) → SF-1 범위 8 + oracle-portability 후속 정정** | 정의 갈림이면 O-29 (1)·O-32 위반이 된다. 지금은 '첫 선언 data 커밋 전 같은 통합 병합'이라는 **조건부 병합 순서 규칙**인데, 이 꼴이 O-165 (a)의 덧대기 신호다. 엔진 `supply_current_dc`와 OP-11 `power_dc_w`가 이미 같은 `counted_rails` 집합을 읽게 되므로(SF-1 범위 8, oracle v0.6.19), oracle `supply_current_A`도 그 집합 Σ I로 정의하면 레일 하나일 때 값이 같아 조건이 없어진다. held-out data에 레일 둘 이상 선언이 들어가는지는 **불확실**(N12 판정값 미확인) | SF-1 범위 8 문장 '선언 레일이 둘 이상인 첫 data 커밋 전에 … 같은 통합 병합에 넣는다(N6.17 백로그 (i))'를 다음으로 바꾼다: "oracle `supply_current_A`의 정의 = 셈하는 레일 집합(`counted_rails`, EO-1이 싣는 같은 칸)의 Σ 레일 전류 -- 엔진 `supply_current_dc`와 같은 정의 하나(O-29 (1)·O-32), 레일 하나면 값 불변(비교 대상), 정정 자리 = oracle-portability 계획(그 계획 후속 정정 행), 완료 toy = 레일 둘 선언 toy에서 엔진·oracle 값 같음". 691행 'N6.17 백로그' 문구 → 'SF-1 범위 8', 2062행 (i) 삭제 | G 3(같은 이름 다른 정의 금지), R(조건부 순서 규칙 제거), P(정의 = SPICE `.op` 레일 전류 합 -- 해석 종류 같음) |
| GB-2062(ii) / GB-2058 | 2058, 2062 | `Role: data` 트레일러 정식 등록(N3.12.3 역할 표·EL3·`role_paths.py`) | **삭제 (c)** | N3.12 역할 분리·N3.12.4 EL1~EL4·N4.2 V1~V10은 '폐기(2026-10-07, gate 끔)'(772·901·1068행, DEC-86)다. 엔진을 막지 않는 인프라다('인프라는 엔진을 막을 때만') | 2062행 (ii) 삭제, 2058행 '정식 등록은 백로그 행이다(이번 범위 아님)' 삭제 -- 트레일러는 관례 인용만 | R, 인프라 원칙 |
| GB-1665 | 1665 | IT-2 '(W4 창 VDSAT 하한 백로그(감사 S3)는 N6.35 E-13으로 닫힘 …)' | **삭제 (a)** | 본문이 스스로 닫힘을 적었다(E-13 = WB-1 범위 3a-0·3a, 2377행) | 괄호 문장을 history로 옮기고 본문에서 삭제(계획/이력 분리) | -- |
| GB-1669 | 1669 | IT-2 완료 조건의 '백로그 B77, IT-2d에서 해소(O-111·O-112)' | **삭제 (a)** | 같은 문장에 해소 자리가 적혀 있다 | '백로그 B77' 표지를 지우고 'IT-2d 범위(O-111·O-112)'만 남김 | -- |
| GB-1857 | 1857 | DE-1 후속 정정 표 headroom-chain 행 'VGS 등식 소속 휴리스틱 공동분석 백로그는 O-23·O-26으로 닫힘(삭제)' | **삭제 (a)** | 행이 스스로 닫힘을 적었다 | 그 구절 삭제 | -- |
| GB-1598(gc) | 1598 표 graph-consumption 행 | IT-1 관련 계획 후속 정정 -- graph-consumption card id 자리(F-G19·465·593-595·R-G6) 옛 문구 | **삭제 (a)** | `wt/plan-v6384/docs/01-plan/features/graph-consumption.history.md:310` -- 'card id 없음/미부여'를 IT-1로 정정한 기록이 있고, 현 `graph-consumption.plan.md`에 'card id 미부여' grep 0 | 표 행을 '정정됨 -- 남은 일 없음'으로 바꾸고, 두 행 모두 닫혔으므로 표를 history로 옮김 | -- |
| GB-1734·1852·1965 | 1734, 1850-1862, 1965-1990 | SH-1·DE-1·LA-1 '관련 계획·문서 후속 정정' 표(다른 계획·design이 자기 개정에서 고침) | **불확실(이 계획 백로그 아님)** | 행마다 다른 문서의 이행 여부를 재지 않았다(이 분석 범위 밖). 표본 1건(GB-1598)은 이행됨 | 처리: 각 계획·design 재감사 몫으로 넘긴다. 이행된 행은 history로 옮긴다(계획/이력 분리 원칙) | -- |
| GB-1873 | 1873 | (A_lo 범위 밖이면 보고) | 미룬 일 아님 | 정의 문장 | -- | -- |
| GB-2228/2230 | 2228, 2230 | GV-1 '`l_classes._main_path_starts`는 범위 밖' | **삭제 (a)** | 2230행 '범위 3 추가'(N6.35 E-10)가 대체했다 | 2228행 (4) 문장 삭제(범위 3 추가와 모순) | G 3 |
| GB-2324 | 2324 | WB-1 '레이아웃 뒤 루프 … 어긋나는 구현은 그 루프 소유 card의 재작성 범위로' | **필요(소유 card 명시)** | 레이아웃 뒤 루프(MOD8·재필터)의 소유는 N6.1 '구현 단위 9'(1253행)와 2401행 R12 = 단위 9(E-24)다. '그 루프 소유 card'라는 불특정 지칭이 문제다 | 2324행 '그 루프 소유 card'를 'N6.1 구현 단위 9(MOD7·MOD8 -- 2401행 R12, E-24)'로 바꾼다 | 문언 정합 |
| GB-2194 AP-1 | 2194-2197 | AP-1 미래 card -- 착수 조건 = 계획 개정(응용 topology 스키마·writer 정본 자리 없음, 규칙 6); (c) current_reuse 슬루 입력 망(O-72 (4) 공동분석 백로그) | **필요 + 사용자 몫** | current_reuse `settle_s`·static settling·출력 범위 판정이 'AP-1까지 판정 대기'다(SF-1 완료 (3), U-119). 엔진 판정 완결성을 막으므로 필요하다. 정본 자리가 없으면 멈추고 계획부터 고친다(규칙 6, S-7) | 질문 후보 Q-C1: 'current_reuse 응용 회로(Cf1·Cf2·Cs 하판 계단 원천 등)의 connectivity 선언 -- 사용자 작성(connectivity는 사용자만)'. 그 뒤 계획 개정 card(응용 topology S0 블록 writer 하나) → design | G 6, N(응용 망은 선언으로만), P(용량 전용 노드 전하 보존 DC 해 = 물리 결정자) |
| GB-2202 NB-1 | 2202-2205 | NB-1 β = 1 폐루프 잡음(미래 card) | **삭제 (c)** | 실측: `feedback.elements = []`인 12회로(library 8·heldout 4) 모두 잡음 제약 0(`noise_out_int_vrms` 선언은 current_reuse 하나이고 그 회로는 Cf1·Cf2 선언). 소비자가 없으니 만들어도 쓰이지 않는다('만들면 배선') | N6.24·N6.1 1267행 삭제, NU-1(정의 불능 표지)만 유지. 재개 조건(spec이 `()` 회로에 잡음 제약을 선언할 때 계획 개정)은 history에 한 줄 | 만들면 배선, R(O-169) |
| GB-163/164 | 163, 164 | 왜곡·ss/ff 코너 기록 옵션 '범위 밖' | 미룬 일 아님(비목표 -- 사용자 승인 P-14) | 범위 정의 | 유지 | -- |
| GB-1339/1392/1463/2599/2615 | 같은 줄 | 마일스톤·옛 엔진 대조 '범위 밖'(P-14) | **삭제 (a) -- 본문에서 history로** | 사용자 결정 P-14로 닫혔다. 1339행은 스스로 '기록으로만 남는다'고 적었다 | 1339행 '마일스톤 1' 절을 history로 옮긴다(계획/이력 분리). 나머지는 한 줄 인용 유지 | -- |
| GB-784 | 784 | N3.12.0 위협 범위 '범위 밖 -- 필요해지면 계획 개정' | **삭제 (c)** | N3.12 전체 폐기(gate 끔, DEC-86) | 폐기 절 본문을 history로 이관(머리 한 줄만 유지) | 인프라 원칙 |
| GB-2392 E-28 | 2392 | 재시작 반경 m = U-47 보류 | **사용자 몫** | 아래 U-47 | U-47 처리 따름 | -- |
| GB-2384 E-20 | 2384 | oracle 출처 미확인 상수 다섯 → oracle-portability 다음 판 card | 범위 밖(다른 계획) | oracle 계획 몫 | 그 계획 재감사로 넘김 | K |
| GB-2401 | 2401 | design 40 §8 '복원' 남은 일 소유 | 미룬 일 아님(모두 소유 card 있음) | R2·R8·R11 LA-1 / R5 UB-1 / R9 DE-1·SB-1 / R12 단위 9 / R21 LI-1 / R22 SF-1·WB-1 / R14 SF-1 | 유지 | -- |
| GB-553 문구 | 553 | 'LA-1 범위 15(c)는 백로그로 둠' | **불확실** | LA-1 범위 15 (c)(1917행)는 `mirror_vds` 목표 행이고 `coupling_vars`와 무관하다. 무엇을 백로그로 둔다는 뜻인지 문맥이 불분명하다 | 1.4 (D) 교체로 그 구절이 함께 사라진다 | 문언 정합 |

---

## 3. N7.2 사용자 결정 U -- 열린 행(닫힘·확정·해당 없음·폐기·대상 소멸 행 제외)

필터: N7.2(2449-2590행) 138행 가운데 '닫힘·확정·결정됨·해당 없음·폐기·대상 소멸·대체'가 없는 행과, 확정 표기가 있어도 '실측 후'·'보류'·'미결'이 남은 행을 모두 읽었다.

| ID | 출처 줄 | 내용 | 판정 | 근거 | 처리(문언 초안 포함) | 원칙 점검 |
|---|---|---|---|---|---|---|
| U-07 | 2461 | 전력 정의 변경 기대값 한 승인 묶음 | **삭제 (b)** | 기준선·기대값 갱신은 O-34 (1) '변경 종류별 판정 기준'(1382행)과 IT-Q3 (가)(검증자 변화표 → test 주체 별도 커밋)가 대체했다. 전력 대조는 PW-1a·PW-1b(N6.17)가 소유한다. '7a' 단계는 폐기된 Phase 체계다 | 행을 '닫힘 -- O-34 (1)·N6.17로 대체'로 바꾸고 history로 이관 | R |
| U-08 | 2462 | folded·nmcnr·two_stage `ports` | **삭제 (a)** | '2026-09-17 선언 완료(9/9)' | 닫힘 표기 | -- |
| U-13 | 2467 | 파일럿 면적 예산 선언 여부·값 | **삭제 (a)** | 실측: library 9회로 spec 모두 `area_search_m2` 제약 선언(`assets/library/*.sizing_spec.json` grep 9/9). 미선언 시 규칙은 DEC-77 | 닫힘 표기('9/9 선언 -- data') | N(회로 이름 무관) |
| U-18 | 2472 | 기준 약화 개별 승인 | **삭제 (열린 결정 아님)** | 상시 절차 규칙이다(O-155 B1 반영). 결정 대기 항목이 아니다 | N2.2 작업 방식 원칙 또는 N6.3으로 옮기고 U 행 삭제 | -- |
| U-19 | 2473 | `gain_db >= 54` 재도출·교체 | **삭제 (a)/(d)** | `>= 54`는 current_reuse 하나만 남았는데(실측 `current_reuse_telescopic_ota.sizing_spec.json` `gain_ss_db >= 54`), SF-1 범위 5가 O-133으로 지운다. 나머지 gain 제약은 모두 `user_spec` 값(two_stage 57, ngcc 111, nmcnr 100, sf 65)이다. 'SPICE에서 재도출'은 spec 값을 엔진·SPICE로 만드는 꼴이라 'spec 값은 사용자 몫·출처 있는 선언'(N3.15)과 충돌한다(d) | U-19·DEC-50(249행) 닫힘 표기('O-133 삭제 + 나머지 user_spec') | K, P |
| U-21 | 2475 | 선언 L theta(`L_cascode`·`L_stage2out_*`) 삭제 | **삭제 (b)** | 새 엔진은 S1v L 동치류만 쓴다(DEC-18). 실측상 그 이름은 topology 주석·`_TEMPLATE` 설명·태그(analog-grammar 산물)에만 있고 엔진·spec 소비 0이다. LT-1(DEC-99)이 태그를 지운다 | 닫힘 표기('LT-1') | R, analog-grammar 금지 |
| U-23 | 2477 | 입력-캐스코드 같은 L 강제 복원(DEC-04) | **삭제 (d) -- 사용자 확인 동봉** | 강제할 물리 결정자가 없다. DEC-04(소자마다 독립 변수, 결합은 제약·목적이 만듦)·'규칙은 물리 정합 최우선, 제한은 물리 근거 있을 때만'에 어긋난다. 선측정도 면적 +2.8~5.9 %로 A 유지다. 레이아웃 L 종류 수는 LY 규칙 몫이다 | U-23 닫힘('A 유지 -- 강제 규칙 두지 않음'), DEC-04(205행) '복원할지는 7b 실측으로 정한다(U-23)' 문장 삭제. 사용자 질문 후보 Q-C2(일괄 승인 묶음 안 한 줄) | P(물리 결정자 없음), 규칙 물리 우선 |
| U-24 | 2478 | 루프 뷰 안정도 제약 선언(CM 루프 예외) | **삭제 (a)** | E-33 = GV-1 범위 4가 소유한다(2232·2397행). CM 루프 PM 값은 회로별 spec(current_reuse 선언됨) | '닫힘 -- GV-1 범위 4(E-33)' 표기 | -- |
| U-46 | 2500 | SPICE 오차 처리(합격 임계·노드전압 기록·조여서 1회 다시 풂) | **삭제 (a) -- 일부 불확실** | 합격 = DEC-90 (1)·N3.6 (ii), 노드전압 = T8 기록만(N3.6), 모델 오차 기록 = DEC-72, 여유 바닥 = NFR-5 max(분해능, 모델 오차). '그만큼 조여 1회 다시 푼다'는 NFR-5 여유 바닥이 같은 뜻인지 **불확실**하다(재풀이 1회 규칙은 다른 자리에서 찾지 못함) | 닫힘 표기('DEC-72·DEC-90 (1)·NFR-5'). 재풀이 1회가 따로 필요하면 LA-2 범위에서 정한다(오케스트레이터 확인) | G(모델 오차 = 선언값 하나) |
| U-47 | 2501 | front 시간 예산(재시작 반경 m, E-28) | **사용자 몫** | 값이 사용자 정책이다. 기본 풀이 1회 300 s(DEC-34)는 있다. 필요 시점은 LA-1 완료 조건 9(front 생성)·CPG-1 판정 전 | 질문 후보 Q-C3: 'front 전체 시간 예산(초)과 재시작 반경 m -- 기본안: front 예산 = 300 s × front 점 수 상한(실측 1회 시간 기준), m은 cProfile 실측 뒤'. 기한 = LA-1 design 착수 전 | K(값은 사용자) |
| U-50 | 2504 | 역할 태그 범위(유도 입력 아님) | **삭제 (b)** | LT-1(DEC-99)이 태그를 지우고 `IGNORED_TAG_KEYS` 허용·무시를 유지한다(1422행). 규칙이 LT-1 범위에 들어 있다 | 닫힘 표기('LT-1 (1) 스키마 A') | analog-grammar 금지 |
| U-52 | 2506 | 이상 전류원 정본(선언값 정본, null이면 엔진) | **삭제 (a)** | 구현됨: `E/sizing/kernel_context.py:72-73`이 `(이름, 값 또는 None)`을 `dc_current_basis`에 넘기고, DEC-08이 이를 규칙으로 정한다 | 닫힘 표기 | -- |
| U-57 | 2511 | 진단 뒤 면적 예산 안 해 없음 | **삭제 (a)** | '확정(Q8): 예산 유지'. 재논의는 사건이 생길 때 하는 일이다 | 닫힘 표기, 재논의 조건은 N8 위험 표 한 줄로 | -- |
| U-75 | 2529 | A' held-out 회로 선정 | **사용자 몫 -- 불확실** | `assets/heldout/`에 4회로(cnr·erfc·r2r·rfc) spec이 이미 있다. 이것이 A' 선정 확정인지 계획에 기록이 없다 | 질문 후보 Q-C4: 'A' held-out = heldout 4회로로 확정하나'(확정이면 U-75 닫힘). 기한 = CPG-1(U17 단계 ②) 판정 전 | N(선정은 사용자) |
| U-76 | 2530 | A' 판정 세부 기본안(오케스트레이터 원칙) | **삭제 (열린 결정 아님)** | '결정은 원칙으로 기본안부터'에 따라 원칙 기본안으로 확정된 규칙이다. 사용자 변경 가능 표지만 남아 있다 | CPG-1(N6.34) 완료 조건으로 옮기고 U 행 닫힘 | -- |
| U-112 | 2566 | 슬루 oracle 탐색 쪽 배선 | **삭제 (a)** | 필요 시점 칸에 '닫힘(FAIL 점 front 제외·기록 = card LA-1 front 판정 …)', 되먹임 없음 = O-144로 닫힘 | 닫힘 표기 정리 | -- |
| U-113 | 2567 | class-B·저바이어스 출력 소자 gm/ID 동작점(O-121 B-4) | **삭제 (b) 권고 -- 사용자 확인 필요** | B-4는 O-121 '슬루 엔진 틀'의 한 항목이다. O-122가 엔진 슬루 관여를 없앴다('엔진 슬루 행·슬루 몫 필드는 소비자 0이라 삭제'). DC 동작점의 gm/ID는 θ 탐색이 정하므로(DEC-04·DEC-88) 따로 정할 규칙 대상이 남지 않는다. 다만 사용자가 '실측 후 결정'으로 유보한 항목이라 사용자 확인이 필요하다('사용자 결정도 재검토 대상') | 질문 후보 Q-C5(일괄 승인 묶음 한 줄): 'U-113은 O-122로 대상 소멸 -- 닫음'. 닫히면 Status(11행)·681행 인용 정리 | P(물리 결정자 = θ 탐색, 슬루 = oracle `.tran`) |
| U-117 | 2570 | F 밀도 둘 이상 고리의 R5′ 재개방 | 유지 -- **card LA-1(기존)** | 재측정 자리 = LA-1 design 착수 | 변경 없음 | -- |
| U-118 | 2571 | 정착 대역폭 출발 목표 β 읽는 점 | 유지 -- **card LA-1 design(기존)** | 같음 | 변경 없음 | P(β 0.086 대 0.5 실측 갈림) |
| U-119 | 2572 | static settling 0.1 % 달성 불가 시 완화 | **삭제 (열린 결정 아님)** | 기본 규칙이 이미 정해졌다(미리 완화 안 함, fail-closed front 빔). 그때 묻는 것은 사건 대응이다 | U 행 닫힘('규칙 = fail-closed'), 위험 문언(대신호 항)은 N8 위험 표로 이관 | fail-closed |
| U-121 | 2574 | follower 출력 범위 ∩ ICMR 공집합(B87) | **삭제 (a)** | 판정 자리가 정해졌다: N3.8 '과도 측정 유효성 조건'(계단 입력 구간 ⊆ follower 사용 범위 -- O-157 S1 (3))이 공집합이면 측정 무효 = 판정 불능으로 처리한다(fail-closed). 엔진 규칙은 두지 않는다(DC/AC 분리 -- 범위는 oracle `.dc`). 첫 사례(1.15 V 계단)도 S1로 사라졌다 | 닫힘 표기('N3.8 유효성 조건') | P, fail-closed, DC/AC |
| U-122 | 2575 | 약반전 pfet BSIM vdsat 바닥 -- 포화 판정 낙관(B88) | **필요 → 측정 = card LA-0(card 0, 엔진 무변경), 규칙 = headroom-chain HC-S** | 엔진 물리 정합 문제다. 봉인 7(`vds_ge_vdsat`)이 약반전에서 거짓 PASS를 내면 fail-open이다. sf_pushpull 봉인 실패 해석(I-H5)도 이 결과에 달려 있다(1226행 'LA-0 측정에 넣고') | LA-0(card 0) 측정 목록에 추가할 문언: "**B88 약반전 포화 대조**(U-122): library 봉인점 가운데 gm/ID ≥ (약반전 판정 -- 정의는 LUT 열, 새 상수 없음) 소자마다 엔진 `vds_ge_vdsat` 판정과 SPICE `.op` gds 기준 포화(같은 점·같은 기하) 대조표; 불일치 1건 이상이면 규칙 정정은 `sat_threshold` 정본 card(headroom-chain HC-S) 범위로 보고, 0건이면 U-122 닫힘". 완료 측정 = 대조표 판정 기록 id | P(BSIM vdsat 정의 대 gds 기준 -- 실측), fail-closed, K(약반전 문턱은 LUT/정의에서) |
| U-123 | 2576 | oracle 입력 생산자 출력 부하 이중 계상(B89) | **삭제 (a) -- 이미 card 배정** | N6.35 E-23(2387행): 규칙 = EO-1 범위 '출력 부하 한 번만', `legacy_adapter`는 LT-1 순서 3이 삭제, 재측정 = EO-1 생산자 경로 | U 행 '닫힘 -- E-23(EO-1·LT-1), 재측정 = EO-1 완료 조건' | G(부하 선언 한 자리) |
| U-124 | 2577 | 그 밖 B 밀도 K-1 (ii) 방향 | 유지 -- **card LA-1 완료 조건 9 (c) 측정 뒤 사용자 결정(기존)** | 측정 자리가 있다 | 변경 없음 | -- |

그 밖에 '확정·닫힘' 표기가 있는 행(U-01·04~06·10~12·14·16·17·20·22·25~45·48·49·51·53~56·58~74·77~111·114~116·120·125~134)은 열린 결정이 아니다. U-25·26·27·31·36·37·44는 '확정' 문언 안에 옛 Phase 시점(7a·7b)만 남아 있어 표기 정리 대상이고, 판정은 바꿀 것 없음(a)이다.

---

## 4. 질문 후보(사용자 몫만)

* Q-C1(AP-1): current_reuse 응용 회로 connectivity 선언 -- 사용자 작성. 그 뒤 AP-1 착수 조건 계획 개정.
* Q-C2(U-23): 같은 L 강제 복원하지 않음(A 유지)으로 닫음 -- 일괄 승인 한 줄.
* Q-C3(U-47): front 시간 예산·재시작 반경 m 값.
* Q-C4(U-75): heldout 4회로 = A' 선정 확정 여부.
* Q-C5(U-113): O-122로 대상 소멸 -- 닫음 확인.
* 승인 필요(card 성격 변화 ⚠): B4·B12 → DT-1(분석가 권고) 대 IT-1(오케스트레이터 기본안), B13 → SF-1 범위 6 (e).

## 5. 집계

| 구분 | 수 | ID |
|---|---|---|
| 검토 항목 | 45 | 본문 21(P9-M1 포함), N7.2 열린·준열린 U 24 |
| 삭제 (a) 이미 닫힘 | 16 | GB-1665, GB-1669, GB-1857, GB-1598(gc), GB-2228/2230, GB-1339 계열, U-08, U-13, U-19, U-24, U-46(일부 불확실), U-52, U-57, U-112, U-121, U-123 |
| 삭제 -- 열린 결정 아님(규칙으로 이관) | 3 | U-18, U-76, U-119 |
| 삭제 (b) 재작성·대체로 대상 소멸 | 4 | U-07, U-21, U-50, U-113(사용자 확인) |
| 삭제 (c) 원칙상 불필요 | 3 | GB-2062(ii) `Role: data` 등록, GB-784 위협 범위, GB-2202 NB-1 |
| 삭제 (d) 물리 전제 틀림 | 1 | U-23(사용자 확인 동봉) |
| 필요 → card 배정 | 5 | P9-M1(B4·B12 → DT-1 권고 / IT-1 대안, B13 → SF-1 범위 6 (e)), GB-1834(→ DT-1, B4와 합침), GB-2062(i) supply_current 정의(→ SF-1 범위 8 무조건 문언 + oracle 후속 정정), GB-2324(→ 단위 9 명시), U-122(→ LA-0 측정 + HC-S) |
| 필요 + 사용자 몫 | 1 | GB-2194 AP-1(Q-C1) |
| 사용자 몫(질문 후보) | 2 | U-47, U-75(불확실) -- U-23·U-113은 삭제 판정에 확인 동봉 |
| 유지(기존 card 소유) | 4 | U-117, U-118, U-124, GB-2401 |
| 범위 밖·미룬 일 아님 | 4 | GB-163/164, GB-1873, GB-2384(E-20 oracle), GB-2392(U-47로) |
| 불확실 | 2 | GB-1734·1852·1965 후속 정정 표 이행 여부, GB-553 'LA-1 범위 15(c) 백로그' 구절 뜻 |

(집계 주: 주 판정 하나로만 셌다. 행 안의 부분 불확실 -- U-46 '1회 다시 풂', U-75 heldout = A' 여부, GB-2062(i) held-out 레일 둘 이상 선언 여부 -- 은 그 행에 적었다.)

**발견(배정표 보강 필요)**: (1) B12 둘째 생산자 목록 누락 -- `E/authoring/spec_supplies.py:23-58`(로더 넷 소속 정규화 -- SF-1 범위 6 G1 몫), `E/metrics/achievability.py:266`, `E/search/iv_context.py:88`. (2) B13 누락 -- `E/metrics/achievability.py:115`, `E/search/iv_context.py:93`, `E/pipeline/stage_a.py:213`. (3) B12 정본 문언 'S1 필드'를 그대로 두면 W0 `node.dc_rail_v`와 정의가 같은 필드 둘이다 → writer 이동(필드 하나)으로 써야 한다. (4) `graph/coupling` 엔진 소비자 0 -- B4 정리와 별도로 LA-1 design에서 GB3 y 소비를 확인하고, 쓰지 않으면 `coupling_vars`를 삭제한다.


---

# D. 하위 계획 다섯 백로그 재감사 (읽기 전용 분석, 2026-10-29)

* 대상 판: `wt/plan-v6384` HEAD `9c45b431`(상위 gain-budget v6.38.4 열둘째 커밋). 하위 계획 판: oracle-portability v0.6.22, graph-consumption v0.14.5, headroom-chain v0.7.9.5, offset-strategy v0.7.5, offset-trim v0.6.2.
* 엔진 사실: `wt/integ-it12` `b12792ab`(`E` = `skills/analog-gmid-design/gmid_engine/`, `O` = `skills/analog-gmid-design/tools/spice_oracle/`). design 문서: `wt/plan-v6384/docs/02-design/features/`.
* 수집 방법: 다섯 문서에서 `백로그|나중|후속|반영 대기|미룸|열림|승인 대기` grep, 열린 결정 절(oracle N7·graph N10·headroom N10/N3.7·offset-strategy N10/N6·offset-trim N7) 전수 읽기, 담당 card id가 card 표에 없는 행 대조(상위 N6.1 card 순서표).
* **제외**: (1) '기록용·이미 승인됨' 절의 닫힌 행(oracle N7.1 D-1~D-9, N7.4·N7.4a·N7.4b·N7.4c, N7.3 X-항목 중 승인·해소된 것, headroom N10.1·N10.2, offset-strategy N10.2·N11, offset-trim N7.2·N7.4 O-항목) (2) 이번 v6.38.4 판의 '상위 승인 대기' 표지(P1·P4·P7·P9-HC) -- 현재 판의 승인 절차 몫이지 백로그가 아님.
* 판정 기호: **삭제(a)** 이미 닫힘 / **삭제(b)** 재작성으로 대상 소멸 / **삭제(c)** 원칙상 불필요 / **삭제(d)** 물리상 틀린 전제 / **필요** 기존 card 배정·확장 / **질문** 사용자 몫 / **불확실** 확인 못함.
* 원칙 점검 약호: G = graph 단일 정본, C = 상수 발명 금지, N = 회로 이름 조건 금지, P = O-171 물리·회로이론 검증, R = O-153/O-165/O-169(재작성·새 card 0·소비자 없는 선언 삭제). ✓ = 위반 없음, ⚠ = 주의.

---

## D1. oracle-portability (v0.6.22)

| ID | 문서·출처 줄 | 내용 | 판정 | 근거 | 처리(문언 초안 포함) | 원칙 점검 |
|---|---|---|---|---|---|---|
| OP-B1 | `oracle-portability.plan.md:626` X-D1, 상위 `gain-budget…plan.md:2384` E-20 | 출처 미확인 반복 상한 다섯: `O/oracle_simulate.py:750` `NYQUIST_K_MAX = 10`, `O/oracle_noise.py:44-45` `NOISE_TOP_K_MAX = 8`·`INTEGRAL_K_MAX = 4`, `O/oracle_swing.py:43-44` `ZOOM_POINTS = 7`·`ZOOM_ROUNDS = 8`. 상위 E-20 소유 = "oracle-portability(X-D1 -- 그 계획 다음 판 card)" → **담당 card 없음** | **필요** | 상수 발명 금지(E-20 대체 규칙 '출처 유도 또는 선언'). 다섯 모두 상한에 닿으면 이미 fail-closed(N 미정·`converged = False`·`sweep_end_unresolved`)라 fail-open은 아니고, 남는 결함은 '근거 없는 숫자'뿐 | **기존 card 확장, 새 card 0**: `NYQUIST_K_MAX` → OP-4(C10·Nyquist를 코어로 옮기는 card), 나머지 넷 → OP-5(noise·swing을 코어로 옮기는 card). OP-4 범위 문언 초안: "Nyquist 세분 종료 = 각 구간 편각 < π/2, 또는 구간 폭이 입력 `Resolution`이 정하는 주파수 분해능 이하; 그래도 못 맞추면 N 미정(사유 그대로). 고정 라운드 상한 삭제". OP-5 범위 문언 초안: "끝 좁히기 라운드 상한 = ⌈log_(P+1)(첫 괄호 폭 / r)⌉(r = design §18.3 전압 분해능, P = 라운드당 점 수); noise 상한 확장은 꼬리 상계 ≤ 적분 상대 분해능이 되는 f_hi를 상계 식에서 직접 정하고, 격자 밀도 반복은 연속 두 적분 차 ≤ 분해능까지(상한은 분해능에서 유도). 식 확정은 design(OP-0 개정)". P(라운드당 점 수)는 비용 선택이라 어댑터 능력 선언 칸에서 읽는다(상수 아님). **완료 측정**: 다섯 이름 `git grep` 0; 상한 도달 toy마다 fail-closed 사유; N4 비교 -- 상한에 닿지 않은 기준선 입력은 비트 동일, 닿은 입력은 '정의를 바꾼 칸'(O-34 (1)) 변화표. 상위 E-20 소유 칸 문언을 "OP-4(Nyquist)·OP-5(나머지 넷)"로 고친다. **순서 충돌**: 없음(두 card 안) | G ✓(oracle은 엔진을 import하지 않음 -- 엔진 `k_max`와 같은 꼴의 식을 인용으로만 맞춤, 사본 코드 아님) C ✓(목표) N ✓ P ✓(괄호 축소 라운드 수는 분해능에서 수학적으로 정해짐) R ✓(새 card 0) |
| OP-B2 | `oracle-portability.plan.md:626` X-D1 첫 괄호, 상위 `:2385` E-21 끝 | oracle 판정 쪽 대체값 `O/oracle_swing.py:15` '`judge.off_current_A` 없으면 문턱 0' | **삭제(a)** | 이미 OP-5 범위: `oracle-portability.plan.md:646` X-31 "(v0.6.10 정정, O-50 O2) **OP-5에서 `judge.off_current_A`를 지운다**(design v0.3.0 B-34)" -- 칸 자체가 사라지므로 대체값도 사라짐 | 상위 E-21 소유 칸의 이 몫을 "oracle-portability OP-5(X-31 -- 칸 삭제, 이미 범위)"로 고치고 X-D1 괄호 문장에서 뺀다 | G ✓ C ✓ R ✓(지울 코드라 고치지 않음) |
| OP-B3 | 상위 `:2385` E-21 '게이트 전용 이상 전압 넷 조건 미검사'; design `oracle-portability.design.md:1655` 백로그 '`/bias_voltages` 게이트 전용 조건을 입력 계약 전체로 넓힐지 = OP-3에서 정함' | `O/oracle_netlist.py:466-478`: 구동 소자 없는 게이트 전용 넷은 `bias_voltages` 선언값, **없으면 예측 노드전압의 이상 전압원으로 대체하고 경고만** 남김 | **필요** | fail-closed: 선언 없는 바이어스를 예측값으로 메우는 것은 '정의 불능을 숫자로 메움'(상위 N6.35 머리 원칙). 담당 = '그 계획 다음 판'이라 card 없음 | **OP-3 범위 확장**(입력 계약 card). 문언 초안: "입력 계약 교차 규칙(design §11.2 1d): 회로 IR의 구동 소자 없는 게이트 전용 넷 집합 = `bias_voltages` 선언 넷 집합. 다르거나 선언이 없으면 거부(사유 이름 design, `oracle_input_*` 계열) -- 예측 노드전압 대체와 경고 경로를 지운다. §21.2 2단계 (0)의 `bias_not_gate_only`는 이 검사를 인용". **완료 측정**: 선언 빠진 게이트 넷 toy → 거부(base 예측값 대체 -- red), `oracle_netlist` 대체 갈래 grep 0. EO-1 완료 조건에 "생산자가 게이트 전용 넷마다 `bias_voltages`를 낸다" 한 줄. **순서**: OP-3 → EO-1(기존 그대로) | G ✓ C ✓ N ✓ P ✓(바이어스 넷 전위는 선언·풀이 값이어야 함) R ✓ |
| OP-B4 | `:605` G-19, `:683` OQ-7, `:512` OP-10, `:433` N3.9, `:782` N9 -- '(→ 반영 대기: 상위 후속 정정 표 oracle-portability(v6.37 O-119) 행 … OP-5 병합 뒤 OP-10 착수 전 반영, 지금 규칙으로 읽지 않음)' | 슬루 계단 = 'ICMR 끝' 옛 문언을 '지금 규칙으로 읽지 않음' 표지로 남겨 둠. 지금 규칙은 N3.9 슬루 행(`:453`, follower 사용 범위·같은 덱 `.dc`) | **필요** | 계획서는 design용(이력은 history). O-119는 승인됨 -- 옛 문언을 OP-5 병합까지 남겨 둘 물리 이유 없음(절차 세부만 OP-5 `.dc` 훑기 구현을 인용) | **이번 판에서 계획 문언 정리**: 다섯 자리의 'ICMR 끝' 계단·확정 범위 지목 왕복 문언을 history로 옮기고 "N3.9 슬루 행 인용" 한 줄만 둔다. **design 몫 = 새 DR-27**(OP-0 design 개정, OP-10 착수 전): 같은 덱 `.dc` follower 사용 범위(`follower_input_range_v`) → 판정 계단, 2단계 왕복 삭제, 두 계단폭 보고(상위 `:1873` (1)~(5)). **완료 측정**: 계획 grep 'ICMR 창 끝' 0(history 제외), DR-27 반영 design plan_version 일치 | G ✓ C ✓ R ✓ |
| OP-B5 | 상위 `:1872` 후속 정정 (3), 상위 `:2561` U-107 | 계통 offset '기준 도달 불가' 정의 불능(V_ref가 출력 스윙 창 밖)을 oracle 쪽 같은 정의로 맞추고 V_ref와 ICMR servo 기준의 축 차이를 적으라는 상위 요구가 **oracle 계획에 없음**(`oracle-portability.plan.md` grep 'U-107'·'기준 도달' 0건; N3.9 `offset_sys_mv` 행 `:452`) | **필요** | 엔진·oracle 정의 하나(같은 양 다른 정의면 '정의 경계 불일치'); 근거 사례 nmcnr @V_ref = 0.9 V -- SPICE servo 해 없음, 1차 −33.6 mV 거짓 값(상위 U-107) | **OP-5 범위 + N3.9 `offset_sys_mv` 행 문언**: "출력을 V_ref에 고정하는 `.dc` 풀이에서 V_ref가 같은 측정 구성의 출력 범위(N3.9 '출력 범위 판정' 행의 `.dc` 출력 훑기) 밖이면 정의 불능, 사유 = 기준 도달 불가(엔진 U-107과 같은 정의, `.dc` 수렴 실패와 다른 사유 -- 이름 design); 결과에 offset 기준 V_ref와 ICMR servo 기준(봉인점 예측)의 차를 기록". design 몫 = 새 DR-28. **완료 측정**: 출력 범위 밖 V_ref 손 회로 toy → 기준 도달 불가(base 수렴 실패 또는 값 -- red), 엔진 U-107 toy와 같은 판정 | G ✓(정의 = 상위 U-107 인용) C ✓(새 문턱 0) N ✓(toy는 손 회로) P ✓(상위 U-107 근거 실측 인용) R ✓ |
| OP-B6 | `:730` DR-26; design 머리 `oracle-portability.design.md` `version: 0.3.10`, `plan_version: 0.6.17`, Status '독립 검증 대기·사용자 승인 전' | ICMR servo(상위 O-115·O-116) design 몫 미반영. **OP-0 design 자체가 아직 승인 전**이라 OP-2·OP-3 → EO-1 → 모든 동작 변경 card의 SPICE 다리가 이 design 승인에 걸려 있다(`wt/integ-it12`에 `O/core/` 없음 -- OP-2·OP-3 미구현) | **필요** | 만들면 배선·fail-closed 판정 다리의 출발 gate. 백로그가 아니라 **가장 앞선 막힘** | 기존 card **OP-0(design 개정)**: DR-26~DR-28(OP-B4·OP-B5) 반영, plan_version 0.6.22, 독립 검증 → 사용자 승인. **완료 측정**: design↔계획 gap 0(DR 표 전 행), 승인 기록 | G ✓ R ✓ |
| OP-B7 | `:582-605` N7.2 G-1~G-14·G-17·G-18 | 'design에서 닫을 항목' | **삭제(a)** | design v0.3.10이 각 절에서 닫음(G-1·G-2 §5·§6, G-3 §8, G-4 §7, G-5 §10, G-6 §18.3, G-7 §9, G-9 §10, G-10 §15, G-12 §5, G-13 §8.4(design 1419행 'G-13 결정'), G-14 §16, G-17 §12.5, G-18 §11.6). G-18의 O-115 영향은 OP-B6 몫 | N7.2 표제에 "design v0.3.10에서 닫힘(승인 전 초안), 남은 것 = DR-26~DR-28"만 적고 행은 history로 | G ✓ |
| OP-B8 | `:596` G-11 '대안(존재 판정용 최소 수)… 기준값을 새 상수 없이 어디서 가져올지 정해지면 대안을 채택' | PC 벤치 표본 수의 열린 대안 | **삭제(c)** | 대안은 기준 확률(새 상수)을 요구 -- design `:1113` "기준 확률의 출처를 새 상수 없이 정하지 못해 이 문서도 대안을 고르지 않는다". 기본안 `sample_count(r)` 재사용(design `:1111`)이 이미 있음 | G-11 '대안' 문장 삭제, "기본안 확정: `sample_count(r)`(r 출처 design §12)"로 | C ✓(발명 상수 차단) |
| OP-B9 | `:600` G-16 (가), `:630` X-15 '두 번째 PDK가 생길 때 엔진 card' | 엔진 σ 기하 환산의 공정 전제: (a) 면적 지수 −1/2 (b) bin 사이 slope 비 환산(상대형 변수 p0가 bin마다 다르면 틀릴 수 있음 -- "sky130 toxe p0의 bin별 차이는 확인하지 않음") (c) `<이름>_slope / sqrt` 파서 | **불확실**(부분 삭제 + 측정 필요) | (a)는 Pelgrom 면적 법칙(σ ∝ 1/√(WL), Pelgrom·Duinmaijer·Welbers, IEEE JSSC 24(5), 1989)이라 공정 일반 -- '공정 전제' 아님(삭제(d)). (c)는 PDK 선언 로더 자리라 원칙 위반 아님. **(b)는 지금 PDK에서도 미확인 물리 전제**이고, 상위 WB-1 범위 2가 "mismatch는 기준 폭 표 키 + 기준 폭 환산 유지"로 같은 전제를 다시 쓴다 | (b)만 남김: **상위 WB-1 착수 실측 항목에 추가** -- "sky130 nfet·pfet mismatch 대상 변수 가운데 상대형(Δp = p0·slope/√…) 변수의 bin별 p0 표(모델 카드 원문 파일:줄); bin마다 다르면 slope 비 환산이 틀리므로 계획부터(DEC-96 (2)) 고친다". (a)(c)와 '두 번째 PDK 때 엔진 card' 문장은 지운다. 원문 확인 필요(이 감사에서 PDK 모델 카드를 읽지 않음) | P ⚠(미측정 -- 측정 뒤 권고) G ✓ C ✓ |
| OP-B10 | `:611` X-1 | 두 번째 실제 시뮬레이터 부재로 '시뮬레이터 무관' 실측 한계 | **삭제(c)** | 보고 문구(한계 기록)이지 할 일이 아님. 엔진을 막지 않음('인프라는 엔진을 막을 때만') | N7.3에서 '보고 문구'로만 두고 백로그 성격 문장 없음을 확인(지금도 할 일 문장 없음 -- 그대로) | R ✓ |
| OP-B11 | `:625` X-13 끝 '**알림**: 관련 계획(XRUN-F1, offset-strategy, offset-trim)에 … 넣도록 알린다' | 엔진 PDK 선언을 바꾸면 기술자 참조도 같은 변경에서 갱신 -- 알림 항목 | **삭제(a)** | 같은 X-13이 OP-2에 '엔진 suite에서도 도는 test(엔진 선언 정규화 sha256 ≠ 기술자 참조면 실패)'를 둠 -- 기계적 강제가 알림을 대신함(offset-strategy·offset-trim·gain-budget에 그 문장 grep 0이어도 무방) | '알림' 문장을 "X-13 test가 강제(OP-2)"로 바꾼다 | G ✓ R ✓ |
| OP-B12 | `:576` D-5, `:615` X-5, `:774` N9 'U16이 `ng-bridge`를 흡수할 때 새 형식으로 낸다' | 엔진 → oracle 입력 생산자 = U16 | **삭제(b)** | 생산자는 상위 card **EO-1**(`gain-budget…plan.md:2092`, O-44 (1)) -- 이 계획 G-18 '생산자 계약'(`:604`)도 EO-1. `ng-bridge`·`legacy_adapter`는 LT-1 삭제 대상. U16은 상위 card 표에 없음 | 세 자리 'U16'·'ng-bridge 흡수' 문언을 "EO-1 생산자"로 고친다(문언만) | G ✓(생산자 하나) R ✓ |
| OP-B13 | `:319-333` N3.5.1 '그 계획이 확정되면 이 표를 그 커밋으로 다시 대조한다'(기준 offset-trim v0.5.2 미승인 판); offset-trim `:734` 후속 4 | offset-trim N3.9-3 요구 대조표 재대조 | **필요**(작음) | offset-trim은 v0.6.2로 바뀜(O-53 B3: 6번 'V_sys(T)' → 부호 있는 V_id*(T), PC-10 = OP-5 `.dc` 온도 조건) | 기존 card **OP-0(design 개정)** 때 offset-trim v0.6.2 N3.9-3과 재대조, 6번 표기 V_id*(T)로. **완료 측정**: 대조표 기준 커밋 = offset-trim 승인 커밋, 일곱 행 '담김' 재확인 | G ✓ |
| OP-B14 | `:776`·`:777` N9 (v0.6.7 '확인 필요'·'관찰') | 기존 LUT 폭 슬라이스 32개 `generator_sha256` `8df35d2e…`가 이력에서 안 찾아짐 → 역할 옆 선언 근거 (a) 불가 → **OP-3 병합 조건 (c)가 막힐 수 있음**; `model_files_sha256` 중첩 dict 모양 | **불확실** | OP-3이 막히면 EO-1 → 모든 SPICE 다리가 막힌다(엔진을 막는 항목). 게다가 상위 WB-1이 바로 그 W 슬라이스를 판정 슬라이스로 쓰고, v6.38.4 P8 (E)는 bin 양 끝 슬라이스를 새로 만든다(LUT 생성 약 2배) | **지금 읽기 전용 검증자 측정으로 앞당김**(OP-1b 확장, 엔진 무변경): 다른 이력 출처 탐색 결과·중첩 dict 실측. 못 찾으면 대안 비교를 사용자에게: (가) 그 32 슬라이스는 P8 (E) 재생성(OP-8 새 생성기 meta가 역할을 씀) 뒤에만 판정에 씀 (나) 옆 선언 근거 (b)(include 그래프 밖 측정)만으로 역할 선언. 권고는 측정 뒤 | P ⚠(미측정) G ✓ |
| OP-B15 | `:364`·`:365`·`:367`·`:397` N3.7 '둠(D-2 승인됨(O-1): OP-8 뒤 고침)' | 상위 DEC-87·DEC-96·tol_V·U3의 'ngspice로 직접' 문언 정정 | **필요**(이미 배정) | OP-8(새 생성기) 병합 때 문언이 사실이 됨 | 기존 card **OP-8** 완료 조건에 "N3.7 'OP-8 뒤 고침' 네 행 상위 문언 정정"을 명시(지금 행 표지만 있음) | G ✓ |

**참고 -- design 쪽 백로그 메모(계획 밖, 판정만)**: (i) design `:1653` bulk(gmb) 엣지를 DC 되먹임 판정 그래프에 넣을지 -- body가 신호 넷에 묶이면 VSB가 ID를 바꾸는 DC 제어 경로라 물리상 엣지(P-1 일반형); 정의 자리는 상위 N3.8 'DC 되먹임 판정'이므로 상위 계획 몫, library에서 body가 레일·자기 source 밖에 묶인 소자 수 실측 뒤(0이면 정의 문장만 고침) -- **불확실** (ii) design `:1884` r(m 좌표)과 포트 전압 단위의 vntol 항 차 -- ICMR이 V_cm 좌표(U-106)로 바뀌어 DR-26 개정에서 함께 재정리(OP-B6) (iii) `/bias_voltages` 게이트 전용 → OP-B3에 합침.

---

## D2. graph-consumption (v0.14.5)

| ID | 문서·출처 줄 | 내용 | 판정 | 근거 | 처리(문언 초안 포함) | 원칙 점검 |
|---|---|---|---|---|---|---|
| GC-B1 | `graph-consumption.plan.md:791` B-G1 | MNA 조건수 기록과 소비자·판정 기준 | **삭제(c)** | 소비자·선언 기준 없음(만들면 배선); 특이는 상위 E-17이 fail-closed; 해의 독립 확인은 oracle forced·free 대조(U-G10) | B-G1 행 삭제(history). 다시 여는 조건 한 줄: "oracle 대조 차가 조건수로만 설명될 때" | R ✓ |
| GC-B2 | `:792` B-G2 | R4 제약 그래프 관계 | **삭제(a)** | 행 자체가 'O-15 (C)·O-16 (3)으로 닫힘' | 행을 history로 | -- |
| GC-B3 | `:793` B-G3 | 비레일/레일 g = s 비대칭 | **삭제(a)** | 상위 E-19 → IT-1 v6.38.3 범위 재작성 범위 5(`gain-budget…plan.md:2383`) | 행을 history로 | -- |
| GC-B4 | `:794` B-G5, `:430` N3.6-2 | 출발 자리값의 '정해진 전류 기하평균' 항(`E/search/start_intervals.py:120-128` -- `max(scale, W_min·IDu/L)`, scale = 정해진 전류의 기하평균) | **필요** | (1) 유도·선언 없는 출발값(계획 스스로 '추정'), 상자 중심 자리값과 같은 결함 유형(상위 N6.35 머리 원칙·E-15 O-127 유형) (2) **근거 소멸(재작성)**: 코드 주석의 이유('눈금이 다른 가지를 섞으면 미러·적층 DC가 무너진다')는 GC-5가 자리값을 기저 자유 원소에만 두고 나머지를 기저 행(KCL)으로 계산하면 사라짐(N3.6-2 '근거(P-1, KCL)') | **기존 card GC-5 확장**(같은 함수 `_state`, 이미 자리 이동 범위). 문언 초안: "정해지지 않은 기저 자유 원소의 자리값 = W_min·IDu/L(선언 W_min·LUT) 하나; '정해진 전류 기하평균' 항과 그 계산을 지운다. `refs` 소비자(층 0 Chebyshev 중심·면적 추정)는 착수 때 재조사 -- 상위 P4로 층 0 상자 중심 출발이 지워지면 그 몫은 대상 소멸". **완료 측정**: `start_intervals.py` 기하평균 계산 grep 0, 9회로 칸 0·사다리·면적 추정 변화표(원인 = 이 행). **원래 취지와 다름**: GC-5 '식을 바꾸지 않는다(동작 보존)'(`:430`)를 바꿈 → 사용자 승인 필요 | G ✓ C ✓ N ✓ P ✓(KCL 기저가 눈금 혼합을 막음) R ✓ ⚠(동작 보존 문언 변경 = 승인) |
| GC-B5 | `:795` (기존) | `structure_rule_fp`를 판정 로직(AST)에만 묶기 (`wt/_drafts/engine/U17_FOLLOWUPS.md:58`) | **삭제(c)** | 인프라 개선, 엔진을 막지 않음; U-G11 (가)(card마다 rule_hash 재기록)가 대신함(`:762`) | 행 삭제 | R ✓ |
| GC-B6 | `:143` O-10 (4) '종속 전류 구간 결합 (a)~(c)는 백로그', `:455` N3.6-4, `:539` K-g | 종속 전류에 W_min·밀도 하한과 면적 상한 구간 결합, L 칸마다 상자∩원뿔 LP 공집합 판정(`U17_FOLLOWUPS.md:57` -- "실패 사례 0이라 백로그") | **삭제(c)** | 실패 사례 0; 공집합 상자는 GC-5 한 규칙(전류 충돌·출발 불능 기록)과 봉인이 fail-closed로 거름 -- 가지치기 최적화일 뿐 | 백로그 문언 삭제, 다시 여는 조건: "GC-5 착수 측정(N4-4)에서 빈 사다리·출발 불능의 원인이 이 공집합으로 관측될 때" | R ✓ P ✓ |
| GC-B7 | `:143` O-10 (4) 'DC 저항 θ 기저 방향 표현은 백로그(공동분석 필요)', `U17_FOLLOWUPS.md:57` | DC 저항이 θ 전류 기저일 때 ln 좌표라 한 방향 양수만 표현 -- 중간 rail(agnd) 부하처럼 동작점에 따라 전류 방향이 바뀌는 저항은 반대 방향을 표현 못함(관찰 대상 r2r RL, rfc RB, nmcnr RL, cnr x37/x40/x9, sf_pushpull R1a~c, current_reuse R1) | **질문**(규칙 승인) + 착수 실측 | 물리: 양 끝 전위가 동작점에 따라 대소가 바뀌는 저항의 전류 부호는 정해지지 않음 → ln θ는 해를 상자 밖에 둘 수 있음. 단 O-127·O-128(값 미선언 DC 경로 저항 = V_R 고리 종속, θ 아님, 상위 `:269`)로 대상이 줄었을 수 있음 -- 미측정 | **상위 card TB-1(θ 기저 S/B/F/X 분류 필드) 착수 실측 + design 문언**: "θ 전류 기저 원소 가운데 선언 방향이 없는 원소(저항·이상원)는 분류 필드에 '방향 확정 여부'를 싣고, 동작점 의존이면 (가) θ에서 빼 고리 종속(V_R)으로 (나) 부호 있는 좌표 -- 고르는 규칙은 사용자 승인". 착수 실측 = library 9 + heldout에서 θ 전류 기저 저항 수와 그중 양 끝이 레일이 아닌 넷 수. 0이면 규칙 문장만(만들 코드 0) | G ✓ C ✓ N ✓(규칙에 회로 이름 없음 -- 관찰 목록은 측정 대상) P ⚠(미측정) R ✓ |
| GC-B8 | `:306` (card = 'U17 ②'), `:308` (card = '상위 N6.1 단위 8') | `graph/stage_b: residual_probe`·`dof_numeric` 배선 대기, `graph/coupling: vars·column_block_map·bias_columns` 배선 대기 -- **card id가 card 표의 id가 아님**(이 계획 규칙 N3.1-6 (f) `:290` "card id는 … card 표에 있는 id여야 한다" 위반) | **필요** | 'U17 ②'·'단위 8'은 상위 N6.1 card 표에 행이 없음. 상위 N6.1 단위 8 행은 "기본 경로 = 층 0 손계산 최적 -- card LA-1", design 40 `:2122` "U15 재구현을 U17 ② 안에서", LA-1 변화표 "U17 ② 상태층 커밋"(LA-Q5) -- 실제 소유는 LA-1 | 두 행의 card 칸을 **LA-1**로 바꾸고, 상위 LA-1 완료 조건에 "graph-consumption 부채 목록 `residual_probe`·`dof_numeric`·`coupling` 항목 0(배선 또는 O-153 삭제 -- 소비자 없으면 지움)" 한 줄. **순서 충돌**: 없음(LA-1은 이미 층 0 소비자) | G ✓ R ✓(소비자 없으면 삭제) |
| GC-B9 | `:307` ly_rows, `:312` start 출력, `:313` dc_scc_log·dc_tie_breaks, `:314` ly_dispositions, `:335` R6 -- card = 'U16' | 출력 전용 선언·배선이 U16(제품 진입점 `run_gmid_design_pipeline` 결과 JSON)을 기다림 -- **U16은 상위 card 표에 없음**(담당 card 없음, 규칙 (f) 위반) | **불확실**(소유 card 없음) | U16을 기다리는 곳이 여러 계획에 흩어짐(이 다섯 행, offset-strategy W-1 'U16은 나중에 CLI를 `run_plan`에', oracle D-5). 새 card는 O-165 (a) '새 card 0' 원칙과 충돌 ⚠ | 단순한 쪽 비교: **(나) 권고** -- 행마다 지금 진입점(단계 A·B 보고, `find_front` 결과, OS-2 `run_plan` 결과)에 도달하는지 GC-0a 계수에서 재고, 도달하면 GC-7에서 출력 전용 선언, 도달하지 않고 소비자도 없으면 O-153으로 삭제; layout 두 행(`ly_rows`·`ly_dispositions`)과 R6(convergence layout 파생 판정)은 같은 `E/convergence/*`를 고치는 상위 **LI-1**로. (가) 상위 N6.1에 'U16 제품 진입점' card 신설 -- card 수 증가, 사용자 승인 필요. 결정 = 오케스트레이터(원칙 (나)), 실측 뒤 | G ✓ R ⚠((가)이면 새 card) |
| GC-B10 | `:12`·`:72`·`:91`·`:120` FR-G18·`:217`·`:761` U-G10 'oracle 입력 배선은 U16' | 독립 KCL·KVL 확인 = oracle forced·free 대조, 배선 = U16 | **삭제(b)** + 문언 | 생산자·판정 배선은 상위 card **EO-1**(O-44 (1), `gain-budget…plan.md:2092`) | 여섯 자리 'U16' → 'EO-1'. 상위 EO-1 완료 조건에 "판정 결과에 free 노드전압 대조와 forced 넷별 KCL 잔차(진단)가 점 레코드로 붙음" 확인 한 줄(지금 EO-1 범위 (2) '판정 배선'의 세부) | G ✓ R ✓ |
| GC-B11 | `:525` P-G2 | 트리 경로 재구성 0 확인을 HC-1 완료 조건에도 둘지(권고만) | **삭제(a)** | headroom-chain HC-1 완료 조건에 WP-10 계측(`headroom-chain.plan.md:141`·`:572`)과 상위 N6.3 '같은 입력 재계산 0 일반 검사'(v6.38.4)가 이미 있음 | 행 닫음 | G ✓ |
| GC-B12 | `:770-786` N10.3 GD-1~GD-14 | design에서 닫을 항목 -- **graph-consumption design 문서가 아직 없음**(`docs/02-design/features/` 목록) | **필요**(이미 배정) | 기존 card GC-D·GC-1·GC-2·GC-5·GC-7·GC-9에 배정됨 | 변경 없음. 보고 몫: design 미작성 상태 | -- |

---

## D3. headroom-chain (v0.7.9.5)

| ID | 문서·출처 줄 | 내용 | 판정 | 근거 | 처리(문언 초안 포함) | 원칙 점검 |
|---|---|---|---|---|---|---|
| HC-B1 | `headroom-chain.plan.md:383` SD-1, `:197` F-11; 엔진 `E/sizing/block_columns.py:404-405`(빈 창 → `(lo + hi)/2`), `:426-427`(근 없음 → \|h\| 작은 끝점) | GS 비엄격 바퀴의 1변수 노드 풀이가 빈 창이면 가운데 값, 근 없음이면 끝점을 씀 -- 앞의 값은 VS 축 밖일 수 있음. 처리 = '백로그 + 재계수, 0이 아니면 별도 card(HC-F, 사용자 승인)' | **필요** | (1) **같은 상황 두 처리**: 같은 파일 W4 `update` 비엄격은 빈 창에서 "현재 값을 그대로 둔다"(`:464-465`, docstring `:441-444`) (2) 가운데 값은 상자 중심 대체와 같은 꼴(상위 N6.35 머리 원칙) (3) 상위 WB-1 범위 3이 바로 이 DC 블록(노드 풀이)을 재작성(O-165 (a)) | **상위 WB-1 범위 3 확장**(새 card 0, HC-F 삭제). 문언 초안: "GS 비엄격 바퀴의 빈 창·근 없음 처리 = 한 규칙(현재 반복값 유지 -- `update` 비엄격과 같음; 다른 투영을 쓰려면 design이 물리로 정함), 가운데 값·작은 \|h\| 끝점 대체 삭제; strict 검증 바퀴 그대로". **완료 측정**: 대체 갈래 grep 0, 9회로 SD-1 발생 수(HC-0 M-H5 기준)·수렴 실패 수 변화표. headroom-chain 쪽: `:519` HC-F 행 삭제, `:518` HC-V의 'SD 재계수' 삭제, `:632` H-10 갱신. **순서**: WB-1은 LA-0 앞 -- HC-0 M-H5는 기록이라 충돌 없음 | G ✓ C ✓ N ✓ P ✓ R ✓(재작성 card에 흡수) |
| HC-B2 | `:384` SD-2 | 봉인이 음수 VDS로 tol을 조회(현재 `E/sizing/seal_saturation.py:41-44` → `E/lut/vdsat_tolerance.py:58-66` 'VDS 축 → `SealViolationError`' -- fail-closed이나 사유가 LUT 축 밖) | **필요** | 결정 6(d/s 방향 고정, `c8d156e3`) 아래 선언 방향 VDS < 0은 물리상 '포화 아님(역방향)' -- 사유가 LUT 축 오류면 원인 귀속이 틀림(변화표 원인 미설명 위험). fail-open은 아님 | **HC-S 확장**(`sat_threshold` 정의 함수 -- 상위 N6.1 '조건부 제작 함수' 꼴로 HC-S·WB-1 중 먼저 병합되는 card가 만듦). 문언 초안: "`sat_threshold` 정의역: 선언 방향 VDS < 0이면 LUT 조회 없이 '포화 아님(역방향 VDS)' 판정과 사유(이름 design)". **완료 측정**: VDS < 0 toy → 그 사유(base LUT 축 오류 -- red). **순서**: 기존 HC-S 그대로 | G ✓(정의 함수 하나) C ✓ P ✓ R ✓ |
| HC-B3 | `:385` SD-3 | ln IDu 상자 하한 < 그 VDS의 LUT 분지 하한(기록만) | **삭제(c)** | 상자 하한 규칙 정의에서 나온 관측이고 결함 아님(그 점은 봉인이 거름). 빈도는 HC-0 M-H5가 이미 셈 | 백로그 표지 삭제, M-H5 계수 항목으로만 | R ✓ |
| HC-B4 | `:632` H-10, `:519` HC-F, `:613` | 'SD-1·SD-2 백로그 + 재계수', 조건부 card HC-F | **삭제(b)** | HC-B1·HC-B2로 기존 card에 흡수 | 행·card 삭제 | R ✓ |
| HC-B5 | `:659` U-H14 | 파일럿 current_reuse M63/M58 triode 허용 선언(spec `intended_region` = `{"pending": "CI-18"}`, `assets/library/current_reuse_telescopic_ota.sizing_spec.json:322-324` 지금도 그대로) | **질문**(spec·회로 해석) | 사용자 몫. 선언 없으면 파일럿은 봉인에서 '포화 불가, triode 선언 필요'로 계속 거부(`:615` -- 의도된 fail-closed) | 질문 시점 = HC-0 M-H1c(원문 동작점 LUT 영역) 측정 뒤. 근거 원문: Xie·Chen 2019 `assets/library/sources/…/current_reuse_telescopic_ota__xie_chen_2019/source.pdf` 부록 Fig.6 p.6·Fig.8 p.8(`:595`). 질문 문안: "M63·M58을 triode 허용으로 선언할지(근거 M-H1c 영역 표)" | N ✓(회로 이름은 spec 자리) |
| HC-B6 | `:38`·`:598` R5 '백로그 `U17_FOLLOWUPS.md` 45-55행' | current_reuse 층 0 40점 전부 봉인 7 실패 조사 | **삭제(a)** | 이 계획 자체의 목적(N1.1 `:94`)과 HC-1이 다룸 | 출처 인용으로만 남김 | -- |
| HC-B7 | `:340` | 'VGS 소속 기준 as-built 보존·공동분석 백로그' | **삭제(a)** | 행이 "이 삭제로 닫혔다"고 적음(DE-1 `ls_swing` 삭제, 상위 후속 정정 `:1857`) | -- | -- |
| HC-B8 | `:664-679` N10.3 G-1~G-13 | design에서 닫을 항목 -- **headroom-chain design 문서가 아직 없음** | **필요**(이미 배정) | 기존 card HC-D·HC-1·HC-O | 변경 없음. 보고 몫: design 미작성 | -- |
| HC-B9 | `:142`·`:655`(U-H10) | 오라클 소비자만 HC-O로 미룸 | **삭제(a)** | 결정됨(H-A), card HC-O(OP-3 뒤) | -- | -- |

---

## D4. offset-strategy (v0.7.5)

| ID | 문서·출처 줄 | 내용 | 판정 | 근거 | 처리(문언 초안 포함) | 원칙 점검 |
|---|---|---|---|---|---|---|
| OS-B1 | `offset-strategy.plan.md:589` DS-U9, `:96` | 시간 예산에서 E_B를 유도하는 실행의 다변형 규칙 -- '기본안 없음(열림)', 정해지기 전에는 그 실행을 완료 조건 2·NFR-S5에서 빼고 표기 | **질문**(정책) | 엔진에 유도 경로가 실제로 있음(`E/search/eval_budget.py:12`, `E/search/find_front.py:42-48` `eval_budget_source`). 벽시계 측정으로 유도하면 실행 순서·기계에 따라 E_B가 달라져 결정론(같은 입력 → 같은 결과)과 충돌. 정본 결정 = 상위 U-47 'front 시간 예산'(사용자 열린 결정, `gain-budget…plan.md:2501`) | 상위 N7.2 U-47 행에 하위 질문 한 줄: "E_B를 시간 예산에서 유도하는 실행의 다변형 규칙(offset-strategy DS-U9) -- 후보: 유도 실행을 결정성 요구 밖으로 표기 유지 / 유도 금지(E_B 선언만)". 그때까지 지금 문언(표기·제외)은 fail-closed 표기라 유지 | C ✓ P ✓ |
| OS-B2 | `:591` DS-U5 | 기존 library spec(`offset_in_sigma_mv`)을 요구 형식으로 옮길지와 값 | **질문**(spec 값) | 사용자 몫. 기본안 '옮기지 않음' | 질문 시점 = OS-2 착수 때(지금 급하지 않음) | N ✓ |
| OS-B3 | `:590` DS-U8 | trim 시험 회로 spec의 `offset_in_max_v` 값 | **질문**(spec 값) | 사용자 몫 | 질문 시점 = TR card(시험 회로 T-27·T-28) 착수 때 | N ✓ |
| OS-B4 | `:404-424` N6 M2, `:479` OS-M, `:478` OS-0 선행 'M2 결과', `:556`·`:558` N9, `:609` DO-8 | matching·trim 국면 1 θ 겹침 측정 card OS-M | **삭제(a)** | M2의 소비처는 DS-1·DS-2 결정(`:402`, `:582`) -- DS-1은 S-14 (다)로 결정, DS-2는 PD-3로 '대상 없음'. 메모리 위험은 N3.7 상한 식 fail-closed와 XS-19(OS-L 반복당 색인 크기 측정)가 맡음 → 소비자 없는 측정(만들면 배선) | N6 M2·OS-M 행·OS-0 선행의 'M2 결과'·N9 두 행의 M2 언급·DO-8을 history로. **완료 측정**: 계획 grep 'OS-M' 0 | R ✓ |
| OS-B5 | `:631` PS-6 | `open_run(s0_sets=B_S0)` 순환 | **필요**(이미 배정) | OS-5 `s0_sets` 구현 전, 40 §2.4.5 소유자 몫 -- 행이 이미 소유·시점을 적음 | 기존 card **OS-5** 착수 조건으로 유지(OS-0 design 개정에서 40 §2.4.5 '수명' (1) 문언안) | G ✓ |
| OS-B6 | `:632` PS-1 잔여 | DEC-74 front 판정 기록 이름 | **필요**(이미 배정) | 종류는 정해짐(gb v6.24 DEC-74), 이름 = 상위 card DE-1 design | 기존 card **DE-1** design 몫, OS-2 착수 조건 그대로 | G ✓ |
| OS-B7 | `:633` GB-N1 | 상위 'DE-1 후속 정정 표' offset-strategy 행에 커널 행 ① 정의 불능 처리를 더할지 | **삭제(a)** | 상위 `gain-budget…plan.md:1867`에 이미 "**커널 행 k·σ_in ≤ `offset_in_max_v`도 같음**(σ_in 정의 불능 → 그 행 fail-closed·원인 = 갈래 사유 …)" | 행 닫음 | -- |
| OS-B8 | `:634` PS-7, `:459` | 하네스가 평가 결과 전수(`seq` 순)를 읽는 S3 색인 평가 키 부분 열거 API -- 소유 'U17 ② design(40 §2.4.5)' -- **U17 ②는 card 표에 없음** | **필요** | W-1(하네스 사슬 대체, 만들면 배선)의 전제. 하네스 실측: `E/tests/integration/nfr4_run_dump.py:417` `sorted(sctx.cache.values(), key=lambda r: r.seq)` | **기존 card OS-2 확장**(소비자와 같은 변경): "S3 색인 평가 키 부분의 읽기 전용 열거(`seq` 순)를 세션 공개 API에 둔다(참조 읽기, 사본·결과 객체 칸 0 -- O-63 (3)); 40 §2.4.5 조회 API 개정안은 OS-0 design 개정". OS-2 착수 조건 'U17 ② design이 열거 API를 정한 뒤'(`:459`)는 삭제. **완료 측정**: 하네스가 그 API로 읽음, `sctx.cache` 직접 읽기 grep 0. **순서**: OS-2·LA-1 선후 고정 없음(기존 규칙 -- 같은 `E/search/*` 파일 겹침, 나중 card rebase) | G ✓(참조 읽기) R ✓ |
| OS-B9 | 상위 `gain-budget…plan.md` N6.1 offset-strategy 행 'OS-2 착수 선행 U17 ②(`graph/metrics: constraint_rows` 필드·writer)' | 선행 단위 U17 ②가 card가 아님(design 40 `:2093` ② 행: 제약 행 `graph/metrics: constraint_rows`, `residual_probe`·`dof_numeric` 배선 등) | **필요** | U17 ②의 실제 소유는 LA-1('U17 ② 상태층 커밋', U15 재구현 = LA-1) -- GC-B8과 같은 뿌리 | 상위 LA-1 범위에 "U17 ② 잔여(`constraint_rows` 필드·writer, `residual_probe`·`dof_numeric`·`coupling` 배선 또는 삭제)" 명시, N6.1 offset-strategy 행 선행을 'LA-1의 `constraint_rows` 커밋'으로 바꿈. **순서 충돌 확인**: 이러면 OS-2 → LA-1 의존이 생김 -- 지금 'OS-2·LA-1 선후 고정 없음'(N6.1)과 충돌 ⚠. 대안: `constraint_rows` 필드·writer를 **OS-2가 만든다**(첫 소비자 = OS-2 유도 제약 행, LA-1은 나중이면 읽음 -- 상위 '조건부 제작 함수' 꼴). 권고 = 대안(새 순서 규칙 0) | G ✓(writer 하나) R ✓ ⚠(순서) |
| OS-B10 | `:614-623` N10.3 G-S1~G-S6 | OS-0 design에서 닫을 기술 항목 | **필요**(이미 배정) | design v0.3.3(plan 0.7.3)이 §3에서 닫음. v0.7.4(상위 E-05 V_id* 세 성분 재작성)·v0.7.5(P1 S-10 검사 자리) 개정분은 design 미반영 | 기존 card **OS-0** design 개정(plan_version 0.7.5) | G ✓ |

---

## D5. offset-trim (v0.6.2)

| ID | 문서·출처 줄 | 내용 | 판정 | 근거 | 처리(문언 초안 포함) | 원칙 점검 |
|---|---|---|---|---|---|---|
| OT-B1 | `offset-trim.plan.md:611-625` N7.1 '사용자 결정 필요' D-1~D-17 | 열린 결정 표제 | **삭제(a)** | `:132` T-6 "계획 v0.4 승인", design `offset-trim.design.md:55` "T-6 \| 계획 v0.4 승인: **D-1~D-17 기본안 전부**"; D-16은 T-7로 변경(행 안 표기) | 표제를 "(전부 T-6으로 승인됨, D-16은 T-7 -- 기록용)"으로 | -- |
| OT-B2 | `:639-645` D-18~D-25 | v0.5 결정 항목 | **삭제(a)** | 행마다 '닫힘(T-34·T-35·T-36)' | 같은 표제 정리 | -- |
| OT-B3 | `:646-675` N7.3 G-1~G-15 | TR-0·TR-0T design에서 닫을 항목 | **필요**(기존 card) | design v0.3.3(`plan_version: 0.5.5`)이 G-1~G-15를 닫음(§3, §3.9, §20). 그러나 v0.6 개정분 -- G-12에 층 0 조립 블록(LA-1)·LR6 읽는 자리(`:668`), G-1·G-6·G-15 O-53 해소 문언 -- 은 design 미반영 | 기존 card **TR-0T(design 개정)**: plan_version 0.6.2, G-12 '문턱 의존 블록 목록'에 LA-1 역산 조립 블록 추가·LR6 인용. **완료 측정**: design↔계획 gap 0 | G ✓(LR6 정본 인용, 사본 금지) |
| OT-B4 | `:700` X-17 '상위 계획 DEC-96 (3) 문언 개정은 이 커밋에 없다(N7.4 후속)', `:734` 후속 1 | 상위 DEC-96 (3) '합격 = TT 27 °C 한 조건'에 T-29 예외가 없음 -- 상위 `gain-budget…plan.md:296` 확인(예외 문장 없음) | **필요** | 정본 문언 충돌: 상위 규칙이 승인된 하위 결정 T-29(offset·trim 잔여 합격 = 오라클 온도 범위 판정)를 부정 | card 불필요(문서). **이번 상위 판(v6.38.4)에서** DEC-96 (3) 끝에 한 문장: "예외: offset·trim 잔여의 합격 = SPICE 오라클 온도 범위 판정(offset-trim T-29·T-34; 엔진 탐색·판정은 한 조건 그대로)". **완료 측정**: 상위 DEC-96 grep 'T-29' ≥ 1, offset-trim X-17·N7.4 후속 1 닫음 | G ✓(정본 한 자리) |
| OT-B5 | `:734` 후속 2 | offset-strategy에 S-9 연결점·'실행 중 변형 추가' 인터페이스 | **삭제(a)** | offset-strategy N3.12·card OS-L(`offset-strategy.plan.md:482`) | 닫음 | -- |
| OT-B6 | `:734` 후속 3 | Δ_T 측정 기록 모양을 상위 DEC-72 기록 모양과 맞춤 | **필요**(작음, 기존 card) | design §20.2(G-9)가 Δ_T 기록 형식을 정함; DEC-72 기록 형식의 실제 writer는 상위 ME-1(아직 미구현) | 기존 card **TR-0T** design 개정 때 ME-1 design의 `model_error_<metric>` 기록 형식을 인용해 대조(같은 모양, 이름 DEC-68). **순서**: ME-1 design 뒤 인용 -- 새 순서 규칙 아님(TR-TL은 원래 ME-1보다 뒤) | G ✓(기록 형식 하나) |
| OT-B7 | `:734` 후속 4 | oracle N3.5.1이 N3.9-3 요구를 담는지 대조 | **삭제(중복)** | OP-B13과 같은 일 | OP-B13 하나로 | -- |
| OT-B8 | `:734` 후속 5 | `intended_region` `off` 칸을 gb·oracle·headroom이 같은 칸으로 받는지 대조 | **삭제(a)** | 상위 후속 정정 표 `:1864`·`:1866` 행이 같은 칸 `{triode, off}`로 정함 | 닫음 | -- |
| OT-B9 | `:527` 'N6.1에 이 계획 card 행 … gain-budget 쪽 개정 몫(N7.4 후속)' | 상위 card 표 인용 행 | **삭제(a)** | 상위 N6.1 'offset-trim TR-* 전부' 행(다른 계획 card 인용 규칙) | 닫음 | -- |
| OT-B10 | `:743-756` N7.5 design 후속 정정 8행 | 균형 풀이 삭제(O-53 A3)·`k_max` 문구·레지스트리 행·TR-5c test·E-4 영역 선언·`output_reference` DEC-23 인용·A_dm → A_dc·V_sys,s → V_id* | **필요**(기존 card) | design v0.3.3이 아직 옛 정의(엔진 안 DC 균형 풀이 등)를 담음 -- 구현 agent가 읽으면 승인 결정(O-53)과 다른 구현 위험 | 기존 card **TR-0T(design 개정)**: 8행 반영 + 함수 레지스트리 §2 '고정 기하 DC 균형 풀이' 행 삭제(같은 변경). **완료 측정**: design grep '균형 풀이'·'A_dm'·'V_sys,s'·`offset_systematic` 0(history 제외) | G ✓ C ✓ R ✓(옛 정의 삭제) |
| OT-B11 | `:141` T-32 'GBW·PM 등 코너 확장은 나중' | 범위 경계 | **삭제(c)** | 백로그가 아니라 사용자 범위 결정 기록 -- 수요가 생기면 계획 개정 | 할 일 문장 없음 확인(그대로) | -- |

---

## D6. 집계

| 문서 | 행 | 삭제 | 필요(기존 card 배정·확장·문언) | 질문(사용자 몫) | 불확실 |
|---|---|---|---|---|---|
| oracle-portability | 15 | 6 (B2·B7·B8·B10·B11·B12) | 7 (B1·B3·B4·B5·B6·B13·B15) | 0 | 2 (B9·B14) |
| graph-consumption | 12 | 7 (B1·B2·B3·B5·B6·B10·B11) | 3 (B4·B8·B12) | 1 (B7) | 1 (B9) |
| headroom-chain | 9 | 5 (B3·B4·B6·B7·B9) | 3 (B1·B2·B8) | 1 (B5) | 0 |
| offset-strategy | 10 | 2 (B4·B7) | 5 (B5·B6·B8·B9·B10) | 3 (B1·B2·B3) | 0 |
| offset-trim | 11 | 7 (B1·B2·B5·B7·B8·B9·B11) | 4 (B3·B4·B6·B10) | 0 | 0 |
| **합계** | **57** | **27** | **22** | **5** | **3** |

**새 card: 0.** 기존 card 확장(문언 초안 위 표): OP-3(B3), OP-4·OP-5(B1), OP-5(B5), OP-0 design 개정(B4 DR-27·B5 DR-28·B6 DR-26·B13), OP-8 완료 조건 명시(B15), 상위 WB-1 범위 3(HC-B1)·착수 실측(OP-B9), HC-S(HC-B2), GC-5(GC-B4 -- 원래 취지와 다름, 승인 필요), 상위 LA-1(GC-B8), OS-2(OS-B8·OS-B9 대안), TR-0T design 개정(OT-B3·B6·B10), 상위 TB-1 착수 실측(GC-B7). 문서만: 상위 DEC-96 (3)(OT-B4), 상위 E-20·E-21 소유 칸(OP-B1·B2), oracle 'U16' → EO-1(OP-B12), graph 'U16' → EO-1(GC-B10).

**담당 card 없던 열린 행(이번 감사에서 찾은 것)**: oracle X-D1(E-20·E-21 몫) → OP-3·OP-4·OP-5; graph 부채 행의 card id 'U17 ②'·'단위 8' → LA-1, 'U16' 다섯 행 → GC-B9(불확실); offset-strategy PS-7 'U17 ② design' → OS-2; offset-strategy OS-2 선행 'U17 ②'(`constraint_rows`) → OS-2 제작 권고. 공통 뿌리: **'U16'·'U17 ②'는 상위 card 표에 없는 design 단위 이름인데 다섯 하위 계획이 card처럼 기다린다** -- 상위 N6.1에 "U16·U17 ② 잔여의 소유 card" 정리 한 문단이 필요하다(오케스트레이터).

**순서 충돌**: OS-B9를 LA-1 소유로 하면 OS-2 → LA-1 의존이 생겨 기존 'OS-2·LA-1 선후 고정 없음'과 충돌 ⚠ -- 그래서 권고는 OS-2 제작(첫 소비자) 쪽. 나머지 배정은 기존 순서 그대로(새 순서 규칙 0).

**사용자 질문 후보(5 + 승인 2)**: HC-B5 U-H14(파일럿 triode 선언, HC-0 M-H1c 뒤), OS-B1 DS-U9(상위 U-47 하위 질문), OS-B2 DS-U5(OS-2 착수 때), OS-B3 DS-U8(TR 착수 때), GC-B7 저항 θ 방향 규칙(TB-1 착수 실측 뒤). 승인 필요: GC-B4(GC-5 '동작 보존' 문언 변경 -- 원래 취지와 다름), GC-B9 (가)를 고르면 새 card.

**가장 앞선 막힘(백로그 아님, 보고 몫)**: OP-0 design v0.3.10이 독립 검증·사용자 승인 전이고 OP-2·OP-3이 미구현이다(OP-B6) -- EO-1과 모든 동작 변경 card의 SPICE 다리가 여기 걸린다. OP-B14(폭 슬라이스 32개 생성기 판 미발견)는 OP-3 병합 조건을 막을 수 있어 지금 읽기 전용 측정으로 앞당길 것을 권고한다. graph-consumption·headroom-chain은 design 문서 자체가 아직 없다(GC-B12·HC-B8).

**불확실(확인 못한 것)**: OP-B9 sky130 상대형 mismatch 변수의 bin별 p0(PDK 모델 카드를 읽지 않음), OP-B14 생성기 판 출처, GC-B9 U16 행의 현재 진입점 도달 여부(GC-0a 계수 필요), GC-B7 θ 전류 기저 저항 발동 수, design 참고 (i) bulk 엣지 발동 수.


---

