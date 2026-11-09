# T0 키트 6df4bd7 반영 독립 검증 -- review_t0_6df

작성 2026-10-07. 검증자 = 작성자가 아님. 대상: `draft_p3_t0.spec.md`, `t0_launch.sh`, `t0_briefs.md`와 각 `*.pre-6df.bak`의 차이, 그리고 `t0_at_6df4bd7.md`의 E1~E7.
실제 저장소는 `git -C`로 읽기만 했다. 측정은 `C:/g429`에서만 했다. clone은 `-c core.autocrlf=false --no-checkout`로 받고 origin을 지운 뒤 6df4bd7을 detach로 checkout했다.
TMP/TEMP/TMPDIR은 `C:/g429/tmp`로 두었다. 모래상자 실행은 `--repo /c/g429/iso --state /c/g429/st/state.txt --wt /c/g429/wtp`로 했다.
끝난 뒤 실제 저장소 상태: HEAD = gate/master = `6df4bd7`이고 reflog 최상단은 그대로다. `status`는 세션 snapshot과 같다. `_drafts/t0_launch_state.txt*`도 생기지 않았다.

## 판정

**B 0 · S 1 · minor 4.** 6df4bd7에서 기대값(hits 36, 잔여 3파일·7이름, exit 0)이 그대로 나온다. E1~E7 반영과 사실 문장도 모두 맞다.
S1(아래)은 plan N3.10 줄기가 기준 rev와 측정 rev 사이에서 바뀌면 shim-resid가 계약 11 표와 다른 잔여를 '표 그대로'(exit 0)로 판단하는 결함이다. 실측으로 재현했다.

## 1. shim-resid 실측(gate master 6df4bd7, 격리 복제본)

* `shim_import_reads.py iso 6df4bd7` → hits 36, 28파일. bound_by 분포: `from stick_diagram` 29, `import` 5, `from dataclasses` 1, `from topology_library` 1.
* `shim-resid` → `측정 hits 36, 잔여 3파일·7이름(서로 다른 6)`, `기준 hits 32, 잔여 3파일·7이름`. 판단은 '= 기준', **exit 0**. 잔여 7건은 계약 11 표(TL `math` / SR `_dc_replace`·`json`·`math`·`np`·nmcnr_predict_ac_response / DR `os`)와 같다.
* 기준 파일 무결성: `shim_import_reads.py iso 4a286f0`을 다시 돌린 결과가 `p3ud6_kit/out/shim_reads_4a286f0.json`과 `rev` 키 밖에서 같다(True). 그러니 지금 기준 파일은 drift가 없다.
* plan `mod_table`은 4a286f0과 6df4bd7이 같다. 10줄기이고 `stick_diagram` = MOD7이다. plan 파일은 두 rev 사이에 바뀌었지만(+4/-1) N3.10 표는 바뀌지 않았다.
* 이름을 코드에 박지 않았다. 스크립트 안에 파일·모듈·이름 리터럴이 없다. 줄기는 `il.mod_table(git show rev:plan)`에서 읽고, 기준은 `SHIM_BASE` 파일에서 읽는다. `"from %s"`는 `shim_import_reads.py`의 bound_by 형식과 맞물린 문자열일 뿐이다.
* `bash -n t0_launch.sh` 통과.

## 2. 적대 사례(모래상자, 각 exit 실측)

