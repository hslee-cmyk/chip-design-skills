# oracle-portability OP-2 (오라클 기술자 + 입력 형식 변경) spec card (card id `op2`)

- 작성: 2026-10-16. 읽기 전용 실측과 card 초안만 담았다. 오라클·엔진·test·git 브랜치는 고치지 않았다.
- **card base = `5fea301`**(master, OP-0 design v0.2.6 병합, 사용자 O-12 승인). `git diff --stat HEAD -- skills/`는 `.bkit/runtime` 파일 6개뿐이라(엔진·오라클·assets 0줄) 아래 작업 트리 실측 = `5fea301`.
- 실측 방법: `git grep`/`git show HEAD:`/`sed -n`로 읽기만 했다(실행 없음, 단 `sha256sum`·`git ls-files --eol`·PDK 폴더 `git log -1`은 읽기). 호출부 수는 줄 단위 grep 결과 수다.
- design 근거(줄 = `5fea301`의 `docs/02-design/features/oracle-portability.design.md` v0.2.6): §20 OP-2 행(1312행), §10.1(558~564행), §10.2(566~612행), §10.3(614~625행), §7 오류 코드 표 가운데 OP-2 몫(378~382·386·387행), §7.2 1·2·8단계(435·436·442행)와 그 아래 문단(445~446행), §11.1~§11.5(703~811행), §15.1 OP-2 행(1038·1040행), §15.4 conftest 옛 형식 생성기 행(1064행), §18.1 'X-13'·'기록 뿌리 해석(OP-2)'·'8a 엔진 무변경' 행(1166·1167·1169행), §18.2 `test_oracle_input_schema.py`·`test_legacy_adapter.py`·conftest 생성기 행(1183·1184·1187행), §19.3 R6 행(1283·1288·1289행), §19.4 X-D4·X-D5(1299·1301행).
- 계획 근거: `docs/01-plan/features/oracle-portability.plan.md` v0.6.6 N5.1 OP-2 행(381행), N3.4(189~212행), N3.6 삭제 목록(293행), N5.3 완료 조건 1·6·7·8a(399~422행), N7 G-5(460행), X-13(493행), D-5(446행), D-9(450행), N8 R6(528행).
- 사용자 결정 원문: `wt/_drafts/user_decisions.md` O-1~O-12, L-1·L-2·L-3, T-31·T-33, S-7, P-1.
- 경로 접두: `O/` = `skills/analog-gmid-design/tools/spice_oracle/`, `E/` = `skills/analog-gmid-design/gmid_engine/`, `A/` = `skills/analog-gmid-design/assets/`.

> **멈춤(2026-10-16)**: 아래 1.8의 `[J-1]`~`[J-15]`는 design v0.2.6이 정하지 않았거나(as-built 결정 금지) design·계획·구조 규칙과 어긋나는 곳이다. S-7("계획과 다른 부분이 생기면 계획부터 수정")대로 **이 card가 정하지 않았다.** J가 닫히기 전(design 개정 → 독립 검증 → 사용자 승인, 계획 개정이 필요한 J-7은 계획부터) code·test 착수 금지. J가 닫히면 이 card의 `[J-n]` 칸만 채워 다시 낸다.

---

## 1. spec card

### 1.1 목표 (사용자 의도 원문)

- T-31(2026-10-16): "공정 무관 방법론 … 어떤 PDK·시뮬레이터 모델이든 … PDK 기술자 선언 + 확인 test, 회로·PDK 이름을 규칙에 넣지 않는다. sky130은 첫 적용 사례일 뿐."
- T-33: "현재 구현되어 있는 spice 오라클도 simulator 무관한 것이어야 해."
- O-1 D-5 "새 입력 형식, 옛 형식 거부", D-9 "별도 오라클 기술자, 엔진 무변경". O-3 DV-1 (가) "extra_sources에 엔진 선언에 없는 파일만, 같은 파일 두 곳 금지". O-6 D-b "기술자에 geometry_unit·m 전달 규칙(mult) 선언". O-11 X-D5 "pdk_root 해석 규칙 오라클 재구현 사본 유지 … pdk_root 없을 때 오라클 거부".
- 목표 한 줄: **PDK 데이터(모델 호출 형식·포함 파일·코너·온도·확산·기하 단위·병렬 배수·LUT 기록 뿌리)를 오라클 입력에서 빼서 엔진 선언을 sha256으로 참조하는 오라클 전용 기술자 파일 하나로 옮기고, 오라클 입력은 기술자 참조 + 조건 + `simulator` 블록만 갖게 하며, 옛 형식은 거부한다. 엔진 파일은 바꾸지 않는다.**

### 1.2 구현하는 design 절

| design 절 | 내용 | 이 card |
|---|---|---|
| §10.1 | 기술자 위치 `O/descriptors/<pdk>.oracle_descriptor.json`, 스키마 이름 `oracle_pdk_descriptor/1`, `engine_decl = {path, sha256}`, 엔진 `sources`는 source 키로만, `extra_sources = {key: {path, sha256, base, provenance}}`(엔진 선언에 없는 파일만), 중복 거부 | 구현 |
| §10.2 | 스키마 전부 **가운데 `mc`·`diagnostic` 칸 제외**(§20 1312행, §10.2 602행): `engine_decl`, `extra_sources`, `lut_record_root`(위치 선언 참조 + 키 `pdk_root`, 해석 규칙 = `E/lut/CONTRACT.md` 1.8 256~261행, 엔진 import 없이 새로 씀), `lut_file_roles`(OP-2는 `[]`), `model_family`, `kinds.<kind>.{call_form, name, inner_device, geometry_unit, parallel_multiplier, includes, polarity}`, `corners`, `temperature`, `diffusion` | 구현 |
| §10.3 | sky130 사례 값(OP-2 칸: `geometry_unit`, `parallel_multiplier`, `extra_sources`, `lut_record_root`, 그 밖 비-MC 칸). **값은 사용자 확인**(614~616행) | 기술자 파일 + 사용자 확인 |
| §7 (OP-2 몫) | `oracle_input_format_old`, `oracle_condition_missing`, `descriptor_source_duplicated`, `descriptor_schema_invalid`, `pdk_descriptor_stale`(`ref` ∈ `engine_decl`·`engine_source:<key>`·`extra_source:<key>`·`lut_location_decl`, `lut_file_roles[<i>]`은 OP-3), `lut_location_decl_invalid`, (`lut_record_root_mismatch` = `[J-5]`) | 구현 |
| §7.2 (OP-2 몫) | 1단계 가운데 입력 형식·조건(어댑터 선택·지문은 OP-3), 2단계 전부(스키마 → 참조 sha256 → 원본 중복 → 참조 파일 형식, sha256 대조는 이 단계 한 곳 -- 445행), 8단계 첫머리 기록 뿌리 교차 검사는 `[J-5]` | 구현 |
| §11.1~§11.3 | 새 `process`(`descriptor{path, sha256}`, `lut_npz`, 선택 `corner`·`temp_c`), `simulator{adapter, exe, options}`, `output_reference`(`[J-8]`), 삭제 칸, `process` 닫힌 키 집합(B-12), 온도·코너 해석 순서, 옛 형식 거부(이중 지원 없음) | 구현 |
| §11.4 | 생산자 수정 없음(저장소 안 생산자 0, `legacy_adapter`는 LT-1 순서 3) | 범위 확인 |
| §11.5 | 입력 변환 필드 대응표 = **검증자 변환 스크립트의 근거**(오라클 코드 아님). 결과 칸 이름 대응 행은 OP-3·OP-4·OP-5 몫 | 범위 확인(코드 없음) |
| §15.1 1038·1040행 | 스키마 `process.models`·`process.ngspice_exe`·`process.diffusion`·`testbench.options` 삭제, CLI `--ngspice`의 '입력' 쪽(`[J-9]`) | 구현 |
| §15.4 1064행 | `O/tests/conftest.py` 옛 형식 생성기 다섯을 새 형식으로(이름·인자 유지, 호출 183곳 무변경) -- **test 주체** | test 주체 |
| §18.1 1167·1169행 | X-13 test(위치 `[J-6]`), 기록 뿌리 해석 test | test 주체 |
| §18.2 1183·1184·1187행 | `test_oracle_input_schema.py` 다시 씀, smoke 고정 자료 '스키마 적합' → '옛 형식이라 거부' | test 주체 |
| §19.3 R6 행, §8.3 504행 | **병합 조건**: ngspice 매뉴얼 원문 보관 + 기본 허용오차 쪽 번호 + abstol 값·쪽(S-28) + 시간 걸음 실패 문장 형태(1289행) -- `[J-14]` | 병합 조건 |

