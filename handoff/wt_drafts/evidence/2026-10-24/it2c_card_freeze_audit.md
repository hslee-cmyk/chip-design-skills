# IT-2c card 재동결본 동결 감사 (계획 N3.12.3 순서 3 상당) -- 2026-10-24

- 대상: card 브랜치 `card/it2c` `d95c8ff8`(부모 `395cc032` = `integ/it12` `34585913` 병합). card 파일 셋: `docs/02-design/specs/20261021-it2c-icm-config.spec.md`, `.interface.md`, `20261021-it2-common.md`.
- 기준: 계획 v6.37(O-124), design 41·40 v1.14.1(O-124), 사용자 결정 O-106~O-126(`wt/_drafts/user_decisions.md` 755~879행).
- 측정 자리: 격리 복제본 `wt/_scratch_it2c_audit3/iso`(`git clone --no-hardlinks --no-local wt/card-it2c`, origin 제거, HEAD `d95c8ff8`). 작성자 수치는 증거로 받지 않았다. 아래 수치는 모두 이 복제본에서 다시 잰 값이다.
- 측정 방법:
  - 줄 사실은 `sed -n`·`awk NR`·`grep -n`로 잼.
  - 서명·칸·`__all__`은 `python -E -P` import(`inspect.signature`, `dataclasses.fields`)로 잼. 스크립트는 `wt/_scratch_it2c_audit3/imp2.py`.
  - 실행 실측: `qd_probe.py`(단계 A → B → 커널 → 탐색 컨텍스트 → `layer0_start`)와 `stale_probe.py`(규칙 지문만 바꾼 단계 A). 로그는 `qd_probe.log`·`stale_probe.log`.
  - 엔진 코드는 고치지 않았다. `stale_probe`는 프로세스 안에서 `stage_a.structure_rule_fp` 이름 하나만 바꿨다.
- `.ai/verification` 판정 기록은 쓰지 않았다. 계획 N3.12(699~701행)가 DEC-86(285행)으로 폐기되었고, 지금 적용 규칙은 N6.3(1285행)이다. 판정 기록 형식을 요구하는 정본이 없으므로 이 파일만 남긴다.

## 1. 동결 판정

**수정 필요(동결 불가)**
- D-1은 계획 보강과 사용자 승인이 먼저 필요하다. 계획·design·card 모두 다루지 않은 동작 변경이기 때문이다.
- D-2~D-14는 card 문서만 고치면 된다.
- base와 엔진 트리는 맞다(아래 2절).

## 2. base 확인 (항목 1)

| 측정 | 결과 |
|---|---|
| `34585913` 존재·부모 | `3179cd78` + master `56dd1f8a`(design v1.14.1 병합) 병합 커밋 |
| `d95c8ff8` 부모 | `395cc032`(= `e2dfef9b` + `34585913` 병합) |
| 실제 저장소 `integ/it12` | `34585913`(앞선 커밋 0), master `56dd1f8a`는 base의 조상 |
| `git diff --stat 34585913 d95c8ff8` | docs 3파일(spec·interface·공통 문서)뿐, `skills/`·`tools/` 0 |
| `git diff --stat 09c3dce2 34585913 -- gmid_engine` | 0 |
| `git diff --stat 6afe4758 34585913 -- gmid_engine` | 0(card '무동작' 문단의 base 동일성 주장 확인) |

**판정**: base가 맞고 엔진 diff는 0이다.

## 3. 착수 실측표 S0~S14와 사실 문장 재측정 (항목 2)

### 3.1 `파일:줄`

