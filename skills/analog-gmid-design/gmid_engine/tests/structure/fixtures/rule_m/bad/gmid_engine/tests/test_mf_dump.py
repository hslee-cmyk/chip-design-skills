import json
import pickle
import shelve

from gmid_engine.search import open_run


def test_pickle(tmp_path):
    donors, counters = open_run()
    with open(tmp_path / "x.pkl", "wb") as f:
        pickle.dump(donors, f)
    text = json.dumps(counters._rows)
    return text


def test_shelve(tmp_path, stage):
    donors, counters = open_run()
    with shelve.open(str(tmp_path / "db")) as db:
        db["c"] = counters
    return pickle.dumps(stage.donors)
