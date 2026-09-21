---
id: 20260921-gate-output-utf8
date: 2026-09-21
target_kind: diff
target: 63d605ec3e534b41663cc29b2f222332a74579b87a32a30eee9a127723ea2210
diff_base: 63ae9b9258a2320132f20950a6f944cd2cd15d30
diff_head: 21c0b610266847d9a601b18cb2bcfcd393e5ff61
diff_path: docs/02-design/specs/20260921-gate-output-utf8.spec.md
scope: 게이트 변경 spec card 20260921-gate-output-utf8(게이트 진입점 UTF-8 출력) 승인 -- 부트스트랩 ⑤의 §12 전 과정 1회에 쓴다
---

## 사용자 원문

> UTF-8 수정으로 승인 (Recommended)

(질문: 메인 세션 재생에서 찾은 거부 메시지 한글 깨짐을 §12 변경 한 건으로 쓸지 -- spec card 초안
`docs/02-design/specs/20260921-gate-output-utf8.spec.md`, 반영 뒤 §13.4 재설치 필요. 선택지 중 위 항목을 골랐다.)

## 범위 설명

덮는 것: spec card `20260921-gate-output-utf8`(21c0b61의 blob `3c9a253a`) 전체 -- 게이트 진입점 16개가 로캘과 무관하게 UTF-8로
출력하는 게이트 변경, 그 판정 기준을 `tools/gates/redteam/`에 red 케이스로 두는 것, 반영 뒤 §13.4 재설치.
또한 이 변경의 1차 시도를 부트스트랩 ⑤ 역할 agent 공격 재생에 쓰고 §12 '재시도' 절차로 정리한 뒤 2차 시도를 실제 변경으로
진행하는 방식(사용자가 앞서 고른 '수동 재생 + 게이트 변경 1건').

덮지 않는 것: 판정 동작(허용·거부·exit code·메시지 문구)의 변경, `run_all.py --mode installed` 실행기 구현.
