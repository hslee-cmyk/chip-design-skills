# D0a·D0b 착수 준비 검토 r1(수정 반영 확인) -- 2026-10-06

검토자는 수정 작성자가 아니다. 대상은 `review_d0a_d0b_ready.md` 지적을 반영한 여섯 파일이다(`draft_p3_d0a.spec.md`·`d0a_briefs.md`·`d0a_launch.sh`·`draft_p3_d0b.spec.md`·`d0b_briefs.md`·`d0b_launch.sh`, 반영 전 사본 `*.pre-rdy.bak`).
기준 gate는 `master` `7243f28`이다.
- 실제 저장소는 `git -C`로 읽기만 했다. 시작·끝 모두 HEAD = `gate/master` = `7243f28`, `status --porcelain` 38줄 md5 `76eea762…`, reflog 첫 줄이 같다.
- 역할 브랜치는 시작 때 `role/test/20260930-b34-grammar-explicit` 하나였고, 끝에는 같은 card의 `role/audit`·`role/code`가 더해져 셋이다. 나는 실제 저장소에서 브랜치·worktree 명령을 쓰지 않았다(다른 세션의 B34 진행으로 보인다).
- 스크래치는 `C:/g289`만 썼다.
  - 작업 트리 저장소에서 `git clone -c core.autocrlf=false --no-local --no-hardlinks`로 복제했다. origin을 지우고 빈 hooksPath를 두었으며, TMP·TEMP·TMPDIR는 `C:/g289/tmp`로 잡았다.
  - 모래상자 bare gate `C:/g289/gate.git`를 만들고, `gate_config.json`의 `gate_path`·`workspace_path`를 바꾼 커밋 `0886104`를 맨 앞에 두었다.
  - 끝에 `C:/g289`를 지웠다.
- 저장소 경로는 모두 인자로 넘겼다(`--repo`·`--state`·`--wt`·`--draft-spec`·`--iso`).

## 판정 요약

| card | 판정 | B | S | minor |
|---|---|---|---|---|
| D0a | **착수 가능**: 지적한 S 2건이 해소됐다. minor 1건(m1)은 반영됐고 4건(m2~m5)은 아직 반영되지 않았다 | 0 | 0 | 4(이월) |
| D0b | **착수 가능**: S1이 해소됐고 minor 6건도 모두 반영됐다. 새 minor 3건은 막는 결함이 아니다 | 0 | 0 | 3(신규) |

`bash -n`: `d0a_launch.sh`·`d0b_launch.sh`·`launch_common.sh` 모두 통과했다.

---

## D0b-S1 (S-7 요약 캐시) -- **해소, 재현으로 확인**

수정 내용: 요약 캐시 이름을 `<상태>.plan.<H>.json.sum.<초안 sha256>.json`으로 바꿨다. `DRAFT_SHA`는 표준 입력으로 받은 `sha256sum` 값이다.

모래상자 사슬은 다음과 같다: `0886104` → FU 대역(`p3fq_kit/fu_standin.py`) + G1 시제품(`g1_kit/install_proto.py` 13:24판, `7243f28` 위에 "installed 4") + `tools/migrate/move_plan.py` = `p3kit_m1/move_plan_sim.py`(문장 키 기본값 `names`) = `869cb0f`.
- `plan`: 46초, exit 1, 배정 403, `reg_mismatch` 80, 여섯 목록 0.
- B26-1 미병합 판이라 표본 `RailDeclaration`·`rail_declaration`은 plan에 없다.
- 그래서 이 두 행을 지운 초안 사본(`d_ok`)과, 거기서 `GmIdLUT` 기대만 `theta_search`로 바꾼 사본(`d_bad`)을 **같은 경로**에 번갈아 넣고 `conds`를 돌렸다.

| 스크립트 | 순서 | S-7 |
|---|---|---|
| 반영 전(`.pre-rdy.bak`) | ok → bad | 충족 → **충족**(낡은 요약을 그대로 씀, 결함 재현) |
| 반영 뒤 | ok → bad → ok | 충족 → **미충족** `[['GmIdLUT', 'theta_search', ['gmid_lut']]]` → 충족(ok 키 캐시를 다시 씀) |

다른 캐시 오염 경로도 확인했다.
- **gate 이동 뒤의 낡은 plan JSON**: 빈 커밋으로 모래상자 gate를 `dc33631`로 옮기고 `--iso` 없이 `conds`를 돌렸다.
  - "plan 캐시가 없다 -- --iso …"가 나오고 S-4·S-5·S-7은 규약오류(exit 1)다. plan·MP_ARGS 캐시는 gate 전체 sha가 키이므로 옛 판의 캐시를 다시 쓰지 않는다.
  - 격리 복제본도 `base == H`를 단언한다.
