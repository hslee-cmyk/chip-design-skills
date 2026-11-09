# Phase 2 DoD E4 드라이런 (오케스트레이터 도구 점검용 -- 판정 증거 아님)

- 일시: 2026-09-30, 측정 주체: 오케스트레이터가 띄운 드라이런 agent(auditor 아님)
- 대상: 기준 판 `da03c0e`(Phase 1 DoD 대상), 새 판 = 현재 gate master `7535799`(드라이런이라 Phase 2 마지막 병합본 대신 사용)
- 기준 문장: design 20 §10 E4 행(2140da8 정정본), `_drafts/phase2_dod_brief.md` E4 항목
- 환경: Windows 11, `C:/Python314/python.exe`(3.14.2) `-B -P`, Git Bash, `APPDATA=C:/Users/HSLEE/AppData/Roaming`
- 임시 경로: `C:/g45`만 사용(iso = 격리 복제본, scripts = 스크립트 사본, cache = gate 캐시, out = 산출, snap = 메인 저장소 스냅숏). 끝나고 `C:/g45` 삭제.

## 1. 결론 요약

| 항목 | da03c0e | 7535799 | 판정(드라이런) |
|---|---|---|---|
| E-LIB `hash` | `1d2e3bf6acf762ebea14aa526405bfe63db9632cfab68672b93948c2be3b7a8f` | `1d2e3bf6acf762ebea14aa526405bfe63db9632cfab68672b93948c2be3b7a8f` | 같음, 두 판 모두 9/9 load·V1·V2 ok, 예외 0 |
| E-INST current_reuse_telescopic_ota `without_topology_ref_sha256` | `185b675e9dd363a535d2942c651cddee4cb1a0ee98b703f0c7abef99f50e51ca` | `185b675e9dd363a535d2942c651cddee4cb1a0ee98b703f0c7abef99f50e51ca` | 같음 (n_sizing 51 / 51) |
| E-INST folded_cascode `without_topology_ref_sha256` | `0ca6746f1cb3d364f26f5ec6b37e931c7fbc3488b610b4e57f377a6067cda754` | `0ca6746f1cb3d364f26f5ec6b37e931c7fbc3488b610b4e57f377a6067cda754` | 같음 (n_sizing 13 / 13) |
| (b) 새 판 topology_ref | -- | `skills/analog-gmid-design/assets/library/<파일>`, `topology_ref_equals_expected_contract1` = true(두 회로), `path_string_hits` = [] | 충족 |
| (c) 기준 판 topology_ref | `C:\g45\iso\skills\analog-gmid-design\assets\library\<파일>`, `topology_ref_is_join_of_ASSETS_DIR` = true(두 회로) | -- | 충족 |
| PT 전체(`--gmid-phase=2`) | (재지 않음 -- E4는 새 판만 요구) | 798 passed, 15 xfailed, 실패 0 (310.9 s) | 실패 0 |
| PT `--gmid-dod`(`--gmid-phase=2`) | -- | 798 passed, 15 xfailed, 실패 0 (255.8 s) | 실패 0 |
| 메인 저장소 쓰기 | `git status --porcelain --ignored` 전/중/후 3회 동일(173줄), 스탬프 이후 수정된 파일 0(workspaces·skills·tools·.ai/verification) | 같음 | 쓰기 없음 |

**불일치 0건.** 동작 변화 의심 없음 → card별 판정 기록 추적 불필요. 세 스크립트 모두 **수정 없이** 두 판에서 돌았다(exit 0). 참고로 이 값들은 DF-35/DF-36 판정 기록 폴더(`20260930-df35-harness-paths/einst/*`, `base_check.json` 등)에 이미 있는 값과 같은 해시다(grep 일치).

다만 E4 절차 문장에 **도구 쪽 모호점 3개**가 있다(§4). 결과는 바뀌지 않지만 auditor가 문장만 보고 실행하면 막히거나 해석이 갈릴 수 있다. 이 중 ①②는 문장 보강, ③은 기준(수행 조건) 해석이라 **정정하려면 승인 필요**로 표시한다.

## 2. 실행 명령(순서대로, 전부 기록)

