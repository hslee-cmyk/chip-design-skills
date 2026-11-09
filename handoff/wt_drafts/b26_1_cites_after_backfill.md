# B26-1 줄 인용 재측정 -- 실제 backfill code 커밋 `495bb0e` 기준 (2026-10-07)

작성: 인용 재측정 agent. 실제 저장소는 `git -C … show/diff/rev-list/rev-parse`로 읽기만 했다. 모래상자는 쓰지 않았다.
`_drafts`에는 이 파일만 새로 썼다(`draft_b26_1.spec.md` sha256 `42063fe7…abe9f`, 손대지 않음).
`b26_1_precheck_863a037.md`(모의 backfill = 두 줄 삭제 가정)의 §2 표와 381행 교체안을 **실제 커밋으로 바로잡는다**.

대상 커밋: `495bb0e`(branch `role/code/20261001-b26-backfill-interdig-final-audit`, 부모 `3004096` test, 그 부모 `863a037` = gate master).
Role `code`, Change-Id `20261001-b26-backfill-interdig-final-audit`.

## 1. 실제 diff (SR, `git diff -U0 863a037 495bb0e`)

numstat SR `4 5`(모의 가정 `0 2`와 다름), 줄 수 12014 → 12013. blob `2a7a1a04…` → **`0a2cc9e3…`**(사전 점검의 모의 blob `fe33a63e…` 아님).

