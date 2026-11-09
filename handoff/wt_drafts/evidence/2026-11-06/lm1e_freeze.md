# card 20261106-lm1e 순서 3 -- freeze·base 확인 (auditor, 2026-11-06)

- 대상: test 머리 `f7025592`(`fcf7c300`·`f7025592`, 2커밋, tests/ 아래 41파일 +1444 -361, tests 밖 경로 0), base `56d88fe7`(엔진 미변경).
- 격리: `C:/Users/HSLEE/AppData/Local/Temp/la1s_lm1e_a3/iso`(`--no-hardlinks --no-local` 복제 + origin 제거). 실제 저장소 `git status --short` 줄 수 시작 73 = 끝 73(변경 없음 확인 별도).
- 기록: `wt/20261106-lm1e-audit/.ai/verification/20261106-lm1e/base_check.json`, `red_base.json`(red 384개 id·예외 타입·해시). 판정 기록 본체 `.ai/verification/20261106-lm1e.json`은 red-green이 `code_commit` sha1 필수(`_schema.json`)라 지금은 못 쓴다 -- 순서 7. 지금 틀린 값으로 채우지 않았다.

## freeze 판정: **test 수정 필요 (1 Major + 1 minor)**

| # | 항목 | 등급 | 조치 |
|---|---|---|---|
| F-4 | 지문 항목 없음 단언 약화 | **Major(기준 약화·interface 이탈)** | test 수정 또는 사용자 승인 |
| RT | `RETIRED_TESTS_lm1e.md` covered_by 이름 오기 | minor | test 수정(문서) |

나머지 (1)(2)(3)(5)(6)(7)(8)은 동결 가능, 아래 기록 사항 포함.

## (a) red 실측

작업 트리 = base 엔진 + test `f7025592`. 변경된 test 파일 34개 전체(integration 9, layout 1, lut 16, metrics 4, search 2, sizing 2), cwd `gmid_engine/tests`, ngspice 0, `--run-slow` 없음.

- 결과 **134 failed, 616 passed, 13 deselected, 250 errors**(181 s). red 합 384. (작성자 보고 'lut 117 failed'는 errors 제외 수치와 맞는 범위, 재현.)
- 파일별 red: integration 193(이름 맞춤만 바뀐 파일의 `loc.midpoints_paths` AttributeError), lut 187(helpers_bins 22·bin_rule_location 12·data_location 13·fingerprint 6·lut_memo 7·lut_set 28·midpoint_checks 16·provenance 20·slope_unit 7·table_cache 6·tolerance 20·vdsat 14 외), metrics 6, search 2, sizing 2, layout 1.
- 이유 구분:
  - **서명/형식 이유**(AttributeError `midpoints_paths`·`midpoint_sources`·`midpoint_bracket`, TypeError `_path_isfile(list)`, 설정 배열 거부): 약 358개. interface 표 base 열이 '새 형식 거부'라 계약대로. T-1·T-2·T-3·T-4·T-5·T-9, F-1~F-6, K-1~K-5, C-1~C-3, G0~G7b, B-1·B-2가 여기 든다. **이 test들의 값 이유(D7 거부 논리·셀 max·지문 항목)는 code 뒤에야 확인된다.**
  - **값 이유**(AssertionError / DID NOT RAISE / `is None` 실패) 약 26: A-0(2), A-0v(2), M-1, J-c, J-a, J-b, P-1, P-2, U-1, T-6(base에 D7 없음), G-1, 설정 단일 객체 거부·저장소 설정 핀(설정이 아직 배열 아님). 이 값 이유 red는 interface 표 '기대'와 같은 방향(base: 정의된 셀 max → 값, 새: None)이다. 예) A-0 base는 vds 0.1에서 셀 1 값(`0.00195`·`0.0078` 따위, `is None` 실패), J-b base는 `SealViolationError`를 내지 않고 수렴.
