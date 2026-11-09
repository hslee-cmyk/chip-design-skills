---
id: 20260930-p3-gate-move-aware
date: <승인일 YYYY-MM-DD>
target_kind: diff
target: <rev-parse>
diff_base: <rev-parse>
diff_head: <rev-parse>
diff_path: docs/01-plan/features/gain-budget-gmid-sizing.plan.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
diff_path: docs/02-design/specs/20260930-p3-gate-move-aware.interface.md
diff_path: docs/02-design/specs/20260930-p3-gate-move-aware.spec.md
scope: 게이트 변경 spec card 20260930-p3-gate-move-aware(G1 -- V3 mutate_changed.py·V6 source_lint.py·V7 reachability.py가 옮긴 단위(design 30 §3 MOVED: M-0·M-0h·M-1~M-4, 클래스 골격, 최상위 문장, qualname 중복 제외)를 같은 경로의 base가 아니라 이동 원본과 비교 -- 판정식은 그대로, 옮긴 def(경로·qualname·def_hash 모두 일치)는 V3 대상 def·V7 새 def가 아니고 V6 이전 항목 수는 원본 맥락)와 design 05 §10 V3·V6·V7 행·거부 증명 줄 문구, 계획 N3.10 이동 규칙 한 문장 -- 사용자 결정 UD-5 (가) 전역 이동 인식 규칙
---

## 사용자 원문

> <UD-5 답 원문 -- AskUserQuestion 답 그대로>

(AskUserQuestion <날짜·시각> 질문 원문: `_drafts/phase3_approval_question.md` UD-5 문단을 올린 그대로 -- 질문 본문·선택지 세 개((가) 전역 이동 인식 규칙 (Recommended) / (나) 승인 기록에 선언한 이동만 인정 / 보류)와 각 설명을 세션 기록(jsonl)과 바이트 대조해 붙인다(B33 키트 `check_user_quote.py` 선례). 답: "<답 라벨>".)

## 범위 설명

덮는 것:
* spec card `20260930-p3-gate-move-aware` 전체(계약 0~13)와 interface card. 게이트 코드(code-author):
  * `tools/gates/reachability.py`: `_strip_doc`·`def_hash`의 유일한 정의(계약 8 -- `mutate_changed`는 같은 이름으로 import), `SourceIndex`(`units`·`global_names`·`binding_origin`·`tree` -- D0a가 재사용, 파일당
    `ast.parse` 1회·`symtable` 1회), `moved_defs(base, head)`(M-0·M-0h·M-1~M-4 고정점, 클래스 골격 해시, 문장 단위, qualname 중복 def 제외), V7 `main`의 `new_defs`에서 옮긴 def 제외
    (경로·qualname·`def_hash` 대조)와 출력 `moved`·`move_rejected`. `build_graph`·도달 계산(B33 R1~R3)은 바꾸지 않는다.
  * `tools/gates/mutate_changed.py`: 대상 선택에서 옮긴 def를 먼저 빼고 나머지는 범위 정책(`20260930-v3-changed-stmt-scope` 계약 1) 그대로, 면제 대조(`20260930-v3-exempt-binding`)
    불변, 출력 `defs`·`moved`·`move_rejected` 추가(기존 키 이름·뜻 불변).
  * `tools/gates/source_lint.py`: 옮긴 def 단위의 이전 항목 수 = 원본 파일 맥락의 원본 단위, 새 파일 `<module>` 이전 항목 수 += 그 파일로 옮긴 문장 단위의 원본 맥락 항목, 출력
    `moved`·`move_rejected`.
* redteam(test-author): 새 케이스 `tools/gates/redteam/attacks/32-moved-defs/`(design 30 D-18 배정 번호 32)와 `lib/rt.py` vcase 관찰 `"observe": "moved"`(계약 12 -- 선례 B28
  `tool_tmpdir`·`root_state`, 34 `out_jsonl`). 단계 = card 계약 12 표(red 8 + 거부 23 = 31단계 x 도구 3 = 93 -- `draft_p3_g1.spec.md` 174행; 이 초안의 이전 판 'red 7 + 거부 22 = 29단계'는 `g1_kit/` 원본 초안에서 옮긴 낡은 수였다).
* 문서(오케스트레이터 문서 커밋, 패치 `_drafts/g1_kit/patch_g1_docs.py`): design 05 §10 V3 행 ①(범위 정책 card 문구 뒤)·V6 행·V7 행(B33 문구 뒤)에 '옮긴 단위는 이동 원본과 비교'
  문장, 같은 절 거부 증명 줄에 공격 32, 계획 N3.10 이동 규칙 줄(`0f23786` 533행) 끝 "V6·V7의 '새'도 같은 규칙" 한 문장. `plan_tables_hash` 불변(모의 확인).
