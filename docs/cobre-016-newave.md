# NEWAVE with Cobre 0.16

The NEWAVE converter supports the upstream and Myria Cobre 0.16 wheels.
Use a separate Python environment for each runtime and install the matching
wheel before the bridge. The bridge's FPHA preprocessing runs with that wheel;
conversion and validation must not silently load a different solver version.

```sh
python3.12 -m venv .venv-cobre016
.venv-cobre016/bin/pip install 'cobre-python==0.16.0' .
.venv-cobre016/bin/cobre-bridge convert newave tests/decks/newave_mini /tmp/newave-cobre016 --validate
```

The converted constraint parameters preserve their existing physical convention:
explicit per-stage integrated productivity overrides remain explicit. The 0.16
stored-energy output uses integrated accumulated productivity; consumers must
use the matching productivity column for maximum-energy denominators.

This compatibility extension covers NEWAVE. DECOMP boundary-checkpoint conversion
still requires the 0.15 runtime: 0.16 changed boundary selection and policy format.
Do not use the NEWAVE validation evidence as certification of that separate path.
