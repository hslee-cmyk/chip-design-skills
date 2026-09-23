# interface card: 20260923-d-delete-telescopic

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `_cmrr_telescopic_class_ab` | `def _cmrr_telescopic_class_ab(metric_spec: dict, ctx: SizingContext) -> float` |
| `sizing_recipe` | `_cmrr_telescopic_class_ab_cmfb` | `def _cmrr_telescopic_class_ab_cmfb(metric_spec: dict, ctx: SizingContext) -> float` |
| `sizing_recipe` | `_psrr_telescopic_class_ab` | `def _psrr_telescopic_class_ab(metric_spec: dict, ctx: SizingContext) -> float` |
| `sizing_recipe` | `_psrr_telescopic_class_ab_cmfb` | `def _psrr_telescopic_class_ab_cmfb(metric_spec: dict, ctx: SizingContext) -> float` |
| `sizing_recipe` | `_cmfb_amp_gain_diode_load` | `def _cmfb_amp_gain_diode_load(metric_spec: dict, ctx: SizingContext) -> float` |
| `sizing_recipe` | `_load_telescopic_topology_cached` | `def _load_telescopic_topology_cached() -> dict` |
| `sizing_recipe` | `_telescopic_class_ab_open_loop_response` | `def _telescopic_class_ab_open_loop_response(metric_spec: dict, ctx: SizingContext, vip: float, vim: float, vdd: float, vcmfb: float) -> tuple` |
| `sizing_recipe` | `_telescopic_open_loop_device_names` | `def _telescopic_open_loop_device_names(metric_spec: dict) -> list` |
| `sizing_recipe` | `_telescopic_class_ab_open_loop_gains` | `def _telescopic_class_ab_open_loop_gains(metric_spec: dict, ctx: SizingContext) -> tuple` |

### `sizing_recipe._cmrr_telescopic_class_ab`

> `circuit_family="telescopic_class_ab"` — current-reuse telescopic 1단(Xie&Chen
> 논문 Fig.2, current_reuse_telescopic_ota)의 **open-loop**(CMFB 루프 제외) CMRR.
> 논문 자체엔 CMRR 폐형식이 없어서(시뮬레이션 수치 94.4dB만 보고) 2026-07-31에 처음
> 유도했고, **2026-08-03에 확정된 topology.json으로 처음부터 재유도**했다
> (`workspaces/current-reuse-telescopic-ota-report/spice/stage1_cmrr_sympy_derivation.py`
> = sympy 정확해, `.../stage1_cmrr_ngspice_crosscheck.py` = ngspice AC 교차검증).

### `sizing_recipe._cmrr_telescopic_class_ab_cmfb`

> `circuit_family="telescopic_class_ab_cmfb"` — current-reuse telescopic OTA의 CMRR,
> stage-1(11소자) + 양쪽 Monticelli class-AB battery(각 10소자) = 31소자 소신호망을
> `_telescopic_class_ab_open_loop_gains()`(세션21 신설)로 **수치 MNA**로 풀어 얻는다.

### `sizing_recipe._psrr_telescopic_class_ab`

> `circuit_family="telescopic_class_ab"` — current-reuse telescopic 1단의
> **open-loop**(CMFB 제외) PSRR+(2026-08-07 신설, `analog-topology-json-library`
> 세션20 후속). 기존 `diff_pair_tail`(M5 하나의 gm/gds만 보는 자리표시자, 이 회로에서는
> 13개 자유 theta 중 어느 것도 M5에 안 닿아 절대 만족시킬 수 없는 상수값이었다 — 세션20
> 실측 발견)를 대체한다.

### `sizing_recipe._psrr_telescopic_class_ab_cmfb`

> `circuit_family="telescopic_class_ab_cmfb"` — current-reuse telescopic OTA의 PSRR,
> `_cmrr_telescopic_class_ab_cmfb`와 **완전히 같은 31소자 수치망**(세션21 신설
> `_telescopic_class_ab_open_loop_gains()`)에서 나오는 `Adm_open`/`Ann_open`/`H`를 쓴다.

### `sizing_recipe._cmfb_amp_gain_diode_load`

> `telescopic_class_ab_cmfb`의 부품: CMFB 에러앰프(Xie&Chen Fig.5)의 소신호 이득
> `A_c = v(Vcmfb)/v(Voc)`. **근사 없는 정확해**(sympy 정확해와 기호적으로 동일함을 확인,
> 2026-08-03 배치 7-5c).

### `sizing_recipe._load_telescopic_topology_cached`

> `current_reuse_telescopic_ota.topology.json`의 connectivity를 캐시해서 돌려준다
> (grid search 중 반복 호출 대비 -- 파일은 이 프로세스 안에서 안 바뀐다는 전제, 세션21).
> connectivity는 오직 이 JSON에서만 읽는다(하드타이핑 없음, topology.json이 유일한
> 토폴로지 소스라는 프로젝트 원칙 그대로 -- `stage1_cmrr_sympy_derivation.py` 등 모든
> 유도 스크립트와 동일한 소스).

### `sizing_recipe._telescopic_class_ab_open_loop_response`

> 1단(11소자) + 양쪽 Monticelli class-AB battery(각 10소자, M8~M14b류/M17~M24b류) =
> 31소자 소신호망을 `metric_spec`의 롤 배정으로 조립해 (Vop1, Vom1)을 수치로 푼다(세션21).

### `sizing_recipe._telescopic_open_loop_device_names`

> `_telescopic_class_ab_open_loop_response()`가 조립하는 31소자망의 소자 이름 목록.
> 소자 열거(원래 그 함수 안에 있던 로직, 2026-08-13 세션31 리팩터로 공용 추출)와 캐시 키
> 구성(`_telescopic_class_ab_open_loop_gains()`) 둘 다 이 목록을 쓴다.

### `sizing_recipe._telescopic_class_ab_open_loop_gains`

> Adm_open/Acm_open/Ann_open/H를 **전부 같은 31소자망**에서 각기 다른 여기(excitation)로
> 구한다(세션21) -- Adm(vip=+0.5/vim=-0.5), Acm(vip=vim=1), Ann(vdd=1, PSRR용 VDD 리플),
> H(vcmfb=1, `v(stage-1 CM out)/v(Vcmfb)` -- CMFB 루프이득 T=-H*A_c*G2의 그 H). 넷 다
> battery의 M10/M19 부하 + M8/M17의 자체 VDD 주입 경로를 동일하게 반영한다(세션20까지는
> H/Acm_open/Ann_open이 Kp'/Kn'/Rx/Ry 폐형식만 썼고 M10/M19를 몰랐다 -- 세션21에 이
> 수치망으로 교체).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