엔진 줄 인용 약 150개를 다시 쟀다. 아래를 빼면 모두 card와 일치한다.
- s2_values: `:73`, `:114-119`, `:146`, `:150`, `:176`, `:177-183`, `:360`, `:395`
- block_columns: 40·57·64·117·137·145(사용 7곳 191·263·336·379·457·498·831)·150·163·197·202·227·235-237·239-245·247-268·270-278·280-287·470·584·652·656·676·685-692·695·704·727·783·790·799·800·803·805·809·810
- writer_plan: 25·49-50·76-77·122-144·266·269
- input_window: 30·33-34·58·67·69
- `_helpers_nodal.py`: 26·28-32·36-49·43·52·65·67·73
- records 214-218, stamp_mos 13·19, stamp_two_terminal 11·14
- 세 factor 자리(offset_analysis 69·offset_systematic 46·block_residual 73), `_helpers_view.py:23`, block_model 91·112, ff_gm_ratio 55
- s1v_fields 117-123·249·250(`def s1v_fields`)·295
- views 66·77·78·81·83-85, view_analysis 173·217, s1v_values 14·45·157·224·379, graph `__init__` 373·374
- sizing `__init__` 158·164·186, s1_values 143, seal_conduction 24·46, achievability 334·347
- ss_evaluate 101·104·107·109-110, ss_circuit 27·36·51, dc_edges 11, authoring `__init__` 108
- failure_errors 48, compute_block 160, immutability 32, s1v_build 36
- `_module_map` 505·596·641-642·773, metrics `__init__` 337
- sizing CONTRACT 16·204·205·1014·1023, metrics CONTRACT 125·1226, structure README 39·148, 레지스트리 732~735

차이:
- `metrics/ss_metrics.py:379-394`(card A와 design 739가 함께 인용): 조립 사본은 `:381-394`다(`:389` 주석 포함). `:379` `requests, *optional = projection.extras`와 `:380` `noise`는 조립이 아니라 `metrics_ss`가 계속 쓰는 줄이다. 그대로 지우면 블록이 깨진다(D-10).
- S3 경로: `tools/spice_oracle/legacy_testbench.json:9`는 저장소 루트에 없다. 실제 자리는 `skills/analog-gmid-design/tools/spice_oracle/legacy_testbench.json:9`이고, 값 `reltol 1e-4`·`vntol 1e-7`은 일치한다(D-11).

### 3.2 서명·칸·`__all__`(import 실측)

| 사실 | 재측정 | card |
|---|---|---|
| `saturation_window` | `(unknown, roots, values, gradient, rows, *, slope=None)` | 같음 |
| `conductance_matrix` | `(circuit, size)` | 같음 |
| `StampSet` 칸 | `g, c` | 같음 |
| `Window` 칸 | `lo, hi, constraints, input_status, tol_v` | 같음 |
| `SsCircuit` 칸 | `nodes, circuit, resistors, capacitors, ground_nets, input_nets, missing` | 같음 |
| `SS_WRITES` writer | `ss_dev, metrics_ss, metrics_dc, passive_values, metrics_aux`(5) | 같음 |
| `DC_WRITES` `dc_writer_plan` 행 | `dc_output_structure` 포함 | 같음 |
| `sizing.__all__` | 150 이름, 새 일곱 0, `CURRENT_SOURCE`·`METRICS_AUX_WRITER` 있음 | 같음 |
| `metrics.__all__` | 새 다섯 + `ss_circuit_field`·`is_dc_conducting_passive` 0, `StampSet`·`mos_stamps`·`two_terminal_stamps`·`ss_circuit` 있음 | 같음 |
| 새 모듈 셋(`ss_nodal`·`icm_config`·`_helpers_dc_solve`) | 모두 `ImportError` | 같음 |
| `ViewSeed` 칸 | `kind, excite, sense, source, cut` | 같음 |
| `ViewS1v.default_port` | 없음 | 같음 |
| `collect_views` ∈ `graph.__all__` | False | 같음 |
| `_Circuit` 메서드 | `writer_head`·`declared_inputs` 있음 | 같음 |
| `_Measured` 칸 | `window, slope, values` | 같음 |
| `metrics_ss`·`metrics_aux` READS | `graph.ss_circuit`·`graph.ss_nodal` 없음, `metrics_aux`에 `node.dc_window` 없음 | 같음 |
| `LOOP_CUT_KINDS` | `('resistor', 'capacitor')` | 같음 |
| `lut` 공개 | `vdsat`·`tol_vdsat_table`·`tol_v_table` | 같음 |
| `block_columns.k_max` | 있음 | 같음 |
| `require_immutable` | `(value)` | 같음 |
| `PORT_ROLE_DIFF_P/_N` | `differential_input_p/_n` | 같음 |
| `DC_CONDUCTING_PASSIVE_KINDS` | `('resistor',)`, `authoring.__all__` 안 | 같음 |
| `ss_evaluate`·`build_s1v` 서명 | interface 표와 같음 | 같음 |
| `DeviceOp` 칸 | `kind, current, ln_idu, gm_id, L, W, vgs, vds, vsb, w_key, idu_forward`(T-L8a 입력 다섯 모두 있음) | 같음 |