```bash
# 0. 메인 저장소 스냅숏(읽기 전용)
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
git -C $R status --porcelain --ignored > /c/g45/snap/main_before.txt   # 173줄
touch /c/g45/snap/stamp
# 1. 격리 복제본
git clone -q --no-hardlinks --no-local -c core.longpaths=true "$R" C:/g45/iso   # 20.4 s
git -C C:/g45/iso remote remove origin
# 2. 스크립트 사본(gate master 판에서 복사 -- da03c0e 판에는 세 스크립트가 없다, §4-①)
cp C:/g45/iso/.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py \
   C:/g45/iso/.ai/verification/20260930-df35-harness-paths/scripts/e_inst_df35.py \
   C:/g45/iso/.ai/verification/20260930-df36-instance-relpath/scripts/e_inst_df36.py /c/g45/scripts/
#   sha256: e_lib 045f65c8…f46201, e_inst_df35 575fcb32…ba384, e_inst_df36 aa76989e…ddccb7
# 3. 기준 판
git -C C:/g45/iso checkout -q --detach da03c0e
git -C C:/g45/iso checkout -- workspaces ; git -C C:/g45/iso clean -fdxq      # status 0줄
python -B -P /c/g45/scripts/e_lib.py C:/g45/iso C:/g45/out/elib_da03c0e.json               # 2.5 s
python -B -P /c/g45/scripts/e_inst_df35.py C:/g45/iso current_reuse_telescopic_ota base C:/g45/out/einst_da03c0e_current_reuse_telescopic_ota.json   # 452 s, exit 0
python -B -P /c/g45/scripts/e_inst_df35.py C:/g45/iso folded_cascode base C:/g45/out/einst_da03c0e_folded_cascode.json   # 52 s, exit 0
git -C $R status --porcelain --ignored  # == before
# 4. 판 바꾸기
git -C C:/g45/iso checkout -- workspaces ; git -C C:/g45/iso clean -fdxq
git -C C:/g45/iso checkout -q --detach 7535799                                  # status --ignored 0줄
python -B -P /c/g45/scripts/e_lib.py C:/g45/iso C:/g45/out/elib_head.json                  # 3.3 s
python -B -P /c/g45/scripts/e_inst_df36.py C:/g45/iso current_reuse_telescopic_ota C:/g45/out/einst_head_current_reuse_telescopic_ota.json   # 409 s, exit 0
python -B -P /c/g45/scripts/e_inst_df36.py C:/g45/iso folded_cascode C:/g45/out/einst_head_folded_cascode.json   # 42 s, exit 0
git -C $R status --porcelain --ignored  # == before
# 5. PT (새 판, 산출 정리 뒤)
git -C C:/g45/iso checkout -- workspaces ; git -C C:/g45/iso clean -fdxq
git -C C:/g45/iso archive 7535799 tools/gates | tar -x -C /c/g45/cache      # <cache> = C:/g45/cache/tools/gates
PYTHONPATH=<cache> PYTHONPYCACHEPREFIX=C:/g45/pyc python -P -m pytest -c <cache>/pytest_gate.ini \
  --rootdir=C:/g45/iso --confcutdir=C:/g45/iso C:/g45/iso/skills/analog-gmid-design/assets/tests \
  --gmid-phase=2 -q -p no:cacheprovider          # 798 passed, 15 xfailed, 325 s wall
#   (-p no:cacheprovider는 PT 정의에 없는 추가 -- 결과 영향 없음, 다음 실행에서는 뺐다)
PYTHONPATH=<cache> PYTHONPYCACHEPREFIX=C:/g45/pyc python -P -m pytest -c <cache>/pytest_gate.ini \
  --rootdir=C:/g45/iso --confcutdir=C:/g45/iso C:/g45/iso/skills/analog-gmid-design/assets/tests \
  --gmid-phase=2 --gmid-dod -q --color=no        # 798 passed, 15 xfailed, 263 s wall
git -C $R status --porcelain --ignored  # == before, 스탬프 이후 수정 파일 0
```

소요: E4 측정(E-LIB 2회 + E-INST 4회) 약 16분(파일럿 E-INST가 판당 7~8분으로 대부분), PT 2회 약 10분, 복제 20초.

## 3. 스크립트별 무수정 실행 확인

| 스크립트 | 판 | 인자 모양 | import/경로 | 복제본 밖 쓰기 |
|---|---|---|---|---|
| e_lib.py | 두 판 | `<iso> <out>` 그대로 | stick_diagram 출처 = `<iso>` assets(가드 통과) | out만(C:/g45/out). 복제본 status 변화 없음 |
| e_inst_df35.py base | da03c0e | `<iso> <회로> base <out>` 그대로 | 리터럴 수 (ASSETS, WORKSPACES) = (2, 1) → 치환 성공. 상수 ASSETS_DIR/LIBRARY_DIR/WORKSPACES_DIR/LUTFILE 전부 `C:\g45\iso\…`. sys.path 추가 = `<iso>\skills\analog-grammar\assets`, `<iso>\skills\analog-gmid-design\assets`. 엔진 3모듈 출처 `<iso>` | 메인 저장소 쓰기 0(3회 스냅숏 동일). 산출은 `<iso>\workspaces\<report_dir>\*.instance.json`·`*.report.html` |
| e_inst_df36.py | 7535799 | `<iso> <회로> <out>` 그대로 | 메인 리터럴 0개(가드 통과), 상수 전부 `<iso>` 유도, 엔진 출처 `<iso>` | 같음 |

