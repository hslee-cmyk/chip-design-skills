# 독립 2차 검토 -- b26pre v2 묶음(`draft_b26pre.spec.md` v2, `draft_b26_backfill_audit.spec.md`, `b26_backfill_question.md`, `b26pre_v2_kill_map.md`, `b26pre_revision_log.md`)

검토자: 독립 reviewer(작성자 아님). 저장소 읽기 전용. gate `master` = `0f23786`(`git -C <repo> rev-parse gate/master`, HEAD·master와 같음).
`git diff --quiet a796468 0f23786 -- skills` = 같음(엔진·test 불변, 바뀐 것은 `.ai/approvals/20261001-p10b-v3-equiv.md`와 P10b spec card뿐). 그래서 초안의 a796468 줄 번호는 gate master에서도 그대로다(인용 줄 전부 `git show master:` 사본에서 다시 확인).
scratch: `C:/g111`만(`git archive master` → `base`, `base` + 두 줄 삭제 → `fix`, 부분 수정 `p_in`·`p_after`, 변이 사본 `mut`, 계측 사본 `instr`). 끝에 삭제.

## 0. 결론

**판정: 조건부 통과(S 반영 뒤 커밋).** 차단(B) 0, 고칠 것(S) 4, 사소(minor) 6.

* 1차 검토의 B1·B2·S1~S5는 **모두 해소**됐다(§1). 숫자는 내 사본에서 다시 재서 같았다.
  * 시제품 17 test: base 사본 전체 실행에 넣어 17 passed(seed 1).
  * 씨앗 6문장: 내 변이 사본에서 6/6 죽음(죽인 test 이름까지 표 1과 같음).
  * SR 11802: 생존(17 passed).
* backfill 결함 card의 red는 **진술한 이유 그대로** base에서 실패한다.
  * 이유: `assert False is True`, `AuditCheck(name='3b. interdigitation[Ma/Mb] [참고용 -- 이 kind는 필수 아님]', ok=True, detail='seg1_seg1: 인접')`.
  * 수정 후보는 `A/tests` 전체에서 회귀가 없다.
    * fix: 888 passed·15 xfailed·2 failed
    * base: 886 passed·15 xfailed·4 failed
    * 차이는 red 시제품 2개뿐이다. 공통 2 failed는 `test_ts6_probe_relocate`의 `.git` 필요 test 2개다(archive 사본 한계).
  * 부분 수정(한 경로만 고침)은 해당 경로 test가 거부한다(실측).
* 'seed 6 + SR 11802는 N2d만이라 B26-1 N2w 규칙의 V3 대상이 아니다'는 **맞다**. 범위 정책 계약 1 T6 문장으로 손 판정했고, 표 1의 정의 열·B26-1 Q1 24개와도 수치가 맞물린다(§4).
  다만 범위 정책 card는 아직 gate에 없다(초안 분류기 기준). 그래서 '그 card가 문장 그대로 병합되면'이라는 조건이 붙는다.
* 순서(b26pre → backfill → B26-1)와 B34의 상호작용
  * 같은 sizing_recipe 영역을 건드리지 않는다. B34는 stick_diagram 4 def만 바꾼다.
  * 실제 접점은 **backfill ↔ B26-1**이다(같은 def의 바로 앞 줄). 순차라 충돌은 없고, B26-1 측정값을 다시 재야 한다는 인계만 필요하다(§5).
* 남은 S
  * backfill card의 oracle 종류 표기 '(b) 문서화된 의도'가 4종 정의에 없다(S1).
  * backfill card 계약에서 피검 함수가 interface card 생성기에 잡히지 않는다(실측 1개만 추출, S2).
  * 'test-author가 쓰는 이름'이 test-author 입력 절 밖에 있다(S3).
  * b26pre '의도'가 N2d만 변이까지 'B26-1 V3 대상'이라고 말한다(S4).

## 1. 1차 검토 지적의 해소 여부

