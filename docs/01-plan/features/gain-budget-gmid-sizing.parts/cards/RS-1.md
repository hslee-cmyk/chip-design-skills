### N6.33 card RS-1 -- 소신호 파라미터 분해능 Δp(사용자 결정 2026-10-14 Q-N11 B)

**근거**: 사용자 결정 2026-10-14 "Q-N은 Q-N4만 제외하고 권고대로 해"(`_drafts/user_decisions.md` 2026-10-14 step-2 Q-N 항목) Q-N11 "B 먼저 후 C 판단"; 결정 자료 PKG §7.11. 계획 정본 = DEC-105 (8)·NFR-5(판정 단위).

**사실**(PKG §7.11, 엔진 `9255a22` 실측; 착수 때 다시 잰다): `E/metrics/ss_linearize.py`의 `lut_rel_tol` = `dc_op.gm_id · dc_tol_v`, `E/metrics/lut_parameters.py` Δp = ε_d·|p| 여섯 열 공통, metrics CONTRACT 9.1(ε_d)·9.3(최악 선형 결합); current_reuse 잡음 분해능 440 µV = 값의 61 %(파라미터 항 89 %, ε_d 중앙 0.169).

**범위**: Δp = |∂ln p/∂VGS|(그 점 LUT 기울기) · tol_V · |p|를 열마다(새 상수 0, 같은 LUT·같은 tol_V; **착수 조건**: card JC-1 뒤 열 목록에 cdb·csb가 있고 이 둘은 off 점 조회 열이라 그 소자 VGS에 의존하지 않는다 -- 그 기울기 꼴을 착수 때 정하고, 정하지 못하면 멈추고 보고(DEC-105 (8), N6.42 범위 4); 이 card가 과도기 꼴(N6.42 범위 4)을 대체한다 -- JC-1 완료 (10)은 Δp 꼴과 무관한 구조 단언이라 그대로 둔다), 결합 최악 선형 유지; metrics CONTRACT 9.1 개정(9.3 유지); 소비자 = 모든 ss metric의 `MetricResult.resolution`(NFR-5 판정 단위, DEC-71 (6) b_gain, LA-1 gain bin 폭). 새 필드·cache 0(분해능은 metric 결과의 기존 칸).

**완료 조건**(O-34 -- 값은 그대로, 분해능 정의가 바뀌는 기준 변경): (1) 단일 소자 toy -- Δgm = LUT 기울기 × tol_V 닫힌 식, 약반전 점에서 새 Δp < 옛 Δp (2) 13회로 metric별 분해능 표(옛/새)와 판정 분류(통과·실패·보류) 변화표, 원인 = '분해능 정의' (3) RSS 판단 입력 기록 -- 같은 점의 최악 선형 대 RSS 분해능(측정 기록, Q-N11 C 결정은 사용자) (4) N6.3 공통.

**순서**: 선행 = card LA-1 병합(b_gain writer와 gain bin 폭 소비자가 LA-1에서 생기므로 그 뒤에 분해능 정의를 바꿔야 두 card 변화표의 원인이 갈린다 -- 검증 1 D-10; LA-0 앞에 두면 LA-0 기준선과 LA-1 사이에 분해능 변화가 섞임). SPICE 다리 '대상 없음'(값 불변). CPG-1 앞. 착수 조건 = 계획 v6.38.2 승인 → design(S-7).

