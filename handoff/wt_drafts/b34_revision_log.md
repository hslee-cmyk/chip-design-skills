# B34 spec card 개정 기록 -- v1 → v2

대상: `_drafts/draft_b34.spec.md`(id `20260930-b34-grammar-explicit`). v1 사본 `_drafts/draft_b34.v1.spec.md`. 입력 검토 `_drafts/review_b34.md`.
새 파일: `_drafts/draft_b34_approval_question.md`(앞당김 decision 승인 질문·기록 초안).
측정: gate `master` `7535799`, 저장소 쓰기·상태 변경 git 없음. scratch `C:/g54`(`git archive HEAD` 사본 `base`, 모의 `head`, 변이 실행용 사본 4개), 측정 뒤 삭제. `$PY` = `C:/Python314/python.exe -B`.
게이트 함수(`mutate_changed.changed_defs`·`mutants`·`_replace_def`·`inventory`, `reachability.build_graph`·`read_tree`·`iter_defs`·`_approved_ids`, `role_paths.parse_spec_card`, `merge_gate.parse_approval_header`)는 저장소 `tools/gates`에서 읽기 전용으로 import했다. `main`은 돌리지 않았다.

## 1. 검토 지적별 처리

| 지적 | 처리 |
|---|---|
| B1 approval 줄 | `approval: 20260930-b34-before-phase3`(decision 기록, 초안은 `draft_b34_approval_question.md`). design 20 승인은 "동작이 바뀌는 수정"을 덮지 않는다. U2와 같은 질문 회차, 기본안은 별도 기록(합치는 방법도 card 결정 1에 적음). `target` = `U3-B34-BEFORE-PHASE3, <등가 변이 id 1개>`. `merge_gate.parse_approval_header` 통과 |
| B2 `==` 판정 불가 | 계약 7(auditor)·8(test)에 정규화 규칙 명시: `Match`류 속성 `kind`·`devices`·`ports`·`note`·`priority` → 튜플, `set`/`frozenset` → 정렬 리스트, dict·list 재귀. 계약 8 oracle = 같은 test 안 부재 전 값. 계약 7은 정규화 또는 같은 `PYTHONHASHSEED`. 거부 입력 절에 비교 함수 자기 점검 추가 |
| B3 인벤토리 누락 | 계약 절 머리에 'test 모양' 규칙: 진입점은 test 함수 본문에서 `stick_diagram.<이름>(…)`으로 직접 호출. parametrize 이름 문자열·모듈 상수 + `getattr` 금지(회로 반복은 parametrize 가능) |
| S1 (a)안 비용·절차 | (a)안은 기각 대안으로만 남기고 비용 네 가지(기준 약화, base 전수 × 2, 대응 절차 없음, B26-1과 이중 변이)를 결정 2에 적음 |
| S2 누락 docstring | SR `resolve_stack_layout` 6509~6512, references 118~121·440~443을 docstring·문서 목록에 추가 |
| S3 사이트 14 줄 | `if` 4087, 본문 4088~4109, `else:` 4110, 4111로 정정(인계 표) |
| S4 계약 7 oracle | 복구 계약(v2 계약 8)은 test 판정, oracle (c) 같은 test 안 부재 전 값. base 대조(v2 계약 7)는 auditor 몫으로 분리 |
| S5 B26-1 순서 | v2는 B26-1과 겹치는 def 0개 → 이중 변이 없음. B26-1에 넣을 인계 한 줄을 결정 3에 적음 |
| M1 docs grep | P9 interface card 60행·P9 spec 58행 명시, 결정 4(P9 알림)로 처리 |
| M2 계약 4 표현 | v1 계약 4(`unavailable_reason` 삭제)는 해당 def가 card 밖으로 나가 삭제. 원칙의 계약화 문장 정정 |
| M3 `Transistor` 경로 | 계약 머리에 `stick_diagram.Transistor(name, kind, source=…, drain=…, gate=…)`와 모듈 경로 명시 |

## 2. 범위 변경(검토 권고안 1·2 채택)

