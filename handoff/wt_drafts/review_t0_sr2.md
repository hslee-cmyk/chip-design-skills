# T0 키트 sr2(shim-resid 재작성) 독립 검증 -- review_t0_sr2

작성 2026-10-07. 검증자는 작성자가 아니다. 앞선 검토는 review_t0_6df.md다.
대상은 diff 범위로 한정했다. `t0_launch.sh`와 `t0_launch.sh.pre-sr2.bak`의 차이(머리 30행 사용법 줄, 80행 `lc_tmp_setup` 분기, 97행 `SHIM_CITE_PY`, 267행 kit-cmds 주석, 282~409행 `shim_cite`·`shim_json_rev`·`shim_resid_body`·`stage_shim_resid`)를 보았다.
`t0_briefs.md` (사) 31~35행도 보았다(`.pre-6df.bak`와의 차이 가운데 sr2 문단).
실제 저장소는 `git -C`로 읽기만 했다. 측정은 `C:/g439`에서만 했다.
- 모래상자 gate: `gate.git`는 `file://` bare clone이고 `-c core.autocrlf=false`로 받았다. master는 `6df4bd7`이다.
- `iso`: 모래상자 gate에서 받은 clone이고 remote 이름은 `gate`다.
- 합성 커밋용 `gate2.git`·`iso2`는 따로 두었다.
- TMP·TEMP·TMPDIR은 `C:/g439/tmp`로 두었다. 실행은 모두 `env … /usr/bin/bash t0_launch.sh --repo … --state /c/g439/st/state.txt --wt /c/g439/wtp [--draft-spec …] --shim-reads … shim-resid`로 했다.

## 판정

**B 0 · S 0 · minor 2.**
- review_t0_6df의 S1과 m1~m4가 모두 닫혔다. 실측 근거는 아래 표에 있다.
- 6df4bd7 정상 실행 결과는 exit 0, 측정 hits 36, 기준 hits 32, 잔여 3파일·3줄·7이름(hit 7, 서로 다른 이름 6)이다. 기준 무결성(4a286f0 재생성 = 기준 파일)도 통과했다.
- `bash -n t0_launch.sh`가 통과한다(`launch_common.sh`도 통과).
- 작성자 13 사례의 목록 파일은 `_drafts`에서 찾지 못했다. 그래서 브리핑 항목(S1, m1~m4, 인용 정확히 한 번)에서 사례를 직접 다시 세웠다. 17개다.
- 그 밖에 적대 사례 7개를 더 돌렸다. 기대와 다른 결과는 minor n1 하나다.

## 1. 정상 실행(6df4bd7)

* `shim_import_reads.py iso 6df4bd7` 결과는 hits 36, 28파일이다(1분 31초).
* `shim-resid` 결과는 **exit 0**이다(2분 29초 -- 기준 재생성 포함).
  - 측정 줄: `측정 rev 6df4bd7: N3.10 줄기 10(...), hits 36, 잔여 3파일·3줄·7이름(hit 7, 서로 다른 이름 6)`
  - 기준 줄: `기준 rev 4a286f0: N3.10 줄기 10(...), hits 32, 잔여 3파일·3줄·7이름`
  - 잔여 7행은 계약 11 표와 같다. TL은 `math`, SR은 `_dc_replace`·`json`·`math`·`nmcnr_predict_ac_response`·`np`, DR은 `os`다. 모두 `from-import` x1이다.
* 기준은 spec 초안에서 읽는다. 95행의 `base \`4a286f0\``와 204행의 `p3ud6_kit/out/shim_reads_4a286f0.json`이다. 인용은 각각 하나다.
* 실행 뒤 `/c/g439/st`와 `/c/g439/tmp`는 비어 있다. 상태 파일, `.tmpd`, mktemp 잔여가 모두 없다(m4).

## 2. 사례 재현(브리핑 항목별)

