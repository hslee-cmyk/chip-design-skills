# B26-1 V3 생존 변이 -- 통합 사용자 질문(최종안)

작성 2026-10-01. 두 분석(`_drafts/draft_b26pre.spec.md` 계열의 N2d 측정, `_drafts/draft_b26_1.spec.md` v4·`b26_1_survivor_question.md`의 card 규칙 측정)과
독립 검토 `_drafts/review_b26pre.md`, b26pre v2 개정(`b26pre_revision_log.md`·`b26pre_v2_kill_map.md`·`b26_backfill_question.md`)을 **한 정의·한 측정**으로 합쳤다.
이 문서가 `b26_1_survivor_question.md`(Q1~Q3)와 `b26_backfill_question.md`(U-BF)를 대신한다. 오케스트레이터는 아래 Q1~Q3을 AskUserQuestion으로 묻는다.

측정 근거(오케스트레이터 사전 측정, 판정 수치 아님 -- auditor가 병합본에서 다시 잰다):
* 정의: 승인된 범위 규칙 **N2(b) + 넓힌 T6**(`20260930-v3-changed-stmt-scope`, 분류기 = 그 card 구현 기준 `v3_scope_widen.py`). N2d(deep)는 쓰지 않는다.
* head: B26-1 **v4** 모의 head(사이트 10·14는 B35로 넘김). 모의 base `b1` = gate `master` `a796468` + B34 코드 변경(사이트 1·2·3·11·11b). 엔진은 `766b5c2` 이후 그대로(그 뒤 커밋은 test·문서뿐).
* 스크립트 `_drafts/b26_reconcile/`(scratch `C:/g103`, 측정 뒤 삭제). 결과 원본은 `_drafts/b26_reconcile/out/`(jsonl·분류·요약), 통합 생존 표 `_drafts/b26_reconcile/out/survivor_table.md`.
* 시제품 합집합(모두 scratch, 커밋하지 않음): B26-1 계약 근사(`b26_reconcile/test_b26x_approx.py` 5 test + `test_b26x_metric_approx.py` 1 test -- 'V3 계획' 4의 `_metric_kcl_residual` 이름 직접 호출 근사, 이번에 더함),
  b26pre 시제품 v1(15)·v2(17, `b26pre_v2_scripts/proto_v2_test_b26pre.py`), trace 보강 2(`b26_reconcile/proto_test_b26pre_trace.py`, 이번에 더함), backfill red-green 2(`b26pre_v2_scripts/proto_bf_test.py`).
  모든 시제품은 변이 없는 base(b1, backfill 수정 base, 정리 base)에서 PASS.

---

## 측정 요약(질문 본문에 쓰는 수치)

**1. 대상**: v4 head의 V3 대상 **301** = b1 대응이 있는 기존 문장 변이 **264** + 새 문장 변이 **37**(새 def `rail_declaration` 14, 선언 획득·`meta["rails"]`·`rail_nets` 거부·사이트 13·B40 문장 23 -- 모의 사본에서 돌릴 수 없어 B26-1 계약 1·2·3·5·6·13·14 몫, auditor가 병합본에서 잰다).

**2. 기존 test로 잰 생존**(264개 전부 판정: 187개는 이전 측정의 '죽음' 재사용 -- 엔진 소스 같고 test 집합은 늘기만 함, 77개는 이번에 `a796468`+B34 사본에서 다시 실행): 죽음 214, **생존 50**.
이 50의 처리(표 `survivor_table.md`, 변이마다 head 줄·b1 줄·문장·세 시제품 판정):

