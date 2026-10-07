# 옛 gm/ID 엔진 (legacy)

2026-10-07 사용자 지시: "옛 엔진은 나중에 삭제하기 편하게 모아둬." 새 엔진은 계획서 아키텍처로
`skills/analog-gmid-design/gmid_engine/`에 따로 짓는다. 이 문서는 옛 엔진이 어디 있고, 어떻게 돌리고,
어떻게 지우는지를 적는다.

* 기준 태그: `legacy-engine-v1` = `6df4bd7` (옮기기 직전 커밋). 옛 배치 그대로 보려면 `git checkout legacy-engine-v1`.
* 옮긴 커밋: 이동만 한 커밋(rename만) 1개, 경로 보정 커밋 1개 (`git log -- skills/analog-gmid-design/legacy`).

## 무엇이 legacy인가

`skills/analog-gmid-design/legacy/` 아래 전부.

| 경로 | 내용 | 옛 자리 |
|---|---|---|
| `legacy/sizing_recipe.py`, `stick_diagram.py`, `topology_library.py`, `design_report.py`, `audit_current_forced.py` | 엔진 소스 | `assets/` |
| `legacy/report_template.html` | 리포트 템플릿 | `assets/` |
| `legacy/sky130_regression_reference.json` | 옛 엔진 회귀 골든값(`tests/tools/regression_runner.py`가 읽음) | `assets/` |
| `legacy/_sweep.cir` | 쓰는 곳 없는 param sweep 넷리스트 | `assets/` |
| `legacy/tests/` | 옛 test 전체(contracts·unit·tooling·probes·tools·conftest) | `assets/tests/` |
| `legacy/workspaces/run_harness.py` | 옛 엔진 실행 하네스 | `workspaces/` |
| `legacy/workspaces/{two-stage-ota,current-reuse-telescopic-ota,folded-cascode,nmcnr-amplifier}-report/` | 하네스 산출물(instance.json 등)과 세션 스크립트 | `workspaces/` |
| `legacy/selftest_session6*.log`, `legacy/workspaces/logs/*.log` | 추적 안 되는(.gitignore) 옛 실행 로그 | `assets/`, `workspaces/` |

## 공용 입력 (assets/ 에 남는다 -- 새 엔진도 쓴다)

* `assets/library/*.topology.json`, `*.topology.md` -- 회로 토폴로지(유일한 토폴로지 소스)
  * library 는 공용 입력이라 2026-10-07 정정(TOPOLOGY_CORRECTION_QUEUE 일괄 반영: folded_cascode M1·M2 nmos, passive_elements·`_declared_target_spec.supplies_v` 추가) 이후 legacy 결과는 tag `legacy-engine-v1` 시점과 다를 수 있다.
* `assets/sky130_nfet_pfet_lut_sample.npz` -- sky130 LUT
* `assets/sky130_lut_sweep.py`, `assets/ac_sweep_checkpoints/` -- LUT 생성기와 그 재개용 체크포인트
  (생성기가 `OUTPUT_DIR/ac_sweep_checkpoints`를 읽고 쓰므로 생성기와 같이 둔다)
* `assets/topology_to_markdown.py` -- topology.json -> .md 변환기

## 남은 의존 (legacy 를 지우기 전에 끊어야 한다)

1. `assets/topology_to_markdown.py`가 `legacy/stick_diagram.py`의 `load_topology`를 import한다
   (`sys.path`에 `../legacy`를 넣음). 새 엔진의 topology 로더로 바꾼 뒤에 지운다.
2. `tools/gates/*`(gate 인프라, 2026-10-07 꺼짐)가 옛 경로 상수를 갖고 있다 -- 고치지 않았다:
   `pytest_gate.ini` `testpaths`, `merge_gate.py` `CONFTEST_PATH`·`TESTS_REL`, `role_paths.py`, `role_hooks.py`,
   `source_lint.py`, `test_lint.py`, `weakening_diff.py`, `import_layering.py`, `interface_card.py`,
   `reachability.py`, `mutate_changed.py`, `gate_config.json`. 경로 인자 없이 `pytest -c tools/gates/pytest_gate.ini`를
   부르면 `testpaths`가 없어 수집 0(INTERNALERROR)이다. gate를 다시 켜려면 이 상수들을 새 엔진 배치에 맞춰야 한다.
   `legacy/tests/conftest.py`는 계획서 표를 `tools/gates/merge_gate.py`로 읽는다(legacy -> gates 의존).
3. `agents/gmid-code-author.md`, `agents/gmid-test-author.md`, `agents/gmid-verification-auditor.md`의 경로 설명이 옛 자리를 가리킨다.
4. `.gitignore`의 `skills/analog-gmid-design/legacy/...` 줄(지운 뒤 함께 지운다).
5. `SKILL.md`의 `legacy/report_template.html`·`legacy/sizing_recipe.py`·`legacy/topology_library.py`·`legacy/stick_diagram.py` 언급.

## 실행 방법 (저장소 루트에서)

```bash
PY=C:/Python314/python.exe
# 옛 test (2026-10-07 기준 1129 수집: 1114 passed, 15 xfailed -- 이동 전과 test id·결과 같음)
$PY -P -m pytest -c tools/gates/pytest_gate.ini --rootdir=. --confcutdir=. \
    skills/analog-gmid-design/legacy/tests --gmid-phase=3 --gmid-strict=
# 옛 하네스 (산출물은 legacy/workspaces/<circuit>-report/ 에 덮어쓴다)
$PY -P skills/analog-gmid-design/legacy/workspaces/run_harness.py current_reuse_telescopic_ota
```

경로 규칙(이동 때 고친 것): 엔진 디렉터리 `A` = `legacy/`(conftest fixture `assets_dir`), 공용 입력은
`legacy/../assets/`(fixture `library_dir`·`real_lut`), 하네스 산출물은 `legacy/workspaces/`.
`legacy/workspaces/*-report/` 안의 세션 스크립트(`resize.py`, `spice/*.py` 등)는 절대 경로를 박은 일회성
이력 스크립트라 경로를 보정하지 않았다(이동 전에도 아무것도 부르지 않았다).

## 삭제 방법

먼저 위 "남은 의존" 1을 끊는다(새 로더로 교체). 그다음:

```bash
git rm -r skills/analog-gmid-design/legacy skills/analog-gmid-design/LEGACY.md
rm -rf skills/analog-gmid-design/legacy   # 추적 안 되는 로그·result.txt·report.html 등 남은 것
```

같은 커밋에서 `.gitignore`의 `skills/analog-gmid-design/legacy/` 줄과 `SKILL.md`의 `legacy/` 언급을 정리한다.
되살리려면 `git checkout legacy-engine-v1 -- <경로>`.