#### 범위 밖(다른 card 몫 -- 넣지 않는다)

| 항목 | card |
|---|---|
| 코어 IR·요청·결과(`core/ir.py`·`requests.py`·`results.py`·`adapter_api.py` 등 §3·§4·§5·§6), ngspice 어댑터, stub 어댑터, 어댑터 지문(`adapter_fingerprint_unavailable`), 실행 캐시 키 §9 | OP-3 |
| 기하 미선언 거부 `descriptor_geometry_undeclared`(§7.2 3단계, §10.6) -- OP-2는 칸을 **선언**만 하고 거부·소자 줄 반영은 하지 않는다 | OP-3(병합 조건 (a)) |
| 모델 묶음 자동 대조 §12.5(§7.2 8단계 `lut_model_provenance_missing`·`model_bundle_mismatch`·`lut_aux_input_mismatch`), `lut_file_roles` 옆 선언과 `lut_file_roles_invalid`, `make_lut`의 `model_files_sha256` | OP-3 |
| 결과 칸 `ngspice_rc`→`status`, `method`, `ngspice_runs`→`sim_runs`(§11.5 결과 칸 대응) | OP-3·OP-4·OP-5 |
| smoke '넷리스트·루프 넷리스트 재생성 일치' test 삭제 + `criteria_weakened` | OP-3(계획) -- 단 `[J-7]` |
| `u6_selfchecks.py` 삭제(O-10), `cm_loop_*` import 변경, `test_verified_by.py:64` glob(8a 예외 둘째), `run_spice`·`independent_*` 이동 | OP-3 |
| `calibration.json`(`default_tolerances`·`data_digits`·`wall_s_per_window`), `_NGSPICE_DEFAULT_TOL` 이동 | OP-4 |
| 기술자 `mc`·`diagnostic` 칸과 그 오류(`mc_*`), 손 모델 픽스처, 4a | OP-5 |
| 능력 기록·온도 게이트(§12.6) | OP-6 |
| `legacy_adapter.py`·`legacy_testbench.json`·`test_legacy_testbench.py`·conftest `--run-legacy`·`legacy_slow` 삭제 | gain-budget LT-1 순서 3 |
| 엔진 쪽 낡은 오라클 파일 인용(S-36) | gain-budget 소유 card(알림만) |

### 1.3 실측 사실 (5fea301, 쓰는 자리에서 다시 잼)

