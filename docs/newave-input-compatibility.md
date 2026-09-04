# NEWAVE input compatibility

The bridge accepts source-model text files in UTF-8 and Latin-1. In particular,
`dger.dat` is decoded before its fixed-width records are parsed, so accented
comments and ordinal symbols do not affect the study-horizon fields near the
start of the file.

No source-file rewrite is required. Convert the original directory directly:

```bash
cobre-bridge convert newave ./newave-case ./cobre-case --validate
```

The conversion keeps the analytical study period and auxiliary post-study tail
separate in `conversion_manifest.json`; see the
[horizon semantics guide](horizon-semantics.md) for that output contract.
