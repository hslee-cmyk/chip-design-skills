# 열일곱째 커밋 M5 -- design(wt/design-v115 e957ba44) 영향 자리 재grep
# 사용: python plan_v6386_design_grep17.py  -> 같은 폴더 plan_v6386_design_grep17.txt
import re, os, subprocess
W = r'C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-v115'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plan_v6386_design_grep17.txt')
files = ['gain-budget-gmid-sizing.40-engine.design.md', 'gain-budget-gmid-sizing.41-gain-budget.design.md',
         'gain-budget-gmid-sizing.42-gap-checklist.design.md', 'oracle-portability.design.md',
         'offset-trim.design.md', 'offset-strategy.design.md', 'gain-budget-gmid-sizing.00-common.design.md']
pats = {
  'tol_plus': r'VDSAT\s*\+\s*tol|VDsat\s*\+\s*tol|\+\s*tol_?[Vv][Dd][Ss]at|\+tol_VDsat|\+ ?tol_vdsat',
  'off_current': r'off_current_A|dc_off_current|_off_current|I_off',
  'conduction_floor': r'conduction_floor|dc_conduction_floor|_conduction_rows|peak_floor',
  'stage2': r'stage2|2단계|둘째 단계|두 단계',
  'g_eq_s': r'off_vgs0|g = s|off_device_on_signal_path|gvgs_self_edge',
  'V_on': r'V_on|off 유지|꺼짐 유지',
  'off_compare': r'off.{0,20}대조|선언 영역(과|을)? 대조',
  'P7_U69': r'P-7|U-69',
  'E_rows': r'E-13|E-21|E-22|E-35',
  'R0': r'R0 |R0\)|R0,|전도 행',
  'judged_by': r'judged_by',
  'dc_window_def': r'dc_window_def',
}
head = subprocess.run(['git', '-C', W, 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
with open(OUT, 'w', encoding='utf-8') as o:
    o.write(f'# design grep -- {W} HEAD {head}\n')
    for f in files:
        p = os.path.join(W, 'docs/02-design/features', f)
        lines = open(p, encoding='utf-8').read().split('\n')
        sec = ''
        for i, l in enumerate(lines, 1):
            if l.startswith('#'):
                sec = l.strip('# ').strip()[:70]
            hit = [k for k, v in pats.items() if re.search(v, l)]
            if hit:
                o.write(f'[{f[:28]}:{i} | {sec}] {",".join(hit)} :: {l[:220]}\n')
print('ok', OUT)
