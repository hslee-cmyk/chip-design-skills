# -*- coding: utf-8 -*-
"""card 20261104-op1b 실행 스크립트(작성 = 구현, 실행·판정 = auditor). op1b_lib의 함수를 부른다.

하위 명령
  feasibility  A-2(시뮬레이터 없음): F-1 npz `corner`·`temp_c`, F-2 kind별 bundle_rules, F-3 meta_json 모양, F-4 파일 sha = 위치 선언.
  run          A-3·A-9(ngspice 실행): 옛 오라클(--old-root = 5fea301e 격리 worktree)로 입력을 순차 2회, 범주·결정성·판 대조,
               R10 MC는 vos_recompute로 표본별 V_os 대조, 변환(C-8) 결과 저장. 한 입력이라도 어기면 Op1bStop으로 멈춘다(대체 입력 없음).

사용
  python -P run_op1b.py feasibility --repo R --location L.json --out out.json [--roles roles.json] [--ids R1 R10]
  python -P run_op1b.py run --repo R --location L.json --old-root W --exe EXE --decl D.json --adapter NAME --work DIR --baseline DIR [--ids ...] [--descriptor PATH SHA]
  roles.json = {PDK 루트 기준 상대 경로: "model_file" | "generation_aux_input"} (검증자가 §12.5 근거 (a)(b)를 재서 만든 값, 판정 기록 안).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import op1b_lib as L  # noqa: E402
import vos_recompute as V  # noqa: E402

OP1_TMP = ".ai/verification/20261016-op1-baseline/baseline/files/pytest/tmp/"
# interface 3 대표 입력 목록(판정 기록의 고정 목록이며 규칙이 아니다): id, 입력 상대 경로, sha256 앞 12자, bias, 범주
INPUTS = [
    ("R1", "sim_fb_b10/t.input.json", "df9d235eb586", ["free"], ["op", "ac", "rail", "stable"]),
    ("R2", "fbstab0/o/t.input.json", "995ee6667d99", ["free"], ["op", "ac", "beta_loop", "rail"]),
    ("R3", "ratio0/o/t.input.json", "b59680b5a477", ["free", "forced"], ["op", "ac", "ratio", "rail"]),
    ("R4", "test_source_follower_rout0/o/t.input.json", "24b81a2e25c1", ["free", "forced"], ["op", "ac", "rout", "rail"]),
    ("R5", "test_iso_spice_values_match_in0/o/t.input.json", "af5a2e89f918", ["iso"], ["op"]),
    ("R6", "classic0/o/t.input.json", "32273556a36f", ["free"], ["op", "ac", "unstable"]),
    ("R7", "rhp0/o/t.input.json", "65dcb06206c7", ["free", "forced"], ["op", "ac", "stability"]),
    ("R8", "test_sustained_oscillation_rb10/o/t.input.json", "f8644260940c", ["free"], ["op", "ac", "stability"]),
    ("R9", "rc_noise0/o/t.input.json", "aa879a99f2f7", ["free"], ["op", "ac", "noise"]),
    ("R10", "mc5t0/o/t.input.json", "f8e53e2f38e3", ["free"], ["op", "ac", "mc"]),
]


def sha_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_input(repo, rel, sha12):
    p = os.path.join(repo, OP1_TMP, rel)
    if sha_file(p)[:12] != sha12:
        raise L.Op1bStop("input_sha_differs", rel)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def read_bytes(p):
    with open(p, "rb") as f:  # 없으면 FileNotFoundError(include_bundle 계약)
        return f.read()


def resolve_lut(repo, location):
    loc = json.load(open(os.path.join(repo, location), encoding="utf-8"))
    root = os.environ.get(loc["root"]["env"], loc["root"]["default"])
    pdk = os.environ.get(loc["pdk_root"]["env"], loc["pdk_root"]["default"])
    f = loc["files"]["cap_npz"]
    return posix(os.path.join(root, f["path"])), f["sha256"], pdk


def posix(p):
    return p.replace("\\", "/")


def lut_meta(lut_path):
    z = np.load(lut_path, allow_pickle=False)
    members = set(z.files)
    meta_text = str(z["meta_json"]) if "meta_json" in members else None
    corner = str(z["corner"]) if "corner" in members else None
    temp = float(z["temp_c"]) if "temp_c" in members else None
    return meta_text, corner, temp


def selected(ids):
    rows = [r for r in INPUTS if not ids or r[0] in ids]
    if ids and len(rows) != len(set(ids)):
        raise L.Op1bStop("id_unknown", sorted(set(ids) - {r[0] for r in rows}))
    return rows


# ---------------------------------------------------------------- feasibility (A-2)
def cmd_feasibility(a):
    lut_path, lut_sha, pdk = resolve_lut(a.repo, a.location)
    out = {"lut": lut_path, "f4_sha_equal": sha_file(lut_path) == lut_sha}
    meta_text, corner, temp = lut_meta(lut_path)
    out["f1"] = {"corner": corner, "temp_c": temp}
    shape = L.provenance_shape(meta_text)
    out["f3_shape"] = shape
    roles = json.load(open(a.roles, encoding="utf-8")) if a.roles else {}
    out["roles_declared"] = sorted(roles)
    failures = []
    if not out["f4_sha_equal"]:
        failures.append("F-4")
    if corner is None or temp is None:
        failures.append("F-1")
    if shape != "nested":
        failures.append("F-3")
    f2 = {}
    if not failures:
        meta = json.loads(meta_text)
        meta_keys = sorted(meta["model_files_sha256"])
        for rid, rel, sha12, _b, _c in selected(a.ids):
            inp = load_input(a.repo, rel, sha12)
            row = L.lut_files_row(inp, lut_sha, shape, meta_keys)[0]
            for kind, key in sorted(row["kinds"].items()):
                if kind in f2:
                    continue
                m = inp["process"]["models"][kind]
                entries = [i.replace("{corner}", corner) for i in m["includes"]]
                bundle = L.include_bundle(entries, read_bytes)
                texts = {k: open(k, encoding="utf-8", errors="replace").read() for k in bundle}
                aux_read = lambda rel_p: (open(os.path.join(pdk, rel_p), "rb").read()  # noqa: E731
                                          if os.path.exists(os.path.join(pdk, rel_p)) else None)
                reasons, raw_only = L.bundle_rules(meta["model_files_sha256"][key], roles, bundle, texts, m["subckt"], aux_read)
                f2[kind] = {"meta_key": key, "reasons": reasons, "raw_only": raw_only, "bundle_files": len(bundle)}
                if reasons:
                    failures.append("F-2:" + kind)
    out["f2"] = f2
    out["failures"] = failures
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))
    if failures:
        raise L.Op1bStop("feasibility_failed", failures)
    return 0


# ---------------------------------------------------------------- run (A-3, A-9)
def isolated_env(env, home_dir):
    e = dict(env)
    e["HOME"] = e["USERPROFILE"] = home_dir
    for k in ("HOMEDRIVE", "HOMEPATH", "SPICE_USERINIT_DIR"):
        e.pop(k, None)
    return e


def check_decl(decl_p):
    d = json.load(open(decl_p, encoding="utf-8"))
    text = d["compat"]["spiceinit_text"]
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != d["compat"]["spiceinit_sha256"]:
        raise L.Op1bStop("compat_decl_sha_wrong")
    return d


def one_run(a, decl, rid, inp_path, biases, out_dir, home_dir):
    for p in (out_dir, home_dir):
        shutil.rmtree(p, ignore_errors=True)
        os.makedirs(p)
    if decl["compat"]["spiceinit_text"]:
        with open(os.path.join(out_dir, ".spiceinit"), "w", encoding="utf-8", newline="") as f:
            f.write(decl["compat"]["spiceinit_text"])
    cmd = [sys.executable, "-P", posix(os.path.join(a.old_root, "skills/analog-gmid-design/tools/spice_oracle/oracle_run.py")),
           inp_path, out_dir, "--bias", *biases, "--ngspice", a.exe]
    pr = subprocess.run(cmd, cwd=a.old_root, env=isolated_env(os.environ, home_dir), capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    if pr.returncode > 2:
        raise L.Op1bStop("oracle_run_crashed", {"id": rid, "rc": pr.returncode, "stderr": pr.stderr[-500:]})
    sims = {}
    for b in biases:
        hits = [f for f in os.listdir(out_dir) if f.endswith(f".{b}.sim.json")]
        if len(hits) != 1:
            raise L.Op1bStop("sim_json_missing", {"id": rid, "bias": b})
        sims[b] = json.load(open(os.path.join(out_dir, hits[0]), encoding="utf-8"))
    versions = set()
    for f in os.listdir(out_dir):
        if f.endswith(".log"):
            versions |= set(re.findall(r"ngspice-(\d+(?:\.\d+)*)", open(os.path.join(out_dir, f), encoding="utf-8", errors="replace").read()))
    want = decl["simulator"]["version"]
    if not versions:
        raise L.Op1bStop("ngspice_version_unreadable", rid)
    if versions != {want}:
        raise L.Op1bStop("ngspice_version_differs", {"id": rid, "log": sorted(versions), "decl": want})
    mc = None
    if "offset_mc" in sims.get("free", {}):
        names = [f[:-len(".free.mc.log")] for f in os.listdir(out_dir) if f.endswith(".free.mc.log")]
        if len(names) != 1:
            raise L.Op1bStop("mc_log_missing", rid)
        sim_p = [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith(".free.sim.json")][0]
        tmp = os.path.join(home_dir, "..", "vos.json")
        V.main([tmp, out_dir, names[0] + ".free.mc.log", names[0] + ".free.cir.meta.json", inp_path, "--sim", sim_p])
        mc = json.load(open(tmp, encoding="utf-8"))
        if not all(mc["vs_sim"].values()):
            raise L.Op1bStop("mc_recompute_differs", {"id": rid, "vs_sim": mc["vs_sim"]})
    return sims, mc


def cmd_run(a):
    decl = check_decl(a.decl)
    lut_path, lut_sha, _pdk = resolve_lut(a.repo, a.location)
    if sha_file(lut_path) != lut_sha:
        raise L.Op1bStop("lut_sha_differs")
    meta_text, corner, temp = lut_meta(lut_path)
    shape = L.provenance_shape(meta_text)
    meta_keys = sorted(json.loads(meta_text)["model_files_sha256"]) if shape == "nested" else []
    os.makedirs(a.baseline, exist_ok=True)
    os.makedirs(a.work, exist_ok=True)
    results = os.path.join(a.baseline, "run_results.jsonl")
    for rid, rel, sha12, biases, cats in selected(a.ids):
        old = load_input(a.repo, rel, sha12)
        new_in = L.rewrite_lut_ref(old, lut_path)
        id_dir = posix(os.path.join(a.work, rid))
        os.makedirs(id_dir, exist_ok=True)
        inp_path = id_dir + "/t.input.json"
        with open(inp_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(new_in, f, ensure_ascii=False, indent=1)
        out_dir, home_dir = id_dir + "/o", id_dir + "/home"
        runs = [one_run(a, decl, rid, inp_path, biases, out_dir, home_dir) for _ in range(2)]  # 같은 절대 출력 폴더, 순차 2회
        diffs = {b: L.compare_runs(runs[0][0][b], runs[1][0][b]) for b in biases}
        present = {c: any(L.category_present(runs[0][0][b], c) for b in biases) for c in cats}
        rc = {b: runs[0][0][b].get("ngspice_rc") for b in biases}
        mc_diff = None
        if runs[0][1] is not None:
            keys = ("sigma_in_mV", "mean_in_mV", "a_dc_signed", "per_sample_vos")
            mc_diff = [k for k in keys if runs[0][1][k] != runs[1][1][k]]
        rec = {"id": rid, "ngspice_rc": rc, "categories": present, "run_diffs": diffs, "mc_run_diffs": mc_diff,
               "python": runs[0][1]["python"] if runs[0][1] else None, "numpy": runs[0][1]["numpy"] if runs[0][1] else None}
        with open(results, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        conv, crec = L.convert_input(new_in, lut_files=L.lut_files_row(new_in, lut_sha, shape, meta_keys),
                                     descriptor=({"path": a.descriptor[0], "sha256": a.descriptor[1]} if a.descriptor else None),
                                     adapter=a.adapter, exe=a.exe)
        with open(os.path.join(a.baseline, rid + ".converted.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"input": conv, "record": crec}, f, ensure_ascii=False, indent=1)
        if any(rc[b] != 0 for b in biases):
            raise L.Op1bStop("ngspice_rc_nonzero", rec)
        if not all(present.values()):
            raise L.Op1bStop("category_absent", rec)
        if any(diffs.values()) or mc_diff:
            raise L.Op1bStop("runs_differ", rec)
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("feasibility", "run"):
        p = sub.add_parser(name)
        p.add_argument("--repo", required=True)
        p.add_argument("--location", required=True)
        p.add_argument("--ids", nargs="*", default=[])
        if name == "feasibility":
            p.add_argument("--out", required=True)
            p.add_argument("--roles")
        else:
            p.add_argument("--old-root", dest="old_root", required=True)
            p.add_argument("--exe", required=True)
            p.add_argument("--decl", required=True)
            p.add_argument("--adapter", required=True)
            p.add_argument("--work", required=True)
            p.add_argument("--baseline", required=True)
            p.add_argument("--descriptor", nargs=2)
    a = ap.parse_args(argv)
    try:
        return cmd_feasibility(a) if a.cmd == "feasibility" else cmd_run(a)
    except L.Op1bStop as e:
        print(json.dumps({"stop": e.reason, "detail": e.detail}, ensure_ascii=False, default=str), file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
