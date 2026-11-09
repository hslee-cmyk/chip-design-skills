# D0a·D0b 착수 준비 독립 검토 -- 2026-10-02

검토자는 작성자가 아니다. 기준 gate는 `master` `4a286f0`이고 시작과 끝이 같다.
실제 저장소는 `git -C`로 읽기만 했다. HEAD·`gate/master`·reflog 첫 줄은 `4a286f0`이고, `status --porcelain` 37줄 md5 `dcc7b56b…`도 시작과 같다. 역할 브랜치 3개(card 35)는 검토 전부터 있었다.
스크래치는 `C:/g268`만 썼다.
- 작업 트리에서 `git clone -c core.autocrlf=false --no-local --no-hardlinks`로 복제했다.
- origin을 지우고 빈 hooksPath를 두었으며, TMP/TEMP는 `C:/g268/tmp`로 잡았다.
- 모래상자 bare gate `C:/g268/gate.git`를 만들고, `gate_config.json`의 `gate_path`를 그쪽으로 바꾼 커밋을 사슬 맨 앞에 두었다.
- 끝에 `C:/g268`을 지웠다.

작성자 키트는 사슬을 만드는 데만 썼다: FU 대역 `p3fq_kit/fu_standin.py`, G1 시제품 `g1_kit/install_proto.py` 13:24판, [D-11] 한 줄 `p3fq_kit/variant.py qtok`, 열 재생성 대역 `regen_registry.py`·`hold_swap.py`.
판정 근거는 내가 쓴 것들이다.
- test 대역: D0a 6단계, D0b 다섯 test. 기대값은 card 문장에서 손으로 정했다.
- AST 스캔 스크립트.
- 거부 입력 편집기.

## 판정 요약

| card | 판정 | B | S | minor |
|---|---|---|---|---|
| D0a `20260930-p3-move-plan-tool` | **착수 가능**(선행 병합 뒤, S 2건은 착수 전에 보완 권고) | 0 | 2 | 5 |
| D0b `20260930-p3-registry-dest` | **착수 가능**(S1 런처 캐시 결함은 착수 전에 고칠 것) | 0 | 1 | 6 |

## 모의 사슬(모래상자)

`4a286f0`에서 시작해 아래 순서로 쌓았다.
1. `f420603`: 모래상자 gate 경로.
2. `81233ef` + `b9d1ff8`: [D-11] 문서 커밋과 승인 기록.
   - `merge_gate.py diff-hash`가 `441b80e1…`로 나왔다. 기록 초안의 사전값과 같다. `parse-approval`도 통과했다.
3. B34·b26pre·backfill: 판정 기록 대역만 넣었다(코드 없음).
4. `3202b27`: B26-1 최소 대역 + 기록. SD에 frozen dataclass `RailDeclaration`과 `rail_declaration(topology)`를 넣고, `load_topology` meta에 `"rails"`를 더했다.
5. B33·card 35: 기록 대역.
6. `9bd700d`: G1 시제품 + 기록.
7. `de68e2d`: FU 대역 + 기록 = **D0a base**.
8. D0a S `0b438fa` → T(내 test) → K(작성자 `p3kit_m1/move_plan_sim.py` 사본, 문장 키 기본값만 `names`) → ff 병합 + D0a 기록 `df43a80` = **D0b base**.
9. D0b S `2931e4c` → T → K(regen + `보류` 9칸).

한계가 있다. B34·backfill·B26-1의 실제 코드 변화(시그니처의 `rails` 주석, grammar 함수 4개)는 모의하지 않았다. 아래 수치는 이 대역 위의 관찰이다.

---

## D0a

### S

**D0a-S1. auditor 브리프 3.1의 oracle 대조 목록이 UD-6 단계를 빠뜨렸다.**
- `d0a_briefs.md` 179행은 필수 단계를 "**18개 이름**(v6 4·v7 1·v8.4 10·conf 1·r1 2)"으로 적었다.
- card 'oracle' 절에는 UD-6 `reg-first-token`이 더해져 19개다. 1절 test-author 브리프는 19로 맞게 적었다.
- 그대로 두면 순서 3 auditor가 첫 토큰 읽기 단계의 유무를 확인하지 않는다. 이 단계는 계약 2의 '모든 토큰' 오구현을 잡는 유일한 합성 단계다.
- 고칠 것: 179행을 "19개(… + UD-6 1)"로 바꾼다. 122행 '단계 18개'도 같이 고친다.

