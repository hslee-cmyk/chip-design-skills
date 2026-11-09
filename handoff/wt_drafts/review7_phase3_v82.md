# 7차 독립 검토 -- Phase 3 `30-module-split` 초안 v8.1 → v8.2 델타 (E5 비교 판 기본안을 선례 모양으로)

검토자: 독립 검토 agent(작성자·이전 검토자 아님). 저장소 읽기 전용, 상태 변경 git 없음.
측정: `C:/g142`(`git clone --no-hardlinks` -- `base` = `a796468`, `old` = `da03c0e`, 시제품 `el_p1`·`el_p4`·`el_p5` = `a796468` + 아래 패치), 끝난 뒤 `C:/g142` 삭제. Python `C:/Python314/python.exe -B -P`, `APPDATA`·`HOME`·`PYTHONPYCACHEPREFIX` export.
**루프 종료 규칙**: (a) v8.2 변경이 만든 결함, (b) 6차 검토 항목 중 풀리지 않은 것만 적는다.

검토 대상 판(sha256 앞 16자리, 검토 시점 재계산 = 승인 질문 '대상 판 해시'와 같음): design v8.2 `dc2a887b2c11f382`, 문서 개정 `5104bfe4c23aeebf`, `e_lib_p3.py` `c6b82fc7b4cd974c`,
`e_inst_p3.py` `7d26134ad00ec504`, G1 `3a99df21414d6e99`, T0 `35f7e3e7850a2847`, D0a `1f9592d491303132`. 승인 질문 = `d2476b580f548fdf`.

## 판정

**막는 것 없음. 고칠 것 2건(S1 판정 python 한 줄, S2 승인 질문의 이미 답한 A2-③), minor 3건. 고친 뒤 승인 요청 가능.**
선례는 충실하게 따랐다. 같은 경로, 같은 사본, 의도된 필드만 계약값으로 판정하고 나머지는 해시가 같아야 한다. E-INST는 선례보다 엄격하다(raw까지 비교).
빼는 필드 목록(`EXCL_INST=()`, `MASK_META=("rails",)`)은 지금 card 초안 계약에서 빠진 것이 없다. `e_lib_p3.py`와 `e_lib.py`의 동등은 다시 재서 확인했다.
약화는 하나 있다. 빼낸 `rails` 값의 계약 판정이 `nets` 성분만 본다(S1). 그래서 계약에 없는 필드가 끼어도 PASS가 난다. 시제품으로 재현했다.

---

## 1. 재측정

| 항목 | 실행 | 결과 |
|---|---|---|
| (1) 선례 원문 | `.ai/approvals/20260930-phase2-e4-baseline.md` | 질문 맥락 원문: "기본안 = da03c0e와 Phase 2 마지막 병합본을 같은 경로에서 비교하고 `topology_ref`만 DF-36 계약값으로 판정, 대안 = card별 판정 기록 사슬로 갈음". 사용자 원문 "둘다 기본안으로 진행해". design 20 §10 E4(223행): 같은 `<iso>`에서 두 판을 차례로 뜨고, 판을 바꿀 때마다 `checkout -- workspaces`·`clean -fdx`를 한다. 사본은 `<iso>` 밖, 두 판에 같은 사본을 쓴다. 판정은 E-LIB `hash` 동일, E-INST `without_topology_ref_sha256` 동일 + `topology_ref` 계약값이다. **v8.2 E5 블록은 이 모양을 지킨다**: `fresh()` = checkout + `checkout -- .` + `clean -fdx`, 사본은 `$X`(iso 밖)·sha256 기록, P2D·HEAD에 같은 사본을 쓴다. 의도된 필드(`rails`)만 계약값으로 따로 판정하고, 나머지 해시는 같아야 한다. 선례와 다른 점은 둘이고 둘 다 더 엄격하다. E-INST는 두 판에 같은 `e_inst_p3`를 쓰고 동등을 먼저 확인한다(선례는 df35/df36 서로 다른 스크립트). raw·키별 해시도 같아야 한다(선례는 without_topology_ref만) |
| (4) `e_lib_p3` ≡ `e_lib` (F1 전 트리) | `a796468`·`da03c0e` 각각 `e_lib.py`, `e_lib_p3.py`(인자 없음), `… rails`, `… rails rails` | 네 판 모두 `hash` `1d2e3bf6acf762eb`이다(두 커밋이 같은 값). 판정 python의 `dropk(q) == e_lib 출력`이 True, stdout은 바이트 동일, `masked` = `{}`(인자 없음) / `{"rails": "<ABSENT>"}` 9회로, 9/9 load ok. F2v82 재현 |
| E-INST(P2D 대용 = `a796468`) | `e_inst_df36`·`e_inst_p3` × 2회로, `el_p1`의 `e_inst_p3` folded | raw: 파일럿 `2fc426d9…`, folded `ef3cd996…`(df36 = p3 = p1). `field_sha256` 키 8개는 F1v82와 같다. `rails`는 instance.json에 닿지 않는다(F3v82 재현) |
| (3) 판정 python | design v8.2에서 PYEOF 블록을 그대로 뽑음(sha `37fecfea…` = 작성자 `p3v82_e5_judge.py`). P2D = `a796468` 실측, HEAD = 시제품 | `p1`(계약 1·2 모양): `E5 E-LIB/E-INST PASS`. **`p4`, `p5`도 `PASS`**(§2 S1·§3 m1) |
| (2) 빼는 필드 | card 초안 현재 판(21:25 -- phase 줄 `3`·`approval: 20261001-b26-phase3-cards`·순서 문장만 바뀜, `draft_b26_1.v5`·`backfill.v3` 대비 diff 확인) + `a796468` 소스 | 아래 §1.1 |

