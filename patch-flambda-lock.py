#!/usr/bin/env python3
"""Export OCAMLPARAM=_,O3=1 from ocaml-option-flambda in every Flambda lock.

dune pkg gives each package the exported_env of its dependency closure, and
every package depends on the compiler, which depends on ocaml-option-flambda.
A plain OCAMLPARAM in the build environment is not part of dune's rule digest,
so cached non-O3 builds would be reused.
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPORTED_ENV = '(exported_env\n (= OCAMLPARAM "_,O3=1"))\n'


def main():
    for path in sorted(HERE.glob("servers/*/dune.lock/ocaml-option-flambda.*.pkg")):
        text = path.read_text()
        if EXPORTED_ENV in text:
            continue
        if "exported_env" in text:
            raise RuntimeError(f"unexpected exported_env in {path}")
        path.write_text(text.rstrip("\n") + "\n\n" + EXPORTED_ENV)


if __name__ == "__main__":
    main()