| # | 사실 | 근거 |
|---|---|---|
| F-1 | 오라클 최상위 `oracle_*.py` 7개 합계 4597줄(`legacy_adapter.py` 제외). test 27개(`test_*.py`) + `u6_toy5t.py` + `conftest.py`, `__init__.py` 없음. `pyproject.toml` `testpaths = ["gmid_engine/tests"]` -- 오라클 test는 경로를 주고 따로 돈다 | `git ls-tree`, `wc -l`, `A/../pyproject.toml` |
| F-2 | 입력 검증 진입: `oracle_netlist.validate_input`(`O/oracle_netlist.py:224-231`, jsonschema Draft 2020-12, 위반 문자열 목록). 거부하는 진입점 셋: `oracle_netlist.py:1315-1317`, `oracle_run.py:80-84`, `oracle_compare.py:785-790`(반환 2, 산출물 없음 = README C13) | 위 파일:줄 |
| F-3 | 스키마 `O/oracle_input.schema.json`: 최상위 `schema` const `spice_oracle_input/1`(`$id`도 같음), 최상위 `additionalProperties` 없음. `process` 필수 `lut_npz, models`, `process.additionalProperties` 없음, `models[kind]` 필수 `subckt, includes, op_probe`(+선택 `polarity`), `process.diffusion` 필수 `ad_per_w_m, pd_extra_m`, `testbench.options`(171행, 값 문자열) | 스키마 7·11·162·171행 |
| F-4 | **옛 형식 칸을 읽는 오라클 코드 13곳**(OP-2가 입력 형식을 바꾸면 모두 깨진다): `oracle_netlist.py:116`(`_includes`, `{corner}` 치환 `:117`), `:126`(`probe_name` = `op_probe` 틀), `:136`(`diffusion_of` = `process.diffusion`), `:146`(`device_line` = `subckt`), `:298-318`(본 넷리스트 머리: LUT meta corner·temp_c, `tb["options"]` → `.option`), `:554`(meta `tb_options`), `:985-1008`(iso 넷리스트: includes·options·`polarity`), `:1113`(`parse_netlist_elements` subckt → kind), `oracle_noise.py:130`·`:272`, `oracle_swing.py:206`(`reltol_of(tb.get("options"))`), `oracle_offset_mc.py:72`·`:148`(`models[kind].subckt`), `oracle_run.py:86-88`(`process.ngspice_exe` 대체값). `oracle_simulate.py`는 입력이 아니라 넷리스트 meta `tb_options`를 읽는다(`:1037, :1124, :1143-1144`) | `git grep` |
| F-5 | CLI `--ngspice`: `oracle_simulate.py:1395`(필수), `oracle_noise.py:342`, `oracle_offset_mc.py:202`, `oracle_swing.py:315`(필수), `oracle_run.py:70`(선택, 없으면 `process.ngspice_exe`). test 쪽: `conftest.py:280`·`:300`, `test_oracle_c10_stability.py:972` | 위 파일:줄 |
| F-6 | conftest 옛 형식 생성기: `process_block`(`:71-90`, `models[kind].{subckt, includes, op_probe}` + `diffusion={ad_per_w_m: 5e-7, pd_extra_m: 2e-6}`, pmos includes 첫 줄 `models/parameters/lod.spice`), `testbench_block`(`:105-109`, `options = {gmin 1e-15, reltol 1e-4, abstol 1e-14, vntol 1e-7}`), `cs_input`(`:118-`), `rc_input`(`:166-`), `fb_input`(`:195-`, `:201` `process_block(lut, diffusion=False)`). 다섯 이름을 쓰는 곳 = conftest 밖 **183줄·28파일**(`O/tests`, `O/smoke`; 이름별 process_block 12, testbench_block 20, cs_input 113, rc_input 14, fb_input 34 -- 줄이 겹쳐 합 193). `make_lut`(`:60-68`, meta `corner`·`temp_c`만)는 160줄 | `git grep -w` |
| F-7 | **생성기 밖에서 옛 칸을 직접 고치는 test 19줄·9파일**(design §15.4 '호출 183곳 무변경'에 들지 않음): `test_oracle_conduction.py:216`(pmos `op_probe`를 없는 내부 소자로), `:285-286`(polarity), `test_oracle_iso.py:22`, `test_oracle_junction_cap.py:94-95, :139-140`(polarity), `:203`(`process.diffusion` 값 교체), `test_oracle_netlist.py:72`(`subckt` 대조), `:81`(`process.diffusion` 값으로 기대값 계산), `test_oracle_netlist_topology.py:214`, `test_oracle_ratio_db.py:265-266`, `test_oracle_rout.py:518-519`, `test_oracle_simulate_cache.py:29`, `:108`, `:125`(nmos includes 첫 줄을 래퍼 파일로). `testbench.options` 직접: `test_oracle_c10_stability.py:1469`(reltol 삭제), `test_oracle_u6_stability.py:766`(reltol·vntol 읽기) | `git grep` |
| F-8 | `diffusion=False` 호출 12곳: `conftest.py:201`(fb_input 기본), `test_oracle_cm_loop.py:57`, `test_oracle_compare.py:295, :305`, `test_oracle_junction_cap.py:79, :93, :106, :120, :131, :138`, `test_oracle_netlist.py:93`, `smoke/u6_selfchecks.py:44`. 뜻 = 'process 확산 규칙 없음'(C22 free 막힘, 독립 넷리스트와 같은 ad/pd 없음 회로) | `git grep` |
| F-9 | smoke 고정 자료 입력 3개(`current_reuse_telescopic_ota.{sizing.engine, layout.engine, layout.topology}.oracle_input.json`): `process` = `lut_npz`·`ngspice_exe`·`models`(nmos·pmos, `op_probe` `@m.{inst}.m<subckt>[{param}]`, `polarity`)·`diffusion`·`lut_reference_width_m`·`provenance`, `testbench.options` 6키(gmin·reltol 1e-4·abstol 1e-14·vntol 1e-7·itl1·itl2) | 파일 |
| F-10 | `O/tests/test_legacy_adapter.py`(LT-1 순서 3 전이라 아직 있음): `test_smoke_input_conforms_to_schema`(`:26-29`, 3항목) = OP-2가 바꿀 것. `test_smoke_netlist_regenerates_identically`(`:58-68`)·`test_smoke_loop_netlist_regenerates_identically`(`:81-92`)는 smoke 입력을 `run_netlist`(= `oracle_netlist.py` 진입, 스키마 검증)에 넣는다 -- **OP-2 새 스키마에서 반환 2로 실패**(각 3 variant × 2 bias = 12항목). 계획·design은 이 둘의 삭제를 OP-3에 둔다(`[J-7]`) | 파일:줄 |
| F-11 | 엔진 선언 `A/sky130_pdk_decl.json`: `pdk = "sky130"`, `pdk_root = "C:/pdk"`, sources 9개(`tech_lef`, `periphery_rules`, `nfet_01v8_tt_model_card`, `pfet_01v8_tt_model_card`, `mim_cap_params`, `nfet_01v8_mismatch_slopes`, `pfet_01v8_mismatch_slopes`, `scale_option`(= `sky130_fd_pr/models/all.spice`), `poly_res_params`), quantity `mismatch_slope_geometry_unit_m`(source `scale_option`, 433행), `junction_nmos_tnom`·`junction_pmos_tnom`(kind마다 하나), `mismatch_models.{nmos,pmos}.{model_source, slope_source, parameters}`. sources 항목에 `provenance` 칸은 없다(파일마다 `path, sha256, format, encoding, …, note`) | 파일 |
| F-12 | **확산 규칙은 다른 엔진 선언 파일에 있다**: `A/sky130_lut_rule_decl.json`(`pdk_root = "C:/pdk/sky130_fd_pr"`, source `lut_generator` = `sky130_lut_sweep.py`, quantity `lut_diffusion_{ad,as}_per_w_m`·`lut_diffusion_{pd,ps}_extra_m` 넷). design §10.2 `diffusion.source = <엔진 선언 lut_rule_decl quantity 키들>`인데 기술자 스키마의 엔진 참조는 `engine_decl` 하나뿐(`[J-2]`) | 파일, design 593행 |
| F-13 | PDK 원본: 모델 카드 `…nfet_01v8__tt.pm3.spice`의 `.subckt sky130_fd_pr__nfet_01v8 d g s b`(28행), 래퍼 기본 `mult = 1`(30행), 내부 첫 MOS `msky130_fd_pr__nfet_01v8 …`(31행, 옛 `op_probe`의 내부 소자 이름), vth0 식 `sqrt(l*w*mult)`(67행). `models/parameters/lod.spice` sha256 `20874af1fcb2d2ce70c65f5f2f7d6500b9e852e2507b7a4014ad2b66b8ce45e9`, 엔진 선언 sources에 없음(design S-7 확인), `models/all.spice:3`이 `.include "parameters/lod.spice"` | `C:/pdk/sky130_fd_pr/…` |
| F-14 | `extra_sources.provenance` 후보 근거: `C:/pdk/sky130_fd_pr`는 git 체크아웃(`origin https://github.com/google/skywater-pdk-libs-sky130_fd_pr.git`, HEAD `f62031a1be9aefe902d6d54cddd6f59b57627436`, 2020-11-10). `PROVENANCE.txt`는 `C:/pdk/sky130_fd_sc_hd/tech/`에만 있다 | `git -C C:/pdk/sky130_fd_pr log -1`, `find` |
| F-15 | LUT 위치 선언 `A/lut_v2_location.json`(`gmid_lut_location/1`): `pdk_root = {"env": "GMID_PDK_ROOT", "default": "C:/pdk/sky130_fd_pr"}`, `root`·`table_cache`·`files`(5항목). 계약 `E/lut/CONTRACT.md` 1.8 = 256~261행(`env` 매핑은 부르는 쪽이 넘김 258~259행, 비어 있지 않은 `env[이름]` → 그 값 `"env:<이름>"`, 아니면 `default` `"config_default"`, 둘 다 없으면 거부 260행, `os.path.abspath` 261행) | 파일·줄 |
| F-16 | **sha256이 체크아웃 줄 끝에 따라 다르다**: 저장소 `core.autocrlf = true`, `.gitattributes` 없음, 세 파일 `i/lf w/crlf`. `A/sky130_pdk_decl.json` 디스크 `24f970d5…7816c25` ≠ blob `5f32257b…6f7bf`, `A/lut_v2_location.json` 디스크 `c7ebb3c7…9383705` ≠ blob `07299556…7e27c`. 엔진 선례: `E/tests/integration/fixtures/u17_1b_s0_baseline.json`의 `pdk_decl_sha256` 9곳이 디스크(CRLF) 값 `24f970d5…` (`[J-15]`) | `sha256sum`, `git show HEAD:… \| sha256sum`, `git ls-files --eol` |
| F-17 | 엔진 구조 규칙 H: `E/tests/<엔진 패키지>/test_<x>.py`에 원본 `E/<패키지>/<x>.py`가 없으면 `orphan_test`(`E/tests/structure/structure_checks.py:940-960`), 교차 관심사 폴더 `CROSS_CUTTING_TEST_DIRS = ("structure", "contracts", "integration", "regression", "oracles", "perf", "unit")`(`:74`)만 면제. design X-13 위치 `E/tests/core/test_oracle_descriptor_engine_sha.py`는 원본 `E/core/oracle_descriptor_engine_sha.py`가 없어 위반(`[J-6]`). 지금 `E/tests/contracts/`는 없다 | 파일:줄, `ls E/tests` |
| F-18 | README 입력 절이 옛 칸을 계약으로 적는다: `O/README.md:30-35`(입력 스키마 요약 `process.models`·`op_probe`·`diffusion`·`ngspice_exe`), `:156`, `:223`(`process.models[kind].polarity`), `:319`, `:505`(`testbench.options.reltol`), CLI 표 `:16-22`(`--ngspice`). conftest 머리말(`:3`)은 "근거: README.md 동작 계약 C1~C12 + oracle_input.schema.json 만"(`[J-13]`) | 파일:줄 |
| F-19 | R6(ngspice 매뉴얼) 원문은 저장소에 없다(`git ls-files`에 매뉴얼 0, 계획 N8 528행 '로컬 PDF 없음'). 로컬 `C:/ngspice/Spice64/docs`는 텍스트 문서만, 실행 파일 판 `ngspice-46` | `git ls-files`, `ngspice_con -v` |
| F-20 | 새 이름 충돌 0건(`5fea301`, docs·`.md`·`.ai`·`.bkit` 제외): `oracle_descriptor`, `oracle_pdk_descriptor`, `lut_record_root`, `location_decl`, `engine_decl`, `extra_sources`, `descriptor_schema_invalid`, `pdk_descriptor_stale`, `descriptor_source_duplicated`, `lut_location_decl_invalid`, `lut_record_root_mismatch`, `oracle_input_format_old`, `oracle_condition_missing`, `test_lut_record_root`, `test_oracle_descriptor`, `descriptor_fp`, `descriptor.py`, `test_descriptor`, `parallel_multiplier`, `inner_device`, `call_form`, `model_family`. `geometry_unit`은 엔진 quantity 이름 `mismatch_slope_geometry_unit_m`(엔진 선언·`E/tests/core/test_pdk_decl.py:1551`)에만 부분 일치 | `git grep` |
| F-21 | design 머리 Status(22행)는 아직 '독립 검증·사용자 승인 전'으로 적혀 있다 -- 사용자 O-12가 v0.2.6을 승인했고 `5fea301`로 병합됐다(문서 표기 낡음, design 소유자에 알림) | design 22행, O-12 |

