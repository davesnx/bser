# Worklog: Improve OCaml httpcats multicore

## Data Summary

- Session started from `main` at `6c0dfbd`.
- Primary metric: median request rate from five 30-second runs.
- Baseline: pending.

## Key Insights

- Short three-second measurements do not separate small changes from host noise.
- `parallel:true` can add a second cross-domain dispatch after accept.

## Next Ideas

- Use `parallel:false` for each domain-local accept loop.
- Prebuild immutable response headers and response values.
- Compare explicit Flambda optimization levels in a later focused session.
