# [T0-V4] 독립 검증 -- 2026-10-02

검증자 ≠ 작성자. gate `master` `4a286f0`(시작·끝 같음). 실제 저장소는 `git -C`로 읽기만 했다. 시작·끝 모두 HEAD·reflog 첫 줄이 `4a286f0`이고, `status --porcelain`은 37줄, md5 `dcc7b56b…`로 같다.
스크래치는 `/c/g261`만 썼다. 작업 트리에서 `-c core.autocrlf=false --no-local`로 복제했고 origin을 지웠으며, 빈 hooksPath와 TMP/TEMP `/c/g261/tmp`를 썼다. gate 도구는 `git archive 4a286f0 tools/gates`로 꺼냈다. 끝에 `/c/g261`을 지웠다.
작성자 키트(`step0_v4.sh`·`install_t0_proto.py`·`install_t0_c11.py`)는 모의 T를 만들 때만 썼다. 판정 수치는 gate 판 도구의 JSON을 내 스크립트로 직접 집계했다.

## 판정 요약

**발견은 사실이다.** V4 FAIL이 실제로 나고, 면제 기록을 두면 PASS가 되며, UNJUDGED 78은 TS2 식과 같다. 모두 재현했다.
기본안(decision 면제)을 Recommended로 두는 것은 타당하다.
다만 질문과 card에 **사실과 다른 문장이 둘** 있다. 하나는 '744행은 고칠 수 없다', 다른 하나는 '계약 11을 빼도 그 card에서 같은 문제가 다시 난다'이다. 그리고 면제가 card에 묶이지 않고 그 뒤 card에도 계속 적용된다는 점이 질문에 빠졌다.
질문 문장은 아래 '고친 질문'으로 바꿔서 올린다.

## (1) V4는 파일 전체를 본다 -- 확인

`git show 4a286f0:tools/gates/test_lint.py` 기준:
- 718~721행: `--base`와 `--head`가 있고 파일 인자가 없으면 `git diff --name-only --no-renames --diff-filter=AM`로 파일을 고른다(`tests/` 아래 `.py`, `tests/tools/`와 conftest는 뺀다).
- 723~726행: 고른 파일마다 `lint_file(rel, read(rel), …)`를 부른다. `read`는 705~709행이고 `git show <head>:<rel>`로 **파일 전체**를 읽는다. hunk만 보는 경로는 없다.
- 727~734행: 면제는 `--head`가 있을 때만 적용된다. `rch._approved_ids(root, ns.head)`(731행)를 쓰고, `rule == "(1)"`이면서 `output == "FAIL"`인 발견만 `exempt`로 바꾼다.
- `reachability.py` 180~193행 `_approved_ids`: **head 트리**의 `.ai/approvals/*.md` 가운데 `_`로 시작하지 않고 `---\n`으로 시작하며 `\ntarget_kind: decision\n`이 있는 파일의 `target:` 줄을 쉼표로 나눠 모은다.
- 선례 `.ai/approvals/20260923-c9-v4-exempt.md`와 머리 모양이 같다(id·date·target_kind decision·`<파일>::<test>` target·scope). 본문 절도 같다(사용자 원문·범위 설명·재검토).
- 정정 1: spec card 158행의 "702~707행이 head 트리의 파일 전체를 읽는다"는 줄 번호가 틀렸다. 702~703행은 '피검 없음' 오류이고, 실제 읽기는 **705~709행**이다.

## (2) 재현 -- 확인

| 조건 | 결과 |
|---|---|
| 모의 T = `4a286f0` + 계약 1~4 시제품 + 계약 11. V4 `--interface-card` 단독(기존 함수 6: `size_transistor`·`width_from_id_density`·`check_quasi_static`·`_build_theta_evaluator`·`load_topology`·`_metric_kcl_residual`) | FAIL, exit 1. 대상 파일 7개(contracts 4 + unit 3). 규칙 (1) FAIL은 정확히 2건이다: `test_s009_revalidate_finger_override` 719·744행. (2) UNJUDGED 78(모두 SR selftest), (2) NO-SUBJECT 241. 다른 FAIL은 0이다. |
| base 트리의 같은 파일, 같은 card, `--head 4a286f0` | FAIL. 같은 두 줄이 base에서는 **714·739행**으로 나온다(T가 import 5줄을 더하므로). T0가 만든 FAIL이 아니다. |
| T 위에 면제 기록을 head 트리에 둔 커밋. date 자리표시자만 `2026-10-02`로 채웠다 | PASS, exit 0. (1) exempt 2(719·744행), UNJUDGED 78, FAIL 0. |
| `merge_gate.py parse-approval`, 파일 이름 `20261002-p3-t0-v4-s009-exempt.md` | exit 0. `target_list` 1개. |
| 같은 명령, 초안 그대로 | exit 2. 파일 이름 `approval_…draft.md`가 id와 다르고, `date: <사용자 답 날짜>`는 '날짜 형식 위반'이다. 둘 다 예정된 자리표시자다. 커밋 전에 채우면 된다. |

## (3) '두 줄을 고치는' 대안 -- 일부 거짓

