# card 묶음 독립 판정 (2026-11-04)

대상: design/v1164 `60d008d0`(master `0d99a813` 대비 diff), card UB-1 + NL-1, TB-1, GC-1, card C의 spec·interface, 위임 A-30·A-32·A-34~A-36.

방법: 문서 읽기와 `git show`·`grep`. 실행 없음. 엔진 인용은 재작성 범위·호출 자리 확인뿐이다(원칙 8). 손계산은 toy 닫힌 식을 직접 유도해 대조했다.

## card별 판정

| card | 판정 | Major | 비고 |
|---|---|---|---|
| UB-1 + NL-1 | V1 정정 뒤 코드 가능 | V1 | toy 닫힌 식은 맞고 FF·§2.5 물리도 맞음 |
| TB-1 | V2·V3 정정 뒤 test 가능 | V2, V3 | interface만으로 기대값을 못 냄 |
| GC-1 | V4 정정 뒤 가능 | V4 | 픽스처·키는 판정 가능. 재측정 규칙에 구멍. GD 정정 필요(아래) |
| card C | **가능**(base 조건 B-1·B-2 뒤) | 0 | m1·m2 |

GL-1 래칫 새 키(IT I2 꼴): 네 card 모두 새 키를 만들 구조가 없다. TB-1만 주의 한 줄(m3). GC-1은 `tests/` 안이라 대상 밖이고, card C의 `S3Index`는 허용 모듈이다.

## Major

**V1. UB-1 C-13: 내부 ¼·½·¾ 점이 끝값을 넘을 때만 세분하면 상한이 깨진다** (fail-open, 구현 불가)

- 단봉 가정 아래에서도 극값이 끝 가까이 있으면 놓친다. 예: 구간 [0, 1], 극값 0.1, f(¼)·f(½)·f(¾) ≤ f(0). 세 점 모두 끝값 이하라 세분 없이 `certified`가 되고, 인증 값이 실제 최댓값보다 낮다. E-16 정의('bin 안 최댓값이어야 상한')를 어기고 거짓 `INFEASIBLE_TARGET`으로 갈 수 있다.
- ¼·¾은 선언에서 유도하지 않은 표본 수 상수다(원칙 11). 규칙 D도 `4` 리터럴을 막을 수 있다(`check_d`의 허용 목록은 확인하지 않음, 메모리 기록 '0·1·-1·산술 2').
- **고칠 문언**(interface C-13, 41 §2.5-9 E-16 세분 문장도 같은 뜻으로):
  'C-13 `block_gain_bound` E-16: 연속 축 세분 뒤 최대 행의 각 L 축에서 같은 bin의 이웃 앵커 구간(`tables.same_l_bin`이 그 축 소자 kind 모두에 참)마다 기존 연속 축 세분과 같은 단봉 최대 찾기(`_TOL` 기준, 새 상수 0)를 `row_gains(..., cont={L축: 값})`로 **늘** 돌린다. 결과 > 끝값이면 `a_max_db`·`row_condition` L 값을 올린다. 찾기 중 NaN이면 `unknown`/`bin_interior_unchecked`. bin이 다른 구간은 안 본다. 구간 안 단봉 가정(§4.2 N5).'
- T-5·T-5a·T-5b·T-5c 기대는 그대로 맞는다. T-5d를 더한다: 'T-5d 끝 근처 극값 | 앵커 평탄, 극값이 구간 폭 ⅛ 이내인 포물선 | `a_max_db` ≈ 그 극값(¼ 표본이면 끝값 -- 옛 안 red) | red'. T-5a '`lookup_at_l` 호출 0'은 유지, T-5c는 호출이 있어도 값 그대로로 읽는다.

**V2. TB-1 interface: `theta_class` 서명과 선언 사실 칸 이름이 없다** (구현 불가, 소스 없는 test)

