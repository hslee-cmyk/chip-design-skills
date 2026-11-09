# 독립 검토 -- Phase 3 DoD 브리핑 초안 v0 + 실행기 kit (2026-10-02)

대상: `_drafts/draft_phase3_dod.md`(v0), `_drafts/phase3_dod_kit/`(run_dod.sh, extract_design_blocks.py, inputs_p3.py, n63_p3.py, judge_p3.py, p3_cards.py).
기준: design 30 §8·§9.1·§10(gate `master` `4a286f0`), 계획 N6.2 Phase 3 행(1018행)·N6.3(1028행~), Phase 2 DoD 기록 `phase2-dod.md`(`2eefda1`)·브리핑 `phase2_dod_brief.md`, 사용자 결정 `user_decisions.md`, 승인 초안 `approval_20261001-b26-phase3-cards.md`.
검토자는 초안·kit의 작성자가 아니다. 저장소는 읽기만 했다(`git -C`, `GIT_OPTIONAL_LOCKS=0`). 모래상자 `C:/g236`(복제 `-c core.autocrlf=false -c core.longpaths=true --no-hardlinks --no-local`, origin 제거, TMP/TEMP = `C:/g236/tmp`)에서 돌렸고 끝에 지웠다.

## 판정: S (공식 실행 전 고칠 것 있음, 차단(B) 없음)

- 기준 약화 없음. 13항목은 design §10 표 E0~E6(E3b 포함 8) + Phase 2 DoD 선례의 N6.3 1~5(5)와 같다.
- S 2건: (S1) design §10 `fresh()`가 실패해도 계속 도는 결함(design 정정 필요), (S2) 판정기가 빈 입력을 PASS로 세는 경로 6개(kit 수정).
- 경미 7건(아래 §5).

## 1. 13항목과 card 목록 -- 기준 대조

| 항목 | 초안 | 기준 | 결과 |
|---|---|---|---|
| E0·E1·E2·E3·E3b·E4·E5·E6 | §5 1~8행 | design §10 표 통과 기준 열 | 같다. E4 `absent_split`은 정렬만 다르고 집합은 같다. E2 ①②③, E5 (i)~(iv), E6 `--allow-changed` 두 단위도 같다 |
| N6.3-1~5 | §5 9~13행 | 계획 N6.3 두 bullet과 Phase 2 브리핑 §6 1~5(선례 형식) | 같은 모양이다. N6.3-2는 Phase 2보다 엄격하다(예외 0) -- 약화 아님 |
| N6.3-4에 `tools/migrate/*` 추가 | 넓힘 | 계획 문언에 없다(N6.3-4 자체가 Phase 2 브리핑이 만든 운용 정의). design §9.1 D-27 동결 범위가 `tools/migrate/**`를 넣는다 | **넓힘이고 약화는 아니다.** 실측: `da03c0e..5f643a9`는 넣든 빼든 31개, `da03c0e..4a286f0` 범위에서 `tools/migrate/*` 커밋 0개. D0a의 code 커밋이 목록에 들어와 N6.3-4가 D0a를 실제로 보게 된다. 사용자 승인 불필요(기준 강화). 단 결과 '절차 메모'에 "브리핑이 더한 경로"로 적을 것. `tools/gates`를 넣지 않은 이유(0.5 게이트 card의 정당한 변경)도 한 줄 적을 것 |
| M10·T1을 card 목록에 넣음 | 넣음 | design §8 표(card 수 17, M10 red-green, T1 test-only) | **design대로다.** 넓힘이 아니다. 지시문 목록에서 빠진 쪽이 틀렸다 |
| B33 제외(phase 0.5) | 뺌, C2·관찰 2로만 | 사용자 답 Q-B34-PHASE "phase 3 + 정정 기록"은 승인 초안 범위 설명상 **B34·b26pre·backfill·B26-1 네 card만** 덮는다. B33 spec card 초안 머리 = `phase: 0.5`, `gate_change: yes`. design §9.1 "게이트 card(`phase: 0.5`) 면제 묶기·범위 정책·B33은 … G1의 선행" | **맞다.** B33은 그 결정에 들지 않았다. G1도 design §8에서 17장에 들지만 `phase: 0.5`라 `^phase: 3$` 목록 밖이다(17 − G1 + 네 card = 20, 산술 맞음). Phase 2 선례(B28·rejudge-cache는 1번 전수에만)와 같은 처리 |
| 0.5 card가 엔진 경로를 건드리면 | -- | -- | 확인함: 34 실측 `tools/gates`만(`dd01d1d`·`8b1f929`), 35 spec card·B33 초안·G1 브리핑의 쓰기 경로가 `tools/gates/**`와 문서뿐이다. B33의 `skills/analog-gmid-design/assets/rt_engine.py`는 redteam 합성 저장소 안 경로다. N6.3-4가 0.5 card에서 거짓 FAIL을 낼 경로는 지금 없다 |

