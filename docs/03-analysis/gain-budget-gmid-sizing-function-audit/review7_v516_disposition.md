# plan v5.15 -> v5.16 결정표 (작성자)

- 대상: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(v5.15, 1132줄, 커밋 4913fac) -> v5.16(**1132줄**, 줄 수 변화 없음).
- 사용자 결정(2026-09-16): "1은 그대로 하고, 2는 1.8에 맞춰." -- v5.15 결정표 `review7/v515_disposition.md` §4 Q5(U-34 회로 선정)의 후속 대화. 1 = 논문 목표 스펙(CL 10 pF·GB 10 MHz·PM 63.4°) 유지, 2 = sky130 재설계 전원 1.8 V.
- 근거(읽은 실제 파일): `skills/analog-gmid-design/assets/library/ngcc_3stage_ff.topology.json`(16 MOS + Cm1·Cm2·CL, `supply_nets` vdd·gnd, `ports` Vinp/Vinn/Vout, `_paper_target_spec`), 같은 이름 `.topology.md`(넷별 연결 표), `review7/v515_verify.md` §3(낮음 N1~N3), plan 원문.
- 패치: `scratchpad/rewrite2/patch_v516.py`(30건) + `patch_v516_fix1.py`(2건). 총 32건, 각 `assert count == 1`. utf-8, `newline=""`. 파일 쓰기는 Write 도구와 이 스크립트만(`git checkout`·`git restore`·bash 리다이렉트 0건).
- 결과: plan `git diff --numstat` = **23/23**, history = **1/0(삭제 0줄)**. CR 0(LF 유지), UTF-8 정상 디코드.
- 줄 번호는 인용하지 않았다(N0.1). 본문 인용은 절 번호·ID뿐이다.

---

## 1. 반영 항목

