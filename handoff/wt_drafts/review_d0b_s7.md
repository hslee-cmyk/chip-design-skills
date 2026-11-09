# review_d0b_s7 -- d0b_launch.sh S-7 표 사실 요약(fact_sum·cond_7_facts) + plan_sum 단일 출처 리팩터 독립 검토

검토 대상: `_drafts/d0b_launch.sh`(797줄) vs `d0b_launch.sh.pre-s7.bak`(577줄). 검토자 ≠ 작성자.
실측 환경: 모래상자 `/c/g431`(bare gate 복제 + `clone -c core.autocrlf=false`, TMP/TEMP/TMPDIR 모두 그 아래, hooksPath 빈 폴더) -- 끝에 삭제했다.
실제 저장소는 읽기만 했다(검토 뒤 HEAD = gate/master = `6df4bd7`, `git status`는 검토 전과 같음 -- `.bkit/state` 2개만 M).

## 판정: B 0 / S 0 / minor 6 -- 그대로 써도 된다(minor는 선택)

## 1. 정적 확인

* `bash -n` 통과.
* 수·표본 이름 하드코딩 없음: 29·24·5·23, `search_shared_finger_w`, `RailDeclaration`·`rail_declaration`이 코드에 없다. 수는 초안 선언 문장 두 개(정규식)에서, B26-1 표본은 `B26MARK='B26-1 병합 뒤에만 있다'`가 근거 칸에 있는 행에서, A-6 표본은 '행' × · '규칙' A-6 행에서 읽는다. 상수는 `B26ID`·`B26MARK`(문구)뿐.
* (a) '행' 열 대 레지스트리: 머리에 `함수`·`이관 목적지` 칸 이름이 정확히 있는 표만, 열 위치는 이름으로(`rh.index`) 찾고, 함수 칸의 **첫 백틱 토큰**을 키로 쓴다 = 표 머리 '단위(함수 칸 첫 토큰)'의 정의와 같다. base red = 칸(strip) != 기대 줄기 -- 선언 23/24와 실측 일치.
* (b) 참조자: 엔진 집합 = gate 트리 `A/` 최상위 `*.py` + `workspaces/run_harness.py` -- `reachability._is_source`·`interface_card.ENGINE_GLOBS`와 같은 집합(확인). 자기 def 노드를 identity로 통째로 건너뛰므로(자기 재귀 제외) `Name`·`Attribute.attr`·`alias`(이름 마지막 토막·asname)를 센다.
* (c) `lc_pred_ok`(B26-1 판정 기록)로 병합 여부를 나눔: 병합 판 -> 트리에 없는 표본 0이어야, 미병합 판 -> 없는 표본 = B26 표시 행(같으면 미충족 3 "B26-1 병합 뒤 다시 잰다", 다르면 3).
* 캐시 키 `<상태>.facts.<H>.<초안16>.<스크립트16>.json`: fact_sum이 읽는 것 = 초안(키), 레지스트리·계획서·엔진 파일(전부 `git cat-file <H>:…` -- H로 충분), `import_layering`(C = gate 캐시, `cache_dir`가 basename = gate/master를 단언하고 호출부의 H = gate/master -- H로 충분), `B26MARK`(스크립트 sha). `lc_pred_ok`는 캐시하지 않고 매번 잰다. 키에 빠진 입력 없음. 실측: 같은 판·같은 초안 재실행 시 파일 mtime 불변(재계산 안 함), 초안 10종 변형마다 다른 키.
* plan_sum 리팩터: 옛 `c[2]`('행' 위치 고정) 대신 fact_sum의 rows(`unit`·`exp`·`row` -- 열 이름 기반). 의미 동일, 표 파싱 한 곳. plan 출력 캐시를 새로 만들 때 `rm -f "$out".sum.*`가 facts는 지우지 않는데 facts는 plan 출력에 의존하지 않으므로 맞다.

## 2. 모래상자 재현(작성자 표 + 내 적대 사례)

`conds` 전체 실행(base0, gate `6df4bd7`): S-7 = 미충족(3) -- (a) "○ 24 모두 행 있음·× 5 모두 없음, base red 23/24 = 선언", (c) "표본 29개 = gate 관찰 27개 + B26-1 표본 2개(RailDeclaration rail_declaration) -- B26-1 병합 뒤 다시 잰다", (b) `search_shared_finger_w(def stick_diagram.py:6179, 행 없음, 참조자 0, 부르는 단위 SharedFingerWCandidate = A-2 이 표본뿐, _quantize_to_grid = 칸 MOD 줄기 ['stick_diagram'])`, plan 쪽은 D0a 미병합이라 판정 안 함. 기대대로(B26-1만 미충족).

