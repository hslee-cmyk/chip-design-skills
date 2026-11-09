# B37 준비 자료 -- topology `ports` 선언을 analog-grammar에 넘기지 않아 운영 경로가 이름 정규식(`HINT_*`)으로 넷을 분류

측정 시점: gate `master` = `7535799`(2026-09-30). 저장소·worktree 쓰기 없음. scratch `C:/g53`(끝나고 삭제):
`git archive HEAD skills/analog-gmid-design/assets skills/analog-grammar workspaces/run_harness.py tools/gates`(pytest용으로 `docs`·`.ai/verification` 추가)로 만든 사본 `base`와 변이 사본 9벌(§3.1).
A = `skills/analog-gmid-design/assets`, SD = `A/stick_diagram.py`, SR = `A/sizing_recipe.py`, AG = `skills/analog-grammar/assets`, NC = `AG/netclass.py`. 줄 번호는 7535799 기준이다.
선행 자료: `prep_b34_b35_grammar.md`(§2.2 인접 관찰이 B37의 출처), `review_phase4_design.md` S8, `draft_phase4_design.v02.md` #47.

---

## 요약

* **정규식 사용처는 NC 한 함수뿐이다.** `HINT_*` 5개(NC 39~43)는 `classify_nets`의 1c(NC 113~124, 게이트 전용 넷 → CLOCK/FEEDBACK/BIAS/INPUT)와 1e(NC 146~150, SIGNAL 넷 → OUTPUT)에서만 쓰인다. 선언(`inputs`/`outputs`/…)을 받은 넷은 1b에서 먼저 확정돼 정규식을 거치지 않는다.
* **운영 경로에서 정규식에 닿는 진입점은 3곳이다.**
  1. SD `load_topology` 8668 → `propose_device_roles_gap_fill`(인자 `inputs`/`outputs` 없음) → `refine_differential_and_mirror_relations` 안의 `classify_nets` 호출 7곳 + 4089. **E-LIB 결과를 바꾸는 유일한 경로다.**
  2. SD `load_topology` 8643 → `propose_vertical_stack_id_gap_fill`: `inputs` 등이 모두 비면 analog-grammar를 아예 부르지 않는다(3292). 차동 다리 간선 기능이 **꺼진 채**로 있다.
  3. SR `resolve_stack_layout` 6572 → `refine_differential_and_mirror_relations(transistors)`: 선언 vsid가 없는 회로에서만 탄다(library 5회로 해당, SPECS 4회로는 해당 없음).
* **9회로 불일치(§2):** 입력 포트 16개 가운데 **정규식이 INPUT으로 맞힌 것은 4개**(`Vip`·`Vim`·`Vinp`·`vin`(pushpull))뿐이다. `vin_p`/`vin_n`/`Vin_p`/`Vin_n`/`Vinn` 11개는 BIAS, common_gate `vin`(소스 입력)은 INTERNAL이다. 출력 포트 10개는 이름으로는 `HINT_OUT`에 모두 걸리지만, 입력 신호가 전파되지 않은 6회로에서는 INTERNAL로 남는다. 포트가 아닌 넷 가운데 `Vom1`·`Vop1`(pilot)은 정규식이 늘 OUTPUT으로 만든다. `O1`(two_stage 둘)·`OUT`(two_stage_ota_sf)은 선언으로 신호가 전파된 **뒤에** 정규식이 OUTPUT으로 만든다. `direction`과 `role`은 9/9 일치한다(불일치 0).
* **ports를 넘기면(§3):**
  * `load_topology` meta가 **5/9 회로**에서 바뀐다. 전부 `device_roles` 자동 채움·review 목록이다. ngcc `headroom_role` 4개, sf_pushpull 20개, two_stage_ota_sf 5개가 사라지고, nmcnr review 12 → 10, two_stage_ota review 9 → 7이다.
  * `transistors` 9/9, `run_full_circuit_audit_from_topology` 9/9, **SPECS 4회로 평가는 base와 같다**(current_reuse·folded_cascode는 metric `float.hex`와 sized 해시까지 같고, two_stage_ota·nmcnr은 같은 거부).
  * vsid 경로에도 ports를 넘겨 차동 간선을 켜도 library 결과는 더 바뀌지 않는다(p2 = p1).
  * ports를 넘긴 뒤 정규식을 **전부** 꺼도 결과가 같다(p4 = p1). **library에서는 선언이 정규식을 완전히 대체한다.**
  * `resolve_stack_layout` 경로 3은 SPECS 밖 3회로(ngcc·sf_pushpull·two_stage_ota_sf)에서 그룹이 바뀐다.
