"""UB-1 착수 사실 보충(LUT·커널 평가 0): 되먹임 저항 표시, 막다른 넷을 읽는 gate, FF 귀속 문언별 합성 잔차, 판정 소비자 grep, 줄 번호 재측정.

실행: PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 C:/Python314/python.exe measure_ub0_extra.py
결과: 같은 폴더 ub0_extra.jsonl(회로마다 append), facts.txt(줄마다 append)
"""
import json
import math
import re
import subprocess
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills"
SKILL = Path(ROOT + "/skills/analog-gmid-design")
sys.path.insert(0, str(SKILL))

from gmid_engine.metrics._helpers_nodal import conductance_matrix, nodal_factor, nodal_solve  # noqa: E402
from gmid_engine.metrics._helpers_view import view_system  # noqa: E402
from gmid_engine.metrics.block_residual import block_residual  # noqa: E402
from gmid_engine.metrics.records import SmallSignalCircuit  # noqa: E402
from gmid_engine.tests.metrics import u7_ngcc as N  # noqa: E402

import s1v_hand  # noqa: E402

LIB = SKILL / "assets" / "library"
CIRCUITS = sorted(p.name[: -len(".topology.json")] for p in LIB.glob("*.topology.json") if not p.name.startswith("_"))
OUT = open(HERE / "ub0_extra.jsonl", "w", encoding="utf-8")
FACTS = open(HERE / "facts.txt", "w", encoding="utf-8")
_orig = s1v_hand.lib_supplies


def _supplies(name):
    try:
        return _orig(name)
    except KeyError:
        return dict(json.loads((LIB / (name + ".sizing_spec.json")).read_text(encoding="utf-8"))["human"]["supplies_v"]["values"])


s1v_hand.lib_supplies = _supplies


def emit(row):
    OUT.write(json.dumps(row, ensure_ascii=False) + "\n")
    OUT.flush()


def say(*parts):
    line = " ".join(str(p) for p in parts)
    print(line)
    FACTS.write(line + "\n")
    FACTS.flush()


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True).stdout.decode("utf-8", "replace")


def ff_literal_residual(ss, decl, vs, view_ground):
    """§2.5-4 문언 그대로(주경로 블록에 FF 셀 스탬프 없음, FF 기여 = merge 모델 + FF 셀 + 탭 구동)의 합성 잔차. 시제품."""
    fixed, drive_idx, sense, pairs, sense_nets = view_system(ss, decl)
    size = len(ss.nodes)
    index = {n: i for i, n in enumerate(ss.nodes)}
    volt, _r = nodal_solve(nodal_factor(conductance_matrix(ss.circuit, size), fixed), size, drive_idx)
    full = float(sense @ volt)
    excluded = {m for f in vs.ff for m in f.members}
    every = {n for b in vs.blocks for n in b.nodes}

    def chain(active):
        volts = dict(pairs)
        for block in vs.blocks:
            here = [f for f in active if f.merge_block == block.key]
            stamp_ff = {m for f in here for m in f.members}
            drive = {n: volts.get(n, 0.0) for n in block.inputs}
            for f in here:
                drive[f.tap] = volts.get(f.tap, 0.0)
            ground = {index[n] for n in tuple(ss.ground_nets) + tuple(view_ground)}
            driven = {index[n] for n in drive} | {index[n] for n in block.inputs}
            outside = {index[n] for n in every - set(block.nodes)}
            stop = ground | driven | outside
            unknown = {index[n] for n in block.nodes} - stop
            grew = True
            mos_on = set()
            while grew:
                grew = False
                for m in ss.circuit.mos:
                    if m.label in mos_on or (m.label in excluded and m.label not in stamp_ff):
                        continue
                    if m.d in unknown or m.s in unknown or m.label in stamp_ff:
                        mos_on.add(m.label)
                        if m.label in stamp_ff:
                            new = {m.d, m.s} - stop - unknown
                            unknown |= new
                        grew = True
            res = [r for r in ss.circuit.resistors if r.a in unknown or r.b in unknown]
            sub = SmallSignalCircuit(mos=tuple(m for m in ss.circuit.mos if m.label in mos_on), resistors=tuple(res))
            v, _ = nodal_solve(nodal_factor(conductance_matrix(sub, size), set(range(size)) - unknown), size, {index[n]: x for n, x in drive.items()})
            if v is None:
                return None
            volts.update({ss.nodes[i]: float(v[i]) for i in unknown | driven})
        return volts.get(sense_nets[0], 0.0) - (0.0 if sense_nets[1] is None else volts.get(sense_nets[1], 0.0))

    main = chain(())
    total = main
    for f in vs.ff:
        with_f = chain((f,))
        total += with_f - main                       # with_f 에는 FF gds 부하도 들어 있다 -- 경로 항과 부하 항이 섞이는 것이 이 문언의 문제
    return 20 * math.log10(abs(full)) - 20 * math.log10(abs(total)), 20 * math.log10(abs(full)) - 20 * math.log10(abs(main))


