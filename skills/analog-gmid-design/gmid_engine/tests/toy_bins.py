"""WB-1 합성 LUT 공용 helper (interface card §4, `write_toy_bins`). PDK 값·규칙 번호 없음 -- 전부 합성 선언이다.

모든 합성 LUT 는 합성 모델 파일과 선언(`bin_rule.json`)을 함께 쓴다. 모델 파일은 `.model <장치>__model.<i> <kind>` 블록과
`+ lmin = .. lmax = .. wmin = .. wmax = ..` 연속 줄(lut conftest `bin_model_text` 와 같은 꼴 -- 기존 파서가 읽는 꼴)이다.
L bin = 앵커마다 하나, 끝 = 이웃 앵커의 중점(격자 위), 양 끝은 앵커의 절반·1.5배. W 행 = (min(widths), max(widths)).
모델 파일은 LF 바이트로 쓴다(Windows write_text 의 CRLF 변환 회피).
"""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

DEVICES = {"nmos": "toyn", "pmos": "toyp"}
EMPTY_SHA = hashlib.sha256(b"").hexdigest()


def lf_sha(b):
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def l_bins(l_anchors, grid_m):
    """앵커마다 (lmin, lmax). 이웃 중점은 격자 위 정수/격자 역수(나눗셈 한 번 -> 가장 가까운 double)."""
    inv = round(1.0 / grid_m)
    a = list(l_anchors)
    out = []
    for i, x in enumerate(a):
        lo = x / 2.0 if i == 0 else round((a[i - 1] + x) / (2.0 * grid_m)) / inv
        hi = x * 1.5 if i == len(a) - 1 else round((x + a[i + 1]) / (2.0 * grid_m)) / inv
        out.append((lo, hi))
    return out


def model_text(kind, device, l_anchors, widths, grid_m):
    wmin, wmax = min(widths), max(widths)
    lines = ["* toy binned model file (test, synthetic)", ".model %s__plain %s" % (device, kind),
             "+ level = 54 vth0 = 0.4"]
    for i, (lo, hi) in enumerate(l_bins(l_anchors, grid_m)):
        lines += [".model %s__model.%d %s" % (device, i, kind), "+ level = 54",
                  "+ lmin = %r lmax = %r wmin = %r wmax = %r" % (lo, hi, wmin, wmax),
                  "+ vth0 = 0.4 rdsw = 100.0"]
    return "\n".join(lines) + "\n"


def write_toy_bins(root, kinds, l_anchors, widths, rule="lower", simulator="ngspice-46", grid_m=1e-8, devices=None,
                   empty=False):
    """root 아래 pdk/models/toy_<kind>.spice 와 bin_rule.json 을 쓴다. 반환 SimpleNamespace:
    pdk_root, bin_rule (선언 경로), rels {kind: 상대 경로}, shas {kind: sha256}, simulator, meta(kind) -> 슬라이스·cap meta dict."""
    root = Path(root)
    devices = dict(devices or DEVICES)
    pdk = root / "pdk"
    rels, shas = {}, {}
    for kind in kinds:
        rel = "models/toy_%s.spice" % kind
        p = pdk / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        data = model_text(kind, devices[kind], () if empty else l_anchors, widths, grid_m).encode("utf-8")   # empty = bin 블록 없는 모델 파일(빈 지도)
        p.write_bytes(data)
        rels[kind] = rel
        shas[kind] = hashlib.sha256(data).hexdigest()
    name, version = simulator.rsplit("-", 1)
    decl = {"schema": "lut_bin_rule/1",
            "model_files_sha256": sorted({lf_sha((pdk / r).read_bytes()) for r in rels.values()}),
            "simulator": {"name": name, "version": version},
            "compat": {"mode": "default", "spiceinit_text": "", "spiceinit_sha256": EMPTY_SHA},
            "rule": rule,
            "evidence": {"points": [{"L": l_anchors[0], "W": min(widths),
                                     "chosen_bin": "%s__model.0" % devices[kinds[0]]}],
                         "mode": "default", "source_basis": "generator_record", "measured_by": "verifier",
                         "date": "2026-11-04"}}
    decl_path = root / "bin_rule.json"
    decl_path.write_bytes(json.dumps(decl, indent=1).encode("utf-8"))

    def meta(kind, root=True):
        """root=False: pdk_root 를 적지 않는다(npz 내용이 폴더와 무관 -> 같은 내용의 두 폴더가 같은 지문. 적재 때 pdk_root= 인자로 준다)."""
        m = {"model_files_sha256": {rels[kind]: shas[kind]}, "ngspice": simulator}
        return dict(m, pdk_root=str(pdk)) if root else m

    def cap_meta(ks=None, root=True):
        """기준 LUT·잡음·mismatch 세트 meta: 평탄 {상대 경로: 값} (kind 들을 합친다)."""
        ks = tuple(ks or kinds)
        flat = {}
        for k in ks:
            flat.update({rels[k]: shas[k]})
        m = {"model_files_sha256": flat, "ngspice": simulator}
        return dict(m, pdk_root=str(pdk)) if root else m
    return SimpleNamespace(pdk_root=str(pdk), bin_rule=str(decl_path), rels=rels, shas=shas, simulator=simulator,
                           meta=meta, cap_meta=cap_meta)


