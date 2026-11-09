# LM-1d 실행 결과 독립 판정 (card 20261106-lm1d, interface §6 V-1~V-10)

- 판정 2026-11-06, 판정자 = 독립 agent(작성자 아님). 판정 대상 = WB-1 브랜치 `role/code/20261104-wb1` 커밋 `5072f6dd`(부모 `b926bbc1`).
- 격리 복제본: `git clone --no-hardlinks --no-local <wb1-c worktree> C:/Users/HSLEE/AppData/Local/Temp/la1s_lm1d_ver24/iso`, `remote remove origin`, HEAD = `5072f6dd`(core.autocrlf = true).
- 판정 폴더 = `C:/Users/HSLEE/AppData/Local/Temp/la1s_lm1d_ver24/`(`v2/`·`v2tmp/`·`v3/`·`v4/`·`out/`·`scripts/`). 판정자 측정 스크립트 = `scripts/judge.py`, `scripts/judge2.py`, 출력 = `out/judge_out.txt`, `out/judge2_out.txt`, `out/v{2,3,4}_stdout.log`, 캐시 전후 = `out/cache_{before,after}*.txt`.
- 환경: `C:\Python314\python.exe -P`, `OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8`, `PYTHONPATH=<iso>/skills/analog-gmid-design`. 실행 전 MemFree 6.13 GB(3.7 GB 넘음).
- **돌린 범위**: V-2·V-3·V-4 스크립트 재실행(card 스크립트, ngspice 0), 판정자 읽기 전용 측정(V-1·V-5·V-7·셀 분석), git 읽기(V-6·V-6b·V-8). **안 돌린 것(통과로 세지 않음)**: ngspice 재실행, pytest, 13회로, LM-1e 적재.
- `<root>` = `C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2`, `<V>` = `<root>/verification/midpoints_w`, `<D>` = `<root>/verify_midpoints_w`. `<root>` 아래 판정자 쓰기 0(V-3 재실행이 멈췄다면 `<V>/record_stop.json`을 쓸 수 있는 구조였으나 멈추지 않았고 파일 없음 확인).

## 결론

**Major 0, minor 4, 관찰 3.** 데이터·출처 기록은 card 정의대로 재현된다(n/N = 120/120, 대조 784셀 문턱 초과 0).

## V-1~V-10 결과

