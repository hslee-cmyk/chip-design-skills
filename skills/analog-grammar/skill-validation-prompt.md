# analog-grammar SKILL.md 일관성 검증 프롬프트

> **용도**: SKILL.md 또는 `references/DESIGN.md` 수정 후, 내부 모순을 사전 차단한다.
> **구조 특성**: 절차적 구조(6단계 파이프라인) + 코드 레지스트리(`@idiom` 데코레이터) —
> `analog-gmid-design`처럼 함수 선택 지도는 없다(스크립트가 4개뿐이라 필요 없음). 마커
> 규약: `[→DESIGN.md §X]`는 항상 `references/DESIGN.md`의 섹션 번호를 가리킨다
> (`references/consistency-map.md` "마커 규약" 참고).

---

## Check 1: 참조 마커 무결성

**대상**: `[→DESIGN.md §X]` 마커 전체 + 괄호 없는 인라인 `§X`(DESIGN.md 자기참조)

**절차**:
1. SKILL.md에서 `[→DESIGN.md §` 패턴을 모두 추출 — 가리키는 번호가 `references/
   DESIGN.md`에 실존하는 헤더(`## N.`)인지 확인.
2. `DESIGN.md` 내부의 괄호 없는 `§X`(예: "DESIGN.md §4 참고")가 자기 자신의 헤더에
   실존하는지 확인.
3. `references/consistency-map.md`가 인용하는 SKILL.md 섹션명(예: "절대 규칙 #1")과
   DESIGN.md 절 번호가 실제로 그 위치에 존재하는지 확인.

**PASS 조건**: 모든 마커가 실존하는 섹션을 가리킴
**FAIL 시**: 잘못된 마커 목록과 올바른 섹션 번호 제안을 출력

---

## Check 2: 코드-문서 대조

**대상**: SKILL.md + `references/DESIGN.md` 내 모든 함수명·idiom 이름·priority 값 언급

**절차**:
1. `grep -n "^def \|^class " assets/netclass.py assets/idioms.py assets/sfg.py
   assets/analyze.py`로 실제 함수 목록을 뽑아, 문서에 언급된 모든 함수명이 존재하는지 확인.
2. `grep -n "@idiom(" assets/idioms.py`로 실제 등록된 idiom 이름·priority를 뽑아,
   SKILL.md/DESIGN.md의 idiom 표(현재 11종)와 개수·priority가 정확히 일치하는지 확인 —
   idiom을 추가/삭제했는데 표를 안 고치면 이 Check가 잡아야 한다.
3. `assets/netclass.py`의 role 상수(`DIODE, CURR_SRC, CTRL_SRC, CASCODE, AMP,
   FOLLOWER, SWITCH, ACTIVE_LOAD`)가 DESIGN.md §3의 Stage 2 판정 순서 의사코드에
   나열된 것과 정확히 일치하는지(추가/누락 없는지) 확인.
4. `assets/examples/*.json`이 실제로 존재하고 `assets/run_example.sh`가 참조하는
   경로와 일치하는지 확인.

**PASS 조건**: 문서에 언급된 모든 함수명·idiom·role 상수가 실제 코드와 정확히 일치
**FAIL 시**: 존재하지 않는 이름, 개수 불일치, 누락된 idiom/role을 출력

---

## Check 3: 용어 일관성

**대상**: SKILL.md + `references/DESIGN.md`

**절차**:
1. 핵심 용어 표기 일관성:
   - `gate`/`source`/`drain` — 영문 소문자 유지(G/D/S는 dict 키로만 사용)
   - `current-mirror`/`전류거울` — 혼용 허용, 단 "gate**와 source** 둘 다 공유"라는
     판정 기준은 모든 언급에서 동일하게 서술되는지 확인(gate만 언급하는 문장이 있으면
     FAIL — `analog-gmid-design`이 겪은 것과 같은 종류의 오탐을 이 skill 문서 자체가
     재도입하는 것이므로 특히 엄격히 본다)
   - `role`/`idiom`/`net class` — 개념 구분을 흐리지 않고 일관되게 쓰는지
   - `ASSUMPTIONS` — 대문자 유지(코드 출력과 동일 표기)
