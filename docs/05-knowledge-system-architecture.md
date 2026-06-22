# 지식 시스템 아키텍처 — 4계층 / 2-tier RAG

> **한 줄 결론**: 프로젝트에서 풀어낸 지식을 *사라지지 않는 자산*으로 만든다. 프로젝트별 단기 지식은
> **graphify(관계 그래프)**, 전 프로젝트 공유 일반 원칙은 **전역 RAG(의미 검색)**로 분리하고,
> **정본은 git, 인덱스는 재생성**으로 둔다. 모든 검색은 다국어 2단계(임베딩→reranker)이고,
> 검색 품질은 eval로 측정·pre-push 게이트로 회귀를 차단한다.

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

## 2. 한눈에 — 4계층 × 2-tier

```
            ┌─────────────────────── 4계층 ───────────────────────┐
 L1 기록    무슨 일이 있었나 (자동·원시)        bkit: audit/decisions/regression-rules/metrics
 L2 큐레이션 어떻게 풀었나 (사람·증류·정본)      docs/solutions(프로젝트) + kb-global/principles(전역)
 L3 항법    무엇이 무엇과 연결되나 (관계 지도)    graphify  → <project>/graphify-out
 L4 검색    질문에 맞는 조각 회수 (의미 검색)     전역 RAG  → .tools/kb-global/kb.sqlite

            ┌────────────── 2-tier 메모리 ──────────────┐
 단기·프로젝트   = L3 graphify (관계, 프로젝트 로컬, 휘발)
 장기·전역       = L4 RAG     (의미, 전 프로젝트 공유, 증류만)
```

핵심 원칙 3가지:
1. **graphify와 RAG는 같은 정보를 색인하지 않는다** — 관계는 graphify, 의미는 RAG (§4).
2. **정본은 git, 인덱스는 재생성** — 증류 지식은 절대 유실되지 않는다 (§5).
3. **산문은 RAG, 구조는 질의** — bkit 로그는 임베딩하지 말고 MCP로 질의한다 (§3.1).

---

## 3. 4계층 상세

### 3.1 L1 — 기록 (bkit, 자동·원시)
bkit 플러그인이 **자동으로** 남기는 append-only 기록. 사람이 손대지 않는다.
- `.bkit/audit/*.jsonl`(감사), `.bkit/decisions/*.jsonl`(결정 추적), `pdca-status.json`(상태),
  checkpoints, quality-metrics, **`regression-rules.json`**(카테고리별 누적 규칙).
- **접근법**: 임베딩 금지. `bkit_audit_search`/`bkit_regression_rules`/`bkit_gap_analysis` 등
  **MCP 도구로 정확 질의**한다. (방대·저신호라 RAG에 넣으면 노이즈·비용만 늘어남.)

### 3.2 L2 — 큐레이션 (사람·증류·**정본**)
사람이 확인해 증류한 재사용 지식. **두 스코프**로 나뉜다:
- **프로젝트 단기**: `<project>/docs/solutions/**` — 그 프로젝트에서 푼 버그 instance를
  실패분류 T1..T9 폴더에 기록(frontmatter + `schema.yaml` + `validate.py`).
- **전역 장기(증류)**: `chip-design-skills/kb-global/principles/**` +
  `chip-design-skills/agent-kit/failure-taxonomy.md` — 여러 프로젝트에 일반화되는 원칙만.
- 도메인 지식: `<project>/.ai/analysis/`(모듈 분석), `<project>/.ai/knowledge/`(버그·툴 가이드).

### 3.3 L3 — 항법 (graphify, 프로젝트 로컬)
`graphifyy`(0.8.39, **tree-sitter-verilog AST**)가 프로젝트의 코드·설계·분석·ADR을 **관계 그래프**로
만든다. "무엇이 무엇과 연결/경로/중심 노드"를 본다. `<project>/graphify-out`에 산출(재생성 가능).
- 질의: `graphify query "<주제>"`, `graphify path A B`, `graphify explain X`.
- 갱신: `graphify update .`(코드) / `/graphify --update`(문서 의미추출, LLM).

### 3.4 L4 — 검색 (전역 RAG, 공유)
**증류 원칙만** 임베딩한 의미 검색. 모든 프로젝트가 하나의 전역 인덱스를 공유한다.
- 코퍼스: `kb-global/principles/` + `agent-kit/failure-taxonomy.md`(정본 git, **직접 색인**).
- 저장: `.tools/kb-global/kb.sqlite`(sqlite-vec, 재생성). 외부 전송 0 → RTL IP 보안.
- 파이프라인: 다국어 2단계(§7). 질의는 스코프 무관 → cross-project 재사용의 핵심.