### 1.4 삭제·변경 목록 (5fea301 실측)

#### 1.4.1 오라클 소스·데이터 (code 주체)

| # | 대상 | 위치(실측) | 처리(design) |
|---|---|---|---|
| P1 | 새 `O/descriptors/sky130.oracle_descriptor.json` | 신규 | §10.2 스키마(`mc`·`diagnostic` 없음). 값: `engine_decl` = `A/sky130_pdk_decl.json` 경로 + sha256(`[J-15]`), `extra_sources` = pmos `lod.spice`(F-13, `provenance` F-14 후보 -- 사용자 확인), `lut_record_root` = `A/lut_v2_location.json` 경로 + sha256 + 키 `pdk_root`, `lut_file_roles = []`, `kinds.{nmos,pmos}`(name·inner_device·includes·polarity·`geometry_unit = {"source": "mismatch_slope_geometry_unit_m"}`·`parallel_multiplier`(to = 인스턴스 배수 + 모델 파라미터 `mult`, 근거 F-13 30·67행)), `corners`(tt), `temperature`(`[J-3]`), `diffusion`(`[J-2]`), `model_family`. **모든 값은 사용자 확인**(§10.3 616행). 경로 기준은 `[J-4]` |
| P2 | 새 `O/core/descriptor.py` | 신규 | 기술자 읽기·검증·지문(§3.1 186행 이름). §7.2 2단계 순서(스키마 → 참조 sha256 → 원본 중복 → 참조 파일 형식), sha256 대조는 이 단계 한 곳, `lut_record_root` 해석(F-15 규칙 재구현, 엔진 import 금지, `env` 매핑을 인자로), 엔진 선언 식 형식의 읽기 함수 새로 씀(§10.2 600행, `read_pdk_decl` import 금지). 공개 서명·반환·오류 표현 = `[J-4]`. `O/core/` 안에는 `.py`만(완료 조건 1, T1-4) -- 기술자 JSON 스키마를 파일로 둘지·둔다면 위치도 `[J-4]` |
| P3 | `O/oracle_input.schema.json` | `process`(11~), `testbench.options`(171행), 최상위 `schema` const | 부분 수정: `process` = `descriptor{path, sha256}`·`lut_npz`·선택 `corner`·`temp_c`, `additionalProperties: false`(B-12). `process.models`·`ngspice_exe`·`diffusion`·`lut_reference_width_m`·`provenance`·`testbench.options` 삭제. 새 최상위 `simulator{adapter, exe, options}`, `output_reference`(`[J-8]`). 최상위 `schema` 값 = `[J-10]` |
| P4 | 옛 형식 거부 | `oracle_netlist.validate_input`(`:224-231`)과 진입점 셋(F-2) | `process.models` 또는 `process.ngspice_exe`가 있으면 `oracle_input_format_old`(§11.3), 이중 지원 없음. 그 코드가 진입점 출력에 어떻게 드러나는지 = `[J-10]` |
| P5 | 옛 모듈의 입력 읽기 13곳 | F-4 | **`[J-1]`**: 계획 OP-2 행 "이때 넷리스트는 아직 옛 생성기가 기술자 값으로 쓴다"(381행)를 design이 사이트별로 정하지 않았다. 정해야 할 것: subckt 이름·include 줄(코너 치환 포함)·동작점 탐침 틀(옛 `op_probe` = 방언 틀 + `inner_device`)·`polarity`·확산 규칙·`.option` 줄·`reltol_of` 입력이 각각 어디(기술자 / `simulator.options`)에서 오는지, 기술자를 누가 언제 읽어 옛 모듈에 넘기는지(`oracle_run`·`oracle_netlist` 진입) |
| P6 | `oracle_run.py:86-88` | `process.ngspice_exe` 대체값 | `simulator.exe`로(§11.5 대응표 `process.ngspice_exe` → `simulator.exe`). CLI `--ngspice`(F-5)와의 관계·이름 변경 card = `[J-9]` |
| P7 | 온도·코너 | `oracle_netlist.py:300-303`, `:987-990`(LUT meta만) | §11.2: 입력 `process.corner`·`temp_c`가 있으면 그것, 없으면 LUT meta, 둘 다 없으면 `oracle_condition_missing`. 입력 온도가 LUT `temp_c`와 다를 때(온도 게이트 §12.6 = OP-6 전) = `[J-8]` |

#### 1.4.2 엔진 쪽 (test 주체 -- 8a 예외 첫째 하나)

| # | 대상 | 처리 |
|---|---|---|
| E1 | X-13 test 새 파일 하나 | (a) 엔진 선언 파일 sha256 ≠ 기술자 `engine_decl.sha256`이면 실패 (b) 엔진 선언 `sources` 파일 집합 ∩ 기술자 `extra_sources` 파일 집합 = ∅(경로·sha256 둘 다). 엔진 코드 import 없음, JSON만. **위치 `[J-6]`**(design `E/tests/core/`는 규칙 H 위반, F-17). 엔진 소스·기존 test·`A/sky130_pdk_decl.json` diff 0 |