| 지적 | v2 처리 | 재측정·확인 | 판정 |
|---|---|---|---|
| B1 등가 후보 9개 중 8개 구별 가능 | 계약 10(TAP_P·TAP_N), 씨앗 6개 '등가' 주장 삭제, backfill 2개는 결함 card로 | 내 변이 사본(`C:/g111/seedkill.py`, 각 문장을 `pass`로): 2100·2176·3985 → `test_b26pre_seed_tap_p`만 실패, 2101·2177·3986 → `test_b26pre_seed_tap_n`만 실패(각 1 failed·16 passed). 11802 → 17 passed(생존). 표 1과 같다 | **해소** |
| B2 backfill 결함 고정 금지 | b26pre는 11800·11879를 고정하지 않음. red-green card + 사용자 질문 | §2·§3 | **해소** |
| S1 계약 2 비공개 함수 | 공개 `run_matching_safety_with_finger_growth(..., gm_id_bounds=(11.9, 12.1))` | 계약 8에 `_fixup_euler_blocked_rows` 금지 명시. 작성자 kill 기록(`out/kill_base.jsonl`·`kill_b34.jsonl`) 32문장 = 29 killed·3 survived(11800·11802·11879), 두 사본 같음. 11696~11700 세 문장은 다중 줄 문장이라 내 `pass` 치환으로는 재지 않았다(1차 검토가 `C:/g99`에서 별도 확인) | **해소** |
| S2 oracle (c)·계약 5 인용 | (c) = 기준선 a796468, auditor 재측정, '현재 출력 붙여넣기 아님', docstring에 값 없는 항목 목록화. 계약 5 인용 교체 | 계획 688행과 N0.4 119행('(c) known-good 기준(SPICE, 결함 도입 전 커밋)') 대조. B26-1 이전 커밋을 known-good으로 두고 '의도와 모순 없음'을 항목마다 확인하는 방식은 조건에 맞는다. 인용 줄 9362~9367·9400~9406·9408~9412·6507~6509·11582~·11784~11786·SD 928~930·2686~·2710·2718·2760·7532·7556을 master 사본에서 다시 읽음 -- 전부 일치 | **해소**(minor m3) |
| S3 계약 4 test 수 | hub 경우 포함 4 test, 총 17 | 시제품 17 test 실행 확인 | **해소** |
| S4 필드 이름 | 'test-author가 쓰는 이름' 절 신설 | 내용은 충분하다. 위치가 test-author 입력 밖이다 → **S3** | 내용 해소, 위치 S |
| S5 승인 줄 | `approval` 줄 삭제, U1 = 원칙 기본안 | `role_paths.parse_spec_card`(master 판): b26pre `approval: []`·`evidence_type: test-only`·`gate_change: no`, backfill `approval: []`·`red-green`·`no`. 둘 다 `expect_id` 일치로 통과 | **해소** |
| M1~M4 | 재현 명령, 측정 단위(base 문장 32), `EULER_OK` 독립성 한 줄, `None` → 빈 목록 | 문장 확인 | **해소** |

## 2. backfill 결함 card(`draft_b26_backfill_audit.spec.md`) -- red·회귀 재측정

### 실측 결과

* **사본**
  * `base` = `git archive master`
  * `fix` = base + 11800·11879 두 줄 삭제(바이너리로 CRLF 보존, `diff` 결과 정확히 두 줄)
* **재현**(`C:/g111/probe_bf.py`, 카드 '재현' 입력 그대로, PYTHONHASHSEED=1)
  * 행이 euler-blocked인 것: `build_stick_diagram(행)["seg1"].status == "blocked"`.
  * base, max_rounds 1·2·3·5
    * `interdig_ok`는 False이고 반환 audit `3b.…[Ma/Mb]`는 True다.
    * rows는 `{seg1_seg0: [Mp], seg1_seg1: [Mb, Ma]}`이고 `audit.ok`는 False다.
    * 사유는 max_rounds=1이면 `max_rounds_exceeded`, 2 이상이면 `relaxed_to_layout`이다.
  * fix: `interdig_ok`만 True로 바뀌고 rows·사유·`audit.ok`는 base와 같다.
