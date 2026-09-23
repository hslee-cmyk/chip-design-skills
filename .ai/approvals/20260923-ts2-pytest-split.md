---
id: 20260923-ts2-pytest-split
date: 2026-09-23
target_kind: diff
target: 38ecdc81cfc03bd8243b7d7115034ce4a365ee895a2339a97c93710e7592983a
diff_base: f45f9aa2235d1d0e6a6e2571d4281eb15b0d48ec
diff_head: bdf9ca626f0000056152f192e60f29bcc8a95755
diff_path: skills/analog-gmid-design/assets/tests/README.md
diff_path: skills/analog-gmid-design/assets/tests/conftest.py
diff_path: skills/analog-gmid-design/assets/tests/contracts/test_ts3_no_print_verdicts.py
diff_path: skills/analog-gmid-design/assets/tests/legacy/test_legacy_selftests.py
scope: C9 TS2 -- conftest C9 부분 추가, test_legacy_selftests.py 삭제, TS3 대조 test 대상 목록 리터럴 교체, tests/README.md 갱신의 DEC-40 승인
---

## 사용자 원문

> 승인 기록에 재검토 줄 넣고 진행해

## 범위 설명

덮는 것(V5 발견 5건, 1차 시도 auditor 실측 diff_hash `38ecdc81…` -- C13 병합 뒤 base f45f9aa에서 다시 계산해 같은 값):
1. `tests/conftest.py`: design 10 §5.4 'C9에서 더하는 것' -- `--shuffle-seed=<int>`, `pytest_report_header`(셔플 seed, real_lut 지문), 세션 fixture 4개(`assets_dir`·`library_dir`·`toy_lut`·`real_lut`). C6 부분 불변.
2. `tests/legacy/test_legacy_selftests.py` 삭제: 이관본 4개를 하위 프로세스로 돌리던 wrapper. 이관본과 함께 지우는 것이 TS2 완료 조건(계획 N3.11 'legacy는 TS2 완료 시 삭제').
3. `tests/contracts/test_ts3_no_print_verdicts.py`: 판정 대상 목록 리터럴을 `legacy/selftest_*.py` 4개에서 `unit/test_selftest_*.py` 4개로 교체(같은 test, assert 수 불변). 이관본이 없어졌으므로 그대로 두면 그 대조 test가 실패한다.
4. `tests/README.md`: legacy 실행법을 지우고 `unit/`과 C9 conftest 옵션을 적는다.
5. 도구가 이름 바뀜을 따라가지 않아 발견 목록에 나오지 않는 것: `unit/test_selftest_{sizing_recipe,stick_diagram}.py`의 I-C11 strict xfail 3개(`test_s051_optimize_full_circuit_budget`·`test_s054_section`·`test_s157_M1`). 방식은 승인 `20260922-c9-ic11-split`으로 이미 확정했고, 이 승인은 그것이 이번 변경에 실제로 들어오는 것을 덮는다.

덮지 않는 것: 판정 약화. 판정 수는 매핑표 `m2_min` 기준 M2로 보존되고 auditor가 순서 7에서 섹션마다 재측정한다. 새 `pytest.skip`·다른 xfail은 없다.

## 재검토

I-C11 xfail 3개는 Phase 4에서 I-C11(U-09)이 해소되면 strict xfail이 XPASS→FAIL로 알린다. 그때 세 test를 이관본 원문 기준으로 다시
보고, 함께 면제한 V4 규칙 (1) 2건(`20260923-c9-v4-exempt`)도 같은 자리에서 판단한다. 백로그 B9.
