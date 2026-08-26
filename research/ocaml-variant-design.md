# OCaml benchmark variants

## Problem

The benchmark needs two independent OCaml comparisons: compiler output with
Flambda enabled, and servers that process work on several cores. Flambda changes
the compiler ABI, while multicore changes process affinity and runtime setup.
The existing harness gave every server one CPU and did not record per-result
affinity.

## Usage

Flambda and multicore entries remain ordinary server names:

```sh
python3 bench.py --servers httpcats,httpcats-flambda,httpcats-multicore
```

A multicore manifest entry declares `"cpu_count": 4`. The harness records the
exact `server_cpus` list in its result and sets `BSER_CPU_COUNT` for the server.
The report hides results with more than one server CPU until the reader enables
**show multicore**.

## Shape

- `servers.json` stays flat. Missing `cpu_count` means one CPU.
- `resolve_cpu_sets` reserves one stable server pool sized for the largest
  selected entry. Load CPUs are outside that pool for every row.
- Each Flambda variant is a standalone Dune project with
  `ocaml-option-flambda`, so its compiler and full dependency graph share one
  ABI.
- Multicore variants use supported domain interfaces: Miou multi-accept loops
  for httpcats and Vif, and Eio `additional_domains` for Cohttp and httpun.
- Old result files remain readable. The report falls back to
  `config.server_cpu` when a row has no `server_cpus` field.

## Synthesis decision

The minimal result-driven design was the base: CPU-list length is the single
source of truth for report filtering. The global reservation policy was adapted
to keep load placement equal across all rows. Explicit `flambda` and
`multicore` booleans, nested project schemas, and a new configuration module
were rejected because the lock dependency and measured CPU list already encode
those facts.

## Tradeoffs accepted

- We accept duplicate projects and locks for ABI-safe compiler comparisons.
- We accept a fixed four-CPU multicore size for a stable published axis.
- We accept longer lock and build times instead of sharing incompatible OCaml
  artifacts.
- We do not add Flambda-plus-multicore combinations in this matrix.

## Sources

- [OCaml 5.5 Flambda](https://ocaml.org/manual/5.5/flambda.html)
- [Dune package management](https://dune.readthedocs.io/en/stable/tutorials/dune-package-management/setup.html)
- [httpcats multicore benchmark](https://github.com/robur-coop/httpcats/blob/v0.3.1/bench/smiou.ml)
- [Eio multi-domain servers](https://github.com/ocaml-multicore/eio/blob/v1.5/lib_eio/net.mli#L409-L440)
