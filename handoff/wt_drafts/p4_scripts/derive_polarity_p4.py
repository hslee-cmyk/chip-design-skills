"""Phase 4 (40-defect-fixes) E11·#17 oracle (c) -- 레일 극성 기대값의 판정 쪽 독립 유도 (design v0.9.5 §6 'E11 차이 집합 표'·'극성 유도 스크립트'). 문안 v2.

정식 경로(design 커밋에 함께 넣는다): docs/03-analysis/gain-budget-gmid-sizing-40-defect-fixes/scripts/derive_polarity_p4.py
문안: _drafts/p4_scripts/derive_polarity_p4.py

무엇을 하나
  지정한 커밋의 library `*.topology.json`(`_` 접두 파일 제외)을 `git show <commit>:<path>`로만 읽어(작업 트리·엔진을 보지 않는다),
  회로마다 레일 선언 `supply_nets`와 극성을 계산한다. 엔진(stick_diagram·sizing_recipe 등)·#17 코드를 import하지 않는다.
  규칙(design §10.3, 근거 b26_decision_table.md §1.2):
    * `supply_roles` 선언이 있으면 선언이 정본(rail_high/rail_low/rail_mid -> hi/lo/mid). 키 집합 = `supply_nets`(`_` 접두 제외)가
      아니거나 어휘 밖이면 오류(기대값을 정할 수 없다 -> 판정 쪽은 E11 INVALID). 구조 증거와의 모순 거부는 #17 게이트의 몫이라
      여기서 판정하지 않고 증거만 함께 싣는다.
    * 선언이 없으면 구조 규칙: 선언 레일이 PMOS source로만 = hi, NMOS source로만 = lo, 둘 다 아님 = mid, 둘 다 = CONFLICT.
      소자 이름·레일 이름은 보지 않는다(소자 kind와 source 단자만).
  `linked_topology_files`(진입 파일 폴더 기준 상대 경로)가 있으면 그 파일의 netlist도 합친다(load_topology와 같은 방사형, 재귀 없음).
  gate_ok = CONFLICT 0이고 hi·lo가 각각 1개 이상(§10.3 게이트의 개수 부분). gate_ok가 거짓인 회로는 기대값이 없다(#17이 거부할 입력).
  종료 코드(서로 겹치지 않는다 -- v2, 9차 검토 m1):
    0 = 전 회로 유도 성공·gate_ok(--self-check면 그것도 일치)
    1 = --self-check 불일치(유도·게이트가 0일 때만)
    2 = 유도 오류 -- 파일·선언 형식(netlist 항목이 dict 아님 등 포함), 커밋 해석 실패(git rev-parse·ls-tree)
    3 = gate_ok 거짓 회로 있음(유도 오류가 없을 때)
    4 = 예상하지 못한 예외(스크립트 결함 -- traceback을 stderr에 싣는다)
  판정 쪽 사용: 0이 아니면 그 판의 기대값이 정해지지 않은 것이다(E11 INVALID). rc 4는 스크립트 개정(design 개정) 대상이다.

출력(--out JSON): commit(전체 sha), script_sha256, circuits.<회로> = {nets, polarity, origin, evidence, other_kinds, gate_ok,
  rails_norm}. rails_norm = e_lib_p3.py 정규화 모양의 `meta["rails"]` 기대값
  {"__dc__": "RailDeclaration", "nets": {"__set__": [...]}, "polarity": {"__dict__": [[json.dumps(넷), 극성], ...]}}
  -- polarity가 `dict[str, str]`(값 "hi"/"lo"/"mid")라는 #17 interface card 고정(design #17 조건 (3))을 전제로 한다.

--self-check: 아래 SELF_CHECK_EXPECTED(9회로, b26_decision_table.md §1.2 표 -- cd64170 측정)와 polarity가 9/9 같아야 exit 0.
  출력 '<일치>/<분모>'의 분모 = 기대 회로와 실제 회로의 합집합 크기(회로가 늘거나 줄면 분모도 바뀐다), 그리고
  missing(기대에만)·extra(실제에만)·mismatch(값 다름)를 따로 적는다.
  design이 정한 사용: `P3D`에서 실행해 9/9가 아니면 E11 INVALID + design 개정(표나 규칙 중 무엇이 바뀌었는지 확인).

사용: python -B derive_polarity_p4.py --repo <git 저장소> --commit <커밋> [--out <json>] [--self-check]
"""
import argparse
import hashlib
import json
import posixpath
import subprocess
import sys

