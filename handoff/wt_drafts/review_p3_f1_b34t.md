# review_p3_f1_b34t -- F1 card B34 test 반영 갱신 독립 검증 (2026-10-06)

대상: `_drafts/draft_p3_f1.spec.md`와 `draft_p3_f1.spec.md.pre-b34t.bak`의 차이(+15줄: 154·158~163·185~186·188·190·197~200·259·278~284행).
검증자는 작성자가 아니다. 모든 수치는 아래 sandbox에서 직접 쟀다. 실제 저장소는 읽기만 했다.

## 판정 요약

| 등급 | 건 | 요지 |
|---|---|---|
| **B** | B1 | `test_b34_grammar_explicit.py`의 **문자열 안 subprocess 스크립트**(`_B34_FRESH_SCRIPT`, F1 base 123행)가 SD 삭제 집합 이름 10개를 `stick_diagram.<이름>`으로 읽는다. 갱신본의 F1 변경 범위(별칭 import 2줄 + 모듈 식, "V5 발견 0")에는 이 문자열이 빠져 있다. 그대로 두면 F2 모의에서 c8이 **9 failed**(`AttributeError: module 'stick_diagram' has no attribute 'find_idiom_matches'`). 계약 5 (b) `E3B_AST` reader 0 검사도 이 자리를 보지 못한다. 이 문자열을 고치면 갱신본의 V5 수치(발견 10·`diff_paths` 6·`diff_hash` 같음)와 "B34 2단위 발견 0" 문장이 달라진다. |
| **S** | S1 | B34 2단위를 범위 설명 원문 인용과 auditor (바) (i) 대조만으로 묶는 것은 **기계 계층에서는 실제로 구멍**이다. c1 약화 commit의 V5 `diff_hash`는 정직한 F1 모의와 **바이트까지 같다**(`e079e9dc…`). 그래서 정직한 판에 준 승인 기록이 약화된 head도 V5 PASS로 통과시킨다. f12_equiv는 LISTED, PT3는 43 passed다. 막을 수 있는 것은 auditor의 수동 diff 원문 대조 하나뿐이다. |
| minor | m1 | 154행 "7파일·9자리"는 6파일·6자리에 B34 1파일·3자리를 더한 수다. 그런데 B34 3자리 가운데 `_b34_exc_problems`(73)와 `c5_import_without_grammar_succeeds`(271)는 F1에서 바뀌지 않는다. ⑤에 들어가는 "바뀌는 목록 단위"는 c1·c8이다. c1은 탈출 자리가 아니며 도우미 `_b34_exc_problems`를 부르기 때문에 목록 단위가 된다. 문언은 이미 그렇게 적혀 있지만, 160행의 "dunder 3자리"와 186행의 "dunder 탈출 자리 파일에서 바뀌는 목록 단위"를 함께 읽으면 c1이 dunder 자리라고 오해하기 쉽다. "c1 = 도우미 호출 단위, c8 = dunder 자리 단위"로 사유를 단위별로 적을 것(⑤ 제시 방법 (2)의 '목록 사유'와 같은 형식). |

## 1. 주장 실측(sandbox `C:/g337`, `core.autocrlf=false`, TMP/TEMP는 sandbox 아래)

사슬: `bash p3kit_f12/mk_chain_r1.sh C:/g337/f <chip-design-skills> g1_kit/install_proto.py 2183f2e` → exit 0
(D-11 'already present' 빈 커밋, G1 'installed 4', M1~M9 `import_fail` 전부 {}, `changed 72 notes 1 d17 files 8`).
커밋: F1 모의 base `e0f2d8a`, F1 모의 `4f93bac`, F2 모의 `af3af94`.

