# Autoresearch Dashboard: Improve OCaml Vif multicore

**Batches:** 3 | **Runs:** 10 | **Kept:** 3 | **Runner-ups:** 3 | **Discarded:** 4 | **Failed:** 0
**Baseline:** requests_per_sec: 181466.67 req/s (#12)
**Best:** requests_per_sec: 322645.04 req/s (#21, +77.8%)
**Confidence:** 3.0x
**Stop:** 10/10 experiments | 0/2 plateau batches | 64/90 minutes
**Stop reason:** Reached the segment experiment limit.

| # | batch | hypothesis | candidate ref | requests_per_sec | status |
|---|---:|---|---|---:|---|
| 12 | 0 | baseline | baseline | 181466.67 | keep |
| 13 | 1 | two_domains | 3901c6d1 | 85601.14 (-52.8%) | discard |
| 14 | 1 | six_domains | daea20e1 | 227247.70 (+25.2%) | runner_up |
| 15 | 1 | eight_domains | 2fbfbb11 | 281222.19 (+55.0%) | keep |
| 16 | 2 | ten_domains | b56c16af | 224929.55 (+24.0%) | discard |
| 17 | 2 | minor_heap_1m | c2c0889e | 333074.16 (+83.5%) | discard (RSS) |
| 18 | 2 | backlog_4096 | 31758435 | 275029.06 (+51.6%) | discard |
| 19 | 3 | minor_heap_384k | 2767e214 | 299413.94 (+65.0%) | runner_up |
| 20 | 3 | minor_heap_512k | 3207fcd9 | 313579.34 (+72.8%) | runner_up |
| 21 | 3 | minor_heap_640k | a41fb15c | 322645.04 (+77.8%) | keep |