**메인 저장소 쓰기 방지 확인(base 모드 치환)**: da03c0e `run_harness.py`의 메인 절대 경로는 35행 `sys.path.insert`, 42행 `ASSETS_DIR`, 44행 `WORKSPACES_DIR` 세 곳뿐이고(LUTFILE·LIBRARY_DIR는 ASSETS_DIR에서 유도), 치환 대상 리터럴 (2, 1)과 정확히 같다. da03c0e 엔진(`skills/analog-gmid-design/assets/*.py`, tests 제외)에는 `HSLEE` 리터럴이 없다. 하네스가 import하는 것은 sizing_recipe·stick_diagram·design_report뿐(365행 `import run_harness as H`는 docstring). 실측으로도 `git -C <main> status --porcelain --ignored`가 전/중/후 동일, 스탬프 이후 수정 파일 0 → **치환이 메인 저장소 쓰기를 막는다.**

## 4. 발견한 도구 문제·모호점 (결과는 불변)

① **스크립트 경로의 기준 트리가 문장에 없다.** E4 행은 `.ai/verification/.../e_lib.py` 등을 상대 경로로 적지만, 이 세 파일은 da03c0e 판에 **없다**(각각 148bd6d, 34bc75e에서 생김). `<iso>`를 da03c0e로 떠 놓고 `<iso>/.ai/verification/...`를 부르면 파일이 없어 실패한다. 이번에는 판을 바꾸기 전에 gate master 판에서 `C:/g45/scripts`로 복사해 두 판 모두 같은 사본을 썼다. 또 `git clean -fdx`가 복제본 안 산출을 지우므로 `<out>`도 복제본 밖이어야 한다.
   - 제안 문장(보강): "세 스크립트는 판을 바꾸기 전에 대상(병합본) 커밋의 `.ai/verification/…`에서 `<iso>` 밖 임시 경로로 복사해(sha256 기록) 두 판에 같은 사본을 쓴다. `<out>`은 `<iso>` 밖."

② **실행 옵션이 스크립트 docstring에만 있다.** docstring은 `python -P …`로 부르라고 하는데 E4 행에는 인터프리터 옵션이 없다. `-P` 없이 부르면 스크립트 디렉터리가 sys.path[0]에 들어간다(이번 구성에선 영향이 없을 것으로 보이나 확인하지 않음). `-B`(복제본에 `__pycache__` 안 남김)도 적는 편이 판 간 `clean` 가정과 맞다.
   - 제안 문장(보강): "`$PY -B -P <스크립트> …`".

③ **E4의 `PT`가 어떤 `--gmid-phase`로 도는지 정해지지 않았다 -- 기준 해석, 승인 필요.** design 20 §10 머리(213행)는 "`PT`는 10-test-separation §10 정의를 그대로 쓴다"인데 그 정의는 `--gmid-phase=1`이 박혀 있다(Phase 1 DoD용). 최근 판정 기록은 `--gmid-phase=0.5`(v3-history-clone V1), `--gmid-phase=2`(DF-36 mutate 재실행)처럼 값을 바꿔 썼다. xfail 조건·엄격 집합이 phase에 따라 달라지므로 Phase 2 DoD에서 `=1`과 `=2`는 다른 검사다. 이번 드라이런은 `--gmid-phase=2`로만 쟀다(`=1`은 재지 않음). 또 `_drafts/phase2_dod_brief.md`는 "PT 전체·PT --gmid-dod"를 E4에 넣었지만 design 20 E4 행에는 `--gmid-dod`가 없다(브리핑과 설계서 불일치).
   - 제안(기준 변경 -- **사용자 승인 필요**): design 20 §10 머리를 "`PT`는 10 §10 정의에서 `--gmid-phase=1`을 `--gmid-phase=2`로 바꾼 것"으로 정하고, `--gmid-dod` 실행을 E4에 넣을지 브리핑에서 뺄지 하나로 맞춘다.

④ (관찰, E4 범위 밖) gate master에 커밋된 `workspaces/*/…instance.json` 두 개는 현재 생성기 산출과 다르다: 두 회로 모두 `topology_ref`가 아직 메인 절대 경로(DF-36 뒤 재생성 안 됨), `folded_cascode.instance.json`은 sizing 값까지 다르다(524줄 diff, 예: `_L_source` `L_role`→`L_role_derived`). 두 판의 생성 결과(without_topology_ref)는 같으므로 Phase 2 이전부터 오래된 추적 산출물이다. E4 판정은 새로 생성한 파일로 하므로 영향 없음. 백로그 후보.

⑤ (관찰) `--gmid-dod`에서도 xfailed 15가 그대로다(엄격 대상 0으로 보임). 기대인지 E5/N6.3 쪽에서 확인할 일, E4 판정 대상 아님.

## 5. 정리

- 복제본 reflog: clone → da03c0e → 7535799, 그 밖의 이동 없음. 복제본 status 마지막 = `!! .pytest_cache/`만.
- 메인 저장소 HEAD 7535799 불변, status 동일.
- `C:/g45` 삭제(산출 JSON은 판정 증거가 아니므로 보존하지 않음; 핵심 값은 §1 표).