| 묶음 | 수 | 누가 죽이나 | 비고 |
|---|---|---|---|
| B26-1 자기 계약 | 26 | B26-1 card 계약 근사(7(e) E1 14, 4 기본값 E3 6, 7(a) E5 2, 7(c) 1) + 'V3 계획' 4 이름 직접 호출 3 | `_metric_kcl_residual` 3개(인벤토리 0)도 직접 호출 근사 1 test로 죽는 것을 이번에 실측 |
| 기존 동작 test 공백 -- b26pre card | 16 | b26pre 시제품(v1·v2 같음) | LUT 없는 repair 4, euler fixup 3, finger growth 4, E7 5(`run_full_circuit_audit` 2·`resolve_stack_layout` 1·포트 1·`case_collisions` 1) |
| 기존 동작 test 공백 -- trace 루프 범위 | 2 | **trace 보강 2 test**(b26pre card에 더할 것) | `find_differential_pair_candidates` `range(i + 1, …)`의 const+(같은 서명 branch 2개에서 후보 소실)·arith(3개에서 후보 목록 순서 변경) -- 아래 Q1 근거 |
| 등가 아님 -- 결함(backfill) | 2 | 지금 동작 고정 test로는 죽이면 안 됨 | SR 11800·11879 `_backfill_interdig_ok(result)` 삭제. 구별 입력 있음(독립 검토 `nohub_blocked`, 이번에 `C:/g103`에서 재확인: 원본 `interdig_ok` False / 반환 audit 3b True / 변이 True). backfill card(U-BF)로 문장을 지우면 대상에서 사라진다 |
| **진짜 등가** | **4** | 어떤 test로도 못 죽임 | 아래 Q1 '등가 4의 근거' |

**3. 계획대로 다 했을 때 남는 것**(통합 측정, 시나리오별로 V3 대상 전체를 다시 분류하고 시제품 합집합 → 생존만 기존 인벤토리로 실행):

| 시나리오(전제: b26pre card[trace 2 포함] + backfill card가 B26-1 앞에 병합) | V3 대상(N2w) | 대응 있음 / 새 문장 | 시제품 합집합 생존 | 기존 test까지 생존 = **남는 수** |
|---|---|---|---|---|
| A. 등가 4는 손대지 않음 | 299 | 262 / 37 | 61 | **4**(등가 4 그대로) |
| B. B26-1이 정리 C1·C2·C3 모두 | 313 | 276 / 37 | 65 | **7**(등가 4는 사라짐, 대신 C3 내어쓰기로 대상이 된 루프 본문 문장 7개 생존) |
| C. B26-1이 정리 C1·C2만(권고) | 299 | -- | -- | **1**(`range` const−). 측정 아닌 조합: C의 대상 id가 def별로 A·B와 정확히 같음을 확인(`_propose_L_roles` 9·`propose_device_roles_gap_fill` 53 = B, `find_differential_pair_candidates` 13·나머지 224 = A), 정리는 동작 불변이라 판정이 def별로 같다 |

* B의 새 생존 7(`find_differential_pair_candidates` 루프 본문 `if a == b: continue`·`if ta.kind != tb.kind or ta.gate == tb.gate: continue`·`if key in seen: continue`·`seen.add(key)`와 그 `continue`들): C3가 이중 루프를 `itertools.combinations` 한 겹으로 바꾸며 본문을 내어써서 이 문장들이 '바뀐 문장'이 된 몫이다.
  일부는 test로 죽일 수 있고 일부는 등가로 보인다 -- 등가 1개를 없애려다 새 몫 7개를 만들므로 C3는 권하지 않는다.
* 요약: **test 보강(b26pre 19 test) + backfill 수정 뒤 B26-1 V3에 남는 것은 진짜 등가 4개뿐이다.** C1·C2 정리를 하면 1개.

**4. 앞선 두 분석과의 차이(정렬 결과)**
* b26pre v1의 '생존 54 = E6·E7 34 + B26-1 몫 20'은 N2d(deep) 대상이었다. N2w로는 E6·E7 생존이 18(b26pre가 16 죽임 + backfill 2)이고, v1이 등가 후보로 둔 9개 중 씨앗 6개·SR 11802는 **N2w 대상이 아니다**(v2 계약 10이 씨앗 6개를 덤으로 죽인다, 11802 면제는 필요 없다).
* B26-1 v4의 '남는 24 = E6 13 + E7 5 + trace 2 + 등가 4'는 N2w로 재현된다(50 − B26-1 계약 26). 그중 '등가 아닌 E6' 2개(backfill)는 등가도 '기존 test 공백'도 아니고 **결함**이었다(독립 검토).
* 등가 판정 정정: 이번 분석의 무작위 퍼즈(1,200건)는 backfill 차이를 못 찾았다(모든 쌍이 source를 공유하게 만들어 repair가 쌍을 새 행으로 빼냈기 때문). 독립 검토의 '공유 source 없는 쌍 + euler-blocked 행' 입력으로 차이를 재현했다. 등가 주장은 구별 입력을 구성으로 찾은 뒤에만 한다.

