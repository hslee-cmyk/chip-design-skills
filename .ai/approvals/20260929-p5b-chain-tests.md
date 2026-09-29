---
id: 20260929-p5b-chain-tests
date: 2026-09-29
target_kind: diff
target: fe5a50f54e622c51dbb1b02a7e68528d0559c104c94a6c13988712a36c845539
diff_base: 98bd969236b4407d6e8ff19af267ecb77c8f116f
diff_head: 3adc1733dc36ed96e6942cc3eb563eb9a6c53031
diff_path: skills/analog-gmid-design/assets/tests/unit/test_selftest_sizing_recipe.py
scope: P5b -- 삭제되는 telescopic CMRR·PSRR 사슬을 판정하던 unit test 3개(s066·s068·s069) 삭제 DEC-40 승인(V5 발견 3건), 삭제 범위에 사슬 전용 상수·필드 2개 추가
---

## 사용자 원문

> 승인

(질문: P5b에서 삭제되는 telescopic CMRR·PSRR 사슬을 판정하던 unit test 3개 -- `test_s066_family`(폐형식 CMRR 앵커 3개),
`test_s068_family`(CMFB CMRR 앵커 128.72/146.72 dB·A_c·자기회귀·가드), `test_s069_section`(PSRR 89.38 dB 앵커·가드) -- 를 함께 지우는
V5 기준 약화(diff_hash fe5a50f5…) 승인, 그리고 삭제 뒤 고아가 되는 모듈 상수 `_TELESCOPIC_FIXED_BASE`(파일럿 넷 이름 Vbias1~4)와
`SizingContext._open_loop_gains_cache` 필드를 삭제 범위에 더하고 spec card 줄 번호를 정정 -- 선택지 '승인'.)

## 범위 설명

근거(auditor 1차 시도 순서 3, base 98bd969 원문과 호출 추적): 세 test가 부르는 피검 코드는 삭제 사슬뿐이고, 계산 경로에 함께 지나가던 공유 함수
(`_mna_solve_smallsignal`·`_hashable_key`)는 다른 test와 파일럿 운영 경로가 계속 부른다. 사라지는 것은 31소자 부분망 고유의 수치 앵커뿐이다.
T 전체 스위트에서 삭제 대상 호출은 이 세 test뿐이었다.
덮는 것: 위 diff_path의 base→T 변경(test 함수 3개·fixture `s067_state`·`s068_state` 삭제, import 이름 2개 제거), spec card
`20260923-d-delete-telescopic` 계약 1·7의 삭제 범위 추가(상수·필드 2개)와 줄 번호 정정.
덮지 않는 것: 남긴 `test_s065_section`·`test_s067_family`의 판정 변경, 다른 test 파일, 이 T blob과 다른 내용.