- **상태 파일을 다른 gate 판에서 다시 쓰는 경우**:
  - `pre`가 상태 파일과 `ids.*`를 지운다.
  - `card`·`final`은 `GATE_BASE == gate/master`, `CACHE` 같음을 다시 본다.
  - `card`는 `conds_eval`을 다시 돌린다. 각 실행이 `DRAFT_SHA`를 새로 계산하므로, 중단 뒤 단계별로 이어 해도 표를 고친 초안은 다시 계산된다.
- 옛 이름 `.sum.json`은 새 스크립트가 읽지 않는다.

**새 minor D0b-r1-m1: 요약 키에 스크립트 쪽 입력이 없다.**
- 요약은 `RULE_IDS`·`SIX`·`D11NAME`와 heredoc 요약 코드에도 의존한다. 그런데 키는 (H, 초안)뿐이다.
- 멈춤 절차 뒤 스크립트 상수만 고치고 같은 판·같은 초안으로 다시 재면 `bad_rules`·`d11_rules`·`lists`가 낡은 값으로 나온다.
- `cond_7`의 "d11_rules 없음 → 옛 판 캐시" 검사는 키가 빠진 경우만 잡는다.
- 고칠 것(둘 중 하나):
  - 키에 `sha256(스크립트 파일)`을 더한다.
  - 원래 검토의 (나)처럼 요약은 늘 다시 계산한다. 요약은 plan JSON을 읽는 1초 미만 작업이다.

**새 minor D0b-r1-m2(반영 전부터 있던 문제): 실패한 plan도 캐시에 남는다.**
- 격리 실행이 일시 오류로 exit 2를 내도 `$STATE.plan.<H>.json`·`.rc`가 남는다. 같은 판에서는 계속 S-4 규약오류다.
- fail-closed라 막는 결함은 아니다. 하지만 메시지가 그 캐시를 지우라고 안내하지 않는다.
- S-4의 exit 2 분기 메시지에 캐시 경로를 덧붙인다.

## D0a-S2 (조건 8, (e1)·(e4) AST 스캔) -- **해소**

**범위**
- 설계와 맞는지:
  - 대상 = design 30 §6.3 `MP_ARGS`의 `--split`(gate `7243f28` 467행 첫 블록 -- §6.3이다. §10의 797행 사본도 같다) + A-0(N3.10 `mod_table` 줄기 중 트리에 있고 `--split`에 없는 파일).
  - 이것이 D0a 계약 2의 '배정 대상 = `--split` 파일의 단위 + A-0 대상'이다.
- 레지스트리 함수 표:
  - 머리에 `함수`·`이관 목적지`가 둘 다 있는 표만 읽는다(계약 2, 키트 v9).
  - 칸은 `role_paths._split_cells`로 나눈다.
  - 함수 칸에서는 첫 백틱 토큰의 `.` 앞만 쓴다(계약 2 UD-6, 메서드 행은 클래스).

**제외 구성이 원칙에 맞는지**
- 단위는 G1 `SourceIndex.units`다. G1 시제품 `g1_core.py`도 main 블록(`_is_main_block`)과 `Import`·`ImportFrom`을 건너뛴다.
- 모듈 docstring 제외는 D0a 계약 2 v8.4다.
- 스캔의 `bound()`는 시제품 `_g1_bound_names`와 줄 단위로 같다. 빠진 `TypeAlias` 분기도 일반 `Name(Store)` 분기가 같은 이름을 잡는다.
- 스캔의 `is_main`은 gate `reachability._is_main_block`(비교 대상 중 `"__main__"` 하나라도 있으면 main 블록)보다 좁다(`len(comparators)==1`). 그래서 갈리는 경우에는 더 많이 보고하는 쪽으로만 틀린다.

**주입 시험(모래상자 `33b8091`)**
- `topology_library.py` 끝에 주입하고, A-0 파일 `gmid_lut.py`를 새로 만들었다.
- `conds` 조건 8과 **내 독립 스캔**(`_g1_bound_names` + gate `_is_main_block` + 정규식으로 읽은 MP_ARGS·N3.10·레지스트리)의 출력이 같았다.