- **base에서 green인 새 이름 test 13**: 전제 5(R-0, J-a0, J-a control, J-b premise, M-0 -- 전제는 base에서 서야 한다, 맞음), T-7(기대가 '전과 같음'), 그리고 **설정 배열 원소 거부 7**(`empty_array` 1 + `bad_entries` 6). 마지막 7개는 base가 배열 자체를 `lut_location_config_invalid`로 거부해 **틀린 이유로 통과**한다(interface L-1 base 열은 red). 변별력은 code 뒤 V3 뮤테이션과 `lut_location_*` 거부 사유 분기 확인으로 본다. 동결 장애는 아님.
- **`tests/structure` + `search/test_canonical_order.py` + `sizing/test_s2_values.py`: 249 passed, 1 deselected, failed 0.** 작성자가 말한 `test_rule_h_tests_mirror_sources` 1 failed(마커 덮어쓰기, 기존 위반 21)는 내 실행에서 재현 안 됨(제외된 1건이 그 test인지는 `-k` 없이 확인 안 함 -- 통과로 세지 않음). 2회로 연기는 base에서 AttributeError뿐이라 생략(O-229).
- **안 돌린 것**(통과로 세지 않음): 13 deselected(실데이터·slow 표지), `tests/convergence/test_converge_point.py` R-2(변경 파일 아님, WB-1 red), 전체 test, ngspice 쓰는 실데이터 test.

## (b) 작성자 (1)~(8) 항목별 판정

| # | 작성자가 interface와 다르게 한 것 | 판정 | 근거 |
|---|---|---|---|
| (1) | G-1 금지어와 U-1을 문자열 조각 연결로 둘 다 만족 | 동결 가능 | G-1 스캔(내가 따로 재현)은 hit이 engine 5파일(`lut/data_location.py`, `lut_set.py`, `lut_types.py`, `midpoint_checks.py`, `search/find_front.py`)뿐이고 tests hit 0 -- code가 지우면 G-1이 통과 가능. 조각 연결은 금지어 grep 자기 충돌을 푸는 표준 방식이고 단언 대상(옛 키 부재, 키 집합 = 넷)은 그대로. |
| (2) | J-b 입력을 nmos 꺼짐 열·(y1,y2)=(0.2,0.7)로 | 동결 가능 | 이유(pmos 꺼짐이면 정의역 밖 `lut_query_failed`가 먼저)가 입력 선택이고 단언(`SealViolationError`, reason `tol_v_undefined`, `__cause__` ≠ Nonconvergent)은 interface 그대로. 통과 spy는 원 함수를 부르고 인자·결과만 기록(값 주입 0). 전제 test가 base에서 green(M1이 [0,0.25) 칸에서 조회되고 pmos 셀은 값)이라 입력이 의도대로임을 base에서 확인. J-b 본 test는 base에서 DID NOT RAISE로 값 이유 red. |
| (3) | P-2를 `dc_tol_v` None tamper, 기존 oracle `_tol_v` 변경 | 동결 가능(기록: interface 이탈 minor) | interface P-2는 J-a 스냅샷 재사용이나 M3가 `dc_coord`에 들 수 없어 `tamper`로 소비자 입력만 만든다. `table_at` → None 경로는 J-a·P-1이 값으로 덮고, P-2는 소비자(`icm_config_window`가 None을 읽고 `tol_v` None을 내는가)만 본다 -- 엔진 우회·cache·사본 아님(테스트 입력 구성). 기존 oracle `_tol_v`는 스냅샷 열에서 직접 계산하는 독립 식(피검 함수 아님)이며 새 규칙(하나라도 None이면 None, 계획 표 10행)과 일치. P-2 base red는 값 이유(`tol_v`가 M2 값). 사용자 승인 대상은 아님(기준 약화 아님, 규칙 강화). |
| (4) | F-4를 '중점 항목 지운 provenance 지문 = 중점 없는 로드 지문'으로 | **Major -- test 수정 필요** | interface F-4: "T-7 → 지문에 `midpoints_sha256` 항목 없음(독립: `core.fp_of`로 항목 tuple 직접)". 작성자 형태는 `lut_fingerprint`(피검 함수) 자신으로 양쪽을 만들어 비교하므로 **엔진이 중점 없을 때도 `("midpoints_sha256", None)`을 항상 더하는 결함을 못 잡는다**(양쪽 지문 모두에 같은 항목이 들어 같다). 즉 '항목 없음'과 '상수 항목'을 구분 못 하는 oracle = 피검 함수로 만든 기대값. 기준 약화 -> Major. 대안: (A) `fp_of(items)`로 항목 tuple을 직접 만든다(`LutProvenance`의 `manifest_sha256, generator_sha256, slices, cap_sha256, cap_conditions, bin_rule_sha256` + `_basis`; CONTRACT 1.5 문장은 6항목이라 stale -- `bin_rule_sha256` 항목이 코드에는 있다, 작성자가 CONTRACT를 읽고도 이 간극에 막힌 듯) -> interface 원안. (B) 사용자가 약화를 승인(F-1·K-3이 '중점 있으면 항목이 들어 지문이 달라진다'는 것은 이미 덮고, 부재 쪽만 못 덮음). 어느 쪽이든 오케스트레이터 결정. |
| (5) | G4 manifest 직접 수정 | 동결 가능 | toy manifest JSON에서 `generator_sha256` 키만 지워 'manifest에 없으면 언제나 거부'(G4 문언)를 만든다. toy 입력 구성이며 단언은 `lut_conditions_mismatch`·`key: generator_sha256`. 엔진 값 사본 없음. |
| (6) | 실데이터 기대 근거 교체(w_key 72/84), `test_real_fp_midpoints_item` 형식, 폐기 단언 | 동결 가능(기록 필요) | 72/84 옛 실측 문자열(p50 0.97 등)은 중점이 없던 때의 값이고 D7 뒤에는 이 폭도 외부 값을 가져 정의상 성립하지 않는다. 대신 독립 구현(`midpoint_ref`)이 만든 외부 값을 넣은 기대와 전 셀·분위수(`rb` 허용)를 대조 -- 변별력 유지(`sorted(ext) == external bin 앵커`까지 단언). 약화 아님이나 CONTRACT 5.2 갱신(작성자 보고)은 code/문서 몫. `test_real_fp_midpoints_item`은 '중점 없는 실 로드'가 D7로 불가해 '중점 지운 provenance 지문 ≠ 원 지문, 하나 덜어도 ≠'로 바뀜 -- 항목 존재 쪽은 보존, 부재 쪽은 toy F-4(위 (4))로 이관. 폐기 표(19개 삭제 함수)를 base..T diff와 대조: 삭제 함수 19개 중 재서명 5개(`test_real_*` 3·`test_midpoint_table_fields`→`test_lm1e_…`)는 같은 이름·다른 서명으로 재추가되어 실삭제는 14개, 전부 `RETIRED_TESTS_lm1e.md`에 사유·`covered_by`가 있다. 미기재 누락 0. **단 covered_by `test_c2_other_width_has_no_midpoint_table`은 실제 이름 `test_midpoint_c2_other_width_has_no_midpoint_table`과 다르다(minor 오기, 수정 필요).** |
| (7) | 목록 밖 실 LUT 적재 미점검 | 동결 가능(위험 기록) | 내 grep: 실 LUT 적재 지점은 전부 `loc.midpoints_paths`로 맞춰져 있고(이름 맞춤 25파일 + sizing/conftest) 실 LUT를 `verify_midpoints` 없이 적재하는 test는 0. 합성 toy 적재(`TOY_SPEC` 최소 폭 1.5 µm)는 D7 영향 여부가 code 실행 때만 드러난다 -- interface가 이미 '목록 밖 `bin_missing_external`이면 멈추고 보고'를 요구하고 A-2가 잡는다. |
| (8) | `lut/CONTRACT.md` 1.5 한 단락 열람 | 동결 가능(기록) | interface 머리: "test 작성 주체는 엔진 소스를 보지 않고 이 문서만" -- CONTRACT.md는 엔진 폴더의 문서이지 소스 코드가 아니다. 한 단락만 열람했고, 얻은 정보(지문 항목 목록 6개)가 stale이라 오히려 (4)에서 독립 oracle을 못 만들게 했다. 코드 구조·자리를 베끼지 않음. 기록만. |

