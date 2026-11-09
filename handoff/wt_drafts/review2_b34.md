# review2 -- draft_b34.spec.md v2 (20260930-b34-grammar-explicit)

검토자: 독립 reviewer(작성자 아님, 1차 검토자 아님). 저장소 읽기 전용, HEAD = gate `master` `7535799`.
scratch `C:/g62`만 사용했다(`git archive HEAD` 사본 `base`와 모의 `head`, card '코드를 바꾸는 것' 표만 적용). 측정 뒤 삭제했다. 저장소 쓰기와 상태 변경 git은 없었다.
게이트 함수(`mutate_changed`·`reachability`·`interface_card`·`merge_gate`·`role_paths`)는 저장소 `tools/gates`에서 읽기 전용으로 import했다. `main`은 돌리지 않았다.
reviewer가 card 문장만 보고 직접 쓴 재현 test(계약 1~6·8, 49 케이스)를 사본에 넣어 쟀다.

## 요약 판정

| 등급 | # | 제목 |
|---|---|---|
| **blocking(card 밖, gate 전 필수)** | B1 | A2 승인 기록 초안(`draft_b26_u2_approval_question.md`)의 질문 원문·`scope`·'덮는 것'에 **B34가 없다**. 이대로 기록하면 card `approval`이 B34를 덮지 않는 기록을 가리킨다(1차 B1이 다시 생긴다) |
| should-fix | S1 | V3 인벤토리 부풀림. 새 test의 helper·중첩 def 이름이 그래프의 다른 이름과 겹치면 인벤토리가 15 → 236으로 커진다(실측). 'test 모양' 규칙에 이름 규칙이 없다 |
| should-fix | S2 | 계약 4·6은 V3 통과에 필수다(기존 test가 못 죽이는 변이 5개를 이 둘만 죽인다, 실측). card는 이 사실을 'V3 계획'에만 적었다. 계약 절에 "생략 불가"를 적을 것 |
| minor | M1 | 계약 3·4의 경로 비교. test 쪽 `Path(__file__).resolve()`와 SD의 `__file__`(sys.path 항목 기준, resolve 안 함)이 다를 수 있다. 양쪽을 `realpath`+`normcase`로 비교하도록 허용 문구를 넓힐 것 |
| minor | M2 | V3 55개는 작성자의 raise 모양(문장 하나)을 전제로 한다. code-author가 모듈마다 반복하거나 상수를 더하면 수가 바뀐다. 모양을 한 줄로 고정하거나 "추가 변이도 계약 1·3이 죽인다"는 조건을 적을 것 |
| minor | M3 | '새 test 포함 시 160·16·67·5'는 새 test 함수가 1개라는 전제다. 실제 값은 기존 값 + (그 def에 닿는 새 test 함수 수)다. 내 재현(test 7개)에서는 166·19·72·8이었다 |
| minor | M4 | 캐시: 문제 없음(아래 3). 다만 부재 상태에서 SR 진입점(`_load_full_topology_cached` 경유)을 부르지 않는다는 금지를 한 줄 적어 두면 test-author의 실수를 막는다 |

**1차 검토 blocking 3건은 card 본문에서 실제로 고쳐졌다**(B1은 승인 기록 쪽 조건이 남았다 -- 위 B1).
red 모양(전부 `builtins.Failed`), 캐시 오염 없음, 55 변이 전부 죽음(면제 0), interface card 진입점 14개 전부 생성, 사실 문장, 쓰기 경로는 card 서술과 일치한다.

---

## 1. 1차 검토 지적 처리 확인

