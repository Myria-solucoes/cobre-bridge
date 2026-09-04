# Source text compatibility

The bridge accepts source-model text files in UTF-8 and Latin-1. Before a text
parser runs, the bridge checks the complete byte stream incrementally and
selects one compatible encoding. The parser is then invoked once. Accented
comments or ordinal symbols later in a file therefore cannot alter records
that were parsed earlier.

This applies to NEWAVE and DECOMP conversion inputs, preflight checks, and the
text reports read by comparison commands. Binary inputs such as `hidr.dat`,
`vazoes.dat`, `cortesh.dat`, and `mlt.dat` keep their binary readers.

No source-file rewrite or encoding flag is required:

```bash
cobre-bridge check newave ./newave-case
cobre-bridge convert newave ./newave-case ./cobre-case --validate
cobre-bridge check decomp ./decomp-case
cobre-bridge convert decomp ./decomp-case ./cobre-case --validate
```

For NEWAVE, the analytical study period and auxiliary post-study tail remain
separate in `conversion_manifest.json`; see the
[horizon semantics guide](horizon-semantics.md) for that output contract.
