# D0b spec card 2차 독립 검토 -- `20260930-p3-registry-dest` (v8.4/v8.5 정렬 판)

검토 2026-10-02, 독립 검토자(작성자 아님). 대상: `_drafts/draft_p3_d0b.spec.md`(현재판)·`d0b_briefs.md`, 비교 `*.pre-v84.md`·`*.pre-v85.md`.
루프 종료 조건(브리핑): 1차 검토 `review_d0b.md`의 B1·B2·S1·S3·S5가 풀렸는지 + v8.5 개정이 새 결함을 들였는지만 본다.

재측정: 격리 복제본 `C:/g198/r`(`git clone --no-local --no-hardlinks`, origin 제거, 빈 hooksPath, TMP/TEMP `C:/g198/tmp`), gate `master` = `dd60db6`.
복제본 가지: `fu`(design_report.py 28행·audit_current_forced.py 38행 앞 FU 한 줄) → `amd85fu`(p3_doc_amendments.md §1 (a)(가)~(d)·§9 (e)~(h) 8블록, '현재' 정확 일치 단언 뒤 교체),
`amd84fu`((h) 없음), `amd85nofu`(FU 없음), `regen85`(`amd85fu` + `p3kit_d0b/regen_registry.py --write` + `보류(Phase 3)`→`(Phase 4)` 9칸).
G1 시제품 `install_proto.py` 5790433c…·`g1_core.py` b3c4e391…(작업 트리). D0a 규칙은 **작성자 스크립트(mk85.py, 삭제됨)를 보지 않고** D0a 계약 2 v8.5 문언(docstring 제외, A-3/A-4 칸 선착석, 단조 올림,
A-2/A-4/A-5 승격 -- R(u) 최댓값은 N3.10 번호만 -- MOD7 상한, A-3 상한 없음, A-K, A-6, A-7 뒤 재고정점, `import_conflicts` (i)~(iv))만 보고 시제품 `move_plan_proto.py`(d2f3da97…) 위에 새로 짰다.
approved 해시 확인: `p3_doc_amendments.md` 363e3cc2da4fc96d…, design `draft_phase3_design_v8.md` a4350dc05ff86179… -- `user_decisions.md` UD-0 답의 해시와 같다.
작업 끝에 `/c/g198` 삭제, 실제 저장소 `HEAD`·`gate/master` `dd60db6`·`status --porcelain` md5·reflog 첫 줄 시작과 같음. 다른 `/c/g*` 무접촉.

## 판정: **조건부 통과 -- S 1건(R-B1 한 행) 고친 뒤 커밋, 재검토 루프 불요**(B 0 · S 1 · minor 4)

1차 B1·B2·S3·S5는 풀렸다. S1은 test 모양(계약 11 (a) 표)이 풀렸고 base red가 각 test 고유 단언에서 나오는 것을 재현했지만, 그 보완으로 둔 test별 거부 입력 중 **R-B1이 겨눈 test(T-B)를 FAIL시키지 않는다**(아래 S-1).
v8.5 개정((h) `_kv_table`, R-A6·R-E1 교체, D0b-6/7/8 닫힘, FU 의존 MOD 셋→둘)이 들인 결함은 없다(경미 문구 어긋남 1건, m1).

---

## 1. 재측정 결과

