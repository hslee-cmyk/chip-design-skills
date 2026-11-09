# O-181 test 영향 분석 + 회귀 정정(feaf6ba2·a12b104f) 독립 검증

검증자: 독립 검증 agent(정정 작성자 아님). 실행 위치: worktree `wt/fix-lutdecl`(HEAD a12b104f, 작업 트리 수정 0 -- `git status` 빈 출력 실측).
산출물: scratchpad `pt/run_a12b_2.txt`(14개 test 파일), `pt/run_pdkdecl.txt`, `stage_a_probe.txt`·`stage_b_probe.txt`·`stage_b_probe2.txt`(엔진 읽기 전용 실행).
엔진 인용 용도(원칙 8): (1) 엔진 밖 사실 (2) 재작성 범위·소비자 목록에 한정. as-built 동작은 판단 근거로 쓰지 않음.

## 1부 -- 회귀 정정 검증

### feaf6ba2 (sky130_lut_rule_decl.json lut_generator sha256 735220… -> 54e257…)
| 확인 | 결과 | 출처 |
|---|---|---|
| O-180 두 커밋의 sky130_lut_sweep.py 변경 | b1c79487~1..a12b104f diff = `EXISTING_LUT` 상수 -> `LUT_LOCATION_JSON`, `candidates()`의 기본 앵커를 `resolve_lut_location(...).cap_npz_path`로, `--existing-npz` 기본 None. 그 밖 변경 없음 | `git diff` 실측 |
| DUT_LINE 불변 | 두 판 모두 90행 `DUT_LINE = "xdut d g s b sky130_fd_pr__{devcell} l={L_um}u w=5u ad=2.5p as=2.5p pd=7u ps=7u"` | `git show` 실측 |
| newline lf sha | O-180 전 blob(CR 제거) = 735220…(옛 선언값과 일치), a12b104f blob = 54e2570b…, 작업 트리 CRLF 파일을 CR 제거 = 54e2570b… | sha256sum 실측. 엔진 검사 `core/pdk_decl.py` 336행 `data.replace(CRLF, LF)` 뒤 sha와 같은 정의 |
| 다른 고정 자리 | 54e257 = 선언 파일 1곳. 735220 = `gmid_engine/core/CONTRACT.md:471`(계약 문장, **낡음**), `docs/03-analysis/...u3-lut-pdk-record.md:15`(이력 기록 -- 그대로 둠). test·code 고정 0 | `git grep` 실측 |
| test | `tests/core/test_pdk_decl.py` 213 passed (기본 tmp). ※ scratchpad basetemp로 돌린 첫 실행의 23 error는 Windows 경로 길이(PDK 사본 경로) 탓 -- 환경 산물, 기본 tmp에서 0 | `pt/run_pdkdecl.txt` |

판정: **맞음**. 한 가지 minor: `core/CONTRACT.md:471`의 `735220532101...` 문장이 낡았다(같은 정정에서 54e2570b…·O-180 사유로 갱신 권고, 동작 영향 없음).

### a12b104f (_GEN_SEARCH·ALLOWED_LITERALS -> lut_data/sky130_lut_v2/verification/slices_vdsat, CONTRACT 문장)
| 확인 | 결과 |
|---|---|
| 사본 sha | `slices_vdsat/sky130_dc_width_slices.py` sha256 = 8df35d2e…319df = `manifest.json` generator_sha256(실측). 저장소 밖 같은 이름 파일은 이것 1개(옛 `wt/_drafts/engine/lut_slices` 없음 실측) |
| 기준 약화 | 없음. 허용은 여전히 (파일, 리터럴) 쌍 1개(`ALLOWED_PAIRS`). 새 폴더 내용 = 생성기·로그·verification json·verify 스크립트, npz·manifest 없음 -> 옛 초안 폴더(LUT 초안 데이터 폴더)보다 좁다. join 거부(manifest·npz) 조항 그대로 |
| guard가 다른 초안 경로 거부 | `DRAFT_RE`(`_drafts/engine|lut_slices|lut_v2/`) 불변. 옛 `_drafts/engine/lut_slices` 리터럴은 이제 허용 밖 -> 거부. 자기 test(`test_literal_guard_rejects_mutations`·`test_allowed_literal_is_pinned_to_one_file`·`test_unparsable_py_fails_closed`) 통과 |
| test | test_tolerance(ngspice 실데이터 2건 포함)·test_lut_single_source 전부 통과(`pt/run_a12b_2.txt`에 FAILED/ERROR 0) |

