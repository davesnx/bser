# Autoresearch Dashboard: Improve OCaml Vif multicore

**Batches:** 2 | **Runs:** 7 | **Kept:** 2 | **Runner-ups:** 1 | **Discarded:** 4 | **Failed:** 0
**Baseline:** requests_per_sec: 181466.67 req/s (#12)
**Best:** requests_per_sec: 281222.19 req/s (#15, +55.0%)
**Confidence:** 2.1x
**Stop:** 7/10 experiments | 1/2 plateau batches | 42/90 minutes

| # | batch | hypothesis | candidate ref | requests_per_sec | status |
|---|---:|---|---|---:|---|
| 12 | 0 | baseline | baseline | 181466.67 | keep |
| 13 | 1 | two_domains | 3901c6d1 | 85601.14 (-52.8%) | discard |
| 14 | 1 | six_domains | daea20e1 | 227247.70 (+25.2%) | runner_up |
| 15 | 1 | eight_domains | 2fbfbb11 | 281222.19 (+55.0%) | keep |
| 16 | 2 | ten_domains | b56c16af | 224929.55 (+24.0%) | discard |
| 17 | 2 | minor_heap_1m | c2c0889e | 333074.16 (+83.5%) | discard (RSS) |
| 18 | 2 | backlog_4096 | 31758435 | 275029.06 (+51.6%) | discard |