| 1차 | 확인 |
|---|---|
| B1 approval | card는 `approval: 20260930-b26-before-phase3`이다. `parse_spec_card` 통과(`approval ['20260930-b26-before-phase3']`, 절 12개). `user_decisions.md` 13행 A2 원문 요지에 "③ B26-1·B34를 Phase 3 모듈 분할보다 먼저"가 있다. **그러나 기록 초안에는 B34가 없다 → B1(이 검토)** |
| B2 `==` 비교 | 계약 7·8에 정규화가 있다. `Match` 속성 이름이 계약 문장에 있다. reviewer 재현 계약 8(9회로 × 3모드 × 진입점 6개)이 head에서 27/27 통과했다. raw `==`는 `find_idiom_matches`에서 실패하므로 정규화가 실제로 필요하다 |
| B3 인벤토리 | 'test 모양' 규칙(본문 직접 호출, parametrize 이름 문자열·모듈 상수 + `getattr` 금지)이 있다. lambda 안 호출도 인벤토리에 잡힌다(`_refs`가 Lambda 몸체를 본다, 실측). **이름 충돌 규칙은 빠졌다 → S1** |
| S1~S5, M1~M3 | revision log 표대로 반영됐다. 사이트 14 줄(4087/4088~4109/4110/4111), SR 6509~6512, references 118~121·440~443, P9 interface 60행·spec 58행을 재확인했다 |

## 2. red 형태 (base, 실측)

* 실행: base 사본에서 00-common §8.1 red 수집 명령 그대로 돌렸다. `PYTHONPATH=<tools/gates>`, `-P -m pytest -c pytest_gate.ini --rootdir --confcutdir -p merge_gate --continue-on-collection-errors --gmid-phase=2 --gmid-strict=`, `GMID_RED_CAPTURE` 사용.
* 결과: base **18 failed / 31 passed**. 실패는 계약 1·3 9개와 계약 2 9개다. `GMID_RED_CAPTURE` 18줄은 **전부 `exc_type: builtins.Failed`**("silently returned")이다.
* `_pytest.outcomes.Failed.__module__ == "builtins"`이다(Python 3.14 실측). 그래서 `_ALWAYS_RED = ("builtins.AssertionError", "builtins.Failed")`에 든다. `pytest.raises`의 DID NOT RAISE도 같은 `Failed`다.
* card가 권고하는 `try/except ImportError/except Exception: pytest.fail/else: pytest.fail` 모양으로 썼다. base에서 비-ImportError가 나도 red가 단언형으로 남는다.
* head: **49 passed**, red 기록 0이다.
* 신규 시그니처 표가 비어 있다. 그래서 ImportError류 red는 인정되지 않는다. 그런데 base는 반환만 하므로 해당이 없다(정상).

## 3. 캐시 오염·순서 의존

* **SD**(`stick_diagram.py`)에는 `lru_cache`도, 모듈 수준 캐시도 없다(grep 0). `load_topology`는 매 호출 새로 계산한다.
* **SR** `_load_full_topology_cached`는 경로 키 dict 캐시이고 `load_topology`의 `meta`를 쥔다. 하지만 card 계약 1~8의 진입점은 전부 SD다. 그리고 head에서 부재는 `load_topology` 안에서 `ImportError`로 끝나 캐시에 들어가지 않는다(`cache[...] =`는 `load_topology` 반환 뒤에 온다).
  * 그래서 'grammar 없이 계산된 값'이 캐시에 남는 경로는 head에 없다.
  * base(red 실행)에서도 B34 test는 SR을 부르지 않으므로 다른 test로 새지 않는다.
  * 반대 방향의 위험도 있다. 앞선 test가 채운 SR 캐시는 부재를 가린다. 이것은 test-author가 SR 진입점을 부재 상태에서 부를 때만 생긴다 → M4(금지 한 줄 권고).
  * 캐시를 비울 공개 API는 필요 없다. card도 요구하지 않는다(맞다).
* `monkeypatch.setitem(sys.modules, …, None)` 복원은 원래 모듈 객체로 돌아간다. card가 "입력을 `load_topology`로 먼저 얻는다"를 강제하므로 netclass·idioms가 먼저 import되어 있다. conftest `--shuffle-seed`로 순서를 섞어도 같다.
* 계약 4의 `monkeypatch.setattr(sys, "path", 새 리스트)`도 복원 뒤 원래 리스트 객체로 돌아간다.
* `idioms`가 `from netclass import …`를 하지만 이미 import된 뒤라 영향이 없다.
* 계약 8(복원 뒤 = 부재 전) 27/27 통과가 실측 근거다.

## 4. V3 재현 (모의 head, 55개 전수)