모래상자에서 T 위에 변형을 만들었다. 피검은 같은 interface card이고, V5는 gate 판 `weakening_diff.py`로 쟀다.

| 변형 | V4 (1) | test_s009 pytest | V5 |
|---|---|---|---|
| A: 719행 우변 `_l4_r1.ID` → `200e-6 / _l4_gm_id` | 744행 FAIL 1 | PASS | FAIL(계약 2~4 몫 4건 그대로). `diff_paths` = contracts 3. **unit 파일 발견 0** |
| B: 744행을 스냅숏 지역 변수(`_l4_w0 = _l4_ctx.sized["M1"]["W"]`)로 | 720·745행 FAIL 2. 인라인이 꿰뚫는다 | PASS | 위와 같음 |
| C: 744행 우변 → `_l4_L * (200e-6 / _l4_gm_id) / lut.gm_id_to_id_density(_l4_gm_id, _l4_L, _l4_vds, 0.0)` | **719행만 FAIL. 744행은 넘어간다** | PASS | 위와 같음 |
| A+C | **V4 PASS, 면제 없음** | PASS | 위와 같음. 변경이 안 보인다 |

- 719행에 대한 작성자 주장은 맞다. 기대값이 '원래 소자 ID 보존'에서 '식 gm/gm_id 값'으로 바뀌고, V5가 잡지 못한다.
- 744행에 대한 주장("지역 변수로 바꿔도 FAIL … 게이트 회피 말고는 길이 없다")은 **절반만 맞다**. 스냅숏은 FAIL이 맞다. 하지만 W 식(L·ID/IDu, `size_transistor` 구현과 같은 식)으로 바꾸면 V4를 넘는다.
- 그러니 두 줄 모두 "고칠 수는 있지만 판정 기준이 바뀌고(구현 식 복사 쪽으로), 그 변경을 V5가 못 잡는다"가 정확하다. (iii)을 하지 않는다는 결론은 그대로 유지된다. card 158~167행 (iii)과 승인 초안 '범위 설명'의 744행 문장은 고친다.

## (4) 질문에서 빠진 다른 길

- **계약 11을 별도 card로 옮기고 그 card에 같은 면제를 싣는다.** T0에 싣는 것과 차이가 없다. `_approved_ids`는 card를 보지 않고 head 트리 전체를 읽기 때문이다. 이 길은 따로 고를 이유가 없다.
- **선택지 3 '계약 11을 T0에서 빼기'의 "같은 V4 문제가 그 card에서 다시 납니다"는 측정과 다르다.**
  - `4a286f0`에 계약 11만 얹은 W-1 단독 T를 만들어 쟀다.
  - `--subject topology_library:nmcnr_predict_ac_response`(계약 11이 언급하는 유일한 엔진 함수)만 주면 **PASS**다(UNJUDGED 2, FAIL 0).
  - `--subject sizing_recipe:size_transistor`를 주면 같은 FAIL 2가 난다.
  - 즉 FAIL은 피검 집합에 달려 있다. T0의 FAIL은 T0 interface card에 `size_transistor`가 있기 때문이다. TS2 판정 기록 V4 basis도 피검이 `optimize_full_circuit_budget` 하나라 UNJUDGED 26만 있었고, s009는 그때 판정되지 않았다.
  - 그래서 선택지 3은 면제 없이 갈 수 있는 길이다. 다만 비용이 있다. [W-1] (가)를 되돌려야 하고 card가 하나 는다. 그리고 `size_transistor`를 피검으로 가진 card가 그 파일을 바꾸면 같은 FAIL이 다시 난다.
  - 설명을 고친다.
- **게이트 변경 card: V4를 바뀐 test 함수(또는 바뀐 문장)로 좁힌다.** V3 `20260930-v3-changed-stmt-scope`와 같은 꼴이다.
  - 비용: 그 선례는 spec 281행, 문서 커밋(design 05 §10·계획 N4.2), interface card, `target_kind diff` 약화 승인 60행, 세 역할 worktree가 들었다.
  - V4판에서는 '모듈 머리(import) 변경이 모든 test의 이름 해석에 영향을 주는가'를 정의해야 하고, 규칙 (3)~(5)의 파일 단위 의미도 다시 정해야 한다. 그러니 같은 규모이거나 더 크다(card 1개 + 약화 승인 + redteam 사례).
  - 판단: 기존 C13 면제 경로가 승인 한 건으로 막힘을 푼다. 그러니 '인프라는 gmid를 막을 때만' 원칙으로 보아 **지금은 정당하지 않다**.
  - 백로그 후보로 둔다. 근거: F1 등에서 큰 selftest 파일을 건드리면 같은 종류가 다시 날 수 있다.
  - 이 길도 범위 축소, 곧 약화라서 '약화 아닌 대안'은 아니다.
- **interface card에서 `size_transistor`를 빼서 피검을 줄인다.** 피검 입력을 조작하는 것이라 게이트 회피다. 선택지가 아니다. 719행 우변에 불투명 함수를 감싸는 것도 같다.