## (c) 엔진 동작 우회(값 사본·cache) 점검

- 새 test 코드에 cache·memo·모듈 dict·값 사본으로 기대를 만드는 곳 0(grep + diff 읽기). J-b spy(`_AtSpy`)는 원 표 객체를 감싸 `at` 호출 인자·결과를 리스트에 기록만 하고 반환값은 그대로(값 주입 0). K-1~K-5는 공개 `TableCache.events`만 읽음.
- 기대 oracle: tol 셀 값은 `tol_cell_ref`·`midpoint_ref`·`vdsat_loo_cell_ref`(conftest 독립 구현)과 손 식, `_tol_v` 스냅샷 열 직접 계산, 설정 자료 id는 `core.fp_of` 직접. 피검 함수로 기대를 만든 곳은 **F-4 하나**.
- 정본 우회: P-2의 `dc_tol_v` tamper는 소비자 입력 구성이다(위 (3)).

## (d) 동결 조건 (모두 test 쪽)

1. F-4: (A) 항목 tuple 직접 `fp_of` 원안으로 고치거나 (B) 사용자 기준 약화 승인을 받는다. O-229 기준 약화는 Major.
2. `RETIRED_TESTS_lm1e.md` covered_by `test_c2_other_width_has_no_midpoint_table` -> `test_midpoint_c2_other_width_has_no_midpoint_table`.
3. (권고, 동결 조건 아님) 설정 배열 원소 거부 7 test가 base에서 틀린 이유로 통과 -- code 뒤 V3에서 변별력 확인.

