# D0b·M card 키트 대 D0a det5 독립 대조 (review_d0b_vs_d0a_det5)

검토자: 독립 검증자(작성자 아님). 기준: gate `master` = 실제 저장소 `HEAD` = `6c724de`(시작·끝 같음, 실제 저장소 쓰기 0 -- `status --porcelain` 줄 수 시작 스냅숏과 같음).
범위: D0a 초안 `draft_p3_d0a.spec.md`(det5 판 -- 계약 1 exit 2 목록 (e5)·(e6), 계약 2 결정성 문단·코드 포인트 순, 계약 4 `--allow-changed`(det4), 필수 단계 `allow-changed-declared`)를
소비하는 쪽: `draft_p3_d0b.spec.md`·`d0b_launch.sh`·`d0b_briefs.md`, `p3kit_m2_m9/`(`mkcards.py`·`chain226.py`·`gen226.py`·`cmp_plans.py`·`move_plan_sim.py`·`move_plan_alltok.py`), `p3kit_m1/`(`move_plan_sim.py`), `p3kit_m10_t1/`(`build323.sh`),
그리고 `--allow-changed`를 쓰는 초안(`draft_p3_m1`·`draft_p3_m10`·`draft_p3_f2`·`draft_phase3_dod`·`phase3_runbook`)은 grep으로만 대조.
실행: 저장소 읽기(`git show 6c724de:…`)와 grep뿐. 샌드박스 `/c/g367`은 쓰지 않았다(만들지 않음). 레지스트리 사본 하나를 세션 scratchpad에 잠깐 썼다가 지웠다(행 수 세기용).

## 판정: **B 0, S 0, minor 4, 선택 2. D0b 착수를 막는 것 없음.**

det5가 바꾼 뜻(출력 순서 고정, (e5)·(e6) exit 2, `--allow-changed` 허용 id = `changed` 단위로 세되 목록에는 적지 않음)과 **어긋나서 판정이 틀어지는 소비자는 없다**.
남은 것은 (e5)·(e6) exit 2가 났을 때의 멈춤 경로 문언 빈칸(m1), M card '이름순' 정의 빈칸(m2), 대역 시제품이 det4 이전 문언으로 남은 것(m3), D0b 실측 한계 문장(m4)이다.

---

## 1. 확인한 것 -- 어긋남 없음

