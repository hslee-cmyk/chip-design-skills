# kit_line_shift.py -- 병합 뒤 엔진 줄 인용 이동 제안

card가 병합되어 엔진 파일(SR `sizing_recipe.py`, SD `stick_diagram.py`)의 줄이 밀리면, 옛 rev에서 잰 초안·키트의 줄 인용을
새 rev 줄로 옮기는 **제안**(patch + 보고서)을 만든다. **초안은 고치지 않는다.** 저장소는 읽기만 한다.

## 실행

```bash
export TMP=/c/gNNN/tmp TEMP=/c/gNNN/tmp          # 임시 파일(새 rev 엔진 사본)은 TMP 아래, 끝나면 지운다
python kit_line_shift.py \
  --repo <저장소> --old <초안이 잰 rev> --new <병합 rev> \
  --engine SR=skills/analog-gmid-design/assets/sizing_recipe.py \
  --engine SD=skills/analog-gmid-design/assets/stick_diagram.py \
  [--base NAME=LABEL:SRC[,LABEL:SRC]] \        # 다른 base. SRC = git rev 또는 로컬 파일. 빠진 LABEL은 --old
  --drafts-root <초안 루트> --out-dir <출력> \
  --draft PATH[@BASE][:LINES] ...               # 같은 PATH를 여러 번: 나중 항목이 그 줄의 base를 덮어쓴다
  [--include-bare] [--include-anchored] [--show-unchanged] [--foreign 낱말 ...]
```

출력(`--out-dir`): `kit_line_shift.patch`(3줄 문맥 unified diff, `a/<PATH>`; 초안 루트에서 `git apply --check` 뒤 사람이 적용),
`kit_line_shift.report.md`(file:line·엔진·base·옛 인용·새 인용·신뢰도·패치 여부·근거), `kit_line_shift.json`(덩어리·전 레코드).

자기 시험: `python kit_line_shift_selftest.py`
* 무엇을 돌리나: 검토 `review_kit_line_shift.md`의 최소 재현 전부(S1·S2·S3·m1~m9)와 재검토 `review_kit_line_shift_r1.md`의 재현(S-A·S-B·m1·m2·m3·m5·m6, r2에서 더함).
* 어디서: 모래상자 `KLS_SB`(기본 `C:/g340/st`, TMP/TEMP 포함, 끝나면 삭제)의 합성 저장소.
* 결과: `KLS_OUT`(기본 `kit_line_shift_selftest.out.txt`)에 쓴다. FAIL이 있으면 rc 1.
* 다른 판 도구를 시험하려면 `KLS_TOOL=<경로>`를 준다.
* 시험이 결함을 실제로 잡는지 옛 판으로 확인했다:
  * r1 판(`kit_line_shift.py.pre-r2.bak`): 103건 중 26건 FAIL.
  * r0 판(`kit_line_shift.py.pre-r1.bak`): r1 시험 70건 중 37건 FAIL.
* r2에서 기대값을 바꾼 옛 시험은 네 개다. 이유는 아래 '이미 옮긴 인용'(S-A·S-B)에 있다.
  * d.md:53·54, S1 재실행: already-new → ambiguous(section-inherited). 둘 다 패치 밖이다.
  * d.md:59: medium 패치 → anchored.

## 줄 대응

엔진 파일마다 `git diff --text --no-textconv --no-renames -U0 <base> <new> -- <path>`(로컬 파일 base는 `git diff --no-index` 같은 옵션)의
덩어리로 old -> new. 바뀐 덩어리 안의 줄은 `remeasure`(None) -- 손으로 다시 잰다.
* `--text --no-textconv`: `.gitattributes`의 `-diff`·NUL 바이트로 바이너리 판정되거나 textconv가 걸려도 덩어리를 읽는다.
* 덩어리 Σ(추가−삭제) ≠ new 줄 수 − base 줄 수이면(덩어리를 빠뜨림) **멈춘다**(SystemExit). 조용한 항등 대응은 없다.
* **이름이 바뀐 엔진은 지원하지 않는다.** new 경로가 base에 없으면 `git show` 실패로 멈춘다(이름 변경 추적 없음).
* 엔진·초안 줄은 `\n`으로만 나눈다(CRLF의 `\r`은 대조 때 뗀다. U+2028·`\x0c`·`\x85`에서 쪼개지 않는다 -- git·편집기 줄 번호와 같다).
  파일 길이는 git이 세는 줄 수다(끝 개행 뒤 빈 원소를 세지 않는다).

