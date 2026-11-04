import numpy as np, json, os, sys
p = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz"
print(os.path.getsize(p))
z = np.load(p, allow_pickle=False)
print(len(z.files), 'meta_json' in z.files, 'corner' in z.files, 'temp_c' in z.files)
m = json.loads(str(z['meta_json']))
print(str(z['corner']), float(z['temp_c']))
print(json.dumps({k: v for k, v in m.items() if k != 'model_files_sha256' and (not isinstance(v, list) or len(v) < 8)}, ensure_ascii=False, indent=0)[:3500])
print(json.dumps(m['model_files_sha256'], indent=1))
json.dump(m, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
