---
id: 20260930-v3-history-clone
date: 2026-09-30
target_kind: diff
target: f9a02d8532119b0824aa61957960c4e5e303bd327af6ca831025c2388b80ecc7
diff_base: 148bd6de8b775ca4b6dda9d77b79ec881ea204fc
diff_head: d99919c6b7f1d04f74a9f2dd96902fc6eeadcebc
diff_path: docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
diff_path: docs/02-design/specs/20260930-v3-history-clone.spec.md
scope: 게이트 변경 spec card 20260930-v3-history-clone(V3 mutate_changed.py 사본을 --head 격리 복제본으로, 기준 실행 실패 = ERROR exit 2, 임시 복제본 누수 없음)과 design 05 §10 V3 행 ④ 개정 승인
---

## 사용자 원문

> 승인 (Recommended)

(질문: d99919c(spec card 20260930-v3-history-clone + design 05 §10 V3 행 ④ 개정) 승인 -- 선택지 '승인 (Recommended)'.
앞서 사용자: "1부터 4까지 다 개선해"(B28 포함), "끝나면 push하고 B28 진행해")

## 범위 설명

덮는 것: spec card `20260930-v3-history-clone` 전체(계약 1~8), design 05 §10 V3 행 ④ 문구 교체(임시 복사본 → `--head` 격리 복제본, 기준 실행 실패 = `ERROR`).
기준 약화가 아니다(기준 실행 실패는 지금 FAIL, 이후 ERROR -- 둘 다 거부). 재설치 불필요(설치 사본 없음, §4.4 캐시에서 실행).
덮지 않는 것: V3 연산자·인벤토리 규칙(①~③)·면제 규칙, 다른 V 도구, merge_gate.