### 3.3 test 단언

- `tests/metrics/test_ss_types.py:93-120`: `dict(SS_WRITES)` 다섯 writer 정확 집합(`:102-104`), `len == 5`(`:105`), 소유 필드 7개(`:117-120`). card와 일치하고, 새 writer 셋·필드 넷이 생기면 red가 된다(8 writer·11 필드, interface 수치 맞음).
- `tests/sizing/test_block_columns.py:1476-1483` `_region_rows_scope`: `ENGINE/"sizing"/"block_columns.py"`를 AST로 읽고 `assert "region_rows" in defs`. card와 일치한다.
- 그 밖의 test 줄: test_s2_values 25·73·84·98·101·218·224·227-228, test_writer_plan 526·566·685(526~695 안 OS def 11개), test_input_window(`saturation_window(` 15건 = 호출 13줄 + 주석 :34 + test 이름 :263), test_ss_metrics 34-36·664-668, test_ss_evaluate 717-724, test_size_and_seal 44, test_ss_circuit 41, integration 421·469. 모두 일치한다.
- **card 목록에 빠진 기존 test 둘**:
  - `tests/metrics/test_ss_metrics.py:87-97` `test_block_declaration`이 `metrics_ss.reads`를 **정확 집합**으로 단언한다. IT-2c가 `graph.ss_circuit`을 READS에 더하면 red가 된다(D-4).
  - `tests/sizing/test_input_window.py:80-92` `test_it2b_sw_several_roots_move_together`(`:87` roots `("x", "w")`)는 묶음 갈래 사례다. card는 쌍 roots `:103`만 지운다고 적었다(D-5).

### 3.4 library 9회로 포트 수(topology `ports` 읽기)

| 회로 | 입력(role) | 출력(role) |
|---|---|---|
| common_gate_amplifier | 1 (single_ended_input) | 1 single |
| current_reuse_telescopic_ota | 2 (diff p/n) | 2 (differential_output_p/n) |
| folded_cascode | 2 diff | 1 single |
| ngcc_3stage_ff | 2 diff | 1 single |
| nmcnr_amplifier | 2 diff | 1 single |
| pushpull_follower_buffer | 1 single | 1 single |
| sf_pushpull_output_opamp | 2 diff | 1 single |
| two_stage_ota | 2 diff | 1 single |
| two_stage_ota_sf | 2 diff | 1 single |

2입력 차동쌍 7, 1입력 2, 단일 출력 8, 차동 출력 1, 입력 셋 이상 0이다. card S4와 일치한다.

### 3.5 S0~S14 행별

