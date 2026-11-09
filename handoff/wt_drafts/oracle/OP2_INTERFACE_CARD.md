# oracle-portability OP-2 (오라클 기술자 + 입력 형식 변경) interface card (card id `op2`)

- 작성: 2026-10-16. 읽기 전용 실측과 card 초안만 담았다. 오라클·엔진·test·git 브랜치는 고치지 않았다.
- **card base = `5fea301`**(master, OP-0 design v0.2.6 병합, 사용자 O-12).
- design 근거: `docs/02-design/features/oracle-portability.design.md` v0.2.6 §10.1~§10.3(`mc`·`diagnostic` 제외), §7(OP-2 몫), §7.2 1·2단계(8단계 첫머리는 `[J-5]`), §11.1~§11.4, §15.4 1064행, §18.1 1167·1169행, §18.2 1183·1184·1187행, §20 OP-2 행. 계획 v0.6.6 N5.1 OP-2 행(381행). 사용자 결정 O-1(D-5·D-9)·O-3·O-6 D-b·O-11·O-12, T-31·T-33.
- **test 작성 주체는 소스를 보지 않고 이 문서(2·3절)만 쓴다.** 기대값은 이 문서, 계약 문서(`E/lut/CONTRACT.md` 1.8), JSON 파일(엔진 선언·위치 선언·기술자), 손계산에서만 만든다. 엔진·오라클 코드를 import해 기대값을 만들지 않는다(오라클 test는 엔진 import 금지).
- 경로 접두: `O/` = `skills/analog-gmid-design/tools/spice_oracle/`, `E/` = `skills/analog-gmid-design/gmid_engine/`, `A/` = `skills/analog-gmid-design/assets/`.

> **멈춤**: `[J-n]` 표시는 design이 아직 정하지 않은 칸이다(spec card 1.8). 그 칸에 기대는 test는 J가 닫힌 개정판이 나오기 전 쓰지 않는다. 3절 표의 '착수' 칸이 `J-n 뒤`인 test가 그것이다.

---

## 2. interface card (공개 계약)

### C0. 오라클 기술자 파일 (`O/descriptors/sky130.oracle_descriptor.json`)

```text
{
  "schema": "oracle_pdk_descriptor/1",
  "engine_decl": {"path": <A/sky130_pdk_decl.json 을 가리키는 경로 [J-4 기준]>, "sha256": <그 파일 sha256 [J-15]>},
  "extra_sources": {<key>: {"path", "sha256", "base" [J-4], "provenance": <비어 있지 않은 문자열>}},   # 엔진 선언 sources 에 없는 파일만
  "lut_record_root": {"location_decl": {"path": <A/lut_v2_location.json [J-4]>, "sha256"}, "key": "pdk_root"},
  "lut_file_roles": [],                                   # OP-2 는 빈 목록(내용은 OP-3)
  "model_family": <문자열>,
  "kinds": {"nmos": {...}, "pmos": {...}},                # 각 kind: call_form, name, inner_device, geometry_unit, parallel_multiplier, includes, polarity
  "corners": {"names": [...], "select": {...}},
  "temperature": {...},                                   # [J-3]
  "diffusion": {...}                                      # [J-2]
}
```

- 칸 모양(design §10.2): `kinds.<kind>.call_form` ∈ {`"subckt_wrapper"`, `"model_direct"`}, `name` = `{"value": str}` 또는 `{"expr": <엔진 선언 식 형식>}`, `inner_device` = `{"expr": ...}` 또는 `null`, `geometry_unit` = `{"source": <엔진 선언 quantity 키>}` 또는 `"si"`, `parallel_multiplier` = `{"to": [{"target": "instance_multiplier"} | {"target": "model_param", "name": {"value"} | {"expr"}}], "source": <원본 근거>}`, `includes` = `[{"source": <키>, "corner_section": <선택>}]`, `polarity` ∈ {`"n"`, `"p"`}.
- OP-2 기술자에는 `mc`·`diagnostic` 칸이 없다(OP-5가 더함). 그 키가 있을 때의 동작 = `[J-11]`.
- **엔진 선언 `sources`의 파일은 source 키로만 가리킨다** -- 기술자 안에 그 파일의 경로·sha256이 다시 나오지 않는다. `extra_sources`에는 엔진 선언 `sources`에 없는 파일만 있다(sky130 사례: pmos가 include하는 `sky130_fd_pr/models/parameters/lod.spice`).
- sky130 `geometry_unit`은 kind마다 엔진 quantity `mismatch_slope_geometry_unit_m`을 source로 가리키고, `parallel_multiplier.to`는 인스턴스 배수와 모델 파라미터 `mult` 둘을 가리킨다(design §10.3 618~619행 안, **값은 사용자 확인 뒤 확정**). OP-2에서 이 두 칸은 선언만 되고 소자 줄·거부에 쓰이지 않는다(OP-3).
- 기술자 파일은 엔진 suite·오라클 suite 어디서든 JSON으로만 읽힌다.