* **pytest(gate 설정, phase 2):** ports를 넘긴 사본의 실패 집합은 base와 같다. 기대값이 바뀌는 test는 0이다. `ports` 누락을 거부하게 하면 `ports` 없는 합성 topology를 쓰는 selftest 17곳이 새로 실패한다. 이 픽스처 보강은 test-author 몫이다.
* **이름 바꾸기 불변(red-green의 대표 관찰):** 정규식에 걸리는 넷과 포트 넷의 이름을 중립 이름(`zq<i>`)으로 바꾸면 base는 **3/9 회로**(current_reuse·ngcc·pushpull)의 meta가 바뀐다. ports를 넘긴 사본은 9/9 불변이다.
* **다른 소비자가 있다:** SR `input_referred_offset_pairs`(4481, 4519)가 이미 `ports`를 `direction == "input"`으로 읽는다. MG2(DEC-69)가 지우는 키다. B37에서 role 접근자를 하나 만들어 두 소비자를 함께 바꾸면 MG2의 ports 몫은 키 삭제와 옛 키 거부만 남는다.
* **권고:** B37을 둘로 나눈다.
  * **B37a**(SD·SR만): role 기반 포트 접근자, 운영 진입점 3곳 배선, `direction` 소비자 교체, `ports` 누락 거부. B26-1 뒤, CC-4a 뒤.
  * **B37b**(AG): 라이브러리 함수의 이름 힌트 제거(CLI 경계로 이동). B36(UD-15) 뒤.
  * 진짜 사용자 결정은 §5의 두 가지뿐이다.

---

## 1. 사용처 인벤토리

### 1.1 AG 쪽

| 기호 | 정의(NC) | 쓰는 곳 | 적용 대상 |
|---|---|---|---|
| `HINT_CLK` | 42 | 118 | 1c: D/S로 한 번도 안 나오는 게이트 전용 넷 중 선언 안 된 것 |
| `HINT_FB` | 41 | 119 | 〃 |
| `HINT_BIAS` | 40 | 120 | 〃. 걸리든 안 걸리든 결과가 BIAS라 **결과에 영향 없음**(1c의 기본값이 BIAS, 122) |
| `HINT_INPUT` | 39 | 121 | 〃 |
| `HINT_OUT` | 43 | 148 | 1e: 1d 신호 전파로 SIGNAL이 된 넷 |

* 1b(NC 105~110) 선언은 레일(1a)까지 덮어쓴다. 선언을 만드는 쪽은 레일을 빼고 넘겨야 한다.
* 가정은 `assume`에 `[inferred] … name hint`로 남지만, SD는 반환값 셋째를 전부 `_assume`로 버린다(1078·1318·1450·1719·1897·2264·2403·2497·4089). 운영 경로에서 **정규식이 쓰였다는 사실이 어디에도 보고되지 않는다.**
* AG 자체 문서(`SKILL.md` 46~50, `analyze.py` 16·48~50)는 이름 힌트를 '선언이 없을 때의 가정, 선언하면 사실로 승격'으로 설계했다. CLI 용도로는 맞는 설계다. 문제는 SD가 선언을 가지고도 넘기지 않는 쪽에 있다.

### 1.2 SD → `classify_nets` 호출(모두 `inputs`… 인자를 호출자에게서 받는다)

| SD 함수(def 줄) | 호출 줄 | 받는 입력 | 운영 도달 |
|---|---|---|---|
| `find_idiom_matches`(1061) | 1078 | 호출자 인자 | 아니오 |
| `find_differential_and_mirror_forks`(1287) | 1318 | 〃 | 아니오 |
| `suggest_vertical_stack_composites`(1363) | 1450 | 〃 | 예(아래 경유) |
| `find_verified_differential_and_mirror_relations`(1625) | 1719 | 〃 | 예 |
| `_propose_vertical_stack_ids`(1811) | 1897 | `base_inputs`(승격 전) | 예 |
| `_propose_headroom_roles`(2197) | 2264 | `base_inputs` | 예 |
| `refine_differential_and_mirror_relations`(2317) 내부 `classify` | 2403(전·후 2회) | `cur_inputs`(승격 반복) | 예 |
| 같은 함수 active-load 블록 | 2497 | `cur_inputs` | 예 |
| `propose_device_roles_gap_fill`(3845) | 4089 | `refined["final_inputs"]` | 예 |
| `_propose_gm_id_roles`(2051)·`_propose_L_roles`(2114)·`find_differential_pair_candidates`(1504) | 2090·2167·2418 경유 | `base_inputs`/`cur_inputs` | 예 |
| `audit_theta_root_direction`(3341)·`propose_theta_kcl_gap_fill`(3442) | 3386·3537(`find_idiom_matches`) | 호출자 인자 | 아니오 |

운영 도달 판정은 `prep_b34_b35_grammar.md` §2.1(V7 `before_phase3` 루트)을 그대로 썼다. 그 측정 시점(`cd64170`) 이후 SD와 `skills/analog-grammar`에는 커밋이 없다(`git log cd64170..7535799 -- <두 경로>` 0건). 줄 번호는 7535799에서 다시 확인했다.

### 1.3 운영 진입점(선언을 가진 쪽 → 문법으로 가는 곳)

| # | 진입점 | 줄 | 지금 넘기는 것 | 결과 |
|---|---|---|---|---|
| E1 | SD `load_topology`(8550) → `propose_device_roles_gap_fill` | 8668~8671 | `inputs` 없음 | `refine`의 부트스트랩(차동쌍 후보의 게이트 넷을 입력으로 승격)이 **나중에** 입력을 찾는다. 그런데 `base_inputs`를 쓰는 `_propose_vertical_stack_ids`·`_propose_gm_id_roles`·`_propose_L_roles`·`_propose_headroom_roles`는 **승격 전** 분류, 곧 정규식 분류를 본다(1813~1817 docstring: 의도적으로 base_inputs 사용) |
| E2 | SD `load_topology` → `propose_vertical_stack_id_gap_fill` | 8643~8644 | `inputs` 없음 | 3292 `if inputs or outputs or …:`가 거짓이라 analog-grammar를 부르지 않는다. 차동 다리 간선은 꺼져 있다(docstring 3282 "조용히 건너뛴다") |
| E3 | SR `_build_theta_evaluator` 8060 → `resolve_stack_layout`(6470) 경로 3 | 6572 | `refine(transistors)` | 선언 vsid가 하나도 없을 때만 탄다. docstring 6537~6543이 "ports 파싱은 필요해지면 추가(의도적 축소)"라고 적어 두었다 |

