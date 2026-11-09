# 독립 재검토 r1 -- kit_line_shift.py(r1) / .md / selftest / b34real 산출물 (2026-10-06)

검토자는 도구 작성자가 아니다. 작성자의 self-test 결과(70/70)와 문서 주장은 증거로 쓰지 않았다. 모든 실측은 모래상자 `C:/g336`(TMP/TEMP 포함)에서 했다.
저장소는 `git clone -c core.autocrlf=false`로 복제했고, 초안은 사본을 썼다. 측정이 끝난 뒤 모래상자는 지웠다. 실제 저장소와 `_drafts`는 읽기만 했다.

## 판정: **S** (B 없음)

* 줄 대응은 맞다. 패치 127건을 독립 difflib 대응과 글 대조로 확인했고 127/127 맞다. S1·S2·S3 수정도 내 적대 사례에서 재현되지 않는다.
* 다만 아래 S 두 건이 있다.
  * **S-A**: `draft_b26pre` 패치 124건은 card 자신이 "옮기지 않는다"고 적은 인용이다. 도구 문서는 이것을 "검증된 패치"로 내놓는다.
  * **S-B**: 절 표지가 다른 절로 번져서, 실제로는 낡은 인용 11건을 보고서가 "이미 새 번호(다시 옮기면 이중 이동)"로 표시한다.

---

## 1. 실제 사례 재실행 (old 7243f28 -> new 2183f2e)

* 모의 base `b1` 재생성: `git archive 2d58fd8` 결과에 `mk_b1.py`(경로만 `C:/g336`으로 바꾼 사본)를 돌렸다. 9024에서 9016줄이 됐고, 보고서 덩어리 머리(SD@b1 18개, SD@old 22개, SD@p0 25개, SR 1개)가 저장된 `current/`와 **글자까지 같다**.
* 초안 사본으로 재실행한 결과: records 471, patched 127(draft_b26pre 124, draft_b26_1 3), already-new 102. `current/`와 비교하면 다른 점은 `backfill_launch.sh` 줄 번호뿐이다(이 파일은 `current/`를 만든 19:35 뒤에 수정됐다).
* 같은 명령을 **실제 저장소·실제 `_drafts`**에 대고 돌린 결과(출력은 모래상자):
  * 초안 9개의 md5, `git status`, `_drafts` 목록이 실행 전후 같다.
  * 패치는 모래상자 결과와 바이트 단위로 같다.
  * TMP의 `kls_*` 디렉터리는 남지 않았다.
* **패치 127건 전수 검증**(검토자 스크립트 `v1.py`):
  * base n행 글 == new m행 글: 127/127.
  * 독립 `difflib.SequenceMatcher(autojunk=False)` 대응 == 도구 대응: 127/127.
  * 사본 초안에서 `git apply --check`가 통과한다.
* **무작위 24건 + 범위 16건 육안 대조** (글이 초안의 의도와 맞는지):
  * 표 행의 high(SR 6573 `if refined is not None and refined.get(...)`, SR 9404 `repaired_rows, repaired_audit = repair_matching_safety(`, SR 11802·11877·11879·11880, SD 2101·2177·3285·4297 등)는 base 줄이 초안 코드 조각과 같다.
  * medium(SR 11800·11879 backfill, 9404·9406, 11696, SD 1539·2100·2114 등)은 base 줄이 초안 서술과 맞는다(예: SD 2114 = `def _propose_L_roles(`, SR 11770 = 그 주석 줄).
  * `draft_b26_1:77` SD 3559·3561·3719 → 3534·3536·3694는 p0(cd64170) 줄이 `if t.source not in _RAIL_NETS:` 등 `propose_theta_kcl_gap_fill`의 레일 판정이다. 맞다.
* 패치된 범위 16쌍 가운데 사이에 덩어리가 걸친 범위는 0이다.
* `validation_snapshot` 대비 r1에서 빠진 draft_b26pre 4건:
  * 357·358행은 초안 글이 바뀌었다.
  * 268행 `11823~11826`은 새로 ambiguous가 됐다. 초안 의도는 old 번호이므로 옛 제안이 맞았다. 정밀도 손실이지만 패치 오류는 아니다(minor m4).

## 2. S-A -- draft_b26pre 124건은 card가 '옮기지 않는다'고 선언한 인용