| 주입 | 기대(계약 2 단위 정의) | 조건 8 |
|---|---|---|
| 같은 이름 최상위 def 둘 | (e1) | (e1) `miller_ota_topology` |
| 모듈 최상위 `if` 블록 안 def가 기존 최상위 def와 같은 이름 | (e1) | (e1) `nmcnr_3stage_topology` |
| `try: import json as _jj / except ImportError: _jj = None` + `_jj = 3` | (e1) | (e1) `_jj` |
| 뒤집은 main 검사 `if "__main__" == __name__:` 안 def | (e1)(gate도 main 블록 아님) | (e1) `nmcnr_compensation_elements` |
| A-0 파일 `gmid_lut.py`에 `X_REV` 두 번 | (e1) | (e1) `gmid_lut.py::X_REV` |
| 레지스트리 행 `gm_from_fT`를 다른 split 파일에도 def | (e4) | (e4) `gm_from_fT -> sizing_recipe.py topology_library.py` |
| 클래스 속성 중복 `class _RevK: a=1; a=2` | 없음(최상위 단위 하나) | 없음 |
| `from os import path as _rev_pp` + `def _rev_pp` | 없음(import는 단위가 아님) | 없음 |
| main 블록 안 def가 최상위 def와 같은 이름 | 없음(main 블록은 단위가 아님) | 없음 |
| `if/else` 두 갈래가 같은 이름에 대입 | 없음(문장 단위 하나) | 없음 |

- 조건 8은 '미충족' exit 3이고 원인 안내 문구도 출력했다.
- 숨김 여부: 제외한 구성(import·main 블록·docstring·클래스 본문)은 D0a 도구도 단위로 세지 않는다. 그래서 거기 있는 중복은 도구 exit 2를 만들지 않는다.
  - import와 def가 같은 이름을 묶는 실제 재바인딩은 (e1)이 아니다. G1 `binding_origin` `multi`와 `check` `import-dup`이 맡는다.
  - 스캔 목적('plan이 exit 2가 될 트리를 미리 잡는다')에 대해 숨는 중복은 없다.
- 오탐 없음:
  - `7243f28`(모래상자 `0886104`): 대상 5파일, A-0 없음, 레지스트리 이름 363개, (e1) 0, (e4) 0. 독립 스캔도 같다(단위 217·168·7·6·5).
  - FU 대역 + G1 시제품 판(`869cb0f`)에서도 0이다.

## D0a-S1 -- 해소
- 브리프 122행 '단계 19개'와 179행 '19개 이름(… + UD-6 1 `reg-first-token`)'은 spec 'oracle' 절의 필수 단계 목록과 같다. 목록은 v6 4·v7 `import-time-high` 1·v8.4 10·conf `a1-conflict` 1·r1 `mod-imports-unresolved`·`edge-fail-closed` 2·UD-6 `reg-first-token` 1, 합 19다.
- 더한 문장 "두 구성(첫 구성 `upward` 1·exit 1, 칸을 `mj`로 바꾼 둘째 구성 exit 0)"은 spec 269~270행과 같다.

## D0b m5 (T0 선행 여부) -- 결정 맞음, 표기 minor

design 30 `7243f28` §8.1 의존 표 원문:
- `| B26-1 | T0 | T0 계약 10이 B26-1의 계수 test를 고친다 |`
- `| B34·b26pre·backfill·B26-1·B33·D0a | D0b | §6.4 -- 이관표를 D0b 자신의 base에서 처음 계산 |`
- `| FU(v8.4) | D0b | §6.5 -- … FU는 다른 card와 의존이 없다(엔진 두 파일 머리 한 줄씩 -- B33 뒤 아무 때나, D-27 동결 전) |`
- `| G1·T0·D0b | M1 | F5·F6, §9.1 |`
- 목록 줄: "실행 순서는 G1 → D0a, T0·FU는 G1과 독립(FU는 D0b 전)."

T0의 뒤는 M1뿐이다. 그래서 `PREDS`에서 T0를 빼고 브리프 4절을 'T0는 D0b 착수 조건이 아니다'로 맞춘 것은 표와 같다.
- T0가 D0b 뒤에 와도 막히지 않는다. D-27 동결 범위는 엔진·`tools/**`·레지스트리 열이고 test는 들지 않는다.
- T0가 D0b 측정과 착수 사이에 `A/tests/contracts`를 바꾸면 D0b 조건 8(`MEAS_PATHS`)이 다시 재게 한다(fail-closed).

