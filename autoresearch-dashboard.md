# Autoresearch Dashboard: Improve OCaml Vif multicore

**Batches:** 1 | **Runs:** 4 | **Kept:** 2 | **Runner-ups:** 1 | **Discarded:** 1 | **Failed:** 0
**Baseline:** requests_per_sec: 181466.67 req/s (#12)
**Best:** requests_per_sec: 281222.19 req/s (#15, +55.0%)
**Confidence:** 2.0x
**Stop:** 4/10 experiments | 0/2 plateau batches | 24/90 minutes

| # | batch | hypothesis | candidate ref | requests_per_sec | status |
|---|---:|---|---|---:|---|
| 12 | 0 | baseline | baseline | 181466.67 | keep |
| 13 | 1 | two_domains | 3901c6d1 | 85601.14 (-52.8%) | discard |
| 14 | 1 | six_domains | daea20e1 | 227247.70 (+25.2%) | runner_up |
| 15 | 1 | eight_domains | 2fbfbb11 | 281222.19 (+55.0%) | keep |
