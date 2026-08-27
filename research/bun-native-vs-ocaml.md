# Why `bun-native` is faster than the fastest one-core OCaml server

> Historical result: this note explains the `bun-native` static-route benchmark
> published on 2026-08-26. The active benchmark now uses `bun-fetch-native`,
> which creates a response for each call to its `fetch` handler.

## Question

Why did `bun-native` beat OCaml code compiled to native machine code, and does
the result show that interpreted code is faster than machine code?

## Short answer

No. This benchmark does not compare an interpreter with machine code in
isolation.

OCaml compiles `httpaf-flambda` ahead of time to native machine code. Bun
transpiles the TypeScript and runs JavaScript with JavaScriptCore, which can
interpret bytecode or compile hot code to machine code with a just-in-time
(JIT) compiler. More importantly, almost no application JavaScript runs for a
successful request in this test. `bun-native` gives `Bun.serve` one prebuilt
`Response` as an exact static route. Bun can serve that cached response through
its native HTTP fast path without calling a JavaScript route handler or
allocating another response for each request.

The result therefore compares two complete HTTP paths, not only two language
execution models. Bun wins this small fixed-response test because its measured
path does less work per request.

## Measured result

The published run used `wrk` for 30 seconds with 64 connections and a 5-second
warmup. Each result below used one server CPU and about 100% of one core. The
load generator used separate CPUs.

| Server | Execution path | Requests/s | Average latency | p99 latency | Peak RSS |
| --- | --- | ---: | ---: | ---: | ---: |
| `bun-native` | Bun 1.4.0, exact static `Bun.serve` route | 170,303 | 0.374 ms | 0.633 ms | 20.4 MB |
| `httpaf-flambda` | OCaml 5.5.0 native code, Flambda, `http/af` and Lwt | 130,931 | 0.489 ms | 0.698 ms | 12.1 MB |
| `node-http-scriptc` | TypeScript compiled ahead of time through LLVM, native `node:http` stack | 117,775 | 0.542 ms | 0.747 ms | 4.5 MB |

Against `httpaf-flambda`, `bun-native` processed 30.1% more requests per second,
with 23.7% lower average latency and 9.3% lower p99 latency. Bun used about 69%
more peak memory. Both completed with no errors.

The `node-http-scriptc` row is a useful control. It compiles TypeScript to a
native executable without a JavaScript engine, but Bun still processed 44.6%
more requests per second. The APIs and HTTP stacks differ, so this is not a
compiler-only comparison. It does show that ahead-of-time machine code alone
does not make an HTTP server faster.

Source: `results/2026-08-26T12-39-22Z/results.md` and
`results/2026-08-26T12-39-22Z/results.json`.

## Why Bun has the shorter path

### 1. The benchmark uses Bun's static-response fast path

`servers/bun-native/src/index.ts` creates the body, headers, and `Response` once
at startup. It then registers that object directly for `GET /`:

```ts
const response = new Response(body, { headers });

Bun.serve({
  routes: {
    "/": {
      GET: response,
    },
  },
});
```

Bun 1.4.0 documents this exact form as a static response. Bun caches the
response for the server's lifetime and optimizes it for zero-allocation
dispatch. Its router builds on uWebSockets' tree-based router. This means that
the successful request does not enter the fallback `fetch` function and does
not call an application route function.

Source: [`servers/bun-native/src/index.ts` at the measured revision](https://github.com/davesnx/bser/blob/c5f15af/servers/bun-native/src/index.ts) and
[Bun 1.4.0 routing documentation](https://github.com/oven-sh/bun/blob/bun-v1.4.0/docs/runtime/http/routing.mdx#static-responses).

### 2. The OCaml path creates and dispatches a response for each request

`servers/httpaf-flambda/main.ml` uses a normal `http/af` request handler. For
each request, the stack parses and dispatches through `http/af` and Lwt, calls
the OCaml handler, creates a response value, and sends the string body:

```ocaml
let request_handler (_ : Unix.sockaddr) reqd =
  Reqd.respond_with_string reqd (Response.create ~headers `OK) text
```

The body and headers are shared, but `Response.create` remains in the per-request
handler. Flambda can inline and simplify OCaml code across modules, but it does
not remove the work required by the selected HTTP and scheduling APIs.

Source: [`servers/httpaf-flambda/main.ml`](../servers/httpaf-flambda/main.ml) and
the [OCaml 5.5 Flambda manual](https://ocaml.org/manual/5.5/flambda.html).

### 3. Bun is not interpreter-only

Bun uses JavaScriptCore. JavaScriptCore first produces bytecode, then executes
that bytecode with an interpreter or a JIT compiler. The JIT can turn hot code
into architecture-specific machine code at runtime.

In this benchmark, that distinction is less important than it first appears.
The TypeScript setup code runs at startup, while Bun's native server, router,
HTTP parser, and cached-response path do most of the repeated request work.

Source: [Bun runtime documentation](https://bun.sh/docs/runtime) and
[Bun bytecode documentation](https://bun.sh/docs/bundler/bytecode#what-is-bytecode).

### 4. Native code does not remove framework costs

OCaml's `ocamlopt` produces standalone native executables. That removes a
bytecode interpreter from the OCaml path, but request speed still depends on:

- HTTP parsing and serialization
- event-loop and scheduler work
- callback and abstraction boundaries
- allocation and garbage collection
- buffer management and system calls
- special handling for known routes and known responses

For a 13-byte constant body, these costs dominate the small amount of business
logic. Bun has a special case for exactly this workload. `http/af` exposes a
general request API.

Source: [OCaml 5.5 native-code compilation](https://ocaml.org/manual/5.5/native.html).

## What Flambda changed

The same run measured plain `httpaf` at 125,788 requests/s and
`httpaf-flambda` at 130,931 requests/s. Flambda improved throughput by 4.1%.
That gain is useful, but it is much smaller than Bun's 30.1% lead over the
Flambda build. This supports the view that the HTTP path and static-response
optimization matter more here than the final OCaml compiler pass.

One run cannot establish a stable Flambda effect. Repeat the benchmark several
times and compare medians before treating 4.1% as a general result.

## Multicore result

The fastest OCaml result in the full table was `cohttp-eio-multicore` at 401,569
requests/s. It used four server CPUs and about 369% CPU, so it is not a direct
comparison with the one-CPU Bun result. It shows that OCaml can exceed Bun's
total throughput when the server receives more cores. The one-core comparison
uses `httpaf-flambda` because it keeps CPU allocation equal.

## What the benchmark proves

- On this machine and workload, Bun's static `Bun.serve` route is faster than
  every one-core OCaml stack in the run.
- Ahead-of-time native compilation does not guarantee the fastest complete
  request path.
- A specialized native fast path can matter more than the source language.
- Bun's lead applies to a fixed in-memory response. It does not predict results
  for database access, JSON processing, application routing, streaming, or
  CPU-heavy work.

## Follow-up tests

To isolate the causes, run these comparisons on one CPU with several repetitions:

1. Measure the active `bun-fetch-native` server. It adds a JavaScript callback
   and creates a response for each request.
2. Add an OCaml server with a lower-level fixed-response path that avoids Lwt
   and minimizes per-request construction.
3. Compare medians and inspect allocations, CPU profiles, and system-call
   counts. Requests per second alone cannot identify which layer costs time.

These tests would measure the static-route advantage directly instead of
inferring it from different server stacks.
