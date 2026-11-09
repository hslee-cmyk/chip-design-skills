# Phase 3 초안 v3 2차 독립 검토 (design v3 · G1 · T0 · D0a)

검토자: 2차 독립 reviewer(초안 작성자·1차 검토자 아님). 기준 HEAD = gate `master` `7535799`(B28 병합 `2b41e79`, 판정 기록 `8790b24`). 저장소 읽기 전용, 스크래치 `C:/g43`(끝나고 삭제).
`$PY` = `C:/Python314/python.exe -B`, `R` = chip-design-skills, `A` = `skills/analog-gmid-design/assets`.

측정 방법: `p3v3_g1_measure.py`의 참조 규칙 부분(합성 저장소·base 도구 실행 포함)을 `C:/g43/ref.py`로 복사해(SCR·OUT만 `C:/g43`로) 그대로 import하고, 새 반례 합성 저장소마다 **HEAD(B28 병합본) 게이트 도구 3개를 실제로 실행**(base 열), v3 규칙은 참조 구현 모의(v3 열)로 쟀다. 모든 반례 원문은 부록 B(재현용 -- 스크래치는 지웠다).

요약: **blocking 2 · should-fix 8 · minor 7**. 1차 검토의 blocking 6·should-fix 13은 **대부분 실제로 고쳐졌다**(§1). 그러나 v3 규칙(M-0~M-4·골격)에 **새 약화 반례 2부류**가 있다 -- (1) V3/V7이 옮긴 def를 **qualname 키로만** 빼서, 같은 qualname의 해시 다른 def(목적 파일 조건부 재정의, property getter/setter)가 V3·V7에서 빠진다(같은 경로에서는 지금 V3가 잡는다) (2) `binding_origin`의 `unbound`·`ext`·`star` 판정이 경로·디렉터리·순서를 무시해 M-4가 '출처 같음'으로 잘못 인정한다. 수정안 4개를 참조 구현에 넣어 재측정하면 새 반례 전부 거부, 실제 엔진 통째 이동 거짓 거부 **0/402 유지**(§2 표 끝). 또 DoD의 `MP_ARGS`가 셸에서 깨져 E2·E4·E6가 문자 그대로는 exit 2다.

---

## 1. 1차 검토 발견 -- 실제로 고쳐졌는가 (반례 재실행)

| # | 판정 | 증거 |
|---|---|---|
| B1 덮어쓰기 | **고쳐짐** | `R1:overwrite` base(HEAD 도구) V3/V6/V7 = 1/1/0, v3 = 1/1/0, `rejected` M-0. `overwrite-import` 1/1/1 = 1/1/1 M-0, `swap` 두 def 모두 M-0 |
| B2 재바인딩·`__file__` | **고쳐짐(단 §2 S1의 구멍)** | `R1:rebind` M-4 거부, `file-dir-change-noshim` M-4 거부, 1/1/1 유지 |
| B3 클래스 | **고쳐짐(단 §2 B1·S6의 구멍)** | `class-header-changed`·`class-field-changed` base = v3 = 1/1/1(C 골격 불인정, `C.m` 대상 유지), `class-exact` 1/1/1 → 0/0/0 |
| B4 `plan` Phase 중·후 | **대체로 고쳐짐 -- 계약 8(b) 문언 결함**(§2 S7) | D0a 계약 2 A-0·`absent_split`·8(c), design E4 `rule` A-0 기준이 서로 맞다 |
| B5 E2 `targets` | **고쳐짐** | HEAD 출력 키 `tool, verdict, targets, mutants, killed, survivors`(ERROR `baseline_failed`) -- `mutate_changed.py:398·407`. E2가 G1이 더하는 `defs`·`moved`를 읽는다 |
| B6 CLI 불일치 | **CLI는 일치, 그러나 `MP_ARGS` 전개가 깨진다**(§2 B2) | design §6.3 표 = D0a 계약 1 |
| S1 단계표 | 고쳐짐 | G1 계약 12 표의 base exit 20개 중 재실행한 8개 전부 일치(HEAD 도구) |
| S2·S3·S4·S5·S6·S7·S8·S10·S12·S13 | 고쳐짐 | S5 `role_paths.py:226 read_section_table` 있음, S13 `git grep _SIZING_RECIPE` → `test_ts6_dead_probes.py` 60·221·222·261·262뿐, m7 문자열 import 10(재측정 일치) |
| S9 판정 도구 소유 | **해소**(§4, 잔여 minor 2) | D-16·D0a 계약 1(게이트는 `--root`에서 import) |
| S11 D군 | 고쳐짐, 단 줄 수 오기(m1) | `p3v3_facts.json` `S11_attr_overrides` = **14줄**, design §7.2 본문 "대입 12줄"(나열은 14줄) |
| m1 `lru_cache` | 고쳐짐 | `topology_library.py:248` 1곳 |
| m2 게이트 밖 호출 | 고쳐짐 | 스크립트 3개(`mut_def.py:67`, `probe_t2_vs_1st_survivor.py:16`, `v3_baseline_probe.py:17`) |
| m3~m8 | 고쳐짐 | 문언 확인 |

