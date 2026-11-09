# 독립 재검토 r2 -- F1 `20261002-p3-callers-update` r2 · F2 r2 · 승인 초안 `20261002-p3-f1-workspaces-write-path` r2

검토 2026-10-02. 기준 gate `master` `4a286f0`(= 로컬 HEAD). 검토자는 초안·키트·승인 초안을 쓰지 않았다.
실제 저장소 읽기 전용(`git -C`, `set -e`) -- 시작·끝 HEAD `4a286f0`, `status --porcelain` 37줄·md5 `dcc7b56b…`, reflog 첫 줄 같음.
스크래치 `C:/g258`만(작업 트리에서 `git -c core.autocrlf=false clone --no-local`, origin 제거, 빈 hooksPath, TMP/TEMP = `C:/g258/tmp`), 끝에 `C:/g258` 삭제.

## 0. 판정

**B 0 · S 1 · minor 5.** 승인 초안은 커밋 가능, F2 r2 그대로 진행 가능. F1 r2는 S1 문장 하나(계약 3 (나) 별칭 해석) 더한 뒤 진행.

## 1. review_p3_f12_r1 항목 해소

| 항목 | r2 | 판단 |
|---|---|---|
| B1 넓은 행 부수 효과 | 재질문 → '좁힘' 답, 두 행, 범위 설명에 22파일·막히는 주체 명기 | 해소(2절) |
| B2 도우미 반드시 FAIL | 계약 3 (바) 목록 단위 → (i)~(iii) | 해소(4절) |
| S1 트레일러 | `Role: doc`(`--trailer`) 지시 | 해소 |
| S2 모듈 객체 탈출 | (바) fail-closed + 거부 입력 A2·A3 | 해소(단 이번 S1 -- 같은 계열의 다른 구멍) |
| m1 F2 깨진 줄 | 고침, `git grep -E "p3_shim_delete\|p3sd_"` `4a286f0` 0건 재확인 | 해소 |
| m2 D-11 순서 문장 | 'plan_tables_hash 기준으로만' 한정 + diff 해시 순서 의존 명기 | 해소 |
| m3 '16' 표현 | '대상 16, 덮는 22' | 해소 |
| m4 같은 값 대입 여럿 | 계약 2 (iii) 사슬 대입 하나로 고정, 호출형 같은 Name 인자 | 해소 |
| m5 D-17 기대 집합 전제 | 착수 조건 (3)에 MOD 엔진 모듈 import·속성 접근 0 확인 + 멈추고 묻기 | 해소 |
| 5절 권고(approval 둘째 줄) | 머리 둘째 `approval:` + 판정 기록 `approvals` | 반영 |

## 2. 좁힌 두 행 -- 독립 재측정(gate `role_paths` 그대로, 개정 판 70행)

* 해시: 개정 전 `7167e028…` → **`16b899d1c745ddd0d305b2a977eecc74b0c830d89507d7eb3476b7323a08aec1`**(재계산 같음), 넓은 행 `31828c5e…` 재현. `read_plan_tables` 불변, `read_write_paths` 68 → 70, 앵커 602행.
  두 행 순서를 바꾸면 해시가 `1fe47e9f…`로 달라진다 -- 초안이 '이 순서'를 박아 둔 것이 맞다.
* `workspaces` 추적 `.py` 39개 중 **바뀌는 것 22**(개정 전 `overlaps_any` 거짓·5주체 거부 → 개정 뒤 `overlaps_any` 참·code-author만 허용):
  * 대상 16 -- current-reuse 12: `diagnose_cmrr_cmfb`·`diagnose_cmrr_psrr`·`probe_group_split_wiring`·`rerun_symmetry`·`resize`·`run_harness_smoke`·`sample_metrics_session22`·`smoke_run_harness_session11`·`smoke_run_harness_session20`·`stick`·`structural_symmetry_probe`·`theta_sensitivity_session22`;
    two-stage 4: `check_box_shape`·`check_box_shape_M5M7split`·`diagnose_gain_sweep`·`diagnose_gain_sweep2` (F1 모의 대상 목록 `equiv_r2_f1.json`의 workspaces 16과 같음).
  * 대상 아닌 current-reuse 6: `build_html`·`build_report`·`probe_crossover_pairing_alternatives`·`probe_d1_verify`·`probe_group_split_reassembly`·`probe_l3_groups`.
