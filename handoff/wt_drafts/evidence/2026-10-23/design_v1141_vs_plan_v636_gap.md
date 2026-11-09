# design v1.14.1 (8f755b05) vs 계획 v6.36 -- IT-2c gap 분석 (독립 gap-detector, 2026-10-23, 요약 전사)

일치율 엄격 23/26 = 88.5%, 가중 94.2%. G 0, S 1, N 6.
- S-1: 완료 조건 (9)(S4-나)(b)(c)(P:1536)와 v6.36 R0(P:604)가 계획 안에서 충돌, design이 (9) 대상을 region_rows로 좁혀 해석(D41:716·810) = 계획 밖 결정 -> 계획 정오: (b) region_rows kind {포화,triode}, 창 전체 {포화,triode,전도}; (c)(ii) _conduction_rows 제외(READS만 허용); (c)(i)(iii) _conduction_rows에도 적용, L8 (h)에 AST 단언 추가.
- N-1: 'e ∥ CM' 정의 불능은 기본 포트 뷰에서 도달 0(가중 ±1/|D| 직교) -> 계획 목록 정오, '선언 뷰 선언 가중' 구절 삭제.
- N-2: S1v 지문 영향 -- default_port 식별 칸으로 13회로 모두 한 번 바뀜(위임 범위 안 다름) -> 계획 1줄 정오.
- N-3: θ f_component_undeclared 값 삭제 = 반영; 계획 1524 '사유 기록' 옛 문언 정오.
- N-4: D40:2092 IT-2c helper 목록에 writer_head 잔존 -> design 정정.
- N-5: D40:1266·1268 DEC-23 정의 칸 낡음(A_dm·gain 제약 뷰) -> 'DE-1 (c)에서 (나′)·기본 포트 뷰로 개정' 표지.
- N-6: D41:734 ③ 괄호 사실 오류(collect_views는 씨앗 0일 때만 view_required, views.py:83-85) -> 문언 정정(결과·fail-closed 불변).
미확인: D41 GV-1 표기 행, writer_head 엔진 호출자 grep, views.py:66-74 입력 0 동작.