판정: **맞음**. 개선 여지(필수 아님, 원칙 7·11): 절대 경로 리터럴 대신 위치 선언 root(`GMID_LUT_V2_ROOT` 기본값) + `verification/slices_vdsat`로 유도하면 허용 리터럴 자체가 없어진다(같은 사실의 둘째 기록 제거). 이 경우 guard의 허용 쌍도 같은 변경에서 삭제.

### 남은 실패 목록
a12b104f에서 관련 14개 파일 재실행: **20 failed + 3 error = 23건**, 목록이 2부 ①~⑤와 정확히 같다(전체 실행 `fixlutdecl_feaf6ba2_pytest_full.txt`의 20F·5E 중 test_tolerance 2E가 사라짐).

### 1부 판정: **병합 가능** (조건 없음; CONTRACT.md:471 낡은 sha 문장은 같은 병합 또는 다음 문서 정정으로 -- minor)

## 2부 -- O-181(9 -> 13) test 영향

대조: O-181(4회로 전부 library 이관, held-out 0), O-182 Q-LB1(합격 범위 library 13, M-LB1 = 옮긴 4회로 단계 A·B 도달·정지 사유 실측 = 단위 11 착수 조건), 계획 128행(`_declared_target_spec`은 출처일 뿐 정본 아님 -- N3.16·U-25).

### ① 회로 수 '9' 단언 3건
- 원인: test 기대(독립 oracle 표 PASS_TABLE·USER_BIAS_INPUTS/USER_MANIFEST_COUNTS·TABLE)가 9회로뿐. "library 집합 = 기대표 집합" 단언은 **새 회로가 기대 없이 들어오면 red가 되게 만든 guard이고 지금 제 역할을 한 것**. 엔진 결함 아님.
- 4회로 사실(JSON 직접 집계): cnr (72 MOS, 10 passive, bias_inputs 없음), erfc (29, 6, 없음), r2r (31, 4, vb1·vb3·vb4·vb5n·vb6n), rfc (35, 2, 없음); source_manifest 수 = 집계 수.

| 대안 | 장점 | 대가 |
|---|---|---|
| (가) 표를 13으로 확장 -- 값은 test 작성자가 원문·JSON에서 독립 유도, `USER_*` 칸은 held-out 판독 결정(2026-10-13·14 A~D, D-2 bias 5넷 등) 기록을 출처로 | 기준 상향(Q-LB1과 일치), guard 유지 | 4회로 × 3표 독립 유도 비용; 사용자 결정 출처가 없는 칸은 확인 질문 필요 |
| (나) 단언을 '≥ 9'나 표 부분집합으로 완화 | 즉시 green | ⚠ 원칙 18 기준 약화(사용자 승인 필요), 새 회로가 기대 없이 통과 |
| (다) test 삭제(원칙 33) | 비용 0 | ⚠ 4회로 로드·spec 계수 검증을 잃음(Q-LB1 13 합격 범위와 어긋남) |

권고: **(가)**. 판정 맞음. 사용자 결정: `USER_BIAS_INPUTS`·`USER_MANIFEST_COUNTS`의 4회로 값이 held-out 판독 결정 기록으로 이미 확정된 값인지 확인 1건(아니면 확인 질문).

### ② fixture 이름이 library와 겹침 2건
- 원인: 합성 fixture(`fx_spec_amp`, `base_valid.topology.json`)의 소자 이름 Q1..Q5가 rfc_ota 소자 이름(Q1..Q18)과 같다. test 목적 = 합성 이름이 library와 겹치지 않음(엔진이 이름에 기대지 않는지 보려는 분리). 엔진·topology 결함 아님.

