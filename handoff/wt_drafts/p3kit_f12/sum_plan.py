import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'))
print('n',d['n'],'rules',d['rule_counts']);print('per_mod',d['per_mod']);print('upward',len(d['upward']),d['upward'][:8]);print('cycles',d['cycles']);print('unassigned',d['unassigned']);print('conflicts',d['conflicts']);print('reg_mm',d['reg_mismatch_n'],'mod7out',d['mod7_outside'],'docs',d['docstrings'])
print([ (k,v['rule']) for k,v in d['assignment'].items() if v['rule'] in ('A-7','A-K','A-3')]); print(d['assignment'].get('design_report.py::_kv_table'))