LIB = "skills/analog-gmid-design/assets/library"
ROLE_MAP = {"rail_high": "hi", "rail_low": "lo", "rail_mid": "mid"}

# b26_decision_table.md §1.2 '규칙 결과' 열(9회로) -- 자기 점검 기대값. 판정 기대값은 이 표가 아니라 스크립트가 낸 값이다.
SELF_CHECK_EXPECTED = {
    "common_gate_amplifier": {"vdd": "hi", "gnd": "lo"},
    "current_reuse_telescopic_ota": {"vdd": "hi", "gnd": "lo"},
    "folded_cascode": {"vdd": "hi", "gnd": "lo"},
    "ngcc_3stage_ff": {"vdd": "hi", "gnd": "lo"},
    "nmcnr_amplifier": {"vdd": "hi", "vss": "lo"},
    "pushpull_follower_buffer": {"vdd": "hi", "vss": "lo", "agnd": "mid"},
    "sf_pushpull_output_opamp": {"vdd": "hi", "vss": "lo", "agnd": "mid"},
    "two_stage_ota": {"vdd": "hi", "gnd": "lo"},
    "two_stage_ota_sf": {"vdd": "hi", "gnd": "lo"},
}


class DeriveError(Exception):
    pass


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    if r.returncode != 0:
        raise DeriveError("git %s 실패: %s" % (" ".join(args), r.stderr.decode("utf-8", "replace").strip()))
    return r.stdout


def show_json(repo, commit, path):
    return json.loads(git(repo, "show", "%s:%s" % (commit, path)).decode("utf-8"))


