#!/usr/bin/env python3
"""Apply OCaml 5.5 compatibility fixes to Trail's archived dependencies."""

from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCK = HERE / "servers" / "trail" / "dune.lock"


def replace_once(filename, before, after, marker):
    path = LOCK / filename
    text = path.read_text()
    if marker in text:
        return
    if text.count(before) != 1:
        raise RuntimeError(f"expected one compatibility patch target in {path}")
    path.write_text(text.replace(before, after))


def main():
    replace_once(
        "config.dev.pkg",
        """(build
 (all_platforms ((dune))))""",
        """(build
 (all_platforms
  ((action
    (progn
     (system
      \"python3 -c 'from pathlib import Path; p = Path(\\\"config/cfg_ppx.ml\\\"); s = p.read_text(); start = s.index(\\\"    | Pexp_fun (\\\"); end = s.index(\\\"    | Pexp_let \\\", start); replacement = \\\"    | Pexp_function (params, constraint_, body) ->\\\\n        let body =\\\\n          match body with\\\\n          | Pfunction_body exp ->\\\\n              Pfunction_body (apply_config_on_expression exp)\\\\n          | Pfunction_cases (cases, loc, attrs) ->\\\\n              Pfunction_cases (apply_config_on_cases cases, loc, attrs)\\\\n        in\\\\n        Pexp_function (params, constraint_, body)\\\\n\\\"; p.write_text(s[:start] + replacement + s[end:])'\")
     (run dune build -p %{pkg-self:name} -j %{jobs} @install))))))""",
        "Pfunction_body (apply_config_on_expression exp)",
    )

    replace_once(
        "riot.dev.pkg",
        """(build
 (all_platforms ((dune))))""",
        """(build
 (all_platforms
  ((action
    (progn
     (system
      \"python3 -c 'from pathlib import Path; p = Path(\\\"packages/riot-runtime/scheduler/scheduler.ml\\\"); s = p.read_text(); old = \\\"      | effect ->\\\\n          Log.trace (fun f ->\\\\n              f \\\\\\\"Process %a: unhandled effect\\\\\\\" Pid.pp (Process.pid proc));\\\\n          k (Reperform effect)\\\"; new = \\\"      | unhandled ->\\\\n          Log.trace (fun f ->\\\\n              f \\\\\\\"Process %a: unhandled effect\\\\\\\" Pid.pp (Process.pid proc));\\\\n          k (Reperform unhandled)\\\"; assert s.count(old) == 1; p.write_text(s.replace(old, new))'\")
     (system
      \"python3 -c 'from pathlib import Path; p = Path(\\\"packages/riot-runtime/scheduler/scheduler.ml\\\"); s = p.read_text(); old = \\\"        Gluon.Poll.deregister pool.io_scheduler.poll source |> Result.get_ok);\\\"; new = \\\"        Gluon.Poll.deregister pool.io_scheduler.poll source |> ignore);\\\"; assert s.count(old) == 1; p.write_text(s.replace(old, new))'\")
     (run dune build -p %{pkg-self:name} -j %{jobs} @install))))))""",
        "Gluon.Poll.deregister pool.io_scheduler.poll source |> ignore",
    )

    replace_once(
        "nomad.0.0.1.pkg",
        """    (progn
     (when %{pkg-self:dev} (run dune subst))""",
        """    (progn
     (system
      \"python3 -c 'from pathlib import Path; p = Path(\\\"nomad/http1.ml\\\"); s = p.read_text(); assert s.count(\\\"Config.t\\\") == 2; p.write_text(\\\"module Nomad_config = Config\\\\n\\\" + s.replace(\\\"Config.t\\\", \\\"Nomad_config.t\\\"))'\")
     (when %{pkg-self:dev} (run dune subst))""",
        "module Nomad_config = Config",
    )


if __name__ == "__main__":
    main()