### C1. 기술자 읽기 API (`O/core/descriptor.py`) -- **`[J-4]`**

- 공개 함수 이름·인자·반환 자료형, 오류를 예외로 낼지 반환 값으로 낼지, 오류 객체에서 `code`·`detail`을 읽는 방법은 design 개정이 정한다. 개정판이 이 절에 서명을 적는다.
- 이미 정해진 성질(design): 인자로 **환경 매핑**을 받는다(모듈이 `os.environ`을 직접 읽지 않는다 -- `E/lut/CONTRACT.md` 1.8 258~259행과 같은 규칙). 엔진을 import하지 않는다. 처음 걸린 하나의 오류만 낸다(C2 순서). 시뮬레이터를 부르지 않는다.
- 성공 결과는 적어도 (i) 푼 LUT 기록 뿌리 경로와 그 출처 표기(`"env:<이름>"` 또는 `"config_default"`) (ii) kind별 기술자 값에 접근하는 길을 준다(이름은 `[J-4]`).

### C2. 기술자 검사 순서와 오류 코드 (design §7·§7.2 2단계)

처음 걸린 하나만 낸다. 순서: **스키마 → 참조 sha256 → 원본 중복 → 참조 파일 형식** (→ `[J-5]` 기록 뿌리 교차 검사).

| 순 | 경우 | 코드 | `detail` |
|---|---|---|---|
| 1 | 기술자 JSON이 `oracle_pdk_descriptor/1` 스키마 위반: 필수 칸 없음, 칸 형식 틀림, 닫힌 키 집합 밖 키, `extra_sources.<key>.provenance` 비어 있음, `schema` 값 다름 | `descriptor_schema_invalid` | JSON 포인터 + 어긴 규칙 |
| 2 | 기술자가 가리키는 파일의 sha256 불일치 또는 파일 없음 -- 대상: 엔진 선언 파일, 기술자가 쓰는 엔진 `sources` 키의 원본(그 sha256은 엔진 선언에 적힌 값), `extra_sources` 파일, 위치 선언 파일. **요청 종류와 무관하게 이 단계 한 곳에서 전부 대조** | `pdk_descriptor_stale` | `{ref, path, expected_sha256, actual_sha256}`, `ref` ∈ `"engine_decl"`, `"engine_source:<key>"`, `"extra_source:<key>"`, `"lut_location_decl"`. 파일 없으면 `actual_sha256 = "missing"` |
| 3 | 같은 원본 파일이 엔진 선언 `sources`와 `extra_sources` 두 곳에 있음(경로 같음 **또는** sha256 같음) | `descriptor_source_duplicated` | (design 미정 -- 단언은 코드만) |
| 4 | 위치 선언 파일 자체의 형식 오류: `gmid_lut_location/1` 형식 아님, `pdk_root` 칸 없음, `pdk_root`의 `env`·`default` 둘 다 없음 | `lut_location_decl_invalid` | `{item, why}` |
| (8) | `[J-5]` 기록 뿌리 아래 파일이 LUT 기록과 다른 PDK 트리 | `lut_record_root_mismatch` | `{path, recorded_sha256, engine_source_key, actual_sha256 \| "missing"}` |

- 1과 4는 다르다: 기술자 자체가 틀리면 1, 기술자는 맞고 가리킨 위치 선언 파일이 틀리면 4.
- 2의 sha256은 파일 디스크 바이트의 sha256이다(줄 끝 처리 = `[J-15]`).
- `pdk_root` 칸이 없으면 엔진은 LUT meta로 돌아가지만 오라클은 4로 거부한다(의도된 엄격, O-11).

### C3. LUT 기록 뿌리 해석 (`lut_record_root`, 규칙 = `E/lut/CONTRACT.md` 1.8 256~261행)

위치 선언의 `pdk_root = {"env": <이름>, "default": <폴더>}`와 넘긴 환경 매핑 `env`로:

| 경우 | 결과 경로 | 출처 표기 |
|---|---|---|
| `env[이름]`이 있고 비어 있지 않음 | `os.path.abspath(env[이름])` | `"env:<이름>"` |
| `env[이름]`이 빈 문자열이거나 없음, `default` 있음 | `os.path.abspath(default)` | `"config_default"` |
| 둘 다 없음 | -- | `lut_location_decl_invalid` |
| `pdk_root` 칸 자체 없음 | -- | `lut_location_decl_invalid`(LUT meta 절대 `pdk_root`로 돌아가지 않음) |

- LUT meta의 절대 `pdk_root`는 읽지 않는다.
- sky130 사례 위치 선언 `A/lut_v2_location.json`: `pdk_root = {"env": "GMID_PDK_ROOT", "default": "C:/pdk/sky130_fd_pr"}`.

