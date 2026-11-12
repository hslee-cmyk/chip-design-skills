# 지식 시스템 아키텍처 — 4계층 × 스코프·시간 축

> **2026-11-10 변경**: 전역 장기지식(구 `kb-global`)의 정본·툴링은 별도 repo **ai-memory**
> (`~/ai-memory`, env `AI_MEMORY_REPO`)로 이전했다 — 칩 키트 밖, 모든 PC·프로젝트·AI 공유.
> 인덱스는 `~/.ai-memory/`(env `AI_MEMORY_HOME`). bkit metric feature 이름 `kb-global`은 이력 연속성을 위해 유지.
>
> **2026-11-11 변경** (ai-memory Phase 7·8):
> - **구조화(Phase 7)**: 전역 지식에 경량 온톨로지(`ai-memory/ontology.yaml` + 정본 md의 `<!-- rel: … -->` 주석)를 둔다.
>   색인할 때 타입·관계를 검증해 노드·간선 그래프로 파생하고(오류 = 색인 실패 = push 차단), 검색은 벡터 + 키워드(FTS5) +
>   ID·별칭 주입 + 1단계 관계 확장으로 찾는다.
> - **단기기억 운용(Phase 8)**: 진행 중 작업 상태는 `<project>/.ai/working/`에 두고 Claude Code hook이 넣고 뺀다.
>   작업을 닫으면 `/wrap`이 교훈(장기기억 제안)과 경과(일화 `.ai/episodes/`, `episode_search`)로 나눈다.

> **한 줄 결론**: 프로젝트에서 풀어낸 지식을 *사라지지 않는 자산*으로 만든다. **스코프 축**으로는 프로젝트 관계는
> **graphify**, 전 프로젝트 공유 일반 원칙은 **전역 RAG(의미 + 선언된 지식 관계)**로 나누고, **시간 축**으로는
> 진행 중 상태(작업메모리) → 끝난 작업의 경과(일화) → 증류된 원칙(영구메모리)으로 흐른다.
> **정본은 git, 인덱스는 재생성**이다. 검색은 다국어 2단계(후보 수집 → reranker)이고, 품질은 eval로 재며
> ai-memory pre-push 게이트로 회귀를 차단한다.

이 문서는 `chip-design-skills` 키트가 fpga 워크스페이스 전체에 깔아둔 **지식 시스템**의 설계와 사용법을
설명한다. 새 프로젝트를 합류시키거나, 지식을 자산화·격상하거나, 검색 품질을 손볼 때 이 문서를 읽는다.

---

## 1. 왜 — 문제와 목표

일반 개발에서 "왜 이렇게 고쳤나"는 **사람 머릿속과 흘러간 대화** 속으로 사라진다. 같은 함정을 다른
사람·다른 프로젝트가 반복한다. 이 시스템의 목표는 **지식 자산화**다:

- 해결한 비자명 문제를 **검색 가능한 영속 자산**으로 기록한다.
- 일반화되는 원칙은 **모든 프로젝트가 자동 상속**한다(한 프로젝트의 교훈 → 전 프로젝트).
- AI 에이전트가 작업 착수 전 **과거 지식을 자동 회수**해 같은 실수를 막는다.
- 지식은 **버전관리·백업**되어 유실되지 않는다.

---

## 2. 한눈에 — 4계층 × 스코프·시간 축

```
            ┌─────────────────────── 4계층 ───────────────────────┐
 L1 기록    무슨 일이 있었나 (자동·원시)        bkit: audit/decisions/regression-rules/metrics
 L2 큐레이션 어떻게 풀었나 (사람·증류·정본)      docs/solutions(프로젝트) + ai-memory/memory(전역)
 L3 항법    무엇이 무엇과 연결되나 (관계 지도)    graphify  → <project>/graphify-out
 L4 검색    질문에 맞는 조각 회수                 영구메모리 RAG(+온톨로지 그래프) → ~/.ai-memory/kb.sqlite

            ┌────────────── 스코프 축 ──────────────┐
 프로젝트 = L3 graphify (코드·문서 관계, 자동 추출, 프로젝트 로컬, 재생성)
 전역     = L4 RAG     (의미 + 선언된 지식 관계, 전 프로젝트 공유, 증류만)

            ┌────────────── 시간 축 ──────────────┐
 진행 중   작업메모리 <project>/.ai/working/   hook이 주입·자동 기록, 끝나면 비움
   │ /wrap
   ├─ 경과  일화      <project>/.ai/episodes/  episode_search (기본 검색과 분리)
   └─ 교훈  docs/solutions → (격상) ai-memory/memory   memory_search
```

핵심 원칙 3가지:
1. **graphify와 RAG는 같은 정보를 색인하지 않는다** — graphify는 프로젝트의 **코드·문서 관계**(자동 추출),
   전역 RAG는 증류된 원칙의 **의미**와 사람이 선언한 **지식 노드 관계**(ontology, 색인 때 검증)다 (§4).
