# scriptc HTTP compatibility

## Question

Which HTTP server should this benchmark compile with `scriptc`, and can it meet
the existing benchmark contract without an embedded JavaScript engine?

This note records the decision for `scriptc` 0.0.35, checked on 2026-08-26.

## Decision

Use `node:http` and name the benchmark `node-http-scriptc`.

The benchmark uses the same request and response logic as `node-http-bun`. It
explicitly narrows `$PORT` from `string | undefined` before calling `Number`
because `scriptc` 0.0.35 rejects `Number(string | number)` with `SC2020`. It
builds with `--backend llvm`, `--optimization release`, and without `--dynamic`.
A compiler coverage gap therefore fails the build instead of changing the
measured runtime, and clang optimizes the server at the release default of
`-O2`.

Do not use Express, Fastify, or another npm framework for this case. npm package
code normally needs `--dynamic`, which embeds QuickJS and would measure a
different execution model.

## Evidence

- Static builds contain the native runtime but no Node or JavaScript engine.
  `--dynamic` explicitly embeds QuickJS for npm packages and `any`-typed code.
  [scriptc README, lines 3-7](https://github.com/vercel-labs/scriptc/blob/v0.0.35/README.md#L3-L7)
- The compiler documents `node:http` as supported native Node API surface and
  gives `createServer` as its server example.
  [scriptc introduction, lines 48-76](https://github.com/vercel-labs/scriptc/blob/v0.0.35/docs/src/app/introduction/page.mdx#L48-L76)
- The shipped static declarations cover every operation used here:
  `request.method`, `request.url`, `writeHead`, `end`, and `createServer`.
  [scriptc HTTP declarations, lines 2156-2207](https://github.com/vercel-labs/scriptc/blob/v0.0.35/packages/compiler/ambient/scriptc-node-fallback.d.ts#L2156-L2207)
  They also cover `listen(port, host)` through the underlying native server.
  [scriptc net declarations, lines 1967-2040](https://github.com/vercel-labs/scriptc/blob/v0.0.35/packages/compiler/ambient/scriptc-node-fallback.d.ts#L1967-L2040)
- Linux uses native `epoll`, and the project tests its native server stack
  against Linux Node.
  [scriptc platform support, lines 18-26](https://github.com/vercel-labs/scriptc/blob/v0.0.35/docs/src/app/platforms/page.mdx#L18-L26)
- Building requires Node.js 24 or newer and clang. The produced executable does
  not require Node.
  [scriptc README, lines 9-15](https://github.com/vercel-labs/scriptc/blob/v0.0.35/README.md#L9-L15)
- The CLI defines `release` as the default `-O2` optimization mode and allows
  the LLVM backend to be pinned so unsupported code fails instead of falling
  back to the C backend.
  [scriptc CLI usage, lines 20-33](https://github.com/vercel-labs/scriptc/blob/v0.0.35/packages/cli/src/usage.ts#L20-L33)
- The LLVM backend emits the opaque `ptr` type. LLVM 15 is the first release
  where opaque pointers are enabled by default, so this benchmark requires
  clang 15 or newer when it pins the LLVM backend.
  [LLVM 15 opaque pointers](https://releases.llvm.org/15.0.0/docs/OpaquePointers.html)

## Compatibility boundary

This decision covers the benchmark's plain HTTP/1.1 contract on native Linux.
It does not claim full Node HTTP compatibility. `scriptc` is experimental, so
the pinned version and the contract check in `bench.py` remain necessary.
