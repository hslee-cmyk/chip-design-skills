# 독립 검증: `draft_p3_t1.spec.md`(20261006-p3-test-relocate) + `m10_t1_open_items.md` T1 항목

검증 2026-10-06, 검증자 = 작성자 아님. 기준: gate `master` `6c724de`(card가 적은 `2183f2e`와 차이는 b26pre spec·interface card 문서 2개뿐 -- `skills`·`tools` 변경 0), design 30 v8.5 §7.1·§8·§8.1·§9.2, 계획 N3.10·N3.11·N3.12.3(689행 test-only 열거에 'Phase 3 T0·T1' 이미 있음), design 05 §10 V5·§12 'V5 승인 운반', 00-common §8.2 diff 해시.
스크래치 `C:/g355`(TMP/TEMP 그 아래, `clone -c core.autocrlf=false --no-hardlinks --no-local`, origin 제거, hooksPath 빈 디렉터리). 실제 저장소는 읽기만 했다. 끝에 스크래치를 지웠다.
절차 위반 자진 신고: 읽기 전용 명령 2회에서 `cd`를 썼다(스크래치 `tmp`, 실제 저장소 `git ls-tree`/`cat-file -e` 루프 -- 쓰기 없음, 결과 영향 없음).
**`p3kit_m10_t1/`은 내 매핑 측정(아래 2)을 마친 뒤에 열었다.** 그 전에 쓴 키트는 `p3kit_m2_m9/`(FU·T0W1 대역, `move_plan_sim`, `regen_registry`, `gen226`, `r1m/chain_lean.py`)과 `g1_kit/install_proto.py`(md5 `733d173f…`)뿐이다.

## 판정: B 0 · S 3 · minor 9

card의 뼈대(규칙 '닫힘의 N3.10 최댓값', PT3·셔플·V4·V5 수치)는 독립 사슬에서 그대로 재현됐다. 고칠 것은 매핑 규칙의 메서드 조항 하나(S-1, 수치 2개가 바뀜), V5 운반 절차(S-2), auditor 거부 판정 문언(S-3)이다.

## 1. 사슬(독립 재구성)

`6c724de` → FU 대역 `9256f88` → T0 W-1 대역 `4814cd9`(3파일 1·3·1 편집) → G1 시제품(`installed 4`) `669e017` → D0a 대역 `7b6b66b` → D0b 재생성(`one 354·multi 0·nested 7·nounit 18`, `보류(Phase 4)`) = M1 base `172fd7e`(plan exit 0)
→ `chain_lean.py` M1~M9 `8e752bf`…`7611ed2`. 8 card 모두 plan 일곱 목록 0, `check` 발견 0, 단위 8·18·82·104·21·11·30·16(작성자 사슬과 같음).
M10은 만들지 않았다(모의 M10 생성기가 작성자 키트 안에 있다). 대신 매핑이 M10에 기대지 않음을 확인했다: 작성자 `t1_map.json`(rev `a83a46b` = 처리부까지 옮긴 M10 대안)과 내 M9 트리 매핑이 **212개 test 전부 같은 k**(차이 0).
→ T1 base로 M9 tip `7611ed2`를 썼다. PT3 총수가 1124가 아니라 1105인 것은 M10 진입점 test 시제품 19개가 없어서다(관계 '병합본 = base를 매핑으로 옮긴 집합'은 같다).

## 2. 매핑(항목 (1)·(2)) -- 내 구현 `my_map.py`

규칙을 card 문언대로 따로 구현했다: R-DEF(`A/*.py` 하위 제외 + `workspaces/run_harness.py` 최상위 def·class·대입 바인딩 파일이 정확히 하나), 메서드 조항, `tests/tools` 경유 조항, 닫힘 = 본문 + 요청 fixture + 부르는 모듈 도우미(전이).
'이름으로 읽는다'를 두 가지로 읽었다 -- LIT(모든 `Name` Load) / SCOPE(함수 안 지역 바인딩을 뺀 자유 이름). **두 읽기 결과가 212개 모두 같다.** 모호(2파일 이상 바인딩) 이름 0, MOD 밖 엔진 정의(ACF·`run_harness`)를 읽는 test 0.

| | MOD1 | MOD3 | MOD4 | MOD5 | MOD6 | MOD7 | MOD8 | MOD9 | 계 |
|---|---|---|---|---|---|---|---|---|---|
| card 문언 그대로(내 측정) | 2 | 57 | 19 + 대체 1 = 20 | 15 | 1 | 77 | 32 | 8 | 212 |
| card '재현할 수치' | 2 | 57 | 20 | 15 | 1 | 77 | 32 | 8 | 212 |