나머지는 `cond_7_facts`·`fact_sum`·`fget`·`fact_path`를 **스크립트에서 그대로 잘라 eval**한 하네스로 모래상자 커밋마다 돌렸다(전체 `conds`는 `cache_dir`가 실제 gate master를 요구해 새 커밋 판에서는 못 돈다).

| 사례 | 변형 | rc | 멈춘 자리 |
|---|---|---|---|
| base0 | 없음 | 3 | (c) B26-1 미병합만 |
| simA | 레지스트리에 `search_shared_finger_w` 함수 행 추가 | 3 | (a) row_mismatch `[search_shared_finger_w, ×, True]`, 측정 25 + (b) "레지스트리 행 있음" |
| simB | design_report.py에 `from stick_diagram import search_shared_finger_w as f` | 3 | (b) 참조자 `design_report.py:320` |
| simB2 | stick_diagram.py에 `_V_ALIAS = search_shared_finger_w` | 3 | (b) 참조자 `stick_diagram.py:9013` |
| simE | `_quantize_to_grid` 칸 -> `gmid_sizing_engine` | 3 | (b) 칸 MOD 줄기 `['gmid_sizing_engine'] != [stick_diagram]` |
| simC | B26-1 판정 기록(V1~V10 PASS)만, 두 표본 정의 없음 | 3 | (c) "B26-1 병합 판인데 … 트리에 없는 것: RailDeclaration rail_declaration" |
| simC2 | simC + topology_authoring.py에 두 정의 | **0** | 전부 통과(병합 판 정상 경로) |
| 선언 red 23->22 | 초안 | 3 | (a) "base red 선언 22 -> 측정 23/24" |
| 선언 문장 삭제 | 초안 | **1** | "선언 문장 … 없음" |
| 선언 29->28 | 초안 | **1** | "선언 … != 표 실제 29행" |
| '행' 머리 이름 변경 | 초안 | **1** | "표 머리에 '행' … 열 없음" |
| 행 하나 삭제, 선언 그대로 | 초안 | **1** | 수 불일치 |
| 행 하나 삭제 + 선언 28/24/4 | 초안 | 3 | (b) "없음(표에 × A-6 행 0)", (c)만 |
| '행' 값 `x` | 초안 | **1** | "○·×가 아니다" |
| × -> ○ 뒤집기(선언 그대로) | 초안 | **1** | 수 불일치(선언도 고치면 (a)가 잡는다) |
| **adv1** | `import stick_diagram as sd; return sd.search_shared_finger_w` | 3 | (b) 참조자 `design_report.py:321`(Attribute로 잡힘) |
| **adv2** | 표 전체 CRLF + 행 끝 공백·탭 + 끝 열 추가 / 기대·행 사이 열 삽입 | 3 | base0와 같은 출력(견고) |
| **adv3a** | 레지스트리 행: 함수 칸은 백틱 없음, 비고 칸 첫 백틱 토큰이 표본 이름 | 3 | 행 없음으로 정상 판정(base0와 같음) |
| **adv3b** | 열 순서가 다른 새 표 `| 이관 목적지 | 비고 | 함수 |`, 함수 칸 = 표본 | 3 | (a)·(b) 행 있음으로 잡힘 |
| adv1c | `getattr(sd, 'search_shared_finger_' + 'w')`(문자열) | 3 | (b) 통과 -- 못 잡음(아래 m3, card 정의 범위 밖) |
| adv7 | def 몸체 안 자기 참조 `_self_ref = search_shared_finger_w` | 3 | (b) 통과 -- 자기 def 제외 정상 |

## 3. minor

