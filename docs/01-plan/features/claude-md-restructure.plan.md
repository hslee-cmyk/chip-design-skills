# CLAUDE.md 개정 — Anthropic 최신 가이드 정합 + 의무(obligation) 기반

- 상태: **승인 2026-11-12** (사용자 "승인할께. 진행해" — 원칙 27 삭제·원칙 26 skill 이전 포함) · 작성 2026-11-12 · 상위: ai-memory `plans/phase-09-auto-recall.md` 9.A·R7
- 목적: 지시가 긴 세션·압축 뒤에도 지켜지게 한다. CLAUDE.md는 **매 세션 필요한 사실만 짧게**, 절차는 skill, 반드시 일어나야
  하는 것은 hook(의무 점검)으로 나눈다. **원칙의 의미는 바꾸지 않는다**(문언 이동·압축만, 원칙 번호·O-·DEC- 보존).
- 이 계획은 원칙 7 단서("계획의 규칙·정의·결정 문언을 바꾸는 개정은 병합 전에 사용자에게 묻는다")의 대상이다.

## 1. 근거 — 공식 가이드(code.claude.com/docs, 2026-11-12 조회)
| 가이드 | 출처 |
|---|---|
| 파일당 200줄 미만 목표, "길수록 context를 쓰고 준수도가 떨어진다". 매 세션 필요한 사실만 | memory § Write effective instructions |
| 여러 단계 절차는 skill, 특정 경로용 지시는 `.claude/rules/*.md`(`paths:`) | memory § When to add to CLAUDE.md |
| 매번 반드시 일어나야 하는 것은 hook·deny rule — "CLAUDE.md is for guidelines" | best-practices, features-overview |
| 강조어를 쌓으면 과잉 적용, 평이한 한 줄로. 저장소에서 읽을 수 있는 구조 설명은 넣지 않는다 | best-practices anti-patterns |
| `.claude/rules/*.md`: `paths:` 없으면 실행 시 CLAUDE.md와 같은 우선순위로 로드, 있으면 해당 파일을 읽고 쓸 때 로드(압축 뒤엔 다시 필요할 때) | memory § Organize rules, context-window § What survives compaction |
| 압축 뒤 루트 CLAUDE.md·auto memory는 디스크에서 다시 주입 | context-window § What survives compaction |
| auto memory `MEMORY.md`는 앞 200줄 또는 25KB까지만 로드 | memory § Auto memory |
| 모순된 지시는 임의로 하나가 선택됨 — 주기적 정리(`/doctor prompt-audit`) | memory § Troubleshoot / Audit |

## 2. 실측 (2026-11-12)
| 파일 | 실측 | 문제 |
|---|---|---|
| `CLAUDE.md` | 71줄, **15,804B**, 최장 줄 1,057자, ★ 강조 | 줄 수만 기준 안. 문단을 한 줄에 넣어 실질 분량이 큼. 절차(원칙 26 보고 5묶음·확인 10항목)가 본문에 |
| Claude auto memory `MEMORY.md`(머신 로컬) | **26,463B > 25KB** | 끝부분 미로드(ask_gate·O-229·PDK 이식성 등 최근 항목). cloud0·다른 AI는 이 메모리를 아예 못 봄 |
| `.claude/hooks/ask_gate_rules.py` | 원칙 26을 **Windows 절대 경로**로 읽음 | cloud0에서 경로 불일치 |
| 메모리 `feedback_report_bkit_stage_compliance.md` 등 | 옛 8·9항목 서술 | 원칙 26(10항목)과 모순(clash) |

