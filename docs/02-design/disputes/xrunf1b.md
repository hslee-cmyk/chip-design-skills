---
id: xrunf1b
spec_card: docs/02-design/specs/xrunf1b.spec.md
test_id: gmid_engine/tests/layout/conftest.py::staged_snapshot (finger_candidates·pattern_select·finger_geometry·rows 블록 단위 test 전부가 쓴다)
test_id: gmid_engine/tests/layout/test_run.py::test_reference_w_change_does_not_recompute_slices (ly_device 열에 W_m 이 남아 있어야 한다는 단언)
---
## 문제의 test

O-24 후속 지시("ly_finger_candidates·ly_pattern_select·ly_rows 가 ly_device 열 전체를 READS 로 읽어 W_m 만 바뀌어도 재계산된다 -- 세 블록이
실제로 쓰는 값만 READS 로, canonical_naming 의 W 도 같은 기준으로")를 구현하려면 세 블록의 READS 를 `ly_device` 에서 다른 필드로 바꿔야 한다.
그러면 test 도구가 깨진다.

* `tests/layout/conftest.py::staged_snapshot`(블록 단위 test 4개 파일 -- test_finger_candidates·test_finger_geometry·test_pattern_select·
  test_rows 가 쓴다)는 입력 필드로 `ly_device`({이름: LayoutDevice}), `ly_pdk`, `ly_groups_in`, `ly_row_groups`, `ly_rejected`, `ly_passives` **만**
  쓰고(`ly_point` 포함 다른 소자 필드는 쓰지 않는다) 블록을 바로 부른다. 세 블록이 `ly_device` 가 아닌 새 필드를 읽으면 그 열이 비어 있어 결과가 달라진다.
* `test_run.py::test_reference_w_change_does_not_recompute_slices` 는 `r2.snapshot.column(DEVICE, F_DEVICE)` 의 값이 `W_m == 7e-6` 인
  `LayoutDevice` 이길 요구한다 -- `ly_device` 는 W_m 을 가진 `LayoutDevice` 로 남아야 한다(W_m 을 `ly_device` 에서 뺄 수 없다).

## 근거(oracle 또는 사용자 원문)

실측(코드 worktree `09523314`+이 변경, 파일:줄은 `skills/analog-gmid-design/gmid_engine/layout/`):

* 세 블록이 `LayoutDevice` 에서 읽는 칸: `finger_candidates.py` 는 `gm_id` 만(44행 이하 `device.gm_id`), `pattern_select.py` 는 `kind`·`L_m`·`W_adjustable`·
  drain/gate/source·diode, `rows.py` 는 `kind`·`L_m`·drain/gate/source/body. **세 블록 어디도 `W_m` 을 읽지 않는다.** 그런데 READS 가 `(device, ly_device)`
  열 통째라 투영 지문에 W_m 이 들어가 W_m 만 바뀌어도 세 블록의 입력 버전이 달라진다(재계산 -- 값은 같다).
* `W_m` 을 쓰는 곳은 `outputs.py:58,70,75`(출력 `DeviceLayout.W_m`·`WRequest` -- 필드 파생 출력, 블록 아님)과 `canonical_naming.py:55`(요소 표시
  `("W", d.W_m)`)뿐이다.
* `canonical_naming.py` 의 `("W", d.W_m)` 표시는 자기동형을 값으로 가르는 표지다. 이것을 빼면 W 만 다른 두 소자의 정준 이름이 같아질 수 있어 정준 이름·패턴 선택
  결과가 바뀔 수 있다(해당 test 로는 `tests/authoring/test_spec_schema.py` 와 레이아웃 그룹 test 가 정준 이름을 쓴다 -- 바뀌는지는 구현해 봐야 안다).

필요한 변경(구현 가능하지만 test 도구를 바꿔야 한다):
1. `ly_device` 를 W_m 없는 값으로 두거나, 세 블록이 읽는 칸만 담은 새 소자 필드(예 `ly_point` 의 연결·역할 확장 또는 `ly_topo`)를 만들고 세 블록의
   READS 를 그쪽으로 바꾼다. `LayoutDevice`(계약 클래스, test 가 직접 생성)에서 W_m 을 빼면 `dev()` 등 모든 test 생성부가 깨진다.
2. `staged_snapshot` 이 새 필드도 써야 한다.
3. `canonical_naming` 의 W 표지는 슬라이스 실현 W(`ly_slices`/`ly_finger`)로 바꾸면 블록 순서(canonical_naming 은 finger 이전에도 불린다)와 충돌한다 --
   W 표지를 빼는 쪽이면 정준 이름 test 기대가 바뀔 수 있다.

## 요청

사람(사용자) 결정이 필요하다.
(a) 세 블록의 READS 를 좁히는 것을 이 card 에 포함하고 `staged_snapshot`(test 도구)이 새 필드를 쓰게 바꾼다 -- test 작성 주체 몫.
(b) 또는 이 card 에서는 하지 않는다: ly_slice_density 만 `ly_point` 로 W_m 에서 분리(O-24 (가), 구현 완료)하고, 세 블록의 W_m 재계산(값 불변, 비용만)은
    후속 card 로 미룬다. 현재 test 기대는 모두 통과한다.
(c) W 표지(`canonical_naming.py:55`)를 어떤 W 로 둘지: 참고 W_m 유지 / 슬라이스 실현 W / 표지에서 제거 중 하나를 정한다.
code 는 (a)~(c) 결정 전까지 세 블록·canonical_naming 을 바꾸지 않는다.