| # | 지시 | 고친 곳(v5.16 절·ID) | 반영 내용 | 판정 |
|---|---|---|---|---|
| 1-a | U-34 확정(회로 추가) | U-34 | 기본안 열을 **확정**으로 바꿨다: `ngcc_3stage_ff`(파일 경로와 넷 표, 출처 Lee et al. JSTS Vol.7 No.1 2007 Fig. 3), connectivity·`ports`·`supply_nets`(vdd·gnd)·`passive_elements`(Cm1 V1–Vout, Cm2 V2–Vout, CL Vout–gnd)는 사용자 확정본, 문서 전용 목표 스펙(sky130 1.8 V·CL 10 pF·GB 10 MHz·PM 63.4°·ICMR ≥ 0.6 V)과 논문 설계 예시는 참고값, 사이징 스펙은 미선언이라 6a 구조 유도에만 들어감. 필요 시점 열은 **닫힘(2026-09-16)** + 소비 Phase(6a/6c/7b) | 반영 |
| 1-b | "발동 0" 전수 정정 | DEC-81, N1.2 Out of scope, N3.7 달성가능성 (a), N3.2-8 (iii)(vi), N5.4, N6.1 7b 착수 조건, N6.2 6a/6c/7b DoD | DEC-81 상태 열 "미구현(발동 0, U-34)" -> **"미구현(발동 1회로 `ngcc_3stage_ff`, 6c·7b 구현 대상)"**, 본문의 "현 library에 발동 회로가 0" -> "발동 회로 기본안이 있다". N1.2의 "분기·합류가 있는 이득 블록 DAG(feedforward …, U-34)" 항목은 out-of-scope 목록에서 **삭제**. N5.4는 "발동 0 명시" -> "발동 회로가 하나이므로 그 회로의 묶음 판정·경로별 기여와 발동/검증 발동 수를 적고 한 회로를 넘는 일반성은 주장하지 않는다". DoD 3곳은 "묶음 0이면 발동 0 명시" -> "발동 회로의 묶음 판정·경로별 기여 제출 + 분기·합류가 없는 회로는 묶음 0 명시" | 반영 |
| 1-c | library 회로 수 7 -> 8 | 용어 'library 회로', '사이징 대상 회로', N0.3(review7 인용), N6.2 6a DoD 3곳, U-08, U-26, N6.1 6a, DEC-71 (3), DEC-76 | 용어집 = "현재 8개 … + `ngcc_3stage_ff`". 6a DoD의 기둥 대상 "(7개)" -> "(8개)", "library 회로 7개 전부에서 블록마다" -> "8개", 기본 전달 뷰 **"4/7 회로에서만 측정" -> "5/8"**(ngcc는 `ports`가 있다). U-08에 "library 8개 중 3개 -- 나머지 5개는 `ports` 선언이 있다". U-26 기본안의 "library 7개 회로 전부가 `supply_nets` 미선언" -> "8개 중 `ngcc_3stage_ff`만 선언, 나머지 7개 미선언"이고 (b) 필요 시점의 "신규 3회로" -> "`supply_nets` 미선언 3회로"(N6.1 6a 착수 조건도 같게). N0.3의 review7 원자료 인용은 **측정 시점 7개**로 표기해 원자료 사실을 보존 | 반영 |
| 1-d | J12에 신규 회로 항목 | J12 | `ngcc_3stage_ff` 항목 신설: 단 구성(1단 M1/M2 + 미러 M3/M4 -> V1, 2단 M8 + 미러 M9/M10 + M11 -> V2, 3단 M13 + M12, feedforward M7·M14가 Vout으로) 서술 뒤 ratify 항목 넷 -- (i) **gmf1 가지 M5·M6A·M6B·M7의 셀 분류·DC 역할**(기본안: M5 = VBP 바이어스 전류원, M6B = ND 미러 선에서 신호 전류 복사, M6A = diode 기준, M7 gate = NX. M6A:M7 = 1:2는 논문 값) (ii) **Vout 합류의 복합 블록 묶음 경계**(DEC-81·J12-d 기준) (iii) **Cm1·Cm2의 DC 고립 판정**(커패시터는 DC 전도 그래프 엣지가 아니므로 잎 가지치기 대상인지, DEC-70·DEC-71) (iv) **미러·차동쌍 후보 ratify**(측정 후보 pmos VBP {M0,M5,M12} / nmos ND {M3,M4,M6B} / nmos NX {M6A,M7} / nmos V1 {M8,M14} / pmos NP {M9,M10} / diff_pair TAIL {M1,M2}, `equal_vgs` 강제 여부는 DEC-09) | 반영 |
| 2-a | 이월 (a) J12-d 갈래 | J12-d | "**갈래**: (a)로 ratify되면 `sf_pushpull_output_opamp`도 DEC-81 발동 회로가 되어 발동 회로가 `ngcc_3stage_ff`와 둘이 되고, K8이면 발동 회로는 `ngcc_3stage_ff` 하나다" 한 줄. 7b DoD의 (ii) 문장에도 같은 갈래를 반영("`sf_pushpull_output_opamp`까지 (a)로 ratify되면 발동 회로가 둘") | 반영 |
| 2-b | 이월 (b) DEC-60 판정 입력 | DEC-60 | 거부 규칙 뒤에 "**이 거부의 판정 입력**은 둘이다: (i) `supply_nets` 선언이 있으면 그 목록의 넷 수와 `supplies_v{넷: 전압}` 값의 부호, (ii) 선언이 없으면 전환기 이름집합 해석이 찾은 레일 수와 실행 spec 레일 전압의 부호다. 이름집합 해석으로 찾은 레일이 정확히 둘이 아니거나(해석 범위 밖 넷 -- `agnd` 같은 중간 전위 넷은 이 해석에서 레일로 읽히지 않는다) 레일 전압에 음수가 있으면 `supply_nets` 없이는 거부한다" | 반영 |
| 2-c | 이월 (c) 6c design 소관 표시 | DEC-81 | 끝에 "**묶음 판정의 나머지 규칙**(합류 노드 선정 절차, 묶을 블록 집합 유도, 합류 노드가 여럿일 때의 묶음 경계, 경로별 기여 기록 형식)은 6c design(N9.1 `6c-coupling-achievability`)이 정한다". N9.1 `6c-coupling-achievability`에 이미 같은 절차가 목록으로 있어 새로 쓰지 않고 **가리키기만** 했다(N0.1) | 반영 |
| 3 | 부록 A.2·헤더·history | 헤더, 부록 A.2, history Version History | 헤더 `version: 5.15` -> `5.16`. A.2에 "**v5.16 신설**: ID 신설 없음(회로 `ngcc_3stage_ff`가 library에 추가됐다)"과 개정 목록. history에 **5.16 행 하나**(사용자 원문 인용 포함) 추가, 기존 줄 삭제 0 | 반영 |

## 2. 문서 규칙 준수

