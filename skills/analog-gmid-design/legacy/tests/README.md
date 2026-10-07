# analog-gmid-design tests

## 실행법

저장소 루트에서 실행한다(`$PY` = `C:/Python314/python.exe`).

* C6 전: `$PY -P -m pytest -c tools/gates/pytest_gate.ini --rootdir=. --confcutdir=. skills/analog-gmid-design/legacy/tests`
  (2026-10-07 `assets/tests`에서 `legacy/tests`로 옮김 -- `../LEGACY.md`)
* C6 뒤: 위 명령 끝에 `--gmid-phase=<Phase>`를 붙인다.
* 순서 의존 확인(C9): `--shuffle-seed=<int>`를 더하면 수집 순서를 `random.Random(<int>)`로 섞는다.

## 판정 규칙

* 판정은 assert로만 한다. print·logging 출력으로 판정하지 않는다 -- `contracts/test_ts3_no_print_verdicts.py`가 검사한다.
* xfail은 test에 직접 쓰지 않는다. conftest가 계획서 N4.1 표로 만든다.

## 디렉터리 (계획 N3.11 트리 인용)

```
skills/analog-gmid-design/assets/tests/
  conftest.py      real_lut(세션, 저장소 npz 경로 고정 + 지문 기록), toy_lut, library_dir, topology 팩토리
                   (library/*.topology.json 로드·변형만), grids, --shuffle-seed 옵션(pytest_collection_modifyitems 자체 구현)
  unit/test_mod1_gmid_lut.py ... unit/test_mod9_instance_report_builder.py
  integration/     파일럿 전체회로(L5c), 레이아웃 파이프라인(엔진 import하는 레이아웃 test), end-to-end
  contracts/       IC1~IC11, SC-a~SC-e 계약 test
  regression/      library 회로 측정(대상 구분 DEC-47), 규칙 분기 발동표(DEC-59)
  oracles/         test-author 소유 독립 참조구현
  legacy/          TS1 이관본(TS2 완료 시 삭제)
  tooling/         code-author 도구(tests/tools/, tools/migrate/)의 test(test-author)
  tools/           정본 데이터를 갱신하는 운영 도구, 계측 도구(성능·무동작)(code-author 소유, 그 test는 test-author. pytest 수집 제외. `00-common` §10·§11)
  probes/          일회성 진단(pytest 수집 제외)
```

| 항목 | 지금 있음 |
|---|---|
| `legacy/` | 없음(C9에서 `unit/test_selftest_<모듈>.py`로 나누고 삭제) |
| `unit/` | 있음(C9: 이관본 섹션별 test `test_selftest_<모듈>.py` 4개, 매핑표 c9-mapping.json) |
| `contracts/` | 있음 |
| `tooling/` | 있음 |
| `conftest.py` | 있음(C6: `--gmid-*` 옵션·`gmid_ic` 표식·xfail / C9: `--shuffle-seed`·보고 머리·세션 fixture `assets_dir`·`library_dir`·`toy_lut`·`real_lut`) |
| `integration/`, `regression/`, `oracles/`, `tools/`, `probes/` | 아직 없음 |
