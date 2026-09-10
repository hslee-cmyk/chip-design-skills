---
template: plan
version: 4.42
---

# gain-budget-gmid-sizing Planning Document

> **Summary**: `analog-gmid-design` skill의 gm/ID 사이징 엔진(`sizing_recipe.py`)을
> "L → VDS(헤드룸) → gm_id" 순서의 role-라벨 기반 방식에서, "stage 분할 → stage별 gain
> 배분 → 그 gain에서 gm_id를 직접 역산 → 그 이후에 VDS/헤드룸을 자기일관되게 해석"하는
> gain-budget-first 방식으로 근본 재설계한다. topology.json은 순수 connectivity 전용으로
> 되돌리고, 사이징 방법론은 새 `<name>.sizing_spec.json`으로 분리한다.
>
> **Project**: chip-design-skills (analog-gmid-design skill)
> **Author**: Claude Code
> **Date**: 2026-09-04
> **Status**: Draft — 사용자 승인 대기, 파일럿 회로(`current_reuse_telescopic_ota`) 1개로
> 먼저 증명 후 나머지 3개 토폴로지 이관

---

## Executive Summary

| Perspective | Content |
|-------------|---------|
| **Problem** | `current_reuse_telescopic_ota`의 SPICE 트랜지언트 폐루프 검증을 시도하다가, 헤드룸(VDS) 배정이 diode-connected 소자(gate=drain, Vgs=Vds가 물리적으로 강제)의 실제 필요 Vgs를 무시하고 role 라벨 기반 상수(기본 0.2V)를 그대로 배정한다는 걸 실측으로 확인했다(16개 diode-connected 소자 중 최대 1.02V 오차 — M36a/M36b는 실제 1.32V 필요한데 0.3V만 할당돼 물리적으로 불가능). 원인을 추적하니 국소 버그가 아니라 파이프라인 순서 자체의 문제였다: 현재 아키텍처는 `L → VDS(헤드룸) → gm_id` 순서로 사이징하는데(`optimize_full_circuit_budget()`, `sizing_recipe.py:5679-5687`), VDS가 gm_id보다 먼저, 그것도 role 라벨 기반 상수/근사식으로 확정되기 때문에 Vgs=Vds 결합 제약이 있는 소자는 애초에 자기일관된 답을 낼 수 없다. |
| **Solution** | gm/ID sizing 방법론을 "stage를 정확히 나누고, 각 stage가 낼 gain을 먼저 배분한 뒤, 그 gain에서 유도되는 gm_id로 사이징한다 — output stage에만 driving capability(slew rate/CL)를 추가로 얹는다"는 원칙으로 baseline부터 재설계한다. VDS/헤드룸은 gm_id가 정해진 *이후*에, connectivity(gate==drain)로 diode-connected 여부를 직접 판정해 해석하므로, 이번에 발견한 버그가 재설계의 자연스러운 부산물로 해소된다. **그리고 이걸로 끝내지 않는다(2026-09-04 확정, §3.1 요구사항 6) — 사이징된 모든 소자의 전압/전류 관계가 실제로 KVL/KCL을 만족하는지 전체회로 단위로 검증하는 `verify_node_voltage_consistency()`/`cross_check_with_spice()` 게이트(§7.5)를 파이프라인에 상시 내장한다.** diode-connected 자기일관성은 이 검증기가 잡아내는 여러 위반 패턴 중 하나일 뿐이다. |
| **Function/UX Effect** | AI/사용자가 새 회로를 사이징할 때 "이 stage가 몇 dB를 낼지"를 명시적으로 배분하는 게 1급 입력이 되고, 개별 소자의 gm_id/L을 role 휴리스틱으로 따로 추측할 필요가 없어진다. 헤드룸도 diode-connected 소자마다 실측 SPICE와 부합하는 값이 나와, 이후 SPICE 폐루프 검증(트랜지언트 포함)이 실제로 수렴할 수 있게 된다. |
| **Core Value** | 물리적 정확성(physical correctness) — "gm/ID sizing은 회로의 물리적 topology 연결을 보지 않고는 할 수 없다"는 이번 세션 핵심 지적을 아키텍처 차원에서 반영한다. 재사용 가능한 계층(LUT 인터페이스, connectivity, post-sizing 레이아웃, 사후검증 metric)은 그대로 두고 사이징 "결정 순서"만 근본적으로 바꾸는 최소침습 재설계다. `.ai/context.md` 세션6~44 전체 자산화(v2.0, §1.4)로 확인됨: 이 방향은 새 발명이 아니라 세션38이 합의만 하고 못 끝낸 "DC bias vs AC amplification 도메인 분리" 아키텍처의 실제 완성이며, 헤드룸 재설계도 기존 `resolve_feed_vds()`/`_resolve_vertical_group()` 인프라를 재사용하는 쪽으로 한층 더 최소침습화됐다. |

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | gm/ID sizing 엔진이 VDS(헤드룸)를 gm_id보다 먼저, role 라벨 기반 상수로 확정하는 구조라 diode-connected 소자(Vgs=Vds 물리적 강제)에서 최대 1.02V 오차가 나고, 이게 SPICE 폐루프 DC 동작점을 출력단 레일 고정으로 발산시킨다(2026-09-04 세션, SPICE 트랜지언트 검증 중 발견) |
| **WHO** | `analog-gmid-design` skill로 아날로그 IC를 sizing하는 (fresh) agent 세션들 + 사용자(hoseung.lee) |
| **RISK** | gm_id를 gain에서 직접 역산하는 신규 함수(§2)가 캐스코드+입력 소자의 2변수 결합을 제대로 못 풀면 회귀 위험. `known-incidents.md` "사고4"(단별 이득배분은 탐색이 맞다)와의 철학적 충돌을 잘못 봉합하면 예전에 이미 폐기된 접근을 반복하는 셈 — 이번 세션 사용자 확정으로 "배분 자체는 여전히 탐색/사용자 지정, 배분 이후 gain→gm_id 역산 한 단계만 결정론화"로 경계를 명확히 함 |
| **SUCCESS** | (0) ★최우선: `verify_node_voltage_consistency(ctx)`가 사이징된 **전체회로**(51소자, diode-connected뿐 아니라)에서 KVL/KCL/VGS Violation 0건 — 이게 이번 재설계의 근본 동기(§3.1 요구사항 6). (1) 그 부분집합으로, `_solve_diode_connected_vgs_fixed_point()`가 16개 diode-connected 소자 전부에서 `vgs_for_gm_id(gm_id,L,vds*,vs)==vds*` 자기일관점에 수렴(현재 오차 0.05~1.02V → 0). (2) `current_reuse_telescopic_ota`를 새 엔진으로 재사이징해도 기존 constraints(gain≥54dB, cmrr/psrr/mismatch/classab)를 여전히 만족. (3) `cross_check_with_spice()`(sky130 트랜지스터 레벨 SPICE `.op`)이 rail-lock 없이 수렴하고 (0)의 LUT 기반 예측과 일치 |
| **SCOPE** | 이번 계획: JSON 스키마 설계 + 신규 사이징 알고리즘 설계 + 헤드룸 해석기 재설계 + 파일럿 회로(`current_reuse_telescopic_ota`) 1개 이관·검증. 나머지 3개 토폴로지(folded_cascode/nmcnr_amplifier/two_stage_ota) 이관은 파일럿 검증 후 별도 작업으로 이연 |

---

## 0. 이어받을 지점 (★ 2026-09-08 기준, 새 세션은 여기부터 읽는다)

> 이 절은 **다음 세션이 곧바로 손댈 지점**만 적는다. 배경은 §1, 설계는 §7, 미해결 목록은 §10.

### 0.1 지금 어디까지 왔나

계획 문서가 v3.4 → **v4.14**까지 왔다. 4개 관점 독립 검토(§10)에서 나온 지적을 실측으로
하나씩 확인·해소했고, **엔진 코드는 "기존 결함 수정 + 계기판 신설"까지만** 손댔다 —
**새 파이프라인(§7.2/§7.6/§7.9의 신규 harness)은 아직 한 줄도 구현하지 않았다.**

**완료(코드)**
- 선행조치 3건: self-test 회귀 기준선 신설(`assets/tests/baseline/`), 소신호 MNA numpy 전환
  (노드 51개 6.1배), 헤드룸 클로저 6개(401줄) 모듈 레벨 추출(`_hr_*`)
- `stick_diagram.py` 출력 결정론화(7줄) — stdout diff를 회귀 단위로 쓸 수 있게 됨
- metric 단위 레지스트리 + 검증기(A12), `vs` → **`vsb`** 개명 + 옛 이름 거부 가드(B9)
- 신규 계기판 5개: `mirror_ratio_error`(A4) / `supply_current`(A3) / `kcl_residual`(B8) /
  `stack_headroom_slack`(A8) + `lut_conditions_from_npz()`(A5)
- 노드전압 복원 `propagate_node_voltages()` + `derive_vsb_from_nodes()` (§7.5 코어)
- diode 자기일관 `solve_diode_connected_vds()`(bisection) + `set_device_vds()` 단일 setter (B1 3~4단계)

**완료(측정)** — 파일럿 한 점에서 이제 이만큼이 보인다. 세션 시작 때는 `gain_db` 하나뿐이었다.

| metric | 값 | 뜻 |
|---|---|---|
| `power_uA` | 243.32 | 직렬 중복 포함(A3) |
| `supply_current_uA` | **86.27** | 진짜 공급전류(2.82배 차이) |
| `kcl_residual_uA` | **3.96** | 전류 정합성 위반(B8) |
| `mirror_ratio_error_pct` | **63.61** | 미러비 계통 오차(A4) |
| `stack_headroom_slack_v` | **−1.35** | 스택 KVL 위반(A8) |
| `gain_db` | 56.98 | |

### 0.2 다음 작업 — B1 5단계(배선) + 재탐색

**이게 유일한 다음 작업이고, 되돌리기 어려운 단계다**(파일럿 산출물이 전부 바뀐다).

> ✅ **2026-09-08 진행 — 1)/2)/5)는 끝났다(v4.17).** vds 기입 7곳이 전부
> `set_device_vds()` 경유로 바뀌었고(원시 대입 0곳, C9 통과), 2)는 방향을 바꿔
> 해소했으며(B16 — `gm_id_for_vgs`로 역방향 강제), 그 과정에서 드러난 모순을 헤드룸
> 배분기까지 고쳌다(diode = 구간 제약 변수). 근거는 §7.3 "B1 5단계 배선 완료 + B16 해소".
>
> ✅ **3)도 끝났다(v4.18) -- 다만 예상과 다른 방식으로.** `stack_headroom_slack >= 0`을
> 제약으로 선언할 필요가 **없어졌다** — 배분기가 "합=vdd"를 구조적으로 강제하고 diode는
> 구간 안에서만 받으므로 **모든 그룹의 여유가 정확히 0**이 된다. 제약이 사후 검사에서
> 배분기의 불변식으로 올겨갔다. B15 ③(LUT 앵커 7→12개)도 완료됐다.
>
> ✅ **4)도 돌렸다(v4.19) -- 그리고 그 과정에서 결함 2개를 더 찾아 고쳍다.** `area_um2`를
> 제약으로 걸었더니 **제약을 걸어도 지켜지지 않았다** -- 추적하여 (i) 엔진이 매칭 쌍에
> gm_id를 전파하지 않고(B17), (ii) 레이아웃 재검증이 전역 metric을 통째로 건너뛰는(B18)
> 두 결함을 찾아 둘 다 고쳍다. 이제 제약이 실제로 지켜지고, **달성 가능한 면적 하한은
> 700~800µm² 사이**다(800µm²에서 gain 56.08dB -- 목표 54dB 대비 여유 2.08dB뿐). 근거는
> §7.3 "면적 제약이 조용히 깨지던 이유".
>
> ✅ **B19를 실측으로 다시 봤다(v4.20) -- 대상과 결론이 둘 다 틀렸다.** 미러는
> 11소자가 아니라 **18소자**이고(6소자가 어떤 matching_pair에도 없다 -- tail M5/M6,
> NMOS 그룹의 diode 레퍼런스 M66, 통째로 누락된 M7/M36a 그룹), 그리고 **미러는
> 성립한다** -- 세 그룹 모두 해가 있고 합쳐 73.95µm²로 **지금보다 면적이 준다**.
> 기존 결론은 (i) VGS를 현재값에 고정한 채 물었고 (ii) W를 깨진 함수로 구해서
> 나온 것이다. 근거는 §10.3 B19'.
>
> **그리고 (ii)가 새 결함이다 -- B20**: `_solve_vgs()`가 "gm/ID는 VGS에 단조감소"를
> 전제하는데 **PMOS LUT는 비단조**라, 그 구간에서 `argsort` 역보간이 다른 branch로
> 튄다. 모든 W 계산의 뿌리이고 오류 없이 조용히 틀린다. 파일럿에서 2소자가 실제로
> 물려 W가 2.36배 어긋나 있다(§10.3 B20).
>
> ✅ **B19'의 공동분석 두 가지는 2026-09-09 확정됐다**: **18소자 전부를 미러로
> 강제하고**(tail M5/M6 포함이 설계 의도), **공유 VGS는 gain 기준으로 고른다**(면적
> 아님 -- tail이 diffpair의 ID를 만들어 gain에 직접 영향).
>
> ✅ **B20은 2026-09-09 해소됐다**(§10.3 B20). `_solve_vgs()`가 rightmost root로
> 바뀌었고, NMOS 16,186건은 값이 한 비트도 안 변한다. 파일럿 재탐색도 정상 완주하며
> 제약 5개를 전부 만족한다(area 922.0->939.96µm², gain_db 65.55->65.75,
> gain_full 77.31->77.12, power 257.98->258.82µA -- 전부 소폭).
>
> ⏸ **B19' 배선은 실제로 해봤고, 배선 자체는 정상 동작한다** -- 15소자 전부 강제되고
> 레퍼런스 3개도 자격 OK다(`probe_mirror_wiring_readiness.py`). 그런데 **현재 동작점이
> 그 관계를 만족하지 못한다**: SLSQP 40회 전부 infeasible, 6소자가 W 상한을 최대 66.7배
> 초과한다. self-test도 깨져 토폴로지는 되돌렸고, 배선 스크립트는
> `tests/apply_b19p_mirror_wiring.py`로 보존했다.
>
> ✅ **B22는 2026-09-09 구현 완료**(§10.3 B22). `diode_vds_window()`가 VGS를 공유하는
> 소자 전원의 W 한계까지 본다. 선언 기반 옵트인이라 **미배선 self-test는 diff 0줄**이다.
> 효과도 실증됐다 -- B22를 끄면 같은 theta에서 `area_um2`가 **655mm²**인데도 통과한다.
>
> **그런데 배선을 켜면 아직 안 풀리고, 그 원인이 B9로 확정됐다(B23)**: 창을 비우는 것은
> `M38`의 **vsb=0.8625V**인데 그 소자는 source=gnd라 0이어야 한다. 가짜 바디바이어스가
> 전류밀도를 55배 낮게 보이게 해 W를 13,340µm로 튀긴다. 물리 vsb=0으로 재면 이 그룹은
> 성립한다.
>
> ⏸ **B9도 실제로 고쳐봤다(B24). 계산은 맞는데 그 뒤가 회로 판단이다.** vsb를
> 노드전압에서 유도하도록 고치고 감사기를 게이트로 배선했더니(둘 다 세션46에 만들어만
> 두고 호출부가 없던 함수다), 올바른 물리가 적용되자 `M11b`(적층 PMOS diode,
> vsb 0.0->0.6750)가 **W=6342µm**를 요구해 파일럿이 성립하지 않는다.
>
> ✅ **선택지를 계산했고, 답은 "설계 변경이 아니라 연립"이다(B25).** 전류는 지렛대가
> 아니고(전 구간 실패), L은 PMOS만 고친다. 그런데 `(v_a, v_b)`를 **함께** 고르면
> PMOS 60조합 / NMOS 32조합이 성립한다 -- 이미 성립하는 배분이 넉넉히 있는데
> 배분기가 diode마다 **독립적으로** 창을 계산해 그것을 못 찾을 뿐이다.
>
> ✅ **B25 + B9 + `bias_replica`가 함께 동작한다 -- 파일럿 평가 성공**:
> gain_db 65.5547(>=54) / **area 847.45µm²(925.52에서 감소)** / cmrr 66.12 / psrr 81.38.
> vsb 감사 게이트도 통과한다.
>
> ✅ **전부 착지했다(v4.30)**. L5c 픽스처의 `r_cmfb_vocdes`를 중점(0.11) 대신
> **하한(0.02, 실제 최적점)**에 고정하고, 적층 쌍 선택을 **W 균형**으로 바꿔
> 레이아웃까지 통과시켰다.
>
>   self-test  `sizing_recipe` exit 0 / **diff 1줄**(의도적), `stick_diagram` **diff 0줄**
>   파일럿     gain 65.5547(>=54) / **area 517.61µm² (925.52에서 -44%)** /
>              cmrr 66.11 / psrr 81.35 / vsb 감사 게이트 통과
>   기준선     mismatch_sigma_mV **3.01 -> 2.19 (27% 개선)**
>
> ✅ **B19' 배선도 착지했다(v4.31)**. 미러 15소자가 실제로 강제된다:
>
>   그룹(레퍼런스)   소자   VGS 퍼짐 배선 전 -> 배선 후
>   M18_bg            8     464.2 mV -> **0.0000 mV**
>   M66               8     663.2 mV -> **0.0000 mV**
>   M36a              2       9.2 mV -> **0.0000 mV**
>
> `M18_bg`의 vds가 0.75 -> **0.825V**로 오른 것은 B22가 미리 계산한 값과 정확히 일치한다.
> 기준선의 `mismatch_sigma_mV`는 누적 **3.01 -> 1.74(42% 개선)**. 파일럿은 gain 65.55 /
> area 584.59µm² / cmrr 62.82 / **psrr 104.30**.
>
> **다음은 재탐색(SLSQP)**이다 -- 지금까지는 고정 theta에서의 평가만 확인했다.
>
> 순서: ~~B20~~ -> ~~B22~~ -> ~~B25+B9~~ -> **L5c 픽스처 처리** -> B19' 배선 -> 재탐색.

```
1) vds 기입 7곳을 set_device_vds()로 치환
   3237 _feed_gm_target_convention / 3304 조인트스캔 / 4729 vds_match_vgs_of pre-pass /
   4772 sibling 갱신 / 4805 same_as_device / 4899 allocate 결과 적용 / 5258 stage 결과
   (줄번호는 2026-09-08 기준 -- 옮겨졌을 수 있으니 `grep -n '\["vds"\] *='`로 다시 확인)
2) 헤드룸 pre-pass에 diode 자기참조 추가 -- diode는 vds_match_vgs_of가 자기 자신을
   가리키는 특수 케이스다(§7.3). 확정값은 unresolved에서 빠져 예산에서 차감된다.
3) `stack_headroom_slack >= 0`을 constraint로 선언(지금은 −1.35라 즉시 infeasible이므로
   4)의 재탐색과 **동시에** 켜야 한다)
4) 파일럿 재탐색 -- gm_id/L을 다시 찾아 7개 스택을 만족시킨다
5) 원시 대입이 남아 있지 않은지 grep 테스트로 강제(C9)
```

### 0.3 착수 전에 알아야 할 것

- **feasible 영역은 비어 있지 않다**(v4.13 사전계산). 7개 초과 스택 중 4개는 비-diode를
  그대로 둬도 되고, 3개는 비-diode가 0.10~0.14V만 내려가면 된다.
- **다만 대가가 크다.** 최소 Vgs는 `gm_id 25~26.5` / `L=0.15µm`에서 나오는데, A11의 gain
  정점(18~20.5)을 지난 영역이고 §7.10 knee(0.30~0.45µm)보다 낮은 L이다. 실제 해는 그 사이
  어딘가이고 **gain·면적 제약과 동시에 만족하는지는 아직 모른다** — 돌려봐야 안다.
- **병목은 M36a/b가 아니다.** 가장 커 보였던 1.361V 요구는 단독 컬럼이라 여유 0.439V가
  남는다. 실제 병목은 **diode 2개가 직렬인 컬럼**(`biasgen_vom/vop_battery_a`)이다.
- **재사이징 후 `vsb`가 확정되어야 다음이 풀린다**: 현재 노드전압 복원에 **다중도달 불일치
  4건(전부 243.5mV)**이 남아 있어 노드전압이 유일하게 정해지지 않는다. 그 모순이 vds 배정에서
  오므로 B1 배선이 그것을 해소하는지 먼저 확인하고, 그 다음에 `vsb` 26개 불일치를 고친다.

### 0.4 검증 방법

- **회귀**: `python sizing_recipe.py` / `python stick_diagram.py`의 stdout이
  `assets/tests/baseline/*.baseline.log`와 **바이트 동일**해야 한다. 배선은 동작을 바꾸므로
  이 기준선도 **의도적으로 갱신**하고, 갱신 사유를 커밋 메시지에 남긴다.
- **계기판**: 위 6개 metric을 재사이징 전/후로 나란히 적는다. 특히
  `stack_headroom_slack_v ≥ 0`과 `kcl_residual_uA` 감소가 성공 판정이다.
- **조사 스크립트**(`assets/tests/probe_*.py` 9개)는 전부 재실행 가능하다 — 값이 바뀌면
  각 파일 상단 docstring의 측정치도 함께 갱신할 것.

### 0.5 아직 사용자 승인이 필요한 것

- **`vsb` 산출 수정**(B9) — 고치면 LUT 조회가 바뀌어 W/gm이 달라진다. B1 배선과 함께 하기로
  했으나 실제 착수 전 재확인.
- **`stack_headroom_slack`을 constraint로 승격**하는 시점.
- **`ideal_sources.value_amp` 소비 배선**(B14) — 규약은 확정됐다(null이면 자유탐색, 값이
  있으면 그 값 사용). 파일럿 Iref 1.2µA가 고정되면 `r_biasgen`의 자유도가 줄어든다.

---

## 1. Overview

### 1.1 Purpose

gm/ID 사이징 엔진의 소자별 결정 순서를 `L → VDS(헤드룸) → gm_id`에서
`stage 분할(connectivity) → stage별 gain 배분(spec) → gm_id 역산(LUT) → VDS/헤드룸 해석`으로
뒤집는다. 이렇게 하면 (a) diode-connected 등 Vgs=Vds 물리 제약이 있는 소자도 자기일관된 헤드룸을
받고, (b) 각 stage의 gm_id가 role 휴리스틱 추측이 아니라 실제 목표 gain에서 결정론적으로 유도되며,
(c) output stage에만 driving capability(slew rate/CL) 제약을 추가로 얹는 구조가 스키마 차원에서
명시적으로 드러난다.

### 1.2 Background

2026-09-04 세션에서 `current_reuse_telescopic_ota`의 class-AB 출력단 Up/Down settling 대칭성을
sky130 트랜지스터 레벨 SPICE 트랜지언트로 검증하려 했다. 51소자 전체 폐루프 `.op`을 시도하는
과정에서 출력이 VDD 레일에 고정(rail-lock)되는 걸 발견했고, CMFB 루프를 열어도 동일하게
재현돼 CMFB 부호 문제가 아니라 바이어스 체인 자체의 문제임을 확인했다. 근본원인을 추적한 결과:

1. `topology.json`의 `ideal_sources.Iref.value_amp=1.2uA`는 순수 선언 메타데이터일 뿐 실제
   사이징 엔진이 읽지 않는다(`sizing_recipe.py:2824`) — 부차적 수정.
2. **핵심 문제**: diode-connected 기준소자(예: M18_bg, gate=drain=Vbias1)는 물리적으로
   Vgs=Vds일 수밖에 없는데, 저장된 `vds`(헤드룸 예산, 예: 0.2V)와 실제 sky130 LUT/SPICE가
   그 gm_id에서 요구하는 실제 Vgs(예: 0.99V)가 전혀 다르다. 16개 diode-connected 소자 전수
   조사 결과 오차가 0.05V~1.02V였다(가장 심한 M36a/M36b: 필요 1.32V, 할당 0.3V).
3. 근본원인은 `allocate_stack_headroom()`/`HeadroomPolicy`가 VDS를 gm_id보다 **먼저**
   role 라벨(`cascode`/`diode_reference`/`mirror`/...) 기반 상수로 확정하는 파이프라인
   순서 자체에 있다(`optimize_full_circuit_budget()` docstring, `sizing_recipe.py:5679-5687`).

사용자가 이를 "gm/ID sizing은 물리적 topology 연결을 보지 않고는 할 수 없다"는 더 근본적인
설계 원칙 문제로 재규정했고, "stage를 먼저 나누고 gain을 배분한 뒤 gm_id를 유도한다"는 방향으로
baseline부터 재설계하기로 확정했다.

### 1.3 Related Documents

- `.ai/context.md` "세션44 (계속)"/"세션44 (계속 2)" — diode-connected 헤드룸 버그 발견 경위
- `skills/analog-gmid-design/references/gm-id-methodology.md` §2.5/§4/§6.4/§6.7 — 기존
  "GBW/PM→gm, gain은 사후 readback" 방향의 근거
- `skills/analog-gmid-design/references/gm-id-methodology.md` §13(§13.1/§13.2/§13.3/§13.7
  특히) — 이 프로젝트 엔진 실전 운영에서 나온 고유 발견, §7.2 알고리즘 개정의 직접 근거
  (2026-09-04 §1.4 추가)
- `skills/analog-gmid-design/references/known-incidents.md` "사고4" — 단별 이득배분을
  닫힌 식으로 강제하려다 탐색+제약조건으로 정정한 전례(이번 재설계와의 경계 구분 필요)
- `skills/analog-gmid-design/references/known-incidents.md` "사고10/16/19/21/22/23/24" —
  오늘 발견한 헤드룸 버그와 같은 클래스의 5개 선례 + §7.3 개정이 재사용하는 기존 인프라
  (`resolve_feed_vds()`/`_resolve_vertical_group()`)의 출처, §8.4 위험(사고16) 근거
  (2026-09-04 §1.4 추가)
- `skills/analog-gmid-design/references/topology-fn-derivation-guide.md` — 기존 GBW/PM→gm
  reverse-derivation 절차(compensation 방향이 반대가 됨에 따라 참고용으로 남김)
- `docs/01-plan/features/analog-topology-json-library.plan.md` — topology.json을
  "사이징과 무관한 connectivity만" 담자는 원래 설계 의도(`_TEMPLATE.topology.json` §schema_note) —
  이번 재설계가 그 원칙을 device_roles/sizing_roles/compensation까지 완성한다
- `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json` —
  파일럿 회로의 현재 connectivity + (폐기 대상) device_roles/sizing_roles/compensation

### 1.4 이 재설계의 역사적 선례 (2026-09-04 `.ai/context.md` 세션6~44 전체 자산화로 발견)

이 계획을 세운 뒤 `.ai/context.md`(세션6~44) 전체를 `references/*.md`로 자산화하다가, 오늘의
diode-connected 헤드룸 버그가 처음이 아니라 **같은 근본 클래스가 최소 5번 반복** 발견/부분수정
됐었고, 이번 재설계가 실제로는 세션38이 설계만 하고 못 끝낸 아키텍처를 완성하는 작업임이
드러났다. 아래는 이 계획을 직접 수정하게 만든 선례만 추린 것(전체는 `known-incidents.md` 사고
10/16/19/21/22/23/24, `gm-id-methodology.md` §13 참고):

- **`known-incidents.md` 사고21(세션38) ★★ — 이 재설계의 진짜 원형**: "AC signal은 input이
  root, bias망의 시작점은 DC 전압이다. DC bias 최적화를 먼저 하고 AC gain 타겟을 그 위에서
  맞춰야 한다"는 **Phase 1(DC 그래프 완전 정합) → Phase 2(남은 자유도만 AC 타겟에 맞춰 탐색)**
  아키텍처가 세션38에서 이미 사용자와 합의됐으나 **당시 미구현**으로 남았다. 이 계획의 "VDS를
  gm_id 확정 이후에만 푼다"는 순서 자체가 정확히 이 Phase 1/Phase 2를 구현하는 것 — 새 개념이
  아니라 세션38 합의를 실제로 완성하는 작업이다. `device_roles.vds_match_vgs_of`/
  `gm_id_match_vgs_of`(참조 소자의 VGS를 그대로 이 소자의 VDS/gm_id로 강제 동일화하는 이미
  구현된 primitive)를 §7.2/§7.3에서 그대로 재사용할 것 — 새로 발명하지 않는다.
- **사고22(세션39)/사고24(세션41) — 재사용할 기존 메커니즘**: 여러 소자/그룹이 서로 다른
  멤버를 통해 맞물리는 상호참조 헤드룸 문제는 이미 `_resolve_vertical_group(vsid)` +
  `_HeadroomDependencyNotReady` 예외 기반 **fixed-point worklist**로 풀려 있고("지금 풀 수
  있는 그룹부터, ctx.sized에 vds가 채워진 소자 수가 늘었는지로 진전 판정"), 소자 하나의 vds를
  결정하는 우선순위는 이미 `resolve_feed_vds(name, declared_vds, ctx)`(① 이미 `ctx.sized`에
  있으면 그 값을 존중 ② declared_vds ③ role 기반 폴백)로 통합돼 있다. §7.3을 이 기존 인프라를
  **대체**하는 대신 **확장**하는 설계로 바꾼다(아래 §7.3 참고).
- **사고23/24(세션40~41) ★★★★ — 오늘 버그가 실제로 사는 함수**: `resolve_feed_vds()`/
  `_feed_vds_fallback()`가 바로 오늘 발견한 diode-connected 헤드룸 버그의 정확한 코드 위치다.
  사고24는 "하드코딩 복붙 4곳"을 하나로 통합해 **중복은 해결**했지만, `gate==drain`(Vgs=Vds
  강제) 소자의 **물리적 정확성**은 그때도 다루지 않았다 — 이번 재설계가 메워야 할 정확히 그
  간극.
- **`gm-id-methodology.md` §13.1/§13.2 — §7.2 stage 알고리즘 보강 근거**: "커플드 소자쌍은
  단일소자 role 기준(예: 캐스코드가 자기 혼자 gm/gds 최대화)으로 최적화하면 결합 최적점을
  놓친다"(M15/M16 실측: 71.14dB→75.80dB), "gm_id 독립화로 806개 지점 동시만족 발견"(세션31,
  `shared_gm_id_groups`의 대칭 개념으로 가칭 `shared_current_groups`—ID만 공유, gm_id는 독립
  탐색—필요성 제기). §7.2의 "stage 내 input+cascode 동시결정" 요구사항이 정확히 이 문제의
  구체 사례.
- **§13.7 — §7.2에 빠져있던 구분**: cascode(gm이 ro에 곱해 기여 → `gm_id_role="gain"`,
  `gm/gds` 최대화)와 **비캐스코드 단순 전류원 부하**(ro 자체가 기여 → 신설된 `role="load"`,
  `gds` 최소화 — `gm/gds`와 다른 물리량이라 서로 대신 최적화 안 됨, 실측: `"gain"` 적용 시
  `ro`가 진짜 최댓값의 절반에 그침)는 **서로 다른 목적함수가 필요**하다. `role="load"`는 이미
  `search_gm_id_for_role()`에 구현돼 있다(§7.2 개정 참고).

---

## 2. Scope

### 2.1 In Scope

- [ ] 새 JSON 스키마 설계: `<name>.sizing_spec.json`(§7.1) —
      `stages[].devices.{input,cascode,load,tail}`, `global_spec.constraints`(총 gain·cmrr·psrr·
      mismatch 문턱), `stages[].driving_spec`(output 전용), `compensation`(방향 반전),
      `headroom.policy`, `bias_devices`(stage 밖 diode-reference/mirror 소자).
      **`gain_budget_db`는 입력이 아니라 출력**(v3.1) — 예외 경로로 `gain_budget_db_override`만 둠
- [ ] `topology.json`을 순수 connectivity 전용으로 되돌림 — `device_roles`/`sizing_roles`/
      `compensation` 필드 제거(새 `sizing_spec.json`으로 이관)
- [ ] 신규 함수 구현(`sizing_recipe.py`, §7.2/§7.3 — 2026-09-04 §1.4 자산화 반영으로 축소됨):
  - [ ] `_solve_diode_connected_vgs_fixed_point(gm_id, L, vs, lut)` — 이번 세션 스크래치패드
        `node_dc_propagate.py`에서 프로토타입 검증 완료, 그대로 이식. connectivity
        (`gate==drain`) 기반 판정, §7.2 stage 사이징 직후 `ctx.sized[name]["vds"]`에 기입해
        기존 `resolve_feed_vds()` 우선순위①(이미 있으면 존중)로 자연스럽게 보호되게 함
  - [ ] `gm_id_for_gm_gds_ratio(target_ratio, L, vds, vs)` — `gm_id_for_vgs()`(:536)와 동일
        패턴의 O(1) 역보간, gm/gds 축 신규
  - [ ] `resolve_stage_sizing(stage_spec, ID, luts)` — stage 알고리즘(§7.2, cascode=`role="gain"`
        /load=`role="load"` 구분 포함) 구현체
  - [ ] ~~`_resolve_device_headroom(device, ctx)`(`allocate_stack_headroom()`/`HeadroomPolicy`
        대체)~~ — **취소(§7.3 개정)**: `resolve_feed_vds()`/`_resolve_vertical_group()`가
        이미 구현돼 있어(사고22/24) 전면 교체 대신 위 diode-connected solver를 그 우선순위
        체인 앞단에 끼워넣는 것으로 충분함이 드러남
  - [ ] `solve_compensation_for_gbw_pm(stage_gms, targets)` — 기존 `topology_fn`(GBW/PM→gm)의
        역방향(gm들→Cc/Rz). `device_roles.vds_match_vgs_of`/`gm_id_match_vgs_of`(사고21,
        이미 구현됨)를 stage 간 결합 소자에 그대로 재사용 — 새 결합 메커니즘 발명하지 않음
  - [ ] **★ `verify_node_voltage_consistency(ctx)`**(§7.5) — 전체 netlist 노드전압 재구성 +
        상호모순/VGS 불일치 검사. 이번 재설계의 가장 근본적인 요구사항(§3.1 요구사항 6)의
        직접 구현체 — diode-connected뿐 아니라 **모든** 소자의 V/I 관계를 검증
  - [ ] **★ `cross_check_with_spice(instance_data)`**(§7.5) — sky130 SPICE `.op` 독립 교차검증,
        스크래치패드 `build_transient_netlist.py`를 skill asset으로 정식 편입
  - [ ] `L_candidates_product()` + `resolve_stage_sizing()`의 L outer-loop(§7.6 (3)) —
        cascode/load/tail의 L을 면적 오름차순으로 전수 스캔하며 각 L_combo에서 §7.2를
        결정론적으로 실행, `extra_feasible`(§13.5 기존 패턴)로 cmrr/psrr/mismatch 판정
  - [ ] **`sweep_area_power_pareto(sizing_spec, luts) -> ParetoReport`**(§7.9, v3.4) — 면적
        예산 미선언 시 전력-면적 Pareto front를 뽑아 제시하고 정지(엔진이 예산을 지어내지
        않는다). 선택 결과는 `global_spec.constraints`의 `area_um2`로 기록
  - [ ] ~~`make_cmrr_psrr_feasibility_check(...)`~~ — **삭제(v4.4)**. `make_matching_
        feasibility_check()`와 "동일 패턴"이 **원리적으로 불가능**함이 실측으로 확인됐다:
        `smallsignal_ratio_db`는 `_full_circuit_devices()`가 전 소자를 요구해 stage 사이징
        도중에는 `KeyError`다(§7.6 B2 해소 참고)
  - [ ] **`make_stage_local_check(metrics, constraints, grp, spec)`**(§7.6, v4.4) — T1/T2
        metric만 골라 `extra_feasible` 콜백으로 변환(기존 `make_matching_feasibility_check()`
        를 일반화). T3가 섞여 들어오면 **선언 시점에 거부**한다
  - [ ] **`check_global_gates(ctx, metrics, constraints) -> GateReport`**(§7.6, v4.4) — T3
        전용 전역 게이트. 전 소자 사이징 완료 후 1회 실행(측정 0.72 ms), 위반 metric과
        여유량을 함께 반환해 §7.6(4) 승격 판단에 쓴다
  - [ ] **`diagnose_sizing_dof(sizing_spec, topology) -> DofReport`**(§7.8) — 사이징 시작
        전에 "목표 개수 대비 실제 자유도가 충분한가"를 스키마+connectivity만으로 판정
        (`ok`/`underdetermined`/`overconstrained`), `overconstrained`면 어느 목표끼리
        같은 자유도를 다투는지 명시 보고하고 반복을 아예 시작하지 않음(사고19 재발 방지)
  - [x] **(2026-09-07 완료)** `_hr_vfind()`/`_hr_thin_singleton_ideal_source_check()`/
        `_hr_fold_group_check()`/`_hr_sum_ref_vds()`/`_hr_verify_group_kvl_sum()`/
        `_hr_resolve_vertical_group()` — 2중 중첩 클로저 6개를 모듈 레벨로 추출(§8.4)
  - [ ] **`compute_metric(metric_spec, ctx)` 경유 gain 제약**(§7.9, v4.0) — `_METRICS_REGISTRY`
        위임. `∂gain/∂gm_id_i`는 LUT 위 수치미분. 회로별 폐형식을 옵티마이저 본문에서 제거
  - [ ] **`solve_allocation_dp(stage_tables, gain_target, area_budget) -> Allocation`**(§7.9,
        v4.2) — stage별 gm_id 배분의 **정확 해법**. 분리성을 이용한 자원배분 DP라 기울기를
        쓰지 않아 비볼록(A11)에 영향받지 않는다. 프로토타입·근거:
        `tests/probe_allocation_solvers.py`. Pareto front(§7.9 v3.4)도 같은 DP의 비지배
        집합에서 **한 번의 전파로** 나온다
  - [ ] **`set_device_vds(ctx, name, value, source)`**(§7.3, v4.3) — vds 기입의 **유일한**
        경로. diode 소자면 고정점 해와 일치하는지 검사해 어긋나면 즉시 실패, `_vds_source`
        태그 기록(B13 추적성 동시 해결). 기존 7개 기입 지점을 전부 이 함수로 치환하고
        원시 대입 잔존 여부를 grep 테스트로 강제
  - [ ] **`load_sizing_spec(path) -> SizingSpec`**(§7.1, v4.0) — 스키마 검증기. 미지 필드 거부,
        `topology_ref` 정합 확인, `metrics[].type`이 `_METRICS_REGISTRY`에 있는지 확인,
        `schema_version` 마이그레이션. 선언만 되고 아무도 안 읽는 필드를 **정적으로 잡는다**
        (C5 재발 방지 — `settling_time_ns`가 실제로 그 상태였다)
  - [ ] **`resolve_headroom(topology_spec, ctx)`**(§8.4) — 위 `_hr_*` 6개를 묶는 독립 harness.
        추출이 끝났으므로 이제 구현 가능
- [ ] 파일럿 회로 이관: `current_reuse_telescopic_ota`를 새 스키마로 재작성, 새 엔진으로
      재사이징
- [ ] 회귀 검증: 기존 사후검증 metric(`gain_db`/`cmrr_estimate_db`/`psrr_estimate_db`/
      `mismatch_sigma_mV`/`classab_centering_dev_v`)이 기존 constraints를 여전히 만족하는지 확인
- [ ] **전체회로 물리 정합성 검증**(§7.5, diode-connected 16개 소자 포함하되 그것만이 아님):
      `verify_node_voltage_consistency()`가 Violation 0건 보고 — diode-connected 자기일관성
      (`vgs_for_gm_id(gm_id,L,vds*,vs)==vds*`)은 이 검증의 특수 케이스로 포함됨
- [ ] SPICE 폐루프 재검증: `cross_check_with_spice()`로 새 사이징 결과의 `.op` 수렴 확인
      (rail-lock 없음) → 원래 목표였던 class-AB Up/Down settling 트랜지언트 검증 재개

### 2.2 Out of Scope

- 나머지 3개 토폴로지(folded_cascode/nmcnr_amplifier/two_stage_ota) 이관 — 파일럿 검증 후
  별도 작업
- `optimize_full_circuit_budget()`의 신/구 경로 강제 일괄 전환 — `sizing_spec` 유무로 분기,
  점진적 이관
- ~~gain 배분 자동 탐색 알고리즘 고도화~~ → **v3.1에서 In Scope로 이동**: 배분은
  §7.9 Phase 2의 root current 1-D 해찾기로 **유도**하는 것으로 확정됐다(별도 탐색 알고리즘이
  아니라 단조 함수의 해찾기라 구현 비용이 작다)
- 레이아웃/floorplan/euler 자동수정 계층 변경 — 전부 재사용, 무변경

---

## 3. Requirements

### 3.1 Functional Requirements

1. Stage 안에 input(들) + cascode(들)이 있는 경우(텔레스코픽류), `gain_budget_db` 하나에서
   input의 gm_id와 cascode의 (L, gm_id)를 함께 결정할 수 있어야 한다(사용자 확정: "동시 결정").
2. Output stage는 `driving_spec`(CL/slew-rate/settling-time)이 있으면 `ID_final = max(KCL ID,
   slew_rate_target * CL)`로 ID를 상향할 수 있어야 하고, 이 상향이 gain 배분 로직과 충돌하지
   않아야 한다.
3. 헤드룸 해석기는 `connectivity(device).gate == connectivity(device).drain`을 role 라벨보다
   우선하는 진실源으로 삼아야 한다.
4. **(v4.0 개정 — 인과 방향 확정)** 위상보상이 **먼저** 돈다: 스펙 `(CL, GBW, PM)`에서
   `(Cc, Rz, gm_1..gm_N)`을 **한 번에** 푼다(2단 Miller면 `gm_1 = 2π·GBW·Cc`, `gm_2 = Z·gm_1`).
   그 다음 `gm_id_i`가 **유일한 자유 축**이 되고 `ID_i = gm_i/gm_id_i`가 파생된다.
   ~~GBW/PM은 이미 정해진 stage gm들로부터 보상소자 값을 역산한다~~
   (사용자 확정: "gain이 주도").
5. **(v3.1 개정)** gain 배분은 **엔진이 유도한다** — 사용자는 총 gain 목표
   (`global_spec.constraints`의 `gain_db>=X`)만 주고, stage별 `gain_budget_db`는 §7.9 Phase 2가
   `A_i,max` 실측 + **`gm_id_i`를 변수로 한 해석해(KKT)+활성제약** 절차로 결정해 **출력**한다
   (v3.2 재정식화 — v3.1의 root-current 1-D 해찾기는 그 특수 케이스). `stages[].gain_budget_db_override`
   는 논문 재현 등 예외 경로로만 남긴다.
   ⚠️ **사고4와의 관계**: 사고4는 "논문에서 배분값을 **찾으려던** 것"을 "회로에서 도출하라"로
   정정한 것이었고, 당시 해법이 "탐색"이었다. v3.1은 그 도출을 **더 좁혀** 물리 상한(`A_i,max`)
   실측 기반의 결정론적 해찾기로 만든다 — 값을 사람이 지어내지 않는다는 사고4의 본질은 그대로다.
6. **★ 이번 재설계의 가장 근본적인 동기(사용자 확정, 2026-09-04) — 전체회로 물리 정합성
   검증**: 사이징된 **모든** 소자(diode-connected뿐 아니라)의 전압(VGS/VDS)·전류(ID) 관계가
   실제로 KVL/KCL을 만족하는지, 파이프라인 마지막에 **전체 netlist 단위로** 독립 검증하는
   단계가 있어야 한다 — 개별 vertical_stack_id/그룹 내부 KVL 합만 맞는지 보는 게 아니라
   (그건 이미 `allocate_stack_headroom()`의 assert가 함), 서로 다른 경로로 같은 net에
   도달하는 두 소자가 실제로 같은 전압을 예측하는지, 그리고 어떤 소자가 게이트로 받는
   내부 net의 실제 전압이 그 소자가 사이징될 때 가정한 VGS와 일치하는지까지 검증해야 한다.
   오늘 diode-connected 버그를 발견한 방식(§7.5 참고 — 레일에서부터 소자별 vds를 따라 전체
   netlist의 노드전압을 직접 재구성하고, 독립된 두 번째 solver(SPICE)로 교차검증) 자체가
   이 요구사항의 프로토타입이었다 — 이걸 **1회성 디버깅 스크립트가 아니라 파이프라인의
   상시 검증 게이트**로 승격하는 게 이번 재설계의 핵심 목적이다(diode-connected 헤드룸
   수정은 이 검증기가 잡아낸 여러 사례 중 하나일 뿐 전부가 아니다).

### 3.2 Non-Functional Requirements — 3대 기본 원칙 (★ 2026-09-07 사용자 확정, v3.0)

이번 재설계의 비기능 요구사항은 아래 셋뿐이며, 우선순위도 이 순서다.

**P1. 버그 free가 최우선 — 전면 재설계를 허용한다.**
v2.x까지 걸어두었던 "기존 재사용 계층의 함수 시그니처는 변경하지 않는다"는 제약은 사용자
확정으로 **폐기**한다. 기존 함수를 개선하거나 통째로 다시 설계하는 것을 막지 않는다 — 판단
기준은 "기존 코드를 얼마나 보존했나"가 아니라 **"물리적으로 옳은가, 조용한 실패가 구조적으로
불가능한가"**다.

> 이 제약이 실제로 설계를 비틀었던 두 사례(둘 다 이번 v3.0에서 바로잡는다):
> - **§7.3**: diode-connected 값을 "먼저 기입하면 `resolve_feed_vds()` 우선순위①이 지켜준다"는
>   **암묵적 순서 의존**으로 우회했다 — 그건 사고19/23이 당한 바로 그 취약성이다.
> - **§7.9**: gain 기여도 기반 가중 헤드룸 배분이 필요한데 `allocate_stack_headroom()`의
>   "남는 예산 균등분배"를 못 고쳐 **구현 자체가 불가능**한 모순 상태였다.

**P1-b. 우회(skip/예외)를 만들기 전에 타당성을 먼저 검토한다** (사용자 지시, 2026-09-08).

> "너는 항상 타당성을 따지지 않고 skip 로직을 만드는 경향이 있어. 그건 금지야."

검사를 통과시키는 가장 빠른 길이 `continue` / `except: pass` / 예외 목록이라 반사적으로 손이
가는데, 그 순간 **"검사가 잡아낸 진짜 결함"이 "검사의 예외"로 둔갑한다**. 우회를 쓰기 전에
세 가지를 먼저 답한다.

1. **이 대상이 실재하는가** — 그 필드/조건이 진짜 설계 입력인지 grep으로 확인한다.
2. **검사가 틀렸는가, 대상이 틀렸는가** — 대부분 후자다. 후자면 대상을 고친다.
3. **우회 없이 고칠 방법이 있는가.**

실제 사례(v4.17 작업 중): diode 자기일관성 검사를 배선했더니 self-test가 깨졌고,
`spec["known_sizing"]` 소자를 건너뛰는 규칙을 넣었다. 그런데 `known_sizing`은
**topology.json에 0건, 워크스페이스/spec 빌더에 0건**인 self-test 픽스처 전용 우회로였다 —
물리 검사를 테스트 편의로 무력화한 것이고, 정작 검사는 픽스처가 diode 소자에 불가능한 값
(`gm_id=12 @ vds=0.6`, 실제 요구값 21.275)을 시드하던 **기존 오류를 정확히 찾아낸 것**이었다.
정답은 skip이 아니라 픽스처의 vds를 물리적으로 일관된 값으로 바꾸는 것이었다.

이 원칙은 C5(게이트 사각)의 예방책이자 **★절대원칙(만들면 배선하라)의 짝**이다 -- 만들어
놓고 예외로 비켜가게 하면 배선하지 않은 것과 같다.

**P2. 효율성 — 재계산·중복 스캔을 구조적으로 막는다.**
같은 `(L, vds, vs, gm_id_grid)` 스캔이 호출부마다 반복되지 않도록 스캔 축을 함수 안으로
내리고(예: L축 내부화, §7.6/§7.10), 캐시 키는 **"그 함수가 실제로 읽는 모든 가변 상태"**
기준으로 잡는다(`lut-generation-checklist.md` §9의 CMFB MNA 캐싱 회귀가 근거 — `metric_spec`만
키로 썼다가 `ctx.sized` 변경을 놓쳐 잘못된 값을 반환했다).

**P3. 기지의 사고(사고1~24)는 구조적으로 재발 불가능해야 한다.**
"조심하겠다"가 아니라 **설계가 그 실수를 애초에 허용하지 않아야** 한다. §3.3의 C1~C10이 그
목록이며, 각 항목은 담당 설계 절과 방지 장치를 명시한다. 구현 완료 판정(§4.1)에 이 표의 모든
행이 방지 장치를 갖췄는지 확인하는 항목이 포함된다.

**부수 요구**: 신규/개선 함수는 §8.8 방침대로 `assets/tests/test_<module>.py`에서 검증한다.

### 3.3 기지 사고 재발 방지 설계 원칙 C1~C10 (★ 신설 v3.0 — P3의 실행 목록)

`known-incidents.md`의 사고1~24를 **실패 클래스**로 묶고, 각 클래스를 구조적으로 막는 장치와
담당 절을 지정한다. "이 설계는 그 실수를 할 수 없다"가 목표이지 "주의하겠다"가 아니다.

| # | 실패 클래스 | 출처 사고 | 구조적 방지 장치 | **강제 테스트**(이게 없으면 방지 장치가 없는 것) | 지금 돌리면 |
|---|---|---|---|---|---|
| **C1** | **물리 제약 미검증 상수** — 전압/전류 기본값이 KVL/KCL/Vgs=Vds를 만족하는지 확인 없이 쓰임 | 10, 23, 24 | 모든 전압/전류 값은 물리 solver 또는 declared 선언을 거친다. 상수 폴백은 "KVL/KCL 그룹에 속하지 않음이 확인된 소자"에만 허용하고, 그 판정을 함수가 직접 한다(§7.3 `set_device_vds()`) | `test_diode_self_consistency` — diode-connected 전수에서 `\|vgs_for_gm_id(gm_id,L,vds*,vs) − vds*\| < tol` | **FAIL** — 16/16 소자가 tol 초과, 최대 1.020V(M36a/b) |
| **C2** | **암묵적 순서 의존** — "누가 먼저 쓰느냐"로 결과가 달라짐 | 13, 19, 23 | vds 기입 7곳을 **단일 setter**로 수렴(§7.3 v4.3). 우선순위는 명시적 티어로 선언 | `test_order_shuffle_invariance` — 소자·그룹 **처리 순서를 셔플**해 2회 실행하고 instance.json이 바이트 동일한지 | 미실행 — `set_device_vds()` 단일화가 선행돼야 성립 |
| **C3** | **조용한 소실·덮어쓰기** — dict 키 충돌/저장 누락으로 데이터가 말없이 사라짐 | 12, 14, 16 | 이름 생성은 호출 전역 유일성 보장, 계산·저장 필드 목록을 한 곳에서 파생, 모든 pass 뒤 커버리지 재검증 게이트 | `test_coverage_and_field_completeness` — **기존 `check_stick_diagram_coverage()`(이미 프로덕션 배선됨)** 재사용 + instance.json 소자 누락 0 + 필수 필드 누락 0 + 이름 충돌 0 | 부분 — 커버리지 게이트는 배선돼 있으나 **필드 완전성·이름 충돌 검사가 없음** |
| **C4** | **role 라벨 과신** — 선언 라벨을 물리/connectivity 확인 없이 신뢰 | 9, 10, 11, 15, 18 | 물리 판정(`gate==drain`, `kind`, KCL)이 **항상 우선**, role 문자열은 최후 폴백 | `test_role_label_removal_invariance` — `headroom_role`/`gm_id_role`/`L_role`을 **전부 제거해도 결과가 같은지**. 물리가 우선이면 라벨은 결과에 영향이 없어야 한다 | **FAIL** — 같은 소자가 role만 바꿔도 vds가 `cascode`→0.200 / `mirror`→0.300 / 라벨없음→0.600으로 갈린다 |
| **C5** | **게이트가 무엇을 못 보는지 모름** — "통과"가 "볼 수 없어 통과"일 수 있음 | 11 | 각 게이트 docstring에 **검사하지 않는 것**을 명시. 상위 검증기(§7.5)가 하위 게이트의 사각을 덮는다 | `test_gate_docstring_declares_blind_spots` — `check_*`/`verify_*`/`validate_*`/`audit_*` 전수에서 docstring에 "검사하지 않는 것" 절이 있는지 정적 검사 | **FAIL** — 게이트류 19개 중 **4개만** 명시(`check_box_shape`, `audit_theta_root_direction`, `check_symmetry_dispositions`) |
| **C6** | **underdetermined를 반복으로 밀어붙임** — 자유도 부족을 반복으로 풀려다 착시적 수렴/데드락 | 19, 22 | **DOF 사전 진단**(`diagnose_sizing_dof()`)으로 판정. 상호참조는 독립방정식인지 먼저 검산 | `test_dof_catches_incident19_fixture` — 사고19 재현 픽스처(한 vertical_stack의 vds 미지수 2 / KVL 방정식 1)를 진단이 잡는지 | 미배선 — B5대로 진단이 **VDS 미지수·KVL 방정식 축을 세지 않는다** |
| **C7** | **단일 회로로만 검증** — 다른 회로에서 원래 있던 gap이 드러남 | 17 | 파일럿 검증 후 나머지 3개 토폴로지 **실제 실행**까지 완료해야 done | `test_all_four_topologies_run` — 4개 토폴로지를 새 엔진으로 실제 실행해 전역 게이트 통과 | 부분 — 현재 self-test는 "선언 위반 0건"만 보고 **사이징 실행은 안 한다** |
| **C8** | **엔진 우회·무근거 자동동작** — 손계산으로 축약하거나 근거 없이 자동 병합 | 1, 8, 20 | 모든 값은 함수 경유. 자동 병합/제안은 net-user-count 등 **connectivity 증거**를 요구하고, 증거가 없으면 `review_needed`로 표시하고 **파이프라인을 정지**한다 | `test_unevidenced_automerge_stops_pipeline` — 증거 없는 자동제안 픽스처를 넣으면 `review_needed`가 서고 파이프라인이 멈추는지 | 미배선 — `review_needed`는 이 표 밖에 등장하지 않는다(상태값 자체가 아직 없음) |
| **C9** | **중복 복붙** — 같은 로직·상수가 여러 곳에 존재해 한쪽만 고쳐짐 | 24 | **단일 출처 함수**로 통합 | `test_no_raw_duplicated_writes` — 단일 setter 우회(원시 대입)·중복 상수가 남아 있지 않은지 grep 검사 | 시작됨 — v4.3이 §7.3에 vds 원시 대입 grep 테스트를 도입 |
| **C10** | **재계산 비효율** — 같은 스캔을 호출부마다 반복 | 사용자 원칙, `lut-generation-checklist.md` §9 | 스캔 축을 함수 내부로 내리고 캐시 키를 "그 함수가 실제로 읽는 모든 가변 상태"로 | `test_cache_key_covers_mutable_state` — `ctx.sized`만 바꾸고 같은 metric을 호출했을 때 **옛 값이 반환되지 않는지**(CMFB MNA 캐싱 회귀 재현) | 미배선 |

> **이 표를 고쳐 쓴 이유(B11, v4.5)**: v3.0의 원래 표는 방지 장치를 **문장으로만** 적어두었고,
> 실측해 보니 그중 다섯(C3 일부·C4·C5·C6·C8)은 문서 전체에서 **그 표 안에서 딱 한 번씩만**
> 등장하는 빈 약속이었다(`review_needed` 2회 중 1회가 이 표, "전역 유일성"·"connectivity에서
> 유도" 각 1회). **선언만 하고 배선하지 않을 거면 애초에 만들지 않는다**는 원칙에 따라, 각 행에
> **"이게 없으면 방지 장치가 없는 것"이라고 말할 수 있는 테스트**를 지정했다.
>
> 그리고 **지금 돌리면 실패하는 것을 실패한다고 적었다**(C1/C4/C5). 이건 결함 고백이 아니라
> **DoD의 이빨**이다 — §4.1은 이 표의 모든 행이 PASS가 되는 것을 완료 조건으로 삼는다. 반대로
> 테스트를 지정할 수 없는 방지 장치가 나오면 그 행은 폐기하거나 다른 실효 장치로 교체한다.
>
> 부수 정정: v3.0 표의 담당 절 지정 중 **C7의 §5는 정반대 내용**(§5는 "파일럿 1개만"을 명시)
> 이었고 **C10의 §7.6에는 캐시 서술이 없었다**(실제 서술처는 §7.10/§6.1). 담당 절 열을 없애고
> 강제 테스트 열로 대체해 이런 어긋남이 재발하지 않게 했다.

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] `<name>.sizing_spec.json` 스키마가 확정되고 `_TEMPLATE.sizing_spec.json` 스캐폴드로
      문서화됨
- [ ] `current_reuse_telescopic_ota`가 새 스키마 + 새 엔진으로 재사이징되어 instance.json이
      갱신됨
- [ ] **★ (최우선, §3.1 요구사항 6) `verify_node_voltage_consistency(ctx)`가 51소자 전체에서
      Violation 0건** — diode-connected 16개 소자의 자기일관 헤드룸(오차→0)은 이 검증의
      부분집합으로 포함되지만, 그 외 소자의 게이트-내부net VGS 불일치/노드 상호모순도 전부
      확인됨
- [ ] 기존 constraints(gain≥54dB, cmrr/psrr/mismatch/classab) 전부 재확인
- [ ] `cross_check_with_spice()`(sky130 SPICE `.op`)이 rail-lock 없이 수렴하고
      `verify_node_voltage_consistency()`의 LUT 기반 예측과 일치(원래 세션 목표였던 트랜지언트
      검증 재개 가능)
- [ ] **★ (v4.5) §3.3 C1~C10 표의 "강제 테스트" 10개가 전부 PASS** — 각 행이 지정한 테스트가
      `assets/tests/`에 실재하고 통과해야 한다. 지금 돌리면 **C1/C4/C5는 FAIL**이고 C2/C6/C8/C10은
      미배선인데, 그게 정상이다 — 이 표는 현재 상태를 정직하게 적고 완료 조건을 거는 장치다.
      특히 다음 셋은 "그 실패를 직접 재현"하는 형태라 통과하면 방지가 구조적으로 증명된다:
      `test_role_label_removal_invariance`(role 라벨 전부 제거해도 결과 동일),
      `test_order_shuffle_invariance`(처리 순서 셔플해도 결과 동일),
      `test_cache_key_covers_mutable_state`(`ctx.sized`만 바꿔도 캐시가 옛 값을 안 준다)
- [ ] **★ (v4.6, B4) 파일럿 1회 전체 실행 wall-clock ≤ 5분** — 기본 L 정책(bounds 내 LUT 앵커
      전수, 4³=64 combo) 기준 실측 예상 2.9분. 초과하면 곱셈 구조에 예상 못 한 항이 들어온
      것이므로 그 자리를 찾아 보고한다(예: `presolve_warm_start()` 16.5s가 루프 안으로 들어감)
- [ ] **★ (v3.0, C7) 파일럿 외 나머지 3개 토폴로지(folded_cascode/nmcnr_amplifier/
      two_stage_ota)도 새 엔진으로 실제 실행** — self-test 통과만으로는 부족(사고17: 다른 회로를
      돌려야 원래 있던 선언 gap이 드러난다)

### 4.2 Quality Criteria

- 새 함수 추가로 인한 기존 self-test 회귀 0건
- diode-connected 자기일관 해석기가 20회 이내 고정점 반복으로 수렴(발산/진동 없음)

---

## 5. Risks and Mitigation

| Risk | Mitigation |
|------|------------|
| stage 내부 input+cascode 동시결정이 수렴 안 하거나 비현실적 W를 낼 위험 | §7.2 알고리즘의 1~4단계는 각각 기존에 검증된 단일 함수 호출(`search_gm_id_for_role(role="gain")`, LUT 역보간, `size_transistor()`)의 조합이라 개별 단계는 이미 신뢰 가능 — 조합 후 W_bounds 위반 시 기존 `InfeasibleSizingError` 관례를 그대로 따른다 |
| "gain이 주도"로 뒤집으면서 GBW/PM이 실제로 안 맞는 회로가 나올 위험 | `solve_compensation_for_gbw_pm()`은 검증(§4.1 DoD)에 GBW/PM 재확인을 포함해야 함 — 이번 계획 문서에는 명시했으나 구현 단계에서 실제 검증 스텝으로 반드시 실행 |
| 사고4 재발(배분 자체를 결정론화하려는 유혹) | §3.1 요구사항 5번으로 명시적 경계를 문서에 고정 — 구현 시 이 경계를 벗어나는 변경은 별도 승인 필요 |
| 4개 토폴로지 동시 이관 시 범위 폭발 | §2.2 Out of Scope로 파일럿 1개만 우선 명시 |
| §8.4 사이징↔레이아웃 피드백 루프가 반복마다 소자를 재배치하며 조용히 소자를 삭제할 위험(2026-09-04 §1.4 추가 — `known-incidents.md` 사고16: `_layout_result_to_rows()`의 행 이름 카운터가 호출 전역에서 유일하지 않아 무관한 반복끼리 이름이 충돌 → `dict.update()`가 이전 결과를 조용히 덮어써 51소자 중 3개가 실제로 사라진 전례) | §8.4의 반복 피드백 구현 시 행/그룹 이름 생성 카운터가 **전체 파이프라인 호출에 걸쳐 유일**한지(지역 카운터가 아닌지) 명시적으로 검증할 것 — 사고16이 신설한 "repair 이후 재검증 게이트"(`check_stick_diagram_coverage()`) 패턴을 §8.4의 5~6단계(수렴/실패 판정)에도 동일하게 적용해, 반복마다 넷리스트 소자 수가 그대로인지 재확인하는 스텝을 넣는다 |

---

## 6. Impact Analysis

### 6.1 Changed Resources (★ v3.0 재분류 — "무변경 보존"에서 "개선 허용"으로)

P1(전면 재설계 허용)에 따라 v2.x의 **"무변경 재사용"** 분류를 폐기하고 아래 3분류로 재정리한다.
판단 기준은 보존이 아니라 **물리적 정확성 + 조용한 실패 불가능성**이다.

**(가) 개선 대상 — 기존 함수를 고친다** (v2.x에서 "무변경"으로 잘못 묶여 있던 것들):

| 함수 | 현재 문제 | 개선 내용 | 방지하는 클래스 |
|---|---|---|---|
| `resolve_feed_vds()` | 우선순위 체인에 diode-connected 티어가 없어 "누가 먼저 쓰느냐"에 의존 | **티어① `gate==drain` → 고정점 solver**를 체인 안에 명시(§7.3) | **C2** (사고13/19/23) |
| `allocate_stack_headroom()` / `HeadroomPolicy` | `stack_entries`에 `gm_id`가 없어 Jespers 공식이 죽은 코드, 남는 예산 **균등분배**는 물리 근거 없음 | `cascode_fn(entry)` → **`headroom_fn(entry, ctx)`**로 LUT/connectivity 접근 허용, 균등분배 → **gain 기여도(`dA/dVDS`) 가중 배분**(§7.9) | **C1, C4** (사고10) |
| `search_gm_id_for_role()` | L을 고정 인자로 받아 호출부가 L 후보를 밖에서 반복 → 동일 `_idu_scan` 중복 실행 | **`search_gm_id_and_L_for_role()`**로 L축 내부화(스캔 재사용), knee 계산(§7.10)과 목적함수를 한 곳에 | **C10** (P2 효율) |
| `_L_ROLE_MULTIPLIERS`(2.5×/1.2× 상수) | 공정이 바뀌면 knee도 바뀌는데 상수 고정 | **`measure_L_knee()` 실측 호출**로 대체(§7.10) | **C1, C9** |
| `optimize_multistage()` / `topology_fn` | GBW/PM→gm 방향 | **방향 반전**(확정된 gm → Cc/Rz 역산, §7.4 원칙2) | — |

**(나) 그대로 사용 — 물리·수치 계층이라 바꿀 이유가 없음**:
`SemiEmpiricalGmIdLUT`/`vgs_for_gm_id()`/`gm_id_for_vgs()`/`gm_id_to_id_density()`/
`gm_gds_ratio()`, `size_transistor()`/`converge_with_parasitics()`, `load_topology()`/
connectivity 파싱, analog-grammar idiom 탐지, `assign_finger_geometry()`/euler 자동수정/
matching-safety/floorplan, `cmrr_estimate_db`/`psrr_estimate_db`/`pelgrom_mismatch`/
`nulling_resistor_ohm`/`battery_centering_deviation` 등 사후검증 metric,
`_resolve_vertical_group()`의 fixed-point worklist(사고22 해법 그대로),
`device_roles.vds_match_vgs_of`/`gm_id_match_vgs_of`(사고21 primitive).
⚠️ "그대로 사용"은 **보존 의무가 아니라 현재 판단**이다 — 구현 중 물리적 결함이 드러나면 P1에
따라 즉시 개선 대상으로 옮긴다.

**(다) 신규 작성**: `sizing_spec.json` 스키마(§7.1), `_solve_diode_connected_vgs_fixed_point()`,
`gm_id_for_gm_gds_ratio()`, `resolve_stage_sizing()`, `verify_node_voltage_consistency()`,
`cross_check_with_spice()`, `diagnose_sizing_dof()`, `allocate_headroom_budget()`,
`measure_stage_gain_ceiling()`, `redistribute_headroom_by_gain_gradient()`,
`measure_L_knee()`, `L_bounds_from_ft_and_matching()`, `L_candidates_product()`,
`make_cmrr_psrr_feasibility_check()`, `solve_compensation_for_gbw_pm()` +
§8의 5개 파일/harness 구조.

### 6.2 Current Consumers

- `workspaces/run_harness.py` — `optimize_full_circuit_budget()` 단일 진입점 호출자, 신규
  `sizing_spec` 유무로 신/구 경로 분기 필요
- `stick_diagram.py`의 `run_topology_pipeline_with_finger_fixup()` — 사이징 결과(W/L/gm_id)를
  소비하는 후단, 입력 스키마 무관하게 그대로 동작

### 6.3 Verification

§6 절(원본 계획 §6 "검증 계획") 참고 — self-test, 회귀 대조, diode-connected 고정점 수렴,
SPICE 폐루프 재검증 4단계.

---

## 7. Architecture Considerations

### 7.1 새 JSON 스키마 (`<name>.sizing_spec.json`)

```jsonc
{
  "schema_version": "4.0",
  "topology_ref": "current_reuse_telescopic_ota.topology.json",

  "global_spec": {
    "vdd": 1.8,
    // v3.3 -- **면적 제약형**이 기본(사용자 확정): 목적함수는 전력 최소화 하나이고,
    //   면적은 아래 constraints의 area_um2 상한으로 건다. 가중합(alpha:beta) 방식은
    //   가중치를 사람이 지어내야 해 결정론이 깨지는데, 실무에서 면적 예산은 대개 스펙으로
    //   주어지므로 제약으로 거는 편이 자연스럽고 임의성이 없다(§7.9 해법 참고).
    "objective": {"minimize": "power_uA"},
    "closed_loop_accuracy_db": null,
    // §7.6 -- CMRR/PSRR/mismatch는 stage별 배분이 아니라 전역 declared constraint로 선언.
    // 계산 로직은 기존 metric(smallsignal_ratio_db/pelgrom_mismatch) 완전 무변경 재사용.
    "constraints": [
      {"metric": "gain_db",           "op": ">=", "value": 54},
      {"metric": "area_um2",          "op": "<=", "value": 2000},   // v3.3 -- 면적 예산.
                                                                    // v3.4: **생략 가능** -- 생략하면
                                                                    // 엔진이 전력-면적 Pareto front를
                                                                    // 뽑아 제시하고 정지한다(§7.9),
                                                                    // 사람이 고른 값이 여기 기록된다
      {"metric": "cmrr_estimate_db",  "op": ">=", "value": 60},
      {"metric": "psrr_estimate_db",  "op": ">=", "value": 60},
      {"metric": "mismatch_sigma_mV", "op": "<=", "value": 5.0},
      {"metric": "input_noise_nv_rthz", "op": "<=", "value": 30}   // v4.0 신설, 아래 (주) 참고
    ]
  },

  // ── v4.0 복원: metric **정의** 블록 ────────────────────────────────────────
  // v3.x는 topology.json에서 `sizing_roles`를 제거하면서 회로별 metric 스펙(`sense_p`/
  // `sense_n`/`circuit_family`/`tail_device` 등)이 **갈 곳을 잃게** 만들었다 -- 새 스키마가
  // 현행보다 표현력이 낮아지는 상태였다. `constraints[]`가 metric을 이름 문자열로만 참조하므로
  // 그 이름이 무엇을 계산하는지는 여기서 선언한다. `type`은 `_METRICS_REGISTRY` 키이고,
  // 미등록 타입은 엔진이 즉시 ValueError를 낸다(조용한 폴백 없음, §3.2 P1).
  "metrics": {
    "gain_db": {
      // ★ 회로마다 다르다. 파일럿은 stage 합, folded_cascode는 Rout 병렬조합,
      //   nmcnr는 3단 폐형식, two_stage_ota는 전체회로 수치 MNA -- §7.9가 이 선언을
      //   compute_metric()으로 호출할 뿐 식을 알지 않는다(circuit-agnostic 규약).
      "type": "gain_stages_sum",
      "stages": [["M1a","M4a","M2a","M3a"], ["M15","M16"]]
    },
    "cmrr_estimate_db":  {"type": "cmrr_estimate", "circuit_family": "telescopic_class_ab_cmfb",
                          "tail_device": "M5"},
    "psrr_estimate_db":  {"type": "psrr_estimate", "circuit_family": "telescopic_class_ab_cmfb"},
    "mismatch_sigma_mV": {"type": "pelgrom_mismatch", "pairs": "symmetry.matching_pairs"},
    "input_noise_nv_rthz": {"type": "flicker_plus_thermal_sum", "devices": ["M1a","M1b","M4a","M4b"]},
    "area_um2":          {"type": "sum_area"},
    "power_uA":          {"type": "sum_current"},
    "classab_centering_dev_v": {"type": "battery_centering_deviation",
                                "battery": ["M8","M9a","M9b","M10"]}
  },
  // (주) `flicker_plus_thermal_sum`은 엔진에 **이미 등록된 metric**이다. v3.x 계획서는 noise를
  //      한 번도 언급하지 않았는데, 이는 "어려워서 범위 밖"이 아니라 **있는 기능을 떨어뜨린
  //      것**이었다. 게다가 v3.3의 핵심 논리("면적이 실질 상한")가 곧 `W·L`을 조이는 것이고
  //      그건 flicker noise를 직접 악화시킨다 -- 배분을 결정하는 바로 그 제약이 1급 스펙 하나를
  //      최악 방향으로 밀고 있었다. 그래서 목적/제약 어디에도 없던 상태를 제약으로 승격한다.

  // ── v4.0 신설: 구조 선언(옛 theta 중 "값이 아닌 것"들의 새 거처) ──────────
  "structural_declarations": {
    // 옛 A / A_signed feed -- KCL이 강제하는 전류 관계(부호 포함)
    "kcl": [
      {"id": "monticelli_battery", "sum": [["+","M9b"], ["-","M18b"]], "target": 0.0}
    ],
    // 옛 C feed -- diode 스택이 만들어야 하는 기준전압
    "diode_stack": [
      {"id": "cmfb_ref", "members": ["M36a","M36b"], "target_net": "Vcmfb"}
    ],
    // 소자 간 결합(이미 구현된 primitive, §1.4) -- v3.x는 "그대로 재사용"이라 써놓고
    // 정작 담을 자리를 스키마에서 없앴다. 여기가 그 거처다.
    "couplings": {
      "vds_match_vgs_of":   {"M16": "M15"},
      "gm_id_match_vgs_of": {"M16": "M15"}
    },
    // device_roles에 있던 나머지 실측 필드들의 거처(파일럿 실측: vs 44개,
    // budget_reference_device 7개, same_as_device 4개)
    "per_device": {
      "vs":                      {"M2a": 0.25, "M15": 0.806},
      "budget_reference_device": {"output_stage_a": "M15"},
      "same_as_device":          {"M1b": "M1a"}
    }
  },

  // ── v4.0 신설: 피드백 루프(CMFB, gain-boost 보조앰프 등) ──────────────────
  // v3.x 스키마에는 CMFB를 담을 필드가 **하나도 없었다**. 파일럿이 CMFB 루프를 갖고 있고
  // 그 사이징 노브가 옛 theta(N_cmfb_bw / N_cmfb_bw_mirror / r_cmfb_vocdes / kcl_tail_M38)에
  // 있었으므로, theta를 없애면서 이 정보가 통째로 사라질 뻔했다.
  "feedback_loops": [
    {
      "id": "cmfb",
      "devices": {"sense": ["M36a","M36b"], "amp": ["M37a","M37b"], "tail": ["M38"]},
      "targets": {"loop_gain_db": 30, "PM_deg": 60, "bandwidth_hz": 2e6},
      "note": "자체 안정성 요구가 있는 별개 루프 -- stage도 bias_device도 아니다"
    }
  ],

  "stages": [
    {
      "id": "stage1_input",
      "devices": {
        "input":   ["M1a","M1b","M4a","M4b"],
        "cascode": ["M2a","M2b","M3a","M3b"],
        "load":    [],
        "tail":    ["M6","M7","M5"]   // §7.6 -- ID를 KCL로 정할 뿐 gain엔 기여 안 함,
                                       // gds가 CMRR/PSRR을 좌우(role="load"로 사이징)
      },
      "ID_source": {"type": "kcl"},
      // v3.1 -- gain_budget_db는 입력이 아니라 §7.9 Phase 2가 유도하는 **출력**이다.
      // 논문 재현 등 특정 배분을 강제할 때만 아래 override를 쓴다(기본 null).
      "gain_budget_db_override": null
    },
    {
      "id": "stage2_output",
      "devices": {"input": ["M15","M16","M25","M26"], "cascode": [], "load": [], "tail": []},
      "ID_source": {"type": "kcl"},
      "gain_budget_db_override": null,
      "driving_spec": {
        "CL_farad": 1e-12,
        "slew_rate_v_per_us": null,
        "settling_time_ns": {"up_max": 40, "down_max": 40}
      }
    }
  ],

  "compensation": {
    "function": "solve_compensation_for_gbw_pm",
    "targets": {"GBW_hz": 5e6, "PM_target_deg": 60},
    "solves_for": ["Cc", "Rz"],
    "stage_gm_ref": ["stage1_input", "stage2_output"]
  },

  "headroom": {
    "policy": "post_gm_id_self_consistent",
    "vertical_stacks": [
      {"id": "output_stage_a", "members": ["M15","M16"], "vdd_kvl": true}
    ]
  },

  "bias_devices": [
    {"name": "M18_bg", "role": "diode_reference",
     "ID_source": {"type": "ideal_source_ref", "ref": "Iref"},
     "gm_id_policy": "min_gm_id_in_bounds"}
  ]
}
```

**핵심 변경 요지**:
- **(v3.1 확정)** `stages[].gain_budget_db`는 **입력이 아니라 출력**이다 — 총 gain 목표는
  `global_spec.constraints`의 `gain_db >= X` 하나로만 주고, stage별 배분은 §7.9 Phase 2가
  `A_i,max` 실측 + root current 1-D 해찾기로 **유도**해 `instance.json`/리포트에 기록한다.
  특정 배분을 강제해야 하는 예외(논문 재현 등)만 `stages[].gain_budget_db_override`로 지정한다.
  근거: 문헌 정본(`gm-id-methodology.md` §6.4)도 gain을 스펙이 아니라 **등고선(contour)**으로
  다루며, 스펙은 GBW/PM이고 자유 축은 (gm/ID₁, gm/ID₂)다.
- `device_roles.headroom_role` 폐기 → §7.3 헤드룸 해석기가 connectivity로 직접 판정.
- `device_roles.gm_id_role` 폐기(gain stage 소속 소자는 §7.2로 유도) — bias-gen 소자만
  `bias_devices[].gm_id_policy`로 단순 존속(strong-inversion 최소화, 기존 role="matching"과
  동일 근거).
- ~~`sizing_roles.theta`의 A/B/C/D taxonomy **전면 폐기**(v3.1)~~ → **v4.0에서 사용자 확정으로
  축소: 폐기 대상은 "자유 탐색 변수"뿐이고, 구조 선언은 새 스키마로 이관해 존속한다.**

  > **왜 축소했나**: v3.1의 "전면 폐기"는 **자유 탐색 변수와 구조 선언을 혼동**했다. 파일럿의
  > theta 22개 중 `A_signed`(Monticelli 부호 있는 KCL 합), `C`(diode-stack 타깃),
  > `metric_stage_budget`(어느 소자군이 어느 metric의 어느 stage인지), servo `B`(CMFB 대역폭)는
  > **값이 아니라 회로 구조를 서술하는 선언**이다. 폐기하면 CMFB 루프·class-AB 배터리·bias
  > 체인 정보가 **대체 표현 없이 소실된다** — 이건 이미 겪은 회귀와 같은 클래스다
  > (`compensation`/`replica`/`metric_stage_budget`/B타입을 확인하지 않은 자동채움이 theta
  > 탐색을 조용히 무력화한 세션33 사례).

  | theta feed 타입 | 성격 | v4.0 처분 |
  |---|---|---|
  | 자유 탐색 변수(`L_cascode`, `k_i` 등 bounds가 열린 것) | 값 | **폐기** — `gm_id_i`가 유일한 자유 축(§7.9) |
  | `A` / `A_signed`(KCL 합, 부호 포함) | 구조 | **존속** — `sizing_spec.json`의 `structural_declarations.kcl[]` |
  | `C`(diode-stack 타깃) | 구조 | **존속** — `structural_declarations.diode_stack[]` |
  | `metric_stage_budget` | 구조 | **존속** — `metrics[].stages`로 흡수(아래 스키마) |
  | servo `B`(CMFB 대역폭 등 피드백 루프) | 구조 | **존속** — `feedback_loops[]`(신설) |
  | `gm_target_convention` | 구조 | **존속** — `compensation.gm_convention` |

- `sizing_roles.theta`의 자유 탐색 변수 부분은 폐기 — 배분도 유도되므로 "자유 theta"로
  남길 항목이 없다. 남는 자유도는 §7.6의 `L_combo`와 §7.9의 VDS 재배분 두 축뿐이고, 둘 다
  선언이 아니라 엔진이 탐색·해찾기로 정한다.

### 7.2 신규 사이징 알고리즘 (stage 1개 기준) — §1.4의 §13.1/§13.2/§13.7 반영으로 개정

```
입력: stage.gain_budget_db, stage.devices.{input,cascode,load}, ID(KCL로 이미 확정)

1. cascode 소자(gm이 ro에 곱해서 기여하는 진짜 캐스코드): L 후보군에서 gm/gds 최대화 지점을
   스캔(기존 search_gm_id_for_role(role="gain") 재사용) → (L_cas, gm_id_cas) 확정, ro 기여분
   = gm_gds_ratio(gm_id_cas, L_cas, vds_cas) 확정.
1'. load 소자(캐스코드가 아니라 ro 자체로만 기여하는 단순 전류원 — §13.7 신규 구분,
    **§7.2 원안에서 빠져 있던 부분**): 같은 스캔을 gm_gds_ratio 대신 gds 최소화 기준으로
    실행(이미 구현된 role="load", search_gm_id_for_role()에 존재) — gm/gds 최대화와 gds
    최소화는 서로 다른 물리량이라(§13.7 실측: "gain" 적용 시 ro가 진짜 최댓값의 절반에 그침)
    load를 cascode와 같은 기준으로 최적화하면 안 된다. stage.devices.cascode/load 서브분류
    (§7.1 스키마)는 바로 이 구분을 스키마 레벨에서 강제하기 위한 것.
2. 필요한 input 쪽 intrinsic gain = 10^(gain_budget_db/20) / (cascode+load가 만든 ro 부스트) →
   input의 목표 gm/gds_effective 역산.
3. input 소자: gm_gds_ratio(gm_id, L, vds)가 2번 목표값과 같아지는 gm_id를 LUT 이분탐색으로
   직접 역산(신규 gm_id_for_gm_gds_ratio()).
4. size_transistor()로 W 확정(기존 함수 그대로).

output stage 추가: driving_spec이 있으면 ID_final = max(KCL ID, slew_rate_target*CL_farad)로
ID 상향 후 위 1~4를 그 ID로 실행 — 같은 gm_id에서 ID만 커지면 gm도 커지므로 gain은 여유가
생기는 방향(배분과 충돌하지 않음).
```

캐스코드/load 둘 다 없는 단순 stage는 "부스트=1(0dB)"로 두면 2/3단계가 자연스럽게 특수 케이스로
커버된다.

**⚠️ 이 순서(1→1'→2→3)가 옳은 이유, 그리고 언제 안 통하는지(§13.1/§13.2 근거)**: 1/1'단계가
"각 소자 독립 최적화"인데도 정당한 이유는, cascode/load의 목적함수(gm/gds 또는 gds)가 **다른
소자와 결합되지 않은 자기 자신만의 함수**이기 때문이다(ID가 이미 고정, 목적함수가 자기
자신만의 (L,gm_id)의 함수라 곱셈적으로 나중에 합쳐도 전역 최적과 같다). 반면 §13.1이 실측한
"결합 최적점을 놓치는" 실패 사례(M15/M16, gm_id_match_vgs_of로 VGS가 강제 동일화된 쌍)는
**목적함수 자체가 다른 소자의 선택에 의존**하는 경우다 — 이런 결합(주로 `vds_match_vgs_of`/
`gm_id_match_vgs_of`로 명시적으로 선언된 관계, 대개 stage 경계를 넘어서 발생, §1.4 참고)가
있는 소자쌍은 이 순차 알고리즘이 아니라 §13.1의 결합 목적함수 조인트 스캔으로 별도 처리해야
한다 — stage 내부 cascode/load/input 관계는 이 결합이 없는 게 일반적이라 순차 알고리즘이
맞지만, 스키마 작성 시(§8.3) `vds_match_vgs_of`/`gm_id_match_vgs_of`가 선언된 소자가 우연히
같은 stage 안에 들어가면 이 예외를 적용해야 함을 `resolve_stage_sizing()` docstring에
명시할 것.

### 7.3 헤드룸(VDS) 해석기 재설계 — v2.0(기존 인프라 재사용) → **v3.0(우선순위 체인에 diode 티어 신설, C2 근본 제거)**

**원안(v1.0)은 `allocate_stack_headroom()`/`HeadroomPolicy`를 통째로 새 함수로 대체하려 했다.
그런데 자산화 과정에서 이미 이 문제의 절반(중복 하드코딩 제거, 상호참조 스케줄링)이 풀려있는
기존 인프라가 있음이 드러났다 — 이번 개정은 그 인프라를 재사용해 신규 코드를 최소화한다:**

- `resolve_feed_vds(name, declared_vds, ctx)`(사고24, 이미 구현됨) — 소자 하나의 vds를 정하는
  **우선순위 체인**: ① `ctx.sized[name]`에 이미 vds가 있으면 그 값을 존중(다른 메커니즘이
  먼저 정함) ② `declared_vds`(spec 명시값) ③ `_feed_vds_fallback()`(role 기반 폴백).
- `_resolve_vertical_group(vsid)`(사고22, 이미 구현됨) — 여러 그룹이 서로 다른 멤버를 통해
  맞물리는 상호참조 헤드룸 문제를 위한 **fixed-point worklist**(`_HeadroomDependencyNotReady`
  예외로 "아직 준비 안 됨"을 표시하고 여러 pass에 걸쳐 재시도, "ctx.sized에 vds가 채워진 소자
  수가 이번 pass 동안 늘었는가"로 진전 판정).

**⚠️ v3.0 재개정 — 위 v2.0안의 "순서 의존" 우회를 폐기한다**: v2.0은 "diode solver가
`ctx.sized`에 **먼저** 기입하면 우선순위①이 지켜준다"로 설계했는데, 이는 **"누가 먼저 쓰느냐"에
결과가 달라지는** 구조이고 그건 사고13/19/23이 반복해서 당한 바로 그 취약성(C2)이다. P1(전면
재설계 허용)에 따라 **`resolve_feed_vds()`의 우선순위 체인 자체를 고쳐** 순서 의존을 제거한다:

```
resolve_feed_vds(name, declared_vds, ctx) -> float(vds):     # ★ v3.0 개선
  티어① connectivity(name).gate == connectivity(name).drain  ← 신설 최우선
         -> _solve_diode_connected_vgs_fixed_point(...)      (물리가 강제하는 값, 협상 불가)
  티어② ctx.sized[name]["vds"]가 이미 있으면 존중            (기존 ①)
  티어③ declared_vds(spec 명시값)                            (기존 ②)
  티어④ _feed_vds_fallback(role 기반)                        (기존 ③ -- KVL/KCL 그룹 비소속이
         확인된 소자에만 허용, C1)
```
이러면 **호출 순서와 무관하게** diode-connected 소자는 항상 물리적으로 옳은 값을 받는다.
`_resolve_vertical_group()`의 fixed-point worklist(사고22)는 그대로 두고, 이 티어①이 그
worklist의 pre-pass 자리를 대신한다.

**신규 함수는 여전히 하나뿐이다**:

```
_solve_diode_connected_vgs_fixed_point(gm_id, L, vs, lut) -> float(vds)
    # 이번 세션 스크래치패드 node_dc_propagate.py에서 프로토타입 검증 완료.
    # gate==drain(connectivity(device).gate == connectivity(device).drain, role 라벨이
    # 아니라 load_topology()가 파싱한 netlist로 직접 판정)인 소자에 대해,
    # vds* = lut.vgs_for_gm_id(gm_id, L, vds*, vs)를 만족하는 고정점을 반복으로 푼다.

호출 시점: §7.2가 diode-connected 소자의 gm_id를 확정한 직후(bias_devices든 stage 소속이든
무관 — connectivity 기반 판정이라 소속과 무관하게 동작), ctx.sized[name]["vds"]에 즉시 기입.
그 이후 헤드룸 루프(_resolve_vertical_group)는 이 값을 resolve_feed_vds() 우선순위①로 그대로
존중하며 정상 동작. (v4.0 정정: 아래 §7.9가 균등분배를 대체하므로 HeadroomPolicy는
결국 손대야 한다 — v2.0의 "교체할 필요 없음"은 사실이 아니었다.)
만약 diode-connected 소자끼리 서로 다른 멤버를 통해 맞물리는 경우(사고22 Monticelli류 패턴이
diode-connected 소자 간에도 나타날 가능성)가 생기면, 새 알고리즘을 발명하지 말고 기존
_resolve_vertical_group()의 fixed-point worklist에 이 pre-pass를 끼워넣는 방식으로 확장할 것
(사고22의 교훈: "새 계산 로직을 발명하기 전에 기존 primitive로 스케줄링 순서만 고치면
풀리는지부터 손 시뮬레이션할 것").
```

**정리(v3.0)**: 신규 함수는 `_solve_diode_connected_vgs_fixed_point()` 하나,
**개선 대상**은 `resolve_feed_vds()`(티어① 추가) —
`_resolve_vertical_group()`의 worklist는 그대로 쓴다. v2.0이 적어둔 "무변경 재사용" 표현은
P1 확정으로 폐기(§6.1 (가) 참고).

#### ★ B4 해소 — 실행시간 예산 (v4.6, 2026-09-08 실측)

v4.5까지 계획에는 **실행시간 예산 항목 자체가 없었다**. §7.6이 L_combo 전수 스캔을 요구하고
§7.9가 그 위에 중첩 루프를 얹는데, 곱이 얼마인지 아무도 세지 않았다. 직접 쟀다.

**단위 비용 실측**(파일럿 51소자, 웜스타트가 찾은 feasible 지점 근방에서 L만 흔들어 12회):

| 항목 | 실측 | 비고 |
|---|---|---|
| `_build_theta_evaluator()` 빌드 | 69 ms | 1회성 |
| `presolve_warm_start()` | **16.5 s** | ★ 1회성인데 크다 — L_combo 루프 **안**에 들어가면 안 된다 |
| **전체 평가 1회**(51소자 사이징+헤드룸+전 metric) | **274.5 ms** | ← **L_combo 단위 비용의 진짜 값** |
| `find_optimal_sizing()` 1회(stage 하나, L 고정) | 3.15 ms | 참고 — 이걸로 예산을 세면 **틀린다**(아래) |
| 전역 게이트(cmrr+psrr) | 0.72 ms | §7.6 B2 |
| IDu 스캔 캐시 효과 | **5.0배** | 새 LUT 첫 호출 59.3 ms → 이후 11.9 ms (C10이 실물로 작동 중) |

> **단위를 잘못 잡으면 예산이 두 자릿수 틀린다**: "L_combo마다 gain stage 2개만 사이징"으로 세면
> 6.3 ms지만, **B2에서 확인했듯 전역 게이트는 51소자 전부가 사이징돼야 돈다**. 따라서 combo 단위
> 비용은 stage 사이징이 아니라 **전체 평가 1회(274.5 ms)**다. 약 44배 차이다.

**L 자유도는 3개**(`L_cascode`/`L_stage2out_p`/`L_stage2out_n`, bounds 전부 `[0.15, 1.0] µm`).

| L 후보 정책 | L_combo | 전수 스캔 | 중첩(레이아웃 5회 × VDS 2회) |
|---|---|---|---|
| **knee 창 3앵커**(v4.7 기본) | 3³ = **27** | **7.4 s** | **74 s (1.2분)** |
| bounds 내 LUT 앵커 4개 | 4³ = 64 | 17.6 s | 175.7 s (2.9분) |
| LUT 전체 앵커 7개 | 343 | 94 s | 15.7분 |
| 0.05 µm 등간격 ~11점 | 1,331 | 6.1분 | 61분 |
| densify 41점 | 68,921 | **5.3시간** | 53시간 |

**확정 정책**:

1. **기본은 "knee 창 전수 + 경계 검사"**다(v4.7 개정, 위 절 참고) — 파일럿에서 **1.2분**.
   ~~bounds 내 앵커 전수(2.9분)~~보다 싸면서 면적 제약이 걸린 정상 조건에서 **전수와 동일한 답**을
   준다(손해 0.00%). 경계 검사가 있어 §7.7 R4의 "조용한 지름길 금지"와도 양립한다.
2. **`dense_candidates()` densify는 기본 금지**한다. 5.3시간은 설계 반복 도구로 쓸 수 없다.
   정말 필요하면 **2단계 정밀화**(앵커 전수 → 최적 근방만 densify)를 쓰되, `IDu(L)`가 비단조라는
   §7.10 반례 때문에 **전역 최적을 놓칠 수 있는 근사**이며 그 사실을 리포트에 찍는다(§3.2 P1).
3. **`presolve_warm_start()`(16.5 s)는 L_combo 루프 **밖**에서 1회만** 호출한다. 루프 안에 들어가면
   64 combo × 16.5 s = 17.6분이 여기서만 추가된다.
4. **infeasible combo는 정상이다** — 실측에서 12개 중 2개가 `InfeasibleSizingError`였다. 루프는
   그것을 세어 리포트하고 계속 진행하되, **전부 infeasible이면** §7.6(4) 상위 수단으로 승격한다.
5. **v3.4 Pareto 12점 스윕은 이미 사라졌다**(v4.2) — DP가 면적 bin별 비지배 집합을 한 번의 전파로
   주므로 12를 곱할 이유가 없다. 곱셈 구조에서 이 항이 빠진 것이 예산을 감당 가능하게 만든 큰 요인이다.

**DoD 측정 항목 신설**: 파일럿 1회 전체 실행 wall-clock **≤ 5분**(기본 정책 기준). 초과하면
곱셈 구조 어딘가에 예상 못 한 항이 들어온 것이므로 그 자리를 찾아 보고한다.


#### ★ L 탐색 범위 — knee 창 + 경계 검사 (v4.7, 2026-09-08 실측)

"LUT 전체를 훑지 말고 knee 근방만 최소 탐색해야 하는 것 아닌가"라는 지적을 받고, **최적 L이
실제로 어디에 오는지** LUT 전 앵커(7개 × 3그룹 = 343 combo)를 전수로 돌려 확인했다.

**결과 — 면적 제약이 걸리느냐에 따라 답이 뒤집힌다**:

| 면적 예산 | feasible | 전수 최적 L(µm) | knee 창(≤0.5µm, 27 combo) 손해 | 최적이 창 밖? |
|---|---|---|---|---|
| 무제약 | 114 | `[0.5, 0.15, **1.5**]` | +1.24% | **예**(`L_stage2out_n`) |
| ≤ 500 µm² | 85 | `[0.5, 0.15, **1.5**]` | +1.24% | **예** |
| **≤ 200 µm²**(v3.3 정신) | 26 | `[0.5, 0.15, 0.5]` | **+0.00%** | **아니오 — 창 안이 곧 전수 최적** |

**면적 제약이 제대로 걸리면 최적이 knee 창 안으로 들어온다.** 상위 10개 해의 L 분포도 함께
이동한다 — 무제약에서는 `{0.15:10, 1.5:7, 4.0:7}`로 큰 L을 활발히 쓰지만, `≤200µm²`에서는
`{0.15:7, **0.35:9**, 0.5:6, 1.0:6, 1.5:2}`로 **0.35µm가 최다**가 되고 4.0µm는 사라진다.
0.35µm는 §7.10이 예측한 knee(2~3×L_min = 0.30~0.45µm) **한가운데**다 — §7.10의 knee 이론이
면적 제약 하에서 실측으로 확증된 것이다.

**부수 관찰**: 전력 스프레드는 454.1~484.4 µA로 **6.7%**뿐인데 면적 스프레드는 47.4~1901.6 µm²로
**40배**다. 즉 **L 선택은 전력이 아니라 면적을 정한다**. 면적을 제약으로 걸지 않으면 L 탐색은
사실상 아무 신호도 못 받고, 그래서 큰 L로 흘러간다.

**확정 정책 — knee 창에서 시작하되 경계를 검사한다**:

```
1) 창 초기값 = measure_L_knee() 결과를 포함하는 LUT 앵커들 (파일럿: 0.15/0.35/0.5, 3^3=27 combo)
2) 창 안에서 전수 스캔(§7.7 R4 준수 -- 창 안에서는 지름길이 없다)
3) ★ 경계 검사: 선택된 L 중 하나라도 **창의 가장자리 앵커**면 창을 한 칸 넓혀 재실행
   · 이미 평가한 combo는 캐시에서 재사용(C10) -- 증분만 새로 돈다
4) 어느 축도 가장자리에 없으면 정지. 그 사실을 리포트에 찍는다("창 내부점에서 수렴")
```

**왜 이게 지름길이 아닌가**: §7.7 R4가 금지한 것은 "단조성을 가정해 스캔을 건너뛰는 것"이고,
그 근거는 §13.7의 M107 26배 악화였다. 여기서 좁히는 근거는 가정이 아니라 **경계 검사라는
사후 검증**이다 — 창이 좁았으면 최적이 가장자리에 붙고, 그러면 자동으로 넓어진다. 즉
**틀리면 조용히 틀리는 게 아니라 스스로 드러난다**(§3.2 P1).

**비용**: 27 combo × 274.5 ms = **7.4 s**(전수 343의 12.7배 절감), 중첩(레이아웃 5회 × VDS 2회)
포함 **1.2분**. 면적 제약이 정상적으로 걸린 경우 경계 검사가 발동하지 않으므로 이 값이 실제
기본 비용이다. 무제약이면 확장이 발동해 전수에 근접하는데, 그건 **면적 예산을 선언하지 않은
대가**이고 §7.9의 Pareto fallback이 이미 그 상황을 다룬다.


#### ★ B2 해소 — metric은 3티어이고, 게이트도 3티어여야 한다 (v4.4, 2026-09-07)

§2.1은 `make_cmrr_psrr_feasibility_check()`를 `make_matching_feasibility_check()`와 **"동일
패턴"**으로 만들자고 했다. 실측해 보니 **그 패턴은 CMRR/PSRR에 원리적으로 적용 불가**다.

**왜 mismatch는 되고 cmrr은 안 되는가**: `pelgrom_mismatch`는 `estimate_mismatch_sigma(
vth0_slope, W, L)`이라는 **닫힌 식**이라 그 stage의 (W, L)만 있으면 계산된다. 반면
`smallsignal_ratio_db`는 `_full_circuit_devices()`를 거치는데, 그 함수는 **topology.json의
모든 소자**가 `ctx.sized`에 있어야 하고 없으면 즉시 `KeyError`를 던진다. L_combo 루프는
stage 하나를 사이징하는 중이므로 그 시점에 다른 stage/bias 소자는 아직 존재하지 않는다.

**실측**(파일럿 13개 metric 전수, stage1 8소자만 사이징한 ctx로 호출):

| 티어 | 뜻 | metric | 1회 비용 |
|---|---|---|---|
| **T1 stage-local** | 그 stage 소자만 있으면 계산됨 | `power_uA`, `area_um2`, `mismatch_sigma_mV`, `noise_v_rthz` | 0.002~0.006 ms |
| **T2 stage-분해가능** | Σ(stage별 항), 각 항은 자기 stage만 필요 | `gain_stages_sum` | 0.003 ms |
| **T3 기약 전역** | 전체 netlist MNA / stage를 가로지르는 노드 | `cmrr_estimate_db`, `psrr_estimate_db`, `gain_full_circuit_db`, `classab_centering_dev_v`, `vg15_level_v`, `vop1_level_v`, `rz1_ohm`, `rz2_ohm` | 0.15~0.29 ms |

> T2는 실측으로 **정확히** 분해된다: stage별 개별 평가 합 56.9842 dB = 전체 평가 56.9842 dB
> (차이 `0.00e+00`). 즉 `gain_stages_sum`을 쓰는 회로에서는 §7.9의 DP가 **대리 함수가 아니라
> 진짜 metric을 분해해서** 쓸 수 있다.
>
> 반대로 `folded_cascode_gain_db`/`nmcnr_gain_db`/`smallsignal_gain_db`를 쓰는 나머지 3개
> 토폴로지는 gain이 **T3**다. 그 경우 DP는 LUT의 `gm_gds_ratio`를 **대리(proxy)**로 쓰고
> **판정 권한은 전역 게이트에** 있다 — 둘이 어긋나면 그 L_combo를 버리고 다음으로 간다(§7.6(4)).
> 이 이원성을 숨기지 않고 리포트에 "DP 예측 vs 전역 게이트 실측"을 나란히 찍는다.

**게이트 구조(§7.6(3) 재작성)**:

```
for L_combo in L_candidates_product(...):          # 면적 오름차순, 전수(§7.7 R4)
    for stage in stages:
        find_optimal_sizing(..., extra_feasible=make_stage_local_check(T1, T2))
        # ^ T1/T2만 여기서 판정한다. T3를 여기 넣으면 KeyError -- 원리적으로 불가.
    if not all_devices_sized(ctx):  continue
    report = check_global_gates(ctx, metrics, constraints)      # 신규, T3 전용
    if report.ok:  return ctx, report
    record_failure(L_combo, report.violations)                  # 어느 제약이 왜 깨졌는지
# 전부 실패 -> §7.6(4) 상위 수단(Phase 1 VDS 재배분)으로 승격
```

**비용은 문제가 아니다**(P-c의 numpy MNA 전환 덕분): T3 게이트 1회(cmrr+psrr+전체회로 gain)가
**0.72 ms**다. L 앵커 7점·3그룹(343 combo)이면 0.25초, densify 41점 3그룹(68,921 combo)이라도
50초다. 병목은 게이트가 아니라 **combo마다 도는 stage 사이징**이며 그건 B4에서 따로 다룬다.
(측정 시 동일 입력 반복이 캐시에 걸리지 않도록 gm/gds를 매번 흔들어 쟀다 — 캐시 히트와의 차이는
0.32 vs 0.34 ms로 유의하지 않았다.)

**§2.1 정정**: `make_cmrr_psrr_feasibility_check()`는 **삭제한다**(구성상 불가능한 함수를
계획에 남겨두면 구현자가 그걸 만들려다 막힌다). 대신 `check_global_gates()`를 신설한다.


#### ★ 면적 제약이 조용히 깨지던 이유 — 결함 2개 해소, 1개 발견 (v4.19, 2026-09-08)

재탐색을 돌리려고 `area_um2`를 제약으로 걸었는데, **제약을 걸어도 지켜지지 않았다**.
`area_um2 <= 900`을 선언했는데 결과가 1050.40µm²인데 "성공"으로 나왔다. 추적하니
**두 개의 독립적인 결함**이었고, 그 과정에서 세 번째를 찾았다.

**(1) B17 -- 엔진이 매칭 쌍에 L만 전파하고 gm_id는 전파하지 않았다** (해소).

`pairs_meta` 루프는 L을 꼼꼼하게 다룬다 -- 한쪽만 있으면 복사, 둘 다 다르면
`_AUTHORITATIVE_L_SOURCES`로 우선순위를 가리고, 그것도 안 되면 명시적으로 실패한다.
**그런데 gm_id에는 그 대응물이 아예 없었다.** VDS는 `same_as_device`/vertical stack이 따로
강제하고 W는 gm_id에서 유도되므로, 결국 **gm_id 하나만 무방비**였다.

전수 조사(`tests/probe_matching_pair_divergence.py`): 매칭 쌍 21개 중 **6개가 갈린다**.
그중 3쌍은 `L/ID/vds/vsb`가 전부 같은데 gm_id만 다르다:

| 쌍 | gm_id | W(µm) | 사이징 경로 |
|---|---|---|---|
| M2a/M2b | 15.0 / **2.5** | 24.52 / 1.11 | `metric_stage_budget` vs `..._vds_deferred` |
| M3a/M3b | 15.0 / **7.5** | 4.33 / 1.02 | 같음 |
| M37a/M37b | 17.23 / **9.5** | 5.00 / 1.01 | `gm_target_convention` vs `L_role` |

한쪽은 권위 있는 출처가 확정하고 다른 쪽은 `gm_id_role` 루프가 **독립 탐색**해서 갈린다.
그 뒤 레이아웃의 matching-safety 복구가 둘을 같게 맞추는데(둘 다 104.036µm -- **원래 값
둘 다보다 크다**) 그러면서 면적이 21% 늘었다.

**수정**: L 전파 루프와 **같은 구조**로 gm_id 전파를 추가했다(`gm_id_match_vgs_of`
2차 pass 직후). 적용 범위는 **`L/ID/vds/vsb`가 전부 같은 쌍**으로 좁혔다 -- 같은
동작점이면 VGS도 같아야 하므로 gm_id가 다를 수 없다. gm_id를 물려받을 때 W/gm/gds를
다시 계산한다(안 그러면 gm_id만 바뀌고 나머지가 옛 값으로 남아 더 나쁜 불일치가 된다).

효과: 갈리는 쌍 6→3개, **레이아웃 복구가 더 이상 W를 건드리지 않고**(모든 쌍에서
W' == W), 총 면적 1050.40 → 936.38µm²(−10.9%), diode 외 35개 384.86 → 237.56µm²(−38%).
gain은 75.39 → 65.75dB로 내려갔는데, 이전 75.39가 **잘못된 사이징(M2b가 gm_id=2.5)의
산물**이었기 때문이다.

**(2) B18 -- 레이아웃 재검증이 전역 metric을 통째로 건너뛰었다** (해소).

B17을 고친 뒤에도 제약은 깨졌다. 이번엔 M2a/M2b가 fixup **전**에 W가 같은데(24.515
둘 다) 레이아웃이 **둘 다 99.785µm로 함께 키운다**(+150.54µm²).

**W가 커지는 기전 자체는 정당하다**: `_sync_finger_fixup()`이 `w = n_fingers * finger_w`로
W를 다시 쓴다. euler/common-centroid 배치를 위해 핑거를 늘리면 폭은 그대로 두고 개수만
늘리므로 W가 비례해 커진다. 레이아웃이 실제로 요구하는 것이다.

**진짜 결함은 재검증이 그 결과를 안 본다는 것**이다. `revalidate_finger_override()`에
재검증이 이미 있는데 "영향받는 metric만 다시 계산한다"는 최적화가 이렇게 돼 있었다:

```
affected = {m for m, spec in metrics_specs.items()
            if _collect_device_refs(spec, known_names) & set(overrides)}
```

`_collect_device_refs()`는 **spec에 이름이 적힌 소자**만 모은다. 그런데 `area_um2`의
선언은 `{"type":"sum_area","unit":"um^2"}`로 `devices` 키가 없고, 계산기는
`spec.get("devices") or list(ctx.sized.keys())`로 **전 소자**를 쓴다. 참조가 빈 집합이라
교집합이 비고, **"무관"으로 분류돼 건너뛴다.**

전수 측정(`tests/probe_revalidation_scope.py`, 파일럿 17개 metric):

| 분류 | metric |
|---|---|
| 전 소자를 쓰는데 건너뜀 **6개** | `power_uA`**(목적함수!)**, `area_um2`, `mirror_ratio_error_pct`, `supply_current_uA`, `kcl_residual_uA`, `stack_headroom_slack_v` |
| 소자 미명시로 건너뜀 **3개** | `cmrr_estimate_db`**(제약!)**, `psrr_estimate_db`**(제약!)**, `gain_full_circuit_db` |

**선언된 제약 5개 중 `gain_db` 하나만 재검증되고 있었다.**

**수정**: 판단 방향을 뒤집어 **metric을 전부 다시 계산**한다. "참조가 안 보이면 무관"이
아니라 **독립임을 적극적으로 확인했을 때만 건너뛰고, 모르면 다시 계산한다**(§3.2 P1).

비용은 먼저 재었다(메모리 규칙: 수정마다 재계산 비효율 점검):

    재검증 호출            8회 (파일럿 1회 최적화)
    17개 metric 전부 재계산  1.6ms (캐시 비운 최악 조건)
    추가 비용              0.016s / 233s = **0.01%**

이 최적화는 **아끼는 게 없으면서 버그만 숨겼다**. MNA metric이 싼 것은 소신호 MNA를
numpy로 전환한 덕(6.1배)이고, `_open_loop_gains_cache`의 키에 실제 gm/gds가 들어 있어
(세션31) 사이징이 바뀌면 자동 무효화된다 -- `_dc_replace`가 캐시를 새 ctx로 옮겨도 안전하다는
것도 확인했다.

**효과 -- 면적 제약이 실제로 지켜진다**:

| 면적 예산 | 수정 전(위반) | 수정 후(만족) | power_uA | gain_db |
|---|---|---|---|---|
| 1000 | 1057.66 | **988.30** | 252.89 | 75.28 |
| 900 | 983.77 | **845.05** | 242.36 | 69.42 |
| 800 | 943.42 | **792.87** | 230.38 | **56.08** |
| 700 | 실패 | 실패 | — | — |

**달성 가능한 면적 하한이 700~800µm² 사이에 있다.** 800µm²에서 gain 56.08dB로 목표 54dB
대비 여유가 **2.08dB뿐**이라 이 설계는 실제로 빡빡하다.

**(3) B19 -- 미러 3그룹의 VGS가 물리적으로 불가능하게 벌어져 있다** (미해결).

B17에서 손대지 않은 3쌍을 조사했다(`tests/probe_ratio_pair_analysis.py`).
**세 그룹 모두 게이트와 소스를 공유하는 진짜 전류미러다**(순수 connectivity 사실):

    M18_bg/M8/M13/M17/M22/M60/M61  PMOS  gate=Vbias1  source=vdd (M18_bg가 diode 레퍼런스)
    M10/M12/M19/M21                NMOS  gate=Vbias4  source=gnd

즉 각 그룹 안에서 VGS가 KVL로 강제 동일해야 하는데, 사이징은 VGS를 **최대 464mV**까지
벌려놓았고 미러 규약(`ID비 == W비`)도 전부 깨다(M8은 1530배 어긋남). "의도된 미러비"가
아니라 **깨진 미러**다. 세션38이 M203/M204에서 발견해 `gm_id_match_vgs_of`를 만든 것과
같은 클래스인데 이 11개 소자는 그 필드가 없다.

> ⚠️ **고치면 회로가 성립하지 않는다(미리 계산함)**. 미러를 강제하면 6개 미러가 레퍼런스
> M18_bg의 VGS(0.675V)를 따라야 하는데, 15배 전류를 흘리는 M8/M17은 **W ≈ 1545µm**가
> 필요해 `W_bounds` 상한 200µm의 7.7배다. 즉 이 bias generator는 **현재 동작점에서
> 원리적으로 성립하지 않는다**. 원인을 거슬러 가면 M18_bg의 vds(0.675V)가 diode 구간의
> **하한**이고, 하한이 낮을수록 VGS가 낮아 미러들이 감당 못 할 W를 요구한다. 고치려면
> **bias generator의 전류(Iref 1.2µA)나 L 자체를 다시 잡아야** 하고, 그건 회로 설계 판단이다.

**(4) 부수 발견(미수정)**: `grid_points_per_theta=1`이 `_theta_grid_points()`의
`i/(n-1)`에서 ZeroDivisionError를 낸다(비-L theta가 하나라도 있을 때).

#### ★ B15 완결 + 면적·코너 실측 — 재탐색의 목표가 바뀜다 (v4.18, 2026-09-08)

**(1) B15 ③ 스윙 완료.** L 앵커를 7→12개로 늘렸다
(`[0.15, 0.20, 0.25, 0.30, 0.35, 0.425, 0.5, 0.70, 1.0, 1.5, 2.5, 4.0]`µm -- 중간 삽입 5개).
체크포인트 120/120(기존 70개 재사용 + 새 50조합, ngspice 95분). 중간 삽입이 가능해진 것은
체크포인트 이름을 인덱스 기반에서 L값 기반으로 바꿔서다.

**①과 ③가 곱해진다**(leave-one-out, `tests/probe_interp_scheme_loo.py`):

| gm/ID 오차 | 기존 방식 + 7앵커 | 로그보간 + 12앵커 |
|---|---|---|
| nmos 중앙 | 6.37% | **0.63%** |
| pmos 중앙 | 13.70% | **1.41%** |
| pmos 최악 | 17,884.9% | **25.2%** |

약 **10배** 개선이다. CGG는 새 LUT에서도 선형이 이긴다(0.27% vs 1.55%) -- 배열별 결정 그대로 유효.

새 앵커의 실측값이 스윙 전 로그보간의 **예측을 검증**해 줌(PMOS gm/ID 최대, L=0.20/0.25/0.30µm):
예측 27.0/27.9/28.9 vs 실측 28.7/29.2/29.6. 보간은 방향은 맞았지만 정확도는 앵커가 필요했다 --
두 조치를 다 해야 했던 근거다.

**(2) 코너 실측 -- 구간 하한은 선호가 아니라 강제다**(`tests/probe_diode_window_corner.py`).
배분기가 diode에게 구간 하한을 주는 게 선택인지 확인하려고 세 코너를 전부 돌렸다:

| 선택 | 총면적 | diode | gain_db | 판정 |
|---|---|---|---|---|
| **lo**(W 최대) | 1042.93µm² | 669.75 | 68.20 | **성립** |
| mid | — | — | — | infeasible(`biasgen_vom_floatsrc_sink` 예산 음수) |
| hi(W 최소) | — | — | — | infeasible(`biasgen_vom_battery_a`) |

구간 폭이 0.19~0.41V 있는데도 **절반만 올리면 예산이 음수**가 된다 -- 지금 사이징에서
diode 구간의 자유도는 실질적으로 **쓸 수 없다**. 따라서 면적을 줄이려면 구간 안에서 미끄러지는 게
아니라 **L/ID를 바꿔야** 한다.

**(3) 면적이 처음으로 측정됐다.** 계기판에 면적을 추가했다(v3.3의 핵심 제약인데 빠져 있었다).

    총 면적     1050.40 µm²
    diode 16개   665.53 µm² (63.4%)
    그 외 35개  384.86 µm²
    v3.3 예시 예산 200µm² 대비 **5.3배**

> ⚠️ 비교 기준을 바로잡아야 한다. 이전 사이징의 117µm²는 **물리적으로 불가능한 상태의
> 면적**이었다(M11a가 vds=0.2V에서 동작한다는 가정). "8.9배 커졌다"가 아니라
> **"처음으로 실제 면적이 측정됐다"**가 맞는 표현이다.

**(4) 계기판 3시점 대조**(`tests/probe_metric_dashboard.py`):

| metric | 세션45 | B16까지 | +새 LUT |
|---|---|---|---|
| `power_uA` | 243.32 | 251.11 | 252.89 |
| `supply_current_uA` | 86.27 | 82.72 | 83.61 |
| `kcl_residual_uA` | 3.96 | 5.18 | 5.18 |
| `mirror_ratio_error_pct` | 63.61 | 22.67 | **22.88** |
| `stack_headroom_slack_v` | **−1.35** | 0.00 | **−0.00** |
| `gain_db` | 56.98 | 68.20 | **75.39** |
| 총 면적(µm²) | — | 1042.93 | **1050.40** |

`gain`이 LUT만으로 **+7.19dB** 올랐다 -- diode들이 L=0.375µm에 있는데 이제 0.35/0.425 앵커
사이라 `gm/gds`가 훨씬 정확해졌다.

**(5) 회귀 골든 갱신.** `nmcnr_3stage`의 stage2가 L=0.35→0.25µm로 옴겼다. **진짜 회귀가
아니다**: `gms`(7.1267/0.6283/1.2566 mS)와 stage1/stage3가 완전히 동일하고 `gm_id`도 23.00
그대로다. `objective=power`에서 `ID=gm/gm_id`는 L/VDS와 무관해 여러 (L,VDS)가 **동점**이고,
동점 해소가 "먼저 발견한 후보 유지"라 후보 목록에 0.25µm이 추가되자 그쪽이 이겼다. 사유를
골든 파일 안 `_stage2_update_note`에 남겼다.

**(6) 재탐색의 목표가 바뀜다.** 계획 §0.2 step 4는 "7개 스택을 만족시킨다"였는데, 그건
배분기가 구조적으로 해결했다(slack ≡ 0). 실측이 드러낸 진짜 문제는 **면적**이다:

- `gain`은 이미 **75.4dB**로 목표(54dB)를 크게 넘는다 → **여유를 면적과 맞바꿀 수 있다**
- 면적 **1050µm²**가 v3.3 예시 예산의 5.3배 → 여기가 진짜 제약
- diode가 면적의 **63.4%**를 차지하고 구간 하한이 강제된 상태 → **L/ID**를 바꿔야 한다

#### ★ B1 5단계 배선 완료 + B16 해소 — diode의 vds·gm_id를 물리 구속으로 (v4.17, 2026-09-08)

사용자 승인 후 배선을 끝냈다. ★절대원칙 이행 — 지난 세션에 만들어만 두고 호출처가
**0곳**이던 `set_device_vds()`/`solve_diode_connected_vds()`가 이제 실제 경로에서 돌고,
그 결과 드러난 모순을 헤드룸 배분기까지 고쳤다.

**(1) vds 기입 단일화(7곳)**. 각 사이트는 `gm_id`/`L`/`vsb`를 **먼저** 확정한 뒤
vds를 기입하도록 순서를 맞췄다 — 그래야 setter가 diode 자기일관성을 실제로 검사할 수 있다.
`grep '\["vds"\] *='` 결과 setter 본체 1곳만 남았다(C9 게이트 통과).

**(2) B16 — 구속을 반대 방향으로 강제한다.** §0.2 step 2는 불가능했고(헤드룸 시점에
diode 16개 전부 gm_id 없음), `gm_id = gm_id_for_vgs(vds, L, vds, vsb)`로 바꿔 배선했다.
`apply_diode_self_consistent_gm_id()`를 `gm_id_role` 루프 **직전**에 놓는다 — 그 시점이라야
L(L_role 루프)·vds(헤드룸)·ID(A엔진)가 모두 확정돼 있다. `_gm_id_source` 태그로 뒤 루프가
덮어쓰지 못하게 막는다(세션33 회귀와 같은 클래스의 사고를 막는 자리).

**(3) 헤드룸 배분기 — diode는 구간 제약 변수다**(사용자 승인). 배선하고 나니 `M11a`가
vds=0.2V에서 **W=4.03e8µm**를 요구했다. diode의 vds는 나눠줄 몷이 아니라 **W를 고르는 일**이기
때문이다. `diode_vds_window(lut, kind, L, ID, vsb, W_bounds) -> (lo, hi)`를 신설하고
(`W(v)`가 감소함수라 `W_bounds`가 그대로 vds 구간으로 번역된다),
`allocate_stack_headroom()`이 `vds_bounds`를 가진 엔트리를 배분 대상에서 빼고 **하한부터** 준 뒤
남은 예산만 자유 소자가 나눈다. 맞지 않으면 조용히 맞추지 않고 실패한다.

> 구간 안 어디를 고를지는 진짜 설계 자유도다(lo=W최대·면적 큼, hi=W최소·헤드룸 많이 쓀).
> 지금은 헤드룸이 더 희소하다는 §7.9 판단에 따라 **하한**을 쓰고, 그 선택은 결국 §7.9의 배분
> 탐색이 가져가야 한다.

**실측**(`tests/probe_diode_vds_window.py`): diode **16/16 전부 구간이 존재**하고(폭 0.19~0.41V),
그중 **14개가 배정된 0.2~0.3V보다 높은 vds를 요구**했다 — 헤드룸이 role 상수를 그대로 주던 것이
물리와 어긋나 있었다는 뜻이다.

**(4) 결과 — 견누지 않은 검증 신호.** self-test 둘 다 exit 0이고, 기준선은 의도적으로 갱신했다.

| | 이전 | 이후 |
|---|---|---|
| `M18_bg` vds | 0.20 V (role 상수) | **0.75 V** (구간 [0.7500, 1.0125] 안) |
| `M36a/b` vds | 0.30 V | **0.9375 V** (구간 [0.8625, 1.2750] 안) |
| 파일럿 gain / cmrr / psrr | 72.95 / 87.28 / 102.13 | 72.90 / 76.47 / 89.29 |
| `stage1_out` KVL 오차(sizing self-test) | +0.162 V | **−0.038 V** |
| `stage1_out` KVL 오차(stick_diagram) | +0.754 V | **+0.391 V** |

마지막 두 줄이 중요하다: 세션41부터 알려져 있던 KVL 위반이 **겹누지 않았는데도 줄었다**.
손대지 않은 지표가 개선됐다는 건 물리가 맞아가고 있다는 독립적 증거다.

**(5) skip 타당성 검토**(P1-b). 새 pass의 `continue` 3개를 실측했다
(`tests/probe_diode_pass_skips.py`): 처리 **6,960회**, S1/S2/S3 **전부 0회**. 근거 없는 방어
분기였으므로 명시적 에러로 바꾸고, 유일하게 남긴 하나는 근거를 주석에 적고 **"실측 0회라 아직
한 번도 실행된 적 없음"**까지 명시했다. 새 검사가 **픽스처의 기존 오류 2건**(L5의 M64,
`_gmv`의 Ma — 둘 다 diode인데 불가능한 값이 시드돼 있었음)도 찾아냈다. 값을 다시 박지 않고
`diode_vds_window()`로 런타임 유도하도록 고쳤다(LUT이 바뀌면 따라가야 하므로).

#### ★ B1 5단계 착수 전 계측 — 두 개의 차단 사유 (v4.16, 2026-09-08)

사용자 승인 후 배선에 착수하면서, 계획이 적어둔 절차가 실제로 성립하는지 먼저 찼다.
**두 가지가 성립하지 않는다.**

**(1) step 2가 그대로는 불가능하다 — 헤드룸 시점에 diode의 `gm_id`가 없다.**

§0.2 step 2는 "헤드룸 pre-pass에 diode 자기참조 추가"였고, 그건 그 시점에
`solve_diode_connected_vds(lut, gm_id, L, vsb)`를 부를 수 있다는 전제였다. 실주행에 계측을
붙여 세어보니(`tests/probe_diode_gmid_readiness.py`) **diode 16개 전부 `L`은 있지만 `gm_id`가
없다(0/16)**. 파이프라인이 `L → VDS → gm_id` 순서라 당연한 결과이고, 이 재설계가 뒤집으려는
바로 그 순서 문제다.

다만 막다른 길은 아니다. diode의 `Vgs = Vds` 구속은 **양방향**이다:

```
gm_id가 먼저면:  vds = solve_diode_connected_vds(gm_id, L, vsb)   (bisection, 기존 함수)
vds가 먼저면:    gm_id = lut.gm_id_for_vgs(vds, L, vds, vsb)      (O(1) 역보간, 기존 함수)
```

두 방향이 같은 곱선인지 80점에서 왜복 검산했고 **76점에서 |오차| < 1mV**로 일치한다.
즉 현재 순서를 유지한 채 **"헤드룸이 diode의 vds를 배정하고, 그 즉시 gm_id가 종속값으로
확정된다"**로 배선할 수 있다 — diode의 gm_id가 자유 탐색 변수에서 빠지는 것이 대가다.
(어긋난 4점은 아래 (2)의 오염 대역에서 나왔다.)

**(2) 그 검산 중에 별개의 결함을 찾았다 — LUT의 L 보간이 PMOS gm/ID를 부순다.**

`tests/probe_lut_L_interpolation.py`. LUT의 L 앵커는 `[0.15, 0.35, 0.5, 1.0, 1.5, 2.5, 4.0]µm`
인데, **앵커 위에서는 정상이고 앵커 사이에서만 PMOS의 gm/ID가 물리 상한(≈30~38)을 몇 자릿수씩
넘는다**:

| L(µm) | 앵커? | nmos gm/ID 최대 | pmos gm/ID 최대 |
|---|---|---|---|
| 0.150 | 앵커 | 24.8 | 26.2 |
| 0.200 | 보간 | 27.0 | **403.0** |
| 0.250 | 보간 | 28.4 | **5,516.8** |
| 0.300 | 보간 | 28.6 | **56,646.3** |
| 0.350 | 앵커 | 26.8 | 29.9 |
| 0.450 | 보간 | 26.9 | **45.7** |
| 0.500 | 앵커 | 27.0 | 30.5 |
| 0.830 | 보간 | 27.3 | **45.9** |
| 1.000 | 앵커 | 27.4 | 30.1 |

**기전**: `_gm_id_curve()`가 **ID는 로그공간**(`self._log_ID`, 세션29에 성능 목적으로 도입),
**GM은 선형공간**에서 보간한 뒤 둘을 나누는다 — 두 보간이 일관되지 않다. PMOS는 L=0.15와
0.35µm 사이에서 같은 VGS의 ID가 **약 6자릿수** 차이 나므로(VGS=0에서 1.12e-11 vs 6.50e-17 A,
짧은 채널의 DIBL이라 물성 자체는 정상), 중간점에서 ID는 기하평균(2.70e-14)·GM은 산술평균
(1.46e-10)이 되어 비가 **207배** 부품려진다. NMOS는 같은 구간의 ID 차이가 완만해 드러나지 않는다.

**이게 실제 파이프라인에 닿는다**: `L_stage2out_p` theta가 **M15/M25(PMOS)**를
`L ∈ [0.15, 1.0]µm`에서 **5nm 격자**(`_theta_grid_points()`의 `L_grid_step` 경로)로 훑는다.
격자점 대부분이 앵커 밖이다. `L_cascode`(M2a/M2b PMOS 포함)도 같다.

**다만 현재 저장된 파일럿 산출물은 오염돼 있지 않다** — PMOS가 전부 앵커에 안착했다
(M2a/M2b=1.0µm, M15/M25=0.15µm). 탐색이 오염된 후보와 정상 후보를 나란히 비교한 뒤 앵커를
골랐다는 뜻이고, **그 선택 자체가 아티팩트일 가능성은 남는다**.

**왜 지금 차단 사유인가**: §0.3은 재탐색 해가 `L = 0.15~0.45µm`에 있으리라 본다 — 정확히
오염 대역이다. 이 상태로 재탐색을 돌리면 **그럴듯해 보이는 틀린 답**이 나온다.

**해결 후보와 그 한계**(어느 것도 아직 채택 안 됨):

| 안 | 내용 | 확인된 사실 | 한계 |
|---|---|---|---|
| ① 일관보간 | GM도 로그보간(`gm/ID = exp(interp(log GM) − interp(log ID))`) | 비물리 폭발 소멸(전 구간 ≤30.3), 앵커값 보존(상대변화 <1.5e-3, 잔차는 VDS축에서) | **완전하지 않다** — `pmos L=0.20, gm_id=20`에서 W=339mm라는 역시 못 쓸 값이 나온다 |
| ② 앵커 고정 | L 탐색을 LUT 앵커로 제한 | 오염 원천 제거 | 유효구간(0.15~1.0µm) 앵커가 **4개뿐** — §7.10 knee(0.30~0.45µm)를 아예 분해 못 한다 |
| ③ LUT 재생성 | `sky130_lut_sweep.py`에 L 앵커 추가 | 체크포인트 재사용 구조라 **새 L만** 스윙(1개 L ≈ 14분 추정, 기존 70개 체크포인트 그대로) | 스윙 스크립트 주석의 경고: **"새 앵커는 반드시 끝에만 추가"** — 0.15~0.35 사이 삽입은 `_L{index}_` 체크포인트 이름과 회귀 골든값을 둘 다 깨단다 |

정직한 평가: **0.15~0.35µm 구간은 PMOS 물성이 너무 빨리 변해서 어떤 보간식으로도 복원되지
않는다.** ①은 비물리 값을 없애지만 정확도를 보장하지 못하고, ③만이 근본 해결이다. ①+③ 병행이
자연스럽지만 ③는 중간 삽입 제약을 먼저 풀어야 하고 ①은 공유 엔진 코드 변경이라 **둘 다 승인
대상**이다.

#### ★ 배선 전 사전계산 — diode 자기일관해가 스택 예산에 들어가는가 (v4.13, 2026-09-08)

B1의 3~4단계(자기일관 solver + 단일 setter)를 만든 뒤, **배선하기 전에** 그 값들이 KVL 예산에
들어가는지 전수 계산했다. 배선 후에 `allocate_stack_headroom()`의 "합=vdd" assert로 알게 되면
원인을 되짚기 어렵기 때문이다.

**결과 1 — 22개 스택 중 7개가 예산을 넘는다**(diode 16개가 자기일관 vds를 가져갈 때):

| 스택 | 현재 합 | 신규 합 | 예산 | 초과 |
|---|---|---|---|---|
| `biasgen_vom_battery_a` / `..._vop_battery_a` | 1.800 | **3.146** | 1.800 | **1.346 V** |
| `vbias2_stack` | 1.550 | 2.401 | 1.550 | 0.851 V |
| `biasgen_vom_battery_b` / `..._vop_battery_b` | 1.800 | 2.503 | 1.800 | 0.703 V |
| `vbias3_stack` | 1.550 | 2.030 | 1.550 | 0.480 V |
| `cmfb_vocdes_gen` | 1.800 | 1.905 | 1.800 | 0.105 V |

> **가장 걱정했던 M36a/M36b(1.361V 요구)는 문제가 아니었다** — `cmfb_load_a`/`cmfb_load_b`가
> 각각 단독 컬럼이라 예산 1.800V에 **여유 0.439V**가 남는다. 실제 병목은 **diode 두 개가 직렬로
> 쌓인 컬럼**이다: `biasgen_vom_battery_a`는 M11a+M11b가 각 0.873V씩(합 1.746V) 쓰는데 비-diode
> M12가 이미 1.400V를 점유해 3.146V가 된다.

**결과 2 — 그러나 원리적으로 불가능한 스택은 하나도 없다.** diode의 자기일관 Vgs는 **gm_id가
클수록 작아지므로**(weak inversion일수록 오버드라이브가 작다), gm_id/L을 다시 고르면 내려간다.
각 diode가 낼 수 있는 **최소 Vgs**로 하한을 잡으면:

| 스택 | diode 최소합 | 비-diode 현재합 | 최선 합 / 예산 | 판정 |
|---|---|---|---|---|
| `biasgen_vom/vop_battery_a` | 0.132 | 1.400 | 1.532 / 1.800 | **여유 있음** |
| `vbias2_stack` | 0.070 | 1.350 | 1.420 / 1.550 | **여유 있음** |
| `cmfb_vocdes_gen` | 0.132 | 0.000 | 0.132 / 1.800 | **여유 있음** |
| `biasgen_vom/vop_battery_b` | 0.501 | 1.400 | 1.901 / 1.800 | 비-diode도 **−0.10V** 필요 |
| `vbias3_stack` | 0.483 | 1.350 | 1.833 / 1.550 | 비-diode도 **−0.14V** 필요 |

즉 **feasible 영역이 비어 있지 않다** — 정공법(배선 + 재탐색)이 실현 가능하다.

**결과 3 — 다만 대가가 크다(정직한 한계).** 위 최소 Vgs는 `gm_id 25~26.5`, `L=0.15µm`(최소)에서
나온다. 그런데 gm_id 26은 LUT 상한(26.8) 바로 아래이고 **A11의 gain 정점(18~20.5)을 지나 떨어지는
영역**이며 면적이 폭발한다. L=0.15µm도 §7.10의 knee(0.30~0.45µm)보다 낮아 gain이 나쁘다. 따라서
실제 해는 최소값이 아니라 그 사이 어딘가이고, **탐색이 찾아야 한다** — 이 표는 "해가 존재한다"는
하한 증명이지 설계안이 아니다.

부수 관찰: PMOS 최소 Vgs가 **0.0658V**(거의 서브스레숄드 극단)인 반면 NMOS는 **0.2505V**로
차이가 크다. M57만 `L=0.500µm`에서 최소가 나오는데 `vsb=0.25` 때문으로 보인다.

**결과 4 — A8(스택 diode 연립)의 재해석**: 원래 "diode가 직렬이면 스택 단위 **연립 solver**가
필요하다"고 적었으나, 계산해 보니 성격이 다르다. **diode의 Vgs는 gm_id가 정하는 종속값이지
예산을 나눠 갖는 자유변수가 아니다.** 따라서 스택 KVL은 연립 방정식이 아니라 **gm_id 조합이
만족해야 하는 제약**이다:

```
Sum_{diode k} Vgs_k(gm_id_k, L_k, vsb_k)  +  Sum_{비-diode j} vds_j  <=  스택 예산
```

이건 §7.9의 gm_id 탐색에 **제약 하나를 더하는 것**과 같고, v4.2의 분리형 DP가 이미 다루는
형태다(면적·gain 제약과 같은 자리). **별도 solver가 아니라 제약 추가**로 처리한다.


#### ★ B1 해소 — 티어의 자리를 실측으로 재지정 (v4.3, 2026-09-07)

v3.0은 diode 티어를 `resolve_feed_vds()` **안**에 넣기로 했다. 계측해 보니 **그 자리로는
diode 소자를 단 하나도 덮지 못한다.**

**실측 1 — 소자별 vds를 실제로 정한 경로**(파일럿 51소자, SLSQP 실주행에 monkeypatch 계측;
스크립트 `tests/probe_vds_assignment_paths.py`):

| 경로 | 호출 횟수 | **vds를 정한 소자** | 그중 diode-connected |
|---|---|---|---|
| `allocate_stack_headroom()` | 1,876 | **28개** | 12개 |
| (위 계측 밖 -- 아래 실측 3 참고) | — | 14개 | **4개**(M18_bg/M66/M36a/M36b) |
| `_metric_stage_budget_vds_by_device()` | 15 | 5개 | 0개 |
| **`resolve_feed_vds()`** | 542 | **4개** | **0개** |

즉 v3.0안대로 티어를 `resolve_feed_vds()`에 넣으면 **51개 중 4개**만 지나가고, **diode
소자는 0개**다. 최악 오차 소자(M36a/M36b, +1.020V)는 그 함수 근처에도 가지 않는다.

> **이건 사고19의 재현이다.** 사고19 기록: "`resolve_feed_vds()`가 `(vds, source)`를 반환하도록
> 확장하는 수정을 시도했으나 분기가 애초에 그 계산을 안 타서 값 자체는 안 바뀌었다 -- 전부
> 되돌렸다." v3.0은 그 사고를 인용하면서 **같은 함수에 같은 방식으로 다시 걸었다.**

**실측 2 — `headroom_role`은 diode 여부를 전혀 반영하지 않는다**: diode-connected 16개의 role이
`cascode` 11 / `mirror` 3 / `diode_reference` 1 / `voltage_divider` 2로 흩어져 있다. 즉
**`diode_reference` 라벨은 실제 diode 16개 중 1개에만 붙어 있다.** 그리고 `vds=0.2`는
`min_vds_by_role["cascode"]`가 그대로 흘러나온 값이라, M2b(diode 아님, 필요 1.398V)와
M11a(diode, 필요 0.871V)가 **똑같이 0.2**를 받는다. role로 diode를 판정하려는 접근이 성립하지
않는다는 실물 증거이며 C4의 사례다.

**실측 3 — vds를 기입하는 엔진 지점은 7곳이다**(정적 전수, self-test 제외):

```
3237  _feed_gm_target_convention()        -> resolve_feed_vds() 경유
3304  공유전류 조인트 스캔(_scb_joint_plan)  -> 직접 기입
4729  vds_match_vgs_of pre-pass           -> ★ 물리적으로 옳게 계산하는 유일한 곳
4772  조인트 스캔 sibling 갱신             -> 직접 기입
4805  same_as_device 전파                  -> 직접 기입
4899  allocate_stack_headroom() 결과 적용   -> 직접 기입 (28개, 최대 경로)
5258  optimize_multistage() stage 결과      -> 직접 기입
```

`resolve_feed_vds()`를 경유하는 것은 **7곳 중 2곳**뿐이다. 한 함수만 고쳐서는 구조적으로
덮을 수 없다.

**확정 설계 — diode는 `vds_match_vgs_of`의 자기참조(self-reference) 특수 케이스다**

4729의 pre-pass는 이미 물리적으로 옳은 일을 한다: `target_vgs = ref_lut.vgs_for_gm_id(
ref.gm_id, ref.L, ref.vds, ref.vs)`를 계산해 `ctx.sized[m]["vds"]`에 박고, 그 소자를
`unresolved`에서 빼 **예산에서 차감**한다. diode-connected는 그 참조가 **자기 자신**인
경우일 뿐이다:

```
일반:   vds[m] = Vgs(ref)          <- ref가 먼저 풀리면 1회 조회로 끝
diode:  vds[m] = Vgs(m)            <- 자기참조라 고정점: v* = vgs_for_gm_id(gm_id, L, v*, vs)
```

따라서 §7.3은 **새 티어를 새 자리에 만드는 대신, 이미 있는 pre-pass를 자기참조까지 확장**한다:

```
_hr_resolve_vertical_group() 의 pre-pass 확장:
 1) diode_set = {m : connectivity(m).gate == connectivity(m).drain}     [토폴로지 레벨,
    `_HeadroomTopoEnv`에 1회 계산해 보관 -- role 라벨을 보지 않는다]
 2) m in diode_set 이면 vds_match_vgs_of[m] = m 으로 간주하고
    **고정점 solver**로 v* 를 푼다(단조 g(v)=Vgs(v)-v 의 bisection, 격자 밖이면 명시 실패)
 3) 나머지는 기존 pre-pass 그대로 -- 확정된 값은 unresolved에서 빠져 예산에서 차감된다
```

**바이패스를 구조적으로 불가능하게 만든다(C2 방지 장치 실물)**: v3.0은 "먼저 기입하면
우선순위①이 지켜준다"는 **암묵적 순서 의존**을 폐기한다고 선언했으므로, 순서 운에 기대면
안 된다. 위 7개 기입 지점을 **단일 setter**로 모은다:

```
set_device_vds(ctx, name, value, source: str) -> None      # 신규, 유일한 기입 경로
  · name이 diode_set이면 value가 고정점 해와 일치하는지 검사하고, 어긋나면 즉시 실패
    (조용히 덮어쓰지 않는다 -- §3.2 P1)
  · `_vds_source` 태그를 함께 남긴다(B13 추적성 요구를 여기서 함께 해결)
  · 7개 기입 지점을 전부 이 함수로 바꾸고, 원시 대입이 남아 있지 않은지 **grep 테스트**로
    강제한다(C9의 "중복 상수 grep 검사"와 같은 형태)
```

**DoD 추가**: 파일럿 재사이징 후 diode-connected 16개 전부에서
`|vgs_for_gm_id(gm_id, L, vds*, vs) - vds*| < tol`이고, `_vds_source`가 전부
`diode_fixed_point`로 찍혀야 한다. 현재는 16개 전부 오차 0.05V 초과이며 최대 1.020V다.


### 7.4 확정된 설계 원칙 (사용자 승인 완료, 이번 세션 AskUserQuestion)

1. Stage 안의 input+cascode는 gain 목표에서 L/gm_id를 **동시에** 결정한다(캐스코드 L을 role
   휴리스틱으로 따로 정하지 않는다).
2. ~~**Gain이 주도**한다 — 모든 stage gm_id를 gain 배분에서 먼저 정하고, GBW/PM은 보상소자
   값으로 사후에 맞춘다.~~ → **v4.0에서 사용자 확정으로 개정: 인과 방향은 그 반대다.**

   > **왜 뒤집혔나**(4개 관점 독립 검토에서 회로물리·문서정합성 두 검토자가 각각 최우선으로
   > 지적): v3.2가 §7.9를 `gm_i ← compensation이 고정`으로 재정식화하면서 이 원칙2와 §3.1
   > 요구사항4를 갱신하지 않아 문서가 **두 갈래로 갈려 있었다**. 둘은 양립 불가다 — §7.9의
   > 목적함수 `min Σ gm_i/gm_id_i`와 KKT `gm_i/gm_id_i²`는 `gm_i`가 상수여야만 성립하고,
   > `gm_i`가 자유롭다면 `gm_i→0`에서 목적함수가 무한히 감소해 문제 자체가 well-posed가 아니다.
   > 물리적으로도 Miller OTA에서 `(gm_1, gm_2, Cc)`는 `GBW = gm_1/Cc`와 PM(비지배극점
   > `gm_2/(C_1+C_2)`, RHP zero `gm_2/Cc`)이 **동시에** 묶는 3-tuple이라 "gm을 먼저 고정하고
   > Cc를 사후 역산"은 애초에 불가능하다. 문헌 정본 §6.4의 순서(`gm1=ω_T·Cm`, `gm2=Z·gm1`)도
   > §7.9 쪽과 일치한다.

   **확정 인과사슬**(문서 전체가 이 하나만 따른다):

   ```
   스펙 (CL, GBW, PM, Z, NDP)
     -> compensation:  (Cc, Rz, gm_1..gm_N) 을 한 번에 결정        [소자 사이징 아님]
     -> 자유 축:       gm_id_i                                      [★ 유일한 설계 자유도]
     -> 파생:          ID_i = gm_i/gm_id_i,  W_i = L_i*ID_i/IDu_i,  k_i = ID_i/ID_ref
     -> 기생:          C_1, C_2 (= f(W_i,L_i))  ->  Cc 재계산  ->  gm_i 갱신  [수렴 루프]
     -> 결과:          gain 은 스펙이 아니라 이 공간 위의 **부등식 제약이자 산출물**
   ```

   **"gain-budget-first"라는 이름의 의미도 여기서 확정한다**: "gain이 gm을 정한다"가 아니라
   **"stage별 gain 예산을 엔진이 유도해 산출한다"**(원칙3)는 뜻이다. gain은 입력이 아니라
   총량 제약 하나로만 들어오고, 단별 배분은 출력이다.
3. ~~배분 자체는 탐색/사용자 지정으로 남긴다~~ → **v3.1에서 사용자 확정으로 개정**:
   **배분도 엔진이 유도한다.** 총 gain 목표만 스펙으로 받고, stage별 배분은 §7.9 Phase 2의
   `A_i,max` 실측 + root current 1-D 해찾기 결과로 나온다(`gain_budget_db`는 출력). 사고4의
   본질("값을 논문에서 찾지 말고 회로에서 도출하라")은 유지되며, 도출 방식이 자유 탐색에서
   물리 실측 기반 결정론으로 좁혀졌을 뿐이다. 특정 배분 강제는 `gain_budget_db_override`로만.

### 7.5 전체회로 물리 정합성 검증기 (★ 신설 — §3.1 요구사항 6, 이번 재설계의 핵심 동기)

**왜 diode-connected 자기일관성(§7.3)만으로는 부족한가**: §7.3은 "gate==drain인 소자"라는
**한 가지** 위반 패턴만 잡는다. 하지만 이번 세션이 실제로 겪은 문제는 이보다 일반적이다 —
diode-connected가 아니어도, 어떤 소자의 게이트가 내부 net에 물려 있고 그 net의 실제 전압이
그 소자가 사이징될 때 가정한 VGS와 다르면, KVL이 조용히 깨진다(예: 사고21의 M301/M204,
사고19/23의 헤드룸 상호참조 — 전부 "diode-connected 여부"와 무관한 사례였다). §7.3이
diode-connected라는 **부분집합**을 고쳤을 뿐, "이 파이프라인이 사이징한 회로가 실제로 물리
법칙(KVL/KCL)을 만족하는가"를 **전체 netlist 단위로** 확인하는 일반 검증기는 아직 없었다.

**설계**: 이번 세션에서 diode-connected 버그를 실제로 발견한 방법(스크래치패드
`node_dc_propagate.py`/`build_transient_netlist.py`) 자체를 그대로 상시 검증 함수로
승격한다 — 2단계 검증, 둘 다 §8.4(사이징↔레이아웃 수렴)의 **마지막 게이트**로 실행하고
`run_sizing_layout_convergence()`가 이 게이트를 통과해야만 Stage 3로 넘어간다:

```
1단계 — LUT 기반 노드전압 재구성 + 상호모순 검사(빠름, 항상 실행):
  verify_node_voltage_consistency(ctx) -> list[Violation]
    - vdd/gnd에서 시작해, 사이징이 확정한 각 소자의 (kind, source, drain, vds)를 따라
      전체 netlist의 모든 net 전압을 전파(이번 세션 node_dc_propagate.py와 동일 알고리즘 —
      "특정 vertical_stack_id 안에서만" 이 아니라 회로 **전체**를 훑는다).
    - 같은 net에 서로 다른 경로로 두 번 이상 도달하면(예: fold_group처럼 여러 branch가
      한 노드에서 합류) 두 예측이 일치하는지 확인(허용오차 ~1mV) — 불일치하면 Violation
      (관련 소자 2개 + 예측값 차이).
    - 게이트가 vdd/gnd/외부 입력이 아닌 내부 net에 물린 모든 소자에 대해: 재구성된
      Vgate/Vsource로 실제 Vgs를 계산하고, 그 소자의 (gm_id,L,vds,vs)가 lut.vgs_for_gm_id()
      로 예측하는 Vgs와 비교 — 어긋나면 Violation("이 소자는 사이징 당시 가정한 게이트
      전압을 실제 회로가 못 준다").

2단계 — SPICE 독립 교차검증(느림, Stage 2 최종 수렴 시 1회만 실행):
  cross_check_with_spice(instance_data) -> bool
    - 이번 세션 build_transient_netlist.py를 skill asset으로 정식 편입해 sky130 트랜지스터
      레벨 넷리스트를 자동 생성, ngspice `.op`을 실행.
    - 1단계의 LUT 기반 노드전압 재구성 결과와 SPICE `.op`의 실제 수렴값을 대조 — 어긋나면
      1단계 자체가 놓친 로딩 경로가 있다는 뜻(LUT 전파는 각 소자를 독립적으로 보지만 SPICE는
      비선형 소자 간 상호작용까지 다 푼다).
    - rail-lock(출력이 VDD/GND에 고정)이나 수렴 실패 자체도 Violation으로 보고.
```

**정직한 실패 원칙**: 두 검증 중 하나라도 Violation을 보고하면 `run_sizing_layout_convergence()`
는 성공을 선언하지 않고 Violation 목록과 함께 명시적으로 실패한다(§3.2 P1 — 값을 지어내거나
조용히 넘어가지 않는다). 이 검증기는 diode-connected 사례(§7.3)를 특수 케이스로 포함하므로,
§7.3의 고정점 solver가 이 검증기의 1단계 안에서 자연스럽게 호출된다(별도 통합 불필요).

**신규 함수**: `verify_node_voltage_consistency(ctx)`, `cross_check_with_spice(instance_data)`
— §2 In Scope/§8.4 harness 순서에 반영(아래).

### 7.6 CMRR/PSRR/mismatch를 gain-budget 방법론에 결합하는 법 (★ 신설, 2026-09-04)

**왜 gain_budget_db처럼 배분할 수 없나**: CMRR/PSRR은 differential gain과 **물리적으로 다른
경로**(공통모드 신호경로, VDD 리플 주입경로)에서 결정되고, dB로 stage마다 깔끔히 더해지지도
않는다 — 대개 **한 소자(tail/바이어스)의 gds가 병목**이 되는 전역(whole-circuit) 특성이다.
따라서 `gain_budget_db`처럼 사전 배분하지 않고, **기존 검증 metric을 재사용한 feasibility
필터**로 다룬다(새 계산 로직 0개).

**(1) 스키마: `stages[].devices`에 `tail` 서브롤 신설**

```jsonc
"devices": {
  "input": [...], "cascode": [...], "load": [...],
  "tail": ["M6","M7"]   // NEW -- ID를 KCL로 정할 뿐 gain엔 기여 안 함, gds가 CMRR/PSRR을 좌우
}
```
tail은 §7.2의 `load`와 **동일하게** 기존 `role="load"`(gds 최소화, §13.7 구현됨)로 사이징한다 —
새 알고리즘이 아니라 "이 소자가 왜 존재하는가"를 스키마에 명시하는 것이 목적(CMRR/PSRR
관점에서 이 소자의 gds가 중요하다는 사실이 지금 스키마엔 어디에도 안 드러남).

**(2) CMRR/PSRR/mismatch는 stage 배분이 아니라 `global_spec.constraints`로 선언**

```jsonc
"global_spec": {
  "constraints": [
    {"metric": "cmrr_estimate_db",  "op": ">=", "value": 60},
    {"metric": "psrr_estimate_db",  "op": ">=", "value": 60},
    {"metric": "mismatch_sigma_mV", "op": "<=", "value": 5.0}
  ]
}
```
계산 로직(`smallsignal_ratio_db` MNA, `pelgrom_mismatch`)은 **완전 무변경 재사용**(§6.1) —
여기선 문턱만 선언한다.

**(3) 알고리즘: cascode/load/tail의 L을 좁은 outer-loop로 탐색, gain 역산은 그대로 결정론적**

L이 커지면 gds가 줄어(ro↑) CMRR/PSRR에 유리하지만 면적/기생커패시턴스 비용이 든다. 이
트레이드오프만 새 탐색 차원으로 열고, **gm_id 역산 자체는 건드리지 않는다**:

```
resolve_stage_sizing(stage_spec, ID, luts, global_constraints):
  for L_combo in L_candidates_product(cascode, load, tail):   # 면적 작은 순 오름차순
      1. cascode/load/tail: role="gain"/"load" 최적화(§7.2 step1/1', 무변경)
      2. input: gain 잔여치에서 gm_id 결정론적 역산(§7.2 step2/3, 무변경)
      3. size_transistor()로 W 확정
      4. extra_feasible(global_constraints) 판정 -- cmrr/psrr/mismatch 문턱 만족?
         (§13.5 `make_*_feasibility_check()`/`_combine_extra_feasible()` 콜백 합성 패턴 재사용)
      5. 만족하는 첫 L_combo 채택(면적 최소부터 봤으므로 area-최소해)
  전부 실패 -> InfeasibleSizingError("이 gain_budget_db 배분으로는 CMRR/PSRR/mismatch를
  동시에 못 맞춘다")
```

**이 설계가 사고4 원칙을 안 깨는 이유**: 새로 열리는 자유도는 **cascode/load/tail의 L 하나뿐**
이고, "가장 작은 면적부터 시도해 첫 feasible 채택"이라는 결정론적 규칙으로 탐색한다. `gain_i →
gm_id_i` 역산은 각 L_combo 안에서 여전히 100% 결정론적이다(§3.1 요구사항 5 유지).
⚠️ 단, L 오름차순 탐색은 "작은 것부터 보되 **전 구간을 실제로 스캔**"이어야 한다 — §13.7 실측
(M107: L=375nm→4µm에서 `gm·ro` 26배 **악화**)대로 gds의 L 의존성은 단조가 아니라 지름길이 없다.

**(4) Infeasible이면 상위 루프로 피드백 (v3.1 개정)**

L_combo를 전부 소진해도 제약을 못 맞추면 §7.9의 **Phase 1(헤드룸 재배분)**으로 올라간다 —
배분은 이제 유도값이므로 "배분을 다시 탐색"이라는 별도 경로가 없고, 진짜 자유도인 VDS 예산을
재배분해 `A_i,max`를 키우는 것이 유일한 상위 수단이다. 헤드룸 재배분으로도 안 되면(swing 하한을
깨야만 가능하면) 조용히 타협하지 않고 명시 실패 보고(§3.2 P1). `gain_budget_db_override`가 선언된
stage는 그 값이 물리 상한 `A_i,max`를 넘는지 먼저 검사해, 넘으면 즉시 그 사실을 보고한다.

**(5) 물리적 대칭(레이아웃)은 이번 범위 밖 — 책임 분담 명시**

`cmrr_estimate_db`/`psrr_estimate_db`는 **이상적 대칭**을 가정한 소신호 계산이고,
`pelgrom_mismatch`는 **그 대칭에서 벗어나는 정도**의 통계적 추정이다 — 둘을 함께 declared
constraint로 걸면 "이상적 대칭 + 현실적 미스매치"를 커버한다. 레이아웃이 그 대칭을 실제로
구현하는지(interdigitation/common-centroid/euler)는 이번 재설계에서 **무변경 재사용**하는
계층(§6.1)의 책임으로 남긴다.

### 7.7 L 변경 규칙 (★ 신설, 2026-09-04 — §7.6의 L 탐색이 레이아웃을 깨지 않게 하는 원칙)

§7.6이 L을 새 탐색 차원으로 열었으므로, "L을 언제/어떻게 바꿔도 되는가"의 규칙이 필요하다.
아래는 전부 기존 자산에서 근거를 찾아 정리한 것이다(신규 발명 없음).

| 규칙 | 내용 | 근거 |
|---|---|---|
| **R1. 누가 바꿀 수 있나** | §13.3의 **5개 구조 신호**로 먼저 판정 — 하나라도 걸리면 L은 파트너와 **강제 일치**(독립 변경 금지), 아무 신호도 안 걸리는 소자만 L 독립 탐색 대상 | `gm-id-methodology.md` §13.3(4개 회로 전수, 반례 0건) |
| **R2. 매칭 그룹은 전원 동시에** | 매칭은 **동일 기하(unit cell)** 전제로 공정 gradient를 상쇄하는 기법이라, 그룹 중 한 소자만 L이 달라지면 전제가 깨진다 — 바꾸려면 그룹 전원을 같은 값으로 한 번에 | `stick-diagram-euler-layout.md` §2.5("W = N × unit_cell"이 조립 방식의 정의) |
| **R3. LUT 실측 격자 밖 금지** | `SemiEmpiricalGmIdLUT`는 보간만 하고 외삽은 안 한다 — sky130 sample LUT의 L 앵커는 **전체 7개**(0.15/0.35/0.5/1.0/1.5/2.5/4.0µm)이고, 그중 파일럿 L theta의 bounds `[0.15,1.0]µm` 안에 드는 것이 **4개**(0.15/0.35/0.5/1.0µm)다 — v4.6 문맥 명시(이 둘을 구분하지 않으면 §7.6 실행시간 예산이 어긋난다) | `lut-generation-checklist.md` §7.7 |
| **R4. L↑가 항상 이득이 아니다 — 전수 스캔** | M107 실측: L=375nm→4µm에서 `gm·ro`가 **26배 악화**(L↑ → W_bounds와 상호작용해 feasible gm_id가 더 낮게 밀림). gds의 L 의존성은 소자·VDS마다 곡선이 달라 지름길 없음 | `gm-id-methodology.md` §13.7 |
| **R4b. 이득이 부족하면 L보다 VDS를 먼저 조정한다 ★** | 문헌 실측(45nm 2단 Miller OTA): L=100nm 고정·V_A 상수 가정으로 41.4dB 미달 → **VDS를 축으로 2회 반복**하자 같은 L에서 **61.4dB 달성**(면적 페널티 0). 우리 sky130 LUT 재측정(gm_id=15, ID=5µA): **VDS 0.2→1.2V는 gm/gds를 21.7→93.2(+329%)로 올리면서 W를 1.332→1.126µm(−15%)로 오히려 줄이는 반면, L 0.15→4µm는 gm/gds를 17.8→280.4(+1480%)로 올리는 대가로 W를 0.636→11.9µm(+1770%, 18.7배)** 쓴다 — R5/R6의 레이아웃 재검증 비용이 정확히 이 W 변화량에 비례하므로, **§7.7 자체가 "VDS를 먼저 소진하라"는 근거**다. ⚠️ VDS 조정도 IDu를 통해 W를 ~15% 바꾸므로 R8(수렴 루프 내부 + 커버리지 재확인)은 VDS에도 동일 적용한다 | `gm-id-methodology.md` §9.4/§9.5, 본 세션 LUT 실측(§7.9) |
| **R5. 직접 영향 — 행 폭** | 행 물리 폭 = `Σ n_fingers × pitch(l)`, `pitch(l)=l+overhead`. L은 행 폭에 **선형으로 직접** 들어가므로 L 변경 시 `check_box_shape()` 재실행이 **필수 게이트**(눈대중 금지) | `stick_diagram.py:6400/6421`, 레이아웃 문서 §8/§8.2 절차 5 |
| **R6. 간접 영향 — W→n_fingers 연쇄** | L이 바뀌면 같은 (gm_id, ID) 유지를 위해 W가 바뀌고 → `n_fingers` 변화 → 행 길이·interdigitation 패턴·`check_finger_width_compatibility()`(W는 finger_w의 정수배) 전부 재판정 대상 | 레이아웃 문서 §3.5 |
| **R7. 안 깨지는 것 2가지(정직 명시)** | (a) **오일러 패스는 L과 무관** — `build_graph()`/`check_euler_condition()`은 net-connectivity 그래프라 `l`을 안 본다(구조적 하드 게이트는 kind 동질성뿐). (b) **같은 물리 행 안에서 `l`은 달라도 되지만 `finger_w`는 반드시 같아야 한다** — `compute_row_geometry()`가 한 행 안의 서로 다른 `l`을 각자 pitch로 계산하도록 명시 설계됨("Euler trail로 여러 소자가 한 diffusion strip에 섞이는 게 정상 동작"), 반면 `finger_w`가 행 안에서 다르면 물리적으로 불가능해 `ValueError`. **단 그 행의 소자들이 매칭 그룹이면 R1/R2가 우선해 L도 일치시켜야 한다.** | 사고11(2축 분리), `stick_diagram.py:6421` docstring |
| **R8. 수렴 루프 "안"에서만 바꾼다** | L 변경 → 사이징 재계산(gm_id/W) → finger 재배분 → §3.5/§8 게이트 재실행 → §7.5 물리 정합성 검증. §7.6의 L 탐색은 §8.4 수렴 루프 **밖에서 따로 돌리면 안 되고 루프 안에** 들어가야 하며, 반복 재배치가 소자를 조용히 잃을 수 있으므로(사고16: 51소자 중 3개 소실) 매 반복 커버리지 재확인 게이트를 함께 돈다 | 사고16, §8.4 |

> **⚠️ branch(전기적)와 row(물리적)를 혼동하지 말 것(R7 관련 실제 질의로 명확화, 2026-09-04)**:
> 하나의 `vertical_stack_id`(=branch, 전기적 VDD~GND 컬럼)에 PMOS와 NMOS가 섞이는 건 **정상**
> 이고(class-AB 출력단의 정의 자체), 그 둘이 **서로 다른 L을 쓰는 것도 이미 정상 동작**이다 —
> 파일럿 회로 실측: `output_stage_a`의 M15(pmos, L=0.150µm)와 M16(nmos, L=0.830µm)로 5.5배
> 차이. 이게 가능한 이유는 R7 때문이 아니라 사고11의 **2축 분리**(`derive_horizontal_stack_
> groups()`가 전기적 그룹을 kind로 먼저 쪼개 `__pmos`/`__nmos` 행을 따로 만든다) 때문이다 —
> PMOS와 NMOS는 애초에 같은 물리 행에 못 들어간다. R7 (b)가 말하는 건 **같은 행(당연히 같은
> kind) 안에서** `l`이 달라도 되는가에 대한 훨씬 좁은 얘기다.

---

### 7.8 DOF 사전 진단 — 목표 개수 대비 자유도가 충분한가 (★ 신설, 2026-09-07)

**왜 필요한가**: §7.2/§7.6/§7.7은 "어느 자유도가 어느 목표를 담당하는가"를 암묵적으로 전제한다.
그 전제(아래 직교 분해)가 성립하면 gain 배분과 compensation을 **반복 없이 1-pass로** 풀 수
있지만, 회로 구조(KCL 결합)에 따라 전제가 깨질 수 있다. 사고19가 겪은 게 정확히 이것 —
상호참조로 풀릴 것 같던 관계가 실제로는 대수적으로 underdetermined였고, **손으로 직접 대입
검산해서야** 확인됐다(그 전까지는 "착시적 통과"와 "순환 데드락"을 오갔다). 그 검산을 사이징
시작 **전에** 자동으로 한 번 하는 것이 이 절의 목적이다.

**직교 분해 전제(§7.2/§7.6이 의존하는 것)** — 이게 성립하면 반복이 원리적으로 불필요하다:

| 목표 | 담당 자유도 | 성립 근거 |
|---|---|---|
| `stages[].gain_budget_db` | `gm_id`, `L`, **`VDS`** | intrinsic gain = `gm_id × V_A(L, VDS)` — **ID에 1차적으로 무관**. ⚠️ **2026-09-07 보정**: 초안은 `V_A(L)`로 적어 **VDS 축을 누락**했다 — `V_A`는 VDS의 강한 함수이고(§9.4, CLM+DIBL로 비단조), VDS는 KVL로 묶인 **제로섬 공유자원**이라 stage 간 결합을 만든다. 이 결합을 다루는 게 §7.9다 |
| `compensation.targets.GBW_hz` | stage별 **ID 스케일** | `gm = gm_id × ID` — gm_id를 안 건드리고 gm만 스케일 |
| `compensation.targets.PM_target_deg` | `Cc` (`Rz=1/gm2`는 종속) | |
| `stages[].driving_spec`(slew/settling) | 출력단 ID 하한 | `max(KCL ID, SR×CL)`(§7.2) |
| `global_spec.constraints`(cmrr/psrr/mismatch) | cascode/load/tail의 `L_combo` | §7.6 |

파일럿 회로 실측으로 이 전제가 실제로 성립함을 확인: stage1 ID=4.626µA / stage2 ID=24.702µA
(**비율 5.34가 바이어스 미러비로 조정 가능** — 옛 스키마의 `r_tail_M6`/`K_replica`류가 그
노브였다), gm_id는 stage1 22/15, stage2 10/17.5로 각자 독립. 즉 이 회로는 목표 수와 자유도
수가 맞아 **over-constrained가 아니다.**

**진단 알고리즘**:

```
diagnose_sizing_dof(sizing_spec, topology) -> DofReport:
  1. 목표 수집: stages[].gain_budget_db / global_spec.constraints /
     compensation.targets / stages[].driving_spec
  2. 자유도 수집(스키마 + connectivity만 보고, 사이징 계산 없이):
     - gm_id: stage별 input 소자 수. 단 matching_pairs/gm_id_match_vgs_of로 묶인 소자는
       1개로 축약(사고21의 primitive가 선언한 강제 동일 관계를 그대로 인정).
     - **(v3.2 정정)** ID/전류 축: v3.1은 "독립적으로 정할 수 있는 root current 개수"로 셌으나,
       §7.9 재정식화로 **자유 변수는 `gm_id_i`(stage마다 1개)**이고 `ID_i`/미러비 `k_i`는
       파생값이 됐다 -- 따라서 이 축의 자유도는 **stage 수**로 세되, `matching_pairs`/
       `gm_id_match_vgs_of`로 묶인 stage는 1개로 축약하고, KCL로 전류가 **강제 동일**한
       (미러비로도 못 바꾸는) stage 쌍만 합산한다.
     - L: R1(§13.3 5개 신호)로 "독립 변경 가능"으로 판정된 소자 그룹 수(§7.7).
     - Cc: compensation.solves_for 중 종속 항목(Rz=1/gm2) 제외한 개수.
  3. 목표별 담당 자유도 대조 -> 부족하면 **어느 목표끼리 같은 자유도를 놓고 다투는지**
     구체적으로 명시. 예:
       "GBW와 PM이 둘 다 hard target인데 이 회로는 stage1/stage2의 ID가 KCL로 고정비라
        실질 자유도가 Cc 하나뿐이다(1 DOF vs 2 target)."
  4. 반환: status = "ok" | "underdetermined"(자유도가 남음 -- 최적화 여지 있음, 실패 아님)
     | "overconstrained"(자유도 부족 -- 목표 충돌, 아래 대응 필요)
```

**언제 실행하나**: Stage 1 `author_topology_spec()`의 **마지막 단계**(§8.3에 반영) — 즉
`sizing_spec.json`이 완성된 직후, 사이징을 **시작하기 전**. 스키마와 connectivity만 보므로
LUT 조회/그리드서치 비용이 없다.

**`overconstrained`일 때 무엇을 하나 — 조용히 iterate하지 않는다**: 사고19의 "착시적 수렴/
순환 데드락" 재발 방지가 이 판정의 존재 이유다. 명시적으로 보고하고 사용자/AI가 셋 중 하나를
고른다:
1. `gain_allocation.method="search"`로 배분을 자유화(§7.6(4)의 조건부 피드백이 이때 발동)
2. 목표 하나를 완화(예: PM을 hard target 대신 범위 제약으로)
3. 회로 구조 자체를 바꿔 DOF를 늘림(예: stage2 전류를 독립 제어하는 미러 추가) — 이건
   topology 변경이므로 Stage 1로 되돌아가는 일이다

**제한적 반복(iteration)은 이 조건에서만 허용**: `DofReport.status == "ok"`인데도 §7.6의
L_combo가 전부 실패하는 경우 — 즉 **자유도는 충분한데 실제 수치가 안 맞는 경우**에만 §7.6(4)의
gain 배분 재탐색이 발동한다. `overconstrained`면 반복을 **아예 시작하지 않는다**(돌려봐야
수렴할 수 없다는 게 이미 대수적으로 확정된 상황 — 사고19가 두 leftover 공식을 서로 대입해
항등식 `b=b`만 나옴을 증명한 것과 같은 종류).

**기생 커패시턴스 반복은 별개(그대로 유지)**: W가 정해져야 `Cgg`/`CJD`를 알고 그게 pole을
옮겨 PM에 영향을 준다 — 이 소규모 고정점 반복은 기존 `converge_with_parasitics()`(방법론
§4.2, 3~4회)가 이미 담당하며 이번 재설계에서 **무변경 재사용**한다. DOF 진단과 무관한 축이다.

**신규 함수**: `diagnose_sizing_dof(sizing_spec, topology) -> DofReport` (§2 In Scope/§8.3에 반영).

---

### 7.9 헤드룸(VDD) 자원배분 — "배분"의 진짜 대상 (★ 신설, 2026-09-07)

**출발점(사용자 지적)**: "stage별로 물리적으로 가능한 gain 상한이 있는 것은 분명하다."
맞다 — 그리고 그 상한 `A_i,max`가 무엇으로 정해지는지 따져보면 **배분해야 할 자원이 gain이
아니라 VDD 헤드룸**임이 드러난다.

**`A_i,max`를 정하는 5가지 요소** (`A_i,max = max over (gm_id, L, VDS) of [gm/gds]`):

| # | 제약 | 성격 |
|---|---|---|
| ① | `gm/ID ≤ 1/(n·U_T)` — 300K에서 **≈32.7 V⁻¹**(250K 39.7 / 350K 27.6) | 물리 상수 |
| ② | `W = L·ID/IDu(gm_id,L,VDS) ≤ W_max` — gm_id↑ 시 IDu 급감으로 W 폭발 | 제조 제약 |
| ③ | `L ∈` LUT 실측 격자(§7.7 R3), **비단조**(§13.7) | 데이터/면적 제약 |
| ④ | **`VDS ≤` 그 소자에 배분된 헤드룸 예산** — `V_A(L,VDS)` 상한을 정함, **비단조**(§9.4) | ← **유일한 설계 자유도** |
| ⑤ | 캐스코드 부스트 `(gm/gds)_cas` | topology 고정 |

①②③⑤는 물리·제조·데이터·topology가 정하고, **④(VDS 예산)만 우리가 배분한다.**

**숨어 있던 순환 의존성**:

```
A_i,max  <-  VDS 예산_i  <-  헤드룸 배분(VDD 나누기)
   |                                    ^
   v                                    |
gain 배분  ->  gm_id  ->  VDS 실제 확정(§7.3)  ->  달성 gain 측정  ---+
```

VDS 예산을 정하려면 gain 기여도를 알아야 하고, gain을 알려면 VDS를 알아야 한다. §7.8의 직교
분해가 `V_A`의 VDS 축을 누락했기 때문에 이 순환이 보이지 않았다(§7.8 표 보정 완료).

**순환을 끊는 구조 — 사고21의 Phase 분리 + 문헌의 2회 반복(§9.4)**:

```
Phase 1 (DC 자원배분): VDD 헤드룸을 stack/소자에 초기 배분
    하한(강제): 출력 swing 스펙, diode-connected Vgs=Vds(§7.3), 포화 유지 Vdsat
    여유분 배분: 초기 seed 규칙  <- equal-margin(각 stage가 자기 상한 대비 동일 여유율)이
                 여기 자리잡는다. **최종값이 아니라 첫 반복의 출발점**이므로 임의성 부담이 없다.
Phase 2 (AC 사이징):   그 VDS 예산 하에서 A_i,max를 LUT로 실측(위 ①~⑤ 전부 반영)
    Sum(A_i,max) < gain_target  ->  Phase 1로 즉시 피드백(이 예산으론 물리적으로 불가능)
    충분하면 root current 1-D 단조 해찾기로 gain 배분을 **유도**(별도 배분 규칙 불필요)
    ->  gm_id/L/W 확정
Phase 3 (검증+피드백): §7.3 헤드룸 실제 확정 + §7.5 물리 정합성 검증
    달성 gain < 목표  ->  `dA_i/dVDS_j`를 LUT로 실측해 "1V가 가장 많은 dB를 만드는 소자"에게
    헤드룸 재배분  ->  Phase 2 재실행 (문헌 실측: 2회로 41.4dB -> 61.4dB)
종료: 수렴, 또는 "swing 하한을 깨지 않고는 목표 불가능"으로 정직한 실패(§3.2 P1)
```

**비용 순 중첩 루프 — 싼 노브를 안쪽에**:

```
outer:  레이아웃 수렴 (§8.4, finger/euler 피드백)          <- 가장 비쌈
  mid:    L_combo 탐색 (§7.6, 면적 오름차순)                <- 비쌈 (W +1770%)
    inner:  VDS 재배분 <-> gain 달성 (Phase 1<->3, ~2회)     <- 쌈 (W -15%, 제로섬)
```

이 중첩이 §9.5("L을 늘리기 전에 VDS 반복부터")를 **구조적으로 강제**하고, §7.7 R8("L 변경은
수렴 루프 안에서만")을 자동으로 만족하며, §7.6의 "면적 오름차순 첫 feasible"도 mid 루프로 그대로
살아남는다.

**두 노브의 자원 성격이 다르다는 게 핵심**:

| 노브 | gain 효과(실측) | W(레이아웃) 영향(실측) | 자원 성격 | 매칭 제약 |
|---|---|---|---|---|
| **VDS** 0.2→1.2V | 21.7 → 93.2 (**+329%**) | 1.332 → 1.126µm (**−15%**, 감소) | **제로섬**(VDD 공유) | offset 쌍은 이미 강제(union), **ratio 쌍은 ΔVDS가 계통 전류오차를 만든다 — `mirror_ratio_error`로 잰다**(v4.8, A4) |
| **L** 0.15→4µm | 17.8 → 280.4 (+1480%) | 0.636 → 11.9µm (**+1770%**) | 소자별 독립(면적 지불) | **있음**(R1/R2) |

(sky130 LUT, gm_id=15/ID=5µA 기준 본 세션 실측) — VDS는 "무료지만 총량이 VDD로 고정된"
제로섬 자원이라 **재배분**이 관건이고, L은 "면적을 지불하면 무제한"이라 **구매 결정**이다.
무료 자원을 최적 배분한 뒤 부족분만 유료로 사는 순서가 원리적으로 맞다.

**부수 발견 — `min_vds=0.2V` 기본값은 gain 관점에서도 최악의 지점**: VDS 0.2→0.4V만으로
`gm/gds`가 **21.7→52.2(2.4배)** 뛴다. 즉 오늘 발견한 diode-connected 버그(0.2V 상수 할당)는
헤드룸 KVL만 깬 게 아니라 **그 소자들의 intrinsic gain을 2배 이상 깎고 있었다**(사고23의
"vds 여유 0.01V면 사실상 triode"와 같은 맥락) — 이번 재설계의 동기가 하나 더 늘었다.

**✅ 확정(v3.1, 사용자 결정)**: `stages[].gain_budget_db`를 **입력에서 출력으로 격하**한다.
사용자는 총 gain 목표(`global_spec.constraints`의 `gain_db>=X`)만 주고, stage별 배분은 아래
Phase 2가 유도해 `instance.json`/리포트에 기록한다. §7.4 원칙 3과 §3.1 요구사항 5도 이에 맞춰
개정했다. 특정 배분 강제는 `stages[].gain_budget_db_override`(기본 `null`)로만 남긴다.

**Phase 2의 배분 유도 절차 (v3.2 재정식화 — 문헌 정합성 갭 해소)**

⚠️ **v3.1의 정식화는 Jespers의 sizing space를 축소하고 있었다**: v3.1은 `ID_i = k_i × ID_root`로
놓고 `k_i`(stage 간 전류비)를 "KCL이 강제하는 고정 비율"로 취급해 **1-D 해찾기**만 했다. 그런데
`k_i`는 바이어스 미러비로 조정 가능한 값이고(파일럿 실측 5.34, 옛 `r_tail_M6`/`K_replica`가 그
노브였다), `k_i`를 바꾸면 stage 간 `gm_id` 비율이 바뀐다 — 즉 **`k_i`가 곧 문헌 정본
(`gm-id-methodology.md` §6.4)의 두 번째 축**이었다. v3.1은 그 2D 공간을 `k_i` 고정 단면의 1D
선으로 줄여 **그 단면 밖의 더 나은 전력/면적 지점을 못 찾는** 상태였다(§13.2가 겪은 "엔진
지름길이 만든 인공적 제약"과 같은 종류).

**해소 방법 — `k_i`를 탐색 축에 추가하는 게 아니라 변수 자체를 바꾼다.** 인과가 거꾸로였다:

```
gm_i    <- compensation(GBW/PM)이 고정          [v4.0: §7.4 원칙2로 문서 전체 확정]
gain_i  =  compute_metric(gain_metric_spec)     [v4.0: 폐형식 곱이 아니라 metric 위임]
gm_i    =  gm_id_i x ID_i     =>   ID_i = gm_i / gm_id_i
```

> **`gm_i`는 완전한 상수가 아니다 — 기생 결합을 KKT 밖에 두면 안 된다(v4.0 정정).**
> `Cc`는 식 8.15로 노드 기생 `C_1, C_2`의 함수이고 `C_1 ≈ C_gg ∝ W·L`, `W = L·ID/IDu`이므로
> `gm_id_i -> W_i -> C_1,C_2 -> Cc -> gm_i` 경로가 존재한다. 즉 `∂gm_i/∂gm_id_i ≠ 0`이다.
> v3.2~v3.4의 §7.8은 이 반복을 "DOF 진단과 무관한 별개 축"으로 분리했는데, 그건 v2.4에서 이미
> 한 번 바로잡은 실수(`V_A(L)`에 VDS 축 누락)와 **같은 클래스의 누락**이다. §7.10 실측이
> "L 2.3배에서 fT 1/3.5"라고 보고할 만큼 `C_gg` 변화폭이 크므로 무시할 크기가 아니다.
> **처리**: `converge_with_parasitics()`를 Phase 2의 **바깥이 아니라 안**에 두고, 기생 갱신
> 이후 KKT 해를 다시 푼다(2~3회 수렴). 한 번만 풀고 끝내는 경로는 금지하며, 수렴 실패는
> §3.2 P1대로 정직한 실패로 보고한다.
즉 **`gm_id_i`를 고르면 `ID_i`가 따라오고, 미러비 `k_i`는 그 전류를 실현하려고 사이징되는
파생값**이다(옛 엔진은 순방향—미러비→전류→gm_id—이라 `k_i`가 자유 theta였지만, gain-budget-first는
역방향이라 그럴 이유가 없다). **진짜 자유 축은 `gm_id_i` 자신이고, 그게 정확히 Jespers의 N-D
sizing space다.**

```
변수: gm_id_{i,j} (stage i의 gm_id 서브그룹 j)  <- Jespers N-D 공간 전체를 덮는다
      · v4.0: "stage당 gm_id 1개"는 파일럿에서조차 거짓이다(stage1이 22/15 두 개).
        current-reuse/인버터형은 PMOS·NMOS gm이 합쳐지므로 서브그룹이 원리적으로 여럿이다.
파생: ID_i = gm_i/gm_id_i,  k_i = ID_i/ID_ref  <- 미러비는 구현값(탐색 축이 아님)
제약: gain    : compute_metric(gain_metric_spec, ctx) >= gain_target   <- ★ v4.0: metric 위임
      driving : ID_out >= SR*CL                (§7.2 output stage)
      물리    : gm_id_i <= 1/(n*U_T)           (최악 코너 값으로, §7.9 ①)
      제조    : W_i = L_i*ID_i/IDu_i <= W_max  (§7.9 ②)
      속도    : fT_i >= N*GBW                  (§7.10)
목적: min Sum_i ID_i (전력)          <- v3.3: 목적함수는 전력 하나
제약(추가): Sum_i Area_i <= area_budget  <- v3.3: **면적은 목적이 아니라 제약**

해법 — 면적 제약형(v3.3 확정, 사용자 선택): 가중치를 지어내지 않는다
   min  Sum_i ID_i = Sum_i gm_i/gm_id_i
   s.t. Sum_i Area_i(gm_id_i, L_i, VDS_i) <= area_budget     <- ★ gm_id 폭주를 여기서 막는다
        compute_metric(gain_metric_spec, ctx) >= gain_target <- ★ v4.0: 회로별 gain 식에 위임
        ID_out >= SR*CL,  gm_id_i <= 1/(n*U_T),  W_i <= W_max,  fT_i >= N*GBW

 1) 전력 최소화는 gm_id를 weak inversion 쪽으로 밀지만 **면적이 그 방향에서 폭발**하므로
    면적 제약이 먼저 걸린다. 실측(gm=75uS 고정, L=0.35um): gm_id 22->26 구간은 gain을
    +0.05dB 얻으려고 면적을 **147배** 쓴다(3.47->509um^2). 즉 **면적 예산이 gm_id의 실질
    상한**이고, 이게 v3.2에서 지적했던 "축퇴"를 해소한다.
 2) **배분은 분리형 DP로 푼다(v4.2 확정) -- KKT 한계비 탐욕은 폐기한다.**
    v3.3이 규정한 규칙("면적 1단위당 전력을 가장 많이 아끼는 stage에게 먼저 배분")은
    **기울기에 의존**하는데, A11에서 확인했듯 gain(gm_id)이 비단조라 그 전제가 깨진다.
    실제로 돌려보니 72개 시나리오 중 **27개(37.5%)에서 전수 최적과 어긋났고**, 그 중
    **8개는 feasible 해가 있는데도 gain 미달 해를 내놓았다**(탐욕 규칙이 gain 제약을
    아예 보지 않기 때문 -- 면적 예산만 보고 멈춘다). 자세한 근거는 아래 표.
 3) slew/driving 하한(ID_out >= SR*CL)에 걸린 stage는 그 하한에 고정(active set) ->
    DP의 해당 stage 격자를 그 하한 위로만 남긴다(별도 반복 불필요)
 5) gm_id_i 확정 -> gain_budget_i = gm_id_i x V_A_i   <- **유도된 배분(출력)**
 6) 이 배분으로 §7.2의 stage 알고리즘 실행(§7.2 로직 자체는 무변경)
 7) 실현: 각 branch의 미러비 k_i = ID_i/ID_ref 를 W 비율로 sizing
```

#### gain 제약은 폐형식이 아니라 metric 레지스트리에 위임한다 (★ v4.0, 사용자 확정)

v3.2~v3.4는 gain 제약을 `Σ 20log10(gm_id_i × V_A_i)`라는 **폐형식**으로 옵티마이저 본문에
박아두었다. 4개 관점 검토에서 이것이 **이 계획의 최대 차단 요인**으로 드러났다:

| 회로 | 등록된 gain metric | 위 폐형식과 호환 |
|---|---|---|
| `current_reuse_telescopic_ota`(파일럿) | `gain_stages_sum` | 형태만 유사(아래 ②) |
| `folded_cascode` | `folded_cascode_gain_db` | **불가** — `gm1·(Rout_p‖Rout_n)`, stage 합으로 분해 안 됨 |
| `nmcnr_amplifier` | `nmcnr_gain_db` | **불가** — 3단 전용 폐형식 |
| `two_stage_ota` | `smallsignal_gain_db` | **불가** — 전체회로 수치 MNA |

즉 §4.1 DoD의 **"4개 토폴로지 전수 실행(C7)"이 원리적으로 통과 불가능**한 상태였다. 그리고
이건 단순 누락이 아니라 **이 프로젝트가 이미 확립한 circuit-agnostic 규약을 §7.9가 깬 것**이다
— `optimize_full_circuit_budget()`은 선언만 읽고 회로별 식은 `_METRICS_REGISTRY`(16종 등록,
미등록 타입은 즉시 `ValueError`)에 위임하는 회로-무관 단일 함수로 설계돼 있다.

**확정 처리**:

```
gain 제약     : compute_metric(gain_metric_spec, ctx) >= gain_target
KKT 기울기    : d(gain)/d(gm_id_i) 는 폐형식 미분이 아니라 **LUT 위 수치미분**으로 얻는다
                (§7.10의 knee 스캔이 이미 쓰는 방식과 동일)
gain_metric_spec: `sizing_spec.json`의 `metrics` 블록에서 온다(§7.1, v4.0 복원)
```

폐형식을 버려야 하는 이유는 이식성만이 아니다. 두 가지가 더 있다:

① **부하 로딩 미반영**. `gm_id_i × V_A_i`는 구동소자 단독 intrinsic gain이라 부하·다음단 입력
   임피던스가 병렬로 붙는 것을 세지 않는다. 문헌 정본 §6.7은 단별 이득을 "그 단의 **두 Early
   전압 병렬조합**"으로 정의한다 — 구동/부하 `r_o`가 비슷하면 단당 −6dB, 2단이면 **−12dB의
   계통 낙관 편향**이다(54dB 목표에서 치명적). §7.2 step 2는 이미 "부하가 만든 부스트로 나눈다"고
   옳게 쓰고 있어, **배분을 유도하는 식(§7.9)과 소비하는 식(§7.2)이 서로 다른 gain 모델**이었다.
② **`V_A`가 `gm_id`와 독립이 아니다 — 오차를 실측했다**. 방법론 §2.5가 "Early 전압이 모든
   VGS에서 한 점으로 수렴한다는 통념은 실측상 거짓"이라고 명시하는데, 그 크기를 A10 조사에서
   정량화했다(`L=0.35µm`, `VDS=0.6V`, nmos):

   | gm_id | 실제 gain(dB) | `V_A` 상수 가정 시(dB) | 오차 |
   |---|---|---|---|
   | 5 (기준) | 28.98 | 28.98 | — |
   | 15 | 36.82 | 38.52 | −1.70 |
   | 20 | 37.75 | 41.02 | −3.27 |
   | 26 | 37.80 | 43.30 | **−5.50** |

   `V_A`가 5.62→2.98V로 **1.88배 감소**하기 때문이다. 즉 분리형은 gm_id를 올릴수록 gain을
   **낙관적으로 과대평가**하며, 그 편향이 5.5dB에 이른다. 미분 `(20/ln10)/gm_id`도
   `∂lnV_A/∂gm_id` 항을 통째로 빠뜨린다. LUT의 `gm_gds_ratio(gm_id, L, vds, vs)`를 **비분리
   함수로 직접 조회**하면 이 문제가 사라진다.

> **A10 조사 완료(2026-09-07) — v3.3 실측치는 옳다. 단위 표기가 빠져 있었을 뿐이다.**
> sky130 LUT로 직접 재현했다(`gm=75µS`, `L=0.35µm`, `VDS=0.6V`, `vs=0`, nmos):
>
> | gm_id | ID(µA) | W(µm) | 면적(µm²) | **gm/gds(선형)** | gain(dB) | V_A(V) |
> |---|---|---|---|---|---|---|
> | 5 | 15.000 | 0.364 | 0.127 | 28.12 | 28.98 | 5.62 |
> | 18 | 4.167 | 2.054 | 0.719 | 75.25 | 37.53 | 4.18 |
> | 22 | 3.409 | 9.926 | 3.474 | 77.16 | 37.75 | 3.51 |
> | 26 | 2.885 | 1455.199 | 509.320 | 77.61 | 37.80 | 2.98 |
>
> 즉 **"28→77.6"은 dB가 아니라 선형 `gm/gds` 비**다(dB로는 28.98→37.80). 같은 문장의
> "gm_id 22→26 구간 gain +0.05dB"는 37.75→37.80의 dB **증분**이라 둘 다 사실이지만, 한 문장에
> 선형비와 dB가 단위 표기 없이 섞여 있어 오독을 유발했다 — **표에 단위를 명시한다.**
> `V_A`는 5.62→2.98V로 지극히 정상적인 값이고, 물리적으로 불가능한 구석은 없다.
>
> **v3.3의 핵심 논거는 그대로 성립한다**: 면적 0.127→509.32µm²(4000배)는 아티팩트가 아니다.
> 전류밀도 `IDu`가 2.03e-6 → 1.98e-9 A/µm로 **1000배** 떨어지는 deep weak inversion이 원인이며
> (`gm = gm_id×ID`는 계속 75µS로 맞는다), 물리적으로 일관된다. `gm_id=26`은 이 조건의 LUT
> 상한(26.8) 바로 아래라 경계 근처지만 값 자체는 유효하다.

#### ★ A10 조사에서 나온 새 발견 — `gm/gds`는 `gm_id`에 단조가 아니다 (2026-09-07)

A10을 확인하려고 LUT를 정밀 스윕하다가, §7.9 해법이 깔고 있던 전제 하나가 **VDS가 클수록
크게 깨진다**는 것을 발견했다. `L=0.35µm`, nmos, `vs=0`에서 gm_id를 0.5 간격으로 훑은 결과:

| VDS(V) | 감소 구간 수 / 42 | `gm/gds` 최대 | 최대가 되는 gm_id |
|---|---|---|---|
| 0.4 | **0** (단조 증가) | 67.57 | 26.0 (구간 끝) |
| 0.6 | 6 | 77.64 | **20.5** |
| 0.9 | 8 | 88.58 | **20.0** |
| 1.2 | 11 | 95.83 | **18.0** |
| 1.5 | 12 | 100.77 | **18.0** |

즉 **VDS가 클수록 내부 최댓값이 뚜렷해지고 그 위치가 낮은 gm_id 쪽으로 이동한다.** 설계가 실제로
쓰는 VDS 대역(0.6~1.2V)에서 stage gain은 `gm_id ≈ 18~20.5`에서 정점을 찍고, 그 위로는
**gain이 오히려 떨어지면서 면적만 폭발한다**(gm_id 20.5→26: gain 77.64→77.61로 사실상 정체,
면적은 3.5→509µm²로 146배).

**세 가지 함의**:

1. **"gm_id를 올리면 gain이 오른다"는 KKT의 전제가 정점 위에서 거짓이다.** 정류조건의 λ 항이
   gm_id를 위로 미는 근거가 그 가정인데, 정점 위 구간은 gain·면적 **둘 다** 나빠지고 전력만
   좋아진다 — 즉 **gain·면적 기준으로 지배당하는(dominated) 영역**이다.
2. **탐색 상한을 면적 예산에만 맡기면 안 된다.** `gm_id ≤ argmax(gm/gds)`를 물리 상한으로 함께
   걸어야 한다(면적 제약이 없을 때의 Pareto 스윕에서도 정점 위 구간은 애초에 후보에서 빠진다).
   이 상한은 지어낸 값이 아니라 **LUT 실측으로 매번 다시 찾는 값**이다(§7.10의 knee 탐색과 동형).
3. **§7.9의 "해석해"라는 표현을 낮춰야 한다.** 목적함수 `Σgm_i/gm_id_i`는 볼록이지만
   `gain(gm_id)`가 비단조이고 `Area(gm_id)`는 LUT 보간이며 `V_A(VDS)`도 비단조(§9.4),
   `IDu(L)`도 비단조(§7.10 반례)다. **(gm_id, L, VDS) 전체 공간은 비볼록이다.** 따라서 KKT는
   **필요조건일 뿐**이고 v3.3이 주장한 "배분이 **유일하게** 결정된다"는 근거가 없다 — "국소
   최적 + 활성 제약 집합을 함께 보고한다"로 표현을 정정한다.

#### ★ 해법 확정 — 분리형 DP (v4.2, A11 해소)

**"해석해가 아니면 결국 탐색 문제가 되는 것 아닌가?"** — 아니다. **탐색이 아니라 "정확한 이산
최적화"가 된다.** 근거는 이 문제의 **분리성(separability)**이다:

```
각 stage의 (전력, 면적, gain) 은 자기 gm_id_i 에만 의존한다  [L_i, VDS_i 고정 시]
   전력 = Σ_i ID_i(gm_id_i)      면적 = Σ_i Area_i(gm_id_i)      gain = Σ_i A_i(gm_id_i)
결합은 오직 "합"으로만 일어난다  ->  자원배분 DP의 정확 알고리즘이 그대로 적용된다
```

```
solve_allocation_dp(stage_tables, gain_target, area_budget) -> Allocation   # 신규
 1) stage마다 gm_id 격자 전수로 (ID, 면적, gain_dB) 표를 만든다        [1차원, 국소최적 없음]
 2) 면적을 bin으로 이산화하고, bin마다 (누적 gain, 누적 전력)의 **비지배 집합**을 전파
 3) 마지막 stage까지 전파한 뒤 gain >= target 중 전력 최소를 고른다
 4) 되짚어 stage별 gm_id_i 확정  ->  gain_budget_i 는 그 결과로 산출(출력)
```

**왜 비볼록이어도 괜찮은가**: DP는 **기울기를 쓰지 않는다.** 각 stage의 1차원 격자를 통째로
훑고 부분해를 비지배 집합으로 들고 가므로, 정점이 여럿이든 감소 구간이 있든 영향받지 않는다.
KKT 탐욕이 무너진 이유(한계비가 비단조)가 DP에는 존재하지 않는다.

**실측 대조**(sky130 LUT, 2-stage, `gm_1=75µS`/`gm_2` 가변, gm_id 격자 0.25 간격 87점):

| 방법 | 전수 최적과 일치 | 비고 |
|---|---|---|
| 전수 대조(ground truth) | — | `87^N` 조합. N=3에서 0.98s, N=4는 5,729만 조합으로 비현실적 |
| **KKT 한계비 탐욕(v3.3)** | **45/72** | 19건 열등(전력 +0.29~0.66%), **8건은 feasible 해가 있는데 gain 미달 해 반환** |
| **분리형 DP(v4.2)** | **9/9** (탐욕이 틀린 케이스 전수) | N=2 0.003s / N=3 0.043s(전수 0.98s) / **N=4 0.294s** |

**사고4와 무엇이 다른가** — 이게 핵심이다:

| | 사고4가 막은 "탐색" | v4.2의 분리형 DP |
|---|---|---|
| 같은 입력 → 같은 답 | 보장 안 됨(초기값·시드·가중치) | **보장** |
| 임의 파라미터 | 가중치/초기해/종료조건을 사람이 지어냄 | **없음**(격자 해상도만, 그것도 리포트에 명시) |
| 국소최적 | 빠질 수 있음 | **구조적으로 없음**(기울기 미사용) |
| 최적성 확인 | 불가 | **전수 대조로 확인 가능**(작은 N에서 실제로 했다) |

즉 잃은 것은 **닫힌 식(closed form) 하나뿐**이고, 결정론·재현성·최적성은 오히려 강해졌다.
**남는 근사는 격자 해상도 하나**이며(gm_id 0.25 간격, 면적 bin 수), 이건 숨은 오차가 아니라
**선언하고 리포트에 찍는 값**이다 — 국소최적처럼 조용히 틀리지 않는다(§3.2 P1).

> **v3.3의 "배분이 유일하게 결정된다"는 표현은 철회한다.** 비볼록이라 KKT는 필요조건일
> 뿐이고, 실제로 그 규칙이 37.5%에서 틀렸다. 대신 **"주어진 격자 위에서 전역 최적이며,
> 활성 제약 집합을 함께 보고한다"**로 바꾼다.

**면적 예산이 선언되지 않으면 -> Pareto front fallback(v3.4, 사용자 확정)**: 예산이 없으면
`W_max`만 상한이 되어 배분이 축퇴되는데, 그렇다고 엔진이 예산을 **지어내면 안 된다**(값을
지어내지 않는다는 이 프로젝트 원칙). 대신 **전력-면적 Pareto front를 뽑아 사람에게 제시하고
선택을 받는다** -- 문헌 정본 §6.4가 "등전력·등면적 contour를 겹쳐 절충점을 사람이 고른다"고
한 그 절차를, 고를 수 있는 후보 집합을 계산해 제시하는 형태로 자동화한 것이다.

```
sweep_area_power_pareto(sizing_spec, luts) -> ParetoReport      # 신규
 1) 스윕 구간 결정(양끝을 물리로 고정 -- 임의값 없음)
      A_min = gain_target을 겨우 만족하는 최소 면적
              (gm_id를 낮출수록 면적은 줄지만 gain이 떨어진다 -> gain 제약이 하한을 정함)
      A_max = d(전력)/d(면적)이 임계 이하로 떨어지는 수확체감 지점
              (실측 근거: gm_id 22->26 구간은 전력 -15%에 면적 147배 -- 이미 A_max 너머)
 2) [A_min, A_max]를 **로그 등간격** N점(기본 12)으로 샘플(면적이 지수적으로 변하므로)
 3) 각 점에서 위 분리형 DP를 1회 실행 -> (area, power, gain, 배분) 기록
    · v4.2: DP는 **면적 bin별 비지배 집합을 이미 들고 있으므로** 한 번의 DP 전파로 front
      전체가 동시에 나온다 -- 점마다 다시 풀 필요가 없다(스윕 비용이 사실상 1회 DP로 붕괴).
    · LUT 스캔 캐시(P2)는 stage별 1차원 표 계산에서 그대로 공유된다
 4) Pareto 지배 관계로 필터 -> 비지배 점만 남김
 5) ParetoReport 반환: 각 점의 (면적, 전력, gain 여유, stage별 유도 배분, 활성 제약 목록)
```

**엔진은 여기서 자동으로 한 점을 고르지 않는다** -- `ParetoReport`를 반환하고 **정지**한다
(§3.2 P1 -- 예산을 지어내 조용히 진행하는 것이 곧 "조용한 실패"다). 사람이 한 점을 고르면
그 면적이 `global_spec.constraints`의 `area_um2`로 기록되고, 그 다음부터는 §7.9 본 해법이 **완전히 결정론적으로** 동작한다 --
즉 이 fallback은 "결정론을 포기하는 경로"가 아니라 **"빠진 스펙 하나를 사람에게 받아오는
경로"**다. 리포트는 §8.5의 HTML 산출물에 그대로 실어 사람이 검토할 수 있게 한다.

가중합(alpha:beta) 방식은 이 fallback이 있으면 필요 없다 -- 가중치를 지어내는 대신 후보를
보여주고 고르게 하는 쪽이 임의성이 없고 근거도 남는다.

**v3.1이 버려지지 않는다**: v3.1의 "ID_root 1-D 해찾기"는 **모든 stage가 비활성일 때의 특수
케이스**(3)의 `ID_i = const = I*`)로 이 일반해에 흡수된다.

**파일럿이 이 구조로 설명된다**: 출력단 `ID=24.702µA`는 class-AB 구동 요구(**활성 제약**)로
고정되고 stage1 `ID=4.626µA`는 비활성이라 최적점에 있다 — 즉 **비율 5.34는 "자유 선택"이 아니라
활성 제약의 결과**였다.

**축퇴 문제의 해소(v3.3)**: v3.2까지 남아 있던 "순수 전력 최소화면 gain과 power가 같은 방향이라
배분에 자유도가 없다"는 한계는 **면적 예산을 제약으로 걸면 사라진다**. 전력 최소화가 gm_id를
weak inversion으로 밀 때 면적이 폭발적으로 늘어 제약이 먼저 걸리고, 그 지점에서 stage 간 KKT
커플링(한계 전력절감 / 한계 면적비용 균등화)이 나타나 **배분이 유일하게 결정**된다.

남는 유일한 자유 입력은 **면적 예산 자체**인데, 이건 물리가 정해줄 수 없는 값이지만 전력 목표·
gain 목표와 같은 **정상적인 설계 스펙**이다(가중치 alpha:beta처럼 물리적 의미 없는 튜닝 노브가
아니다). 이 구조는 문헌 정본 §6.4의 "등전력(타원)·등면적(쌍곡선)·등이득(점선) contour를 겹쳐
절충점을 고른다"를 **자동화**한 것에 해당한다 — 사람이 눈으로 고르던 절충점을 면적 예산이라는
명시적 제약과 KKT 정류조건으로 결정론적으로 찾는다.

**개선 대상 함수(★ v3.0)**: 위 Phase 1/3은 `allocate_stack_headroom()`의 **"남는 예산
균등분배"** 정책을 대체하는 것이라, 그 함수를 안 고치면 **구현 자체가 불가능**하다(v2.x의
§6.1 "무변경" 선언과 정면 모순이었다 — P1 확정으로 해소):

```
HeadroomPolicy.cascode_fn(entry)  ->  headroom_fn(entry, ctx)     # ★ 시그니처 확장
   - entry에 gm_id/L/kind/connectivity를 실어 보낸다(사고10: 지금은 gm_id가 없어 Jespers
     공식이 죽은 코드이고 상수로 떨어진다 -- 이건 재사용할 게 아니라 고쳐야 할 버그다).
   - ctx로 LUT 접근을 허용해 dA/dVDS 실측 기반 가중 배분을 가능하게 한다.
allocate_stack_headroom(...)의 "남는 예산 균등분배"
   -> "swing/포화/Vgs=Vds 하한을 먼저 확보한 뒤, 잔여분을 dA/dVDS 가중으로 배분"
```
균등분배는 물리적 근거가 없는 임의 정책이었다(C1/C4). 가중 배분으로 바꾸면 §7.9 Phase 3의
"1V가 가장 많은 dB를 만드는 소자에게" 규칙이 그대로 이 함수 안에서 실행된다.

---

### 7.10 초기 L 선택 기준 (★ 신설, 2026-09-07 — §7.6 L_combo 탐색의 시작점)

**왜 필요한가**: 현재 엔진은 `_L_ROLE_MULTIPLIERS = {"mirror": 2.5, "bias_replica": 1.2}`
(×L_min) 고정배수만 갖고 있고, 캐스코드/신호경로는 `select_L_by_role()`이 명시적으로 거부하며
"theta 탐색이 대신 결정"으로 비워둔 상태다. 코드 주석 자신이 2.5배를 "실무 관례 2~3배의 **중간값**
(범위 내 대표값)"이라 밝히고 있어 임의성이 남아 있었다. §7.6이 L을 탐색 차원으로 열었으므로
**그 탐색의 시작점**을 원리적으로 정할 필요가 있다.

**측정 1 — L을 늘릴 때 얻는 것과 잃는 것** (본 세션 sky130 LUT 실측, nmos, gm_id=15, ID=5µA, VDS=0.6V):

| L/L_min | gain배(gm/gds) | 면적배(W·L) | fT배 | mismatch 개선배(√WL) |
|---|---|---|---|---|
| 1.0 (0.15µm) | 1.00 | 1.00 | 1.000 | 1.00 |
| **2.3 (0.35µm)** | **3.91** | **4.29** | 0.288 | 2.07 |
| 3.3 (0.50µm) | 5.94 | 8.94 | 0.149 | 2.99 |
| 6.7 (1.0µm) | 8.47 | 34.5 | 0.041 | 5.87 |
| 26.7 (4.0µm) | 15.80 | **498.8** | **0.003** | 22.33 |

- **gain 수확체감이 극심**: 첫 2.3배 구간이 gain 3.91배를 주는데, 이후 L을 11.6배 더 늘려도 4배만 추가.
- **fT는 L²에 반비례로 붕괴**(fT=gm/2πCgg, Cgg∝W·L∝L²): 2.3배에서 이미 1/3.5, 6.7배면 1/24
  → **fT가 L 상한을 정하는 진짜 제약**이다(기생 pole이 GBW를 침범하면 PM이 무너진다).
- **mismatch 개선은 √(W·L)이라 완만**: 2.3배 → 2.07배.

**측정 2 — 한계효율 knee의 위치** (`Δ(gm/gds)/Δ(W·L)` = 면적 1단위당 얻는 gain):

| | 0.15→0.35 | 0.35→0.50 | 0.50→1.0 | 1.0→1.5 |
|---|---|---|---|---|
| nmos gm_id=8 | **406** | 205 | 74 | 13 |
| nmos gm_id=15 | **165** | 81 | 18 | 5.4 |
| nmos gm_id=22 | **25.5** | 5.9 | 1.0 | 0.5 |
| pmos gm_id=15 | **최대** | 25.8 | 17.8 | 3.5 |

**kind와 gm_id를 바꿔도 knee는 항상 `L ≈ 2~3 × L_min`** 구간이다 — 즉 기존 `mirror: 2.5×L_min`
배수는 "관례의 중간값(임의 선택)"이 아니라 **실측 knee와 일치**함이 사후 검증됐다(근거가 생겼으니
주석의 "임의 대표값" 표현은 구현 시 이 실측으로 대체할 것).

**원칙 — 초기 L은 knee에서 시작하되 물리 제약으로 clamp한다**:

```
L_init = knee(kind, gm_id, vds)          # 한계 gain/면적 효율이 최대인 구간의 상단, LUT 실측
clamp:
    L <= L_max(fT)     : fT(L) >= N x GBW      (N~5~10, 기생 pole의 GBW 침범 방지)
    L >= L_min(match)  : sigma_VT = A_VT/sqrt(W*L) <= 목표(§7.6 global_spec.constraints)
    L in LUT 실측 격자  (§7.7 R3, 외삽 금지)
role별 방향 편향:
    cascode(role="gain")        : knee 이상으로 밀어도 됨(ID 고정이라 전력비용 0) -- fT 상한이 우선
    mirror/matching             : knee + mismatch 하한(면적이 매칭에 직접 기여)
    속도 임계(GBW 담당 입력단)   : fT 상한이 지배 -> knee보다 작을 수도 있음
    tail/load(§7.6)             : gds 최소화가 목적 -> CMRR/PSRR을 만족하는 최소 L
```

**왜 L_min이 아니라 knee에서 시작하나**: §7.6의 L_combo 탐색은 "면적 오름차순 첫 feasible"이므로
시작점은 원칙적으로 "제약이 허용하는 최소 L"이어야 한다. 그런데 그걸 그냥 `L_min`으로 두면
gain이 너무 낮아(측정 1: L_min에서 gm/gds=17.75, 약 25dB) 대부분의 조합이 infeasible로 버려져
탐색이 낭비된다 — **knee에서 시작하는 것이 실용적이며, knee 아래는 fT가 정말 급한 소자에만
내려간다.**

**§7.7 R4b와의 결합(중요)**: knee에서 시작 → gain이 부족하면 **먼저 VDS 재배분**(§7.9 inner
루프, W −15%) → 그래도 부족할 때만 L을 knee 위로 올린다(§7.6 mid 루프, W +1770%). 즉 §7.10은
"어디서 출발하나", §7.7 R4b는 "부족하면 어느 노브부터 쓰나"를 각각 답한다.

**⚠️ 실측으로 찾은 반례 — "면적은 L에 단조 증가"가 아니다**: pmos 일부 구간에서 **L을 늘렸는데
`W·L`이 오히려 감소**했다(한계효율이 `inf`로 계산됨). `IDu`가 L에 비단조이기 때문이며, §7.7 R4의
"지름길 없이 전수 스캔" 원칙이 여기서도 확인된다 — knee 탐색도 닫힌 식이 아니라 격자 전수
스캔으로 구현할 것.

**신규 함수**: `measure_L_knee(lut, kind, gm_id, vds, L_grid) -> float`(측정 2의 한계효율 스캔),
`L_bounds_from_ft_and_matching(spec, stage) -> (L_lo, L_hi)`(fT 상한/mismatch 하한 계산) —
둘 다 §7.6의 `L_candidates_product()`가 탐색 범위를 정할 때 호출한다.

**개선 대상 함수(★ v3.0)**:
- `_L_ROLE_MULTIPLIERS = {"mirror": 2.5, "bias_replica": 1.2}` **상수 → `measure_L_knee()`
  실측 호출로 대체**. 이번 실측으로 2.5×가 sky130 knee와 일치함이 확인됐지만, **공정이 바뀌면
  knee도 바뀐다** — 상수로 두면 다른 PDK로 이식할 때 조용히 틀린 값을 쓴다(C1/C9). 실측
  호출로 바꾸면 자동 추종하고, `select_L_by_role()`이 `cascode`/`signal`을 거부하던 제약도
  함께 해소된다(knee가 모든 role에 정의되므로).
- `search_gm_id_for_role()` → **`search_gm_id_and_L_for_role()`**(L축 내부화, §6.1 (가)) —
  knee 탐색·L_combo 탐색·role 목적함수가 **같은 `_idu_scan` 결과를 공유**하게 되어 P2(중복
  스캔 금지)를 만족한다.

---

### 7.11 기생 pole clamp — L 상한을 **회로가 스스로 말하게** 한다 (★ 신설, 2026-09-10)

**왜 필요한가**: §7.10이 `L <= L_max(fT) : fT(L) >= N x GBW (N~5~10)`이라 적어뒀는데
**엔진에 이 검사가 없다**(`fT()`는 있으나 호출부 0개, B20 조사 때 확인). 상한이 없으면
gain이 L을 무한정 밀어 올린다 — 실제로 미러 gain 랭킹에서 최적이 `L=4.0µm`(격자 최대)로
나왔다(§10.3 B19'). 그런데 `N`을 상수로 박으면 **그 회로에 맞춘 숫자**가 되어 일반성을
잃는다. 이 절은 N을 **유도해서 없애는** 방법을 정한다.

#### 1) 문헌 조사 (2026-09-10, 사용자 지시)

| 출처 | 내용 |
|---|---|
| Sansen, *Analog Design Essentials* | 비지배 pole은 GBW의 **약 2배 이상** |
| 표준 2-pole 결과 | p₂/UGF = 1 → PM 45° / 2 → ~59° / **3 → 71.6°** |
| 실무 경험칙(EDAboard) | 단일단 fT ≥ **10×**GBW, 2단 **>20×** |
| 미러가 신호경로에 있을 때 | `fT ≈ (N_mirror + 4) × UGF`이면 p₂ ≥ 3×UGF 달성 |

#### 2) 그런데 이 회로엔 **정의식**이 이미 있다

`compensation` 주석에 원문(Xie & Chen) PDF에서 직접 확인해 등록한 관계가 있다:

    PM = tan⁻¹(ω_p2 / ω_c)

일반 경험칙이 아니라 **이 토폴로지의 정의식**이다. 여기서 바로 나온다:

    PM_target = 70°  →  ω_p2 ≥ tan(70°)·ω_c = 2.747·ω_c
    ω_c = 6.9/t_lln = 2.3e8 rad/s  →  f_c = 36.6 MHz,  f_p2 ≥ 100.6 MHz

#### 3) N의 정체 — §7.10의 "5~10"은 임의값이 아니었다

노드 pole `f_p = gm/(2π·C_node)`, `fT = gm/(2π·Cgg)`이므로 `C_node = α·Cgg`라 두면

    **N = α × tan(PM_target)**

| α (노드 용량 / 소자 Cgg) | 2 | 3 | 3.6 | 4 | 7.3 |
|---|---|---|---|---|---|
| N | 5.5 | 8.2 | 9.9 | 11.0 | 20.1 |

즉 §7.10의 `N~5~10`은 정확히 `α ∈ [2, 3.6]`이고, 문헌의 "2단 20×"는 `α ≈ 7.3`이다.
**N은 독립 상수가 아니라 (PM 관계식) × (노드 용량비)의 결과다.**

#### 4) 실측 — 이 회로에서 fT는 knee 근방을 안 묶는다

tail 4개(M5/M6/M7/M38)의 최소 `fT/f_c`:

    L=0.150µm  83.8      L=0.375µm(knee)  ~28      L=0.700µm  9.5      L=1.000µm  4.9

knee에서 여유가 28배라 N=10은 물론 N=20에도 안 걸린다. **fT가 실제로 무는 것은
L ≳ 0.7µm**이고, 그게 바로 gain이 L을 4.0µm로 밀려 할 때 필요한 제동이다.

#### 5) ★ 코드화 원칙 — 숫자를 박지 말고 **유도 경로를 배선**한다

`N`을 상수로 넣으면 이 회로 전용이 된다. 대신 N을 만드는 두 항을 각각 회로에서 얻는다:

```
필요 pole 위치   ω_p2_req = f_PM(PM_target, ω_c)   <- **토폴로지가 안다**
                 (이 회로: tan(PM)·ω_c. nmcnr/folded는 자기 topology_fn이 정의)
노드 용량비      α_node   = C_node / Cgg_device    <- **넷리스트에서 잰다**
                 (노드에 붙은 모든 소자의 Cgg/Cdb 합, cgg_absolute()로 계산)
제약             ω_pole(node) = G_node / C_node >= ω_p2_req
```

**즉 `fT >= N·GBW`는 `ω_pole(node) >= ω_p2_req`의 손 근사였다.** 노드 pole을 직접 쓰면
α도 N도 필요 없다 — 둘 다 측정/유도로 사라진다.

**단계**:

| | 내용 | 일반성 |
|---|---|---|
| L1 | 노드별 `G/C` 추정(LUT gm·gds·Cgg를 넷리스트 노드로 합산) | 회로 무관 |
| L2 | 기존 51노드 MNA에서 **실제 pole 추출**(고유값) | 회로 무관, 더 정확·비쌈 |

**선언으로 노출**(§3.2 P1, C1 — 선언 출처 없는 제약 금지): 이 clamp는 숨은 상수가 아니라
`sizing_roles.metrics`의 **metric**으로 내놓고 constraint로 걸 수 있게 한다.

#### 6) ★ 구현 완료 (2026-09-10) — 하한까지 유도해 상수를 전부 없앴다

**하한도 `k`(pole 개수)로 배분하지 않는다 — 위상을 직접 더한다**:

    PM_parasitic = 90 - sum_over_nodes( atan(w_c / w_pole(node)) )
    제약:          PM_parasitic >= PM_target_deg      <- 이미 선언된 값

이 식은 **원문 관계를 특수케이스로 포함한다**: 비지배 pole이 하나면
`90 - atan(w_c/w_p2) == atan(w_p2/w_c)`(항등식)이라 원문의 `PM = atan(w_p2/w_c)`와 **정확히
같다**. 즉 `alpha`·`N`·`k`가 **셋 다 사라진다** — 하한은 새 상수가 아니라 이미 선언된 PM 목표다.

**신설 함수 3개**(전부 회로 무관):

| | 하는 일 |
|---|---|
| `signal_path_nodes(by_name, excite, sense)` | `gate->drain`/`source->drain` 방향그래프에서 excite 도달 ∩ sense 역도달. **bias 노드를 자동으로 배제**한다 |
| `node_pole_estimate(by_name, sized, spec, only)` | 노드별 `G/C`. 드레인→`gds`, 소스→`gm+gds`, 게이트→`Cgg`(`cgg_absolute()`) |
| `_metric_parasitic_pm_deg` | 위 둘을 합쳐 metric. `excite`/`sense_p`/`sense_n`을 `smallsignal_gain_db`와 **같은 형태로** 선언받는다 |

**구현 중 실측으로 바로잡은 것 둘**:

1. **전 노드를 세면 무의미하다** — 처음엔 모든 내부 노드를 더했더니 `PM = -1004도`가 나왔다.
   `Vbias1`/`Vbias4` 같은 **순수 bias 노드가 각각 ~90도**를 먹기 때문이다. 그 노드들은 pole이
   있어도 이 경로의 위상을 안 먹는다 → `signal_path_nodes()`로 경로를 유도해 해결.
   그래서 **어느 경로의 PM인지가 선언에 있어야 한다**(전 노드 합산은 원리적으로 틀렸다).
2. **못 세는 노드를 조용히 넘기지 않는다** — LUT에 CGG만 있고 **접합용량(Cdb/Csb)이 없어서**
   게이트가 안 붙은 노드는 용량을 셀 수 없다. 근거를 따져 둘로 갈랐다: **소스가 붙은 노드**는
   `1/(gm+gds)` 저임피던스라 pole이 높아 지배할 수 없으므로 이유와 함께 제외하고, **드레인만
   붙은 고임피던스 노드**는 `undetermined`로 돌려 **명시적으로 실패**한다. (파일럿은 경로를
   좁히자 `undetermined` 0개가 됐다 — 못 세던 5개는 전부 포트였다.)

**파일럿 실측(2026-09-10)** — 신호경로 8노드 중 셀 수 있는 4개:

    Vg15 / Vg25    f_pole =  31.6 MHz = **0.86 x f_c**   각 49.2도씩 먹는다
    Vom1 / Vop1    f_pole =  11.1 GHz =  304  x f_c      각 0.19도

    PM_parasitic = 90 - 98.9 = **-8.9도**   (PM_target 70도)

**class-AB 출력단 게이트 노드(`Vg15`/`Vg25`)의 pole이 크로스오버보다 아래**에 있다. 기존
metric 어느 것도 이걸 못 봤다. **constraint로는 아직 안 건다** —
`mirror_ratio_error`/`kcl_residual` 선례대로 4개 회로에서 먼저 재고 상한을 정한다.

## 8. 3단계 실행 파이프라인 — 파일/harness 함수 구조 (2026-09-04 추가)

### 8.1 배경

사용자 지적: `sizing_recipe.py`라는 파일명이 "gm/ID sizing을 실제로 수행하는 엔진"이라기보다
"사이징에 필요한 도구 모음"처럼 느껴진다. AI가 회로마다 topology를 제멋대로 다르게 해석해
일관성 없이 사이징하는 사고(이 프로젝트 실제 이력, `known-incidents.md`)를 막으려면,
**"topology 수집" → "gm/ID 방법론으로 사이징(+레이아웃 수렴)" → "결과물 산출"** 세 단계를
물리적으로 분리된 파일로 명확히 나누고, 각 단계를 대표하는 이름의 top-level harness 함수
하나가 그 안의 모든 하위 함수를 순차 호출하도록 구조화한다. self-test는 소스 파일에 인라인으로
두지 않고 별도 test 파일로 분리한다(기존 `python sizing_recipe.py` 인라인 self-test 관례에서
전환, 2026-09-04 사용자 확정).

### 8.2 3단계 구조 개요

| 단계 | 책임 | 소스 파일 | test 파일 | top-level harness |
|---|---|---|---|---|
| 1 | topology netlist + 제약 + FoM 스펙 구성 | `topology_authoring.py`(신규) | `tests/test_topology_authoring.py` | `author_topology_spec()` |
| 2 | gm/ID 방법론 기반 사이징 엔진 | `gmid_sizing_engine.py`(신규, `sizing_recipe.py` 핵심부 계승) | `tests/test_gmid_sizing_engine.py` | (엔진 함수군 — harness는 아래 오케스트레이션 파일에서 호출) |
| 2 | 오일러 패스 stick-diagram/레이아웃 | `stick_diagram.py`(기존 유지, 소스 로직 변경 없음) | `tests/test_stick_diagram.py`(신규 — 기존 인라인 self-test, `stick_diagram.py:8980`~파일 끝 약 4000줄 이관) | — |
| 2 | 사이징↔레이아웃 반복 수렴 오케스트레이션 | `sizing_layout_convergence.py`(신규, 얇은 조정 로직만) | `tests/test_sizing_layout_convergence.py` | `run_sizing_layout_convergence()` |
| 3 | instance.json + HTML report 산출 | `instance_report_builder.py`(신규) | `tests/test_instance_report_builder.py` | `build_instance_and_report()` |
| 전체 | 위 3개 harness를 순서대로 호출하는 유일한 최상위 진입점 | `gmid_design_pipeline.py`(신규) | `tests/test_gmid_design_pipeline.py`(end-to-end 통합) | `run_gmid_design_pipeline()` |

`tests/`는 `skills/analog-gmid-design/assets/tests/`에 신설한다(소스와 물리적으로 분리, 표준
pytest 관례와 동일 — 2026-09-04 사용자 확정). 각 단계는 독립적으로도 호출 가능해야 한다(예:
topology만 다시 다듬고 싶을 때 `author_topology_spec()`만 재실행) — 그러면서도
`run_gmid_design_pipeline()` 하나만 부르면 3단계가 전부 순차 실행된다.

### 8.3 Stage 1 — `topology_authoring.py`

**왜 분리하나**: topology 수집(논문/스펙 해석, netlist 확정)은 gm/ID *방법론* 실행과 완전히
다른 활동이다 — 전자는 "이 회로가 무엇인가"를 확정하는 일(사람+AI 협업, 재해석 여지가 있는
일), 후자는 "이 회로를 어떻게 사이징하는가"를 결정론적으로 실행하는 일이다. 섞여 있으면 AI가
사이징 도중 topology를 "편의상 다시 해석"하는 사고가 반복된다.

**harness**: `author_topology_spec(source_spec: dict) -> (topology.json, sizing_spec.json)`

내부에서 순차 호출:
1. netlist 등록/검증(connectivity만, 값 없음) — 기존 `load_topology()`/스키마 검증 재사용
2. `symmetry.matching_pairs`/`dispositions` 자동탐지 — 기존 analog-grammar idiom 탐지
   (`find_matching_candidates()` 등, `stick_diagram.py`에서 import) 재사용
3. gain-stage 후보(§1 스키마의 `stages[].devices.{input,cascode,load}`) 자동제안(신규 —
   단, 판정 로직은 신규 발명이 아니라 §1.4의 `gm-id-methodology.md` §13.3(current mirror
   다리가 ratio-matching인지 gain-stage load인지 판정하는 5개 구조 신호 — 구조 대칭 partner/
   diffpair branch-load partner/active_load_legs/signal_referenced_mirror_legs, 4개 회로
   전수 반례 0건으로 검증됨)를 그대로 재사용: 5개 신호 중 하나라도 파트너/레퍼런스-신호
   관계가 잡히면 `devices.cascode` 또는 그 회로의 기존 matching 소자로, 아무 신호도 안
   잡히는 소자만 `devices.input`/`devices.load` 자동 후보로 제안) — 사람이 최종 확정
4. `ideal_sources`/`passive_elements` connectivity 등록
5. figure-of-merit 스펙(`global_spec`, `stages[].gain_budget_db`, `driving_spec`,
   `gain_allocation_check`) 등록 — 사람이 확정하는 입력을 받아 스키마에 채워넣는 역할
6. 완성된 `topology.json` + `sizing_spec.json`을 `library/`에 저장
7. **`diagnose_sizing_dof()` 실행(§7.8)** — 사이징을 시작하기 전에 목표 대비 자유도를
   대조해 `overconstrained`면 여기서 멈추고 명시 보고(Stage 2로 넘기지 않는다). 스키마와
   connectivity만 보므로 LUT 조회/탐색 비용 없음

### 8.4 Stage 2 — `gmid_sizing_engine.py` + `stick_diagram.py` + `sizing_layout_convergence.py`

**파일명 근거**: "sizing_recipe"(도구 모음 느낌) → "gmid_sizing_engine"(gm/ID 방법론을
결정론적으로 실행하는 엔진이라는 정체성 명시). 기존 `sizing_recipe.py`의 LUT 인터페이스/
`size_transistor()`/사후검증 metric/`resolve_feed_vds()`/`_resolve_vertical_group()`은 그대로
옮기고, 이번 계획(§7.2)의 gain-budget-first 알고리즘(`resolve_stage_sizing()`), diode-connected
고정점 solver(§7.3의 `_solve_diode_connected_vgs_fixed_point()`), 전체회로 물리 정합성
검증기(§7.5의 `verify_node_voltage_consistency()`/`cross_check_with_spice()`)가 이 파일의
핵심부가 된다.

**harness**: `run_sizing_layout_convergence(topology_spec) -> instance_data`
(`sizing_layout_convergence.py`에 위치, 실제 계산 로직은 갖지 않고 아래 순서로 호출만 한다)

내부 순차 호출(사용자가 명시한 "사이징→레이아웃→피드백→재사이징" 루프 + ★신설 물리 정합성
검증 게이트):
0. **(v3.4) 면적 예산 확인** — `global_spec.constraints`에 `area_um2`가 없으면
   `sweep_area_power_pareto()`를 실행해 `ParetoReport`를 반환하고 **여기서 정지**한다
   (사람이 한 점을 고른 뒤 재실행). 있으면 1번으로 진행.
1. `gmid_sizing_engine.size_all_stages()` — §7.2 알고리즘으로 전체 gm_id/L/W 1차 확정
   (diode-connected 소자는 §7.3의 고정점 solver로 vds까지 함께 확정)
2. `gmid_sizing_engine.resolve_headroom()` — 기존 `allocate_stack_headroom()`/
   `resolve_feed_vds()`/`_hr_resolve_vertical_group()`으로 나머지 VDS 확정.
   **(v4.0 사실 정정)** `_resolve_vertical_group()`은 "무변경 재사용"할 수 있는 함수가
   아니었다 — `_build_theta_evaluator()`(indent 4) → `_evaluate()`(indent 8) 안의 **2중 중첩
   클로저**라서 theta 평가와 떼어내 부르는 것이 원리적으로 불가능했다. 2026-09-07 선행조치로
   6개 함수(총 401줄)를 모듈 레벨 `_hr_*`로 추출했고(자유변수 13개를 `_HeadroomTopoEnv`/
   `_HeadroomEvalEnv`로 명시화, **본문 무변경**), self-test stdout 바이트 동일 회귀를 확인했다.
   이제 이 harness가 실제로 성립한다.
3. `stick_diagram.assign_finger_geometry()` — finger/width 배분
4. `stick_diagram.check_euler_condition()`/`resolve_stack_layout()` — 오일러 패스 레이아웃
   가능성 검증
5. 4번이 실패하거나 finger 수/width가 바뀌면(레이아웃 제약으로 인한 조정) → 그 변경분을
   1번 사이징 엔진에 피드백(예: W 상한 축소로 gm_id 재탐색) → 2~4 재실행
6. 수렴(레이아웃 목표 달성 + 사이징 constraint 유지)하면 §7.5의 검증 게이트로 진입:
   `gmid_sizing_engine.verify_node_voltage_consistency(ctx)` 실행(항상, 빠름) — Violation이
   있으면 **1번으로 돌아가지 않고 즉시 실패 보고**(어느 소자/net에서 KVL/VGS 불일치가
   났는지 포함) — §3.2 P1(조용히 타협하지 않음).
7. 6번을 통과하면(파일럿 회로 최초 검증 시, 또는 `verify_spice=True` 옵션 시)
   `gmid_sizing_engine.cross_check_with_spice(instance_data)` 실행(느림, sky130 SPICE `.op`
   1회) — 여기서도 Violation이 있으면 실패 보고. 둘 다 통과해야 최종 성공.
8. 최대 반복(5번) 초과 시에도 명시적 실패 보고(조용히 타협하지 않음).

`sizing_layout_convergence.py`는 1~8단계를 순서대로 호출하는 얇은 오케스트레이션만 담고,
실제 계산 로직은 전부 `gmid_sizing_engine.py`/`stick_diagram.py`에 남는다(레이어 분리 원칙
유지, `run_topology_pipeline_with_finger_fixup()`가 이미 증명한 패턴과 동일).

### 8.5 Stage 3 — `instance_report_builder.py`

**harness**: `build_instance_and_report(instance_data) -> (instance.json 경로, report.html 경로)`

내부 순차 호출:
1. `save_instance_json()`(기존 `stick_diagram.py` 함수 이관 또는 재사용) — 사이징+레이아웃
   결과를 instance.json으로 저장
2. `render_design_report_html()`(신규 — 현재 워크스페이스마다 ad hoc하게 있던
   `build_report.py`/`build_html.py`를 skill asset으로 정식 편입) — 사람이 검토 가능한
   HTML report 생성(gm_id/W/L 표, 헤드룸 검증 결과, gain 배분 대조표, CMRR/PSRR/mismatch 등
   사후검증 metric 요약 포함)

### 8.6 최상위 파이프라인 — `gmid_design_pipeline.py`

```python
def run_gmid_design_pipeline(source_spec: dict) -> str:
    """3단계를 순서대로 실행하는 유일한 최상위 진입점 -- AI는 이 함수 하나만 호출한다
    (optimize_full_circuit_budget()의 '단일 진입점' 원칙을 3단계 구조에 맞게 계승)."""
    topology_json, sizing_spec_json = author_topology_spec(source_spec)
    instance_data = run_sizing_layout_convergence(sizing_spec_json)
    instance_path, report_path = build_instance_and_report(instance_data)
    return report_path
```

각 단계 harness는 독립 호출도 가능(예: topology만 다시 다듬고 싶으면 `author_topology_spec()`만
재실행) — `run_gmid_design_pipeline()`은 그 3개를 그대로 이어 붙이기만 한다(새 로직 없음).

### 8.7 기존 `sizing_recipe.py`와의 관계

`sizing_recipe.py`는 폐기되지 않는다 — 이번 재구조화로 그 내용이 성격별로 새 파일로
재배치된다:
- LUT 인터페이스, `size_transistor()`, 사후검증 metric → `gmid_sizing_engine.py`
- topology 스키마 검증/analog-grammar 연동 부분 → `topology_authoring.py`(이미
  `stick_diagram.py`에 있던 것과 통합 검토)
- (변경 없음) 레이아웃/euler → `stick_diagram.py` 그대로

이 재배치는 §5(마이그레이션 계획)의 "파일럿 회로 1개로 먼저 증명" 범위 안에서 함께
수행한다 — 새 gain-budget-first 알고리즘 구현과 파일 재구조화를 별개 작업으로 쪼개지 않는다
(어차피 새 함수들은 새 파일에 바로 작성되므로 추가 이관 비용이 없음).

### 8.8 self-test 분리 방침

기존 관례(`python sizing_recipe.py`/`python stick_diagram.py` 실행 시 파일 하단의 인라인
self-test 블록이 함께 실행됨)에서 전환 — **`stick_diagram.py`를 포함해 소스와 test를 물리적으로
분리한다**(2026-09-04 사용자 확정 — 처음엔 `stick_diagram.py`는 이번 재구조화 범위 밖으로
잡았으나, 사용자 지시로 범위에 포함시킴):

- `skills/analog-gmid-design/assets/tests/test_<module>.py` 형태(모듈당 1개, `gmid_design_
  pipeline.py`만 end-to-end 통합 test로 별도 성격).
- 각 test 파일은 대응하는 소스 모듈을 import해서 검증하는 표준 구조(`sizing_recipe.py`가
  지금까지 쌓아온 self-test 커버리지 — L5c 헤드룸 singleton, ideal_sources 대조 검증 등 —
  는 성격에 맞는 새 test 파일로 이관).
- **`stick_diagram.py:8980`부터 파일 끝(12923줄)까지의 `if __name__ == "__main__":` 인라인
  self-test 블록(약 3900줄)을 `tests/test_stick_diagram.py`로 이관한다.** `stick_diagram.py`
  자체의 소스 로직(오일러 패스/finger 배분/floorplan 계산 함수들)은 이번 재구조화에서 손대지
  않는다 — 이관 대상은 self-test 블록뿐이며, 이관 후 `stick_diagram.py`는 소스 함수만
  남기고 self-test import는 `test_stick_diagram.py` 쪽에서 `from stick_diagram import *`
  (또는 명시적 심볼 import)로 가져간다.
- 이관 시 회귀 확인: `python tests/test_stick_diagram.py` 실행 결과가 이관 전
  `python stick_diagram.py` 실행 결과(**`assets/tests/baseline/*.baseline.log`**, 2026-09-07
  신설)와 동일한 PASS/FAIL

  > **(v4.0 사실 정정)** v1.2가 기준선으로 지목했던 `assets/selftest_session*.log`는 쓸 수
  > 없었다: (1) 6개 전부 `sizing_recipe.py` 출력이고 `stick_diagram.py` 기준선은 **존재하지
  > 않았으며**, (2) `.gitignore`의 `*.log`에 걸려 **git에 추적조차 되지 않았다**(추적된 `.log`
  > 0건). 즉 재현 가능한 대조가 불가능했다. 2026-09-07 선행조치로 두 self-test의 stdout을
  > `tests/baseline/`에 캡처해 추적 대상에 넣고 재생성 절차를 README로 남겼다.
  >
  > 그 과정에서 **`stick_diagram.py`의 출력 7줄이 실행마다 달라진다**는 것을 발견했다(파이썬
  > 문자열 해시 랜덤화 → set 원소 순서). stdout diff를 회귀 단위로 쓰려면 먼저 이걸 고쳐야 해서
  > `_sorted_setmap()` 신설 + 정렬 출력으로 결정론화했다 — 7곳 모두 **표시 전용**이고 판정은
  > 순서 무관(`len()==0`/`==`/`in`)이라 엔진 로직은 바뀌지 않았다. `PYTHONHASHSEED` 1~5에서
  > 두 로그 모두 바이트 동일함을 확인했다. **새 비결정 출력이 들어오면 이 대조가 먼저 깨지므로
  > 그 자체가 회귀 감지기 역할을 한다**(C9/C10 계열의 구조적 방지 장치).
  집합을 내는지 대조한다 — 이관 자체가 코드 로직을 바꾸지 않으므로 결과가 완전히 같아야 함.

---

## 9. Next Steps

> 착수 지점과 전제는 **§0 이어받을 지점**에 정리돼 있다. 여기는 그 이후의 큰 흐름만 적는다.

1. **B1 5단계(배선) + 파일럿 재탐색** — §0.2. 지금 유일하게 열려 있는 작업이다.
2. 재탐색 성공 시 `vsb` 산출 수정(B9) → 노드전압 유일해 확인(다중도달 불일치 4건 = 243.5mV
   해소) → `verify_node_voltage_consistency()` 게이트 완성(§7.5)
3. `ideal_sources.value_amp` 소비 배선(B14) — `seed_currents` 경로
4. §7.6(3)의 3티어 게이트 구조 구현(T1/T2는 `extra_feasible`, T3는 `check_global_gates`)
5. §7.9 배분 DP(`solve_allocation_dp`) 구현 — `stack_headroom_slack`을 제약에 포함
6. §8 파일 구조 재배치(5개 신규 파일 + `tests/`) — 이건 위 기능이 안정된 뒤가 안전하다
7. 나머지 3개 토폴로지 이관(C7) + §4 Success Criteria 전항목 검증

**아직 안 한 것 중 큰 것**: §10의 미해결 항목(A1/A2/A6/A7/A9, B3/B5/B6/B10/B12, G1~G8,
C 정합성 잔여). 특히 **G6(stage 분할 규칙 부재)**와 **A2(`Area` 정의 부재)**는 새 파이프라인
구현 전에 결정이 필요하다.

---

## 10. 독립 검토에서 나온 미해결 항목 (★ 신설 v4.0, 2026-09-07)

계획 v3.4를 **4개 관점의 독립 검토자**가 병렬로 심사했다 — (A) 회로 물리·방법론 타당성,
(B) 구현 가능성·성능·코드 대조, (C) 문서 내부 정합성, (D) 임의 토폴로지 일반성. 각 검토자는
서로의 결과를 보지 않았고, 지적은 문서 원문·실제 코드와 대조해 검증한 뒤에만 아래에 남긴다.

v4.0은 이 중 **사용자가 결정한 3건과 코드 선행조치 3건**을 반영했다. 나머지는 아직 열려 있으며,
**유실을 막기 위해** 여기 기록한다. 각 항목은 "누가 지적했는지 / 검증 상태 / 필요한 결정"을 함께
적는다.

### 10.1 반영 완료 (v4.0)

| # | 내용 | 반영 위치 |
|---|---|---|
| D1 | `gm_i` 인과 방향을 "compensation이 먼저 고정"으로 통일, `gain-budget-first`의 의미 재정의 | §3.1 req4, §7.4 원칙2, §7.9 |
| D2 | gain 제약을 폐형식에서 `compute_metric()` 위임으로 전환(+기생 결합을 KKT 안으로) | §7.9, §7.1 `metrics` |
| D3 | theta 폐기를 "자유 탐색 변수만"으로 축소, 구조 선언은 `structural_declarations`/`feedback_loops`로 이관 | §7.1 |
| P-a | 헤드룸 클로저 6개(401줄) 모듈 레벨 추출 — `resolve_headroom()` harness가 비로소 성립 | §8.4, §2.1 |
| P-b | self-test 회귀 기준선 신설 + `stick_diagram.py` 출력 결정론화(7줄) | §8.8 |
| P-c | 소신호 MNA를 `numpy.linalg.solve`로 전환(노드 51개 6.1x) + numpy 지연 import 7곳 통합 | §7.6 실행시간 |

### 10.2 미해결 — 물리·수식 (검토자 A)

| # | 내용 | 검증 상태 | 필요한 결정 |
|---|---|---|---|
| A1 | **KKT λ 항 부호 오류**. `L = Σgm_i/x_i + μ(ΣArea−A) + λ(G − Σgain_i)`에서 `gm_i/x_i² = μ·Area_i′ **−** λ(20/ln10)/x_i`인데 문서는 `+`로 적혀 있다 | 재미분으로 확인 | 단순 정정. 더불어 **전력·gain이 gm_id에 대해 같은 방향**이라 μ>0·λ>0 동시 성립 내부해가 일반적으로 없다는 사실(케이스 3)이 사실상 공집합)도 명시할 것 |
| A2 | **`Area_i`의 정의가 문서 어디에도 없다**. `∂Area/∂gm_id`를 쓰면서 정의가 없고, 최적화가 쓰는 면적(W·L 추정)과 레이아웃 게이트가 판정하는 면적(`Σ n_fingers × pitch(L)`, §7.7 R5)이 **서로 다른 물리량**이다. 게다가 `Cc` 면적이 빠져 있다(정본 §6.4 예제 기준 Cm 1.41pF ≈ 1,400µm² > 트랜지스터 전체) | 문서에 없음 확인 | `Area = Σ(n_fingers×pitch(L)×W_finger) + Σ(C/C_density + R_area)`로 정의를 못박을지 결정 |
| A3 | ~~`min Σ ID_i`가 회로 전력이 아니다(bias 전류 누락)~~ → **2026-09-08 해소(v4.9)**. **bias 누락은 사실이 아니었다** — `sum_current`는 `devices` 미선언 시 `ctx.sized` 전체를 더하고, gain-stage 밖 39소자 107.50µA가 이미 포함돼 있다. 진짜 결함은 **직렬 중복 계상**이다: 전 소자 ID 합 **243.32µA** vs VDD 레일 유입 **86.27µA** = **2.82배**. 더 나쁜 건 배수가 branch마다 다르다는 것(`diffpair_branch_a` 8소자 vs battery 3소자) — 즉 `min sum_current`는 **"그 branch에 소자가 몇 개냐"는 설계 무관 가중치**가 붙은 전력을 최소화한다 | 실측 + metric 신설 | **부분 잔여** — `supply_current` metric을 신설·선언해 나란히 보고한다. **objective 교체는 탐색 결과를 바꾸는 설계 결정이라 아직 안 했다**(design/do 단계) |
| A4 | ~~VDS 재배분이 매칭 쌍을 깬다~~ → **2026-09-08 해소(v4.8)**. 실측하니 지적의 절반은 이미 해결돼 있었다: `matching_pairs`가 `offset`/`ratio`로 갈려 있고 **offset 3쌍은 ΔVDS=0**(헤드룸 해석기가 `_hr_vfind()` union으로 이미 강제). 진짜 gap은 `ratio`(미러) 쌍이다 — 18쌍 중 3쌍이 VDS 불일치이고 **M18_bg/M60은 ΔVDS=1.300V, V_A=2.04V로 ΔI/I=63.6%**(미러비가 설계값의 1.6배). B1(diode 고정점)을 고쳐도 25.0%가 남아 **독립 문제**다. 다만 "VDS도 같게 강제하라"는 미러에 물리적으로 틀리다 — 레퍼런스(diode)와 출력(부하 노드)의 VDS가 다른 것이 정상이다. 그래서 제약이 아니라 **재는 값**으로 처리: `mirror_ratio_error` metric 신설(unit `%`, `aggregate` max/rss). 파일럿 실측 max **63.606%** / rss 71.912% | 실측 + metric 신설 | **부분 잔여** — metric은 만들어 배선했으나(선언만으로 계산·보고됨) **상한 제약은 아직 안 걸었다**. 먼저 4개 회로에서 재보고 나서 값을 정한다(값을 지어내지 않는다). §7.9 VDS 재배분이 이 비용을 보게 하는 것은 design/do 단계 몫 |
| A5 | ~~온도·공정 코너 전무, gm_id가 300K 천장으로 밀린다~~ → **2026-09-08 부분 해소(v4.9)**. 구체 우려는 **현 파일럿에서 미발생**: gm_id 최대 24.68(M6)로 350K 천장 27.6보다 낮다(250/300/350K 어느 천장도 초과 0개). 그런데 **더 근본적인 문제**를 찾았다 — 엔진에 온도 개념이 noise metric 하나뿐(`temperature_K` 기본 300)이고 사이징 어디에도 없으며, **LUT npz에 코너/온도 메타데이터가 아예 없다**. 즉 사이징 결과가 어느 조건에서 유효한지 산출물이 말할 수 없다. 생성기 코드상으로는 `__tt.pm3.spice`(TT) + `.temp` 미지정(ngspice 기본 27°C)이다 | 실측 + 생성기 코드 확인 | **부분 잔여** — 생성기가 `corner`/`temp_c`를 기록하도록 고치고 `lut_conditions_from_npz()`가 기록 없으면 **조용히 300K를 가정하지 않고** `recorded=False`를 돌려주게 했다. 기존 8MB npz는 재저장하지 않았다(재생성 시 기록됨). **코너 스윕 자체는 여전히 범위 밖** — §2.2에 명시 필요 |
| A6 | **ICMR·출력 swing·THD가 §7.9 헤드룸 하한 목록에 없다**. `output_swing`은 하한으로 쓰인다고 서술되나 스키마에 슬롯이 없다(선언 출처 없는 제약 = 상수 폴백, C1) | 문서 확인 | 스키마 슬롯 신설 여부 |
| A7 | **고정점 수렴이 "20회 이내"라는 요구사항으로만 존재**하고 논증이 없다. 단순 대입 반복 대신 `g(v)=f(v)−v` 단조성을 이용한 **bisection**이면 유일해·유한회 수렴이 보장되고 "격자 안에 해 없음"을 명시적 실패로 낼 수 있다 | 문서 인용 확인 | 구현 방식 확정(대입 반복 vs bisection) |
| A8 | ~~스택 diode 연립 solver가 필요하다~~ → **2026-09-08 재해석(v4.13)**. 실물에 **diode 2개 직렬 스택이 존재함은 확인**됐다(`biasgen_vom/vop_battery_a`의 M11a+M11b, `..._battery_b`의 M14a+M14b) — 그 때문에 22개 스택 중 **7개가 예산 초과**한다(최대 1.346V). 다만 **연립 solver는 필요 없다**: diode의 Vgs는 gm_id가 정하는 **종속값**이지 예산을 나눠 갖는 자유변수가 아니므로, 스택 KVL은 방정식이 아니라 **gm_id 조합이 만족해야 하는 제약**이다 (`Σ Vgs_k(gm_id_k,...) + Σ vds_j ≤ 예산`). v4.2의 분리형 DP가 이미 다루는 형태라 **제약 추가**로 처리한다 | 전수 사전계산 | **2026-09-08 계기판 배선 완료(v4.14)** — `stack_headroom_slack` metric 신설·선언(실측 **−1.3456V**, 사전계산과 일치). 아직 **constraint로 걸지 않았다** — 지금 걸면 즉시 infeasible이라, 먼저 재탐색으로 해를 찾은 뒤 건다. 다음: B1 5단계(배선)+재탐색 |
| A9 | **SPICE 교차검증의 허용오차 미정**. 방법론 §6.5가 "LUT 1차 계산은 10~20% 오차"라고 적고 있는데 §4.1 DoD는 "일치"만 요구한다 → 사후에 임의 임계값을 정하게 된다(C1 재발) | 문서 확인 | 노드전압 절대오차·전류 상대오차를 **미리** 못박을 것 |
| A10 | ~~v3.3 근거 실측치가 물리적으로 불가능~~ → **2026-09-07 조사 완료: 기각.** "28→77.6"은 dB가 아니라 **선형 `gm/gds` 비**였다(dB로는 28.98→37.80). `V_A` 5.62→2.98V로 정상이고 면적 4000배 폭발도 실재한다(`IDu`가 1000배 하락하는 deep weak inversion) | LUT 직접 재현 | **없음** — v3.3 논거 유지. 다만 §7.9 표에 단위를 명시했다(선형비/dB 혼용이 오독을 유발) |
| **A12** | **★ metric 이름이 단위를 거짓말한다(실물 결함)**. 파일럿 실제 설계점에서 `power_uA`=0.000243323(실제 **A**, 직접 합산 243.32µA), `area_um2`=1.17156e-10(실제 **m²**, 직접 합산 117.16µm²) — 정확히 10⁶·10¹²배. 엔진은 SI로 반환하는데 이름은 µ 단위다. **지금까지 안 드러난 이유**: 4개 토폴로지 어디에도 `area_um2` 제약이 선언돼 있지 않고, `power_uA`는 objective(최소화)라 상수배가 순위를 안 바꾼다 | 실측(metric 값 vs 51소자 직접 합산) | **★ 시급**. v3.3/v3.4가 `area_um2 <= 2000`을 핵심 제약으로 도입하는데, 그대로 두면 2000µm² 의도가 **2000 m²**와 비교돼 항상 만족 = 제약이 없는 것과 동일해진다 → v3.3의 "면적 예산이 gm_id의 실질 상한" 논거, v4.2 DP의 면적 bin, v3.4 Pareto의 A_min/A_max가 **전부 무력화**. 선택지: ① metric이 이름대로(µA/µm²) 반환하도록 변환 ② 이름을 `power_A`/`area_m2`로 정정 ③ metric 선언에 `unit` 필드를 필수화하고 로드 시점에 이름-단위 불일치를 거부. **공유 엔진 동작 변경이라 사용자 승인 필요** |
| **A11** | **★ A10 조사에서 새로 발견: `gm/gds`가 `gm_id`에 단조가 아니다.** VDS 0.6/0.9/1.2/1.5에서 각각 6/8/11/12개 구간이 감소하고, 최댓값이 `gm_id ≈ 20.5/20.0/18.0/18.0`에 있다(VDS=0.4에서만 단조). 정점 위 구간은 **gain·면적 둘 다 나빠지고 전력만 좋아지는 지배당한 영역**이다 | LUT 정밀 스윕으로 확인 **2026-09-07 해소** — §7.9 해법을 **분리형 DP**로 교체(v4.2). "해석해"·"유일 결정" 표현 철회. `argmax(gm/gds)` 상한은 DP가 격자를 전수로 훑으므로 별도 상한 없이 자동 배제된다 |

### 10.3 미해결 — 구현·성능 (검토자 B, 코드 대조 완료)

| # | 내용 | 검증 상태 | 필요한 결정 |
|---|---|---|---|
| B1 | ~~§7.3 티어①이 실제 버그 경로를 안 지난다~~ → **2026-09-07 해소(v4.3)**. 계측 확증: `resolve_feed_vds()`는 51소자 중 **4개**만 정하고 **diode 소자는 0개**다(최대 경로는 `allocate_stack_headroom()` 28개). vds 기입 지점은 **7곳**이라 한 함수만 고쳐선 못 덮는다. diode를 `vds_match_vgs_of`의 **자기참조 특수 케이스**로 보고 기존 pre-pass를 확장 + 7개 지점을 `set_device_vds()` 단일 setter로 수렴(§7.3) | monkeypatch 실주행 계측 + 정적 전수 | **없음** — 설계 확정. 구현 시 grep 테스트로 원시 대입 잔존 금지 |
| B2 | ~~CMRR/PSRR을 stage-local 콜백으로 만들 수 없다~~ → **2026-09-07 해소(v4.4)**. 실측 확증(`KeyError: 'M6' 소자가 ctx.sized에 없다`). 13개 metric을 전수 분류해 **T1 stage-local 4개 / T2 stage-분해가능 1개 / T3 기약 전역 8개**로 나누고 게이트도 3티어로 재작성. `gain_stages_sum`이 정확히 분해됨을 확인(stage 합 = 전체, 차이 0.00e+00)해 DP가 대리가 아닌 **진짜 metric**을 쓸 수 있음도 확정. T3 게이트 1회 0.72 ms로 비용도 문제없음 | 실측 분류 + 비용 측정 | **없음** — §2.1의 `make_cmrr_psrr_feasibility_check()`는 삭제, `check_global_gates()` 신설 |
| B3 | **`resolve_stage_sizing()` 시그니처에 `vds`/`vs`가 없다**. 모든 LUT 호출이 필수로 요구하는데 §7.9 Phase 1의 VDS 예산이 §7.2/§7.6으로 전달되지 않는다 | 코드 확인 | `resolve_stage_sizing(stage_spec, ID, luts, vds_budget, vs_by_device, constraints)`로 확정 |
| B4 | ~~실행시간 예산 항목이 계획에 없다~~ → **2026-09-08 해소(v4.6)**. 직접 측정: **전체 평가 1회 274.5 ms**가 L_combo 단위 비용이다(stage 사이징 3.15ms로 세면 44배 틀린다 — 전역 게이트가 51소자 전부를 요구하므로). L 자유도 3개, 기본 정책(bounds 내 앵커 4개, 64 combo)에서 전수 17.6s / 중첩 포함 **2.9분**. densify 41점은 5.3시간이라 기본 금지. `presolve_warm_start()` 16.5s는 루프 밖 1회 규약. **부수 정정: R3의 "앵커 4개"는 stale이 아니었다** — LUT 전체는 7개지만 파일럿 theta bounds `[0.15,1.0]µm` 안이 4개라 둘 다 맞고 문맥이 달랐다(검토자 지적을 그대로 받았으면 잘못 고쳤을 것) | 실측 | **없음** — DoD에 wall-clock ≤ 5분 신설 |
| B5 | **C6이 사고19를 안 막는다**. 사고19의 underdetermined는 vertical_stack 내부 헤드룸 KVL(미지수 2/방정식 1)인데 `diagnose_sizing_dof()`는 gm_id/전류/L/Cc 넷만 세고 **VDS 미지수·KVL 방정식을 세지 않는다** | 문서 확인 | DOF 진단에 "stack별 (vds 미지수 vs KVL+참조 등식, 랭크)" 축 추가 |
| B6 | **§7.8 DOF 진단이 부등식을 등식처럼 센다**. 부등식은 활성일 때만 자유도를 소비하는데 목표 수만 세어 `overconstrained`면 **반복을 아예 시작하지 않는다** → 오탐 하나가 곧 hard stop | 문서 확인 | 등식 제약만 대조에 쓰고 부등식은 경고로 낮출 것 |
| B7 | ~~§7.5 프로토타입 "그대로 이식"은 과대평가~~ → **2026-09-08 확인(v4.10)**. 네 지적 중 **셋은 코드로 확인**(set 순회 / `not progressed and not unresolved` 논리오류 / 다중도달 일치검사 미구현 / VGS 3쌍 하드코딩). 다만 **set 순회는 이 회로에서 실제 차이를 만들지 않았다**(순회 순서를 뒤집어도 노드값 32개 전부 동일) — 잠재 위험이지 실현된 결함은 아니다. 반대로 **다중도달 미검사는 실물에서 위반이 나온다**: 21건 중 **4건이 243.5 mV 불일치**(Vop1/Vom1에 M2a/M2b/M3a/M3b 경로가 0.6565 vs 0.9000으로 도달). 프로토타입은 이걸 `elif`에서 검사 없이 discard한다 | 코드 확인 + 실측 | **없음** — "그대로 이식" 표현을 §2.1/§7.3에서 내리고, §7.5의 다중도달 검사가 잡아야 할 실물 위반 4건을 DoD 기준값으로 삼는다 |
| B8 | ~~§7.5가 KCL을 검증하지 않는다~~ → **2026-09-08 해소(v4.10)**. 실측: 내부 노드 30개 중 **3개**가 잔차 >1nA이고 **`Vx`(입력쌍 소스)가 −3.96µA**, 레일은 vdd −86.27 / gnd +88.93µA로 **2.66µA** 어긋난다. `_metric_kcl_residual()` 신설(부호규약 명시, `ideal_sources.value_amp` 포함, `value_amp=null`이면 지어내지 않고 그 노드 skip, `exclude_nets`는 이유를 선언에 적어야 함) | 실측 + metric 신설 | **없음** — `kcl_residual_uA`로 선언·배선(실측 **3.9601µA**). 상한 제약은 아직 안 건다(4개 회로에서 먼저 잰다) |
| B9 | ~~`vs`가 39소자에서 0.0~~ → **2026-09-08 원인 확정(v4.11), 수정 대기**. `vs`의 정의를 LUT 생성 넷리스트(정본)에서 확인: `xdut d g 0 b`로 **source는 항상 노드 0**이고 VS가 바꾸는 것은 벌크 전압(`vb_dc = vb_sign·VS·(−1)`)이라 **VS 축은 소스-벌크 역바이어스 |V_SB|**다. 벌크가 레일에 묶이면 NMOS는 `V_source`, PMOS는 `vdd − V_source`가 된다. 이 정의로 51소자를 검산하니 **25개 불일치**(일치 26개는 전부 source가 레일인 소자). 세 부류: ① 비레일 source인데 vs=0 — 최대 **−1.3000V**(M37a/M37b) ② 레일 source인데 vs≠0 — 4개(M60/M61/M38/M68) ③ **M9a/M9b·M18a/M18b는 값이 정확히 서로 바뀜**(M9a 기대 0.8060인데 0.6565, M9b 기대 0.6565인데 0.8060). **원인**: `_hr_resolve_vertical_group()`의 `other_entry.setdefault("vs", ref_vds)`가 **kind를 보지 않는다** — `ref_vds`는 vss 기준 체인의 VDS 합이라 NMOS엔 맞지만 PMOS엔 `vdd − V_source`여야 한다. 게다가 topology의 `device_roles[*].vs`(선언 0.0)와 이 전파가 **경쟁**해 어느 쪽이 이기는지가 순서에 달렸다(C2). C1(물리 미검증)+C4(kind 무시)+C2(순서 의존)가 한 줄에 겹친 자리 | LUT 넷리스트 + 실측 51소자 | **★ 수정 승인 대기** — 고치면 LUT 조회가 달라져 W/gm이 바뀌므로 재사이징이 필요하다 |
| B10 | **§7.10이 사고4 경계를 건드린다**. `select_L_by_role()`의 cascode/signal 거부는 사고4 정정의 결과이고 §5가 "별도 승인 필요"라 못박은 경계인데, §7.10이 이를 부수 효과처럼 없앤다 | 코드 docstring 확인 | 명시적 승인 필요 |
| B11 | ~~C1~C10 중 5개가 빈 약속~~ → **2026-09-08 해소(v4.5)**. 실측 확증: `review_needed`·"전역 유일성"·"connectivity에서 유도"가 각각 **C 표 안에서만 1회** 등장했다. 표를 **"강제 테스트" 열이 있는 형태로 재작성**하고, 지금 돌리면 실패하는 것(C1 16/16 tol 초과, C4 role만 바꿔도 vds 0.2/0.3/0.6, C5 게이트 19개 중 4개만 blind spot 명시)을 **실패한다고 적었다**. 담당 절 열은 제거(C7의 §5가 정반대 내용, C10의 §7.6에 캐시 서술 없음 — 어긋남이 반복되던 열) | 정적 grep + 실측 | **없음** — §4.1 DoD가 10개 테스트 전원 PASS를 완료 조건으로 건다 |
| B12 | **결정론 규칙이 계획에 없다**. `for name in set(...)` 패턴이 엔진에 아직 남아 있다 | 코드 확인 | §3.2 P1에 "모든 반복은 정렬된 시퀀스 위에서만" 규칙 + grep 테스트 추가 |
| B13 | **추적성**. 기존 엔진은 `_L_source` 같은 출처 태그를 남기는데, 새 파이프라인에서 vds/gm_id/L이 **어느 티어·어느 Phase에서 확정됐는지** 남기는 규정이 없다 → C2 사후 디버깅 불가 | 실측 확인 | `_vds_source`/`_gm_id_source` 태그를 DoD에 넣을지 |
| **B14** | `ideal_sources.value_amp` 정책 → **2026-09-08 사용자 확정(v4.12)**: **null이면 자유탐색, 값이 있으면 그 값을 실제 전류로 쓴다.** 파일럿 Iref는 1.2µA가 선언돼 있으므로 **고정 대상**이고, theta `r_biasgen`의 자유도는 그만큼 줄어든다. `kcl_residual`은 선언값이 있으면 그것을 실제 전류로 세므로 현재의 1.851배 괴리(선언 1.2µA vs 사이징 0.6484µA)가 **잔차로 드러난다** | 사용자 결정 | **★ 엔진 미구현** — 아직 `value_amp`를 소비하는 경로가 없다. B1+vs 구현 시 `seed_currents`로 배선한다 |
| **B15** | ~~★신규(v4.16)~~ → **① 2026-09-08 해소(v4.17), ③ 2026-09-08 완료(v4.18)**. ① leave-one-out 실측으로 **배열별** 결정(ID/GM/GDS=로그, CGG=선형) — gm/ID 곱선 오차 중앙 13.70→2.63%(pmos), 최악 17,884.9→33.6%. ③ L 앵커 7→12개(0.20/0.25/0.30/0.425/0.70 중간 삽입, 체크포인트를 L값 기반 이름으로 마이그레이션해 중간 삽입 제약 해소) | 원문 → **★신규(v4.16, 아무도 지적 안 함) — LUT의 L 보간이 PMOS gm/ID를 비물리 값으로 만든다.** `_gm_id_curve()`가 ID는 로그·GM은 선형으로 보간해 두 보간이 불일치한다. 앵커 사이에서 PMOS gm/ID가 **403 / 5,517 / 56,646**까지 오른다(물리 상한 ≈30~38). PMOS는 L=0.15↔0.35µm에서 같은 VGS의 ID가 6자릿수 차이(DIBL, 물성은 정상)라 기하평균 vs 산술평균 괴리가 **207배**로 증폭된다. NMOS는 무사. `L_stage2out_p`/`L_cascode` theta가 이 대역을 5nm 격자로 실제 탐색한다 | 실측(`tests/probe_lut_L_interpolation.py`) | **★ B1 재탐색의 차단 사유** — §0.3이 예상한 해(`L=0.15~0.45µm`)가 정확히 오염 대역이다. 후보 ①일관보간(폭발 제거·앵커 보존, 그러나 정확도 미보장) ②앵커 고정(유효 앵커 4개뿐) ③LUT 재생성(근본 해결, 중간 삽입 제약) — **전부 승인 대상** |
| **B16** | ~~step 2 재설계 필요~~ → **2026-09-08 해소(v4.17)** — `apply_diode_self_consistent_gm_id()` 신설·배선(gm_id_role 루프 직전), 헤드룸 배분기에 `diode_vds_window()` 구간 제약 추가. 원문 → **step 2 재설계 필요 — 헤드룸 시점에 diode의 `gm_id`가 없다(0/16 실측).** §0.2 step 2가 전제한 `solve_diode_connected_vds(gm_id, ...)` 호출이 그 시점에 불가능하다. 다만 `Vgs=Vds` 구속은 양방향이라 `gm_id = lut.gm_id_for_vgs(vds, L, vds, vsb)`(O(1), 기존 함수)로 **현재 순서를 유지한 채** 배선 가능하다 — 80점 왜복 검산에서 76점이 오차 1mV 미만으로 일치(어긋난 4점은 B15 오염 대역) | 실측(`tests/probe_diode_gmid_readiness.py`) | **diode의 gm_id를 자유 탐색 변수에서 제외**하고 종속값으로 확정하는 것이 대가 — 승인 필요 |
| **B17** | ~~★신규(v4.19)~~ → **2026-09-08 해소**. 엔진이 `matching_pairs`에 **L만 전파하고 gm_id는 전파하지 않았다** — VDS는 `same_as_device`/vertical stack이, W는 gm_id가 결정하므로 **gm_id 하나만 무방비**였다. 매칭 쌍 21개 중 6개가 갈리고, 그중 3쌍(M2a/M2b, M3a/M3b, M37a/M37b)은 `L/ID/vds/vsb`가 전부 같은데 gm_id만 다르다(한쪽은 권위 있는 출처, 다른 쪽은 `gm_id_role` 루프의 독립 탐색). L 전파 루프와 같은 구조로 gm_id 전파를 추가하되 **동작점이 완전히 같은 쌍만** 대상으로 좁혔다 | 실측(`tests/probe_matching_pair_divergence.py`) | **없음** — 갈리는 쌍 6→3개, 면적 1050.40→936.38µm², 레이아웃 복구가 더 이상 W를 안 건드린다 |
| **B18** | ~~★신규(v4.19)~~ → **2026-09-08 해소**. 레이아웃 재검증이 **전역 metric을 통째로 건너뛰었다** — `_collect_device_refs()`가 spec에 이름이 적힌 소자만 모으는데 `area_um2`처럼 `devices`를 안 쓰는 metric은 참조가 빈 집합이라 "무관"으로 분류됐다. 전 소자를 쓰는데 건너뛴 metric 6개(`power_uA` 목적함수 포함) + 소자 미명시로 건너뜀 전체회로 metric 3개(`cmrr`/`psrr` 제약 포함). 선언된 제약 5개 중 `gain_db` 하나만 재검증되고 있었다. **전부 재계산으로 전환**(비용 실측: 8회 호출 × 1.6ms = 전체의 0.01%) | 실측(`tests/probe_revalidation_scope.py`) | **없음** — 면적 제약이 실제로 지켜진다(cap 800에서 792.87µm²) |
| **B19** | **★신규(v4.19) — 미러 3그룹의 VGS가 물리적으로 불가능하게 벌어져 있다.** (v4.20 정정: 11소자가 아니라 **18소자**다 — 아래 B19' 참고.) `M18_bg/M8/M13/M17/M22/M60/M61`(PMOS, gate=Vbias1, source=vdd)과 `M10/M12/M19/M21`(NMOS, gate=Vbias4, source=gnd)은 게이트·소스를 공유하는 **진짜 전류미러**라 VGS가 KVL로 강제 동일해야 하는데, 사이징은 최대 **464mV** 벌려놓았고 미러 규약(ID비==W비)도 전부 깨다(M8은 1530배). 세션38의 `gm_id_match_vgs_of`와 같은 클래스인데 이 소자들은 그 필드가 없다 | 실측(`tests/probe_ratio_pair_analysis.py` → `probe_mirror_design_space.py`) | **2026-09-09 결론 번복 — 성립한다. 회로 설계 판단이 아니라 배선 과제다.** 설계공간을 실제로 훑으니 세 그룹 모두 해가 있다(아래 B19' 참고) |
| **B19'** | **★신규(v4.20) — B19의 대상과 결론이 둘 다 틀렸다.** ① **대상**: 앞선 조사는 `symmetry.matching_pairs`에 **선언된** 그룹만 봐서 11소자로 셌는데, VGS 동일 강제는 선언이 아니라 게이트·소스 공유라는 connectivity에서 나온다. 넷리스트를 전수로 세면 **18소자 3그룹**이고, **6소자(`M5 M6 M7 M38 M66 M68`)는 어떤 matching_pair에도 안 나온다** — 그중 **M6/M5는 diffpair tail**(회로의 주 전류), **M66은 NMOS 그룹의 diode 레퍼런스**(즉 그 그룹은 레퍼런스 없이 분석됐다), **M7/M36a 그룹은 통째로 누락**(M36a는 이 계획서 Executive Summary가 지목한 원래 버그의 대표 소자다). ② **결론**: VGS를 현재값에 고정한 채 물었고, W를 깨진 `gm_id_to_id_density()`로 구했다(B20). VGS를 자유변수로 두고 다시 재면 **세 그룹 모두 성립**한다 — PMOS Vbias1 20조합/최소 22.90µm²(L=0.20µm, VGS=0.75V, gm_id 15.42~15.70), NMOS Vbias4 9조합/50.28µm²(L=0.15µm, VGS=0.55V), PMOS Vcmfb 36조합/0.77µm². 합 **73.95µm²**인데 **지금은 M18_bg 혼자 38.6µm² + M66 혼자 61.6µm²**라 제대로 강제하면 **면적이 오히려 준다**. 부수: `k_Iref`는 지렛대가 아니다(0.25~15배에서 성립조합 20→13개, W∝ID라 비율이 안 변함) — 진짜 지렛대는 **공유 VGS**다. B9(vsb)는 NMOS 그룹을 최대 **8.07배** 부풀린다(M38의 vsb가 0이어야 하는데 0.8625) | 실측(`tests/probe_mirror_design_space.py`) | **✅ 2026-09-09 사용자 확정 — 둘 다 답을 받았다.** (가) **18소자 전부를 미러로 강제한다. tail M5/M6를 bias 미러에 묶는 것이 설계 의도다.** (나) **공유 VGS는 gain 기준으로 고른다** — 면적이 아니다. 근거(사용자 원문): "첫번째 differential input 단의 tail이기 때문에 gain에 직접적으로 영향을 미치는 id전류를 만들고 있어." 따라서 `probe_mirror_design_space.py`가 준 **면적 오름차순 랭킹은 기준이 틀린 것**이고, `probe_mirror_gain_ranking.py`가 같은 조합을 엔진의 실제 `gain_db`로 다시 줄 세운다. 남은 것은 배선뿐 — 기전은 이미 있다(nmcnr M203/M204의 `gm_id_match_vgs_of`, 세션38과 같은 클래스). **다만 B20이 미해결인 채로 배선하면 PMOS 2개 그룹의 W가 깨진 경로로 계산된다 — B20이 먼저다.** **2026-09-09 gain 랭킹 실측(6480조합)**: gain 최적은 두 신호경로 그룹 모두 **L=4.0µm**(PMOS VGS=1.10 / NMOS VGS=0.60)이고 `gain_full_circuit_db` **89.82dB**(미러면적 1775µm², 전체 2535µm²). 면적 최소 조합(73.95µm²)은 63.72dB로 **gain 순위 6423/6480 = 사실상 최악** — 기준을 바로잡지 않았으면 정확히 반대로 골랐다. 그룹별 지렛대: pmos:Vbias1 폭 20.8dB / nmos:Vbias4 폭 20.0dB / **pmos:Vcmfb 폭 0.0dB**(CMFB 경로라 gain과 무관 — 이 그룹만은 gain이 기준이 될 수 없고 다른 기준이 맞다). **그리고 gain 최적점 L=4.0µm가 정확히 B20이 가장 심하게 무는 구간**이라, B20 선행은 순서 위생이 아니라 실질이다 |
| **B20** | **★신규(v4.20) — `_solve_vgs()`가 단조를 전제하는데 PMOS LUT는 비단조다. W가 조용히 틀린다.** `_solve_vgs()`는 docstring에 "gm/ID는 VGS에 단조감소"라 적어놓고 `np.argsort(gm_id_vals)` 후 `np.interp`로 역보간한다. 비단조이면 **서로 다른 branch의 VGS가 정렬에서 뒤섞여** VGS 축에서 인접하지도 않은 두 점 사이를 보간한다. 이 함수는 `gm_id_to_id_density()`(=`W = L*ID/IDu`의 분모)·`gm_gds_ratio()`·`fT()`·`cgg_absolute()`가 전부 첫 줄에서 부르므로 **모든 W 계산의 뿌리**다. raw LUT(보간 없음)에서 확인: PMOS L=0.15µm/VDS=0.90에서 gm/ID가 VGS 0.41→0.64 구간에 14.19→15.34로 **오르다** 꺾인다(ID 자체는 단조증가라 데이터가 깨진 건 아니다 — 저전압 쪽 누설로 보인다). **NMOS는 전 구간 단조라 무사하다.** 범위: `VDS>=0.15` 격자 2700점 중 비단조 75.3%인데, 상승 대부분이 약반전 꼬리(gm/ID 26~31)라 그것만 보면 과장이다 — **탐색범위 `gm_id_grid`(4~24)와 겹치는 것은 53.6%**이고 겹칠 때 중앙값 폭이 **20.0**(=탐색범위가 통째로 이중값). 위험은 두 축에 몰린다: **vsb**(0V 43.3% → 0.8V **95.7%**)와 **긴 L**(L=0.30~1.00µm는 완전 단조인데 L=1.5/2.5/4.0µm는 전부 탐색범위와 겹침). 파일럿은 theta bounds가 `[0.15,1.0]µm`이고 대부분 vsb=0이라 거의 안 물리지만 **실제로 2소자가 물렸다**: `M18a`/`M9a`(vsb=0.8003, vds=0.0587)의 W가 1.0177µm인데 강반전 branch의 올바른 해는 0.4306µm — **2.36배**, 오류 없이 조용히 | 실측(`tests/probe_gm_id_monotonicity.py`) | **✅ 2026-09-09 해소(사용자 승인 후 수정)** — `_solve_vgs()`를 **rightmost root**로 재작성했다(목표를 품는 가장 오른쪽 구간에서만 보간, 곡선 범위 밖이면 명시적 실패이며 비단조 사실을 오류 메시지에 적는다). 검증 4건: ① 문제 지점 VGS 1.3124→**1.5047V**로 독립 계산한 올바른 해와 일치 ② **NMOS 전 격자 16,186건 구/신 완전 동일**(같은 방향·같은 연산 순서 `slope*(x-x0)+y0`로 구현) ③ `two_stage_ota` 실주행에서 달라진 조회 **1,895건이 전부 긴 L(2.9~3.7µm)**이고 **Δ가 전부 양(+)**(강반전 해로 이동) — 최악은 `gm_id=6, L=3.71µm, vds=0.30`의 **0.719→1.333V** ④ 파일럿 재탐색 정상 완주, 제약 5개 전부 만족. 비용 실측: 호출 1회 4.95→5.85µs(1.18배)인데 이 함수가 평가 1회(465ms)의 14.0%라 **순증가는 2.55%**. 기준선 2개는 각 1줄씩 의도적 갱신(사유는 `tests/baseline/README.md` 갱신 이력) |
| **B20 보강** | **2026-09-09 추가 실측 — 선택지 ①을 그대로 쓰면 안 된다.** "정점 오른쪽만 쓰면 단조"라고 가정했는데 실제로는 비단조 2032점 중 **682점(33.6%)만** 그렇다. 나머지 1350점은 정점 오른쪽에도 상승이 있다. 다만 그 크기를 재보니 **중앙 0.606% / 90분위 2.03% / 최대 2.20%**(상승 횟수 중앙 2회)로 **LUT 수치잡음**이지 별개 branch가 아니다 — 약반전 쪽 주 봉우리(8% 규모, VGS 0.50 vs 0.71로 IDu가 170배 갈림)와는 성격이 다르다. **따라서 올바른 정식화는 "정점 오른쪽을 자른다"가 아니라 "가장 큰 VGS 해(rightmost root)를 취한다"다** — 2% 잡음이 만드는 미세 교차는 VGS 축에서 서로 인접해 오차가 무시할 수준이고, 목표가 전역 최댓값을 넘으면 해가 없어 깨끗하게 실패한다. 선택지 ②는 단독 불가(탐색범위와 겹치는 동작점 53.6%라 파일럿이 즉시 멈춘다), ③은 데이터를 바꿔 진짜 약반전 설계를 막는다 | 실측 | **추천: ①′ rightmost root + 전역 최댓값 초과 시 명시적 실패**. 승인 필요 |
| **B21** | **★신규(v4.22) — 선언된 gain 제약이 미러 18소자를 구조적으로 못 본다.** `gain_db`는 `{"type":"gain_stages_sum","stages":[["M1a","M4a","M2a","M3a"],["M15","M16"]]}`로 **소자 6개**만 더한다. 미러를 (L,VGS) 6480조합으로 강제해도 `gain_db`는 **65.5547dB로 완전 불변**(Δ=0.0000)인데, 같은 조합에서 전체회로 MNA `gain_full_circuit_db`는 **63.67~89.82dB로 26.15dB 벌어진다**. 그런데 `M19.drain=Vom1`, `M10.drain=Vop1` — **stage1 출력노드 그 자체**라 그 gds가 이득을 직접 깎는다. 즉 **선언된 제약 `gain_db >= 54`는 26dB짜리 실효과에 눈이 멀어 있고**, 목적함수(`power_uA` 최소화)는 그 눈먼 제약만 지키면 되므로 미러를 마음대로 나쁘게 만들 수 있다. (위생검사: 같은 스윕에서 `area_um2`는 6480개 전부 다른 값 → ctx 패치는 metric에 정상 반영됨. 즉 Δ=0은 진짜 무감도다.) B18(재검증이 전역 metric을 건너뜀)과 같은 클래스지만 이건 **metric 선언 자체의 범위** 문제다 | 실측(`tests/probe_mirror_gain_ranking.py`) | **★ 결정 필요** — ① 제약을 `gain_full_circuit_db`로 바꾼다(정확하지만 매 평가에 MNA) ② `gain_db`의 `stages`에 부하 소자를 추가한다(누가 부하인지 판정 규칙 필요 = G6와 같은 문제) ③ 둘 다 제약으로 걸고 괴리를 metric으로 감시. §10.2 A6/§10.4 G6와 얽힌다 |
| **B22** | **★신규(v4.24) — B19' 배선이 드러낸 다음 차단막: `diode_vds_window()`가 diode 자신의 W_bounds만 본다.** 미러 15소자에 `gm_id_match_vgs_of`를 선언해 실제로 배선했더니(그 자체는 정상 동작 -- 15소자 전부 강제되고 레퍼런스 3개 자격 OK) **SLSQP 40회 전부 infeasible**이고 이어서 레이아웃이 `cmfb_tail`(M37a/M37b/M38)에서 공통 finger 폭을 못 찾는다. 원인을 소자 단위로 규명: 미러가 강제되면 그룹 VGS가 diode 레퍼런스의 VDS로 통일되는데, **헤드룸 배분기가 diode에 구간의 `lo`를 준다**(`allocate_stack_headroom()` docstring이 이미 경고하고 있었다 -- "`lo`를 고르는 것은 **면적을 크게 잡는 쪽**이다(W(v)가 감소함수라 lo↔W최대)"). 미러 강제 전에는 그게 diode 혼자의 면적 문제였지만, **이제 그룹 전원의 W를 결정한다**. 실측: 6소자가 상한을 초과하고 최악이 66.7배다 — `M8`/`M17` 1427.9µm(7.1배), `M10`/`M19` 2153.0µm(10.8배), `M5` 12623.3µm(63.1배), `M38` 13339.9µm(66.7배). 필요한 VGS는 **pmos:Vbias1 ≥ 0.80V**(현재 0.675), **nmos:Vbias4 ≥ 0.55V**(현재 0.375)이고, `pmos:Vcmfb`는 지금도 성립한다(M7이 1.2µm). 부수 확인: 그룹 안에서 **L이 갈린다** — `L_role="mirror"`는 `L_min×2.5=0.375µm`, `bias_replica`는 `×1.2=0.180µm`인 **하드코딩 상수**(`_L_ROLE_MULTIPLIERS`)라 theta가 아니다 | 실측(`tests/probe_mirror_infeasibility.py`, `probe_mirror_wiring_readiness.py`) | **✅ 2026-09-09 구현 완료(사용자 승인)** — `diode_vds_window(..., mirror_members=())`로 확장. 후보 vds마다 diode 자신뿐 아니라 **VGS를 공유하는 소자 전원**의 W가 한계 안인지 본다. 설계 결정 3건: ① **선언 기반 옵트인**(connectivity가 아니라 `gm_id_match_vgs_of` 선언을 본다 — 미배선 self-test **diff 0줄**로 무영향 확인) ② 종속의 vds가 아직 미정이면(헤드룸이 스택별로 풀리는데 diode 스택이 **가장 먼저**라 실측상 종속 7개 전부 미정) **역할별 `min_vds`를 바닥으로** 쓴다 — IDu가 vds에 증가함수라 안전한 방향이고 보수성 대가는 실측 **격자 한 칸(0.0375V)** ③ 종속의 L/ID가 미확정이면 **조용히 건너뛰지 않고 명시적 실패**(§3.2 P1). 부수로 `id_density_at_vgs()` 신설 — VGS를 아는 호출자가 `gm_id_to_id_density()`로 왕복하면 비단조 구간에서 다른 branch로 튄다(B20). **효과 실증**: 같은 theta에서 배선+B22끔은 `area_um2`가 **655,086µm²(=655mm²)**인데도 **통과한다**(파일럿 제약 목록에 area가 없다) — B22가 그 조용한 부조리를 명시적 실패로 바꾼다 |
| **B23** | **★신규(v4.25) — B19'+B22가 성립하려면 B9(vsb 오산출)가 먼저다. 실측으로 확정.** B22를 켜니 파일럿에서 `M66`의 창이 비었다. 진짜 물리적 불가능인지 확인하려고 후보 vds마다 어느 멤버가 막는지 전수로 찍었더니, 막는 것은 **`M38`(ID=23.73µA)이고 그 멤버의 `vsb=0.8625V`** 였다. `M38`은 넷리스트상 **source=gnd**라 vsb가 0이어야 한다 — B9가 이미 지목한 그 4소자(M60/M61/M38/M68) 그대로다(이번 덤프에서 `M68`도 vsb=0.2000으로 확인). 가짜 바디바이어스가 Vth를 올려 **같은 VGS에서 전류밀도를 55배 낮게** 보이게 만들고, 그래서 W가 13,340µm로 튀어 창이 빈다. **물리 vsb=0으로 재면 이 그룹은 성립한다**(`probe_mirror_design_space.py`가 이미 그렇게 쟀다 -- nmos:Vbias4 성립조합 9개). 즉 B19'/B22가 틀린 게 아니라 **입력이 오염돼 있다** | 실측(`tests/probe_b22_headroom_attribution.py` + `.window_dump.txt`) | **없음(순서만 확정)** — 작업 순서는 **B9 -> B19' 배선(스크립트 보존됨) -> 재탐색**이다. B9는 §10.3에서 이미 "★ 수정 승인 대기"였고, 이제 그것이 미러 작업의 **선행 조건**임이 실측으로 확정됐다 |
| **B24** | **★신규(v4.26) — B9를 실제로 고쳐봤다. 계산은 맞는데 그 뒤가 회로 판단이다.** ① **현재 상태를 처음으로 정확히 쟀다**(`tests/probe_node_voltage_audit.py`를 낡은 instance.json 대신 **지금 엔진으로 새로 사이징**해서 재도록 고침 — 그 전엔 세션18 산출물의 옛 필드 `vs`를 읽고 있었다): 51소자 중 **26개 불일치**, 세 부류로 갈린다 — **(가) 소스가 레일인데 vsb≠0 4개**(`M38` +0.8625 / `M60` +0.3750 / `M61` +0.2000 / `M68` +0.2000), **(나) 소스가 비레일인데 vsb=0 15개**(`M40` −0.9375, `M2a`/`M2b` −0.7997, `M37a`/`M37b` −0.7375 …), **(다) 그 외 7개**(`M9a`/`M9b`·`M18a`/`M18b`는 값이 정확히 **서로 바뀜**). 노드는 36개 전부 해소되고 다중도달 불일치는 4건(전부 정확히 +99.7mV). ② **수정 구현**: `reconcile_vsb_from_nodes()` 신설 — 헤드룸이 끝나 vds가 전부 확정된 시점에 `propagate_node_voltages()`+`derive_vsb_from_nodes()`로 vsb를 다시 유도해 덮어쓰고, 소스 전압을 못 구하면 0.0으로 때우지 않고 **명시적 실패**한다. 그리고 `audit_vsb_consistency()`를 파이프라인 **게이트로 배선**했다 — 이 두 함수는 세션46에 만들어졌는데 **엔진 호출부가 하나도 없었다**(★절대원칙 위반 상태였다). ③ **결과**: 올바른 물리가 적용되자 `M11b`(class-AB battery의 적층 PMOS diode, vsb 0.0→0.6750)가 **W=6342µm**를 요구해 파일럿이 성립하지 않는다. 헤드룸 시점에도 노드전압으로 vsb를 구하도록 한 곳 더 고쳐봤으나 M11b의 소스 노드는 그 시점에 아직 복원되지 않아 같은 결과다 | 실측(`tests/probe_node_voltage_audit.py`) | **★ 회로 설계 판단 필요 — 혼자 진행하지 않음.** 남은 것은 "바디효과를 제대로 넣으면 M11b가 지금 예산으로는 성립하지 않는다"이고, 선택은 그 스택의 vds 예산 / `L` / 전류 중 무엇을 바꿀지다(B19'가 `Iref` 대신 공유 VGS였던 것과 같은 성격). 엔진 변경분은 `tests/b9_vsb_from_nodes.patch`(166줄)로 보존했고 저장소는 되돌려 self-test 2개 모두 diff 0줄이다 |
| **B25** | **★신규(v4.27) — A8의 "연립 solver는 필요 없다"는 재해석이 틀렸다. 적층 diode는 vsb로 결합돼 있다.** class-AB 배터리 4스택이 전부 **적층 diode**다(vom/vop × PMOS/NMOS 대칭): `vdd→M11a→M11b→M12→gnd`, `vdd→M13→M14a→M14b→gnd`와 그 vop 쌍(M20a/M20b/M21, M22/M23a/M24b). 적층이라 **아래쪽 diode의 vsb = 위쪽 diode의 vds**이고(M11b.vsb = VDS(M11a) = 0.675V), 그래서 M11a와 M11b는 같은 전류·같은 L·같은 VGS인데 **M11b가 61.3배 넓어야 한다** -- 차이는 오직 바디효과다. v4.13이 A8을 "diode의 Vgs는 종속값이라 연립이 아니라 제약 추가로 처리"로 재해석했는데, **그 재해석은 vsb 결합을 못 봤다**. ② **실측한 선택지**(`tests/probe_stacked_diode_options.py`): **전류는 지렛대가 아니다**(0.235~1.765배 전 구간 실패 -- W가 두 소자 모두 ID에 비례해 61배 비율이 안 변한다, B19'의 `Iref`와 같은 구조). **L은 PMOS만 고친다**(`bias_replica` 0.180µm → M11b 6342→**20.00µm**, 그러나 NMOS는 1882→1687µm로 거의 안 변한다 -- NMOS 배터리는 diode에 0.375V씩만 가고 M13이 1.05V를 가져가 깊은 약반전이라 L이 상쇄된다). ③ **결정적**: `(v_a, v_b)`를 **연립으로** 고르면 PMOS는 L=0.180µm에서 **60조합**, NMOS는 **현재 L 그대로 32조합**이 성립한다(최적 각각 (0.675/0.825/0.300) W 2.32/1.42µm, (0.562/0.675/0.562) W 1.52/1.52µm). 즉 **설계 변경이 더 필요한 게 아니라 배분을 함께 풀기만 하면 된다** | 실측(`probe_stacked_diode_options.py` + 배선 시험) | **★ 승인 필요(공유 엔진)** — `diode_vds_window()`가 diode마다 **독립적으로** 창을 계산하고 그때 vsb를 모른다(실측: 계산된 창의 vsb가 전부 0.0/0.2였고 실제값 0.675/0.375가 아니었다). 그래서 배분기가 고른 `lo`가 결합 제약을 위반한다(M11b W=924µm). 필요한 것은 **같은 스택의 적층 diode를 2변수로 함께 푸는 것**(아래쪽 vsb=위쪽 vds). **✅ 2026-09-09 구현 완료** — `solve_stacked_diode_pair()` 신설(위/아래 vds를 함께 훑고 아래쪽 vsb를 위쪽에서 유도) + 헤드룸 배분기 배선 + B9(vsb 노드전압 유도) 동시 적용 + `L_role: bias_replica`(M11a/M11b/M20a/M20b). **파일럿 평가 성공**: gain_db 65.5547(≥54), area_um2 **847.45**(925.52에서 **감소**), cmrr 66.12(≥60), psrr 81.38(≥60), power 258.82µA. vsb 감사 게이트도 통과. 구현 중 실측으로 바로잡은 것 셋: ① 결합식이 `vsb_lo = v_up`이 아니라 **`vsb_lo = vsb_up + v_up`**(직렬이면 역바이어스가 누적된다 — 위쪽 소스가 레일일 때만 둘이 같아서 배터리 쌍에서는 우연히 맞았다. 검산: M58(vsb 0.2, vds 0.2) 아래 M57은 vsb 0.4) ② 쌍의 합에 **스택 예산 상한**이 필요하다(cmfb_vocdes_gen에서 1.837V>1.8V) ③ 쌍이 스택의 전부면 합이 예산과 **정확히 같아야** 한다(≤로는 0.2625V가 남는다) ④ 위쪽이 **diode가 아닌 경우도** 대상이다(M57←M58, M64←M63 — 위쪽 W는 제약하지 않고 최소 vds만 지킨다) ⑤ 위쪽 소스가 레일이 아니면 그 vsb가 **다른 스택이 정한 노드**에 달렸다(M58의 소스 Vx는 diffpair_branch_a 소관) — 노드전압으로 유도해야 한다. **잔여**: self-test L5c 픽스처의 고정점(거의 모든 theta를 중점에 고정한 인위적 단일 점)만 막힌다 — 그 점의 M39/M40 전류에서는 최소합 1.837V로 몫 1.8V를 넘는다. 파일럿(자유 탐색)은 통과하므로 설계 문제가 아니라 **픽스처 문제**다. **2026-09-09 추가조사("2번 봐")**: L5c만 막히는 원인은 **그 점의 M39/M40 전류가 파일럿의 17배**라는 것이다(8.197µA vs 0.47µA -- 픽스처가 `r_cmfb_vocdes`를 bounds 중점 0.11에 고정하기 때문). **M39/M40의 `L_role` 변경은 해법이 아님이 실측으로 확인됐다** -- 두 동작점을 동시에 만족하는 L이 없다: `mirror`(0.375µm)면 파일럿 OK / L5c 실패(최소합 1.837>1.8), `bias_replica`(0.180µm)면 L5c OK(정확 1.8V 쌍 8개) / **파일럿 실패**(성립 합 1.05~1.24 < 1.8). 즉 문제는 L이 아니라 **픽스처의 고정 전류**다. 부수 개선: 정확 일치를 격자점 쌍에서만 찾던 것을 **`v_lo = 예산 - v_up`으로 연속 평가**하도록 보완(LUT는 VDS를 연속 보간하므로 격자 양자화는 물리가 아니다). 변경분은 `tests/b25_b9_stacked_diode.patch`(388줄)로 보존 |
### 10.4 미해결 — 일반성 (검토자 D)

**판정**: 이 방법론은 "임의 토폴로지"가 아니라 **"차동 입력 + 캐스코드/미러 부하 + 2단 Miller
보상 전압증폭기"** 한 부류에 맞춰져 있고, 그마저도 파일럿 1개를 정본으로 일반화한 것이다.
D2(gain metric 위임)로 가장 큰 차단 요인은 풀렸으나 아래가 남는다.

| # | 반례 | 어디서 막히나 | 처리 방향 |
|---|---|---|---|
| G1 | **단일단(5T/텔레스코픽)** | `compensation: null`(folded_cascode가 실제로 그렇다)이면 `gm_i`의 출처가 사라져 §7.9 인과사슬이 끊긴다 | `compensation: null`을 1급 케이스로 명시하고 그때 gm의 출처(GBW×CL 또는 gain 제약)를 §7.9에 정의 |
| G2 | **3단 이상 중첩보상(NMCNR — 저장소에 있음)** | `solves_for:["Cc","Rz"]`·`stage_gm_ref` 2개가 2단 하드코딩. `Rz=1/gm2`가 **범용 DOF 계수기 본문**에 상수로 박혀 있다. NMCNR의 자유도 `kg=gm2/gm3`를 선언할 자리가 없다 | `compensation`을 stage 수 종속으로 일반화, 종속관계를 `topology_fn` 메타데이터로 이동 |
| G3 | **Gain-boosted cascode** | §7.9의 "④ VDS 예산만이 유일한 설계 자유도"라는 출발 명제를 직접 반증한다(⑤ 캐스코드 부스트를 설계 변수로 만드는 기법) | `stages[].boost_amp` 재귀 또는 명시적 범위 밖 선언 |
| G4 | **class-AB 정지전류** | `ID_source ∈ {kcl, ideal_source_ref}`뿐인데 Monticelli 정지전류는 **VGS 합(KVL)**이 정한다. `ID_final = max(KCL, SR×CL)`은 class-A 규칙이라 class-AB 정지점을 파괴한다 | `ID_source.type`에 `kvl_battery_loop` 추가, `driving_spec.output_class ∈ {A, AB}` 신설 |
| G5 | **폴딩 노드** | `folded_cascode`의 gain metric은 역할을 **5종**(`gm1_device`/`fold_leg_a`/`fold_leg_b`/`cascode_p`/`cascode_n`/`mirror_n`)으로 요구하는데 서브롤은 4종이다. `fold_leg_b`가 어디에도 안 들어간다 | 서브롤 확장(+`follower`/`common_gate`/`floating_current_source`/`voltage_divider`) |
| G6 | **stage 분할 규칙이 없다** | 문서 어디에도 stage 경계 정의가 없다. §8.3은 `stages[]`가 이미 있다고 가정하고, §13.3의 5신호(원래 "미러 다리 matching vs gain-load" 판정용)를 input/cascode 분류기로 전용해 **신호2가 입력 차동쌍에 먼저 걸린다**(입력쌍이 cascode로 분류됨). `input↔load` 구분·`tail` 판정 규칙도 없다 | "stage 분할은 사람이 확정하는 입력"임을 명시하거나 진짜 판정 규칙을 세울 것. §8.3의 5신호 전용은 **철회** 권장 |
| G7 | **비증폭 회로**(밴드갭·constant-gm bias·비교기·SC) | §2.2가 회로 부류를 하나도 배제하지 않아 암묵적 보편성을 주장한다 | §2.2에 "Out of Scope — 회로 부류" 절 신설. 이들은 배제하는 편이 옳다 |
| G8 | **새 토폴로지 추가 비용이 문서화돼 있지 않다** | §8.3은 "JSON 두 개 쓰면 끝"처럼 읽히나 실제로는 gain metric·CMRR/PSRR estimator·`topology_fn`을 각 레지스트리에 등록하는 **엔진 작업 3~4곳**이 필요하다 | §8.3에 그 목록을 명시 |

### 10.5 정합성 잔여 (검토자 C)

v4.0에서 §1.5 참조 4곳·`schema_version`·"무변경 재사용" 2곳·§8.8 기준선 서술을 고쳤다.
남은 것: 유령 함수 3개(`allocate_headroom_budget()`/`measure_stage_gain_ceiling()`/
`redistribute_headroom_by_gain_gradient()` — §6.1에 1회씩만 등장, 본문에 정의 없음, §7.9는
같은 기능을 다른 이름으로 서술), 삭제 선언한 `gain_allocation`/`gain_allocation_check`의 잔존
(L794/L1150), §2.2 vs §4.1 C7의 범위 충돌(파일럿 1개 vs 4개 전수), §7.9 3-Phase 순서와 §8.4
harness 순서의 불일치(§8.4에 Phase 1이 없고 되먹임을 금지), 신규 함수 목록 3중 관리
(§2.1/§6.1/각 §7 절 말미), `closed_loop_accuracy_db`·`stage_gm_ref`·`vdd_kvl` 미소비 필드,
`slew_rate_v_per_us` vs `slew_rate_target`·`battery_centering_deviation` vs
`classab_centering_dev_v` 명칭 흔들림, §7.10 측정2 표의 빈 헤더.


### 10.6 spec 정본화 — 2026-09-10 사고와 재발 방지 (★ 신설 v4.34)

#### 무슨 일이 있었나

조사 스크립트들이 spec 딕셔너리를 **손으로 복붙**해 썼는데, 그것이 정본
(`workspaces/run_harness.py`의 `SPECS[*]["spec_fn"]()`)과 갈려 있었다:

| 항목 | 정본 | 복제본 |
|------|------|--------|
| `L_candidates` | `layout_grid_L_candidates(n=41)` 41점 | LUT 앵커 12점 |
| `VDS_candidates` | `dense_candidates(n=13)` 13점 | 손으로 적은 9점 |
| `gm_id_grid` | 2.0~30.0 / 0.5 간격 **57점** | 4~24 / 1.0 간격 **21점** |
| `stage_power_tolerance` | 0.05 | **없음** |

정본 주석에는 이미 세션30 실측으로 **"L을 촘촘히 하면 gm_id도 촘촘해야 한다"**가 적혀
있었다(성긴 gm_id 격자가 임의 L에서 feasible W를 못 찾아 크래시). 복제본은 **둘 다 성긴**
조합이라 우연히 안 터졌을 뿐이다. 결과적으로 v4.28~v4.33의 파일럿 수치가 전부 비정본
기준이었고, 4개 회로 조사를 돌려서야 드러났다.

#### 정본으로 돌리면 파일럿이 수렴하지 않는다 (★ 새 blocker)

정본 spec으로 SLSQP 3 start × 25 iter를 돌린 결과(625초): **3회 전부 실현가능한 해를
못 찾았다**. 사유는 매번 같다 —

    'biasgen_vom_floatsrc_sink' 그룹(예산 -0.02396V, 미해결 ['M9b'])
    스택 예산이 음수다: 고정분 합이 0V인데 초과 0.02396V. diode 구간 하한 없음.

즉 v4.28~v4.33에서 보고한 수치(gain 65.55 / area 584.59µm² / `PM_parasitic` -8.9° 등)는
**전부 비정본 해상도에서 잰 값**이며, 정본에서는 그 동작점에 도달하지 못한다. 이 스택
예산 음수는 별도 blocker로 다뤄야 한다(§10.2/§10.3 대기열).

#### 재발 방지 — 무엇을 만들고 어디에 배선했나

| 장치 | 위치 | 하는 일 |
|------|------|---------|
| `require_declared_spec_source()` | `sizing_recipe.py` | `library/*.topology.json`을 **해상도 필드나 LUT가 실린 spec**으로 사이징하는데 `_spec_source`가 없으면 `ValueError`. `_build_theta_evaluator()` 첫 줄에 배선 → `optimize_full_circuit_budget()`도 자동 적용 |
| `spec_fingerprint()` | `sizing_recipe.py` | 해상도 결정 7개 필드의 개수·범위를 짧은 지문으로. 거부 메시지에 찍혀 "무엇이 갈렸는지"가 바로 보인다 |
| `canonical_spec(key)` | `run_harness.py` | 정본을 쓰는 길을 **복붙보다 짧게** 만든다 |
| `derived_spec(key, why, **overrides)` | `run_harness.py` | 정본에서 **명시한 항목만** 갈린다. `why`가 비면 거부. `_spec_source`에 `[gm_id_grid:n57->n21] -- <이유>` 형태로 자동 기록 |
| 자기시험 4건 | `sizing_recipe.py` self-test | 게이트가 실제로 무는지 상시 검증(아래 참고) |

**배선 결과**: 복붙 spec 블록 **238줄을 16개 조사 스크립트에서 제거**하고 전부
`H.canonical_spec("current_reuse_telescopic_ota")`로 교체했다. 복제본은 정본의 **부분집합**
(24키 ⊂ 26키)이라 잃은 항목은 없고 `stage_power_tolerance`가 회복됐다. 같은 블록이 16개
파일에 그대로 퍼져 있었으므로 파일마다 다른 판단을 한 것이 아니라 **복제본 하나가 번진
것**이었다 — 그래서 일괄 교체가 각 스크립트의 의도를 훼손하지 않는다.

#### ★ 게이트를 만들자마자 그 게이트가 죽어 있었다

처음 구현한 `require_declared_spec_source()`는 **한 번도 거부하지 않았다**. 원인:

```python
try:
    real = os.path.realpath(topology_path)   # 이 모듈은 os를 최상위 import하지 않는다
except Exception:
    return                                    # NameError를 삼키고 항상 통과
```

재발 방지 장치가 재발 방지 없이 죽은 셈이다. 조치는 두 가지다:

1. **광범위 `except`를 제거**했다(모듈 관례대로 `import os as _rds_os`를 함수 안에서).
   메모리 원칙 "우회/skip 로직은 타당성 검토 후에만"의 실례가 하나 더 생겼다 — 이번엔
   `skip`이 아니라 **예외를 삼키는 것**이 같은 역할을 했다.
2. **자기시험에 게이트 자체를 넣었다**. `sizing_recipe.py` self-test가 ① 출처 없는 spec
   거부 ② 출처 선언 시 통과 ③ 빈 spec(gap 진단 전용) 통과 ④ library 밖 fixture 비대상
   을 매번 확인한다. 게이트가 다시 조용히 죽으면 기준선 diff가 깨진다.

**검증**: `sizing_recipe` exit 0 / 기준선 diff **0줄**(기준선에 13줄 추가 반영),
`stick_diagram` exit 0 / diff **0줄**, 조사 스크립트 16개 배선 smoke 전부 통과.

### 10.7 class-AB 배터리 헤드룸 + 기준점 복구 (★ 신설 v4.35)

#### A. M9b 스택 예산 음수 -- 배터리 KVL을 아무도 안 보고 있었다

정본 spec(§10.6)으로 돌리자 `'biasgen_vom_floatsrc_sink' 그룹(예산 -0.0239609V)`으로 즉시
멈췄다. 세션22 J-2가 이미 확인해둔 순수 connectivity 사실이 열쇠였다 -- `M9a`(PMOS,
source=Vg15, drain=Vop1)와 `M9b`(NMOS, drain=Vg15, source=Vop1)는 **직렬이 아니라 같은 두
노드를 잇는 상보 병렬쌍**(Monticelli floating current source)이다. 실제 컬럼은

    vdd -> M8 -> Vg15 -> (M9a || M9b) -> Vop1 -> M10 -> gnd

이고 `load_topology()`가 connectivity에서 `VDS(M8)=VGS(M15)`, `VDS(M10)=VGS(M16)`을 자동
유도하므로(M8.drain=Vg15=M15.gate, M10.drain=Vop1=M16.gate)

    V_bat = vdd - VGS(M15) - VGS(M16)

이다. 그런데 선언된 `classab_centering_dev_v`(=|VGS(M16)-VGS(M15)| <= 0.15V)는 **차이**만
잰다 -- **합을 보는 것이 아무것도 없었다**. 완벽히 센터링해도 `V_bat = vdd - 2*VGS`라 VGS가
크면 음수가 된다. 실측(정본, theta 중점): `0.9799 + 0.8441 = 1.824 > vdd` ⟹ **V_bat =
-0.024V**인데 centering(0.136 <= 0.15)은 **통과한 채**였다. 즉 그동안의 파일럿 수치는
배터리 전압이 음수인, 물리적으로 불가능한 동작점의 값이었다.

`tests/probe_classab_battery_headroom.py` 실측: `V_bat >= VDsat` 영역은 **44/100칸**으로 넓게
있고 L=0.575um에서도 gm_id>=19면 성립한다. 실패한 M15는 gm_id=16.5 -- **설계 불가능이 아니라
탐색이 그 영역을 피할 이유가 없었던 것**이다.

**해결(사용자 선택 2건)**

① **gm_id 탐색에 KVL을 먹인다.** `search_gm_id_for_role(..., vgs_max=...)`는 기계적 필터일
뿐이고(W_bounds 필터와 같은 성격, 회로를 모른다), 상한은 `stack_kvl_vgs_limit()`이 **선언만
읽어** 유도한다: `VGS(name)`을 VDS로 쓰는 소자 Y마다 Y가 속한 그룹의 예산식
`vdd - sum(vds(refs)) = sum(vds(members))`를 `VGS(name)`에 대해 정리하고, 각 항을
(a) `VGS(name)` 종속 -> **계수 k에 더함** (b) 확정된 vds -> 상수로 뺌 (c) 미확정 -> 최소
필요분을 뺌으로 분류한다. 계수를 세는 덕에 **"M15와 M16이 같다"를 함수가 알 필요가 없다** --
`gm_id_match_vgs_of` 선언이 이미 그 사실을 담고 있다. 이 회로에서는 k=2가 되어
`VGS(M15) <= (vdd - VDsat(M9a))/2 = 0.8417V`(손계산과 일치).

② **포화 하한은 LUT에서.** `lut_vdsat_headroom()`이 references/gm-id-methodology.md §2.7의
`VDsat ~ 2/(gm/ID)`를 쓴다 -- 이 저장소가 이미 `_default_cascode_headroom()`(Jespers
`2/gm_id + margin`)으로 캐스코드에 쓰는 **바로 그 식**이라 새 상수·새 근사가 없다. gm_id를
모르는 시점이라 **실현 가능한 최대 gm_id**로 가장 느슨한 하한(=필요조건)을 만든다.
`floating_current_source` role만 `min_vds_by_role` 폴백 상수(0.2V) 대신 이 값을 쓴다 -- 이
role의 소자는 "남는 예산을 받는 멤버"가 아니라 **그 예산 자체가 설계량**(배터리 전압)이기
때문이다. ★ 헤드룸 배분기와 gm_id 탐색이 **같은 헬퍼**를 쓰므로 둘이 어긋날 수 없다.

#### B. 기준점이 중점에 묶여 탐색이 출발을 못 하고 있었다

사용자 지적: *"중점에 묶이는 것도 해결했잖아. 왜 반영이 안 되어 있어?"* -- 맞다.
v4.30이 이미 실측으로 **`r_cmfb_vocdes`의 실제 설계값은 중점(0.11)이 아니라 하한(0.02)**임을
확정했는데(중점은 M39/M40에 17배 전류를 흘려 1.8V를 못 나눈다, B25), 그 결론이 **self-test
픽스처에만 적히고 엔진 경로에는 반영되지 않았다**.

그 결과가 컸다. `presolve_warm_start()`의 세 단계 -- 선형 feasibility 투표, `search_stage_
budget_L_warm_start()`의 L 스캔, `derive_theta_dependency_graph()`의 분류 -- 가 **전부
"기준점이 평가 가능하다"를 전제**한다. 기준점이 크래시하면:

  * L 스캔은 21점이 전부 죽어 조용히 **bounds-midpoint로 후퇴**하고(실측 반환값이 정확히
    0.5750um -- 이 함수는 배선돼 있고 6.1초 동안 실제로 돈다. 앞선 보고에서 "미배선"이라 한
    것은 필자의 grep 오류였다),
  * 의존성 그래프는 전 theta를 `ambiguous`로 분류하며(notes에 "baseline_theta_values 자체가
    infeasible"이 전 theta에 걸쳐 남는다),
  * SLSQP는 그 midpoint에서 출발해 한 발도 못 움직인다(3 start x 25 iter, 625초, 전부 실패).

**해결: `repair_infeasible_baseline()`** -- 기준점이 infeasible이면 **실패 증거를 따라**
자유 theta를 bounds로 옮겨 복구한다. 사용자 지시("이 설계에만 적용되는 것은 안 돼. 반드시
일반화된 솔루션을 코드화해야 해")대로 **회로 이름·소자 이름·theta 이름·상수가 하나도 없다.**
읽는 것은 넷뿐이다:

  1. 선언(`thetas`의 feeds -- `_theta_device_map()`이 임의 깊이의 문자열/리스트를 훑는다)
  2. 넷리스트 소자 이름(`ev["by_name"]`)
  3. **엔진 자신의 실패 메시지가 지목한 소자**(이 저장소의 오래된 규약: 실패 메시지는 항상
     막힌 소자/그룹을 적는다)
  4. 각 theta 자신의 `bounds`

매 라운드 (1)기준점 평가 -> (2)메시지에서 실제 소자 이름 추출 -> (3)그 소자를 담당하는 자유
theta를 교집합 크기 순으로 -> (4)그 theta를 **자기 bounds 양 끝**에 놓아 보고 **평가가
통과하거나 막히는 소자가 바뀌면** 채택. "병목이 바뀌면 진전"이라는 판정이 핵심이다 --
병목이 연쇄일 때 한 번에 feasible이 되기를 기다리면 아무것도 못 고친다.

증거가 어떤 theta도 못 짚으면 **이미 평가에 성공한 것이 측정된 점**(`fallback_point`)으로
하나씩 물러난다 -- 값을 지어내는 게 아니라 측정된 실현가능점 쪽으로 후퇴하는 것이다.
그것도 없으면 **복구를 포기하고 원래 기준점을 그대로** 돌려준다(없는 근거로 값을 옮기지
않는다).

**파일럿에서 실제로 일어난 일**(전부 유도된 것이고 코드에 박힌 값이 아니다):

    L_stage2out_p 0.575um -> 0.15um(하한)   막힌 소자 [M15] -> [M39, M40]로 병목 이동
    r_cmfb_vocdes 0.11    -> 0.02 (하한)    [M39, M40]에서 평가 성공
    r_diode_M11a  0.02    -> 0.085          (측정된 실현가능점으로 되돌림) 평가 성공

두 번째 줄이 바로 v4.30이 손으로 확정했던 그 값이다 -- 이제 **엔진이 스스로 유도한다.**

**일반성 검증(4개 회로 전수)**

| 회로 | 결과 |
|------|------|
| `folded_cascode` | 기준점이 이미 실현가능 -> 복구 **0건, 무동작** |
| `current_reuse_telescopic_ota` | 복구 3건 -> x0 `feasible=True` |
| `two_stage_ota` | 세션41이 이미 이월한 `stage1_out` KVL 항목에 걸림(이 변경과 무관) |
| `nmcnr_amplifier` | 복구 대상 없음(무동작) |

self-test 둘 다 **exit 0 / diff 0줄** -- 복구 장치는 필요 없는 회로의 동작을 전혀 바꾸지 않는다.

#### C. 결과 -- 정본 spec으로 파일럿이 처음 수렴했다

    SLSQP 3 start x 25 iter, 145초 (직전: 625초 동안 3 start 전부 실패)

| metric | 값 | 제약 | |
|--------|-----|------|---|
| `gain_full_circuit_db` | 65.97 | >=54 | OK |
| `cmrr_estimate_db` | 60.42 | >=60 | OK |
| `psrr_estimate_db` | 81.97 | >=60 | OK |
| `mismatch_sigma_mV` | 1.36 | <=5 | OK |
| `classab_centering_dev_v` | 0.1481 | <=0.15 | OK |
| **V_bat (vom/vop)** | **+0.380 V** | (고치기 전 -0.024) | |
| `parasitic_pm_deg`(§7.11) | **+33.88°** | (고치기 전 -8.9) | |
| `power_uA` / `area_um2` | 267.59 / 693.88 | | |

`theta_star`가 복구 장치의 유도와 일치한다: `r_cmfb_vocdes=0.02`(하한),
`L_stage2out_p=0.15um`. §7.11의 `parasitic_pm_deg`가 음수에서 +33.9도로 뒤집힌 것도
같은 원인이다 -- 배터리가 음수 전압일 때의 출력단 게이트 pole이었다.

#### D. 함께 고친 것

* **M18b 선언 누락(사용자 승인)** -- 넷리스트는 vom/vop가 완전 대칭인데 `M9b`만
  `budget_reference_device="M8"`을 갖고 `M18b`는 짝(`="M17"`)이 없었다(세션39가 vom 쪽만
  정정하고 빠뜨림). 선언이 없는 동안 `biasgen_vop_floatsrc_sink`가 vdd~gnd 전체 컬럼으로
  취급돼 M17의 몫이 0이 되는 모순이 있었다.
* **`_grid_points_in_range(n=1)`의 ZeroDivisionError** -- 자유 `metric_stage_budget`(L)
  theta가 없는 동안 실행될 일이 없던 잠복 버그. 구간 중앙에 가장 가까운 격자점을 준다.
* **self-test L5c** -- 이 픽스처가 쓰던 중점이 바로 `V_bat<0`인 그 점이라 도달 불가능해졌다.
  새 `stop_after_sizing=True`로 **사이징까지만** 보게 했다(사용자 선택): 이 픽스처가 검증하는
  헤드룸 singleton KVL은 전부 사이징 단계에서 끝나는데, 레이아웃 핑거 배정(별개 한계)
  때문에 전기 검증 자체를 못 하고 있었다(L_cascode 후보 6개 + theta 자유화 2조합을 전수
  시험해도 같은 지점이거나 다른 스택으로 옮겨갈 뿐). 고정점도 실측으로 골랐고
  (L_stage2out=0.2um), 픽스처 머리말이 원래 말하던 대로 `L_cascode`를 자유로 되돌렸다
  (코드가 주석과 어긋나 전부 고정하고 있었다). 기준선 diff **1줄**: `gain_db 76.35->61.30,
  cmrr 76.12->60.04` -- **옛 수치가 물리적으로 불가능한 점의 값이었다.**

### 10.8 §7.11 L2 완성 — 보상망을 실제로 세고, Cc를 유도한다 (★ 신설 v4.36)

#### A. L1은 보상망을 못 보고 있었다 (사용자 지적)

> "pm보상 회로가 있는데 왜 그건 고려하지 않지?"

`node_pole_estimate()`(L1)는 **소자 단자만** 셌다. 그런데 이 회로의 보상망은
`passive_elements`에 **이미 선언돼 있었고**(Cc1: Vom-N_cc_rz1, Rz1: N_cc_rz1-Vop1, 대칭쌍),
엔진의 MNA는 그 저항을 이미 쓰고 있었다(`_full_circuit_devices()` + `_resolve_nulling_
resistor_ohm()`으로 `Rz = 1/gm(M16)` 동적 계산). **`node_pole_estimate()`만 그 인자를 안
받았다.** 하필 L1이 "위상을 먹는다"고 지목한 노드(`Vop1`/`Vom1`)가 정확히 Rz가 붙는
노드였다 -- 보상이 붙는 자리를 보상 없이 잰 셈이라 그 값(34.2도)은 무효다.

#### B. L2 — pole을 뽑지 않고 주파수응답을 직접 푼다

§7.11은 L2를 "MNA에서 실제 pole 추출(고유값)"으로 적어뒀는데, 구현하며 **그대로는 틀린다**는
것이 드러났다: `det(G+sC)=0`의 근에는 bias 노드 모드까지 들어오는데 그 모드들은 excite→sense
전달함수에서 zero와 상쇄돼 위상을 안 먹는다. 그걸 다 더하면 L1에서 전 노드를 더했을 때
-1004도가 나온 것과 **같은 종류의 오류**가 pole 형태로 재발한다.

그래서 `(G + j*w*C) v = b`를 실제로 풀어 위상을 직접 본다:

    PM = 180 - (DC -> w_c 사이에 누적된 위상 지연)

단일 지배 pole이면 지연 90도로 수렴해 **PM=90도** -- L1 식의 기준선 `90`이 그 몫이었으므로
**L1을 특수케이스로 포함**하고, 원문 `PM = atan(w_p2/w_c)`도 pole 하나짜리 특수케이스로
재현한다. 부수적으로 **지배 pole을 따로 빼는 처리(사용자 확인 3번)도, 신호경로 제한도
필요 없어진다** -- 둘 다 응답에 이미 들어 있다.

신설: `full_circuit_response_at_omega()`, `_mna_stamp_capacitance()`,
`_resolve_capacitor_farad()`.

#### C. 논문으로 검증 — `omega_c`에 대한 필자의 해석이 틀렸다

사용자 지시로 원문 PDF를 확인한 결과 **필자의 앞선 주장("선언된 omega_c는 실제 크로스오버가
아니다")이 틀렸다**. 원문 Eq.(2) 아래: `omega_c`는 **loop gain unity gain bandwidth**다
(개루프 A의 unity gain이 아니다). Eq.(4) `beta = Cf/(Cf+Cs+Cgg1)`이므로 `|beta*A|=1`인
지점에서 `|A| = 1/beta`다.

    실측: w_c(30.50MHz)에서 |A| = 6.52dB,  1/beta 기대값 = 6.38dB(beta 0.4514)

거의 정확히 일치한다 -- 선언이 맞고 필자가 개루프 unity gain(66MHz)을 본 것이 틀렸다.
그리고 beta가 주파수 무관한 용량분배라 `∠(beta*A) = ∠A`이므로, A의 위상을 w_c에서 재는
지금 구현이 PM 정의와 정확히 맞는다.

#### D. 빠져 있던 connectivity (사용자 확정)

원문 Table I `C1, C2, C_L = 500fF, 500fF, 1pF`, Eq.(6) `omega_p2 ~ gm2/(C_Ltot*Cgg2/Cc +
Cgg2 + C_Ltot)`가 **비지배 pole을 C_Ltot으로** 정하는데 `passive_elements`에 부하/피드백
용량이 없었다. 사용자 확정으로 추가:

| 소자 | 연결 | 값 |
|------|------|-----|
| CL1 / CL2 | Vop-gnd / Vom-gnd | `C_Ltot` |
| Cf1 / Cf2 | **Vom-Vip / Vop-Vim (교차)** | `Cf` |
| Cs1 / Cs2 | Vip-gnd / Vim-gnd | `Cs` |

**교차인 이유**: `Vip -> M1a -> Vom1 -> M26(공통소스) -> Vop`로 반전이 두 번이라 Vip와 Vop가
**동상**이다(실측 DC 위상 -5.15도). `Vop->Vip`로 되먹이면 정궤환이다. 수치로도 확인됐다 --
교차면 w_c에서 `|A|=6.80dB`로 `1/beta`에 가깝고 비교차면 5.90dB로 멀어진다. (개루프 AC에서는
어느 쪽이든 출력을 Cf만큼 부하할 뿐이라 결과는 같지만, 기록은 물리대로 둔다. `Cs`는
양단이 다 구동 노드라 기여 0 -- 실측 확인.)

측정 변화: `PM = 93.76도(부하 없음) -> 81.13도(+C_L) -> 75.35도(+Cf)`.

#### E. Cc를 보상망이 유도한다 (사용자 지시)

> "Cc와 Rz는 보상망이 계산해서 확정해야지."

`Rz`는 이미 유도되고 있었다(`nulling_reference_device`로 `1/gm(M16)`). **`Cc`만 spec 상수
(500fF)** 였다 -- 원문이 "By setting Cc to 500fF"로 사람이 고른 값을 그대로 복사한 것이다.

그런데 그 값은 **원문 자신의 식에서 유도된다**. Cc를 키우면 Eq.3의 `gm1 = w_c*Cc/beta`는
선형으로 늘고 Eq.6의 `gm2`는 Miller 항 `C_Ltot*Cgg2/Cc`가 작아져 준다. 선언된 목적이 전력
최소화(`sum(gm_i/gm_id_i)`)이므로 두 단의 gm/ID가 같다는 1차 가정에서 `d(gm1+gm2)/dCc = 0`:

    Cc = sqrt( beta * tan(PM_target) * C_Ltot * Cgg2 )

**새 상수가 하나도 없다** -- beta는 Cf/Cs/Cgg1(실측), tan(PM_target)/C_Ltot은 선언, Cgg2는
`prev_cggs`로 들어오는 실측값이다. `miller_ota_topology()`가 `Cm`을 실측 용량에서 계산하는
것(그쪽도 pole-splitting 최적점)과 정확히 같은 성격이고, 그 함수가 이미 선례였다.

실측: `Cc = 374~385fF`(원문의 500fF는 **그들의** Cgg2에 대한 값). `compensation.parameters`
에서 `Cc`를 빼고 `exposed_params`로 노출한다.

배선하며 드러난 것 둘:
* `_feed_gm_target_convention()`의 `cap_key`만 `ctx.spec`을 직접 읽고 있었다(바로 윗줄
  `omega_key`는 derived 우선). Cc를 유도로 바꾸자 `KeyError: 'Cc'`로 드러났다 -- 그 전에는
  두 값이 우연히 같아 안 보였다.
* `exposed_params`는 팩토리 직후에만 읽혔는데, Cc는 `prev_cggs`에 의존해 **호출 중에**
  정해진다. 호출 후에도 받아오고 `_comp_cache`에 함께 저장하도록 고쳤다.

#### F. 제약 판정의 수치 공차

SLSQP가 활성제약에 수렴하자 `cmrr = 59.999999999118884`(잔차 **-8.8e-10**)로 5 start가 전부
버려졌다. `_CONSTRAINT_OPS`에 **상대오차 1e-9** 공차를 준다(단일 지점). 설계 여유가 아니라
float64 반올림이다 -- SLSQP의 유한차분 eps 자체가 2e-3라 경계는 그 이하로 분해되지도 않는다.

⚠️ 처음엔 `max(1.0, |target|)`으로 절대 하한을 뒀다가 **self-test가 잡았다**: 면적 제약
(`pair_area <= 9.1e-12` m^2)에서 그 하한이 값보다 100배 큰 공차가 되어 2배 초과 위반까지
통과시켰다(L4b 픽스처). 순수 상대오차로 고쳤다 -- 스케일 무관하게 항상 "값의 1e-9"다.

#### G. 결과 — `parasitic_pm_deg`를 제약으로 걸고 재탐색 성공

`parasitic_pm_deg >= PM_target_deg`를 **`value_from_spec`으로** 선언했다(숫자 복제 금지,
§10.6 사고와 같은 형태 방지). 신설 `value_from_spec`은 constraint와 passive 양쪽에 쓰인다.

| metric | 값 | 제약 | |
|--------|-----|------|---|
| `parasitic_pm_deg` | **71.87** | >=70 | OK |
| `gain_db` / `gain_full_circuit_db` | 63.55 / 66.05 | >=54 | OK |
| `cmrr_estimate_db` / `psrr_estimate_db` | 60.50 / 81.65 | >=60 | OK |
| `mismatch_sigma_mV` | **0.753** | <=5 | OK |
| `classab_centering_dev_v` | 0.1471 | <=0.15 | OK |
| `power_uA` | **233.73** | (v4.35에서 267.59) | -12.6% |
| V_bat (vom/vop) | +0.2971 V | | |

self-test 둘 다 exit 0 / diff **0줄**(L5c 기준선 3줄은 유도된 Cc 반영으로 갱신).
L5c 픽스처는 `parasitic_pm_deg`를 제외한다 -- 그 제약은 **L 상한**이라 L 자유도가 있어야
만족할 수 있는데 이 픽스처는 거의 모든 theta를 고정한 한 점이다(51.06도). 실제 자유탐색은
71.87도로 만족하므로 제약이 과한 게 아니라 이 픽스처가 검증할 자리가 아니다 --
`classab_centering_dev_v`/`gain_db`를 뺀 것과 같은 판단이다.

### 10.9 미러 공통 L -- 3층 구조 (★ 신설 v4.37, 층1/2/0 착지 · 층3 미완)

사용자 확정 원칙: *"gain stage의 tail이 L의 주인이고, 특히 최초 input 단의 tail이 실제
주인이야. 다른 gain stage의 tail도 함께 묶여 있으면 두 stage의 gain을 모두 만족시키는 L을
sweep해야 해. 이게 결정되면 나머지 mirror구조로 연결된 소자들은 전부 L을 공유해야 하잖아."*

물리 근거: `ID2/ID1 = (W2/L2)/(W1/L1)`가 **순수 W 비**(레이아웃 비, PVT에 강함)로 축약되려면
`L1 == L2`여야 한다. 다르면 이동도/Vth/채널길이변조의 L 의존성을 타고 공정·전압·온도에
흔들린다.

#### 층1 -- 무엇이 같은 L을 써야 하는가 (`l_sharing_classes()`)

세 edge를 union-find로 묶는다. 전부 **이미 있는 선언·연결**이다:

| edge | 출처 |
|------|------|
| 진짜 전류미러 = 같은 `(kind, gate net, source net)` | **순수 connectivity**(`true_current_mirror_groups()`) |
| `device_roles[X].same_as_device` | 기존 선언 |
| `symmetry.matching_pairs` | 이미 L 불일치를 하드에러로 강제 중 -- 재사용 |

⚠️ `gm_id_match_vgs_of`는 edge로 **안 쓴다**. 그 필드는 진짜 미러와 cross-kind VGS 매칭
둘 다에 쓰이는데 후자는 L을 공유하면 안 된다(세션30 M15-M16 결정). connectivity 판정이
그 둘을 정확히 갈라준다 -- 실측으로 M15/M25와 M16/M26이 **별도 류**로 나온다.

실측(파일럿): 동치류 15개. 큰 둘이 `M68류`(8소자, M5·M38 포함), `M8류`(11소자, M6·M7·M36a
포함) -- 사용자와 추적했던 사슬 그대로다(`M7 --same_as-- M6`이 Vcmfb 그룹과 Vbias1 그룹을 잇는다).

#### 층2 -- 누가 정하는가 (`gain_stage_tails()` / `l_class_owners()`)

전부 선언·연결에서 유도한다(회로 이름 없음):

    tail          device_roles[X].headroom_role == "tail"
    gain stage    gain metric의 stages(gain_stages_sum)
    stage의 tail  그 stage 소자들의 **source net을 drain으로 갖는** tail   <- 연결
    최초 input단  gain metric의 excite net을 **gate로 갖는** 소자가 속한 stage

"stage의 tail"을 연결로 찾는 이유: `stages`에는 증폭 소자만 있고 tail은 없다(파일럿 stage1 =
M1a/M4a/M2a/M3a인데 tail M5는 목록에 없다).

실측: **M68류 주인 = M5**, **M8류 주인 = M6**(공동 sweep 후보 M6/M7). 사용자가 말한
"M5가 주인이야"가 그대로 나온다. 다른 3개 회로는 `gain_stages_sum` 선언이 없어 tail을 못 찾고
**전부 `L_role` 폴백 = 동작 무변경**이다.

주인의 L은 §7.10대로 **knee에서 출발**한다(역할 휴리스틱이 아니라). 그 값이 류 전체로 전파되며,
권위 있는 출처(theta/compensation)는 덮지 않는다(`matching_pairs` 전파와 같은 우선순위 규약).

#### knee -- 상수 제거 (`measure_L_knee()` / `knee_L_for_kind()`)

§7.10이 이름까지 명세해 둔 함수를 구현했다. 한계효율 `Δ(gm/gds)/Δ(W·L)`의 최대 구간 상단이
knee이고, `W·L ∝ ID·L²/IDu`라 **ID는 argmax에 영향이 없어** 인자로 받지 않는다. 단조성을
가정하지 않고 격자를 전수 훑으며 `Δ(W·L) <= 0` 구간(§7.10이 찾은 pmos 반례)은 건너뛴다.

**민감도 실측**(단위 x L_min):

| kind | vds 0.3 | 0.6 | 0.9 | 1.2 | gm_id별 범위 | 중앙값 |
|------|---------|-----|-----|-----|--------------|--------|
| nmos | 1.63 | 1.63 | 1.63 | 1.63 | 1.63 ~ 17.67 | **1.63** |
| pmos | 2.27 | 2.27 | 2.27 | 2.27 | 1.63 ~ 10.63 | **2.27** |

* **vds에는 사실상 무관** -- 네 vds에서 중앙값이 완전히 같다. L은 vds가 정해지기 전에
  배정되므로 이 성질이 결정적이다(대표 vds 하나로 찍어도 안전).
* **gm_id에는 민감** -- 약반전 끝에서 튄다. 그래서 격자 전체의 **중앙값**을 쓴다(꼬리가
  한쪽으로 길어 평균이 아니라 중앙값).
* **kind마다 다르다**(1.63 vs 2.27) -- 단일 상수 `mirror: 2.5`로는 원리적으로 못 담는 차이다.

⚠️ `gm_id_grid`/`L_candidates`/`VDS_candidates`가 spec에 **전부 선언돼야만** knee를 잰다.
LUT 자신의 격자로 폴백하면 "이 설계가 실제로 탐색하는 범위"가 아닌 데서 재게 된다 --
self-test의 toy LUT 픽스처가 그 경우로, 폴백 knee가 W를 0.824um로 끌어내려 하한을 깼다.
근거가 없으면 계산하지 않고 호출자가 기존 배수로 폴백한다.

#### 결과

| | 상수 시절 | 전파만 | knee+전파 | **재탐색 후** |
|---|---|---|---|---|
| L 갈린 동치류 | **3/3** | 0 | 0 | **0** |
| M68류(NMOS) / M8류(PMOS) L | 0.18~0.375 혼재 | 0.18 / 0.18 | 0.245 / 0.340 | 0.245 / 0.340 |
| `mirror_ratio_error_pct` | 11.84 | 61.91 | 13.96 | **13.96** |
| `power_uA` | 267.59 | -- | -- | **225.38** |
| `area_um2` | 693.88 | -- | -- | **524.24** |

재탐색(정본 spec, SLSQP 5x80, 735초) 전 제약 통과: `gain_db` 60.39(>=54),
`cmrr` 60.00(>=60), `psrr` 63.93(>=60), `mismatch` 2.79(<=5), `centering` 0.1427(<=0.15),
**`parasitic_pm_deg` 70.12(>=70)**. self-test 둘 다 exit 0 / diff 0줄.

#### 남은 것 -- 층3과 층0 배선

* **층3(공동 sweep) 미완**: `M8류`가 `needs_joint_sweep=True`(주인 후보 M6·M7)인데 아직
  공동 sweep이 없다. 설계는 합의됐다 -- 동치류의 공통 L을 **theta 하나**로 두고(이름은
  동치류에서 파생, `L_cascode`류 **특정 이름 금지**) 걸린 **모든** gain 제약을 동시에
  만족시킨다(`metric_stage_budget`의 `metric`을 리스트로 확장). bounds는 새 함수가 필요
  없다 -- **이미 선언된 두 제약**이 상·하한을 정의한다(상한 `parasitic_pm_deg >=
  PM_target_deg`(§7.11, 배선 완료), 하한 `mismatch_sigma_mV <= 선언값`).
* **층0 게이트 미배선**: `audit_l_sharing_consistency()`는 만들었으나 파이프라인에 안 걸려
  있다(현재는 전파가 갈림을 없애므로 회귀 감시용). ★절대원칙상 배선하거나 승인받아야 한다.
* `L_ROLE_MULTIPLIERS`의 `bias_replica: 1.2`는 아직 상수다(knee가 대체하는 것은 `mirror`).
  그 role의 의도(§7.10 "PVT 민감도 완화, 미러의 출력임피던스 극대화가 아님")가 knee와
  다르므로 별도 판단이 필요하다.

### 10.10 층3 착지 -- 동치류 공통 L을 theta로 파생 (★ 신설 v4.38)

#### 무엇을 만들었나

`synthesize_l_class_thetas()` -- **동치류의 공통 L을 theta로 파생**한다. topology.json에
손으로 적지 않는다(사용자 지시 *"L theta를 일반화해. 특정 이름으로 하지마."*): 층1 동치류와
층2 주인에서 파생되고 이름도 대표 소자에서 만들어진다(`L_class__<root>`).

  * 주인(gain stage tail)이 있는 류에만 생긴다. 선언된 L theta가 그 류 멤버를 이미 건드리면
    만들지 않는다(자유도 중복 방지).
  * feed 타입 `l_class` 신설(`_feed_l_class`) -- **L만 확정**하고 gm_id/vds/W는 기존 경로가
    그 L로 다시 사이징한다. `_THETA_FEED_REGISTRY`가 문서화한 확장 계약("한 줄만 등록")대로.
  * 실측: 파일럿에만 2개(`L_class__M68` 주인 M5 / `L_class__M8` 주인 M6), 나머지 3개 회로는
    **0개 = 동작 무변경**.

#### 공동 sweep은 구조에서 저절로 나온다

주인이 여럿인 류(파일럿 M8류의 M6·M7)에서도 **theta는 하나**다 -- 자유도가 동치류당 하나뿐
이기 때문이다. 그 하나가 관련된 모든 gain 제약을 동시에 만족해야 하므로, 사용자가 말한
*"두 stage의 gain을 모두 만족시키는 L을 sweep"*이 별도 장치 없이 성립한다.

#### bounds -- 두 번 좁혔고 둘 다 실측이 시켰다

1. 처음엔 `L_candidates` 실측 전 범위(0.15~4.0um)를 썼다. **SLSQP가 L=1.86um 같은 곳으로 가
   diode 레퍼런스(M66/M18_bg, 0.25uA)가 W 한계 안에서 사이징 불가**가 되어 5 start 전부
   실패했다(1465초). 선언된 제약이 clamp할 기회조차 없다.
2. 그래서 상한을 **이 토폴로지가 이미 선언한 L theta들의 상한**(1.0um)으로 좁혔다. 그래도
   실패했다 -- 실현가능 L이 **연속 구간이 아니라 구멍이 뚫린 집합**이기 때문이다. 이건
   세션40이 이미 기록한 현상이다(`search_stage_budget_L_warm_start()` docstring:
   "feasible한 L 구간이 넓지 않고 좁고 끊긴 조각들로 존재").

#### 해결 -- 기준점 복구가 L 격자를 훑는다

`repair_infeasible_baseline()`(§10.7)을 두 군데 고쳤다:

  * **(theta, 값) 단위로 시도를 기록**한다. theta 이름만 기록하면 한 번 옮겨 병목이 옆으로
    간 뒤 같은 theta의 다른 값을 못 써본다 -- 실측으로 정확히 그 일이 났다(`L_class__M8`을
    하한으로 옮기자 병목이 **같은 류의 다른 멤버** M18_bg로 갔는데 거기서 멈췄다).
  * **L theta는 bounds 양 끝이 아니라 `L_candidates` 격자를 훑는다**(9점 서브샘플). 구멍이
    뚫린 집합이라 양 끝만 보면 못 찾는다.

실측 복구 경로(4단계, x0 feasible=True):

    L_stage2out_p 0.575 -> 0.15um     막힌 소자 [M15]에서 평가 성공
    L_class__M8   0.575 -> 0.15um     [M6,M66] -> [M18_bg]로 병목 이동
    L_class__M8   0.15  -> 0.245um    [M18_bg] -> [M6,M66]로 병목 이동   <- 재시도
    L_class__M68  0.575 -> 0.15um     [M6,M66]에서 평가 성공

#### 결과 -- 미러비 오차가 3.8배 줄었다

| metric | 층2까지 | **층3** |
|--------|---------|---------|
| `mirror_ratio_error_pct` | 13.96 | **3.64** |
| `cmrr_estimate_db` | 60.00 | **73.14** |
| `psrr_estimate_db` | 63.93 | **73.65** |
| `parasitic_pm_deg` | 70.12 | **77.37** |
| `gain_full_circuit_db` | 59.66 | **67.64** |
| `power_uA` / `area_um2` | 225.38 / 524.24 | 231.17 / 688.12 |

파생 theta가 고른 값: `L_class__M68 = 0.445um`, `L_class__M8 = 0.573um` -- **knee(0.245/0.340)
보다 위**다. 즉 sweep이 §7.10의 knee 시작점보다 나은 점을 실제로 찾았고, 그 대가로 면적이
늘고 미러비/CMRR/PSRR/PM이 좋아졌다. 전 제약 통과, self-test 둘 다 exit 0 / diff 0줄.

#### 중복계산 전수검사 (사용자 지시, 같은 커밋 범위)

프로파일로 재서 셋을 찾았고 **셋 다 이번 세션에 내가 넣은 코드**가 원인이었다:

| 원인 | 비중 | 고친 방법 | 결과 |
|------|------|-----------|------|
| `stack_kvl_vgs_limit()`이 `load_topology()`를 호출마다 | **99.3%** | 이미 부르며 **버리던 meta**를 캐시에 보관 | 0.142s → 0.001s |
| L2가 ω마다 네트워크 재조립(25회) | **28%** | ω 무관 조립을 `build_ac_network()`로 1회 | 0.371s → 0.024s |
| `_query` 18,636회 중 **12,891회(69.2%) 중복** | 44% | 메모이제이션(상한 400k) | — |

**평가 1회 1,325ms → 72.9ms(18배)**, 탐색 1,465초 → 134초. 이 원칙은 메모리
`feedback-always-check-recompute-efficiency`에 Python 코딩원칙으로 못박았다.

#### 남은 것

* `_L_ROLE_MULTIPLIERS`의 `bias_replica: 1.2`는 아직 상수다(knee가 대체한 것은 `mirror`).
  그 role의 의도(§7.10 "PVT 민감도 완화, 출력임피던스 극대화가 아님")가 knee와 달라 별도 판단.
* `search_stage_budget_L_warm_start()`는 아직 `metric_stage_budget`만 본다 -- `l_class`도
  포함하면 복구에 기대지 않고 처음부터 좋은 L을 준다(지금은 복구가 그 일을 대신한다).

### 10.11 `_L_ROLE_MULTIPLIERS` 완전 제거 -- knee를 실현가능 창으로 clamp (★ 신설 v4.39)

사용자 지시: *"bias_replica 상수도 없애"* -> **(1) 전 회로 적용**.

#### 남아 있던 상수와, 그것이 실제로 정하던 것

§7.10 C1/C9에서 `mirror: 2.5`는 이미 `knee_L_for_kind()`(LUT 실측)로 대체됐다. 남은 건
`bias_replica: 1.2`뿐이고, 실측하면 **파일럿 4소자**(M11a/M11b/M20a/M20b, class-AB 배터리
diode)의 L만 그 상수가 정하고 있었다.

그 값의 근거를 세 방향으로 찾았는데 **셋 다 없었다**:

| 후보 | 결과 |
|------|------|
| 선언된 mismatch | `mismatch_sigma_mV <= 5.0`은 `devices=['M1a','M1b']`만 본다 -- 이 4소자는 어떤 `matching_pair`에도 없다 |
| knee | PMOS knee 0.34um은 이 소자들의 W 한계를 깬다(`probe_stacked_diode_options.py`) |
| 소자별 W 실현가능성 | diode 물리로 다시 재면 창이 **0.245~0.440um** -- 실제로 쓰던 0.180um은 애초에 실현 불가능한 값이었다 |

#### 무엇을 만들었나 -- 두 함수, 전부 이미 있는 것에서 나온다

```
derive_role_L(ctx, name, spec, role)                  L = clamp(목표점, feasible_L_window(...))
derive_class_L(ctx, members, spec, prefer_knee)       주인 없는 동치류의 공통 L (창 교집합)
```

  * **목표점** `knee_L_for_kind()`(LUT 실측, §7.10) 또는 창의 하한 -- role이 고른다(아래 표).
  * **clamp** `feasible_L_window()` -- 선언된 `W_bounds`와 **그 소자의 실제 ID**로 그리는
    "W 한계 안에 들어오는 L 구간". 새 상수가 없다.
  * 판정 술어는 `lut_vdsat_headroom()` 안에 인라인으로 있던 것을 `feasible_gm_ids()`로
    꺼내 **공유**한다(두 벌로 갈라지지 않게).
  * role은 **어떤 측정을 쓸지**만 고른다(`_L_ROLE_TARGETS`). 값이 아니다:

    | `L_role` | 목표점 | 근거 |
    |----------|--------|------|
    | `mirror` | `knee_L_for_kind()` | 목적이 출력임피던스 극대화 -- 한계 gm/gds 효율 최대점(§7.10) |
    | `bias_replica` | 창의 하한 `lo` | §7.10이 선언한 이 role의 목적이 "PVT 민감도 완화"이고 **출력임피던스 극대화가 아니다**. gain 요구가 없으니 실현 가능한 가장 작은 L = 면적 최소 |

    등록 안 된 role은 `ValueError` -- 새 role은 **측정으로** 정의해 등록해야 한다(상수 금지).

#### ★ 한 번 합쳤다가 실측이 되돌렸다 (정직한 기록)

처음엔 두 role을 합쳐 **둘 다 knee**로 뒀다. "전류가 작으면 창이 알아서 작은 L을 강제한다"고
본 것인데, **틀렸다**. end-to-end로 돌리자 파일럿이 레이아웃에서 죽었다:

    ValueError: stack 'biasgen_vom_battery_a__pmos'(소자 ['M11a','M11b','M20a','M20b'])에
    대해 어떤 finger_w 후보도 못 찾음 (min_finger_w=1e-06, max_finger_w=4e-05)

PMOS knee 0.34um에서 이 배터리 diode들의 W가 **125.4um / 123.4um**로 나왔고(`W_bounds` 상한
200um 안이라 창은 "가능"이라 말한다), 두 W의 비가 1.0157이라 공통 finger 폭이 없다. 창은
"물리적으로 가능한가"를 말할 뿐 **"이 role에 맞는가"를 말하지 않는다** -- 그래서 목표점을
role에서 고르도록 되돌렸다. SLSQP는 이때도 수렴했다(start 1/3 success, 11.3s) -- 즉
사이징이 아니라 **레이아웃이 잡아낸 것**이고, self-test만 봤으면 못 봤다.

옛 상수와의 차이: `bias_replica: 1.2`는 `L_min`에 곱하는 고정 배수였고, `lo`는 이 소자의
실제 ID와 선언된 `W_bounds`로 매번 다시 재는 값이다. 실측으로 두 값은 **다르다**(0.180um
vs **0.245um**) -- diode 인식 창이 0.180um을 실현 불가능으로 정확히 걸러냈다.

#### diode는 gm_id가 자유롭지 않다 (self-test가 잡아낸 것)

`gate == drain`이면 vds가 gm_id를 정하고 gm_id가 W를 정한다. gm_id 격자를 훑는 판정은
diode에 **너무 관대**해서 못 쓰는 L을 통과시킨다 -- self-test 픽스처 `Mo`가 정확히 그
경우로, "가능"으로 나온 L에서 diode 자기일관 사이징이 W=0.824um로 하한 1um을 깼다
(`knee_L_for_kind()` docstring이 이미 기록해 둔 반례다). 그래서 `feasible_L_window()`에
분기를 뒀다 -- 새 판정을 만들지 않고 **이미 있는 `diode_vds_window()`**를 쓴다:

  * vds가 아직 자유로우면 -> 그 L에서 W 한계에 드는 vds가 있는가
  * vds가 이미 고정됐으면(`known_sizing` 등) -> 고를 자유가 없으니 그 vds가 강제하는
    gm_id(`gm_id_for_vgs(vds, L, vds, vsb)`, VGS==VDS)로 W를 직접 계산

#### 왜 theta로 파생하지 않았나 (사용자 선택지 (1)의 의도는 지키면서)

주인 없는 동치류까지 전부 theta로 만들면 파일럿만 **자유변수가 15개 는다**(24 -> 39, 실측).
SLSQP는 자유변수마다 유한차분을 돌아 탐색이 크게 느려지고 수렴도 어려워진다. 여기서 정하는
L은 **결정적으로 유도**되므로 자유도를 안 늘린다 -- 설계 자유도가 실제로 필요한 곳(gain
stage tail이 주인인 동치류)은 이미 층3이 theta로 노출했다. 즉 "전 회로에서 상수 제거"는
그대로 이루고, 탐색 비용만 안 낸다.

#### 폴백을 남기지 않았다

옛 코드는 knee를 못 재면 `L_min x 배수`로 값을 **지어냈다**. 지금은 즉시 `ValueError`다
(격자 3종이 선언돼야 knee를 잴 수 있다는 `knee_L_for_kind()`의 원칙 그대로). 실측:
4개 회로 전수 **상수 폴백 0건**. self-test toy 픽스처 6개가 격자를 선언하지 않아 새로
거부됐고, `_tst_grids()` 헬퍼로 실제 spec과 같은 모양(격자 3종 선언)으로 맞췄다 --
엔진에 새 폴백을 만들지 않았다.

#### 4개 회로 전수 측정 (`tests/probe_role_L_derivation.py`)

| 회로 | L_role 소자 | 유도 성공 | 상수 폴백 | **값이 달라진 것** |
|------|------------|----------|----------|------------------|
| current_reuse_telescopic_ota | 17(평가 도달) | 17 | 0 | **5** (M11a/M11b/M20a/M20b 0.180->**0.245**um, M37b clamp 0.245->0.350um) |
| folded_cascode | 13 | 13 | 0 | **0 = 동작 무변경** |
| two_stage_ota / nmcnr_amplifier | - | - | - | 평가가 세션41 이월 항목에서 먼저 실패(변경 전후 **동일**) |

`derive_class_L()`은 3개 회로에서 **15개 류에 실제로 호출**되고, 류 안에 목표점이 knee인
멤버가 하나라도 있으면 그 요구가 이긴다(`prefer_knee`) -- L은 류 전체가 하나뿐이라 더
보수적인 쪽을 따라야 한다. 남긴 이유: 소자별로 두면 같은 류에서 L이 갈릴 수 있고
(멤버마다 ID가 달라 창이 다르다), 갈리면 미러비 `ID2/ID1=(W2/L2)/(W1/L1)`가 순수 W 비로
축약되지 않는다. 실측으로 그 조건을 만나지 않았다는 것과 안전하다는 것은 다르다.

#### end-to-end 재탐색 결과 -- 착지가 v4.38보다 나쁘다 (정직한 기록)

정본 파라미터(`n_starts=3, maxiter=25`) 그대로 다시 돌렸다. **파이프라인은 끝까지 간다**:
SLSQP start 1/3 수렴(`max_violation=0`), floorplan aspect 1.190 / density 0.999 통과,
`run_full_circuit_audit.ok=True`. `audit_ok=False`는 `audit_row_split`의 레이아웃 항목이고
**이전 커밋에도 있던 것**이다(FAIL 79건 -> 80건, box-shape/common-centroid류).

그런데 **착지점이 v4.38보다 나쁘다**:

| metric | v4.38(커밋된 theta_star) | v4.39 재탐색 | |
|--------|------------------------|-------------|---|
| `power_uA`(목적함수) | 231.17 | **238.94** | 나쁨 |
| `area_um2` | 688.12 | 775.52 | 나쁨 |
| `cmrr_estimate_db` | 73.14 | 64.36 | 나쁨 |
| `psrr_estimate_db` | 73.65 | 69.72 | 나쁨 |
| `gain_full_circuit_db` | 67.64 | 63.26 | 나쁨 |
| `mirror_ratio_error_pct` | 3.64 | 17.67 | 나쁨 |
| `parasitic_pm_deg` | 77.37 | 73.19 | 나쁨(제약은 만족) |
| `gain_db` | 60.42 | 60.42 | 같음 |
| `L_class__M68` / `L_class__M8` | 0.445 / 0.573um | 0.245 / 0.575um | |

**원인은 유도가 아니라 탐색 착지다.** 근거: v4.38의 `canonical_theta_star.json`을 **새
엔진으로 그대로 평가**하면 여전히 실행가능하고 값도 더 좋다 --
`power_uA=231.2, area=655.4, cmrr=73.14, psrr=73.65, gain_full=67.64,
mirror_ratio_error=8.215, parasitic_pm=75.90`. 즉 새 엔진에서도 더 좋은 점이 실재하는데
SLSQP가 이번엔 3 start 중 1개만 수렴하면서 거기로 못 갔다(2/3, 3/3은 'Positive directional
derivative for linesearch'로 실패).

배터리 diode의 L이 0.180 -> 0.245um으로 바뀌면서 헤드룸 배분이 달라졌고, 그게 x0를 다른
계곡으로 옮긴 것으로 보인다. **이미 적어둔 다음 과제가 정확히 이 문제를 겨냥한다**:
`search_stage_budget_L_warm_start()`가 아직 `metric_stage_budget`만 보고 `l_class`를 안
본다(§10.10 "남은 것"). 그게 들어가면 L 계열 theta의 x0가 복구에 기대지 않고 처음부터
좋은 값에서 출발한다. 정본 탐색 파라미터(`n_starts`)를 임의로 올려서 덮지 않았다 --
세션31 BU가 검증한 값이고, 바꾸면 이후 모든 비교의 기준이 흔들린다.

#### self-test는 '통과'가 아니라 '동작'을 본다

없어진 7-3f 블록 자리에 `derive_role_L()` 게이트를 넣되, **clamp가 위/아래 양방향으로
실제로 값을 바꾸는지**를 assert한다(toy LUT knee=0.350um 기준):

    ID=30000uA, W_bounds 1~200um  -> 창=[0.180,0.180]um, 0.350 -> 0.180um (아래로)
    ID=0.01uA,  W_bounds 120~200um -> 창=[0.500,1.000]um, 0.350 -> 0.500um (위로)

여기에 (1) ID 미확정 -> knee 그대로, (2) 격자 미선언 -> `None`(호출부가 거부), (3)
`cascode`/`signal` -> `ValueError`(없어진 `select_L_by_role()`의 가드를 이관 -- 옛 함수는
self-test에서만 불렸는데 이제 **실제 사이징 경로 위에** 있다), (4) 전류가 4배 다른 두
멤버의 류 공통 L이 양쪽 창 안. self-test 둘 다 exit 0.

### 10.12 웜스타트에 `l_class` 포함 -- 두 번의 되돌림 (★ 신설 v4.40)

사용자 지시: *"warm start에 l_class 포함해서 재탐색해"*. §10.11이 남긴 과제다.

#### 타입 하나 추가로 끝나는 일이 아니었다 (먼저 쟀다)

`tests/probe_lclass_warm_start.py`로 두 가지를 먼저 쟀다:

1. **`l_class` theta에 걸리는 제약은 전부 footprint가 "ALL"이다** -- 파일럿 실측:
   `cmrr_estimate_db` / `psrr_estimate_db` / `parasitic_pm_deg`. 기존 고속경로 두 갈래
   (`gain_stages_sum` 방향 판정 / `battery_centering_deviation` 최소화)는 "이 theta의
   `devices`만 보면 방향을 안다"는 전제 위에 있어 **쓸 수 없다**. 타입만 추가했으면
   `bounds-midpoint`로 조용히 후퇴해 **무동작**이 됐을 것이다. 그래서 실제 `evaluate()`
   조인트 스캔(complex 분기)으로 보낸다.
2. **웜스타트가 정한 theta는 SLSQP 자유변수에서 빠진다**
   (`held_names = vote_determined | stage_budget_L`). `l_class`가 거기 들어가면 층3이
   만든 설계 자유도를 격자점에 얼리는 셈이다 -- §10.10 실측에서 SLSQP는 격자 사이 값
   (0.445/0.573um)을 찾아 knee보다 나은 점에 도달했었다. 그래서
   `presolve_warm_start()` 반환에 **`l_class_L`**을 신설해 x0만 주고 자유변수로 남긴다.

#### ★ 되돌림 1 -- 점수를 목적함수로 뒀다가 되돌렸다

`l_class` 그룹엔 centering 같은 전용 metric이 없다. 처음엔 선언된 `objective`
(`power_uA` 최소)를 점수로 썼다. **실측이 틀렸다고 했다**: 실현가능 후보 중 전력이 가장
낮은 점은 `L_class__M68`의 **bounds 하한(0.15um)**이었고, 착지점의
`mirror_ratio_error_pct`가 **43.45%**였다(v4.38: 3.64). 미러비 오차는 `V_A = ID/gds`에
반비례하고 `V_A`는 L에 비례하므로, L을 하한에 붙이는 것은 **층3이 존재하는 이유를 정확히
거스른다**.

바꾼 기준: **선언된 제약의 최소 여유를 최대화**(`_group_score_interior()`). 각 제약의
여유를 그 제약값 자신으로 정규화해 최솟값을 본다 -- 새 상수가 없다. 웜스타트의 일은
최적점을 찾는 게 아니라 **SLSQP가 잘 출발할 실현가능점을 주는 것**이고, 제약 경계에 붙은
점은 (1) 민감도가 죽고 (2) 한 발만 움직여도 infeasible이라 linesearch가 막힌다.

#### ★ 되돌림 2 -- 진짜 원인은 `baseline` 주입이었다 (프로브가 잡았다)

점수를 바꿔도 프로브는 여전히 **`L_class__M68`이 자유변수에서 빠졌다**고 경고했다.
`held_names`에는 안 넣었는데도 그랬다 -- 자유변수 필터는 조건이 하나 더 있다:

    graph[name]["classification"] in ("coupled", "ambiguous")

`presolve_warm_start()`가 스캔 결과를 `baseline`에 주입한 **직후** 그 baseline으로
`derive_theta_dependency_graph()`를 부르는데, 주입된 점에서 분류가 `isolated`로 뒤집혔다.
같은 회로에서 복구된 기준점 기준으로는 `ambiguous`다(실측: L 값 0.15~0.575um 어디서도
`ambiguous`였다 -- 즉 뒤집은 건 이 theta 자신의 값이 아니라 함께 주입된 다른 L들이다).

고침: `baseline`에는 **고정될 theta만** 주입한다(`stage_budget_L_held`). x0에는 그대로
반영되므로 웜스타트 효과는 유지된다. 프로브 재측정: **2/2가 자유변수로 남는다**.

#### 결과

| metric | v4.38 | v4.39(웜스타트 전) | **v4.40** |
|--------|-------|------------------|-----------|
| `power_uA`(목적함수) | 231.17 | 238.94 | **231.17** |
| `gain_db` | 60.42 | 60.42 | **61.56** |
| `mismatch_sigma_mV` | 2.795 | 2.795 | **1.334** |
| `gain_full_circuit_db` | 67.64 | 63.26 | **67.08** |
| `cmrr_estimate_db` | 73.14 | 64.36 | 72.55 |
| `psrr_estimate_db` | 73.65 | 69.72 | 72.49 |
| `parasitic_pm_deg` | 77.37 | 73.19 | 75.02 |
| `mirror_ratio_error_pct` | 3.64 | 17.67 | 7.13 |
| `area_um2` | 688.12 | 775.52 | 806.90 |
| `L_class__M68` / `__M8` | 0.445 / 0.573um | 0.15 / 1.0um | **0.511 / 0.474um** |

웜스타트 전 대비 전 항목이 개선됐고, v4.38 대비로는 목적함수 동률(231.17)에 `gain_db`
+1.14dB, `mismatch_sigma_mV` **2.1배 개선**, `gain_full` 동급이다. 대신 `area`가 17%
크고 `mirror_ratio_error_pct`가 3.64 -> 7.13이다. floorplan/`run_full_circuit_audit.ok`
통과, self-test 둘 다 exit 0.

#### 남은 판단 -- `mirror_ratio_error_pct`는 아직 제약이 아니다

topology.json이 이 metric에 적어둔 그대로다: *"제약은 아직 걸지 않는다 -- 먼저 재고 나서
상한을 정한다."* 이제 여러 착지점에서 값을 봤다: **3.64 / 7.13 / 17.67 / 43.45%**. 탐색이
좋아질수록 이 값이 나빠지는 방향으로 자유도를 쓴다는 것이 드러났다(제약이 없으니 당연하다).
상한을 얼마로 걸지는 **설계 결정**이라 사용자 확정 없이 넣지 않는다.

### 10.13 미러비 계통오차에 상한 -- **숫자를 박지 않고** (★ 신설 v4.41)

사용자 지시: *"mirror_ratio_error 상한 걸어. 얼마가 적당한지 근거로 제안해"* ->
*"상수를 임의로 자꾸 만들지마. 근거가 되는 mismatch_sigma_mV만 유지하고 나머지는 계산으로
도출해서 caching하도록 해."* -> *"그게 이번에 고친 이유잖아. 원칙에 추가해."*

#### ★ 내가 먼저 틀렸다 (기록)

처음엔 `mirror_ratio_error_pct <= 8.0`을 박았다. 유도는 있었다 -- 선언된
`mismatch_sigma_mV <= 5.0mV` × 입력쌍 실측 `gm_id = 16.00/V` = 8.00%. 주석에 그 유도를
적어두기까지 했다. **그래도 틀렸다**: 유도를 주석에 적고 **결과 숫자를 박는 순간 그 유도는
문서일 뿐 코드가 아니게 된다** -- `gm_id`가 바뀌어도 8.0은 안 따라간다. §10.11에서 세션
절반을 들여 없앤 `_L_ROLE_MULTIPLIERS`와 **정확히 같은 형태의 상수**를 같은 세션에 다시
만든 것이다. 사용자가 즉시 지적했고, 원칙으로 못박았다
(메모리 `feedback-never-invent-constants-derive-and-cache`).

#### 해법 -- 단위를 맞추면 임계값이 참조로 끝난다

`%`로 두면 임계값을 `sigma x gm_id`로 계산해 박아야 한다. 대신 **같은 오차를 입력환산
전압으로** 재면 랜덤 예산과 단위가 같아진다:

    dI/I = |dVDS| / V_A          계통 (1차 CLM, V_A = ID/gds)
    dV   = (dI/I) / (gm/ID)      입력환산 -> mismatch_sigma_mV와 **같은 단위**

그래서 제약에 **숫자가 없다**:

```json
{"metric": "mirror_ratio_error_mV", "op": "<=",
 "value_from_constraint": "mismatch_sigma_mV"}
```

규칙은 *"계통 오차가 이 회로가 이미 받아들이기로 한 **랜덤** 오차 예산을 넘지 않는다"*이고,
이 회로에 남은 선언 숫자는 여전히 `mismatch_sigma_mV = 5.0` **하나**다.

#### 만든 것

| 이름 | 역할 |
|------|------|
| `_mirror_ratio_error_pairs(ctx)` | 쌍별 `(전류비 오차, 입력환산 V)`를 **한 번** 계산해 `ctx.derived`에 캐시 -- `pct`/`mV` 두 metric이 공유(재계산 0) |
| `_mirror_ratio_aggregate()` | 선언된 `aggregate` 적용을 두 metric이 공유 |
| `_metric_mirror_ratio_error_input_referred` | 같은 오차의 입력환산 표현(정규 단위 V). `mirror_ratio_error_pct`는 사람이 읽는 보고용으로 유지 |
| `resolve_constraint_references()` | 인라인이던 `value_from_spec` 해석을 **이름 있는 함수**로 빼고 `value_from_constraint` 추가. 참조 연쇄 금지(근거는 한 곳에만) |

#### 부수 소득 -- 내가 박은 8.0%는 물리적으로도 틀렸다

쌍마다 **자기 gm_id**로 환산하는 것이 맞다. 최댓값을 만드는 쌍은 `M10/M12`(`gm_id`=22.50/V)
인데 나는 입력쌍의 `gm_id`=16.00/V를 거기 적용했다. 같은 동작점을 제대로 환산하면
8.215% = **3.65mV**로 예산 5.0mV 안이다. 즉 박힌 숫자는 근거를 못 따라갈 뿐 아니라 **잘못된
환산**이었다.

구속력은 그대로다 -- 나쁜 착지들은 여전히 탈락한다: 17.67% -> 7.85mV, 43.45% -> 19.3mV.

#### 게이트가 실제로 거부하는지 (self-test)

  * 동작: `dVDS=0.5V / V_A=10V -> 5.00%`, `gm_id=20/V`로 나누면 `2.50mV`(같은 오차의 두 표현).
  * 캐시: 쌍별 표가 `ctx.derived`에 남아 두 metric이 공유한다.
  * **거부 3종**: 참조 대상 없음 / 참조 대상이 자기도 참조(연쇄) / `value`와 참조가 둘 다
    있고 값이 다름 -- 전부 `ValueError`.
  * 저장소 자체 게이트도 새 타입을 잡았다(`_metric_device_footprint()` 미등록 -- 이번 세션
    `parasitic_pm_deg`/`l_class` 때와 같은 자리). 등록해서 해결.

#### 결과 -- 착지 무변경, 여유 36%

정본 재탐색 착지가 v4.40과 **동일**하다(power 231.17, gain_db 61.56, mismatch 1.334,
cmrr 72.55, psrr 72.49, gain_full 67.08, parasitic_pm 75.02). 새 제약은
`mirror_ratio_error_mV = 3.186mV`로 예산 5.0mV 대비 **36% 여유**로 통과한다. 즉 지금
설계를 바꾸는 제약이 아니라, 탐색이 이 축을 희생하려 할 때 **막는** 가드다(§10.12에서
실제로 43.45%까지 갔다). floorplan/`run_full_circuit_audit.ok` 통과, self-test 둘 다 exit 0.

L5c 픽스처에서는 이 제약을 뺐다 -- `classab_centering_dev_v`/`gain_db`/`parasitic_pm_deg`를
뺀 것과 **같은 판단이고 같은 근거 제시 방식**이다(픽스처는 거의 모든 theta를 중점에 고정한
인위적 한 점이라 L 자유도가 필요한 제약을 검증할 자리가 아니다 -- 픽스처 값 vs 자유탐색 값을
나란히 적었다).

#### ⚠️ 그런데 그 앵커 자신은 근거가 없다 (사용자 질문으로 드러남)

사용자: *"mismatch_sigma_mV가 어떻게 도출된 값이지?"* -- 추적했고, **기록된 도출 근거가
없다**:

  * 설계 초안(`docs/04-report/analog-topology-json-library.do.md` 1457행)은
    `{"metric": "mismatch_sigma_mV", "op": "<=", "value": X}`로 **X를 자리표시자**로 뒀다.
  * 최초 라이브러리 커밋(`e329283`, 배치 1~7)에서 5.0으로 채워지며 **근거 주석 없이** 남았다.
  * `two_stage_ota`는 그 값을 명시적으로 복제했다(*"새 문헌값이 아니라 ...
    current_reuse_telescopic_ota의 문턱(5.0mV)을 재사용"*).
  * `gain_db >= 75.6`이 세션44에서 재도출되기 전과 **정확히 같은 상태**다 -- 그
    `_gain_db_target_comment`가 *"이 constraint만 도출 근거 주석 없이 남아있었음"*이라고
    적은 바로 그 부류이고, 이제는 `mismatch_sigma_mV`가 그 마지막 하나다.
  * **한 번도 구속한 적이 없다**: 실측 착지 3.01(세션28) / 2.795(v4.38~4.39) /
    1.334(v4.40~4.41) -- 전부 5.0 아래다.

즉 §10.13이 "숫자 0개"를 이룬 것은 사실이지만, 그 **참조 대상 자체가 근거 없는 숫자**다.
그리고 이제 `mirror_ratio_error_mV`가 이 값을 참조하므로 이 숫자를 고치면 그 제약도 함께
움직인다 -- 근거를 세우는 일의 중요도가 올라갔다.

재도출 방법은 **사용자 확정 전까지 정하지 않는다**(값을 지어내지 않는다). 선언 옆
(`constraints`의 `_comment`)에 이 사실을 그대로 기록해 뒀다.

### 10.14 입력환산 오프셋 + 달성 가능 임계값 유도 (★ 신설 v4.42)

#### (1) 오프셋을 만드는 쌍이 하나가 아니었다 (사용자 지적)

사용자: *"파일럿은 PMOS/NMOS 모두야. M1a/M1b/M2a/M2b, M3a/M3b/M4a/M4b인 current reuse
구조지. ... 모두 해야 하는 거 아닌가?"* -- 넷리스트로 확인했고 **맞다**:

    게이트가 입력(Vip/Vim)에 물린 소자 = M1a/M1b(pmos, s=Vx) + M4a/M4b(nmos, s=Vy)
    symmetry.matching_pairs도 **둘 다 이미 `offset`으로 선언**돼 있었다
    그런데 metric은 `devices: ["M1a","M1b"]` -- **한 쌍만** 세고 있었다

**사이징은 반영돼 있었다**: `topology_library.current_reuse_telescopic_topology()`가 원문
Eq.5(`gm1 = gmn + gmp`)를 명시적으로 다루고(2026-07-31 사용자와 설계), `stage_devices` 4개 +
`shared_gm_id_groups [[0,1],[2,3]]`로 두 쌍이 전류를 공유한다(실측 `gm(M1a)=gm(M4a)=79.7uS`).
**반영 안 된 곳은 mismatch metric 한 곳뿐**이었다.

#### (2) 새 metric -- `input_referred_offset` (사용자 확정: gm 가중, 캐스코드 제외)

    sigma_in = sqrt( sum_i (gm_i * sigma_i)^2 ) / sum_i gm_i

쌍 i의 Vth 미스매치는 출력에서 전류오차 `gm_i*sigma_i`를 만들고, **입력으로 되돌리려면
전체 전달컨덕턴스로 나눈다**. current-reuse는 그 합이 `gm_p+gm_n`이다.

  * 쌍은 **선언에서 찾는다**(`input_referred_offset_pairs()`): `matching_sensitivity ==
    "offset"` **그리고** 게이트가 `ports`의 `direction=="input"` net에 물린 것.
  * 실측으로 이 두 번째 조건이 실제로 일을 한다 -- 파일럿의 `offset` 쌍은 셋인데
    `M37a/M37b`는 **CMFB 오차증폭기**(g=Voc/Voc_des)라 신호 입력쌍이 아니다.
  * 캐스코드(M2a/M2b, M3a/M3b)는 게이트가 Vbias2/Vbias3이고 선언도 `ratio`라 **두 조건
    모두에서 자동으로** 빠진다.
  * 쌍이 하나뿐인 회로(`two_stage_ota` M1/M2)는 `sigma_1`으로 **정확히 환원** = 동작 무변경.
    (그 회로에 `ports` 선언을 추가했다 -- net 이름이 `vin_p`/`vin_n`이고 connectivity는
    안 건드린다.)
  * 실측: 2.795mV(옛, PMOS쌍만) vs **1.651mV**(gm 가중, 두 쌍). 크기도 1.69배 다르지만 더
    중요한 건 **M4a/M4b의 사이징이 오프셋에 아무 영향을 못 주고 있었다**는 점이다.

**기존 소비자 셋을 조용히 끄지 않았다**: `devices`를 읽는 `_metric_device_footprint()`와
`make_matching_feasibility_check()`(사이징 중 mismatch 선제 필터)가 있어서,
`materialize_input_offset_pairs()`가 **빌드 시 한 번** 찾아 `devices`/`_pairs`를 선언에
적어둔다(`value_from_spec` 치환과 같은 관례). 가드는 쌍 단위로 판정하는데, 그것이
전체 조건의 **충분조건**임을 증명해 docstring에 적었다:
`sum w_i = 1`이므로 모든 쌍이 `sigma_i<=B`면 `sigma_in <= sqrt(sum w_i^2)*B <= B`.

#### (3) `mismatch_sigma_mV = 5.0`은 근거가 없었다 -> 유도로 대체

§10.13 말미에 기록한 대로 그 값은 do.md의 자리표시자 `"value": X`가 최초 커밋에서 채워진
것이고 **한 번도 구속한 적이 없었다**. 사용자 확정(*"1번으로 진행해"*)에 따라 세션44가
`gain_db`에 손으로 한 절차를 **회로/metric 무관 함수**로 만들었다:

```
achievable_metric_bound(topology_path, spec, metric_name, sense, n_probes, slsqp_kwargs)
  1. objective를 그 metric으로 교체
  2. 그 metric의 제약 + **그 값을 참조하는 제약**을 제거(순환/참조 붕괴 방지)
  3. 나머지 제약은 전부 유지 -- "예산 안에서 실제로 도달하는 값"이 질문이다
  4. 서로 다른 random_seed로 그 회로의 **선언된 탐색 파라미터** 그대로 n_probes회
```

**마진 상수도 안 쓴다**: `conservative` = 수렴한 probe가 **전부** 도달한 값. 세션44가 3dB
마진의 이유로 든 것이 "LUT 격자 해상도/SLSQP 재현성 편차 흡수"인데, 그 편차가 곧 probe
사이의 퍼짐이므로 실측으로 흡수하면 지어낼 필요가 없다.

##### 실측이 두 번 되돌렸다

  1. probe를 `n_starts=1`로 깎았더니 3 probe 전부 "실현가능한 해를 못 찾음" -- 이 회로는
     정본 3-start 중 보통 1개만 수렴한다. probe를 가르는 것은 **`random_seed`**다.
  2. `mirror_ratio_error_mV`가 `value_from_constraint: mismatch_sigma_mV`를 쓰고 있어서,
     그 값을 재는 동안 참조가 갈 곳을 잃었다 -> **참조하는 제약도 함께 제거**.

##### 그리고 세 번째로 되돌렸다 -- 바인딩 방식 (정직한 기록)

처음엔 `value_from_achievable`를 **런타임 참조**로 만들어 사이드카에서 읽게 했다. 그러자
**self-test/진단 픽스처가 줄줄이 깨졌다** -- 그것들은 일부러 다른 격자(spec)와 임시 경로를
쓰는데, 유도는 정본 spec 지문에 묶여 있기 때문이다. 빌드를 죽이면 회로 해석 전체가 막힌다.

바꾼 방식: **유도 스크립트가 결과를 선언 자신에 적는다.**

```json
{"metric": "mismatch_sigma_mV", "op": "<=",
 "value": <유도값>,
 "value_from_achievable": {"sense": "min"},
 "_derived": {"by": "achievable_metric_bound", "spec_fingerprint": "...",
              "per_probe": [...], "constraints_dropped": [...], "derived_at": "..."}}
```

  * 숫자는 있지만 **손으로 적은 게 아니라 생성된 것**이고, 언제 어떤 조건에서 나왔는지가
    붙어 있다 -- 사용자의 반대("유도를 주석에 적고 결과를 박으면 근거가 바뀌어도 안
    따라간다")에 대한 답은 `_derived.spec_fingerprint`다: 지문이 어긋나면 엔진이 **안다**.
  * 엔진은 평소처럼 `value`만 읽는다 -> 모든 픽스처가 그대로 동작.
  * 지문 불일치는 **빌드를 죽이지 않고** `_RESOLVE_STALE_NOTES`에 기록한다(조용하지 않되
    해석을 막지도 않는다). `value`가 아예 없으면 손으로 적지 말라며 `ValueError`.

#### (4) ★ 유도는 **실패했다** -- 그리고 실패가 답을 줬다

두 회로 모두 `achievable_metric_bound()`가 값을 못 냈다. 원인이 서로 다르다:

| 회로 | 실패 |
|------|------|
| 파일럿 | sigma를 objective로 최소화 -> 3 probe 전부 "실현가능한 해 없음" |
| `two_stage_ota` | `stage1_out` VDS 합이 vdd와 불일치 -- **세션41 이월 항목**(이번 변경 전부터 평가 불가) |

파일럿의 실패가 핵심이다. **두 방향 모두 막힌다**:

  * `sigma`를 최소화하면 `W*L`이 커지고 -> `Cgg` 증가 -> 노드 pole 하강 ->
    **`parasitic_pm_deg`와 정면충돌**해 실현가능점이 사라진다.
  * 제약을 떼고 원래 objective(power 최소)로 두면 최적화기가 입력쌍을 줄여 **sigma가 오히려
    나빠진다** -- 세션31이 이미 실측했다: *"M1a/M1b가 power 최소화로 L=0.235um/W=2.505um를
    골랐는데, `mismatch_sigma_mV<=5.0`을 만족하려면 W*L이 4.7배 필요"*.

**결론: 이 임계값은 회로 안에서 도출되는 값이 아니라 시스템 레벨 오프셋 요구에서 와야 하는
설계 입력이다.** 내가 제안하고 사용자가 고른 "1번(달성 가능 상한에서 역산)"이 이 metric에는
성립하지 않는다는 것이 **측정으로** 드러났다 -- `gain_db`는 "높을수록 좋다"라 상한이 의미가
있지만, `sigma`는 **면적/PM과의 트레이드오프 지점**이라 회로 혼자 정할 수 없다.

그래서 **값을 지어내지 않고** 5.0을 유지하되, 두 회로 선언에 유도를 시도했고 왜 실패했는지를
그대로 적었다. 미구현 후보도 남겼다 -- **제약값 자체를 bisection**해 "탐색이 아직 실현가능한
가장 빡빡한 sigma"를 찾는 것. 그건 위 두 실패를 모두 피한다(objective를 안 바꾸고, 제약을
떼지도 않는다).

⚠️ `achievable_metric_bound()`/`tests/derive_achievable_bounds.py`는 **이 metric에 대해서는
쓸모없는 답을 낸다**. `gain_db`류(단조 방향이 있는 metric)에는 유효하지만 아직 그 용도로
배선되지 않았다 -- "만들면 반드시 배선하라" 원칙상 **사용자 판단 대기**(유지/되돌림/bisection
확장).

#### (5) 재탐색 실측 -- 설계는 안 바뀌었다

| metric | v4.41 | **v4.42** |
|--------|-------|-----------|
| `mismatch_sigma_mV` | 1.334 (옛 정의, PMOS쌍만) | **1.090** (입력환산, 두 쌍) |
| `power_uA` / `gain_db` | 231.17 / 61.56 | 231.17 / 61.56 |
| `cmrr` / `psrr` / `gain_full` | 72.55 / 72.49 / 67.08 | 동일 |
| `mirror_ratio_error_mV` | 3.186 | 3.186 |
| `parasitic_pm_deg` / `area_um2` | 75.02 / 806.90 | 동일 |

착지가 **완전히 같다**. metric이 더 정확해졌지만 임계값 5.0이 여전히 안 걸리기 때문이다
(1.090 << 5.0) -- 즉 **정의를 고친 효과는 지금 설계에 안 나타나고, 임계값이 근거를 얻은 뒤에야
나타난다**. floorplan/`run_full_circuit_audit.ok` 통과, self-test 둘 다 exit 0.

## 11. CircuitGraph -- 다음 baseline (★ 신설 v4.42, 사용자 지시)

사용자: *"여기까지 구현한 것을 계획에 모두 반영해놓고, 지금 새롭게 다듬어진 계획을 기본적인
최초 baseline으로 작성하고 이것 활용하는 방향으로 엔진을 다시 개선하자."*

### 11.1 왜 -- 지금 그래프는 열 번쯤 만들어졌다 버려진다

같은 넷리스트를 **각자 다시 훑는** 함수들(전수):

| 함수 | 하는 일 |
|------|---------|
| `signal_path_nodes(by_name, excite, sense)` | gate->drain / source->drain **방향 그래프**로 신호경로 노드 유도(§7.11이 이미 사용) |
| `true_current_mirror_groups` / `l_sharing_classes` / `gain_stage_tails` / `vgs_alias_map` | 미러군·L 동치류·tail |
| `input_referred_offset_pairs`(§10.14 신설) | 입력 offset 쌍 |
| `find_diode_stacks` / `propagate_topology_forced_currents` / `derive_horizontal_stack_groups` | KCL·스택 |
| `_full_circuit_devices` / `_mna_stamp_capacitance` / `node_pole_estimate` | MNA·용량·pole |
| `propagate_node_voltages` | **모든 내부 노드의 DC 절대전압** |
| `StackGraph`/`build_graph`(stick_diagram) | **레이아웃(Euler trail) 전용** -- 전기 해석용 아님 |

★ 특히 `propagate_node_voltages()`는 **전 노드 DC 전압을 계산해 vsb 복원에만 쓰고 버린다**.
사용자가 요구한 "노드에 DC bias 저장"은 새로 만들 게 아니라 **버려지는 것을 붙잡는 것**이다.

### 11.2 노드/엣지 스키마 -- 소비자에서 역산했다(지어내지 않음)

**노드(net)**

| 필드 | 지금 만드는 곳 | 현재 상태 |
|------|---------------|-----------|
| `voltage_dc`, `unresolved`, `conflicts` | `propagate_node_voltages()` | **계산 후 버림** |
| `terminals` (소자,단자) | 함수마다 재구성 | 매번 재계산 |
| `degree`(2단자 vs 3+단자 허브) | `audit_vertical_stack_id_vs_kcl` | 재계산 |
| `port_role`/`direction` | `ports` 선언 | §10.14에서 캐시 시작 |
| `cap_total` | `_mna_stamp_capacitance()` | 평가마다 재계산 |
| `pole_rad_s` | `node_pole_estimate()` | 재계산 |
| `on_signal_path` | `signal_path_nodes()` | 재계산 |
| `stack_id`/`budget`/`slack` | 선언 + 헤드룸 배분 | 부분 |
| **`flow_dir`(신호 전파방향)** | **없음** | **아래 11.3** |
| **`stage_index`** | **없음** | Q1 Case B가 요구 |

**엣지(소자)**: 선언 쪽(`kind`, 단자, `device_roles`, `is_diode`, `mirror_group`,
`l_class`, `matching_pair`+`sensitivity`)은 대부분 이미 캐시돼 있다. 없는 것은
**`stage_index`와 `role_in_stage`**(input/cascode/tail/load).

### 11.3 ★ 신호 전파방향을 노드에 기록하고, 탐색은 **항상 input->output**

사용자 지시: *"노드에 신호의 전파방향도 기록되어 있어서 stage를 탐색할 때 역방향으로
탐색하지 않고 언제나 input ports부터 output ports까지의 방향으로 탐색되도록 해야 해."*

  * 방향의 근거는 소자 물리다 -- 신호는 `gate->drain`, `source->drain`으로 간다
    (`signal_path_nodes()`가 이미 이 규칙으로 유도한다). 그 함수는 지금 **집합만** 돌려주고
    방향 정보를 버린다.
  * 노드에 `flow_dir`(이 노드가 입력에서 몇 홉인지 = 위상 순서)과 `preds`/`succs`를 남기면,
    stage 탐색이 **위상 정렬 순서대로 한 방향으로만** 돈다.
  * 왜 중요한가: 역방향 탐색은 (1) 피드백 경로(CMFB, Miller `Cc`)에서 **순환에 빠지고**
    (2) "이 쌍이 몇 단째인가"를 모호하게 만든다. 방향을 고정하면 피드백 엣지를
    **역엣지로 명시적으로 표시**해 stage 계산에서 빼고 안정성 해석에만 쓸 수 있다.
  * 출력은 `ports`의 `direction=="output"`으로 정의된다 -- 파일럿은 Vop/Vom이 이미 선언돼
    있고, `two_stage_ota`는 §10.14에서 입력만 적었으니 출력도 필요해지면 추가한다.

### 11.4 ★ 3층 분리 -- 안 지키면 평가 간 오염이 난다

| 층 | 내용 | 수명 | 무효화 |
|----|------|------|--------|
| **L1 정적** | 연결성·선언·유도된 구조(미러군, L동치류, 신호경로, 방향, stage, diff-pair) | topology당 1회 | 파일 변경 |
| **L2 평가별** | 사이징, `voltage_dc`, `cap_total`, `pole`, 헤드룸 slack | 평가 1회 | 매 평가 새로 |
| **L3 지속** | 지난 수렴점, 달성 가능 임계값, 실현가능 창 | 세션/디스크 | `spec_fingerprint` 불일치 |

지금 `ctx`(평가별)와 `_load_full_topology_cached`(토폴로지별)가 분리돼 있는 이유가 이것이다.
L3는 §10.14에서 시작했다(`<topo>.derived.json` + 선언의 `_derived`).

### 11.5 탐색범위 축소 -- 조각은 이미 있는데 서로 모른다

  * `search_stage_budget_L_warm_start(window_around_reference=True, window_frac=0.2)` --
    **기준값 근방만 스캔하는 기능이 이미 구현돼 있는데** 기준을 줄 사람이 블록좌표
    탐색뿐이다.
  * `tests/canonical_theta_star.json` -- 지난 수렴점이 파일로 있는데 탐색이 안 읽는다.
  * `feasible_L_window`/`diode_vds_window` -- 매번 전 격자를 훑는다.

L3에 지난 수렴점을 넣으면 셋이 한 기준을 공유한다: SLSQP bounds를 "지난 해 ± 여유"로 좁히고
창 스캔도 그 근방부터. 세션40이 기록한 *"feasible한 L은 좁고 끊긴 조각들"* 문제에 직접
듣는다 -- 넓게 훑는 대신 **지난번에 살아남은 조각 근처**를 촘촘히 본다.

### 11.6 ★ 정직한 한계 -- 다중 differential pair를 아직 정확히 못 다룬다

사용자 질문: *"differential pair가 여러 개 있을 때 gain과 mismatch 모두 정확히 다룰 수
있나?"* -- 답은 **아니오, 세 경우 중 하나만 맞다**.

| 경우 | 예 | gain | mismatch |
|------|-----|------|----------|
| **A. 같은 입력에 병렬** | current-reuse M1a/M1b ∥ M4a/M4b | `stage_devices`+`shared_gm_id_groups` **손 선언**, topology_fn이 gm1->gmp/gmn 손 분할 -- 결과는 맞지만 유도 아님 | §10.14의 gm 가중이 **이 경우에만** 맞다 |
| **B. 직렬(cascade) 단** | 2단/3단 amp의 2단 쌍 | `gain_stages_sum`의 `stages`도 손 선언 | **틀린다.** 2단 오프셋은 선행 이득으로 나눠 입력환산해야 하는데(`sigma_in += sigma_2/A_1`) 그 개념이 없다 |
| **C. 다른 입력의 쌍** | CMFB 오차증폭기 M37a/M37b | -- | `ports` 필터가 빼는 건 맞지만 **무해하다는 뜻이 아니다** -- 출력 공통모드를 미는 별도 오프셋인데 재는 metric이 없다 |

그리고 **"각 쌍의 오프셋을 개별로 최소화"는 단일 입력환산 제약 하나로는 불가능하다** --
그 제약은 총합만 보므로 최적화기가 한 쌍을 줄이고 다른 쌍을 키워도 통과한다. 쌍별 요구가
있으면 쌍별 metric+constraint를 선언해야 하고, 프레임워크는 지원하지만 자동 유도는 없다.

공통 원인은 하나다 -- **"몇 개의 단이 있고 어느 쌍이 몇 단째인가"를 사람이 topology.json에
적고 있다.** `stage_index`가 유도되면 B가 풀리고, 손 선언(`stage_devices`/`gain_stages`/
`shared_gm_id_groups`)을 유도값과 대조해 궁극적으로 대체할 수 있다.

### 11.7 단계 (승인 후 착수)

1. **L1 그래프 신설 + 기존 순회 이설** -- 동작 무변경, 4개 회로 전수로 출력 동일 증명.
2. **L2 부착** -- `propagate_node_voltages()` 결과를 버리지 않고 적재 + 용량/pole/헤드룸.
3. **방향 + stage/diff-pair 유도**(11.3) -- 손 선언과 **대조 보고만**, 아직 대체 안 함.
4. **L3 기준값** -- warm start·SLSQP bounds·창 스캔이 공유(11.5).
5. 그 위에서 오프셋 **Case B/C** 확장(11.6).

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-09-04 | 초안 작성 — SPICE 트랜지언트 검증 중 발견한 diode-connected 헤드룸 버그를 계기로 gain-budget-first 근본 재설계안 정리 |
| 1.1 | 2026-09-04 | §8 추가 — 3단계 실행 파이프라인(topology 수집/gm-ID 사이징+레이아웃 수렴/결과물 산출)을 대표하는 5개 신규 파일 + top-level harness 함수 구조 확정, self-test를 `tests/test_<module>.py`로 분리하는 방침 확정 |
| 1.2 | 2026-09-04 | `stick_diagram.py`의 기존 인라인 self-test(8980~12923줄)도 `tests/test_stick_diagram.py`로 이관하는 것으로 §8.2/§8.8/Next Steps 수정(처음엔 재구조화 범위 밖으로 뒀으나 사용자 지시로 포함) |
| 2.0 | 2026-09-04 | `.ai/context.md` 세션6~44 전체 자산화(사고1~24, gm-id-methodology.md §13) 결과를 반영 — §1.4 신설(이 재설계가 세션38의 미완성 DC/AC Phase1/Phase2 아키텍처를 완성하는 작업임을 확인), §7.2(cascode/load 목적함수 구분 — gm/gds 최대화 vs gds 최소화, §13.7 반영), §7.3(전면 교체 설계를 취소하고 기존 `resolve_feed_vds()`/`_resolve_vertical_group()` 우선순위 체인·fixed-point worklist를 재사용하는 최소침습 설계로 개정, 신규 함수를 `_solve_diode_connected_vgs_fixed_point()` 하나로 축소), §8.3(gain-stage 자동분류에 5개 구조 신호 재사용 명시), §5(사고16 레이아웃 피드백 루프 위험 추가), §6.1/§1.3(Changed/Related Documents 갱신) |
| 2.1 | 2026-09-04 | 사용자 지적("각 소자의 전압/전류 관계가 물리적으로 맞는지 검증돼야 한다 — 이게 재설계 이유")을 반영해 §3.1에 요구사항 6(전체회로 물리 정합성 검증, ★최우선) 신설, §7.5 신설(`verify_node_voltage_consistency()`/`cross_check_with_spice()` — diode-connected만이 아니라 모든 소자의 KVL/KCL/VGS를 노드전압 재구성+SPICE 독립 교차검증으로 상시 검증하는 파이프라인 게이트, 이번 세션 diode-connected 버그를 실제로 찾아낸 방법론을 공식 함수로 승격), §8.4 harness 순서에 이 검증을 6~7단계로 삽입, §2.1/§4.1/Context Anchor SUCCESS/Executive Summary Solution을 이 요구사항이 diode-connected 수정을 포함하는 상위 목표임을 드러내도록 갱신 |
| 2.2 | 2026-09-04 | §7.6 신설(CMRR/PSRR/mismatch 결합 — `devices.tail` 서브롤 + `global_spec.constraints` 전역 선언 + cascode/load/tail의 L을 면적 오름차순으로 전수 스캔하는 outer-loop에 §13.5 `extra_feasible` 콜백 합성 재사용, gain→gm_id 역산의 결정론성은 각 L_combo 안에서 그대로 유지), §7.7 신설(L 변경 규칙 R1~R8 — 전기적 판정(§13.3 5신호)→LUT 격자(§7.7 자산)→전수 스캔 필요성(§13.7 M107 26배 악화)→행 폭 직접영향(`pitch(l)`)/W→n_fingers 간접영향→오일러·finger_w와의 직교성→수렴 루프 내부 실행), §7.1 스키마에 `devices.tail`/`global_spec.constraints` 반영, §2.1에 신규 함수 2개 추가. R7은 사용자 질의로 "branch(전기적, PMOS/NMOS 혼재 정상·L 상이 정상)와 row(물리적, kind 동질·finger_w 균일 강제)의 2축 구분"을 명시하도록 정정(파일럿 실측 M15 L=0.150µm vs M16 L=0.830µm 인용) |
| 2.3 | 2026-09-07 | "stage별 gain 배분과 compensation을 iterative하게 최적화할 필요가 있나"라는 사용자 질의에 대한 결론을 §7.8로 반영 — gm_id⊥ID 직교성(intrinsic gain=gm_id×V_A(L)은 ID에 무관, gm=gm_id×ID)으로 gain 배분과 compensation이 서로 다른 변수를 건드리므로 **전면 반복은 원리적으로 불필요**함을 파일럿 실측(stage1 4.626µA/stage2 24.702µA, 비율 5.34가 미러비로 조정 가능)으로 확인. 대신 `diagnose_sizing_dof()` 사전 진단을 신설해 목표 대비 자유도를 Stage 1 마지막에 판정하고, `overconstrained`면 반복을 아예 시작하지 않고 어느 목표끼리 충돌하는지 명시 보고(사고19의 착시적 수렴/순환 데드락 재발 방지). 제한적 반복은 `status=="ok"`인데 §7.6 L_combo가 실패할 때만 발동, 기생 커패시턴스 반복(`converge_with_parasitics()`)은 별개 축으로 무변경 유지 |
| 2.4 | 2026-09-07 | "stage별 물리적 gain 상한이 분명히 있다"는 사용자 지적을 파고들어 **배분의 진짜 대상이 gain이 아니라 VDD 헤드룸**임을 확인하고 §7.9 신설 — A_i,max를 정하는 5요소 중 VDS 예산만이 설계 자유도이고, 이 때문에 숨은 순환(A_max←VDS예산←헤드룸배분 / gain배분→gm_id→VDS확정→달성gain)이 존재함을 도출. 사고21 Phase 분리 + 문헌 §9.4의 'VDS 2회 반복'(45nm 실측 41.4→61.4dB, 면적 페널티 0)으로 순환을 끊는 3-Phase 구조와 **비용 순 중첩 루프**(outer 레이아웃 / mid L_combo / inner VDS) 확정. 근거로 sky130 LUT 직접 실측(VDS 0.2→1.2V: gain +329%/W −15% vs L 0.15→4µm: gain +1480%/W +1770%)을 §7.7 R4b로 추가하고, §7.8 직교분해 표의 V_A 축 누락(V_A(L)→V_A(L,VDS))을 보정. 부수 발견: min_vds=0.2V 기본값이 gm/gds를 2.4배 깎는 최악 지점. equal-margin은 폐기가 아니라 Phase 1 초기 seed로 이동. gain_budget_db 입력→출력 격하는 §7.4 원칙3 변경이라 보류(미확정 표기) |
| 2.5 | 2026-09-07 | §7.10 신설(초기 L 선택 기준) — sky130 LUT 직접 실측으로 (a) L 증가의 gain 수확체감(첫 2.3배가 3.91배를 주고 이후 11.6배 더 늘려도 4배만 추가), (b) fT의 L² 반비례 붕괴(2.3배에서 1/3.5, 6.7배에서 1/24)가 L 상한의 진짜 제약임, (c) 한계효율 knee가 kind/gm_id와 무관하게 항상 L≈2~3×L_min임을 확인 — 기존 `_L_ROLE_MULTIPLIERS`의 `mirror: 2.5×`가 '관례의 임의 중간값'이 아니라 실측 knee와 일치함이 사후 검증됨. 초기 L = knee에서 시작하되 fT 상한/mismatch 하한/LUT 격자로 clamp하고 role별로 방향 편향. 부수 반례: pmos 일부 구간에서 L↑인데 W·L↓(IDu 비단조) — '면적은 L에 단조'라는 가정이 깨지므로 knee 탐색도 전수 스캔으로 구현할 것 |
| **3.0** | 2026-09-07 | **설계 철학 전환(사용자 확정)** — "전면 재설계도 가능하다. 무조건 버그free와 효율성이 원칙이고, 다만 이전 사고로 알려진 문제는 재발하지 않아야 한다." §3.2를 3대 원칙(P1 버그free 최우선·전면 재설계 허용 / P2 효율성 / P3 기지 사고 재발 방지)으로 재작성하고 v2.x의 "함수 시그니처 무변경" 제약을 폐기. §3.3 신설 — 사고1~24를 실패 클래스 C1~C10으로 묶고 각각에 구조적 방지 장치와 담당 절을 지정(C1 물리 미검증 상수 / C2 암묵적 순서 의존 / C3 조용한 소실 / C4 role 과신 / C5 게이트 사각 / C6 underdetermined 반복 / C7 단일회로 검증 / C8 엔진 우회 / C9 중복 복붙 / C10 재계산 비효율). 이 원칙에 따라 제약이 비틀어 놓았던 절들을 바로잡음: §6.1을 개선대상/그대로/신규 3분류로 재작성, §7.3의 "먼저 기입하면 우선순위①이 지켜준다"는 순서 의존 우회를 폐기하고 `resolve_feed_vds()`에 **티어① gate==drain → 고정점 solver**를 명시(C2 근본 제거), §7.9의 가중 헤드룸 배분을 위해 `cascode_fn(entry)`→`headroom_fn(entry, ctx)` 시그니처 확장 + 균등분배 폐기(C1/C4, v2.x에서는 무변경 선언과 모순돼 구현 불가였음), §7.10의 `_L_ROLE_MULTIPLIERS` 상수를 `measure_L_knee()` 실측 호출로 대체(공정 이식성) + `search_gm_id_and_L_for_role()`로 L축 내부화(C10). §4.1 DoD에 C1~C10 방지장치 확인과 4개 토폴로지 전수 실행(C7) 항목 추가 |
| 3.1 | 2026-09-07 | **`gain_budget_db`를 입력에서 출력으로 격하(사용자 결정)** — 사용자는 총 gain 목표(`global_spec.constraints`의 `gain_db>=X`)만 주고, stage별 배분은 §7.9 Phase 2가 `A_i,max` 실측 + root current 1-D 단조 해찾기로 유도해 instance.json/리포트에 기록한다. §7.9에 그 유도 절차(gm_i←compensation / V_A_i←L_combo+VDS예산 / ID_i=k_i×ID_root / Σ20log10(...)=gain_target 해찾기 / 유도된 배분으로 §7.2 실행)를 확정본으로 명시. §7.1 스키마에서 `gain_budget_db`·`gain_allocation`·`gain_allocation_check` 제거하고 `gain_budget_db_override`(기본 null, 논문 재현용 예외)만 남김. §3.1 요구사항5와 §7.4 원칙3(둘 다 '배분은 탐색/사용자 지정으로 남긴다'였음)을 개정하고, 사고4와의 관계를 명시 — 사고4의 본질은 '값을 논문에서 찾지 말고 회로에서 도출하라'이고 v3.1은 그 도출을 자유 탐색에서 물리 실측 기반 결정론으로 좁힌 것이라 충돌하지 않음. 문헌 정본(§6.4)이 gain을 스펙이 아니라 등고선으로 다루는 것과도 일치. §2.2의 '배분 탐색 고도화는 범위 밖' 항목은 In Scope로 이동 |
| 3.2 | 2026-09-07 | **문헌 정합성 검증에서 발견한 갭 해소** — 웹검색(Murmann/Boser/Silveira-Flandre-Jespers 등)과 프로젝트 문헌 정본(§6.4)을 v3.1과 대조한 결과, v3.1의 `ID_i=k_i×ID_root` 1-D 해찾기가 **Jespers의 2D sizing space `(gm/ID₁, gm/ID₂)`를 `k_i` 고정 단면의 1D 선으로 축소**하고 있었음을 확인(k_i는 바이어스 미러비로 조정 가능한 값이라 곧 두 번째 축이다). 해소는 `k_i`를 탐색 축에 추가하는 게 아니라 **변수 자체를 `gm_id_i`로 바꾸는 재정식화**로 했다 — `ID_i=gm_i/gm_id_i`이고 `k_i`는 그 전류를 실현하는 파생값이므로 theta 폭발 없이 N-D 공간 전체를 덮는다. 해법은 탐색이 아니라 해석해+활성제약(active set): min-power면 각 stage가 자기 상한(gm_id_phys/W_max/fT_min)까지 독립 최대화(gain과 power가 같은 방향이라 결합 없음), area가 목적에 들어가면 gain 등식이 binding해져 KKT 정류조건이 **비활성 stage끼리 ID_i=const**를 준다(2단 대수 검증). v3.1의 1-D 해찾기는 '모든 stage 비활성' 특수 케이스로 흡수. 파일럿의 stage2/stage1 전류비 5.34가 자유 선택이 아니라 class-AB 구동 하한이라는 **활성 제약의 결과**임도 설명됨. §7.1 objective에 area/가중합 옵션을 열고, §7.8 DOF 진단의 전류 축 계수법도 gm_id_i 기준으로 정정. 정직한 한계: 순수 power 최소화에서는 배분이 축퇴(자유도 없음)되고, 진짜 배분 문제는 area가 목적에 들어갈 때만 나타남 |
| 3.3 | 2026-09-07 | **면적 제약형 채택(사용자 선택) — v3.2가 남긴 배분 축퇴 문제 해소**. LUT 실측으로 전력(ID=gm/gm_id)과 면적(W·L)이 gm_id 축에서 **정확히 반대 방향**임을 확인(gm=75µS 고정, L=0.35µm: gm_id 5→26에서 전력 15→2.9µA로 감소하는 동안 면적은 0.13→509µm²로 **4000배 폭발**, gain은 28→77.6으로 포화 — gm_id 22→26 구간은 gain +0.05dB에 면적 147배). 따라서 목적함수는 **전력 최소화 하나**로 두고 **면적은 `global_spec.constraints`의 `area_um2` 상한**으로 건다(가중합 α:β는 가중치를 사람이 지어내야 해 결정론이 깨지므로 기본에서 제외). 이러면 전력 최소화가 gm_id를 weak inversion으로 밀 때 면적 제약이 먼저 걸리고, KKT 정류조건 `gm_i/gm_id_i² = μ·∂Area_i/∂gm_id_i`가 **"면적 1단위당 전력을 가장 많이 아끼는 stage부터 배분"**이라는 규칙을 주어 **배분이 유일하게 결정**된다 — 면적 예산이 교환비 μ를 정하므로 임의 가중치가 필요 없다. 남는 자유 입력은 면적 예산 하나인데 이는 전력·gain 목표와 같은 정상적 설계 스펙이다. 문헌 정본 §6.4의 '등전력·등면적·등이득 contour 겹쳐 절충점 선택'을 결정론적으로 자동화한 구조. 면적 예산 미선언 시 W_max만 상한이 되어 축퇴가 재발하므로 선언을 권장으로 명시 |
| 3.4 | 2026-09-07 | **면적 예산 미선언 시 Pareto front fallback 신설(사용자 확정)** — 예산이 없으면 배분이 축퇴되는데 엔진이 예산을 지어내서는 안 되므로, `sweep_area_power_pareto()`가 전력-면적 Pareto front를 계산해 제시하고 **정지**한다(자동 선택 금지, §3.2 P1). 스윕 구간의 양끝을 물리로 고정해 임의값을 없앰: A_min은 gain_target을 겨우 만족하는 최소 면적, A_max는 d전력/d면적이 임계 이하로 떨어지는 수확체감 지점(실측 근거: gm_id 22→26이 전력 −15%에 면적 147배로 이미 A_max 너머). 로그 등간격 12점에서 KKT+active-set 해법을 각각 1회 실행하고 Pareto 비지배 점만 남겨 (면적, 전력, gain 여유, stage별 유도 배분, 활성 제약)을 리포트한다 — 해석해라 점당 비용이 작고 LUT 스캔 캐시를 공유(P2). 사람이 고른 점이 `area_um2` 제약으로 기록되면 그 다음부터는 완전 결정론적으로 동작하므로, 이 fallback은 결정론을 포기하는 경로가 아니라 **빠진 스펙 하나를 사람에게 받아오는 경로**다. 이로써 가중합(α:β) 방식은 불필요해졌다. §8.4 harness에 0단계 분기, §2.1에 신규 함수 등록 |
| **4.0** | 2026-09-07 | **4개 관점 독립 검토(회로물리/구현가능성/문서정합성/토폴로지 일반성) 반영 + 코드 선행조치 3건 완료**. 사용자 결정 3건: ① `gm_i` 인과 방향을 **"compensation이 (Cc,Rz,gm_1..gm_N)을 먼저 한 번에 결정"**으로 통일하고 §3.1 req4·§7.4 원칙2를 폐기 — v3.2가 §7.9만 뒤집고 이 둘을 안 고쳐 문서가 두 갈래였다(둘은 양립 불가: `min Σ gm_i/gm_id_i`는 `gm_i`가 상수여야 well-posed). "gain-budget-first"의 의미도 "gain이 gm을 정한다"가 아니라 "단별 gain 예산을 엔진이 유도해 **산출**한다"로 확정. 기생 결합 `∂gm_i/∂gm_id_i ≠ 0`을 KKT 밖에 두던 것도 정정(v2.4의 V_A 축 누락과 같은 클래스). ② **gain 제약을 폐형식에서 `compute_metric()` 위임으로 전환** — 4개 토폴로지가 네 가지 다른 gain metric(`gain_stages_sum`/`folded_cascode_gain_db`/`nmcnr_gain_db`/`smallsignal_gain_db`)을 쓰므로 폐형식 `Σ20log10(gm_id·V_A)`으로는 §4.1 DoD의 4개 전수 실행이 **원리적으로 불가능**했고, `_METRICS_REGISTRY` 위임이라는 이 프로젝트의 circuit-agnostic 규약을 §7.9가 깨고 있었다. 부하 로딩 미반영(2단 −12dB 계통 낙관)과 `V_A`가 `gm_id`와 독립이 아니라는 문제도 함께 해소. ③ **theta 폐기를 "자유 탐색 변수"로 축소** — `A_signed`/`C`/`metric_stage_budget`/servo `B`는 값이 아니라 **구조 선언**이라 전면 폐기하면 CMFB·class-AB 배터리·bias 체인 정보가 소실된다(세션33 회귀와 같은 클래스). `structural_declarations`/`feedback_loops`/`metrics` 블록을 스키마에 신설·복원하고 noise(`flicker_plus_thermal_sum`, **엔진에 이미 등록돼 있는데 계획이 떨어뜨린 것**)를 제약으로 승격. 코드 선행조치: (a) 헤드룸 2중 중첩 클로저 6개(401줄)를 모듈 레벨 `_hr_*`로 추출해 `resolve_headroom()` harness를 비로소 가능하게 함(본문 무변경, self-test stdout 바이트 동일), (b) self-test 회귀 기준선 신설 — 기존에 지목된 로그는 stick_diagram 것이 없고 `.gitignore`로 **git 추적조차 안 됐다**; 캡처 중 stick_diagram 출력 7줄이 실행마다 달라지는 것을 발견해 결정론화, (c) 소신호 MNA를 `numpy.linalg.solve`로 전환(노드 51개 6.1x, 상대편차 1e-13) + numpy 지연 import 7곳 통합. 미반영 지적 전량을 **§10 신설**로 기록(A1~A10 물리, B1~B13 구현, G1~G8 일반성, C 잔여) — 특히 B1(티어①이 실제 버그 경로를 안 지남, 호출자 2곳뿐)과 A10(v3.3 근거 실측치가 `V_A` 58배 상승을 함의해 물리적으로 불가능)은 다음 결정 대상. 부수 정정: §1.5 끊어진 참조 4곳→§3.2 P1, `schema_version` 3.0→4.0, "무변경 재사용" 잔재 2곳 |
| 4.1 | 2026-09-07 | **A10 조사 완료 — 우려 기각, 대신 A11 발견**. v3.3이 면적 제약형 채택 근거로 든 실측(`gm=75µS`, `L=0.35µm`, gm_id 5→26)을 sky130 LUT로 직접 재현한 결과 **"28→77.6"은 dB가 아니라 선형 `gm/gds` 비**였다(dB로는 28.98→37.80; 같은 문장의 "+0.05dB"는 37.75→37.80 증분이라 둘 다 사실이나 한 문장에 단위 없이 섞여 오독을 유발했다). `V_A` 5.62→2.98V로 정상이고, 면적 0.127→509.32µm²(4000배)도 아티팩트가 아니라 전류밀도 `IDu`가 2.03e-6→1.98e-9 A/µm로 1000배 떨어지는 deep weak inversion의 결과다 -- **v3.3 논거 그대로 유지**. §7.9 표에 단위를 명시했다. 부수로 결정2(metric 위임)의 근거를 정량화: 분리형 `gain=gm_id×V_A`는 gm_id 5→26에서 실제 37.80dB를 43.30dB로 **5.50dB 과대평가**한다(`V_A`가 1.88배 감소하기 때문). **새 발견 A11**: `gm/gds`가 `gm_id`에 단조가 아니다 -- VDS 0.6/0.9/1.2/1.5에서 감소 구간이 6/8/11/12개이고 최댓값이 gm_id≈20.5/20.0/18.0/18.0에 있다(VDS=0.4에서만 단조). 정점 위는 gain·면적 둘 다 나빠지고 전력만 좋아지는 **지배당한 영역**이라 (i) "gm_id를 올리면 gain이 오른다"는 KKT 전제가 거짓이 되고 (ii) 탐색 상한을 면적 예산에만 맡기면 안 되며 (iii) `V_A(VDS)`·`IDu(L)` 비단조와 합쳐 **(gm_id,L,VDS) 공간이 비볼록**이므로 v3.3의 "배분이 유일하게 결정된다"는 근거가 없다. §10.2에 A11로 등록 |
| **4.2** | 2026-09-07 | **A11 해소 — §7.9 해법을 KKT 한계비 탐욕에서 분리형 DP로 교체**. 사용자 질문("해석해가 아니면 탐색을 해야 하는 문제로 바뀌는 것 아닌가")에 답하려고 세 방법을 sky130 LUT로 직접 돌려 비교했다(2-stage, gm_id 격자 0.25 간격 87점). **v3.3이 규정한 KKT 한계비 탐욕이 72 시나리오 중 27건(37.5%)에서 전수 최적과 어긋났고, 그 중 8건은 feasible 해가 존재하는데도 gain 미달 해를 반환했다** — 탐욕 규칙이 면적 예산만 보고 gain 제약을 아예 보지 않기 때문이다(단순 열등이 아니라 **스펙 위반 해를 내놓는 결함**). 대신 각 stage의 (전력·면적·gain)이 자기 `gm_id_i`에만 의존한다는 **분리성**을 이용한 자원배분 DP를 쓰면 기울기를 전혀 쓰지 않으므로 비볼록이 무관해진다 — 탐욕이 틀린 9개 케이스에서 전수와 **9/9 일치**했고 비용도 N=3에서 0.043s(전수 0.98s), **N=4에서 0.294s**(전수 5,729만 조합으로 비현실적)로 오히려 싸다. 따라서 **탐색 문제로 바뀌는 것이 아니라 '정확한 이산 최적화'가 된다**: 같은 입력→같은 답, 임의 가중치·초기값·시드 없음, 국소최적 구조적 부재, 작은 N에서 전수 대조로 최적성 확인 가능 — 사고4가 막았던 '탐색'과는 성질이 다르다. 잃은 것은 닫힌 식 하나뿐이고 남는 근사는 격자 해상도 하나인데 그건 숨은 오차가 아니라 리포트에 찍는 값이다. v3.3의 "배분이 **유일하게** 결정된다"는 표현을 철회하고 "주어진 격자 위에서 전역 최적 + 활성 제약 집합 보고"로 대체. 부수: Pareto front(v3.4)도 DP가 면적 bin별 비지배 집합을 이미 들고 있어 **한 번의 전파로** 나오므로 12점을 따로 풀 필요가 없어졌다. 프로토타입을 `tests/probe_allocation_solvers.py`로 자산화 |
| **4.3** | 2026-09-07 | **B1 해소 — §7.3 diode 티어의 자리를 실측으로 재지정**. v3.0은 티어①을 `resolve_feed_vds()` 안에 넣기로 했는데, 파일럿 실주행(SLSQP)에 monkeypatch 계측을 붙여 세어 보니 **그 자리로는 diode 소자를 하나도 못 덮는다**: `resolve_feed_vds()`가 정하는 소자는 51개 중 **4개(diode 0개)**뿐이고, 최대 경로는 `allocate_stack_headroom()`(**28개**, diode 12개)이며 M18_bg/M66/M36a/M36b(최악 오차 +1.020V)는 그 함수 근처에도 가지 않는다. **사고19가 기록한 실패("resolve_feed_vds()를 확장했으나 분기가 애초에 그 계산을 안 타서 값이 안 바뀌어 전부 되돌렸다")의 재현**이다. 정적 전수로 vds 기입 지점이 **7곳**임도 확인했다(그중 `resolve_feed_vds()` 경유는 2곳). 부수 확인: `headroom_role`은 diode 여부를 전혀 반영하지 않는다 — diode 16개의 role이 cascode 11/mirror 3/diode_reference 1/voltage_divider 2로 흩어져 있어 **`diode_reference` 라벨은 16개 중 1개에만** 붙어 있고, `vds=0.2`는 `min_vds_by_role["cascode"]`가 흘러나온 값이라 M2b(diode 아님, 필요 1.398V)와 M11a(diode, 필요 0.871V)가 똑같이 0.2를 받는다(C4 실물). **확정 설계**: diode를 `vds_match_vgs_of`의 **자기참조 특수 케이스**로 보고 이미 물리적으로 옳게 계산하는 기존 pre-pass(4729행)를 자기참조 고정점(bisection)까지 확장한다 — 확정값은 unresolved에서 빠져 예산에서 차감되므로 자리가 정확하다. 순서 운에 기대지 않도록 7개 기입 지점을 **`set_device_vds()` 단일 setter**로 수렴시키고(diode면 고정점 해와 불일치 시 즉시 실패, `_vds_source` 태그 기록으로 B13 추적성 동시 해결), 원시 대입 잔존을 grep 테스트로 강제한다. 계측 스크립트를 `tests/probe_vds_assignment_paths.py`로 자산화 |
| **4.4** | 2026-09-07 | **B2 해소 — metric 3티어 분류로 게이트 구조 재작성**. §2.1이 `make_cmrr_psrr_feasibility_check()`를 `make_matching_feasibility_check()`와 "동일 패턴"으로 만들자고 했으나 **원리적으로 불가능**함을 실측 확증했다(`KeyError: 'M6' 소자가 ctx.sized에 없다`). mismatch가 되는 이유는 닫힌 식(W,L만 필요)이고, cmrr/psrr은 `_full_circuit_devices()`가 **전 소자**를 요구하는데 L_combo 루프는 stage 하나를 사이징하는 중이기 때문이다. 파일럿 13개 metric 전수 분류: **T1 stage-local**(power/area/mismatch/noise, 0.002~0.006ms) / **T2 stage-분해가능**(`gain_stages_sum`) / **T3 기약 전역**(cmrr/psrr/전체회로 gain/classab/rail level/rz, 0.15~0.29ms). 게이트도 3티어로 재작성 — T1/T2만 `extra_feasible`로 stage 안에서, T3는 전 소자 사이징 완료 후 `check_global_gates()`로 1회, L_combo는 바깥 재시도 루프. **부수 소득**: `gain_stages_sum`이 정확히 분해됨을 실측(stage별 합 56.9842dB = 전체 56.9842dB, 차이 0.00e+00)해 §7.9 DP가 대리 함수가 아니라 **진짜 metric을 분해해서** 쓸 수 있음이 확정됐다 — 반대로 나머지 3개 토폴로지는 gain이 T3라 DP가 LUT 대리를 쓰고 판정 권한은 전역 게이트에 있다는 이원성을 명시했다. 비용은 문제가 아니다: T3 게이트 1회 **0.72ms**(P-c numpy MNA 전환 덕분), 343 combo에 0.25초 / 68,921 combo에도 50초. 캐시 히트를 피하려고 gm/gds를 매번 흔들어 쟀다(캐시와 차이 0.32 vs 0.34ms로 유의하지 않음). 부수 정정: noise metric은 처음에 실패했는데 프로브가 `SID_1F`를 안 넘긴 탓이었고, 넘기니 stage-local로 정상 동작(T1) |
| **4.5** | 2026-09-08 | **B11 해소 — C1~C10을 선언에서 테스트 목록으로 교체**. v3.0의 C 표는 방지 장치를 문장으로만 적어두었고, 실측해 보니 다섯 항목이 **문서 전체에서 그 표 안에만 한 번씩** 등장하는 빈 약속이었다(`review_needed` 2회 중 1회가 표 자신, "전역 유일성"/"connectivity에서 유도" 각 1회). ★절대원칙(만들면 반드시 배선)에 따라 각 행에 **"이게 없으면 방지 장치가 없는 것"이라 말할 수 있는 강제 테스트**를 지정하고, 담당 절 열은 제거했다(C7이 지목한 §5는 "파일럿 1개만"이라 **정반대** 내용이었고 C10이 지목한 §7.6엔 캐시 서술이 아예 없었다 — 어긋남이 반복되던 열이다). **지금 돌리면 실패하는 것을 실패한다고 적었다**: C1은 diode 16/16이 tol 초과(최대 1.020V), C4는 같은 소자가 role만 바꿔도 vds가 `cascode`→0.200/`mirror`→0.300/라벨없음→0.600으로 갈리며(물리 `gate==drain`은 보지 않는다), C5는 게이트류 19개 중 **4개만** "검사하지 않는 것"을 docstring에 명시한다. 가장 강한 세 테스트는 실패를 직접 재현하는 형태다 — `test_role_label_removal_invariance`(role 라벨을 전부 제거해도 결과가 같아야 한다), `test_order_shuffle_invariance`(처리 순서를 셔플해도 결과가 같아야 한다), `test_cache_key_covers_mutable_state`(`ctx.sized`만 바꿔도 캐시가 옛 값을 주면 안 된다). 부수 확인: 메모리에 "만들고 배선 안 함" 사례로 남아 있던 `check_stick_diagram_coverage()`/`find_euler_repair_options()`/`validate_theta_declaration_order()`는 **현재 전부 프로덕션 경로에 배선돼 있다**(각각 프로덕션 호출 9/2/2곳) — 그 우려는 이미 해소된 상태다. §4.1 DoD를 "10개 테스트 전원 PASS"로 교체 |
| **4.6** | 2026-09-08 | **B4 해소 — 실행시간 예산 신설**. v4.5까지 계획에 예산 항목 자체가 없어 §7.6 L_combo 전수 스캔 × §7.9 중첩 루프의 곱을 아무도 세지 않았다. 직접 측정: `_build_theta_evaluator()` 69ms(1회성), **`presolve_warm_start()` 16.5s**(1회성이나 크다), **전체 평가 1회 274.5ms**, `find_optimal_sizing()` 1회 3.15ms, 전역 게이트 0.72ms, IDu 스캔 캐시 **5.0배**(59.3→11.9ms, C10이 실물로 작동 중). **핵심 교정: L_combo 단위 비용은 stage 사이징이 아니라 전체 평가다** — B2에서 확인했듯 전역 게이트가 51소자 전부를 요구하므로, "gain stage 2개만"으로 세면 6.3ms vs 실제 274.5ms로 **44배** 틀린다. L 자유도는 3개(`L_cascode`/`L_stage2out_p`/`L_stage2out_n`, bounds 전부 `[0.15,1.0]µm`). 기본 정책 **bounds 내 LUT 앵커 4개(4³=64 combo)**에서 전수 17.6s, 중첩(레이아웃 5회×VDS 2회) 포함 **2.9분** — 감당 가능. LUT 전체 앵커 7개면 15.7분, 0.05µm 등간격 11점이면 61분, **densify 41점이면 53시간**이라 densify는 기본 금지하고 필요 시 2단계 정밀화를 쓰되 `IDu(L)` 비단조(§7.10) 때문에 전역 최적을 놓칠 수 있는 **근사**임을 리포트에 찍는다. `presolve_warm_start()`는 L_combo 루프 **밖에서 1회** 규약(안에 들어가면 여기서만 17.6분 추가). infeasible combo는 정상이며(실측 12개 중 2개) 세어 보고하고 계속 진행한다. 예산이 감당 가능해진 큰 요인은 **v4.2의 DP가 Pareto 12점 스윕을 없앤 것**이다. **부수 정정: §7.7 R3의 "L 앵커 4개"는 stale이 아니었다** — LUT 전체는 7개이나 파일럿 theta bounds 안이 4개라 둘 다 맞고 문맥이 달랐을 뿐이라, 검토자 지적을 그대로 받았으면 잘못 고쳤을 것이다. 두 숫자의 문맥을 R3에 명시했다. DoD에 "파일럿 1회 wall-clock ≤ 5분" 신설 |
| **4.7** | 2026-09-08 | **L 탐색을 knee 창 + 경계 검사로 확정 + 단위 불일치(A12) 발견**. "LUT 전체를 훑지 말고 knee 근방만 최소 탐색해야 하지 않나"라는 지적을 받아 LUT 전 앵커 7³=343 combo를 전수로 돌렸다. **면적 제약이 걸리느냐에 따라 답이 뒤집힌다**: 무제약/≤500µm²에서는 전수 최적이 `[0.5, 0.15, **1.5**]`µm로 knee 창(≤0.5µm) **밖**이고 창으로 좁히면 +1.24% 손해지만, **≤200µm²(v3.3 정신)에서는 전수 최적이 `[0.5, 0.15, 0.5]`로 창 안에 들어와 손해가 0.00%**다. 상위 10개 L 분포도 무제약 `{0.15:10, 1.5:7, 4.0:7}`에서 ≤200µm² `{0.15:7, **0.35:9**, 0.5:6, 1.0:6, 1.5:2}`로 이동해 **0.35µm가 최다**가 되는데, 이는 §7.10이 예측한 knee(0.30~0.45µm) 한가운데라 **knee 이론이 면적 제약 하에서 실측 확증**됐다. 부수 관찰: 전력 스프레드는 6.7%(454~484µA)인데 면적 스프레드는 **40배**(47~1902µm²) — **L 선택은 전력이 아니라 면적을 정한다**. 확정 정책: `measure_L_knee()` 결과를 포함하는 앵커 창(파일럿 3개, 27 combo)에서 전수 스캔하고, 선택된 L이 **창 가장자리면 한 칸 넓혀 재실행**(이미 평가한 combo는 캐시 재사용). 가정이 아니라 **사후 검증**이라 §7.7 R4와 양립한다 — 창이 좁았으면 스스로 드러난다. 비용 7.4s / 중첩 포함 **1.2분**(전수 대비 12.7배 절감). **★ 부수 발견 A12(시급)**: `power_uA`가 실제로는 A를, `area_um2`가 m²를 반환한다(파일럿에서 0.000243323 vs 직접 합산 243.32µA, 1.17156e-10 vs 117.16µm² — 정확히 10⁶·10¹²배). 4개 토폴로지 어디에도 area 제약이 선언돼 있지 않아 드러나지 않았는데, v3.3/v3.4가 `area_um2 <= 2000`을 핵심 제약으로 도입하므로 그대로 두면 **2000µm² 의도가 2000 m²와 비교돼 제약이 사라진다** — v3.3의 면적 상한 논거, v4.2 DP의 면적 bin, v3.4 Pareto 구간이 전부 무력화된다. §10.2에 A12로 등록(공유 엔진 동작 변경이라 사용자 승인 대기) |
| **4.8** | 2026-09-08 | **A4 해소 — `mirror_ratio_error` metric 신설**. "VDS 재배분이 매칭 쌍을 깬다"는 지적을 실측하니 **절반은 이미 해결돼 있었다**: `matching_pairs`가 `offset`(공유 tail KCL이 강제하는 진짜 대칭)/`ratio`(전류미러)로 갈려 있고, offset 3쌍은 헤드룸 해석기가 `_hr_vfind()` union으로 VDS를 이미 같게 강제해 **ΔVDS=0**이다. 진짜 gap은 `ratio` 쌍 — 18쌍 중 3쌍이 불일치이고 **M18_bg/M60이 ΔVDS=1.300V, V_A=2.04V로 ΔI/I=63.6%**(미러비가 설계값의 1.6배)인데 **아무 metric도 이를 보고하지 않았다**. `pelgrom_mismatch`는 `estimate_mismatch_sigma(vth0_slope, W, L)` — vds도 V_A도 인자로 안 받아 **랜덤** 성분만 보므로 **계통** 오차는 구조적으로 시야 밖이다. B1(diode 고정점)을 고치면 M18_bg vds가 0.200→0.989V로 잡히지만 M18_bg/M60은 여전히 25.0%, M10/M12는 diode가 아니라 15.7%가 그대로 남아 **독립 문제**임이 확인됐다. **처리 방향 정정**: 검토자가 제안한 "VDS 매칭 제약(R2′)"은 미러에 물리적으로 틀리다 — 레퍼런스(diode, Vgs 고정)와 출력(부하 노드 전압)의 VDS가 다른 것이 회로의 본질이라 같게 강제하면 회로가 성립하지 않는다. 그래서 **제약이 아니라 비용**으로 둔다: `_metric_mirror_ratio_error()` 신설(1차 CLM `ΔI/I = |ΔVDS|/V_A`, `aggregate` max|rss, unit `%`), `_METRICS_REGISTRY`/`_METRIC_UNITS`/`_UNIT_SCALES`/이름접미사(`_pct`) 4곳 등록, 파일럿 topology.json에 선언(선언된 metric은 전부 계산·보고되므로 이것으로 배선 완료). 실측 max **63.606%** / rss 71.912%. docstring에 "검사하지 않는 것" 4가지 명시(C5 관례). **상한 제약은 아직 걸지 않았다** — 4개 회로에서 먼저 재보고 값을 정한다(값을 지어내지 않는다). 회귀: 두 self-test stdout 기준선과 바이트 동일 |
| **4.9** | 2026-09-08 | **A3/A5 조사 — 둘 다 지적과 실제가 달랐다**. **A3**: "bias 전류가 목적함수에서 빠졌다"는 **사실이 아니다** — `sum_current`는 `devices` 미선언 시 `ctx.sized` 전체를 더하고 gain-stage 밖 39소자(107.50µA)가 이미 들어 있다. 진짜 결함은 **직렬 중복 계상**: 전 소자 ID 합 243.32µA vs VDD 레일 유입 86.27µA로 **2.82배**이고, 배수가 branch마다 달라(diffpair 8소자 vs battery 3소자) **"소자 수"라는 설계 무관 가중치**가 전력에 붙는다. `_metric_supply_current()` 신설(connectivity로만 판정: PMOS.source 또는 NMOS.drain이 공급 레일), `supply_current_uA`로 선언해 나란히 보고. **objective 교체는 탐색 결과를 바꾸는 설계 결정이라 하지 않았다.** 부수 관찰: vdd 유입 86.27µA vs gnd 유출 88.93µA로 **3.1% 어긋난다** — B8(KCL 잔차 검증 부재)의 실물 증거다. **A5**: gm_id가 천장으로 밀린다는 구체 우려는 **현 파일럿에서 미발생**(최대 24.68 < 350K 천장 27.6, 어느 천장도 초과 0개). 대신 더 근본적인 것 — 엔진에 온도 개념이 noise metric 하나뿐이고 사이징엔 없으며, **LUT npz에 코너/온도가 아예 기록돼 있지 않다**. 생성기는 `__tt.pm3.spice`(TT)를 include하고 `.temp`를 안 넣어 ngspice 기본 27°C인데 그게 파일에 안 남는다. `sky130_lut_sweep.py`의 `savez`에 `corner="tt", temp_c=27.0`을 기록하도록 고치고(지어낸 값이 아니라 그 스크립트가 실제로 쓰는 값), `lut_conditions_from_npz()`가 기록 없으면 **조용히 300K를 가정하지 않고** `recorded=False`와 사유를 돌려주게 했다(§3.2 P1). 기존 8MB npz는 재저장하지 않았다. 회귀: 두 self-test 기준선과 바이트 동일 |
| **4.10** | 2026-09-08 | **B7/B8/B9 묶음 조사 + `kcl_residual` metric 신설**. **B7**: 네 지적 중 셋을 코드로 확인했으나 **set 순회 의존은 이 회로에서 실현되지 않았다**(순회 순서를 뒤집어도 노드값 32개 전부 동일) — 잠재 위험과 실현된 결함을 구분해 적었다. 반대로 **다중도달 미검사는 실물 위반을 낳는다**: 21건 중 **4건이 243.5mV 불일치**(Vop1/Vom1에 두 경로가 0.6565 vs 0.9000으로 도달)로, 프로토타입이 `elif`에서 검사 없이 discard하는 바로 그 자리다. **B8**: 내부 노드 30개 중 3개가 잔차 >1nA, **Vx −3.96µA**, 레일 vdd/gnd **2.66µA** 불일치. `_metric_kcl_residual()` 신설 — NMOS drain→source / PMOS source→drain 부호규약을 명시하고 `ideal_sources.value_amp`를 함께 세되 `value_amp=null`이면 **값을 지어내지 않고 그 노드를 skip**하며, `exclude_nets`는 빼는 이유를 선언에 적게 했다(조용한 면제 금지). 실측 **3.9601µA**. **B9**: "39개가 vs=0이라 틀렸다"는 부정확 — **24개는 source가 레일이라 vs=0이 옳다**. 진짜 문제는 일관성이다: 레일이 아닌데 vs=0인 소자 **15개**, **반대로 레일인데 vs≠0인 소자 4개**(M60/M61/M38/M68). vs의 정의와 후자의 의도 여부는 회로 해석이라 **공동분석으로 남긴다**. **★ 새 발견 B14**: `ideal_sources.value_amp`(Iref 1.2µA, 주석에 "사용자가 논문 원문에서 직접 확인")가 **엔진에서 전혀 소비되지 않는다** — `Iref` 문자열은 topology.json에 선언 1회뿐이고 바이어스 전류는 theta `r_biasgen`이 자유 탐색으로 정해 실제 0.6484µA(**1.851배** 차이). `settling_time_ns`와 같은 "선언만 있고 안 읽는 필드" 클래스지만 **사용자 확인 값이라 더 무겁다** — 공동분석 필요. 회귀: 두 self-test 기준선과 바이트 동일 |
| **4.11** | 2026-09-08 | **`vs` 정의 확정(B9 원인 규명) + Iref 자유탐색 확정(B14 해소)**. **B9**: `vs`의 정의를 LUT 생성 넷리스트에서 확인했다 — `xdut d g 0 b`로 source가 항상 노드 0이고 VS는 벌크 전압(`vb_dc = vb_sign·VS·(−1)`)을 움직이므로 **VS 축은 소스-벌크 역바이어스 |V_SB|**다. 벌크가 레일에 묶이면 NMOS는 `V_source`, PMOS는 `vdd − V_source`가 되어 사용자가 말한 "소스 전압"과 NMOS에서 일치한다. 이 정의로 51소자 검산 → **25개 불일치**: ① 비레일 source인데 vs=0(최대 −1.3000V, M37a/M37b) ② 레일인데 vs≠0(M60/M61/M38/M68) ③ **M9a/M9b·M18a/M18b 값이 정확히 교환**. **원인 확정**: `other_entry.setdefault("vs", ref_vds)`가 kind를 보지 않는다 — `ref_vds`는 `budget_reference_device`의 VDS 합(vss 기준)이라 NMOS엔 맞고 PMOS엔 틀리다. M9a(PMOS, ref=M10)가 0.6565(=V(Vop1), NMOS용 값)를, M9b(NMOS, ref=M8)가 0.8060(=vdd−V(Vg25), PMOS용 값)을 받아 정확히 뒤바뀐다. 더해서 topology의 `device_roles[*].vs`(선언 0.0)와 이 전파가 경쟁해 순서 의존까지 있다 — C1+C4+C2가 한 줄에 겹쳤다. **수정은 재사이징을 유발하므로 승인 대기**. **B14**: 사용자 확정 — `value_amp`는 **참고값**이고 실제 전류는 `r_biasgen` 자유 탐색이 **전력 최적으로** 정한다. 1.2µA(논문) vs 0.6484µA(사이징)의 1.851배 차이는 **의도된 것**이다. topology의 Iref에 `_value_amp_status`로 명시하고, `kcl_residual`이 이상전원 노드를 제외하도록 고쳐 이 괴리를 KCL 위반으로 오보고하지 않게 했다(`count_ideal_sources=true`로 반대 선택 가능). 회귀: self-test 기준선과 바이트 동일 |
| **4.12** | 2026-09-08 | **`ideal_sources.value_amp` 정책 확정(사용자 지시)**: ~~참고값~~ → **null이면 자유탐색, 값이 있으면 그 값을 실제 전류로 쓴다**. 파일럿 Iref(1.2µA 선언)는 고정 대상이 되고 `r_biasgen`의 자유도가 줄어든다. `_metric_kcl_residual()`을 그 규약에 맞게 되돌렸다 — `value_amp=null`이면 그 노드를 제외(값을 지어내지 않는다), 값이 있으면 실제 전류로 세어 **괴리를 드러낸다**. topology.json의 Iref `_value_amp_status`도 새 규약으로 갱신. 엔진이 아직 `value_amp`를 소비하지 않으므로 B1+vs 구현 시 `seed_currents` 경로로 배선한다 |
| **4.13** | 2026-09-08 | **B1 3~4단계 구현 + 배선 전 스택 feasibility 사전계산**. `is_diode_connected()`(connectivity만 본다 — 파일럿 diode 16개의 `headroom_role`이 cascode 10/mirror 3/voltage_divider 2/diode_reference 1로 흩어져 있어 role로 판정하면 **15개를 놓친다**), `solve_diode_connected_vds()`(A7 권고대로 대입 반복이 아니라 **bisection**, 브래킷도 지어내지 않고 **LUT VDS 격자에서 부호가 갈리는 구간**을 찾는다 — 처음에 `[min,max]`로 잡았더니 VDS=0에서 소자가 꺼져 gm_id 조회가 범위 밖이라 **16개 전부 실패**했다), `set_device_vds()`(vds 기입의 유일한 경로, diode면 자기일관해와 불일치 시 즉시 실패, `_vds_source` 태그로 B13 추적성 동시 해결) 신설. 실측: **16/16 해 찾음**, 검산 `g(v*)`~1e-7, 현재 배정과 **|오차| 평균 0.548V·최대 1.061V**(M36a/b 0.300→1.361V). **배선 전 사전계산**: 22개 스택 중 **7개가 예산 초과**(최대 1.346V, `biasgen_vom/vop_battery_a`). 가장 걱정했던 M36a/b는 단독 컬럼이라 **여유 0.439V로 문제 없었고**, 실제 병목은 **diode 2개 직렬 컬럼**이었다. 그러나 diode 최소 Vgs로 하한을 잡으면 **원리적으로 불가능한 스택은 하나도 없다** — 4개는 비-diode 그대로도 가능하고 3개는 비-diode가 0.10~0.14V만 내려가면 된다. 정직한 한계: 그 최소값은 `gm_id 25~26.5`/`L=0.15µm`에서 나오는데 A11의 gain 정점(18~20.5)을 지난 영역이고 §7.10 knee보다 낮은 L이라 **대가가 크다** — 표는 해의 존재를 보이는 하한 증명이지 설계안이 아니다. **A8 재해석**: diode Vgs는 gm_id가 정하는 종속값이라 스택 KVL은 연립 방정식이 아니라 **gm_id 제약**이다 → 별도 solver가 아니라 §7.9에 제약 추가로 처리 |
| **4.14** | 2026-09-08 | **A8 재해석의 계기판 구현 — `stack_headroom_slack` metric 신설**. 스택 KVL을 연립 solver가 아니라 **gm_id 제약**으로 다루기로 한 v4.13 결론을 실물로 만들었다: 각 `vertical_stack_id`에 대해 `Σ_{diode} Vgs_k(gm_id_k,L_k,vsb_k) + Σ_{비-diode} vds_j`를 예산(`vdd` 또는 `vdd − ref_vds`)과 비교해 **최소 여유**를 V로 돌려준다. 음수면 그 스택이 성립하지 않는다. 값-동일 그룹(offset 매칭 쌍)은 대표 1개만 합산하고, diode 해가 없는 그룹은 `-inf` 대신 건너뛴다. 파일럿 실측 **−1.3456V**로 사전계산 스크립트와 정확히 일치. 부수로 `diode_vds_cached()` 신설 — 자기일관 해법은 LUT 격자 49점 스캔 + bisection 60회라 diode 하나당 100회 넘는 조회인데, 이 metric이 16개 소자에 매번 하므로 캐시가 필요했다(**353.6ms → 0.069ms, 5100배**). 캐시 키는 "이 계산이 실제로 읽는 모든 값"(kind/gm_id/L/vsb)로 잡아 CMFB MNA 캐싱 회귀(`metric_spec`만 키로 써서 `ctx.sized` 변경을 놓친 사고)를 반복하지 않게 했고, gm_id/vsb를 바꾸면 값이 실제로 달라지는지 확인했다. **아직 constraint로 걸지 않았다** — 현재 사이징에서 7개 스택이 음수라 지금 걸면 즉시 infeasible이 되므로, 먼저 재탐색으로 해를 찾은 뒤 건다. 회귀: 두 self-test 기준선과 바이트 동일 |
| **4.15** | 2026-09-08 | **§0 "이어받을 지점" 신설 + §9 Next Steps 현재화**. 세션이 길어져 다음 세션이 어디서부터 손대야 하는지가 문서에서 바로 안 보였다. 문서 최상단(Context Anchor 다음)에 §0을 만들어 (0.1) 지금까지 완료한 코드 변경과 **파일럿 계기판 6개 실측값**, (0.2) 다음 작업인 **B1 5단계 배선+재탐색**의 구체 절차(vds 기입 7곳 줄번호 포함), (0.3) 착수 전 알아야 할 전제(feasible 영역은 있으나 대가가 크다 / 병목은 M36a/b가 아니라 diode 2개 직렬 컬럼이다 / 재사이징 후에야 vsb가 확정된다), (0.4) 검증 방법(기준선 바이트 대조 + 계기판 6개 전후 비교 + probe 9개 재실행), (0.5) 아직 사용자 승인이 필요한 것 3가지를 정리했다. §9는 그 이후의 큰 흐름만 남기고 이미 끝난 항목을 걷어냈다. **엔진 코드는 "기존 결함 수정 + 계기판 신설"까지만 손댔고 새 파이프라인은 한 줄도 구현하지 않았다**는 경계를 §0.1에 명시 |
| **4.16** | 2026-09-08 | **B1 5단계 착수 계측 — 차단 사유 2건 발견(B15/B16), 배선 착수 보류**. 사용자 승인 후 배선에 들어가면서 계획이 적어둔 절차가 성립하는지 먼저 찼다. **B16**: §0.2 step 2가 전제한 `solve_diode_connected_vds(gm_id,...)` 호출이 헤드룸 시점에 불가능하다 — 실주행 계측에서 **diode 16개 전부 `L`은 있고 `gm_id`가 없다(0/16)**. `L→VDS→gm_id` 순서의 필연적 결과이고 이 재설계가 뒤집으려는 바로 그 문제다. 다만 `Vgs=Vds` 구속은 양방향이라 `gm_id = gm_id_for_vgs(vds, L, vds, vsb)`(O(1), 기존 함수)로 **현재 순서를 유지한 채** 배선 가능하다 — 80점 왜복 검산에서 76점이 오차 1mV 미만으로 일치. 대가는 diode의 gm_id가 자유 탐색 변수에서 빠지는 것. **B15(아무도 지적 안 한 신규 결함)**: 그 왜복 검산이 PMOS에서만 깨져 파고들었더니 **LUT의 L 보간 자체가 부서져 있었다** — `_gm_id_curve()`가 ID는 로그공간(세션29 성능 최적화), GM은 선형공간에서 보간해 두 보간이 불일치한다. PMOS는 L=0.15↔0.35µm에서 같은 VGS의 ID가 **6자릿수** 차이라(DIBL, 물성은 정상) 기하평균 vs 산술평균 괴리가 **207배**로 증폭돼, **앵커 사이에서 gm/ID가 403 / 5,517 / 56,646**까지 오른다(물리 상한 ≈30~38). 앵커 위에서는 전부 정상이고 NMOS는 무사하다. `L_stage2out_p`(M15/M25 PMOS)/`L_cascode`(M2a/M2b) theta가 `L∈[0.15,1.0]µm`를 **5nm 격자**로 훑으므로 실제 탐색이 이 대역에 들어간다. **현재 저장된 파일럿은 오염되지 않았다**(PMOS가 전부 앵커에 안착 — 그 선택 자체가 아티팩트일 가능성은 남는다). **차단 이유**: §0.3이 예상한 재탐색 해가 `L=0.15~0.45µm`로 정확히 오염 대역이라, 지금 재탐색하면 그럴듯해 보이는 틀린 답이 나온다. 해결 후보 ①GM도 로그보간(폭발 소멸·앵커 보존 <1.5e-3, 그러나 `pmos L=0.20,gm_id=20`에서 W=339mm로 정확도 미보장) ②L을 앵커로 고정(유효 앵커 4개뿐이라 §7.10 knee 분해 불가) ③`sky130_lut_sweep.py`로 앵커 추가(근본 해결, 체크포인트 재사용으로 새 L만 ≈14분, 단 주석의 '새 앵커는 끝에만 추가' 제약이 중간 삽입을 막는다) — **전부 승인 대상**. 조사 스크립트 2개 자산화(`probe_diode_gmid_readiness.py`/`probe_lut_L_interpolation.py`) |
| **4.17** | 2026-09-08 | **B15 ① + B16 + B1 5단계 배선 해소 — ★절대원칙 이행**. 지난 세션에 만들어만 두고 호출처가 **0곳**이던 `set_device_vds()`/`solve_diode_connected_vds()`를 실제 경로에 넣었다. **B15 ①**: 보간 방식을 논증이 아니라 **leave-one-out 실측**으로 고랐고(L 앵커 하나를 빼고 보간해 그 앵커의 실제 SPICE 스윙값과 대조), 배열마다 답이 달랐다 — ID/GM/GDS는 로그, **CGG만 선형**(Cgg는 ~W·L·Cox라 L에 거의 선형, 로그로 바꾸면 0.3%→10.2%로 오히려 나빠진다). gm/ID 곱선 오차 중앙 13.70→2.63%(pmos)·최악 17,884.9→33.6%. **B16**: §0.2 step 2가 전제한 방향이 불가능해(헤드룸 시점에 diode 16개 전부 gm_id 없음) `gm_id = gm_id_for_vgs(vds, L, vds, vsb)`로 **반대 방향** 강제. `apply_diode_self_consistent_gm_id()`를 `gm_id_role` 루프 직전에 배선하고 `_gm_id_source` 태그로 덮어쓰기를 막는다. **B1 5단계**: vds 원시 대입 7곳을 전부 setter 경유로 교체(각 사이트는 gm_id를 먼저 확정하도록 순서 조정 — 그래야 검사가 성립한다), setter 본체 1곳만 남음. **헤드룸 배분기 변경(사용자 승인)**: 배선하자 M11a가 vds=0.2V에서 W=4.03e8µm를 요구했다 — diode의 vds는 나눠줄 몷이 아니라 W를 고르는 일이다. `diode_vds_window()` 신설 + `allocate_stack_headroom()`이 구간 소자를 배분에서 빼고 하한부터 주도록 수정(singleton 우회 3곳도 `_singleton_vds()`로 묶음, C9). 실측: diode **16/16 구간 존재**(폭 0.19~0.41V), 그중 14개가 배정된 0.2~0.3V보다 **높은** vds를 요구. **결과**: self-test 둘 다 exit 0, M18_bg 0.20→0.75V·M36a/b 0.30→0.9375V(둘 다 구간 안), 파일럿 gain 72.95→72.90·cmrr 87.28→76.47·psrr 102.13→89.29. ★견누지 않은 신호: 세션41부터 알려진 `stage1_out` KVL 위반이 두 곳에서 저절로 줄었다(+0.162→−0.038V, +0.754→+0.391V). **P1-b 신설(사용자 지시)**: "타당성을 따지지 않고 skip 로직을 만들지 말 것". 새 pass의 continue 3개를 실측했더니 처리 6,960회/skip 전부 0회라 명시적 에러로 교체했고, 앞서 넣었던 `known_sizing` skip은 그것이 topology·워크스페이스에 0건인 **self-test 픽스처 전용 우회로**라 제거했다. 그 검사가 픽스처의 기존 오류 2건도 찾아냈다. 부수 발견(미수정): `grid_points_per_theta=1`이 `i/(n-1)`에서 ZeroDivisionError |
| **4.18** | 2026-09-08 | **B15 완결(③ 스윙) + 코너·면적 실측 — 재탐색의 목표가 스택에서 면적으로 바뀜다**. LUT 앵커 7→12개(중간 삽입 5개, ngspice 95분, 체크포인트 120/120). leave-one-out으로 재측정하니 ①과 ③가 곱해졌다 — pmos 중앙 오차 13.70%(기존+7앵커) → **1.41%**(로그+12앵커), 최악 17,884.9% → 25.2%로 약 10배 개선. 새 앵커 실측이 스윙 전 로그보간 예측을 검증했다(PMOS gm/ID 최대 예측 27.0/27.9/28.9 vs 실측 28.7/29.2/29.6) — 보간은 방향만 맞춰주고 정확도는 앵커가 필요했다는 근거다. **코너 실측**: diode 구간의 하한을 고르는 것은 선호가 아니라 **강제**였다 — lo만 성립하고 mid/hi는 둘 다 infeasible(구간 폭 0.19~0.41V가 있어도 절반만 올리면 스택 예산이 음수). **면적이 처음으로 측정됐다**: 총 1050.40µm², diode 16개가 665.53µm²(63.4%), v3.3 예시 예산 200µm²의 5.3배. ⚠️ 이전의 117µm²는 물리적으로 불가능한 상태의 면적이라 비교 대상이 아니다. 계기판에 면적을 추가했고(v3.3의 핵심 제약인데 빠져 있었다), gain이 새 LUT만으로 +7.19dB 올라 75.39dB가 됐다. **회귀 골든**: nmcnr_3stage stage2의 L이 0.35→0.25µm로 옴겨서 갱신했는데 진짜 회귀가 아니다 — gms와 stage1/stage3가 동일하고 gm_id도 그대로며, 전력 동점에서 새 앵커가 목록 앞이라 이긴 것(문서화된 동점 해소 규칙). **§0.2 step 3 불필요 판명**: 배분기가 합=vdd를 구조적으로 강제해 모든 그룹의 slack이 정확히 0이다 — 제약이 사후 검사에서 불변식으로 올겨갔다. 남은 작업은 step 4 하나이고, 그 목표는 스택이 아니라 **면적**이다 |
| **4.19** | 2026-09-08 | **면적 제약이 조용히 깨지던 이유 — 결함 2개 해소(B17/B18), 1개 발견(B19)**. 재탐색을 돌리려고 `area_um2 <= 900`을 걸었는데 결과가 1050.40µm²인데 "성공"이었다. **B17**: 엔진의 `pairs_meta` 루프가 **L만 전파하고 gm_id는 전파하지 않았다** — VDS는 `same_as_device`가, W는 gm_id가 결정하므로 gm_id 하나만 무방비였다. 매칭 쌍 21개 중 6개가 갈리고, 그중 3쌍은 동작점(L/ID/vds/vsb)이 완전히 같은데 gm_id만 다르다(M2a/M2b 15.0 vs 2.5). 한쪽은 권위 있는 출처가 확정하고 다른 쪽은 `gm_id_role` 루프가 독립 탐색해서 갈린다. L 전파와 같은 구조로 gm_id 전파를 추가(동작점이 같은 쌍만) → 갈리는 쌍 6→3개, 면적 1050.40→936.38µm², 레이아웃 복구가 더 이상 W를 안 건드린다. **B18**: 그래도 제약이 깨졌다 — `_sync_finger_fixup()`이 `w = n_fingers * finger_w`로 W를 다시 쓰는 것(레이아웃의 정당한 요구)은 문제가 아니고, **재검증이 그 결과를 안 본다**는 게 결함이었다. `_collect_device_refs()`가 spec에 이름이 적힌 소자만 모으는데 `area_um2`처럼 `devices`를 안 쓰는 metric은 참조가 빈 집합이라 "무관"으로 분류됐다 — 전 소자를 쓰는데 건너뜀 metric 6개(`power_uA` 목적함수 포함)와 소자 미명시 전체회로 metric 3개(`cmrr`/`psrr` 제약 포함)이 다 빠졌고, 선언된 제약 5개 중 `gain_db` 하나만 재검증되고 있었다. **판단 방향을 뒤집어** 전부 재계산으로 바꿔다(비용을 먼저 측정: 8회 호출 × 1.6ms = 전체 233s의 **0.01%** — 아끼는 게 없으면서 버그만 숨기던 최적화였다). 결과 **면적 제약이 실제로 지켜진다**: cap 1000/900/800에서 988.30/845.05/792.87µm²(이전엔 1057.66/983.77/943.42로 전부 위반), **달성 가능한 면적 하한은 700~800µm² 사이**고 800µm²에서 gain 56.08dB로 여유가 2.08dB뿐이라 설계가 실제로 빡빡하다. **B19(신규, 미해결)**: 남은 3쌍을 조사했더니 세 그룹 모두 게이트·소스를 공유하는 **진짜 전류미러**인데(순수 connectivity 사실) VGS가 최대 464mV 벌려있고 미러 규약도 깨졌다(M8 1530배). 다만 고치면 M8/M17이 W≈1545µm를 요구해 상한의 7.7배라 **현재 동작점에선 회로가 성립하지 않는다** — bias generator의 전류/L을 다시 잡는 회로 설계 판단이 필요하다 |
| **4.20** | 2026-09-09 | **B19 결론 번복 + B20 신규 발견**. B19 선택지를 계산하려고 설계공간을 훑다가 두 가지가 드러났다. ① **B19의 대상이 틀렸다** — 미러 그룹을 `symmetry.matching_pairs`(선언)로 셌는데 VGS 동일 강제는 게이트·소스 공유(connectivity)에서 나온다. 넷리스트 전수로 세면 11→**18소자**이고 6소자(`M5 M6 M7 M38 M66 M68`)가 어떤 선언에도 없다 — tail 2개, NMOS 그룹의 diode 레퍼런스 M66, 통째로 누락된 M7/M36a 그룹. ② **B19의 결론도 틀렸다** — VGS를 자유변수로 두면 세 그룹 모두 성립하고(20/9/36 조합) 합 73.95µm²로 **면적이 오히려 준다**. `k_Iref`는 지렛대가 아니었다. ③ 그 과정에서 **B20 발견**: `_solve_vgs()`가 단조를 전제하는데 PMOS LUT가 비단조라 `argsort` 역보간이 branch를 넘나든다 — 모든 W 계산의 뿌리이고 조용히 틀린다(탐색범위와 겹치는 동작점 53.6%, 파일럿 2소자에서 2.36배). NMOS는 무사. 위험은 vsb(0.8V에서 95.7%)와 긴 L(>=1.5µm)에 몰려 있어 **B9를 고치면 노출이 커진다**. 조사 도구 2개 신설(`probe_mirror_design_space.py`, `probe_gm_id_monotonicity.py`) |
| 4.21 | 2026-09-09 | **B19'의 미결 판단 2건 사용자 확정**. (가) 미러 18소자를 **전부 강제한다** — tail M5/M6를 bias 미러에 묶는 것이 설계 의도임을 확인받았다. (나) 공유 VGS는 **gain 기준**으로 고른다(면적 아님) — "첫번째 differential input 단의 tail이기 때문에 gain에 직접적으로 영향을 미치는 id전류를 만들고 있어". 이에 따라 v4.20이 제시한 면적 오름차순 랭킹은 **기준이 틀린 것**으로 철회하고 `tests/probe_mirror_gain_ranking.py`를 신설해 같은 조합을 엔진의 실제 `gain_db`로 다시 줄 세운다(3그룹 교차, ctx 복사 후 `compute_metric` 직접 호출). **작업 순서 확정: B20 -> B19' 배선 -> B9** — 3그룹 중 2그룹이 PMOS라 B20을 안 고치고 배선하면 W가 깨진 경로로 계산된다 |
| 4.22 | 2026-09-09 | **gain 기준 랭킹 실측(6480조합) + B21 신설**. 사용자가 확정한 gain 기준으로 미러 조합을 다시 줄 세웠더니 **답이 뒤집혔다** — 면적 최소 조합은 gain 순위 **6423/6480**(63.72dB)이고, gain 최적은 두 신호경로 그룹 모두 **L=4.0µm**에서 **89.82dB**(미러면적 24배). 지렛대는 pmos:Vbias1(20.8dB)과 nmos:Vbias4(20.0dB)이고 **pmos:Vcmfb는 0.0dB**(CMFB 경로). 그 과정에서 **B21 발견**: 선언된 제약 `gain_db`는 `gain_stages_sum`으로 소자 6개만 더해 미러 18소자를 **구조적으로 못 본다** — 6480조합 전부에서 Δ=0.0000인데 전체회로 MNA는 **26.15dB** 벌어진다. `M10/M19`의 drain이 stage1 출력노드(Vop1/Vom1)인데도 그렇다. 즉 `gain_db >= 54` 제약이 26dB짜리 효과에 눈이 멀어 있다. **B20 보강**: 선택지 ①(정점 오른쪽만)은 33.6%에만 성립 — 나머지는 잡음성 미세상승(중앙 0.606%)이라 올바른 정식화는 **rightmost root**다. gain 최적점 L=4.0µm가 B20 최악 구간과 정확히 겹쳐 **B20 선행이 실질적 필수**가 됐다 |
| 4.23 | 2026-09-09 | **B20 해소(사용자 승인 후 엔진 수정)**. `SemiEmpiricalGmIdLUT._solve_vgs()`를 `np.argsort` 전역 역보간에서 **rightmost root**로 재작성 — 목표를 품는 가장 오른쪽 구간에서만 보간하고, 곡선 범위 밖이면 명시적으로 실패하며(비단조 사실을 메시지에 적는다) 평탄 구간은 큰 VGS 쪽을 취한다. **검증 4건**: 문제 지점 VGS 1.3124→1.5047V(독립 계산치와 일치) / NMOS 전 격자 **16,186건 구·신 완전 동일**(같은 연산 순서로 구현해 비트 단위 보존) / `two_stage_ota`에서 달라진 조회 **1,895건이 전부 긴 L(2.9~3.7µm)**이고 Δ가 전부 양(강반전 해로 이동, 최악 0.719→1.333V) / 파일럿 재탐색 완주 + 제약 5개 만족. **비용**: 호출 1회 4.95→5.85µs(1.18배), 평가 1회의 **2.55% 증가** (이 함수가 465ms 중 14.0%). 처음 구현은 2.3배 느렸고 docstring에 '오히려 싸다'고 잘못 적었던 것을 실측으로 바로잡았다. self-test 기준선 2개를 각 1줄씩 의도적 갱신(사유 `tests/baseline/README.md`) |
| 4.24 | 2026-09-09 | **B19' 배선 실행 + B22 발견**. 미러 15소자에 `gm_id_match_vgs_of`를 선언해 실제로 배선했다(`device_roles`만 변경, netlist 포함 다른 섹션은 구조 대조로 무변경 확인). **배선 전 점검 3건 통과**: 걸어도 무효인 소자 0개(`_gm_id_already_authoritative`의 조용한 skip에 걸리는 소자 없음), 레퍼런스 3개(M18_bg/M66/M36a) 전부 `diode_self_consistency`로 확정돼 companion 자격 OK, 체인 아님. 뒤에 도는 B17 매칭 전파도 `ratio` 미러를 명시적으로 제외해 되돌리지 않는다. **그런데 돌려보니 현재 동작점이 그 관계를 만족하지 못한다** -- SLSQP 40회 전부 infeasible, 레이아웃이 `cmfb_tail`에서 공통 finger 폭 실패, self-test도 깨짐. 원인은 **B22**: 헤드룸 배분기가 diode에 구간의 `lo`를 주는데(면적을 크게 잡는 쪽 -- 이미 docstring에 경고돼 있었다) 미러 강제 후에는 그게 그룹 전원의 W를 결정한다. 6소자가 상한을 최대 **66.7배** 초과(M38 13339.9µm, M5 12623.3µm). 필요 VGS는 Vbias1 >= 0.80V / Vbias4 >= 0.55V. 저장소를 깨끗이 두려고 토폴로지는 되돌리고 배선 스크립트를 `tests/apply_b19p_mirror_wiring.py`로 보존했다. 부수 확인: 미러 그룹 안에서 L이 갈리고(`mirror`=0.375µm / `bias_replica`=0.180µm) 둘 다 `_L_ROLE_MULTIPLIERS` **하드코딩 상수**라 theta가 아니다 -- gain 최적 L=4.0µm로 가려면 그 상수나 theta 신설이 필요하다 |
| 4.25 | 2026-09-09 | **B22 구현 완료 + B23 발견(B9가 선행 조건)**. `diode_vds_window(..., mirror_members=())`로 확장해 VGS를 공유하는 소자 전원의 W 한계를 함께 본다. 선언 기반 옵트인이라 미배선 회로는 무영향(self-test diff 0줄). 종속의 vds가 미정이면 역할별 `min_vds`를 바닥으로(안전 방향, 보수성 대가 실측 0.0375V), L/ID 미정이면 명시적 실패. `id_density_at_vgs()` 신설(VGS를 아는 호출자용 -- 왕복이 비단조 구간에서 branch를 넘나드는 것을 피한다). **B22의 효과가 실증됐다**: 같은 theta에서 B22를 끄면 `area_um2`=**655,086µm²(655mm²)**인데도 통과한다(파일럿 제약에 area가 없다). **B23**: 그래도 파일럿이 안 풀리는 원인을 후보 vds 전수 덤프로 짚으니 `M38`의 **vsb=0.8625V**(source=gnd라 0이어야 함, B9가 지목한 그 4소자)가 전류밀도를 55배 낮게 보이게 해 W를 13,340µm로 튀긴 것이었다. 즉 B19'/B22가 틀린 게 아니라 입력이 오염돼 있다 -- **작업 순서 B9 -> B19' 배선 -> 재탐색**으로 확정. 조사 도구 신설 `probe_b22_headroom_attribution.py`(미배선/배선+B22끔/배선+B22켬 3자 대조) |
| 4.26 | 2026-09-09 | **B9 수정 시도 + B24 기록**. `probe_node_voltage_audit.py`가 낡은 instance.json(세션18, 옛 필드 `vs`)을 읽고 있던 것을 **지금 엔진으로 새로 사이징**해서 재도록 고쳤고, 그 결과 vsb 불일치를 처음으로 정확히 쟀다 — 51소자 중 **26개**, (가)레일인데 vsb≠0 4개 / (나)비레일인데 vsb=0 15개 / (다)값 불일치 7개(M9a·M9b, M18a·M18b는 정확히 서로 바뀜). `reconcile_vsb_from_nodes()` 신설 + `audit_vsb_consistency()`를 게이트로 **배선**(두 함수 모두 세션46에 만들어졌으나 엔진 호출부 0개였다). 올바른 물리가 적용되자 `M11b`가 W=6342µm를 요구해 파일럿이 성립하지 않는다 — **남은 것은 회로 설계 판단**이라 혼자 진행하지 않았다. 엔진 변경분은 `tests/b9_vsb_from_nodes.patch`(166줄)로 보존하고 저장소는 되돌려 self-test 2개 모두 diff 0줄 |
| 4.27 | 2026-09-09 | **적층 diode 선택지 계산 + B25(A8 재해석 정정)**. class-AB 배터리 4스택이 전부 적층 diode이고 **아래쪽 vsb = 위쪽 vds**라, M11a와 M11b는 같은 전류·L·VGS인데 M11b가 **61.3배** 넓어야 한다(차이는 오직 바디효과). v4.13이 A8을 "연립 solver 불필요"로 재해석한 것은 **이 vsb 결합을 못 본 것**이다. 축별 실측: 전류는 전 구간 실패(W가 둘 다 ID에 비례해 비율 불변), L은 PMOS만 고침(`bias_replica` 0.180µm → 6342→20.00µm, NMOS는 1882→1687µm로 무효 -- diode에 0.375V씩만 가는 깊은 약반전). **연립으로 (v_a,v_b)를 함께 고르면 PMOS 60조합 / NMOS는 현재 L 그대로 32조합 성립** -- 설계 변경이 아니라 배분을 함께 푸는 문제다. 배선 시험으로 확인: 계산된 diode 창의 vsb가 전부 0.0/0.2로 실제값(0.675/0.375)이 아니었고, 그래서 배분기의 `lo`가 결합 제약을 위반한다(M11b W=924µm). 사용자 확정: M11a/M11b/M20a/M20b의 `L_role`은 `bias_replica`(class-AB 배터리 전압기준이지 신호경로 미러 아님). 조사 도구 `probe_stacked_diode_options.py` 신설 |
| 4.28 | 2026-09-09 | **B25 구현 완료 -- 파일럿이 처음으로 물리적으로 옳은 vsb로 통과**. `solve_stacked_diode_pair()` 신설 + 헤드룸 배선 + B9(vsb 노드전압 유도, 감사 게이트) + `L_role: bias_replica`(M11a/M11b/M20a/M20b)를 함께 적용해 **파일럿 평가 성공**(gain 65.55 / **area 847.45µm², 925.52에서 감소** / cmrr 66.12 / psrr 81.38). 구현 중 실측으로 바로잡은 것: 결합식은 `vsb_lo = vsb_up + v_up`(누적이다 -- 위쪽 소스가 레일일 때만 `v_up`과 같다), 쌍의 합에 스택 예산 상한 필요, 쌍이 스택의 전부면 합이 예산과 정확히 같아야 함, 위쪽이 비-diode인 경우도 대상(M57←M58, M64←M63), 위쪽 소스가 비레일이면 그 vsb가 다른 스택이 정한 노드에 달림(M58의 Vx는 diffpair 소관)이라 노드전압으로 유도. 잔여는 L5c 픽스처 고정점 하나(M39/M40 최소합 1.837V > 1.8V) -- 파일럿은 통과하므로 픽스처 문제다. 변경분 `tests/b25_b9_stacked_diode.patch`(363줄) 보존, 저장소는 되돌려 diff 0줄 |
| 4.29 | 2026-09-09 | **L5c 잔여의 원인 확정 -- L이 아니라 픽스처의 고정 전류다**(사용자 지시 "2번 봐"). 오류 메시지에 쌍의 L/ID/vsb를 넣어 재보니 L5c 고정점의 M39/M40 전류가 **8.197µA로 파일럿(0.47µA)의 17배**였다. **`L_role` 변경은 해법이 아님을 실측 확인**: `mirror`(0.375µm)면 파일럿 OK/L5c 실패, `bias_replica`(0.180µm)면 L5c OK/**파일럿 실패**(성립 합 1.05~1.24 < 1.8) -- 전류가 17배 다르면 같은 L로 둘 다 1.8V를 정확히 나눌 수 없다. 부수 개선: 정확 일치를 격자점 쌍에서만 찾던 것을 `v_lo = 예산 - v_up`으로 **연속 평가**하도록 보완(LUT는 VDS를 연속 보간하므로 격자 양자화는 물리가 아니다). 패치 363→388줄 |
| **4.30** | 2026-09-09 | **B25+B9+L5c 픽스처까지 착지 -- 파일럿 면적 44% 감소**. 사용자 선택(1번)대로 L5c의 `r_cmfb_vocdes`를 중점(0.11) 대신 **하한(0.02)**에 고정했다 -- 그 값이 파일럿의 실제 최적점이고, 중점은 M39/M40에 **17배** 전류를 흘려 바디효과를 넣은 뒤로는 도달 불가능한 점이 됐기 때문이다(`K_replica`/`r_classab_battery`를 이미 특별 고정하는 것과 같은 방식). 그러자 사이징은 완주하는데 레이아웃이 `assign_finger_geometry`에서 막혀(M11a/M11b/M20a/M20b의 공통 finger 폭 없음), 적층 쌍 선택을 min-sum에서 **W 균형**으로 바꿨다 -- 예산 보장은 이미 상한이 하므로 자유로운 tie-break이고, 같은 60개 성립 쌍 중 min-sum은 W 2.320/1.415µm(비 1.64)인데 W 균형은 4.305/4.802(비 1.12)다. **결과**: self-test `sizing_recipe` exit 0 / diff **1줄**(의도적), `stick_diagram` diff **0줄**, 기준선의 `mismatch_sigma_mV`가 **3.01→2.19로 27% 개선**(W 균형이 매칭에도 유리). 파일럿은 gain 65.55 / **area 517.61µm²(925.52에서 -44%)** / cmrr 66.11 / psrr 81.35이고 vsb 감사 게이트도 통과한다. **이번이 파일럿이 물리적으로 옳은 바디효과로 끝까지 완주한 첫 결과다** |
| **4.31** | 2026-09-09 | **B19' 배선 착지 -- 미러 VGS 퍼짐이 0이 됐다**. `tests/apply_b19p_mirror_wiring.py`로 15소자를 배선하니 처음엔 M66의 창이 다시 비었는데, 원인은 B22가 **헤드룸 시점**에 미러 멤버의 vsb를 `ctx.sized`에서 읽는데 B9의 보정은 그 **뒤에** 일어난다는 것이었다. 멤버 vsb도 노드전압에서 유도하도록 맞추자 통과했다. **검증**: VGS 퍼짐이 세 그룹 모두 464.2/663.2/9.2mV -> **정확히 0.0000mV**. 미러비도 대부분 1.0배 근처(0.877~1.106)이고, 어긋나는 셋(M6/M7/M5)은 전부 tail이라 `L_role`이 달라 L·vds가 다른 정당한 경우다(§10.2 A4와 일치). `M18_bg`의 vds가 0.75→**0.825V**로 오른 것은 **B22가 미리 계산한 값과 정확히 일치**한다. self-test `sizing_recipe` exit 0 / diff 2줄(의도적), `stick_diagram` diff **0줄**. `mismatch_sigma_mV` 누적 **3.01→1.74(42% 개선)**. 파일럿 gain 65.55 / area 584.59µm² / cmrr 62.82 / **psrr 104.30** |
| 4.32 | 2026-09-10 | **§7.11 신설 — 기생 pole clamp를 상수 없이 유도한다**(사용자 지시로 문헌 조사 후, "수치로만 적용하면 이 회로에 특화된 값이 된다"는 지적 반영). 조사: Sansen "비지배 pole ≥ 2×GBW", 표준 2-pole(p₂/UGF 3배 → PM 71.6°), 실무 경험칙(단일단 fT ≥ 10×GBW, 2단 >20×). 그런데 **이 회로엔 원문 정의식이 이미 있다** — `PM = tan⁻¹(ω_p2/ω_c)`. 여기서 `N = α × tan(PM_target)`가 유도되고, **§7.10의 "N~5~10"이 정확히 α∈[2,3.6]**임이 드러났다(임의값이 아니었다). 실측: tail 4개의 최소 `fT/f_c`가 knee(0.375µm)에서 **28배**라 N=10/20 어느 쪽도 안 걸리고, 실제로 무는 것은 **L≳0.7µm** — gain이 L을 4.0µm로 밀려 할 때의 제동이다. **코드화 원칙**: N을 상수로 박으면 회로 전용이 되므로, 두 항을 각각 회로에서 얻는다 — 필요 pole 위치는 **토폴로지의 PM 관계식**에서, 노드 용량비는 **넷리스트에서 측정**. 그러면 `fT ≥ N·GBW`는 `ω_pole(node) = G/C ≥ ω_p2_req`의 손 근사였음이 드러나고 α·N이 둘 다 사라진다. clamp는 숨은 상수가 아니라 `sizing_roles.metrics`의 metric으로 노출한다(C1) |
| 4.33 | 2026-09-10 | **§7.11 구현 완료 — 하한까지 유도해 상수를 전부 없앴다**. `PM_parasitic = 90 - Σ atan(w_c/w_pole)`로 위상을 직접 더해 `k`(pole 개수) 배분을 없앴고, 하한은 새 상수가 아니라 **이미 선언된 `PM_target_deg`**다. 이 식은 원문의 `PM = atan(w_p2/w_c)`를 pole 하나일 때의 특수케이스로 **정확히 포함**한다(항등식). 신설: `signal_path_nodes()`(gate→drain 방향그래프 도달성으로 bias 노드 자동 배제), `node_pole_estimate()`(드레인→gds / 소스→gm+gds / 게이트→Cgg), `_metric_parasitic_pm_deg`. **실측으로 두 번 바로잡음**: ① 전 노드를 더하면 bias 노드가 각각 ~90도를 먹어 **-1004도**가 나온다 → 경로 선언 필수 ② LUT에 접합용량이 없어 못 세는 노드는 근거를 따져 갈랐다(소스 붙은 저임피던스는 이유와 함께 제외, 드레인만 붙은 고임피던스는 **명시적 실패**). **파일럿 실측 `PM_parasitic = -8.9도`** — `Vg15`/`Vg25`(class-AB 출력단 게이트)의 pole이 31.6MHz로 **크로스오버의 0.86배**라 각 49.2도씩 먹는다. 기존 metric 어느 것도 못 보던 문제다. constraint는 아직 안 건다(선례대로 4개 회로에서 먼저 잰다). self-test diff 0줄 |
| **4.34** | 2026-09-10 | **spec 정본화 — 한 세션치 측정이 비정본 기준이었음을 확인하고 재발 방지를 배선했다**(사용자 지시 "이번 실수가 재발하지 않도록 방법을 강구해"). 조사 스크립트들이 spec을 손으로 복붙해 정본(`run_harness.SPECS`)과 갈려 있었다(`gm_id_grid` 57점 vs **21점**, `L_candidates` 41점 vs 12점, `stage_power_tolerance` 누락). 정본 주석에 이미 세션30 실측 "L을 촘촘히 하면 gm_id도 촘촘해야 한다"가 있었는데 복제본은 **둘 다 성겨** 우연히 안 터졌던 것이다. **정본으로 재탐색하면 파일럿이 수렴하지 않는다**(SLSQP 3 start 전부 실패, `biasgen_vom_floatsrc_sink` 스택 예산 **-0.024V**, M9b 미해결) — 즉 v4.28~v4.33의 수치는 정본에서 도달 불가능한 동작점이다(§10.6). **신설·배선**: `require_declared_spec_source()`(`_build_theta_evaluator()` 첫 줄), `spec_fingerprint()`, `run_harness.canonical_spec()`/`derived_spec(key, why, **overrides)`(덮어쓴 항목만 갈리고 무엇을 왜 바꿨는지 `_spec_source`에 자동 기록). 복붙 블록 **238줄을 16개 스크립트에서 제거**하고 정본 호출로 교체(복제본은 정본의 부분집합 24키⊂26키라 손실 없음). **★ 게이트를 만들자마자 그것이 죽어 있었다** — 모듈이 `os`를 최상위 import하지 않아 `NameError`가 났고 `except Exception: return`이 삼켜 항상 통과했다. 광범위 except를 제거하고 **자기시험 4건을 넣어** 게이트가 다시 조용히 죽으면 기준선 diff가 깨지게 했다. self-test 둘 다 exit 0 / diff **0줄** |
| **4.35** | 2026-09-10 | **M9b 스택 예산 음수 해결 + 기준점 복구 일반화 -- 정본 spec으로 파일럿이 처음 수렴했다**(145초, 직전엔 625초 동안 3 start 전부 실패). ① **배터리 KVL이 아무 데서도 강제되지 않고 있었다**: `M9a`/`M9b`는 직렬이 아니라 Vg15↔Vop1를 잇는 **상보 병렬쌍**(Monticelli floating battery)이라 `V_bat = vdd - VGS(M15) - VGS(M16)`인데, 선언된 `classab_centering_dev_v`는 VGS의 **차이**만 재고 **합**은 아무도 안 봤다. 실측 0.9799+0.8441=1.824>vdd ⟹ **V_bat=-0.024V**인데 centering(0.136≤0.15)은 **통과한 채** -- 즉 그동안의 파일럿 수치는 배터리 전압이 음수인 불가능한 동작점의 값이었다. 해결(사용자 선택): `stack_kvl_vgs_limit()`이 **선언만 읽어** VGS 상한을 유도(종속항을 **계수 k로 세는** 덕에 'M15와 M16이 같다'를 알 필요가 없다, k=2 ⟹ 0.8417V로 손계산과 일치) -> `search_gm_id_for_role(vgs_max=…)`; 포화 하한은 `lut_vdsat_headroom()`이 §2.7 `2/(gm/ID)`로 유도해 **새 상수 없음**(기존 `_default_cascode_headroom()` 재사용, 배분기와 **같은 헬퍼**). ② **기준점이 중점에 묶여 탐색이 출발을 못 하고 있었다**(사용자 지적 "중점에 묶이는 것도 해결했잖아. 왜 반영이 안 되어 있어?"): v4.30이 이미 `r_cmfb_vocdes`의 설계값은 하한이라고 확정했는데 그게 **self-test 픽스처에만 적히고 엔진에는 반영되지 않았다**. presolve의 세 단계가 전부 '기준점 평가 가능'을 전제해, 크래시하면 L 스캔이 조용히 midpoint로 후퇴하고 전 theta가 ambiguous가 된다. **`repair_infeasible_baseline()` 신설** -- 실패 메시지가 지목한 소자 -> 선언에서 그 소자를 담당하는 자유 theta -> 자기 bounds 양 끝을 시도, '평가 성공 **또는 병목 이동**'이면 채택. 증거가 못 짚으면 **측정된 실현가능점**으로 후퇴하고, 그것도 없으면 포기(없는 근거로 값을 옮기지 않는다). **회로/소자/theta 이름·상수가 코드에 하나도 없다**(사용자 지시 "이 설계에만 적용되는 것은 안 돼"). 파일럿 실측: `L_stage2out_p→하한 / r_cmfb_vocdes→하한 / r_diode_M11a→측정점 복귀` 3단계로 복구 -- 두 번째가 바로 v4.30이 손으로 정한 그 값이고 **이제 엔진이 스스로 유도한다**. 4개 회로 전수: folded_cascode는 **복구 0건 무동작**, two_stage/nmcnr는 기존 이월 항목. **결과**: gain_full 65.97 / cmrr 60.42 / psrr 81.97 / mismatch 1.36 / centering 0.1481 전부 통과, **V_bat -0.024→+0.380V**, **parasitic_pm_deg -8.9°→+33.88°**. **함께 고침**: M18b `budget_reference_device="M17"` 누락(vom 쪽 대칭 짝, 사용자 승인), `_grid_points_in_range(n=1)` ZeroDivisionError(잠복), L5c를 `stop_after_sizing=True`로 사이징까지만 분리(사용자 선택). self-test 둘 다 exit 0 / diff **0줄**(L5c 기준선 1줄은 앞서 갱신) |
| **4.36** | 2026-09-10 | **§7.11 L2 완성 -- 보상망을 실제로 세고 Cc를 유도한다**(사용자 지적 "pm보상 회로가 있는데 왜 그건 고려하지 않지?", "Cc와 Rz는 보상망이 계산해서 확정해야지"). ① **L1은 보상망을 못 봤다**: `node_pole_estimate()`가 소자 단자만 셌는데, 보상망은 `passive_elements`에 **이미 선언돼 있었고**(Cc1/Rz1/Cc2/Rz2) MNA는 그 저항을 이미 쓰고 있었다 -- 그 인자를 안 받은 것뿐이다. 하필 L1이 지목한 노드(Vop1/Vom1)가 정확히 Rz가 붙는 자리라 34.2도는 무효. ② **L2는 pole을 뽑지 않는다**: `det(G+sC)=0`의 근에는 bias 모드가 섞여 -1004도와 같은 오류가 재발하므로, `(G+jwC)v=b`를 직접 풀어 `PM = 180 - (DC->w_c 누적 지연)`으로 잰다. L1 식과 원문 `atan(w_p2/w_c)`를 **둘 다 특수케이스로 포함**하고, 지배 pole 제외 처리도 신호경로 제한도 불필요해진다. ③ **논문 확인 -- 필자의 해석이 틀렸다**: `omega_c`는 **loop gain** unity gain이고(개루프 A가 아님), 실측 `|A|(w_c)=6.52dB`가 `1/beta=6.38dB`와 일치해 선언이 옳음이 독립 확인됐다. ④ **빠진 connectivity 추가**(사용자 확정): CL1/CL2(Vop/Vom-gnd), Cf1/Cf2(**교차** Vom-Vip/Vop-Vim -- Vip와 Vop가 동상이라 비교차면 정궤환, 수치로도 |A|가 1/beta에 더 가깝다), Cs1/Cs2. PM 93.76 -> 81.13(+C_L) -> 75.35(+Cf)도. ⑤ **Cc 유도**: 원문 Eq.3/Eq.6에서 `d(gm1+gm2)/dCc=0` ⟹ `Cc = sqrt(beta*tan(PM_target)*C_Ltot*Cgg2)` -- **새 상수 0개**, 실측 374~385fF(원문 500fF는 그들의 Cgg2에 대한 값). `miller_ota_topology()`의 `Cm`과 같은 성격이고 그게 이미 선례였다. 배선 중 `cap_key`가 derived를 안 읽던 것(`KeyError: 'Cc'`로 드러남)과 `exposed_params`가 호출 후 갱신 안 되던 것을 함께 고침. ⑥ **제약 판정 수치 공차**: 활성제약 수렴으로 `cmrr=59.999999999118884`(잔차 -8.8e-10)가 5 start를 전부 버렸다 -> 상대오차 1e-9. 처음 `max(1.0,|target|)`로 뒀다가 **self-test가 잡았다**(면적 9.1e-12에서 공차가 값의 100배). **결과**: `parasitic_pm_deg >= PM_target_deg`를 `value_from_spec`으로 선언하고 재탐색 성공 -- PM **71.87**, gain_full 66.05, cmrr 60.50, psrr 81.65, mismatch **0.753**, power **233.73uA**(267.59에서 -12.6%). self-test 둘 다 exit 0 / diff 0줄 |
| **4.37** | 2026-09-10 | **미러 공통 L 3층 구조 -- 층1/층2/knee 착지**(사용자 확정 "M5가 주인이야"). ① **층1 동치류**: 진짜 전류미러(같은 kind/gate/source, **순수 connectivity**) + `same_as_device` + `matching_pairs`. `gm_id_match_vgs_of`는 **안 쓴다** -- 그 필드는 cross-kind VGS 매칭에도 쓰여 L을 공유하면 안 되는데(세션30 M15-M16), connectivity 판정이 둘을 정확히 가른다(실측 확인). 파일럿 15개 류, 큰 둘이 M5·M38 포함 8소자 / M6·M7·M36a 포함 11소자 -- 추적했던 사슬 그대로. ② **층2 주인**: tail=`headroom_role`, gain stage=`gain_stages_sum.stages`, stage의 tail="그 stage 소자들의 source net을 drain으로 갖는 tail"(연결), 최초 input 단=gain metric `excite` net을 gate로 갖는 소자의 stage. 실측 **주인 M5 / M6** -- 지시와 일치. 다른 3개 회로는 `gain_stages_sum` 미선언이라 **전부 폴백 = 동작 무변경**. ③ **knee로 상수 제거**: §7.10이 이름까지 명세해둔 `measure_L_knee()` 구현(한계효율 `Δ(gm/gds)/Δ(W·L)`, ID는 argmax에 무관해 인자 아님, 비단조 구간 건너뜀) + `knee_L_for_kind()`(gm_id 격자 **중앙값**, 캐시). 실측: **vds에 무관**(네 vds 중앙값 동일 -- L이 vds보다 먼저 배정되므로 결정적)하고 **kind마다 다르다**(nmos 1.63x / pmos 2.27x) -- 단일 상수 2.5x로는 못 담는 차이다. 격자가 spec에 선언돼야만 계산한다(toy LUT 폴백이 W 하한을 깨는 것을 self-test가 잡았다). **결과**: L 갈린 동치류 **3/3 → 0**, `mirror_ratio_error_pct` 11.84→13.96, 재탐색 전 제약 통과 (`parasitic_pm_deg` 70.12 / cmrr 60.00 / gain_db 60.39), **power 267.59→225.38uA**, **area 693.88→524.24um²**. self-test 둘 다 exit 0 / diff 0줄. **남은 것**: 층3(공동 gain sweep + L theta 일반화), 층0 게이트 파이프라인 배선, `bias_replica: 1.2` 상수 |
| **4.38** | 2026-09-10 | **층3 착지 + 중복계산 전수검사**. ① `synthesize_l_class_thetas()`가 동치류 공통 L을 **theta로 파생**한다(손선언 없음, 이름도 파생 -- 사용자 지시 "특정 이름으로 하지마"). feed 타입 `l_class` 신설(L만 확정, 레지스트리 확장 계약대로). 파일럿에만 2개, 나머지 3개 회로는 **0개 = 동작 무변경**. 주인이 여럿인 류도 **theta는 하나**라 "두 stage gain 동시 만족 sweep"이 구조에서 저절로 성립한다. ② **bounds를 두 번 좁혔고 둘 다 실측이 시켰다**: LUT 전 범위(4.0um)에서는 SLSQP가 L=1.86um로 가 diode 레퍼런스가 사이징 불가(5 start 전부 실패, 1465초), 선언된 L theta 상한(1.0um)으로 좁혀도 실패 -- **실현가능 L이 구멍 뚫린 집합**이기 때문(세션40이 이미 기록). ③ 그래서 `repair_infeasible_baseline()`을 고쳤다: **(theta,값) 단위 시도 기록**(같은 theta의 다른 값을 재시도 못 하던 버그 -- 병목이 같은 류의 다른 멤버로 간 뒤 멈췄다) + **L theta는 격자를 훑는다**. 4단계 복구로 x0 feasible. ④ **중복계산 전수검사**(사용자 지시, 프로파일 실측): `stack_kvl_vgs_limit`이 `load_topology()`를 호출마다(평가의 **99.3%**, 이미 부르며 **버리던 meta**를 보관해 해결), L2가 ω마다 네트워크 재조립(**28%**, `build_ac_network()`로 1회), `_query` 18,636회 중 **69.2%가 중복**(메모이제이션). **평가 1회 1,325ms → 72.9ms(18배)**, 탐색 1,465초 → 134초. **결과**: `mirror_ratio_error_pct` 13.96 → **3.64**(3.8배), cmrr 60.00 → 73.14, psrr 63.93 → 73.65, `parasitic_pm_deg` 70.12 → 77.37, gain_full 59.66 → 67.64. 파생 theta가 고른 L(0.445/0.573um)은 knee(0.245/0.340)보다 위 -- sweep이 시작점보다 나은 점을 실제로 찾았다. self-test 둘 다 exit 0 / diff 0줄 |
| **4.39** | 2026-09-10 | **`_L_ROLE_MULTIPLIERS` 완전 제거**(사용자 지시 "bias_replica 상수도 없애" -> 전 회로 적용). ① 남은 상수 `bias_replica: 1.2`가 실제로 정하던 건 **파일럿 4소자**(class-AB 배터리 diode)뿐이었고, 그 값의 근거를 mismatch 선언/knee/소자별 W 실현가능성 세 방향으로 찾았으나 **셋 다 없었다**. ② `derive_role_L()` = `clamp(목표점, feasible_L_window(선언 W_bounds + 그 소자의 실제 ID))` -- 새 상수 없음. **role은 '어떤 측정을 쓸지'만 고른다**(`_L_ROLE_TARGETS`): `mirror`는 knee(출력임피던스 극대화), `bias_replica`는 창 하한(§7.10이 선언한 목적이 PVT 완화이고 gain 요구가 없으므로 면적 최소). 등록 안 된 role은 ValueError. 판정 술어는 `lut_vdsat_headroom()` 안 인라인 코드를 `feasible_gm_ids()`로 꺼내 공유. **한 번 두 role을 합쳤다가 실측이 되돌렸다** -- 둘 다 knee로 두자 배터리 diode W가 125.4/123.4um(비 1.0157)로 나와 `assign_finger_geometry()`가 공통 finger 폭을 못 찾아 파일럿이 **레이아웃에서** 죽었다(SLSQP는 수렴했다 -- self-test만 봤으면 못 봤다). ③ **diode는 gm_id가 자유롭지 않다** -- self-test 픽스처 `Mo`가 "가능"한 L에서 W=0.824um로 하한을 깨며 잡아냈다(`knee_L_for_kind()`가 이미 기록한 반례). 새 판정을 만들지 않고 **기존 `diode_vds_window()`**로 분기(vds가 고정됐으면 그 vds가 강제하는 gm_id로 W를 직접 계산). ④ **theta로 파생하지 않았다** -- 주인 없는 동치류까지 theta로 만들면 파일럿 자유변수가 24->39(실측)로 늘어 SLSQP가 느려진다. 유도값은 결정적이라 자유도를 안 늘리고, 설계 자유도가 필요한 곳은 층3이 이미 theta로 노출했다. ⑤ **폴백 없음** -- 근거(격자 3종)가 없으면 값을 지어내지 않고 즉시 ValueError. 4개 회로 전수 **상수 폴백 0건**; self-test toy 픽스처 6개는 `_tst_grids()`로 실제 spec과 같은 모양으로 맞췄다(엔진에 새 폴백 없음). ⑥ **전수 측정**: 값이 달라진 소자는 파일럿 **5개**(bias_replica 4개 0.180->**0.245**um -- diode 인식 창이 옛 0.180um을 실현 불가능으로 걸러냈다, M37b clamp 0.245->0.350um), folded_cascode는 13개 전부 **무변경**, 나머지 2개 회로는 세션41 이월 항목에서 먼저 실패(변경 전후 동일). `derive_class_L()`은 3개 회로 15개 류에서 실제 호출되나 현재는 소자별 유도와 값이 일치(무동작) -- 갈릴 가능성에 대한 불변식 보증으로 남긴다. ⑦ self-test는 clamp가 **위/아래 양방향으로 실제 값을 바꾸는지**를 assert한다(무동작 게이트 금지). `select_L_by_role()`의 cascode/signal 가드는 `derive_role_L()`로 이관 -- 옛 함수는 self-test 에서만 불렸는데 이제 실제 사이징 경로 위에 있다. self-test 둘 다 exit 0. ⑧ **end-to-end 재탐색은 파이프라인 끝까지 가지만 착지가 v4.38보다 나쁘다**(power 231.17->238.94, cmrr 73.14->64.36, mirror_ratio 3.64->17.67). **유도가 아니라 탐색 착지 문제**다 -- v4.38의 theta_star를 새 엔진으로 평가하면 여전히 실행가능하고 더 좋다(power 231.2). 정본 `n_starts=3` 중 1개만 수렴했다. 다음 과제(`search_stage_budget_L_warm_start()`에 `l_class` 포함, §10.10에 이미 기록)가 정확히 이 x0 문제를 겨냥한다 -- 정본 탐색 파라미터를 임의로 올려 덮지 않았다 |
| **4.40** | 2026-09-10 | **웜스타트에 `l_class` 포함**(사용자 지시). ① 타입 추가로 끝나지 않는다 -- 실측: `l_class`에 걸리는 제약은 **전부 footprint가 "ALL"**(cmrr/psrr/parasitic_pm_deg)이라 기존 LUT-only 고속경로 두 갈래의 전제가 성립하지 않는다(그냥 넣었으면 bounds-midpoint로 후퇴해 **무동작**). 실제 `evaluate()` 조인트 스캔으로 보낸다. ② 웜스타트가 정한 theta는 SLSQP 자유변수에서 빠지는데(`held_names`), `l_class`가 얼면 층3이 만든 설계 자유도가 사라진다 -- `presolve_warm_start()`에 **`l_class_L`** 신설해 x0만 주고 자유변수로 남긴다. ③ **되돌림 1**: 점수를 선언된 `objective`(power 최소)로 뒀더니 x0가 `L_class__M68` 하한(0.15um)에 붙고 착지 `mirror_ratio_error_pct`가 **43.45%**(v4.38: 3.64) -- 미러비 오차는 `V_A∝L`에 반비례라 층3의 존재 이유를 거스른다. **선언된 제약의 최소 여유 최대화**(내부점, `_group_score_interior()`)로 교체(정규화 분모가 제약값 자신이라 새 상수 없음). ④ **되돌림 2**(프로브가 잡았다): 점수를 바꿔도 `L_class__M68`이 자유변수에서 빠졌다 -- 자유변수 필터의 두 번째 조건인 `graph[...]['classification']`이 **`baseline` 주입 직후 그 점에서** `isolated`로 뒤집혔다. `baseline`에는 **고정될 theta만** 주입하도록 고쳐 2/2가 자유변수로 남는다. ⑤ **결과**(웜스타트 전 대비 전 항목 개선): power 238.94 → **231.17**, gain_db 60.42 → **61.56**, mismatch 2.795 → **1.334**, gain_full 63.26 → **67.08**, cmrr 64.36 → 72.55, mirror_ratio 17.67 → 7.13. L_class 0.511/0.474um. v4.38 대비 목적함수 동률 + gain/mismatch 개선, area 17% 증가. self-test 둘 다 exit 0, floorplan/full_circuit_audit 통과. ⑥ `mirror_ratio_error_pct`는 여전히 **제약이 아니다** -- 관측값 3.64/7.13/17.67/43.45%. 상한은 설계 결정이라 사용자 확정 전까지 안 건다 |
| **4.41** | 2026-09-10 | **미러비 계통오차 상한 -- 숫자를 박지 않고**(사용자 지시). ① **내가 먼저 틀렸다**: `mirror_ratio_error_pct <= 8.0`을 박았다. 유도(선언된 5.0mV × 입력쌍 gm_id 16.00/V)를 주석에 적었지만 **결과를 박는 순간 유도는 문서일 뿐 코드가 아니게 된다** -- gm_id가 바뀌어도 8.0은 안 따라간다. §10.11에서 없앤 `_L_ROLE_MULTIPLIERS`와 같은 형태의 상수를 같은 세션에 다시 만든 것이고, 사용자 지적으로 원칙에 못박았다(메모리 `feedback-never-invent-constants-derive-and-cache`). ② **해법은 단위 맞추기**: 계통 오차를 **입력환산 전압**으로 재면(`dV=(dI/I)/(gm/ID)`) 랜덤 예산과 단위가 같아져 임계값을 `value_from_constraint: mismatch_sigma_mV`로 **참조**하면 끝난다 -- 제약에 숫자가 0개이고, 이 회로에 남은 선언 숫자는 `mismatch_sigma_mV = 5.0` 하나다. ③ 신설: `_mirror_ratio_error_pairs()`(쌍별 표를 `ctx.derived`에 **한 번** 계산해 pct/mV 두 metric이 공유), `_metric_mirror_ratio_error_input_referred`, `resolve_constraint_references()`(인라인 해석을 함수로 빼고 `value_from_constraint` 추가, 참조 연쇄 금지). ④ **부수 소득**: 박은 8.0%는 물리적으로도 틀렸다 -- 최댓값 쌍 M10/M12의 gm_id는 22.50/V인데 입력쌍 16.00/V를 적용했다. 제대로 환산하면 8.215% = **3.65mV**로 예산 안이다. 구속력은 유지(17.67% → 7.85mV, 43.45% → 19.3mV 전부 탈락). ⑤ self-test: 환산 동작 + 캐시 공유 + **거부 3종**(참조 없음/연쇄/value 충돌). 저장소 자체 게이트도 새 타입 미등록을 잡아 등록. ⑥ **결과**: 착지 무변경(power 231.17 등 v4.40과 동일), `mirror_ratio_error_mV = 3.186mV`로 예산 5.0mV 대비 **36% 여유** -- 설계를 바꾸는 제약이 아니라 탐색이 이 축을 희생하려 할 때 막는 가드다. self-test 둘 다 exit 0 |
| **4.42** | 2026-09-10 | **입력환산 오프셋 + 달성 가능 임계값 유도 + CircuitGraph baseline**. ① 사용자 지적으로 발견: 파일럿은 current-reuse라 **M4a/M4b(NMOS)도 같은 입력에 물려 있고** `matching_pairs`도 이미 `offset`으로 선언돼 있는데 metric이 `devices:[M1a,M1b]` **한 쌍만** 세고 있었다(사이징 쪽은 Eq.5 `gm1=gmn+gmp`로 **이미 반영**돼 있었다 -- metric만 빠졌다). ② 새 metric `input_referred_offset`: 쌍을 **선언에서 찾고**(`matching_sensitivity==offset` + 게이트가 `ports`의 input net) **gm 가중 RSS로 입력환산**(사용자 확정). 실측 2.795 -> **1.651mV**. 파일럿 offset 쌍 3개 중 CMFB 오차증폭기가 `ports` 필터로 정확히 빠진다. 쌍 하나인 회로는 정확히 환원 = 무동작. 기존 소비자 셋(`_metric_device_footprint`/`make_matching_feasibility_check`)을 조용히 끄지 않으려고 **빌드 시 한 번** `devices`/`_pairs`를 적어 넣고, 쌍별 가드가 전체 조건의 **충분조건**임을 증명해 docstring에 남겼다. ③ `mismatch_sigma_mV=5.0`(근거 없던 값)을 `achievable_metric_bound()`로 유도 **시도했고 실패했다 -- 실패가 답을 줬다**: sigma를 최소화하면 W*L이 커져 `parasitic_pm_deg`와 정면충돌해 실현가능점이 사라지고(3 probe 전부), 제약을 떼면 최적화기가 입력쌍을 줄여 sigma가 오히려 나빠진다(세션31 실측 4.7배). **즉 이 임계값은 회로 안에서 도출되는 값이 아니라 시스템 레벨 오프셋 요구에서 와야 하는 설계 입력이다** -- 내가 제안하고 사용자가 고른 '달성 가능 상한에서 역산'이 이 metric엔 성립하지 않음이 측정으로 드러났다. 값을 지어내지 않고 5.0을 유지하되 **유도를 시도했고 왜 실패했는지**를 두 회로 선언에 적었다. 미구현 후보: 제약값 자체를 **bisection**해 '탐색이 아직 실현가능한 가장 빡빡한 sigma'를 찾기(두 실패를 모두 피한다). ④ **실측이 세 번 되돌렸다**: probe를 n_starts=1로 깎아 전부 실패 / 참조 제약 붕괴 / **런타임 참조 방식이 self-test 픽스처를 줄줄이 깨뜨림** -> 유도 스크립트가 결과를 **선언에 기록**(`value`+`_derived` 지문)하고 지문 불일치는 빌드를 죽이지 않고 기록만 남기는 방식으로 전환. **재탐색 실측: 착지 무변경**(power 231.17 등 v4.41과 동일), `mismatch_sigma_mV`만 1.334 -> **1.090**(정의가 바뀌어서) -- 임계값 5.0이 여전히 안 걸리므로 정의 수정 효과는 **임계값이 근거를 얻은 뒤에야** 나타난다. ⑤ **§11 CircuitGraph baseline 신설**(사용자 지시): 같은 넷리스트를 각자 훑는 함수 12개 전수 조사 -- 특히 `propagate_node_voltages()`가 **전 노드 DC 전압을 계산해 버린다**. 노드/엣지 스키마를 소비자에서 역산하고, **신호 전파방향을 노드에 기록해 stage 탐색이 항상 input->output**으로만 돌게 한다(사용자 지시 -- 역방향은 피드백에서 순환에 빠지고 단 판정을 모호하게 한다). **L1 정적/L2 평가별/L3 지속 3층 분리**가 핵심(안 지키면 평가 간 오염). ⑥ **정직한 한계 기록**: 다중 diff pair 세 경우 중 **A(병렬)만 맞고 B(cascade 입력환산)는 틀리며 C(CMFB 쌍)는 재는 metric이 없다** -- 공통 원인은 '몇 단째인가'를 사람이 적고 있다는 것이고 `stage_index` 유도가 그 열쇠다 |
