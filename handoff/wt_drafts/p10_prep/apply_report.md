# P10 문서 커밋 적용 도구 -- 시험 보고 (2026-09-30)

대상 card: `20260930-p10-df23-inventory` (정본 입력 `_drafts/draft_p10_b22.reviewed.spec.md`, `_drafts/draft_p10b.reviewed.spec.md` '결정 필요 항목', `_drafts/review_p10_p10b.md`,
`_drafts/p10_reconcile_log.md`, `p10_prep/b22_lines.md`). 도구: `p10_prep/apply_p10_doc_commit.py`. 이 보고의 수치는 오케스트레이터 준비 사실이다(판정 기록·보고 수치의 증거 아님 -- spec oracle 절).

## 1. 도구가 하는 일

`python -B apply_p10_doc_commit.py --repo <작업 트리> --commit <C> [--dry-run] [--json-diff] [--allow-line-shift]`

| # | 내용 | spec 근거 |
|---|---|---|
| 1 | `regen_df23.py --repo <R> --commit C --prev-measured-at 1e2e243`(C의 blob만 읽음)로 `df23_inventory.json` 재생성, `measured_at == C` 확인 | '결정 필요 항목' 둘째 점, 계약 1·7 (e)·8 |
| 1b | 생성기를 같은 폴더에 `mk_df23_inventory.py`로 복사(바이트 동일, sha256 `b4a75e92…` 고정 -- reconcile 판이 아니면 거부) | 같은 점("`mk_tables.py` 선례처럼 … 커밋") |
| 2 | 참조 문서 19줄 표시(`b22_lines.md` 문안 그대로, 편집 1~19) | 계약 5 |
| 3 | `probe-df23-summary.md` §B 제목 바로 아래 표지 한 줄(편집 20) | '결정 필요 항목' 셋째 점 |
| 4 | design 20 §8 P10 행 정정(편집 21), P10b 행 추가(편집 22, P10b 문안 그대로), §11-1 정정(편집 23) | 넷째 점, P10b '결정 필요 항목' 둘째 점 |

* 전제 점검(실패 = exit 2, 아무것도 쓰지 않음): `HEAD == C`(문서 커밋의 부모 = `measured_at`), 작업 트리의 `A/*.py`·`run_harness.py`·`A/library`가 C와 같음, 생성기 sha256.
  도구 밖 변경·미추적 파일은 경고만 한다(문서 커밋에 넣지 말 것 -- 작업 저장소에는 `.bkit/**` 등 미추적 파일이 늘 있다).
* 편집마다 옛 줄 전체 문자열로 고정: (옛 1·새 0) → 적용, (옛 0·새 1) → 적용됨(건너뜀), 그 밖 → exit 2. 줄 번호도 C 실측값(같은 파일 앞 삽입분 보정)과 같아야 한다.
* 모든 편집을 메모리에서 계산·대조한 뒤에만 쓴다. 바이트로 읽고 UTF-8 strict, 줄마다 원래 줄 끝 보존(새 줄은 우세 줄 끝), BOM 보존, 표준 밖 줄 끝(`\r` 단독 등)·비UTF-8은 거부.
  목록 JSON은 기존 작업 트리 파일의 줄 끝 방식으로 쓴다(생성기 출력은 LF).
* `--dry-run`: 쓰지 않고 파일별 unified diff(JSON·생성기는 요약, `--json-diff`면 전체) + 편집별 상태.

## 2. 시험 (격리 복제본 `C:/g50`, 끝나고 삭제)

복제: 작업 저장소 `master`(= gate master `7535799`, P9 spec card 커밋)에서 `git clone --no-hardlinks --no-local`, origin 제거. (gate bare 경로를 인자로 쓰면 role_guard가 EL1로 막아 작업 저장소에서 복제했다 -- 두 머리가 같음.)
전역 `core.autocrlf=true`라 새 복제본 작업 트리는 전부 CRLF(색인 LF) -- CRLF 보존 시험이 된다. LF 시험은 `-c core.autocrlf=false` 두 번째 복제본.

