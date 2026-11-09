# 독립 검토: Phase 3 DoD 초안 v4 -- refresh 검토(S1, m1~m5, m7, m8) 반영 확인

검토 대상: `_drafts/draft_phase3_dod.md`(v4), `phase3_dod_kit/judge_p3.py`·`run_dod.sh`(v4) 대 `*.pre-v4.bak`, 기준 `_drafts/review_phase3_dod_refresh.md`.
대조: `draft_p3_d0a.spec.md`(det5, 계약 1·4, 단계 `allow-changed-declared`), `draft_p3_m10.spec.md`, 각 초안 머리 `id:` 줄, design 30 §10(gate `master` `ae1b588` 판, 복제본에서 `git show`).
검토자는 작성자가 아니다. 고친 파일 없음(이 파일만 씀). 실행은 모래상자 `C:/g382`에서만 했다(TMP/TEMP 그 아래, `cd` 없음, `clone -c core.autocrlf=false`, 끝에 삭제).

## 판정 요약

- **B(차단): 없음.**
- **S(중대): 1건** -- S1 E6 판정기가 **진짜 E6 실패(선언 밖 변경·`lost` 등)를 `E6 INVALID`(측정 무효)로 찍는다**. 거짓 PASS는 없지만 공식 결과에 판정 종류가 잘못 적히고, 원인을 '거부 확인' 쪽으로 돌린다. 이 동작은 초안 §5 8행·§6 E6 행 문언 그대로라 브리핑과 kit을 같이 고쳐야 한다(refresh m2 제안 문언에서 들어온 결함).
- **minor: 4건**(m-a~m-d, 아래).
- **반영 확인**: S1(nomerge 문장), m1(11종·'모든 목록'), m2(E6 거부 확인 배선), m3(id), m4(§0), m5(E2 키 관찰), m7(§8 '다시 볼 것'), m8(머리 v4 줄)이 모두 들어갔다. 실측 수치(`missing` 25, n63 줄)가 그대로 재현된다.

## 0. 실측 (모래상자 `C:/g382`, 2026-10-06, kit 무수정)

`git clone -q --no-hardlinks --no-local -c core.longpaths=true -c core.autocrlf=false` → origin 제거 → `checkout --detach ae1b5886…`(status `--ignored` 0줄), `git archive ae1b588 tools/gates` 캐시. `inputs_p3.py`·`n63_p3.py`만 직접 실행(guard·watch·측정 단계는 돌리지 않음).

- `inputs.json` `missing` **25**: b26pre 판정 기록 1 + spec card 0장 18(backfill·B26-1·T0·FU·D0a·D0b·M1~M6·M8·M9·M10·T1·F1·F2) + 게이트 B33·G1 2 + B0·MPC 2 + 파일 2(`test_p3_registry_dest.py`·`move_plan.py`). P2D `5f643a9…`. 초안 §0·§8.v4와 같다.
- `n63_p3.py`: `N6.3 1 PASS(n=37) | 2 FAIL(2/20, 기록 없음 1) | 3 FAIL | 4 PASS(n=2, 어긋남 0, 덮음 누락 0, 경로 밖 0) | 5 FAIL`, `merges_clean` [], `obs_tools_gates` 4, `without_record` = [`20260930-b26-pre-test-strengthen`], 관찰 0.5 = 34·35 `PNNNNNNNNP` audit·merge True, B33·G1 없음. **§8.v4 `ae1b588` 행과 같다(n63 줄 변화 없음).**
- nomerge 동작 확인: `5f643a9..ae1b588` 엔진 pathspec `git log`(--no-merges 없이) = `2eb7e55`·`d504784` 두 개뿐. 병합 `c851e54`(부모 `d504784`·`2eb7e55`)는 둘째 부모와 엔진 경로 diff 0(TREESAME)이라 기본 history simplification이 뺀다 → `merge_class`까지 가지 않아 `merges_clean` []. 초안 §5 12행·§10 ③ 문언과 맞다.
- `bash -n run_dod.sh` OK.
- 메인 저장소: 실행 전후 HEAD = gate `master` = `ae1b588`, status `--ignored` 176줄·reflog 357줄 같음. 역할 브랜치 2개(`role/audit|test/20260930-b26-pre-test-strengthen` = `e4d5833`)는 이 검토 밖 주체(b26pre 진행 중)다 -- 이 검토는 메인에 `git -C` 읽기만 했다.