### C4. X-13 엔진 쪽 계약 (엔진 suite에서 도는 test, 위치 `[J-6]`)

- (a) `A/sky130_pdk_decl.json`의 sha256 = 기술자 `engine_decl.sha256`.
- (b) 엔진 선언 `sources`의 파일 집합 ∩ 기술자 `extra_sources`의 파일 집합 = ∅ -- 경로로 한 번(엔진 선언 `pdk_root` + `sources.<k>.path` 대 기술자 `extra_sources` 경로 `[J-4]`), sha256으로 한 번.
- 엔진·오라클 코드를 import하지 않고 JSON 두 파일만 읽는다(계획 8a 예외 첫째). 엔진 소스·기존 엔진 test 파일은 바뀌지 않는다.

### C5. 새 오라클 입력 형식 (`O/oracle_input.schema.json`, design §11.1)

```text
"process": {
  "descriptor": {"path": <기술자 경로 [J-4]>, "sha256": <기술자 파일 sha256>},
  "lut_npz": <경로>,
  "corner": <선택>, "temp_c": <선택>
}                                             # 이 밖의 키는 거부(additionalProperties: false)
"simulator": {"adapter": <이름>, "exe": <실행 파일 경로>, "options": {<키>: <값 문자열>}}
"output_reference": ...                       # [J-8]
```

- 삭제: `process.models`(`subckt`·`includes`·`op_probe`·`polarity`), `process.ngspice_exe`, `process.diffusion`, `process.lut_reference_width_m`, `process.provenance`, `testbench.options`(→ `simulator.options`). 최상위 `provenance`와 소자별 `devices[].diffusion`은 그대로.
- `testbench`의 다른 칸(`dc_choke_H`, `ac_couple_F`, `ac`, `loop_dc_choke_H` 등)과 그 밖 최상위 칸은 그대로.
- 최상위 `schema` 값 = `[J-10]`.
- `simulator.options`의 키는 어댑터 방언(첫 조합: `gmin`·`reltol`·`abstol`·`vntol` 등)이고 값은 문자열이다(옛 `testbench.options`와 같은 모양).

### C6. 옛 형식 거부 (design §11.3, README C13 방식)

- `process.models` 또는 `process.ngspice_exe`가 있는 입력은 `oracle_input_format_old`로 거부한다. 이중 지원 없음.
- 관찰: netlist·run·compare 진입점이 **반환 2**로 끝나고 산출물(넷리스트·meta·sim·compare 파일)을 하나도 쓰지 않으며 시뮬레이터를 부르지 않는다. `oracle_input_format_old`가 출력 어디에 어떤 꼴로 나오는지 = `[J-10]`.
- `process`에 정의 밖 키(예: `lut_reference_width_m`)만 있고 옛 형식 표지가 없으면 스키마 위반(C13 반환 2)이다(코드 이름 `[J-10]`).
- `O/smoke/`의 옛 형식 입력 3개는 고정 자료이고 이 규칙으로 거부된다.

### C7. 온도·코너 해석 (design §11.2)

- 입력 `process.corner`·`temp_c`가 있으면 그것, 없으면 LUT npz meta의 `corner`·`temp_c`.
- LUT meta에 기록이 없으면 입력에 둘 다 있어야 하고, 없으면 `oracle_condition_missing`(실행 전).
- 입력 온도가 LUT `temp_c`와 다를 때 = `[J-8]`.

### C8. 옛 넷리스트 생성기 관찰 계약 -- **`[J-1]`**

- 계획: OP-2에서 넷리스트는 아직 옛 생성기가 **기술자 값으로** 쓴다. 기하 단위·병렬 배수 반영은 OP-3이다 -- 그래서 같은 회로·같은 PDK 값이면 소자 줄(`X<이름> d g s b <subckt> l=… w=… m=… [ad…]`)·동작점 탐침·`.option`·`.temp`는 옛 형식 입력 때와 같다.
- 소자 줄의 subckt 이름 = 기술자 `kinds.<kind>.name`이 정하는 이름, include 줄 = 기술자 `kinds.<kind>.includes`가 가리키는 원본들, `.option` 줄 = `simulator.options`, iso 모드 극성 = 기술자 `kinds.<kind>.polarity`, 확산 규칙 = `[J-2]`.
- 비교 기준(include 경로 표기 차이를 허용하는지 등)과 각 값의 정확한 출처 = `[J-1]`.

### C9. conftest 입력 생성기 (`O/tests/conftest.py`, test 주체 소유)

- `process_block(lut, diffusion=True)`, `testbench_block()`, `cs_input(lut, *, …)`, `rc_input(lut, circuit=…)`, `fb_input(lut, *, …)`의 **이름·인자는 그대로**(호출 183줄·28파일을 바꾸지 않는다). 반환 dict만 C5 새 형식이다.
- `testbench_block()`는 `options`를 더 이상 담지 않는다(그 값은 `simulator.options`로 -- 어느 생성기가 `simulator` 블록을 채우는지는 test 주체가 정한다, 공개 동작 아님).
- `diffusion=False`의 새 뜻 = `[J-12]`.
- OP-2에는 stub 어댑터가 없으므로 생성기의 기술자는 sky130 기술자(C0)다.

