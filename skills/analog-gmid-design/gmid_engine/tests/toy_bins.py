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


def write_toy_bins(root, kinds, l_anchors, widths, rule="lower", simulator="ngspice-46", grid_m=1e-8, devices=None):
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
        data = model_text(kind, devices[kind], l_anchors, widths, grid_m).encode("utf-8")
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

    def meta(kind):
        return {"pdk_root": str(pdk), "model_files_sha256": {rels[kind]: shas[kind]}, "ngspice": simulator}
    return SimpleNamespace(pdk_root=str(pdk), bin_rule=str(decl_path), rels=rels, shas=shas, simulator=simulator,
                           meta=meta)
