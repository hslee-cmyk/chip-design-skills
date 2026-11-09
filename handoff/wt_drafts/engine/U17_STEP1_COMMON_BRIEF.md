# U17 단계 ① 공통 브리핑 (모든 code·test agent 필독)

base = master `a3987ab` (계획 v6.5, design 40·41·42 v1.6 승인본, 사용자 2026-10-12 "design 승인").
design 경로(각 worktree 안): `docs/02-design/features/gain-budget-gmid-sizing.{40-engine,41-gain-budget,42-gap-checklist}.design.md`,
계획: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`. 엔진: `skills/analog-gmid-design/gmid_engine/`.
사용자 결정 기록: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md` (읽기만).

## 절대 규칙
1. **design 그대로 구현한다. as-built 결정 금지.** design에 없는 것을 정해야 하거나, design이 모순·불가능하면 **그 자리에서 멈추고 보고**한다(무엇이, 어느 절이, 선택지). 범위 축소·대체 금지.
2. **graph 단일 정본(DEC-83, 40 §2.4)**: 설계 값은 graph 필드에만. graph 밖 허용 저장소는 LUT memo(순수 함수)·S3 기록/색인·실행 계수·S0 스냅샷 영속화 넷뿐. 새 dict 캐시·객체 칸·사본 금지.
3. **계산값 재사용**: 한 번 계산한 값은 입력이 안 바뀌면 다시 계산하지 않는다. 루프 불변식은 S0 수준 필드로. 같은 인자 반복 호출 금지.
4. **틀린 구조는 전체 재작성**(부분 패치 금지). 대체한 옛 코드·옛 경로는 **같은 변경에서 삭제**(만들면 반드시 배선 -- 새 코드는 실제 파이프라인 경로에서 호출돼야 한다).
5. **상수 발명 금지**(WP-03), **회로 이름·소자 이름 코드 금지**(topology 무관).
6. **파일 분할 규칙**(사용자 2026-10-07, NEW_ENGINE_DESIGN_REQUIREMENTS §1.2): 파일 하나 = 한 개념/계산 블록, (A) 파일당 독립 진입점 1개, (B) `_` helper는 그 파일만(2파일 이상이면 helper 모듈), (C) `@compute_block` 파일당 ≤1, (D) test는 `tests/<pkg>/test_<file>.py` 1:1, `_module_map.py`에 새 파일 등록(책임 한 문장·계획 ID), 층 순서 core<lut<authoring<graph<sizing<metrics<search<layout<convergence<report<pipeline.
   끝나기 전 `tests/structure` 통과 필수(규칙 A~I, 위반 0).
7. **작성자 ≠ 검증자**: code agent는 test·기대값을 쓰지 않는다(옛 test가 design 삭제로 깨지면 고치지 말고 목록으로 보고). test agent는 피검 코드를 불러 기대값을 만들지 않는다 -- design 식·LUT·손계산으로 독립 도출.

## 실행 환경·git 가드
- python: `/c/Python314/python.exe` (bash에서 `timeout` 래퍼로 감싸지 말 것 -- user site가 빠져 pytest를 못 찾는다). `export OPENBLAS_NUM_THREADS=1`.
- 실행 위치: `<worktree>/skills/analog-gmid-design`, `python -m pytest -q gmid_engine/tests/<경로> -p no:cacheprovider`.
- **전체 suite는 끝에 한 번만**(메모리 한도). 중간엔 관련 test만. 긴 실행은 결과를 파일에 쓴다(`> <worktree>/../_scratch_<unit>/run.txt`).
- git: 항상 `git -C <자기 worktree>`, 스크립트는 `set -e`. 다른 worktree·master를 건드리지 않는다. reset --hard·checkout 다른 브랜치·push·merge 금지. 커밋은 자기 브랜치에만.
- 커밋 메시지 끝:
  `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>` 와 `Claude-Session: https://claude.ai/code/session_012FxFP7YSWEBBCB9rmBQjLL`
- 임시 파일은 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_<unit>/`(자기 것만).

## 최종 보고(한국어) 필수 항목
1. 구현/작성한 design 절 목록과 각 절의 상태(구현됨/부분/못함+사유).
2. 멈춤·보고 항목(as-built 결정이 필요했던 곳).
3. 삭제한 옛 코드·경로(파일:줄), 배선 위치(호출부 파일:줄).
4. **graph 단일 정본 자기 점검**: 새로 만든 graph 밖 저장소 0인지(있으면 목록), 40 §2.4.8 필드 소유표 대조 결과.
5. **계산값 재사용 자기 점검**: 같은 입력 재계산 경로가 남았는지, 루프 불변식 위치.
6. `tests/structure` 결과(규칙별 대상 수·위반 수), 관련 test 결과, 깨진 옛 test 목록.
7. 커밋 해시.