| # | card 상태 | 재측정 |
|---|---|---|
| S0 | 엔진 diff 0 | 일치(2절) |
| S1 (a) | "gain view `{pending: MOD5}` → 실행 전 정지 갈래·layer0 봉인점 없음 → 잴 수 없을 가능성" | **사유가 사실과 다르다.** `current_reuse`는 단계 A `ok`(exit 0), 단계 B `ok`(exit 0)다. `layer0_start` 결과는 `start is None`이고 stop은 `start_no_root_in_window+probe_eval_budget`, 17.9 s다. 실행 전 정지는 없고, 봉인점이 없는 원인은 층 0 시작점 부재다(B81, O-125 근거와 같음). `{"pending": "MOD5"}`는 `:155`가 맞다. **결론(미측정)은 같다**(D-2) |
| S2 (b) | a_e 기준 착수 때 | 대상 아님(착수 실측) |
| S3 (c) | reltol 1e-4·vntol 1e-7 | 값 일치, 경로 접두 틀림(D-11) |
| S4 (d) | 9회로 정적 | 일치. 다만 S1v 소비자 값 변화 0 기대는 D-1 때문에 nmcnr·current_reuse에서 깨진다 |
| S5 (e) | 미측정, Q-D | S1과 같은 회로·같은 사유로 잴 수 없다(봉인점 없음) |
| S6 C-2 | 미측정 | 정적 근거를 확보했다. library spec에 명시 view 선언은 `current_reuse` 4건뿐이고 모두 `{"pending": "MOD5"}`(`:154·188·202·281`)다. 나머지는 로더 기본 port 뷰라 `view_system`(`_helpers_view.py:16-23`)의 구동 쌍이 입력 포트다. 따라서 정적으로 구동 쌍 ⊆ 입력 넷이다. 실행 확인은 착수 때 한다 |
| S7 | sf_pushpull 미측정(착수 때 재측정) | **층 0 시작점 없음**: 단계 A·B ok, `start is None`, stop `start_lut_query_failed+probe_eval_budget`, 2.6 s. 착수 때 재측정해도 잴 수 없을 가능성이 높으므로 S1·S5와 같은 O-72 (1) 처리가 필요하다(D-3) |
| S8·S9 | 미측정 | 대상 아님 |
| S10 | `nmcnr_amplifier.sizing_spec.json:117-126` 옛 문구 | 일치(`:122` record = 옛 문구) |
| S11 | 고정값 단언 미확인 | **닫을 수 있다.** 지문 문자열 `adc91fc8…`(structure)·`56683d7d…`(s1v)를 `git grep`하면 library `structure.json` 2파일뿐이고 tests에는 0이다. `s1v_rule_fp` 참조 test 파일은 **5개**(graph 3 + integration `test_stage_a_library` + pipeline `test_stage_a`)다. card는 '다섯'이라 적고 `test_stage_a_report.py`까지 6개를 나열했다. 그 파일에는 참조가 0이다(D-8) |
| S12~S14 | 미확인(test 주체) | 대상 아님 |

### 3.6 새 이름 충돌(엔진 비test `.py`)

- 0건: card가 0건이라 한 이름 전부. 다만 `g_bound`는 부분 문자열로 9건이다(`matching_bounds`·`crossing_bound_violated`). 식별자 단어 경계로는 0이므로 문자열 grep 판정에는 단어 경계가 필요하다.
- `"conduction"`은 **3곳**이다: `s2_values.py:73`, `:82`(`SEAL_ITEM_NAMES.index("conduction")`), `cell_floor.py:54`. card는 2곳으로 적었다(D-9).
- `_helpers_dc_solve` 1(`input_window.py:8`), `default_port` 1(`VIEW_SOURCE_DEFAULT`): card와 일치한다.
- test 함수 이름 수: it2c 0, servo 0, default_port 0, vcm 0, ss_nodal 0, icm_config 0, kvl_sensitivity 0, g_ops 0, pivot 1, conduction 2, g_bound 1, ss_circuit 1, circuit 67, bound 86, view 137. card와 모두 일치한다.

## 4. card ↔ 계획·design 대조 (항목 3 -- 변화 목록 1~11)