옛 파일별도 같다(sizing 1:2·3:9·4:10·5:15·6:1·8:30, stick 3:48·7:77·8:2·9:4, DR 9:4, TL 4:9 + 엔진 이름 없음 1 `test_s011_tan`). fixture·도우미 57(쓰는 test 없는 것 0), 둘 이상 파일이 쓰는 fixture 2(`s086_state` 7·9, `s120_state` 3·9), 목적 파일 안 fixture 이름 충돌 1(`s065_state`, MOD3, sizing·stick), 목적 파일 안 test 이름 충돌 0 -- 전부 card와 같다.

엣지 케이스:
* **엔진 이름 없는 test**: 1개(`topology_library::test_s011_tan`, `math`만). 대체 규칙 'TL → MOD4'로 MOD4. (m-1 참고 -- 대체 규칙이 TL에만 정의돼 있다.)
* **fixture**: 닫힘에 전이로 들어간다(`_tst_grids` 같은 도우미도). 옛 파일 끝까지 def 뒤 모듈 문장 0이라 '머리 = def 앞 문장' 정의에 빈틈 없음(4파일 실측).
* **parametrize**: 함수 단위로 정하고 파라미터 id는 따라간다 -- 옮긴 수집 id 213 = 함수 212 중 하나가 파라미터 2개.
* **`s065_state` 충돌**: 뒤 옛 파일(stick) 쪽을 `s065_state__stick_diagram`으로. 내 AST 대조에서 그 토큰을 되돌리면 base와 같다(바뀐 것은 def 이름과 사용처의 매개변수·본문 참조뿐).
* **메서드 조항**: 결정에 쓰인 test 2개 -- `test_s056_noise_1f_density`(`toy_lut.noise_1f_density` → MOD1, 맞음)와 **`test_s155_propose_device_roles_gap_fill`(`.add` → MOD7, 틀림)**. S-1.

### S-1 메서드 조항이 내장 `set.add`를 엔진 메서드로 읽는다 -- s155가 근거 없이 MOD7로 간다

`test_s155_propose_device_roles_gap_fill` 본문의 `_t53_declared_keys.add(frozenset(...))`는 지역 `set()`의 메서드다. card 조항('그 이름의 최상위 정의가 없고 메서드를 정의한 파일이 하나')은 수신자를 보지 않아서, `stick_diagram.py:3209` 어떤 클래스의 `def add(self, name, ok, detail="")`와 맞춘다.
메서드 조항을 빼면 이 test의 닫힘 최댓값은 3(`load_topology`·`propose_device_roles_gap_fill`)이다. 작성자 `t1_map.json`도 같다(`R1`(슬러그) 3, `R2c` 7) -- 작성자 수치 'MOD3 57·MOD7 77'에 이 오배정이 들어 있다.
매핑 표의 '근거(닫힘 이름과 정의 파일)'에 `.add → stick_diagram`이 사실처럼 박힌다. 엔진 클래스에 `get`·`update`·`run`·`add` 같은 흔한 메서드 이름이 생기면 같은 일이 되풀이된다(일반화 원칙 위반).
* **고칠 방향(원칙 기본안)**: 메서드 조항은 **대체 조항으로만** 쓴다 -- 닫힘이 최상위 엔진 정의를 하나도 읽지 않을 때만 적용. 근거는 card 자신의 근거 문장이다: 매핑 규칙은 'import는 작은 번호로만'의 test 판이다. 그런데 메서드 호출은 test 파일에 import 줄을 만들지 않는다(수신 객체는 fixture가 준다). 그래서 메서드 이름은 계층 판정의 입력이 아니고, 배정할 다른 근거가 없을 때만 쓰는 근거다.
* 결과(실측): s056 → MOD1(그대로), s155 → MOD3. **MOD3 58·MOD7 76**, 나머지 같음. 공유 fixture·이름 충돌·쓰지 않는 fixture는 그대로(공유 2, 충돌 1, 미사용 0).
  변형 트리(`gen_t1` + 바꾼 매핑)에서 `test_mod3`·`test_mod7` 두 파일 `134 passed`. V4 FAIL 대상 3 test(MOD8)는 영향 없음 → T1-2 질문 문안의 파일 이름도 그대로다.
