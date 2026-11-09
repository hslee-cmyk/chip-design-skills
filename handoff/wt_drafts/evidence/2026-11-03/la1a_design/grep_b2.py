# design 묶음 ② 낡은 자리 전수 grep -- 키워드마다 파일:줄·앞뒤 문맥을 grep_b2.txt에 쓴다(저장소 쓰기 0).
import re, os, sys
D = r'C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/gain-budget-gmid-sizing.%s.design.md'
FILES = {'D40': '40-engine', 'D41': '41-gain-budget', 'D42': '42-gap-checklist'}
KEYS = ['tol_vdsat', 'tol_VDsat', 'dc_window_def', '_conduction_rows', '전도 행', r'R0\b', 'V_on', 'off_vgs0', 'off_device_on_signal_path', 'bias_fixed', 'gvgs_self_edge', 'E-19', 'E-21', 'E-22', 'E-35',
        'conduction_floor', 'dc_off_current', 'off_current_A', 'dc_seal_conduction', 'conduction_mask', '기능 기준', 'U-69', 'P-7', '열린 결정', '순환수', 'input_point', 'y_key', 'input_port_multiple_roots', 'input_tie',
        'net_model', 'composite_internal', 'TieBreak', 'dc_colour_not_unique', '꺼짐', r'`off`', 'S4-가', 'L8', 'swing_out_v', 'IT-2b', '봉인 9', '봉인 6', 'tol_V 미정', 'I_off', 's1v_predicates', '반전 수준 하한', 'peak_floor']
out = []
for tag, nm in FILES.items():
    L = open(D % nm, encoding='utf-8', newline='').read().split('\n')
    for k in KEYS:
        for n, l in enumerate(L):
            ms = list(re.finditer(k, l))
            if ms:
                m = ms[0]
                out.append('[%s] %s:%d x%d | %s' % (k, tag, n + 1, len(ms), l[max(0, m.start() - 90):m.end() + 110]))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grep_b2.txt'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(len(out))
