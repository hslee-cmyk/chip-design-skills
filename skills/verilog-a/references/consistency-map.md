# Consistency Map

## 사용법

SKILL.md 원칙 수정 시:
1. 아래 맵에서 해당 원칙의 반영 위치 확인
2. 모든 반영 위치를 함께 업데이트
3. SKILL.md 내부 요약 (체크리스트, Quick Reference)도 확인
4. **수정 후: `../skill-validation-prompt.md` 절차로 일관성 검증**

## 원칙별 반영 위치

| 원칙 | SKILL.md 섹션 | SKILL.md 내부 요약 | reference 반영 위치 |
|------|--------------|-------------------|-------------------|
| Continuous output only | 핵심 원칙 #1, §2 Signal Types | QR Key Rule #1, 체크리스트 작성후 | coding-guideline §3.2, convergence > 불연속 출력 |
| Discrete → transition() | 핵심 원칙 #2, §2 Golden Rule | QR Key Rule #2, 체크리스트 작성후 | coding-guideline §3.2/§5.1, convergence > 해결 |
| Feedback 연속성 (값+기울기) | 핵심 원칙 #3, §3 Feedback | QR Key Rule #3, 체크리스트 작성후 | coding-guideline §4.3, convergence > 피드백 |
| Floating node 방지 | 핵심 원칙 #4, §3 | QR Key Rule #4, 체크리스트 작성후 | coding-guideline §4.4, convergence > 해 없는 시스템 |
| 4-state logic (===) | §7 | QR Key Rule #5, 체크리스트 작성후 | coding-guideline §9 |
| cross/above 최소화 | §5 Events | QR Key Rule #6, 체크리스트 작성후 | coding-guideline §6 |
| transition delay=0, tr/tf 최대화 | §4 transition | QR Key Rule #7, 체크리스트 작성후 | coding-guideline §5.3 |
| Piecewise-linear → smooth 함수 | §3 Convergence | QR Key Rule #8, 체크리스트 작성후 | coding-guideline §4.2, convergence > PWL |
| 초기 조건 제공 (@initial_step) | - | QR Key Rule #9, 체크리스트 작성후 | convergence > 수렴 개선 #3 |
| 파라미터 범위 정의 | §1 Basic Syntax | 체크리스트 작성전 | coding-guideline §2.5 |
| 공통 회로 모델 | §8 Common Models | - | common-models > 전체 |

## Cross-Skill 참조

| 원칙 | 본 skill | 참조 skill |
|------|---------|-----------|
| AMS 모델 레벨 | §8 Common Models | chip-verification > analog-model-levels |
| Mixed-signal 인터페이스 | §5 Events | chip-verification > connect-modules |

## 마커 규약

- **형식**: `[→§X]` — X는 SKILL.md 내 섹션 번호
- **서브토픽**: `[→§X.Topic]` — 섹션 내 특정 주제 (예: `[→§1.CDC]`, `[→§1.Reset]`)
- **용도**: 요약 Zone의 항목이 어느 상세 섹션에서 유래했는지 추적
- **수정 시**: 상세 섹션 변경 → 마커가 가리키는 요약 항목도 반드시 동기화

## 변경 이력

- 2026-04-17 (7차): 6-Check FAIL 수정 — common-models.md vsource_pulse transition() 추가, nmos_simple PWL 의도적 예외 주석 추가
- 2026-02-09 (6차): SKILL.md 2단계 확장 패턴 적용 (413줄→230줄, -44%). §1 전체→포인터, §2 BAD예제→포인터, §3 코드→포인터, §4-5 코드→포인터, §8 Resistor/Capacitor→포인터, §9 체크리스트 압축, §10 QR 55줄→27줄. 중복체크 A1-A7 전 PASS
- 2026-02-09 (5차): Context 최적화 — §8 Analog MUX(-19줄), Comparator with Hysteresis(-24줄) 전체 코드를 reference 포인터로 교체 (common-models.md §5, §7). Resistor/Capacitor는 짧고 foundational이므로 유지. 450줄→~415줄
- 2026-02-06 (4차): Step 6 초기 검증 완료 (5/5 PASS). §9 체크리스트에 PWL→smooth·초기조건 항목 추가, consistency-map 동기화
- 2026-02-06 (3차): [→§X] 참조 마커 시스템 도입, skill-validation-prompt.md 연동
- 2026-02-06 (2차): 필수규칙 vs 상세내용 모순 점검 — Floating Node Prevention GOOD 예제에 transition() 누락 발견 → SKILL.md, coding-guideline.md, convergence-issues.md 3파일 동기화 수정
- 2026-02-06 (1차): 전체 점검 완료 (SKILL.md ↔ 3개 reference 파일 일관성 확보)