* 그대로 17: current-reuse `spice/` 14, `verilog-rtl-workspace/desc-opt/{gen_html,launch_all}.py` 2, `workspaces/run_harness.py`(기존 행). 5주체 판정·`overlaps_any` 모두 개정 전과 같다.
* 탐침: `…/__init__.py`·`…/conftest.py` = `판정 환경` 사용자만 그대로, 미추적 `smoke_run_harness_session18_save.py`·두 폴더의 새 `.py` = 개정 뒤 code-author 전용, 대소문자 다른 폴더 이름도 casefold로 같이 잠김.
* **glob 의미 차이(오케스트레이터 수치 14/2의 정체)**: `git ls-files 'workspaces/*/**/*.py'`는 기본 pathspec이라 `*`가 `/`를 넘고 `**`는 `*` 둘일 뿐 -- 리터럴 `/`가 셋 필요해 **깊이 3 이상만** 나온다(current-reuse `spice/` 14 + verilog 2 = 16).
  게이트는 조각 단위(`*` 한 조각, `**` 0개 이상 조각)라 같은 넓은 행이 38을 덮는다(`git ls-files ':(glob)workspaces/*/**/*.py'` = 38로 일치). 즉 그 16개는 우연히도 **좁힌 행이 풀어 주는 파일** 쪽이다. 저자 수치(22·17·38)가 게이트 의미로 맞다.

### 사용자에게 보인 문안과 6파일
선택지 설명 "행 glob을 F1이 고칠 gmid 작업 폴더(…)로만 한정 … 다른 workspaces 폴더는 지금처럼 사용자가 씁니다"는 **폴더 단위** 잠금을 말하고, 질문 본문이 잠금의 뜻(사용자 커밋·메인 세션·비 gmid agent 거부)을 이미 보였다.
그래서 같은 폴더의 비대상 6파일이 잠기는 것은 문안과 **어긋나지 않는다**(방향도 맞다). 실제와 다른 점은 반대 방향 하나 -- '폴더'라 했지만 하위 디렉터리 `spice/` 14는 잠기지 않는다(사용자 권한이 문안보다 넓게 남음, 해 없음).
오도 가능성은 "F1이 고칠"이라는 수식어로 '고칠 파일만'으로 읽힐 수 있다는 정도인데, 오케스트레이터가 답 뒤 `2026-10-02T09:14:47.244Z`(uuid `8e9a12fb-1940-4634-a484-4dac99aef542`) 보고에서
"두 행이 잠그는 추적 .py는 22개 … 고칠 대상이 아닌 같은 폴더 파일 6개도 함께 code-author 전용이 됩니다. 이 숫자는 질문 문안에는 없었습니다"라고 사용자에게 알렸다(사용자 이의 없음 -- 동의가 아니라 고지).
→ 질문을 다시 할 사안은 아니다. 다만 아래 m1.

## 3. 승인 초안 r2

* 사용자 원문: 내 비교 스크립트(jsonl 바이트, 사이드체인 제외)로 두 문답 모두 header당 AskUserQuestion 1건, 질문·라벨 3·설명 3·답(`toolUseResult.answers` = 라벨, tool_result 본문 같음)이 초안 인용과 바이트 같음, multiSelect false, annotations `{}`, BOM·CRLF 없음.
  tool_use id·uuid·시각 넷 모두 맞음. `> gmid 폴더로 좁힘 (Recommended)` 블록 = 둘째 답. 저자 `verify_approval_f1wp.py` r2도 다시 돌려 ALL OK(머리 파싱 `plan_tables`, 해시, 68 → 70, 새 행 원문).
* `target_kind: plan_tables`, `target` = 개정 뒤 해시, `diff_*` 없음, 커밋 지시 `Role: doc`·Change-Id 없음 -- 맞다.
* **m1** '사용자에게 보인 것' 2는 "22파일은 문안에 숫자로 나오지 않았다"에서 멈춘다. 초안 작성(17:46 KST) 뒤 위 `09:14:47Z` 메시지가 사용자에게 22·6을 알렸으므로 항목 하나로 더한다(원문 인용 -- 기록이 실제로 보인 것을 빠짐없이 적게).

