# 문서 백로그 B22 (b) -- P10 문서 커밋이 표시할 참조 문서 19줄 (HEAD `cd64170` 재확인)

재확인 방법: `check_contracts.py <후보> --repo <R> --base cd64170 --docs`(계약 5 판정기 -- 이름 집합 N은 초안 원문, 정의 위치는 base blob AST)
→ 위반 **19줄 20건**(`known-incidents.md:104`에 `_cmrr_telescopic_class_ab`와 선택 키 `telescopic_class_ab` 둘). 초안 계약 5의 19줄 목록과 같다.
원문 줄은 `git show cd64170:skills/analog-gmid-design/<파일> | sed -n <줄>p`로 뽑았다(줄 끝 공백 없음). 정의 위치 사실:

* 삭제(정의 없음 -- `A/*.py`·`run_harness.py`·`A/tests/tools/*.py` 어디에도 없음): `converge_with_parasitics`, `slew_rate`, `render_stick_diagram`(P5 `2a123ba`), 메서드 `fT`(P5, `SemiEmpiricalGmIdLUT.fT` -- 호출형 `.fT(`만 대상), `_cmrr_telescopic_class_ab`(P5b `6612902`), 선택 키 `telescopic_class_ab`(SR `_CMRR_ESTIMATOR_REGISTRY`·`_PSRR_ESTIMATOR_REGISTRY` 키는 HEAD에서 `diff_pair_tail`뿐).
* 이동: `find_interleaved_symmetric_splits` → `skills/analog-gmid-design/assets/tests/tools/interleave_splits.py`(P6 `1c5b920`). 계약 5는 줄에 `Phase 2에서`와 `tests/tools/interleave_splits.py`가 함께 있기를 요구한다.

문안 원칙: 줄 끝(또는 이름 바로 뒤)에 짧은 괄호 표시만 붙인다. 표 행은 마지막 칸 앞 셀에, 코드 블록 줄은 `#` 주석으로. 문장 흐름·줄 수는 바꾸지 않는다(다른 줄 번호가 움직이지 않게).
사용 안내 표 행(function-selection-map 35·38·80)은 표시만 붙이는 안(아래)과 행을 지우는 안이 모두 계약 5를 통과한다 -- 기본안은 표시(이력 보존, 줄 번호 불변).