### 1.1 빼는 필드 목록 완전성 (점검 2)

| 후보 | 근거 | E-LIB·E-INST에 닿나 |
|---|---|---|
| B34 meta(grammar 있음) | 계약 7: "E-LIB 9/9(`load_topology`, `run_topology_pipeline` V1·V2)와 E-INST가 base와 같다". E5는 `<iso>` 저장소 안 `skills/analog-grammar`가 있는 상태에서 돈다(저장소에 있음 확인) | 없음. 다르면 E5 FAIL 쪽(거짓 FAIL)이고 약화는 아니다 |
| B26-1 다른 meta 키 | 계약 2 "`meta`의 다른 키와 `transistors`는 base와 같다", 계약 8 "`meta`(새 키 `rails` 제외)… `run_topology_pipeline` 출력이 base와 같다… E-INST 해시 동일". 씨앗이 vss 3회로에서 하나 늘지만 "`load_topology` 결과는 9/9 같다"('무동작') | `rails` 하나 |
| B40 `unavailable_reason`(B26-1 계약 14) | `a796468` SD 8657~8726: `load_topology`는 `propose_device_roles_gap_fill` 반환 중 `device_roles_proposals`·`matching_pairs_proposals`·`review_needed`만 읽는다. `unavailable_reason`은 `refined is None`(gate 없는 입력·grammar 부재)일 때만 생긴다 | 없음 |
| B26-1 계약 13 인계 삭제 | grammar 있음에서 반환 9/9 같음(계약 13 끝) | 없음 |
| P9 시그니처(B26-1이 `rails` kwarg 추가, 승인 `20261001-b26-p9-signature-update`) | 시그니처는 E-LIB·E-INST 출력이 아니다. P9 자체는 `a796468` 이전 병합 | 없음 |
| backfill `interdig_ok` | 계약 2 "rows·audit·사유 불변", 'library 적용' "`load_topology`·`run_topology_pipeline`은 닿지 않는다". `save_instance_json` 키 8개 고정(위 E-INST 재측정과 같음) | 없음 |
| b26pre | test-only | 없음 |
| 사이 다른 card(면제 묶기·범위 정책·B33·G1·T0·D0a·D0b) | 게이트·도구·test·레지스트리 | 없음. B37a는 `phase: 4`라 창 밖 |

결론: 지금 계약 기준으로 **목록은 완전하다**. 단 증거는 card 계약과 시제품이다. 실제 병합본 값은 DoD가 잰다(design 부록 A 한계 문장이 이미 적음).

---

## 2. Should-fix

### S1. `rails` 계약값 판정이 `nets`만 보고 `RailDeclaration`의 다른 필드는 보지 않는다 (v8.2 결함, fail-open)