2. **정본은 git, 인덱스는 재생성** — 증류 지식은 절대 유실되지 않는다 (§5).
3. **산문은 RAG, 구조는 질의** — bkit 로그는 임베딩하지 말고 MCP로 질의한다 (§3.1).

---

## 3. 4계층 상세

### 3.1 L1 — 기록 (bkit, 자동·원시)
bkit 플러그인이 **자동으로** 남기는 append-only 기록. 사람이 손대지 않는다.
- `.bkit/audit/*.jsonl`(감사), `.bkit/decisions/*.jsonl`(결정 추적), `pdca-status.json`(상태),
  checkpoints, **`quality-metrics.json`**(품질 지표), **`regression-rules.json`**(카테고리별 누적 규칙).
- **지식 시스템 통합 이벤트** (§8.1 E·F):
  - `preflight.py` 실행 → `audit/*.jsonl`에 `gate_passed/quality` 기록 (actorId=preflight, mode=lean|rerank)
  - `/kb-promote` [A]/[B] 격상 → `audit/*.jsonl` + `decisions/*.jsonl`에 `quality_gate_result` 기록
  - `eval_gate.py` PASS → `quality-metrics.json`의 `kb-global` feature에 MRR/P@1 기록
- **접근법**: 임베딩 금지. `bkit_audit_search`/`bkit_metrics_get`/`bkit_regression_rules`/`bkit_gap_analysis` 등
  **MCP 도구로 정확 질의**한다. (방대·저신호라 RAG에 넣으면 노이즈·비용만 늘어남.)

### 3.2 L2 — 큐레이션 (사람·증류·**정본**)
사람이 확인해 증류한 재사용 지식. **두 스코프**로 나뉜다:
- **프로젝트 단기**: `<project>/docs/solutions/**` — 그 프로젝트에서 푼 버그 instance를
  실패분류 T1..T9 폴더에 기록(frontmatter + `schema.yaml` + `validate.py`).
- **전역 장기(증류)**: 별도 repo `ai-memory`의 `memory/<domain>/**`(실패분류 T1..T9 `memory/rtl/failure-taxonomy.md` 포함,
  2026-11-11 키트 `agent-kit/`에서 이전) — 여러 프로젝트에 일반화되는 원칙만.
- 도메인 지식: `<project>/.ai/analysis/`(모듈 분석), `<project>/.ai/knowledge/`(버그·툴 가이드).

### 3.3 L3 — 항법 (graphify, 프로젝트 로컬)
`graphifyy`(0.8.39, **tree-sitter-verilog AST**)가 프로젝트의 코드·설계·분석·ADR을 **관계 그래프**로
만든다. "무엇이 무엇과 연결/경로/중심 노드"를 본다. `<project>/graphify-out`에 산출(재생성 가능).
- 질의: `graphify query "<주제>"`, `graphify path A B`, `graphify explain X`.
- 갱신: `graphify update .`(코드) / `/graphify --update`(문서 의미추출, LLM).

### 3.4 L4 — 검색 (전역 RAG, 공유)
**증류 원칙만** 임베딩한 의미 검색. 모든 프로젝트가 하나의 전역 인덱스를 공유한다.
- 코퍼스: `ai-memory/memory/`(failure-taxonomy 포함). RTL agent가 읽는 `~/.claude/agent-kit/failure-taxonomy.md`는
  ai-memory `tools/render_global.py`가 쓰는 배포본(생성물)이다.
- 저장: `AI_MEMORY_HOME`(기본 `~/.ai-memory/`)`/kb.sqlite`(sqlite-vec, 재생성). 외부 전송 0 → RTL IP 보안.
- 파이프라인: 다국어 2단계(§7). 질의는 스코프 무관 → cross-project 재사용의 핵심.
- **온톨로지 그래프(Phase 7)**: `ai-memory/ontology.yaml`이 노드 타입(FailureClass·Signature·Route·Owner·Pattern·
  PropertyTemplate·Evidence·Rule·Preference·Episode …)·관계(`routes_to`·`proven_by`·`example_of`·`generalizes`·`about` …)·
  필수 규칙을 정한다. 정본 md의 ID 절(`## T4 · …`, `## P-… · …`)마다 `<!-- rel: … -->` 한 줄, 표의 열이 관계인 표
  (class route·구조 라벨·S/R)는 행을 그대로 읽는다. 색인이 검증해 노드·간선을 파생하고(관계는 한쪽에만 적고 역관계는
  자동), 검색 결과마다 `nodes`·`neighbors`를 붙인다. 타입은 데이터다 — 새 타입은 새 관계 규칙이 생길 때만(§12).

### 3.5 작업메모리·일화 — 시간 축 (Phase 8)
- **작업메모리** `<project>/.ai/working/ACTIVE.md` + `<slug>.md`(≤ 60줄, git 추적): 진행 중 작업의 체크리스트·시도·결정·
  다음 할 일. `ACTIVE.md`가 있는 프로젝트만 대상(opt-in). Claude Code hook(§8.1 G)이 세션 시작·압축 직후 주입하고,
  응답 끝에 자동 기록(무엇이 바뀌었나)을 남기며, 작업이 있었는데 본문이 그대로면 세션당 1회 갱신을 요구한다.
  → context를 비우거나 압축해도 정확한 상태 파일로 이어받는다.