| 사례 | 입력 | 결과 | 맞나 |
|---|---|---|---|
| 잔여 항목 제거 | `os` hit 삭제 | `- 잔여에서 빠짐 … design_report.os`, exit 3 | 맞음 |
| hits 전부 비움 | `hits: []` | 7건 모두 '빠짐', exit 3 | 맞음 |
| 같은 이름, 다른 모듈(교체) | TL `math` hit의 module을 `sizing_recipe`로 바꿈 | `+ sizing_recipe.math` / `- topology_library.math`, exit 3 | 맞음 |
| 같은 이름, 다른 모듈(추가) | 위 hit를 하나 더 둠 | `+` 1, exit 3 | 맞음 |
| bound_by 변형 | Transistor의 bound_by를 `from stick_diagram.sub` / `from  stick_diagram`(공백 2)로 바꿈 | 잔여 +1, exit 3. 정확 일치라 보수적으로 동작함 | 맞음 |
| 실제 트리: `from stick_diagram import Transistor as _AliasT`(SR) → test `from sizing_recipe import _AliasT` | 합성 커밋 `29e40d8` | bound_by `from stick_diagram` → 잔여 밖 | 맞음(계약 11 (a)·(c)와 같은 근거) |
| 실제 트리: `import stick_diagram as _sdmod`(SR) → test `from sizing_recipe import _sdmod` | 같은 커밋 | bound_by `import` → `+ zz_adv_probe.py sizing_recipe._sdmod` | 맞음('from … import'로 받은 이름이 아님) |
| 실제 트리: test `from sizing_recipe import json as J` | 같은 커밋 | `al.name` = `json`으로 잡혀 `+ … sizing_recipe.json` | 맞음 |
| 실제 트리: test `import sizing_recipe as sr; sr.np` | 같은 커밋 | attribute hit → `+ … sizing_recipe.np` | 맞음(위 셋 합쳐 exit 3, 4파일·10이름) |
| **plan 줄기 변경** | 합성 커밋 `2f0b0f7` = 6df4bd7 + N3.10에 `MOD11 \| \`topology_library.py\`` 1행. SR·test는 그대로 | 측정 6이름, **기준도 6이름**(cur rev 줄기로 재계산), '표 그대로', **exit 0** | **틀림 -- S1** |
| 잔여 줄만 이동 | `os` line 24→99 | exit 0 | 허용 범위(줄 모양은 w1_lines 바이트 대조가 잡음) |
| 같은 잔여의 형태 변경 | `how` from-import→attribute | exit 0 | minor m3 |
| 같은 잔여를 다른 줄에서 한 번 더 | (file, module, name) 같은 hit 추가 | exit 0 | minor m3 |
| json `rev`를 다른 rev로 표기 | hits는 6df, `rev: 4a286f0` | exit 0, '측정 rev 4a286f0'으로 출력 | minor m2 |
| json에 `rev` 없음 / 깨진 json / 없는 파일 | -- | exit 1 / 1 / 1 | 맞음 |
| json rev가 R에 없음 | `rev: deadbeef…` | **exit 128** | minor m1 |
| `--shim-reads … conds` | -- | exit 2 | 맞음 |
| `shim-resid --shim-reads …`(옵션이 단계 뒤) | -- | exit 2 | 맞음 |
| `--shim-reads` 없이 `shim-resid` | -- | exit 1 | 맞음('입력 오류 1') |
| `--shim-reads` 값 빠짐 | -- | exit 2 | 맞음 |

## 3. 질문에 대한 답 -- 4a286f0 기준 파일과 대조하는 것이 계약 11 (c)에 맞나

* 계약 11 (c)는 **병합본** 판정(잔여 0)이다. 착수 0단계 (사)가 확인할 것은 그와 다르다. card 범위인 **계약 11 표(3파일·3줄·7이름)가 아직 정확한가**이다.
  card는 그 표의 측정 출처를 `shim_reads_4a286f0.json`으로 적는다(spec 95행 "base `4a286f0`에서 이 세 파일 3줄·7이름, 그 밖의 추적 `.py` 0", 204행).
  그래서 정본은 **표**이고, 기준 파일은 그 표의 대리값이다. 대리 비교는 다음 세 조건이 모두 성립할 때만 '표 그대로'와 같은 뜻이 된다.
  (i) 기준 파일이 4a286f0 측정 그대로다. (ii) 표 = 기준 잔여다(UD-6 측정으로 성립). (iii) 기준 잔여도 **기준 rev의 줄기**로 계산한다.
* 지금 구현은 (iii)을 어긴다. 기준 잔여를 **측정 rev의 plan 줄기**로 다시 계산한다(`routed`를 한 번 만들어 두 json에 같이 씀). 그래서 줄기가 바뀌면 기준도 같이 움직여 표와 어긋난 잔여를 '같음'으로 판단한다(2절의 `2f0b0f7` 재현).
  줄기가 줄어드는 경우도 같다. 그 줄기를 경유한 hit 수가 두 rev에서 같으면 양쪽이 똑같이 늘어 '같음'이 나온다.
  줄기가 바뀌면 (c)가 가리키는 대상이 바뀐 것이므로 표는 어차피 고쳐야 한다. 그러니 exit 3이 맞다.
* (i)은 검사하지 않는다. `_drafts`는 git 밖이라 기준 파일을 덮어써도 흔적이 남지 않는다. 다른 rev에서 같은 이름으로 다시 생성해도 마찬가지다. 스크립트는 기준 json의 `rev`가 4a286f0인지도, 내용 해시도 보지 않는다.
  지금은 drift가 없다(1절 재생성 대조 True). 그러나 '기준 파일 drift'는 조용히 통과한다.

**S1 고칠 방향**(작성자 몫이고 검증자는 제안만 한다):
기준 잔여는 기준 json의 `rev`에서 읽은 plan 줄기로 계산한다. 그리고 `mod_table(base rev) != mod_table(cur rev)`이면 차이를 출력하고 exit 3으로 판단한다.
drift 가드로는 둘 중 하나를 둔다. (a) 기준 json `rev`가 card 95행이 인용한 rev로 해석되는지 단언한다. (b) 더 강하게, `shim_import_reads.py`를 그 rev에서 다시 돌려 기준 파일과 `rev` 밖 대조한다. 이렇게 하면 파일을 믿지 않고 git에서 다시 만든다.