---

## Q1. [U3 통합] B26-1 V3에서 남는 생존 변이를 어떻게 처리할까요?

**배경(질문 본문)**:
B26-1을 정하신 V3 규칙(바뀐 문장 + 같은 블록 뒤쪽 읽기)으로 재면 대상은 301개이고, 지금 test로는 그중 50개가 살아남습니다.
- 26개는 B26-1 card가 이미 계획한 계약 test가 죽입니다(모의 측정).
- 18개는 **기존 동작인데 test가 없는 경로**입니다(레일과 무관: LUT 없는 matching 수리, euler 막힘 행 분할, 핑거증가 반환 경로, 전체 감사 체크 3, stack 후보, 포트 경로, 넷 대소문자 충돌, 차동 후보 trace 루프 범위). 앞선 test-only card(b26pre) 1건이 19 test로 전부 죽입니다(엔진 변경 없음, base에서 PASS).
- 2개는 **결함**입니다: 핑거증가 루프가 돌려주는 `interdig_ok`가 같은 반환의 audit과 어긋납니다(재현 입력 있음). 지금 동작을 test로 고정하면 결함을 정답으로 박게 되므로, 고치는 card(red-green)를 따로 두면 이 두 줄이 없어집니다.
- 4개는 **등가 변이**(바꿔도 동작이 같음)라 어떤 test로도 죽지 않습니다.

**등가 4의 근거**(구별 입력이 존재할 수 없는 이유):
1. `_propose_L_roles` `if gm_id_roles is None: return None` 삭제, 2. 같은 함수 `if candidates is None: return None` 삭제 -- `_propose_gm_id_roles`가 `None`을 돌려주는 유일한 경우는 같은 인자의 `find_differential_pair_candidates`가 `None`일 때다(모의 head 2086~2089). 두 가드는 같은 조건을 두 번 보므로 어느 하나를 지워도 다른 하나가 같은 `None`을 돌려준다.
3. `propose_device_roles_gap_fill` `open_net = open_terminals[0]` → `[-1]` -- 바로 앞 줄이 `len(open_terminals) != 1`이면 건너뛴다(원소가 정확히 1개).
4. `find_differential_pair_candidates` `range(i + 1, …)` → `range(i, …)` -- 늘어난 짝 `j == i`는 같은 chain끼리라 모든 위치에서 `a == b`로 건너뛴다(부작용 없음). 합성 2·3 branch 입력에서도 출력 동일 실측(`out/exp_trace.txt`).

**선택지**:
1. **(Recommended) test 보강 + 결함 수정 + 등가는 동작 불변 정리 2줄 + 남는 등가 1개만 해시 묶기 면제**
   - (a) b26pre test-only card(19 test = v2 시제품 17 + trace 범위 2)를 B26-1 앞에 병합. 엔진 변경 없음, 판정 기준 약화 없음.
   - (b) backfill 결함 card(red-green, `_drafts/draft_b26_backfill_audit.spec.md`)를 b26pre 뒤·B26-1 앞에 병합: `interdig_ok`를 반환 audit(euler 정리 뒤)으로 채운다. 관찰 가능한 값 1개가 바뀌는 **엔진 변경**(행·audit·사유는 그대로, 사본에서 `A/tests` 전체 회귀 없음 -- b26pre v2 측정).
   - (c) B26-1 code-author가 같은 def 안에서 **동작 불변 정리 2줄**(엔진 변경, 명시): `_propose_L_roles`의 중복 가드 `if candidates is None: return None` 삭제, `open_net = open_terminals[0]` → `(open_net,) = open_terminals`. 등가 3개가 사라지고, 남는 `gm_id_roles` 가드의 삭제 변이는 B26-1 계약 14(E4)가 죽인다(측정 B).
   - (d) `range(i + 1, …)` const− 1개는 정리로 없앨 수 없다(`itertools.combinations`로 바꾸면 루프 본문 7문장이 새로 대상이 되어 생존 7 -- 측정 B). 그래서 이 1개만 **변이 id@함수 원본 해시 decision 면제**(A1-a 규칙, 해시가 바뀌면 자동 무효). 판정 범위 축소라 **약화 승인**이다(1건).
   - 결과: B26-1 V3 남는 생존 **0**(면제 1 제외). 비용: test 19(그중 새로 쓸 것 trace 2), 결함 card 1건, 엔진 정리 2줄, 면제 1건.