## 2. design §10과 어긋난 두 곳 -- design 결함인지, kit만의 보강인지

### 2.1 `fresh()` 순서와 HEAD 확인 -- **design 결함(S1), 정정 필요**

재현(`C:/g236/fresh_demo`, 합성 저장소 A→B, `w/inst.json` 두 판이 다름): A에서 추적 파일을 고친 뒤(E-INST가 하는 일) design `fresh B` → `checkout --detach`가 "local changes would be overwritten"으로 거부, rc 1, **HEAD = A 그대로**, 파일은 고친 내용 그대로. design 호출부는 `fresh "$H";   $PY -P …`처럼 `;`로 잇기 때문에 **HEAD 측정이 P2D 판에서 돌아 E-INST "같음"이 나온다. 실패해야 할 곳에서 통과하는 경로다.** kit `to_h B`는 rc 0, HEAD = B, 파일 = v2.
발동 조건: E-INST/E-LIB 스크립트가 쓰는 추적 파일(`workspaces/*/…instance.json` 등. Phase 2 DoD 복제본 status에 ` M` 2줄이 남았다)이 P2D와 H에서 다를 때. `5f643a9..4a286f0`에서는 다르지 않아 리허설에서는 안 보인다. 다만 Phase 3 card가 추적 산출물을 다시 커밋하면 바로 발동한다.
선례와도 어긋난다: design 20 §10 E4(223행)는 "판을 바꿀 때마다 `checkout -- workspaces`·`clean -fdx`로 산출을 지운다"였고, Phase 2 브리핑 §2도 "지우기 → detach → HEAD 대조 → status 0줄" 순서였다. design 30이 순서를 거꾸로 하고 확인을 뺐다.

정정안(design 30, `4a286f0` 판 줄 번호):
- 1034행 현재:
  `fresh() { git -C "$ISO" checkout -q --detach "$1" && git -C "$ISO" checkout -q -- . && git -C "$ISO" clean -q -fdx; }`
  고칠 문안:
  `fresh() { git -C "$ISO" checkout -q -- . ; git -C "$ISO" clean -q -fdx; git -C "$ISO" checkout -q --detach "$1" && [ "$(git -C "$ISO" rev-parse HEAD)" = "$(git -C "$ISO" rev-parse "$1^{commit}")" ] && [ -z "$(git -C "$ISO" status --porcelain --ignored)" ] || { echo "E5 INVALID: 판 전환 실패 $1"; return 1; }; }   # 산출을 먼저 지우고 옮긴 뒤 HEAD·status를 확인한다(design 20 §10 E4 순서, Phase 2 브리핑 §2)`
- 1036~1038행·1040행·1044행: 줄은 그대로 둔다. `E5 INVALID` 줄이 나오면 E5 통과 기준("`E5 INVALID` 줄이 없고")이 이미 FAIL로 만든다. 더 엄격하게 하려면 `fresh "$X"; $PY …`를 `fresh "$X" && $PY …`로 바꾼다(선택).
- 1099행 E6 `--head HEAD` → `--head "$H"`(선택). E5의 마지막 `fresh "$H"`가 성공한다는 전제에 기대지 않게 한다.
- 성격: 판정 기준은 그대로이고 실행을 실패 시 멈추게 하는 절차 강화다. 원칙상 사용자 승인은 필요 없다. 다만 design 30은 UD-0 승인 해시(`a4350dc05ff86179`)가 걸린 문서이므로 정정 커밋 + 이력(history) 기록이 필요하다. 승인 기록을 새로 남길지는 오케스트레이터가 정한다(약화가 아니므로 `target_kind: diff` 승인은 불필요하다고 본다).

### 2.2 `GC`를 `<iso>` 밖 캐시로 -- **kit만의 보강, design 결함 아님(경미, 선택 정정)**

