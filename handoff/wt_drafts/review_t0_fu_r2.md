# T0·FU 초안 r2t+ 독립 재검토 -- 2026-10-06

검토자는 작성자가 아니다. 기준은 gate `master` `fd4ef8c`다.
대상은 아래와 같다.
- `draft_p3_t0.spec.md`, `t0_briefs.md`, `t0_launch.sh`
- `p3kit_t0/`(`step0_v4.sh`, `approval_…draft.md`, `v_tools.sh` CRLF 수정 포함)
- `approval_20261002-p3-t0-v4-s009-exempt.md`
- `draft_p3_fu.spec.md`, `fu_briefs.md`, `fu_launch.sh`, `p3kit_fu/`

앞선 검토는 `review_t0_fu.md`(B2·S4·minor 9)와 `review_t0_v4.md`이다.

## 실제 저장소와 모래상자

**실제 저장소**는 `git -C`로 읽기만 했다.
- 검토 중 다른 주체가 커밋해 master가 `fd4ef8c`에서 `b4734cd`(`.ai/context.md` +22)를 거쳐 `7243f28`로 움직였다. B34 문서 커밋 2개와 B34 역할 브랜치·worktree 3개가 생겼다. 내가 한 것이 아니다.
- `status --porcelain`은 38줄로 시작과 같다.

**모래상자**는 `/c/g284`만 썼다.
- `-c core.autocrlf=false --no-local`로 복제했고, origin을 지웠다.
- 빈 hooksPath와 모래상자 bare gate를 썼다. `gate_config.json`의 `gate_path`는 모래상자로 바꿨다.
- TMP/TEMP는 `/c/g284/tmp`였다.
- 끝에 `/c/g284`를 지웠다. redteam은 돌리지 않았다(`C:\Windows\Temp\gmid-redteam` 비어 있음).

**모의 선행**: `fd4ef8c`(card 35 실제 V3 도구 포함) 위에 커밋 두 개를 얹었다. 이것이 B0 `6754275`다.
- 첫 커밋은 `gate_path`를 모래상자로 바꿨다.
- 둘째 커밋은 B34·b26pre·backfill·B26-1·B33 판정 기록 자리표시자(V1~V10 PASS)와 `test_b26_rail_accessor.py` 자리표시자를 넣었다.

## 판정 요약

| card | 판정 | B | S | minor |
|---|---|---|---|---|
| T0 `20260930-p3-tests-location-free` | **착수 가능**(S 2 반영 권장) | 0 | 2 | 5 |
| FU `20261002-p3-future-annotations` | **착수 전 B1 수정 필요**(한 줄 고치기) | 1 | 0 | 3 |

## 앞선 지적의 해소

- **T0-B1(V4)**: 해소됐다.
  - 결정 면제 승인 기록, spec [T0-V4], `step0_v4.sh`, launch 조건 11, 브리프 0단계 (아)·3.2 V4 행이 모두 들어갔다.
  - `v_tools.sh`는 `\r`을 떼고 개수를 출력하며, CR이 남으면 멈춘다.
- **T0-S1**: 해소됐다. 계약 4 범위를 추적 `.py`로 바꿨다. `fd4ef8c`에서도 design 30 577·611·1183행 3줄과 ts6 다섯 줄 그대로다.
- **T0-S2**: 해소됐다. 1절 입력이 1~11이고, 모양 요구 8이 생겼고, 자기 실행에 unit 3파일이 들어갔다.
- **T0-S3**: 해소됐다. 0단계 (사)와 kit-cmds의 `w1_lines`·`shim_import_reads`가 들어갔다.
- **T0-S4**: 해소됐다. 0단계 (자) 계약 10 dry run을 B26-1 직후, test-author 전에 둔다. 대상 파일이 아직 없으므로 스크립트가 없는 것은 타당하다.
- **T0 minor m1~m5**: 해소됐다.
  - m1~m4는 spec에 반영됐다.
  - m5는 백로그 B59(`backlog_additions.md`)로 옮겨졌다.
