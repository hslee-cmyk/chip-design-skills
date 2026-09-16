# plan v5.16 독립 검증 (검증자 판정, H1 정정판)

- 대상: 작업본 plan(1132줄, 커밋 전. v5.15 = 커밋 4913fac 대비 23/23). 신규 회로 커밋 5459a44.
- **판정: 커밋 가능.** 막음 0, 높음 0, 중간 2, 낮음 2.

## 0. 앞 판의 H1 철회 (검증자 오류)

- 앞 판에서 "topology의 `_paper_target_spec.supplies_v`가 1.2 V이므로 plan의 '사용자 결정 1.8 V'는 사실오류"라고 적었다. **이 지적은 틀렸다. 철회한다.**
- 원인: `_paper_target_spec`을 JSON 들여쓰기로 덤프하면서 출력 1,800자에서 잘라 읽었고, **`sky130_supplies_v` 키가 `design_example` 뒤에 있어 잘린 구간에 들어갔다**. `.topology.md`에 "1.8"이 없다는 사실은 그 md가 connectivity만 렌더링하므로 근거가 되지 못한다 -- 이 두 가지를 근거로 오판했다.
- 재확인(전체 키 출력): `_paper_target_spec` 키 = [process, supplies_v, loading, performance_targets, design_example, **sky130_supplies_v**]. `supplies_v` = {vdd 1.2, gnd 0, "논문 VDD=1.2V"}, **`sky130_supplies_v` = {vdd 1.8, gnd 0}**이며 주석에 사용자 결정 원문("2는 1.8에 맞춰")과 ICMR 재계산 근거(VDD/3 → 0.6 V)가 있다. `performance_targets.icmr_v` = 0.6(1.8 V 기준). 작업 트리와 커밋 5459a44 내용이 같다(library 경로 로컬 변경 0).
- 따라서 **nmcnr과 같은 분리 방식(논문 값 / sky130 확정 값)이 이미 적용돼 있고**, plan U-34의 "sky130 재설계 전원 1.8 V(사용자 결정)"은 파일과 일치한다.

## 1. 사실 대조(정정 후)

| plan 서술 | 파일 | 일치 |
|---|---|---|
| 소자 16, Cm1 V1–Vout·Cm2 V2–Vout·CL Vout–gnd | 동일 | 예 |
| `supply_nets` vdd·gnd, `ports` Vinp/Vinn/Vout | 동일 | 예 |
| 단 구성·미러/차동쌍 후보(VBP{M0,M5,M12}, ND{M3,M4,M6B}, NX{M6A,M7}, V1{M8,M14}, NP{M9,M10}, TAIL{M1,M2}) | 게이트·소스 전부 일치 | 예 |
| 사이징 스펙 미선언 | `sizing_roles`·`device_roles`·`compensation` 모두 null | 예 |
| 문서 전용 목표 스펙: sky130 1.8 V(사용자 결정)·CL 10 pF·GB 10 MHz·PM 63.4°·ICMR ≥ 0.6 V | `sky130_supplies_v` 1.8 / `loading.CL_farad` 1e-11 / `gbw_hz` 1e7 / `pm_deg` 63.4 / `icmr_v` 0.6 | 예 |
| DEC-81 발동 조건 | Vout에 M7(g NX)·M13(g V2)·M14(g V1) drain 합류, 입력→Vout 신호 사슬 셋(V1→M14 / V1→M8→NP→M10→V2→M13 / ND→M6B→NX→M7). 합류 노드가 출력 포트이자 전류 구동 | 예(발동 1회로) |

잔존 검사: "library 7"·"7개 회로"·"4/7" 0건, "발동 0" 12곳은 전부 다른 분기 문장, U-34 확정·DEC-81 상태·N1.2 삭제·J12 신규 항목·이월 3건 모두 주장 위치에 있다.

## 2. 지적 표(정정 후)

