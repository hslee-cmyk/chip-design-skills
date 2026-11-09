# B26 계획 정정안: DEC-60 넷 전환기 종료 + DF-19·DF-26을 MG1에서 분리

대상 = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(v5.19, gate `master` cd64170), 이력 = `gain-budget-gmid-sizing.history.md`.
쓰는 주체 = 오케스트레이터(N3.12.2 `docs/01-plan/**`). 이 정정은 **판정 표(`plan_tables_hash` 입력: N4.1 `담당 Phase`·`강제 test`, N4.2 `도입`, N6.1 `Phase` 열,
N3.12.2)를 바꾸지 않는다**. 아래 대상은 N2 결정표·N3 표·N3.16·N5.2·N6.1 `범위` 칸 글뿐이고, `plan_tables_hash`는 정정 전후가 같아야 한다(커밋 전 `merge_gate.py plan-tables-hash`로
두 값을 재서 같음을 확인한다 -- 다르면 이 정정이 아니라 판정 표 변경이다).

B26-1 spec card(`draft_b26_1.spec.md`)의 착수 조건이다. 이 커밋이 들어간 뒤 card를 커밋한다.

## 0. 근거(원칙으로 정한 기본안 -- 사용자 결정 항목이 아니다)

1. **넷 전환기의 전제가 없어졌다.** DEC-60의 전환기 이름집합 해석은 "`supply_nets`가 없는 기존 4개 회로"를 위한 한시 조항이었다. U-26 (b)가 2026-09-17에 9/9 선언을 끝냈다
   (계획 1101행 "충족: 9/9 선언 완료"). 실측(cd64170): library 9회로 전부 최상위 `supply_nets` 선언이 있다(`_TEMPLATE`만 없음 -- 작성 틀이고 지금도 `load_topology`가 못 읽는다,
   `AttributeError: 'str' object has no attribute 'items'`).
2. **사용자 원칙**: 엔진 식은 topology 무관이어야 하고 이름 기반 `_DEFAULT_RAIL_*`는 정본이 아니다(메모리 "해결책은 반드시 일반화", 2026-09-30). 이름 집합 폴백을 남기면 원칙 위반이 살아 있다.
3. **넷과 전압은 다른 변경 단위다.** 넷 판정(어느 넷이 레일인가)은 topology만으로 정해지고 판정 입력이 이미 다 있다. 전압(`supplies_v`, 스칼라 `vdd` 폴백 삭제, IC11)은 U-26 (a)
   (기존 3회로 `supplies_v` 값 미확정)를 기다린다. 한 단위로 묶으면 넷 판정이 U-26 (a)에 묶여 Phase 4 끝까지 밀린다.
4. **Phase 3 전이 싸다**(`prep_b26_supply_nets.md` §3.5): 편집 파일 2개 vs Phase 3 뒤 6개 모듈. B26-1만으로도 `_RAIL_NETS`를 참조하는 함수가 cd64170 10개(P9 병합 뒤 9개)에서 3개(`trace_vdd_to_gnd_branches`·`trace_gnd_to_vdd_branches` = 초안 MOD3, `propose_theta_kcl_gap_fill` = MOD2)로 준다
   (Phase 3 초안이 `_RAIL_NETS`를 MOD7에 두면서 생긴 역방향 import 10건 중 남는 것은 이 3함수 몫이다 -- 상수 삭제는 B26-2·B26-4).

## 1. DEC-60 (254행)

원문(발췌 1):
> `supply_nets`가 없는 기존 4개 회로는 **전환기 이름집합 해석**으로 현 코드 이름 집합(정본 표 N3.16, DF-19·DF-26)을 쓴다. MG1(Phase 4) 전까지만 전환기 이름집합 해석을 쓴다: `supplies_v`가 없으면 레일 둘, 가장 높은 레일 = spec `vdd`, 가장 낮은 레일 = 0 V.