| # | 결과 | 근거(재측정) |
|---|---|---|
| V-1 | 충족 | `<D>` npz 30개, 출처 기록 `files` 30개, raw sha256 30/30·bytes 30/30 일치. `<D>` 다른 파일 = `generation_progress.log`뿐. 출처 기록 n/N = 120/120 |
| V-2 | 충족 | 재실행 `v2/compare.json`이 `<V>/compare.json`과 **원 바이트 그대로 같음**(repack_sha256도 같음: 두 kind 모두 `1acaf009…f503` -- 예외 칸이 이번엔 다르지 않았음). 출처 기록 `compare` = compare.json. 재실행 stop = None |
| V-3 | 충족(비교 기준 주의, minor m3) | 재실행 출력 sha256 `2a334b47…1bfa` = **git blob**(`git show 5072f6dd:…provenance.json`) = 작성 worktree 파일. 격리 복제본 작업 파일(autocrlf=true checkout, CR 12044개) sha `9b5164ef…f929`와는 다름 -- 줄끝 변환만의 차이(index `i/lf`) |
| V-4 | 충족(stub sha는 대체 판정) | `--verify` 재실행 OK, N = 120, cells 784, per kind nmos 18·pmos 12. `combos`·`n_expected`·`n_cells_expected`·`mids_um`·`min_finger_w_m`·`manufacturing_grid_m`·`pdk_decl_sha256`·`lut_manifest_sha256`·`expect`·`s0.generator`·`s0.ngspice`·`s0.l_grid.sha256` 같음, widths 두 파일 바이트 같음. `stub_sha256` 다름(`13e68c43…` 대 plan `33315719…`) → 배열 L·VGS·VDS·VS `array_equal` 참, `meta_json`은 **`L_source.path` 한 칸만 다름**(작성 worktree 경로 대 격리 복제본 경로; sha256·sha256_lf·key·axes_source 같음) -- minor m4 |
| V-5 | 충족 | 손 표본 nmos w_key 84(0.42 µm, 가장 좁음)·1400(7 µm, 가장 넓음)·pmos 330(1.65 µm) × L_mid 4: W·VGS/VDS/VS 축 같음, L = 승인 중점, meta 7칸 같음, generator sha·ref_npz sha 같음, model_bin_bounds 4값이 두 앵커 bin과 rel 1e-12 안 같음·모델 이름 셋 같음, ID·GM·VDSAT 유한. 진행 로그 시간 줄 120·`cached` 0(그 밖 30줄 = `saved …` 줄, 2줄 `# start`, 2줄 `# done`). 격자 정수 33·170·350·650 |
| V-6 | 충족(대상 커밋 주의) | `git diff --name-only dcd54095..5072f6dd` = spec·interface card 2 + 출처 기록 1 + `<SC>/` 스크립트 3. `E/`·`A/lut_v2_location.json`·topology 0. 문언의 `dcd54095..card/lm1d`는 card/lm1d가 데이터 커밋을 갖지 않아(아래 m1) `5072f6dd`로 쟀다 |
| V-6b | 충족 | 병합 전: `dcd54095` ⊑ card/lm1d 참. 병합 직후(판정자 재확인): `56f64edb` ⊑ `role/code/20261104-wb1` **참**, `56f64edb` ⊑ master(`d3782917`) **거짓**, `5072f6dd` ⊑ master 거짓. `b926bbc1` tree = `56f64edb` tree(`40de29be…`) -- 데이터 생성 base 내용 = card 머리 |
| V-7 | 충족 | `preexisting_files.json` 54개 모두 있고 raw sha 같음(바뀜·없어짐 0). 새 파일 41개(= `<V>` 10 + `<D>` 31), `<V>`∪`<D>` 밖 0. `<V>`에 interface §1 목록 밖 `compare.stdout.log`·`gen_t0.txt`가 있으나 `<V>` 안(허용 자리) |
| V-8 | 충족 | 스크립트 셋 import = 표준 라이브러리·numpy·`gmid_engine.core`(BoundedLRU, file_sha256, read_pdk_decl)·`gmid_engine.lut`(LutSpec, load_lut_set, resolve_lut_location, widths, LutMemo, midpoint_l_bin_checks, tol_v_table) + 같은 폴더 `plan_midpoints`. log·exp·gm/ID·보간 식 grep 0 -- 대조 식은 |new−old|·비율·짝짓기·부호 셈뿐(`midpoint_l_bin_checks`·`tol_v_table` 출력 그대로). 엔진 소스 변경 0. 공용 표 캐시 `lut_table_cache`: 파일 목록·mtime(`ls --full-time` 210줄)·폴더 mtime 실행 전후 같음. 판정용 `--cache` 폴더는 실행 뒤 지워짐. test·gate 등록 0(`git grep` = 출처 기록의 `plan_command` 문자열만) |
| V-9 | 충족 | 숫자 리터럴: `round(·, 6)`·`1e6`·`1e-6` 단위 환산, `SHOWMOD_REL_TOL = 1e-12`(생성기 :129 인용), VS 확장 `round(·, 9)`(생성기 :259·:264 같은 식), `ANCHORS_PER_BIN = 2`(정의, 관찰 o3), `LutMemo(point=256, curve=256, root=256)`(용량 -- 값 영향 0), `failures[:200]`(멈춤 기록 자르기). 폭·L·문턱·기대 수 리터럴 0(기대 = `--expect`, 784 = plan에서 셈) |
| V-10 | 의견 기록 | 아래 |

## 재측정 수치

- **n/N = 120/120**(V-3 재실행 `OK record n=120 N=120 files=30`, V-4 N = 120). 30 슬라이스 = nmos 18(0.42~7 µm) + pmos 12, 슬라이스마다 앵커 2개 bin 4개(중점 0.165·0.85·1.75·3.25 µm).
- **관문 G-a~G-h**: 재실행에서 실패 0(record_stop.json 없음). 손 표본 3 슬라이스 × 4 중점 = 12 조합 G-a·G-b·G-c·G-d·G-e 독립 확인, G-f = V-7, G-g = compare stop None, G-h = 시간 줄 120·cached 0.
- **대조(기준 폭 w_key 1000 = 5 µm, 784셀)**:

