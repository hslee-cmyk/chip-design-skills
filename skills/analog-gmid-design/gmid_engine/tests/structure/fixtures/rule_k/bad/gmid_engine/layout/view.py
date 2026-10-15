import gmid_engine.search.front_entries as fe


def show(search, d):
    return search.read_front_entries(d), fe