* 무동작: 기존 redteam V3·V6·V7 케이스(먼저 병합된 33·34·35 포함)와 `--cases 0.5` 판정 불변, 과거 판정 기록 2건(`df36`·`dup-w-calc`) base·head 옮긴 단위 0(계약 11).
* 덮는 G1 card 판과 질문 뒤 변경: 질문 문안이 가리킨 판은 `_drafts/draft_p3_g1.spec.md` sha256 `b8a47418c8923b6082037986d57f3e9cd9b2bae8990939b39319cf0f0b7013a6`
  (`phase3_approval_question.md` 137행). 질문 뒤 2026-10-02 02:00:59~02:01:12 KST에 G1 재측정 agent(세션 subagent 기록 `agent-a50ba62f02e834ef3.jsonl`)의 Edit 3건
  (tool_use `toolu_01F9Q4jef4pUTnXqgJ1AKK1C`·`toolu_01RR2RrB6LDETErztSb2X2Fc`·`toolu_01TuHeBJdsRPAE2uaNDvHdgC`)으로 `b758140a8744fc951dac22c9f1a651423b2214c0f60fce27af5780aa0c385e20`이 됐다.
  세 Edit는 '판정 유형 근거'에 v8.4 재검토 한 문장, '작성 전 실측' 머리에 v8.4 재검토 문단(공격 32 측정판 31단계 x 3 = 93 재측정), '작성 전 실측' 9 (b) 끝 문장과 (c) V3·V6·V7 잔여 측정을 더한 것뿐이다 --
  모두 측정 기록이고 '관찰 가능한 계약'(계약 0~13, 계약 12의 redteam 32 단계 표 -- 31단계 = red 8 + 거부 23)은 바이트 그대로다(지금 판에 세 Edit를 거꾸로 적용하면 `b8a47418…`이 나온다 -- 2026-10-02 실측).
  그 뒤 2026-10-02 r3(G1 착수 리허설)와 착수 재측정(gate `master` `4a286f0`)이 card를 `89719c852cdd88571e13909285ae041bbc49888f5a39968781753129ad63d8ff`로 바꿨다 -- 차이는 '의도' 한 문장(게이트 밖 `changed_defs`·`def_hash`
  호출 스크립트 수 4 → 8)과 '작성 전 실측'(재측정 문단 순서 정리, 2 이름 충돌의 design 30 33줄 문장, 5 게이트 밖 호출 목록, 착수 재측정 문단 `4a286f0`)뿐이고 나머지 11절(머리 블록 포함 --
  '관찰 가능한 계약' 계약 0~13과 계약 12의 redteam 32 단계 표 31단계 = red 8 + 거부 23)은 `b758140a…` 판(사본 `_drafts/draft_p3_g1.spec.pre-r3.md`)과 바이트 그대로다(절 단위 대조, 2026-10-02 실측).
  그 뒤 card 35 병합본 재측정(gate `master` `a17b8bd`, 2026-10-02 G1 재고정)이 card를 `a6615951c0bff060acc0798a282bb405d6e15321ed5b18ba09678a9988c3f9a3`로,
  gate `master` `dafe5cf` 착수 재측정(2026-10-06 -- 무동작 기준선 재취득·키트 환경 원인 확인)이 `72d8ff60eecc88015ab4d461cd7e1416819dc688d9bd87f0d6983a7845f515fd`로 바꿨다 --
  두 번 모두 차이는 '작성 전 실측' 절뿐이고(`a17b8bd` 재측정 문단 +20줄; `dafe5cf` 재측정 문단, `4a286f0` 문단 끝 한 구절, 문단 순서 줄) 나머지 11절(머리 블록 포함 --
  '관찰 가능한 계약' 계약 0~13과 계약 12의 redteam 32 단계 표 31단계 = red 8 + 거부 23)은 `89719c85…` 판과 바이트 그대로다(절 단위 대조, 2026-10-06 실측).
  그 뒤 독립 검토 반영(2026-10-06 r1g -- `_drafts/review_g1_dafe.md` §3 (a)·(b))이 card를 `93a85998b8fd006f43c5b62af6cdc1f997acd80be30ac7606c2acd5299f7fa67`로 바꿨다 --
  차이는 '작성 전 실측' 절 끝에 덧붙인 정정 메모 10뿐이다(계약 12 "(같은 이유)" 구절은 픽스처 의존 -- `overwrite-similar` M-0에서 `not_targeted` 12, 근거 계약 4·design 30 §5.5.2, 기대값 무변경;
  qualname 중복 def의 `targets_by_def` 사실). 나머지 11절(머리 블록 포함 -- '관찰 가능한 계약' 계약 0~13과 계약 12의 redteam 32 단계 표 31단계 = red 8 + 거부 23)은 `72d8ff60…` 판과
  바이트 그대로다(계약 문장 무변경, 절 단위 대조, 2026-10-06 실측).
  G1 card 커밋 때 card가 `93a85998…`과 또 다르면 그 차이가 계약·redteam 표 밖인지 다시 재서 이 문단을 고친다.

덮지 않는 것:
* 선언 기반 이동 인정(UD-5 (나)) -- 이 card는 전역 규칙이다.
* V3 연산자·면제 원소 형식·범위 정책 규칙 자체, V7 그래프 간선 규칙(B33) -- 바꾸지 않는다(합성 문장만 이 card가 가진다).
* 알려진 보수 비용: 바이트 그대로 옮긴 property 클래스의 `P.x`처럼 qualname이 겹치는 def는 옮긴 def로 인정하지 않는다(V3·V7 대상에 남는다 -- 엔진 4파일 qualname 중복 0).
* Phase 3 M card 각각의 판정 -- 그 card의 판정 기록이 `moved` 목록으로 보인다(design 30 §8 M행·§10 E2).

<!-- 오케스트레이터: 이 초안은 Phase 3 design 승인(UD-0)과 UD-5 답을 받은 뒤에만 쓴다(G1 착수 조건). date·사용자 원문·답 라벨을 채우고,
     target·diff_base·diff_head는 문서 커밋(design 05·계획 패치) + spec card·interface card 커밋 뒤 fill_v3_approval.py로 채운다(BASE = 착수 때 gate master, HEAD = spec 커밋).
     diff_path는 그 사이에서 실제로 바뀐 네 경로(card 계약 13: spec card·interface card·design 05·계획서). 채울 때 이 주석은 지워진다. -->
