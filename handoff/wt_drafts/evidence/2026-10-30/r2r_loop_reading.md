# r2r_opamp 다이오드 없는 kvl_branch 고리의 소자 읽기 -- (i) pass 대 (ii) B (2026-10-30)

역할: 회로 해석 초안이다. 사용자는 승인만 한다(원칙 14). 문서·데이터·git은 쓰지 않았다.

근거는 셋만 썼다.
- 연결: `chip-design-skills/skills/analog-gmid-design/assets/library/r2r_opamp.topology.json`의 `netlist`·`ideal_sources`·`bias_inputs`. device_roles 같은 태그는 쓰지 않았다(이 파일에는 없다).
- 원문: Hogervorst et al., JSSC 29(12) 1994. 로컬 PDF는 `assets/library/sources/r2r_opamp__hogervorst_1994/source.pdf`, 쪽 렌더는 같은 폴더 `pages/pNN.png`, 텍스트는 `paper.md`.
  - 쪽 대응: PDF p.N = 저널 p.(1504+N).
  - 웹 링크: TU Delft repository 사본(`tudelft_0fc1.pdf`, topology.json `source` 문언). URL은 이번에 확인하지 않았다.
- 계획 정의(정의 문언만): `wt/plan-v6385/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`
  - 용어집 '소자 역할(DC·AC)'·'셀'·'signal stage'(88~95행대)
  - DEC-104 R13(303행)
  - Q-KV1(1174행, 배터리 손 판정 문언)
- as-built 엔진 판정(current_reuse loop_pick이 M9a를 pass로 분류한 것 등)은 근거로 쓰지 않았다.

## 0. 원문 근거 위치

| 내용 | 원문 | PDF 쪽 / 저널 쪽 | 로컬 |
|---|---|---|---|
| class-AB 출력단 동작 | Fig. 5 "Rail-to-rail output stage with floating class-AB control"과 본문 III절. "The floating class-AB control is formed by M19 and M20. The stacked diode-connected transistors, M23–M24 and M21–M22, bias the gates of the class-AB transistors M19 and M20" / "two translinear loops M20, M21, M22, M25 and M19, M23, M24, M26, which determine the quiescent current in the output transistors" / "Suppose the in-phase signal current sources, Iin1 and Iin2, are pushed into the class-AB output stage. As a result, the current of ... M20 increases while the current in ... M19 decreases" | PDF p.3 / 저널 p.1507 | `source.pdf` p.3, `pages/p03.png` |
| class-AB 제어를 합산 회로 안으로 옮김 | Fig. 8 "The floating class-AB control is biased by the cascodes of the summing circuit" | PDF p.4 / 저널 p.1508 | `pages/p04.png` |
| 떠 있는 전류원(바이어스 배터리) | Fig. 10(Ib3 떠 있는 전류원), Fig. 11 "The floating current source is implemented by means of M27 and M28". 본문: "The floating current source has the same structure as the floating class-AB control. The value of the current source is set by two translinear loops, M11, M21, M22, M28 and M17, M23, M24, M27" / "Because of the floating architecture of the current source, it does not contribute to the noise and offset" | PDF p.5 / 저널 p.1509 | `pages/p05.png` |
| 전체 회로 | Fig. 13 "Overall design ... with Miller compensation". V절: "a rail-to-rail class-AB output stage, M19 – M26. The floating current source, M27 – M28, biases the summing circuit and the floating class-AB control" | 그림 PDF p.6 / 저널 p.1510. V절 문장은 PDF p.5 / 저널 p.1509 | `pages/p06.png`, `pages/p05.png` |

## 1. 연결 (topology.json `netlist`)

벌크 넷은 31개 MOS 모두 선언되어 있지 않다(`bulk` 키 없음). 쪽 렌더 해상도로는 Fig. 13의 벌크 단자를 판독할 수 없다. 이 스크래치에는 PIL·PyMuPDF가 없어 확대 렌더도 하지 못했다.

