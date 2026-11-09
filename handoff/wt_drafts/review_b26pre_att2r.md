# 독립 검토(r) -- b26pre 2차 시도 준비 반영분(review_b26pre_att2.md S1·m1~m5)

검토자 = 작성자 아님, diff 한정. 대조 기준 = 각 `*.pre-att2r.bak`. gate master `6c724de`(실제 저장소 읽기 전용 -- `git archive`만), 모래상자 `/c/g375`만 사용(TMP·TEMP·TMPDIR·PYTHONPYCACHEPREFIX·pytest basetemp 그 아래, 끝에 통째 삭제).
절차 위반 1건 자진 기재: `test_lint.py --help`를 부를 때 명령 앞에 `cd /c/g375`를 한 번 붙였다(모래상자 안 이동만, 쓰기 없음, 결과 영향 없음). 그 밖 명령은 전부 절대 경로.

## 판정: **B 0 · S 0 · minor 2(정보성)** -- card는 push 준비가 됐다

## 1. S1 scratch -- 반영 확인
* 네 파일의 `g341`·`g342`·`g348`·`g349` = **0**(Python 정규식 전수). 새 번호 분포: briefs g370 10·g371 9·g372 30, launch g370 5·g371 3·g372 3, runbook §4 각 4, spec card 0(spec card의 g310·g344·g365는 오케스트레이터 측정 이력 문장 -- 역할에게 건네는 문장 아님).
* 역할에게 건네는 본문에 글자 그대로 들어감: 1.1절 test-author 코드 블록 `scratch: C:/g370 하나만`, 2절 auditor 머리 블록 `순서 3 = C:/g371, 순서 7 = C:/g372`, V1·V3 명령(2.2 표)·2.3 (가) 1~3·함정 3의 경로 전부 `C:/g372`, 순서 요약 0·3·5·8 `/c/g370`·`/c/g371`·`/c/g372`, runbook §4 명령 뒤 흐름. '바꿔 읽기' 문장은 scratch에 대해 남지 않았다(A2 '2차 차이'는 '글자 그대로 적혀 있다'로 바뀜).
* 지금 `/c/g370`·`/c/g371`·`/c/g372` 없음(2026-10-06 실측, 있는 것은 g366·g369·g373·g374와 내 g375).
* launch 거부: `attempt2_guard`(pre·card 단계)와 `after-push`에 `SCRATCH2="/c/g370 /c/g371 /c/g372"` 부재 확인. 그 코드 줄을 launch 파일에서 그대로 잘라(266~268행, 416행) 모래상자 경로로 바꿔 돌림 -- 셋 다 없음 → 통과, g370·g371·g372 각각 하나만 만들면 두 자리 모두 멈춤(6/6 거부).

## 2. m1 -- 계약 1 (d) 두 리터럴 비교, base 재측정
* card 개정: `{t.stack_id for t in pr["transistors"]} == {"pair_row_repair0_repair0_repair0"}` **와** `set(pr["repaired_rows"]) == {"pair_row_repair0_repair0_repair0"}`, 두 필드끼리 `==` 금지 문장 유지. 브리프 표 1행·1.1 코드 블록 (1)·A2 (iv)·runbook §4도 같은 두 비교.
* 내 재측정(gate `6c724de` archive, `T1.patch`를 모래상자에 적용한 1차 시나리오 그대로 + 내 측정 test, `pytest_gate.ini`, `--gmid-phase=3`): `PYTHONHASHSEED` **0·1·7 모두** 두 비교 참. `transistors` stack_id 집합 = `["pair_row_repair0_repair0_repair0"]`(Ma·Mb 둘 다, n_fingers 1), `repaired_rows` 키 = 같은 한 개(행 = `["Ma","Mb"]`), `audit_ok` False, 3c 체크 1개 `3c. common-centroid[Ma/Mb]` ok False, `growth_rounds` 없음. 172행을 두 비교로 바꾼 계약 1 test도 세 seed 모두 PASS(파일 전체 21 passed = T1 19 + 측정 test 2).

## 3. 172행만 바꾼 사본의 V4(gate `6c724de` `tools/gates/test_lint.py --interface-card`, 19행 interface card)
* 사본 = 1차 T1과 diff가 172행 → 172·173행 두 줄뿐임을 확인.
* 결과: 172·173행 = 규칙 (2) **UNJUDGED**, 규칙 (1) FAIL 없음. 남은 FAIL 5 = (1) 197·398행, (4) 239·495·506행(1차 196·397·238·494·505의 +1 이동). 대조로 원본 T1은 FAIL 6(172행 (1) 포함) 재현. card '2차 시도 개정' 문단의 서술과 같다.

## 4. m2·m3 -- card 계약 8 문구
* m2: 공통 입력 항목과 '`==` 판정의 기대 쪽'이 'interface card 심볼 호출을 담지 않는 값(W0·S는 기대 쪽 금지)'으로 바뀜. 1.1 코드 블록 규칙 줄도 같다.
* m3: 규칙 (4) 근거에 '본문(중첩 def 제외) `assert` 문, `assert…` 호출, `pytest.raises/warns/fail/deprecated_call`' 추가.
* 개정 초안으로 gate 판 `interface_card.py` 재생성 = sha256 `54552e82…` = gate `6c724de` interface card blob = launch `IFC_SHA_EXP`(바이트 불변).

