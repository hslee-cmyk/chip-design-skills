---
title: offset-trim -- design 이력
design: offset-trim.design.md
date: 2026-10-15
---

# offset-trim design 이력

> design 본문(`offset-trim.design.md`)에 넣지 않는 경위·옛 문장을 둔다. 현행 규칙은 본문이 정본이다.

## H1. 버전 경위

| 판 | 커밋 | 내용 |
|---|---|---|
| v0.1 | 6898cac | TR-0 초안. 독립 검증 66/100(차단 B1~B5) |
| v0.2 | d4addd0 | 차단 B1·B3·B4, 비차단 N1~N13 반영. B2·B5와 TD-1~TD-9는 사용자 결정 대기 |
| v0.2 | bd695f2 | 사용자 결정 T-7~T-13 반영 |
| v0.2 | 2e05be8 | 사용자 결정 T-14(온도 sweep 범위) 반영 |
| v0.2 | 0f7332a | 재검증 82점의 차단 B6, M1~M6, X-T16, TD-10 대기 반영 |
| v0.2 | (이 커밋) | 사용자 결정 T-15(TR-2 병합 U16 뒤)·T-16(X-T15 확인) 반영 |

## H2. 본문에서 옮긴 경위 문장

- **pass 0**(v0.1·v0.2 초안): θ마다 원본 회로를 커널 평가해 I_u 유도의 출발값을 θ만의 함수로 만들려고 두었다. 사용자 결정 T-7(I_u = θ)로 출발값이 필요 없어져 삭제했다.
- **원뿔 분리**(v0.2 초안, TD-1 (가) 하한 유도안 전제): `current_cone`을 `cone`·`cone_trim`으로 나누고 `check_theta` 서명을 넓혀 `cone_trim` 위반을 후보 실패 `trim_cone_outside`로 두었다. T-7로 I_u가 θ 전류가 되어 대상이 없어 삭제했다.
- **고정점 반복·K_trim·ln I 이분**(v0.1 고정점 반복, v0.2 초안 ln I 이분 + K_trim = 2 + k_max): T-7로 평가당 커널 1회가 되어 모두 삭제했다. 관련 실패 사유 `trim_iu_unconverged`·`trim_iu_no_bracket`, 결과 칸 `perf.trim_kernel_passes`·S3 `trim_iu_amp`, 'I_u 반복 기록'도 같이 지웠다.
- **I_u θ 키**(v0.2, bd695f2): `trim<d>:unit`이라는 원소가 아닌 키를 썼다. `search_domain.py:62` `_current_bounds`가 `classes[key]`에서 KeyError가 나는 결함(재검증 B6)이라, 가중치 1 셀 전류원 `trim<d>_c0_src`의 전류로 바꿨다.
