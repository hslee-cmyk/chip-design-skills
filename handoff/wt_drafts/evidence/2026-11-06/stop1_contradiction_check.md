# STOP-1 처리 3안 모순 점검 (2026-11-06)

대상: worktree `wt/20261105-gc1-audit`, 머리 `fa519a6d`. 코드 경로는 `gmid_engine/` 기준.
방법: 파일 읽기와 grep만 했다. 엔진·test·도구를 실행하지 않았다. 점검자는 A 권고 작성자가 아니다.

## 결론

| 안 | 판정 | 핵심 근거 |
|---|---|---|
| **A** (면제 + test) | **모순 있음** | N3.1-5의 O-241 문언, A-59 V9·E-9의 같은 꼴 결정, `fpga/CLAUDE.md` graph 규칙 2와 어긋난다. 전제 'detail 엔진 reader 0'도 객체 단위로는 거짓이고, `value` 키 단위로만 참이다 |
| **B** (부채 + 새 card, 값 삭제) | **조건부** | 결정과 모순은 없다. 다만 (1) card 표 개정이 B에도 필요하고 (2) 값 삭제 범위가 다 재어지지 않았고 (3) '진단 손실'은 경로에 따라 다르다 |
| **C** (GC-7에 넣어 B와 같은 처리) | **조건부** | 내용은 B와 같고 선례(A-32)가 있다. 조건은 GC-7 행 문언 추가와 GC-7 시점 확인이다 |

**A 권고는 재고를 권한다.** 런타임 해는 실제로 찾지 못했다(1·2절). 문제는 규칙 일관성과 면제 누수다. 규칙과 가장 맞는 처리는 B의 내용을 C의 자리에 넣는 것이다(5절 E안). 그래도 A를 올린다면 A-59 V9 번복을 질문에 명시해야 한다.

전달받은 사실 가운데 정정할 것이 셋 있다.
- `search/start_points.py:51`은 `append_eval`로 가지 않는다. `log` → `search/find_front.py:64, :138-140` `append_run`, 즉 `runs.jsonl`의 `starts` 칸이다.
- 영속 자리는 S3 줄 둘만이 아니다(2.3).
- 조회 입력 경로는 `ss_linearize` 하나가 아니다(1.4).

## 1. 엔진 reader (확인 1)

### 1.1 `value` 키: reader 0 (직접 확인)

`tests` 밖 엔진을 grep한 결과, `FailureRecord.detail`의 `value`를 읽는 자리는 없다. 패턴은 `["value"]`, `.get("value")`, `.get("lo"/"hi"/"below"/"above")`이다. 걸린 자리는 모두 다른 객체다(spec 로더, `front_query.py:45-53`의 스냅샷 dict 등). `lo`·`hi`·`below`·`above`도 읽는 곳이 없다. S3 `fail`을 읽는 엔진 코드도 없다: `["fail"]`은 쓰기 두 자리(`search/kernel.py:76`, `search/start_points.py:51`)뿐이다. `evals.jsonl`을 여는 엔진 코드는 `search/archive.py:53` 쓰기뿐이고, `search/front_entries.py:14,25-27`은 `runs.jsonl`의 `front`·`pending_front`만 읽는다. 저장소 전체(`gmid_engine` 밖)에서 `evals.jsonl`을 찾아도 `.py`·`.ps1`·`.sh` 0건이다.

**한계:** grep은 키 이름 일치만 본다. `dict(...)`를 통째로 돌며 읽는 자리는 1.3으로 따로 봤고, 동적 키 읽기를 전수로 증명한 것은 아니다.

### 1.2 `detail` 전체: reader 있음, 상태를 바꾼다 (A 전제의 틀린 곳)

판정 기록의 'detail은 reason만 읽고'와 A의 '실패 진단 기록(엔진 reader 0)'은 객체 단위로 틀렸다. `FailureRecord.detail`의 다른 키가 엔진 판정을 바꾼다.

