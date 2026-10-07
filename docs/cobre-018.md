# Cobre 0.18 compatibility

The bridge accepts the official Cobre 0.18 wheel and the matching Myria build
in separate virtual environments. The packaging regression checks both the
project dependency and lock metadata; the development lock may retain an older
compatible version. For an official installation from this checkout:

```sh
python -m pip install . 'cobre-python==0.18.0'
python -m pip check
```

NEWAVE conversion and DECOMP conversion with imported FCF were exercised with
the official wheel. Cobre 0.18 writes policy format 3 and records the producer's
software identity and version. Reconvert a DECOMP boundary with the same wheel
that will execute the case; policies from Cobre 0.16 or a different variant
cannot be reused. Preserve the original deck for this reconversion.

The official solver can reject nonstationary estimated inflows in real NEWAVE
decks. The bridge does not silently regularize these models; inspect validation
diagnostics or select a runtime with the documented regularization behavior.

Native checkpoints live under the output directory's `policy/`. A validator of
a resumed case must receive that same output directory. The bridge's conversion
validation concerns the newly converted case, before runtime resume preparation.
