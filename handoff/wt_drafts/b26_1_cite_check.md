# draft_b26_1.spec.md 줄 인용 실측 -- gate master `6c724de` 기준 (2026-10-06)

`draft_b26_1.spec.md`는 고치지 않았다. 아래 교체안을 적용할지는 오케스트레이터가 정한다.

**측정 방법**
* 모래상자 `C:/g340`에서 했다(TMP/TEMP 포함, 측정 뒤 삭제). 저장소는 `git clone -c core.autocrlf=false`로 복제해 읽기만 했다.
* 측정 스크립트는 `C:/g340/cite_check.py`·`cite_check2.py`다(삭제됨).
* 인용마다 다음을 쟀다:
  * 주장 rev에서 그 줄의 글과 그 줄을 감싸는 def(AST).
  * `6c724de`로 가는 줄 대응. kit_line_shift를 쓰지 않고 `difflib.SequenceMatcher(autojunk=False)`로 따로 계산했다.
  * 대응된 줄의 글.
* `unavailable_reason` 소비처는 `git grep`으로 7535799와 6c724de에서 다시 쟀다.

**엔진 blob**(`git rev-parse <rev>:<path>`)

| rev | SR | SD | 줄 수 SR / SD |
|---|---|---|---|
| cd64170 | 97a6c7bb | dbd35acd | 12015 / 9035 |
| 7535799 | 97a6c7bb | dbd35acd | 12015 / 9035 |
| dd60db6 · 7243f28 · 2d58fd8 | 97a6c7bb | ca46b5cd | 12015 / 9024 |
| 2183f2e | 2a7a1a04 | 9993047c | 12014 / 9010 |
| **6c724de (gate master)** | 2a7a1a04 | 9993047c | 12014 / 9010 |

* gate master `6c724de`의 엔진은 `2183f2e`와 같다. 그래서 '`2183f2e` 줄'이라고 적은 인용은 gate master 줄과 같다.
* cd64170과 7535799는 SR·SD 모두 같다. card가 'cd64170 줄'과 '7535799 줄'을 섞어 써도 번호 값은 같다.
* SR은 cd64170 → 2183f2e에서 6510~6512(docstring 3줄 → 2줄)만 바뀌었다. 그래서 6512 앞 SR 줄은 번호가 그대로다.

## 결론 요약

| 행 | 인용이 주장하는 rev | 주장 rev 기준 | gate master 기준 | 판정 |
|---|---|---|---|---|
| 35~36(머리 문장) | 표 = 7535799 / 2183f2e, b1 대비 "2~6줄" | 맞다 | -- | 고칠 것 없음 |
| 40~44(표)·46~47·52·54 | 7535799 / 2183f2e 병기 | 맞다(17쌍) | 2183f2e 값 = gate master 값 | 고칠 것 없음 |
| 65~67(범위 밖) | 표시 없음. card 머리 15행 기본값 cd64170. 바로 위 머리(35~36·38)는 7535799 / 2183f2e 병기 | cd64170으로 읽으면 맞다. **2183f2e로 읽으면 SD 11곳이 다른 코드다** | SD −5, SR 그대로 | **모호, 낡음.** 병기 추가를 권함(아래 1) |
| 71 | cd64170(SR), 2183f2e 병기 | 맞다(8 + 8) | 맞다 | 고칠 것 없음 |
| 77 | card 기본값 cd64170(71행 '줄은 cd64170'을 이어 받음) | 맞다 | SD 3559·3561·3719 → 3534·3536·3694, SR 3950 그대로 | **gate master 기준 낡음.** 병기 추가를 권함(아래 2) |
| 499~501 | '작성 전 실측' 머리 494행 `(cd64170, 2026-09-30 …)` | 맞다(SD 14, SR 2) | 16행의 2183f2e 목록과 1:1(3042는 P9가 없앰) | 측정 기록이라 번호는 그대로 둔다. 안내 한 줄만 제안(아래 3) |
| 542 | `git grep` 7535799 | 번호는 맞다. **SD 3527(`propose_theta_kcl_gap_fill` docstring) 하나가 목록에서 빠졌다** | SD 3506·3510·3515·3943만 남음. 두 docstring 언급은 B34가 지움 | 빠진 줄을 넣고, gate master 값을 병기하기를 권함(아래 4) |

다음 경우는 없다: 주장한 rev에서 번호가 틀린 인용, 그리고 '2183f2e 줄'이라 적었는데 실제로는 다른 판의 번호인 인용.
낡은 인용은 두 종류다. 하나는 gate master 기준으로 낡은 cd64170 인용이다(65~67, 77, 499~501). 다른 하나는 한 줄이 빠진 7535799 목록이다(542).