## 무엇을 인용으로 보나(보수적)

| 종류 | 예 | 처리 |
|---|---|---|
| 표지 + 숫자 목록 | `SR 11800·11879`, `A/sizing_recipe.py:11784~11786`, `stick_diagram.py 1507~1509(…)·1539`, `내용은 SR 1300.`(문장 끝 마침표) | 묶음(marker). 사이에 허용하는 것: 구분자, 한글 없는 백틱, 3자리 이상 숫자 없는 괄호. 범위 `a~b`는 두 끝이 함께 패치될 때만 패치한다. 사이에 바뀐 덩어리가 있으면 `span-hunk` ambiguous(r2 m1) |
| 두 자리 수 | `SR 42`, `SD 18, SR 2` | 표지·리터럴에 묶였을 때만 인용으로 본다. 글 근거(리터럴·조각 high)가 없으면 `two-digit` ambiguous로 보고만 한다(개수일 수 있다). 두 자리 + 단위(`12개`)는 보고하지 않는다(r2 m2) |
| 표지가 연달아 | `SR·SD 1300` | 어느 엔진인지 모른다 -> `multi-engine` ambiguous. 엔진마다 계산한 값을 근거 칸에 적는다(r2 m5) |
| 스크립트 리터럴 | `exp={11800:b'        _backfill_interdig_ok(result)', …}`, `{42: b'…'}` | base 그 줄 글과 같아야 묶음(high). 두 엔진 base 줄과 다 같으면 ambiguous |
| 스크립트 대입 | `SITE_SD_B1 = [1014, 1571, …]` | 이름 토큰(SD)으로 엔진, 토큰(B1)이 --base 이름이면 그 base |
| 단위가 붙은 수 | `130줄`, `133개`, `2026년`, `100%`, `512 MB`, `300 tests`/`passed`, `9016행 수` | 인용 아님. 표지에 묶였으면 `unit(…)` ambiguous로 보고만 하고 목록을 끊는다 |
| 날짜·앞 0·소수·버전 | `2026-10-06`, `2026/10/06`, `01200`, `3.14159`, `SR 1300.5`, `1300.py`, `v1.2.300`, `0x1234`, `1,200` | 인용 아님 |
| `a → b` 쌍 | `SR 1200 → 1205`, `9024→9016줄`, `1200->1205` | 둘 다 `arrow-pair` ambiguous(옛·새를 함께 적은 것) |
| 하이픈 범위 | `SR 1200-1210` | 두 끝 다 `hyphen-range` ambiguous(시작 수도 보고서에 남는다) |
| 연도 꼴 수 | `SR 2026` | 19xx·20xx이고 글·def 근거가 없으면 `year-like` ambiguous |
| 경로 조각의 base 이름 | `` `C:/g83/b1/skills/a/stick_diagram.py:1200` `` | 경로 안 `b1`은 base 표지가 아니다(base를 바꾸지 않음). 배정 base가 아니면 `path-mentions-base` ambiguous |
| 표지 줄의 끊긴 숫자 | `sizing_recipe.py … 인용 줄(11758~11881, …)` | `untied` -- 그 줄 엔진이 하나면 값만 계산, 패치 밖 |
| 표지 없는 숫자 | `루프 안(11800)` | `bare` -- 이번 실행의 묶인 인용과 번호가 같을 때만 제안, 패치 밖(--include-bare로 포함) |
| 다른 base 표지 | `SD 1567(b34 1563)`, `b1 2491` | `other-base` -- 앞 인용의 새 값을 힌트로, 패치 밖 |
| 커밋·blob 해시가 있는 줄 | `(sizing_recipe.py 9363~9367, a796468)` | `anchored` -- 측정 기록일 수 있다. 해시가 base와 같은 blob인지(≡/≠) 적고 패치 밖(--include-anchored로 포함) |
| 다른 파일:줄 | `test_selftest_sizing_recipe.py:1480` | 무시 |

