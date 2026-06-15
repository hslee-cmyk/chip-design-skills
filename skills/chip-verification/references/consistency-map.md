# Consistency Map

## 사용법

SKILL.md 원칙 수정 시:
1. 아래 맵에서 해당 원칙의 반영 위치 확인
2. 모든 반영 위치를 함께 업데이트
3. cross-skill 참조 (verilog-rtl, uvm-verification)도 확인
4. **수정 후: `../skill-validation-prompt.md` 절차(6-Check)로 일관성 검증**

## 원칙별 반영 위치

| 원칙 | SKILL.md 섹션 | reference 반영 위치 |
|------|--------------|-------------------|
| 듀얼탑 구조 (hdl_top/hvl_top) | 듀얼탑 아키텍처 | interface-mapping > Step 3 |
| DUT→Interface→VIF 연결 | 워크플로우 #2 | interface-mapping > 전체 |
| Clocking Block 타이밍 (#1step/#1) | - | interface-mapping > Clocking Block |
| Ref Model 사이클 정확 | 워크플로우 #3 | refmodel-patterns > cycle_accurate |
| Ref Model FSM 대응 | - | refmodel-patterns > FSM Ref Model |
| Transaction vs Cycle Level | - | refmodel-patterns > 비교 |
| Scoreboard 비교 | 듀얼탑 다이어그램 | refmodel-patterns > Scoreboard 연결 |
| 디버그 5단계 플로우 | 워크플로우 #5 | debug-flow > 전체 |
| 회귀 테스트 3레벨 | 워크플로우 #6 | regression-strategy > 전체 |
| Coverage 기반 회귀 | - | regression-strategy > Coverage |
| 아날로그 모델 3단계 (Behav/Wreal/Spectre) | 아날로그 모델 교체 | analog-model-levels > 전체 |
| 모델 선택 Makefile | 아날로그 모델 교체 컴파일 옵션 | analog-model-levels > Makefile |
| Connect Module (D2A/A2D) | AMS 추가 단계 A2 | connect-modules > D↔E, D↔W |
| Connect Rules 자동 삽입 | - | connect-modules > Connect Rules |
| Wreal 모델링 | AMS 추가 단계 A3 | wreal-modeling > 전체 |
| Wreal UVM 연동 | - | wreal-modeling > UVM에서 Wreal |
| Spectre 연결 | AMS 추가 단계 A4 | spectre-integration > 전체 |
| AMS Control File | - | spectre-integration > 제어 파일 |

## Cross-Skill 참조

| 원칙 | 본 skill | 참조 skill |
|------|---------|-----------|
| RTL 설계 규칙 | 워크플로우 #1 | verilog-rtl |
| FSM 패턴 | refmodel-patterns | verilog-rtl > FSM |
| UVM 컴포넌트 | hvl_top 구조 | uvm-verification |

## 변경 이력

- 2026-04-17 (6차): 6-Check FAIL 수정 — description 직접 skill 참조 제거 (uvm-verification 언급 삭제)
- 2026-02-20 (5차): 6-Check 체계 전환 — "5-Check"→"6-Check" 표기 갱신, SKILL.md line 86 고립 코드 펜스 삭제
- 2026-02-06 (4차): 5-Check 검증 완료 (5/5 PASS). 개선 권고: interface-mapping.md config_db set 위치 코드-주석 혼동 가능
- 2026-02-06 (3차): [→§X] 참조 마커 시스템 도입, skill-validation-prompt.md 연동
- 2026-02-06 (2차): 필수규칙 vs 상세내용 모순 점검 — 절차적 가이드 구조로 해당 유형의 모순 없음 확인
- 2026-02-06 (1차): 전체 점검 완료 (SKILL.md ↔ 8개 reference 파일 일관성 확보)
