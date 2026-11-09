# 검토 -- B37a spec card v4s(#47) 변경분(독립 검토자, 작성자 아님)

대상: `_drafts/draft_b37a.spec.md`(v4s) vs `.pre-surv.md`(v4m)·`.pre-v3m.md`(r4), `_drafts/b37a_survivor_options.md`.
범위(루프 종료 조건): 새 계약 10, 계약 6 수용 추가 1줄, 'V3 계획' 수치. 그 밖은 보지 않았다.

## 판정: **PASS -- B 0 · S 0 · minor 3**(+ 참고 1)

생존 변이 5개는 card 문장만으로 쓴 내 구현·내 test에서 모두 죽었다. base·head의 결과도 card가 말한 증거 유형과 같다. 계약 10은 B55(충돌 의미)를 고정하지 않는다. minor는 모두 문구 수준이라 착수를 막지 않는다.

## 독립 재측정(scratch `C:/g199`, TMP·TEMP도 그 아래. 작성자 스크립트 `make_head.py`·`contracts.py`·`mkmut.py`는 쓰지 않음)

* base = `git clone --no-checkout` → `git archive dd60db6`(= `gate/master` = HEAD). 저장소 `git status --porcelain` md5는 시작과 끝이 같다(`dcc7b56b…`). 측정 뒤 `C:/g199`를 지웠다.
* head 시제품은 card 범위 1~4 문장에서 내가 직접 썼다(`mk_head.py` -- scratch, 삭제됨). B26-1·CC-4a 전이라 레일은 raw `supply_nets`, 거부는 `ValueError`로 대신했다.
  * 접근자 `port_declaration`/`PortDeclaration`과 role 6어휘 표
  * `load_topology`: 진입 파일 접근자 1회, 연결 파일 `ports` 일치 검사, `all_passive`(진입 + 연결), 존재·레일 검사, E1·E2에 `inputs`/`outputs`, `meta["ports"]`
  * `resolve_stack_layout(*, ports)` 경로 3, `_build_theta_evaluator`가 `ports=meta["ports"]` 전달
  * `input_referred_offset_pairs`: `meta["ports"].inputs`, 입력 0 + offset 쌍 거부. 캐시 raw `ports` 삭제
  * 확인: library 9/9 `meta["ports"]`가 card '`ports` 기대값' 9회로 값과 같다.
