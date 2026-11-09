# 독립 검토: Phase 3 DoD 초안 v3 -- 오늘(2026-10-06) card 변경과의 정합성

검토 대상: `_drafts/draft_phase3_dod.md`(v3, 18:45), kit `_drafts/phase3_dod_kit/`(`n63_p3.py` 21:51 nomerge 판, `run_dod.sh` 16:07, `inputs_p3.py`·`judge_p3.py`·`p3_cards.py`).
대조: `draft_b26pre.spec.md`(attempt 2), `draft_p3_d0a.spec.md`(det5)·`d0a_determinism.md`, `draft_p3_f1.spec.md`(b1fix)·`f1_v5_carry_plan.md`, `draft_p3_f2.spec.md`(r5),
`draft_p3_m10.spec.md`·`draft_p3_t1.spec.md`·`m10_t1_open_items.md`(T1-2), `review_nomerges.md`, `user_decisions.md`, design 30·계획 at gate `master` `6c724de`(저장소 읽기 전용).
고친 파일 없음. 실행은 모래상자 `C:/g368`만(TMP/TEMP 그 아래, `cd` 없음, 끝에 삭제).

## 판정 요약

- **B(차단): 없음.**
- **S(중대): 1건** -- S1 `--no-merges` 제거(nomerge, 사용자 승인)가 kit에는 들어갔는데 브리핑 본문(§5 12행 명령, §10 필수 메모 ③)은 옛 사실을 적는다. 공식 결과 파일의 필수 문장 ③이 거짓이 된다.
- **minor: 8건**(m1~m8, 아래).
- **변경 불필요로 확인한 것**: card 목록·순서, 기대 건수(N6.3-1 58, N6.3-2 20, 5번 유형 7/3/10), E-항목의 T1 뒤 test 위치, V4 면제 id, V5 승인 수(아래 '확인만' 절).

## 0. 실측 (모래상자 `C:/g368`, 2026-10-06, kit 무수정)

`git clone --no-hardlinks --no-local -c core.longpaths=true -c core.autocrlf=false` → origin 제거 → `checkout --detach 6c724de`, `git archive 6c724de tools/gates` 캐시. `inputs_p3.py`·`n63_p3.py`만 직접 실행(guard·watch 미실행).

- design 30·계획·`tools/gates`: `git log fd4ef8c..6c724de -- <세 경로>` **0커밋** → §2 블록 sha256 5개·줄 범위, 계획 N6.2 1020행 인용 그대로 유효. design 30 §8.1 순서 `… M9 → M10 → T1 → F1 → F2`(632·653행) = `p3_cards.PHASE3` 순서.
- `inputs.json` `missing` **25**: phase 3 spec card 0장 18(backfill·B26-1·T0·FU·D0a·D0b·M1~M6·M8·M9·M10·T1·F1·F2) + `b26pre 판정 기록(20260930-b26-pre-test-strengthen)` 1 + 게이트 B33·G1 2 + B0·MPC 2 + 파일 2. (v3 §8.v3 '뒤 사정' 예고와 같음 -- 수는 그대로, b26pre 항목 종류만 바뀜.)
- `n63_p3.py`(nomerge 판): `1 PASS(n=37) | 2 FAIL(2/20, 기록 없음 1) | 3 FAIL | 4 PASS(n=2, 어긋남 0, 덮음 누락 0, 경로 밖 0) | 5 FAIL`, `merges_clean` `[]`, `obs_tools_gates` 4, 관찰 0.5 = 34·35 `PNNNNNNNNP` audit·merge True, B33·G1 없음. `review_nomerges.md` §1(old/new 같음)과 일치.
- 오늘 초안 id가 kit 정규식에 모두 정확히 1개로 맞음: M10 `20261006-p3-mod10-entry`, T1 `20261006-p3-test-relocate`, M1~M9 `20261002-p3-move-mod<n>-…`, FU `20261002-p3-future-annotations`, F1 `20261002-p3-callers-update`, F2 `20261002-p3-shim-delete`, G1 `20260930-p3-gate-move-aware`(phase 0.5), D0a·D0b·T0·B26-1·backfill·b26pre·B33. 초안 머리 `evidence_type`도 `p3_cards` design 유형과 모두 같음.
- 메인 저장소: 실행 뒤 status `--ignored` 176줄·reflog 356줄(v3 §8.v3 끝 값과 같음), HEAD = gate `master` = `6c724de`, 역할 브랜치 0.

## 1. S1 -- nomerge가 브리핑 본문에 없다

