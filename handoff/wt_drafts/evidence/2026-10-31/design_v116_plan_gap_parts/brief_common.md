# 공통 브리핑 -- design v1.16.0 ↔ 계획 v6.38.5 gap 분석 (부분 작업)

역할: design↔계획 gap 분석자(작성자·design 검증자와 별개). **읽기만.** git은 `git -C <경로>` + `set -e`만, reset·checkout·stash·push 금지. 프로젝트 파일 수정 금지(결과 파일은 아래 scratchpad 경로에만 Write 도구로).

## 입력
- 계획 단어 단위 diff(이 agent 몫): 아래 개별 지시의 파일. 형식: `===== <tag> old a-b new c-d | <새 계획의 절 제목>` 다음에 `[replace/insert/delete] ctx«앞 문맥»`, `- 지운 말`, `+ 넣은 말`.
- 새 계획 전체(줄 번호 = diff의 new 줄): scratchpad `new_<계획이름>.md`, 옛 계획: `old_<계획이름>.md`
  (scratchpad = C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad)
- design v1.16.0 (worktree C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115, HEAD bc3b3572):
  - docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md
  - docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md
  - docs/02-design/features/gain-budget-gmid-sizing.42-gap-checklist.design.md
  - (참고) docs/02-design/features/ 아래 다른 design 문서(headroom-chain·graph-consumption·offset 등)가 있으면 그 계획 몫은 그 design 자리도 본다.
  파일이 매우 크다(줄이 길다). Grep(-n, 키워드·DEC/O/U/card 번호·필드 이름)으로 자리를 찾고 필요한 줄만 Read(offset/limit)한다.
- 사용자 결정 O-175~O-193 요약: scratchpad decisions.txt

## 할 일
1. diff의 각 변경을 **의미 단위 항목**으로 묶는다(판 번호·괄호 출처·줄 번호만 바뀐 것, 경위 문장, 정정 이력은 '계획서 정리'로 한 줄에 묶어 '해당 없음(근거)'으로 처리).
2. 항목마다 그 변경이 담은 규칙·정의·게이트·완료 조건·card 범위·착수 조건·병합 순서가 design 40/41/42에 **빠짐없이, 다르지 않게** 들어갔는지 grep·Read로 확인해 판정한다:
   - 일치: design 자리(파일 약칭 40/41/42 + 절 + 줄)에 같은 뜻이 있다.
   - 누락: design에 대응 자리가 없다(design 몫인데).
   - 다름: design 문언이 계획과 다르다(옛 문언이 남은 것 포함 -- 바뀐 결정의 옛 말(예: '가장 큰 VGS 해', 이름 tie-break, e_m·model_error, ME-1, PW-1b, HC-S → TB-1 순서, R-1′ 생산 card TB-1, held-out 4회로, 9회로 범위 등)이 design에 살아 있으면 다름).
   - design 몫 아님: 계획 운영·history·다른 문서 몫(근거 한 줄).
   판정마다 design 줄을 직접 확인한다(추측 금지). '일치'는 design 문언을 찾았을 때만.
3. 이 몫에 card 절(N6.x)이 있으면, 그 card의 범위·완료 조건·착수 조건 각각이 design에 대응 자리를 갖는지(card 착수 가능성) 표로.
4. design이 계획과 다르거나, 계획이 고쳐져야 할 곳(계획 안 자기모순·낡은 문언·design이 정한 것을 계획이 모름)을 따로 목록.
5. Major = 누락·다름 가운데 card 착수를 막거나 사용자 결정(O-번호)과 어긋나는 것.

## 원칙(판정에 쓴다)
- chip-design-skills/CLAUDE.md A~F, 특히: graph 단일 정본(필드마다 writer 하나, 새 cache·memo·sctx 슬롯·EvalResult 값 칸·사본 금지, 정본 자리가 없으면 멈추고 보고), 계획과 다르면 계획부터, 상수 발명 금지, 회로 이름·매직넘버 금지, DC/AC 분리, 원칙 2 오차 규칙(e_m 없음, oracle 닫기).
- **as-built 엔진 코드는 근거가 아니다(O-153·O-165).** 엔진 소스는 읽지 않아도 된다. 읽는다면 재작성 범위 확인 용도로만.
- 작성자 보고를 증거로 받지 않는다. design 문언 실측만.

## 결과
- scratchpad에 `gap_<몫이름>.md`를 Write로 쓴다(중간에 끊겨도 건지게 절마다 나눠 써도 된다). 형식:
  - 표 A: `# | 계획 자리(절·new 줄) | 변경 요지(짧게) | design 자리(40/41/42 §·줄) | 판정 | 메모(다름이면 무엇이)`
  - 표 B(card가 있으면): `card | 항목(범위 n·완료 n·착수) | design 자리 | 판정`
  - 목록 C: 계획 개정 필요(근거 줄)
  - 목록 D: Major 후보(근거 줄)
  - 끝에 집계: 항목 수, 일치/누락/다름/해당 없음 수.
- 최종 보고(SubagentHandback)는 한글로 짧게: 집계 + Major 후보 + 계획 개정 필요 + 결과 파일 경로.
