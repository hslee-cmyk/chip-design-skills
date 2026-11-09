"""post-35 재측정 -- 항목 목록(옛 값·적힌 곳·기대 방향)과 결과 기록·표.

    python -B p35_items.py v3     <G> <label>               # <G>/out/v3_<label>.json -> 항목 레코드 append
    python -B p35_items.py static <G>                       # <G>/out/{lines,anchors}_{old,new}.json, oog_*.txt, install_*.txt -> append
    python -B p35_items.py slow   <G> <kind>                # a32b | a32p | noop  (<G>/out/<kind>_new.jsonl vs 옛 jsonl)
    python -B p35_items.py add    <G> <id> <status> <new> [note]   # 셸에서 직접 한 줄(예: needs35, skipped)
    python -B p35_items.py table  <G>                       # results.jsonl -> 표(stdout + <G>/results/table.txt)

결과 파일: <G>/results/results.jsonl -- 항목마다 한 줄 append(중간에 죽어도 앞 항목은 남는다).
status: same(옛 값 = 새 값) | changed(달라짐 -- '적힌 곳'을 고쳐야 함) | needs35(도구가 35 전 판) | deferred(실제 test 실행 필요 -- 아래 note) | error | info
"""
import json
import os
import sys

DR = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts"
SPEC35 = "docs/02-design/specs/20260930-v3-changed-stmt-scope.spec.md"

# label -> (항목 id, 옛 대상, 옛 not_targeted, 적힌 곳, 옛 값을 낸 명령)
V3 = {
    "p9": ("V3-P9", 12, 16, SPEC35 + " '작성 전 실측' 1 표 P9 행; v3_scope_briefs.md §0.2 표",
           "v3scope_kit/measure_b26.py measure('p9_real','6bf510b','93b18db') -- scope_proto N2w"),
    "bf": ("V3-BF", 4, 93, "backfill_launch.sh:81 V3_WANT=4; draft_b26_backfill_audit.spec.md:180 'v3count 대상 4·not_targeted 93'; b26_backfill_briefs.md:71·136",
           "backfill_launch.sh stage_v3count(REV + SR 11800·11879 삭제, 실제 pytest) -- 옛 값은 시제품 N2w(b26_backfill_briefs §0.3)"),
    "b34": ("V3-B34", 10, 45, "b34_briefs.md:14·250 '대상 10(not_targeted 45)'; draft_b34.final.spec.md 'V3 계획' 표 10 id·318행; b34_commit_plan.md",
            "b34_kit/measure_b34.py(REV..sim-b34, scope_proto N2w) + v3scope_kit/probe_selection.py(현행 도구 55)"),
    "b26v4": ("V3-B26v4", 301, 2141, "draft_b26_1.spec.md 'V3 계획' 1(v4 301, 2,442); v3_scope_briefs.md §0.2; " + SPEC35 + " '작성 전 실측' 1",
              "v3scope_kit/measure_b26.py measure('b26_v4', B1, H4)"),
    "b26a": ("V3-B26A", 299, 2141, "draft_b26_1.spec.md:362·386(시나리오 A 299, 2,440); b26_reconcile/out/plan_summary.txt",
             "b26_reconcile plan_measure(시나리오 A) / 36e170e 재측정"),
    "b26v5": ("V3-B26v5", 299, 2136, "draft_b26_1.spec.md 'V3 계획' 1(착수 base 299); v3_scope_briefs.md §0.2 끝(v5 2,435/238/299); approval_20260930-v3-changed-stmt-scope.md 재측정 문단",
              "36e170e 재측정(C:/g210/kit measure_b26.py 사본 + v5 head) -- 이 키트 p35_heads.py가 같은 head를 다시 만든다"),
    "b26u3": ("V3-B26U3", 299, 2136, "draft_b26_1.spec.md 'V3 계획' 1·4(이름 직접 호출 test로 인벤토리 0 -> 1), b26_1_carry.sh check 단계",
              "H5 + 직접 호출 test 1개(p35_heads H5T), 가짜 pytest = U3 변이(range(i + 0, …))만 생존"),
}
B34_SPEC10 = ["stick_diagram:" + s for s in (
    "_import_analog_grammar:stmt_delete:body[4]", "_import_analog_grammar:except_body_delete:body[4].handlers[0]",
    "_import_analog_grammar:early_return:body[1]", "find_idiom_matches:stmt_delete:body[2]", "find_idiom_matches:early_return:body[1]",
    "find_stack_edges:stmt_delete:body[2]", "find_stack_edges:early_return:body[1]", "audit_theta_root_direction:stmt_delete:body[2]",
    "audit_theta_root_direction:stmt_delete:body[5]", "audit_theta_root_direction:early_return:body[1]")]