- **일화** `<project>/.ai/episodes/<날짜>-<slug>.md`(`/wrap`이 씀, git 추적): 끝난 작업의 결정(사용자 원문)·실패와 원인·
  결과. ai-memory가 `Episode` 노드로 색인(머신 로컬)하고 `about` 관계로 의미론 노드와 잇는다. `memory_search`
  기본 결과에서는 빠지고 `episode_search`(최근성 가중)로 찾는다.

---

## 4. 스코프 축 — graphify ≠ RAG (왜 분리하나)

(시간 축 — 작업메모리·일화·영구메모리 — 은 §3.5. 아래는 프로젝트 ↔ 전역의 분리다.)

| | 프로젝트 지식 | 전역 일반 지식 |
|--|----------------|----------------|
| 인덱스 | **graphify**(코드·문서 관계, 자동 추출) | **전역 RAG**(의미 + 선언된 지식 관계) |
| 코퍼스 | 프로젝트 `.ai/analysis`·설계·`docs/solutions`(instance) | `ai-memory/memory` + taxonomy(증류만) |
| 잘하는 질의 | "X와 연결된 것/X→Y 경로/허브" | "이 질문과 의미적으로 가까운 조각" |
| 스코프 | **프로젝트 로컬**(관계는 프로젝트 내부에서 dense) | **전 프로젝트**(의미 유사도는 스코프 무관) |
| 수명·크기 | 프로젝트와 함께, 휘발/재생성, 작게 | 영속·누적, 증류만 → 작고 고신호 |

→ 관계는 *프로젝트 현상*이라 graphify를 프로젝트별로 둔다(여러 프로젝트 병합 시 community 희석·비대).
유사도는 스코프 무관이라 RAG는 전역 1개로 둔다. **프로젝트 로컬 RAG는 두지 않는다**(절제):
프로젝트 내부 탐색은 graphify, 일반 의미 검색은 전역 RAG.

---

## 5. 정본 vs 인덱스 — 영속성 모델

> 규칙: **재생성 불가능한 것(정본)만 git. 재생성 가능한 것(인덱스)은 비추적.**

| 정본 (git·원격 백업 → 유실 불가) | 인덱스 (비추적, 언제든 재생성) |
|----------------------------------|-------------------------------|
| `<project>/docs/solutions/**` (각 프로젝트 repo) | `<project>/graphify-out/` (L3) |
| `ai-memory/memory/**` (전역 원칙, 별도 repo) | `~/.ai-memory/kb.sqlite` (L4 인덱스) |
| (failure-taxonomy는 위 `ai-memory/memory/rtl/`) | `.tools/hf-cache/` (임베딩 모델 캐시) · `~/.claude/agent-kit/{failure-taxonomy,methodology,evidence,property-library}.md`(배포본) |
| `ai-memory/ontology.yaml` + 정본 md의 `<!-- rel: -->` 주석 | `kb.sqlite`의 `nodes`·`edges`·`fts_chunks`(그래프·키워드 색인) |
| `<project>/.ai/episodes/**` (일화, 각 프로젝트 repo) | `kb.sqlite`의 `kind=episode` 조각 |
| `<project>/.ai/working/**` (진행 중 상태 — git이지만 작업이 끝나면 비움) | `AI_MEMORY_HOME/sessions/*.json`(hook 세션 기록, 7일) |
| 툴링: `ai-memory/{tools,hooks}/*`, `ai-memory/requirements.txt`, 키트 `kb-venv-requirements.txt` | `.tools/kb-venv/` (공유 venv) |

핵심 설계(**단일 정본**): `kb_index.py`는 런타임에 principles 복사본을 만들지 않고
**git 정본을 직접 색인**한다(경로 해석은 `ai-memory/tools/am_paths.py` 한 곳). 따라서 정본/인덱스가
분기할 수 없고, 격상된 지식은 항상 git(원격)에 있어 유실되지 않는다. 그래프도 정본(md·yaml)에서 매번 파생한다.

⚠️ **격상은 정본에만 쓴다**: 일반 원칙은 `ai-memory/memory/<domain>/`(git)를 편집한다.
런타임 `~/.ai-memory/`는 인덱스 전용(재생성)이라 거기 쓰면 사라진다.

---

## 6. 데이터 흐름 — 자산화 → 격상 → 회수 (닫힌 루프)