2. **이 skill 고유 — "확정"과 "추정" 표현 검증**: Stage 6 관련 서술에서 코드가
   결정론적으로 낸 것(구조 시그니처)과 LLM이 해석한 것(문헌 명칭 등)을 섞어 쓰지
   않았는지 확인 — 섞이면 §1 "회상 vs 분석" 원칙 위반.

**PASS 조건**: 핵심 용어가 일관되게 사용되고, 확정/추정 구분이 모든 서술에서 유지됨
**FAIL 시**: 불일치 용어 쌍, 확정/추정 혼동 위치를 출력

---

## Check 4: consistency-map 정합성

**대상**: `references/consistency-map.md`

**절차**:
1. 맵에 기록된 모든 원칙의 "SKILL.md 섹션" 항목이 실제 SKILL.md에 존재하는지 확인.
2. 모든 "reference 반영 위치"(`DESIGN.md §X`)가 실제로 그 절에 존재하는지 확인.
3. Cross-Skill 참조 표의 두 항목(`circuit-topology-extraction`, `analog-gmid-design`)이
   가리키는 대상이 실제로 존재하거나(analog-gmid-design) 존재 예정으로 명시돼
   있는지(circuit-topology-extraction, 아직 미반입) 확인.
4. **역방향 확인**: SKILL.md에 존재하는 원칙이 맵에 누락되지 않았는지 확인.

**PASS 조건**: 맵의 모든 항목이 실제 파일 구조와 일치, 역방향 누락 없음
**FAIL 시**: 불일치 항목과 실제 위치를 출력; 역방향 누락 시 추가할 원칙 목록 제안

---

## Check 5: Best Practices 준수

**대상**: SKILL.md frontmatter + body 전체

**절차**:
1. **SKILL.md 크기**: `wc -w SKILL.md` ≤ 5,000 words(현재 기준 여유 충분, 원본이
   이미 이 저장소 다른 skill보다 짧음). body ≤ 500줄.
2. **Description 필드**: `[What it does] + [When to use it] + [Key capabilities]`
   구조, ≤ 1024자, `<`/`>` 금지, 다른 skill 직접 참조는 "Cross-Skill 참조" 섹션에만.
3. **Progressive Disclosure**: 파이프라인 상세·Fig.2/Fig.3 실증·L1 idiom 표 전체는
   `DESIGN.md`에만 있고 SKILL.md에 재서술되지 않았는지(15줄 이상 산문 설명 블록이
   SKILL.md에 중복돼 있으면 FAIL).
4. **폴더 구조**: skill 폴더 내 최상위 `README.md`가 없는지 확인(이 저장소 관례 —
   반입 시 원본 zip의 `README.md` 내용은 SKILL.md "워크플로"/"참조 파일" 절에
   흡수됐어야 한다).
5. **Composability**: `analog-gmid-design`/`circuit-topology-extraction` 영역을
   침범하는 지침이 없는지(이 skill은 순수 netlist 구조 분석만 다루고, gm/ID 사이징이나
   PDF 추출 절차를 직접 서술하지 않아야 한다).

**PASS 조건**: 5개 항목 모두 충족
**FAIL 시**: 위반 항목, 현재 상태, 권장 개선을 출력

---

## 실행 결과 보고 형식

```
=== analog-grammar SKILL.md 일관성 검증 결과 ===
대상: analog-grammar SKILL.md
일시: [날짜]

Check 1 (참조 마커): PASS / FAIL
Check 2 (코드-문서 대조): PASS / FAIL
Check 3 (용어 일관성): PASS / FAIL
Check 4 (consistency-map): PASS / FAIL
Check 5 (Best Practices): PASS / FAIL

총 결과: X/5 PASS
```

---

## 수정 후 재검증

검증에서 FAIL이 발견되면:
1. SKILL.md 또는 `references/DESIGN.md` 수정
2. 동일 검증을 재실행
3. 전체 PASS 확인 후 `references/consistency-map.md` 변경 이력에 기록
