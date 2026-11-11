### N6.45 card LY-1 -- MOD7 행 구성 재작성(LY13)

**근거**: LY13, LY2·LY5 개정, DEC-84 개정, S §2-8. **범위**: 레이아웃 입력에 실현 손가락 (m, w_f) 기록 참조(계약 입력 개정), MOD7 손가락 후보 블록(as-built `finger_candidates`)·nf 재선택 삭제, 행 = FP-1 행 구성 함수, m·w_f 변경 = W_request(LY3 -- 요청 레코드 {device, nf, finger_w, reason}, 요청 nf = card FS-1의 실현 정수화 함수 호출(LY3 (ii) -- 탐색 스냅샷 `DeviceOp.W` 참조) + 패턴·행 최소 조정); LY5 (i)의 nf 조정을 요청으로. **완료 조건**: 패턴·접기·hub 병합 toy가 사이징 손가락으로 돎, 요청 nf toy(정합 칸 max_i 목적식·선언 정수비 파생·최소 조정 -- 손계산 기대값), 실현 정수화 정의 1곳·레이아웃 쪽 둘째 구현 0(`git grep`), nf 재선택 정의 `git grep` 0, LR8 행 안 폭 하나가 구성으로 성립(위반 0 단언), O-229 2 범위. **순서**: LA-1a + LA-1 뒤(**LA-1 비차단** -- LA-1 경로에서 MOD7이 돌지 않음, O-229 4), FP-1 뒤, 단위 9 MOD7 design 안.

