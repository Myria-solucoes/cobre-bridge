# cobre-bridge

Convert power system data formats to [Cobre](https://github.com/cobre-rs/cobre) input format.

## Installation

```bash
uv tool install cobre-bridge   # recommended: isolated, on-PATH CLI
pipx install cobre-bridge       # alternative
```

Requires Python >= 3.12. `cobre-python` is bundled as a core dependency, so
`convert --validate` and `compare` work out of the box.

For NEWAVE decks that request computed FPHA, conversion also performs a
zero-iteration Cobre preprocessing pass and writes the conditioned planes as
`system/fpha_hyperplanes.parquet`. Structurally-zero storage slopes are snapped
to exact zero before the case selects the supported `precomputed` source. This
is part of the default conversion path; it does not run SDDP training and is
reported as the `fpha-numerical-hardening` diagnostic.

## Usage

| Command                                                | What it does                                             |
| ------------------------------------------------------ | -------------------------------------------------------- |
| `cobre-bridge convert newave <SRC> <DST>`              | Convert a NEWAVE case to Cobre input format.             |
| `cobre-bridge convert decomp <SRC> <DST>`              | Convert a DECOMP case to Cobre input format.             |
| `cobre-bridge check newave <SRC>`                      | Preflight-validate NEWAVE inputs (no conversion).        |
| `cobre-bridge check decomp <SRC>`                      | Preflight-validate DECOMP inputs (no conversion).        |
| `cobre-bridge compare newave <NEWAVE_DIR> <COBRE_DIR>` | Compare simulation results against Cobre output.         |
| `cobre-bridge compare decomp <DECOMP_DIR> <COBRE_DIR>` | Compare a DECOMP run against its converted Cobre output. |
| `cobre-bridge dashboard <CASE_DIR>`                    | Build an interactive HTML dashboard from Cobre results.  |

Every command accepts `--json` (a single machine-readable verdict
`{schema_version, command, status, summary, diagnostics}` on stdout) and
`-v/-vv`, `--log-file PATH`, `--no-color`, `--quiet`. `convert` adds
`--validate`, `--force`, `--dry-run`, `--diagnostics-json PATH`. `dashboard`
adds `--open`. `compare newave` and `compare decomp` add `--tolerance`,
`--format`, `--out-dir` — with `--format html` both write a full multi-tab
comparison report (Overview/cost, System, Energy Balance, Network, Convergence,
Performance, plant detail, Productivity, FPHA; `compare decomp` adds REE,
constraints, and evaporation sections).

See [docs/cli.md](docs/cli.md) for the full per-command reference.

> **Cobre version.** This release targets **cobre 0.15.0** and requires
> `cobre-python >= 0.15.0,<0.16`.

## Configuration

Defaults for `compare newave` `tolerance`, `format`, and `out_dir` can be set
in a `cobre-bridge.toml` file (discovered from the working directory upward, then
`$XDG_CONFIG_HOME/cobre-bridge/config.toml`, then
`~/.config/cobre-bridge/config.toml`) or via `COBRE_BRIDGE_*` environment
variables (e.g. `COBRE_BRIDGE_RESULTS_TOLERANCE`, `COBRE_BRIDGE_FORMAT`,
`COBRE_BRIDGE_OUT_DIR`). Precedence is flag > env > config file > default.

## Shell completion

```bash
cobre-bridge --install-completion   # install for your shell
cobre-bridge --show-completion      # print the script
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

## License

Apache-2.0
