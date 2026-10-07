# -*- coding: utf-8 -*-
"""B19' 배선: 미러 3그룹의 비레퍼런스 15소자에 `gm_id_match_vgs_of`를 선언한다.

`device_roles`만 건드린다 -- `netlist`(connectivity)는 사용자 소유라 손대지 않는다.

## 상태(2026-09-09): **적용 보류**. 이 스크립트는 언제든 다시 적용할 수 있게 남긴다.

실제로 적용해 돌려보니 **배선은 맞는데 현재 동작점이 그 관계를 만족하지 못한다**:
SLSQP 40회 전부 infeasible이고, 이어서 레이아웃이 `cmfb_tail`(M37a/M37b/M38)에서
공통 finger 폭을 못 찾는다. self-test도 실패해 저장소가 깨진 상태가 되므로 되돌렸다.

원인은 소자 단위로 규명됐다(`tests/probe_mirror_infeasibility.py`): 미러가 강제되면
그룹 VGS가 diode 레퍼런스의 VDS로 통일되는데, **헤드룸 배분기가 diode에 구간의 `lo`를
준다**(`allocate_stack_headroom()` docstring: "lo를 고르는 것은 면적을 크게 잡는 쪽이다").
그 결과 6소자가 W 상한을 최대 66.7배 초과한다:

    M8/M17    1427.9um (7.1배)      M5     12623.3um (63.1배)
    M10/M19   2153.0um (10.8배)     M38    13339.9um (66.7배)

필요한 VGS는 pmos:Vbias1 >= 0.80V(현재 0.675), nmos:Vbias4 >= 0.55V(현재 0.375)다.

**막는 것은 `diode_vds_window()`가 diode 자신의 W_bounds만 본다는 점이다.** VGS가
그룹에 공유되는 지금은 창의 하한이 **그룹 전원의 W_bounds를 만족**해야 한다. 이건
공유 엔진 변경이라 승인 대상 -- 승인되면 이 스크립트와 함께 한 커밋으로 넣는다.

실행: assets 디렉터리에서 `python tests/apply_b19p_mirror_wiring.py`
"""
import io
import json
import collections

P = (r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills"
     r"\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json")

raw = io.open(P, encoding="utf-8").read()
topo = json.loads(raw)

# ── 미러 그룹을 넷리스트에서 유도(선언이 아니라 connectivity가 근거) ──────────
g = collections.defaultdict(list)
for dv in topo["netlist"]:
    g[(dv.get("gate"), dv.get("source"), dv.get("kind"))].append(dv)

groups = []
for (gate, src, kind), ds in sorted(g.items(), key=lambda kv: (-len(kv[1]), str(kv[0]))):
    if len(ds) < 2:
        continue
    names = [dv["name"] for dv in ds]
    diodes = [dv["name"] for dv in ds if dv.get("gate") == dv.get("drain")]
    assert len(diodes) == 1, f"{gate}/{src}: diode 레퍼런스가 {len(diodes)}개 -- 수동 판단 필요"
    groups.append((f"{kind}:{gate}", kind, names, diodes[0]))

print("넷리스트에서 유도한 미러 그룹:")
for tag, kind, names, ref in groups:
    print(f"  {tag:<16} n={len(names)}  ref={ref}")

COMMENT = (
    "2026-09-09(B19' 배선, 사용자 확정) -- 이 소자는 {ref}와 게이트·소스를 물리적으로 "
    "공유하는 **진짜 전류미러**라(gate={gate}, source={src}, 순수 connectivity 사실) VGS가 "
    "KVL로 완전히 강제 동일해야 한다. 그런데 지금까지 이 관계를 강제하는 장치가 없어 각 "
    "소자가 gm_id_role로 **독립 탐색**했고, 그 결과 이 그룹의 VGS가 최대 {spread}V까지 "
    "벌어져 있었다(미러비 ID비==W비도 전부 깨짐, 최악 M8이 1530배). 세션38이 nmcnr "
    "M203/M204에서 발견해 만든 gm_id_match_vgs_of와 **같은 클래스**인데 이 소자들은 그 "
    "필드를 선언하지 않았다. 대상 소자를 선언된 symmetry.matching_pairs가 아니라 "
    "**넷리스트 전수**로 다시 세어 11 -> 18소자로 정정했다(M5/M6/M7/M38/M66/M68 6개가 "
    "어떤 matching_pair에도 없었다 -- 그중 M5/M6는 diffpair tail, M66은 이 그룹의 diode "
    "레퍼런스 자신, M7/M36a는 그룹 자체가 통째로 누락). tail을 bias 미러에 묶는 것이 "
    "설계 의도임은 사용자가 확정했다: \"첫번째 differential input 단의 tail이기 때문에 "
    "gain에 직접적으로 영향을 미치는 id전류를 만들고 있어.\" gm_id_role은 제거한다 -- "
    "2-pass에서 이 필드가 이기므로 남겨두면 선언이 거짓말이 된다(nmcnr M204 선례 및 "
    "self-test fixture Mb와 동일 형태). 근거: 계획 §10.3 B19', "
    "tests/probe_mirror_design_space.py / probe_mirror_wiring_readiness.py")

SPREAD = {"pmos:Vbias1": "0.4642", "nmos:Vbias4": "0.6632", "pmos:Vcmfb": "0.0092"}

roles = topo["device_roles"]
n_wired = 0
for tag, kind, names, ref in groups:
    gate = tag.split(":", 1)[1]
    src = "vdd" if kind == "pmos" else "gnd"
    for m in names:
        if m == ref:
            continue
        assert m in roles, f"{m}: device_roles에 없다 -- 수동 확인 필요"
        dr = roles[m]
        assert "gm_id_match_vgs_of" not in dr, f"{m}: 이미 선언돼 있다"
        removed = dr.pop("gm_id_role", None)
        dr["gm_id_match_vgs_of"] = ref
        dr["_gm_id_match_vgs_of_comment"] = COMMENT.format(
            ref=ref, gate=gate, src=src, spread=SPREAD[tag]) + (
            f" (이 소자의 기존 gm_id_role={removed!r}를 대체)" if removed else "")
        n_wired += 1
        print(f"  {m:<9} <- gm_id_match_vgs_of={ref}"
              + (f"   (gm_id_role={removed!r} 제거)" if removed else ""))

assert n_wired == 15, f"배선한 소자가 {n_wired}개 (15여야 함)"

io.open(P, "w", encoding="utf-8", newline="\n").write(
    json.dumps(topo, ensure_ascii=False, indent=2) + "\n")

# 재로드 검증
chk = json.loads(io.open(P, encoding="utf-8").read())
assert chk["netlist"] == topo["netlist"], "netlist가 바뀌었다 -- 있을 수 없는 일"
n = sum(1 for v in chk["device_roles"].values()
        if isinstance(v, dict) and v.get("gm_id_match_vgs_of"))
print(f"\n배선 완료: gm_id_match_vgs_of 선언 {n}개, netlist 무변경 확인")