* **m1 (참조 셈 범위)** 문자열 참조(`getattr(m, "...")`, `__all__`)는 세지 않는다(adv1c). card 근거 칸 정의("`Name`·`Attribute`·`import` 참조 0")와 같으므로 결함은 아니다. 다만 D0a `move_plan`의 A-5 참조자 정의와 같은지는 D0a 병합 뒤 한 번 대조할 것(다르면 표/근거 문구를 맞춘다).
* **m2 (부르는 단위 판정이 card보다 좁다 -- 보수 쪽)** callee = def 몸체의 `ast.Name` ∩ 같은 파일 최상위 이름. (i) 다른 파일에서 import한 단위는 빠진다(최댓값을 올리는 다른 파일 callee를 놓치면 거짓 통과 가능 -- 지금 표본은 같은 파일 callee뿐이라 영향 없음). (ii) 함수 callee는 "칸 MOD 줄기 = [기대] 정확히"를 요구한다 -- A-1 토큰·`--aliases` 별칭(`optimizer`)·두 MOD 칸(A-3 최솟값)·모듈 상수(Assign 이름도 `own`에 들어가 "행 없음"이 된다)·같은 이름 지역 변수가 있는 표본이면 거짓 멈춤. card의 규칙은 "callee MOD의 **최댓값** = 기대"이므로 지금 구현은 그보다 엄격하다. 멈춤 쪽 실패라 안전하지만, 표본이 바뀔 때 거짓 멈춤이 나면 이 한계 때문이라는 주석 한 줄을 두면 좋다.
* **m3 (S-4·S-5 결합)** `plan_sum`이 `fact_sum`을 먼저 부르므로, fact_sum의 Python이 죽으면(gate 판 엔진 파일 SyntaxError, `cat-file` 실패 등) S-4·S-5도 규약오류(1)가 되고 원인 메시지는 S-7 쪽 traceback뿐이다. 옛 판도 초안 표 파싱 실패로 같은 결합이 있었으나 지금은 레지스트리·엔진 AST까지 넓어졌다. `plan_sum`이 facts 실패 시 `rows=[]`로 진행하고 S-7만 1로 떨어지게 하거나, 실패 문구를 한 줄 더하면 된다.
* **m4 (`||` 문맥의 fget 실패)** `cond_7_facts`는 `conds_eval`의 `|| r=$?` 문맥에서 돌아 `set -e`가 꺼진다. `fget`이 실패하면(예: facts 파일 손상) 빈 문자열로 진행한다. 지금은 `row_mismatch`의 `!= "[]"` 비교 덕에 3으로 떨어져 거짓 통과는 없지만(우연한 보호), `e=$(fget …) || return 1` 처럼 명시 return이 낫다(기존 sum_get도 같은 패턴 -- 기존 결함). 하네스에서 stdout 인코딩을 안 맞췄을 때 실제로 이 경로로 들어가 3이 나왔다(실 스크립트는 `PYTHONIOENCODING=utf-8`을 export하므로 해당 없음).
* **m5 (선언 문장 중복)** `re.search`는 절 안 첫 출현만 본다. 같은 절에 옛 수를 담은 선언 문장이 하나 더 생기면(재측정 문단 덧붙이기) 앞 것을 읽는다. 지금은 각각 1회(실측). `len(re.findall(...)) == 1`을 요구하면 닫힌다.
* **m6 (셀 분할)** 초안 표·레지스트리 모두 `split("|")`로 나눈다 -- `\|` 이스케이프 셀이 생기면 열이 밀린다. 지금 레지스트리 표 행에 `\|` 0개(실측)라 영향 없음. gate의 `role_paths._split_cells`(이스케이프 인식)를 C에서 import해 쓰면 같은 규약이 된다. 또 행 칸 수가 머리보다 적은 초안 행은 IndexError traceback으로 1이 된다(멈춤은 맞고 문구만 거칠다).

## 4. 요청 항목별 답

* 하드코딩: 없음(1절).
* 초안 표 파싱 견고성: CRLF·행 끝 공백/탭·끝 열 추가·중간 열 삽입·백틱 모두 통과(adv2), 머리 이름 변경·마크 오기·행 수 불일치는 1로 멈춤. 표 변경 시 동작: 초안 sha가 키라 즉시 재계산, 선언 문장과 어긋나면 1, 레지스트리와 어긋나면 3.
* 참조자 셈: 자기 def 제외 정상(adv7), Attribute(adv1)·import alias(simB)·Name(simB2) 포함. 문자열은 제외(m1).
* 캐시 키: gate sha + 초안 sha + 스크립트 sha로 충분 -- 레지스트리·계획서·엔진은 gate 트리 H에서 읽고 import_layering도 H 판 gate 캐시다(1절).