| 소자 | 종류 | gate | drain | source | 연결에서 유도한 역할 | 원문 서술 |
|---|---|---|---|---|---|---|
| M26 | n | n_gn | Vo | VSS | 출력 CS. gate가 신호 넷이다 | 출력 트랜지스터(p.1507) |
| M25 | p | n_gp | Vo | VDD | 출력 CS | 같음 |
| M19 | n | n_abn | n_gp | n_gn | 채널이 두 출력 gate 넷 사이에 있다. gate는 다이오드가 만든 넷이다 | "floating class-AB control"(p.1507) |
| M20 | p | n_abp | n_gn | n_gp | M19와 역병렬이다(같은 두 넷) | 같음 |
| M27 | n | n_abn | n_mp | n_mn | 채널이 두 미러 기준 넷 사이에 있다. gate는 **M19와 같은 넷**이다 | "floating current source"(p.1509) |
| M28 | p | n_abp | n_mn | n_mp | M27과 역병렬이다. gate는 **M20과 같은 넷**이다 | 같음 |
| M17·M18 | n | n_mn | n_fn1·n_fn2 | VSS | N 미러. gate·source가 같아 평행 엣지(equal_vgs)다. M15(d = n_mn, s = n_fn1)를 거쳐 gate가 n_mn에 붙은 캐스코드 다이오드 꼴이다 | "M15 – M18" 미러(p.1509) |
| M11·M12 | p | n_mp | n_fp1·n_fp2 | VDD | P 미러. M13을 거친 같은 꼴이다 | "M11 – M14" 미러 |
| M23 / M24 | n | n_abn / n_m24 | n_abn / n_m24 | n_m24 / VSS | 쌓인 다이오드 두 개다. 전류는 Ib2 = 7 µA(VDD → n_abn)로 고정된다 | "stacked diode-connected"(p.1507) |
| M22 / M21 | p | n_abp / n_m21 | n_abp / n_m21 | n_m21 / VDD | 쌓인 다이오드 두 개다. 전류는 Ib5 = 7 µA(n_abp → VSS)로 고정된다 | 같음 |

넷의 성격(연결만으로 판단):
- n_abn에는 다이오드 M23의 drain·gate, Ib2, 그리고 M19·M27의 gate만 붙는다. 그래서 어떤 여기 뷰의 신호 경로에서도 도달하지 않는다(바이어스 넷). n_abp도 같다.
- n_gp·n_gn은 신호 넷이다. n_gp는 M14 캐스코드 → n_fp2 → M4 drain으로, n_gn은 M16 → n_fn2 → M2 drain으로 입력쌍 신호를 받는다.
- n_mp·n_mn도 신호 넷이다. n_mp는 M13 → n_fp1 → M3 drain으로, n_mn은 M15 → n_fn1 → M1 drain으로 받는다.

## 2. 두 고리의 구성

- 고리 N: {M17/18, M19, M26, M27}. 꼴은 F–M26–n_gn–M19–n_abn–M27–n_mn–M17/18–F이다.
  - 등식은 VGS17 + VGS27 = VGS19 + VGS26이다.
- 고리 P: {M11/12, M20, M25, M28}. 꼴은 위와 대칭이다.
- **물리 사실**: 고리 N은 원문이 이름을 붙인 두 translinear 고리의 차이다.
  - A = {M19, M23, M24, M26}(p.1507)
  - B = {M17, M23, M24, M27}(p.1509)
  - 둘이 VGS23 + VGS24를 공유하므로 N = A ⊕ B이다. 새 물리 정보는 없다.
  - DEC-64 기본 사이클은 스패닝 트리에 따라 {A, N} 또는 {A, B} 등을 고른다. `2026-10-29/classab_battery.md` 59행이 적은 엔진 기저는 {A, N}이다. 해 집합은 같다(사이클 공간이 같다).
  - **고리 N이 기저에 들어올 때만** (i)/(ii) 물음이 생긴다. 원문의 물리 결정자(I_27을 정하는 고리)는 다이오드가 있는 B이다.

## 3. 소자별 판정 (계획 정의 R13: S = R3이 gm을 정하는 신호 소자, F = 그 밖 신호 소자, B = 부하·미러·바이어스·FF)

