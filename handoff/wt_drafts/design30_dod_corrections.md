# design 30 §10 DoD 블록 정정 D1~D4 -- 적용 안내 (2026-10-02, 기준 gate `master` `4a286f0`)

근거: 독립 검토 `_drafts/review_phase3_dod.md` §2(S1)·§6(정정 목록). 패치 도구: `_drafts/design30_dod_corrections.py`.
대상: `docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md`(v8.5, UD-0 승인본) §10 bash 블록, 이력 `docs/01-plan/features/gain-budget-gmid-sizing.history.md` H2 표.

## 1. 무엇을 고치나

| # | 줄(`4a286f0`) | 채택 | 내용 | E 통과 기준에 닿나 |
|---|---|---|---|---|
| D1 | 1034 `fresh()` | **필수(S1)** | 검토 §2.1 문안 그대로: `checkout -- .` → `clean -fdx` → `checkout --detach "$1"` → HEAD = `$1^{commit}`·`status --porcelain --ignored` 0줄 단정, 실패 시 `E5 INVALID: 판 전환 실패 <판>` + `return 1` | 아니다. §10 표 E5 문구 "`E5 INVALID` 줄이 없고"가 그대로 FAIL로 만든다(새 기준 없음) |
| D2 | 1036~1038, 1040, 1044 | 채택 | 측정 줄 `fresh "$X"; $PY …` → `fresh "$X" && $PY …`(실패면 `exit=1`이 찍힌다). 단독 줄 `fresh "$P2D"`·`fresh "$H"` → `… \|\| exit 1`(다른 판에서 E-LIB를 재지 않음 -- 뒤 E5 판정 python·E6이 돌지 않아 측정 누락 = PASS 불가) | 아니다. 실패 시 멈추게만 한다 |
| D3 | 1099 E6 | 채택 | `--head HEAD` → `--head "$H"`(1028행 E5 머리에서 정의). 마지막 `fresh "$H"` 성공에 기대지 않는다 | 아니다. 같은 판(H)을 명시할 뿐 |
| D4 | 786·788·789·793 | 채택 | `GC` = H 판 `git archive … tools/gates`를 `<iso>` 밖(또는 `<git-common-dir>/gmid-gate-cache/<H>/`)에 푼 것, PT3의 `<cache>` 두 곳을 `$GC`로 -- 게이트 출처 하나 | 아니다. E0/E2/IMPORT-ANY가 쓰던 `$ISO/tools/gates`는 그 시점 `<iso>` = H라 내용이 같고, PT3는 원래 `<cache>`(05 §4.4)였다. 통과 기준 문구·판정 블록 무변경 |
| H | history H2 표 끝 | 같이 | 정정 경위 한 행(아래 §3) | -- |

모두 줄 단위 교체라 design 줄 수 1397 그대로, 바뀐 줄 = 786·788·789·793·1034·1036·1037·1038·1040·1044·1099(11줄). DoD kit가 바이트 그대로 뽑는 판정 블록 5개(E3_AST·E3B_AST·E5 판정 python·`import_any`·`EXCL`/`MP_ARGS`) 밖이다 -- 도구가 쓰기 전에 단정하고, 모래상자 합성 저장소에서 `extract_design_blocks.py`로 패치 전후 sha256 5개가 같음을 확인했다(§4).
D4를 넣는 이유: 검토 §2.2 -- 정해진 순서에서는 문제가 없지만 단계 순서를 바꾸거나 E5 판 전환이 실패하면 `$ISO/tools/gates`가 P2D 판이 된다(`P2D..4a286f0`에 `tools/gates` 커밋 2개). 실행기 kit는 이미 캐시 방식이다(`run_dod.sh` 30~32행).

design 머리 버전 줄(v8.5 …)은 바꾸지 않는다 -- 계획서·design은 규칙만, 경위는 history(메모리 규칙 '계획서는 design용, 이력은 항상 history 문서', 선례 `58024de`: design 20 §11-1 한 줄 교체 + history H1·H2 행, design 머리 무변경). design 30 머리의 "승인본 = 초안 … 이 줄만 바꿨다"는 저장 시점 사실이고, 그 뒤 정정은 H2 행이 적는다.

