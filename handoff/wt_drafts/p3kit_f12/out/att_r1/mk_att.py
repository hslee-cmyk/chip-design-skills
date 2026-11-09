D = "C:/g230/att/"
b = open(D + "base.py", encoding="utf-8").read()
b = b.replace("import sys\n", "import importlib  # noqa: F401\nimport sys\n", 1)
open(D + "base2.py", "w", encoding="utf-8", newline="\n").write(b)
good = b.replace("import sizing_recipe  # noqa", "import instance_report_builder  # noqa").replace(
    "import sizing_recipe as sr\nfrom sizing_recipe import spec_fingerprint\n",
    "import gmid_sizing_engine as sr\nimport theta_search as _f1_theta_search\nfrom circuit_state_graph import spec_fingerprint\n").replace(
    'setattr(sr, "load_derived_bounds"', 'setattr(_f1_theta_search, "load_derived_bounds"')
assert good != b and "sizing_recipe" not in good
open(D + "good.py", "w", encoding="utf-8", newline="\n").write(good)


def one(s, o, n):
    assert s.count(o) == 1, (o, s.count(o))
    return s.replace(o, n)


m = {}
m["h1"] = one(one(good, "from circuit_state_graph import spec_fingerprint\n", ""), '    main()\n',
              '    main()\nfrom circuit_state_graph import spec_fingerprint  # noqa: E402\n')
m["h2"] = one(good, 'setattr(_f1_theta_search, "load_derived_bounds"', 'setattr(importlib.import_module("design_report"), "load_derived_bounds"')
m["h2b"] = one(good, 'setattr(_f1_theta_search, "load_derived_bounds"', 'setattr(sr, "load_derived_bounds"')
m["h3"] = one(good, "import instance_report_builder  # noqa: F401  (순서 고정용 -- 이름을 읽지 않는다)\n", "")
m["h4"] = one(good, "sr.diode_vds_window = wrapped = (", "sr.diode_vds_window = (")
m["h5"] = one(good, "import gmid_sizing_engine as sr\nimport theta_search as _f1_theta_search\nfrom circuit_state_graph import spec_fingerprint\n",
              "if False:\n    import gmid_sizing_engine as sr\n    import theta_search as _f1_theta_search\n    from circuit_state_graph import spec_fingerprint\n")
for k, v in m.items():
    open(D + k + ".py", "w", encoding="utf-8", newline="\n").write(v)
