# design v1.13.0 (128dfc41) vs 계획 v6.34.1 (37d6b7e8) -- IT-2c gap 분석 (독립 gap-detector, 2026-10-22)

일치율 21/24 = 87.5% (G 0, S 1, N 7). 원문 보고는 오케스트레이터 세션 transcript(agent a8dd4f77) -- 요약 전사.

- S-1: 용량만 결측 toy (ii) 기대가 design 안에서 모순(41:812 vs 41:739, metrics_aux.py:164-166 B77). 뿌리 = 계획 (10)(c)(ii). = recheck3 S-B와 같은 건 -> 계획 다섯째 커밋에서 정정.
- N-1: 41:814 L12 (a) 봉인 통과 전제가 tol 미정 toy에도 붙음 -> k_max toy로 한정(계획 (12)(a)와 같게).
- N-2: U-101 (가') 이동 범위가 계획 (vi) '뿐'보다 넓음(writer_head 등) -- 위임 범위 안, '원래 취지와 다름 아님' 한 줄.
- N-3: git grep 'ss_circuit(' 가 def 줄도 잡음 -> 정의 제외 명시.
- N-4: ss_nodal Undefined detail 키 'devices' -> 기존 'elements'로.
- N-5: 저항 판정 술어가 ss_circuit.py와 ss_nodal 두 자리 -> ss_circuit.py 술어 하나.
- N-6: 실패 블록 이름 변경(metrics_ss -> ss_circuit)을 4.7-8 변화표에 적기.
- N-7: B75(kvl_sensitivity 0 근처 분모) 계획 몫 -- 백로그 유지.
미확인: (8)(b)~(e), (9), (11), 범위 4·5, 4.7-8a, 4.7-9 전문, 42 전체, 41:741 전제 코드 확인, c_s 계수 코드 대조, LOOP_CUT_KINDS 순서 직접 확인.