* 코드 변경 def: v1 13개 → **v2 5개**(`_import_analog_grammar`, `find_idiom_matches`, `find_stack_edges`, `find_differential_and_mirror_forks`, `audit_theta_root_direction`).
* 인계: 사이트 9·10·10b·13·14 + `propose_device_roles_gap_fill` 3966~3970 `unavailable_reason` → B26-1. 사이트 5~8 → B35. 사이트 12 + `propose_theta_kcl_gap_fill` 3533~3535 → 백로그. 이 분기들은 B34 뒤 도달 불가(동작 영향 없음), docstring은 이 card에서 고친다.
* 계약 변경(v1 → v2 번호): 1·2·3 유지 / **4 신설**(탐색 경로 `sys.path` 맨 앞·멱등) / 5 = v1 5 + `forks(fx) is None` / **6 신설**(`audit_theta` 두 입력 → `[]`) / 7 = v1 6(정규화 추가) / 8 = v1 7(test oracle·정규화) / **9 신설**(forks는 같은 kind끼리만) / v1 4 삭제(인계).
* v1 (a)(기존 생존 면제)·(b)(세 def만) 대신: 기준 약화 없음. 기존 생존은 죽이는 계약(4·6·9)으로 처리하고, 진짜 등가 변이 1개만 decision 기록으로 면제.

## 3. 실측(모의 head)

모의 head = HEAD의 SD(git blob LF 원문)에 사이트 1(except → `raise ImportError(… _ag_path …) from e`)·2·3·4·11·11b만 적용. docstring은 해시 불변이라 적용하지 않았다(주석·docstring을 바꾼 사본에서도 `changed_defs`가 같은 5개임을 확인).

### 3.1 V3 규모

| def | 변이 head(base) | 인벤토리 기존 | + 본문 직접 호출 test | + parametrize/상수 test |
|---|---|---|---|---|
| `_import_analog_grammar` | 12 (12) | 159 | 160 | 159 |
| `find_idiom_matches` | 8 (11) | 15 | 16 | 15 |
| `find_stack_edges` | 6 (9) | 66 | 67 | 66 |
| `find_differential_and_mirror_forks` | 47 (50) | 10 | 11 | 10 |
| `audit_theta_root_direction` | 29 (36) | 4 | 5 | 4 |
| 합 | **102** (118) | | | |

HEAD 승인 기록 면제 id와 겹침 0.

### 3.2 계약(9회로 × 14 진입점 = 126; base `PYTHONHASHSEED=2`, head `=1`)

| 항목 | base | head |
|---|---|---|
| 둘 다 부재 → `ImportError` | 0/126(전부 반환, 다른 예외 0) | **126/126**, 메시지 `analog-grammar` 126, 경로 126, `__cause__` 126 |
| `idioms`만 부재 | 0/126 | 108/126(`find_stack_edges`·`geometry_colocation_union`은 idioms 미사용 -- 반환), `load_topology` 9/9 |
| `netclass`만 부재 | 0/126 | 126/126, `find_stack_edges` 9/9 |
| 복원 뒤 = 부재 전(정규화) | 378/378 | 378/378 |
| 계약 5·6 | 전부 참 | 전부 참 |
| 계약 4(경로 맨 앞·1개) | -- | 참. `insert` 상수 ±1 변이 2개는 거짓 |
| 계약 9 | `[(gnd_to_vdd, [], (Ml1, Ml2), mirror)]` | 같음 |
| 계약 7(base 대 head 정규화 digest) | 126/126 같음 | |
| raw `==`(같은 프로세스 두 번) | `find_idiom_matches` 9/9 다름 | 같음 → 정규화 필요 확인 |
| 부재 상태 `import stick_diagram` | -- | 성공, 이어 `load_topology` → `ImportError` |

### 3.3 변이 판정(102개, 변이마다 새 프로세스)

