# analog-gmid-design SKILL.md 일관성 검증 프롬프트

> **용도**: SKILL.md 또는 reference 파일 수정 후, 내부 모순을 사전 차단한다.
> **구조 특성**: 절차적 구조(6단계 설계 절차 + Definition of Done 체크리스트) + **함수
> 선택 지도**(script 함수를 상황별로 매핑한 별도 reference, `function-selection-map.md`) —
> 다른 skill에 없는 이 skill 고유 구조. 마커 규약도 고유하다: `[→§X]`는 SKILL.md 자신이 아니라
> **항상 `gm-id-methodology.md`의 섹션 번호**를 가리킨다(`references/consistency-map.md`
> "마커 규약" 참고).

---

## Check 1: 참조 마커 무결성

**대상**: `[→§X]`/`[→references §X]` 마커 + 괄호 없는 인라인 `§X` 마커 전체

**절차**:
1. SKILL.md에서 `[→§` 패턴을 모두 추출 — **이 마커들은 예외 없이
   `references/gm-id-methodology.md`의 섹션 번호를 가리킨다.** 각 마커가 가리키는 번호가
   `gm-id-methodology.md`에 실존하는 헤더(`## N.`/`### N.M`)인지 확인.
2. 괄호 없는 인라인 `§X`(예: "§1.5", "(§8)", "stick-diagram-euler-layout.md §8.5")를 모두
   추출 — 파일명이 명시된 경우 그 파일에, 없으면 SKILL.md 자신의 섹션(§1, §1.5, §2, §2.1,
   §3, §4, §5, §6, §7)에 실존하는지 확인.
3. `references/function-selection-map.md`·`known-incidents.md`·`spice-verification-workflow.md`
   ·`consistency-map.md`가 가리키는 자기 자신의 §번호(예: function-selection-map.md 본문의
   "§1"~"§7")도 그 문서 안에 실존하는지 확인.

**PASS 조건**: 모든 마커가 실존하는 섹션을 가리킴(파일 self-reference 포함)
**FAIL 시**: 잘못된 마커 목록과 올바른 섹션 번호 제안을 출력

---

## Check 2: 요약 vs 상세 일치

**대상**: 3개 요약 Zone