* `draft_b26pre.spec.md` 본문(현재 판):
  * 464행 `**measured at dd60db6** … 이 card의 줄 인용은 그대로다`
  * 471행 `이 card의 SD·SR 줄 번호는 measured 판 기준이다`
  * 476행 `measured rev는 dd60db6 그대로이고 표·인용 줄도 그 판 기준이다`
  * **481행 `줄 이동 도구 _drafts/kit_line_shift.py(…)가 제안한 128곳(…)은 측정 rev를 밝힌 표·인용이라 옮기지 않는다`**
  * 2183f2e 위치는 479행에 따로 적혀 있다.
* 도구는 `measured at <rev>` 절 표지를 읽는다. 하지만 그 rev의 엔진 blob이 base와 같으면 `section-rev(..)≡base`로 **그대로 진행**해 high·medium 패치를 낸다. 보고서 근거 칸이 `section-rev(a796468)≡base`다.
* 그 결과 적용하면 card가 자기모순이 된다. 측정 rev 머리글은 dd60db6인데 인용만 2183f2e 번호가 되고, 479행 대응표와도 겹친다.
* `kit_line_shift.md` 105~110행은 이 124건을 "검증된 패치 127건"으로 소개한다. 사람이 이 패치를 그대로 적용하라는 신호로 읽힌다.
* 도구 문서 85행의 원칙("측정 기록(measured rev 앵커…) 줄은 바꾸지 않는 것이 기본이다(anchored)")은 줄 안 해시에만 적용된다. 절 단위 `measured at` 표지에는 적용되지 않는다.
* 수정 제안(둘 중 하나):
  * (1) `measured rev/at <rev>` 절 표지가 base와 같으면 그 절의 high·medium을 `anchored`로 내린다(`--include-anchored`로만 패치).
  * (2) md 실사례 절에 "draft_b26pre는 card 481행 결정에 따라 패치 대상이 아니다. 실사례 유효 패치는 draft_b26_1 3건"이라고 쓰고, 예시 명령에서 `--draft draft_b26pre.spec.md`를 뺀다.
* 줄 대응 자체는 맞다. 그래서 B가 아니라 S로 둔다.

## 3. S-B -- 절 표지 번짐으로 생기는 거짓 already-new (요청 (3): 'missed' 14건)

`validation_snapshot`에서 패치됐다가 r1에서 빠진 draft_b26_1 제안은 정확히 14건이다. 행마다 엔진 글을 대조했다.

| 행 | 인용 | r1 분류 | 실제 번호 판 | 판정 |
|---|---|---|---|---|
| 66 | SD 1355·1357·1557·1558·1737 | **already-new** `section-rev(2183f2e)=new` | **cd64170/7535799**. cd64170 1355 = `down_chains … == "gnd"`, 1557 = `("vdd_to_gnd", …)`, 1737 = `for direction, terminal in ((…"vdd_to_gnd"…`. 2183f2e의 같은 번호는 `+ _classify_forks(…)`·`groups[…]`·`for b in complete:`로 다르다 | 패치 밖이라 틀린 패치는 아니다. **분류가 틀렸다** -- 낡은 인용인데 보고서가 '이미 새 번호, 다시 옮기면 이중 이동'이라 적는다 |
| 71 | SR 7282·8003·8091 | anchored(cd64170·dd60db6·2183f2e 해시) | 행이 "줄은 cd64170"이라 밝히고 2183f2e 값(7281·8002·8090)을 같이 적었다 | 안전하고 올바른 생략 |
| 499 | SD 1575·1617·2096 | ambiguous `section-rev(2d58fd8)≠base·new` | cd64170(1575 = `if ta.source != tb.source or ta.source in _RAIL_NETS:`). 낡은 인용 | 안전한 생략. 새 값을 계산해 보고서 '모호'에 남김 |
| 542 | SD 3531·3535·3540 | ambiguous(같은 절 표지) | 7535799(= cd64170 SD blob `dbd35acd`). `"unavailable_reason": …` 줄. 낡은 인용 | 안전한 생략. 보고서에 남음 |

