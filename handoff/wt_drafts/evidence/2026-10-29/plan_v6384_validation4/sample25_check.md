# '이미 닫힘(a)' 68건 무작위 25건 원문·엔진 대조 (검증 4)

표본: `random.Random(20261029).sample(68, 25)`. 엔진 E = `wt/integ-it12/skills/analog-gmid-design/gmid_engine` @ `b12792ab`(읽기만). 계획 = `00628569` 스냅샷(`snap/`).

| ID | 닫은 근거(재감사) | 검증자 실측 | 판정 |
|---|---|---|---|
| DF-06 | 구조 규칙 F, `except Exception` 0 | `grep -rn "except Exception\|except BaseException\|except:"` 비 test 0건, `test_rule_f_no_broad_except`(`tests/structure/test_structure_rules.py:46`) 있음 | 닫힘 맞음 |
| DF-10 | `lut/id_inverse.py` DF-10 대체, DEC-87 단조 검사 | 모듈 머리 1~8행 'DF-10 … 단조성' 명시, `test_curve_check.py:26,33` 단조 위반 test | 맞음 |
| DF-11 | LUT 실패 → `SealViolationError(lut_query_failed)` | `tests/sizing/test__helpers_lut.py:53-58` 확인. 비 test `= 1.0`은 행렬 계수뿐 | 맞음 |
| DF-13 | 모듈 수준 `id()` 키 0, 규칙 G | `core/bounded_lru.py:8`·`core/fingerprint.py:11` 'id() 없음'. 단 `search/search_context.py:58 self.cache = {}`(EvalKey → EvalResult, 상한 없음·실행 수명)·`:67 self.cell_floors = {}` 실재 -- 검증 4 M-1 | id 키 부분 맞음, '캐시 슬롯' 잔여는 M-1 |
| DF-16 | DEC-78 `supply_current_dc` = `counted_rails` 합 | `metrics/supply.py:1-14` docstring 그대로 | 맞음 |
| DF-19 | `supply_nets` 선언, 이름 무관 test | `test_rails.py:31`, `test_bulk_default.py:103` 존재 | 맞음 |
| DF-20 | 규칙 D(`# derive:` 없는 숫자 FAIL) | `structure_checks.py:40-42,771` 규칙 D. `min_vds_by_role`은 `authoring/_spec_fields.py:53` `CIRCUIT_SPECIFIC_KEYS`(거부 키). 참고: MOD7 복사 정의 숫자 62개는 `_copy_manifest.py` 면제(design 2.2, 기존 정책) | 맞음 |
| DF-27 | `lut/axis_guard.py:17` 축 밖 거부 | 10~20행 `lut_axis_out_of_range` raise 확인 | 맞음 |
| DF-31 | 회로별 보상 함수 0 | `_COMPENSATION_REGISTRY`·`def _comp_` 0건 | 맞음 |
| DF-32 | 규칙 I `headroom_role` 금지 키 | `structure_checks.py:1001-1008` `TAG_ROLE_KEYS_U50`에 포함, 운영 코드 사용 0 | 맞음 |
| DF-33 | 스키마 밖 키 거부 | `stack_groups_override`·`row_split`는 `_spec_fields.py:52` `CIRCUIT_SPECIFIC_KEYS`(거부)에만 | 맞음 |
| I-A7 | `sizing/scc_newton.py`·호출 | 머리 1~6행, `block_columns.py:58` import | 맞음 |
| I-B8 | 봉인 3 `sizing/seal_kcl.py` | 머리 1~8행 tol_I 식, `seal.py:24` 배선 | 맞음 |
| I-G1 | U-12 + `compensation` 무시 태그 | `authoring/topology_schema.py:22` `IGNORED_TAG_KEYS`, `search/iv_speed.py` 머리(PM_FLOOR = atan(1) 유도) | 맞음 |
| I-G2 | 일반 보상 규칙, 극점 노드 | `graph/pole_nodes.py:1-9`(모든 비교류접지 노드) | 맞음 |
| I-G4 | 정지전류 = θ 전류 기저 | `sizing/current_basis.py:1-14`(유리수 기저, 자유 열 = θ) | 맞음 |
| I-G6 | `graph/stage_bfs.py` | 머리 확인 | 맞음 |
| I-H3 | E-22 + O-118 2번 수용, 재개 조건 | 계획 680행에 '다시 열 조건: CMP-1·CPG-1 … SPICE 통과인데 엔진 FAIL' 기재, 2322행 E-22 | 맞음 |
| I-H5 | LA-0 분류·LA-1 범위 15 (f)·완료 조건 9 (e) | 계획에 sf 봉인 재현 문언 5곳, 1853행 출처 `h_judgment.md` §5 Q3 | 맞음 |
| GB-2228 | 2230행 범위 3 추가(E-10)가 대체 | 스냅샷 2164행 (4) 문장 삭제, history에 원문 1건 | 맞음 |
| GB-1339 | 마일스톤 1 → history(P-14) | 계획 본문 삭제, history 원문 있음 | 맞음 |
| U-08 | 2026-09-17 선언 완료 9/9 | 행 문언 그대로 '닫힘' | 맞음 |
| U-57 | Q8 확정 예산 유지 | N8 위험 표 2562행 이관 | 맞음 |
| U-112 | O-144 되먹임 없음·LA-1 front 판정 | O-124 행·U-112 필요 시점 칸 일치 | 맞음 |
| U-123 | E-23 = EO-1 '출력 부하 한 번만' + LT-1 순서 3 | 2321~2322행 E-23 행 확인 | 맞음 |

결과: 25/25 닫는 근거가 실제로 그 항목을 닫는다(DF-13은 id 키 부분만 닫히고, 같은 행의 '상한 없는 캐시' 관찰이 남긴 `sctx.cache` 슬롯 소유 문제는 검증 4 M-1).

추가 실측: NB-1 삭제 근거 -- 13 spec 중 `feedback.elements = []` 12개 모두 `noise_out_int_vrms` 0, current_reuse만 잡음 1·Cf1·Cf2(맞음). `pipeline/entry.py`는 엔진에 없음(`ls pipeline/` = stage_a·stage_a_budget·stage_a_report·stage_b), 구조 규칙 상수 `BROAD_EXCEPT_ENTRY_FILE = "pipeline/entry.py"`(`structure_checks.py:49`)만 있음 -- M-2 근거. 엔진 `except ValueError` 포획 10곳, `pytest.raises(ValueError)` 202곳(재감사 수치와 같음).
