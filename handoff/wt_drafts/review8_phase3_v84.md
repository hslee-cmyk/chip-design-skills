# 8차 검토 -- Phase 3 design 30 초안 v8.3 → v8.4 (델타 검토, 독립 검토자)

판정: **ready to ask**(질문을 올려도 된다). v8.4가 들인 결함 중 사용자 승인을 틀리게 하거나 계획을 실행할 수 없게 만드는 것은 없다. 경미한 문구 5건은 아래 §5 목록에 둔다(질문 전에 고치면 좋지만 막는 사유는 아니다).

검토 범위: `*.v8.3.md` 사본과 현재 판의 diff -- `draft_phase3_design_v8.md`, `phase3_approval_question.md`, `p3_doc_amendments.md`, `draft_p3_d0a.spec.md`, `phase3_revision_log.md` '초안 v8.3 → v8.4' 절.
환경: gate `master` = `git -C <repo> rev-parse gate/master` → `dd60db6`(질문 머리와 같다). 스크래치 `C:/g178`(`git clone --no-local`, origin 제거, 빈 hooksPath, 끝에 삭제). 메인 저장소 `git status --short`는 검토 전후로 같았다(36줄, diff 0), HEAD·reflog도 그대로.
Python 3.14.2. 주의: 하위 `bash` 스크립트 안에서는 `APPDATA`를 명시해야 user-site numpy가 잡히고, `VAR=x bash script` 형태로 준 환경 변수는 이 도구 환경에서 자식 python까지 전달되지 않았다. 그래서 변형 실행은 인자로 export해 다시 쟀다(아래 값은 다시 잰 값이다).

## 1. FU card (D-29) -- `from __future__ import annotations` 두 줄

`dd60db6` 복제본(`repo`)과, 거기에 DR 28행 앞·ACF 38행 앞으로 한 줄씩만 더한 복제본(`fut`, LF 유지)을 비교했다.

| 확인 | 결과 |
|---|---|
| 코드 객체(`compile`, `co_consts` 재귀, qualname별 `co_code`·상수 repr·names·varnames·free/cellvars·flags(future 비트 제외)·인자 수) | 함수 몸체는 모두 같다. 다른 것은 `<module>`(import 줄이 더해짐)과 `__annotate__`뿐이다(DR 5·ACF 4). 몸체 qualname은 DR 12·ACF 5로 design §6.5의 '17'과 같다 |
| 실행 시점(두 판을 각각 import) | 모듈 이름 차이는 `annotations` 하나. `__annotations__`가 값에서 문자열로 바뀌는 함수: DR 5(`_kv_table`·`assemble_report_data`·`build_topology_device_table`·`render_html_report`·`save_html_report`), ACF 4(`_as_set`·`_theta_evidence_for_pair`·`audit_topology`·`render_report`) |
| 주석을 읽는 곳(추적 `.py` 전체 grep: `get_type_hints`·`__annotations__`·`annotationlib`·`get_annotations`·`inspect.signature`/`signature(`·`dataclasses.fields`/`fields(`·`pydantic`·`__annotate__`) | DR·ACF 객체를 읽는 곳은 0이다. `inspect.signature`는 SD(`test_dup_kcl_edges.py`)·SR(`test_dup_w_calc.py`·`probe_mirror_ratio_error.py`)만 대상이고, `dataclasses.fields`는 `probe_metric_tiers.py`의 SR `SizingContext`뿐이다. pydantic 0. DR·ACF에는 dataclass·NamedTuple·TypedDict·ClassVar·typing import가 없어서 PEP 563 문자열화가 클래스 생성에 닿을 곳도 없다. DR·ACF를 import하는 곳에서 `dir`·`vars`·`getmembers`·`__dict__`로 모듈 이름을 세는 곳도 0이다(`.ai/verification`의 `exec(..., mod.__dict__)`는 하네스 모듈 자신의 dict다) |
| 전체 test(`pytest -c tools/gates/pytest_gate.ini --gmid-phase=2 --gmid-strict=`, junit) | 두 판 모두 **1047 passed·15 xfailed**(295.7 s·291.9 s). test id 1062개 집합이 같고 결과가 다른 id는 0이다 |
| E-LIB(`e_lib.py`, p9 사본 -- 판정 기록 6곳의 사본이 md5로 모두 같다) | 같은 체크아웃 경로 `C:/g178/iso`에서 두 판의 `hash`가 같다: `1d2e3bf6…`(P2D 기록값과 같음). 참고: `e_lib.py`는 `stick_diagram`만 import하므로 DR·ACF 변경과는 원래 무관하다 |
| E-INST(`e_inst_p3.py` 문안, `folded_cascode`·`current_reuse_telescopic_ota`) | 같은 경로에서 두 판의 출력 22키가 모두 같다. crt stdout 차이는 SLSQP `elapsed=` 시간뿐이다 |
| 게이트(base 판 `tools/gates`, `dd60db6` → FU 헤드) | V3 PASS(대상 DR·ACF 2파일, `mutants` 0), V6 PASS(`findings` []), V7 PASS(`new_defs` []) |
| D0a `import_conflicts`(`__future__` 부분만 독립 구현) | FU 없이: MOD2·MOD4·MOD9 세 곳이 갈린다(§6.5 '세 MOD 모두'와 같다). FU 뒤에는 0이다. 그래서 '만들면 배선'(D0b exit 0 단언이 FU 미병합을 잡는다)이 실제로 성립한다 |

