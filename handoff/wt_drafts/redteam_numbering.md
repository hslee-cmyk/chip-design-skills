# redteam 번호 메모 (오케스트레이터용, 2026-10-01 B33 개정 agent)

B33 개정 중 `_drafts/draft_v3_exempt_binding.spec.md`·`draft_v3_scope_policy.spec.md`·`v3_cards_revision_log.md`가 12:04~12:10에 다른 agent에 의해 수정되고 있어
(내가 시작한 11:30에는 로그가 30초 전 수정) 두 V3 초안은 **고치지 않았다**. 대신 확인한 현재 상태와 남은 일을 적는다.

## 확정 번호 (design v4 D-18 원칙: 미리 나눔, 병합 순서 무관 -- review_b33 S6 제안 그대로)

| 번호 | 디렉터리 | card | 현재 초안 상태(12:11 grep) |
|---|---|---|---|
| 32 | `32-moved-defs` | G1 `20260930-p3-gate-move-aware` | `draft_p3_g1.spec.md` 125행 이미 32 (그 초안은 "design v5 D-18"을 인용) |
| 33 | `33-v7-registry-edges` | B33 `20260930-v7-registry-edges` | `draft_b33.spec.md` 개정 완료(문구 변경 338행·oracle 표·계약 14·결정 필요 항목 '번호') |
| 34 | `34-v3-exempt-binding` | `20260930-v3-exempt-binding` | 그 초안 82·220행, 승인 초안 36행 이미 34 |
| 35 | `35-v3-changed-scope` | `20260930-v3-changed-stmt-scope` | 그 초안 89행, 승인 초안 49행 이미 35 |

→ 두 V3 초안은 번호 수정이 이미 반영돼 있다(내가 고칠 것 없음).

## 남은 일 (오케스트레이터)

1. `draft_phase3_design_v4.md` 210행·406행(D-18)의 B33 이름 `33-v7-graph-edges` → **`33-v7-registry-edges`**(B33 초안·G1 초안이 쓰는 이름). G1 초안이 "design v5 D-18"을
   인용하므로 v5가 있으면 거기에 반영.
2. B33은 `build_graph`(V3 인벤토리와 공유)를 바꾼다. 34·35가 B33보다 먼저 병합되면 그 V3 합성 케이스 기대가 B33 계약 14(무동작)에서 다시 판정되고, B33이 먼저면
   34·35 test worktree는 B33 그래프 위에서 만든다. 공격 34·35는 V3 합성 저장소라 레지스트리 바인딩·생성자를 쓰지 않으면 인벤토리 변화가 없을 것으로 보이나 실측하지 않았다
   (그 초안들의 구성이 아직 바뀌는 중).
3. 각 card의 무동작 redteam 목록은 "그 시점 `attacks/` 전체"로 쓰면 병합 순서와 무관하다(B33 계약 14가 그렇게 적었다).


## 2026-10-01 B33 최종본 준비 agent 추가 (Phase 3 drafts 담당에게 -- 이 agent는 Phase 3 초안을 고치지 않았다)

- B33 이름 확정: `33-v7-registry-edges` (최종 card `_drafts/draft_b33.final.spec.md`, 승인 초안 `_drafts/approval_20260930-v7-registry-edges.md`). 사용자 승인 2026-10-01(Q1 (a)).
- `draft_phase3_design_v5.md`: D-18 표 519행·§ 222-224행은 이미 `33-v7-registry-edges`(정정 완료), 666행은 v4→v5 변경 기록 행이라 옛 이름이 남는 것이 맞다.
  단 224행 "지금 세 card 초안은 각각 32·32·33을 적고 있"는 2026-10-01 현재 사실과 다를 수 있다(B33·34·35 초안은 이미 33·34·35) -- 재측정 권고.
- `draft_phase3_design_v4.md` 210·406행은 옛 이름 `33-v7-graph-edges` 그대로. v4가 v5로 대체된 사본이면 둘 것, v4를 커밋 대상으로 쓰면 `33-v7-graph-edges` → `33-v7-registry-edges` 2곳 수정.
- 위 "남은 일 1"은 v5 기준으로 끝난 상태다(v4만 남음).