### C10. 바뀌지 않는 것

- 엔진 전부(`E/`), `A/sky130_pdk_decl.json`, `A/sky130_lut_rule_decl.json`, `A/lut_v2_location.json`.
- 결과 JSON(`*.sim.json`, `*.compare.json/md`) 칸·값 규칙, 판정·측정 수학(OP-3~OP-5).
- 넷리스트 소자 줄 규칙(finger당 1 인스턴스, `m=n_fingers`, `nf` 없음, C3), 탐침 매개변수 집합.
- `O/smoke/` 고정 자료 파일(입력 3개·넷리스트·compare).
- `make_lut`(meta `corner`·`temp_c`만 -- `model_files_sha256`은 OP-3).

### C11. 단언 금지

- 기술자 읽기 함수 안쪽 자료 구조, 오류 문장(사람이 읽는 메시지)의 글자, `descriptor_source_duplicated`의 `detail` 모양(design 미정), 기술자 파일 안 키 순서·공백, sha256 문자열 값 자체(같음·다름만 -- 단 X-13 (a)는 두 값의 같음), 입력 `simulator.adapter` 값이 실행에 미치는 영향(OP-3).

---

## 신규 시그니처 (merge_gate가 새 심볼 부재 red를 card 이유로 센다 -- card A J-O1)

base `5fea301`에 없는 것. 이것 때문에 base에서 나는 `ImportError`·`FileNotFoundError`·`KeyError`·스키마 거부는 card 이유의 red다.

| 심볼 | 위치 | 종류 |
|---|---|---|
| 기술자 파일 `sky130.oracle_descriptor.json` | `O/descriptors/` | 데이터 |
| 기술자 읽기 공개 함수 `[J-4]` | `O/core/descriptor.py` | 함수 |
| 오류 코드 `descriptor_schema_invalid`, `pdk_descriptor_stale`, `descriptor_source_duplicated`, `lut_location_decl_invalid`, `oracle_input_format_old`, `oracle_condition_missing`, (`lut_record_root_mismatch` `[J-5]`) | 기술자 읽기·진입점 출력 `[J-4]`·`[J-10]` | 코드 |
| 입력 칸 `process.descriptor`, `process.corner`, `process.temp_c`, `simulator.{adapter, exe, options}`, (`output_reference` `[J-8]`) | `O/oracle_input.schema.json` | 칸 |
| X-13 test 파일 | `E/tests/<[J-6]>/` | test |

없어지는 것: 입력 칸 `process.models`(`subckt`·`includes`·`op_probe`·`polarity`), `process.ngspice_exe`, `process.diffusion`, `process.lut_reference_width_m`, `process.provenance`, `testbench.options`. (CLI `--ngspice` = `[J-9]`.)

---

## 3. test 목록

위치는 제안이다(오라클 test는 `O/tests/` 아래, 코어 test는 `O/tests/core/`, design §3.1). oracle: (식) design·계약 문서 식, (손) 손으로 만든 JSON·파일 변형, (비교) 같은 진입점 두 출력 비교, (독립) 피검 코드를 거치지 않고 test가 직접 계산(예: `hashlib.sha256`로 파일 sha256, JSON 직접 읽기). 기술자·위치 선언·엔진 선언 변형은 **test 안 tmp 사본**으로만 만든다(저장소 파일은 고치지 않는다).

### 3.1 새 test

