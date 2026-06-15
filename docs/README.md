# Agent Building — 학습 노트 (docs)

에이전트 설계 권위 문서 2종을 **공부용으로 재구성**한 노트. 원문을 읽기 전 예습, 읽은 뒤 복습, 또는
핵심을 빠르게 다시 볼 때 사용한다. (원문 인용은 짧은 핵심 정의 위주, 나머지는 우리말 재서술.)

## 목차
1. [Anthropic — *Building Effective Agents*](01-anthropic-building-effective-agents.md)
   — workflow↔agent 구분, **start simple**, workflow 5패턴, **3원칙(Simplicity·Transparency·ACI)**, 도구 prompt-engineering.
2. [OpenAI — *A Practical Guide to Building Agents*](02-openai-practical-guide.md)
   — agent 정의/언제, **3 foundation(Model·Tools·Instructions)**, single→multi-agent orchestration, **layered guardrails**, human-in-the-loop.
3. [종합·비교·체크리스트](03-synthesis-and-checklist.md)
   — 두 문서가 같은 점/강조 다른 점, 통합 멘탈모델, 한 장 체크리스트.

## 원문 (Primary sources)
- **Anthropic**, *Building Effective Agents* (2024-12) — https://www.anthropic.com/engineering/building-effective-agents
- **OpenAI**, *A Practical Guide to Building Agents* (2025) — https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf

## 실무와의 연결
- `../agent-quality/AGENT_BEST_PRACTICES.md` — 이 두 문서를 **R1~R12 루브릭**으로 압축. `check_agents.py`로 자동 점검(매 커밋 게이트).
- `../agents/` — 그 원칙을 적용한 실제 Verilog RTL agent들(architect-advisor·coder·reviewer·prover).
- `../agent-kit/methodology.md` — 이 프로젝트가 두 문서의 원칙을 RTL 도메인에 적용한 방법론.

## 한 줄 요약 (두 문서 공통 정신)
> **단순하게 시작하라**(workflow/단일 LLM 호출로 충분하면 그걸로). **도구·지시·경계(interface)에 공을 들이고**,
> 에이전트의 **계획을 투명하게 드러내고**, **위험·반복실패엔 사람을 끼운다(guardrail + human-in-the-loop)**.

## 읽는 순서 제안
- 처음이면 **1 → 2 → 3**. (1은 *개념·패턴 분류*에 강하고, 2는 *실전 구성·운영*에 강하다 — 상보적.)
- 빠른 복습이면 **3**(종합) 한 장 → 필요한 패턴만 1/2에서 깊게.
