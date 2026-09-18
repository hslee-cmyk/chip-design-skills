# review21 -- `00-common` design 독립 검증

* 대상: `docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md`(작업 트리 판, 462줄), `.ai/verification/_schema.json`, `.ai/approvals/_TEMPLATE.md`, `common00_schema_reject_check.py`/`.txt`
* 기준: 계획서 v5.19(작업 트리. `git diff HEAD`의 v5.19 개정 포함), 함수 레지스트리, `workspaces/run_harness.py`, `skills/analog-gmid-design/assets/sizing_recipe.py`·`stick_diagram.py` 실제 소스
* 검증자: 독립 검증 agent(작성자 아님). 검증 중에 계획서가 바뀌었다(U-38 행이 "확정(2026-09-18)"으로 바뀌었고 `.ai/approvals/20260918-u38-jsonschema.md`가 생겼다). 아래 판정은 그 뒤 상태 기준이다.
* 심각도: **S1** = 승인을 막는다(틀림·모순·구현 불가) / **S2** = 승인 전에 고쳐야 한다(구현자 둘이 서로 다르게 갈 수 있는 모호성) / **S3** = 경미

---

## S1

### C-01 (S1) 성능 측정(§10)과 무동작 판정(§11)이 audit/base worktree의 코드를 재지 않는다
* **위치**: §10 '도구가 하는 일' 1·2, §11.4 `--base-worktree/--head-worktree`
* **근거**(`workspaces/run_harness.py` 모듈 머리):
  * `sys.path.insert(0, r"C:\Users\HSLEE\...\chip-design-skills\skills\analog-gmid-design\assets")`: **메인 체크아웃의 절대 경로**가 하드코딩돼 있다. audit worktree(`../wt/<id>-audit`)에서 `import run_harness`를 하면 `sizing_recipe`·`stick_diagram`·`design_report`를 **메인 체크아웃에서** import한다.
  * `ASSETS_DIR`, `LIBRARY_DIR`, `LUTFILE`도 메인 체크아웃 절대 경로다. `_d = np.load(LUTFILE)`와 `_NMOS/_PMOS` 생성은 **import 시점**에 일어나고, `spec_fn`은 그 객체를 담는다(`"lut_by_kind": {"nmos": _NMOS, ...}`). 그래서 import한 뒤에 전역을 패치하면 이미 늦다.
  * 설계가 패치하는 것은 `WORKSPACES_DIR` 하나뿐이다. 그 기본값도 메인 체크아웃 경로라서, 패치하지 않았을 때 파일이 생기는 곳은 worktree가 아니라 **메인 체크아웃**이다. §10-2의 "worktree에 파일이 생기면 EL2가 거부"는 사실과 다르다. EL2는 이 쓰기를 보지 못하고 메인 작업 트리만 더러워진다.
  * 결과: perf 수치는 병합본이 아니라 메인 체크아웃 코드·LUT·topology의 수치가 된다. 무동작 판정에서는 base와 head가 같은 메인 체크아웃 코드를 돌리므로 해시가 **자명하게 같아진다**. 판정이 가짜 PASS를 낸다.
  * 경로를 고쳐도 문제가 하나 남는다. `stick_diagram.py:save_instance_json`은 `"topology_ref": topology_json_path`(절대 경로)를 instance.json에 쓴다. worktree마다 경로가 다르니 §11.3 정규화 해시가 **항상 달라진다**. 판정이 가짜 FAIL을 낸다.
* **수정**: 도구가 import하기 **전에** 대상 worktree의 `skills/analog-gmid-design/assets`와 `workspaces`를 `sys.path` 앞에 두는 절차를 명시한다. `ASSETS_DIR/LIBRARY_DIR/LUTFILE`을 worktree 기준으로 바꾸는 방법도 적는다(권장: 별도 프로세스를 `cwd=worktree`로 띄우고 run_harness의 경로 상수를 worktree 상대 경로로 바꾸는 code 변경을 선행 spec card로 둔다). base와 head는 서로 다른 프로세스로 실행한다. §11.3 정규화에 "worktree 루트 절대 경로를 상대 경로로 치환(또는 `topology_ref` 같은 경로 필드 제외 목록)"을 더한다. 끝으로 audit worktree의 `sizing_recipe.__file__`이 worktree 안인지 단언하는 사전 검사를 도구에 넣는다(WP-02 '실제로 그 코드를 잰다').

### C-02 (S1) 예외 계층의 위치가 N3.10 import 규칙과 레지스트리 목적지에 어긋난다
* **위치**: §7.1 "클래스 구조 (MOD2 `topology_authoring.py`)"와 `class InfeasibleSizingError(ValueError): ...  # 기존 클래스 유지(sizing_recipe.py)`, §12 행 `FAILURE_CLASSES, 예외… | MOD2`
* **근거**:
  * 함수 레지스트리 `InfeasibleSizingError` 행의 이관 목적지는 `gmid_sizing_engine`(MOD4)이다.
  * N3.10: "import는 번호가 작은 모듈 쪽으로만". 하위 클래스(`StructureUnresolvedError` 등)를 MOD2에 두고 기반을 MOD4(또는 `sizing_recipe.py`)에 두면 MOD2가 MOD4를 import해야 하므로 규칙 위반이다.
  * CC-4는 Phase 4 몫이다. 그런데 Phase 3 DoD(N6.2)는 "`sizing_recipe.py` 삭제"라서, "유지(sizing_recipe.py)"라는 위치는 CC-4 시점에 존재하지 않는다.