| id | 위치(제안) | 내용 | 계약 | oracle | base 결과 | 착수 |
|---|---|---|---|---|---|---|
| OP2-T0 | `O/tests/core/test_descriptor_file.py` | sky130 기술자 파일: 존재, `schema = "oracle_pdk_descriptor/1"`, `mc`·`diagnostic` 키 없음, kind 둘(nmos·pmos) 각각 `geometry_unit`·`parallel_multiplier`·`polarity`·`includes` 있음, `extra_sources` 항목마다 `provenance` 비어 있지 않음, `lut_file_roles == []`, `lut_record_root.key == "pdk_root"`, `engine_decl.sha256` = test가 직접 잰 엔진 선언 sha256, `location_decl.sha256` = 직접 잰 위치 선언 sha256, **기술자 안에 엔진 선언 sources의 경로·sha256 문자열이 다시 나오지 않음**(정본 하나) | C0 | (독립) | red(파일 없음) | J-4·J-15 뒤(경로 기준·sha 정의) |
| OP2-T1 | `E/tests/<J-6>/test_oracle_descriptor_engine_sha.py` | X-13 (a)(b). 거부 증거: tmp 기술자 사본에서 sha256 한 글자 바꾸면 (a) 실패, `extra_sources`에 엔진 source 하나(경로 같게 / sha256만 같게)를 넣으면 (b) 실패(test 안 검사 함수에 사본을 넣어 확인) | C4 | (독립) | red(파일 없음) | J-6·J-15 뒤 |
| OP2-T2 | `O/tests/core/test_descriptor_read.py` | 양성 대조: 실제 sky130 기술자가 오류 없이 읽힘. 거부: C2 1행 변형마다(필수 칸 삭제, 닫힌 키 밖 키 추가, `provenance = ""`, `schema` 값 변경) → `descriptor_schema_invalid`, `detail`이 그 위치를 가리킴 | C1·C2 | (손) | red(ImportError) | J-4·J-11 뒤 |
| OP2-T3 | 같은 파일 | `pdk_descriptor_stale`: `engine_decl.sha256` 변경 → `ref = "engine_decl"`, 엔진 선언 사본에서 쓰는 source sha256 변경(원본은 그대로) → `"engine_source:<key>"`, `extra_sources` sha256 변경 → `"extra_source:<key>"`, 위치 선언 sha256 변경 → `"lut_location_decl"`, 가리킨 파일 삭제 → `actual_sha256 = "missing"`. `expected`·`actual`이 test가 잰 값과 같음 | C2 | (손)+(독립) | red | J-4 뒤 |
| OP2-T4 | 같은 파일 | `descriptor_source_duplicated`: `extra_sources`에 엔진 source와 경로가 같은 항목 / sha256만 같은 항목(다른 경로의 같은 바이트 사본) 각각 | C2 | (손) | red | J-4 뒤 |
| OP2-T5 | 같은 파일 | 순서: 스키마 위반 + sha256 불일치가 함께 있는 변형 → `descriptor_schema_invalid` 하나만, sha256 불일치 + 중복이 함께 → `pdk_descriptor_stale`, 중복 + 위치 선언 형식 오류 → `descriptor_source_duplicated`. 모든 거부에서 시뮬레이터 호출 0 | C2 | (손) | red | J-4 뒤 |
| OP2-T6 | `O/tests/core/test_lut_record_root.py`(design 1169행 이름) | C3 표 네 행 + 결과 출처 표기, `pdk_root` 칸 없는 위치 선언 → `lut_location_decl_invalid`(LUT meta로 돌아가지 않음), `env`·`default` 둘 다 없음 → 같은 코드, 위치 선언이 `gmid_lut_location/1`이 아님 → 같은 코드, 기술자 자체 형식 오류 → `descriptor_schema_invalid`(위 셋과 다름을 함께 단언), 위치 선언 sha256 다름 → `pdk_descriptor_stale`(`lut_location_decl`). 기대 경로 = test가 `os.path.abspath`로 직접 계산(계약 1.8 261행) | C3·C2 | (식)+(독립) | red | J-4 뒤 |
| OP2-T6b | 같은 파일 | 다른 트리를 가리키는 뿌리 → `lut_record_root_mismatch` | C2 (8) | (손) | red | **J-5 뒤**(OP-3으로 옮길 수 있음) |
| OP2-T7 | `O/tests/test_oracle_input_schema.py`(다시 씀) | 스키마 자체 유효(Draft 2020-12), 새 생성기 입력(cs·rc·fb) 적합, 위반 변형 표(옛 표의 형식 무관 항목 유지 + `process` 닫힌 키: `lut_reference_width_m`·`provenance`·임의 키 추가 / `simulator` 필수 칸 삭제 / `process.descriptor` 삭제) → jsonschema로 위반 확인 후 netlist·run·compare 진입점 반환 2·산출물 0, 양성 대조(원본 입력 수용) | C5·C6 | (손)+(비교) | red(base 스키마가 새 형식 거부) | J-10 뒤(최상위 `schema` 값) |
| OP2-T8 | 같은 파일 | 옛 형식 거부: 새 형식 입력에 `process.models`를 더한 변형, `process.ngspice_exe`를 더한 변형 각각 → 세 진입점에서 `oracle_input_format_old`, 반환 2, 산출물 0, 시뮬레이터 호출 0. 같은 입력에서 그 칸만 뺀 것은 수용(양성 대조) | C6 | (손)+(비교) | red(base는 옛 형식 수용) | J-10 뒤(코드 표현) |
| OP2-T9 | `test_legacy_adapter.py::test_smoke_input_conforms_to_schema` 자리(LT-1 순서 3이 먼저면 옮긴 파일) | smoke 고정 자료 3개가 `oracle_input_format_old`로 거부됨(netlist 진입점, 산출물 0). 고정 자료 파일은 고치지 않음 | C6 | (식) | red(base는 적합) | J-10 뒤 |
| OP2-T10 | `O/tests/test_oracle_netlist.py`(또는 새 파일) | 조건 해석: (i) LUT meta만 → `.temp` = meta temp_c, include 코너 = meta corner (ii) 입력 `corner`·`temp_c`가 meta와 같은 값 → 같은 넷리스트 (iii) meta 없음 + 입력 둘 다 → 입력 값 (iv) meta 없음 + 입력 하나 이상 없음 → `oracle_condition_missing`, 산출물 0 | C7 | (식)+(비교) | red | J-8·J-10 뒤((ii) 다른 값은 J-8) |
| OP2-T11 | `O/tests/test_oracle_netlist.py` | `.option` 줄 = `simulator.options`의 키=값(옛 `testbench.options` 자리), meta `tb_options`가 같은 dict. `simulator.options`에서 `reltol`을 뺀 변형의 동작이 옛 'testbench.options에서 reltol 뺌'(`test_oracle_c10_stability.py:1469`)과 같음 | C5·C8 | (비교) | red | J-1 뒤 |
| OP2-T12 | `O/tests/test_oracle_netlist.py`(`:72`·`:81` 자리 다시 씀) | 소자 줄 subckt 이름·include 줄·확산 ad/pd·iso 극성의 기대값을 test가 **기술자 JSON과 엔진 선언 JSON(필요하면 원본 파일)을 직접 읽어** 계산(피검 코드 출력 아님) | C8·C0 | (독립) | red | J-1·J-2 뒤 |
| OP2-T13 | `O/tests/test_oracle_run.py` | 실행 파일: CLI 인자 없이 `simulator.exe`만으로 실행 경로가 잡힘, `simulator.exe` 없고 CLI도 없으면 반환 2 | C5 | (비교) | red | J-9 뒤 |
| OP2-T14 | `O/tests/test_oracle_junction_cap.py`·`test_oracle_netlist.py:93` 자리 | '확산 규칙 없음'(옛 `diffusion=False`) 표현에서 free 막힘(C22)·forced 노트 동작이 옛과 같음 | C9·C8 | (비교) | red | J-12 뒤 |