| 규칙 | 처리 |
|---|---|
| N0.1 "모든 항목은 한 곳에만" | 복합 블록 규칙 정본은 DEC-81 하나. 회로 사실(출처·스펙·선언)은 U-34 하나, 회로 해석 항목은 J12 하나, ratify 갈래는 J12-d 하나에만 적었다. DoD·N5.4는 측정·보고 의무 자리라 사실을 반복하지 않고 소비 주체로 갈랐다 |
| N0.1 경위 금지 | 이력성 서술("추가할지였다", "옛 발동 0")은 history 5.16 행과 부록 A.2 개정 줄에만 있다. 본문에는 옛 상태 서술을 남기지 않았다 |
| 줄 번호 인용 금지 | 새 문장에 줄 번호 0건 |
| 회로 해석 확정 문장 금지 | DEC-81·N3.7의 발동 회로 서술을 **"발동 회로 기본안"**으로 낮추고(`patch_v516_fix1.py`), "M7·M13·M14의 drain이 모두 Vout에 붙는 것은 connectivity 사실이고, 그 합류를 분기·합류로 볼지와 묶음 경계는 J12 ratify다"를 붙였다. J12 항목의 셀 분류·DC 역할·미러 후보도 전부 "기본안 / 측정 후보 / ratify 대상"으로만 적었다 |
| ID 체계 | 신설 0. DEC·U·J·DF·IC 모두 새 번호를 만들지 않았다(회로만 늘었다) |
| 파일 쓰기 | Write 도구와 패치 스크립트만. `git checkout`·`git restore`·heredoc·`>>` 0건. topology.json은 읽기만 했다 |
| 코드·테스트 | 손대지 않았다(계획·이력 문서 2개만 변경) |

## 3. 기존 규칙과 충돌해 조정한 곳

| 곳 | 충돌 | 조정 |
|---|---|---|
| DEC-81 상태 열 | DEC-76은 "발동 0인 분기는 구현하지 않는다"였고 DEC-81은 그 형식으로 "미구현(발동 0, U-34)"이었다. 발동 회로가 생겨 DEC-76의 유예 근거가 사라진다 | 상태를 **"미구현(발동 1회로 `ngcc_3stage_ff`, 6c·7b 구현 대상)"**으로 바꿔 DEC-76의 "발동 회로가 들어온 뒤 구현한다"를 그대로 따르게 했다. 구현 Phase는 이미 적용 열(GB2·GB3·GB6·N3.7)과 6c·7b DoD가 가리키고 있어 새 Phase를 만들지 않았다 |
| N1.2 Out of scope | 이 행은 "계산 규칙을 정의하고 발동 회로를 넣어 ratify하면 범위에 들어온다"가 판정 규칙이다. 두 조건이 모두 충족됐다 | 목록에서 해당 부류만 삭제했다(행 자체와 판정 규칙은 유지). 다른 부류(gain boosting, 전류 입력 뷰 등)는 그대로 |
| DEC-59 `기록만` 목록 | 지시에 "DEC-59 목록"이 있었으나 실제 본문의 `기록만` 목록에는 복합 블록 항목이 없다(v5.15에서 이미 삭제됨) | **수정하지 않았다**. DEC-59의 나머지 문장은 분기 일반 규칙이라 회로 수와 무관하다 |
| N0.3 review7 원자료 인용 | 원자료는 "library 7개 회로 규칙 분기 발동 전수 측정"이다. 8로 고치면 동결 원자료의 사실과 어긋난다 | 수를 고치지 않고 **"(측정 시점 7개 -- `ngcc_3stage_ff` 추가 전)"**로 표기했다 |
| DEC-71 (3)·DEC-76 기둥 수 근거 | "현 library 7개 회로에서는 어느 정의에서도 상한을 넘지 않는다"가 8번째 회로에서 미측정 | "측정한 회로에서는 … 넘지 않는다(`ngcc_3stage_ff`는 6a에서 함께 잰다)"로 바꿔 미측정을 미측정으로 남겼다. 상상으로 기둥 수를 적지 않았다 |
| N3.2-8 (iii) 측정 기대 | 회로별 기본 폐경로 전수 기대값이 회로마다 적혀 있는데 새 회로 값이 없다 | "`ngcc_3stage_ff`는 U-34로 새로 들어온 회로라 기대값 없이 6a에서 처음 잰다"로 적었다(기대값을 지어내지 않았다) |
| N6.1 7b 착수 조건 | U-34가 열린 착수 조건으로 남아 있었다 | "U-34(**확정** -- 검증 발동 회로 `ngcc_3stage_ff`)"로 바꿨다. U-31처럼 닫힌 항목도 목록에 남기는 기존 형식을 따랐다 |
| U-26 (b) "신규 3회로" | 신규 회로가 넷이 됐고 그중 `ngcc_3stage_ff`만 `supply_nets` 선언이 있다 | 조건을 **선언 유무 기준**("`supply_nets` 미선언 3회로")으로 바꿔 회로가 더 들어와도 규칙이 그대로 성립하게 했다 |

