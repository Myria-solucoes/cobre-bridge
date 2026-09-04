# Documentation contract

Every change to code, conversion behavior, configuration, emitted files,
diagnostics, packaging, or release automation must update the documentation in
the same pull request.

- Add a concise entry under `Unreleased` in `CHANGELOG.md`, or under the
  release-specific section when documenting an already-published release.
- Update the durable guide that owns the changed behavior. Keep `README.md` as
  an entry point and link to the guide instead of duplicating the full contract.
- Add or update a copy-pasteable example for every user-visible command,
  configuration, output, diagnostic, or installation change.
- Keep documentation and regression tests aligned. Verify every path, command,
  field name, version range, and Cobre compatibility statement against the code.
- Never edit generated `docs/cli.md` by hand; regenerate it with
  `scripts/gen-cli-docs.sh` after a CLI surface change.
- If a code-only refactor has no user-visible effect, record that explicitly in
  the pull request. It does not need a changelog entry, but any changed invariant
  or maintainer workflow still belongs in the relevant developer documentation.

Follow `CLAUDE.md` and `.claude/rules/doc-integrity.md` for the complete project
rules. Do not consider a change complete while required documentation is
missing.
