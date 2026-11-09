# B34 spec card 커밋 계획 -- `20260930-b34-grammar-explicit` (v2)

작성 2026-10-01. v1(`b34_commit_plan.v1.md`, 측정 `2d58fd8`/`8356c1e`)을 gate `master` **`0f23786`** 에서 다시 쟀다(scratch `C:/g123`, 격리 복제본, 끝에 삭제).
v1 대비 바뀐 것: (1) 명령을 전부 절대 경로로(이 세션 hook `role_guard.py`가 `(cd … && …)`와 `cd` 뒤 상대 경로 쓰기를 거부한다) (2) references 문서 커밋을 패치 스크립트로(`b34_kit/patch_b34_refs.py`)
(3) phase 질문(Q-B34-PHASE)의 답에 따라 갈리는 단계 표시 (4) 사용자 `install.py` 작업 절차를 게이트 규칙(`Role: user` + staged_diff 승인 기록)대로 구체화 (5) 착수 조건의 지금 상태.
상세 수치: `draft_b34.final.spec.md` '작성 전 실측' 00, 브리프 `b34_briefs.md`.

## 0. 산출물

| 파일 | 내용 |
|---|---|
| `draft_b34.final.spec.md` | 커밋할 spec card(→ `docs/02-design/specs/20260930-b34-grammar-explicit.spec.md`). 직전판 `draft_b34.final.spec.v1.md`. `parse_spec_card` 통과(phase 2, red-green, gate_change no, approval `20260930-b26-before-phase3`, 절 12개) |
| (생성) interface card | 커밋 직전에 저장소 `tools/gates/interface_card.py`로 만든다. `0f23786` 모의: 기존 함수 **14개 전부 `stick_diagram`**, 계약 1 진입점과 같음 |
| `b34_kit/patch_b34_refs.py` | references 문서 폴백 서술 정정(앵커 5개, `--check`/적용/멱등, CRLF 작업 사본 대응) |
| `b34_kit/sim_b34.py` | 이 계획 §4의 모의(격리 복제본 + 가짜 bare gate). `0f23786` 결과 NG 0(`b34_kit/out/sim_b34.txt`) |

## 1. 착수 조건(순서 -- `_drafts/user_decisions.md` 14행)

P10b → Phase 2 DoD → V3 면제 묶기(34) → V3 범위(35) → **B34** → B26-1(앞선 test 보강 card 포함) → B33 → Phase 3.

| 조건 | `0f23786` 상태 | 확인 명령(§4.0) |
|---|---|---|
| 두 V3 card 병합·정리 | 미충족 -- gate 판 `mutate_changed.py`에 `not_targeted` 0개(범위 card 미병합) | `git show gate/master:tools/gates/mutate_changed.py \| grep -c not_targeted` ≥ 1 |
| `role/*` 브랜치 0 | 미충족 -- `role/{audit,code,test}/20260930-df23-registry-record` 3개(P10b 진행 중). design 05 §12: 역할 브랜치가 있는 동안 문서 커밋 gate push는 EL1 거부 | `git branch --list 'role/*'` 빈 출력 |
| 승인 기록 `20260930-b26-before-phase3` | 충족(`2d58fd8`) | `test -f` |
| **Q-B34-PHASE 답** | **미결** -- 답 전에는 spec card를 커밋하지 않는다(머리 `phase`가 답에 달렸다) | 사용자 답 기록(`_drafts/user_decisions.md`) |
| 사용자 `install.py` 편집 | **착수 조건 아님**(§5) | -- |

범위 card가 늦어져 현행 규칙(def 전체)으로 돌아도 이 card는 통과하도록 설계했다(55/55 -- card 'V3 계획').

## 2. 커밋 전에 오케스트레이터가 확인할 것