**새 minor D0b-r1-m3: 브리프의 근거 문장이 한 줄 확정 순서를 빼먹었다.**
- 같은 절의 한 줄 확정 순서는 `Phase 3: T0, FU, G1(32) → D0a → D0b`라서 T0가 D0a 앞 묶음에 있다.
- 그런데 브리프 4절은 옛 "T0·FU·G1 → D0a"를 "FU·G1 → D0a"로 고치면서 표만 인용한다.
- 고칠 것: 근거 문장에 "한 줄 순서의 `T0, FU, G1`은 쉼표 묶음(순서 없음)이고, 'D0b 전' 제약은 FU에만 있다(목록 줄)"를 한 구절 더한다. 그래야 읽는 사람이 모순으로 보지 않는다.

## 문구 수정 확인(사실 대조)

| 수정 | 확인 |
|---|---|
| D0a m1(spec 334행), D0b spec 233행 'r1 미반영' 세 곳 | 원래 검토의 m1 측정 문장과 같다 |
| D0b m1 '커밋됨 -- gate `36e170e`' | `36e170e`가 `.ai/approvals/20260930-30-module-split-design.md`를 처음 더한 커밋이다(`--diff-filter=A`). `6c8287f`(design 30)와 함께 `7243f28`의 조상이다 |
| `29d2fc2`(계획 1+/1−)·`300fd65`(승인 기록 70줄)·`7f67ec3` | 모두 `7243f28`의 조상이고 커밋 내용도 문장과 같다 |
| D0b m2 계약 11 (b)·브리프 1절 2항 `verdict != "ERROR"` | 두 곳의 문구가 같다 |
| D0b m3 브리프 V10 ⑥ R-A2 | spec 표 180행(T-A `conflicts` 첫 단언·T-B·T-C·T-D PASS·T-E `compute_metric`)과 같다 |
| D0b m4 계약 12·브리프 7항 'MP_ARGS 줄 밖 0' | 뜻은 맞다. test가 `MP_ARGS`를 여러 줄 리스트로 쓰면 'MP_ARGS 줄'이 모호하다. "`topology_library.py` 인자 리터럴 한 곳 밖"이 더 정확하다(사소, 판정 무관) |
| D0b m6 `freeze` | 모래상자에서 새 스크립트는 `[거부] …` exit 1, ERR 표지 없음이다. 반영 전은 `[중단] …:560: return 1`이 함께 찍혔다 |

## 모래상자 시연(`conds`·`pre`)

**`d0a_launch.sh conds`**
- `0886104`: exit 3. 조건 2(선행 기록)·4(G1 없음)·6(앵커 없음)이 미충족이고 나머지는 충족이다. 조건 8의 출력 문구는 위와 같다.

**`d0b_launch.sh --iso … conds`**
- `869cb0f`: exit 3. S-2·measured가 미충족이다. S-7은 B26-1 표본 2개가 plan에 없어 미충족인데, B26-1 미병합 판이므로 의도한 동작이다.
- S-1은 [D-11] 기록과 MOD1 토큰을 gate에서 찾는다.
- 진행 중 spec card 목록에 `20260923-probe-promote-consistency`와 `20260930-b34-grammar-explicit`가 나온다. 정보로만 출력하는 줄이다.

**`pre`(clone `master` = `869cb0f`)**
- D0b·D0a 모두 착수 조건 표를 낸 뒤 "[중단] 착수 조건 미충족(exit 3)"로 멈췄다. 저장소 변경은 0이다.
- D0a 조건 8은 G1·FU 판에서도 (e1) 0·(e4) 0이었다.

## 아직 반영되지 않은 D0a minor(원래 검토에서 이월)
- **m2**: `d0a_briefs.md` 머리의 기준 `36e170e`와 C-3 "V3 범위 정책은 미병합"이 낡았다. card 35는 `a17b8bd`에 병합됐고 판정 기록은 `dafe5cf`다.
  - 0.5-2와 225행 "`install_proto.py`는 설치가 멈춘다"도 이제 사실이 아니다. 13:24판이 `7243f28` 위 모래상자에 "installed 4"로 설치됐다.
- **m3**: `d0a_launch.sh` `PREDS`에 card 35(`20260930-v3-changed-stmt-scope`)가 없다. 지금은 병합됐으므로 넣어도 충족이다.
- **m4·m5**: 브리프에 `check` 단계 구성 대조 한 줄과 V4 (3)('if·try 밖 assert') 강조가 없다.
- 넷 모두 착수를 막지 않는다.