## 1. 지시받은 확인 항목

| 확인 | 결과 |
|---|---|
| `--no-merges`/evil merge 거짓 문장 | **남은 거짓 문장 없음.** `--no-merges`가 나오는 곳은 머리 v4 줄(이력), §5 12행("`--no-merges` 없음"), §10 ③("없이 뽑는다")뿐이고 셋 다 kit(`n63_p3.py` 9·17~22·151·207행)과 맞다. evil 정의(merge에서만 바뀐 내용·충돌 해결·부모 3개 이상 → trailer와 무관하게 어긋남)도 `merge_class`(68~87행)·164행과 같다. 문구 하나만 m-d(이력 절, 판정 무관). |
| `CHK_KINDS` = D0a det5 계약 4의 11종 | **같다.** 계약 4 발견 항목 172~209행 = `move-set`·`move-rejected`·`changed`·`rebind`·`future`·`import-dup`·`stmt-order`·`lost`·`order`·`shim`·`cache`(11), 단계 `allow-changed-declared` (1) "발견 11종". `judge_p3.py` 22행 집합과 같음(순서만 다름 -- 판정은 집합). |
| E2가 비어 있지 않은 목록을 모두 잡는가 | **잡는다.** 독립 합성 입력(cards.txt 8줄): 모두 빈 목록 → `E2 PASS card 8개`; 한 card `import-dup` 1 → `E2 FAIL … {'import-dup': 1}`; 한 card `import-dup` 키 없음 → `E2 FAIL … 없는 키 ['import-dup']`; 한 card 열거 밖 종류 `zzz` 1 → `E2 FAIL … {'zzz': 1}`. |
| E6 판정기 | §2 표(내 합성 입력 30가지, 작성자 13가지와 독립). 거짓 PASS 0. S1·m-a·m-b 참고. |
| `run_dod.sh` e6 CLI | **맞다.** 허용 있는 실행은 design 30 §10 E6 블록(`ae1b588` 판)과 바이트 같은 인자(`check --root --base "$B0" --head "$H" --card ALL "${MP_ARGS[@]}" --allow-changed <2>`), 거부 확인은 같은 명령에서 `--allow-changed`만 뺀 것 -- D0a 계약 1 CLI 정본(`check --root --base --head --card <MOD>|ALL --plan --registry --split… [--keep…] [--aliases] [--allow-changed <경로>::<qualname>…]`)과 맞고, `MP_ARGS`는 배열 전개(계약 1 '셸 사용')다. 종료 코드는 각 서브셸 직후에 받는다(`E6RC=$?`, `echo $? > …exit`). judge 인자 4개를 항상 넘긴다. |
| §4 id = 초안 머리 `id:` | **모두 같다.** M1 `20261002-p3-move-mod1-gmid-lut`, D0a `20260930-p3-move-plan-tool`, D0b `20260930-p3-registry-dest`, B26-1 `20260930-b26-rail-accessor-set`(`draft_b26_1.spec.md`), M10 `20261006-p3-mod10-entry`, G1 `20260930-p3-gate-move-aware`(`phase: 0.5`), F1 `20261002-p3-callers-update`, F2 `20261002-p3-shim-delete`; §9-3의 T1 `20261006-p3-test-relocate`. 머리 `evidence_type`도 §5 13행 분류(red-green 7·test-only 3·equivalence 10)와 같다(M2~M9·T0·FU 머리도 확인). kit 정규식(`p3_cards.py`)이 각 id에 맞는다. |
| M10이 `run`을 실제로 바꾸는가(거부 확인 전제) | 맞다 -- M10 초안 계약 1(code diff에 `run_harness.py` 수정)·계약 8(V3 `defs`·`targets_by_def` = `run_harness.py::run`·`gmid_design_pipeline.py::run_gmid_design_pipeline`). 올바른 H에서 허용 없는 실행은 `changed` = 두 id가 되어 거부 확인이 성립한다. |

## 2. E6 판정기 독립 합성 입력 (`judge_p3.py e6`, `C:/g382/jt`)

