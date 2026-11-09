# 판정 기록 -- 계획 v6.38.24 / design 40 v1.16.21 / WB-1 card 여섯째 개정 (위임 A-139 단순화) 독립 판정

- 판정자: 독립 판정 agent(작성자 아님). 2026-11-06.
- 대상: worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261106-simplify-plan`, 브랜치 `plan/simplify-a139`, 커밋 `31dda995`(base `29e907b9`). 바뀐 파일은 plan·history·D40·design history·WB-1 spec·interface이고, 판정 시점에 worktree는 깨끗했다.
- 기준:
  - A-139(`wt/_drafts/la1_auto_decisions.md`:145)와 점검 기록 `new_sets_branches_simplicity_check.md` 항목 2·4·5.
  - 사용자 지시: "새로운 집합을 만들거나 가지를 새로 만들때는 … 불필요하게 복잡해지지 않는지 점검해." / "원리에 맞으면 현재 코드 구현은 기준이 아니야. 재작성의 대상일 뿐이지."
  - 프로젝트 CLAUDE.md(O-229, 원칙 7·8·10·25), 상위 graph 단일 정본 규칙.
- 방법: `git -C diff/show/grep`, `grep`, `sed`, `awk`로 읽기만 했다. pytest·ngspice·python은 0이다. 엔진은 WB-1 code 브랜치 `role/code/20261104-wb1`(머리 `29e907b9`)을 원칙 8 용도(재작성 범위)로만 인용했다.

## 결론

**Major 1건(M-1), minor 4건.** A-139 문언 반영, 부류 셋에서 둘로 줄인 것, 집계 규칙 하나는 맞다. 작성자 의문 (2)는 R-3 해석이 성립한다. 남은 Major는 하나다: 범위 7 (a)가 쓰는 '레이아웃이 정한 요청 (nf, finger_w)'가 계획의 LY3 W_request 정의({device, W_new, reason})에 없다.

## (1) A-139 문언 대조

| A-139 요소 | 계획 자리 | 판정 |
|---|---|---|
| `dc_finger` 원리 하나('그 평가가 쓴 손가락, 입력이면 선택 함수를 부르지 않음'), 레이아웃 뒤도 소자 전부 행 | N6.32 범위 7 (a) 머리, 범위 5 W′ 문장, D40 §3.7-A 3·6 | 같음 |
| 대기 = 레이아웃 요청 (nf, finger_w) 참조, `finger_slice` 재호출 금지(A-62 D5) | 범위 7 (a), spec 재작성 범위 여섯째 행 | 같음(정의 출처는 M-1) |
| 접합 부류 둘(배치 `layout_ref` 확산 / 나머지 그 평가 `dc_finger`), (다)·helper·`RealizedFinger.fp` 덧댐 삭제 | 범위 7 (a) '접합 기하', 완료 (10) (a) '정의 0 grep' | 같음 |
| 집계 규칙 하나(min·max 항에 None → 집계 None) | N3.6 표 10행 괄호 | 같음 |
| LM-1e 갈래 넷 → 셋, (d) 기록 이름 = 봉인 6 '띠 미정' | N6.40 LM-1e 3 (a)~(c)·6 (1) | 같음 |
| '봉인 3·4' → '봉인 1·3' | LM-1e 3 (a), N3.6 표 10행 | 같음. N3.6 표에서 봉인 4는 tol을 쓰지 않고, 노드 max 집계는 봉인 1(노드 충돌)·3(KCL)이다 -- 맞음 |
| 접합 용량 정본 DEC-91 그대로, 질문 대기 | 범위 7 (a) '**접합 용량 정본은 DEC-91 그대로, 질문 대기**' | 같음 |
| 유지: front 재분류·`moved`·게이트, 질문 후보 (4)(6) | 범위 7 (b) 머리, LM-1e 3 끝, history | 같음 |

## (2) 작성자 의문

### (2-1) 배치 소자 `dc_finger` 행이 `layout_ref`와 같은 값인 것 -- **graph 규칙 3·4 위반 아님. R-3과 같은 해석이 성립한다.**

- **선례**: 실현 평가 R-3(DEC-105 (2) (ii), 위임 A-62 D5)은 '`dc_finger` = 입력 값(탐색 스냅샷 `dc_finger`), `finger_slice` 호출 0'이다. 다른 스냅샷의 같은 필드 값을 그 평가 필드로 쓰는 것을 이미 사본이 아니라고 정했다. 레이아웃 뒤 평가가 `layout_ref`의 (nf, finger_w)를 그 평가 `dc_finger`로 쓰는 것도 같은 꼴이다.
- **두 필드는 정의 축이 다르다.**
  - `dc_finger` = S2 `dc` 층의 '그 평가 DC 해가 쓴 손가락 (m, w_s, 잔차)'.
  - `layout_ref` = S2 `layout` 층의 '레이아웃 실현 확산 기하(ad·as·pd·ps 포함, 확산 공유 결과)'.
  - 겹치는 것은 (m, w_f) 투영뿐이다.
  - 같은 목적으로 둘을 읽는 소비자도 없다. 접합은 배치 소자 = `layout_ref`, 나머지 = `dc_finger`로 나뉜다.
- **(가-2)안**(배치 행을 쓰지 않음)은 열 일부만 채운다. 그러면 손가락 의존 소비자가 평가 종류마다 두 자리를 읽어야 해서 부류 갈래가 되살아난다(점검 기록 :84 ⚠). 단순화 목적과 반대다.
- 남은 일은 minor n1: 정의 축을 문언에 적는 것(graph 규칙 3 '정의가 다르면 축을 적음').

### (2-2) `w_request`를 요청 손가락 행 참조로 바꾼 것

**`realized_geometry`(배치 소자도 `w_request`에 넣음)**: 모순 없음. 엔진 사실(재작성 범위 인용):
- `convergence/realized_geometry.py`:7·:24는 놓인 소자 = nf × finger_w, 대기 소자 = 요청 W를 넣는다.
- 같은 docstring은 대기 소자를 `layout_ref`에서 뺀다. 이유는 '레이아웃이 놓은 잠정 기하가 요청한 (키, nf)와 다르므로'다.

새 규칙에서 대기 소자는 요청 행, 배치 소자는 `layout_ref`를 쓴다. 이 docstring과 맞는다. 다만 배치 소자 항목의 `w_request` 내용(W 그대로인지 손가락 행인지)은 문언에 없다 → n2와 함께 적는다.

**수렴 상태 비교**: 모순은 아니다. 다만 고칠 자리가 하나 남는다.
- 엔진 사실: `converge_point.py`:114-118은 `dc_state = geometry.w_request`를 주기 판정 키로 쓰고, `for m, _w in geometry.w_request`로 (소자, W) 쌍을 푼다.
- 대기 소자 항목이 손가락 행이 되면 키가 DC 평가 입력과 같은 정밀도가 된다. WB-1에서는 DC 슬라이스가 finger_w로 정해지므로(범위 5) 물리적으로 더 맞는 쪽이다.
- 그러나 배치 소자 항목이 W로만 남으면 같은 W, 다른 분할인 두 레이아웃이 같은 DC 상태로 보인다. 그러면 거짓 주기로 NONCONVERGENT가 된다(fail-closed 쪽 오판).
- → minor n2: 수렴 DC 상태 키 = 그 평가의 입력 손가락(배치 = `layout_ref` (nf, finger_w), 대기 = 요청 행)으로 적고, `converge_point.py` 주기 키·쌍 풀기를 재작성 범위에 넣는다.

## (3) 집계 규칙 하나 -- **fail-closed 유지, 새 갈래 0**

- **봉인 1·3 노드 행 max 항에 None → 집계 None → 봉인 10행 `seal_undefined`.** 옛 'max of defined'는 빠진 항이 더 크면 문턱이 느슨해질 수 있었다. 새 규칙이 더 닫힌 쪽이다.
- **SCC min 항에 None → tol None → DC 블록 실패 `tol_v_undefined`.** 옛 '일부 None이면 min of defined'는 결과적으로 봉인 10으로 가긴 했지만 간접 논증이 필요했다. 새 규칙에서 판정 자리는 기존 둘(봉인 10행, O-240 순환 수렴)뿐이고 새 사유·갈래는 0이다. 오히려 갈래가 넷에서 셋으로 줄었다.
- 봉인 8 멤버 합도 같은 꼴이라는 것은 재작성 범위 사실 인용이다.
- **Rʳ ⚠**: 중간 회차의 None으로 최종 회차가 정의일 점을 버리는 것은 fail-closed 쪽 손실이다(받아들일 수 있음). 다만 근거 '지금 발동 0(library 9/9 Rʳ = ∅)'의 9/9는 2026-10-29 측정(`design_v1152/m4_measure/`)이다. 지금 library는 13회로다(`assets/library/*.topology.json` 14개 − 템플릿 1). → minor n3.

## (4) 결정 간 모순

| 결정 | 판정 |
|---|---|
| A-123 (2) '빈 열' 철회 | 위임 결정을 위임으로 철회했다. 근거(실현 평가 R-3과 모순)가 맞고 '원래 취지와 다름'으로 표지했다 |
| A-62 D5 | 정합. 레이아웃 뒤도 입력 손가락이면 `finger_slice` 0이다 -- D5의 일반화 |
| O-242 | 정합. 판정 자리 둘(봉인 10행 `seal_undefined`, SCC `tol_v_undefined`)은 그대로다. 집계 규칙은 O-242 바탕('정의 항이 없으면 값을 내지 않음')과 같고, 중점 결측 시 적재 거부는 질문 대기로 바꾸지 않았다 |
| O-244 | 무관·정합(원 넷 집합 유지) |
| O-240 | 정합(tol_V 용도 자리 불변) |
| O-200 | 정합(물리 경계를 tol로 정하지 않음, None = 정의 불능) |
| DEC-91 (2)(3)·Q6 | 바꾸지 않음, 질문 대기 표지 |
| **LY3**(`W_requests[{device, W_new, reason}]`, P:1108) | **범위 7 (a)의 '레이아웃이 정한 요청 (nf, finger_w)'와 정의 공백 → M-1** |

## (5) 낡은 문언 grep

`부류 셋`·`geometry_device_class`·`min of defined`·`정의된 셀`·`빈 열`·`봉인 3·4`를 계획·D40·WB-1 spec·interface에서 grep했다. 남은 것은 모두 낡은 규칙이 아니다:
- '효력 없음'·'지운 것'·'정의 0 grep'·'옛 …' 인용: interface:155, spec:98·147, D40:1216, P:2500 완료 (10) (a).
- 부정문 '정의된 셀만으로 min을 내지 않는다': D40:1212.

spec:146(넷째 개정 재작성 범위 행)은 helper를 적고 있지만, 바로 아래 :147이 '위 두 행 가운데 `geometry_device_class` … 만들지 않는다(효력 없음)'로 무효를 표지했다. **낡은 규칙 문언 0.**

## (6) 원칙 25

규칙 문언 위반은 0이다. 경위·점검·옛 문언은 history v6.38.24에 있다. 계획 안의 '정적 실측, 점검 기록 2.2'와 'library 9/9'는 근거 인용 한 마디라 서술이 아니다.

## Major

- **M-1 -- 대기 소자의 입력 손가락 '레이아웃이 정한 요청 (nf, finger_w)'가 계획에 정의돼 있지 않음**
  - 범위 7 (a)·범위 5 W′ 문장은 대기 소자 입력을 '레이아웃이 정한 요청 (nf, finger_w)를 참조로 받는다'고 정했다.
    - 근거: '요청 기하는 r = 0이라 다른 슬라이스도 r = 0이면 동률 규칙이 다른 (m, w_s)를 고를 수 있어' `finger_slice` 재호출을 금지한다.
    - 귀결: `slice_of_finger(finger_w)`, `dc_finger` = (nf, finger_w, 0).
  - 그러나 계획의 레이아웃 출력 정의 LY3(P:1108)은 `W_requests[{device, W_new, reason}]`, 즉 W만 돌려준다. 요청 손가락(nf, finger_w)과 'finger_w = 슬라이스 폭'이라는 조건이 없다.
  - as-built 레이아웃은 그 값을 갖고 있다(`layout/CONTRACT.md`:325-326 `WRequest(이름, W_need(키*), W_new, …)`, step `w_request` finger_w = W_new/n, nf = n). 그래도 원칙 8에 따라 as-built는 근거가 아니다.
  - 계획 문언만으로 구현하면 두 길밖에 없다. 손가락을 다시 유도하거나(계획이 금지한 꼴), 정의 없는 값을 읽게 된다. 즉 규칙끼리 서로를 만족할 수 없다.
  - **고칠 방법**:
    - LY3의 W_request 레코드에 요청 손가락을 정의로 더한다: `{device, W_new, nf, finger_w, reason}`. 조건은 finger_w = 그 요청의 슬라이스 폭(LY2 PDK 특성화 폭), W_new = nf·finger_w, 물리 근거는 '요청은 정합 패턴이 요구한 nf와 슬라이스에서 나온다'(LY5 (i)(ii)).
    - 범위 7 (a)·범위 5는 그 정의를 인용하게 한다. 요청 finger_w가 슬라이스가 아니면 `slice_missing`(fail-closed)이라는 한 줄도 둔다.
    - 이 일은 결정을 바꾸지 않는 정의 보충이므로 위임으로 처리할 수 있다. LY3의 'W를 조용히 바꾸지 않는다' 취지는 그대로다.

## minor

- **n1**: 범위 7 (a)에 정의 축 한 줄을 넣는다: '`dc_finger` = 그 평가 DC 해가 쓴 손가락(S2 `dc`), `layout_ref` = 레이아웃 실현 확산 기하(S2 `layout`) -- 배치 소자에서 (m, w_f) 투영이 같아도 다른 정의, 같은 목적으로 둘을 읽는 소비자 0'(graph 규칙 3).
- **n2**: 수렴 DC 상태 키(`converge_point.py`:114-118 `dc_state = geometry.w_request`, 쌍 풀기 `for m, _w`)를 재작성 범위에 넣는다. 키 = 그 평가 입력 손가락(배치 = `layout_ref` (nf, finger_w), 대기 = 요청 행)으로 정한다. 배치 소자 `w_request` 항목 내용도 적는다. 그렇지 않으면 같은 W·다른 분할이 거짓 주기로 NONCONVERGENT가 된다(fail-closed 쪽 오판).
- **n3**: Rʳ ⚠ '지금 발동 0(library 9/9 Rʳ = ∅)'는 2026-10-29 측정 9회로 기준이다. 지금 library는 13회로이므로 '9/13 측정, 4회로 미측정(LA-1 측정 시점)'으로 고친다(N3.6 표 10행·LM-1e 3 (b)).
- **n4**: history '하지 않은 것'의 '(다) 실행 도달 n/N 측정(LA-1 측정 시점)'은 (다) 갈래를 지운 뒤라 대상이 바뀌었다. 'MOD8 경로에서 배치도 요청도 아닌 소자 0(`realized_finger_missing` 발동 0)'의 실행 확인으로 문언을 맞춘다.

## 재지 않은 것(통과로 세지 않음)

(나) 옛 pick ≠ 요청 기하 발생 n/N, Rʳ 4회로, 거짓 주기 발생 빈도, LY3 요청 레코드의 finger_w가 언제나 슬라이스 폭인지(as-built 밖 PDK 격자 요청 꼴).

---

## 재판정 (커밋 `94b89e45`, 2026-11-06)

- 대상: `31dda995..94b89e45`(plan·history·D40·design history·WB-1 spec, 21+/11−). worktree는 깨끗했다.
- 방법은 앞과 같다(읽기만). 레이아웃 쪽 writer·소비자는 WB-1 code 브랜치를 재작성 범위로 인용했다.

### 결론: **Major 0.** M-1·n1~n4는 해소됐다. 남은 minor는 2건(u1·u2)이고, 둘 다 왕복 없이 card 착수 때 처리하면 된다.

### M-1 -- **해소**

- LY3(P:1108)가 `W_requests[{device, W_new, nf, finger_w, reason}]`로 바뀌었다. 조건은 finger_w = 그 요청의 슬라이스 폭(LY2 PDK 특성화 폭), W_new = nf·finger_w, 근거는 LY5 (i)(ii)다.
- 범위 5·7 (a)와 D40 §3.7-A 6이 이 정의를 인용한다. '슬라이스가 아니면 `slice_missing`'(fail-closed)도 들어갔다.
- history 둘째 커밋은 옛 문언 둘을 인용하고 '정의 보충, 결정 변경 아님'으로 표지했다.
- **LY 규칙·결정과의 대조**:

| 대상 | 판정 |
|---|---|
| LY1 (ID, VGS, L) 보존·`W_need(fw) = ID / J_slice` | 정합. 요청의 finger_w가 슬라이스라 J_slice가 정의되고, 실현 W = nf·finger_w다 |
| LY2(finger_w는 PDK 특성화 폭 DC 슬라이스만) | 정합. 요청 finger_w = 슬라이스 폭과 같은 조건 |
| LY3 'W를 조용히 바꾸지 않음'·K_max·NONCONVERGENT | 불변 |
| LY5 (i)(ii)(nf 조정 → W_request) | 근거로 인용, 정합 |
| LY7(W_request 유무와 관계없이 재평가) | 정합. 배치 소자를 `w_request`에서 빼도 `layout_ref`로 재평가가 그대로 일어난다 |
| LY8(SPICE 기하 = 수렴 스냅샷 (finger_w, nf, 확산)) | 무관·정합 |
| O-186 (L2) VGS 보존, gm 이동은 DEC-89 (2) 재평가가 판정 | 정합(보존량·판정 자리 불변) |
| DEC-89 (1)(2) | 정합(보존량·실현 기하 재평가 불변) |
| D40:1377 'cc_nf 그룹 요청은 요청한 (폭 키, nf)로 평가' | 정합(기존 design 문언과 같은 뜻이 계획 정의로 올라감) |

- **레이아웃 쪽 writer**(재작성 범위 사실, `role/code/20261104-wb1`):
  - `layout/contract_output.py`:110 `WRequest(device, W_old_m, W_new_m, reason, group)`에는 nf·finger_w 칸이 없다.
  - 생산 자리는 셋이다: `layout/pattern_select.py`:229(`cc_nf`, W_new = n·키*·격자), `layout/finger_geometry.py`:78(`finger_quantization`, 후보 실현 W), `layout/outputs.py`:59(`no_usable_slice`, W_new = W_old).
  - 앞의 둘은 (nf, 키*) 또는 (nf, 후보 키)가 생산 자리에서 정해져 있어 새 정의를 채울 수 있다. 셋째는 아래 u1.
  - spec 재작성 범위 행은 '레이아웃 요청 레코드(계획 LY3 …)'로만 적혀 있다 → u2.

### n2 수렴 키 -- **해소, 주기 판정·NONCONVERGENT 정의와 맞음**

- 수렴 DC 상태 키 = 그 평가의 입력 손가락이다(배치 = `layout_ref` (nf, finger_w) 투영, 대기 = 요청 행). 배치 소자는 `w_request`에 두지 않는다(정본 = `layout_ref`). 재작성 범위는 `converge_point.py:114-118`·`realized_geometry.py`다.
- 주기 판정의 전제는 '다음 레이아웃은 평가 점의 DC 상태만 읽는 결정론적 사상'이다(as-built `convergence/CONTRACT.md`:113). 평가 점의 DC 해는 θ 고정 아래 그 평가의 입력 손가락으로 정해진다(WB-1 범위 5: finger_w가 슬라이스를 정함). 그러므로 키 = 입력 손가락이 그 사상의 입력과 같다.
  - 진짜 주기는 그대로 잡는다.
  - 옛 W 키의 거짓 주기(같은 W·다른 분할)는 사라진다.
  - '확산 기하는 출력이라 키에 넣지 않는다'와도 맞다. 키는 (nf, finger_w) 투영뿐이고, CONVERGED 판정(`geometry == previous_geometry`)은 확산 포함 전체 비교 그대로다.
- NONCONVERGENT 정의(LY3·N3.6 K_max 상한)는 불변이고 상한이 반복을 끝낸다(fail-closed).
- 부수 변화: NONCONVERGENT 기록의 `devices`(as-built `w_request` 소자 목록)가 대기 소자만이 된다. u2에서 함께 적는다.

### n1·n3·n4 -- **해소**

- n1: 범위 7 (a)의 '정의 축(graph 규칙 3)' 문장이 옛 ⚠ 문장을 대체했다.
- n3: N3.6 표 10행·LM-1e 3 (b)·D40 §3.7-A 2가 '9/13 측정(2026-10-29), 4회로 미측정(LA-1 측정 시점)'으로 바뀌었다.
- n4: history '하지 않은 것'의 문언을 맞췄다.

### 새 결함(minor)

- **u1 -- `no_usable_slice` 요청에는 새 LY3 레코드의 finger_w가 없다**
  - 쓸 수 있는 슬라이스가 하나도 없는 소자에도 as-built는 `WRequest(이름, W_m, W_m, "no_usable_slice", None)`를 낸다(`layout/outputs.py`:59, `layout/CONTRACT.md`:478).
  - 새 정의 'finger_w = 그 요청의 슬라이스 폭'이 성립하지 않는다. '슬라이스가 아니면 `slice_missing`'은 값이 있을 때의 문장이라, 값이 아예 없는 꼴을 덮지 못한다.
  - 고칠 방법: LY3에 한 줄을 더한다. 'nf·finger_w가 정의되지 않는 요청(쓸 수 있는 슬라이스 없음)은 손가락 칸 = 정의 불능이다. 그 소자는 배치되지 않으므로 MOD8은 재평가 전에 멈춘다(`unplaced` → STATUS_UNPLACEABLE, fail-closed). 재평가 입력에 닿으면 `realized_finger_missing`.' 또는 이 꼴을 W_request가 아닌 배치 불능 기록으로 옮긴다.
- **u2 -- LY3 레코드 변경의 writer·schema·소비자 자리를 재작성 범위에 이름으로 적기**
  - 계획 P:1119('스키마 세부는 MOD7 design')에 따라 MOD7 출력 스키마의 `WRequest` 칸(nf, finger_w)을 design에 적는다.
  - WB-1 spec 재작성 범위 행에 다음을 이름으로 적는다:
    - 생산 셋: `pattern_select.py:229`·`finger_geometry.py:78`·`outputs.py:59`.
    - 운반: `convergence/convergence_values.py` `Placement`·실효 배치 → `realized_geometry`.
    - 소비: `converge_point.py` 주기 키·NONCONVERGENT `devices`.
  - 그래야 '정의 1곳·writer 1곳' grep 완료 조건을 판정자가 확인할 수 있다.

### 재지 않은 것(통과로 세지 않음)

앞 절과 같다. 여기에 더해 `no_usable_slice` 요청이 MOD8 재평가 입력까지 닿는 실경로가 있는지, 키 변경 뒤 주기 판정 빈도 변화.