| # | 파일:줄 | 이름(종류) | 현재 줄(HEAD) | 바꿀 줄(제안) |
|---|---|---|---|---|
| 1 | `references/function-selection-map.md:35` | `converge_with_parasitics` (삭제) | `\| 단일 소자, 기생 커패시턴스까지 반복 수렴시켜 사이징 \| \`converge_with_parasitics(fT, C_external, gm_id, L, lut, ...)\` \| §1 스텝 3~5를 자동 반복 \|` | `\| 단일 소자, 기생 커패시턴스까지 반복 수렴시켜 사이징 \| \`converge_with_parasitics(fT, C_external, gm_id, L, lut, ...)\` (Phase 2에서 삭제) \| §1 스텝 3~5를 자동 반복 \|` |
| 2 | `references/function-selection-map.md:38` | `slew_rate` (삭제) | `\| slew-rate 계산 \| \`slew_rate(ID, C)\` \| \|` | `\| slew-rate 계산 \| \`slew_rate(ID, C)\` (Phase 2에서 삭제) \| \|` |
| 3 | `references/function-selection-map.md:80` | `render_stick_diagram` (삭제) | `\| PDF 스타일 텍스트 렌더링(터미널 확인용, **리포트의 시각 자료 아님**) \| \`render_stick_diagram(result)\` \| ⚠️ 이 함수의 출력 문자열을 … \`renderStack()\`(SVG) 재사용 \|` | 가운데 칸만: `\`render_stick_diagram(result)\` (Phase 2에서 삭제)` (나머지 칸 그대로) |
| 4 | `references/function-selection-map.md:99` | `find_interleaved_symmetric_splits` (이동) | `\| 매칭쌍 개수가 홀수라 단독 좌우 분할이 안 될 때 \| \`find_interleaved_symmetric_splits(count_a, count_b)\` \| §2.5.4 \|` | `\| 매칭쌍 개수가 홀수라 단독 좌우 분할이 안 될 때 \| \`find_interleaved_symmetric_splits(count_a, count_b)\` (Phase 2에서 tests/tools/interleave_splits.py로 이동) \| §2.5.4 \|` |
| 5 | `references/sky130-worked-example.md:256` | `converge_with_parasitics` (삭제, 이력 서술) | `**부수적으로 발견한 버그**: 이 최적화기를 만들다가 \`converge_with_parasitics()\`의` | `**부수적으로 발견한 버그**: 이 최적화기를 만들다가 \`converge_with_parasitics()\`(Phase 2에서 삭제)의` |
| 6 | `references/sky130-worked-example.md:262` | `converge_with_parasitics` (삭제, 이력 서술) | `` `converge_with_parasitics()`는 수정 완료(현재 커밋에 반영됨). `` | `` `converge_with_parasitics()`는 수정 완료(현재 커밋에 반영됨) -- 이 함수는 Phase 2에서 삭제. `` |
| 7 | `references/stick-diagram-euler-layout.md:113` | `find_interleaved_symmetric_splits` (이동) | `` > `find_interleaved_symmetric_splits()`(§2.5.4, 개수가 안 맞는 매칭쌍도 다른 소자와 섞어 `` | `` > `find_interleaved_symmetric_splits()`(Phase 2에서 tests/tools/interleave_splits.py로 이동, §2.5.4, 개수가 안 맞는 매칭쌍도 다른 소자와 섞어 `` |
| 8 | `references/stick-diagram-euler-layout.md:215` | `find_interleaved_symmetric_splits` (이동) | `` **구현**: `find_interleaved_symmetric_splits(count_a, count_b)`가 이 조건(count_a==count_b)을 `` | `` **구현**: `find_interleaved_symmetric_splits(count_a, count_b)`(Phase 2에서 tests/tools/interleave_splits.py로 이동)가 이 조건(count_a==count_b)을 `` |
| 9 | `references/stick-diagram-euler-layout.md:464` | `find_interleaved_symmetric_splits` (이동) | `` 잡아 `find_interleaved_symmetric_splits(10,10)`의 최선 분할 `(5,5,5,5)`로 diffpair의 `` | `` 잡아 `find_interleaved_symmetric_splits(10,10)`(Phase 2에서 tests/tools/interleave_splits.py로 이동)의 최선 분할 `(5,5,5,5)`로 diffpair의 `` |
| 10 | `references/stick-diagram-euler-layout.md:1065` | `render_stick_diagram` (삭제, 예제 import) | `    Transistor, build_stick_diagram, render_stick_diagram,` | `    Transistor, build_stick_diagram,  # render_stick_diagram: Phase 2에서 삭제` (import에서 이름을 빼 예제가 실행되게 하고 표시는 주석에) |
| 11 | `references/stick-diagram-euler-layout.md:1102` | `render_stick_diagram` (삭제, 예제 호출) | `    print(render_stick_diagram(result))` | `    # print(render_stick_diagram(result))  -- Phase 2에서 삭제` |
| 12 | `references/stick-diagram-euler-layout.md:1223` | `find_interleaved_symmetric_splits` (이동, 체크리스트) | `` 구성했는가 — `build_mirror_symmetric_pattern()`/`find_interleaved_symmetric_splits()` `` (앞 공백 6칸) | `` 구성했는가 — `build_mirror_symmetric_pattern()`/`find_interleaved_symmetric_splits()`(Phase 2에서 tests/tools/interleave_splits.py로 이동) `` (앞 공백 6칸 유지) |
| 13 | `references/design-report-spec.md:92` | `find_interleaved_symmetric_splits` (이동, 사례 서술) | `` 19. **증상**: 18번의 재구성 중 `find_interleaved_symmetric_splits()`가 반환한 모든 후보로 `` | `` 19. **증상**: 18번의 재구성 중 `find_interleaved_symmetric_splits()`(Phase 2에서 tests/tools/interleave_splits.py로 이동)가 반환한 모든 후보로 `` |
| 14 | `references/design-report-spec.md:308` | `find_interleaved_symmetric_splits` (이동) | `` `find_interleaved_symmetric_splits()`로 홀수 조합의 불균등 분할을 구하고), 각 소자를 `` (앞 공백 3칸) | `` `find_interleaved_symmetric_splits()`(Phase 2에서 tests/tools/interleave_splits.py로 이동)로 홀수 조합의 불균등 분할을 구하고), 각 소자를 `` (앞 공백 유지) |
| 15 | `references/consistency-map.md:207` | `.fT(` (삭제 메서드, 이력 서술) | `` 않음): `fT_dev = lut.fT(gm_id, L, VDS, vs); fnqs_ok = fT <= quasi_static_margin * fT_dev`로 `` (앞 공백 5칸) | `` 않음): `fT_dev = lut.fT(gm_id, L, VDS, vs); fnqs_ok = fT <= quasi_static_margin * fT_dev`(`lut.fT()`는 Phase 2에서 삭제)로 `` (앞 공백 유지) |
| 16 | `references/consistency-map.md:209` | `.fT(` (삭제 메서드) | `` 있었다 — element 함수를 호출하는 대신 그 안의 공식을 그대로 베껴 쓴 것. `lut.fT()`가 `` (앞 공백 5칸) | `` 있었다 — element 함수를 호출하는 대신 그 안의 공식을 그대로 베껴 쓴 것. `lut.fT()`(Phase 2에서 삭제)가 `` (앞 공백 유지) |
| 17 | `references/known-incidents.md:104` | `_cmrr_telescopic_class_ab` + 선택 키 `telescopic_class_ab` (삭제, 사고 기록) | `` `telescopic_class_ab` CMRR 폐형식(`_cmrr_telescopic_class_ab`)의 self-test를 작성하며, `` | `` `telescopic_class_ab` CMRR 폐형식(`_cmrr_telescopic_class_ab`, 둘 다 Phase 2에서 삭제)의 self-test를 작성하며, `` |
| 18 | `references/known-incidents.md:125` | 선택 키 `telescopic_class_ab` (삭제) | `` 구현 예시: `sizing_recipe.py`의 `telescopic_class_ab` self-test(2026-07-31, `_crt_by_name` `` | `` 구현 예시: `sizing_recipe.py`의 `telescopic_class_ab` self-test(Phase 2에서 삭제, 2026-07-31, `_crt_by_name` `` |
| 19 | `SKILL.md:74` | 선택 키 `telescopic_class_ab` (삭제, 사고 요약 표) | `` \| 6 \| 순수 수식 함수의 self-test라는 이유로, … 역할 배정해서 씀(2026-07-31, `telescopic_class_ab` CMRR 계기) \| 그 이름을 값에 채워 넣기 전에 … \| `` | 둘째 칸의 괄호만: `` (2026-07-31, `telescopic_class_ab` CMRR 계기 -- Phase 2에서 삭제) `` (다른 칸 그대로) |

## 적용 뒤 확인

1. 문서 커밋 뒤 `check_contracts.py <목록> --repo <R> --base <문서 커밋> --docs` → 계약 5 PASS(위반 0).
2. 표시 문자열은 계약 문장과 글자 그대로여야 한다: 삭제 = `Phase 2에서 삭제`(띄어쓰기 한 칸씩), 이동 = `Phase 2에서` + `tests/tools/interleave_splits.py`. 6번처럼 `이 함수는 Phase 2에서 삭제.`도 부분 문자열로 통과한다.
3. 줄 수를 바꾸지 않으므로 다른 대상 줄 번호는 그대로다. 행을 지우는 안을 택하면 같은 파일 아래 대상 줄 번호가 한 줄씩 당겨지므로 아래 줄부터 고칠 것.
4. 대상 밖(초안 '분리한 것' 표): `SR:15`·`SR:4737/4743/5015` 엔진 텍스트, `tests/unit/test_selftest_sizing_recipe.py:2765/2791/2824`, library topology.json 주석 필드(보류), Phase 2 이전 낡은 이름(`run_sizing_pipeline` 등) -- 이 문서 커밋에 넣지 않는다.
5. 같은 이름의 단어형 `fT`(물리량 표기)는 대상이 아니다(`consistency-map.md:208/214`, `gm-id-methodology.md` 등 64곳) -- 계약 5가 호출형 `.fT(`만 보므로 건드리지 않는다.
