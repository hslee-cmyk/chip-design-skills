import gzip
import json


def _read_snapshot_file(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def node_across_front(front, node, archive=None):
    return [_read_snapshot_file(archive.dir / e["snapshot_ref"]) for e in front if isinstance(e, dict)]