## 이미 옮긴 인용(already-new -- 이중 이동 방지)

다음이면 `already-new`(또는 ambiguous)로 보고하고 패치에서 뺀다(보고서 '이미 새 번호' 절).
* **절 표지**는 두 종류다.
  * 줄 번호 표지: 줄 안의 `<rev> 줄 번호`, `줄 번호는 <rev>`·`줄은 <rev>`, `gate master <rev>`(백틱 유무 무관), 표 머리 `줄(<A> / <B>)`.
  * measured 표지: `measured rev는 <rev>`·`measured at <rev>`.
  * 숫자만인 짧은 해시(`7535799`)도 받는다. 커밋이 아니면 버린다.
* 표지가 있는 줄과 그 아래 줄은 다음 표지까지 그 표지를 따른다.
  * 한 줄에 measured 표지가 있으면 그것이 그 줄의 표지다(예 `gate master 2183f2e … measured rev는 dd60db6` -> dd60db6).
  * measured 표지가 없으면 그 줄의 rev 전부를 모은다. 표지 바로 뒤 병기 `` `A` / `B` ``·`A·B`·`A와 B`도 함께 모은다.
* 엔진마다 표지 rev의 blob을 base·new와 비교한다:
  * **같은 줄** 표지가 new와 같으면 already-new다(`section-rev(..)=new`).
  * **위 줄에서 이어 온** 표지가 new와 같으면 already-new가 아니라 high·medium -> ambiguous(`section-inherited(.. @Lk)=new`)다(r2 S-B).
    표지가 이 인용을 실제로 다스리는지 모르기 때문이다. 출처 설명 문장('모의 base = gate master X archive')이나 병기 문장이 아래 문단으로 번진다.
  * rev가 여럿이고 엔진 상태가 갈리면(`줄 번호는 7535799와 2183f2e`, `줄(7535799 / 2183f2e)`) 그 줄과 아래 줄의 high·medium -> ambiguous(`section-mixed`)다.
  * base·new 어느 쪽과도 다르면 ambiguous(`section-rev(..)≠base·new`)다.
  * 줄 번호 표지가 base와 같으면 그대로 진행한다(`section-rev(..)≡base`).
* **measured 표지가 base와 같으면 anchored다(r2 S-A).**
  * 그 아래 인용은 측정 rev를 밝힌 기록이다. card가 일부러 옮기지 않는 표·인용이므로 패치 밖에 둔다(`measured-rev(.. @Lk)≡base`, `--include-anchored`로만 패치).
  * 같은 줄에 `이 card의`·`이 문서의`가 있으면 **문서 전체** 선언으로 본다. 표지보다 앞 줄과, 줄 번호 표지가 base인 절에도 적용한다.
    예: draft_b26pre 464행 `**measured at dd60db6** … 이 card의 줄 인용은 그대로다`.
  * 다른 강등(line-mentions-base·new-value-present·line-suspect·range-partner)을 먼저 다 거친다. 그 뒤에도 high·medium일 때만 anchored로 바꾼다.
    그래서 `--include-anchored`로도 그 보호는 그대로다.
* **글 대조**: 같은 줄 코드 조각, 또는 인용 줄 바로 아래 `>` 인용 줄(범위 길이와 줄 수가 같으면 줄마다 대조)이 base 그 번호 줄이 아니라
  **new 그 번호 줄**과 맞는다. 리터럴 줄 글도 같다. 줄에 인용이 여럿이면(조각이 이웃 줄을 가리킬 수 있다) already-new 대신 ambiguous.
  base·new 같은 번호 줄 둘 다와 맞으면 ambiguous.
* **새 값이 곁에 있다**: 같은 줄에 그 새 값이 already-new·other-base 인용으로 이미 있거나(`SD 1567(b34 1562)`), 바로 옆 줄에
  already-new 리터럴이 있다(`{새} if 새 판 else {옛}`) -> ambiguous(`new-value-present`).