* **수정**: 기반 클래스를 포함한 계층 전체를 MOD2(또는 더 낮은 번호)에 두기로 정하고 레지스트리 목적지를 바꾼다(WP-14, 같은 변경 단위). 아니면 계층 전체를 MOD4에 두고 MOD2의 `SchemaRejectedError`만 독립 클래스로 둔다. 어느 쪽이든 §7.1 머리와 주석을 한 위치로 맞춘다.

### C-03 (S1) CC-3·CC-7·CC-8의 판정 유형 `test-only`가 계획의 정의 밖이라 V2가 판정할 증거가 없다
* **위치**: §13 CC-3(`IC_TABLE` + TS7 xfail + §9.4 IC 부분), CC-7(성능 측정 도구), CC-8(무동작 판정 도구)
* **근거**:
  * N3.12.3: "test 전용 변경(판정 유형 `test-only`: TS2·TS3·TS5, TS6의 probe 승격·삭제) … 증거 = 변경 전 test 집합이 base에서 통과시킨 섹션을 변경 후 test가 모두 PASS함".
  * N4.2 V2: "test-only: 섹션->test 매핑표의 모든 섹션이 변경 후 test에서 PASS".
  * 새 계측·판정 도구와 새 상수표에는 '변경 전 섹션'이 없다. 그러면 V2가 **공허하게 PASS**해서 아무 증거 없이 병합된다. 이것은 WP-02가 금하는 "통과만 확인하는 게이트"다.
  * 또 N6.1 Phase 1 판정 유형 열은 TS7에 유형을 주지 않는다. 설계가 새 유형 용법을 만든 것이다.
* **수정**: 두 길 중 하나를 고른다. (가) CC-3·CC-7·CC-8을 `red-green`으로 바꾼다. 도구의 거부 동작을 합성 입력으로 보이는 red, 예컨대 CC-8은 발동 1건을 넣은 변형에서 FAIL, CC-7은 실패 경로에서도 파일을 쓰는지. (나) 계획 N3.12.3·N4.2 V2에 "신규 test-author 도구"용 test-only 증거 규칙을 추가한다(계획 개정 요청). 어느 쪽이든 각 CC의 V2 증거를 §13에 적는다.

---

## S2

### C-04 (S2) CC-1·CC-2(merge gate, code-author, red-green, Phase 0.5)와 부트스트랩 ①의 관계가 미정이다
* **위치**: §9.1 "`V_CHECKS` (`tools/gates/merge_gate.py`, code-author)", §12, §13 CC-1·CC-2
* **근거**:
  * N3.12.6 ①은 "오케스트레이터가 … hook·게이트 스크립트, 양식 초안을 작성"하고, ⑤ "이후 … 모든 변경은 N3.12.3 흐름으로"다.
  * N3.12.2에서 code-author가 `tools/gates/*.py`를 쓰려면 "게이트 변경 spec card와 승인 기록"이 있어야 한다.
  * 그런데 N4.3 공격 5(EL4 거부)는 0.5에서 merge gate가 이미 있어야 증명된다.
  * 설계는 CC-1·CC-2가 ① 안에서 만드는 것인지(그러면 작성자는 오케스트레이터이고 red-green 흐름이 아니다), ⑤ 이후의 게이트 변경인지(그러면 0.5 DoD 전에 게이트 변경 흐름이 한 번 돌아야 한다)를 정하지 않는다. 구현자에 따라 작성 주체가 달라진다.
* **수정**: §13에 "CC-1·CC-2는 부트스트랩 ⑤ 이후의 게이트 변경(spec card + 승인 기록)이며, ①의 merge gate는 판정 기록 존재·freeze 해시만 검사한다"처럼 순서를 못박는다. 아니면 ①에서 오케스트레이터가 쓴다고 바꾸고, `소유 역할`을 고친다.

