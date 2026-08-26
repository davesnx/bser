# Worklog: Improve OCaml Vif multicore

## Data Summary

- Segment starts from `5225c12`, after the accepted httpcats improvements.
- Primary metric: median request rate from five 30-second runs.
- Baseline: 181,466.67 req/s; p99 3.42 ms; peak RSS 56,639,488 bytes.

## Key Insights

- Vif manages its own Miou/httpcats multicore accept loops.
- Vif scales through eight domains without the sharp contention seen in the
  old httpcats configuration.

## Next Ideas

- Test selected minor-heap sizes on the best domain count.
- Test ten domains to locate Vif's scaling limit.

### Run 12, batch 0: baseline - requests_per_sec=181466.67 (KEEP)

- Timestamp: 2026-08-26 15:06 UTC
- Base: `140c742`
- Candidate: baseline
- Files: none
- Result: 181,466.67 req/s, p99 3.42 ms, peak RSS 56,639,488 bytes,
  CPU 392.06%, 0 errors
- Samples: 171,050.72; 181,466.67; 193,702.01; 196,352.81; 147,858.92
- Insight: Vif has wider run-to-run variance than the final httpcats setup, so
  improvements near 5% will need confirmation.
- Next: Sweep domain counts before tuning the heap.

### Run 13, batch 1: two_domains - requests_per_sec=85601.14 (DISCARD)

- Timestamp: 2026-08-26 15:26 UTC
- Base: `140c742`
- Candidate: `3901c6d16ad5ff0ba7eb80d2b40d4925816aa9886f02bb1cb25135072ea4aa45`
- Files: `README.md`, `servers.json`
- Result: 85,601.14 req/s (-52.8% vs baseline), p99 1.27 ms,
  peak RSS 42,283,008 bytes, CPU 199.52%, 0 errors
- Insight: Two domains improve latency but leave too much throughput unused.
- Next: Discard for the throughput objective.

### Run 14, batch 1: six_domains - requests_per_sec=227247.70 (RUNNER_UP)

- Timestamp: 2026-08-26 15:26 UTC
- Base: `140c742`
- Candidate: `daea20e1901683de19c14c4c41afd15a6b1313ba41ec46e76a537b2a9238bcda`
- Files: `README.md`, `servers.json`
- Result: 227,247.70 req/s (+25.2% vs baseline), p99 3.79 ms,
  peak RSS 71,639,040 bytes, CPU 576.15%, 0 errors
- Insight: Vif continues to scale beyond four domains.
- Next: Eight domains supersede this result.

### Run 15, batch 1: eight_domains - requests_per_sec=281222.19 (KEEP)

- Timestamp: 2026-08-26 15:26 UTC
- Base: `140c742`
- Candidate: `2fbfbb1114c197bbbc110ccdc5854d0248da18e88fc68ce19486580e54cbc75c`
- Files: `README.md`, `servers.json`
- Result: 281,222.19 req/s (+55.0% vs baseline), p99 4.65 ms,
  peak RSS 84,332,544 bytes, CPU 750.61%, 0 errors
- Samples: 281,222.19; 283,061.29; 283,399.57; 277,050.63; 270,364.61
- Insight: Eight domains give a clear, stable gain and remain within the memory
  constraint.
- Next: Tune the minor heap on this domain count.