* **줄에 의심 인용이 있다**(r2 m3): 한 줄의 인용 하나가 이미 옮긴 것으로 의심되면, 같은 줄의 다른 high·medium도 ambiguous(`line-suspect`)로 내린다.
  의심의 근거는 already-new, 조각·`>` 인용·리터럴이 new 줄과 맞음, new-value-present다.

## 신뢰도

**high** = 리터럴 줄 글이 base 그 줄과 같음 / 같은 줄 코드 조각(식별자 하나짜리는 근거 아님, 따옴표·괄호 무시)이 base 그 줄과 맞음 /
`>` 인용 줄이 base 줄과 맞음. **medium** = 글 근거 없음(이동만. 이름 붙은 def 범위 안이면 근거에 `def-ok`를 적지만 high로 올리지 않는다 --
같은 def 안에서 k줄 어긋난 것을 가리지 못한다). **low** = base 파일 길이 밖·표 행의 코드 조각·리터럴이 base 줄과 다름(base가 틀렸을 가능성).
**already-new**·**ambiguous**·**anchored**·**remeasure** = 위. 패치에는 high·medium만 들어간다.
줄에 배정 base 아닌 base 표지(`b34`·`B34 사본`·`모의`, 다른 --base 이름)가 있으면 medium은 ambiguous로 내린다.

## 주의

* **이미 옮긴 초안에 다시 돌리지 않는다.** 절 표지·글 대조가 잡지 못하는 인용(표지도 글도 없는 `SR 1205`)은 다시 옮겨진다.
  다시 돌려야 하면 다음 셋 중 하나를 한다:
  * 옮기기 전 사본(.bak)을 `--drafts-root`로 준다.
  * 옮긴 절에 `줄 번호는 <new rev>` 표지를 적는다. 아래 줄은 ambiguous(section-inherited)가 되어 패치에서 빠진다.
  * 옮긴 줄 안에 표지를 적는다. 그 줄은 already-new다.
* **base를 정확히 줘야 한다.** 초안마다 측정 rev가 다르다(예: B26-1 card는 `cd64170` 기준, 사이트 줄은 모의 `b1` 기준). 초안의
  '줄 번호는 <rev>' 문장을 보고 `@BASE`·`:LINES`로 배정한다. 절 표지와 배정 base가 어긋나면 도구는 ambiguous로 내릴 뿐 base를 바꾸지 않는다.
* 절 표지는 '다음 표지까지' 이어진다. `gate master <rev>`가 줄 번호가 아니라 출처 설명인 문장(예 '모의 base b1 = gate master `2d58fd8` archive')도 표지로 읽는다.
  * 그 아래 인용은 ambiguous로 빠질 수 있다. 이것은 보수 방향이다. 틀린 패치가 아니라 빠진 제안이고, 보고서 '모호' 절에 새 값과 함께 남는다.
  * r2부터 이어 온 표지로는 already-new를 주지 않는다. 그래서 보고서가 '다시 옮기면 이중 이동'이라는 반대 지시를 내지 않는다.
  * '모호' 절의 `section-inherited`·`section-mixed` 인용은 손으로 다시 재야 한다(B26-1 예: `_drafts/b26_1_cite_check.md`).
* 측정 기록(measured 표지, 해시 앵커, `a..b에서 다시 읽어 확인`) 줄은 바꾸지 않는 것이 기본이다(anchored). 측정 rev를 새로 앵커할 때만 `--include-anchored`로 함께 고친다.
* 줄 번호 표지(`줄 번호는 <old>`) 아래 인용을 패치로 바꾸면, 그 표지 문장도 함께 고치거나 새 번호를 병기해야 한다. 표지는 도구가 고치지 않는다.
* 스크립트 **동작 조건**(예: `diff --quiet M H -- SR`가 B34 docstring 때문에 멈춤, `ALLOW_SR`)은 줄 번호가 아니라 이 도구 범위 밖이다.

## 실제 사례(B34 병합, 2026-10-06)