| 대안 | 장점 | 대가 |
|---|---|---|
| (가) fixture 소자 이름을 13회로 이름 집합 밖으로 개명(test 작성자, 기대값 속 이름 같이) | test 취지 유지, 기준 불변 | fixture 이름을 쓰는 다른 test 기대값 동반 수정 |
| (나) rfc_ota 소자 개명 | -- | ⚠ 원칙 15(소자 이름 포함 connectivity는 사용자만), 원문 Fig. 표기와 갈림 |
| (다) 단언 삭제·완화 | 즉시 | ⚠ 원칙 18 |

권고: **(가)**, 사용자 결정 불필요(test 데이터, 기준 불변).

### ③ 구조 규칙 E 35건 (test 1건)
실제 리터럴(전부 실측):
- `_module_map.py` 'Q4'·'Q8'·'Q9' 20건 = `ModuleEntry.plan_ids` 안 **설계 40 §9 열린 질문 ID**(design 40:692 'Q8' 행 등). 회로 이름과 **우연 일치**(rfc_ota 소자 Q4·Q8·Q9). 행동 결정에 안 쓰임(메타데이터).
- `authoring/_spec_fields.py:52` 'Z' = `CIRCUIT_SPECIFIC_KEYS`(옛 회로 전용 spec 키 목록, 거부용 어휘). erfc_ota 넷 Z와 우연 일치.
- lut·metrics·sizing 14건 'VS' = **LUT 축 이름**(`AXES = ("L","VGS","VDS","VS")`, npz 키 `z["VS"]` -- 엔진 밖 데이터 형식 사실). cnr_ota 넷 VS(원 schematic 이름)와 우연 일치.
- 결론: 35건 모두 회로 이름 의존 아님. 규칙 E는 '정확 일치 어휘 검사'라서 library가 커질수록(짧은 이름 Q4·VS·Z·A·B) 엔진 어휘와 우연 충돌이 늘어난다(일반성: 9 -> 13에서 새 충돌 35건 = 이 검사 방식의 구조적 성질).

| 대안 | 장점 | 대가 |
|---|---|---|
| (가) 엔진 리터럴 개명(plan_ids를 'D40-Q8' 꼴, spec 키 'Z' 개명, LUT 축 'VS'는 적재 경계에서 별칭) | 기준 불변 | 'VS'는 외부 npz 키라 별칭 층 = 같은 양의 둘째 이름(원칙 7 ⚠); 다음 회로가 또 다른 어휘와 충돌하면 반복 |
| (나) 규칙 E 이름 집합에서 '엔진 선언 어휘'(LUT 축 선언 `AXES`, spec 키 목록, plan_ids 칸)를 정준 선언 한 곳에서 읽어 빼기 | 원인(우연 충돌) 자체를 정의로 해결, 회로 수와 무관 | ⚠ 원칙 18 기준 정의 변경 = 사용자 승인. 빼는 어휘 자리가 정확히 '선언 한 곳'이어야 함 |
| (다) (파일, 리터럴, 사유) 허용 쌍 등록(LUT guard와 같은 꼴) | 범위 좁음, 명시적 | ⚠ 원칙 18 승인. 회로가 늘 때마다 등록 증가 |
| (라) rfc·cnr·erfc 소자/넷 개명 | -- | ⚠ 원칙 15(사용자만), 원문 표기와 갈림 -- 비권고 |
| (마) `_module_map.py` plan_ids만 문자열 상수 검사에서 제외(메타데이터 칸) + 나머지는 (나) | 메타데이터와 코드 분리 | ⚠ 원칙 18 승인 |

권고: **(나)** (판정: 조건부 맞음 -- 조건 = 빼는 어휘가 엔진 안 정준 선언 한 곳(AXES·spec 키 상수·plan_ids 필드)에서 읽히고 이름 집합 축소가 그 어휘에 한정됨을 거부 픽스처로 확인). 사용자 결정 필요(규칙 E 정의 변경).

### ④ 기준선 fixture 9회로 대 library 13회로 KeyError 3건
- 원인: `fixtures/u17_1b_s0_baseline.json`이 9회로뿐인데 CIRCUITS는 library glob(13). **모듈 수집 시점** KeyError라 세 파일(test_s0_layer_9circuits·test_g10_no_recompute_9circuits·test_layer0_boundary_rows)의 **9회로 test 전부가 안 돌고 있다** -- 회귀 검출 공백(심각도 높음). 엔진 결함 아님.