**절차**:
1. 아래 Zone의 각 항목을 추출:
   - **핵심 원칙 절대 원칙 표**(SKILL.md 상단, 4행)
   - **§5 검증 체크리스트**(Definition of Done, 전체 항목)
   - **§1.5 규칙**(모든 소자 확정 원칙 — 표 #4의 1줄 요약과 §1.5 본문의 상세 절차)
2. 절대 원칙 표 4행 각각이 가리키는 `known-incidents.md`의 해당 "사고 N" 전문을 읽음
3. §5 체크리스트의 두 항목("폐루프 SPICE...", "LUT를 SPICE와...")이 가리키는
   `spice-verification-workflow.md` §1/§2 전문을 읽음
4. 요약 문구와 상세 내용이 **의미적으로 동일**한지 비교(허용: 축약/동의어, 불허: 반대 의미·
   누락된 조건·추가된 조건)

**PASS 조건**: 모든 요약 항목이 상세 내용과 의미 일치
**FAIL 시**: 불일치 항목, 요약 문구, 상세 문구를 나란히 출력

---

## Check 3: 코드 예제 및 함수 시그니처 준수

**대상**: SKILL.md + `function-selection-map.md` + `spice-verification-workflow.md` 내
모든 코드 블록·함수명 언급

**절차**:
1. `function-selection-map.md`에 등장하는 모든 함수 시그니처(예: `search_stack_finger_w(devices,
   target_row_fingers, ...)`)를 추출
2. 실제 코드에서 대조: `grep -n "^def " assets/sizing_recipe.py assets/stick_diagram.py
   assets/topology_library.py`로 전체 함수 목록을 뽑아, 문서의 모든 함수명이 실제로 존재하는지,
   인자 이름이 실제 시그니처와 일치하는지 확인(**이 skill의 원칙상 함수 로직을 재서술하지
   않으므로, 재서술된 pseudo-code가 섞여 들어오지 않았는지도 함께 확인**)
3. `spice-verification-workflow.md` §2의 ❌/✅ 코드 블록 — ❌ 예제가 실제로 §1.5/§5가 금지하는
   패턴(IDu와 SPICE 전류 직접 비교)인지, ✅ 예제가 올바른 절차(W=L·ID_target/IDu 경유)인지 확인
4. `report_template.html`에서 `renderSchematic()`/`renderStack()` 함수가 실제로 존재하고
   SKILL.md/design-report-spec.md가 그 이름을 정확히 인용하는지 확인

**PASS 조건**: 문서에 언급된 모든 함수명·시그니처가 실제 코드와 일치, ❌/✅ 예제가 의도대로 반대
**FAIL 시**: 존재하지 않는 함수명, 시그니처 불일치, 잘못된 예제를 출력

---

## Check 4: 용어 일관성

**대상**: SKILL.md + 전체 reference 파일

**절차**:
1. 핵심 용어 목록 교차 검증:
   - `gm/ID` — 표기 일관(gm/Id, gmid, GmID 등 변형 금지)
   - `moderate inversion` / `weak inversion` / `strong inversion` — 영문 표기 일관
   - `stack_id` / `finger_w` / `n_fingers` — 코드 변수명 그대로(스네이크케이스) 인용 일관
   - `box-shape` — 하이픈 표기 일관
   - `Euler trail` / `오일러 trail` — 한영 혼용이지만 "trail"은 항상 영문 유지
   - `current mirror` / `전류거울` — 혼용 허용, 단 판정 기준("게이트 net 공유")은 모든
     언급에서 동일하게 서술되는지 확인
   - `replica-bias` — 하이픈 표기 일관
   - `check_mirror_symmetry()` / `mirror-symmetry` / `matching-symmetry` — 함수명과
     개념명을 혼동하지 않고 구분해 쓰는지
2. **이 skill 고유 — "out of scope"/"범위 밖"/"범위 제외" 용어 검증**: 이 표현이 등장하는
   모든 위치를 추출해, §1.5 마지막 단락에 명시된 정당한 예외(ESD/guard-ring/foundry DRC/정확한
   메탈 스택 선택)에만 쓰였는지 확인 — 트랜지스터나 R/C 값 자체에 이 표현이 쓰였으면 FAIL
   (`references/consistency-map.md` "이 skill 고유 검증 항목" 참고).
3. reference 파일 간 동일 개념에 다른 용어 사용 탐지(전체 reference 목록은 SKILL.md "참조
   파일" 섹션).

**PASS 조건**: 핵심 용어가 일관되게 사용되고, "out of scope"류 표현이 정당한 예외에만 등장
**FAIL 시**: 불일치 용어 쌍, "out of scope" 오용 위치, 권장 통일 용어를 출력

---

## Check 5: consistency-map 정합성

**대상**: `references/consistency-map.md`

**절차**:
1. consistency-map에 기록된 22개 원칙(위 "원칙별 반영 위치" 표)의 모든 "SKILL.md 섹션" 항목이
   실제 SKILL.md에 존재하는지 확인
2. 모든 "reference 반영 위치" 항목이 실제 reference 파일에 존재하는지 확인(파일 경로 실존 +
   해당 내용이 실제로 그 위치에 있는지)
3. reference 파일 경로가 실제로 존재하는지 확인:
   - `references/function-selection-map.md`, `known-incidents.md`,
     `spice-verification-workflow.md`, `design-report-spec.md`, `gm-id-methodology.md`,
     `lut-generation-checklist.md`, `topology-fn-derivation-guide.md`,
     `topology-behavior-diagnosis-workflow.md`, `stick-diagram-euler-layout.md`,
     `sky130-worked-example.md`, `consistency-map.md`
   - `assets/report_template.html`, `sizing_recipe.py`, `topology_library.py`,
     `stick_diagram.py`, `sky130_lut_sweep.py`, `lut_v2_location.json`
4. Cross-Skill 참조(verilog-a, chip-verification)가 실제로 존재하는 skill인지 확인
5. **역방향 확인**: SKILL.md에 존재하는 원칙이 consistency-map에 누락되지 않았는지 확인
6. **이 skill 고유**: consistency-map의 "이 skill 고유 검증 항목"(out-of-scope 오용 탐지)이
   실제로 Check 4에서 실행됐는지 확인

**PASS 조건**: 맵의 모든 항목이 실제 파일 구조와 일치, 역방향 누락 없음
**FAIL 시**: 불일치 항목과 실제 위치를 출력; 역방향 누락 시 추가할 원칙 목록 제안

---

## Check 6: Best Practices 준수

**대상**: SKILL.md frontmatter + body 전체

**절차** (Anthropic "Complete Guide to Building Skills" 기준 보강):

1. **SKILL.md 크기 (Anthropic 공식 기준: 5,000 words 이하)**:
   - `wc -w SKILL.md`로 전체 단어 수 측정(현재 기준 약 1,370 단어 — 여유 충분)
   - 보조 지표: body 줄 수 ≤ 500줄(현재 약 357줄)
   - **초과 시 대응 절차**:
     1. 상세 예시·체크리스트 세부·긴 코드 블록 → `references/`로 분리하고 포인터만 유지
     2. 표준 지식 제거(Claude가 이미 아는 문법/패턴은 인라인 불필요)
     3. 분리 후에도 초과 시 → 섹션별 단어 수 측정하여 가장 큰 섹션부터 reference 추출
     4. 규칙 테이블·판단 기준·핵심 원칙 1줄 요약은 SKILL.md에 유지(분리 불가)
   - FAIL: 5,000 words 초과 + 분리 가능한 내용이 남아있음
2. **간결성**: 표준 문법/패턴이 인라인되지 않았는지
3. **Progressive Disclosure**: 1단계(frontmatter, 트리거)/2단계(SKILL.md body, 핵심 규칙)/
   3단계(references, 상세) 구조가 유지되는지 — 15줄 이상 코드 블록이 SKILL.md에 인라인돼
   있지 않은지(있다면 FAIL, `spice-verification-workflow.md`/`function-selection-map.md`로
   이동해야 함). 절대 원칙 4행은 SKILL.md 최상단에 유지되는지.
4. **Description 필드**:
   - `[What it does] + [When to use it] + [Key capabilities]` 구조
   - **description ≤ 1024자**(파이썬으로 실측: `description: |` 블록 전체 길이) — 현재
     약 1,017자, 재수정 시 반드시 재측정할 것
   - `<`, `>` 금지, 다른 skill 직접 참조 금지(Cross-Skill 섹션에만 배치)
5. **장식용 ASCII 최소화**: §1/§6의 플로우차트는 구조적 다이어그램이라 허용 — 이 외 순수
   장식용 box가 추가되지 않았는지
6. **압축 vs 명확성 균형**: reference 분리 가능(상세 예시·체크리스트 세부·긴 prose) vs
   SKILL.md 유지 필수(규칙 테이블·판단 기준·1줄 요약) 경계가 지켜지는지
7. **Composability**: 다른 skill(verilog-a, chip-verification) 영역을 침범하는 지침이 없는지
8. **폴더 구조**: skill 폴더 내 README.md가 없는지 확인

**PASS 조건**: 8개 항목 모두 충족
**FAIL 시**: 위반 항목, 현재 상태, 권장 개선을 출력

---

## 실행 결과 보고 형식

```
=== analog-gmid-design SKILL.md 일관성 검증 결과 ===
대상: analog-gmid-design SKILL.md
일시: [날짜]

Check 1 (참조 마커): PASS / FAIL
  - [상세 내용]

Check 2 (요약 vs 상세): PASS / FAIL
  - [상세 내용]

Check 3 (코드 예제/함수 시그니처): PASS / FAIL
  - [상세 내용]

Check 4 (용어 일관성 + out-of-scope 오용 탐지): PASS / FAIL
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
3. 전체 PASS 확인 후 `references/consistency-map.md` 변경 이력에 기록