## 2. 승인 기록이 필요한가 -- 게이트 실측: **문서 커밋만**(새 승인 기록 불필요, 사용자 질문 불필요)

| 확인 | 근거(`4a286f0` 판 코드 줄) | 결과 |
|---|---|---|
| design 경로 쓰기 권한 | 계획 N3.12.2 624행 `\| 오케스트레이터 \| docs/02-design/** \| docs/02-design/disputes/** \| 없음 \|`, 623행 `docs/01-plan/**` 없음(history 포함). `role_paths.py` 65행 `doc` 분류 | `Role: doc` 커밋이면 조건 '없음' -- 승인 기록 요구 없음 |
| `staged_diff` 승인 요구 조건 | `merge_gate.py` 821행 `if "승인 기록" in pending or role == "user":` -- `pending`은 경로표 조건이 `승인 기록`인 행(topology.json 등, `role_paths.py` 36행 CONTENT_CONDITIONS)에서만 생긴다 | design·history 경로는 해당 없음 |
| 계획 판정 표 | `merge_gate.py` 857행 `if PLAN_PATH in paths:` -- `plan.md`일 때만 `plan_tables` 해시 대조 | history.md·design은 대상 아님(계획서 무변경) |
| UD-0 승인 기록이 design 내용을 묶는가 | `.ai/approvals/20260930-30-module-split-design.md` 머리 = `target_kind: diff`, `diff_base 3e835e0…`, `diff_head 6c8287f…`(고정 커밋 쌍). 게이트는 이 머리를 **파싱만** 한다: `merge_gate.py` 470~481행 `rule6_dates_approvals`(파일 존재 + `parse_approval_header`), `gate_change_ok` 720행~. `diff_base`·`diff_head`를 쓰는 코드는 파서(178·247·262~268행)뿐이고, 기록된 해시를 지금 트리로 다시 계산하는 코드는 없다(`git grep diff_base -- tools/gates` 결과 = 파서 줄만). `target_kind: diff` 해시를 대조하는 곳은 V5(`merge_gate.py` 1219행~, `weakening_diff.py` 215~226행 -- test diff 전용)뿐 | design을 고쳐도 UD-0 기록은 깨지지 않고, 그 해시로 이 편집을 승인할 경로도 없다 |
| design 해시 고정 | `git grep -n -E "design\.md\|a4350dc" -- tools/gates hooks .githooks` = 0줄 | 게이트가 design 30 바이트를 묶는 곳 없음 |
| 원칙(기준 약화만 승인) | 계획 DEC-40(234행) "기준 약화는 매 건 사용자 승인", U-18(1093행). 검토 §2.1 "판정 기준은 그대로 … 원칙상 사용자 승인은 필요 없다" | D1~D4는 약화가 아니다(실행을 실패 시 멈추게 하는 강화·출처 통일). `decision` 기록도 게이트가 요구하지 않는다(`decision`을 읽는 곳은 V3 면제·V7 미도달 면제·test_lint 규칙(1) 면제뿐 -- `mutate_changed.py` 13행, `reachability.py` 7·188행, `test_lint.py` 728행) |

결론: **`Role: doc` 문서 커밋 한 개(design 11줄 + history 1행)로 충분하다. 새 승인 기록 초안은 만들지 않았다**(필요 없는 기록을 만들면 '승인 없이는 못 고친다'는 거짓 선례가 된다). 사용자 질문 불필요.
선례 대조: design 20 §10 E4 정정(`2140da8`·`fe638ab`)은 승인 기록을 받았지만, 그것은 **통과 기준 값 자체**를 바꾼 사용자 결정(A3·D1 -- history H1)이었다. 이번 정정은 기준 문구를 바꾸지 않는다.

## 3. history H2 행 (도구가 `**닫힌 열린 이슈**` 앞 H2 표 끝에 넣는 문안)