## 3. 새 구조 (의미 변경 0)
| 옛 위치 | 새 위치 | 로드 | 비고 |
|---|---|---|---|
| 머리 임시 규칙 O-229(1–7) | `CLAUDE.md` 맨 위(압축) + **의무 `o229-la1-sprint`(until: LA-1 병합)** | 항상 | 기한이 있는 규칙 → 의무 수명 관리(R7 a2) |
| A 1–6(1a 포함) 엔진 목적·계산 방식 | `.claude/rules/engine-principles.md` | 항상(`paths:` 없음) | 권고·계획에도 필요하므로 경로 한정하지 않음 |
| B 7–10 엔진 구조, C 11–16 값과 회로 | 같은 파일 | 항상 | |
| D 17–25 계획·결정 절차 | `.claude/rules/decision-process.md` | 항상 | 원칙 22(권고 전 확인)의 세부 절차는 skill로 |
| **E 26 보고 5묶음·확인 10항목** | **skill `.claude/skills/report-bundle/SKILL.md`**(절차 정본) + **의무 `report-bundle`**(트리거·필수 표지 = skill에서 파싱) + hook(질문 경로 ask_gate, 텍스트 보고 경로 Stop 점검) | 의무가 필요한 순간 주입·점검 | ask_gate 파서는 skill 파일을 읽도록 재배선(상대 경로) |
| E 27 최종 보고 한글 | 삭제 — 전역 지침 PREF-LANG과 중복(포인터 한 줄) | — | |
| F 28–33 운영·안전 | `.claude/rules/operations.md` | 항상 | 29(heredoc append 금지)는 append_guard hook이 이미 강제 — 그 사실을 적는다 |
| (신규) | `.ai/obligations.yaml` | hook이 읽음 | 의무: `report-bundle`, `o229-la1-sprint`, (이관안 확정분) |
- **새 `CLAUDE.md`**: 이 repo의 목적 한 줄, 지시가 어디 있는지(rules·skill·의무·hook), O-229 요지, **원칙 번호 색인**(번호·이름 한 줄씩 — 기존 문서의 "원칙 N" 인용이 계속 통하게). 목표 ≤ 80줄·≤ 6KB, ★ 없음.
- 문체: 평이한 문장, 원칙당 1–3줄. 경위·사례(O-170 등의 이력)는 이미 있는 history·결정 기록으로 포인터만.
- `.claude/rules/`·`.claude/skills/`는 git 추적(모든 PC·AI 공유). `settings.json`은 지금처럼 머신별.

## 4. 함께 하는 것
- **auto memory 정리안**(머신 로컬, 반영은 승인 뒤): 절차성 feedback 항목을 의무·rules로 옮기고 메모리엔 포인터만 → `MEMORY.md` < 25KB. 옛 8·9항목 서술 → 원칙(skill) 포인터.
- **검증**(원칙 18 작성자 ≠ 검증자): 독립 검증 agent가 옛 CLAUDE.md의 원칙 문장마다 새 위치를 찾아 **의미 동일/변경/누락**을 판정한 대조표 — Major 0이 병합 조건.
- **실측 확인**: `paths:` 없는 rules가 압축 뒤 다시 주입되는지(공식 문서는 루트 CLAUDE.md만 명시) → 실세션 `/compact` 1회 또는 `InstructionsLoaded` hook 기록으로 확인. 안 되면 해당 내용을 CLAUDE.md에 남긴다.
- ask_gate self-test(Windows·cloud0) 통과, append_guard 무변경.

## 5. 완료 조건
- 새 `CLAUDE.md` ≤ 80줄·≤ 6KB, ★ 0. rules·skill·obligations 추적.
- 독립 대조표 Major 0(의미 변경·누락 0), 원칙 번호 색인으로 기존 "원칙 N" 인용 해소.
- ask_gate가 skill에서 항목을 읽어 self-test 통과(Windows·cloud0).
- 압축 뒤 rules 재주입 확인(또는 대안 적용).
- auto memory 정리안 제출(반영은 승인 뒤).

## 6. 원래 취지와 다름
- 없음(의미 변경 0이 조건). 단 **원칙 27 삭제**는 전역 PREF-LANG과 같은 내용이라 중복 제거다 — 승인 필요 항목으로 표시.
- 원칙 26의 **정본 위치가 CLAUDE.md → skill로 바뀐다**(메모리 `reference_ask_gate_hook`의 "확인 항목을 늘리려면 CLAUDE.md 원칙 26을 고친다"도 skill로 바뀜).