| # | 사례 | 입력 | exit | 출력 요지 | 맞나 |
|---|---|---|---|---|---|
| 1 | 정상 | 6df4bd7 측정 | 0 | 위 1절 | 맞음 |
| 2 | `--shim-reads` 없음 | -- | 1 | `--shim-reads … 단계 이름 앞에 준다` | 맞음 |
| 3 | 측정 json 없음 | 없는 경로 | 1 | `없거나 비었다` | 맞음 |
| 4 | m1 측정 rev가 R에 없음 | `rev: deadbeef…` | **1** | `R에 없다(입력 오류)` -- 전에는 128이었다 | 맞음 |
| 5 | m2 측정 rev ≠ gate master | 6df 내용에 `rev: 4a286f0` | **1** | `측정 json rev 4a286f0 != gate master 6df4bd7` | 맞음 |
| 6 | 측정 json에 rev 없음 | -- | 1 | KeyError 뒤 `rev를 읽지 못했다` | 맞음 |
| 7 | 깨진 json | `{not json` | 1 | 같음 | 맞음 |
| 8 | spec 기준 rev 인용 0개 | '같은 정의'를 '같은 방식'으로 바꾼 사본 | 1 | `기준 rev 인용 []` | 맞음 |
| 9 | spec 기준 rev 인용 2개 | `… base \`36e170e\`` 한 줄 추가 | 1 | `['4a286f0', '36e170e']` | 맞음 |
| 10 | 기준 파일 없음 | 사본 옆에 p3ud6_kit 없음 | 1 | `기준 파일 … 없거나 비었다` | 맞음 |
| 11 | 기준 파일 rev ≠ 인용 rev | 기준 json `rev`를 `36e170e`로 바꿈 | 1 | `기준 파일 rev 36e170e != spec 계약 11 인용 rev 4a286f0` | 맞음 |
| 12 | 기준 파일 내용 drift(rev는 그대로) | 기준에서 `os` hit 삭제 | 1 | `재생성과 다르다(rev 밖, hits 31 vs 32)` | 맞음 |
| 13 | m3 `how`만 바뀜 | DR `os`를 from-import에서 attribute로 | **3** | `+ … os attribute` / `- … os from-import` | 맞음(전에는 0) |
| 14 | m3 같은 키를 다른 줄에서 한 번 더 | `os` hit를 300행에 복제 | **3** | `x1 -> x2`, `잔여 줄 수 … 1 -> 2` | 맞음(전에는 0) |
| 15 | m3 같은 줄에서 attribute로 다시 읽음 | `os` attribute hit 추가(줄 같음) | **3** | `+ … os attribute x0 -> x1`. 줄 수는 같다 | 맞음 |
| 16 | 줄 위치만 이동 | `os` 24행을 99행으로 | 0 | -- | 맞음(줄 모양은 w1_lines 바이트 대조가 잡는다는 설계와 같다) |
| 17 | **S1 줄기 변경(잔여 영향 없음)** | 합성 `27ddb9c` = 6df4bd7 + N3.10 `MOD11 \| \`zz_new_mod.py\``(아무것도 경유하지 않는 줄기) + 모래상자 gate_path. gate2 master = 이 커밋 | **3** | 측정 줄기 11, 기준 줄기 10, `+ N3.10 줄기 더해짐: zz_new_mod`. 잔여 7행은 같은데도 3 | **맞음 -- S1 닫힘**(줄기 비교만으로 거부한다) |

## 3. 적대 사례(검증자 추가)

| # | 사례 | 입력 | exit | 결과 | 맞나 |
|---|---|---|---|---|---|
| A1 | 기준 인용이 spec 디렉터리 밖을 가리킴 | spec 사본에서 두 인용을 `` `../evil/p3ud6_kit/out/shim_reads_4a286f0.json` ``로 바꿈 | 1 | 정규식은 백틱 바로 뒤 `p3ud6_kit/`와 16진 rev만 받는다. 그래서 `UD-6 기준 파일 인용 []`이 된다. `..`·절대 경로로 빠져나갈 길이 없다 | 맞음 |
| A1b | `_drafts` 밖의 위조 기준 파일 | spec 사본 옆 기준 파일에서 잔여가 아닌 hit 하나(`from stick_diagram`)를 지움. 잔여는 그대로다 | 1 | `재생성과 다르다(hits 31 vs 32)` | 맞음 -- 위치와 상관없이 내용은 git 재생성으로 증명된다 |
| A1c | `_drafts` 밖의 똑같은 기준 파일 | 바이트가 같은 사본 | 0 | -- | 맞음(내용이 재생성과 같으므로 위치는 판정과 무관하다. `--draft-spec`은 `--repo`와 함께만 쓸 수 있다) |
| A2 | 잔여 개수는 같고 이름이 다름 | TL `math`를 `cmath`로 | 3 | `+ cmath` / `- math` | 맞음 |
| A2b | 잔여 개수는 같고 모듈이 다름 | TL `math`의 module을 `sizing_recipe`로 | 3 | `+ sizing_recipe.math` / `- topology_library.math` | 맞음 |
| A3 | **줄기 추가 + 보상 읽기를 한 커밋에** | 합성 `7183a64` = 27ddb9c 위에서 MOD11을 `topology_library.py`로 바꿈(SR selftest의 `nmcnr_predict_ac_response`가 잔여에서 빠짐). 같은 커밋에서 SR selftest 24행에 `re`(SR이 `import re`로 받은 이름)를 더함. gate2 master = 이 커밋 | 3 | 측정 잔여가 다시 3파일·3줄·7이름(hit 7)이 되었다. 그래도 `+ N3.10 줄기 더해짐: topology_library`, `- nmcnr_predict_ac_response`, `+ re`로 거부한다 | 맞음 -- 개수 보상으로는 통과하지 못한다. 줄기와 키 두 겹에서 잡힌다 |
| A4 | 측정 json의 내용은 옛 rev이고 rev 키만 위조 | 4a286f0 측정 내용(hits 32)에 `rev: 6df4bd7` | **0** | `측정 rev 6df4bd7 … hits 32`, '표 그대로' | **minor n1** |
| A5 | 기준 파일 인용 2개 | `shim_reads_36e170e.json` 인용 한 줄 추가 | 1 | `UD-6 기준 파일 인용 [... 2개]` | 맞음 |

