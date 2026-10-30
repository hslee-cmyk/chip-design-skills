---
id: 20260922-ts2-pytest-split
phase: 1
evidence_type: test-only
gate_change: no
approval: 20260922-10-test-separation-design
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260922-ts2-pytest-split.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 1 test 분리 card이고 Phase 1은 폐기됐다(계획 N6.1 '옛 Phase 처리' 1행; N3.11 'TS0~TS6 폐기'). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 덧대지 않는다(O-169).

## 의도

TS2(계획 N3.11): 이관본 4개(`A/tests/legacy/selftest_{sizing_recipe,stick_diagram,design_report,topology_library}.py`)의 섹션을
`A/tests/unit/test_selftest_<모듈>.py`의 pytest test로 나누고, 이관본 4개와 `A/tests/legacy/test_legacy_selftests.py`를 지운다.
conftest에 셔플·세션 fixture·보고 머리를 더한다. 정본 명세는 design `10-test-separation` v1.2 §5.4 'C9에서 더하는 것'·§6.8·§7(M1·M2·Q)·§10 D3·D3b.
A = `skills/analog-gmid-design/assets`. conftest 변경과 `test_legacy_selftests.py` 삭제는 V5 발견이라 DEC-40 승인과 R1(05 §12 'V5 승인 운반')이 필요하다.

**매핑표**(§6.8 '섹션->test 매핑표'의 정본): `docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/c9-mapping.json`
(생성기 `build_c9_mapping.py` 같은 폴더, 입력 = C2 병합 커밋 6abe0fc 이관본(번호)과 head 커밋 이관본(범주), C12로 고친 `sections`).
섹션마다 `number`(C2 병합본 번호 = test id의 `NNN`), `category`(C4 뒤), `target`(`header`·`docstring_of`·`test`·`fixture`·`none`),
`test_ids`, `m2_min`, `guarded_only`, `deps`(이름, 만든 섹션 번호), 원문 줄 범위(`start`·`end`, head 이관본)가 있다.

## 관찰 가능한 계약

1. `A/tests/unit/test_selftest_<모듈>.py` 4개에 매핑표 `test_ids`의 test 함수가 **모두, 그 이름 그대로** 있고 수집된다(M1). 매핑표에 없는 test 함수를 더하지 않는다. 합계 215(sizing 70, stick 131, design_report 4, topology_library 10).
2. 섹션 변환은 design §6.8-2~4 그대로: P → 파일 머리(`sys.stdout.reconfigure` 버림), D → 다음 섹션 test docstring 첫 줄, `fixture` → 그 이름을 만드는 함수 범위 fixture(불변 자원만 세션 fixture `assets_dir`·`library_dir`·`toy_lut`·`real_lut`), 블록 안 `def` → 모듈 수준 함수, 전역 `lut` → `toy_lut`, `_ASSETS_DIR` 경로 → `assets_dir`·`library_dir`, 거부 try → `pytest.raises`(메시지 단언은 `match=`나 `excinfo`로), `_drl_case` → `parametrize` 2케이스(케이스마다 새 ctx).
3. 판정 수 보존(M2): 섹션마다 (그 섹션 test들의 `assert` + `pytest.raises` 수) ≥ 매핑표 `m2_min`. `m2_min` = 거부 try 밖의 `assert`·`raise AssertionError` 수 + 거부 try 수(거부 try 안의 `assert False`는 `pytest.raises` 하나가 되므로 따로 세지 않는다. design §7 M2의 `asserts + reject_try`와 다른 점 -- C4가 `raise AssertionError`를 `assert False`로 바꿔 그 식이 같은 판정을 두 번 센다. `sections`의 `reject_try` 필드는 루프 안 데이터 수집용 `try/except ValueError`도 세므로 쓰지 않는다: sizing S021, stick S032·S038).
4. `guarded_only` 섹션(design §6.8-6, 판정이 모두 `if`·`try` 아래) 5개의 처리와 근거:
   * sizing S014: `try` 본문 `optimize_full_circuit_budget(... stop_after_sizing=True)`의 `except ValueError` 분기를 지우고 `if _l5c_result is not None:` 아래 assert를 조건 밖에서 실행. 근거: head 이관본 실행 출력에 이 섹션의 '참고(정직한 한계' 줄이 없다(성공 분기).
   * design_report S003: `assert os.path.exists(<_crt_instance>)` 뒤 원래 assert. 근거: `workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.instance.json`은 추적되는 파일.
   * sizing S051·S054, stick S157: 승인 `20260922-c9-ic11-split`대로 test 2개. `test_s<NNN>_<slug>`는 성공 경로 assert를 그대로 담고 `pytest.mark.xfail(raises=ValueError, strict=True, reason="I-C11 two_stage_ota stage1_out KVL -- 담당 Phase 4")`, `test_s<NNN>_<slug>_known_limitation`은 지금 동작(ValueError 메시지에 `stage1_out`과 `KVL`)을 `pytest.raises`로 단언. ValueError를 내는 호출은 **test 본문**에 둔다(fixture setup의 예외는 xfail이 아니라 ERROR다). 근거: head 이관본 실행 출력의 '참고(정직한 한계, DC/AC 아키텍처 미분리' 줄(sizing 1곳 = S051, S054는 같은 호출 재실행, stick 1곳 = S157).