**code card인가, 순서·DAG에 들어 있는가**: 들어 있다.
- §8 표 FU 행: equivalence(test 커밋 0), 판정 (c)는 V3 0·V6 0·V7 0·E-LIB·E-INST = base·몸체 코드 객체 동일.
- §8.1 순서 줄 `T0, FU, G1(32) → D0a → D0b`, 의존표 `FU → D0b`, `Phase 2 DoD PASS → T0·FU·D0a·D0b`.
- D-23(`phase: 3`), D0b base 사슬(`… → B33 → G1 → FU → D0a`), card 수 16 → 17(§8 끝, 질문 UD-0).
- 동결(D-27)은 D0b 병합부터라 'D0b 전 병합'과 겹치지 않는다. design에 '16건' 같은 옛 수치가 남은 곳은 없다(grep).
- FU spec card 초안은 아직 없다. 다만 §8.1이 'FU 준비 가능'으로 적어 두었으니 design 승인을 막지 않는다.

## 2. D-31 배정 규칙과 A-1 보정 8건 -- 독립 재현

방법: `dd60db6` 복제본에 G1 시제품을 설치했다(`g1_kit/install_proto.py`, `g1_core.py` `b3c4e391…`). D0a 시제품(`move_plan_proto.py` `d2f3da97…`)은 키트의 변형 스위치를 쓰지 않았다(작성자 스크래치는 삭제됨). 대신 **D0a 계약 2 v8.4 문언만 보고** 규칙 부분을 다시 구현했다.
- 모듈 docstring 제외(`SourceIndex.tree`).
- A-K를 A-5보다 먼저 적용.
- A-3·A-4 칸 선착석, 반복은 올리기만 함(단조).
- A-4·A-2·A-5 승격과 MOD7 상한.
- A-6, A-7.
- `__future__` 갈림.

N3.10 개정은 문서 개정 문안의 '현재 `plan.md:N`' 블록을 그대로 대조·교체했다(D-19 (가), 521~528행). '현재' 블록 7개가 모두 일치했다.

| 트리 | 결과 |
|---|---|
| v8.3 개정 + 원래 시제품(키트 재현) | `upward` 34·`cycles` 1·`unassigned` 18 -- 키트 값과 같다 |
| v8.3 개정 + v8.4 규칙 | `upward` 8·`cycles` 2·`unassigned` 1(`signal_path_nodes`). 남은 위쪽 간선은 모두 A-1 토큰 원천 6건과 `check_symmetry_dispositions` → `find_hub_merge_candidates`·`find_matching_candidates`(상한이 남긴 것)이다. 상한 없는 변형(설계 기록의 7)과 정확히 같은 상태는 아니지만 'A-1 원천이라 규칙으로 못 푼다'는 결론은 같다 |
| **v8.4 개정(§1+§9) + v8.4 규칙 + FU** | **`upward` 0·`cycles` 0·`unassigned` 0·`conflicts` 0·`import_time_high` 0·`import_conflicts`(future) 0·MOD7 파일 밖 MOD7 0·배정 403·`reg_mismatch` 78** -- F4v84와 같다. 규칙 분포 A-4 230·A-5 64·A-1 59·A-2 38·A-6 7·A-7 2·A-K 2·A-3 1 |
| 같은 트리, 상한 끔 / 승격에 keep 번호 포함 / A-5 후보에서 keep 제외 | 세 변형 모두 같은 결과다(상한 유무 같음 -- 주장대로) |
| `find_hub_merge_candidates` 토큰만 뺀 개정 | 상한 있음: `upward` 2(`check_symmetry_dispositions` → hub·matching). 상한 없음: `upward` 1(`load_topology` → `propose_device_roles_gap_fill`, 그것이 SD 파일 단위라 'MOD7 밖 0' 단언으로는 안 잡힌다) -- D0b 검토 S2의 근거와 같다 |
| MOD6 → MOD8 네 토큰 중 1개만 / 3개만 | `upward` 4 / 1 -- 주장대로 |
| 재생성(`regen_registry.py --write`) 커밋에서 다시 `plan` | exit 0·`reg_mismatch` 0·(단위 → MOD) 사상 차이 0(멱등). `rule`은 11단위가 바뀐다(A-5/A-6/A-7/A-3 → A-4·A-2). §8 D0b 행의 "`근거 규칙` = 재생성 시점 규칙, test는 집합 소속만"이 이 현상을 정확히 다룬다 |
| 승격으로 칸과 달라지는 A-4 단위 | **32**(MOD2 → MOD3 12·MOD4 → MOD5 11·MOD6 → MOD8 4·MOD3 → MOD4 3·MOD4 → MOD9 1·MOD2 → MOD8 1), 32개 모두 함수다 |

