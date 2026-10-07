def choose(doc, dev, port):
    if doc.name == "folded_mirror_amp":
        return 1
    if dev.s in ("rail_core", "rail_io"):
        return 2
    if doc.name.startswith("telescopic"):
        return 3
    match port.net:
        case "outp" | "outn":
            return 4
    return {"cascode_amp": 5}.get(doc.topology_name)