정정:
> 레일 **넷**의 전환기 이름집합 해석은 **B26-1(`<B26-1 card id>`)에서 끝났다**: library 9/9 선언(U-26 (b), 2026-09-17) 뒤로는 `supply_nets`가 없는 topology를 `load_topology`가 `ValueError`로 거부하고, 넷 이름 집합으로 대신 판정하지 않는다. 레일 **전압**의 전환기 해석(`supplies_v`가 없으면 레일 둘, 가장 높은 레일 = spec `vdd`, 가장 낮은 레일 = 0 V)은 MG1(Phase 4)까지 유지한다.

원문(발췌 2, 판정 입력):
> (ii) 선언이 없으면 전환기 이름집합 해석이 찾은 레일 수와 실행 spec 레일 전압의 부호다. 이름집합 해석으로 찾은 레일이 정확히 둘이 아니거나(`agnd` 같은 중간 전위 넷은 이 해석에서 레일로 읽히지 않는다) 레일 전압에 음수가 있으면 `supply_nets` 없이는 거부한다.

정정:
> (ii) `supply_nets` 미선언 -- B26-1부터 `load_topology`가 거부한다(로드의 첫 거부. 이름집합 해석으로 넘어가지 않으므로 레일 수·전압 부호를 셀 판정 입력이 생기지 않는다).

원문(발췌 3):
> 전환기 이름집합 해석은 **레일이 정확히 둘이고 그 이름 집합을 쓰는 회로에만 MG1(Phase 4)까지 한시 허용**한다.

정정:
> 레일 넷의 전환기 이름집합 해석은 B26-1에서 종료했다. 레일 **전압**의 전환기 해석은 **레일이 정확히 둘인 회로에만 MG1(Phase 4)까지 한시 허용**한다.

상태 칸 원문: `미구현(현 코드는 이름 집합, DF-19·DF-26)` → 정정: `부분 구현: 레일 넷 선언 접근자와 집합 판정(B26-1). 극성(B26-2)·MNA 고정 노드(B26-3)·이름 상수 삭제와 lint(B26-4)·레일 전압(MG1)은 미구현`.
(상태 칸은 B26-1 **병합 뒤** 바꾼다. 착수 전 정정 커밋에서는 발췌 1~3만 "B26-1에서 끝난다(병합 시점)"로 적고, 병합 뒤 상태 칸과 시제를 고친다.)

## 2. GB0 (314행), W0 (388행)

GB0 원문 발췌:
> `supply_nets`·`supplies_v` 선언 또는 전환기 이름집합·기본 해석(DEC-60: `supply_nets`는 library 회로 전부 필수이고 **레일 셋 이상·음전위 레일 회로는 미선언이면 여기서 거부**한다, 전환기 이름집합 해석은 레일이 정확히 둘인 회로에만 MG1까지 허용, 레일 셋 이상·음전위 레일이면 `supplies_v` 필수, `supplies_v` 넷 키 = `supply_nets`)

정정:
> `supply_nets` 선언(없으면 `load_topology`가 거부 -- B26-1)과 `supplies_v` 선언 또는 전환기 전압 해석(DEC-60: 전환기 전압 해석은 레일이 정확히 둘인 회로에만 MG1까지 허용, 레일 셋 이상·음전위 레일이면 `supplies_v` 필수, `supplies_v` 넷 키 = `supply_nets`)

W0 원문 발췌: `(미선언이면 DEC-60 전환기 이름집합·기본 해석 -- 레일이 정확히 둘인 회로에만 허용)`
정정: `(`supplies_v` 미선언이면 DEC-60 전환기 전압 해석 -- 레일이 정확히 둘인 회로에만 MG1까지 허용. 레일 넷은 `supply_nets`만 -- B26-1)`

## 3. N3.16 정본표 (769행), DEC-69 (263행), MG1 (802행)