| # | 입력(허용 있음 / 허용 없음) | 출력 | 평가 |
|---|---|---|---|
| 01 | 11종 빈 목록 rc 0 / rc 1, `changed` = [id2, id1](순서 반대) | `E6 PASS` | 맞음(집합 비교) |
| 02 | 같음 / 사전 원소 `{"unit": …, 다른 키}` | `E6 PASS` | 맞음 |
| 03·04 | 같음 / id 앞 공백·끝 `\n` | `E6 INVALID 거부 확인` | 맞음(엄격) |
| 05 | 같음 / `changed`에 셋째 id | `E6 INVALID 거부 확인` | 맞음(두 실행이 어긋남) |
| 06 | 같음 / ERROR JSON exit 2 | `E6 INVALID … 출력 없음/findings 없음(exit 2)` | 맞음 |
| 07 | 같음 / findings 정상인데 exit 2 | `E6 INVALID` | 맞음 |
| 08 | 같음 / 파일 없음 | `E6 INVALID … (exit )` | 맞음 |
| 09 | judge에 인자 2개만 | `TypeError` traceback, 판정 줄 없음 | m-b(kit은 항상 4개를 넘겨 실제 경로 아님) |
| 10 | 같음 / rc 인자 `" 1"` | `E6 INVALID` | 맞음(셸 `$(cat)`은 개행을 떼므로 실제 경로 아님) |
| 11 | 같음 / `changed` = [id1, id1, id2] | **`E6 PASS`** | m-a(중복을 '정확히 두 id'로 셈) |
| 12 | 같음 / 사전에 `unit` 없음 | `E6 INVALID … 모양 모름` | 맞음 |
| 13·14·15 | 같음 / id 1개 · 빈 목록 rc 1 · 빈 목록 rc 0(공허) | `E6 INVALID` | 맞음 |
| 16 | 열거 밖 종류 1 rc 1 / 두 id | `E6 FAIL {'newkind': 1}` | 맞음 |
| 17·18 | `import-dup` 키 없음(허용 있음 쪽·없음 쪽) | `E6 INVALID 없는 종류 키` / `E6 INVALID 거부 확인` | 맞음 |
| **19** | `lost` 1 rc 1 / 두 id + 같은 `lost` 1 | **`E6 INVALID 거부 확인 … 다른 종류 비지 않음`** | **S1** -- 진짜 FAIL |
| **20** | `changed` = [선언 밖 id] rc 1 / 세 id | **`E6 INVALID 거부 확인`** | **S1** -- MOVE-TOTAL 위반 그 자체 |
| 21 | 빈 목록인데 rc 1 / 두 id | `E6 FAIL exit=1` | 맞음 |
| 22 | ERROR JSON exit 2 / 두 id | `E6 INVALID check 출력 없음` | 맞음 |
| 23 | `lost` 값이 정수 3 | `TypeError: object of type 'int' has no len()`, 판정 줄 없음 | m-b |
| 24 | `findings`가 목록 | `E6 INVALID` | 맞음 |
| 25 | 앞에 경고 줄, 마지막 줄 JSON | `E6 PASS` | 맞음(`load`는 마지막 줄) |
| 26·27 | `changed`가 문자열·사전(목록 아님) | `E6 INVALID … 모양 모름` | 맞음 |
| 28 | 허용 있음 출력 빈 파일 | `E6 INVALID` | 맞음 |
| 29 | `changed` id가 A 기준(`gmid_design_pipeline.py::…`) | `E6 INVALID` | fail-closed(관찰 m-c) |
| 30 | det3 모양(허용 있음에 `lost` 1·`rebind` 1) / 두 id | `E6 FAIL {'lost': 1, 'rebind': 1}` | 맞음 |

## 3. S1 -- 진짜 E6 실패가 INVALID로 찍힌다

원인: `--allow-changed`는 `changed` 목록 소속만 바꾼다(D0a 계약 4 178~181행: `lost`·`rebind` 예외는 두 실행에서 같다). 그래서 H에 실제 결함(선언 밖 `changed`, `lost`, `rebind`, `shim` 등)이 있으면 **허용 없는 실행에도 같은 발견이 나타난다**. 지금 판정기는 거부 확인을 "`changed` = 정확히 두 id, 다른 10종 빈 목록"으로 먼저 걸기 때문에(초안 §5 8행 "…이 아니면 **E6 INVALID**", §6 E6 행 "다른 10종 빈 목록 … 아니면 E6 INVALID"), 결함이 있는 H는 허용 있는 실행의 판정(FAIL)에 이르기 전에 `E6 INVALID 거부 확인: …`이 된다(합성 19·20). E6이 잡으려는 바로 그 경우(MOVE-TOTAL 위반)가 '측정 무효'로 기록되고, 문구가 원인을 거부 확인 쪽으로 돌린다. 종합은 PASS가 아니므로 거짓 PASS는 아니다(그래서 B가 아니라 S).