design 블록 순서에서 `$GC`(= `$ISO/tools/gates`)를 쓰는 명령(E0/E1·E2·`import_any`·E4 plan의 `$S` 사본은 GC 아님)은 모두 E5 앞이다. E5 안의 `fresh "$P2D"`~`fresh "$H"` 사이에는 `$GC`를 쓰지 않는다. E6은 `$S/move_plan.py` 사본을 쓴다. 따라서 **정해진 순서에서는 다른 판의 게이트로 도는 일이 없다.** 위험이 생기는 경우는 둘이다. (a) 단계 순서를 바꿀 때, (b) 2.1 결함으로 마지막 `fresh "$H"`가 실패해 `<iso>`가 P2D에 남을 때. (b)는 2.1을 고치면 막힌다.
한편 design 자체에 게이트 출처가 둘이다. PT3는 `<cache>`(05 §4.4), E0/E2/IA는 `$ISO/tools/gates`다. 선택 정정 문안(786행):
`GC="<05 §4.4 캐시: git archive <H> tools/gates를 <iso> 밖 또는 <git-common-dir>/gmid-gate-cache/<H>/에 푼 것>/tools/gates"`. 그리고 793행의 `<cache>`를 `$(dirname "$GC")`/`$GC`로 통일한다. 판정 영향 없음.

## 3. 리허설 재실행 결과 (`C:/g236`, H = `4a286f0`, kit 그대로 `run_dod.sh /c/g236 4a286f0 rehearse`)

시간 2026-10-02 15:28~16:09(41분). 결과는 초안 §0·§5·§6·§8의 주장과 **모두 같다**:

| 단계 | 재실행 결과 | 초안과 같은가 |
|---|---|---|
| guard | G1 PASS(H = gate/master = ls-remote = `4a286f0`), G2 INFO(역할 브랜치 `role/test/20260930-v3-changed-stmt-scope` 1개 -- 공식 실행이면 여기서 멈춤), G3 PASS, G4 PASS | O |
| design 블록 sha256 | `ec96033a…`·`b3803fca…`·`ae6422d6…`·`de554c33…`·`e00a4634…`(줄 822-858·875-988·1047-1095·999-1018·820/797-801) | O(바이트 단위로 같음) |
| inputs | P2D `5f643a905fbc…`, B0·MPC 없음, cards.txt 0줄, missing **28** | O |
| e01 | `E0 FAIL present 1/10`(9개 없음), **`E1 PASS exit=0 findings=0`**(공허 -- 4-a) | O(초안은 '공허'라 적었지만 실행기 출력은 PASS) |
| e2 | PENDING. 기계 리허설 V3 `H^..H` exit 0. 키 = `exempt_ignored killed mutants survivor_bindings survivors targets tool verdict`, design ① 키 중 없는 것 `defs move_rejected not_targeted targets_by_def moved` | O |
| e3 | 세 shim 있음 → FAIL 3줄. 거부 확인(대용 B0 = H) rc 0, stmt 69, call 9, 파일 67(제외 집합 1). `E3 FAIL: 제외 집합 밖 importer 66파일` | O |
| e3b | `LIVE moved_out=0 base_files_reading_moved_out=0 pre_existing=1` + `E3b INVALID` | O |
| e4 / e6 | PENDING / PENDING | O |
| ia | `IMPORT-ANY tried=5 expected=5 failed=0`, 종료 0 | O |
| e5pt | `PT3` exit 0 **1047 passed, 15 xfailed**(402.13 s), `PT3 --gmid-dod` exit 0 **1047 passed, 15 xfailed**(325.70 s) | O(수 같음, 시간만 다름) |
| e5lib | 10회 실행 모두 exit 0. `E5 INVALID` 없음. E-INST crt `185b675e`/raw `2fc426d9`, fc `0ca6746f`/raw `ef3cd996` -- P2D·H 같음. E-LIB `1d2e3bf6` 9회로 같음. **`E5 E-LIB rails 계약 FAIL` 9줄**(HEAD·P2D `<ABSENT>`) → `E5 E-LIB/E-INST FAIL rails:…`. 사본 sha256 `7d26134a…`·`c6b82fc7…`·`6cc48495…`·`41b72d7d…` | O |
| n63 | `1 True(n=35) | 2 False(0/20) | 3 False | 4 True(n=0) | 5 False` -- 4번 PASS는 공허(4-c) | O |
| watch | W1·W2·W3 PASS. 복제본 reflog clone → H → (P2D ↔ H) **3왕복** → H(초안 §8 watch 행의 "4왕복"은 오기 -- 경미 8), 끝 status `--ignored` 0줄 | O |