| 대안 | 장점 | 대가 |
|---|---|---|
| (가) 4회로 기준선을 test 작성자가 master 기준 코드로 독립 측정해 추가(옛 기준선 출처 방식과 같음), 기준선 없는 회로는 회로별 test에서 실패(fail-closed)로 -- 수집 시점 KeyError 제거 | 13회로 회귀 보호, 9회로 즉시 복구 | 측정 비용; 단계 A가 정지인 회로(cnr·r2r·erfc)는 보고서 대조만 해당 |
| (나) CIRCUITS를 기준선 키(9)로 제한 | 즉시 green | ⚠ 4회로 회귀 보호 없음, Q-LB1 13과 어긋남(원래 취지와 다름 표지 필요) |
| (다) 삭제 | -- | ⚠ S0·G-10 결정성 회귀 보호 상실 |

권고: **(가)**, 먼저 수집 시점 KeyError를 회로별 실패로 바꿔 9회로를 바로 되살리는 것이 우선. 사용자 결정 불필요(기준선 추가는 기준 상향, 작성자 ≠ 측정자 지킴).

### ⑤ 단계 A/B 새 회로 실패 14건 (실측으로 분류)
| test | 회로 | 실제 원인 | 분류 |
|---|---|---|---|
| stage_a ×3 | cnr·erfc·r2r | test helper `_supplies()`가 topology `_declared_target_spec.supplies_v` 또는 **기본값 {vdd 1.8, gnd 0}**을 넣음. 새 회로 레일 = cnr {VDD_1V8, VSS}, r2r {VDD, VSS}, erfc {vdd, gnd, vcp, vcn} -> 엔진이 `supplies_unknown_net`·`supplies_missing_rail`로 거부(exit 7, fail-closed 정상) | **test 결함**(9회로 전제 + 발명 상수 기본값, 원칙 11; 정본은 sizing_spec `human.supplies_v.values` -- 계획 128행) |
| stage_b ×5 | erfc | 단계 A spec 로드 거부 `topology_fp_mismatch`: spec meta.topology_fp cc69e381… ≠ 현재 connectivity_fp a5710202…. 6705b911(O-174 erfc M19·M20·M21 bulk 정정)이 connectivity를 바꿨는데 spec 지문 미갱신 | **spec 데이터 결함**(O-174 반영 누락, 엔진은 올바르게 거부) |
| stage_b ×4 | cnr | 단계 A 정지(exit 2: `cs_output_low_impedance`, `loop_record_only` global_feedback/cross_coupled, `undeclared_loop_constraint`, A4 `column_unassigned` IDC·x24.M1) 뒤 단계 B 진단 모드도 `dc_resistor_cycle`(x40, VCR–VDD_1V8)로 정지 -> achievability None, graph/ach 레코드 없음 | **엔진 규칙 분기 미지원**(M-LB1 대상) + test가 '진단 모드는 항상 ach 계산'을 9회로 전제로 단언 |
| stage_b block_grid | r2r | 블록 (n_gn, n_gp)(22 MOS) `block_input_pattern_unsupported` -> 엔진이 `pi=0, axes=()` 기록, test는 `pi == prod(()) = 1` 기대. 타입 문서는 'pi = 격자 곱 Π(항상)' | **엔진 gain 모델 미지원 + 계약 모호**(모델 없는 블록의 Π를 0 감시값으로 씀 -- 정의 불능은 None이 맞다고 봄) |
| stage_b area | r2r | 엔진 면적 항 M21~M24 추가. 손 해석: n_abp는 M22 drain·gate + Ib5(7 µA) + 게이트만(M20·M28), M21–M22 직렬 diode -> 전류 = Ib5 단독; n_abn도 Ib2·M23–M24 같은 꼴 -> **엔진이 맞다**. test `_CURRENT_FED` 표에 r2r 칸 없음 | **test 결함**(9회로 손 해석 표) |
(rfc_ota: 단계 A review_needed exit 2, 단계 B 진단 표 통과 -- 실패 0.)