for name in CIRCUITS:
    try:
        doc = json.loads((LIB / (name + ".topology.json")).read_text(encoding="utf-8"))
        ss, structs, decls = N.library_case(name)
        _s1, s1v = s1v_hand.build_lib(name)
        raw = {v.id: v for v in s1v.views}
        gate_nets = {}
        for e in doc["netlist"]:
            gate_nets.setdefault(e["gate"], []).append(e["name"])
        res = {e["name"]: e for e in doc.get("passive_elements") or () if e["kind"] == "resistor"}
        conduct = {}
        for e in doc["netlist"]:
            for t in (e["drain"], e["source"]):
                conduct[t] = conduct.get(t, 0) + 1
        for e in res.values():
            for t in e["terminals"]:
                conduct[t] = conduct.get(t, 0) + 1
        one_terminal = sorted(n for n, c in conduct.items() if c == 1 and n not in doc["supply_nets"])
        far_gate = {n: gate_nets[n] for n in one_terminal if n in gate_nets and any(n in e["terminals"] for e in res.values())}
        emit({"circuit": name, "kind": "resistor_only_end_nets_with_gate_reader", "nets": far_gate})
        for vs, decl in zip(structs, decls):
            got = block_residual(ss, decl, vs)
            flags = [list(b.key) for b in got.blocks if b.decomposed_only]
            emit({"circuit": name, "kind": "decomposed_only", "view": vs.id, "blocks": flags, "n_blocks": len(vs.blocks)})
            row = {"circuit": name, "kind": "ff_attribution", "view": vs.id, "ff": len(vs.ff), "asbuilt_residual_db": got.gain_residual_db}
            if vs.ff:
                row["literal_residual_db"], row["main_chain_without_ff_vs_full_db"] = ff_literal_residual(ss, decl, vs, tuple(raw[vs.id].ac_ground))
            emit(row)
    except Exception:  # noqa: BLE001
        emit({"circuit": name, "kind": "failure", "trace": traceback.format_exc()})

say("# master", git("rev-parse", "master").strip())
say("# integ/it12", git("rev-parse", "integ/it12").strip(), "ss_nodal module in tree:", "metrics/ss_nodal.py" in git("ls-tree", "-r", "--name-only", "integ/it12"))
E = "skills/analog-gmid-design/gmid_engine"
for path, pat in (("metrics/sensitivity_gate.py", r"None in \(dec|not errors"), ("search/gate_run.py", r"return None|continue"), ("search/find_front.py", r"run_sensitivity_gate\(|if gate is not None"),
                  ("metrics/block_gain_model.py", r"bin 내부 극값|attach\.get"), ("metrics/block_model.py", r"^def |conductance_matrix"), ("metrics/block_residual.py", r"conductance_matrix|block_local_gain"),
                  ("metrics/ff_gm_ratio.py", r"conductance_matrix|block_local_gain"), ("metrics/offset_analysis.py", r"nodal_factor"), ("metrics/offset_systematic.py", r"nodal_factor")):
    text = git("show", "master:%s/%s" % (E, path))
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(pat, line):
            say("%s:%d: %s" % (path, i, line.strip()[:120]))
say("\n## grep 판정 소비자 (master, tests·md 제외)")
for pat in (r"block_local_gain\(", r"block_residual\(", r"gain_residual_db", r"decomposed_gain_db", r"residual_probe\(", r"coupled_residual\(", r"\.residual_probe", r"\"residual_probe\"", r"ff_gm_ratio\("):
    hits = [ln for ln in git("grep", "-n", "-E", pat, "master", "--", E + "/*.py").splitlines() if "/tests/" not in ln]
    say("--", pat, len(hits))
    for ln in hits:
        say("  ", ln.replace("master:" + E + "/", "")[:170])
say("\n## spec에 ff_gm_ratio 제약 선언")
say(git("grep", "-l", "ff_gm_ratio", "master", "--", "skills/analog-gmid-design/assets/library") or "0 files")
say("\n## floating 소비자")
say(git("grep", "-n", "floating", "master", "--", E + "/metrics/*.py", E + "/search/*.py")[:1200])
