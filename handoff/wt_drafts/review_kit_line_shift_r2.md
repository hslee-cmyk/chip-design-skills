# 독립 재검토 r2 -- kit_line_shift.py(r2) / .md / selftest (2026-10-06)

검토자는 도구 작성자가 아니다. 작성자의 self-test 결과와 문서 수치는 증거로 쓰지 않고 다시 쟀다.
* 모래상자 `C:/g349`(TMP/TEMP·`KLS_SB`·`KLS_OUT` 모두 그 아래)에서만 쟀고, 끝난 뒤 지웠다. `cd`는 쓰지 않았다.
* 저장소는 `git clone -c core.autocrlf=false`로 복제했다. 실제 저장소와 `_drafts`는 읽기만 했다(쓰기 범위 확인용 1회 실행, 출력은 모래상자).
* 대조 기준: `kit_line_shift.py.pre-r2.bak`(r1 판) 대 `kit_line_shift.py`(r2), selftest도 같은 방식으로 비교했다.

## 판정: **minor** (B 없음, S 없음)

* S-A·S-B·m1·m2·m3·m5·m6은 고쳐졌다. 내 독립 사례에서도 재현되지 않았다.
* 실제 사례의 패치는 `draft_b26_1:77`의 3건뿐이다. `draft_b26pre`는 0건이다. 줄 대응은 맞다.
* 기대값 변경 4건은 r1 재검토가 제안한 원칙에서 나온 것이다. 코드에 맞춰 바꾼 것으로 보지 않는다(§2).
* 남은 것은 minor 7건이다(§6). 모두 패치 밖 표시·보고 정밀도 문제이고, 틀린 패치를 만들지 않는다.

---

## 1. r1 지적별 확인 (코드 diff + 실측)

| 지적 | r2 수정 | 확인 |
|---|---|---|
| S-A measured 표지 | `measured rev/at` 표지를 `kind="measured"`로 가른다. base와 같으면 다른 강등을 다 거친 뒤 남은 high·medium을 `anchored`로 바꾼다. `이 card의`가 같은 줄에 있으면 문서 전체에 적용한다 | 실제: draft_b26pre 패치 0. r1 패치 124건 = anchored 123 + ambiguous 1(268행 line-suspect). 합성 a1·a5·a6·d1도 맞다 |
| S-B 절 표지 번짐 | 위 줄에서 이어 온 new 표지는 `section-inherited` ambiguous로 둔다. 병기(`A와 B`, `A / B`, `줄(A / B)`)는 엔진 상태가 갈리면 `section-mixed`로 둔다. 숫자만인 짧은 해시도 받는다 | 실제: r1 already-new 102 = already-new 22 + ambiguous 80. 합성 b2·b3·b6·b7도 맞다 |
| m1 범위 사이 덩어리 | `spans_change` → `span-hunk` ambiguous | 경계 7가지 확인(§3 c1). 끝 바로 뒤 삽입(1195~1200)은 패치하고, 사이 삽입·교체·삭제는 ambiguous. 맞다 |
| m2 두 자리·문장 끝 마침표 | NUM_RE를 2~5자리로 넓혔다. 두 자리는 묶였을 때만 보고하고, 글 근거가 없으면 `two-digit` ambiguous로 둔다. `1300.`도 받는다 | `SR 1300.`은 패치된다. `1300.5`·`19:35`·`외 12`·`#42`·`v12`는 인용으로 보지 않는다. 두 자리가 패치된 경우는 0이다 |
| m3 줄 의심 | `SUSPECT_PREFIXES` → `line-suspect` | c3 1행·d1에서 확인. base 조각(high)만 있는 줄은 그대로 패치되고, 과잉 강등은 없다 |
| m4 | 일부러 손대지 않음 | §5 |
| m5 `SR·SD n` | `multi:` 문맥 → `multi-engine` ambiguous | `SR·SD`, `SR/SD`, `SR, SD`, `SR SD`, `*.py·*.py:` 모두 ambiguous다. `SR와 SD 1300`만 SD로 묶여 패치된다(minor n3) |
| m6 | S-B와 같은 원인 | 실제: `b26v4_head.py:18` SITE_SD_B1_MOCK 13건과 `draft_b26_1:44` 병기 열 4건이 ambiguous다 |

selftest 재실행(모래상자):
* r2 도구: 103건 중 FAIL 0.
* r1 도구(`KLS_TOOL=…pre-r2.bak`): 103건 중 FAIL 26.
* 작성자 수치(26)와 같다. 새 시험이 옛 결함을 실제로 잡는다.

