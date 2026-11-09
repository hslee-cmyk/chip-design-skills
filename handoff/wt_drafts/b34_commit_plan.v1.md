# B34 spec card 커밋 계획 -- `20260930-b34-grammar-explicit`

작성 2026-10-01. 측정 기준: gate `master` `2d58fd8`(작업 시작), 작업 중 `8356c1e`(P10 test·audit, A2 계획 정정)로 움직여 그 트리에서도 다시 확인했다(SD 동일, 인벤토리 159·15·66·4 동일, 이름 충돌 없음).
scratch `C:/g84`만 썼고 끝에 지웠다. 저장소 쓰기·상태 변경 git 없음. 상세 수치는 `draft_b34.final.spec.md` '작성 전 실측' 0과 `b34_revision_log.md` §7.

## 0. 산출물

| 파일 | 내용 |
|---|---|
| `draft_b34.final.spec.md` | 커밋할 spec card(→ `docs/02-design/specs/20260930-b34-grammar-explicit.spec.md`). `parse_spec_card` 통과(phase 2, red-green, gate_change no, approval `20260930-b26-before-phase3`, 절 12개) |
| (생성) interface card | 커밋 직전에 저장소 `tools/gates/interface_card.py`로 만든다. `C:/g84` 모의 생성(8356c1e 사본 루트): 기존 함수 **14개 전부 `stick_diagram`**, 빠진 진입점 0, 엉뚱한 기호 0(아래 3절) |

## 1. 착수 조건(순서 -- `_drafts/user_decisions.md`)

P10 → P10b → Phase 2 DoD → V3 binding(`20260930-v3-exempt-binding`) → V3 scope(`20260930-v3-changed-stmt-scope`) → **B34** → B26-1 → B33.

* 두 V3 card가 gate에 병합되고 정리(worktree·`role/*` 브랜치 삭제)까지 끝나야 한다. design 05 §12: 역할 브랜치가 있는 동안 문서 커밋의 gate push는 EL1이 거부한다.
* B34 'V3 계획'의 판정 규칙은 **N2(넓힌 T6 포함)** 를 전제로 쓴다. 착수 전에 gate 판 `tools/gates/mutate_changed.py`에 범위 card가 들어왔는지 확인한다(아래 4.0의 grep -- 범위 card가 정한 출력 이름 `not_targeted`가 있는지).
  범위 card가 늦어져 현행 규칙(def 전체)으로 돌아도 이 card는 통과한다(55/55 -- card 'V3 계획' 표).
* 승인 기록 `20260930-b26-before-phase3`은 이미 gate에 있다(`2d58fd8`). 이 card는 새 승인 기록이 필요 없다(V3·V7 면제 0, gate_change no).

## 2. 커밋 전에 오케스트레이터가 확인할 것

1. **B26-1 card v4와의 인계 일치.** 이 card는 사이트 10·14를 **B35**로, 9·10b·13·B40(`unavailable_reason` 키)을 B26-1로 적었다(`b26_scripts/b26v4_head.py` mode "v4"와 같은 목록).
   B26-1 card가 v4로 확정되지 않고 사이트 10·14를 다시 가져가면 이 card '의도' 3번·인계 표·결정 3을 되돌린다(코드·계약·V3 수치는 무관 -- docstring 문구의 'B26-1/B35'만).
2. B35 card(아직 없음)를 만들 때 인계 목록 = 사이트 5~8·10·14(+ 블록 뒤 `gain_role_candidates |= cascoded_active_load_legs`). 백로그 기록에 한 줄 남긴다(`.ai/context.md`는 Python 바이너리 append, `git diff --numstat` 삭제 0줄 확인).
3. `references/analog-grammar-integration.md` 폴백 서술 정정(card '작성 전 실측' 7)은 이 card의 문서 커밋 몫이다. spec card 커밋과 같이 해도 되고 병합 뒤 따로 해도 된다.
   고친 뒤 `tests/contracts/test_phase2_stale_refs.py`를 돌린다(P10 계약 5, references 줄마다 Phase 2 삭제·이동 이름 표시 검사).

## 3. interface card 모의 생성 결과(`C:/g84`, 지움)

* `interface_card.build(card, root=8356c1e 사본)`와 CLI `interface_card.py --root <사본> --out <scratch>` 출력이 같았다.
* 표 14행: `load_topology`, `run_topology_pipeline`, `find_stack_edges`, `find_idiom_matches`, `find_differential_and_mirror_forks`, `suggest_vertical_stack_composites`,
  `find_differential_pair_candidates`, `find_verified_differential_and_mirror_relations`, `refine_differential_and_mirror_relations`, `audit_theta_root_direction`,
  `propose_theta_kcl_gap_fill`, `propose_device_roles_gap_fill`, `geometry_colocation_union`, `propose_vertical_stack_id_gap_fill` -- 전부 모듈 `stick_diagram`.
* 계약 절의 백틱 토큰 중 엔진 def 이름과 겹치는 것은 위 14개와 `reachability.build_graph`뿐이고, 후자는 모듈 힌트(`reachability`)가 엔진 모듈이 아니라 표에 실리지 않는다.
  `snap`·`norm`·`insert`·`kind`·`note` 등 흔한 이름은 엔진 def와 겹치지 않는다. SR 함수는 표에 없다(계약 머리의 '부재 상태에서 SR 함수 금지' 의도대로).
