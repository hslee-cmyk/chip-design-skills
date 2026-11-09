# 독립 검토: M1 spec 초안(`draft_p3_m1.spec.md`) + `m_cards_plan.md`

검토자: 독립 reviewer(작성자 아님). 2026-10-02. 저장소는 읽기만 했다. 스크래치는 `C:/g216`(격리 복제본, 작업 끝에 삭제).
기준: gate `master` `36e170e`의 design `30-module-split` v8.5(§2.2·§3·§6.2·§8 M행·§10 E3/E3b/IMPORT-ANY/PT3, D-22·D-30·D-31), D0a/D0b/FU/G1 spec 초안.
작성자의 `p3kit_m1/` 스크립트는 쓰지 않았다. G1 시제품(`g1_kit`)만 설치 도구로 썼다(아래 R0).

## 판정

**조건부 통과(S 3건 수정 뒤 card 커밋 가능)**. 차단(B) 0건.
M1의 동등성 주장(단위 집합 8, 바이트 이동, `check` 발견 0, V3/V6/V7, IMPORT-ANY, E3/E3b, PT3, E-LIB, E-INST)은 **독립 재구현으로 전부 재현**했다.
남은 문제는 판정식이 아니라 (1) M1-2를 '사용자 질문 아님'으로 분류한 것, (2) M1-2의 근본 원인(레지스트리 행 키 오기)을 놓친 것, (3) W-1 권고안의 기준 변경 성격이다.

## 재측정 방법(독립)

* 모의 base 사슬(`C:/g216/r`, gate `36e170e`에서 복제, LF 체크아웃):
  `36e170e` → `0be054c` FU 대역(DR 28행·ACF 38행 첫 import 앞에 `from __future__ import annotations`) →
  `f89f4e2` G1 시제품(R0 참조) → `1d374d7` N3.10 MOD1 `대표 대상`에 `` `_QUERY_CACHE_MAX` `` 토큰(M1-2 기본안) →
  `4d21539` D0b 대역(내 재생성 스크립트: 대상 행 354, 칸 225개 바뀜, `보류(Phase 3)`→`(Phase 4)` 9칸) = **모의 base B**.
* D0a `plan`·`check`는 **D0a spec 계약 1~4 문언에서 내가 새로 구현**(`C:/g216/mp.py`; G1 `SourceIndex`·`moved_defs`·`binding_origin`만 import).
  단위 키는 계약 2 문언(문장 = 바인딩 이름을 이은 것, `--keymode names`)이 기본이고, 비교용으로 시제품 모양(`<stmt:해시>`, `--keymode hash`)도 낼 수 있게 했다.
* 이동은 내 스크립트(`domove.py`)로 B의 `plan` 출력(`assignment`·`mod_imports`·`reexports`)만 보고 했다 → **모의 head H = `3970c48`**.
* 판정은 design §10의 python/bash를 design 문서에서 그대로 뽑아 실행했다(E3_AST, E3B_AST, `import_any`), PT3·E-LIB·E-INST는 같은 체크아웃 경로에서 base → head 차례로.

**R0(G1 시제품 설치 -- M1 밖 관찰)**: `g1_kit/install_proto.py`는 `36e170e`에 그대로 설치되지 않는다. (i) 앵커 `mc print`가 면제 묶기(34)가 바꾼 출력 줄과 맞지 않아 exit 1,
(ii) 앵커만 고치면 `_strip_doc`~`changed_defs` 사이를 통째로 지우는 치환이 34가 넣은 `bind_hash`·`_HASH_RE`·`approved_index`·`exempt_decision`까지 지워 V3가 `NameError: approved_index`로 죽는다.
치환 끝을 `def bind_hash` 앞으로 고친 사본으로 설치해 측정했다(G1 판정 동작은 같음). M1 spec 머리의 "`36e170e` 기준에서도 그대로"는 **diff로만 확인한 문장**이었고, 재실행으로는 이번이 처음 확인이다 -- 결과는 같았다.
G1 card(키트)는 새 base에서 이 두 앵커를 다시 잡아야 한다(G1 spec 계약 8 '정의 하나'가 `bind_hash`를 건드리지 않게).