| 자리 | 읽는 키 | 바뀌는 것 |
|---|---|---|
| `search/layer0_center.py:451-456` | `reason`, `h_lo`, `h_hi` (수치) | 수리 대상 판정, `tol` 계산 |
| `search/layer0_center.py:484` | `node` | 수리 후보 소자 |
| `search/layer0_center.py:493`, `:692` | `reason` | 수리 판정, 정지 사유 |
| `sizing/block_columns.py:271-274` | `reason`, `target`, `branch_max` (수치) | bisection 부호 ±inf |
| `sizing/block_columns.py:226-229` | `lut_reason` | 일시 이탈 판정 |
| `sizing/block_columns.py:540-543, :566` | `reason`, `deltas` (수치) | Newton 전환, `SccLog`(값 일부가 graph 로그로 간다) |
| `search/area_decl.py:32`, `search/iv_matching_l.py:56`, `search/iv_noise.py:88`, `metrics/noise_devices.py:26`, `metrics/device_sigma.py:25`, `lut/sat_threshold.py:50`, `lut/sat_threshold_grid.py:21`, `layout/slice_density.py:31` | `reason` | 분기·사유 문자열 |

`margin`도 읽힌다(`convergence/converge_point.py:60`, `layer0_center.py:449,456`). 이 칸들은 지금 `dc_op` 출처가 아니다(`h_lo`·`h_hi`는 DC 풀이 중 잔차, `target`은 ln IDu 파생). 그래도 N3.1-2 출력 함수 기준 (i)(`graph-consumption.plan.md:249`)은 `FailureRecord`나 `seal_violation`에 적용할 수 없다. `detail`은 엔진이 읽는 객체다. **그래서 '엔진 reader 0'은 키 단위로만 쓸 수 있고, A 문언은 객체 이름으로 적으면 안 된다.**

### 1.3 통째 전달·재포장: 값이 판정으로 가는 경로 없음

| 경로 | 값이 유지되나 | 그 뒤 |
|---|---|---|
| `metrics/ss_linearize.py:53-55` `_query` | 유지 | `reason` 교체, `lut_reason` 추가. 뒤 reader는 `lut_reason`·`reason`만 |
| `sizing/_helpers_lut.py:34-38` `with_device` | 유지 | 위와 같음 |
| `core/compute_block.py:161` `register_failure` → `:156` `from_record` | 같은 객체 재연 | reader는 위 표와 같음 |
| `core/failure_errors.py:41, :85` `str(to_json())`, `pipeline/stage_b.py:162, :172`, `pipeline/stage_a.py:106, :160` | 문자열 | 정지 사유 보고(iii). 판정에 안 쓰임 |
| `Undefined(... cause.detail)` (`metrics/crossing.py:75`, `rout.py:52`, `ratio.py:44`, `icm_config.py:139`, `loop_analysis.py:50,59`) | 해당 없음 | 다른 객체 사슬이다. `metrics` 안의 `exc.record.detail` 읽기는 `ss_linearize:53`, `noise_devices:26`(`reason`만), `device_sigma:25`(`reason`만)뿐이라 FailureRecord의 값이 `Undefined`로 넘어가지 않는다 |

**A의 전제 중 `value` 키 reader 0은 살아 있다.** 무너지는 것은 객체 단위 표현이다.

### 1.4 조회 입력 경로가 더 있다 (STOP-1 기록보다 넓음)