**ports의 다른 소비자**: SR `input_referred_offset_pairs`(4481) 4511~4519. `_load_full_topology_cached`(4833)가 raw `ports`를 싣고, `p.get("direction") == "input"`으로 입력 넷을 고른다. `ports`가 비면 `ValueError`(4513)를 낸다. 저장소 전체 `.py`에서 `ports`의 `direction`을 읽는 엔진 코드는 이곳 하나다(grep, docs/03-analysis 탐색 스크립트 제외).

---

## 2. 9회로: 정규식 분류 vs `ports` 선언

측정: `cmp_classes.py`. 각 회로를 `load_topology`로 읽고 `_to_analog_grammar_devs`를 거친 소자로 `classify_nets(devs)`(= E1의 `base_inputs` 분류, 정규식)와 `classify_nets(devs, 입력 포트, 출력 포트)`(선언)를 비교했다. 입출력 구분은 `role`의 `_` 토큰에 `input`/`output`이 있는지로 읽었다. library의 role 어휘는 `single_ended_input`, `differential_input_p`, `differential_input_n`, `single_ended_output`, `differential_output_p`, `differential_output_n` 6개가 전부다. `direction`과 role은 9/9에서 모순이 없다.

### 2.1 포트 넷

| 회로 | 포트(role) | 단자 | 정규식 결과 | 선언 결과 | 불일치 |
|---|---|---|---|---|---|
| common_gate_amplifier | `vin`(se_in) | D,S | INTERNAL | INPUT | **예**(소스 입력이라 게이트 전용 규칙 1c 밖) |
| 〃 | `vout`(se_out) | D | INTERNAL | OUTPUT | **예**(신호 미전파) |
| current_reuse_telescopic_ota | `Vip`/`Vim`(diff_in) | G | INPUT | INPUT | 아니오 |
| 〃 | `Vop`/`Vom`(diff_out) | D | OUTPUT | OUTPUT | 아니오 |
| folded_cascode | `vin_p`/`vin_n` | G | **BIAS** | INPUT | **예** |
| 〃 | `out` | D | INTERNAL | OUTPUT | **예** |
| ngcc_3stage_ff | `Vinp` | G | INPUT | INPUT | 아니오 |
| 〃 | `Vinn` | G | **BIAS** | INPUT | **예**(`v?in[pm]?`에 `n`이 없다 -- 한 쌍의 반쪽만 맞는다) |
| 〃 | `Vout` | D | OUTPUT | OUTPUT | 아니오 |
| nmcnr_amplifier | `Vin_p`/`Vin_n` | G | **BIAS** | INPUT | **예** |
| 〃 | `Vout` | D | INTERNAL | OUTPUT | **예** |
| pushpull_follower_buffer | `vin` | G | INPUT | INPUT | 아니오 |
| 〃 | `vout` | S | OUTPUT | OUTPUT | 아니오 |
| sf_pushpull_output_opamp | `vin_p`/`vin_n` | G | **BIAS** | INPUT | **예** |
| 〃 | `vout` | S | INTERNAL | OUTPUT | **예** |
| two_stage_ota | `vin_p`/`vin_n` | G | **BIAS** | INPUT | **예** |
| 〃 | `OUT` | D | INTERNAL | OUTPUT | **예** |
| two_stage_ota_sf | `vin_p`/`vin_n` | G | **BIAS** | INPUT | **예** |
| 〃 | `vout` | D,S | INTERNAL | OUTPUT | **예** |

입력 포트 16개 중 정규식이 맞힌 것 4개, 출력 포트 10개 중 OUTPUT으로 끝난 것 4개(나머지는 이름은 맞지만 1e가 SIGNAL 넷에만 적용된다).

### 2.2 포트가 아닌 넷

| 회로 | 넷 | 정규식 | 선언 적용 후 | 비고 |
|---|---|---|---|---|
| current_reuse | `Vom1`, `Vop1` | OUTPUT(`HINT_OUT`) | OUTPUT(`HINT_OUT` 그대로) | 포트 아님(1단 출력). 선언만 넘겨서는 없어지지 않는 잔여 정규식 |
| two_stage_ota | `O1` | BIAS | **OUTPUT**(`HINT_OUT`) | 선언으로 신호가 전파되자 정규식이 새로 발동한다 |
| two_stage_ota_sf | `O1`, `OUT` | BIAS | **OUTPUT**(`HINT_OUT`) | 〃. `OUT`은 이 회로에서 포트가 아니다(포트는 `vout`) |
| 각 회로 | `VNBias*`·`Vbias*`·`VB1~5`·`bias`·`bias3`·`vb1`·`vb2` 등 | BIAS(`HINT_BIAS`) | BIAS | 결과가 기본값과 같아 무영향 |
| 각 회로 | 신호 경로 내부 넷(`Vg7`, `X`, `Y`, `ND`, `NX`, `NodeC`, `N1`…, `D3`) | BIAS 또는 INTERNAL | SIGNAL | 정규식이 아니라 **입력 오분류의 전파 결과**(입력이 BIAS면 1d 전파가 시작되지 않아 1e2가 BIAS로 굳힌다) |