| 시험 | 결과 |
|---|---|
| dry-run (C = 7535799, CRLF 트리) | exit 0, 바뀔 파일 11개(아래 표), 편집 23개 전부 `applied` |
| 적용 | exit 0, 11개 파일. `git diff --numstat`는 편집한 줄만(표 3절) -- CRLF 트리에서 줄 끝 변화로 인한 전 파일 diff 없음 |
| 멱등 | 두 번째 적용: 23개 전부 `already`, 바뀐 파일 0. 이어서 dry-run: 바뀔 파일 0 |
| LF 트리(autocrlf=false) 적용 | 11개 파일 모두 LF 유지(CR 0). 결과 blob(`git hash-object`)이 CRLF 트리 커밋의 blob과 11개 모두 같다 |
| 거부: HEAD ≠ C | exit 2 "HEAD != C … 문서 커밋의 부모가 measured_at(C)이어야 한다", 쓰기 없음 |
| 거부: 대상 줄 변조(38행 한 칸) | exit 2 "편집 2 … 옛 줄 0번·새 줄 0번", 트리 해시 전후 같음(쓰기 없음) |
| 거부: 엔진 파일 변경(`sizing_recipe.py` 끝 한 줄) | exit 2 "엔진·library 경로가 C와 다르다" |
| 단위(TextFile/apply_edit) | BOM+혼합 줄 끝+끝 줄 바꿈 없음 왕복 바이트 동일, 적용/적용됨, 끝 줄 뒤 삽입이 '끝 줄 바꿈 없음'을 유지, 중복 옛 줄 거부, `\r` 단독·비UTF-8 거부 |
| 편집한 예제 코드 블록(`stick-diagram-euler-layout.md` 1063-1107 ```python) | 편집 뒤 `ast.parse` OK(편집 전도 OK) -- 1065 import에서 이름을 빼고 1102 호출을 주석으로 |
| 재생성 목록 vs 준비 후보(`df23_inventory.candidate.json`, cd64170) | 다른 최상위 키는 `measured_at`뿐(7535799까지 엔진·계획·library 불변) |

### dry-run diff 통계 (C = 7535799)

| 파일 | difflib +/- | git numstat +/- | 줄 끝(작업 트리) |
|---|---|---|---|
| `docs/03-analysis/…-20-dead-code-dup/df23_inventory.json` | +9989 −9774 | +4319 −4104 | CRLF 트리 CRLF / LF 트리 LF |
| `…/mk_df23_inventory.py` (새 파일) | +791 | +791 | 생성기 바이트 그대로(LF) |
| `references/function-selection-map.md` | +4 −4 | +4 −4 | 보존 |
| `references/sky130-worked-example.md` | +2 −2 | +2 −2 | 보존 |
| `references/stick-diagram-euler-layout.md` | +6 −6 | +6 −6 | 보존 |
| `references/design-report-spec.md` | +2 −2 | +2 −2 | 보존 |
| `references/consistency-map.md` | +2 −2 | +2 −2 | 보존 |
| `references/known-incidents.md` | +2 −2 | +2 −2 | 보존 |
| `SKILL.md` | +1 −1 | +1 −1 | 보존 |
| `…/probe-df23-summary.md` | +1 | +1 | 보존 |
| `design 20` | +3 −2 | +3 −2 | 보존 |

재생성 목록(7535799): 515항목(메시지뿐 302·동작을 정함 213), `by_phase` 해당 없음 317·`4` 63·`3` 61·`7b` 46·`7a` 27·`6b` 1, LF sha256 `41a28d9c…4c43`.
(실제 C는 P9 병합·판정 기록 뒤라 SR 줄 번호가 움직여 목록 값·sha가 달라진다 -- 계약은 값에 묶이지 않는다.)

## 3. 계약 점검 (spec 문장에서 새로 쓴 독립 판정기, scratch `C:/g50/verify_contracts.py` -- 생성기·`check_contracts.py`와 코드 공유 없음)

정본 파서 사용: 계약 2 닫힌 집합 = `merge_gate.read_plan_tables_text(...).phase_order`의 `2` 뒤 + `해당 없음`, 계약 3 = `role_paths.read_section_table(plan, "### N5.2 ")` + `merge_gate.plan_phase_tokens` 괄호 밖 − {`2`}, 레일 R = library `supply_nets` 합집합.

| 대상 | 계약 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| 시뮬레이션 card base S(문서 커밋 D + spec/interface card 커밋) | PASS | PASS | PASS | PASS | PASS (대상 (줄, 이름) 20건 모두 표시) |
| `measured_at` = C = 7535799 (계약 8 거부 모양) | FAIL 416(`measured_at` 없음, 빈 `function`) | FAIL 1874(`phase` 없음) | FAIL 184 | FAIL 1(`by_phase`) | FAIL 20(19줄) |

* R = {agnd, gnd, vdd, vss}(library 10파일, `_TEMPLATE` 선언 없음).
* 계약 6: `git diff --name-only C S`에서 card 두 파일을 빼면 11경로 -- 모두 `docs/03-analysis/…-20-dead-code-dup/**`·`docs/02-design/**`·`references/**`·`SKILL.md` 안.
* 계약 7 (e): `git diff --name-only C S -- A/*.py workspaces/run_harness.py` = 0줄. D^ = C 확인.
* 쓰기 경로: `role_paths.allowed("오케스트레이터", <경로>, …)` -- 11경로 + spec/interface card 두 경로 모두 허용(`docs/03-analysis/**`·`docs/02-design/**`·`skills/analog-gmid-design/references/**`·`SKILL.md` 행).
* spec card: `role_paths.parse_spec_card` 통과(test-only / gate_change no / approval `20260923-20-dead-code-dup-design`, phase 2). `interface_card.py` → 기존 함수 0개, 신규 시그니처 0행(리뷰 M2와 같음).
* 참고 실행(증거 아님): `check_contracts.py <목록> --repo <R> --base S --docs` → 1·2·3·4·7a~7d·5 PASS.
* 문서·목록을 읽는 기존 test/도구: `git grep`(tests·tools/gates·workspaces) 0건 → 기존 test 영향 없음(pytest는 시스템 Python에 없어 실행하지 않았다).
* 복제본 commit-msg hook 시험은 불가: 무결성 대조가 `remote.gate.url`·`.claude/hooks` 부재로 EL3 차단(복제본 `.git` 안 표지뿐, 복제본과 함께 삭제). 트레일러 모양은 선례(`7535799`, `2140da8`)대로 했다.

## 4. 오케스트레이터 명령 순서

순서 조정(과제의 두 요구 -- "spec card 커밋은 test worktree보다 앞", "`measured_at` = 문서 커밋의 부모"): **문서 커밋 D를 C 바로 위에 먼저, 그 위에 spec card·interface card 커밋 S**,
둘을 한 번에 push한 뒤 test worktree. 이렇게 하면 D^ = C = `measured_at`이 성립하고(계약 8), spec card는 test worktree(= gate master S)보다 앞이며, 문서 커밋은 정확히 하나다.
(S를 먼저 두면 목록을 S에서 재생성해야 한다 -- 가능하지만 spec '결정 필요 항목'의 "C(문서 커밋 직전)에서 생성" 문장과 맞추려면 D 먼저가 간단하다. 두 경우 모두 엔진 blob은 같다.)

전제: P9 `20260930-p9-kcl-edges` 판정 기록이 gate master에 있고 `role/*/20260930-p9-kcl-edges` 브랜치가 모두 정리됨(있으면 EL1이 문서 push를 거부 -- 리뷰 S6). 경로 변수:
`W=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, `P=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p10_prep`, `ID=20260930-p10-df23-inventory`.

```bash
# 0. C 확정 (메인 worktree)
git -C $W fetch gate
git -C $W branch -a --list 'role/*'                  # 비어 있어야 한다
git -C $W merge --ff-only gate/master
C=$(git -C $W rev-parse HEAD); echo $C                # = gate/master, P9 판정 기록 포함
git -C $W log -1 --format='%B' $C                     # Role: audit / Change-Id: 20260930-p9-kcl-edges 확인
git -C $W status --porcelain --untracked-files=no -- docs skills workspaces   # 비어 있어야 한다
#   (미추적 `skills/analog-gmid-design/assets/*.zip`·`workspaces/current-reuse-…-report/*`·`.bkit/**`는 도구가 경고만 한다 -- add 목록이 경로를 지정하므로 섞이지 않는다)

# 1. 미리 보기 -> 적용 -> 멱등 확인
C:/Python314/python.exe -B $P/apply_p10_doc_commit.py --repo $W --commit $C --dry-run
#   줄 번호 불일치로 멈추면: 그 파일이 C에서 바뀐 것이다(P9 병합의 design 20 기록 등). diff를 보고 옛 줄이 그대로면 --allow-line-shift로 다시.
C:/Python314/python.exe -B $P/apply_p10_doc_commit.py --repo $W --commit $C
C:/Python314/python.exe -B $P/apply_p10_doc_commit.py --repo $W --commit $C --dry-run   # "바뀔 파일 0개"

# 2. 사전 점검(오케스트레이터 전용, 증거 아님)
C:/Python314/python.exe -B $P/check_contracts.py $W/docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json --repo $W --base $C
#   (--docs 판정은 D 커밋 뒤 --base D로: 계약 5 PASS)

# 3. 문서 커밋 D (정확히 하나, 부모 = C)
D3=docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup
git -C $W add -- $D3/df23_inventory.json $D3/mk_df23_inventory.py $D3/probe-df23-summary.md \
  docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md \
  skills/analog-gmid-design/SKILL.md skills/analog-gmid-design/references
git -C $W diff --cached --name-only                   # 정확히 11경로
git -C $W commit -m "docs: P10 문서 커밋 $ID(df23_inventory.json 재측정 measured_at=${C:0:7}, 생성기 mk_df23_inventory.py, 참조 문서 19줄 Phase 2 삭제·이동 표시(문서 백로그 B22 (b)), probe-df23-summary §B 표지, design 20 §8 P10 행 정정·P10b 행 추가·§11-1 정정)" \
  --trailer "Role: doc" --trailer "Change-Id: $ID" \
  --trailer "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
D=$(git -C $W rev-parse HEAD); test "$(git -C $W rev-parse $D^)" = "$C" && echo "D^ = C OK"
C:/Python314/python.exe -B $P/check_contracts.py $W/$D3/df23_inventory.json --repo $W --base $D --docs   # 계약 5 PASS

# 4. spec card + interface card 커밋 S
cp C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/draft_p10_b22.reviewed.spec.md $W/docs/02-design/specs/$ID.spec.md
(cd $W/tools/gates && C:/Python314/python.exe -B interface_card.py $W/docs/02-design/specs/$ID.spec.md --root $W --out $W/docs/02-design/specs/$ID.interface.md)
#   기대: "기존 함수 0개"
git -C $W add -- docs/02-design/specs/$ID.spec.md docs/02-design/specs/$ID.interface.md
git -C $W commit -m "docs: P10 spec card $ID(DF-23 전수 목록 재측정·담당 Phase, 참조 문서 Phase 2 이름 표시, test-only) + interface card" \
  --trailer "Role: doc" --trailer "Change-Id: $ID" \
  --trailer "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"

# 5. push (단독 실행, 전체 출력 확인 -- 병렬·tail 금지)
git -C $W push gate master
git -C $W rev-parse gate/master HEAD                  # 같아야 한다

# 6. 그 뒤 N3.12.3 순서 2: gate/master(= S)에서 test worktree <W>/$ID-test (role/test/$ID)
```

auditor 브리핑에 넣을 값: `measured_at` = C, 문서 커밋 = D(`git rev-parse D^` = C, 계약 8), card base old = S(또는 그 뒤 test worktree 생성 시 gate master).

## 5. spec 불일치·판단 (오케스트레이터 확인 필요)

1. **'card base가 될 C(문서 커밋 직전)'라는 말**: reviewed spec '결정 필요 항목' 둘째 점은 C를 "card base가 될 gate master 머리"라 부르지만, D·S를 C 위에 올리면 card base(old)는 S다.
   `measured_at` = C = D^만 참이다. 엔진 blob이 같아(계약 7 (e)) 판정에 영향은 없고 '순서' 단락(40행 "그 부모가 `measured_at`")과는 맞다 -- 표현만 모호. 다음 정정 때 "C = `measured_at`(문서 커밋의 부모)"로 줄이는 것을 권한다.
2. **design §11-1 꼬리**: spec은 굵은 구절 "63건에 DF 번호가 없다"의 교체만 적고 같은 줄 끝 "→ DF 신설 요청(담당 Phase 4, …)"은 말하지 않는다. 그대로 두면 한 줄 안에서 모순이라
   꼬리를 "→ 새 DF 없이 DF-19·DF-26 교체(담당 Phase 4, MG1 레일 이름 변경과 같은 자리)에서 다룬다."로 바꾸고 옛 문장을 괄호 안에 인용해 보존했다(편집 23 -- 원치 않으면 그 한 항목의 `new`만 고치면 된다).
   §11 머리 문장(228행 "다음 두 가지는 **계획서 개정 요청**으로 올린다")은 손대지 않았다 -- 1번이 더는 개정 요청이 아니므로 이것도 고칠지 판단 필요(사실 정정 범위).
3. **design §8 P10 행 문안**: spec은 교체할 구절 셋만 주고 완성 문장은 주지 않는다. 글자 그대로 치환하면 문장이 깨져("…문서화(card base 재측정(`measured_at`))와 레지스트리 기록은 별도 card…, card base 재측정의 담당 Phase 배정")
   다음 문장으로 썼다: "DF-23 전수 목록 문서화(card base 재측정(`measured_at`))와 항목마다 담당 Phase 배정, 참조 문서의 Phase 2 삭제·이동 이름 표시(문서 백로그 B22 (b)). 레지스트리 기록은 별도 card(code 경로 -- 아래 행) (2026-09-30 정정, spec card `20260930-p10-df23-inventory`)"
   -- '(2026-09-30 정정, spec card …)'는 P7·P9 행 선례 표기. '참조 문서 … 표시'는 이 card 계약 5 산출이라 넣었다(없애도 됨). 산출물 칸 '목록'은 그대로.
4. **§B 표지 문안**: spec 인용 문장("… 항목마다 `phase`)")에 문장 끝 마침표만 더했다. 위치는 제목 바로 다음 줄(한 줄 추가, 빈 줄 추가 없음 -- CommonMark에서 제목 뒤 문단으로 보인다).
5. **과제 목록 (1)~(4)에 없는 산출물**: spec은 생성기 `mk_df23_inventory.py`를 같은 문서 커밋에 넣으라고 한다 -- 도구가 넣는다(바이트 동일이라 docstring의 `regen_df23.py`·'준비용' 표기가 남는다. sha 고정을 위해 고치지 않았다.
   고치려면 복사 뒤 별도 편집하고 `GEN_SHA256`이 아니라 새 파일 sha를 판정 기록 측에 알릴 것).
6. **P9 뒤 C**: P9는 `sizing_recipe.py`의 `kcl_series_union` 본문을 바꾸므로 실제 C에서 목록의 줄 번호·일부 항목이 이 시험(7535799)과 달라진다. 계약은 값에 묶이지 않고,
   도구의 문서 편집 대상(references·SKILL.md·summary·design 20)은 P9가 바꾸지 않는 한 그대로다. P9 완료 기록이 design 20에 줄을 더하면 편집 21~23이 줄 번호 불일치로 멈춘다 → dry-run diff 확인 뒤 `--allow-line-shift`.
7. **리뷰 문서와 사실 일치 확인**: reviewed spec 계약 5의 19줄·고정 분류, 1c 어휘 정의, R, `phase_order`는 7535799에서도 그대로(독립 판정기 결과). 새 불일치 없음.

## 6. 파일

* 도구: `p10_prep/apply_p10_doc_commit.py`(이 보고와 같은 폴더, 커밋하지 않음 -- 오케스트레이터 준비 도구).
* scratch `C:/g50`(복제본 2개, `verify_contracts.py`, dry-run 출력) -- 삭제함.