| 질문 | 결과 | 근거 |
|---|---|---|
| D0b 캐시 키가 det5를 반영하나 | **반영할 필요가 없고, 지금 구조가 맞다.** `plan` 출력 캐시(`<상태>.plan.<H>.json`)는 gate sha H만 키이고, 실행하는 것은 **gate H 트리의 `tools/migrate/move_plan.py`**(`plan_at`: `"$ISO/r/$TOOL" plan --root "$ISO/r" --rev "$H"`)다. D0a **초안**은 `plan_at`·`plan_sum` 어디에도 입력이 아니다 -- det5는 D0a 병합(새 H)으로만 들어오고 새 H는 새 캐시다. 요약 캐시 키(`SUM_KEY` = D0b 초안 sha256 16자 + 스크립트 sha256 16자)는 요약이 읽는 것(D0b 초안 (d)-1 표·`RULE_IDS`·`SIX`·`D11NAME`·heredoc)과 정확히 같다. det 결정성 문단 덕에 같은 H의 캐시 바이트가 `PYTHONHASHSEED`와 무관해져 캐시가 오히려 더 안전해졌다. | `d0b_launch.sh` 75~79·195~221행 |
| exit 1 대 2 | 어긋남 없음. S-5는 D0b base exit **1**(`reg_mismatch` > 0)을 기대, S-4는 exit 2를 규약오류(1)로 멈춤. D0b test 계약 11 (b)는 `verdict != "ERROR"`(exit ≠ 2)를 판정 목록 앞에 단언 -- (e5)·(e6) exit 2도 `KeyError`가 아니라 `AssertionError`로 FAIL. M card 계약 2·9(`check`·`plan` exit 0), M10 계약 10(`plan` exit 0), DoD E6(exit 0) 모두 det5와 같다. D0a 계약 8 (a)(실제 트리 `plan` exit ≠ 2)와 det3 재측정(`6c724de` (e5)·(e6) 참인 이름 0)이 D0b base 전제를 덮는다. | D0b 계약 11 (b)·S-4/S-5, D0a 계약 1·8 (a)·det3 재측정 |
| D0b 거부 입력이 (e5)·(e6)에 걸리나 | **걸리지 않는다.** 레지스트리(`6c724de`) 함수 칸 첫 토큰 행 수: `quantize_L` 1·`_theta_evidence_for_pair` 1·`size_transistor` 1·`_as_set` 1·`save_html_report` 1·`compute_metric` 1·`validate_theta_declaration_order` 1 -- 여러 행인 키는 `SemiEmpiricalGmIdLUT` 14뿐이고 어느 R-입력도 그 행을 건드리지 않는다. 그래서 R-B1·R-B2·R-B3·R-E1(칸 변경)은 측정 열 그대로 exit 0/1이고 exit 2로 바뀌지 않는다. 재생성 뒤 `SemiEmpiricalGmIdLUT` 14행은 모두 같은 줄기가 되어 (e5) 조건이 생기지 않는다. | `git show 6c724de:<레지스트리>` 행 수 grep |
| 출력 순서 가정(`mod_imports`·`reexports`) | det2~det4가 고정한 순서(`__future__` 줄 → `from` 줄 모듈 이름 오름차순 → `import` 줄 줄 문자열 오름차순, `from` 항목 문자열순, `reexports` MOD 번호순·이름 코드 포인트순)는 대역 `move_plan_sim.py` 538~553·401~410행과 같다(`sorted` = 코드 포인트). `gen226.py` 120행 재수출 줄도 `sorted(names)`. 그래서 M card 계약 3 (a) "`mod_imports` 줄을 **차례로** 파싱"은 이제 D0a가 순서를 정한 목록을 가리키고 키트 측정 바이트와도 같다. | 대역 소스, `gen226.py` |
| `--allow-changed` 소비자 | DoD E6(`draft_phase3_dod.md` 98·115행), F2 표(82행), M1 170행, runbook 332행은 모두 "M10 두 id로 `--card ALL` exit 0"을 기대한다 -- det3 문언이면 `lost` 1·`rebind` 1로 FAIL(X-1)이었고 det4 문언이라야 성립한다. **det5 판과 같다.** M10 초안은 `check`에서 `order` 0만 단언하고 `--allow-changed`에 기대지 않는다(계약 12). | grep `allow-changed` |
| 측정 키트의 출력 소비 | `chain226.py`·`cmp_plans.py`·`mkcards.py`는 JSON을 파싱해 키·길이·사상으로만 비교한다(바이트·목록 위치 비교 없음; `v[:3]` 견본은 표시용). `check` `findings` 종류 키 11개가 항상 있다는 가정은 D0a 계약 4와 같다. | 해당 파일 |
| D0b test 브리프 | 목록 순서·키 위치 가정 없음(`"tool"` 값·`verdict` 값으로 단언). | `d0b_briefs.md` 1절 |

---

## 2. minor

### m1. (e5)·(e6) exit 2가 D0b base에서 나면 멈춤 경로가 없다 -- 런처는 '일시 오류면 캐시를 지워라'로 안내한다

* 사실: D0b 계약 8의 멈춤 조건 (a)~(f)는 exit 1 목록만 다룬다. det 이후 exit 2에는 **입력 오류가 아닌 레지스트리 사실**((e5) 한 키의 MOD 하나짜리 칸이 서로 다른 MOD, (e6) A-3 칸의 가장 작은 MOD가 서로 다름)이 들어 있다.
  `d0b_launch.sh` `cond_4`는 exit 2를 규약오류(1)로 멈추고(fail-closed라 조용한 통과는 없다) `plan_clear_hint`("일시 오류였으면 … 캐시를 지우고 다시")를 붙인다 -- (e5)·(e6)이면 지워도 같은 결과라 안내가 틀린 쪽을 가리킨다.
  지금 트리 0건(det3 재측정)이고 D0a 계약 8 (a)가 D0a 병합 때 실제 트리 exit ≠ 2를 보므로 잠재 결함이다. D0a 병합과 D0b base 사이에 레지스트리나 계획서가 바뀌면 드러난다.
