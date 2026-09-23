---
id: 20260923-v4-decision-exempt
date: 2026-09-23
target_kind: diff
target: 3d5e7fe2534f00a2a2b3234cb85e767dd78040b2d2b97683d0227bae7a73e307
diff_base: 523d0ced2ad7acc1036feaa166467e1b88c30dd3
diff_head: 8699d8aa08a8308fe4f34b490e9543341c36091c
diff_path: docs/02-design/specs/20260923-v4-decision-exempt.spec.md
scope: 게이트 변경 C13 -- test_lint.py가 `target_kind: decision` 승인 기록의 test id를 V4 규칙 (1) 면제로 읽는다(V3 선례와 같은 방식, 규칙 (2)~(5)는 불변)
---

## 사용자 원문

> V4 면제 게이트 변경 (Recommended)

## 범위 설명

덮는 것: spec card `20260923-v4-decision-exempt`(8699d8a) 전체 -- `tools/gates/test_lint.py` 수정(code-author)과 redteam 합성 케이스
4가지(test-author). 면제는 규칙 (1)에만, 승인 기록에 적힌 test id에만 적용된다. 판정식·다른 규칙·공격 06 적발은 불변.
덮지 않는 것: 다른 게이트 도구, C9에서 실제로 면제할 test id의 승인(그것은 C9 착수 전에 따로 받는다).
