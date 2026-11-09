# Phase 3 초안 v2 → v3 개정 기록 (검토 `review_phase3_drafts.md` 대응)

기준 HEAD = gate `master` `cd64170`(B28 미병합, B28 code 브랜치 `dee338d`). 저장소 읽기 전용, 스크래치 `C:/g29`(끝에 삭제).

산출물(모두 `wt/_drafts/`):
* `draft_phase3_design_v3.md` -- design v3(v2는 `draft_phase3_design_v2.md` 그대로 둠).
* `draft_p3_g1.spec.md`·`draft_p3_t0.spec.md`·`draft_p3_d0a.spec.md` -- 제자리 개정. 원본 사본 `*.spec.v2.md`(내용 동일 -- T0·D0a 원본은 CRLF, 사본은 LF. `diff --strip-trailing-cr` 차이 0, G1은 `cmp` 동일).
* `p3v3_g1_measure.py` → `p3v3_g1_results.json`: v3 이동 규칙(M-0~M-4·클래스 골격·문장) **참조 구현**, 합성 27단계(검토 반례 전부 + 인정·관찰 단계)에서 **base 게이트 도구 3개를 실제 실행**,
  v3 규칙은 모의. 실제 엔진 통째 이동 모의(거짓 거부 측정), 판정 기록 2건 무동작.
* `p3v3_facts.py` → `p3v3_facts.json`: N3.10 열·토큰, 중첩 참조, 인벤토리, 전수 스캔 이름, 문자열 import, `_SIZING_RECIPE`, 속성 덮어쓰기, V3 출력 키(HEAD·B28 판).
* 스펙 머리 검증: `PYTHONPATH=tools/gates $PY -c "role_paths.parse_spec_card(text, id)"` 세 card 모두 성공(절 11개씩).

작업 방식 고지: 두 측정 스크립트는 자기 JSON 결과를 `_drafts`에 직접 쓴다(v2 `p3v2_g1_measure.py` 선례). G1 card의 이름 치환 4곳은 `_drafts` 안에서 Python 문자열 치환으로 적용했다
(Write/Edit 도구 외 쓰기 1회 -- 내용은 아래 B1~B3 대응 그대로).

---

## Blocking

| # | 발견(요지) | 대응 | 위치 | 재실행 결과 |
|---|---|---|---|---|
| B1 | 덮어쓰기가 이동으로 분류됨 | **M-0**: u가 바인딩하는 이름마다 base p_h의 바인딩 출처가 없거나 `("def", p_b, 이름)`. 검토 제안("p_h가 q를 정의하지 않음")보다 넓게 **import 바인딩**도 막는다(base `b.py`가 `from c import f`면 호출자가 c.f를 보고 있었으므로 역시 덮어쓰기 -- `overwrite-import`). 원본을 import하던 경우(`absorb-own-import`)는 동작 불변이라 인정. M-2도 "p_b에 남은 바인딩은 p_h를 가리키는 재수출뿐"으로 강화. D0a `lost`는 (파일, 키, 해시) 기준, 덮어쓰기는 `changed`(목적)+`lost`(원본)+`move-rejected` M-0으로 함께 보고 | G1 계약 3·7(f)(g)·12, design §3 MOVED·§5.2, D0a 계약 4 | `overwrite`·`overwrite-import`·`swap` → M-0 거부, base = v3 exit(V3/V6/V7 1/1/0·1/1/1·1/1/0). `absorb-own-import` 1/1/1 → 0/0/0 |
| B2 | 자유 이름 재바인딩·`__file__` 디렉터리 변경이 이동으로 분류됨 | **M-4**: `global_names(u)`(symtable 유효 범위 규칙 + 데코레이터·기본값·기반·주석, 문자열 주석 포함)의 이름마다 base p_b의 바인딩 출처 = head p_h의 바인딩 출처, 또는 함께 옮긴 단위(고정점). 바인딩 출처 = `from` 사슬을 따라간 `("def", 파일, 이름)`; `__file__` = `("file-dir", 디렉터리)`(같은 디렉터리만 같음), `__name__` 등·`globals`/`eval`/`exec` = `("module-identity", 파일)`(항상 다름), `multi`·`star`·`cycle`은 경로 포함이라 이동에서 항상 다름. 측정 가능: `SourceIndex.global_names`·`binding_origin`을 G1 공개 계약으로. redteam 단계 `rebind`·`file-dir-change-noshim`. D0a는 `move-rejected`(규칙 이름 포함)로 보고(검토의 `rebind` 발견을 규칙 이름으로 일반화) | G1 계약 0~3·7(h)(i)·12, design §3·§5.2, D0a 계약 4 | `rebind` M-4 거부, `file-dir-change-noshim` M-4 거부(`file-dir-change`는 원본 자리 shim이 해석 불가라 M-2 거부), `local-shadow`(지역 이름이 원본 최상위와 같음) 인정, `move-chain` 인정. 실제 엔진 통째 이동(같은 디렉터리) 거짓 거부 0/402 단위 -- `stick_diagram` `__file__` 2곳 포함 |
| B3 | 클래스가 이동 판정 밖 | **클래스 골격 단위**: ClassDef 사본에서 클래스 안 모든 def를 `<method 이름>` 표지로 바꾼 `def_hash`(머리·데코레이터·기반·클래스 수준 문장·메서드 순서 포함). 메서드는 골격이 옮겨지고 자기 해시가 원본과 같을 때만 옮긴 def. MOVE-AST (a)의 원소 = 최상위 단위(함수·클래스·문장). `moved_defs` 반환에 `units`(클래스 포함) | G1 계약 3·7(j)·12, design §3, D0a 계약 2·4 | `class-exact` 1/1/1 → 0/0/0, `class-header-changed`·`class-field-changed` 1/1/1 유지(메서드도 대상). 메서드 없는 레코드 클래스(`record-class-*`)는 V3·V6·V7이 원래 보지 않음(0/0/0) -- `move_plan check` `changed`(골격 해시)가 잡는다 |
| B4 | `plan`의 이동 중·후 동작 미정 → D0b test·E4 불가 | 검토 두 안 중 **규칙 A-0 현재 위치**를 택하고 `verify` 부명령은 만들지 않았다(같은 판정을 두 명령으로 두지 않기 위해 -- REG-DEST를 `plan`의 `reg_mismatch`로 흡수). `--split` 파일 부재 = `absent_split` 보고(오류 아님, 오타는 E4가 `absent_split` 목록 대조로 잡음). Phase 전 구간 동작을 계약으로(이동 card를 차례로 적용한 커밋마다 배정 불변, shim 삭제 커밋에서 exit ≠ 2) | D0a 계약 2·8·9, design §2.4·§3 REG-DEST·§6.2 A-0·§10 E4 | 설계 문장 -- 도구가 없어 실행 불가. 전제 사실: A-0 대상 파일은 지금 트리에 없음(N3.10 파일 중 `stick_diagram.py`만 있고 split이라 A-0 밖) |
| B5 | E2가 파일 목록 `targets`를 잼 | E2 = V3 **재실행** JSON의 `defs` = `[]`(G1이 더하는 필드), `mutants` = 0, `move_rejected` 빈 사전 + `check` 발견 0 + V3 `moved` = `check` `moved_defs` + `moved_units` 목적지 = `assigned`. 판정 기록 `checks.V3`는 `{verdict, basis}` 자유 문장이라(스키마 실측) 기록에서 필드를 읽지 않고 도구를 다시 돌린다. **B28 의존**: HEAD와 B28 판(`dee338d`) 모두 출력 키 `tool, verdict, targets, mutants, killed, survivors`(B28은 ERROR에 `baseline_failed`만 추가) -- B28 뒤 키가 바뀌면 E2를 다시 잰다고 명시 | design §5.3-4·§10 E2, G1 계약 4, D0a 계약 4 | `p3v3_facts.py` `B5_v3_output_keys`, `_schema.json` `$defs.check` |
| B6 | design·D0a CLI 불일치 | D0a 계약 1을 **정본**으로(경로 인자는 커밋에서 `git show`, `--card <MOD 파일>|ALL`, `--rev`, `--allow-changed`), design §6.3은 요약표와 실제 인자 `MP_ARGS`(split 5·keep 1·`{"optimizer": "theta_search.py"}`)만. E2·E4·E6 명령이 `MP_ARGS`를 쓴다 | D0a 계약 1, design §6.3·§10 | -- |

## Should-fix

| # | 대응 | 위치 |
|---|---|---|
| S1 | 고침. redteam 20단계 표 = 단계 × 구성 × V3/V6/V7 base→병합본 exit × `moved`/`move_rejected`, 공통 픽스처 성질(인벤토리 없음·운영 루트 미도달·리터럴 3.7·`except Exception`) 명시. base exit는 합성 저장소에서 **실제 도구로 측정**한 값. `wrapper`는 미도달 픽스처라 V7 1(검토 지적대로 도달하면 0). `cache-together`의 red 원천은 g 안 리터럴(`len(` 검사가 파일 전체 텍스트라 캐시는 red를 못 만든다 -- `source_lint.py:129`) | G1 계약 12 |
| S2 | 고침. 기준 = 도구별 함수 호출 수(`moved_defs` 1, `read_tree` V3 ≤ 2·V6 ≤ 2·V7 = 2), `moved_defs` 입력은 소스 파일만(`SOURCE_GLOBS`/`_is_source`), `SourceIndex`가 파일당 `ast.parse`·`symtable` 1회. "V3가 base를 트리로 한 번 읽는다"는 뺐다(B28과 겹치는 편집을 줄이려고 base 파일 읽기 방식은 그대로) | G1 계약 0·10 |
| S3 | 고침. 문장 단위는 해시로만 식별(출력 키 `<stmt:해시 12자>`), 한 파일 안 중복·base 여러 파일 = 모호(M-1) | G1 계약 2·3, design §3 |
| S4 | 고침. 문서 개정(design 05 §10·계획 533행)은 **spec card와 같은 커밋(승인 전)**, 승인 `diff_path`가 spec card·design 05·계획서 세 경로(B28 승인 기록 두 줄 선례 실측) | G1 계약 13, design §9.1 |
| S5 | 고침. A-1은 `role_paths.read_section_table(plan, "### N3.10 ")`의 `대표 대상` 열(머리 실측 `ID, 파일, 책임, 대표 대상`), `mod_table`은 번호표만 -- 게이트 코드 무변경 | D0a 계약 2, design §6.2 |
| S6 | 고침(검토 제안보다 한 단계 정밀). R(u)는 `_refs`가 아니라 G1 `global_names`(모든 하위 유효 범위 + 문자열 주석) + 모듈 별칭 속성(u 전체)으로. 실측: 중첩 def·메서드 안에서만 다른 최상위 이름을 참조하는 최상위 단위 SR 17·SD 4. 합성 test에 "중첩 def 안에서만 상위 참조" 포함 | D0a 계약 3·oracle, design §6.1·§6.2 |
| S7 | 고침. 레코드 = `@dataclass`(이름·속성·호출) / 내장 예외·다른 레코드를 기반 / 메서드 없음. '받는' = 참조(문자열 주석 포함 -- `from __future__ import annotations` SR 35·SD 32행 실측, G1이 문자열 주석을 파싱해 넣는다) | D0a 계약 2 A-2 |
| S8 | 고침. "파일 텍스트 어디에도(주석·docstring 포함)" -- auditor `git grep`과 같은 기준, 사용 예는 가짜 이름 | D0a 계약 7 |
| S9 | 고침. M card는 `tools/**` 변경 0(명령으로 판정), 판정 도구는 D0a 병합 커밋의 `move_plan.py` 사본. 사본 실행이 가능하도록 D0a는 게이트 모듈을 `--root`의 `tools/gates`에서 import(계약) | design §2.4·§8 M행·§10·D-16, D0a 계약 1 |
| S10 | 고침. CACHE-ID = `check` `cache`(빈 dict 캐시는 `source_lint._is_empty_dict` 재사용, 주석 대입 포함 -- V6가 AnnAssign을 안 보는 것 실측), SHIM `is` 동일성 = `check` `shim`의 **정적** 형태(재수출 이름마다 shim 출처 = MOD 출처; 하위 프로세스 import는 체크아웃이 필요해 택하지 않음 -- 실행 중 속성 덮어쓰기는 S11/UD-7), MOVE-TOTAL = E6 `check --card ALL --allow-changed <M10 두 id>`. §3 표에 '판정 도구' 열 -- 빈 칸 없음 | design §3·§10 E2·E6, D0a 계약 4 |
| S11 | 고침 + 사용자 결정. §7.2 D군 = probe 6 + `workspaces` 진단 2(대입 12줄, 검토는 probe 6만 -- 저장소 전체 grep으로 2개 추가 발견). F8 실패 경로, UD-7(기본안: F1에서 덮어쓰기 대상을 `binding_origin`으로 찾은 호출자 모듈 전부로, F1 oracle에 그 대입 줄만 예외) | design §4 F8·§7.2·§8 F1·§9.2 UD-7 |
| S12 | 고침(결정). 실측: `run_harness.py::run` 인벤토리 60개 전부 이름 과대 근사(직접 호출자 12 = `_run_combo`·`_run`·`base_blob_text`·spice `run` 등, 하네스를 import하는 계약 test `test_restore_plan_functions`도 인벤토리에 없음) → 변이를 죽이지 못함 → **M10 = red-green** | design §2.3·§8 M10·D-15 |
| S13 | 고침. `_SIZING_RECIPE` 소비자 = 60(정의)·221·222·261·262뿐, docs·`.ai` 0 → T0에서 지운다. "229행이 계속 쓴다" 삭제 | T0 계약 4·작성 전 실측 5, design §7.1 |