2. **test 보강 + 결함 수정 + 등가 4개 모두 해시 묶기 면제(약화)**
   - (a)·(b)는 1과 같고, 엔진 정리 없이 등가 4개를 변이 id@def 해시로 면제한다(승인 기록 1건에 4개). 면제 수 4, 엔진 정리 0.
3. **test 보강 + 결함 수정 + 등가 4개 모두 정리(C1·C2·C3)** -- 권하지 않음: 면제는 0이지만 C3가 새 생존 7을 만들어 그 7개를 다시 test 보강하거나 면제해야 한다(측정 B).
4. **(기준 약화) test 보강 없이 남는 것을 모두 해시 묶기 면제** -- 권하지 않음: 26개를 뺀 24개(죽일 수 있는 18 + 결함 2 + 등가 4)를 면제하게 되고, 결함 2개를 '면제'로 덮는다(등가가 아니므로 A1-a '등가' 문구로는 쓸 수 없다).

**하위 결정 Q1-BF(1·2·3을 고르면 함께 확정)**: backfill 결함을 위 (b)대로 고칠까요?
- (Recommended) 고친다 -- 승인 기록 문안은 `_drafts/b26_backfill_question.md` 1번(id 후보 `20261001-b26-backfill-interdig-fix`, `target_kind: decision`) 그대로.
- 지금 동작 고정 -- 권하지 않음(결함을 정답으로 박음).
- 백로그 + B26-1 V3에서 '알려진 결함 생존' 2개 면제 -- 별도 결정 기록 필요, 불일치 남음.

**1번이면 남길 면제 승인 기록 문안(d)**:
```
id: 20261001-b26-v3-equiv-range
date: <답한 날>
target_kind: decision
target: stick_diagram:find_differential_pair_candidates:const-:<B26-1 병합본 AST 경로>@<그 def 원본 해시>
scope: 결정 U3 -- B26-1(20260930-b26-rail-accessor-set) V3 등가 변이 1건 면제: range(i + 1, len(chains))의 1 -> 0. 늘어난 j == i 짝은 같은 chain이라 모든 위치에서 a == b로 건너뛴다(부작용 없음)
```
(본문) 사용자 원문 / 질문 / 덮는 것: 위 변이 1건(id·해시는 auditor가 병합본에서 `mutants()`로 확정해 적는다) / 덮지 않는 것: 같은 def의 다른 변이, 다른 card / 재검토: def 해시가 바뀌면 자동 무효(면제 묶기 card 규칙).
2번이면 `target`에 4개 id@해시를 적고 scope에 등가 4의 근거 1~4를 적는다(id 후보 `20261001-b26-v3-equiv-4`).

---

## Q2. [U4] A2 승인 기록에 B40(gate 없는 입력의 `unavailable_reason` 키 삭제)을 더해도 될까요?

(`_drafts/b26_1_survivor_question.md` Q2 그대로 옮김.)

**배경**: gate에 커밋된 A2 기록 `20260930-b26-before-phase3`의 범위 ③ B26-1 항목은 "B34에서 인계받은 도달 불가 부재 분기 삭제를 포함한다"만 적었습니다.
B40은 도달 불가 분기가 아니라 **도달 가능한 분기의 반환값 변경**입니다: analog-grammar가 있어도 gate 소자가 없는 입력이면 `propose_device_roles_gap_fill`이
`{…3키…, "unavailable_reason": "analog-grammar를 import할 수 없어…"}`(틀린 사유)를 돌려주는데, B26-1은 이 키만 지워 3키 dict를 돌려주게 합니다. 소비처는 0곳입니다(`git grep`).

**선택지**:
1. **(Recommended) 짧은 추가 승인 기록 1건으로 덮는다** -- id 후보 `20260930-b26-b40-reason-key`, `target_kind: decision`, `target: U4-B26-B40`.
2. B40을 B26-1에서 빼고 백로그(B39와 함께)로 둔다 -- 틀린 사유는 남습니다.