- `theta_class(snapshot, <선언 사실>, *, donors, counters)`는 자리표다. T-T1이 호출하거나 `DcInputs`로 넣을 이름이 interface에 없다. design은 `has_gbw_target`·`has_rout_limit`·`has_settling`으로 정했다(D40 §2.4.8, J-T1).
- **고칠 문언**(§1 코드 블록과 그 아래):
  ```text
  theta_class(snapshot, has_gbw_target, has_rout_limit, has_settling, *, donors, counters) -> GraphSnapshot   # bool 셋 = 블록 extras
  DcInputs 칸: has_gbw_target, has_rout_limit, has_settling (bool, 값은 읽지 않음)
  ```
  '`build_kernel_context`가 `DcInputs`의 세 칸을 넘긴다. PM 선언은 입력이 아니다. T-T1의 PM 유무 조합은 분류 불변을 단언한다.'
- spec '신규 시그니처'의 `<선언 사실>`도 같게 고친다.

**V3. TB-1 interface: '정준 위치'와 '대칭 궤도 대표'가 정의되지 않아 T-T3·T-T4·T-T6 기대값을 유도할 수 없다** (틀린 기대값 위험)

- interface는 어느 쪽이 '앞'인지, 무엇을 읽어 비교하는지 적지 않았다. design 40 §3.7-4도 궤도 대표를 정의하지 않고, 정준 위치 단독 필드는 없다. `device.dc_colour` = (wl, 정준 위치) 순위뿐이다(§2.4.8).
- **고칠 문언**(§2 '`kvl_branch` 고리' 앞, 40 §3.7-4 (a)에도 같은 한 줄):
  '**정준 위치 키** = `device.dc_colour` 오름차순(§2.4.8, 정점마다 유일·이름 무관). 표의 "앞" = 값이 작은 쪽. **궤도 대표** = `graph.orbits`에서 크기 ≥ 2인 궤도의 `dc_colour` 최소 멤버. toy는 `dc_colour`·`orbits`를 스냅샷 필드로 직접 넣어 순서를 정하고, 기대값은 그 값에서 손으로 낸다.'
- 뜻 결정은 작성자 판단(위임 기록 필요). 대안은 정준 위치 단독 필드 신설인데 소비자가 이 키뿐이라 graph 규칙 3에 비춰 택하지 않는다. wl이 다른 후보끼리 정준 위치 단독 순서와 갈릴 수 있으나 둘 다 이름 무관이라 metamorphic 조건은 성립한다.

**V4. GC-1 '기준선은 그 master에서 다시 잰다'가 앞선 card의 새 위반을 부채로 흡수한다** (fail-open)

- spec S-8은 HC-1 바로 앞 master에서 재측정하고 '최초 값이라 기준 약화 아님'으로 적었다. 그러면 IT·EO-1·card C·TB-1·HC-S가 만든 reader 없는 필드·칸이 규칙 L 위반 없이 부채가 된다. GC:663과 GD §3의 '새 필드에 부채 항목을 줄 수 없다'를 우회한다.
- **고칠 문언**(spec S-8 끝, interface '`PARAMS` 값' 끝):
  '재측정은 검증자 독립 스크립트로 한다. `7620f5ee` 390항목 대비 **늘어난 키마다** 원인 card와 근거(소유표 소비자 또는 출력 전용 행)를 판정 기록에 적는다. 근거 없는 새 `L-1`·`L-2`·`L-4` 키는 부채로 넣지 않고 멈춰 그 card로 되돌린다. 줄어든 키는 사유만 적는다. 현재 엔진 test 3·4의 키가 앞 card로 사라졌으면 같은 표 근거로 그 줄을 뺀다(약화 아님, 해소).'

## 물리·기대값 대조(손 유도, 모두 맞음)

