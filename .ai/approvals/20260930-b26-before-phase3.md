---
id: 20260930-b26-before-phase3
date: 2026-10-01
target_kind: decision
target: U2-B26-BEFORE-PHASE3
scope: 결정 A2 -- DEC-60 레일 넷 전환기 종료(supply_nets 선언만, 없으면 load_topology 거부) + DF-19·DF-26 전원 넷 판정 몫을 MG1에서 분리(B26-1~B26-4) + B26-1(spec card 20260930-b26-rail-accessor-set)과 B34(spec card 20260930-b34-grammar-explicit, analog-grammar 부재 시 조용한 폴백 -> ImportError 동작 변경)를 Phase 3 모듈 분할 전(Phase 2 진행 중)에 착수 -- 계획 정정과 두 spec card의 착수 조건
---

## 사용자 원문

> 승인 (Recommended)

(질문: [A2] 다음 세 가지를 한 건의 승인 기록으로 받아도 될까요? ① DEC-60의 '넷 이름으로 전원을 판정하는 전환기' 조항을 끝냅니다. 앞으로 전원은 topology의 supply_nets 선언으로만 정하고,
선언이 없으면 오류를 냅니다. ② DF-19·DF-26 가운데 전원 넷 판정 부분을 MG1(전압값 작업)과 분리합니다. ③ B26-1(전원 선언을 읽는 접근자와 '전원인가'만 묻는 곳 교체)과 B34(analog-grammar가
없으면 조용히 폴백하던 것을 명시적 오류로 바꿈)를 Phase 3 모듈 분할보다 먼저 합니다. 먼저 하면 모듈 분할 때 생기는 역방향 import와 이동 비용이 줄어듭니다. 9회로 결과는 사본 실측에서 같았습니다.
-- 선택지 '승인 (Recommended)': 승인 기록 1건으로 ①②③을 모두 덮습니다. 계획서 정정 커밋과 함께 올리고, B26-1·B34 spec card의 approval 줄이 이 기록을 가리킵니다.
다른 선택지는 '①②만 승인, ③은 Phase 3 뒤'와 '보류'였다. 질문 2026-09-30, 답 2026-10-01.)

## 범위 설명

덮는 것:
* ① DEC-60 레일 넷 전환기 종료 -- B26-1부터 `supply_nets`가 없는 topology는 `load_topology`가 거부하고 넷 이름 집합(`vdd`/`gnd`/`vss` 등)으로 대신 판정하지 않는다.
  전제(`supply_nets` 없는 회로)는 library 9회로의 선언(U-26 (b), 2026-09-17)으로 이미 없어졌다.
* ② DF-19·DF-26의 전원 넷 판정 몫(B26-1 집합 판정, B26-2 극성, B26-3 MNA 고정 노드, B26-4 이름 상수 삭제와 lint)을 MG1(레일 전압, U-26 (a) 대기)과 다른 변경 단위로 나누는 것.
* ①②의 계획 정정(이 기록과 함께 커밋): 계획 N2 DEC-60 발췌 1~3과 상태 칸, GB0·W0 문구, N3.16 레일 넷 행 마지막 칸(kcl_residual 선언의 `rail_nets` 키를 B26-1에서 거부),
  DEC-69 발췌, MG1 행, DF-19·DF-26 담당·비고·위치 칸, N6.1 Phase 4 행 `범위` 칸, 공격 13 기대 로그, N6.2 6a 문장, U-26 (a) 문구, history H2·H4와 Version History 행.
* ③ B26-1 -- spec card `20260930-b26-rail-accessor-set`을 Phase 2 진행 중에 병합하는 것(card `phase: 2`, DF-35·DF-36 선례). B34에서 인계받은 도달 불가 부재 분기 삭제를 포함한다.
* ③ B34 -- spec card `20260930-b34-grammar-explicit`을 Phase 2 진행 중에 병합하는 것(card `phase: 2`)과 그 **동작 변경**: analog-grammar(`netclass`·`idioms`)를 import하지 못하면
  `stick_diagram`의 공개 진입점이 조용히 `None`·`[]`·`unavailable_reason` dict를 돌려주던 것을, skill 이름 `analog-grammar`와 탐색 경로를 적고 원래 예외를 `__cause__`로 이은 `ImportError`로 바꾼다.
  바뀌는 def는 4개다: `_import_analog_grammar`(예외를 삼키지 않고 다시 던짐), `find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`(부재 분기 삭제).
  운영 경로 큰 def의 부재 분기는 도달 불가로 남기고 코드 삭제를 B26-1·B35로 넘기는 순서, 관련 docstring·`references/analog-grammar-integration.md` 폴백 서술 정정도 덮는다.

덮지 않는 것:
* 레일 전압(`supplies_v`, 스칼라 `vdd` 폴백 삭제, IC11)과 옛 키 거부 게이트 일반형 -- MG1, U-26 (a) 그대로.
* B26-2(극성)·B26-3(MNA 고정 노드)의 방식 -- 각 card의 착수 조건으로 따로 묻는다.
* V3·V7 면제 일체. B26-1의 V3 처리는 별도 결정(A1)이고, B34는 V3 면제가 없다(기존 생존 면제·등가 변이 면제 모두 0 -- `find_differential_and_mirror_forks`의 부재 분기는 이 때문에 B34 범위에서 빼 백로그로 보냈다).
  이 기록의 `target`(`U2-B26-BEFORE-PHASE3`)은 결정 이름이며 def id·변이 id가 아니다.
* `install.py` `SKILLS`에 `analog-grammar`를 더하는 것(사용자 쓰기 경로, 별도 사용자 작업), analog-grammar sys.path 주입 방식(레지스트리 R1), analog-grammar 이름 집합(`netclass.RAILS*`, 백로그 B35)·쓰기 경로(B36).
* 판정 표(`plan_tables_hash` 입력: N4.1 `ID`·`담당 Phase`·`강제 test`, N4.2 `도입`, N6.1 `Phase` 열, N3.12.2) -- 바꾸지 않는다. 바뀌면 이 승인이 아니라 `plan_tables` 승인이 필요하다.

## 재검토

B26-1 또는 B34가 병합되지 않은 채 Phase 3 M 카드가 `stick_diagram`·`sizing_recipe`를 나누기 시작하면, ③ 중 병합되지 않은 card의 앞당김은 효력을 잃고 그 card의 편집 범위를 새 모듈 기준으로 다시 잰다.