거부 확인이 보여야 하는 것은 "허용 두 id가 실제 `changed` 단위다(공허 허용이 아니다)"와 "두 실행이 허용 두 id 밖에서 같다"뿐이다. 판정(PASS/FAIL)은 허용 있는 실행이 정한다.

**제안 수정(정확한 문안)**:

(a) 초안 §5 8행 '기대(PASS)' 칸의 v4 문장을 다음으로 바꾼다:
> v4(검토 refresh m2, v4 검토 S1): 같은 B0..H를 `--allow-changed` 없이 돌린 거부 확인이 exit 1이고, 그 `findings.changed` 단위 id 집합이 두 허용 id를 **포함**하고(중복 없음), 두 허용 id를 뺀 `changed`와 다른 10종이 허용 있는 실행의 `findings`와 같아야 한다 -- 아니면 **E6 INVALID**(허용이 실제 바뀐 단위를 덮지 않거나 두 실행이 어긋남). 거부 확인이 성립하면 판정은 허용 있는 실행으로 한다(선언 밖 `changed`·`lost` 등은 두 실행 모두에 나오므로 `E6 FAIL`)

(b) §6 E6 거부 확인 행 '기대' 칸을 다음으로 바꾼다:
> exit 1, `findings.changed` ⊇ {`workspaces/run_harness.py::run`, `skills/analog-gmid-design/assets/gmid_design_pipeline.py::run_gmid_design_pipeline`}(중복 없음), 두 id를 뺀 발견 = 허용 있는 실행의 발견(올바른 H에서는 `changed` = 정확히 두 id·다른 10종 빈 목록 -- D0a 단계 `allow-changed-declared` (2)와 같은 모양) -- 아니면 E6 INVALID

(c) `judge_p3.py` `e6`의 거부 확인 조건(지금 158~161행)을 다음으로 바꾼다:
```python
    mf = d["findings"]
    ids = _unit_ids(nf.get("changed"))
    mids = _unit_ids(mf.get("changed"))
    allow = set(E6_ALLOW)
    nabs = [k for k in CHK_KINDS if k not in nf]
    same_rest = ({k: v for k, v in nf.items() if k != "changed"} == {k: v for k, v in mf.items() if k != "changed"})
    if (nrc != "1" or ids is None or mids is None or nabs
            or len(nf["changed"]) != len(ids) or not allow <= ids
            or ids - allow != mids or not same_rest):
        print("E6 INVALID 거부 확인: --allow-changed 없이 exit=%s changed=%s(기대 exit 1, 허용 두 id %s 포함·중복 없음, "
              "그 둘을 뺀 발견 = 허용 있는 실행) 없는 키 %s" % (
              nrc, "모양 모름" if ids is None else sorted(ids), list(E6_ALLOW), nabs)); return
    nz = {k: len(v) for k, v in mf.items() if v}
    print("E6 %s exit=%s 비지 않은 발견 %s | 거부 확인 --allow-changed 없이 exit=1, 허용 두 id가 changed 단위(나머지 발견 두 실행 같음)" % (
        "PASS" if rc == "0" and not nz else "FAIL", rc, nz))
```
올바른 H에서는 지금 조건과 같은 결과(PASS)이고, 합성 19 → `E6 FAIL {'lost': 1}`, 20 → `E6 FAIL {'changed': 1}`, 05(허용 없는 쪽에만 셋째 id) → INVALID 그대로, 11(중복) → INVALID가 된다. 고친 뒤 이 표의 30가지를 다시 돌려 둘 것(작성자 13가지에 19·20·11을 더하면 충분).

## 4. minor