## Minor

| # | 대응 | 위치 |
|---|---|---|
| m1 | `lru_cache` 데코레이터 1곳(248행) | design §2.2·부록 A M18 |
| m2 | 게이트 밖 호출 3곳 | design §5.2·부록 A G4 |
| m3 | B6로 해소(`--card <MOD 파일 이름>|ALL`) | D0a 계약 1 |
| m4 | A-1 토큰 규칙(식별자·글롭, `<파일>.py`, `<모듈>.<이름>`, 나머지 무시) + 실측 분류(식별자 41·파일 1·점 이름 1·무시 2, MOD7 산문뿐 → A-4) | D0a 계약 2, design §6.2 |
| m5 | `ast.parse` 호출 상한 = 그 실행이 읽은 커밋들의 소스 파일 수 합(계획서·레지스트리는 문자열 표 읽기) | D0a 계약 6 |
| m6 | T0 계약 9에 피할 토큰 전 목록(`m6_scan_names` 실측) + auditor 명령(`+` 줄 스캔) | T0 계약 9 |
| m7 | E3에 문자열 import 패턴 추가(10곳 실측), GONE-SHIM 정의에도 | design §3·§7.2·§10 E3 |
| m8 | 한 파일 안 같은 키·같은 문장 해시 = 모호(M-1). 최상위 블록 안 def는 옮긴 def 아님(보수적). 엔진 실측 중복 0 | G1 계약 3 |

## 검토 §2의 기타 지적

| 지적 | 대응 |
|---|---|
| (3) D0a: exit 2 기대 test가 도구 없는 base에서 `can't open file` exit 2로 통과할 수 있음 | D0a 계약 10(모든 test가 먼저 도구 존재·JSON 첫 줄 `"tool": "move_plan"` 단언) |
| (3) V4: D0b "레지스트리 열 = `plan` 출력" 동어반복 위험 | design §8 D0b 행에 oracle 둘(규칙 손적용 합성 표본 + 실제 트리 drift guard) 명시 -- 본문 작성은 D0b card |
| (3) T0 test-only 스키마: `red`·`equivalence` 필드 불가 | T0 판정 유형 근거에 `basis` 문장으로만 남긴다고 명시 |

## 사용자 결정(검토 §3)

| 검토 항목 | v3 |
|---|---|
| 1 UD-0 | 유지. 덮는 문서 개정 목록 갱신(G1 문구는 G1 spec card와 같은 커밋) |
| 2 UD-5 + 비용 선택 | **비교표와 권고 추가**: (가) 전역 이동 인식 규칙(권고) 대 (나) 승인 기록 선언 이동만. 근거 -- 두 방식 모두 선언 안에서도 M-0~M-4가 필요하고, Phase 3의 '선언'은 이미 이관표 + `check` `move-set`이 한다, (나)는 M card 8건의 추가 승인만 늘린다, (가)의 거짓 거부 0·반례 거부 13/13 실측 |
| 3 UD-6 | 유지(근거에 죽은 상수 삭제 추가) |
| 4 UD-1(U-03) | 유지 |
| 5 S11 probe 방침 | **UD-7** 신설(기본안 제시, 대안 '동작 안 하는 probe로 표시') |

UD는 5개(UD-0·1·5·6·7) -- UD-7만 새로 늘었다(검토가 사용자 몫으로 지정).

## 새로 드러난 것(검토 밖, v3에 기록)

* **같은 경로 import 재바인딩**은 지금 게이트도 보지 않는다(`same-path-rebind(observation)` base 0/0/0) -- G1의 M-4는 옮긴 def만 다룬다. 약화도 강화도 아님, 백로그 후보(design §5.4).
* **클래스 수준 문장(dataclass 필드 기본값)**은 V3·V6가 원래 보지 않는다(`record-class-default-changed` 0/0/0) -- 이동 card는 `check` `changed`가 잡는다, 같은 경로 변경은 백로그 후보.
* Python 3.14에서 `from __future__ import annotations`가 없으면 주석 이름이 `__annotate__` 별도 symtable에 들어간다(함수 표에 없다) -- G1 `global_names`는 주석 이름을 AST에서 따로 모은다고
  계약에 적었다(참조 구현이 처음에 이것을 놓쳐 수정 후 재실행, 결과 동일).
* `move-with-helper-import`(새 파일이 원본 모듈에서 import)는 G1이 동작 동일로 인정하지만 Phase 3에서는 `check` `order`가 거부한다 -- 게이트와 이동 도구의 역할 분담으로 기록.


---

# 초안 v3 → v4 개정 기록 (2차 검토 `review2_phase3_v3.md` 대응)

기준 HEAD = gate `master` `7535799`(B28 병합 `2b41e79`, 판정 기록 `8790b24`). 저장소 읽기 전용, 스크래치 `C:/g51`(끝에 삭제).

산출물(모두 `wt/_drafts/`):
* `draft_phase3_design_v4.md` -- design v4(v3는 `draft_phase3_design_v3.md` 그대로 둠).
* `draft_p3_g1.spec.md`·`draft_p3_t0.spec.md`·`draft_p3_d0a.spec.md` -- 제자리 개정. 개정 전 사본 `draft_p3_{g1,t0,d0a}.spec.v3.md`(`cmp` 동일 확인 후 개정).
* `p3v4_g1_measure.py` → `p3v4_g1_results.json`(+ 케이스별 누적 `p3v4_g1_results.partial.jsonl`): `p3v3_g1_measure.py`를 확장. v3 규칙과 v4 규칙을 같은 입력에서 나란히 재고,
  2차 검토 부록 B·§3 표의 새 반례 전부(+ S2·S5 반례, 인정 대조 `P-property-exact`·`N5ok`·`N6ok`) 24단계를 더해 51단계, 단계마다 합성 git 저장소에서 **HEAD `7535799`의 게이트 도구
  3개를 실제 실행**, v4는 D0a `check` 발견(changed·lost·def 단위 changed·stmt-order·future·rebind)까지 모의. 실제 엔진 4파일 통째 이동(v4 + check 모의), 판정 기록 2건 무동작.
* 스펙 머리 검증: `PYTHONPATH=tools/gates $PY -c "role_paths.parse_spec_card(text, id)"` 세 card 모두 성공(절 11개씩).

재측정 결과 요지(`p3v4_g1_results.json`):
* v3 규칙으로 잰 27단계 = 초안 v3 측정 27/27 동일(`v3_regression`) -- 참조 구현 확장이 기존 결과를 바꾸지 않았다.
* v4 규칙은 v3 27단계의 exit를 하나도 바꾸지 않는다(`v3_steps_v4_changed` 빈 사전).
* 적대적 반례 22건 전부 거부(`adversarial_summary`): G1 19건, `move_plan check` 발견만으로 3건(`same-path-rebind`·`S5-inplace-rebind-in-move-card` → `rebind`, `N6` → `stmt-order`).
  v3 규칙이 base보다 약했던 N1·N2·P·N3b·N4·N13·S2(`except as`)는 v4에서 base 도구와 같은 exit.
* 실제 엔진 통째 이동 거짓 거부 0: 단위 218/218·169/169·8/8·7/7, def 272/272·181/181·12/12·8/8, M-0h 위반 0, qualname 중복 제외 0, `check` 모의 발견 0. 판정 기록 2건 빈 결과.
* 알려진 보수 비용: `P-property-exact`(바이트 그대로 옮긴 property 클래스) v4 V3/V7 1 -- 엔진 qualname 중복 0이라 노출 0.

## Blocking

