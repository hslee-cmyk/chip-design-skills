# #24 R14 미러 비 강제 -- 착수 전 실측 (2026-10-28)

- 역할: 계획 v6.38.3 작성자(일곱째 커밋) 실측. 엔진은 읽기·import만 했다.
- 엔진: `wt/integ-it12` `d759838a`(`skills/analog-gmid-design/gmid_engine`). 끝난 뒤 `git -C wt/integ-it12 status --short` 빈 출력 확인.
- 스크립트(엔진 밖): `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/r14/r14_measure.py`, 결과 같은 폴더 `r14_out.jsonl`(회로마다 append).
- 실행 경로(공개 API): `load_topology` → `load_sizing_spec` → `dc_inputs_from_spec` → `build_s1` → `lift_s1` → `dc_rails` → `s1_symmetry` → `dc_current_basis`(커널 컨텍스트와 같은 순서, LUT 불요). `PYTHONDONTWRITEBYTECODE=1`.
- 대상: library 9회로(heldout은 재지 않았다).

## 질문과 판정 방법

1. **미러 출력 전류가 독립 θ 성분인가**(DEC-70 전류 변수 정의 '강제 관계로 정해지지 않는 가지 전류의 독립 기저'): 미러 묶음 = S1 `graph.rel_matching_ratio`(gate가 레일이 아닌 `gs_groups` 묶음, 같은 kind·gate·source). 묶음 구성원마다 전류를 KCL 해 공간 좌표(자유 기저 + 값 선언 전류원)의 선형식으로 읽고(`CurrentBasis.rows`), 구성원 전류 벡터의 rank를 정확 유리수로 잰다. rank = 구성원 수이면 KCL이 구성원 전류비를 정하지 않는다(I_out = ρ·I_ref 강제는 자유도 하나를 줄인다 = 지금 출력 전류는 독립 θ 성분). 두 구성원 벡터가 비례(rank ≤ 1)이면 KCL이 이미 비를 정한다.
2. **`graph.rel_matching_ratio` 소비자 수**: `git grep`(엔진 전체, tests 제외).
3. **선언된 비율 수**: library·heldout `*.sizing_spec.json`·`*.topology.json`·`*.structure.json`의 비율 키.

## 결과

| 회로 | θ 전류 자유 기저 수 | 미러 묶음 수 | 묶음(diode 기준) -- 구성원 전류 rank |
|---|---|---|---|
| common_gate_amplifier | 1 | 0 | - |
| current_reuse_telescopic_ota | 22 | 3 | {M10,M12,M19,M21,M38,M5,M66,M68} diode=M66 8/8; {M13,M17,M18_bg,M22,M6,M60,M61,M8} diode=M18_bg 8/8; {M36a,M7} diode=M36a 2/2 |
| folded_cascode | 5 | 3 | {M10,M9} diode=M9 2/2; {M11,MN} diode=MN 2/2; {M3,M4,MP} diode=MP 3/3 |
| ngcc_3stage_ff | 9 | 5 | {M3,M4,M6B} diode=M3 3/3; {M6A,M7} diode=M6A 2/2; {M14,M8} 외부 바이어스 2/2; {M10,M9} diode=M9 2/2; {M0,M12,M5} 외부 바이어스 3/3 |
| nmcnr_amplifier | 8 | 3 | {M203,M204} diode=M203 2/2; {M104,M105} 외부 바이어스 2/2; {M108,M109} diode=M108 2/2 |
| pushpull_follower_buffer | 3 | 0 | - |
| sf_pushpull_output_opamp | 7 | 4 | {M14,M16,M20} 외부 바이어스 3/3; {M3,M4} diode=M4 2/2; {M17,M6,M9} 외부 바이어스 3/3; {M11,M8} 외부 바이어스 2/2 |
| two_stage_ota | 3 | 2 | {M5,M7} 외부 바이어스 2/2; {M3,M4} diode=M3 2/2 |
| two_stage_ota_sf | 4 | 2 | {M5,M7,M9} 외부 바이어스 3/3; {M3,M4} diode=M3 2/2 |