### C-05 (S2) `SchemaRejectedError(ValueError)`가 기존 `except ValueError`/`except Exception`에 삼켜진다(§7.3 근거가 현 코드와 맞지 않다)
* **위치**: §7.1 `class SchemaRejectedError(ValueError)`, §7.3 "InfeasibleSizingError 하위가 아닌 이유 … 루프가 조용히 삼킨다"
* **근거**(실제 소스):
  * `sizing_recipe.py:_optimize_theta_slsqp_block_coordinate`: `except ValueError as _fast_e:` 뒤 라운드를 건너뛴다(탐색 루프 안).
  * `sizing_recipe.py:repair_infeasible_baseline._probe`: `except Exception: return False, frozenset()`
  * `sizing_recipe.py:achievable_metric_bound` 근처: 시드 루프의 `except Exception as e:`는 notes만 적고 계속한다.
  * `sizing_recipe.py:_build_theta_evaluator`: `synthesize_l_class_thetas(...)`를 `except (KeyError, ValueError): pass`로 감싼다. 이 안의 `_matching_pairs_cached(topology_path)`가 topology를 다시 읽는다. 로더에 게이트를 배선하면 거부가 여기서 **조용히** 사라질 수 있다.
  * `workspaces/run_harness.py:run`: `except Exception as e:` 뒤 print만 하고 정상 종료한다. exit code는 항상 0이다.
  * 설계의 루프 규칙은 "`InfeasibleSizingError`를 잡지 않는다"뿐이다. `ValueError`를 상속했으니 위 지점들이 그대로 삼킨다. N3.14 하위 클래스 전부(`StructureUnresolvedError` 등)도 같은 이유로 삼켜진다.
* **수정**: (가) `SchemaRejectedError`를 `ValueError`가 아닌 `Exception` 하위로 두거나, (나) CC-4 범위에 "기존 광범위 except(위 5곳 + `grep -n "except \(ValueError\|Exception\)"` 전수)가 N3.14 클래스를 재raise한다"를 넣고 그 목록을 §7.3에 적는다. CC-4의 oracle "삼키지 않음"은 이 지점들을 겨누는 red로 구체화한다.

### C-06 (S2) 계획 표 일치 test(§9.4)의 파싱 규칙이 모호하고 표 구조가 상수 형식과 맞지 않는다
* **위치**: §9.1 `V_CHECKS: Mapping[str, Mapping[str, str]]`(`introduced_phase` 한 값), §9.2 `part`, §9.3 `PHASE_ORDER`, §9.4 "`PHASE_ORDER` 원소를 셀 문자열에서 찾는다", §7.1 `FAILURE_CLASSES`
* **근거**:
  * N4.2 V1 `도입` = "1(0.5는 redteam 스크립트)"는 Phase 두 개인데 `introduced_phase`는 문자열 하나다.
  * 부분 문자열로 찾으면 "0.5" 안에서 "5"가, IC11 셀 "4(DEC-60 구현, 2레일), 6a(3레일 추가)"에서 "2"·"3"이 걸린다.
  * IC7 "6a 이후 매 Phase(정지 케이스는 6c)"는 원소 몇 개로 나눠야 하는지 정해지지 않는다.
  * N6.1 `Phase` 열에는 "0"과 "0(문서)"가 있는데 `PHASE_ORDER`에는 없다. §9.4대로 비교하면 FAIL이고, 제외 규칙을 두면 그것이 skip이다.
  * N3.14 표에는 `STRUCTURE_UNRESOLVED`가 두 행(최종 해 포함)이고 괄호 안에 후보 레코드 행이 둘 있다. `{분류 이름: …}` dict 키를 어떻게 만드는지 정의가 없다.
* **수정**: 토큰화 규칙을 정한다. 예: 셀에서 괄호 밖 토큰만 `re.findall(r"(?<![\w.])(0\.5|[1-5]|6[abc]|7[abc])(?![\w.])")`로 읽는다. `introduced_phase`를 tuple로 바꾼다. "이후 매 Phase"는 `from_phase` 필드로 표현한다. N6.1의 '0'·'0(문서)'는 `PHASE_ORDER` 밖임을 계획과 설계에 명시하고 test 기대값에 포함한다. N3.14 행→키 대응 규칙을 표로 적는다.

### C-07 (S2) N9.1 `00-common` '반드시 담을 것'과 N6.2 `0(문서)` DoD 일부가 명목상으로만 충족된다
* **위치**: §1 "범위 밖: 각 표의 **내용**…", §4, §9, §14 마지막 행
* **근거**:
  * N6.2 `0(문서)`: "… V 도입 표·IC 담당 표·성능 측정 명령·무동작 판정 방법이 `00-common` 한 곳에 모임". 그런데 §9는 형식(`{"V1": {"introduced_phase": ..., ...}}`)만 두고 내용은 Phase 0.5/1의 코드 상수로 미룬다.
  * N9.1은 "용어집 최종본(N0.4)"을 요구하는데 §4는 코드 이름 대응 11행뿐이다.
  * §14 "이후 design 문서가 재서술하지 않고 인용함 → 이 문서의 완료 조건이 아니라 이후 문서의 검사 항목"은 계획 DoD를 설계가 **일방적으로 재정의**한 것이다.
  * 구성안 C 자체는 타당할 수 있다. 다만 그러면 계획 DoD 문구와 N9.1 열이 설계와 모순된다.
* **수정**: 계획 N6.2 `0(문서)`와 N9.1 행을 C안에 맞게 개정하도록 요청한다. 예: "V/IC 표는 형식과 일치 test 명세, 내용은 계획 N4.1·N4.2가 정본" 및 "인용 여부는 각 문서의 검증 항목". 아니면 §9에 표 내용을 옮긴다.