* 판정식(design §10 E5 판정 python): `cok = (want is not None and isinstance(hv, dict) and hv.get("__dc__") == "RailDeclaration" and hv.get("nets") == want and (bv == "<ABSENT>" or bv == hv))`.
* B26-1 계약 1: "`RailDeclaration(nets=frozenset(topology["supply_nets"]))`(frozen dataclass, **필드 `nets` 하나** -- B26-2가 극성 필드를 더한다)". 계약값은 필드 하나짜리 값 전체다.
* `rails`는 해시에서 빠진다. 그래서 `rails` 안에서 `nets` 밖에 있는 것은 이 판정 말고는 아무도 보지 않는다. Q-B34-PHASE 답으로 네 card가 P2D 뒤에 오므로 P2D `bv`는 `<ABSENT>`이고, `bv == hv` 쪽 보호도 없다.
* **재현**: `el_p4` = `a796468` + 계약 모양 `RailDeclaration`에 계약 밖 필드 `polarity: str = 'junk-g142'`. 원래 `e_lib.py` 해시는 `7f03751a…`로 base와 다르다. `e_lib_p3 rails` 해시는 `1d2e3bf6…`로 base와 같다. 판정 python 출력은 `E5 E-LIB/E-INST PASS`이다.
* 다른 방어선: Phase 3 M card equivalence는 `e_lib.py`를 그대로 쓴다(rails 포함 해시). 그래서 M card가 그 필드를 바꾸면 card 단계에서 잡힌다. 그러니 실제 위험은 낮다. 그래도 DoD 판정식은 'card 계약값으로 판정'(D-28 (e))을 계약보다 좁게 옮겼다.
* **고칠 것(한 줄)**: `hv.get("__dc__") == … and hv.get("nets") == want`를 `hv == {"__dc__": "RailDeclaration", "nets": want}`로 바꾼다. E5 행 (iv)는 이미 "HEAD `masked.rails` = `{"__dc__": "RailDeclaration", "nets": …}`"라고 같음으로 적었으니 표 문장은 그대로 둔다. 판정 python이 바뀌므로 F3v82의 judge sha(`37fecfea…`)와 시나리오를 다시 재고, 이 p4 모양을 FAIL 시나리오에 더한다.

### S2. 승인 질문에 이미 답한 A2-③가 남아 있다 (질문 올리기 전 정리)

* `_drafts/user_decisions.md`(21:17:22) 67행: `[Q-B34-PHASE] "phase 3 + 정정 기록 (Recommended)" -- B34·b26pre·backfill·B26-1 네 card phase: 3 …, 후보 id 20261001-b26-phase3-cards`. card 초안 넷은 21:25에 `phase: 3`·`approval: 20261001-b26-phase3-cards`로 바뀌었다. B26-1 순서 문장은 "P10b → **Phase 2 DoD** → … → B26-1"이다.
* v8.2 승인 질문(21:19)은 여전히 "**다섯 질문**"(10행)이고 A2-③(79~89행)을 묻는다. design D-28 (e)에도 "(나)로 네 card가 P2D 앞에 오면…" 가지가 남아 있다.
* 판정식은 어느 답이든 같아서(질문 87행 (5)) 결과는 변하지 않는다. 다만 이대로 올리면 같은 질문을 두 번 묻는다.
* **고칠 것**: 질문에서 A2-③ 블록을 빼고 "네 질문"으로 고친다. A2-③ 승인 기록 문장(12행)은 `20261001-b26-phase3-cards` 참조로 바꾼다. D-28 (e) '(나)' 문장은 "답 = (가)(Q-B34-PHASE): P2D `masked.rails` = `<ABSENT>`"로 좁힌다(선택. 판정 python의 `bv == hv` 허용은 남겨도 무해하다).

---

## 3. Minor

