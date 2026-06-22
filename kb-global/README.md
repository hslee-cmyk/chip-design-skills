# kb-global — 장기·전역 지식 (정본, 버전관리)

fpga 전 프로젝트가 공유하는 **장기 일반지식 RAG**의 *정본 소스*. 이 디렉터리는 git으로
버전관리되고 github에 푸시되므로 **증류된 지식이 유실되지 않는다**.

## 영속성 모델 — 정본은 git, 인덱스는 재생성

**Option 2 (단일 정본)**: `kb_index.py`는 이 repo의 정본 코퍼스를 **직접 색인**한다 —
런타임에 principles 복사본을 두지 않으므로 분기·유실이 구조적으로 불가능하다.

| 종류 | 위치 | git |
|------|------|:--:|
| 증류 원칙(authored) | `kb-global/principles/*.md` (여기, 직접 색인) | ✅ |
| failure-taxonomy(정본) | `../agent-kit/failure-taxonomy.md` (직접 색인) | ✅ |
| 툴링 | `kb-global/kb_index.py`, `kb_search.py` | ✅ |
| venv 핀 | `kb-global/requirements.txt` | ✅ |
| **인덱스/모델/venv** | 런타임 `fpga/.tools/{kb-global/kb.sqlite, hf-cache, kb-venv}` | ❌ 재생성 |

→ `kb_index.py`가 `chip-design-skills/kb-global/principles/` + `agent-kit/failure-taxonomy.md`(git)를
**직접 읽어** 런타임 `fpga/.tools/kb-global/kb.sqlite`(재생성)만 만든다. 위치는 `parents[1]=fpga`로
자동 해석(런타임/정본 어디서 실행해도 동일). `install.py --only kb-global`은 **툴링만** 런타임에
배포한다(편의용 사본; 정본 principles는 repo에만).

## 검색 파이프라인 (2단계 — 다국어)
1. **bi-encoder 검색**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
   (dim=384, 다국어) + 메타필터 → 후보 top-N(`KB_RERANK_POOL`, 기본 20).
2. **cross-encoder rerank**: `jinaai/jina-reranker-v2-base-multilingual` → 최종 top-k.

- bi-encoder/reranker 모두 다국어 → 한/영 혼합 질의에서 순위 분리 개선.
- env: `KB_EMBED_MODEL`(색인·검색 동일해야 함; 변경 시 자동 재빌드), `KB_RERANK_MODEL`,
  `KB_RERANK_POOL`. CLI: `--no-rerank`(bi-encoder만), `--pool N`. 모델 없으면 rerank 폴백.
- **품질 검증(eval)**: `kb_eval.py` + 골드셋 `eval/queries.json`(한/영 16질의)로 설정 비교.
  ```bash
  "$VPY" .tools/kb-global/kb_eval.py --verbose   # MRR/P@1/hit@k 비교 표
  ```
  측정값(16질의 골드셋): bi-encoder only MRR 0.79·P@1 0.75(2질의 top-5 miss) →
  **rerank(pool≥10) MRR 1.00·P@1 1.00**. reranker가 결정적 개선.
  ⚠️ 코퍼스가 격상으로 커지면 골드셋 보강 후 **재측정**(pool/모델 재튜닝). `--no-rerank`로 A/B 가능.
- **pre-push 게이트**: `.githooks/pre-push`가 `kb-global/**` push 시 인덱스 최신화 + eval 실행 →
  `MRR/P@1`이 임계(`KB_EVAL_MIN_MRR`/`KB_EVAL_MIN_P1`, 기본 0.9) 미만이면 **push 차단**(회귀 방지).
  로직: `eval_gate.py`. 인프라 문제는 SKIP(품질 회귀만 차단; `KB_EVAL_STRICT=1`이면 차단). 우회: `git push --no-verify`.

## 재색인 / 툴링 배포
```bash
VPY=<workspace>/.tools/kb-venv/Scripts/python.exe
"$VPY" <workspace>/.tools/kb-global/kb_index.py   # 정본 직접 색인 (배포 불필요)
python install.py --only kb-global                # 툴링(kb_index/search) 변경 시에만
```

## 지식 격상 (cross-project)
프로젝트 `docs/solutions/` 패턴이 일반화(3건+/원칙)되면:
1. **이 repo** `kb-global/principles/`에 일반화 형태로 추가 (정본·버전관리).
2. commit + push (github → 백업·타기계 공유, 유실 불가).
3. `kb_index.py` 재색인 → 모든 프로젝트 공유. (런타임 `.tools/kb-global`엔 원칙을 쓰지 않는다.)

## 원칙 작성 규칙
- 특정 프로젝트 버그 instance 금지 — **여러 프로젝트 일반화 원칙만**.
- frontmatter: `kind`(pattern|principle|failure-taxonomy), `domain`, `tags`.
- 프로젝트 고유 지식은 각 프로젝트 `docs/solutions/`(단기) + graphify(항법).