### C-08 (S2) `_schema.json`이 거부해야 할 기록을 통과시킨다(독립 측정)
* **위치**: `.ai/verification/_schema.json` `pattern`들, §8.1
* **근거**: 스크래치 스크립트로 작성자가 시험하지 않은 18건을 jsonschema 4.26.0, `Draft202012Validator` + `FormatChecker`에서 돌렸다. 결과:

  | 케이스 | 기대 | 결과 |
  |---|---|---|
  | `id = "20260918-s\n"`(끝 개행) | 거부 | **통과** |
  | `base_commit = "a"*40 + "\n"` | 거부 | **통과** |
  | `spec_card` 끝 개행 | 거부 | **통과** |
  | `reproduced_numbers.value = NaN` | 거부(JSON 밖) | **통과** |
  | `checks.V1.basis = "   "`(공백만, 설계 "비지 않은 문자열") | 거부 | **통과** |
  | `approvals` 중복 id / `red.test_ids` 중복 | 거부가 합당 | 통과 |
  | `id = "20261399-s"`(없는 날짜) | 거부가 합당 | 통과 |
  | `evidence_type` 누락·null, equivalence인데 `code_commit` null, test-only인데 `code_commit` 키 없음, value `true`, verdict `"pass"` | 거부 | 거부(정상) |
  | red-green 최소·test-only 정상 | 통과 | 통과(정상) |
  | `failure_hashes`와 `test_ids` 길이 불일치, N/A basis에 도입 Phase 없음 | 스키마 통과, 로더 담당(§8.1) | 통과(설계대로) |

  원인: Python `re`의 `$`는 끝 개행 앞에서도 맞는다. jsonschema는 `re.search`를 쓴다. 이 스키마는 ECMA-262 검증기와 결과가 갈린다. U-38로 jsonschema가 확정됐으니 이 차이가 곧 운영 동작이 된다.
* **수정**: 패턴을 `^…$` 대신 `^…(?![\s\S])`로 쓰거나 로더 추가 검사(§8.1 목록)에 "모든 문자열에 제어문자·끝 개행 없음"을 넣는다. basis는 `"pattern": "\\S"`로 둔다. `approvals`·`test_ids`에 `uniqueItems: true`를 둔다. NaN/Inf는 로더가 `json.loads(..., parse_constant=거부)`로 막는다. §14 거부 케이스 목록에도 이 케이스들을 더한다.

### C-09 (S2) `failure_hashes`·`outputs_hash`에 소비자가 없고, 정의가 재현되지 않는다(WP-01)
* **위치**: §8.1 해시 정의, §8.1 '스키마로 못 하는 검사' 목록
* **근거**:
  * 로더 추가 검사 목록에 해시 **재계산·대조**가 없다. 누가 언제 이 값을 검사하는지 설계 어디에도 없다. 만들고 쓰지 않는 필드다.
  * `failure_hashes` 입력인 "pytest reprcrash 메시지"에는 파일 절대 경로(worktree마다 다르다)와 실수 repr이 흔히 들어가므로, 다른 worktree에서 재실행하면 값이 달라진다.
* **수정**: 소비자를 정한다. 예: "merge gate가 freeze worktree에서 red를 재실행해 해시를 재계산하고 대조한다(V2)". 해시 입력을 경로 정규화된 형태로 정의하거나 `(test_id, 예외 타입)`만 쓴다. 소비자를 둘 수 없으면 필드를 계획 N3.12.5에서 빼도록 요청한다.

### C-10 (S2) 작성자≠검증자 위반 3곳(WP-13)
* **위치**: §14·`.txt`, §13 CC-3, §13 CC-8
* **근거**:
  * `_schema.json`(§3.3 부류 "코드(데이터)")과 그 거부 측정 스크립트, 측정 결과("24/24")를 모두 오케스트레이터가 썼다. history v5.19 행은 그 수치를 근거로 인용한다. 스크립트가 시험하지 않은 거부 누락이 실제로 있다(C-08).
  * CC-3: `IC_TABLE`(판정 입력 상수)도, 그것을 계획서와 대조하는 §9.4 IC 부분 test도 test-author가 쓴다.
  * CC-8: 무동작 판정 도구와 그 도구의 test를 둘 다 test-author가 쓴다(test-only).
* **수정**: §14 통과 기준을 "독립 검증 agent의 재실행·추가 케이스 결과"로 바꾼다(작성자 `.txt`는 참고). CC-3은 상수를 code-author로 옮기거나 §9.4 대조 test를 auditor가 실행하는 것으로 분리한다. CC-8은 도구의 거부 동작을 auditor 재실행이나 별도 역할의 test로 판정한다.

### C-11 (S2) oracle (d)를 재정의했다(N9.4 인용 규칙)
* **위치**: §9.4 "oracle 종류: (d) 사용자가 승인한 계획서 값", §13 CC-2 "(d) 계획서 N4.2·N6.1", CC-3, CC-5
* **근거**: N0.4 "oracle 4종 … (d) spec card에 사용자가 적은 값". N3.12.3 선택 기준은 "(d) 회로 해석 결론이나 사용자가 선언한 스펙값"이다. '계획서 표'는 (d)에 없다.
* **수정**: 정의를 넓힐 필요가 있으면 계획 N0.4 (d)를 개정하도록 요청한다. 아니면 spec card의 '오라클 출처'에 사용자 승인 계획 절을 적는 방식으로 (d)에 맞춘다.