| kind | 셀 | 둘 다 None | 한쪽 None | tol None(차 정의) | 정의 셀 | 새>옛 | 새<옛 | 같음 | 최대 차 V | 최대 차/문턱 | 최소 새 tol_V |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nmos | 392 | 8 | 0 | 0 | 384 | 230 | 154 | 0 | 6.3928e-7 | 3.987e-5 | 5.675e-3 |
| pmos | 392 | 8 | 0 | 0 | 384 | 174 | 210 | 0 | 2.5655e-7 | 3.154e-5 | 4.476e-3 |

  최대 차·비율은 셀 값에서 다시 셈해 기록값과 같음. 문턱 초과 0.
- **둘 다 None 16셀의 원인**: 모두 VDS 격자 k = 0(VDS = 0 V), kind마다 앵커 8개 × 1. 새 기준 폭 파일에서 VDS = 0의 |ID| 최댓값 = 0, GM 최댓값 = 0(nfet·pfet) → 엔진 정의(`midpoint_checks.py:12`: 점 = 중점 on(ID > 0, GM > 0) ∧ 두 앵커 on)의 점 집합이 비어 값이 None. 같은 셀의 tol_V도 None(8/8, 같은 k = 0). 물리적으로 VDS = 0이면 드레인 전류 0이라 ln ID 기반 지표가 정의되지 않는 것이 맞고, 옛 값도 같은 이유로 None이다. spec 완료 조건 3대로 **통과로 세지 않고 따로 셈**(정의 셀 768 = 784 − 16만 문턱 판정) -- 맞다. 이 셀은 LM-1e 정의 불능 갈래의 입력이다.

## Major

없음.

## minor

- **m1 (절차 -- card와 다름, 결과 동등)**: interface §7·spec '절차'는 데이터 커밋을 `card/lm1d`에 두고 독립 판정 뒤 오케스트레이터가 WB-1에 병합하게 했다. 실제는 `card/lm1d` = `56f64edb`(데이터 커밋 없음)이고 데이터 커밋 `5072f6dd`가 WB-1 브랜치에 판정 전에 직접 들어갔다(base = `b926bbc1` 병합, tree = card 머리와 같음). 표 #24(master에는 WB-1 + LM-1e 통합 병합으로만)는 지켜짐(`5072f6dd` ⊑ master 거짓). 데이터·판정 결과에는 영향 없음. 다만 '판정 전 WB-1 착지'는 순서 위반으로 기록하고, 판정이 실패했다면 WB-1에서 되돌리기 커밋이 필요했을 경로다. Major로 올리지 않은 이유: O-229 3 Major 목록(물리·graph·fail-open·기준 약화·엔진 누출·범위·test 실패) 어느 것에도 해당하지 않고 산출물이 card 정의와 바이트 단위로 재현됨. 오케스트레이터는 card/lm1d 브랜치를 그대로 둘지(데이터 커밋 없는 card 머리) 정리할지 정한다.
- **m2 (출처 기록 `commands`)**: interface §4 '`commands`: S2 두 호출 전문, 인자 실제 값'을 plan.json `s2_commands`(S1이 만든 명령)에서 옮긴다 -- 실행 때 잡은 argv가 아니다. 데이터 쪽 대조(npz meta `ref_npz_sha256` = stub, 진행 로그의 (장치, W, L) 120쌍 = plan, `# start` 블록 2개)로 두 호출이 그 명령과 맞음을 간접 확인했으나 `--jobs 4`는 데이터로 확인할 수 없다(값 영향 없음). plan.json의 interface 목록 밖 키(`s2_commands`, `per_kind_widths`, `mids_um`, `units`, `root`, `data_dir`, `record_dir`, `pdk_root`, `pdk_decl`, `lut_manifest_sha256`, `repo`, combos의 `slice_device_meta`·`anchor_idx`)는 interface가 금지하지 않고 출처 기록 칸을 채우는 데 쓰여 card와 어긋나지 않는다. LA-1 재점검 입력.
- **m3 (CRLF)**: 출처 기록은 LF로 쓰이고(index `i/lf`, 작성 worktree `w/lf`), autocrlf = true checkout에서는 작업 파일이 CRLF가 된다. 출처 기록 자체의 sha를 대조하는 곳은 없고(엔진 reader 0, 위치 선언 대상 아님) V-3은 blob 바이트로 같음 -- 판정 영향 없음. `.gitattributes`로 이 파일을 `-text`/`eol=lf`로 둘지는 LA-1 재점검 입력.
- **m4 (V-4 stub meta 경로)**: stub `meta_json.L_source.path`가 실행 경로 절대값이라 격리 복제본 재실행이 stub sha를 바이트로 재현하지 못한다(배열·sha256 같음). card V-4가 둔 대체 판정으로 충족. 재현성 개선(상대 경로)은 LA-1 재점검 입력.

