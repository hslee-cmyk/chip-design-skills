# 세션 인계 2026-11-09 (다른 서버에서 이어서 작업)

## 0. 복원 방법
- 저장소: `git@github.com:hslee-cmyk/chip-design-skills.git` -- `master` + 진행 중 브랜치(아래 §3)를 받는다.
- 결정·증거 폴더(원래 저장소 밖 `fpga/wt/_drafts/`)는 브랜치 **`handoff/2026-11-09`**의 `handoff/wt_drafts/`에 스냅샷으로 들어 있다. 새 서버에서 `fpga/wt/_drafts/`로 복사해 쓴다(계획·결정·agent 브리핑이 모두 `wt/_drafts/...` 경로를 인용한다). worktree 루트도 `fpga/wt/`.
- gmid agent 정의(`.claude/agents/gmid-*.md` 5개)도 같은 브랜치에 있다 -- 새 서버의 `chip-design-skills/.claude/agents/`로.
- **git에 없는 것(직접 옮겨야 함)**: gm/ID·Razavi 원본 서적 PDF(`skills/analog-gmid-design/references/gmid_sources/` -- 출판 서적이라 .gitignore, 원래 경로·sha256은 그 폴더 README), PDK(`C:/pdk/...` -- sky130 + KLayout 덱, `C:\pdk\sky130_klayout_pdk.PROVENANCE.txt`), OSS CAD Suite·ngspice·KLayout 설치, auto-memory(`~/.claude/projects/<proj>/memory/`).
- 규칙 정본: `chip-design-skills/CLAUDE.md`(임시 규칙 O-229와 7번 '위임의 한계 = 원칙 19·20', 원칙 1a gm/ID 원본 우선 O-270), 상위 `fpga/CLAUDE.md`(graph 단일 정본).

## 1. 지금 멈춘 자리 -- 사용자 답을 기다리는 결정
계획 수정은 원칙 19·20(O-267)에 따라 **병합 전 사용자 승인**. 아래를 하나의 계획 수정안으로 묶어 승인받을 차례.

1. **계획 v6.39.6**(브랜치 `plan/v6396-fs1`, head `ec1aad3a`, master 미병합) -- O-264(차동 입력 구조 판정)·O-265(DC 묶음과 대칭 사이징 분리, 찾아 둔 대칭 짝 사용)·FS-1 짝 정의·card DI-1. 판정 r2 Major 1(N-1)은 넷째 커밋에서 정정, 재판정 전.
2. **계획 전수 모순 점검**(사용자 지시) 종합: `evidence/2026-11-08/plan_fullcheck_summary.md`(구간 보고서 6) -- 결정 D1~D9, 문언 정합 묶음 B 1~9, 불확실 C.
   - D1 입력 방향 정본(P-4 번복, Q-DI3), D2 대칭 정본 필드(Q-FS2: DEC-97 궤도 대 matching_groups, N3.2 :545 legacy 함수), D3 Q-W1 재풀이 자리(O-257로 닫힘), D4 spec/interface card 흐름(DEC-86), D5 review_needed, D6 DEC-93 교류접지 재해석, D7 O-264 한정, D8 오라클 쪽 차동 판정.
3. **입력 고정점(초기값)** -- 사용자 결정 O-268(피드백 = 출력 스윙 최대 출력 바이어스), O-269 → O-272 정정(비피드백 = 물리 정합 중앙값 = 가능 창 중심, O-172 유지), O-271(v_cm max-min·재개방은 초기값에서 빼고 ICMR 쪽 통일). 근거:
   - 모순 점검 `evidence/2026-11-08/o268_contradiction_check.md`(모순 3 C1~C3, K1~K6)
   - 원본 대조 감사 `evidence/2026-11-08/o270_gmid_source_audit.md`(위반 후보 4 V1~V4, O-271 비교, C1~C3 해소안 -- 출력 범위 = θ 틀 R-1′ 출력 마디 구간, 원본 JM Ex.6.4 p.255·Razavi Ex.9.6 p.305)
   - 실측 `evidence/2026-11-08/o268_measure.md`(출력 스윙 중심 생산자 없음, 5회로 창 판정, `feedback: []` = β=1 기본)
   - **사용자에게 물은 것(답 대기)**: E1 ICMR 통일 방식((A) θ 틀 창 하나 -- DEC-103 개정 필요 / (B) 권고: 초기값 = θ 틀 창 중심, ICMR 검증 = KCL·생산자 하나), E2 원본 위반 후보 V3(matching L 하한)·V4(cubic-Hermite 보간), E3 피드백 판정(권고: DC 경로 있는 되먹임 = 소자 미선언 β=1 직결·저항 등, Cf만이면 비피드백).

## 2. 진행 중 card FS-1 (손가락 좌표, DEC-108)
- 상태: code 브랜치 `role/code/20261107-fs1`(head 802b3ed1 근처)에 v6.39.5 기준 구현(start_partner 등) -- **원칙 위반 덧대기 구조라 재작성 대상**(사용자 "원칙에 부합하지 않는코드는 재작성해"). 계획 v6.39.6·입력 고정점 개정 승인 → design·card 재작성 범위 → code 재작성 순서. code·design·card·test는 위임.
- test 브랜치 `role/test/20261107-fs1`(묶음 A·B·C 병합), audit 브랜치 `role/audit/20261107-fs1`(freeze 판정 기록). card(spec/interface)는 test 브랜치의 `docs/02-design/specs/20261107-fs1.*`.
- 남은 red 분류·dispute는 `la1_auto_decisions.md` A-195~A-206.

## 3. push한 브랜치
`master`, `handoff/2026-11-09`, `plan/v6396-fs1`, `role/code/20261107-fs1`, `role/test/20261107-fs1`, `role/audit/20261107-fs1`, `role/test/20261104-gc1`, `role/audit/20261104-gc1`, `card/fs1`. 그 밖의 옛 로컬 브랜치(350여 개)는 push하지 않았다.

## 4. 기록 위치
- 사용자 결정: `wt/_drafts/user_decisions.md`(O-1~O-272), 위임 기록: `wt/_drafts/la1_auto_decisions.md`(A-1~A-212).
- 이 세션 증거: `wt/_drafts/evidence/2026-11-07/`, `2026-11-08/`.
- 다음 card 순서(LA-1 경로): FS-1 재작성 → FP-1(분산 gate R 근거 = Razavi 2001 §7.2.1 p.214, `gmid_sources/razavi_2001`) → DI-1 → LA-1a + LA-1. GC-1·HC-1+GC-8·EO-1·SF-1 r9·OP-5·LA-0 상태는 N6.1 순서표 확인.

## 5. 운영 주의(이 세션에서 반복된 사고)
- 회로당 엔진 실행 ~5 GB, 여유 메모리 3.7 GB 미만 착수 금지·1 GB 미만 정지, pytest 하나씩.
- agent 금지 명령(heredoc, `python -`, `python -c` 대입, cat stdin, `<<<`, `sed -i`, 수동 `&`, `timeout`, `taskkill`, 공용 scratchpad 덮어쓰기) 위반이 계속 재발 -- 브리핑에 항상.
- 계획을 판정 결과로 덧대지 말 것, 새 문제는 gm/ID 원본 접근부터(원칙 1a).