**D0a-S2. 착수 0단계가 실제 트리의 가장자리 (e1)·(e4)를 미리 보지 않는다.**
- 계약 1·2(r1)는 다음 경우 `plan` exit 2라고 정한다.
  - (e1) 한 파일 안에 단위 키가 중복된다.
  - (e4) 레지스트리 이름이 두 파일 이상의 단위에 맞는다.
- 계약 8 (a)(V10)과 D0b S-4는 실제 병합본에서 exit ≠ 2를 요구한다.
- 지금은 0이다. 내 AST 스캔에서 `4a286f0`과 B26-1 대역 트리 모두 split 5파일의 중복 키 0, 두 파일 이상에 맞는 레지스트리 이름 0이었다. 검토 r1이 잰 `36e170e`와도 같다.
- 그러나 B34·backfill·B26-1 실제 코드는 아직 보지 못했다. 그 코드가 최상위 재바인딩(예: `try`/`except` 밖에서 같은 이름을 다시 대입)을 더하면 D0a V10에서 늦게 드러나고 D0b까지 막는다.
- 도구가 없어도 AST로 잴 수 있다. 착수 0단계에 이 스캔을 넣는다.
  - 대상: split 5파일. docstring과 import 문은 빼고, 최상위 def·class 이름과 문장 바인딩 이름 정렬 키를 센다.
  - 판단: 둘 다 0이어야 한다.

### minor
- **m1 시제품의 'r1 재구현' 표기가 사실과 다르다.** spec '작성 전 실측' UD-6 문단(334행)과 D0b 233행은 `move_plan_sim.py`를 "계약 2 v8.5 + conf + r1 재구현"이라고 적는다. 내 card 문장 기준 단계 test로 재면 r1 세 곳이 card와 다르다.
  - (e1) `X = 1`·`X = 2`에서 exit 1이 나온다. card는 exit 2다.
  - (e2) `--keep` 함수 하나만 부르는 `h`가 `tool.py` A-5로 배정된다. card는 `unassigned`다.
  - '배정 없는 출처': `mod_imports["mk.py"]`에 `from src import f`가 나온다. card는 항목 없음이다.
  - `reg-first-token`·`a1-conflict`·`lift-a4`(exit 1, `reg_mismatch` 1)는 card와 같았다.
  - 실제 트리 관찰 수치는 영향이 없다. 실제 트리에는 위 경우가 0이다.
  - 그러나 이 시제품을 test 사전 dry run의 '옛 코드'나 기준 구현으로 쓰면 card대로 쓴 test가 FAIL한다. 표기를 'v8.5 + conf(r1 미반영)'로 고친다.
- **m2 브리프 머리가 낡았다.** `d0a_briefs.md` 머리의 '기준 `36e170e`'와 0.5-2 "`install_proto.py`(`5790433c…`)는 설치가 멈춘다"는 지금 사정과 다르다. 13:24판(`p3_ud6_runbook` §6)은 `4a286f0`에 그대로 설치됐다(내 사슬 `9bd700d`, "installed 4"). 단, card 35가 병합되어 `mutate_changed.py`가 바뀌면 앵커를 다시 봐야 한다.
- **m3 `d0a_launch.sh`의 선행 목록이 card 35를 보지 않는다.** `PREDS`에 V3 범위 정책 card(`20260930-v3-changed-stmt-scope`)가 없다. 이 card는 G1 base의 전제(design §5.5)다. 지금은 G1 기록만으로 간접 확인한다.
- **m4 `check` 계약은 어떤 검토도 독립 실행하지 않았다.** 계약 4의 발견 11종(r1 검토도 '재구현하지 않았다')이 해당된다. 첫 실행은 test-author 단계가 된다. 막는 결함은 아니지만, 순서 3 auditor가 `check` 단계(v6 `order-*`·`shim-*`, v8.4 `import-dup`)의 구성 기대를 card 문장과 줄 단위로 대조하는 일이 더 무겁다는 점을 브리프에 한 줄 적는다.
- **m5 V4 (3) 규칙.** 내 대역 test는 `if`/`for` 안에만 assert를 둔 함수에서 V4 (3) FAIL이 났다. 그 밖의 판정 문장 26개는 전부 NO-SUBJECT였다. 브리프 1절 7항 "if·try 밖 assert ≥ 1"이 이를 막는다. 두 갈래 단계(`reg-first-token` 등)를 쓰는 test-author에게 그 문장이 특히 중요하다고 적어 두면 재시도를 줄인다.