SR, SD = "sizing_recipe:", "stick_diagram:"
B26PRE_20 = [SR + s for s in (
    "_fixup_euler_blocked_rows:stmt_delete:body[5].body[13]", "_fixup_euler_blocked_rows:stmt_delete:body[5].body[14]",
    "_fixup_euler_blocked_rows:stmt_delete:body[5].body[16]",
    "optimize_full_circuit_budget._evaluate_row_split:stmt_delete:body[5].body[3].orelse[0]",
    "optimize_full_circuit_budget._evaluate_row_split:stmt_delete:body[5].body[3].orelse[1]",
    "optimize_full_circuit_budget:stmt_delete:body[12].body[3].body[5].body[3].orelse[0]",
    "optimize_full_circuit_budget:stmt_delete:body[12].body[3].body[5].body[3].orelse[1]",
    "resolve_stack_layout:stmt_delete:body[5]",
    "run_matching_safety_with_finger_growth:stmt_delete:body[10].body[1]", "run_matching_safety_with_finger_growth:stmt_delete:body[10].body[2]",
    "run_matching_safety_with_finger_growth:stmt_delete:body[11]", "run_matching_safety_with_finger_growth:stmt_delete:body[12]",
    "run_matching_safety_with_finger_growth:stmt_delete:body[13]", "run_matching_safety_with_finger_growth:stmt_delete:body[14]")] + [SD + s for s in (
    "propose_device_roles_gap_fill:stmt_delete:body[49]", "propose_vertical_stack_id_gap_fill:stmt_delete:body[2]",
    "run_full_circuit_audit:stmt_delete:body[16]", "run_full_circuit_audit:stmt_delete:body[17]",
    "find_differential_pair_candidates:const+:body[8].body[3].body[1].body[0].iter.args[0].right",
    "find_differential_pair_candidates:arith:body[8].body[3].body[1].body[0].iter.args[0]")]
EQ4 = [SD + "find_differential_pair_candidates:const-:body[8].body[3].body[1].body[0].iter.args[0].right",
       SD + "_propose_L_roles:stmt_delete:body[2]", SD + "_propose_L_roles:stmt_delete:body[4]",
       SD + "propose_device_roles_gap_fill:const-:body[40].body[8].value.slice"]
IDS = {"b34": B34_SPEC10, "b26v4": B26PRE_20, "b26a": EQ4, "b26v5": EQ4}

OLD_SLOW = {"a32b": DR + "/g1_kit/out/a32_base_4a286f0.jsonl", "a32p": DR + "/g1_kit/out/a32_proto_4a286f0.jsonl",
            "noop": DR + "/g1_kit/out/noop_base_4a286f0.jsonl"}


def res_path(G):
    os.makedirs(G + "/results", exist_ok=True)
    return G + "/results/results.jsonl"