---

## 4. 2-tier 메모리 — graphify ≠ RAG (왜 분리하나)

| | 단기·작업 기억 | 장기·일반 기억 |
|--|----------------|----------------|
| 인덱스 | **graphify**(관계·항법) | **전역 RAG**(의미 검색) |
| 코퍼스 | 프로젝트 `.ai/analysis`·설계·`docs/solutions`(instance) | `kb-global/principles` + taxonomy(증류만) |
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
| `chip-design-skills/kb-global/principles/**` (전역 원칙) | `.tools/kb-global/kb.sqlite` (L4 인덱스) |
| `chip-design-skills/agent-kit/failure-taxonomy.md` | `.tools/hf-cache/` (임베딩 모델 캐시) |
| 툴링: `kb_index/kb_search/kb_eval/eval_gate.py`, `requirements.txt` | `.tools/kb-venv/` (공유 venv) |

핵심 설계(**단일 정본**): `kb_index.py`는 런타임에 principles 복사본을 만들지 않고
**git 정본을 직접 색인**한다(경로는 `parents[1]=워크스페이스`로 자동 해석). 따라서 정본/인덱스가
분기할 수 없고, 격상된 지식은 항상 git(원격)에 있어 유실되지 않는다.

⚠️ **격상은 정본에만 쓴다**: 일반 원칙은 `chip-design-skills/kb-global/principles/`(git)를 편집한다.
런타임 `.tools/kb-global`은 인덱스 전용이라 **거기 쓰면 다음 배포 때 덮여 사라진다**.

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
        │ chip-design-skills/kb-global/principles/ 편집 + commit/push   ← L2 전역 정본
        ▼   kb_index.py 재색인
[4] 전역 RAG 갱신 → 모든 프로젝트가 공유              ← L4
        ▲
        └─ 착수 전 preflight가 회수 (§7)                ← recall
```

이 루프가 "한 프로젝트의 교훈 → 전 프로젝트 일반지식"의 격상 경로다.

---

## 7. 검색 파이프라인 — 다국어 2단계

작업 착수 전 `preflight.py`가 **장기(전역 RAG) + 단기(프로젝트 graphify)** 를 한 번에 조회한다.
전역 RAG는 2단계:

```
질의 → [1] bi-encoder + 메타필터 → 후보 top-N (KB_RERANK_POOL, 기본 20)
      → [2] cross-encoder rerank      → 최종 top-k (기본 5)