| # | 발견(요지) | 대응 | 위치 | 재실행 결과 |
|---|---|---|---|---|
| B1 | V3·V7이 옮긴 def를 `<경로>::<qualname>` 키로만 빼서 같은 키의 해시 다른 def(목적 파일 조건부 재정의, property getter)가 빠짐 | 검토의 세 수정 전부: (1) **M-0h**(= 검토 M-0'): u가 바인딩하는 이름마다 **head** p_h 출처 = `("def", p_h, 이름)` (2) p_b 또는 p_h에서 `iter_defs` qualname이 둘 이상인 def는 `defs`에 넣지 않음 (3) V3·V7 제외 대조 = (경로, qualname, `def_hash`) -- `moved_defs` 반환에 `def_hashes` 추가. G1 계약 7 (k)~(m), 계약 12에 `dest-conditional-redef`·`dest-lambda-rebind`·`augassign-rebind`·`except-as-rebind`·`property-getter-changed` 단계 | G1 계약 3·4·6·7·12, design §3 MOVED·§5.2 | N1·N1b·N2·S2 두 건 → M-0h 거부, base = v4 exit(1/1/1). P → `P.x` 중복 제외, V3/V6/V7 1/0/1 = base, `check` def 단위 `changed`도 잡음. 엔진 M-0h 위반 0 |
| B2 | `MP_ARGS` 문자열 전개가 `--aliases` JSON을 쪼갬 → E2·E4·E6 exit 2 | bash 배열 `MP_ARGS=(…)` + `"${MP_ARGS[@]}"`(검토 첫 안). `--aliases`의 JSON 모양(D0a 정본)은 유지 -- 테스트는 인자 목록으로 부르므로 셸 무관. D0a 계약 1에 셸 사용 문장 | design §6.3·§10 E2·E4·E6, D0a 계약 1 | 실측: 문자열 전개 `['{"optimizer":]`·`["theta_search.py"}']`, 배열 전개 마지막 원소 `{"optimizer": "theta_search.py"}`·`json.loads` 성공·인자 14개(design 부록 A B2) |

## Should-fix

| # | 대응 | 위치 | 재실행 |
|---|---|---|---|
| S1 | (a) 모듈 어디서든 `global` 선언된 이름 = `("global-dynamic", 경로, 이름)`(경로를 `unbound` 전체에 붙이지 않음 -- 검토가 잰 SR 24단위 거짓 거부 회피) (b) `ext`·`ext-module`에 가져오는 파일의 디렉터리 (c) star import가 하나라도 있으면 모든 이름(`__file__`·module-identity 제외) = `star`. 판정 순서를 계약 1에 명시 | G1 계약 1·7 (n)(o)(p)·12 `star-shadow`·`global-reader`·`ext-dir-change`, design §3 | N3b·N3 → M-0h(helper·g 둘 다 -- star 모듈), N4 → M-4, N13 → M-4. 엔진 star 0·global 0이라 거짓 거부 0 |
| S2 | 바인딩 = 모듈 공간 `Store`/`Del` 전부 + import(블록 안)·def·class·`except as`·`match` 포획·`type` 별칭(컴프리헨션 안 walrus 포함, lambda·컴프리헨션 지역 제외). 문장 단위 전역 읽기도 유효 범위 규칙(AST -- 3.14 `symtable`이 인라인 컴프리헨션 변수를 모듈 표 지역으로 넣는 것을 실측해 symtable 대신 AST로) | G1 계약 1·2, design §3 | `augassign-rebind`(v3도 거부)·`except-as-rebind`(v3 V3 0 → v4 1) M-0h. 엔진 거짓 거부 0 |
| S3 | M-4에 `__future__` 기능 집합 대조, D0a `check`에 `future` 발견(목적 ⊇ 원본), 엔진 사실에 TL 24행 | G1 계약 3 M-4·7 (q)·12 `future-dropped`(관찰 판정), D0a 계약 4, design §3·부록 A F | N5 → M-4 거부 + `future` 발견, N5ok(future 줄 유지) 인정 |
| S4 | `move-set` = 이 base→head의 **모든** 옮긴 단위 = 배정 집합, 목적지 전부 `--card`(`ALL`이면 목적지 = 배정 MOD) | D0a 계약 4, design §3 MOVE-AST (a)·§9.2 표 | 문언 -- `move-set`은 이관표가 필요해 모의 밖(design 부록 A 측정 한계) |
| S5 | `check`에 `rebind`: head의 모든 단위(옮긴 것·제자리, `changed` 제외)의 전역 읽기 출처 = base 출처(옮긴 단위 사상 적용) | D0a 계약 4, design §3 MOVE-AST (e)·§5.4 | `same-path-rebind`·`S5-inplace-rebind-in-move-card` → `rebind` 발견. 엔진 통째 이동에서 트리 전체 `rebind` 0 |
| S6 | M card 판정에 card마다 V3 JSON `defs` = `[]`·`move_rejected` = `{}`, `check` `changed`가 옮긴 클래스 안 def(qualname별 해시 목록)까지 | design §8 M행·§3 MOVE-AST (b)·§5.4·§10 E2, D0a 계약 4 | N7 → V3 대상 `C.m`(v3도) + def 단위 `changed`, P → def 단위 `changed` |
| S7 | 계약 8(b) = (단위 키 → `mod`) 사상 동일(파일 부분·`rule` 제외). 단위 키 정의: 문장 = 바인딩 이름 이름순 `,` 연결, 바인딩 없는 문장 = `<stmt:해시12>` | D0a 계약 2·8 | 문언 |
| S8 | 줄 번호·상태 갱신(`changed_defs` 88~100, `make_clone` 53·323, cat-file 359, `base_src` 361, 호출 364, diff 314, `_rmtree_force` 406, 출력 398·402·407), B28 병합 완료, `copytree` → `make_clone`, redteam `31-v3-git-history` 다음 번호. P9·P10 뒤 엔진 줄 재측정 조건을 design 머리에 | G1 의도·계약 11·12·작성 전 실측 1·2, design 머리·§5.1·§5.3·§9.1·부록 A S8·H, D0a·T0 작성 전 실측 머리 | `7535799`에서 재측정 일치. `git diff --stat cd64170 HEAD -- A/*.py run_harness.py docs/01-plan` 0 |

## Minor

| # | 대응 | 위치 |
|---|---|---|
| m1 | D군 대입 14줄(probe 12 + workspaces 2) | design §7.2·D-17·부록 A S11 |
| m2 | `check` `stmt-order`(같은 원본 → 같은 목적의 옮긴 문장 단위 상대 순서 보존). 모의: N6 → 발견, N6ok 인정 | D0a 계약 4, design §3 MOVE-AST (g) |
| m3 | `shim` 발견에 base의 `if __name__ == "__main__"` 블록 제거·변경 포함(엔진 4파일 main 블록 0) | D0a 계약 4, design §3 SHIM |
| m4 | E6 base = M1 판정 기록 `base_commit`(D0b 병합 뒤) | design §10 E6 |
| m5 | E2 ③을 '일관성 점검(증거로 세지 않음)'으로 | design §10 E2 |
| m6 | 사본 출처 하나: `tools/migrate/move_plan.py`를 마지막으로 바꾼 판정 기록의 `code_commit` | design §2.4·§8 M행·§10·D-16, D0a 계약 1·작성 전 실측 4 |
| m7 | redteam 단계에 `"observe": "moved"` → `vcase`가 `{moved, move_rejected 규칙}`을 `observed`로 기록, `expect.observed_equals`(`run_all.py:98`)로 대조. `rt.py` 추가는 test-author | G1 계약 12 |

## redteam 번호 배정(요청 사항)

`ls tools/gates/redteam/attacks` 마지막 = `31-v3-git-history`(B28). `_drafts/draft_b33.spec.md`는 **없다**. B33 준비 문서 `prep_b33_v7_edges.md` 278행이 "`<다음 번호>-v7-graph-edges`(B28 31, G1 32
예정이면 그 다음)"이라 적었으므로 **G1 = `32-moved-defs`, B33 = `33-v7-graph-edges`**로 미리 나눴다(design v4 §5.3-5·D-18, G1 계약 12·작성 전 실측 2). 병합 순서와 무관하게 두 card가
같은 번호를 쓰지 않는다. B33 spec card를 쓸 때 33을 쓰고 `ls attacks`로 비었는지만 확인한다.

## 사용자 결정(2차 검토 §5)

| v3 | v4 |
|---|---|
| UD-0·1·5·6·7(5개) | **UD-0·1·5**(3개). UD-7 → **D-17**(probe 기능 보존이라 원칙으로 확정, UD-0이 덮음, 대안은 사용자가 원할 때만). UD-6 → '뒤에 올 승인'(T0 test 커밋 뒤 diff 해시로 -- T1·F1과 같은 기준, T0 card '결정 필요 항목' 문구도 바꿈) |
| UD-5 근거 "옮긴 단위는 바이트·전역 출처가 같아 동작이 같다(M-4)", "반례 거부 13/13" | v4 수치로 다시 씀: v3 27단계 exit 불변, 2차 검토 약화 7부류 모두 base exit로 복귀, 새 반례 22/22 거부(G1 19 + check 3), 엔진 통째 이동 거짓 거부 0(402/402·473/473, M-0h 위반 0). 규칙은 완전성 증명이 아니라 측정이므로 Phase 3 안의 두 번째 선(`check` + card별 V3 `defs` = `[]`)을 근거에 명시. (나)도 N1·P·N3b·N4·N13·N5는 선언 안에서 일어나 막지 못한다는 비교표 결론 유지 |

## 새로 드러난 것(검토 밖, v4에 기록)

* Python 3.14 `symtable`은 인라인 컴프리헨션(PEP 709) 변수를 모듈 표의 지역·대입 기호로 넣는다(`X = [t*K for t in range(3)]` → 모듈 표에 `t`). 그래서 문장 단위 전역 읽기·바인딩은 `symtable`이
  아니라 AST 유효 범위로 센다(G1 계약 2, design 부록 A F). 검토 S2 제안("symtable 모듈 표로")을 이 실측 때문에 AST로 바꿨다.
* qualname 중복 제외(B1 (2))는 바이트 그대로 옮긴 property 클래스도 `P.x`를 V3·V7 대상에 남긴다(보수 비용, `P-property-exact`). 엔진 노출 0이라 받아들이고 G1 '거부해야 할 입력'에 적었다 --
  더 정밀한 안(qualname별 해시 목록이 원본과 같으면 제외)은 계약이 복잡해져 택하지 않았다.
* `N6`(옮긴 최상위 문장 순서 교환)은 base V6 1 → v4 0이다(옮긴 문장은 원본 맥락으로 센다). G1만으로는 '인정'이고 `check` `stmt-order`가 거부한다 -- 엔진 최상위 문장은 이름 대입뿐(검토 부록 A)이라 노출 0.

# 초안 v4 → v5 개정 기록 (v4 뒤 확정된 결정·card 반영, 2026-10-01)

대상: `draft_phase3_design_v5.md`(새 파일 -- v4는 `draft_phase3_design_v4.md` 그대로 사본으로 남김), `draft_p3_g1.spec.md`·`draft_p3_t0.spec.md`·`draft_p3_d0a.spec.md`(고치기 전 사본
`*.spec.v4.md`), 이 기록(사본 `phase3_revision_log.v4.md`). 저장소 HEAD `7535799`(변화 없음), 저장소·worktree 쓰기와 상태 변경 git 없음, 스크래치 `C:/g71`(끝나면 삭제).
B26-1·B34·B33·면제 묶기·범위 정책은 모두 **병합 전 초안**이라 그 card들이 바꿀 사실은 초안에서 추정했고 문서에 'Phase 3 시작 때 재측정'으로 표시했다(추정치를 판정 근거로 쓰지 않는다).

## (a) 사용자 결정 A2 -- B26-1·B34를 Phase 3 전에 병합

| 항목 | 대응 | 위치 |
|---|---|---|
| 착수 조건 | B34 → B26-1 병합을 M1 착수 조건으로. 승인 기록 `20260930-b26-before-phase3` '재검토'(병합 안 된 채 M card 시작 시 앞당김 효력 상실) 인용 | design §6.4 머리·§9.1 |
| D0b 재측정 조건 | 이관표·`reg_mismatch`·PLAN-LAYER는 B26-1·B34 병합 뒤 master에서 **처음** 계산, 그 전 실제 저장소 `plan` 출력은 참고 관찰 | design §6.4 끝·§8 D0b행·§9.1 (3), D0a 의도 |
| 바뀌는 사실(추정) | SD Class 28→29·Func 132→133, 통째 이동 단위 402→404·def 473→474, 엔진 클래스 41→42(dataclass 37·메서드 없음 37), 행 없는 정의 SD 24→26, 바뀌는 def(B34 4, B26-1 SD 18·SR 2 시그니처 + 본문), SD `__file__`·future·SR 캐시 줄 이동, `run_harness.py`·`topology_library.py:248` 불변 확인만 | design §6.4 표, 머리 재측정 조건 (1), G1·D0a '작성 전 실측' |
| 배정(MOD) | **D-19**: `rail_declaration` → N3.10 MOD2 '대표 대상' 추가(A-1, UD-0 문서 개정). 규칙만이면 A-5로 MOD3(유일 운영 호출자 `load_topology`가 A-3로 MOD3)인데 MOD2 책임 "스키마·…선언… 게이트"와 어긋남. `RailDeclaration`은 A-2로 MOD2(MOD2 함수의 `rails: RailDeclaration` 주석이 위쪽 참조가 되지 않게). B37a `port_declaration`도 같은 MOD2(B37a 초안 "`rail_declaration` 옆"·"MOD2 쪽"과 일치 -- 확인만). `_import_analog_grammar`는 A-4/A-5, `__file__` 같은 디렉터리라 G1 인정, B34 계약 3 경로(`stick_diagram.__file__` 디렉터리)도 그대로 | design §6.4·D-19·UD-0·§11-7, D0a 의도 |
| 계약 test | B26-1 계수 test(`stick_diagram.rail_declaration` 모듈 속성 교체)는 M3에서 깨지는 **A군**(V1 수집 test라 FAIL → F6) → T0 계약 10. B34 test(`stick_diagram.<이름>` 직접 호출)·B26-1의 `sizing_recipe._metric_kcl_residual` 이름 호출은 **B군** → F1 | design §7.1 v5 행, T0 의도·계약 1·8·10·작성 전 실측 7·8 |
| D군 측정 | S11은 대입문만 센다 -- HEAD `setattr` 0건 실측(v4 결론 유지), Phase 3 시작 때 대입문 + `setattr` 두 형태로 재측정 | design §7.2, 부록 A E3 |
| T0 순서 | T0 base = P9·B34·B26-1 병합 뒤(계약 10 때문) | design §8.1, T0 작성 전 실측 머리 |

## (b) V3 면제 묶기·범위 정책(N2 + 넓힌 T6) -- G1 전 병합

