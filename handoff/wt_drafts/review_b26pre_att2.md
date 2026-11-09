# 독립 검토 -- b26pre 2차 시도 준비(draft_b26pre.spec.md · b26pre_briefs.md · b26pre_launch.sh · phase3_runbook.md §4)

검토자 = 작성자 아님. gate master `6c724de`(실제 저장소 읽기 전용), 모래상자 `/c/g356`만 사용(TMP·TEMP 그 아래, clone `-c core.autocrlf=false`, cd 없음, 끝에 삭제).
대조 기준 = 각 `*.pre-att2.bak`. 오케스트레이터 시제품(`b26pre_att2_scripts/proto_att2_NOT_FOR_ROLES.py`)은 열지 않았고, 시제품은 개정 card 문장만 보고 내가 새로 썼다(`/c/g356/proto`, 19 test).

## 판정: **B 0 · S 1 · minor 6** -- S1을 고치면 착수해도 된다

## 1. 계약 1 (d) 리터럴 -- 확인됨
* 내 스크립트로 card 계약 1 입력을 base `6c724de` 엔진에 넣었다(`PYTHONHASHSEED` 0·1·7·123·42). 다섯 seed 모두 같다:
  `{t.stack_id for t in pr["transistors"]}` = `{"pair_row_repair0_repair0_repair0"}`(Ma·Mb 둘 다, n_fingers 1), `repaired_rows` 키 = 같은 한 개, (a) 세 조건 참, `audit_ok` False, 3c 체크 1개(`3c. common-centroid[Ma/Mb]`) ok False, 소자 이름 `["Ma","Mb"]`.
* max_iter 설명: 같은 두 소자 행을 `repair_matching_safety`에 바로 넣으면 max_iter 1·2·3·4·5 → 접미 `_repair0`이 1·2·3·4·5번, 기본값 → 3번. 소스 확인: 시그니처 `max_iter: int = 3`, 루프 `for _ in range(max_iter)`, 폴백 호출부(SR 9403)는 max_iter를 안 넘긴다. '진행 없으면 조기 종료' 단서에 걸리지 않음(매 반복 재배치가 일어남). card 설명 맞다.
* 인용 줄 `stick_diagram.py 7523`·`7532`·SR `9408~9412`는 card가 정한 `dd60db6` 판 번호로 맞다(6c724de에서는 7509·7518·9408). card 머리 규약과 일치.

## 2. 계약 2·5 리터럴 -- base 값과 같다
내 시제품(개정 card 문장 그대로)이 base에서 **19 passed**(seed 0·1·7·123). 계약 2: `set(rows) == {"row_seg0","row_seg1"}`, 정렬 이름 `["M1","M2","M3"]`, 행별 stack_id `{"row_seg0"}`·`{"row_seg1"}`, n_fingers `{1}` 전부 참. 계약 5: 정렬 목록 `["M1","M1c","M2","M2c","M3","M4","M5"]` 참.

## 3. 계약 8 새 규칙 vs gate `tools/gates/test_lint.py`(6c724de)
* 규칙 (1): 도구 = 지역 대입 인라인 뒤 판정 쌍(`==`·`abs(a-b)<tol`·`isclose`·`approx`) **두 쪽에 같은 피검 호출(인자 정규형)**이 있으면 FAIL. card = '같은 피검 출력의 두 값 `==` 금지, 한 쪽은 리터럴/입력 값'. card가 더 엄격(도우미에 숨긴 호출까지 금지)하나 불가능하지 않다. `in`·`not in`은 쌍이 안 만들어져 대상 아님 -- card 문장 맞다.
* 규칙 (3): 도구 = 판정 문장이 **전부** If/Try 조상 아래면 FAIL. card '`if`·`try` 안에만 두지 않는다, `for`는 된다' = 정확히 같다.
* 규칙 (4): 도구 = test 본문(중첩 def 제외)의 `assert` 문 + 이름이 `assert`로 시작하는 호출 + `pytest.raises/warns/fail/deprecated_call`이 0개면 FAIL. card는 '도우미 `assert` 0'으로 더 엄격 -- 불가능하지 않다(minor m3 참고).
* 강제 위반 검사: 다른 계약(3(a)·3(c)·4·6·7·10·11) 중 같은 출력끼리 `==`나 if/try 안 판정을 강요하는 문장 없음. 실증: 내 시제품을 gate 도구 `--interface-card`(19행)로 돌리면 **PASS exit 0, FAIL 0**(UNJUDGED 54, NO-SUBJECT 23). 대조: T1.patch를 같은 도구로 돌리면 FAIL 6(172·196·397행 (1), 238·494·505행 (4)) 재현 -- 도구가 실제로 거부함 확인.