```
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

---

## 8. 품질 보증 — eval + pre-push 게이트

검색 품질을 "느낌"이 아니라 **숫자**로 관리한다.

- **eval 하니스**: `kb_eval.py` + 골드셋 `kb-global/eval/queries.json`(한/영 16질의, 부분일치 라벨).
  설정별 **MRR/P@1/hit@k** 비교. 실측: bi-encoder only MRR 0.79·P@1 0.75(2질의 top-5 miss) →
  **rerank(pool≥10) MRR 1.00·P@1 1.00**.
  ```bash
  "$KB_PY" .tools/kb-global/kb_eval.py --verbose
  ```
- **pre-push 게이트**: `.githooks/pre-push` + `eval_gate.py`. `kb-global/**`가 push에 포함되면
  인덱스 최신화 → eval → `MRR/P@1 < 임계`(기본 0.9)면 **push 차단**. 전 프로젝트 공유 지식의
  품질 회귀를 push 직전에 막는다. 인프라 문제는 SKIP(`KB_EVAL_STRICT=1`이면 차단). 우회: `--no-verify`.
  ⚠️ 코퍼스가 커지면 골드셋을 함께 키우고 재측정(pool/모델 재튜닝).

### 8.1 자동화 (hooks) — "배관은 자동, 판단은 넛지"

자산화 루프의 *배관*은 hook으로 결정론적 자동화, *판단*(무엇을 자산화·근본원인)은 적시 환기만 한다.

| 단계 | 메커니즘 | 동작 |
|------|----------|------|
| **A. validate+sync** | 프로젝트 `.git/hooks/pre-commit` | `docs/solutions/*.md` 커밋 시 `validate.py`(불량이면 **차단**) + `sync_rules.py`(regression-rules 재생성·stage) |
| **B. graph 갱신** | 프로젝트 `.git/hooks/post-commit` | `.v/.sv` 커밋 + `graphify-out` 존재 시 `graphify update` 백그라운드(코드 전용·비차단) |
| **C. 품질 게이트** | 키트 `.githooks/pre-push` | (위) kb-global push 시 eval 게이트 |
| **D. recall 넛지** | CC `PreToolUse` 훅 `kb-preflight-nudge.py` | RTL(`db/design/**/*.v`) Edit/Write 시 세션당 1회 "preflight 권장" 컨텍스트 주입(비차단) |
| capture 넛지 | `/solution-capture` skill 트리거 | "그게 됐다"류 감지 → 자산화(모델 판단) |

배포: `python install.py --install-git-hooks --project <repo>`(A·B) · `--only hooks --project <repo>`(D).
`.git/hooks`는 클론마다 재실행 필요. 완전 무인 자산화는 *판단*이 LLM 몫이라 불가하며, 그게 의도다(노이즈 방지).

---

## 9. 구성요소 지도

| 위치 | 무엇 | git |
|------|------|:--:|
| `kb-global/principles/*.md` | 전역 증류 원칙(정본) | ✅ |
| `agent-kit/failure-taxonomy.md` | 실패분류 T1..T9(정본) | ✅ |
| `kb-global/kb_index.py` | 전역 RAG 인덱서(정본 직접 색인) | ✅ |
| `kb-global/kb_search.py` | 2단계 검색(bi-encoder+reranker) | ✅ |
| `kb-global/kb_eval.py` + `eval/queries.json` | 품질 eval + 골드셋 | ✅ |
| `kb-global/eval_gate.py` + `.githooks/pre-push` | 회귀 차단 게이트 | ✅ |
| `kb-global/requirements.txt` | 공유 venv 핀 | ✅ |
| `project-template/{ai/rag/preflight.py, docs/solutions/**}` | 프로젝트 스캐폴드 | ✅ |
| `<workspace>/.tools/kb-venv` · `hf-cache` · `kb-global/kb.sqlite` | 공유 venv·모델·인덱스 | ❌ 재생성 |
| `<project>/graphify-out` | 프로젝트 관계 그래프 | ❌ 재생성 |

전역 도구는 `install.py --only kb-global`이 `<workspace>/.tools/kb-global`로 배포한다(인덱스는 보존).

---

## 10. 사용법 (Quickstart)

`KB_PY` = 공유 venv python (`<workspace>/.tools/kb-venv/Scripts/python.exe`).

**(0) 공유 venv 1회 구성** (워크스페이스당 1회)
```bash
cd <workspace>
python -m venv .tools/kb-venv
.tools/kb-venv/Scripts/python.exe -m pip install --only-binary=:all: -r chip-design-skills/kb-global/requirements.txt
python chip-design-skills/install.py --only kb-global   # 전역 툴링 배포
"$KB_PY" .tools/kb-global/kb_index.py                    # 전역 RAG 색인
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

**(4) 일반 원칙 격상 (cross-project)**
```bash
# chip-design-skills/kb-global/principles/ 편집(정본, git)
cd chip-design-skills && git add kb-global/principles && git commit && git push   # pre-push 게이트 통과 필요
"$KB_PY" <workspace>/.tools/kb-global/kb_index.py        # 재색인 → 전 프로젝트 공유
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
- **게이트 임계**: `KB_EVAL_MIN_MRR`/`KB_EVAL_MIN_P1`(기본 0.9), `KB_EVAL_STRICT`.
- **graphify 버전**: 거의 매일 릴리스 → `requirements.txt`로 핀 + 주기 검토. 업그레이드 시 skill 재동기
  (`python -m graphify install --platform claude`) + 그래프 재빌드 필수.
- **공급망 정책**: 의존성은 ≥7일 적격 버전으로 핀(`requirements.txt`). 휠 전용 설치(sdist 스크립트 차단).

---

### 관련 문서
- `../kb-global/README.md` — 전역 지식층 운영 상세(영속성 모델·검색 파이프라인·게이트).
- `<project>/.ai/KNOWLEDGE_MAP.md` — 각 프로젝트의 정본/인덱스 경계.
- `04-bkit-customization-guide.md` — bkit 커스터마이즈(이 시스템의 install.py 배포 기반).
- `../agent-kit/methodology.md` — RTL 에이전트 방법론(Constrain & Escalate).