* 제안 편집(정확 문안):
  1. `draft_p3_d0b.spec.md` 계약 8, (f) 줄 바로 뒤에 새 항목:
     ```
        (g) **`plan` exit 2**(D0a 계약 1 -- 입력 오류, 계약 2 가장자리 (e1)·(e4)·(e5)·(e6)): 열을 쓰지 않는다(이관표가 없다 -- D0a 계약 8 (a) 전제가 깨졌다). `error` 문자열을 판정 근거로 남긴다.
        (e5)·(e6)(한 단위 키에 짝지어진 레지스트리 칸끼리 모순)이면 (a)의 경로로 닫는다 -- 그 단위를 N3.10 토큰으로 A-1에 두면 (e5)·(e6) 범위 밖이 된다(D0a 계약 2 범위 문장, D-11 별도 승인). 레지스트리 칸을 손으로 고르는 정정은 이 card의 '손으로 쓰지 않는다'와 부딪히므로 별도 사용자 결정 없이 하지 않는다.
        (e1)·(e4)·입력 오류는 엔진 소스·인자 쪽 원인이라 오케스트레이터가 원인을 적고 멈춘다. 지금 트리(`6c724de`)에서 (e5)·(e6) 조건이 참인 이름 0(D0a det3 재측정).
     ```
     그리고 같은 계약 끝 문장 "이 card의 test·code 커밋은 (a)~(e)가 모두 빈 base" → "(a)~(e)가 모두 비고 (g)가 아닌 base".
  2. `d0b_briefs.md` 0.4 멈춤 절차 2. 끝에 한 문장: "`plan` exit 2(spec 계약 8 (g)) → (e5)·(e6)이면 N3.10 토큰(D-11), 그 밖이면 원인 보고 후 멈춤 -- 캐시 지우기로 풀리지 않는다."
     2절(code-author) 5. 앞에 "`plan`이 exit 2이면 쓰지 말고 멈춘다(오케스트레이터 보고, spec 계약 8 (g))."
  3. `d0b_launch.sh` `cond_4`의 exit 2 줄(334행)을 다음으로(반환값 1 유지, 안내만 보탠다):
     ```
     [ "$(sum_get "$H" "s['exit']")" != 2 ] || { echo "      plan exit 2(ERROR): $(sum_get "$H" "s['error']")" >&2; echo "      D0a 계약 2 가장자리 (e1)·(e4)·(e5)·(e6)이면 캐시를 지워도 같다 -- spec 계약 8 (g)·d0b_briefs 0.4 멈춤 절차로" >&2; plan_clear_hint "$H"; return 1; }
     ```
     (스크립트 sha가 요약 캐시 키에 들어 있어 요약은 다시 계산된다 -- 의도된 동작.)

### m2. M card 계약 3 (b)의 '이름순'이 정의되지 않았다 -- `ast.dump` 열 비교라 별칭 순서가 판정에 든다

* 사실: M1~M9 초안(8개 모두, `mkcards.py` 192행이 생성) 계약 3 (b)는 split 파일 최상위 문장 열을 `ast.dump`로 비교하고 재수출 `ImportFrom`의 이름을 "(`_` 접두 포함, **이름순**, `as` 없음)"이라 적는다. `ast.dump`는 `names` 순서를 담는다.
  D0a det4는 '이름순' = **코드 포인트 순**(대문자 → `_` → 소문자)이라 정했고 도구 `reexports`도 그 순서다. 그런데 같은 초안 '의도'는 design §2.2 예 `from <MOD> import a, b, _c`(`_c`가 끝 -- 코드 포인트 순이면 `_c, a, b`)를 인용한다.
  auditor가 기대 문장을 '이름순'을 사람 읽기(밑줄 무시·대소문자 무시)로 만들면 정직한 이동이 FAIL하고, code-author가 예를 따라 손으로 줄을 쓰면 도구 줄과 갈린다.
* 제안 편집:
  * `mkcards.py` 192행과 M1~M9 초안 계약 3 (b)(M1은 43행): "(`_` 접두 포함, 이름순, `as` 없음)" →
    "(`_` 접두 포함, `as` 없음; 이름 순서 = card base `plan` `reexports[\"<그 split 파일>\"]`의 이 MOD 줄 그대로 -- D0a 계약 2 결정성 문단의 코드 포인트 순, 대문자 → `_` 접두 → 소문자)".
  * `mkcards.py` 134행과 각 초안 '의도'의 `from <MOD> import a, b, _c` 인용 뒤에 "(design §2.2의 형태 예 -- 실제 이름 순서는 위 계약 3 (b))"를 붙인다. design 문서는 고치지 않는다(형태만 말하는 문장이다).
* M card 수치·판정 기준은 바뀌지 않는다(키트 `gen226.py`가 이미 `sorted` = 코드 포인트로 측정).

### m3. 대역 시제품 `move_plan_sim.py`(·`move_plan_alltok.py`)가 det4 이전 `--allow-changed` 문언으로 남아 있다