#### 1.4.3 test (test 주체 몫 -- 5fea301 실측)

| 대상 | 처리 | 실측 |
|---|---|---|
| `O/tests/conftest.py` 생성기 다섯(F-6) | 새 형식으로(§15.4 1064행, 이름·인자 유지 → 183줄·28파일 무변경). 기술자 = sky130 기술자(OP-2에는 stub 없음 -- stub용 SI 기술자는 OP-3). `diffusion=False`(F-8 12곳)의 새 뜻 = `[J-12]` | F-6, F-8 |
| 생성기 밖 옛 칸 직접 수정 19줄·9파일 + `testbench.options` 2줄(F-7) | 새 형식으로 다시 씀(polarity·subckt·includes 변형은 기술자 변형 픽스처가 필요 -- 기술자 경로 기준 `[J-4]`) | F-7 |
| CLI `--ngspice` 3곳(conftest `:280`·`:300`, c10 `:972`) | `[J-9]` | F-5 |
| `test_oracle_input_schema.py`(8함수) | 새 형식 + 옛 형식 거부로 다시 씀(§18.2 1183행) | F-2 |
| `test_legacy_adapter.py::test_smoke_input_conforms_to_schema`(3항목) | '옛 형식이라 거부(`oracle_input_format_old`)' test로(계획 381행) | F-10 |
| `test_legacy_adapter.py`의 재생성 일치 test 2함수 12항목 | `[J-7]`(OP-2 새 스키마에서 실패, 삭제는 계획상 OP-3) | F-10 |
| 새 test | OP2-T1~OP2-T14(interface card 3절) | 이름 충돌 0(F-20) |

#### 1.4.4 문서

| 위치 | 처리 |
|---|---|
| `O/README.md` 입력 절·CLI 표(F-18) | `[J-13]` |
| design·계획 J 개정 | 오케스트레이터(S-7 순서) |
| history·옛 판 문장 | 바꾸지 않는다 |

#### 1.4.5 삭제 이름 grep 0 (완료 조건 6 가운데 OP-2 몫)

| 이름 | grep 범위 | 범위 밖 남는 쓰임 | 실측 hit(5fea301) |
|---|---|---|---|
| 스키마 키 `op_probe`·`ngspice_exe`·`models`(`process` 아래)·`diffusion`(`process` 아래)·`lut_reference_width_m`·`provenance`(`process` 아래) | `O/oracle_input.schema.json` | 최상위 `provenance`(그대로), `devices[].diffusion`(그대로) | 스키마에 모두 있음(F-3) |
| `testbench.options` | 스키마 | -- | 171행 |
| 옛 칸 읽기 `["process"]["models"]`·`process.get("diffusion")`·`["process"].get("ngspice_exe")`·`tb.get("options")`·`tb["options"]` | `O/oracle_*.py` | `legacy_adapter.py`(LT-1) | 13곳(F-4) -- 처리 방식 `[J-1]` |
| `process_from_lut_generator` | -- | LT-1 순서 3 몫(완료 조건 6이 그 병합에 의존, 계획 N5.3-6) | `legacy_adapter.py`에 있음 |

#### 1.4.6 보존 계약

| 대상 | 내용 |
|---|---|
| `E/` 전체, `A/sky130_pdk_decl.json`, `A/sky130_lut_rule_decl.json`, `A/lut_v2_location.json` | diff 0(8a, D-9). X-13 test 새 파일 하나만 예외 |
| `O/smoke/*.oracle_input.json` 3개 | 고정 자료, 고치지 않음(X-5) |
| `O/oracle_*.py`의 판정·측정 수학·결과 칸 | OP-3~OP-5 몫, 이 card에서 바꾸지 않음(입력 읽기 자리 `[J-1]`만) |
| 넷리스트 본문 | 같은 회로·같은 PDK 값이면 소자 줄·탐침·`.option`이 base와 같아야 함(기하 단위·배수 반영은 OP-3). 비교 기준 = `[J-1]`(include 경로 표기 차이 허용 여부) |

### 1.5 배선 (design 확정값 + 미정 칸)

#### 1.5.1 기술자 읽기 흐름

```text
진입(oracle_run / oracle_netlist / oracle_compare)
  1 입력 스키마 검증: process.models | process.ngspice_exe 있음 -> oracle_input_format_old      [표현 J-10]
    process 닫힌 키(B-12) 위반 -> 스키마 위반(C13)
    조건: input corner/temp_c -> 없으면 LUT meta -> 둘 다 없음 -> oracle_condition_missing [입력≠LUT 온도 J-8]
  2 기술자 읽기(core/descriptor.py, 처음 걸린 하나):
    스키마(닫힌 키, extra_sources.provenance 비어 있지 않음 등) -> descriptor_schema_invalid {detail: JSON 포인터 + 규칙}
    참조 sha256 전부 한 번에(engine_decl, 쓰는 engine source 키, extra_sources, lut_record_root.location_decl)
      -> pdk_descriptor_stale {ref, path, expected_sha256, actual_sha256|"missing"}
    원본 중복(엔진 sources ∩ extra_sources, 경로 또는 sha256) -> descriptor_source_duplicated
    참조 파일 형식(위치 선언: 1.8 형식 아님 / pdk_root 없음 / env·default 둘 다 없음) -> lut_location_decl_invalid {item, why}
    lut_record_root 해석: env[이름] 비어 있지 않음 -> abspath(값) "env:<이름>", 아니면 abspath(default) "config_default"
  8 (첫머리) 기록 뿌리 교차 검사 -> lut_record_root_mismatch                               [J-5]
  -> 옛 넷리스트 생성기가 기술자 값으로 씀                                                  [J-1]
```

#### 1.5.2 만들면 배선 -- 새 칸마다 소비자 또는 출력 전용(design §6.1 원칙의 OP-2판)

| 새 칸 | 소비자(OP-2 시점) | 상태 |
|---|---|---|
| 입력 `process.descriptor{path, sha256}` | 진입점 → `core/descriptor.py` | `[J-1]`·`[J-4]` |
| 입력 `process.corner`·`temp_c` | 옛 넷리스트 `.temp`·include 코너 | `[J-8]`(LUT와 다른 온도) |
| 입력 `simulator.exe` | `oracle_run.py:86` 대체값 | `[J-9]` |
| 입력 `simulator.options` | 옛 `.option` 줄(`oracle_netlist.py:317`·`:998`), meta `tb_options`(`:554`), `reltol_of`(noise·swing) | `[J-1]` |
| 입력 `simulator.adapter` | **OP-2에 소비자 없음**(어댑터 선택 §7.2 1단계 = OP-3) | `[J-8]` |
| 입력 `output_reference` | **OP-2에 소비자 없음**(V_sys·PC-10 = OP-5·OP-6) | `[J-8]` |
| 기술자 `kinds.*.name`·`includes`·`polarity`·`inner_device`, `corners`, `diffusion` | 옛 넷리스트 생성기 | `[J-1]`·`[J-2]` |
| 기술자 `kinds.*.geometry_unit`·`parallel_multiplier` | **OP-2에 소비자 없음** -- 계획 OP-2 행이 '선언'만 OP-2에 두고 소비(소자 줄·미선언 거부)를 OP-3에 둠 | 계획이 정한 시차(1.9 D-3) |
| 기술자 `temperature.tnom` | **OP-2에 소비자 없음**(옛 코드는 tnom을 쓰지 않음, `.temp` = LUT temp_c) | `[J-3]`·`[J-8]` |
| 기술자 `model_family` | **OP-2에 소비자 없음**(op 이름 대응표 = OP-3 어댑터) | 1.9 D-3과 같음 |
| 기술자 `lut_record_root` | `[J-5]` | `[J-5]` |
| 기술자 `lut_file_roles` | OP-2는 `[]`, 소비자 OP-3 | 1.9 D-3 |