```bash
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
python kit_line_shift.py --repo $R --old 7243f28 --new 2183f2e \
  --engine SR=skills/analog-gmid-design/assets/sizing_recipe.py --engine SD=skills/analog-gmid-design/assets/stick_diagram.py \
  --base b1=SD:<b1>/skills/analog-gmid-design/assets/stick_diagram.py --base p0=SD:cd64170 \
  --drafts-root . --out-dir kit_line_shift_b34real/r2 \
  --draft draft_b26pre.spec.md --draft b26pre_launch.sh --draft draft_b26_backfill_audit.spec.md --draft b26_backfill_briefs.md \
  --draft backfill_launch.sh --draft draft_b26_1.spec.md@p0 --draft draft_b26_1.spec.md@b1:16,149 --draft b26_1_launch.sh \
  --draft b26_scripts/b26v4_head.py@b1 --draft post35_kit/p35_heads.py
```

`<b1>`(모의 base, SD만 다름) 재생성: `git -C $R archive 2d58fd8 | tar -x -C <G>/g83/b1`, `b26_scripts/{sim_head,v3_scope_classify,mk_b1}.py`를
`<G>/scripts`에 복사해 `C:/g83`→`<G>/g83`, `…/_drafts/b26_scripts`→`<G>/scripts`로 바꾼 뒤 `python mk_b1.py`(9024→9016줄; SD @ b1 덩어리 18개).
SR·SD blob은 `c851e54`와 `2183f2e`에서 같다.

결과(세 디렉터리):
* `kit_line_shift_b34real/validation_snapshot/`: 2026-10-06 18:03 오케스트레이터 수정 **전** 초안 사본 기준. r0 판 도구.
* `kit_line_shift_b34real/current/`: r1 판 도구(2026-10-06 19:35).
  * 결과는 records 471, 패치 127건(draft_b26pre 124, draft_b26_1 3), already-new 102다.
  * **이 패치는 적용하지 말 것.** draft_b26pre 124건은 card 481행 결정('측정 rev를 밝힌 표·인용이라 옮기지 않는다')과 충돌한다(재검토 S-A).
  * already-new 102건 가운데 80건은 절 표지 번짐으로 생긴 거짓 분류다(재검토 S-B).
* `kit_line_shift_b34real/r2/`: **r2 판 도구, 현재 초안**(2026-10-06). 결과는 records 473, 패치 3, already-new 22다.
  * 패치 = `draft_b26_1.spec.md` 77행 SD 3559·3561·3719 → 3534·3536·3694의 3건뿐이다.
    * 대응 글은 같다(`propose_theta_kcl_gap_fill` 레일 판정).
    * 이 줄은 15·71행의 'cd64170 줄' 선언 아래에 있다. 그래서 바꿔 쓰기보다 `` (`2183f2e` 3534·3536·3694) `` 병기가 card 규칙과 맞다(`b26_1_cite_check.md` 교체안 2).
  * **draft_b26pre는 패치 0건이다.** 464행 문서 전체 measured 선언(dd60db6 ≡ base)에 따라 r1 패치 124건은 다음과 같이 나뉜다:
    * 123건 anchored.
    * 1건(268행 11825) ambiguous(`line-suspect`, m3 보수 규칙).
  * r1의 already-new 102건은 다음과 같이 바뀌었다:
    * 22건 already-new 유지: 같은 줄 표지 14, `>` 인용·리터럴 글 대조 8.
    * 80건 ambiguous(`section-inherited`·`section-mixed`).
    * draft_b26_1 65~67행 SD·SR 인용은 `section-mixed(2183f2e/7535799 @L38)`로 '모호' 절에 새 값과 함께 남는다. 실측 판정은 `b26_1_cite_check.md`에 있다.
    * m6 대상(`b26v4_head.py` 18행 `SITE_SD_B1_MOCK`, draft_b26_1 44행 병기 열)도 ambiguous다.
  * r1 대비 레코드 증가 2건:
    * draft_b26_1 67행 `SR 4086·4991.`의 4991(문장 끝 마침표, m2).
    * 503행 `SD 18`(두 자리, `two-digit` ambiguous).
  * `git apply --check -p1` 통과(사본).