1. B34 계약 1~3·5·6·8만: 죽음 59, 나머지 43(`_import` 2, `find_stack_edges` 1, `forks` 25, `audit_theta` 15).
2. 나머지 43개를 인벤토리 기존 test로(도구와 같은 pytest 명령, 기준 실행 통과 확인 뒤): 죽음 38(`audit_theta` 15/15, `forks` 22/25, `find_stack_edges` 1/1), 생존 5.
3. 생존 5: `_import_analog_grammar` `const±:body[3].body[0].value.args[0]` 2개 → 계약 4로 죽음(실측). `forks` `stmt_delete:body[9].body[1].body[1].body[0].body[1]`·`….body[1].body[0]`(kind 검사) 2개 → 계약 9로 죽음(실측).
   `forks` `const-:body[8].body[2].value.generators[0].ifs[0].comparators[0]`(`len(members) >= 2` → `>= 1`) 1개 → **등가**(구성원 하나인 fork는 쌍이 없음, library 반환 동일).
4. 검토 표본의 base `audit_theta` 기존 생존 3개(3384 두 개, 3402)는 head에서 계약 6으로 죽음.

결론: 계약 4·6·9를 더하면 102개 중 101개가 죽고, 1개는 등가 변이 면제(승인 기록 target). 기준 약화 없음.

측정 주의: archive 사본에는 git 이력이 없어 `test_ts6_probe_relocate::test_base_blob_reader_reads_the_base_tree`가 기준 실행에서 실패했다(사본 결함 -- 도구는 이력 있는 복제본에서 돈다). `_import_analog_grammar`·`find_stack_edges` 인벤토리 판정은 그 test만 빼고(157·64개) 돌렸다.

### 3.4 머리 블록

`role_paths.parse_spec_card(text, "20260930-b34-grammar-explicit")` 통과: `phase 2`, `evidence_type red-green`, `gate_change no`, `approval ['20260930-b34-before-phase3']`.
절: 의도 / 관찰 가능한 계약 / 신규 시그니처 / 판정 유형 근거 / oracle 종류와 출처 / 거부해야 할 입력 / library 회로 적용 여부 / 무동작 판정 입력(무발동 값) / 재현할 수치 / V3 계획 / 결정 필요 항목 / 작성 전 실측.
(승인 기록 초안을 card 안 코드 블록에 두면 그 안의 `## ` 줄이 card 절로 파싱되어 절이 셋 늘고 '결정 필요 항목'이 잘린다 -- 그래서 별도 파일로 옮겼다.)

## 4. 남은 것(오케스트레이터·사용자)

* 사용자 승인 1건: `20260930-b34-before-phase3`(앞당김 + 등가 변이 1개 면제). U2와 같은 회차.
* 사용자 작업 1건: `install.py` `SKILLS`에 `"analog-grammar"`.
* B26-1 card 개정 때 인계 한 줄 반영(card 결정 3). B35·백로그에 사이트 5~8·12 인계 기록.
* 계약 9는 레일을 넷 이름 `vdd`/`gnd`로 준다 -- B26 계열이 `trace_*_branches`의 레일 판정을 바꾸면 그 card가 이 test 입력을 조정해야 한다(card 계약 9에 명시).
* 대안(등가 변이 면제를 원하지 않으면): `forks`를 빼면 변이 55개, 면제 0, 계약 9 삭제(card 'V3 계획' 끝).

## 5. 2차 수정(2026-10-01, 오케스트레이터 지시: A2 승인 반영)

* `approval: 20260930-b26-before-phase3`(사용자 승인 A2 -- DEC-60 전환기 종료 + DF-19·26 분리 + B26-1·B34 Phase 3 전 착수, 원문 "승인 (Recommended)"). 위 1·4절의 `20260930-b34-before-phase3` 별도 기록은 폐기(`draft_b34_approval_question.md` 머리에 폐기 표시). A2 기록은 card 커밋 전에 gate에 있어야 한다(현재 HEAD `7535799`에는 아직 없음).
* A2 target에는 변이 id가 없으므로, 등가 변이 면제가 필요한 `find_differential_and_mirror_forks`(사이트 4)를 **범위에서 뺐다**(백로그, 도달 불가 분기 1개 남음). 계약 9 삭제(card 'V3 계획' 끝에 기각한 확장으로 수치와 함께 기록). 계약 5의 `forks(fx) is None`은 기존 동작 고정이라 유지.
* 재측정(모의 head2 = head에서 사이트 4만 되돌림): `changed_defs` = 4개, 변이 12·8·6·29 = **55**(변이 id가 head와 같음 -- 3.3의 판정을 그대로 쓴다), 인벤토리 159·15·66·4.
  계약: 둘 다 부재 126/126 `ImportError`(메시지·경로·`__cause__` 126), `idioms`만 `load_topology` 9/9, `netclass`만 `find_stack_edges` 9/9, 복원 378/378, 계약 5·6 참, base(seed 2) 대 head2(seed 1) 정규화 126/126 같음.
  V3: B34 계약으로 37, 기존 test로 16(`audit_theta` 15, `find_stack_edges` 1), 계약 4로 2 → **55/55 죽음, 면제 0**.