| # | 분류 | 심각도 | 위치 | 내용 | 수정 제안 |
|---|---|---|---|---|---|
| M1 | 누락 | 중간 | MG0(N3.16), N6.2 0.5 DoD, U-34 | `ngcc_3stage_ff`의 사용자 확정 값도 nmcnr처럼 `_paper_target_spec` 안의 `sky130_supplies_v`에 있다. 그런데 MG0 목록은 "`_paper_target_spec` → `_declared_target_spec`(**사용자 확정 스펙 세 회로**)"와 "**nmcnr** `sky130_supplies_v` → `_declared_target_spec.supplies_v`"만 적고, 0.5 DoD도 "**세 회로**의 `_paper_target_spec` 컨테이너명 0"이라 **ngcc가 계수에서 빠진다**(조용히 옛 이름으로 남는다) | MG0에 "`ngcc_3stage_ff` `sky130_supplies_v` → `_declared_target_spec.supplies_v`"를 추가하고 0.5 DoD의 "세 회로"를 "해당 회로 전부"로 바꾼다 |
| M2 | 모순 | 중간 | N4.3 표, N6.2 0.5 DoD, N9.1 `05-role-separation` | v5.15가 공격 **13**을 신설했는데 0.5 DoD는 "공격 **12**건 거부 로그", N9.1 05-role은 "공격 **12** + 사례 5"로 남아 있다. 게다가 공격 13은 GB0 로드 게이트(6a 구현)를 대상으로 하므로 0.5에서 실행할 수 없다 -- 숫자만 어긋난 게 아니라 **실행 Phase가 다른 항목**이 한 표에 섞여 있다 | N4.3 표에 공격 13의 실행 시점을 적고("GB0 로드 게이트 구현 뒤 = 6a, IC11 선행 조건"), 0.5 DoD·N9.1은 "0.5에서 12건, 공격 13은 6a"로 맞춘다 |
| L1 | 누락 | 낮음 | DEC-81 상태, DEC-59 | ngcc는 **발동** 회로이지만 J12 ratify 전에는 **검증 발동**(발동 + ratified 대조표 일치 + 계산 규칙 있음)이 아니라 DEC-59 정지가 유지된다. 이 단계 구분이 상태 열에 없다 | 상태 열에 "(J12 ratify 전에는 검증 발동 0이라 DEC-59 정지 유지)" |
| L2 | 잔여 | 낮음 | U-34 | U-34가 값만 적고 **필드 이름을 적지 않아** 읽는 사람이 `supplies_v`(논문 1.2)와 `sky130_supplies_v`(사용자 1.8)를 구분하기 어렵다(내가 오판한 경로가 그대로다) | "문서 전용 목표 스펙: `supplies_v` 1.2 V(논문) / **`sky130_supplies_v` 1.8 V(사용자 확정)**, CL 10 pF…"처럼 필드 이름을 병기한다 |

## 3. 검사 항목별 결론

- **(1) U-34 서술**: 두 필드 구조와 값이 맞다. 다만 필드 이름 병기가 낫다(L2).
- **(2) M1·L1**: 둘 다 유효하다. M1은 앞 판에서 "사용자 확정 스펙이 `_paper_target_spec`에 들어갔다"고 적은 취지 그대로이며, 실제로는 nmcnr과 같은 구조라서 **문제는 이름 규칙이 아니라 MG0 목록·DoD 계수 누락**이다(그에 맞게 다시 썼다). L1은 그대로다.
- **(3) 남은 막음·높음**: 없다. (a) DEC-76 ↔ DEC-81 상태 정합, (b) 회로 수 갱신과 착수 조건(U-08 8개 중 3개, U-26 8개 중 ngcc만 선언, 기본 전달 뷰 5/8), (c) 기둥 62 근거 하향("측정한 회로에서는", ngcc는 6a에서 함께 측정), (d) J12-d 갈래와 U-34 닫힘은 서로 모순이 없다.

## 4. 판정

**커밋 가능.** M1·M2는 커밋과 함께 또는 Phase 0.5·6a 착수 전에 정리할 항목이고, L1·L2는 문장 한 줄씩이다.