769행 원문: `| 레일 넷 | `supply_nets`(list) | topology | sizing_recipe `_DEFAULT_RAIL_HI/LO`, `rail_nets`, stick_diagram `_RAIL_NETS` | MG1 |`
정정 마지막 칸: `B26(DF-19·DF-26 넷 몫, Phase 3 전 가능: B26-1 집합 판정·B26-2 극성·B26-3 MNA·B26-4 상수 삭제와 lint). metric 키 `rail_nets` 읽기는 B26-1에서 없앤다(옛 키 거부 게이트는 MG1)`

DEC-69 원문 발췌: `MG1 Phase 4(레일 코드)` → 정정: `MG1 Phase 4(레일 전압 코드. 레일 넷 코드는 B26 -- DF-19·DF-26)`

MG1 원문:
> | MG1 | 레일: topology `supply_nets`, spec `supplies_v`, `vdd` 유도 함수, 이름 집합 제거, metric 인자 `supply_nets`/`rail_nets` 정리. 옛 키 거부 게이트 + IC11 | code-author / test-author | Phase 4(DF-19·24·26과 같은 변경 단위) |

정정:
> | MG1 | 레일 전압: spec `supplies_v`, `vdd` 유도 함수, metric 인자 `supply_nets` 정리. 옛 키(계획 `supplies`, spec 스칼라 `vdd`, metric 인자 `supply_nets`·`rail_nets`) 거부 게이트 + IC11. 레일 넷(`supply_nets` 배선·이름 집합 제거)은 B26(DF-19·DF-26)이 먼저 한다 | code-author / test-author | Phase 4(DF-24와 같은 변경 단위. B26-1 병합이 선행) |

## 4. DF-19 (929행), DF-26 (936행)

DF-19 원문:
> | DF-19 | 레일 넷 집합이 모듈마다 다르다(대소문자) | stick_diagram `_RAIL_NETS`, sizing_recipe `_DEFAULT_RAIL_HI`/`_DEFAULT_RAIL_LO` 레일 판정 | 4(DEC-60 `supply_nets`·`supplies_v` 선언으로 교체, MG1, DF-26과 같은 변경 단위, U-26) | **위치 열은 전수여야 한다**: 레일 넷 이름을 동작 조건으로 쓰는 운영부 함수가 실측 29개(`sizing_recipe` 15 · `stick_diagram` 10 · `run_harness` 4)인데 현 목록은 일부만 적는다 -- MNA 고정 노드(`fixed = {"gnd": 0.0}`)와 기둥 추적의 진입 넷 비교가 특히 빠져 있고, 이 둘은 DEC-71 기둥 유도·IC11 3레일이 겨누는 고장이다. Phase 4에 **'운영부 레일 이름 리터럴 0' lint**를 두고 목록을 그 lint 산출로 대체한다(원자료는 history H4) |