### C-12 (S2) 성능 측정(§10)의 산출이 구현자마다 달라진다
* **위치**: §10 '도구가 하는 일' 3·4, '출력 JSON'
* **근거와 모호점**:
  1. `status`/`failure_class`: `run_harness.run()`이 모든 예외를 `except Exception`으로 잡고 print만 한다. 도구가 `run()`의 반환이나 예외로는 실패를 알 수 없다. 패치 래퍼 안에서 잡는지, stdout을 파싱하는지가 정해져 있지 않다.
  2. `eval_times_s`: `ev["evaluate"]`는 `InfeasibleSizingError`로 실패하는 호출이 흔하다(`_optimize_theta_slsqp`, `repair_infeasible_baseline._probe` 등). 실패 호출 시간을 포함할지 정해지지 않았다. 또 `_optimize_theta_slsqp._cached_evaluate` 캐시 **아래**를 재므로 `eval_count`는 캐시 미스 수라는 점을 명시해야 한다.
  3. `spec_fingerprint` = "`canonical_spec(circuit)`를 키 정렬한 JSON의 sha256": spec에 `SemiEmpiricalGmIdLUT` 객체(`lut_by_kind`, `lut`)가 있어 `json.dumps`가 실패한다. 또 같은 이름의 기존 함수 `sizing_recipe.py:spec_fingerprint(spec)`(레지스트리 등재, S0로 대체 예정)가 있어 이름이 두 정의가 된다(WP-14).
  4. `lut_fingerprint`: 계산법이 없다.
  5. 실행 단위: N6.3은 "매 Phase 보고"인데 출력 경로는 `<spec card id>.json`이다. 어느 spec card에서 도는지(모든 동작 변경 card인지 Phase 마지막 card인지) 정해지지 않았다.
  6. 출력 위치 `.ai/verification/perf/…`, `.ai/verification/noop/…`: N3.12.1에서 auditor는 "판정 기록 외 쓰기" 불가다. 이 파일들은 판정 기록(`.ai/verification/<id>.json`)이 아니다. merge gate 로더가 `.ai/verification/*.json`을 훑을 때(그리고 `_schema.json` 자신도) 어떤 파일을 스키마에 대는지 glob 규칙이 없다.
* **수정**: (1) 래퍼가 탐색 호출 예외를 잡아 `failure_class = FAILURE_CLASSES` 조회 결과로 기록한 뒤 재raise한다. (2) `eval_times_s`는 성공·실패를 모두 넣고 `eval_outcomes`를 병기한다. (3) 기존 `spec_fingerprint`를 재사용하거나(한계 명시) S0 지문이 생기기 전에는 `repr` 기반 정의를 명시한다. 이름 충돌은 피한다. (4) LUT npz 파일 바이트 sha256으로 정한다. (5) "Phase 마지막 병합 card에서 1회"처럼 정한다. (6) 계획 N3.12.1/N3.12.5에 auditor 부속 산출물 경로를 추가하도록 요청하고, 로더 glob를 `^[0-9]{8}-[a-z0-9-]+\.json$`로 한정한다.

### C-13 (S2) 무동작 판정(§11)을 두 구현자가 같게 구현할 수 없다
* **위치**: §11.2·§11.3·§11.4
* **근거와 모호점**:
  1. 산출물을 **어떤 명령으로** 만드는지 없다. `run_harness`는 `SPECS` 4회로만 실행한다. "구조 단계까지만 가는 회로"(`common_gate_amplifier` 등)는 6a 진입점 전에는 실행 경로가 없다.
  2. "그 회로가 base에서 만드는 파일 **전부**": 사이징 회로는 `report.html`도 만든다. 정규화는 JSON만 정의돼 있다.
  3. "base 키 집합으로 투영": 중첩 dict·list 안의 새 키를 어떻게 다루는지 정해지지 않았다.
  4. `runs/<spec card id>/<circuit>/activations.json`: 엔진이 spec card id를 알아야 하는데 전달 경로가 없다. 엔진이 역할 절차에 의존하게 된다.
  5. `--activation-ids`와 '무발동 값' 선언을 spec card에서 읽는다. 그런데 N3.12.3 spec card 필드 목록에는 '무발동 값'도 '발동 계수 ID'도 없다(v5.19에서 Phase만 추가).
  6. 결정론 사전 검사 시드 `0과 1`: 계획 TS1은 1~5를 쓴다. 근거 없는 선택이다.
* **수정**: 도구가 부르는 진입점을 Phase별로 표로 정한다(Phase 3 전 `run_harness.run`, 6a 이후 구조 진입점). 비교 대상을 "JSON 산출물(`*.instance.json`, `*.structure.json`)"로 한정한다. 투영 규칙은 "재귀, list는 원소별"처럼 적는다. activations 출력 경로는 도구가 인자로 넘기게 한다(엔진은 경로만 받는다). N3.12.3 spec card 필드에 '발동 계수 ID·무발동 값'을 더하도록 계획 개정을 요청한다. 시드 집합은 TS1과 같이 1~5로 하거나 근거를 적는다.

