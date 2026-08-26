# Autoresearch Ideas: OCaml Servers

- Test a 2M-word minor heap for `httpcats-multicore` to map the space between
  the accepted 1M result and the memory-heavy 4M result.
- Capture `runtime_events_tools` traces for the default and 1M minor heaps to
  confirm that fewer minor collections explain the throughput gain.
- Run a separate focused session for Flambda `-O2` and `-O3` variants. Keep
  each server's normal compiler result as the baseline because earlier Flambda
  effects differed by stack.
