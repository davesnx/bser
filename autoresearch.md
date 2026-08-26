# Autoresearch: Improve OCaml httpcats multicore

## Objective

Increase sustained request throughput for the `httpcats-multicore` hello-world
server under the repository's standard 64-connection workload without breaking
the HTTP contract or causing severe latency, memory, CPU, or error regressions.

## Metrics

- **Primary**: median request rate (requests/second, higher is better)
- **Secondary**: median p99 latency, peak RSS, CPU use, and total errors

## How to Run

`./autoresearch.sh` builds the server, runs five 30-second measurements, and
outputs `METRIC name=value` lines.

## Files in Scope

- `servers/httpcats-multicore/main.ml`: request handler and Miou scheduling
- `servers/httpcats-multicore/dune`: native compiler options
- `servers.json`: declared domain count, only for domain-count experiments
- `README.md`: behavior documentation if a kept change makes it inaccurate
- `research/ocaml-variant-design.md`: design notes if scheduling changes

## Off Limits

- Other server implementations and their dependency locks
- Benchmark harness behavior and published benchmark results
- New dependencies

## Constraints

- Preserve `GET /` -> `200 text/plain "Hello, World!"`.
- Keep one process and use `BSER_CPU_COUNT` as the assigned domain count.
- Use the existing locked OCaml 5.5.0 and httpcats 0.3.1 dependency graph.
- Build successfully with the server's standalone Dune project.
- Reject any result with request errors or non-2xx responses.
- Measure candidates sequentially because they compete for the same CPUs.

## Stop Conditions

- Maximum experiments: 12
- Plateau: 2 consecutive batches without a confirmed improvement
- Time budget: 90 minutes
- Parallel implementation experiments: 3
- Sequential benchmark measurements: required

## What's Been Tried

- Earlier three-second trials were too noisy for changes below about 5%.
- Upstream httpcats and Vif use one accept loop per domain with
  `parallel:false`; this repository currently uses `parallel:true`, which can
  transfer each accepted connection to another domain.
- Flambda showed mixed results across stacks and is not assumed to be a win.