| hunk | 863a037 | 495bb0e | 내용 |
|---|---|---|---|
| 1 | 11758 (1줄) | 11758~11759 (2줄) | docstring `"interdig_ok":bool|None` → `…bool|None(반환 직전 _finalize가 계산한 최종 audit의` / `3b 체크로 채움)}, ...]}`…` |
| 2 | 11768~11769 (2줄) | 11769~11770 (2줄) | `_backfill_interdig_ok` 안 주석 고쳐 씀 |
| 3 | 11799 | (없음) | 루프 안 `_backfill_interdig_ok(result)` 삭제 |
| 4 | 11878 | (없음) | 루프 뒤 `_backfill_interdig_ok(result)` 삭제 |

## 2. 줄 대응 863a037(= 2183f2e SR, 같은 blob) → 495bb0e

구간 바이트 비교(`cmp`)로 확인 -- 다섯 구간 모두 동일:

| 863a037 | 495bb0e | 이동 |
|---|---|---|
| 1~11757 | 1~11757 | 0 (PREFIX 동일) |
| 11758 | 11758~11759 | 고쳐 씀(1→2) |
| 11759~11767 | 11760~11768 | +1 |
| 11768~11769 | 11769~11770 | 고쳐 씀(2→2) |
| 11770~11798 | 11771~11799 | +1 |
| 11799 | (없음) | 삭제 |
| 11800~11877 | 11800~11877 | **0** |
| 11878 | (없음) | 삭제 |
| 11879~12014 | 11878~12013 | −1 |

**사전 점검 §2 표 정정**: 사전 점검은 11800 → 11799, 11876~11877 → 11875~11876, 11879~11883 → 11877~11881이라 했다(두 줄 삭제만 가정). 실제는 docstring +1이 11799 삭제를 상쇄해
**11800~11877은 번호 그대로**, 11879 이후만 −1이다. 글 대조(495bb0e): 11800 `if result.ok:`, 11801 `_finalize`, 11802~11804 `return {…}`, 11876~11877 루프 뒤 `repair_matching_safety(`,
11878 `_finalize`, 11879~11882 `return {…}`. `_backfill_interdig_ok` 남은 출현 = 11768 `def`, 11793(중첩 `_finalize` 안 호출) 2곳.

## 3. 초안 `draft_b26_1.spec.md` SR 인용 전수 재검증(495bb0e 글 대조)

11758 앞 인용은 PREFIX 동일이라 번호·글 모두 그대로다. 그래도 전부 495bb0e에서 글을 다시 봤다(감싸는 최상위 def 포함):

| 초안 행 | 인용 | 495bb0e 글(감싸는 def) | 판정 |
|---|---|---|---|
| 12, 67, 504 | SR 4361 | `rails = set(spec.get("supply_nets") or ("vdd", "VDD"))` (`_metric_supply_current`). 그 밖 `supply_nets` 출현은 4352 docstring뿐 | 그대로 |
| 16 | "backfill은 SR 6513행 이후만 바꿔" | 실제 변경은 11758 이후 -- 문장은 참 | 그대로(선택 교체 §5) |
| 17, 111, 501 | SR 2207 | `rails = set(_DEFAULT_RAIL_HI) \| set(_DEFAULT_RAIL_LO)` (`true_current_mirror_groups` 2191) | 그대로 |
| 17, 501 | SR 4293 | `rails = set(spec.get("rail_nets") or ("vdd", …, "VSS"))` (`_metric_kcl_residual` 4267) | 그대로 |
| 66 | SR 3728·3790 | `rail_hi=_DEFAULT_RAIL_HI, rail_lo=_DEFAULT_RAIL_LO` (`propagate_node_voltages` 3727, `derive_vsb_from_nodes` 3789) | 그대로 |
| 67 | 4626 | `rail_v = ctx.spec["vdd"] if spec["rail"] == "vdd" else 0.0` (`_metric_rail_referenced_voltage`) | 그대로 |
| 67 | 4650~4653 | `"rail": "vdd"` … `"rail": "gnd"` … `abs((high + low) - ctx.spec["vdd"])` (`_metric_battery_centering_deviation`) | 그대로 |
| 67 | SR 4086·4991 | `fixed = {"gnd": 0.0}` (`build_ac_network`, `_full_circuit_response`) | 그대로 |
| 71·72·75 | 2183f2e 7281·8002·8090 | 7281 `if _usrc in _DEFAULT_RAIL_HI or …` (`_hr_resolve_vertical_group` 7088), 8002 `_rail_nets = frozenset({"vdd", "gnd", "vss"})`·8090 `rail_nets=_rail_nets, …` (`_build_theta_evaluator` 7929) | 그대로 |
| 71 | 2183f2e 6880·6885 / 6919·6930·6947 | `_rail_nets = topo.rail_nets` / `… not in _rail_nets` (`_hr_thin_singleton_ideal_source_check` 6872, `_hr_fold_group_check` 6905) | 그대로 |
| 71 | 6510~6512 | `resolve_stack_layout`(6470) docstring 끝 | 그대로 |
| 77 | SR 3950 | `rails = set(_DEFAULT_RAIL_HI) \| set(_DEFAULT_RAIL_LO)` (`node_pole_estimate` 3917) | 그대로 |
| 380 | 4271·4298·4299 | 모의 v4 head 줄(측정 기록) -- 11758 앞이라 backfill 무관 | 그대로 |
| 381 | 9411·9413, 11704·11706·11708, 6875·6877, 6578 | 모의 v4 head 줄 -- 전부 11758 앞(모의 offset +10 → base 11694~11698 등) | 그대로 |
| **381** | **11810·11886·11889·11890** | 모의 v4 head 줄. base 대응 863a037 11800·11876·11879·11880 → **495bb0e 11800·11876·11878·11879** | 병기 권장(§4) |
| **383** | **11809·11888** | 모의 v4 head 줄. base 863a037 11799·11878 → 495bb0e에는 없음 | 병기 권장(§4) |

(SD 인용은 SD blob `9993047c`가 863a037·3004096·495bb0e 모두 같아 이동 없음. 1563·2161·2165·3967·3968 등은 SD.)

모의 v4 head 쪽 대응(+10)은 사전 점검 §2의 대응(11810↔11800, 11886↔11876, 11889↔11879, 11890↔11880, 11809↔11799, 11888↔11878 -- 이 구간 균일 +10)을 그대로 썼다. 모의 head는 다시 만들지 않았다(재생성 안 함 -- 가정).
모의 v4를 실제 post-backfill base 위에 다시 만들면 그 head 번호는 11810·11886·**11888**·11889가 되고, 이 **11888은 383행 옛 번호 11888(`_backfill_interdig_ok`)과 겹쳐 다른 문장(`_finalize`)을 가리킨다** -- 그래서 번호를 바꿔 쓰지 말고 병기한다(사전 점검 권고 유지, 이유는 −2가 아니라 −1 때문).

## 4. 정확한 교체 문자열 (사전 점검 §2 교체안 정정)

두 옛 글은 초안에서 각각 1회만 나온다(`grep -c` = 1).

**381행** 옛 글:
```
`run_matching_safety_with_finger_growth` 11810·11886·11889·11890 삭제 4;
```
새 글(사전 점검안의 `11799·11875·11877·11878`은 **틀림** -- 실제 11800·11876·11878·11879):
```
`run_matching_safety_with_finger_growth` 11810·11886·11889·11890 삭제 4(모의 v4 head 줄 -- backfill 병합 착수 base(SR blob `0a2cc9e3`)에서는 11800·11876·11878·11879: `if result.ok:`·루프 뒤 `repair_matching_safety(`·`_finalize`·`return`);
```

**383행** 옛 글:
```
`run_matching_safety_with_finger_growth` 11809·11888 `_backfill_interdig_ok(result)` 삭제
```
새 글(사전 점검안 그대로 유효 -- 2183f2e와 863a037 SR blob이 같으므로 863a037을 덧붙임):
```
`run_matching_safety_with_finger_growth` 11809·11888(모의 v4 head 줄, gate `2183f2e`·`863a037` 11799·11878 -- backfill 병합 뒤 base에는 없다) `_backfill_interdig_ok(result)` 삭제
```

## 5. 선택 교체(필수 아님)

**16행** 문장은 참이지만 실제 범위로 좁힐 수 있다. 옛 글(1회):
```
backfill은 SR 6513행 이후만 바꿔 이 줄들은 착수 base에서도 같다
```
새 글:
```
backfill(code `495bb0e`)은 SR 11758행 이후만 바꿔(11758 docstring 1→2줄, 11768~11769 주석, 11799·11878 삭제) 이 줄들은 착수 base에서도 같다
```

## 6. launch·carry·브리프

* `b26_1_launch.sh`: SR 줄 인용은 85행 주석 `6510~6512`(resolve_stack_layout docstring) 하나 -- 495bb0e 글 같음, 수정 없음. 5자리 SR 인용 없음.
* `b26_1_carry.sh`: SR 줄 인용 없음.
* B26-1 전용 브리프 파일은 `_drafts`에 없다(브리프 파일은 `b26pre_briefs.md`·`b26_backfill_briefs.md`뿐, 둘 다 B26-1 착수 base를 인용하지 않음). launch·carry 안 heredoc에도 SR 줄 번호 없음.
* 참고(측정 기록이라 고치지 않음): `b26_1_ready_fd4.md:24`(모의 `11800·11879` 삭제), `b26_1_on_b34real.md:25·34`(모의 `11799·11878`) -- 둘 다 그때의 모의 base 기록.

## 7. 사전 점검 (3) engine_since ALLOW -- 실제 커밋으로 재실행

launch `engine_since`와 같은 명령(`rev-list 7535799..495bb0e -- <경로>`, trailer `Change-Id` valueonly)을 실제 저장소에서 읽기 전용으로 돌렸다:

| 경로 | 커밋 | Change-Id | ALLOW |
|---|---|---|---|
| SD | `2eb7e55` | 20260930-b34-grammar-explicit | ALLOW_SD 있음 |
| SD | `a410f31` | 20260930-p9-kcl-edges | 있음 |
| SR | **`495bb0e`** | **20261001-b26-backfill-interdig-final-audit** | ALLOW_SR 있음 |
| SR | `2eb7e55` | 20260930-b34-grammar-explicit | 있음 |
| P9T | `6bf510b` | 20260930-p9-kcl-edges | 있음 |

`3004096`(test)은 SD·SR·P9T를 건드리지 않는다. **수정 불필요.** 조건: 병합(`--no-ff`, M 트리 = M^2 트리)이 SR에서 두 번째 부모와 TREESAME이어야 merge가 rev-list에서 빠진다 --
병합 전에 master가 SR을 바꾸는 다른 커밋으로 움직이면 merge 자체가 남고 merge의 Change-Id로 판정된다(backfill id면 통과). 병합 뒤 확인:
`git -C <R> rev-parse gate/master:skills/analog-gmid-design/assets/sizing_recipe.py` = `0a2cc9e3cd180ae842323b19a3d1b9d3bc093e61`이면 §2 대응이 그대로 맞다.

## 8. 사전 점검 (4) blob 의존 -- 실제 SR blob으로 재확인

| 대상 | 863a037 | 3004096 | 495bb0e |
|---|---|---|---|
| SD | 9993047c | 9993047c | 9993047c |
| SR | 2a7a1a04 | 2a7a1a04 | **0a2cc9e3** |
| P9T | 003c0d1d | 003c0d1d | 003c0d1d |

* 승인 초안 5(`approval_20261001-b26-v3-equiv-range.md`)의 `<V3_BIND_HASH_64>` = SD `find_differential_pair_candidates` def AST 해시 -- SD 불변, SR 무관.
* 승인 초안 4(`approval_20261001-b26-p9-signature-update.md`)의 `<TARGET_DIFF_HASH_64>` = P9T diff -- P9T 불변, SR 무관.
* `_drafts`의 B26-1 파일(launch·carry·spec·두 승인 초안·kit)에 SR blob(`2a7a1a04`·`fe33a63e`·`0a2cc9e3`) 고정 없음(blob 언급은 측정 기록 `b26_1_cite_check.md`·`b26_1_precheck_863a037.md`와 다른 card 초안뿐).
* carry 바이트 핀 5개 재계산 -- 전부 일치: U3 초안 `3d2333b7…`, fill_u3 `fb8a1948…`, P9 초안 `22da78b7…`, quote_bind `050a27cd…`, t0_quote_check `03d07619…`.
* interface card: diff에 def 추가·삭제·이름 변경 없음 → `IFC_ROWS` 46 그대로 예상.
* **수정 불필요.** 사전 점검 15행의 "SR만 `2a7a1a04`→`fe33a63e`"는 모의 값이고 실제는 `0a2cc9e3`(결론 같음).

## 9. 측정하지 않은 것

* 모의 v4 head 재생성(§3의 +10 대응은 사전 점검 값을 이어 씀).
* 초안 362행 "착수 base 대상 299"(= 301 − 2)를 실제 backfill로 다시 잰 V3 대상 수 -- 실제 커밋은 같은 두 문장을 지우고, 나머지는 docstring·주석이라 B26-1이 바꾸는 문장이 아니므로 같을 것으로 보지만 재측정하지 않았다.
