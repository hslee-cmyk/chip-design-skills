# 독립 검증: F1 b1fix4 · F2 r6/r7 (작성자 아님)

판정: **B 0 · S 0 · minor 5** -- 진행 가능. minor는 문구 정합만(판정 수치에 영향 없음).

판: 실제 저장소 `HEAD`·`master`·`gate/master` = `6df4bd7`, 읽기만(`status --porcelain` md5 `0474ab6d…`, 시작 시점 측정).
스크래치 `C:/g434`(TMP/TEMP `C:/g434/tmp`, cd 없음, clone `core.autocrlf=false`), 작업 끝에 삭제.

## 1. F1 b1fix4 (spec·kit·selftest)

spec diff(`.pre-b1fix4.bak` 대비): 문언 4곳 보탬 + 실측 단락 1곳. 모두 review_p3_f1_b1fix3 minor 1~4와 맞는다.
* minor 1 대소문자 무시: kit `f12_execstr.py:167` `….lower().startswith("python")`(`\`→`/` 정규화 포함)와 같다.
* minor 2 '이 식이 보지 않는 것'(③ 기본값, (s3) 메서드 매개변수 경유): 문언과 kit 동작이 같다(selftest DOC 2경우 통과). 내용 규칙 기록 + '실행 흐름이 이 식 밖' 멈춤으로 넘기는 연결도 맞다.
* minor 3 판 순서: kit `meta["fpos"]`(채움 노드 `(lineno, col_offset)`의 최소)로 정렬, 같은 원문은 처음 나온 판 하나 -- '가장 앞 채움 자리의 판 하나'와 같다.
  `f12_equiv`는 파싱 실패(`exec_str_parse`)를 먼저 보고, 그 다음 판 수 다름(`exec_str_variant_count`, `variants` 기록)을 본다 -- 계약 3 (사) 새 문장과 같다.
* minor 4 이름 충돌 멈춤: selftest DOC 2경우(다른 함수 `code = "x = ("` → `parse_fail` 줄 2, f-string → `stop_fstring` 1) 통과.

selftest를 다시 돌렸다(내 실행):
* `selftest_execstr_b1fix4.py` rc 0 -- 새 kit ADV 2/2·DOC 6/6 통과, 옛 kit(`.pre-b1fix4.bak`) ADV 2/2 실패·DOC 6/6 통과(문언만 보탠 것이라는 주장과 같음).
  ADV 입력은 소스 순서(zzz → aaa)가 `repr` 순서와 반대라 옛 판을 실제로 구별한다.
* `selftest_execstr_b1fix3.py`(새 kit vs `.pre-b1fix3.bak`) rc 0 -- 새 adv 13/13·reg 17/17 통과, 옛 adv 13/13 실패 = spec '새 30/30·옛 적대 13/13 실패'와 같음.
* `parse_spec_card`(gate `6df4bd7` `role_paths.py`, `expect_id 20261002-p3-callers-update`): 현재 판·`.pre-b1fix4.bak` 둘 다 통과, 절 11.

## 2. F2 r6/r7 (spec·시제품)

문언: '(F1 계약 1 (e)와 같은 정의)'가 계약 3·4·6 (a)·6 (b) (iv) 네 곳에 같은 꼴로 있고, 모두 '실행 자리 (s1)~(s3)·닿음 ①~③·감싼 식 (w1)~(w3)·템플릿 채움·판 순서·이 식이 보지 않는 것까지' 같은 열거를 쓴다(계약 6은 짧게 참조하고 interface card 원문 싣기로 넘김).
FAIL 표지: 계약 3 = 줄 표지 `EXEC-PARSE-ERROR`·`EXEC-FSTRING`(셸 `sed 's/^[A-Za-z-]* //'`가 경로만 남김 -- 블록 `PARSE-ERROR`와 같은 길), 계약 4 = 이름 표지 `<EXEC-PARSE-ERROR>`·`<EXEC-FSTRING>`(블록 `MARK`가 `<`로 시작하는 이름을 `pre`에서 빼지 않으므로 base에 있어도 FAIL -- 문언과 같음). B0 거부 확인 `stmt`·`call` 계수에 내장 몫이 들어가지 않음(아래 실측 `b0_stmt 69·b0_call 9` 그대로).
규칙 밖: 계약 3·4는 '판정 기록에 자리만', 6 (a)는 '세지 않는다' -- 판정 아님으로 같다.

시제품 diff: r6 = `_exec_embedded_reads`((b)에 더함), r7 = `_shim_hits` 함수 추출(동작 같음) + `_exec_embedded_imports`((a)에 더함) + `P3SD_REPORT_A`. 바깥 판정 식은 바뀌지 않았다.

### 재측정(내 사슬 -- `mk_chain_r1.sh C:/g434/f <저장소> g1_kit/install_proto.py 6c724de`, exit 0)
G1 `bf7d01c`(=B0), M9 정정 `14dea75`, F1 없는 F2 `f6e66e0`, F1 모의 `b57d4fb`(=F2 base, `changed 72 notes 2 d17 files 8`), F2 모의 `18ff7ff`(=head), SD 49·ACF 2.
B1 모양 F1은 내가 따로 만들었다(작성자 `mk_b1shape_r6.py`를 쓰지 않고 정규식으로 `_B34_FRESH_SCRIPT = r'''…'''` 원문을 M9 정정 판으로 되돌림, `+10/-12`) → `a565a93`, 그 위 F2 `cd5cfa7`(5파일 3·116 -- 같음).
E3·E3b 확장 판도 내가 따로 썼다(`design 30`을 `6df4bd7`에서 잘라 내장 트리를 파일 루프 안에서 같은 식으로 걷는 판 -- 앵커 각 1회 단언; 내장 파일 계산만 kit `f12_execstr` b1fix4).
합성 거부 커밋 둘(내 입력): syn1 `21d7ee6` = head + `[sys.executable, "-B", "-c", _CODE]`·`_CODE`에 `import sizing_recipe`((s2)·② 대입),
syn2 `a6dffd4` = syn1 + `exec(_T.format(mod="design_report"))`·`_T`에 `importlib.import_module('{mod}')`((s1)·템플릿 import 호출 채움).

| 판 | E3 블록 / 확장 | E3b 블록 / 확장 | 시제품 r3 / r6 / r7 |
|---|---|---|---|
| F2 base `b57d4fb` | 부재 FAIL 3 + PASS / 같음(head 출력 바이트 같음) | PASS / PASS | 2 failed / 2 failed / 2 failed (전부 `AssertionError`, 다른 예외 0) |
| head `18ff7ff` | PASS / PASS(바이트 같음) | PASS / PASS | 2 passed ×3 (r7 importer 0) |
| **B1 모양 위 F2 `cd5cfa7`** | PASS / PASS(바이트 같음) | PASS(놓침) / **FAIL 10줄·1파일** (`test_b34_grammar_explicit.py:125`, SD 삭제 이름 10) | 2 passed(놓침) / **1 failed**(`…sd_names_resolve`, 미해석 10 = E3b 10과 같은 (파일, 줄, 이름)) / 1 failed((a) importer 0) |
| F1 없는 F2 `f6e66e0` | FAIL 65파일 / 같음(바이트 같음) | FAIL 78줄·13파일 / FAIL **88줄**·13파일(B34 39) | 2 failed(미해석 69) / 2 failed(79) / 2 failed((a) importer 58·내장 0) |
| **syn1** | PASS(놓침) / **FAIL 1파일**(`exec-stmt …test_zz_v434_probe.py:4`) | PASS / PASS | 2 passed / 2 passed(놓침) / **(a) 1 failed**(importer 1 = 내장 1) |
| **syn2** | PASS(놓침) / **FAIL 2파일**(+ `exec-call …probe2.py:1` -- 템플릿 채운 판) | PASS / PASS | 2 passed / 2 passed / **(a) 1 failed**(importer 2 = 내장 2) |

PT3 꼴 B34 파일 pytest(gate `6c724de` `pytest_gate.ini`, `--gmid-phase=3`): head 43 passed, B1 모양 위 F2 **9 failed·34 passed**(`AttributeError: module 'stick_diagram' has no attribute …` 9).
모든 판 `E3b LIVE moved_out=57 base_files_reading_moved_out=33 pre_existing=1`, E3 B0 `stmt 69·call 9`(`INVALID` 없음).
→ card r6·r7 표·시제품 수치(커밋 해시 빼고)와 **모두 같다**. 요청한 확인: B1 모양 E3b FAIL 10줄·1파일 ✔, 6 (b) 1 failed ✔, 실행 문자열 안 `import sizing_recipe` 합성을 r7(E3 확장·6 (a))이 잡고 블록·r6은 놓침 ✔(작성자 합성과 다른 내 입력 두 꼴 -- (s2)·(s1) 템플릿 import 호출).

`parse_spec_card`(gate `6df4bd7`, `expect_id 20261002-p3-shim-delete`): 현재 판·`.pre-r7.bak`·`.pre-r6.bak` 모두 통과, 절 11.

## 3. 오케스트레이터 메모(F1 1 (e) 원문을 F2 interface card에 싣기) -- 파서 확인

gate `6df4bd7`의 `interface_card.build`로 현재 F2 card의 interface card를 실제로 만들고(엔진 = `6df4bd7` 트리, 기존 함수 12행), 메모대로
`## 신규 시그니처` 바로 앞에 `### 실행 문자열 정의(F1 계약 1 (e) 원문)` + 대응 한 줄 + F1 초안 93~152행(60줄, sha256 `bfa719e1…f357`)을 넣은 판을 만들어 두 파서를 돌렸다:
* `merge_gate.read_new_symbols`: 넣기 전·뒤 같음(빈 집합 -- `## 신규 시그니처`로 시작하는 줄 여전히 1개).
* `test_lint.read_card_symbols`: 넣기 전·뒤 같음(12쌍 -- `stick_diagram` 8·`audit_current_forced` 4).
* 60줄 중 `|`로 시작 0, `#`로 시작 0, '신규 시그니처'·'모듈…심볼' 문자열 0 -- 메모의 '표로 오인되지 않음'과 같다. 실린 바이트 sha 같음.
* F2 card r6·r7 전후 `build` 결과 행 수 같음(12) -- r6/r7이 '관찰 가능한 계약'에 더한 백틱 토큰이 엔진 함수 행을 늘리지 않았다.
다른 gate 코드(`tools/gates/**`, `.claude/hooks`)에 interface card를 생성기 출력과 바이트 대조하는 곳은 없다(grep).

## 4. minor

1. **F1 b1fix4 이력 단락 끝 문장이 r7 뒤 낡음**: "F2 card 계약 4·6 (b)가 이 (e) 문언을 참조로 옮겼다(F2 card r6 …)" -- r7에서 계약 3·6 (a)도 같은 참조를 쓴다. "계약 3·4·6 (a)·6 (b)(r6·r7)"로.
2. **F1 계약 5 (a)에 f-string 멈춤이 없다**: 5 (a)는 "파싱 실패 실행 문자열 = FAIL"만 적고, F2 계약 3(r7)은 `EXEC-FSTRING`도 FAIL로 센다('F1 계약 5 (a)가 같은 식 -- 정의 하나'). 1 (e) 대상 계산에서 f-string이 이미 멈추므로 실해는 없지만 문장 대칭을 위해 5 (a)·(b)에 "f-string 잎 = FAIL"을 더하는 편이 정의 하나와 맞다.
3. **계약 6 (a)·(b) (iv) 표지의 범위가 시제품보다 넓게 읽힌다**: 문언은 '범위의 `.py` 안 실행 문자열'의 파싱 실패·f-string을 FAIL로 센다고 하는데, 시제품은 (a)를 SR·TL·DR 글자가 든 파일, (b)를 `stick_diagram` 글자가 든 파일에만 적용한다(계약 3·4 auditor 판처럼 '파일 고르기 그대로'). 지금 코퍼스는 표지 0이라 수치 차이 없음. test-author가 interface card만 보고 짜므로 6 (a)·(b) (iv)에 "표지도 위 고르기(글자 포함 파일)에서만" 또는 "범위 전부" 중 하나를 명시하길 권함(어느 쪽이든 판정 수치 같음).
4. **6 (b) (iv)에 '규칙 밖 자리는 세지 않는다'가 없다**: 6 (a)(r7)에는 있고, 계약 3·4는 '판정 기록에 자리만'이 있다. (iv)에도 한 구절을 더하면 넷이 같은 꼴이 된다(interface card에 실릴 F1 원문이 '판정 아님'을 이미 말하므로 실해 없음).
5. **interface card에 실릴 F1 원문의 렌더링·참조**(문서 품질만): 60줄 중 59줄이 4칸 이상 들여쓰기라 빈 줄 뒤에 두면 markdown에서 코드 블록으로 보인다(파서 영향 없음 -- 바이트 그대로 요구라 고칠 대상 아님, 소절 머리 한 줄에 "들여쓰기 원문 그대로"라고 적으면 충분). 원문 안 '계약 3 (사) `.v<j>`'·'재현할 수치 6c724de 단락'은 F1 card 쪽 참조라 test-author가 볼 수 없다 -- 대응 한 줄에 "그 밖 F1 계약 번호 참조는 이 test와 무관"을 더하면 혼동이 없다.

(범위 밖 기록, 이번 diff 아님) F1 102행 "(①~④, ③ 매개변수 경유 포함)"의 ④는 닿음 목록(①~③)에 없다(b1fix4 전부터) -- '①~③'으로.

## 정리
* 사슬·worktree·스크래치 `C:/g434` 삭제. 실제 저장소 읽기만(끝에 `status --porcelain` md5 다시 확인).