* 14건 모두 **틀린 패치는 아니다**(요청 (3)의 '안전한 생략'은 성립). 다만 66행 5건은 분류가 틀렸다.
* 같은 원인으로 65행 SD 1222·1233·1234·1270·1281·1282(6건)도 already-new로 표시된다. cd64170 1222 = `if en in _RAIL_NETS:`, 초안 서술 "종료 판정 `en in _RAIL_NETS`"와 같다. 낡은 인용이다.
* **원인**: 35~36행 "줄 번호는 gate master `7535799`(…)와 실제 B34 병합본 gate master `2183f2e`" 같은 **두 판 병기** 문장이 있다. 도구가 그 마지막 표지(2183f2e)를 30줄 아래 '범위 밖' 문단까지 이어 적용한다.
* `kit_line_shift.md` 83~84행은 표지가 번진다는 사실은 인정한다. 그러면서 "빠진 제안이고 보고서에 남는다"고 하지만, 실제로는 '이미 새 번호' 절에 '다시 옮기면 이중 이동'이라는 **반대 지시**와 함께 남는다. 사람이 그대로 따르면 낡은 인용 11건이 고쳐지지 않는다.
* 내 합성 재현: `gate master <new> archive에서 가져온 모의 base`라는 출처 문장 아래의 낡은 `SR 1300` → already-new로 나온다(adv L22·L24).
* 수정 제안:
  * 절 표지에 의한 already-new는 표지가 **같은 줄**에 있거나, 줄에 글 근거(조각·리터럴·인용 줄)가 new와 맞을 때만 준다. 그 밖은 `ambiguous(section-inherited)`로 둔다.
  * 한 문장에 판이 둘 이상인 병기 표지(`A와 … B`, `A / B`)는 절 상태를 '모름'으로 둔다.

## 4. 적대 사례 (검토자 하네스 `adv.py`, self-test와 독립)

합성 저장소에서 old → new로 다음을 바꿨다:
* SR 파일 처음에 3줄 삽입
* 1000행 교체
* 1200행 뒤 5줄 삽입
* 2001~2002행 삭제
* 끝에 2줄 추가
* SD는 100행 뒤 7줄 삽입
* 중간 판 M = 처음 3줄 삽입만 적용

| 사례 | 결과 | 판정 |
|---|---|---|
| `SR 1300` | 1308 medium, 패치. 독립 대응식과 대조한 패치 불일치 0 | 정상 |
| 이미 옮긴 `SR 1308`(표지·글 근거 없음) | 1316으로 이중 이동 | 문서(79행)가 인정한 한계 |
| `줄 번호는 <new>` 아래 `SR 1308` / `<base>` 표지로 복귀 | already-new / 다시 진행 | 정상 |
| `SR 1308 \`sr_line_1300 = 1300\``(조각 = new 1308행) | already-new | 정상(S1 수정 확인) |
| 리터럴 `{1308: b'sr_line_1300 = 1300'}` | already-new | 정상 |
| 리터럴 `{1500: b'    pass'}`(base 1500 = new 1500 글) | ambiguous | 정상 |
| 리터럴 base 일치, 바로 옆 줄에 already-new 리터럴 | ambiguous(new-value-present) | 의도대로 |
| 파일 처음 삽입 `SR 100·101` / 끝 줄 `SR 3000` / 길이 밖 `SR 3001` | 103·104 / 3006 / low | 정상 |
| 바뀐 줄 `SR 2001`, 범위 끝점이 바뀐 덩어리 안 `SR 1000~1010` | remeasure / 짝은 ambiguous | 정상 |
| **덩어리를 품은 범위** `SR 1195~1210`(사이 5줄 삽입), `SR 995~1005`(사이 1000행 교체) | 1198~1218, 998~1008 둘 다 medium **패치**, 경고 없음 | minor m1 |
| `SR 42`(두 자리) / `내용은 SR 1300.`(문장 끝 마침표) | **인식 안 함, 보고서에도 없음** | minor m2 |
| 이미 옮긴 줄에서 인용 하나만 의심되는 경우 `sizing_recipe.py 1308~1310, 1320행(\`sr_line_1300 = 1300\`)` | 1308~1310은 ambiguous인데 같은 줄 1320은 medium **패치**(1328, 이중 이동) | minor m3 |
| `SR·SD 1300` | SD에만 묶임 | minor m5 |
| `SR 1300, SD 1300`, `sizing_recipe.py:1300 과 stick_diagram.py:1300` | 각 엔진 1308·1307 | 정상 |
| `SR 1300 -> 1308`, `SR 1300 (2026-10-06 측정)` | 둘 다 ambiguous / 1300만 패치(날짜 무시) | 정상(S2 수정 확인) |
| 중간 판 표지 아래 인용 | ambiguous(`≠base·new`) | 정상 |
| CRLF 초안 | 레코드가 LF판과 같다. `git apply --check` rc 0. 적용 뒤 홑 LF 0개(CRLF 보존) | 정상 |
| CRLF 엔진 | 리터럴 high 1308, 조각 already-new | 정상(m1 수정 확인) |
| 이름 바뀐 엔진 | `git show … does not exist`로 멈춤 | 정상(문서대로) |
| textconv(`diff=weird` + `textconv`), `*.py -diff` + NUL 바이트 + `diff.external` | 1308·2506으로 올바른 대응 | 정상(S3 수정 확인) |
| 하네스 저장소 `git status` | 빈 결과 | 쓰기 없음 |

