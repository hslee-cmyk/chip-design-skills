# v1.16.3 낡은 문언 잔재 -- 표지 없는 줄만 출력(resid_163.txt).
import re, os
D = r'C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115/docs/02-design/features/gain-budget-gmid-sizing.%s.design.md'
KEYS = [r'\+ tol_V', r'\+ tol_vdsat', r'VDSAT \+', 'dc_window_def', '_conduction_rows', '전도 행', r'\bR0\b', 'V_on', 'off_vgs0', 'off_device_on_signal_path', 'bias_fixed_net', 'gvgs_self_edge', 'dc_conduction_floor', 'conduction_floor', 'dc_off_current', 'off_current_A', 'dc_seal_conduction', '같은 DC 엣지 없는', 'U-69', r'P-7\b', 'S4-가', 'E-19', 'E-21', 'E-22']
out = []
for tag, nm in (('D40', '40-engine'), ('D41', '41-gain-budget'), ('D42', '42-gap-checklist')):
    for n, l in enumerate(open(D % nm, encoding='utf-8', newline='').read().split('\n')):
        if 'v1.16.3' in l[:60] or '보류' in l[:40]:
            continue
        hit = [k for k in KEYS if re.search(k, l)]
        if hit:
            m = re.search(hit[0], l)
            out.append('%s:%d %s | %s' % (tag, n + 1, ','.join(hit), l[max(0, m.start() - 70):m.end() + 70]))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resid_163.txt'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('\n'.join(out))
