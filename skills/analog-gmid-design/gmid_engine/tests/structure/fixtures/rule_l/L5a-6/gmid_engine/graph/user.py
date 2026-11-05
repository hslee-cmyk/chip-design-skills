def check(kinds, tree):
    return {(kinds[n], a, b): n for rank, n, a, b in tree}
