# lattice-fpga SKILL.md 일관성 검증 프롬프트

> **용도**: SKILL.md 또는 reference 파일 수정 후, 내부 모순을 사전 차단한다.
> **구조 특성**: 절차적 워크플로우 가이드 — 규칙 중복 Zone 없음.

---

## Check 1: 참조 경로 무결성

**대상**: SKILL.md에 나열된 모든 참조 파일 경로

**절차**:
1. SKILL.md에서 `references/` 경로를 모두 추출
2. 각 경로가 파일시스템에 실존하는지 확인
3. 예상 파일 목록:
   - `references/device-guide.md`
   - `references/constraints-guide.md`
   - `references/reveal-debug.md`
   - `references/fpga-vs-asic.md`
   - `references/tcl-scripts.md`
   - `references/consistency-map.md`

**PASS 조건**: 모든 참조 경로가 실존
**FAIL 시**: 누락 파일 목록 출력

---

## Check 2: 워크플로우-참조 정합

**대상**: SKILL.md 워크플로우 6단계 + TIMING GATE

**절차**:
1. 워크플로우 각 단계의 내용이 reference 파일과 부합하는지:
   - `1. RTL 설계` → verilog-rtl skill (cross-skill 참조)
   - `2. Lattice 프로젝트 설정` → constraints-guide.md, device-guide.md
   - `3. 합성 & 구현 (Phase 1)` → device-guide.md (리소스), tcl-scripts.md (자동화)
   - `TIMING GATE` → tcl-scripts.md (Claude 실행 규칙, 타이밍 게이트 출력 형식)
   - `4. Bitmap 생성 (Phase 2)` → tcl-scripts.md (Phase 2)
   - `5. FPGA 검증` → reveal-debug.md
   - `6. Git Push → UVM 검증` → chip-verification skill (cross-skill 참조)
2. "Lattice 툴 선택" 테이블의 정보가 device-guide.md 각 디바이스 섹션과 일치하는지:
   - iCE40 UltraPlus → Radiant, .rdf, .pdc
   - MachXO2 → Diamond, .ldf, .lpf
   - LatticeXP2 → Diamond, .ldf, .lpf
3. "사용 환경" 코드 블록의 스펙이 device-guide.md와 일치하는지:
   - iCE40: 5.3K LUT, 1Mbit SPRAM, ~75µW
   - MachXO2: 최대 6.9K LUT, EBR
   - LatticeXP2: 최대 40K LUT, EBR + DSP

**PASS 조건**: 워크플로우/테이블이 reference 파일 내용과 부합
**FAIL 시**: 불일치 항목, SKILL.md 값, reference 실제 값을 나란히 출력

---

## Check 3: 다이어그램/코드 일관성

**대상**: SKILL.md 내 ASCII 다이어그램 및 코드 블록

**절차**:
1. "환경 구조" 디렉토리 트리의 구성 요소가 본문과 일치하는지:
   - `radiant_proj/` → Radiant 프로젝트 (.rdf)
   - `constraints/` → .pdc 파일 (constraints-guide.md 참조)
   - `ip/` → PLL, DDR 등 (device-guide.md IP 섹션과 대응)
   - `reveal/` → .rvl 파일 (reveal-debug.md 참조)
   - `scripts/` → build.tcl (tcl-scripts.md 참조)
2. 디렉토리 트리의 주석이 참조 파일 내용과 모순되지 않는지
3. "사용 환경" 코드 블록 3개 디바이스 정보가 "Lattice 툴 선택" 테이블과 일치하는지

**PASS 조건**: 다이어그램/코드 내용이 본문/참조와 모순 없음
**FAIL 시**: 불일치 요소와 위치를 출력

---

## Check 4: 용어 일관성

**대상**: SKILL.md + 5개 reference 파일