* **red 이유**(full suite 출력)
  * 두 test 모두 `assert e["interdig_ok"] is c3b[0].ok` → `AssertionError: assert False is True`다. 카드 '판정 유형 근거'의 진술과 같다.
* **부분 수정 판별**(카드 '거부해야 할 입력' 둘째 항목)
  * `p_in`(11800만 삭제): m=1이면 False(루프 뒤 test 실패), m≥2이면 True.
  * `p_after`(11879만 삭제): m=1이면 True, m≥2이면 False(루프 안 test 실패).
  * 그래서 두 경로를 별개 test로 두는 근거가 실측으로 맞다.
* **회귀**(`C:/g111/run.py`, `pytest -c tools/gates/pytest_gate.ini … --gmid-phase=2 --gmid-strict=`, `A/tests` 전체, seed 1, 두 사본 contracts에 시제품 두 파일)
  * base: 886 passed·15 xfailed·4 failed
  * fix: 888 passed·15 xfailed·2 failed
  * 공통 실패 2개는 `test_ts6_probe_relocate`의 `.git` 필요 test다. 초안 수치와 정확히 같다.
* **기존 test 불변**: L4e(`test_selftest_sizing_recipe.py` 1480행 `is not None`)가 fix에서 통과한다(위 전체 실행에 포함).
* **library·기존 test 노출**(이 검토 추가 측정, `instr` 사본): `_finalize`에 계측을 넣어 `A/tests` 전체를 돌렸다. 결과는 §2 끝 '계측 결과'에 있다.

### S1. oracle 종류 '(b) 문서화된 의도'는 4종 정의에 없다

* 근거
  * 계획 N0.4(plan.md 119행): "(a) 물리 불변식·손계산(구성으로 정답이 정해진 합성 입력 포함) (b) 다른 방법의 참조구현 (c) known-good 기준 (d) spec card에 사용자가 적은 값".
  * 계획 688행: "oracle은 4종만".
  * 이 card 계약 1의 기대값('반환 `interdig_ok`는 반환 audit의 3b와 같다')은 참조구현이 아니다.
  * master 판 spec card 전체에 '(b) 문서화' 용례가 0건이다(`git grep`).
* 위험
  * auditor V4가 test 주석의 `oracle 대조:`를 4종으로 확인할 때 걸린다.
  * 기대값이 **같은 피검 호출의 다른 반환 필드**라 V4 (1) '피검 함수로 기대값 만들기'로 읽힐 여지도 있다.
* 고칠 것
  * 이 관계는 U-BF 승인(사용자 결정 '`interdig_ok`를 반환 audit의 3b로 채운다')이 정하는 계약이다. 그러니 **(d) 사용자 결정**(승인 기록 id)으로 적는다. 두 코드 주석은 그 결정의 근거로 인용한다.
  * 입력은 (a) 구성으로 둔다(넷 차수로 euler-blocked, 좁은 gm/ID 범위로 완화).
  * 관계 단언이 '피검 출력으로 기대값 만들기'가 아닌 이유도 한 줄 적는다. 결정된 계약이 **두 반환 필드의 일치 자체**이고, 어느 한쪽 값을 숫자로 박지 않는다.
  * (선택) 구성 쪽 독립 단언을 더하면 V4가 더 단단해진다. 예: 최종 rows에 소자 집합이 정확히 `{Ma, Mb}`인 행이 있고 두 소자가 확산 넷 `n2`를 공유하면 3b '인접'이므로 `interdig_ok is True`다. 다만 rows 모양 고정이 따라오므로 code-author 자유도와 맞바꾼다 -- 기본안은 위 (d) 표기만이다.