---

## 2. 발견 표 (심각도 순)

### Blocking

| # | 대상 | 발견 | 증거 | 고칠 것 |
|---|---|---|---|---|
| B1 | G1 계약 3·4·6(V3·V7 제외 키), design §3 MOVED | **옮긴 def를 `<경로>::<qualname>` 키로만 빼서, 같은 키의 해시 다른 def가 V3·V7에서 빠진다(약화).** (a) 목적 파일에 `if FLAG: def f(x): return -x`(조건부 재정의)를 옮긴 f 뒤에 두고 원본 자리에 재수출이 없으면(호출자를 갱신한 경우) M-0(base만 봄)·M-2(원본 자리 unbound)·M-3(최상위 단위만 셈) 모두 통과 → `defs`에 `b.py::f` → `iter_defs`가 내는 **두 `f` 모두** 제외. (b) 옮긴 클래스의 `@property def x`/`@x.setter def x`에서 getter 본문만 바꾸면 골격 동일, setter 해시가 base `P.x`(dict 마지막 값)와 같아 `P.x` 키가 `defs`에 들어가 **바뀐 getter도** 제외. 같은 경로에서는 지금 V3가 둘 다 잡는다. D0a `check`는 (a)는 새 `If` 문장 단위로 `changed`가 잡지만 (b)는 단위(골격)가 같아 **못 잡는다**. | `N1-dest-conditional-redef-noshim`: base 1/1/1 → v3 **0/0/0**, `excluded_but_hash_differs = [b.py::f]`. 같은 경로 대조 `N1c`: base V3 **1**. `adv5` property: v3 V3 **0**, 같은 경로 `changed_defs` → `['P.x']`. `N1b`(재수출 있음)는 M-2 거부 -- 재수출 여부로 결과가 갈린다 | (1) **M-0'**: u가 바인딩하는 이름 n마다 `H.binding_origin(p_h, n)` = `("def", p_h, n)`(목적 파일에서도 유일 -- `multi` 거부). (2) `iter_defs` 기준으로 p_b 또는 p_h에 qualname이 둘 이상인 def는 `defs`에 넣지 않는다(M-1 '모호'를 def 단위에도). (3) V3·V7 제외 대조를 (경로, qualname, `def_hash`)로. 계약 7·12에 `dest-conditional-redef`·`property-getter-changed` 거부 단계 추가. 수정안 측정: (1)만으로 N1·N2 거부, 실제 엔진 거짓 거부 0(아래 '수정안 재측정') |
| B2 | design §6.3 `MP_ARGS`, §10 E2·E4·E6 | **DoD 명령이 문자 그대로 실행되지 않는다.** `MP_ARGS="… --aliases '{\"optimizer\": \"theta_search.py\"}'"`를 `$MP_ARGS`로 전개하면 따옴표는 다시 해석되지 않고 공백에서 쪼개져 `--aliases`의 값이 `'{"optimizer":`, 여분 인자 `"theta_search.py"}'` → D0a 계약 1대로 exit 2(JSON 파손). E2 ②·E4·E6 모두 해당 -- 1차 B6과 같은 부류(auditor가 DoD를 못 돌림). | `MP_ARGS="--split a.py b.py --aliases '{\"optimizer\": \"theta_search.py\"}'"; printf '[%s]\n' $MP_ARGS` → `['{"optimizer":]`, `["theta_search.py"}']` | bash 배열: `MP_ARGS=(--plan … --split … --keep audit_current_forced.py --aliases '{"optimizer": "theta_search.py"}')`, 명령은 `"${MP_ARGS[@]}"`. 또는 `--aliases`를 `KEY=VALUE` 모양으로 바꾼다(D0a 계약 1 정본에서) |

