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
- Domain-local accept loops add a further 9.2% on the eight-domain setup.
- Six and seven domains improve p99 latency but give up throughput.

## Next Ideas

- Test nine domains with domain-local handling.
- Measure selected minor-heap sizes before changing GC defaults.
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

### Run 5, batch 1: eight_domains_local_accept - requests_per_sec=310832.19 (KEEP)

- Timestamp: 2026-08-26 14:05 UTC
- Base: `36d1249`
- Candidate: `566abe7d1e3e592601825d64bfbad2f9b4e908c70d49e3fdea1d2d35e7f6777f`
- Files: `README.md`, `servers/httpcats-multicore/main.ml`
- Result: 310,832.19 req/s (+52.1% vs baseline, +9.2% vs prior best),
  p99 5.19 ms, peak RSS 71,921,664 bytes, CPU 731.52%, 0 errors
- Samples: 310,832.19; 299,913.43; 311,799.94; 313,247.10; 184,451.45
- Insight: Domain-local handling and the lower domain count address separate
  costs and combine successfully.
- Next: Sweep nearby domain counts and test the upstream listen backlog.

### Run 6, batch 2: six_domains - requests_per_sec=278929.84 (DISCARD)

- Timestamp: 2026-08-26 14:25 UTC
- Base: `5183c4c`
- Candidate: `83850bf5935c72005c06bf0ba664b1eb242adac20700c338444c48c70bd9f9e4`
- Files: `README.md`, `servers.json`
- Result: 278,929.84 req/s (-10.3% vs best), p99 4.38 ms,
  peak RSS 58,347,520 bytes, CPU 562.16%, 0 errors
- Insight: Six domains trade throughput for lower resource use and tail latency.
- Next: Keep eight domains for the throughput objective.

### Run 7, batch 2: seven_domains - requests_per_sec=302803.75 (DISCARD)

- Timestamp: 2026-08-26 14:25 UTC
- Base: `5183c4c`
- Candidate: `bbdbf6779185a2290daa0766e540f72ef558c2f294c18ca9dd09d92802852845`
- Files: `README.md`, `servers.json`
- Result: 302,803.75 req/s (-2.6% vs best), p99 4.67 ms,
  peak RSS 64,753,664 bytes, CPU 649.46%, 0 errors
- Insight: Seven domains are close, but do not beat the eight-domain median.
- Next: Keep eight domains.

### Run 8, batch 2: backlog_4096 - requests_per_sec=308924.85 (DISCARD)

- Timestamp: 2026-08-26 14:25 UTC
- Base: `5183c4c`
- Candidate: `3de592036211da23b2172fc7e7bd7ed6f6ce12f9d53373e3f518f3dc781dcd88`
- Files: `servers/httpcats-multicore/main.ml`
- Result: 308,924.85 req/s (-0.6% vs best), p99 4.82 ms,
  peak RSS 71,745,536 bytes, CPU 737.38%, 0 errors
- Insight: The explicit backlog is equivalent within noise and adds no value at
  64 persistent connections.
- Next: Keep the default backlog.
