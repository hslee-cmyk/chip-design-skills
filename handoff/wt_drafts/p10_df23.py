import json, collections, glob, os
R = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
os.chdir(R)
d = json.load(open('docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json', encoding='utf-8'))
it = d['items']
b = [x for x in it if x['role'] == '동작을 정함']
out = []
out.append(f'behavior {len(b)}')
out.append('behavior by plan_mapping ' + str(collections.Counter(x['plan_mapping'] for x in b).most_common()))
out.append('behavior new_subcat ' + str(collections.Counter(x.get('new_subcategory') for x in b if x['plan_mapping'].startswith('신규')).most_common()))
out.append('behavior by context ' + str(collections.Counter(x['context'][:10] for x in b).most_common()))
out.append('A py now ' + str(sorted(os.path.basename(p) for p in glob.glob('skills/analog-gmid-design/assets/*.py'))))
same = moved = gone = 0
gone_list = []
for x in b:
    try:
        L = open(x['file'], encoding='utf-8').read().splitlines()
    except Exception:
        gone += 1; continue
    sl = x['source_line'].strip()
    if x['line'] <= len(L) and L[x['line'] - 1].strip() == sl:
        same += 1
    elif any(l.strip() == sl for l in L):
        moved += 1
    else:
        gone += 1; gone_list.append((x['file'], x['line'], x['literal'], x['function']))
out.append(f'behavior items: line same {same} moved {moved} gone {gone}')
out.append('gone fn counter ' + str(collections.Counter(g[3] for g in gone_list).most_common()))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p10_df23.out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