| 항목 | 재측정(독립 재구현) | spec 주장 | 판정 |
|---|---|---|---|
| `amd85fu` `plan` | exit 1 · `upward` 0 · `cycles` 0 · `unassigned` 0 · `conflicts` 0 · `import_time_high` 0 · `import_conflicts` 0 · MOD7 밖 0 · `reg_mismatch` **79** · 배정 **403**(A-4 229·A-5 64·A-1 60·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1), MOD별 8/18/82/102/21/11/110/32/17/ACF 2, docstring 제외 5 | 같음 | 재현 |
| `amd84fu` | `reg_mismatch` 78, A-4 230·A-1 59, `_kv_table` = `gmid_sizing_engine` A-4, `amd85fu`와 사상 차이는 `_kv_table` 하나 | 같음 | 재현 |
| FU 의존 | `amd85nofu`: `import_conflicts` **2** = `__future__` `topology_authoring`(ACF ∅ 대 SR·SD annotations)·`instance_report_builder`(ACF·DR ∅ 대 SD), 그 밖 배정 차이 0. (i)~(iii) 이름 출처 갈림은 FU 유무와 무관하게 0 | 2(MOD2·MOD9) | 재현 |
| 일곱 목록 빔(재생성 뒤) | `regen85` exit 0 · PASS · 일곱 목록 모두 [] · MOD7 밖 0 · `reg_mismatch` 0, `rule` A-4 239·A-5 60·A-1 60·A-2 39·A-6 3·A-K 2 | 같음 | 재현 |
| 재생성 멱등 | (키 → `mod`) 사상 차이 0 · 키 차이 0, 레지스트리 diff 409+/409−, 함수 표 15 · 대상 347(base 칸 = 줄기 128·다름 219) · 중첩 7 · 비대상 25, `보류(Phase 3)` 9→0 · `(Phase 4)` 14→23 | 같음 | 재현 |
| `reg_check` | `regen85`에서 `reg_check.py --registry … --root …` exit 0 `발견 0`; `test_reg_check.py`·`test_reg_check_df23.py`·`test_df23_inventory.py` **210 passed**(`-c tools/gates/pytest_gate.ini --gmid-phase=3 --gmid-strict=`) | 같음 | 재현 |
| (d)-1 표본 25(B26-1 뒤 둘 제외) | base·재생성 `plan` `mod` 25/25 = 기대, 행 있는 23 중 base 칸 = 기대 1(`run_topology_pipeline_with_finger_fixup`), 재생성 칸 23/23, × 두 행은 레지스트리 행 없음 확인 | 같음 | 재현 |
| interface card | gate `dd60db6` `interface_card.py <현재 초안> --root <git archive 사본>` → exit 0 **'기존 함수 0개'**, 두 표 빈 표 | 같음 | 재현 |
| `parse_spec_card` | `expect_id` 일치, exit 0, `phase` 3·`red-green`·`gate_change` no·`approval` [`20260930-30-module-split-design`], 절 11개, `activated_ic_case`·`noop_activation_id` [] | 같음 | 재현 |

### 1.1 손 재유도 5행(도구와 무관 -- 레지스트리 원문·N3.10(개정 뒤)·소스 AST에서)