| 질문 | 결론 | 위치 |
|---|---|---|
| 합성 문장의 주인 | 셋 다 G1보다 먼저 → **G1이 나중 card로서 합성 문장을 가진다**(범위 정책 card '결정 필요 항목' 규칙). 범위 정책 card가 표시한 G1 문장(계약 4 "나머지 대상 선택은 지금과 같다(…`changed_defs`와 같은 결과…)")을 고쳤다: 대상 def 집합 = `changed_defs` 결과 − 옮긴 def, **def 안 변이 선택 = `20260930-v3-changed-stmt-scope` 계약 1 그대로** | G1 의도·계약 4, design §5.5.1 |
| 옮긴 def 제외 대 N2 | 먼저 제외, 그다음 N2. 옮긴 def는 대상 def가 아니므로 `not_targeted`·`targets_by_def`에도 없음. 범위 정책 계약 2(바뀐 기존 def마다 대상 ≥ 1)와 충돌 없음(옮긴 def는 '해시가 바뀐 기존 def'가 아님) | G1 계약 4, design §5.5.2 |
| 옮기며 바뀐 def·거부 후보 | **D-20**: 새 경로의 새 def(본문 전체). 이동 원본과 문장 단위로 맞추지 않는다 -- A1-b 약화 승인은 같은 경로의 기존 def만 덮음, Phase 3는 옮기며 바꾸지 않음(F2), 거부 판정을 무르지 않음 | G1 계약 4·12 합성 관찰, design §5.2·§5.5.2·D-20 |
| 옮긴 def의 면제(해시 같으면 유효?) | 변이 id 모듈 = 파일 줄기(실측 `mutate_changed.py` 362·374, `reachability.module_name` 47). 옮긴 def는 대상이 아니라 대조 없음. 거부 후보는 새 모듈 id라 옛 원소 미적용(fail-closed) -- 필요하면 `<새 모듈>:…@<같은 묶기 해시>`로 재승인. 이동 뒤 변경은 묶기 해시가 바뀌어 미적용. **D-21**: G1은 면제 대조를 바꾸지 않는다. 누수 경로 없음 | G1 계약 4·작성 전 실측 7, design §5.5.3·D-21, 부록 A E2 |
| 정의 하나 | 묶기 해시(docstring 포함)는 이동 판정의 `def_hash`와 별개 정의 -- G1은 섞지 않음 | G1 계약 8, design §2.4 |
| 출력 키·E2 | 범위 정책 `not_targeted`·`targets_by_def`, 면제 묶기 `exempt_ignored`·`survivor_bindings`는 이름·뜻 유지. M card·E2 기준에 `not_targeted` = 0·`targets_by_def` = `{}` 추가(면제 키는 기준 아님) | G1 계약 4, design §5.2·§8 M행·§10 E2 |
| redteam 기대 | 29단계 V3 exit는 범위 정책 뒤에도 불변으로 봄(합성 저장소에 test 없음 → 대상 ≥ 1이면 전부 생존, 대상 0은 '옮긴 def만'). 합성 관찰에 `defs`·`not_targeted` 추가(red 단계 병합본 `[]`·0, `move-edited`·`class-*`·거부 단계 `not_targeted` = 0 -- D-20 확인). base 열은 병합본 도구로 재측정 | G1 계약 12·작성 전 실측 7, design §5.5.2 |
| 문서 개정 | design 05 §10 V3 ①은 범위 정책·면제 묶기가 고친 문구 **뒤에** G1 구절을 더함(그 문구를 지우지 않음) | G1 계약 13 |
| 순서 문장 | G1 '결정 필요 항목'에 순서(셋 뒤)와 순서가 바뀔 때의 규칙. 범위 정책은 A1-b로 확정 -- G1은 그 card 계약 1을 인용만 | G1 결정 필요 항목 |

## (c) B33(V7 그래프 간선) -- G1 전 병합

| 항목 | 대응 | 위치 |
|---|---|---|
| 판정 효과 | 독립(B33 = 무엇이 도달하는가, G1 = 무엇이 새 def인가). G1은 `build_graph`·도달 계산을 바꾸지 않음, B33 redteam 전 단계를 G1 무동작 입력에 | G1 계약 6·11, design §5.5.4 |
| 바인딩 노드 | `<파일>::=<이름>`은 def가 아니라 `moved_defs`·`new_defs`에 안 나옴. 옮긴 레지스트리 문장은 새 파일 바인딩 노드가 되고 shim 경유 참조는 B33 R1 재수출 해석이 이음 -- 검토 `review_b33.md` S3(옛·새 모듈 같은 이름 공존 = Phase 3 중간 상태)이 권한 chase 판이 맞다고 적음(최종 문언은 B33 card) | design §5.5.4 |
| R3 | `moved_defs` 입력과 같은 `_is_source` | G1 계약 6, design §5.5.4 |
| 수치 | F5·§5.1 'V7 미도달 약 108' → B33 뒤 재측정(시제품 추정 약 39, 소스 전체 기준). §5.4 첫 항목(`__init__`·레지스트리 간선 백로그)은 B33이 닫음. 줄 번호(`build_graph` 97~, `main` 223~231)는 G1 착수 때 재측정 | design §4 F5·§5.1 주의·§5.4·§11-6, G1 의도·작성 전 실측 머리 |
| 비용 | B33은 V3 인벤토리를 키움(쌍 33,991 → 79,809), M card V3는 `defs` = `[]`이라 무관 | design §5.5.4 |

## (d) redteam 번호

G1 `32-moved-defs`(그대로), B33 `33-v7-registry-edges`(v4의 `33-v7-graph-edges`를 B33 card 꼬리로), 면제 묶기 `34-v3-exempt-binding`, 범위 정책 `35-v3-changed-scope`. D-18·§5.3-5·G1 계약 11·12·
작성 전 실측 2(착수 때 33·34·35 있음, 32 없음 확인) 갱신.

## 다른 초안에 넘기는 것(이 작업은 고치지 않았다)

* `draft_b33.spec.md`: `attacks/32-v7-registry-edges` → `33-…`, '순서' 절의 "먼저 병합하는 card가 32"를 오케스트레이터 배정으로.
* `draft_v3_exempt_binding.spec.md`: `32-v3-exempt-binding` → `34-…`(78·148·192행 부근), '결정 필요 항목'의 G1 번호 겹침 문장 정리.
* `draft_v3_scope_policy.spec.md`: `33-v3-changed-scope` → `35-…`, 계약 7의 `32-v3-exempt-binding` → `34-…`, 계약 3·'결정 필요 항목'의 G1 조건문을 확정 문장으로(G1이 나중 -- `review2_v3_cards.md` S7). G1 쪽 문장은 이번에 반영했다.
* `draft_b37a.spec.md`: 접근자 모듈 = MOD2(`topology_authoring.py`, D-19) -- 초안 문장과 일치, 확인만.

## 머리 블록 재검증

`role_paths.parse_spec_card(text, id)`(저장소 `tools/gates`, `$PY` 3.14.2) 세 card 모두 통과: G1 `phase 0.5`·`red-green`·`gate_change yes`·approval 1, T0 `phase 3`·`test-only`·`no`·approval 2,
D0a `phase 3`·`red-green`·`no`·approval 1, 절 11개씩(의도 / 관찰 가능한 계약 / 신규 시그니처 / 판정 유형 근거 / oracle 종류와 출처 / 거부해야 할 입력 / library 회로 적용 여부 /
무동작 판정 입력(무발동 값) / 재현할 수치 / 결정 필요 항목 / 작성 전 실측).

## 측정(읽기 전용, `7535799`)

* `git rev-parse --short HEAD` = `7535799`.
* `grep -n "mid\|modname" tools/gates/mutate_changed.py` → 362 `modname = rch.module_name(path)`, 374 `mid = "%s:%s:%s:%s" % (modname, q, opname, npath)`, 375 면제 대조; `reachability.py` 47 `module_name`.
* `git grep -n setattr HEAD -- '*.py'` → 0건; `git grep -n "monkeypatch\." HEAD -- skills/analog-gmid-design/assets/tests` → `test_df36_instance_relpath.py` `chdir` 4건.
* `grep -n "^def …"` → `load_topology` SD 8550, `_import_analog_grammar` SD 1045, `true_current_mirror_groups` SR 2191, `resolve_stack_layout` SR 6470. N3.10 표 515~531행(MOD2 책임).
* `ls tools/gates/redteam/attacks | tail -3` → `29-v4-decision-exempt`, `30-rejudge-cache`, `31-v3-git-history`.

# 초안 v5 → v6 개정 기록 (3차 검토 `review3_phase3_v5.md` 대응, 2026-10-01)

대상: `draft_phase3_design_v6.md`(새 파일 -- v5는 그대로 둠), `draft_p3_g1.spec.md`·`draft_p3_t0.spec.md`·`draft_p3_d0a.spec.md`(고치기 전 사본 `*.spec.v5.md`, `cmp` 동일 확인 후 개정),
이 기록(사본 `phase3_revision_log.v5.md`), 새 문서 `p3_doc_amendments.md`(UD-0 문서 개정 문안)·`phase3_approval_question.md`(승인 질문). 스크립트·결과는 `p3_scripts/`.
저장소 HEAD `7535799`(변화 없음), 저장소·worktree 쓰기와 상태 변경 git 없음. 측정은 `C:/g73/repo`(`git clone --no-hardlinks`)와 그 아래 모의 트리, 끝나면 `C:/g73` 삭제.

## Blocking

| # | 발견(요지) | 대응 | 위치 | 재실행·실측 |
|---|---|---|---|---|
| B1 | D0a `order`가 split이자 MOD7인 `stick_diagram.py` import를 위반으로 잡아 M8·M9 통과 불가 | N3.10 파일은 split이어도 N3.10 번호로 판정, N3.10 밖 split 파일만 금지, 그 밖 트리 파일은 판정 밖. D0a 합성 단계 `order-split-n310-lower` 추가 | design §3 ORDER·§5.2 인정 단계 문장, D0a 계약 4 `order`·oracle·거부 입력·작성 전 실측 8 | `p3v6_order_shim_sim.py`(실제 import `sizing_recipe.py:5302`·`design_report.py:32`를 가진 M1~M9 모의 트리): 옛 문언 M8·M9 발견(`stick_diagram.py`), 새 문언 M1~M9 발견 0 -- 배치·보정 변형 6개 모두 |
| B2 | D0a `shim`이 잔여 정의 있는 중간 card마다 발견, 최종 shim `__future__`도, 무동작 문장과 모순 | (a) 중간 상태 = base에 없던 최상위 문장은 재수출 줄뿐 (b) 완전 shim(단위 0)만 docstring·재수출·`__future__`·main 블록 (c) 이름 집합·출처(`ALL`은 이름 집합 제외) (d) main 블록. 무동작 문장에 정합 이유 추가. 합성 단계 `shim-partial-move`·`shim-complete`·`shim-all-mode` | design §3 SHIM, D0a 계약 4 `shim`·무동작·oracle | 같은 모의: 옛 문언 M1~M9 모두 발견(SR 214→…→1(`__future__`)·TL·DR), 새 문언 M1~M9 발견 0. 완전 shim TL M4, SR M8/M9, DR M9 |
| B3 | DoD E3 명령이 표 칸 `\|` 때문에 공허 PASS | E0~E6 명령을 bash 블록 하나로(표는 ID·기준만), E3 거부 확인(B0에서 import 문장·호출 모두 비지 않음), E3를 AST로(D-24), `GC`·`--gmid-phase=3`·`--gmid-strict` 정의(m2), `import_any`(IMPORT-ANY) | design §10 전체, 부록 A F2v6·F3v6 | 원문 `\|` 0파일 대 57, 문자열 0 대 6. **새로 드러남**: 정규식(`|`로 고쳐도)은 `import numpy as np, sizing_recipe as sr` 6파일을 놓친다(57 대 AST 63, 엔진 4모듈 86 대 92) → F1 목록·E3를 AST로. `p3v6_sec10_selftest.sh`가 문서의 E3·`import_any` 블록을 잘라 그대로 실행: HEAD에서 E3 `INVALID` 없음·`FAIL`(거부 동작), `import_any` HEAD 실패 0 |
| B4 | UD-0 문서 개정 문안 없음, N3.10 개정 시점 모순, `validate_theta_declaration_order` 목적지 미정 | `p3_doc_amendments.md`(계획 N3.10 4행·534·687, `00-common` 103·431, `10` §5.6 250·252 -- 현재 원문·줄 번호 + 새 문안, D-19 두 안). UD-0 = 지금 계산 가능한 3건 + D-19, D0b 추가 개정은 따로 승인(권고 (가), D-11). `validate_theta_declaration_order` → MOD3(두 피호출 함수가 레지스트리 A-4 MOD3) | design §6.2·§8 D0b행·§9.1·§9.2·D-11·§11, D0a 의도·결정 필요 항목, T0 판정 유형 근거·작성 전 실측 5 | `p3v6_amend_check.py`: '현재' 블록 10개 = 실제 줄, 두 안 모두 표 파싱·`mod_table` 10·두 행 걸친 토큰 0·`import_layering` exit 0·10 §5.6 21행. **새로 드러남**: MOD6 행 `` `optimize_full_circuit_budget` 탐색부 ``는 A-1이 함수 전체를 MOD6로 보낸다(모의 근사 배정도 A-1 MOD6) → 백틱을 MOD8 행으로 옮기는 문안. 설명 문장 함수 이름은 백틱 없이(두 행 걸침 방지). `00-common` 103행은 §3.2가 아니라 §3.3 표 |

