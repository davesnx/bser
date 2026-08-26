# Worklog: Improve OCaml httpcats multicore

## Data Summary

- Session started from `main` at `6c0dfbd`.
- Primary metric: median request rate from five 30-second runs.
- Baseline: 204,346.99 req/s; p99 9.51 ms; peak RSS 84,951,040 bytes.

## Key Insights

- Short three-second measurements do not separate small changes from host noise.
- `parallel:true` can add a second cross-domain dispatch after accept.
- Eight domains use this host more efficiently than ten and improve both
  throughput and tail latency.

## Next Ideas

- Combine eight domains with `parallel:false` domain-local accept loops.
- Sweep six and seven domains after testing the safe combination.
- Compare explicit Flambda optimization levels in a later focused session.

### Run 1, batch 0: baseline - requests_per_sec=204346.99 (KEEP)

- Timestamp: 2026-08-26 13:35 UTC
- Base: `b8cef8e`
- Candidate: baseline
- Files: none
- Result: 204,346.99 req/s, p99 9.51 ms, peak RSS 84,951,040 bytes,
  CPU 787.50%, 0 errors
- Samples: 194,344.99; 204,346.99; 203,906.63; 207,694.66; 206,604.73
- Insight: The first sample was low, but the other four stayed within 1.9%.
- Next: Test domain-local accept loops and immutable response values.

### Run 2, batch 1: domain_local_accept - requests_per_sec=221679.69 (RUNNER_UP)

- Timestamp: 2026-08-26 13:55 UTC
- Base: `b8cef8e`
- Candidate: `3d5e5c3bf8cecec3e56a7bc5c64682e92f276e18f72043c046882c169d5eb1f0`
- Files: `servers/httpcats-multicore/main.ml`
- Result: 221,679.69 req/s (+8.5%), p99 9.41 ms, peak RSS 84,750,336 bytes,
  CPU 862.69%, 0 errors
- Insight: Removing the second dispatch lets the server use more assigned CPU
  while slightly improving tail latency.
- Next: Combine with the disjoint eight-domain winner.

### Run 3, batch 1: prebuilt_response - requests_per_sec=200640.63 (DISCARD)

- Timestamp: 2026-08-26 13:55 UTC
- Base: `b8cef8e`
- Candidate: `de15c358741844bc9b05fac02bed08446259f27e1ec72c7b8389328fcdcb05f6`
- Files: `servers/httpcats-multicore/main.ml`
- Result: 200,640.63 req/s (-1.8%), p99 10.38 ms, peak RSS 84,541,440 bytes,
  CPU 782.79%, 0 errors
- Insight: Reusing the response value did not reduce the measured bottleneck and
  made tail latency worse.
- Next: Do not combine this change.

### Run 4, batch 1: eight_domains - requests_per_sec=284568.97 (KEEP)

- Timestamp: 2026-08-26 13:55 UTC
- Base: `b8cef8e`
- Candidate: `94618b7343672719b327e4d1fbbf1f946ad759a0cf1a00bb6b59c0058eeff8fd`
- Files: `README.md`, `servers.json`
- Result: 284,568.97 req/s (+39.3%), p99 5.24 ms, peak RSS 71,548,928 bytes,
  CPU 658.46%, 0 errors
- Samples: 279,932.79; 294,150.02; 284,568.97; 304,743.14; 282,104.07
- Insight: Ten domains exceeded the useful scaling point for this workload on
  this host. Eight domains increased throughput while using less CPU and memory.
- Next: Test the safe combination with domain-local accept loops.