## 재현 결과(모의 B = `4d21539`, H = `3970c48`)

| 항목 | spec 주장 | 독립 측정 | 판정 |
|---|---|---|---|
| D0b 전 `plan`(시제품 키) | 배정 403, A-1 60·A-4 229·A-5 64·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1, 판정 목록 0 | 같음(403, 같은 분포, `upward`·`cycles`·`unassigned`·`conflicts`·`import_time_high`·`import_conflicts` 0) | 일치 |
| MOD1 단위 | 8(SR 52~73·141~203·206~251·257·259~672·1343~1353·1356~1394·4782~4803) | 같은 8단위, 같은 줄 범위 | 일치 |
| `mod_imports["gmid_lut.py"]` | future·`import math`·`import numpy as np` | 같음 | 일치 |
| SR 재수출 줄 | `from gmid_lut import GmIdLUT, …, lut_conditions_from_npz`(8이름, 45행 뒤) | 같음 | 일치 |
| `check` | exit 0, 11종 0, assigned 8·moved_units 8·moved_defs 22 | 같음(목적지 전부 `gmid_lut.py`) | 일치 |
| 계약 3 독립 `ast.dump` | 8/8, SR = base − 단위 + 재수출 1 | (a) True 8/8 (b) True, 재수출 이름 = 바인딩 이름·이름순·`as` 없음 (c) 첫 문장 future | 일치 |
| V3/V6/V7(G1) | V3 `defs` []·`mutants` 0·`moved` 22·`move_rejected` {}, V6 `findings` [], V7 `new_defs` [] | 같음(V3 76 s, V6 64 s, V7 89 s) | 일치 |
| IMPORT-ANY | base `tried=5 expected=5 failed=0`, head `6/6/0` | 같음 | 일치 |
| E3 | `stmt` 69·`call` 9·제외 밖 66파일 같음 | 같음 | 일치 |
| E3b(SR 사본) | `LIVE moved_out=8 base_files_reading_moved_out=46 pre_existing=1`, FAIL 9(`<동적 이름>`) = base 자기 대조 | 같음, FAIL 집합 같음. SD·TL·DR·ACF 사본 `INVALID`(m=0) | 일치 |
| PT3 | 1054 passed·15 xfailed, id 1069, 차이 0 | **1047 passed·15 xfailed, id 1062**, id 집합 같음, 결과 차이 0 | 수 차이 설명됨(아래) |
| E-LIB | `hash` `1d2e3bf6…`, JSON 전체 같음 | 같음 | 일치 |
| E-INST | 22키 중 `engine_origin`만 다름(+`gmid_lut`), raw `2fc426d9…`·`ef3cd996…` | 같음, head `engine_origin` 경로 전부 iso 안, stdout(elapsed 가림) 같음 | 일치 |
| 계약 9 `plan`(H) | exit 0·일곱 0·사상 차이 0, 옮긴 8단위 A-0 | 같음 | 일치 |
| 거부 R-1·R-3·R-4·R-5·R-7 | 표 | `check` 발견 종류 같음(R-1 move-set·move-rejected 1·changed 2·lost 2·shim 1; R-3 order 1 + 단독 import FAIL; R-4 import-dup 1·move-rejected 3·changed 3·lost 3·rebind 2·shim 1; R-5 move-rejected 8·changed 8·lost 8·rebind 11·shim 1·`future` 0; R-7 changed 1) | 일치(R-6 미측정) |

**PT3 수 차이(1054/1069 대 1047/1062)**: 작성자 모의 base에는 D0b 계약 test 시제품 7개가 들어 있었고 내 D0b 대역에는 test가 없다(1047 + 7 = 1054, 1062 + 7 = 1069).
design 30 본문(550행 FU 측정)의 `1047 passed·15 xfailed·id 1062`와도 같다. 판정(같음·실패 0)에는 영향 없음. 실제 base에서는 T0 변경과 D0a `tooling/test_move_plan.py`·D0b 계약 test가 더해져 수가 또 바뀐다 -- spec이 이미 '관찰, auditor가 다시 잰다'로 둔 대로다.

## 발견

### S-1 M1-2는 '사용자 질문 아님'이 아니다 -- 기본안이 D-11 사용자 승인을 요구한다