* card 고칠 곳: '의도' 매핑 규칙 문장, '재현할 수치' 매핑 줄(옛 파일별 stick → 3:49·7:76), T1-1 근거(슬러그 대비 11개 수 -- s155가 '다른 것'에서 빠질 수 있다. 다시 셀 것). auditor가 생성기를 다시 돌려 같은지 보는 계약 2 구조는 그대로 맞다.

## 3. 생성 결과 대조(작성자 생성기 `gen_t1.py`를 내 M9 tip에 적용 → head `750205e`)

diff 14파일 +3284 −3139(card와 같음). 아래는 내 도구로 쟀다.
* **계약 2·3**(`my_verify.py`): 새 파일 9개. 옮긴 def 마다 `ast.dump`가 base 원본과 같다(불일치 0, `s065_state__stick_diagram` 토큰 예외만). test 212개가 모두 내 매핑의 k 파일에 하나씩 있다.
* **계약 3 머리 `is`**(`my_hdr.py`, 문장마다 따로 실행): 두 문장 이상이 묶는 이름 21개(6파일), 서로 다른 객체 0.
* **계약 6·7**: `_LEGACY_SCRIPTS` 8줄. 추적 `.py`(`.ai/verification` 제외)에 `test_selftest_[a-z_]+\.py::` 꼴 0. `test_selftest` 언급 11줄(ts3 주석 27·74(head 행) + 새 파일 docstring 9) 모두 `::` 없음.
* **PT3**(`pt3.sh`, `--gmid-phase=3`, junit): base `3 failed, 1087 passed, 15 xfailed`, head 같음. base id를 매핑으로 옮긴 집합 = head 집합(1105 = 1105, 한쪽에만 있는 id 0), id별 결과 차이 0. 실패 3 = T0 A군(대역 사슬에 T0 R-DEF 없음, 작성자와 같다).
* **셔플** `U/` `--shuffle-seed=1..5`: 다섯 번 모두 `239 passed, 3 xfailed`, exit 0(각 3분 40초~4분).
* **V5**(gate `6c724de` `weakening_diff.py`): FAIL, 발견 215 = assert 삭제 212(sizing 67·stick 131·DR 4·TL 10) + 리터럴 변경 3. `diff_paths` 7, `diff_hash` `aad798728d13…0131` -- **작성자 모의 해시와 같다**(4절).
* **V4**(gate `test_lint.py` + gate `interface_card.py`로 이 초안에서 만든 interface card, 기존 함수 6): FAIL, 규칙 (1) 4줄(s009 2·s052·s054, 전부 `test_mod8_sizing_layout_convergence.py`), UNJUDGED 182, NO-SUBJECT 478. 그 밖 FAIL 0.
  새 id 셋을 target으로 한 decision 기록 시제품을 head에 두면 **PASS**(`exempt` 4, FAIL 0). `merge_gate.py parse-approval` 통과(`target_list` 3).

## 4. V5 -- 리터럴 변경 3건과 승인 운반(항목 (3))

리터럴 변경 3건(모두 `<module>` 단위, `weakening_diff`가 모듈 docstring은 빼지 않는다 -- def·class docstring만 뺀다):
1. `contracts/test_ts3_no_print_verdicts.py` `_LEGACY_SCRIPTS` 튜플(4 → 8). **필요하다**: 옛 4파일이 지워지므로 그대로 두면 `test_target_set_includes_legacy_scripts`가 FAIL한다(R-6).
2. `unit/test_probe_revalidation_scope.py` 모듈 docstring의 `unit/test_selftest_sizing_recipe.py::test_s009_…` → `unit/test_mod8_…::test_s009_…`.
3. `unit/test_probe_role_L_derivation.py` 모듈 docstring의 `…::test_s024_section` → `unit/test_mod8_…::test_s024_section`.
2·3은 판정에 영향이 없다(docstring). 필요성은 '죽은 참조를 남기지 않는다'(T1-3)는 선택이다. 대가는 V5 경로 2개와 그 운반이다. 이 선택은 타당하다고 본다(F1 뒤로 미루면 더 오래 죽은 참조가 된다).

