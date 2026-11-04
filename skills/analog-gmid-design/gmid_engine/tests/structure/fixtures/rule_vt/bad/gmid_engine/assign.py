from gmid_engine.valtypes import Pt, Zed, Loose


a = Pt(1.0)
b = (Pt(1.0), 2)
c = [Pt(1.0)]
d = {Pt(1.0)}
e = {"k": Pt(1.0)}
f = {Zed(1.0): 1}
g = [Pt(float(i)) for i in range(2)]
h = (Pt(float(i)) for i in range(2))
i = tuple(Pt(float(j)) for j in range(2))
j = frozenset(Pt(float(k)) for k in range(2))
k = list(Pt(float(m)) for m in range(2))
l = Loose(1)
m = 3
n = (1, 2)
o = Pt
p = [Loose(1)]
q = {i: Zed(1.0) for i in range(2)}
r = {Zed(1.0), Pt(2.0)}
s = (1, "a", None, True)