### C-14 (S2) 옛 키 거부 게이트 형식(§6)이 N3.16과 현 코드를 다 덮지 못한다
* **위치**: §6.1 `stage: "MG1" | "MG2" | "MG3"`, §6.2 '배선'·'대체'
* **근거**:
  * N3.16에서 `vs`→`vsb` 행의 단계는 **"MG0(`_TEMPLATE` 안내)"**다. 그런데 §6.2는 `vs` 행을 `LEGACY_NAMES`에 넣으면서 `stage`에 MG0을 허용하지 않는다. MG0의 `_paper_target_spec`→`_declared_target_spec` 등도 같다.
  * 배선 대상이 "`load_topology`, `load_sizing_spec`, metric 선언 읽기, 하네스 spec 읽기"뿐이다. 하지만 topology JSON을 직접 `json.load`하는 곳이 더 있다: `sizing_recipe.py` 5388·8268·8315행 부근, `stick_diagram.py` 3958·4722·8590행 부근. 그 경로는 게이트를 우회한다(WP-02). 참고로 현 `validate_no_legacy_vs_key`도 `load_topology`가 아니라 `_build_theta_evaluator`에서 `synthesize_l_class_thetas`·`validate_metric_units` **뒤**에 불린다.
  * `where` 값 `"metric_decl"`과 `"topology"`는 7b 전에 metric 선언이 topology 안(`sizing_roles.metrics`)에 있어 겹친다.
  * `"harness_spec"`은 JSON이 아니라 Python dict(`SPECS`)라 "JSON을 파싱한 직후"가 성립하지 않는다.
* **수정**: `stage`에 `"MG0"`을 더한다. 모든 JSON 읽기가 한 로더를 거치도록 하거나, 직접 읽는 지점 전수 목록을 CC-5 범위에 넣는다. `where`를 "파일 종류"로만 정의하고 위치는 `scope`로만 가른다. 하네스 spec은 "`spec_fn()` 반환 직후"로 적는다.

### C-15 (S2) 부트스트랩 뒤 `_schema.json`을 바꿀 역할이 없다
* **위치**: §3.3 "오케스트레이터(부트스트랩 ①), 이후 변경은 N3.12.3", §12
* **근거**: N3.12.2에서 `.ai/verification/**`는 auditor 경로다. N3.12.1에서 auditor는 "판정 기록 외 쓰기" 불가, code-author 경로에는 `.ai/`가 없다. 오케스트레이터는 `.ai/approvals/**`만 쓴다. 그러니 "N3.12.3 흐름"으로 스키마를 바꿀 주체가 없다.
* **수정**: 스키마 변경 주체와 경로 예외를 정하고 계획 N3.12.2 개정을 요청한다(예: "게이트 변경 spec card + 승인 기록이 있을 때 code-author").

### C-16 (S2) `qualifier` 거부 규칙과 `QUALIFIERS` 상수가 미정의이고 미배선이다
* **위치**: §5 마지막 행, §5 머리 글머리 1, §12 `DOMAINS, QUALIFIERS` 행, §13 CC-6
* **근거**:
  * "판정 함수는 `qualifier`가 붙은 값을 받으면 `SchemaRejectedError`로 거부"라고 하는데 '판정 함수'가 무엇인지(목록·식별 방법) 없다.
  * 이 거부는 탐색 **중에** 일어날 수 있다. 그런데 N3.14 SCHEMA_REJECTED의 처리는 "탐색 시작 전 정지"라 서술이 어긋난다.
  * `qualifier`를 값에 붙이는 모양(`{"value":…, "qualifier":…}`인지)도 없다.
  * CC-6의 첫 소비자는 S1 엣지 `domain` 검사인데, 그 검사는 `QUALIFIERS`를 쓰지 않는다. 소비자 없이 만들어진다(WP-01).
* **수정**: `QUALIFIERS`는 봉인 전 값을 처음 내는 변경(6b 봉인 전 추정 또는 7b)과 같은 단위로 옮긴다. 판정 함수 식별 규칙과 값 모양을 적는다. 탐색 중 거부의 처리를 N3.14에 맞춘다(예: 탐색 중 발생도 즉시 정지·exit 7).

### C-17 (S2) IC5 확장이 계획 개정 없이 Phase 1 DoD 범위를 늘린다
* **위치**: §5 '게이트 함수' 행 "docstring의 `영역:` 한 줄 … IC5 test 확장(Phase 1, `10-test-separation`)"
* **근거**: N4.1 IC5 = "검사하지 않는 것" 절 필수. N6.2 Phase 1 DoD = "IC3·IC5 PASS". `영역:` 줄 요구를 IC5에 붙이면 Phase 1 DoD가 계획에 없는 조건으로 늘어난다. `10-test-separation`의 N9.1 행에도 이 항목이 없다. 또 `reject_legacy_names` docstring의 "영역: 해당 없음"은 `DOMAINS` 값 집합 밖인데, 허용 규칙이 없다.
* **수정**: 계획 N4.1 IC5 또는 DEC-67 적용 항목에 추가하도록 요청하고 N9.1 `10-test-separation` 행에 반영한다. '해당 없음' 토큰을 정의한다.