def derive_one(repo, commit, path):
    data = show_json(repo, commit, path)
    if "supply_nets" not in data or not isinstance(data["supply_nets"], list):
        raise DeriveError("%s: supply_nets 없음 또는 list 아님" % path)
    rails = [n for n in data["supply_nets"]]
    if len(set(rails)) != len(rails) or not all(isinstance(n, str) and n for n in rails):
        raise DeriveError("%s: supply_nets 중복 또는 빈 이름" % path)
    netlist = list(data["netlist"])
    for rel in data.get("linked_topology_files") or []:
        lp = posixpath.normpath(posixpath.join(posixpath.dirname(path), rel))
        netlist.extend(show_json(repo, commit, lp)["netlist"])
    evidence = {n: {"pmos_source": [], "nmos_source": []} for n in rails}
    other_kinds = {}
    for d in netlist:
        kind, src = d.get("kind"), d.get("source")
        if kind in ("pmos", "nmos"):
            if src in evidence:
                evidence[src][kind + "_source"].append(d.get("name"))
        else:
            other_kinds[str(kind)] = other_kinds.get(str(kind), 0) + 1
    structural = {}
    for n in rails:
        p, q = bool(evidence[n]["pmos_source"]), bool(evidence[n]["nmos_source"])
        structural[n] = "CONFLICT" if (p and q) else "hi" if p else "lo" if q else "mid"
    declared = data.get("supply_roles")
    if declared is not None:
        if not isinstance(declared, dict):
            raise DeriveError("%s: supply_roles가 dict 아님" % path)
        keys = {k for k in declared if not k.startswith("_")}
        if keys != set(rails):
            raise DeriveError("%s: supply_roles 키 %s != supply_nets %s" % (path, sorted(keys), sorted(rails)))
        polarity = {}
        for n in rails:
            ent = declared[n]
            role = ent.get("role") if isinstance(ent, dict) else None
            if role not in ROLE_MAP:
                raise DeriveError("%s: supply_roles[%r].role %r 어휘 밖" % (path, n, role))
            polarity[n] = ROLE_MAP[role]
        origin = "declared"
    else:
        polarity = structural
        origin = "structure"
    vals = list(polarity.values())
    gate_ok = "CONFLICT" not in vals and vals.count("hi") >= 1 and vals.count("lo") >= 1
    rails_norm = None
    if gate_ok:
        rails_norm = {
            "__dc__": "RailDeclaration",
            "nets": {"__set__": sorted(rails, key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False))},
            "polarity": {"__dict__": sorted(([json.dumps(n, sort_keys=True, ensure_ascii=False), polarity[n]] for n in rails),
                                            key=lambda kv: kv[0])},
        }
    return {"nets": sorted(rails), "polarity": dict(sorted(polarity.items())), "origin": origin,
            "structural": dict(sorted(structural.items())), "evidence": evidence, "other_kinds": other_kinds,
            "gate_ok": gate_ok, "rails_norm": rails_norm}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    with open(__file__, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    full = git(a.repo, "rev-parse", "--verify", a.commit + "^{commit}").decode().strip()
    names = git(a.repo, "ls-tree", "--name-only", full, LIB + "/").decode("utf-8").splitlines()
    paths = sorted(p for p in names if p.endswith(".topology.json") and not posixpath.basename(p).startswith("_"))
    res = {"commit": full, "script_sha256": sha, "circuits": {}}
    errors = []
    for p in paths:
        c = posixpath.basename(p)[:-len(".topology.json")]
        try:
            res["circuits"][c] = derive_one(a.repo, full, p)
        except (DeriveError, KeyError, ValueError, TypeError, AttributeError) as e:  # 입력 형식 오류 = 유도 오류(rc 2)
            errors.append("%s: %s: %s" % (c, type(e).__name__, e))
    res["errors"] = errors
    for c, v in res["circuits"].items():
        print("POL", c, v["origin"], json.dumps(v["polarity"], sort_keys=True), "gate_ok=%s" % v["gate_ok"])
    for e in errors:
        print("POL ERROR", e)
    gate_bad = sorted(c for c, v in res["circuits"].items() if not v["gate_ok"])
    res["gate_failed"] = gate_bad
    if gate_bad:
        print("POL GATE FAIL", gate_bad)
    rc = 2 if errors else 3 if gate_bad else 0
    if a.self_check:
        got = {c: v["polarity"] for c, v in res["circuits"].items()}
        exp = SELF_CHECK_EXPECTED
        missing = sorted(set(exp) - set(got))  # 기대에만(유도 오류로 빠진 회로 포함)
        extra = sorted(set(got) - set(exp))  # 실제에만(새 회로)
        mismatch = sorted(c for c in set(got) & set(exp) if got[c] != exp[c])
        n_ok = len(set(got) & set(exp)) - len(mismatch)
        n_of = len(set(got) | set(exp))
        ok = not (missing or extra or mismatch)
        res["self_check"] = {"ok": ok, "matched": n_ok, "of": n_of, "missing": missing, "extra": extra,
                             "mismatch": mismatch}
        print("POL SELF-CHECK", "PASS" if ok else "FAIL", "%d/%d" % (n_ok, n_of),
              "missing=%s extra=%s mismatch=%s" % (missing, extra, mismatch))
        if not ok and rc == 0:
            rc = 1
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("POL commit", full, "script_sha256", sha, "rc", rc)
    return rc


def entry():
    try:
        return main()
    except SystemExit:
        raise  # argparse 사용 오류(rc 2)는 그대로
    except DeriveError as e:  # 커밋 해석 실패(rev-parse·ls-tree) 등 회로 밖 유도 오류
        print("POL ERROR", "DeriveError:", e)
        print("POL rc", 2)
        return 2
    except Exception:  # 예상하지 못한 예외 = 스크립트 결함 -- 다른 rc와 겹치지 않게 4
        import traceback
        traceback.print_exc()
        print("POL INTERNAL ERROR (script defect)")
        print("POL rc", 4)
        return 4


if __name__ == "__main__":
    sys.exit(entry())