* `parse_spec_card` 재통과: approval `['20260930-b26-before-phase3']`, 절 12개(위 3.4와 같음).
* 4절 '남은 것' 갱신: 사용자 승인 추가 0건(A2로 충분). 사용자 작업 `install.py` 1건, B26-1 인계 한 줄, 백로그(사이트 4·12) 기록은 그대로.

## 6. B26-1 인계 반영(2026-10-01, 오케스트레이터 지시)

* `_drafts/draft_b26_1.spec.md`에 card 결정 3의 인계 한 줄을 반영했다(개정 전 사본 `_drafts/draft_b26_1.v2.spec.md`). 사이트 9·10·10b·13·14의 부재 분기 삭제와 `propose_device_roles_gap_fill`
  3966~3970 `unavailable_reason` 키 삭제(백로그 B40 해소. 분기 자체는 gate 소자 없는 입력 때문에 남김)를 B26-1 범위('의도' 표, 줄은 `7535799` 재측정 -- 이 card 표와 일치)와 계약 13·14에 넣었다.
  순서는 P9 → B34 → B26-1이고, B26-1 착수 조건 4가 B34 병합이다. approval은 두 card 모두 A2 `20260930-b26-before-phase3`이다.
* 재측정(scratch C:/g59, `7535799` archive. 모의 base = +P9 +B34 코드 변경, 모의 head = +B26-1 rails +인계 삭제. `mutate_changed`·`reachability` 함수만 import, `main` 미실행. 측정 뒤 삭제):
  B34 `changed_defs` = 4개(이 card와 같음). B26-1 대상 def 32·변이 2,438·닿은 변이 135. 인계 삭제 없는 비교는 31·2,447·105다. 인계 몫은 중첩 `refine_…classify` +1 def(6변이),
  변이 순 −9(`refine_…` 95→84, `propose_device_roles_gap_fill` 331→327)다. B34 def와 겹침 0, HEAD decision 승인 id와 겹침 0.
  동작: library 9/9 `load_topology`·`refine_…`·`propose_device_roles_gap_fill` 정규화 해시가 모의 base와 head에서 같다. 부재 시 두 함수는 양쪽 다 `ImportError`다. gate 소자 없는 입력에서는
  `unavailable_reason` 키만 사라진다.

## 7. 커밋 준비 최종판(2026-10-01, `draft_b34.final.spec.md`, 계획 `b34_commit_plan.md`)

측정: gate `master` `2d58fd8`(작업 중 `8356c1e`로 움직여 재확인, SD 같음). scratch `C:/g84`(측정 뒤 삭제). 도구 `main` 미실행, 저장소 쓰기 없음.