## 2. 기대값 변경 판정 (요청 핵심)

| 위치 | r1 기대 → r2 기대 | 판정 |
|---|---|---|
| d.md:53 `* SR 1205, SD 1210`(바로 위 줄 `## 근거(gate master <new> 줄 번호)`) | already-new → ambiguous | **원칙에 따른 변경.** r1 S-B 수정안("표지가 같은 줄에 있거나 글 근거가 있을 때만 already-new, 그 밖은 `ambiguous(section-inherited)`")을 그대로 적용한 결과다. 패치 밖이라는 핵심 성질은 같다. 대가: 이 줄은 실제로 이미 옮긴 인용이라 '이미 새 번호'라는 정확한 표시를 잃는다(n1). |
| d.md:54 `SITE_SD = [1014, 1571]` | already-new → ambiguous | 위와 같다. |
| d.md:59 `* SR 1200`(위 줄 `gate master <new> 재측정 -- measured rev는 <old> 그대로`) | medium 패치 → anchored | **원칙에 따른 변경이고, 옛 기대가 틀렸다.** 문장 자체가 '측정 rev는 old 그대로'라고 선언한다. 이것은 draft_b26pre 481행 결정과 같은 구조다. 옮기면 card가 자기모순이 된다(r1 S-A). 도구 문서의 원칙("측정 기록 줄은 바꾸지 않는 것이 기본(anchored)")과도 맞는다. |
| S1 재실행 단언(`줄 번호는 <new>` 다음 줄 `SR 1205`) | `already-new 존재` → `already-new 또는 ambiguous이고 section-rev·section-inherited 근거` | 이중 이동 0이라는 핵심 단언은 같다. 다만 OR로 **느슨해졌다.** 이 경우 r2의 결과는 ambiguous(section-inherited) 하나로 정해져 있으므로, 그 값으로 고정하는 것이 맞다(n6). |

* 새로 넣은 `r2 m6.py L2 1576`(new 표지 아래, 실제로 new 번호인 대입 → ambiguous 기대)도 같은 S-B 대가를 시험으로 고정한 것이다. 일관성은 있다.
* 기대값 변경의 출처는 작성자 자신이 아니라 독립 검토(r1)가 낸 수정 원칙이다. 변경은 모두 '패치하지 않음'을 지키는 방향이다. 패치를 새로 허용한 기대값 변경은 0건이다.

## 3. 검토자 적대 사례 (`adv.py`, 작성자 selftest와 독립)

합성 저장소: old → new로 SR은 처음 3줄 삽입, 1000행 교체, 1200행 뒤 5줄 삽입, 2001~2002 삭제, 끝 2줄 추가. SD는 100행 뒤 7줄 삽입.
중간 판 M은 SR 처음 3줄 삽입만 적용했다. N2는 엔진 blob이 N과 같은 다른 커밋이다.