### C-18 (S2) 승인 기록 머리 형식이 모호하다
* **위치**: §8.2, `.ai/approvals/_TEMPLATE.md`
* **근거**:
  * `diff_paths: <공백 구분 경로>`: 저장소에는 공백이 든 경로가 실제로 있다(`skills/analog-gmid-design/assets/아날로그 기능분석기.zip` 등). 공백 분리로는 되살릴 수 없다.
  * 머리에 모르는 키가 있을 때의 처리(스키마 밖 필드 거부 원칙)가 없다.
  * §8.2 코드 블록에는 `# target_kind=diff일 때만` 주석이 값 뒤에 붙는데, 파서의 주석 규칙이 없다.
  * design 문서 자체의 승인(§15 `20260918-00-common-design`)은 `target_kind` diff와 decision 중 어느 쪽인지 정해지지 않았다.
  * `target` 결정 ID 구분자 "쉼표(예: `U-26, J1`)"에서 공백을 처리하는 규칙이 없다.
  * 머리 파서의 위치도 §12("V5 `weakening_diff.py`")와 §13 CC-1("merge gate 로더")로 갈린다.
* **수정**: 경로는 한 줄에 하나(`diff_path:` 반복)로 하거나 JSON 배열 문자열로 둔다. 모르는 키는 거부한다. 주석 줄은 금지한다. design 승인은 `target_kind: diff`(문서 경로)로 명시한다. 구분자는 `,` 후 strip으로 정한다. 파서 소유 모듈은 하나로 정한다.

---

## S3

### C-19 (S3) 버전·상태 표기가 낡았다
* front matter `plan_version: 5.18`, 머리 "v5.18", §15 "계획서 v5.18 확정본(9f4e3e1)"이라고 적었지만, 이 문서는 커밋되지 않은 v5.19 개정(SCHEMA_REJECTED·Phase 필드·`perf/`·U-38)에 기대고 있다.
* §14·§16은 U-38을 "Phase 0.5 착수 조건으로 넘겼다"고 하는데, 계획 N7.2는 이제 "**확정(2026-09-18)**"이고 승인 기록 `.ai/approvals/20260918-u38-jsonschema.md`가 있다. §15의 "첫 승인 기록" 서술도 틀렸다.
* **수정**: 5.19로 맞추고, §14·§15·§16에 U-38 확정과 승인 기록 id를 반영한다.

### C-20 (S3) §3.3이 자기 양식(§3.2)을 어긴다
* `부류` 값을 셋으로 한정해 놓고 "코드(데이터)"를 쓴다.
* `소유 역할`은 N3.12.1 네 주체 이름이어야 하는데 "code-author / test-author" 약칭을 쓴다.
* "부류가 코드이면 구현과 test 소유자 둘 다"라고 해 놓고 `_schema.json`·`_TEMPLATE.md`·도구 행에는 하나만 적었다.
* **수정**: 값 집합에 맞추거나 양식을 고친다.

### C-21 (S3) §7.3이 계획 N3.14에 들어간 행과 탐색 루프 규칙을 다시 적는다(N9.4)
* 문구도 다르다: 설계는 "옛 이름(§6)", 계획은 "옛 이름(DEC-69)"이다. v5.19 반영 뒤이므로 §7.3은 "N3.14 SCHEMA_REJECTED 행" 인용 한 줄이면 된다.

### C-22 (S3) N9.1 '읽을 plan 절' 열을 갱신하지 않았다
* 설계는 N3.10·N3.11·N3.12.2~4·N3.16·N6.1·N6.2·N0.1을 쓰는데, N9.1 `00-common` 행에는 없다(N9.1: "읽기 전에 그 절을 이 열에 추가한다").
* 또 CC-7·CC-8을 `40-defect-fixes`가, CC-1·CC-2를 `05-role-separation`이 발행하게 했지만, 그 문서들의 '반드시 담을 것' 열에는 반영하지 않았다. 해당 문서를 쓸 때 빠질 위험이 있다.

### C-23 (S3) 근거 없는 고정값(WP-03·WP-05)
* 결정론 시드 `0과 1`은 C-13에서 다뤘다.
* §10 명령에 파일럿 이름 `current_reuse_telescopic_ota`를 박았다. N0.4가 파일럿을 정하지만 이름은 선언에서 읽는 편이 일반적이다.
* 명령의 `python`이 프로젝트 인터프리터 `C:\Python314\python.exe`와 일치하는지 명시하지 않았다.