## 4. 판정기 r2(`f12_equiv.py`) 재현과 새 공격

### 재현(사슬을 `mk_chain_r1.sh C:/g258/c`로 다시 만듦 -- M9 정정 `b035520`, F1 모의 `3fdf21c`, F2 모의 `e40da5b`)
* `--approved approved_v5_5_mock.txt`: **PASS 62 · LISTED 6 · FAIL 3**(selftest 3, `ast_same`·`from_same`) -- 저자 `equiv_r2_f1.json`과 summary·파일별 결과 **완전히 같음**(71파일). 목록 단위 수 4·3·6·3·1·1 = 계약 문언.
* `--approved` 없이: 도우미 5파일 `listed_changes_approved` FAIL, `test_restore_plan_functions` LISTED -- `equiv_r2_f1_noapproved.json`과 같음(대조가 실제로 거부).
* `t0sim.py`(F1 모의 base 위 T0 모의 `85d044d` → `c312809`): selftest 3파일 **PASS 3 · FAIL 0** → F1 모의의 설명되지 않는 FAIL 0 확인.
* 저자 공격 결과 파일(`out/att_r2/r2.*`): h1~h5 FAIL, A1b·A2·A10·A3 4/4 FAIL(probe는 `listed_collected`도), good probe는 `listed_collected` FAIL(fail-closed), contracts good은 LISTED -- 내용 확인.

### 내 새 공격(합성 파일, base = F1 모의 base + 파일, head = F1 모의 + 변이; 이름 셋은 모의에서 `gmid_sizing_engine`에만 있고 `gmid_lut`에는 없음 -- 실행 시 `AttributeError`)

| 공격 | 모양 | 판정기 r2 |
|---|---|---|
| T1 | base: 최상위 `import sizing_recipe as sr` + 함수 안 `import sizing_recipe as sr`. head: 최상위를 `import gmid_lut as sr`, 함수 안을 `import gmid_sizing_engine as sr` | **PASS(속음)** -- probe·contracts 둘 다 |
| T3 | 같은 모양, 함수 안 별칭이 `sr = importlib.import_module(…)` | **PASS(속음)** -- 둘 다 |
| T1 good | 두 import 모두 정의 모듈 | PASS(맞음) |
| T5 | head에만 있는 새 test 파일(탈출 자리 포함) | 판정 `absent` -- PASS·FAIL 어느 쪽에도 세지 않음 |

### S1 -- 계약 3 (나)가 별칭을 '어느 자리의 바인딩'으로 푸는지 정하지 않아, 같은 별칭 이름이 파일 안 여러 스코프에서 엔진 모듈에 묶이면 속는다
판정기는 별칭표를 파일 전체 하나(`ast.walk` 순서상 마지막 바인딩이 이김)로 만든다. T1·T3에서 함수 안 바인딩이 최상위 바인딩을 덮어, 최상위 자리 `sr.x`를 정의 모듈로 풀고 (나)(다) 참,
import 문은 (가) 표지로 지워지고 모듈 식은 `<M>`이라 (가) 참, 탈출 자리도 없다 → (바) 미적용. 계약 (나) 문언("모듈 식 속성 … 정의 목록")도 스코프를 말하지 않아 auditor 독립 구현이 같은 구멍을 가질 수 있다.
현재 노출: F1 모의 base 대상 71파일 중 함수·블록 안 엔진 import 별칭이 있는 파일 **0**(내 스캔) -- base에 그런 바인딩이 없으면 head가 새로 넣는 순간 (가) 문장 차이로 FAIL이므로 지금은 무해. F1 base(M10·T1·T0 뒤)에서 생길 수 있다.
고칠 문언(원칙 기본안, 질문 아님) -- 계약 3 (나) 또는 (바)에 한 문장: "**같은 이름이 파일 안에서 엔진 모듈(import 문·import 호출 대입)에 두 번 이상 묶이거나 최상위가 아닌 스코프에서 묶이면** 그 이름을 쓰는 단위는 목록 단위로 둔다(그렇지 않으면 별칭은 사용 자리의 Python 스코프 규칙으로 푼다) -- F1 base에서 목록화, 목록 밖 head 신규는 FAIL".
'거부해야 할 입력'에 T1 한 줄을 더하고, 착수 조건 (3)과 같은 자리에서 F1 base의 그런 파일 수를 잰다(모의 0).

