# 종합·비교·체크리스트 (두 문서 합본 학습 노트)

> Anthropic *Building Effective Agents* [A] 와 OpenAI *A Practical Guide to Building Agents* [O] 를
> 한 장으로 합친 노트. 세부는 [01](01-anthropic-building-effective-agents.md)·[02](02-openai-practical-guide.md) 참조.

---

## 1. 두 문서가 **같은** 점 (핵심 공통 원칙)

1. **Start simple / 단일 agent 최대화 먼저.** [A] "simplest solution first" = [O] "maximize a single agent first, multi-agent only when needed".
2. **agentic ≠ 항상 agent.** 흐름을 미리 알면 workflow/결정론으로. [A] workflow 5패턴, [O] "deterministic solution may suffice".
3. **도구·인터페이스가 성능을 좌우.** [A] ACI(도구 prompt-engineering) = [O] "well-documented, tested, reusable tools" + 명확한 이름/파라미터.
4. **명확한 지시 + edge case.** [A] transparency·planning = [O] clear steps·actions·edge cases.
5. **stop 조건 + guardrail + 사람 개입.** [A] stopping conditions·guardrails = [O] failure thresholds·high-risk → human-in-the-loop.
6. **점진적으로 키워라.** 측정된 개선이 있을 때만 복잡도↑.

---

## 2. **강조가 다른** 점 (상보적)

| 측면 | Anthropic [A] | OpenAI [O] |
|------|---------------|------------|
| 강점 | **개념·패턴 분류** (workflow 5패턴, agent 정의) | **실전 구성·운영** (Model/Tools/Instructions, 배포·guardrail) |
| 패턴 어휘 | prompt chaining·routing·parallelization·orchestrator-workers·evaluator-optimizer | single-agent run-loop · multi-agent **manager** vs **decentralized(handoffs)** |
| 도구론 | **ACI prompt-engineering**(poka-yoke·생각할 토큰·자연 포맷·테스트) | **3타입**(data/action/orchestration)·재사용·"tool overload는 중복이 문제" |
| 모델 | (명시 적음) "right augmentation" | **명시적 절차**: baseline=최강모델 → 작은 모델로 cost 최적화 |
| guardrail | "guardrails + 샌드박스 테스트" (원칙) | **layered 타입 카탈로그**(relevance·safety·PII·moderation·tool-risk·rules·output) |
| 사람 | 체크포인트·human oversight | **트리거 명시**: failure threshold·high-risk/irreversible |

> 요령: **[A]로 "이게 workflow냐 agent냐, 어떤 패턴이냐"를 정하고, [O]로 "Model·Tools·Instructions·guardrail을 어떻게 실제 구성하냐"를 채운다.**

---

## 3. 통합 멘탈 모델 (의사결정 흐름)

```
                          ┌─ 흐름을 미리 알 수 있나?
작업 ──▶ 가장 단순한 해법?─┤   ├─ 예 → 단일 LLM 호출 / workflow 5패턴 [A]
                          │   └─ 아니오(open-ended) → AGENT
                          └─ [O] 3신호(복잡판단/유지난해룰/비정형데이터) 충족?
                                                              │
            AGENT 구성 [O 기초] ───────────────────────────────┘
              Model(baseline→최적화) · Tools(data/action/orch, 최소·명확 ACI [A]) · Instructions(단계·action·edge)
                          │
            오케스트레이션: single run-loop 먼저 → (complex-logic | tool-overload) 면 multi(manager|handoff)
                          │
            제어: stop 조건 + layered guardrail + human-in-the-loop(failure threshold·high-risk)
                          │
            운영: 샌드박스 테스트 → 실사용 검증 → 점진 확장 (transparency 유지)
```

---

## 4. 한 장 체크리스트 (실무 적용)

> 이 체크리스트의 **강제 가능 버전**이 `../agent-quality/AGENT_BEST_PRACTICES.md`(R1~R12) + `check_agents.py`다.

- [ ] **단순성**: workflow/단일 호출로 안 되나 확인했나? agent가 정말 필요한가? [A,O]
- [ ] **패턴**: (workflow면) 5패턴 중 어느 것? (multi-agent면) manager vs handoff, 분리가 정당한가? [A,O]
- [ ] **Model**: 작업 tier에 맞나? 더 싼 모델로 대체 가능한 부분은? [O]
- [ ] **Tools**: 최소·중복없음·명확(ACI), data/action/orchestration 분류, poka-yoke? [A,O]
- [ ] **Instructions**: 단계=구체 action, edge case 분기, "신입도 따라올" 명확성? [A,O]
- [ ] **Transparency**: 계획을 드러내고 명시적 output/report 형식이 있나? [A]
- [ ] **Stop**: 종료/최대반복/scope-exit 조건이 있나? [A,O]
- [ ] **Guardrails**: high-risk/비가역 행동이 rating·gate되나? hard 제약 명시? [O,A]
- [ ] **Human-in-the-loop**: failure threshold·high-risk → escalate 경로가 있나? [O,A]
- [ ] **Honest limits**: 못 하는 것을 정직히 적었나? [A]
- [ ] **Evals/test**: regression/answer-key로 검증 가능한가? 광범위 테스트했나? [A,O]

---

