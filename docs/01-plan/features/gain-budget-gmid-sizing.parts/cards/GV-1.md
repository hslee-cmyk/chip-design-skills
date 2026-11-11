### N6.27 card GV-1 -- 판정 gain 전달 뷰 소비 통일(v6.35.1 둘째 커밋, 검증 S-1)

**근거**: graph 규칙 1 -- '판정 gain 전달 뷰'(gain 제약 판정용 -- v6.36 O-118 6번으로 ICMR·DEC-23 A_dc와 분리, 그 둘은 기본 포트 뷰)의 정본 = S1v writer `s1v_fields`가 쓰는 값 하나 -- **이 card 착수 때 만든다**(소비자가 GB4·block_residual뿐 -- 만들면 배선; 선택 규칙(결정 대기 뷰·다른 gain 뷰 둘 이상 등 v6.35.1 (i)~(vii)의 gain 쪽)은 착수 전 계획 개정으로 정한다). as-built GB4 achievability(`E/metrics/achievability.py:347-349` -- gain 표지를 보지 않고 첫 전달 뷰를 골라 그 뷰에서 `gain_ss_db >= G` 가능 여부를 판정)와 block_residual(`E/metrics/CONTRACT.md:1093` '뷰 = 첫 전달 뷰')이 같은 뷰를 다른 규칙으로 고르는 둘째 생산자다(integ/it12 `1fa7b1e5` 확인; 검증 `wt/_drafts/evidence/2026-10-23/plan_v6351_validation.md` S-1). **원래 취지와 다름(승인됨 O-117)**: 기존 위반을 IT-2c에서 고치지 않고 이 card로 미룬다.

**범위**: (1) achievability(GB4)와 block_residual, 그리고 achievability가 같은 `view`를 넘기는 `_headroom` 버퍼 창 보고(`E/metrics/achievability.py:263-275` -- 재검증 N-1)가 S1v 정본 값을 READS로 읽는다 (2) 첫 전달 뷰 대체 식을 지운다 -- 정본 값이 정의 불능이면 그 판정·보고도 정의 불능(사유 그대로, fail-closed); GB4에서 정의 불능은 정지가 아니라 '판정 안 함 + 사유'로 보고하고(재검증 N-2), 버퍼 창 보고에는 버퍼 창 항목이 없다 (3) `E/metrics/CONTRACT.md:1093` 문언 정정.

**범위 3 추가**(v6.38.3 -- N6.35 E-10, **원래 취지와 다름**: 옛 문언은 L 주인 할당 첫 뷰를 범위 밖으로 두었다): `l_classes._main_path_starts`의 첫 뷰 대체를 지우고 뷰 사이 규칙은 design에서 물리로 정하며 못 정하면 L 주인 할당 정의 불능(fail-closed) -- 같은 '첫 뷰 대체' 결함 군·같은 S1v 뷰 READS라 새 순서 규칙 0; 완료 toy는 N6.35 E-10 행.

**범위 4 추가**(v6.38.3 일곱째 커밋 -- N6.35 E-33, 결정 재검토 #4; **원래 취지와 다름**: U-24 CM 루프 예외(2026-10-08 Q1 R31 '예외 확정')를 바꾼다): CM 루프(`cm_loop`)도 다른 루프 뷰와 같은 GB2 출구 게이트 정지(안정도 제약 미선언 = 탐색 전 정지, `undeclared_loop_constraint`) -- `E/graph/s1v_fields.py:92`의 `cm_loop_unconstrained` INFO 갈래와 `E/metrics/ss_metrics.py:76·273` 경고 경로를 같은 변경에서 지운다(O-153); 같은 S1v writer `s1v_fields`라 새 순서 규칙 0; library 실측 CM 루프 보유 1(current_reuse -- `pm_cm_ss_deg` 선언)이라 발동 0; 완료 toy는 N6.35 E-33 행.

**변경 종류**: 동작 변경(O-34 (1) -- 뷰가 달라질 수 있음: 판정 gain 뷰가 첫 전달 뷰가 아닌 회로, 첫 뷰 대체로 값이 나던 정의 불능 회로(예: current_reuse 규칙 (i))); 변화표에 회로·원인.

**완료 조건**: (1) 판정 gain 전달 뷰를 고르는 식이 S1v writer 한 자리뿐(`git grep`·AST -- achievability·block_residual 안의 뷰 선택 식 0, 두 블록 READS에 그 S1v 값) (2) 13회로 변화표(뷰 id·GB4 판정·block_residual 값·버퍼 창 보고 -- 바뀐 회로마다 원인) (3) 정본 값 정의 불능 toy → GB4 판정·block_residual 보고 정의 불능(첫 뷰로 값이 나면 red) (4) N6.3 공통(graph 정본 -- 새 필드·cache 0, 바뀐 소비 배선의 소비자 ≥ 1). (5) N6.35 E-10 완료 toy(뷰마다 출발점이 다른 toy → 첫 뷰 결과 없음 -- base red) (6) N6.35 E-33 완료 toy(CM 루프 + 안정도 제약 미선언 → 탐색 전 정지 -- base 경고만, red; `cm_loop_unconstrained` grep 0).

**순서·착수 조건**: 선행 = IT-1 + IT-2 통합 병합(S1v 기본 포트 뷰 변경 뒤 -- 판정 gain 전달 뷰 값은 이 card가 만든다, v6.36); 착수 조건 = 계획 승인 → design(design 41 GB4·block_residual 절; 범위 4는 design 40 §5 H5·R31·design 41 §1.8·`E/graph/CONTRACT.md:660`·`E/metrics/CONTRACT.md:688·766` 정정) → design↔계획 gap → 착수 사실 재측정.