| 단위 | 손적용 | 결과 = spec 표 |
|---|---|---|
| `_theta_evidence_for_pair`(ACF:56) | A-1 토큰 아님·레코드 아님 → 레지스트리 388행 칸 `〃` → 387행 `render_html_report` 칸 `` `instance_report_builder.render_design_r… `` → 식별자 중 N3.10 줄기 `instance_report_builder` 하나 = MOD9(A-4). R(u) = {`_as_set`(259행 칸 `topology_authoring.py` → MOD2)} → max(9, 2) = 9 | `instance_report_builder` ✓ |
| `save_html_report`(DR:313) | 258행 칸 `〃` → 사슬이 249행 `miller_ota_topology` 칸 `gmid_sizing_engine.py` = MOD4(A-4). 몸체는 `render_html_report`만 부름 = A-1 MOD9(N3.10 MOD9 `design_report.render_html_report`) → max(4, 9) = 9, MOD7 아님 | `instance_report_builder` ✓ |
| `NameCollisionVerdict`(SD:8478) | `@dataclass(frozen=True)` 레코드, 참조자는 `check_topology_name_uniqueness` 하나 → 그것은 행 없음, 참조자 `load_topology`(A-1 MOD3) → A-5 = 3. A-2 = min 참조자 = 3, R(u) 0 → 3 | `circuit_state_graph` ✓ |
| `solve_diode_stack_current`(SR:1499) | 칸 "삭제 후보" → MOD 토큰 0(A-4 아님), SR은 `--keep` 아님, 트리 안 참조자 0 → A-6 = R(u) 최댓값; R(u) ∋ `_invert_gm_id_for_current`(칸 `gmid_sizing_engine.py` MOD4) → 4 | `gmid_sizing_engine` ✓ |
| `_topology_ref_relpath`(SD:8956) | 레지스트리 행 없음, 참조자 `save_instance_json`(N3.10 MOD9 토큰 → A-1 9) 하나, R(u) 0 → A-5 = 9 | `instance_report_builder` ✓ |

### 1.2 base red / 병합본 green (계약 11 (a) 표대로 다섯 test를 단언 순서 그대로 모사)

* base(`amd85fu`): T-A → `reg_mismatch`(앞의 여섯 목록·MOD7 통과), T-B → 대상 행 칸(앞 단언 통과, 다름 219), T-C → `근거 규칙` 머리, T-D → `보류(Phase 3)` 9, T-E → 표본 22개. **다섯 모두 그 test 고유의 마지막 단언에서 FAIL** -- 1차 S1의 '머리 단언 하나에서만 red' 문제는 해소.
* 병합본(`regen85`): 다섯 모두 통과.

### 1.3 거부 입력(병합본 사본에 하나씩 커밋, 독립 재구현 `plan` + 다섯 test 모사)

| id | 겨눔 | 실측: 첫 FAIL 단언(test별) | 판정 |
|---|---|---|---|
| R-A1 | T-A `upward` | T-A `upward` 1(`save_html_report -> render_html_report`), `cycles` 0, `reg_mismatch` 1; T-B·T-E도 FAIL | ✓ |
| R-A2 | T-A `conflicts` | T-A `conflicts` 1; T-E도(`compute_metric` 미배정) | ✓ |
| R-A3 | T-A `unassigned` | T-A `unassigned` 1만 | ✓ |
| R-A4 | T-A `import_time_high` | T-A `import_time_high` 1만 | ✓ |
| R-A5 | T-A `import_conflicts` | T-A `import_conflicts` 1(MOD9 `__future__`)만 | ✓ |
| R-A6 | T-A MOD7 | T-A MOD7 밖 1(`_as_set` A-1 → `stick_diagram`), `conflicts` 0, `reg_mismatch` 1; T-B도 | ✓ |
| R-A7 | T-A·T-B·T-E 첫 줄 JSON | 셋 모두 JSON 단언 | ✓ |
| **R-B1** | **T-B 칸 = 줄기(+ T-A `reg_mismatch`)** | **`plan` exit 0, `reg_mismatch` 0, `quantize_L` `mod` = `gmid_lut.py`(A-4가 바뀐 칸을 따라감) → T-A·T-B 통과, T-E만 FAIL** | **✗ (S-1)** |
| R-B2 | T-B 정확 일치 | T-B 칸(`theta_search(S3)` ≠ `theta_search`); **T-E도 FAIL**(`quantize_L`이 표본) | ✓ (m2) |
| R-B3 | T-B `〃` 금지 | T-B 칸; T-E도 FAIL(표본) | ✓ |
| R-C1 | T-C 머리 | T-C 머리만 | ✓ |
| R-C2 | T-C 집합 | T-C 집합(`A-9`)만 | ✓ |
| R-D1 | T-D | T-D `보류(Phase 3)` 1만(`validate_theta_declaration_order` 행) | ✓ |
| R-E1 | T-E | `plan` exit 0·일곱 목록 []·`_theta_evidence_for_pair` `mod` = `theta_search.py`, T-A~T-D 통과, **T-E만 FAIL** | ✓ |

---

## 2. 1차 지적 해소 여부

| 1차 | 해소 | 근거 |
|---|---|---|
| B1 (d)-1 행 없는 두 행 | **해소** | oracle 120~121행: × 표본은 `plan` `mod`만 단언, 행을 더하지 않음. 표 × 행(`_topology_ref_relpath`·`check_topology_name_uniqueness`·B26-1 뒤 두 행)은 레지스트리 행 없음 확인 |
| B2 v8.4 정렬(`import_conflicts`·FU) | **해소** | 목록 일곱(의도·계약 3·T-A·(d)-2), base 사슬에 FU(16행), 계약 8 (d) FU 경로, `mod_imports` 판정 안 함(계약 3). FU 없이 `import_conflicts` 2 재현 → 이 단언이 FU 누락을 FAIL로 잡는다 |
| S1 red 모양 | **대부분 해소** | 표 1.2: base red가 test마다 고유 단언. 단 거부 입력 R-B1 오겨눔(S-1) |
| S3 규칙 ID 형식 | **해소** | 계약 6 (c): 'D0a 계약 2가 정의한 집합' 참조 + 현재 원소 9개(A-K·A-6·A-7 포함), R-C2 `A-9` = 집합 밖 |
| S5 표본 편중 | **해소** | 25행이 A-1·A-2·A-3·A-4(일반·별칭·`〃`·`〃`+승격)·A-5·A-K·A-6·A-7 모두 덮음, `〃` 번짐·토큰 우선(`_kv_table`)·A-2 우선(`NameCollisionVerdict`) 표본 포함. '원천도 대상도 아니다' 문장은 관찰상 `upward` 자체가 0이라 참 |

---

## 3. S(중요)

### S-1. R-B1은 T-B를 FAIL시키지 않는다 -- 겨눔이 틀렸다(1차 S1 (3) 보완의 결함)

재생성 뒤 대상 행 칸은 A-4 입력이다(계약 6 (c)·9가 스스로 적는다). `quantize_L`은 A-4(별칭 `optimizer`) 단위라 칸을 `gmid_lut`로 바꾸면 도구가 그 칸을 따라 MOD1로 배정한다(R(u) 0, 승격 없음) --
`reg_mismatch` 0, 칸 = 줄기라 **T-B 통과**, T-A 통과. 실제로 잡는 것은 T-E(표본)뿐이고, 이것은 R-E1과 같은 종류('도구와 열이 함께 틀림')다. spec '측정' 열이 '--'(재지 않음)이어서 v8.4·v8.5 두 판 모두 놓쳤다.
auditor가 V10 ⑥을 spec대로 재면 'R-B1 → T-B FAIL'이 성립하지 않아 판정이 막힌다.
**고칠 것**(한 행): 칸이 배정을 정하지 않는 단위로 바꾼다 -- 예 A-1 토큰 단위(표본이 아닌 것이 깔끔하다; 표본이면 T-E도 함께 FAIL)의 칸을 다른 MOD 줄기로: 도구는 토큰으로 원래 MOD를 유지 → `reg_mismatch` 1(T-A) + T-B 칸 불일치.
'측정' 열을 실측으로 채운다(이 검토 재현기로는 A-1 단위 칸 변경 시 T-A `reg_mismatch`·T-B 칸이 함께 FAIL함이 R-A1·R-A6의 `reg_mismatch` 1과 같은 기제). 이 수정은 기대값·기준을 바꾸지 않으므로 재검토 루프 불요.

---

## 4. minor

* m1(v8.5 개정과 design 문구). 계약 8 (e)는 "'M7을 실제 card로' 하는 길은 없다"고 닫았지만, **같은 승인 design §8 D0b 행(614행) 멈춤 경로는 "MOD7 밖 → N3.10 또는 M7 card"**를 그대로 적는다. spec 근거로 든 M7 행(616행 'M2·M3·M9에 흡수(빈 card 금지)')과 D0b 행이 design 안에서 서로 다르다. spec 쪽은 더 좁은(안전한) 읽기이므로 기능 문제는 없다 -- 계약 8 (e)에 "D0b 행의 'M7 card' 경로는 M7 행·UD-0 뒤 design 개정(D-11)이 있어야 열린다" 정도로 어긋남을 드러내거나 design 후속 정정 백로그로.
* m2. R-B2 '만드는 법' 열의 "T-B만 잡는다"는 사실과 다르다 -- `quantize_L`은 (d)-1 표본(행 ○)이라 T-E도 FAIL한다(R-B3도 같음). 겨눔(T-B 고유 단언 FAIL)은 성립하므로 문구만 "T-A는 못 잡는다(T-B·T-E가 잡는다)"로.
* m3. T-C의 '대상 행 `근거 규칙` 칸 ∈ 집합' 단언은 대상 행을 알아야 하므로 `plan` 출력이 필요하다(비대상 행 `-`는 집합 밖) -- 그런데 계약 11 (b)는 "T-A·T-B·T-E가 이 출력을 쓴다"고만 한다. T-C도 출력을 쓴다고 적을 것(R-A7에서 T-C의 행동도 정해진다).
* m4. 거부 입력 표 머리말 "'측정' 열은 … `plan` 시제품으로 판정 목록이 실제로 비지 않음을 확인한 것"은 '--' 행(R-B1·R-B3·R-C*·R-D1)이 재지 않았다는 뜻인데, 그중 R-B1은 `plan` 결과가 겨눔을 좌우한다(S-1). 칸·문자열만 보는 입력도 '다섯 test 모사로 첫 FAIL 단언 확인'을 측정 열에 남기면 V10 ⑥ 재현이 기계적이 된다.

---

## 5. 질문별 답

1. **일곱 목록 빔·멱등·`reg_check` 0**: 독립 재구현으로 모두 재현(1절). 규칙 분포·MOD별 수까지 spec·design 부록 A F5v85와 바이트 같은 값.
2. **25행 표본**: 도구 출력과 25/25 일치, 5행 손 재유도(1.1)도 일치.
3. **거부 입력 → 겨눈 test 고유 단언 FAIL**: 14개 중 13개 ✓, **R-B1 ✗**(S-1). red가 앞에 몰리지 않음(1.2 -- base에서 다섯 test 모두 마지막 고유 단언 FAIL).
4. **FU 의존**: FU 없이 `import_conflicts` 2(MOD2·MOD9 `__future__`) -- 재현. R-A5(DR FU 줄 삭제)는 `import_conflicts` 1(MOD9)로 T-A가 잡는다.
5. **interface card '기존 함수 0개'·`parse_spec_card` 통과**: 둘 다 확인.
6. **v8.5 개정이 들인 결함**: 없음(m1 문구 어긋남만). `_kv_table` A-1 표본, 새 R-A6(`_as_set` MOD7 토큰 → MOD7 단언에서 FAIL, `conflicts` 0), 새 R-E1(T-E만 FAIL) 모두 실측과 맞다.