## 관찰

- **o1 (부호별 셀 수)**: 새>옛 nmos 230·pmos 174, 새<옛 154·210, 같음 0. 새 생성기 차는 문턱의 최대 4e-5배(상대 1e-5 수준)로 옛 기준 생성기 중점과 사실상 같다.
- **o2 (물리 관찰, 판정 기준 아님)**: nmos 슬라이스 다수에서 중점 L의 |ID|가 두 앵커 |ID|보다 큰 점이 있다(예: 7 µm L 0.165 µm 1094/23520점, VGS 0.075~0.375 V, 앵커 범위 밖 최대 상대 38%; 0.42 µm L 0.165 1492점 7.9%; pmos 0점). 같은 모델 bin 안의 L 비단조(짧은 채널 bin의 binning 계수 효과로 보임 -- 원인은 재지 않음)로, 생성기·데이터 결함이 아니라 SPICE 모델 사실이며 그 셀의 L 보간 오차(tol_V)를 크게 만든다. 판정자 측정 `out/judge2_out.txt` `OUT` 줄. LM-1e 적재 뒤 tol_V 값과 LA-1 재점검 입력.
- **o3 (정의 사본)**: `ANCHORS_PER_BIN = 2`는 엔진 `midpoint_checks._PAIR = len(LINEAR_CONDITIONS)`의 정의를 숫자로 다시 적은 것(엔진 이름이 비공개라 import 안 함). 대조 스크립트가 엔진 rows 수와 자기 bin 수가 다르면 멈추므로 fail-closed. 장치 ↔ kind 셋째 사본과 함께 LA-1 재점검 입력.

## V-10 판정자 의견

1. **'생성 1회(호출 둘)'**: 진행 로그에 `# start` 2개(nfet 101.5 s, pfet 53.6 s, 합 155.1 s), 시간 줄 120, cached 0, 같은 생성기 sha. 체크포인트 재사용·재실행 흔적 없음 → O-242 '1회'를 kind별 두 호출로 읽은 것과 맞다.
2. **스크립트 셋의 O-229 4 예외**: 조건(card 폴더 안, 밖 import 0 -- 엔진 공개 이름 + 같은 폴더 공용 함수, test·gate 등록 0, 엔진 식 재구현 0) 모두 충족. 스크립트끼리 import(compare·record → plan_midpoints)는 같은 card 폴더 안이라 '밖 import 0'과 어긋나지 않는다.
3. **장치 ↔ kind 셋째 사본**: 값이 `E/tests/lut/conftest.py:47-48`과 같음(확인). 출처 줄 주석 있음. 정리는 LA-1 재점검.

## graph 규칙 점검

- 계산식별 정본: 대조값 = `midpoint_l_bin_checks(...).rows[*].id_equivalent_v`, 문턱 = `tol_v_table(...).cells[i][k].id_equivalent_v` -- 엔진 정의 함수 출력 그대로(정본 우회 재계산 0). 스크립트 안 식은 계획이 정의한 대조량(|new−old|·비율·부호 셈)뿐.
- 새 graph 필드 0(데이터 card), 소비자 판정 해당 없음. 출처 기록은 출력 전용(엔진 reader 0).
- graph 밖 저장 자리: 엔진 쪽 0(엔진 변경 0). 대조 실행의 U-87 디스크 표 캐시는 빈 임시 폴더로 돌렸고 실행 뒤 지워짐, 공용 캐시 전후 같음. LutSet A·B는 적재 순서대로 하나씩(동시 보유 없음).
- KVL·KCL 관계 적용: 해당 없음(엔진 계산 변경 0, 데이터는 ngspice `.dc` 산출).
- 수치: 필드 수 0 / 소비자 0인 새 필드 0 / 정본 우회 의심 0 / KVL·KCL 관계 미적용 0 / graph 밖 저장 자리 0.

## 정리

- 판정 뒤 python·ngspice 프로세스 0(`tasklist`). 커밋 0(이 파일은 오케스트레이터가 기록 자리를 정함).
