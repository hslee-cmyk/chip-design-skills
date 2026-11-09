import hashlib, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
O, ISO = sys.argv[1], sys.argv[2]          # O = 출력 경로(<iso> 밖), ISO = HEAD로 되돌린 <iso>(계약값의 supply_nets를 HEAD library에서 읽는다)
ld = lambda n: json.load(open(os.path.join(O, n), encoding="utf-8")) if os.path.exists(os.path.join(O, n)) else None
# stdout 사본 비교는 SLSQP 진행 줄의 경과 시간 `elapsed=<초>s`만 가린다(파일럿 stdout은 경과 시간을 찍는다 -- v8 실측, 부록 A F3v8)
fh = lambda n: hashlib.sha256(re.sub(rb"elapsed=[0-9.]+s", b"elapsed=<T>s", open(os.path.join(O, n), "rb").read())).hexdigest() if os.path.exists(os.path.join(O, n)) else None
# 의도된 변경 목록(v8.2, D-28 (e) -- 사이 card 계약에서 유도, 실측 부록 A F1v82~F3v82):
#   E-INST instance.json 최상위 키: 없음(B34 계약 7·B26-1 계약 8 = instance.json 같음, b26pre = test-only,
#     backfill의 relaxed_pairs[i]["interdig_ok"]는 pipeline_result에만 있고 save_instance_json이 쓰지 않는다)
#   E-LIB: load_topology meta 키 "rails"(B26-1 계약 2·8) -- 해시에서 빼고(e_lib_p3.py 인자) 계약값 RailDeclaration(nets = 그 회로 supply_nets)로 따로 판정
EXCL_INST = ()
MASK_META = ("rails",)
bad = []
for c in ("current_reuse_telescopic_ota", "folded_cascode"):
    d, p, h = ld("p2d_df36_%s.json" % c), ld("p2d_p3_%s.json" % c), ld("h_p3_%s.json" % c)
    if d is None or p is None:
        print("E5 INVALID: P2D E-INST 출력 없음 %s" % c); bad.append(c); continue
    # 동등 확인(먼저): F1 전 판(P2D)에서 e_inst_p3 = e_inst_df36 (engine_origin 키 하나만 다르고 df36의 항목을 포함, stdout 사본 같음)
    diff = sorted(k for k in set(d) | set(p) if d.get(k) != p.get(k))
    sub = all(p["engine_origin"].get(k) == v for k, v in d["engine_origin"].items())
    if diff != ["engine_origin"] or not sub or fh("p2d_df36_%s.json.stdout.txt" % c) != fh("p2d_p3_%s.json.stdout.txt" % c):
        print("E5 INVALID: e_inst_p3 ≠ e_inst_df36 on P2D %s (다른 키 %s, 포함 %s)" % (c, diff, sub)); bad.append(c); continue
    strip = lambda r: {k: v for k, v in r["field_sha256"].items() if k not in EXCL_INST}
    ok = (h is not None and h["exists"] and not h["fail_in_stdout"] and h["path_string_hits"] == []
          and h["topology_ref_equals_expected_contract1"] and p["topology_ref_equals_expected_contract1"]
          and strip(h) == strip(p) and (EXCL_INST or (h["raw_sha256"] == p["raw_sha256"]
                                                      and h["without_topology_ref_sha256"] == p["without_topology_ref_sha256"])))
    print("E5 E-INST %s %s" % (c, "같음" if ok else "다름/실패")); ok or bad.append(c)
e0, q0, m0, m1 = ld("p2d_elib.json"), ld("p2d_elibp3_nomask.json"), ld("p2d_elibp3.json"), ld("h_elibp3.json")
# 동등 확인(먼저): P2D에서 e_lib_p3(MASK 없음) = e_lib.py (더한 키 masked_meta_keys·circuits.*.masked 밖 전부 같음)
dropk = lambda r: {**{k: v for k, v in r.items() if k not in ("masked_meta_keys", "circuits")},
                   "circuits": {n: {k: v for k, v in cv.items() if k != "masked"} for n, cv in r["circuits"].items()}}
if e0 is None or q0 is None or dropk(q0) != e0:
    print("E5 INVALID: e_lib_p3(MASK 없음) ≠ e_lib on P2D"); bad.append("E-LIB-equiv")
else:
    lib_ok = (m0 is not None and m1 is not None and m0["masked_meta_keys"] == m1["masked_meta_keys"] == sorted(MASK_META)
              and m0["hash"] == m1["hash"] and set(m0["circuits"]) == set(m1["circuits"])
              and all(v["ok"].get("load") for v in m1["circuits"].values()))
    print("E5 E-LIB(rails 뺀 해시) %s (%d 회로)" % ("같음" if lib_ok else "다름/실패", len(m1["circuits"]) if m1 else 0)); lib_ok or bad.append("E-LIB")
    for n in sorted(m1["circuits"]) if m1 else []:   # 뺀 키의 계약값(B26-1 계약 1·2·8): HEAD = RailDeclaration(nets = 그 회로 supply_nets), P2D = 없음 또는 같은 값
        nets = json.load(open(os.path.join(ISO, "skills", "analog-gmid-design", "assets", "library", n + ".topology.json"), encoding="utf-8")).get("supply_nets")
        want = {"__set__": sorted(nets, key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False))} if isinstance(nets, list) else None
        hv, bv = m1["circuits"][n]["masked"].get("rails"), (m0["circuits"].get(n) or {}).get("masked", {}).get("rails")
        cok = (want is not None and isinstance(hv, dict) and hv.get("__dc__") == "RailDeclaration" and hv.get("nets") == want
               and (bv == "<ABSENT>" or bv == hv))
        if not cok:
            print("E5 E-LIB rails 계약 FAIL %s (HEAD %s, P2D %s, 기대 nets %s)" % (n, hv, bv, nets)); bad.append("rails:" + n)
print("E5 E-LIB/E-INST PASS" if not bad else "E5 E-LIB/E-INST FAIL " + ",".join(bad))