| # | card 변화 | 계획 v6.37 | design v1.14.1 | 판정 |
|---|---|---|---|---|
| 1 | 측정 구성 = servo 하나, 선언 되먹임·반전 입력·S-OS2·`tied_ports`·`transfer` 삭제 | 609 'ICMR 측정 구성'·'선언 되먹임', 1545 (vii) | 41:729·734·738·744, 726 | 일치 |
| 2 | `IcmConfig` 칸 일곱 | 609 'V_cm의 정본 자리', 1545 (vii) | 41:732 | 일치 |
| 3 | `kvl_sensitivity(nodal, drive, servo=None)` | 609 'ICMR servo 감도 -- KCL' | 41:734 (3) | 일치 |
| 4 | 정의 불능 code 넷 | 609 정의 불능 셋 + 'e ∥ CM 대상 없음'(gap N-1) | 41:734 (1)·744 | 일치 |
| 5 | 전도 행 R0·일반 1차 행 | 609 '측정 구성 창 행 = 포화 행 + 전도 행 (R0)' | 41:705 1·716 6 | 일치(k 식 동치는 41:716이 보임) |
| 6 | F 성분 포트 함께 구동, `writer_head`·상수 삭제 | O-118 3번, 1545 (vii) | 41:697·734 (4)(ii)·744·760 | 일치 |
| 7 | S1v `default_port` | 609 'ICMR 전달 뷰 = 기본 포트 뷰'·'S1v 지문 영향' | 41:731·834 | 일치. **단 세 문서 모두 `structure.json` `rule_hash` stale 결과를 빠뜨림(D-1)** |
| 8 | 절단 넷 함수 → TN-1 | 2071 N6.26, 1545 (vii) | 41:738·744·812 | 일치 |
| 9 | `sizing.__all__` 일곱 | 2249 U-101 | 41:760 | 일치 |
| 10 | test L-항목 | 1541 (7)(8)(10)(12) | 41:800~814 | 일치. L8 (g)의 `metrics_aux` READS·`_icm_ports` AST와 L12 (a)(c)의 metric·front 부분은 IT-2d 함수라 interface에서 빠졌는데, spec F는 'L8 (a)~(h)'로 통째 배정했다(D-14) |
| 11 | 착수 실측표 | 1537 (a)~(e)·'차동 출력 servo 착수 실측' | 41:735·834 | 항목은 일치. S1·S5·S7 사유·전망이 실측과 다르다(D-2·D-3) |

그 밖 확인:
- design 41:730의 `SS_WRITES` 인용 `:173-179`는 낡았다(실제 `:177-183`). card는 맞는 줄을 썼다. design 정정 대상이지 card 결함은 아니다.
- 공통 문서 30행 '계획 663행'·'1237행'과 41행 '669행'은 낡았다(N3.12 = 699, N6.3 = 1285)(D-13).

## 5. interface card만으로 test를 쓸 수 있는가 (항목 4)

대체로 쓸 수 있다. 다음은 갖춰져 있다.
- 입력: 블록 호출 꼴, extras 둘, 엔진 입력 필드, LUT 원시 함수.
- 출력: `Window`·`IcmConfig`·`NodalSystem`·`Undefined` 꼴. `Undefined` 칸 `quantity, code, category, detail`은 import로 확인했다.
- 정의 불능 code 넷과 '없는 것' 목록, fail-closed 갈래 순서, writer·READS 표, 부르는 순서.

빠진 것:
- **레일 값의 출처**: span, 그리고 레일 자름의 `rail_min`·`rail_max`가 `node.dc_rail_v`의 최대 − 최소라는 정의(41:735)가 interface에 없다(D-6).
- **부호 규약**: 행의 '부호'·σ와 `Circuit.kind_sign`이 어느 kind에서 +1인지(nmos +1·pmos −1)가 없다. 손 조립 행 계수에 필요하다(D-6).
- **import 규칙의 예외**: interface는 '공개 이름만 import'라 하면서 `gmid_engine.metrics._helpers_nodal.conductance_matrix`를 대상으로 적었다. 선례 `tests/metrics/test__helpers_nodal.py:14`가 있으니 예외를 명시해야 한다(D-7).

## 6. 원칙 전 범위 (항목 5)