### S2. 계약 절에서 피검 함수가 interface card에 잡히지 않는다

* 실측: `tools/gates/interface_card.build`(master 판)를 이 card에 돌렸다(`--root C:/g111/base`).
  * **추출 심볼은 1개(`size_transistor`)뿐**이다.
  * 생성기는 '관찰 가능한 계약' 절의 `` `이름` `` 또는 `` `이름(…)` `` 꼴 백틱만 잡는다(interface_card.py 70행 정규식).
  * 계약 1의 호출은 `` `res = run_matching_safety_with_finger_growth(…)` ``로 시작해 잡히지 않는다.
  * `SizingContext`·`Transistor`는 클래스라 원래 대상 밖이다.
* 결과: test-author는 피검 함수의 시그니처·docstring 첫 단락을 interface card에서 보지 못한다.
  'test-author가 쓰는 이름'은 '작성 전 실측' 끝 문단에 있어 test-author 입력 절(아래 S3) 밖이다.
* 고칠 것
  * 계약 1 머리에 `` `sizing_recipe.run_matching_safety_with_finger_growth` ``를 단독 백틱으로 한 번 적는다.
  * 이름 목록 문단을 '관찰 가능한 계약' 절 끝으로 옮긴다.
  * 고친 뒤 생성기를 다시 돌려 2개 이상 추출되는지 확인한다.
  * 참고로 b26pre card는 같은 생성기로 21개가 추출됐다(아래 m1).

## 3. 사용자 질문(`b26_backfill_question.md`) -- 사실·인용 대조(gate master `0f23786`)

| 질문 문장 | master에서 확인 | 판정 |
|---|---|---|
| 주석 11784~11786 원문 | `sizing_recipe.py` 11784~11786 글자 그대로(괄호 '(저장 버그와 같은 종류의 불일치 재발 방지)' 앞에서 끊음) | 맞음 |
| 정리 전 audit으로 먼저 채움(11800 루프 안, 11879 루프 뒤), 이미 채운 항목은 건너뜀 | 11800·11879 `_backfill_interdig_ok(result)`, 11772~11773 `if entry["interdig_ok"] is not None: continue`, `_finalize` 11787~11794 안의 backfill | 맞음 |
| 재현 값(False / True / rows 분할) | §2 실측과 같음 | 맞음 |
| 운영 코드 소비처 없음(엔진 자신 + selftest `is not None` 1곳) | `git grep interdig_ok master`(`.ai/context.md` 제외): 엔진 밖은 selftest 1480~1481뿐(그 밖에는 `.ai/verification/…/ast_*.json`의 AST 노드 집계 숫자 2건 -- 코드 소비 아님). library에 `interdig_ok` 0건(저장 산출물에 실리지 않음) | 맞음 |
| `pipeline_result["relaxed_pairs"]`로 보고 | 9393~9398 `pr = dict(pr, …, relaxed_pairs=match_fix["relaxed_pairs"])` | 맞음 |
| 세션17 / 세션31 경위, `.ai/context.md` 1558~1561 | master 판 `.ai/context.md` 1558~1561 문장 일치, `_finalize` 주석 '2026-08-13(세션31 이어…)' | 맞음 |
| 수정 후보 회귀 수치(888 passed·15 xfailed, 실패 2개 = `.git` 없는 사본) | §2 재측정과 같음 | 맞음 |
| '바뀌는 관찰값은 이 경우의 `interdig_ok` 하나(행·audit·사유는 그대로)' | `_backfill_interdig_ok`는 `relaxed_pairs` 항목만 쓴다(부작용 없음). 실측 m 1·2·3·5에서 rows·`audit.ok`·사유 동일 | 맞음 |