위 1·2가 고쳐지면 동결 가능. 값 이유 red 26과 서명 이유 red 약 358의 구분은 `red_base.json`에 있다. 수정된 test 커밋을 받으면 base 재실행은 F-4 파일(`lut/test_fingerprint.py`)과 구조 test만 다시 돌린다(나머지는 불변이므로 이 측정 재사용).

## 부록: 항목 수치
graph 정본·소비 확인(이 단계 해당): test 변경만이라 엔진 필드 0, 소비자 0 해당 없음, 정본 우회 의심 0(test 쪽 확인 -- (c)), KVL·KCL 관계 미적용 해당 없음, graph 밖 저장 자리(test) 0.

## 재확인 (test 머리 `cf72a278`, 병합 `8d1b9b5a` = card `1d43e754` interface §4 지문 10항목 계약)

**동결 판정: 동결 가능** (앞 절의 동결 조건 1·2 해소, 3은 권고 그대로 code 뒤 V3).

1. F-4 `lut/test_fingerprint.py::test_lm1e_f4_fp_item_tuple_contract` (diff 직접 읽음)
   - 기대를 `core.fp_of` 로 직접 만든다. `_fp_items_1_to_7` 가 interface §4 표 1~7(키·순서·값 출처)을 공개 칸(`provenance.*`, `cap_map`)에서 모은다. 새 test 안에 `lut_fingerprint` 호출 0(import 줄만 남아 다른 test 가 씀).
   - (a) T-7 꼴(중점·잡음·mismatch 없음): `plain.fp == fp_of(1~7)` 이고 `plain.fp != fp_of(1~7 + ("midpoints_sha256", None))`, `!= fp_of(1~7 + ("midpoints_sha256", ()))`. 엔진이 항목을 늘 더하면 첫 등식이 깨지므로 앞 판의 구멍(상수 항목 구분 불가)이 닫혔다. 표의 7항목 키·순서·내용은 base 엔진 `lut/fingerprint.py` 와 일치함을 읽어 확인(기대가 엔진 모양을 우연히 베낀 것이 아니라 표와 엔진이 같다는 뜻).
   - (b) T-1: `with_mid.fp == fp_of(1~7 + ("midpoints_sha256", 두 파일 raw sha 정렬 tuple))`, sha 는 파일에서 `hashlib.sha256` 직접. 항목 존재·값·순서(8번째)를 고정한다.
2. covered_by: `RETIRED_TESTS_lm1e.md` 가 `test_midpoint_c2_other_width_has_no_midpoint_table` 로 정정됨(실제 함수명과 일치 확인).
3. 이 새 머리는 앞 머리 대비 tests·docs 만 변경(엔진 소스 diff 0, 비-test·비-docs 경로 0).
4. 재실행(격리 복제본 `iso` 를 `cf72a278` 로 detach, base 엔진 56d88fe7 소스 그대로):
   - `lut/test_fingerprint.py`: **4 failed, 7 passed, 2 errors** -- 4 failed = F-1·F-2·F-3·F-4, 모두 `TypeError: _path_isfile: path should be string ... not list`(base 가 `verify_midpoints` sequence 를 못 받는 서명 이유, interface 표 base 열 '새 형식 거부'와 같음). 작성자 보고(4 failed F-1~F-4 TypeError)와 일치. 2 errors 는 실 LUT 픽스처(`midpoints_paths` 부재) 서명 이유.
   - F-4 의 값 이유(등식 (a)(b))는 서명 이유에 가려져 code 뒤에야 확인된다 -- 앞 판과 같은 한계.
   - `tests/structure`: **189 passed, 1 deselected, failed 0**(작성자 보고와 일치. 앞 절의 249 는 canonical_order·s2_values 를 더한 수라 다르다. 그 둘은 이 재확인에서 안 돌림 -- 앞 측정 재사용, 변경 없음).
   - 나머지 카드 test 는 앞 측정(red 384)을 재사용한다. 이번 변경이 닿은 파일은 test_fingerprint.py 하나라 그 파일만 새로 쟀다.