## 5. m4 -- T1.patch 격리
* `stage_t1_input`: 원본 sha256 확인 → 폴더 없으면 만들고 `T1.patch` 한 파일만 복사 → `ls -A` = `T1.patch` 하나 → 복사본 sha256 확인. `pre`(attempt2_guard 다음)와 `after-push`에서 부른다.
* 모래상자 실행(함수 본문을 launch에서 그대로 잘라 경로만 바꿈): 새로 복사 OK(폴더 내용 `T1.patch` 하나), 다시 실행 OK, 군더더기 파일 → 멈춤, 복사본 변조 → 멈춤, 원본 변조 → 멈춤(5/5 기대대로).
* 실제 `T1.patch` sha256 = `286667e28e12e1a02e36ac9ce6575189e0b7a669233fd2c9e09dfb1bfb9159e4` = `T1_PATCH_SHA`. `_drafts/b26pre_att2_input/`은 아직 없음(launch가 만든다).
* test-author 코드 블록(브리프 70~89행)에서 `b26pre_attempt1` = **0**, 입력은 `_drafts/b26pre_att2_input/T1.patch` 하나와 '그 밖 `_drafts/**` 전부 금지'. 1.1절 위 근거 문단(67~68행, 오케스트레이터용 산문, 블록 밖)에는 원본 위치 언급 2곳 -- 역할에게 건네는 본문이 아니라 문제없다.
* 근거 문장은 '열거에 없는 입력을 오케스트레이터가 더한다' + 선례 runbook 8.4로 바뀜(m4 요구대로).

## 6. m5 · runbook diff 범위
* m5: '`C:/g342`가 남아 있다' 문장이 A2와 runbook §4에서 빠짐. `/c/g34*` 없음(실측).
* runbook diff(`.pre-att2r.bak` 대비) hunk 2개: §4(위 반영, 맞음) **와 §8.4 한 줄**(t0 'review_t0_carry_r1 반영(r2)' 문장 추가) -- minor n1.

## 7. SPEC2_SHA · bash -n · parse_spec_card
* 초안 sha256 = `dba86fa160a9c0b5d7c88b4c733d75cb40b87fea1bfe4948a88a8a4c9ac08eb1` = launch `SPEC2_SHA`(브리프 A2·runbook §4의 `dba86fa1…`도 같음).
* `bash -n b26pre_launch.sh` OK.
* gate `6c724de` `role_paths.parse_spec_card(초안, id)` = id 일치, phase `3`, `test-only`, gate_change `no`, approval `['20261001-b26-phase3-cards']`, activated 목록 빈 것, 절 11 -- `.pre-att2r.bak`와 같다.

## 지적

### minor(정보성)
* **n1** runbook diff가 §4만이 아니다: `.pre-att2r.bak` 대비 §8.4에 t0 r2 문장 한 줄이 더 들어 있다. `.pre-att2r.bak`와 `.pre-r2.bak`(t0 r2 백업)이 바이트 같으므로 같은 시점에서 갈라진 t0 r2 편집이 함께 반영된 것으로 보인다 -- b26pre 내용이 아니고 b26pre 역할 본문에 영향 없음. 그 문장의 옳고 그름은 이 검토 범위 밖이다(t0 쪽 검토 몫). 오케스트레이터가 그 hunk가 t0 r2 의도분인지만 확인하면 된다.
* **n2** auditor 머리 블록은 여전히 `base = gate master 6c724de…`이고 A2 '2차 차이'가 'S2로 읽는다'로 덧붙인다. S1의 '바꿔 읽기 금지'는 scratch 대상이었고 S2 sha는 push 전에 알 수 없으며 머리 블록에 '착수 시 gate master -- 다르면 그 값을 쓰고' 대체 규칙이 있어 결함은 아니다. 원하면 after-push 뒤 브리프에 S2 sha를 글자로 넣는다.
* (지난 m6 -- 리터럴 재측정 조건이 SR·SD diff뿐 -- 은 그대로, 정보성.)

## 결론
S1과 m1~m5가 지시대로 반영됐고, 계약 1 (d) 두 리터럴은 base `6c724de`에서 seed 0·1·7 모두 참, 그 두 줄은 gate V4 도구에서 FAIL이 아니다. **spec card 초안(sha256 `dba86fa1…`)은 push해도 된다** -- launch `conds` → `local` → 단독 push → `after-push` 순서대로.

## 측정 산출(모래상자, 삭제됨)
`/c/g375/base`(6c724de archive + T1 적용·172행 수정 사본·측정 test), `run_meas.sh`, `run_lint.sh`, `harness.sh`, 출력 `out/`(measure.jsonl, lint_mod/orig JSON, harness.txt, ifc_regen.md) -- 끝에 `/c/g375` 통째 삭제. 실제 저장소·gate·`_drafts`(이 파일 말고) 무변경.
