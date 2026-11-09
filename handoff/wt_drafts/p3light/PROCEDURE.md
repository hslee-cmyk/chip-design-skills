# Phase 3 가벼운 절차 (2026-10-07 사용자 지시 "phase3를 가벼운 절차로 진행해.")

작업 장소: C:/Users/HSLEE/Documents/Todoc/fpga/gmid-light (clone, 브랜치 phase3-light, base 6df4bd7 = gate master).
gate 저장소·메인 저장소(chip-design-skills)·hook·master는 건드리지 않는다. 메인 저장소는 읽기만.

## 남기는 것
1. 코드 작성 주체와 test 작성 주체를 분리한다(같은 agent가 둘 다 쓰지 않는다).
2. 기존 test가 깨지면 조용히 고치지 않는다: 깨진 test 목록과 이유(예정된 변경인지, 버려도 되는 legacy인지)를 보고서에 적는다. assert 삭제·허용오차 확대·skip/xfail 추가는 보고서 '약화' 절에 반드시 나열.
3. 이동(M card)은 무변경 증명: 이동 전후 함수별 ast.dump(docstring 제외) 해시 같음 + import·재수출 줄만 차이.
4. 매 변경 뒤: 전체 pytest + E-INST·E-LIB(library 회로 instance 출력) base와 같음.
5. 커밋은 변경 하나당 하나, 메시지는 평문(트레일러 규칙 없음, Co-Authored-By 한 줄은 허용).

## 버리는 것
spec card·interface card·승인 기록·판정 기록 JSON·V1~V10·두 번 시도 운반·gate push·역할 worktree·T0/T1/B33/G1/FU 같은 gate·legacy 보존 card.

## 순서
B26-1(레일 선언 접근자, 1차 시도 산출물 재사용) -> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M8 -> M9 -> M10(진입점) -> F1(호출부) -> F2(shim 삭제).