```
[1] bkit가 자동 포착 (decision/audit/gap)        ← L1
        │ 사람 확인("그게 됐다")
        ▼
[2] docs/solutions/<T*>/...md 작성 (증류·frontmatter)   ← L2 프로젝트 단기
        │ sync_rules.py
        ▼   regression-rules.json 동기(bkit) + critical-patterns 승격 후보 리포트
[3] 일반화(3건+ 또는 명백한 원칙)
        │ ai-memory/memory/<domain>/ 편집(ID 절 + rel 주석, kb_index --check) + eval_gate + commit/push   ← L2 전역 정본
        ▼   kb_index.py 재색인(온톨로지 검증 → 그래프 파생)
[4] 전역 RAG 갱신 → 모든 프로젝트가 공유              ← L4
        ▲
        └─ 착수 전 preflight가 회수 (§7)                ← recall
```

이 루프가 "한 프로젝트의 교훈 → 전 프로젝트 일반지식"의 격상 경로다.

**작업 종료 갈래 (`/wrap`, Phase 8)** — 작업메모리에서 시작하는 같은 루프의 입구:
```
.ai/working/<slug>.md ──/wrap──┬─ 해결한 비자명 버그 → /solution-capture → [2]
                               ├─ 일반화되는 교훈   → /kb-promote [B](솔루션이 출처) 또는 memory_propose(inbox, 승인)
                               ├─ 일회성 경과       → .ai/episodes/<id>.md (Episode 노드, episode_search)
                               └─ 작업 파일·ACTIVE 줄 삭제(사용자 확인 뒤)
```

### 6.1 격상 탐지 자동화 — sync_rules.py [A]/[B]

`docs/solutions/sync_rules.py`는 격상 후보를 **두 경로**로 자동 탐지한다.

```
docs/solutions/<T*>/*.md
        │ sync_rules.py --dry-run
        ├──[A] 카테고리 fresh ≥ 2개 또는 severity=critical
        │       → critical-patterns.md (이 프로젝트 RTL 코딩 전 강제 회독)
        └──[B] problem_type=toolflow 또는 module=System (RTL 타입 아닌 것)
                → ai-memory/memory/ (전 프로젝트 전역 원칙)
```

**[B] 영구메모리(ai-memory) 경로** — 즉시 후보 (violationCount 무관):
- `toolflow` 타입 또는 System-level 솔루션은 환경·툴 수준으로 프로젝트 무관 → 생성 즉시 후보
- 추적: `ai-memory/memory/**/*.md` 프론트매터 `promoted_from:` 리스트로 중복 탐지

**[A] critical-patterns.md 경로** — 카테고리 반복 감지:
- `fresh` = contributed_from 미등록 **AND** kb_promoted_ids 미등록
  - `violationCount`는 bkit이 자동 증가하지 않아 영구 1로 고정 → 카테고리 파일 수로 대체
  - 이미 [B]로 격상된 ID는 [A] fresh 카운트에서 제외 (toolflow 등 중복 방지)
  - 격상 후 재탐지 방지: 기여된 ID를 `contributed_from:`에 등록
- 추적: `docs/solutions/patterns/critical-patterns.md` 프론트매터 `contributed_from:` 리스트

**격상 실행**: `/kb-promote` skill — 후보 탐지 → 내용 미리보기 + 사람 승인 → 패턴 합성/작성 → ID 등록 → **bkit audit/decisions 기록** → 커밋/push.

격상 직후(커밋 전) `sync_rules.py --record-promo`로 L1에 이벤트를 남긴다:
```bash
"$KB_PY" docs/solutions/sync_rules.py --record-promo \
  --type A|B --category <cat> --ids "<id1>,..." --target "<파일>" --reason <reason>
# → .bkit/audit/YYYY-MM-DD.jsonl (file_modified/quality)
# → .bkit/decisions/YYYY-MM-DD.jsonl (quality_gate_result)
```
`bkit_audit_search` MCP로 `actorId=kb-promote`를 필터링하면 언제 어떤 패턴이 격상됐는지 추적할 수 있다.

---

## 7. 검색 파이프라인 — 다국어 2단계

작업 착수 전 `preflight.py`가 **장기(전역 RAG) + 단기(프로젝트 graphify)** 를 한 번에 조회한다.
전역 RAG는 2단계:

```
질의 → [1] 후보 수집(pool = KB_RERANK_POOL, 기본 30, 크기 고정)
          벡터 top-60 ⊕ FTS5(trigram) BM25 top-60  → RRF 융합
          + 질의에 나온 ID·별칭의 노드 조각 주입
          + 상위 후보 노드의 1단계 이웃 조각(관계 확장)
      → [2] cross-encoder rerank (길이순 정렬 + 8개 묶음 — padding 낭비 방지)
      → 최종 top-k (기본 5), 결과마다 nodes·neighbors
```
- 일화(`kind=episode`)는 기본 제외. `episode_search`는 일화만 찾고 최근성 가중을 더한다.
- 실측 기여(Phase 7, 45질의): 벡터만 MRR 0.634 → +rerank 0.763 → **+FTS 0.881** → 주입·확장(관계 질의·neighbors 근거).
- bi-encoder: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (dim=384, 다국어).
- reranker: `jinaai/jina-reranker-v2-base-multilingual`.
- **둘 다 다국어** → 한/영 혼합 질의에서 순위 분리 개선. fastembed 내장(새 의존성 0).
- 토글/튜닝: `--no-rerank`, `--pool N`, env `KB_EMBED_MODEL`/`KB_RERANK_MODEL`. 모델 변경 시
  인덱스 자동 재빌드(혼합 벡터 방지). 모델 없으면 bi-encoder 순서로 폴백.