메인 저장소 HEAD는 실행 전후 `4a286f0`. `status --porcelain --ignored`(175줄)와 reflog(345줄)도 전후 같다(kit W1·W2와 검토자 별도 대조).

### 3.1 N6.3 검사기 Phase 2 재현 (`n63_p3.py <iso> 5f643a9 da03c0e out 2`)

`N6.3 1 True(n=34) | 2 False(18/17, 기록 없음 1) | 3 True | 4 True(n=31, 어긋남 0) | 5 True`.
판정 기록 34건 전부 PASS/N/A, phase 2 card 18장·기록 17·없는 것 `20260923-probe-promote-consistency` 1. evidence_type red-green 8·equivalence 4·test-only 5. audit 커밋 17개(`1cdebc9`…`5f643a9`)와 병합 12개(`05afe00`·`427b0c3`·`2a2a7a0`·`d473f65`·`1adbb76`·`dd3fae4`·`243e6ed`·`93b18db`·`54ef51c`·`f1c4b7d`·`d23f4bb`·`b29be01`)가 `phase2-dod.md` 표와 같다. red 개수 1/5/1/25/1/34/6/21도 같다. 엔진 커밋 31·어긋남 0이다(세 pathspec만으로도 31).
2번의 `False`는 Phase 2 브리핑이 허용한 예외 1건 때문이다(phase=2 모드에 예외 목록이 없다). 수치는 재현됐다. 초안 §6 마지막 행의 "재현" 주장은 맞다. 다만 "2번 판정까지 같다"고 읽히지 않게 고쳐 쓸 것.

## 4. 판정기를 속일 수 있는가 (S2 -- kit 수정)

공식 실행에서는 가드 G5(`missing` 0)가 대부분의 빈 입력을 먼저 막는다. 하지만 아래는 G5를 통과한 뒤에도 비어 있는 결과를 PASS로 센다. 리허설에서 이미 `E1 PASS` 줄이 실제로 찍혔다.

| # | 위치 | 속는 경로 | 고칠 것 |
|---|---|---|---|
| a | `judge_p3.e01` E1 | `present` 1/10(E0 FAIL)인데 `E1 PASS exit=0 findings=0`을 찍는다(리허설 실측). MOD 파일이 없으면 import 계층 위반도 있을 수 없다 | E0이 PASS가 아니면 E1은 `PENDING(E0 미충족 -- 공허)`. 판별력 대조에 "F2 판정 기록 `base_commit`(SD → MOD9 임시 재수출이 있는 판)에서 `findings` > 0" 한 줄 추가(design §2.2 D-22, E1 문구 "F2가 … 지운 뒤"의 거부 확인) |
| b | `judge_p3.e01` E0 | `mod_table`이 빈 표를 돌려주면 `miss` = ∅ → `E0 PASS present 0/0` | `len(table) == 10`이고 번호 집합이 1..10일 것. 아니면 INVALID |
| c | `n63_p3` 4번 | 커밋 0개 → `ok = not badc` = PASS(리허설 "4 PASS(0개)"). Phase 2는 기대 개수 31을 대조해 공허를 막았다 | n = 0이면 PENDING. 덮음 대조 추가: 20 card 판정 기록의 `test_commit`·`code_commit`(null 아닌 것) 전부가 4번 목록에 있어야 한다(없으면 FAIL -- 경로 밖을 고친 card는 목록에서 빠진다) |
| d | `n63_p3` 5번 test-only | `roles <= {"test"}` -- 4번 목록에 그 card 커밋이 하나도 없어도(빈 집합) PASS | `roles == {"test"}`(Phase 2 문구 "`Role: test` 각 1개") |
| e | `n63_p3` 5번 equivalence | V2 PASS만으로 ok. Phase 2 브리핑 §6-5는 "base = 병합본 문장 인용, 없으면 '근거 문장 없음'(`outputs_hash`만으로 통과 금지)" | basis가 비면 `근거 문장 없음`으로 적고 ok = False(또는 사람 확인 표시). 판정은 auditor가 인용으로 한다 |
| f | `judge_p3.e4` | `d.get("assignment", {})`가 없거나 키 이름이 다르면 "SD·ACF 밖 단위 rule 전부 A-0" 검사가 공허하게 참이 된다 | `assignment`가 없거나 비면 INVALID |
| g | `run_dod.sh e3` | design은 `e3_run HEAD && {…}`로 도구 오류 때 PASS를 막는다. kit은 rc≠0이어도 계속해, 출력이 비면 `E3 FAIL(도구 오류 …)`과 `E3 PASS`를 **둘 다** 찍는다. 묶어 판정하는 도구가 없어 grep으로 PASS를 읽으면 속는다 | design과 같게: `[ "$rc" -eq 0 ] && { …PASS/FAIL… }`. B0 거부 확인도 rc≠0이면 design 문구대로 `E3 FAIL(도구 오류 …)` |

