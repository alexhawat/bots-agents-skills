## What?

<!-- What does this change do? Keep it short and concrete. -->

## Why?

<!-- Why is this needed? Link any related issues. -->

Closes #

<!--
Keep the `Closes #<n>` line above (or `Fixes` / `Resolves`) when this PR fully
resolves an issue; delete it when it does not.
-->

## Test plan

- [ ] `make check` green in every bot pack this PR touches
- [ ] Added or updated tests where it makes sense

> Note: `hermes/` and `openclaw/` are instruction-only packs — they must never
> contain `.py`/`.mjs` code. CI enforces this via `tools/pack_drift_guard.py`.
