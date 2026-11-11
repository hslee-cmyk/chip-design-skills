### N6.19 card CL-1 -- oracle 닫기(Z1): e_m 폐지 뒤 front 점 판정 확정(사용자 결정 O-178; card ME-1 대체 -- **원래 취지와 다름 -- 승인됨(O-182)**(새 card와 실측 자리 -- N5.3 Q-CL1))

**근거·사실**: 사용자 결정 O-178(`wt/_drafts/user_decisions.md` O-178 행), 재분석 `wt/_drafts/evidence/2026-10-29/em_reanalysis.md`·`z1_closure.md` §1~§8(경위·toy 실측은 history). 옛 card ME-1(모델 오차 측정 실행, 7a)은 e_m 폐지로 삭제한다(옛 본문 history).

**범위**(정의 = DEC-72 (1)~(5); 새 cache·memo·sctx 슬롯·사본 0; 필드·자리 이름은 design): (1) 정의 동일성 관문 -- 모든 대응 행에서 엔진·oracle 정의 대조, 다르면 거부(닫기 앞) (2) oracle 닫기 -- 활성 제약 oracle 여유 ∈ [0, 분해능] 밖인 front·선택 점에서 (점, metric)별 Δ secant 갱신(목표 분해능/2), 다제약 metric별 독립 동시 갱신, 재풀이 = 그 점의 실현 평가(N5.3 Q-W1) (3) 멈춤 규칙 셋(DEC-72 (3)) (4) 엔진 결함 분류(E-0·정의 위반·닫기 비수렴)와 판정 뒤집힘의 대조 기록(oracle 판정 기록 칸, record_id 참조) (5) U-122 판정(card LA-0 (5) 대조표 입력 -- 이득·rout metric의 E-1 판정, 닫힘 = 규칙 결함 0건 그리고 판정 불능 0건) (6) 재작성 범위(같은 변경에서 삭제): S0 필드 `model_error`·spec `derived.model_error_<metric>`·`value_from_model_error`·`verified_by.max_error`·`model_error_ref`·`E/metrics/model_error.py`, `E/search/ss_constraints.py` c 정규화의 e_m 항.

**착수 조건**: N5.3 Q-W1 결정 + Δ 정본 자리 계획 개정·검증·승인(DEC-72 (5) -- 정본 자리가 없으면 만들지 않고 멈춘다, graph 규칙 6) → design → design↔계획 gap. 선행 card: oracle OP-3·OP-5·OP-10·OP-11, 엔진 EO-1(엔진 점 → oracle 입력 생산자·판정 배선)·PW-1a·VB-1, metric 계산 코드를 바꾸는 DE-1·NL-1·UB-1·IT-2. held-out 회로는 쓰지 않는다(U-75 (3)).

**완료 조건**(검증자 판정 -- 동작 변경, O-34 (1); 결정성 비트 동일): (1) 정의 관문 toy -- 엔진·oracle 정의가 다른 대응 행 → 거부(base = 관문이 없어 그 행이 oracle 판정으로 그대로 넘어감 -- red) (2) 닫기 toy(합성 회로) -- 도달 가능 점이 oracle 여유 [0, 분해능]으로 닫힘·secant 갱신식·다제약 동시 갱신 (3) 멈춤 toy 셋 -- oracle 진전 없음 / 갱신점 E-0 실현 불가 / 선언 반복 상한 (4) **O-178 착수 조건 실측을 완료 조건으로 둠**(**원래 취지와 다름 -- 승인됨(O-182)**, N5.3 Q-CL1; O-178 원문 = 착수 조건 -- library 닫기 반복 수·t_oracle은 닫기 구현(이 card) 없이는 잴 수 없음): library 13회로(O-182 Q-LB1) front 점의 닫기 반복 수·oracle 실행 수, t_oracle(oracle 1회 시간), σ_in(MC metric) 닫기 반복 수와 비용을 (회로, metric)별로 판정 기록에 적는다 -- 비용이 front 예산(O-173 C13·U-47)을 넘으면 멈추고 사용자에게 보고 (5) Δ writer 하나·새 cache 0·사본 0(`git grep`·블록 READS), 재작성 범위 삭제 grep 0 (6) U-122 판정 기록 (7) N6.3 공통.

**순서**: EO-1 뒤, card LA-1 완료 판정 앞(LA-1 완료 조건 4 oracle 다리), 단위 11 앞. 뒤따름: LA-1 완료·단위 11·A' 판정(DEC-98).

