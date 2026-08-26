# Autoresearch Dashboard: Improve OCaml httpcats multicore

**Batches:** 2 | **Runs:** 8 | **Kept:** 3 | **Runner-ups:** 1 | **Discarded:** 4 | **Failed:** 0
**Baseline:** requests_per_sec: 204346.99 req/s (#1)
**Best:** requests_per_sec: 310832.19 req/s (#5, +52.1%)
**Confidence:** 3.8x
**Stop:** 8/12 experiments | 1/2 plateau batches | 54/90 minutes

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
