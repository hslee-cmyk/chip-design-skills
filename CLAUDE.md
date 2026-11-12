# chip-design-skills — Claude 지시

칩 설계 키트(skill·agent·hook·analog-gmid-design 엔진) 저장소. 지시는 성격별로 나뉘어 있다(Anthropic 가이드에 맞춰 2026-11-12 개정):
- 상시 원칙 `.claude/rules/`(실행 때 함께 로드): 임시 규칙 O-229, 엔진 A·B·C, 계획·결정 D, 운영 F
- 보고 절차(원칙 26): skill `report-bundle` — 질문은 ask_gate hook, 텍스트 보고는 의무 점검(`.ai/obligations.yaml` + ai-memory `hooks/ob_*.py`, setup.py로 등록)이 강제
- 진행 중 작업: `.ai/working/`(hook이 주입) · 최종 보고는 한글(전역 지침 PREF-LANG, 옛 원칙 27)

## 지금 최우선: 임시 규칙 O-229 (LA-1 구현 완료까지)
원칙 1·6(물리 정합)과 원칙 7(graph 단일 정본)은 완화하지 않는다. 세부(test 범위, card 뒤 필수만, 승인 위임과 그 한계 O-267)는
`.claude/rules/o229-la1-sprint.md` — 아래 원칙과 계획 문언보다 앞선다.

## 세션 시작 시 가장 먼저: 지켜야 할 원칙 (원칙 1–33 — 아래 파일들)
이 목록(원칙 1–33: `.claude/rules/` + skill `report-bundle`)은 모든 권고·계획·design·card·검증 브리핑·재판정·보고 **전에** 대조한다. agent 브리핑에도 해당 항목을 넣는다. 결정 원문·경위는 `wt/_drafts/user_decisions.md`(O-번호)와 auto-memory에 있다.

**원칙 26(보고 5묶음)**: 권고·결정 질문이 들어가는 모든 보고에 bkit 단계표 / 단계별 점검표 / 원래 취지와 다름 / 권고 실측 출처 / 권고 확인표 10항목을 담는다 — 칸 규칙·10항목 전문은 skill `report-bundle`(보고 전에 연다).

### 원칙 번호 색인 ("원칙 N" 인용은 해당 파일을 가리킨다)
- **엔진 A·B·C** (`.claude/rules/engine-principles.md`): 1 물리 정합이 먼저, 그다음 gm/ID 손계산 · 1a 새 문제는 gm/ID 원본의 접근법부터 · 2 오차 범위 규칙 · 3 DC/AC 분리 · 4 계산 틀은 질문에 맞춘다 · 5 θ 기저 · 6 물리 정합 최우선, 가장 일반적인 형태부터 · 7 graph 단일 정본 · 8 코드는 언제든 재작성 가능 · 9 만들면 배선 · 10 fail-closed · 11 상수 발명 금지 · 12 일반화 · 13 논문 값 그대로 인용 금지 · 14 회로 해석은 연결과 원문만으로 · 15 topology connectivity는 사용자만 수정 · 16 held-out 회로는 spec 조정에 쓰지 않는다
- **계획·결정 D** (`.claude/rules/decision-process.md`): 17 bkit PDCA · 18 작성자 ≠ 검증자 · 19 새 근본원칙은 사용자 승인 뒤 적용 · 20 사용자 결정도 재검토 대상 · 21 권고는 물리·회로이론 검증과 함께 · 22 권고 전 확인 · 23 열린 권고는 그 사이 결정·실측으로 갱신 · 24 원래 취지와 다른 것은 표지하고 따로 보고 · 25 계획서는 규칙·정의·게이트·완료 조건만
- **보고 E** (`.claude/skills/report-bundle`): 26 보고 5묶음
- **운영 F** (`.claude/rules/operations.md`): 28 git -C·&&·push 금지 · 29 파일 수정 방식(heredoc append 금지) · 30 측정 결과는 evidence 파일로 · 31 agent 재개 목록·worktree 정리 · 32 agent 모델 · 33 목표는 엔진
- **27** 최종 보고는 한글 → 전역 지침 PREF-LANG (2026-11-12 중복 제거)