def add(G, rec):
    with open(res_path(G), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("  [%s] %s: %s -> %s (%s)" % (rec["status"], rec["id"], rec.get("old"), rec.get("new"), rec.get("note", "")[:160]))


def ids_write(G):
    os.makedirs(G + "/out", exist_ok=True)
    for k, v in IDS.items():
        with open(G + "/out/ids_%s.json" % k, "w", encoding="utf-8") as fh:
            json.dump(v, fh)


def do_v3(G, label):
    iid, old_t, old_nt, where, cmd = V3[label]
    p = G + "/out/v3_%s.json" % label
    if not os.path.exists(p):
        add(G, {"id": iid, "status": "error", "old": "%d/%d" % (old_t, old_nt), "new": None, "where": where, "cmd": cmd, "note": "결과 파일 없음"})
        return
    r = json.load(open(p, encoding="utf-8"))
    if "error" in r:
        add(G, {"id": iid, "status": "error", "old": "%d/%d" % (old_t, old_nt), "new": None, "where": where, "cmd": cmd, "note": r["error"][:300]})
        return
    proto = "%d/%d" % (r["proto_targeted"], r["proto_not_targeted"])
    if not r.get("has35"):
        add(G, {"id": iid, "status": "needs35", "old": "%d/%d" % (old_t, old_nt), "new": "도구 %s(전체 실행, not_targeted 없음)" % r.get("mutants"),
                "proto": proto, "where": where, "cmd": cmd, "note": "도구에 targets_by_def 없음 -- 35 병합 전 판. proto(scope_proto N2w) = " + proto})
        return
    new_t, new_nt = r["mutants"], r["not_targeted"]
    if label == "bf":
        new_t = r.get("def_key_targeted")
    st = "same" if (new_t, new_nt) == (old_t, old_nt) else "changed"
    note = "proto %s, 도구-proto 대칭차 %s, out 레코드 %d(대상 %d·밖 %d), 순서 %s" % (
        proto, r.get("sym_diff"), r["out_records"], r["out_targeted"], r["out_not_targeted"], r.get("order_ok"))
    if label == "bf":
        note += ", targets_by_def 키 %s" % r.get("def_keys")
    add(G, {"id": iid, "status": st, "old": "%d/%d" % (old_t, old_nt), "new": "%s/%s" % (new_t, new_nt), "proto": proto,
            "where": where, "cmd": cmd, "note": note})
    cs = r.get("carry_subset")
    if cs is not None:
        add(G, {"id": "CARRY5-" + label, "status": "same" if cs.startswith("ok") else "changed", "old": "가정(계약 5 문장)", "new": cs,
                "where": "b26_1_carry.sh:248~256(범위 card 35 계약 5 단정)", "cmd": "p35_v3count.py carry_subset(블록 그대로 exec)",
                "note": "가짜 pytest 출력에 대한 모양 단정. 실제 1차 출력(attempt1_v3.json) 전체 단정은 B26-1 1차 auditor 뒤 b26_1_carry.sh check가 한다 -- deferred"})
    cf = r.get("carry_full")
    if cf is not None:
        add(G, {"id": "CARRY-FULL-" + label, "status": "same" if cf.startswith("PASS") else "changed",
                "old": "spec·모의 도구로만 정한 모양(m1~m4)", "new": cf, "survivors": r.get("survivors"),
                "where": "b26_1_carry.sh check 단계 V3 heredoc(`local v3; v3=$(... attempt1_v3.json ... <<'EOF'`) -- b26_1_kit_selftest/out_check_test.sh의 피검",
                "cmd": "p35_v3count.py --carry-full(heredoc 그대로 추출, 인자 = 판정 JSON·--out·head SD·V3_RE·SD)",
                "note": "FAIL이면 carry 쪽 정정 대상(오케스트레이터 지시). 생존 %d개(기대 1 = U3)" % r.get("n_survivors", -1)})
    ic = r.get("ids_check")
    if ic is not None:
        if label == "b34":
            add(G, {"id": "V3-B34-ids", "status": "same" if r["ids_targeted"] == 10 and r["mutants"] == 10 else "changed", "old": "10/10",
                    "new": "%d/%d" % (r["ids_targeted"], r["ids_total"]), "where": "draft_b34.final.spec.md 'V3 계획' 표 10 id",
                    "cmd": "b34_kit/measure_b34.py spec10", "note": "도구 대상 id = spec 10 id인지"})
        elif label == "b26v4":
            add(G, {"id": "B26PRE-20", "status": "same" if r["ids_targeted"] == 20 else "changed", "old": "20/20 대상",
                    "new": "%d/%d 대상" % (r["ids_targeted"], r["ids_total"]),
                    "where": "draft_b26pre.spec.md:13~14·335~357(주표 20 = N2w 대상), b26pre_launch.sh:74 제목 '주표 20 중 18 죽임'",
                    "cmd": "b26_reconcile 통합 측정(v4 head, scope_proto/v3_scope_widen N2w)",
                    "note": "대상 여부만. '18 죽임'은 b26pre test가 있어야 잰다 -- b26pre 순서 7 auditor(deferred). 대상 밖 id: %s" %
                            [k for k, s in ic.items() if s != "targeted"]})
        elif label in ("b26a", "b26v5"):
            want = {"b26a": {i: "targeted" for i in EQ4},
                    "b26v5": {EQ4[0]: "targeted", EQ4[3]: "absent"}}[label]
            ok = all(ic.get(k) == v for k, v in want.items())
            add(G, {"id": "EQ4-" + label, "status": "same" if ok else "changed",
                    "old": {"b26a": "등가 4 전부 대상", "b26v5": "range const- 대상, [0] const- 없음(C2)"}[label],
                    "new": ", ".join("%s=%s" % (k.split(":", 1)[1][:48], v) for k, v in ic.items()),
                    "where": "draft_b26_1.spec.md:386~397(등가 4 → C1·C2 뒤 1), b26_1_carry.sh:89 V3_RE",
                    "cmd": "b26_reconcile/out/plan_summary.txt REMAIN 4(시나리오 A)",
                    "note": "대상 집합 단정만. '4 → 1 생존'은 실제 test 실행(B26-1 1차 auditor attempt1_v3.json)에서만 -- deferred. "
                            "_propose_L_roles body[4]는 C1 뒤 다른 문장을 가리킬 수 있어 v5에서는 단정하지 않는다"})


def do_static(G):
    lo = json.load(open(G + "/out/lines_old.json", encoding="utf-8"))
    ln = json.load(open(G + "/out/lines_new.json", encoding="utf-8"))
    for tag, where in (("G1", "draft_p3_g1.spec.md '작성 전 실측' 1(0f23786 줄), g1_briefs.md §0.1 26~27행·§0.7 ③"),
                       ("B33", "draft_b33.final.spec.md 292~301행 '작성 전 실측' 1·2(0f23786 줄 215·317·315·354-356·387-392)"),
                       ("35", "(표지) b34_launch.sh:209·b26pre_launch.sh:244·backfill_launch.sh:255 `grep -c targets_by_def` ≥ 1")):
        for k in sorted(set(lo) | set(ln)):
            if not k.startswith(tag + "|"):
                continue
            o, n = lo.get(k), ln.get(k)
            add(G, {"id": "LINES-" + k, "status": "same" if o == n else "changed", "old": o, "new": n, "where": where,
                    "cmd": "p35_static.py lines(grep -n 같은 식)", "note": ""})
    ko, kn = lo.get("V3 output keys"), ln.get("V3 output keys")
    exp = (ko or []) + ["not_targeted", "targets_by_def"]
    add(G, {"id": "G1-KEYS", "status": "same" if kn == exp else "changed", "old": ko, "new": kn,
            "where": "g1_briefs.md §0.7 ③(V3 출력 키 = 34·35 키 + G1 defs·moved·move_rejected 겹침 없음), " + SPEC35 + " 계약 5",
            "cmd": "p35_static.py lines -> main 마지막 json.dumps 키", "note": "기대 = 옛 키 + not_targeted, targets_by_def. G1 키와 겹침: %s" %
            sorted(set(kn or []) & {"defs", "moved", "move_rejected"})})
    ao = {a["label"]: a["count"] for a in json.load(open(G + "/out/anchors_old.json", encoding="utf-8"))}
    an = {a["label"]: a["count"] for a in json.load(open(G + "/out/anchors_new.json", encoding="utf-8"))}
    for k in ao:
        add(G, {"id": "G1-ANCH-" + k, "status": "same" if ao[k] == an.get(k) else "changed", "old": ao[k], "new": an.get(k),
                "where": "g1_kit/install_proto.py sub(..., '%s'); g1_briefs.md 113~114행('35 병합 뒤 앵커를 병합본에 맞춰 고친다')" % k,
                "cmd": "p35_static.py anchors", "note": "1이 아니면 install_proto가 이 앵커에서 멈춘다(측정 전용 시제품 -- 역할 산출물 아님)"})
    io_ = open(G + "/out/install_old.txt", encoding="utf-8").read().strip().splitlines()[-1:] if os.path.exists(G + "/out/install_old.txt") else ["?"]
    in_ = open(G + "/out/install_new.txt", encoding="utf-8").read().strip().splitlines()[-1:] if os.path.exists(G + "/out/install_new.txt") else ["?"]
    add(G, {"id": "G1-INSTALL", "status": "same" if io_ == in_ else "changed", "old": io_[0], "new": in_[0],
            "where": "g1_briefs.md 113행('4a286f0에서도 installed 4'), draft_p3_g1.spec.md 키트 표", "cmd": "python -B install_proto.py <트리 사본>", "note": ""})
    oo = open(G + "/out/oog_old.txt", encoding="utf-8").read().strip().splitlines()
    on = open(G + "/out/oog_new.txt", encoding="utf-8").read().strip().splitlines()
    files = lambda L: len({l.split(":")[1] for l in L if l.count(":") >= 2})
    add(G, {"id": "G1-OOG", "status": "same" if oo == on else "changed", "old": "%d줄·%d파일" % (len(oo), files(oo)),
            "new": "%d줄·%d파일" % (len(on), files(on)),
            "where": "draft_p3_g1.spec.md:278~279(4a286f0 9줄·8 스크립트), g1_briefs.md:29·178·316·382(dd60db6 7개)",
            "cmd": "git grep -n -E '(mc|mutate_changed)\\.(changed_defs|def_hash)\\(' <rev> -- . ':!*.jsonl' ':!tools/gates'",
            "note": "더해진 줄: %s" % [l for l in on if l.split(":", 1)[1] not in {x.split(":", 1)[1] for x in oo}][:6]})


def steps(path):
    out = {}
    for l in open(path, encoding="utf-8"):
        if not l.strip():
            continue
        c = json.loads(l)
        if "case" not in c:
            continue
        out[c["case"]] = {"verdict": c.get("verdict"), "steps": {s.get("step"): (s.get("exit"), s.get("verdict")) for s in c.get("steps", [])}}
    return out


def do_slow(G, kind):
    newp = G + "/out/%s_new.jsonl" % kind
    where = {"a32b": "g1_briefs.md §0.7 ⑥(기대: 93 단계 exit가 표 왼쪽 열과 같음), g1_kit/out/a32_base_4a286f0.*",
             "a32p": "g1_briefs.md §0.4·§0.7 ⑥(시제품 93 PASS), g1_kit/out/a32_proto_4a286f0.*",
             "noop": "g1_briefs.md §0.7 ⑥ 무동작 미리보기(--only 34- --only 35-), g1_kit/out/noop_base_4a286f0.*"}[kind]
    if not os.path.exists(newp):
        add(G, {"id": "G1-" + kind.upper(), "status": "error", "old": None, "new": None, "where": where, "cmd": kind, "note": "새 로그 없음"})
        return
    o, n = steps(OLD_SLOW[kind]), steps(newp)
    for case in sorted(set(o) | set(n)):
        oc, nc = o.get(case), n.get(case)
        if oc and nc:
            diff = [s for s in set(oc["steps"]) | set(nc["steps"]) if oc["steps"].get(s, (None,))[0] != nc["steps"].get(s, (None,))[0]]
            st = "same" if oc["verdict"] == nc["verdict"] and not diff else "changed"
            note = "exit 다른 단계 %d: %s" % (len(diff), sorted(diff)[:5])
        else:
            st, note = "changed", "케이스가 한쪽에만 있다"
        sm = lambda c: None if c is None else "%s(%d단계, exit %s)" % (c["verdict"], len(c["steps"]),
                                                                        dict(sorted(__import__("collections").Counter(str(e) for e, _v in c["steps"].values()).items())))
        add(G, {"id": "G1-%s-%s" % (kind.upper(), case), "status": st, "old": sm(oc), "new": sm(nc), "where": where,
                "cmd": "run_all.py --phase 0.5 --mode direct --only ... (g1_kit/run_attack32.sh·run_noop.sh와 같은 명령, 출력은 scratch)", "note": note})


def table(G):
    rows = [json.loads(l) for l in open(res_path(G), encoding="utf-8") if l.strip()]
    out = ["%-9s %-58s %-34s %-34s" % ("status", "item", "old", "new")]
    for r in rows:
        f = lambda x: (json.dumps(x, ensure_ascii=False) if not isinstance(x, str) else x)[:34]
        out.append("%-9s %-58s %-34s %-34s" % (r["status"], r["id"][:58], f(r.get("old")), f(r.get("new"))))
    from collections import Counter
    out.append("합계 %d항목: %s" % (len(rows), dict(Counter(r["status"] for r in rows))))
    s = "\n".join(out)
    open(G + "/results/table.txt", "w", encoding="utf-8").write(s + "\n")
    print(s)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    G = a[1].replace("\\", "/").rstrip("/")
    if a[0] == "ids":
        ids_write(G)
    elif a[0] == "v3":
        do_v3(G, a[2])
    elif a[0] == "static":
        do_static(G)
    elif a[0] == "slow":
        do_slow(G, a[2])
    elif a[0] == "add":
        add(G, {"id": a[2], "status": a[3], "old": None, "new": a[4], "note": a[5] if len(a) > 5 else ""})
    elif a[0] == "table":
        table(G)
    else:
        raise SystemExit("모르는 하위 명령 " + a[0])