## 5. 용어 미니 사전
- **Workflow**: 흐름을 코드로 고정한 LLM 시스템. **Agent**: 흐름을 모델이 동적으로 결정.
- **Augmented LLM**: retrieval+tools+memory를 붙인 기본 단위.
- **ACI (Agent-Computer Interface)**: 모델이 쓰는 도구/인터페이스 — "사람용 UI만큼 공들여라".
- **Poka-yoke**: 실수 자체를 어렵게 만드는 설계(예: 절대경로 강제).
- **Orchestrator-workers / Manager pattern**: 중앙이 동적으로 분할·위임·합성.
- **Handoff (decentralized)**: agent가 다른 agent로 제어를 일방향 이전.
- **Tool risk rating**: 도구를 low/med/high로 평가해 high면 gate/escalate.
- **Anti-tautology**: 구현을 재진술하는 property로 자기 인증하지 않기(→ 이 repo `agent-kit/methodology.md`, prover §1b).

---

## 6. 이 프로젝트(`chip-design-skills`)에의 적용
- 두 문서의 원칙을 RTL 도메인에 적용한 것이 **Constrain-&-Escalate 4-agent 시스템**(`../agents/`) + 방법론(`../agent-kit/methodology.md`).
  - **Routing**[A] = bug-class router(클래스→가장 싼 검출기). **Orchestrator/escalate** = architect-advisor.
  - **ACI/도구**[A,O] = agent-kit 스크립트(boundary-classifier·harness_builder…)를 명확한 경계로.
  - **Honest limits·Transparency**[A] = 각 agent의 한계·보고 형식 섹션.
  - **Stop/guardrail/human**[A,O] = "ARCH면 escalate", "RTL 수정 금지", pre-merge gate.
- 그 준수를 **자동 점검**하는 게 `../agent-quality/`(R1~R14 + check_agents.py + pre-commit 훅).

---

## 7. 추가 교훈 — TB agent family 신설 세션(2026-07-22)에서 관찰

`verilog-tb-architect-advisor`/`verilog-tb-coder`/`verilog-tb-reviewer` 3개 agent를 한 세션에서
Plan→Design→Do→Check→Report까지 진행하며 반복 관찰된 것들. 강제 가능한 부분은 `R14`(§6, `AGENT_BEST_PRACTICES.md`)로 이미 편입했고, 여기는 **프로세스 차원**의 교훈만 남긴다.

| # | 교훈 | 근거(이 세션 실제 사례) | 어떻게 적용하나 |
|---|---|---|---|
| 1 | **"agent가 특정 flow에 종속되면 안 된다"는 실수는 한 번 고쳐도 다시 나온다.** 같은 세션 안에서 `verilog-tb-coder`(Plan 0.3→0.4)와 `verilog-tb-reviewer`(Plan 0.3→0.4)가 **독립적으로** 같은 결함을 반복했다 — 앞선 수정을 "알고 있었다"는 사실이 다음 agent 설계에 자동으로 전이되지 않았다. | 두 Plan 문서 모두 "호출자가 사람이든 workflow든 동일 절차"를 강조하면서도, 정작 §1.1/§4 절차 본문은 특정 호출자의 산출물(fix-plan.md)이 항상 있다고 가정하고 있었다 | 새 agent를 설계할 때 **스타일 일관성 감사(모델·frontmatter 등)와 별개로**, "이 절차가 특정 호출자 없이도 성립하는가"를 명시적으로 한 번 더 질문한다(`R14` 체크리스트). |
| 2 | **자동 검증 도구(`check_agents.py`)는 커밋 시점이 아니라 Design/Do 단계에서 먼저 돌려봐야 한다.** 이번 세션은 pre-commit 훅이 이미 있었는데도, 실제로는 사람이 Plan 문서를 다시 읽으며 "model 필드가 없다"를 수동으로 발견했다 — 자동화가 이미 있는데 늦게 활용한 셈. | `verilog-tb-reviewer.plan.md` 0.3의 "model: opus 누락" 발견은 `check_agents.py` 실행이 아니라 다른 9개 agent 파일과의 수동 대조로 나왔다 | agent 파일 초안을 쓴 직후 `python agent-quality/check_agents.py agents/<new>.md`를 **바로** 돌려 구조적 누락을 먼저 걷어내고, 그다음에 내용 판단(JUDGE)에 시간을 쓴다. |
| 3 | **cross-repo 계약(다른 repo가 정의한 스키마)은 그 repo의 실제 문서를 열어 대조해야지, "예전에 그렇게 정했다고 들었다"로 추정하면 안 된다.** verdict enum(`clean`/`issues_found`)이 정말 xcelium-mcp의 계약인지, 아니면 이 repo가 임의로 만든 편차인지는 `xcelium-mcp-debug-workflow-v2.plan.md`를 직접 열어 특정 줄(L637-639, L918)을 인용하고서야 확정됐다. | 사용자가 "rtl-reviewer/rtl-prover도 이 verdict를 지원해야 하지 않냐"고 물었을 때, 직접 소스를 다시 열어 대조하지 않았다면 잘못된 결론(3-way로 통일)을 냈을 수 있다 | cross-repo 주장은 반드시 절대경로로 실제 문서를 Read하고 **줄 번호를 인용**해 근거를 남긴다 — 이 근거를 agent 파일/Plan 문서에도 남겨야 나중에 "일관성 있게 고친다"며 되돌리는 실수를 막는다(교훈 #1과 동일한 방어 패턴). |

> 요약: **패밀리 일관성 감사(스타일)와 워크플로우 독립성 감사(절차)는 서로 다른 축이라 하나를 통과해도 다른 하나를 자동으로 통과하지 못한다** — 새 agent 설계 시 둘 다 별도로 체크한다.