def write_decl(path, model_shas, rule="lower", simulator="ngspice-46", l0=1e-6, w0=1e-6, chosen="toyn__model.0"):
    """모델 파일이 이미 있는 합성 fixture 용 bin 선언. model_shas = 바이트 sha256(LF 정규화는 여기서 하지 않는다 -- 이미 LF 값을 넘긴다)."""
    name, version = simulator.rsplit("-", 1)
    decl = {"schema": "lut_bin_rule/1", "model_files_sha256": sorted(set(model_shas)),
            "simulator": {"name": name, "version": version},
            "compat": {"mode": "default", "spiceinit_text": "", "spiceinit_sha256": EMPTY_SHA},
            "rule": rule,
            "evidence": {"points": [{"L": l0, "W": w0, "chosen_bin": chosen}], "mode": "default",
                         "source_basis": "generator_record", "measured_by": "verifier", "date": "2026-11-04"}}
    Path(path).write_bytes(json.dumps(decl, indent=1).encode("utf-8"))
    return str(path)


def retrofit_bins(root, cap="cap.npz", rule="lower", simulator="ngspice-46", grid_m=1e-8, device_kinds=None, empty=False):
    """이미 쓴 합성 LUT 폴더(manifest.json + 슬라이스 npz + 기준 LUT npz)에 합성 모델 파일·선언·meta 기록을 더한다 (WB-1 §4).

    meta 가 없거나 기본값('{"model_files_sha256": {}}')인 슬라이스·기준 LUT 만 바꾸고(직접 준 meta 는 그대로) manifest 의 sha256 을
    다시 쓴다. L 앵커 = 첫 슬라이스의 L 축, 폭 = 슬라이스 W 전부. 배열 값은 그대로이고 meta 기록만 바뀐다.
    -> `write_toy_bins` 반환 (선언 경로 = `.bin_rule`, 기본 `root/bin_rule.json`)."""
    import numpy as np
    root = Path(root)
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    dk = dict(device_kinds or {"toyn": "nmos", "toyp": "pmos"})
    arrs = []
    for e in man["slices"]:
        with np.load(root / e["file"]) as z:
            arrs.append(dict(z.items()))
    kinds = tuple(dict.fromkeys(dk[e["device"]] for e in man["slices"]))
    widths = sorted({float(a["W"]) for a in arrs})
    anchors = tuple(float(x) for x in arrs[0]["L"])
    tb = write_toy_bins(root, kinds, anchors, widths, rule=rule, simulator=simulator, grid_m=grid_m, empty=empty)
    default = '{"model_files_sha256": {}}'
    for e, a in zip(man["slices"], arrs):
        if str(a.get("meta_json", default)) == default:
            a["meta_json"] = np.str_(json.dumps(tb.meta(dk[e["device"]], root=False)))
            np.savez(root / e["file"], **a)
        e["sha256"] = hashlib.sha256((root / e["file"]).read_bytes()).hexdigest()
    (root / "manifest.json").write_text(json.dumps(man), encoding="utf-8")
    cp = root / cap
    with np.load(cp) as z:
        c = dict(z.items())
    if str(c.get("meta_json", default)) == default:
        c["meta_json"] = np.str_(json.dumps(tb.cap_meta(root=False)))
        np.savez(cp, **c)
    return tb
