# offset-trim · offset-strategy 정합 감사 요약 (2026-10-20)

대상: master `9401e98f`의 offset-trim 계획(v0.5.4/0.5.5, 감사자 표기 v0.5.6)과 offset-strategy 계획(v0.6.2), 참고 design 두 편. 기준: 사용자 결정 O-23~O-53, gain-budget v6.20(`plan/gb-v620`), oracle-portability v0.6.10(`plan/oracle-v0610`). 감사 추출본: scratchpad `offset_audit/`. "OT" = offset-trim, "OS" = offset-strategy. 줄 번호는 master 판.

## 사용자 결정으로 닫힌 것 (O-53)
- A2 matching 합성 제약 판정 위치(OS 203·294·312행, OT 318·342·352행) → O-53 A2.
- A3 trim 균형 풀이 삭제(OT FR-T8 102행, N3.4 268·272행, N3.5 288-291행, TR-5 528행; design §10.5 602행·84행 newton 상한·810행 레지스트리 '고정 기하 DC 균형 풀이'·TR-5c 846행) → O-53 A3.
- B1 코드 상태별 의도적 꺼짐·triode 선언(OT N3.5 291행, design E-4 104행, N3.3-1 지문 결속, G-1 630행) → O-53 B1.
- B2 온도 점 전도 판정(OT N3.8.1·N3.8.2·N3.9) → O-53 B2.
- B3 output_reference·PC-10(OT design 730행, OS design 419행, oracle 'PC-10과 같은 기준인지' 미결) → O-53 B3.

## 원칙 기본안으로 고칠 것 (결정 불필요)
- A1 [차단] 계통 offset 정의·부호: OT N0.1 42행·N3.4 251행 `V_sys,s = output_error_v / A_dm`(offset_systematic.py:7-8)·크기 칸 offset_sys_mv·'균형 입력 = −V_sys,s', 보정 구간 중심 '≈ −V_sys,s'(268행); OS N3.3 203행 V_sys = offset_sys_mv(크기), 498행 offset_systematic → DEC-23 부호 있는 V_id* 한 칸 인용(V_id* = −ΔV_out/A_dc, ΔI_k = ID_k·ΔW_k/W_k, O-46·O-47·O-50 G1), 크기 칸·offset_systematic 인용 삭제, 보정 중심 부호 재작성.
- A4 [중간] σ_in·t 환산 이득: OT 41·45행 'A_dm = gain_ss_db의 T(0)' → DEC-23·N3.8 정의 인용(봉인점 DC 방정식 1차 감도, A_dc = 여기 방향 DC 극한 전달, 오라클 A = .tf), t = (z_p − z_n)/(2·A_dc) 같은 A_dc.
- A5 [중간] trim 범위 하한(OT N3.4 267행) |V_sys,s| → front 재판정 |V_id*|, 단위 9 뒤 실현 W 재판정(O-45 U3).
- B4 [높음] 오라클 입력 생산자 하나: TR-TL 구동기·TR-7 레인 P 확장 칸(코드 벡터·표본별 코드·온도) → EO-1 생산자 호출, 확장 칸은 G-18 + U-6 규칙(그 card 통합 병합에 EO-1 생산자 갱신 커밋).
- B5 [중간] TR-7·TR-TL 판정에 O-34 네 다리(정의 손계산 toy, 봉인 불변식, SPICE 대조, 검증자 변화표)와 모델 오차 규칙(DEC-72).
- C1 [높음] OS N3.6(241-251행)·완료 조건 2·9: 층 0 조립·수리·외층 자동 켬(O-41 규칙 분기)·비지배 재판정(O-37 (A))은 변형 단위.
- C2 [중간] OT G-12·OS 완료 조건 9 '문턱 의존 블록'에 층 0 조립 블록 포함, G-S2(iv_matching_l L 하한)와 LA-1 역산 조립 출발 규칙의 정본 관계.
- C3 [중간] OS-2 W-1 base 사슬(수작업 사슬 → find_front를 run_plan으로)과 LA-1(find_front 기본 경로 변경, O-49 P4 호출 자리)의 선후.
- D1 [높음] gain-budget N6.1(유일한 순서 정본)에 OS-2·OS-V·OS-5·OS-L·TR-1~TR-7·TR-TL 행 또는 다른 계획 card 인용 규칙(gain-budget 쪽 개정).
- D2 [높음] 동작 변경 card(OS-2, TR-2~TR-6)에 EO-1 완료 판정 선행(N6.20, N6.3 (iii)·(iv)).
- D3 [높음] OS-V(design 492행 verified_by offset_sys_mv → spice_oracle)와 gain-budget VB-1(N6.18) 범위 겹침 → OS-V는 합성 행 결속만, offset_sys_mv verified_by는 VB-1 선행 인용.
- D4 [중간] 오라클 선행을 OP-3·EO-1·OP-5(.tf A, .dc V_id*, 2단계 전도)로, OT N3.9 477행 '오라클 계획은 아직 초안' 낡은 사실 정정.
- E1 [중간] '비트 동일' 완료 조건 변경 종류 표시: OT 완료 조건 1·TL 'Δ_T 없는 실행 v0.5 전과 비트 동일', OS 완료 조건 1 = 순수 리팩터링(필드별); OS 완료 조건 2·9 = 결정성(비트 동일 유지).
- E2 [낮음] OT N3.2 극성별 headroom 창 근사에 '추정' 표기·DC 정의 인용(O-29 (2), O-31).
- E3 [낮음] 삭제 예정 모듈(offset_systematic) 근거 사실표(F-1·F-23 등)는 history로.
