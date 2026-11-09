# LA-1까지 빠른 진행 -- 공통 브리핑 (2026-11-03)

**임시 규칙 O-229(이 브리핑과 card 절차보다 앞선다, 정본 = 저장소 `CLAUDE.md` 맨 위):** 물리 정합과 graph 단일 정본·단일화는 완화 금지. test = 그 card의 test + `tests/structure` + 2회로 연기(`folded_cascode`, `ngcc_3stage_ff`). 전체 test는 card마다 돌리지 않는다. 판정은 1회, Major를 고쳤을 때만 재판정. Major = 물리 정합·graph 정본 위반, fail-open, 기준 약화, 엔진 누출, 범위 위반, 필수 test 실패. 나머지는 LA-1 재점검으로 넘긴다.

사용자 지시: "우선 최대한 빨리 la-1까지 구현해". 절차(bkit PDCA, 작성자 ≠ 검증자, 승인 게이트)는 유지하고 왕복과 대기를 줄인다.

## 사실
- master c8ecc4e7(계획 v6.38.7, design v1.14.2 승인본). 결정 O-220~O-224 = wt/_drafts/user_decisions.md 끝 행. 후보 근거 = wt/_drafts/evidence/2026-11-03/la1a_pg/d_questions.md §1~§5.
- 순서: 공통 선행 15 card(IT-1, IT-2, WB-1, UB-1, NL-1, HC-S, TB-1, HC-1, GC-8, GC-1, EO-1, OP-2, OP-3, OP-7, XRUN-F1 card C) → 재측정 → Q0(LA-1a 대 LA-1) → LA-1.
- 저장소: C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills, worktree 루트 C:/Users/HSLEE/Documents/Todoc/fpga/wt.

## 위임(O-225, O-226)
- LA-1 구현까지 측정과 결정 간 모순 점검은 뒤로 미루고 구현에 집중한다. 그 시점에 재점검해 고친다.
- LA-1까지 결정은 사용자 승인 없이 권고대로 채택한다. agent는 '사용자 질문'을 만들지 말고 권고 하나와 근거·대안·원래 취지와 다름을 오케스트레이터에게 보고한다. 오케스트레이터가 wt/_drafts/la1_auto_decisions.md에 기록한다.
- 유지: 독립 검증(작성자 ≠ 검증자), bkit 순서, fail-closed·E-0·toy·회귀·병합 때 연기 시험, graph 단일 정본, 측정을 빼서 fail-open이 되지 않음.
- 위임 밖이라 멈추고 보고: push, 근본원칙 변경, topology connectivity 수정, 기준 약화로 시험을 통과시키는 일.

- 전 card 공통(A-34): `structure_rule_fp` 입력 rule 파일을 고치는 card는 같은 변경에서 `structure.json`의 rule_hash 줄만 재기록하고 connectivity는 건드리지 않으며, '사실이 여전히 적용됨' test를 둔다. stale이면 사실이 조용히 안 쓰인다.

## 빠르게 하는 규칙
- 할 일 하나를 끝까지 끝낸다. 범위를 넓히지 않는다. 승인을 틀리게 만드는 것이 아니면 표지만 하고 넘어간다.
- 원칙으로 정해지는 것은 정하고 근거를 적는다. 사용자 몫(spec, 회로 해석, 삭제·공유, 원칙 변경, 계획 없는 결정)만 멈추고 보고한다.
- 측정할 수 없는 것은 미측정으로 표지하고 진행한다. 지어내지 않는다.

## 원칙(저장소 CLAUDE.md 33개가 정본, 작업 전에 읽는다)
- 원칙 8: as-built 엔진의 구조·자리·이름·동작은 근거가 아니다. 엔진 인용은 (1) 엔진 밖 사실 (2) 재작성 범위에만 쓴다. 자리·writer·입력·순서·판정은 원칙에서 유도한다.
- graph 단일 정본(fpga/CLAUDE.md): 계산값은 graph 필드로만, 필드마다 writer 하나, 다른 곳은 READS. 재사용은 graph reuse와 실행 수명 S3 블록 결과 색인 graft 두 길만. 새 cache·memo·dict·sctx 슬롯·결과 객체 값 칸·값 사본 금지(예외는 계획 N3.3·N3.5의 승인 예외). 같은 정의는 필드 하나. 단계 사이 전달은 참조. 정본 자리가 없으면 만들지 말고 멈추고 보고.
- 물리 정합 우선, gm/ID 손계산 방식(SPICE식 정풀이 금지), 물리 경계를 수치 분해능으로 정하지 않음, C 열 사용, DC·AC 분리, 상수 발명 금지, PDK 양은 역할 이름으로(O-197), 회로·소자 이름을 규칙에 쓰지 않음, fail-closed, 만들면 배선.
- as-built 결정 금지: 계획과 다르면 계획부터. 원래 취지와 다른 것은 표지. 승인 사실은 근거가 아니다(O-208).
- topology.json connectivity 수정 금지. 측정 결과와 스크립트는 evidence 폴더에 파일로, 케이스마다 append.

## 안전
- git은 `git -C <절대 경로>`. reset·checkout·stash·push 금지. master에 직접 커밋하지 않는다.
- ⚠ 이 도구의 Bash에서 맨 위 `set -e`는 동작하지 않는다(2026-11-03 실측: `(set -e; false; echo x)`가 x를 출력, 스크립트 실패 뒤 병합까지 진행된 사고). 순서가 중요한 명령은 `&&`로 잇거나 `bash -c 'set -e; ...'`로 돌리고, 파이프는 실패를 가리니 쓰지 않거나 pipefail을 건다.
- 파일 수정은 Edit/Write 또는 Python 바이너리 치환. heredoc append 금지(hook). user_decisions.md는 쓰지 않는다.
- Python = C:\Python314\python.exe(Windows 경로), 출력 PYTHONIOENCODING=utf-8. timeout 명령 금지. rm은 변수에 ${X:?} 가드.
- 커밋 트레일러: --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ". merge는 둘째 -m.
- 메모리: 전체 15.6 GB. LUT를 읽는 측정은 회로마다 프로세스를 나눠 순차로 돌리고, 측정 agent 하나만 무거운 실행을 한다. 여유 2 GB 아래면 중단하고 보고. 장시간 실행은 run_in_background.
- 임시 경로는 agent별 전용(C:/Users/HSLEE/AppData/Local/Temp/la1s_<역할>/). 공용 루트를 지우지 않는다.

## 보고
한글로 짧게: 산출물 경로·커밋, 원칙 근거가 필요한 판단, 멈춤 항목(사용자 몫), 원래 취지와 다른 것, 미측정.