| design 30 §10 E5 `fresh()` 판 전환(v8.5 승인본 1034행) | `checkout --detach "$1" && checkout -- . && clean -fdx` 순서였다. 직전 E-INST가 추적 산출물(`workspaces/*/…instance.json`)을 고친 상태에서 두 판의 그 파일이 다르면 `checkout --detach`가 거부되고(rc 1) HEAD가 이전 판에 남는데, 호출부가 `fresh "$X"; $PY …`로 이어 **이전 판에서 측정이 돌아 E-INST '같음'이 나올 수 있었다**(실패해야 할 곳에서 통과). HEAD 확인도 없었다. design 20 §10 E4와 Phase 2 DoD 브리핑 §2의 '지우기 → detach → HEAD 대조 → status 0줄' 순서를 거꾸로 옮긴 것이다. 독립 검토 `_drafts/review_phase3_dod.md` §2.1이 합성 저장소로 재현했다. `5f643a9..4a286f0`에서는 그 파일이 두 판에서 같아 리허설에는 드러나지 않았다 | 2026-10-02 정정 D1(…), D2, D3, D4. §10 표의 통과 기준 문구와 DoD kit가 뽑는 판정 블록 5개(sha256)는 그대로 -- 절차 강화라 승인 기록을 새로 받지 않았다(게이트 근거 …) | design 30 §10 E5·E6 블록 |

(정확한 바이트는 `design30_dod_corrections.py`의 `HIST_ROW`.) 커밋 해시는 행에 넣지 않았다(커밋 전에는 모른다 -- 필요하면 커밋 뒤 `.ai/context.md`에 적는다).

## 4. 적용 절차(오케스트레이터)와 모래상자 확인

```bash
P=C:/Python314/python.exe; T=_drafts/design30_dod_corrections.py
$P -B $T --check --design docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md \
                 --history docs/01-plan/features/gain-budget-gmid-sizing.history.md      # 기대: pending 12, exit 1
$P -B $T --design … --history …                                                            # 기대: 바뀐 줄 [786, 788, 789, 793, 1034, 1036, 1037, 1038, 1040, 1044, 1099], history +1행
git diff --numstat   # design 11 11, history 1 0
```
그 뒤 `Role: doc` 커밋(트레일러 `--trailer`), `.ai/context.md` Python 바이너리 append(삭제 0줄 확인), push 단독 실행·전체 출력 확인.

도구 성질: 인자로 받은 두 경로만 읽고 쓴다. 앵커(줄 머리 개행 포함 고정 문자열)가 정확히 1번이 아니면 아무것도 쓰지 않고 exit 2. `--check`는 pending/applied만 출력(pending 있으면 exit 1). 두 번 돌려도 바뀌지 않는다. `--only`로 D1만(또는 D1 + 일부) 적용할 수 있고, D2~D4는 D1 없이 적용할 수 없다.

모래상자 확인(`C:/g245/dp`, `4a286f0` 판 두 파일 사본 -- 저장소 쓰기 없음):
- `--check` pending 12 / exit 1 → 적용 exit 0, 바뀐 줄 위 11개, history +1행 → `--check` applied 12 / exit 0 → 재적용 바뀐 줄 0.
- 앵커 중복 사본(1034행을 파일 끝에 한 번 더): `D1 ERROR: 옛 앵커 2번` exit 2, 파일 sha256 불변.
- `--only D2`(D1 없이): exit 2.
- 합성 저장소에 패치 전후 design을 커밋하고 `phase3_dod_kit/extract_design_blocks.py`로 추출: sha256 5개(`ec96033a…`·`b3803fca…`·`ae6422d6…`·`de554c33…`·`e00a4634…`)와 줄 범위(822-858·875-988·1047-1095·999-1018·820/797-801)가 전후 같다. `git diff --numstat` = `11 11`.

## 5. DoD kit와의 관계

kit(`phase3_dod_kit/run_dod.sh` r1)는 이미 D1(`to_h` + `fresh_k`가 같은 `E5 INVALID: 판 전환 실패` 줄)·D2(`fresh_k … &&`, 단독 줄 `|| exit 1`)·D3(`--head "$H"`)·D4(`GC` = `$G/cache_<H>`)와 같은 동작이다. 정정 전후 kit 판정 블록 추출값이 같으므로 kit 수정은 필요 없다. 정정을 커밋하면 브리핑 초안 §9의 어긋남 1·2는 '해소(정정 커밋 <해시>)'로 바꾼다.
