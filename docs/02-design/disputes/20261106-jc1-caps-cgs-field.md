---
id: 20261106-jc1
role: test
---
## 문제

위임 A-169 항목 3: `cap_query` 가 내는 새 칸(측정 CGS 열 값, 열 없으면 None)에 대한 두 줄짜리 lut test 를 요청받았다. 그러나 그 **칸 이름**이 interface card 에 없고(§1~§9 어디에도 `Caps` 새 칸 없음), 엔진 소스는 열람할 수 없어 test 쪽에서 정할 수 없다. 추측한 이름으로 test 를 쓰면 거짓 red/green 이 된다.

## 요청

오케스트레이터가 칸 이름을 정해 주세요(interface card §1 '신규 시그니처'에 `Caps` 칸 추가 또는 위임 메시지에 이름 명시). 이름이 오면 test 를 `tests/lut/test_cap_query.py` 에 둔다:
- CGS 열 있음(`toy_cap_arrays` + `CGS_n`, `CGB_n` 없음 포함) -> 새 칸 == 열 값(격자 마디 조회, 비트 동일), 기존 `cgs`(= cgg − cgd)·`model`(cgg_minus_cgd_at_gs) 불변
- CGS 열 없음 -> 새 칸 is None

이 항목만 보류한다. 나머지(A-169 1·2·4)는 커밋했다.