## Should-fix

| # | 대응 | 위치 |
|---|---|---|
| S1 | 번호 33·34·35는 세 초안에 이미 반영(131·144·160 / 82 / 89행)으로 사실 갱신, B33 chase는 34행 최종 문언 인용(R2'·계약 9 개정 반영), 인벤토리 44,493(79,809는 v1). 인계 목록에서 번호 정정 삭제 | design §5.3-5·§5.5.4·§11-8, G1 작성 전 실측 2 |
| S2 | §9.1 남은 것 = P9·P10·P10b·B34·B26-1 + DoD E0~E5(게이트 card는 G1 선행), D-23(T0·D0a·D0b 병합 = Phase 2 DoD 뒤, 그 전 준비만), §8.1을 필수 순서 표 + 편의 그림으로 | design §8.1·§9.1·D-23, T0 의도, D0a 의도 |
| S3 | M10 V3 비용: 회로 = E-INST 한 판이 가장 짧은 library 회로(기록 `folded_cascode` 13~19초, telescopic 98~137초, 파일럿 7~8분), `run` 인벤토리 60 id 한 번 실행 **143초 실측**, 추정 30~40분(최악 3.2시간; 파일럿이면 9시간 이상), M10 '작성 전 실측' 3항목, D-25 | design §2.3·§8 M10행·D-25, 부록 A F4v6 |
| S4 | D-19 근거를 '선언 게이트 + B37a 같은 곳'으로 좁히고 `RailDeclaration` 문장은 근거에서 뺌, 한계(`validate_theta_declaration_order` MOD3) 기록, 두 안 중립 -- 따로 질문 | design §6.4·§9.2·D-19, 질문 D-19 |
| S5 | G1 31~32행 base 문장 정정, 세 card의 'design v4/v5' 인용 → 'design 30'(G1 14·T0 6·D0a 20곳), '(초안 v5)' → v6 | G1 의도, 세 card 전체 |
| S6 | 26단계·26/26·51 = 26 + 25(원자료 키 계수 재확인 F5v6) | design 머리·§5.2·§9.2·부록 A G5·G5'·부록 C, G1 작성 전 실측 1·결정 필요 항목 |
| S7 | 문자열 import = 호출 9곳 + docstring 1(`test_d_move_tests.py:37`), F1 범위 9곳, E3는 AST 호출(D-24)이라 docstring에 걸리지 않음 | design §7.2·§8 F1행·§10 E3 |
| S8 | UD-1 대안 (나) 추적 추가 후 F1 갱신 (다) 삭제, 두 import(9·10행) 명시 | design §9.2, 질문 UD-1 |

## Minor

| # | 대응 | 위치 |
|---|---|---|
| m1 | card 수 16 | design §8 |
| m2 | `GC` 정의(05 §4.4), V3에 `--python`·`--gmid-phase=3`·`--gmid-strict=`(10 §6.10 428행 V1과 같은 값) | design §10 |
| m3 | F2는 SD 자신이 읽지 않는 이름의 재수출만 지움 | design §2.2·§8 F2행 |
| m4 | D0b 계약 test에 'SD 밖 split 단위의 MOD7 배정 0' 단언(모의 근사 배정에서도 0) | design §8 D0b행 |
| m5 | §8.1 필수/편의 순서 분리(B34와 34·35 사이 자유) | design §8.1 |
| m6 | B34 초안 212행 "M2" 단정 → 'D0b 이관표가 정한다' 인계 문장(B34 초안은 고치지 않음) | design §6.4·§11-8 |

## 검토 §7 -- 승인 질문

UD-0 질문에 D-9·D-17(기준에 닿는 기본값)과 '추가 표 개정 위임하지 않음'(선택지로 '승인 + 위임'을 중립으로 둠)을 드러냄. D-19 따로, UD-5·UD-1 대안 포함 → `phase3_approval_question.md`.

## 새로 드러난 것(검토 밖, v6에 반영)

* **M9~F1의 순환 import(D-22)**: N3.10이 `save_instance_json` 계열 SD 단위를 MOD9로 보내고 추적 test·하네스가 그 이름을 F1까지 `stick_diagram`에서 읽으므로 SD가 MOD9를 임시 재수출한다
  → SD(7) → MOD9 위쪽 import, MOD9 → SD·MOD8 → SD와 순환. 모의 `pull_top`(import 줄 모두 머리): M9에서 `instance_report_builder`·`design_report`를 먼저 import하면 `ImportError`(부분 초기화).
  V1이 SR을 먼저 import하면 숨어 있다가 F1(test가 MOD9를 직접 import)에서 터진다. 규칙: split 재수출은 import 머리 뒤, SD의 MOD 8·9 재수출은 SD 끝, MOD8·MOD9의 번호 7 이상 import는 파일 끝 →
  `pull_bottom7`에서 M1~M9 모듈별 단독 import 전부 성공(`bottomall`은 MOD9 레지스트리 문장 `NameError` -- 7 미만 import는 머리에 둬야 한다). M card·F1·E5에 IMPORT-ANY(`import_any`) 판정 추가.
  M9 트리 `import_layering` FAIL(위쪽 import·순환)은 F2가 SD 재수출을 지우면 사라진다 -- LAYER는 F2 뒤 판정으로 명시.
* 재수출 줄을 split 파일 **끝**에 두면 M8에서 SR 모듈 수준 문장이 옮겨진 이름을 읽어 `NameError`(첫 모의) -- 재수출 위치 규칙(import 머리 뒤)으로 명시.
* 줄 머리 import 정규식이 `import a, sizing_recipe` 모양을 놓침(6파일, 전부 probe -- V1 미수집이라 조용히 깨질 곳) -- E3·F1 목록을 AST로, 다른 정규식 계수는 백로그 후보(design §11-9).
* N3.10 MOD6 행의 백틱 `optimize_full_circuit_budget`가 A-1로 함수 전체를 MOD6에 보낸다 -- 개정 문안이 토큰을 MOD8로 옮김(B4).
* 측정 환경 메모: 이 작업 환경의 하위 bash에서 `APPDATA`가 비어 사용자 site-packages(numpy)가 안 보였다 -- 모의·자가 시험 스크립트에 `PYTHONPATH`를 명시했다(문서 명령의 일부 아님).

## 머리 블록 재검증

`role_paths.parse_spec_card(text, id)`(복제본 `tools/gates`, `$PY` 3.14.2) 세 card 모두 통과: G1 `phase 0.5`·`red-green`·`gate_change yes`·approval 1, T0 `phase 3`·`test-only`·`no`·approval 2,
D0a `phase 3`·`red-green`·`no`·approval 1, 절 11개씩.

## 산출물·스크립트(`_drafts/`)

* `draft_phase3_design_v6.md`, `draft_p3_{g1,t0,d0a}.spec.md`(사본 `*.spec.v5.md`), `p3_doc_amendments.md`, `phase3_approval_question.md`, 이 기록(사본 `phase3_revision_log.v5.md`).
* `p3_scripts/p3v6_order_shim_sim.py` → `p3v6_order_shim_sim.{json,top,bottom,bottomall,bottom7,pull_top,pull_bottom7}.json`(+ `.partial.jsonl`): B1·B2·D-22 모의.
* `p3_scripts/p3v6_e3_check.sh` → `p3v6_e3_check.out.txt`, `p3_scripts/p3v6_sec10_selftest.sh` → `p3v6_sec10_selftest.out.txt`: B3.
* `p3_scripts/p3v6_m10_inventory_time.py` → `p3v6_m10_inventory_time.json`: S3.
* `p3_scripts/p3v6_amend_check.py` → `p3v6_amend_check.json`: B4.
* 편집 보조 `p3_scripts/v6_splice.py`와 조각 `*.md.part`(문서에 그대로 들어간 원문).

## 기준 커밋 이동(작성 중)

작업 시작 때 gate `master` = `7535799`였고 끝날 때 `a796468`이었다(P9 병합·판정 기록 `766b5c2`, P10 판정 기록 `62ae24f`, 계획 A2 정정 `8356c1e`, P10b spec card -- 이 작업이 만든 커밋 아님).
`a796468` 복제본에서 다시 확인: `p3v6_amend_check.py` '현재' 블록 10개 일치·두 안 결과 동일(`p3_scripts/p3v6_amend_check.a796468.json`), `p3v6_e3_check.sh` 수치 동일(문장 69줄·63파일, 호출 9줄·5파일),
`sizing_recipe.py:5302`·`design_report.py:32` import 그대로, 레지스트리 129·131행 그대로, `tools/gates` 무변경, 엔진 변경은 `stick_diagram.py` −11줄(P9)뿐. design §9.1의 Phase 2 남은 목록을 `a796468` 기준으로 고쳤다
(P10b·B34·B26-1 + DoD E0~E5). 모의(`p3v6_order_shim_sim`)·M10 인벤토리 시간은 `7535799` 측정 그대로다(SD 줄 이동만 -- 결론 영향 없음으로 보지만 Phase 3 시작 재측정 대상).


---

# 초안 v6 → v7 개정 기록 (4차 검토 `review4_phase3_v6.md` 대응 + 오케스트레이터 확정 순서, 2026-10-01)

대상: `draft_phase3_design_v7.md`(새 파일 -- v6은 그대로 둠), `draft_p3_g1.spec.md`·`draft_p3_t0.spec.md`·`draft_p3_d0a.spec.md`(고치기 전 사본 `*.spec.v6.md`),
`phase3_approval_question.md`(사본 `phase3_approval_question.v6.md`), `p3_doc_amendments.md`(사본 `p3_doc_amendments.v6.md`), 이 기록(사본 `phase3_revision_log.v6.md`).
저장소 HEAD = gate `master` `a796468`(변화 없음), 저장소·worktree 쓰기와 상태 변경 git 없음. 측정은 `C:/g95b/repo`·`C:/g95b/repo_m10`(`git clone --no-hardlinks`)과 그 아래 모의 트리·합성 커밋,
끝나면 `C:/g95b` 삭제. 스크립트는 `p3_scripts/p3v7_*`.

## Blocking

| # | 발견(요지) | 대응 | 위치 | 재실행·실측 |
|---|---|---|---|---|
| N1 | F2가 SD 임시 재수출을 지운 뒤 깨지는 추적 파일(V1 밖 다수)을 DoD·F1·F2가 보지 않음 | **E3b**(SD-NAMES, D-26): D-9 제외 집합 밖 추적 `.py`가 SD에서 읽는 이름(`from stick_diagram import N`, SD 모듈 식 = `import stick_diagram [as a]`·`import_module("stick_diagram")`·`_import`·`__import__`·그것을 대입받은 이름·그것을 돌려주는 함수 호출의 속성 `.N`, `getattr`/`hasattr`/`setattr`/`delattr`의 상수 이름)이 head SD 최상위 바인딩(symtable 정의·import)이나 모듈 기본 속성으로 해석. base에서 이미 풀리지 않던 (파일, 이름)은 빼고 수만 기록. star·동적 이름·파싱 오류·도구 오류 = FAIL. 거부 확인 = base SD 정의 중 head SD에 정의가 없는 이름 > 0 그리고 base에서 그것을 SD에서 읽는 추적 파일 > 0(아니면 INVALID). F2 oracle에 E3b, F1 범위 = 이름 단위(SR·TL·DR 모듈 단위, SD는 F2 뒤 SD에 남지 않는 이름의 reader만), F9 실패 경로, 계획 534행 개정 문안에 SD 재수출 문장 | design §1·§2.2·§3 SD-NAMES·§4 F9·§7.2·§8 F1·F2행·§9.3 D-26·§10 E3b 블록·표, `p3_doc_amendments.md` §2, 승인 질문 UD-0 ② | `a796468` 합성 커밋(F2v7): HEAD = base → INVALID; 모의 M9(재수출 유지) → `LIVE moved_out=62 base_files_reading_moved_out=31` + PASS; 재수출 하나 삭제 → `structural_symmetry_probe.py:10` FAIL 한 줄; F1 없는 F2 → FAIL 88줄(V1 밖 `spice/*.py` 11 등); 비ASCII reader 추가 → 그 경로도 FAIL; 없는 B0 → `ERROR` + `FAIL(도구 오류 rc=3)` |

## Should-fix

| # | 대응 | 위치 | 재실행·실측 |
|---|---|---|---|
| S1 | E3 fail-closed: `git -c core.quotepath=off … grep -z -l`, `git show` 실패 = `ERROR <경로>` + 종료 코드 3, `e3_run`이 `PIPESTATUS`로 종료 코드를 받아 `E3 FAIL(도구 오류 rc=… rev=…)`. 같은 틀을 E3b에 | §10 E3 블록·표, §3 GONE-SHIM | 비ASCII 경로 importer 하나만 남긴 합성 커밋: v6 블록 `git show` exit 128 traceback 뒤 `E3 PASS`(재현), v7 블록 `E3 FAIL: workspaces/k/probe_전압.py`. 없는 B0 → `E3 FAIL(도구 오류 rc=1 …)` |
| S2 | `import_any`: 목록 계산 실패 = `INVALID`(대입과 `tr`을 나눠 종료 코드를 잃지 않게), 빈 목록 = `INVALID`, `tried` = `expected`(`import_layering` `present` ∪ 트리의 split 파일 -- 따로 계산) 아니면 `INVALID`, 출력 `IMPORT-ANY tried=… expected=… failed=…`, 함수 종료 코드 0/1/2. E5 기준에 그 줄 | §10 IMPORT-ANY 블록·E5 행, §3 IMPORT-ANY 행, D-22 | 모의 M9 `top`: FAIL 2·`tried=13 expected=13`; `bottom7`: failed 0; 고장 `GC`: v6 `design_report`만·종료 0(재현) / v7 `INVALID`(종료 2); 잘못된 트리 루트: `INVALID` |
| S3 | M10 '작성 전 실측' 항목을 실측으로 고침: 지금 `run()` 변이 71개를 `folded_cascode`로 하나씩 실행 -- E-INST 해시만 대조하면 생존 50(print 18, `folded_cascode` 미도달 줄 24, 어느 회로도 미도달 13), stdout `[FAIL]` 유무 46, stdout 전체 해시 24, + report 해시 24. 회로별 도달(파일럿 = 감사 성공·report, `two_stage_ota`·`nmcnr_amplifier` = `ValueError` + 진단 분기, instance 없음). 더할 것: (i) 준비 문장(키 검사·경로·spec·setdefault)은 `run()`에 남기고 `try` 몸체부터 옮김, `print`는 그대로 (ii) stdout·report 해시 대조 + 실패 경로 회로 하나 (iii) 미도달 분기는 진입점 모듈 속성을 합성 반환값으로 바꾸는 계약 (iv) 비용 = 목표 생존 0으로 약 20~40분(v6 계획이면 2.5시간 이상 + V3 FAIL) (v) D-25는 새 test 회로만, M10 E-INST 집합은 `20-dead-code-dup` §3 그대로 | design §2.3·§8 M10행·D-25, 부록 A F6v7 | `p3v7_m10_mutants.py all`(변이마다 새 프로세스, 결정성 확인: 기준 2회 해시 동일) → `p3v7_m10_mutants.folded_cascode.json`, `p3v7_m10_summarize.py` → `p3v7_m10_summary.json`, 세 회로 `trace` |
| S4 | D-27 엔진 card 동결: D0b 병합부터 F2까지 엔진 파일을 바꾸는 Phase 3 밖 card 병합 금지(필요하면 병합 뒤 D0b 재계산, N3.10 밖 개정은 D-11). B26-2~B26-4 기본 F2 뒤(앞당기면 D0b 전·§9.1 재측정 (1)에 포함), B35(사이트 5~8·10·14 -- 함수 이름·레지스트리 목적지 `topology_authoring` 인용) F2 뒤(착수 조건 B36·`plan_tables`·B26-2) | design §6.4·§8.1 마지막 행·§9.1·D-27, 승인 질문 UD-0 ④ | 계획 769·929·936행, B34 final 사이트 표 61~64행·249행, 레지스트리 430~438행(`a796468`) |
| S5 | D0a `plan` 출력에 `import_time_high`(s = split이자 N3.10인 파일의 최소 번호, σ(u) > s인 단위의 import 시점 이름 중 출처 단위 w가 s ≤ σ(w) < σ(u)) + exit 1 사유 + 합성 단계 `import-time-high` 5개 + 거부 입력 + 작성 전 실측 9. D0b 계약 test가 그 키 0을 단언, 위반이면 D0b가 레지스트리 열을 쓰기 전에 멈추고 배정 변경(N3.10 밖이면 D-11). F3 처리 칸 | design §2.2(전제 문단)·§4 F3·§8 D0b행·D-22, D0a 의도·계약 2·6·oracle·거부·실측 9 | `p3v7_import_time_reads.py`(F4v7): SR·DR·TL·ACF의 SD 이름 import 시점 읽기 0, 모의 M9 MOD8·MOD9의 SD·MOD8 이름 import 시점 읽기 0 |

## Minor

| # | 대응 | 위치 |
|---|---|---|
| m1 | `a796468` 재확인 문장: 승인 질문 머리, G1 의도(B28 문단)·작성 전 실측 머리, T0 의도(setattr)·작성 전 실측 머리(새 계약 test 3개 -- A군 0)·8, D0a 작성 전 실측 머리 | 각 문서 |
| m2 | D-9·§9.2 UD-0의 "판정 기록 스크립트 6개" → E3 AST 적중 `.ai/verification/**` 0(제외 집합 안 적중은 `probe_stage_partition.py` 1), `import stick_diagram as sd` 8파일(SD 경유로만 깨짐, E3b 제외 대상). `p3_doc_amendments.md` §2 '기준에 닿는 점'에 v7 수치 | design §9.2·D-9, 개정 문안 §2, 승인 질문 (a) |
| m3 | §7.1 B군에 `test_dup_kcl_edges.py:35`(`_sd()` = `importlib.import_module("stick_diagram")`) + 속성 `_kcl_and_matching_edges`(274·293)·`kcl_series_union`(265·283), 둘 다 레지스트리 목적지 MOD3. T0 B군 목록 10 → 11 | design §7.1, T0 의도·7 |
| m4 | E3 첫 루프가 세 shim 파일 모두의 부재를 본다(E4 `absent_split`과 같은 사실을 직접) | §10 E3 블록·표 |
| m5 | D-24 한계 문장(별칭 `import_module as`, 하위 프로세스 `-c` 문자열, 변수 인자, 문자열 조립) + `a796468` 실측(별칭 0, `-c` 0, 변수 인자 2곳 -- SD:1056 analog-grammar·`test_restore_plan_functions.py:59` 도우미, `getattr(sd, 변수)` 0) | D-24, 부록 A F5v7 |
| m6 | 승인 질문 UD-0 ②에 "SD 임시 재수출을 지운 뒤 추적 파일이 그 이름을 여전히 찾는지 확인(DoD 추가 -- 판정을 더하는 쪽)" 반 줄, ④에 엔진 card 동결 한 줄, D-26·D-27을 '질문에 넣지 않은 것'에 | 승인 질문 |

## 오케스트레이터 지시 -- 확정 순서(사용자 지시 "P10b 끝나면 push하고 Phase 2 완료 판정 진행해")

| 지시 | 대응 | 위치 |
|---|---|---|
| 순서 = P10b → Phase 2 DoD → 면제 묶기(34) → 범위 정책(35) → B34 → B26-1(앞선 test 보강 card 포함) → B33(33) → Phase 3 | §8.1을 한 줄 확정 순서 + 의존 근거 표로(v6의 필수/편의 구분 대체). test 보강 card = `20260930-b26-pre-test-strengthen` | design 머리·§6.4·§8.1, G1·T0·D0a 순서 문장 |
| B34·B26-1을 Phase 2 DoD 안에 둔 v6 §9.1은 틀림 -- Phase 2 DoD 뒤·M card 전 앞당긴 card(A2), N6.3 판정 기록 목록에 없음 | §9.1 공통·엔진 선행 문단, §6.4 첫 문단 정정 | design §6.4·§9.1 |
| D0b 재측정 조건은 이 순서 기준 | D0b = 자기 base(B34·B26-1·B33·G1·D0a 병합 뒤 master)에서 처음 계산, §9.1 재측정 (1)을 B34·B26-1(+ D0b 전 병합된 엔진 card) 기준으로 | design §6.4·§8 D0b행·§9.1·D-11, D0a 의도 |
| (괄호) "Phase 3(T0·D0a·D0b → G1(32) → M1…)" | **따르지 않고 확인 요청**: D0a가 G1의 `SourceIndex`·`moved_defs`를 import(D0a 계약 5)하므로 G1 → D0a → D0b로 둔다. D0a를 G1 전에 병합하려면 D0a 계약 5를 바꿔야 해 이 design 범위 밖 | design §8.1 G1→D0a 행·§11-12 |
| (결과로 드러난 어긋남) | B34·B26-1 card 초안 `phase: 2`, 승인 기록 A2 ③ "Phase 2 진행 중에 병합" -- 계획 1001행대로면 Phase 2 DoD 뒤 병합 card의 `phase`는 3. 이 design은 고치지 않고 인계 | design §6.4·§11-11 |

## 새로 드러난 것(검토 밖)

* `workspaces/current-reuse-telescopic-ota-report/stick.py:9~13`이 `a796468` SD에 없는 `block_from_row_widths`를 import -- 이미 깨진 추적 스크립트. E3b는 `pre_existing`으로 빼고 수를 남긴다(§11-10, 백로그 후보).
* M10 회로별 도달: `folded_cascode` = 감사 SKIP·note·report 생략, 파일럿 = 감사 성공·report 저장(이 측정 616초, 경합), `two_stage_ota`·`nmcnr_amplifier` = 현재 `ValueError`(모든 θ infeasible)로 instance.json을 만들지 않는다 -- E-INST 회로가 아니다(20-dead-code-dup §3 정의와 일치).

## 머리 블록 재검증

`role_paths.parse_spec_card(text, id)`(복제본 `a796468`의 `tools/gates`, `$PY` 3.14) 세 card 모두 통과: G1 `phase 0.5`·`red-green`·`gate_change yes`·approval 1, T0 `phase 3`·`test-only`·`no`·approval 2,
D0a `phase 3`·`red-green`·`no`·approval 1, 절 11개씩.

## 문서 개정 재확인

`p3v6_amend_check.py`를 v7 개정 문안(§2 새 문장 하나 추가)으로 `a796468` 복제본에서 재실행 → `p3v7_amend_check.a796468.json`, `p3v6_amend_check.a796468.json`과 키 정렬 동일('현재' 블록 10개 일치,
두 안 `mod_table` 10·표 4열·10행·`import_layering` exit 0). `merge_gate.plan_tables_hash` 개정 전·두 안 모두 `7167e028…`.

## 산출물·스크립트(`_drafts/`)

* `draft_phase3_design_v7.md`, `draft_p3_{g1,t0,d0a}.spec.md`(사본 `*.spec.v6.md`), `p3_doc_amendments.md`(사본 `.v6.md`), `phase3_approval_question.md`(사본 `.v6.md`), 이 기록(사본 `phase3_revision_log.v6.md`).
* `p3_scripts/p3v7_e3b_synth.py` → `p3v7_e3b_synth.json`(합성 커밋 -- 스크래치 복제본 전용, `C:/g95b` 밖이면 멈춤).
* `p3_scripts/p3v7_sec10_selftest.sh` → `p3v7_sec10_selftest.out.txt`(§10 E3·E3b·`import_any`를 v7·v6 문서에서 잘라 실행; 문서 블록 = 실행 블록 `diff` 동일 확인).
* `p3_scripts/p3v7_m10_mutants.py`(`list`·`trace`·`mutant`·`all`) → `p3v7_m10_mutants.list.json`·`p3v7_m10_mutants.folded_cascode.json`·`p3v7_m10_trace.*.json`, `p3v7_m10_summarize.py` → `p3v7_m10_summary.json`.
* `p3_scripts/p3v7_import_time_reads.py` → `p3v7_import_time_reads.json`. `p3v7_amend_check.a796468.json`.

---

# 초안 v7 → v8 (2026-10-01, 5차 독립 검토 `review5_phase3_v7.md` 반영)

기준 gate `master` `0f23786`(`a796468` 대비 승인 기록 `20261001-p10b-v3-equiv`·P10b spec card 2파일만 -- 엔진·`tools/`·계획·레지스트리 무변경). 스크래치 `C:/g113`(복제본 `repo`·`repo2`, 끝나면 삭제).
산출물: `draft_phase3_design_v8.md`(v7 유지), `draft_p3_{g1,t0,d0a}.spec.md`(사본 `*.spec.v7.md`), `p3_doc_amendments.md`(사본 `.v7.md`), `phase3_approval_question.md`(사본 `.v7.md`).
검토 판정 '고친 뒤 승인 요청 가능' -- 막는 것 2, 고칠 것 6, minor 7 전부 반영.

## Blocking

| # | 발견 | 대응(위치) | 확인 |
|---|---|---|---|
| B1 | DoD E4·E5와 T0 oracle의 `PT`가 `--gmid-phase=1`(Phase 2 승인 `20260930-phase2-e4-phase`로 고친 결함의 재발) | design §10 머리에 `PT3`(10 §10 `PT`에서 `--gmid-phase=3`만) 정의와 bash 함수, E4 test = `PT3`, E5 = `PT3` 전체 + `PT3 --gmid-dod` 전체(둘 다 실패 0) bash·표, T0 spec '무동작 판정 입력' `PT3`. 기준을 더하는 쪽 | §10 블록 `bash -n` 통과(자리표시 치환) |
| B2 | E3b `pre_existing`이 표지 이름(`*`·`<동적 이름>`·`<PARSE-ERROR>`)을 면제 -- 합성 커밋에서 `E3b PASS` | `MARK` 표지를 `pre`에서 뺀다(한 줄 → 세 줄). SD-NAMES 행·E3b 행·D-26 문장 | `p3v8_sec10_selftest.out.txt`: 검토자 합성(B0' = star·dyn·파싱 오류 reader, H = def 이동 + probe 갱신)에서 **v7 블록 `pre_existing=4` + `E3b PASS`(재현) / v8 블록 `pre_existing=1` + FAIL 세 줄**. v8 블록이 base(HEAD = B0)에서 `INVALID`, 모의 M9에서 `PASS`(`moved_out=62 base_files_reading_moved_out=31 pre_existing=1`) |

## Should-fix

| # | 발견 | 대응 | 확인 |
|---|---|---|---|
| S1 | F1 뒤 `e_inst_df36.py`가 `sys.modules["sizing_recipe"]` `KeyError` -- 대체 명령 없음 | **결정**: 새 스크립트 `e_inst_p3.py`를 **design 커밋에 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/`로 고정**(D-28, 문서 개정 §7, 승인 diff에 포함). 이유: 판정 측정 스크립트를 Phase 3 code 커밋 전에 승인 대상 diff로 고정해 code-author가 맞춰 쓸 수 없게(작성자≠검증자), `.ai/verification/**`은 판정 기록 증거 자리, design 원자료 자리와 같음. df36과 엔진 출처 확인 한 곳만 다름(이름 대신 `assets`에서 로드된 모듈 전부가 `<root>` 안). **동등 보이기**: DoD E5 (i)이 B0(F1 전)에서 두 스크립트 출력 JSON이 `engine_origin` 하나만 다르고(p3 ⊇ df36) stdout 사본이 같음(`elapsed=<초>s`만 가림)을 먼저 재고 다르면 INVALID. **비교 판**: v7 'Phase 2 DoD와 같은 해시'는 B26-1 `meta["rails"]` 같은 사이 card의 의도된 변경을 세어 원리상 성립하지 않았다 -- B0(M1 판정 기록 `base_commit`)로. E-LIB는 `e_lib.py` 사본 그대로(F2 뒤에도 `load_topology`·`run_topology_pipeline`이 SD에 남음) | `p3v8_einst_equiv.out.txt`: `0f23786`에서 두 회로 모두 다른 키 = `engine_origin`, stdout 같음(가림 뒤). 근사 F1 트리 `syn/f1h`에서 df36 `KeyError`, p3 `raw_sha256`·`without_topology_ref_sha256`가 `0f23786`과 같음. E-LIB 해시 `0f23786`·`syn/f2drop`·`syn/f1h` 모두 `1d2e3bf6…`. E5 비교 python을 이 출력에 돌려 `PASS`, 해시 하나를 바꾸면 `FAIL folded_cascode` |
| S2 | UD-0 (a) "판정 기록 스크립트 8개가 … 읽는 이름" 깨짐은 재지 않은 사실 | 실측: 8개 중 **2개**(`e_lib_inst.py` -- `save_instance_json`, `diff_dup.py` -- `_import_analog_grammar`·`_kcl_and_matching_edges`), 6개 `e_lib.py`는 안 깨짐(근사 배정 기준, 정확한 수는 D0b 뒤). 승인 질문 UD-0 (a)·design D-9·§9.2 UD-0·문서 개정 §2 | E3b 블록의 제외 집합을 비운 측정 사본을 정정된 모의 F2(`syn/f2drop`)에 실행(F1v8) |
| S3 | A2 ③ 'Phase 2 진행 중(card `phase: 2`)'과 확정 순서(Phase 2 DoD 뒤)의 충돌이 사용자에게 보이지 않음, '사용자 지시' 귀속 과대 | **결정하지 않음**: 승인 질문에 별도 항목 **A2-③**(사실 5개 -- 승인 기록 27·28행 원문, 순서 결정, 계획 1001행, card 초안 셋 `phase: 2`, 게이트가 phase를 진행 Phase와 대조하지 않음(`merge_gate.py` 532~549·1008~1010) -- 기본안 'card `phase: 3`, M card 전 병합 유지, 정정은 새 decision 승인 기록', 대안 'Phase 2 DoD 앞으로 당겨 `phase: 2`'). `pending_questions.md` Q-B34-PHASE 연결 문장. design 머리·§8.1 귀속을 원문 범위로("P10b → Phase 2 DoD"만 사용자 지시, 34→35→B34→B26-1은 제안에 대한 "응, 그렇게 진행해", 나머지는 오케스트레이터 배열), §11-11·§9.2 행 | 질문 문안 |
| S4 | D-25 '네 library 회로 중 가장 짧은 것'이 instance.json을 만들지 않는 회로를 뽑음, §2.3 옛 '기록 없음' 문장 | D-25·§2.3·§8 M10 행: E-INST 회로 집합(instance.json을 만드는 회로) 중 가장 짧은 것 = `folded_cascode`, 실패 경로 두 회로는 (ii) 보조 회로로만. 옛 문장 삭제, '작성 전 실측' (2) 문언 | -- |
| S5 | UD-1 경로 오류 | `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py`(design §7.2·§9.2·승인 질문) | `git status --porcelain --untracked-files=all -- '*.py'`(메인 저장소 읽기): 이것 + `.claude/hooks/*` 4 |
| S6 | D-27 동결이 엔진 파일뿐, `GC` 주석이 사실과 다를 수 있음 | D-27·§8.1·§9.1·§6.4·§8 D0b 행: 동결에 `tools/gates/**`·`tools/migrate/**`·레지스트리 목적지 열. 사후 강제: E6(M1~F2 엔진 단위), E2 앞 `git diff --quiet "$B0" HEAD -- tools/gates tools/migrate`(위반이면 `E2 INVALID`), E4 `reg_mismatch`. D0b~M1 base 구간은 DoD가 덮지 않음을 명시. `GC` 주석을 D-27 전제로 고침 | `0f23786` `tools/**`의 `.py`에 엔진 모듈 import 0(redteam 데이터만 이름을 담음) -- Phase 3 card가 M1 뒤 `tools`를 바꿀 이유가 없어 확인 줄이 오탐하지 않음 |

## Minor

| # | 대응 |
|---|---|
| m1 | 승인 질문 머리·끝에 대상 판 해시(design v8 `29ae10e99ff4b40d`, G1 `3a99df21414d6e99`, T0 `35f7e3e7850a2847`, D0a `1f9592d491303132`, 문서 개정 `c775320e6c2b7e1a`, `e_inst_p3.py` `7d26134ad00ec504`) -- 질문 때 다시 계산 |
| m2 | D-26에 `symtable` 한계(조건부 바인딩도 '있음') + DoD가 G1 코드에 기대지 않게 독립 식으로 둔 이유, `0f23786` SD 최상위 `try`·`if` 0 실측 |
| m3 | §10 공통에 `export APPDATA=… HOME=…` |
| m4 | 승인 질문 '뒤에 올 승인'에 M10 V3 생존 면제 |
| m5 | D-19 (가)·§6.4·승인 질문: B37a(미승인) '둘 예정' |
| m6 | 승인 질문·G1·T0·D0a에 `0f23786` 재확인 문장(변경 2파일, 엔진·tools·계획·레지스트리 무변경). 검토 m6의 ".ai/specs"는 실제 `docs/02-design/specs/…`였다 |
| m7 | D-24 한계에 경로 로드(`spec_from_file_location`·`runpy.run_path`) -- `0f23786` 엔진 4파일 로드 0 |

## 새로 드러난 것(검토 밖)

* **v7 측정 결함**: `p3v7_e3b_synth.py`의 모의 F2는 SD '읽지 않는 이름'을 모듈 최상위 symtable `is_referenced()`로만 셌다 -- 함수 몸체에서만 읽는 재수출 11개(`load_topology`·`Transistor`·`kcl_series_union` 등)까지 지운 과대 삭제. v7 design §2.2 reader 목록·E3b 행 'FAIL 88줄'·부록 A F1v7·F2v7이 그 결과였다. `p3v8_e3b_synth.py`에서 모든 유효 범위의 전역 참조 + 주석 이름으로 고쳐 다시 잼: FAIL **49줄·12파일**(V1 밖 7, V1 수집 test 5). 판정 명령(E3b)은 그대로이고 모의 입력만 틀렸다. 첫 v8 실행(`p3v8_sec10_selftest.run1_overdrop.out.txt`)도 같은 결함으로 S2를 과대 측정(6개 `e_lib.py`까지 FAIL) -- 정정 뒤 재실행 결과만 쓴다.
* 파일럿 E-INST stdout은 SLSQP 진행 줄의 `elapsed=<초>s` 때문에 바이트로 결정적이지 않다(`folded_cascode`는 결정적). E5 동등 확인은 그 숫자만 가린다. §2.3 (ii)에 관찰 문장.
* E-LIB 비교 판: B26-1 계약 2가 `load_topology` meta에 `rails`를 더하므로(`draft_b26_1.spec.md` 계약 2 -- 20:04 판 92행, 첫 언급 58행; v8.1 정정, 6차 검토 m-c: '91행'은 그 전 판 줄 번호), `e_lib.py`(meta를 해시)로 Phase 2 DoD 판과 Phase 3 판을 raw 해시로 비교하면 다르다(v8.1 좁힘 -- 6차 검토 N1) -- S1 대응에서 비교 판을 B0로 둔 근거.
* `p3v8_sec10_selftest.sh`의 머리 `diff` 출력이 결과 파일에 남지 않았다(빈 줄). 대신 실행된 블록 = 현재 문서 블록임을 줄 수(v8 178·v7 176)와 `diff`(바뀐 곳 `pre` 계산 한 곳)로 따로 확인했다.

## 머리 블록 재검증

`role_paths.parse_spec_card(text, id)`(복제본 `0f23786`의 `tools/gates`, `$PY` 3.14) 세 card 모두 통과: G1 `phase 0.5`·`red-green`·`gate_change yes`·approval 1, T0 `phase 3`·`test-only`·`no`·approval 2,
D0a `phase 3`·`red-green`·`no`·approval 1(v7과 같음).

## 문서 개정 재확인

`p3v6_amend_check.py`를 v8 문서 개정(§1~§6 블록 불변, §2 사실 문장·§7 새 파일 설명 추가)으로 `0f23786` 복제본에서 재실행 → `p3v8_amend_check.0f23786.json`이 `p3v7_amend_check.a796468.json`과 키 정렬 동일.

## 산출물·스크립트(`_drafts/`)

* `draft_phase3_design_v8.md`(부록 A F1v8~F5v8, 부록 H), `draft_p3_{g1,t0,d0a}.spec.md`(사본 `*.spec.v7.md`), `p3_doc_amendments.md`(사본 `.v7.md`), `phase3_approval_question.md`(사본 `.v7.md`).
* `p3_scripts/p3v8_e3b_synth.py` → `p3v8_e3b_synth.json`(합성 커밋 -- `C:/g113` 밖이면 멈춤; 모의 F2 정정, `v7_overdropped_reexports` 기록).
* `p3_scripts/p3v8_sec10_selftest.sh` → `p3v8_sec10_selftest.out.txt`(정정 뒤), `p3v8_sec10_selftest.run1_overdrop.out.txt`(정정 전 첫 실행 -- 참고용).
* `p3_scripts/e_inst_p3_proposed/e_inst_p3.py`(design 커밋에 넣을 새 측정 스크립트 문안), `p3_scripts/p3v8_einst_equiv.sh` → `p3v8_einst_equiv.out.txt`.
* `p3_scripts/p3v8_amend_check.0f23786.json`.

---

# 초안 v8 → v8.1 (6차 검토 `review6_phase3_v8.md` 반영, 2026-10-01)

입력: `_drafts/review6_phase3_v8.md`(막는 것 1·고칠 것 3·minor 3, 루프 종료 규칙: v8이 만든 결함과 5차 미해결만). 개정 전 사본: `draft_phase3_design_v8.0.md`, `phase3_approval_question.v8.md`.
모두 문장 수정이다 -- 판정 명령(§10 bash)·spec card(G1·T0·D0a)·문서 개정 문안·`e_inst_p3.py`는 바꾸지 않았다.

| # | 발견 | 대응 |
|---|---|---|
| N1 | E5 비교 판 B0가 선례 `20260930-phase2-e4-baseline`의 고르지 않은 대안과 같은 모양인데 '원칙 기본값'으로 분류 | 승인 질문 UD-0 '기준에 닿는 기본값'에 (c) 추가: 기본안 = B0(M1 base) + Phase 2 DoD와는 card 판정 기록(B34·b26pre·backfill·B26-1)이 잇는다, 대안 = Phase 2 DoD 대상 커밋과 마지막 병합본 비교 + 의도적으로 바뀐 필드(B34·B26-1·backfill)만 그 card 계약값으로 따로 판정. 선례 기록의 사용자 원문 "둘다 기본안으로 진행해"와 선택지 문장("기본안 = da03c0e와 Phase 2 마지막 병합본을 같은 경로에서 비교하고 `topology_ref`만 DF-36 계약값으로 판정, 대안 = card별 판정 기록 사슬로 갈음")을 원문 그대로 인용, 선례와 일치하는 쪽 = 대안이라고 명시. 수정 요청 선택지 예시에 (c), '질문에 넣지 않은 것'의 D-28에서 비교 판 부분 삭제. design: D-28 첫 칸·(e), §10 E5 행 'raw 해시 그대로는 성립하지 않는다'로 좁힘, §9.2 UD-0 행. 어느 쪽을 기본안(Recommended)으로 둘지는 오케스트레이터 몫 -- 문안은 v8 기본안(B0)을 그대로 기본안으로 두고 선례와의 관계를 사실로 적었다 |
| N2 | E2 통과 기준 행에 `E2 INVALID` 없음(fail-open) | §10 E2 행 맨 앞에 "`E2 INVALID` 줄 없음(B0..HEAD `tools/gates`·`tools/migrate` 무변경 -- D-27)" |
| N3 | A2-③·확정 순서에 backfill 결함 card `20261001-b26-backfill-interdig-final-audit`(초안 `phase: 2`) 누락 | 승인 질문 A2-③ 사실 (3)·(가)를 네 card로(backfill은 승인 ③ 대상이 아니라 계획 1001행으로 같은 값이라는 줄), 순서 B34 → b26pre → backfill → B26-1(`b26pre_revision_log.md` m5). design §8.1 머리 문장·코드 블록·표(b26pre·backfill 행 추가), §9.1 엔진 선행·재측정 (1), §9.2 A2-③ 행, §11-11, D-28 (e)·E5의 구간 card 목록 |
| N4 | A2-③ 사실 (4)가 '판정에 영향 없음'으로 읽힘 | (4)와 §11-11에 문장 추가: card `phase`가 이 card들의 V1 `--gmid-phase`·`--gmid-strict`를 정한다. gate `master` `0f23786` `tools/gates/merge_gate.py` 재확인 -- 1042행 `if c["phase"] == card["phase"]: keys |= set(c["activated_ic_case"])`, 1210~1211행 `conftest_has_gmid_phase` → `strict = strict_set(old_view, card)`, 1212~1213행 `v1_command_check(..., strict_needed=strict, phase=card["phase"])`, 1009~1012행 `phase_tok`·`strict_tok` 대조 |
| m-a | E3b가 놓치는 세 모양 | D-26 한계에 `sys.modules` 대입 별칭·lambda가 돌려주는 모듈·이름 바꾼 `import_module` 추가. `0f23786` 추적 `.py`에서 `git grep -E 'sys\.modules\[[^]]*stick_diagram|import_module as|from importlib import import_module'` 0건 재확인 |
| m-b | `e_inst_p3.py` 출처 확인 범위(경로 꼬리 조건, run 전 시점) | D-28 첫 칸에 범위 차이 문장(스크립트는 바꾸지 않음 -- 바꾸면 sha256과 F3v8 동등 실측을 다시 재야 한다) |
| m-c | revision log '새로 드러난 것'의 "`draft_b26_1.spec.md` 91행" | 그 줄을 '계약 2(20:04 판 92행, 첫 언급 58행)'로 고침(제자리 수정 -- 이 절 외 유일한 기존 줄 변경) |

## 대상 판 해시(v8.1, sha256 앞 16자리 -- 승인 질문 끝 목록과 같음)

* design `draft_phase3_design_v8.md` `7da84c9a0237b604`(v8 `29ae10e99ff4b40d`), 승인 질문 `phase3_approval_question.md` `dcb20e72f4e94885`(v8 `b0e4a9061eff2093`).
* 바뀌지 않음: G1 `3a99df21414d6e99`, T0 `35f7e3e7850a2847`, D0a `1f9592d491303132`, 문서 개정 `c775320e6c2b7e1a`, `e_inst_p3.py` `7d26134ad00ec504`.
* 도구: `p3_scripts/p3v81_append.py`(design 부록 I와 이 절을 바이너리 append -- 앞 바이트 불변 단언).

---

# 초안 v8.1 → v8.2 (오케스트레이터 결정 -- UD-0 (c) 기본안을 선례 모양으로, 2026-10-01)

입력: 오케스트레이터 결정(원칙: 같은 상황에서 사용자가 고른 쪽을 따른다 -- 승인 `.ai/approvals/20260930-phase2-e4-baseline.md`, 사용자 원문 "둘다 기본안으로 진행해"; 그 질문의 기본안 = da03c0e와 Phase 2 마지막 병합본을 같은 경로에서 비교하고 `topology_ref`만 DF-36 계약값으로 판정, 대안 = card별 판정 기록 사슬). 개정 전 사본: `draft_phase3_design_v8.1.md`, `phase3_approval_question.v8.1.md`, `p3_doc_amendments.v8.1.md`. 측정: `a796468` 복제본(`C:/g135`, 끝나면 삭제), 엔진은 gate `master` `0f23786`과 같다.

| # | 대상 | 대응 |
|---|---|---|
| 1 | UD-0 (c) 기본안 | B0 비교 → 선례 모양(P2D 비교 + 의도된 필드만 계약값으로 따로 판정). B0는 대안(같은 블록에서 `P2D=`만 바꿈). design 머리·D-28 가운데·(e)·§9.2 UD-0 행·§10 E5 블록·행, 승인 질문 (c)·'수정 요청' 예시·머리 |
| 2 | 빼는 필드 목록 | 초안 계약에서 유도: B34(`draft_b34.final.spec.md` 계약 7) 없음, b26pre 없음, backfill(`draft_b26_backfill_audit.spec.md` 계약 1·2) 값은 `pipeline_result`까지만 -- 실측 F1v82로 instance.json·report 0 확인 -- 없음, B26-1(`draft_b26_1.spec.md` 계약 2·8) E-LIB `meta["rails"]` 하나. E-INST 빼는 키 없음 |
| 3 | 계산 가능성 | E-INST: 기존 `e_inst_p3.py` 출력(`field_sha256`·raw)으로 충분. E-LIB: `e_lib.py`는 해시만 내므로 확장 `e_lib_p3.py`(meta 키 빼기 인자) -- F1 전 트리(`a796468`)에서 인자 없음·`rails` 모두 `e_lib.py`와 같은 `hash` `1d2e3bf6…`(F2v82) |
| 4 | 거부 확인 | 판정 python을 design에서 그대로 뽑아(sha256 `37fecfea…`) 시제품에 실행: 계약 모양 p1 PASS, nets 틀림 p2 FAIL(9줄), meta 키 하나 더 p3 FAIL, 동등 고장 INVALID(F3v82). 원래 `e_lib.py`는 p1에서 해시가 달라 raw 비교 불성립을 재현 |
| 5 | 문서 개정 | `p3_doc_amendments.md` 머리 `diff_path` 문장에 `e_lib_p3.py`, §7 동등 확인 판 문장(B0 → P2D), 새 §8(`e_lib_p3.py` sha256) |

## 대상 판 해시(v8.2, sha256 앞 16자리 -- 승인 질문 끝 목록과 같음)

* design `draft_phase3_design_v8.md` `dc2a887b2c11f382`(v8.1 `7da84c9a0237b604`), 승인 질문 `phase3_approval_question.md` `d2476b580f548fdf`(v8.1 `dcb20e72f4e94885`), 문서 개정 `p3_doc_amendments.md` `5104bfe4c23aeebf`(v8.1 `c775320e6c2b7e1a`).
* 새 파일: `p3_scripts/e_lib_p3_proposed/e_lib_p3.py` `c6b82fc7b4cd974c`. 바뀌지 않음: G1 `3a99df21414d6e99`, T0 `35f7e3e7850a2847`, D0a `1f9592d491303132`, `e_inst_p3.py` `7d26134ad00ec504`.
* 도구: `p3_scripts/p3v82_patch.py`(design 본문 교체, '현재' 문자열 1회 단언), `p3v82_patch_question.py`(승인 질문·문서 개정), `p3v82_append.py`(부록 A 행 삽입, 부록 J·이 절 바이너리 append -- 앞 바이트 불변 단언), `p3v82_e5_judge.py`(§10 E5 판정 python 원본), `p3v82_relaxed_reach.py`, `p3v82_judge_scenarios.sh` → `p3v82_judge_scenarios.out.txt`, 실행 스크립트·요약 `p3v82_out/`.