**해시가 T에 기대는가**: 아니다. 00-common §8.2 식은 경로별 (base blob, head blob)만 쓴다. 독립 사슬(커밋 id 전부 다름)에서 작성자와 **같은 해시**가 나온 것이 증거다. 대역 사슬의 7경로 blob이 바이트로 같기 때문이다.
그래서 2차 시도에서 필요한 것은 (i) ts3·docstring 2파일의 head blob이 1차와 같을 것, (ii) 옛 4파일이 head에 없을 것, (iii) 7경로의 base blob이 그대로일 것(1차와 2차 사이에 승인·운반 커밋만 들어가야 한다)이다.
새 `test_mod*.py`·`_selftest_shared.py`는 해시 경로 밖이다(추가 파일은 V5 '삭제'가 아니다). 그래서 2차 생성물이 1차와 바이트로 같을 필요는 없고, 계약 2·3이 판정한다.

### S-2 운반 절차가 삭제 경로를 다루지 않는다

design 05 §12 'V5 승인 운반' (2)는 **발견 경로마다** `git cat-file blob <T>:<path>`로 `.blob`을 만든다. 7경로 중 4개(옛 4파일)는 T에서 지워졌다. 그래서 명령이 실패하고, `paths.tsv`에 넣을 blob id도 없다.
card는 계약 10에서 '승인을 diff 해시로'라고만 적고 운반 절차는 적지 않았다(T0와 같은 2회 시도가 필요하다 -- 승인은 head 트리에서 찾으므로 1차 test 커밋 뒤에만 만들 수 있다).
* 고칠 방향: 계약 10에 운반 범위를 적는다. `.blob`은 head에 있는 3경로(ts3·docstring 2)만 만든다. `paths.tsv`에는 삭제 4경로를 `-`로 적는다(head blob `-`는 2차 test-author가 옛 4파일을 지우면 재현된다). 승인 기록 `diff_path`는 7경로 전부다. 2차 시도에서 test-author는 3경로를 `cp`, 4경로를 삭제, 새 파일을 매핑 표로 다시 만든다. auditor는 1차 해시 = 2차 해시를 확인한다.
  design 05 §12 문언 자체의 삭제 경로 공백은 문서 정정 후보다(기준 변경 아님).

## 5. V4 면제(항목 (4)·(5))

* **면제가 풀리는 것은 사실**: `20260923-c9-v4-exempt`(s052·s054)는 "이름·경로가 바뀐 뒤의 같은 판정(그때는 면제가 저절로 풀린다)"고 적었다. T0 기록 초안(s009)도 같다. 특히 T0 질문의 선택지 1 설명이 사용자에게 **"test 이름·경로가 바뀌면 풀립니다"**를 그대로 보였다.
  → 다시 묻는 것은 기본안이 아니라 사용자 답의 조건 그대로다. T1-2를 사용자 질문으로 분류한 것이 맞다.
* **기본안 (가) 기록 모양**: decision 하나, target 3 id(`::`)를 쉼표로, 범위 = 규칙 (1)만. 시제품으로 V4 PASS·parse 통과를 확인했다. 대안 (나)(피검 축소)를 기본안에서 뺀 이유(판정 범위 축소)도 맞다.
* **시점**: V4가 head 트리 `.ai/approvals`를 읽는다. 그래서 test worktree 생성 **전** master 커밋이 맞다(T0 선례). V5 승인(1차 test 커밋 뒤)과 따로 묻는 것도 맞다.
* **(5) 계약이 V4 위반을 강요하는가**: 아니다. 측정한 FAIL은 이미 면제받았던 3 test의 규칙 (1) 4줄뿐이다. 규칙 (2)~(5) FAIL 0, `_selftest_shared.py`·ts3·docstring 2파일에서도 FAIL 0.
  계약 11의 피검 합집합은 s009를 판정 안에 두는 선택이다(판정 범위를 좁히지 않는다). 이것이 FAIL 1 test를 '만들지만' 판정 범위 유지 원칙의 결과이고, 면제 질문으로 드러냈다. 문제 없음.

## 6. 양식(항목 (6), gate `6c724de` `git archive` 사본)

* `role_paths.parse_spec_card(text, expect_id="20261006-p3-test-relocate")`: 예외 없음, phase 3·test-only·gate_change no·approval 3(형식만 검사 -- 승인 존재는 V5·V4가 따로 본다), 절 11.
* `interface_card.py <초안> --root <T1 head 사본>`: exit 0, 기존 함수 6(`sizing_layout_convergence.optimize_full_circuit_budget`·`_build_theta_evaluator`, `gmid_sizing_engine.size_transistor`·`width_from_id_density`·`check_quasi_static`, `circuit_state_graph.load_topology`), 신규 시그니처 표 빈 것.

## 7. S-3 거부 판정 R-4·계약 2 문언이 정상 병합본을 거부한다