`HINT_FB`·`HINT_CLK`에 걸리는 넷은 library에 없다.

### 2.3 운영 경로가 실제로 쓰는 분류

`refine`의 부트스트랩은 차동쌍 후보의 게이트 넷을 입력으로 승격한다(`refine_cmp.py` 실측, base):

| 회로 | base 승격 | ports를 넘긴 뒤 승격 |
|---|---|---|
| current_reuse | `Vip`, `Vim`, `Voc`, `Voc_des` | `Voc`, `Voc_des`(CMFB 2차 입력, 포트 아님) |
| folded_cascode, nmcnr, two_stage_ota(_sf), sf_pushpull, ngcc | 두 입력 포트 | 없음 |
| common_gate, pushpull | 없음(차동쌍 아님) | 없음 |

그래서 `final_inputs`를 쓰는 분류(2403 후반, 2497, 4089)는 base에서도 대부분 선언과 같다. 차이는 **승격 전 `base_inputs`를 쓰는 4함수**와 common_gate·pushpull(승격할 게 없어 정규식에 그대로 기댐)에서 난다.

---

## 3. 변이 실측

### 3.1 사본

| 사본 | 변경 |
|---|---|
| base | 원본 |
| p1 | `load_topology`가 `ports`에서 role로 `_port_inputs`/`_port_outputs`를 만들어 `propose_device_roles_gap_fill`에 넘김(E1) |
| p2 | p1 + E2(`propose_vertical_stack_id_gap_fill`)에도 넘김 |
| p3 | p1 + `HINT_INPUT`·`HINT_OUT` 무력화(NC) |
| p4 | p3 + `HINT_BIAS`·`HINT_FB`·`HINT_CLK` 무력화(정규식 전부 끔) |
| p5 | p2 + p4 |
| p6 | p1 + 게이트 전용이고 입력 포트·레일이 아닌 넷을 전부 `biases`로 선언 |
| p7 | p6에서 수동소자·이상원 단자를 뺌(계획 N3.2-1 교류접지 (2)의 제외 조건 그대로) |
| p8 | p7 + `ports`가 없으면 `ValueError`(pytest 영향 측정용) |
| c1 | 대조군: ports를 넘기지 않고 정규식만 전부 끔 |

측정 스크립트 `measure.py <사본>`: library 9회로 `load_topology`(transistors 해시, meta 키별 해시와 전문), `run_full_circuit_audit_from_topology`, `run_harness.SPECS` 4회로 `_library_sized_contexts._evaluate_once`(metric `float.hex`, sized 해시, 거부·예외 전문). 케이스마다 JSONL에 append했다. 비교 `compare.py`.

### 3.2 결과 (base 대비)

| 관찰 | p1 | p2 | p3 | p4 | p5 | p7 | c1 |
|---|---|---|---|---|---|---|---|
| `load_topology` transistors | 9/9 같음 | 같음 | 같음 | 같음 | 같음 | 같음 | 같음 |
| `load_topology` meta | **5회로 다름** | p1과 같음 | p1과 같음 | p1과 같음 | p1과 같음 | p1과 같음 | **3회로 다름**(current_reuse·ngcc·pushpull, 자동 채움 증가) |
| audit 9회로 | 같음 | 같음 | 같음 | 같음 | 같음 | 같음 | 같음 |
| SPECS 4회로 평가 | 같음 | 같음 | 같음 | 같음 | 같음 | 같음 | 같음 |

p2~p5·p7은 p1과 **모든 케이스가 같다**(케이스별 레코드 비교, 경로 문자열 제외).
p6은 current_reuse에서 p1과 다르다. `Voc`/`Voc_des`(수동소자 R1/R2 단자, CMFB 감지 넷)를 BIAS로 선언하면 NC 1b의 적용 순서(inputs 뒤 biases)가 승격 입력을 BIAS로 덮어쓴다. 그 결과 review 목록이 바뀌고(`M36a`–`M7` 매칭쌍 등), current_reuse θ\* 평가가 `ValueError`(`optimize_full_circuit_budget() 실행 전 review가 필요하다`)로 바뀐다. → '게이트 전용 비포트 = 바이어스'를 SD에서 직접 만들려면 N3.2-1 제외 조건을 빠짐없이 지켜야 하고, 틀리면 파일럿이 깨진다(§4.3 기각 근거).

p1의 meta 차이(5회로, 전부 `device_roles` 자동 채움·review 목록. vsid·matching·symmetry는 불변):

