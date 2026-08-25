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
| `express-bun` | [Express](https://expressjs.com) on Bun |
| `fastify-bun` | [Fastify](https://fastify.dev) on Bun |
| `dream` | OCaml [Dream](https://aantron.github.io/dream) on Lwt |
| `opium` | OCaml [Opium](https://github.com/rgrinberg/opium) on http/af and Lwt |
| `vif` | OCaml [Vif](https://robur-coop.github.io/vif/) on httpcats and Miou |
| `trail` | OCaml [Trail](https://github.com/leostera/trail), Nomad, and Riot |
| `httpcats` | OCaml [httpcats](https://github.com/robur-coop/httpcats) on Miou |
| `cohttp-eio` | OCaml [Cohttp](https://github.com/mirage/ocaml-cohttp) on Eio |
| `cohttp-lwt` | OCaml Cohttp on Lwt |
| `httpun-eio` | OCaml [httpun](https://github.com/anmonteiro/httpun) on Eio |
| `httpun-lwt` | OCaml httpun on Lwt |
| `httpaf` | OCaml [http/af](https://github.com/inhabitedtype/httpaf) on Lwt |
| `tiny-httpd` | OCaml [tiny_httpd](https://github.com/c-cube/tiny-httpd) with system threads |

Every server does the same thing: `GET /` → `200 text/plain "Hello, World!"`,
listening on `$PORT` (default 8080), single process, no logging middleware. The
harness validates that contract before warmup and pins the server process tree
to one logical CPU.

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

  Every OCaml server is locked to OCaml 5.5.0.

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

Servers run one at a time on the same port; each is built, pinned to one logical
CPU, started, contract-checked, warmed up, measured, and torn down before the
next starts. Bun processes always receive `NODE_ENV=production`.

## Methodology notes

- Run on an idle machine; close other workloads. Results from laptops with
  thermal throttling are noisy — prefer several runs (`for i in 1 2 3; do ...`)
  and compare medians.
- Load generator and server share the machine here, so they compete for
  cores. For serious numbers, run the generator from a second machine against
  the server's IP (start servers by hand with `PORT=8080 <run cmd>`).
- The harness pins every server to one logical CPU. Use `--server-cpu` to select
  it. The harness pins the load generator to separate logical CPUs when the
  machine has them. The processes still share caches and memory bandwidth; use
  a second machine for rigorous measurements.
- All servers are intentionally single-process and single-CPU. Multicore setups (Bun
  `reusePort` clusters, eio/miou multi-domain accept loops) are interesting
  follow-ups but a different benchmark.

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
   `build`, and `run` (the command must stay in the foreground).
3. `python3 bench.py --servers <name> --duration 3` to try it out.