**추가 승인 기록 문안(1번)**:
```
---
id: 20260930-b26-b40-reason-key
date: <답한 날>
target_kind: decision
target: U4-B26-B40
scope: 결정 U4 -- A2(20260930-b26-before-phase3) 범위 ③ B26-1 보충: propose_device_roles_gap_fill이 gate 소자 없는 입력(refined is None, analog-grammar 있음)에서 돌려주는 dict의 unavailable_reason 키 삭제(백로그 B40, 관찰 가능한 반환값 변경)
---
(본문) 사용자 원문 / 질문 / 덮는 것: 위 키 하나 삭제(분기 자체와 나머지 세 키 matching_pairs_proposals·device_roles_proposals·review_needed는 그대로, spec card 계약 14) /
덮지 않는 것: propose_theta_kcl_gap_fill의 unavailable_reason(B39), V3·V7 면제 / 재검토: 소비처가 생기면 다시 묻는다.
```

---

## Q3. [U5] P9 계약 test 2개의 시그니처 단언을 B26-1의 새 시그니처로 갱신해도 될까요?

(`_drafts/b26_1_survivor_question.md` Q3 그대로 옮김.)

**배경**: P9(`20260930-p9-kcl-edges`, 병합 `b7765b0`)의 영구 계약 test `test_kcl_series_union_signature_unchanged`·`test_kcl_and_matching_edges_signature_unchanged`는
매개변수 목록이 정확히 `[netlist, matching_pairs]`·`[transistors, matching_pairs]`이고 모든 매개변수 주석이 `list`인지 단언합니다. B26-1은 두 함수에 기본값 없는 키워드 전용 `rails: RailDeclaration`을 더하므로
병합본에서 두 test가 FAIL합니다. 기대값 변경은 test 작성자가 혼자 할 수 없습니다(작성자≠검증자, V5).

**선택지**:
1. **(Recommended) 갱신 승인** -- 새 기대 = `[…, "rails"]`, 앞 두 매개변수 단언 그대로(주석 `list`, 기본값 없음), `rails`는 키워드 전용·기본값 없음·주석 `RailDeclaration`, 반환 주석 그대로.
   P9의 '시그니처 유지' 계약을 B26-1 계약 4가 대체하며, 정확 일치 단언은 유지되므로 판정 기준 약화가 아닙니다. 승인 기록 `target_kind: diff`(id 후보 `20260930-b26-p9-signature-update`, test diff 위).
2. P9 시그니처를 유지하고 B26-1이 `kcl_series_union`·`_kcl_and_matching_edges`에 `rails`를 넘기지 않게 설계를 바꾼다 -- 두 함수의 레일 판정(계약 7(b))을 선언으로 바꿀 수 없어 B26-1 목표와 충돌(권하지 않음).

---

## 순서(Q1 1번 기준, 원칙 기본안)

P9 → P10 → P10b → V3 면제 묶기 → V3 범위 정책 → B34 → **b26pre(test-only, 19 test)** → **backfill 결함 card(red-green)** → B26-1(정리 2줄 포함, 면제 1건).
b26pre는 B34와 독립이지만 B34 인벤토리 수치를 낡게 하지 않으려 B34 뒤에 둔다(b26pre card U3). backfill card는 b26pre의 핑거증가 반환 경로 test 위에서 판정하도록 b26pre 뒤에 둔다.

## 부록 -- 재현

`_drafts/b26_reconcile/`: `setup103.py`(사본) → `mk_b1.py`(b1) → `b26v4_classify.py v4`(301) → `reconcile_run.py baseline|proto|existing`(v4 50 생존·세 열) → `reconcile_run2.py trace_v4`(trace 2 죽음) →
`plan_measure.py <A|B> classify|baseline|proto|existing`(시나리오 A 4·B 7) → `combine.py`·`combine_plan.py`·`survivor_table.py`(표). 등가·구별 입력 실험 `exp_trace.py`·`exp_backfill*.py`.
pytest는 `APPDATA=C:/Users/HSLEE/AppData/Roaming`(사용자 site-packages의 numpy) 필요 -- `timeout` 명령은 Windows 환경변수를 넘기지 않아 쓰지 않는다.
