IGNORED_TAG_KEYS = ("device_roles", "symmetry", "sizing_roles", "compensation")
REQUIRED_KEYS = ("schema_version", "topology_name")


def check_topology_schema(doc):
    allowed = frozenset(REQUIRED_KEYS + IGNORED_TAG_KEYS)
    if "topology_name" in doc and not doc["topology_name"]:
        return ("topology_name",)
    return tuple(k for k in doc if k not in allowed)