**minor(m4)**:
* 문안이 근거를 11784~11786 주석 하나만 인용한다. 그 주석은 **audit**의 일치를 말하고, `interdig_ok`를 직접 말하지는 않는다.
* 결함이라는 판단은 그 주석과 11769~11770('새로 계산된 audit_result가 나오면 그 3b 체크로 채운다')을 **결합한 해석**이다. card는 이것을 '결합'이라고 정직하게 적었다.
* 사용자가 같은 사실 위에서 고르도록 질문 배경에 11769~11770 원문 한 줄과 '두 주석을 합친 해석'이라는 말을 넣는다.
* 3b 체크 이름이 offset 쌍에서 '[참고용 -- 이 kind는 필수 아님]'이라는 점(그래서 `audit.ok`는 3c로 계속 False)도 한 줄 넣으면 오해가 없다.
* '현재 gate `a796468`'은 '현재 gate `0f23786`(엔진은 a796468과 동일)'로 고친다.

## 4. 'seed 6 + SR 11802는 N2d만 → B26-1 N2w 규칙의 V3 대상 아님' 판정

**결론: 맞다(범위 정책 문장 기준). 단 조건부.**

* **B26-1 card 규칙**: `draft_b26_1.spec.md` 324~338행 -- 범위 정책 `20260930-v3-changed-stmt-scope` + T6 넓힘, 'V3 대상 301 = N2b 235 + 넓힌 T6 66'. 이것이 표 1의 'N2w'(301)와 같은 집합이다.
* **T6 문장**(`draft_v3_scope_policy.spec.md` 66~68행): "(나) 바뀐 영역 R마다, R과 같은 블록(head 목록)에서 R 뒤에 오는 문장 중 R이 바꾸는 이름을 읽는 문장의 몫 … **뒤 복합문의 안쪽 블록에 있는 문장은 '같은 블록'이 아니다**".
* **씨앗(SD 2100·2101·2176·2177·3985·3986)**
  * R은 `seeds = {...}`(B26-1이 `rails.nets`로 바꾸는 새 문장)이다.
  * 같은 블록의 다음 `for c in candidates["candidates"]:`는 자기 필드(`c`, `candidates[...]`)에서 `seeds`를 읽지 않는다. 그래서 T6 대상이 아니고, T4 조상도 아니다.
  * `seeds[ga] = gb`는 그 `for`의 안쪽 블록이다. → T6 밖이다.
  * 바뀐 def 머리의 매개변수 `rails`를 읽지 않으므로 T3 밖이다. → N2d만이다.
* **SR 11802**
  * R은 루프 본문의 `current_rows, result = repair_matching_safety(…, rails=rails)`다.
  * 같은 블록(반복문 body라 위치 무관)에서 `result`를 읽는 `if result.ok:`는 자기 필드 → 대상이다(표 1 SR 11801 'N2w').
  * 그 안쪽 블록의 `_finalize` 줄(11802)은 '같은 블록'이 아니다. `_finalize`(중첩 def)는 B26-1에서 바뀌지 않는다. `_fixup_euler_blocked_rows`는 시그니처가 불변인 뿌리이고, `audit_row_split`은 계약 4의 20함수에 없다. → N2d만이다.
* **수치 맞물림**
  * 표 1 34 변이 id 중 'N2d만'은 16개다(11802·11803·11828·11835·11836·11837, 씨앗 6, SD 4530·3286, SD 3285 삭제·뒤집기).
  * 나머지 18 = Q1의 E6 13 + E7 5와 정확히 같다(`b26pre_v2_kill_map.md` §1). 그래서 'N2w 생존 중 16 죽임, 남는 E6·E7 = backfill 2'가 성립한다.
* **조건**
  1. 범위 정책 card가 아직 gate에 없다(master `docs/02-design/specs`에 `v3-changed-stmt-scope` 없음). 위 판정은 초안 문장과 초안 분류기(`v3_scope_widen.py`/`b26v4_classify`) 기준이다. 병합된 도구가 'T6 = 자기 필드만'을 그대로 구현해야 성립한다.
  2. B26-1 code-author가 씨앗 루프 자체를 고치지 않아야 한다(예: 씨앗 생성을 컴프리헨션 하나로 합침). 고치면 그 문장들이 T1 새 문장이 된다.
     이 경우에도 b26pre 계약 10이 이미 죽이므로 결과는 안전하다. 그러니 'U2-a는 N2d로 잴 때만'이라는 결론은 그대로이고, 위험은 수치 문장뿐이다.