**사실 확인(독립)**: D0a 계약 2 문언 키(`--keymode names`)로 D0b 전 트리를 계산하면
`upward` 1(`sizing_recipe.py::SemiEmpiricalGmIdLUT -> sizing_recipe.py::_QUERY_CACHE_MAX`), `cycles` 1(`gmid_lut.py` ↔ `gmid_sizing_engine.py`), MOD1 **7단위**,
`mod_imports["gmid_lut.py"]`에 `from gmid_sizing_engine import _QUERY_CACHE_MAX`(위쪽 import)가 생긴다. 상수 행 변화도 W-4대로(`_COMPENSATION_REGISTRY`·`_L_ROLE_TARGETS` MOD8 → MOD4, `INSTANCE_TOP_FIELDS` MOD9 → SD 잔류).
N3.10 MOD1에 토큰 하나를 더하면 `upward` 0·`cycles` 0·MOD1 8단위·`mod_imports` 3줄 -- M1-2의 관찰은 정확하다.
**문제**: '결정 필요 항목' 머리가 "모두 기본안이 있다(원칙 유도 -- 사용자 질문 아님)"인데, M1-2 기본안은 스스로 적었듯 **N3.10 표 diff의 D-11 별도 사용자 승인**(`target_kind: diff`)이다.
원천이 A-1 토큰(`SemiEmpiricalGmIdLUT`)인 `upward`라 D0b 계약 8 (a) 멈춤 경로에 정확히 걸린다 -- 즉 **D0b 착수 전 사용자 결정 하나가 숨어 있다**.
그리고 "어느 길이든 M1 단위 집합은 같은 8단위"의 '두 길'은 (시제품 키 -- 계약 문언이 아니다)와 (문언 키 + 승인)이라, 승인이 거절되면 M1은 착수할 수 없다.
**고칠 것**: M1-2를 'D0b 착수 조건 = 사용자 결정(또는 S-2의 원인 수정)'으로 분류를 바꾸고, D0b spec '실측 3'의 "(a)~(e) 모두 비어 있다"가 시제품 키로 잰 값이라 계약 문언 키에서는 거짓임을 D0b 초안에 사실로 적는다(작성자가 '오케스트레이터 할 일'로 적은 내용을 착수 조건으로 승격).

### S-2 M1-2의 근본 원인은 레지스트리 행 키 오기다 -- N3.10 개정 없이 닫힌다

레지스트리 277행은 함수 칸이 `` `_QUERY_CACHE_MAX` ``인데 책임 칸이 "4D 배열 적재, shape 검증, log(ID/GM/GDS) 사전계산(B15), 캐시 dict 5종 생성" -- **`SemiEmpiricalGmIdLUT.__init__`의 설명**이다(SR 257행 상수 바로 뒤가 259행 클래스).
같은 모양이 291행(`_KNEE_L_CACHE` 칸, 책임 = `knee_L_for_kind`), 293행(`_FEASIBLE_L_WINDOW_CACHE` 칸, 책임 = `feasible_L_window`)에도 있고 세 함수 모두 자기 행이 없다(`grep -c` 0) --
앞 상수 이름을 함수 칸에 잘못 적은 체계적 오기로 보인다(294행 `_L_ROLE_TARGETS`도 같은 모양 의심, 미확인). 시제품 키(`<stmt:해시>`)는 이 행들과 짝이 지어지지 않아 오기가 가려졌고, 계약 문언 키가 그것을 드러냈다.
**실측**: 277·291·293 세 행의 함수 칸만 고친 가지(토큰 추가 없음, 문언 키)에서 `plan` → `upward` 0·`cycles` 0·`unassigned` 0·`conflicts` 0, MOD1 = 같은 8단위(`_QUERY_CACHE_MAX`는 A-5 → MOD1), `mod_imports` 3줄 같음.
**권고**: 기본안을 '레지스트리 함수 칸 사실 정정(오기 3~4행)'으로 두고 N3.10 토큰 추가는 대안으로 내린다. 레지스트리 함수 칸 정정은 N3.10(계획) 개정이 아니라 D-11 대상이 아니다
(D0b 전 문서 커밋 -- D-27 동결 전). 다만 배정을 바꾸는 사실 정정이므로 오케스트레이터가 정정 근거(책임 칸·소스 줄)를 기록에 남기고, 판단이 애매하면 사용자에게 한 줄로 확인한다.
W-4의 다른 상수 행(`_L_ROLE_TARGETS` 등)의 M4/M8 배정 변화도 같은 정정 여부에 따라 달라진다 -- m_cards_plan W-4에 함께 적을 것.

