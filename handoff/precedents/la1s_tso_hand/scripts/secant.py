"""E-1 닫기 secant 1회(두 점 (Cc, fu) 에서 GBW 목표 Cc 를 직선으로) -- 곱셈 갱신이 분해능 근처에서 느리게 다가갈 때.
argv: choice_a.json spice_a.json choice_b.json spice_b.json out_choice.json"""
import json, sys
ca, sa, cb, sb = [json.load(open(p, encoding="utf-8")) for p in sys.argv[1:5]]
x0, y0 = ca["x"]["Cc"], sa["fu"]
x1, y1 = cb["x"]["Cc"], sb["fu"]
t = 7e6
x2 = x1 + (t - y1) * (x1 - x0) / (y1 - y0)
cb["x"]["Cc"] = x2
cb["close_e1_secant"] = {"pts": [[x0, y0], [x1, y1]], "Cc_new": x2}
json.dump(cb, open(sys.argv[5], "w", encoding="utf-8"), indent=1)