### S4. b26pre '의도'가 N2d만 변이까지 'B26-1의 V3 대상'이라고 말한다

* 해당 문장: 10행 "그래서 이 경로가 B26-1의 V3 대상에 들어오는데, 지금 test로는 그 변이가 죽지 않는다"
* 표 1의 34개 중 16개는 위 §4대로 B26-1 규칙(N2w)에서 V3 대상이 아니다. card 자신(22~23행 'N2d 대상 중 E6·E7 def만 골랐고')과 kill map §3도 그렇게 적었다.
* 고칠 것: '의도'에 한 줄을 더한다. "범위는 B26-1 규칙(N2w)보다 넓은 N2d로 잡았다. N2w 대상은 18(Q1의 E6 13·E7 5), N2d만은 16이다. N2d만 몫은 B26-1 V3 판정과 무관하지만 같은 경로의 test 강도이고, 범위 규칙이 깊어지는 경우의 예비다."
  이 말이 없으면 B26-1 auditor가 'b26pre로 죽인 수'를 N2w 수치와 섞을 수 있다.

## 5. 순서(b26pre → backfill → B26-1)와 B34

* **B34가 바꾸는 곳**(`draft_b34.final.spec.md`, `b26pre_v2_scripts/mk_g106.py`)
  * stick_diagram의 `_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction` 4 def뿐이다. sizing_recipe는 0곳이다(B34 card 87행 'SR 모듈의 함수는 하나도 부르지 않는다').
  * → **같은 sizing_recipe 영역 접점 없음.** b26pre는 test만, backfill은 SR `run_matching_safety_with_finger_growth` 두 줄이다.
* **B34 인벤토리**
  * b26pre·backfill의 새 test가 B34 def 인벤토리('159·15·66·4 + k')를 늘릴 수 있다. 계약 5·6·7·10이 analog-grammar 경로와 `load_topology`를 지난다.
  * 둘 다 B34 **뒤**라 B34 판정 수치에는 영향이 없다(b26pre U3가 이것을 근거로 적었다).
  * backfill card는 'b26pre → 이 card → B26-1'만 적고 B34를 명시하지 않는다. b26pre가 B34 뒤라 전이적으로 성립한다 → minor m5(한 줄 명시).
* **B34 위에서의 동작**: 초안 `bf_b34.txt`·`kill_b34.jsonl`·`baseline.txt`(b34 × 4 seed 17 passed)로 같음이 기록돼 있다.
  * 내 재측정은 base(=master)만 했다. B34 사본에서 backfill fix의 전체 회귀는 아무도 재지 않았다. B34가 SR 경로를 바꾸지 않으므로 위험은 낮다 → minor m6, backfill auditor 몫으로 적는다.
* **실제 접점 = backfill ↔ B26-1(같은 def, 인접 줄)**
  * B26-1은 이 def의 `repair_matching_safety(…)` 호출(11798·11877, 각각 지울 backfill 줄 바로 앞)에 `rails=rails`를 붙인다. 뿌리 선언 획득 문장도 더한다(계약 4 '시그니처가 안 바뀌는 뿌리').
  * 순차 병합이라 텍스트 충돌은 없다. 다만 다음이 낡는다.
    1. B26-1 card 360행 E6 행의 '11809 `_backfill_interdig_ok(result)`'와 finger growth 6
    2. 'V3 대상 301', Q1 24개
    3. 모의 head의 AST 경로(`body[10].body[1]` 등 -- 한 문장이 빠지면 뒤 순번이 당겨진다)
  * kill map §3이 '고치면 남는 생존 0'이라고 했으므로, B26-1 card 인계에 다음을 더한다. **"backfill card 병합 뒤 B26-1 모의 head·V3 대상 수·Q1 문안을 그 병합본에서 다시 잰다(E6 finger growth 6 → 4, 11809 행 삭제)."**
  * b26pre U3의 'B26-1 card에 넣을 인계'에는 b26pre 몫만 있다 → S4와 함께 반영을 권한다(별도 번호 없이 minor로 묶음, m5).