* 실제 생성은 커밋 시점 저장소 판(docstring은 base 그대로 -- B34 docstring 정정은 code-author 몫이라 interface card에는 지금 docstring이 실린다. design 05 §12 순서대로 정상).

## 4. 명령 시퀀스(오케스트레이터, MSYS bash)

```bash
set -euo pipefail
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt
DR=$W/_drafts
PY="/c/Python314/python.exe -B"
ID=20260930-b34-grammar-explicit
```

### 4.0 착수 전 확인

```bash
git -C "$R" fetch gate
test "$(git -C "$R" rev-parse --abbrev-ref HEAD)" = master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
test -z "$(git -C "$R" branch --list 'role/*')"
test -z "$(git -C "$R" status --porcelain -- docs/02-design/specs/ .ai/approvals/)"
test -f "$R/.ai/approvals/20260930-b26-before-phase3.md"
git -C "$R" show gate/master:tools/gates/mutate_changed.py | grep -c not_targeted     # 1 이상 = 범위 card 병합됨(0이면 1절 확인)
test ! -e "$R/docs/02-design/specs/$ID.spec.md"
# 사실 재확인(SD가 2d58fd8 뒤 바뀌었으면 card 줄 번호를 다시 잰다 -- 출력이 비어야 한다)
git -C "$R" diff --stat 2d58fd8 HEAD -- skills/analog-gmid-design/assets/stick_diagram.py skills/analog-gmid-design/assets/sizing_recipe.py install.py skills/analog-gmid-design/references/analog-grammar-integration.md
```

### 4.1 spec card + interface card 커밋

```bash
cp "$DR/draft_b34.final.spec.md" "$R/docs/02-design/specs/$ID.spec.md"
(cd "$R" && $PY -P -c "import sys;sys.path.insert(0,'tools/gates');import role_paths as rp;c=rp.parse_spec_card(open('docs/02-design/specs/$ID.spec.md',encoding='utf-8').read(),'$ID');print(c['phase'],c['evidence_type'],c['gate_change'],c['approval'],len(c['sections']))")
#   -> 2 red-green no ['20260930-b26-before-phase3'] 12
(cd "$R" && $PY tools/gates/interface_card.py "docs/02-design/specs/$ID.spec.md" --root . --out "docs/02-design/specs/$ID.interface.md")
#   -> "기존 함수 14개"
grep -c '^| `stick_diagram` |' "$R/docs/02-design/specs/$ID.interface.md"     # 14
grep '^| `' "$R/docs/02-design/specs/$ID.interface.md" | grep -vc '^| `stick_diagram` |' || true   # 0
git -C "$R" add -- "docs/02-design/specs/$ID.spec.md" "docs/02-design/specs/$ID.interface.md"
git -C "$R" commit --trailer "Role: doc" --trailer "Change-Id: $ID" -m "docs: B34 spec card $ID(analog-grammar 부재 시 조용한 None/[]/unavailable_reason 폴백 -> 탐색 경로와 원인을 담은 ImportError, 바뀌는 def 4개, red-green, 승인 20260930-b26-before-phase3) + interface card"
```

(선례 `b8d4c4d`는 `Role: doc`·`Change-Id` 트레일러 둘을 달았다. 메시지 끝 `Co-Authored-By` 줄은 세션 규칙대로.)

### 4.2 push -- 단독 실행, 전체 출력 확인(병렬·`tail` 금지)

```bash
git -C "$R" push gate master:master
git -C "$R" fetch gate
git -C "$R" merge --ff-only gate/master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
```

### 4.3 test worktree(design 05 §12 순서 1)

```bash
git -C "$R" worktree add "$W/$ID-test" -b "role/test/$ID" gate/master
```

이어서 §12 순서 2~8: gmid-test-author(입력 = spec card + interface card, 새 파일 `A/tests/contracts/test_b34_grammar_explicit.py`, def 이름 규칙 `_b34_`/`test_b34_`)
→ auditor freeze(red 확인: base에서 계약 1·2·3이 `Failed`/`AssertionError`, 인벤토리 159·15·66·4 + k 확인 -- card 'V3 계획')
→ code worktree → gmid-code-author(SD 사이트 1·2·3·11·11b + docstring·주석, SR docstring) → 병합 → auditor 판정(V3 N2 대상 10개) → `push gate role/audit/$ID:master` → 정리.

## 5. 사용자 작업(별도, card 밖)

**`install.py` `SKILLS`에 `"analog-grammar"`를 더한다**(27~29행, 지금 `analog-gmid-design`만 있고 `analog-grammar`는 없다).
쓰기 경로 N3.12.2 `사용자 | install.py`라서 오케스트레이터·역할 agent가 고치지 않는다. B34 병합 뒤에는 이 편집이 없으면 설치본이 조용히 틀리는 대신
`load_topology` 등에서 `ImportError`("analog-grammar" + 탐색 경로)로 멈춘다. 병합 보고 때 사용자에게 이 한 건을 알린다.