- 미러 묶음 22개(7회로), 구성원 62개(검증 7 L-7 정정 -- 옛 '61'은 셈 오기), diode 기준이 아닌 구성원(출력) 48개. **22개 묶음 모두 rank = 구성원 수**, KCL 비례 구성원 쌍 **0** -- 지금 엔진에서 미러 출력 전류는 모두 독립 θ 전류 성분이고 KCL은 미러 비를 정하지 않는다(엔진 문언 `E/sizing/current_basis.py:12` '`matching_ratio` 관계는 비율 값 선언이 어디에도 없어 전류를 강제하지 않는다 -- 미러 출력 전류도 기저에 든다'와 일치).
- 같은 묶음 구성원은 gate·source를 공유해 VGS가 KVL로 같다(쓰기 계획: diode/쓰기 소자 하나가 ln IDu θ 성분, 나머지는 VGS 종속 -- `E/sizing/theta_schema.py` 머리 'ln_idu(쓰기 소자)'). 그래서 θ(쓰기 소자 ln IDu·L 동치류 L·θ 전류)가 정해지면 출력 소자 W = I/IDu가 정해지고 W/L 비 = 전류비가 저절로 성립한다 -- 미러 비 ρ는 파생값이다. ρ를 새 θ 종류로 두면 출력 전류 θ 성분과 같은 자유도의 두 표현이 되므로(DEC-70 '중복 계수하지 않는다'·graph 규칙 3 ⚠) 출력 전류를 기저에서 빼야 하고, 그것은 좌표 바꾸기일 뿐 물리 자유도 변화 0이다.
- `graph.rel_matching_ratio` 운영 소비자 **0**: `git grep` -- writer `E/graph/rel_matching.py`, 상수 `E/graph/s1_values.py:80·174·201`, 문서 `E/graph/CONTRACT.md:245·250`, test 3개(`tests/graph/test_rel_matching.py`·`tests/graph/test_s1_values.py`·`tests/generality/test_metamorphic_s1.py`)뿐. 만들고 배선하지 않은 필드다.
- 선언된 비율 **0**: library topology의 `"ratio"` 28곳은 모두 레이아웃 `matching_sensitivity: "ratio"` 표지(비율 값 아님), spec의 `*_ratio_*` 이름은 metric 이름(`ratio_ss_db`·`mirror_ratio_error`)뿐. 비율 값 선언 키는 spec 스키마에 없다.

## 결론(계획 반영)

- 재검토 전제 (a) 미러 출력 전류 = 독립 θ 성분 -- **성립**(22/22 묶음). (c) 선언 비율 0 -- **성립**. (d) 소비자 0 -- **성립**.
- 기본안 = '선언된 비율만 KCL 강제 + `rel_matching_ratio` 배선'(재검토 (나)). 비율 값이 선언된 미러만 전류 기저에 I_out = ρ·I_ref 강제 행을 더해 그 가지를 기저에서 뺀다(DEC-70 전류 변수 정의 '전류 강제 관계 -- 미러 비율' 문언 그대로). 미선언 비는 W/L 비 파생값(보고). library 발동 0(변화표 무변화 예상).
- 계획 자리: card SF-1 범위 10(선언 키 = spec 로더 단독 소유 card와 같은 card -- 범위 8과 같은 꼴, 새 병합 순서 규칙 0). 재검토가 적은 LA-1 범위 15는 선언 자리(spec 로더)가 SF-1 소유라 병합 순서 규칙 SF-1 → LA-1이 하나 생겨(O-165 (a) ⚠) 택하지 않았다.
- 원래 취지와 다름: 2026-10-08 R14 '복원' 결정의 design 40 형태(D-GB7b 새 θ 종류 ρ, U4b 7모듈)를 바꾼다. DEC-70 θ 독립 성분 목록은 바꾸지 않는다(ρ는 θ가 아님).