A3의 회로 확인: 측정 json(`shim_import_reads.py iso2 7183a64`)은 hits 37이다. stick_diagram 경유 hit가 그대로이고, `re` 1이 늘었으며, `nmcnr`는 hit로 남되 bound_by `from topology_library`라서 줄기 경유로 빠진다.

## 4. 코드 읽기(diff 범위)

* **S1**: `stems(rev)`가 rev마다 `git show rev:plan`에서 `mod_table`을 읽는다. 기준 잔여는 `sb`(기준 rev), 측정 잔여는 `sc`(측정 rev)로 계산한다. `sc != sb`이면 `bad`다(17·A3에서 실측).
  기준 rev와 파일은 `shim_cite`가 spec 초안에서 읽는다. rev 인용은 정확히 한 개를 요구한다. 파일 인용은 `set`으로 중복을 지운 뒤 한 개를 요구한다(95·204행에서 같은 파일을 두 번 인용해도 하나로 센다 -- 의도와 같다).
  기준 무결성은 세 단계로 본다. (1) 기준 json `rev`를 rev-parse한 값 = 인용 rev를 rev-parse한 값. (2) `shim_import_reads.py`를 그 rev에서 `$t`로 재생성한다. (3) `rev` 밖 dict가 같다. 스크립트에 박힌 파일, 모듈, 이름, rev 리터럴은 없다.
* **m1·m2**: `rev-parse --verify --quiet … || exit 1`, 그리고 `[ "$cur" = "$H" ] || exit 1`이다(4·5에서 실측).
* **m3**: 키는 `Counter((file, module, name, how))`와 파일별 `len(set(line))`이다(13·14·15에서 3, 16에서 0).
* **m4**: Python은 `sys.path.insert(0, C)`로 `C=$(cache_dir)`에서 `import_layering`을 읽는다. `[ "$1" = shim-resid ] || lc_tmp_setup`이고, `mktemp -d` 하나를 끝에 `rm -rf`로 지운다(실측: st·tmp가 비었다).
* exit 규약: 부분 셸 `( trap … ERR; set -e; shim_resid_body )`이고 바깥은 `set +e … set -e`다. 결과가 0·1·3이 아니면 1로 바꾼다. 판정 3·1에서는 바깥 ERR 표지가 찍히지 않는다(로그 확인). 예상하지 못한 실패는 안쪽 trap이 줄 번호를 찍는다.
* briefs (사) 31~35행은 코드와 같다. 기준을 인용에서 읽는다는 것, 줄기를 rev별로 비교한다는 것, 1/3 규약, 키 정의가 모두 맞는다.

## 5. minor

* **n1(측정 json 내용 미검증)**: 측정 json은 `rev`가 R에 있는지와 gate master와 같은지만 본다. 내용은 믿는다. A4(옛 rev 측정 내용 + rev 키 위조)가 exit 0이었다. 6df4bd7에서는 잔여가 우연히 같아서 판정이 틀리지 않았다.
  하지만 측정 파일이 섞이거나(다른 rev의 scratch 파일) 손으로 고친 경우는 잡지 못한다. 기준 쪽에는 이미 재생성 대조를 들였다.
  제안: 측정 쪽도 같은 대조를 하면 대칭이 된다. `shim_import_reads.py R $H`를 `$t`에 재생성해 `rev` 밖에서 대조하는 방법이 있다. 아니면 `--shim-reads` 입력 없이 shim-resid가 직접 잰다. 비용은 약 1분 30초가 더 든다. 영향은 작다. 측정 직후 같은 사람이 넘기는 파일이다.
* **n2(문구)**: briefs 34행은 "기준 재생성 때문에 1분쯤 걸린다"라고 쓴다. 실측은 재생성 1분 31초, shim-resid 전체 2분 29초다(모래상자, 단독 실행). "2분 30초쯤"이 실측에 맞다.

(참고 -- 결함 아님)
- 실제 모드의 `cache_dir`는 다른 단계와 같다. `$R/tools/gates`의 role_paths로 `ensure_cache`를 부르고, `<git-common-dir>/gmid-gate-cache`를 만들거나 상한대로 정리할 수 있다. 머리 30행의 '읽기 전용'은 작업 트리·상태 파일 기준의 표현이다.
- 기준 파일 이름의 16진 값과 인용 rev가 같은지는 보지 않는다. 내용 rev와 재생성으로 증명하므로 판정에 영향이 없다.

## 6. 정리

* 실제 저장소: HEAD = gate/master = `6df4bd7`이다. reflog 최상단과 `status --porcelain` 해시는 시작 때와 같다. `_drafts/t0_launch_state.txt*`는 생기지 않았다.
* 절차 고지: 첫 명령에서 `cd /c/g439`를 한 번 실행했다(모래상자 디렉터리, 출력 없음). 그 뒤 명령은 모두 절대 경로와 `git -C`로 했고, 실제 저장소에는 영향이 없었다(위 확인).
* 합성 커밋 `27ddb9c`·`7183a64`는 모래상자 `gate2.git`·`iso2` 안에만 있었다. 모래상자 `C:/g439`는 삭제했다.