kit `n63_p3.py`는 2026-10-06 사용자 승인('[--no-merges] 빼도 됨', `user_decisions.md`; 독립 검증 `review_nomerges.md` B·S 0)으로 4번·관찰 3의 `git log`에서 `--no-merges`를 빼고 `merge_class()`(clean = 목록에서 빼고 `merges_clean`에 적기만, evil = 어긋남)를 더했다. 브리핑은 v3(18:45) 그대로라:
- §5 12행 명령이 `git log --no-merges P2D..H -- …`로 적혀 kit과 다르다.
- §10 r2 필수 메모 ③ "N6.3-4 목록은 `--no-merges`라 … evil merge는 목록에 나오지 않는다"는 이제 거짓이다(kit은 evil merge를 잡는다 -- `review_nomerges` 합성 B·B2·B3·C). auditor가 이 줄을 '필수'로 결과 파일에 옮기면 사실과 다른 기록이 남는다.
- §6 마지막 행(Phase 2 재현)과 §8.v3 n63 행은 옛 kit 실행값이다(nomerge 판도 수치 같음 -- `review_nomerges` §1, 위 §0).

**제안 수정(정확한 문안)**:

(a) §5 12행 '명령' 칸, `같은 도구: \`git log --no-merges P2D..H -- …\`` 를 다음으로 바꾼다:
> 같은 도구: `git log P2D..H -- 'skills/analog-gmid-design/assets/*.py' workspaces/run_harness.py 'skills/analog-gmid-design/assets/library/*.json' 'tools/migrate/*'`(nomerge -- `--no-merges` 없음, 2026-10-06 사용자 승인; 기본 history simplification이 남긴 merge는 `merge_class`로 가른다: 자동 병합(`merge-tree --write-tree`)과 그 경로 내용이 같으면 clean → 목록에서 빼고 `merges_clean`에 적기만, 다르면 evil(충돌 해결·부모 3개 이상 포함) → trailer와 무관하게 어긋남)

(b) §10 r2 필수 메모 ③ 전체를 다음으로 바꾼다:
> ③ "N6.3-4 목록은 `--no-merges` 없이 뽑는다(nomerge, 2026-10-06 사용자 승인). 엔진 경로 내용이 자동 병합과 다른 merge(evil -- merge에서만 바뀐 내용·충돌 해결·부모 3개 이상)는 trailer와 무관하게 어긋남이고, 자동 병합과 같은 merge(clean)는 `merges_clean`에 적기만 한다. 남는 사각(`review_nomerges` m4): 충돌을 한 부모와 TREESAME으로 해결한 merge는 기본 simplification이 그 부모만 따라가 반대편 커밋이 목록에 나오지 않는다 -- 그 내용은 H 트리에 없다. EL4(`merge_gate.py` 'M 트리 = M^2(code 끝) 트리', 1147~1148행)는 그대로 병합 내용을 막는다. merge-tree 객체는 임시 객체 디렉터리에만 쓰지만 복제본에 이미 있는 loose 객체의 mtime이 갱신될 수 있다(복제본 한정, 메인 무관 -- `review_nomerges` m3)."

(c) §6 마지막 행 '리허설' 칸 끝에 덧붙인다:
> nomerge 판 kit(2026-10-06)으로 같은 범위를 다시 재면 JSON이 `merges_clean: []` 한 키만 늘고 수치 그대로(n=31, `review_nomerges` §1 -- `C:/g353`).

(d) §7 관찰 3 끝에 덧붙인다: "(nomerge 판: `--no-merges` 없이, clean merge는 빼고 evil merge는 `merge`·`merge_only_paths` 키와 함께 적는다.)"

(e) 머리에 v4 줄(아래 m8).

## 2. minor