DC 역할은 용어집의 유도 절차를 따랐다.
- (1) diode: M19·M27 모두 gate ≠ drain이라 해당하지 않는다.
- (2) gate와 source를 둘 다 공유하는 그룹: M19(n_abn, n_gn)와 M27(n_abn, n_mn)은 source가 달라 묶이지 않는다. 다이오드 M23은 source가 n_m24라 이 둘과 묶이지 않는다.
- (3) gate가 교류접지이고 source가 레일: gate n_abn은 교류접지지만 source n_gn·n_mn이 레일이 아니다. 그래서 해당하지 않는다. 계획은 이 조건이 "CG 셀이 전부 걸린다"를 막으려고 둔 것이라고 명시한다.
- (5) 그러므로 M19·M20·M27·M28의 DC 역할은 모두 **신호 소자**이다.

AC 셀은 용어집 '셀'의 pass 정의를 따랐다. pass = 채널 source↔drain, gate가 그 뷰의 신호 경로 밖(바이어스·diode 구동 넷 포함)이다.
- 네 소자 모두 이 정의에 맞는다.
- 역병렬 쌍 M19/M20과 M27/M28은 각각 pass 묶음 하나가 된다.
- 이것은 용어집이 예로 든 파일럿 M9a/M9b('gate가 diode 구동 넷이라 pass')와 같은 꼴이다.

| 소자 | 계획 정의 판정 | 원문·물리 | (i) pass | (ii) B | 의견 | 확신도 |
|---|---|---|---|---|---|---|
| M19 (M20 대칭) | DC 신호 소자, AC pass. R3 대상(매크로 활성 입력·rout follower)이 아니므로 **F** | 원문이 신호 전류가 이 소자를 지나며 전류를 바꾼다고 적는다(p.1507 "current ... M19 decreases"). class-AB 제어는 신호 경로 안이다 | 맞음 | 근거 없음. B 목록(부하·미러·바이어스·FF)에 pass가 없다. '바이어스'는 DC 역할 말이고(용어집) DC 절차 (3)에서 탈락한다 | **(i)** | 상 |
| M19의 M9a형 경계 | n_gp·n_gn은 둘 다 따로 구동되는 넷이다(동상 Iin1·Iin2, p.1507). 그래서 쌍은 한 방향 CG(M9b 꼴)이면서 두 gate 사이 종단 임피던스(M9a 꼴)이기도 하다 | Q-KV1 손 판정의 M9a 'F/B 경계(중하)'와 같은 기능 논리가 일부 적용된다 | -- | -- | F 유지. 다만 기능상 부하 성분이 있다(⚑) | 중상 |
| M27 (M28 대칭) | DC 신호 소자(source n_mn 비레일), AC pass(채널 n_mp↔n_mn, 둘 다 신호 넷). 그래서 **F** | 원문 기능은 "floating current source"가 합산 회로를 **바이어스**한다는 것이다(p.1509). "같은 구조"라고 명시하고, 떠 있어서 잡음·offset에 기여하지 않는다고 적는다 | 정의 문언에 맞음 | 기능(원문)으로는 바이어스다. 그러나 계획의 '바이어스'(DC 역할)는 절차 (3)에서 탈락하므로 **정의상 근거 없음** | **(i)**(정의). 기능과 긴장이 있다 | 중 |
| M17/M18 | AC 미러 → **B**. DC 절차로는 (2) 그룹에 다이오드가 없고 공유 gate n_mn이 신호 넷이다. 그래서 `review_needed`이다(용어집 (2)) | 원문 "current mirror M15 – M18"(p.1509) | B | B | B(미러) | 중상 |
| M26 (M25 대칭) | 출력 CS. 출력 극점 gm(R3 매크로)에 들면 S, 아니면 F | 출력 트랜지스터 | S/F | S/F | B 아님 | 상 |

### 핵심 논거: 연결만으로는 M19와 M27을 가를 수 없다

M19와 M27을 연결만으로 비교하면 다음이 같다.
- gate가 같은 넷(n_abn)이다.
- 같은 꼴의 역병렬 n/p 쌍이다.
- 채널이 두 신호 넷 사이에 있다.
- 원문도 "same structure"라고 적는다(p.1509).