| 주장 | 실측 | 결과 |
|---|---|---|
| `assets` 트리 7c6c2c8·e25ccd3·f05f7b8 | `7c6c2c8`·`e25ccd3`·`f05f7b8` | 일치 |
| 재작성기 changed 72, D-17 8파일 | `changed 72 … d17 files 8` | 일치 |
| 7단위 목록 → 62/7/3 (FAIL = selftest 3 `ast_same`·`from_same`) | 72파일 PASS 62·LISTED 7·FAIL 3, FAIL 3 = `test_selftest_{design_report,sizing_recipe,topology_library}.py` `['ast_same','from_same']` | 일치 |
| 5단위 → 62/6/4 (+B34 `listed_changes_approved`) | 62·6·4, B34 `listed_unapproved` = c1·c8 | 일치 |
| 목록 없음 → 62/1/9 | 62·1·9 | 일치 |
| `d17_expect_vs_f1sim_diff` [] | 키가 출력에 없음(`None`). 옛 판 출력 형식과 같은 것으로 보이고 판정에는 영향 없음 | 사실상 일치 |
| B34 목록 단위 7, 바뀐 단위 2(c1·c8), dunder 73·271·301 | `listed_units` 7(card 열거와 같음), `listed_changed_units` = c1·c8, `escape_sites_base` = (`_b34_exc_problems`,dunder,73)·(c5_import…,dunder,271)·(c8,dunder,301) | 일치 |
| V5 FAIL 발견 10·`diff_paths` 6·`diff_hash` e079e9dcab5a | FAIL 10(conftest 1 + 리터럴 9)·paths 6·`e079e9dcab5a5347384f8d93f682d6065221b2c869abf35643fa9c8235229898`, B34 파일은 paths 밖 | 일치 |
| 대상 72(+3 = 75), test-author 56 | B34 파일은 `import stick_diagram`만 있고 SR·TL·DR import가 없다 → (b)만 +1. 경로는 `A/tests/contracts` → test-author. (c)만 3과 code-author 쪽은 다시 세지 않았다(옛 판 수치 그대로) | 일치(+1 부분) |
| gate 6c724de에서 parse_spec_card 불변 | `git diff --stat 2183f2e 6c724de` = docs spec·interface 2파일뿐이고 `tools/` 변경 0 | 일치 |
| B34 변경 = 별칭 import 2줄 + 모듈 식뿐 | 모의 diff는 그렇다. 다만 **c5_no_gate·c6 단위도 바뀐다**(목록 밖 → (가)~(마) PASS로 판정). 그리고 B1의 문자열은 모의가 바꾸지 않았다 | 부분 -- B1 |

## 2. B1 상세 -- 문자열 안 스크립트 reader

- F1 base `test_b34_grammar_explicit.py` 123행 `_B34_FRESH_SCRIPT = r'''…'''`은 c8이 `subprocess`로 새 인터프리터에서 실행하는 스크립트다. 그 안에서 `stick_diagram.find_idiom_matches`·`find_differential_and_mirror_forks`·`suggest_vertical_stack_composites`·`find_differential_pair_candidates`·`find_verified_differential_and_mirror_relations`·`refine_differential_and_mirror_relations`·`audit_theta_root_direction`·`propose_theta_kcl_gap_fill`·`propose_device_roles_gap_fill`·`propose_vertical_stack_id_gap_fill`를 부른다. 10개 모두 F2 SD 삭제 집합 49에 든다.
  주석이 직접 밝히듯 "호출은 문자열 안에 있어 V3 그래프가 … 보지 않는다". 같은 이유로 `E3B_AST` `file_reads`(계약 1 (b) 대상 정의, 계약 5 (b) reader 0)도 이 자리를 보지 못한다.
- 실측(`pytest -p no:cacheprovider` B34 파일 전체): F1 모의 `4f93bac` **43 passed**(shim 재수출이 남아 있음), F2 모의 `af3af94` **9 failed·34 passed**. 실패 9개는 모두 c8 × 9회로이고 원인은 `AttributeError: module 'stick_diagram' has no attribute 'find_idiom_matches'`(subprocess rc 1)다.
- 문자열 상수 전수 스캔(`C:/g337/strscan.py`, F1 모의 base 추적 `.py`, 길이 20자를 넘는 문자열에서 `stick_diagram.<삭제 집합>`과 `from stick_diagram import <삭제 집합>`을 찾음): 실행되는 자리는 이 파일 하나다. 나머지 4곳은 docstring이거나 범위 밖이다(`docs/…/probe_stage_partition.py` docstring, `tools/gates/test_lint.py` docstring, `.ai/verification/…/v4diag_b34.py`).
- 영향: (1) 이 card가 이 줄을 고치지 않으면 F1 계약 6(PT3 같음)은 통과하지만 F2가 깨진다. F2는 test를 고치는 card가 아니므로 test 변경을 F2로 미룰 수 없다. (2) 고치면 모듈 수준 문자열 상수 교체가 되어 V5 '리터럴 변경' 발견 +1(단위 `<module>`)이 생긴다. 그러면 발견 11·`diff_paths` 7·`diff_hash`가 바뀌어, 갱신본 197~200행의 "B34 test 2단위는 발견 0 / `diff_paths` 밖"과 284행의 "`7243f28` 판과 같음"이 틀린 문장이 된다. f12_equiv (가)도 이 변경을 `ast_same` FAIL로 낼 것이다(목록 단위가 아님). 계약 3에 이 자리의 판정 규칙(목록 단위로 둘지, 별도 규칙을 둘지)이 필요하다.
- 요청: 계약 1 (b)·5 (b)의 reader 정의에 "실행되는 문자열 스크립트 안 읽기"를 넣거나 명시적 예외 + 수동 목록을 두고, 이 1자리를 대상에 더한 뒤 V5·f12_equiv 수치를 다시 잴 것. 같은 맹점이 F2 card의 E3b에도 있는지 확인할 것.

