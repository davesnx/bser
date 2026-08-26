# Hello-world web server benchmark

One project to compare minimal "Hello, World!" HTTP servers across runtimes:

[View the latest benchmark report.](https://davesnx.github.io/bser/)

| Server | Stack |
| --- | --- |
| `elysia-bun` | [Elysia](https://elysiajs.com) on Bun |
| `bun-native` | Native [`Bun.serve`](https://bun.com/docs/runtime/http/server) |
| `hono-bun` | [Hono](https://hono.dev) on Bun |
| `h3-bun` | [H3](https://h3.dev) on Bun |
| `node-http-bun` | Bun's `node:http` compatibility layer |
| `node-http-scriptc` | [scriptc](https://scriptc.dev) native `node:http` implementation |
| `express-bun` | [Express](https://expressjs.com) on Bun |
| `fastify-bun` | [Fastify](https://fastify.dev) on Bun |
| `dream` | OCaml [Dream](https://aantron.github.io/dream) on Lwt |
| `dream-flambda` | Dream built with Flambda enabled |
| `opium` | OCaml [Opium](https://github.com/rgrinberg/opium) on http/af and Lwt |
| `vif` | OCaml [Vif](https://robur-coop.github.io/vif/) on httpcats and Miou |
| `vif-multicore` | Vif with four Miou domains |
| `trail` | OCaml [Trail](https://github.com/leostera/trail), Nomad, and Riot |
| `httpcats` | OCaml [httpcats](https://github.com/robur-coop/httpcats) on Miou |
| `httpcats-flambda` | httpcats built with Flambda enabled |
| `httpcats-multicore` | httpcats with eight domain-local Miou accept loops |
| `cohttp-eio` | OCaml [Cohttp](https://github.com/mirage/ocaml-cohttp) on Eio |
| `cohttp-eio-flambda` | Cohttp Eio built with Flambda enabled |
| `cohttp-eio-multicore` | Cohttp Eio with four domains |
| `cohttp-lwt` | OCaml Cohttp on Lwt |
| `httpun-eio` | OCaml [httpun](https://github.com/anmonteiro/httpun) on Eio |
| `httpun-eio-multicore` | httpun Eio with four domains |
| `httpun-lwt` | OCaml httpun on Lwt |
| `httpaf` | OCaml [http/af](https://github.com/inhabitedtype/httpaf) on Lwt |
| `httpaf-flambda` | http/af built with Flambda enabled |
| `tiny-httpd` | OCaml [tiny_httpd](https://github.com/c-cube/tiny-httpd) with system threads |
| `tiny-httpd-flambda` | tiny_httpd built with Flambda enabled |

Every server does the same thing: `GET /` → `200 text/plain "Hello, World!"`,
listening on `$PORT` (default 8080), single process, no logging middleware. The
harness validates that contract before warmup. Baselines and Flambda builds use
one logical CPU. Multicore entries declare their CPU count and receive it in
`BSER_CPU_COUNT`.

Each OCaml server is its **own standalone dune project** (with its own
`dune-project` and `dune-workspace`) using [dune package
management](https://dune.readthedocs.io/en/stable/explanation/package-management.html):
`dune pkg lock` solves and locks that server's dependencies into a private
`dune.lock/`, so version constraints of one stack (say httpcats' h1/miou) can
never collide with another's (Dream's lwt ecosystem) — no opam switch needed.

## Measurements

For each server, `bench.py` reports:

- **Req/s** — sustained requests per second over the measurement window.
- **Latency** — average, p50, p90, p99, and max, in milliseconds.
- **Throughput** — response bytes per second (MB/s).
- **Peak / avg memory** — RSS of the whole server process tree, sampled from
  `/proc` every 200 ms during the measurement window.
- **CPU** — CPU time consumed by the server process tree during the window,
  reported as a percentage of one core.
- **Errors** — socket errors, timeouts, and non-2xx responses.

## Prerequisites

- Linux (resource sampling reads `/proc`).
- [Bun](https://bun.sh) for the TypeScript servers.
  Reports identify TypeScript 7.0.2.
- Node.js >= 24 and clang >= 15 for the `scriptc` compiler. The compiled server
  does not require Node.js. Zig is also supported with `SCRIPTC_CC=zigcc`.
- System libraries used by the OCaml dependency trees — dune builds the OCaml
  side but not C depexts (libev for lwt/dream, gmp for zarith, openssl for
  ssl/tls):

  ```sh
  sudo apt-get install -y libev-dev libssl-dev libgmp-dev pkg-config
  ```

- dune >= 3.24 with package management for the OCaml servers — easiest via
  the standalone dune binary (no opam required):

  ```sh
  curl -fsSL https://get.dune.build/install | sh
  ```

  Then, per server (or `make deps` / `make build` for all of them):

  ```sh
  cd servers/dream
  dune pkg lock   # solve + lock this server's deps into dune.lock/
  dune build      # fetch, build deps, and build the server
  ```

  Locks are per project. Commit the generated `dune.lock/` directories if you
  want reproducible benchmark builds across machines.

  Every OCaml server is locked to OCaml 5.5.0. Flambda projects also lock
  `ocaml-option-flambda`; their private compiler and dependencies are rebuilt
  with Flambda enabled.

- A load generator, one of (checked in this order):
  - [`oha`](https://github.com/hatoo/oha) — recommended (`cargo install oha`)
  - [`wrk`](https://github.com/wg/wrk)
  - [`autocannon`](https://github.com/mcollina/autocannon)
    (`bun add -g autocannon`; also found via `bunx`/`npx`)

## Running

Start with a single OCaml server before bringing up the full matrix — `make first`
locks and builds **dream** only, then runs a short benchmark of it against
the Bun baseline:

```sh
curl -fsSL https://get.dune.build/install | sh   # recent dune, once
make first
```

Once that works, the same flow scales to everything:

```sh
make deps      # bun install + dune pkg lock for every server
make bench     # full run: 30s per server, 64 connections, 5s warmup
make smoke     # quick 3s-per-server pipeline check
```

Or drive `bench.py` directly:

```sh
python3 bench.py --duration 60 --connections 256 --tool oha
python3 bench.py --servers dream,httpaf --no-build
python3 bench.py --server-cpu 2 --servers bun-native,httpaf
python3 bench.py --list
```

Each run writes to `results/<timestamp>/`:

- `results.json` — full metrics, resource samples, config, and environment,
- `results.md` — a ready-to-paste Markdown table,
- `report.html` — a standalone interactive report,
- `<server>.log` — stdout/stderr of each server.

Servers run one at a time on the same port; each is built, pinned to its declared
CPU count, started, contract-checked, warmed up, measured, and torn down before
the next starts. The HTML report hides multicore results by default; use its
**show multicore** control to include them. Bun processes always receive
`NODE_ENV=production`.

## Methodology notes

- Run on an idle machine; close other workloads. Results from laptops with
  thermal throttling are noisy — prefer several runs (`for i in 1 2 3; do ...`)
  and compare medians.
- Load generator and server share the machine here, so they compete for
  cores. For serious numbers, run the generator from a second machine against
  the server's IP (start servers by hand with `PORT=8080 <run cmd>`).
- The harness reserves a server CPU pool large enough for the selected entries.
  Use `--server-cpu` to select its first logical CPU. One-CPU entries use only
  that CPU. The load generator uses a stable, disjoint CPU set.
- Multicore results use each entry's declared OCaml domain count. httpcats uses
  eight; the other multicore entries use four. They are an explicit scaling axis,
  not direct replacements for the one-CPU rankings. Logical CPU topology still
  matters; use separate physical cores for publishable results.

## Status / caveats

- Every server with third-party dependencies has its own lock and is exercised
  by `make smoke`.
- Trail pins Riot commit `310a486` because the latest Riot release restricts
  OCaml to versions older than 5.3. `patch-trail-lock.py` applies three narrow
  OCaml 5.5 compatibility fixes to the archived Config, Riot, and Nomad sources.
- H3 2 is currently a release candidate; its lockfile fixes the tested version.

## Adding a server

1. Create a directory under `servers/` with the implementation. Read `$PORT`,
   respond to `GET /` with `text/plain` `Hello, World!`.
2. Add an entry to `servers.json` with `name`, `runtime`, `cwd`, optional
   `build`, and `run` (the command must stay in the foreground). For a
   multicore entry, add `cpu_count` and read the assigned total from
   `$BSER_CPU_COUNT`.
3. `python3 bench.py --servers <name> --duration 3` to try it out.