L3 graphify는 관계 항법이라 reranker 대상이 아니다(그래프 순회로 관련 모듈·과거 결정 추적).

### 7.1 preflight 배치 — GENERAL 우선 + 차이 명시 + graphify MCP 심층탐색
`preflight.py`는 두 계층을 **순서·라벨**로 분리해 제시한다:
1. **GENERAL** (전역 RAG, 일반 원칙) — **먼저·우선·정본 git**. "충돌 시 일반 원칙을 따른다" 명시.
2. **PROJECT** (graphify, 이 repo instance/관계) — 그 원칙의 *구체 적용/instance*.
끝에 **GENERAL vs PROJECT 차이 설명**(규칙 vs instance, 정본 위치, 격상 관계)을 붙여 사용자가
둘을 혼동하지 않게 한다. 프로젝트 wiki **심층 탐색**은 graphify MCP(`graphify.serve`,
`--install-mcp --project`로 `.mcp.json` 등록) — 에이전트가 query/shortest_path/explain/neighbors 사용.

**린 규칙 (plan 시간 보호)**: recall은 "방향 잡기"용이지 검증이 아니다. preflight는 **변경당 1회**(construct마다 N회 금지 — 호출마다 reranker 재로드), plan-time 기본은 **bi-encoder**(빠름, reranker 1.1GB 미로드); top 결과 모호할 때만 `--rerank`. 무거운 검증(formal/sim)은 절대 plan/recall에 끼우지 않고 taxonomy **Routing 절(정본)**의 owner로 넘긴다(architect는 *route*만, *run* 안 함).

---

## 8. 품질 보증 — eval + pre-push 게이트 (ai-memory)

검색 품질을 "느낌"이 아니라 **숫자**로 관리한다.

- **eval 하니스**: `ai-memory/tools/kb_eval.py` + 골드셋 `ai-memory/eval/queries.json`(한/영 47질의).
  정답 = **그래프 라벨**(질의의 정답 노드 + `ontology.yaml`의 `answer_equivalent` 관계로 1단계 이어진 노드 — 관계마다
  한 번 정하고 질의별로 넓히지 않는다). 기존 부분일치 라벨은 회귀 비교용으로 함께 출력.
  설정별(벡터만 → +rerank → +FTS → +주입 → +확장) **MRR/P@1/hit@k** 비교. 운영 실측(2026-11-11): 그래프 라벨 MRR 0.989·P@1 0.979.
  ```bash
  "$KB_PY" ~/ai-memory/tools/kb_eval.py --verbose
  ```
- **pre-push 게이트**: ai-memory `.githooks/pre-push` → `tools/eval_gate.py --gate`(`memory/`·`eval/`·`sources.yaml`·`ontology.yaml`·`tools/kb_*` 변경 push 시).
  키트의 옛 `.githooks/pre-push`(kb-global·taxonomy 트리거)는 정본 이전으로 대상이 없어져 2026-11-11 삭제. 게이트 동작:
  인덱스 최신화(온톨로지 검증 실패면 즉시 **차단**) → eval → `MRR/P@1 < 임계`(기본 0.9)면 **push 차단**. 전 프로젝트 공유 지식의
  품질 회귀를 push 직전에 막는다. 인프라 문제는 SKIP(`KB_EVAL_STRICT=1`이면 차단). 우회: `--no-verify`.
  **캐싱**: full eval이 ~7분 걸리므로 `eval_gate.py`는 SHA-256 콘텐츠 해시 기반
  캐시(기본 TTL 8시간, `KB_EVAL_CACHE_TTL_H` env)를 사용한다. 캐시 키 = 의미론 코퍼스 + `ontology.yaml` + 골드셋 +
  검색 코드(`tools/kb_*.py`)이고, 일화는 넣지 않는다(다른 repo의 일화가 ai-memory push를 막지 않게). 키가 바뀌지 않으면
  캐시 히트 → 0.2초 내 통과. 내용 변경 시 push 전 `eval_gate.py`를 수동 실행(pre-warm)해
  캐시를 채워두면 hook이 즉시 통과한다. PASS 결과만 캐시(FAIL은 재push 때 항상 재평가).
  **bkit quality-metrics 통합**: eval_gate PASS 시 ai-memory `sources.yaml` `bkit_workspaces`의 모든 프로젝트
  `.bkit/state/quality-metrics.json`에 `kb-global` feature로 MRR/P@1/질의 수를 기록한다.
  `bkit_metrics_get` MCP로 RAG 품질 이력 조회 가능(feature=`kb-global`, metrics: `kb_search_mrr`/`kb_search_p1`/`kb_eval_n_queries`).
  ⚠️ 코퍼스가 커지면 골드셋을 함께 키우고 재측정(pool/모델 재튜닝).

