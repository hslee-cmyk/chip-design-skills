---
id: 20261107-fs1-sb8-power-resolution
spec_card: docs/02-design/specs/20261107-fs1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_start_intervals.py::test_sb8_circuit_without_a_transfer_view_still_has_a_wf_start
---
## 문제의 test

S-B8 (d): `layer0_start(case.sctx)`의 `res.start is not None` 단언(test_start_intervals.py 772행)이 red다. (a)(b)(c)와 (e)는 그 앞에서 통과한다(`graph/start: inactive`에 A-205·A-206 이름 전부 있음, wf_start 3칸 모두 w_key 100).

## 근거(oracle 또는 사용자 원문)

실측(code 브랜치 head, 스크립트로 `fs1_no_view_toy` + `FS1_NOV_ELS` + `TOY_CONS` 재현):
- 층 0 사다리 칸 0의 첫 평가 `status == seal_undefined`, `failure is None`, `evaluation.report.status == sealed`(봉인 항목 1~9 전부 pass, `n_undefined` 0).
- `kernel.evaluate`는 `objective_values(snapshot).power_resolution_w is None`이면 STATUS_UNDEFINED로 둔다(kernel.py 163~164행). 이 toy에서 `power_resolution_w`가 None이다.
- 원인: `metrics/dc_metrics._power_resolution`은 |V|≠0인 레일에 **채널이 닿는 MOS**의 `dc_tol_v·dc_gm`으로 b_P를 정의한다. 이 toy는 vdd를 선언 이상 전류원 I1, I2만 닿고 어떤 MOS 채널도 vdd에 닿지 않아(M1 드레인 = out, M3 드레인 = d3) 정의되는 항이 없다 -> `defined` False -> None.
- 이는 FS-1 코드(출발 블록·`wf_start`·평가 입력) 밖이다. 출발 블록은 늘 실행되고(`wf_start` 3칸, inactive 기록 정상), 평가 입력 `WfInput`도 정상이다. 물리적으로도 b_P(전력 축 분해능) 정의에 레일에 닿는 MOS가 필요하다는 기존 정의이고 FS-1은 바꾸지 않는다.

## 요청

S-B8 (d)의 toy를 b_P가 정의되도록 고친다(예: 전류원 대신 MOS 채널이 vdd에 닿는 가지를 두거나, 레일 쪽 MOS 하나를 추가). 또는 (d)의 기대를 'start None이 아님'에서 '이 toy는 b_P 미정이라 O-2 꼴이 아니고 평가를 했다' 같은 FS-1 계약 범위로 좁힌다. `dc_metrics._power_resolution` 정의 변경은 FS-1 범위 밖이라 code가 하지 않는다.