### 3.2 삭제·고칠 test (5fea301 실측)

| 대상 | 처리 |
|---|---|
| `O/tests/conftest.py` 생성기 다섯(`:71-90`, `:105-109`, `:118-`, `:166-`, `:195-`) | C5 새 형식으로, 이름·인자 유지(C9). `diffusion=False` = `[J-12]` |
| 생성기 밖 옛 칸 직접 수정 19줄·9파일: `test_oracle_conduction.py:216, :285-286`, `test_oracle_iso.py:22`, `test_oracle_junction_cap.py:94-95, :139-140, :203`, `test_oracle_netlist.py:72, :81`, `test_oracle_netlist_topology.py:214`, `test_oracle_ratio_db.py:265-266`, `test_oracle_rout.py:518-519`, `test_oracle_simulate_cache.py:29, :108, :125` | 기술자 변형(tmp 사본)으로 다시 씀. `:216`(없는 내부 소자 탐침 → SPICE ID 없음 → INCOMPLETE)은 `inner_device` 변형으로, polarity 대입은 기술자 `polarity`(C0 필수 칸)로 옮겨 가므로 그 줄을 지울지는 test 주체가 판단하고 이유를 기록(단언이 약해지면 `criteria_weakened` -- 사용자 승인), `:108`·`:125`(include 첫 줄을 래퍼 파일로)는 기술자 `includes` 변형 + `extra_sources`(sha256) 변형 -- 경로 기준 `[J-4]` |
| `testbench.options` 직접 2줄: `test_oracle_c10_stability.py:1469`, `test_oracle_u6_stability.py:766` | `simulator.options`로 |
| CLI `--ngspice` 3곳: `conftest.py:280, :300`, `test_oracle_c10_stability.py:972` | `[J-9]` |
| `test_oracle_input_schema.py` 8함수 | OP2-T7·T8로 다시 씀 |
| `test_legacy_adapter.py::test_smoke_input_conforms_to_schema`(3항목) | OP2-T9로 |
| `test_legacy_adapter.py::test_smoke_netlist_regenerates_identically`·`test_smoke_loop_netlist_regenerates_identically`(12항목) | **`[J-7]`** -- OP-2 새 스키마에서 반환 2로 실패한다. J 전에는 손대지 않는다 |
| `test_legacy_adapter.py`의 고정 자료만 읽는 test(finger 규칙, W 자기모순, feedback_passives) | 그대로 |
| `smoke/u6_selfchecks.py`(conftest import·생성기 사용 `:44, :52, :54, :66-67, :84`) | OP-3이 지운다(O-10). OP-2에서는 생성기가 새 형식이라 따라 바뀐다(스크립트 자체는 고치지 않음, test 아님) |
| 그 밖 `make_lut` 160줄 | 그대로(OP-3) |

### 3.3 이름 규칙