### 8.1 자동화 (hooks) — "배관은 자동, 판단은 넛지"

자산화 루프의 *배관*은 hook으로 결정론적 자동화, *판단*(무엇을 자산화·근본원인)은 적시 환기만 한다.

| 단계 | 메커니즘 | 동작 |
|------|----------|------|
| **A. validate+sync** | 프로젝트 `.git/hooks/pre-commit` | `docs/solutions/*.md` 커밋 시 `validate.py`(불량이면 **차단**) + `sync_rules.py`(regression-rules 재생성·stage) |
| **B. graph 갱신** | 프로젝트 `.git/hooks/post-commit` | `.v/.sv` 커밋 + `graphify-out` 존재 시 `graphify update` 백그라운드(코드 전용·비차단) |
| **C. 품질 게이트** | ai-memory `.githooks/pre-push` → `eval_gate.py --gate` | 영구메모리(taxonomy 포함) push 시 eval 게이트. PASS 시 `.bkit/state/quality-metrics.json`에 MRR/P@1 기록 |
| **D. 자동 회상** | CC hook `ai-memory/hooks/rc_*.py`(`setup.py` ⑤b, 전역) — ai-memory Phase 9 계획 v2 | **AI가 판단, hook은 힌트만.** `UserPromptSubmit`: 승인류가 아니면 '회상 단계' 한 줄(관련되면 맥락으로 질의를 써서 `memory_search`/`episode_search`) + 참고 후보 ID, 입력에 ID·별칭이 그대로 있으면 그 노드의 제목 힌트(본문은 `memory_read`). `PreToolUse Edit\|Write\|MultiEdit`: 편집 경로 → 영역 점검표(RTL T1–T9·`.sby` TPL·hook·지시 파일·auto memory), 영역별 세션 1회(옛 `kb-preflight-nudge` 대체). `PostToolUse Bash\|PowerShell`: 셸 명령 뒤 실제로 바뀐 파일이 규칙에 맞으면 같은 점검표. `PostToolUseFailure`: 오류의 ID·별칭 → 제목 힌트, 없으면 회상 단계 줄(세션당 3회). 예산 600자/4,000자, `[mem:ID]` 인용, `recall_report`로 사용률 측정 |
| **E. preflight audit** | `preflight.py` 자체 | 실행 시 `.bkit/audit/YYYY-MM-DD.jsonl`에 `gate_passed/quality` 기록 (actorId=preflight, mode=lean\|rerank). RTL 착수 전 지식 조회 증적 |
| **F. 격상 audit** | `/kb-promote` Step 5 (`sync_rules.py --record-promo`) | [A]/[B] 격상 시 `audit/*.jsonl` + `decisions/*.jsonl`에 기록 (actorId=kb-promote, decisionType=quality_gate_result) |
| capture 넛지 | `/solution-capture` skill 트리거 | "그게 됐다"류 감지 → 자산화(모델 판단) |
| **G. 작업메모리** | CC hook `ai-memory/hooks/wm_*.py`(`setup.py` ⑤b가 `~/.claude/settings.json`에 병합, 기존 hook 보존) | `.ai/working/ACTIVE.md`가 있는 프로젝트만. **SessionStart**: startup·clear = ACTIVE + `다음 할 일`, compact·resume = 진행 중 작업 파일 전문(≤ 8,000자). **PreCompact**: 요약 지시("상태 정본은 작업 파일") + 자동 기록, 압축은 막지 않음. **Stop**: 자동 기록 한 줄(B) + git 변경이 있었는데 본문 미갱신이면 세션당 1회 갱신 요구(A). 도구 실행 상태(`.bkit` 등)는 변경 감지에서 제외 |
| **H. 작업 종료** | `/wrap` skill(키트) + `ai-memory/tools/wm_wrap.py gather·check·close` | 교훈 → solution-capture·kb-promote·memory_propose(제안), 경과 → 일화, 작업 파일 정리(사용자 확인 뒤) |
| **I. 의무(obligation)** | CC hook `ai-memory/hooks/ob_*.py` + `<proj>/.ai/obligations.yaml`(git) | 프로젝트에서 반복해야 하는 절차·출력 항목. 트리거 입력이면 필수 항목 주입, 압축 직후 재주입. Stop: AI가 의도 표지(`## 결정 요청`)를 단 응답은 필수 표지가 빠지면 1회 차단, 표지 없이 보조 정규식만 걸린 응답은 1회 되묻기(결정 요청이면 표지·항목, 아니면 그대로). 필수 항목은 정본 문서에서 파싱(사본 없음), 수명(`until`)이 끝나면 은퇴. 준수율은 `recall_report` |