---

## 실측 근거(행별)

### 35~36·40~47·52·54 -- 표와 병기(7535799 / 2183f2e)

7535799 줄의 글 → 6c724de 대응 줄 = 표의 2183f2e 값. 대응 줄의 글이 같다.

| 표 값 7535799 / 2183f2e | 글(두 판 같음) | 감싸는 def |
|---|---|---|
| 2400~2401 / 2394~2395 | `if netclass is None:` / `return None, None` | `classify`(refine_… 안) |
| 2410~2411 / 2404~2405 | `if cls_before is None:` / `return None` | `refine_differential_and_mirror_relations` |
| 2440~2441 / 2434~2435 | `if relations is None:` / `return None` | 같음 |
| 2420 / 2414 | `if candidates is None:` | 같음 |
| 4071~4073 / 4046~4048 | `_static_ref_roles = (` … `if _netclass_lcmf is not None else ())` | `propose_device_roles_gap_fill` |
| 3966~3970 / 3941~3945 | `if refined is None:` … `"unavailable_reason": "analog-grammar를 import할 수 없어 …"` … `"None을 반환)."}` | 같음 |
| 2495 / 2489 | `if _netclass_al is not None:` | refine_… |
| 4087 / 4062 | `if _idioms_lcmf is not None:` | propose_… |
| 52행 2183f2e 3907~3908 · 2343~2344 | "…`ImportError`를 던진다 (`… is None` 분기는 도달 불가 -- 삭제는 B26-1/B35/백로그)." | propose_… · refine_… docstring |

* 7535799의 같은 docstring(3932~3933, 2349~2350)은 2183f2e에서 바뀐 줄이다. 대응이 없다(B34가 고침). 52행이 '`2183f2e` 줄'이라 밝힌 것이 맞다.
* **36행 "예전 모의 base `b1` 줄은 … 2~6줄 더 당겨졌다"**: b1 → 2183f2e 차이를 쟀다.
  * refine_… 사이트(2396·2397·2406·2407·2416·2436·2437·2491): 2.
  * propose_… 사이트(4052·4054·4068·3947·3951): 6.
  * 따라서 2~6이 맞다.
* (참고, 요청 밖) 16행:
  * 2183f2e 사이트 줄 SD 1014·1570·1612·2090·2166·3130·3235·3967·4146·4282·4298·4345·4367과 SR 2207·4293은 글이 모두 레일 판정이다(`_RAIL_NETS`·`seeds`·`rails =`). 맞다.
  * b1 줄 1571·…·4373 → 2183f2e의 차이는 1,1,2,2,3,3,6,6,6,6,6,6이다("1014 말고 전부 1~6줄"). 맞다.

### 65~67 -- 범위 밖(다른 card)

cd64170(= 7535799) 줄을 6c724de로 대응한 결과다(글은 두 판에서 같다).

| 인용 | cd64170 글(def) | 6c724de |
|---|---|---|
| SD 1222 | `if en in _RAIL_NETS:`(`_trace`) | 1217 |
| SD 1233 | `start_names = [… if entry_net(t) == "vdd"]`(`trace_vdd_to_gnd_branches`) | 1228 |
| SD 1234 | `branches = [{… "gnd" if term == "gnd" …}]` | 1229 |
| SD 1270 | `if en in _RAIL_NETS:`(`_trace`) | 1265 |
| SD 1281 | `start_names = [… == "gnd"]`(`trace_gnd_to_vdd_branches`) | 1276 |
| SD 1282 | `branches = [{… "vdd" if term == "vdd" …}]` | 1277 |
| SD 1355 | `down_chains = [… == "gnd"]`(`find_differential_and_mirror_forks`) | 1350 |
| SD 1357 | `up_chains = [… == "vdd"]` | 1352 |
| SD 1557 | `("vdd_to_gnd", composites_down, "gnd"),`(`find_differential_pair_candidates`) | 1552 |
| SD 1558 | `("gnd_to_vdd", composites_up, "vdd")):` | 1553 |
| SD 1737 | `for direction, terminal in (("vdd_to_gnd", "gnd"), …`(`find_verified_differential_and_mirror_relations`) | 1732 |
| SR 3728·3790 | `rail_hi=_DEFAULT_RAIL_HI, rail_lo=_DEFAULT_RAIL_LO`(`propagate_node_voltages`·`derive_vsb_from_nodes`) | 3728·3790 |
| SR 4361 | `rails = set(spec.get("supply_nets") or ("vdd", "VDD"))`(`_metric_supply_current`) | 4361 |
| SR 4626 | `rail_v = ctx.spec["vdd"] if spec["rail"] == "vdd" else 0.0` | 4626 |
| SR 4650~4653 | `_metric_battery_centering_deviation` 본문 | 4650~4653 |
| SR 4086 · 4991 | `fixed = {"gnd": 0.0}`(`build_ac_network` · `_full_circuit_response`) | 4086 · 4991 |

