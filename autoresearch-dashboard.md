# Autoresearch Dashboard: Improve OCaml httpcats multicore

**Batches:** 1 | **Runs:** 4 | **Kept:** 2 | **Runner-ups:** 1 | **Discarded:** 1 | **Failed:** 0
**Baseline:** requests_per_sec: 204346.99 req/s (#1)
**Best:** requests_per_sec: 284568.97 req/s (#4, +39.3%)
**Confidence:** 7.6x
**Stop:** 4/12 experiments | 0/2 plateau batches | 24/90 minutes

| # | batch | hypothesis | candidate ref | requests_per_sec | status |
|---|---:|---|---|---:|---|
| 1 | 0 | baseline | baseline | 204346.99 | keep |
| 2 | 1 | domain_local_accept | 3d5e5c3b | 221679.69 (+8.5%) | runner_up |
| 3 | 1 | prebuilt_response | de15c358 | 200640.63 (-1.8%) | discard |
| 4 | 1 | eight_domains | 94618b73 | 284568.97 (+39.3%) | keep |