## (5) UNJUDGED 78 = TS2 `caac910` -- 확인(더 강하게)

- 내 스크립트로 확인했다(AST, 함수별). 78개 모두 같은 test 함수 안에서 assert 식과 **메시지까지** `ast.unparse` 문자 단위로 `caac910`과 같다. 다른 것은 0이다.
- 분포: s009 8, s010 9, s011 16, s013 3, s015 11, s038 1, s040 3, s042 4, s062 7, s065 16.
- TS2 V4 basis 전수 대조(642개 중 636개가 이관본 식과 같음)에서 예외 6개는 S014·S051·S054·design_report·stick 조건 승격이다. 위 78개 함수는 그 예외에 들지 않는다. 그러니 oracle (c) 출처를 그대로 잇는다는 주장은 성립한다.
- 참고: 파일 전체 assert는 T 219, `caac910` 229다. T에 있고 `caac910`에 없는 것은 0이다.
- 표현 정정: TS2 basis는 이 78개를 'UNJUDGED'로 다룬 것이 아니라 '전수 대조'로 덮었다. TS2 때 UNJUDGED는 26개였다. auditor basis에는 "TS2 전수 대조의 식과 같다"로 적는다.

## (6) 질문 문장 검토

- 형식: header `T0-V4`(5자), 선택지 3, Recommended가 첫째, multiSelect false. 문제없다.
- 고칠 것:
  - (a) 선택지 2의 "744행은 고쳐도 FAIL이 남아"는 거짓이다(위 C 변형).
  - (b) 선택지 3의 "같은 V4 문제가 그 card에서 다시 납니다"는 피검에 달려 있다. 측정상 PASS가 가능하다.
  - (c) 선택지 1에 면제가 **T0에 묶이지 않는다**는 점을 적는다. head 트리에 남아 있는 동안 이후 모든 card의 V4에 적용되고, 이름·경로가 바뀌면 풀린다. 사용자가 무엇을 승인하는지 정확히 알아야 한다.
  - (d) 본문에 "피검 `size_transistor`는 입력을 만드는 데만 쓰였다(시험 대상은 `revalidate_finger_override`)"와 "base에서도 같은 FAIL"을 한 줄로 넣는다. 그래야 FAIL이 오검출 성격이라는 것과 T0가 만든 문제가 아니라는 것이 드러난다.
- 승인 초안: (3)의 744행 문장을 고친다. '덮지 않는 것'에 "다른 card 범위로 한정하지 않는다(head 트리에 남는 동안 유지)"를 한 줄 더한다. 줄 번호 702~707은 705~709로 고친다.

## 고친 질문(JSON)

```json
{"question": "[T0-V4] T0 계약 11(unit selftest 3파일 import 출처 3줄)로 test_selftest_sizing_recipe.py가 diff에 들어가면, 파일 전체를 보는 V4가 T0가 손대지 않는 기존 test_s009의 판정 2줄(revalidate 뒤 ID 보존, 원본 ctx 불변)을 규칙 (1) '같은 피검 호출이 양쪽에 있다'로 FAIL합니다. 피검 size_transistor는 입력 소자를 만드는 데만 쓰였고, base 트리에서도 같은 피검으로 재면 같은 FAIL입니다(TS2 때는 피검이 달라 드러나지 않았습니다). 어떻게 할까요?", "header": "T0-V4", "multiSelect": false, "options": [{"label": "test_s009 규칙(1) 면제 (Recommended)", "description": "선례 c9-v4-exempt처럼 decision 승인 기록 하나로 이 test id의 규칙 (1)만 면제합니다. 판정 2줄은 그대로이고 다른 규칙·다른 test는 계속 검사합니다. 기록이 저장소에 있는 동안 이후 card의 V4에도 적용되고, test 이름·경로가 바뀌면 풀립니다. 모래상자: 기록이 있으면 V4 PASS(면제 2, FAIL 0; 미판정 78은 TS2 이관본과 식이 같아 auditor가 basis에 적음)."}, {"label": "T0에서 두 줄을 식 값으로 고침", "description": "719행 기대값을 gm/gm_id 식으로, 744행을 W = L·ID/IDu 식으로 바꾸면 면제 없이 V4·test 모두 PASS입니다(모래상자). 대신 '원래 값 보존·원본 불변' 판정이 '구현과 같은 식의 값'으로 바뀌고, 이 파일은 V5 diff 해시 밖이라 V5가 이 변경을 잡지 못합니다. 계약 11의 '기대값 불변'과 V5 승인 범위를 다시 써야 합니다."}, {"label": "계약 11을 T0에서 빼기", "description": "unit 3파일 import 수정을 별도 test-only card로 옮겨, 이미 고른 [W-1] (가)를 되돌립니다. M4 전에 card가 하나 더 듭니다. 그 card의 피검이 nmcnr_predict_ac_response뿐이면 V4는 이 FAIL을 내지 않습니다(모래상자 PASS). 그러나 이는 test_s009를 판정하지 않기 때문이고, size_transistor를 피검으로 가진 card가 그 파일을 바꾸면 같은 FAIL이 다시 납니다."}]}
```
