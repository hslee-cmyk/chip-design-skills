# 전체 Skill 일관성 점검 결과 (2026-02-06)

## 점검 대상: 5개 Skill

| Skill | SKILL.md | Reference 파일 수 | 불일치 발견 | 수정 완료 |
|-------|----------|-------------------|-------------|-----------|
| verilog-rtl | O | 6 | 7건 | O |
| chip-verification | O | 8 | 2건 | O |
| lattice-fpga | O | 5 | 2건 | O |
| uvm-verification | O | 4 | 0건 | - |
| verilog-a | O | 3 | 3건 | O |

## 주요 수정 내역

### verilog-rtl (첫 번째 세션)
- review-checklist.md: FSM 2-process 패턴 반영
- naming-examples.md: 네이밍 규칙 동기화
- cdc-patterns.md: CDC 패턴 정리
- fsm-patterns.md: 2-process FSM 일관성
- synthesis-check.md: 합성 체크 항목 동기화
- SKILL.md: Quick Reference 업데이트

### chip-verification
- interface-mapping.md: `tb_top` → `hdl_top` (듀얼탑 네이밍 일관성)
- interface-mapping.md: hvl_top 역할 주석 추가
- refmodel-patterns.md: "3-process FSM" → 중립적 표현 (verilog-rtl의 2-process 정책과 충돌 방지)

### lattice-fpga
- SKILL.md: iCE40 전력 수치 보정 (`~1mW` → `대기~75µW, 동작~1mW`)
- SKILL.md: 존재하지 않는 `assets/project-template/` 경로 제거

### uvm-verification
- 불일치 없음 (SKILL.md와 4개 reference 파일 완벽 동기화)

### verilog-a
- SKILL.md: comparator 초기화 코드 수정 (`state = 0` → 조건부 초기화)
- SKILL.md: Quick Reference에 규칙 2개 추가 (piecewise-linear→smooth, initial_step)
- coding-guideline.md: 체크리스트 2단계→3단계 구조로 변경

## 생성된 파일

5개 skill 모두 `references/consistency-map.md` 생성 완료:
- 각 skill의 핵심 원칙 → SKILL.md 섹션 + reference 파일 위치 매핑
- cross-skill 참조 포함 (skill 간 관련 원칙 연결)

## 점검 방법론

1. SKILL.md를 **source of truth**로 설정
2. 모든 reference 파일을 읽고 SKILL.md 대비 비교
3. 불일치 목록 작성 → 사용자 승인 → 수정 적용
4. consistency-map.md 생성 (향후 수정 시 참조용)

## 교훈

- cross-skill 충돌 주의: chip-verification이 "3-process FSM"을 언급했지만, verilog-rtl은 2-process를 정책으로 채택 → 중립적 표현으로 해결
- 존재하지 않는 경로 참조 주의: lattice-fpga의 `assets/project-template/` 실제 미존재
- 수치 정밀도: device-guide.md의 상세 수치와 SKILL.md 요약 수치 간 차이 발생 가능

---

## 2차 점검: 필수규칙 vs 상세내용 모순 점검 (2026-02-06)

### 점검 동기
- verilog-rtl SKILL.md 필수 규칙 테이블에 "순차/조합 로직 혼합 금지"가 있었으나, 하위 섹션 2에서 유연성 허용 → 모순

### verilog-rtl (4건 수정)
1. **필수 규칙 테이블 재구성** — Always블록분리/단일출력 제거, Blocking/단일할당 승격
2. **No Latches 문구** — "default 필수" → "기본값 할당 또는 if/case 완전성으로 방지"
3. **CDC Pulse Sync 위치** — Fast→Slow에서 Slow→Fast로 교정 (guide box, 섹션10, QR)
4. **reference 파일 동기화** — review-checklist, synthesis-check, consistency-map 업데이트

### verilog-a (1건, 3파일 수정)
- **Floating Node Prevention GOOD 예제**: `enable` 신호가 transition() 없이 직접 사용됨 → Rule 2 위반
- 수정: `I(in,out) <+ V(in,out) * transition(enable ? 1/Ron : 1/Roff, 0, Tr);`
- 반영 파일: SKILL.md, coding-guideline.md, convergence-issues.md

### chip-verification, lattice-fpga, uvm-verification
- 필수/권장 구분 없는 절차적 가이드 구조 → 해당 유형의 모순 불가능 → 모순 없음

---

## 3차: 참조 마커 시스템 도입 (2026-02-06)