- T-1 CS → CG: g_in = gm2 + gmb2 + gds2, A·B gain·zout. T-2 비율. T-3·T-3a·T-3b. T-4 D = C1 + C2 + cgs + cgb + cgd(1 + gm·R'). T-7 캐스코드 gain·zout. T-9 follower. T-9a. T-10.
- **FF gds 유지(A-35)**: merge 넷 KCL에 gds가 탭 전압과 무관하게 있으므로 맞다. 호출도 맞다. `block_residual._cascade`·`ff_gm_ratio._one`은 merge 블록 FF를 이미 `extra`로 넘기고 탭을 구동에서 빼면 gm 항이 0이 된다(`master` `block_residual.py:50-58`). 그래서 'exclude·extra 의미 유지'로 충분하다. SPICE·원문 미대조이고 회로 해석을 위임으로 정한 표지는 그대로다.
- **§2.5 스탬프**: 비멤버 단자 스탬프(G1), gate 독자가 있는 막다른 넷 유지(G2), 남의 블록 넷 멈춤(G3) 모두 ω → 0 KCL과 맞다. 행 모드 0 + 사유도 상한으로 건전하다(C-4, 되먹임 없는 블록).
- **card C**: 경계값은 §1 정의에서 유도된다.
- **graph**: 네 card에서 writer 둘·둘째 생산자를 찾지 못했다. `dependent_facts`(writer `s1v_fields`)와 `theta_class`는 소비자 있음.

## GD §2·§3 초기안 차이(A-32): design 정정 필요

필요하다. 구현이 design과 다르면 design부터(원칙 17). GD는 '다르면 GC-1을 멈춘다'고 적었고, A-32가 그 멈춤을 푼 값이 GD에 없다. 정정 문언(`graph-consumption.design.md`):

- **§1 머리 줄**: '엔진 운영 코드 변경 0. `rule_l_checks.py` = code, `rule_l_tables.py`·`rule_l_debt.py`·test·픽스처 = test(A-32 J-1).'
- **§2 진입점 표**: 표를 '진입점 11개 = card interface `PARAMS.entry_points`(A-32 S-1, 측정 근거 spec S-1). 초기안 4개는 이력으로' 한 줄로 바꾼다.
- **§2 출력 함수**: '출력 함수 5개 = `_ach_body`, `_coupling_report`, `structure_tables`, `orbit_matching_crosstab`, `_from_snapshot`(A-32 S-2). `node_across_front`는 진입점이다.' 끝 문단 '미측정 초기안'은 '`7620f5ee` 실측, 병합 base에서 재측정'으로.
- **§3 동적 접근**: '허용 파일 넷 = `core/graph_snapshot.py`, `core/projection.py`, `core/graft.py`(core 접근자), `sizing/seal_versions.py`(봉인 판 검사) -- 계획 N3.1-1의 두 부류. 늘리지 않는다. 기존 9함수는 키 `("L-1d", "모듈.함수")` 부채, card GC-7(A-32 S-3).'
- **§3 GD-14**: '함수·메서드·클래스(A-32 S-5).' **L-4 대상** = spec 계약 6(S-7).
- **§3 항목 키 줄**: 키 표 정본 = interface '위반 키와 code', L-1d 추가.
- **병합 자리**: 'HC-1 + GC-8 바로 앞(A-32 S-8), 재측정 = V4 문언.'

## 정정 문언 요청분

**42 D-TB1a**: '입력 = S1v `Block.roles`·spec 선언 사실·L 동치류(`device.dc_coord` 읽지 않음, topology 태그 READS 0)'를 다음으로 바꾼다.
> 입력 = S1v `Block.roles`·`DcInputs` 선언 사실 유무 칸(`has_gbw_target`·`has_rout_limit`·`has_settling`, 값 안 읽음 -- J-T1). `device.dc_coord`·L 동치류·topology 태그 READS 0(L 동치류는 S/B/F 정의에 소비처가 없음 -- 규칙 L-3)

계획 N6.29 범위 1의 'L 동치류'는 계획 후속 정정 표지로 둔다(D40 표지와 같음).

**40·41 Status**(지금 '승인됨'과 '묶음 ④ -- 검증 전', '묶음 ⑥ 초안'이 한 줄에 함께 있다). 머리 줄을 다음으로 바꾼다. 끝의 옛 Status 인용은 파일별 그대로 둔다(40 = H40-39, 41 = H41-38).
> **Date**: 2026-11-04 · **Status**: **design v1.16.4 -- 계획 기준 = v6.38.8(master `c0b41eee`, 승인 A-25).** **승인(O-226 위임 A-27, v1.16.3)**: 묶음 ②(IT-1·IT-2·TB-1·UB-1 + NL-1·범위 나눔), ④(HC-S·HC-1·GC-1·GC-8), ⑥(EO-1, SF-1 로더 조각), card C 정정. **v1.16.4 card 후속(UB-1 A-35·A-36, TB-1 A-34, IT A-33 J4, rule_hash 공통 규칙) = 독립 판정 `cards_batch_validation.md` 문언 반영 뒤 채택.** **미승인**: ① LA-1a(§6.9, '보류 중' 표지), ③ WB-1(Q-W1 기본안 뒤 재검증). 자리: HC-S·HC-1 = `headroom-chain.design.md` v0.1, GC-1·GC-8 = `graph-consumption.design.md` v0.1, EO-1 = 41 §4.8·§4.9(40·41·42 같은 판).

## Minor (막지 않음)

- m1. **'새 실패 0' 합격 문언**: TB-1 T-3, card C C-3는 N6.3 '0 failed'보다 약하고 A-31은 아직 master에 없다. '전체 0 failed. 남으면 목록을 올리고 판정을 멈춘다'로.
- m2. **card C §1**: `front_budget_s` 자리가 없어 가짜 `sctx`를 만들 수 없다. 'D = ⌊`sctx.settings.front_budget_s` / 평가 시간 중앙값⌋, `sctx.settings.eval_budget`'로 적는다.
- m3. **TB-1 G-8**: `ThetaClass(...)`를 모듈 수준에 두면 `vt_assign` 새 키다. `writer_plan` 재작성에서 새 클래스의 가변 속성도 새 키다. interface §6 T-4에 '`ratchet.new` 0, 모듈 수준 `ThetaClass` 상수 없음'.
- m4. **UB-1 판정 측정 표 없음**: interface·spec에 N6.3 넷과 `ratchet.new` 0, 13회로 보류 문구를 적은 audit 표가 없다(spec 판정 유형에 일부). TB-1 §6 꼴로 한 표 추가. `structure_rule_fp` 대상 파일 grep(공통 규칙)도 넣는다.
- m5. **`nodal_solve` 소비자**: charge 주입이 `(None, None)`이 되면 EO-1 `ss_off_delta`(41 §4.8-5 3)가 사유 없이 깨진다. UB-1 재작성 범위에 'None = `off_delta_undefined`'를 더한다. `kvl_sensitivity`는 계약이 이미 None을 받는다.
- m6. **용량 결측 + 전하 노드**: `ss_nodal` '용량만 결측 = `NodalSystem`'과 NL-1 전하 행이 만나면 C 일부로 푼다. '전하 노드에 닿는 용량이 결측이면 `lu=None` 또는 `passive_value_undeclared`' 한 줄과 toy. library 0/13.
- m7. **`capacitance_matrix` 호출**: `block_local_gain`에서 블록마다 전회로 C를 다시 조립하지 않도록 '전하 넷이 있을 때만'을 적는다(블록 안 재계산).
- m8. **TB-1 T-T5** 'red 또는 사유 기록'은 판정이 흐리다. red가 안 나면 green 유지로 적고 이유를 쓴다.
- m9. **TB-1 §5**: 비어 있는 동안 T-T12를 동결하지 않는 것은 맞다. 표를 채우는 주체가 오케스트레이터이므로 작성자 ≠ 기대값 분리를 판정 기록에 적는다.
- m10. **FF 문언 잔재**: 41 §1.12.2-4·§5.1이 '스탬프 안 함'으로 읽히는지 이 판정에서 대조하지 않았다(아래 미확인).

## 미확인

- UB-1 `ub0_code_compare.md`, `toy_hand_check.py`, GC-1 `baseline_items.jsonl` 내용 재측정. card C spec 뒷부분은 grep으로만 봤다.
- 41 §1.12.2-4·§5.1 문언 대조, `check_d` 허용 리터럴 원문, GD와 N3.10 상위 개정 대조.
- ⑩ 결정 간 모순 점검은 O-225로 하지 않았다.

쓰기: 이 파일 하나.

verdict: Major 4
