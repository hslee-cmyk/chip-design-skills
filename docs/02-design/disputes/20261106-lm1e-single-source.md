---
id: 20261106-lm1e-single-source
spec_card: docs/02-design/specs/20261106-lm1e.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_lut_single_source.py::test_py_files_reference_only_declared_lut_npz_names
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_lut_single_source.py::test_root_env_still_sha256_checked
test_id: skills/analog-gmid-design/gmid_engine/tests/lut/test_lut_single_source.py::test_checks_actually_reject
---
## 문제의 test

세 test가 `TypeError: list indices must be integers or slices, not str`로 실패한다. `_declared_names()`(test 파일 줄 29-31)가 `cfg["files"].values()` 각 원소를 `ent["path"]`로 읽는데, `files.verify_midpoints`가 배열(list)이 됐다.

## 근거(oracle 또는 사용자 원문)

- spec card §범위 126행·interface §1(14행): `files.verify_midpoints` = `{path, sha256}` 배열, 옛 단일 객체는 `lut_location_config_invalid`. 즉 이 꼴 바뀜은 card 계약이다.
- 이 test 파일은 card의 영향 test 교체 목록(`RETIRED_TESTS_lm1e.md`)에 없다. card 계약대로 구현하면 이 test의 `files` 값 순회 가정이 깨진다.
- 엔진은 계약대로(배열)이므로 엔진을 고치면 interface 위반이다.

## 요청

`_declared_names()`가 배열 원소도 풀어 읽도록(값이 list면 각 원소의 `path`) test를 고치게 해 달라. 기대값은 바뀌지 않는다(선언된 npz 이름 집합이 30개 늘 뿐).