## 4. minor

* **m1** json rev가 R에 없으면 `g rev-parse` 실패로 exit 128이 난다. 머리 주석은 '입력 오류 1'이라고 한다. `rev=$(g rev-parse … ) || { …; return 1; }`로 맞추는 편이 좋다.
* **m2** 측정 json의 `rev`를 그대로 믿는다. kit-cmds는 `B=gate master`에서 만들라고 하지만 shim-resid는 `rev == gate/master`(또는 measured rev와의 관계)를 보지 않는다. 판단 줄에 rev가 찍히므로 사람이 볼 수는 있다. 단언 한 줄을 권한다.
* **m3** 비교 키가 (file, module, name)이라 `how`와 줄 수가 빠진다. 계약 11 표는 '3줄'이다. 최상위 import 줄은 w1_lines 바이트 대조가 잡는다. 함수 안 import나 attribute 읽기로 같은 이름을 다시 읽는 경우는 둘 다 놓친다.
  키에 `how`를 넣거나 (file, module, name)별 hit 수를 함께 대조하면 닫힌다. 영향은 작다.
* **m4** 게이트 코드(`import_layering`)를 `$R/tools/gates` 작업 트리에서 import한다. 머리 4행 원칙('게이트 캐시 절대 경로')과 다르다. 실제 모드에서는 실제 저장소 작업 트리가 다른 브랜치이거나 더러울 수 있다.
  plan은 rev에서 읽으니 판정 영향은 작다. `cache_dir`이나 `git show rev:tools/gates/import_layering.py`를 쓰는 편이 일관된다.
  (참고) 실제 모드 실행은 다른 단계와 같이 `lc_tmp_setup`으로 `_drafts/t0_launch_state.txt.tmpd`를 만든다. '읽기 전용'이라는 문구와 조금 어긋나지만 conds와 같은 동작이다.

## 5. 다른 편집의 사실 확인(E1~E7)

| 항목 | 실측 | 판정 |
|---|---|---|
| E5 backfill이 바꾼 것은 SD가 아니라 SR | `git diff --stat 2183f2e 6df4bd7 -- assets/*.py` = `sizing_recipe.py` 4+/5-뿐 | 맞음 |
| def 11711 | 2183f2e·6df4bd7 모두 `11711:def run_matching_safety_with_finger_growth(` | 맞음 |
| hunk 11758~11878(2183f2e 쪽) | `@@ -11758`, `-11768,2`, `-11799`, `-11878` | 맞음(t0_at 제안의 '11755'보다 적용문이 정확함) |
| E7 SR 5개 | `t0_facts.py` 123~124행 probe의 SR 이름 = `size_transistor`·`width_from_id_density`·`audit_vsb_consistency`·`_build_theta_evaluator`·`check_quasi_static`이고, 6df4bd7에서 5개 모두 `sizing_recipe.py` 최상위 def | 맞음(launch 260행, briefs 27행) |
| E6 meas_rev 132~137 | 편집 뒤 `t0_launch.sh` 132~137행 = `meas_rev()`. 제안의 127~132는 편집 전 기준이고, 적용문은 shim-resid 추가로 밀린 뒤 값으로 맞게 고쳤다 | 맞음 |
| E4 수집 1129 | `pytest --collect-only --gmid-phase=3`(iso 6df4bd7) = **1129 tests collected** | 맞음 |
| E1·E1'·E3 | spec 219·238~239·251~252행 문구가 제안과 같다 | 맞음 |
| E2 | launch 265~268행 주석, briefs 31~32행, 그리고 문구를 계산 단계 `shim-resid`로 구현했다(제안보다 강함) | 맞음. S1은 이 구현에 대한 지적이다 |
| E5 b26pre 행 | "-- `6df4bd7` 확인: B군, glob 0" 추가 | 맞음 |
| 다른 키트 줄 인용 | 남은 `t0_launch.sh` 줄 인용은 briefs 45행 하나뿐(현재 값). 나머지는 이력 문서 | 이상 없음 |

conds는 읽기 전용임을 확인했다. 모래상자에서 `--shim-reads … conds`는 exit 2로 거부되고, 일반 conds 경로는 바뀌지 않았다(diff에 conds 변경 없음).

## 6. 정리

모래상자 `C:/g429`는 삭제했다. 합성 커밋 `29e40d8`(별칭 형태)과 `2f0b0f7`(plan 줄기)은 모래상자 안에만 있었다.