**m1 -- E2 ②·E6의 `findings` 종류에 `import-dup`가 빠짐.** D0a 계약 4는 `check` 발견 종류 **11개**(`import-dup` 포함, v8.4 D-30 -- design 30 §6.3 459행도 같음; D0a 단계 `allow-changed-declared` (1) "발견 11종 모두 빈 목록")이고 "종류 키는 항상 있다". design §10 E2 통과 기준은 "`findings`의 **모든** 목록 비어 있음"이고 괄호 열거만 10개다(design 표 문구 정정 후보 -- 기준 변경 아님). `judge_p3.py` `CHK_KINDS`는 10개라 `import-dup` 키 부재를 못 잡고 보고에도 안 나온다(판정은 D0a 계약 1 'exit 1 = 하나라도 있음'으로 rc에서 여전히 FAIL -- 그래서 minor).
- 브리핑 §5 3행 기대 ②의 괄호 열거에 `import-dup`를 더한다: "`findings` 열 종류(`move-set`·`move-rejected`·`changed`·`lost`·`rebind`·`future`·`import-dup`·`stmt-order`·`order`·`shim`·`cache` -- D0a 계약 4 11종, design §10 E2 표 괄호는 10개(§6.3 459행은 11개) -- '모든 목록'으로 판정) 모두 빈 목록".
- §9-4 끝 문장 "`findings` 종류 10개" → "`findings` 종류 11개(`import-dup` 포함 -- D0a 계약 4 v8.4)".
- kit `judge_p3.py` 20행: `CHK_KINDS = ("move-set", "move-rejected", "changed", "lost", "rebind", "future", "import-dup", "stmt-order", "order", "shim", "cache")`, 93행을 '모든 목록'으로: `nz = {k: len(v) for k, v in ck["findings"].items() if v}`(열거 밖 종류가 비지 않아도 잡는다).

**m2 -- E6에 판별력 대조가 없고 판정 줄이 exit 숫자뿐.** E6 PASS는 D0a det4 문언(허용 id = `changed` 단위이되 목록에 적지 않음 -- base 짝 `lost` 아님·자기 읽기 `rebind` 아님; 다른 단위의 `rebind`·`lost`와 삭제된 허용 id의 `lost`는 그대로)에 기댄다. det3 문언이었다면 `lost` 1 + `rebind` 1로 FAIL했다(`m10_t1_open_items.md` X-1 실측). 허용 id가 실제 바뀐 단위를 덮는지(공허 PASS 아님)를 공식 H에서 보이는 줄이 없다. §6 원칙("검사가 실제로 거부함을 보인다")대로:
- §4 'E6 `--allow-changed`' 행 '주는 card' 칸: "**M10** `20261006-p3-mod10-entry`(초안 id, ENTRY -- 계약 3 MOD10 최상위 = import + def 하나) · 의미는 **D0a** 계약 4 `changed` 끝 문단(det4·det5, 단계 `allow-changed-declared`)".
- §6 표에 행 추가:
  `| E6 거부 확인 | B0..H, --allow-changed 없이 | exit 1, `findings.changed` = 정확히 {`workspaces/run_harness.py::run`, `skills/analog-gmid-design/assets/gmid_design_pipeline.py::run_gmid_design_pipeline`}, 다른 10종 빈 목록(D0a 단계 `allow-changed-declared` (2)와 같은 모양) -- 아니면 E6 INVALID | 공식에서만(리허설은 D0a 없음) |`
- kit `run_dod.sh` e6(173~177행) -- `chk_all.json` 실행 뒤에 덧붙임:
  ```
  E6RC=$?   # (위 check 직후에 받는다 -- 지금 줄의 echo 앞으로 옮김)
  ( cd "$G" && $PY "$S/move_plan.py" check --root "$ISO" --base "$B0" --head "$H" --card ALL "${MP_ARGS[@]}" > "$S/chk_all_noallow.json" ); echo $? > "$S/chk_all_noallow.exit"
  $PY "$KIT/judge_p3.py" e6 "$S/chk_all.json" "$E6RC" "$S/chk_all_noallow.json" "$(cat "$S/chk_all_noallow.exit")" | tee -a "$O/judge.txt"
  ```
  `judge_p3.py`에 `e6(chk, rc, nochk, nrc)`: `chk`가 없거나 `findings` 없음 → `E6 INVALID`; `nochk` 거부 확인이 exit 1·`changed` 단위 id 집합(원소가 문자열이면 그대로, 사전이면 `unit` 키 -- 다른 모양이면 INVALID) = 위 두 id·다른 종류 빈 목록이 아니면 `E6 INVALID 거부 확인`; 그 밖은 `rc == "0"`·모든 종류 빈 목록이면 `E6 PASS`, 아니면 `E6 FAIL <비지 않은 종류>`. 디스패치 표(126행)에 `"e6": e6`.
  (allow id 표기 = 저장소 상대 `<경로>::<qualname>`: design 1100행·D0a 계약 1 58행·단계 `A/h.py::run`과 같음 -- 지금 kit 175행 문자열은 design 1100행과 바이트 같음.)