## 4. 남은 사용자 질문

| ID | 질문 |
|---|---|
| Q1 | **`ngcc_3stage_ff`의 사이징 스펙 선언 여부** -- 지금은 문서 전용(`_paper_target_spec`)이라 6a 구조 유도에만 들어간다. 사이징 대상 회로로 올리려면 U-25와 같은 형식(`supplies_v`, CL, 성능 제약, 목적 축 예산)으로 선언해야 하고, 그때 논문 설계 예시(gm·Cm·W/L)는 참고값으로만 둔다 |
| Q2 | **J12-d 귀결** -- `sf_pushpull_output_opamp` M17/M20을 (a) 분기·합류로 ratify하면 DEC-81 발동 회로가 둘이 되고 7b DoD (ii)의 정지 기록도 바뀐다. 6a-2 공동분석에서 확정할 항목이다 |
| Q3 | **DEC-81 묶음 크기 상한의 소비 자리**(v5.15 Q6 이월) -- 복합 블록이 층 0 기둥 집합과 겹치는 범위 산정은 여전히 미기재이며, 발동 회로가 생겼으므로 6c/7b design이 실제 회로로 정할 수 있게 됐다. 지금 규칙을 더 쓰지 않았다 |

**v5.15에서 열려 있던 Q5(U-34 회로 선정)는 이번 판에서 닫혔다. Q6은 Q3로 이월한다.**

## 5. 독립 검증(`review7/v516_verify.md`) 반영 -- `patch_v516_fix2.py`(14건)

| # | 반영 | 고친 곳 |
|---|---|---|
| M1 | rename 대상을 "사용자 확정 스펙 세 회로"·"nmcnr `sky130_supplies_v`"에서 **"문서 전용 스펙 필드를 가진 5회로(`nmcnr_amplifier`·`two_stage_ota_sf`·`pushpull_follower_buffer`·`sf_pushpull_output_opamp`·`ngcc_3stage_ff`)"**로 고치고 `sky130_supplies_v` 대상은 그 필드를 실제로 가진 두 회로(nmcnr·ngcc)로 적었다(실측: `grep -l`) | MG0(N3.16), N3.15 문서 목표 기록 행, N6.2 0.5 DoD |
| M2 | 공격 계수를 **13**으로 맞추고 실행 Phase를 분리했다: N4.3 머리말 "13건, 1~12는 0.5, 13은 6a", 공격 13 행에 "실행 Phase = 6a", 0.5 DoD "13건 중 0.5 대상 12건", N9.1 05-role "13건(0.5 12 + 6a 1)". 6a DoD에 공격 13 거부 로그를 **배선**했다(만든 게이트를 실제로 실행하는 자리) | N4.3, N6.2 0.5·6a DoD, N9.1 `05-role-separation` |
| L1 | "발동 회로 ≠ 검증 발동 회로" 단계 구분: J12 ratify 전에는 검증 발동 0이라 DEC-59 정지가 유지된다는 한 줄을 네 곳에 넣었다 | DEC-81 상태 열, N6.2 6a·6c DoD, U-34 |
| L2 | U-34에 topology 필드 이름 병기: `supplies_v` 1.2 V(논문) / `sky130_supplies_v` 1.8 V(사용자 확정) / `loading.CL_farad` 10 pF / `performance_targets.gbw_hz`·`pm_deg`·`icmr_v`(= `sky130_supplies_v` 기준 VDD/3) | U-34 |
| H1 | **반영 없음** -- 검증자가 `_paper_target_spec` 덤프를 잘라 읽어 `sky130_supplies_v`를 못 본 오판이며 정정판에서 철회됐다. 파일에는 두 필드가 모두 있다 | -- |

누적 결과: plan `git diff --numstat` = **29/29**(1132줄 유지), history = **1/0**. CR 0, UTF-8 정상.