5. 남은 python 프로세스는 내 것 0(pid 504 다른 agent 것은 건드리지 않음).

## 재확인 2 (test 머리 `fffe989f`, 병합 `b86ecce0` = card `686bc7a2` dispute 정정, 위임 A-159)

**동결 판정: test 수정 필요 -- Major 1건(72 case 삭제), minor 1건(cyclic 물리 전제 단언). 나머지는 동결 가능.** `cf72a278..fffe989f` 의 tests diff 를 직접 읽었다(엔진 소스 diff 0, docs 2 + tests 7파일).

### (1) 기준 약화 점검
- **cyclic `d["vds"] < _floor(...)` 단언 삭제 -- minor, 동결 가능(조건 1개 권고).**
  - 삭제 이유는 사실이다: base 엔진 `sizing/block_dc.py:508·511` 의 `tol_v_undefined` 는 `detail={"reason": REASON_TOL_UNDEFINED}` 뿐이고 `vds` 키가 없다. interface §8(A-159)이 기대 사유를 `tol_v_undefined` 로 정했으므로 detail 의 `vds` 를 단언할 근거가 interface 에 없다.
  - 그 단언이 고정하던 것은 '거부 원인 = VDS 가 하한 아래'였다. 지금 이 물리 앵커는 (i) 입력 구성: 수렴점 VDS = vin − 0.6 = 0.1·0.15 가 하한 0.25 아래, (ii) 같은 회로의 대조 case `[0.9-True]`(VDS 0.3 ≥ 하한)가 풀린다는 단언이 맡는다. 이 둘로 '하한 아래면 거부, 위면 통과'가 판별되므로 원인은 덮인다. 다만 하한 아래라는 사실을 test 가 명시 단언하지는 않는다.
  - 고치는 방법(card 수정 불필요, test 만): 거부 case(`ok=False`)에 전제 `assert y < _floor("nmos", "F")`(입력의 손 계산, detail 에 기대지 않음)를 더한다.
  - 기록(LA-1 재점검 입력): 하한 아래 VDS 의 거부 사유가 '정의역 밖 lut_curve_undefined' 에서 '허용오차 미정 tol_v_undefined' 로 바뀌어 진단 정보가 줄었다. fail-closed 는 유지. A-159 위임 범위다.
  - base 재현: 두 case 모두 `assert 'lut_query_failed' == 'tol_v_undefined'` (값 이유 red, test_block_dc.py:1093).
- **nmos w_key 72 case 삭제 -- Major(기준 약화), 사용자 승인 없이 복원으로 해소 가능.**
  - 전제는 맞다: 내가 실 manifest 를 직접 읽어 nmos 슬라이스 20개 중 W_min 0.42 µm 미만 2개(0.36 = 키 72, 0.39 µm = 키 78)를 확인했고 `widths` nmos = 18·pmos = 12 도 독립 재현했다. 그래서 '72 도 widths 안'이라던 앞 판 문언 철회는 옳다.
  - 그러나 삭제는 맞지 않다. 키 72 는 중점 파일이 없어 **값이 LM-1e 와 무관하게 불변**이고(tol 셀은 지문과 무관), 옛 기대(외부 값 없음, `missing_external ≥ 1`, 계약 5.2 실측 p50/p90/max 0.97/1.31/1.39 mV)가 그대로 유효하다. 실 LUT 에서 'widths 밖 폭은 D7 거부 대상이 아니고 외부 값 없이 `missing_external` 로 남는다'는 유일한 실데이터 보증이 사라졌다(toy T-4 와 R-1(i) 키 집합 등식이 논리는 덮지만 실 슬라이스 값 불변은 덮지 않음). 대체 폭 없이 case 만 지운 것은 약화다.
  - 고치는 방법: card 쪽 — interface §7 A-159 문단 끝에 '`widths()` 밖 폭(실 LUT nmos 키 72·78)의 실데이터 기대는 옛 기대 그대로(외부 값 없음, `missing_external ≥ 1`, 값 불변)이며 두 test 의 이 case 는 삭제하지 않고 widths 밖 분기로 둔다' 한 줄. test 쪽 — `test_real_cells_match_independent`·`test_real_contract_measured` 에 nmos 72 case 를 되살려 `widths()` 밖이면 옛 분기(`"external" not in sts and missing_external ≥ 1`, 옛 p50/p90/max)를 쓰게 하고, `RETIRED_TESTS_lm1e.md` 22행의 '72 case 는 삭제' 문장을 '72 는 widths 밖 -- 옛 기대 유지'로 고친다. 키 78 case 추가는 선택. 새 상수 없음(옛 test 가 이미 가진 값).