### 확인된 것(재현)
- **`d0a_launch.sh`(모래상자)**
  - measured 앵커가 없으면 `conds`는 조건 6을 '미충족'으로 내고 exit 3이다. `pre`도 같은 경로로 멈춘다.
  - 앵커 `de68e2d`를 넣은 사본에서는 `local`(pre → card → final)이 통과했다.
    - 조건 1~7 모두 0이다(조건 4는 `SourceIndex.tree` 등 G1 공개 표면).
    - `parse_spec_card`는 ('3', red-green, no, [`20260930-30-module-split-design`], [], 11)이다.
    - interface card는 '기존 함수 0개'이고 신규는 `move_plan.*`·`move_plan.main`이다.
    - 커밋 `0b438fa`는 spec과 interface 두 파일이고 초안과 바이트가 같다.
  - push 명령은 출력만 한다. `after-push`는 통과하고 test worktree 명령과 4절 순서를 출력한다.
    - 그 출력에 순서 3 '커밋하지 않는다'와 순서 6 `log role/test/..HEAD` 빈 출력 가드가 있다.
    - 브리프 3.1·4절에도 같다.
  - 가드:
    - 옵션을 단계 뒤에 두면 exit 2.
    - `--state`가 빠지면 exit 2.
    - `--repo`에 실제 저장소 별칭(끝 `/`)을 주면 exit 2.
- **착수 0단계 명령(모래상자 base)**
  - `reachability.py`: `read_tree` 31, `iter_defs` 51, `_refs` 69, `SOURCE_GLOBS` 172, `_is_source` 175. G1 시제품 `SourceIndex` 549, `tree`·`units`·`global_names`·`binding_origin`, `moved_defs` 646.
  - `mod_table` 22, `read_section_table` 226, `_is_empty_dict` 171. 이 값은 card '작성 전 실측' 10의 168과 다른데, card 35가 아니라 G1 시제품이 `source_lint`를 바꿔서 그렇다. 착수 때 다시 재는 항목이다.
- **test-first**
  - T 단독(도구 없음): 7 failed, 전부 `AssertionError: 도구 없음`이다. 수집 오류는 0이다.
  - K(시제품): `reg-first-token`·`a1-conflict`·`lift-a4`가 PASS다.
- **V 도구(base S → K, gate 캐시 판)**
  - V3 PASS `targets []`·`mutants 0`(V3 면제 묶기 뒤 판 키 `survivor_bindings`·`exempt_ignored` 있음).
  - V5 PASS `diff_paths []`, V6 PASS `targets []`, V7 PASS `new_defs []`.
  - V4 `--interface-card` + `--module-dir tools/migrate`에서 판정 문장은 NO-SUBJECT뿐이다(위 m5 하나 제외). 브리프 3.2 기대와 같다.
- **재현 수치 / absolute drift**
  - D0a card '재현할 수치'는 '없음'이다. V10 계약 8 (a)는 exit ≠ 2만 본다.
  - 그래서 FU-B1 모양의 절대값 위험이 없다.
  - 작성 전 실측의 줄 번호는 `MEAS_PATHS`(tools/gates·계획서·레지스트리·tooling)로 조건 6이 다시 재게 한다.

---

## D0b

### S

**D0b-S1. `d0b_launch.sh` S-7이 초안 표가 바뀌어도 낡은 판정을 그대로 쓴다(재현).**
- `plan_sum`(208~210행)은 `<상태>.plan.<sha>.json.sum.json`이 있으면 다시 계산하지 않는다(`[ -s "$out.sum.json" ] && return 0`).
- 그런데 이 요약에는 **초안에서 읽은** (d)-1 표본 대조(`samples`·`sample_mismatch`)가 들어 있다. 키는 gate sha뿐이고 초안 내용은 키에 없다.
- `pre`는 상태 파일만 지우고 plan 캐시는 남긴다(448행).
- 모래상자 재현:
  - 정상 초안으로 `conds`를 돌렸다(gate `2931e4c`, 캐시 생성, S-7 충족).
  - 그 뒤 초안 사본의 `GmIdLUT` 기대를 `theta_search`로 바꿔 다시 `conds`를 돌렸다.
  - 결과는 **S-7 '충족 -- 표본 28개 모두 plan mod 줄기 = 기대'**였다.
- 영향:
  - S-7은 '표를 고친 spec card가 test-author 전에'를 지키는 착수 조건이다. 표를 고친 뒤 같은 판에서 다시 재면, 고친 것이 틀려도 통과한다.
  - 반대로 처음 미충족을 낸 뒤 표를 맞게 고쳐도 계속 미충족이다(fail-closed 쪽).
  - 틀린 표는 결국 green 단계의 T-E가 잡는다. 하지만 그때는 code-author dispute가 생겨 재시도가 된다.