| 사례 | 결과 | 판정 |
|---|---|---|
| a1 `measured at <old> -- 이 card의 계약 7 기준선…`(줄 인용 얘기 아님) | 앞·뒤 인용 모두 anchored(문서 전체) | 과잉 보수. 패치 밖이라 안전하다(n4) |
| a2 `Measured rev: <old>`(대문자 M) | **표지 미인식** → medium 패치 | minor n2 |
| a3 measured = 중간 판 | ambiguous(≠base·new) | 정상 |
| a4 measured = new: 아래 줄 / 같은 줄 | ambiguous(inherited) / already-new | 정상 |
| a5 문서 전체 measured(old) 뒤 `줄 번호는 <new>` 절 / `줄 번호는 <old>` 절 | ambiguous / anchored | 정상 |
| a6 한 줄에 `gate master <new> 줄 번호 -- measured rev는 <old>` | anchored(measured 우선) | 정상 |
| a7 measured(old) 절 뒤 `줄 번호는 <old>` 새 절 | medium 패치 | 문서의 '다음 표지까지' 규칙과 맞다 |
| b1 같은 줄 출처 설명 `모의 base = gate master <new> archive, 낡은 인용 SR 1300` | already-new(거짓) | 같은 줄 표지는 여전히 already-new다. 패치 밖이라 안전하다. 표시만 틀린다(n5) |
| b2 `줄 번호는 <old>와 <new>` 아래 | section-mixed ambiguous | 정상 |
| b3 `<new> / <N2>`(둘 다 new 상태): 아래 줄 / 같은 줄 | inherited ambiguous / already-new | 정상 |
| b4 `줄 번호는 <old>, 그리고 <M>`(병기 아님) | base로 보고 패치 | 정상(병기 정규식이 넘치지 않는다) |
| b5 `줄 번호는 <old>` 뒤 빈 줄, 그 아래 인용 | 패치 | 정상(base 표지는 이어 받아도 진행한다) |
| b6 표 머리 `줄(<old> / <new>)` 아래 `SR 1300 / SR 1308` | 둘 다 mixed ambiguous | 정상 |
| b7 new 표지 12줄 아래 다른 문단 | inherited ambiguous | 정상(r1 S-B 재현이 사라졌다) |
| c1 `1199~1202`, `999~1001`, `SD 95~105`, `1999~2004`, `2000~2003` | span-hunk·year-like ambiguous | 정상 |
| c1 `1201~1210`, `1195~1200`(끝 바로 뒤 삽입), `SD 101~110` | 1209~1218, 1198~1203, 108~117 패치 | 정상(경계에서 한 칸씩 어긋나는 오류 없음) |
| c1 `SR 1~5` | 기록 없음 | 한 자리는 기존부터 범위 밖이다. 문서에는 2자리 이상이라고 적혀 있다 |
| c2 `SR 1300(19:35 측정)`, `외 12`, `(PR #42)`, `v12`, `Python 3.14` | 1300만 패치, 나머지는 기록 없음 | 정상(두 자리 확장이 새로 거짓 인용을 만들지 않는다) |
| c2 `SD 50`, `SR 99`, `SR 1300, 42`, `SR 12~15` | 두 자리는 two-digit ambiguous, 1300은 패치 | 정상 |
| c3 `SR 1308 \`sr_line_1300 = 1300\`, SR 1500` / base 조각이 있는 같은 꼴 | 1500 line-suspect / 1500 패치 | 정상 |
| c5 `SR와 SD 1300` | **SD로 묶여 패치** | minor n3 |
| d1 measured(old) + 의심 줄 | 의심 근거 보존, anchored로 덮이지 않음 | 정상(강등 순서가 맞다) |
| 패치 25건 대응 대조(검토자 대응식) | 불일치 0 | 정상 |
| `git apply --check` | rc 0 | 정상 |
| `--include-anchored` | measured anchored만 더 패치된다(a1·a5·a6·a7…) | 문서와 같다. 해시 앵커와 한 스위치로 묶여 있다(n4) |
| 초안 md5, 합성 저장소 `git status`, TMP 잔여 | 같음 / 같음 / 비어 있음 | 쓰기 없음 |

## 4. 실제 사례 재실행 (old 7243f28 → new 2183f2e)

* 모의 `b1` 재생성: md 절차대로 했다(`git archive 2d58fd8` → `mk_b1.py` 등 3개를 경로만 `C:/g349`로 바꿔 실행). 9024에서 9016줄이 됐다.
* **주의 -- 초안이 r2 산출 뒤에 바뀌었다.**
  * `draft_b26_1.spec.md`가 20:58에 바뀌었다(77행에 `` (`2183f2e` 3534·3536·3694) `` 병기, 65~67·501·542행 보강).
  * `draft_b26pre.spec.md`(21:06)와 `b26pre_launch.sh`(21:11)도 검토 중에 오케스트레이터 쪽에서 바뀌었다. 도구 실행 전후의 디렉터리 목록 해시가 같으므로 도구가 바꾼 것은 아니다.
  * 그래서 두 가지로 쟀다:
    * (B) `draft_b26_1`만 `.pre-cite.bak`(병기 전)으로 바꾼 사본: **records 473, 패치 3, already-new 22.** 저장된 `kit_line_shift_b34real/r2/`와 패치가 바이트 단위로 같고, 레코드 473/473이 같다. 도구 파일(20:50 수정)이 r2 산출(20:48)보다 늦지만 결과는 같다.
    * (A) 현재 초안: records 487, **패치 0.** 77행의 3559·3561·3719는 같은 줄의 `2183f2e` 해시 때문에 anchored가 된다. 병기를 단 뒤 다시 돌려도 이중 이동이 없다.
* **패치 = `draft_b26_1:77` SD 3559·3561·3719 → 3534·3536·3694의 3건뿐이다.**
  * medium인데 패치되지 않은 5건(12·77·501·504행 SR)은 이동이 0이다(SR 줄은 p0와 new에서 같다).