| 회로 | 바뀐 키 | 내용 |
|---|---|---|
| ngcc_3stage_ff | `device_roles`, `_device_roles_autofilled` | `headroom_role` 4개 사라짐: M1 `cascode`, M4·M6B·M7 `mirror` |
| sf_pushpull_output_opamp | 〃 | `headroom_role` 20개 사라짐: M1·M2(입력쌍) `cascode`, M5~M22 18개 전부(`cascode`/`mirror`) |
| two_stage_ota_sf | 〃 | 5개 사라짐: M1·M2 `cascode`, M4·M6 `mirror`, M8 `cascode` |
| nmcnr_amplifier | `_device_roles_gap_fill_review_needed` | 12 → 10. M201·M301의 'compensation.stage_devices 소속 gm_id_role' 안내 2건 사라짐 |
| two_stage_ota | 〃 | 9 → 7. M4 `headroom_role` 충돌(선언 `cascode` vs 제안 `mirror`) 사라짐, M6 안내 사라짐 |

원인(`refine_cmp.py`, `refine`을 base_inputs 없이/포트로 직접 비교): 입력 포트가 BIAS로 분류되면 입력쌍은 `assign_roles`에서 `CASCODE`/`CURRENT_SOURCE`가 되고, 신호 경로 전체가 BIAS 트리로 굳는다(§2.2 마지막 행). `_propose_headroom_roles` 규칙(2197 docstring)은 `AMPLIFYING`(게이트가 신호)을 `None`으로 둔다. 선언을 넘기면 입력쌍과 신호 경로 소자가 `AMPLIFYING`이 되어 제안이 사라진다. 이 규칙이 보정된 조건(파일럿 37/37)은 **입력이 INPUT으로 분류된 상태**였다(파일럿 `Vip`/`Vim`은 정규식에 걸린다). 곧 base에서 입력쌍 제안이 나오는지 여부는 **넷 이름이 정규식에 걸리는지**로 갈린다.
* folded_cascode·nmcnr·two_stage_ota에서도 `refine`의 `headroom_role_candidates`·`vertical_stack_id_candidates`가 바뀐다. 하지만 선언값이 이미 있거나 충돌로 걸러져 meta에는 두 review 항목만 남는다.

### 3.3 E3 (`resolve_stack_layout` 경로 3)

`rsl_cmp.py`: 선언 vsid가 없는 5회로(common_gate·ngcc·pushpull·sf_pushpull·two_stage_ota_sf)가 이 경로를 탄다. SPECS 4회로는 모두 vsid가 있어 타지 않는다. ports를 넘기면:

| 회로 | base 그룹 | ports 그룹 |
|---|---|---|
| ngcc_3stage_ff | `[M0, M1, M2]` 한 그룹 | `[M0]`, `[M1, M2]` |
| sf_pushpull_output_opamp | `[M17, M18]`, `[M19, M20]` | 네 개로 분리 |
| two_stage_ota_sf | `[M8, M9]` | `[M8]`, `[M9]` |
| common_gate, pushpull | 같음 | 같음 |

SPECS 밖이라 평가 결과로는 드러나지 않는다. 이 세 회로를 사이징 대상에 올리는 시점(6b 이후)에 레이아웃 그룹이 달라진다.

### 3.4 이름 바꾸기 불변 (`rename_inv.py`)

회로마다 원래 `HINT_*` 중 하나에 걸리는 넷과 포트 넷을 전부 `zq<i>`로 바꾼 topology를 scratch에 만든다. `load_topology` meta를 역변환(파생 문자열 `…_fold` 안의 이름 포함)해서 원본과 비교했다.

| 사본 | 불변 회로 | 깨지는 회로 |
|---|---|---|
| base | 6/9 | current_reuse(M1a·M1b·M4a·M4b·M15·M16·M25·M26 `headroom_role` 추가), ngcc(M2·M10·M8·M13·M14 추가), pushpull(M1~M4 `cascode` 추가) |
| p1 | **9/9** | 없음 |
| p7 | 9/9 | 없음 |

이 실측은 '이름이 정규식을 벗어나는' 방향만 쟀다. 반대 방향(`vin_p` → `Vip`)은 folded·nmcnr·sf_pushpull·two_stage 계열 5회로를 깬다고 예상되지만 재지 않았다(§3.2 p1 차이가 그 방향의 결과와 같은 종류다).

### 3.5 pytest (판정 실행 설정 `tools/gates/pytest_gate.ini`, `--gmid-phase=2`)

실행: `python -m pytest -c <사본>/tools/gates/pytest_gate.ini --rootdir=<사본> --confcutdir=<사본> --gmid-phase=2 -p no:cacheprovider`. 사본 셋(base·p7·p8)을 병렬로 돌렸다.

| 사본 | FAILED+ERROR | base 대비 |
|---|---|---|
| base | 43 | -- |
| p7 | 43 | **같은 집합**(새 실패 0, 고쳐진 것 0) |
| p8(누락 거부) | 60 | **새 17**: `test_selftest_sizing_recipe.py` 15(s003·s011·s012·s036~s043·s045·s050·s052·s053), `test_selftest_stick_diagram.py` 2(s071·s125). 전부 `ports` 없는 합성 topology를 tmp 파일로 써서 `load_topology`를 부르는 selftest다 |