* 사실: `p3kit_m1/move_plan_sim.py`와 `p3kit_m2_m9/move_plan_sim.py`(두 파일 같음, 621~624행), `p3kit_m2_m9/move_plan_alltok.py`(623~626행)는 허용 id를 `changed` 목록에서 빼면서 `changed_ids`에도 넣지 않는다 -- det3 문언 그대로라
  base 짝이 `lost`, 자기 읽기가 `rebind`로 나온다(X-1이 이 대역으로 재현한 결함). `p3kit_m10_t1/build323.sh`는 이 대역을 `tools/migrate/move_plan.py`로 설치한다. 대역은 (e5)·(e6) exit 2도 없고(첫 행 선택), 출력 키 정렬도 하지 않는다.
  지금 어느 키트도 대역으로 `--card ALL --allow-changed`를 돌리지 않으므로 기록된 수치에는 영향이 없다. 다만 DoD 사전 시험(E6)이나 F2 키트가 이 대역을 다시 쓰면 E6가 거짓 FAIL한다.
* 제안 편집(측정 키트 -- 역할 산출물 아님):
  * 세 파일의 `compute_check` 해당 줄:
    ```
                if huid in mv["units"] or (k, q, h) in bunits.get(p, set()) or huid in allow:
                    continue
                F["changed"].append({"unit": huid, "kind": k})
                changed_ids.add((p, k, q))
    ```
    →
    ```
                if huid in mv["units"] or (k, q, h) in bunits.get(p, set()):
                    continue
                changed_ids.add((p, k, q))          # D0a det4: an allowed id is a changed unit (base pair not lost, own reads not rebind)
                if huid in allow:
                    continue                         # ... but it is not listed in `changed`
                F["changed"].append({"unit": huid, "kind": k})
    ```
    (head에 없는 허용 id는 이 고리에 들지 않아 base 단위가 그대로 `lost` -- det4 '삭제된 허용 id는 그대로 보고'와 같다.)
  * 같은 파일 100행 머리 주석 뒤에 한 줄: "# NOT det~det5: no (e5)/(e6) exit 2 (first registry row wins), no output key/list normalization -- current tree has 0 such keys (D0a det3 re-measure 6c724de), so recorded numbers are unaffected."

### m4. D0b '작성 전 실측' 시제품 한계 문장에 det~det5가 빠져 있다

* 사실: D0b 초안 '작성 전 실측' UD-6 문단(154행)은 대역의 'r1 미반영' 세 곳만 적는다. det(결정성)·det3((e5)·(e6))·det4(`--allow-changed`)도 대역에 없다. D0b 수치에는 영향이 없지만(현재 트리 (e5)·(e6) 0, D0b는 `check` 미사용) 한계 목록이 불완전하다.
* 제안 편집: 154행 괄호 "… 세 곳이 card와 다르다, review_d0a_d0b_ready D0a m1; 실제 트리는 그 경우가 0이라 아래 수치에는 영향 없음)" 뒤에
  "; **det~det5 미반영**: 출력 키·목록 정렬 정규화 없음, (e5)·(e6) exit 2 대신 첫 행 선택, `--allow-changed` det3 문언 -- 지금 트리 (e5)·(e6) 참인 이름 0(D0a det3 재측정 `6c724de`), D0b는 `check`를 쓰지 않으므로 아래 수치 영향 없음"을 더한다.

---

## 3. 선택

* s1. det로 `plan` stdout이 바이트 결정적이 되었으니 D0b auditor 3.1에 한 줄을 더할 수 있다: `out/plan_base.json`과 런처 캐시 `<상태>.plan.<base sha>.json`이 **바이트 같음**(서로 다른 프로세스·시드에서 실제 트리 결정성의 증인 -- D0a `determinism` 단계는 합성 입력만 본다). 비용 0(이미 있는 두 출력의 `cmp`).
* s2. D0b oracle 절 89행이 D0a 합성 단계를 예로 열거한다(`doc-excluded`…`monotone-seed`). 완전 목록이 아니므로 고칠 필요는 없다. 바꾼다면 "(D0a 필수 단계 21 -- `determinism`·`allow-changed-declared` 포함)"처럼 수만 적어 D0a 개정 때 다시 낡지 않게 한다.

## 4. 범위 밖 관찰(조치 불요)

* `gen226.py` 6행 docstring은 "<card MOD file> = docstring + plan.mod_imports"라고 적지만 코드(81행 `out = list(head)  # no module docstring`)는 docstring을 두지 않는다 -- M1-1 기본안과 같고, 주석만 낡았다.