따라서 일반 규칙(원칙 12: 이름·매직넘버 금지)으로는 둘을 같은 부류로 묶어야 한다.
- M19/M20이 신호 경로 소자(F)라는 것은 원문 동작 서술로 확실하다(상).
- 그러면 규칙이 일관되려면 M27/M28도 F여야 한다.
- 둘을 가르려면 연결상 차이 하나를 규칙으로 새로 정해야 한다. 그 차이는 채널 양끝 넷이 '미러 기준 넷(캐스코드 다이오드 꼴 n_mp·n_mn)'이냐 'CS gate 넷(n_gp·n_gn)'이냐이다.
- 그런 규칙은 R13 B 정의를 바꾸는 것이므로 계획 개정과 사용자 승인 대상이다(원칙 17·19).

### 읽기 (ii)의 '다이오드가 만든 바이어스 gate → B' 논리에 대한 물리 점검

- gate가 바이어스 넷이라는 것은 계획 정의에서 **pass의 조건**이지 B의 조건이 아니다.
- B(바이어스 전류원)의 DC 조건은 source가 레일인 것이다. 이 조건이 없으면 CG·pass가 모두 바이어스가 된다(용어집 (3)이 명시한 반례).
- 판정: **틀림**. 이 논리는 정의 위반이다. 확신도는 상이다.

## 4. 결론 (초안 -- 사용자 승인 대상)

| 물음 | 의견 | 근거 | 확신도 |
|---|---|---|---|
| 고리 N·P에서 (i)·(ii) 중 계획 정의(R13·용어집)에 맞는 읽기 | **(i) pass(F)**. 고리 B 멤버는 M17/18(고리 P에서는 M11/12) 하나다 | §3 표. DC 절차 (3) source 레일 조건, pass 정의, R13 B 목록 | 상(M19/M20), 중(M27/M28) |
| (ii)가 맞으려면 | R13 B에 '떠 있는 바이어스(미러 기준 넷 사이 pass 묶음)' 같은 새 규칙이 필요하다 | 원문 기능 p.1509. 연결 판별자는 채널 양끝 넷의 종류 | 계획 개정 사항(판정 아님) |

(i)의 귀결(m_kv1 §5와 같음):
- 종속은 M17/18로 강제된다.
- M27의 source n_mn = VGS17이다. 그래서 M27의 VDS(n_mp − n_mn)가 종속값을 읽는다.
  - 벌크가 레일이면 VSB도 종속값을 읽는다. 벌크는 미선언이다.
- 결과적으로 고리 N은 1차원 암묵 풀이가 된다.

## 5. 판정 전에 더 필요한 것 / 열린 상호작용 (⚑)

1. **기저 선택**: 원문의 물리 결정자 고리는 다이오드가 있는 B {M17, M23, M24, M27}이다(p.1509).
   - DEC-64 스패닝 트리가 {A, B}를 고르면 다이오드 없는 고리 자체가 기저에 없다. 그러면 (i)/(ii) 물음이 사라진다.
   - 대신 A와 B가 M23·M24를 공유한다. '이미 종속된 멤버 제외' 규칙 때문에 B의 종속은 M24 또는 M17/18이 된다. 이때 A·B의 종속이 서로 엮인다(M23의 VSB = VGS24).
   - 어느 쪽이 손계산상 싼지는 이번에 재지 않았다. 기저를 어떻게 고를지는 계획 DEC-64의 몫이다(as-built가 아니다).
2. **벌크 미선언**: VSB 결합 여부(P(M27)의 '결합')는 벌크 선언에 달려 있다.
   - topology 파일에 벌크 넷이 없다. 원문 Fig. 13 렌더에서도 판독이 불가했다.
   - 정정이 필요하면 topology 정정 대기열 사항이다(원칙 15, 사용자 몫).
3. **M27/M28 기능 대 정의의 긴장**: 원문은 M27/M28을 바이어스(떠 있는 전류원)로 서술한다.
   - 계획 정의로는 F이다. 이 차이는 '원래 취지와 다름' 후보로 표지한다.
   - B로 바꾸려면 §3의 새 규칙이 필요하다(계획 개정·승인).
4. **M19/M20의 M9a형 경계**: Q-KV1 손 판정은 current_reuse M9a를 'F/B 경계(중하)'로 두었다.
   - r2r M19/M20은 양끝이 모두 구동되는 넷이라 그 경계 성분이 있다.
   - 같은 기준을 쓰면 확신도는 중상이다. 확정은 Q-KV1 판정대로 card TB-1 몫이다.
