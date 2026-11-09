# U2 승인 질문 -- `20260930-b26-before-phase3`

B26-1 spec card(`draft_b26_1.spec.md`, id `20260930-b26-rail-accessor-set`)의 머리 `approval` 줄이 가리키는 decision 승인 기록의 질문 원문과 범위다.
근거: review_b26_1 S3 -- DEC-60의 한시 조항과 기한은 사용자가 확정한 결정 내용이고, Phase 4 DF를 Phase 3 전으로 당기는 것은 순서 변경이다. 선례 U-39(기본안이어도 decision 승인 기록),
DF-35·DF-36(사용자 지시로 앞당김). 그래서 '보고 때 알림'이 아니라 승인 한 건으로 받는다. U1(V3 처리)은 별도 질문이다(이 승인에 넣지 않는다).

## 질문 원문(그대로 묻는다)

> **B26-1(레일 넷 선언 접근자) 착수를 위해 세 가지를 한 번에 승인해 주실지 여쭙니다.**
>
> 1. **DEC-60 '넷' 전환기 종료**: DEC-60은 `supply_nets`가 없는 기존 회로를 위해 MG1(Phase 4)까지 레일을 넷 이름 집합(`vdd`/`gnd`/`vss` 등)으로 판정하는 한시 조항을 두었습니다.
>    library 9회로가 2026-09-17에 모두 `supply_nets`를 선언해(U-26 (b)) 이 조항의 전제가 없어졌습니다. B26-1부터 `supply_nets`가 없는 topology는 `load_topology`가 거부하고, 이름 집합으로
>    대신 판정하지 않습니다. 레일 **전압**의 전환기 해석(`supplies_v`가 없으면 레일 둘, 높은 레일 = spec `vdd`, 낮은 레일 = 0 V)은 지금대로 MG1까지 둡니다.
> 2. **DF-19·DF-26의 넷 몫을 MG1에서 분리**: 레일 넷 판정(B26-1 집합 판정, B26-2 극성, B26-3 MNA 고정 노드, B26-4 이름 상수 삭제와 lint)을 MG1(레일 전압, U-26 (a) 대기)과 다른 변경
>    단위로 나눕니다. 묶어 두면 넷 판정이 `supplies_v` 값 확정(U-26 (a))을 기다려 Phase 4 끝까지 밀립니다.
> 3. **B26-1을 Phase 3 전(지금, Phase 2 진행 중)에 착수**: 편집 파일이 지금은 2개(stick_diagram·sizing_recipe)인데 Phase 3 모듈 분리 뒤에는 6개 모듈로 흩어집니다. 계획의 Phase 열(판정 표)은
>    바꾸지 않고, card의 `phase` 값은 병합 시점의 진행 Phase(2)로 적습니다(DF-35·DF-36 선례).
>
> 판정 표(`plan_tables_hash`)는 바뀌지 않습니다. 계획 정정안은 `_drafts/draft_b26_plan_patch.md`입니다.

선택지:
* **승인 (Recommended)** -- 세 항목 모두. decision 승인 기록 `20260930-b26-before-phase3`를 만들고 계획 정정 커밋 → B26-1 card 커밋 순서로 간다.
* **넷 전환기 종료·분리만 승인, 착수는 Phase 3 뒤** -- 1·2만. B26-1은 Phase 3 모듈 분리 뒤 새 모듈에서 한다(편집 범위가 커진다). card `phase`를 그때 값으로 바꾼다.
* **보류** -- DEC-60을 지금대로 둔다(MG1에서 넷·전압을 함께 처리). B26-1 착수 안 함.

## 승인 기록 초안(사용자 원문을 받은 뒤 오케스트레이터가 `.ai/approvals/20260930-b26-before-phase3.md`로 쓴다)

머리 블록은 scratch에서 `merge_gate.py parse-approval`로 파싱 통과를 확인했다(아래 `<원문>`만 채운다).

```
---
id: 20260930-b26-before-phase3
date: 2026-09-30
target_kind: decision
target: U2-B26-BEFORE-PHASE3
scope: DEC-60 레일 넷 전환기 종료(B26-1부터 supply_nets 없으면 load_topology 거부) + DF-19·DF-26 넷 몫을 MG1에서 분리(B26-1~B26-4) + B26-1을 Phase 3 전에 착수 -- 계획 정정(draft_b26_plan_patch)과 spec card 20260930-b26-rail-accessor-set의 착수 조건
---

## 사용자 원문

> <원문>

(질문: 위 '질문 원문' 그대로 -- 선택지 '<고른 선택지>')

## 범위 설명

덮는 것:
* 계획 N2 DEC-60 발췌 1~3과 상태 칸, GB0·W0 문구, N3.16 레일 넷 행 마지막 칸, DEC-69 발췌, MG1 행, DF-19·DF-26 담당·비고·위치 칸, N6.1 Phase 4 행 `범위` 칸, 공격 13 기대 로그,
  N6.2 6a 문장, U-26 (a) 문구 -- `draft_b26_plan_patch.md` §1~§6의 정정 전부와 history H2·H4·Version History 5.20 행.
* B26-1 card를 Phase 2 진행 중에 병합하는 것(card `phase: 2`).
* kcl_residual 선언의 `rail_nets` 키를 B26-1에서 거부하는 것(N3.16 정정 문구).
덮지 않는 것:
* 레일 전압(`supplies_v`, 스칼라 `vdd` 폴백 삭제, IC11)과 옛 키 거부 게이트 일반형 -- MG1, U-26 (a) 그대로.
* B26-2(극성, 사용자 결정 D1)·B26-3(MNA 고정 노드, 사용자 결정 D2)의 방식과 앞당김 -- 각 card의 착수 조건으로 따로 묻는다.
* B26-1의 V3 처리(U1) -- 별도 결정. V3 면제(변이 id)는 이 기록의 target이 아니다.
* 판정 표(`plan_tables_hash` 입력: N4.1 `ID`·`담당 Phase`·`강제 test`, N4.2 `도입`, N6.1 `Phase` 열, N3.12.2) -- 바꾸지 않는다. 바뀌면 이 승인이 아니라 `plan_tables` 승인이 필요하다.
* analog-grammar 이름 집합(`netclass.RAILS*`)의 처리(백로그 B35·B36, 게이트 변경은 별도 승인).

## 재검토

B26-1이 병합되지 않은 채 Phase 3 M 카드가 `stick_diagram`·`sizing_recipe`를 나누기 시작하면, 3항(앞당김)은 효력을 잃고 B26-1 card의 편집 범위를 새 모듈 기준으로 다시 잰다.
```

주의(target 값): V3 도구와 V7 도구는 head 트리의 **모든** decision 승인 기록 `target` 원소를 면제 id로 읽는다(`reachability._approved_ids`). 그래서 target은 def id(`<파일>::<qualname>`)나
변이 id(`<모듈>:<qualname>:<연산자>:<경로>`) 모양이 아닌 이름(`U2-B26-BEFORE-PHASE3`)으로 둔다 -- 기존 결정 기록 `U-38`·`U-39`·`C9-IC11-SPLIT`과 같은 방식이다.