- **review_t0_v4**: 해소됐다. spec과 승인 기록의 줄 번호 705~709, 744행 문장, '피검 집합에 달림', '이후 card에도 적용'이 모두 반영됐다.
  - 남은 것은 브리프 표 두 곳뿐이다(아래 T0 m2).
- **FU-B1**: 해소됐다. '재현할 수치'를 A1(관계)·A2(DR·ACF·Python)·B(관찰, V10 밖)로 나눴고, `pre`가 Python 3.14.2를 확인한다.
  - 다만 A2 안에 새 결함이 하나 있다(아래 FU-B1').
- **FU m1~m3**: 해소됐다. 거부 입력 2개, e_lib blob `00fbb20f`와 LF sha `41b72d7d`(모래상자 실측 일치), S-1 충족과 249행이 반영됐다.
- **FU m4**: 환경 문제라서 조치가 필요 없다.

---

## T0

### B

없음.

### S

**T0-S1'. 이미 답을 받은 [T0-V4] 질문을 다시 올리라는 문장이 남아 있다.**
- spec 158행과 승인 기록은 "결정 완료 19:54 KST, 답 = 면제"이다. 채운 기록 `_drafts/approval_20261002-p3-t0-v4-s009-exempt.md`도 `p3kit_t0/…draft.md`와 바이트가 같다.
- 그런데 아래 세 곳은 아직 '질문을 올리고 답을 받은 뒤 draft를 채워' 흐름이다.
  - 브리프 머리 0단계 (아) 32행: "MATCH면 [T0-V4] 질문(`ask_t0_v4.md`)을 그대로 올리고, 답 뒤 … draft.md를 채워"
  - `t0_launch.sh` kit-cmds 246~247행
  - `t0_launch.sh` conds 268행: "조건 11 -- 사용자 답 [T0-V4](ask_t0_v4.md) 뒤 기록 커밋"
- 그대로 따르면 사용자에게 같은 질문을 세 번째로 올리게 된다.
- 고칠 것: "MATCH면 채운 기록 `_drafts/approval_…md`의 MATCH 자리 한 줄만 채워 Role: doc 커밋·push(질문 없음). DIFF면 늘어난 id로 질문 재작성"으로 바꾼다.

**T0-S2'. 승인 기록의 `<MATCH 결과 줄 …>` 자리표시자가 그대로 커밋되는 것을 막는 장치가 없다.**
- 모래상자에서 쟀다. 자리표시자가 남은 기록을 `merge_gate.py parse-approval`에 넣으면 **exit 0**이다.
- 그래서 `t0_launch.sh pre`·`card`의 `approval_at`(parse-approval, id, target_kind만 봄)과 조건 11이 모두 통과한다.
- 승인 기록은 gate에 한 번 올라가면 고치는 데 커밋이 하나 더 든다.
- 고칠 것: `approval_at "$H" "$C" "$EXAID" decision` 뒤에 아래 확인 한 줄을 넣는다(`pre`·`card` 두 곳).

  ```
  ! g show "$H:.ai/approvals/$EXAID.md" | grep -q '<MATCH 결과 줄'
  ```

  `판단: MATCH` 줄이 있는지도 함께 보면 더 좋다.

### minor

- **m1. 계획서 줄 번호가 밀렸다.** `fd4ef8c`에서 계획서가 602행 뒤에 2줄 늘었다(N3.12.2 쓰기 경로 두 행).
  - 그래서 spec의 "계획 N3.12.3 686행"은 이제 **688행**이고, "991행"은 **993행**이다.
  - 착수 0단계에서 rev를 갱신할 때 같이 고친다(사실 문장).
- **m2. 브리프에 낡은 줄 번호와 문장이 남아 있다.** spec은 이미 고쳤다.
  - 0.5 표 'V4 범위' 행에 "719~725행 … 702~707행"이 있고, 3.2 V4 행에 "719~725행"이 있다. 정본은 718~721행(선택)·723~726행(lint)·705~709행(read)이다.
  - 0.5 표 (iii) 행의 "744행은 스냅숏 지역 변수로 바꿔도 FAIL 1 그대로"는 review_t0_v4 (3) 이전 문장이다. W 식으로 바꾸면 V4를 통과한다.
- **m3. `t0_launch.sh` 21행 주석이 낡았다.** "test-only라 문서 패치·승인 기록 커밋 없음"이라고 적혀 있지만, 지금은 V4 면제 기록 커밋(조건 11, 스크립트 밖)이 있다.
- **m4. 승인 기록 87~88행 사이에 빈 줄이 없다.** "사용자에게 제시하지 않은 것: …" 바로 다음 줄이 `## 범위 설명`이다. 파싱에는 영향이 없다(parse-approval exit 0).
- **m5. 순서 번호가 브리프마다 다르다.** T0 브리프는 auditor 판정을 '순서 6'이라고 하고, FU 브리프는 '순서 7'이라고 한다.
  - 계획 N3.12.3 표에서는 6 = 병합 + auditor 검증·판정 기록, 7 = push다.
  - 그런데 `agents/gmid-verification-auditor.md` 본문 48~50행은 "커밋은 순서 7에서"라고 적고 머리에는 "3·6"이라고 적어, 정의 파일 자체가 섞여 있다.
  - 내용 오해는 없다. 두 브리프 모두 3.1에 '커밋하지 않는다'가 있고, 4절에 병합 전 `log role/test..HEAD` 빈 출력 가드가 있다. 그래도 한쪽으로 맞추고, 정의 파일 불일치는 백로그 한 줄로 둔다.

### 모래상자 재현(T0)

**`t0_launch.sh` 옵션 가드** -- 아래는 모두 exit 2로 거부됐다.
- 단계 뒤에 옵션을 붙인 경우(`conds --repo …`)
- `--wt`가 빠진 경우
- `--repo`에 실제 저장소 별칭(끝 `/`)을 준 경우
- `--state`에 실제 상태 파일을 준 경우
- 단계 자리에 `--draft-spec`을 둔 경우

**conds**
- 기록 커밋 전: 조건 1~10은 0, 조건 11은 128 → exit 3.
- 기록 커밋 뒤(`29a3d97`): 11/11이 0 → exit 0.

**step0_v4.sh**(격리 복제본 B0, 게이트 캐시는 B0 판):
- `test_lint(iface)`가 exit 1(FAIL)이었다. 규칙 (1) FAIL은 `test_s009` 719·744행 2건이고, UNJUDGED 78, NO-SUBJECT 242(자리표시자 rail 파일 +1)였다.
- UNJUDGED 식은 TS2 `caac910`과 78/78 같았다.
- 결과는 `판단: MATCH`다. 자리표시자 rail lint는 PASS였다.

**local**(measured 줄 `6754275`을 넣은 초안 사본):
- pre·card·final 모두 통과했다. S = `dd5910d`.
- interface card는 기존 함수 6개(rail_declaration 0 -- 자리표시자 SD에는 정의가 없다), 신규 0이다.
- `_approved_ids`는 39개이고 test_s009 id를 포함한다.

**after-push**:
- worktree 명령은 출력만 했다. `worktree list`는 master 하나였다.

**모의 T** = S + `install_t0_proto` + `install_t0_c11`. diff는 7파일이다(계약 10 대상은 자리표시자라 제외). 게이트 캐시는 S 판(card 35 V3 포함)이다.

| 확인 | 결과 |
|---|---|
| **V4, 면제 기록이 head 트리에 있음** | **PASS exit 0** -- (1) exempt 2(719·744), UNJUDGED 78, NO-SUBJECT 241, FAIL 0 |
| **V4, 기록이 없음**(T에서 기록만 지운 커밋) | **FAIL exit 1** -- (1) FAIL 2(같은 두 줄), 나머지 같음 |
| V5 | FAIL exit 1(승인 전 예정). 발견 4, `diff_paths` = contracts 3(`test_dup_w_calc`·`test_ic5`·`test_ts6_dead_probes`) -- unit 3파일은 해시 밖(spec 문장과 같음) |
| V3(card 35 도구) | PASS `targets []`·`mutants 0`·`not_targeted 0`·`targets_by_def {}` |
| V6 | PASS `targets []` |
| V7 | PASS `new_defs []` |
| PT3, 바뀐 6개 test 파일(contracts 3 + unit 3) | base·T 모두 221 passed 2 xfailed, (판정, id) 223개 같음 |

---

## FU

### B

**FU-B1'. '재현할 수치' A2의 요약 sha256 `f94f7895…`는 작성자 시제품 출력 형식에 묶인 값이다. 독립 판정기로는 재현할 수 없다.**
- spec이 서로 맞지 않는 두 가지를 요구한다.
  - 계약 3(d)와 'oracle' 절, 브리프 3절은 "auditor는 판정기(계약 1·2·3(d))를 독립으로 쓴다 -- `fu_codeobj.py`를 판정 도구로 쓰지 않는다"고 한다.
  - 그런데 A2와 브리프 3.2 V10 행은 "요약 sha256 `f94f7895…` 21줄"을 재현 대상으로 둔다.
- 이 해시는 `fu_codeobj.py dump`의 줄 형식에서만 나온다. 줄 형식은 `<파일>::<qualname[#n]> <sha256(repr(([필드값…], norm_consts, flags)))>`이다.
- 계약 3(d)는 줄 형식·직렬화·키 표기를 정하지 않는다.
- 모래상자 실측:
  - 시제품으로는 base = head = `f94f7895…`(21줄)가 재현됐다.
  - 내 독립 구현(같은 비교 필드, 다른 줄 형식)은 base = head = `e611a39c…`(21줄)였다. **관계는 같지만 절대값이 다르다.**
- 결과: auditor가 지시대로 하면 V10 A2가 숫자 불일치(FAIL 또는 재시도)로 끝난다. 아니면 시제품을 판정 도구로 쓰게 된다(작성자≠검증자 위반).
- 고칠 것(둘 중 하나):
  - (가) A2에서 `f94f7895…`를 빼고 "요약 출력 21줄, base = 병합본"만 둔다. 관계 A1의 3(d)와 같은 꼴이다.
  - (나) 계약 3(d)에 줄 형식을 바이트 수준으로 정해 독립 구현이 같은 바이트를 내게 한다.
- (가)를 권한다. 브리프 3.2 V10 행과 `fu_launch.sh` 15~17행 주석의 `f94f7895…`도 함께 고친다.

### S

없음.

### minor

- **m1. 계획서 줄 번호가 밀렸다**(T0 m1과 같은 원인). spec의 '판정 유형 근거'와 '자리'에 있는 계획 줄 번호가 이제 모두 2씩 뒤다.
  - 686행 → 688행
  - 680·686·838행 → 682·688·840행
  - 838행(V2) → 840행
  - 991행 → 993행
- **m2. 순서 번호가 계획과 다르다.** `fu_launch.sh` `print_role_cmds`·after-push와 브리프 §1·§4는 test worktree 만들기를 '순서 2'라고 한다. 계획 N3.12.3에서는 순서 1(오케스트레이터 worktree add)이다. auditor 판정 '순서 7'은 T0 m5와 같다.
  - 동작에는 영향이 없다.
- **m3. 브리프 3.2 equivalence 블록 (4)는 "auditor가 쓴 요약 스크립트"이다.** FU-B1'을 (가)로 고치면 `outputs_hash` 문장은 그대로 둘 수 있다. (나)로 고치면 형식 정의를 그 문장에서 가리키게 한다.

### A1·A2 실측(모래상자, B0 `6754275` → 두 줄 head, DR·ACF = `dd60db6` 바이트)

**A2**: 내 독립 판정기로 쟀다(`co_qualname@순번` 짝짓기, 계약 2 필드).
- 몸체 코드 객체 같음: DR 16, ACF 5. 다름 0. 한쪽에만 있는 키 0.
- `__annotate__` 차이: DR 5, ACF 4.
- 계약 1 AST(`B[:1]+[I]+B[1:]`, docstring 같음)와 diff 부분('+' 한 줄, 바이트 같음, '-' 0)은 두 파일 모두 참이다.
- 계약 5 import 관찰:
  - DR 이름 차이는 `annotations` 하나이고, 문자열화된 함수는 5개다(`_kv_table`·`assemble_report_data`·`build_topology_device_table`·`render_html_report`·`save_html_report`).
  - ACF는 4개다(`_as_set`·`_theta_evidence_for_pair`·`audit_topology`·`render_report`).
- Python은 3.14.2다.
- 이 수치들은 spec 값과 같다. 요약 sha256 절대값만 위 FU-B1'과 같다.

**A1**(관계):
- PT3 base·head 모두 1047 passed 15 xfailed, id 1062, 차이 0이다. 자리표시자 rail 파일은 `--ignore`했다. 그 파일이 import 경로 결함으로 수집 오류를 냈기 때문이다(모래상자 자리표시자 결함, card 무관).
- E-LIB JSON, E-INST 파일럿·`folded_cascode` JSON 모두 base와 head가 바이트 같다.
- 참고로 절대값은 E-LIB `1d2e3bf6…`, `raw_sha256` 파일럿 `2fc426d9…`·folded `ef3cd996…`이다. 엔진이 `dd60db6`과 같아서 B 관찰과도 같다. B26-1 실제 병합 뒤에는 바뀔 수 있다는 spec 문장이 맞다.

**fu_launch.sh**
- conds는 13/13이 0이다.
- 옵션을 단계 뒤에 붙이면 exit 2로 거부된다.
- measured 줄이 없으면 pre가 거부한다.
- local(pre·card·final)은 통과했다(S' = `a849d09`). pre는 Python 3.14.2를 확인하고 `e_inst_p3.py`가 gate에 있음을 출력한다. interface card는 두 표가 빈 행이다.
- after-push와 roles는 명령만 출력한다.
- 세 worktree를 만든 뒤 roles를 돌리면 `role/test` = S'·커밋 0이고, audit 0, code 1(code 커밋 뒤)이다.
- 병합 전 가드 `log role/test..HEAD`는 빈 출력이었다.

**병합본 게이트**(S' 판 캐시, card 35 V3):

| V | 결과 |
|---|---|
| V3 | PASS. `targets` = DR·ACF, `mutants 0`, `not_targeted 0`, `targets_by_def {}` -- spec 계약 4 '범위 정책 병합 뒤' 문장과 같다 |
| V4 | `--interface-card`만 주면 ERROR exit 2. `--subject` 둘을 주면 PASS `files []` |
| V5 | PASS `diff_paths []` |
| V6 | PASS. `findings []`(`targets` DR·ACF) |
| V7 | PASS `new_defs []` |

## 착수 전 할 일

1. **FU-B1'**: A2에서 sha256 절대값을 뺀다. spec과 브리프 V10 행, launch 주석을 함께 고친다.
2. **T0-S1'**: 0단계 (아)·kit-cmds·conds 문장을 '질문 없음, 채운 기록에 MATCH 줄만'으로 바꾼다.
3. **T0-S2'**: `pre`·`card`에 MATCH 자리표시자 거부 한 줄을 넣는다.
4. minor는 착수 0단계에서 rev를 갱신할 때 함께 고친다. 계획서 줄 번호, 브리프 표의 낡은 줄 번호, 순서 번호 통일이다.