배포: `python install.py --install-git-hooks --project <repo>`(A·B) · D·G·I는 `ai-memory/tools/setup.py --only-claude-hooks`(전역, 멱등).
`.git/hooks`는 클론마다 재실행 필요. 완전 무인 자산화는 *판단*이 LLM 몫이라 불가하며, 그게 의도다(노이즈 방지).

---

## 9. 구성요소 지도

| 위치 | 무엇 | git |
|------|------|:--:|
| `ai-memory/memory/**/*.md` (별도 repo) | 전역 증류 원칙(정본) | ✅ |
| `ai-memory/memory/rtl/failure-taxonomy.md` (별도 repo) | 실패분류 T1..T9(정본). 배포본 `~/.claude/agent-kit/failure-taxonomy.md` | ✅ |
| `ai-memory/tools/{am_paths,kb_index,kb_search}.py` | 경로 해석·인덱서·2단계 검색 | ✅ |
| `ai-memory/ontology.yaml` + `tools/kb_graph.py` | 노드 타입·관계·필수 규칙, 그래프 파생·검증(`kb_index.py --check`) | ✅ |
| `ai-memory/hooks/wm_*.py` + `tools/wm_wrap.py` | 작업메모리 hook(주입·요약 지시·자동 기록·갱신 요구), `/wrap` 보조 | ✅ |
| 키트 `skills/{solution-capture,kb-promote,wrap}` | 자산화·격상·작업 종료 skill (`install.py`가 설치) | ✅ |
| `<project>/.ai/working/`, `<project>/.ai/episodes/` | 작업메모리(진행 중), 일화(끝난 작업 경과) | ✅ |
| `ai-memory/tools/kb_eval.py` + `eval/queries.json` | 품질 eval + 골드셋 | ✅ |
| `ai-memory/tools/eval_gate.py` + ai-memory `.githooks/pre-push` | 회귀 차단 게이트 | ✅ |
| `ai-memory/requirements.txt` + 키트 `kb-venv-requirements.txt` | 공유 venv 핀(RAG / graphify) | ✅ |
| `project-template/{ai/rag/preflight.py, docs/solutions/**}` | 프로젝트 스캐폴드 | ✅ |
| `<workspace>/.tools/kb-venv` · `hf-cache`, `~/.ai-memory/kb.sqlite` | 공유 venv·모델·인덱스 | ❌ 재생성 |
| `<project>/graphify-out` | 프로젝트 관계 그래프 | ❌ 재생성 |

영구메모리는 별도 repo다. `install.py --only ai-memory`는 없으면 `~/ai-memory`로 clone만 한다(배포 사본 없음).

---

## 10. 사용법 (Quickstart)

`KB_PY` = 공유 venv python (`<workspace>/.tools/kb-venv/Scripts/python.exe`).

**(0) 설치** — 새 PC는 `python ~/ai-memory/tools/setup.py` 한 번(venv·git hook·색인·전역 지침 렌더·MCP·작업메모리 hook,
glibc < 2.28 Linux는 conda 모드 자동). 이 워크스페이스처럼 공유 venv를 따로 쓰는 경우:
```bash
cd <workspace>
python -m venv .tools/kb-venv
python chip-design-skills/install.py --only ai-memory   # ~/ai-memory clone (없을 때만)
.tools/kb-venv/Scripts/python.exe -m pip install --only-binary=:all: \
    -r ~/ai-memory/requirements.txt -r chip-design-skills/kb-venv-requirements.txt
"$KB_PY" ~/ai-memory/tools/kb_index.py                   # 영구메모리 RAG 색인 (~/.ai-memory/)
```

**(1) 새 프로젝트 합류 — 한 방 온보딩**
```bash
python chip-design-skills/install.py --onboard --project <repo>
# = init-ai-infra(.ai/rag/preflight + docs/solutions + CLAUDE.md 의무, 기존 보존)
#   + git-hooks A·B(pre-commit 검증·동기, post-commit graphify)
#   + CC hooks D(RTL 편집 preflight 넛지)
# 선택: RTL 에이전트 `--only agents --project <repo>`, 그래프 1회 `/graphify .`
```

**(2) 작업 착수 전 — 지식 회수**
```bash
"$KB_PY" <repo>/.ai/rag/preflight.py "<증상/주제>"   # 장기 원칙(전역 RAG) + 단기 관계(graphify)
```

**(3) 문제 해결 후 — 자산화**
```
/solution-capture        # 대화 내역에서 발췌 → docs/solutions/<T*> 자산 구조화(권장)
```
`/solution-capture` skill이 7단계로 대화에서 증상·근본원인·해결을 발췌해 우리 T1..T9 스키마로
작성·검증(`validate.py`)·동기(`sync_rules.py`)한다. 수동 작성도 가능:
```bash
# <repo>/docs/solutions/<T*>/<증상>-<module>-<YYYYMMDD>.md 직접 작성(frontmatter)
"$KB_PY" <repo>/docs/solutions/validate.py     # frontmatter/카테고리 검증
"$KB_PY" <repo>/docs/solutions/sync_rules.py   # bkit regression-rules 동기 + 승격 후보 리포트
```