| 원칙 | card 계약 | 판정 |
|---|---|---|
| graph 단일 정본 | G1~G7, 근본원칙 계약 1항 | 들어 있음. G3 cfg `tol_v` '같은 정의'에 축(평가 점 = 봉인점 대 커널 해, 41:688)을 적어야 한다(D-12). **graph 밖 지문 소비자(`structure.json` `rule_hash`)의 영향이 빠짐**(D-1) |
| 계획 우선 | 있음, Q-A·Q-B를 결정하지 않고 올림 | 들어 있음 |
| fail-closed | 있음(code·`unmeasured`·`Undefined`) | 들어 있음 |
| 상수 발명 금지 | u = 2⁻⁵³ 하나, 문턱은 기존 정본 | 들어 있음 |
| 회로 이름 금지 | EP-1, 포트 role 맞바꿈 불변 | 들어 있음 |
| DC/AC | 용량 개방, 용량만 결측이면 노달 계 성립 | 들어 있음 |
| DEC-103 | KCL 섭동 대 θ 설계점, θ 감도 호출 0 | 들어 있음 |
| 만들면 배선 | G6, 만들지 않을 칸 목록 | 들어 있음 |
| heldout 금지 | library toy·이름 없는 toy만 | 들어 있음. C-12의 '13회로 = 2입력 11·1입력 2'는 근거가 아니라 개수 사실 |

## 7. 결함 목록