### 1.6 결과 JSON·공개 형식 변경

| 출력 | 바뀌는 것 |
|---|---|
| 오라클 입력 형식 | `process` 칸 교체(1.4.1 P3), `testbench.options` → `simulator.options`, 새 `simulator`, `output_reference`(`[J-8]`), 최상위 `schema` 값 `[J-10]` |
| 진입점 거부 | 옛 형식 → `oracle_input_format_old`(표현 `[J-10]`), 기술자 오류 다섯 코드(1.5.1) |
| 새 파일 | `O/descriptors/sky130.oracle_descriptor.json`, `O/core/descriptor.py`(공개 API `[J-4]`) |
| 결과 JSON(`*.sim.json`·`*.compare.*`) | 바뀌지 않음(결과 칸 대응은 OP-3~OP-5). 기술자 지문 칸을 결과에 넣는 것은 OP-3(`ResultBundle.descriptor_fp`) |
| CLI | `[J-9]` |

### 1.7 완료 조건

1. (J 전부 닫힘 -- 착수 조건) design 개정 병합, J-7은 계획 개정 먼저(S-7).
2. 기술자 파일이 §10.2 스키마(mc·diagnostic 제외)를 따르고, 기술자 읽기가 실제 sky130 기술자를 오류 없이 읽는다(양성 대조). sky130 값은 사용자 확인 기록(user_decisions)이 있다.
3. 거부가 **실제로 거부함**을 먼저 보인다: 1.5.1의 코드마다 깨진 변형 하나 이상이 그 코드로, 실행 전에(ngspice 호출 0) 거부된다. 처음 걸린 하나만 나온다(§7.2 순서: 스키마 위반과 sha256 불일치가 함께 있는 변형 → `descriptor_schema_invalid`).
4. `lut_record_root` 해석: §18.1 1169행 경우 전부(환경 값 있음 / 빈 값 / 없음 + default / 둘 다 없음 / `pdk_root` 칸 없음 / 기술자 자체 형식 오류와 구분 / 위치 선언 sha256 다름 / (`[J-5]`) 다른 트리) + 쓴 쪽 기록(`env:<이름>` / `config_default`).
5. 옛 형식 입력(smoke 고정 자료 3개 포함)이 netlist·run·compare 진입점에서 거부되고 산출물 0(C13 방식), 같은 회로의 새 형식 입력은 받아들여진다(양성 대조).
6. X-13 test가 엔진 suite에서 돌고 통과, 기술자 sha256을 하나 바꾼 사본·`extra_sources`에 엔진 source 경로(또는 sha256)를 넣은 사본에서 실패함을 보인다(검사기 거부 증거, 사본은 test 안 tmp).
7. 8a: `E/`(X-13 새 파일 제외)·`A/sky130_pdk_decl.json`·`A/sky130_lut_rule_decl.json`·`A/lut_v2_location.json` diff 0. `E/tests/structure` 위반 0(규칙 H는 `-m structure_test_mapping`으로 base와 비교 -- X-13 파일이 orphan을 더하지 않음).
8. 1.4.5 grep(스키마 키·옛 칸 읽기, `[J-1]` 결과대로) 0.
9. 오라클 test 전체(`python -m pytest -q skills/analog-gmid-design/tools/spice_oracle/tests -p no:cacheprovider`, ngspice·PDK 있는 기계, slow 포함) 통과. 깨진 옛 test 목록과 처리(다시 씀 / `[J-7]`)를 보고.
10. 넷리스트 동등성(감사): conftest 생성기 회로(cs·rc·fb, free·forced·iso)에서 base(옛 형식)와 head(새 형식) 넷리스트 줄 차이가 `[J-1]` 기준 안.
11. **병합 조건(R6, `[J-14]`)**: ngspice 매뉴얼 원문 보관, reltol·vntol 기본값 쪽 번호, abstol 값·쪽(S-28), 시간 걸음 실패 문장 형태(design 1289행)가 채워진 기록.
12. 공통: 만들면 배선 1.5.2 표의 모든 칸이 소비자 있음 또는 출력 전용 선언(design 개정으로), graph 단일 정본 오라클판(같은 값의 정본 하나: 엔진 sources 파일 정보는 엔진 선언에만, LUT 기록 뿌리는 `A/lut_v2_location.json`에만, 기술자에 사본 없음 -- 기술자 sha256 참조만), gap-detector ≥ 90 %.

### 1.8 판단 기록 -- 미정 `[J-n]` (이 card가 정하지 않음, S-7)