정정(담당 칸과 비고 칸):
> 담당: `4(DEC-60 `supply_nets` 선언으로 교체 -- 넷 몫. B26-1~B26-4로 나누고 Phase 3 착수 전에 해도 된다. DF-26과 같은 변경 단위. 전압 몫(`supplies_v`)은 MG1이 맡아 이 DF와 분리한다, U-26)`
> 비고: `**위치 열은 전수여야 한다**: 2026-09-30 AST 전수(원자료 history H4로 옮김 -- `_drafts/prep_b26_supply_nets.md` §1)는 넷 판정 운영 함수 `sizing_recipe` 14 · `stick_diagram` 14(이름 상수 3 별도, 예제 데이터 2 제외)이고 그중 운영 경로 밖 3(`node_pole_estimate`, `find_differential_and_mirror_forks`, `propose_theta_kcl_gap_fill`)이다. 옛 '29개'의 `run_harness` 4는 넷 판정이 아니라 전압 선언(스칼라 `vdd`, MG1)이다. **assets 밖 사이트**: `skills/analog-grammar/assets/netclass.py`의 `RAILS`·`RAILS_POS`·`RAILS_NEG`(대소문자 무관 이름 집합 -- `netclass.classify_nets`·`assign_roles`·`is_mutual_loop_partner`, `idioms.m_diffpair`·`m_cascode`·`m_pushpull` 등이 쓴다)를 stick_diagram 11개 함수(운영 경로 7: `suggest_vertical_stack_composites`, `refine_differential_and_mirror_relations`, `find_verified_differential_and_mirror_relations`, `propose_device_roles_gap_fill`, `_propose_headroom_roles`, `_propose_vertical_stack_ids`, `find_stack_edges`)가 `_import_analog_grammar`로 불러 쓴다 -- 극성 판정이라 B26-2와 같은 결정(D1)을 따르고, 파일이 code-author 쓰기 경로(N3.12.2) 밖이라 경로표 개정 또는 호출부 대체가 필요하다. MNA 고정 노드(`fixed = {"gnd": 0.0}`, B26-3)와 기둥 추적의 진입 넷 비교(B26-2)가 특히 빠져 있던 것이고 DEC-71 기둥 유도·IC11 3레일이 겨누는 고장이다. **'운영부 레일 이름 리터럴 0' lint**(B26-4)를 두고 목록을 그 lint 산출로 대체한다`

DF-26 원문:
> | DF-26 | 레일 판정이 넷 이름 집합 하드코딩이다(sizing_recipe `_DEFAULT_RAIL_HI`/`_DEFAULT_RAIL_LO`, stick_diagram `_RAIL_NETS`). 신규 회로 `sf_pushpull_output_opamp`·`pushpull_follower_buffer`의 중간 전위 레일 `agnd`(DC에서는 W0 레일, AC구조에서는 교류접지)를 레일로 읽지 못한다 | sizing_recipe.py 3882~3883, stick_diagram.py 3147 참고 | 4(DEC-60 구현, DF-19와 같은 변경 단위) | DEC-60, DF-19, IC11, U-26 |

정정(위치 칸과 담당 칸):
> 위치: `sizing_recipe `_DEFAULT_RAIL_HI`/`_DEFAULT_RAIL_LO`(cd64170 3714·3715), stick_diagram `_RAIL_NETS`(2983) -- 사용처 전수는 DF-19 비고`
> 담당: `4(DEC-60 넷 몫 구현 = B26-1~B26-4, Phase 3 착수 전에 해도 된다. DF-19와 같은 변경 단위. MG1과 분리)`

(`agnd` 문장은 유지한다. 참고 사실: `agnd`는 두 회로에서 커패시터 단자로만 나오므로 트랜지스터 단자만 보는 집합 판정(B26-1)에서는 결과가 바뀌지 않고, 바뀌는 곳은 MNA 고정 노드(B26-3)다.)

## 5. N6.1 Phase 4 행 `범위` 칸(1001행) -- `Phase` 열은 바꾸지 않는다

원문 발췌: `MG1 레일 이름 변경(DEC-69)`
정정: `MG1 레일 전압 이름 변경(DEC-69). DF-19·DF-26의 넷 몫(B26-1~B26-4)은 Phase 3 착수 전에 해도 된다(이 행의 범위에서 빠지지 않는다 -- 앞서 병합한 card의 spec card `phase` 값은 병합 시점의 진행 Phase다. 선례 DF-35·DF-36 = `phase: 2`)`

## 6. 전환기 문구를 인용하는 다른 행 (정정 대상 확인)