* `changed_defs(base, head)` = 4개, `mutants` = **12·8·6·29 = 55**(card와 같다). 변이 id 목록은 card 경로 표기와 일치한다(`_import_analog_grammar:const±:body[3].body[0].value.args[0]` 등).
* 인벤토리(그래프 = HEAD 트리 + 모의 head SD): 새 test 없이 **159·15·66·4**(card와 같다).
* 판정: 변이마다 head 사본에 적용했다. 순서는 (1) reviewer B34 test 중 인벤토리에 든 것, (2) 거기서 안 죽으면 인벤토리 기존 test(`tools/gates/pytest_gate.ini`, `-x -q -p no:cacheprovider --gmid-phase=2 --gmid-strict=`)다.
  * **55/55 죽음.** B34 test로 39, 기존 test로 16(`audit_theta` 15, `find_stack_edges:stmt_delete:body[4]` 1)이다. card 표의 37 + 2(계약 4) = 39, 16/16과 일치한다.
* 표본 확인(계약 하나만 돌림):

| 변이 | 그 계약만 | 기존 인벤토리 test만 |
|---|---|---|
| `_import_analog_grammar:const+:body[3].body[0].value.args[0]`(`insert(1,…)`) | 계약 4 → 죽음 | (card 실측: 생존) |
| `_import_analog_grammar:const-:…`(`insert(-1,…)`) | 계약 4 → 죽음 | 같음 |
| `_import_analog_grammar:stmt_delete:body[3]`(`if … not in sys.path` 블록 삭제) | 계약 4 → 죽음 | -- |
| `audit_theta…:stmt_delete:body[3]`(3384 `if not devs` 삭제) | 계약 6 → 죽음 | **생존(rc 0)** |
| `audit_theta…:stmt_delete:body[3].body[0]`(3385 `return []` 삭제) | 계약 6 → 죽음 | **생존** |
| `audit_theta…:stmt_delete:body[6].body[5].orelse[0]`(3402 `others = …` 삭제) | 계약 6 → 죽음 | **생존** |

  → 기존 생존 3개는 계약 6만 죽인다. `insert` 상수 2개(와 if 블록 삭제)는 계약 4만 죽인다. **둘 중 하나라도 test에서 빠지면 V3 FAIL**(재시도 1~2 h) → S2.
* 기준 실행 주의: archive 사본에서는 기준 실행이 이력 의존 test 2개 때문에 실패한다. `test_ts6_probe_relocate::test_base_blob_reader_reads_the_base_tree`(card가 적은 것)과 **`test_ts6_probe_relocate::test_moved_tool_matches_base_except_path_lines`**(card에 없는 둘째)다. 이력 있는 격리 복제본에서는 해당이 없다. 그래도 card '작성 전 실측' 4의 "그 test만 빼고"는 둘로 고쳐 적는 것이 사실과 맞다(minor, M3에 묶음).

### S1 상세 -- 인벤토리 부풀림 (실측)

* reviewer 재현 test에 계약 8용 중첩 함수 `snap()`을 두었다. 그러자 인벤토리가 **237·236·234·234**가 됐다(기존 159·15·66·4).
* 원인은 `reachability.build_graph`의 이름 해석이다. 다른 모듈이 해석하지 못한 이름 참조를 `by_name`으로 전 그래프에 잇는다. 그래서 `probes/probe_classab_battery_headroom.py::vgs`가 부르는 `snap`이 새 test의 `test_c8_recovery.snap`으로 이어진다. 그 결과 `toy_lut`·`SemiEmpiricalGmIdLUT` 등을 거치는 거의 모든 test가 4 def에 '도달'한다.
* 이름을 `_b34_snapshot`으로 바꾸자 **166·19·72·8**(= 기존 + 새 test 함수 수)로 돌아왔다.
* 영향(정확성이 아니라 비용·위험):
  * 4 def의 기준 실행이 suite의 대부분(약 230 test)을 4번 돈다. 기준 실행 실패는 ERROR(B28)다. 그래서 무관한 test 하나의 불안정성이 이 card의 재시도가 된다.
  * 변이마다 `-x`라도 죽이는 test가 정렬 순서 뒤에 있으면 오래 걸린다.