**'열 = 하한'을 UD-0 (d)로 정직하게 제시했는가**: 그렇다.
- (d)는 517행 두 문장의 충돌을 원문으로 보여 준다.
- 기본안이 '옛 열 값은 정본이 아니라 하한'이 된다는 점과, D0b가 열을 다시 써서 열 = 이관표로 되돌린다는 점을 적었다.
- MOD7로는 올리지 않고, 그런 경우는 따로 묻는다는 점도 적었다.
- 대안('열 정본 + 32개를 표에 하나씩')과 그 대가(표에 이름이 쌓이고, 토큰도 결국 칸을 덮어씀)를 나란히 두었다.
- 수정 요청 선택지에 (d) 대안이 있다. D-31 행과 질문의 '32'는 위 재현과 같다.
- 보강 권고 하나(막는 사유는 아님): 32개 중 12개가 계획 MOD2 책임 '구조 제안'의 `propose_*`·`check_symmetry_dispositions` 등이고, 이들이 MOD3로 간다는 분해를 한 줄 넣으면 사용자가 무엇이 움직이는지 더 잘 보인다(§5 m2).

## 3. 승인 질문

- **질문 수와 대상**: 넷(UD-0·D-19·UD-5·UD-1)이다. A2-③은 다시 묻지 않는다. UD-0의 '기준에 닿는 기본값'은 (a)~(d) 네 개다.
- **사실 대조**:
  - 기준 `dd60db6`: `0f23786..dd60db6`에서 엔진 최상위 `A/*.py`·`tools/`·`workspaces` 변경 0, 계획서는 839행 한 줄, 레지스트리는 524행 뒤 77줄 덧붙임(목적지 열 무변경).
  - `5f643a9` = P2D(`phase2-dod.md` 대상).
  - 레지스트리 §7 `보류(Phase 3)` 칸은 9개(495·505·509~515행)이다.
  - 계획 517행 원문, MOD7 책임 "레이아웃만(구조 유도 함수는 MOD2·MOD3로 나간다)" 원문을 확인했다.
  - 추적 안 된 `.py`는 5개(hooks 4 + U-03 1)이고, U-03 9·10행 import 원문도 맞다.
  - (c) 문장 끝 'v8.4: 준비 card가 E-LIB·E-INST 값을 바꾸지 않는다'는 §1에서 재현했다.
- **원문 인용**:
  - U-02 1항 원문 "보류(Phase 3 모듈 이동·Phase 4 배선)"은 `.ai/approvals/20260923-u02-d-list.md`와 글자 그대로 같다. '재검토' 문장 "승인표를 바꾸는 것은 사용자 승인 사항이다"도 같다.
  - `20260930-phase2-e4-baseline`의 기본안·대안 문언과 답 "둘다 기본안으로 진행해"는 기록과 글자 그대로 같다.