| 경로 | S3까지 가나 |
|---|---|
| `ss_linearize.py:75-77` (`baseline_proposal.json` site에 있음) | 간다 |
| `sizing/seal_tolerances.py:29` → `_helpers_lut.py:52` `tol_v_cell` → `lut/_helpers_loo.py:157,159` `l_position`·`check_axes` → `with_device` | 정적으로는 간다. `baseline_proposal.json`은 `tol_v_cell`을 '.at 격자 조회 결과(새 값)'로만 분류해 실패 경로를 안 봤다. 도달 가능성은 재지 않았다 |
| `search/constraints.py:45` `gm_id_curve` | `kernel.py:152`는 try 밖이다. S3 줄이 아니라 정지 경로일 것으로 읽힌다(추측, 실행 안 함) |
| `metrics/noise_devices.py:31`, `ls_fields.py:55-57`, `ss_off_gate.py:41` | 잡아서 값을 버린다(`noise`는 reason, `ls_fields`는 None). `ss_off_gate`→`sat_threshold:50`도 reason만 본 것으로 확인했고 끝까지 따라가지는 않았다 |
| `metrics/ss_off_delta.py:47` | 출처가 `off_op`로 보인다(N3.1-5 출처 정의는 `dc_op`만). 실패 처리 경로는 미확인 |

따라서 `_query` 한 곳만 고치는 처리는 부족하다. 값 칸은 LUT 쪽 원천에서 없애야 한 번에 정리된다.

## 2. 값이 정본과 갈라지는가 (확인 2)

### 2.1 실행 안: 갈라지지 않음 (직접 확인)

- 재연 키의 입력 버전은 `fp_of((이름, code_hash, projection.fp))`다(`core/compute_block.py:132`). `ss_dev`는 `dc_op`를 READS하므로(`ss_linearize.py:40`) 같은 키면 `value`도 같다. 재연은 같은 객체를 다시 던진다(`failure_errors.py:29`).
- `sctx.cache` 적중은 θ·셀 키의 같은 `EvalResult`를 돌려준다(`kernel.py:99-105`). 적중 때는 S3 줄을 쓰지 않는다(`archive.py:5`).
- `start_points.py:49-54`는 실패 점을 시작점으로 쓰지 않는다. 기록만 남기고 `continue`한다.
- S3 graft는 성공 스냅샷만 받는다(`compute_block.py:146-149`). 실패는 값 재사용이 아니라 재연이다.

### 2.2 실행 사이: 갈라지지 않음

엔진이 안 읽는다(`archive.py:7-9`, `user_decisions.md:411`, X-1 계열). 줄마다 `code_fp`가 붙는다.

### 2.3 graph 규칙 대조: 해는 없지만 규칙에는 걸린다

| 규칙 (`fpga/CLAUDE.md`) | 판정 |
|---|---|
| 1 둘째 생산자 | 위반 아님. 계산하지 않는다 |
| 2 새 값 사본, '결과 객체의 값 칸(`EvalResult` 값 칸 등)' 금지. 예외는 **N3.3·N3.5의 승인 예외뿐** | **걸린다.** N3.5는 '실패는 N3.14 구조화 실패로 저장'(`gain-budget-gmid-sizing.plan.md:642`), 저장소는 '허용 넷'(`:1514`)으로 저장 자체를 승인한다. X-9도 실패 기록 등록을 승인한다(`user_decisions.md:469`). 그러나 그 안에 `dc_op` 값을 담는 예외는 적혀 있지 않다. A는 N3.1-5만 고치므로 규칙 2의 예외 자리와 맞지 않는다 |
| 3 같은 정의 필드 하나 | 정의 동일(조회 입력 = `dc_op` 칸). 걸린다 |
| 4 전달은 참조로 | 걸린다. **참조는 이미 있다:** 실패 줄의 `snapshot_fp`(`kernel.py:88-89`, X-3·X-10) |
| 6 정본 자리가 없으면 멈춤 | 정본 자리는 있다(`device.dc_op`) |

**영속 자리는 네 종류 이상이다.** A 문언이 S3 줄만 면제하면 나머지가 그대로 위반으로 남는다.
- (ii) `evals.jsonl`: `kernel.py:76,90`
- (ii)·(iii) `runs.jsonl` `starts`: `start_points.py:51`, `find_front.py:138-140`
- (iv) `sctx.cache` → `EvalResult.failure`: `kernel.py:159,163`. LA-1 범위 15 (iv)가 색인으로 옮긴다(`gain-budget-gmid-sizing.plan.md:2058, :2099`)
- (ii) `S3Index._failures`: `search/s3_index.py:59`
- 결과 객체: `Layer0Result.start_failure`(`layer0_center.py:693,700`, 엔진 소비자를 찾지 못함), 수렴 결과 `failure`(`convergence/converge_point.py:150`, `convergence_values.py:140`, 소비자 미확인)

