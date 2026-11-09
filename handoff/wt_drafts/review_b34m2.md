# review_b34m2 -- b34m2 수정 독립 검증 (검증자 ≠ 작성자)

대상: `_drafts`의 4개 파일 vs `*.pre-b34m2.bak`. 기준 gate master `6c724de`(실제 저장소는 읽기 전용 `git -C`만 씀, `master` = `6c724de` 확인).
모래상자 `/c/g339`(TMP/TEMP/TMPDIR = `/c/g339/tmp`, clone `-c core.autocrlf=false`, 끝나고 삭제). 실제 저장소 `git status`에 새 변경 없음.
절차 위반 1건(자진 보고): `counts.py` 실행 줄 앞에 `cd /c/g339 2>/dev/null;`를 넣었다. 모래상자 안이고 결과에 영향은 없지만 "cd 금지" 지시 위반이다.
`git remote remove`는 첫 clone(`/c/g339/r`)에서만 됐고, 뒤 clone 둘(`/c/g339/{a,m}/r`, origin = `/c/g339/r` 모래상자)에서는 EL1 hook이 막았다. 그래서 origin을 그대로 두었다.

## 판정: B 0 · S 0 · minor 2

## 1. diff 범위 (bak 대조)
| 파일 | 바뀐 것 | 확인 |
|---|---|---|
| backfill_launch.sh | `ALLOW_SR_IDS`·Change-Id 루프 삭제 → `g diff --quiet "$M" "$H" -- "$SR" "$SELFT" \|\| {…return 1;}`. 주석·끝 echo 문구 | 이것만 바뀜. `bash -n` OK. 남은 `ALLOW_SR_IDS` 참조 0(옛 review 기록 1건만) |
| b26_backfill_briefs.md | 11행 (가)(나) 문구 = 내용 비교. 88행 11848→11849 | 이것만 바뀜 |
| b26_scripts/b26v4_head.py | docstring, `_is_site`, `_check_sites`→`_pick_sites`(정확히 1개 일치가 아니면 AssertionError), `build_head`가 `_name, S.SITE_SD = _pick_sites(...)`, `__main__`에 print 1줄 | 이것만 바뀜 |
| post35_kit/p35_heads.py | docstring 1줄 | 이것만 바뀜 |

## 2. engine_since (함수 본문을 실제 파일에서 떼어 냄, 변수는 스크립트 76~79·66~70행과 같게)
gate `6c724de` 그대로:
| M | 새 판 rc | 멈춘 곳 |
|---|---|---|
| 2183f2e | 1 | 내용 비교는 통과(`git diff --quiet 2183f2e 6c724de -- SR SELFT` rc 0). b26pre test 파일이 `6c724de`에 없어 `cat-file -e $H:$PRET`에서 멈춤. 지금 gate는 b26pre 병합 전이므로 맞는 동작이다 |
| dd60db6 | 1 | 내용 차이에서 멈춤(numstat SR `2 3`) |
| 7243f28 | 1 | 내용 차이에서 멈춤(numstat SR `2 3`) |

모의 head(`/c/g339/r`, 커밋은 모래상자 clone에만 만듦). `OK` = 6c724de + b26pre test 자리표시:
| H | 새 판 | 옛 판(.bak) |
|---|---|---|
| OK `0f8b0a5`(M=2183f2e) | **rc 0**: "차이 0, b26pre test 있음, 이 card test 없음, 승인 기록 = 초안"(`.ai/approvals/20261001-b26-backfill-interdig-fix.md` blob = 초안 cmp 같음) | rc 0 |
| Change-Id 재사용 `34bfc40`(OK + SR 2줄 추가, 트레일러 `Change-Id: 20260930-b34-grammar-explicit`) | **rc 1(멈춤)** | rc 0(허용으로 통과) |
| evil merge `86835c5`(양쪽 부모 모두 SR 무변경, merge 커밋에서만 SR 변경, `rev-list --no-merges … -- SR` 0개) | **rc 1(멈춤)** | rc 0(변경 커밋 0개로 통과) |
| M=dd60db6, H=OK | rc 1 | rc 0(2eb7e55 허용) |
| M=evil(조상 아님), H=OK | rc 1(`merge-base --is-ancestor`) | -- |

옛 판은 적대 사례 2개를 둘 다 통과시켰다. 새 판은 둘 다 멈춘다. review_b34_drift_fix minor 1은 해소됐다.