### S-3 W-1은 실재하지만 권고 (가)는 판정 기준 완화다 -- (나)를 동등 이상으로 제시할 것

**사실 확인(정적)**: `36e170e`에서 `test_selftest_topology_library.py:24`가 TL에서 `math`, `test_selftest_sizing_recipe.py:24`가 SR에서 `_dc_replace`·`json`·`math`·`np`·`nmcnr_predict_ac_response`(SR이 TL에서 import),
`test_selftest_design_report.py:24`가 DR에서 `os`를 읽는다(엔진 파일이 import로 묶은 이름). SHIM (b)(design §3, D0a 계약 4 "남은 일반 import 줄 포함 -- 그 card가 지운다")대로 완전 shim에서 그 import 줄을 지우면 이 import가 깨진다.
재수출로 살릴 수도 없다: `from gmid_sizing_engine import math`는 '재수출 줄'이지만 SHIM (c) 이름 집합(base 재수출 ∪ 옮긴 단위 이름)에 `math`가 없어 발견이 된다. 그래서 M4(TL)·M8 또는 M9(SR·DR)는 지금 기준으로 PT3를 통과할 수 없다 -- W-1의 진단은 맞다.
**권고에 대한 판단**: (가) "base에 있던 import 문장을 완전 shim에 남기는 것 허용"은 SHIM (b)·D0a 계약 4 문언을 바꾸는 **기준 완화**다(완전 shim에 허용되는 문장 집합이 넓어진다) -- 작성자도 사용자 몫이라 적었지만 '권고'로 둘 근거가 약하다.
(나) "M4 전에 세 selftest의 엔진 밖 이름 import를 표준 모듈 직접 import로" 또는 그 변형 (나') "M4 card 자신에 test 커밋(V5 승인)으로 같은 수정"은 판정 기준을 건드리지 않고, F1이 어차피 할 import 경로 정정의 일부를 앞당길 뿐이다.
원칙(기준 약화는 사용자 승인, 기준 불변 경로가 있으면 그쪽)으로는 (나)/(나')가 기본안이고 (가)는 대안이다. 어느 쪽이든 M4 착수 전 결정이고 M1에는 영향이 없다(M1은 완전 shim을 만들지 않는다 -- 확인).

### 경미(minor)

* m-1 **R-2 행의 "계약 8 (b) 새 FAIL"은 틀렸다**: R-2(재수출에서 `GmIdLUT` 뺌) 커밋에 E3b SR 사본을 돌리면 새 FAIL **0**(`LIVE` 줄만, FAIL은 base와 같은 `<동적 이름>` 9줄).
  추적 파일 중 `sizing_recipe`에서 `GmIdLUT`을 읽는 곳이 없기 때문이다(문자열·주석 언급뿐). 작성자 실측 10도 R-2에 E3b를 적지 않았다. 거부는 `check` `rebind` 9·`shim` 1과 계약 3 (b)가 한다 -- 표에서 '계약 8 (b) 새 FAIL'을 빼거나, 읽는 파일이 있는 이름으로 변형을 바꿀 것 -- 실측: 재수출에서 `lut_conditions_from_npz`를 뺀 변형은 E3b SR 사본이 새 FAIL 5줄(`test_restore_plan_functions.py:115·122·129·135·143 lut_conditions_from_npz`)로 거부한다.
* m-2 **E-LIB 사본 sha256 표기**: 계약 6 (b)의 `045f65c8…`는 `core.autocrlf=true` 체크아웃(CRLF) 파일의 해시다. design §10 E5처럼 `git show`로 꺼낸 blob은 `41b72d7d…`다(E-INST `7d26134a…`는 blob 해시라 두 값의 기준이 섞였다). 어느 바이트의 해시인지 적거나 blob 해시로 통일할 것.
* m-3 계약 4의 `not_targeted`·`targets_by_def`는 `36e170e` V3가 내지 않는다(범위 정책 35 미병합, `targets_by_def` 0회). 착수 조건(35 병합)에 걸려 있으니 문제는 아니나, '작성 전 실측 8'처럼 판정 때 실측임을 계약 4에도 한 구절 적어 두면 auditor 혼동이 없다.
* m-4 `m_cards_plan.md` §1 표의 단위 수(M4 102·M8 32·M9 17·SD 잔류 110·합 291)는 **시제품 키** 값이다(내 재구현으로 같은 수 재현). 계약 문언 키 + 토큰(또는 S-2 정정)에서는 M4 **104**·M8 **30**·M9 **16**·SD 잔류 **111**·이동 합 **290**(CACHE-ID 세 캐시는 사용 함수와 같은 MOD 유지). 표 머리에 키 방식을 적고 W-4에 이 수를 넣을 것.
* m-5 m_cards_plan W-2(ACF 재수출 위치)는 사실(ACF 머리: future 38 → import 39~41 → `sys.path.insert` 43 → `from stick_diagram import load_topology` 44). 기본안(경로 설정 묶음의 마지막 import 뒤)은 타당하다. 다만 "어느 판정도 위치를 보지 않는다"면 M2·M9 계약에 auditor 측정(A 밖 cwd에서 `spec_from_file_location` 로드)을 넣는 것이 유일한 방어라는 점을 card 초안 매개변수(§3-5)에 명시할 것.
* m-6 M1 spec '규칙 A-1 5·A-4 2·A-5 1'은 시제품 키 값이다. 문언 키 + 토큰이면 D0b 재생성 뒤 A-1 6·A-4 2(D0b 전 A-1 6·A-5 1·A-6 1), S-2 정정이면 A-1 5·A-4 2·A-5 1. '재현할 수치'를 D0b 판정 기록 값으로 바꾼다는 실측 15 (ii)대로면 문제 없음.

## test 커밋 0 equivalence 절차(FU 선례 대조)

M1 '판정 유형 근거'는 FU spec(초안)의 근거 (i)~(iii)과 같은 문장을 인용하고, `role/test/<id>`를 커밋 0으로 만들어 두는 절차(FU 작성 전 실측 15)를 그대로 쓴다. gate `36e170e`에서 다시 확인:
`merge_gate.py` 1152행 `if ev == "red-green" and not chain`(equivalence의 빈 test 사슬은 거부하지 않음), 1173행의 빈 사슬 거부는 test-only 분기, `role_hooks.py` 913행(code·audit worktree base = `role/test/<id>`)·1066행(`refs/heads/role/test/<id>`),
`role_commit_gate.py` 98~99행(audit 병합 HEAD = `role/test/<id>` 끝), design 05 289행 "equivalence | 같음, 단 ①의 `Role: test`가 0개면 M^1 = `old`" -- 모두 그대로다. **절차 일치.**
유의: FU 자체가 아직 병합 전이라 '선례'는 실행된 선례가 아니라 같은 근거의 초안이다(FU가 D0b 전, M1보다 먼저 병합되므로 M1 착수 시점에는 실행 선례가 된다 -- 그때 FU 판정 기록을 '작성 전 실측 15'에 인용할 것).

## M1-1·M1-3 판단

* M1-1(MOD 파일 모듈 docstring 없음): 동의. R-7로 `changed` 1을 독립 확인했다. 기본안 (가)는 문서·도구 개정 0이고 이동 card = 이동만 원칙에 맞다.
* M1-3(E3·E3b 식의 card 단위 사용, base 자기 대조 FAIL 집합): 동의(강화). design 블록을 그대로 뽑아 SR 사본으로 돌려 주장 수치를 재현했고, 단위를 내보내지 않는 네 split 사본이 `INVALID`인 것도 확인했다. 단 m-1처럼 이 판정이 실제로 무엇을 거부하는지는 이름마다 읽는 파일이 있을 때뿐이다.

## 정리

스크래치 `C:/g216`은 삭제했다. 저장소 `git status`는 시작 때와 같다(쓰기 0 -- 이 파일만 `_drafts`에 새로 씀).