`EvalResult.partial`은 메모리에만 있다. `write_snapshot` 호출자는 `find_front.py:47` 하나라서 실패 줄의 `snapshot_fp`는 **디스크에서 풀리지 않는다.** 2.3의 참조는 실행 안에서만 유효하다.

## 3. 결정 대조 (확인 3)

| 결정·문언 | A | B | C |
|---|---|---|---|
| **O-241**, `graph-consumption.plan.md:269` '이름으로 면제·직렬화를 가르는 허용 목록을 두지 않는다' | **어긋남.** '실패 진단 기록'은 이름·종류 면제다. 도구로 구현하면 `seal_violation`·`FailureRecord`를 이름으로 면제하게 된다. 직전에 기각한 꼴이다 | 맞음 | 맞음 |
| **O-241**, `:270` '실제 사본은 이 표가 아니라 부채 목록(card id)에 둔다' | **어긋남.** 이 자리는 사본이라고 이미 분류됐다(STOP-1 `why_copy`). 정해진 길은 부채다. A는 셋째 범주를 새로 만든다 | 맞음 | 맞음 |
| **A-59 V9, E-9, `20261104-hc1-gc8.spec.md:105, :161, :169`, `headroom-chain` plan:299** | **같은 꼴을 반대로 정함 (아래)** | 같은 논리 | 같은 논리 |
| **N3.1-5 `:272`** 출력 함수 면제는 (iii) 한정, S3 (ii) 제외 | 넓히는 개정이다 | 해당 없음 | 해당 없음 |
| **N3.1-6 (d) `:290`, (e) `:291`** | 넓히기 = 기준 약화. `criteria_weakened` + 사용자 승인. 질문에 이 표지를 써야 한다 | (e)대로 코드가 바뀌어 항목이 사라짐 | 같음 |
| **N3.1-6 (f) `:292`** card id는 card 표에 있어야 함 | 해당 없음 | **새 id면 card 표 개정 필요.** 'C만 개정이 필요하다'는 비교는 틀렸다 | GC-7 id는 있음, 행 문언 추가 필요 |
| **O-229 1번** graph 정본 완화 금지 | **긴장.** 사본을 면제로 남기는 것이 곧 완화다. 위임 밖 항목(5번)이라 사용자 결정은 가능하다 | 맞음 | 맞음 |
| **O-229 4번** 새 검증 도구 금지(LA-1을 실제로 막을 때만) | **걸림.** A의 '못 읽게 막는 test'는 새 검증 도구다. B·C로 풀리므로 '막는다'는 예외가 약하다 | 해당 없음 | 해당 없음 |
| **O-27** (`user_decisions.md:646`) 사본은 부채 + card id, 후속 card로 제거 | 선례와 다름 | 같음 | 같음 |
| **O-33** | 사본 정의의 '범위' 근거로 인용될 뿐 실패 기록을 말하지 않음. 모순 없음 | 없음 | 없음 |
| **X-3, X-10** (`:459, :470`) 실패 줄에 부분 스냅샷·`snapshot_fp` | 모순 없음. 다만 값 칸이 없어도 된다는 설계 방향이다 | 일치 | 일치 |
| **X-9** (`:469`) 실패 기록 등록·재연 | 모순 없음 | 모순 없음(기록은 남고 값 칸만 빠짐) | 같음 |
| **`user_decisions.md:411`** S3 jsonl은 결과 기록(출력) | **A의 유리한 근거**(`archive.py:7`과도 일치). 단 메모리 색인과 `sctx.cache`는 출력이 아니다 | 무관 | 무관 |
| **A-32** (`la1_auto_decisions.md:38`) `ls_fields` 동작점 사본 → GC-7 수정 | 선례와 다름 | 다른 자리 | **선례 있음** |
| 원칙 7 (`chip-design-skills/CLAUDE.md`) | 어긋남(사본) | 맞음 | 맞음 |
| 원칙 10 fail-closed | 면제가 이름 기반이면 fail-open 쪽 | 맞음 | 맞음 |
| 원칙 11 상수 | 해당 없음 | 해당 없음 | 해당 없음 |

