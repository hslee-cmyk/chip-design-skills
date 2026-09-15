# 입력 극성 독립 MNA 측정 (gm=1mS, gds=10uS 균일, 부호만 판정)

## two_stage_ota
- 출력 노드: `OUT`, ports: {"vin_p": "differential_input_p", "vin_n": "differential_input_n"}
- vin_p 단독 +1 V: v(OUT) = -2487 -> 반전(-)
- vin_n 단독 +1 V: v(OUT) = +2488 -> 비반전(+)
- 차동 vin_p=+0.5, vin_n=-0.5: v(OUT) = -2488 -> 반전(-)

## two_stage_ota_sf
- 출력 노드: `vout`, ports: {"vin_p": "differential_input_p", "vin_n": "differential_input_n", "vout": "single_ended_output"}
- vin_p 단독 +1 V: v(vout) = +2439 -> 비반전(+)
- vin_n 단독 +1 V: v(vout) = -2439 -> 반전(-)
- 차동 vin_p=+0.5, vin_n=-0.5: v(vout) = +2439 -> 비반전(+)

## sf_pushpull_output_opamp
- 출력 노드: `vout`, ports: {"vin_p": "differential_input_p", "vin_n": "differential_input_n", "vout": "single_ended_output"}
- vin_p 단독 +1 V: v(vout) = +3.23e-12 -> 비반전(+)
- vin_n 단독 +1 V: v(vout) = -3.197e-14 -> 반전(-)
- 차동 vin_p=+0.5, vin_n=-0.5: v(vout) = +1.631e-12 -> 비반전(+)

## sf_pushpull_output_opamp (재측정: R1a/b/c 컨덕턴스 1e-4 S 스탬프, Cc·CL 개방, IBias 개방)
- vin_p 단독 +1 V: v(Y) = +4596, v(vout) = +4461 -> 비반전(+) (cond 1.04e+05)
- vin_n 단독 +1 V: v(Y) = -4596, v(vout) = -4461 -> 반전(-) (cond 1.04e+05)
- 차동 +0.5/-0.5: v(Y) = +4596, v(vout) = +4461 -> 비반전(+) (cond 1.04e+05)
# 입력 극성 독립 MNA 측정 (gm=1mS, gds=10uS 균일, 부호만 판정)

## two_stage_ota
- 출력 노드: `OUT`, ports: {"vin_p": "differential_input_p", "vin_n": "differential_input_n"}
- vin_p 단독 +1 V: v(OUT) = +2488 -> 비반전(+)
- vin_n 단독 +1 V: v(OUT) = -2487 -> 반전(-)
- 차동 vin_p=+0.5, vin_n=-0.5: v(OUT) = +2488 -> 비반전(+)

## two_stage_ota_sf
- 출력 노드: `vout`, ports: {"vin_p": "differential_input_p", "vin_n": "differential_input_n", "vout": "single_ended_output"}
- vin_p 단독 +1 V: v(vout) = +2439 -> 비반전(+)
- vin_n 단독 +1 V: v(vout) = -2439 -> 반전(-)
- 차동 vin_p=+0.5, vin_n=-0.5: v(vout) = +2439 -> 비반전(+)

## sf_pushpull_output_opamp
- 출력 노드: `vout`, ports: {"vin_p": "differential_input_p", "vin_n": "differential_input_n", "vout": "single_ended_output"}
- vin_p 단독 +1 V: v(vout) = +3.23e-12 -> 비반전(+)
- vin_n 단독 +1 V: v(vout) = -3.197e-14 -> 반전(-)
- 차동 vin_p=+0.5, vin_n=-0.5: v(vout) = +1.631e-12 -> 비반전(+)
