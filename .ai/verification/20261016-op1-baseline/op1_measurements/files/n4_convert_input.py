# -*- coding: utf-8 -*-
"""n4_convert_input.py -- verifier-owned mechanical converter: old oracle input (spice_oracle_input/1, process.models form)
-> new form of design oracle-portability v0.2.3 §11.1 (process.descriptor + simulator block). Plan N4-2a. DRAFT (OP-1).

usage: python n4_convert_input.py <old.json> <new.json> [--descriptor D.json] [--adapter ngspice] [--record rec.jsonl]

Field map (design §11.1, the only source used here):
  process.models            -> deleted (descriptor kinds)            [§11.1 삭제 칸]
  process.ngspice_exe       -> simulator.exe, then deleted           [§11.1 simulator.exe, 삭제 칸]
  process.diffusion         -> deleted (descriptor); old value kept in the record for the OP-2 equality check
  testbench.options         -> simulator.options, then deleted       [§11.1 'options 는 옛 testbench.options 를 옮긴 것']
  process.lut_npz           -> kept
  process.descriptor        <- {path, sha256} of --descriptor (absent: null + draft flag; such output is NOT valid for N4)
  simulator.adapter         <- --adapter (default 'ngspice')
  process.corner / temp_c   -> not written (old form has none; LUT meta is used, §11.2)
  output_reference          -> not written (old producers have none, §11.4)
Any other process.* key is NOT in the §11.1 map: the converter refuses unless --keep-unmapped is given, and the record
lists it (open point for the OP-0 mapping table). Nothing outside process/testbench.options is touched.
"""
import argparse, copy, hashlib, json, os, sys

MAPPED_PROCESS = {"models", "ngspice_exe", "diffusion", "lut_npz"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def convert(old, descriptor=None, adapter="ngspice", keep_unmapped=False):
    new = copy.deepcopy(old)
    p = new.get("process") or {}
    unmapped = sorted(set(p) - MAPPED_PROCESS)
    if unmapped and not keep_unmapped:
        raise SystemExit(f"unmapped process keys (not in design §11.1): {unmapped}")
    rec = {"unmapped_process_keys": unmapped, "old_diffusion": p.get("diffusion"),
           "old_models_kinds": sorted((p.get("models") or {}).keys()), "old_ngspice_exe": p.get("ngspice_exe")}
    exe = p.pop("ngspice_exe", None)
    p.pop("models", None)
    p.pop("diffusion", None)
    p["descriptor"] = {"path": descriptor, "sha256": sha(descriptor)} if descriptor else None
    tb = new.get("testbench") or {}
    opts = tb.pop("options", None)
    rec["options_moved"] = opts
    new["simulator"] = {"adapter": adapter, "exe": exe, "options": opts if opts is not None else {}}
    if opts is None:
        rec["options_absent"] = True        # X-D4: such an input stops with dc_tolerance_undeclared under the new core
    rec["draft_no_descriptor"] = descriptor is None
    return new, rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("old"); ap.add_argument("new")
    ap.add_argument("--descriptor"); ap.add_argument("--adapter", default="ngspice")
    ap.add_argument("--keep-unmapped", action="store_true"); ap.add_argument("--record")
    a = ap.parse_args(argv)
    old = json.load(open(a.old, encoding="utf-8"))
    new, rec = convert(old, a.descriptor, a.adapter, a.keep_unmapped)
    json.dump(new, open(a.new, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    rec.update(old=a.old, old_sha256=sha(a.old), new=a.new, new_sha256=sha(a.new), converter_sha256=sha(__file__))
    if a.record:
        with open(a.record, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False)[:600])
    return 0


if __name__ == "__main__":
    sys.exit(main())
