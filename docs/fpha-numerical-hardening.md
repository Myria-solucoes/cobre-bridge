# FPHA numerical hardening in NEWAVE and DECOMP conversion

`cobre-bridge convert newave` and `cobre-bridge convert decomp` turn a requested computed FPHA model into a
materialized, numerically conditioned input that Cobre can load through its
supported precomputed-FPHA contract. This step is part of normal conversion; it
does not train an SDDP policy or run a final simulation.

## Why the conversion materializes FPHA

Convex-hull fitting can leave a storage slope (`gamma_v`) that is physically zero
but represented by floating-point residue around machine precision. Sending that
coefficient into the optimization matrix can damage numerical scaling even
though it contributes no meaningful hydro production.

When at least one hydro requests computed FPHA, the converter therefore:

1. writes the otherwise complete Cobre case;
2. starts a temporary Cobre study with one thread and a zero-iteration training
   limit, which performs deterministic preprocessing only;
3. reads the generated `hydro_models/fpha_hyperplanes.parquet`;
4. replaces each nonzero `gamma_v` satisfying `|gamma_v| <= 1e-10 MW/hm3` with
   exact zero while preserving every larger coefficient;
5. writes the result to `system/fpha_hyperplanes.parquet`; and
6. changes the affected entries in `system/hydro_production_models.json` from
   `source: computed` to `source: precomputed`.

The temporary Cobre output is discarded. The converted directory contains the
conditioned, reproducible input artifact used by subsequent Cobre runs.
Both converters use the same implementation. Publishing these planes with the
case avoids architecture-dependent refitting on remote runners, including ARM.
DECOMP materialization precedes terminal boundary-cut import and does not alter
the imported NEWAVE cuts.

## Inactive hydro plants

A hydro registration with zero installed generation is excluded from computed
FPHA. The bridge emits it with a constant-productivity model instead. Its zero
generation bounds keep it operationally inert, and avoiding an unnecessary hull
fit prevents a degenerate plant from reaching Cobre's FPHA preprocessing.

This fallback emits the warning diagnostic
`fpha-inactive-plant-fallback`, including plant names and codes. Missing or
malformed machine data is not silently classified as inactivity; normal parsing
and validation still report those data errors.

## Run and audit a conversion

The following command writes both the converted case and a standalone diagnostic
report. `--validate` also asks the bundled `cobre-python` runtime to validate the
result:

```bash
cobre-bridge convert newave NEWAVE_CASE converted-case \
  --validate \
  --diagnostics-json conversion-diagnostics.json
```

Inspect the two FPHA diagnostics without parsing terminal text:

For a DECOMP source, use the same diagnostic contract:

```bash
cobre-bridge convert decomp DECOMP_CASE converted-decomp \
  --validate \
  --diagnostics-json conversion-diagnostics.json
```

```bash
jq '.diagnostics[] | select(
  .code == "fpha-numerical-hardening" or
  .code == "fpha-inactive-plant-fallback"
)' conversion-diagnostics.json
```

`fpha-numerical-hardening` is informational. Its summary reports the number of
materialized rows and snapped coefficients; its notes report the threshold and
smallest retained absolute slope. `fpha-inactive-plant-fallback` is a warning
because the source deck requested a production representation for a plant with
no installed generation.

The same structured diagnostics are persisted in the converted case's
`conversion_manifest.json`:

```bash
jq '.diagnostics[] | select(.code | startswith("fpha-"))' \
  converted-case/conversion_manifest.json
```

## Preserve Cobre validation warnings

Automatic stochastic-model adjustments performed by Cobre are validation
warnings, not bridge conversion diagnostics. When `--json` and `--validate` are
used together, the bridge preserves their rendered messages under
`summary.validation.warning_messages`:

```bash
cobre-bridge convert newave NEWAVE_CASE converted-case \
  --force --validate --json > conversion-verdict.json
jq '.summary.validation.warning_messages[]?' conversion-verdict.json
```

For example, a Cobre `StationarityRegularized` warning remains visible to an
orchestrator after conversion. Consumers should store and display these messages;
they should not infer them from stderr or discard them because validation still
returned `valid: true`.

## Failure and dry-run behavior

- If Cobre cannot materialize FPHA or does not produce a nonempty hyperplane
  table, conversion fails instead of leaving a partially hardened case.
- `--dry-run` performs no Cobre preprocessing and writes no files. Its planned
  output list still includes `system/fpha_hyperplanes.parquet`.
- A coefficient above the snap threshold is always retained. The converter does
  not round or refit physically meaningful FPHA coefficients.

Regression coverage lives in `tests/test_numeric_hardening.py`,
`tests/test_pipeline.py`, `tests/test_decomp_pipeline.py`, and
`tests/test_fpha_conversion.py`.
