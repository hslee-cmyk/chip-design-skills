# G1 입력 사전 재측정 -- gate `master` `6c724de` (2026-10-06, 측정 전용, spec·승인 초안 무수정)

격리 복제본 `C:/g330`(b·p 둘 다 `6c724de`, `-c core.autocrlf=false`, TMP/TEMP·HOME/APPDATA/USERPROFILE export, **측정 뒤 삭제 확인**). 실제 저장소는 읽기만.
키트 산출물: `g1_kit/out/{a32_base,a32_proto,noop_base,noop_proto}_6c724de.*`, `g7_facts_6c724de.json`, `m9_6c724de.json(.partial.jsonl)`, `order_sim_6c724de.json(.partial.jsonl)`.
비교 기준: spec 초안 '작성 전 실측'의 `a17b8bd` 문단(H·W·M·공격 32)과 `dafe5cf` 문단(이름 grep·호출·무동작).

## 0. 입력 차이 `dafe5cf..6c724de`
* `tools/` 차이 **0**(`git diff --stat` 빈 출력) -- 게이트 도구·redteam·`gate_config.json`·`merge_gate.py` 불변. `install_proto.py`(`a17b8bd` 앵커) `installed 4`, parse ok.
* 엔진: B34 `sizing_recipe.py` +2/−3(`resolve_stack_layout` 근처 docstring/주석), `stick_diagram.py` +28/−42(`_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction` 본문 + 여러 def docstring).
* test: `tests/contracts/test_b34_grammar_explicit.py` 신규(386줄) -- 게이트 import 없음(계약 7 grep `mutate_changed|reachability|source_lint` 여전히 0건).
* 문서: 계획서(N3.10 MOD1 `_QUERY_CACHE_MAX` 토큰 [D-11] `29d2fc2` + N3.12.2 쓰기 경로 2행; 533행 이동 규칙 줄 위치·내용 그대로), design 30(§10 DoD 절차 정정), history, B34·b26pre spec/interface, 승인 3건, `.ai/context.md`, `.ai/verification/20260930-b34-grammar-explicit*`.

## 1. 결과 대조표

| 항목 | 기준(`a17b8bd`/`dafe5cf`) | `6c724de` | 원인 |
|---|---|---|---|
| (1) 도구 줄 번호 | `a17b8bd` 문단 값 | **같음**(mc 59·67/740·80·90·140/676·198/691·248·361·618·665·667·687·741, rch 97·196·224·227·230·231, sl 102·129·212·268, rt 689·695·699·710·1450, run_all 98) | tools 무변경 |
| (2) 새 이름 grep | tools 0 · design 30 33줄 | **같음** | design 30 변경은 §10 절차뿐 |
| (2) attacks `3x-` | 30·31·34·35, `32-*` 없음 | **같음** | -- |
| (5) 게이트 밖 호출 | 10줄·9 스크립트 | **같음**. B34 판정 기록 스크립트는 `mc.make_clone`·`mc.inventory`·`mc.inventory_gmid_keys`·`mc.test_nodeid`·`rch.read_tree`·`rch.build_graph`만 부름(`changed_defs`·`def_hash` 0). B34 spec card 368행의 `changed_defs`는 `.md` 서술 | -- |
| (8) 엔진 사실 `g7_facts` | star·global·multi·qual_dups 0, 클래스 41, 단위 402·def 473, future SR·SD·TL, 판정 기록 2건 옮긴 단위 0 | **JSON 값 전부 같음** | -- |
| (8) `__file__` 줄 | SD `1050`·`8962` | **SD `1049`·`8948`** | **B34**(`_import_analog_grammar` 안 −1, 그 뒤 −14 누적) |
| (8) future 줄 | SR 35·SD 32·TL 24 | 같음 | -- |
| H def / 변이 | 473 / **15,650** | 473 / **15,637**(SD 5,906 → **5,893**; SR 8,874·TL 683·DR 187 같음) | **B34**: 바뀐 4 def 변이 68 → 55(−13) -- B34 spec card 368행(base 12·11·9·36 = 68 → 12·8·6·29 = 55)와 정확히 일치 |
| H V6 / V7 미도달 | 859 / 109(면제 제외 108) | **같음** | -- |
| W | 402/402·473/473·거부 0, base V3 473·15,650 → 0·0, V6 1(859) → 0, V7 1(109) → 0(`moved` 473), `moved_defs` 1·`ast.parse` 20·`symtable` 4 | base V3 **473·15,637** → 0·0, 나머지 **전부 같음** | **B34**(H와 같은 −13) |
| M2(order sim raw) | base V3 변이 315 | **302**(−13), 시제품 잔여 4·81 같음 | **B34**(바뀐 SD def가 M2 배정) |
| M1·M4(order sim raw) | M1 단위 5·def 6·base V3 7·270·V6 5·V7 3 / M4 93·116·116·3,270·199·52 | M1 **8·22·23·610·35·6** / M4 **90·100·100·2,930·169·49**(둘 다 시제품 잔여 변화 없음, M4 시제품 0) | **B34 아님** -- 계획서 `29d2fc2`(MOD1 `_QUERY_CACHE_MAX`): order sim 규칙 A-4 240 → 239·A-1 60 → 61, `changed_from_rules` 73 → 72, `upward_n` 35 → 34, per_mod M1 7 → 10·M4 93 → 90 |
| M3·M5·M6·M8·M9 | `m9_a17b8bd` | 같음(시제품 잔여 M3 59·2,253, M9 10·229, M-4 거부 포함 -- raw 판 기존 값) | -- |
| 공격 32(93단계) | base 93 FAIL·exit 표 왼쪽 열 93/93·병합본과 다른 exit 22, 시제품 93/93 PASS | **단계별 exit·판정·관찰 93/93 같음**(base·시제품 각각 `a32_*_a17b8bd` 대조), base≠시제품 exit 22 | 합성 저장소, 엔진 무관(1,414초·1,679초) |
| 무동작(13케이스, `--only 34- --only 35-`) | 13 PASS·264단계, base=시제품 | **264단계 exit·판정·관찰 `noop_*_dafe5cf`와 전부 같음**, base=시제품 | -- |