### A-59 V9·E-9와의 관계 (가장 큰 모순)

- E-9 (`hc1-gc8.spec.md:161`): '봉인 `detail`의 `vgs_y`, `loop_stack_notes`의 `rhs`는 ... `vgs_y`·`rhs`는 N3.1-5 대입으로 사본이 맞아(A-59 V9) HC:299를 개정하고 `lhs_max`·`gap_v`로 바꾼다'.
- A-59 (`la1_auto_decisions.md:65`): 대안 'V9 값 유지 ⚠ L-5 op_copy'를 기각.
- HC:299: '값은 읽을 수 있고 사본만 없앤다'. 원래 취지와 다름으로 표지까지 했다.

실패 쪽 `detail`에 든 `dc_op` 값이라는 점이 같고, 처리가 값 삭제이고, 유지안이 op_copy 경고로 기각됐다. A는 같은 꼴을 면제하므로 **A-59 V9의 논리를 뒤집는다.**

구별 근거를 찾아봤지만 약하다. '조회 실패의 원인 값'이라는 점은 다르지만, HC:299의 VGS(Y)도 '판정 실패의 근거 값'이다. 원칙 20상 번복은 가능하다. 그러면 A를 고를 때 V9도 재검토하거나, 왜 다른지를 적어야 한다.

참고: `gap_v`·`vgs_y`는 이 worktree·master 엔진 `sizing/`에 아직 없다(`git grep`). HC-1 card는 문서로 승인됐고 구현 전이다. 그래서 A가 채택되면 HC-1 card 문언과 바로 충돌한다.

## 4. 면제가 새는가, 문언 (확인 4)

**샌다.** `FailureRecord.__post_init__`은 키·불변성만 본다(`core/failure_record.py:41-46`). 그래서 다음이 '실패 진단' 이름으로 들어갈 수 있다.

- frozen `DeviceOp` 객체 통째(`require_immutable` 통과, 불변 검사 코드 기준 추정, 실행 안 함)
- `dc_op` 칸 여러 개(`ft_curve.py:26`, `mismatch_query.py:42`, `vgs_current_density.py:42`, `_helpers_gmid_axis.py:28`, `id_inverse.py:54,62`에 이미 `L`·`vgs`·`vds`·`vsb` 칸이 있다. `dc_op` 출처 호출이 닿는지는 재지 않았다)
- 봉인 항목 값: `sizing/seal.py:83`, `size_and_seal_local.py:97`의 `item_detail`
- HC-1의 `vgs_y` 꼴

**구체 사례 (추가 확인 요망):** `sizing/seal_bulk_reverse.py:34-35, :38`의 `band.append((m, min(op.vsb, op.vds + op.vsb)))`는 `detail["indistinct"]`로 간다. `dc_seal_6` graph 필드에 쓰이고(`:43` 부근) 위반이면 `item_detail`로 S3까지 간다. `min`은 `vds ≥ 0`이면 `op.vsb`를 그대로 돌려주므로 N3.1-5 '그대로'에 해당한다. `baseline_proposal.json`·`opcopy_failclosed_sites.json`에 이 자리는 없고 `evidence/a119/holes.txt:92-93`에 스캔 행으로만 있다. '실제 샌 자리는 STOP-1 한 곳'(판정 기록)과 맞지 않을 수 있다. M-5 수정(FLOW = 라벨 합침) 뒤 도구가 잡을 것으로 보인다(추측, 수정 도구 미실행). **A의 면제 문언이 `detail`을 넓게 잡으면 이 자리를 가린다.** B·C여도 별도 분류가 필요하다.