* **고칠 것**('관찰 가능한 계약'의 'test 모양'에 한 줄): "새 test 파일의 모든 def(helper·중첩 함수 포함) 이름은 `_b34_` 접두 등으로 저장소 그래프에서 유일하게 짓는다(V3 정적 그래프는 이름만으로 잇는다 -- 흔한 이름 `snap`·`run`·`check`는 인벤토리를 suite 전체로 부풀린다)."
* auditor 확인 항목(순서 3 freeze 뒤): 인벤토리가 159·15·66·4 + (새 test 함수 수) 근처인지 본다.

## 5. interface card 생성

* `interface_card.build(card 사본, root=C:/g62/base)`와 `root=…/head`: 둘 다 **기존 함수 14개**다.
  * `load_topology`, `run_topology_pipeline`, `find_stack_edges`, `find_idiom_matches`, `find_differential_and_mirror_forks`, `suggest_vertical_stack_composites`, `find_differential_pair_candidates`, `find_verified_differential_and_mirror_relations`, `refine_differential_and_mirror_relations`, `audit_theta_root_direction`, `propose_theta_kcl_gap_fill`, `propose_device_roles_gap_fill`, `geometry_colocation_union`, `propose_vertical_stack_id_gap_fill`.
  * 계약 1~6이 부르는 진입점이 전부 들어 있다.
* `Transistor`는 dataclass라 생성기가 잡지 못한다. card 계약 머리의 생성자 서술(`stick_diagram.Transistor(name, kind, source=…, drain=…, gate=…)`)이 유일한 근거이고, 그것으로 충분했다(reviewer test가 그대로 썼다).
* 계약 6의 `` `audit_theta_root_direction(fx, {...}) == []` ``처럼 괄호 뒤에 `== …`가 붙은 백틱 토큰은 생성기 정규식에 안 잡힌다. 그래도 같은 함수가 계약 1에서 잡히므로 누락은 없다.
* docstring 첫 단락(base판)에 '부재 → None' 서술은 없다. test-author를 오도하지 않는다.

## 6. 사실·쓰기 경로

재확인(HEAD `7535799`):
* 사이트 1(1057~1058)·2(1073~1074)·3(1089~1090)·11(3381~3382)·11b(3387~3388)는 모의 head 편집 위치와 일치한다.
* 3400/3402 `others`는 A/A_signed 분기다(3402 = A_signed).
* SR 6509~6512 원문, `install.py` 27~29 `SKILLS`(analog-grammar 없음), references 118~121·440~443, 레지스트리 360행, P9 interface 60행·spec 58행, `test_s120_section` 2712~2718 docstring을 확인했다.
* SD에 module-level `importlib`·`sys` import가 없다. 그래서 `import sys`/`import importlib` 문장 삭제 변이는 NameError로 죽는다(위 55/55에 포함).
* 부재·`unavailable_reason`에 기대는 기존 test는 0개다(`setitem(sys.modules`·`unavailable_reason` grep, test 디렉터리 0건). V5 불필요는 맞다.
* `test_ic5`: '검사하지 않는 것:' 절 머리·`영역: dc, ac_struct` 줄을 남기고 analog-grammar 문장만 빼면 m_cascode 문장이 절 본문으로 남는다. 형식 규칙을 통과한다.
* 쓰기 경로: SD·SR 본문·docstring은 code-author(`A/*.py`), test는 test-author(`A/tests/contracts/test_b34_grammar_explicit.py`, 이름 충돌 없음), references는 오케스트레이터, `install.py`는 사용자다. N3.12.2와 맞다.
* minor: `test_s120_section` docstring "analog-grammar 미설치 상황(ImportError 경로)은 … self-test로 하기엔 위험 … 하지 않는다"는 B34 뒤 낡은 서술이 된다(B34 test가 sys.modules로 재현). 판정 불변이라 고치지 않는다는 card 결정은 받아들일 수 있다. 다만 백로그 한 줄을 권고한다.

## 7. approval 줄과 gate 순서 (B1)