| 행 | 원문 요지 | 정정 |
|---|---|---|
| 870 공격 13 | "`supply_nets` 없이 로드 → GB0 로드 게이트 거부(DEC-60). 전환기 이름집합 해석으로 조용히 넘어가지 않음을 거부 로그로" | 기대 로그에 "B26-1 뒤로는 `load_topology`의 `supply_nets` 없음 거부가 그 거부다(6a GB0 로드 게이트가 이 거부를 그대로 쓴다)"를 덧붙인다. 실행 Phase(6a)는 그대로 둔다 |
| 1021 N6.2 6a | "`supply_nets` 미선언 회로는 … 전환기 이름집합 해석으로 정해져 … 무효로 보고" | "`supply_nets` 미선언 topology는 B26-1부터 로드에서 거부된다(무효 판정 대상이 생기지 않는다)"로 교체 |
| 1101 U-26 | "(a) … 확정 전에는 DEC-60 전환기 이름집합·기본 해석(레일이 정확히 둘인 회로만)" | "확정 전에는 DEC-60 전환기 전압 해석(레일이 정확히 둘인 회로만). 레일 넷은 9/9 선언으로 전환기 불필요(B26-1)" |
| 319·325·404·410·435 | "전환기 경로/writer"는 N3.5 평가 커널 전환기다(레일과 무관) | 바꾸지 않는다 |

`docs/02-design` 소비자: `grep -rn "전환기 이름집합" docs/02-design` → 0건(2026-09-30 cd64170, 설계 문서는 아직 이 문구를 인용하지 않는다). `docs/03-analysis`의 review 기록 10개는 이력이라 바꾸지 않는다.

## 7. 이력 문서

H2(정정·폐기 이력) 표에 행 추가:
> | DEC-60 넷 전환기 | 레일 넷도 전압과 함께 MG1까지 이름집합 해석을 허용했다(선언이 없던 4회로용 한시 조항) | 2026-09-30 -- 9/9 선언(U-26 (b)) 뒤라 전제가 없어졌고, 넷과 전압을 한 변경 단위로 묶으면 넷 판정이 U-26 (a)에 묶인다. 넷 전환기를 B26-1에서 종료하고 DF-19·DF-26을 MG1에서 분리(원칙 기본안: 사용자 원칙 '엔진 식은 topology 무관') | 계획서 DEC-60·GB0·W0·N3.16·DEC-69·MG1·DF-19·DF-26·N6.1 Phase 4 범위·공격 13·N6.2 6a·U-26 |

H4(측정 근거표)에 `prep_b26_supply_nets.md` §1(AST 전수)·§2(선언 대 이름 집합)의 요약을 옮긴다(DF-19 비고가 가리키는 원자료).

`## Version History` 행:
> | **5.20** | 2026-09-30 | **DEC-60 넷 전환기 종료 + DF-19·DF-26을 MG1에서 분리**(원칙 기본안 -- 사용자 원칙 '엔진 식은 topology 무관', U-26 (b) 9/9 선언 완료). 레일 넷은 `supply_nets`만(없으면 `load_topology` 거부, B26-1), 레일 전압 전환기는 MG1까지 유지. DF-19·DF-26 = B26-1~B26-4(Phase 3 전 가능), MG1 = 전압 몫. DF-19 위치 비고를 AST 전수로 갱신하고 assets 밖 사이트(`analog-grammar` `netclass.RAILS_*`)를 추가. 판정 표 무변경(`plan_tables_hash` 전후 동일) |

## 8. 커밋 전 확인(오케스트레이터)

1. `$PY -P tools/gates/merge_gate.py plan-tables-hash docs/01-plan/features/gain-budget-gmid-sizing.plan.md`를 정정 전·후로 재서 같다.
2. `grep -n "전환기 이름집합" docs/01-plan/features/gain-budget-gmid-sizing.plan.md` → 남은 것이 모두 "종료" 문맥이다.
3. 파일 쓰기는 Write/Edit 도구로 한다(heredoc append 금지 -- 메모리 규칙).
4. 사용자 보고: DEC-60은 사용자가 확정한 결정이다. 전압 몫은 그대로이고 넷 몫의 한시 조항만 전제가 사라져 닫는 것이므로 원칙 기본안으로 기록하되, **보고 때 반드시 알린다**(DF-36 '저장소 밖 거부' 선례와 같은 처리).