**m3 -- §4·§5의 `<날짜>` 자리 id가 이제 초안 id로 정해짐.** §4 B0 행 `<날짜>-p3-move-mod1-gmid-lut` → `20261002-p3-move-mod1-gmid-lut`(초안 id), E6 행 M10 → `20261006-p3-mod10-entry`, E2 키 행 G1 → `20260930-p3-gate-move-aware`, E1·E3·E3b 행 F2 → `20261002-p3-shim-delete`·F1 → `20261002-p3-callers-update`. 각 뒤에 "(초안 id -- 커밋 날짜로 바뀔 수 있음, kit은 slug 정규식)". §9-3의 `p3-mod10-entry`·`p3-test-relocate`에 "초안 `draft_p3_m10.spec.md`·`draft_p3_t1.spec.md`(2026-10-06)"를 덧붙인다.

**m4 -- §0 C1·C4·card 상태 문장이 `fd4ef8c` 판 그대로.** C1 실측 칸 "20장 모두 미병합" → "`6c724de`: `^phase: 3$` 2장(B34 기록 있음, b26pre 기록 없음 -- attempt 1 폐기, attempt 2 대기), 나머지 18장 spec card 없음"; C4 "뒤 것 없음" → "있음(`8b64a84`)"; §0 'card 상태' 문단에 "B34 완료(`2183f2e`), b26pre spec card `6c724de`(attempt 2 -- 계약 1(d)·2·5·8 리터럴 개정, 같은 id·test-only), M10·T1 초안 작성(2026-10-06). T1 착수는 사용자 질문 T1-2(V4 면제 다시 받기 `20261006-p3-t1-v4-exempt`) 답 뒤"를 더한다. 수치(`missing` 25 등)는 §0 실측 값.

**m5 -- §4 E2 키 행에 G1 키 이름 근거 추가(관찰).** M10 초안 V3-RESULT(G1 시제품 + 범위 정책 판 `mutate_changed`)가 `defs`·`moved`·`move_rejected`·`not_targeted`·`targets_by_def`를 design 이름 그대로 낸다(`m10_t1_open_items.md` 'M10 V3'). §9-4 "G1 판정 기록 뒤 다시 잰다"는 그대로 두고, "시제품에서 다섯 키 이름 = design 이름(M10 모의, 판정 기준 아님)" 한 구절을 더한다.

