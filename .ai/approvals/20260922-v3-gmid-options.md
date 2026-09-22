---
id: 20260922-v3-gmid-options
date: 2026-09-22
target_kind: diff
target: 7968d656f94a1331912c8f104e050cc4b32008930253095aeb1b0a0cbb25f664
diff_base: ee835d24b3dd7c8b764abdfeb64a6893e0b159da
diff_head: 7ad9d1fa7532177a06a5e4bc9c96d62219564ed3
diff_path: docs/02-design/specs/20260922-v3-gmid-options.spec.md
scope: 게이트 변경 C11 -- V3 도구 mutate_changed.py가 conftest의 --gmid-phase·--gmid-strict(인벤토리 표식 키만)를 넘기게 한다(design 10 §6.10)
---

## 사용자 원문

> 승인

## 범위 설명

덮는 것: spec card `20260922-v3-gmid-options`(7ad9d1f) 전체 -- `tools/gates/mutate_changed.py` 수정(code-author)과 `tools/gates/redteam/**`
케이스 3종(test-author). V3 판정식·conftest 거부 규칙 불변, 설치 사본 없음(재설치 불필요).
덮지 않는 것: 다른 게이트 도구.
