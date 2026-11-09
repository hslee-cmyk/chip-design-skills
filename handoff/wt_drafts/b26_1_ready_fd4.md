# B26-1 착수 키트 준비 확인 -- gate master fd4ef8c(→ b4734cd) 기준, card 35 실제 도구

작성 2026-10-06. 실제 저장소는 읽기만 했다(git -C, set -e). `_drafts`는 이 파일만 썼다(launch·carry·spec 수정 없음 -- 고칠 앵커 없음).
모래상자 `/c/g282`(TMP·TEMP·TMPDIR 그 안, 끝나고 삭제).

## 0. 결론

**멈춤 0. kit(launch·carry·spec)에서 고칠 file:line 없음.** 범위 밖 문구 1건(승인 기록 4 초안의 P9 병합 sha, 아래 §4 n1)만 보고한다.

* `b26_1_launch.sh` conds(exit 3, 미충족 = 10뿐, 기대대로) → local1 → push #1(모래상자 EL4 통과) → after-push-appr(1~11 전부 0) → local2 → push #2(EL4 통과) → after-push(B1 기록): 전부 통과.
* `b26_1_carry.sh check`(실제 card 35 도구 출력, 1차 시도 모의): **rc 0** -- V5 diff_hash 3중 일치, 발견 = 두 시그니처 test, V3 생존 1 = U3, K1 def 묶기 해시 일치.
* V3 대상(실제 도구 + 가짜 pytest, B1..K1): **299 / not_targeted 2,136 / defs 32**, scope_proto N2w 독립 계산과 대칭차 0, `--out` 순서 일치.
* 키트 셋에 `plan_tables_hash` 하드코딩 없음(`pre`가 읽어 상태 파일에 적고 뒤 단계는 '불변'만 본다). 관측값 `16b899d1c745ddd0d305b2a977eecc74b0c830d89507d7eb3476b7323a08aec1`.
* 중간에 실제 gate master가 fd4ef8c → b4734cd(`.ai/context.md` +22) → 7243f28(B34 0단계 실제 진행: phase3-cards 승인, references, B34 spec card, role/*/B34 브랜치)로 움직였다. 이 작업은 실제 저장소에 쓰지 않았다(status md5 앞뒤 같음 `76eea762…`).
  모래상자는 b4734cd 위에서 만들었다. 실제 커밋된 `20261001-b26-phase3-cards.md`는 모래상자에 쓴 `_drafts` 초안과 바이트 같음(cmp). b4734cd..7243f28은 SD·SR·P9 계약 test를 바꾸지 않는다.

## 1. 모래상자 구성

* `r` = 작업 트리 저장소 `git -c core.autocrlf=false clone --no-hardlinks --no-local`, master b4734cd. 그 위 선형 커밋(빈 hooksPath, 이전 리허설 방식):
  1. `audit:` gate_config·pre-receive 경로만 모래상자로(`post_p10b_dryrun_setup.sh` 식)
  2. `docs:` 승인 `20261001-b26-phase3-cards`(= `_drafts` 초안, B34 launch P 모의)
  3. B34 code 모의 = `p35_heads` B1의 SD(mk_b1 사이트 1·2·3·11·11b), `Change-Id: 20260930-b34-grammar-explicit` + 판정 기록 자리표시(V1~V10 PASS, `DRY_RUN` 키)
  4. b26pre 모의 = 시제품 test 2파일(`proto_v2_test_b26pre.py`, `proto_test_b26pre_trace.py`, 무수정 복사), `Change-Id: 20260930-b26-pre-test-strengthen` + 자리표시
  5. backfill 모의 = `p35_heads` C4B의 SR(11800·11879 삭제, numstat 0 2), `Change-Id: 20261001-b26-backfill-interdig-final-audit` + 자리표시
  (B34·b26pre·backfill spec card 등 문서 커밋은 넣지 않음 -- b26_1 키트가 보지 않는 경로.)
* bare `gate.git` = 실제 `pre-receive`·`gate-runner.py`(EL4), accept-log 2줄. `r`: remote gate, hooksPath `.githooks`(EL3), `.claude/hooks` 복사.
* 측정 복제본 `m` = 같은 방식 복제 + `post35_kit/p35_heads.py setup/build`(REV fd4ef8c): B1 `3c22248`, C4B `6f4dffa`, H5 `1d005d5`, H5T `9935951`.
* 게이트 캐시(B1 판) `mutate_changed.py`·`weakening_diff.py`·`reachability.py`·`merge_gate.py`·`interface_card.py`·`role_paths.py` = 실제 fd4ef8c 파일과 바이트 같음(cmp) -- 실제 card 35 도구.

## 2. b26_1_launch.sh

| 단계 | 결과 |
|---|---|
| `conds` | `1:0 2:0 3:0 4:0 5:0 6:0 7:0 8:0 9:0 10:128 11:0`, D2 card = 규약 전체 = 0, approval 줄 b40-reason-key만 gate에 없음 → exit 3(기대) |
| `pre` | measured `7535799`(spec:35 앵커, 출현 1개) → gate: SD·SR·P9T 변경 커밋 4개 전부 확정 순서 card(`4a34f84` B34 SD, `a410f31` P9 SD, `8e9676e` backfill SR, `6bf510b` P9 P9T), 새 test 파일 없음, P9 시그니처 test 2개 있음. **`_approved_ids` 39**, plan_tables_hash `16b899d1…` |
| `appr`/`final-appr` | 승인 기록 바이트 OK 2614 B, parse decision target `U4-B40-UNAVAILABLE-REASON-KEY`, ids +1 = ATARGET(39 → 40), plan hash 불변 |
| push #1 → `after-push-appr` | EL4 통과(accept-log 1줄) / 조건 1~11 전부 0 |
| `local2` | approval 3건 parse OK, parse_spec_card `('3','red-green','no',[3건],[],12)`, **interface 행 46 = IFC_ROWS(신규 2)**, 371줄, numstat 삭제 0, final OK |
| push #2 → `after-push` | EL4 통과 / B1 = S `20417ab` 기록, plan hash 불변 |

## 3. 1차 시도 모의 + carry `check`

* T1(`Role: test`, Change-Id B26-1): 두 시그니처 test를 승인 기록 4 초안 '범위 설명'대로(`[…, "rails"]`, `ps[:2]` 루프, `rails` KEYWORD_ONLY·기본값 없음·`(RailDeclaration, "RailDeclaration")`) + `p35_heads` H5T 인벤토리 probe test. K1(`Role: code`) = T1 + H5의 SD·SR(B26-1 v5 head). audit worktree = T1.
  (첫 T1 시도 -- 리스트에 `"rails"`만 더하고 루프를 `[:2]`로 -- 는 `weakening_diff` PASS·발견 0이었다: 순수 리스트 원소 추가는 '비교 완화'가 아님. 초안 모양에서는 아래처럼 FAIL. 정보.)
* `base_check.json` = 실제 `weakening_diff.py --base B1 --head T1`: **FAIL**, 발견 정확히 2 = `test_kcl_series_union_signature_unchanged`·`test_kcl_and_matching_edges_signature_unchanged`('비교 완화'), `diff_paths` = [P9 경로], `diff_hash` `d2241482be375886…`.
* `attempt1_v3.json`·`.out.jsonl` = 실제 `mutate_changed.py --base B1 --head K1`(`p35_v3count.py`, 가짜 pytest = `range(i + 0, len(chains))`만 생존): exit 1(FAIL), mutants **299**, not_targeted **2,136**, 레코드 2,435, defs 32, proto 대칭차 0, 순서 일치, 생존 1 = `stick_diagram:find_differential_pair_candidates:const-:body[8].body[3].body[1].body[0].iter.args[0].right`, 묶기 해시 `cdab7b02a219b8e8…`(post35 재측정과 같은 값). 소요 12분 28초.
* `b26_1_carry.sh check`: **rc 0** -- dispute 없음, V5 `base_check.json` = 재실행 = `merge_gate diff-hash`, V3 원소 = K1 def 묶기 해시 따로 계산 일치, 노드 = `range(… + 1, …)`의 1. 상태 파일에 B1·T1·K1·DIFF_HASH·V3_ELEM·CHECK_OK 기록.
* carry 기록 5 핀: `approval_20261001-b26-v3-equiv-range.md` sha256 `3d2333b7…0f10` = `b26_1_carry.sh:76`, `fill_u3.py` `a6d05133…455caf` = `:77`(일치, records는 범위 밖이라 실행 안 함).
* carry를 고치지 않았으므로 self-test 두 suite(62/0, 18/0)는 다시 돌리지 않았다(공유 `out/*.tsv` 앞뒤 sha256 같음).

## 4. 요청 항목별 drift

| 항목 | 위치 | 결과 |
|---|---|---|
| plan_tables_hash 하드코딩 | `b26_1_launch.sh:108·315·373·386·454·469`(읽기·불변 비교만), carry 없음 | 없음 -- 수정 불필요. 관측 `16b899d1…` |
| approved_ids 수 | launch는 수를 단정하지 않음(`:325` 출력, `:371` +1 = ATARGET, `:453` 불변) | 39 → 40. 수를 적은 b26_1 문서 없음 |
| measured rev 앵커 | `draft_b26_1.spec.md:35` `7535799`(유일 출현) | 유효. 이후 SD·SR·P9T 변경 = 확정 순서 card뿐(실제 gate b4734cd·7243f28 기준도 a410f31·6bf510b뿐) |
| 사이트 줄 앵커 | `draft_b26_1.spec.md:15`(SD 1014·1571·1613·2092·2168·3133·3238·3973·4152·4288·4304·4351·4373, SR 2207·4293) | 모의 B1 트리에서 13+2줄 전부 `_RAIL_NETS`·씨앗·`_DEFAULT_RAIL_*`·인라인 튜플 줄 -- 그대로 |
| 인용 줄(design 05·도구) | spec '두 번 시도 절차': design 05 397·399행, `role_hooks.py` 808, `merge_gate.py` 1149(`_first_parent_chain`) | 0f23786·5f643a9·b4734cd 모두 같은 줄 |
| V3 대상 299 | `draft_b26_1.spec.md:333·362·396` | 실제 도구 299 / 2,136 -- 같음 |
| P9 시그니처 test 기대 | `b26_1_launch.sh:146`, `b26_1_carry.sh:92`(UNITS) | B1에 두 이름 있음, V5 발견 단위 = 정확히 두 이름 -- 같음 |
| interface 행 | `b26_1_launch.sh:92` IFC_ROWS 46 | B34·backfill 모의 뒤 46 그대로 |
| `stick_diagram.py` 32행 `from __future__` | 승인 기록 4 초안 '범위 설명' | b4734cd에서도 32행 |

**n1(범위 밖, 고치지 않음 -- 승인 기록 초안이라 이 작업의 수정 범위가 아님):** `_drafts/approval_20261001-b26-p9-signature-update.md:21` '덮는 것'의 "P9 `20260930-p9-kcl-edges` 계약 test, 병합 `b7765b0`" -- `b7765b0`은 gate에 없는 P9 1차 시도 병합이다(`merge-base --is-ancestor b7765b0 b4734cd` exit 1; spec card 조건 3도 그렇게 적었다). gate의 P9 병합은 `93b18db`. 기록 파싱·target과 무관한 산문이라 동작 영향 없지만, 커밋되는 기록이므로 records 전에 `93b18db`로 고칠지 오케스트레이터가 결정. (이 초안은 핀 대상이 아니다 -- 기록 4는 핀 없음.)

## 5. 격리

* 실제 저장소: 쓰기 0. status md5 앞뒤 `76eea762…` 같음. HEAD·gate/master·reflog·role 브랜치 변화(fd4ef8c → 7243f28, role/*/20260930-b34-grammar-explicit 3개)는 실행 중 오케스트레이터의 B34 실제 진행이다.
* `_drafts` 핀 대상·launch·carry·spec·self-test `out/*.tsv` sha256 앞뒤 같음.
* 모래상자 git 작업은 `/c/g282/bin/*.sh` 안에서만. 첫 audit 실행은 bg 시간 제한(10분)으로 중단돼 V3만 다시 돌렸다(위 수치는 다시 돈 완료 실행). `/c/g282` 삭제.