대안·권고:
- stage_a 3건: (가) `_supplies`를 sizing_spec `human.supplies_v.values`에서 읽고 기본값 삭제(정본 하나, 상수 발명 제거) -- **권고**, 기준 불변. (나) 4회로에 `_declared_target_spec` 추가 ⚠ 원칙 7(둘째 기록)·15(topology 파일 편집). 고친 뒤 cnr·r2r는 exit 2(정지)로 단언 범위 안에 들 것으로 예상(실측: spec 입력 시 cnr·r2r exit 2).
- erfc 5건: (가) spec을 바뀐 bulk 연결로 재확인(spec 항목이 bulk에 의존하지 않는지) 후 meta.topology_fp 갱신 -- **권고**. 이관된 library 회로라 held-out 동결(O-175 Ⅰ-3)은 해당 없음(O-181). 사용자 결정: 확인 보고 1건(지문 갱신 = spec 재확인 표지).
- cnr 4건·r2r block_grid 1건: 엔진 범위(규칙 분기 `dc_resistor_cycle`·`block_input_pattern_unsupported`·`loop_record_only` 등)는 M-LB1·단위 11 범위로 기록(Q-LB1 13 합격의 일). test 쪽은 (가) 진단 모드의 '단계 B 자기 정지 시 ach 없음'과 '모델 없는 블록 Π' 정의를 계약(pipeline CONTRACT 5절·metrics CONTRACT)에 먼저 적고 그에 맞춰 단언을 고침 -- 계약 개정은 design 경로(계획 → design → card), (나) 해당 회로를 xfail로 ⚠ 원칙 18·10(우회). **권고 (가)**, Π 감시값 0 -> None은 계약 결정(오케스트레이터 → 계획/design).
- r2r area 1건: (가) test 작성자가 4회로 손 해석으로 `_CURRENT_FED` 확장(r2r: M21·M22 pmos ← Ib5, M23·M24 nmos ← Ib2; 회로 해석이라 사용자 확인 대상) -- **권고**.

## 원칙 점검(★graph 단일 정본 포함)
- 새 cache·사본 권고 0. ③ (나)·stage_a (가)·a12b104f 개선안은 둘째 기록을 줄이는 방향.
- ⚠ 기준 변경이 필요한 것: ③ 규칙 E 정의(원칙 18) -- 사용자 승인. 나머지 권고는 기준 유지·상향.
- 원칙 15: 소자·넷 개명안((②나)(③라))은 비권고.
- 원래 취지와 다름: 없음(④ (나)를 고르면 Q-LB1과 다름 -- 비권고).

## 사용자 질문 초안
1. [규칙 E] library 13회로가 되며 엔진 어휘(LUT 축 'VS', 설계 질문 ID 'Q4·Q8·Q9', 옛 spec 키 'Z')가 회로 소자·넷 이름과 우연히 같아 규칙 E가 35건 실패합니다(회로 이름 의존 0건 실측). 어떻게 할까요? (가) 규칙 E 이름 집합에서 엔진이 한 곳에 선언한 어휘를 빼도록 정의 변경 (Recommended -- ⚠ 기준 정의 변경) (나) 엔진 리터럴 개명('VS'는 npz 키라 별칭 층 필요 ⚠ 둘째 이름) (다) (파일, 리터럴, 사유) 허용 쌍 등록 ⚠ 회로 늘 때마다 증가.
2. [erfc spec 지문] O-174 bulk 정정(6705b911)으로 erfc_ota connectivity_fp가 바뀌었는데 spec의 topology_fp가 그대로라 spec 로드가 거부됩니다. spec 내용을 바뀐 연결로 재확인하고 지문을 갱신해도 될까요? (Recommended)
3. [회로 해석 확인] r2r_opamp M21·M22(pmos)는 Ib5, M23·M24(nmos)는 Ib2만으로 전류가 정해진다(직렬 diode + 게이트만 연결)는 해석으로 면적 하한 oracle을 확장해도 될까요? 같은 방식으로 나머지 3회로 표(bias_inputs·소자 수)는 held-out 판독 결정 기록을 출처로 씁니다.