| id | 심각도 | 내용 | 재현·근거 | 수정안 |
|---|---|---|---|---|
| **D-1** | **높음** | IT-2c는 `graph/views.py`·`s1v_values.py`·`s1v_fields.py`·`view_analysis.py`를 고친다(41:834, card C′). 넷 다 `S1V_RULE_FILES`(`s1v_values.py:14-19`) 안에 있어 `structure_rule_fp`가 바뀐다. library `nmcnr_amplifier.structure.json`(`l_owner` ratified)과 `current_reuse_telescopic_ota.structure.json`(`ac_ground_exception` ratified)의 `rule_hash`(`adc91fc8…`, 현재 값과 같음)가 stale이 된다. 그러면 `structure_load.py:148-152`가 사실을 버리고 `structure_fact_stale`을 낸다. 실측(규칙 지문만 바꿈): nmcnr 단계 A `review_needed` exit 2, current_reuse 단계 A `stopped` exit 2(바꾸기 전에는 둘 다 `ok` exit 0). 두 회로가 단계 B·탐색 전에 멈추고, integration 기준선 test도 red가 된다(`u17_1b_s0_baseline.json`이 두 회로를 `["ok", "ok"]`로 적고 있어, `test_layer0_boundary_rows.py`의 `assert (a.status, b.status) == ("ok", "ok")` 등이 깨진다 -- 실행 확인은 안 함, 코드 읽기). 계획 1537·609('S1v 소비자 값 변화 0'), design 41:731·817, card S4·'무동작'·변화표 원인 칸 어디에도 이 결과가 없다. 선례: 계획 1414 F-IT7(IT-1은 rule 파일을 건드리지 않아 재기록 불요), 1707 (2)·1584 4 '`rule_hash` 재기록 근거 기록' | `wt/_scratch_it2c_audit3/stale_probe.py`, `stale_probe.log` | (1) 오케스트레이터가 계획 N6.6 IT-2c 완료 조건에 'library `structure.json` 2파일 `rule_hash` 재기록과 근거(값 비교) -- 사실 재비준'을 더한다(계획 우선, 원래 취지와 다름 여부 판단 포함). (2) 사실 재비준(ratified 유지)은 사용자 승인 대상이다. stale 전이는 검토를 강제하려는 장치이기 때문이다. (3) 그 뒤 card에 사실 행 S16, 변화표 원인 칸, data 커밋 시점(code 커밋과 같은 통합 병합 안), 멈춤 조건(재기록 없이 착수 금지)을 더한다 |
| D-2 | 중간 | S1·S5(와 계획 1537)의 '실행 전 정지 갈래' 사유가 실측과 다르다. 단계 A·B는 ok이고 층 0 시작점이 없다 | `qd_probe.log` | S1·S5와 Q-D 사유를 '층 0 시작점 없음(`start_no_root_in_window+probe_eval_budget`, B81) → 봉인점 없음'으로 고친다. 계획 1537 문언은 오케스트레이터 후속 정정 목록에 넣는다 |
| D-3 | 중간 | S7 `sf_pushpull` 층 0 시작점 없음(`start_lut_query_failed+probe_eval_budget`). '착수 때 재측정'으로도 잴 수 없을 가능성이 높다 | `qd_probe.log` | S7·41:817 (5) 행에 O-72 (1) '미측정 + 사유, 사용자 보고 뒤 착수'를 적고 C-11 목록에 더한다 |
| D-4 | 중간 | `test_ss_metrics.py:87-97`의 `metrics_ss.reads` 정확 집합 단언이 test 작성 주체 목록에 없다. 조립을 지운 뒤 `metrics_ss`·`metrics_aux`가 더는 쓰지 않는 조립 열(`element_class`·`pins`·`bulk`·`ac_ground_class`·`port_direction`·`passive_value`·`node.dc_colour`)을 READS에서 뺄지가 정해지지 않았다. design 739는 `ss_values`·`device_orbit`만 '자기 READS로 읽는다'고 했다. code 주체의 as-built 결정이 될 위험이 있다 | 3.3 | card A에 READS 처리 규칙(뺌 또는 남김)과 근거를 적는다(design에 없으면 design 정정 대상으로 올린다). test 목록에 `:87-97`을 더한다 |
| D-5 | 낮음~중간 | `test_input_window.py:80-92` 묶음 갈래 사례가 지울 목록에 없다 | 3.3 | spec 'test 작성 주체 몫'과 interface '고칠 기존 test'에 `:80`(`:87`·`:91`)을 더한다 |
| D-6 | 낮음 | interface에 레일 값 출처(`node.dc_rail_v` 최대 − 최소)와 부호 규약(`kind_sign`: nmos +1·pmos −1)이 없다 | 5절 | interface '측정 구성 규칙'과 '`Circuit` 계약'에 한 줄씩 더한다 |
| D-7 | 낮음 | '공개 이름만 import'와 `_helpers_nodal` 대상이 충돌한다 | `test__helpers_nodal.py:14` 선례 | 예외 문장을 명시한다(규칙 H 1:1 test는 그 모듈 이름 직접 import) |
| D-8 | 낮음 | `s1v_rule_fp` 참조 파일을 '다섯'이라 하고 6개를 나열했다(`test_stage_a_report.py` 참조 0). 고정값 단언 '미확인'은 실측으로 0이다 | 3.5 S11 | 목록을 5로 고치고 S11 '고정값 단언 0(지문 문자열 tests grep 0)'으로 닫는다 |
| D-9 | 낮음 | `"conduction"` 엔진 비test 3곳(card 2), `g_bound` 부분 문자열 9 | 3.6 | 사실 문장을 고친다(단어 경계 명시) |
| D-10 | 낮음 | `ss_metrics.py:379-394` 범위에 조립 아닌 `:379-380`이 든다(design 739도 같음) | 3.1 | card A를 `:381-394`로 고치고, design 정정 목록에 넣는다 |
| D-11 | 낮음 | S3 경로 접두 | 3.1 | `skills/analog-gmid-design/tools/spice_oracle/legacy_testbench.json:9` |
| D-12 | 낮음 | G3 cfg `tol_v` '같은 정의'에 다른 축(평가 점)을 적지 않았다(CLAUDE.md graph 규칙 3) | 41:688 '축' | '같은 정의, 평가 점만 봉인점(커널은 마지막 해)'으로 고친다 |
| D-13 | 낮음 | 공통 문서 줄 인용 낡음(30행 '663행'·'1237행', 41행 '669행'). 213행 '작성 전 실측 1'은 '재측정'이라 적었지만 내용이 `468e6e73` 기록이다(`input_window.py:48 root` 등 현재와 다름) | 4절 | 줄 고침, '기록' 표지 |
| D-14 | 낮음 | spec F 'L8 (a)~(h)' 배정에 IT-2d 부분(L8 (g) `metrics_aux` READS·`icm_window_metrics`/`_icm_ports` AST, L12 (a)(c) metric·front)이 섞여 있다 | 41:811 (g)·814 | F에 'IT-2d 부분 제외'를 명시한다 |