- 5개 skill 모두 `[→§X]` 참조 마커 시스템 도입
- consistency-map.md에 마커 규약 섹션 추가
- 공통 검증 프롬프트 `skill-validation-prompt.md` 생성 (Check 1~5 정의)

---

## 4차: 5-Check 검증 시스템 완성 및 전체 검증 (2026-02-06)

### 검증 프롬프트 체계

| Skill | 개별 프롬프트 | Check 구조 |
|-------|-------------|-----------|
| verilog-rtl | `verilog-rtl/skill-validation-prompt.md` | 참조마커 → 요약vs상세 → 코드예제 → 용어 → map |
| verilog-a | `verilog-a/skill-validation-prompt.md` | 참조마커 → 요약vs상세 → 코드예제 → 용어 → map |
| chip-verification | `chip-verification/skill-validation-prompt.md` | 참조경로 → 워크플로우-참조 → 다이어그램/코드 → 용어 → map |
| lattice-fpga | `lattice-fpga/skill-validation-prompt.md` | 참조경로 → 워크플로우-참조 → 다이어그램/코드 → 용어 → map |
| uvm-verification | `uvm-verification/skill-validation-prompt.md` | 참조경로 → 워크플로우-참조 → 코드예제 → 용어 → map |

- 공통 프롬프트 `skill-validation-prompt.md`는 Check 정의 원본 + 적용 범위 테이블 역할

### 전체 검증 결과: 5/5 PASS (전 skill)

| Skill | 결과 | 개선 권고 반영 |
|-------|------|--------------|
| verilog-rtl | 5/5 PASS | INFO 2건 (r_busy 인라인 스니펫, 유니코드 화살표 미세 차이) — 현행 유지 |
| verilog-a | 5/5 PASS | §9 체크리스트에 PWL→smooth, 초기조건 항목 2개 추가 |
| chip-verification | 5/5 PASS | interface-mapping.md config_db set 위치 주석 명확화 |
| lattice-fpga | 5/5 PASS | 변경 사항 없음 |
| uvm-verification | 5/5 PASS | consistency-map "Phase 주의" → "핵심 Phase 순서 (주의 문구)" 명확화 |

### 수정 내역

1. **verilog-a SKILL.md §9**: 체크리스트 "작성 후 확인"에 2항목 추가
   - `- [ ] Piecewise-linear 대신 smooth 함수 (tanh, limexp) 사용했는가? [→§3]`
   - `- [ ] @(initial_step)에서 적절한 초기 조건을 제공했는가? [→§5]`
2. **chip-verification interface-mapping.md**: Step 3 코드 블록의 config_db 주석을 코드 내부 상단으로 이동, 간략화 예제임을 명시
3. **uvm-verification consistency-map.md**: "Phase 주의" → "핵심 Phase 순서 (주의 문구)"

---

## 5차: BSC 네이밍 postfix 설명 수정 (2026-02-06)

### verilog-rtl (1건 수정)
- **SKILL.md §4 BSC 네이밍 테이블**: `_a`/`_z` postfix 어원 설명 수정
  - 기존: `_a` = "Actual/Application", `_z` = "Zero-delay output"
  - 변경: `_a` = "primitive cell 관행: a,b,c=입력", `_z` = "primitive cell 관행: z=출력"
- **사유**: primitive cell(buffer 등)에서 입력을 a,b,c, 출력을 z로 명명하는 관행을 따른 것이며, Actual이나 Zero-delay와는 무관
- **검증**: 5/5 PASS. "Actual"/"Zero-delay" 용어가 전체 디렉토리에서 완전 제거 확인

---

## 6차: verilog-rtl, verilog-a 개별 검증 프롬프트 생성 (2026-02-06)

### 배경
- 3~4차에서 chip-verification, lattice-fpga, uvm-verification 개별 프롬프트는 생성 완료
- verilog-rtl, verilog-a는 공통 프롬프트만 참조하고 있었음 → 개별 프롬프트 부재

### 생성 파일
| Skill | 파일 | Check 구조 |
|-------|------|-----------|
| verilog-rtl | `verilog-rtl/skill-validation-prompt.md` | 참조마커 → 요약vs상세(4 Zone: 필수규칙/사이클/리뷰/QR) → 코드예제 → 용어(11개) → map(15원칙) |
| verilog-a | `verilog-a/skill-validation-prompt.md` | 참조마커 → 요약vs상세(3 Zone: 핵심원칙/체크리스트/QR) → 코드예제 → 용어(12개) → map(11원칙) |

### 결과
- 5개 skill 모두 개별 `skill-validation-prompt.md` 보유 완료 (전체 57개 파일)
- git commit: `76e37ff`
