# kb-global — 장기·전역 지식 (정본, 버전관리)

fpga 전 프로젝트가 공유하는 **장기 일반지식 RAG**의 *정본 소스*. 이 디렉터리는 git으로
버전관리되고 github에 푸시되므로 **증류된 지식이 유실되지 않는다**.

## 영속성 모델 — 정본은 git, 인덱스는 재생성

| 종류 | 위치 | git |
|------|------|:--:|
| 증류 원칙(authored) | `kb-global/principles/*.md` (여기) | ✅ |
| failure-taxonomy(정본) | `../agent-kit/failure-taxonomy.md` (install 시 principles로 병합) | ✅ |
| 툴링 | `kb-global/kb_index.py`, `kb_search.py` | ✅ |
| venv 핀 | `kb-global/requirements.txt` | ✅ |
| **인덱스/모델/venv** | 런타임 `fpga/.tools/{kb-global/kb.sqlite, hf-cache, kb-venv}` | ❌ 재생성 |

→ `install.py --only kb-global` 가 정본을 런타임(`<workspace>/.tools/kb-global/`)으로 배포하고
agent-kit taxonomy를 principles로 병합한다. `kb.sqlite` 등 재생성물은 보존(덮어쓰지 않음).

## 배포 / 재색인
```bash
python install.py --only kb-global              # 정본 → <workspace>/.tools/kb-global 배포
VPY=<workspace>/.tools/kb-venv/Scripts/python.exe
"$VPY" <workspace>/.tools/kb-global/kb_index.py # 배포 후 재색인
```

## 지식 격상 (cross-project)
프로젝트 `docs/solutions/` 패턴이 일반화(3건+/원칙)되면:
1. `kb-global/principles/`에 일반화 형태로 추가(이 repo, 버전관리).
2. commit + push (github → 백업·타기계 공유).
3. `install.py --only kb-global` 재배포 → `kb_index.py` 재색인 → 모든 프로젝트 공유.

## 원칙 작성 규칙
- 특정 프로젝트 버그 instance 금지 — **여러 프로젝트 일반화 원칙만**.
- frontmatter: `kind`(pattern|principle|failure-taxonomy), `domain`, `tags`.
- 프로젝트 고유 지식은 각 프로젝트 `docs/solutions/`(단기) + graphify(항법).