### Should-fix

| # | 대상 | 발견 | 증거 | 고칠 것 |
|---|---|---|---|---|
| S1 | G1 계약 1(`binding_origin`) → M-4 | **출처 튜플이 위치를 잃어 M-4가 다른 것을 '같음'으로 본다(약화 3건).** (a) `("unbound", name)`에 경로가 없다 -- 원본 파일의 다른 함수가 `global X`로 쓰는 X를 읽는 g를 옮기면 base·head 모두 `unbound`라 인정, g는 이제 목적 모듈의 X(아무도 안 씀)를 읽는다. (b) `("ext", M, n)`에 디렉터리가 없다 -- `A/a.py`의 `from wsutil import h`와 `workspaces/run_harness.py`의 같은 줄은 `sys.path[0]`이 달라 다른 모듈일 수 있는데 같다고 본다(`__file__`만 디렉터리를 본다). (c) `from … import *`는 "바인딩이 없을 때만" `star` -- 명시 바인딩 **뒤에** 온 star import가 이름을 덮어도 `("def", p, n)`. | `N4-unbound-global-reader-moved`: base 1/1/1 → v3 **0/0/0**. `N13-ext-dir-change`: 1/1/1 → **0/0/0**. `N3b`(builtin을 읽지 않는 g + 끝의 `from c import *`): v3 V3 **0**, 옮긴 단위 `{g, helper}`(`N3`은 `Exception`이 우연히 `star`가 되어 거부된 것) | (a) 모듈 어디든 `global v`가 있으면 v의 출처 `("global-dynamic", path, v)`(항상 경로 포함). 경로를 무조건 붙이면 문장 단위의 컴프리헨션 변수(`t`)가 `unbound`로 잡혀 SR 24단위 거짓 거부 -- 실측, 그래서 `global` 선언 이름만. (b) `ext`·`ext-module`에 가져오는 파일의 디렉터리를 붙인다. (c) 모듈에 star import가 하나라도 있으면 그 모듈의 모든 이름 출처 = `star`(`__file__`·module-identity 제외). 재측정: 셋 모두 거부, 엔진 거짓 거부 0. 계약 12에 `global-reader`·`ext-dir-change`·`star-shadow` 단계 |
| S2 | G1 계약 1 바인딩 열거 | 바인딩 종류가 "def·class·대입·`for`/`with` 대상"뿐이다. 참조 구현은 `ast.walk`의 `Store`/`Del` 전부(증강 대입·walrus·`del`·`except … as`·`match` 포획 포함)로 센다. 계약 문장 그대로 구현하면 `helper += …`·`del helper`가 `multi`가 아니어서 M-0'/M-4가 뚫린다. 문언과 참조 구현이 다르다. | `p3v3_g1_measure.py` `_bound_names`(Store·Del 전부) 대 G1 계약 1 | "모듈 공간(def·class 몸체 밖)에서 이름이 `Store`/`Del` 문맥이거나 import·def·class·`type` 별칭으로 묶이는 모든 곳"으로. 문장 단위 전역 읽기도 `symtable` 모듈 표로(컴프리헨션·lambda 지역 제외) -- 지금 "문장 안 모든 `Name`(Load)"은 과대 근사라 S1 (a) 강화 시 거짓 거부를 낳는다 |
| S3 | G1 M-4, D0a `check` | **`from __future__ import annotations` 차이를 아무도 보지 않는다.** SR·SD·**TL**(24행)에 있고, 새 MOD 파일에 빠뜨리면 AST·해시·전역 출처가 다 같아 이동으로 인정되지만 주석이 문자열 → 평가값으로 바뀐다(3.14 실측: `dataclasses.fields(R)[0].type` = `'float'` 대 `<class 'float'>`). import 줄은 단위가 아니라 D0a `changed`도 못 본다. 엔진 dataclass 36개가 옮겨질 대상. 지금 저장소의 `.type`·`__annotations__`·`get_type_hints` 소비자 0이라 당장 실해는 없다. | `N5-future-annotations-dropped`: base 0/0/0, v3 0/0/0, 옮긴 단위 `b.py::Rec`. `git grep -E "__annotations__\|get_type_hints\|fields\("` → e_lib 스크립트의 `f.name`만 | M-4에 의사 이름 하나: p_b와 p_h의 `__future__` 기능 집합이 다르면 옮긴 단위 아님. D0a `order` 또는 새 발견 `future`: MOD 파일의 `__future__` 집합 ⊇ 원본들의 집합. design §7·부록 사실에 TL 24행 추가(지금 "SR 35·SD 32"만) |
| S4 | D0a 계약 4 `move-set` | **다른 MOD 파일로의 끼워 넣은 이동을 못 잡는다.** `move-set`은 목적지가 `--card` 파일인 옮긴 단위만 배정과 대조한다. 같은 card에서 배정 밖 단위를 **다른** MOD 파일로 옮기면 `changed`(옮긴 단위라 아님)·`lost`(원본이라 아님)·`order`(`--card` 파일만) 어디에도 안 걸린다 -- '모듈 하나당 이동 전용 커밋'(533행) 위반이 통과. | D0a 계약 4 `move-set`·`order` 문언 | `move-set` = (이 base→head에서 옮긴 **모든** 단위) = (배정 집합)이고 목적지가 전부 `--card`. `ALL`은 지금대로 |
| S5 | D0a `check`, design §5.4 | **같은 경로 import 교체(§5.4 관찰)를 Phase 3 안에서도 막지 않는다.** M card는 "import 줄만 차이"를 허용하고 D0a는 import를 단위로 보지 않아, 옮기지 않은 단위(`stick_diagram` 잔류분, shim, `A/` 도구 파일)가 읽는 이름을 import 줄로 다른 정의에 묶어도 발견 0. 1차 검토가 제안한 `rebind` 발견이 '옮긴 단위의 `move-rejected`'로만 일반화됐다. | `same-path-rebind(observation)` base 0/0/0(v3 기록), D0a 계약 4 발견 목록 | `check`에 `rebind`: head의 **모든** 단위 u(옮긴 것·제자리)에서 `global_names(u)`의 이름마다 head 출처 = base 출처(옮긴 단위 사상 적용). `SourceIndex`가 이미 있어 비용은 질의뿐. Phase 3 안의 §5.4 사각을 닫는다 |
| S6 | D0a `changed`, design §8 M card oracle | **옮긴 클래스 안 메서드 본문 변경을 `check`가 못 본다.** 골격 해시는 메서드 몸체를 빼므로 클래스 단위는 '옮김', `changed`는 단위 수준이라 발견 0. V3는 그 메서드를 대상으로 잡지만(아래) 인벤토리 test가 변이를 죽이면 V3 PASS -- card 판정에서 `defs = []`는 DoD E2에만 있다. 결국 Phase 끝(E2)에서야 드러난다. | `N7-method-body-changed-in-moved-class`: v3 V3 1(대상 `C.m`), 옮긴 단위에 `C` 포함 | M card 판정(§8 M행 oracle·MOVE-AST 판정 도구 열)에 "V3 JSON `defs` = `[]`"을 **card마다** 명시하거나, `changed`를 def 단위(옮긴 클래스의 메서드 해시)까지 |
| S7 | D0a 계약 8(b) | "각 커밋의 `plan` `assignment`가 이동 전 커밋의 것과 같다" -- `assignment` 키는 `"<A 기준 파일>::<키>"`라 옮긴 뒤 파일 부분이 바뀌고(`sizing_recipe.py::f` → `gmid_lut.py::f`) `rule`도 A-1 → A-0로 바뀐다. 문자 그대로는 항상 거짓, test-author가 기대값을 유일하게 못 정한다. 키 없는 문장 단위(바인딩 없는 `Expr`)의 키도 미정. | D0a 계약 2 출력 키 정의 대 8(b) | "(단위 키 → `mod`) 사상이 같다(파일 부분·`rule` 제외)"로. 문장 단위 키 = 바인딩 이름(없으면 `<stmt:해시12>`) |
| S8 | G1 spec 의도·작성 전 실측 1, design §5.1·§5.3·§9.1·부록 A V3·H | **B28 병합으로 사실 문장이 낡았다**(spec 스스로 "B28 뒤 다시 잰다"). HEAD 실측: `_strip_doc` 74, `def_hash` 84, `changed_defs` **88~100**(초안 50~62), diff 314(276), `copytree` **없음**(→ `make_clone`, 53행), cat-file 359(321), `base_src` 361(323), `changed_defs` 호출 364(326), `_rmtree_force` 406, 출력 398·402·407~408. "B28은 병합 전(`dee338d`)", "지금 마지막 30, B28이 31" → 병합됨(`2b41e79`), `attacks` 마지막 `31-v3-git-history` → 새 번호 32 확정. `lib/rt.py`에 `vcase` 선택 관찰(`tool_tmpdir`·`root_state`, 599~621행)이 생겼고 `add_parser("vcase")` 1351행. 출력 키는 불변이라 **E2 기준은 영향 없음**. 엔진·계획서·design 00/05/10/20의 인용 줄은 cd64170 이후 불변(`git diff --stat cd64170 HEAD`는 tools·P9 spec·design 20 E4뿐) | `grep -n 'diff", "--name-only\|copytree\|cat-file\|changed_defs\|rmtree\|json.dumps\|def def_hash' tools/gates/mutate_changed.py` | 줄 번호·상태 문장 갱신. 작성 전 실측 1의 grep 패턴에서 `copytree`를 `make_clone`으로. P9·P10(엔진 변경 card) 병합 뒤 엔진 줄(`sizing_recipe.py:2391·2530·7697`, `stick_diagram.py:1050·8973`) 재측정 조건을 design 머리에 |

