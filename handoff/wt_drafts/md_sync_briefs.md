# md 일치 card `20261001-topology-md-sync` -- 착수 키트(test-author·auditor 브리프 + 사전 시험 결과)

작성 2026-10-01. 기준: gate `master` **`0f23786`**. 저장소 쓰기·상태 변경 git 없음(작업 전후 `git status --short` 동일). 모의는 격리 복제본 `C:/g146`(끝나고 삭제)에서만.
대상: spec 초안 `_drafts/draft_md_sync.final.spec.md`, runbook `_drafts/post_p10b_runbook.sh` 단계 `d`, 명령 `_drafts/b47_regen_commands.md`. 키트 `_drafts/md_sync_kit/`.

## 0. 사전 시험 결과(오케스트레이터용)

| 단계 | 방법 | 결과 |
|---|---|---|
| D 적용 | `C:/g146/r` = 메인 저장소 복제(`--no-hardlinks --no-local`, master = `0f23786`). 상태 파일에 `C1=<HEAD>`를 손으로 넣고(c1 생략) `bash post_p10b_runbook.sh --repo C:/g146/r --render-tmp C:/g146/render --state C:/g146/state.txt --wt C:/g146/wt d` | `d OK: D 2e0cbee, measured_at = D^ = 0f23786`. runbook 안의 blob 단정(`711a5910…`·`2a3e67a5…`)·numstat(5 5 / 12 6)·나머지 4개 md 차이 0 전부 통과(`md_sync_kit/sandbox_stage_d.log`) |
| (1) 프로토타입 test | card '관찰 가능한 계약' 1~5·7과 '거부해야 할 입력'만으로 작성(렌더러·로더·`_drafts` 사전 점검기 안 봄, library md·json 데이터만 형식 확인용으로 읽음). `md_sync_kit/test_topology_md_sync.prototype.py` | **D에서 35 passed**(0.5s, pytest 기동 포함 13s). **D^(`0f23786`)에 새 파일만 복사 → 1 failed(AssertionError) 34 passed**, 수집 오류 0. 실패 test = `test_mdsync_library_tables_match_json` 하나, 메시지의 (계약, 파일) 쌍 = 정확히 {(2,folded),(4,folded),(3,CRTO),(4,CRTO),(5,CRTO)} -- 계약 8 (b) 기대와 같다. 합성 자기 점검 33개는 D^에서도 PASS(`sandbox_Dparent_run.txt`) |
| 전체 실행 | D + 새 파일, 게이트 판 `pytest_gate.ini`, `--gmid-phase=2 --gmid-strict=` | **906 passed, 15 xfailed**(기존 871 + 새 35), 6분 26초. 기존 전수 스캐너(`test_ts3_no_print_verdicts`, `test_d_*` 이름 스캔, `test_ic_markers_match_plan`) 영향 0 |
| (2) V4 | `git archive 0f23786 tools/gates`의 `test_lint.py --root <D+test 커밋> --base D --head T --module-dir skills/analog-gmid-design/assets` | `--subject` 없이(= interface card 0행과 같은 상황) **exit 2 `피검 심볼이 없다`**. A/*.py 최상위 def·class **373개**를 `--subject`로 주면 **PASS exit 0**, `files` = 새 test 파일 1개, findings 5개 전부 규칙 (2) `NO-SUBJECT`(test 함수 5개), UNJUDGED 0, FAIL 0 (`sandbox_v4.json`) -- P10 판정 기록 V4와 같은 처리 |
| V3·V5·V6·V7 | 같은 base/head | V5 PASS `findings []` 2s · V6 PASS `targets []` 52s · V7 PASS `new_defs []` 117s · V3 PASS `targets [] mutants 0` 148s (`sandbox_v3_v5_v6_v7.jsonl`) |
| (3) 이름 충돌 | `A/tests/**` glob 전수 + `-k` 필터 | 새 이름이 걸리는 glob 0: 기존 패턴은 `*.py`·`probe_*.py`·`test_probe_*.py`·`*.topology.json`·`references/**/*.md`·`contracts/*.py`(`test_ic_markers_match_plan` -- `gmid_ic` 표식만 봄). `test_d_move_tests._CONTRACT_FILE_PATTERNS = ("probe_*.py","test_probe_*.py","*.topology.json")`와 겹침 0. `mdsync`·`topology.md`를 읽는 기존 test·게이트 코드 0. `-k "dup_"`·`-k "dup_w_calc or dup_kcl_edges"`·`-k new_topology`를 새 파일에 걸면 35개 전부 deselected(모듈 이름도 -k 대상인데 `test_topology_md_sync`엔 해당 문자열 없음) |

**결론**: card 문장만으로 쓴 test가 D에서 PASS·D^에서 의도한 5쌍으로만 FAIL한다. card 수정 없이 착수 가능 -- 다만 아래 §3 함정 1(T(J) 형식 위반 시 실패 집합)은 test-author에게 '자기 점검 케이스로 단정하지 말 것'을 미리 알린다.

---

## 1. gmid-test-author 브리프(순서 2)

**입력**: interface card(피검 심볼 0행) + spec card '관찰 가능한 계약' 1~7·'거부해야 할 입력'. 렌더러(`topology_to_markdown.py`)·로더·`stick_diagram.py` 소스, `_drafts/`는 보지 않는다. library md·json은 데이터라 형식 확인용으로 읽어도 된다(판정 대상 데이터).

**쓸 것**: `skills/analog-gmid-design/assets/tests/contracts/test_topology_md_sync.py` 하나. 커밋 트레일러 `Role: test`, `Change-Id: 20261001-topology-md-sync`. 다른 경로 변경 0(계약 9: test 커밋 diff = 이 파일 하나).

**모양 요구(card에서 -- 놓치기 쉬운 것)**
1. test 함수 `test_mdsync_*`, 모듈 수준 도우미·상수 `_mdsync_*`/`_MDSYNC_*`. parametrize id에 `dup_`·`new_topology` 금지(중복 케이스는 `repeated_row`).
2. import = 표준 모듈(`collections`·`json`·`pathlib`·`re`) + `pytest`뿐. A/*.py·`run_harness`·`subprocess`·`importlib`·`runpy` 금지(계약 6). md 쓰기 금지.
3. 실제 library 판정 = md 전부의 계약 1 (b)~(d)·2~5 실패 쌍을 **전부 모은 뒤** `assert fails == [], 메시지` 하나. 메시지는 쌍마다 `계약 <k> <n>: <사유>` 한 줄(auditor가 이 줄로 계약 8 (b) 쌍을 센다).
4. 계약 1 (a)(md ≥ 1개)는 **별도 test 함수**. 합성 자기 점검 '판정 대상 md 0개(1)'는 디렉터리 단위 판정 함수를 `tmp_path`(빈 폴더)에 돌려 실패 집합 == {1}로 단정한다 -- 1 (a) test가 glob 길이만 보면 이 자기 점검을 만들 수 없다.
5. 계약 판정기마다 `except (ValueError, KeyError, IndexError)`만 잡아 그 계약의 실패로 기록. **`TypeError`·`OSError`는 잡지 않으므로** 미리 `ValueError`로 바꿔 올린다: T(J) 원소가 dict가 아니거나 키 누락(→ `d["name"]`가 TypeError), `linked_topology_files` 파일 없음(→ OSError). 그대로 두면 test가 예외로 끝난다(card 금지).
6. 각 test 함수에 if·try 밖 assert ≥ 1(V4 (3)(4)), print·logging 판정 금지.
7. 파일 읽기: `read_bytes().decode("utf-8")` 후 `\r\n`→`\n`(작업 트리 md는 CRLF).
8. 플래그 바이트: ` ⚠️` = `" \u26a0\ufe0f"`, ` ℹ️` = `" \u2139\ufe0f"`, `⚡` = `\u26a1`. 소스에 이스케이프로 적으면 편집기 정규화 사고가 없다.
9. 절 머리는 **접두** 일치(실제 머리 줄은 `## Net별 연결 표 (이 net에 물린 모든 단자)`처럼 괄호 설명이 붙는다). 표 머리 행은 **문자열 완전 일치**.

**합성 자기 점검 기대(card 그대로 -- 프로토타입이 전부 확인)**: 통과 9(기준, CRLF, `소스:` 경로, Net 플래그 제거, ` ℹ️`로 바꿈, 플래그 절 문장, 행 순서 섞기, 기준 짝 2, 기준 짝 2 Value·Implementable 변경) / 거부 23 + 빈 폴더 1:
Gate 바꿈 {2}, 소자 행 중복 {2}, 소자 행 삭제 {2}, 소자 절 없음 {2}, 소자 표 머리 다름 {2}, json 수동 C2 추가 {3,4,5}, 수동 표 절 삭제 {3}, Terminals 뒤집기 {3}, json에만 I1 {3,4,5}, 기준 짝 2 md vs 기준 json {3,4,5}, ideal source 절만 더함 {3}, Net 단자 삭제 {4}, 단자 수 열 {4}, 여분 net 행 {4}, net 행 중복 {4}, 백틱 없음 {4}, 다른 플래그 문자 {4}, 합계 수동소자 수 {5}, 합계 줄 없음 {5}, 합계 문형 {5}, H1 이름 {1}, 파일 이름≠topology_name {1}, 짝 json 없음 {1}, md 0개 {1}.
주의: '파일 이름 다름' 케이스는 H1도 파일 이름으로 맞춰야 {1} 하나로 끝난다(H1·topology_name 둘 다 계약 1이라 어느 쪽이든 {1}이지만, H1을 json 이름으로 두면 (d)도 함께 실패 -- 집합은 여전히 {1}).

**자기 실행(작성자 확인용, 판정 아님)**: test worktree에서
`PYTHONPATH=<게이트 캐시> $PY -P -m pytest -c <캐시>/pytest_gate.ini --rootdir=<wt> --confcutdir=<wt> --gmid-phase=2 --gmid-strict= <wt>/skills/analog-gmid-design/assets/tests/contracts/test_topology_md_sync.py` -- 약 13초, 전부 PASS여야 한다(base에 D 포함). D^ 실행은 auditor 몫이라 하지 않아도 된다.

**소요 예상**: 작성 20~30분(프로토타입 ≈ 420줄), 자기 실행 15초.

---

## 2. gmid-verification-auditor 브리프(순서 3·6)

test-only 모양(design 05 §9.2-4): `old..new^` = Role: test 커밋 T 하나, code 커밋 없음, `red` 필드 금지(00-common §8.1) -- 계약 8 (b) 결과는 `checks.V2.basis`·`reproduced_numbers`에. 기준 P10 판정 기록 `.ai/verification/20260930-p10-df23-inventory.json`과 같은 형태.

| V | 기대 | 증거 명령(격리 복제본·base 판 게이트 캐시) | 사전 시험 소요 |
|---|---|---|---|
| V1 | PASS. T에서 전체 `--gmid-phase=2 --gmid-strict=` -- 기존 871(+ D 뒤 병합된 card가 더한 test) 전부 base와 같은 결과 + 새 test 전부 PASS. 사전 시험: 906 passed 15 xfailed | `PYTHONPYCACHEPREFIX=<고유> PYTHONPATH=<캐시> $PY -P -m pytest -c <캐시>/pytest_gate.ini --rootdir=<iso> --confcutdir=<iso> <iso>/skills/analog-gmid-design/assets/tests --gmid-phase=2 --gmid-strict= -rA` | 6분 30초(base도 같은 시간 -- 병렬 가능) |
| V2 | PASS. 계약 8 (a) base에서 새 test 전부 PASS, (b) `measured_at`=D^ 복제본 + T의 새 파일(`git cat-file blob T:<path>`)만 복사 → **assertion 실패 1건 이상, 수집 오류 0**, 메시지의 `계약 <k> <n>` 쌍 = 정확히 {(2,folded_cascode),(4,folded_cascode),(3,current_reuse_telescopic_ota),(4,current_reuse_telescopic_ota),(5,current_reuse_telescopic_ota)}, 나머지 4개 md는 쌍 0, 합성 자기 점검 test 전부 PASS. `git rev-parse D^` == `measured_at` | 위 형식에 `-p merge_gate --continue-on-collection-errors`·`GMID_RED_CAPTURE=<out>`를 붙여 D^ 복제본의 새 파일만 실행(P10 계약 8 명령과 같은 형태). 쌍 추출은 auditor 스크립트로 assert 메시지에서 `^계약 (\d) (\S+):` 정규식 | 15초 |
| V3 | PASS `targets [] mutants 0` | `$PY <캐시>/mutate_changed.py --root <iso> --base <base> --head <T> --pytest-ini <캐시>/pytest_gate.ini --python C:/Python314/python.exe --gmid-phase=2 --gmid-strict= --out <out>` | 2분 30초 |
| V4 | PASS. `--interface-card` 단독은 exit 2(피검 0행) -- A/*.py 최상위 def·class 전부(0f23786에서 373)를 `--subject`로. findings 전부 규칙 (2) NO-SUBJECT, (1)(3)(4)(5) 0. basis에 기대값별 oracle 대조: library 판정 = (d) json 데이터(계약 2~5 정의), 합성 = (a) card '거부해야 할 입력' 목록 전부 포함 여부 | `md_sync_kit/v_tools.sh`(V4 부분) 또는 `$PY <캐시>/test_lint.py --root <iso> --base <base> --head <T> --module-dir skills/analog-gmid-design/assets --subject …` | 20초 |
| V5 | PASS `findings [] diff_paths []`(새 파일 추가뿐) | `weakening_diff.py --root --base --head` | 2초 |
| V6 | PASS `targets []` | `source_lint.py --root --base --head` | 52초 |
| V7 | PASS `new_defs []`(도입 2 -- N/A 불가) | `reachability.py --root --base --head` | 2분 |
| V8 | N/A `도입 4: …` | -- | -- |
| V9 | N/A `도입 6b: …` | -- | -- |
| V10 | PASS. card '재현할 수치'를 auditor 스크립트로 json에서 직접 셈: md 6, md별 (소자, 수동, ideal, net) = json에서 다시 센 값(card 수 옮기지 말 것), 계약 8 (b) 쌍 5·실패 test id 수·D^ 통과 합성 test 수, 계약 9 Change-Id 커밋 수·경로 3·D blob 일치, 계약 6 금지 import 0 | auditor 스크립트(AST import 검사 + `git log --format='%H %(trailers:key=Change-Id,valueonly)' <measured_at>..<new>` + `git diff-tree --no-commit-id --name-only -r`) | 1분 |

**계약 9 주의**: `<measured_at>..<new>` 사이에는 runbook의 Change-Id 없는 문서 커밋(`appr`, `e2`, `e2appr`, `ubf`)이 끼고, `c1`은 D^ 자체다(= measured_at). Change-Id 커밋 = D, card(spec+interface) 커밋, T, audit 4개. card 커밋의 spec·interface 두 경로와 `.ai/verification/20261001-topology-md-sync*`를 빼면 경로 3개.
**계약 6**: 새 파일 AST의 `Import`/`ImportFrom` 모듈 이름 ⊆ {collections, json, pathlib, re, pytest, …표준}, 문자열 `importlib`·`__import__`·`runpy`·`subprocess` 0, `open(... "w")`·`write_text`·`write_bytes` 0.
**환경**: MSYS2 bash에서 `APPDATA` export, `PYTHONIOENCODING=utf-8`(판정 기록 JSON을 cp949로 읽으면 깨진다 -- 사전 시험 실측). 격리 경로는 auditor 고유 `C:/g<번호>`.
**총 소요 예상**: 순서 3(freeze·base·계약 8) 15분, 순서 6(V1 두 번 병렬 + V3~V7 + 기록) 25분.

---

## 3. 함정(사전 시험에서 찾은 것)

1. **T(J) 형식 위반의 실패 집합이 card에서 하나로 정해지지 않는다.** card는 "그 md는 계약 2 FAIL"이라고만 한다. 계약 4(N(J))·5(len T)도 T(J)를 쓰므로 판정기 안에서 ValueError로 기록하면 {2,4,5}, 계약 4·5를 건너뛰면 {2}. 실제 library(`_TEMPLATE`은 md 없음)와 card 합성 목록 어디에도 이 경우가 없어 판정·계약 8에 영향 0. test-author가 이 경우를 자기 점검 케이스로 단정하면 auditor가 card 문장과 대조할 근거가 없다 -- **단정하지 말 것**(프로토타입은 {2,4,5}).
2. 잡는 예외가 3종이라 `TypeError`(dict 아닌 원소)·`OSError`(연결 파일 없음)는 미리 ValueError로 바꿔야 한다(§1-5).
3. runbook `d`를 단독 실행하려면 상태 파일에 `C1=<HEAD>`가 있어야 한다(`stage_d`가 `HEAD == st_get C1`을 확인). 옵션은 반드시 단계 이름 **앞**. 실제 흐름에서는 c1이 먼저라 measured_at = c1 커밋이고 gate master가 아니다(c1은 library를 안 건드려 blob 기대는 그대로).
4. EL1 `role_guard` hook이 bash 리다이렉트 대상에 변수 경로(`> $S/x.json`)가 있으면 명령을 거부한다 -- auditor·test-author 브리프 명령은 스크립트 파일로 실행하거나 리터럴 경로를 쓴다(`md_sync_kit/v_tools.sh`).
5. V4는 `--interface-card` 단독이면 exit 2 -- 판정 기록에 ERROR로 적지 말고 `--subject` 373 방식으로(P10 선례).
6. 합성 '판정 대상 md 0개' 자기 점검은 디렉터리 단위 함수가 있어야 쓸 수 있다(§1-4).
7. `test_lint` findings가 `NO-SUBJECT`뿐인 것은 독립의 증거가 아니다 -- V4 basis는 oracle 대조 문장으로 채운다.

## 4. 키트 파일(`_drafts/md_sync_kit/`)

| 파일 | 내용 |
|---|---|
| `test_topology_md_sync.prototype.py` | 오케스트레이터 사전 시험용 프로토타입 -- **test-author·auditor에게 건네지 않는다**(작성자≠검증자, card '누가 무엇을 쓰는가'와 같은 취급) |
| `sandbox_stage_d.log`, `sandbox_D_run.txt`, `sandbox_Dparent_run.txt` | runbook `d` 출력, D·D^ 실행 결과(D^ assert 메시지 5쌍 원문) |
| `sandbox_v4.json`, `sandbox_v3_v5_v6_v7.jsonl` | 게이트 도구 출력 |
| `v4_subjects.py`, `v4_subjects_0f23786.txt` | V4 `--subject` 목록 생성기와 0f23786 결과(373) |
| `v_tools.sh` | V3~V7 일괄 실행(리다이렉트 hook 회피용 스크립트) |