- **해시**(sha256 앞 16자리, 지금 디스크 값을 다시 계산): 목록의 10개가 모두 일치한다.
  - design `ba5131aba3f07b0e`, 문서 개정 `bf5c0c5f311fec40`, G1 `cacf06adf1bc5bba`, T0 `f490002034a57f8d`, D0a `b6f7dc22157596b5`.
  - `e_inst_p3.py` `7d26134ad00ec504`, `e_lib_p3.py` `c6b82fc7b4cd974c`.
  - 판정 python(§10 셋째 `PYEOF` 블록 1045~1093행, CRLF 유무 무관) `ae6422d680dae2ab`. 이 블록은 v8.3 판 987~1035행과 diff 0이다.
  - `p3v83_judge_scenarios.sh` `7c9be52da0fc7ff0`·출력 `52bbe243777d6d65`, UD-5 기록 초안 `8236cb3377cc7463`.
  - 질문 파일 자신 `203a43319d9e6012`(개정 기록 값과 같음).
  - v8.3 사본 값(`5ea5683e…`·`bc1958b4…`·`5104bfe4…`·D0a 사본 `2f864846…`·pre-kit `1f9592d4…`)도 기록과 같다.

## 4. 무효로 기록된 측정

개정 기록에 따르면 `fin_one`·`fin_three`·`cap_*` 첫 판은 재생성된 레지스트리 위에서 돌아 무효였다. 그 뒤 `exp.sh`를 고쳐 다시 쟀다. 그 스크립트는 삭제되어 직접 볼 수 없다. 대신 위 §2를 **깨끗한 복제본**에서 다시 쟀다. 측정마다 별도 브랜치(레지스트리는 `dd60db6` 판)를 썼고, 재생성은 별도 브랜치 `regen`에서만 했다.

최종 수치가 모두 같다: 0·0·0, 배정 403, `reg_mismatch` 78, 멱등, 상한 유무 같음, hub 없이 2, MOD6 1개 4·3개 1, 승격 32.
→ design 부록 A F4v84·문서 개정 §9 '적용 실측'·D0a 근거 문단의 값은 깨끗한 실행의 값과 일치한다.

## 5. 경미(목록 -- 루프 종료 조건 밖, 질문 전 선택 수정)

- m1. design §9.1 UD-0 행은 D-31을 '기준에 닿는 기본값'(D-9·D-17·D-28) 묶음이 아니라 'v8.4 사실로 드러낼 것'에 두었고, 끝 열 "…(D-28)은 사용자 몫"에도 D-31이 없다. 질문·D-31 행·질문 머리 '판단'은 (d)로 '기준에 닿는다'고 적는다. 한 문장 정렬을 권한다.
- m2. 질문 (d)에 32개의 분해(특히 MOD2 '구조 제안' 함수 12개 → MOD3)를 한 줄 넣으면 '하한' 기본안의 실제 효과가 더 잘 보인다.
- m3. 질문 ④ "그 9개 함수"는 실제로 9**단위**다(함수 8 + 문장 `_CSS`, §6.5). 그리고 '동작이 같음' 근거에 '함수 `__annotations__`가 값에서 문자열로 바뀌지만 그것을 읽는 곳 0'을 한 마디 덧붙이면 정확하다(design §6.5에는 있다).
- m4. D0a 계약 2 v8.4 문언의 모호 두 곳:
  - (i) 승격의 'R(u) 배정 MOD 최댓값'에 `--keep` 도구 번호가 드는지.
  - (ii) A-6 결과의 '같은 상한'은 칸이 없어 공허하다.
  - 지금 트리에서는 어느 쪽으로 읽어도 결과가 같다(§2 변형). D0a 역할 구현 전에 한 줄로 정하면 된다.
- m5. FU 동작 불변 근거의 E-LIB는 `e_lib.py`가 `stick_diagram`만 import해 DR·ACF와 원래 무관하다. 증거로서 가치는 0에 가깝다(틀린 말은 아님). 실질 근거는 E-INST·전체 test·코드 객체다.

## 6. 재현 명령 요지(스크래치는 삭제)

- `C:/g178/repo`(dd60db6)·`fut`(+ FU 두 줄): `probe_co.py`(코드 객체), `probe_rt.py`(실행 시점 주석·이름), pytest 두 번(junit 비교), `iso`에서 `e_lib.py`·`e_inst_p3.py` 두 회로씩, base `tools/gates/{mutate_changed,source_lint,reachability}.py --base dd60db6 --head <FU>`.
- `C:/g178/d0b`: 브랜치 `amd83`(v8.3 개정), `amd`(v8.4 개정), `amdfu`(+FU), `nohub`, `m6_1`·`m6_3`, `regen`. 작업 트리에 G1 시제품 설치. `mp_orig.py`(시제품 그대로)·`mp84.py`(계약 2 v8.4 독립 구현) `plan`을 design §6.3 인자(`--split` 5개, `--keep audit_current_forced.py`, `--aliases optimizer`)로 실행.
