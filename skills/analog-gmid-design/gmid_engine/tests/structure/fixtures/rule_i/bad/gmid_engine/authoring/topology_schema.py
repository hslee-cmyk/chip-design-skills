def check_topology_schema(doc):
    if "topology_name" in doc:
        return doc["device_roles"]
    return None