1. **B26-1 card와의 인계 일치**: `draft_b26_1.spec.md`(v4) 52행 "사이트 10·14(B35)" -- 이 card의 인계 표와 같다(`0f23786` 시점 확인). B26-1 card가 다시 10·14를 가져가면 이 card '의도' 3번·인계 표·결정 3의 'B26-1/B35' 문구만 되돌린다.
2. B35 card(아직 없음) 인계 목록 = 사이트 5~8·10·14(+ 블록 뒤 `gain_role_candidates |= cascoded_active_load_legs`). 백로그 기록 한 줄(`.ai/context.md`는 Python 바이너리 append, `git diff --numstat` 삭제 0줄 확인).
3. Phase 질문 답이 (가) `phase: 3`이면: spec card 머리 `phase: 3` + `approval: <새 decision 기록 id>` 줄 추가, 새 decision 승인 기록(사용자 원문 = 답 그대로)을 spec card보다 **먼저 또는 같이** 커밋. 브리프의 `--gmid-phase=2`를 전부 `3`으로.
   답이 (나) 'Phase 2 DoD 앞'이면 머리 그대로, 순서를 P10b → B34 → B26-1 → Phase 2 DoD로 바꾼 기록(`user_decisions.md`)과 Phase 2 DoD 브리프의 N6.3 2·5번 목록 수정(이 card를 phase 2 red-green 목록에 넣음)이 필요하다.

## 3. interface card 모의 생성 결과(`C:/g123/seq_P2`, 지움)

* 절대 경로 호출 `interface_card.py <seq>/docs/02-design/specs/<id>.spec.md --root <seq> --out <seq>/docs/02-design/specs/<id>.interface.md` → "기존 함수 14개".
* 표 14행 전부 `stick_diagram`: `load_topology`, `run_topology_pipeline`, `find_stack_edges`, `find_idiom_matches`, `find_differential_and_mirror_forks`, `suggest_vertical_stack_composites`,
  `find_differential_pair_candidates`, `find_verified_differential_and_mirror_relations`, `refine_differential_and_mirror_relations`, `audit_theta_root_direction`,
  `propose_theta_kcl_gap_fill`, `propose_device_roles_gap_fill`, `geometry_colocation_union`, `propose_vertical_stack_id_gap_fill`. `phase: 3` 변형도 같다.
* docstring은 커밋 시점 저장소 판(base) 그대로 실린다 -- B34 docstring 정정은 code-author 몫(design 05 §12 순서대로 정상).

## 4. 명령 시퀀스(오케스트레이터, MSYS bash -- 절대 경로만, `cd` 금지)

```bash
set -euo pipefail
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt
DR=$W/_drafts
PY=/c/Python314/python.exe
ID=20260930-b34-grammar-explicit
```

### 4.0 착수 전 확인

```bash
git -C "$R" fetch gate
test "$(git -C "$R" rev-parse --abbrev-ref HEAD)" = master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
test -z "$(git -C "$R" branch --list 'role/*')"
test -z "$(git -C "$R" status --porcelain -- docs/02-design/specs/ .ai/approvals/ skills/analog-gmid-design/references/)"
test -f "$R/.ai/approvals/20260930-b26-before-phase3.md"
git -C "$R" show gate/master:tools/gates/mutate_changed.py | grep -c not_targeted     # 1 이상 = 범위 card 병합됨
test ! -e "$R/docs/02-design/specs/$ID.spec.md"
# 사실 재확인 -- 출력이 비어야 card 줄 번호가 유효(아니면 b34_kit/dump_lines.py·measure_b34.py로 다시 잰다)
git -C "$R" diff --stat 2d58fd8 HEAD -- skills/analog-gmid-design/assets/stick_diagram.py skills/analog-gmid-design/assets/sizing_recipe.py install.py skills/analog-gmid-design/references/analog-grammar-integration.md
```

(4.0의 마지막 명령이 비지 않으면 -- 예: B26-1이 먼저 들어오는 순서 변경 -- `b34_kit/mk_head.py`의 base 커밋을 그 판으로 바꿔 `measure_b34.py`·`dump_lines.py`를 다시 돌리고 card '작성 전 실측' 00을 갱신한다.)

