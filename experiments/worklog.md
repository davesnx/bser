# Worklog: Improve OCaml Vif multicore

## Data Summary

- Segment starts from `5225c12`, after the accepted httpcats improvements.
- Primary metric: median request rate from five 30-second runs.
- Baseline: pending.

## Key Insights

- Vif manages its own Miou/httpcats multicore accept loops.

## Next Ideas

- Sweep two, six, and eight total domains around the current four-domain point.
- Test selected minor-heap sizes on the best domain count.