5. 판정 없는 print·skip 문구는 옮기지 않는다. 새 `pytest.skip`·다른 xfail·`-k` 우회를 만들지 않는다.
6. `A/tests/conftest.py`: design §5.4 'C9에서 더하는 것' 그대로 -- `--shuffle-seed=<int>`(`pytest_collection_modifyitems` 끝, xfail 표시 뒤 `random.Random(seed).shuffle(items)`, 플러그인 없음), `pytest_report_header`(`shuffle-seed: <값 또는 none>`, `real_lut: <npz 상대 경로> sha256=<해시>`, PASS/FAIL 토큰 없음), 세션 fixture 4개. C6의 기존 동작은 불변.
7. 이관본 4개와 `test_legacy_selftests.py`를 지운다(`A/tests/legacy/`가 비면 디렉터리째).
8. `--gmid-phase=1 --gmid-strict=IC3:,IC5:`로 전체 실행: 기본 순서와 `--shuffle-seed` 1~5 여섯 번 모두 실패·오류 0(D3). I-C11 xfail 3개는 XFAIL, 그 밖의 새 test는 PASS. `--collect-only -q`에서 seed k마다 순서가 기본과 다르고 두 번 같다(Q, D3b).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only(계획 N3.12.3 개정 P5): 대상 코드 불변. 증거(design §6.8): base에서 `test_legacy_selftests.py` 4케이스 PASS(= 모든 섹션 통과), 변경 뒤 매핑표의 모든 test가 기본·셔플 순서에서 계약 8대로 통과, M1·M2 성립, `--durations=0` 표를 판정 기록 부속 산출물로 첨부.

## oracle 종류와 출처

(c) 이관본 판정(동작 보존): 기대값은 head 이관본의 `assert`·거부 try 그대로 옮긴다(새 기대값을 만들지 않는다). 매핑·판정 수의 기준은 매핑표. 계약 4의 조건 근거는 위에 섹션마다 적었다.

## 거부해야 할 입력

이관본의 거부 try(각 `pytest.raises`), I-C11 `_known_limitation` 3개(ValueError).

## library 회로 적용 여부

해당 없음(test 재배치). 섹션이 쓰는 library 회로는 이관본 그대로.

## 무동작 판정 입력(무발동 값)

해당 없음.

## 재현할 수치

없음.

## 결정 필요 항목

conftest 변경·`test_legacy_selftests.py` 삭제·xfail 3개의 DEC-40 승인(V5) -- 1차 시도에서 auditor가 발견 경로와 diff 해시를 내면 사용자에게 보여 받는다(R1). I-C11 섹션 처리는 승인 `20260922-c9-ic11-split`로 확정.

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260922-ts2-pytest-split.spec.md`.