- 0건 확인(5fea301, docs·`.md`·`.ai`·`.bkit` 제외): `oracle_descriptor`, `oracle_pdk_descriptor`, `lut_record_root`, `location_decl`, `engine_decl`, `extra_sources`, `descriptor_schema_invalid`, `pdk_descriptor_stale`, `descriptor_source_duplicated`, `lut_location_decl_invalid`, `lut_record_root_mismatch`, `oracle_input_format_old`, `oracle_condition_missing`, `test_lut_record_root`, `test_oracle_descriptor`, `test_descriptor`, `descriptor.py`, `parallel_multiplier`, `inner_device`, `call_form`, `model_family`. `geometry_unit`은 엔진 quantity `mismatch_slope_geometry_unit_m`에만 부분 일치(기능 충돌 없음).
- 엔진 suite `-k` 식(card A·xrunf1b와 같음): `"test_ic"`, `"g10"`, `"ic11 or kvl_branch_residual"`, `"rule_g or design_value_location"`, `rule_k_`, `rule_m_`, `"duplicate_args or loop_invariant"`, `"ic1 or ic2 or ic9 or ic10 or shared_gate_net or kcl_residual"`, `"mna_assembly_count or mna_solve_count"`. X-13 test 함수 이름은 `test_ic`로 시작하지 않고 `ic1`·`ic2`·`ic9`·`ic10`·`ic11`·`g10`·`rule_g`·`rule_k_`·`rule_m_`를 담지 않는다. 권장 접두 `test_oracle_descriptor_…`. 작성 뒤 엔진 `--collect-only -k <각 식>` 수를 base와 함께 보고.
- 오라클 suite에는 `__init__.py`가 없어 test 모듈 이름(basename)이 오라클 test 전체에서 겹치면 안 된다: 새 이름 `test_descriptor_file`, `test_descriptor_read`, `test_lut_record_root`는 지금 0건.
- 권장 접두: `test_descriptor_file_…`(T0), `test_oracle_descriptor_…`(T1), `test_descriptor_read_…`(T2~T5), `test_lut_record_root_…`(T6), `test_input_format_…`(T7·T8), `test_smoke_input_rejected_as_old_format`(T9), `test_condition_…`(T10).
- **red 예상 목록**(감사 대상) = OP2-T0~OP2-T14(착수한 것만). 제외: 새 conftest로 base에서 red가 되는 **기존 오라클 test 전부**(base 스키마가 새 형식 입력을 거부하기 때문 -- 엔진·오라클 동작 red가 아니라 test 도구 변경 red, nfr4c2 J-O2), conftest 생성기 자체.

---

## 4. 판정 측정 (audit)

격리 복제본(`<W>/op2-audit`, base 비교용 base 복제본 따로)에서만 잰다. ngspice 실행은 한 번에 하나, 결과는 파일에 append.

| # | 측정 | 방법 | 합격 |
|---|---|---|---|
| O-1 | 삭제 이름 grep 0 | spec card 1.4.5 이름·범위별 `git grep -n`(스키마 키, 옛 칸 읽기 -- `[J-1]` 결과 범위) | 범위 안 0 |
| O-2 | 엔진 무변경(8a) | `git diff base..head -- skills/analog-gmid-design/gmid_engine skills/analog-gmid-design/assets/sky130_pdk_decl.json skills/analog-gmid-design/assets/sky130_lut_rule_decl.json skills/analog-gmid-design/assets/lut_v2_location.json` = X-13 새 파일 하나만 | 그 하나만 |
| O-3 | 구조 | 엔진 `tests/structure` 기본 실행 위반 0, `-m structure_test_mapping`(규칙 H) 위반 집합이 base와 같음(X-13 파일이 `orphan_test`를 더하지 않음) | 같음 |
| O-4 | 거부가 실제로 거부 | C2 표 코드마다 변형 하나 이상이 그 코드로 거부됨을 감사가 따로 확인(test 통과가 아니라 거부 자체). 검사 하나를 빼는 변형 구현(복제본 안, 커밋 안 함: sha256 대조 생략 / 중복 검사 생략 / `pdk_root` 없을 때 LUT meta로 돌아가기)에서 해당 test가 실패하는지 | 모든 변형에서 test 실패 |
| O-5 | 정본 하나 | 기술자 JSON 안에 엔진 선언 `sources`의 `path`·`sha256` 문자열 재기재 0, `extra_sources` ∩ 엔진 sources = ∅(경로·sha256), 기술자에 DC 허용오차 칸 0, LUT 기록 뿌리 값(`C:/pdk/…` 같은 경로) 재기재 0 | 0 |
| O-6 | sha256 정의 | 기술자 `engine_decl.sha256`·`location_decl.sha256`이 디스크 바이트 sha256과 같음, 같은 파일의 git blob sha256과의 차이 보고(`[J-15]` 결정 대조) | J-15 결정대로 |
| O-7 | 넷리스트 동등성 | base(옛 형식 conftest 입력)와 head(새 형식 conftest 입력)를 같은 환경에서 netlist 진입점에 넣어 cs·rc·fb × free·forced·iso 넷리스트·meta를 줄 단위 비교 | `[J-1]` 기준 안, 차이 줄 전부 기록 |
| O-8 | red-green | base + 새 test: OP2-T*가 red이고 사유가 신규 시그니처 부재 또는 단언 실패인지 test마다 기록. head 전부 통과 | head 통과 |
| O-9 | 오라클 suite | head `python -m pytest -q skills/analog-gmid-design/tools/spice_oracle/tests -p no:cacheprovider`(slow 포함) 한 번, 실패 0. `[J-7]` 대상 12항목 처리 확인 | 0 failed |
| O-10 | 엔진 suite | X-13 test 통과, 엔진 기본 suite 영향 없음(X-13 파일 하나만 추가) | 통과 |
| O-11 | 만들면 배선 | spec card 1.5.2 표의 칸마다 head에서 소비자 호출 경로(기술자 읽기가 진입점에서 불림 -- 호출 기록) 또는 design의 '출력 전용' 선언 | 전부 |
| O-12 | 병합 조건 R6 | `[J-14]` 산출물: 매뉴얼 원문 보관 위치·sha256, reltol·vntol 기본값 쪽, abstol 값·쪽, 시간 걸음 실패 문장 쪽 | 있음 |
| O-13 | 이름 충돌 | 3.3 `-k` 식 엔진 `--collect-only` head·base, 오라클 test basename 중복 0 | 증가분 = 새 test만 |
| O-14 | 공통 | gap-detector ≥ 90 %, 사용자 확인 기록(sky130 기술자 값) 존재 | 통과 |

