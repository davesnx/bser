#!/usr/bin/env python3
"""Render a standalone HTML report from benchmark results.json."""

import argparse
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "report-template.html")
DATA_TOKEN = "__REPORT_DATA__"


def _add_version(packages, name, version):
    packages.setdefault(name, set()).add(version)


def _package_list(packages):
    return [
        {"name": name, "versions": sorted(versions)}
        for name, versions in sorted(packages.items())
    ]


def _locked_versions(lock_dir):
    packages = {}
    for package_path in glob.glob(os.path.join(lock_dir, "*.pkg")):
        package_file = os.path.basename(package_path).removesuffix(".pkg")
        name, separator, version = package_file.partition(".")
        if not separator:
            continue
        if version == "dev":
            with open(package_path) as lock_file:
                commit = re.search(r"#([0-9a-f]{40})", lock_file.read())
            if commit:
                version = f"dev@{commit.group(1)[:7]}"
        _add_version(packages, name, version)
    return packages


def _dune_dependencies(project_path):
    with open(project_path) as project_file:
        text = project_file.read()
    start = text.index("(depends") + len("(depends")
    dependencies = []
    depth = 1
    index = start
    while depth and index < len(text):
        if text[index] == ";":
            index = text.find("\n", index)
            if index == -1:
                break
        elif text[index].isspace():
            index += 1
        elif text[index] == ")":
            depth -= 1
            index += 1
        elif text[index] == "(":
            if depth == 1:
                match = re.match(r"\(\s*([^\s()]+)", text[index:])
                dependencies.append(match.group(1))
            depth += 1
            index += 1
        else:
            end = index
            while end < len(text) and not text[end].isspace() and text[end] != ")":
                end += 1
            if depth == 1:
                dependencies.append(text[index:end])
            index = end
    return dependencies


def collect_dependency_versions():
    npm_packages = {}
    go_packages = {}
    bun_versions = set()
    with open(os.path.join(HERE, "servers.json")) as manifest_file:
        runtime_versions = json.load(manifest_file).get("runtime_versions", {})
    for package_path in glob.glob(os.path.join(HERE, "servers", "*", "package.json")):
        with open(package_path) as package_file:
            package = json.load(package_file)
        package_manager = package.get("packageManager", "")
        if package_manager.startswith("bun@"):
            bun_versions.add(package_manager.removeprefix("bun@"))
        direct_dependencies = package.get("dependencies", {})
        package_dir = os.path.dirname(package_path)
        bun_lock_path = os.path.join(package_dir, "bun.lock")
        npm_lock_path = os.path.join(package_dir, "package-lock.json")
        if not direct_dependencies:
            continue
        resolved = {}
        if os.path.exists(bun_lock_path):
            with open(bun_lock_path) as lock_file:
                for line in lock_file:
                    match = re.match(r'^\s+"[^"]+": \["([^"]+)"', line)
                    if not match or "@" not in match.group(1):
                        continue
                    name, version = match.group(1).rsplit("@", 1)
                    _add_version(resolved, name, version)
        elif os.path.exists(npm_lock_path):
            with open(npm_lock_path) as lock_file:
                npm_lock = json.load(lock_file)
            locked_packages = npm_lock.get("packages", {})
            for name in direct_dependencies:
                metadata = locked_packages.get(f"node_modules/{name}", {})
                if "version" in metadata:
                    _add_version(resolved, name, metadata["version"])
        else:
            continue
        for name in direct_dependencies:
            for version in resolved.get(name, []):
                _add_version(npm_packages, name, version)

    for module_path in glob.glob(os.path.join(HERE, "servers", "*", "go.mod")):
        with open(module_path) as module_file:
            for name, version in re.findall(
                r"^require\s+(\S+)\s+(v\S+)", module_file.read(), re.MULTILINE
            ):
                _add_version(go_packages, name, version)

    ocaml_packages = {}
    ocaml_versions = set()
    for project_path in glob.glob(os.path.join(HERE, "servers", "*", "dune-project")):
        lock_dir = os.path.join(os.path.dirname(project_path), "dune.lock")
        resolved = _locked_versions(lock_dir)
        ocaml_versions.update(resolved.get("ocaml", []))
        for name in _dune_dependencies(project_path):
            if name == "ocaml":
                continue
            for version in resolved.get(name, []):
                _add_version(ocaml_packages, name, version)

    return {
        "runtimes": [
            {"name": "Bun", "versions": sorted(bun_versions)},
            {
                "name": "TypeScript",
                "versions": [runtime_versions["typescript"]],
            },
            {"name": "Go", "versions": [runtime_versions["go"]]},
            {"name": "OCaml", "versions": sorted(ocaml_versions)},
        ],
        "npm": _package_list(npm_packages),
        "go": _package_list(go_packages),
        "ocaml": _package_list(ocaml_packages),
    }


def write_report(payload, output_path):
    with open(TEMPLATE_PATH) as template_file:
        template = template_file.read()
    if template.count(DATA_TOKEN) != 1:
        raise ValueError(f"expected one {DATA_TOKEN} token in {TEMPLATE_PATH}")

    data = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    data = data.replace("</", "<\\/")
    with open(output_path, "w") as output_file:
        output_file.write(template.replace(DATA_TOKEN, data))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", help="path to results.json")
    parser.add_argument("--out", help="output path; defaults to report.html beside results")
    parser.add_argument(
        "--copy-results",
        action="store_true",
        help="copy results.json beside the generated report",
    )
    parser.add_argument(
        "--refresh-dependencies",
        action="store_true",
        help="replace the stored dependency inventory with the current locks",
    )
    args = parser.parse_args()

    with open(args.results) as results_file:
        payload = json.load(results_file)
    if args.refresh_dependencies:
        payload["dependencies"] = collect_dependency_versions()
    output_path = args.out or os.path.join(os.path.dirname(args.results), "report.html")
    write_report(payload, output_path)
    if args.copy_results:
        results_output = os.path.join(os.path.dirname(output_path), "results.json")
        with open(results_output, "w") as results_file:
            json.dump(payload, results_file, indent=2, default=str)
    print(output_path)


if __name__ == "__main__":
    main()
