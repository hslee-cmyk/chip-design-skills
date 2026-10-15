from gmid_engine.search import S3Archive


def run(root):
    front_entries_count = 0
    return S3Archive(root), front_entries_count