* **N2w 대상 수**(`base/tools/gates/mutate_changed`의 `changed_defs`·`mutants` + `_drafts/v3scope_kit/scope_proto.py` `select`, `PARAM_POS=kind_index`·`NEW_COMPOUND_NAMES=subtree` assert):

  | def | card(N2b/N2w) | 내 시제품 B(`all_passive` 초기화를 `all_ideal_sources` 뒤에 둠) | 내 시제품 A(`all_netlist` 앞에 둠) |
  |---|---|---|---|
  | `port_declaration` | 27/27 | 29/29 | 29/29 |
  | `load_topology` | 27/39 | 26/38 | 26/44 |
  | `input_referred_offset_pairs` | 16/16 | 17/17 | 17/17 |
  | `_load_full_topology_cached` | 4/4 | 4/4 | 4/4 |
  | `resolve_stack_layout` | 4/4 | 4/4 | 4/4 |
  | `_build_theta_evaluator` | 3/4 | 3/4 | 3/4 |
  | 합 | 81/**94** | 83/**96** | 83/**102** |

  * 94는 재현되지 않았다. 차이는 모두 **구현 모양**에서 온다.
  * 넓힌 T6 몫은 시제품 B에서 card 목록과 **정확히 같은 13개**다: `linked =`·`_name_verdict`·`_comp`·`_comp_stage_devices`·`for _name…`·`for _p…`, 연결 파일 루프 병합 6개, `_build_theta_evaluator` `return`.
  * N2b 몫(접근자·offset 함수의 문장 모양)만 +2다.
  * 시제품 A는 `data.get(…)`을 읽는 새 문장이 앞에 오므로 기존 초기화 문장 7개(`all_netlist =` ~ `linked =`)를 더 끌어들인다. 그 7개 `stmt_delete`는 내 계약 10·6 test로 7/7 죽었다(`NameError`). 그래서 생존 기대 0은 모양에 흔들리지 않는다.
* **생존 5개**(시제품 B, 연결 파일 루프 = `body[13]`, 다섯 병합 문장 = `body[13].body[4]`~`[8]` -- card 경로와 같다. 변이마다 그 문장이 `Pass`인지 assert):
  * test는 내가 card 문장만으로 썼다(`test_rev_b37a_c10.py` -- scratch, 삭제됨). 계약 10 (i)~(vi)와 계약 6 수용 추가 1건이다.
  * 기대값은 card의 두 JSON 리터럴과 계약 1 role 표에서만 만들었다. 포함·다중집합·`==`를 쓰고 엔진 출력은 쓰지 않았다. 계약 6 추가의 `(("inn","inp","vsrc"),("out",))`도 선언 + role 표로 다시 만든 값과 같다.

  | 판 | 계약 10 | 계약 6 추가 |
  |---|---|---|
  | base | **PASS** | FAIL `KeyError: 'ports'`(허용 밖, red 아님) |
  | head | PASS | PASS |
  | `body[4]` `all_matching_pairs.extend` 삭제 | FAIL `AssertionError`(연결 파일 `ratio` 쌍 없음) | PASS |
  | `body[5]` `all_dispositions.extend` 삭제 | FAIL `AssertionError`(다중집합 다름) | PASS |
  | `body[6]` `all_device_roles.update` 삭제 | FAIL `AssertionError`(`M3 vertical_stack_id None`) | PASS |
  | `body[7]` `…sections_structured.update` 삭제 | FAIL `AssertionError`(`load` 블록 없음) | PASS |
  | `body[8]` `all_ideal_sources.extend` 삭제 | FAIL `AssertionError`(`Vs` 없음) | FAIL `ValueError: ports: netlist에 없는 넷 ['vsrc'](DEC-62)` |

  5/5 죽었다. card '작성 전 실측' 11·`b37a_survivor_options.md` §1과 변이·실패 원인이 모두 같다(모양이 다른 독립 구현에서 같은 결과).
* card 사실 확인:
  * `test_ic3::test_linked_topology_files_merge_and_collision`의 `part_b`는 `schema_version`·`symmetry.matching_pairs: []`·`netlist`·`linked_topology_files`만 가진다. card의 '비-netlist 필드를 모두 진입 파일에 둔다'는 맞다.
  * 계약 6 수용 개수: 7 + 존재 범위 4 = 11. '원칙의 계약화'의 '수용 11'과 같다.
  * V3 표 합: 83 + 4 + 2 + 1 + 4 = 94.

## 질문별 답

1. **계약 10 기대값이 선언에서만 오는가** -- 그렇다. (i)~(vi) 모두 두 리터럴의 합(포함·다중집합·`==`)이다. (iv)는 선언 (소자, 필드, 값)만 보고, (ii)는 자동 채움 `offset` 덧붙임을 포함 관계로 허용한다. 피검 출력이나 측정값은 쓰지 않는다.
2. **B55(충돌 시 덮어쓰기)를 굳히지 않는가** -- 굳히지 않는다.
   * 다섯 병합 경로(쌍·disposition·`device_roles` 소자·섹션 블록 키·이상원) 모두 입력이 겹치지 않는다.
   * B55의 '충돌 거부' 수정이나 중복 제거 수정이 들어와도 계약 10 입력은 그대로 통과한다.
   * '고정하지 않는 것' 문단과 survivor options §2(Q-S1 권장 A = 백로그 B55)는 `backlog_additions.md` B55 문장과 일치한다. 덮어쓰기 사실(dict `update` 단위, `extend` 중복)은 base 코드 8566~8571행 읽기로도 확인했다.
3. **red-green card 안의 보존 계약(base PASS)이 허용되는가** -- 허용된다(선례 있음). 다만 문구 보강을 권한다(m2).
   * 계획 N4.2 V2(838행) 문장은 '새·바뀐 test가 base에서 assertion FAIL'이다.
   * 그러나 gate에 있는 red-green 판정 기록 `20260923-v4-decision-exempt`가 "계약 3·4는 base에서도 PASS라 red가 아니라 회귀 대조다"로 기록하고 통과했다. merge gate 코드도 test마다 red를 요구하지 않는다(`_RedCapture`는 실패만 기록하고, V2는 auditor 판정이다).
   * 이 card는 계약 9(보존)·계약 5(허용 밖 실패)를 이미 나눠 적는 구조다. 계약 10의 '보존 계약 -- red 근거 없음' 표기도 그 구조 안에 맞는다.
4. **D-19** -- 사실상 MOD2로 적혀 있다(43행 '접근자는 `ports`를 읽는 MOD2 쪽'). 모듈 확정은 card 커밋 때로 미룬다(43·77·378행 '`rail_declaration`이 있는 모듈'). 승인 기록 초안 `approval_20260930-30-module-split-design.md` 73행("B37a의 `port_declaration`도 같은 결정을 따라 그 card 커밋 때 적는다")과 모순되지 않는다. 다만 인용이 낡았다(m3).

## minor

* **m1 (V3 계획 1 -- 구현 모양 단서가 빠졌다).**
  * r4 판 406행에는 "변이 수는 접근자·검사 문장의 구현 모양에 따라 달라진다(모의 구현 기준 근삿값)"가 있었다. v4m에서 표를 바꾸며 이 문장이 빠졌다(현재 card에 '구현 모양' 0건).
  * '측정과 추론의 경계'는 착수 base의 차이만 적는다.
  * 내 독립 시제품은 96·102다. 넓힌 T6 13개는 같고, `all_passive` 위치에 따라 +6이 된다.
  * 오케스트레이터나 auditor가 94를 기대값처럼 대조하면 거짓 불일치가 난다.
  * 고침: 1행 복원 -- "94는 작성자 모의 구현의 값이다. code-author의 문장 모양(특히 `data.get(…)`을 읽는 새 문장의 위치)에 따라 N2b·넓힌 T6 몫이 달라진다(독립 시제품 96/102). 판정은 실제 도구 `targets_by_def`로 하고 기대는 '생존 0'이다." 생존 0은 두 모양 모두에서 확인했다.
* **m2 (판정 유형 근거 -- 계약 10의 선례와 판정 기록 칸).**
  * 계약 10 머리의 '(P10b·b26pre 선례)'는 '면제 대신 test 보강'의 선례다. 'red-green card의 base-green 새 test'의 선례는 아니다.
  * 고침 1: 403행에 gate 선례 `20260923-v4-decision-exempt`(계약 3·4 base PASS = 회귀 대조)를 인용한다.
  * 고침 2: 계약 5처럼 auditor가 계약 10 test id를 `red.test_ids` 밖 '회귀 대조(보존)'로 V2 basis에 따로 적는다고 한 줄 더한다.
  * 이유: V2 문장을 글자대로 읽는 auditor가 'red 부재'로 오판하지 않게 하려는 것이다.
* **m3 (D-19 인용).**
  * 43행 근거가 'Phase 3 v4 A-3 · 준비 자료 §4.1'이다. 2026-10-02 답 D-19 (가)(`rail_declaration` = MOD2 `topology_authoring`, 승인 기록 `20260930-30-module-split-design`, design 30 v8.5 §6.4)로 바꾸고 모듈 이름 `topology_authoring`을 적기를 권한다.
  * 표 칸 확정은 지금처럼 card 커밋 때 해도 된다(승인 기록 문장과 같다).

## 참고(결함 아님)

* 계약 10 (iii)·(v)·(vi)는 포함이 아니라 `==`·다중집합 같음이다. 그래서 '병합 외에 그 meta 칸에 다른 항목이 더해지지 않음'도 함께 고정한다.
* 지금 문서화된 동작이고, 변이를 죽이는 데는 포함 관계로도 충분하다.
* 뒤 card가 그 칸에 자동 항목을 더하면 기대값 변경(V5)이 된다. 그대로 둬도 된다.