* **draft_b26pre: 패치 0.**
  * r1 패치 124건 = anchored 123 + ambiguous 1. 근거는 `measured-rev(dd60db6 @L483, 문서 전체)≡base`다.
  * 문서 전체 선언 줄이 지금 card에서는 483행이다. md에는 464행으로 적혀 있다(n7).
* **already-new 22** = 같은 줄 section-rev 14(draft_b26_1 16행), `>` 인용 4, 리터럴 4. md 주장과 같다.
* **재분류 80건**(r1 already-new → ambiguous; 줄이 밀린 파일은 문맥으로 맞춤, 빠진 것 0):
  * 근거: section-inherited 56, section-mixed 24.
  * 파일: backfill_audit 28, draft_b26_1 26, b26v4_head 26.
* **무작위 15건 엔진 글 대조**(seed 349):

| 묶음 | 표본 | 엔진 글로 본 실제 판 | 판정 |
|---|---|---|---|
| `b26v4_head:17` SITE_SD_B1 4298·4367·1612 | 3 | **2183f2e 번호다**(2183f2e 1612 = `if t.source in _RAIL_NETS:`, b1 1612 = `for t in transistors:`) | r1 already-new가 맞았다. r2는 표시를 잃었다(패치 밖) |
| `draft_b26_1:52` 2343·2344·3907 | 3 | **2183f2e 번호다**(2183f2e 2343~2344·3907~3908 = B34가 고친 docstring `… is None 분기는 도달 불가`. p0 같은 번호는 다른 글). 줄 안에 `` (`2183f2e` 줄) ``이 있지만 표지 정규식(`줄 번호`·`줄은`)에 걸리지 않는다 | 위와 같다 |
| `backfill_audit:59` 11802 | 1 | **2183f2e 번호다**(14행 `gate master 2183f2e 줄 번호` 절. 2183f2e 11802 = `return {…`, 7243f28 11802 = `_finalize(…)` 줄) | 위와 같다 |
| `b26v4_head:18` SITE_SD_B1_MOCK 3133·2092·1571 | 3 | **낡은 b1 번호다**(b1 1613 = `if t.source in _RAIL_NETS:`). 도구 새 값 3130·2090·1570 = 17행 실측값과 같다 | r1 거짓 분류가 바로잡혔다 |
| `draft_b26_1:65` 1281·1270 | 2 | **낡은 cd64170 번호다**(r1 확인). 도구 새 값 1276·1265 = card가 20:58에 단 병기 값과 같다 | 바로잡혔다 |
| `draft_b26_1:67` SR 4653·4626, `b26v4_head:17` 1014 | 3 | 이동 0 | 무해 |

  * 판정: 15건 모두 패치 밖이므로 안전하다. 그 가운데 5건은 r1의 거짓 already-new가 바로잡혔다.
  * 7건은 r1 already-new가 맞았는데 r2에서 ambiguous로 내려갔다. 이것은 S-B 수정의 예상된 대가다.
  * 문제는 이 7건의 '모호' 표 새 값(예 1612→1611, 2343→2337, 11802→11801)이 **이중 이동 값**이라는 점이다(n1).
  * 전체 80건 가운데 이렇게 실제로 이미 새 번호인 것은 backfill_audit 28, SITE_SD_B1 13, draft_b26_1 52·44행 일부로, 절반 이상이다.

## 5. m4 생략 판단

* m4는 정밀도 손실이다. 줄에 인용이 여럿이고 조각이 이웃 번호 줄과 맞으면, 옳은 제안까지 ambiguous가 된다. 틀린 패치는 만들지 않는다.
* 실제 유일 사례(draft_b26pre 268행)는 r2에서 S-A로 어차피 anchored 대상이 됐다. m3 규칙도 같은 방향(보수)이다.
* **생략은 받아들일 만하다.** 다만 md 신뢰도·글 대조 절에 "줄에 인용이 여럿이면 옳은 제안도 ambiguous가 될 수 있다(r1 m4, 보수 방향으로 둔다)"는 한 줄이 있으면 좋다.

## 6. minor (모두 패치 밖 표시·문서 문제. 틀린 패치 0)