## 3. S1 상세 -- 적대 약화 실험

`C:/g337/r2`(사슬 clone)에서 F1 모의 `4f93bac` 위에 두 commit을 만들었다.
- **adv A `acbf56f`(목록 단위 c1 약화)**: ① `_f1_topology_authoring.audit_theta_root_direction(ts, None)` → `_f1_topology_authoring.find_idiom_matches(ts)`(진입점 14개 중 하나의 부재 판정을 잃음). ② `propose_theta_kcl_gap_fill` 블록의 `assert _b34_exc_problems(ei.value) == []` → `assert [] == []`(항진식).
- **adv B `b717bc8`(대조: 목록 밖 단위 c5_no_gate 약화)**: `assert …find_idiom_matches(fx) is None` → `… is None or True`.

| 층 | adv A (c1, 목록 단위) | adv B (c5_no_gate, 목록 밖) |
|---|---|---|
| gate V5 `weakening_diff` | FAIL 발견 10·paths 6·`diff_hash` **e079e9dc…(정직한 판과 같음)** → 정직한 판의 승인 기록이 그대로 'approved' | 같음(e079e9dc…) |
| f12_equiv r4(7단위 목록) | B34 **LISTED**(`listed_changes_approved` 참) → 62/7/3, 정직한 판과 구분 불가 | B34 **FAIL** `ast_same`·`attr_same` |
| PT3(B34 파일) | 43 passed | 43 passed |
| (ii) 정적 확인(R-DEF·N3.10 범위) | 해당 없음(도우미 반환 모듈 규칙과 무관) | -- |
| (바) (i) auditor diff 원문 대조 | **유일하게 잡을 수 있는 층**(승인 기록에 인용된 원문과 다른 줄이 생김) | -- |

결론: 같은 약화를 목록 밖 단위에 넣으면 (가)가 기계적으로 잡지만, 목록 단위 c1·c8에 넣으면 기계 계층(V5 해시·f12_equiv·PT3)은 모두 통과한다. 방어는 auditor가 손으로 원문을 대조하는 것 하나뿐이다.
card는 이것을 '승인 구속은 범위 설명의 원문 인용과 (바) (i) auditor 대조뿐'이라고 정직하게 밝히고 있고 계약상 FAIL 규정도 있다. 그래서 B는 아니다. 그러나 c1은 계약 test 14개 진입점의 오류 문구 단언이 몰려 있는 단위이고, `diff_hash`가 그 파일을 덮지 않아 승인 해시가 약화본에서도 그대로 맞는다. 그래서 **S**로 둔다.
권고(택1): (a) 승인 기록 범위 설명에 목록 단위가 든 파일(발견 0인 파일 포함)의 `경로\tbase blob\thead blob` 줄과 그 sha256을 두 번째 target으로 적게 하고, auditor가 head에서 다시 계산해 대조하도록 계약 3 (바) (i)에 명시한다. (b) auditor 판정 기록에 "목록 단위 diff 원문 = 인용 원문" 대조를 기계 비교(문자열 동일)로 남기도록 V 항목을 정한다.
B1을 고치면 B34 파일이 V5 발견 경로에 들어가 `diff_hash`가 그 파일 blob 전체를 덮게 되므로, **B34 파일에 한해서는** 이 구멍이 부수적으로 닫힌다. 다만 ⑤-b(S1 묶는 자리) 같은 발견 0 목록 단위 일반에는 그대로 남는다.

## 4. 정리

- sandbox `C:/g337`은 삭제했다(`ls /c/g337` → No such file, 남은 프로세스 0). 실제 저장소 쓰기는 없다(clone `--no-local`, origin 제거, hooksPath는 sandbox).
- 판정: **B 1 · S 1 · minor 1**. B1(문자열 스크립트 reader 누락 → F2에서 c8 9 failed, V5 수치 문장 변동)이 풀리기 전에는 이 갱신본을 확정하지 말 것.
