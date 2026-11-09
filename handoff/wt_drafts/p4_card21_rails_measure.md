# #21 `mg1-rail-voltage` -- `meta["rails"]`·다른 meta 키·instance.json 영향 실측

> 대상 질문: `draft_phase4_design.md` v0.9.2 머리 P-37 항목의 [미확인] -- "#21의 `rail_voltages` 보관 위치는 'spec dict 밖, `RailDeclaration`과
> 같은 계층'(§10.4)이다 -- `meta["rails"]` 안에 들어가는지는 [미확인](#21 작성 전 실측, 들어가면 #21 oracle과 E11 목록에 더한다)".
> 측정 판 = `a796468`(게이트 master 엔진), 스크래치 `C:/g148`(끝나고 삭제), 스크립트·출력 `_drafts/p4_scripts/c21/`.

## 1. 답

**아니다(no).** #21이 의도한 변경은 9개 library 회로에서 `load_topology`가 돌려주는 `meta["rails"]`도, 그 밖의 meta 키·값도,
`transistors`·`run_topology_pipeline` 결과도, `instance.json`도 바꾸지 않는다. 그래서 #21 oracle의 E-LIB는 Phase 3 E5식
'`rails`를 빼고 계약값으로 따로 판정(masked-by-contract)'이 아니라 **'card base 대 병합본 해시 같음(`meta["rails"]` 포함, 빼는 키 없음)'**이 맞다.
E11(Phase 4 E-LIB 재측정)의 빼는 meta 키 목록에 #21 몫은 없다(그 목록의 `rails`는 #17 `polarity` 몫뿐).

근거는 둘이다.

* **코드(구조)**: `load_topology(json_path)`는 인자가 topology 경로 하나다(SD 8539, `a796468`). spec(하네스 `SPECS`)은 이 함수에 들어오지 않으므로
  `rail_voltages(spec, rails)`(§10.4)는 `load_topology` 안에서 계산될 수 없다 -- 계산 지점은 spec과 `meta["rails"]`가 만나는 평가 문맥
  (`_build_theta_evaluator` SR 7930, `load_topology` 직후 7944)이다. meta를 만든 뒤 고치는 대입(`meta[...] =`·`setdefault`·`update`)은
  SR·SD·하네스 어디에도 없다(grep 0). 그래서 #21이 meta에 닿는 길은 둘뿐이다: (i) `load_topology`가 쓰는 파일 읽기(#20 `load_json_checked`)에
  #21이 더하는 `where="topology"` 옛 키 행(metric 인자 `supply_nets`)이 library 파일을 **거부**하는 경우, (ii) 구현이 전압을 meta나
  `RailDeclaration` 필드로 싣는 경우(§10.4 '보관 위치'의 오독). (i)은 library 9회로에 해당 키가 0이라(아래 §3) 거부가 없고, (ii)는 계약 위반이다.