## 8. 작성자 확인 항목 Q-A~Q-D 판정 (항목 6)

- **Q-A(41:817 U-104 문언)**: card의 식별이 맞다. 41:817은 '다른 양'이고, 계획 2252 (3)·O-119 정정 1·2는 '사용자 지정 ICMR 최소 요구, servo ICMR과 같은 양'이다.
  - 이미 `design/v1142` 셋째 커밋 `f4359e17`('IT-2c 재동결 정오 Q-A·Q-C')에서 고쳐졌다. 재검증 `evidence/2026-10-24/design_v1142_recheck.md` 45~49행에 따르면 계획 문구와 글자 그대로 같다. 미병합·검증 대기 상태다.
  - card는 변화표 문언을 단언하지 않으므로 **동결 차단 아님**.
  - 주의: v1.14.2가 IT-2c code보다 먼저 병합되면 card의 `41:n` 인용 줄을 다시 재야 한다.
- **Q-B(U-104 data 커밋 시점)**: 계획 안에 문언이 셋 있다. 2252 (3) '착수 전 data 커밋', 2252 시점 칸 '변화표 작성 전', 1545 끝 'U-104는 IT-2c 변화표 작성 전'.
  - `source.record`는 지문에 들지 않으므로(2252 (1) '지문은 `kind`만') 엔진 영향은 0이다. 실질 요구는 '변화표 작성 전'이다.
  - **권고: 두 문언을 모두 만족하는 'IT-2c code 착수 전'에 (5) 사용자 승인 → data 커밋.** 계획 문언 통일은 오케스트레이터 후속 정정이다.
  - **동결 차단 아님**. card가 S10·Q-B로 올린 처리는 맞다.
- **Q-C(40:1881 `vds_vsb`)**: card의 식별이 맞다. 40:1881 메서드 목록에 `vds_vsb`가 없고 41:760에는 있다. card는 4.7 정본을 따랐다. `design/v1142` `f4359e17`에서 고쳐졌다(그 판 40 문서 `vds_vsb` 3건). 동작 영향 0, **동결 차단 아님**.
- **Q-D(착수 실측 (a)(e))**: **실제로 쟀고 잴 수 없다 → '미측정 + 사유'로 판정한다(O-72 (1)).**
  - 사유: `current_reuse_telescopic_ota`는 단계 A ok·B ok이지만 층 0 시작점이 없어(`start is None`, stop `start_no_root_in_window+probe_eval_budget`) 봉인점이 없다. (a) a_e·δA_num과 (e) 차동 출력 servo 연립 특이·|a_e|를 잴 점이 없다.
  - O-72 (1)이 금지하므로 다른 회로·다른 점으로 대체 측정하지 않았다.
  - library 차동 출력 회로는 이것 하나다(3.4). 따라서 차동 출력 servo의 엔진 근거는 L8 (b) toy뿐이다.
  - 사용자 보고 기록은 아직 없다(`user_decisions.md` grep '착수 실측'·'current_reuse' -- O-72 뒤 0건). **IT-2c code 착수 전에 사용자 보고가 필요하다**(41:834, O-72 (1)).
  - card 사유 문장은 D-2대로 고친다.

## 9. 사람(사용자) 결정이 필요한 항목

1. **D-1**: library 2회로 `structure.json` 사실 재비준과 `rule_hash` 재기록(IT-2c 같은 통합 병합). 먼저 계획 보강이 필요하다.
2. **Q-D·D-3**: (a)(e)와 S7 '미측정 + 사유' 보고(O-72 (1)). 이 보고 뒤에 IT-2c code를 착수한다.
3. **Q-B**: U-104 spec 문구 data 커밋 승인(U-104 (5)).

## 10. 가드 확인

- 격리 복제본: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_it2c_audit3/iso`(origin 제거). 실행 산출물은 `_scratch_it2c_audit3/{qd_work,stale_work,pyc}`에만 있다.
- 실제 저장소와 `wt/card-it2c`의 reflog·status를 시작 전·후로 대조했다(최종 보고에 결과).