### C-24 (S3) 소소한 정의 누락
* `exit_code_for`가 `isinstance` 대조인지 정확한 타입 대조인지 정하지 않았다. 기반 `InfeasibleSizingError` 직접 raise는 1이 된다.
* CC-8 oracle "(a) 결정론 사전 검사 + 합성 변경"은 (a)(물리 불변식·손계산)에 해당하지 않는다.
* 판정식(N9.2-3)을 담는 절이 따로 없고 §10·§11에 흩어져 있다.

---

## 검사 항목별 요약(지시 1~9)

1. **적용 범위**: 분류 양식·영역 규약·옛 키 게이트·실패 규약·두 양식·성능 명령·무동작 방법은 모두 절이 있다. V 도입 표·IC 담당 표·용어집 최종본·"이후 문서 인용"은 명목상으로만 충족한다(C-07).
2. **모순**: 예외 계층 위치(C-02), test-only 용법(C-03), 부트스트랩 대 CC-1·2(C-04), MG0 단계(C-14), 스키마 변경 주체(C-15), auditor 쓰기 범위(C-12-6), 문서 내부 불일치(C-18 파서 위치, C-20).
3. **인용 규칙**: oracle (d) 재정의(C-11), N3.14 행 중복(C-21), DoD 재정의(C-07).
4. **필수 절**: 1~8이 모두 있다(3은 산재, C-24). '열린 질문 없음'이라고 했지만 숨은 미정 항목이 있다: 판정 함수 정의(C-16), 산출물 생성 명령(C-13), spec card 필드(C-13), 파싱 규칙(C-06), 해시 소비자(C-09), 스키마 변경 주체(C-15).
5. **WP-03·02·01·13**: 고정값(C-23), 게이트 우회 읽기 경로(C-14)와 광범위 except(C-05), 미배선(C-09, C-16), 작성자=검증자(C-10).
6. **코드 사실**:
   * (a) `run()`은 호출 시점에 `WORKSPACES_DIR`을 읽는다. **맞다**(`run_harness.py:run`의 `os.path.join(WORKSPACES_DIR, cfg["report_dir"])`). 다만 다른 경로 상수와 `sys.path`가 하드코딩이라 측정이 성립하지 않는다(C-01).
   * (b) `from sizing_recipe import (… optimize_full_circuit_budget …)` 후 `run()`에서 전역 이름으로 호출하므로 패치가 가로챈다. **맞다**.
   * (c) `optimize_full_circuit_budget`은 모듈 전역 `_build_theta_evaluator`를 부르고 `_evaluate = ev["evaluate"]`를 쓴다. slsqp 경로(`_optimize_theta_slsqp`→`presolve_warm_start(ev=ev)`→…)는 모든 평가를 `ev["evaluate"]`로 하고, `ev or _build_theta_evaluator(...)` 재빌드 경로도 모듈 전역을 부른다. 그래서 `sizing_recipe._build_theta_evaluator`를 패치하면 **전부 덮인다**. 다만 `_cached_evaluate` 캐시 아래와 실패 호출 포함 여부가 미정이다(C-12).
   * (d) `sizing_recipe.py:validate_no_legacy_vs_key(device_roles)`는 있다. dict인 `device_roles` 항목에 `"vs"` 키가 있으면 `ValueError`를 낸다(목록은 6개로 잘라 표시). 호출 지점은 `_build_theta_evaluator` 한 곳이고, 다른 필드를 읽은 뒤다. N3.16 단계는 MG0이다(C-14).
   * (e) `class InfeasibleSizingError(ValueError)`(`sized_snapshot` 속성). grid 루프(`optimize_full_circuit_budget`)는 `except InfeasibleSizingError`만 잡는다. 하지만 block-coordinate의 `except ValueError`, `_probe`의 `except Exception`, `_build_theta_evaluator`의 `except (KeyError, ValueError): pass`, `run()`의 `except Exception`이 `SchemaRejectedError(ValueError)`를 삼킨다(C-05).
7. **스키마**: 필드 집합은 N3.12.5와 정확히 일치한다(누락·추가 0. `checks` 값의 "근거"는 `basis`). 조건부 규칙은 N3.12.3과 일치한다(test-only는 `code_commit` null, red·equivalence 금지). 독립 케이스 18건 중 **거부 누락 5건**(끝 개행 3, NaN, 공백 basis)과 합당한 거부 누락 3건(중복·날짜)을 찾았다(C-08).
8. **일반성**: 회로·소자·넷 한정 규칙은 없다. 예시와 파일럿 명령만 있다(C-23).
9. **§10·§11 결정성**: 산출이 갈리는 지점은 C-12의 6개와 C-13의 6개다. 무엇보다 두 방법 모두 현재 코드로는 대상 worktree의 코드를 재지 않는다(C-01).

---

## 집계

| 심각도 | 건수 | ID |
|---|---|---|
| S1 | 3 | C-01, C-02, C-03 |
| S2 | 15 | C-04 ~ C-18 |
| S3 | 6 | C-19 ~ C-24 |

**판정: 수정 후 승인**. S1 3건은 모두 국소 수정으로 닫힌다: 측정 도구의 import·경로 절차, 예외 계층 위치 하나로 통일, CC 판정 유형이나 V2 규칙. 재작성은 필요 없다.