* base 43건은 **scratch 사본의 환경 결함**이다. `tools/migrate` 등 사본에 없는 경로를 찾는 tooling test 38, ts6·probe_dup 4, design_report 1이다. 실제 gate 실행(795 passed)과는 관계가 없고, base·p7이 같은 집합이라 비교에는 쓸 수 있다. 다만 이 43개 test는 이번 측정에서 **판정하지 못했다**.
* p1은 pytest로 돌리지 않았다. p7은 p1에 `biases` 선언만 더한 것이고 library 결과는 p1과 같다(§3.2).
* 결론:
  * ports 전달 자체는 기존 test의 기대값을 바꾸지 않는다. 따라서 **기준 약화(DEC-40) 대상이 아니다**(E-LIB meta 차이 5회로는 어떤 test도 고정하지 않는다).
  * 누락 거부(C3)는 selftest 합성 픽스처 17곳에 `ports`를 넣는 **test-author 작업**을 부른다. 이것은 기대값 변경이 아니라 입력 픽스처 보강이다. 그래도 test 파일 변경이므로 B37a의 test 커밋에 함께 넣는다. code 커밋과 같은 커밋에 넣으면 안 된다(작성자≠검증자, 계획 §14).

---

## 4. card 모양

### 4.1 분할과 순서