**A를 그래도 택할 때 문언 제안.** 이 문언도 O-241의 키 이름 면제 금지와 긴장이 남는다.

> **조회 실패 입력 표지 면제**(사용자 승인 O-xxx, 기준 약화 N3.1-6 (d)). 다음을 모두 만족하는 자리만 면제한다. (1) 값 = LUT 조회 축 검사에서 범위를 벗어난 스칼라 하나(`float`). 출처 객체, 칸 묶음, 여러 축 값은 아니다. (2) 영속 자리 = `FailureRecord.detail`의 닫힌 키 목록(`lut_axis_out_of_range`·`lut_l_*` 사유의 `value` 키). 이 목록은 N3.1-6 (d) 지문 대상이고 행 추가는 (e)의 기준 변경이다. (3) 그 키의 엔진 reader = 0. 객체 단위가 아니라 **키 단위**로 검증자가 card마다 독립 측정한다. reader가 하나라도 생기면 면제가 풀려 위반이다. (4) graph 필드 쓰기(봉인 항목 `detail` 포함)와 그것을 옮기는 `item_detail`은 면제하지 않는다. (5) 봉인·판정 근거 값(HC:299 꼴)은 대상이 아니다. (6) 함께 개정: 상위 N3.5의 graph 밖 저장 예외 목록(`fpga/CLAUDE.md` 규칙 2의 예외 자리).

(3)의 test는 정적 해석으로는 건전하지 않다. `dict(...)` 재포장과 `**detail`이 정상 경로이고, 같은 도구가 M-5에서 새 주입 67꼴 중 52를 놓쳤다(`.ai/verification/20261104-gc1-rule-l.json:29`). 키 문자열 대조 수준이면 약속한 '못 읽게 막음'이 아니라 '`"value"` 문자열 읽기 없음'만 보인다.

## 5. 대안 (확인 5)

| 안 | 내용 | 판정 |
|---|---|---|
| **(iii) 재분류** | 실패 기록을 보고 경로로 옮겨 기존 출력 함수 면제를 적용 | **불가.** `:249` 기준 (i)·(ii)를 `FailureRecord`가 못 넘는다(1.2의 reader, 재연 경로). `kernel.py:68 _record`만은 함수로 보면 기준에 맞을 수 있으나, N3.1-5는 S3를 (ii)로 (iii)과 구분해 적었으므로 정의 개정이고, 메모리 색인·`sctx.cache`는 남는다 |
| **D: 경계에서만 제거** | LUT는 `value`를 유지하고 `_query`와 `tol_v_cell` 재포장에서 뺀다. DC 반복값 진단과 test 11줄이 유지된다 | 조건부. 1.4의 경로마다 고쳐야 하고 `with_device`는 반복값 경로와 공유한다. 도구는 LUT 쪽 원천을 계속 잡을 것으로 보여(추측) `op_copy_cleared` 행이 필요하다 |
| **E: B 내용 + C 자리 (제일 일관됨)** | 부채 항목 card id = GC-7, 처리 종류 '정본 읽기로 교체'. GC-7 행에 'LUT 실패 `detail`의 조회 입력 값 칸 삭제'를 더한다. 진단은 `device`·`device_query`·`axis`·`lo`·`hi`가 남아 `device.dc_op[m].<축>`을 가리킨다 | O-241 `:270`, A-59 V9, A-32, 규칙 4와 모두 맞다. 새 card·새 test 도구 없음. 부채 동안 런타임 해 없음(2절). 조건은 아래 |

### B·C·E 공통 조건