- 고칠 것(둘 중 하나):
  - (가) 요약 캐시 키에 초안 sha256을 넣는다.
  - (나) `plan` JSON만 캐시하고 표본 대조는 매번 다시 계산한다.

### minor
- **m1 "커밋 대기"라는 낡은 문장이 남아 있다.** 승인 기록 `20260930-30-module-split-design`은 `36e170e`에 커밋되었다. 그런데 spec 11행·160행·218행과 브리프 19행(S-1)·189행(4절)은 아직 '커밋 대기'라고 적는다.
- **m2 head 단언(review_d0a m6)이 반영되지 않았다.** 계약 11 (b)는 "도구가 없거나 exit 2이면 판정 목록 단언 전에 FAIL"이라고 적는다.
  - 오류 출력도 첫 줄이 JSON이고 `"tool": "move_plan"`이 있다. 그래서 머리 단언을 통과하고, 다음 `o["conflicts"]`에서 `KeyError`가 난다.
  - '허용 예외 `AssertionError`만'(실측 14)과 맞지 않는다.
  - 내 대역 test는 `verdict != "ERROR"`를 더해 썼다. 계약 11 (b)와 브리프 1절 2항에 한 구절을 더한다.
- **m3 R-A2의 T-E를 두고 spec과 브리프가 갈린다.** spec 표(180행)는 T-E 표본 `compute_metric`를 "결정됨"으로 적는다. 브리프 3.2 V10 ⑥(181행)은 "R-A2의 T-E는 D0a 구현 의존이라 판정에 쓰지 않는다"고 적는다. conf 이후에는 정해진 동작이므로 브리프 문장을 지운다. 내 측정에서 R-A2는 T-A(`conflicts`)와 T-E가 FAIL하고 T-B·T-C·T-D는 PASS였다.
- **m4 계약 12 문장과 `MP_ARGS`가 충돌해 보인다.** 계약 12는 "test 소스에 `library` 없음"이라고 적지만, `MP_ARGS`의 `topology_library.py`가 그 부분 문자열을 담는다. 같은 계약의 'MP_ARGS 인자 리터럴로만'이 예외로 읽히지만, auditor가 D0a처럼 `git grep library`로 재면 걸린다. "MP_ARGS 줄 밖에서 0"으로 적는다.
- **m5 브리프 4절 순서와 런처 `PREDS`가 다르다.** 4절은 "T0·FU·G1 → D0a"라고 적는데, `PREDS`는 T0를 보지 않는다. spec 실측 13은 "T0가 D0b 뒤면"이라는 갈래를 허용한다. 하나로 맞춘다.
- **m6 freeze 실패 시 ERR 표지가 함께 찍힌다.** D0b 기록이 없을 때 `freeze`가 exit 1로 멈추면서 `[중단] …:560: return 1`도 찍힌다. 판정 결과인데 오류처럼 보인다. `conds`처럼 `trap - ERR`를 넣는다.

### 확인된 것(재현)
- **`d0b_launch.sh --iso /c/g268/iso1 conds`(D0b base `df43a80`, 앵커 없음)**
  - S-1~S-5·S-7 충족, S-6(sandbox 역할 브랜치)·measured 미충족, exit 3.
  - S-1은 [D-11] 기록(parse-approval)과 계획 MOD1 행 `D11TOK`을 함께 본다.
  - plan 38초 exit 1.
    - 배정 405(대역 B26-1 두 단위 +2), A-1 62·A-2 39·A-4 235·A-5 57·A-6 7·A-K 2·A-7 2·A-3 1.
    - 여섯 목록 0, MOD7 밖 0, `reg_mismatch` 80.
  - 표본 **28개**(B26-1 둘 포함) 모두 기대와 같다. `RailDeclaration`은 A-2 `topology_authoring`이다.
  - `_QUERY_CACHE_MAX` 규칙은 A-1이다.
- **앵커 `df43a80` 사본에서 `local` 통과**
  - 조건 1~8 모두 0이다.
  - `parse_spec_card` approval은 두 줄이고 순서가 같다.
  - interface card는 두 표 모두 빈 표다.
  - 커밋 `2931e4c`. `after-push`는 통과하고 동결 대기열과 test worktree 명령을 출력한다.
  - `freeze`는 D0b 기록이 없어 거부했다.
  - 가드: 옵션을 단계 뒤에 두면 exit 2, `--iso`가 `/c/g<n>/` 밖이면 exit 2.
