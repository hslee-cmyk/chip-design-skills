"""재판정 계획. 앞 판정 plan.json(bin 표 = pm3 .model, include = 생성기 model_includes, records = 세트 meta 전부, set_versions = 세트 meta `ngspice`)을
읽어 값을 그대로 두고 C-10~C-13 칸을 더한다. 새 칸 근거:
 - slices: manifest 슬라이스 32 전부, kind = manifest device, scale_to_m = 1 (L 멤버는 m, meta axes.L_m과 같음을 아래에서 재확인)
 - combined_sets: 위치 선언 cap_npz, verify_midpoints
 - bound_sets: 위치 선언 noise, mismatch
 - location: 격리 복제본의 위치 선언
 - kinds[*].meta_key: r2 meta model_bin_per_L_at_w_ref 키 = kind 이름과 같음(아래 재확인)
옛 source 칸(값 대조 입력)과 `_` 칸은 뺀다."""
import json, sys
import numpy
T = "C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit"
R = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2"
ISO = T + "/op7a-iso2"
LOC = ISO + "/skills/analog-gmid-design/assets/lut_v2_location.json"
plan = json.load(open(T + "/work/plan.json", encoding="utf-8"))
del plan["source"]
man = json.load(open(R + "/manifest.json", encoding="utf-8"))
loc = json.load(open(LOC, encoding="utf-8"))
plan["slices"] = [{"set": s["file"], "kind": s["device"], "npz": f"{R}/{s['file']}", "scale_to_m": 1.0} for s in man["slices"]]
plan["combined_sets"] = [{"set": k, "npz": f"{R}/{loc['files'][k]['path']}"} for k in ("cap_npz", "verify_midpoints")]
plan["bound_sets"] = [{"set": k, "npz": f"{R}/{loc['files'][k]['path']}"} for k in ("noise", "mismatch")]
plan["location"] = LOC
with numpy.load(plan["combined_sets"][0]["npz"]) as z:
    m = json.loads(str(z["meta_json"]))
    assert abs(float(z["L"][0]) - m["axes"]["L_m"][0]) == 0.0
for k in plan["kinds"]:
    assert k["name"] in m["model_bin_per_L_at_w_ref"]
    k["meta_key"] = k["name"]
json.dump(plan, open(sys.argv[1], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("slices", len(plan["slices"]), "kinds", [k["meta_key"] for k in plan["kinds"]])