## 2. B34로 영향받는 card 문장(spec 초안 `draft_p3_g1.spec.md`, 고치지 않았음)
1. **'작성 전 실측' 8**(349행): "`__file__` 2곳(`stick_diagram.py:1050`·`:8962`" → `6c724de`에서 **1049·8948**. (267·280행은 과거 측정 문단 -- 규약대로 새 재측정 문단에 새 값을 적으면 된다.)
2. **머리 수치 변이 15,650**: 13행('의도' 머리), 281·296·365행(재측정 문단·9의 W/H) -- `6c724de` 값 **15,637**(SD 5,893). W의 "base V3 473·15,650 → 0·0"도 15,637. def 473·V6 859·V7 109(108)는 그대로.
   * 문서 밖 참고(고치지 않음): design 30 5·237·251행도 15,650을 적는다(1382행 '15,677'은 더 이른 판 값). 승인 초안 `g1_kit/approval_…md`에는 15,650 없음.
   * design 30 492행 예측("B34 코드만으로 1073 이후 4줄 당김")과 실측(8962 → 8948, −14)이 다름 -- design 30 정정 대기열 후보(G1 범위 밖).
3. **'작성 전 실측' 9(M 모의)**: card의 M 수치는 `dd60db6` FU·dedup 판(별도 스크래치)이라 이번 raw m9와 직접 대응하지 않는다. raw 판 M 차이 중 B34 몫은 M2 base 변이 −13뿐이고 M1·M4 변화는 계획서 [D-11] 몫. G1이 인식할 모양·거부 원인(M-4)은 그대로 -- 계약·redteam 32 표 변경 불필요.
4. 바뀌지 않는 것: 계약 0~13 문언, 공격 32 단계 표·기대값, 1의 줄 번호, 2의 이름 충돌, 5의 호출 수(10줄·9 스크립트), 7(기존 계약 test 0건), 8의 star·global·multi·qualname·클래스·future.

## 3. 다음 착수 재측정(b26pre·backfill·B26-1·B33 병합 뒤) 메모
* b26pre는 test 전용이라 위 값 불변 예상. B26-1은 def +1·단위 +1 추정(design 30 §6.4) -- H·W·`__file__` 줄 다시. B33은 `reachability.py` 변경 -- (1) rch 줄, V7 미도달 109 → 약 39(키트 추정), 공격 32 base 열, `install_proto.py` rch 앵커 재확인 + `run_noop.sh --only 33-`.
* order sim `interest.refs_mod` 순서는 실행마다 바뀜(집합 순회) -- 대조 시 정렬해서 볼 것.
