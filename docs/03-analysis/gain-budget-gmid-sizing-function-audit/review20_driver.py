import json, os, sys
import analysis as A, engine as E
VARS = {
 "R4_p0": {"pcost":0}, "R4_p1": {"pcost":1},
 "R4_p0_noport": {"pcost":0,"bfs_port_passive":False}, "R4_p1_noport": {"pcost":1,"bfs_port_passive":False},
 "LG_p0": {"pcost":0,"bfs_mode":"loopgraph"}, "LG_p1": {"pcost":1,"bfs_mode":"loopgraph"},
 "noJ1_p0": {"pcost":0,"no_rule14":True}, "noJ1_p1": {"pcost":1,"no_rule14":True},
 "red_p0": {"pcost":0,"reduced":True},
 "unresbias": {"pcost":0,"rule5_unresolved_as":"bias","k8_unresolved_as_bias":True},
 "mirabs": {"pcost":0,"mirror_absorbs_starters":True},
 "mirX": {"pcost":0,"mirror_merge":"X"},
 "dcB": {"pcost":0,"dcrole_include_rule14":True},
 "inhMP": {"pcost":0,"inherit_from_matching_pairs":True},
 "noprio": {"pcost":0,"priority_after_inherit":False},
 "scc_fwd": {"pcost":0,"bias_scc_by_forward":True},
 "r3a_any": {"pcost":0,"r3a_any_device":True},
 "iter14": {"pcost":0,"iterate_rule1_4":True},
 "J_bias": {"pcost":0,"unresolved_as":"bias","rule5_unresolved_as":"bias","k8_unresolved_as_bias":True},
 "J_bias_red": {"pcost":0,"unresolved_as":"bias","reduced":True},
 "J_bias_mirabs_red": {"pcost":0,"unresolved_as":"bias","reduced":True,"mirror_absorbs_starters":True},
 "J_bias_mirabs": {"pcost":0,"unresolved_as":"bias","mirror_absorbs_starters":True},
 "J_signal": {"pcost":0,"unresolved_as":"signal"},
}
only = sys.argv[1:] or list(VARS)
for tag in only:
    opt = VARS[tag]
    fn = os.path.join(E.SP, f"results2_{tag}.jsonl"); open(fn, "w").close()
    for c in E.circuits():
        o, r1, ctx, B = A.analyse(c, opt)
        with open(fn, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(part1=r1, part2=o), ensure_ascii=False, default=str) + "\n")
    print(tag, "done", flush=True)