* 같은 SD 번호를 2183f2e로 읽으면 다른 줄이다. 예:
  * 1222 = `out = []`, 1233 = 빈 줄, 1234 = `def trace_gnd_to_vdd_branches(…)`
  * 1355 = `+ _classify_forks(up_chains, "gnd_to_vdd")}`, 1557 = `groups[signature(b)].append(…)`, 1737 = `for b in complete:`
* 이 문단은 35~36행 "줄 번호는 7535799와 2183f2e"와 38행 표 머리 `줄(7535799 / 2183f2e)` 아래에 있다. 그런데 값은 하나뿐이다(cd64170 = 7535799 값).
* 정리하면, 15행의 card 기본값(cd64170)으로 읽으면 맞다. 하지만 바로 위 머리를 따르는 독자에게는 낡은 인용이다(재검토 S-B가 짚은 11곳).

### 71 -- SR `_hr_*`·`_build_theta_evaluator`

* cd64170 7282·8003·8091·6881·6886·6920·6931·6948은 글과 def가 맞다(`_hr_resolve_vertical_group`, `_rail_nets = frozenset({"vdd", "gnd", "vss"})`, `rail_nets=_rail_nets, …`, `_rail_nets = topo.rail_nets`, `open_nets`·`sib_nets`).
* 6c724de 대응은 7281·8002·8090·6880·6885·6919·6930·6947이다. 행에 적힌 2183f2e 값과 8/8 같다.

### 77 -- SR 3950, SD 3559·3561·3719

* SR 3950 `rails = set(_DEFAULT_RAIL_HI) | set(_DEFAULT_RAIL_LO)`(`node_pole_estimate`). 6c724de에서도 3950이다.
* SD는 cd64170 → 6c724de로 이렇게 대응한다(글이 같다):
  * 3559 `if t.source not in _RAIL_NETS:` → 3534
  * 3561 `if t.drain not in _RAIL_NETS:` → 3536
  * 3719 `if by_name[n].source in _RAIL_NETS or …` → 3694
  * 셋 다 `propose_theta_kcl_gap_fill` 안이다.
* kit_line_shift r2가 낸 패치 3건(3559·3561·3719 → 3534·3536·3694)과 값이 같다. 다만 그 패치는 번호를 **바꿔 쓴다**. 그러면 15행 "줄 번호는 cd64170"·71행 "줄은 cd64170" 아래에 2183f2e 번호가 홑으로 들어간다. 71행처럼 병기하는 쪽이 card 규칙과 맞다(아래 2).

### 499~501 -- '작성 전 실측' 1

* 494행 머리 `(cd64170, 2026-09-30. …)` 아래의 측정 기록이다. cd64170 글과 def가 맞다:
  * SD: 1014 `find_matching_candidates` · 1575 `find_differential_pair_candidates` · 1617 `_diff_pair_layer1_groups` · 2096 `_propose_gm_id_roles` · 2172 `_propose_L_roles` · 3042 `kcl_series_union` · 3148 `_kcl_and_matching_edges` · 3253 `audit_vertical_stack_id_vs_kcl` · 3992·4171·4307·4323·4370·4392 `propose_device_roles_gap_fill`
  * SR: 2207 `true_current_mirror_groups` · 4293 `_metric_kcl_residual`
* 6c724de 대응은 1014·1570·1612·2090·2166·(3042 없음 -- P9가 지운 줄)·3130·3235·3967·4146·4282·4298·4345·4367, SR 2207·4293이다. 16행의 2183f2e 목록과 1:1로 같다.

### 542 -- `unavailable_reason` 소비처

