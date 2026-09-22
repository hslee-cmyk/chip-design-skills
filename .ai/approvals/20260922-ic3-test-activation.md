---
id: 20260922-ic3-test-activation
date: 2026-09-22
target_kind: diff
target: 7826a406f8760ea5042f0c1998753794a68cca42a405eecb4e0ee55b5acf9a98
diff_base: 3e4d0d226fa988a6a747a404f27103363c128885
diff_head: c11ece54730879c91e1b34f915b182e23a3ceb70
diff_path: skills/analog-gmid-design/assets/tests/contracts/test_ic3.py
scope: C8 IC3 -- 뼈대 pytest.fail()을 실제 IC3 검사로 바꾼 contracts/test_ic3.py의 DEC-40 승인(V5 발견 2건: 비교 완화·리터럴 변경)
---

## 사용자 원문

> 승인 (Recommended)

## 범위 설명

덮는 것: `contracts/test_ic3.py` base blob fcd70e9f -> head blob 94b0525a(필드 상수·완전성·이름 충돌·저장/로드 배선·library 9회로 원본
로드 오거부 0·연결 파일 픽스처). 이관본 stick Test 26 정정(blob 562cb34b)도 승인 질문에 보였다(도구는 발견으로 잡지 않음). 2차 시도는 R1대로
`v5-carry/20260922-ic3-completeness/`의 blob 2개를 복원한다. 발견 두 건 모두 검사 추가(B7 패턴), 판정 약화 없음.
덮지 않는 것: code 쪽 변경(IC3 코드·배선, common_gate_amplifier `_comment` 로드 결함 수정 -- 계약 5).
