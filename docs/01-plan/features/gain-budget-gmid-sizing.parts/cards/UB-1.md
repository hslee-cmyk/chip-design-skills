### N6.15 card UB-1 -- 블록 국소 모델 U9 하나로 통합(사용자 결정 O-38 (2), LA-1 선행)

**근거**: 사용자 결정 O-38(2026-10-19 "모두 대안", `_drafts/user_decisions.md` O-38 행) (2) "LA-Q4 블록 국소 모델 통합(U9 하나)을 LA-1 안이 아니라 LA-1 앞 별도 card로(NL-1과 함께), 값이 바뀌면 block_residual·ff_gm_ratio에 동작 변경 기준(O-34) -- LA-1 변화표 원인 귀속 분리". 원칙: 같은 개념은 정본 하나(NFR-2·DEC-83).

**사실**(base master `b2c72a01`, 2026-10-19 재확인 -- 착수 때 다시 잰다): LA-1 F-LA4 그대로 -- (i) GB4/U9 `E/metrics/block_gain_model.py:132` `block_gain_model_of`·`E/metrics/block_gain_rows.py:26` `row_gains`(LUT 행 축 모델, 블록 노드 중 교류접지·여기 넷 제외, 저항 끝만 달린 막다른 가지 제외) (ii) `E/metrics/block_model.py:98` `block_local_gain`(봉인 `ss` 값, `_helpers_nodal` 컨덕턴스 조립, netlist 인접·폐포·FF `exclude`/`extra`, 복합 블록 경로 기여·`zout_ohm`·`decomposed_only`), 공개 `E/metrics/__init__.py:69`, 엔진 소비자 `E/metrics/block_residual.py:24`·`E/metrics/ff_gm_ratio.py:24`(`ff_gm_ratio`는 `spice_unverifiable` 선언 -- `E/metrics/verified_by.py:47`). 두 구현의 스탬프 규칙(미지수 노드 집합·폐포·막다른 가지)이 같은지는 재지 않았다 -- card 0 UB-0이 잰다.

**범위**: (1) 스탬프 조립을 U9 모델 하나로 두고 `block_local_gain`은 그 모델을 봉인 `ss` 값(gm·gmb·gds)으로 평가하는 진입점으로 바꾼다(두 번째 컨덕턴스 조립 삭제) (2) 두 규칙이 다른 자리(UB-0 측정)는 물리 정의(ω → 0 KCL, 같은 미지수 노드 집합)로 정본 규칙 하나를 design에서 정한다 -- 블록 경계·FF 묶음 같은 회로 해석이 걸리면 공동분석으로 올린다 (3) NL-1(노달 극한 정본)과 같은 통합 병합으로 한다(파일 겹침 `_helpers_nodal`). (4) 예외 정리(v6.38.3 -- N6.35 E-01 감도 게이트 검사 불능 = 판정 불능, E-16 bin 내부 극값 미세분 = 상한 미상; 대체 규칙·옛 코드 삭제·완료 toy는 그 표가 정본, 동작 변경 변화표에 원인 'N6.35').

**card 0 UB-0**(검증자, 엔진 무변경): 13회로 봉인점마다 블록별로 두 구현의 gain·`zout_ohm`·경로 기여를 같은 동작점 값으로 재 차이와 원인(규칙 차이 자리)을 기록한다. 결과는 파일에 케이스마다 append.

**완료 조건**(O-34 (1) 동작 변경 -- `block_residual`·`ff_gm_ratio` 값이 바뀌는 경우): (1) 정의 손계산 오라클 toy -- 저항 부하 CS, 캐스코드, 차동쌍 + 미러, FF 합류 복합 블록에서 gain·Z_out·경로 기여가 손계산과 같음(허용오차 = 부동소수 풀이 잔차, 새 상수 없음) (2) 봉인 불변식 -- 이 card는 DC 상태를 바꾸지 않으므로 봉인 결과·S2 `dc` 필드는 순수 리팩터링 필드별 동일(NFR-4) (3) SPICE oracle 대조 -- 대상 값이 보고 전용 진단(`block_residual`)과 `spice_unverifiable` 선언 metric(`ff_gm_ratio`)뿐이라 이 다리는 '대상 없음'(DEC-90 (3) 선언 근거)으로 적는다 -- '보류'가 아니다. 단 착수 때 `git grep`으로 `block_residual`·`block_local_gain` 값을 **판정(제약 행·봉인·front 비지배)에 쓰는 소비자가 0**임을 확인해 판정 기록에 남긴다(소비자가 있으면 '대상 없음'이 성립하지 않으므로 멈추고 보고) (4) 검증자 변화표 -- UB-0 기록 대비 두 metric의 회로별 변화와 원인(원인 미설명 0) (5) 결정성 비트 동일 (6) `git grep` 두 번째 스탬프 조립 0, N6.3 공통 (7) N6.35 E-01 완료 toy(섭동 None → 판정 불능, 영향 집합 빈 경우 사유 기록 -- base red)·E-16 완료 toy(안쪽 극값 → 미상 또는 세분 값 -- base red).

**순서**: 착수 조건 = design 개정(S-7 -- design 41 §2 블록 국소 모델 정본 규칙: 미지수 노드 집합·폐포·막다른 가지·FF 묶음 처리를 하나로)과 card 0 UB-0(처리 = N6.1 측정 게이트 처리 표, 사용자 결정 O-225). NL-1과 같은 통합 병합, LA-1 앞(LA-1 선행 card 목록). 다른 card와 독립.