**(3b) 작업 시작·종료 — 작업메모리**
```
<repo>/.ai/working/_TEMPLATE.md → <slug>.md 작성 + ACTIVE.md에 `| [slug](slug.md) | 진행 | … |` 한 줄
… 작업 중: 체크리스트·시도·결정·다음 할 일 갱신(hook이 주입·자동 기록) …
/wrap                    # 작업 종료: 교훈 제안 + 일화 기록 + 작업 파일 정리
```
지난 작업의 결정·경과는 MCP `episode_search`로 찾는다.

**(4) 격상 후보 확인 + 격상 실행**
```bash
# 후보 자동 탐지
"$KB_PY" <repo>/docs/solutions/sync_rules.py --dry-run
# → [A] 없음·[B] 없음이면 완료. 후보 있으면 /kb-promote skill 실행.
```
`/kb-promote` skill이 [A]/[B] 후보별로 내용 미리보기 + 승인 → 패턴 합성/작성 → ID 등록 → 커밋/push 까지 처리. [B]는 push 전 eval_gate pre-warm 필요(§8 캐싱 참고).
```bash
# [B] eval pre-warm (ai-memory memory/ 변경 후, push 전)
"$KB_PY" ~/ai-memory/tools/eval_gate.py   # → PASS 확인 후 ai-memory push (재색인 포함)
```

---

## 11. 설계 원칙·근거 (왜 이렇게)

- **graphify ≠ RAG (§4)**: 관계(graphify)와 의미(RAG)는 다른 축. 관계는 프로젝트 내부에서 dense하고
  스코프 의존적, 의미는 스코프 무관. 그래서 graphify=프로젝트별, RAG=전역.
- **전역은 증류만**: 모든 프로젝트 내용을 전역에 덤프하면 사이즈·노이즈·stale로 cross-project 이득이
  사라진다. 전역엔 일반화된 원칙만 올린다.
- **정본 직접 색인(§5)**: 런타임 복사본을 없애 분기·유실을 구조적으로 차단.
- **로그는 질의, 산문은 RAG**: bkit 구조화 로그를 임베딩하지 않고 MCP로 질의(고신호 유지).
- **측정 기반 품질**: eval로 검색 품질을 수치화하고 게이트로 회귀를 막는다(주관 배제).
- **오프라인·IP 보안**: 임베딩/reranker 모두 로컬 ONNX(fastembed), 외부 전송 0.

---

## 12. 확장·튜닝·주의

- **코퍼스 성장 시**: 골드셋(`eval/queries.json`)을 함께 키우고 `kb_eval`로 재측정 → pool/모델/임계
  재튜닝. 현재 소형 코퍼스에선 reranker가 쉽게 만점이라, bi-encoder **재현율(pool)**이 커질수록 중요해진다.
- **모델 교체**: `KB_EMBED_MODEL`/`KB_RERANK_MODEL` env. 임베딩 변경 시 인덱스 자동 재빌드.
- **노드 타입 확장**: 타입은 `ontology.yaml`의 데이터다(코드는 타입 이름을 모른다). 새 타입은 그 타입에만 걸 관계 규칙이
  생길 때만 만들고, 규칙 없이 분류만 다르면 기존 타입 + 태그로 둔다. 새 ID 항목은 rel 주석 필수(없으면 색인 실패).
- **일화 정리 단계(E3, 후속)**: 같은 노드를 `about`하는 일화가 쌓이면(≥ 3건) 원칙 후보로 보여 주는 단계 — 일화가 쌓인 뒤 구현.
- **게이트 임계**: `KB_EVAL_MIN_MRR`/`KB_EVAL_MIN_P1`(기본 0.9), `KB_EVAL_STRICT`.
- **graphify 버전**: 거의 매일 릴리스 → `requirements.txt`로 핀 + 주기 검토. 업그레이드 시 skill 재동기
  (`python -m graphify install --platform claude`) + 그래프 재빌드 필수.
- **공급망 정책**: 의존성은 ≥7일 적격 버전으로 핀(`requirements.txt`). 휠 전용 설치(sdist 스크립트 차단).

---

### 관련 문서
- `ai-memory/README.md` — 영구메모리 운영 상세(구조·검색·게이트·쓰기 규칙). 이전 안내: `../kb-global/README.md`.
- `<project>/.ai/KNOWLEDGE_MAP.md` — 각 프로젝트의 정본/인덱스 경계.
- `04-bkit-customization-guide.md` — bkit 커스터마이즈(이 시스템의 install.py 배포 기반).
- `ai-memory/memory/rtl/methodology.md` — RTL 에이전트 방법론(Constrain & Escalate, 정본). 배포본 `~/.claude/agent-kit/methodology.md`.
- `ai-memory/plans/phase-07-structured-memory.md`·`phase-08-short-term-memory.md` — 온톨로지·하이브리드 검색, 작업메모리·일화 설계와 실측.
