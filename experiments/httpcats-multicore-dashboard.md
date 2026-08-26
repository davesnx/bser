# Autoresearch Dashboard: Improve OCaml httpcats multicore

**Batches:** 3 | **Runs:** 11 | **Kept:** 4 | **Runner-ups:** 1 | **Discarded:** 6 | **Failed:** 0
**Baseline:** requests_per_sec: 204346.99 req/s (#1)
**Best:** requests_per_sec: 374169.25 req/s (#10, +83.1%)
**Confidence:** 2.7x
**Stop:** 11/12 experiments | 0/2 plateau batches | 75/90 minutes
**Stop reason:** Insufficient time remains for another measured and confirmed candidate.

| # | batch | hypothesis | candidate ref | requests_per_sec | status |
|---|---:|---|---|---:|---|
| 1 | 0 | baseline | baseline | 204346.99 | keep |
| 2 | 1 | domain_local_accept | 3d5e5c3b | 221679.69 (+8.5%) | runner_up |
| 3 | 1 | prebuilt_response | de15c358 | 200640.63 (-1.8%) | discard |
| 4 | 1 | eight_domains | 94618b73 | 284568.97 (+39.3%) | keep |
| 5 | 1 | eight_domains_local_accept | 566abe7d | 310832.19 (+52.1%) | keep |
| 6 | 2 | six_domains | 83850bf5 | 278929.84 (+36.5%) | discard |
| 7 | 2 | seven_domains | bbdbf677 | 302803.75 (+48.2%) | discard |
| 8 | 2 | backlog_4096 | 3de59203 | 308924.85 (+51.2%) | discard |
| 9 | 3 | nine_domains | 712b86e1 | 186003.63 (-9.0%) | discard |
| 10 | 3 | minor_heap_1m | e782a02e | 374169.25 (+83.1%) | keep |
| 11 | 3 | minor_heap_4m | 04ac03c2 | 396189.56 (+93.9%) | discard (RSS) |
