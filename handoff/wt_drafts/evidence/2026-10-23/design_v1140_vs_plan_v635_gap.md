# design v1.14.0 (c545a528) vs 계획 v6.35 -- gap 분석 (독립 gap-detector, 2026-10-23, 요약 전사)

일치율 94.6%(계획 28항목) / 84.3%(design 자체 결정 7건 포함). G 1, S 5, N 6.
- G-1: ICMR 전달 뷰 새 입력 칸(SizingSpecDoc.icmr_view -> DcInputs.icm_view) = 계획 밖, graph 규칙 1·2·6 위반 후보. 정본 후보 graph/s1v views.
  - 오케스트레이터 실측: s1v_fields.py:256-257이 뷰별 gain 제약 여부(flags[i][1])와 seed.source를 이미 계산하고 l_classes에만 넘긴 뒤 버림. ViewS1v(s1v_values.py:379-)에 gain/source 칸 없음. -> (가') 기존 writer가 ViewS1v에 두 값을 기록, icm_config가 READS(재계산 금지). 계획 먼저.
- S-1: gain 제약 없는 회로 = 기본 포트 뷰 해석(계획 밖). S-2: 여기 넷이 입력 밖 -> view_required 새 갈래(계획 밖). S-3: D41:697 대 700·734 (F 성분 미선언 포트 구동 여부) 모순, O-61 P4 (b)(가) 관계. S-4: D41:817 (1) U-106 전 문언. S-5: 끝 상태 레일 자름 = 계획 밖, O-49 P2 대비 취지 다름 표시 필요.
- N-1 U-104 변화표 누락, N-2 계획 (7)(b) 문언 갱신, N-3 RB-1 소멸 표시, N-4 ⑤ code 이름, N-5 D42:230 사실 오류(sf_pushpull icm_margin_v 있음 :141), N-6 D40 relabel 표지 일관.
- 7건 판정: (1)(2)(3) 계획 밖, (4) 계획 밖이지만 정합, (5)(7) 계획 안, (6) 계획 근거 있음(모순 S-3).