**m-a -- 중복 id를 '정확히 두 id'로 센다(합성 11).** `_unit_ids`가 집합을 만들어 `[id1, id1, id2]`가 PASS다. D0a 계약 2 '결정성'은 정렬만 정하고 유일성은 말하지 않는다 -- 중복은 도구 결함 표지이므로 거부 확인에서 `len(목록) == len(집합)`을 단언한다(S1 (c)에 포함). 초안 §5 8행 '정확히 두 허용 id' 문언도 S1 (a)로 같이 바뀐다.

**m-b -- 판정 줄 없이 끝나는 경로 2개(합성 09·23).** `findings` 값이 목록이 아니면(`len(int)`) e2·e6 모두 traceback으로 끝나 `judge.txt`에 E2/E6 줄이 없다(PASS가 아니므로 fail-closed지만, 결과 파일에 'E6 줄 없음'으로만 남는다). kit은 인자 4개를 항상 넘겨 09는 실제 경로가 아니다. 제안: e2 `nz`·e6의 `len(v)` 앞에 `if not all(isinstance(v, list) for v in f.values()): print("E? INVALID findings 값 모양 …"); return`(e2는 그 card를 `bad`에 넣고 계속).

**m-c -- `changed` id 표기(관찰, 판정 영향 없음).** D0a 계약 2의 `plan` 단위 id는 `<A 기준 파일>::<키>`(78·111행)이고, 계약 4 `--allow-changed`는 `<경로>::<qualname>`(단계 예 `A/h.py::run` -- A 약어를 쓴 저장소 상대), design E6은 저장소 상대다. `check` `changed` 원소가 A 기준으로 나오면 판정기는 INVALID(합성 29, fail-closed)라 거짓 PASS는 없다. 초안 §9-4 "D0a 병합 뒤 확인" 목록에 "`check` `changed` 원소 표기가 `--allow-changed` 표기(저장소 상대)와 같은지"를 한 구절 더하면 공식 실행에서 놀랄 일이 없다.

**m-d -- §8.v3 4번 한 문구(이력, 판정 무관).** "다른 6개 커밋(문서 4·merge·audit)은 pathspec 밖" 중 merge `c851e54`는 엔진 경로를 첫 부모 대비 2파일 바꾸므로 'pathspec 밖'이 아니라 **둘째 부모와 TREESAME이라 history simplification이 뺀 것**이다(v3 당시 kit은 `--no-merges`가 뺐다). 고친다면: "다른 6개 커밋 중 문서 4·audit은 pathspec 밖, merge `c851e54`는 둘째 부모 `2eb7e55`와 엔진 경로가 같아(TREESAME) 목록에서 빠진다(v3 kit은 `--no-merges`, v4 kit은 기본 simplification -- `merges_clean` [])".

## 5. 확인만 -- 변경 불필요

1. refresh S1 (a)~(e): §5 12행, §10 ③(v4 표시 포함), §6 마지막 행 끝 문장, §7 관찰 3 괄호, 머리 v4 줄 -- 제안 문안과 같다.
2. refresh m1: §5 3행 괄호 11종·'모든 목록', §9-4 "11개(`import-dup` 포함)", `CHK_KINDS` 11종, e2 `nz` 모든 목록. 위 §1 합성으로 판별 확인.
3. refresh m2: §4 E6 행 '주는 card' 칸, §6 E6 거부 확인 행, `run_dod.sh` e6 두 실행·judge 줄, 디스패치 `"e6": e6`. 배선은 맞고 판정 조건만 S1.
4. refresh m3·m4·m5·m7·m8: §4 각 행 id(초안 머리와 같음)·§9-3 초안 경로, §0 C1·C4·card 상태 문단, §4 E2 키 행·§9-4 관찰 구절, §8.v3 끝 'v4 추가' 줄, 머리 v4 줄 -- 모두 들어갔다. m6을 T1 card 몫으로 넘긴 것은 머리에 적혀 있다.
5. §8.v4 '대역으로 E6 B0→H 모의 수행 안 함'의 사유(det3 모양 대역)는 D0a 단계 `allow-changed-declared` 끝 문단(det3 구현이 (1)에서 `lost` 1·`rebind` 1)과 맞다.

## 6. 뒷정리

`C:/g382` 삭제 확인(`ls` 없음). 메인 저장소 쓰기 0(HEAD·gate `master` `ae1b588`, status 176줄·reflog 357줄 전후 같음). 쓴 파일은 이 검토 파일 하나.