| id | 무엇이 | 어느 절 | 선택지(정하지 않음) |
|---|---|---|---|
| **J-1** | OP-2에서 옛 모듈 13곳(F-4)이 새 형식을 읽는 방식이 design에 없다. 계획 381행 "넷리스트는 아직 옛 생성기가 기술자 값으로 쓴다"만 있다. 특히 (i) 옛 `op_probe` 틀 `@m.{inst}.<내부>[{param}]`의 방언 부분은 design상 어댑터 몫(599행)인데 OP-2에는 어댑터가 없다 (ii) include `{corner}` 치환 ↔ 기술자 `includes[{source, corner_section}]`·`corners.select` 대응 (iii) 확산 규칙 값의 출처(J-2) (iv) 기술자를 읽는 호출 자리 (v) 넷리스트 동등성 판정 기준(include 경로 표기) | §20 OP-2 행, §10.2, §15.1 | (가) design에 'OP-2 옛 모듈 입력 읽기 대응표'(사이트별 새 출처, 방언 틀은 옛 `oracle_netlist`에 두는 과도기 -- OP-3이 지움) 추가 (나) OP-2는 기술자·스키마·읽기 코드만 만들고 입력 형식 전환(옛 형식 거부)을 OP-3과 같은 변경으로 -- 계획 OP-2 행·D-5 시점 개정(S-7) |
| **J-2** | 기술자 `diffusion.source`가 '엔진 선언 lut_rule_decl quantity 키들'인데 그 quantity는 다른 엔진 선언 파일 `A/sky130_lut_rule_decl.json`에 있고(F-12), 기술자 스키마의 엔진 참조는 `engine_decl` 하나다. 옛 2키(`ad_per_w_m`·`pd_extra_m`)와 엔진 4키(`ad`·`as`·`pd`·`ps`)도 다르다 | §10.2 593행 | (가) 엔진 선언 참조를 여럿 받는 칸(이름은 design이 정함) (나) `diffusion`을 기술자 밖에 둠(소자별 `devices[].diffusion`만, C22 막힘 그대로) (다) 그 밖 design 안 |
| **J-3** | `temperature.tnom.source`는 키 하나인데 엔진 quantity는 kind마다(`junction_nmos_tnom`·`junction_pmos_tnom`, F-11). OP-2 시점 소비자도 없다 | §10.2 592행 | (가) kind별 칸 (나) OP-2 기술자에서 빼고 소비 card(OP-5·OP-6)가 더함 |
| **J-4** | `core/descriptor.py` 공개 API(함수 이름·인자·반환 자료형), 오류 표현(예외 클래스 / 반환 값, `code`·`detail` 접근), 기술자 JSON 스키마를 어디에 둘지(`O/core`에는 `.py`만), 경로 기준: `engine_decl.path`·`extra_sources.{path, base}`(`base` 뜻 미정의)·`location_decl.path`·입력 `process.descriptor.path`가 무엇 기준 상대인지(저장소 루트 / 기술자 폴더 / 절대) | §10.1·§10.2, §3.1 | design이 정함. test는 이 API로만 쓴다(interface card C2) |
| **J-5** | `lut_record_root_mismatch` 교차 검사는 §7.2 8단계(모델 묶음 비교, OP-3)이고 LUT 기록(`model_files_sha256`)이 있어야 한다. 그런데 §18.1 1169행은 OP-2 test에 넣었다. OP-2에 배선하면 conftest `make_lut`(기록 없음)·smoke LUT로 도는 지금 test가 처리 규칙 없는 상태가 되고(`lut_model_provenance_missing`은 OP-3), 배선하지 않으면 '만들고 안 씀'이다 | §7.2 446행, §18.1 1169행 | (가) 교차 검사 함수·그 test 행을 OP-3으로 옮김(design §18.1 행 개정) (나) OP-2에서 만들고 배선은 OP-3 -- 미배선 기간 사용자 승인 필요(절대원칙) |
| **J-6** | X-13 test 위치 `E/tests/core/test_oracle_descriptor_engine_sha.py`는 엔진 규칙 H `orphan_test`(F-17) | §18.1 1167행 | (가) 교차 관심사 폴더(`E/tests/contracts/` 신설 또는 `E/tests/integration/`) -- design 개정 (나) 규칙 H 예외 추가(엔진 test 도구 변경 = 8a 위반) |
| **J-7** | smoke 재생성 일치 test 2함수 12항목이 OP-2 새 스키마에서 실패(F-10). 계획(381·382행)·design(1184행)은 삭제를 OP-3에 둔다 → OP-2~OP-3 사이 깨진 test | 계획 N5.1 OP-2·OP-3 행 | (가) 그 삭제 + `criteria_weakened`를 OP-2로 앞당김(계획 개정, 같은 비교는 검증자 N4-3) (나) J-1 (나)로 입력 형식 전환 자체를 OP-3으로 |
| **J-8** | OP-2 시점 소비자 없는 새 칸: `simulator.adapter`(OP-3), `output_reference`(OP-5·OP-6), 입력 `temp_c`가 LUT `temp_c`와 다를 때(온도 게이트 OP-6 전), 기술자 `geometry_unit`·`parallel_multiplier`·`model_family`·`tnom` | §11.1·§11.2, §6.1 원칙 | (가) 칸을 그 소비 card에서 더함 (나) OP-2에서 더하고 '출력 전용'/fail-closed 거부(예: LUT와 다른 온도 = 거부)로 design에 적음. 기하 두 칸은 계획이 OP-2 선언을 정했다(1.9 D-3) |
| **J-9** | CLI `--ngspice`(F-5 다섯 진입 + test 3곳): §15.1 1040행 'OP-2(입력), OP-3(실행)'이 어느 card가 인자를 바꾸는지 정하지 않는다. `simulator.exe`와 `--ngspice`/`--sim-exe`의 우선 순서도 없다(옛 규칙: CLI 우선, `oracle_run.py:86`) | §15.1, §8.2 471행 | (가) OP-2 = 입력 칸 `simulator.exe` 대체값만, 인자 이름 변경은 OP-3 (나) OP-2에서 인자도 `--sim-exe`로 |
| **J-10** | 새 입력 형식의 최상위 `schema` 값(옛 `spice_oracle_input/1` 유지 / 새 이름), 옛 형식 판정이 §11.3의 칸 기준뿐인지, `oracle_input_format_old`가 옛 진입점(반환 2 + 위반 문장 출력, F-2)에 어떤 꼴로 나오는지(문장 안 코드 문자열 / 별도 출력) | §11.3, §7 378행 | design이 정함(이름 발명 금지) |
| **J-11** | OP-2 기술자 스키마가 `mc`·`diagnostic` 키를 만나면: 닫힌 키 집합으로 거부(`descriptor_schema_invalid`) / 선택 칸으로 허용하고 OP-5가 검사 | §10.2 602행, §10.4 653행 | fail-closed 쪽이 거부지만 design이 정함 |
| **J-12** | conftest `diffusion=False`(F-8, 12곳)의 뜻 '확산 규칙 없음'이 기술자로 옮겨진 뒤 무엇으로 표현되는지(기술자 변형 / `diffusion` 칸 선택 여부), 생성기 밖 polarity·subckt·includes 변형(F-7)의 기술자 변형 방식 | §15.4 1064행 | J-2·J-4 결정에 따름. design이 '기술자 `diffusion` 선택/필수'를 정함 |
| **J-13** | `O/README.md` 입력 절·CLI 표(F-18)는 conftest의 계약 근거인데 §17.4(1141행)는 README 재작성을 OP-3~OP-6에만 둔다 | §17.4 | (가) OP-2가 입력 절만 고침 (나) OP-3에서 한꺼번에(그동안 README와 스키마 불일치) |
| **J-14** | R6 병합 조건의 산출물 위치·주체: 매뉴얼 원문 보관 경로(계획 N8 'assets/ 원문 보관소 규칙'), 쪽 번호·abstol 값을 OP-2 시점 어디에 적는지(`calibration.json`은 OP-4), 누가(검증자/오케스트레이터 문서 작업) | §8.3 504행, §19.3 1283·1288·1289행, X-D4 | design·계획이 정함 |
| **J-15** | git 텍스트 파일 sha256이 체크아웃 줄 끝에 따라 다르다(F-16). 기술자 `engine_decl.sha256`·`location_decl.sha256`과 X-13 test가 이 기계(CRLF) 값이면 LF 체크아웃에서 `pdk_descriptor_stale`·X-13 실패 | §10.1, D-9 | (가) 엔진 선례대로 디스크 바이트 값(기계 의존 수용, 위험 기록) (나) `.gitattributes`로 해당 JSON 줄 끝 고정(저장소 설정 변경 -- 사용자 승인) (다) 정규화한 바이트의 sha256(엔진 `decl_sha256`과 정의가 달라져 X-13 비교가 깨짐 -- 계획 개정) |

### 1.9 원래 취지와 다른 판단

| # | 내용 | 상태 |
|---|---|---|
| D-1 | 이 card는 취지 쪽(PDK 데이터를 입력에서 빼 기술자로, 엔진 무변경)으로 간다 | -- |
| D-2 | (J-1 (나)를 고르면) 계획 OP-2 행의 '옛 형식 거부'가 OP-3으로 밀린다 -- 원래 계획과 다름 | J-1 결정 때 보고 |
| D-3 | 기술자 `geometry_unit`·`parallel_multiplier`·`model_family`·`lut_file_roles`는 OP-2에서 선언되지만 소비는 OP-3(계획 381·382행이 정한 시차). '만들면 배선'의 card 사이 공백이다 -- 계획이 정한 것이라 이 card는 바꾸지 않고 보고만 | 보고 |
| D-4 | (J-7 (가)) 재생성 일치 test 삭제를 OP-2로 앞당기면 `criteria_weakened`가 한 card 앞선다 | J-7 결정 때 |
| D-5 | (J-15 (가)) 기술자 참조 sha256이 기계 줄 끝 설정에 묶인다 -- '공정·시뮬레이터 무관' 취지와 별개로 '기계 무관'이 깨진다(엔진 선례 같음) | J-15 결정 때 |

