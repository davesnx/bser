# Autoresearch: Improve OCaml Vif multicore

## Objective

Increase sustained request throughput for the `vif-multicore` hello-world
server under the repository's standard 64-connection workload without breaking
the HTTP contract or more than doubling peak RSS from this segment's baseline.

## Metrics

- **Primary**: median request rate (requests/second, higher is better)
- **Secondary**: median p99 latency, peak RSS, CPU use, and total errors

## How to Run

`./autoresearch.sh` builds the server, runs five 30-second measurements, and
outputs `METRIC name=value` lines. The benchmark performs the HTTP contract
check, so no separate correctness script is needed.

## Files in Scope

- `servers/vif-multicore/main.ml`: Vif and Miou runtime configuration
- `servers.json`: declared domain count and OCaml runtime parameters
- `README.md`: behavior documentation for kept configuration changes
- `research/ocaml-variant-design.md`: design notes if runtime behavior changes

## Off Limits

- Other server implementations and dependency locks
- Benchmark harness behavior and published benchmark results
- New dependencies

## Constraints

- Preserve `GET /` -> `200 text/plain "Hello, World!"`.
- Keep one process and use `BSER_CPU_COUNT` as the assigned domain count.
- Use the existing locked OCaml 5.5.0 and Vif beta4 dependency graph.
- Build successfully with the standalone Vif Dune project.
- Reject any result with request errors or non-2xx responses.
- Reject a candidate whose peak RSS exceeds twice the segment baseline.
- Measure candidates sequentially because they compete for the same CPUs.

## Stop Conditions

- Maximum experiments: 10
- Plateau: 2 consecutive batches without a confirmed improvement
- Time budget: 90 minutes
- Parallel implementation experiments: 3
- Sequential benchmark measurements: required

## What's Been Tried

- No controlled Vif tuning experiments have been run in this segment.
- Vif currently uses four total domains and no explicit OCaml GC parameters.
- Its multicore runtime already creates domain-local accept loops, so the
  httpcats `parallel:false` source change does not transfer directly.
- The httpcats session showed that domain-count scaling was non-linear and a
  1M-word minor heap improved throughput with a clear memory tradeoff. These are
  hypotheses for Vif, not assumed defaults.
- Eight domains confirmed at 281,222.19 req/s, 55.0% above the four-domain
  baseline. Six domains improved throughput by 25.2%, while two domains reduced
  throughput by 52.8%.
- The accepted eight-domain result uses 84.33 MB peak RSS, below the segment's
  113.28 MB limit.