---

## 5. 공통 브리핑

> spec card 2절과 같다. test agent는 이 문서 2·3절만 읽고 소스를 보지 않는다.

base = `5fea301`(J 개정 뒤 그 병합 master). design v0.2.6 §10.1~§10.3(mc·diagnostic 제외)·§7·§7.2·§11·§15.4·§18.1·§18.2·§20, 계획 v0.6.6 N5.1 OP-2 행. 사용자 결정 기록: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md`(읽기만). card: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/oracle/OP2_SPEC_CARD.md`(code·audit), `OP2_INTERFACE_CARD.md`(test는 이것만).

### 절대 규칙
1. design 그대로. as-built 결정 금지 -- `[J-n]` 칸은 닫히기 전 쓰지 않는다. 모르면 멈추고 보고.
2. 정본 하나: 엔진 sources 파일 정보는 엔진 선언에만, LUT 기록 뿌리는 위치 선언에만, 기술자는 참조(sha256)만. 사본 금지.
3. 만들면 배선: 새 칸마다 소비자 또는 출력 전용.
4. fail-closed: 처음 걸린 하나로 실행 전 거부, 기본값 대체 금지.
5. 이름·상수 발명 금지, 규칙·코어 코드에 PDK·시뮬레이터·회로 이름 금지.
6. 엔진 무변경(X-13 새 test 파일 하나만), 오라클 test는 엔진 import 금지.
7. 작성자 ≠ 검증자. 기대값은 계약 문서·JSON·손계산에서. 같은 커밋에서 코드와 기준 동시 변경 금지, 기준 약화는 사용자 승인.

### 실행 환경·git 가드
- python `/c/Python314/python.exe`. 오라클 test: `<worktree>`에서 `python -m pytest -q skills/analog-gmid-design/tools/spice_oracle/tests -p no:cacheprovider`. 엔진 test: `<worktree>/skills/analog-gmid-design`에서 `python -m pytest -q gmid_engine/tests/<경로> -p no:cacheprovider`.
- ngspice 실행은 한 번에 하나, 결과는 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op2_<role>/run.txt`에 append, 백그라운드 실행이 끝날 때까지 턴을 끝내지 않는다.
- git: `git -C <자기 worktree>`, `set -e`, 다른 worktree·master 금지, reset --hard·checkout·push·merge 금지.
- 커밋 트레일러(`--trailer`): `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, `Claude-Session: https://claude.ai/code/session_012FxFP7YSWEBBCB9rmBQjLL`.

### 최종 보고(한국어)
1. 작성한 절과 상태 2. 멈춤·보고 3. 바꾼 test·지운 단언(파일:줄) 4. 정본 점검 5. 거부 실제 확인 6. 오라클·엔진 test 결과, 깨진 옛 test 7. 커밋 해시.

## 오케스트레이터 판단 (상속)
- (card A J-O1) 위 '## 신규 시그니처' 절.
- (nfr4c2 J-O2) red 예상 = OP2-T*(착수한 것). 새 conftest 때문에 base에서 red가 되는 기존 오라클 test는 제외.
- (card A J-7) base·head 같은 환경(O-7).
- `[J-1]`~`[J-15]` 닫히기 전 착수 금지(spec card 1.8).