### 4.1 (phase 답이 (가)일 때만) decision 승인 기록

오케스트레이터가 `.ai/approvals/<새 id>.md`를 쓴다(머리 `target_kind: decision`, `target: <결정 이름>`, `scope:`에 B34·B26-1·b26pre card `phase: 3`과 'Phase 2 DoD 뒤·Phase 3 M card 전', '사용자 원문' = 답 원문).
`$PY -B -P -c "import sys;sys.path.insert(0,'$R/tools/gates');import merge_gate as mg;print(mg.parse_approval_header(open('$R/.ai/approvals/<새 id>.md','rb').read(),'<새 id>.md'))"` 통과 확인 →
`git -C "$R" add -- .ai/approvals/<새 id>.md` → `git -C "$R" commit --trailer "Role: doc" -m "docs: 승인 기록 <새 id>(…)"`. 옛 기록 `20260930-b26-before-phase3`은 고치지 않는다.

### 4.2 spec card + interface card 커밋

```bash
cp "$DR/draft_b34.final.spec.md" "$R/docs/02-design/specs/$ID.spec.md"
# (가)이면 여기서 머리 두 줄을 고친다: phase: 3, approval: <새 id> 줄 추가 -- Edit 도구로
"$PY" -B -P -c "import sys;sys.path.insert(0,'$R/tools/gates');import role_paths as rp;c=rp.parse_spec_card(open('$R/docs/02-design/specs/$ID.spec.md',encoding='utf-8').read(),'$ID');print(c['phase'],c['evidence_type'],c['gate_change'],c['approval'],len(c['sections']))"
#   -> 2 red-green no ['20260930-b26-before-phase3'] 12      ((가)이면 3 … ['20260930-b26-before-phase3', '<새 id>'] 12)
"$PY" -B "$R/tools/gates/interface_card.py" "$R/docs/02-design/specs/$ID.spec.md" --root "$R" --out "$R/docs/02-design/specs/$ID.interface.md"
#   -> "기존 함수 14개"
grep -c '^| `stick_diagram` |' "$R/docs/02-design/specs/$ID.interface.md"                      # 14
grep '^| `' "$R/docs/02-design/specs/$ID.interface.md" | grep -vc '^| `stick_diagram` |' || true  # 0
git -C "$R" add -- "docs/02-design/specs/$ID.spec.md" "docs/02-design/specs/$ID.interface.md"
git -C "$R" commit --trailer "Role: doc" --trailer "Change-Id: $ID" -m "docs: B34 spec card $ID(analog-grammar 부재 시 조용한 None/[]/unavailable_reason 폴백 -> 탐색 경로와 원인을 담은 ImportError, 바뀌는 def 4개, red-green, 승인 20260930-b26-before-phase3) + interface card"
```

### 4.3 references 문서 커밋(같은 push에 넣어도 되고 병합 뒤 따로 해도 된다)

```bash
"$PY" -B "$DR/b34_kit/patch_b34_refs.py" --root "$R" --check      # pending 5 (무쓰기)
"$PY" -B "$DR/b34_kit/patch_b34_refs.py" --root "$R"              # applied
git -C "$R" diff --numstat -- skills/analog-gmid-design/references/analog-grammar-integration.md   # 17 16 (0f23786 모의)
"$PY" -B "$DR/b34_kit/patch_b34_refs.py" --root "$R"              # already-applied
PYTHONDONTWRITEBYTECODE=1 "$PY" -B -P -m pytest -c "$R/tools/gates/pytest_gate.ini" --rootdir="$R" --confcutdir="$R" -q -p no:cacheprovider --gmid-phase=2 --gmid-strict= "$R/skills/analog-gmid-design/assets/tests/contracts/test_phase2_stale_refs.py"
#   -> 18 passed ((가)이면 --gmid-phase=3, 결과 같음 -- 모의 확인)
git -C "$R" add -- skills/analog-gmid-design/references/analog-grammar-integration.md
git -C "$R" commit --trailer "Role: doc" --trailer "Change-Id: $ID" -m "docs: B34 references analog-grammar-integration.md 폴백 서술 -> ImportError(95~98·106~107·118~119·186~188·197~198·440~443, gate 소자 없음 줄은 유지)"
```

(패치 문안은 초안이다 -- 커밋 전에 `git -C "$R" diff`로 읽고 고칠 것이 있으면 `patch_b34_refs.py`의 새 문안을 고친다. `pytest`가 이 세션 hook에서 `$R` 안 산출물(`__pycache__`)로 막히면 `PYTHONPYCACHEPREFIX=/c/g<n>/pyc`를 앞에 붙인다.)

### 4.4 push -- 단독 실행, 전체 출력 확인(병렬·`tail` 금지)

```bash
git -C "$R" push gate master:master
git -C "$R" fetch gate
git -C "$R" merge --ff-only gate/master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
```

### 4.5 test worktree(design 05 §12 순서 1)와 이후

```bash
git -C "$R" worktree add "$W/$ID-test" -b "role/test/$ID" gate/master
```

이어서 §12 순서 2~8: `b34_briefs.md` 1절(test-author) → 3.1(auditor freeze) → 순서 4 code worktree(`git -C "$R" worktree add "$W/$ID-code" -b "role/code/$ID" <T>`) → 2절(code-author) → 순서 6 병합
→ 3.2·3.3(auditor 판정) → `git -C "$W/$ID-audit" push gate role/audit/$ID:master`(단독) → 정리(worktree·`role/*` 삭제는 push 결과 확인 뒤).

## 5. 사용자 작업(별도, card 밖 -- B34 착수 조건 아님)

**무엇**: `install.py` 29행 `SKILLS` 끝에 `"analog-grammar"`를 더한다(`… "solution-capture", "analog-gmid-design", "analog-grammar"]`).
**왜 card 밖인가**: 쓰기 경로 N3.12.2 `사용자 | install.py`(계획 645행) -- 오케스트레이터·역할 agent는 쓰지 못한다(EL1). 승인 기록 `20260930-b26-before-phase3` '덮지 않는 것'도 별도 사용자 작업으로 적었다.
**착수 전에 필요한가**: 아니다. card test·auditor 판정은 저장소 트리(analog-grammar 있음)에서 돌고 부재는 `sys.modules`로 흉내 낸다. 사용자 전역 설치(`~/.claude/skills`)에는 지금 두 skill이 모두 없어(`0f23786` 시점 확인)
병합 즉시 깨지는 설치본도 없다. 필요한 시점 = **B34 병합 뒤 다음 `python install.py`(또는 `--only skills`) 실행 전**. 편집 없이 설치하면 설치본의 `load_topology` 등이 `ImportError`("analog-grammar" + 탐색 경로)로 멈춘다(설치 모양 사본 실측 9/9).
**게이트 절차(선례 `d72475a`)**: 한 커밋에 install.py 변경 + 새 승인 기록 `.ai/approvals/<id>.md`(`target_kind: staged_diff`, `target` = HEAD→staged install.py 변경의 `merge_gate.compute_diff_hash`, `diff_base` = HEAD, `diff_path: install.py`, '사용자 원문').
승인 기록 파일은 오케스트레이터가 쓰고(사용자 원문 = 사용자 지시), install.py 편집·stage·커밋(`--trailer "Role: user"`)은 사용자가 한다. 모의(`sim_b34.py` 사용자 단계): 승인 기록 있으면 가짜 gate 통과, 없으면 `[EL4 거부] target_kind: staged_diff 승인 기록 필요`.
**설치 확인(사용자)**: `python install.py --only skills` 뒤 `~/.claude/skills/analog-grammar/assets/netclass.py`가 있는지. 병합 보고 때 이 한 건을 알린다.