* 실제 사례 영향:
  * m1: 패치 범위 16쌍 가운데 걸친 것 0.
  * m2: 실제 초안에서 `SR|SD|*.py` 뒤 `NNNN.` 패턴 0건.
  * m3: 의심 인용과 패치가 한 줄에 같이 있는 경우는 draft_b26pre 268행 하나뿐이다. 그 줄은 실제로 old 번호라 11825→11824가 맞다.

## 5. 쓰기 범위 (요청 (4))

* 코드가 쓰는 곳은 `--out-dir`의 세 파일과 `tempfile.mkdtemp`(TMP 아래, `finally`에서 지움)뿐이다. 저장소에 대한 git 호출은 `show`·`diff`(트리 대 트리)·`rev-parse`·`cat-file -e`·`hash-object`(`-w` 없음)와 `diff --no-index`로, 모두 읽기다.
* 실측: 실제 저장소·실제 `_drafts`에 대고 돌렸을 때 초안 md5, `git status`, `_drafts` 목록이 전후 같았다. 비정상 종료(rename·Σ 단언) 뒤에도 TMP가 비어 있었다.
* 주의: `--out-dir`를 초안 디렉터리로 주는 것은 막지 않는다(사용자 책임. minor 아님).

## 6. minor

* m1 사이에 바뀐 덩어리를 품은 범위 `a~b`는 두 끝이 옮겨진 채 medium으로 패치되고 근거 칸에 표시가 없다. `span-hunk` 근거를 붙이거나 ambiguous로 둔다.
* m2 두 자리 이하 줄 번호(`SR 42`)와 문장 끝 마침표가 붙은 번호(`SR 1300.`)는 인식되지 않고 보고서에도 없다. 문서 '무엇을 인용으로 보나' 표에 적거나 `untied`로라도 남긴다.
* m3 한 줄에서 인용 하나가 already-new·'new 같은 번호' 의심이면, 같은 줄의 다른 high·medium도 ambiguous로 내리는 것이 보수적이다.
* m4 줄에 인용이 여럿일 때 조각 하나가 이웃 번호 줄(new n)과 맞으면 범위 전체가 ambiguous가 된다(268행 11823~11826, 옳은 제안을 잃음). 정밀도 손실이고 안전 문제는 아니다.
* m5 `SR·SD 1300`처럼 표지가 연달아 오면 마지막 표지에만 묶인다.
* m6 `b26v4_head.py:16` `SITE_SD_B1_MOCK`(일부러 남긴 옛 b1 번호)과 `draft_b26_1:44`의 `7535799 / 2183f2e` 병기 열의 옛 값도 already-new로 표시된다. 패치 밖이라 해는 없지만 S-B와 같은 원인의 오분류다.

## 7. 결론

* 줄 대응, S1(표지·글 근거가 있는 이중 이동), S2(단위·날짜·화살표), S3(바이너리·textconv)는 독립 사례로 고쳐졌음을 확인했다. 실제 사례 패치 127건은 글 기준 127/127 정확하다. 도구는 저장소와 초안에 쓰지 않는다.
* **적용 판단은 별개다**:
  * `draft_b26pre` 124건은 card 481행 결정과 충돌하므로 적용하지 말 것(S-A).
  * 적용 후보는 `draft_b26_1:77`의 3건뿐이다.
* draft_b26_1 65·66행의 SD 11건은 보고서가 already-new라 하지만 cd64170 번호다. 손으로 다시 재야 한다(S-B).