## 4. 판정 강도 -- 약해지지 않았다(변이 결과 1차와 같음)
1차 auditor 스크립트(`kill_b26pre.py`)의 `kill_map.json`(base 경로)과 base 판 `mutate_changed.mutants/_replace_def`를 그대로 써서, **내 시제품**만 실행(seed 1, gate ini, `--gmid-phase=3`):
* 주표 20 id: **18 죽음**, 생존 2 = SR 11799·11878(`_backfill_interdig_ok` -- card의 dd60db6 번호 11800·11879, 결함 card 몫).
* 참고표 16: **15 죽음**, 생존 SR 11801(card 11802).
* const−(등가): 생존(기대대로). 기준·복원 19 passed, 엔진 diff 0.
* 변이마다 죽인 계약이 1차 판정 기록과 **같다**(주표 #1~3 계약 2, #4~7 계약 1, #8 계약 5, #13 3(b), #14 3(a)·(b), ref 6 계약 2·3(e), ref 7~12 계약 10 …). 18개 중 생존으로 바뀐 것 0.
* 판정 자체의 변화: 계약 2·5는 중복 단언 삭제 + 리터럴 비교로 같거나 더 강함. 계약 1 (d)는 리터럴로 바꾸며 '`transistors` ↔ `repaired_rows` 정합'이 빠졌다 -- m1.

## 5. T1.patch 열람 허용 -- 타당(조건부), 금지 집합 충분
* `T1.patch` sha256 `286667e2…` 일치, `diff --git` 1개(새 test 파일, `/dev/null` → 파일), 소스 줄 0, auditor 수치·경로 문자열 없음.
* design 05 §6.4는 소스 분류 열람만 막는다. 다만 §14·`agents/gmid-test-author.md` '입력'은 interface card·spec card·worktree를 열거한다 -- T1.patch는 오케스트레이터가 더하는 입력이다(m4). 선례는 브리프가 든 것보다 runbook 8.4의 t0 2차 시도('운반 blob cp + T1.patch')가 직접적이다.
* 금지 집합(`b26pre_attempt1/.ai/**`, `b26pre_att2_scripts/**`, 그 밖 `_drafts/**`, 엔진·도구 소스)은 충분하다. 단 EL1이 `_drafts`를 막지 않아 지시로만 지켜진다(m4).

## 6. launch `attempt2_guard` -- 정확(모래상자 실측)
* `bash -n` OK. 모래상자(`/c/g356/sb`: bare gate + clone, gate master 6c724de):
  `conds` exit 0(조건 1~5 = 0), `local` exit 0 → S2 = card **한 파일** 커밋, 트레일러 Role: doc·Change-Id·Co-Authored-By, interface card 재생성 sha256 `54552e82…` 불변, final OK.
  `after-push`는 `cache_dir`에서 멈춤 -- `load_env`가 실제 gate 경로를 쓰는 모래상자 한계(오케스트레이터 보고 B62와 같다, 스크립트 결함 아님).
* 거부 사례 6 모두 거부: (가) 이미 개정된 card(push 뒤 pre 재실행 -- S1 sha 불일치), (나) 역할 브랜치(pre 285행이 먼저), (다) `$W/$ID-audit` 경로 존재, (라) T1이 gate master(실제 저장소에서 T1 객체 fetch -- '1차 test 커밋이 gate에 들어 있다'), (마) LIT_REV 뒤 stick_diagram.py 변경, (바) 판정 기록 json 존재. T1 객체만 있고 조상 아님 → 통과(맞다).
* 스크래치 경로 -- **S1**(아래).

## 7. parse_spec_card · interface card -- 확인됨
* gate 6c724de `role_paths.parse_spec_card(초안, id)` = `('3','test-only','no',['20261001-b26-phase3-cards'],[],11절)` -- 1차 card와 같다.
* gate 판 `interface_card.py`로 개정 초안에서 재생성 → `6c724de`의 interface card와 **바이트 같음**(sha256 `54552e82…`, 기존 함수 19).
* 초안 sha256 = `c7616fd8…` = launch `SPEC2_SHA`. `.pre-att2.bak` = gate 커밋 card(`2a657824…` = `S1_SPEC_SHA`). measured 표지(`**measured at \`dd60db6\`**`)는 하나뿐이고 계약 1 (d)의 'measured at gate `6c724de`'는 표지 정규식에 안 걸린다(meas_rev 영향 없음).

## 지적

### S1. 2차 scratch 경로 충돌 + '바꿔 읽기' 지시
* `b26pre_briefs.md` A2 '2차 차이'·순서 0과 runbook §4가 auditor scratch로 `C:/g348`(순서 3)·`C:/g349`(순서 7)를 배정했다. 둘 다 **오늘 이미 쓴 번호**(오늘 사용 g323~g355). 지금 다른 agent가 `/c/g357`·`/c/g359`·`/c/g360`을 쓰고 있다(`/c/g352`·`g354`·`g355`도 있음).
* 더해 2절 auditor 머리 블록(역할에 그대로 건네는 본문)은 아직 `C:/g341`·`C:/g342`를 20여 곳에 박아 두었고(V1 명령, 2.3 스크립트 경로, "scratch는 … 순서 3 = C:/g341, 순서 7 = C:/g342"), 순서 요약 3·5·8도 `test ! -e /c/g341`·`/c/g342`다. 2차는 'C:/g348·g349로 **읽는다**'로만 덧붙였다 -- 한 프롬프트 안에서 두 배정이 부딪친다.
* 고침: 오늘 쓰지 않았고 지금 없는 새 번호 두 개를 고르고(예: g361 이후 -- 띄우기 직전 `test ! -e`와 오늘 기록 대조), 2절 머리 블록·2.x 명령·순서 요약 3·5·8·runbook §4의 경로를 **글자 그대로** 바꾼다('읽기 치환' 금지).

### minor
* **m1** 계약 1 (d): 리터럴로 바꾸며 '`transistors`가 `repaired_rows`로 승격됨' 정합 판정이 `transistors` 쪽만 남았다(`repaired_rows` 키는 (c)의 접두 판정뿐). `set(pr["repaired_rows"]) == {"pair_row_repair0_repair0_repair0"}`를 하나 더하면(한 쪽이 리터럴 -- V4 안전) 1차 판정의 정합 의미가 돌아온다. 측정한 변이 집합에서는 차이 없음.
* **m2** 계약 8 '`==` 한 쪽은 … 피검을 부르지 않고 입력에서 만든 값': card는 `size_transistor`를 '피검이 아니다'로 적지만 interface card 표에 있어 도구에는 피검이다. `W0`·`S`에서 나온 값을 기대 쪽에 쓰면 실제 쪽(spec·ctx에 `S`가 인라인됨)과 같은 `size_transistor(...)` 호출이 겹쳐 규칙 (1) FAIL이 된다. 지금 그런 비교를 강요하는 계약은 없다. 문구를 'interface card 심볼 호출을 담지 않는 값'으로.
* **m3** 계약 8 규칙 (4) 설명이 `pytest.raises/warns/fail/deprecated_call`도 판정으로 세는 점을 빠뜨렸다(이 card엔 거부 test가 없어 영향 없음).
* **m4** T1.patch 허용 근거: §6.4·§14를 '소스만 막는다'로 인용했지만 §14·agent 정의 '입력'은 열거형이다 -- '오케스트레이터가 더한 입력'으로 적고 선례는 runbook 8.4(t0 2차 시도)를 든다. 금지 집합은 EL1이 강제하지 않으므로, T1.patch만 담은 별도 폴더(예: `_drafts/b26pre_att2_input/T1.patch`)로 복사해 test-author가 `b26pre_attempt1/`을 아예 가리키지 않게 하는 편이 낫다.
* **m5** A2·runbook §4의 '`C:/g342`가 남아 있다(정리 슬롯에서 지운다)'는 지금 사실이 아니다(`/c/g342` 없음, 2026-10-06 실측).
* **m6** `attempt2_guard`의 리터럴 재측정 조건이 SR·SD 두 파일 diff뿐이다. 계약 1 경로가 다른 모듈(analog-grammar 등)에 기대면 그쪽 변경은 못 잡는다 -- auditor (iv) 재측정이 막으므로 정보성.

## 측정 산출(모래상자, 삭제됨)
`/c/g356/v/m1.py`(계약 1·max_iter), `/c/g356/proto/test_b26pre_existing_paths.py`(내 시제품), `/c/g356/v/kill2.py`(1차 kill_map 재사용), lint 결과 JSON -- 끝에 `/c/g356` 통째 삭제. 실제 저장소·gate 무변경(읽기만).
