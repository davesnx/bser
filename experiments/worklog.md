# Worklog: Improve OCaml Vif multicore

## Data Summary

- Segment starts from `5225c12`, after the accepted httpcats improvements.
- Primary metric: median request rate from five 30-second runs.
- Baseline: 181,466.67 req/s; p99 3.42 ms; peak RSS 56,639,488 bytes.

## Key Insights

- Vif manages its own Miou/httpcats multicore accept loops.
- Vif scales through eight domains without the sharp contention seen in the
  old httpcats configuration.
- Ten domains cross Vif's scaling limit; eight remains the best domain count.
- A 640k-word minor heap is the fastest tested setting within the fixed RSS
  limit.

## Next Ideas

- Capture GC runtime events for the default and accepted 640k heaps.

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

### Run 16, batch 2: ten_domains - requests_per_sec=224929.55 (DISCARD)

- Timestamp: 2026-08-26 15:44 UTC
- Base: `a26dc50`
- Candidate: `b56c16af4182f66f393f9fd6610e68f353a89f732f1ae2e8af762846cfee3086`
- Files: `README.md`, `servers.json`
- Result: 224,929.55 req/s (-20.0% vs best), p99 8.73 ms,
  peak RSS 96,100,352 bytes, CPU 876.00%, 0 errors
- Insight: Vif hits contention above eight domains.
- Next: Keep eight domains.

### Run 17, batch 2: minor_heap_1m - requests_per_sec=333074.16 (DISCARD)

- Timestamp: 2026-08-26 15:44 UTC
- Base: `a26dc50`
- Candidate: `c2c0889e7916d377474185b6dabb99c404bcc608c546d68d46f629084e98b47e`
- Files: `README.md`, `servers.json`
- Result: 333,074.16 req/s (+18.4% vs best), p99 3.67 ms,
  peak RSS 134,029,312 bytes, CPU 757.94%, 0 errors
- Insight: The heap reduces GC cost but exceeds the fixed 113,278,976-byte RSS
  limit, so the primary gain is not eligible.
- Next: Test smaller heaps.

### Run 18, batch 2: backlog_4096 - requests_per_sec=275029.06 (DISCARD)

- Timestamp: 2026-08-26 15:44 UTC
- Base: `a26dc50`
- Candidate: `317584358cb7deb7f36211aa3b78c8d44b789c1353a7544b086b05897a59a038`
- Files: `servers/vif-multicore/main.ml`
- Result: 275,029.06 req/s (-2.2% vs best), p99 5.02 ms,
  peak RSS 83,628,032 bytes, CPU 746.21%, 0 errors
- Insight: A larger listen queue does not help 64 persistent connections.
- Next: Keep Vif's default backlog.

### Run 19, batch 3: minor_heap_384k - requests_per_sec=299413.94 (RUNNER_UP)

- Timestamp: 2026-08-26 16:05 UTC
- Base: `a26dc50`
- Candidate: `2767e2140c807a374a7858d0e8df0b2b53f24056ef5dd701932d0c12e0ad9a3d`
- Files: `README.md`, `servers.json`
- Result: 299,413.94 req/s (+6.5% vs prior best), p99 4.25 ms,
  peak RSS 92,454,912 bytes, CPU 749.84%, 0 errors
- Insight: A modest heap increase reduces enough collection work to improve
  throughput without approaching the memory limit.
- Next: Larger safe heaps performed better.

### Run 20, batch 3: minor_heap_512k - requests_per_sec=313579.34 (RUNNER_UP)

- Timestamp: 2026-08-26 16:05 UTC
- Base: `a26dc50`
- Candidate: `3207fcd9672f96adb49fb25692cc553bcbed95e0ca392eddc4a9ee58c88c03d1`
- Files: `README.md`, `servers.json`
- Result: 313,579.34 req/s (+11.5% vs prior best), p99 4.24 ms,
  peak RSS 100,683,776 bytes, CPU 755.34%, 0 errors
- Insight: Throughput continues to improve as the heap grows within budget.
- Next: The 640k candidate supersedes this result.

### Run 21, batch 3: minor_heap_640k - requests_per_sec=322645.04 (KEEP)

- Timestamp: 2026-08-26 16:05 UTC
- Base: `a26dc50`
- Candidate: `a41fb15c65d5ab30154041d557f1a17a1a12230d5081a52b3fc04345db1acc09`
- Files: `README.md`, `servers.json`
- Result: 322,645.04 req/s (+77.8% vs baseline, +14.7% vs prior best),
  p99 3.74 ms, peak RSS 108,290,048 bytes, CPU 759.84%, 0 errors
- Samples: 333,454.12; 320,410.31; 324,886.31; 314,412.65; 322,645.04
- Insight: The 640k heap captures most of the 1M throughput gain while staying
  about 5 MB below the fixed RSS limit.
- Next: Keep this setting.

## Stop Summary

- Stop reason: reached the segment limit of 10 experiments.
- Final accepted result: 322,645.04 req/s, 77.8% above baseline.
- Confidence: 3.0x the measured cross-experiment noise floor.
- Kept changes: eight total domains and a 640k-word minor heap.
- Untested: GC runtime-event profiling and workload sensitivity at other
  connection counts.