* **n1** '모호' 표의 새 값은 언제나 base→new로 옮긴 값이다.
  * `section-inherited`·`section-mixed`이고 표지가 new인 경우, 그 인용이 실제로 이미 새 번호이면 표의 새 값은 이중 이동 값이다. 실제 사례 80건 중 절반 이상이 그렇다(§4).
  * md는 "손으로 다시 재야 한다"고 하지만, 표가 한 값만 보여 주면 그 값을 옮겨 적게 된다.
  * 수정 제안: 이 두 근거일 때 표에 `그대로(이미 new일 때)`/`<새 값>(base일 때)` 두 판독을 함께 적는다.
* **n2** measured 표지 정규식이 대소문자를 가린다. `Measured rev: <old>`는 표지로 읽지 않아 그대로 패치된다. `re.I`를 쓰거나 문서에 소문자만 받는다고 적는다.
* **n3** `SR와 SD 1300`(`와`·`과`·`및`)은 multi-engine으로 잡히지 않고 SD로 묶여 패치된다. `SR·SD`·`SR/SD`·`SR, SD`·`SR SD`는 잡힌다.
* **n4** 두 가지가 과잉 보수다:
  * 문서 전체 선언 판정은 `measured …`와 `이 card의`가 같은 줄에 있기만 하면 된다. 줄 인용 얘기가 아닌 문장(a1)에서도 card 전체를 anchored로 만든다.
  * `--include-anchored`는 measured 앵커와 해시 앵커를 한 스위치로 함께 푼다.
  * 둘 다 안전 방향이다. 다만 measured를 선언한 card를 새로 앵커하려면 해시 앵커까지 함께 풀어야 한다.
  * 같은 줄에 해시가 있는 병기(현재 draft_b26_1:77)는 `--include-anchored`로 다시 돌리면 `SD 3534·3536·3694(\`2183f2e\` 3534·3536·3694)`가 된다. 표지 없는 병기 숫자는 new-value-present가 보지 못하기 때문이다.
* **n5** 같은 줄의 출처 설명 표지(`모의 base = gate master <new> archive, … SR 1300`)는 여전히 already-new(거짓)다. r1이 받아들인 경계(같은 줄)이고 패치 밖이다. md '주의'에 같은 줄 예외를 한 줄 적으면 충분하다.
* **n6** selftest의 S1 재실행 단언이 `already-new 또는 ambiguous`로 느슨해졌다. r2에서 기대되는 결과는 `ambiguous(section-inherited)` 하나다. 그 값으로 고정해야 다음 판에서 같은 줄/이어 온 표지 구분이 다시 무너지는 것을 잡는다.
* **n7** md 실사례 절이 낡았다:
  * 결과(473/3/22)는 draft_b26_1 병기 전 사본 기준이다. 현재 초안으로 돌리면 487/0/34다. 측정한 초안 시점(또는 `.pre-cite.bak`)을 밝힌다.
  * draft_b26pre 문서 전체 선언 줄은 지금 464행이 아니라 483행이다.

## 7. 쓰기 범위

* 코드 diff상 새 쓰기 경로는 없다(`--out-dir` 세 파일과 TMP 아래 `mkdtemp`).
* 실측 결과:
  * 실제 저장소·실제 `_drafts`에 대고 1회 돌렸다(출력은 `C:/g349/out_real`). `git --no-optional-locks status --porcelain` 해시와 `_drafts` 목록(mtime 포함) 해시가 전후 같았다.
  * 모래상자 TMP에 남은 파일은 0이다.
  * 합성 저장소 status와 초안 md5도 전후 같았다.
  * 실행 중 바뀐 b26pre 두 파일은 실행 전에 바뀐 것이다(mtime 21:06·21:11 < 실행 21:13).
* 모래상자 `C:/g349`는 측정 뒤 지웠다.

## 8. 결론

* r2는 S-A·S-B를 원칙대로 고쳤다. m1·m2·m3·m5·m6도 독립 사례로 확인했다. 실제 사례에서 패치는 `draft_b26_1:77`의 3건뿐이고 draft_b26pre는 0건이다.
* 기대값 변경 4건은 검토 원칙에서 나온 보수 방향 변경이다. 끼워 맞춘 것이 아니다. d.md:59의 옛 기대는 틀렸었다.
* 다만 S1 단언의 OR 완화(n6)는 다시 고정하는 것이 좋다.
* 남은 것은 표시 정밀도와 문서 문제(n1~n7)다. 가장 쓸모 있는 후속은 n1(모호 표의 두 판독 표시)과 n7(실사례 절 시점 명시)이다.
* draft_b26_1:77은 이미 병기가 반영됐다. 따라서 B34 실사례에서 이 도구로 더 적용할 패치는 없다.