* `.ai/approvals/20260930-b26-before-phase3.md`는 HEAD에 **없다**(`.ai/approvals/` 목록 확인).
* card 결정 1이 "그 기록은 이 card 커밋 전에 gate에 있어야 한다(오케스트레이터)"를 적었다. gate 순서 요건은 명시돼 있다.
* 기계 검사 시점: spec card 커밋 때 `role_paths`는 id 형식만 본다. 병합 판정 때 `merge_gate.rule6_dates_approvals`가 판정 기록 `approvals`의 각 id 파일이 존재하고 머리가 파싱되는지 본다. 그래서 기록 없이도 card 커밋 자체는 통과할 수 있다. card 문장의 "card 커밋 전"이 더 엄격하고 맞다.
* **결함:** 기록 초안 `_drafts/draft_b26_u2_approval_question.md`의 세 부분에 B34가 없다.
  * 질문 원문: 1~3항이 전부 B26-1이다.
  * `scope:` 줄: "… B26-1을 Phase 3 전에 착수 -- … spec card 20260930-b26-rail-accessor-set의 착수 조건"뿐이다.
  * '덮는 것': "B26-1 card를 Phase 2 진행 중에 병합"뿐이다.
* `decision_package.md` A2도 "B34 앞당김도 같은 기록으로 받을 수 있다"고만 적었다. 사용자 답(`user_decisions.md` 13행)은 ③에 B34를 넣은 요지다.
* 초안 그대로 `.ai/approvals/`에 쓰면 범위 설명이 B34의 동작 변경(부재 → `ImportError`)을 덮지 않는다. 1차 B1과 같은 결함이 기록 쪽에서 다시 생긴다.
* **고칠 것**(오케스트레이터, card 커밋 전):
  * 기록의 사용자 원문 절에 실제로 물은 질문(③ B26-1·B34)을 인용한다.
  * `scope:`와 '덮는 것'에 "B34(`20260930-b34-grammar-explicit`)를 Phase 2 진행 중에 병합 -- analog-grammar 부재 시 `ImportError`로 바뀌는 동작 변경과 def 4개의 부재 분기 삭제"를 더한다.
  * '덮지 않는 것'에 "B34의 V3 면제 없음"을 적는다.
  * card 결정 1에 "기록 범위에 B34가 명시돼 있어야 한다"를 한 구절 더한다.

## 8. 권고 수정 요약(card 편집량 작음)

1. (B1) 승인 기록 초안 범위에 B34 추가. card 결정 1에 범위 명시 조건을 한 구절 넣는다.
2. (S1) 'test 모양'에 def 이름 유일성 규칙. 'V3 계획'에 auditor 인벤토리 확인을 넣는다.
3. (S2) 계약 4·6 머리에 "V3 필수(기존 test가 못 죽이는 변이 `…const±…args[0]`·`audit_theta…body[3]`·`body[3].body[0]`·`body[6].body[5].orelse[0]`를 이 계약만 죽인다) -- 생략 불가".
4. (M1) 경로 비교를 `os.path.normcase(os.path.realpath(…))` 양쪽 허용으로 넓힌다.
5. (M2) raise 모양 고정(`except ImportError as e: raise ImportError(<'analog-grammar'·_ag_path 포함 메시지>) from e` 한 문장, 정수 상수 없음).
6. (M3) 인벤토리 '+1'을 '+새 test 함수 수'로 고친다. 이력 의존 기준 실행 실패 test를 2개로 적는다.
7. (M4) "부재 상태에서는 SD 진입점만 부른다(SR 캐시 경유 진입점 금지)" 한 줄.

## 산출물·정리

scratch `C:/g62`: base·head 사본, `mkhead.py`(모의 head), `count.py`(변이 수), `test_b34_grammar_explicit.py`(reviewer 재현 test), `run_red.py`(red 수집), `invcheck.py`(인벤토리·이름 충돌), `mut_run.py`(55 전수), `targeted.py`(계약별 표본), `ic.py`(interface card). 수치는 이 문서에 옮겨 적었다. 측정 뒤 `C:/g62`를 삭제했다.