### Minor

| # | 대상 | 발견 | 고칠 것 |
|---|---|---|---|
| m1 | design §7.2 D군 | "8개(대입 12줄)"인데 나열과 `p3v3_facts.json` `S11_attr_overrides`는 14줄(probe 12 + workspaces 2) | "14줄" |
| m2 | D0a 이동 판정 순서 | 옮긴 **문장** 단위의 상대 순서가 바뀌어도(`X.update(a=1)`/`X.update(a=2)` 교환) G1·`check` 모두 통과(`N6`: v3 0/0/0, 옮긴 단위 3). 지금 엔진 최상위 문장은 전부 이름 하나 대입(SR 30·SD 8·DR 1, 변이 문장 0)이라 순서 변경은 V1 import 오류로만 드러난다 | `check` 전제로 "옮긴 문장 단위의 원본 상대 순서 보존"(또는 "최상위 문장은 이름 대입뿐")을 발견으로 |
| m3 | D0a `lost`·단위 정의 | `if __name__ == "__main__"` 블록은 단위가 아니어서 split 파일을 shim으로 바꿀 때 main 블록을 지워도 `lost` 0. 엔진 4파일에는 main 블록 0(`audit_current_forced.py:160`은 `--keep`) | `shim` 발견에 "main 블록 제거" 포함 또는 전제로 명시 |
| m4 | design §10 E6 | `--base <Phase 3 첫 card base>` -- 첫 card가 G1이면 레지스트리 재생성(D0b) 전이라 `check`의 `assigned`가 다르다 | "M1 판정 기록 `base_commit`(D0b 병합 뒤)" |
| m5 | design §10 E2 ③ | V3의 `moved`와 `check`의 `moved_defs`는 **같은 `<iso>/tools/gates` 코드의 같은 함수**(D0a가 `--root`에서 import)라 대조가 동어반복이다 -- 증거로 세지 말 것 | ③을 '일관성 점검'으로 표기 |
| m6 | D0a·design 사본 출처 | 사본 출처가 D0a spec은 "D0a **병합 커밋**", design §8·§10은 "D0a `code_commit`". 또 D0a를 고치는 후속 card가 생기면 어느 사본인지 규칙이 없다 | "`move_plan.py`를 마지막으로 바꾼 판정 기록의 `code_commit`" 하나로 |
| m7 | G1 계약 12 관찰 방법 | "거부 단계는 `move_rejected` 규칙 이름까지 대조" -- 지금 `vcase`의 관찰은 `v4_first`·`tool_tmpdir`·`root_state`뿐(rt.py 612~621행). 규칙 이름을 어떻게 기대와 비교하는지(`message_contains`? 새 `observe` 모드?)가 없다 | 관찰 방식 명시(예: `observe: "moved"` → `{moved, move_rejected 규칙}`), rt.py 쓰기 = test-author(B28 선례) |

