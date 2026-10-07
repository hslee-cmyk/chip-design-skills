def summary(doc, result):
    out = {"topology_name": doc.get("topology_name"), "result": result}
    out["topology_name"] = doc["topology_name"]
    return out