계약 4의 '정의 하나'를 R-4는 "같은 이름 def가 두 파일"로 판정한다. 그런데 옛 파일 사이 같은 이름 fixture 4개 중 3개(`s040_state` MOD7·8, `s051_state` MOD7·8, `s063_state` MOD5·7)는 **출처가 다른 별개 fixture**인데 정상 배치에서 두 목적 파일에 나뉜다.
같은 이름 test 12쌍(`test_s030_section` 등)도 두 파일에 나뉜다(실측). 문언대로 구현한 auditor 판정기는 올바른 병합본을 거부한다.
계약 2의 "test 함수 이름은 … base 4파일 안팎 어디에도 이름 겹침 없이 그대로"도 사실과 다르다(같은 이름 12쌍).
* 고칠 방향: R-4 = "**같은 출처 (옛 파일, 이름)**의 def가 두 파일 이상". 계약 2 = "목적 파일 **안**에서 이름 충돌 0(test 0, fixture는 계약 5의 1건)". 실측값: 출처 같은 def 중복 0.

## minor

* m-1 대체 규칙('옛 파일의 엔진 모듈 단위가 모두 간 MOD')은 TL(→ MOD4)에서만 하나로 정해진다. SR·SD·DR 출신 test가 엔진 이름을 안 읽으면 정해지지 않는다(SR → 여러 MOD). 이번 base에서 해당 0이지만 '그런 test가 나오면 멈춘다'를 한 줄 넣는다. S-1 고친 판에서는 메서드 대체 조항이 그 앞에 온다(순서를 적는다).
* m-2 계약 5 "사용처 매개변수만 같이 바꾼다"는 그 매개변수의 본문 참조(`s065_state.<속성>`)도 바뀌어야 성립한다. "그 fixture 이름 **토큰**(def 이름·사용처 매개변수와 본문 참조)"으로 R-10 문언과 맞춘다.
* m-3 계약 11 "`load_topology` 등" -- `interface_card.py`는 card 본문의 backtick 심볼로 피검을 정한다. '등'이 아니라 실제 T0 병합 판정 기록의 interface 함수 목록을 커밋 직전에 정확히 적는다(작성 전 실측 11에 항목 추가).
* m-4 ts3 주석 27~28행("이 4개 파일에 있다")·73~74행(head; "unit/test_selftest_<m>.py 4개")은 계약 6('다른 줄 바꾸지 않는다') 때문에 낡은 서술로 남는다. 주석은 AST·V5 밖이다. 그래서 주석 갱신을 허용하거나 '남는다'를 명시한다.
* m-5 계약 7의 "ts3 27·74행"은 head 행 번호다. base(gate)는 27·68행이다(open items 표기). 어느 판의 행인지 적는다.
* m-6 계약 11 V4 UNJUDGED 182의 basis 문장이 없다. T0 선례처럼 "본문 `ast.dump` = base(계약 3) -- base에서 같은 식"을 basis로 적는다고 명시한다.
* m-7 T1-2 질문 문안 "본문은 한 글자도 바뀌지 않습니다" -- T1 전체에서는 `s065_state` 토큰이 바뀐다. 문맥상 세 test 이야기지만 "이 세 test의 본문은"으로 좁힌다.
* m-8 '작성 전 실측'의 T1 모의 base `b6d4eb2`는 기본안 M10(`1306cfc`)이 아니라 처리부까지 옮긴 대안 위다. 매핑에는 영향이 없다(내 M9 트리와 212개 같음). 다만 사슬 문장에 그렇다고 적어 둔다.
* m-9 card 머리 'gate master 2183f2e 판'은 지금 `6c724de`다(문서 2개 차이, 영향 0). 커밋 직전 재확인 항목 (iv)가 덮는다.

## 재현 방법(스크래치는 지웠다)

`build355.sh`(build226.sh와 같은 단계, REV `6c724de`, qtok 단계 없음) → `chain_lean.py gmid_lut,…,instance_report_builder` → `my_map.py`(내 매핑) → (그 뒤에 연) `gen_t1.py <M9 tip> t1_map.json` → `my_verify.py`·`my_hdr.py`·`junit_cmp.py` → gate `weakening_diff.py`·`interface_card.py`·`test_lint.py`(`PYTHONPATH` = gate 사본) → 셔플 `--shuffle-seed=1..5`.
스크립트는 스크래치에만 있었다(역할 산출물 아님). 필요하면 다시 만든다.
