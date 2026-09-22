---
id: 20260922-c2-extract-repro-path-line
date: 2026-09-22
target_kind: decision
target: C2-E4
scope: C2 추출 재현 비교에서 이관본 머리글 `# 원본 경로:` 주석 한 줄을 제외(파일 이름만 대조)
---

## 사용자 원문

> 비교 기준 조정 (Recommended)

## 범위 설명

근거: C1 도구가 머리글 둘째 줄에 `--source` 절대 경로(worktree 경로)를 적어, 격리 복제본에서의 재추출은 그 줄이 반드시 다르다
(C2 test-author 보고). 그 줄은 주석이라 실행에 영향이 없다. 덮는 것: design 10 §6.1 C2 증거 4의 비교에서 그 한 줄 제외, 그 줄의
끝 파일 이름 대조. 덮지 않는 것: 실행 동등성(20쌍 stdout 바이트 동일), 도구 수정(백로그 B5).