## 6. b26pre card(v2) 기타

* **계약 10 일반성**
  * 소자 `M1..M5`·`Mx1`·`Mx2`·`My`, 넷 `ninp`·`ninn`·`ntail`·`nd*`·`nx*`·`ny`·`nbp`·`nvb`, 레일 `vdd`·`gnd`만 쓴다.
  * 시제품 두 파일에서 library 회로 이름 grep 0건이다(`folded`·`telescop`·`miller`·`two_stage`·`nmcnr`·`ngcc`·`current_reuse`·`classab`·`M1a` 등).
  * 인용 docstring(SD 6507)에 `folded_cascode`가 나오지만 docstring 원문이라 test 입력과 무관하다. **일반적이다.**
* **parse_spec_card**: 두 card 모두 통과(§1 S5 행).
* **템플릿 대조**(`_TEMPLATE.spec.md`)
  * 머리 키·필수 절이 다 있다. b26pre는 '관찰 가능한 계약'과 '신규 시그니처' 사이에 'test-author가 쓰는 이름' 절을 더했다(템플릿·파서가 금지하지 않음).
  * 다만 아래 S3.

### S3. 'test-author가 쓰는 이름'이 test-author 입력 절 밖이다(두 card 공통)

* 근거
  * `agents/gmid-test-author.md` 21~22행 입력: "interface card … 뿐", "spec card('관찰 가능한 계약', 'oracle 종류와 출처', '거부해야 할 입력', '재현할 수치')".
  * b26pre의 새 절과 backfill card의 '작성 전 실측' 끝 문단은 이 목록에 없다.
  * interface card 생성기도 '관찰 가능한 계약' 절만 읽으므로, 클래스(`SizingContext`·`Transistor`·`AuditResult`)와 필드 이름은 어디에도 실리지 않는다.
* 고칠 것: 두 card 모두 그 문단을 '관찰 가능한 계약' 절 끝의 '이름(입력·판정용)' 항목으로 옮긴다. 1차 S4의 내용은 그대로 두고 위치만 옮긴다.

## 7. 사소(minor)

* **m1. b26pre interface card에 비공개 심볼이 실린다**
  * 실측 추출 21개 중 4개(`_fixup_euler_blocked_rows`·`_scan_case_collisions`·`_propose_gm_id_roles`·`_propose_L_roles`)가 비공개다. 계약 근거 문장에 백틱으로 적혀서다.
  * 계약 8이 호출을 금지하므로 판정에는 문제가 없다. 다만 test-author에게 시그니처를 보여 주는 셈이다.
  * 근거 문장의 비공개 이름을 백틱 없이 적거나 '(비공개, 호출 금지)'를 붙인다. B34 card 87행이 같은 기법을 쓴다.
* **m2. 계약 10의 `Mx1`(↔`My`) 단언은 '동점이면 이름순'(코드 주석, SD 2760)에 기댄다**
  * docstring 규칙만으로 정해지는 더 약한 단언도 씨앗 6개를 모두 죽인다(변이 쪽에서는 Mx1·Mx2 어느 것도 My와 짝이 되지 않는다 -- 손 추적). 예: "`Mx1`·`Mx2` 중 정확히 하나가 `My`와 matching/mirror이고 나머지 하나는 키 없음, 매칭쌍 제안은 그 하나와 `My`".
  * 지금 문장도 (a)+주석 인용으로 성립하므로 선택 사항이다.
  * 손 추적: TAP_P에서 ninp→ninn 방향이 빠지면 `Mx1`의 gate가 미지라 후보가 여럿이다. `My`의 기대 파트너(gate ninp, source gnd)는 `Mx1`·`Mx2` 둘이라 보류된다. 반대 방향이 빠진 변이는 TAP_N이 같은 방식으로 잡는다.
