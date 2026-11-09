# K13 ⑨ 손계산: 단위 캡 배열 면적 효율 u^2/(u+s)^2 (큰 배열 근사, 바깥 감싸기 무시), sky130 사례 값
# s = MIM 배열 간격(sky130 capm.2a 0.84 um, sky130.tech 5105행), 감싸기(capm.3 0.14 um, 5112~5113행)는 배열 바깥 한 번이라 큰 배열에서 무시
import sys
s = 0.84
rows = []
for u in (1.0, 2.0, 5.0, 10.0, 20.0, 30.0):
    eff = u * u / (u + s) ** 2
    rows.append((u, eff, 30 * eff, 80 * eff))
with open(sys.argv[1], 'w', encoding='utf-8') as fh:
    fh.write('u_um\tarea_eff\tC_up_two_stage(30pF bound)\tC_up_current_reuse(80pF bound)\n')
    for r in rows:
        fh.write('%.1f\t%.3f\t%.1f\t%.1f\n' % r)