| card | 범위 | 쓰기 주체 | 선행 | 판정 유형 |
|---|---|---|---|---|
| **B37a** `b37-ports-role-wiring` | ① role 기반 포트 접근자 1개 ② E1·E2·E3 배선 ③ SR `input_referred_offset_pairs`의 `direction` 읽기를 접근자로 교체 ④ `ports` 누락·모르는 role 거부 | code-author(SD·SR), test-author(`A/tests/contracts/`) | B34(#45, 같은 def를 고침) → B26-1(#1, `meta["rails"]`) → CC-4a(#6, `SchemaRejectedError`). 셋 모두 `propose_device_roles_gap_fill`·`load_topology`를 건드리므로 **순차 병합** | red-green + E-LIB 차이표 |
| **B37b** `b37-grammar-no-name-hints` | AG `classify_nets` 라이브러리 경로에서 `HINT_*` 제거. 이름 힌트는 `analyze.py` CLI 경계에서 명시 가정으로 만들어 넘기고 `assume`에 보고(B35 prep §3.2 (1)의 레일 처리와 같은 모양) | AG 쓰기 주체(B36이 정함) | **B36(#46, UD-15)** + B37a | red-green(E-LIB 무변화, §3.2 p4 = p1 근거) |

* `draft_phase4_design.v02.md` §3.3의 `B26-2 ─> B37`은 B37a에는 필요 없다. 극성을 쓰지 않고, 레일 소속만 쓴다(B26-1). 파일 충돌 때문에 병합 순서만 이어 두면 된다. B26-2와 B37a 중 어느 쪽이 먼저여도 되지만 **동시 착수는 하지 않는다**(`propose_device_roles_gap_fill` 변이 약 331, §8.4-1 비용).
* **MG2(6a 전)와의 관계:** B37a가 role만 읽고 `direction` 소비자를 0으로 만들어 두면, MG2의 `ports.direction` 삭제는 topology JSON 9개에서 키를 지우는 일과 옛 키 거부 게이트만 남는다. B37a가 `direction`을 읽게 만들면 MG2에서 다시 고쳐야 한다(review S8-3).
* **Phase 3(MOD2/MOD3):** Phase 3 v4 A-3 계산에서 `load_topology`는 MOD3로 간다(구조 자동채움 호출 때문). B37a가 Phase 3 뒤로 가면 MOD3 파일에서 하고, 접근자는 `ports`를 읽는 MOD2(로드·스키마) 쪽에 둔다. Phase 3 이동 card는 해시 동일성 증명이므로 B37a를 앞에 넣을 이유는 없다. Phase 4 레일 묶음에 둔다(#47, pre 아님). SR `input_referred_offset_pairs`는 레지스트리 311행상 `circuit_state_graph.py`(S1 유도 사실) 목적지다.
* **B26-1과의 접점:** E3의 `resolve_stack_layout`은 B26-1이 이미 `rails` 인자를 넣는 함수다. B37a는 같은 방식으로 `ports` 파생값을 인자로 받는다. 값의 출처는 `load_topology` meta다(재계산 금지 -- 아래 C5).

### 4.2 B37a 계약 (test-author가 관찰할 수 있는 것만)

* **C1 이름 바꾸기 불변(대표 관찰, red-green):**
  * library 회로 X에서 포트 넷과 `HINT_INPUT`·`HINT_OUT`에 걸리는 넷을 중립 이름으로 바꾼 topology를 만든다. 두 topology의 `load_topology` meta를 이름 역변환 후 비교하면 **같아야 한다**.
  * base에서 current_reuse·ngcc·pushpull 3회로가 FAIL(§3.4), 병합본 PASS.
  * 합성 topology만으로도 만들 수 있다: 입력 포트 이름을 정규식에 걸리지 않는 이름(예: `sig_a`/`sig_b`)으로 둔 차동쌍 + 미러 부하. base에서는 입력쌍이 `headroom_role` 제안을 받고, 병합본에서는 받지 않는다(`AMPLIFYING` → `None`, 2197 규칙).
  * B37a 범위의 불변은 **포트 넷과 `HINT_INPUT`에 걸리는 비포트 게이트 전용 넷까지**다. 비포트 SIGNAL 넷에 대한 `HINT_OUT`(§2.2 `Vom1`/`Vop1`/`O1`/`OUT`)과 수동소자 단자 게이트 전용 넷(`Voc`류)에 대한 1c 힌트는 B37b가 닫는다. 계약 문장에 이 경계를 적는다. library에서는 둘 다 결과에 영향이 없다(§3.2 p3·p4 = p1). 그러니 test는 합성 topology로 경계를 고정해야 한다(예: 포트가 아닌 내부 넷 `vo1`이 B37a 뒤에도 OUTPUT으로 분류되는 것은 B37b의 red가 된다).
* **C2 입출력은 role에서 유도:**
  * 접근자가 role 어휘 6개 중 `input` 토큰이 있는 것을 입력으로, `output` 토큰이 있는 것을 출력으로 돌려준다.
  * `direction`을 지운 topology에서도 결과가 같아야 한다(MG2 대비). `direction`과 role이 모순된 topology는 거부하거나 role을 따른다. **기본안은 거부다**. MG2 전까지 두 키가 공존하므로 조용히 한쪽을 고르지 않는다.
  * SR `input_referred_offset_pairs`가 같은 접근자를 쓴다. 관찰: `direction` 키가 없는 합성 topology에서 입력 오프셋 쌍이 base와 같게 나온다(base는 `direction`이 없으면 입력 집합이 비어 쌍이 0개가 되고, 거부하지 않는다. SR 4518~4527 코드 판독이며 실행 실측은 아니다. 이것도 조용한 빈 결과라 base red가 된다).
* **C3 누락 거부:**
  * `ports`가 없거나 비었거나 입력 role이 하나도 없는 topology는 `load_topology`에서 거부한다. CC-4a 뒤면 `SchemaRejectedError`(N3.14 SCHEMA_REJECTED), 전이면 `ValueError`(메시지에 `ports`와 DEC-62)다.
  * 모르는 role도 거부한다.
  * 조용한 정규식 폴백으로 돌아가지 않는다(review S8-1). 판정기 자기 점검: 누락 시 정규식 분류로 계속 가는 합성 구현을 넣으면 test가 FAIL해야 한다.
  * 영향 범위: library 9/9는 `ports`를 가진다. `_TEMPLATE`은 `ports: null`이지만 netlist가 설명 문자열이라 지금도 로드 전에 실패한다. test 픽스처 영향은 §3.5.
* **C4 배선(만들면 배선):** 접근자의 실인자가 운영 진입점 E1·E2·E3에 전부 닿는다.
  * E2를 켜면 `propose_vertical_stack_id_gap_fill`의 차동 간선이 운영에서 처음 동작한다. library 결과는 불변이다(p2 = p1).
  * E3는 `resolve_stack_layout`에 인자를 추가한다. `_build_theta_evaluator` 8060이 meta에서 넘긴다.
  * 관찰: 합성 topology 두 개(선언 vsid 없음, 입력 이름만 다름)의 `resolve_stack_layout` 그룹이 같아야 한다.
* **C5 재계산 금지:** 포트 파생값은 `load_topology`에서 한 번 만들어 meta에 싣는다(키 이름은 interface card에서 정함, 예: `meta["port_nets"]`). SR은 `_load_full_topology_cached` 경로에서 raw `ports`를 다시 해석하지 않고 같은 접근자를 쓴다. 새 캐시는 만들지 않는다.
* **C6 동작 보존:**
  * SPECS 4회로 평가는 base와 같다(§3.2 p1, metric `float.hex`·sized 해시).
  * audit 9/9도 같다.
  * E-LIB meta는 §3.2 표 5회로만 달라진다. 이것은 기대 차이로 적는다. 달라지는 필드는 전부 `_device_roles_autofilled`/review 목록이고, 사람이 선언한 값은 바뀌지 않는다.
* **판정 유형과 oracle:**
  * red-green. C1·C3는 구성 oracle이고, C6는 auditor의 base 실행 결과다.
  * E-LIB 차이는 기대 차이 목록(위 표)과 대조한다. 표에 없는 차이가 나오면 FAIL이다.
* **쓰기 경로:**
  * SD·SR: code-author
  * 합성 topology·test: test-author(`A/tests/contracts/`)
  * SD 6537~6543·3276~3283·3855~3857 docstring("ports 파싱은 필요해지면", "`inputs=`를 안 주면 조용히 건너뛴다"): code-author
  * 레지스트리(접근자 행 신설, 311행 비고): code-author

### 4.3 기각한 안

| 안 | 기각 이유 |
|---|---|
| `direction`을 읽는다 | MG2가 지우는 키다(계획 N3.16 786행). 6a 전에 다시 고쳐야 한다 |
| ports가 없으면 정규식으로 폴백 | 조용한 폴백. 계획 §3.2 P1, review S8-1 |
| SD에서 '게이트 전용 비포트 넷 = 바이어스'를 만들어 `biases`로 넘긴다(p6·p7) | p6이 보이듯 N3.2-1 제외 조건(수동소자·이상원 단자)을 하나라도 빠뜨리면 파일럿이 깨진다. 제대로 만든 p7은 library에서 p1과 같아서 얻는 것이 없다. 게다가 교류접지 집합 판정은 6a GB0/S1의 몫이라, SD에 두 번째 정본을 만들게 된다(DUP). 정규식 제거는 AG에서 하는 것이 맞다(B37b) |
| B37b를 SD에서 넷 이름을 바꿔 우회 | B35 prep §3.2 (2) 기각 이유와 같다(역변환 누락 위험, AG는 여전히 이름 기반) |
| E1만 배선(초안 #47 문구) | E3가 같은 문제를 가진 운영 진입점이다(docstring이 스스로 '의도적 축소'라고 적음). E2는 `inputs` 없음 = 기능 꺼짐이다. 하나만 고치면 이름 의존이 다른 입구로 남는다 |

---

## 5. 사용자 결정

**결정이 아닌 것(원칙 기본안):**
* 선언이 정규식을 이긴다. `ports`는 사용자가 확인한 선언이다(DEC-35, 파일별 `_comment`의 '사용자 확정'). §2의 불일치는 '어느 쪽이 맞나'의 문제가 아니라 정규식의 오분류다. 입력 11개가 BIAS가 된 것은 이름 표기(`_p`, `Vinn`) 때문이지 회로 해석의 차이가 아니다.
* role 기반, 누락 거부, E1~E3 전부 배선, B37a/B37b 분할과 순서.
* role 어휘 6개를 닫힌 목록으로 두는 것: library 실측값 그대로다. 계획 N3.16 786행에 어휘를 적는 개정은 오케스트레이터가 계획 표 개정 절차(plan_tables 승인)로 올린다. 새 결정이 아니라 기존 행의 빈칸 채우기다.

**사용자 몫(회로 해석):**
1. **§3.2의 자동 채움 소실 3회로(ngcc 4개, sf_pushpull 20개, two_stage_ota_sf 5개 `headroom_role`)와 §3.3의 레이아웃 그룹 변화 3회로를 받아들일지.**
   * base 제안은 입력을 BIAS로 오분류한 결과다. 예: sf_pushpull `M1`/`M2` 입력쌍 `cascode`, 신호 경로 소자의 `mirror`/`cascode`, ngcc 테일 `M0`과 입력쌍 `M1`/`M2`를 한 수직 그룹으로 묶은 것.
   * 그런데 사람이 선언한 4회로에서는 입력쌍 `headroom_role`이 `cascode`다(current_reuse·folded·nmcnr·two_stage_ota). 그러니 B37a 뒤 입력쌍 제안이 `None`이 되는 것은 **`_propose_headroom_roles` 규칙이 입력쌍을 다루지 않는 빈칸**이 드러나는 것이다. 틀린 값이 새로 생기는 것은 아니다.
   * 세 회로 모두 SPECS 밖이라 지금의 평가 수치는 그대로다. 이 세 회로의 `headroom_role`·수직 그룹을 무엇으로 볼지(사람 선언으로 채울지, 규칙을 넓힐지)는 회로 해석이라 사용자 몫이다. **B37a 착수 조건이 아니다.** E-LIB 기대 차이표를 승인 기록에 붙이고, 세 회로의 선언 보강은 6a의 ports·역할 제안표(DEC-35 절차)로 넘기는 것이 기본안이다.
   * 기준 약화(DEC-40) 여부: §3.5에서 기대값이 바뀌는 test가 0이었다. 따라서 약화가 아니며, 이 항목은 승인 사안이 아니라 **확인** 사안이다.
2. **current_reuse의 `Vom1`/`Vop1`(1단 출력, 포트 아님)이 B37b 뒤 OUTPUT → SIGNAL로 바뀌는 것.** library 결과에는 영향이 없다(p3 = p1). 다만 `_reaches_output`(idioms 81~95, `m_cascode` 방향 판정)이 '출력'을 포트만으로 볼지는 회로 해석의 경계다. 기본안은 포트만(선언만이 사실)이고, 확인만 받는다.

대기 중인 결정 UD-15(analog-grammar 소속)는 B37b의 선행 조건이지만 새 결정은 아니다.

---

## 부록 -- 명령과 원자료 (scratch 삭제 전 기록)

* 사본: `git -C <repo> archive HEAD <경로들> | tar -x -C C:/g53/base`. 변이는 `make_variants.py`(p1~p5, c1)가 만들었고, p6~p8은 인라인 스크립트로 문자열을 치환했다. 치환 전에 대상 문자열이 정확히 1회 나오는지 assert로 확인했다.
* p1 핵심 삽입(SD 8641 뒤): `_ports_decl = {k: v for k, v in (data.get("ports") or {}).items() if not k.startswith("_") and isinstance(v, dict)}`. 입력 = role의 `_` 토큰에 `input`이 있는 넷, 출력 = `output`이 있는 넷. `propose_device_roles_gap_fill(..., inputs=_port_inputs, outputs=_port_outputs)`.
* `cmp_classes.py`: §2 표. `measure.py <사본>` / `run_all.py`: §3.2. `compare.py`: 차이. `refine_cmp.py`: §2.3·§3.2 원인. `rsl_cmp.py`: §3.3. `rename_inv.py <사본>`: §3.4. `run_pytest.py`: §3.5.
* 모든 측정 스크립트는 import한 모듈 경로가 해당 사본 루트 아래인지 assert로 확인했다(`sd.__file__`, `netclass.__file__`, `run_harness.__file__`).
