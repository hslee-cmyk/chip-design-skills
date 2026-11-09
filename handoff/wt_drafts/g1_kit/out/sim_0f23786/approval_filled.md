---
id: 20260930-p3-gate-move-aware
date: 2026-10-01
target_kind: diff
target: 3adeb714cebc710a7be67b6c69235ad51e9080cbb1e037a89ae370c25367b4cf
diff_base: c7dde68e5c6a5f287708f46096b3dcd3bc1f18db
diff_head: eeaec120c92a96b95aa9780e1bf903278279b8c5
diff_path: docs/01-plan/features/gain-budget-gmid-sizing.plan.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
diff_path: docs/02-design/specs/20260930-p3-gate-move-aware.interface.md
diff_path: docs/02-design/specs/20260930-p3-gate-move-aware.spec.md
scope: 게이트 변경 spec card 20260930-p3-gate-move-aware(G1 -- V3 mutate_changed.py·V6 source_lint.py·V7 reachability.py가 옮긴 단위(design 30 §3 MOVED: M-0·M-0h·M-1~M-4, 클래스 골격, 최상위 문장, qualname 중복 제외)를 같은 경로의 base가 아니라 이동 원본과 비교 -- 판정식은 그대로, 옮긴 def(경로·qualname·def_hash 모두 일치)는 V3 대상 def·V7 새 def가 아니고 V6 이전 항목 수는 원본 맥락)와 design 05 §10 V3·V6·V7 행·거부 증명 줄 문구, 계획 N3.10 이동 규칙 한 문장 -- 사용자 결정 UD-5 (가) 전역 이동 인식 규칙
---

## 사용자 원문

> (모의) (가) 전역 이동 인식 규칙 (Recommended)

(AskUserQuestion (모의) 질문 원문: `_drafts/phase3_approval_question.md` UD-5 문단을 올린 그대로 -- 질문 본문·선택지 세 개((가) 전역 이동 인식 규칙 (Recommended) / (나) 승인 기록에 선언한 이동만 인정 / 보류)와 각 설명을 세션 기록(jsonl)과 바이트 대조해 붙인다(B33 키트 `check_user_quote.py` 선례). 답: "(모의)".)

## 범위 설명

덮는 것:
* spec card `20260930-p3-gate-move-aware` 전체(계약 0~13)와 interface card. 게이트 코드(code-author):
  * `tools/gates/reachability.py`: `_strip_doc`·`def_hash`의 유일한 정의(계약 8 -- `mutate_changed`는 같은 이름으로 import), `SourceIndex`(`units`·`global_names`·`binding_origin`, 파일당
    `ast.parse` 1회·`symtable` 1회), `moved_defs(base, head)`(M-0·M-0h·M-1~M-4 고정점, 클래스 골격 해시, 문장 단위, qualname 중복 def 제외), V7 `main`의 `new_defs`에서 옮긴 def 제외
    (경로·qualname·`def_hash` 대조)와 출력 `moved`·`move_rejected`. `build_graph`·도달 계산(B33 R1~R3)은 바꾸지 않는다.
  * `tools/gates/mutate_changed.py`: 대상 선택에서 옮긴 def를 먼저 빼고 나머지는 범위 정책(`20260930-v3-changed-stmt-scope` 계약 1) 그대로, 면제 대조(`20260930-v3-exempt-binding`)
    불변, 출력 `defs`·`moved`·`move_rejected` 추가(기존 키 이름·뜻 불변).
  * `tools/gates/source_lint.py`: 옮긴 def 단위의 이전 항목 수 = 원본 파일 맥락의 원본 단위, 새 파일 `<module>` 이전 항목 수 += 그 파일로 옮긴 문장 단위의 원본 맥락 항목, 출력
    `moved`·`move_rejected`.
* redteam(test-author): 새 케이스 `tools/gates/redteam/attacks/32-moved-defs/`(design 30 D-18 배정 번호 32)와 `lib/rt.py` vcase 관찰 `"observe": "moved"`(계약 12 -- 선례 B28
  `tool_tmpdir`·`root_state`, 34 `out_jsonl`). 단계 = card 계약 12 표(red 7 + 거부 22 = 29단계 x 도구 3).
* 문서(오케스트레이터 문서 커밋, 패치 `_drafts/g1_kit/patch_g1_docs.py`): design 05 §10 V3 행 ①(범위 정책 card 문구 뒤)·V6 행·V7 행(B33 문구 뒤)에 '옮긴 단위는 이동 원본과 비교'
  문장, 같은 절 거부 증명 줄에 공격 32, 계획 N3.10 이동 규칙 줄(`0f23786` 533행) 끝 "V6·V7의 '새'도 같은 규칙" 한 문장. `plan_tables_hash` 불변(모의 확인).
* 무동작: 기존 redteam V3·V6·V7 케이스(먼저 병합된 33·34·35 포함)와 `--cases 0.5` 판정 불변, 과거 판정 기록 2건(`df36`·`dup-w-calc`) base·head 옮긴 단위 0(계약 11).

덮지 않는 것:
* 선언 기반 이동 인정(UD-5 (나)) -- 이 card는 전역 규칙이다.
* V3 연산자·면제 원소 형식·범위 정책 규칙 자체, V7 그래프 간선 규칙(B33) -- 바꾸지 않는다(합성 문장만 이 card가 가진다).
* 알려진 보수 비용: 바이트 그대로 옮긴 property 클래스의 `P.x`처럼 qualname이 겹치는 def는 옮긴 def로 인정하지 않는다(V3·V7 대상에 남는다 -- 엔진 4파일 qualname 중복 0).
* Phase 3 M card 각각의 판정 -- 그 card의 판정 기록이 `moved` 목록으로 보인다(design 30 §8 M행·§10 E2).