* **m3. 기준선 커밋 표기**
  * card는 '기준선 = gate `master` `a796468`'이라 적었으나 gate는 이미 `0f23786`이다(엔진 동일).
  * auditor가 순서 3에서 실제 base로 다시 재므로 판정에는 영향이 없다. '기준선 = 착수 시 gate master(엔진은 a796468과 같음, 다르면 재측정)'로 적는다.
  * 계약 3(e)는 3b 실패가 하나도 없는 입력에서 사유 리터럴 `"only_3b_failures_left"`를 고정한다. 코드 주석(11823~11826, 11825행 '이 분기에 도달했다고 euler까지 깨끗하다는 보장이 없다')이 이 분기 도달을 인정하므로 의도와 모순은 아니다. 다만 이름이 부정확한 리터럴의 (c) 고정이라, 사유 이름을 바꾸는 후속 card에 V5 비용이 생긴다는 점을 (c) 목록 옆에 한 줄 적는다.
* **m4.** §3 끝(질문 문안 보강).
* **m5.** backfill card 순서에 'B34 뒤(전이)' 한 줄. B26-1 인계에 'backfill 병합 뒤 재측정' 한 줄(§5).
* **m6.** backfill fix의 B34 사본 전체 회귀는 미측정이다 → backfill auditor 몫으로 card '재현할 수치'에 적는다.

## 8. 재현(scratch `C:/g111`, 검토 뒤 삭제)

* 사본: `git -C <repo> archive master -o C:/g111/base.tar` → `base`. `fix` = `mkfix.py`(줄 11800·11879 바이너리 삭제, CRLF 보존). `p_in`·`p_after` = `mkpartial.py`.
* `run.py <copy> 1 <name> skills/analog-gmid-design/assets/tests` → base 886/15/4, fix 888/15/2(위 §2).
* `probe_bf.py <copy>` → §2 재현 값.
* `seedkill.py` → 씨앗 6/6 죽음, 11802 생존.
* `interface_card.build(<card>, "C:/g111/base")` → b26pre 21개, backfill 1개.
* `role_paths.parse_spec_card(<card>, expect_id=…)` → 두 card 통과.
* 계측: `mkinstr.py`·`mkinstr2.py`(`_finalize`에 사전값 ≠ 최종값 기록) + `run.py instr 1 full_instr …`.

### 계측 결과(`instr` 사본, `A/tests` 전체, seed 1)

* 실행 결과는 869 passed·15 xfailed·2 failed다. 시제품 19개를 뺀 기존 test 전체이고, 2 failed는 `.git` 필요 test다.
* `_finalize`가 비어 있지 않은 `relaxed_pairs`를 본 호출은 **기존 suite 전체에서 1회**뿐이다. 그 호출은 `test_selftest_sizing_recipe.py::test_s016_run_matching_safety_with_finger_growth`(합성 Ma/Mb, `interdig_ok=True`)다.
* 사전값과 최종값이 어긋난 호출은 **0회**다(`instr_hits.txt` 없음).
* 뜻: 수정 후보는 기존 test·suite가 돌리는 library 경로에서 관찰값을 하나도 바꾸지 않는다. 사용자 질문의 '영향 범위' 문장을 뒷받침한다.
* 다만 suite가 library 9회로 전부의 `optimize_full_circuit_budget`을 돌리지는 않는다. 질문의 'library 9회로 미측정' 문장은 그대로 두고, 다음 한 줄을 더하기를 권한다. "기존 test 전체에서 완화 발생 1회(합성), 불일치 0회(독립 검토 계측)".