| # | 내용 |
|---|---|
| m1 | **계약값의 출처가 HEAD library다.** `want`는 `ISO`(HEAD)의 `library/<회로>.topology.json` `supply_nets`에서 읽는다. P2D `bv`가 `<ABSENT>`라서 P2D와 HEAD 사이에 library `supply_nets`를 바꿔도, 다른 출력이 같으면 걸리지 않는다. 재현: `el_p5` = p1 + `two_stage_ota` `supply_nets`에 `agnd` 추가(트랜지스터 단자가 아님). 원래 `e_lib.py`는 `9812155e…`로 다르다. `e_lib_p3 rails`는 `1d2e3bf6…`이고 판정 python은 **PASS**이다. 선례에서도 입력 파일 자체는 해시하지 않았고, Phase 3 card가 library를 바꿀 경로는 승인 기록이 막는다. 그래서 차단은 아니다. 고치려면 `nets`를 `git -C "$ISO" show "$P2D:skills/analog-gmid-design/assets/library/<회로>.topology.json"`에서 읽는다(P2D library도 `supply_nets`를 이미 선언했다 -- 2026-09-17 U-26). 그러면 '그 card 계약값 = 비교 시작 판의 선언'이 된다 |
| m2 | **승인 질문 (c) 기본안에 비용 문장이 없다.** 대안에는 "대안이 나은 경우"가 있다. 그런데 기본안의 비용은 없다. 빼는 필드 목록이 design 상수(`EXCL_INST`·`MASK_META`)라서, 사이 card 계약이 바뀌면 design 개정(승인 diff)이 다시 필요하다는 점이다(D-28 (e) 끝 문장이 적음). 중립을 위해 한 줄 더한다. 또 "빼는 필드는 card 계약에서 유도하고 **실측으로 확인했습니다**"는 rails 쪽이 B26-1 실물이 아니라 계약 모양 시제품이다(design 부록 A 한계 문장). 그래서 "계약 모양 시제품으로 실측"으로 좁힌다 |
| m3 | E5 블록은 `e_inst_df36.py`·`e_lib.py` 사본을 P2D 판에서 뜨고, 선례는 병합본 판에서 떴다. D-9(`.ai/verification/**` 무변경)로 같은 바이트이고 sha256을 기록하므로 영향은 없다. 기록용 |

---

## 4. 6차 검토 항목 상태

| 6차 # | 상태 |
|---|---|
| N1 | 해결 -- v8.1에서 질문 (c)로 드러냈고, v8.2는 기본안을 선례 쪽으로 옮겼다. 선례 인용 문장은 승인 기록 원문과 같다 |
| N2 | 해결(E2 행에 "`E2 INVALID` 줄 없음" 있음) |
| N3 | 해결(질문 A2-③ '네 card'). 다만 그 질문 자체가 이제 답해졌다 -- S2 |
| N4 | 해결(질문 86~87행 V1 `--gmid-phase`·`--gmid-strict` 문장) |
| m-a~m-c | v8.1 반영. 이번 범위 밖 |

## 5. 점검 (5) 승인 질문 UD-0 (c) 문구

* 기본안 문구 "Phase 2 완료 판정 대상 커밋과 Phase 3 마지막 병합본을 같은 경로에서 비교…의도적으로 바꾼 필드만 빼서 그 card의 계약값으로 따로 판정…나머지는 해시가 같아야" -- design E5 블록·행과 같다.
* 대안 "B0… 측정 명령은 같고 비교 커밋 하나만 바뀝니다" -- 블록 주석 "P2D 자리에 B0… 나머지 명령·판정 python 그대로"와 같다.
* 선례 인용 -- 승인 기록 질문 맥락 원문과 같다(따옴표 안 문장 일치).
* `(Recommended)`는 권고 하나에만 붙었고, v8.1에서 뒤집은 사실도 밝혔다. 중립성 보강 m2 하나만 남는다.

## 6. 정리

S1(판정 python 한 줄 + F3v82 재측정, p4 시나리오 추가)과 S2(이미 답한 A2-③ 제거)를 고치면 승인 질문을 올릴 수 있다. m1~m3는 선택이다.
재현 자료(`C:/g142`, 삭제함): 패치 스크립트 `mkproto.py`(p1 = `meta["rails"] = rail_declaration(data)` + frozen `RailDeclaration(nets)`, p4 = p1 + `polarity` 필드, p5 = p1 + `two_stage_ota` `supply_nets`에 `agnd`), 판정 python은 design에서 그대로 뽑았다(sha `37fecfea…`).
`git -C <repo> status --short` 출력은 검토 전후 같다.