* **시제품 실측(§4)**: B26-1 계약 1·2 시제품(p1) 위에 CC-5 최소 시제품(p20, #21의 선행 #20 대용)과 #21 시제품(p21)을 얹어 `e_lib_p3.py`로 잰 결과,
  p20 → p21에서 E-LIB 해시(`rails` 포함, 빼는 키 없음)가 같고(`c121333162fade9e` = `c121333162fade9e`), meta 키 집합이 같고(base 대비 `rails` 하나),
  `masked.rails` 9회로 값이 같다. E-INST(`e_inst_p3.py`) folded_cascode·current_reuse 두 회로의 instance.json 해시·파일 바이트가 p1 → p21에서 같다.

## 2. 읽은 계약

* Phase 4 v0.9.2 §5.4 #21 행: `supplies_v`(하네스 `SPECS`: two_stage·current_reuse·folded = `{vdd: 1.8, gnd: 0.0}`, nmcnr = `{vdd: 1.8, vss: 0.0}`),
  `rail_voltages` 유도 함수, 스칼라 `vdd` 20줄을 span/hi/lo로 교체, metric 인자 `supply_nets`·`rail_nets` 정리, 옛 키 행(`supplies`, spec `vdd`, metric
  `supply_nets`). 판정 = red-green + DEC-69 equivalence('키 매핑 뒤 θ*·metric·instance.json 동일'). oracle (c) = 'E-INST'.
* §10.4: `RailVoltages(by_net, hi, lo, span)`, `rail_voltages(spec, rails)`, 거부 `set(supplies_v) != set(rails.nets)`·spec 스칼라 `vdd`.
  "보관 위치는 spec dict 밖 ... `RailDeclaration`과 같은 계층(로드 결과 객체 → 평가 문맥 `ctx`)". 분류표 F4 20줄 + 레일 0 V 리터럴 3곳.
* 00-common §6.1·6.2: `LEGACY_NAMES` 행(`where`·`scope`·`match`), `load_json_checked`(파일 읽기 직후 `reject_legacy_names`), 하네스 spec은
  `spec_fn()` 반환 직후 `reject_legacy_names(spec, "harness_spec")`. 계획 N3.16 769~771행·802행(MG1 옛 키 = 계획 `supplies`, spec 스칼라 `vdd`,
  metric 인자 `supply_nets`).
* B26-1 card(`draft_b26_1.spec.md`) 계약 1(`RailDeclaration(nets=frozenset(supply_nets))`, 필드 `nets` 하나 -- B26-2가 극성 필드를 더한다),
  계약 2(`load_topology`가 진입 파일로 정확히 한 번 `rail_declaration`을 불러 `meta["rails"]`), 계약 8(E-LIB 9/9 -- `rails` 제외 meta·`transistors` 같음).
* `instance.json` 키(SD 8988 `save_instance_json`): `schema_version`·`topology_ref`·`sizing`·`netlist`·`floorplan`·`box_shape`·`audit_row_split`·`coverage`
  (선택 `scope_note`) -- spec은 들어가지 않는다. 그래서 하네스 `SPECS`의 `vdd` → `supplies_v` 교체도 instance.json에 닿지 않는다.

## 3. library 데이터 사실 (`a796468`, 9회로 + `_TEMPLATE` 제외)

| 키 | 위치 | 회로 | #21과의 관계 |
|---|---|---|---|
| `supply_nets` | 최상위 | 9/9 | B26-1 `meta["rails"]`의 원천. #21은 읽기만(`rails.nets`) |
| metric 인자 `supply_nets`·`rail_nets` | `/sizing_roles/metrics/*` | **0** | #21 옛 키 행(`supply_nets`)이 거부할 대상이 library에 없음 |
| `supplies` | 어디든 | **0** | 옛 키 행(`supplies`, harness_spec) 대상 없음 |
| 키 이름 `vdd` | `/sizing_roles/metrics/psrr_estimate_db/excite_den/vdd`(current_reuse), `/sizing_roles/metrics/gain_db/excite/vdd`(two_stage) | 2 | 넷 이름 키(여기 전압)다. spec 스칼라 `vdd` 행은 `where="harness_spec"`이라 topology를 훑지 않는다 |
| `supplies_v` | `/_declared_target_spec/supplies_v`(ngcc·nmcnr·pushpull·sf_pushpull), `/_paper_target_spec/supplies_v`(ngcc·nmcnr) | 4 | `_` 접두 문서 필드. `load_topology`가 meta에 싣지 않는다(meta는 고정 키만) |
| metric `rail` 값 `"vdd"`·`"gnd"` | current_reuse `vg15_level_v`·`vop1_level_v` | 1 | #21은 `else 0.0` → `lo`만 바꾸고 선언은 그대로. 이름 비교는 #17 몫 |

## 4. 시제품과 측정

트리(모두 `a796468` 복제, `PYTHONHASHSEED=1`, 패치 `p4_scripts/c21/patch.py`, diff `out/diff_<판>.patch`):

| 판 | 내용 |
|---|---|
| base | `a796468` 그대로 |
| p1 | B26-1 계약 1·2 시제품: SD 끝 `RailDeclaration(nets)`·`rail_declaration(topology)`(계약 1 거부 4종), `load_topology`가 진입 파일로 1회 호출해 `meta["rails"]`, 연결 파일 선언은 같은 검사 + 집합 다르면 `ValueError` (Phase 3 v8.2 F3v82 `el_p1`과 같은 모양 -- E-LIB 해시 `c121333162fade9e`로 일치 확인) |
| p20 | p1 + CC-5 최소 시제품(#21 선행 #20 대용): `LEGACY_NAMES`·`reject_legacy_names`, `load_topology` `_read_one`이 파일 읽기 직후 `where="topology"` 검사. 행 = `vs`(`/device_roles/*`) 하나 |
| **p21** | p20 + #21 시제품: (1) 옛 키 행 3개 -- `supplies`(harness_spec, 루트 `""`), `vdd`(harness_spec, 루트 `""`), `supply_nets`(topology, `/sizing_roles/metrics/*`) (2) 하네스 4회로 `"vdd": 1.8` → `supplies_v`(nmcnr는 `vss`), `canonical_spec`·`run`의 `spec_fn()` 직후 `reject_legacy_names(spec, "harness_spec")` (3) SR `RailVoltages`·`rail_voltages(spec, rails)` -- `_build_theta_evaluator`의 `load_topology` 직후 1회(`set(supplies_v) != rails.nets` 거부) (4) §10.4 분류표대로 F4 20줄 + 0 V 리터럴 3곳 교체(span 15곳·hi 3곳·lo 3곳·hi+lo 2곳), spec dict에 키를 더하지 않음(값은 spec 밖 캐시 -- 실제 card는 `ctx`) |
| x1 (음성) | p21, 단 metric `supply_nets` 행의 scope를 `""`(루트)로 잘못 둔 판 |
| x2 (음성) | p21 + `load_topology`가 `meta["rail_voltages"]`(topology `_declared_target_spec.supplies_v`)를 더하는 판 -- 전압을 로드 결과에 싣는 잘못된 보관 위치 |
| x3 (음성) | p21, 단 harness_spec `vdd` 행이 자손 매핑까지 훑는 판 |
| x4 (음성) | p21 + `RailDeclaration`에 `voltages` 필드를 더한 판 -- 전압을 `meta["rails"]` 안에 싣는 판 |

### 4.1 E-LIB (`e_lib_p3.py` sha256 `c6b82fc7…` -- Phase 3 F2v82와 같은 사본, 인자 없음 = `e_lib.py`와 같은 hash)

| 판 | MASK 없음 hash | MASK `rails` hash | load 실패 | base 대비 meta 키(더한 것, 뺀 것) |
|---|---|---|---|---|
| base | `1d2e3bf6acf762eb` | `1d2e3bf6acf762eb` | 0 | -- |
| p1 | `c121333162fade9e` | `1d2e3bf6acf762eb` | 0 | (`rails`), () 9/9 |
| p20 | `c121333162fade9e` | `1d2e3bf6acf762eb` | 0 | (`rails`), () 9/9 |
| **p21** | **`c121333162fade9e`** | **`1d2e3bf6acf762eb`** | 0 | (`rails`), () 9/9 |
| x1 | `c42dcb00f9e78372` | `c42dcb00f9e78372` | **9** (`SCHEMA_REJECTED ... ('', 'supply_nets')`) | load 예외 |
| x2 | `813ce7bb72a43c1f` | `2d734d14869e4132` | 0 | (`rail_voltages`, `rails`), () |
| x4 | `4e9814f1c67c3d84` | `1d2e3bf6acf762eb` | 0 | (`rails`), () -- 필드 `voltages`가 `rails` 안에 |

* p20 → p21: MASK 없는 해시 같음(= `rails` 값까지 같음), `masked.rails` 9회로 모두 같음(`{"__dc__": "RailDeclaration", "nets": {"__set__": supply_nets}}`).
* p1 = p20: CC-5 최소 시제품은 무동작(library에 `vs` 키 0).
* base → p1: MASK `rails` 해시 같음 -- B26-1 계약 8과 Phase 3 F3v82 재현.

### 4.2 판정기 두 모양의 대조 (base = p20, #21 card base 대용)

| head | J-hash: MASK 없음 hash 같음 + load 9/9 | J-mask: Phase 3 E5 모양(`rails` 빼고 hash 같음 + `__dc__`·`nets` 계약값) | J-mask+: J-mask + `rails` 필드 집합 같음 |
|---|---|---|---|
| p21 | PASS | PASS | PASS |
| x1 | FAIL | FAIL | FAIL |
| x2 | FAIL | FAIL | FAIL |
| **x4** | **FAIL** | **PASS** (놓침) | FAIL |

`p3v82_e5_judge.py`의 rails 계약 조건(`hv.get("__dc__") == "RailDeclaration" and hv.get("nets") == want`)은 필드 집합을 보지 않는다. 그래서
`rails`를 masked-by-contract로 판정하면 '전압을 `RailDeclaration` 필드로 싣는' 구현(§10.4 보관 위치 오독)을 통과시킨다. #21에서는 `rails`를 빼지
않는 J-hash가 그 구현을 잡는다 -- #21 oracle은 해시 같음이어야 하는 이유가 하나 더 있다.

### 4.3 게이트·유도 함수 직접 점검 (`gate_check.py` → `out/gate_<판>.json`)

| 판 | SPECS 4회로 `canonical_spec` | `rail_voltages` | 합성 거부 |
|---|---|---|---|
| p21 | 4/4 통과(키 `supplies_v`만) | 4회로 `hi 1.8, lo 0.0, span 1.8, hi+lo 1.8`(nmcnr `by_net {vdd 1.8, vss 0.0}`) | spec + 스칼라 `vdd` → 거부, spec + `supplies` → 거부, metric 선언 `supply_nets` → 거부, `supplies_v`에서 `vdd` 뺌 → 거부; 최상위 `supply_nets` + metric `excite.vdd` → **통과** |
| x1 | 4/4 통과 | 4회로 거부(`load_topology`에서 최상위 `supply_nets`가 걸림) | 최상위 `supply_nets` 합성 입력도 거부 |
| x3 | **4/4 거부**(`supplies_v/vdd`가 걸림) | -- | -- |
| p20 | 옛 키 행 없음 -- 스칼라 `vdd`·`supplies`·metric `supply_nets` 모두 통과(= #21 red의 base 쪽) | -- | -- |

### 4.4 E-INST (`e_inst_p3.py` sha256 `7d26134a…`, runpy 래퍼 `e_inst_c21.py`)

| 회로 | p1 instance.json `raw_sha256` | p21 `raw_sha256` | 파일 바이트 | 다른 최상위 키 | stdout(경과 시간·트리 루트 이름 가림) | p21 `RailVoltages` 읽기 |
|---|---|---|---|---|---|---|
| folded_cascode | `ef3cd9963d0a…` | `ef3cd9963d0a…` | 같음 | 없음 | 같음 | build 1·read 5601 |
| current_reuse_telescopic_ota | `2fc426d9ef3a…` | `2fc426d9ef3a…` | 같음 | 없음 | 같음 | build 1721·read 5,978,602 |

두 회로의 p1 값(`ef3cd9963d0a…`·`2fc426d9ef3a…`)은 Phase 3 F2v82 base 값과 같다(B26-1 시제품이 instance.json을 바꾸지 않음의 재현). read 5601 > 0이 교체한 줄이 실제
실행됐음을 보인다(spec에 `vdd`가 없으므로 교체하지 않은 읽기가 남았으면 `KeyError`/`None`이 났다 -- 패치가 남은 읽기 0을 단언).

## 5. #21이 지녀야 할 oracle 문장 (제안)

#21 행 oracle (c)의 'E-INST'를 아래로 바꾼다(E-LIB를 더하고, 두 측정 모두 **빼는 키 없는 해시 같음**):

> (c) **E-LIB 9/9·E-INST 해시 같음(빼는 키·필드 없음)**: card base 대 병합본에서 `e_lib.py`(MASK 없음) 해시가 같고 load 9/9 성공이다 --
> `load_topology`의 `meta`는 `meta["rails"]`를 **포함해** 값이 같다(#21은 `meta`에 키를 더하지 않고 `RailDeclaration`에 필드를 더하지 않는다.
> 레일 전압은 spec dict 밖·`meta` 밖의 평가 문맥에 둔다, §10.4). E-INST는 SPECS 사이징 대상 회로에서 `instance.json` 정규화 해시가 같다
> (DEC-69 equivalence -- 4회로 최저 레일 0 V). 옛 키 행 중 `where="topology"`인 것(metric 인자 `supply_nets`, scope `/sizing_roles/metrics/*`)은
> library 9회로 어디에서도 걸리지 않는다(load 9/9가 이를 판정), `where="harness_spec"`인 스칼라 `vdd`·`supplies` 행은 spec **루트** 키만 본다
> (자손을 훑으면 `supplies_v.vdd`가 걸려 E-INST가 실패한다).

그리고 §10.4 '보관 위치' 문장의 '로드 결과 객체'는 `load_topology` 반환(meta)로 읽힐 수 있으므로 "`load_topology`의 `meta`(`meta["rails"]` 포함)와
`RailDeclaration`에는 싣지 않는다 -- spec 로드 결과(하네스 `spec_fn()` 반환을 받은 쪽) → 평가 문맥 `ctx`"로 좁히는 것을 권한다(x2·x4가 그 오독의 두 형태다).

E11 목록: #21 몫 없음. P-37 머리 문장의 [미확인]은 "실측: 들어가지 않는다(`_drafts/p4_card21_rails_measure.md`)"로 닫을 수 있다.

## 6. 실행 기록

* `bash p4_scripts/c21/run.sh gate|elib|einst` → `out/log_<단계>.txt`, `out/gate_*.json`·`out/elib_*_{nomask,mask}.json`·`out/einst_*`; 비교 `python -B p4_scripts/c21/compare.py` → `out/compare.txt`.
* E-INST 소요: folded 59 s / 62 s, current_reuse 413 s / 423 s(p1 / p21). 모든 실행 rc 0, `fail_in_stdout` False.
* stdout 사본은 경과 시간(`elapsed=`)과 트리 루트 이름(`C:\g148\p1`·`p21`, `[SKIP]`·`instance.json 저장:` 줄)만 가리면 같다.

## 7. 한계

* p21은 #21 **시제품**이다. 실제 card의 `ctx` 배선·`SchemaRejectedError` 클래스·#20 실제 `load_json_checked`(UTF-8 BOM·중복 키·NaN 거부 포함)·
  #23(tol_V)·#6(N3.14)·#17(극성) 병합 상태를 흉내 내지 않았다. 보인 것은 '§10.4·N3.16·00-common §6이 정한 #21 몫을 그대로 구현하면 meta와
  instance.json이 바뀌지 않는다'와 '두 가지 오독(x2·x4)과 두 가지 scope 오류(x1·x3)는 해시 같음 판정(또는 load/E-INST 실패)으로 드러난다'이다.
* #21 card base에 #17이 먼저 병합돼 있으면 `meta["rails"]`에 `polarity`가 있다. 그 경우에도 #21은 그 값을 바꾸지 않으므로 base·병합본 해시 비교는
  그대로 성립한다(이 측정은 `polarity` 없는 base에서 했다).
* **캐시(NFR-2) 참고**: 시제품은 값을 spec dict 식별자로 캐시했는데 current_reuse에서 build 1721회가 났다(평가 루프가 spec을 복사한다). 실제 card는 §10.4대로 spec 로드당 1회 계산해 `ctx`에 두어야 한다 -- 이 측정의 결론(meta·instance 불변)과는 무관하다.
* metric 인자 `supply_nets`의 '레일별 기록'(계획 771행) 코드 변경(`_metric_supply_current`의 기본 이름 집합)은 #17 행 목록에 있어 시제품에 넣지 않았다.
  그 코드는 metric 값만 바꿀 수 있고 meta에는 닿지 않는다(meta를 고치는 대입 0).