**m6 -- T1 생성기 `.py`가 E3·E3b 스캔 범위 안, F1 쓰기 경로 밖.** T1 초안은 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/build_t1_mapping.py`(정본 생성기)를 spec card 커밋(Role: doc)으로 넣는다. E3(`git grep … -- "*.py"`)·E3b는 D-9 제외 집합(`.ai/verification/`·`probe_stage_partition.py`) 밖 추적 `.py` 전부를 보므로, 그 파일이 SR·TL·DR import(문장·`import_module` 호출)나 SD에서 나간 이름 읽기를 가지면 F2 뒤 E3/E3b FAIL이고 F1(쓰기 경로에 docs 없음)이 고칠 수 없다. 시제품 `p3kit_m10_t1/t1_map.py`는 `ast`·`git show`만 쓰고 엔진 import가 없어(문자열 목록 `OLD`는 E3·E3b 판정 대상 아님) 지금은 영향 없다. 제안: §7에 관찰 7 "Phase 3 기간 docs에 들어온 추적 `.py`(`build_t1_mapping.py` 등)의 E3 `stmt`/`call`·E3b reads 0 확인" -- 또는 T1 초안 '만들면 배선'에 "생성기는 엔진 모듈을 import하지 않는다(E3·E3b 대상)" 한 문장(오케스트레이터 판단). V5 운반 blob(`…/v5-carry/<id>/<blob>.blob`)은 `.py`가 아니라 E3·E3b·N6.3-4 범위 밖이다.

**m7 -- E6 B0→H 전체 모의가 없다(관찰).** 지금까지의 실측은 card별 `check`(M1~M9 발견 0)와 M9→M10 `--card gmid_design_pipeline.py`(X-1)뿐이다. `--card ALL` B0→(M10·T1·F1·F2 뒤)를 한 번도 돌리지 않았다. 추론상 PASS 모양이다(import 문은 `check` 단위가 아니라 `rebind`로 보고, F1의 `run_harness.py` import 교체는 같은 정의로 풀리면 `rebind` 예외, T1·F1 test·`A/tests/tools/**`·workspaces 스크립트는 단위 밖). §8 '공식 실행 전 다시 볼 것'에 "D0a 병합 뒤, M/T1/F 모의 사슬이 있으면 `check --card ALL` B0→끝을 한 번(판정 아님)"을 적어 두기를 권한다.

**m8 -- 머리 v4 줄.** 맨 위에 추가:
> **v4(2026-10-06, 정합 갱신 -- 판정 기준 불변)**: gate `master` `2183f2e` → `6c724de`(문서 커밋 1 -- b26pre spec card). design 30·계획·`tools/gates` 변경 0(`fd4ef8c..6c724de`) → §2 블록 sha256·줄 번호 그대로. 반영: kit `n63_p3.py` nomerge(사용자 승인, `review_nomerges.md` B·S 0) → §5 12행·§10 ③·§6·§7 관찰 3; D0a det4·det5 `--allow-changed` 의미 → §4 E6 행·§6 E6 거부 확인; D0a 계약 4 `import-dup` → §5 3행·§9-4·`judge_p3.py`; M10·T1 초안 id. `6c724de` 모래상자(`C:/g368`): `missing` 25, `N6.3 1 PASS(n=37) | 2 FAIL(2/20, 기록 없음 1) | 3 FAIL | 4 PASS(n=2) | 5 FAIL`, `merges_clean` [].

## 3. 확인만 -- 변경 불필요

1. **card 목록·순서**: `p3_cards.PHASE3` 20장 = design §8 17 + 네 card(B34·b26pre·backfill·B26-1) -- M10·T1 포함, M7 없음(SD 잔류). 순서 = design 30 632·653행·M10 초안 착수 조건(`B34 → b26pre → backfill → B26-1 → B33 → T0·FU·G1 → D0a → D0b → M1…M9 → M10 → T1 → F1 → F2`). B33·G1은 `phase: 0.5`라 `GATE05`(초안 머리 확인).
2. **기대 건수**: N6.3-1 58 = 지금 37 + phase 3 남은 19 + B33·G1 2. b26pre attempt 1 판정 기록(`3950232`)은 gate에 들어가지 않았다(역할 브랜치 0, gate `6c724de`) → 세지 않음. B41(`phase: 4`)은 DoD 뒤. N6.3-5 유형 red-green 7(M10 포함)·test-only 3(b26pre·T0·T1)·equivalence 10 -- 초안 머리와 같음.
3. **E-항목과 T1 뒤 test 위치**: E4 test = `contracts/test_p3_registry_dest.py`(D0b, T1 대상 아님). E3 거부 확인은 B0(= M1 base, T1 전) 판이라 §6 파일 목록 그대로. E3b는 판마다 따로 계산하고 `pre_existing`(경로 키)은 `workspaces/current-reuse-telescopic-ota-report/stick.py` 1건이라 T1 이름 바꾸기와 무관. `EXCL`은 test 경로를 담지 않음. E5 PT3는 `assets/tests` 전체를 모아 T1 `unit/test_mod*.py`·M10 `integration/`·D0a `tooling/`을 포함(`norecursedirs = tools`는 `tooling`과 다름). T1은 수집 id 집합 불변(모의 1124 = 1124).
4. **V4 면제 id(T1 뒤)**: DoD에 V4 항목이 없다. N6.3-1은 기록에 적힌 판정을 읽을 뿐 다시 재지 않으므로 T0 기록(옛 id 면제)·T1 기록(새 id 면제 `20261006-p3-t1-v4-exempt`) 모두 그대로 PASS/N/A로 센다.
5. **V5 승인 수(F1 두 기록·T0/T1/F1 두 번 시도 운반)**: DoD는 승인 기록 수를 세지 않는다(입력 존재 확인은 design 승인·phase3-cards 두 개뿐 -- 나머지는 merge gate가 병합 때 강제). 운반 blob·`paths.tsv`는 `docs/03-analysis/…/v5-carry/`(`.py` 아님) → N6.3-4 pathspec·E3·E3b 밖. 1차 시도 커밋은 gate에 들지 않아 N6.3-3 병합 수(정확히 1)·test-only 단일 부모 조건에 영향 없음(b26pre 브리프 117행 test-only 모양 = n63 `merge_ok` 식).
6. **F2 r5**: F2 계약 13 DoD 의존 표(E0~E6)가 브리핑 §4·§5와 같다. `--head` 40자 sha 조건은 V 도구 실행 조건 -- kit e2는 기록의 40자 sha를 넘김(리허설의 `$H^`만 예외, 판정 밖).
7. **b26pre attempt 2**: 같은 id·`test-only`·approval 그대로 -- kit 정규식·5번 분기 영향 없음.

## 4. 뒷정리

`C:/g368` 삭제(아래 보고). 메인 저장소 쓰기 0(status·reflog 줄 수 전후 같음, HEAD·gate `master` = `6c724de`).