### minor
* m2 T5 -- 계약 7 둘째 문장('바뀐 줄은 import 문…뿐')이 새 파일을 사실상 거부하지만 계약 3에 '대상 계산 밖·base나 head 한쪽에만 있는 파일 = FAIL'이 없고 시제품도 `absent`를 어디에도 세지 않는다. 계약 3 첫 줄에 "base·head 파일 집합이 같다(추가·삭제 0 -- '작성 전 실측' 2 '새 파일 없음')"를 더한다.
* m3 (바) (iii) '수집되는 계약 test'의 판정은 `pytest_gate.ini`(testpaths `A/tests`, `norecursedirs = tools`) 의미로 -- 시제품의 `collected`(경로가 `A/tests/` 아래이고 `test_*`)는 `A/tests/tools/test_*.py`도 수집으로 본다(지금 그런 파일 0). 문언에 "gate `pytest_gate.ini` 수집 규칙으로"를 붙인다.
* m4 시제품은 (바) (ii) 정적 확인과 (i)의 'diff = 승인 diff'를 기계화하지 않았다(승인 목록은 단위 이름뿐) -- auditor 몫으로 계약에 이미 있으므로 '재현할 수치'의 LISTED 6이 "(i) 이름 수준만 모의"임을 한 구절로 적는다.

## 5. TS6 (마) 전사

* F1 계약 1 (d)의 (A1)·(A3) 줄을 `draft_p4_first.spec.md` 계약 8 r4(현 판, 18:11) 줄과 앞 공백만 빼고 줄 단위 비교: (A1) 5줄(P4 62~66 → F1 56~60), (A3) 24줄(P4 72~95 → F1 61~84) **모두 바이트 같음**, 순서·연속 같음. (A2)·(B)는 옮기지 않음(문언대로).
* `pin_commit` `9d6800ef74017dd015f4628e840bdc9d965b42ce`: `rev-parse 9d6800e` 같음(40자), `merge-base --is-ancestor … 4a286f0` exit 0, 부모 정확히 하나 `a574f977…`(그 부모에 새 자리 없음, `36e170e^`에는 있음 -- 거부 표본 둘과 맞음). `pin_edits = ()`, 정수 0. 사용자 답 인용 `"(마) 전체 정규화 핀 (Recommended)"` jsonl `answers`와 같음.
* m5 옮긴 (A3) 머리에 "(마) 모듈 전체 정규화 핀 -- **기본안**"이 그대로 남았다(정본 P4 문장도 같음 -- 바이트 전사라 정상). 결정 완료 표기는 F1 51행이 이미 하므로 고치지 않아도 된다 -- 기록만.

## 6. 사용자 질문

없음. (6파일 잠금은 문안의 폴더 단위 결정 범위이고 답 뒤 고지도 됐다. S1·minor는 모두 원칙 기본안으로 문언 보강.)

## 7. 재현 명령(스크래치, 삭제됨)

```bash
git -c core.autocrlf=false clone -q --no-local <repo> C:/g258/r   # origin 제거·빈 hooksPath·detach 4a286f0
python -B my/cover.py            # 해시 3종·순서 뒤집기·39파일 판정 행렬·git pathspec 16 / :(glob) 38
python -B my/quote.py            # 두 문답 바이트 대조
python -B p3kit_f12/verify_approval_f1wp.py C:/g258/r/tools/gates C:/g258/r          # ALL OK
bash p3kit_f12/mk_chain_r1.sh C:/g258/c <repo>                                         # b035520 3fdf21c e40da5b
python -B p3kit_f12/f12_equiv.py C:/g258/c/r b035520 3fdf21c eq.json --d17 … [--approved out/approved_v5_5_mock.txt]   # 62/6/3 = 저자 json
python -B p3kit_f12/t0sim.py C:/g258/a b035520 3fdf21c t0.json ; f12_equiv … 85d044d c312809 --only <selftest 3>          # PASS 3
# 공격(C:/g258/a, plumbing): T1 base 18759c0/good cb2bf1e/bad 2771d7a(probe), 78b9eaf/f83c662/e7fa803(contracts); T3 40a0972→56f0ac1, d26020e→50bd728; T5 c32e57e
```
