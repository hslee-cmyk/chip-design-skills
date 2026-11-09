"""E-1 닫기 1회(원칙 2): SPICE GBW 여유가 음수면 활성 제약(GBW) 문턱 이동 Δ 를 secant 로 -- GBW ∝ 1/Cc 근사로 Cc 를
   Cc·(fu_spice / GBW_target) 로 옮긴 choice 를 만든다(손가락·전류 불변). argv: choice.json spice.json out.json"""
import json, sys
ch = json.load(open(sys.argv[1], encoding="utf-8"))
sp = json.load(open(sys.argv[2], encoding="utf-8"))
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/scripts")
import design as D
ch["x"]["Cc"] = ch["x"]["Cc"] * sp["fu"] / D.GBW_T
ch["close_e1"] = {"fu_spice": sp["fu"], "Cc_new": ch["x"]["Cc"]}
json.dump(ch, open(sys.argv[3], "w", encoding="utf-8"), indent=1)