* **승인 기록 대조.** gate의 `.ai/approvals/20260930-b26-before-phase3.md`가 review2 B1 조건을 채운다: `scope`에 card id·동작 변경, '덮는 것' ③ B34에 동작 변경과 def 4개 이름, 사용자 원문 A2 질문 ③ 인용, '덮지 않는 것'에 V3·V7 면제 일체("B34는 V3 면제가 없다"). `parse_approval_header` 통과. card 결정 1을 '기록 있음 + 대조 결과'로 고침.
* **인계 갱신(B26-1 card v4).** 사이트 10·14를 B26-1 → **B35**로(근거 `review2_b26_1.md` B2·E2·E2b, `b26_scripts/b26v4_head.py` mode v4). B26-1 몫 = 9·10b·13 + B40(`unavailable_reason` 키만). '의도' 3번, 인계 표, 결정 3 고침. 승인 기록 문구("코드 삭제를 B26-1·B35로 넘기는 순서")와 어긋나지 않음.
* **줄 번호.** P9가 SD 3052행 이후를 −11 밀었다. card의 SD 줄 103개를 `difflib` 대응으로 옮김(3020행 미만 그대로). 4 def 포함 15 def의 `def_hash`·`ast.dump`가 `7535799`과 같음.
* **V3 두 규칙.** 변이 55(id 목록 `7535799`과 같음), 인벤토리 159·15·66·4(`8356c1e`도 같음). N2(N2b + 넓힌 T6) 대상 10(3·2·2·3, 넓힌 T6 추가 0).
  55개 B34 계약 판정 재실행: 죽음 39, 나머지 16 = v2의 기존 test 몫 목록과 같음. N2 10개: B34 계약 10/10, 기존 test 9/10(`_import_analog_grammar:except_body_delete:body[4].handlers[0]`만 생존 → 계약 1·2·3이 N2에서도 V3 필수).
  계약 4·6이 혼자 죽이던 변이 5개는 N2 대상 밖 → 두 계약은 '현행 규칙에서 V3 필수, N2에서는 동작 고정 계약으로 유지'로 표시만 바꿈(삭제하지 않음).
* **계약 7 정규화 주의(새 발견).** `refine_…` 반환 `vertical_stack_id_candidates["groups"]`의 dict 키 순서가 `PYTHONHASHSEED`마다 다르다. card 정규화(dict `==`)로는 문제없지만 문자열·해시 비교면 키 정렬이 필요 -- card 정규화 절에 한 줄 추가. 정렬 시 base 대 head 126/126.
* **red 재현.** `8356c1e` base: 세 부재 모드 각 126/126 조용히 반환, 다른 예외 0. 모의 head: 계약 1~6·8 전부 참.
* **interface card.** `build`와 CLI 출력 같음, 14행 전부 `stick_diagram`, 빠짐·엉뚱한 기호 0. `parse_spec_card` 통과(절 12개).
* **기타 반영.** 결정 4(P9 병합 완료, P9 판정 스크립트 `diff_dup.py` 17~20행의 `None` 검사는 과거 산출물이라 그대로), 문서 커밋 뒤 `test_phase2_stale_refs`(P10 계약 5) 실행 안내.

## 7. 인계 사이트 10·14를 B35로 이동(2026-10-01, B26-1 v4 -- review2_b26_1 B2 E2·E2b)

* B26-1 v4는 사이트 9·10b·13·B40만 지운다. 사이트 10(`refine_…` `if _netclass_al is not None:` 삭제 + 블록 내어쓰기)과 14(`propose_device_roles_gap_fill` `if _idioms_lcmf is not None:`·`else:`·
  `cascoded_active_load_legs = set()` 삭제 + 블록 내어쓰기)는 **B35**로 옮겼다. 근거: V3 범위 정책(`20260930-v3-changed-stmt-scope` 계약 1)에서 들여쓰기만 바뀐 문장은 새 문장이라 두 블록 전체가
  대상이 되고, 그 출력(netclass·idioms 유래)은 B26-1의 '계약이 아닌 것'이며 기존 test도 보지 않는다(모의 실측 생존 13 + 1). 두 분기는 B34 뒤 도달 불가인 채 남는다(동작 영향 없음).
* 고친 곳: `draft_b34.spec.md`(사본 `draft_b34.v3.spec.md`) '범위' 3의 인계 글머리표, 인계 표 10·14 행(→ B35), 결정 3의 인계 한 줄(9·10b·13). `backlog_additions.md` B35 줄에 추가.
  `parse_spec_card` 재통과(approval `['20260930-b26-before-phase3']`, 절 12개). B34 자신의 코드 변경·계약·V3(55/55)는 그대로다.
* 재측정(scratch C:/g83, 삭제): v4 B26-1 대상(범위 정책 규칙) 330 → 301(`refine_…` 40 → 17, `propose_device_roles_gap_fill` 58 → 52). 상세 `_drafts/b26_1_revision_log_v4.md` §2.