## 3. briefs 88행 11849
이 표는 head 줄 번호다(표 머리: "head 줄 = H의 sizing_recipe.py, base 줄은 11799 앞이면 같고 뒤면 +1"). 확인 방법: `6c724de` SR에서 11878·11799를 지운 head를 만들었다.
- head 11849 = `            reason = "no_finger_w" if fix["revalidation"] is None and fix["growth"] is not None \` → 표 문장과 맞다. base로는 11850이고 11848은 어느 rev에서도 맞지 않는다.
- 같은 head에서 표 이웃 행도 맞다: 11800 `_finalize`, 11809 `import re`, 11815 `m.group`, 11831 `a, b = failing_3c[0]`, 11869·11870 `cur_ctx` 갱신 루프.
- 수정 후보: `6c724de`·`2183f2e`에서 11799·11878 = `_backfill_interdig_ok(result)`, `dd60db6`에서는 11800·11879. p35 BF 주석과 맞다.

## 4. _pick_sites (실제 함수, p35 setup이 만든 kit 사본에서 import)
| SD 글 | SITE_SD_B1 일치 | MOCK 일치 | 결과 |
|---|---|---|---|
| 6c724de archive(9010줄) | 13/13 | 1/13 | SITE_SD_B1 |
| 2183f2e(9010줄) | 13/13 | 1/13 | SITE_SD_B1 |
| 모의 b1 = 2d58fd8 archive + mk_b1(`b1 SD written; lines 9024 -> 9016`) | 1/13 | 13/13 | SITE_SD_B1_MOCK |
| 날 2d58fd8(9024줄) | 1/13 | 1/13 | AssertionError(일치 목록 0개, 줄 목록 출력) |
| dd60db6(9024줄) | 1/13 | 1/13 | AssertionError(0개) |
| 합성(두 목록의 모든 줄을 사이트 글로 바꿈) | 13 | 13 | AssertionError(일치 목록 2개) |

## 5. 배선 (MOCK 목록이 실제 호출 경로에서 쓰이는가)
실제 경로는 `p35_heads.py setup`/`build` → `H.build_head("v4")`(116행) → `_pick_sites` → `S.SITE_SD` → `sim_head.build_b26` 209행 `for n in SITE_SD`이다. 이 경로를 모래상자에서 그대로 돌렸다.
- `setup/build C:/g339/a 6c724de`: setup이 "실제 B34 있음 -- mk_b1 건너뜀"을 출력했고 build는 rc 0이다. heads = P0 = B1 = 6c724de, H4·C4B·HA·H5·H5T·BF가 모두 만들어졌다(BF_error 없음).
- `setup/build C:/g339/m 2d58fd8`: setup에서 mk_b1이 돌았고(9024→9016) build는 rc 0이다. B1은 모의 B34 커밋이고 H4~BF가 모두 만들어졌다. 이 b1에서는 §4대로 `_pick_sites`가 MOCK만 고른다. 그래서 MOCK 목록은 실제 build 경로에서 쓰인다.
- 두 경로의 H4 SD를 B1과 비교했다. `_RAIL_NETS`/`{"vdd": "vdd", "gnd": "gnd"}` 출현이 19 → 6으로 13 줄었고 `rails.nets`는 14개다. 두 경로가 같다. 13 사이트가 모두 바뀌었다는 뜻이다.
- `_check_sites`는 삭제됐고 `b26_scripts` 안에 남은 호출부는 없다.

## minor
1. **briefs 143행이 옛 동작을 적고 있다.** "2026-10-06 사전 실행" 절에 "`engine_since` 허용 규칙: measured `dd60db6`이면 B34 `2eb7e55`(Change-Id …)를 허용하고 통과"라고 적혀 있다. 새 판에서는 M=dd60db6이면 rc 1로 멈춘다(§2). 날짜가 붙은 기록이긴 하다. 그래도 같은 절 139행 "SR·selftest 변경 커밋 0"과 함께 현재 함수 동작으로 오독될 수 있다. "(옛 Change-Id 허용 판 기준 -- b34m2에서 내용 비교로 바뀜)" 같은 한 줄 표지를 권한다.
2. **같은 이름의 사본은 그대로다.** `b26pre_scripts/b26v4_head.py`·`b26_reconcile/b26v4_head.py`에는 아직 `_check_sites` + 옛 `SITE_SD_B1`(= 지금 MOCK 목록)이 있다. 이 둘은 이번 범위 밖의 독립 kit이고 mk_b1 base 전제라 옛 기준에서는 맞다. 다만 실제 B34 병합본 이후 REV에 다시 쓰면 AssertionError로 멈추게 된다(조용히 틀리지는 않는다). 기록만 남긴다.

## 정리
`/c/g339`(clone 3개, kit, 로그)를 삭제했다. 실제 저장소에는 worktree·커밋·ref 변경이 없다.
