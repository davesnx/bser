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
- Reducing the declared domain count from ten to eight improved the confirmed
  median from 204,346.99 to 284,568.97 req/s (+39.3%), reduced p99 latency from
  9.51 to 5.24 ms, and reduced peak RSS from 84.95 to 71.55 MB.
- Domain-local accept loops improved the original ten-domain baseline by 8.5%
  and remain a safe combination candidate because they change a separate file.
- Reusing one response value regressed throughput by 1.8% and p99 latency by
  9.1%; do not repeat this shape without allocation-profile evidence.
- Combining eight domains with domain-local accept loops confirmed at
  310,832.19 req/s, 52.1% above the original baseline and 9.2% above eight
  domains alone. This is the current best configuration.
- Six and seven domains were 10.3% and 2.6% slower than eight domains. The
  useful scaling point is eight for this workload on this host.
- An explicit listen backlog of 4096 was 0.6% slower, which is within noise;
  keep the simpler default.
- Nine domains were 40.2% slower than the eight-domain best and increased p99
  latency to 12.67 ms.
- A one-megaword minor heap confirmed at 374,169.25 req/s, 83.1% above the
  original baseline and 20.4% above the prior best. Peak RSS increased from
  71.92 to 122.00 MB.
- A four-megaword minor heap was only 5.9% faster than the confirmed 1M result
  but raised peak RSS to 324.93 MB, so it was rejected as a severe memory
  regression.
