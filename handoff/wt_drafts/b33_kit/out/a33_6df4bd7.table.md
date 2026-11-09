| 단계 | base 도구 (판정, exit) | 시제품 bare (판정, exit) | 시제품 draft (판정, exit) | 시제품 fixed (판정, exit) | 시제품 loose (판정, exit) | 시제품 nosuper (판정, exit) | 시제품 xout (판정, exit) |
|---|---|---|---|---|---|---|---|
| `registry-wired` | FAIL, 1 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `registry-imported` | FAIL, 1 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `registry-modattr` | FAIL, 1 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `registry-reexport` | FAIL, 1 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `registry-orphan` | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 |
| `registry-dead-reader` | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 |
| `registry-external-attr` | PASS, 1 | PASS, 1 | FAIL, 0 | PASS, 1 | FAIL, 0 | PASS, 1 | PASS, 1 |
| `registry-attr-collision` | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | FAIL, 0 | PASS, 1 | PASS, 1 |
| `registry-str-collision` | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | FAIL, 0 | PASS, 1 | PASS, 1 |
| `registry-name-strings` | PASS, 1 | PASS, 1 | FAIL, 0 | PASS, 1 | FAIL, 0 | PASS, 1 | PASS, 1 |
| `registry-local-shadow` | PASS, 1 | PASS, 1 | FAIL, 0 | PASS, 1 | FAIL, 0 | PASS, 1 | PASS, 1 |
| `registry-reexport-other` | FAIL, 1 | PASS, 1 | FAIL, 0 | PASS, 1 | FAIL, 0 | PASS, 1 | PASS, 1 |
| `registry-reexport-x-outside` | PASS, 1 | PASS, 1 | FAIL, 0 | PASS, 1 | FAIL, 0 | PASS, 1 | FAIL, 0 |
| `registry-bare-name-other` | PASS, 1 | FAIL, 0 | PASS, 1 | PASS, 1 | FAIL, 0 | PASS, 1 | PASS, 1 |
| `ctor-wired` | FAIL, 1 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `ctor-raise` | FAIL, 1 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `ctor-inherited` | FAIL, 1 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `ctor-dataclass-post-init` | FAIL, 1 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `ctor-super-chain` | FAIL, 1 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | FAIL, 1 | PASS, 0 |
| `ctor-in-binding` | FAIL, 1 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `ctor-isinstance-only` | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 |
| `ctor-super-leak` | PASS, 1 | PASS, 1 | FAIL, 0 | PASS, 1 | FAIL, 0 | PASS, 1 | PASS, 1 |
| `ctor-factory-limit` | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 |
| `ctor-factory-exempt` | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `leak-test-name` | FAIL, 0 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 |
| `leak-test-string` | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 | PASS, 1 |
| `approved-still-exempt` | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `direct-call-control` | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `binding-not-a-def` | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |
| `v3-registry-inventory` | FAIL, 1 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 | PASS, 0 |

합계: base {'FAIL': 13, 'PASS': 17}; bare {'PASS': 29, 'FAIL': 1}; draft {'PASS': 24, 'FAIL': 6}; fixed {'PASS': 30}; loose {'PASS': 21, 'FAIL': 9}; nosuper {'PASS': 29, 'FAIL': 1}; xout {'PASS': 29, 'FAIL': 1}