---

## 3. 새 적대적 구성 (요청 (2)) -- V3/V6/V7(v3 규칙) + D0a `check`가 잡는가

"base" = HEAD 게이트 도구 실제 실행(V3/V6/V7 exit), "v3" = 참조 구현 모의. D0a 열은 D0a 계약 4 문언을 합성 입력에 손으로 적용한 판단.

| # | 구성 | base | v3 | v3 규칙 | D0a `check` | 결론 |
|---|---|---|---|---|---|---|
| N1 | 이동 + 목적 파일 `if FLAG: def f` 조건부 재정의(원본 재수출 없음) | 1/1/1 | **0/0/0** | 인정(키 충돌로 새 def 제외) | `changed`(새 `If` 문장) | **G1 약화 → B1** |
| N1b | 같은데 원본 재수출 있음 | 1/1/1 | 1/1/1 | M-2 거부(`multi`) | -- | 잡음 |
| N1c | 같은 경로 대조(지금 게이트) | V3 1 | V3 1 | -- | -- | 지금은 잡는다 |
| P | 옮긴 클래스의 property getter 본문 변경(setter 같음) | -- | V3 **0** | 골격 같음, `P.x` 키 제외 | **못 잡음** | **G1·D0a 약화 → B1** |
| N2 | 이동 + 목적 파일 `f = (lambda g: …)(f)`(def 없는 재바인딩) | 1/1/1 | 0/0/0 | 인정 | `changed`(새 문장) | 같은 경로와 같은 사각(지금 게이트도 문장을 안 본다). M-0'로 G1 자체에서 막힘 |
| N3/N3b | 함께 옮긴 helper를 목적 파일 끝 `from c import *`가 가림 | 1/1/1 | N3 1/1/1(우연), **N3b V3 0** | `star` 무시 | import는 단위 아님 → 못 잡음 | **S1 (c)** |
| N4 | 다른 함수가 `global X`로 쓰는 X를 읽는 g만 이동 | 1/1/1 | **0/0/0** | `unbound` = `unbound` | 못 잡음(캐시 아님) | **S1 (a)**(엔진 `global` 0) |
| N5 | `__future__ annotations` 없는 새 파일로 dataclass 이동 | 0/0/0 | 0/0/0 | 인정 | 못 잡음 | **S3** |
| N6 | 옮긴 최상위 문장 순서 교환 | 0/1/0 | 0/0/0 | 인정 | 못 잡음 | m2(엔진 노출 0) |
| N7 | 옮긴 클래스 안 메서드 본문 변경 | 1/1/1 | 1/1/1 | `C` 골격 인정, `C.m` 대상 | `changed` 0 | V3가 잡음, card 판정 기준 필요 → S6 |
| N8a | 이동 + 데코레이터 추가 | 1/1/1 | 1/1/1 | 해시 다름 | `changed` | 잡음 |
| N8b | 데코레이터 이름을 목적 파일이 다른 정의로 import | 1/1/1 | 1/1/1 | M-4 | `move-rejected` | 잡음 |
| N9a | 기본값이 읽는 상수를 목적 파일이 다른 값으로 | 1/1/1 | 1/1/1 | M-4 | `move-rejected` | 잡음 |
| N9b | 이동 + 기본값 식 변경 | 1/1/1 | 1/1/1 | 해시 다름 | `changed` | 잡음 |
| N10 | `from c import helper as h` → 목적 `from d import helper as h` | 1/1/1 | 1/1/1 | M-4 | `move-rejected` | 잡음 |
| N11 | 메서드를 클래스 밖 최상위로 | 1/1/1 | 1/1/1 | 원본 없음(메서드는 단위 아님) | `changed`·`lost` | 잡음 |
| N12 | 목적 파일 `try: from fastlib import helper except ImportError: pass` | 1/1/1 | 1/1/1 | M-2/M-4(`multi`) | `move-rejected` | 잡음 |
| N13 | 비소스 같은-디렉터리 모듈 import를 쓰는 def를 다른 디렉터리 소스로 | 1/1/1 | **0/0/0** | `ext` = `ext` | 못 잡음 | **S1 (b)** |
| -- | 다른 모듈에서 `b.f = other`(속성 덮어쓰기) | -- | -- | 단위 밖 | -- | 같은 경로와 같은 사각, D군(UD-7) |
| -- | 상대 import(`from .c import h`) 패키지 간 이동 | -- | -- | `("ext", ".c", h)`가 패키지 무관하게 같음 | -- | 소스가 평면 `A/*.py`라 현재 노출 0, S1 (b)의 디렉터리 부착으로 함께 닫힘 |
| -- | `__all__` | -- | -- | star 경로에서만 의미 | -- | S1 (c)로 닫힘 |
| -- | dataclass 필드 기본값 변경 + 이동 | 1/1/1 (`class-field-changed`) | 1/1/1 | 골격 다름 | `changed` | 잡음 |

