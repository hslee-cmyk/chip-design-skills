---
title: graph-consumption -- design 이력
design: graph-consumption.design.md
date: 2026-11-03
---

# graph-consumption design 이력

> 본문에 넣지 않는 경위를 둔다. 현행 규칙은 본문이 정본이다.

| 판 | 내용 |
|---|---|
| v0.1.1 | 위임 A-50~A-52: J1 목록 추가, 창 미상 조건(옛: 창 미상 처리: `STATUS_UNKNOWN` 그대로, `iv_headroom` 예산은 HC design §8.), 호출자 둘, G3. 독립 판정 전 |
| v0.1 | GC-D 일부 첫 판: GC-1, GC-8(O-191 통합 병합 짝). 나머지 GD는 해당 card 전 개정. 독립 검증·승인 전 |

## v0.1 §2 초기안(A-32로 대체, 2026-11-04)

**진입점 초기안**(`_module_map` 'entry'는 근거가 아니다 -- F-G27):

| 진입점 | 근거 |
|---|---|
| `pipeline/stage_a.py: run_stage_a` | 단계 A 사용자 입구 |
| `pipeline/stage_b.py: run_stage_b` | 단계 B 사용자 입구 |
| `search/find_front.py: find_front` | 탐색 입구 |
| `search/front_query.py: node_across_front` | 사용자 S3 조회(N3.1-5 출력 함수 면제 자리) |

OS-2 `run_plan`은 그 card 병합 때 더한다(기준 변경 아님 -- 대상 넓힘).

**출력 함수 초기안**: `run_stage_a`·`run_stage_b` 안의 보고 함수와 `node_across_front`. 기준은 N3.1-2다.

이 두 목록은 **미측정 초기안**이다(M-G9 미룸). 검증자가 GC-1에서 독립 스크립트로 재고, 다르면 GC-1을 멈춘다(N3.1-2). 이 절차가 그대로라 O-225로 약해지지 않는다.