- **`test_widths` 20 → 18 -- 동결 가능.** 기대 개수 18 은 실 manifest 에서 W ≥ W_min 슬라이스를 직접 센 값과 같다(독립). 그 test 의 `exp` 도 슬라이스 파일에서 유도하므로 개수 상수가 사실과 어긋났던 낡은 값을 바로잡은 것이다. 약화 아님.
- **`test_lut_single_source` 배열 순회 -- 동결 가능.** 선언 npz 이름 집합과 sha 검사 대상이 원소마다 확장될 뿐 단언 강도 불변(`_file_entries` 가 객체·배열 둘 다 받음, `parent.mkdir` 는 하위 폴더 허용 때문).

### (2) J-a `N3 ⊆ item.nodes`
- interface §5 J-a(A-159 (3)(c))는 N3 = '`dc_path_values` 경로 소자에 M3 가 든 넷'을 test 가 스냅샷 열에서 유도하고(이 toy 에서 `pb`·`vdd`, `vout` 아님), 각 넷의 봉인 1·3 행 tol = None → 그 item undefined 를 요구한다. 구현은 이와 일치: `_nets_with_m3_on_path` 가 `node.dc_path_values` 열에서 `relation[1] == "M3"` 인 넷을 모으고, 비면 `pytest.fail`(전제), 각 넷을 `items[n].nodes` 에 대해 단언, J-a0 전제 test 도 N3 비어 있지 않음을 먼저 단언.
- 한계(기록): base 에서 J-a 는 `dc_tol_v["M3"] is None` 에서 먼저 값 이유로 실패(`assert 0.0078 is None`)하므로 `net in items[n].nodes` 줄은 base 에서 실행되지 않는다. 레일 넷 `vdd` 가 봉인 1·3 item 의 `nodes` 에 드는지는 code 뒤에야 확인된다 -- 안 들면 card dispute 재발 후보(이 판정에서 구분: card 쪽 N3 정의 문제이지 test 결함 아님).
- N3 유도는 upstream 열(`dc_path_values`, 이 card 변경 0)을 읽는 것이고 판정 대상 함수(`dc_tolerances`·봉인 블록)로 기대를 만들지 않는다 -- 정본 열 소비이지 재계산·사본 아님.

### (3) 피검 함수로 기대 만들기
- 이번 diff 안 0. `_nets_with_m3_on_path` 는 스냅샷 입력 구조 읽기, `test_widths` 의 18 은 파일에서 센 값, 단언 사유는 interface 표. 이전 판의 F-4 문제는 `cf72a278` 에서 해소됨(앞 절).

### (4) base 재현
- 격리 복제본을 `fffe989f` 로 detach 해 base 엔진에서 변경 test 만(`-k` 로 card 관련 선택): **9 failed, 25 passed, 8 errors**. 작성자가 말한 4 failed(J-a·cyclic 2·P-1)가 모두 재현됐고 나머지 5 failed 는 선택에 같이 든 J-b·A-0v(2)·T-8(2)로 앞 측정과 같은 값 이유 red 다. 8 errors 는 실 LUT fixture(`LutLocation.midpoints_paths` 부재 AttributeError) -- 작성자 말 '7 errors'에 `test_real_widths` 1건이 더해진 수(`test_widths` 도 같은 fixture, 서명 이유).
- cyclic 두 case: `lut_query_failed` ≠ `tol_v_undefined` 값 이유 red. J-a: tol 값 이유 red. P-1: `0.0078 is None` 값 이유 red.
- `tests/structure`: **189 passed, 1 deselected, failed 0** (작성자 보고와 일치).
- 안 돌린 것: 앞 판과 같음(13 deselected 실데이터, 전체 test, ngspice, 2회로 연기).

### 동결 조건 (모두 test/card)
1. 72 case 복원(위 방법, card §7 한 줄 + test 두 곳 + RETIRED 22행) -- Major.
2. cyclic 거부 case 에 `y < _floor` 전제 단언 -- minor.
이 둘이 반영되면 동결 가능. 반영 뒤 재측정은 `lut/test_vdsat_tolerance.py`(실 LUT fixture 는 base 에서 서명 이유 red 라 변경분 확인은 collect 와 code 뒤 몫)와 `sizing/test_block_dc.py` cyclic 만 다시 돌리면 된다.