**수정안 재측정**(참조 구현에 B1 (1) M-0' + S1 (a)(b)(c)만 넣음, `C:/g43/adv4.py`): N1·N2 → M-0' 위반, N4·N13 → M-4 거부, N3b → 거부. `move-exact`·`class-exact` 인정 유지. 실제 엔진 4파일 통째 이동(같은 디렉터리) **218/218·169/169·8/8·7/7, 거부 0, M-0' 위반 0**. (경로를 무조건 붙인 `unbound`는 SR 24단위 거짓 거부 -- 원인은 문장 단위 전역 읽기가 컴프리헨션 변수를 포함하는 것, S2.)

---

## 4. D0a `move_plan.py` 소유(1차 S9)와 작성자≠검증자 (요청 (4))

**해소됨.** 근거: (i) design D-16·§8 M행 -- M card는 `git diff --name-only <base> <head> -- tools` 빈 출력이 판정 조건이라 code-author가 판정 도구를 같은 card에서 바꾸면 FAIL, (ii) 판정은 D0a 판 사본 실행, (iii) D0a 계약 1이 게이트 모듈을 `--root`에서 import하게 해 사본 실행이 가능, (iv) `check`의 배정은 `--base` 커밋의 계획서·레지스트리에서 읽어 head 편집이 판정에 들지 않음, (v) D0b 계약 test(`test_p3_registry_dest.py`)는 head의 `tools/migrate`를 부르지만 (i) 때문에 = D0a 판.
잔여: m5(E2 ③ 동어반복), m6(사본 출처 커밋 문언 두 가지·후속 수정 card 규칙 없음). 참고: 계획 601행 `tools/migrate/**` 조건 '없음'은 그대로이므로 (i)은 hook이 아니라 auditor 판정이다 -- 설계상 충분.

---

## 5. 사용자 결정 목록 최소성 (요청 (5))

지금 목록 UD-0·UD-1·UD-5·UD-6·UD-7(5개). 원칙('결정은 원칙으로 기본안부터 -- 묻는 건 착수 조건만')으로 줄일 수 있다:
* **UD-7 → UD-0에 흡수**(D-17로): 기본안(F1에서 덮어쓰기 대상을 호출자 모듈로 옮김)은 probe 기능을 **보존**하므로 삭제·범위 축소가 아니다. 대안('동작 안 하는 probe로 표시')을 원할 때만 사용자가 말하면 된다.
* **UD-6은 착수 전 결정이 아니다**: V5 승인은 T0 test 커밋 뒤 diff 해시로만 받을 수 있다 -- T1·F1의 V5처럼 '뒤에 올 승인' 목록으로 옮긴다(지금 표는 T0만 UD로 올리고 T1·F1은 뒤로 미뤄 기준이 다르다).
* 남는 착수 결정: **UD-0**(design, D-17 포함), **UD-1**(U-03 -- 계획이 사용자 몫으로 지정), **UD-5**(G1 게이트 변경 + (가)/(나) 비용 선택, 기본안 (가)).
* UD-5 권고 근거 문장 "옮긴 단위는 바이트·전역 출처가 같아 동작이 같다(M-4)"·"반례 거부 13/13"은 §3 반례(N1·P·N3b·N4·N13·N5)로 지금은 사실이 아니다 -- B1·S1·S3 반영 뒤 거부 단계 수·근거를 다시 적어 승인받을 것. (나)도 N1·P는 못 막으므로(선언된 from→to 안에서 일어남) 비교표 결론은 유지된다.

---

## 부록 A. 재측정 명령과 결과 (HEAD `7535799`)

| 항목 | 명령 | 결과 |
|---|---|---|
| HEAD·B28 | `git log --oneline -8` | `8790b24` B28 판정 기록, `2b41e79` 병합, `dee338d` code |
| V3 줄·키 | `grep -n '…' tools/gates/mutate_changed.py`(S8) | 74·84·88·314·359·361·364·398·402·406·407; 출력 키 불변 |
| V6·V7 줄 | `grep -n "^def compare\|findings += compare\|module_text\|Assign" source_lint.py`; `grep -n "base_defs\|new_defs = " reachability.py` | 102·126·129·168·212·268 / 224·227·230·231 -- 초안과 같음 |
| redteam | `ls tools/gates/redteam/attacks \| tail`; `grep -n 'add_parser("vcase"\|tool_tmpdir' lib/rt.py` | 마지막 `31-v3-git-history`; vcase 1351, 관찰 599~621 |
| 엔진 변경 | `git diff --stat cd64170 HEAD -- A/*.py workspaces/run_harness.py` | 없음 |
| star·global·future·main | `grep -n "import \*\|^\s*global \|__future__\|^if __name__" A/*.py workspaces/run_harness.py` | star 0, global 0, future SR 35·SD 32·**TL 24**, main 블록은 `audit_current_forced`·`sky130_lut_sweep`·`topology_to_markdown`·`run_harness` |
| 주석·모듈 내성 소비자 | `git grep -n -E "__annotations__\|get_type_hints\|dataclasses\.fields\|\bfields\(\|__module__\|pickle\|__qualname__"` | e_lib 스크립트 `f.name`, probe `f.name` -- `.type`·`__module__` 소비 0 |
| 엔진 모듈 alias·덮어쓰기 | `git grep -h -o -E "import (sizing_recipe\|…)( as \w+)?"`; `git grep -n "setattr\|monkeypatch"` | alias는 `sr`·`sd`·원래 이름뿐, `setattr`·`monkeypatch.setattr` 엔진 대상 0 → D군 목록 완전(14줄) |
| 최상위 문장 종류 | AST 스캔 | SR 이름 대입 30·SD 8·DR 1, 변이 문장(Expr·AugAssign·속성/첨자 대입) 0 |
| qualname 중복 | `iter_defs` 전수(A/*.py + run_harness) | 0 -- B1(P)의 현재 노출 0 |
| 1차 반례 재실행 | `$PY C:/g43/adv.py`(HEAD 도구) | §1 표 |
| 새 반례 | 같은 실행 + `adv2.py`(N3b)·`adv5.py`(property) | §3 표 |
| 수정안 | `$PY C:/g43/adv4.py` | §3 끝 |
| 셸 전개 | `printf '[%s]\n' $MP_ARGS` | B2 |

## 부록 B. 새 반례 원문(재현용, 합성 저장소 경로는 `A/` = `skills/analog-gmid-design/assets/`, 공통 `workspaces/run_harness.py` = `from a import run` + `run2`)

* F1 = `def f(x):\n    try:\n        return x / 3.7\n    except Exception:\n        return None`
* **N1**: base `a.py` = `run` + F1. head `a.py` = `run`만, `b.py` = F1 + `FLAG = True\nif FLAG:\n    def f(x):\n        return -x`.
* **P**: base `a.py` = `run` + `class P:` `@property def x(self): return self._x * 3.7` / `@x.setter def x(self, v): self._x = v`. head `a.py` = `from b import P` + `run`, `b.py` = 같은 클래스에서 3.7 → 4.7.
* **N2**: N1의 head `b.py` = F1 + `f = (lambda g: (lambda x: -g(x)))(f)`.
* **N3b**: base `a.py` = `run`·`helper()→2`·`g(x): return helper() * x`, `c.py` = `helper()→5`. head `a.py` = `from b import g, helper` + `run`, `b.py` = helper·g + 끝에 `from c import *`.
* **N4**: base `a.py` = `run`·`setx(v): global X; X = v`·`g(y): try: return X / 3.7 except Exception: return y`. head `a.py` = `from b import g` + `run`·`setx`, `b.py` = g.
* **N5**: base `a.py` = `from __future__ import annotations` + `import dataclasses` + `run` + `@dataclasses.dataclass class Rec: a: float = 2.5`. head `a.py` = future + `from b import Rec` + `run`, `b.py` = `import dataclasses` + Rec(future 없음).
* **N6**: base `a.py` = `run` + `X = {}` / `X.update(a=1)` / `X.update(a=2)`. head `a.py` = `from b import X` + `run`, `b.py` = `X = {}` / `X.update(a=2)` / `X.update(a=1)`.
* **N7**: `class-exact` base, head `b.py`의 `C.m`에서 3.7 → 3.8.
* **N13**: base `a.py` = `from wsutil import h` + `run` + `g(x): try: return h() / 3.7 …`, `workspaces/wsutil.py` = `h()→1`. head `a.py` = `run`만, `run_harness.py` 끝에 `from wsutil import h` + g.
* N8a·N8b·N9a·N9b·N10·N11·N12는 §3 표 문구대로(모두 거부 확인).