**절차**:
1. 핵심 용어 목록 교차 검증:
   - `Radiant` / `Diamond` — 대문자 일관
   - `.rdf` / `.ldf` — 프로젝트 파일 확장자
   - `.pdc` / `.lpf` — 제약 파일 확장자, Tool-Family 매핑 일관
   - `iCE40 UltraPlus` — 대소문자, 띄어쓰기 일관
   - `MachXO2` — 대소문자 일관
   - `LatticeXP2` — 대소문자 일관
   - `Reveal` — 대문자 표기 일관
   - `Bitstream` / `bitstream` — 일관
   - `Git submodule` — 표기 일관
   - `Implementation` / `impl` — 약어 일관
2. reference 파일 간 동일 디바이스 스펙에 다른 값 사용 탐지

**PASS 조건**: 핵심 용어가 일관되게 사용됨
**FAIL 시**: 불일치 용어 쌍과 파일 위치를 출력

---

## Check 5: consistency-map 정합성

**대상**: `references/consistency-map.md`

**절차**:
1. consistency-map의 모든 "SKILL.md 섹션" 항목이 실제 SKILL.md에 존재하는지 확인
2. consistency-map의 모든 "reference 반영 위치" 항목이 실제 reference 파일에 존재하는지 확인
3. Cross-Skill 참조가 대상 skill에 실존하는지:
   - `verilog-rtl` — RTL 설계
   - `chip-verification` — UVM 검증 (Linux)
4. SKILL.md에 있지만 consistency-map에 누락된 원칙이 없는지 확인

**PASS 조건**: 맵의 모든 항목이 실제 파일 구조와 일치
**FAIL 시**: 불일치 항목과 실제 위치를 출력

---

## Check 6: Best Practices 준수

**대상**: SKILL.md frontmatter + body 전체

**절차**:
1. **Body 줄 수 ≤ 500줄**: frontmatter(`---`...`---`) 이후의 body 줄 수 측정
2. **간결성 (No Standard Knowledge)**: Claude가 이미 알고 있는 표준 문법/패턴이 인라인 코드로 포함되지 않았는지 확인:
   - 표준 언어 문법 (기본 SystemVerilog/Verilog-A syntax)
   - 일반적으로 알려진 라이브러리 패턴 (UVM 기본 등록 코드 등)
   - 포인터로 대체 가능한 상세 코드 블록
3. **Progressive Disclosure**: 15줄 이상의 코드 블록이 인라인되지 않았는지 (긴 코드는 reference로 분리)
4. **Description 필드 정합**:
   - description에 `연관 skill:` 또는 다른 skill 직접 참조가 없는지 (→ body의 Cross-Skill 섹션에 배치)
   - description이 skill의 역할과 트리거를 기술하는지
5. **장식용 ASCII 최소화**: 순수 장식용 ASCII box (`━`, `┌┐└┘│├┤` 등)가 과도하지 않은지 (구조적 다이어그램/트리는 허용, 텍스트 테두리 장식은 markdown으로 대체)

**PASS 조건**: 5개 항목 모두 충족
**FAIL 시**: 위반 항목, 현재 상태, 권장 개선을 출력

---

## 실행 결과 보고 형식

```
=== lattice-fpga SKILL.md 일관성 검증 결과 ===
대상: lattice-fpga SKILL.md
일시: [날짜]

Check 1 (참조 경로): PASS / FAIL
  - [상세 내용]

Check 2 (워크플로우-참조): PASS / FAIL
  - [상세 내용]

Check 3 (다이어그램/코드): PASS / FAIL
  - [상세 내용]

Check 4 (용어 일관성): PASS / FAIL
  - [상세 내용]

Check 5 (consistency-map): PASS / FAIL
  - [상세 내용]

Check 6 (Best Practices): PASS / FAIL
  - [상세 내용]

총 결과: X/6 PASS
```

---

## 수정 후 재검증

검증에서 FAIL이 발견되면:
1. SKILL.md 또는 reference 파일 수정
2. 동일 검증을 재실행
3. 전체 PASS 확인 후 consistency-map.md 변경 이력에 기록