---

## 2. 공통 브리핑 (이 card의 code·test·audit agent 필독, 1쪽)

base = `5fea301`(J 개정 뒤에는 그 병합 master로 바꾼다). design: `docs/02-design/features/oracle-portability.design.md` v0.2.6 §10.1~§10.3(mc·diagnostic 제외), §7(OP-2 몫), §7.2 1·2(·8 첫머리 J-5)단계, §11, §15.1 1038·1040행, §15.4 1064행, §18.1 1167·1169행, §18.2 1183·1184·1187행, §20 OP-2 행. 계획: `docs/01-plan/features/oracle-portability.plan.md` v0.6.6 N5.1 OP-2 행(381행), N3.4, N5.3 1·6·7·8a, G-5. 사용자 결정 기록: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md`(읽기만, O-1~O-12·L-1~L-3·T-31·T-33·S-7·P-1). card: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/oracle/OP2_SPEC_CARD.md`(code·audit), `OP2_INTERFACE_CARD.md`(test는 이것만 -- 소스 열람 금지).

### 절대 규칙
1. **design 그대로 구현한다. as-built 결정 금지.** `[J-n]` 칸은 닫히기 전 손대지 않는다. design에 없는 것을 정해야 하거나 모순이면 멈추고 보고(무엇이, 어느 절이, 선택지).
2. **정본 하나(오라클판 graph 단일 정본)**: 엔진 선언 `sources`의 파일 경로·sha256은 엔진 선언에만(기술자는 source 키로만), 엔진 선언에 없는 파일만 `extra_sources`, LUT 기록 뿌리는 `A/lut_v2_location.json`에만(기술자는 경로 + sha256 참조), DC 허용오차는 기술자에 두지 않음(`simulator.options`·어댑터 보정값). 같은 값의 사본을 만들지 않는다. 계산식(1.8 해석 규칙, 엔진 선언 식 형식 읽기)을 쓰기 전에 기존 정본(계약 문서)을 확인하고 그 규칙만 옮긴다.
3. **만들면 배선**: 새 칸·함수마다 소비자 또는 '출력 전용' 선언(1.5.2). 소비자 없는 칸은 J 결정 전 만들지 않는다.
4. **fail-closed**: 기술자·입력 결함은 실행 전에 처음 걸린 하나로 거부(§7.2 순서). 기본값으로 대체하지 않는다(SI·배수 1·LUT meta 절대 `pdk_root`로 돌아가기 금지).
5. **P-1**: 규칙의 제한·예외는 물리·계약 근거가 있을 때만, 가장 일반적인 형태부터.
6. **이름·상수 발명 금지, 규칙·코어 코드에 PDK·시뮬레이터·회로 이름 금지**(사례 값은 기술자 JSON에만). 오류 코드·칸 이름은 design §7·§10·§11 그대로.
7. **엔진 무변경**(8a, D-9): `E/`·`A/sky130_pdk_decl.json`·`A/sky130_lut_rule_decl.json`·`A/lut_v2_location.json` diff 0. 오라클은 엔진을 import하지 않는다(오라클 C1, P NFR-P3). 예외는 X-13 test 새 파일 하나(위치 J-6).
8. **틀린 구조는 재작성**, 옛 스키마 칸·옛 입력 읽기·README 옛 문장은 같은 변경에서 삭제(J-1·J-13 결정대로).
9. **작성자 ≠ 검증자**: code agent는 test·기대값·기술자 변형 픽스처를 쓰지 않는다(conftest 생성기·X-13 test도 test 주체). test agent는 피검 코드를 불러 기대값을 만들지 않는다(기대값 = 계약 문서·JSON·손계산). 같은 커밋에서 코드와 기준을 함께 바꾸지 않는다. 기준 약화(`criteria_weakened`)는 사용자 승인 사항.
10. **sky130 기술자 값은 사용자 확인 뒤**(§10.3). code agent는 사용자 확인 기록이 있는 값만 쓴다.

### 실행 환경·git 가드
- python: `/c/Python314/python.exe`(bash `timeout` 래퍼 금지). 오라클 test: 위치 `<worktree>`, `python -m pytest -q skills/analog-gmid-design/tools/spice_oracle/tests -p no:cacheprovider`(ngspice `C:/ngspice/Spice64/bin/ngspice_con.exe`, PDK `C:/pdk/sky130_fd_pr` -- 환경 `SPICE_ORACLE_NGSPICE`·`SPICE_ORACLE_PDK`). 엔진 test: 위치 `<worktree>/skills/analog-gmid-design`, `python -m pytest -q gmid_engine/tests/<경로> -p no:cacheprovider`, 규칙 H `-m structure_test_mapping`.
- **ngspice 실행은 한 번에 하나**(엔진 실행과 겹치지 않게). 긴 실행은 결과를 파일에(`C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op2_<role>/run.txt`, 케이스마다 append). 백그라운드 실행이 끝날 때까지 턴을 끝내지 않는다.
- git: 항상 `git -C <자기 worktree>`, 스크립트 `set -e`. 다른 worktree·master 금지, reset --hard·다른 브랜치 checkout·push·merge 금지, 커밋은 자기 브랜치에만.
- 커밋 메시지 끝(`--trailer`): `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, `Claude-Session: https://claude.ai/code/session_012FxFP7YSWEBBCB9rmBQjLL`.
- 임시 파일: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op2_<role>/`(자기 것만).

### 최종 보고(한국어) 필수 항목
1. 구현·작성한 design 절과 상태. 2. 멈춤·보고 항목. 3. 지운 옛 칸·코드(파일:줄), 바뀐 입력 읽기 자리(파일:줄), 1.4.5 grep. 4. 정본 하나 자기 점검(사본 0, 기술자에 엔진 source 경로·sha256 재기재 0). 5. 만들면 배선 자기 점검(1.5.2 표 칸별 소비자). 6. 오라클 test·엔진 `tests/structure`(H는 base 비교)·X-13 결과, 깨진 옛 test 목록. 7. 커밋 해시.

## 오케스트레이터 판단 (상속 -- card A·nfr4c2·xrunf1b 교훈)
- (card A J-O1) interface card '## 신규 시그니처' 절로 merge_gate가 새 심볼 부재 red를 card 이유로 센다.
- (nfr4c2 J-O2) red 예상 목록에는 오라클·엔진 동작을 보는 test만. test 도구(conftest 생성기 자체) 시험은 빼고 감사도 세지 않는다. **기존 오라클 test는 새 conftest(새 형식 입력)로 base에서 대부분 red가 된다**(base 스키마가 새 형식을 거부) -- 이것은 red 예상 목록 밖이고, 감사는 head 통과만 본다.
- (card A J-7) base·head를 같은 환경으로 감사가 둘 다 잰다(넷리스트 동등성 1.7-10).
- (이 card) J-1~J-15가 닫히기 전 code·test 착수 금지. 닫히면 J 칸만 채운 개정판을 낸다.
