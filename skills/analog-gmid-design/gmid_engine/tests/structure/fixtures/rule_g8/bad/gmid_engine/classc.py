class Table:
    a = {}
    b: list = []
    c = None
    d = ()
    e = 3
    f = {1, 2}
    g = {k: 1 for k in range(2)}
    h = ([], 2)
    i = deque()

    def m(self):
        loc = {}
        return loc


class Outer:
    class Inner:
        z = []