더해서 kit 단계 일부는 작업 트리를 읽는데 HEAD를 확인하지 않는다. e01(`import_layering --root`), e4(PT3·`plan --root`), e6(`--head HEAD`)이 그렇다. 기본 순서에서는 문제가 없지만, e5lib가 중간에 끊긴 뒤 `run_dod.sh … e6`처럼 단계만 다시 돌리면 P2D 판을 잰다. 세 단계 머리에 `[ HEAD = H ] || to_h "$H" || die`를 넣을 것(e3b·ia에는 이미 있다).

## 5. 경미

1. `inputs_p3`: `MPC_blob_equals_H` = False는 `notes`에만 남고 `missing`에 들지 않아 공식 가드가 멈추지 않는다. design은 D0b~M1 구간을 DoD가 덮지 않는다고 적었다. 그래도 MPC 판과 H의 blob이 다르면 '판정 기록 밖 변경'이 확정되므로 G5에서 INVALID로 멈추는 편이 맞다.
2. `inputs_p3`: M card V1의 `--gmid-phase=`를 읽기만 하고 3인지 단정하지 않는다(초안 §4 "3이어야 한다"). `v1_phase != "3"`이면 missing에 넣을 것.
3. `judge_p3.e2`: cards.txt가 8줄인지 단정하지 않는다(G5에 기댄다). 8줄이 아니면 INVALID.
4. 초안 §5 2행 문구 "exit 0, findings 0(공허 -- 판별 아님)"에 비해 실행기 출력은 `E1 PASS`다 -- 4-a로 고치면 맞아진다.
5. 초안 §9-6(N6.3-4 경로 추가)은 "확인 요청"으로 남기지 말고 "기준 강화, Phase 2 재현 수 불변 31"로 확정해도 된다(1절).
6. G1은 design §8 card 표에 있지만 N6.3-3(EL4 형식)·5(red 증거)에서 빠진다(Phase 2 B28 선례와 같다). 0.5 card 넷(34·35·B33·G1)에도 같은 n63 행 검사를 '관찰'로 돌리면 비용 없이 판별력이 생긴다(판정 기준에 넣지는 않는다).
8. 초안 §8 watch 행 "P2D ↔ H 4왕복"은 실제 3왕복이다(회로마다 1 + E-LIB 1. reflog의 `to 5f643a9` 3줄).
7. `extract_design_blocks`의 sha256 5개는 리허설 재추출과 바이트 단위로 같다(design 줄 822-858·875-988·1047-1095·999-1018·820/797-801).

## 6. design 정정 목록

| # | 줄(`4a286f0`) | 필수 여부 | 내용 |
|---|---|---|---|
| D1 | 1034 `fresh()` | **필수(S1)** | 2.1 문안: 지우기 → detach → HEAD·status 단정, 실패 시 `E5 INVALID: 판 전환 실패` 출력 + return 1 |
| D2 | 1036~1038·1040·1044 | 선택 | `fresh …;`를 `fresh … &&`로 |
| D3 | 1099 E6 `--head HEAD` | 선택 | `--head "$H"` |
| D4 | 786 `GC=`·793 `<cache>` | 선택(경미) | 게이트 출처 하나로 통일(H 판 archive 캐시, `<iso>` 밖 또는 `<git-common-dir>`) |

## 7. 모래상자 정리

`C:/g236` 전체 삭제(2026-10-02 16:1x). `/tmp`에는 쓰지 않았다. 메인 저장소: HEAD `4a286f0`, status·reflog가 실행 전 스냅숏과 바이트 단위로 같다. 이 검토가 쓴 파일은 `_drafts/review_phase3_dod.md` 하나다.