* `git grep -n unavailable_reason 7535799 -- skills workspaces tools docs/01-plan docs/02-design` 결과는 SD 3527·3531·3535·3540·3933·3968이다.
  * 3527은 `propose_theta_kcl_gap_fill` docstring 끝 줄 `` `unavailable_reason`.""" ``이다. **542행 목록에 없다.**
  * 나머지 5개는 행의 목록·글과 맞다.
* 같은 grep을 6c724de에서 돌리면:
  * SD는 3506·3510·3515(`propose_theta_kcl_gap_fill`)와 3943(정의)뿐이다. 두 docstring의 언급(7535799 3527·3933)은 B34가 `ImportError` 서술로 고쳐 없다.
  * skills 아래에 `tests/contracts/test_b34_grammar_explicit.py:348`이 새로 잡힌다. 이것은 판정기 자기 점검용 가짜 반환값 `lambda *a: {"unavailable_reason": "x"}`이고, SD의 키를 읽거나 단언하지 않는다.
  * 문서 쪽은 `docs/02-design/specs/20260930-b34-grammar-explicit.spec.md`와 `…30-module-split.design.md`의 서술이다.
* 결론:
  * "읽거나 단언하는 test·운영 코드 0곳"은 gate master에서도 성립한다.
  * 44행 "(소비처 0 -- `git grep` 7535799 …: SD 정의 줄 외 0)"은 7535799에서 맞다. 그대로 둬도 된다.

---

## 교체안 (정확한 문자열)

### 1. 65~67행 -- 2183f2e 병기(권함)

옛 글(65행 끝):
```
SD `trace_vdd_to_gnd_branches`·`trace_gnd_to_vdd_branches`(1222·1233·1234·1270·1281·1282 --
```
새 글:
```
SD `trace_vdd_to_gnd_branches`·`trace_gnd_to_vdd_branches`(1222·1233·1234·1270·1281·1282, `2183f2e` 1217·1228·1229·1265·1276·1277 --
```
옛 글(66행):
```
방향 라벨 비교(SD 1355·1357·1557·1558·1737), SR `propagate_node_voltages`·`derive_vsb_from_nodes` 기본 인자(3728·3790),
```
새 글:
```
방향 라벨 비교(SD 1355·1357·1557·1558·1737, `2183f2e` 1350·1352·1552·1553·1732), SR `propagate_node_voltages`·`derive_vsb_from_nodes` 기본 인자(3728·3790),
```
옛 글(67행 끝):
```
MNA 고정 노드 = B26-3(D2 대기): SR 4086·4991.
```
새 글:
```
MNA 고정 노드 = B26-3(D2 대기): SR 4086·4991. (이 문단의 홑 번호는 cd64170(= 7535799) 줄이다. SR 줄은 `2183f2e`에서도 같다.)
```

### 2. 77행 -- 2183f2e 병기(권함. kit_line_shift 패치 대신)

옛 글:
```
SD 3559·3561·3719 `propose_theta_kcl_gap_fill`(운영 호출 0,
```
새 글:
```
SD 3559·3561·3719(`2183f2e` 3534·3536·3694) `propose_theta_kcl_gap_fill`(운영 호출 0,
```
* 대안은 kit_line_shift 패치를 그대로 적용하는 것이다(3559·3561·3719 → 3534·3536·3694로 바꿔 씀). 그 경우 15행·71행의 'cd64170 줄' 선언과 어긋난다. 그래서 그 자리에 `(2183f2e 줄)`을 함께 적어야 한다:
  ```
  SD 3534·3536·3694(`2183f2e` 줄) `propose_theta_kcl_gap_fill`(운영 호출 0,
  ```
* SR 3950은 두 판에서 같으므로 고치지 않는다.

### 3. 499~501행 -- 번호는 그대로(측정 기록), 안내 한 줄(선택)

옛 글(501행 끝):
```
= 11함수, 16줄. `prep`의 줄 번호와 전부 일치(review 재측정 일치).
```
새 글:
```
= 11함수, 16줄. `prep`의 줄 번호와 전부 일치(review 재측정 일치). (`2183f2e` 위치는 머리 16행 -- 3042는 P9가 없앴다.)
```

### 4. 542~543행 -- 빠진 3527과 gate master 값

옛 글(542행 끝~543행 앞부분. 543행의 뒤 ' 조정할 기존 test 0개. …'는 그대로):
```
(`git grep` 7535799 `skills workspaces tools docs/01-plan docs/02-design` -- SD 3531·3535·3540(`propose_theta_kcl_gap_fill`,
     백로그 B39, 이 card 밖)과 3968 정의, 3933 docstring뿐).
```
새 글:
```
(`git grep` 7535799 `skills workspaces tools docs/01-plan docs/02-design` -- SD 3527 docstring·3531·3535·3540(`propose_theta_kcl_gap_fill`,
     백로그 B39, 이 card 밖)과 3968 정의, 3933 docstring뿐. gate `master` `6c724de`(엔진 = `2183f2e`)에서는 SD 3506·3510·3515·3943뿐이고(두 docstring 언급은 B34가 지웠다),
     그 밖은 B34 계약 test `test_b34_grammar_explicit.py:348`의 가짜 반환값 `{"unavailable_reason": "x"}`(SD 키를 읽지 않는다)와 문서 서술이다).
```

## 적용하지 말 것

* 35~36·40~47·52·54·71행의 번호: 두 판 모두 맞다.
* 44행의 '소비처 0' 문장: 7535799에서 맞고, gate master에서도 소비처는 0이다.