1. **범위를 먼저 잰다.** `axis_guard.py:17`·`_helpers_anchor.py:32`의 `value`만인지, 4절의 `L`·`vds`·`vsb`·`vgs` 칸까지인지를 호출 경로로 나눈다. 안 재면 삭제 뒤 같은 항목이 다시 나온다.
2. **'진단 손실'을 다시 적는다.**
   - `dc_op` 출처 경로: 실질 손실이 거의 없다. 같은 S3 줄에 `theta`·`cells`가 있고(`kernel.py:71-73`), 결정적이라 재실행으로 재현된다. 실행 안에서는 `EvalResult.partial`로 읽힌다(`kernel.py:127,140`, `ss_evaluate.py:131`). 디스크 스냅샷은 없다(2.3).
   - DC 반복값 경로(`block_columns.py:245,269` 등): 손실이 실재한다. 이 값은 graph 필드가 없어 **애초에 사본이 아닌데** 같이 사라진다. LUT 쪽 원천에서 지우면 과잉 삭제이고, 이 점이 D안의 유일한 이득이다. θ 재실행 재현으로 받아들일 수 있다는 것이 내 판단이나 사용자 몫일 수 있다.
   - NaN 구분: `test_axis_guard.py:45`가 NaN을 `value`로 확인한다. 값을 빼면 NaN과 범위 밖이 같은 사유가 된다. NaN은 물리 이탈이 아니라 수치 결함 표지라, 값이 아니라 표지로 남길지 card에서 정해야 한다.
3. **바꿀 것:** test `value` 단언 11줄(`test_axis_guard.py:36,45,73`, `test_tolerance.py:141,666`, `test_vdsat_query.py:89`, `test__helpers_anchor.py:52,143,180,402,460`), `lut/CONTRACT.md:455`, `axis_guard.py:11` docstring. test 쪽은 test 역할이 고친다(작성자 ≠ 검증자). 물리·판정 기준이 아니라 기록 칸이므로 기준 약화는 아닌 것으로 보이나, 판정자가 확인해야 한다.
4. **S3 줄 형식 변경**을 X-10처럼 기록한다.
5. **C·E 시점:** master log에서 GC-7 코드 병합 흔적을 찾지 못했다(문서 커밋만, `git log --grep`). LA-1 앞인지는 확인하지 못했다. A-55가 'GC-7 전도 조건이 LA-1 때도 남는' 경우를 재점검 입력으로 넘긴 것을 보면 LA-1 뒤일 수 있다(추측). 뒤여도 런타임 해가 없으므로 부채로 무방하다.
6. **GC-7 변경 종류:** 값 칸 삭제는 필드 무변화라 리팩터링 부분(`FR-G15`, 필드별 동일)에 넣을 수 있다. GC-7 행(`:644`)은 '필드 정리'가 제목이라 이 일이 범위 밖으로 읽힌다. 문언 추가가 필요하다.

## 확인 범위

**직접 확인:** 위 `파일:행` 전부(읽기·grep), `fa519a6d` 기준. 결정 원문: `user_decisions.md` `:411, :459, :469, :470, :646, :653, :1222`, `la1_auto_decisions.md:38, :61, :65, :66, :125, :126`. 계획 N3.1-2·N3.1-5·N3.1-6, HC:299, spec E-9.

**확인 못 함·안 함:**
- 동적 키 읽기의 전수 증명, 엔진 실행, 도구 실행, 런타임 도달 측정(특히 `seal_tolerances` 경로와 `L` 실패).
- M-5·M-6 수정 뒤 도구의 실제 결과.
- `user_decisions.md`의 길어서 잘린 행 일부(`grep` 'Omitted long' 행 205·241·513·601·623 등). 실패 기록 관련 키워드가 걸렸으나 전문을 읽지 않았다. O-33 행은 앞 1,400자만 읽었다. X-3·X-10 묶음의 주변 행과 함께 점검 누락 가능성이 있다.
- `LutMemo`가 실패를 저장하는지(`lut/lut_memo.py` 미독). 저장한다면 영속 자리가 하나 더 는다.
- `Layer0Result.start_failure`, 수렴 결과 `failure`의 결과 JSON 소비자.
- GC-7의 LA-1 대비 순서, N6.1 병합 순서 표.