- **test-first, T 단독(base S)**: 다섯 test가 **각자 고유 단언에서** `AssertionError`로 FAIL했다.
  - T-A `reg_mismatch` 80.
  - T-B 칸 불일치 225.
  - T-C 머리에 `근거 규칙` 없음.
  - T-D `보류(Phase 3)` 9.
  - T-E 표본 23.
  - spec 계약 11 표와 실측 UD-6 수치가 그대로다. 앞쪽(base에서 참인) 단언에서 난 FAIL은 0이다.
- **K(regen 354행 + `보류` 9칸, diff 409/409)**
  - 새 test 5와 `test_reg_check*`·`test_df23_inventory`를 합쳐 **215 passed**다.
  - 전체 PT3 결과: K 1056 passed·15 xfailed, base 1051 passed·15 xfailed. 차이는 새 test 5개뿐이다.
  - 양쪽 3 failed는 같고, 모래상자에 남은 내 D0a 대역 test가 r1 미반영 시제품과 어긋난 것이다(D0a m1, 판정 무관).
- **V 도구(S → K)**
  - V3 PASS `targets []`, V5 PASS `diff_paths []`, V6 PASS `targets []`, V7 PASS `new_defs []`.
  - V4 `--interface-card`만이면 **ERROR '피검 심볼이 없다'**(exit 2)이고, `--module-dir tools/migrate --subject move_plan:main`이면 PASS(NO-SUBJECT뿐)다.
  - 브리프 3.2와 같다.
- **거부 입력(K 사본에 하나씩 커밋, 내 대역 test, 7/14)**: 모두 spec '측정' 열의 test별 첫 FAIL과 같다.

  | 입력 | 결과 |
  |---|---|
  | R-A7 | T-A·T-B·T-E가 첫 줄 JSON 단언에서 FAIL, T-C는 머리 단언 통과 뒤 같은 단언에서 FAIL, T-D PASS |
  | R-B2 | T-B 칸·T-E만 FAIL(T-A PASS) |
  | R-B3 | T-B·T-E |
  | R-E1 | T-E만 |
  | R-C1 | T-C 머리만 |
  | R-C2 | T-C 집합만 |
  | R-A2 | T-A `conflicts`·T-E |

- **(d)-1 행 분류**: × 넷(`_topology_ref_relpath`·`check_topology_name_uniqueness`·`RailDeclaration`·`rail_declaration`)은 레지스트리에 행이 없다. B26-1 계약 11의 레지스트리 수정은 §2 `개념|정본` 표(함수 표 아님)와 §6 책임 문장이라 대상 행을 바꾸지 않는다.
- **절대값 drift**
  - spec의 80·225·9·23·354·15 등은 모두 '관찰'로 표기되어 있고, '재현할 수치'는 "D0b base에서 처음 계산"이다.
  - auditor 3.1은 red의 **위치**를 보고 개수는 보지 않는다.
  - 조건 8(`MEAS_PATHS` = plan 입력 전부 + contracts)이 D0a 병합 뒤 재측정을 강제한다.
  - 조건 5·7이 판정 목록과 표본을 실제 도구로 다시 본다(단 S1 캐시 결함).
  - 그래서 FU-B1 모양(V10이 낡은 절대값과 대조)의 위험은 없다.
- **[D-11] 승인 기록**
  - 모래상자 문서 커밋 뒤 `target`이 사전값 `441b80e1…`와 같다(부모 계획서 blob이 `4a286f0` 판일 때).
  - G1·F1 문서 커밋이 먼저 들어가 계획서 blob이 바뀌면 다시 계산해야 한다. runbook §1이 이미 이렇게 적었다.

## 선행 card 병합 뒤 착수를 막는 것(정리)
1. **D0b-S1**: S-7 요약 캐시가 초안을 키에 넣지 않는다. 표를 고친 뒤 재확인이 무력하므로 착수 전에 고친다.
2. **D0a-S1**: auditor 순서 3의 단계 목록이 18개다. `reg-first-token`을 더해 19개로 만든다.
3. **D0a-S2**: 착수 0단계에 (e1)·(e4) AST 스캔을 넣는다. B34·backfill·B26-1 실제 코드 위에서 0인지 본다(지금 대역 위에서는 0).
4. 두 card 모두 measured 앵커가 지금 초안에 없다. 의도대로 `pre`가 조건 6(D0a)·조건 8(D0b)로 거부하는 것을 모래상자에서 확인했다. 착수 0단계 재측정 뒤 앵커 문장을 더한다.
5. 순서 밖 전제: [D-11] 문서 커밋·승인 기록은 card 35 정리(역할 브랜치 0) 뒤 단독 push다. D0b S-1이 이 둘을 함께 본다.
